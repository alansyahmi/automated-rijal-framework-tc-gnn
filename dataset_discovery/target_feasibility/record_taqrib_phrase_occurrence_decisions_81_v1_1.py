#!/usr/bin/env python3
"""Record user approval of the 81-entry second-pass phrase occurrence audit (TODO line 15).

Verifies rank_label_phrase_occurrence_audit_v1_1_2026-11-16/MANIFEST.json and
rank_label_phrase_occurrence_review_v1_2026-11-16/MANIFEST.json, leaves the
blank template and AI suggestions untouched, and writes a separate dated
human-decision package with canonical_rank strictly omitted/unassigned.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PIPELINE = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline"
AUDIT_DIR = PIPELINE / "rank_label_phrase_occurrence_audit_v1_1_2026-11-16"
REVIEW_DIR = PIPELINE / "rank_label_phrase_occurrence_review_v1_2026-11-16"
OUT_DIR = PIPELINE / "rank_label_phrase_occurrence_user_decisions_v1_1_2026-11-16"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\r\n")
        writer.writeheader()
        writer.writerows(rows)


def assert_no_em_en_dash(text: str, label: str) -> None:
    if "\u2014" in text or "\u2013" in text:
        raise SystemExit(f"Forbidden em-dash or en-dash in {label}")


def verify_package(directory: Path) -> None:
    manifest_path = directory / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    sidecar = (directory / "MANIFEST.sha256").read_text(encoding="ascii").split()[0]
    if digest(manifest_path) != sidecar:
        raise SystemExit(f"MANIFEST.sha256 mismatch in {directory}")
    for name, expected in manifest["outputs"].items():
        if digest(directory / name) != expected:
            raise SystemExit(f"Hash mismatch for {directory.name}/{name}")


def main() -> None:
    if OUT_DIR.exists() and any(OUT_DIR.iterdir()):
        raise SystemExit(f"Refusing to overwrite existing decision package: {OUT_DIR}")

    verify_package(AUDIT_DIR)
    verify_package(REVIEW_DIR)

    audit_rows = read_csv(AUDIT_DIR / "ENTRY_LEVEL_AUDIT_81_V1_1.csv")
    assert len(audit_rows) == 81, f"Expected 81 audit rows, got {len(audit_rows)}"

    timestamp = datetime.now(timezone.utc).isoformat()
    decision_rows: list[dict[str, Any]] = []
    for row in audit_rows:
        out = dict(row)
        out["human_phrase_role_in_context"] = row["recommended_phrase_role_in_context"]
        out["human_is_first_complete_target_phrase"] = row["recommended_is_first_complete_target_phrase"]
        out["human_qualification_or_conflict"] = row["recommended_qualification_or_conflict"]
        out["human_critic_attribution"] = row["recommended_critic_attribution"]
        out["human_entry_disposition"] = row["recommended_entry_disposition"]
        out["human_reviewer_notes"] = f"User approved second-pass audit ({row['second_pass_audit_status']}). {row['second_pass_audit_note']}"
        out["user_decision_recorded_utc"] = timestamp
        out["user_decision_scope"] = "Entry-level review disposition only; no production rank label or active rule enabled."
        for k, v in out.items():
            assert_no_em_en_dash(str(v), f"{out['case_id']}.{k}")
        decision_rows.append(out)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUT_DIR / "ENTRY_LEVEL_USER_DECISIONS_81_V1_1.csv"
    write_csv(csv_path, decision_rows, list(decision_rows[0]))

    disp_counts = Counter(r["human_entry_disposition"] for r in decision_rows)
    readme_text = "\n".join([
        "# Taqrīb Phrase Occurrence User Decisions v1.1 (81 Entries)",
        "",
        "**Status:** user approved all 81 second-pass audit dispositions (`51 retain_as_candidate`, `28 conditional`, `2 needs_repair`). Zero canonical production rank labels or active rules assigned.",
        "",
        "- [ENTRY_LEVEL_USER_DECISIONS_81_V1_1.csv](ENTRY_LEVEL_USER_DECISIONS_81_V1_1.csv): all 81 distinct local entries with recorded `human_*` review dispositions and notes.",
        "- Original blank template (`rank_label_phrase_occurrence_review_v1_2026-11-16/ENTRY_LEVEL_REVIEW_V1.csv`) and `AI_SUGGESTIONS_V1.csv` remain unmodified.",
        "- `MANIFEST.json` and `MANIFEST.sha256`: input and output SHA-256 checksums.",
        "",
    ])
    assert_no_em_en_dash(readme_text, "README.md")
    readme_path = OUT_DIR / "README.md"
    readme_path.write_text(readme_text, encoding="utf-8", newline="\n")

    inputs = [
        AUDIT_DIR / "ENTRY_LEVEL_AUDIT_81_V1_1.csv",
        AUDIT_DIR / "MANIFEST.json",
        REVIEW_DIR / "ENTRY_LEVEL_REVIEW_V1.csv",
        REVIEW_DIR / "MANIFEST.json",
        Path(__file__).resolve(),
    ]
    outputs = [csv_path, readme_path]
    manifest = {
        "package_id": OUT_DIR.name,
        "generated_at_utc": timestamp,
        "decision_basis": "User explicitly approved the 81-entry second-pass audit recommendations.",
        "counts": {
            "entries_decided": len(decision_rows),
            "human_entry_disposition_counts": dict(disp_counts),
            "canonical_ranks_assigned": 0,
            "rules_enabled": 0,
        },
        "inputs": {path.relative_to(ROOT).as_posix(): digest(path) for path in inputs},
        "outputs": {path.name: digest(path) for path in outputs},
        "manifest_hash_policy": "MANIFEST.sha256 records this manifest hash separately; it is not recursively embedded.",
    }
    manifest_str = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    assert_no_em_en_dash(manifest_str, "MANIFEST.json")
    manifest_path = OUT_DIR / "MANIFEST.json"
    manifest_path.write_text(manifest_str, encoding="utf-8", newline="\n")
    (OUT_DIR / "MANIFEST.sha256").write_text(f"{digest(manifest_path)}  MANIFEST.json\n", encoding="ascii", newline="\n")

    print(json.dumps({"output": str(OUT_DIR), **manifest["counts"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
