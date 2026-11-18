"""Targeted Experiment (v1.1): ConcatDirGNN + Out-of-Fold Sparse TF-IDF LogReg Predictions.

Tests whether feeding full-vocabulary TF-IDF LogisticRegression 12-dimensional
narrator-level out-of-fold log-probabilities (strictly leakage-free) alongside
pure graph topology into ConcatDirGNN overcomes TruncatedSVD(256) compression
loss and improves over both standalone Text_LogReg and EarlyMLP/VanillaGCN.
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
from joblib import Parallel, delayed
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
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
PIPELINE_DIR = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline"
V03_INPUT_DIR = PIPELINE_DIR / "task_b_historical_inputs_v0_3_2026-11-17"
V04_INPUT_DIR = PIPELINE_DIR / "task_b_historical_inputs_v0_4_2026-11-17"
V03_GRAPH_DIR = PIPELINE_DIR / "task_b_consolidated_graph_v0_3_2026-11-17"
V10_RESULTS_DIR = ROOT / "results/section4_task_b_baselines_v1_0_2026-11-17"
OUT_DIR = ROOT / "results/section4_oof_text_gnn_v1_1_2026-11-17"

SEEDS = [42, 123, 456, 789, 101112]
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

AR_DIACRITICS_RE = re.compile(r"[\u064B-\u065F\u0670\u0640]")


def normalize_arabic(text: str) -> str:
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
        m = json.loads((pkg_dir / "MANIFEST.json").read_text(encoding="utf-8"))
        pkg_hashes: dict[str, str] = {}
        for rel, info in m.get("outputs", {}).items():
            fp = pkg_dir / rel
            actual = sha256_file(fp)
            expected = info["sha256"] if isinstance(info, dict) else info
            if actual != expected:
                raise AssertionError(f"Checksum mismatch for {fp}: {actual} != {expected}")
            pkg_hashes[rel] = actual
        verified[pkg_dir.name] = pkg_hashes
    return verified


def load_cohort_and_topology():
    feat_fp = V03_GRAPH_DIR / "TASK_B_NODE_STRUCTURAL_FEATURES_V0_3.csv"
    with feat_fp.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 5250

    split_eids = defaultdict(set)
    split_sids = defaultdict(set)
    for r in rows:
        split_eids[r["split"]].add(r["entry_id"])
        split_sids[r["split"]].add(r["shamela_narrator_id"])
    for a, b in [("train", "val"), ("train", "test"), ("val", "test")]:
        assert not (split_eids[a] & split_eids[b])
        assert not (split_sids[a] & split_sids[b])

    entry_ids = [r["entry_id"] for r in rows]
    shamela_ids = [r["shamela_narrator_id"] for r in rows]
    eid_to_idx = {eid: i for i, eid in enumerate(entry_ids)}
    y = np.array([int(r["task_a_rank_1_to_12"]) - 1 for r in rows], dtype=np.int64)
    splits = np.array([r["split"] for r in rows])
    has_quote = np.array([int(r["has_early_critic_quote"]) for r in rows], dtype=np.int64)

    X_topo = np.zeros((len(rows), len(TOPO_COLS)), dtype=np.float32)
    for j, c in enumerate(TOPO_COLS):
        vals = np.array([float(r[c]) for r in rows], dtype=np.float32)
        if c != "sanadset_non_sahihayn_ratio":
            vals = np.log1p(np.maximum(vals, 0.0))
        X_topo[:, j] = vals

    return rows, entry_ids, shamela_ids, eid_to_idx, y, splits, has_quote, X_topo


def load_text_arms(entry_ids: list[str]) -> dict[str, list[str]]:
    eid_set = set(entry_ids)
    v03_map: dict[str, list[str]] = defaultdict(list)
    fwaed_map: dict[str, list[str]] = defaultdict(list)
    ablation_map: dict[str, list[str]] = defaultdict(list)

    with (V03_INPUT_DIR / "TASK_B_ELIGIBLE_HISTORICAL_PASSAGES_V0_3.csv").open(
        encoding="utf-8-sig", newline=""
    ) as f:
        for r in csv.DictReader(f):
            src = r.get("source_work_normalised", "") + " " + r.get("source_citation_exact", "")
            spk = r.get("historical_attribution_critic", "")
            for t in FORBIDDEN_TERMS:
                assert t not in src and t not in spk
            eid = r["entry_id"]
            if eid in eid_set:
                txt = normalize_arabic(r["quotation_text_exact"])
                if txt:
                    v03_map[eid].append(txt)

    with (V04_INPUT_DIR / "TASK_B_FWAED_PASSAGES_V0_4.csv").open(
        encoding="utf-8-sig", newline=""
    ) as f:
        for r in csv.DictReader(f):
            src = r.get("source_citation_exact", "")
            for t in FORBIDDEN_TERMS:
                assert t not in src
            eid = r["entry_id"]
            if eid in eid_set:
                txt = normalize_arabic(r["fwaed_text_exact"])
                if txt:
                    fwaed_map[eid].append(txt)

    with (V04_INPUT_DIR / "TASK_B_EARLY_SPEAKER_ABLATION_PASSAGES_V0_4.csv").open(
        encoding="utf-8-sig", newline=""
    ) as f:
        for r in csv.DictReader(f):
            src = r.get("source_work_normalised", "") + " " + r.get("source_citation_exact", "")
            spk = r.get("historical_attribution_critic", "")
            for t in FORBIDDEN_TERMS + ["قلت", "قال المؤلف"]:
                assert t not in spk
            for t in FORBIDDEN_TERMS:
                assert t not in src
            eid = r["entry_id"]
            if eid in eid_set:
                txt = normalize_arabic(r["quotation_text_exact"])
                if txt:
                    ablation_map[eid].append(txt)

    return {
        "arm2_v03_all": [" \n ".join(v03_map[eid]) for eid in entry_ids],
        "arm3_v03_plus_fwaed": [" \n ".join(v03_map[eid] + fwaed_map[eid]) for eid in entry_ids],
        "arm4_v03_plus_fwaed_plus_tahdhib": [
            " \n ".join(v03_map[eid] + fwaed_map[eid] + ablation_map[eid]) for eid in entry_ids
        ],
    }


def normalize_sym_adj(adj: sp.spmatrix) -> torch.Tensor:
    adj = adj.tocoo()
    rowsum = np.array(adj.sum(1)).flatten()
    d_inv_sqrt = np.power(np.maximum(rowsum, 1e-12), -0.5)
    normed = sp.diags(d_inv_sqrt).dot(adj).dot(sp.diags(d_inv_sqrt)).tocoo()
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


def load_graph_adjacency(eid_to_idx: dict[str, int], num_nodes: int):
    edge_fp = V03_GRAPH_DIR / "TASK_B_CONSOLIDATED_GRAPH_EDGES_V0_3.csv"
    rows, cols, vals = [], [], []
    dir_rows, dir_cols, dir_vals = [], [], []
    with edge_fp.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            if r["both_in_cohort_5250"] != "yes":
                continue
            t_idx = eid_to_idx[r["teacher_entry_id"]]
            s_idx = eid_to_idx[r["student_entry_id"]]
            w_scaled = math.log1p(max(float(r["total_consolidated_weight"]), 1.0))
            dir_rows.append(t_idx)
            dir_cols.append(s_idx)
            dir_vals.append(w_scaled)
            rows.extend([t_idx, s_idx])
            cols.extend([s_idx, t_idx])
            vals.extend([w_scaled, w_scaled])

    adj_sym = sp.coo_matrix((vals, (rows, cols)), shape=(num_nodes, num_nodes), dtype=np.float32).tocsr()
    adj_sym = adj_sym.maximum(adj_sym.T)
    adj_norm = normalize_sym_adj(adj_sym + sp.eye(num_nodes, dtype=np.float32))

    adj_t2s = sp.coo_matrix((dir_vals, (dir_rows, dir_cols)), shape=(num_nodes, num_nodes), dtype=np.float32).tocsr()
    adj_s2t = adj_t2s.T.tocsr()
    return adj_norm, row_normalize(adj_t2s), row_normalize(adj_s2t)


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
    r2_mask = yt >= 1
    yt3 = tier3_map(yt)
    yp3 = tier3_map(yp)
    return {
        "n": int(len(yt)),
        "macro_f1": float(f1_score(yt, yp, labels=list(range(12)), average="macro", zero_division=0)),
        "r2_12_macro_f1": float(
            f1_score(yt[r2_mask], yp[r2_mask], labels=list(range(1, 12)), average="macro", zero_division=0)
        ),
        "r2_12_acc": float(accuracy_score(yt[r2_mask], yp[r2_mask])),
        "accuracy": float(accuracy_score(yt, yp)),
        "weighted_f1": float(f1_score(yt, yp, labels=list(range(12)), average="weighted", zero_division=0)),
        "qwk": float(cohen_kappa_score(yt, yp, weights="quadratic")),
        "mae": float(mean_absolute_error(yt, yp)),
        "tier3_macro_f1": float(f1_score(yt3, yp3, labels=[0, 1, 2], average="macro", zero_division=0)),
        "tier3_acc": float(accuracy_score(yt3, yp3)),
    }


def fit_tfidf_logreg_predict_log_proba(
    train_texts: list[str],
    y_train: np.ndarray,
    eval_texts: list[str],
    c_val: float,
    cw_mode: str,
) -> np.ndarray:
    word_vec = TfidfVectorizer(
        analyzer="word", ngram_range=(1, 2), min_df=2, max_features=30000, sublinear_tf=True
    )
    char_vec = TfidfVectorizer(
        analyzer="char_wb", ngram_range=(3, 5), min_df=3, max_features=30000, sublinear_tf=True
    )
    X_tr = sp.hstack([word_vec.fit_transform(train_texts), char_vec.fit_transform(train_texts)], format="csr")
    X_ev = sp.hstack([word_vec.transform(eval_texts), char_vec.transform(eval_texts)], format="csr")
    cw = make_class_weights(y_train, cw_mode)
    clf = LogisticRegression(
        C=c_val, class_weight=cw, max_iter=150, tol=5e-3, solver="lbfgs", random_state=42
    )
    clf.fit(X_tr, y_train)
    assert list(clf.classes_) == list(range(12)), f"Missing classes in fold: {clf.classes_}"
    return clf.predict_log_proba(X_ev).astype(np.float32)


def generate_narrator_disjoint_oof_text_features(
    arm_name: str,
    texts: list[str],
    entry_ids: list[str],
    shamela_ids: list[str],
    y: np.ndarray,
    tr_mask: np.ndarray,
    va_mask: np.ndarray,
    te_mask: np.ndarray,
):
    """Strictly narrator-disjoint OOF inside train; full-train model for val and test."""
    tr_indices = np.where(tr_mask)[0]
    y_tr = y[tr_indices]
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    folds = list(skf.split(tr_indices, y_tr))

    # Assert strict narrator-level disjointness across every CV fold
    for fold_idx, (f_tr_pos, f_va_pos) in enumerate(folds):
        f_tr_idx = tr_indices[f_tr_pos]
        f_va_idx = tr_indices[f_va_pos]
        assert not (set(entry_ids[i] for i in f_tr_idx) & set(entry_ids[i] for i in f_va_idx))
        assert not (set(shamela_ids[i] for i in f_tr_idx) & set(shamela_ids[i] for i in f_va_idx))
        assert len(set(y[f_tr_idx].tolist())) == 12, f"Fold {fold_idx} missing class"

    # Select LogReg (C, cw_mode) strictly using train OOF Macro-F1 (zero val/test peeking!)
    best_cfg = None
    best_oof_f1 = -1.0
    best_oof_logp = None

    for cw_mode in ["none", "sqrt"]:
        for c_val in [0.5, 1.0, 2.0]:
            fold_preds = Parallel(n_jobs=5)(
                delayed(fit_tfidf_logreg_predict_log_proba)(
                    [texts[i] for i in tr_indices[f_tr_pos]],
                    y[tr_indices[f_tr_pos]],
                    [texts[i] for i in tr_indices[f_va_pos]],
                    c_val=c_val,
                    cw_mode=cw_mode,
                )
                for f_tr_pos, f_va_pos in folds
            )
            oof_logp = np.zeros((len(tr_indices), 12), dtype=np.float32)
            for (_f_tr_pos, f_va_pos), fp in zip(folds, fold_preds):
                oof_logp[f_va_pos] = fp
            oof_pred = oof_logp.argmax(axis=1)
            oof_f1 = float(f1_score(y_tr, oof_pred, labels=list(range(12)), average="macro", zero_division=0))
            if oof_f1 > best_oof_f1:
                best_oof_f1 = oof_f1
                best_cfg = {"C": c_val, "class_weight": cw_mode, "train_oof_macro_f1": oof_f1}
                best_oof_logp = oof_logp

    assert best_cfg is not None and best_oof_logp is not None

    # Fit ONE model exclusively on full train partition for val & test predictions
    va_indices = np.where(va_mask)[0]
    te_indices = np.where(te_mask)[0]
    va_te_indices = np.concatenate([va_indices, te_indices])
    va_te_logp = fit_tfidf_logreg_predict_log_proba(
        [texts[i] for i in tr_indices],
        y_tr,
        [texts[i] for i in va_te_indices],
        c_val=best_cfg["C"],
        cw_mode=best_cfg["class_weight"],
    )

    all_logp = np.zeros((len(texts), 12), dtype=np.float32)
    all_logp[tr_indices] = best_oof_logp
    all_logp[va_te_indices] = va_te_logp

    print(
        f"[oof-text] {arm_name} | OOF_MacroF1={best_oof_f1:.4f} | cfg={best_cfg} | "
        f"val_MacroF1={f1_score(y[va_mask], all_logp[va_mask].argmax(1), labels=list(range(12)), average='macro', zero_division=0):.4f} | "
        f"test_MacroF1={f1_score(y[te_mask], all_logp[te_mask].argmax(1), labels=list(range(12)), average='macro', zero_division=0):.4f}",
        flush=True,
    )
    return best_cfg, all_logp


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
    configs = [
        {"hidden_dim": 64, "dropout": 0.3, "lr": 1e-2, "wd": 1e-3, "cw": "none"},
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
    seed_val_metrics, seed_test_metrics, seed_test_preds = [], [], []
    for seed in SEEDS:
        _, preds = train_torch_transductive(
            arch,
            X_np,
            y_np,
            tr_mask,
            va_mask,
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

    agg_test = {"n": seed_test_metrics[0]["n"]}
    for k in seed_test_metrics[0]:
        if k == "n":
            continue
        vals = [m[k] for m in seed_test_metrics]
        agg_test[k] = float(np.mean(vals))
        agg_test[f"{k}_std"] = float(np.std(vals, ddof=1))

    agg_val = {"n": seed_val_metrics[0]["n"]}
    for k in seed_val_metrics[0]:
        if k == "n":
            continue
        agg_val[k] = float(np.mean([m[k] for m in seed_val_metrics]))

    print(
        f"[done] {name} | val_f1={agg_val['macro_f1']:.4f} | test_f1={agg_test['macro_f1']:.4f} +/- {agg_test['macro_f1_std']:.4f} | "
        f"acc={agg_test['accuracy']:.4f} | qwk={agg_test['qwk']:.4f} | cfg={best_cfg}",
        flush=True,
    )
    return {
        "name": name,
        "cfg": best_cfg,
        "val_metrics": agg_val,
        "test_metrics": agg_test,
        "test_pred": seed_test_preds[0],
        "all_seed_test_preds": seed_test_preds,
    }


def paired_bootstrap_delta(
    y_true: np.ndarray, pred_a: np.ndarray, pred_b: np.ndarray, n_boot: int = 2000
) -> dict[str, float]:
    rng = np.random.default_rng(42)
    n = len(y_true)
    d_acc, d_f1, d_qwk = [], [], []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        yt, pa, pb = y_true[idx], pred_a[idx], pred_b[idx]
        d_acc.append(accuracy_score(yt, pa) - accuracy_score(yt, pb))
        d_f1.append(
            f1_score(yt, pa, labels=list(range(12)), average="macro", zero_division=0)
            - f1_score(yt, pb, labels=list(range(12)), average="macro", zero_division=0)
        )
        d_qwk.append(cohen_kappa_score(yt, pa, weights="quadratic") - cohen_kappa_score(yt, pb, weights="quadratic"))
    d_acc_a = np.array(d_acc)
    d_f1_a = np.array(d_f1)
    d_qwk_a = np.array(d_qwk)
    return {
        "delta_macro_f1": float(
            f1_score(y_true, pred_a, labels=list(range(12)), average="macro", zero_division=0)
            - f1_score(y_true, pred_b, labels=list(range(12)), average="macro", zero_division=0)
        ),
        "ci95_macro_f1_low": float(np.percentile(d_f1_a, 2.5)),
        "ci95_macro_f1_high": float(np.percentile(d_f1_a, 97.5)),
        "p_macro_f1": float(min(2.0 * min(np.mean(d_f1_a <= 0), np.mean(d_f1_a >= 0)), 1.0)),
        "delta_acc": float(accuracy_score(y_true, pred_a) - accuracy_score(y_true, pred_b)),
        "p_acc": float(min(2.0 * min(np.mean(d_acc_a <= 0), np.mean(d_acc_a >= 0)), 1.0)),
        "delta_qwk": float(
            cohen_kappa_score(y_true, pred_a, weights="quadratic")
            - cohen_kappa_score(y_true, pred_b, weights="quadratic")
        ),
        "p_qwk": float(min(2.0 * min(np.mean(d_qwk_a <= 0), np.mean(d_qwk_a >= 0)), 1.0)),
    }


def load_v10_predictions() -> dict[str, np.ndarray]:
    fp = V10_RESULTS_DIR / "TEST_PREDICTIONS_V1_0.csv"
    preds = defaultdict(list)
    with fp.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            for k, v in r.items():
                if k.startswith("pred_"):
                    preds[k[len("pred_"):]].append(int(v) - 1)
    return {k: np.array(v, dtype=np.int64) for k, v in preds.items()}


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    verified_inputs = verify_input_manifests()
    rows, entry_ids, shamela_ids, eid_to_idx, y, splits, has_quote, X_topo_raw = (
        load_cohort_and_topology()
    )
    text_arms = load_text_arms(entry_ids)
    adj_sym, adj_t2s, adj_s2t = load_graph_adjacency(eid_to_idx, len(entry_ids))
    adj_sym, adj_t2s, adj_s2t = adj_sym.to(device), adj_t2s.to(device), adj_s2t.to(device)

    tr_mask = splits == "train"
    va_mask = splits == "val"
    te_mask = splits == "test"

    topo_scaler = StandardScaler().fit(X_topo_raw[tr_mask])
    X_topo = topo_scaler.transform(X_topo_raw).astype(np.float32)

    results = []
    oof_cache = {}
    for arm_name, texts in text_arms.items():
        oof_cfg, logp_all = generate_narrator_disjoint_oof_text_features(
            arm_name, texts, entry_ids, shamela_ids, y, tr_mask, va_mask, te_mask
        )
        oof_cache[arm_name] = (oof_cfg, logp_all)

        # Standalone full-train sparse TF-IDF LogReg (trained ONLY on train, tuned inside train OOF)
        va_pred_raw = logp_all[va_mask].argmax(axis=1)
        te_pred_raw = logp_all[te_mask].argmax(axis=1)
        results.append(
            {
                "name": f"BaseText_{arm_name}_OOFSelectedLogReg",
                "cfg": oof_cfg,
                "val_metrics": compute_metrics(y[va_mask], va_pred_raw),
                "test_metrics": compute_metrics(y[te_mask], te_pred_raw),
                "test_pred": te_pred_raw,
            }
        )

        # Standardize 12-dim OOF log-probabilities strictly on train
        logp_scaler = StandardScaler().fit(logp_all[tr_mask])
        X_oof_text = logp_scaler.transform(logp_all).astype(np.float32)
        X_oof_plus_topo = np.hstack([X_oof_text, X_topo]).astype(np.float32)

        results.append(
            run_neural_suite(
                f"OOFTextOnly_{arm_name}_MLP",
                "mlp",
                X_oof_text,
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
                f"FusionOOF_{arm_name}_PlusTopo_EarlyMLP",
                "mlp",
                X_oof_plus_topo,
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
                f"FusionOOF_{arm_name}_PlusTopo_VanillaGCN",
                "gcn",
                X_oof_plus_topo,
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
                f"FusionOOF_{arm_name}_PlusTopo_ConcatDirGNN",
                "dir_concat_gnn",
                X_oof_plus_topo,
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

    # Save MODEL_COMPARISON_V1_1.csv
    comp_fp = OUT_DIR / "MODEL_COMPARISON_V1_1.csv"
    with comp_fp.open("w", encoding="utf-8-sig", newline="") as f:
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

    by_name = {r["name"]: r for r in results}
    y_test = y[te_mask]
    q_test = has_quote[te_mask]
    v10_preds = load_v10_predictions()

    key_models = [
        "BaseText_arm2_v03_all_OOFSelectedLogReg",
        "OOFTextOnly_arm2_v03_all_MLP",
        "FusionOOF_arm2_v03_all_PlusTopo_EarlyMLP",
        "FusionOOF_arm2_v03_all_PlusTopo_VanillaGCN",
        "FusionOOF_arm2_v03_all_PlusTopo_ConcatDirGNN",
        "BaseText_arm3_v03_plus_fwaed_OOFSelectedLogReg",
        "OOFTextOnly_arm3_v03_plus_fwaed_MLP",
        "FusionOOF_arm3_v03_plus_fwaed_PlusTopo_EarlyMLP",
        "FusionOOF_arm3_v03_plus_fwaed_PlusTopo_VanillaGCN",
        "FusionOOF_arm3_v03_plus_fwaed_PlusTopo_ConcatDirGNN",
        "BaseText_arm4_v03_plus_fwaed_plus_tahdhib_OOFSelectedLogReg",
        "OOFTextOnly_arm4_v03_plus_fwaed_plus_tahdhib_MLP",
        "FusionOOF_arm4_v03_plus_fwaed_plus_tahdhib_PlusTopo_EarlyMLP",
        "FusionOOF_arm4_v03_plus_fwaed_plus_tahdhib_PlusTopo_ConcatDirGNN",
    ]

    # Per-rank metrics CSV
    with (OUT_DIR / "PER_RANK_METRICS_V1_1.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(
            f, fieldnames=["model_name", "rank_1_to_12", "support", "precision", "recall", "f1"]
        )
        w.writeheader()
        for mname in key_models:
            p, r_sc, f1_sc, sup = precision_recall_fscore_support(
                y_test, by_name[mname]["test_pred"], labels=list(range(12)), zero_division=0
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

    # Paired bootstrap comparisons (including directly vs v1.0 TruncatedSVD(256) ConcatDirGNN!)
    paired_tests = {
        "Arm2_OOF_ConcatDirGNN_vs_V10_Text_arm2_LinearSVC": paired_bootstrap_delta(
            y_test,
            by_name["FusionOOF_arm2_v03_all_PlusTopo_ConcatDirGNN"]["test_pred"],
            v10_preds["Text_arm2_v03_all_LinearSVC"],
        ),
        "Arm2_OOF_ConcatDirGNN_vs_Arm2_BaseText_LogReg": paired_bootstrap_delta(
            y_test,
            by_name["FusionOOF_arm2_v03_all_PlusTopo_ConcatDirGNN"]["test_pred"],
            by_name["BaseText_arm2_v03_all_OOFSelectedLogReg"]["test_pred"],
        ),
        "Arm2_OOF_ConcatDirGNN_vs_Arm2_OOF_EarlyMLP": paired_bootstrap_delta(
            y_test,
            by_name["FusionOOF_arm2_v03_all_PlusTopo_ConcatDirGNN"]["test_pred"],
            by_name["FusionOOF_arm2_v03_all_PlusTopo_EarlyMLP"]["test_pred"],
        ),
        "Arm3_OOF_ConcatDirGNN_vs_V10_SVD256_ConcatDirGNN": paired_bootstrap_delta(
            y_test,
            by_name["FusionOOF_arm3_v03_plus_fwaed_PlusTopo_ConcatDirGNN"]["test_pred"],
            v10_preds["Fusion_arm3_v03_plus_fwaed_PlusTopo_ConcatDirGNN"],
        ),
        "Arm3_OOF_ConcatDirGNN_vs_Arm3_BaseText_LogReg": paired_bootstrap_delta(
            y_test,
            by_name["FusionOOF_arm3_v03_plus_fwaed_PlusTopo_ConcatDirGNN"]["test_pred"],
            by_name["BaseText_arm3_v03_plus_fwaed_OOFSelectedLogReg"]["test_pred"],
        ),
        "Arm3_OOF_ConcatDirGNN_vs_Arm3_OOF_EarlyMLP": paired_bootstrap_delta(
            y_test,
            by_name["FusionOOF_arm3_v03_plus_fwaed_PlusTopo_ConcatDirGNN"]["test_pred"],
            by_name["FusionOOF_arm3_v03_plus_fwaed_PlusTopo_EarlyMLP"]["test_pred"],
        ),
        "Arm3_OOF_ConcatDirGNN_vs_Arm3_OOF_VanillaGCN": paired_bootstrap_delta(
            y_test,
            by_name["FusionOOF_arm3_v03_plus_fwaed_PlusTopo_ConcatDirGNN"]["test_pred"],
            by_name["FusionOOF_arm3_v03_plus_fwaed_PlusTopo_VanillaGCN"]["test_pred"],
        ),
        "Arm4_OOF_ConcatDirGNN_vs_Arm4_BaseText_LogReg": paired_bootstrap_delta(
            y_test,
            by_name["FusionOOF_arm4_v03_plus_fwaed_plus_tahdhib_PlusTopo_ConcatDirGNN"]["test_pred"],
            by_name["BaseText_arm4_v03_plus_fwaed_plus_tahdhib_OOFSelectedLogReg"]["test_pred"],
        ),
        "Arm4_OOF_ConcatDirGNN_vs_Arm4_OOF_EarlyMLP": paired_bootstrap_delta(
            y_test,
            by_name["FusionOOF_arm4_v03_plus_fwaed_plus_tahdhib_PlusTopo_ConcatDirGNN"]["test_pred"],
            by_name["FusionOOF_arm4_v03_plus_fwaed_plus_tahdhib_PlusTopo_EarlyMLP"]["test_pred"],
        ),
    }

    # Subgroup diagnostics (primary quoted N=725 vs zero-quote N=63)
    subgroup_diag = {}
    for m in key_models:
        p = by_name[m]["test_pred"]
        subgroup_diag[m] = {
            "has_quote": compute_metrics(y_test, p, q_test == 1),
            "zero_quote": compute_metrics(y_test, p, q_test == 0),
        }

    # Confusion matrices
    cm_dict = {
        m: confusion_matrix(y_test, by_name[m]["test_pred"], labels=list(range(12))).tolist()
        for m in key_models
    }
    (OUT_DIR / "CONFUSION_MATRICES_V1_1.json").write_text(
        json.dumps(cm_dict, indent=2), encoding="utf-8"
    )

    # Save TEST_PREDICTIONS_V1_1.csv
    te_indices = np.where(te_mask)[0]
    with (OUT_DIR / "TEST_PREDICTIONS_V1_1.csv").open("w", encoding="utf-8-sig", newline="") as f:
        fieldnames = [
            "entry_id",
            "shamela_narrator_id",
            "true_rank_1_to_12",
            "has_early_critic_quote",
        ] + [f"pred_{m}" for m in key_models]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for pos, idx in enumerate(te_indices):
            row_out = {
                "entry_id": rows[idx]["entry_id"],
                "shamela_narrator_id": rows[idx]["shamela_narrator_id"],
                "true_rank_1_to_12": int(y[idx]) + 1,
                "has_early_critic_quote": int(has_quote[idx]),
            }
            for m in key_models:
                row_out[f"pred_{m}"] = int(by_name[m]["test_pred"][pos]) + 1
            w.writerow(row_out)

    # Report
    lines = [
        "# Section 4 Targeted Experiment v1.1: ConcatDirGNN + Out-of-Fold Sparse TF-IDF LogReg Features",
        "",
        "- **Protocol:** 5-fold stratified narrator-disjoint OOF log-probabilities inside `train` (`N=3,674`; `C` and `class_weight` selected solely by `train` OOF Macro-F1); `val` (`N=788`) and `test` (`N=788`) receive predictions from one TF-IDF LogisticRegression model trained exclusively on `train`.",
        "",
        "## 1. Model Comparison on Held-Out Test (`N = 788`)",
        "",
        "| Model | Val Macro-F1 | Test Macro-F1 (12R) | Test R2-12 Macro-F1 | Test Acc | Test W-F1 | Test QWK | Test MAE | Aux 3-Tier Macro-F1 | Aux 3-Tier Acc |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]
    for res in results:
        vm, tm = res["val_metrics"], res["test_metrics"]
        std_s = f" +/- {tm['macro_f1_std']:.4f}" if "macro_f1_std" in tm else ""
        lines.append(
            f"| `{res['name']}` | {vm['macro_f1']:.4f} | {tm['macro_f1']:.4f}{std_s} | "
            f"{tm['r2_12_macro_f1']:.4f} | {tm['accuracy']:.4f} | {tm['weighted_f1']:.4f} | "
            f"{tm['qwk']:.4f} | {tm['mae']:.4f} | {tm['tier3_macro_f1']:.4f} | {tm['tier3_acc']:.4f} |"
        )

    lines.extend([
        "",
        "## 2. Quoted (`N=725`) vs Zero-Quote (`N=63`) Subgroup Diagnostics",
        "",
        "| Model | Quoted Macro-F1 | Quoted Acc | Zero-Quote Macro-F1 | Zero-Quote Acc |",
        "| :--- | :---: | :---: | :---: | :---: |",
    ])
    for m in key_models:
        hq, zq = subgroup_diag[m]["has_quote"], subgroup_diag[m]["zero_quote"]
        lines.append(
            f"| `{m}` | {hq['macro_f1']:.4f} | {hq['accuracy']:.4f} | {zq['macro_f1']:.4f} | {zq['accuracy']:.4f} |"
        )

    lines.extend([
        "",
        "## 3. Paired Bootstrap Tests (`2,000` resamples, representative `seed=42` for neural models)",
        "",
    ])
    for label, d in paired_tests.items():
        lines.append(
            f"- **{label}:** delta Macro-F1 = `{d['delta_macro_f1']:+.4f}` "
            f"(95% CI `[{d['ci95_macro_f1_low']:+.4f}, {d['ci95_macro_f1_high']:+.4f}]`, p=`{d['p_macro_f1']:.4f}`), "
            f"delta Acc = `{d['delta_acc']:+.4f}` (p=`{d['p_acc']:.4f}`), "
            f"delta QWK = `{d['delta_qwk']:+.4f}` (p=`{d['p_qwk']:.4f}`)"
        )

    (OUT_DIR / "RESULTS_SUMMARY_V1_1.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    exp_lines = [
        "# Experiment Record: Section 4 Targeted OOF Text + ConcatDirGNN (v1.1)",
        "",
        "- Experiment ID: `EXP-SEC4-OOF-GNN-V1.1`",
        "- Date: `2026-11-17`",
        "- Research question / objective: Test whether feeding 12-dimensional narrator-level out-of-fold TF-IDF LogisticRegression log-probabilities plus pure graph topology into ConcatDirGNN resolves the TruncatedSVD(256) compression loss observed in v1.0.",
        "- Leakage controls: OOF folds inside `train` (`3,674`) asserted narrator-disjoint on both `entry_id` and `shamela_narrator_id`; `C` and `class_weight` tuned solely on train OOF Macro-F1; `val` and `test` features generated strictly by full-`train` LogReg; all Ibn Hajar / Taqrib / Tahrir exclusions asserted at load time.",
        f"- Software and hardware environment: Python, scikit-learn, PyTorch `{torch.__version__}`, device `{device}`.",
    ]
    (OUT_DIR / "EXPERIMENT_RECORD.md").write_text("\n".join(exp_lines) + "\n", encoding="utf-8")

    out_files = [
        "EXPERIMENT_RECORD.md",
        "RESULTS_SUMMARY_V1_1.md",
        "MODEL_COMPARISON_V1_1.csv",
        "PER_RANK_METRICS_V1_1.csv",
        "TEST_PREDICTIONS_V1_1.csv",
        "CONFUSION_MATRICES_V1_1.json",
    ]
    manifest_obj = {
        "experiment_id": "EXP-SEC4-OOF-GNN-V1.1",
        "verified_input_manifests": verified_inputs,
        "outputs": {name: {"sha256": sha256_file(OUT_DIR / name)} for name in out_files},
    }
    (OUT_DIR / "MANIFEST.json").write_text(json.dumps(manifest_obj, indent=2), encoding="utf-8")
    (OUT_DIR / "MANIFEST.sha256").write_text(
        "\n".join(f"{sha256_file(OUT_DIR / name)}  {name}" for name in out_files) + "\n",
        encoding="utf-8",
    )
    print("SECTION4_V1_1_COMPLETE", OUT_DIR, flush=True)


if __name__ == "__main__":
    main()
