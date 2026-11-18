#!/usr/bin/env python3
"""Record the user's explicit acceptance of all 889 rows in AI advisory batch 02.

The AI advisory package and the blank Batch 02 review frame remain untouched.
This writes a separate, versioned decision package whose acceptance scope is
each row's selected review case only, with canonical_rank and numeric_score
kept strictly blank.
"""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PIPELINE = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline"
AI_DIR = PIPELINE / "evaluation_statement_occurrence_advisory_batch_02_v0_1_2026-11-16"
AI_CSV = AI_DIR / "AI_ADVISORY_REVIEW_BATCH_02_V0_1.csv"
AI_MANIFEST = AI_DIR / "MANIFEST.json"
OUTPUT = PIPELINE / "evaluation_statement_occurrence_user_decisions_batch_02_v0_1_2026-11-16"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_no_em_en_dash(text: str, label: str) -> None:
    if "\u2014" in text or "\u2013" in text:
        raise SystemExit(f"Forbidden em-dash or en-dash in {label}")


def main() -> None:
    if OUTPUT.exists() and any(OUTPUT.iterdir()):
        raise SystemExit(f"Refusing to overwrite an existing decision package: {OUTPUT}")

    source_manifest = json.loads(AI_MANIFEST.read_text(encoding="utf-8"))
    sidecar = (AI_DIR / "MANIFEST.sha256").read_text(encoding="ascii").split()[0]
    if digest(AI_MANIFEST) != sidecar:
        raise SystemExit("AI advisory MANIFEST.sha256 mismatch")
    if digest(AI_CSV) != source_manifest["outputs"][AI_CSV.name]:
        raise SystemExit("AI advisory CSV does not match its recorded output hash")

    with AI_CSV.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
        fields = list(rows[0]) if rows else []

    if len(rows) != 889 or len({row["review_case_id"] for row in rows}) != 889:
        raise SystemExit("Expected 889 unique Batch 02 review cases")

    timestamp = datetime.now(timezone.utc).isoformat()
    for row in rows:
        if row["canonical_rank"] or row["numeric_score"]:
            raise SystemExit(f"Unexpected rank or score in {row['review_case_id']}")
        row["human_decision"] = "accept"
        row["human_match_use"] = row["ai_match_use"]
        row["human_statement_role"] = row["ai_statement_role"]
        row["human_statement_start_char_zero_based"] = row["ai_statement_start_char_zero_based"]
        row["human_statement_end_char_exclusive"] = row["ai_statement_end_char_exclusive"]
        row["human_referent"] = row["ai_referent"]
        row["human_attribution"] = row["ai_attribution"]
        row["human_qualification"] = row["ai_qualification"]
        row["human_confidence"] = row["ai_interpretation_confidence"]
        row["human_notes"] = "User accepted all AI-proposed fields for this selected review case only."
        row["user_decision_recorded_utc"] = timestamp
        row["user_decision_scope"] = "Selected review case in this row only; no phrase-wide generalization."
        for k, v in row.items():
            assert_no_em_en_dash(str(v), f"{row['review_case_id']}.{k}")

    fields += ["user_decision_recorded_utc", "user_decision_scope"]

    OUTPUT.mkdir(parents=True, exist_ok=True)
    decisions_path = OUTPUT / "HUMAN_DECISIONS_BATCH_02_V0_1.csv"
    with decisions_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\r\n")
        writer.writeheader()
        writer.writerows(rows)

    readme = "\n".join([
        "# User decisions for AI advisory batch 02",
        "",
        "**Status:** all 889 AI proposals were accepted by the user in this conversation. This is a single-reviewer decision record adopting the AI-proposed statement-layer fields, not independent expert validation.",
        "",
        "## Decision and scope",
        "",
        'The user explicitly instructed: "looks good, i trust ur judgements so represent mine the human same too". In response, `human_decision=accept` and the corresponding `human_*` fields are recorded from the AI proposals for all 889 Batch 02 review cases (`842` distinct source entries). Acceptance applies only to each row\'s selected local review case. It does **not** generalize to unselected occurrences of the same phrases, establish historical truth or source independence, assign a canonical rank, or authorize a numeric score.',
        "",
        "The original AI advisory package remains untouched at `../evaluation_statement_occurrence_advisory_batch_02_v0_1_2026-11-16/`, and the blank Batch 02 review frame remains untouched at `../evaluation_statement_occurrence_review_batch_02_v0_1_2026-11-16/`.",
        "",
        "## Files",
        "",
        "- `HUMAN_DECISIONS_BATCH_02_V0_1.csv`: all 889 accepted review cases with AI proposal fields, recorded `human_*` fields, complete source entry, locator, and blank `canonical_rank` / `numeric_score` columns.",
        "- `MANIFEST.json` and `MANIFEST.sha256`: source and output SHA-256 digests.",
        "",
    ])
    assert_no_em_en_dash(readme, "README.md")
    readme_path = OUTPUT / "README.md"
    readme_path.write_text(readme, encoding="utf-8", newline="\n")

    inputs = [AI_CSV, AI_MANIFEST, Path(__file__).resolve()]
    outputs = [decisions_path, readme_path]
    manifest = {
        "package_id": OUTPUT.name,
        "generated_at_utc": timestamp,
        "decision_basis": "User explicitly adopted all AI advisory proposals in Batch 02.",
        "decision_scope": "Acceptance applies to all proposed statement-layer fields for each selected review case only; it does not generalize to unselected phrase hits.",
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
    manifest_str = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    assert_no_em_en_dash(manifest_str, "MANIFEST.json")
    manifest_path = OUTPUT / "MANIFEST.json"
    manifest_path.write_text(manifest_str, encoding="utf-8", newline="\n")
    (OUTPUT / "MANIFEST.sha256").write_text(f"{digest(manifest_path)}  MANIFEST.json\n", encoding="ascii", newline="\n")

    print(json.dumps({"output": str(OUTPUT), **manifest["counts"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
