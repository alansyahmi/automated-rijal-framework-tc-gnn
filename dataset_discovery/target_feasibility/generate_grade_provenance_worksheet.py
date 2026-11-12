#!/usr/bin/env python3
"""Generate the 60-Record Ibn Hajar Grade Provenance Investigation package.

This script extracts candidate Ibn Hajar grade strings from HadithDB and Shamela4,
evaluates six overlapping diagnostic categories, applies deterministic multi-label
stratified sampling to select 60 unique records, and produces:
  1. IBN_HAJAR_GRADE_PROVENANCE_WORKSHEET.csv (with blank human review fields)
  2. ibn_hajar_grade_provenance_manifest.json (with population and sample metrics, hashes)

Methodological Safeguards:
  Safeguard 1 (Attribution vs. Textual Witness):
    Distinguishes directly transmitted judgments, traceable intermediary judgments,
    insufficiently evidenced judgments, compiler syntheses, and modern editorial material.
    Defines explicit criteria to promote intermediary-preserved judgments from quarantine
    to historical input eligibility.
  Safeguard 2 (Overlapping Multi-Label Sampling):
    Categories are non-exclusive. This purposive, quota-based diagnostic stress test
    deliberately selects difficult properties; sample frequencies do not estimate
    candidate-pool prevalence or dataset-wide error rates.

Rule: Strictly ZERO em-dash (\\u2014) and ZERO en-dash (\\u2013). Use standard ASCII '-'.
"""
from __future__ import annotations

import csv
import hashlib
import json
import random
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VERSION = "1.2.0"
RANDOM_SEED = 42
SAMPLE_SIZE_PER_DATASET = 30
TOTAL_SAMPLE_SIZE = 60

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "dataset_discovery" / "target_feasibility"
HADITHDB_PATH = ROOT / "data/1_raw/hadithdb/narrators_db.json"
SHAMELA_PATH = ROOT / "data/1_raw/Shamela4_Full_DB/_meta/narrators.parquet"
TAQRIB_DIR = ROOT / "data/1_raw/Shamela4_Full_DB/26__التراجم-والطبقات/3076__تقريب-التهذيب"

CSV_PATH = OUT_DIR / "IBN_HAJAR_GRADE_PROVENANCE_WORKSHEET.csv"
MANIFEST_PATH = OUT_DIR / "ibn_hajar_grade_provenance_manifest.json"
CODEBOOK_PATH = OUT_DIR / "IBN_HAJAR_GRADE_PROVENANCE_CODEBOOK.md"
PROTOCOL_PATH = OUT_DIR / "IBN_HAJAR_GRADE_PROVENANCE_PROTOCOL.md"
FIREWALL_SPEC_PATH = OUT_DIR / "PROVENANCE_AND_TEMPORAL_FIREWALL_SPEC.md"

# Diagnostic terms
CONVENTIONAL_TERMS = [
    "ثقة", "صدوق", "ضعيف", "متروك", "مجهول", "مقبول", "لين الحديث", "كذاب", "وضاع",
    "لا بأس به", "ليس بالقوي", "مجهول الحال", "مستور", "ثبت", "حجة", "صالح",
    "مجهول العين", "متهم بالكذب", "ساقط", "واه", "منكر الحديث", "ليس بحجة", "ضعيف الحديث"
]

COMPOUND_TERMS = [
    "يهم", "يخطئ", "سيئ الحفظ", "له أوهام", "له أغاليط", "حيث يتابع", "رمي بالتشيع",
    "رمي بالنصب", "تغير بأخرة", "فيه لين", "يعتبر به", "تغير", "اختلط", "أفراد",
    "غرائب", "دلس", "ربما", "إلا أنه", "إذا حدث من حفظه", "في حديثه لين", "فيه مقال",
    "فيه ضعف", "ليس بالحافظ", "إلا في روايته", "تكلم فيه", "ربما وهم", "له مناكير",
    "يغرب", "يرسل", "مدلس", "شيعي", "قدري", "ناصبي"
]

DESCRIPTIVE_TERMS = [
    "صحابي", "صحابة", "التابعين", "مخضرم", "أحد الأعلام", "أحد الأئمة", "فقيه", "حافظ",
    "إمام", "عابد", "فاضل", "زاهد", "أمير المؤمنين", "مقرئ", "شاعر", "قاضي", "أمير",
    "ملك", "نسابة", "علامة", "صاحب", "بدري", "شيخ", "من خيار", "كبير القدر", "شريف",
    "رئيس", "عالم", "مكثر", "العبادلة"
]

ATTRIBUTED_TERMS = [
    "قال ", "روى ", "وثقه", "ضعفه", "سئل ", "سمعت ", "ذكره ", "عن ابن ", "عن يحيى",
    "عن أحمد", "عن أبي", "قال أبو", "قال ابن", "قال البخاري", "قال الدارقطني",
    "قال النسائي", "قال الحاكم", "قال الترمذي", "مشاه"
]

EDITORIAL_MARKERS = [
    "[", "]", "؟", "?", "...", "…", "حاشية", "تحقيق", "نسخة", "كذا", "انظر", "هامش",
    "طبعة", "راجع", "موضع آخر"
]

FLAG_KEYS = [
    "flag_conventional_grade",
    "flag_compound_qualified_grade",
    "flag_descriptive_non_grade",
    "flag_explicit_attributed_quote",
    "flag_criticism_text_overlap",
    "flag_ambiguous_truncated_editorial",
]

PREPOPULATED_COLUMNS = [
    "audit_record_id",
    "dataset_name",
    "dataset_narrator_id",
    "dataset_narrator_name",
    "candidate_grade_field",
    "candidate_grade_verbatim",
    "candidate_grade_source_location",
    "flag_conventional_grade",
    "flag_compound_qualified_grade",
    "flag_descriptive_non_grade",
    "flag_explicit_attributed_quote",
    "flag_criticism_text_overlap",
    "flag_ambiguous_truncated_editorial",
    "diagnostic_flags_summary",
]

BLANK_HUMAN_COLUMNS = [
    "taqrib_entry_number",
    "taqrib_printed_page",
    "taqrib_entry_name_verbatim",
    "taqrib_grade_verbatim",
    "taqrib_qualification_verbatim",
    "taqrib_rank_number",
    "taqrib_identity_match_status",
    "taqrib_text_match_status",
    "assessment_author",
    "assessment_attribution_status",
    "compiler_or_transmitter",
    "editorial_material_status",
    "attribution_evidence_verbatim",
    "source_locator",
    "source_verification_status",
    "textual_fidelity",
    "attribution_fidelity",
    "identity_fidelity",
    "record_disposition",
    "input_eligibility",
    "exclusion_or_quarantine_reason",
    "reviewer_notes",
    "corroboration_status",
]

ALL_COLUMNS = PREPOPULATED_COLUMNS + BLANK_HUMAN_COLUMNS


def compute_sha256(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    if not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def assert_no_forbidden_dashes(text: str, filename: str) -> None:
    """Assert zero em-dash (\\u2014) and zero en-dash (\\u2013)."""
    if "\u2014" in text:
        raise ValueError(f"Forbidden em-dash (\\u2014) found in {filename}")
    if "\u2013" in text:
        raise ValueError(f"Forbidden en-dash (\\u2013) found in {filename}")


def extract_hadithdb_records() -> list[dict[str, Any]]:
    """Extract and analyze all candidate records from HadithDB."""
    raw_data = json.loads(HADITHDB_PATH.read_text(encoding="utf-8-sig"))
    records = []
    for raw_id, row in raw_data.items():
        data = row.get("data", {}) if isinstance(row.get("data"), dict) else {}
        grade = data.get("الرتبة عند ابن حجر")
        if not grade or not isinstance(grade, str) or not grade.strip():
            continue
        grade_clean = grade.strip()
        name = str(row.get("name") or "").strip()

        jarh_dict = data.get("الجرح والتعديل", {})
        crit_text = ""
        if isinstance(jarh_dict, dict):
            crit_parts = []
            for critic_quotes in jarh_dict.values():
                if isinstance(critic_quotes, list):
                    for q in critic_quotes:
                        if isinstance(q, str):
                            crit_parts.append(q)
            crit_text = " ".join(crit_parts)

        flags = compute_diagnostic_flags(grade_clean, crit_text)
        records.append({
            "dataset_name": "HadithDB",
            "dataset_narrator_id": str(raw_id),
            "dataset_narrator_name": name,
            "candidate_grade_field": "الرتبة عند ابن حجر",
            "candidate_grade_verbatim": grade_clean,
            "candidate_grade_source_location": 'data["الرتبة عند ابن حجر"]',
            **flags,
        })
    return records


def extract_shamela_records() -> list[dict[str, Any]]:
    """Extract and analyze all candidate records from Shamela4 narrators.parquet."""
    import pyarrow.parquet as pq

    table = pq.read_table(SHAMELA_PATH)
    raw_rows = table.to_pylist()
    records = []
    for row in raw_rows:
        bio_raw = row.get("biography_text")
        if not bio_raw or not isinstance(bio_raw, str):
            continue
        try:
            bio = json.loads(bio_raw)
        except (json.JSONDecodeError, TypeError):
            continue
        if not isinstance(bio, dict):
            continue
        summary = bio.get("summary", [])
        if not isinstance(summary, list):
            continue

        grade_clean = ""
        for pair in summary:
            if isinstance(pair, (list, tuple)) and len(pair) >= 2:
                if pair[0] == "الرتبة عند ابن حجر" and pair[1] and isinstance(pair[1], str):
                    grade_clean = pair[1].strip()
                    break
        if not grade_clean:
            continue

        name = str(row.get("short_name") or row.get("long_name") or "").strip()

        crit_raw = row.get("criticism_text")
        crit_text = ""
        if crit_raw and isinstance(crit_raw, str):
            try:
                crit = json.loads(crit_raw)
                if isinstance(crit, dict):
                    crit_parts = []
                    for section in ["garh", "fwaed"]:
                        for item in crit.get(section, []):
                            if isinstance(item, list) and len(item) >= 2 and isinstance(item[1], list):
                                for q in item[1]:
                                    if isinstance(q, list) and len(q) >= 1 and isinstance(q[0], str):
                                        crit_parts.append(q[0])
                    crit_text = " ".join(crit_parts)
            except (json.JSONDecodeError, TypeError):
                crit_text = ""

        flags = compute_diagnostic_flags(grade_clean, crit_text)
        records.append({
            "dataset_name": "Shamela4",
            "dataset_narrator_id": str(row.get("id", "")),
            "dataset_narrator_name": name,
            "candidate_grade_field": "الرتبة عند ابن حجر",
            "candidate_grade_verbatim": grade_clean,
            "candidate_grade_source_location": 'biography_text["summary"]["الرتبة عند ابن حجر"]',
            **flags,
        })
    return records


def compute_diagnostic_flags(grade: str, criticism_text: str) -> dict[str, Any]:
    """Compute the six diagnostic boolean flags for a candidate grade string."""
    is_conv = any(term in grade for term in CONVENTIONAL_TERMS)
    is_compound = any(term in grade for term in COMPOUND_TERMS)
    is_desc = any(term in grade for term in DESCRIPTIVE_TERMS)

    is_attr = any(term in grade for term in ATTRIBUTED_TERMS)
    if not is_attr and ":" in grade:
        scholar_tokens = ["أبو", "ابن", "أحمد", "يحيى", "علي", "البخاري", "حاتم", "زرعة", "معين", "حبان", "النسائي", "الترمذي"]
        if any(tok in grade for tok in scholar_tokens):
            is_attr = True

    is_overlap = bool(criticism_text and len(grade) >= 4 and grade in criticism_text)

    is_edit = any(marker in grade for marker in EDITORIAL_MARKERS) or len(grade) > 80
    if not is_edit and "(" in grade and ")" in grade and any(ch.isdigit() for ch in grade):
        is_edit = True

    active_summaries = []
    if is_conv:
        active_summaries.append("conventional")
    if is_compound:
        active_summaries.append("compound")
    if is_desc:
        active_summaries.append("descriptive")
    if is_attr:
        active_summaries.append("attributed")
    if is_overlap:
        active_summaries.append("overlap")
    if is_edit:
        active_summaries.append("editorial")

    return {
        "flag_conventional_grade": is_conv,
        "flag_compound_qualified_grade": is_compound,
        "flag_descriptive_non_grade": is_desc,
        "flag_explicit_attributed_quote": is_attr,
        "flag_criticism_text_overlap": is_overlap,
        "flag_ambiguous_truncated_editorial": is_edit,
        "diagnostic_flags_summary": "; ".join(active_summaries) if active_summaries else "unclassified",
    }


def compute_population_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute aggregate flag counts and overlap statistics for a population."""
    total = len(records)
    flag_counts = {}
    flag_percentages = {}
    for flag in FLAG_KEYS:
        c = sum(1 for r in records if r[flag])
        flag_counts[flag] = c
        flag_percentages[flag] = f"{100 * c / total:.2f}%" if total else "0.00%"

    overlap_matrix = {}
    for f1 in FLAG_KEYS:
        overlap_matrix[f1] = {}
        for f2 in FLAG_KEYS:
            overlap_matrix[f1][f2] = sum(1 for r in records if r[f1] and r[f2])

    flag_count_dist = Counter(sum(1 for f in FLAG_KEYS if r[f]) for r in records)

    return {
        "total_candidate_records": total,
        "flag_counts": flag_counts,
        "flag_percentages": flag_percentages,
        "flag_count_per_record_distribution": {str(k): v for k, v in sorted(flag_count_dist.items())},
        "pairwise_overlap_matrix": overlap_matrix,
    }


def sample_records_stratified(
    pool: list[dict[str, Any]],
    n_target: int,
    seed: int,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Deterministically sample n_target records covering all diagnostic categories.

    Refined Stratified Multi-Label Selection:
      Prioritizes diagnostic diversity by explicitly balancing:
        1. Editorial anomalies (brackets, footnotes, multi-quote truncation)
        2. Pure attributed quotations (quotes without conventional grade tokens)
        3. General attributed quotations (multi-label attributed quotes)
        4. Pure descriptive non-grade phrases (historical/generational terms without conventional grades)
        5. General descriptive evaluations (multi-label descriptive assessments)
        6. Compound / qualified evaluations (conditions, defects, sectarian tags)
        7. Non-overlap evaluations (candidate grades not found in criticism text)
        8. Uncomplicated conventional-grade baselines (operational flag definition)
        9. Deterministic fill for any remainder.
    """
    rng = random.Random(seed)
    sorted_pool = sorted(
        pool,
        key=lambda x: int(x["dataset_narrator_id"]) if x["dataset_narrator_id"].isdigit() else x["dataset_narrator_id"],
    )

    selected_ids: set[str] = set()
    selected_records: list[dict[str, Any]] = []
    primary_category_counts: dict[str, int] = defaultdict(int)

    def pick_from_stratum(condition, quota: int, cat_name: str) -> int:
        candidates = [r for r in sorted_pool if condition(r) and r["dataset_narrator_id"] not in selected_ids]
        rng.shuffle(candidates)
        picked = candidates[:quota]
        for r in picked:
            selected_ids.add(r["dataset_narrator_id"])
            selected_records.append(r)
            primary_category_counts[cat_name] += 1
        return len(picked)

    # 1. Editorial anomalies (rare)
    pick_from_stratum(lambda r: r["flag_ambiguous_truncated_editorial"], 5, "editorial_anomaly")

    # 2. Attributed quotations: 3 pure attributed + 3 general attributed
    pick_from_stratum(
        lambda r: r["flag_explicit_attributed_quote"] and not r["flag_conventional_grade"],
        3,
        "attributed_pure",
    )
    pick_from_stratum(
        lambda r: r["flag_explicit_attributed_quote"],
        3,
        "attributed_general",
    )

    # 3. Descriptive non-grades: 3 pure descriptive + 3 general descriptive
    pick_from_stratum(
        lambda r: r["flag_descriptive_non_grade"] and not r["flag_conventional_grade"],
        3,
        "descriptive_pure",
    )
    pick_from_stratum(
        lambda r: r["flag_descriptive_non_grade"],
        3,
        "descriptive_general",
    )

    # 4. Compound / qualified evaluations: 5
    pick_from_stratum(
        lambda r: r["flag_compound_qualified_grade"],
        5,
        "compound_qualified",
    )

    # 5. Non-overlap evaluations (compiler syntheses absent from criticism text): 3
    pick_from_stratum(
        lambda r: not r["flag_criticism_text_overlap"] and (r["flag_conventional_grade"] or r["flag_compound_qualified_grade"]),
        3,
        "non_overlap_evaluation",
    )

    # 6. Uncomplicated conventional-grade baselines: 4. This is not leakage-clean;
    # criticism-text overlap is deliberately allowed to preserve the existing sample.
    pick_from_stratum(
        lambda r: r["flag_conventional_grade"]
        and not r["flag_compound_qualified_grade"]
        and not r["flag_descriptive_non_grade"]
        and not r["flag_explicit_attributed_quote"]
        and not r["flag_ambiguous_truncated_editorial"],
        4,
        "uncomplicated_conventional_grade_baseline",
    )

    # 7. Fill remainder deterministically up to n_target
    if len(selected_records) < n_target:
        remain = [r for r in sorted_pool if r["dataset_narrator_id"] not in selected_ids]
        rng.shuffle(remain)
        needed = n_target - len(selected_records)
        for r in remain[:needed]:
            selected_ids.add(r["dataset_narrator_id"])
            selected_records.append(r)
            primary_category_counts["fill_remainder"] += 1

    selected_records.sort(
        key=lambda x: int(x["dataset_narrator_id"]) if x["dataset_narrator_id"].isdigit() else x["dataset_narrator_id"],
    )
    return selected_records, dict(primary_category_counts)


def generate_worksheet_and_manifest() -> dict[str, Any]:
    """Execute the full generation and validation pipeline."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Extracting candidate records from HadithDB...")
    hadithdb_pool = extract_hadithdb_records()
    print(f"  HadithDB candidates with Ibn Hajar grade: {len(hadithdb_pool)}")

    print("Extracting candidate records from Shamela4...")
    shamela_pool = extract_shamela_records()
    print(f"  Shamela4 candidates with Ibn Hajar grade: {len(shamela_pool)}")

    print("Computing population metrics...")
    hadithdb_pop_metrics = compute_population_metrics(hadithdb_pool)
    shamela_pop_metrics = compute_population_metrics(shamela_pool)

    print("Sampling 30 records from HadithDB (seed=42)...")
    hadithdb_sample, h_primary_counts = sample_records_stratified(
        hadithdb_pool, SAMPLE_SIZE_PER_DATASET, RANDOM_SEED
    )
    print("Sampling 30 records from Shamela4 (seed=42)...")
    shamela_sample, s_primary_counts = sample_records_stratified(
        shamela_pool, SAMPLE_SIZE_PER_DATASET, RANDOM_SEED
    )

    combined_sample = hadithdb_sample + shamela_sample
    if len(combined_sample) != TOTAL_SAMPLE_SIZE:
        raise ValueError(f"Expected {TOTAL_SAMPLE_SIZE} records, got {len(combined_sample)}")

    worksheet_rows = []
    for idx, record in enumerate(combined_sample, start=1):
        row = {
            "audit_record_id": f"PROV-{idx:02d}",
            "dataset_name": record["dataset_name"],
            "dataset_narrator_id": record["dataset_narrator_id"],
            "dataset_narrator_name": record["dataset_narrator_name"],
            "candidate_grade_field": record["candidate_grade_field"],
            "candidate_grade_verbatim": record["candidate_grade_verbatim"],
            "candidate_grade_source_location": record["candidate_grade_source_location"],
            "flag_conventional_grade": "TRUE" if record["flag_conventional_grade"] else "FALSE",
            "flag_compound_qualified_grade": "TRUE" if record["flag_compound_qualified_grade"] else "FALSE",
            "flag_descriptive_non_grade": "TRUE" if record["flag_descriptive_non_grade"] else "FALSE",
            "flag_explicit_attributed_quote": "TRUE" if record["flag_explicit_attributed_quote"] else "FALSE",
            "flag_criticism_text_overlap": "TRUE" if record["flag_criticism_text_overlap"] else "FALSE",
            "flag_ambiguous_truncated_editorial": "TRUE" if record["flag_ambiguous_truncated_editorial"] else "FALSE",
            "diagnostic_flags_summary": record["diagnostic_flags_summary"],
        }
        for col in BLANK_HUMAN_COLUMNS:
            row[col] = ""
        worksheet_rows.append(row)

    print(f"Writing worksheet to {CSV_PATH}...")
    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ALL_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(worksheet_rows)

    combined_primary_counts: dict[str, int] = defaultdict(int)
    for k, v in h_primary_counts.items():
        combined_primary_counts[k] += v
    for k, v in s_primary_counts.items():
        combined_primary_counts[k] += v

    flag_count_per_rec = Counter(sum(1 for f in FLAG_KEYS if r[f]) for r in combined_sample)
    no_rare_count = sum(
        1 for r in combined_sample
        if not r["flag_compound_qualified_grade"]
        and not r["flag_descriptive_non_grade"]
        and not r["flag_explicit_attributed_quote"]
        and not r["flag_ambiguous_truncated_editorial"]
    )

    sample_metrics = {
        "sample_size": TOTAL_SAMPLE_SIZE,
        "hadithdb_count": len(hadithdb_sample),
        "shamela_count": len(shamela_sample),
        "primary_selection_category_counts": {
            "combined": dict(combined_primary_counts),
            "hadithdb": h_primary_counts,
            "shamela4": s_primary_counts,
        },
        "flags_per_record_distribution": {str(k): v for k, v in sorted(flag_count_per_rec.items())},
        "single_flag_records_count": flag_count_per_rec.get(1, 0),
        "multiple_flag_records_count": sum(v for k, v in flag_count_per_rec.items() if k > 1),
        "records_without_rare_diagnostic_properties_count": no_rare_count,
        "non_overlap_with_criticism_text_count": sum(1 for r in combined_sample if not r["flag_criticism_text_overlap"]),
        "diagnostic_descriptive_without_conventional_grade_count": sum(1 for r in combined_sample if r["flag_descriptive_non_grade"] and not r["flag_conventional_grade"]),
        "diagnostic_attributed_without_conventional_grade_count": sum(1 for r in combined_sample if r["flag_explicit_attributed_quote"] and not r["flag_conventional_grade"]),
        "uncomplicated_conventional_grade_baseline_count": sum(
            1 for r in combined_sample
            if r["flag_conventional_grade"]
            and not r["flag_compound_qualified_grade"]
            and not r["flag_descriptive_non_grade"]
            and not r["flag_explicit_attributed_quote"]
            and not r["flag_ambiguous_truncated_editorial"]
        ),
        "strict_conventional_grade_baseline_without_criticism_overlap_count": sum(
            1 for r in combined_sample
            if r["flag_conventional_grade"]
            and not r["flag_compound_qualified_grade"]
            and not r["flag_descriptive_non_grade"]
            and not r["flag_explicit_attributed_quote"]
            and not r["flag_ambiguous_truncated_editorial"]
            and not r["flag_criticism_text_overlap"]
        ),
        "flag_representation": {
            flag: {
                "total_count": sum(1 for r in combined_sample if r[flag]),
                "hadithdb_count": sum(1 for r in hadithdb_sample if r[flag]),
                "shamela_count": sum(1 for r in shamela_sample if r[flag]),
                "percentage_of_sample": f"{100 * sum(1 for r in combined_sample if r[flag]) / TOTAL_SAMPLE_SIZE:.2f}%",
            }
            for flag in FLAG_KEYS
        },
        "sample_pairwise_overlap_matrix": {
            f1: {f2: sum(1 for r in combined_sample if r[f1] and r[f2]) for f2 in FLAG_KEYS}
            for f1 in FLAG_KEYS
        },
    }

    csv_content = CSV_PATH.read_text(encoding="utf-8-sig")
    assert_no_forbidden_dashes(csv_content, "IBN_HAJAR_GRADE_PROVENANCE_WORKSHEET.csv")

    manifest_data = {
        "manifest_version": VERSION,
        "generator_script": "dataset_discovery/target_feasibility/generate_grade_provenance_worksheet.py",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "random_seed": RANDOM_SEED,
        "target_book": {
            "book_id": 3076,
            "title_ar": "تقريب التهذيب",
            "author_ar": "ابن حجر العسقلاني",
            "death_hijri": 852,
            "editor_ar": "محمد عوامة",
            "relative_path": "data/1_raw/Shamela4_Full_DB/26__التراجم-والطبقات/3076__تقريب-التهذيب",
            "sha256_pages_jsonl": compute_sha256(TAQRIB_DIR / "pages.jsonl"),
            "sha256_book_metadata": compute_sha256(TAQRIB_DIR / "book_metadata.json"),
        },
        "raw_source_hashes": {
            "hadithdb_narrators_db_json": compute_sha256(HADITHDB_PATH),
            "shamela4_narrators_parquet": compute_sha256(SHAMELA_PATH),
        },
        "output_hashes": {
            "worksheet_csv": compute_sha256(CSV_PATH),
            "codebook_md": compute_sha256(CODEBOOK_PATH),
            "protocol_md": compute_sha256(PROTOCOL_PATH),
            "firewall_spec_md": compute_sha256(FIREWALL_SPEC_PATH),
            "generator_script_py": compute_sha256(Path(__file__)),
            "test_suite_py": compute_sha256(OUT_DIR / "test_grade_provenance_worksheet.py") if (OUT_DIR / "test_grade_provenance_worksheet.py").is_file() else "",
        },
        "population_statistics": {
            "hadithdb": hadithdb_pop_metrics,
            "shamela4": shamela_pop_metrics,
        },
        "sample_statistics": sample_metrics,
        "sampling_interpretation": {
            "design": "Purposive quota-based diagnostic stress test, not a probability sample.",
            "sample_flag_counts_scope": "Descriptive of the selected 60 records only; not population prevalence or dataset-wide error rates.",
            "population_flag_counts_scope": "Descriptive diagnostics computed from the full candidate pools; not estimates of annotation error.",
            "primary_selection_strata_vs_diagnostic_flags": "Primary selection category counts record the pass that selected each record. Diagnostic counts are recomputed row-level Boolean flag combinations and are non-exclusive; records selected in a general pass may also meet a pure diagnostic flag definition.",
            "uncomplicated_conventional_grade_baseline_definition": "flag_conventional_grade TRUE AND flag_compound_qualified_grade FALSE AND flag_descriptive_non_grade FALSE AND flag_explicit_attributed_quote FALSE AND flag_ambiguous_truncated_editorial FALSE. Criticism-text overlap may remain, so this is not a leakage-clean baseline.",
            "strict_conventional_grade_baseline_definition": "The uncomplicated definition plus flag_criticism_text_overlap FALSE.",
        },
        "methodological_safeguards": {
            "safeguard_1_attribution_vs_textual_witness": {
                "principle": "Evaluator attribution is not proof of historical input eligibility.",
                "attribution_categories": [
                    "directly_transmitted_historical_judgment",
                    "traceable_intermediary_historical_judgment",
                    "insufficient_evidence_historical_judgment",
                    "compiler_own_synthesis",
                    "modern_editorial_material",
                ],
                "input_eligibility_categories": [
                    "eligible_historical_input",
                    "quarantined_intermediary_input",
                    "quarantined_insufficient_evidence",
                    "target_evaluation_only",
                    "ineligible_compiler_synthesis",
                    "ineligible_editorial_material",
                ],
                "quarantine_to_eligibility_criteria": [
                    "provisional_temporal_rule: T <= 365 AH is an operational inclusion boundary requiring historical justification, not a universal division; evaluator death does not date an individual judgment.",
                    "traceable_transmission_lineage: Intermediary text cites identifiable source work or documented isnad.",
                    "corroboration_status: Classify as independent_corroboration, dependent_corroboration, or unresolved_corroboration; multiple compilations alone do not establish independence.",
                    "editorial_integrity_verification: Wording confirmed as critic appraisal without intermediary editorial distortion.",
                ],
                "corroboration_status_allowed_values": [
                    "independent_corroboration",
                    "dependent_corroboration",
                    "unresolved_corroboration",
                ],
                "date_dimensions": [
                    "critic_lifespan_and_death",
                    "approximate_judgment_date_if_known",
                    "source_work_composition_date",
                    "surviving_manuscript_or_textual_witness_date",
                    "modern_editor_and_edition_date",
                ],
                "date_inference_rule": "Do not infer judgment date from critic death date, or surviving witness date from source-work composition date.",
                "temporal_boundary": "T <= 365 AH is a provisional operational inclusion boundary requiring historical justification, not a universal historical division.",
                "witness_rule": "A later surviving witness may preserve an earlier judgment; assess the surviving evidence and transmission uncertainty. A pre-365 AH physical witness is not an absolute eligibility requirement.",
            },
            "safeguard_2_overlapping_multilabel_sampling": {
                "principle": "The six diagnostic categories are non-exclusive and multi-label. The sample is purposive and quota-based; sample frequencies describe selected records only.",
                "categories": FLAG_KEYS,
                "sampling_strategy": "Deterministic purposive, quota-based diagnostic stress test balancing rare/difficult properties against uncomplicated conventional-grade baselines. It is not representative and does not estimate population prevalence or error rates.",
            },
        },
        "verification_dimensions": {
            "dimensions": [
                "textual_fidelity",
                "attribution_fidelity",
                "narrator_identity_resolution",
                "historical_input_eligibility",
                "target_candidate_suitability",
                "construct_validity",
            ],
            "independence_rule": "Each dimension is assessed separately; passing one does not imply passing another.",
            "record_disposition_scope": "Target-candidate disposition only; it does not determine historical input eligibility.",
            "cautions": [
                "A verified Ibn Hajar assessment is not automatically a valid historical input.",
                "An attributed early critic judgment is not automatically eligible without provenance verification.",
                "A verified target candidate does not establish construct validity.",
            ],
        },
        "reconciled_taxonomy": {
            "record_disposition_allowed_values": [
                "verified_ibn_hajar_assessment",
                "excluded_not_a_grade",
                "excluded_not_ibn_hajar",
                "excluded_editorial_material",
                "excluded_identity_mismatch",
                "excluded_textual_corruption",
                "quarantined_unattributed_synthesis",
                "quarantined_uncertain",
            ],
            "construct_validity_note": "Textual verification of Ibn Hajar's authorship in Taqrib establishes source fidelity and attribution fidelity; it does not independently prove construct validity or machine-learning target suitability.",
        },
    }

    manifest_json_str = json.dumps(manifest_data, ensure_ascii=False, indent=2)
    assert_no_forbidden_dashes(manifest_json_str, "ibn_hajar_grade_provenance_manifest.json")
    print(f"Writing manifest to {MANIFEST_PATH}...")
    MANIFEST_PATH.write_text(manifest_json_str, encoding="utf-8")

    print("\nGeneration completed successfully.")
    print(f"Worksheet: {CSV_PATH}")
    print(f"Manifest: {MANIFEST_PATH}")
    return manifest_data


if __name__ == "__main__":
    generate_worksheet_and_manifest()
