#!/usr/bin/env python3
"""Build a full local-corpus, two-layer phrase candidate inventory.

Exact phrase hits are unreviewed candidates only. No rank labels are assigned.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PIPELINE = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline"
SHADOW_DIR = PIPELINE / "rank_label_shadow_run_v1_2026-11-15"
PILOT_DIR = PIPELINE / "rank_label_agent_review_v1_2026-11-15/first_grade_policy_v0_2"
POLICY_PATH = PIPELINE / "RANK_TARGET_POLICY_V0_2.md"
OUTPUT_DIR = PIPELINE / "rank_label_candidate_inventory_v0_1_2026-11-15"
OUTPUT_FILES = [
    "PHRASE_INVENTORY.csv",
    "GRADE_CUE_OCCURRENCES.csv",
    "CONTEXT_NOTE_OCCURRENCES.csv",
    "ENTRY_FIRST_CANDIDATE_SUMMARY.csv",
    "PHRASE_COUNTS.csv",
    "RUN_REPORT.md",
    "README.md",
]
ARABIC_LETTER = re.compile(r"[\u0621-\u064a\u066e-\u06d3\u06fa-\u06fc]")


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


def occurrences(text: str, needle: str):
    start = 0
    while True:
        found = text.find(needle, start)
        if found < 0:
            return
        yield found, found + len(needle)
        start = found + 1


def adjacent_arabic(text: str, index: int) -> bool:
    return 0 <= index < len(text) and bool(ARABIC_LETTER.fullmatch(text[index]))


def main() -> None:
    if OUTPUT_DIR.exists():
        raise SystemExit(f"Refusing to overwrite existing inventory: {OUTPUT_DIR}")

    run_manifest_path = SHADOW_DIR / "RUN_MANIFEST.json"
    run_manifest = json.loads(run_manifest_path.read_text(encoding="utf-8"))
    for name in ("ENTRY_INDEX.csv", "CUE_OCCURRENCES.csv", "RULE_REGISTRY_SNAPSHOT.csv"):
        actual = sha256(SHADOW_DIR / name)
        if run_manifest["outputs"].get(name) != actual:
            raise SystemExit(f"Shadow-run input hash mismatch for {name}")

    pilot_manifest_path = PILOT_DIR / "MANIFEST.json"
    pilot_manifest = json.loads(pilot_manifest_path.read_text(encoding="utf-8"))
    for name in (
        "PRIORITY_12_FIRST_GRADE_TARGETS_DRAFT_V0_2.csv",
        "PRIORITY_12_CONTEXT_NOTE_LEDGER_DRAFT_V0_2.csv",
    ):
        if sha256(PILOT_DIR / name) != pilot_manifest["outputs"].get(name):
            raise SystemExit(f"v0.2 pilot input hash mismatch for {name}")

    _, entry_rows = read_csv(SHADOW_DIR / "ENTRY_INDEX.csv")
    _, source_cues = read_csv(SHADOW_DIR / "RANK_CUE_INVENTORY.csv")
    _, registry_rules = read_csv(SHADOW_DIR / "RULE_REGISTRY_SNAPSHOT.csv")
    _, pilot_targets = read_csv(PILOT_DIR / "PRIORITY_12_FIRST_GRADE_TARGETS_DRAFT_V0_2.csv")
    _, pilot_notes = read_csv(PILOT_DIR / "PRIORITY_12_CONTEXT_NOTE_LEDGER_DRAFT_V0_2.csv")

    specs: dict[str, dict[str, Any]] = {}

    def add_spec(
        phrase: str,
        *,
        source: str,
        role: str,
        rank_anchor: str = "",
        pilot_rank: str = "",
        broad_note_type: str = "",
        source_note: str = "",
        target_candidate: bool = True,
        context_candidate: bool = False,
    ) -> None:
        phrase = phrase or ""
        if not phrase:
            return
        spec = specs.setdefault(phrase, {
            "phrase_exact": phrase,
            "sources": set(),
            "candidate_roles": set(),
            "source_rank_anchors": set(),
            "pilot_rank_proposals": set(),
            "broad_note_types": set(),
            "source_notes": set(),
            "target_candidate": False,
            "context_candidate": False,
        })
        spec["sources"].add(source)
        spec["candidate_roles"].add(role)
        if rank_anchor:
            spec["source_rank_anchors"].add(str(rank_anchor))
        if pilot_rank:
            spec["pilot_rank_proposals"].add(str(pilot_rank))
        if broad_note_type:
            spec["broad_note_types"].add(broad_note_type)
        if source_note:
            spec["source_notes"].add(source_note)
        spec["target_candidate"] = spec["target_candidate"] or target_candidate
        spec["context_candidate"] = spec["context_candidate"] or context_candidate

    # Source-inventory examples remain illustrative and can be rank or context candidates.
    affiliation_cues = {"التشيع", "القدر", "النصب", "الإرجاء", "التجهم"}
    non_target_context_cues = affiliation_cues | {"فلين الحديث"}
    for cue in source_cues:
        family = cue.get("cue_family", "")
        phrase = cue["cue_text_exact"]
        broad_type = ""
        is_context = False
        if phrase in affiliation_cues:
            broad_type = "affiliation_or_innovation_reference"
            is_context = True
        elif phrase in {"له أوهام", "يخطئ", "تغير بأخرة", "صدوق يهم", "صدوق سيء الحفظ"}:
            broad_type = "memory_or_assessment_qualification"
            is_context = True
        elif family == "contextual_assessment":
            broad_type = "context_dependent_rank_phrase"
            is_context = True
        add_spec(
            phrase,
            source="source_inventory_v0_exact_example",
            role="rank_cue_or_context_candidate",
            rank_anchor=cue.get("source_rank_anchor", ""),
            broad_note_type=broad_type,
            source_note=cue.get("source_note", ""),
            target_candidate=phrase not in non_target_context_cues,
            context_candidate=is_context,
        )

    # Include only existing rank-family registry candidates; generation rules are separate context.
    for rule in registry_rules:
        if rule.get("rule_family") != "taxonomy_rank" or rule.get("rule_status") != "candidate_not_enabled":
            continue
        add_spec(
            rule.get("rule_exact_string", ""),
            source="inactive_rank_registry_candidate",
            role="unapproved_rule_phrase_candidate",
            rank_anchor=rule.get("candidate_rank_from_registry", ""),
            source_note=rule.get("rule_id", ""),
            target_candidate=True,
        )

    for target in pilot_targets:
        add_spec(
            target["first_grade_phrase_candidate_exact"],
            source="priority12_ai_pilot_target_candidate_v0_2",
            role="observed_first_grade_candidate",
            pilot_rank=target["target_rank_candidate_under_policy"],
            source_note=target["candidate_basis"],
            target_candidate=True,
        )
    for note in pilot_notes:
        add_spec(
            note["context_note_text_exact"],
            source="priority12_ai_pilot_context_note_v0_2",
            role="context_note_candidate",
            pilot_rank="",
            broad_note_type=note["context_note_type_broad"],
            source_note=note["possible_rank_relevance"],
            target_candidate=False,
            context_candidate=True,
        )

    phrase_texts = sorted(specs)
    for index, phrase in enumerate(phrase_texts, start=1):
        specs[phrase]["phrase_id"] = f"PHT-{index:04d}"

    grade_hits: list[dict[str, Any]] = []
    note_hits: list[dict[str, Any]] = []
    hits_by_entry: dict[str, list[dict[str, Any]]] = defaultdict(list)
    counts: Counter[str] = Counter()
    entries_with_hit: dict[str, set[str]] = defaultdict(set)
    occurrence_number = 0

    for entry in entry_rows:
        text = entry["entry_text_verbatim"]
        for phrase in phrase_texts:
            spec = specs[phrase]
            for start, end in occurrences(text, phrase):
                occurrence_number += 1
                row = {
                    "occurrence_id": f"OCC-{occurrence_number:08d}",
                    "phrase_id": spec["phrase_id"],
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
                    "left_adjacent_arabic_letter": str(adjacent_arabic(text, start - 1)).lower(),
                    "right_adjacent_arabic_letter": str(adjacent_arabic(text, end)).lower(),
                    "context_before": text[max(0, start - 80):start],
                    "matched_text": text[start:end],
                    "context_after": text[end:end + 80],
                    "source_rank_anchor_candidates": ";".join(sorted(spec["source_rank_anchors"], key=lambda v: int(v) if v.isdigit() else 99)),
                    "pilot_rank_proposals_unverified": ";".join(sorted(spec["pilot_rank_proposals"])),
                    "candidate_sources": ";".join(sorted(spec["sources"])),
                    "candidate_roles": ";".join(sorted(spec["candidate_roles"])),
                    "rank_assignment": "",
                    "human_disposition": "",
                    "auto_accept": "false",
                    "boundary_status": "whole_entry_exact_string_hit_only",
                }
                hits_by_entry[entry["entry_id"]].append(row)
                counts[phrase] += 1
                entries_with_hit[phrase].add(entry["entry_id"])
                if spec["target_candidate"]:
                    grade_hits.append(row.copy())
                if spec["context_candidate"]:
                    note_hits.append(row.copy())

    # Mark lexical overlaps without treating substring containment as a rank decision.
    for entry_occurrences in hits_by_entry.values():
        for hit in entry_occurrences:
            overlaps = {
                other["phrase_id"]
                for other in entry_occurrences
                if other["occurrence_id"] != hit["occurrence_id"]
                and max(int(hit["match_start_char"]), int(other["match_start_char"]))
                < min(int(hit["match_end_char"]), int(other["match_end_char"]))
            }
            hit["overlapping_phrase_ids"] = ";".join(sorted(overlaps))

    # Split final occurrence rows by layer after overlap metadata has been added.
    grade_ids = {row["occurrence_id"] for row in grade_hits}
    all_occurrences = [row for hits in hits_by_entry.values() for row in hits]
    grade_hits = [row for row in all_occurrences if row["occurrence_id"] in grade_ids]
    context_ids = {
        row["occurrence_id"]
        for hits in hits_by_entry.values()
        for row in hits
        if specs[row["phrase_exact_verbatim"]]["context_candidate"]
    }
    note_hits = [row for row in all_occurrences if row["occurrence_id"] in context_ids]

    summary_rows = []
    for entry in entry_rows:
        hits = hits_by_entry.get(entry["entry_id"], [])
        target_hits = [row for row in hits if specs[row["phrase_exact_verbatim"]]["target_candidate"]]
        target_hits.sort(key=lambda row: (int(row["match_start_char"]), int(row["match_end_char"])))
        first_start = int(target_hits[0]["match_start_char"]) if target_hits else None
        earliest = [row for row in target_hits if int(row["match_start_char"]) == first_start] if first_start is not None else []
        summary_rows.append({
            "entry_id": entry["entry_id"],
            "local_book_id": entry["local_book_id"],
            "shamela_book_id": entry["shamela_book_id"],
            "local_page_id": entry["local_page_id"],
            "shamela_page_id": entry["shamela_page_id"],
            "printed_page_num": entry["printed_page_num"],
            "entry_number_verbatim": entry["entry_number_verbatim"],
            "source_chunk_index": entry["source_chunk_index"],
            "duplicate_printed_entry_number_on_page": entry["duplicate_printed_entry_number_on_page"],
            "entry_text_verbatim": entry["entry_text_verbatim"],
            "earliest_lexical_grade_candidate": " || ".join(sorted({r["phrase_exact_verbatim"] for r in earliest})),
            "earliest_candidate_rank_anchors_unverified": ";".join(sorted({a for r in earliest for a in r["source_rank_anchor_candidates"].split(";") if a}, key=lambda v: int(v) if v.isdigit() else 99)),
            "earliest_pilot_rank_proposals_unverified": ";".join(sorted({p for r in earliest for p in r["pilot_rank_proposals_unverified"].split(";") if p})),
            "earliest_candidate_offsets": ";".join(f"{r['match_start_char']}:{r['match_end_char']}" for r in earliest),
            "earliest_hit_has_arabic_letter_boundary_warning": "yes" if any(r["left_adjacent_arabic_letter"] == "true" or r["right_adjacent_arabic_letter"] == "true" for r in earliest) else ("no" if earliest else ""),
            "all_grade_candidate_hit_count": len(target_hits),
            "context_note_candidate_hit_count": sum(1 for r in hits if specs[r["phrase_exact_verbatim"]]["context_candidate"]),
            "all_rank_anchor_candidates_unverified": ";".join(sorted({a for r in target_hits for a in r["source_rank_anchor_candidates"].split(";") if a}, key=lambda v: int(v) if v.isdigit() else 99)),
            "rank_assignment": "",
            "human_disposition": "",
            "candidate_status": "earliest_lexical_candidate_unreviewed" if earliest else "no_exact_inventory_candidate_hit",
        })

    inventory_rows = []
    for phrase in phrase_texts:
        spec = specs[phrase]
        inventory_rows.append({
            "phrase_id": spec["phrase_id"],
            "phrase_exact_verbatim": phrase,
            "candidate_sources": ";".join(sorted(spec["sources"])),
            "candidate_roles": ";".join(sorted(spec["candidate_roles"])),
            "source_rank_anchor_candidates": ";".join(sorted(spec["source_rank_anchors"], key=lambda v: int(v) if v.isdigit() else 99)),
            "pilot_rank_proposals_unverified": ";".join(sorted(spec["pilot_rank_proposals"])),
            "broad_context_note_types": ";".join(sorted(spec["broad_note_types"])),
            "source_notes": " || ".join(sorted(spec["source_notes"])),
            "observed_exact_occurrences": counts[phrase],
            "unique_entries_with_hit": len(entries_with_hit[phrase]),
            "target_phrase_candidate_for_first_hit": str(spec["target_candidate"]).lower(),
            "context_note_candidate": str(spec["context_candidate"]).lower(),
            "rank_assignment": "",
            "rule_status": "inventory_only_unreviewed",
        })

    phrase_count_rows = [
        {
            "phrase_id": specs[phrase]["phrase_id"],
            "phrase_exact_verbatim": phrase,
            "observed_exact_occurrences": counts[phrase],
            "unique_entries_with_hit": len(entries_with_hit[phrase]),
            "candidate_sources": ";".join(sorted(specs[phrase]["sources"])),
            "source_rank_anchor_candidates": ";".join(sorted(specs[phrase]["source_rank_anchors"], key=lambda v: int(v) if v.isdigit() else 99)),
            "pilot_rank_proposals_unverified": ";".join(sorted(specs[phrase]["pilot_rank_proposals"])),
        }
        for phrase in phrase_texts
    ]
    OUTPUT_DIR.mkdir(parents=True)
    write_csv(OUTPUT_DIR / "PHRASE_INVENTORY.csv", inventory_rows, list(inventory_rows[0]))
    occurrence_fields = list(all_occurrences[0]) + ["overlapping_phrase_ids"]
    write_csv(OUTPUT_DIR / "GRADE_CUE_OCCURRENCES.csv", grade_hits, occurrence_fields)
    write_csv(OUTPUT_DIR / "CONTEXT_NOTE_OCCURRENCES.csv", note_hits, occurrence_fields)
    write_csv(OUTPUT_DIR / "ENTRY_FIRST_CANDIDATE_SUMMARY.csv", summary_rows, list(summary_rows[0]))
    write_csv(OUTPUT_DIR / "PHRASE_COUNTS.csv", phrase_count_rows, list(phrase_count_rows[0]))

    source_rank_counts = Counter(
        rank
        for entry in summary_rows
        for rank in entry["earliest_candidate_rank_anchors_unverified"].split(";")
        if rank
    )
    note_occurrence_count = len(note_hits)
    grade_occurrence_count = len(grade_hits)
    report = f"""# Taqrīb two-layer rank-candidate inventory v0.1

**Status:** full numbered-entry phrase scan complete; no rank labels assigned or accepted.

## Scope

- Local numbered entry strings scanned: {len(entry_rows):,}.
- Exact candidate phrase definitions searched: {len(phrase_texts)}.
- Candidate-role occurrence rows: {grade_occurrence_count:,}.
- Context-note occurrence rows: {note_occurrence_count:,}.
- Candidate definitions come from the source inventory's illustrative examples, existing inactive rank registry phrases, and exact forms observed in the priority-12 AI pilot. They are not exhaustive.
- Matching is exact Unicode substring matching only: no orthographic normalization, fuzzy matching, or semantic classification.

## Reading the candidate outputs

`ENTRY_FIRST_CANDIDATE_SUMMARY.csv` reports the earliest lexical candidate hit in each numbered entry. It does **not** establish that the hit is the first complete grade-bearing phrase. Some strings are substrings of longer words, compounds, qualifications, or attributed/contextual notes. Review boundary flags, overlaps, full source text, and the separate context-note file before deciding.

Source rank anchors and pilot rank proposals are explicitly unverified. `rank_assignment` and `human_disposition` remain blank in occurrence outputs; no candidate rule was enabled or auto-accepted. Entries without an exact hit are not proven to lack a rank phrase, because the inventory is incomplete.

The two layers are:

- **Grade/target candidates:** exact source-anchor, inactive-rule, and pilot target phrases that may be the first grade-bearing phrase.
- **Context-note candidates:** exact source or pilot phrases that may be an attached qualification, affiliation/innovation reference, transmission note, or attributed judgement. Their relation to a target is not inferred by this scan.

## Source and coverage limits

The scan uses the previously hashed local `pages.jsonl` extraction: it starts at printed page 75, omits the rank introduction, and contains 688 page rows. It includes 8,827 numbered entry strings; 3,459 nonempty unnumbered chunks were not included in that numbered-entry index. The rank introduction's cue list is illustrative, not exhaustive. These results are occurrence counts, not rank counts, label coverage, precision, recall, or model performance.

## Files

- `PHRASE_INVENTORY.csv`: exact phrase definitions, sources, candidate roles, and occurrence counts.
- `GRADE_CUE_OCCURRENCES.csv`: exact candidate occurrences and context windows.
- `CONTEXT_NOTE_OCCURRENCES.csv`: exact context-note candidate occurrences; relations are not assigned.
- `ENTRY_FIRST_CANDIDATE_SUMMARY.csv`: one row per numbered entry, with earliest lexical candidate and full source entry.
- `PHRASE_COUNTS.csv`: exact occurrence and unique-entry counts by phrase.
- `MANIFEST.json` and checksum: input/output hashes and scope metadata.

No frozen annotation, source entry, rank assignment, or automation registry state was modified.
"""
    (OUTPUT_DIR / "RUN_REPORT.md").write_text(report, encoding="utf-8", newline="\n")
    readme = """# Taqrīb rank candidate inventory v0.1\n\nThis is a full numbered-entry exact-phrase inventory under Rank Target Policy v0.2. It is candidate-only: the earliest lexical hit is not a confirmed first grade phrase, context-note relation is not inferred, ranks are not assigned, and no rules are enabled. Use the report and manifest for scope and provenance. CSV files include a UTF-8 BOM for Arabic display in Excel.\n"""
    (OUTPUT_DIR / "README.md").write_text(readme, encoding="utf-8", newline="\n")

    inputs = {
        "ENTRY_INDEX.csv": sha256(SHADOW_DIR / "ENTRY_INDEX.csv"),
        "CUE_OCCURRENCES.csv": sha256(SHADOW_DIR / "CUE_OCCURRENCES.csv"),
        "RANK_CUE_INVENTORY.csv": sha256(SHADOW_DIR / "RANK_CUE_INVENTORY.csv"),
        "RULE_REGISTRY_SNAPSHOT.csv": sha256(SHADOW_DIR / "RULE_REGISTRY_SNAPSHOT.csv"),
        "PRIORITY_12_FIRST_GRADE_TARGETS_DRAFT_V0_2.csv": sha256(PILOT_DIR / "PRIORITY_12_FIRST_GRADE_TARGETS_DRAFT_V0_2.csv"),
        "PRIORITY_12_CONTEXT_NOTE_LEDGER_DRAFT_V0_2.csv": sha256(PILOT_DIR / "PRIORITY_12_CONTEXT_NOTE_LEDGER_DRAFT_V0_2.csv"),
        "RANK_TARGET_POLICY_V0_2.md": sha256(POLICY_PATH),
    }
    manifest = {
        "package": "Taqrib two-layer rank-candidate inventory v0.1",
        "status": "exact phrase inventory only; no labels assigned or accepted",
        "generated_by": "dataset_discovery/target_feasibility/build_taqrib_two_layer_candidate_inventory_v0_1.py",
        "policy_version": "RANK_TARGET_POLICY_V0_2.md",
        "source_entry_count": len(entry_rows),
        "phrase_definition_count": len(phrase_texts),
        "grade_candidate_occurrences": grade_occurrence_count,
        "context_note_occurrences": note_occurrence_count,
        "entries_with_earliest_lexical_candidate": sum(1 for row in summary_rows if row["earliest_lexical_grade_candidate"]),
        "entries_without_exact_candidate_hit": sum(1 for row in summary_rows if not row["earliest_lexical_grade_candidate"]),
        "rank_assignments": 0,
        "auto_accepted": 0,
        "inputs": inputs,
        "outputs": {name: sha256(OUTPUT_DIR / name) for name in OUTPUT_FILES},
        "limits": [
            "The source-defined cue examples are illustrative, not exhaustive.",
            "Earliest lexical occurrence is not necessarily the first complete grade-bearing phrase.",
            "Context-note relations and target rank are not inferred from occurrences.",
            "Counts are not labels, coverage, precision, recall, or model performance.",
            "The local extraction omits the opening rank introduction and excludes nonempty unnumbered chunks from this entry index.",
        ],
    }
    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    manifest_path = OUTPUT_DIR / "MANIFEST.json"
    manifest_path.write_bytes(manifest_bytes)
    (OUTPUT_DIR / "MANIFEST.sha256").write_text(
        f"{hashlib.sha256(manifest_bytes).hexdigest()}  MANIFEST.json\n",
        encoding="ascii", newline="\n",
    )
    print(json.dumps({
        "output_dir": str(OUTPUT_DIR),
        "source_entries": len(entry_rows),
        "phrase_definitions": len(phrase_texts),
        "grade_candidate_occurrences": grade_occurrence_count,
        "context_note_occurrences": note_occurrence_count,
        "entries_with_earliest_candidate": manifest["entries_with_earliest_lexical_candidate"],
        "entries_without_exact_candidate_hit": manifest["entries_without_exact_candidate_hit"],
        "rank_assignments": 0,
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
    }, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
