#!/usr/bin/env python3
"""Flatten hadithdb narrator-level quotation groups into a quote-occurrence CSV.

This is an extraction aid, not a critic-attribution or ESA-labeling system.
The original scholar-group key is retained as source_group_label and MUST NOT
be treated as a verified speaker/critic identity.

Usage:
  python extract_hadithdb_quotes.py narrators_db.json --out hadithdb_quote_occurrences.csv

Input JSON is read only. The output CSV is a derived working file.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any

CITATION_RE = re.compile(r"(?P<citation>\[[^\[\]]+\])\s*$")
WORK_LOCATOR_RE = re.compile(
    r"^\s*(?P<work>.*?)\s*\((?P<locator>[^()]*)\)\s*$"
)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def json_pointer_escape(value: str) -> str:
    return str(value).replace("~", "~0").replace("/", "~1")


def first_value(record: dict[str, Any], keys: tuple[str, ...]) -> Any:
    """Look for a field at record level, then inside common nested containers."""
    for key in keys:
        if key in record and record[key] not in (None, ""):
            return record[key]
    for container_key in ("data", "narrator", "بيانات"):
        nested = record.get(container_key)
        if isinstance(nested, dict):
            for key in keys:
                if key in nested and nested[key] not in (None, ""):
                    return nested[key]
    return None


def parse_citation(raw_quote: str) -> dict[str, str]:
    """Parse only the trailing bracketed citation; preserve the original string."""
    match = CITATION_RE.search(raw_quote)
    if not match:
        return {
            "parsed_citation_text": "",
            "cited_work_title_raw": "",
            "cited_volume_page_raw": "",
            "quote_text_without_trailing_citation": raw_quote,
            "citation_parse_status": "no_trailing_bracketed_citation",
        }

    citation = match.group("citation")
    inner = citation[1:-1].strip()
    work_match = WORK_LOCATOR_RE.match(inner)
    if not work_match:
        return {
            "parsed_citation_text": citation,
            "cited_work_title_raw": "",
            "cited_volume_page_raw": "",
            "quote_text_without_trailing_citation": raw_quote[:match.start()].rstrip(),
            "citation_parse_status": "bracket_found_but_format_unparsed",
        }

    return {
        "parsed_citation_text": citation,
        "cited_work_title_raw": work_match.group("work").strip(),
        "cited_volume_page_raw": work_match.group("locator").strip(),
        "quote_text_without_trailing_citation": raw_quote[:match.start()].rstrip(),
        "citation_parse_status": "trailing_bracket_parsed",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_json", type=Path)
    parser.add_argument("--out", type=Path, default=Path("hadithdb_quote_occurrences.csv"))
    args = parser.parse_args()

    raw_bytes = args.input_json.read_bytes()
    input_hash = hashlib.sha256(raw_bytes).hexdigest()
    data = json.loads(raw_bytes.decode("utf-8-sig"))

    if not isinstance(data, dict):
        raise SystemExit("Expected narrator database JSON to be an object keyed by narrator ID.")

    columns = [
        "source_dataset_id", "source_file", "source_file_sha256",
        "source_record_id", "raw_narrator_display_name", "raw_narrator_name_ar",
        "source_group_label", "quotation_index_within_group", "json_pointer",
        "raw_quote_text", "quote_text_without_trailing_citation",
        "parsed_citation_text", "cited_work_title_raw", "cited_volume_page_raw",
        "citation_parse_status", "quote_occurrence_sha256", "raw_record_sha256",
        "speaker_attribution_status", "source_verification_status",
        "esa_annotation_status",
    ]

    rows = []
    unexpected_groups = []
    for narrator_id, record in data.items():
        if not isinstance(record, dict):
            continue
        groups = first_value(record, ("الجرح والتعديل",))
        if not isinstance(groups, dict):
            continue

        display_name = first_value(record, ("name", "اسم الراوي", "الاسم"))
        arabic_name = first_value(record, ("الاسم", "اسم الراوي"))
        if isinstance(display_name, (dict, list)):
            display_name = json.dumps(display_name, ensure_ascii=False)
        if isinstance(arabic_name, (dict, list)):
            arabic_name = json.dumps(arabic_name, ensure_ascii=False)

        canonical_record = json.dumps(
            record, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        record_hash = sha256_text(canonical_record)

        for group_label, quotations in groups.items():
            if isinstance(quotations, str):
                quotations = [quotations]
            if not isinstance(quotations, list):
                unexpected_groups.append((narrator_id, group_label, type(quotations).__name__))
                continue

            for quote_index, quote in enumerate(quotations):
                if not isinstance(quote, str):
                    unexpected_groups.append((narrator_id, group_label, type(quote).__name__))
                    continue
                parsed = parse_citation(quote)
                pointer = (
                    "/" + json_pointer_escape(narrator_id)
                    + "/data/الجرح والتعديل/"
                    + json_pointer_escape(group_label)
                    + "/" + str(quote_index)
                )
                occurrence_key = "\0".join(
                    ("hadithdb", str(narrator_id), str(group_label), str(quote_index), quote)
                )
                rows.append({
                    "source_dataset_id": "hadithdb",
                    "source_file": args.input_json.name,
                    "source_file_sha256": input_hash,
                    "source_record_id": str(narrator_id),
                    "raw_narrator_display_name": "" if display_name is None else str(display_name),
                    "raw_narrator_name_ar": "" if arabic_name is None else str(arabic_name),
                    "source_group_label": str(group_label),
                    "quotation_index_within_group": quote_index,
                    "json_pointer": pointer,
                    "raw_quote_text": quote,
                    **parsed,
                    "quote_occurrence_sha256": sha256_text(occurrence_key),
                    "raw_record_sha256": record_hash,
                    "speaker_attribution_status": "unreviewed",
                    "source_verification_status": "unverified",
                    "esa_annotation_status": "unannotated",
                })

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    citation_counts = {}
    for row in rows:
        status = row["citation_parse_status"]
        citation_counts[status] = citation_counts.get(status, 0) + 1

    print(f"input_file={args.input_json}")
    print(f"input_sha256={input_hash}")
    print(f"narrator_records={len(data)}")
    print(f"quote_occurrences_extracted={len(rows)}")
    print(f"unique_exact_quote_strings={len({r['raw_quote_text'] for r in rows})}")
    print(f"citation_parse_counts={json.dumps(citation_counts, ensure_ascii=False, sort_keys=True)}")
    print(f"unexpected_group_values={len(unexpected_groups)}")
    if unexpected_groups[:20]:
        print("unexpected_group_examples=" + json.dumps(unexpected_groups[:20], ensure_ascii=False))
    print(f"output_csv={args.out.resolve()}")
    print("NOTE: source_group_label is not a verified critic/speaker attribution.")


if __name__ == "__main__":
    main()
