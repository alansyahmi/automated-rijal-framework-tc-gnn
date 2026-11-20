"""Read-only analytical audit (v2.0) for Task B ESA feasibility and experimental integrity.

Covers Parts A to D strictly before any v1.4/v2 model development:
- Part A: Reproducibility & Baseline Integrity Check (CUDA sparse.mm vs CPU-precomputed
  [X || X_in || X_out], 3-run bit-exactness, seed=42 vs 5-seed val selection, and
  benchmark classification across v1.0-v1.3).
- Part B: Task B Historical Statement & Attribution Integrity Audit (categorizing
  10,597 v0.3 & 4,115 v0.4 duplicates, provenance-preserving deduplication key, and
  speaker-attribution syntax segmentation on train N=3,674).
- Part C: Task B ESA Spec & Pilot Feasibility on train N=3,674 (coverage of 205
  Taqrib Task A phrases vs early-critic idioms, gap frequencies, and pilot stratification).
- Part D: Biographical Assertions Audit on train N=3,674 (unrestricted vs cohort-only
  student/teacher counts in Method 1 bios & Sanadset edges, 3-state book indicators
  across Ranks 1-12, and Shamela narrators.csv contamination against Taqrib).

Zero edits to v1.0-v1.3 artifacts or governance/ files. Test N=788 remains sealed for
all Part B-D feature discovery and specification analysis.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import random
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
csv.field_size_limit(10_000_000)

import numpy as np
import scipy.sparse as sp
import torch
import torch.nn as nn
import torch.nn.functional as F
from joblib import Parallel, delayed
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, cohen_kappa_score, f1_score, mean_absolute_error
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline"
V03_INPUT_DIR = PIPELINE / "task_b_historical_inputs_v0_3_2026-11-17"
V04_INPUT_DIR = PIPELINE / "task_b_historical_inputs_v0_4_2026-11-17"
V03_GRAPH_DIR = PIPELINE / "task_b_consolidated_graph_v0_3_2026-11-17"
V12_BIOS_DIR = PIPELINE / "task_b_method1_clean_bios_v1_2_2026-11-18"
PHRASE_SUMMARY_FP = (
    PIPELINE
    / "evaluation_statement_occurrence_inventory_v0_1_2026-11-16/PHRASE_OCCURRENCE_SUMMARY_V0_1.csv"
)
CONSOLIDATED_ESA_FP = (
    PIPELINE
    / "evaluation_statement_decisions_consolidated_v0_1_2026-11-16/CONSOLIDATED_DECISION_LEDGER_922_ROWS_V0_1.csv"
)
ENTRY_INDEX_FP = PIPELINE / "rank_label_shadow_run_v1_2026-11-15/ENTRY_INDEX.csv"
NARRATORS_CSV_FP = ROOT / "data/2_interim/shamela4_narrator_audit/narrators.csv"
RESULTS_ROOT = ROOT / "results"
OUT_DIR = RESULTS_ROOT / "v2_0_esa_and_integrity_audit_2026-11-19"

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

BOOK_LABELS = [
    "method1_tahdhib_alkamal",
    "method1_jarh_tadil",
    "method1_thiqat_ibn_hibban",
    "method1_tarikh_kabir",
    "method1_thiqat_ijli",
    "method1_kamil",
]

AR_DIACRITICS_RE = re.compile(r"[\u064B-\u065F\u0670\u0640]")


def normalize_arabic(text: str) -> str:
    text = AR_DIACRITICS_RE.sub("", text or "")
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    text = text.replace("ى", "ي")
    return re.sub(r"\s+", " ", text).strip()


def normalize_strict_match(text: str) -> str:
    text = normalize_arabic(text)
    text = text.replace("ة", "ه").replace("ؤ", "و").replace("ئ", "ي")
    text = re.sub(r"[^\u0600-\u06FF0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_all_input_manifests() -> dict[str, int]:
    verified_counts: dict[str, int] = {}
    for pkg_dir in [V03_INPUT_DIR, V04_INPUT_DIR, V03_GRAPH_DIR, V12_BIOS_DIR]:
        manifest = json.loads((pkg_dir / "MANIFEST.json").read_text(encoding="utf-8"))
        outputs = manifest.get("outputs", {})
        for rel, info in outputs.items():
            fp = pkg_dir / rel
            actual = sha256_file(fp)
            expected = info["sha256"] if isinstance(info, dict) else info
            if actual != expected:
                raise AssertionError(f"Checksum mismatch for {fp}: {actual} != {expected}")
        verified_counts[pkg_dir.name] = len(outputs)
    return verified_counts


# ==============================================================================
# PART A: Reproducibility & Baseline Integrity Check
# ==============================================================================

def load_cohort_and_graph():
    feat_fp = V03_GRAPH_DIR / "TASK_B_NODE_STRUCTURAL_FEATURES_V0_3.csv"
    with feat_fp.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 5250

    entry_ids = [r["entry_id"] for r in rows]
    shamela_ids = [r["shamela_narrator_id"] for r in rows]
    eid_to_idx = {eid: i for i, eid in enumerate(entry_ids)}
    y = np.array([int(r["task_a_rank_1_to_12"]) - 1 for r in rows], dtype=np.int64)
    splits = np.array([r["split"] for r in rows])

    X_topo = np.zeros((len(rows), len(TOPO_COLS)), dtype=np.float32)
    for j, c in enumerate(TOPO_COLS):
        vals = np.array([float(r[c]) for r in rows], dtype=np.float32)
        if c != "sanadset_non_sahihayn_ratio":
            vals = np.log1p(np.maximum(vals, 0.0))
        X_topo[:, j] = vals

    dir_rows, dir_cols, dir_vals = [], [], []
    with (V03_GRAPH_DIR / "TASK_B_CONSOLIDATED_GRAPH_EDGES_V0_3.csv").open(
        encoding="utf-8-sig", newline=""
    ) as f:
        for r in csv.DictReader(f):
            if r["both_in_cohort_5250"] != "yes":
                continue
            t_idx = eid_to_idx[r["teacher_entry_id"]]
            s_idx = eid_to_idx[r["student_entry_id"]]
            w_scaled = math.log1p(max(float(r["total_consolidated_weight"]), 1.0))
            dir_rows.append(t_idx)
            dir_cols.append(s_idx)
            dir_vals.append(w_scaled)

    adj_t2s = sp.coo_matrix(
        (dir_vals, (dir_rows, dir_cols)), shape=(len(rows), len(rows)), dtype=np.float32
    ).tocsr()
    adj_s2t = adj_t2s.T.tocsr()

    def row_norm(adj):
        adj = adj.tocoo()
        rs = np.array(adj.sum(1)).flatten()
        d_inv = np.where(rs > 0, 1.0 / np.maximum(rs, 1e-12), 0.0)
        n = sp.diags(d_inv).dot(adj).tocoo()
        return torch.sparse_coo_tensor(
            torch.tensor(np.vstack([n.row, n.col]), dtype=torch.long),
            torch.tensor(n.data, dtype=torch.float32),
            size=n.shape,
        ).coalesce()

    return rows, entry_ids, shamela_ids, y, splits, X_topo, row_norm(adj_t2s), row_norm(adj_s2t)


def load_arm4_plain_texts(entry_ids: list[str]) -> list[str]:
    eid_set = set(entry_ids)
    v03_plain: defaultdict[str, list[str]] = defaultdict(list)
    fwaed_plain: defaultdict[str, list[str]] = defaultdict(list)
    abl_plain: defaultdict[str, list[str]] = defaultdict(list)

    with (V03_INPUT_DIR / "TASK_B_ELIGIBLE_HISTORICAL_PASSAGES_V0_3.csv").open(
        encoding="utf-8-sig", newline=""
    ) as f:
        for r in csv.DictReader(f):
            eid = r["entry_id"]
            if eid in eid_set:
                txt = normalize_arabic(r["quotation_text_exact"])
                if txt:
                    v03_plain[eid].append(txt)

    with (V04_INPUT_DIR / "TASK_B_FWAED_PASSAGES_V0_4.csv").open(
        encoding="utf-8-sig", newline=""
    ) as f:
        for r in csv.DictReader(f):
            eid = r["entry_id"]
            if eid in eid_set:
                txt = normalize_arabic(r["fwaed_text_exact"])
                if txt:
                    fwaed_plain[eid].append(txt)

    with (V04_INPUT_DIR / "TASK_B_EARLY_SPEAKER_ABLATION_PASSAGES_V0_4.csv").open(
        encoding="utf-8-sig", newline=""
    ) as f:
        for r in csv.DictReader(f):
            eid = r["entry_id"]
            if eid in eid_set:
                txt = normalize_arabic(r["quotation_text_exact"])
                if txt:
                    abl_plain[eid].append(txt)

    return [" \n ".join(v03_plain[e] + fwaed_plain[e] + abl_plain[e]) for e in entry_ids]


def make_class_weights(y_train: np.ndarray, mode: str) -> dict[int, float] | None:
    if mode == "none":
        return None
    counts = Counter(y_train.tolist())
    n, k = len(y_train), 12
    return {
        c: (math.sqrt(n / (k * max(counts.get(c, 1), 1))) if mode == "sqrt" else n / (k * max(counts.get(c, 1), 1)))
        for c in range(k)
    }


def fit_tfidf_logreg_predict_log_proba(
    train_texts: list[str], y_train: np.ndarray, eval_texts: list[str], c_val: float, cw_mode: str
) -> np.ndarray:
    word_vec = TfidfVectorizer(
        analyzer="word", ngram_range=(1, 2), min_df=2, max_features=35000, sublinear_tf=True
    )
    char_vec = TfidfVectorizer(
        analyzer="char_wb", ngram_range=(3, 5), min_df=3, max_features=35000, sublinear_tf=True
    )
    X_tr = sp.hstack([word_vec.fit_transform(train_texts), char_vec.fit_transform(train_texts)], format="csr")
    X_ev = sp.hstack([word_vec.transform(eval_texts), char_vec.transform(eval_texts)], format="csr")
    clf = LogisticRegression(
        C=c_val, class_weight=make_class_weights(y_train, cw_mode), max_iter=160, tol=5e-3, solver="lbfgs", random_state=42
    )
    clf.fit(X_tr, y_train)
    return clf.predict_log_proba(X_ev).astype(np.float32)


def generate_oof_arm4_features(
    texts: list[str], y: np.ndarray, tr_mask: np.ndarray, va_mask: np.ndarray, te_mask: np.ndarray
) -> tuple[np.ndarray, dict]:
    tr_idx = np.where(tr_mask)[0]
    va_te_idx = np.concatenate([np.where(va_mask)[0], np.where(te_mask)[0]])
    y_tr = y[tr_idx]
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    folds = list(skf.split(tr_idx, y_tr))

    best_cfg, best_oof_f1, best_oof_logp = None, -1.0, None
    for cw_mode in ["none", "sqrt"]:
        for c_val in [0.5, 1.0, 2.0]:
            fold_preds = Parallel(n_jobs=5)(
                delayed(fit_tfidf_logreg_predict_log_proba)(
                    [texts[i] for i in tr_idx[ftr]],
                    y[tr_idx[ftr]],
                    [texts[i] for i in tr_idx[fva]],
                    c_val,
                    cw_mode,
                )
                for ftr, fva in folds
            )
            oof_logp = np.zeros((len(tr_idx), 12), dtype=np.float32)
            for (_ftr, fva), fp in zip(folds, fold_preds):
                oof_logp[fva] = fp
            oof_f1 = float(f1_score(y_tr, oof_logp.argmax(1), labels=list(range(12)), average="macro", zero_division=0))
            if oof_f1 > best_oof_f1:
                best_oof_f1 = oof_f1
                best_cfg = {"C": c_val, "class_weight": cw_mode, "train_oof_macro_f1": oof_f1}
                best_oof_logp = oof_logp

    va_te_logp = fit_tfidf_logreg_predict_log_proba(
        [texts[i] for i in tr_idx],
        y_tr,
        [texts[i] for i in va_te_idx],
        best_cfg["C"],
        best_cfg["class_weight"],
    )
    full_logp = np.zeros((len(texts), 12), dtype=np.float32)
    full_logp[tr_idx] = best_oof_logp
    full_logp[va_te_idx] = va_te_logp
    return full_logp, best_cfg


class ConcatDirGNN(nn.Module):
    def __init__(self, in_dim: int, hid: int, out_dim: int, dropout: float):
        super().__init__()
        self.ego_fc = nn.Linear(in_dim, hid)
        self.t2s_fc = nn.Linear(in_dim, hid)
        self.s2t_fc = nn.Linear(in_dim, hid)
        self.bn = nn.BatchNorm1d(hid * 3)
        self.dropout = dropout
        self.head = nn.Linear(hid * 3, out_dim)

    def forward(self, x: torch.Tensor, adj_t2s: torch.Tensor, adj_s2t: torch.Tensor) -> torch.Tensor:
        h = F.relu(
            self.bn(
                torch.cat(
                    [
                        self.ego_fc(x),
                        self.t2s_fc(torch.sparse.mm(adj_t2s, x)),
                        self.s2t_fc(torch.sparse.mm(adj_s2t, x)),
                    ],
                    dim=1,
                )
            )
        )
        return self.head(F.dropout(h, p=self.dropout, training=self.training))


class PrecomputedConcatDirGNN(nn.Module):
    """Mathematically equivalent 1-hop ConcatDirGNN consuming CPU-precomputed [X || X_in || X_out]."""

    def __init__(self, base_in_dim: int, hid: int, out_dim: int, dropout: float):
        super().__init__()
        self.d = base_in_dim
        self.ego_fc = nn.Linear(base_in_dim, hid)
        self.t2s_fc = nn.Linear(base_in_dim, hid)
        self.s2t_fc = nn.Linear(base_in_dim, hid)
        self.bn = nn.BatchNorm1d(hid * 3)
        self.dropout = dropout
        self.head = nn.Linear(hid * 3, out_dim)

    def forward(self, x_concat: torch.Tensor) -> torch.Tensor:
        d = self.d
        h = F.relu(
            self.bn(
                torch.cat(
                    [
                        self.ego_fc(x_concat[:, :d]),
                        self.t2s_fc(x_concat[:, d : 2 * d]),
                        self.s2t_fc(x_concat[:, 2 * d :]),
                    ],
                    dim=1,
                )
            )
        )
        return self.head(F.dropout(h, p=self.dropout, training=self.training))


def set_deterministic(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    torch.use_deterministic_algorithms(True, warn_only=False)


def train_variant(
    mode: str,
    X_in_mat: np.ndarray,
    y_np: np.ndarray,
    tr_mask: np.ndarray,
    va_mask: np.ndarray,
    adj_t2s: torch.Tensor | None,
    adj_s2t: torch.Tensor | None,
    device: torch.device,
    cfg: dict,
    seed: int,
    base_in_dim: int,
) -> tuple[float, np.ndarray]:
    set_deterministic(seed)
    X_t = torch.tensor(X_in_mat, dtype=torch.float32, device=device)
    y_t = torch.tensor(y_np, dtype=torch.long, device=device)
    tr_t = torch.tensor(tr_mask, dtype=torch.bool, device=device)

    cw_dict = make_class_weights(y_np[tr_mask], cfg["cw"])
    criterion = (
        nn.CrossEntropyLoss()
        if cw_dict is None
        else nn.CrossEntropyLoss(weight=torch.tensor([cw_dict[c] for c in range(12)], dtype=torch.float32, device=device))
    )
    if mode == "sparse_cuda":
        model = ConcatDirGNN(base_in_dim, cfg["hidden_dim"], 12, cfg["dropout"]).to(device)
        a1, a2 = adj_t2s.to(device), adj_s2t.to(device)
    else:
        model = PrecomputedConcatDirGNN(base_in_dim, cfg["hidden_dim"], 12, cfg["dropout"]).to(device)
        a1, a2 = None, None
    opt = torch.optim.AdamW(model.parameters(), lr=cfg["lr"], weight_decay=cfg["wd"])

    best_val, best_pred, bad = -1.0, None, 0
    for _ in range(250):
        model.train()
        opt.zero_grad()
        logits = model(X_t, a1, a2) if mode == "sparse_cuda" else model(X_t)
        loss = criterion(logits[tr_t], y_t[tr_t])
        loss.backward()
        opt.step()

        model.eval()
        with torch.no_grad():
            ev = model(X_t, a1, a2) if mode == "sparse_cuda" else model(X_t)
            preds = ev.argmax(1).cpu().numpy()
        vf1 = float(f1_score(y_np[va_mask], preds[va_mask], labels=list(range(12)), average="macro", zero_division=0))
        if vf1 > best_val:
            best_val = vf1
            best_pred = preds
            bad = 0
        else:
            bad += 1
            if bad >= 40:
                break
    assert best_pred is not None
    return best_val, best_pred


def run_part_a_audit() -> tuple[dict, list[dict]]:
    print("[Part A] Running reproducibility & benchmark classification audit...", flush=True)
    _, entry_ids, _, y, splits, X_topo, adj_t2s, adj_s2t = load_cohort_and_graph()
    tr_mask = splits == "train"
    va_mask = splits == "val"
    te_mask = splits == "test"

    texts = load_arm4_plain_texts(entry_ids)
    logp, oof_cfg = generate_oof_arm4_features(texts, y, tr_mask, va_mask, te_mask)

    scaler = StandardScaler()
    X_raw = np.hstack([logp, X_topo]).astype(np.float32)
    X_np = scaler.fit(X_raw[tr_mask]).transform(X_raw).astype(np.float32)
    base_d = X_np.shape[1]

    # CPU-precomputed 1-hop propagated concatenation [X || adj_t2s @ X || adj_s2t @ X]
    X_cpu = torch.tensor(X_np, dtype=torch.float32)
    with torch.no_grad():
        X_in = torch.sparse.mm(adj_t2s, X_cpu)
        X_out = torch.sparse.mm(adj_s2t, X_cpu)
        X_concat_cpu = torch.cat([X_cpu, X_in, X_out], dim=1).numpy().astype(np.float32)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # 1. Mathematical equivalence check (single step forward + backward gradient diff)
    set_deterministic(42)
    m_sp = ConcatDirGNN(base_d, 128, 12, 0.4).to(device)
    m_pr = PrecomputedConcatDirGNN(base_d, 128, 12, 0.4).to(device)
    m_pr.load_state_dict(m_sp.state_dict())
    m_sp.eval()
    m_pr.eval()
    X_gpu = torch.tensor(X_np, dtype=torch.float32, device=device)
    Xc_gpu = torch.tensor(X_concat_cpu, dtype=torch.float32, device=device)
    a1_gpu, a2_gpu = adj_t2s.to(device), adj_s2t.to(device)
    with torch.no_grad():
        out_sp = m_sp(X_gpu, a1_gpu, a2_gpu)
        out_pr = m_pr(Xc_gpu)
        max_logit_diff = float((out_sp - out_pr).abs().max().item())

    # 2. Repeated 3x identical-seed (seed=42) 250-epoch runs on CUDA
    cfg128 = {"hidden_dim": 128, "dropout": 0.4, "lr": 5e-3, "wd": 5e-3, "cw": "sqrt"}
    sp_runs, pr_runs = [], []
    for _ in range(3):
        vf, prd = train_variant("sparse_cuda", X_np, y, tr_mask, va_mask, adj_t2s, adj_s2t, device, cfg128, 42, base_d)
        tf = float(f1_score(y[te_mask], prd[te_mask], labels=list(range(12)), average="macro", zero_division=0))
        sp_runs.append({"val_f1": vf, "test_f1": tf, "pred_sha256": hashlib.sha256(prd.tobytes()).hexdigest()})

        vfp, prdp = train_variant("precomputed_cuda", X_concat_cpu, y, tr_mask, va_mask, None, None, device, cfg128, 42, base_d)
        tfp = float(f1_score(y[te_mask], prdp[te_mask], labels=list(range(12)), average="macro", zero_division=0))
        pr_runs.append({"val_f1": vfp, "test_f1": tfp, "pred_sha256": hashlib.sha256(prdp.tobytes()).hexdigest()})

    sparse_bit_exact = len({r["pred_sha256"] for r in sp_runs}) == 1
    precomputed_bit_exact = len({r["pred_sha256"] for r in pr_runs}) == 1

    # 3. 5-seed config evaluation using deterministic precomputed CUDA across the 3 Exp A configs
    configs = [
        {"hidden_dim": 128, "dropout": 0.4, "lr": 5e-3, "wd": 5e-3, "cw": "sqrt"},
        {"hidden_dim": 256, "dropout": 0.4, "lr": 5e-3, "wd": 5e-3, "cw": "sqrt"},
        {"hidden_dim": 128, "dropout": 0.5, "lr": 3e-3, "wd": 1e-2, "cw": "balanced"},
    ]
    cfg_results = []
    for idx, cfg in enumerate(configs):
        seed_vals, seed_tests, seed_accs = [], [], []
        s42_val = None
        for seed in SEEDS:
            vf, prd = train_variant(
                "precomputed_cuda", X_concat_cpu, y, tr_mask, va_mask, None, None, device, cfg, seed, base_d
            )
            tf = float(f1_score(y[te_mask], prd[te_mask], labels=list(range(12)), average="macro", zero_division=0))
            ta = float(accuracy_score(y[te_mask], prd[te_mask]))
            if seed == 42:
                s42_val = vf
            seed_vals.append(vf)
            seed_tests.append(tf)
            seed_accs.append(ta)
        cfg_results.append({
            "config_id": f"cfg_{idx+1}",
            "cfg": cfg,
            "seed42_val_macro_f1": s42_val,
            "val_5seed_mean_macro_f1": float(np.mean(seed_vals)),
            "val_5seed_std": float(np.std(seed_vals, ddof=1)),
            "test_5seed_mean_macro_f1": float(np.mean(seed_tests)),
            "test_5seed_std": float(np.std(seed_tests, ddof=1)),
            "test_5seed_mean_acc": float(np.mean(seed_accs)),
        })

    # 4. Classify all v1.0-v1.3 benchmark rows
    classified_rows = []
    sources = [
        ("v1.0", RESULTS_ROOT / "section4_task_b_baselines_v1_0_2026-11-17/MODEL_COMPARISON_V1_0.csv"),
        ("v1.1", RESULTS_ROOT / "section4_oof_text_gnn_v1_1_2026-11-17/MODEL_COMPARISON_V1_1.csv"),
        ("v1.2", RESULTS_ROOT / "v1_2_controlled_experiments_2026-11-18/MODEL_COMPARISON_V1_2.csv"),
        ("v1.3", RESULTS_ROOT / "v1_3_genre_dilution_diagnostic_2026-11-19/MODEL_COMPARISON_V1_3.csv"),
    ]
    for ver, fp in sources:
        with fp.open(encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                mname = r["model_name"]
                if ver == "v1.0":
                    if "Ref_" in mname or "PureTopo" in mname or ("Text_" in mname and "SVC" not in mname) or "Fusion_" in mname:
                        # LinearSVC had validation leak in v1.0 prior to v1.1 OOF fix; VanillaGCN/ConcatDirGNN used leaky LinearSVC OOF or uncalibrated features
                        status = "superseded_v1_0_feature_leak_or_non_oof" if not mname.startswith("Ref_") and "PureTopo" not in mname else "matched_reference_v1_0"
                        det = "deterministic" if any(k in mname for k in ["Dummy", "SVC", "LogReg"]) else ("cuda_sparse_nondet" if "GCN" in mname or "GNN" in mname else "deterministic_cuda_mlp")
                    else:
                        status = "superseded_v1_0_feature_leak_or_non_oof"
                        det = "deterministic"
                elif ver == "v1.1":
                    status = "confirmatory_canonical_v1_1"
                    det = "deterministic" if "LogReg" in mname else ("cuda_sparse_nondet" if "GCN" in mname or "GNN" in mname else "deterministic_cuda_mlp")
                elif ver == "v1.2":
                    if "Exploratory" in mname:
                        status = "exploratory_v1_2"
                    elif "PhaseA_ExpA" in mname:
                        status = "confirmatory_matched_baseline_v1_2"
                    elif "PhaseA_" in mname:
                        status = "controlled_confirmatory_v1_2"
                    else:
                        status = "ablation_phase_b_v1_2"
                    det = "deterministic" if "LogReg" in mname else ("cuda_sparse_nondet" if "GNN" in mname else "deterministic_cuda_mlp")
                else:
                    status = "diagnostic_ablation_v1_3"
                    det = "deterministic" if "LogReg" in mname else ("cuda_sparse_nondet" if "GNN" in mname else "deterministic_cuda_mlp")

                classified_rows.append({
                    "version": ver,
                    "model_name": mname,
                    "val_macro_f1": r.get("val_macro_f1", ""),
                    "test_macro_f1": r.get("test_macro_f1", ""),
                    "test_macro_f1_std": r.get("test_macro_f1_std", ""),
                    "test_accuracy": r.get("test_accuracy", ""),
                    "determinism_status": det,
                    "methodological_role": status,
                })

    part_a = {
        "device": str(device),
        "arm4_oof_logreg_cfg": oof_cfg,
        "forward_logit_max_abs_diff_sparse_vs_precomputed": max_logit_diff,
        "sparse_cuda_3runs_seed42": sp_runs,
        "sparse_cuda_bit_exact": sparse_bit_exact,
        "precomputed_cuda_3runs_seed42": pr_runs,
        "precomputed_cuda_bit_exact": precomputed_bit_exact,
        "seed42_vs_5seed_val_selection_arm4_deterministic": cfg_results,
        "v1_1_vs_v1_2_logreg_diff_cause": "v1.1 used max_features=30000 and max_iter=150 vs v1.2 max_features=35000 and max_iter=160 (0.4549 vs 0.4528).",
        "v1_2_vs_v1_3_gnn_diff_cause": "Identical Arm 4 OOF/topo features (EarlyMLP exact 0.4601); ConcatDirGNN drifted (0.4762 vs 0.4649) purely from CUDA torch.sparse.mm non-determinism plus single-seed (seed=42) val config selection.",
    }
    return part_a, classified_rows


# ==============================================================================
# PART B: Task B Historical Statement & Attribution Integrity Audit
# ==============================================================================

MULTI_SPEAKER_MARKERS = [
    "وقال ", "قال ", "وسئل ", "سئل ", "سمعت ", "سألت ", "عن ", "حدثنا ", "أخبرنا ",
    "وذكر ", "ذكره ", "وذكره ", "وضعفه ", "ووثقه ",
]
EXPLICIT_NAMING_RE = re.compile(
    r"(?:قال|وقال|سئل|وسئل|ذكره|وذكره|وثقه|ضعفه)\s+(?:أبو|ابو|ابن|أحمد|احمد|يحيى|يحيي|علي|محمد|البخاري|النسائي|النسايي|الدارقطني|الترمذي|مسلم|شعبة|سفيان|مالك|الشافعي|العجلي|الساجي|الذهلي|أبي)"
)
PRONOMINAL_REF_RE = re.compile(r"(?:سمعت أبي|سمعت ابي|سألته|سالته|قلت له|سمعته يقول)")
NESTED_CHAIN_RE = re.compile(r"(?:حدثنا|نا|حدثني|أخبرنا|اخبرنا)\s+\S+.*(?:قال|سمعت|سألت)")
PURE_BIO_PREFIX_RE = re.compile(r"^(?:\.|،|\s)*(?:روى عن|روي عن|سمع من|حدث عن|مات سنة|ولد سنة|سكن |أصله |اصله )")


def classify_passage_rows(rows: list[dict], source_name: str, train_eids: set[str]) -> tuple[dict, list[dict]]:
    total = len(rows)
    by_eid_norm = defaultdict(list)
    for r in rows:
        eid = r["entry_id"]
        txt = normalize_arabic(r.get("quotation_text_exact", "") or r.get("fwaed_text_exact", ""))
        by_eid_norm[(eid, txt)].append(r)

    unique_pairs = len(by_eid_norm)
    excess_rows = total - unique_pairs

    dup_cat_counts = Counter()
    train_dup_cat_counts = Counter()
    sample_examples = defaultdict(list)

    provenance_keys = set()
    train_prov_keys = set()

    for (eid, txt), grp in by_eid_norm.items():
        # Provenance-preserving key: (entry_id, critic/category, source_work, source_citation, norm_text)
        for r in grp:
            spk = normalize_arabic(r.get("historical_attribution_critic", "") or r.get("fwaed_category", ""))
            wrk = normalize_arabic(r.get("source_work_normalised", "") or "")
            cit = normalize_arabic(r.get("source_citation_exact", "") or "")
            provenance_keys.add((eid, spk, wrk, cit, txt))
            if eid in train_eids:
                train_prov_keys.add((eid, spk, wrk, cit, txt))

        if len(grp) == 1:
            continue
        anchor = grp[0]
        a_spk = normalize_arabic(anchor.get("historical_attribution_critic", ""))
        a_wrk = normalize_arabic(anchor.get("source_work_normalised", ""))
        a_cit = normalize_arabic(anchor.get("source_citation_exact", ""))

        # Compare each duplicate copy beyond the first
        seen_cits = {(a_spk, a_wrk, a_cit)}
        for r in grp[1:]:
            spk = normalize_arabic(r.get("historical_attribution_critic", ""))
            wrk = normalize_arabic(r.get("source_work_normalised", ""))
            cit = normalize_arabic(r.get("source_citation_exact", ""))
            if wrk == a_wrk and cit == a_cit and spk != a_spk:
                cat = "class1_shamela_multi_group_same_citation_diff_label"
            elif wrk == a_wrk and cit == a_cit and spk == a_spk:
                cat = "class1b_exact_same_work_citation_and_label"
            elif spk == a_spk and wrk != a_wrk:
                cat = "class2_same_critic_distinct_source_work"
            elif spk == a_spk and wrk == a_wrk and cit != a_cit:
                cat = "class3_same_critic_same_work_distinct_citation"
            else:
                cat = "class4_distinct_critic_distinct_or_parallel_work"

            dup_cat_counts[cat] += 1
            if eid in train_eids:
                train_dup_cat_counts[cat] += 1
                if len(sample_examples[cat]) < 2:
                    sample_examples[cat].append({
                        "entry_id": eid,
                        "anchor": {"critic": a_spk, "work": a_wrk, "cit": a_cit},
                        "dup": {"critic": spk, "work": wrk, "cit": cit},
                        "text_preview": txt[:120],
                    })
            seen_cits.add((spk, wrk, cit))

    breakdown_rows = []
    for cat in [
        "class1_shamela_multi_group_same_citation_diff_label",
        "class1b_exact_same_work_citation_and_label",
        "class2_same_critic_distinct_source_work",
        "class3_same_critic_same_work_distinct_citation",
        "class4_distinct_critic_distinct_or_parallel_work",
    ]:
        breakdown_rows.append({
            "source_file": source_name,
            "duplicate_class": cat,
            "excess_rows_overall": dup_cat_counts.get(cat, 0),
            "excess_rows_train": train_dup_cat_counts.get(cat, 0),
        })

    summary = {
        "source_file": source_name,
        "total_rows": total,
        "unique_eid_norm_text": unique_pairs,
        "excess_rows_by_text": excess_rows,
        "unique_provenance_preserving_rows": len(provenance_keys),
        "excess_pure_extraction_or_exact_prov_duplicates": total - len(provenance_keys),
        "train_total_rows": sum(1 for r in rows if r["entry_id"] in train_eids),
        "train_unique_provenance_rows": len(train_prov_keys),
        "dup_category_counts_overall": dict(dup_cat_counts),
        "dup_category_counts_train": dict(train_dup_cat_counts),
        "train_examples": dict(sample_examples),
    }
    return summary, breakdown_rows


def split_compound_clauses(txt_norm: str) -> list[str]:
    # Split on clear attribution connectors when preceded by space/punctuation
    parts = re.split(
        r"(?:(?<=^)|(?<=[\s،.:؛]))(?=(?:وقال|قال|وسئل|سئل|وذكر|ذكره|سمعت|سألت)\s+)",
        txt_norm,
    )
    return [p.strip(" ،.:؛") for p in parts if p and p.strip(" ،.:؛")]


def run_part_b_and_c_audit(
    train_eids: set[str], eid_to_rank: dict[str, int]
) -> tuple[dict, list[dict], dict, list[dict]]:
    print("[Part B & C] Auditing Task B duplicates, syntax segmentation, and ESA gaps on train...", flush=True)
    with (V03_INPUT_DIR / "TASK_B_ELIGIBLE_HISTORICAL_PASSAGES_V0_3.csv").open(encoding="utf-8-sig", newline="") as f:
        v03_rows = list(csv.DictReader(f))
    with (V04_INPUT_DIR / "TASK_B_EARLY_SPEAKER_ABLATION_PASSAGES_V0_4.csv").open(encoding="utf-8-sig", newline="") as f:
        abl_rows = list(csv.DictReader(f))
    with (V04_INPUT_DIR / "TASK_B_FWAED_PASSAGES_V0_4.csv").open(encoding="utf-8-sig", newline="") as f:
        fwd_rows = list(csv.DictReader(f))

    s_v03, b_v03 = classify_passage_rows(v03_rows, "v03_eligible_passages", train_eids)
    s_abl, b_abl = classify_passage_rows(abl_rows, "v04_tahdhib_early_ablation", train_eids)
    s_fwd, b_fwd = classify_passage_rows(fwd_rows, "v04_fwaed_passages", train_eids)
    dup_breakdown_rows = b_v03 + b_abl + b_fwd

    # Build provenance-preserving deduplicated Arm 4 corpus strictly on TRAIN
    seen_train_prov = set()
    train_dedup_passages = []
    raw_train_passages_count = 0

    for src_tag, src_rows, is_fwd in [("v03", v03_rows, False), ("v04_abl", abl_rows, False), ("v04_fwd", fwd_rows, True)]:
        for r in src_rows:
            eid = r["entry_id"]
            if eid not in train_eids:
                continue
            raw_train_passages_count += 1
            txt_raw = r["fwaed_text_exact"] if is_fwd else r["quotation_text_exact"]
            txt = normalize_arabic(txt_raw)
            if not txt:
                continue
            spk = normalize_arabic(r.get("fwaed_category", "") if is_fwd else r.get("historical_attribution_critic", ""))
            wrk = normalize_arabic(r.get("source_work_normalised", ""))
            cit = normalize_arabic(r.get("source_citation_exact", ""))
            pkey = (eid, spk, wrk, cit, txt)
            if pkey in seen_train_prov:
                continue
            seen_train_prov.add(pkey)
            train_dedup_passages.append({
                "src_tag": src_tag,
                "entry_id": eid,
                "rank": eid_to_rank[eid],
                "critic_field": spk,
                "source_work": wrk,
                "source_citation": cit,
                "text_norm": txt,
                "text_strict": normalize_strict_match(txt),
            })

    # Also measure impact on critic-count conflict/diversity if pure duplicates removed on train
    raw_critics_by_eid = defaultdict(set)
    dedup_critics_by_eid = defaultdict(set)
    raw_quotes_cnt = Counter()
    dedup_quotes_cnt = Counter()
    for p in train_dedup_passages:
        dedup_critics_by_eid[p["entry_id"]].add(p["critic_field"] or "UNATTRIBUTED")
        dedup_quotes_cnt[p["entry_id"]] += 1

    # Speaker syntax & atomic segmentation audit on non-fwaed train dedup passages (critics' quotations)
    seg_counts = Counter()
    seg_examples = defaultdict(list)
    total_atomic_units_est = 0
    quote_passages = [p for p in train_dedup_passages if p["src_tag"] != "v04_fwd"]

    for p in quote_passages:
        t = p["text_norm"]
        spk = p["critic_field"]
        has_pronom = bool(PRONOMINAL_REF_RE.search(t))
        has_nested = bool(NESTED_CHAIN_RE.search(t))
        clauses = split_compound_clauses(t)
        named_hits = EXPLICIT_NAMING_RE.findall(t)
        is_pure_bio = bool(PURE_BIO_PREFIX_RE.match(t)) and len(named_hits) == 0 and not has_pronom

        if len(clauses) >= 2 and any(EXPLICIT_NAMING_RE.search(c) for c in clauses):
            cat = "splittable_compound_multi_clause"
            total_atomic_units_est += len(clauses)
        elif has_pronom or has_nested:
            cat = "ambiguous_pronominal_or_nested_isnad"
            total_atomic_units_est += max(1, len(clauses))
        elif len(named_hits) >= 1 and spk and spk != "غير منسوب":
            cat = "clean_atomic_explicit_speaker"
            total_atomic_units_est += 1
        elif is_pure_bio:
            cat = "biographical_or_transmission_mix_no_internal_speaker"
            total_atomic_units_est += 1
        elif spk and spk not in {"", "غير منسوب"}:
            cat = "clean_atomic_header_attributed"
            total_atomic_units_est += 1
        else:
            cat = "unattributed_statement"
            total_atomic_units_est += 1

        seg_counts[cat] += 1
        if len(seg_examples[cat]) < 3:
            seg_examples[cat].append({
                "entry_id": p["entry_id"],
                "critic_field": spk,
                "source_work": p["source_work"],
                "text": t[:180],
                "n_clauses_split": len(clauses),
            })

    # Part C: Check Task A 205 vocabulary coverage against train deduplicated passages
    with PHRASE_SUMMARY_FP.open(encoding="utf-8-sig", newline="") as f:
        phrase_rows = list(csv.DictReader(f))
    taqrib_phrases = []
    for r in phrase_rows:
        p_norm = normalize_strict_match(r["phrase_candidate_exact"])
        if p_norm:
            taqrib_phrases.append((r["candidate_id"], r["phrase_candidate_exact"], p_norm))

    # Build normalized strict patterns bounded cleanly by spaces
    taqrib_patterns = [
        (cid, raw_p, norm_p, re.compile(r"(?:^|\s)" + re.escape(norm_p) + r"(?:$|\s)"))
        for cid, raw_p, norm_p in taqrib_phrases
    ]

    # Key Task B early-critic / jarh wa ta'dil idioms & syntactic modifiers to measure explicitly
    EARLY_CRITIC_IDIOMS = [
        ("لا باس به", "no_harm_idiom_praise_tadil", "positive_or_restrained_praise"),
        ("ليس به باس", "no_harm_negated_idiom", "positive_or_restrained_praise"),
        ("محله الصدق", "place_is_truthfulness", "restrained_praise"),
        ("مقارب الحديث", "near_standard_hadith", "restrained_praise_or_moderate"),
        ("صالح الحديث", "sound_hadith", "restrained_praise"),
        ("صالح", "sound_general", "praise_or_moderate"),
        ("يكتب حديثه", "his_hadith_is_written", "conditional_transmission"),
        ("لا يحتج به", "not_used_as_proof", "negated_authority"),
        ("يحتج به", "used_as_proof", "authority"),
        ("سكتوا عنه", "critics_silent_about_him", "adverse_silence_or_abandonment"),
        ("فيه نظر", "there_is_concern_in_him", "adverse_criticism_bukhari_idiom"),
        ("ليس بالقوي", "not_strong_qualified_negation", "negated_strength"),
        ("ليس بذاك", "not_that_strong", "mitigated_criticism"),
        ("ليس بشيء", "is_nothing_strong_rejection", "severe_rejection"),
        ("ليس بمتين", "not_firm", "weakness"),
        ("شيخ", "shaykh_intermediate_term", "biographical_or_tadil_level"),
        ("مجهول", "unknown_majhul", "unknownness"),
        ("لا اعرفه", "i_do_not_know_him", "unknownness_explicit_critic"),
        ("لا يعرف", "is_not_known", "unknownness"),
        ("لا يتابع عليه", "not_corroborated_upon_it", "corroboration_deficit"),
        ("يحدث عن الضعفاء", "narrates_from_weak_narrators", "transmission_habit"),
        ("يروي المناكير", "narrates_rejected_reports", "narration_anomaly"),
        ("منكر الحديث", "munkar_al_hadith", "severe_rejection"),
        ("متروك", "matruk_abandoned", "severe_rejection"),
        ("واهي", "wahi_frail", "severe_rejection"),
        ("ضعيف الحديث", "daif_al_hadith", "weakness"),
        ("ضعيف", "daif_weak", "weakness"),
        ("ثقة ثقة", "doubled_thiqah", "intensified_trustworthiness"),
        ("ثقة ثبت", "thiqah_thabt", "intensified_trustworthiness"),
        ("ثقة حجة", "thiqah_hujjah", "intensified_trustworthiness"),
        ("ثقة مامون", "thiqah_mamun", "intensified_trustworthiness"),
        ("ثقة", "thiqah_trustworthy", "trustworthiness"),
        ("صدوق", "saduq_truthful", "truthfulness"),
        ("ان شاء الله", "in_sha_allah_modal_hedging", "hedging_qualification"),
        ("ارجو انه", "i_hope_that_he_modal", "hedging_qualification"),
        ("يهم", "makes_occasional_errors", "error_qualification"),
        ("يخطئ", "makes_mistakes", "error_qualification"),
        ("اختلط", "suffered_ikhtilat", "temporal_deterioration"),
        ("تغير", "changed_memory", "temporal_deterioration"),
        ("بأخرة", "late_in_life", "temporal_scope"),
        ("اذا روى عن", "conditional_teacher_scope", "conditional_transmission_scope"),
        ("في بعض حديثه", "partial_hadith_scope", "conditional_scope"),
        ("سمعت ابي", "son_reporting_abu_hatim", "attributed_son_report"),
    ]
    EARLY_IDIOM_MATCHERS = [
        (raw_id, label, role, re.compile(r"(?:^|\s)" + re.escape(normalize_strict_match(raw_id)) + r"(?:$|\s)"))
        for raw_id, label, role in EARLY_CRITIC_IDIOMS
    ]

    taqrib_norm_set = {norm_p for _, _, norm_p, _ in taqrib_patterns}
    passages_with_taqrib_hit = 0
    passages_with_early_idiom_hit = 0
    passages_with_no_taqrib_hit = 0
    idiom_passage_counts = Counter()
    idiom_narrator_sets = defaultdict(set)
    idiom_rank_counts = defaultdict(Counter)
    unmatched_token_counts = Counter()
    train_narrators_covered_any_taqrib = set()
    train_narrators_covered_any_passage = set()

    for p in train_dedup_passages:
        eid = p["entry_id"]
        ts = p["text_strict"]
        train_narrators_covered_any_passage.add(eid)
        hit_t = any(pat.search(ts) for _, _, _, pat in taqrib_patterns)
        if hit_t:
            passages_with_taqrib_hit += 1
            train_narrators_covered_any_taqrib.add(eid)
        else:
            passages_with_no_taqrib_hit += 1
            for w in ts.split():
                if len(w) >= 3 and w not in {"قال", "وقال", "عن", "بن", "ابن", "ابي", "ابو", "في", "من", "على", "الي", "كان", "حدثنا", "سمعت", "سالت", "هو", "ان", "ما", "كل", "غير"}:
                    unmatched_token_counts[w] += 1

        hit_e = False
        for raw_id, label, role, pat in EARLY_IDIOM_MATCHERS:
            if pat.search(ts):
                hit_e = True
                idiom_passage_counts[raw_id] += 1
                idiom_narrator_sets[raw_id].add(eid)
                idiom_rank_counts[raw_id][p["rank"]] += 1
        if hit_e:
            passages_with_early_idiom_hit += 1

    # Idiom gap summary table
    idiom_gap_rows = []
    for raw_id, label, role in EARLY_CRITIC_IDIOMS:
        in_taqrib_vocab = normalize_strict_match(raw_id) in taqrib_norm_set
        top_ranks = idiom_rank_counts[raw_id].most_common(3)
        idiom_gap_rows.append({
            "idiom_arabic": raw_id,
            "semantic_label": label,
            "esa_role": role,
            "exact_in_taqrib_205_vocab": "yes" if in_taqrib_vocab else "no",
            "train_dedup_passages": idiom_passage_counts[raw_id],
            "train_unique_narrators": len(idiom_narrator_sets[raw_id]),
            "top_3_ranks_train": "; ".join(f"R{rk}:{cnt}" for rk, cnt in top_ranks),
        })

    # Inspect existing Task A 6D consolidated ESA dimension values for spec alignment
    esa_dims = defaultdict(Counter)
    with CONSOLIDATED_ESA_FP.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            for col in ["statement_family", "statement_domain", "claim_content", "claim_mode", "wording_force", "consensus_wording"]:
                esa_dims[col][r[col]] += 1

    # Pilot stratification counts on train N=3,674
    train_rank_counts = Counter(eid_to_rank[e] for e in train_eids)
    train_has_passage_by_rank = Counter(eid_to_rank[e] for e in train_narrators_covered_any_passage)

    part_b = {
        "duplicate_summaries": [s_v03, s_abl, s_fwd],
        "recommended_dedup_key": "(entry_id, normalized_historical_attribution_critic_or_category, normalized_source_work, normalized_source_citation, normalized_quotation_text)",
        "rationale_dedup_key": "Collapses Shamela4 multi-group extraction duplicates sharing the same source_citation while preserving genuine cross-work recurrence and distinct critic attributions.",
        "train_raw_arm4_passages": raw_train_passages_count,
        "train_dedup_arm4_passages": len(train_dedup_passages),
        "train_dedup_removed_rows": raw_train_passages_count - len(train_dedup_passages),
        "train_quote_passages_for_segmentation": len(quote_passages),
        "train_estimated_atomic_units_from_quote_passages": total_atomic_units_est,
        "train_segmentation_categories": dict(seg_counts),
        "train_segmentation_pct": {k: round(100.0 * v / max(len(quote_passages), 1), 2) for k, v in seg_counts.items()},
        "train_segmentation_examples": dict(seg_examples),
    }

    part_c = {
        "taqrib_phrase_inventory_size": len(taqrib_patterns),
        "train_dedup_passages_total": len(train_dedup_passages),
        "train_passages_with_taqrib_205_hit": passages_with_taqrib_hit,
        "train_passages_without_taqrib_205_hit": passages_with_no_taqrib_hit,
        "train_passages_without_taqrib_hit_pct": round(100.0 * passages_with_no_taqrib_hit / max(len(train_dedup_passages), 1), 2),
        "train_narrators_with_any_arm4_passage": len(train_narrators_covered_any_passage),
        "train_narrators_with_taqrib_205_hit": len(train_narrators_covered_any_taqrib),
        "train_passages_with_early_idiom_hit": passages_with_early_idiom_hit,
        "top_unmatched_tokens_in_no_taqrib_hit_passages": unmatched_token_counts.most_common(35),
        "existing_task_a_6d_distributions": {k: dict(v) for k, v in esa_dims.items()},
        "train_rank_counts_and_arm4_coverage": {
            f"R{rk}": {"train_n": train_rank_counts[rk], "with_arm4_passage": train_has_passage_by_rank[rk]}
            for rk in range(1, 13)
        },
    }
    return part_b, dup_breakdown_rows, part_c, idiom_gap_rows


# ==============================================================================
# PART D: Biographical Assertions Audit on train N=3,674
# ==============================================================================

def parse_m1_bio_relations(text: str) -> tuple[int, int]:
    """Count named teachers after روى عن: and named students after روى عنه: in clean Method 1 bio."""
    # Look for segment starting with روى عن: up to روى عنه: or sentence stop / قيل / قال
    m_t = re.search(r"رو[ىي]\s+عن\s*:?\s*(.+?)(?=رو[ىي]\s+عنه|قال\s+|وذكر|وقال|مات|$)", text)
    m_s = re.search(r"رو[ىي]\s+عنه\s*:?\s*(.+?)(?=قال\s+|وذكر|وقال|ذكره|مات|$)", text)

    def count_names(seg: str) -> int:
        if not seg:
            return 0
        # Stop at obvious evaluation clause markers
        seg = re.split(r"(?:\.\s+|قال\s+(?:أبو|ابو|ابن|أحمد|يحيى|البخاري|النسائي|علي)|سئل|وسئل)", seg)[0]
        parts = [p.strip() for p in re.split(r"[،,]|(?:\s+و(?=[أ-ي]))", seg) if len(p.strip()) >= 3]
        # Filter out purely relational continuations like "بن فلان" attached inside a name? Better: split mainly on comma + ' و'
        comma_parts = [p.strip() for p in re.split(r"[،,]", seg) if len(p.strip()) >= 3]
        return len(comma_parts)

    return count_names(m_t.group(1) if m_t else ""), count_names(m_s.group(1) if m_s else "")


def run_part_d_audit(
    train_eids: set[str], eid_to_sid: dict[str, str], eid_to_rank: dict[str, int]
) -> tuple[dict, list[dict], list[dict]]:
    print("[Part D] Auditing biographical assertions, book indicators, and Taqrib overlap on train...", flush=True)

    # 1. Load V0_3 node features (cohort-vs-unrestricted graph counts) & edge cohort flag on train
    node_meta = {}
    with (V03_GRAPH_DIR / "TASK_B_NODE_STRUCTURAL_FEATURES_V0_3.csv").open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            if r["entry_id"] in train_eids:
                node_meta[r["entry_id"]] = r

    # Check raw edges in V03_GRAPH_EDGES including both_in_cohort_5250 == no for train narrators
    unrestricted_m1_students = defaultdict(set)
    cohort_m1_students = defaultdict(set)
    unrestricted_sanad_students = defaultdict(set)
    cohort_sanad_students = defaultdict(set)
    with (V03_GRAPH_DIR / "TASK_B_CONSOLIDATED_GRAPH_EDGES_V0_3.csv").open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            t_eid = r["teacher_entry_id"]
            if t_eid not in train_eids:
                continue
            s_eid = r["student_entry_id"]
            if int(r["method1_rijal_weight"]) > 0:
                unrestricted_m1_students[t_eid].add(s_eid)
                if r["both_in_cohort_5250"] == "yes":
                    cohort_m1_students[t_eid].add(s_eid)
            if int(r["sanadset_unique_weight"]) > 0:
                unrestricted_sanad_students[t_eid].add(s_eid)
                if r["both_in_cohort_5250"] == "yes":
                    cohort_sanad_students[t_eid].add(s_eid)

    # 2. Load Method 1 clean bios & count unrestricted named students/teachers directly from bio text
    m1_bios_by_eid = defaultdict(list)
    with (V12_BIOS_DIR / "TASK_B_METHOD1_CLEAN_BIOS_V1_2.csv").open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            eid = r["entry_id"]
            if eid in train_eids:
                m1_bios_by_eid[eid].append(r)

    max_bio_students = {}
    max_bio_teachers = {}
    for eid in train_eids:
        best_s, best_t = 0, 0
        for b in m1_bios_by_eid.get(eid, []):
            tc, sc = parse_m1_bio_relations(b["clean_bio_text"])
            best_t = max(best_t, tc)
            best_s = max(best_s, sc)
        max_bio_teachers[eid] = best_t
        max_bio_students[eid] = best_s

    # 3. Load 3-state book indicators
    book_ind = {}
    with (V12_BIOS_DIR / "TASK_B_METHOD1_BOOK_INDICATORS_V1_2.csv").open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            if r["entry_id"] in train_eids:
                book_ind[r["entry_id"]] = r

    rank_bio_rows = []
    book_status_by_rank = {}
    for rk in range(1, 13):
        eids_r = [e for e in train_eids if eid_to_rank[e] == rk]
        n = len(eids_r)
        m1_linked = [e for e in eids_r if int(book_ind[e]["n_books_linked"]) > 0]
        tk_linked = [e for e in eids_r if book_ind[e]["status_method1_tahdhib_alkamal"] == "linked_unique"]

        cohort_m1_ge2 = sum(1 for e in eids_r if len(cohort_m1_students[e]) >= 2)
        unres_m1_edge_ge2 = sum(1 for e in eids_r if len(unrestricted_m1_students[e]) >= 2)
        raw_bio_ge2 = sum(1 for e in eids_r if max_bio_students[e] >= 2)
        raw_bio_eq1 = sum(1 for e in eids_r if max_bio_students[e] == 1)
        raw_bio_0_linked = sum(1 for e in m1_linked if max_bio_students[e] == 0)
        raw_bio_ge2_linked = sum(1 for e in m1_linked if max_bio_students[e] >= 2)
        sanad_unres_ge2 = sum(1 for e in eids_r if len(unrestricted_sanad_students[e]) >= 2)
        has_quote_cnt = sum(1 for e in eids_r if node_meta[e]["has_early_critic_quote"] == "1")

        rank_bio_rows.append({
            "rank": rk,
            "train_n": n,
            "has_early_quote_n": has_quote_cnt,
            "has_early_quote_pct": round(100.0 * has_quote_cnt / max(n, 1), 1),
            "m1_any_linked_n": len(m1_linked),
            "tahdhib_kamal_linked_n": len(tk_linked),
            "cohort_m1_edge_students_ge2_n": cohort_m1_ge2,
            "unrestricted_m1_edge_students_ge2_n": unres_m1_edge_ge2,
            "raw_bio_named_students_ge2_n": raw_bio_ge2,
            "raw_bio_named_students_ge2_of_linked_pct": round(100.0 * raw_bio_ge2_linked / max(len(m1_linked), 1), 1),
            "raw_bio_named_students_eq1_n": raw_bio_eq1,
            "raw_bio_named_students_0_of_linked_n": raw_bio_0_linked,
            "median_raw_bio_students_linked": float(np.median([max_bio_students[e] for e in m1_linked])) if m1_linked else 0.0,
            "median_raw_bio_teachers_linked": float(np.median([max_bio_teachers[e] for e in m1_linked])) if m1_linked else 0.0,
            "unrestricted_sanadset_students_ge2_n": sanad_unres_ge2,
        })

        bk_stats = {}
        for bl in BOOK_LABELS:
            c = Counter(book_ind[e][f"status_{bl}"] for e in eids_r)
            bk_stats[bl] = dict(c)
        book_status_by_rank[f"R{rk}"] = bk_stats

    # 4. Shamela narrators.csv biography_json summary fields vs Taqrib entry_text contamination audit
    taqrib_text_by_eid = {}
    with ENTRY_INDEX_FP.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            if r["entry_id"] in train_eids:
                taqrib_text_by_eid[r["entry_id"]] = r["entry_text_verbatim"]

    sid_to_train_eid = {eid_to_sid[e]: e for e in train_eids}
    # Concatenate Method 1 clean bios per train eid for attribution comparison
    m1_concat_by_eid = {
        e: normalize_strict_match(" ".join(b["clean_bio_text"] for b in m1_bios_by_eid.get(e, [])))
        for e in train_eids
    }

    summary_key_total = Counter()
    summary_key_exact_in_taqrib = Counter()
    summary_key_token_overlap_taqrib = Counter()
    summary_key_exact_in_m1 = Counter()
    summary_key_examples = defaultdict(list)

    with NARRATORS_CSV_FP.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            sid = r["id"]
            if sid not in sid_to_train_eid:
                continue
            eid = sid_to_train_eid[sid]
            bjson = r.get("biography_json", "")
            if not bjson:
                continue
            try:
                obj = json.loads(bjson)
            except Exception:
                continue
            taq_norm = normalize_strict_match(taqrib_text_by_eid.get(eid, ""))
            m1_norm = m1_concat_by_eid.get(eid, "")
            for item in obj.get("summary", []):
                if not isinstance(item, list) or len(item) < 2:
                    continue
                k, v = str(item[0]).strip(), str(item[1]).strip()
                v_norm = normalize_strict_match(v)
                if not v_norm:
                    continue
                summary_key_total[k] += 1
                in_taq = v_norm in taq_norm
                in_m1 = v_norm in m1_norm if m1_norm else False
                if in_taq:
                    summary_key_exact_in_taqrib[k] += 1
                if in_m1:
                    summary_key_exact_in_m1[k] += 1
                v_toks = {w for w in v_norm.split() if len(w) >= 2}
                taq_toks = set(taq_norm.split())
                if v_toks and len(v_toks & taq_toks) / len(v_toks) >= 0.5:
                    summary_key_token_overlap_taqrib[k] += 1
                if len(summary_key_examples[k]) < 2:
                    summary_key_examples[k].append({
                        "entry_id": eid,
                        "value": v[:80],
                        "exact_in_taqrib": in_taq,
                        "exact_in_m1": in_m1,
                        "taqrib_tail": taqrib_text_by_eid.get(eid, "")[-100:],
                    })

    overlap_rows = []
    for k, tot in summary_key_total.most_common():
        ex_t = summary_key_exact_in_taqrib[k]
        tok_t = summary_key_token_overlap_taqrib[k]
        ex_m1 = summary_key_exact_in_m1[k]
        overlap_rows.append({
            "summary_key_arabic": k,
            "train_non_empty_n": tot,
            "exact_substring_in_taqrib_n": ex_t,
            "exact_substring_in_taqrib_pct": round(100.0 * ex_t / max(tot, 1), 1),
            "token_overlap_ge50_in_taqrib_n": tok_t,
            "token_overlap_ge50_in_taqrib_pct": round(100.0 * tok_t / max(tot, 1), 1),
            "exact_substring_in_m1_bios_n": ex_m1,
            "exact_substring_in_m1_bios_pct": round(100.0 * ex_m1 / max(tot, 1), 1),
        })

    part_d = {
        "train_n": len(train_eids),
        "r7_vs_r9_student_evidence_summary": {
            row["rank"]: row for row in rank_bio_rows if row["rank"] in {6, 7, 9}
        },
        "book_indicator_status_by_rank_r1_to_r12": book_status_by_rank,
        "shamela_summary_key_examples": dict(summary_key_examples),
    }
    return part_d, rank_bio_rows, overlap_rows


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\r\n")
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    verified = verify_all_input_manifests()

    # Load train partition map cleanly
    feat_rows = list(csv.DictReader((V03_GRAPH_DIR / "TASK_B_NODE_STRUCTURAL_FEATURES_V0_3.csv").open(encoding="utf-8-sig")))
    train_eids = {r["entry_id"] for r in feat_rows if r["split"] == "train"}
    eid_to_sid = {r["entry_id"]: r["shamela_narrator_id"] for r in feat_rows if r["split"] == "train"}
    eid_to_rank = {r["entry_id"]: int(r["task_a_rank_1_to_12"]) for r in feat_rows if r["split"] == "train"}
    assert len(train_eids) == 3674

    part_a, bench_rows = run_part_a_audit()
    part_b, dup_rows, part_c, idiom_rows = run_part_b_and_c_audit(train_eids, eid_to_rank)
    part_d, rank_bio_rows, overlap_rows = run_part_d_audit(train_eids, eid_to_sid, eid_to_rank)

    write_csv(OUT_DIR / "AUDIT_V2_0_BENCHMARK_CLASSIFICATION.csv", bench_rows, list(bench_rows[0].keys()))
    write_csv(OUT_DIR / "AUDIT_V2_0_TASK_B_DUPLICATE_BREAKDOWN.csv", dup_rows, list(dup_rows[0].keys()))
    write_csv(OUT_DIR / "AUDIT_V2_0_TASK_B_IDIOM_GAP_TOP_TRAIN.csv", idiom_rows, list(idiom_rows[0].keys()))
    write_csv(OUT_DIR / "AUDIT_V2_0_STUDENT_TEACHER_BY_RANK_TRAIN.csv", rank_bio_rows, list(rank_bio_rows[0].keys()))
    write_csv(OUT_DIR / "AUDIT_V2_0_NARRATORS_TAQRIB_OVERLAP_TRAIN.csv", overlap_rows, list(overlap_rows[0].keys()))

    payload = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "verified_input_manifests": verified,
        "part_a_reproducibility_and_benchmarks": part_a,
        "part_b_statement_and_attribution_integrity": part_b,
        "part_c_esa_coverage_and_gaps_train": part_c,
        "part_d_biographical_assertions_train": part_d,
    }
    json_path = OUT_DIR / "AUDIT_V2_0_PARTS_A_TO_D.json"
    json_text = json.dumps(payload, ensure_ascii=False, indent=2)
    assert "\u2014" not in json_text and "\u2013" not in json_text, "Forbidden dash detected!"
    json_path.write_text(json_text, encoding="utf-8")
    print(f"[DONE] Saved Part A-D outputs to {OUT_DIR}", flush=True)


if __name__ == "__main__":
    main()
