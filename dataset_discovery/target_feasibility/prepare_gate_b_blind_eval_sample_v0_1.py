#!/usr/bin/env python3
"""Prepare a strictly blind 120-entry manual-first Gate B evaluation sample (TODO lines 38-39).

Excludes all 1,405 entries ever touched in boundary pilot v1.3, priority-12,
evaluative statement batches (866), phrase occurrence review (81), none-found (161),
example triplets, and both Gate A 100-entry sample audits.

Outputs:
- BLIND_EVALUATION_SHEET_120_V0_1.csv: purely raw Arabic entries + blank human_*
  columns in shuffled eval order (zero machine spans, hints, or strata exposed).
- SEALED_MACHINE_PROPOSALS_120_V0_1.csv: hidden census v0.2 proposals sealed by
  SHA-256 in MANIFEST.json until human labels are frozen.
- BLIND_EVALUATION_GUIDE_V0_1.md, MANIFEST.json, MANIFEST.sha256.
"""

from __future__ import annotations

import csv
import hashlib
import json
import random
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PIPELINE = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline"
ENTRY_INDEX = PIPELINE / "rank_label_shadow_run_v1_2026-11-15/ENTRY_INDEX.csv"
CENSUS_V02 = PIPELINE / "gate_a_complete_span_census_v0_2_2026-11-17/GATE_A_ENTRY_COMPLETE_SPAN_CENSUS_V0_2.csv"
OUT_DIR = PIPELINE / "gate_b_blind_manual_eval_v0_1_2026-11-17"


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


def collect_dev_exclusions(entries: list[dict[str, str]]) -> set[str]:
    dev_ids: set[str] = set()
    id_files = [
        PIPELINE / "evaluation_statement_decisions_consolidated_v0_1_2026-11-16/CONSOLIDATED_REVIEW_CASE_DECISIONS_V0_1.csv",
        PIPELINE / "rank_label_phrase_occurrence_user_decisions_v1_1_2026-11-16/ENTRY_LEVEL_USER_DECISIONS_81_V1_1.csv",
        PIPELINE / "rank_label_phrase_review_user_decisions_v1_2_2026-11-16/NONE_FOUND_USER_DECISIONS_161_V1_2.csv",
        PIPELINE / "gate_a_census_sample_audit_v0_1_2026-11-17/GATE_A_CENSUS_SAMPLE_100_AUDIT_V0_1.csv",
        PIPELINE / "gate_a_census_sample_audit_v0_2_2026-11-17/GATE_A_CENSUS_SAMPLE_100_AUDIT_V0_2.csv",
    ]
    for fp in id_files:
        for r in read_csv(fp):
            if r.get("entry_id"):
                dev_ids.add(r["entry_id"])

    example_files = [
        (PIPELINE / "rank_label_phrase_review_v1_1_2026-11-16/PHRASE_REVIEW_WORKSHEET_V1_1.csv", ("example_1_entry_id", "example_2_entry_id", "example_3_entry_id")),
        (PIPELINE / "gate_a_morphological_candidate_scan_v0_1_2026-11-16/MORPHOLOGICAL_SURFACE_FORMS_V0_1.csv", ("example_1_entry_id", "example_2_entry_id")),
        (PIPELINE / "gate_a_morphological_candidate_scan_v0_2_2026-11-17/MORPHOLOGICAL_SURFACE_FORMS_V0_2.csv", ("example_1_entry_id", "example_2_entry_id")),
    ]
    for fp, cols in example_files:
        for r in read_csv(fp):
            for c in cols:
                if r.get(c):
                    dev_ids.add(r[c])

    bp_nums = {
        r["entry_number_numeric"]
        for r in read_csv(PIPELINE / "boundary_pilot_v1/frozen_v1_3_2026-11-15/TAQRIB_BOUNDARY_ANNOTATIONS_FROZEN_V1_3.csv")
    }
    p12_nums = {
        r["entry_number_verbatim"]
        for r in read_csv(PIPELINE / "rank_label_agent_review_v1_2026-11-15/first_grade_policy_v0_2/PRIORITY_12_FIRST_GRADE_TARGETS_DRAFT_V0_2.csv")
    }
    for e in entries:
        if e["entry_number_numeric"] in bp_nums or e["entry_number_verbatim"] in p12_nums:
            dev_ids.add(e["entry_id"])
    return dev_ids


def main() -> None:
    if OUT_DIR.exists() and any(OUT_DIR.iterdir()):
        raise SystemExit(f"Refusing to overwrite existing Gate B blind eval package: {OUT_DIR}")

    entries = read_csv(ENTRY_INDEX)
    assert len(entries) == 8827
    census = {r["entry_id"]: r for r in read_csv(CENSUS_V02)}
    dev_ids = collect_dev_exclusions(entries)

    unseen = [e for e in entries if e["entry_id"] not in dev_ids]
    rng = random.Random(20261119)

    chosen_map: dict[str, str] = {}

    def pick_from(stratum_name: str, pool: list[dict[str, str]], quota: int) -> None:
        avail = [e for e in pool if e["entry_id"] not in chosen_map]
        rng.shuffle(avail)
        assert len(avail) >= quota, f"Insufficient pool for {stratum_name}: {len(avail)} < {quota}"
        for e in avail[:quota]:
            chosen_map[e["entry_id"]] = stratum_name

    # Draw rarer strata first so sampling stays disjoint and balanced across all 12 categories
    pick_from(
        "rare_rank_11_12",
        [e for e in unseen if any(k in census[e["entry_id"]]["first_complete_target_span_exact"] for k in ("كذاب", "وضاع", "متهم", "اتهم", "كذبوه", "رمي ب"))],
        5,
    )
    pick_from("tamiz_boundary", [e for e in unseen if "تمييز" in e["entry_text_verbatim"]], 5)
    pick_from(
        "companion_status_cue",
        [e for e in unseen if any(k in census[e["entry_id"]]["first_complete_target_span_exact"] for k in ("صحابي", "بدري", "صحبة", "رؤية", "مخضرم"))],
        10,
    )
    pick_from(
        "anchor_rank_2_5_10",
        [e for e in unseen if census[e["entry_id"]]["matched_source_anchor_ranks"] in {"2", "5", "10"}],
        15,
    )
    pick_from(
        "anchor_rank_7_8_9",
        [e for e in unseen if census[e["entry_id"]]["matched_source_anchor_ranks"] in {"7", "8", "9"}],
        15,
    )
    pick_from(
        "anchor_rank_6_corroboration",
        [e for e in unseen if census[e["entry_id"]]["matched_source_anchor_ranks"] == "6"],
        15,
    )
    pick_from(
        "anchor_rank_3_4",
        [e for e in unseen if census[e["entry_id"]]["matched_source_anchor_ranks"] in {"3", "4"}],
        25,
    )
    pick_from(
        "unanchored_multiword_or_qualified",
        [e for e in unseen if census[e["entry_id"]]["matched_source_anchor_ranks"] == ""],
        30,
    )

    assert len(chosen_map) == 120
    entry_by_id = {e["entry_id"]: e for e in entries}
    selected_ids = list(chosen_map.keys())
    rng.shuffle(selected_ids)

    blind_rows: list[dict[str, Any]] = []
    sealed_rows: list[dict[str, Any]] = []
    for idx, eid in enumerate(selected_ids, 1):
        e = entry_by_id[eid]
        c = census[eid]
        eval_id = f"GB-EVAL-{idx:03d}"
        blind_row = {
            "eval_id": eval_id,
            "entry_id": eid,
            "printed_page_num": e["printed_page_num"],
            "source_chunk_index": e["source_chunk_index"],
            "entry_number_verbatim": e["entry_number_verbatim"],
            "entry_text_verbatim": e["entry_text_verbatim"],
            "human_entry_eligibility": "",
            "human_first_complete_target_span_exact": "",
            "human_context_note_spans_exact": "",
            "human_source_rank_1_to_12_or_abstain": "",
            "human_precondition_status": "",
            "human_notes": "",
        }
        sealed_row = {
            "eval_id": eval_id,
            "entry_id": eid,
            "hidden_stratum": chosen_map[eid],
            "sealed_machine_target_span_exact": c["first_complete_target_span_exact"],
            "sealed_machine_context_span_exact": c["context_note_spans_exact"],
            "sealed_machine_matched_source_ranks": c["matched_source_anchor_ranks"],
            "sealed_machine_gate_a_category": c["gate_a_category"],
            "sealed_note": "DO NOT OPEN until human labels in BLIND_EVALUATION_SHEET_120_V0_1.csv are frozen.",
        }
        for k, v in blind_row.items():
            assert_no_em_en_dash(str(v), f"blind.{eval_id}.{k}")
        for k, v in sealed_row.items():
            assert_no_em_en_dash(str(v), f"sealed.{eval_id}.{k}")
        blind_rows.append(blind_row)
        sealed_rows.append(sealed_row)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    blind_csv = OUT_DIR / "BLIND_EVALUATION_SHEET_120_V0_1.csv"
    sealed_csv = OUT_DIR / "SEALED_MACHINE_PROPOSALS_120_V0_1.csv"
    write_csv(blind_csv, blind_rows, list(blind_rows[0]))
    write_csv(sealed_csv, sealed_rows, list(sealed_rows[0]))

    stratum_counts = Counter(chosen_map.values())
    guide_lines = [
        "# Gate B Blind Manual-First Evaluation Guide v0.1 (TODO Lines 38-42)",
        "",
        "**Protocol Rule:** annotate [BLIND_EVALUATION_SHEET_120_V0_1.csv](BLIND_EVALUATION_SHEET_120_V0_1.csv) strictly BEFORE opening `SEALED_MACHINE_PROPOSALS_120_V0_1.csv`. Freeze the human-only sheet first with its own SHA-256 hash before comparing against machine proposals.",
        "",
        "## Sampling & Exclusion Guarantee",
        f"- Total numbered corpus: `{len(entries)}`",
        f"- Excluded development/prior-review entries: `{len(dev_ids)}` (boundary pilot `25`, priority-12, evaluative statements `866`, phrase occurrence `81`, none-found `161`, worksheet/scan example triplets, and both Gate A `100`-entry sample audits).",
        f"- Eligible completely unseen pool: `{len(unseen)}`",
        f"- Blind sample drawn (`N=120`, `seed=20261119`, shuffled display order): `{dict(sorted(stratum_counts.items()))}`",
        "",
        "## Annotation Instructions (12 Ranks Preserved; Zero Silent Collapsing)",
        "1. `human_entry_eligibility`: `eligible_grade_or_status` | `non_grade_biographical_or_tamiz` | `unresolved_or_abstain`",
        "2. `human_first_complete_target_span_exact`: copy exact verbatim Arabic of the first complete grade/status phrase (Policy v0.2), or leave blank for non-grade.",
        "3. `human_context_note_spans_exact`: copy any attached/later qualifiers kept separate from the target label.",
        "4. `human_source_rank_1_to_12_or_abstain`: assign `1`..`12` ONLY when source-definition preconditions are satisfied; otherwise use `abstain_precondition_unmet` (e.g. Rank 6 `مقبول` without corroboration, Rank 7/9 without transmitter evidence, disputed `رؤية`), `abstain_non_grade`, or `abstain_ambiguous`.",
        "5. Single-researcher scope (`TODO` line 40): report agreement, rank/construction disagreements, false suggestions, and abstentions as a single-researcher feasibility check; do not claim inter-reviewer reliability.",
        "",
    ]
    guide_text = "\n".join(guide_lines)
    assert_no_em_en_dash(guide_text, "BLIND_EVALUATION_GUIDE_V0_1.md")
    guide_path = OUT_DIR / "BLIND_EVALUATION_GUIDE_V0_1.md"
    guide_path.write_text(guide_text, encoding="utf-8", newline="\n")

    timestamp = datetime.now(timezone.utc).isoformat()
    inputs = [ENTRY_INDEX, CENSUS_V02, Path(__file__).resolve()]
    outputs = [blind_csv, sealed_csv, guide_path]
    manifest = {
        "package_id": OUT_DIR.name,
        "generated_at_utc": timestamp,
        "counts": {
            "corpus_total": len(entries),
            "dev_excluded_entries": len(dev_ids),
            "unseen_eligible_pool": len(unseen),
            "blind_sample_size": len(blind_rows),
            "stratum_quotas_hidden_in_sealed": dict(sorted(stratum_counts.items())),
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
