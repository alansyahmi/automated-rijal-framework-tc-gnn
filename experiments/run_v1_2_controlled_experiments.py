"""v1.2 Controlled Phase A (Method 1 Evidence), Phase B (Critic Attribution), & Phase C (Error Analysis).

Follows every methodological safeguard approved after Stage 1 / Stage 3 audit:
- Preserves v1.0, v1.1, and audit_v1_1 completely immutable.
- Uses features designed/verified strictly on train-only feasibility (N=3,674),
  5-fold narrator-disjoint OOF text fitting strictly inside train, validation-only
  model/hyperparameter/checkpoint selection (val N=788), and single 5-seed
  evaluation on the frozen test set (test N=788).
- Keeps graph architecture fixed (ConcatDirGNN + EarlyMLP from v1.1) so gains
  can be attributed cleanly to historically admissible evidence.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

csv.field_size_limit(10_000_000)

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
V12_BIOS_DIR = PIPELINE_DIR / "task_b_method1_clean_bios_v1_2_2026-11-18"
OUT_DIR = ROOT / "results/v1_2_controlled_experiments_2026-11-18"

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

PRAISE_CUES = ("ثقة", "ثبت", "حجة", "صدوق", "لا بأس به", "ليس به بأس", "مأمون", "إمام", "حافظ", "صالح الحديث")
CRIT_CUES = ("ضعيف", "متروك", "كذاب", "يضع", "وضاع", "منكر الحديث", "ليس بشيء", "لا يكتب حديثه", "واهي", "مجهول", "متهم")
MIXED_QUAL_CUES = ("يهم", "يخطئ", "له أوهام", "لين", "فيه نظر", "مختلف فيه", "مستور", "لا يعرف", "روى عنه جماعة", "لم يرو عنه غير")

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


def verify_all_input_manifests() -> dict[str, dict[str, str]]:
    verified: dict[str, dict[str, str]] = {}
    for pkg_dir in [V03_INPUT_DIR, V04_INPUT_DIR, V03_GRAPH_DIR, V12_BIOS_DIR]:
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


def load_cohort_and_graph():
    feat_fp = V03_GRAPH_DIR / "TASK_B_NODE_STRUCTURAL_FEATURES_V0_3.csv"
    with feat_fp.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 5250

    split_eids, split_sids = defaultdict(set), defaultdict(set)
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
    cohort_deg = np.array([int(r["cohort_consolidated_degree"]) for r in rows], dtype=np.int64)

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

    return (
        rows,
        entry_ids,
        shamela_ids,
        eid_to_idx,
        y,
        splits,
        has_quote,
        cohort_deg,
        X_topo,
        row_norm(adj_t2s),
        row_norm(adj_s2t),
    )


def load_evidence_and_features(entry_ids: list[str]):
    """Load Arm 4, Clean Method 1 Bios, 3-State Book Indicators, and Objective Critic Attribution."""
    eid_set = set(entry_ids)

    v03_plain: defaultdict[str, list[str]] = defaultdict(list)
    v03_prefixed: defaultdict[str, list[str]] = defaultdict(list)
    fwaed_plain: defaultdict[str, list[str]] = defaultdict(list)
    abl_plain: defaultdict[str, list[str]] = defaultdict(list)
    abl_prefixed: defaultdict[str, list[str]] = defaultdict(list)

    critics_all: defaultdict[str, set[str]] = defaultdict(set)
    critics_praise: defaultdict[str, set[str]] = defaultdict(set)
    critics_crit: defaultdict[str, set[str]] = defaultdict(set)
    critics_mixed: defaultdict[str, set[str]] = defaultdict(set)
    sources_all: defaultdict[str, set[str]] = defaultdict(set)
    has_ambig_critic: defaultdict[str, int] = defaultdict(int)

    def normalize_critic_tag(critic: str) -> str:
        c = normalize_arabic(critic).strip()
        if not c:
            return "CRITIC_UNATTRIBUTED"
        if len(c) > 40 or "،" in c or "غيره" in c:
            return "CRITIC_COMPOUND_OR_AMBIGUOUS"
        return "CRITIC_" + re.sub(r"\s+", "_", c)

    def record_critic_passage(eid: str, critic: str, src_work: str, txt_norm: str, target_prefixed: defaultdict[str, list[str]]):
        tag = normalize_critic_tag(critic)
        target_prefixed[eid].append(f"{tag} : {txt_norm}")
        if tag in {"CRITIC_UNATTRIBUTED", "CRITIC_COMPOUND_OR_AMBIGUOUS"}:
            has_ambig_critic[eid] = 1
        critics_all[eid].add(tag)
        if src_work:
            sources_all[eid].add(src_work)
        hp = any(k in txt_norm for k in PRAISE_CUES)
        hc = any(k in txt_norm for k in CRIT_CUES)
        hm = any(k in txt_norm for k in MIXED_QUAL_CUES)
        if hp and not hc and not hm:
            critics_praise[eid].add(tag)
        elif hc and not hp:
            critics_crit[eid].add(tag)
        elif (hp and hc) or hm:
            critics_mixed[eid].add(tag)

    with (V03_INPUT_DIR / "TASK_B_ELIGIBLE_HISTORICAL_PASSAGES_V0_3.csv").open(
        encoding="utf-8-sig", newline=""
    ) as f:
        for r in csv.DictReader(f):
            src = r.get("source_work_normalised", "") + " " + r.get("source_citation_exact", "")
            spk = r.get("historical_attribution_critic", "")
            for t in FORBIDDEN_TERMS:
                assert t not in src and t not in spk
            eid = r["entry_id"]
            if eid not in eid_set:
                continue
            txt = normalize_arabic(r["quotation_text_exact"])
            if txt:
                v03_plain[eid].append(txt)
                record_critic_passage(eid, spk, r.get("source_work_normalised", ""), txt, v03_prefixed)

    with (V04_INPUT_DIR / "TASK_B_FWAED_PASSAGES_V0_4.csv").open(
        encoding="utf-8-sig", newline=""
    ) as f:
        for r in csv.DictReader(f):
            src = r.get("source_citation_exact", "")
            for t in FORBIDDEN_TERMS:
                assert t not in src
            eid = r["entry_id"]
            if eid not in eid_set:
                continue
            txt = normalize_arabic(r["fwaed_text_exact"])
            if txt:
                fwaed_plain[eid].append(txt)

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
            if eid not in eid_set:
                continue
            txt = normalize_arabic(r["quotation_text_exact"])
            if txt:
                abl_plain[eid].append(txt)
                record_critic_passage(eid, spk, "تهذيب التهذيب", txt, abl_prefixed)

    # Clean Method 1 full biographies
    m1_bios: defaultdict[str, list[str]] = defaultdict(list)
    with (V12_BIOS_DIR / "TASK_B_METHOD1_CLEAN_BIOS_V1_2.csv").open(
        encoding="utf-8-sig", newline=""
    ) as f:
        for r in csv.DictReader(f):
            eid = r["entry_id"]
            if eid in eid_set:
                txt = normalize_arabic(r["clean_bio_text"])
                if txt:
                    m1_bios[eid].append(f"SOURCE_{r['source_label']} : {txt}")

    # 3-State Method 1 book indicators aligned strictly to entry_ids
    ind_by_eid = {}
    with (V12_BIOS_DIR / "TASK_B_METHOD1_BOOK_INDICATORS_V1_2.csv").open(
        encoding="utf-8-sig", newline=""
    ) as f:
        for r in csv.DictReader(f):
            ind_by_eid[r["entry_id"]] = r

    book_ind_cols = []
    for bl in BOOK_LABELS:
        book_ind_cols.extend([f"is_linked_{bl}", f"is_ambig_{bl}", f"log1p_chars_{bl}"])
    X_book_ind = np.zeros((len(entry_ids), len(book_ind_cols)), dtype=np.float32)
    for i, eid in enumerate(entry_ids):
        ir = ind_by_eid[eid]
        for j, col in enumerate(book_ind_cols):
            X_book_ind[i, j] = float(ir[col])

    # Objective structured critic features (9 cols, zero subjective strictness weighting!)
    X_critic_struct = np.zeros((len(entry_ids), 9), dtype=np.float32)
    for i, eid in enumerate(entry_ids):
        nc = len(critics_all[eid])
        np_c = len(critics_praise[eid])
        nc_c = len(critics_crit[eid])
        nm_c = len(critics_mixed[eid])
        ns = len(sources_all[eid])
        conflict = 1.0 if (np_c > 0 and nc_c > 0) else 0.0
        denom = max(nc, 1)
        X_critic_struct[i] = [
            math.log1p(nc),
            math.log1p(np_c),
            math.log1p(nc_c),
            math.log1p(nm_c),
            conflict,
            np_c / denom,
            nc_c / denom,
            math.log1p(ns),
            float(has_ambig_critic[eid]),
        ]

    text_arm4_plain = [" \n ".join(v03_plain[e] + fwaed_plain[e] + abl_plain[e]) for e in entry_ids]
    text_arm4_plus_m1 = [" \n ".join(v03_plain[e] + fwaed_plain[e] + abl_plain[e] + m1_bios[e]) for e in entry_ids]
    text_arm4_critic_prefixed = [
        " \n ".join(v03_prefixed[e] + [f"FWAED_NOTE : {ft}" for ft in fwaed_plain[e]] + abl_prefixed[e])
        for e in entry_ids
    ]
    text_combined_m1_critic = [
        " \n ".join(v03_prefixed[e] + [f"FWAED_NOTE : {ft}" for ft in fwaed_plain[e]] + abl_prefixed[e] + m1_bios[e])
        for e in entry_ids
    ]

    return (
        {
            "arm4_plain": text_arm4_plain,
            "arm4_plus_m1_clean_bios": text_arm4_plus_m1,
            "arm4_critic_prefixed": text_arm4_critic_prefixed,
            "arm4_m1_plus_critic_prefixed": text_combined_m1_critic,
        },
        X_book_ind,
        X_critic_struct,
    )


def make_class_weights(y_train: np.ndarray, mode: str) -> dict[int, float] | None:
    if mode == "none":
        return None
    counts = Counter(y_train.tolist())
    n, k = len(y_train), 12
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


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    r2_mask = y_true >= 1
    yt3, yp3 = tier3_map(y_true), tier3_map(y_pred)
    return {
        "n": int(len(y_true)),
        "macro_f1": float(f1_score(y_true, y_pred, labels=list(range(12)), average="macro", zero_division=0)),
        "r2_12_macro_f1": float(
            f1_score(y_true[r2_mask], y_pred[r2_mask], labels=list(range(1, 12)), average="macro", zero_division=0)
        ),
        "r2_12_acc": float(accuracy_score(y_true[r2_mask], y_pred[r2_mask])),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "weighted_f1": float(f1_score(y_true, y_pred, labels=list(range(12)), average="weighted", zero_division=0)),
        "qwk": float(cohen_kappa_score(y_true, y_pred, weights="quadratic")),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "tier3_macro_f1": float(f1_score(yt3, yp3, labels=[0, 1, 2], average="macro", zero_division=0)),
        "tier3_acc": float(accuracy_score(yt3, yp3)),
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
    assert list(clf.classes_) == list(range(12))
    return clf.predict_log_proba(X_ev).astype(np.float32)


def generate_oof_text_features(
    arm_name: str,
    texts: list[str],
    entry_ids: list[str],
    shamela_ids: list[str],
    y: np.ndarray,
    tr_mask: np.ndarray,
    va_mask: np.ndarray,
    te_mask: np.ndarray,
):
    tr_idx = np.where(tr_mask)[0]
    va_idx = np.where(va_mask)[0]
    te_idx = np.where(te_mask)[0]
    va_te_idx = np.concatenate([va_idx, te_idx])

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    folds = list(skf.split(tr_idx, y[tr_idx]))
    for f_tr, f_va in folds:
        assert not (set(entry_ids[i] for i in tr_idx[f_tr]) & set(entry_ids[i] for i in tr_idx[f_va]))
        assert not (set(shamela_ids[i] for i in tr_idx[f_tr]) & set(shamela_ids[i] for i in tr_idx[f_va]))

    # Hyperparameters selected strictly by train OOF Macro-F1 (zero val/test peeking!)
    best_cfg, best_oof_f1, best_oof_logp = None, -1.0, None
    for cw_mode in ["none", "sqrt"]:
        for c_val in [1.0, 2.0]:
            fold_preds = Parallel(n_jobs=5)(
                delayed(fit_tfidf_logreg_predict_log_proba)(
                    [texts[i] for i in tr_idx[f_tr]],
                    y[tr_idx[f_tr]],
                    [texts[i] for i in tr_idx[f_va]],
                    c_val,
                    cw_mode,
                )
                for f_tr, f_va in folds
            )
            oof_logp = np.zeros((len(tr_idx), 12), dtype=np.float32)
            for (_f_tr, f_va), fp in zip(folds, fold_preds):
                oof_logp[f_va] = fp
            oof_f1 = float(
                f1_score(y[tr_idx], oof_logp.argmax(1), labels=list(range(12)), average="macro", zero_division=0)
            )
            if oof_f1 > best_oof_f1:
                best_oof_f1 = oof_f1
                best_cfg = {"C": c_val, "class_weight": cw_mode, "train_oof_macro_f1": oof_f1}
                best_oof_logp = oof_logp

    assert best_cfg is not None and best_oof_logp is not None
    va_te_logp = fit_tfidf_logreg_predict_log_proba(
        [texts[i] for i in tr_idx],
        y[tr_idx],
        [texts[i] for i in va_te_idx],
        best_cfg["C"],
        best_cfg["class_weight"],
    )
    all_logp = np.zeros((len(texts), 12), dtype=np.float32)
    all_logp[tr_idx] = best_oof_logp
    all_logp[va_te_idx] = va_te_logp
    print(f"[oof] {arm_name} | OOF_MacroF1={best_oof_f1:.4f} | val_MacroF1={f1_score(y[va_mask], all_logp[va_mask].argmax(1), labels=list(range(12)), average='macro', zero_division=0):.4f}", flush=True)
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

    def forward(self, x: torch.Tensor, adj_t2s: torch.Tensor, adj_s2t: torch.Tensor) -> torch.Tensor:
        h_ego = self.ego_fc(x)
        h_in = self.t2s_fc(torch.sparse.mm(adj_t2s, x))
        h_out = self.s2t_fc(torch.sparse.mm(adj_s2t, x))
        h = F.relu(self.bn(torch.cat([h_ego, h_in, h_out], dim=1)))
        h = F.dropout(h, p=self.dropout, training=self.training)
        return self.head(h)


def train_torch_run(
    arch: str,
    X_np: np.ndarray,
    y_np: np.ndarray,
    tr_mask: np.ndarray,
    va_mask: np.ndarray,
    adj_t2s: torch.Tensor,
    adj_s2t: torch.Tensor,
    device: torch.device,
    cfg: dict,
    seed: int,
):
    torch.manual_seed(seed)
    np.random.seed(seed)
    X_t = torch.tensor(X_np, dtype=torch.float32, device=device)
    y_t = torch.tensor(y_np, dtype=torch.long, device=device)
    tr_t = torch.tensor(tr_mask, dtype=torch.bool, device=device)

    cw_dict = make_class_weights(y_np[tr_mask], cfg["cw"])
    if cw_dict is None:
        criterion = nn.CrossEntropyLoss()
    else:
        criterion = nn.CrossEntropyLoss(
            weight=torch.tensor([cw_dict[c] for c in range(12)], dtype=torch.float32, device=device)
        )

    in_dim = X_np.shape[1]
    model = (
        MLPNet(in_dim, cfg["hidden_dim"], 12, cfg["dropout"]).to(device)
        if arch == "mlp"
        else ConcatDirGNN(in_dim, cfg["hidden_dim"], 12, cfg["dropout"]).to(device)
    )
    opt = torch.optim.AdamW(model.parameters(), lr=cfg["lr"], weight_decay=cfg["wd"])

    best_val, best_pred, bad = -1.0, None, 0
    for _ in range(250):
        model.train()
        opt.zero_grad()
        logits = model(X_t) if arch == "mlp" else model(X_t, adj_t2s, adj_s2t)
        loss = criterion(logits[tr_t], y_t[tr_t])
        loss.backward()
        opt.step()

        model.eval()
        with torch.no_grad():
            ev = model(X_t) if arch == "mlp" else model(X_t, adj_t2s, adj_s2t)
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


def run_neural_experiment(
    name: str,
    phase: str,
    arch: str,
    X_np: np.ndarray,
    y_np: np.ndarray,
    tr_mask: np.ndarray,
    va_mask: np.ndarray,
    te_mask: np.ndarray,
    adj_t2s: torch.Tensor,
    adj_s2t: torch.Tensor,
    device: torch.device,
):
    configs = [
        {"hidden_dim": 128, "dropout": 0.4, "lr": 5e-3, "wd": 5e-3, "cw": "sqrt"},
        {"hidden_dim": 256, "dropout": 0.4, "lr": 5e-3, "wd": 5e-3, "cw": "sqrt"},
        {"hidden_dim": 128, "dropout": 0.5, "lr": 3e-3, "wd": 1e-2, "cw": "balanced"},
    ]
    best_cfg, best_tune = None, -1.0
    for cfg in configs:
        vf1, _ = train_torch_run(arch, X_np, y_np, tr_mask, va_mask, adj_t2s, adj_s2t, device, cfg, seed=42)
        if vf1 > best_tune:
            best_tune = vf1
            best_cfg = cfg
    assert best_cfg is not None

    va_ms, te_ms, te_preds = [], [], []
    for seed in SEEDS:
        _, preds = train_torch_run(arch, X_np, y_np, tr_mask, va_mask, adj_t2s, adj_s2t, device, best_cfg, seed=seed)
        va_ms.append(compute_metrics(y_np[va_mask], preds[va_mask]))
        te_ms.append(compute_metrics(y_np[te_mask], preds[te_mask]))
        te_preds.append(preds[te_mask])

    agg_test = {"n": te_ms[0]["n"]}
    for k in te_ms[0]:
        if k == "n":
            continue
        vals = [m[k] for m in te_ms]
        agg_test[k] = float(np.mean(vals))
        agg_test[f"{k}_std"] = float(np.std(vals, ddof=1))

    agg_val = {"n": va_ms[0]["n"]}
    for k in va_ms[0]:
        if k == "n":
            continue
        agg_val[k] = float(np.mean([m[k] for m in va_ms]))

    print(
        f"[done] {name} | val_f1={agg_val['macro_f1']:.4f} | test_f1={agg_test['macro_f1']:.4f} +/- {agg_test['macro_f1_std']:.4f} | "
        f"acc={agg_test['accuracy']:.4f} | qwk={agg_test['qwk']:.4f}",
        flush=True,
    )
    return {
        "name": name,
        "phase": phase,
        "cfg": best_cfg,
        "val_metrics": agg_val,
        "test_metrics": agg_test,
        "all_seed_test_preds": te_preds,
    }


def paired_bootstrap_multi_seed(y_true: np.ndarray, preds_a_5: list[np.ndarray], preds_b_5: list[np.ndarray], n_boot: int = 2000):
    rng = np.random.default_rng(42)
    n = len(y_true)
    d_f1, d_acc, d_qwk = [], [], []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        yt = y_true[idx]
        sf1, sacc, sqwk = [], [], []
        for pa, pb in zip(preds_a_5, preds_b_5):
            pa_s, pb_s = pa[idx], pb[idx]
            sf1.append(
                f1_score(yt, pa_s, labels=list(range(12)), average="macro", zero_division=0)
                - f1_score(yt, pb_s, labels=list(range(12)), average="macro", zero_division=0)
            )
            sacc.append(accuracy_score(yt, pa_s) - accuracy_score(yt, pb_s))
            sqwk.append(cohen_kappa_score(yt, pa_s, weights="quadratic") - cohen_kappa_score(yt, pb_s, weights="quadratic"))
        d_f1.append(np.mean(sf1))
        d_acc.append(np.mean(sacc))
        d_qwk.append(np.mean(sqwk))
    df1, dacc, dqwk = np.array(d_f1), np.array(d_acc), np.array(d_qwk)
    exact_df1 = np.mean([
        f1_score(y_true, pa, labels=list(range(12)), average="macro", zero_division=0)
        - f1_score(y_true, pb, labels=list(range(12)), average="macro", zero_division=0)
        for pa, pb in zip(preds_a_5, preds_b_5)
    ])
    exact_dacc = np.mean([accuracy_score(y_true, pa) - accuracy_score(y_true, pb) for pa, pb in zip(preds_a_5, preds_b_5)])
    exact_dqwk = np.mean([
        cohen_kappa_score(y_true, pa, weights="quadratic") - cohen_kappa_score(y_true, pb, weights="quadratic")
        for pa, pb in zip(preds_a_5, preds_b_5)
    ])
    return {
        "delta_macro_f1": float(exact_df1),
        "ci95_f1": [float(np.percentile(df1, 2.5)), float(np.percentile(df1, 97.5))],
        "p_f1": float(min(2.0 * min(np.mean(df1 <= 0), np.mean(df1 >= 0)), 1.0)),
        "delta_acc": float(exact_dacc),
        "p_acc": float(min(2.0 * min(np.mean(dacc <= 0), np.mean(dacc >= 0)), 1.0)),
        "delta_qwk": float(exact_dqwk),
        "p_qwk": float(min(2.0 * min(np.mean(dqwk <= 0), np.mean(dqwk >= 0)), 1.0)),
    }


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    verified = verify_all_input_manifests()
    rows, entry_ids, shamela_ids, eid_to_idx, y, splits, has_quote, cohort_deg, X_topo_raw, adj_t2s, adj_s2t = (
        load_cohort_and_graph()
    )
    adj_t2s, adj_s2t = adj_t2s.to(device), adj_s2t.to(device)
    text_arms, X_book_ind_raw, X_critic_raw = load_evidence_and_features(entry_ids)

    tr_mask = splits == "train"
    va_mask = splits == "val"
    te_mask = splits == "test"
    y_test = y[te_mask]

    # Fit tabular scalers STRICTLY on train
    X_topo = StandardScaler().fit(X_topo_raw[tr_mask]).transform(X_topo_raw).astype(np.float32)
    X_book_ind = StandardScaler().fit(X_book_ind_raw[tr_mask]).transform(X_book_ind_raw).astype(np.float32)
    X_critic = StandardScaler().fit(X_critic_raw[tr_mask]).transform(X_critic_raw).astype(np.float32)

    # Generate 5-fold narrator-disjoint OOF text features for all 4 text corpora
    oof_scaled = {}
    oof_raw = {}
    oof_cfgs = {}
    for arm_key, texts in text_arms.items():
        cfg, logp = generate_oof_text_features(
            arm_key, texts, entry_ids, shamela_ids, y, tr_mask, va_mask, te_mask
        )
        oof_cfgs[arm_key] = cfg
        oof_raw[arm_key] = logp
        oof_scaled[arm_key] = StandardScaler().fit(logp[tr_mask]).transform(logp).astype(np.float32)

    results = []

    def add_base_logreg(name: str, phase: str, arm_key: str):
        vp = oof_raw[arm_key][va_mask].argmax(1)
        tp = oof_raw[arm_key][te_mask].argmax(1)
        results.append({
            "name": name,
            "phase": phase,
            "cfg": oof_cfgs[arm_key],
            "val_metrics": compute_metrics(y[va_mask], vp),
            "test_metrics": compute_metrics(y_test, tp),
            "all_seed_test_preds": [tp] * 5,
        })

    # === Phase A: Method 1 Evidence ===
    add_base_logreg("PhaseA_ExpA_Arm4_BaseText_LogReg", "PhaseA_Baseline", "arm4_plain")
    results.append(run_neural_experiment(
        "PhaseA_ExpA_Arm4_EarlyMLP", "PhaseA_Baseline", "mlp",
        np.hstack([oof_scaled["arm4_plain"], X_topo]), y, tr_mask, va_mask, te_mask, adj_t2s, adj_s2t, device
    ))
    results.append(run_neural_experiment(
        "PhaseA_ExpA_Arm4_ConcatDirGNN", "PhaseA_Baseline", "dir_concat_gnn",
        np.hstack([oof_scaled["arm4_plain"], X_topo]), y, tr_mask, va_mask, te_mask, adj_t2s, adj_s2t, device
    ))

    add_base_logreg("PhaseA_ExpB_Arm4PlusM1Bios_BaseText_LogReg", "PhaseA_M1Bios", "arm4_plus_m1_clean_bios")
    results.append(run_neural_experiment(
        "PhaseA_ExpB_Arm4PlusM1Bios_OOFTextOnly_MLP", "PhaseA_M1Bios", "mlp",
        oof_scaled["arm4_plus_m1_clean_bios"], y, tr_mask, va_mask, te_mask, adj_t2s, adj_s2t, device
    ))
    results.append(run_neural_experiment(
        "PhaseA_ExpB_Arm4PlusM1Bios_EarlyMLP", "PhaseA_M1Bios", "mlp",
        np.hstack([oof_scaled["arm4_plus_m1_clean_bios"], X_topo]), y, tr_mask, va_mask, te_mask, adj_t2s, adj_s2t, device
    ))
    results.append(run_neural_experiment(
        "PhaseA_ExpB_Arm4PlusM1Bios_ConcatDirGNN", "PhaseA_M1Bios", "dir_concat_gnn",
        np.hstack([oof_scaled["arm4_plus_m1_clean_bios"], X_topo]), y, tr_mask, va_mask, te_mask, adj_t2s, adj_s2t, device
    ))

    results.append(run_neural_experiment(
        "PhaseA_ExpC_Arm4PlusBookInd_EarlyMLP", "PhaseA_BookInd", "mlp",
        np.hstack([oof_scaled["arm4_plain"], X_topo, X_book_ind]), y, tr_mask, va_mask, te_mask, adj_t2s, adj_s2t, device
    ))
    results.append(run_neural_experiment(
        "PhaseA_ExpC_Arm4PlusBookInd_ConcatDirGNN", "PhaseA_BookInd", "dir_concat_gnn",
        np.hstack([oof_scaled["arm4_plain"], X_topo, X_book_ind]), y, tr_mask, va_mask, te_mask, adj_t2s, adj_s2t, device
    ))

    results.append(run_neural_experiment(
        "PhaseA_ExpD_Arm4PlusM1BiosAndBookInd_EarlyMLP", "PhaseA_M1BiosAndBookInd", "mlp",
        np.hstack([oof_scaled["arm4_plus_m1_clean_bios"], X_topo, X_book_ind]), y, tr_mask, va_mask, te_mask, adj_t2s, adj_s2t, device
    ))
    results.append(run_neural_experiment(
        "PhaseA_ExpD_Arm4PlusM1BiosAndBookInd_ConcatDirGNN", "PhaseA_M1BiosAndBookInd", "dir_concat_gnn",
        np.hstack([oof_scaled["arm4_plus_m1_clean_bios"], X_topo, X_book_ind]), y, tr_mask, va_mask, te_mask, adj_t2s, adj_s2t, device
    ))

    # === Phase B: Critic Attribution (on Arm 4 base quotes) ===
    results.append(run_neural_experiment(
        "PhaseB_AblA_Arm4PlusCriticCounts_EarlyMLP", "PhaseB_CriticCounts", "mlp",
        np.hstack([oof_scaled["arm4_plain"], X_topo, X_critic]), y, tr_mask, va_mask, te_mask, adj_t2s, adj_s2t, device
    ))
    results.append(run_neural_experiment(
        "PhaseB_AblA_Arm4PlusCriticCounts_ConcatDirGNN", "PhaseB_CriticCounts", "dir_concat_gnn",
        np.hstack([oof_scaled["arm4_plain"], X_topo, X_critic]), y, tr_mask, va_mask, te_mask, adj_t2s, adj_s2t, device
    ))

    add_base_logreg("PhaseB_AblB_Arm4CriticPrefixed_BaseText_LogReg", "PhaseB_CriticPrefixed", "arm4_critic_prefixed")
    results.append(run_neural_experiment(
        "PhaseB_AblB_Arm4CriticPrefixed_EarlyMLP", "PhaseB_CriticPrefixed", "mlp",
        np.hstack([oof_scaled["arm4_critic_prefixed"], X_topo]), y, tr_mask, va_mask, te_mask, adj_t2s, adj_s2t, device
    ))
    results.append(run_neural_experiment(
        "PhaseB_AblB_Arm4CriticPrefixed_ConcatDirGNN", "PhaseB_CriticPrefixed", "dir_concat_gnn",
        np.hstack([oof_scaled["arm4_critic_prefixed"], X_topo]), y, tr_mask, va_mask, te_mask, adj_t2s, adj_s2t, device
    ))

    results.append(run_neural_experiment(
        "PhaseB_AblC_CombinedCriticCountsAndPrefixed_EarlyMLP", "PhaseB_CombinedCritic", "mlp",
        np.hstack([oof_scaled["arm4_critic_prefixed"], X_topo, X_critic]), y, tr_mask, va_mask, te_mask, adj_t2s, adj_s2t, device
    ))
    results.append(run_neural_experiment(
        "PhaseB_AblC_CombinedCriticCountsAndPrefixed_ConcatDirGNN", "PhaseB_CombinedCritic", "dir_concat_gnn",
        np.hstack([oof_scaled["arm4_critic_prefixed"], X_topo, X_critic]), y, tr_mask, va_mask, te_mask, adj_t2s, adj_s2t, device
    ))

    # Exploratory synthesis check: M1 Bios + Book Indicators + Critic Prefixed + Critic Counts
    results.append(run_neural_experiment(
        "Exploratory_AllV12Evidence_EarlyMLP", "Exploratory_Combined", "mlp",
        np.hstack([oof_scaled["arm4_m1_plus_critic_prefixed"], X_topo, X_book_ind, X_critic]), y, tr_mask, va_mask, te_mask, adj_t2s, adj_s2t, device
    ))
    results.append(run_neural_experiment(
        "Exploratory_AllV12Evidence_ConcatDirGNN", "Exploratory_Combined", "dir_concat_gnn",
        np.hstack([oof_scaled["arm4_m1_plus_critic_prefixed"], X_topo, X_book_ind, X_critic]), y, tr_mask, va_mask, te_mask, adj_t2s, adj_s2t, device
    ))

    # Write MODEL_COMPARISON_V1_2.csv
    with (OUT_DIR / "MODEL_COMPARISON_V1_2.csv").open("w", encoding="utf-8-sig", newline="") as f:
        fields = [
            "model_name", "phase", "val_macro_f1", "val_accuracy", "test_macro_f1", "test_macro_f1_std",
            "test_r2_12_macro_f1", "test_accuracy", "test_accuracy_std", "test_weighted_f1", "test_qwk",
            "test_mae", "test_tier3_macro_f1", "test_tier3_acc", "best_config_json",
        ]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in results:
            vm, tm = r["val_metrics"], r["test_metrics"]
            w.writerow({
                "model_name": r["name"],
                "phase": r["phase"],
                "val_macro_f1": f"{vm['macro_f1']:.4f}",
                "val_accuracy": f"{vm['accuracy']:.4f}",
                "test_macro_f1": f"{tm['macro_f1']:.4f}",
                "test_macro_f1_std": f"{tm.get('macro_f1_std', 0.0):.4f}",
                "test_r2_12_macro_f1": f"{tm['r2_12_macro_f1']:.4f}",
                "test_accuracy": f"{tm['accuracy']:.4f}",
                "test_accuracy_std": f"{tm.get('accuracy_std', 0.0):.4f}",
                "test_weighted_f1": f"{tm['weighted_f1']:.4f}",
                "test_qwk": f"{tm['qwk']:.4f}",
                "test_mae": f"{tm['mae']:.4f}",
                "test_tier3_macro_f1": f"{tm['tier3_macro_f1']:.4f}",
                "test_tier3_acc": f"{tm['tier3_acc']:.4f}",
                "best_config_json": json.dumps(r["cfg"], ensure_ascii=False),
            })

    by_name = {r["name"]: r for r in results}

    # Phase C Error Analysis across key GNN / Baseline runs (averaged across all 5 seeds!)
    q_te = has_quote[te_mask]
    deg_te = cohort_deg[te_mask]
    zq_all = q_te == 0
    zq_conn = (q_te == 0) & (deg_te > 0)
    zq_iso = (q_te == 0) & (deg_te == 0)

    def eval_phase_c(r_obj):
        p5 = r_obj["all_seed_test_preds"]
        r7_f1s, r7_to_r9s, r3_r4s, r4_r5s = [], [], [], []
        zq_f1s, zq_accs, czq_f1s, czq_accs, izq_f1s, izq_accs = [], [], [], [], [], []
        cm_sum = np.zeros((12, 12), dtype=np.float64)
        for p in p5:
            cm = confusion_matrix(y_test, p, labels=list(range(12)))
            cm_sum += cm
            _, _, f1_arr, _ = precision_recall_fscore_support(y_test, p, labels=list(range(12)), zero_division=0)
            r7_f1s.append(float(f1_arr[6]))
            r7_to_r9s.append(int(cm[6, 8]))  # True R7 (idx 6) -> Pred R9 (idx 8)
            r3_r4s.append(int(cm[2, 3] + cm[3, 2]))  # Mutual R3 <-> R4 errors
            r4_r5s.append(int(cm[3, 4] + cm[4, 3]))  # Mutual R4 <-> R5 errors
            zq_f1s.append(float(f1_score(y_test[zq_all], p[zq_all], labels=list(range(12)), average="macro", zero_division=0)))
            zq_accs.append(float(accuracy_score(y_test[zq_all], p[zq_all])))
            czq_f1s.append(float(f1_score(y_test[zq_conn], p[zq_conn], labels=list(range(12)), average="macro", zero_division=0)))
            czq_accs.append(float(accuracy_score(y_test[zq_conn], p[zq_conn])))
            izq_f1s.append(float(f1_score(y_test[zq_iso], p[zq_iso], labels=list(range(12)), average="macro", zero_division=0)))
            izq_accs.append(float(accuracy_score(y_test[zq_iso], p[zq_iso])))
        return {
            "r7_f1_mean": float(np.mean(r7_f1s)),
            "r7_to_r9_count_mean": float(np.mean(r7_to_r9s)),
            "r3_r4_mutual_err_mean": float(np.mean(r3_r4s)),
            "r4_r5_mutual_err_mean": float(np.mean(r4_r5s)),
            "zq_all_f1": float(np.mean(zq_f1s)),
            "zq_all_acc": float(np.mean(zq_accs)),
            "zq_conn_f1": float(np.mean(czq_f1s)),
            "zq_conn_acc": float(np.mean(czq_accs)),
            "zq_iso_f1": float(np.mean(izq_f1s)),
            "zq_iso_acc": float(np.mean(izq_accs)),
            "mean_cm": np.round(cm_sum / 5.0, 2).tolist(),
        }

    phase_c_diag = {r["name"]: eval_phase_c(r) for r in results}

    # Per-rank CSV (representative seed=42 + 5-seed mean precision/recall/F1!)
    with (OUT_DIR / "PER_RANK_METRICS_V1_2.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["model_name", "rank_1_to_12", "support", "f1_5seed_mean", "f1_5seed_std", "recall_5seed_mean", "precision_5seed_mean"])
        w.writeheader()
        for r in results:
            per_rk = [[] for _ in range(12)]
            rec_rk = [[] for _ in range(12)]
            prec_rk = [[] for _ in range(12)]
            sup_ref = None
            for p in r["all_seed_test_preds"]:
                pr, rc, f1a, sup = precision_recall_fscore_support(y_test, p, labels=list(range(12)), zero_division=0)
                sup_ref = sup
                for k in range(12):
                    prec_rk[k].append(float(pr[k]))
                    rec_rk[k].append(float(rc[k]))
                    per_rk[k].append(float(f1a[k]))
            for k in range(12):
                w.writerow({
                    "model_name": r["name"],
                    "rank_1_to_12": k + 1,
                    "support": int(sup_ref[k]),
                    "f1_5seed_mean": f"{np.mean(per_rk[k]):.4f}",
                    "f1_5seed_std": f"{np.std(per_rk[k], ddof=1):.4f}",
                    "recall_5seed_mean": f"{np.mean(rec_rk[k]):.4f}",
                    "precision_5seed_mean": f"{np.mean(prec_rk[k]):.4f}",
                })

    # Paired bootstrap vs PhaseA_ExpA_Arm4_ConcatDirGNN (and vs EarlyMLP inside each phase)
    base_gnn = by_name["PhaseA_ExpA_Arm4_ConcatDirGNN"]["all_seed_test_preds"]
    base_txt = by_name["PhaseA_ExpA_Arm4_BaseText_LogReg"]["all_seed_test_preds"]
    paired = {
        "PhaseA_ExpB_M1Bios_ConcatDirGNN_vs_ExpA_Arm4_ConcatDirGNN": paired_bootstrap_multi_seed(
            y_test, by_name["PhaseA_ExpB_Arm4PlusM1Bios_ConcatDirGNN"]["all_seed_test_preds"], base_gnn
        ),
        "PhaseA_ExpC_BookInd_ConcatDirGNN_vs_ExpA_Arm4_ConcatDirGNN": paired_bootstrap_multi_seed(
            y_test, by_name["PhaseA_ExpC_Arm4PlusBookInd_ConcatDirGNN"]["all_seed_test_preds"], base_gnn
        ),
        "PhaseA_ExpD_M1BiosAndBookInd_ConcatDirGNN_vs_ExpA_Arm4_ConcatDirGNN": paired_bootstrap_multi_seed(
            y_test, by_name["PhaseA_ExpD_Arm4PlusM1BiosAndBookInd_ConcatDirGNN"]["all_seed_test_preds"], base_gnn
        ),
        "PhaseA_ExpD_M1BiosAndBookInd_ConcatDirGNN_vs_ExpD_EarlyMLP": paired_bootstrap_multi_seed(
            y_test,
            by_name["PhaseA_ExpD_Arm4PlusM1BiosAndBookInd_ConcatDirGNN"]["all_seed_test_preds"],
            by_name["PhaseA_ExpD_Arm4PlusM1BiosAndBookInd_EarlyMLP"]["all_seed_test_preds"],
        ),
        "PhaseB_AblA_CriticCounts_ConcatDirGNN_vs_ExpA_Arm4_ConcatDirGNN": paired_bootstrap_multi_seed(
            y_test, by_name["PhaseB_AblA_Arm4PlusCriticCounts_ConcatDirGNN"]["all_seed_test_preds"], base_gnn
        ),
        "PhaseB_AblB_CriticPrefixed_ConcatDirGNN_vs_ExpA_Arm4_ConcatDirGNN": paired_bootstrap_multi_seed(
            y_test, by_name["PhaseB_AblB_Arm4CriticPrefixed_ConcatDirGNN"]["all_seed_test_preds"], base_gnn
        ),
        "PhaseB_AblC_CombinedCritic_ConcatDirGNN_vs_ExpA_Arm4_ConcatDirGNN": paired_bootstrap_multi_seed(
            y_test, by_name["PhaseB_AblC_CombinedCriticCountsAndPrefixed_ConcatDirGNN"]["all_seed_test_preds"], base_gnn
        ),
        "Exploratory_AllV12Evidence_ConcatDirGNN_vs_ExpA_Arm4_ConcatDirGNN": paired_bootstrap_multi_seed(
            y_test, by_name["Exploratory_AllV12Evidence_ConcatDirGNN"]["all_seed_test_preds"], base_gnn
        ),
        "Exploratory_AllV12Evidence_ConcatDirGNN_vs_ExpA_BaseTextLogReg": paired_bootstrap_multi_seed(
            y_test, by_name["Exploratory_AllV12Evidence_ConcatDirGNN"]["all_seed_test_preds"], base_txt
        ),
    }

    # Write detailed report RESULTS_SUMMARY_V1_2.md (zero em/en-dashes!)
    lines = [
        "# v1.2 Controlled Phase A (Method 1), Phase B (Critic Attribution), and Phase C Error Analysis Report",
        "",
        "- **Methodological Correction Applied:** Prior `audit_v1_2` (`train+val N=4,462`) was superseded for feature feasibility by strictly `train`-only (`N=3,674`) statistics in `TRAIN_ONLY_FEATURE_FEASIBILITY_V1_2.md`. All OOF text tuning ran strictly inside `train`, checkpoint/hyperparameter tuning strictly on `val` (`N=788`), and held-out `test` (`N=788`) evaluated identically across 5 seeds (`[42, 123, 456, 789, 101112]`).",
        "",
        "## 1. Phase A, Phase B, and Exploratory Test Results (`N = 788`, 5-Seed Means)",
        "",
        "| Model | Phase | Val Macro-F1 | Test Macro-F1 | Test R2-12 F1 | Test Acc | Test W-F1 | Test QWK | Test MAE | 3-Tier F1 / Acc |",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]
    for r in results:
        vm, tm = r["val_metrics"], r["test_metrics"]
        std_s = f" +/- {tm['macro_f1_std']:.4f}" if tm.get("macro_f1_std", 0.0) > 0 else ""
        lines.append(
            f"| `{r['name']}` | {r['phase']} | {vm['macro_f1']:.4f} | {tm['macro_f1']:.4f}{std_s} | {tm['r2_12_macro_f1']:.4f} | "
            f"{tm['accuracy']:.4f} | {tm['weighted_f1']:.4f} | {tm['qwk']:.4f} | {tm['mae']:.4f} | "
            f"{tm['tier3_macro_f1']:.4f} / {tm['tier3_acc']:.4f} |"
        )

    lines.extend([
        "",
        "## 2. Phase C Targeted Error Analysis (5-Seed Averages on `test N = 788`)",
        "",
        "| Model | R7 F1 (`n=27`) | R7->R9 Err (`mean /27`) | R3<->R4 Err | R4<->R5 Err | ZQ All (`63`) F1 / Acc | ZQ Conn (`25`) F1 / Acc | ZQ Iso (`38`) F1 / Acc |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ])
    for r in results:
        d = phase_c_diag[r["name"]]
        lines.append(
            f"| `{r['name']}` | {d['r7_f1_mean']:.4f} | {d['r7_to_r9_count_mean']:.1f} | {d['r3_r4_mutual_err_mean']:.1f} | "
            f"{d['r4_r5_mutual_err_mean']:.1f} | {d['zq_all_f1']:.4f} / {d['zq_all_acc']:.4f} | "
            f"{d['zq_conn_f1']:.4f} / {d['zq_conn_acc']:.4f} | {d['zq_iso_f1']:.4f} / {d['zq_iso_acc']:.4f} |"
        )

    lines.extend([
        "",
        "## 3. Five-Seed Paired Bootstrap Tests (`2,000` resamples on `test N = 788`)",
        "",
    ])
    for lbl, p in paired.items():
        lines.append(
            f"- **{lbl}:** delta Macro-F1 = `{p['delta_macro_f1']:+.4f}` (95% CI `[{p['ci95_f1'][0]:+.4f}, {p['ci95_f1'][1]:+.4f}]`, p=`{p['p_f1']:.4f}`), "
            f"delta Acc = `{p['delta_acc']:+.4f}` (p=`{p['p_acc']:.4f}`), delta QWK = `{p['delta_qwk']:+.4f}` (p=`{p['p_qwk']:.4f}`)"
        )

    (OUT_DIR / "RESULTS_SUMMARY_V1_2.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (OUT_DIR / "PHASE_C_ERROR_DIAGNOSTICS_V1_2.json").write_text(
        json.dumps({"paired_bootstrap": paired, "phase_c_diagnostics": phase_c_diag}, indent=2),
        encoding="utf-8",
    )

    exp_lines = [
        "# Experiment Record: v1.2 Controlled Phase A and Phase B Evidence Study",
        "",
        "- Experiment ID: `EXP-V1.2-CONTROLLED-EVIDENCE`",
        "- Date: `2026-11-18`",
        "- Safeguard record: Feature inspection re-run strictly on `train` (`N=3,674`) in `TRAIN_ONLY_FEATURE_FEASIBILITY_V1_2.md` prior to implementation; `v1.0`, `v1.1`, and `audit_v1_1` preserved unmodified.",
        "- Scope note: Graph architecture (`ConcatDirGNN` and `EarlyMLP`), 5-seed protocol, and narrator-disjoint splits held constant to isolate historical evidence effects cleanly.",
    ]
    (OUT_DIR / "EXPERIMENT_RECORD_V1_2.md").write_text("\n".join(exp_lines) + "\n", encoding="utf-8")

    out_files = [
        "EXPERIMENT_RECORD_V1_2.md",
        "RESULTS_SUMMARY_V1_2.md",
        "MODEL_COMPARISON_V1_2.csv",
        "PER_RANK_METRICS_V1_2.csv",
        "PHASE_C_ERROR_DIAGNOSTICS_V1_2.json",
    ]
    manifest = {
        "experiment_id": "EXP-V1.2-CONTROLLED-EVIDENCE",
        "verified_input_manifests": verified,
        "outputs": {name: {"sha256": sha256_file(OUT_DIR / name)} for name in out_files},
    }
    (OUT_DIR / "MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (OUT_DIR / "MANIFEST.sha256").write_text(
        "\n".join(f"{sha256_file(OUT_DIR / name)}  {name}" for name in out_files) + "\n",
        encoding="utf-8",
    )
    print("V1_2_CONTROLLED_EXPERIMENTS_COMPLETE", OUT_DIR, flush=True)


if __name__ == "__main__":
    main()
