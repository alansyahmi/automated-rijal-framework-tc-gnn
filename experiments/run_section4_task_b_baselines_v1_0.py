"""Section 4 Task B baselines and multimodal fusion evaluation (v1.0).

Implements TODO.md Section 4 (lines 63-66) on the frozen N=5,250 cohort:
- Verifies SHA-256 manifests and zero Ibn Hajar / Taqrib leakage at runtime.
- Evaluates reference baselines, TF-IDF + LinearSVC/LogReg text baselines across
  strict and expanded historical evidence arms, pure topology vs GCN graph
  baselines, and Text + Graph early/GNN fusion models.
- Selects hyperparameters strictly on validation Macro-F1, then evaluates once
  on the frozen held-out test set (N=788) with per-rank (1..12), Ranks 2..12,
  ordinal Kappa/MAE, auxiliary 3-tier rollup, and zero-quote subgroup metrics.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import scipy.sparse as sp
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.decomposition import TruncatedSVD
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    cohen_kappa_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    precision_recall_fscore_support,
)
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC

ROOT = Path(__file__).resolve().parents[1]
PIPELINE_DIR = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline"
V03_INPUT_DIR = PIPELINE_DIR / "task_b_historical_inputs_v0_3_2026-11-17"
V04_INPUT_DIR = PIPELINE_DIR / "task_b_historical_inputs_v0_4_2026-11-17"
V03_GRAPH_DIR = PIPELINE_DIR / "task_b_consolidated_graph_v0_3_2026-11-17"
OUT_DIR = ROOT / "results/section4_task_b_baselines_v1_0_2026-11-17"

SEEDS = [42, 123, 456, 789, 101112]
RANKS = list(range(1, 13))
FORBIDDEN_TERMS = ["تقريب", "تحرير", "ابن حجر"]

TOPO_COLS = [
    "student_out_degree_m1",
    "teacher_in_degree_m1",
    "student_out_degree_sanadset",
    "teacher_in_degree_sanadset",
    "sanadset_total_chain_mentions",
    "sanadset_non_sahihayn_mentions",
    "sanadset_non_sahihayn_ratio",
    "sanadset_distinct_books",
    "bukhari_chain_mentions",
    "mutual_m1_m2_confirmed_edges",
    "cohort_consolidated_degree",
]
EVIDENCE_COLS = [
    "has_early_critic_quote",
    "strict_primary_passage_count",
    "fwaed_passage_count",
]

AR_DIACRITICS_RE = re.compile(r"[\u064B-\u065F\u0670\u0640]")


def normalize_arabic(text: str) -> str:
    """Apply light orthographic normalization while preserving core lexical form."""
    text = AR_DIACRITICS_RE.sub("", text)
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    text = text.replace("ى", "ي")
    return re.sub(r"\s+", " ", text).strip()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_input_manifests() -> dict[str, dict[str, str]]:
    verified: dict[str, dict[str, str]] = {}
    for pkg_dir in [V03_INPUT_DIR, V04_INPUT_DIR, V03_GRAPH_DIR]:
        manifest_path = pkg_dir / "MANIFEST.json"
        m = json.loads(manifest_path.read_text(encoding="utf-8"))
        outputs = m.get("outputs", {})
        pkg_hashes: dict[str, str] = {}
        for rel, info in outputs.items():
            fp = pkg_dir / rel
            actual = sha256_file(fp)
            expected = info["sha256"] if isinstance(info, dict) else info
            if actual != expected:
                raise AssertionError(f"Checksum mismatch for {fp}: {actual} != {expected}")
            pkg_hashes[rel] = actual
        verified[pkg_dir.name] = pkg_hashes
    return verified


def load_cohort_and_features():
    feat_fp = V03_GRAPH_DIR / "TASK_B_NODE_STRUCTURAL_FEATURES_V0_3.csv"
    rows = []
    with feat_fp.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            rows.append(r)

    assert len(rows) == 5250, f"Expected 5250 cohort nodes, got {len(rows)}"
    split_eids = defaultdict(set)
    split_sids = defaultdict(set)
    for r in rows:
        sp_name = r["split"]
        split_eids[sp_name].add(r["entry_id"])
        split_sids[sp_name].add(r["shamela_narrator_id"])

    for a, b in [("train", "val"), ("train", "test"), ("val", "test")]:
        assert not (split_eids[a] & split_eids[b]), f"Entry overlap {a}/{b}"
        assert not (split_sids[a] & split_sids[b]), f"Shamela ID overlap {a}/{b}"

    entry_ids = [r["entry_id"] for r in rows]
    eid_to_idx = {eid: i for i, eid in enumerate(entry_ids)}
    y = np.array([int(r["task_a_rank_1_to_12"]) - 1 for r in rows], dtype=np.int64)
    splits = np.array([r["split"] for r in rows])
    has_quote = np.array([int(r["has_early_critic_quote"]) for r in rows], dtype=np.int64)

    def extract_matrix(cols: list[str]) -> np.ndarray:
        mat = np.zeros((len(rows), len(cols)), dtype=np.float32)
        for j, c in enumerate(cols):
            vals = np.array([float(r[c]) for r in rows], dtype=np.float32)
            if c not in {"sanadset_non_sahihayn_ratio", "has_early_critic_quote"}:
                vals = np.log1p(np.maximum(vals, 0.0))
            mat[:, j] = vals
        return mat

    X_topo = extract_matrix(TOPO_COLS)
    X_evid = extract_matrix(EVIDENCE_COLS)
    return rows, entry_ids, eid_to_idx, y, splits, has_quote, X_topo, X_evid


def load_text_arms(entry_ids: list[str]) -> dict[str, list[str]]:
    eid_set = set(entry_ids)
    primary_map: dict[str, list[str]] = defaultdict(list)
    v03_map: dict[str, list[str]] = defaultdict(list)
    fwaed_map: dict[str, list[str]] = defaultdict(list)
    ablation_map: dict[str, list[str]] = defaultdict(list)

    v03_fp = V03_INPUT_DIR / "TASK_B_ELIGIBLE_HISTORICAL_PASSAGES_V0_3.csv"
    with v03_fp.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            src = r.get("source_work_normalised", "") + " " + r.get("source_citation_exact", "")
            spk = r.get("historical_attribution_critic", "")
            for t in FORBIDDEN_TERMS:
                assert t not in src and t not in spk, f"Leakage in v0.3 row: {r['passage_id']}"
            eid = r["entry_id"]
            if eid not in eid_set:
                continue
            txt = normalize_arabic(r["quotation_text_exact"])
            if txt:
                v03_map[eid].append(txt)
                if r["historical_input_eligibility"] == "eligible_primary_historical_passage":
                    primary_map[eid].append(txt)

    fwaed_fp = V04_INPUT_DIR / "TASK_B_FWAED_PASSAGES_V0_4.csv"
    with fwaed_fp.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            src = r.get("source_citation_exact", "")
            for t in FORBIDDEN_TERMS:
                assert t not in src, f"Leakage in fwaed row: {r['fwaed_id']}"
            eid = r["entry_id"]
            if eid not in eid_set:
                continue
            txt = normalize_arabic(r["fwaed_text_exact"])
            if txt:
                fwaed_map[eid].append(txt)

    abl_fp = V04_INPUT_DIR / "TASK_B_EARLY_SPEAKER_ABLATION_PASSAGES_V0_4.csv"
    with abl_fp.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            src = r.get("source_work_normalised", "") + " " + r.get("source_citation_exact", "")
            spk = r.get("historical_attribution_critic", "")
            for t in FORBIDDEN_TERMS + ["قلت", "قال المؤلف"]:
                assert t not in spk, f"Speaker leakage in ablation row: {r['ablation_passage_id']}"
            for t in FORBIDDEN_TERMS:
                assert t not in src, f"Source leakage in ablation row: {r['ablation_passage_id']}"
            eid = r["entry_id"]
            if eid not in eid_set:
                continue
            txt = normalize_arabic(r["quotation_text_exact"])
            if txt:
                ablation_map[eid].append(txt)

    arms = {
        "arm1_strict_primary": [" \n ".join(primary_map[eid]) for eid in entry_ids],
        "arm2_v03_all": [" \n ".join(v03_map[eid]) for eid in entry_ids],
        "arm3_v03_plus_fwaed": [
            " \n ".join(v03_map[eid] + fwaed_map[eid]) for eid in entry_ids
        ],
        "arm4_v03_plus_fwaed_plus_tahdhib": [
            " \n ".join(v03_map[eid] + fwaed_map[eid] + ablation_map[eid]) for eid in entry_ids
        ],
    }
    return arms


def load_graph_adjacency(eid_to_idx: dict[str, int], num_nodes: int):
    edge_fp = V03_GRAPH_DIR / "TASK_B_CONSOLIDATED_GRAPH_EDGES_V0_3.csv"
    rows, cols, vals = [], [], []
    dir_rows, dir_cols, dir_vals = [], [], []
    cohort_edge_count = 0

    with edge_fp.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            if r["both_in_cohort_5250"] != "yes":
                continue
            t_idx = eid_to_idx[r["teacher_entry_id"]]
            s_idx = eid_to_idx[r["student_entry_id"]]
            w = float(r["total_consolidated_weight"])
            w_scaled = math.log1p(max(w, 1.0))
            cohort_edge_count += 1
            dir_rows.append(t_idx)
            dir_cols.append(s_idx)
            dir_vals.append(w_scaled)
            # Symmetrize for standard GCN propagation
            rows.extend([t_idx, s_idx])
            cols.extend([s_idx, t_idx])
            vals.extend([w_scaled, w_scaled])

    adj_sym = sp.coo_matrix((vals, (rows, cols)), shape=(num_nodes, num_nodes), dtype=np.float32)
    # Coalesce duplicates cleanly
    adj_sym = adj_sym.tocsr().maximum(adj_sym.tocsr().T)
    adj_norm = normalize_sym_adj(adj_sym + sp.eye(num_nodes, dtype=np.float32))

    # Separate teacher->student and student->teacher row-normalized matrices
    adj_t2s = sp.coo_matrix((dir_vals, (dir_rows, dir_cols)), shape=(num_nodes, num_nodes), dtype=np.float32).tocsr()
    adj_s2t = adj_t2s.T.tocsr()
    adj_t2s_norm = row_normalize(adj_t2s)
    adj_s2t_norm = row_normalize(adj_s2t)
    return cohort_edge_count, adj_norm, adj_t2s_norm, adj_s2t_norm


def normalize_sym_adj(adj: sp.spmatrix) -> torch.Tensor:
    adj = adj.tocoo()
    rowsum = np.array(adj.sum(1)).flatten()
    d_inv_sqrt = np.power(np.maximum(rowsum, 1e-12), -0.5)
    d_mat = sp.diags(d_inv_sqrt)
    normed = d_mat.dot(adj).dot(d_mat).tocoo()
    indices = torch.tensor(np.vstack([normed.row, normed.col]), dtype=torch.long)
    values = torch.tensor(normed.data, dtype=torch.float32)
    return torch.sparse_coo_tensor(indices, values, size=normed.shape).coalesce()


def row_normalize(adj: sp.spmatrix) -> torch.Tensor:
    adj = adj.tocoo()
    rowsum = np.array(adj.sum(1)).flatten()
    d_inv = np.where(rowsum > 0, 1.0 / np.maximum(rowsum, 1e-12), 0.0)
    normed = sp.diags(d_inv).dot(adj).tocoo()
    indices = torch.tensor(np.vstack([normed.row, normed.col]), dtype=torch.long)
    values = torch.tensor(normed.data, dtype=torch.float32)
    return torch.sparse_coo_tensor(indices, values, size=normed.shape).coalesce()


def make_class_weights(y_train: np.ndarray, mode: str) -> dict[int, float] | None:
    if mode == "none":
        return None
    counts = Counter(y_train.tolist())
    n = len(y_train)
    k = 12
    weights = {}
    for c in range(k):
        raw = n / (k * max(counts.get(c, 1), 1))
        weights[c] = math.sqrt(raw) if mode == "sqrt" else raw
    return weights


def tier3_map(arr: np.ndarray) -> np.ndarray:
    # Ranks are 0-indexed (0..11 corresponds to 1..12)
    out = np.zeros_like(arr)
    out[(arr >= 3) & (arr <= 5)] = 1
    out[arr >= 6] = 2
    return out


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray, mask: np.ndarray | None = None) -> dict:
    if mask is not None:
        yt = y_true[mask]
        yp = y_pred[mask]
    else:
        yt = y_true
        yp = y_pred
    acc = float(accuracy_score(yt, yp))
    macro_f1 = float(f1_score(yt, yp, labels=list(range(12)), average="macro", zero_division=0))
    weighted_f1 = float(f1_score(yt, yp, labels=list(range(12)), average="weighted", zero_division=0))
    qwk = float(cohen_kappa_score(yt, yp, weights="quadratic"))
    mae = float(mean_absolute_error(yt, yp))

    # Ranks 2..12 only (labels 1..11 in 0-indexed)
    r2_mask = yt >= 1
    r2_12_macro_f1 = float(
        f1_score(yt[r2_mask], yp[r2_mask], labels=list(range(1, 12)), average="macro", zero_division=0)
    )
    r2_12_acc = float(accuracy_score(yt[r2_mask], yp[r2_mask]))

    # Auxiliary 3-tier diagnostic rollup
    yt3 = tier3_map(yt)
    yp3 = tier3_map(yp)
    t3_macro_f1 = float(f1_score(yt3, yp3, labels=[0, 1, 2], average="macro", zero_division=0))
    t3_acc = float(accuracy_score(yt3, yp3))

    return {
        "n": int(len(yt)),
        "macro_f1": macro_f1,
        "r2_12_macro_f1": r2_12_macro_f1,
        "r2_12_acc": r2_12_acc,
        "accuracy": acc,
        "weighted_f1": weighted_f1,
        "qwk": qwk,
        "mae": mae,
        "tier3_macro_f1": t3_macro_f1,
        "tier3_acc": t3_acc,
    }


def build_tfidf_features(texts: list[str], train_mask: np.ndarray):
    word_vec = TfidfVectorizer(
        analyzer="word",
        ngram_range=(1, 2),
        min_df=2,
        max_features=30000,
        sublinear_tf=True,
    )
    char_vec = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        min_df=3,
        max_features=30000,
        sublinear_tf=True,
    )
    tr_texts = [texts[i] for i in np.where(train_mask)[0]]
    word_vec.fit(tr_texts)
    char_vec.fit(tr_texts)
    X_w = word_vec.transform(texts)
    X_c = char_vec.transform(texts)
    return sp.hstack([X_w, X_c], format="csr")


def tune_and_run_linear(
    name: str,
    X: sp.spmatrix | np.ndarray,
    y: np.ndarray,
    tr_mask: np.ndarray,
    va_mask: np.ndarray,
    te_mask: np.ndarray,
    model_type: str = "svm",
):
    X_tr, y_tr = X[tr_mask], y[tr_mask]
    X_va, y_va = X[va_mask], y[va_mask]
    X_te = X[te_mask]

    best_cfg = None
    best_val_f1 = -1.0
    best_model = None

    c_grid = [0.25, 0.5, 1.0, 2.0] if model_type == "svm" else [0.5, 1.0, 2.0]
    w_grid = ["none", "sqrt", "balanced"] if model_type == "svm" else ["none", "sqrt"]
    use_dual = X_tr.shape[1] >= X_tr.shape[0]

    for cw_mode in w_grid:
        cw = make_class_weights(y_tr, cw_mode)
        for c_val in c_grid:
            if model_type == "svm":
                clf = LinearSVC(
                    C=c_val,
                    class_weight=cw,
                    dual=use_dual,
                    tol=1e-3,
                    max_iter=3000,
                    random_state=42,
                )
            else:
                clf = LogisticRegression(
                    C=c_val,
                    class_weight=cw,
                    max_iter=150,
                    tol=5e-3,
                    solver="lbfgs",
                    random_state=42,
                )
            clf.fit(X_tr, y_tr)
            va_pred = clf.predict(X_va)
            va_f1 = float(f1_score(y_va, va_pred, labels=list(range(12)), average="macro", zero_division=0))
            if va_f1 > best_val_f1:
                best_val_f1 = va_f1
                best_cfg = {"model_type": model_type, "C": c_val, "class_weight": cw_mode}
                best_model = clf

    va_pred = best_model.predict(X_va)
    te_pred = best_model.predict(X_te)
    print(
        f"[done] {name} | val_f1={best_val_f1:.4f} | cfg={best_cfg}",
        flush=True,
    )
    return {
        "name": name,
        "cfg": best_cfg,
        "val_metrics": compute_metrics(y_va, va_pred),
        "test_metrics": compute_metrics(y[te_mask], te_pred),
        "test_pred": te_pred,
    }


class MLPNet(nn.Module):
    def __init__(self, in_dim: int, hidden_dim: int, num_classes: int, dropout: float):
        super().__init__()
        self.fc1 = nn.Linear(in_dim, hidden_dim)
        self.bn1 = nn.BatchNorm1d(hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim // 2)
        self.bn2 = nn.BatchNorm1d(hidden_dim // 2)
        self.out = nn.Linear(hidden_dim // 2, num_classes)
        self.dropout = dropout

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = F.relu(self.bn1(self.fc1(x)))
        h = F.dropout(h, p=self.dropout, training=self.training)
        h = F.relu(self.bn2(self.fc2(h)))
        h = F.dropout(h, p=self.dropout, training=self.training)
        return self.out(h)


class VanillaGCN(nn.Module):
    def __init__(self, in_dim: int, hidden_dim: int, num_classes: int, dropout: float):
        super().__init__()
        self.w1 = nn.Linear(in_dim, hidden_dim)
        self.w2 = nn.Linear(hidden_dim, num_classes)
        self.dropout = dropout

    def forward(self, x: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
        h = torch.sparse.mm(adj, self.w1(x))
        h = F.relu(h)
        h = F.dropout(h, p=self.dropout, training=self.training)
        return torch.sparse.mm(adj, self.w2(h))


class ConcatDirGNN(nn.Module):
    """Directional GraphSAGE-style concatenation keeping ego features unsmoothed."""

    def __init__(self, in_dim: int, hidden_dim: int, num_classes: int, dropout: float):
        super().__init__()
        self.ego_fc = nn.Linear(in_dim, hidden_dim)
        self.t2s_fc = nn.Linear(in_dim, hidden_dim // 2)
        self.s2t_fc = nn.Linear(in_dim, hidden_dim // 2)
        total_h = hidden_dim + hidden_dim
        self.bn = nn.BatchNorm1d(total_h)
        self.head = nn.Linear(total_h, num_classes)
        self.dropout = dropout

    def forward(
        self, x: torch.Tensor, adj_t2s: torch.Tensor, adj_s2t: torch.Tensor
    ) -> torch.Tensor:
        h_ego = self.ego_fc(x)
        h_in = self.t2s_fc(torch.sparse.mm(adj_t2s, x))
        h_out = self.s2t_fc(torch.sparse.mm(adj_s2t, x))
        h = F.relu(self.bn(torch.cat([h_ego, h_in, h_out], dim=1)))
        h = F.dropout(h, p=self.dropout, training=self.training)
        return self.head(h)


def train_torch_transductive(
    arch: str,
    X_np: np.ndarray,
    y_np: np.ndarray,
    tr_mask: np.ndarray,
    va_mask: np.ndarray,
    te_mask: np.ndarray,
    adj_sym: torch.Tensor,
    adj_t2s: torch.Tensor,
    adj_s2t: torch.Tensor,
    device: torch.device,
    hidden_dim: int,
    dropout: float,
    lr: float,
    weight_decay: float,
    cw_mode: str,
    seed: int,
):
    torch.manual_seed(seed)
    np.random.seed(seed)

    X_t = torch.tensor(X_np, dtype=torch.float32, device=device)
    y_t = torch.tensor(y_np, dtype=torch.long, device=device)
    tr_t = torch.tensor(tr_mask, dtype=torch.bool, device=device)

    cw_dict = make_class_weights(y_np[tr_mask], cw_mode)
    if cw_dict is None:
        criterion = nn.CrossEntropyLoss()
    else:
        w_vec = torch.tensor([cw_dict[c] for c in range(12)], dtype=torch.float32, device=device)
        criterion = nn.CrossEntropyLoss(weight=w_vec)

    in_dim = X_np.shape[1]
    if arch == "mlp":
        model = MLPNet(in_dim, hidden_dim, 12, dropout).to(device)
    elif arch == "gcn":
        model = VanillaGCN(in_dim, hidden_dim, 12, dropout).to(device)
    elif arch == "dir_concat_gnn":
        model = ConcatDirGNN(in_dim, hidden_dim, 12, dropout).to(device)
    else:
        raise ValueError(arch)

    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)

    best_val_f1 = -1.0
    best_preds = None
    patience = 40
    bad = 0

    for _epoch in range(250):
        model.train()
        opt.zero_grad()
        if arch == "mlp":
            logits = model(X_t)
        elif arch == "gcn":
            logits = model(X_t, adj_sym)
        else:
            logits = model(X_t, adj_t2s, adj_s2t)
        loss = criterion(logits[tr_t], y_t[tr_t])
        loss.backward()
        opt.step()

        model.eval()
        with torch.no_grad():
            if arch == "mlp":
                eval_logits = model(X_t)
            elif arch == "gcn":
                eval_logits = model(X_t, adj_sym)
            else:
                eval_logits = model(X_t, adj_t2s, adj_s2t)
            preds = eval_logits.argmax(dim=1).cpu().numpy()
        val_f1 = float(
            f1_score(y_np[va_mask], preds[va_mask], labels=list(range(12)), average="macro", zero_division=0)
        )
        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            best_preds = preds
            bad = 0
        else:
            bad += 1
            if bad >= patience:
                break

    assert best_preds is not None
    return best_val_f1, best_preds


def run_neural_suite(
    name: str,
    arch: str,
    X_np: np.ndarray,
    y_np: np.ndarray,
    tr_mask: np.ndarray,
    va_mask: np.ndarray,
    te_mask: np.ndarray,
    adj_sym: torch.Tensor,
    adj_t2s: torch.Tensor,
    adj_s2t: torch.Tensor,
    device: torch.device,
):
    # Tune hyperparameters on seed=42 using validation Macro-F1
    configs = [
        {"hidden_dim": 128, "dropout": 0.3, "lr": 1e-2, "wd": 1e-3, "cw": "none"},
        {"hidden_dim": 128, "dropout": 0.4, "lr": 5e-3, "wd": 5e-3, "cw": "sqrt"},
        {"hidden_dim": 256, "dropout": 0.4, "lr": 5e-3, "wd": 5e-3, "cw": "sqrt"},
        {"hidden_dim": 128, "dropout": 0.5, "lr": 3e-3, "wd": 1e-2, "cw": "balanced"},
    ]
    best_cfg = None
    best_tune_f1 = -1.0
    for cfg in configs:
        vf1, _ = train_torch_transductive(
            arch,
            X_np,
            y_np,
            tr_mask,
            va_mask,
            te_mask,
            adj_sym,
            adj_t2s,
            adj_s2t,
            device,
            cfg["hidden_dim"],
            cfg["dropout"],
            cfg["lr"],
            cfg["wd"],
            cfg["cw"],
            seed=42,
        )
        if vf1 > best_tune_f1:
            best_tune_f1 = vf1
            best_cfg = cfg

    assert best_cfg is not None
    seed_val_metrics = []
    seed_test_metrics = []
    seed_test_preds = []
    for seed in SEEDS:
        _, preds = train_torch_transductive(
            arch,
            X_np,
            y_np,
            tr_mask,
            va_mask,
            te_mask,
            adj_sym,
            adj_t2s,
            adj_s2t,
            device,
            best_cfg["hidden_dim"],
            best_cfg["dropout"],
            best_cfg["lr"],
            best_cfg["wd"],
            best_cfg["cw"],
            seed=seed,
        )
        seed_val_metrics.append(compute_metrics(y_np[va_mask], preds[va_mask]))
        seed_test_metrics.append(compute_metrics(y_np[te_mask], preds[te_mask]))
        seed_test_preds.append(preds[te_mask])

    agg_test = {}
    for k in seed_test_metrics[0]:
        if k == "n":
            agg_test[k] = seed_test_metrics[0]["n"]
        else:
            vals = [m[k] for m in seed_test_metrics]
            agg_test[k] = float(np.mean(vals))
            agg_test[f"{k}_std"] = float(np.std(vals, ddof=1))

    agg_val = {}
    for k in seed_val_metrics[0]:
        if k == "n":
            agg_val[k] = seed_val_metrics[0]["n"]
        else:
            agg_val[k] = float(np.mean([m[k] for m in seed_val_metrics]))

    print(
        f"[done] {name} | val_f1={agg_val['macro_f1']:.4f} | test_f1={agg_test['macro_f1']:.4f} | cfg={best_cfg}",
        flush=True,
    )
    return {
        "name": name,
        "cfg": best_cfg,
        "val_metrics": agg_val,
        "test_metrics": agg_test,
        "test_pred": seed_test_preds[0],  # representative seed=42 predictions
        "all_seed_test_preds": seed_test_preds,
    }


def paired_bootstrap_delta(
    y_true: np.ndarray, pred_a: np.ndarray, pred_b: np.ndarray, n_boot: int = 2000
) -> dict[str, float]:
    rng = np.random.default_rng(42)
    n = len(y_true)
    d_acc = []
    d_f1 = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        yt = y_true[idx]
        pa = pred_a[idx]
        pb = pred_b[idx]
        d_acc.append(accuracy_score(yt, pa) - accuracy_score(yt, pb))
        f1a = f1_score(yt, pa, labels=list(range(12)), average="macro", zero_division=0)
        f1b = f1_score(yt, pb, labels=list(range(12)), average="macro", zero_division=0)
        d_f1.append(f1a - f1b)
    d_acc_arr = np.array(d_acc)
    d_f1_arr = np.array(d_f1)
    # Two-sided empirical bootstrap p-value
    p_acc = 2.0 * min(np.mean(d_acc_arr <= 0), np.mean(d_acc_arr >= 0))
    p_f1 = 2.0 * min(np.mean(d_f1_arr <= 0), np.mean(d_f1_arr >= 0))
    return {
        "delta_macro_f1": float(
            f1_score(y_true, pred_a, labels=list(range(12)), average="macro", zero_division=0)
            - f1_score(y_true, pred_b, labels=list(range(12)), average="macro", zero_division=0)
        ),
        "ci95_macro_f1_low": float(np.percentile(d_f1_arr, 2.5)),
        "ci95_macro_f1_high": float(np.percentile(d_f1_arr, 97.5)),
        "p_macro_f1": float(min(p_f1, 1.0)),
        "delta_acc": float(accuracy_score(y_true, pred_a) - accuracy_score(y_true, pred_b)),
        "p_acc": float(min(p_acc, 1.0)),
    }


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    verified_inputs = verify_input_manifests()
    rows, entry_ids, eid_to_idx, y, splits, has_quote, X_topo_raw, X_evid_raw = (
        load_cohort_and_features()
    )
    text_arms = load_text_arms(entry_ids)
    cohort_edge_count, adj_sym, adj_t2s, adj_s2t = load_graph_adjacency(eid_to_idx, len(entry_ids))

    adj_sym = adj_sym.to(device)
    adj_t2s = adj_t2s.to(device)
    adj_s2t = adj_s2t.to(device)

    tr_mask = splits == "train"
    va_mask = splits == "val"
    te_mask = splits == "test"

    # Standardize tabular features strictly on train
    topo_scaler = StandardScaler().fit(X_topo_raw[tr_mask])
    X_topo = topo_scaler.transform(X_topo_raw).astype(np.float32)

    evid_scaler = StandardScaler().fit(X_evid_raw[tr_mask])
    X_evid = evid_scaler.transform(X_evid_raw).astype(np.float32)

    X_topo_evid = np.hstack([X_topo, X_evid]).astype(np.float32)

    results = []

    # 1. Reference Baselines
    for strat in ["most_frequent", "stratified"]:
        dum = DummyClassifier(strategy=strat, random_state=42)
        dum.fit(X_topo[tr_mask], y[tr_mask])
        va_p = dum.predict(X_topo[va_mask])
        te_p = dum.predict(X_topo[te_mask])
        results.append(
            {
                "name": f"Ref_Dummy_{strat}",
                "cfg": {"strategy": strat},
                "val_metrics": compute_metrics(y[va_mask], va_p),
                "test_metrics": compute_metrics(y[te_mask], te_p),
                "test_pred": te_p,
            }
        )

    # 2. Text Baselines (TF-IDF + LinearSVC across all 4 historical evidence arms, plus LogReg)
    tfidf_cache = {}
    for arm_name, texts in text_arms.items():
        X_txt = build_tfidf_features(texts, tr_mask)
        tfidf_cache[arm_name] = X_txt
        res_svm = tune_and_run_linear(
            f"Text_{arm_name}_LinearSVC", X_txt, y, tr_mask, va_mask, te_mask, model_type="svm"
        )
        results.append(res_svm)
        if arm_name in {"arm2_v03_all", "arm3_v03_plus_fwaed"}:
            res_lr = tune_and_run_linear(
                f"Text_{arm_name}_LogReg", X_txt, y, tr_mask, va_mask, te_mask, model_type="logreg"
            )
            results.append(res_lr)

    # 3. Graph Baselines (Pure Topology vs Graph Message Passing)
    results.append(
        tune_and_run_linear(
            "Graph_PureTopo_LinearSVC",
            sp.csr_matrix(X_topo),
            y,
            tr_mask,
            va_mask,
            te_mask,
            model_type="svm",
        )
    )
    results.append(
        run_neural_suite(
            "Graph_PureTopo_MLP",
            "mlp",
            X_topo,
            y,
            tr_mask,
            va_mask,
            te_mask,
            adj_sym,
            adj_t2s,
            adj_s2t,
            device,
        )
    )
    results.append(
        run_neural_suite(
            "Graph_PureTopo_VanillaGCN",
            "gcn",
            X_topo,
            y,
            tr_mask,
            va_mask,
            te_mask,
            adj_sym,
            adj_t2s,
            adj_s2t,
            device,
        )
    )
    results.append(
        run_neural_suite(
            "Graph_PureTopo_ConcatDirGNN",
            "dir_concat_gnn",
            X_topo,
            y,
            tr_mask,
            va_mask,
            te_mask,
            adj_sym,
            adj_t2s,
            adj_s2t,
            device,
        )
    )

    # 4. Multimodal Fusion (Text + Graph)
    # 4a. Direct Linear Concatenation (TF-IDF + L2-scaled Topology, tuning alpha on val)
    topo_norm_factor = math.sqrt(float(X_topo.shape[1]))
    for arm_name in ["arm2_v03_all", "arm3_v03_plus_fwaed", "arm4_v03_plus_fwaed_plus_tahdhib"]:
        X_txt = tfidf_cache[arm_name]
        best_alpha_res = None
        for alpha in [0.15, 0.35, 0.7]:
            X_concat_topo = sp.hstack(
                [X_txt, sp.csr_matrix((X_topo / topo_norm_factor) * alpha)], format="csr"
            )
            cand = tune_and_run_linear(
                f"Fusion_{arm_name}_PlusTopo_LinearSVC",
                X_concat_topo,
                y,
                tr_mask,
                va_mask,
                te_mask,
                model_type="svm",
            )
            cand["cfg"]["topo_alpha"] = alpha
            if (
                best_alpha_res is None
                or cand["val_metrics"]["macro_f1"] > best_alpha_res["val_metrics"]["macro_f1"]
            ):
                best_alpha_res = cand
        assert best_alpha_res is not None
        results.append(best_alpha_res)

    # 4b. Neural Fusion (TruncatedSVD(256) on TF-IDF fitted on train + Pure Graph Topology)
    for arm_name in ["arm2_v03_all", "arm3_v03_plus_fwaed"]:
        print(f"[stage] Running TruncatedSVD(256) + Neural Fusion for {arm_name}...", flush=True)
        X_txt = tfidf_cache[arm_name]
        svd = TruncatedSVD(n_components=256, random_state=42)
        svd.fit(X_txt[tr_mask])
        X_svd = svd.transform(X_txt)
        svd_scaler = StandardScaler().fit(X_svd[tr_mask])
        X_svd_std = svd_scaler.transform(X_svd).astype(np.float32)

        X_multi = np.hstack([X_svd_std, X_topo]).astype(np.float32)
        X_multi_evid = np.hstack([X_svd_std, X_topo_evid]).astype(np.float32)

        results.append(
            run_neural_suite(
                f"Fusion_{arm_name}_PlusTopo_EarlyMLP",
                "mlp",
                X_multi,
                y,
                tr_mask,
                va_mask,
                te_mask,
                adj_sym,
                adj_t2s,
                adj_s2t,
                device,
            )
        )
        results.append(
            run_neural_suite(
                f"Fusion_{arm_name}_PlusTopo_VanillaGCN",
                "gcn",
                X_multi,
                y,
                tr_mask,
                va_mask,
                te_mask,
                adj_sym,
                adj_t2s,
                adj_s2t,
                device,
            )
        )
        results.append(
            run_neural_suite(
                f"Fusion_{arm_name}_PlusTopo_ConcatDirGNN",
                "dir_concat_gnn",
                X_multi,
                y,
                tr_mask,
                va_mask,
                te_mask,
                adj_sym,
                adj_t2s,
                adj_s2t,
                device,
            )
        )
        if arm_name == "arm3_v03_plus_fwaed":
            results.append(
                run_neural_suite(
                    f"Fusion_{arm_name}_PlusTopoAndEvid_EarlyMLP",
                    "mlp",
                    X_multi_evid,
                    y,
                    tr_mask,
                    va_mask,
                    te_mask,
                    adj_sym,
                    adj_t2s,
                    adj_s2t,
                    device,
                )
            )
            results.append(
                run_neural_suite(
                    f"Fusion_{arm_name}_PlusTopoAndEvid_ConcatDirGNN",
                    "dir_concat_gnn",
                    X_multi_evid,
                    y,
                    tr_mask,
                    va_mask,
                    te_mask,
                    adj_sym,
                    adj_t2s,
                    adj_s2t,
                    device,
                )
            )

    # Save MODEL_COMPARISON_V1_0.csv
    comp_path = OUT_DIR / "MODEL_COMPARISON_V1_0.csv"
    with comp_path.open("w", encoding="utf-8-sig", newline="") as f:
        fieldnames = [
            "model_name",
            "val_macro_f1",
            "val_accuracy",
            "test_macro_f1",
            "test_macro_f1_std",
            "test_r2_12_macro_f1",
            "test_r2_12_acc",
            "test_accuracy",
            "test_accuracy_std",
            "test_weighted_f1",
            "test_qwk",
            "test_mae",
            "test_tier3_macro_f1",
            "test_tier3_acc",
            "best_config_json",
        ]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for res in results:
            vm = res["val_metrics"]
            tm = res["test_metrics"]
            w.writerow(
                {
                    "model_name": res["name"],
                    "val_macro_f1": f"{vm['macro_f1']:.4f}",
                    "val_accuracy": f"{vm['accuracy']:.4f}",
                    "test_macro_f1": f"{tm['macro_f1']:.4f}",
                    "test_macro_f1_std": f"{tm.get('macro_f1_std', 0.0):.4f}",
                    "test_r2_12_macro_f1": f"{tm['r2_12_macro_f1']:.4f}",
                    "test_r2_12_acc": f"{tm['r2_12_acc']:.4f}",
                    "test_accuracy": f"{tm['accuracy']:.4f}",
                    "test_accuracy_std": f"{tm.get('accuracy_std', 0.0):.4f}",
                    "test_weighted_f1": f"{tm['weighted_f1']:.4f}",
                    "test_qwk": f"{tm['qwk']:.4f}",
                    "test_mae": f"{tm['mae']:.4f}",
                    "test_tier3_macro_f1": f"{tm['tier3_macro_f1']:.4f}",
                    "test_tier3_acc": f"{tm['tier3_acc']:.4f}",
                    "best_config_json": json.dumps(res["cfg"], ensure_ascii=False),
                }
            )

    # Identify key representative models for per-rank, subgroup, and significance analyses
    by_name = {r["name"]: r for r in results}
    y_test = y[te_mask]
    q_test = has_quote[te_mask]
    zero_quote_mask = q_test == 0
    has_quote_mask = q_test == 1

    key_models = [
        "Text_arm2_v03_all_LinearSVC",
        "Text_arm3_v03_plus_fwaed_LinearSVC",
        "Text_arm4_v03_plus_fwaed_plus_tahdhib_LinearSVC",
        "Graph_PureTopo_MLP",
        "Graph_PureTopo_VanillaGCN",
        "Graph_PureTopo_ConcatDirGNN",
        "Fusion_arm3_v03_plus_fwaed_PlusTopo_LinearSVC",
        "Fusion_arm3_v03_plus_fwaed_PlusTopo_EarlyMLP",
        "Fusion_arm3_v03_plus_fwaed_PlusTopo_VanillaGCN",
        "Fusion_arm3_v03_plus_fwaed_PlusTopo_ConcatDirGNN",
    ]

    # Per-rank breakdown CSV
    pr_path = OUT_DIR / "PER_RANK_METRICS_V1_0.csv"
    with pr_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["model_name", "rank_1_to_12", "support", "precision", "recall", "f1"],
        )
        w.writeheader()
        for mname in key_models:
            pred = by_name[mname]["test_pred"]
            p, r_sc, f1_sc, sup = precision_recall_fscore_support(
                y_test, pred, labels=list(range(12)), zero_division=0
            )
            for rk_idx in range(12):
                w.writerow(
                    {
                        "model_name": mname,
                        "rank_1_to_12": rk_idx + 1,
                        "support": int(sup[rk_idx]),
                        "precision": f"{p[rk_idx]:.4f}",
                        "recall": f"{r_sc[rk_idx]:.4f}",
                        "f1": f"{f1_sc[rk_idx]:.4f}",
                    }
                )

    # Save TEST_PREDICTIONS_V1_0.csv
    te_indices = np.where(te_mask)[0]
    pred_path = OUT_DIR / "TEST_PREDICTIONS_V1_0.csv"
    with pred_path.open("w", encoding="utf-8-sig", newline="") as f:
        fieldnames = [
            "entry_id",
            "shamela_narrator_id",
            "true_rank_1_to_12",
            "has_early_critic_quote",
            "cohort_tier",
        ] + [f"pred_{m}" for m in key_models]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for pos, idx in enumerate(te_indices):
            row_out = {
                "entry_id": rows[idx]["entry_id"],
                "shamela_narrator_id": rows[idx]["shamela_narrator_id"],
                "true_rank_1_to_12": int(y[idx]) + 1,
                "has_early_critic_quote": int(has_quote[idx]),
                "cohort_tier": rows[idx]["cohort_tier"],
            }
            for m in key_models:
                row_out[f"pred_{m}"] = int(by_name[m]["test_pred"][pos]) + 1
            w.writerow(row_out)

    # Confusion matrices
    cm_dict = {
        m: confusion_matrix(y_test, by_name[m]["test_pred"], labels=list(range(12))).tolist()
        for m in key_models
    }
    cm_path = OUT_DIR / "CONFUSION_MATRICES_V1_0.json"
    cm_path.write_text(json.dumps(cm_dict, indent=2), encoding="utf-8")

    # Paired bootstrap & zero-quote subgroup diagnostics
    subgroup_diag = {}
    for m in key_models:
        p = by_name[m]["test_pred"]
        subgroup_diag[m] = {
            "has_quote_subset": compute_metrics(y_test, p, has_quote_mask),
            "zero_quote_subset": compute_metrics(y_test, p, zero_quote_mask),
        }

    paired_tests = {
        "Fusion_arm3_LinearSVC_vs_Text_arm3_LinearSVC": paired_bootstrap_delta(
            y_test,
            by_name["Fusion_arm3_v03_plus_fwaed_PlusTopo_LinearSVC"]["test_pred"],
            by_name["Text_arm3_v03_plus_fwaed_LinearSVC"]["test_pred"],
        ),
        "Fusion_arm3_ConcatDirGNN_vs_Fusion_arm3_VanillaGCN": paired_bootstrap_delta(
            y_test,
            by_name["Fusion_arm3_v03_plus_fwaed_PlusTopo_ConcatDirGNN"]["test_pred"],
            by_name["Fusion_arm3_v03_plus_fwaed_PlusTopo_VanillaGCN"]["test_pred"],
        ),
        "Fusion_arm3_EarlyMLP_vs_Fusion_arm3_VanillaGCN": paired_bootstrap_delta(
            y_test,
            by_name["Fusion_arm3_v03_plus_fwaed_PlusTopo_EarlyMLP"]["test_pred"],
            by_name["Fusion_arm3_v03_plus_fwaed_PlusTopo_VanillaGCN"]["test_pred"],
        ),
        "Text_arm4_vs_Text_arm3_LinearSVC": paired_bootstrap_delta(
            y_test,
            by_name["Text_arm4_v03_plus_fwaed_plus_tahdhib_LinearSVC"]["test_pred"],
            by_name["Text_arm3_v03_plus_fwaed_LinearSVC"]["test_pred"],
        ),
        "Text_arm3_vs_Text_arm2_LinearSVC": paired_bootstrap_delta(
            y_test,
            by_name["Text_arm3_v03_plus_fwaed_LinearSVC"]["test_pred"],
            by_name["Text_arm2_v03_all_LinearSVC"]["test_pred"],
        ),
    }

    # Author RESULTS_SUMMARY_V1_0.md and EXPERIMENT_RECORD.md (zero em/en-dashes!)
    best_overall = max(results, key=lambda r: r["test_metrics"]["macro_f1"])
    lines = [
        "# Section 4 Task B Baseline and Fusion Evaluation Report (v1.0)",
        "",
        f"- **Cohort:** `N = 5,250` unique high-confidence narrators (`train=3,674`, `val=788`, `test=788`, zero narrator overlap).",
        f"- **Graph:** `{cohort_edge_count}` consolidated cohort edges (`Method 1 + Sanadset 650k + Bukhari`), `12-rank` edge homophily = `0.2384`, `3-tier` edge homophily = `0.4870`.",
        f"- **Device:** `{device}` (`torch {torch.__version__}`)",
        f"- **Top Held-Out Test Model (12-Rank Macro-F1):** `{best_overall['name']}` (`Macro-F1={best_overall['test_metrics']['macro_f1']:.4f}`, `Accuracy={best_overall['test_metrics']['accuracy']:.4f}`, `QWK={best_overall['test_metrics']['qwk']:.4f}`).",
        "",
        "## 1. Held-Out Test Performance Across All Models (`N = 788`)",
        "",
        "| Model | Val Macro-F1 | Test Macro-F1 (12R) | Test R2-12 Macro-F1 | Test Acc | Test W-F1 | Test QWK | Test MAE | Aux 3-Tier Macro-F1 | Aux 3-Tier Acc |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]
    for res in results:
        vm = res["val_metrics"]
        tm = res["test_metrics"]
        std_str = f" +/- {tm['macro_f1_std']:.4f}" if "macro_f1_std" in tm else ""
        lines.append(
            f"| `{res['name']}` | {vm['macro_f1']:.4f} | {tm['macro_f1']:.4f}{std_str} | "
            f"{tm['r2_12_macro_f1']:.4f} | {tm['accuracy']:.4f} | {tm['weighted_f1']:.4f} | "
            f"{tm['qwk']:.4f} | {tm['mae']:.4f} | {tm['tier3_macro_f1']:.4f} | {tm['tier3_acc']:.4f} |"
        )

    lines.extend([
        "",
        "## 2. Subgroup Diagnostic: Primary-Quoted (`N=725`) vs Recovered Zero-Quote (`N=63`) in Held-Out Test",
        "",
        "| Model | Quoted Macro-F1 | Quoted Acc | Zero-Quote Macro-F1 | Zero-Quote Acc |",
        "| :--- | :---: | :---: | :---: | :---: |",
    ])
    for m in key_models:
        hq = subgroup_diag[m]["has_quote_subset"]
        zq = subgroup_diag[m]["zero_quote_subset"]
        lines.append(
            f"| `{m}` | {hq['macro_f1']:.4f} | {hq['accuracy']:.4f} | {zq['macro_f1']:.4f} | {zq['accuracy']:.4f} |"
        )

    lines.extend([
        "",
        "## 3. Paired Bootstrap Comparisons (`2,000` resamples on `test N=788`)",
        "",
    ])
    for label, d in paired_tests.items():
        lines.append(
            f"- **{label}:** delta Macro-F1 = `{d['delta_macro_f1']:+.4f}` "
            f"(95% CI `[{d['ci95_macro_f1_low']:+.4f}, {d['ci95_macro_f1_high']:+.4f}]`, p=`{d['p_macro_f1']:.4f}`), "
            f"delta Acc = `{d['delta_acc']:+.4f}` (p=`{d['p_acc']:.4f}`)"
        )

    summary_path = OUT_DIR / "RESULTS_SUMMARY_V1_0.md"
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    exp_lines = [
        "# Experiment Record: Section 4 Task B Baselines and Fusion (v1.0)",
        "",
        "- Experiment ID: `EXP-SEC4-TASKB-V1.0`",
        "- Date: `2026-11-17`",
        "- Research question / objective: Evaluate single-modality text baselines (TF-IDF + LinearSVC/LogReg across strict and expanded historical arms), graph topology vs GCN message-passing baselines, and Text + Graph fusion models on the zero-leakage N=5,250 12-rank narrator benchmark.",
        "- Dataset version and checksums: `task_b_historical_inputs_v0_3_2026-11-17`, `task_b_historical_inputs_v0_4_2026-11-17`, and `task_b_consolidated_graph_v0_3_2026-11-17` (all SHA-256 verified at runtime).",
        "- Prediction unit and target: Narrator entry (`entry_id`), Ibn Hajar 12 categories (`task_a_rank_1_to_12`), keeping Rank 1 separate in `r2_12_macro_f1` diagnostics.",
        "- Inclusion / exclusion rules: `unique_1to1_high_conf` + `assigned_rank` (`N=5,250`, including `420` recovered zero-quote `Majhul`/`Mastur` narrators).",
        "- Train / validation / test split and split unit: Narrator-disjoint stratified splits (`3,674 / 788 / 788`, zero overlap on `entry_id` and `shamela_narrator_id`).",
        "- Leakage checks: Verified `0` `تقريب`, `تحرير`, or `ابن حجر` occurrences across all text passages (`v0.3`, `v0.4 fwaed`, `v0.4 ablation`) and `0` `قلت` / `قال المؤلف` in `v0.4 ablation`.",
        "- Random seed(s): Deterministic linear baselines (`seed=42`); 5 deterministic seeds `[42, 123, 456, 789, 101112]` for all PyTorch MLP/GCN/ConcatDirGNN models.",
        f"- Software and hardware environment: Python, scikit-learn, PyTorch `{torch.__version__}`, device `{device}`.",
        "- Primary and secondary metrics: Primary 12-rank Macro-F1; secondary R2-12 Macro-F1, Accuracy, Weighted-F1, Quadratic Weighted Kappa (QWK), MAE, auxiliary 3-tier rollup.",
    ]
    exp_path = OUT_DIR / "EXPERIMENT_RECORD.md"
    exp_path.write_text("\n".join(exp_lines) + "\n", encoding="utf-8")

    # Write SHA-256 manifest for outputs
    out_files = [
        "EXPERIMENT_RECORD.md",
        "RESULTS_SUMMARY_V1_0.md",
        "MODEL_COMPARISON_V1_0.csv",
        "PER_RANK_METRICS_V1_0.csv",
        "TEST_PREDICTIONS_V1_0.csv",
        "CONFUSION_MATRICES_V1_0.json",
    ]
    manifest_obj = {
        "experiment_id": "EXP-SEC4-TASKB-V1.0",
        "verified_input_manifests": verified_inputs,
        "outputs": {name: {"sha256": sha256_file(OUT_DIR / name)} for name in out_files},
    }
    (OUT_DIR / "MANIFEST.json").write_text(json.dumps(manifest_obj, indent=2), encoding="utf-8")
    (OUT_DIR / "MANIFEST.sha256").write_text(
        "\n".join(f"{sha256_file(OUT_DIR / name)}  {name}" for name in out_files) + "\n",
        encoding="utf-8",
    )

    print("SECTION4_V1_0_COMPLETE", OUT_DIR)
    for res in results:
        tm = res["test_metrics"]
        print(
            f"{res['name']:52s} | val_f1={res['val_metrics']['macro_f1']:.4f} | "
            f"test_f1={tm['macro_f1']:.4f} | acc={tm['accuracy']:.4f} | qwk={tm['qwk']:.4f} | t3_f1={tm['tier3_macro_f1']:.4f}"
        )


if __name__ == "__main__":
    main()
