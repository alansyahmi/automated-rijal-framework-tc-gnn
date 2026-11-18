#!/usr/bin/env python3
"""Create a corrected, review-pending copy of the Taqrib boundary pilot.

The dated reviewer submission is preserved byte-for-byte. This script repairs
lossless segmentation, uses the pilot's documented role labels, and leaves the
repaired draft explicitly pending human confirmation.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PILOT_DIR = ROOT / "data" / "2_interim" / "rijal_fyp_modelling_pipeline" / "boundary_pilot_v1"
REVIEWED_INPUT = PILOT_DIR / "BOUNDARY_PILOT_REVIEWER_ANNOTATED_2026-11-15.csv"
SOURCE_DIR = (
    ROOT
    / "data"
    / "1_raw"
    / "Shamela4_Full_DB"
    / "26__التراجم-والطبقات"
    / "3076__تقريب-التهذيب"
)
SOURCE_PAGES = SOURCE_DIR / "pages.jsonl"
SOURCE_MANIFEST = SOURCE_DIR / "manifest.json"
OUTPUT_CSV = PILOT_DIR / "BOUNDARY_PILOT_REVIEW_CORRECTED_2026-11-15.csv"
OUTPUT_SHA = PILOT_DIR / "BOUNDARY_PILOT_REVIEW_CORRECTED_2026-11-15.sha256"
OUTPUT_MANIFEST = PILOT_DIR / "BOUNDARY_PILOT_REVIEW_CORRECTED_2026-11-15_MANIFEST.json"
OUTPUT_MANIFEST_SHA = PILOT_DIR / "BOUNDARY_PILOT_REVIEW_CORRECTED_2026-11-15_MANIFEST.sha256"

EXPECTED_REVIEWED_SHA256 = "c8eb9d73e04cb180d02e0fbba886f7474d94c1c91400da2a9613845ca15e1645"
EXPECTED_PAGES_SHA256 = "45c2f611cee35f7394da23f58ded71280fbf18d99be163347d1ad38b8fc824fa"
ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
ENTRY_PREFIX = re.compile(r"^\s*[0-9٠-٩۰-۹]+\s*[-–]")
MAX_SEGMENTS = 15

ROLE_ALIASES = {
    "narrator_name_or_identity": "narrator_name_or_identity",
    "assessment_or_grade": "assessment_or_grade",
    "grade_or_assessment": "assessment_or_grade",
    "assessment_qualification_or_scope": "assessment_qualification_or_scope",
    "specific_criticism_or_attributed_report": "specific_criticism_or_attributed_report",
    "status_or_companion_classification": "status_or_companion_classification",
    "generation_classification": "generation_classification",
    "source_citation": "source_or_transmission_symbol",
    "source_citations": "source_or_transmission_symbol",
    "source_or_transmission_symbol": "source_or_transmission_symbol",
    "biographical_fact": "biographical_fact",
    "biographical_fact_residence": "biographical_fact",
    "biographical_fact_occupation": "biographical_fact",
    "biographical_fact_death": "biographical_fact",
    "death_year": "biographical_fact",
    "death_age": "biographical_fact",
    "death_location": "biographical_fact",
    "full_name": "narrator_name_or_identity",
    "name_ism": "narrator_name_or_identity",
    "nisba": "narrator_name_or_identity",
    "nisba_1": "narrator_name_or_identity",
    "nisba_2": "narrator_name_or_identity",
    "nisba_3": "narrator_name_or_identity",
    "kunya": "narrator_name_or_identity",
    "kunya_1": "narrator_name_or_identity",
    "kunya_2": "narrator_name_or_identity",
    "nickname_laqab": "narrator_name_or_identity",
    "pronunciation_guide": "other_text",
    "disambiguation_note": "other_text",
    "other_text": "other_text",
    "uncertain": "uncertain",
}

ROLE_CHOICES = {
    "source_entry_number",
    "narrator_name_or_identity",
    "assessment_or_grade",
    "assessment_qualification_or_scope",
    "specific_criticism_or_attributed_report",
    "status_or_companion_classification",
    "generation_classification",
    "biographical_fact",
    "source_or_transmission_symbol",
    "other_text",
    "uncertain",
}

GAP_LABELS = {
    ("TB-006", "آخر"): "other_text",
    ("TB-007", "من العاشرة"): "generation_classification",
}
TRAILING_SYMBOLS = {
    "TB-001": "source_or_transmission_symbol",
    "TB-020": "source_or_transmission_symbol",
}

CASE_CORRECTION_NOTES = {
    "TB-001": "Restored the omitted trailing reference symbols.",
    "TB-005": "Separated صدوق from the following qualification له أوهام.",
    "TB-006": "Restored آخر as a separate other-text span.",
    "TB-007": "Restored the omitted generation phrase من العاشرة.",
    "TB-009": "Separated the name from عن يزيد ابن هارون; retained the possible identification as uncertain.",
    "TB-010": "Restored زاهد as descriptive text and من الحادية عشرة as the generation span.",
    "TB-011": "Restored the bracketed nisba wording and يكنى, supplied the missing role, and separated the grade from its qualification.",
    "TB-014": "Kept the adjacent praise descriptors in the assessment role; no rank was assigned.",
    "TB-015": "Classified صاحب حديث as other text rather than presuming it qualifies the assessment.",
    "TB-016": "Re-segmented the identifying label, lexical note, status, reported name, biography, and omitted source symbols.",
    "TB-018": "Separated the generation wording from the trailing reference symbol خت.",
    "TB-020": "Separated صدوق from يغرب and restored the trailing reference symbol. The alternate-name note remains a hypothesis.",
    "TB-021": "Reclassified ت ق as source/reference symbols and إلا أنه يرسل as assessment qualification.",
    "TB-022": "Restored ثم and classified ت س as source/reference symbols.",
    "TB-023": "Classified تفرد الحسن بالرواية عنه as other text; the wording alone does not make it an explicit criticism.",
    "TB-024": "Restored brackets and the conjunction in the kunya list; retained the external interpretation note as out of scope.",
    "TB-025": "Separated صدوق from the following qualifying wording يخطىء.",
}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_review_rows() -> list[dict[str, str]]:
    actual_hash = file_sha256(REVIEWED_INPUT)
    if actual_hash != EXPECTED_REVIEWED_SHA256:
        raise RuntimeError(
            f"Reviewed source changed ({actual_hash}); refusing to repair an unverified input"
        )
    with REVIEWED_INPUT.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_source_entries() -> dict[tuple[int, int], tuple[str, int, int]]:
    actual_hash = file_sha256(SOURCE_PAGES)
    if actual_hash != EXPECTED_PAGES_SHA256:
        raise RuntimeError(f"Unexpected source pages hash: {actual_hash}")
    manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    recorded_hash = next(
        (item["sha256"] for item in manifest.get("files", []) if item.get("path") == "pages.jsonl"),
        None,
    )
    if recorded_hash != EXPECTED_PAGES_SHA256:
        raise RuntimeError("Source manifest hash does not match the expected frozen extraction")

    wanted_pages: set[int] = set()
    entries: dict[tuple[int, int], tuple[str, int, int]] = {}
    rows = read_review_rows()
    wanted = {
        (int(row["printed_page_number"]), int(row["entry_number_numeric"]))
        for row in rows
    }
    wanted_pages.update(page for page, _ in wanted)
    with SOURCE_PAGES.open(encoding="utf-8", newline="") as handle:
        for line in handle:
            page = json.loads(line)
            if page.get("page_num") not in wanted_pages:
                continue
            for segment in page["body"].split("\r"):
                match = re.match(r"^\s*([0-9٠-٩۰-۹]+)\s*[-–]", segment)
                if not match:
                    continue
                number = int(match.group(1).translate(ARABIC_DIGITS))
                locator = (page["page_num"], number)
                if locator in wanted:
                    if locator in entries:
                        raise RuntimeError(f"Duplicate local source entry: {locator}")
                    entries[locator] = (segment, page["page_id"], page["shamela_page_id"])
    if entries.keys() != wanted:
        raise RuntimeError(f"Source locators differ: missing={wanted - entries.keys()}")
    return entries


def split_phrase(text: str, head: str, tail: str) -> list[tuple[str, str]]:
    leading = text[: len(text) - len(text.lstrip())]
    core = text[len(leading) :]
    expected = f"{head} {tail}"
    if core != expected:
        raise RuntimeError(f"Expected exact phrase {expected!r}, got {core!r}")
    return [
        (leading + head, "assessment_or_grade"),
        (" " + tail, "assessment_qualification_or_scope"),
    ]


def original_segments(row: dict[str, str]) -> list[tuple[str, str]]:
    result = []
    for index in range(1, 30):
        text = row.get(f"segment_{index}_text_verbatim", "")
        role = row.get(f"segment_{index}_role", "")
        if text or role:
            if not text:
                raise RuntimeError(f"Role without text in {row['case_id']} segment {index}")
            result.append((text, role))
    return result


def prepare_semantic_pieces(row: dict[str, str]) -> list[tuple[str, str]]:
    case_id = row["case_id"]
    pieces = original_segments(row)

    if case_id == "TB-016":
        return [
            ("آبي اللحم", "narrator_name_or_identity"),
            (" بالمد بلفظ اسم الفاعل من الإباء", "other_text"),
            (" صحابي", "status_or_companion_classification"),
            (" غفاري", "narrator_name_or_identity"),
            (" يقال إن اسمه خلف", "uncertain"),
            (" وقيل غير ذلك", "uncertain"),
            (" استشهد بحنين", "biographical_fact"),
            (" ت س", "source_or_transmission_symbol"),
        ]

    result: list[tuple[str, str]] = []
    for text, role in pieces:
        clean = text.strip()
        leading = text[: len(text) - len(text.lstrip())]

        if case_id == "TB-009" and clean == "أحمد ابن خلاد عن يزيد ابن هارون":
            result.extend(
                [
                    (leading + "أحمد ابن خلاد", "narrator_name_or_identity"),
                    (" عن يزيد ابن هارون", "other_text"),
                ]
            )
            continue

        if case_id == "TB-005" and clean == "صدوق له أوهام":
            result.extend(split_phrase(text, "صدوق", "له أوهام"))
            continue
        if case_id == "TB-011" and clean == "صدوق تغير بأخرة":
            result.extend(split_phrase(text, "صدوق", "تغير بأخرة"))
            continue
        if case_id == "TB-020" and clean == "صدوق يغرب":
            result.extend(split_phrase(text, "صدوق", "يغرب"))
            continue
        if case_id == "TB-025" and clean == "صدوق يخطىء":
            result.extend(split_phrase(text, "صدوق", "يخطىء"))
            continue

        if case_id == "TB-018" and clean == "من السابعة أيضا خت":
            result.extend(
                [
                    (leading + "من السابعة أيضا", "generation_classification"),
                    (" خت", "source_or_transmission_symbol"),
                ]
            )
            continue

        if case_id == "TB-011" and clean == "الوهبي":
            text = leading + "[الوهبي]"
            role = "narrator_name_or_identity"
        elif case_id == "TB-011" and clean == "أبا عبيد الله":
            text = leading + "يكنى أبا عبيد الله"
            role = "narrator_name_or_identity"
        elif case_id == "TB-024" and clean == "ذو البطين":
            text = leading + "[ذو البطين]"
            role = "narrator_name_or_identity"
        elif case_id == "TB-024" and clean == "أبو زيد":
            text = leading + "وأبو زيد"
            role = "narrator_name_or_identity"
        elif case_id == "TB-022" and clean == "الكوفي":
            text = leading + "ثم الكوفي"
            role = "narrator_name_or_identity"

        if case_id == "TB-011" and clean == "من الحادية عشرة" and not role.strip():
            role = "generation_classification"

        canonical_role = ROLE_ALIASES.get(role)
        if canonical_role is None:
            raise RuntimeError(f"Unmapped role {role!r} in {case_id}")
        if case_id == "TB-014" and clean in {"فقيه", "حجة"}:
            canonical_role = "assessment_or_grade"
        if case_id == "TB-015" and clean == "صاحب حديث":
            canonical_role = "other_text"
        if case_id == "TB-021" and clean == "إلا أنه يرسل":
            canonical_role = "assessment_qualification_or_scope"
        if case_id in {"TB-021", "TB-022"} and clean in {"ت ق", "ت س"}:
            canonical_role = "source_or_transmission_symbol"
        if case_id == "TB-023" and clean == "تفرد الحسن بالرواية عنه":
            canonical_role = "other_text"
        if case_id == "TB-009" and clean == "يحتمل أن يكون هو ابن خالد الخلال":
            canonical_role = "uncertain"

        result.append((text, canonical_role))
    return result


def missing_gap_pieces(case_id: str, gap: str) -> list[tuple[str, str]]:
    if not gap:
        return []
    if gap.isspace():
        return [(gap, "__SPACE_ONLY__")]
    normalized = gap.strip()
    role = GAP_LABELS.get((case_id, normalized))
    if role:
        return [(gap, role)]
    if case_id == "TB-010" and normalized == "زاهد من الحادية عشرة":
        leading_count = len(gap) - len(gap.lstrip())
        trailing_count = len(gap) - len(gap.rstrip())
        leading = gap[:leading_count]
        trailing = gap[len(gap) - trailing_count :] if trailing_count else ""
        body = gap[leading_count : len(gap) - trailing_count if trailing_count else len(gap)]
        first, second = "زاهد", "من الحادية عشرة"
        expected = f"{first} {second}"
        if body != expected:
            raise RuntimeError(f"Unexpected TB-010 gap: {gap!r}")
        return [
            (leading + first, "other_text"),
            (" " + second + trailing, "generation_classification"),
        ]
    raise RuntimeError(f"Unclassified missing source text in {case_id}: {gap!r}")


def make_lossless_segments(row: dict[str, str], source: str) -> list[tuple[str, str]]:
    case_id = row["case_id"]
    match = ENTRY_PREFIX.match(source)
    if not match:
        raise RuntimeError(f"Could not identify source entry prefix for {case_id}")
    prefix = match.group(0)
    pieces: list[tuple[str, str]] = [(prefix, "source_entry_number")]
    cursor = len(prefix)

    for text, role in prepare_semantic_pieces(row):
        start = source.find(text, cursor)
        if start < 0:
            raise RuntimeError(f"Span not found in source for {case_id}: {text!r}")
        gap = source[cursor:start]
        for gap_text, gap_role in missing_gap_pieces(case_id, gap):
            if gap_role == "__SPACE_ONLY__":
                text = gap_text + text
            else:
                pieces.append((gap_text, gap_role))
        pieces.append((text, role))
        cursor = start + len(text) - len(gap) if gap.isspace() else start + len(text)

    tail = source[cursor:]
    if tail:
        if tail.isspace():
            text, role = pieces[-1]
            pieces[-1] = (text + tail, role)
        else:
            tail_role = TRAILING_SYMBOLS.get(case_id)
            if tail_role is None:
                raise RuntimeError(f"Unclassified trailing source text in {case_id}: {tail!r}")
            pieces.append((tail, tail_role))

    if "".join(text for text, _ in pieces) != source:
        raise RuntimeError(f"Lossless reconstruction failed for {case_id}")
    if any(role not in ROLE_CHOICES for _, role in pieces):
        raise RuntimeError(f"Unsupported role in repaired segments for {case_id}")
    return pieces


def output_fieldnames(input_fieldnames: list[str]) -> list[str]:
    before = []
    after = []
    found_segment = False
    for field in input_fieldnames:
        if field.startswith("segment_"):
            found_segment = True
            continue
        if not found_segment:
            before.append(field)
        else:
            after.append(field)
    segment_fields = [
        name
        for index in range(1, MAX_SEGMENTS + 1)
        for name in (f"segment_{index}_text_verbatim", f"segment_{index}_role")
    ]
    after.extend(
        [
            "original_reviewer_completion_value",
            "original_reviewer_confidence_value",
            "correction_status",
            "correction_notes",
        ]
    )
    return before + segment_fields + after


def main() -> None:
    for path in (REVIEWED_INPUT, SOURCE_PAGES, SOURCE_MANIFEST):
        if not path.is_file():
            raise FileNotFoundError(path)
    outputs = (OUTPUT_CSV, OUTPUT_SHA, OUTPUT_MANIFEST, OUTPUT_MANIFEST_SHA)
    if any(path.exists() for path in outputs):
        raise FileExistsError("A corrected boundary-pilot output already exists; refusing to overwrite it")

    rows = read_review_rows()
    source_entries = read_source_entries()
    if len(rows) != 25:
        raise RuntimeError(f"Expected 25 reviewed cases; found {len(rows)}")

    original_header = list(rows[0].keys())
    fieldnames = output_fieldnames(original_header)
    corrected_rows: list[dict[str, Any]] = []

    for row in rows:
        case_id = row["case_id"]
        locator = (int(row["printed_page_number"]), int(row["entry_number_numeric"]))
        source, local_page_id, shamela_page_id = source_entries[locator]
        if source != row["entry_text_verbatim"]:
            raise RuntimeError(f"Original source entry was edited in the reviewed CSV: {case_id}")
        if int(row["local_page_id"]) != local_page_id or int(row["shamela_page_id"]) != shamela_page_id:
            raise RuntimeError(f"Source page IDs differ for {case_id}")

        pieces = make_lossless_segments(row, source)
        if len(pieces) > MAX_SEGMENTS:
            raise RuntimeError(f"Need more than {MAX_SEGMENTS} segment slots for {case_id}")

        new_row = {field: row.get(field, "") for field in fieldnames if field in row}
        for index in range(1, MAX_SEGMENTS + 1):
            new_row[f"segment_{index}_text_verbatim"] = ""
            new_row[f"segment_{index}_role"] = ""
        for index, (text, role) in enumerate(pieces, start=1):
            new_row[f"segment_{index}_text_verbatim"] = text
            new_row[f"segment_{index}_role"] = role

        new_row["original_reviewer_completion_value"] = row.get("boundary_review_complete", "")
        new_row["original_reviewer_confidence_value"] = row.get("boundary_confidence", "")
        new_row["boundary_review_complete"] = "no"
        new_row["boundary_confidence"] = ""
        new_row["correction_status"] = "AI_REPAIRED_PENDING_HUMAN_CONFIRMATION"
        new_row["correction_notes"] = CASE_CORRECTION_NOTES.get(
            case_id,
            "Restored exact source spacing and entry marker; standardized role labels. No rank assigned.",
        )

        if case_id == "TB-016":
            note = row.get("reviewer_notes", "")
            new_row["reviewer_notes"] = (
                "[Out-of-scope inference, not checked in this audit; not part of the source-span annotation.] "
                + note
            )
        elif case_id == "TB-020":
            note = row.get("reviewer_notes", "")
            new_row["reviewer_notes"] = (
                "[Hypothesis only; the proposed alternate full name is not stated verbatim as a complete name in the entry.] "
                + note
            )
        elif case_id == "TB-024":
            note = row.get("reviewer_notes", "")
            new_row["reviewer_notes"] = (
                "[Out-of-scope external interpretation; not verified in this boundary audit.] " + note
            )
        corrected_rows.append(new_row)

    with OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="raise")
        writer.writeheader()
        writer.writerows(corrected_rows)

    with OUTPUT_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        reread = list(csv.DictReader(handle))
    if len(reread) != 25:
        raise RuntimeError("Corrected CSV round-trip changed the case count")
    for row in reread:
        reconstructed = "".join(
            row[f"segment_{index}_text_verbatim"] for index in range(1, MAX_SEGMENTS + 1)
        )
        if reconstructed != row["entry_text_verbatim"]:
            raise RuntimeError(f"Corrected CSV round-trip failed for {row['case_id']}")
        if row["boundary_review_complete"] != "no" or row["boundary_confidence"]:
            raise RuntimeError(f"Human confirmation state is misleading for {row['case_id']}")

    output_hash = file_sha256(OUTPUT_CSV)
    OUTPUT_SHA.write_text(f"{output_hash}  {OUTPUT_CSV.name}\n", encoding="ascii", newline="\n")
    manifest = {
        "package": "Taqrib boundary pilot corrected draft v1.1",
        "status": "AI repaired; pending human confirmation",
        "generator": "dataset_discovery/target_feasibility/repair_taqrib_boundary_review_v1_1.py",
        "inputs": {
            "reviewer_submission": {
                "path": REVIEWED_INPUT.relative_to(ROOT).as_posix(),
                "sha256": file_sha256(REVIEWED_INPUT),
            },
            "source_pages": {
                "path": SOURCE_PAGES.relative_to(ROOT).as_posix(),
                "sha256": file_sha256(SOURCE_PAGES),
            },
            "source_manifest": {
                "path": SOURCE_MANIFEST.relative_to(ROOT).as_posix(),
                "sha256": file_sha256(SOURCE_MANIFEST),
            },
        },
        "outputs": {
            OUTPUT_CSV.name: output_hash,
        },
        "method": [
            "Preserved all original reviewer data in the dated input copy; generated a separate corrected draft.",
            "Restored exact source coverage, including entry-number prefixes, spaces, punctuation, and identified omitted text.",
            "Standardized roles to the pilot guide, with source_entry_number added for the printed entry marker.",
            "No rank number, historical attribution, or reliability judgment was assigned.",
            "All completion flags are no and confidence fields blank until the reviewer confirms the repaired draft.",
        ],
        "case_count": 25,
        "max_segment_slots": MAX_SEGMENTS,
        "all_segment_concatenations_match_source": True,
    }
    OUTPUT_MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    OUTPUT_MANIFEST_SHA.write_text(
        f"{file_sha256(OUTPUT_MANIFEST)}  {OUTPUT_MANIFEST.name}\n",
        encoding="ascii",
        newline="\n",
    )
    print(f"Created corrected draft: {OUTPUT_CSV}")
    print(f"Cases: {len(reread)}; exact source reconstructions: 25/25")
    print(f"Corrected CSV SHA-256: {output_hash}")


if __name__ == "__main__":
    main()
