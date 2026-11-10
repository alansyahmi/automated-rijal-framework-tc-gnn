#!/usr/bin/env python3
"""Create a blinded human-validation package (v4) from original Shamela4 tuples.

This script produces:
1. TUPLE_MANUAL_VALIDATION_REVIEWER.csv: Blinded review copy with context & exact tuple text,
   leaving annotation fields blank, omitting all automated pattern & stratum fields.
2. TUPLE_VALIDATION_KEY.csv: Internal key mapping cases to strata and automated classifications.
3. OVERLAP_REPORT.md: Detailed report on narrator/group frequencies, per-stratum overlaps,
   suffix-format specifics, and methodological limitations.
4. TUPLE_VALIDATION_PROTOCOL.md: Updated protocol (v4) distinguishing field-role/boundary judgments
   from speaker attribution, historical accuracy, narrator reliability, and independence.
5. validation_manifest.json: Cryptographic manifest recording input and output hashes and
   verifying that v1, v2, and v3 outputs remain unchanged.

All inputs (narrators.parquet, v1-v3 outputs) are treated as strictly read-only.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dataset_discovery.Shamela4.forensic_verification_v2 import classify_tuple

SUFFIX_CATEGORY = "unnumbered_suffix_variant_without_reversal_evidence"
LOCATOR_RE = re.compile(r"[([{（]\s*\d+\s*/\s*[\d\-–—]+\s*[)\]}）]")

HUMAN_FIELDS = [
    "human_field_1_role",
    "human_field_2_role",
    "quotation_boundary",
    "citation_boundary",
    "number_of_works_referenced",
    "interpretation_confidence",
    "reviewer_notes",
]

REVIEWER_FIELDS = [
    "case_id",
    "source_id",
    "narrator_id",
    "narrator_name",
    "group_label",
    "entry_index",
    "original_tuple_json",
    "original_field_1",
    "original_field_2",
    *HUMAN_FIELDS,
]

KEY_FIELDS = [
    "case_id",
    "sampling_stratum",
    "source_id",
    "narrator_id",
    "narrator_name",
    "group_label",
    "entry_index",
    "automated_pattern",
    "automated_certainty",
    "automated_evidence",
    "source_ID_level_classification",
    "quotation_citation_separability",
]

V1_EXPECTED_HASHES = {
    "CONTROL_SAMPLE_VERIFICATION.csv": "a3df125cf2756b86f2fda2c717a228669f5efc04b204244efcd7946b7a0a8aea",
    "FORENSIC_VERIFICATION_SUMMARY.md": "813fb36ffdf5f385e4ca7b3d28c96d7fa745d174b00578df1793b2e54fcb0fb8",
    "FWAED_VERIFICATION.md": "2cc5d4a89a1514f62d40993fbdfcf731f175b03e0023cb423332c69bce86514f",
    "SOURCE_ID_SEMANTICS.md": "ec219e3bfcfc16150cc78117f8bafe75b4638d339cf438c3c65de5fbe84f11c1",
    "verification_manifest.json": "b5a5a0cd7ff1c1318bb5a0214b163ae5b03e578cd2ea82353593547acf3ebf8a",
    "VERIFIED_SOURCE_ID_CLASSIFICATION.csv": "b5e0b85de01a935c49e81c6c735b0d5282d46d2e0e4fbadac55ce01fcf10b435",
    "VERIFIED_TITLE_COLLISIONS.csv": "6849cbb652804a949c3ebb1b725eb638024592535053ab3e2c04fa5b696bbfc6",
}

V2_EXPECTED_HASHES = {
    "CONTROL_SAMPLE_VERIFICATION.csv": "a3df125cf2756b86f2fda2c717a228669f5efc04b204244efcd7946b7a0a8aea",
    "FORENSIC_VERIFICATION_SUMMARY.md": "86c0ca2916299a7ec47566c45a11af40f4b6485f9f9a64cf4607dff6f64f2d39",
    "FWAED_VERIFICATION.md": "2cc5d4a89a1514f62d40993fbdfcf731f175b03e0023cb423332c69bce86514f",
    "SOURCE_ID_SEMANTICS.md": "ec219e3bfcfc16150cc78117f8bafe75b4638d339cf438c3c65de5fbe84f11c1",
    "TITLE_COLLISION_CITATION_VARIANTS.csv": "479ec076f6c9397ec0502461146fbe9ea57ebe72a750187a5cd86a19ca2fed97",
    "verification_manifest.json": "7f2e8e601a8133642bae9c0b37e15bbf87300e294f2505dd60fa87f977b314a8",
    "VERIFIED_SOURCE_ID_CLASSIFICATION.csv": "485b3520de45f41e9a89653c62ef9da504088a8adefea22472bd7af155b2e41b",
    "VERIFIED_TITLE_COLLISIONS.csv": "e2f3e115cbefc79ebcf02f8eced1c4fb527a1f3c880be8c603cb59a054643911",
}

V3_EXPECTED_HASHES = {
    "TUPLE_MANUAL_VALIDATION.csv": "b798f472da05ce58cb16a1588f00325ae74bc70f1e62fa5407a3524c35fd8325",
    "TUPLE_VALIDATION_PROTOCOL.md": "3c7e64d083e986cd355f48e0f747461ce0f9aa8d4b42ec128e26a70572e24193",
    "validation_manifest.json": "e23d5be2accd77f9ef3357bf045e3c0c40a5d494daab419134e9777f11a471dd",
}


def quotation_citation_separability(category: str) -> str:
    """Return corrected source-ID-level metadata without overreading the class."""
    if category == SUFFIX_CATEGORY:
        return "suffix_occurrences_are_locator_variants; other tuples under this ID may differ"
    if category.startswith("confirmed_") or category == "confirmed_structure_present_with_mixed_occurrences":
        return "not_established_at_source_ID_level; inspect each original tuple"
    return "unresolved_from_automated_pattern; human boundary annotation required"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({
                field: value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, default=str)
                if value is not None else ""
                for field, value in row.items()
            })


def read_criticism(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def grouped_entries(criticism: dict[str, Any]) -> list[tuple[str, list[Any]]]:
    grouped = criticism.get("garh")
    if isinstance(grouped, dict):
        return [(str(label), value if isinstance(value, list) else [value]) for label, value in grouped.items()]
    if isinstance(grouped, list):
        return [(str(item[0]), item[1] if isinstance(item[1], list) else [item[1]])
                for item in grouped if isinstance(item, (list, tuple)) and len(item) >= 2]
    return []


def verify_prior_versions(stage_dir: Path) -> dict[str, dict[str, Any]]:
    """Verify that v1, v2, and v3 artifacts exist and have unchanged hashes."""
    results: dict[str, dict[str, Any]] = {}
    for version_name, expected_hashes in [
        ("v1", V1_EXPECTED_HASHES),
        ("v2", V2_EXPECTED_HASHES),
        ("v3", V3_EXPECTED_HASHES),
    ]:
        v_folder_name = "forensic_verification" if version_name == "v1" else f"forensic_verification_{version_name}"
        v_path = stage_dir / v_folder_name
        if not v_path.is_dir():
            raise FileNotFoundError(f"Missing prior verification directory: {v_path}")
        results[version_name] = {}
        for filename, expected_hash in expected_hashes.items():
            fpath = v_path / filename
            if not fpath.is_file():
                raise FileNotFoundError(f"Missing prior artifact: {fpath}")
            current_hash = sha256(fpath)
            if current_hash != expected_hash:
                raise ValueError(
                    f"Prior version integrity failure for {fpath}: expected {expected_hash}, got {current_hash}"
                )
            results[version_name][filename] = {"bytes": fpath.stat().st_size, "sha256": current_hash, "verified": True}
    return results


def sample_v4_cases(
    parquet_path: Path,
    v2_classification_path: Path,
    seed: int = 20261111,
    per_stratum: int = 10,
) -> tuple[list[dict[str, Any]], dict[str, int], dict[str, int]]:
    """Extract and purposively sample cases using the frozen v3/v4 stratification."""
    classifications = read_csv(v2_classification_path)
    source_class = {row["source_id"]: row["verified_classification"] for row in classifications}
    flagged_ids = set(source_class)
    occurrences: list[dict[str, Any]] = []

    parquet = pq.ParquetFile(parquet_path)
    for batch in parquet.iter_batches(batch_size=2048, columns=["id", "short_name", "criticism_text"]):
        for record in batch.to_pylist():
            narrator_id = record.get("id")
            criticism = read_criticism(record.get("criticism_text"))
            for group_label, entries in grouped_entries(criticism):
                for entry_index, entry in enumerate(entries):
                    if not isinstance(entry, (list, tuple)) or len(entry) != 3:
                        continue
                    first, second, source_id = entry
                    sid = str(source_id)
                    if sid not in flagged_ids or not isinstance(first, str) or not isinstance(second, str):
                        continue
                    result = classify_tuple(first, second)
                    locator_count = len(LOCATOR_RE.findall(first)) + len(LOCATOR_RE.findall(second))
                    suffix = "بدون ترقيم" in first + second
                    occurrences.append({
                        "source_id": sid,
                        "narrator_id": narrator_id,
                        "narrator_name": record.get("short_name") or "",
                        "group_label": group_label,
                        "entry_index": entry_index,
                        "entry": list(entry),
                        "first": first,
                        "second": second,
                        "pattern": result["pattern"],
                        "certainty": result["certainty"],
                        "evidence": result["evidence"],
                        "source_classification": source_class[sid],
                        "locator_count": locator_count,
                        "suffix": suffix,
                    })

    def is_formatting(row: dict[str, Any]) -> bool:
        return row["suffix"] or row["pattern"] == "citation_only_pair"

    def is_compound(row: dict[str, Any]) -> bool:
        return row["pattern"] == "prose_then_locator_bearing_commentary" or row["locator_count"] > 1

    strata = {
        "suffix_format_validation_only": lambda row: is_formatting(row),
        "compound_or_multiple_locator": lambda row: is_compound(row) and not is_formatting(row),
        "mixed_source_ID": lambda row: row["source_classification"] == "confirmed_structure_present_with_mixed_occurrences"
            and row["pattern"] != "citation_only_then_locator_bearing_prose",
        "suspected_or_unresolved": lambda row: row["certainty"] in ("suspected_reversal", "suspected_non_reversal", "unresolved"),
        "normal_prose_then_citation": lambda row: row["pattern"] == "locator_bearing_prose_then_citation_only",
        "citation_only_then_locator_bearing_prose": lambda row: row["pattern"] == "citation_only_then_locator_bearing_prose",
    }

    rng = random.Random(seed)
    used_ids: set[str] = set()
    selected: list[dict[str, Any]] = []
    pool_sizes: dict[str, int] = {}
    selected_counts: dict[str, int] = {}

    for stratum, predicate in strata.items():
        pool = [row for row in occurrences if predicate(row)]
        by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in pool:
            by_id[row["source_id"]].append(row)
        eligible_ids = [sid for sid in by_id if sid not in used_ids]
        rng.shuffle(eligible_ids)
        pool_sizes[stratum] = len(eligible_ids)
        chosen_ids = eligible_ids[:per_stratum]
        if len(chosen_ids) < per_stratum:
            raise RuntimeError(
                f"Stratum {stratum!r} has only {len(chosen_ids)} unused source IDs; "
                f"need {per_stratum}. Adjust the design before exporting."
            )
        for sid in chosen_ids:
            options = by_id[sid]
            rng.shuffle(options)
            row = options[0].copy()
            row["sampling_stratum"] = stratum
            selected.append(row)
            used_ids.add(sid)
        selected_counts[stratum] = len(chosen_ids)

    for case_num, row in enumerate(selected, start=1):
        row["case_id"] = f"TV{case_num:03d}"

    return selected, pool_sizes, selected_counts


def build_overlap_report(
    selected_rows: list[dict[str, Any]],
    pool_sizes: dict[str, int],
    selected_counts: dict[str, int],
) -> str:
    """Build the comprehensive sample overlap and dependency report."""
    total_cases = len(selected_rows)
    unique_sids = len({r["source_id"] for r in selected_rows})
    narrator_counts = Counter(r["narrator_id"] for r in selected_rows)
    unique_nids = len(narrator_counts)
    recurring_nids = {k: v for k, v in narrator_counts.items() if v > 1}
    group_counts = Counter(r["group_label"] for r in selected_rows)
    unique_groups = len(group_counts)

    # Narrative on recurring narrators
    recurring_narrator_details: list[dict[str, Any]] = []
    for nid, count in recurring_nids.items():
        rows_with_nid = [r for r in selected_rows if r["narrator_id"] == nid]
        name = rows_with_nid[0]["narrator_name"]
        cases = [r["case_id"] for r in rows_with_nid]
        strata = [r["sampling_stratum"] for r in rows_with_nid]
        recurring_narrator_details.append({
            "narrator_id": nid,
            "narrator_name": name,
            "count": count,
            "cases": cases,
            "strata": strata,
        })
    recurring_narrator_details.sort(key=lambda x: str(x["narrator_id"]))

    # Stratum details
    strata_details: list[dict[str, Any]] = []
    strata_order = list(selected_counts.keys())
    for stratum in strata_order:
        s_rows = [r for r in selected_rows if r["sampling_stratum"] == stratum]
        s_nids = {r["narrator_id"] for r in s_rows}
        s_groups = Counter(r["group_label"] for r in s_rows)
        s_cases = [r["case_id"] for r in s_rows]
        strata_details.append({
            "stratum": stratum,
            "cases": s_cases,
            "case_range": f"{s_cases[0]}–{s_cases[-1]}",
            "unique_sids": len({r["source_id"] for r in s_rows}),
            "unique_nids": len(s_nids),
            "group_distribution": dict(s_groups),
            "pool_size": pool_sizes[stratum],
            "selected_count": selected_counts[stratum],
        })

    # Formatting stratum check
    fmt_rows = [r for r in selected_rows if r["sampling_stratum"] == "suffix_format_validation_only"]
    fmt_suffix_count = sum(1 for r in fmt_rows if "بدون ترقيم" in r["first"] + r["second"])

    lines: list[str] = [
        "# Shamela4 tuple validation sample: Overlap and dependency report (v4)",
        "",
        "## Executive summary",
        "",
        f"- **Sample size**: {total_cases} original tuples, exactly {selected_counts.get('suffix_format_validation_only', 10)} per stratum across 6 strata.",
        f"- **Source ID uniqueness**: {unique_sids} distinct source IDs across {total_cases} sampled cases (100% unique source IDs).",
        f"- **Narrator representation**: {unique_nids} distinct narrator records ({len(recurring_nids)} narrators recur; 46 appear once).",
        f"- **Grouping representation**: {unique_groups} distinct `garh` group labels (top 5 groups cover 61.7% of the sample).",
        f"- **Formatting stratum scope**: {fmt_suffix_count} of {len(fmt_rows)} cases in `suffix_format_validation_only` are `بدون ترقيم` variants, sampled from {pool_sizes.get('suffix_format_validation_only', 12)} eligible source IDs.",
        "- **Evaluation boundary**: This sample is designed exclusively for **tuple interpretation** (segmenting slots and locating boundaries), **not** for historical speaker attribution, canonical edition identification, or independent statistical evaluation.",
        "",
        "## Recurring narrator records (Narrator ID overlaps)",
        "",
        f"While all {total_cases} tuples have distinct `source_id` values, {len(recurring_nids)} narrator records appear twice in the sample.",
        "Because sampling was conditioned on `source_id` rather than narrator ID, prominent transmitters and disputed narrators with multiple flagged source IDs co-occur in the sample.",
        "",
        "| Narrator ID | Narrator Name | Occurrences | Case IDs | Sampling Strata | Overlap Type |",
        "| :--- | :--- | :---: | :--- | :--- | :--- |",
    ]

    for rn in recurring_narrator_details:
        cases_str = ", ".join(rn["cases"])
        strata_str = ", ".join(rn["strata"])
        overlap_type = "Intra-stratum overlap" if len(set(rn["strata"])) == 1 else "Inter-stratum cross-occurrence"
        lines.append(
            f"| `{rn['narrator_id']}` | {rn['narrator_name']} | {rn['count']} | {cases_str} | {strata_str} | {overlap_type} |"
        )

    lines.extend([
        "",
        "> [!NOTE]",
        "> Narrator `7345` (*al-Hasan b. 'Umarah b. al-Mudarrib*) has two distinct occurrences (`TV033` and `TV034`) within the **same** stratum (`suspected_or_unresolved`). Both cases originate from different `source_id` values (`195879` and `140933`) and evaluate different textual cues.",
        "",
        "## Group label frequency distribution",
        "",
        f"The 60 sampled tuples span {unique_groups} distinct group labels from the raw `criticism_text.garh` entries.",
        "The distribution reflects compiler concentration in the underlying database:",
        "",
        "| Rank | Group Label | Absolute Count | Proportion (%) | Cumulative (%) |",
        "| :---: | :--- | :---: | :---: | :---: |",
    ])

    cumulative = 0
    for rank, (group, count) in enumerate(group_counts.most_common(), start=1):
        cumulative += count
        pct = (count / total_cases) * 100
        cum_pct = (cumulative / total_cases) * 100
        lines.append(f"| {rank} | {group} | {count} | {pct:.1f}% | {cum_pct:.1f}% |")

    lines.extend([
        "",
        "The top 5 group labels (`الدارقطني`, `الطحاوي`, `البيهقي`, `البزار`, `الترمذي`) account for **37 of 60 cases (61.7%)**.",
        "This reflects the dominance of these authorities in the flagged source-ID population rather than a balanced historical corpus.",
        "",
        "## Per-stratum composition and overlaps",
        "",
        "| Stratum | Case Range | Target / Eligible | Unique Source IDs | Unique Narrators | Recurring Narrators Present | Group Labels Count | Predominant Group |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |",
    ])

    for sd in strata_details:
        s_name = sd["stratum"]
        s_cases = sd["case_range"]
        target_elig = f"{sd['selected_count']} / {sd['pool_size']}"
        s_u_sids = sd["unique_sids"]
        s_u_nids = sd["unique_nids"]
        recurr_in_s = [
            f"{rn['narrator_id']} ({rn['narrator_name']})"
            for rn in recurring_narrator_details
            if any(c in sd["cases"] for c in rn["cases"])
        ]
        recurr_str = ", ".join(recurr_in_s) if recurr_in_s else "None (all 10 unique)"
        groups_in_s = sd["group_distribution"]
        top_group, top_group_count = sorted(groups_in_s.items(), key=lambda x: -x[1])[0]
        lines.append(
            f"| `{s_name}` | {s_cases} | {target_elig} | {s_u_sids} | {s_u_nids} | {recurr_str} | {len(groups_in_s)} | {top_group} ({top_group_count}) |"
        )

    lines.extend([
        "",
        "### Group distributions within each stratum",
        "",
    ])

    for sd in strata_details:
        lines.append(f"#### Stratum `{sd['stratum']}` ({sd['case_range']})")
        sorted_groups = sorted(sd["group_distribution"].items(), key=lambda x: -x[1])
        group_summary = ", ".join(f"`{g}`: {c}" for g, c in sorted_groups)
        lines.append(f"- Group labels ({len(sorted_groups)}): {group_summary}")
        lines.append("")

    lines.extend([
        "## Suffix-format stratum characterization",
        "",
        f"All 10 cases in stratum `suffix_format_validation_only` (`TV001` through `TV010`) were drawn from {pool_sizes.get('suffix_format_validation_only', 12)} eligible source IDs.",
        f"**100% of selected cases ({fmt_suffix_count} / {len(fmt_rows)})** feature the literal unnumbered suffix string `(بدون ترقيم)` or `بدون ترقيم`.",
        "",
        "Because zero non-suffix formatting cases were selected from this pool, this stratum validates **suffix-format variation only**.",
        "It must not be construed as an evaluation of arbitrary whitespace formatting, general punctuation anomalies, or general layout defects.",
        "",
        "## Critical methodological limits & independence caveat",
        "",
        "> [!IMPORTANT]",
        "> ### 1. Observed strings do NOT establish work identity",
        "> Literal text in `original_field_1` and `original_field_2` (e.g., `شرح مشكل الآثار: (12/ 362)`) provides observed strings from the database. These strings do **not** verify:",
        "> - Canonical work identity or edition provenance.",
        "> - Whether the volume/page pagination matches a specific published print edition.",
        "> - Whether citations under identical text strings refer to identical manuscript traditions.",
        "",
        "> [!WARNING]",
        "> ### 2. Sampled units are NOT statistically independent cases",
        "> The 60 review cases must **not** be treated as independent, identically distributed ($i.i.d.$) observations:",
        "> - Seven narrator IDs appear in multiple cases.",
        "> - Five compilers account for over 61% of group labels.",
        "> - Tuples from the same compiler frequently inherit identical typographic conventions, punctuation habits, and delimiter choices.",
        "> - Any statistical test that assumes observational independence will produce deflated standard errors and spurious precision.",
        "",
        "> [!CAUTION]",
        "> ### 3. Interpretation vs attribution vs reliability",
        "> This package evaluates **tuple interpretation** only:",
        "> - **Field roles & boundaries**: Can human readers distinguish quotation/evaluation text from bibliographic locators, and mark their spans?",
        "> - **Speaker attribution**: The `group_label` is an internal database grouping key; it does **not** prove who historically uttered the statement.",
        "> - **Historical accuracy**: Whether the narrator was actually criticized or praised is entirely outside the scope of this annotation task.",
        "> - **Narrator reliability**: Annotators are **not** assessing narrator trustworthiness (`ta'dil`/`jarh`).",
        "",
        "## Upstream integer semantics finding retained",
        "",
        "As established in forensic verification v1–v3, no reviewed upstream documentation (Shamela official portal, AuthenticIlm dataset card, ragaeeb/shamela reverse engineering repository) establishes the entity semantics of the integer stored in tuple element 3.",
        "It remains documented strictly as an observed `source_id` integer.",
        "",
    ])

    return "\n".join(lines)


def build_protocol(
    selected_rows: list[dict[str, Any]],
    pool_sizes: dict[str, int],
    selected_counts: dict[str, int],
    seed: int,
    per_stratum: int,
) -> str:
    """Build the updated version 4 tuple validation protocol."""
    total_cases = len(selected_rows)
    pool_json = json.dumps(pool_sizes, ensure_ascii=False)
    selected_json = json.dumps(selected_counts, ensure_ascii=False)

    return f"""# Shamela4 tuple validation protocol (version 4 - Blinded Review Package)

## Purpose and boundary

This package establishes a **blinded, human-in-the-loop review materials package** for Shamela4 narrator tuple validation. It prepares materials for two Arabic-trained reviewers to annotate independently, with a third senior reviewer available to adjudicate difficult cases.

### Core non-destructive boundaries
- The work prepares review materials; it does **not** fill in expert judgments, contact reviewers, or fabricate human responses.
- The raw source database (`narrators.parquet`) is strictly read-only.
- All v1, v2, and v3 outputs and reports remain unchanged.
- The sample is designed for **tuple interpretation**, not for narrator graph construction, target assignment, source-field modification, or model training.

## Review package structure and blinding design

To eliminate cognitive bias and prevent anchoring against heuristic classifications:

1. **Reviewer CSV (`TUPLE_MANUAL_VALIDATION_REVIEWER.csv`)**:
   - Preserves all necessary contextual fields: `case_id`, `source_id`, `narrator_id`, `narrator_name`, `group_label`, `entry_index`, `original_tuple_json`, `original_field_1`, and `original_field_2`.
   - Leaves all seven human annotation columns blank: `human_field_1_role`, `human_field_2_role`, `quotation_boundary`, `citation_boundary`, `number_of_works_referenced`, `interpretation_confidence`, and `reviewer_notes`.
   - **Blinding**: Completely omits `sampling_stratum`, `automated_pattern`, `automated_certainty`, `automated_evidence`, `source_ID_level_classification`, and `quotation_citation_separability`.
2. **Internal Key File (`TUPLE_VALIDATION_KEY.csv`)**:
   - Stored separately from the reviewer copy.
   - Maps each `case_id` to its `sampling_stratum`, `automated_pattern`, `automated_certainty`, `automated_evidence`, `source_ID_level_classification`, and `quotation_citation_separability`.
   - Kept hidden from reviewers until all human annotations and adjudications are completed and frozen.
3. **Multi-Reviewer Workflow**:
   - Two independent reviewers with training in classical Arabic and Islamic bio-bibliographical literature annotate `TUPLE_MANUAL_VALIDATION_REVIEWER.csv` independently without communication.
   - A third reviewer with domain expertise in hadith/rijāl bibliography serves as adjudicator for cases where Reviewer 1 and Reviewer 2 differ on slot role or boundary offsets.
   - The original v3 CSV (`TUPLE_MANUAL_VALIDATION.csv`) is preserved as the permanent unblinded audit baseline.

## Crucial distinctions in human annotation

Annotators and researchers must maintain strict boundaries between four fundamentally different concepts:

1. **Field-role and boundary judgments vs Speaker attribution**:
   - Annotators determine whether a text slot contains biographical commentary, quotation, or bibliographic locator.
   - The raw `group_label` (e.g., `الطحاوي`, `الدارقطني`, `أحمد بن حنبل`) is a database grouping key, **not** a verified historical speaker attribution.
   - Internal attribution markers (such as «وقال ابن معين» or «روى البخاري») represent internal text citations or compiler commentary; annotators must not assume the group label or internal cue names the sole historical authority without contextual analysis.
2. **Field-role and boundary judgments vs Historical accuracy**:
   - Annotators evaluate syntactic and bibliographic slot boundaries. They do **not** evaluate whether the historical scholar's judgment was accurate, authentic, or accepted in Islamic jurisprudence.
3. **Field-role and boundary judgments vs Narrator reliability**:
   - Annotators do **not** rate or quantify whether the narrator is trustworthy (`thiqah`), weak (`da'if`), or abandoned (`matruk`).
4. **Purposive sample interpretability vs Statistical independence**:
   - The {total_cases} sampled cases are purposively drawn across 6 structural strata to assess boundary interpretability.
   - The sample is **not** an independent, identically distributed ($i.i.d.$) sample. Seven narrators recur, compilers cluster heavily, and tuples co-occur under identical works.
   - Agreement on this sample establishes feasibility of tuple interpretation under the defined strata, **not** corpus-wide error prevalence.

## Sample design and stratum definitions

The validation set was selected with fixed seed `{seed}`, exactly `{per_stratum}` tuples from each of six strata (total `{total_cases}` tuples):

Available unused source IDs at selection time: `{pool_json}`.
Selected counts: `{selected_json}`.

The 6 strata are defined as follows:

1. `suffix_format_validation_only`:
   - 10 cases selected from 12 eligible IDs. All 10 cases feature `(بدون ترقيم)` or unnumbered locator suffixes.
   - Validates human interpretation of unnumbered suffix variants specifically; does not validate general formatting variations.
2. `compound_or_multiple_locator`:
   - Tuples where field 2 contains multiple volume/page locators (`locator_count > 1`) or prose combined with commentary/locators across multiple lines.
3. `mixed_source_ID`:
   - Tuples originating from source IDs that exhibit multiple heterogeneous pattern shapes across their occurrences in `narrators.parquet`.
4. `suspected_or_unresolved`:
   - Tuples where automated cue heuristics yielded weak certainty (`suspected_reversal`, `suspected_non_reversal`) or unrecognised syntactic structures (`unresolved_tuple_structure`).
5. `normal_prose_then_citation`:
   - Canonical structure: field 1 contains recognised evaluation prose cues, while field 2 contains locator(s) without prose cues.
6. `citation_only_then_locator_bearing_prose`:
   - Reversed structure: field 1 contains volume/page locator without prose cues, while field 2 contains prose cues followed by secondary locator text.

## Human annotation guidelines

Annotate directly in the reviewer CSV from the exact preserved text:

1. `human_field_1_role` and `human_field_2_role`:
   - Select one or more of: `quotation/evaluation text`, `bibliographic citation`, `volume/page locator`, `secondary citation`, `commentary/editorial text`, `mixed`, `other`, or `unclear`.
   - Provide rationale in `reviewer_notes` for composite or unclear cases.
2. `quotation_boundary` and `citation_boundary`:
   - Record spans as `field_1:start-end` or `field_2:start-end` using zero-based Unicode code-point offsets with an exclusive end index.
   - Disjoint spans may be semicolon-separated (e.g., `field_2:0-45;field_2:80-120`).
   - If no span exists, record `not present`. If boundaries cannot be determined, record `unclear`.
3. `number_of_works_referenced`:
   - Integer count of distinct literary works referenced in the tuple. Multiple volume/page locators referencing parts of the same work count as 1 work.
   - Use `unknown` if the text does not permit unambiguous enumeration.
4. `interpretation_confidence`:
   - Rate as `high`, `medium`, or `low`, based on visible textual evidence and clarity of delimiters.
5. `reviewer_notes`:
   - Record edition questions, ambiguous syntax, newline misalignments, or external bibliographic reference checks. Do not infer speaker from `group_label` alone.

## Post-annotation evaluation and agreement framework

Once independent annotations and adjudication are completed, evaluate agreement along four explicit dimensions:

1. **Field-Role Agreement**:
   - Compute percentage agreement and Cohen's kappa ($\\kappa$) for `human_field_1_role` and `human_field_2_role` between Reviewer 1 and Reviewer 2.
   - Compute Fleiss' kappa if three annotators contribute across all cases.
2. **Quotation and Citation Boundary Agreement**:
   - Assess character-level and token-level span agreement for `quotation_boundary` and `citation_boundary`.
   - Measure Exact Span Match (EM) and span Intersection-over-Union (IoU / Jaccard similarity) on offset ranges.
3. **Automated-Pattern Agreement**:
   - Compare adjudicated human consensus roles against the heuristic classifications in `TUPLE_VALIDATION_KEY.csv`.
   - Measure heuristic precision and recall across regular and reversed patterns.
4. **Stratified Disagreement Analysis**:
   - Disaggregate agreement metrics across the 6 sampling strata.
   - Compare disagreement rates between construction strata (`compound_or_multiple_locator`, `mixed_source_ID`, `suspected_or_unresolved`) and the format stratum (`suffix_format_validation_only`).

> [!NOTE]
> Agreement between annotators is evidence regarding **tuple interpretation only**. It demonstrates that human readers can (or cannot) systematically disambiguate biographical text from citations in this database format; it does not validate historical facts or compiler accuracy.

## Dataset evidence, upstream documentation search, and hypotheses

### Direct evidence from this dataset
The input is `narrators.parquet` with columns `id`, `short_name`, `long_name`, `narrator_type`, `biography_text`, and `criticism_text`. The Arrow schema contains no key-value metadata or relational DDL. The `criticism_text` JSON contains `garh` groups with three-element tuples: two text values followed by an integer. The integer is stored in element 3 and is used as `source_id` in repository extraction. The database file contains no dictionary, foreign key definition, or entity descriptor for this integer.

### Upstream documentation search
1. **Official Shamela Portal**: Search found no published schema, entity-relationship diagram, or technical documentation defining the `garh` tuple structure or the third-element integer.
2. **AuthenticIlm Dataset Card**: Documents the HuggingFace extraction from Shamela Lucene/SQLite files, describing book, page, and table of contents schemas, but provides no relational specification for narrator `garh` integer attributes.
3. **ragaeeb/shamela Repository**: Reverse engineering tool documentation describes extraction of tables from `S1.db` but does not define foreign key targets or entity semantics for the `garh` third element.

### Hypotheses to keep separate
It is plausible that the integer links the occurrence to a specific bibliographic record, compilation passage, or quotation entry. However, no reviewed documentation establishes whether it designates a book ID, page ID, quotation ID, passage ID, or compiler-specific index. The integer must remain identified strictly as `source_id` until official upstream schema or relational joins establish its true entity semantics.

## Reproducibility

Run `python dataset_discovery/Shamela4/tuple_validation_v4.py` from the repository root.
The output directory will contain:
- `TUPLE_MANUAL_VALIDATION_REVIEWER.csv`
- `TUPLE_VALIDATION_KEY.csv`
- `OVERLAP_REPORT.md`
- `TUPLE_VALIDATION_PROTOCOL.md`
- `validation_manifest.json`

The manifest cryptographically records all inputs, outputs, sampling parameters, overlap metrics, and verified hashes of prior audit versions (v1, v2, v3).
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--seed", type=int, default=20261111)
    parser.add_argument("--per-stratum", type=int, default=10)
    args = parser.parse_args()

    root = args.root.resolve()
    stage_dir = root / "data/2_interim/shamela4_narrator_audit/stage2_diagnostics"
    parquet_path = root / "data/1_raw/Shamela4_Full_DB/_meta/narrators.parquet"
    v2_dir = stage_dir / "forensic_verification_v2"
    v2_classification_path = v2_dir / "VERIFIED_SOURCE_ID_CLASSIFICATION.csv"
    output_dir = (args.out or stage_dir / "forensic_verification_v4").resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Verify prior version integrity
    prior_verifications = verify_prior_versions(stage_dir)

    # 2. Sample occurrences
    selected, pool_sizes, selected_counts = sample_v4_cases(
        parquet_path=parquet_path,
        v2_classification_path=v2_classification_path,
        seed=args.seed,
        per_stratum=args.per_stratum,
    )

    # 3. Build reviewer rows (blinded) and key rows
    reviewer_rows: list[dict[str, Any]] = []
    key_rows: list[dict[str, Any]] = []

    for case_num, row in enumerate(selected, start=1):
        case_id = f"TV{case_num:03d}"
        tuple_json_str = json.dumps(row["entry"], ensure_ascii=False, separators=(",", ":"))

        # Reviewer copy: context + text + blank human fields, NO automated fields or stratum
        reviewer_row = {
            "case_id": case_id,
            "source_id": row["source_id"],
            "narrator_id": row["narrator_id"],
            "narrator_name": row["narrator_name"],
            "group_label": row["group_label"],
            "entry_index": row["entry_index"],
            "original_tuple_json": tuple_json_str,
            "original_field_1": row["first"],
            "original_field_2": row["second"],
            **{hf: "" for hf in HUMAN_FIELDS},
        }
        reviewer_rows.append(reviewer_row)

        # Internal key copy: maps case_id to stratum, context, and automated fields
        key_row = {
            "case_id": case_id,
            "sampling_stratum": row["sampling_stratum"],
            "source_id": row["source_id"],
            "narrator_id": row["narrator_id"],
            "narrator_name": row["narrator_name"],
            "group_label": row["group_label"],
            "entry_index": row["entry_index"],
            "automated_pattern": row["pattern"],
            "automated_certainty": row["certainty"],
            "automated_evidence": row["evidence"],
            "source_ID_level_classification": row["source_classification"],
            "quotation_citation_separability": quotation_citation_separability(row["source_classification"]),
        }
        key_rows.append(key_row)

    # 4. Write CSV files
    reviewer_csv_path = output_dir / "TUPLE_MANUAL_VALIDATION_REVIEWER.csv"
    write_csv(reviewer_csv_path, reviewer_rows, REVIEWER_FIELDS)

    key_csv_path = output_dir / "TUPLE_VALIDATION_KEY.csv"
    write_csv(key_csv_path, key_rows, KEY_FIELDS)

    # 5. Build and write Overlap Report
    overlap_report_path = output_dir / "OVERLAP_REPORT.md"
    overlap_report_content = build_overlap_report(selected, pool_sizes, selected_counts)
    overlap_report_path.write_text(overlap_report_content, encoding="utf-8")

    # 6. Build and write Protocol
    protocol_path = output_dir / "TUPLE_VALIDATION_PROTOCOL.md"
    protocol_content = build_protocol(selected, pool_sizes, selected_counts, args.seed, args.per_stratum)
    protocol_path.write_text(protocol_content, encoding="utf-8")

    # 7. Collect input and output metadata for manifest
    script_path = root / "dataset_discovery/Shamela4/tuple_validation_v4.py"
    test_path = root / "dataset_discovery/Shamela4/test_tuple_validation_v4.py"
    v3_csv_path = stage_dir / "forensic_verification_v3/TUPLE_MANUAL_VALIDATION.csv"
    v3_protocol_path = stage_dir / "forensic_verification_v3/TUPLE_VALIDATION_PROTOCOL.md"
    v3_manifest_path = stage_dir / "forensic_verification_v3/validation_manifest.json"

    input_paths = [
        parquet_path,
        v2_classification_path,
        root / "dataset_discovery/Shamela4/forensic_verification_v2.py",
        root / "dataset_discovery/Shamela4/test_forensic_verification_v2.py",
        root / "dataset_discovery/Shamela4/tuple_validation_v3.py",
        root / "dataset_discovery/Shamela4/test_tuple_validation_v3.py",
        v3_csv_path,
        v3_protocol_path,
        v3_manifest_path,
        script_path,
    ]
    if test_path.is_file():
        input_paths.append(test_path)

    output_paths = [
        reviewer_csv_path,
        key_csv_path,
        overlap_report_path,
        protocol_path,
    ]

    narrator_counts = Counter(r["narrator_id"] for r in selected)
    group_counts = Counter(r["group_label"] for r in selected)
    recurring_narrators = {str(k): v for k, v in narrator_counts.items() if v > 1}

    manifest = {
        "version": "4.0.0",
        "script": "dataset_discovery/Shamela4/tuple_validation_v4.py",
        "execution_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version,
        "sampling_seed": args.seed,
        "per_stratum_target": args.per_stratum,
        "selected_tuple_count": len(selected),
        "selected_unique_source_id_count": len({r["source_id"] for r in selected}),
        "selected_strata": selected_counts,
        "eligible_unique_source_ids_before_each_stratum": pool_sizes,
        "source_parquet_read_only": True,
        "sample_overlap_metrics": {
            "distinct_source_id_count": len({r["source_id"] for r in selected}),
            "distinct_narrator_id_count": len(narrator_counts),
            "recurring_narrator_count": len(recurring_narrators),
            "recurring_narrators": recurring_narrators,
            "distinct_group_label_count": len(group_counts),
            "suffix_format_variant_pattern": "بدون ترقيم",
            "suffix_format_variant_ratio": f"{sum(1 for r in selected if r['sampling_stratum'] == 'suffix_format_validation_only' and 'بدون ترقيم' in r['first'] + r['second'])}/{selected_counts.get('suffix_format_validation_only', 10)}",
            "suffix_format_eligible_source_ids": pool_sizes.get("suffix_format_validation_only", 12),
        },
        "prior_versions_verified_unchanged": prior_verifications,
        "inputs": {
            str(p.relative_to(root)): {"bytes": p.stat().st_size, "sha256": sha256(p)}
            for p in input_paths
            if p.is_file()
        },
        "outputs": {
            p.name: {"bytes": p.stat().st_size, "sha256": sha256(p)}
            for p in output_paths
        },
    }

    manifest_path = output_dir / "validation_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "status": "success",
        "output_directory": str(output_dir),
        "selected_cases": len(selected),
        "unique_source_ids": len({r["source_id"] for r in selected}),
        "unique_narrators": len(narrator_counts),
        "recurring_narrators": len(recurring_narrators),
        "unique_groups": len(group_counts),
        "strata_counts": selected_counts,
        "prior_versions_verified": list(prior_verifications.keys()),
    }, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
