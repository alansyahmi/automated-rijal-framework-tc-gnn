#!/usr/bin/env python3
"""Second-stage diagnostics for Shamela4 source references and fwaed labels.

Consumes the occurrence-preserving CSV exports from audit_shamela_narrators.py.
It does not claim to resolve source-ID semantics or infer the meaning of unknown
fwaed labels; it isolates records that need upstream metadata or human review.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

EXPECTED_FWAED = {
    "الإرسال", "المفاضلة بين الرواة", "إثبات سماع الراوي",
    "التوثيق الضمني", "الإدراك", "الاختلاط", "التدليس",
    "الاختلاف في سماع الراوي", "المفاضلة بين الرواة في راو",
    "التضعيف الاستثنائي", "التوثيق الاستثنائي", "التضعيف الضمني",
    "المفاضلة بين الرواة في بلد",
}
SCHOLAR_CUES = (
    "ابن ", "أبو ", "أبي ", "أبو", "الذهبي", "العجلي", "المزي",
    "الترمذي", "الطحاوي", "الحاكم", "النسائي", "البخاري",
    "الدارقطني", "الرازي", "السجستاني", "القعنبي",
)
LOCATOR_RE = re.compile(r"[\(（]\s*\d+\s*/\s*[\d\-–—]+\s*[\)）]")
MULTIWORK_CUES = ("؛", ";", "\n", "\r", " وكتاب ", "، كتاب ")

def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))

def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({
                key: value if isinstance(value, str) else json.dumps(
                    value, ensure_ascii=False, default=str
                ) if value is not None else ""
                for key, value in row.items()
            })

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audit_dir", type=Path,
                        help="Directory created by audit_shamela_narrators.py")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--examples", type=int, default=12)
    args = parser.parse_args()
    source_dir = args.audit_dir.resolve()
    out = (args.out or source_dir / "stage2_diagnostics").resolve()
    out.mkdir(parents=True, exist_ok=True)

    source_rows = read_csv(source_dir / "source_references.csv")
    fwaed_rows = read_csv(source_dir / "fwaed_raw.csv")
    if not source_rows or not fwaed_rows:
        raise SystemExit(
            "Expected non-empty source_references.csv and fwaed_raw.csv. "
            "Check first-stage audit outputs and headers."
        )

    # Source identifiers are opaque keys; observed mappings do not define them.
    id_rows = []
    citation_shape_counts = Counter()
    for row in source_rows:
        sid = row["source_id"]
        citations = json.loads(row.get("citation_variants_json") or "[]")
        titles = json.loads(row.get("normalised_titles_json") or "[]")
        all_flags = Counter()
        for citation in citations:
            flags = []
            if "\n" in citation or "\r" in citation:
                flags.append("multiline")
            if any(cue in citation for cue in ("؛", ";", " وكتاب ", "، كتاب ")):
                flags.append("possible_multiple_work_or_clause")
            if len(LOCATOR_RE.findall(citation)) > 1:
                flags.append("multiple_volume_page_locators")
            if len(citation) > 180:
                flags.append("long_citation_string")
            if not flags:
                flags.append("simple_single_line_candidate")
            all_flags.update(flags)
        citation_shape_counts.update(all_flags)
        id_rows.append({
            "source_id": sid,
            "occurrence_count": int(row.get("occurrence_count") or 0),
            "citation_variant_count": len(citations),
            "normalised_title_count": len(titles),
            "citation_variants": citations,
            "normalised_titles": titles,
            "citation_shape_flags": dict(all_flags),
            "needs_manual_review": (
                len(titles) > 1 or any(flag in all_flags for flag in (
                    "multiline", "possible_multiple_work_or_clause",
                    "multiple_volume_page_locators"
                ))
            ),
        })

    id_rows.sort(key=lambda r: (-r["occurrence_count"], r["source_id"]))
    review_ids = [r for r in id_rows if r["needs_manual_review"]]
    write_csv(out / "source_id_review_queue.csv", review_ids, [
        "source_id", "occurrence_count", "citation_variant_count",
        "normalised_title_count", "citation_variants",
        "normalised_titles", "citation_shape_flags", "needs_manual_review"
    ])

    title_to_ids = defaultdict(set)
    for row in id_rows:
        for title in row["normalised_titles"]:
            if title:
                title_to_ids[title].add(row["source_id"])
    title_multi_ids = [
        {"title_candidate": title, "source_id_count": len(ids),
         "source_ids": sorted(ids)}
        for title, ids in title_to_ids.items() if len(ids) > 1
    ]
    title_multi_ids.sort(key=lambda r: (-r["source_id_count"], r["title_candidate"]))
    write_csv(out / "title_candidate_review_queue.csv", title_multi_ids, [
        "title_candidate", "source_id_count", "source_ids"
    ])

    category_counts = Counter(row.get("category_raw", "").strip() for row in fwaed_rows)
    category_narrators = defaultdict(set)
    shape_counts = Counter()
    unknown_examples = defaultdict(list)
    unknown_categories = []
    entry_shape_examples = defaultdict(list)
    for row in fwaed_rows:
        category = row.get("category_raw", "").strip()
        category_narrators[category].add(row.get("narrator_id", ""))
        try:
            entry = json.loads(row.get("entry_json") or "null")
            shape = type(entry).__name__
        except json.JSONDecodeError:
            shape = "invalid_json"
        shape_counts[shape] += 1
        if len(entry_shape_examples[shape]) < args.examples:
            entry_shape_examples[shape].append({
                "narrator_id": row.get("narrator_id"),
                "category_raw": category,
                "entry_json": row.get("entry_json"),
            })
        if category not in EXPECTED_FWAED:
            if category not in unknown_examples:
                unknown_categories.append(category)
            if len(unknown_examples[category]) < args.examples:
                unknown_examples[category].append({
                    "narrator_id": row.get("narrator_id"),
                    "short_name": row.get("short_name"),
                    "entry_json": row.get("entry_json"),
                })

    scholar_cues = (
        "ابن ", "أبو ", "أبي ", "الذهبي", "العجلي", "المزي",
        "الترمذي", "الطحاوي", "الحاكم", "النسائي", "البخاري",
        "الدارقطني", "الرازي", "السجستاني",
    )
    unknown_rows = []
    for category in unknown_categories:
        possible_person = any(cue in category for cue in scholar_cues)
        unknown_rows.append({
            "category_raw": category,
            "occurrence_count": category_counts[category],
            "narrator_count": len(category_narrators[category]),
            "heuristic_flag": "possible_person_or_scholar_label" if possible_person
                              else "unclassified_label",
            "examples_json": unknown_examples[category],
        })
    unknown_rows.sort(key=lambda r: (-r["occurrence_count"], r["category_raw"]))
    write_csv(out / "fwaed_unexpected_labels.csv", unknown_rows, [
        "category_raw", "occurrence_count", "narrator_count",
        "heuristic_flag", "examples_json"
    ])

    shape_rows = [
        {"entry_json_type": shape, "occurrence_count": count,
         "examples_json": entry_shape_examples[shape]}
        for shape, count in shape_counts.most_common()
    ]
    write_csv(out / "fwaed_entry_shapes.csv", shape_rows, [
        "entry_json_type", "occurrence_count", "examples_json"
    ])

    summary = {
        "source_ids_examined": len(id_rows),
        "source_ids_flagged_for_review": len(review_ids),
        "source_citation_shape_flag_counts": dict(citation_shape_counts),
        "title_candidates_linked_to_multiple_source_ids": len(title_multi_ids),
        "fwaed_occurrences": len(fwaed_rows),
        "fwaed_distinct_labels": len(category_counts),
        "fwaed_expected_labels_observed": {
            label: category_counts[label] for label in sorted(EXPECTED_FWAED)
            if category_counts[label]
        },
        "fwaed_unexpected_labels": len(unknown_rows),
        "fwaed_unexpected_occurrences": sum(
            row["occurrence_count"] for row in unknown_rows
        ),
        "fwaed_entry_json_shapes": dict(shape_counts),
        "interpretation": [
            "Source IDs remain opaque; observed citation mappings do not establish identifier semantics.",
            "Citation flags are heuristics for prioritising manual review, not bibliographic parsing.",
            "Unexpected fwaed labels are not automatically errors; inspect context before recoding.",
            "Scholar-name detection is a weak string heuristic, not entity recognition.",
            "fwaed entries are not assumed to be direct narrator reliability grades."
        ],
    }
    (out / "STAGE2_SUMMARY.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    lines = [
        "# Shamela4 stage-two diagnostics", "",
        "## Source-reference diagnostics", "",
        f"- Source IDs examined: {len(id_rows):,}",
        f"- IDs flagged for manual review: {len(review_ids):,}",
        f"- Title candidates linked to multiple IDs: {len(title_multi_ids):,}", "",
        "| Citation-shape flag | Count |", "|---|---:|",
    ]
    lines += [f"| {key} | {value:,} |" for key, value in citation_shape_counts.most_common()]
    lines += [
        "",
        "Flags are triage heuristics; they do not establish whether an identifier refers",
        "to a book, volume, page, or passage.", "",
        "## fwaed diagnostics", "",
        f"- Occurrences: {len(fwaed_rows):,}",
        f"- Distinct raw labels: {len(category_counts):,}",
        f"- Unexpected labels: {len(unknown_rows):,}",
        f"- Occurrences under unexpected labels: {summary['fwaed_unexpected_occurrences']:,}", "",
        "| Entry JSON type | Count |", "|---|---:|",
    ]
    lines += [f"| {key} | {value:,} |" for key, value in shape_counts.most_common()]
    lines += [
        "",
        "Unexpected labels are retained verbatim. Scholar-name detection is a weak",
        "heuristic. Human inspection must decide whether a label is a person, subtopic,",
        "malformed category, or legitimate additional evidence class. JSON types describe",
        "serialization shape, not semantic function.", "",
        "## Outputs", "",
        "- source_id_review_queue.csv",
        "- title_candidate_review_queue.csv",
        "- fwaed_unexpected_labels.csv",
        "- fwaed_entry_shapes.csv",
        "- STAGE2_SUMMARY.json", "",
        "No raw input is modified and no source ID, category, or quotation is recoded.",
    ]
    (out / "STAGE2_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\nOutputs: {out}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
