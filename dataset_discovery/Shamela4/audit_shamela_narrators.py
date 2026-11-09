#!/usr/bin/env python3
"""Read-only structural audit and export for Shamela4 narrator Parquet.

Requires pyarrow. Run from repository root:
python dataset_discovery/Shamela4/audit_shamela_narrators.py data/1_raw/Shamela4_Full_DB/_meta/narrators.parquet

The script preserves source text and every quotation occurrence. It does not
infer the true historical speaker or silently deduplicate records.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import pyarrow.parquet as pq
except ImportError:
    raise SystemExit("Missing dependency. Install with: python -m pip install pyarrow")

BIO_FIELDS = [
    "النسب", "الكنية", "تاريخ الوفاة", "الرتبة عند ابن حجر",
    "طبقة رواة التقريب", "علاقات الراوي", "الرتبة عند الذهبي",
    "بلد الإقامة", "بلد الوفاة", "اللقب", "بلد الرحلة", "تاريخ الميلاد",
    "الشهرة", "المذهب العقدي", "بلد الميلاد", "تاريخ الرحلة",
]


def as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def parse_json(value: Any) -> tuple[Any, str]:
    if value is None:
        return None, "null"
    if isinstance(value, (dict, list)):
        return value, "already_nested"
    if not isinstance(value, str):
        return None, "unexpected_type:" + type(value).__name__
    try:
        return json.loads(value), "valid"
    except Exception as exc:
        return None, "invalid_json:" + type(exc).__name__


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: as_text(row.get(key)) for key in fields})


def normalise_title(citation: Any) -> str:
    value = as_text(citation).strip()
    value = re.sub(r"\s*[\(（]\s*\d+\s*/\s*[\d\-–—]+\s*[\)）]\s*$", "", value)
    return re.sub(r"\s+", " ", value).strip()


def parse_garh(grouped: Any, warnings: Counter) -> list[dict[str, Any]]:
    rows = []
    if grouped is None:
        return rows
    if not isinstance(grouped, dict):
        warnings["garh_not_dict:" + type(grouped).__name__] += 1
        return rows
    for group, entries in grouped.items():
        if entries is None:
            continue
        if not isinstance(entries, list):
            warnings["garh_group_not_list"] += 1
            entries = [entries]
        for index, entry in enumerate(entries):
            raw = json.dumps(entry, ensure_ascii=False, default=str)
            if isinstance(entry, (list, tuple)):
                if len(entry) >= 3:
                    quote, citation, source_id = entry[0], entry[1], entry[2]
                elif len(entry) == 2:
                    quote, citation, source_id = entry[0], entry[1], None
                    warnings["garh_entry_len_2"] += 1
                elif len(entry) == 1:
                    quote, citation, source_id = entry[0], None, None
                    warnings["garh_entry_len_1"] += 1
                else:
                    quote, citation, source_id = "", None, None
                    warnings["garh_entry_empty"] += 1
            elif isinstance(entry, dict):
                quote = entry.get("text", entry.get("quote", entry.get("نص", "")))
                citation = entry.get("source", entry.get("citation", entry.get("المصدر")))
                source_id = entry.get("source_id", entry.get("id", entry.get("رقم المصدر")))
                warnings["garh_entry_dict_shape"] += 1
            else:
                quote, citation, source_id = entry, None, None
                warnings["garh_entry_scalar_shape"] += 1
            rows.append({
                "group_label_raw": as_text(group),
                "group_entry_index": index,
                "quotation_text": as_text(quote),
                "source_citation_raw": as_text(citation),
                "source_id_raw": as_text(source_id),
                "raw_entry_json": raw,
            })
    return rows


def parse_fwaed(value: Any, warnings: Counter) -> list[dict[str, Any]]:
    rows = []
    if value is None:
        return rows
    if not isinstance(value, dict):
        warnings["fwaed_not_dict:" + type(value).__name__] += 1
        return rows
    for category, entries in value.items():
        if not isinstance(entries, list):
            warnings["fwaed_category_not_list"] += 1
            entries = [entries]
        for entry in entries:
            rows.append({
                "category_raw": as_text(category),
                "entry_json": json.dumps(entry, ensure_ascii=False, default=str),
            })
    return rows


def counter_rows(counter: Counter, key_name: str, value_name: str) -> list[dict[str, Any]]:
    return [{key_name: key, value_name: count} for key, count in counter.most_common()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Input narrators.parquet")
    parser.add_argument("--out", type=Path,
                        default=Path("data/2_interim/shamela4_narrator_audit"))
    parser.add_argument("--sample", type=int, default=50)
    parser.add_argument("--top", type=int, default=50)
    args = parser.parse_args()

    source = args.input.resolve()
    output = args.out.resolve()
    if not source.is_file():
        raise SystemExit(f"Input file not found: {source}")
    output.mkdir(parents=True, exist_ok=True)

    parquet = pq.ParquetFile(source)
    print("=" * 76)
    print("SHAMELA4 NARRATOR CORPUS AUDIT")
    print("=" * 76)
    print(f"Input: {source}")
    print(f"Bytes: {source.stat().st_size:,}")
    print(f"SHA-256: {sha256(source)}")
    print(f"Rows: {parquet.metadata.num_rows:,}")
    print(f"Row groups: {parquet.metadata.num_row_groups}")
    print(f"Columns: {parquet.metadata.num_columns}")
    print("\nPARQUET SCHEMA\n" + str(parquet.schema))
    print("\nARROW SCHEMA\n" + str(parquet.schema_arrow))

    narrator_rows = []
    eval_rows = []
    fwaed_rows = []
    quote_samples = []
    narrator_samples = []
    death_samples = []
    warnings = Counter()
    bio_status = Counter()
    criticism_status = Counter()
    bio_presence = Counter()
    evaluator_appearances = Counter()  # quotation occurrences per group
    evaluator_record_pairs = set()  # distinct narrator/group pairs
    citation_counts = Counter()  # citations, including rows without source IDs
    ibn_hajar = Counter()
    dhahabi = Counter()
    narrator_types = Counter()
    quote_occurrences = Counter()
    quote_narrators = defaultdict(set)
    quote_groups = defaultdict(set)
    quote_source_ids = defaultdict(set)
    source_id_occurrences = Counter()
    source_id_citations = defaultdict(set)
    title_source_ids = defaultdict(set)
    doc_key_counts = Counter()
    multi_group_keys = defaultdict(set)
    group_appearance_total = 0
    garh_total = 0
    fwaed_total = 0
    null_narrator_type = 0
    null_criticism = 0
    seen = 0

    for batch in parquet.iter_batches(batch_size=512):
        for record in batch.to_pylist():
            seen += 1
            narrator_id = record.get("id")
            narrator_key = as_text(narrator_id)
            bio, bio_state = parse_json(record.get("biography_text"))
            criticism, criticism_state = parse_json(record.get("criticism_text"))
            bio_status[bio_state] += 1
            criticism_status[criticism_state] += 1
            bio = bio if isinstance(bio, dict) else {}
            criticism = criticism if isinstance(criticism, dict) else {}

            if record.get("narrator_type") is None:
                null_narrator_type += 1
            else:
                narrator_types[as_text(record["narrator_type"])] += 1

            if record.get("criticism_text") is None:
                null_criticism += 1

            for field in BIO_FIELDS:
                if bio.get(field) not in (None, "", [], {}):
                    bio_presence[field] += 1
            if bio.get("الرتبة عند ابن حجر") not in (None, "", [], {}):
                ibn_hajar[as_text(bio["الرتبة عند ابن حجر"])] += 1
            if bio.get("الرتبة عند الذهبي") not in (None, "", [], {}):
                dhahabi[as_text(bio["الرتبة عند الذهبي"])] += 1

            if record.get("narrator_type") is not None and bio.get("تاريخ الوفاة") not in (None, "", [], {}) and len(death_samples) < args.sample:
                death_samples.append({
                    "id": narrator_id, "short_name": record.get("short_name"),
                    "narrator_type": record.get("narrator_type"),
                    "death_date": bio.get("تاريخ الوفاة"),
                })

            nrow = {
                "id": narrator_id, "short_name": record.get("short_name"),
                "long_name": record.get("long_name"),
                "narrator_type": record.get("narrator_type"),
                "biography_json_status": bio_state,
                "criticism_json_status": criticism_state,
                "biography_json": record.get("biography_text"),
                "criticism_json": record.get("criticism_text"),
            }
            for index, field in enumerate(BIO_FIELDS):
                nrow[f"bio_{index}"] = bio.get(field)
            narrator_rows.append(nrow)
            if len(narrator_samples) < args.sample:
                narrator_samples.append(nrow.copy())

            parsed_garh = parse_garh(criticism.get("garh"), warnings)
            for item in parsed_garh:
                garh_total += 1
                group = item["group_label_raw"]
                quote = item["quotation_text"]
                sid = item["source_id_raw"]
                citation = item["source_citation_raw"]
                title = normalise_title(citation)
                evaluator_appearances[group] += 1
                evaluator_record_pairs.add((narrator_key, group))
                quote_occurrences[quote] += 1
                quote_narrators[quote].add(narrator_key)
                quote_groups[quote].add(group)
                if sid:
                    source_id_occurrences[sid] += 1
                    quote_source_ids[quote].add(sid)
                if citation:
                    citation_counts[citation] += 1
                if sid and citation:
                    source_id_citations[sid].add(citation)
                    title_source_ids[title].add(sid)
                doc_key_counts[(narrator_key, group, quote, sid)] += 1
                multi_group_keys[(narrator_key, quote, sid)].add(group)
                eval_rows.append({
                    "narrator_id": narrator_id,
                    "short_name": record.get("short_name"),
                    "long_name": record.get("long_name"),
                    **item,
                    "normalised_title_candidate": title,
                })
                if len(quote_samples) < args.sample * 10:
                    quote_samples.append({
                        "narrator_id": narrator_id,
                        "short_name": record.get("short_name"),
                        **item,
                    })

            for item in parse_fwaed(criticism.get("fwaed"), warnings):
                fwaed_total += 1
                fwaed_rows.append({
                    "narrator_id": narrator_id,
                    "short_name": record.get("short_name"),
                    **item,
                })

    # Source ID -> citation/title mappings and collisions.
    source_rows = []
    source_id_collisions = []
    for sid, citations in sorted(source_id_citations.items()):
        titles = sorted({normalise_title(c) for c in citations})
        source_rows.append({
            "source_id": sid,
            "occurrence_count": source_id_occurrences[sid],
            "citation_variant_count": len(citations),
            "normalised_title_count": len(titles),
            "citation_variants_json": json.dumps(sorted(citations), ensure_ascii=False),
            "normalised_titles_json": json.dumps(titles, ensure_ascii=False),
        })
        if len(titles) > 1:
            source_id_collisions.append({
                "source_id": sid, "normalised_title_count": len(titles),
                "normalised_titles_json": json.dumps(titles, ensure_ascii=False),
                "citation_variants_json": json.dumps(sorted(citations), ensure_ascii=False),
            })

    title_collisions = []
    for title, ids in sorted(title_source_ids.items()):
        if len(ids) > 1:
            title_collisions.append({
                "normalised_title_candidate": title,
                "source_id_count": len(ids),
                "source_ids_json": json.dumps(sorted(ids), ensure_ascii=False),
            })

    repeated_quotes = []
    for quote, count in quote_occurrences.items():
        if count > 1:
            repeated_quotes.append({
                "quotation_text": quote, "occurrence_count": count,
                "narrator_count": len(quote_narrators[quote]),
                "group_count": len(quote_groups[quote]),
                "source_id_count": len(quote_source_ids[quote]),
            })
    repeated_quotes.sort(key=lambda row: (-row["occurrence_count"], row["quotation_text"]))

    duplicate_docs = [
        {"narrator_id": key[0], "group_label_raw": key[1],
         "quotation_text": key[2], "source_id_raw": key[3],
         "occurrence_count": count, "excess_occurrences": count - 1}
        for key, count in doc_key_counts.items() if count > 1
    ]
    duplicate_docs.sort(key=lambda row: (-row["occurrence_count"], row["narrator_id"]))

    multi_group = [
        {"narrator_id": key[0], "quotation_text": key[1], "source_id_raw": key[2],
         "group_count": len(groups),
         "group_labels_json": json.dumps(sorted(groups), ensure_ascii=False)}
        for key, groups in multi_group_keys.items() if len(groups) > 1
    ]
    multi_group.sort(key=lambda row: (-row["group_count"], row["narrator_id"]))

    summary = {
        "dataset": "AuthenticIlm/Shamela4_Full_DB",
        "input_path": str(source),
        "file_bytes": source.stat().st_size,
        "sha256": sha256(source),
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "parquet_rows": parquet.metadata.num_rows,
        "rows_iterated": seen,
        "row_groups": parquet.metadata.num_row_groups,
        "columns": parquet.metadata.num_columns,
        "biography_json_status": dict(bio_status),
        "criticism_json_status": dict(criticism_status),
        "null_narrator_type": null_narrator_type,
        "null_criticism_text": null_criticism,
        "biography_field_presence": dict(bio_presence),
        "ibn_hajar_assessment_count": sum(ibn_hajar.values()),
        "ibn_hajar_distinct_strings": len(ibn_hajar),
        "ibn_hajar_top": ibn_hajar.most_common(args.top),
        "al_dhahabi_assessment_count": sum(dhahabi.values()),
        "al_dhahabi_distinct_strings": len(dhahabi),
        "al_dhahabi_top": dhahabi.most_common(args.top),
        "narrator_type_top": narrator_types.most_common(args.top),
        "garh_occurrences": garh_total,
        "unique_exact_quotes": len(quote_occurrences),
        "repeated_exact_quote_strings": sum(1 for n in quote_occurrences.values() if n > 1),
        "occurrences_in_repeated_quote_strings": sum(n for n in quote_occurrences.values() if n > 1),
        "evaluator_group_appearances": sum(evaluator_appearances.values()),
        "distinct_evaluator_group_strings": len(evaluator_appearances),
        "evaluator_group_top": evaluator_appearances.most_common(args.top),
        "distinct_exact_citation_strings": len(citation_counts),
        "distinct_citations_with_source_id": len({c for values in source_id_citations.values() for c in values}),
        "distinct_narrator_group_pairs": len(evaluator_record_pairs),
        "source_ids_with_citations": len(source_id_citations),
        "source_ids_with_multiple_normalised_titles": len(source_id_collisions),
        "normalised_titles_with_multiple_source_ids": len(title_collisions),
        "unique_narrator_group_quote_source_combinations": len(doc_key_counts),
        "repeated_documentary_combinations": len(duplicate_docs),
        "excess_documentary_duplicate_occurrences": sum(row["excess_occurrences"] for row in duplicate_docs),
        "same_narrator_quote_source_multiple_group_cases": len(multi_group),
        "fwaed_occurrences": fwaed_total,
        "fwaed_category_counts": Counter(row["category_raw"] for row in fwaed_rows),
        "shape_warnings": dict(warnings),
    }

    write_csv(output / "narrators.csv", narrator_rows,
              ["id", "short_name", "long_name", "narrator_type",
               "biography_json_status", "criticism_json_status"] +
              [f"bio_{i}" for i in range(len(BIO_FIELDS))] +
              ["biography_json", "criticism_json"])
    write_csv(output / "evaluations_raw.csv", eval_rows, [
        "narrator_id", "short_name", "long_name", "group_label_raw",
        "group_entry_index", "quotation_text", "source_citation_raw",
        "source_id_raw", "raw_entry_json", "normalised_title_candidate"])
    evaluator_group_rows = [{
        "group_label_raw": label,
        "quotation_occurrences": count,
        "narrator_record_appearances": sum(1 for pair in evaluator_record_pairs if pair[1] == label),
    } for label, count in evaluator_appearances.most_common()]
    write_csv(output / "evaluator_groups.csv", evaluator_group_rows,
              ["group_label_raw", "quotation_occurrences", "narrator_record_appearances"])
    write_csv(output / "source_references.csv", source_rows, [
        "source_id", "occurrence_count", "citation_variant_count",
        "normalised_title_count", "citation_variants_json", "normalised_titles_json"])
    write_csv(output / "source_id_title_collisions.csv", source_id_collisions, [
        "source_id", "normalised_title_count", "normalised_titles_json", "citation_variants_json"])
    write_csv(output / "title_source_id_collisions.csv", title_collisions, [
        "normalised_title_candidate", "source_id_count", "source_ids_json"])
    write_csv(output / "fwaed_raw.csv", fwaed_rows, [
        "narrator_id", "short_name", "category_raw", "entry_json"])
    write_csv(output / "repeated_exact_quotes.csv", repeated_quotes, [
        "quotation_text", "occurrence_count", "narrator_count", "group_count", "source_id_count"])
    write_csv(output / "duplicate_documentary_entries.csv", duplicate_docs, [
        "narrator_id", "group_label_raw", "quotation_text", "source_id_raw",
        "occurrence_count", "excess_occurrences"])
    write_csv(output / "multi_group_same_quote_source.csv", multi_group, [
        "narrator_id", "quotation_text", "source_id_raw", "group_count", "group_labels_json"])
    write_csv(output / "narrator_type_death_date_sample.csv", death_samples, [
        "id", "short_name", "narrator_type", "death_date"])
    write_csv(output / "narrator_sample.csv", narrator_samples, [
        "id", "short_name", "long_name", "narrator_type",
        "biography_json_status", "criticism_json_status", "biography_json", "criticism_json"])
    write_csv(output / "quotation_sample.csv", quote_samples, [
        "narrator_id", "short_name", "group_label_raw", "group_entry_index",
        "quotation_text", "source_citation_raw", "source_id_raw", "raw_entry_json"])

    summary["fwaed_category_counts"] = dict(summary["fwaed_category_counts"])
    (output / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    report = [
        "# Shamela4 narrator audit",
        "",
        f"- Audit timestamp UTC: {summary['audit_timestamp_utc']}",
        f"- Input file: {source}",
        f"- File bytes: {source.stat().st_size:,}",
        f"- SHA-256: {summary['sha256']}",
        f"- Parquet rows / iterated: {parquet.metadata.num_rows:,} / {seen:,}",
        "",
        "## JSON and missingness",
        "",
        f"- Biography JSON statuses: {dict(bio_status)}",
        f"- Criticism JSON statuses: {dict(criticism_status)}",
        f"- Null narrator_type: {null_narrator_type:,}",
        f"- Null criticism_text: {null_criticism:,}",
        "",
        "## Biography field coverage",
        "",
        "| Field | Records |",
        "|---|---:|",
    ]
    report += [f"| {field} | {bio_presence[field]:,} |" for field in BIO_FIELDS]
    report += [
        "",
        "## Quotation and group structure",
        "",
        f"- ghar occurrences: {garh_total:,}",
        f"- Unique exact quotes: {len(quote_occurrences):,}",
        f"- Repeated exact quote strings: {summary['repeated_exact_quote_strings']:,}",
        f"- Occurrences in repeated quote strings: {summary['occurrences_in_repeated_quote_strings']:,}",
        f"- Evaluator-group quotation occurrences: {sum(evaluator_appearances.values()):,}",
        f"- Distinct narrator/evaluator-group appearances: {len(evaluator_record_pairs):,}",
        f"- Distinct group labels: {len(evaluator_appearances):,}",
        f"- fwaed occurrences: {fwaed_total:,}",
        "",
        "## Source ID/title string checks",
        "",
        f"- Source IDs with citations: {len(source_id_citations):,}",
        f"- IDs associated with multiple normalised titles: {len(source_id_collisions):,}",
        f"- Normalised titles associated with multiple IDs: {len(title_collisions):,}",
        "",
        "These are string-level diagnostics, not proof of bibliographic identity.",
        "",
        "## Duplicate diagnostics",
        "",
        f"- Unique narrator/group/quote/source combinations: {len(doc_key_counts):,}",
        f"- Repeated documentary combinations: {len(duplicate_docs):,}",
        f"- Excess duplicate occurrences: {sum(r['excess_occurrences'] for r in duplicate_docs):,}",
        f"- Same narrator + quote + source assigned to multiple groups: {len(multi_group):,}",
        "",
        "Do not automatically delete these records.",
        "",
        "## Shape warnings",
        "",
    ]
    report += [f"- {key}: {count:,}" for key, count in warnings.most_common()] or ["- None detected."]
    report += [
        "",
        "## Interpretation cautions",
        "",
        "- Group labels are not verified historical-speaker attribution.",
        "- One quotation occurrence is not necessarily one independent evaluation.",
        "- Normalised title matching is heuristic, not bibliographic authority control.",
        "- Existing grades are not automatically clean target labels.",
        "- Raw Parquet input was not modified.",
        "",
    ]
    (output / "PROFILE_REPORT.md").write_text("\n".join(report), encoding="utf-8")

    print("\n" + "=" * 76)
    print("AUDIT SUMMARY")
    print("=" * 76)
    for label, value in [
        ("Rows iterated", seen),
        ("Biography JSON statuses", dict(bio_status)),
        ("Criticism JSON statuses", dict(criticism_status)),
        ("Null narrator_type", null_narrator_type),
        ("Null criticism_text", null_criticism),
        ("ghar occurrences", garh_total),
        ("Unique exact quotes", len(quote_occurrences)),
        ("Repeated exact quote strings", summary["repeated_exact_quote_strings"]),
        ("Occurrences in repeated quote strings", summary["occurrences_in_repeated_quote_strings"]),
        ("Evaluator-group quotation occurrences", sum(evaluator_appearances.values())),
        ("Distinct narrator/evaluator-group appearances", len(evaluator_record_pairs)),
        ("Distinct exact citation strings (including rows without source ID)", len(citation_counts)),
        ("Distinct group labels", len(evaluator_appearances)),
        ("Source IDs with citations", len(source_id_citations)),
        ("Source IDs -> multiple normalised titles", len(source_id_collisions)),
        ("Normalised titles -> multiple source IDs", len(title_collisions)),
        ("Unique documentary combinations", len(doc_key_counts)),
        ("Repeated documentary combinations", len(duplicate_docs)),
        ("Excess duplicate occurrences", sum(r["excess_occurrences"] for r in duplicate_docs)),
        ("Same narrator/quote/source with multiple groups", len(multi_group)),
        ("fwaed occurrences", fwaed_total),
    ]:
        print(f"{label}: {value:,}" if isinstance(value, int) else f"{label}: {value}")

    print("\nTop evaluator groups:")
    for label, count in evaluator_appearances.most_common(min(args.top, 25)):
        print(f"  {count:>8,}  {label}")
    print("\nTop Ibn Hajar assessment strings:")
    for label, count in ibn_hajar.most_common(min(args.top, 20)):
        print(f"  {count:>8,}  {label}")
    print("\nTop al-Dhahabi assessment strings:")
    for label, count in dhahabi.most_common(min(args.top, 20)):
        print(f"  {count:>8,}  {label}")
    print("\nShape warnings:")
    for label, count in warnings.most_common():
        print(f"  {count:>8,}  {label}")
    if not warnings:
        print("  None")
    print(f"\nOutputs: {output}")
    print("Raw Parquet input was not modified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
