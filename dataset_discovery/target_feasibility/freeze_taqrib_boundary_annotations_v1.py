#!/usr/bin/env python3
"""Freeze the user-approved, AI-assisted Taqrib boundary annotation snapshot."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PILOT_DIR = ROOT / "data" / "2_interim" / "rijal_fyp_modelling_pipeline" / "boundary_pilot_v1"
INPUT_CSV = PILOT_DIR / "BOUNDARY_PILOT_REVIEW_CORRECTED_GRANULAR_2026-11-15.csv"
ORIGINAL_REVIEW = PILOT_DIR / "BOUNDARY_PILOT_REVIEWER_ANNOTATED_2026-11-15.csv"
SOURCE_PAGES = ROOT / "data" / "1_raw" / "Shamela4_Full_DB" / "26__التراجم-والطبقات" / "3076__تقريب-التهذيب" / "pages.jsonl"
SOURCE_MANIFEST = SOURCE_PAGES.parent / "manifest.json"
OUTPUT_DIR = PILOT_DIR / "frozen_2026-11-15"
OUTPUT_CSV = OUTPUT_DIR / "TAQRIB_BOUNDARY_ANNOTATIONS_FROZEN_V1.csv"
OUTPUT_MANIFEST = OUTPUT_DIR / "FREEZE_MANIFEST.json"
OUTPUT_MANIFEST_SHA = OUTPUT_DIR / "FREEZE_MANIFEST.sha256"
OUTPUT_README = OUTPUT_DIR / "README.md"

EXPECTED_INPUT_SHA256 = "168d7f3ad5b9ea77bc19b56215e69d2acee157719038424ce01c5dd73eedcafe"
EXPECTED_REVIEWER_SHA256 = "c8eb9d73e04cb180d02e0fbba886f7474d94c1c91400da2a9613845ca15e1645"
EXPECTED_PAGES_SHA256 = "45c2f611cee35f7394da23f58ded71280fbf18d99be163347d1ad38b8fc824fa"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    for path in (INPUT_CSV, ORIGINAL_REVIEW, SOURCE_PAGES, SOURCE_MANIFEST):
        if not path.is_file():
            raise FileNotFoundError(path)
    if sha256(INPUT_CSV) != EXPECTED_INPUT_SHA256:
        raise RuntimeError("The granular corrected input changed; refusing an unverified freeze")
    if sha256(ORIGINAL_REVIEW) != EXPECTED_REVIEWER_SHA256:
        raise RuntimeError("The original reviewer snapshot changed; refusing an unverified freeze")
    if sha256(SOURCE_PAGES) != EXPECTED_PAGES_SHA256:
        raise RuntimeError("The local Taqrib source changed; refusing an unverified freeze")
    if OUTPUT_DIR.exists():
        raise FileExistsError(f"Refusing to overwrite freeze directory: {OUTPUT_DIR}")

    with INPUT_CSV.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])
    if len(rows) != 25:
        raise RuntimeError(f"Expected 25 cases, found {len(rows)}")
    if any(row.get("correction_status") != "AI_REPAIRED_PENDING_HUMAN_CONFIRMATION" for row in rows):
        raise RuntimeError("Unexpected correction status in source snapshot")
    if {row.get("original_reviewer_confidence_value") for row in rows} != {"100%"}:
        raise RuntimeError("Original reviewer confidence values differ from the documented mapping basis")

    if "confidence_basis" in fieldnames or "freeze_status" in fieldnames:
        raise RuntimeError("Freeze metadata columns already exist in the source snapshot")
    fieldnames.extend(["confidence_basis", "freeze_status"])

    for row in rows:
        joined = "".join(
            row.get(f"segment_{index}_text_verbatim", "") for index in range(1, 16)
        )
        if joined != row["entry_text_verbatim"]:
            raise RuntimeError(f"Source reconstruction failed for {row['case_id']}")
        row["boundary_review_complete"] = "yes"
        row["boundary_confidence"] = "high"
        row["correction_status"] = "FROZEN_USER_APPROVED_WITH_AI_ASSISTANCE"
        row["confidence_basis"] = (
            "Original reviewer self-rating 100%, mapped to high after explicit user approval "
            "of AI-assisted repairs; subjective and not probability-calibrated."
        )
        row["freeze_status"] = "frozen_on_user_authorization_2026-11-15"

    OUTPUT_DIR.mkdir(parents=True, exist_ok=False)
    with OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)

    with OUTPUT_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        round_trip = list(csv.DictReader(handle))
    if len(round_trip) != 25:
        raise RuntimeError("Frozen CSV round-trip changed case count")
    for row in round_trip:
        if row["boundary_review_complete"] != "yes" or row["boundary_confidence"] != "high":
            raise RuntimeError(f"Freeze state failed for {row['case_id']}")
        if "".join(row[f"segment_{i}_text_verbatim"] for i in range(1, 16)) != row["entry_text_verbatim"]:
            raise RuntimeError(f"Frozen source reconstruction failed for {row['case_id']}")

    manifest = {
        "package": "Taqrib boundary annotations frozen v1",
        "frozen_on": "2026-11-15",
        "authorization": "User explicitly instructed the assistant to freeze the AI-assisted annotations.",
        "annotation_status": "frozen; AI-assisted; single-researcher study",
        "case_count": 25,
        "source_entry_reconstructions_exact": 25,
        "inputs": {
            INPUT_CSV.name: {
                "path": INPUT_CSV.relative_to(ROOT).as_posix(),
                "sha256": sha256(INPUT_CSV),
            },
            ORIGINAL_REVIEW.name: {
                "path": ORIGINAL_REVIEW.relative_to(ROOT).as_posix(),
                "sha256": sha256(ORIGINAL_REVIEW),
            },
            SOURCE_PAGES.name: {
                "path": SOURCE_PAGES.relative_to(ROOT).as_posix(),
                "sha256": sha256(SOURCE_PAGES),
            },
            SOURCE_MANIFEST.name: {
                "path": SOURCE_MANIFEST.relative_to(ROOT).as_posix(),
                "sha256": sha256(SOURCE_MANIFEST),
            },
        },
        "outputs": {
            OUTPUT_CSV.name: sha256(OUTPUT_CSV),
        },
        "confidence_note": (
            "The original human self-rating of 100% was mapped to the protocol's high category "
            "after the user's explicit approval. This is subjective confidence in the boundary review, "
            "not calibrated probability, independent expert validation, or inter-reviewer agreement."
        ),
        "preserved_limits": [
            "This annotation freezes textual boundaries and structural roles only.",
            "It assigns none of Ibn Hajar's twelve ranks.",
            "Uncertain passages remain labelled uncertain; freezing preserves that uncertainty.",
            "It does not establish historical attribution, truth, narrator reliability, or model-target eligibility.",
        ],
    }
    OUTPUT_MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    OUTPUT_MANIFEST_SHA.write_text(
        f"{sha256(OUTPUT_MANIFEST)}  {OUTPUT_MANIFEST.name}\n",
        encoding="ascii",
        newline="\n",
    )
    OUTPUT_README.write_text(
        "# Frozen Taqrīb Boundary Annotations v1\n\n"
        "This is the user-approved freeze of the 25-case AI-assisted textual-boundary pilot. "
        "The dated reviewer submission and pre-freeze corrected versions remain unchanged.\n\n"
        "- `TAQRIB_BOUNDARY_ANNOTATIONS_FROZEN_V1.csv` is the frozen table.\n"
        "- `FREEZE_MANIFEST.json` records authorization, inputs, output hash, and limits.\n"
        "- `FREEZE_MANIFEST.sha256` contains the manifest checksum.\n\n"
        "The freeze records boundary and role annotations only. No ranks were assigned, and uncertain spans remain uncertain. "
        "The confidence field maps the original reviewer self-rating of 100% to `high` after user approval; this is not calibrated probability or independent validation.\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"Frozen 25 annotations at {OUTPUT_DIR}")
    print(f"CSV SHA-256: {sha256(OUTPUT_CSV)}")


if __name__ == "__main__":
    main()
