#!/usr/bin/env python3
"""Record user approval of the Gate A morphological second-pass audit v0.1."""

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
AUDIT_DIR = PIPELINE / "gate_a_morphological_audit_v0_1_2026-11-16"
OUT_DIR = PIPELINE / "gate_a_morphological_user_decisions_v0_1_2026-11-17"


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
        raise SystemExit(f"Refusing to overwrite existing package: {OUT_DIR}")

    verify_package(AUDIT_DIR)
    surf_rows = read_csv(AUDIT_DIR / "MORPHOLOGICAL_SURFACE_FORMS_AUDIT_V0_1.csv")
    none_rows = read_csv(AUDIT_DIR / "NONE_FOUND_44_MORPH_AUDIT_V0_1.csv")
    assert len(surf_rows) == 177
    assert len(none_rows) == 44

    timestamp = datetime.now(timezone.utc).isoformat()

    surf_decisions: list[dict[str, Any]] = []
    for row in surf_rows:
        out = dict(row)
        out["human_census_disposition"] = row["recommended_gate_a_action"]
        out["human_notes"] = f"User approved Gate A morphological audit ({row['audit_category']}). {row['audit_rationale']}"
        out["user_decision_recorded_utc"] = timestamp
        for k, v in out.items():
            assert_no_em_en_dash(str(v), f"{row['surface_form_no_diacritics']}.{k}")
        surf_decisions.append(out)

    none_decisions: list[dict[str, Any]] = []
    for row in none_rows:
        out = dict(row)
        out["human_decision"] = row["recommended_disposition"]
        out["human_notes"] = f"User approved Gate A morphological audit ({row['audit_category']}). {row['audit_rationale']}"
        out["user_decision_recorded_utc"] = timestamp
        for k, v in out.items():
            assert_no_em_en_dash(str(v), f"{row['entry_id']}.{k}")
        none_decisions.append(out)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    surf_csv = OUT_DIR / "MORPHOLOGICAL_SURFACE_FORMS_USER_DECISIONS_V0_1.csv"
    none_csv = OUT_DIR / "NONE_FOUND_44_MORPH_USER_DECISIONS_V0_1.csv"
    write_csv(surf_csv, surf_decisions, list(surf_decisions[0]))
    write_csv(none_csv, none_decisions, list(none_decisions[0]))

    surf_counts = Counter(r["human_census_disposition"] for r in surf_decisions)
    none_counts = Counter(r["human_decision"] for r in none_decisions)

    readme_text = "\n".join([
        "# Gate A Morphological User Decisions v0.1",
        "",
        "**Status:** user approved all `177` morphological surface-form dispositions and `44` `none_found` morphological hit dispositions. Zero canonical production ranks or active rules assigned.",
        "",
        f"- `MORPHOLOGICAL_SURFACE_FORMS_USER_DECISIONS_V0_1.csv`: `177` rows (`{dict(sorted(surf_counts.items()))}`).",
        f"- `NONE_FOUND_44_MORPH_USER_DECISIONS_V0_1.csv`: `44` rows (`{dict(sorted(none_counts.items()))}`).",
        "",
    ])
    assert_no_em_en_dash(readme_text, "README.md")
    readme_path = OUT_DIR / "README.md"
    readme_path.write_text(readme_text, encoding="utf-8", newline="\n")

    inputs = [
        AUDIT_DIR / "MORPHOLOGICAL_SURFACE_FORMS_AUDIT_V0_1.csv",
        AUDIT_DIR / "NONE_FOUND_44_MORPH_AUDIT_V0_1.csv",
        AUDIT_DIR / "MANIFEST.json",
        Path(__file__).resolve(),
    ]
    outputs = [surf_csv, none_csv, readme_path]
    manifest = {
        "package_id": OUT_DIR.name,
        "generated_at_utc": timestamp,
        "decision_basis": "User explicitly approved Gate A morphological second-pass audit v0.1.",
        "counts": {
            "surface_forms_decided": len(surf_decisions),
            "surface_disposition_counts": dict(sorted(surf_counts.items())),
            "none_found_hits_decided": len(none_decisions),
            "none_found_disposition_counts": dict(sorted(none_counts.items())),
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
