#!/usr/bin/env python3
"""Audit exact duplicate quotation structures in the HadithDB extraction.

Descriptive only: does not infer speaker identity, statement subject, group-key
meaning, or Evaluative Stance Analysis labels. Inputs are read-only.

Usage:
  python dataset_discovery/hadithdb/audit_duplicate_structure.py data/interim/hadithdb_quote_occurrences.csv data/raw/hadithdb/narrators_db.json --out-dir data/interim/hadithdb_structure_audit
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

TASHKEEL_RE = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")
WHITESPACE_RE = re.compile(r"\s+")


def clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def normalize_for_literal_search(value: str) -> str:
    """Normalize only for a literal-presence signal, never for identity matching."""
    value = unicodedata.normalize("NFKC", value)
    value = value.replace("\u0640", "")
    value = TASHKEEL_RE.sub("", value)
    return WHITESPACE_RE.sub(" ", value).strip()


def record_group_map(root: dict[str, Any]) -> dict[str, dict[str, list[str]]]:
    result = {}
    for record_id, record in root.items():
        if not isinstance(record, dict):
            continue
        data = record.get("data", {})
        if not isinstance(data, dict):
            continue
        groups = data.get("الجرح والتعديل", {})
        if not isinstance(groups, dict):
            continue
        result[str(record_id)] = {
            str(label): values if isinstance(values, list)
            else ([values] if isinstance(values, str) else [])
            for label, values in groups.items()
        }
    return result


def classify_pattern(record_ids, group_pairs, same_group_excess):
    has_multi_group_record = any(
        sum(1 for rid, _ in group_pairs if rid == record_id) > 1
        for record_id in record_ids
    )
    if len(record_ids) > 1 and has_multi_group_record:
        return "mixed_within_and_cross_record"
    if len(record_ids) > 1:
        return "cross_record"
    if len(group_pairs) > 1:
        return "within_record_multi_group"
    if same_group_excess:
        return "within_record_same_group"
    return "other"


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_csv", type=Path)
    parser.add_argument("input_json", type=Path)
    parser.add_argument("--out-dir", type=Path, default=Path("data/interim/hadithdb_structure_audit"))
    parser.add_argument("--sample-size", type=int, default=100)
    args = parser.parse_args()

    with args.input_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise SystemExit("Input CSV contains no data rows.")

    required = {
        "source_record_id", "source_group_label", "quotation_index_within_group",
        "raw_quote_text", "json_pointer", "cited_work_title_raw",
        "cited_volume_page_raw",
    }
    missing = required - set(rows[0])
    if missing:
        raise SystemExit(f"Missing required CSV columns: {sorted(missing)}")

    raw_bytes = args.input_json.read_bytes()
    root = json.loads(raw_bytes.decode("utf-8-sig"))
    if not isinstance(root, dict):
        raise SystemExit("Expected narrator JSON root to be an object keyed by record ID.")
    groups_by_record = record_group_map(root)

    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    # Validate extracted occurrence coordinates against the original JSON.
    pointer_checks = Counter()
    record_name_mismatches = []
    for row in rows:
        rid = clean(row["source_record_id"])
        label = clean(row["source_group_label"])
        quote = row["raw_quote_text"]
        try:
            index = int(row["quotation_index_within_group"])
            source_quote = groups_by_record[rid][label][index]
            pointer_checks["matched" if source_quote == quote else "quote_mismatch"] += 1
        except (KeyError, IndexError, TypeError, ValueError):
            pointer_checks["location_missing"] += 1

        record = root.get(rid, {})
        source_name = clean(record.get("name")) if isinstance(record, dict) else ""
        extracted_name = clean(row.get("raw_narrator_display_name"))
        if source_name and extracted_name and source_name != extracted_name:
            record_name_mismatches.append({
                "source_record_id": rid,
                "json_name": source_name,
                "csv_name": extracted_name,
            })

    # Duplicate identity uses exact raw quote text; no normalization is applied.
    by_quote = defaultdict(list)
    for row in rows:
        by_quote[row["raw_quote_text"]].append(row)

    duplicate_clusters = []
    occurrence_examples = []
    pattern_counts = Counter()
    duplicate_cluster_occurrences = 0
    within_record_multi_group_clusters = 0
    cross_record_clusters = 0
    same_record_same_group_clusters = 0
    group_key_literal_hits = 0
    group_key_literal_tests = 0

    for quote, occurrences in by_quote.items():
        if len(occurrences) < 2:
            continue

        record_ids = {clean(x["source_record_id"]) for x in occurrences}
        group_pairs = {
            (clean(x["source_record_id"]), clean(x["source_group_label"]))
            for x in occurrences
        }
        pair_counts = Counter(
            (clean(x["source_record_id"]), clean(x["source_group_label"]))
            for x in occurrences
        )
        same_group_excess = sum(n - 1 for n in pair_counts.values() if n > 1)
        pattern = classify_pattern(record_ids, group_pairs, same_group_excess)
        pattern_counts[pattern] += 1
        duplicate_cluster_occurrences += len(occurrences)

        if pattern in {"within_record_multi_group", "mixed_within_and_cross_record"}:
            within_record_multi_group_clusters += 1
        if len(record_ids) > 1:
            cross_record_clusters += 1
        if same_group_excess:
            same_record_same_group_clusters += 1

        works = {clean(x["cited_work_title_raw"]) for x in occurrences if clean(x["cited_work_title_raw"])}
        locators = {clean(x["cited_volume_page_raw"]) for x in occurrences if clean(x["cited_volume_page_raw"])}
        pointers = [clean(x["json_pointer"]) for x in occurrences]

        duplicate_clusters.append({
            "frequency": len(occurrences),
            "distinct_record_ids": len(record_ids),
            "distinct_record_group_pairs": len(group_pairs),
            "distinct_group_labels": len({label for _, label in group_pairs}),
            "distinct_cited_work_titles": len(works),
            "distinct_volume_page_locators": len(locators),
            "same_record_same_group_excess_occurrences": same_group_excess,
            "pattern": pattern,
            "source_record_ids_json": json.dumps(sorted(record_ids), ensure_ascii=False),
            "group_pairs_json": json.dumps(sorted([list(x) for x in group_pairs]), ensure_ascii=False),
            "cited_work_titles_json": json.dumps(sorted(works), ensure_ascii=False),
            "locators_json": json.dumps(sorted(locators), ensure_ascii=False),
            "json_pointers_json": json.dumps(pointers, ensure_ascii=False),
            "raw_quote_text": quote,
        })

        normalized_quote = normalize_for_literal_search(quote)
        for occurrence in occurrences:
            label = clean(occurrence["source_group_label"])
            normalized_label = normalize_for_literal_search(label)
            literal_hit = bool(normalized_label and normalized_label in normalized_quote)
            group_key_literal_tests += 1
            group_key_literal_hits += int(literal_hit)
            occurrence_examples.append({
                "frequency": len(occurrences),
                "pattern": pattern,
                "source_record_id": clean(occurrence["source_record_id"]),
                "source_group_label": label,
                "literal_group_label_found_in_quote": literal_hit,
                "cited_work_title_raw": clean(occurrence["cited_work_title_raw"]),
                "cited_volume_page_raw": clean(occurrence["cited_volume_page_raw"]),
                "json_pointer": clean(occurrence["json_pointer"]),
                "raw_quote_text": quote,
            })

    duplicate_clusters.sort(key=lambda x: (-int(x["frequency"]), x["pattern"], x["raw_quote_text"]))
    occurrence_examples.sort(key=lambda x: (-int(x["frequency"]), x["source_record_id"], x["source_group_label"]))

    write_csv(
        out / "duplicate_structure_patterns.csv",
        [
            "frequency", "distinct_record_ids", "distinct_record_group_pairs",
            "distinct_group_labels", "distinct_cited_work_titles",
            "distinct_volume_page_locators", "same_record_same_group_excess_occurrences",
            "pattern", "source_record_ids_json", "group_pairs_json",
            "cited_work_titles_json", "locators_json", "json_pointers_json",
            "raw_quote_text",
        ],
        duplicate_clusters,
    )
    write_csv(
        out / "duplicate_group_key_examples.csv",
        [
            "frequency", "pattern", "source_record_id", "source_group_label",
            "literal_group_label_found_in_quote", "cited_work_title_raw",
            "cited_volume_page_raw", "json_pointer", "raw_quote_text",
        ],
        occurrence_examples,
    )

    # Rank biographical records by repeated exact text across group labels.
    record_group_counts = Counter()
    record_quote_counts = defaultdict(Counter)
    record_quote_groups = defaultdict(lambda: defaultdict(set))
    record_names = {}
    for rid, groups in groups_by_record.items():
        record_group_counts[rid] = len(groups)
        record = root.get(rid, {})
        record_names[rid] = clean(record.get("name")) if isinstance(record, dict) else ""
        for label, quotes in groups.items():
            for quote in quotes:
                record_quote_counts[rid][quote] += 1
                record_quote_groups[rid][quote].add(label)

    record_profiles = []
    for rid, quote_counter in record_quote_counts.items():
        repeated = [q for q, n in quote_counter.items() if n > 1]
        multi_group = [q for q in repeated if len(record_quote_groups[rid][q]) > 1]
        examples = [
            {
                "frequency": quote_counter[q],
                "group_labels": sorted(record_quote_groups[rid][q]),
                "quote_preview": q[:350],
            }
            for q in sorted(multi_group, key=lambda q: (-quote_counter[q], q))[:5]
        ]
        record_profiles.append({
            "source_record_id": rid,
            "source_record_name": record_names.get(rid, ""),
            "group_count": record_group_counts[rid],
            "quote_occurrences_in_record": sum(quote_counter.values()),
            "unique_exact_quotes_in_record": len(quote_counter),
            "repeated_exact_quote_strings_in_record": len(repeated),
            "exact_quotes_repeated_across_multiple_group_labels": len(multi_group),
            "largest_same_quote_frequency_in_record": max(quote_counter.values(), default=0),
            "examples_json": json.dumps(examples, ensure_ascii=False),
        })
    record_profiles.sort(key=lambda x: (
        -int(x["exact_quotes_repeated_across_multiple_group_labels"]),
        -int(x["group_count"]), x["source_record_id"]
    ))
    write_csv(
        out / "record_group_semantics_sample.csv",
        [
            "source_record_id", "source_record_name", "group_count",
            "quote_occurrences_in_record", "unique_exact_quotes_in_record",
            "repeated_exact_quote_strings_in_record",
            "exact_quotes_repeated_across_multiple_group_labels",
            "largest_same_quote_frequency_in_record", "examples_json",
        ],
        record_profiles[:max(args.sample_size, 1)],
    )

    summary = {
        "input_csv": str(args.input_csv),
        "input_json": str(args.input_json),
        "input_json_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "extracted_quote_occurrences": len(rows),
        "source_records_with_quote_groups": len(groups_by_record),
        "json_pointer_validation": dict(pointer_checks),
        "record_name_mismatch_count": len(record_name_mismatches),
        "unique_exact_quote_strings": len(by_quote),
        "duplicate_exact_quote_clusters": len(duplicate_clusters),
        "occurrences_in_duplicate_clusters": duplicate_cluster_occurrences,
        "duplicate_cluster_pattern_counts": dict(pattern_counts),
        "clusters_repeated_across_multiple_group_labels_within_a_record": within_record_multi_group_clusters,
        "clusters_spanning_multiple_source_records": cross_record_clusters,
        "clusters_with_repetition_inside_same_record_and_group": same_record_same_group_clusters,
        "group_label_literal_presence_checks": {
            "occurrence_checks": group_key_literal_tests,
            "literal_substring_hits": group_key_literal_hits,
            "interpretation": "String-presence signal only; not speaker attribution or entity resolution.",
        },
        "record_profiles_generated": len(record_profiles),
        "record_profiles_written": min(len(record_profiles), max(args.sample_size, 1)),
        "warnings": [
            "Duplicate identity uses exact raw quotation text; no quote normalization is used.",
            "Repeated occurrences are not automatically errors or independent judgements.",
            "Group-label substring matches are not proof of speaker identity or resolved person identity.",
            "Record ID identifies the biography record containing a quote, not necessarily every statement subject.",
            "No group-key semantic types, speaker attributions, statement types, or ESA stances are inferred.",
        ],
    }
    with (out / "duplicate_structure_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)

    report = [
        "# HadithDB duplicate-structure audit",
        "",
        f"- Extracted quotation occurrences: **{len(rows):,}**",
        f"- Unique exact quotation strings: **{len(by_quote):,}**",
        f"- Duplicate exact-text clusters: **{len(duplicate_clusters):,}**",
        f"- Occurrences in duplicate clusters: **{duplicate_cluster_occurrences:,}**",
        "",
        "## Duplicate cluster patterns",
        "",
    ]
    for pattern, count in pattern_counts.most_common():
        report.append(f"- {pattern}: {count:,} clusters")
    report += [
        "",
        "## Structural validation",
        "",
        f"- JSON pointer checks: {dict(pointer_checks)}",
        f"- Extracted/source record-name mismatches: {len(record_name_mismatches):,}",
        "",
        "## Group-label literal-presence check",
        "",
        f"- Literal substring hits: {group_key_literal_hits:,} / {group_key_literal_tests:,} occurrence checks",
        "- This is a string-presence signal after conservative Unicode, diacritic, and whitespace normalization. It is not evidence of speaker identity or resolved person identity.",
        "",
        "## Interpretation",
        "",
        "- within_record_multi_group: exact text occurs under multiple group labels within one biographical record.",
        "- cross_record: exact text occurs in more than one biographical record.",
        "- mixed_within_and_cross_record: a cluster spans records and has multiple labels within at least one record.",
        "- within_record_same_group: repeated exact text occurs more than once under one record/group pair.",
        "- These categories describe storage patterns only; they do not establish why the source repeated the text.",
        "- Do not automatically deduplicate, discard occurrences, infer speaker identities, or assign ESA labels from these results.",
        "",
        "## Output files",
        "",
        "- duplicate_structure_summary.json: machine-readable summary.",
        "- duplicate_structure_patterns.csv: one row per repeated exact quotation string.",
        "- duplicate_group_key_examples.csv: occurrence-level details for repeated strings.",
        "- record_group_semantics_sample.csv: records ranked by cross-group exact repetition.",
        "",
    ]
    (out / "PROFILE_REPORT.md").write_text("\n".join(report), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\noutput_dir={out.resolve()}")


if __name__ == "__main__":
    main()
