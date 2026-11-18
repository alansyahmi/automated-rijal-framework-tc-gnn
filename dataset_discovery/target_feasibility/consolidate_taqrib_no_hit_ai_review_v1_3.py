#!/usr/bin/env python3
"""Validate and consolidate the disjoint no-hit AI review worksheets."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PIPELINE = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline"
PACKAGE_DIR = PIPELINE / "rank_label_no_hit_ai_review_v1_2026-11-15"
OUTPUT_DIR = PACKAGE_DIR / "CONSOLIDATED_V1_3"
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
ALLOWED_STATUS = {"candidate", "conditional", "unresolved", "no_candidate"}
ALLOWED_TYPES = {
    "standardized_grade", "specialized_evaluation", "status_or_biography",
    "non_grade_description", "uncertain",
}
ALLOWED_CONFIDENCE = {"high", "moderate", "low"}
ALLOWED_RANKS = {str(rank) for rank in range(1, 13)} | {
    "unresolved", "not_applicable", "conditional"
}


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


def exact_substring_errors(row: dict[str, str], line_label: str) -> list[str]:
    text = row["entry_text_verbatim"]
    errors = []
    span = row["ai_first_grade_span_exact"]
    if span not in {"none_found", ""}:
        candidate = span[len("uncertain: "):].strip() if span.startswith("uncertain: ") else span
        if candidate and candidate not in text:
            errors.append(f"{line_label}: first-grade span is not an exact source substring")
    qualifier = row["ai_attached_qualifier_exact"]
    if qualifier not in {"none_observed", "", "uncertain"} and qualifier not in text:
        errors.append(f"{line_label}: qualifier is not an exact source substring")
    notes = row["ai_context_note_spans_exact"]
    if notes not in {"none_observed", "", "uncertain"}:
        for item in notes.split(" || "):
            candidate = item.strip()
            if candidate and candidate not in text:
                errors.append(f"{line_label}: context note is not an exact source substring: {candidate!r}")
    return errors


def main() -> None:
    if OUTPUT_DIR.exists():
        raise SystemExit(f"Refusing to overwrite consolidated results: {OUTPUT_DIR}")
    batch_manifest = json.loads((PACKAGE_DIR / "MANIFEST.json").read_text(encoding="utf-8"))
    all_rows: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    errors: list[str] = []
    batch_summaries = []
    result_paths = []
    for index in range(1, int(batch_manifest["batch_count"]) + 1):
        stem = f"BATCH_{index:02d}"
        source_path = PACKAGE_DIR / f"{stem}_INPUT.csv"
        result_path = PACKAGE_DIR / f"{stem}_AI_REVIEW.csv"
        source_fields, source_rows = read_csv(source_path)
        result_fields, result_rows = read_csv(result_path)
        expected_fields = SOURCE_FIELDS + REVIEW_FIELDS
        if source_fields != SOURCE_FIELDS:
            errors.append(f"{stem}: source input headers differ from schema")
        if result_fields != expected_fields:
            errors.append(f"{stem}: result headers differ from schema")
        if len(result_rows) != len(source_rows):
            errors.append(f"{stem}: output row count {len(result_rows)} != input {len(source_rows)}")
        source_by_id = {row["entry_id"]: row for row in source_rows}
        batch_candidate_count = 0
        for row_num, row in enumerate(result_rows, start=2):
            label = f"{stem} CSV row {row_num}"
            entry_id = row.get("entry_id", "")
            if entry_id in seen_ids:
                errors.append(f"{label}: duplicate entry_id across batches: {entry_id}")
            seen_ids.add(entry_id)
            source_row = source_by_id.get(entry_id)
            if source_row is None:
                errors.append(f"{label}: entry_id not present in its input batch: {entry_id}")
            elif any(row.get(field, "") != source_row.get(field, "") for field in SOURCE_FIELDS):
                errors.append(f"{label}: source fields changed for {entry_id}")
            for field in REVIEW_FIELDS:
                if not row.get(field, "").strip():
                    errors.append(f"{label}: blank required review field {field}")
            if row.get("ai_status") not in ALLOWED_STATUS:
                errors.append(f"{label}: invalid ai_status {row.get('ai_status')!r}")
            if row.get("ai_phrase_type") not in ALLOWED_TYPES:
                errors.append(f"{label}: invalid ai_phrase_type {row.get('ai_phrase_type')!r}")
            if row.get("ai_confidence") not in ALLOWED_CONFIDENCE:
                errors.append(f"{label}: invalid ai_confidence {row.get('ai_confidence')!r}")
            if row.get("ai_rank_candidate_1_to_12") not in ALLOWED_RANKS:
                errors.append(f"{label}: invalid rank candidate {row.get('ai_rank_candidate_1_to_12')!r}")
            errors.extend(exact_substring_errors(row, label))
            if row.get("ai_status") == "candidate":
                batch_candidate_count += 1
        all_rows.extend(result_rows)
        result_paths.append(result_path)
        batch_summaries.append({
            "batch": stem,
            "input_rows": len(source_rows),
            "result_rows": len(result_rows),
            "candidate_status_rows": batch_candidate_count,
        })

    if len(seen_ids) != batch_manifest["source_entry_count"]:
        errors.append(f"Unique reviewed ID count {len(seen_ids)} != manifest count {batch_manifest['source_entry_count']}")
    if errors:
        print("Validation failed; no consolidated outputs written.")
        for error in errors[:100]:
            print(error)
        if len(errors) > 100:
            print(f"... plus {len(errors) - 100} more errors")
        raise SystemExit(1)

    all_rows.sort(key=lambda row: row["entry_id"])
    rank_counts = Counter(row["ai_rank_candidate_1_to_12"] for row in all_rows)
    status_counts = Counter(row["ai_status"] for row in all_rows)
    type_counts = Counter(row["ai_phrase_type"] for row in all_rows)
    phrase_counts: Counter[str] = Counter()
    uncertain_phrase_counts: Counter[str] = Counter()
    phrase_groups: dict[str, list[dict[str, str]]] = {}
    for row in all_rows:
        value = row["ai_first_grade_span_exact"]
        if value in {"none_found", ""}:
            continue
        uncertain = value.startswith("uncertain: ")
        phrase = value[len("uncertain: "):].strip() if uncertain else value.strip()
        phrase_counts[phrase] += 1
        phrase_groups.setdefault(phrase, []).append(row)
        if uncertain:
            uncertain_phrase_counts[phrase] += 1
    OUTPUT_DIR.mkdir(parents=True)
    consolidated_path = OUTPUT_DIR / "AI_REVIEW_ALL_1211.csv"
    phrase_path = OUTPUT_DIR / "AI_DISCOVERED_FIRST_PHRASE_FREQUENCIES.csv"
    index_path = OUTPUT_DIR / "AI_FIRST_PHRASE_REVIEW_INDEX.csv"
    write_csv(consolidated_path, all_rows, SOURCE_FIELDS + REVIEW_FIELDS)
    phrase_rows = [
        {
            "phrase_text_trimmed_for_grouping": phrase,
            "entry_count": count,
            "uncertain_status_count": uncertain_phrase_counts[phrase],
            "status": "provisional_ai_candidate",
        }
        for phrase, count in sorted(phrase_counts.items(), key=lambda item: (-item[1], item[0]))
    ]
    write_csv(phrase_path, phrase_rows, ["phrase_text_trimmed_for_grouping", "entry_count", "uncertain_status_count", "status"])
    phrase_index_rows = []
    for phrase, group in sorted(phrase_groups.items(), key=lambda item: (-len(item[1]), item[0])):
        status_counts_for_phrase = Counter(row["ai_status"] for row in group)
        rank_counts_for_phrase = Counter(row["ai_rank_candidate_1_to_12"] for row in group)
        type_counts_for_phrase = Counter(row["ai_phrase_type"] for row in group)
        examples = sorted(group, key=lambda row: row["entry_id"])[:3]
        record = {
            "phrase_text_trimmed_for_grouping": phrase,
            "entry_count": len(group),
            "uncertain_status_count": uncertain_phrase_counts[phrase],
            "ai_status_counts": ";".join(f"{key}:{value}" for key, value in sorted(status_counts_for_phrase.items())),
            "rank_suggestion_counts_unverified": ";".join(f"{key}:{value}" for key, value in sorted(rank_counts_for_phrase.items())),
            "phrase_type_counts": ";".join(f"{key}:{value}" for key, value in sorted(type_counts_for_phrase.items())),
        }
        for example_index in range(1, 4):
            example = examples[example_index - 1] if len(examples) >= example_index else {}
            record[f"example_{example_index}_entry_id"] = example.get("entry_id", "")
            record[f"example_{example_index}_entry_text"] = example.get("entry_text_verbatim", "")
        phrase_index_rows.append(record)
    index_fields = [
        "phrase_text_trimmed_for_grouping", "entry_count", "uncertain_status_count", "ai_status_counts",
        "rank_suggestion_counts_unverified", "phrase_type_counts",
        "example_1_entry_id", "example_1_entry_text", "example_2_entry_id", "example_2_entry_text",
        "example_3_entry_id", "example_3_entry_text",
    ]
    write_csv(index_path, phrase_index_rows, index_fields)
    report = [
        "# Taqrīb no-hit AI review v1: consolidated provisional findings",
        "",
        f"Reviewed rows: {len(all_rows):,} of {batch_manifest['source_entry_count']:,} no-exact-inventory-hit entries, across {len(batch_summaries)} disjoint batches.",
        "",
        "## AI review status counts",
        "",
        *[f"- `{key}`: {value:,}" for key, value in sorted(status_counts.items())],
        "",
        "## Phrase-type counts",
        "",
        *[f"- `{key}`: {value:,}" for key, value in sorted(type_counts.items())],
        "",
        "## Rank-candidate counts (unverified AI suggestions)",
        "",
        *[f"- `{key}`: {value:,}" for key, value in sorted(rank_counts.items())],
        "",
        f"Distinct phrase strings proposed: {len(phrase_counts):,}; aggregation removes the `uncertain: ` marker and trims surrounding whitespace only. The row-level review file preserves each exact extracted span. See `AI_DISCOVERED_FIRST_PHRASE_FREQUENCIES.csv` and the sample-backed `AI_FIRST_PHRASE_REVIEW_INDEX.csv`.",
        "",
        "These are AI triage findings, not human-approved labels, taxonomy rules, or measured accuracy. Entries were selected because the current exact phrase inventory had no hit; the review may still miss specialized terms or misread constructions. Rank definitions with external evidence requirements remain conditional or unresolved. The results do not establish identity, attribution, historical accuracy, narrator reliability, or target eligibility.",
        "",
    ]
    report_path = OUTPUT_DIR / "REVIEW_SUMMARY.md"
    report_path.write_text("\n".join(report), encoding="utf-8", newline="\n")
    output_files = [consolidated_path, phrase_path, index_path, report_path]
    manifest = {
        "package": "Taqrib no-hit AI review v1 consolidated results",
        "status": "provisional AI review suggestions; no human-approved labels",
        "source_entry_count": len(all_rows),
        "unique_entry_ids": len(seen_ids),
        "all_source_columns_preserved": True,
        "exact_span_containment_checked": True,
        "batch_results": batch_summaries,
        "prep_manifest_sha256": sha256(PACKAGE_DIR / "MANIFEST.json"),
        "pre_review_template_hashes": batch_manifest["package_files"],
        "review_result_hashes": {
            str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path)
            for path in result_paths
        },
        "outputs": {path.name: sha256(path) for path in output_files},
        "rank_candidate_counts": dict(rank_counts),
        "status_counts": dict(status_counts),
        "phrase_type_counts": dict(type_counts),
        "limitations": [
            "AI suggestions are not expert or human annotations.",
            "No-hit status meant no exact match against an incomplete inventory; it did not imply no grade wording.",
            "Exact span validation checks string containment only, not semantic correctness.",
            "Counts are triage counts, not corpus prevalence, coverage, precision, recall, or model performance.",
        ],
    }
    raw = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    (OUTPUT_DIR / "REVIEW_RESULTS_MANIFEST.json").write_bytes(raw)
    (OUTPUT_DIR / "REVIEW_RESULTS_MANIFEST.sha256").write_text(
        f"{hashlib.sha256(raw).hexdigest()}  REVIEW_RESULTS_MANIFEST.json\n",
        encoding="ascii", newline="\n",
    )
    print(json.dumps({
        "output_dir": str(OUTPUT_DIR),
        "entries": len(all_rows),
        "unique_entry_ids": len(seen_ids),
        "status_counts": dict(status_counts),
        "phrase_type_counts": dict(type_counts),
        "rank_candidate_counts": dict(rank_counts),
        "distinct_first_phrase_values": len(phrase_counts),
    }, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
