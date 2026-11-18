#!/usr/bin/env python3
"""Prepare a reproducible, candidate-only AI review of Taqrib no-hit entries."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PIPELINE = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline"
INVENTORY_DIR = PIPELINE / "rank_label_candidate_inventory_v0_2_2026-11-15"
OUTPUT_DIR = PIPELINE / "rank_label_no_hit_ai_review_v1_2026-11-15"
BATCH_COUNT = 3

SOURCE_FIELDS = [
    "entry_id", "local_book_id", "shamela_book_id", "local_page_id",
    "shamela_page_id", "printed_page_num", "entry_number_verbatim",
    "entry_text_verbatim",
]
REVIEW_FIELDS = [
    "ai_first_grade_span_exact", "ai_rank_candidate_1_to_12",
    "ai_phrase_type", "ai_attached_qualifier_exact",
    "ai_context_note_spans_exact", "ai_context_note_types",
    "ai_status", "ai_confidence", "ai_reason",
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


def main() -> None:
    if OUTPUT_DIR.exists():
        raise SystemExit(f"Refusing to overwrite existing review package: {OUTPUT_DIR}")
    summary_path = INVENTORY_DIR / "ENTRY_FIRST_CANDIDATE_SUMMARY.csv"
    _, summary = read_csv(summary_path)
    no_hit = [row for row in summary if row["candidate_status"] == "no_exact_inventory_candidate_hit"]
    # Longest-processing-first balances estimated reading load deterministically.
    no_hit.sort(key=lambda row: (-len(row["entry_text_verbatim"]), row["entry_id"]))
    batches: list[list[dict[str, str]]] = [[] for _ in range(BATCH_COUNT)]
    batch_char_load = [0] * BATCH_COUNT
    for row in no_hit:
        batch_index = min(range(BATCH_COUNT), key=lambda i: (batch_char_load[i], i))
        batches[batch_index].append(row)
        batch_char_load[batch_index] += len(row["entry_text_verbatim"])

    OUTPUT_DIR.mkdir(parents=True)
    batch_files: dict[str, str] = {}
    for index, batch in enumerate(batches, start=1):
        batch.sort(key=lambda row: row["entry_id"])
        stem = f"BATCH_{index:02d}"
        input_name = f"{stem}_INPUT.csv"
        output_name = f"{stem}_AI_REVIEW.csv"
        source_rows = [{field: row.get(field, "") for field in SOURCE_FIELDS} for row in batch]
        write_csv(OUTPUT_DIR / input_name, source_rows, SOURCE_FIELDS)
        review_rows = []
        for row in source_rows:
            review_rows.append({**row, **{field: "" for field in REVIEW_FIELDS}})
        write_csv(OUTPUT_DIR / output_name, review_rows, SOURCE_FIELDS + REVIEW_FIELDS)
        batch_files[input_name] = sha256(OUTPUT_DIR / input_name)
        batch_files[output_name] = sha256(OUTPUT_DIR / output_name)

    protocol = """# AI review instructions: entries with no exact inventory hit

This is a candidate-discovery review of the complete local Arabic entry strings. These rows had no exact hit in the current phrase inventory. That does not mean they lack an evaluative phrase.

For every row, complete the matching `BATCH_NN_AI_REVIEW.csv` and preserve all source columns byte-for-byte at the text level. Use only the entry text and repository's `IBN_HAJAR_12_RANK_SOURCE_INVENTORY_V0.md` plus `RANK_TARGET_POLICY_V0_2.md` as the rank framework. Do not use earlier annotations or external biographical claims.

## Output fields

- `ai_first_grade_span_exact`: exact contiguous substring of the entry text for the first complete grade-bearing/evaluative phrase. Use `none_found` if none; use `uncertain: <exact candidate substring>` if unsure.
- `ai_rank_candidate_1_to_12`: a rank number only when the wording and the source definition support it; otherwise `unresolved`, `not_applicable`, or `conditional`.
- `ai_phrase_type`: `standardized_grade`, `specialized_evaluation`, `status_or_biography`, `non_grade_description`, or `uncertain`.
- `ai_attached_qualifier_exact`: exact contiguous qualification attached to the candidate, `none_observed`, or `uncertain`.
- `ai_context_note_spans_exact`: exact relevant note spans, separated by ` || `; use `none_observed` if none. Do not invent fine-grained affiliation labels.
- `ai_context_note_types`: broad terms such as `memory_or_transmission`, `attribution`, `affiliation_or_innovation`, `biographical`, `generation`, or `other`; use `none` if none.
- `ai_status`: `candidate`, `conditional`, `unresolved`, or `no_candidate`.
- `ai_confidence`: `high`, `moderate`, or `low`.
- `ai_reason`: short reason tied to wording and the rank definition; state missing conditions.

Do not turn a lexical cue into a rank when the definition needs evidence not present in the entry. In particular, rank 6, 7, 8, 9, 10, 11, and 12 have context or evidence distinctions; the source inventory describes them. Keep rank 1 status separate from ordinary grade. Preserve the full first phrase and qualifications. Do not normalize Arabic, rewrite the entry, or assign a final label.

All results are AI suggestions for human review. They do not establish historical attribution, identity, target eligibility, accuracy, or annotation reliability.
"""
    (OUTPUT_DIR / "AI_REVIEW_INSTRUCTIONS.md").write_text(protocol, encoding="utf-8", newline="\n")
    readme = f"""# Taqrīb no-hit AI review v1

This package assigns the {len(no_hit):,} numbered entries with no exact phrase-inventory hit to three disjoint, reproducible AI-review batches. It is intended to discover missed specialized wording and context notes. It does not assign production labels.

Batch row counts: {', '.join(str(len(batch)) for batch in batches)}. Estimated text-character loads: {', '.join(str(value) for value in batch_char_load)}.

See `AI_REVIEW_INSTRUCTIONS.md`. The source phrase inventory and review policy are linked by the manifest. Reviewer outputs are provisional suggestions requiring human review.
"""
    (OUTPUT_DIR / "README.md").write_text(readme, encoding="utf-8", newline="\n")
    input_paths = [
        summary_path,
        INVENTORY_DIR / "PHRASE_INVENTORY.csv",
        PIPELINE / "IBN_HAJAR_12_RANK_SOURCE_INVENTORY_V0.md",
        PIPELINE / "RANK_TARGET_POLICY_V0_2.md",
    ]
    package_files = [*batch_files, "AI_REVIEW_INSTRUCTIONS.md", "README.md"]
    manifest = {
        "package": "Taqrib no-hit AI review v1",
        "date": "2026-11-15",
        "status": "candidate discovery only; AI suggestions are not labels",
        "source_entry_count": len(no_hit),
        "batch_count": BATCH_COUNT,
        "batch_row_counts": [len(batch) for batch in batches],
        "batch_character_loads": batch_char_load,
        "partition_method": "deterministic longest-processing-first by source-text character count; tie break by entry_id then batch number",
        "source_entry_ids_unique": len({row["entry_id"] for row in no_hit}) == len(no_hit),
        "inputs": {str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path) for path in input_paths},
        "package_files": {name: sha256(OUTPUT_DIR / name) for name in package_files},
        "review_output_hashes": "to be recorded after AI review outputs are completed",
        "limitations": [
            "No-hit means no exact match to the current incomplete phrase inventory, not no grade wording.",
            "AI review can miss wording or misread Arabic; outputs are provisional suggestions.",
            "No ranks, labels, source corrections, identity decisions, or eligibility decisions are authorized by this package.",
            "The local text corpus is an edition-aligned digital transcription, not direct verification against the printed pages.",
        ],
    }
    raw = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    (OUTPUT_DIR / "MANIFEST.json").write_bytes(raw)
    (OUTPUT_DIR / "MANIFEST.sha256").write_text(
        f"{hashlib.sha256(raw).hexdigest()}  MANIFEST.json\n", encoding="ascii", newline="\n"
    )
    print(json.dumps({
        "output_dir": str(OUTPUT_DIR),
        "entries": len(no_hit),
        "batch_rows": [len(batch) for batch in batches],
        "batch_char_loads": batch_char_load,
        "unique_entry_ids": len({row["entry_id"] for row in no_hit}),
    }, indent=2))


if __name__ == "__main__":
    main()
