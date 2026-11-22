#!/usr/bin/env python3
"""Unified Track R + Track L Experiment Suite (P5, taqrib-oriented-v2 / v3).

Runs on CPU for all deterministic Track R experiments (Exp A: B, Exp B-det: B+E1,
Exp C: B+E1+E2 vs al-Kashif only, E1 sensitivity across 4 presets, graph homophily,
coverage/missingness accounting, and slice breakdowns). If GPU Stage 2 ESA and/or
Stage 3 TC-GNN v3 output directories exist (auto-detected or passed via CLI),
gracefully merges Exp B-learned and Exp D (TC-GNN G4a + model_estimate rows)
without overwriting any observed scholarly verdicts.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import tempfile
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import spearmanr
from sklearn.metrics import accuracy_score, cohen_kappa_score, f1_score

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from common.hashing import sha256_text_normalized, to_posix_relative  # noqa: E402
from common.rank_scale import score_to_rank_cont as _scale_score_to_rank  # noqa: E402
from dataset_discovery.target_feasibility.build_layered_scores_v3 import (  # noqa: E402
    DEFAULT_BILGIN_CSV,
    DEFAULT_MASTER_CSV,
    DEFAULT_RULES_PATH,
    run_build,
)
from experiments.v3_common import (  # noqa: E402
    EXCLUDED_E2_STATUSES,
    compute_graph_homophily,
    compute_metrics,
    rank_to_tier3_id,
)

MASTER_NODES = (
    ROOT
    / "data"
    / "2_interim"
    / "rijal_fyp_modelling_pipeline"
    / "taqrib_v2_master_dataset_2026-11-20"
    / "TAQRIB_V2_MASTER_NODES_8827.csv"
)
GRAPH_EDGES = (
    ROOT
    / "data"
    / "2_interim"
    / "rijal_fyp_modelling_pipeline"
    / "taqrib_v2_master_dataset_2026-11-20"
    / "TAQRIB_V2_GRAPH_EDGES.csv"
)
LAYERED_WIDE = (
    ROOT
    / "data"
    / "2_interim"
    / "rijal_fyp_modelling_pipeline"
    / "layered_scores_v3_2026-11-21"
    / "LAYERED_SCORES_WIDE_V3.csv"
)
KASHIF_AUDIT = (
    ROOT
    / "data"
    / "2_interim"
    / "rijal_fyp_modelling_pipeline"
    / "kashif_validation_v1_2026-11-21"
    / "KASHIF_OVERLAP_AUDIT_V1.csv"
)
DEFAULT_OUT_DIR = ROOT / "results" / "layered_experiments_v3_2026-11-21"


def score_to_rank_cont(score: float, scale: str = "linear_v1") -> float:
    """Inverse of the 0-100 rank scale the layered CSV was built with.

    linear_v1 is the exact inverse of 100 * (12 - rank) / 11. Rows carry their
    scale in the ``rank_scale`` column; rows without it are linear_v1.
    """
    return _scale_score_to_rank(score, scale)


def _row_scale(row: dict[str, str]) -> str:
    return (row.get("rank_scale") or "linear_v1").strip() or "linear_v1"


def rank_cont_to_tier3(rank_cont: float) -> int:
    return rank_to_tier3_id(int(np.clip(np.rint(rank_cont), 1, 12)))


def rank_cont_to_tier5(rank_cont: float) -> int:
    r = int(np.clip(np.rint(rank_cont), 1, 12))
    if r <= 2:
        return 5
    if r == 3:
        return 4
    if r <= 6:
        return 3
    if r <= 9:
        return 2
    return 1


def _find_latest_dir(prefix: str) -> Path | None:
    results_dir = ROOT / "results"
    if not results_dir.exists():
        return None
    matches = sorted([p for p in results_dir.iterdir() if p.is_dir() and p.name.startswith(prefix)])
    return matches[-1] if matches else None


def load_core_tables(
    layered_csv: Path = LAYERED_WIDE,
    master_csv: Path = MASTER_NODES,
    kashif_csv: Path = KASHIF_AUDIT,
) -> tuple[list[dict[str, str]], dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    with master_csv.open("r", encoding="utf-8-sig", newline="") as f:
        master_rows = list(csv.DictReader(f))
    with layered_csv.open("r", encoding="utf-8-sig", newline="") as f:
        layered_by_id = {r["entry_id"]: r for r in csv.DictReader(f)}
    with kashif_csv.open("r", encoding="utf-8-sig", newline="") as f:
        kashif_by_id = {r["entry_id"]: r for r in csv.DictReader(f)}
    return master_rows, layered_by_id, kashif_by_id


def compute_chrono_sanad_degrees(
    master_rows: list[dict[str, str]],
    edges_csv: Path = GRAPH_EDGES,
) -> dict[str, Any]:
    id_to_idx = {r["entry_id"]: i for i, r in enumerate(master_rows)}
    n = len(master_rows)
    tabaqa = np.array([int(r["tabaqa_1_to_12"]) if r["tabaqa_1_to_12"].strip() else -1 for r in master_rows], dtype=int)

    unpruned_src: list[int] = []
    unpruned_dst: list[int] = []
    chrono_src: list[int] = []
    chrono_dst: list[int] = []
    out_deg = np.zeros(n, dtype=np.int32)
    in_deg = np.zeros(n, dtype=np.int32)

    total_sanad = 0
    pruned_edges = 0
    with edges_csv.open("r", encoding="utf-8-sig", newline="") as f:
        for e in csv.DictReader(f):
            if e["sanad_only_edge"] != "1":
                continue
            u = id_to_idx.get(e["teacher_entry_id"])
            v = id_to_idx.get(e["student_entry_id"])
            if u is None or v is None:
                continue
            total_sanad += 1
            unpruned_src.append(u)
            unpruned_dst.append(v)
            tu, tv = int(tabaqa[u]), int(tabaqa[v])
            if tu > 0 and tv > 0 and (tv - tu) <= -2:
                pruned_edges += 1
                continue
            chrono_src.append(u)
            chrono_dst.append(v)
            out_deg[u] += 1
            in_deg[v] += 1

    return {
        "n_sanad_raw": total_sanad,
        "n_sanad_kept": len(chrono_src),
        "n_sanad_pruned": pruned_edges,
        "unpruned_src": unpruned_src,
        "unpruned_dst": unpruned_dst,
        "chrono_src": chrono_src,
        "chrono_dst": chrono_dst,
        "out_deg": out_deg,
        "in_deg": in_deg,
        "is_isolated": (out_deg + in_deg) == 0,
    }


def evaluate_track_r_on_tahrir_test(
    master_rows: list[dict[str, str]],
    layered_by_id: dict[str, dict[str, str]],
    layer_col: str,
    indices: list[int],
) -> dict[str, float]:
    """Descriptive alignment check for B or B+E1 against observed E2 (NEVER run for E2)."""
    y_rank: list[float] = []
    y_shift: list[int] = []
    pred_rank: list[float] = []
    pred_shift: list[int] = []
    is_maqbul: list[bool] = []
    for gi in indices:
        eid = master_rows[gi]["entry_id"]
        lr = layered_by_id[eid]
        sc_s = lr[layer_col].strip()
        rk_b_s = lr["rank_B"].strip()
        rk_e2_s = lr["rank_E2"].strip()
        if not sc_s or not rk_b_s or not rk_e2_s:
            continue
        rb = int(rk_b_s)
        re2 = int(rk_e2_s)
        y_rank.append(float(re2))
        y_shift.append(0 if re2 < rb else (2 if re2 > rb else 1))
        pred_rank.append(score_to_rank_cont(float(sc_s), _row_scale(lr)))
        pred_shift.append(1)  # Identity / unchanged baseline for shift
        is_maqbul.append(lr["taqrib_is_conditional_maqbul"] == "True")
    return compute_metrics(
        np.array(y_rank),
        np.array(y_shift, dtype=int),
        np.array(pred_rank),
        np.array(pred_shift, dtype=int),
        np.array(is_maqbul, dtype=bool),
    )


def evaluate_against_kashif(
    pred_ranks_by_id: dict[str, float],
    kashif_by_id: dict[str, dict[str, str]],
    *,
    subset_name: str,
    filter_fn: Any = None,
) -> dict[str, Any]:
    yt3: list[int] = []
    pt3: list[int] = []
    yt5: list[int] = []
    pt5: list[int] = []
    prank: list[float] = []
    used_ids: list[str] = []

    for eid, kr in kashif_by_id.items():
        if eid not in pred_ranks_by_id:
            continue
        kt3_s = kr["kashif_tier_3"].strip()
        kt5_s = kr["kashif_tier_5"].strip()
        if not kt3_s or not kt5_s:
            continue
        if filter_fn is not None and not filter_fn(eid, kr):
            continue
        rc = float(pred_ranks_by_id[eid])
        used_ids.append(eid)
        yt3.append(int(kt3_s))
        pt3.append(rank_cont_to_tier3(rc))
        yt5.append(int(kt5_s))
        pt5.append(rank_cont_to_tier5(rc))
        prank.append(rc)

    n = len(yt3)
    if n == 0:
        return {
            "subset": subset_name,
            "n": 0,
            "tier3_acc": float("nan"),
            "tier3_macro_f1": float("nan"),
            "tier3_weighted_f1": float("nan"),
            "tier3_qwk": float("nan"),
            "tier5_qwk": float("nan"),
            "tier5_spearman": float("nan"),
            "_arrays": None,
        }

    yt3_a = np.array(yt3, dtype=int)
    pt3_a = np.array(pt3, dtype=int)
    yt5_a = np.array(yt5, dtype=int)
    pt5_a = np.array(pt5, dtype=int)
    prank_a = np.array(prank, dtype=float)
    sp = float(spearmanr(yt5_a, -prank_a).statistic)
    if math.isnan(sp):
        sp = 0.0

    return {
        "subset": subset_name,
        "n": n,
        "tier3_acc": round(float(accuracy_score(yt3_a, pt3_a)), 4),
        "tier3_macro_f1": round(float(f1_score(yt3_a, pt3_a, labels=[0, 1, 2], average="macro", zero_division=0)), 4),
        "tier3_weighted_f1": round(float(f1_score(yt3_a, pt3_a, labels=[0, 1, 2], average="weighted", zero_division=0)), 4),
        "tier3_qwk": round(float(cohen_kappa_score(yt3_a, pt3_a, weights="quadratic")), 4),
        "tier5_qwk": round(float(cohen_kappa_score(yt5_a, pt5_a, weights="quadratic")), 4),
        "tier5_spearman": round(sp, 4),
        "_arrays": (used_ids, yt3_a, pt3_a, yt5_a, pt5_a, prank_a),
    }


def _majority_floor(ev: dict[str, Any]) -> dict[str, Any]:
    """Constant-prediction floor on exactly the rows of `ev`: always predict the most common al-Kashif tier."""
    if not ev.get("_arrays"):
        return {"majority_tier3": "", "majority_tier3_acc": float("nan"), "majority_tier3_macro_f1": float("nan")}
    yt3 = ev["_arrays"][1]
    vals, cnts = np.unique(yt3, return_counts=True)
    maj = int(vals[np.argmax(cnts)])
    pred = np.full_like(yt3, maj)
    return {
        "majority_tier3": maj,
        "majority_tier3_acc": round(float(np.mean(yt3 == maj)), 4),
        "majority_tier3_macro_f1": round(float(f1_score(yt3, pred, labels=[0, 1, 2], average="macro", zero_division=0)), 4),
    }


def paired_bootstrap_kashif(
    ref_ranks: dict[str, float],
    cand_ranks: dict[str, float],
    kashif_by_id: dict[str, dict[str, str]],
    filter_fn: Any,
    n_boot: int = 2000,
    seed: int = 42,
) -> list[dict[str, Any]]:
    common_ids = sorted(
        eid
        for eid, kr in kashif_by_id.items()
        if eid in ref_ranks
        and eid in cand_ranks
        and kr["kashif_tier_3"].strip()
        and kr["kashif_tier_5"].strip()
        and (filter_fn is None or filter_fn(eid, kr))
    )
    if not common_ids:
        return []
    yt3 = np.array([int(kashif_by_id[e]["kashif_tier_3"]) for e in common_ids], dtype=int)
    yt5 = np.array([int(kashif_by_id[e]["kashif_tier_5"]) for e in common_ids], dtype=int)
    p3_ref = np.array([rank_cont_to_tier3(ref_ranks[e]) for e in common_ids], dtype=int)
    p3_cand = np.array([rank_cont_to_tier3(cand_ranks[e]) for e in common_ids], dtype=int)
    p5_ref = np.array([rank_cont_to_tier5(ref_ranks[e]) for e in common_ids], dtype=int)
    p5_cand = np.array([rank_cont_to_tier5(cand_ranks[e]) for e in common_ids], dtype=int)
    rc_ref = np.array([ref_ranks[e] for e in common_ids], dtype=float)
    rc_cand = np.array([cand_ranks[e] for e in common_ids], dtype=float)

    def _stats(idx: np.ndarray) -> tuple[float, float, float, float, float]:
        t3_acc_d = float(accuracy_score(yt3[idx], p3_cand[idx]) - accuracy_score(yt3[idx], p3_ref[idx]))
        t3_mf1_d = float(
            f1_score(yt3[idx], p3_cand[idx], labels=[0, 1, 2], average="macro", zero_division=0)
            - f1_score(yt3[idx], p3_ref[idx], labels=[0, 1, 2], average="macro", zero_division=0)
        )
        t3_qwk_d = float(cohen_kappa_score(yt3[idx], p3_cand[idx], weights="quadratic") - cohen_kappa_score(yt3[idx], p3_ref[idx], weights="quadratic"))
        t5_qwk_d = float(cohen_kappa_score(yt5[idx], p5_cand[idx], weights="quadratic") - cohen_kappa_score(yt5[idx], p5_ref[idx], weights="quadratic"))
        sp_c = float(spearmanr(yt5[idx], -rc_cand[idx]).statistic)
        sp_r = float(spearmanr(yt5[idx], -rc_ref[idx]).statistic)
        sp_d = (0.0 if math.isnan(sp_c) else sp_c) - (0.0 if math.isnan(sp_r) else sp_r)
        return t3_acc_d, t3_mf1_d, t3_qwk_d, t5_qwk_d, sp_d

    full_idx = np.arange(len(common_ids))
    obs = _stats(full_idx)
    rng = np.random.default_rng(seed)
    samples = np.zeros((n_boot, 5), dtype=float)
    n = len(common_ids)
    for b in range(n_boot):
        idx = rng.integers(0, n, size=n)
        samples[b] = _stats(idx)

    metric_names = ["tier3_acc", "tier3_macro_f1", "tier3_qwk", "tier5_qwk", "tier5_spearman"]
    out: list[dict[str, Any]] = []
    for j, mname in enumerate(metric_names):
        arr = samples[:, j]
        p_pos = float(np.mean(arr >= 0.0))
        p_neg = float(np.mean(arr <= 0.0))
        p_2sided = min(1.0, 2.0 * min(p_pos, p_neg))
        out.append(
            {
                "n_common": n,
                "metric": mname,
                "delta": round(float(obs[j]), 4),
                "ci95_low": round(float(np.percentile(arr, 2.5)), 4),
                "ci95_high": round(float(np.percentile(arr, 97.5)), 4),
                "p_value_2sided": round(p_2sided, 4),
            }
        )
    return out


def compute_disagreement_audit(layered_by_id: dict[str, dict[str, str]]) -> dict[str, Any]:
    status_counts = Counter(r["status_E2"] for r in layered_by_id.values())
    b_status_counts = Counter(r["status_B"] for r in layered_by_id.values())
    e1_status_counts = Counter(r["status_E1"] for r in layered_by_id.values())
    upgraded = unchanged = downgraded = 0
    bin_up = bin_down = 0
    tier3_cross = Counter()
    e1_toward_e2 = e1_away_e2 = e1_neutral = 0

    for r in layered_by_id.values():
        st = r["status_E2"]
        if st in EXCLUDED_E2_STATUSES:
            continue
        rb_s = r["rank_B"].strip()
        re2_s = r["rank_E2"].strip()
        if not rb_s or not re2_s:
            continue
        rb, re2 = int(rb_s), int(re2_s)
        if re2 < rb:
            upgraded += 1
        elif re2 > rb:
            downgraded += 1
        else:
            unchanged += 1
        if rb >= 7 and re2 <= 6:
            bin_up += 1
        elif rb <= 6 and re2 >= 7:
            bin_down += 1
        t3b = rank_to_tier3_id(rb)
        t3e2 = rank_to_tier3_id(re2)
        if t3b != t3e2:
            tier3_cross[f"T{t3b}->T{t3e2}"] += 1

        if r["status_E1"] == "observed":
            d_e1 = float(r["delta_E1"])
            sc_b = float(r["score_B"])
            sc_e2 = float(r["score_E2"])
            if abs((sc_b + d_e1) - sc_e2) < abs(sc_b - sc_e2):
                e1_toward_e2 += 1
            elif abs((sc_b + d_e1) - sc_e2) > abs(sc_b - sc_e2):
                e1_away_e2 += 1
            else:
                e1_neutral += 1

    return {
        "status_B": dict(b_status_counts),
        "status_E1": dict(e1_status_counts),
        "status_E2": dict(status_counts),
        "rank_shifts_paired_obs": {"upgraded": upgraded, "unchanged": unchanged, "downgraded": downgraded},
        "binary_crossings": {"jarh_to_tadil": bin_up, "tadil_to_jarh": bin_down},
        "tier3_crossings": dict(tier3_cross),
        "e1_alignment_with_e2": {"toward": e1_toward_e2, "away": e1_away_e2, "unchanged_dist": e1_neutral},
    }


def run_e1_sensitivity(
    master_rows: list[dict[str, str]],
    kashif_by_id: dict[str, dict[str, str]],
    default_layered_by_id: dict[str, dict[str, str]],
    test_indices: list[int],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    presets = ("default", "halved", "doubled", "off")
    for preset in presets:
        if preset == "default":
            lmap = default_layered_by_id
        else:
            with tempfile.TemporaryDirectory() as tmpd:
                tmp_path = Path(tmpd)
                run_build(
                    rules_path=DEFAULT_RULES_PATH,
                    bilgin_csv=DEFAULT_BILGIN_CSV,
                    master_csv=DEFAULT_MASTER_CSV,
                    out_dir=tmp_path,
                    e1_preset=preset,
                    rank_scale=_row_scale(next(iter(default_layered_by_id.values()))),
                )
                with (tmp_path / "LAYERED_SCORES_WIDE_V3.csv").open("r", encoding="utf-8-sig", newline="") as f:
                    lmap = {r["entry_id"]: r for r in csv.DictReader(f)}

        tahrir_test_m = evaluate_track_r_on_tahrir_test(master_rows, lmap, "score_E1", test_indices)
        pred_e1 = {
            eid: score_to_rank_cont(float(r["score_E1"]), _row_scale(r))
            for eid, r in lmap.items()
            if r["score_E1"].strip() and r["status_E2"] not in EXCLUDED_E2_STATUSES
        }
        kashif_all = evaluate_against_kashif(pred_e1, kashif_by_id, subset_name="full_linked")
        kashif_nv = evaluate_against_kashif(
            pred_e1,
            kashif_by_id,
            subset_name="non_verbatim",
            filter_fn=lambda _eid, kr: kr["verbatim_overlap"] == "False",
        )
        n_changed = sum(1 for r in lmap.values() if r["status_E1"] == "observed")
        rows.append(
            {
                "e1_preset": preset,
                "n_e1_observed": n_changed,
                "test_vs_e2_rank_mae": tahrir_test_m["rank_mae"],
                "test_vs_e2_rank_spearman": tahrir_test_m["rank_spearman"],
                "test_vs_e2_tier3_macro_f1": tahrir_test_m["tier3_macro_f1"],
                "test_vs_e2_r6_mae": tahrir_test_m["r6_rank_mae"],
                "kashif_full_n": kashif_all["n"],
                "kashif_full_tier3_acc": kashif_all["tier3_acc"],
                "kashif_full_tier3_mf1": kashif_all["tier3_macro_f1"],
                "kashif_full_tier5_spearman": kashif_all["tier5_spearman"],
                "kashif_nv_n": kashif_nv["n"],
                "kashif_nv_tier3_acc": kashif_nv["tier3_acc"],
                "kashif_nv_tier3_mf1": kashif_nv["tier3_macro_f1"],
                "kashif_nv_tier5_spearman": kashif_nv["tier5_spearman"],
            }
        )
    return rows


def run_suite(
    *,
    out_dir: Path = DEFAULT_OUT_DIR,
    stage2_dir: Path | None = None,
    stage3_dir: Path | None = None,
    layered_csv: Path = LAYERED_WIDE,
    master_csv: Path = MASTER_NODES,
    graph_csv: Path = GRAPH_EDGES,
    kashif_csv: Path = KASHIF_AUDIT,
    bootstrap_iters: int = 2000,
) -> dict[str, Any]:
    t0 = time.time()
    out_dir.mkdir(parents=True, exist_ok=True)
    master_rows, layered_by_id, kashif_by_id = load_core_tables(layered_csv, master_csv, kashif_csv)
    deg_info = compute_chrono_sanad_degrees(master_rows, graph_csv)

    if stage2_dir is None:
        stage2_dir = _find_latest_dir("stage2_esa_benchmarks_v3_")
    if stage3_dir is None:
        stage3_dir = _find_latest_dir("stage3_tc_gnn_benchmarks_v3_")

    # Clean test indices (excluding status_E2 in {missing, suspect_alignment})
    clean_test_idx = [
        i
        for i, r in enumerate(master_rows)
        if r["split"] == "test"
        and layered_by_id[r["entry_id"]]["status_E2"] not in EXCLUDED_E2_STATUSES
        and layered_by_id[r["entry_id"]]["rank_E2"].strip()
    ]

    # Pred maps (continuous 1..12 ranks) for Kashif validation, strictly excluding missing/suspect_alignment E2 flags
    ranks_b_clean = {
        eid: score_to_rank_cont(float(r["score_B"]), _row_scale(r))
        for eid, r in layered_by_id.items()
        if r["score_B"].strip() and r["status_E2"] not in EXCLUDED_E2_STATUSES
    }
    ranks_e1_clean = {
        eid: score_to_rank_cont(float(r["score_E1"]), _row_scale(r))
        for eid, r in layered_by_id.items()
        if r["score_E1"].strip() and r["status_E2"] not in EXCLUDED_E2_STATUSES
    }
    ranks_e2_clean = {
        eid: score_to_rank_cont(float(r["score_E2"]), _row_scale(r))
        for eid, r in layered_by_id.items()
        if r["score_E2"].strip() and r["status_E2"] not in EXCLUDED_E2_STATUSES
    }

    # Paired common IDs where BOTH B and E2 exist (excludes E2 first-grade so deltas aren't skewed by coverage)
    common_b_e2_ids = set(ranks_b_clean.keys()) & set(ranks_e2_clean.keys())

    # Exp A..D summary table
    exp_rows: list[dict[str, Any]] = []

    m_a_test = evaluate_track_r_on_tahrir_test(master_rows, layered_by_id, "score_B", clean_test_idx)
    exp_rows.append(
        {
            "experiment": "Exp_A_Baseline_B",
            "track": "Track_R_Deterministic",
            "model_or_layer": "score_B (Ibn Hajar Taqrib)",
            "eval_target": "tahrir_clean_test_descriptive",
            "status": "COMPLETED",
            "n_eval": len(clean_test_idx),
            "rank_mae": m_a_test["rank_mae"],
            "rank_qwk": m_a_test["rank_qwk"],
            "rank_spearman": m_a_test["rank_spearman"],
            "bin_acc": m_a_test["bin_acc"],
            "tier3_acc": m_a_test["tier3_acc"],
            "tier3_macro_f1": m_a_test["tier3_macro_f1"],
            "shift_macro_f1": m_a_test["shift_macro_f1"],
            "r6_rank_mae": m_a_test["r6_rank_mae"],
        }
    )

    m_b_test = evaluate_track_r_on_tahrir_test(master_rows, layered_by_id, "score_E1", clean_test_idx)
    exp_rows.append(
        {
            "experiment": "Exp_B_Qualifiers_E1_Det",
            "track": "Track_R_Deterministic",
            "model_or_layer": "score_E1 (B + within-band E1 qualifiers)",
            "eval_target": "tahrir_clean_test_descriptive",
            "status": "COMPLETED",
            "n_eval": len(clean_test_idx),
            "rank_mae": m_b_test["rank_mae"],
            "rank_qwk": m_b_test["rank_qwk"],
            "rank_spearman": m_b_test["rank_spearman"],
            "bin_acc": m_b_test["bin_acc"],
            "tier3_acc": m_b_test["tier3_acc"],
            "tier3_macro_f1": m_b_test["tier3_macro_f1"],
            "shift_macro_f1": m_b_test["shift_macro_f1"],
            "r6_rank_mae": m_b_test["r6_rank_mae"],
        }
    )

    # Optional Stage 2 ESA integration
    if stage2_dir is not None and (stage2_dir / "STAGE2_MODEL_COMPARISON_V3.csv").exists():
        with (stage2_dir / "STAGE2_MODEL_COMPARISON_V3.csv").open("r", encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                if r["split"] != "test":
                    continue
                exp_rows.append(
                    {
                        "experiment": "Exp_B_ESA_Learned",
                        "track": "Track_L_ESA",
                        "model_or_layer": r["model"],
                        "eval_target": "tahrir_clean_test",
                        "status": "COMPLETED",
                        "n_eval": len(clean_test_idx),
                        "rank_mae": float(r["rank_mae"]),
                        "rank_qwk": float(r["rank_qwk"]),
                        "rank_spearman": float(r["rank_spearman"]),
                        "bin_acc": float(r["bin_acc"]),
                        "tier3_acc": float(r["tier3_acc"]),
                        "tier3_macro_f1": float(r["tier3_macro_f1"]),
                        "shift_macro_f1": float(r["shift_macro_f1"]),
                        "r6_rank_mae": float(r["r6_rank_mae"]),
                    }
                )
    else:
        exp_rows.append(
            {
                "experiment": "Exp_B_ESA_Learned",
                "track": "Track_L_ESA",
                "model_or_layer": "M3b_AraBERTv02_Full / M3a_GenericSentiment",
                "eval_target": "tahrir_clean_test",
                "status": "PENDING_CUDA_GPU",
                "n_eval": len(clean_test_idx),
                "rank_mae": "",
                "rank_qwk": "",
                "rank_spearman": "",
                "bin_acc": "",
                "tier3_acc": "",
                "tier3_macro_f1": "",
                "shift_macro_f1": "",
                "r6_rank_mae": "",
            }
        )

    # Exp C is evaluated ONLY vs al-Kashif (NEVER vs Tahrir)
    kashif_rows: list[dict[str, Any]] = []
    boot_rows: list[dict[str, Any]] = []
    layer_maps = [
        ("Exp_A_score_B", ranks_b_clean),
        ("Exp_B_score_E1", ranks_e1_clean),
        ("Exp_C_score_E2", ranks_e2_clean),
    ]
    stage3_outputs_by_id: dict[str, dict[str, str]] = {}
    if stage3_dir is not None and (stage3_dir / "STAGE3_TC_GNN_OUTPUTS_8827_V3.csv").exists():
        with (stage3_dir / "STAGE3_TC_GNN_OUTPUTS_8827_V3.csv").open("r", encoding="utf-8-sig", newline="") as f:
            stage3_outputs_by_id = {r["entry_id"]: r for r in csv.DictReader(f)}
        ranks_g_est = {
            eid: float(r["score_G_continuous"])
            for eid, r in stage3_outputs_by_id.items()
            if r["source"] == "model_estimate" and r["score_G_continuous"].strip()
        }
        ranks_g_all = {
            eid: float(r["score_G_continuous"])
            for eid, r in stage3_outputs_by_id.items()
            if r["score_G_continuous"].strip()
        }
        if ranks_g_all:
            layer_maps.append(("Exp_D_G4a_All", ranks_g_all))
        if ranks_g_est:
            layer_maps.append(("Exp_D_G4a_EstimateOnly", ranks_g_est))

    def _paired_clean(eid: str, kr: dict[str, str]) -> bool:
        """Primary subset: paired, symmetric non-verbatim, and Tahrir does not cite al-Dhahabi."""
        return (
            eid in common_b_e2_ids
            and kr["verbatim_overlap"] == "False"
            and kr.get("tahrir_cites_dhahabi", "False") == "False"
        )

    for lname, rmap in layer_maps:
        for sname, fn in [
            ("all_observed", None),
            ("all_excl_sahabi", lambda _eid, kr: kr["is_sahabi"] == "False"),
            ("paired_B_E2_common", lambda eid, _kr: eid in common_b_e2_ids),
            ("non_verbatim", lambda _eid, kr: kr["verbatim_overlap"] == "False"),
            # v1 one-sided filter (al-Kashif span absent from Taqrib only), kept for comparison
            ("paired_non_verbatim_taqrib_only_v1", lambda eid, kr: eid in common_b_e2_ids and kr.get("verbatim_overlap_taqrib", kr["verbatim_overlap"]) == "False"),
            ("paired_non_verbatim", lambda eid, kr: eid in common_b_e2_ids and kr["verbatim_overlap"] == "False"),
            (
                "paired_non_verbatim_excl_sahabi",
                lambda eid, kr: eid in common_b_e2_ids and kr["verbatim_overlap"] == "False" and kr["is_sahabi"] == "False",
            ),
            ("paired_clean", _paired_clean),
            ("observed_first_grade_abstained_B", lambda _eid, kr: kr["status_E2"] == "observed_first_grade"),
        ]:
            ev = evaluate_against_kashif(rmap, kashif_by_id, subset_name=sname, filter_fn=fn)
            if ev["n"] == 0:
                continue
            kashif_rows.append(
                {
                    "layer": lname,
                    "subset": sname,
                    "n": ev["n"],
                    "tier3_acc": ev["tier3_acc"],
                    "tier3_macro_f1": ev["tier3_macro_f1"],
                    "tier3_weighted_f1": ev["tier3_weighted_f1"],
                    "tier3_qwk": ev["tier3_qwk"],
                    "tier5_qwk": ev["tier5_qwk"],
                    "tier5_spearman": ev["tier5_spearman"],
                    **_majority_floor(ev),
                }
            )
            if lname == "Exp_C_score_E2" and sname == "paired_clean":
                exp_rows.append(
                    {
                        "experiment": "Exp_C_Scholarly_E2",
                        "track": "Track_R_Deterministic",
                        "model_or_layer": "score_E2 (B + E1 + Tahrir)",
                        "eval_target": "al_kashif_paired_clean",
                        "status": "COMPLETED",
                        "n_eval": ev["n"],
                        "rank_mae": "",
                        "rank_qwk": ev["tier3_qwk"],
                        "rank_spearman": ev["tier5_spearman"],
                        "bin_acc": "",
                        "tier3_acc": ev["tier3_acc"],
                        "tier3_macro_f1": ev["tier3_macro_f1"],
                        "shift_macro_f1": "",
                        "r6_rank_mae": "",
                    }
                )

    for sname, fn in [
        ("paired_B_E2_common", lambda eid, _kr: eid in common_b_e2_ids),
        ("paired_non_verbatim", lambda eid, kr: eid in common_b_e2_ids and kr["verbatim_overlap"] == "False"),
        (
            "paired_non_verbatim_excl_sahabi",
            lambda eid, kr: eid in common_b_e2_ids and kr["verbatim_overlap"] == "False" and kr["is_sahabi"] == "False",
        ),
        ("paired_clean", _paired_clean),
    ]:
        for b_row in paired_bootstrap_kashif(
            ranks_b_clean, ranks_e2_clean, kashif_by_id, fn, n_boot=bootstrap_iters, seed=42
        ):
            boot_rows.append({"comparison": "E2_vs_B", "subset": sname, **b_row})

    # Optional Stage 3 TC-GNN Exp D integration
    if stage3_dir is not None and (stage3_dir / "STAGE3_MODEL_COMPARISON_5SEED_V3.csv").exists():
        with (stage3_dir / "STAGE3_MODEL_COMPARISON_5SEED_V3.csv").open("r", encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                if r["split"] != "test":
                    continue
                exp_rows.append(
                    {
                        "experiment": "Exp_D_TC_GNN",
                        "track": "Track_L_TC_GNN",
                        "model_or_layer": r["model"],
                        "eval_target": "tahrir_clean_test_5seed_ens",
                        "status": "COMPLETED",
                        "n_eval": len(clean_test_idx),
                        "rank_mae": float(r["ens_rank_mae"]),
                        "rank_qwk": float(r["rank_qwk_mean"]),
                        "rank_spearman": float(r["rank_spearman_mean"]) if r.get("rank_spearman_mean") else "",
                        "bin_acc": float(r["bin_acc_mean"]),
                        "tier3_acc": float(r["tier3_acc_mean"]) if r.get("tier3_acc_mean") else "",
                        "tier3_macro_f1": float(r["tier3_macro_f1_mean"]),
                        "shift_macro_f1": float(r["ens_shift_macro_f1"]),
                        "r6_rank_mae": float(r["r6_rank_mae_mean"]),
                    }
                )
    else:
        exp_rows.append(
            {
                "experiment": "Exp_D_TC_GNN",
                "track": "Track_L_TC_GNN",
                "model_or_layer": "G4a_Directed_TC_GNN_Sanad (vs G2b & G0)",
                "eval_target": "tahrir_clean_test_5seed_ens",
                "status": "PENDING_CUDA_GPU",
                "n_eval": len(clean_test_idx),
                "rank_mae": "",
                "rank_qwk": "",
                "rank_spearman": "",
                "bin_acc": "",
                "tier3_acc": "",
                "tier3_macro_f1": "",
                "shift_macro_f1": "",
                "r6_rank_mae": "",
            }
        )

    # Graph Homophily (CPU exact)
    n_nodes = len(master_rows)
    valid_b = np.array([bool(layered_by_id[r["entry_id"]]["rank_B"].strip()) for r in master_rows], dtype=bool)
    labels_b12 = np.array(
        [int(layered_by_id[r["entry_id"]]["rank_B"]) - 1 if layered_by_id[r["entry_id"]]["rank_B"].strip() else -1 for r in master_rows],
        dtype=np.int64,
    )
    labels_b3 = np.array(
        [rank_to_tier3_id(int(layered_by_id[r["entry_id"]]["rank_B"])) if layered_by_id[r["entry_id"]]["rank_B"].strip() else -1 for r in master_rows],
        dtype=np.int64,
    )
    valid_e2 = np.array(
        [
            layered_by_id[r["entry_id"]]["status_E2"] not in EXCLUDED_E2_STATUSES
            and bool(layered_by_id[r["entry_id"]]["rank_E2"].strip())
            for r in master_rows
        ],
        dtype=bool,
    )
    labels_e2_12 = np.array(
        [int(layered_by_id[r["entry_id"]]["rank_E2"]) - 1 if valid_e2[i] else -1 for i, r in enumerate(master_rows)],
        dtype=np.int64,
    )
    labels_e2_3 = np.array(
        [rank_to_tier3_id(int(layered_by_id[r["entry_id"]]["rank_E2"])) if valid_e2[i] else -1 for i, r in enumerate(master_rows)],
        dtype=np.int64,
    )
    homophily_summary = {
        "n_nodes": n_nodes,
        "sanad_edges_raw": deg_info["n_sanad_raw"],
        "sanad_edges_chrono_kept": deg_info["n_sanad_kept"],
        "sanad_edges_chrono_pruned": deg_info["n_sanad_pruned"],
        "chrono_sanad_rank_B_12": compute_graph_homophily(deg_info["chrono_src"], deg_info["chrono_dst"], labels_b12, valid_b),
        "chrono_sanad_rank_B_3tier": compute_graph_homophily(deg_info["chrono_src"], deg_info["chrono_dst"], labels_b3, valid_b),
        "chrono_sanad_rank_E2_12": compute_graph_homophily(deg_info["chrono_src"], deg_info["chrono_dst"], labels_e2_12, valid_e2),
        "chrono_sanad_rank_E2_3tier": compute_graph_homophily(deg_info["chrono_src"], deg_info["chrono_dst"], labels_e2_3, valid_e2),
        "unpruned_sanad_rank_E2_12": compute_graph_homophily(deg_info["unpruned_src"], deg_info["unpruned_dst"], labels_e2_12, valid_e2),
        "unpruned_sanad_rank_E2_3tier": compute_graph_homophily(deg_info["unpruned_src"], deg_info["unpruned_dst"], labels_e2_3, valid_e2),
    }

    # Slice metrics & coverage/missingness accounting
    slice_rows: list[dict[str, Any]] = []
    iso_mask = deg_info["is_isolated"]
    test_conn = [i for i in clean_test_idx if not iso_mask[i]]
    test_iso = [i for i in clean_test_idx if iso_mask[i]]
    test_r6 = [i for i in clean_test_idx if layered_by_id[master_rows[i]["entry_id"]]["taqrib_is_conditional_maqbul"] == "True"]
    all_e2_obs = [
        i
        for i, r in enumerate(master_rows)
        if layered_by_id[r["entry_id"]]["status_E2"] not in EXCLUDED_E2_STATUSES
        and layered_by_id[r["entry_id"]]["rank_B"].strip()
        and layered_by_id[r["entry_id"]]["rank_E2"].strip()
    ]
    all_r6 = [i for i in all_e2_obs if layered_by_id[master_rows[i]["entry_id"]]["taqrib_is_conditional_maqbul"] == "True"]

    for sname, idxs, desc in [
        ("clean_test_cohort", clean_test_idx, "Core test split after excluding missing + suspect_alignment"),
        ("test_connected_chrono_sanad", test_conn, "Clean test narrators with >=1 chrono_pruned sanad edge"),
        ("test_isolated_chrono_sanad", test_iso, "Clean test narrators with 0 chrono_pruned sanad edges"),
        ("test_rank6_maqbul", test_r6, "Clean test conditional maqbul narrators"),
        ("full_rank6_maqbul_paired", all_r6, "All clean paired conditional maqbul narrators"),
    ]:
        mb = evaluate_track_r_on_tahrir_test(master_rows, layered_by_id, "score_B", idxs)
        me1 = evaluate_track_r_on_tahrir_test(master_rows, layered_by_id, "score_E1", idxs)
        slice_rows.append(
            {
                "slice": sname,
                "n": len(idxs),
                "description": desc,
                "B_vs_E2_rank_mae": mb["rank_mae"],
                "E1_vs_E2_rank_mae": me1["rank_mae"],
                "B_vs_E2_tier3_mf1": mb["tier3_macro_f1"],
                "E1_vs_E2_tier3_mf1": me1["tier3_macro_f1"],
                "B_vs_E2_qwk": mb["rank_qwk"],
                "E1_vs_E2_qwk": me1["rank_qwk"],
            }
        )

    audit = compute_disagreement_audit(layered_by_id)
    sens_rows = run_e1_sensitivity(master_rows, kashif_by_id, layered_by_id, clean_test_idx)

    # Write CSV artefacts
    exp_csv = out_dir / "EXPERIMENT_A_TO_D_METRICS_V3.csv"
    with exp_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(exp_rows[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(exp_rows)

    kashif_out_csv = out_dir / "KASHIF_AGREEMENT_V3.csv"
    with kashif_out_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(kashif_rows[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(kashif_rows)

    boot_csv = out_dir / "KASHIF_PAIRED_BOOTSTRAP_V3.csv"
    with boot_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(boot_rows[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(boot_rows)

    sens_csv = out_dir / "E1_SENSITIVITY_SUMMARY_V3.csv"
    with sens_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(sens_rows[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(sens_rows)

    slice_csv = out_dir / "SLICE_METRICS_V3.csv"
    with slice_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(slice_rows[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(slice_rows)

    # Write Final Consolidated 8,827 Narrator Table
    final_csv = out_dir / "FINAL_LAYERED_RIJAL_SCORES_8827_V3.csv"
    final_fields = [
        "entry_id", "entry_number_numeric", "split",
        "score_B", "rank_B", "status_B",
        "score_E1", "delta_E1", "status_E1", "e1_rules_applied",
        "score_E2", "rank_E2", "delta_E2", "status_E2", "tahrir_disposition",
        "taqrib_is_conditional_maqbul", "suspect_alignment_reason",
        "score_G_continuous", "score_G_0_100", "score_G_estimate", "score_G_entropy",
        "source", "G_agrees_with_tahrir", "G_residual",
        "sanad_chrono_pruned_out_degree", "sanad_chrono_pruned_in_degree", "sanad_chrono_pruned_is_isolated",
        "kashif_tier_3", "kashif_tier_5", "kashif_verbatim_overlap",
    ]
    with final_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=final_fields, lineterminator="\n")
        w.writeheader()
        for i, r in enumerate(master_rows):
            eid = r["entry_id"]
            lr = layered_by_id[eid]
            kr = kashif_by_id.get(eid, {})
            s3r = stage3_outputs_by_id.get(eid)
            if s3r is not None:
                g_cont = s3r["score_G_continuous"]
                g_100 = s3r["score_G_0_100"]
                g_est = s3r["score_G_estimate"]
                g_ent = s3r["score_G_entropy"]
                src = s3r["source"]
                g_ag = s3r["G_agrees_with_tahrir"]
                g_res = s3r["G_residual"]
            else:
                st_e2 = lr["status_E2"].strip()
                needs_est = st_e2 in {"missing", "abstained", "suspect_alignment"} or not lr["rank_E2"].strip()
                g_cont = g_100 = g_est = g_ent = g_ag = g_res = ""
                src = "pending_stage3_gpu" if needs_est else "observed_scholarly"

            w.writerow(
                {
                    "entry_id": eid,
                    "entry_number_numeric": lr["entry_number_numeric"],
                    "split": lr["split"],
                    "score_B": lr["score_B"],
                    "rank_B": lr["rank_B"],
                    "status_B": lr["status_B"],
                    "score_E1": lr["score_E1"],
                    "delta_E1": lr["delta_E1"],
                    "status_E1": lr["status_E1"],
                    "e1_rules_applied": lr["e1_rules_applied"],
                    "score_E2": lr["score_E2"],
                    "rank_E2": lr["rank_E2"],
                    "delta_E2": lr["delta_E2"],
                    "status_E2": lr["status_E2"],
                    "tahrir_disposition": lr["tahrir_disposition"],
                    "taqrib_is_conditional_maqbul": lr["taqrib_is_conditional_maqbul"],
                    "suspect_alignment_reason": lr["suspect_alignment_reason"],
                    "score_G_continuous": g_cont,
                    "score_G_0_100": g_100,
                    "score_G_estimate": g_est,
                    "score_G_entropy": g_ent,
                    "source": src,
                    "G_agrees_with_tahrir": g_ag,
                    "G_residual": g_res,
                    "sanad_chrono_pruned_out_degree": int(deg_info["out_deg"][i]),
                    "sanad_chrono_pruned_in_degree": int(deg_info["in_deg"][i]),
                    "sanad_chrono_pruned_is_isolated": int(deg_info["is_isolated"][i]),
                    "kashif_tier_3": kr.get("kashif_tier_3", ""),
                    "kashif_tier_5": kr.get("kashif_tier_5", ""),
                    "kashif_verbatim_overlap": kr.get("verbatim_overlap", ""),
                }
            )

    # Markdown Report
    md = [
        "# Layered 0–100 Narrator Score: Experiments A–D Report (v3)",
        "",
        f"- **Generated (UTC):** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%SZ')}",
        f"- **Stage 2 ESA Dir:** `{to_posix_relative(stage2_dir, ROOT) if stage2_dir and stage2_dir.exists() else 'NOT YET RUN (CUDA GPU required)'}`",
        f"- **Stage 3 TC-GNN Dir:** `{to_posix_relative(stage3_dir, ROOT) if stage3_dir and stage3_dir.exists() else 'NOT YET RUN (CUDA GPU required)'}`",
        "",
        "## 0. Coverage, Missingness, and Exclusion Accounting (8,827 Narrators)",
        "",
        f"- **Layer B (`status_B`):** observed `{audit['status_B'].get('observed', 0)}`, abstained `{audit['status_B'].get('abstained', 0)}`.",
        f"- **Layer E1 (`status_E1`):** observed qualifier adjustment `{audit['status_E1'].get('observed', 0)}`, not_applicable `{audit['status_E1'].get('not_applicable', 0)}`, abstained `{audit['status_E1'].get('abstained', 0)}` (within paired B+E2 clean cohort: shifted toward E2 `{audit['e1_alignment_with_e2']['toward']}`, unchanged distance `{audit['e1_alignment_with_e2']['unchanged_dist']}`, away `{audit['e1_alignment_with_e2']['away']}`).",
        f"- **Layer E2 (`status_E2`):** agreement `{audit['status_E2'].get('observed_agreement', 0)}`, dissent `{audit['status_E2'].get('observed_dissent', 0)}`, maqbul_to_r7 `{audit['status_E2'].get('observed_maqbul_to_r7', 0)}`, first_grade `{audit['status_E2'].get('observed_first_grade', 0)}`, no_grade `{audit['status_E2'].get('observed_no_grade', 0)}`, qualification `{audit['status_E2'].get('observed_qualification', 0)}`, abstained `{audit['status_E2'].get('abstained', 0)}`, **excluded `missing` (`{audit['status_E2'].get('missing', 0)}`) + `suspect_alignment` (`{audit['status_E2'].get('suspect_alignment', 0)}`)**.",
        f"- **Rank Shift Audit (paired observed B & E2):** upgraded `{audit['rank_shifts_paired_obs']['upgraded']}`, unchanged `{audit['rank_shifts_paired_obs']['unchanged']}`, downgraded `{audit['rank_shifts_paired_obs']['downgraded']}`; binary band crossings (`1–6 <-> 7–12`): `{audit['binary_crossings']['jarh_to_tadil']}` upgrades, `{audit['binary_crossings']['tadil_to_jarh']}` downgrades.",
        "",
        "## 1. Experiments A–D Summary",
        "",
        "| Experiment | Track | Model / Layer | Eval Target | Status | N | Rank MAE ↓ | QWK ↑ | 3-Tier Acc ↑ | 3-Tier MF1 ↑ | Shift MF1 ↑ | R6 MAE ↓ |",
        "|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in exp_rows:
        md.append(
            f"| `{r['experiment']}` | `{r['track']}` | `{r['model_or_layer']}` | `{r['eval_target']}` | `{r['status']}` | {r['n_eval']} | "
            f"{r['rank_mae']} | {r['rank_qwk']} | {r['tier3_acc']} | {r['tier3_macro_f1']} | {r['shift_macro_f1']} | {r['r6_rank_mae']} |"
        )
    md.extend(
        [
            "",
            "## 2. External Validation vs al-Dhahabi's *al-Kāshif* (1616)",
            "",
            "Primary subset: `paired_clean` (paired B/E2, al-Kashif span in neither Taqrib nor Tahrir, Tahrir does not cite al-Dhahabi). "
            "QWK and Macro-F1 are the primary agreement metrics; accuracy is secondary and must be read against the majority-class floor.",
            "",
            "| Layer | Subset | N | 3-Tier Acc ↑ | Majority Acc | 3-Tier MF1 ↑ | 3-Tier QWK ↑ | 5-Tier QWK ↑ | 5-Tier Spearman ↑ |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for kr in kashif_rows:
        md.append(
            f"| `{kr['layer']}` | `{kr['subset']}` | {kr['n']} | {kr['tier3_acc']:.4f} | {kr['majority_tier3_acc']:.4f} | {kr['tier3_macro_f1']:.4f} | "
            f"{kr['tier3_qwk']:.4f} | {kr['tier5_qwk']:.4f} | {kr['tier5_spearman']:.4f} |"
        )
    md.extend(
        [
            "",
            f"### Paired Bootstrap E2 vs B on *al-Kāshif* ($B = {bootstrap_iters}$, `seed = 42`)",
            "",
            "| Subset | Metric | N | Δ (E2 − B) | 95% CI | Two-sided p |",
            "|---|---|---:|---:|---|---:|",
        ]
    )
    for br in boot_rows:
        md.append(
            f"| `{br['subset']}` | `{br['metric']}` | {br['n_common']} | {br['delta']:+.4f} | [{br['ci95_low']:+.4f}, {br['ci95_high']:+.4f}] | {br['p_value_2sided']:.4f} |"
        )
    md.extend(
        [
            "",
            "## 3. Graph Homophily (`TAQRIB_V2_GRAPH_EDGES.csv`, Pure Sanad)",
            "",
            f"- **Chronology Pruning (`chrono_pruned`):** `{homophily_summary['sanad_edges_raw']}` -> `{homophily_summary['sanad_edges_chrono_kept']}` edges (`{homophily_summary['sanad_edges_chrono_pruned']}` pruned).",
            f"- **Chronology-Pruned Sanad (E2 labels):** 12-rank edge={homophily_summary['chrono_sanad_rank_E2_12']['edge_homophily']:.4f} (class={homophily_summary['chrono_sanad_rank_E2_12']['class_homophily']:.4f}); 3-tier edge={homophily_summary['chrono_sanad_rank_E2_3tier']['edge_homophily']:.4f} (class={homophily_summary['chrono_sanad_rank_E2_3tier']['class_homophily']:.4f}).",
            f"- **Unpruned Sanad (E2 labels):** 12-rank edge={homophily_summary['unpruned_sanad_rank_E2_12']['edge_homophily']:.4f} (class={homophily_summary['unpruned_sanad_rank_E2_12']['class_homophily']:.4f}); 3-tier edge={homophily_summary['unpruned_sanad_rank_E2_3tier']['edge_homophily']:.4f} (class={homophily_summary['unpruned_sanad_rank_E2_3tier']['class_homophily']:.4f}).",
            "",
            "## 4. Layer E₁ Sensitivity Analysis (`default`, `halved`, `doubled`, `off`)",
            "",
            "| Preset | N Observed E1 | Test Rank MAE | Test Spearman | Test 3-Tier MF1 | Kashif Full 3T Acc | Kashif Full 3T MF1 | Kashif NV 3T Acc | Kashif NV 3T MF1 |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for sr in sens_rows:
        md.append(
            f"| `{sr['e1_preset']}` | {sr['n_e1_observed']} | {sr['test_vs_e2_rank_mae']:.4f} | {sr['test_vs_e2_rank_spearman']:.4f} | "
            f"{sr['test_vs_e2_tier3_macro_f1']:.4f} | {sr['kashif_full_tier3_acc']:.4f} | {sr['kashif_full_tier3_mf1']:.4f} | "
            f"{sr['kashif_nv_tier3_acc']:.4f} | {sr['kashif_nv_tier3_mf1']:.4f} |"
        )
    md.extend(
        [
            "",
            "## 5. Slice Breakdowns (Clean Test & Subgroup Coverage)",
            "",
            "| Slice | N | B vs E2 MAE | E1 vs E2 MAE | B vs E2 3T-MF1 | E1 vs E2 3T-MF1 | B vs E2 QWK | E1 vs E2 QWK |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for sl in slice_rows:
        md.append(
            f"| `{sl['slice']}` | {sl['n']} | {sl['B_vs_E2_rank_mae']:.4f} | {sl['E1_vs_E2_rank_mae']:.4f} | "
            f"{sl['B_vs_E2_tier3_mf1']:.4f} | {sl['E1_vs_E2_tier3_mf1']:.4f} | {sl['B_vs_E2_qwk']:.4f} | {sl['E1_vs_E2_qwk']:.4f} |"
        )

    report_md = out_dir / "LAYERED_EXPERIMENTS_REPORT_V3.md"
    report_md.write_bytes(("\n".join(md) + "\n").encode("utf-8"))

    manifest_files = [exp_csv, kashif_out_csv, boot_csv, sens_csv, slice_csv, final_csv, report_md]
    manifest = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "script": to_posix_relative(Path(__file__), ROOT),
        "elapsed_sec": round(time.time() - t0, 2),
        "stage2_dir": to_posix_relative(stage2_dir, ROOT) if stage2_dir and stage2_dir.exists() else None,
        "stage3_dir": to_posix_relative(stage3_dir, ROOT) if stage3_dir and stage3_dir.exists() else None,
        "disagreement_audit": audit,
        "homophily": homophily_summary,
        "files": {p.name: {"sha256": sha256_text_normalized(p), "bytes": p.stat().st_size} for p in manifest_files},
    }
    manifest_json = out_dir / "MANIFEST.json"
    manifest_json.write_bytes((json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    (out_dir / "MANIFEST.sha256").write_bytes(
        ("\n".join(f"{sha256_text_normalized(p)}  {p.name}" for p in [*manifest_files, manifest_json]) + "\n").encode("ascii")
    )
    return {"out_dir": out_dir, "audit": audit, "homophily": homophily_summary, "kashif": kashif_rows, "sensitivity": sens_rows}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run P5 Track R (+ optional Track L) experiments.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--stage2-dir", type=Path, default=None)
    parser.add_argument("--stage3-dir", type=Path, default=None)
    parser.add_argument("--bootstrap-iters", type=int, default=2000)
    parser.add_argument("--kashif-csv", type=Path, default=KASHIF_AUDIT, help="al-Kashif overlap audit (e.g. a wuththiqa-policy sensitivity build).")
    args = parser.parse_args()
    res = run_suite(
        out_dir=args.out_dir,
        kashif_csv=args.kashif_csv,
        stage2_dir=args.stage2_dir,
        stage3_dir=args.stage3_dir,
        bootstrap_iters=args.bootstrap_iters,
    )
    print(f"Layered experiments v3 complete -> {res['out_dir']}")


if __name__ == "__main__":
    main()
