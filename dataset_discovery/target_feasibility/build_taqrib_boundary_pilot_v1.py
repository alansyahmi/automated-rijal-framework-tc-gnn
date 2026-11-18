#!/usr/bin/env python3
"""Build a fixed, annotation-blank sample for Taqrib entry-boundary review.

This is a purposive boundary pilot, not a rank classifier or a statistical sample.
The script copies exact entry segments from the frozen local pages.jsonl extract.
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
INPUT_DIR = (
    ROOT
    / "data"
    / "1_raw"
    / "Shamela4_Full_DB"
    / "26__التراجم-والطبقات"
    / "3076__تقريب-التهذيب"
)
INPUT_PATH = INPUT_DIR / "pages.jsonl"
INPUT_MANIFEST_PATH = INPUT_DIR / "manifest.json"
GUIDE_SOURCE_PATH = ROOT / "dataset_discovery" / "target_feasibility" / "TAQRIB_BOUNDARY_PILOT_GUIDE_V1.md"
OUTPUT_DIR = ROOT / "data" / "2_interim" / "rijal_fyp_modelling_pipeline" / "boundary_pilot_v1"

EXPECTED_INPUT_SHA256 = "45c2f611cee35f7394da23f58ded71280fbf18d99be163347d1ad38b8fc824fa"
BOOK_ID = 3076
SHAMELA_BOOK_ID = 8609

# Fixed purposive sample. These locators were selected to expose different
# boundary problems, not to represent the frequency of constructions in Taqrib.
SELECTED_LOCATORS = (
    (77, 1),
    (77, 3),
    (77, 5),
    (77, 9),
    (77, 12),
    (78, 14),
    (78, 17),
    (79, 34),
    (79, 35),
    (81, 54),
    (82, 67),
    (82, 68),
    (83, 82),
    (84, 96),
    (85, 110),
    (86, 131),
    (87, 136),
    (88, 148),
    (88, 150),
    (90, 181),
    (90, 182),
    (93, 233),
    (96, 287),
    (98, 316),
    (110, 491),
)

ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
ENTRY_PREFIX = re.compile(r"^\s*([0-9٠-٩۰-۹]+)\s*[-–]")
SEGMENT_COUNT = 10


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_entry_number(segment: str) -> tuple[str, int] | None:
    match = ENTRY_PREFIX.match(segment)
    if not match:
        return None
    original = match.group(1)
    return original, int(original.translate(ARABIC_DIGITS))


def load_selected_entries() -> list[dict[str, Any]]:
    actual_hash = sha256(INPUT_PATH)
    if actual_hash != EXPECTED_INPUT_SHA256:
        raise RuntimeError(
            f"Unexpected pages.jsonl SHA-256: {actual_hash}; "
            f"expected {EXPECTED_INPUT_SHA256}"
        )

    manifest = json.loads(INPUT_MANIFEST_PATH.read_text(encoding="utf-8"))
    manifest_hash = next(
        (item["sha256"] for item in manifest.get("files", []) if item.get("path") == "pages.jsonl"),
        None,
    )
    if manifest_hash != EXPECTED_INPUT_SHA256:
        raise RuntimeError("The source manifest does not record the expected pages.jsonl hash")

    wanted = set(SELECTED_LOCATORS)
    found: dict[tuple[int, int], dict[str, Any]] = {}
    with INPUT_PATH.open(encoding="utf-8", newline="") as handle:
        for line in handle:
            page = json.loads(line)
            if page.get("book_id") != BOOK_ID or page.get("page_num") not in {p for p, _ in wanted}:
                continue
            for segment in page["body"].split("\r"):
                parsed = parse_entry_number(segment)
                if parsed is None:
                    continue
                entry_number_verbatim, entry_number = parsed
                locator = (page["page_num"], entry_number)
                if locator not in wanted:
                    continue
                if locator in found:
                    raise RuntimeError(f"Duplicate selected locator found: {locator}")
                found[locator] = {
                    "printed_page_number": page["page_num"],
                    "entry_number_numeric": entry_number,
                    "entry_number_verbatim": entry_number_verbatim,
                    "local_page_id": page["page_id"],
                    "shamela_page_id": page["shamela_page_id"],
                    # Keep this exact split segment; do not trim, normalize, or edit Arabic.
                    "entry_text_verbatim": segment,
                }

    missing = wanted - found.keys()
    if missing:
        raise RuntimeError(f"Selected locators not found in the frozen source: {sorted(missing)}")

    rows: list[dict[str, Any]] = []
    for index, locator in enumerate(SELECTED_LOCATORS, start=1):
        source = found[locator]
        row: dict[str, Any] = {
            "case_id": f"TB-{index:03d}",
            "source_work": "تقريب التهذيب",
            "local_book_id": BOOK_ID,
            "shamela_book_id": SHAMELA_BOOK_ID,
            **source,
        }
        for segment_index in range(1, SEGMENT_COUNT + 1):
            row[f"segment_{segment_index}_text_verbatim"] = ""
            row[f"segment_{segment_index}_role"] = ""
        row["boundary_review_complete"] = ""
        row["boundary_confidence"] = ""
        row["unassigned_or_overlapping_text_notes"] = ""
        row["reviewer_notes"] = ""
        rows.append(row)
    return rows


def output_columns() -> list[str]:
    columns = [
        "case_id",
        "source_work",
        "local_book_id",
        "shamela_book_id",
        "local_page_id",
        "shamela_page_id",
        "printed_page_number",
        "entry_number_numeric",
        "entry_number_verbatim",
        "entry_text_verbatim",
    ]
    for segment_index in range(1, SEGMENT_COUNT + 1):
        columns.extend(
            [
                f"segment_{segment_index}_text_verbatim",
                f"segment_{segment_index}_role",
            ]
        )
    columns.extend(
        [
            "boundary_review_complete",
            "boundary_confidence",
            "unassigned_or_overlapping_text_notes",
            "reviewer_notes",
        ]
    )
    return columns


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=output_columns(), extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)

    # Verify round-trip preservation of every source Arabic string and blank field.
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        round_trip = list(csv.DictReader(handle))
    if len(round_trip) != len(rows):
        raise RuntimeError("CSV round-trip row count changed")
    for original, restored in zip(rows, round_trip, strict=True):
        for key in ("case_id", "entry_text_verbatim", "entry_number_verbatim"):
            if restored[key] != original[key]:
                raise RuntimeError(f"CSV round-trip mismatch in {key} for {original['case_id']}")
        for key in output_columns():
            if key.startswith("segment_") or key in {
                "boundary_review_complete",
                "boundary_confidence",
                "unassigned_or_overlapping_text_notes",
                "reviewer_notes",
            }:
                if restored[key] != "":
                    raise RuntimeError(f"Annotation field is not blank: {original['case_id']} {key}")


def main() -> None:
    for required_path in (INPUT_PATH, INPUT_MANIFEST_PATH, GUIDE_SOURCE_PATH):
        if not required_path.is_file():
            raise FileNotFoundError(f"Required input is missing: {required_path}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    existing = list(OUTPUT_DIR.iterdir())
    if existing:
        raise FileExistsError(
            f"Refusing to overwrite a non-empty output directory: {OUTPUT_DIR}"
        )

    rows = load_selected_entries()
    csv_path = OUTPUT_DIR / "BOUNDARY_PILOT_REVIEW.csv"
    guide_path = OUTPUT_DIR / "REVIEW_GUIDE.md"
    write_csv(csv_path, rows)
    shutil.copyfile(GUIDE_SOURCE_PATH, guide_path)

    manifest = {
        "package": "Taqrib textual-boundary pilot v1",
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "generator": "dataset_discovery/target_feasibility/build_taqrib_boundary_pilot_v1.py",
        "sampling": {
            "method": "fixed purposive boundary-challenge sample",
            "seed": None,
            "row_count": len(rows),
            "selected_locators_printed_page_and_entry_number": [list(x) for x in SELECTED_LOCATORS],
        },
        "inputs": {
            "pages_jsonl": {
                "path": INPUT_PATH.relative_to(ROOT).as_posix(),
                "sha256": sha256(INPUT_PATH),
            },
            "source_manifest": {
                "path": INPUT_MANIFEST_PATH.relative_to(ROOT).as_posix(),
                "sha256": sha256(INPUT_MANIFEST_PATH),
            },
            "review_guide_source": {
                "path": GUIDE_SOURCE_PATH.relative_to(ROOT).as_posix(),
                "sha256": sha256(GUIDE_SOURCE_PATH),
            },
        },
        "outputs": {
            "BOUNDARY_PILOT_REVIEW.csv": sha256(csv_path),
            "REVIEW_GUIDE.md": sha256(guide_path),
        },
        "limitations": [
            "Purposive sample; not suitable for estimating corpus-wide frequencies.",
            "No rank labels or automated suggestions are supplied.",
            "Text is copied from the local extraction; printed-edition accuracy is not established.",
            "No historical attribution, reliability, or target-eligibility conclusions are made.",
        ],
    }
    manifest_path = OUTPUT_DIR / "MANIFEST.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (OUTPUT_DIR / "MANIFEST.sha256").write_text(
        f"{sha256(manifest_path)}  MANIFEST.json\n",
        encoding="ascii",
        newline="\n",
    )

    print(f"Created {len(rows)} blank review rows at {csv_path}")
    print(f"Input SHA-256: {sha256(INPUT_PATH)}")
    print(f"CSV SHA-256: {sha256(csv_path)}")
    print(f"Manifest SHA-256: {sha256(manifest_path)}")


if __name__ == "__main__":
    main()
