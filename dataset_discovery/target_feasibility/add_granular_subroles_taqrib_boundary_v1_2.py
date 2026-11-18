#!/usr/bin/env python3
"""Add fine-grained span subroles without replacing broad parent roles."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PILOT_DIR = ROOT / "data" / "2_interim" / "rijal_fyp_modelling_pipeline" / "boundary_pilot_v1"
CORRECTED_INPUT = PILOT_DIR / "BOUNDARY_PILOT_REVIEW_CORRECTED_2026-11-15.csv"
REVIEWER_INPUT = PILOT_DIR / "BOUNDARY_PILOT_REVIEWER_ANNOTATED_2026-11-15.csv"
OUTPUT_CSV = PILOT_DIR / "BOUNDARY_PILOT_REVIEW_CORRECTED_GRANULAR_2026-11-15.csv"
OUTPUT_SHA = PILOT_DIR / "BOUNDARY_PILOT_REVIEW_CORRECTED_GRANULAR_2026-11-15.sha256"
OUTPUT_MANIFEST = PILOT_DIR / "BOUNDARY_PILOT_REVIEW_CORRECTED_GRANULAR_2026-11-15_MANIFEST.json"
OUTPUT_MANIFEST_SHA = PILOT_DIR / "BOUNDARY_PILOT_REVIEW_CORRECTED_GRANULAR_2026-11-15_MANIFEST.sha256"

EXPECTED_CORRECTED_SHA256 = "cd664598d5a3573b863e2d79467b6069cf77927248a9a371be9c018cab0b3e6b"
EXPECTED_REVIEWER_SHA256 = "c8eb9d73e04cb180d02e0fbba886f7474d94c1c91400da2a9613845ca15e1645"
MAX_SEGMENTS = 15

OLD_ROLE_SUBROLE = {
    "full_name": "full_name_or_lineage",
    "name_ism": "reported_personal_name",
    "nisba": "nisba",
    "nisba_1": "nisba",
    "nisba_2": "nisba",
    "nisba_3": "nisba",
    "kunya": "kunya",
    "kunya_1": "kunya",
    "kunya_2": "kunya",
    "nickname_laqab": "nickname_or_laqab",
    "pronunciation_guide": "pronunciation_or_lexical_note",
    "biographical_fact_residence": "residence",
    "biographical_fact_occupation": "occupation_or_role",
    "biographical_fact_death": "death_event",
    "death_year": "death_year",
    "death_age": "age_or_lifespan_statement",
    "death_location": "death_location",
    "biographical_fact": "biographical_statement",
    "assessment_or_grade": "assessment_formula_or_cluster",
    "grade_or_assessment": "assessment_formula_or_cluster",
    "assessment_qualification_or_scope": "assessment_qualifier",
    "specific_criticism_or_attributed_report": "specific_criticism_or_report",
    "status_or_companion_classification": "status_classification",
    "generation_classification": "generation_phrase",
    "source_citation": "source_reference_symbol",
    "source_citations": "source_reference_symbol",
    "disambiguation_note": "disambiguation_marker",
}

MANUAL_SUBROLES = {
    ("TB-006", "آخر"): "disambiguating_descriptor",
    ("TB-009", "عن يزيد ابن هارون"): "transmission_relation_or_context",
    ("TB-009", "يحتمل أن يكون هو ابن خالد الخلال"): "possible_identity",
    ("TB-010", "زاهد"): "descriptive_status",
    ("TB-014", "أحد الأئمة ثقة حافظ"): "assessment_cluster",
    ("TB-014", "فقيه"): "assessment_descriptor",
    ("TB-014", "حجة"): "assessment_descriptor",
    ("TB-015", "صاحب حديث"): "specialty_or_biographical_description",
    ("TB-016", "آبي اللحم"): "epithet_or_narrator_label",
    ("TB-016", "بالمد بلفظ اسم الفاعل من الإباء"): "pronunciation_or_etymology_note",
    ("TB-016", "يقال إن اسمه خلف"): "reported_identity",
    ("TB-016", "وقيل غير ذلك"): "alternative_identity_uncertainty",
    ("TB-018", "خت"): "source_reference_symbol",
    ("TB-023", "تفرد الحسن بالرواية عنه"): "transmission_observation",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_rows(path: Path, expected_hash: str) -> tuple[list[dict[str, str]], list[str]]:
    actual = sha256(path)
    if actual != expected_hash:
        raise RuntimeError(f"Unexpected input hash for {path.name}: {actual}")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def old_spans(row: dict[str, str], source: str) -> list[tuple[int, int, str, str]]:
    spans = []
    cursor = 0
    for index in range(1, 30):
        text = row.get(f"segment_{index}_text_verbatim", "")
        role = row.get(f"segment_{index}_role", "")
        if not text:
            continue
        start = source.find(text, cursor)
        if start < 0:
            raise RuntimeError(f"Original span not found for {row['case_id']}: {text!r}")
        end = start + len(text)
        spans.append((start, end, role, text))
        cursor = end
    return spans


def fallback_subrole(parent: str) -> str:
    return {
        "source_entry_number": "printed_entry_number",
        "narrator_name_or_identity": "identity_detail",
        "assessment_or_grade": "assessment_formula_or_cluster",
        "assessment_qualification_or_scope": "assessment_qualifier",
        "specific_criticism_or_attributed_report": "specific_criticism_or_report",
        "status_or_companion_classification": "status_classification",
        "generation_classification": "generation_phrase",
        "biographical_fact": "biographical_statement",
        "source_or_transmission_symbol": "source_reference_symbol",
        "other_text": "descriptive_or_contextual_text",
        "uncertain": "uncertain_statement_or_identity",
    }[parent]


def subrole_for(
    case_id: str,
    text: str,
    parent: str,
    start: int,
    end: int,
    original: list[tuple[int, int, str, str]],
) -> str:
    clean = text.strip()
    override = MANUAL_SUBROLES.get((case_id, clean))
    if override:
        return override

    if parent == "assessment_qualification_or_scope":
        return "assessment_qualifier"

    overlaps = [
        role
        for old_start, old_end, role, _ in original
        if max(start, old_start) < min(end, old_end)
    ]
    for old_role in overlaps:
        mapped = OLD_ROLE_SUBROLE.get(old_role)
        if mapped:
            if parent == "assessment_or_grade" and mapped == "assessment_formula_or_cluster":
                return "assessment_formula_or_cluster"
            if parent == "specific_criticism_or_attributed_report" and mapped == "specific_criticism_or_report":
                return mapped
            if parent == "source_or_transmission_symbol" and mapped == "source_reference_symbol":
                return mapped
            if parent == "generation_classification" and mapped == "generation_phrase":
                return mapped
            if parent == "status_or_companion_classification" and mapped == "status_classification":
                return mapped
            if parent == "biographical_fact" and mapped not in {
                "assessment_formula_or_cluster",
                "assessment_qualifier",
                "specific_criticism_or_report",
                "status_classification",
                "generation_phrase",
                "source_reference_symbol",
            }:
                return mapped
            if parent == "narrator_name_or_identity" and mapped in {
                "full_name_or_lineage",
                "reported_personal_name",
                "nisba",
                "kunya",
                "nickname_or_laqab",
            }:
                return mapped
            if parent == "other_text" and mapped in {"pronunciation_or_lexical_note", "disambiguation_marker"}:
                return mapped
    return fallback_subrole(parent)


def main() -> None:
    outputs = (OUTPUT_CSV, OUTPUT_SHA, OUTPUT_MANIFEST, OUTPUT_MANIFEST_SHA)
    if any(path.exists() for path in outputs):
        raise FileExistsError("Granular output exists already; refusing to overwrite")

    corrected, corrected_fields = read_rows(CORRECTED_INPUT, EXPECTED_CORRECTED_SHA256)
    reviewer, _ = read_rows(REVIEWER_INPUT, EXPECTED_REVIEWER_SHA256)
    reviewer_by_case = {row["case_id"]: row for row in reviewer}
    if len(corrected) != 25 or set(reviewer_by_case) != {r["case_id"] for r in corrected}:
        raise RuntimeError("Input case sets differ or the expected 25 cases are incomplete")

    # Add one detailed subtype alongside each standardized parent role.
    before: list[str] = []
    after: list[str] = []
    seen_segments = False
    for field in corrected_fields:
        if field.startswith("segment_"):
            seen_segments = True
            continue
        (after if seen_segments else before).append(field)
    segment_fields = [
        name
        for index in range(1, MAX_SEGMENTS + 1)
        for name in (
            f"segment_{index}_text_verbatim",
            f"segment_{index}_role",
            f"segment_{index}_subrole",
        )
    ]
    fieldnames = before + segment_fields + after

    output_rows: list[dict[str, Any]] = []
    for row in corrected:
        case_id = row["case_id"]
        original = reviewer_by_case[case_id]
        source = row["entry_text_verbatim"]
        old = old_spans(original, source)
        new_row: dict[str, Any] = {field: row.get(field, "") for field in before + after}
        for index in range(1, MAX_SEGMENTS + 1):
            new_row[f"segment_{index}_text_verbatim"] = ""
            new_row[f"segment_{index}_role"] = ""
            new_row[f"segment_{index}_subrole"] = ""

        cursor = 0
        pieces: list[tuple[str, str, str]] = []
        for index in range(1, MAX_SEGMENTS + 1):
            text = row.get(f"segment_{index}_text_verbatim", "")
            parent = row.get(f"segment_{index}_role", "")
            if not text:
                continue
            if not parent:
                raise RuntimeError(f"Parent role missing in {case_id} segment {index}")
            if not source.startswith(text, cursor):
                raise RuntimeError(f"Noncontiguous source span in {case_id} segment {index}")
            start = cursor
            end = cursor + len(text)
            subrole = subrole_for(case_id, text, parent, start, end, old)
            pieces.append((text, parent, subrole))
            cursor = end
        if cursor != len(source):
            raise RuntimeError(f"Lossless source coverage failed for {case_id}")
        if len(pieces) > MAX_SEGMENTS:
            raise RuntimeError(f"Segment slot overflow in {case_id}")
        for index, (text, parent, subrole) in enumerate(pieces, start=1):
            new_row[f"segment_{index}_text_verbatim"] = text
            new_row[f"segment_{index}_role"] = parent
            new_row[f"segment_{index}_subrole"] = subrole
        output_rows.append(new_row)

    with OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="raise")
        writer.writeheader()
        writer.writerows(output_rows)

    with OUTPUT_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        reread = list(csv.DictReader(handle))
    for row in reread:
        joined = "".join(row[f"segment_{i}_text_verbatim"] for i in range(1, MAX_SEGMENTS + 1))
        if joined != row["entry_text_verbatim"]:
            raise RuntimeError(f"Round-trip failed after CSV write for {row['case_id']}")
        if any(row[f"segment_{i}_text_verbatim"] and not row[f"segment_{i}_subrole"] for i in range(1, MAX_SEGMENTS + 1)):
            raise RuntimeError(f"Subrole missing after CSV write for {row['case_id']}")

    output_hash = sha256(OUTPUT_CSV)
    OUTPUT_SHA.write_text(f"{output_hash}  {OUTPUT_CSV.name}\n", encoding="ascii", newline="\n")
    manifest = {
        "package": "Taqrib boundary pilot corrected granular copy v1.2",
        "status": "AI-assisted draft; pending human confirmation",
        "generator": "dataset_discovery/target_feasibility/add_granular_subroles_taqrib_boundary_v1_2.py",
        "inputs": {
            CORRECTED_INPUT.name: EXPECTED_CORRECTED_SHA256,
            REVIEWER_INPUT.name: EXPECTED_REVIEWER_SHA256,
        },
        "output": {OUTPUT_CSV.name: output_hash},
        "case_count": len(reread),
        "segment_fields": ["segment_N_text_verbatim", "segment_N_role", "segment_N_subrole"],
        "design": {
            "role": "consistent broad parent category used for inclusion/exclusion and high-level analysis",
            "subrole": "more specific span type retaining identity, assessment, biography, and reference distinctions",
            "no_rank_labels_added": True,
            "all_spans_reconstruct_source": True,
        },
        "limits": [
            "The 25 purposively selected entries are for boundary-protocol feasibility, not model training or held-out evaluation.",
            "Subroles are structural metadata and do not establish historical attribution, source truth, or rank.",
            "A human confirmation pass is needed before freezing the corrected segmentation.",
        ],
    }
    OUTPUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    OUTPUT_MANIFEST_SHA.write_text(
        f"{sha256(OUTPUT_MANIFEST)}  {OUTPUT_MANIFEST.name}\n",
        encoding="ascii",
        newline="\n",
    )
    print(f"Created {len(reread)} cases with broad roles and fine-grained subroles")
    print(f"CSV SHA-256: {output_hash}")


if __name__ == "__main__":
    main()
