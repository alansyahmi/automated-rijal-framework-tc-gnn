"""Shared pure-NumPy/scikit-learn helpers for Stage 2, Stage 3, and P5 v3 pipelines.

Contains zero PyTorch/CUDA imports so CPU unit tests and deterministic
Track R experiments run cleanly in any environment.
"""

from __future__ import annotations

import math
import re
from collections import defaultdict
from typing import Any

import numpy as np
from scipy.stats import spearmanr
from sklearn.metrics import (
    accuracy_score,
    cohen_kappa_score,
    f1_score,
    mean_absolute_error,
    precision_recall_fscore_support,
    root_mean_squared_error,
)

DIACRITICS_RE = re.compile(r"[\u064b-\u065f\u0670\u0640]")
LEAD_NUM_RE = re.compile(r"^[٠-٩0-9]+\s*[-–]\s*")
WHITESPACE_RE = re.compile(r"\s+")

SHIFT_LABELS = ["upgraded", "unchanged", "downgraded"]
SHIFT_TO_ID = {s: i for i, s in enumerate(SHIFT_LABELS)}

SUBTIERS = ["kibar", "awsat", "sighar", "unspecified"]
SIGIL_COLS = [
    "sigil_bukhari",
    "sigil_muslim",
    "sigil_abudawud",
    "sigil_tirmidhi",
    "sigil_nasai",
    "sigil_ibnmajah",
    "sigil_in_sahihayn",
    "sigil_canonical_book_count",
    "sigil_has_ayn",
    "sigil_has_four",
    "sigil_is_tamyiz",
    "sigil_has_aux_only",
]
QUAL_COLS = [
    "taqrib_has_context_note",
    "qual_yudallis",
    "qual_yursil",
    "qual_yukhti_yahim",
    "qual_ikhtalata",
    "qual_rumiya_bidah",
    "qual_sayyi_hifz",
    "qual_lin",
    "qual_qalil_hadith",
]

EXCLUDED_E2_STATUSES = {"missing", "suspect_alignment"}


def normalize_text(s: str) -> str:
    s = LEAD_NUM_RE.sub("", s.strip())
    s = DIACRITICS_RE.sub("", s)
    return WHITESPACE_RE.sub(" ", s).strip()


def rank_to_0_100(rank: float, scale: str | None = None) -> float:
    """Rank (fractional allowed) -> 0-100 on the active scale (common/rank_scale.py)."""
    from common.rank_scale import DEFAULT_SCALE, rank_to_score

    return rank_to_score(rank, scale or DEFAULT_SCALE)


def rank_to_0_1(rank: float, scale: str | None = None) -> float:
    return rank_to_0_100(rank, scale) / 100.0


def rank_to_tier3_id(rank: int) -> int:
    """Map Bilgin 1-12 rank to 3-tier ordinal class: 2=1..3, 1=4..6, 0=7..12."""
    if rank <= 3:
        return 2
    if rank <= 6:
        return 1
    return 0


def assert_no_tahrir_leakage(feature_names: list[str], extra_banned: tuple[str, ...] = ()) -> None:
    banned = ("tahrir", "score_e2", "rank_e2", "delta_e2", "status_e2", "score2") + extra_banned
    for fn in feature_names:
        low = fn.lower()
        for b in banned:
            if b in low:
                raise AssertionError(f"Leakage feature detected in model inputs: {fn}")


def build_meta_matrix(rows: list[dict[str, str]]) -> tuple[np.ndarray, list[str]]:
    feat_names = (
        ["taqrib_rank_num", "taqrib_is_conditional_maqbul"]
        + [f"taqrib_rank_oh_{k}" for k in range(1, 13)]
        + ["tabaqa_num"]
        + [f"subtier_{st}" for st in SUBTIERS]
        + SIGIL_COLS
        + QUAL_COLS
        + ["taqrib_char_len", "taqrib_word_count"]
    )
    assert_no_tahrir_leakage(
        feat_names,
        extra_banned=("graph_", "sanad_", "bukhari_out", "bukhari_in", "nbr_"),
    )

    mat = np.zeros((len(rows), len(feat_names)), dtype=np.float32)
    for i, r in enumerate(rows):
        rk_str = r["taqrib_rank_bilgin_1_to_12"].strip()
        rk = int(rk_str) if rk_str else -1
        col = 0
        mat[i, col] = float(rk)
        col += 1
        mat[i, col] = 1.0 if r["taqrib_is_conditional_maqbul"] == "True" else 0.0
        col += 1
        for k in range(1, 13):
            mat[i, col] = 1.0 if rk == k else 0.0
            col += 1
        tb = int(r["tabaqa_1_to_12"]) if r["tabaqa_1_to_12"].strip() else -1
        mat[i, col] = float(tb)
        col += 1
        st = r["tabaqa_subtier"]
        for s in SUBTIERS:
            mat[i, col] = 1.0 if st == s else 0.0
            col += 1
        for sc in SIGIL_COLS:
            mat[i, col] = float(r[sc])
            col += 1
        for qc in QUAL_COLS:
            mat[i, col] = float(r[qc])
            col += 1
        mat[i, col] = float(r["taqrib_char_len"])
        col += 1
        mat[i, col] = float(r["taqrib_word_count"])
        col += 1
    return mat, feat_names


def compute_metrics(
    y_rank_true: np.ndarray,
    y_shift_true: np.ndarray,
    y_rank_pred_cont: np.ndarray,
    y_shift_pred: np.ndarray,
    is_maqbul: np.ndarray,
) -> dict[str, float]:
    y_rank_pred_disc = np.clip(np.rint(y_rank_pred_cont), 1, 12).astype(int)

    rank_mae = float(mean_absolute_error(y_rank_true, y_rank_pred_cont))
    rank_rmse = float(root_mean_squared_error(y_rank_true, y_rank_pred_cont))
    rank_qwk = float(cohen_kappa_score(y_rank_true, y_rank_pred_disc, weights="quadratic"))
    sp_corr = float(spearmanr(y_rank_true, y_rank_pred_cont).statistic)
    if math.isnan(sp_corr):
        sp_corr = 0.0
    rank_exact_acc = float(accuracy_score(y_rank_true, y_rank_pred_disc))
    rank_within1_acc = float(np.mean(np.abs(y_rank_true - y_rank_pred_disc) <= 1))

    w_prec, w_rec, w_f1, _ = precision_recall_fscore_support(
        y_rank_true, y_rank_pred_disc, average="weighted", zero_division=0
    )
    rank_macro_f1 = float(f1_score(y_rank_true, y_rank_pred_disc, average="macro", zero_division=0))

    # Wahba et al. (2026) Binary Ta'dil (1..6) vs Jarh (7..12)
    y_bin_true = (y_rank_true <= 6).astype(int)
    y_bin_pred = (y_rank_pred_disc <= 6).astype(int)
    bin_acc = float(accuracy_score(y_bin_true, y_bin_pred))
    b_prec, b_rec, b_wf1, _ = precision_recall_fscore_support(
        y_bin_true, y_bin_pred, average="weighted", zero_division=0
    )
    bin_macro_f1 = float(f1_score(y_bin_true, y_bin_pred, average="macro", zero_division=0))

    # PO1 3-Tier Ordinal Classification (1-3 / 4-6 / 7-12)
    y_t3_true = np.array([rank_to_tier3_id(int(r)) for r in y_rank_true], dtype=int)
    y_t3_pred = np.array([rank_to_tier3_id(int(r)) for r in y_rank_pred_disc], dtype=int)
    tier3_acc = float(accuracy_score(y_t3_true, y_t3_pred))
    tier3_macro_f1 = float(f1_score(y_t3_true, y_t3_pred, labels=[0, 1, 2], average="macro", zero_division=0))
    tier3_weighted_f1 = float(f1_score(y_t3_true, y_t3_pred, labels=[0, 1, 2], average="weighted", zero_division=0))

    # Alturayeif et al. (2024 StanceEval) 3-Class Shift
    shift_acc = float(accuracy_score(y_shift_true, y_shift_pred))
    shift_macro_f1 = float(f1_score(y_shift_true, y_shift_pred, labels=[0, 1, 2], average="macro", zero_division=0))
    shift_weighted_f1 = float(
        f1_score(y_shift_true, y_shift_pred, labels=[0, 1, 2], average="weighted", zero_division=0)
    )
    per_cls_f1 = f1_score(y_shift_true, y_shift_pred, labels=[0, 1, 2], average=None, zero_division=0)
    f1_up, f1_unch, f1_down = float(per_cls_f1[0]), float(per_cls_f1[1]), float(per_cls_f1[2])
    shift_active_macro_f1 = 0.5 * (f1_up + f1_down)

    # Rank 6 Maqbul subgroup
    r6_mask = is_maqbul.astype(bool)
    r6_n = int(r6_mask.sum())
    if r6_n > 0:
        r6_mae = float(mean_absolute_error(y_rank_true[r6_mask], y_rank_pred_cont[r6_mask]))
        r6_exact = float(accuracy_score(y_rank_true[r6_mask], y_rank_pred_disc[r6_mask]))
        r6_shift_mf1 = float(
            f1_score(y_shift_true[r6_mask], y_shift_pred[r6_mask], labels=[0, 1, 2], average="macro", zero_division=0)
        )
    else:
        r6_mae = r6_exact = r6_shift_mf1 = 0.0

    return {
        "rank_mae": round(rank_mae, 4),
        "rank_rmse": round(rank_rmse, 4),
        "rank_qwk": round(rank_qwk, 4),
        "rank_spearman": round(sp_corr, 4),
        "rank_exact_acc": round(rank_exact_acc, 4),
        "rank_within1_acc": round(rank_within1_acc, 4),
        "rank_weighted_precision": round(float(w_prec), 4),
        "rank_weighted_recall": round(float(w_rec), 4),
        "rank_weighted_f1": round(float(w_f1), 4),
        "rank_macro_f1": round(rank_macro_f1, 4),
        "bin_acc": round(bin_acc, 4),
        "bin_weighted_precision": round(float(b_prec), 4),
        "bin_weighted_recall": round(float(b_rec), 4),
        "bin_weighted_f1": round(float(b_wf1), 4),
        "bin_macro_f1": round(bin_macro_f1, 4),
        "tier3_acc": round(tier3_acc, 4),
        "tier3_macro_f1": round(tier3_macro_f1, 4),
        "tier3_weighted_f1": round(tier3_weighted_f1, 4),
        "shift_acc": round(shift_acc, 4),
        "shift_macro_f1": round(shift_macro_f1, 4),
        "shift_active_macro_f1": round(shift_active_macro_f1, 4),
        "shift_weighted_f1": round(shift_weighted_f1, 4),
        "f1_upgraded": round(f1_up, 4),
        "f1_unchanged": round(f1_unch, 4),
        "f1_downgraded": round(f1_down, 4),
        "r6_n": r6_n,
        "r6_rank_mae": round(r6_mae, 4),
        "r6_rank_exact_acc": round(r6_exact, 4),
        "r6_shift_macro_f1": round(r6_shift_mf1, 4),
    }


def compute_graph_homophily(
    src_idx: list[int],
    dst_idx: list[int],
    labels: np.ndarray,
    valid_mask: np.ndarray,
) -> dict[str, float]:
    """Compute edge homophily and Lim et al. (2021) class-insensitive homophily."""
    both_valid = [(u, v) for u, v in zip(src_idx, dst_idx) if valid_mask[u] and valid_mask[v]]
    if not both_valid:
        return {"n_labeled_edges": 0, "edge_homophily": 0.0, "class_homophily": 0.0}

    same = sum(1 for u, v in both_valid if int(labels[u]) == int(labels[v]))
    edge_h = same / len(both_valid)

    # Lim et al. (2021) adjusted class homophily h_class
    deg_by_cls: dict[int, int] = defaultdict(int)
    same_by_cls: dict[int, int] = defaultdict(int)
    cnt_by_cls: dict[int, int] = defaultdict(int)
    valid_nodes = [i for i in range(len(labels)) if valid_mask[i]]
    for i in valid_nodes:
        cnt_by_cls[int(labels[i])] += 1
    for u, v in both_valid:
        lu, lv = int(labels[u]), int(labels[v])
        deg_by_cls[lu] += 1
        if lu == lv:
            same_by_cls[lu] += 1

    n_valid = len(valid_nodes)
    uniq_cls = sorted(cnt_by_cls.keys())
    if len(uniq_cls) <= 1 or n_valid == 0:
        class_h = 0.0
    else:
        pos_sum = 0.0
        for c in uniq_cls:
            if deg_by_cls[c] == 0:
                continue
            h_k = same_by_cls[c] / deg_by_cls[c]
            p_k = cnt_by_cls[c] / n_valid
            pos_sum += max(0.0, h_k - p_k)
        class_h = pos_sum / (len(uniq_cls) - 1)

    return {
        "n_labeled_edges": len(both_valid),
        "edge_homophily": round(float(edge_h), 4),
        "class_homophily": round(float(class_h), 4),
    }
