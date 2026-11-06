
#!/usr/bin/env python3
"""Profile the extracted hadithdb quotation-occurrence CSV.

Read-only with respect to the input CSV. Writes separate profiling outputs.
Does not infer critic identity, statement type, or ESA labels.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from collections import Counter, defaultdict
from pathlib import Path


def value(row, field):
    return (row.get(field) or "").strip()


def write_counter(path, counter, key_name, count_name="occurrences"):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=[key_name, count_name]
        )
        writer.writeheader()
        for key, count in counter.most_common():
            writer.writerow({key_name: key, count_name: count})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input_csv",
        type=Path,
        help="Extracted hadithdb quote-occurrence CSV",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("data/interim/hadithdb_profile"),
    )
    parser.add_argument("--sample-size", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    with args.input_csv.open(
        "r", encoding="utf-8-sig", newline=""
    ) as f:
        rows = list(csv.DictReader(f))

    if not rows:
        raise SystemExit("Input CSV contains no data rows.")

    required = {
        "source_record_id",
        "source_group_label",
        "raw_quote_text",
        "citation_parse_status",
        "cited_work_title_raw",
        "quote_text_without_trailing_citation",
    }
    missing = required - set(rows[0])
    if missing:
        raise SystemExit(f"Missing required columns: {sorted(missing)}")

    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    # 1. Basic corpus profile
    narrator_counts = Counter(
        value(r, "source_record_id") for r in rows
    )
    group_counts = Counter(
        value(r, "source_group_label") for r in rows
    )
    work_counts = Counter(
        value(r, "cited_work_title_raw") or "[UNPARSED / MISSING]"
        for r in rows
    )
    citation_status_counts = Counter(
        value(r, "citation_parse_status") or "[MISSING]"
        for r in rows
    )

    exact_quote_counts = Counter(
        value(r, "raw_quote_text") for r in rows
    )
    quote_location_map = defaultdict(list)

    for r in rows:
        quote = value(r, "raw_quote_text")
        quote_location_map[quote].append({
            "source_record_id": value(r, "source_record_id"),
            "source_group_label": value(r, "source_group_label"),
            "cited_work_title_raw": value(r, "cited_work_title_raw"),
            "parsed_citation_text": value(r, "parsed_citation_text"),
        })

    duplicate_strings = {
        quote: count
        for quote, count in exact_quote_counts.items()
        if count > 1
    }

    # 2. Exact duplicate report
    duplicate_rows = []
    for quote, count in sorted(
        duplicate_strings.items(),
        key=lambda item: (-item[1], item[0])
    ):
        locations = quote_location_map[quote]
        duplicate_rows.append({
            "frequency": count,
            "distinct_narrators": len({
                x["source_record_id"] for x in locations
            }),
            "distinct_group_labels": len({
                x["source_group_label"] for x in locations
            }),
            "distinct_cited_works": len({
                x["cited_work_title_raw"] for x in locations
                if x["cited_work_title_raw"]
            }),
            "raw_quote_text": quote,
            "locations_json": json.dumps(
                locations, ensure_ascii=False
            ),
        })

    with (out / "exact_duplicate_strings.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as f:
        fields = [
            "frequency", "distinct_narrators",
            "distinct_group_labels", "distinct_cited_works",
            "raw_quote_text", "locations_json",
        ]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(duplicate_rows)

    # 3. Narrator distribution
    with (out / "quotes_per_narrator.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as f:
        writer = csv.DictWriter(
            f, fieldnames=["source_record_id", "quote_occurrences"]
        )
        writer.writeheader()
        for narrator_id, count in narrator_counts.most_common():
            writer.writerow({
                "source_record_id": narrator_id,
                "quote_occurrences": count,
            })

    # 4. Main frequency tables
    write_counter(
        out / "citation_work_frequencies.csv",
        work_counts, "cited_work_title_raw"
    )
    write_counter(
        out / "source_group_frequencies.csv",
        group_counts, "source_group_label"
    )
    write_counter(
        out / "citation_parse_statuses.csv",
        citation_status_counts, "citation_parse_status"
    )

    # 5. Deterministic uniform sample for manual inspection.
    # This is not a gold-standard or stratified annotation sample.
    rng = random.Random(args.seed)
    sample_size = min(args.sample_size, len(rows))
    sample = rng.sample(rows, sample_size)

    with (out / "manual_review_sample.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(sample)

    # 6. Summary statistics
    total = len(rows)
    unique_quotes = len(exact_quote_counts)
    excess_occurrences = total - unique_quotes
    duplicated_string_count = len(duplicate_strings)

    summary = {
        "input_csv": str(args.input_csv),
        "total_quote_occurrences": total,
        "unique_narrator_ids": len(narrator_counts),
        "unique_source_group_labels": len(group_counts),
        "unique_cited_work_titles": len({
            x for x in work_counts
            if x != "[UNPARSED / MISSING]"
        }),
        "unique_exact_quote_strings": unique_quotes,
        "distinct_quote_strings_repeated": duplicated_string_count,
        "excess_occurrences_beyond_first": excess_occurrences,
        "citation_parse_statuses": dict(citation_status_counts),
        "sample_size": sample_size,
        "sample_seed": args.seed,
        "interpretation_warning": (
            "Exact repetition is not automatically an error or "
            "independent evidence. Inspect the locations."
        ),
    }

    with (out / "profile_summary.json").open(
        "w", encoding="utf-8"
    ) as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # 7. Human-readable report
    report = [
        "# hadithdb quotation corpus profile",
        "",
        f"- Total quotation occurrences: **{total:,}**",
        f"- Unique narrator IDs: **{len(narrator_counts):,}**",
        f"- Unique source-group labels: **{len(group_counts):,}**",
        f"- Unique exact quotation strings: **{unique_quotes:,}**",
        f"- Distinct strings repeated: **{duplicated_string_count:,}**",
        f"- Excess occurrences beyond first: **{excess_occurrences:,}**",
        "",
        "## Citation parsing",
        "",
    ]

    for status, count in citation_status_counts.most_common():
        report.append(f"- `{status}`: {count:,} ({count / total:.2%})")

    report += [
        "",
        "## Most frequently cited works",
        "",
    ]
    for work, count in work_counts.most_common(20):
        report.append(f"- {work}: {count:,}")

    report += [
        "",
        "## Most frequent source-group labels",
        "",
    ]
    for group, count in group_counts.most_common(20):
        report.append(f"- {group}: {count:,}")

    report += [
        "",
        "## Interpretation cautions",
        "",
        "- A source-group label is not verified speaker attribution.",
        "- A parsed citation is not a verified bibliographic reference.",
        "- Exact duplicate strings are not automatically erroneous.",
        "- A quotation occurrence is not necessarily an independent judgement.",
        "- The random sample is for initial inspection, not final annotation.",
        "",
    ]

    (out / "PROFILE_REPORT.md").write_text(
        "\n".join(report), encoding="utf-8"
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\nprofile_output_dir={out.resolve()}")


if __name__ == "__main__":
    main()
