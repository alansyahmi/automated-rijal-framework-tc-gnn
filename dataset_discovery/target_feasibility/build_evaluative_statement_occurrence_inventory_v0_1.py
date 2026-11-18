#!/usr/bin/env python3
"""Index exact candidate phrase occurrences in local numbered Taqrib entries."""
from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PIPELINE = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline"
VOCAB_DIR = PIPELINE / "rank_vocabulary_candidate_inventory_v0_1_2026-11-16"
VOCABULARY = VOCAB_DIR / "CANDIDATE_VOCABULARY_V0_1.csv"
VOCAB_MANIFEST = VOCAB_DIR / "MANIFEST.json"
SHADOW_DIR = PIPELINE / "rank_label_shadow_run_v1_2026-11-15"
ENTRY_INDEX = SHADOW_DIR / "ENTRY_INDEX.csv"
SHADOW_MANIFEST = SHADOW_DIR / "RUN_MANIFEST.json"
OUTPUT = PIPELINE / "evaluation_statement_occurrence_inventory_v0_1_2026-11-16"
ARABIC_LETTER = re.compile(r"[\u0621-\u064a\u066e-\u06d3\u06fa-\u06fc]")

# These are the separate phrases raised as praise modifiers in the codebook
# discussion. The longer combined praise wording is already in the 203-cue list.
DISCUSSION_CUES = [
    ("MOD-001", "جبل الحفظ"),
    ("MOD-002", "إمام الدنيا في فقه الحديث"),
]

HUMAN_FIELDS = [
    "human_review_status",
    "human_statement_family",
    "human_statement_domain",
    "human_claim_content",
    "human_claim_mode",
    "human_wording_force",
    "human_consensus_wording",
    "human_notes",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\r\n")
        writer.writeheader()
        writer.writerows(rows)


def verify_package(directory: Path, manifest_name: str, checksum_name: str) -> dict[str, Any]:
    manifest_path = directory / manifest_name
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    checksum_path = directory / checksum_name
    expected_manifest = checksum_path.read_text(encoding="ascii").split()[0]
    if sha256(manifest_path) != expected_manifest:
        raise SystemExit(f"Manifest sidecar mismatch: {manifest_path}")
    for name, expected in manifest.get("outputs", {}).items():
        path = directory / name
        if not path.is_file() or sha256(path) != expected:
            raise SystemExit(f"Input package output mismatch: {path}")
    return manifest


def arabic_letter_at(text: str, pos: int) -> bool:
    return 0 <= pos < len(text) and bool(ARABIC_LETTER.fullmatch(text[pos]))


def find_matches(text: str, phrase: str) -> list[tuple[int, int, bool]]:
    found: list[tuple[int, int, bool]] = []
    pos = 0
    while phrase and (start := text.find(phrase, pos)) >= 0:
        end = start + len(phrase)
        bounded = not arabic_letter_at(text, start - 1) and not arabic_letter_at(text, end)
        found.append((start, end, bounded))
        pos = start + 1
    return found


def write_manifest(inputs: list[Path], outputs: list[Path], counts: dict[str, Any]) -> None:
    manifest_path = OUTPUT / "MANIFEST.json"
    manifest = {
        "package_id": OUTPUT.name,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "exact phrase occurrence index; no statement categories, ranks, or numeric scores assigned",
        "method": (
            "Scan every exact string in candidate vocabulary v0.1 plus two separately identified praise cues "
            "against all numbered entries in the frozen shadow-run entry index. No normalization, stemming, "
            "fuzzy matching, or semantic classification is performed."
        ),
        "counts": counts,
        "inputs": {
            path.relative_to(ROOT).as_posix(): sha256(path)
            for path in inputs
        },
        "outputs": {
            path.name: sha256(path)
            for path in outputs
        },
        "human_fields_policy": "All human review and statement descriptor fields in the occurrence CSV are blank.",
        "manifest_hash_policy": "MANIFEST.sha256 records this manifest hash separately; it is not recursively embedded.",
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    (OUTPUT / "MANIFEST.sha256").write_text(
        f"{sha256(manifest_path)}  MANIFEST.json\n", encoding="ascii", newline="\n"
    )


def main() -> None:
    protected_outputs = {
        "PHRASE_OCCURRENCES_V0_1.csv",
        "PHRASE_OCCURRENCE_SUMMARY_V0_1.csv",
        "README.md",
        "MANIFEST.json",
    }
    if OUTPUT.exists() and any((OUTPUT / name).exists() for name in protected_outputs):
        raise SystemExit(f"Refusing to overwrite an existing generated package: {OUTPUT}")

    vocab_manifest = verify_package(VOCAB_DIR, "MANIFEST.json", "MANIFEST.sha256")
    shadow_manifest = verify_package(SHADOW_DIR, "RUN_MANIFEST.json", "RUN_MANIFEST.sha256")
    if sha256(VOCABULARY) != vocab_manifest["outputs"]["CANDIDATE_VOCABULARY_V0_1.csv"]:
        raise SystemExit("Candidate vocabulary changed since its manifest was written")
    if sha256(ENTRY_INDEX) != shadow_manifest["outputs"]["ENTRY_INDEX.csv"]:
        raise SystemExit("Entry index changed since the shadow-run manifest was written")

    candidates = read_csv(VOCABULARY)
    if len(candidates) != 203 or len({row["candidate_id"] for row in candidates}) != len(candidates):
        raise SystemExit("Expected 203 uniquely identified vocabulary candidates")
    phrases = [row["phrase_candidate_exact"] for row in candidates]
    if len(set(phrases)) != len(phrases):
        raise SystemExit("Candidate vocabulary contains duplicate exact phrases")

    cue_rows: list[dict[str, Any]] = []
    for cue_id, phrase in DISCUSSION_CUES:
        if phrase in phrases:
            raise SystemExit(f"Discussion cue duplicates a vocabulary phrase: {phrase}")
        cue_rows.append({
            "candidate_id": cue_id,
            "phrase_candidate_exact": phrase,
            "candidate_source": "discussion_addition_for_praise_modifier_review",
            "discovery_sources": "user_review_discussion_2026-11-16",
            "source_rank_anchor_numbers": "",
        })
    for row in candidates:
        cue_rows.append({
            "candidate_id": row["candidate_id"],
            "phrase_candidate_exact": row["phrase_candidate_exact"],
            "candidate_source": "rank_vocabulary_candidate_inventory_v0_1",
            "discovery_sources": row.get("discovery_sources", ""),
            "source_rank_anchor_numbers": row.get("source_rank_anchor_numbers", ""),
        })
    cue_rows.sort(key=lambda row: row["candidate_id"])

    entries = read_csv(ENTRY_INDEX)
    if len(entries) != 8827 or len({row["entry_id"] for row in entries}) != len(entries):
        raise SystemExit("Expected 8,827 unique numbered local Taqrib entries")

    occurrences: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    occurrence_counter = 0
    for cue in cue_rows:
        hits: list[tuple[dict[str, str], int, int, bool]] = []
        for entry in entries:
            for start, end, bounded in find_matches(entry["entry_text_verbatim"], cue["phrase_candidate_exact"]):
                hits.append((entry, start, end, bounded))
        bounded_hits = [hit for hit in hits if hit[3]]
        summaries.append({
            "candidate_id": cue["candidate_id"],
            "candidate_source": cue["candidate_source"],
            "phrase_candidate_exact": cue["phrase_candidate_exact"],
            "discovery_sources": cue["discovery_sources"],
            "source_rank_anchor_numbers_unverified": cue["source_rank_anchor_numbers"],
            "exact_substring_occurrences": len(hits),
            "entries_with_exact_substring": len({hit[0]["entry_id"] for hit in hits}),
            "arabic_letter_bounded_occurrences": len(bounded_hits),
            "entries_with_arabic_letter_bounded_match": len({hit[0]["entry_id"] for hit in bounded_hits}),
            "substring_only_occurrences": len(hits) - len(bounded_hits),
            "interpretation": "Occurrence counts are lexical discovery counts, not statement labels or independent cases.",
        })
        for entry, start, end, bounded in hits:
            occurrence_counter += 1
            text = entry["entry_text_verbatim"]
            occurrence = {
                "occurrence_id": f"OCC-{occurrence_counter:07d}",
                "candidate_id": cue["candidate_id"],
                "candidate_source": cue["candidate_source"],
                "phrase_candidate_exact": cue["phrase_candidate_exact"],
                "discovery_sources": cue["discovery_sources"],
                "source_rank_anchor_numbers_unverified": cue["source_rank_anchor_numbers"],
                "entry_id": entry["entry_id"],
                "printed_page_num": entry["printed_page_num"],
                "entry_number_verbatim": entry["entry_number_verbatim"],
                "match_start_char_zero_based": start,
                "match_end_char_exclusive": end,
                "arabic_letter_bounded": "yes" if bounded else "no",
                "matched_text_verbatim": text[start:end],
                "context_before": text[max(0, start - 70):start],
                "context_after": text[end:min(len(text), end + 70)],
                "entry_text_verbatim": text,
            }
            occurrence.update({field: "" for field in HUMAN_FIELDS})
            occurrences.append(occurrence)

    OUTPUT.mkdir(parents=True, exist_ok=True)
    occurrence_fields = list(occurrences[0].keys()) if occurrences else [
        "occurrence_id", "candidate_id", "candidate_source", "phrase_candidate_exact",
        "discovery_sources", "source_rank_anchor_numbers_unverified", "entry_id",
        "printed_page_num", "entry_number_verbatim", "match_start_char_zero_based",
        "match_end_char_exclusive", "arabic_letter_bounded", "matched_text_verbatim",
        "context_before", "context_after", "entry_text_verbatim", *HUMAN_FIELDS,
    ]
    summary_fields = list(summaries[0].keys())
    occurrence_path = OUTPUT / "PHRASE_OCCURRENCES_V0_1.csv"
    summary_path = OUTPUT / "PHRASE_OCCURRENCE_SUMMARY_V0_1.csv"
    write_csv(occurrence_path, occurrences, occurrence_fields)
    write_csv(summary_path, summaries, summary_fields)

    bounded_total = sum(row["arabic_letter_bounded_occurrences"] for row in summaries)
    counts = {
        "numbered_entries_scanned": len(entries),
        "candidate_strings": len(cue_rows),
        "candidate_strings_from_vocabulary_v0_1": len(candidates),
        "additional_discussion_cues": len(DISCUSSION_CUES),
        "exact_substring_occurrences_across_candidate_strings": len(occurrences),
        "arabic_letter_bounded_occurrences_across_candidate_strings": bounded_total,
        "rank_assignments": 0,
        "statement_descriptor_assignments": 0,
        "numeric_scores_assigned": 0,
    }
    readme = f"""# Evaluative statement phrase occurrences v0.1

**Status:** exact-string occurrence index for discovery and source review. No human statement descriptors, ranks, or numeric scores are assigned.

## Scope and method

The scan covers {len(entries):,} numbered entries in the local Taqrib entry index. It records every exact Unicode substring occurrence for the 203 phrase strings in the current rank-vocabulary candidate inventory plus two separately identified praise cues: جبل الحفظ and إمام الدنيا في فقه الحديث. The combined praise wording جبل الحفظ وإمام الدنيا في فقه الحديث remains in the original phrase inventory; the two added cues let the reviewer inspect each component as well.

No Arabic normalization, stemming, fuzzy matching, or semantic classification is performed. Character offsets are zero-based Python Unicode character positions; the end position is exclusive. The Arabic-letter-bounded flag only indicates whether an Arabic letter directly touches the match boundary. It does not establish a semantic word or statement boundary.

## Files

- PHRASE_OCCURRENCES_V0_1.csv contains the full local entry text, exact matched text, entry/page locator, offsets, short neighboring context, and blank human review fields.
- PHRASE_OCCURRENCE_SUMMARY_V0_1.csv gives exact and Arabic-letter-bounded occurrence counts by candidate phrase.
- MANIFEST.json and MANIFEST.sha256 record the source and output hashes.

Candidate strings can overlap in one entry. For example, a standalone praise cue can also match inside a longer compound. Counts across candidate strings therefore overlap and are not counts of distinct claims, narrators, or independent observations. The candidate list remains a seed inventory, not an exhaustive census of all praise or criticism wording.

The candidate inventory's rank suggestions and source anchors are preserved only as unverified discovery metadata. The human statement-family, domain, claim-content, claim-mode, wording-force, consensus-wording, review-status, and note columns are blank. This package does not update the 12-rank labels or enable extraction rules.

## Source limits

The source is the local numbered-entry index from the Shamela4 Taqrib extraction. Its text is a digital transcription, not a visual check against printed page images. The inventory excludes unnumbered page chunks. Phrase occurrence counts must not be presented as total corpus coverage or as the number of validated evaluation statements.

## Next review

Review phrases and full entry contexts by statement construction. Add or revise candidate strings in a later version only after preserving exact wording and provenance. Then manually code the statement-level descriptors; keep canonical rank decisions and any numeric scoring separate.
"""
    readme_path = OUTPUT / "README.md"
    readme_path.write_text(readme, encoding="utf-8", newline="\n")

    inputs = [VOCABULARY, VOCAB_MANIFEST, ENTRY_INDEX, SHADOW_MANIFEST, Path(__file__).resolve()]
    write_manifest(inputs, [occurrence_path, summary_path, readme_path], counts)
    print(json.dumps({"output": str(OUTPUT), **counts}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
