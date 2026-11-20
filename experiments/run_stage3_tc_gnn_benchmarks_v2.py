#!/usr/bin/env python3
"""Stage 3: TC-GNN Graph Enrichment & Controlled Ablation Study (taqrib-oriented v2).

Evaluates directional temporal-causal message passing over the Hadith Sanad / Bukhari
transmission network fused with Stage 2 5-fold OOF AraBERTv02 semantics and structured
Taqrib metadata, grounded in Zeng et al. (2024, MV-HGNN) and Mahmoud et al. (2024).

Controlled ablation ladder (seeds 42..46):
  - G0_Stage2_AraBERT_NoGraph: Stage 2 text+metadata anchor (from 5-fold OOF export)
  - G1_GraphOnly_NoText: Pure graph structure + tabaqa + sigils (NO text, NO Score 1)
  - G2a_Sem_Plus_SanadStruct_HistGBDT: Non-GNN HistGBDT over Meta + Sem + SanadStruct
  - G2b_Sem_Plus_SanadStruct_MLP: Non-GNN Dual-Head MLP over Meta + Sem + SanadStruct
  - G3a_Undirected_GCN: Symmetrized 2-layer GCN + residual skip
  - G3b_Undirected_GraphSAGE: Symmetrized 2-layer GraphSAGE + residual skip
  - G3c_Undirected_GATv2: Symmetrized 2-layer GATv2 + residual skip
  - G4a_Directed_TC_GNN_Sanad (PRIMARY): Residual-gated directed Forward+Reverse edge-conditioned GATv2 on TC-pruned Pure Sanad (37,364 edges)
  - G4b_Directed_TC_GNN_UnprunedSanad: Decision 2 ablation on unpruned Pure Sanad (42,011 edges)
  - G4c_MV_TC_GNN_Sanad_Plus_kNN: Decision 3 ablation (G4a + Semantic kNN k=8 view per Zeng 2024)
  - G4d_Directed_TC_GNN_Consolidated: Decision 1 ablation on TC-pruned Consolidated graph (59,864 minus impossible edges)
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import random
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.metrics import cohen_kappa_score, f1_score, mean_absolute_error, accuracy_score
from sklearn.preprocessing import StandardScaler
from torch_geometric.nn import GATv2Conv, GCNConv, SAGEConv

from run_stage2_semantic_benchmarks_v2 import (
    SHIFT_LABELS,
    SHIFT_TO_ID,
    build_meta_matrix,
    compute_metrics,
)


ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline"
MASTER_NODES = PIPELINE / "taqrib_v2_master_dataset_2026-11-20/TAQRIB_V2_MASTER_NODES_8827.csv"
GRAPH_EDGES = PIPELINE / "taqrib_v2_master_dataset_2026-11-20/TAQRIB_V2_GRAPH_EDGES.csv"
STAGE2_OOF = ROOT / "results/stage2_semantic_benchmarks_v2_2026-11-20/STAGE2_OOF_SEMANTIC_FEATURES_8827_V2.csv"
OUT_DIR = ROOT / "results/stage3_tc_gnn_benchmarks_v2_2026-11-20"

SEEDS = [42, 43, 44, 45, 46]
BOOTSTRAP_B = 2000


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_graph_and_struct_features(
    node_rows: list[dict[str, str]],
    edge_rows: list[dict[str, str]],
    id_to_idx: dict[str, int],
    score1_all: np.ndarray,
    tabaqa_all: np.ndarray,
    mode: str,
) -> dict[str, Any]:
    """Build directed edge tensors and leak-free structural node features for a given graph mode.

    mode in {'tc_sanad', 'unpruned_sanad', 'tc_consolidated'}.
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
        if mode in ("tc_sanad", "unpruned_sanad") and not is_sanad:
            continue

        u = id_to_idx[e["teacher_entry_id"]]
        v = id_to_idx[e["student_entry_id"]]
        tu = int(tabaqa_all[u])
        tv = int(tabaqa_all[v])
        missing_tab = 1.0 if (tu <= 0 or tv <= 0) else 0.0
        delta_tab = float(tv - tu) if missing_tab == 0.0 else 0.0

        if mode in ("tc_sanad", "tc_consolidated") and missing_tab == 0.0 and delta_tab <= -2.0:
            pruned_impossible += 1
            continue

        kept += 1
        buk_w = int(e["bukhari_isnad_weight"])
        su_w = int(e["sanadset_unique_weight"])
        sm_w = int(e["sanadset_method1_disambig_weight"])
        sdb = int(e["sanadset_distinct_books"])
        tot_w = int(e["total_consolidated_weight"])
        edge_w = float(su_w + sm_w + buk_w) if mode in ("tc_sanad", "unpruned_sanad") else float(tot_w)

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

    # 17-dim structural features (Score-1-only neighbor aggregations, zero Score-2 leakage)
    struct = np.zeros((n_nodes, 17), dtype=np.float32)
    for i in range(n_nodes):
        tot_d = out_deg[i] + in_deg[i]
        o_ranks = [float(score1_all[j]) for j in out_nbrs[i] if score1_all[j] > 0]
        i_ranks = [float(score1_all[j]) for j in in_nbrs[i] if score1_all[j] > 0]
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

    # Deduplicated undirected symmetrized edge_index for G3 baselines
    undir_pairs = set(zip(fwd_src, fwd_dst)) | set(zip(rev_src, rev_dst))
    u_src = [p[0] for p in undir_pairs]
    u_dst = [p[1] for p in undir_pairs]
    edge_index_undir = torch.tensor([u_src, u_dst], dtype=torch.long)

    return {
        "kept_edges": kept,
        "pruned_impossible": pruned_impossible,
        "out_deg": out_deg,
        "in_deg": in_deg,
        "is_isolated": (out_deg + in_deg) == 0,
        "struct": struct,
        "edge_index_fwd": edge_index_fwd,
        "edge_attr_fwd": edge_attr_fwd,
        "edge_index_rev": edge_index_rev,
        "edge_attr_rev": edge_attr_rev,
        "edge_index_undir": edge_index_undir,
    }


def build_semantic_knn_view(cls_pca: np.ndarray, k: int = 8) -> tuple[torch.Tensor, torch.Tensor]:
    """Build directed k-NN cosine similarity edges (neighbor -> node) over Stage 2 PCA space."""
    z = torch.tensor(cls_pca, dtype=torch.float32)
    z = F.normalize(z, p=2, dim=-1)
    sim = z @ z.T
    sim.fill_diagonal_(-1e9)
    vals, idxs = torch.topk(sim, k=k, dim=1)
    n = z.size(0)
    dst = torch.arange(n, dtype=torch.long).unsqueeze(1).expand(n, k).reshape(-1)
    src = idxs.reshape(-1)
    edge_index = torch.stack([src, dst], dim=0)
    edge_attr = vals.reshape(-1, 1)
    return edge_index, edge_attr


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


class UndirectedGNN(nn.Module):
    def __init__(self, in_dim: int, conv_type: str, hid: int = 128, dropout: float = 0.3) -> None:
        super().__init__()
        self.in_proj = nn.Sequential(nn.Linear(in_dim, hid), nn.LayerNorm(hid), nn.GELU(), nn.Dropout(dropout))
        if conv_type == "gcn":
            self.conv1 = GCNConv(hid, hid)
            self.conv2 = GCNConv(hid, hid)
        elif conv_type == "sage":
            self.conv1 = SAGEConv(hid, hid)
            self.conv2 = SAGEConv(hid, hid)
        elif conv_type == "gatv2":
            self.conv1 = GATv2Conv(hid, hid // 4, heads=4, dropout=dropout, add_self_loops=False)
            self.conv2 = GATv2Conv(hid, hid // 4, heads=4, dropout=dropout, add_self_loops=False)
        else:
            raise ValueError(conv_type)
        self.norm1 = nn.LayerNorm(hid)
        self.norm2 = nn.LayerNorm(hid)
        self.drop = nn.Dropout(dropout)
        self.trunk = nn.Sequential(
            nn.Linear(hid * 2, hid),
            nn.LayerNorm(hid),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        self.rank_head = nn.Linear(hid, 12)
        self.shift_head = nn.Linear(hid, 3)

    def forward(
        self, x: torch.Tensor, edge_index: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor, dict[str, torch.Tensor]]:
        h0 = self.in_proj(x)
        h1 = self.norm1(h0 + self.drop(F.gelu(self.conv1(h0, edge_index))))
        h2 = self.norm2(h1 + self.drop(F.gelu(self.conv2(h1, edge_index))))
        h = self.trunk(torch.cat([h0, h2], dim=-1))
        return self.rank_head(h), self.shift_head(h), {}


class DirectedTCGNN(nn.Module):
    """Residual-Gated Directional Edge-Conditioned GATv2 (Forward + Reverse + optional kNN view)."""

    def __init__(
        self, in_dim: int, edge_dim: int = 5, hid: int = 128, dropout: float = 0.3, use_knn: bool = False
    ) -> None:
        super().__init__()
        self.use_knn = use_knn
        self.in_proj = nn.Sequential(nn.Linear(in_dim, hid), nn.LayerNorm(hid), nn.GELU(), nn.Dropout(dropout))

        self.fwd1 = GATv2Conv(hid, hid // 4, heads=4, edge_dim=edge_dim, dropout=dropout, add_self_loops=False)
        self.rev1 = GATv2Conv(hid, hid // 4, heads=4, edge_dim=edge_dim, dropout=dropout, add_self_loops=False)
        self.fwd2 = GATv2Conv(hid, hid // 4, heads=4, edge_dim=edge_dim, dropout=dropout, add_self_loops=False)
        self.rev2 = GATv2Conv(hid, hid // 4, heads=4, edge_dim=edge_dim, dropout=dropout, add_self_loops=False)

        self.gate_fwd1 = nn.Linear(hid * 2, hid)
        self.gate_rev1 = nn.Linear(hid * 2, hid)
        self.gate_fwd2 = nn.Linear(hid * 2, hid)
        self.gate_rev2 = nn.Linear(hid * 2, hid)

        if use_knn:
            self.knn1 = GATv2Conv(hid, hid // 4, heads=4, edge_dim=1, dropout=dropout, add_self_loops=False)
            self.knn2 = GATv2Conv(hid, hid // 4, heads=4, edge_dim=1, dropout=dropout, add_self_loops=False)
            self.gate_knn1 = nn.Linear(hid * 2, hid)
            self.gate_knn2 = nn.Linear(hid * 2, hid)

        self.norm1 = nn.LayerNorm(hid)
        self.norm2 = nn.LayerNorm(hid)
        self.drop = nn.Dropout(dropout)
        self.trunk = nn.Sequential(
            nn.Linear(hid * 2, hid),
            nn.LayerNorm(hid),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        self.rank_head = nn.Linear(hid, 12)
        self.shift_head = nn.Linear(hid, 3)

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
    if device.type == "cuda":
        torch.cuda.empty_cache()
    return {"rank_probs": r_probs, "rank_exp": r_exp, "shift_probs": s_probs, "gates": gates_np}


def paired_bootstrap_vs_g0(
    y_rank: np.ndarray,
    y_shift: np.ndarray,
    is_maqbul: np.ndarray,
    g0_rc: np.ndarray,
    g0_sp: np.ndarray,
    m_rc: np.ndarray,
    m_sp: np.ndarray,
    n_boot: int = BOOTSTRAP_B,
    seed: int = 42,
) -> list[dict[str, Any]]:
    rng = np.random.default_rng(seed)
    n = len(y_rank)
    g0_disc = np.clip(np.rint(g0_rc), 1, 12).astype(int)
    m_disc = np.clip(np.rint(m_rc), 1, 12).astype(int)
    y_bin = (y_rank <= 6).astype(int)
    g0_bin = (g0_disc <= 6).astype(int)
    m_bin = (m_disc <= 6).astype(int)
    r6_mask = is_maqbul.astype(bool)

    diffs: dict[str, list[float]] = defaultdict(list)
    obs: dict[str, tuple[float, float]] = {}

    obs["rank_mae"] = (float(mean_absolute_error(y_rank, g0_rc)), float(mean_absolute_error(y_rank, m_rc)))
    obs["rank_qwk"] = (
        float(cohen_kappa_score(y_rank, g0_disc, weights="quadratic")),
        float(cohen_kappa_score(y_rank, m_disc, weights="quadratic")),
    )
    obs["bin_acc"] = (float(accuracy_score(y_bin, g0_bin)), float(accuracy_score(y_bin, m_bin)))
    obs["shift_macro_f1"] = (
        float(f1_score(y_shift, g0_sp, labels=[0, 1, 2], average="macro", zero_division=0)),
        float(f1_score(y_shift, m_sp, labels=[0, 1, 2], average="macro", zero_division=0)),
    )
    obs["r6_rank_mae"] = (
        float(mean_absolute_error(y_rank[r6_mask], g0_rc[r6_mask])),
        float(mean_absolute_error(y_rank[r6_mask], m_rc[r6_mask])),
    )

    for _ in range(n_boot):
        b = rng.integers(0, n, size=n)
        diffs["rank_mae"].append(float(mean_absolute_error(y_rank[b], m_rc[b]) - mean_absolute_error(y_rank[b], g0_rc[b])))
        diffs["rank_qwk"].append(
            float(
                cohen_kappa_score(y_rank[b], m_disc[b], weights="quadratic")
                - cohen_kappa_score(y_rank[b], g0_disc[b], weights="quadratic")
            )
        )
        diffs["bin_acc"].append(float(accuracy_score(y_bin[b], m_bin[b]) - accuracy_score(y_bin[b], g0_bin[b])))
        diffs["shift_macro_f1"].append(
            float(
                f1_score(y_shift[b], m_sp[b], labels=[0, 1, 2], average="macro", zero_division=0)
                - f1_score(y_shift[b], g0_sp[b], labels=[0, 1, 2], average="macro", zero_division=0)
            )
        )
        b_r6 = b[r6_mask[b]]
        if len(b_r6) > 0:
            diffs["r6_rank_mae"].append(
                float(mean_absolute_error(y_rank[b_r6], m_rc[b_r6]) - mean_absolute_error(y_rank[b_r6], g0_rc[b_r6]))
            )

    rows = []
    for metric, (v0, v1) in obs.items():
        arr = np.array(diffs[metric])
        ci_lo, ci_hi = np.percentile(arr, [2.5, 97.5])
        # Two-sided bootstrap p-value around 0
        p_pos = float(np.mean(arr >= 0.0))
        p_neg = float(np.mean(arr <= 0.0))
        p_val = min(1.0, 2.0 * min(p_pos, p_neg))
        rows.append(
            {
                "metric": metric,
                "g0_stage2_val": round(v0, 4),
                "model_ens_val": round(v1, 4),
                "delta_vs_g0": round(v1 - v0, 4),
                "ci95_low": round(float(ci_lo), 4),
                "ci95_high": round(float(ci_hi), 4),
                "p_value_2sided": round(p_val, 4),
            }
        )
    return rows


def main() -> None:
    t0 = time.time()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    with MASTER_NODES.open(encoding="utf-8-sig") as f:
        node_rows = list(csv.DictReader(f))
    with GRAPH_EDGES.open(encoding="utf-8-sig") as f:
        edge_rows = list(csv.DictReader(f))
    with STAGE2_OOF.open(encoding="utf-8-sig") as f:
        oof_rows = list(csv.DictReader(f))

    assert len(node_rows) == 8827 and len(oof_rows) == 8827
    assert [r["entry_id"] for r in node_rows] == [r["entry_id"] for r in oof_rows]

    id_to_idx = {r["entry_id"]: i for i, r in enumerate(node_rows)}
    splits = np.array([r["split"] for r in node_rows])
    idx_train = np.where(splits == "train")[0]
    idx_val = np.where(splits == "val")[0]
    idx_test = np.where(splits == "test")[0]

    y_rank_all = np.array([int(r["tahrir_rank_bilgin_1_to_12"]) if r["tahrir_rank_bilgin_1_to_12"] else -1 for r in node_rows])
    y_shift_all = np.array([SHIFT_TO_ID[r["shift_class"]] if r["shift_class"] else -1 for r in node_rows])
    score1_all = np.array([int(r["taqrib_rank_bilgin_1_to_12"]) if r["taqrib_rank_bilgin_1_to_12"] else -1 for r in node_rows])
    tabaqa_all = np.array([int(r["tabaqa_1_to_12"]) if r["tabaqa_1_to_12"] else -1 for r in node_rows])
    is_maqbul_all = np.array([1 if r["taqrib_is_conditional_maqbul"] == "True" else 0 for r in node_rows])

    X_meta, meta_names = build_meta_matrix(node_rows)
    sem_cols = [c for c in oof_rows[0].keys() if c not in ("entry_id", "split", "in_core_cohort_7258")]
    X_sem = np.array([[float(r[c]) for c in sem_cols] for r in oof_rows], dtype=np.float32)
    cls_pca = np.array([[float(r[f"arabert_cls_pca_{d:02d}"]) for d in range(32)] for r in oof_rows], dtype=np.float32)

    # Graph modes
    g_tc_sanad = load_graph_and_struct_features(node_rows, edge_rows, id_to_idx, score1_all, tabaqa_all, "tc_sanad")
    g_unpruned_sanad = load_graph_and_struct_features(node_rows, edge_rows, id_to_idx, score1_all, tabaqa_all, "unpruned_sanad")
    g_tc_consol = load_graph_and_struct_features(node_rows, edge_rows, id_to_idx, score1_all, tabaqa_all, "tc_consolidated")
    assert g_tc_sanad["pruned_impossible"] == 4647 and g_tc_sanad["kept_edges"] == 37364, g_tc_sanad

    ei_knn, ea_knn = build_semantic_knn_view(cls_pca, k=8)

    # Feature sets standardized strictly on train
    def std_feats(arr: np.ndarray) -> torch.Tensor:
        sc = StandardScaler()
        sc.fit(arr[idx_train])
        return torch.tensor(sc.transform(arr).astype(np.float32), device=device)

    # Pure G1: structural + tabaqa + sigils ONLY (NO Score 1, NO Stage 2 text)
    tab_sig_idx = [i for i, n in enumerate(meta_names) if n == "tabaqa_num" or n.startswith("subtier_") or n.startswith("sigil_")]
    X_g1_np = np.hstack([X_meta[:, tab_sig_idx], g_tc_sanad["struct"]])
    X_full_sanad_np = np.hstack([X_meta, X_sem, g_tc_sanad["struct"]])
    X_full_unpruned_np = np.hstack([X_meta, X_sem, g_unpruned_sanad["struct"]])
    X_full_consol_np = np.hstack([X_meta, X_sem, g_tc_consol["struct"]])

    X_g1_t = std_feats(X_g1_np)
    X_sanad_t = std_feats(X_full_sanad_np)
    X_unpruned_t = std_feats(X_full_unpruned_np)
    X_consol_t = std_feats(X_full_consol_np)

    # Move graph tensors to device
    for g in (g_tc_sanad, g_unpruned_sanad, g_tc_consol):
        for k in ("edge_index_fwd", "edge_attr_fwd", "edge_index_rev", "edge_attr_rev", "edge_index_undir"):
            g[k] = g[k].to(device)
    ei_knn = ei_knn.to(device)
    ea_knn = ea_knn.to(device)

    # Verify G0 reproduces Stage 2 exact test metrics
    g0_rank_exp = np.array([float(r["arabert_oof_rank_exp"]) for r in oof_rows], dtype=np.float32)
    g0_sprobs = np.array([[float(r["arabert_p_up"]), float(r["arabert_p_unch"]), float(r["arabert_p_down"])] for r in oof_rows], dtype=np.float32)
    g0_test_m = compute_metrics(
        y_rank_all[idx_test], y_shift_all[idx_test], g0_rank_exp[idx_test], g0_sprobs[idx_test].argmax(axis=1), is_maqbul_all[idx_test]
    )
    assert abs(g0_test_m["rank_mae"] - 0.6600) < 1e-3, f"G0 MAE mismatch: {g0_test_m}"

    comp_rows: list[dict[str, Any]] = []
    ens_preds_all: dict[str, dict[str, np.ndarray]] = {}
    gate_logs: dict[str, dict[str, float]] = {}

    def record_5seed(
        name: str,
        family: str,
        seed_val_metrics: list[dict[str, float]],
        seed_test_metrics: list[dict[str, float]],
        ens_r_probs: np.ndarray,
        ens_s_probs: np.ndarray,
    ) -> None:
        ens_r_exp = (ens_r_probs * np.arange(1, 13, dtype=np.float32)).sum(axis=1)
        ens_preds_all[name] = {"rank_probs": ens_r_probs, "rank_exp": ens_r_exp, "shift_probs": ens_s_probs}
        ens_test_m = compute_metrics(
            y_rank_all[idx_test],
            y_shift_all[idx_test],
            ens_r_exp[idx_test],
            ens_s_probs[idx_test].argmax(axis=1),
            is_maqbul_all[idx_test],
        )
        for sp_name, m_list in [("val", seed_val_metrics), ("test", seed_test_metrics)]:
            row_d: dict[str, Any] = {"model": name, "family": family, "split": sp_name, "n_seeds": len(m_list)}
            for k in m_list[0].keys():
                if k == "r6_n":
                    row_d[k] = m_list[0][k]
                    continue
                vals = np.array([m[k] for m in m_list], dtype=float)
                row_d[f"{k}_mean"] = round(float(vals.mean()), 4)
                row_d[f"{k}_std"] = round(float(vals.std()), 4)
            if sp_name == "test":
                for ek in ("rank_mae", "rank_qwk", "rank_exact_acc", "bin_acc", "bin_weighted_f1", "shift_macro_f1", "shift_active_macro_f1", "r6_rank_mae"):
                    row_d[f"ens_{ek}"] = ens_test_m[ek]
            comp_rows.append(row_d)
        print(
            f"[{name}] TEST 5-Seed Mean | MAE={np.mean([m['rank_mae'] for m in seed_test_metrics]):.4f} "
            f"QWK={np.mean([m['rank_qwk'] for m in seed_test_metrics]):.4f} "
            f"BinAcc={np.mean([m['bin_acc'] for m in seed_test_metrics]):.4f} "
            f"ShiftMF1={np.mean([m['shift_macro_f1'] for m in seed_test_metrics]):.4f} "
            f"R6_MAE={np.mean([m['r6_rank_mae'] for m in seed_test_metrics]):.4f} | "
            f"Ens MAE={ens_test_m['rank_mae']:.4f} ShiftMF1={ens_test_m['shift_macro_f1']:.4f}"
        )

    # Record G0 anchor
    g0_val_m = compute_metrics(y_rank_all[idx_val], y_shift_all[idx_val], g0_rank_exp[idx_val], g0_sprobs[idx_val].argmax(axis=1), is_maqbul_all[idx_val])
    g0_r_probs = np.array([[float(r[f"arabert_p_r{k}"]) for k in range(1, 13)] for r in oof_rows], dtype=np.float32)
    record_5seed("G0_Stage2_AraBERT_NoGraph", "stage2_text_anchor", [g0_val_m], [g0_test_m], g0_r_probs, g0_sprobs)

    # G2a HistGBDT (5-seed)
    g2a_vm, g2a_tm = [], []
    g2a_r_sum = np.zeros((len(node_rows), 12), dtype=np.float32)
    g2a_s_sum = np.zeros((len(node_rows), 3), dtype=np.float32)
    for sd in SEEDS:
        reg = HistGradientBoostingClassifier(max_iter=250, learning_rate=0.05, random_state=sd).fit(
            X_full_sanad_np[idx_train], y_rank_all[idx_train] - 1
        )
        cls = HistGradientBoostingClassifier(max_iter=250, learning_rate=0.05, class_weight="balanced", random_state=sd).fit(
            X_full_sanad_np[idx_train], y_shift_all[idx_train]
        )
        rp = reg.predict_proba(X_full_sanad_np)
        sp = cls.predict_proba(X_full_sanad_np)
        rexp = (rp * np.arange(1, 13, dtype=np.float32)).sum(axis=1)
        g2a_r_sum += rp / len(SEEDS)
        g2a_s_sum += sp / len(SEEDS)
        g2a_vm.append(compute_metrics(y_rank_all[idx_val], y_shift_all[idx_val], rexp[idx_val], sp[idx_val].argmax(axis=1), is_maqbul_all[idx_val]))
        g2a_tm.append(compute_metrics(y_rank_all[idx_test], y_shift_all[idx_test], rexp[idx_test], sp[idx_test].argmax(axis=1), is_maqbul_all[idx_test]))
    record_5seed("G2a_Sem_Plus_SanadStruct_HistGBDT", "tabular_with_struct", g2a_vm, g2a_tm, g2a_r_sum, g2a_s_sum)

    # Runner for PyTorch / PyG transductive models
    def run_pyg_5seed(name: str, family: str, model_fn: Any, fwd_args: tuple[torch.Tensor, ...]) -> None:
        vm_list, tm_list = [], []
        r_sum = np.zeros((len(node_rows), 12), dtype=np.float32)
        s_sum = np.zeros((len(node_rows), 3), dtype=np.float32)
        gf_conn, gf_iso, gr_conn, gr_iso, gk_all = [], [], [], [], []
        conn_mask = ~g_tc_sanad["is_isolated"]
        iso_mask = g_tc_sanad["is_isolated"]
        for sd in SEEDS:
            out = train_transductive_model(model_fn, fwd_args, idx_train, idx_val, y_rank_all, y_shift_all, is_maqbul_all, seed=sd)
            rp, rexp, sp = out["rank_probs"], out["rank_exp"], out["shift_probs"]
            r_sum += rp / len(SEEDS)
            s_sum += sp / len(SEEDS)
            vm_list.append(compute_metrics(y_rank_all[idx_val], y_shift_all[idx_val], rexp[idx_val], sp[idx_val].argmax(axis=1), is_maqbul_all[idx_val]))
            tm_list.append(compute_metrics(y_rank_all[idx_test], y_shift_all[idx_test], rexp[idx_test], sp[idx_test].argmax(axis=1), is_maqbul_all[idx_test]))
            if "g_fwd" in out["gates"]:
                gf_conn.append(float(out["gates"]["g_fwd"][conn_mask].mean()))
                gf_iso.append(float(out["gates"]["g_fwd"][iso_mask].mean()))
                gr_conn.append(float(out["gates"]["g_rev"][conn_mask].mean()))
                gr_iso.append(float(out["gates"]["g_rev"][iso_mask].mean()))
            if "g_knn" in out["gates"]:
                gk_all.append(float(out["gates"]["g_knn"].mean()))
        if gf_conn:
            gate_logs[name] = {
                "g_fwd_connected": round(float(np.mean(gf_conn)), 4),
                "g_fwd_isolated": round(float(np.mean(gf_iso)), 4),
                "g_rev_connected": round(float(np.mean(gr_conn)), 4),
                "g_rev_isolated": round(float(np.mean(gr_iso)), 4),
                **({"g_knn_all": round(float(np.mean(gk_all)), 4)} if gk_all else {}),
            }
        record_5seed(name, family, vm_list, tm_list, r_sum, s_sum)

    # G1 Graph-Only (No Text, No Score 1)
    run_pyg_5seed(
        "G1_GraphOnly_NoText",
        "graph_only",
        lambda: DirectedTCGNN(X_g1_t.size(1), edge_dim=5, hid=128, dropout=0.3, use_knn=False),
        (X_g1_t, g_tc_sanad["edge_index_fwd"], g_tc_sanad["edge_attr_fwd"], g_tc_sanad["edge_index_rev"], g_tc_sanad["edge_attr_rev"]),
    )

    # G2b Dual-Head MLP
    run_pyg_5seed("G2b_Sem_Plus_SanadStruct_MLP", "tabular_with_struct", lambda: DualHeadMLP(X_sanad_t.size(1)), (X_sanad_t,))

    # G3 Undirected GNN Baselines
    run_pyg_5seed("G3a_Undirected_GCN", "undirected_gnn", lambda: UndirectedGNN(X_sanad_t.size(1), "gcn"), (X_sanad_t, g_tc_sanad["edge_index_undir"]))
    run_pyg_5seed("G3b_Undirected_GraphSAGE", "undirected_gnn", lambda: UndirectedGNN(X_sanad_t.size(1), "sage"), (X_sanad_t, g_tc_sanad["edge_index_undir"]))
    run_pyg_5seed("G3c_Undirected_GATv2", "undirected_gnn", lambda: UndirectedGNN(X_sanad_t.size(1), "gatv2"), (X_sanad_t, g_tc_sanad["edge_index_undir"]))

    # G4 Directed TC-GNN Suite
    run_pyg_5seed(
        "G4a_Directed_TC_GNN_Sanad",
        "directed_tc_gnn_primary",
        lambda: DirectedTCGNN(X_sanad_t.size(1), edge_dim=5, hid=128, dropout=0.3, use_knn=False),
        (X_sanad_t, g_tc_sanad["edge_index_fwd"], g_tc_sanad["edge_attr_fwd"], g_tc_sanad["edge_index_rev"], g_tc_sanad["edge_attr_rev"]),
    )
    run_pyg_5seed(
        "G4b_Directed_TC_GNN_UnprunedSanad",
        "ablation_unpruned_edges",
        lambda: DirectedTCGNN(X_unpruned_t.size(1), edge_dim=5, hid=128, dropout=0.3, use_knn=False),
        (X_unpruned_t, g_unpruned_sanad["edge_index_fwd"], g_unpruned_sanad["edge_attr_fwd"], g_unpruned_sanad["edge_index_rev"], g_unpruned_sanad["edge_attr_rev"]),
    )
    run_pyg_5seed(
        "G4c_MV_TC_GNN_Sanad_Plus_kNN",
        "ablation_semantic_knn",
        lambda: DirectedTCGNN(X_sanad_t.size(1), edge_dim=5, hid=128, dropout=0.3, use_knn=True),
        (X_sanad_t, g_tc_sanad["edge_index_fwd"], g_tc_sanad["edge_attr_fwd"], g_tc_sanad["edge_index_rev"], g_tc_sanad["edge_attr_rev"], ei_knn, ea_knn),
    )
    run_pyg_5seed(
        "G4d_Directed_TC_GNN_Consolidated",
        "ablation_consolidated_edges",
        lambda: DirectedTCGNN(X_consol_t.size(1), edge_dim=5, hid=128, dropout=0.3, use_knn=False),
        (X_consol_t, g_tc_consol["edge_index_fwd"], g_tc_consol["edge_attr_fwd"], g_tc_consol["edge_index_rev"], g_tc_consol["edge_attr_rev"]),
    )

    # Subgroup analysis + Paired Bootstrap vs G0 on TEST
    g0_rc_te = ens_preds_all["G0_Stage2_AraBERT_NoGraph"]["rank_exp"][idx_test]
    g0_sp_te = ens_preds_all["G0_Stage2_AraBERT_NoGraph"]["shift_probs"][idx_test].argmax(axis=1)
    conn_test = ~g_tc_sanad["is_isolated"][idx_test]
    iso_test = g_tc_sanad["is_isolated"][idx_test]

    sig_rows: list[dict[str, Any]] = []
    for m_name in ["G4a_Directed_TC_GNN_Sanad", "G4b_Directed_TC_GNN_UnprunedSanad", "G4c_MV_TC_GNN_Sanad_Plus_kNN", "G4d_Directed_TC_GNN_Consolidated", "G3c_Undirected_GATv2", "G2b_Sem_Plus_SanadStruct_MLP"]:
        m_rc_te = ens_preds_all[m_name]["rank_exp"][idx_test]
        m_sp_te = ens_preds_all[m_name]["shift_probs"][idx_test].argmax(axis=1)
        for row_b in paired_bootstrap_vs_g0(y_rank_all[idx_test], y_shift_all[idx_test], is_maqbul_all[idx_test], g0_rc_te, g0_sp_te, m_rc_te, m_sp_te):
            sig_rows.append({"section": "bootstrap_vs_g0", "model": m_name, **row_b})

    for m_name in ["G0_Stage2_AraBERT_NoGraph", "G2b_Sem_Plus_SanadStruct_MLP", "G3c_Undirected_GATv2", "G4a_Directed_TC_GNN_Sanad", "G4c_MV_TC_GNN_Sanad_Plus_kNN"]:
        m_rc_te = ens_preds_all[m_name]["rank_exp"][idx_test]
        m_sp_te = ens_preds_all[m_name]["shift_probs"][idx_test].argmax(axis=1)
        for sub_name, mask in [("connected_sanad", conn_test), ("isolated_sanad", iso_test)]:
            sm = compute_metrics(y_rank_all[idx_test][mask], y_shift_all[idx_test][mask], m_rc_te[mask], m_sp_te[mask], is_maqbul_all[idx_test][mask])
            sig_rows.append({"section": f"subgroup_{sub_name}", "model": m_name, "metric": "summary", "g0_stage2_val": int(mask.sum()), "model_ens_val": sm["rank_mae"], "delta_vs_g0": sm["rank_qwk"], "ci95_low": sm["bin_acc"], "ci95_high": sm["shift_macro_f1"], "p_value_2sided": sm["r6_rank_mae"]})

    # Write CSVs
    comp_csv = OUT_DIR / "STAGE3_MODEL_COMPARISON_5SEED_V2.csv"
    all_comp_keys = list(dict.fromkeys(k for r in comp_rows for k in r.keys()))
    with comp_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=all_comp_keys)
        w.writeheader()
        w.writerows(comp_rows)

    sig_csv = OUT_DIR / "STAGE3_SUBGROUP_AND_SIGNIFICANCE_V2.csv"
    with sig_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(sig_rows[0].keys()))
        w.writeheader()
        w.writerows(sig_rows)

    pred_csv = OUT_DIR / "STAGE3_TEST_PREDICTIONS_V2.csv"
    pred_fields = ["entry_id", "taqrib_rank_bilgin_1_to_12", "tahrir_rank_bilgin_1_to_12", "shift_class", "tc_sanad_is_isolated"]
    for m_name in ens_preds_all:
        pred_fields.extend([f"{m_name}_rank_pred", f"{m_name}_shift_pred"])
    with pred_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=pred_fields)
        w.writeheader()
        for gi in idx_test:
            r = node_rows[gi]
            row_d = {
                "entry_id": r["entry_id"],
                "taqrib_rank_bilgin_1_to_12": r["taqrib_rank_bilgin_1_to_12"],
                "tahrir_rank_bilgin_1_to_12": r["tahrir_rank_bilgin_1_to_12"],
                "shift_class": r["shift_class"],
                "tc_sanad_is_isolated": int(g_tc_sanad["is_isolated"][gi]),
            }
            for m_name, p_d in ens_preds_all.items():
                row_d[f"{m_name}_rank_pred"] = f"{p_d['rank_exp'][gi]:.4f}"
                row_d[f"{m_name}_shift_pred"] = SHIFT_LABELS[int(p_d["shift_probs"][gi].argmax())]
            w.writerow(row_d)

    # Export FINAL_TWO_SCORE_RIJAL_REPRESENTATION_8827.csv from primary flagship G4a
    flagship = "G4a_Directed_TC_GNN_Sanad"
    fp = ens_preds_all[flagship]
    final_csv = OUT_DIR / "FINAL_TWO_SCORE_RIJAL_REPRESENTATION_8827.csv"
    final_fields = [
        "entry_id", "entry_number_numeric", "split",
        "score1_ibn_hajar_rank_1_to_12", "score1_reliability_0_1", "score1_reliability_0_100",
        "taqrib_is_conditional_maqbul",
        "tahrir_scholar_rank_1_to_12", "tahrir_reliability_0_1", "tahrir_reliability_0_100",
        "tahrir_disposition",
        "score2_tc_gnn_continuous", "score2_tc_gnn_rank_1_to_12",
        "score2_reliability_0_1", "score2_reliability_0_100", "reliability_delta_0_100",
        "score2_predicted_shift", "score2_p_upgraded", "score2_p_unchanged", "score2_p_downgraded",
        "score2_rank_entropy", "tc_sanad_out_degree", "tc_sanad_in_degree", "tc_sanad_is_isolated",
    ]

    def rank_to_rel(r_val: float) -> tuple[float, float]:
        rel01 = (12.0 - r_val) / 11.0
        return rel01, rel01 * 100.0

    with final_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=final_fields)
        w.writeheader()
        for i, r in enumerate(node_rows):
            rp = np.clip(fp["rank_probs"][i], 1e-8, 1.0)
            ent = float(-(rp * np.log(rp)).sum() / math.log(12.0))
            rexp = float(fp["rank_exp"][i])
            rdisc = int(np.clip(np.rint(rexp), 1, 12))
            sp = fp["shift_probs"][i]
            assert not (math.isnan(rexp) or math.isnan(ent)), f"NaN in final export row {i}"
            s2_01, s2_100 = rank_to_rel(rexp)

            s1_str = r["taqrib_rank_bilgin_1_to_12"].strip()
            if s1_str:
                s1_01, s1_100 = rank_to_rel(float(s1_str))
                s1_01_s, s1_100_s = f"{s1_01:.4f}", f"{s1_100:.2f}"
                delta_s = f"{(s2_100 - s1_100):.2f}"
            else:
                s1_01_s = s1_100_s = delta_s = ""

            th_str = r["tahrir_rank_bilgin_1_to_12"].strip()
            if th_str:
                th_01, th_100 = rank_to_rel(float(th_str))
                th_01_s, th_100_s = f"{th_01:.4f}", f"{th_100:.2f}"
            else:
                th_01_s = th_100_s = ""

            w.writerow({
                "entry_id": r["entry_id"],
                "entry_number_numeric": r["entry_number_numeric"],
                "split": r["split"],
                "score1_ibn_hajar_rank_1_to_12": s1_str,
                "score1_reliability_0_1": s1_01_s,
                "score1_reliability_0_100": s1_100_s,
                "taqrib_is_conditional_maqbul": r["taqrib_is_conditional_maqbul"],
                "tahrir_scholar_rank_1_to_12": th_str,
                "tahrir_reliability_0_1": th_01_s,
                "tahrir_reliability_0_100": th_100_s,
                "tahrir_disposition": r["tahrir_disposition"],
                "score2_tc_gnn_continuous": f"{rexp:.4f}",
                "score2_tc_gnn_rank_1_to_12": rdisc,
                "score2_reliability_0_1": f"{s2_01:.4f}",
                "score2_reliability_0_100": f"{s2_100:.2f}",
                "reliability_delta_0_100": delta_s,
                "score2_predicted_shift": SHIFT_LABELS[int(sp.argmax())],
                "score2_p_upgraded": f"{sp[0]:.4f}",
                "score2_p_unchanged": f"{sp[1]:.4f}",
                "score2_p_downgraded": f"{sp[2]:.4f}",
                "score2_rank_entropy": f"{ent:.4f}",
                "tc_sanad_out_degree": int(g_tc_sanad["out_deg"][i]),
                "tc_sanad_in_degree": int(g_tc_sanad["in_deg"][i]),
                "tc_sanad_is_isolated": int(g_tc_sanad["is_isolated"][i]),
            })

    # Write STAGE3_RESULTS_SUMMARY_V2.md
    test_comp = [r for r in comp_rows if r["split"] == "test"]
    md = [
        "# Stage 3: TC-GNN Graph Enrichment & Controlled Ablation Report (v2)",
        "",
        f"- **Generated (UTC):** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%SZ')}",
        f"- **Elapsed:** {time.time() - t0:.1f}s | **Device:** {device.type.upper()}",
        f"- **Temporal-Causal Pruning Audit (Pure Sanad):** 42,011 total → **{g_tc_sanad['pruned_impossible']}** impossible edges (`Δṭabaqah ≤ -2`) pruned → **{g_tc_sanad['kept_edges']}** TC-clean edges.",
        f"- **Primary Two-Score Deliverable Generator:** `{flagship}` (5-seed ensemble).",
        "",
        "## 1. 5-Seed Test Split Ablation Table (`N = 1,089`, Mean ± Std + Ensemble)",
        "",
        "| Model | Family | Rank MAE ↓ | QWK ↑ | Bin Acc ↑ | Shift MF1 ↑ | R6 Maqbūl MAE ↓ | Ens MAE ↓ | Ens Shift MF1 ↑ |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in test_comp:
        md.append(
            f"| `{r['model']}` | `{r['family']}` | {r['rank_mae_mean']:.4f}±{r['rank_mae_std']:.4f} | "
            f"{r['rank_qwk_mean']:.4f}±{r['rank_qwk_std']:.4f} | {r['bin_acc_mean']:.4f}±{r['bin_acc_std']:.4f} | "
            f"{r['shift_macro_f1_mean']:.4f}±{r['shift_macro_f1_std']:.4f} | {r['r6_rank_mae_mean']:.4f}±{r['r6_rank_mae_std']:.4f} | "
            f"{r['ens_rank_mae']:.4f} | {r['ens_shift_macro_f1']:.4f} |"
        )

    md.extend(["", "## 2. Connected vs. Isolated Subgroup Breakdown (`test`, Ensemble)", "", "| Model | Subgroup | N | Rank MAE ↓ | QWK ↑ | Bin Acc ↑ | Shift MF1 ↑ | R6 MAE ↓ |", "|---|---|---:|---:|---:|---:|---:|---:|"])
    for sr in sig_rows:
        if sr["section"].startswith("subgroup_"):
            md.append(f"| `{sr['model']}` | `{sr['section'].replace('subgroup_', '')}` | {sr['g0_stage2_val']} | {sr['model_ens_val']:.4f} | {sr['delta_vs_g0']:.4f} | {sr['ci95_low']:.4f} | {sr['ci95_high']:.4f} | {sr['p_value_2sided']:.4f} |")

    md.extend(["", "## 3. Learned Directional Gate Activations", ""])
    for m_name, g_d in gate_logs.items():
        md.append(f"- `{m_name}`: " + ", ".join(f"{k}={v:.4f}" for k, v in g_d.items()))

    report_md = OUT_DIR / "STAGE3_RESULTS_SUMMARY_V2.md"
    report_md.write_text("\n".join(md) + "\n", encoding="utf-8")

    manifest_files = [comp_csv, sig_csv, pred_csv, final_csv, report_md]
    manifest = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "script": "experiments/run_stage3_tc_gnn_benchmarks_v2.py",
        "elapsed_sec": round(time.time() - t0, 2),
        "tc_sanad_kept_edges": g_tc_sanad["kept_edges"],
        "tc_sanad_pruned_edges": g_tc_sanad["pruned_impossible"],
        "gate_logs": gate_logs,
        "files": {p.name: {"sha256": sha256_file(p), "bytes": p.stat().st_size} for p in manifest_files},
    }
    manifest_json = OUT_DIR / "MANIFEST.json"
    manifest_json.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT_DIR / "MANIFEST.sha256").write_text(
        "\n".join(f"{sha256_file(p)}  {p.name}" for p in [*manifest_files, manifest_json]) + "\n",
        encoding="utf-8",
    )
    print("Stage 3 complete in", round(time.time() - t0, 1), "s ->", OUT_DIR)


if __name__ == "__main__":
    main()
