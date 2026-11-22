#!/usr/bin/env python3
"""Stage 3: TC-GNN (Text-Classification-informed GNN) Graph Enrichment & Controlled Ablation (v3).

Evaluates directional message passing over the Hadith Sanad / Bukhari transmission network
with tabaqah chronology pruning (chrono_pruned: 42,011 -> 37,364), fused with Stage 2
5-fold OOF AraBERTv02 ESA representations and structured Taqrib metadata.

Key v3 updates (P4.2 & P4.3 Option A):
  - Excludes status_E2 in {missing, suspect_alignment} from train/val/test evaluation.
  - Sets deterministic CUDA flags (CUBLAS_WORKSPACE_CONFIG=:4096:8, use_deterministic_algorithms)
    and logs a 3-run SHA-256 determinism check on G4a (seed=42).
  - Computes 3-tier metrics (1-3 / 4-6 / 7-12) and transmission-network homophily (PO1/PO2).
  - Emits score_G_estimate / score_G_rank / score_G_entropy / source=model_estimate ONLY
    where Tahrir is missing/abstained/suspect; emits G_agrees_with_tahrir & G_residual
    diagnostics for observed Tahrir entries without overwriting scholarly verdicts.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import random
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score, cohen_kappa_score, f1_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler
from torch_geometric.nn import GATv2Conv, GCNConv, SAGEConv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from common.hashing import sha256_text_normalized, to_posix_relative
from experiments.mps_layers import (
    MPSGATv2Conv,
    MPSGCNConv,
    MPSSAGEConv,
    empty_device_cache,
    select_device,
)
from experiments.run_stage2_esa_benchmarks_v3 import load_v3_stage2_inputs
from experiments.v3_common import (
    EXCLUDED_E2_STATUSES,
    SHIFT_LABELS,
    assert_no_tahrir_leakage,
    build_meta_matrix,
    compute_graph_homophily,
    compute_metrics,
    rank_to_0_1,
    rank_to_0_100,
    rank_to_tier3_id,
)

PIPELINE = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline"
MASTER_NODES = PIPELINE / "taqrib_v2_master_dataset_2026-11-20/TAQRIB_V2_MASTER_NODES_8827.csv"
GRAPH_EDGES = PIPELINE / "taqrib_v2_master_dataset_2026-11-20/TAQRIB_V2_GRAPH_EDGES.csv"
LAYERED_WIDE = PIPELINE / "layered_scores_v3_2026-11-21/LAYERED_SCORES_WIDE_V3.csv"
LAYER_RULES = ROOT / "dataset_discovery/target_feasibility/layer_rules_v3.json"
DEFAULT_STAGE2_DIR = ROOT / "results/stage2_esa_benchmarks_v3_2026-11-21"
DEFAULT_OUT_DIR = ROOT / "results/stage3_tc_gnn_benchmarks_v3_2026-11-21"

SEEDS = [42, 43, 44, 45, 46]
BOOTSTRAP_B = 2000


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    if hasattr(torch, "mps") and hasattr(torch.mps, "manual_seed"):
        torch.mps.manual_seed(seed)


def load_graph_and_struct_features(
    node_rows: list[dict[str, str]],
    edge_rows: list[dict[str, str]],
    id_to_idx: dict[str, int],
    score_b_all: np.ndarray,
    tabaqa_all: np.ndarray,
    mode: str,
) -> dict[str, Any]:
    """Build directed edge tensors and leak-free structural node features.

    mode in {'chrono_sanad', 'unpruned_sanad', 'chrono_consolidated'}.
    """
    n_nodes = len(node_rows)
    fwd_src, fwd_dst, fwd_attr = [], [], []
    rev_src, rev_dst, rev_attr = [], [], []

    out_deg = np.zeros(n_nodes, dtype=np.float32)
    in_deg = np.zeros(n_nodes, dtype=np.float32)
    out_wt = np.zeros(n_nodes, dtype=np.float32)
    in_wt = np.zeros(n_nodes, dtype=np.float32)
    max_books = np.zeros(n_nodes, dtype=np.float32)
    buk_out = np.zeros(n_nodes, dtype=np.float32)
    buk_in = np.zeros(n_nodes, dtype=np.float32)
    out_nbrs: dict[int, list[int]] = defaultdict(list)
    in_nbrs: dict[int, list[int]] = defaultdict(list)

    pruned_impossible = 0
    kept = 0

    for e in edge_rows:
        is_sanad = e["sanad_only_edge"] == "1"
        if mode in ("chrono_sanad", "unpruned_sanad") and not is_sanad:
            continue

        u = id_to_idx[e["teacher_entry_id"]]
        v = id_to_idx[e["student_entry_id"]]
        tu = int(tabaqa_all[u])
        tv = int(tabaqa_all[v])
        missing_tab = 1.0 if (tu <= 0 or tv <= 0) else 0.0
        delta_tab = float(tv - tu) if missing_tab == 0.0 else 0.0

        if mode in ("chrono_sanad", "chrono_consolidated") and missing_tab == 0.0 and delta_tab <= -2.0:
            pruned_impossible += 1
            continue

        kept += 1
        buk_w = int(e["bukhari_isnad_weight"])
        su_w = int(e["sanadset_unique_weight"])
        sm_w = int(e["sanadset_method1_disambig_weight"])
        sdb = int(e["sanadset_distinct_books"])
        tot_w = int(e["total_consolidated_weight"])
        edge_w = float(su_w + sm_w + buk_w) if mode in ("chrono_sanad", "unpruned_sanad") else float(tot_w)

        out_deg[u] += 1.0
        in_deg[v] += 1.0
        out_wt[u] += edge_w
        in_wt[v] += edge_w
        if sdb > max_books[u]:
            max_books[u] = float(sdb)
        if sdb > max_books[v]:
            max_books[v] = float(sdb)
        if buk_w > 0:
            buk_out[u] += 1.0
            buk_in[v] += 1.0
        out_nbrs[u].append(v)
        in_nbrs[v].append(u)

        is_peer = 1.0 if (missing_tab == 0.0 and delta_tab == 0.0) else 0.0
        clipped_delta = max(-5.0, min(10.0, delta_tab)) / 10.0
        feat = [
            math.log1p(edge_w),
            math.log1p(float(sdb)),
            clipped_delta,
            is_peer,
            missing_tab,
        ]
        fwd_src.append(u)
        fwd_dst.append(v)
        fwd_attr.append(feat)
        rev_src.append(v)
        rev_dst.append(u)
        rev_attr.append(feat)

    struct = np.zeros((n_nodes, 17), dtype=np.float32)
    struct_names = [
        "sanad_log_out_deg", "sanad_log_in_deg", "sanad_log_tot_deg",
        "sanad_log_out_wt", "sanad_log_in_wt", "sanad_log_max_books",
        "sanad_log_buk_out", "sanad_log_buk_in", "sanad_is_isolated", "sanad_out_ge2",
        "sanad_nbr_out_ranked_log", "sanad_nbr_out_mean_score_B",
        "sanad_nbr_out_thiqah_log", "sanad_nbr_out_thiqah_ratio",
        "sanad_nbr_in_ranked_log", "sanad_nbr_in_mean_score_B",
        "sanad_nbr_in_thiqah_ratio",
    ]
    for i in range(n_nodes):
        tot_d = out_deg[i] + in_deg[i]
        o_ranks = [float(score_b_all[j]) for j in out_nbrs[i] if score_b_all[j] > 0]
        i_ranks = [float(score_b_all[j]) for j in in_nbrs[i] if score_b_all[j] > 0]
        o_thiq = sum(1 for r in o_ranks if r <= 3)
        i_thiq = sum(1 for r in i_ranks if r <= 3)

        struct[i, 0] = math.log1p(out_deg[i])
        struct[i, 1] = math.log1p(in_deg[i])
        struct[i, 2] = math.log1p(tot_d)
        struct[i, 3] = math.log1p(out_wt[i])
        struct[i, 4] = math.log1p(in_wt[i])
        struct[i, 5] = math.log1p(max_books[i])
        struct[i, 6] = math.log1p(buk_out[i])
        struct[i, 7] = math.log1p(buk_in[i])
        struct[i, 8] = 1.0 if tot_d == 0.0 else 0.0
        struct[i, 9] = 1.0 if out_deg[i] >= 2.0 else 0.0
        struct[i, 10] = math.log1p(float(len(o_ranks)))
        struct[i, 11] = (sum(o_ranks) / len(o_ranks)) if o_ranks else 0.0
        struct[i, 12] = math.log1p(float(o_thiq))
        struct[i, 13] = (o_thiq / len(o_ranks)) if o_ranks else 0.0
        struct[i, 14] = math.log1p(float(len(i_ranks)))
        struct[i, 15] = (sum(i_ranks) / len(i_ranks)) if i_ranks else 0.0
        struct[i, 16] = (i_thiq / len(i_ranks)) if i_ranks else 0.0

    edge_index_fwd = torch.tensor([fwd_src, fwd_dst], dtype=torch.long)
    edge_attr_fwd = torch.tensor(fwd_attr, dtype=torch.float32)
    edge_index_rev = torch.tensor([rev_src, rev_dst], dtype=torch.long)
    edge_attr_rev = torch.tensor(rev_attr, dtype=torch.float32)

    undir_pairs = set(zip(fwd_src, fwd_dst)) | set(zip(rev_src, rev_dst))
    u_src = [p[0] for p in undir_pairs]
    u_dst = [p[1] for p in undir_pairs]
    edge_index_undir = torch.tensor([u_src, u_dst], dtype=torch.long)

    return {
        "kept_edges": kept,
        "pruned_impossible": pruned_impossible,
        "fwd_src": fwd_src,
        "fwd_dst": fwd_dst,
        "out_deg": out_deg,
        "in_deg": in_deg,
        "is_isolated": (out_deg + in_deg) == 0,
        "struct": struct,
        "struct_names": struct_names,
        "edge_index_fwd": edge_index_fwd,
        "edge_attr_fwd": edge_attr_fwd,
        "edge_index_rev": edge_index_rev,
        "edge_attr_rev": edge_attr_rev,
        "edge_index_undir": edge_index_undir,
    }


def build_semantic_knn_view(cls_pca: np.ndarray, k: int = 8) -> tuple[torch.Tensor, torch.Tensor]:
    z = torch.tensor(cls_pca, dtype=torch.float32)
    z = F.normalize(z, p=2, dim=-1)
    sim = z @ z.T
    sim.fill_diagonal_(-1e9)
    vals, idxs = torch.topk(sim, k=k, dim=1)
    n = z.size(0)
    dst = torch.arange(n, dtype=torch.long).unsqueeze(1).expand(n, k).reshape(-1)
    src = idxs.reshape(-1)
    return torch.stack([src, dst], dim=0), vals.reshape(-1, 1)


class DualHeadMLP(nn.Module):
    def __init__(self, in_dim: int, hid: int = 192, dropout: float = 0.3) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, hid),
            nn.LayerNorm(hid),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hid, hid),
            nn.LayerNorm(hid),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        self.rank_head = nn.Linear(hid, 12)
        self.shift_head = nn.Linear(hid, 3)

    def forward(self, x: torch.Tensor, *args: Any) -> tuple[torch.Tensor, torch.Tensor, dict[str, torch.Tensor]]:
        h = self.net(x)
        return self.rank_head(h), self.shift_head(h), {}


def _make_gatv2(
    in_channels: int,
    out_channels: int,
    heads: int,
    edge_dim: int | None,
    dropout: float,
    backend: str,
) -> nn.Module:
    if backend == "mps_native":
        return MPSGATv2Conv(
            in_channels,
            out_channels,
            heads=heads,
            edge_dim=edge_dim,
            dropout=dropout,
            add_self_loops=False,
        )
    return GATv2Conv(
        in_channels,
        out_channels,
        heads=heads,
        edge_dim=edge_dim,
        dropout=dropout,
        add_self_loops=False,
    )


class UndirectedGNN(nn.Module):
    def __init__(self, in_dim: int, conv_type: str, hid: int = 128, dropout: float = 0.3, backend: str = "pyg") -> None:
        super().__init__()
        self.in_proj = nn.Sequential(nn.Linear(in_dim, hid), nn.LayerNorm(hid), nn.GELU(), nn.Dropout(dropout))
        if conv_type == "gcn":
            cls = MPSGCNConv if backend == "mps_native" else GCNConv
            self.conv1, self.conv2 = cls(hid, hid), cls(hid, hid)
        elif conv_type == "sage":
            cls = MPSSAGEConv if backend == "mps_native" else SAGEConv
            self.conv1, self.conv2 = cls(hid, hid), cls(hid, hid)
        elif conv_type == "gatv2":
            self.conv1 = _make_gatv2(hid, hid // 4, heads=4, edge_dim=None, dropout=dropout, backend=backend)
            self.conv2 = _make_gatv2(hid, hid // 4, heads=4, edge_dim=None, dropout=dropout, backend=backend)
        else:
            raise ValueError(conv_type)
        self.norm1, self.norm2 = nn.LayerNorm(hid), nn.LayerNorm(hid)
        self.drop = nn.Dropout(dropout)
        self.trunk = nn.Sequential(nn.Linear(hid * 2, hid), nn.LayerNorm(hid), nn.GELU(), nn.Dropout(dropout))
        self.rank_head, self.shift_head = nn.Linear(hid, 12), nn.Linear(hid, 3)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, dict[str, torch.Tensor]]:
        h0 = self.in_proj(x)
        h1 = self.norm1(h0 + self.drop(F.gelu(self.conv1(h0, edge_index))))
        h2 = self.norm2(h1 + self.drop(F.gelu(self.conv2(h1, edge_index))))
        h = self.trunk(torch.cat([h0, h2], dim=-1))
        return self.rank_head(h), self.shift_head(h), {}


class DirectedTCGNN(nn.Module):
    """Residual-Gated Directional Edge-Conditioned GATv2 (Forward + Reverse + optional kNN view)."""

    def __init__(
        self,
        in_dim: int,
        edge_dim: int = 5,
        hid: int = 128,
        dropout: float = 0.3,
        use_knn: bool = False,
        backend: str = "pyg",
    ) -> None:
        super().__init__()
        self.use_knn = use_knn
        self.in_proj = nn.Sequential(nn.Linear(in_dim, hid), nn.LayerNorm(hid), nn.GELU(), nn.Dropout(dropout))
        self.fwd1 = _make_gatv2(hid, hid // 4, heads=4, edge_dim=edge_dim, dropout=dropout, backend=backend)
        self.rev1 = _make_gatv2(hid, hid // 4, heads=4, edge_dim=edge_dim, dropout=dropout, backend=backend)
        self.fwd2 = _make_gatv2(hid, hid // 4, heads=4, edge_dim=edge_dim, dropout=dropout, backend=backend)
        self.rev2 = _make_gatv2(hid, hid // 4, heads=4, edge_dim=edge_dim, dropout=dropout, backend=backend)

        self.gate_fwd1, self.gate_rev1 = nn.Linear(hid * 2, hid), nn.Linear(hid * 2, hid)
        self.gate_fwd2, self.gate_rev2 = nn.Linear(hid * 2, hid), nn.Linear(hid * 2, hid)

        if use_knn:
            self.knn1 = _make_gatv2(hid, hid // 4, heads=4, edge_dim=1, dropout=dropout, backend=backend)
            self.knn2 = _make_gatv2(hid, hid // 4, heads=4, edge_dim=1, dropout=dropout, backend=backend)
            self.gate_knn1, self.gate_knn2 = nn.Linear(hid * 2, hid), nn.Linear(hid * 2, hid)

        self.norm1, self.norm2 = nn.LayerNorm(hid), nn.LayerNorm(hid)
        self.drop = nn.Dropout(dropout)
        self.trunk = nn.Sequential(nn.Linear(hid * 2, hid), nn.LayerNorm(hid), nn.GELU(), nn.Dropout(dropout))
        self.rank_head, self.shift_head = nn.Linear(hid, 12), nn.Linear(hid, 3)

    def forward(
        self,
        x: torch.Tensor,
        ei_fwd: torch.Tensor,
        ea_fwd: torch.Tensor,
        ei_rev: torch.Tensor,
        ea_rev: torch.Tensor,
        ei_knn: torch.Tensor | None = None,
        ea_knn: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor, dict[str, torch.Tensor]]:
        h0 = self.in_proj(x)
        f1 = F.gelu(self.fwd1(h0, ei_fwd, ea_fwd))
        r1 = F.gelu(self.rev1(h0, ei_rev, ea_rev))
        gf1 = torch.sigmoid(self.gate_fwd1(torch.cat([h0, f1], dim=-1)))
        gr1 = torch.sigmoid(self.gate_rev1(torch.cat([h0, r1], dim=-1)))
        upd1 = gf1 * f1 + gr1 * r1
        if self.use_knn and ei_knn is not None and ea_knn is not None:
            k1 = F.gelu(self.knn1(h0, ei_knn, ea_knn))
            gk1 = torch.sigmoid(self.gate_knn1(torch.cat([h0, k1], dim=-1)))
            upd1 = upd1 + gk1 * k1
        h1 = self.norm1(h0 + self.drop(upd1))

        f2 = F.gelu(self.fwd2(h1, ei_fwd, ea_fwd))
        r2 = F.gelu(self.rev2(h1, ei_rev, ea_rev))
        gf2 = torch.sigmoid(self.gate_fwd2(torch.cat([h1, f2], dim=-1)))
        gr2 = torch.sigmoid(self.gate_rev2(torch.cat([h1, r2], dim=-1)))
        upd2 = gf2 * f2 + gr2 * r2
        gates = {"g_fwd": gf2.mean(dim=-1), "g_rev": gr2.mean(dim=-1)}
        if self.use_knn and ei_knn is not None and ea_knn is not None:
            k2 = F.gelu(self.knn2(h1, ei_knn, ea_knn))
            gk2 = torch.sigmoid(self.gate_knn2(torch.cat([h1, k2], dim=-1)))
            upd2 = upd2 + gk2 * k2
            gates["g_knn"] = gk2.mean(dim=-1)
        h2 = self.norm2(h1 + self.drop(upd2))

        h = self.trunk(torch.cat([h0, h2], dim=-1))
        return self.rank_head(h), self.shift_head(h), gates


def train_transductive_model(
    model_fn: Any,
    forward_args: tuple[torch.Tensor, ...],
    idx_train: np.ndarray,
    idx_val: np.ndarray,
    y_rank_all: np.ndarray,
    y_shift_all: np.ndarray,
    is_maqbul_all: np.ndarray,
    seed: int,
    max_epochs: int = 200,
    patience: int = 30,
) -> dict[str, Any]:
    set_seed(seed)
    device = forward_args[0].device
    model = model_fn().to(device)

    tr_t = torch.tensor(idx_train, dtype=torch.long, device=device)
    yr_tr = torch.tensor(y_rank_all[idx_train] - 1, dtype=torch.long, device=device)
    ys_tr = torch.tensor(y_shift_all[idx_train], dtype=torch.long, device=device)

    cnts = np.bincount(y_shift_all[idx_train], minlength=3).astype(np.float32)
    sw = np.sqrt(cnts.sum() / (3.0 * np.maximum(cnts, 1.0)))
    sw = torch.tensor(sw / sw.mean(), dtype=torch.float32, device=device)

    ce_rank = nn.CrossEntropyLoss()
    ce_shift = nn.CrossEntropyLoss(weight=sw)
    smooth_l1 = nn.SmoothL1Loss()
    rank_vals = torch.arange(1, 13, dtype=torch.float32, device=device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=1.5e-3, weight_decay=2e-2)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=max_epochs, eta_min=1e-4)

    best_score = -1e9
    best_state = None
    no_imp = 0

    for ep in range(1, max_epochs + 1):
        model.train()
        optimizer.zero_grad()
        r_log, s_log, _ = model(*forward_args)
        r_probs_tr = torch.softmax(r_log[tr_t], dim=-1)
        r_exp_tr = (r_probs_tr * rank_vals).sum(dim=-1)
        loss = (
            ce_rank(r_log[tr_t], yr_tr)
            + 0.35 * smooth_l1(r_exp_tr, (yr_tr + 1).float())
            + ce_shift(s_log[tr_t], ys_tr)
        )
        assert not torch.isnan(loss), f"NaN loss at epoch {ep}"
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 2.0)
        optimizer.step()
        scheduler.step()

        model.eval()
        with torch.no_grad():
            r_log, s_log, _ = model(*forward_args)
            r_probs = torch.softmax(r_log, dim=-1).cpu().numpy()
            s_probs = torch.softmax(s_log, dim=-1).cpu().numpy()
        r_exp = (r_probs * np.arange(1, 13, dtype=np.float32)).sum(axis=1)
        vm = compute_metrics(
            y_rank_all[idx_val],
            y_shift_all[idx_val],
            r_exp[idx_val],
            s_probs[idx_val].argmax(axis=1),
            is_maqbul_all[idx_val],
        )
        comp = vm["shift_macro_f1"] - 0.15 * vm["rank_mae"]
        if comp > best_score:
            best_score = comp
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            no_imp = 0
        else:
            no_imp += 1
            if no_imp >= patience:
                break

    assert best_state is not None
    model.load_state_dict({k: v.to(device) for k, v in best_state.items()})
    model.eval()
    with torch.no_grad():
        r_log, s_log, gates = model(*forward_args)
        r_probs = torch.softmax(r_log, dim=-1).cpu().numpy()
        s_probs = torch.softmax(s_log, dim=-1).cpu().numpy()
        gates_np = {k: v.cpu().numpy() for k, v in gates.items()}
    r_exp = (r_probs * np.arange(1, 13, dtype=np.float32)).sum(axis=1)
    del model
    empty_device_cache(device)
    return {"rank_probs": r_probs, "rank_exp": r_exp, "shift_probs": s_probs, "gates": gates_np}


def paired_bootstrap_vs_ref(
    y_rank: np.ndarray,
    y_shift: np.ndarray,
    is_maqbul: np.ndarray,
    ref_rc: np.ndarray,
    ref_sp: np.ndarray,
    m_rc: np.ndarray,
    m_sp: np.ndarray,
    n_boot: int = BOOTSTRAP_B,
    seed: int = 42,
) -> list[dict[str, Any]]:
    rng = np.random.default_rng(seed)
    n = len(y_rank)
    ref_disc = np.clip(np.rint(ref_rc), 1, 12).astype(int)
    m_disc = np.clip(np.rint(m_rc), 1, 12).astype(int)
    y_bin = (y_rank <= 6).astype(int)
    ref_bin = (ref_disc <= 6).astype(int)
    m_bin = (m_disc <= 6).astype(int)
    y_t3 = np.array([rank_to_tier3_id(int(r)) for r in y_rank], dtype=int)
    ref_t3 = np.array([rank_to_tier3_id(int(r)) for r in ref_disc], dtype=int)
    m_t3 = np.array([rank_to_tier3_id(int(r)) for r in m_disc], dtype=int)
    r6_mask = is_maqbul.astype(bool)

    diffs: dict[str, list[float]] = defaultdict(list)
    obs: dict[str, tuple[float, float]] = {
        "rank_mae": (float(mean_absolute_error(y_rank, ref_rc)), float(mean_absolute_error(y_rank, m_rc))),
        "rank_qwk": (float(cohen_kappa_score(y_rank, ref_disc, weights="quadratic")), float(cohen_kappa_score(y_rank, m_disc, weights="quadratic"))),
        "bin_acc": (float(accuracy_score(y_bin, ref_bin)), float(accuracy_score(y_bin, m_bin))),
        "tier3_macro_f1": (
            float(f1_score(y_t3, ref_t3, labels=[0, 1, 2], average="macro", zero_division=0)),
            float(f1_score(y_t3, m_t3, labels=[0, 1, 2], average="macro", zero_division=0)),
        ),
        "shift_macro_f1": (
            float(f1_score(y_shift, ref_sp, labels=[0, 1, 2], average="macro", zero_division=0)),
            float(f1_score(y_shift, m_sp, labels=[0, 1, 2], average="macro", zero_division=0)),
        ),
        "r6_rank_mae": (float(mean_absolute_error(y_rank[r6_mask], ref_rc[r6_mask])), float(mean_absolute_error(y_rank[r6_mask], m_rc[r6_mask]))),
    }

    for _ in range(n_boot):
        b = rng.integers(0, n, size=n)
        diffs["rank_mae"].append(float(mean_absolute_error(y_rank[b], m_rc[b]) - mean_absolute_error(y_rank[b], ref_rc[b])))
        diffs["rank_qwk"].append(float(cohen_kappa_score(y_rank[b], m_disc[b], weights="quadratic") - cohen_kappa_score(y_rank[b], ref_disc[b], weights="quadratic")))
        diffs["bin_acc"].append(float(accuracy_score(y_bin[b], m_bin[b]) - accuracy_score(y_bin[b], ref_bin[b])))
        diffs["tier3_macro_f1"].append(
            float(f1_score(y_t3[b], m_t3[b], labels=[0, 1, 2], average="macro", zero_division=0) - f1_score(y_t3[b], ref_t3[b], labels=[0, 1, 2], average="macro", zero_division=0))
        )
        diffs["shift_macro_f1"].append(
            float(f1_score(y_shift[b], m_sp[b], labels=[0, 1, 2], average="macro", zero_division=0) - f1_score(y_shift[b], ref_sp[b], labels=[0, 1, 2], average="macro", zero_division=0))
        )
        b_r6 = b[r6_mask[b]]
        if len(b_r6) > 0:
            diffs["r6_rank_mae"].append(float(mean_absolute_error(y_rank[b_r6], m_rc[b_r6]) - mean_absolute_error(y_rank[b_r6], ref_rc[b_r6])))

    rows = []
    for metric, (v0, v1) in obs.items():
        arr = np.array(diffs[metric])
        ci_lo, ci_hi = np.percentile(arr, [2.5, 97.5])
        p_pos, p_neg = float(np.mean(arr >= 0.0)), float(np.mean(arr <= 0.0))
        p_val = min(1.0, 2.0 * min(p_pos, p_neg))
        rows.append(
            {
                "metric": metric,
                "ref_val": round(v0, 4),
                "model_ens_val": round(v1, 4),
                "delta_vs_ref": round(v1 - v0, 4),
                "ci95_low": round(float(ci_lo), 4),
                "ci95_high": round(float(ci_hi), 4),
                "p_value_2sided": round(p_val, 4),
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Stage 3 TC-GNN Benchmarks (v3).")
    parser.add_argument("--stage2-dir", type=Path, default=DEFAULT_STAGE2_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--device", type=str, default="auto", choices=["auto", "mps", "cuda", "cpu"])
    parser.add_argument("--backend", type=str, default="auto", choices=["auto", "mps_native", "pyg"])
    parser.add_argument("--max-epochs", type=int, default=200)
    parser.add_argument("--patience", type=int, default=30)
    parser.add_argument("--resume", action="store_true", help="Resume from per-model 5-seed checkpoints inside out-dir.")
    args = parser.parse_args()

    t0 = time.time()
    torch.use_deterministic_algorithms(True, warn_only=True)
    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    ckpt_dir = out_dir / "checkpoints"
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    device = select_device(args.device)
    backend = args.backend if args.backend != "auto" else ("mps_native" if device.type == "mps" else "pyg")
    print(f"Stage 3 v3 device={device.type}, backend={backend}, max_epochs={args.max_epochs}")

    stage2_oof = args.stage2_dir / "STAGE2_OOF_ESA_FEATURES_8827_V3.csv"
    if not stage2_oof.is_file():
        raise FileNotFoundError(f"Missing Stage 2 v3 OOF file: {stage2_oof}")

    with GRAPH_EDGES.open(encoding="utf-8-sig") as f:
        edge_rows = list(csv.DictReader(f))
    with stage2_oof.open(encoding="utf-8-sig") as f:
        oof_rows = list(csv.DictReader(f))

    data = load_v3_stage2_inputs()
    node_rows = data["all_rows"]
    layered_by_id = data["layered_by_id"]
    statuses_e2 = data["statuses_e2"]
    idx_train = data["idx_train"]
    idx_val = data["idx_val"]
    idx_test = data["idx_test"]
    y_rank_all = data["y_rank_all"]
    score_b_all = data["score_b_all"]
    y_shift_all = data["y_shift_all"]
    is_maqbul_all = data["is_maqbul_all"]

    assert len(node_rows) == 8827 and len(oof_rows) == 8827
    assert [r["entry_id"] for r in node_rows] == [r["entry_id"] for r in oof_rows]
    assert all(statuses_e2[i] not in EXCLUDED_E2_STATUSES for i in [*idx_train, *idx_val, *idx_test])

    id_to_idx = {r["entry_id"]: i for i, r in enumerate(node_rows)}
    tabaqa_all = np.array([int(r["tabaqa_1_to_12"]) if r["tabaqa_1_to_12"] else -1 for r in node_rows])

    X_meta, meta_names = build_meta_matrix(node_rows)
    sem_cols = [c for c in oof_rows[0].keys() if c not in ("entry_id", "split", "in_core_cohort_7258")]
    X_sem = np.array([[float(r[c]) for c in sem_cols] for r in oof_rows], dtype=np.float32)
    cls_pca = np.array([[float(r[f"arabert_cls_pca_{d:02d}"]) for d in range(32)] for r in oof_rows], dtype=np.float32)

    g_chrono_sanad = load_graph_and_struct_features(node_rows, edge_rows, id_to_idx, score_b_all, tabaqa_all, "chrono_sanad")
    g_unpruned_sanad = load_graph_and_struct_features(node_rows, edge_rows, id_to_idx, score_b_all, tabaqa_all, "unpruned_sanad")
    g_chrono_consol = load_graph_and_struct_features(node_rows, edge_rows, id_to_idx, score_b_all, tabaqa_all, "chrono_consolidated")
    assert g_chrono_sanad["pruned_impossible"] == 4647 and g_chrono_sanad["kept_edges"] == 37364

    # Zero-Tahrir feature assertion across all feature names
    all_feature_names = meta_names + sem_cols + g_chrono_sanad["struct_names"]
    assert_no_tahrir_leakage(all_feature_names)

    # Graph homophily diagnostics (PO2)
    valid_e2_mask = np.array([y_rank_all[i] > 0 and statuses_e2[i] not in EXCLUDED_E2_STATUSES for i in range(len(node_rows))])
    y_tier3_all = np.array([rank_to_tier3_id(int(r)) if r > 0 else -1 for r in y_rank_all])
    homophily = {
        "chrono_sanad_12rank": compute_graph_homophily(g_chrono_sanad["fwd_src"], g_chrono_sanad["fwd_dst"], y_rank_all, valid_e2_mask),
        "chrono_sanad_3tier": compute_graph_homophily(g_chrono_sanad["fwd_src"], g_chrono_sanad["fwd_dst"], y_tier3_all, valid_e2_mask),
        "unpruned_sanad_12rank": compute_graph_homophily(g_unpruned_sanad["fwd_src"], g_unpruned_sanad["fwd_dst"], y_rank_all, valid_e2_mask),
        "unpruned_sanad_3tier": compute_graph_homophily(g_unpruned_sanad["fwd_src"], g_unpruned_sanad["fwd_dst"], y_tier3_all, valid_e2_mask),
    }

    ei_knn, ea_knn = build_semantic_knn_view(cls_pca, k=8)

    def std_feats(arr: np.ndarray) -> torch.Tensor:
        sc = StandardScaler()
        sc.fit(arr[idx_train])
        return torch.tensor(sc.transform(arr).astype(np.float32), device=device)

    tab_sig_idx = [i for i, n in enumerate(meta_names) if n == "tabaqa_num" or n.startswith("subtier_") or n.startswith("sigil_")]
    X_g1_t = std_feats(np.hstack([X_meta[:, tab_sig_idx], g_chrono_sanad["struct"]]))
    X_full_sanad_np = np.hstack([X_meta, X_sem, g_chrono_sanad["struct"]])
    X_sanad_t = std_feats(X_full_sanad_np)
    X_unpruned_t = std_feats(np.hstack([X_meta, X_sem, g_unpruned_sanad["struct"]]))
    X_consol_t = std_feats(np.hstack([X_meta, X_sem, g_chrono_consol["struct"]]))

    for g in (g_chrono_sanad, g_unpruned_sanad, g_chrono_consol):
        for k in ("edge_index_fwd", "edge_attr_fwd", "edge_index_rev", "edge_attr_rev", "edge_index_undir"):
            g[k] = g[k].to(device)
    ei_knn, ea_knn = ei_knn.to(device), ea_knn.to(device)

    # 3-run determinism check on primary G4a (seed=42)
    det_hashes: list[str] = []
    det_rank_exps: list[np.ndarray] = []
    g4a_args = (X_sanad_t, g_chrono_sanad["edge_index_fwd"], g_chrono_sanad["edge_attr_fwd"], g_chrono_sanad["edge_index_rev"], g_chrono_sanad["edge_attr_rev"])
    for _run in range(3):
        out_det = train_transductive_model(
            lambda: DirectedTCGNN(X_sanad_t.size(1), edge_dim=5, hid=128, dropout=0.3, use_knn=False, backend=backend),
            g4a_args, idx_train, idx_val, y_rank_all, y_shift_all, is_maqbul_all, seed=42,
            max_epochs=args.max_epochs, patience=args.patience,
        )
        det_rank_exps.append(out_det["rank_exp"])
        det_hashes.append(hashlib.sha256(out_det["rank_exp"].tobytes()).hexdigest())
    max_det_diff = max(
        float(np.max(np.abs(det_rank_exps[0] - det_rank_exps[1]))),
        float(np.max(np.abs(det_rank_exps[0] - det_rank_exps[2]))),
    )
    determinism_check = {
        "device": device.type,
        "backend": backend,
        "seed": 42,
        "run_sha256": det_hashes,
        "all_3_bit_exact": len(set(det_hashes)) == 1,
        "max_abs_rank_exp_diff": round(max_det_diff, 8),
    }

    comp_rows: list[dict[str, Any]] = []
    ens_preds_all: dict[str, dict[str, np.ndarray]] = {}
    gate_logs: dict[str, dict[str, float]] = {}

    def record_5seed(name: str, family: str, seed_vm: list[dict[str, float]], seed_tm: list[dict[str, float]], ens_r_probs: np.ndarray, ens_s_probs: np.ndarray) -> None:
        ens_r_exp = (ens_r_probs * np.arange(1, 13, dtype=np.float32)).sum(axis=1)
        ens_preds_all[name] = {"rank_probs": ens_r_probs, "rank_exp": ens_r_exp, "shift_probs": ens_s_probs}
        ens_test_m = compute_metrics(y_rank_all[idx_test], y_shift_all[idx_test], ens_r_exp[idx_test], ens_s_probs[idx_test].argmax(axis=1), is_maqbul_all[idx_test])
        for sp_name, m_list in [("val", seed_vm), ("test", seed_tm)]:
            row_d: dict[str, Any] = {"model": name, "family": family, "split": sp_name, "n_seeds": len(m_list)}
            for k in m_list[0].keys():
                if k == "r6_n":
                    row_d[k] = m_list[0][k]
                    continue
                vals = np.array([m[k] for m in m_list], dtype=float)
                row_d[f"{k}_mean"] = round(float(vals.mean()), 4)
                row_d[f"{k}_std"] = round(float(vals.std()), 4)
            if sp_name == "test":
                for ek in ("rank_mae", "rank_qwk", "rank_exact_acc", "bin_acc", "bin_weighted_f1", "tier3_macro_f1", "shift_macro_f1", "shift_active_macro_f1", "r6_rank_mae"):
                    row_d[f"ens_{ek}"] = ens_test_m[ek]
            comp_rows.append(row_d)
        print(f"[{name}] TEST 5-Seed Mean | MAE={np.mean([m['rank_mae'] for m in seed_tm]):.4f} Tier3MF1={np.mean([m['tier3_macro_f1'] for m in seed_tm]):.4f} ShiftMF1={np.mean([m['shift_macro_f1'] for m in seed_tm]):.4f}")

    # G0 Stage 2 Anchor
    g0_rank_exp = np.array([float(r["arabert_oof_rank_exp"]) for r in oof_rows], dtype=np.float32)
    g0_sprobs = np.array([[float(r["arabert_p_up"]), float(r["arabert_p_unch"]), float(r["arabert_p_down"])] for r in oof_rows], dtype=np.float32)
    g0_rprobs = np.array([[float(r[f"arabert_p_r{k}"]) for k in range(1, 13)] for r in oof_rows], dtype=np.float32)
    g0_vm = compute_metrics(y_rank_all[idx_val], y_shift_all[idx_val], g0_rank_exp[idx_val], g0_sprobs[idx_val].argmax(axis=1), is_maqbul_all[idx_val])
    g0_tm = compute_metrics(y_rank_all[idx_test], y_shift_all[idx_test], g0_rank_exp[idx_test], g0_sprobs[idx_test].argmax(axis=1), is_maqbul_all[idx_test])
    record_5seed("G0_Stage2_AraBERT_NoGraph", "stage2_esa_anchor", [g0_vm], [g0_tm], g0_rprobs, g0_sprobs)

    # G2a HistGBDT (5-seed)
    g2a_vm, g2a_tm = [], []
    g2a_r_sum = np.zeros((len(node_rows), 12), dtype=np.float32)
    g2a_s_sum = np.zeros((len(node_rows), 3), dtype=np.float32)
    for sd in SEEDS:
        reg = HistGradientBoostingClassifier(max_iter=250, learning_rate=0.05, random_state=sd).fit(X_full_sanad_np[idx_train], y_rank_all[idx_train] - 1)
        cls = HistGradientBoostingClassifier(max_iter=250, learning_rate=0.05, class_weight="balanced", random_state=sd).fit(X_full_sanad_np[idx_train], y_shift_all[idx_train])
        rp, sp = reg.predict_proba(X_full_sanad_np), cls.predict_proba(X_full_sanad_np)
        rexp = (rp * np.arange(1, 13, dtype=np.float32)).sum(axis=1)
        g2a_r_sum += rp / len(SEEDS)
        g2a_s_sum += sp / len(SEEDS)
        g2a_vm.append(compute_metrics(y_rank_all[idx_val], y_shift_all[idx_val], rexp[idx_val], sp[idx_val].argmax(axis=1), is_maqbul_all[idx_val]))
        g2a_tm.append(compute_metrics(y_rank_all[idx_test], y_shift_all[idx_test], rexp[idx_test], sp[idx_test].argmax(axis=1), is_maqbul_all[idx_test]))
    record_5seed("G2a_Sem_Plus_SanadStruct_HistGBDT", "tabular_with_struct", g2a_vm, g2a_tm, g2a_r_sum, g2a_s_sum)

    def run_pyg_5seed(name: str, family: str, model_fn: Any, fwd_args: tuple[torch.Tensor, ...]) -> None:
        ckpt_path = ckpt_dir / f"{name}.npz"
        if args.resume and ckpt_path.exists():
            z = np.load(ckpt_path, allow_pickle=True)
            r_sum = z["r_sum"]
            s_sum = z["s_sum"]
            vm_list = list(z["vm_list"])
            tm_list = list(z["tm_list"])
            glog = z["gate_log"].item() if "gate_log" in z else {}
            if glog:
                gate_logs[name] = glog
            record_5seed(name, family, vm_list, tm_list, r_sum, s_sum)
            return

        vm_list, tm_list = [], []
        r_sum = np.zeros((len(node_rows), 12), dtype=np.float32)
        s_sum = np.zeros((len(node_rows), 3), dtype=np.float32)
        gf_c, gf_i, gr_c, gr_i, gk_a = [], [], [], [], []
        conn_mask, iso_mask = ~g_chrono_sanad["is_isolated"], g_chrono_sanad["is_isolated"]
        for sd in SEEDS:
            out = train_transductive_model(
                model_fn,
                fwd_args,
                idx_train,
                idx_val,
                y_rank_all,
                y_shift_all,
                is_maqbul_all,
                seed=sd,
                max_epochs=args.max_epochs,
                patience=args.patience,
            )
            rp, rexp, sp = out["rank_probs"], out["rank_exp"], out["shift_probs"]
            r_sum += rp / len(SEEDS)
            s_sum += sp / len(SEEDS)
            vm_list.append(compute_metrics(y_rank_all[idx_val], y_shift_all[idx_val], rexp[idx_val], sp[idx_val].argmax(axis=1), is_maqbul_all[idx_val]))
            tm_list.append(compute_metrics(y_rank_all[idx_test], y_shift_all[idx_test], rexp[idx_test], sp[idx_test].argmax(axis=1), is_maqbul_all[idx_test]))
            if "g_fwd" in out["gates"]:
                gf_c.append(float(out["gates"]["g_fwd"][conn_mask].mean()))
                gf_i.append(float(out["gates"]["g_fwd"][iso_mask].mean()))
                gr_c.append(float(out["gates"]["g_rev"][conn_mask].mean()))
                gr_i.append(float(out["gates"]["g_rev"][iso_mask].mean()))
            if "g_knn" in out["gates"]:
                gk_a.append(float(out["gates"]["g_knn"].mean()))
        if gf_c:
            gate_logs[name] = {
                "g_fwd_connected": round(float(np.mean(gf_c)), 4),
                "g_fwd_isolated": round(float(np.mean(gf_i)), 4),
                "g_rev_connected": round(float(np.mean(gr_c)), 4),
                "g_rev_isolated": round(float(np.mean(gr_i)), 4),
                **({"g_knn_all": round(float(np.mean(gk_a)), 4)} if gk_a else {}),
            }
        np.savez(
            ckpt_path,
            r_sum=r_sum,
            s_sum=s_sum,
            vm_list=np.array(vm_list, dtype=object),
            tm_list=np.array(tm_list, dtype=object),
            gate_log=np.array(gate_logs.get(name, {}), dtype=object),
        )
        record_5seed(name, family, vm_list, tm_list, r_sum, s_sum)

    run_pyg_5seed(
        "G1_GraphOnly_NoText", "graph_only",
        lambda: DirectedTCGNN(X_g1_t.size(1), edge_dim=5, hid=128, dropout=0.3, use_knn=False, backend=backend),
        (X_g1_t, g_chrono_sanad["edge_index_fwd"], g_chrono_sanad["edge_attr_fwd"], g_chrono_sanad["edge_index_rev"], g_chrono_sanad["edge_attr_rev"]),
    )
    run_pyg_5seed("G2b_Sem_Plus_SanadStruct_MLP", "tabular_with_struct", lambda: DualHeadMLP(X_sanad_t.size(1)), (X_sanad_t,))
    run_pyg_5seed("G3a_Undirected_GCN", "undirected_gnn", lambda: UndirectedGNN(X_sanad_t.size(1), "gcn", backend=backend), (X_sanad_t, g_chrono_sanad["edge_index_undir"]))
    run_pyg_5seed("G3b_Undirected_GraphSAGE", "undirected_gnn", lambda: UndirectedGNN(X_sanad_t.size(1), "sage", backend=backend), (X_sanad_t, g_chrono_sanad["edge_index_undir"]))
    run_pyg_5seed("G3c_Undirected_GATv2", "undirected_gnn", lambda: UndirectedGNN(X_sanad_t.size(1), "gatv2", backend=backend), (X_sanad_t, g_chrono_sanad["edge_index_undir"]))
    run_pyg_5seed("G4a_Directed_TC_GNN_Sanad", "directed_tc_gnn_primary", lambda: DirectedTCGNN(X_sanad_t.size(1), edge_dim=5, hid=128, dropout=0.3, use_knn=False, backend=backend), g4a_args)
    run_pyg_5seed(
        "G4b_Directed_TC_GNN_UnprunedSanad", "ablation_unpruned_edges",
        lambda: DirectedTCGNN(X_unpruned_t.size(1), edge_dim=5, hid=128, dropout=0.3, use_knn=False, backend=backend),
        (X_unpruned_t, g_unpruned_sanad["edge_index_fwd"], g_unpruned_sanad["edge_attr_fwd"], g_unpruned_sanad["edge_index_rev"], g_unpruned_sanad["edge_attr_rev"]),
    )
    run_pyg_5seed(
        "G4c_MV_TC_GNN_Sanad_Plus_kNN", "ablation_semantic_knn",
        lambda: DirectedTCGNN(X_sanad_t.size(1), edge_dim=5, hid=128, dropout=0.3, use_knn=True, backend=backend),
        (*g4a_args, ei_knn, ea_knn),
    )
    run_pyg_5seed(
        "G4d_Directed_TC_GNN_Consolidated", "ablation_consolidated_edges",
        lambda: DirectedTCGNN(X_consol_t.size(1), edge_dim=5, hid=128, dropout=0.3, use_knn=False, backend=backend),
        (X_consol_t, g_chrono_consol["edge_index_fwd"], g_chrono_consol["edge_attr_fwd"], g_chrono_consol["edge_index_rev"], g_chrono_consol["edge_attr_rev"]),
    )

    # Paired bootstrap vs G0 AND vs G2b (honest multi-hop vs 1-hop test)
    g0_rc_te, g0_sp_te = ens_preds_all["G0_Stage2_AraBERT_NoGraph"]["rank_exp"][idx_test], ens_preds_all["G0_Stage2_AraBERT_NoGraph"]["shift_probs"][idx_test].argmax(axis=1)
    g2b_rc_te, g2b_sp_te = ens_preds_all["G2b_Sem_Plus_SanadStruct_MLP"]["rank_exp"][idx_test], ens_preds_all["G2b_Sem_Plus_SanadStruct_MLP"]["shift_probs"][idx_test].argmax(axis=1)
    conn_test, iso_test = ~g_chrono_sanad["is_isolated"][idx_test], g_chrono_sanad["is_isolated"][idx_test]

    sig_rows: list[dict[str, Any]] = []
    for m_name in ["G4a_Directed_TC_GNN_Sanad", "G4b_Directed_TC_GNN_UnprunedSanad", "G4c_MV_TC_GNN_Sanad_Plus_kNN", "G4d_Directed_TC_GNN_Consolidated", "G3c_Undirected_GATv2", "G2b_Sem_Plus_SanadStruct_MLP"]:
        m_rc_te, m_sp_te = ens_preds_all[m_name]["rank_exp"][idx_test], ens_preds_all[m_name]["shift_probs"][idx_test].argmax(axis=1)
        for rb in paired_bootstrap_vs_ref(y_rank_all[idx_test], y_shift_all[idx_test], is_maqbul_all[idx_test], g0_rc_te, g0_sp_te, m_rc_te, m_sp_te):
            sig_rows.append({"section": "bootstrap_vs_g0", "model": m_name, **rb})
    for m_name in ["G4a_Directed_TC_GNN_Sanad", "G4c_MV_TC_GNN_Sanad_Plus_kNN", "G4d_Directed_TC_GNN_Consolidated"]:
        m_rc_te, m_sp_te = ens_preds_all[m_name]["rank_exp"][idx_test], ens_preds_all[m_name]["shift_probs"][idx_test].argmax(axis=1)
        for rb in paired_bootstrap_vs_ref(y_rank_all[idx_test], y_shift_all[idx_test], is_maqbul_all[idx_test], g2b_rc_te, g2b_sp_te, m_rc_te, m_sp_te):
            sig_rows.append({"section": "bootstrap_vs_g2b", "model": m_name, **rb})
    for m_name in ["G0_Stage2_AraBERT_NoGraph", "G2b_Sem_Plus_SanadStruct_MLP", "G3c_Undirected_GATv2", "G4a_Directed_TC_GNN_Sanad", "G4c_MV_TC_GNN_Sanad_Plus_kNN"]:
        m_rc_te, m_sp_te = ens_preds_all[m_name]["rank_exp"][idx_test], ens_preds_all[m_name]["shift_probs"][idx_test].argmax(axis=1)
        for sub_name, mask in [("connected_sanad", conn_test), ("isolated_sanad", iso_test)]:
            sm = compute_metrics(y_rank_all[idx_test][mask], y_shift_all[idx_test][mask], m_rc_te[mask], m_sp_te[mask], is_maqbul_all[idx_test][mask])
            sig_rows.append({"section": f"subgroup_{sub_name}", "model": m_name, "metric": "summary", "ref_val": int(mask.sum()), "model_ens_val": sm["rank_mae"], "delta_vs_ref": sm["rank_qwk"], "ci95_low": sm["bin_acc"], "ci95_high": sm["shift_macro_f1"], "p_value_2sided": sm["r6_rank_mae"]})

    comp_csv = out_dir / "STAGE3_MODEL_COMPARISON_5SEED_V3.csv"
    all_comp_keys = list(dict.fromkeys(k for r in comp_rows for k in r.keys()))
    with comp_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=all_comp_keys, lineterminator="\n")
        w.writeheader()
        w.writerows(comp_rows)

    sig_csv = out_dir / "STAGE3_SUBGROUP_AND_SIGNIFICANCE_V3.csv"
    with sig_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(sig_rows[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(sig_rows)

    pred_csv = out_dir / "STAGE3_TEST_PREDICTIONS_V3.csv"
    pred_fields = ["entry_id", "score_B_rank_1_to_12", "score_E2_rank_1_to_12", "shift_class", "sanad_chrono_pruned_is_isolated"]
    for m_name in ens_preds_all:
        pred_fields.extend([f"{m_name}_rank_pred", f"{m_name}_shift_pred"])
    with pred_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=pred_fields, lineterminator="\n")
        w.writeheader()
        for gi in idx_test:
            r = node_rows[gi]
            row_d = {
                "entry_id": r["entry_id"],
                "score_B_rank_1_to_12": int(score_b_all[gi]),
                "score_E2_rank_1_to_12": int(y_rank_all[gi]),
                "shift_class": SHIFT_LABELS[int(y_shift_all[gi])],
                "sanad_chrono_pruned_is_isolated": int(g_chrono_sanad["is_isolated"][gi]),
            }
            for m_name, p_d in ens_preds_all.items():
                row_d[f"{m_name}_rank_pred"] = f"{p_d['rank_exp'][gi]:.4f}"
                row_d[f"{m_name}_shift_pred"] = SHIFT_LABELS[int(p_d["shift_probs"][gi].argmax())]
            w.writerow(row_d)

    # Export Option-A v3 outputs (estimate ONLY for missing/abstained/suspect; diagnostics for observed)
    flagship = "G4a_Directed_TC_GNN_Sanad"
    fp = ens_preds_all[flagship]
    out_csv = out_dir / "STAGE3_TC_GNN_OUTPUTS_8827_V3.csv"
    out_fields = [
        "entry_id", "entry_number_numeric", "split",
        "score_B_rank_1_to_12", "score_B_reliability_0_1", "score_B_0_100",
        "taqrib_is_conditional_maqbul",
        "score_E2_rank_1_to_12", "score_E2_reliability_0_1", "score_E2_0_100",
        "tahrir_disposition", "status_E2",
        "score_G_continuous", "score_G_rank", "score_G_reliability_0_1", "score_G_0_100",
        "score_G_estimate", "score_G_entropy",
        "score_G_predicted_shift", "score_G_p_upgraded", "score_G_p_unchanged", "score_G_p_downgraded",
        "source", "G_agrees_with_tahrir", "G_residual",
        "sanad_chrono_pruned_out_degree", "sanad_chrono_pruned_in_degree", "sanad_chrono_pruned_is_isolated",
    ]
    with out_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=out_fields, lineterminator="\n")
        w.writeheader()
        for i, r in enumerate(node_rows):
            lrow = layered_by_id[r["entry_id"]]
            rp = np.clip(fp["rank_probs"][i], 1e-8, 1.0)
            ent = float(-(rp * np.log(rp)).sum() / math.log(12.0))
            rexp = float(fp["rank_exp"][i])
            rdisc = int(np.clip(np.rint(rexp), 1, 12))
            sp = fp["shift_probs"][i]
            g_01, g_100 = rank_to_0_1(rexp), rank_to_0_100(rexp)

            sb_rk = lrow["rank_B"].strip()
            sb_100 = lrow["score_B"].strip()
            sb_01 = f"{float(sb_100)/100.0:.4f}" if sb_100 else ""
            e2_rk = lrow["rank_E2"].strip()
            e2_100 = lrow["score_E2"].strip()
            e2_01 = f"{float(e2_100)/100.0:.4f}" if e2_100 else ""
            st_e2 = lrow["status_E2"].strip()

            needs_estimate = st_e2 in {"missing", "abstained", "suspect_alignment"} or not e2_rk
            if needs_estimate:
                source = "model_estimate"
                g_est_s = f"{g_100:.2f}"
                g_agrees_s = ""
                g_res_s = ""
            else:
                source = "observed_scholarly"
                g_est_s = ""
                g_agrees_s = str(rdisc == int(e2_rk))
                g_res_s = f"{(g_100 - float(e2_100)):.2f}"

            w.writerow({
                "entry_id": r["entry_id"],
                "entry_number_numeric": r["entry_number_numeric"],
                "split": r["split"],
                "score_B_rank_1_to_12": sb_rk,
                "score_B_reliability_0_1": sb_01,
                "score_B_0_100": f"{float(sb_100):.2f}" if sb_100 else "",
                "taqrib_is_conditional_maqbul": r["taqrib_is_conditional_maqbul"],
                "score_E2_rank_1_to_12": e2_rk,
                "score_E2_reliability_0_1": e2_01,
                "score_E2_0_100": f"{float(e2_100):.2f}" if e2_100 else "",
                "tahrir_disposition": lrow["tahrir_disposition"],
                "status_E2": st_e2,
                "score_G_continuous": f"{rexp:.4f}",
                "score_G_rank": rdisc,
                "score_G_reliability_0_1": f"{g_01:.4f}",
                "score_G_0_100": f"{g_100:.2f}",
                "score_G_estimate": g_est_s,
                "score_G_entropy": f"{ent:.4f}",
                "score_G_predicted_shift": SHIFT_LABELS[int(sp.argmax())],
                "score_G_p_upgraded": f"{sp[0]:.4f}",
                "score_G_p_unchanged": f"{sp[1]:.4f}",
                "score_G_p_downgraded": f"{sp[2]:.4f}",
                "source": source,
                "G_agrees_with_tahrir": g_agrees_s,
                "G_residual": g_res_s,
                "sanad_chrono_pruned_out_degree": int(g_chrono_sanad["out_deg"][i]),
                "sanad_chrono_pruned_in_degree": int(g_chrono_sanad["in_deg"][i]),
                "sanad_chrono_pruned_is_isolated": int(g_chrono_sanad["is_isolated"][i]),
            })

    # Write Summary Report
    test_comp = [r for r in comp_rows if r["split"] == "test"]
    md = [
        "# Stage 3: TC-GNN (Text-Classification-informed GNN) Ablation Report (v3)",
        "",
        f"- **Generated (UTC):** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%SZ')}",
        f"- **Elapsed:** {time.time() - t0:.1f}s | **Device:** {device.type.upper()} (`backend={backend}`)",
        f"- **Clean Cohort (excluding `missing` + `suspect_alignment`):** `train = {len(idx_train)}`, `val = {len(idx_val)}`, `test = {len(idx_test)}`.",
        f"- **Ṭabaqah Chronology Pruning (`chrono_pruned`, Pure Sanad):** 42,011 → **{g_chrono_sanad['kept_edges']}** kept (`{g_chrono_sanad['pruned_impossible']}` pruned).",
        f"- **3-Run Determinism Check (`G4a`, `seed=42`):** `all_3_bit_exact = {determinism_check['all_3_bit_exact']}`, `max_abs_diff = {determinism_check['max_abs_rank_exp_diff']}`.",
        f"- **Graph Homophily (`chrono_sanad`):** 12-rank edge={homophily['chrono_sanad_12rank']['edge_homophily']:.4f} (class={homophily['chrono_sanad_12rank']['class_homophily']:.4f}); 3-tier edge={homophily['chrono_sanad_3tier']['edge_homophily']:.4f} (class={homophily['chrono_sanad_3tier']['class_homophily']:.4f}).",
        "",
        "## 1. 5-Seed Test Split Ablation Table (Mean ± Std + Ensemble)",
        "",
        "| Model | Family | Rank MAE ↓ | QWK ↑ | Bin Acc ↑ | 3-Tier MF1 ↑ | Shift MF1 ↑ | R6 MAE ↓ | Ens MAE ↓ | Ens Shift MF1 ↑ |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in test_comp:
        md.append(
            f"| `{r['model']}` | `{r['family']}` | {r['rank_mae_mean']:.4f}±{r['rank_mae_std']:.4f} | "
            f"{r['rank_qwk_mean']:.4f}±{r['rank_qwk_std']:.4f} | {r['bin_acc_mean']:.4f}±{r['bin_acc_std']:.4f} | "
            f"{r['tier3_macro_f1_mean']:.4f}±{r['tier3_macro_f1_std']:.4f} | {r['shift_macro_f1_mean']:.4f}±{r['shift_macro_f1_std']:.4f} | "
            f"{r['r6_rank_mae_mean']:.4f}±{r['r6_rank_mae_std']:.4f} | {r['ens_rank_mae']:.4f} | {r['ens_shift_macro_f1']:.4f} |"
        )
    report_md = out_dir / "STAGE3_RESULTS_SUMMARY_V3.md"
    report_md.write_bytes(("\n".join(md) + "\n").encode("utf-8"))

    manifest_files = [comp_csv, sig_csv, pred_csv, out_csv, report_md]
    manifest = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "script": to_posix_relative(Path(__file__), ROOT),
        "elapsed_sec": round(time.time() - t0, 2),
        "inputs": {
            "layer_rules_v3.json": {"path": to_posix_relative(LAYER_RULES, ROOT), "sha256": sha256_text_normalized(LAYER_RULES)},
            "LAYERED_SCORES_WIDE_V3.csv": {"path": to_posix_relative(LAYERED_WIDE, ROOT), "sha256": sha256_text_normalized(LAYERED_WIDE)},
            "STAGE2_OOF_ESA_FEATURES_8827_V3.csv": {"path": to_posix_relative(stage2_oof, ROOT), "sha256": sha256_text_normalized(stage2_oof)},
            "TAQRIB_V2_MASTER_NODES_8827.csv": {"path": to_posix_relative(MASTER_NODES, ROOT), "sha256": sha256_text_normalized(MASTER_NODES)},
            "TAQRIB_V2_GRAPH_EDGES.csv": {"path": to_posix_relative(GRAPH_EDGES, ROOT), "sha256": sha256_text_normalized(GRAPH_EDGES)},
        },
        "chrono_sanad_kept_edges": g_chrono_sanad["kept_edges"],
        "chrono_sanad_pruned_edges": g_chrono_sanad["pruned_impossible"],
        "determinism_check": determinism_check,
        "homophily": homophily,
        "gate_logs": gate_logs,
        "files": {p.name: {"sha256": sha256_text_normalized(p), "bytes": p.stat().st_size} for p in manifest_files},
    }
    manifest_json = out_dir / "MANIFEST.json"
    manifest_json.write_bytes((json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    (out_dir / "MANIFEST.sha256").write_bytes(
        ("\n".join(f"{sha256_text_normalized(p)}  {p.name}" for p in [*manifest_files, manifest_json]) + "\n").encode("ascii")
    )
    print("Stage 3 v3 complete in", round(time.time() - t0, 1), "s ->", out_dir)


if __name__ == "__main__":
    main()
