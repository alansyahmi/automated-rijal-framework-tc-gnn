#!/usr/bin/env python3
"""Freeze the user-approved granular Taqrib boundary revision v1.3."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline/boundary_pilot_v1"
REVISION_DIR = BASE / "granular_revision_v1_3_2026-11-15"
REVISION_MANIFEST_PATH = REVISION_DIR / "REVISION_MANIFEST.json"
DRAFT_PATH = REVISION_DIR / "TAQRIB_BOUNDARY_ANNOTATIONS_GRANULAR_V1_3_DRAFT.csv"
LEDGER_PATH = REVISION_DIR / "ORIGINAL_REVIEWER_LABEL_LEDGER.csv"
PRIOR_FREEZE_PATH = BASE / "frozen_2026-11-15/TAQRIB_BOUNDARY_ANNOTATIONS_FROZEN_V1.csv"
OUTPUT_DIR = BASE / "frozen_v1_3_2026-11-15"
FROZEN_NAME = "TAQRIB_BOUNDARY_ANNOTATIONS_FROZEN_V1_3.csv"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    if OUTPUT_DIR.exists():
        raise SystemExit(f"Refusing to overwrite frozen package: {OUTPUT_DIR}")

    revision_manifest = json.loads(REVISION_MANIFEST_PATH.read_text(encoding="utf-8"))
    expected_draft = revision_manifest["outputs"][DRAFT_PATH.name]
    expected_ledger = revision_manifest["outputs"][LEDGER_PATH.name]
    if sha256(DRAFT_PATH) != expected_draft:
        raise SystemExit("v1.3 draft hash differs from its revision manifest")
    if sha256(LEDGER_PATH) != expected_ledger:
        raise SystemExit("Original label ledger hash differs from its revision manifest")

    with DRAFT_PATH.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    if len(rows) != 25:
        raise SystemExit(f"Expected 25 annotation rows; found {len(rows)}")
    if "revision_status" not in fields or "freeze_status" in fields:
        raise SystemExit("Unexpected v1.3 draft status fields")

    fields.insert(fields.index("revision_status") + 1, "freeze_status")
    for row in rows:
        row["revision_status"] = "approved_and_frozen_2026-11-15"
        row["freeze_status"] = "frozen_on_user_approval_2026-11-15"

    OUTPUT_DIR.mkdir(parents=True)
    frozen_csv = OUTPUT_DIR / FROZEN_NAME
    with frozen_csv.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    frozen_ledger = OUTPUT_DIR / "ORIGINAL_REVIEWER_LABEL_LEDGER.csv"
    shutil.copyfile(LEDGER_PATH, frozen_ledger)

    readme = """# Taqrīb boundary annotations: frozen granular revision v1.3

This snapshot was frozen after the user explicitly approved the v1.3 granular-label revision on 2026-11-15. It supersedes v1.2 for the current annotation view while preserving the earlier v1 and v1.2 artifacts unchanged.

The package preserves the original reviewer segment labels in a linked ledger, restores indexed nisba/kunya subroles where the mapping is one-to-one, and separates TB-022 `ثم` as `temporal_transition` from `الكوفي` as `nisba_2`.

The annotation remains single-reviewer and AI-assisted. The freeze does not claim independent expert validation, inter-reviewer reliability, historical attribution, or model readiness. No rank labels were assigned.
"""
    (OUTPUT_DIR / "README.md").write_text(readme, encoding="utf-8", newline="\n")

    output_names = [FROZEN_NAME, frozen_ledger.name, "README.md"]
    manifest: dict[str, Any] = {
        "package": "Taqrib boundary annotations frozen granular revision v1.3",
        "version": "1.3",
        "status": "frozen_on_user_approval_2026-11-15",
        "user_authorized_freeze": True,
        "approval_basis": "The user explicitly approved the v1.3 granular-label revision in conversation.",
        "review_status": "single-reviewer, AI-assisted; no independent expert review claimed",
        "case_count": len(rows),
        "original_reviewer_label_count": 189,
        "rank_labels_assigned": 0,
        "no_model_training": True,
        "inputs": {
            "v1_3_draft": {
                "path": str(DRAFT_PATH.relative_to(ROOT)).replace("\\", "/"),
                "sha256": sha256(DRAFT_PATH),
            },
            "original_reviewer_label_ledger": {
                "path": str(LEDGER_PATH.relative_to(ROOT)).replace("\\", "/"),
                "sha256": sha256(LEDGER_PATH),
            },
            "v1_frozen_snapshot": {
                "path": str(PRIOR_FREEZE_PATH.relative_to(ROOT)).replace("\\", "/"),
                "sha256": sha256(PRIOR_FREEZE_PATH),
            },
            "v1_3_revision_manifest": {
                "path": str(REVISION_MANIFEST_PATH.relative_to(ROOT)).replace("\\", "/"),
                "sha256": sha256(REVISION_MANIFEST_PATH),
            },
        },
        "outputs": {name: sha256(OUTPUT_DIR / name) for name in output_names},
        "manifest_hash_note": "This manifest does not hash itself; FREEZE_MANIFEST.sha256 records its SHA-256.",
    }
    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    manifest_path = OUTPUT_DIR / "FREEZE_MANIFEST.json"
    manifest_path.write_bytes(manifest_bytes)
    (OUTPUT_DIR / "FREEZE_MANIFEST.sha256").write_text(
        f"{hashlib.sha256(manifest_bytes).hexdigest()}  FREEZE_MANIFEST.json\n",
        encoding="ascii", newline="\n",
    )
    print(json.dumps({
        "frozen_csv": str(frozen_csv),
        "case_count": len(rows),
        "frozen_csv_sha256": sha256(frozen_csv),
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
    }, indent=2))


if __name__ == "__main__":
    main()
