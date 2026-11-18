#!/usr/bin/env python3
"""Extend candidate inventory v0.1 with reviewer-observed specialized wording."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PIPELINE = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline"
V1_DIR = PIPELINE / "rank_label_candidate_inventory_v0_1_2026-11-15"
SHADOW_DIR = PIPELINE / "rank_label_shadow_run_v1_2026-11-15"
POLICY_PATH = PIPELINE / "RANK_TARGET_POLICY_V0_2.md"
OUTPUT_DIR = PIPELINE / "rank_label_candidate_inventory_v0_2_2026-11-15"
ARABIC_LETTER = re.compile(r"[\u0621-\u064a\u066e-\u06d3\u06fa-\u06fc]")

EXTENSIONS = [
    {
        "phrase_exact_verbatim": "صدوق حافظ",
        "origin": "user_review_observation",
        "candidate_roles": "observed_compound_grade_candidate",
        "pilot_rank_proposals_unverified": "2_or_4_unresolved",
        "broad_context_note_types": "compound_praise_or_grade_qualification",
        "target_phrase_candidate_for_first_hit": "true",
        "context_note_candidate": "false",
        "source_notes": "Longer compound must be preserved; it overlaps the shorter source cue صدوق. Rank mapping is unresolved because it differs from the explicit source example ثقة حافظ.",
    },
    {
        "phrase_exact_verbatim": "لين الحديث",
        "origin": "user_review_observation",
        "candidate_roles": "observed_grade_candidate;context_note_candidate",
        "pilot_rank_proposals_unverified": "6_candidate_unverified",
        "broad_context_note_types": "rank6_hadith_criticism_or_qualification",
        "target_phrase_candidate_for_first_hit": "true",
        "context_note_candidate": "true",
        "source_notes": "Observed local wording corresponding to the source definition's فلين الحديث; preserve exact local spelling and check Rank 6 conditions.",
    },
    {
        "phrase_exact_verbatim": "كذبوه",
        "origin": "user_review_observation",
        "candidate_roles": "observed_grade_candidate;attributed_judgement_candidate",
        "pilot_rank_proposals_unverified": "12_candidate_rank11_rank12_boundary_unresolved",
        "broad_context_note_types": "lying_or_fabrication_judgement",
        "target_phrase_candidate_for_first_hit": "true",
        "context_note_candidate": "true",
        "source_notes": "User identified this as a grade wording. Preserve exact verb form; rank 11 versus 12 depends on Ibn Hajar's distinction and surrounding attribution.",
    },
    {
        "phrase_exact_verbatim": "خلط في غيره",
        "origin": "user_flagged_entry_observation",
        "candidate_roles": "context_note_candidate",
        "pilot_rank_proposals_unverified": "possible_rank5_memory_or_transmission_context",
        "broad_context_note_types": "memory_or_transmission_note",
        "target_phrase_candidate_for_first_hit": "false",
        "context_note_candidate": "true",
        "source_notes": "Observed in S3076-P077-C012-E0009; relation to a standardized grade is not determined by the occurrence scan.",
    },
    {
        "phrase_exact_verbatim": "مخلط في غيرهم",
        "origin": "local_corpus_variant_observation",
        "candidate_roles": "context_note_candidate",
        "pilot_rank_proposals_unverified": "possible_rank5_memory_or_transmission_context",
        "broad_context_note_types": "memory_or_transmission_note",
        "target_phrase_candidate_for_first_hit": "false",
        "context_note_candidate": "true",
        "source_notes": "Variant observed in the local Taqrib entry S3076-P109-C008-E0473; not a new rank rule.",
    },
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def find_occurrences(text: str, phrase: str):
    offset = 0
    while True:
        index = text.find(phrase, offset)
        if index < 0:
            return
        yield index, index + len(phrase)
        offset = index + 1


def is_arabic_letter(text: str, position: int) -> bool:
    return 0 <= position < len(text) and bool(ARABIC_LETTER.fullmatch(text[position]))


def main() -> None:
    if OUTPUT_DIR.exists():
        raise SystemExit(f"Refusing to overwrite existing inventory: {OUTPUT_DIR}")

    v1_manifest = json.loads((V1_DIR / "MANIFEST.json").read_text(encoding="utf-8"))
    for name, expected in v1_manifest["outputs"].items():
        if sha256(V1_DIR / name) != expected:
            raise SystemExit(f"Candidate inventory v0.1 hash mismatch: {name}")
    _, entries = read_csv(SHADOW_DIR / "ENTRY_INDEX.csv")
    _, prior_inventory = read_csv(V1_DIR / "PHRASE_INVENTORY.csv")
    _, prior_grade_hits = read_csv(V1_DIR / "GRADE_CUE_OCCURRENCES.csv")
    _, prior_note_hits = read_csv(V1_DIR / "CONTEXT_NOTE_OCCURRENCES.csv")
    _, prior_summary = read_csv(V1_DIR / "ENTRY_FIRST_CANDIDATE_SUMMARY.csv")
    _, prior_counts = read_csv(V1_DIR / "PHRASE_COUNTS.csv")
    entry_by_id = {row["entry_id"]: row for row in entries}
    inventory_by_phrase = {row["phrase_exact_verbatim"]: row for row in prior_inventory}
    if any(ext["phrase_exact_verbatim"] in inventory_by_phrase for ext in EXTENSIONS):
        raise SystemExit("An extension phrase already exists in v0.1; review before proceeding")

    max_phrase_num = max(int(row["phrase_id"].split("-")[-1]) for row in prior_inventory)
    for index, ext in enumerate(EXTENSIONS, start=1):
        ext["phrase_id"] = f"PHT-{max_phrase_num + index:04d}"

    next_occurrence = len({row["occurrence_id"] for row in prior_grade_hits + prior_note_hits}) + 1
    new_hits: list[dict[str, Any]] = []
    added_counts: dict[str, int] = defaultdict(int)
    added_entries: dict[str, set[str]] = defaultdict(set)
    for ext in EXTENSIONS:
        phrase = ext["phrase_exact_verbatim"]
        for entry in entries:
            text = entry["entry_text_verbatim"]
            for start, end in find_occurrences(text, phrase):
                new_hits.append({
                    "occurrence_id": f"OCC-V02-{next_occurrence:07d}",
                    "phrase_id": ext["phrase_id"],
                    "phrase_exact_verbatim": phrase,
                    "entry_id": entry["entry_id"],
                    "local_book_id": entry["local_book_id"],
                    "shamela_book_id": entry["shamela_book_id"],
                    "local_page_id": entry["local_page_id"],
                    "shamela_page_id": entry["shamela_page_id"],
                    "printed_page_num": entry["printed_page_num"],
                    "entry_number_verbatim": entry["entry_number_verbatim"],
                    "source_chunk_index": entry["source_chunk_index"],
                    "match_start_char": start,
                    "match_end_char": end,
                    "left_adjacent_arabic_letter": str(is_arabic_letter(text, start - 1)).lower(),
                    "right_adjacent_arabic_letter": str(is_arabic_letter(text, end)).lower(),
                    "context_before": text[max(0, start - 80):start],
                    "matched_text": text[start:end],
                    "context_after": text[end:end + 80],
                    "source_rank_anchor_candidates": "",
                    "pilot_rank_proposals_unverified": ext["pilot_rank_proposals_unverified"],
                    "candidate_sources": ext["origin"],
                    "candidate_roles": ext["candidate_roles"],
                    "rank_assignment": "",
                    "human_disposition": "",
                    "auto_accept": "false",
                    "boundary_status": "whole_entry_exact_string_hit_only",
                    "overlapping_phrase_ids": "",
                })
                next_occurrence += 1
                added_counts[phrase] += 1
                added_entries[phrase].add(entry["entry_id"])

    all_hits_by_id: dict[str, dict[str, Any]] = {}
    for row in prior_grade_hits + prior_note_hits + new_hits:
        all_hits_by_id[row["occurrence_id"]] = row.copy()
    all_hits = list(all_hits_by_id.values())
    by_entry: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in all_hits:
        by_entry[row["entry_id"]].append(row)
    for entry_hits in by_entry.values():
        for hit in entry_hits:
            overlaps = {
                other["phrase_id"]
                for other in entry_hits
                if other["occurrence_id"] != hit["occurrence_id"]
                and max(int(hit["match_start_char"]), int(other["match_start_char"]))
                < min(int(hit["match_end_char"]), int(other["match_end_char"]))
            }
            hit["overlapping_phrase_ids"] = ";".join(sorted(overlaps))

    extension_by_id = {ext["phrase_id"]: ext for ext in EXTENSIONS}
    grade_rows = [row for row in prior_grade_hits if row["occurrence_id"] in all_hits_by_id]
    note_rows = [row for row in prior_note_hits if row["occurrence_id"] in all_hits_by_id]
    for hit in new_hits:
        ext = extension_by_id[hit["phrase_id"]]
        if ext["target_phrase_candidate_for_first_hit"] == "true":
            grade_rows.append(hit.copy())
        if ext["context_note_candidate"] == "true":
            note_rows.append(hit.copy())
    # Update overlap lists for all existing and new occurrences in each layer.
    grade_ids = {row["occurrence_id"] for row in grade_rows}
    note_ids = {row["occurrence_id"] for row in note_rows}
    grade_rows = [all_hits_by_id[oid] for oid in sorted(grade_ids)]
    note_rows = [all_hits_by_id[oid] for oid in sorted(note_ids)]

    summary_by_id = {row["entry_id"]: row.copy() for row in prior_summary}
    all_grade_by_entry: dict[str, list[dict[str, Any]]] = defaultdict(list)
    all_context_by_entry: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in grade_rows:
        all_grade_by_entry[row["entry_id"]].append(row)
    for row in note_rows:
        all_context_by_entry[row["entry_id"]].append(row)
    for entry_id, summary in summary_by_id.items():
        hits = all_grade_by_entry.get(entry_id, [])
        hits.sort(key=lambda r: (int(r["match_start_char"]), -len(r["phrase_exact_verbatim"]), r["phrase_exact_verbatim"]))
        if hits:
            first_start = int(hits[0]["match_start_char"])
            earliest = [r for r in hits if int(r["match_start_char"]) == first_start]
            summary["earliest_lexical_grade_candidate"] = " || ".join(dict.fromkeys(r["phrase_exact_verbatim"] for r in earliest))
            summary["earliest_candidate_rank_anchors_unverified"] = ";".join(sorted({a for r in earliest for a in r["source_rank_anchor_candidates"].split(";") if a}, key=lambda v: int(v) if v.isdigit() else 99))
            summary["earliest_pilot_rank_proposals_unverified"] = ";".join(sorted({a for r in earliest for a in r["pilot_rank_proposals_unverified"].split(";") if a}))
            summary["earliest_candidate_offsets"] = ";".join(f"{r['match_start_char']}:{r['match_end_char']}" for r in earliest)
            summary["earliest_hit_has_arabic_letter_boundary_warning"] = "yes" if any(r["left_adjacent_arabic_letter"] == "true" or r["right_adjacent_arabic_letter"] == "true" for r in earliest) else "no"
            summary["candidate_status"] = "earliest_lexical_candidate_unreviewed"
        else:
            summary["earliest_lexical_grade_candidate"] = ""
            summary["earliest_candidate_rank_anchors_unverified"] = ""
            summary["earliest_pilot_rank_proposals_unverified"] = ""
            summary["earliest_candidate_offsets"] = ""
            summary["earliest_hit_has_arabic_letter_boundary_warning"] = ""
            summary["candidate_status"] = "no_exact_inventory_candidate_hit"
        summary["all_grade_candidate_hit_count"] = str(len(hits))
        summary["context_note_candidate_hit_count"] = str(len(all_context_by_entry.get(entry_id, [])))
        summary["all_rank_anchor_candidates_unverified"] = ";".join(sorted({a for r in hits for a in r["source_rank_anchor_candidates"].split(";") if a}, key=lambda v: int(v) if v.isdigit() else 99))
        summary["rank_assignment"] = ""
        summary["human_disposition"] = ""

    inventory_rows = [row.copy() for row in prior_inventory]
    counts_by_phrase = {row["phrase_exact_verbatim"]: row.copy() for row in prior_counts}
    for ext in EXTENSIONS:
        phrase = ext["phrase_exact_verbatim"]
        inventory_rows.append({
            "phrase_id": ext["phrase_id"],
            "phrase_exact_verbatim": phrase,
            "candidate_sources": ext["origin"],
            "candidate_roles": ext["candidate_roles"],
            "source_rank_anchor_candidates": "",
            "pilot_rank_proposals_unverified": ext["pilot_rank_proposals_unverified"],
            "broad_context_note_types": ext["broad_context_note_types"],
            "source_notes": ext["source_notes"],
            "observed_exact_occurrences": added_counts[phrase],
            "unique_entries_with_hit": len(added_entries[phrase]),
            "target_phrase_candidate_for_first_hit": ext["target_phrase_candidate_for_first_hit"],
            "context_note_candidate": ext["context_note_candidate"],
            "rank_assignment": "",
            "rule_status": "inventory_only_unreviewed",
        })
        counts_by_phrase[phrase] = {
            "phrase_id": ext["phrase_id"],
            "phrase_exact_verbatim": phrase,
            "observed_exact_occurrences": added_counts[phrase],
            "unique_entries_with_hit": len(added_entries[phrase]),
            "candidate_sources": ext["origin"],
            "source_rank_anchor_candidates": "",
            "pilot_rank_proposals_unverified": ext["pilot_rank_proposals_unverified"],
        }

    OUTPUT_DIR.mkdir(parents=True)
    write_csv(OUTPUT_DIR / "PHRASE_INVENTORY.csv", inventory_rows, list(inventory_rows[0]))
    fields = list(all_hits[0])
    write_csv(OUTPUT_DIR / "GRADE_CUE_OCCURRENCES.csv", grade_rows, fields)
    write_csv(OUTPUT_DIR / "CONTEXT_NOTE_OCCURRENCES.csv", note_rows, fields)
    summary_rows = [summary_by_id[row["entry_id"]] for row in entries]
    write_csv(OUTPUT_DIR / "ENTRY_FIRST_CANDIDATE_SUMMARY.csv", summary_rows, list(summary_rows[0]))
    write_csv(OUTPUT_DIR / "PHRASE_COUNTS.csv", list(counts_by_phrase.values()), list(next(iter(counts_by_phrase.values()))))
    write_csv(OUTPUT_DIR / "USER_IDENTIFIED_PHRASES_V0_2.csv", EXTENSIONS, list(EXTENSIONS[0]))

    report = f"""# Taqrīb two-layer candidate inventory v0.2

**Status:** v0.1 extended with five exact phrases raised or surfaced during review; candidate-only, no rank labels assigned.

## Additions

- `صدوق حافظ`: compound candidate retained alongside the shorter overlapping `صدوق`; rank remains unresolved between the source example and the compound definition.
- `لين الحديث`: exact local wording observed in 115 entries; Rank 6 candidate, subject to the definition's conditions.
- `كذبوه`: exact local wording observed in 15 entries; possible Rank 12 candidate, with the Rank 11/12 boundary unresolved.
- `خلط في غيره` and `مخلط في غيرهم`: memory/transmission context candidates; their relation to a first-grade target is not assigned.

## Current counts

- Phrase definitions: {len(inventory_rows)}.
- Numbered entries: {len(entries)}.
- Grade/target candidate occurrence rows: {len(grade_rows)}.
- Context-note occurrence rows: {len(note_rows)}.
- Earliest lexical candidate present in {sum(1 for row in summary_rows if row['earliest_lexical_grade_candidate']):,} entries; no exact inventory candidate hit in {sum(1 for row in summary_rows if not row['earliest_lexical_grade_candidate']):,}.
- Rank assignments and auto-accepts: zero.

The new terms are exact-string seeds, not approved vocabulary rules. A match may be a substring or contextual use. `ENTRY_FIRST_CANDIDATE_SUMMARY.csv` records the earliest lexical candidate, not a verified complete first-grade phrase.

The local extraction begins at printed page 75 and excludes nonempty unnumbered chunks from the numbered-entry index. The phrase inventory is not exhaustive; blank entries do not imply absence of a grade phrase.
"""
    (OUTPUT_DIR / "RUN_REPORT.md").write_text(report, encoding="utf-8", newline="\n")
    (OUTPUT_DIR / "README.md").write_text(
        "# Taqrīb rank candidate inventory v0.2\n\nThis is a non-destructive extension of v0.1 with five exact phrase seeds from review. It adds the user-observed forms without assigning ranks or enabling rules. Use the UTF-8 BOM CSVs for Excel Arabic display. The earliest match is lexical only; see RUN_REPORT.md.\n",
        encoding="utf-8", newline="\n",
    )
    extension_path = OUTPUT_DIR / "USER_IDENTIFIED_PHRASES_V0_2.csv"

    input_paths = [
        V1_DIR / "MANIFEST.json",
        V1_DIR / "ENTRY_FIRST_CANDIDATE_SUMMARY.csv",
        SHADOW_DIR / "ENTRY_INDEX.csv",
        POLICY_PATH,
    ]
    output_names = [
        "PHRASE_INVENTORY.csv", "GRADE_CUE_OCCURRENCES.csv", "CONTEXT_NOTE_OCCURRENCES.csv",
        "ENTRY_FIRST_CANDIDATE_SUMMARY.csv", "PHRASE_COUNTS.csv", "USER_IDENTIFIED_PHRASES_V0_2.csv",
        "RUN_REPORT.md", "README.md",
    ]
    manifest = {
        "package": "Taqrib two-layer rank-candidate inventory v0.2",
        "status": "exact phrase candidates only; no ranks assigned or rules enabled",
        "policy_version": "Rank Target Policy v0.2",
        "source_entry_count": len(entries),
        "phrase_definition_count": len(inventory_rows),
        "grade_candidate_occurrences": len(grade_rows),
        "context_note_occurrences": len(note_rows),
        "entries_with_earliest_lexical_candidate": sum(1 for row in summary_rows if row["earliest_lexical_grade_candidate"]),
        "entries_without_exact_candidate_hit": sum(1 for row in summary_rows if not row["earliest_lexical_grade_candidate"]),
        "rank_assignments": 0,
        "auto_accepted": 0,
        "inputs": {str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path) for path in input_paths},
        "outputs": {name: sha256(OUTPUT_DIR / name) for name in output_names},
        "extension_phrases": [item["phrase_exact_verbatim"] for item in EXTENSIONS],
        "limitations": [
            "Phrase extensions came from user-reviewed examples or local variant observations; they remain unapproved candidates.",
            "Exact occurrence does not establish a complete grade span, rank, attribution, or context relationship.",
            "No-cue entries may contain unlisted specialized wording and need review.",
            "Counts are not assigned-label counts, coverage, precision, recall, or model performance.",
        ],
    }
    raw = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    (OUTPUT_DIR / "MANIFEST.json").write_bytes(raw)
    (OUTPUT_DIR / "MANIFEST.sha256").write_text(
        f"{hashlib.sha256(raw).hexdigest()}  MANIFEST.json\n", encoding="ascii", newline="\n"
    )
    print(json.dumps({
        "output_dir": str(OUTPUT_DIR),
        "phrase_definitions": len(inventory_rows),
        "added_occurrences": dict(added_counts),
        "grade_candidate_occurrences": len(grade_rows),
        "context_note_occurrences": len(note_rows),
        "earliest_candidate_entries": manifest["entries_with_earliest_lexical_candidate"],
        "no_exact_candidate_hit_entries": manifest["entries_without_exact_candidate_hit"],
        "rank_assignments": 0,
    }, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
