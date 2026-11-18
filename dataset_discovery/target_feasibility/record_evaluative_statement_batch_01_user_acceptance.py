#!/usr/bin/env python3
"""Record the user's acceptance of every row in AI advisory batch 01.

The AI proposal package remains untouched. This writes a separate, versioned
decision package whose acceptance scope is the selected occurrence per row.
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PIPELINE = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline"
AI_DIR = PIPELINE / "evaluation_statement_occurrence_review_v0_1_2026-11-16"
AI_CSV = AI_DIR / "AI_ADVISORY_REVIEW_BATCH_01.csv"
AI_MANIFEST = AI_DIR / "MANIFEST.json"
OUTPUT = PIPELINE / "evaluation_statement_occurrence_user_decisions_batch_01_v0_1_2026-11-16"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if OUTPUT.exists() and any(OUTPUT.iterdir()):
        raise SystemExit(f"Refusing to overwrite an existing decision package: {OUTPUT}")

    source_manifest = json.loads(AI_MANIFEST.read_text(encoding="utf-8"))
    if digest(AI_CSV) != source_manifest["outputs"][AI_CSV.name]:
        raise SystemExit("AI advisory CSV does not match its recorded output hash")

    with AI_CSV.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
        fields = list(rows[0]) if rows else []
    if len(rows) != 33 or len({row["advisory_id"] for row in rows}) != 33:
        raise SystemExit("Expected 33 unique advisory rows")

    timestamp = datetime.now(timezone.utc).isoformat()
    for row in rows:
        row["human_decision"] = "accept"
        row["human_notes"] = "User accepted all AI-proposed fields for this selected occurrence only."
        row["user_decision_recorded_utc"] = timestamp
        row["user_decision_scope"] = "Selected occurrence in this row only; no phrase-wide generalization."
    fields += ["user_decision_recorded_utc", "user_decision_scope"]

    OUTPUT.mkdir(parents=True, exist_ok=True)
    decisions_path = OUTPUT / "HUMAN_DECISIONS_BATCH_01.csv"
    with decisions_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\r\n")
        writer.writeheader()
        writer.writerows(rows)

    readme_path = OUTPUT / "README.md"
    readme = f"""# User decisions for AI advisory batch 01

**Status:** all 33 AI proposals were accepted by the user in this conversation. This is a single-reviewer decision record, not independent expert validation.

## Decision and scope

The user said: “i accept all”. In response, `human_decision=accept` is recorded for all 33 rows. Under the review instructions, acceptance means the user accepts all proposed descriptor fields for that row's selected local occurrence. It does **not** accept the same interpretation for every occurrence of that phrase, establish historical accuracy or source independence, assign a canonical rank, or authorize a numeric score.

The 33 rows cover {len({row['entry_id'] for row in rows})} distinct entries. Their original AI proposal package remains unchanged at `../evaluation_statement_occurrence_review_v0_1_2026-11-16/`; this folder is the separate decision copy. Original phrase occurrence counts are retained as context, not as a reviewed denominator.

## File

- `HUMAN_DECISIONS_BATCH_01.csv` contains the AI proposal fields, complete source entry, locator, and the recorded user decisions. Rank and numeric-score fields remain blank.
- `MANIFEST.json` records the source and output hashes. `MANIFEST.sha256` records the manifest hash separately.

Do not interpret these 33 accepted examples as exhaustive review or validation of the full 11,478-hit occurrence inventory.
"""
    readme_path.write_text(readme, encoding="utf-8", newline="\n")

    inputs = [AI_CSV, AI_MANIFEST, Path(__file__).resolve()]
    outputs = [decisions_path, readme_path]
    manifest = {
        "package_id": OUTPUT.name,
        "generated_at_utc": timestamp,
        "decision_basis": "The user explicitly accepted all proposals in AI advisory review batch 01.",
        "decision_scope": "Acceptance applies to all proposed fields for each selected occurrence only; it does not generalize to all phrase hits.",
        "counts": {
            "rows": len(rows),
            "distinct_entries": len({row["entry_id"] for row in rows}),
            "accepted_rows": sum(row["human_decision"] == "accept" for row in rows),
            "canonical_ranks_assigned": sum(bool(row["canonical_rank"]) for row in rows),
            "numeric_scores_assigned": sum(bool(row["numeric_score"]) for row in rows),
        },
        "inputs": {path.relative_to(ROOT).as_posix(): digest(path) for path in inputs},
        "outputs": {path.name: digest(path) for path in outputs},
        "manifest_hash_policy": "MANIFEST.sha256 records this manifest hash separately; it is not recursively embedded.",
    }
    manifest_path = OUTPUT / "MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    (OUTPUT / "MANIFEST.sha256").write_text(f"{digest(manifest_path)}  MANIFEST.json\n", encoding="ascii", newline="\n")
    print(json.dumps({"output": str(OUTPUT), **manifest["counts"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
