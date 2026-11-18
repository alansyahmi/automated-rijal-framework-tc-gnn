#!/usr/bin/env python3
"""Record user approval of Gate A Census v0.2 100-entry stratified sample audit."""

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
AUDIT_DIR = PIPELINE / "gate_a_census_sample_audit_v0_2_2026-11-17"
OUT_DIR = PIPELINE / "gate_a_census_sample_user_decisions_v0_2_2026-11-17"

STATUS_MAP = {
    "exact_span_match": "verified_exact_span",
    "confirmed_non_grade_or_abstain": "verified_non_grade_abstain",
    "context_split_needed": "flagged_context_split_needed",
    "missed_grade_in_abstain": "flagged_missed_grade_in_abstain",
}


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
        raise SystemExit(f"Refusing to overwrite existing sample user decisions: {OUT_DIR}")

    verify_package(AUDIT_DIR)
    rows = read_csv(AUDIT_DIR / "GATE_A_CENSUS_SAMPLE_100_AUDIT_V0_2.csv")
    assert len(rows) == 100

    timestamp = datetime.now(timezone.utc).isoformat()
    out_rows: list[dict[str, Any]] = []
    for row in rows:
        out = dict(row)
        out["human_verification_status"] = STATUS_MAP[row["audit_boundary_status"]]
        out["human_notes"] = f"User approved Gate A census v0.2 sample audit ({row['audit_boundary_status']}). {row['audit_note']}"
        out["user_decision_recorded_utc"] = timestamp
        for k, v in out.items():
            assert_no_em_en_dash(str(v), f"{row['sample_id']}.{k}")
        out_rows.append(out)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUT_DIR / "GATE_A_CENSUS_SAMPLE_100_USER_DECISIONS_V0_2.csv"
    write_csv(csv_path, out_rows, list(out_rows[0]))

    counts = Counter(r["human_verification_status"] for r in out_rows)
    readme_text = "\n".join([
        "# Gate A Census v0.2 100-Entry Sample User Decisions",
        "",
        f"**Status:** user approved all `100` sample verification checks (`{dict(sorted(counts.items()))}`). Zero canonical ranks assigned and zero rules enabled.",
        "",
    ])
    assert_no_em_en_dash(readme_text, "README.md")
    readme_path = OUT_DIR / "README.md"
    readme_path.write_text(readme_text, encoding="utf-8", newline="\n")

    inputs = [AUDIT_DIR / "GATE_A_CENSUS_SAMPLE_100_AUDIT_V0_2.csv", AUDIT_DIR / "MANIFEST.json", Path(__file__).resolve()]
    outputs = [csv_path, readme_path]
    manifest = {
        "package_id": OUT_DIR.name,
        "generated_at_utc": timestamp,
        "counts": {
            "sample_size": len(out_rows),
            "human_verification_counts": dict(sorted(counts.items())),
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
