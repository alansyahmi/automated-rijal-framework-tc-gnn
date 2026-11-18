#!/usr/bin/env python3
"""Record user approval of the v1.2 phrase review audit (148 groups + 161 none-found, TODO line 16).

Verifies rank_label_phrase_review_v1_2_audit_2026-11-16/MANIFEST.json and
rank_label_phrase_review_v1_1_2026-11-16/MANIFEST.json, preserves the 18 existing
v1.1 human decisions verbatim, records the 130 newly approved phrase group
dispositions and 161 none-found dispositions into a separate dated package,
and assigns zero canonical production ranks or active rules.
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
AUDIT_DIR = PIPELINE / "rank_label_phrase_review_v1_2_audit_2026-11-16"
V1_1_DIR = PIPELINE / "rank_label_phrase_review_v1_1_2026-11-16"
OUT_DIR = PIPELINE / "rank_label_phrase_review_user_decisions_v1_2_2026-11-16"


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
    verify_package(V1_1_DIR)

    phrase_audit_rows = read_csv(AUDIT_DIR / "PHRASE_REVIEW_148_AUDIT_V1_2.csv")
    none_audit_rows = read_csv(AUDIT_DIR / "NONE_FOUND_161_AUDIT_V1_2.csv")
    assert len(phrase_audit_rows) == 148, f"Expected 148 phrase rows, got {len(phrase_audit_rows)}"
    assert len(none_audit_rows) == 161, f"Expected 161 none-found rows, got {len(none_audit_rows)}"

    timestamp = datetime.now(timezone.utc).isoformat()

    phrase_decisions: list[dict[str, Any]] = []
    v1_1_preserved = 0
    v1_2_recorded = 0
    for row in phrase_audit_rows:
        out = dict(row)
        existing_decision = (row.get("human_decision") or "").strip()
        if existing_decision:
            out["decision_source_version"] = "v1_1_preserved"
            out["user_decision_recorded_utc"] = "2026-11-16_v1_1_existing"
            v1_1_preserved += 1
        else:
            out["human_decision"] = row["recommended_human_decision"]
            out["human_approved_span_exact"] = row["recommended_approved_span_exact"]
            out["human_rank_or_status_decision"] = row["recommended_rank_or_status_decision"]
            out["human_notes"] = f"User approved v1.2 audit recommendation. {row['recommended_audit_rationale']}"
            out["decision_source_version"] = "v1_2_user_approved"
            out["user_decision_recorded_utc"] = timestamp
            v1_2_recorded += 1
        out["user_decision_scope"] = "Phrase-group policy disposition only; no production rank label or active rule enabled."
        for k, v in out.items():
            assert_no_em_en_dash(str(v), f"{out['review_id']}.{k}")
        phrase_decisions.append(out)

    assert v1_1_preserved == 18 and v1_2_recorded == 130

    none_decisions: list[dict[str, Any]] = []
    for row in none_audit_rows:
        out = dict(row)
        out["human_decision"] = row["recommended_human_decision"]
        out["human_notes"] = (
            f"User approved v1.2 audit ({row['recommended_none_found_category']}). "
            f"{row['recommended_rationale']}"
        )
        out["decision_source_version"] = "v1_2_user_approved"
        out["user_decision_recorded_utc"] = timestamp
        out["user_decision_scope"] = "None-found entry disposition only; no production rank label or active rule enabled."
        for k, v in out.items():
            assert_no_em_en_dash(str(v), f"{out['entry_id']}.{k}")
        none_decisions.append(out)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    phrase_csv_path = OUT_DIR / "PHRASE_REVIEW_USER_DECISIONS_148_V1_2.csv"
    none_csv_path = OUT_DIR / "NONE_FOUND_USER_DECISIONS_161_V1_2.csv"
    write_csv(phrase_csv_path, phrase_decisions, list(phrase_decisions[0]))
    write_csv(none_csv_path, none_decisions, list(none_decisions[0]))

    phrase_counts = Counter(r["human_decision"] for r in phrase_decisions)
    none_counts = Counter(r["human_decision"] for r in none_decisions)

    readme_text = "\n".join([
        "# Taqrīb Phrase Review User Decisions v1.2 (148 Phrase Groups + 161 None-Found Entries)",
        "",
        "**Status:** user approved the v1.2 second-pass audit (`18` v1.1 decisions preserved verbatim + `130` newly recorded phrase-group dispositions + `161` none-found entry dispositions). Zero canonical production rank labels or active rules assigned.",
        "",
        "## Summary Counts",
        f"- `PHRASE_REVIEW_USER_DECISIONS_148_V1_2.csv`: `148` total (`{dict(sorted(phrase_counts.items()))}`).",
        f"- `NONE_FOUND_USER_DECISIONS_161_V1_2.csv`: `161` total (`{dict(sorted(none_counts.items()))}`).",
        "- Original `v1_1` worksheets (`PHRASE_REVIEW_WORKSHEET_V1_1.csv`, `NONE_FOUND_AUDIT_161.csv`) and `v1_2_audit` tables remain unmodified.",
        "- `MANIFEST.json` and `MANIFEST.sha256`: input and output SHA-256 checksums.",
        "",
    ])
    assert_no_em_en_dash(readme_text, "README.md")
    readme_path = OUT_DIR / "README.md"
    readme_path.write_text(readme_text, encoding="utf-8", newline="\n")

    inputs = [
        AUDIT_DIR / "PHRASE_REVIEW_148_AUDIT_V1_2.csv",
        AUDIT_DIR / "NONE_FOUND_161_AUDIT_V1_2.csv",
        AUDIT_DIR / "MANIFEST.json",
        V1_1_DIR / "PHRASE_REVIEW_WORKSHEET_V1_1.csv",
        V1_1_DIR / "NONE_FOUND_AUDIT_161.csv",
        V1_1_DIR / "MANIFEST.json",
        Path(__file__).resolve(),
    ]
    outputs = [phrase_csv_path, none_csv_path, readme_path]
    manifest = {
        "package_id": OUT_DIR.name,
        "generated_at_utc": timestamp,
        "decision_basis": "User explicitly approved the v1.2 phrase review audit (130 remaining groups + 161 none-found entries).",
        "counts": {
            "phrase_groups_total": len(phrase_decisions),
            "phrase_groups_v1_1_preserved": v1_1_preserved,
            "phrase_groups_v1_2_recorded": v1_2_recorded,
            "phrase_group_decision_counts": dict(sorted(phrase_counts.items())),
            "none_found_total": len(none_decisions),
            "none_found_decision_counts": dict(sorted(none_counts.items())),
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
