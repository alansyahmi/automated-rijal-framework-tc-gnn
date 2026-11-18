"""v1.3 Diagnostic: Genre Mismatch, Feature Dilution, Evaluative Passage Filtering, and Hierarchical Fusion.

Tests the 4 hypotheses following v1.2 Phase A negative full-text result:
1. Vocabulary overlap between Arm 4 extracted critic quotes and Method 1 full bios (train-only).
2. Evaluative vocabulary & clause density across Arm 4 vs Method 1 overall and per book (train-only).
3. Source-specific lexical & JSD divergence across the 6 Method 1 books (train-only).
4. Length-controlled evaluative-passage ablation + hierarchical multi-stream fusion
   evaluated cleanly on the frozen N=5,250 cohort (5 seeds, val-only tuning, single test eval).
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
from scipy.spatial.distance import jensenshannon
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

csv.field_size_limit(10_000_000)

ROOT = Path(__file__).resolve().parents[1]
PIPELINE_DIR = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline"
V03_INPUT_DIR = PIPELINE_DIR / "task_b_historical_inputs_v0_3_2026-11-17"
V04_INPUT_DIR = PIPELINE_DIR / "task_b_historical_inputs_v0_4_2026-11-17"
V03_GRAPH_DIR = PIPELINE_DIR / "task_b_consolidated_graph_v0_3_2026-11-17"
V12_BIOS_DIR = PIPELINE_DIR / "task_b_method1_clean_bios_v1_2_2026-11-18"
OUT_DIR = ROOT / "results/v1_3_genre_dilution_diagnostic_2026-11-19"

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

# Classical Jarh wa Ta'dil evaluative vocabulary & verdict markers (domain-standard cues)
EVAL_CUES = (
    "ثقة", "ثبت", "حجة", "صدوق", "مأمون", "إمام", "حافظ", "صالح الحديث", "صالح",
    "لا بأس به", "ليس به بأس", "ما به بأس", "محله الصدق", "وسط", "حسن الحديث",
    "مستقيم الحديث", "لا أعلم به بأسا", "شيخ", "مقارب", "يقارب",
    "ضعيف", "متروك", "كذاب", "يضع", "وضاع", "دجال", "منكر", "مناكير",
    "ليس بشيء", "لا شيء", "ليس بالقوي", "لا يكتب حديثه", "واهي", "واه",
    "مجهول", "مستور", "لا يعرف", "لم يوثق", "فيه نظر", "سكتوا عنه",
    "يهم", "يخطئ", "أوهام", "غلط", "لين", "مضطرب", "مدلس", "يرسل", "اختلط",
    "متهم", "هالك", "ساقط", "ذاهب", "روى عنه جماعة", "لم يرو عنه غير",
    "مختلف فيه", "يروي الموضوعات", "يحدث بالبواطيل", "أفراد", "تفرد",
)

CRITIC_VERB_CUES = (
    "قال أبو حاتم", "سألت أبي", "سمعت أبي", "قال أبو زرعة",
    "قال يحيى", "قال ابن معين", "سألت يحيى", "قال أحمد", "قال البخاري",
    "قال النسائي", "قال أبو داود", "قال الترمذي", "قال الدارقطني",
    "قال ابن عدي", "قال الشيخ", "قال شعبة", "قال ابن المبارك", "قال الساجي",
    "قال العجلي", "قال يعقوب", "ذكره ابن حبان في الثقات", "وثقه", "ضعفه", "كذبه", "تركه",
)

PRAISE_CUES = ("ثقة", "ثبت", "حجة", "صدوق", "لا بأس به", "ليس به بأس", "مأمون", "إمام", "حافظ", "صالح الحديث")
CRIT_CUES = ("ضعيف", "متروك", "كذاب", "يضع", "وضاع", "منكر الحديث", "ليس بشيء", "لا يكتب حديثه", "واهي", "مجهول", "متهم")
MIXED_QUAL_CUES = ("يهم", "يخطئ", "له أوهام", "لين", "فيه نظر", "مختلف فيه", "مستور", "لا يعرف", "روى عنه جماعة", "لم يرو عنه غير")

TRANSMISSION_ROSTER_PREFIXES = (
    "روى عن", "يروي عن", "سمع من", "روى عنه", "يروي عنه",
)

AR_DIACRITICS_RE = re.compile(r"[\u064B-\u065F\u0670\u0640]")
TOKEN_RE = re.compile(r"[\u0621-\u064A]{2,}")


def normalize_arabic(text: str) -> str:
    text = AR_DIACRITICS_RE.sub("", text)
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    text = text.replace("ى", "ي")
    return re.sub(r"\s+", " ", text).strip()


def tokenize_ar(text: str) -> list[str]:
    return TOKEN_RE.findall(normalize_arabic(text))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_all_manifests() -> dict[str, dict[str, str]]:
    verified: dict[str, dict[str, str]] = {}
    for pkg_dir in [V03_INPUT_DIR, V04_INPUT_DIR, V03_GRAPH_DIR, V12_BIOS_DIR]:
        m = json.loads((pkg_dir / "MANIFEST.json").read_text(encoding="utf-8"))
        hashes: dict[str, str] = {}
        for rel, info in m.get("outputs", {}).items():
            fp = pkg_dir / rel
            actual = sha256_file(fp)
            expected = info["sha256"] if isinstance(info, dict) else info
            if actual != expected:
                raise AssertionError(f"Checksum mismatch for {fp}: {actual} != {expected}")
            hashes[rel] = actual
        verified[pkg_dir.name] = hashes
    return verified


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

    adj_t2s = sp.coo_matrix((dir_vals, (dir_rows, dir_cols)), shape=(len(rows), len(rows)), dtype=np.float32).tocsr()
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

    return rows, entry_ids, shamela_ids, y, splits, has_quote, cohort_deg, X_topo, row_norm(adj_t2s), row_norm(adj_s2t)


# Freeze normalized cue lists once for deterministic clause extraction
NORM_EVAL_CUES = tuple(normalize_arabic(c) for c in EVAL_CUES)
NORM_CRITIC_VERBS = tuple(normalize_arabic(c) for c in CRITIC_VERB_CUES)
NORM_ROSTER_PREFIXES = tuple(normalize_arabic(c) for c in TRANSMISSION_ROSTER_PREFIXES)


def is_evaluative_clause(clause_norm: str) -> bool:
    if not clause_norm or len(clause_norm) < 4:
        return False
    # Exclude pure long "روى عن / روى عنه" lists unless they contain an explicit evaluative cue/critic verdict!
    has_eval = any(c in clause_norm for c in NORM_EVAL_CUES) or any(cv in clause_norm for cv in NORM_CRITIC_VERBS)
    if not has_eval:
        return False
    if any(clause_norm.startswith(rp) for rp in NORM_ROSTER_PREFIXES) and len(clause_norm) > 220:
        # Very long teacher/student roster paragraph that happens to contain a word like "صالح" inside a person's name
        return any(cv in clause_norm for cv in NORM_CRITIC_VERBS) or any(
            strong in clause_norm for strong in ("ثقة", "صدوق", "ضعيف", "متروك", "كذاب", "مجهول", "مستور", "لا باس به", "ليس بالقوي")
        )
    return True


def extract_evaluative_clauses_from_bio(clean_bio_text: str) -> tuple[list[str], int, int]:
    """Deterministically segment clean biography into clauses and retain only evaluative ones."""
    norm_txt = normalize_arabic(clean_bio_text)
    raw_clauses = re.split(r"(?<=[.!؟])\s+|\s+-\s+|\n+", norm_txt)
    # Further split very long sentences on "، وقال" / "وقال" / "قال " / "روى عن" / "روى عنه" transitions
    sub_clauses = []
    for cl in raw_clauses:
        parts = re.split(r"(?=(?:روى عن|روى عنه|يروي عن|يروي عنه|سمع من|وقال|قال |سالت |سمعت |ذكره ))", cl)
        for pt in parts:
            s = pt.strip(" ،.")
            if s:
                sub_clauses.append(s)
    kept = [c for c in sub_clauses if is_evaluative_clause(c)]
    return kept, len(sub_clauses), len(kept)


def run_train_only_genre_dilution_analyses(
    train_eids: set[str],
    arm4_by_eid: dict[str, str],
    m1_rows_by_eid: dict[str, list[dict]],
):
    """Run Analyses 1, 2, and 3 STRICTLY on split == 'train' (N = 3,674)."""
    arm4_tf = Counter()
    m1_tf = Counter()
    m1_eval_tf = Counter()
    book_tf: defaultdict[str, Counter] = defaultdict(Counter)
    book_stats: defaultdict[str, dict] = defaultdict(lambda: {
        "train_bios": 0, "total_tokens": 0, "eval_tokens": 0, "total_clauses": 0, "eval_clauses": 0
    })

    arm4_doc_lens = []
    arm4_eval_tokens_tot = 0
    arm4_tot_tokens = 0
    arm4_tot_clauses = 0
    arm4_eval_clauses = 0

    for eid in train_eids:
        txt = arm4_by_eid.get(eid, "")
        toks = tokenize_ar(txt)
        arm4_doc_lens.append(len(toks))
        arm4_tot_tokens += len(toks)
        arm4_tf.update(toks)
        clauses = [c.strip() for c in re.split(r"[.!؟\n]+", normalize_arabic(txt)) if len(c.strip()) >= 3]
        arm4_tot_clauses += len(clauses)
        for cl in clauses:
            if is_evaluative_clause(cl):
                arm4_eval_clauses += 1
                arm4_eval_tokens_tot += len(tokenize_ar(cl))

    m1_doc_lens = []
    m1_eval_doc_lens = []
    m1_tot_clauses = 0
    m1_kept_clauses = 0

    for eid in train_eids:
        bios = m1_rows_by_eid.get(eid, [])
        joined_full = " ".join(b["clean_bio_text"] for b in bios)
        toks_full = tokenize_ar(joined_full)
        if toks_full:
            m1_doc_lens.append(len(toks_full))
        m1_tf.update(toks_full)

        joined_eval_parts = []
        for b in bios:
            sl = b["source_label"]
            btoks = tokenize_ar(b["clean_bio_text"])
            kept_cl, n_cl, n_k = extract_evaluative_clauses_from_bio(b["clean_bio_text"])
            kept_toks = tokenize_ar(" ".join(kept_cl))

            book_tf[sl].update(btoks)
            book_stats[sl]["train_bios"] += 1
            book_stats[sl]["total_tokens"] += len(btoks)
            book_stats[sl]["eval_tokens"] += len(kept_toks)
            book_stats[sl]["total_clauses"] += n_cl
            book_stats[sl]["eval_clauses"] += n_k

            m1_tot_clauses += n_cl
            m1_kept_clauses += n_k
            m1_eval_tf.update(kept_toks)
            joined_eval_parts.extend(kept_cl)

        etoks = tokenize_ar(" ".join(joined_eval_parts))
        if etoks:
            m1_eval_doc_lens.append(len(etoks))

    # Analysis 1: Vocabulary overlap (all tokens and df-like freq>=3 tokens)
    v_arm4 = {w for w, c in arm4_tf.items() if c >= 3}
    v_m1 = {w for w, c in m1_tf.items() if c >= 3}
    v_m1_eval = {w for w, c in m1_eval_tf.items() if c >= 3}
    shared_14 = v_arm4 & v_m1
    union_14 = v_arm4 | v_m1
    m1_new_tokens_occ = sum(c for w, c in m1_tf.items() if w not in arm4_tf)
    m1_tot_occ = max(sum(m1_tf.values()), 1)

    # Disproportionately enriched tokens in M1 vs Arm 4 (Laplace smoothed log-odds ratio)
    tot_a4 = sum(arm4_tf.values()) + len(union_14)
    tot_m1 = sum(m1_tf.values()) + len(union_14)
    enriched_m1 = []
    enriched_a4 = []
    for w in union_14:
        p_m1 = (m1_tf[w] + 1.0) / tot_m1
        p_a4 = (arm4_tf[w] + 1.0) / tot_a4
        lr = math.log(p_m1 / p_a4)
        if m1_tf[w] >= 100 and lr > 0:
            enriched_m1.append((round(lr, 3), w, m1_tf[w], arm4_tf[w]))
        if arm4_tf[w] >= 80 and lr < 0:
            enriched_a4.append((round(-lr, 3), w, arm4_tf[w], m1_tf[w]))
    enriched_m1.sort(reverse=True)
    enriched_a4.sort(reverse=True)

    # Analysis 3: Pairwise Jensen-Shannon Divergence across Arm 4 and the 6 Method 1 books
    dist_vocab = sorted({w for w, c in (arm4_tf + m1_tf).items() if c >= 10})
    w_idx = {w: i for i, w in enumerate(dist_vocab)}

    def to_prob_vec(cnt: Counter) -> np.ndarray:
        vec = np.ones(len(dist_vocab), dtype=np.float64) * 1e-6
        for w, c in cnt.items():
            if w in w_idx:
                vec[w_idx[w]] += c
        return vec / vec.sum()

    prob_dists = {"arm4": to_prob_vec(arm4_tf), "m1_eval_filtered": to_prob_vec(m1_eval_tf)}
    for sl in BOOK_LABELS:
        prob_dists[sl] = to_prob_vec(book_tf[sl])

    jsd_vs_arm4 = {
        name: round(float(jensenshannon(prob_dists["arm4"], vec) ** 2), 4)
        for name, vec in prob_dists.items()
        if name != "arm4"
    }

    per_book_summary = {}
    for sl in BOOK_LABELS:
        bs = book_stats[sl]
        top_words = [w for w, _c in book_tf[sl].most_common(12)]
        per_book_summary[sl] = {
            "train_bios": bs["train_bios"],
            "mean_tokens_per_bio": round(bs["total_tokens"] / max(bs["train_bios"], 1), 1),
            "eval_token_density_pct": round(100.0 * bs["eval_tokens"] / max(bs["total_tokens"], 1), 1),
            "eval_clause_share_pct": round(100.0 * bs["eval_clauses"] / max(bs["total_clauses"], 1), 1),
            "jsd_vs_arm4": jsd_vs_arm4[sl],
            "top_tokens": top_words,
        }

    return {
        "analysis1_vocab_overlap_freq_ge3": {
            "arm4_vocab_size": len(v_arm4),
            "m1_full_vocab_size": len(v_m1),
            "m1_eval_filtered_vocab_size": len(v_m1_eval),
            "shared_arm4_m1_vocab": len(shared_14),
            "jaccard_arm4_m1": round(len(shared_14) / max(len(union_14), 1), 4),
            "jaccard_arm4_m1_eval": round(len(v_arm4 & v_m1_eval) / max(len(v_arm4 | v_m1_eval), 1), 4),
            "m1_unseen_in_arm4_vocab_pct": round(100.0 * len(v_m1 - v_arm4) / max(len(v_m1), 1), 1),
            "m1_unseen_in_arm4_token_occ_pct": round(100.0 * m1_new_tokens_occ / m1_tot_occ, 1),
            "top15_enriched_in_m1_vs_arm4": enriched_m1[:15],
            "top15_enriched_in_arm4_vs_m1": enriched_a4[:15],
        },
        "analysis2_evaluative_density": {
            "arm4_mean_tokens": round(float(np.mean(arm4_doc_lens)), 1),
            "arm4_median_tokens": float(np.median(arm4_doc_lens)),
            "arm4_eval_token_density_pct": round(100.0 * arm4_eval_tokens_tot / max(arm4_tot_tokens, 1), 1),
            "arm4_eval_clause_share_pct": round(100.0 * arm4_eval_clauses / max(arm4_tot_clauses, 1), 1),
            "m1_full_mean_tokens": round(float(np.mean(m1_doc_lens)), 1),
            "m1_full_median_tokens": float(np.median(m1_doc_lens)),
            "m1_full_eval_token_density_pct": round(100.0 * sum(m1_eval_tf.values()) / m1_tot_occ, 1),
            "m1_full_eval_clause_share_pct": round(100.0 * m1_kept_clauses / max(m1_tot_clauses, 1), 1),
            "m1_filtered_eval_mean_tokens": round(float(np.mean(m1_eval_doc_lens)), 1),
            "m1_filtered_eval_median_tokens": float(np.median(m1_eval_doc_lens)),
        },
        "analysis3_source_specific_distributions": {
            "jsd_vs_arm4": jsd_vs_arm4,
            "per_book": per_book_summary,
        },
    }


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
        f"[done] {name} | val_f1={agg_val['macro_f1']:.4f} | test_f1={agg_test['macro_f1']:.4f} +/- {agg_test['macro_f1_std']:.4f} | acc={agg_test['accuracy']:.4f} | qwk={agg_test['qwk']:.4f}",
        flush=True,
    )
    return {
        "name": name,
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

    verified = verify_all_manifests()
    rows, entry_ids, shamela_ids, y, splits, has_quote, cohort_deg, X_topo_raw, adj_t2s, adj_s2t = (
        load_cohort_and_graph()
    )
    adj_t2s, adj_s2t = adj_t2s.to(device), adj_s2t.to(device)
    eid_set = set(entry_ids)
    train_eids = {r["entry_id"] for r in rows if r["split"] == "train"}

    # Load Arm 4 plain passages & critic counts
    v03_p: defaultdict[str, list[str]] = defaultdict(list)
    fwaed_p: defaultdict[str, list[str]] = defaultdict(list)
    abl_p: defaultdict[str, list[str]] = defaultdict(list)

    critics_all: defaultdict[str, set[str]] = defaultdict(set)
    critics_praise: defaultdict[str, set[str]] = defaultdict(set)
    critics_crit: defaultdict[str, set[str]] = defaultdict(set)
    critics_mixed: defaultdict[str, set[str]] = defaultdict(set)
    sources_all: defaultdict[str, set[str]] = defaultdict(set)
    has_ambig_critic: defaultdict[str, int] = defaultdict(int)

    def rec_critic(eid: str, critic: str, src_work: str, txt_norm: str):
        c = normalize_arabic(critic).strip()
        if not c:
            tag = "CRITIC_UNATTRIBUTED"
        elif len(c) > 40 or "،" in c or "غيره" in c:
            tag = "CRITIC_AMBIG"
        else:
            tag = c
        if tag in {"CRITIC_UNATTRIBUTED", "CRITIC_AMBIG"}:
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

    with (V03_INPUT_DIR / "TASK_B_ELIGIBLE_HISTORICAL_PASSAGES_V0_3.csv").open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            eid = r["entry_id"]
            if eid in eid_set:
                tx = normalize_arabic(r["quotation_text_exact"])
                if tx:
                    v03_p[eid].append(tx)
                    rec_critic(eid, r.get("historical_attribution_critic", ""), r.get("source_work_normalised", ""), tx)

    with (V04_INPUT_DIR / "TASK_B_FWAED_PASSAGES_V0_4.csv").open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            eid = r["entry_id"]
            if eid in eid_set:
                tx = normalize_arabic(r["fwaed_text_exact"])
                if tx:
                    fwaed_p[eid].append(tx)

    with (V04_INPUT_DIR / "TASK_B_EARLY_SPEAKER_ABLATION_PASSAGES_V0_4.csv").open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            eid = r["entry_id"]
            if eid in eid_set:
                tx = normalize_arabic(r["quotation_text_exact"])
                if tx:
                    abl_p[eid].append(tx)
                    rec_critic(eid, r.get("historical_attribution_critic", ""), "تهذيب التهذيب", tx)

    arm4_by_eid = {e: " \n ".join(v03_p[e] + fwaed_p[e] + abl_p[e]) for e in entry_ids}

    # Load v1.2 clean Method 1 bios
    m1_rows_by_eid: defaultdict[str, list[dict]] = defaultdict(list)
    with (V12_BIOS_DIR / "TASK_B_METHOD1_CLEAN_BIOS_V1_2.csv").open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            if r["entry_id"] in eid_set:
                m1_rows_by_eid[r["entry_id"]].append(r)

    # Run Analyses 1, 2, 3 STRICTLY on split == 'train'
    print("[stage] Running train-only Analyses 1, 2, 3...", flush=True)
    diag_123 = run_train_only_genre_dilution_analyses(train_eids, arm4_by_eid, m1_rows_by_eid)

    # Apply deterministic Method 1 Evaluative Passage filter to all 5,250 cohort entries
    m1_eval_rows = []
    m1_eval_by_eid: defaultdict[str, list[str]] = defaultdict(list)
    m1_full_by_eid: defaultdict[str, list[str]] = defaultdict(list)
    m1_eval_stats_by_eid: defaultdict[str, list[int]] = defaultdict(lambda: [0, 0])  # [raw_len, eval_len]
    train_eval_samples: list[dict[str, str]] = []

    for eid in entry_ids:
        for r in m1_rows_by_eid[eid]:
            m1_full_by_eid[eid].append(f"SOURCE_{r['source_label']} : {normalize_arabic(r['clean_bio_text'])}")
            kept_cl, n_cl, n_k = extract_evaluative_clauses_from_bio(r["clean_bio_text"])
            m1_eval_stats_by_eid[eid][0] += len(r["clean_bio_text"])
            if kept_cl:
                joined_k = " . ".join(kept_cl)
                m1_eval_by_eid[eid].append(f"SOURCE_{r['source_label']} : {joined_k}")
                m1_eval_stats_by_eid[eid][1] += len(joined_k)
                m1_eval_rows.append({
                    "bio_id": r["bio_id"],
                    "entry_id": eid,
                    "source_label": r["source_label"],
                    "page_id_start": r["page_id_start"],
                    "total_clauses": n_cl,
                    "kept_evaluative_clauses": n_k,
                    "clean_char_len": len(r["clean_bio_text"]),
                    "eval_char_len": len(joined_k),
                    "eval_passages_text": joined_k,
                })
                if eid in train_eids and len(train_eval_samples) < 8 and n_k >= 2:
                    train_eval_samples.append({
                        "bio_id": r["bio_id"],
                        "train_entry_id": eid,
                        "source_label": r["source_label"],
                        "kept_clauses": f"{n_k}/{n_cl}",
                        "chars": f"{len(joined_k)}/{len(r['clean_bio_text'])}",
                        "preview": joined_k[:260],
                    })

    # Save filtered Method 1 evaluative passages CSV
    eval_fp = OUT_DIR / "TASK_B_METHOD1_EVALUATIVE_PASSAGES_V1_3.csv"
    with eval_fp.open("w", encoding="utf-8-sig", newline="") as f:
        fields = [
            "bio_id", "entry_id", "source_label", "page_id_start", "total_clauses",
            "kept_evaluative_clauses", "clean_char_len", "eval_char_len", "eval_passages_text",
        ]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(m1_eval_rows)

    # 3-state book indicators + M1 eval lengths
    ind_by_eid = {}
    with (V12_BIOS_DIR / "TASK_B_METHOD1_BOOK_INDICATORS_V1_2.csv").open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            ind_by_eid[r["entry_id"]] = r

    book_ind_cols = []
    for bl in BOOK_LABELS:
        book_ind_cols.extend([f"is_linked_{bl}", f"is_ambig_{bl}", f"log1p_chars_{bl}"])
    X_meta = np.zeros((len(entry_ids), len(book_ind_cols) + 2 + 9), dtype=np.float32)
    for i, eid in enumerate(entry_ids):
        ir = ind_by_eid[eid]
        vals = [float(ir[col]) for col in book_ind_cols]
        raw_l, eval_l = m1_eval_stats_by_eid[eid]
        vals.extend([math.log1p(eval_l), 1.0 if eval_l > 0 else 0.0])

        nc, np_c, nc_c, nm_c, ns = (
            len(critics_all[eid]),
            len(critics_praise[eid]),
            len(critics_crit[eid]),
            len(critics_mixed[eid]),
            len(sources_all[eid]),
        )
        denom = max(nc, 1)
        vals.extend([
            math.log1p(nc),
            math.log1p(np_c),
            math.log1p(nc_c),
            math.log1p(nm_c),
            1.0 if (np_c > 0 and nc_c > 0) else 0.0,
            np_c / denom,
            nc_c / denom,
            math.log1p(ns),
            float(has_ambig_critic[eid]),
        ])
        X_meta[i] = vals

    tr_mask, va_mask, te_mask = splits == "train", splits == "val", splits == "test"
    y_test = y[te_mask]

    X_topo = StandardScaler().fit(X_topo_raw[tr_mask]).transform(X_topo_raw).astype(np.float32)
    X_meta_std = StandardScaler().fit(X_meta[tr_mask]).transform(X_meta).astype(np.float32)

    # 4 text corpora for Analysis 4 & Hierarchical Stream 2
    corpora = {
        "arm4_plain": [arm4_by_eid[e] for e in entry_ids],
        "arm4_plus_m1_full": [
            " \n ".join(([arm4_by_eid[e]] if arm4_by_eid[e] else []) + m1_full_by_eid[e]) for e in entry_ids
        ],
        "arm4_plus_m1_eval_filtered": [
            " \n ".join(([arm4_by_eid[e]] if arm4_by_eid[e] else []) + m1_eval_by_eid[e]) for e in entry_ids
        ],
        "m1_eval_only_stream": [" \n ".join(m1_eval_by_eid[e]) for e in entry_ids],
    }

    oof_raw, oof_scaled, oof_cfgs = {}, {}, {}
    for ckey, texts in corpora.items():
        cfg, logp = generate_oof_text_features(
            ckey, texts, entry_ids, shamela_ids, y, tr_mask, va_mask, te_mask
        )
        oof_cfgs[ckey] = cfg
        oof_raw[ckey] = logp
        oof_scaled[ckey] = StandardScaler().fit(logp[tr_mask]).transform(logp).astype(np.float32)

    results = []

    def add_logreg(name: str, ckey: str):
        vp = oof_raw[ckey][va_mask].argmax(1)
        tp = oof_raw[ckey][te_mask].argmax(1)
        results.append({
            "name": name,
            "cfg": oof_cfgs[ckey],
            "val_metrics": compute_metrics(y[va_mask], vp),
            "test_metrics": compute_metrics(y_test, tp),
            "all_seed_test_preds": [tp] * 5,
        })

    # Abl1: Original Arm 4
    add_logreg("Abl1_Arm4_BaseText_LogReg", "arm4_plain")
    results.append(run_neural_experiment(
        "Abl1_Arm4_EarlyMLP", "mlp",
        np.hstack([oof_scaled["arm4_plain"], X_topo]), y, tr_mask, va_mask, te_mask, adj_t2s, adj_s2t, device
    ))
    results.append(run_neural_experiment(
        "Abl1_Arm4_ConcatDirGNN", "dir_concat_gnn",
        np.hstack([oof_scaled["arm4_plain"], X_topo]), y, tr_mask, va_mask, te_mask, adj_t2s, adj_s2t, device
    ))

    # Abl2: Arm 4 + Full Method 1 Bio Text
    add_logreg("Abl2_Arm4PlusM1Full_BaseText_LogReg", "arm4_plus_m1_full")
    results.append(run_neural_experiment(
        "Abl2_Arm4PlusM1Full_EarlyMLP", "mlp",
        np.hstack([oof_scaled["arm4_plus_m1_full"], X_topo]), y, tr_mask, va_mask, te_mask, adj_t2s, adj_s2t, device
    ))
    results.append(run_neural_experiment(
        "Abl2_Arm4PlusM1Full_ConcatDirGNN", "dir_concat_gnn",
        np.hstack([oof_scaled["arm4_plus_m1_full"], X_topo]), y, tr_mask, va_mask, te_mask, adj_t2s, adj_s2t, device
    ))

    # Abl3: Arm 4 + Evaluative Method 1 Bio Passages ONLY
    add_logreg("Abl3_Arm4PlusM1EvalPassages_BaseText_LogReg", "arm4_plus_m1_eval_filtered")
    results.append(run_neural_experiment(
        "Abl3_Arm4PlusM1EvalPassages_EarlyMLP", "mlp",
        np.hstack([oof_scaled["arm4_plus_m1_eval_filtered"], X_topo]), y, tr_mask, va_mask, te_mask, adj_t2s, adj_s2t, device
    ))
    results.append(run_neural_experiment(
        "Abl3_Arm4PlusM1EvalPassages_ConcatDirGNN", "dir_concat_gnn",
        np.hstack([oof_scaled["arm4_plus_m1_eval_filtered"], X_topo]), y, tr_mask, va_mask, te_mask, adj_t2s, adj_s2t, device
    ))

    # Abl4: Arm 4 + Biography Metadata & Structured Features (BookInd + Critic Counts)
    results.append(run_neural_experiment(
        "Abl4_Arm4PlusMetaAndStruct_EarlyMLP", "mlp",
        np.hstack([oof_scaled["arm4_plain"], X_topo, X_meta_std]), y, tr_mask, va_mask, te_mask, adj_t2s, adj_s2t, device
    ))
    results.append(run_neural_experiment(
        "Abl4_Arm4PlusMetaAndStruct_ConcatDirGNN", "dir_concat_gnn",
        np.hstack([oof_scaled["arm4_plain"], X_topo, X_meta_std]), y, tr_mask, va_mask, te_mask, adj_t2s, adj_s2t, device
    ))

    # Abl5: Hierarchical Multi-Stream Representation ([Arm4 OOF || M1-Eval OOF || Meta+Critic+Topo])
    X_hier_no_meta = np.hstack([oof_scaled["arm4_plain"], oof_scaled["m1_eval_only_stream"], X_topo])
    X_hier_full = np.hstack([oof_scaled["arm4_plain"], oof_scaled["m1_eval_only_stream"], X_topo, X_meta_std])
    results.append(run_neural_experiment(
        "Abl5_HierStreams_TextOnlyPlusTopo_ConcatDirGNN", "dir_concat_gnn",
        X_hier_no_meta, y, tr_mask, va_mask, te_mask, adj_t2s, adj_s2t, device
    ))
    results.append(run_neural_experiment(
        "Abl5_HierStreams_FullWithMeta_EarlyMLP", "mlp",
        X_hier_full, y, tr_mask, va_mask, te_mask, adj_t2s, adj_s2t, device
    ))
    results.append(run_neural_experiment(
        "Abl5_HierStreams_FullWithMeta_ConcatDirGNN", "dir_concat_gnn",
        X_hier_full, y, tr_mask, va_mask, te_mask, adj_t2s, adj_s2t, device
    ))

    # Subgroup & R7 diagnostics
    q_te = has_quote[te_mask]
    deg_te = cohort_deg[te_mask]
    zq_all = q_te == 0
    zq_conn = (q_te == 0) & (deg_te > 0)
    zq_iso = (q_te == 0) & (deg_te == 0)

    diag_map = {}
    for r in results:
        r7s, r7_9s, zq_f1s, czq_f1s, czq_accs, izq_f1s = [], [], [], [], [], []
        for p in r["all_seed_test_preds"]:
            cm = confusion_matrix(y_test, p, labels=list(range(12)))
            _, _, f1a, _ = precision_recall_fscore_support(y_test, p, labels=list(range(12)), zero_division=0)
            r7s.append(float(f1a[6]))
            r7_9s.append(int(cm[6, 8]))
            zq_f1s.append(float(f1_score(y_test[zq_all], p[zq_all], labels=list(range(12)), average="macro", zero_division=0)))
            czq_f1s.append(float(f1_score(y_test[zq_conn], p[zq_conn], labels=list(range(12)), average="macro", zero_division=0)))
            czq_accs.append(float(accuracy_score(y_test[zq_conn], p[zq_conn])))
            izq_f1s.append(float(f1_score(y_test[zq_iso], p[zq_iso], labels=list(range(12)), average="macro", zero_division=0)))
        diag_map[r["name"]] = {
            "r7_f1": float(np.mean(r7s)),
            "r7_to_r9": float(np.mean(r7_9s)),
            "zq_all_f1": float(np.mean(zq_f1s)),
            "zq_conn_f1": float(np.mean(czq_f1s)),
            "zq_conn_acc": float(np.mean(czq_accs)),
            "zq_iso_f1": float(np.mean(izq_f1s)),
        }

    by_name = {r["name"]: r for r in results}
    paired = {
        "Abl3_M1EvalPassages_ConcatDirGNN_vs_Abl2_M1Full_ConcatDirGNN": paired_bootstrap_multi_seed(
            y_test, by_name["Abl3_Arm4PlusM1EvalPassages_ConcatDirGNN"]["all_seed_test_preds"], by_name["Abl2_Arm4PlusM1Full_ConcatDirGNN"]["all_seed_test_preds"]
        ),
        "Abl3_M1EvalPassages_LogReg_vs_Abl2_M1Full_LogReg": paired_bootstrap_multi_seed(
            y_test, by_name["Abl3_Arm4PlusM1EvalPassages_BaseText_LogReg"]["all_seed_test_preds"], by_name["Abl2_Arm4PlusM1Full_BaseText_LogReg"]["all_seed_test_preds"]
        ),
        "Abl3_M1EvalPassages_ConcatDirGNN_vs_Abl1_Arm4_ConcatDirGNN": paired_bootstrap_multi_seed(
            y_test, by_name["Abl3_Arm4PlusM1EvalPassages_ConcatDirGNN"]["all_seed_test_preds"], by_name["Abl1_Arm4_ConcatDirGNN"]["all_seed_test_preds"]
        ),
        "Abl5_HierTextStream_ConcatDirGNN_vs_Abl2_M1Full_ConcatDirGNN": paired_bootstrap_multi_seed(
            y_test, by_name["Abl5_HierStreams_TextOnlyPlusTopo_ConcatDirGNN"]["all_seed_test_preds"], by_name["Abl2_Arm4PlusM1Full_ConcatDirGNN"]["all_seed_test_preds"]
        ),
        "Abl5_HierFullWithMeta_ConcatDirGNN_vs_Abl1_Arm4_ConcatDirGNN": paired_bootstrap_multi_seed(
            y_test, by_name["Abl5_HierStreams_FullWithMeta_ConcatDirGNN"]["all_seed_test_preds"], by_name["Abl1_Arm4_ConcatDirGNN"]["all_seed_test_preds"]
        ),
        "Abl4_Arm4PlusMetaAndStruct_ConcatDirGNN_vs_Abl1_Arm4_ConcatDirGNN": paired_bootstrap_multi_seed(
            y_test, by_name["Abl4_Arm4PlusMetaAndStruct_ConcatDirGNN"]["all_seed_test_preds"], by_name["Abl1_Arm4_ConcatDirGNN"]["all_seed_test_preds"]
        ),
    }

    # Save MODEL_COMPARISON_V1_3.csv
    with (OUT_DIR / "MODEL_COMPARISON_V1_3.csv").open("w", encoding="utf-8-sig", newline="") as f:
        fields = [
            "model_name", "val_macro_f1", "test_macro_f1", "test_macro_f1_std",
            "test_r2_12_macro_f1", "test_accuracy", "test_qwk", "test_mae",
            "test_tier3_macro_f1", "test_tier3_acc", "r7_f1", "r7_to_r9",
            "zq_conn_f1", "zq_conn_acc", "zq_iso_f1",
        ]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in results:
            vm, tm, dm = r["val_metrics"], r["test_metrics"], diag_map[r["name"]]
            w.writerow({
                "model_name": r["name"],
                "val_macro_f1": f"{vm['macro_f1']:.4f}",
                "test_macro_f1": f"{tm['macro_f1']:.4f}",
                "test_macro_f1_std": f"{tm.get('macro_f1_std', 0.0):.4f}",
                "test_r2_12_macro_f1": f"{tm['r2_12_macro_f1']:.4f}",
                "test_accuracy": f"{tm['accuracy']:.4f}",
                "test_qwk": f"{tm['qwk']:.4f}",
                "test_mae": f"{tm['mae']:.4f}",
                "test_tier3_macro_f1": f"{tm['tier3_macro_f1']:.4f}",
                "test_tier3_acc": f"{tm['tier3_acc']:.4f}",
                "r7_f1": f"{dm['r7_f1']:.4f}",
                "r7_to_r9": f"{dm['r7_to_r9']:.1f}",
                "zq_conn_f1": f"{dm['zq_conn_f1']:.4f}",
                "zq_conn_acc": f"{dm['zq_conn_acc']:.4f}",
                "zq_iso_f1": f"{dm['zq_iso_f1']:.4f}",
            })

    # Write comprehensive diagnostic report (zero em/en-dashes!)
    a1 = diag_123["analysis1_vocab_overlap_freq_ge3"]
    a2 = diag_123["analysis2_evaluative_density"]
    a3 = diag_123["analysis3_source_specific_distributions"]

    lines = [
        "# v1.3 Diagnostic Report: Genre Mismatch, Feature Dilution, Evaluative Passage Filtering, and Hierarchical Fusion",
        "",
        "Analyses 1, 2, and 3 plus the evaluative clause extraction rules were developed strictly on `split == 'train'` (`N = 3,674`).",
        "",
        "## 1. Analysis 1: Vocabulary Overlap (`train`, tokens with corpus freq >= 3)",
        "",
        f"- **`Arm 4` vocab size:** `{a1['arm4_vocab_size']}` | **Method 1 Full Bio vocab size:** `{a1['m1_full_vocab_size']}` | **Shared:** `{a1['shared_arm4_m1_vocab']}` (Jaccard = `{a1['jaccard_arm4_m1']}`)",
        f"- **Method 1 Filtered Evaluative vocab size:** `{a1['m1_eval_filtered_vocab_size']}` (Jaccard vs `Arm 4` = `{a1['jaccard_arm4_m1_eval']}`)",
        f"- **Fraction of Method 1 vocabulary NOT in `Arm 4`:** `{a1['m1_unseen_in_arm4_vocab_pct']}%` of unique types (`{a1['m1_unseen_in_arm4_token_occ_pct']}%` of total Method 1 token occurrences).",
        f"- **Top tokens enriched in Method 1 vs `Arm 4` (log-odds, word, M1 count, Arm 4 count):** `{a1['top15_enriched_in_m1_vs_arm4'][:10]}`",
        f"- **Top tokens enriched in `Arm 4` vs Method 1:** `{a1['top15_enriched_in_arm4_vs_m1'][:10]}`",
        "",
        "## 2. Analysis 2: Evaluative Vocabulary and Clause Density (`train`)",
        "",
        "| Evidence Corpus (`train`) | Mean Tokens/Doc | Median Tokens/Doc | Evaluative Token Density % | Evaluative Clause Share % |",
        "| :--- | :---: | :---: | :---: | :---: |",
        f"| `Arm 4` (extracted critic quotes) | {a2['arm4_mean_tokens']} | {a2['arm4_median_tokens']} | **{a2['arm4_eval_token_density_pct']}%** | **{a2['arm4_eval_clause_share_pct']}%** |",
        f"| Method 1 Full Biographies | {a2['m1_full_mean_tokens']} | {a2['m1_full_median_tokens']} | {a2['m1_full_eval_token_density_pct']}% | {a2['m1_full_eval_clause_share_pct']}% |",
        f"| Method 1 Filtered Evaluative Passages | {a2['m1_filtered_eval_mean_tokens']} | {a2['m1_filtered_eval_median_tokens']} | (filtered stream) | 100% retained |",
        "",
        "## 3. Analysis 3: Source-Specific Distribution Across the 6 Classical Books (`train`)",
        "",
        f"- **Jensen-Shannon Divergence vs `Arm 4` (`m1_eval_filtered` vs `Arm 4` = `{a3['jsd_vs_arm4']['m1_eval_filtered']}`)**",
        "",
        "| Book (`train`) | Bios | Mean Tokens/Bio | Eval Token Density % | Eval Clause Share % | JSD vs `Arm 4` |",
        "| :--- | :---: | :---: | :---: | :---: | :---: |",
    ]
    for sl in BOOK_LABELS:
        bs = a3["per_book"][sl]
        lines.append(
            f"| `{sl}` | {bs['train_bios']} | {bs['mean_tokens_per_bio']} | {bs['eval_token_density_pct']}% | {bs['eval_clause_share_pct']}% | {bs['jsd_vs_arm4']} |"
        )

    lines.extend([
        "",
        "## 4. Analysis 4: Length-Controlled Evaluative Passage Ablation and Hierarchical Fusion (`test N = 788`, 5-Seed Means)",
        "",
        "| Model | Val F1 | Test Macro-F1 | Test R2-12 F1 | Test Acc | Test QWK | 3-Tier F1 | R7 F1 / R7->R9 | ZQ Conn F1 / Acc |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ])
    for r in results:
        vm, tm, dm = r["val_metrics"], r["test_metrics"], diag_map[r["name"]]
        std_s = f" +/- {tm['macro_f1_std']:.4f}" if tm.get("macro_f1_std", 0.0) > 0 else ""
        lines.append(
            f"| `{r['name']}` | {vm['macro_f1']:.4f} | {tm['macro_f1']:.4f}{std_s} | {tm['r2_12_macro_f1']:.4f} | "
            f"{tm['accuracy']:.4f} | {tm['qwk']:.4f} | {tm['tier3_macro_f1']:.4f} | "
            f"{dm['r7_f1']:.4f} / {dm['r7_to_r9']:.1f} | {dm['zq_conn_f1']:.4f} / {dm['zq_conn_acc']:.4f} |"
        )

    lines.extend(["", "## 5. Five-Seed Paired Bootstrap Comparisons (`2,000` resamples on `test N = 788`)", ""])
    for lbl, p in paired.items():
        lines.append(
            f"- **{lbl}:** delta Macro-F1 = `{p['delta_macro_f1']:+.4f}` (95% CI `[{p['ci95_f1'][0]:+.4f}, {p['ci95_f1'][1]:+.4f}]`, p=`{p['p_f1']:.4f}`), "
            f"delta Acc = `{p['delta_acc']:+.4f}` (p=`{p['p_acc']:.4f}`), delta QWK = `{p['delta_qwk']:+.4f}` (p=`{p['p_qwk']:.4f}`)"
        )

    lines.extend(["", "## 6. Sample Train-Only Filtered Method 1 Evaluative Passages", ""])
    for s in train_eval_samples:
        lines.append(f"- `{s['bio_id']}` (`{s['train_entry_id']}`, `{s['source_label']}`, clauses=`{s['kept_clauses']}`, chars=`{s['chars']}`): `{s['preview']}`")

    (OUT_DIR / "DIAGNOSTIC_REPORT_V1_3.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (OUT_DIR / "DIAGNOSTIC_METRICS_V1_3.json").write_text(
        json.dumps({"analyses_123": diag_123, "paired_bootstrap": paired, "subgroups": diag_map}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    out_files = [
        "DIAGNOSTIC_REPORT_V1_3.md",
        "DIAGNOSTIC_METRICS_V1_3.json",
        "MODEL_COMPARISON_V1_3.csv",
        "TASK_B_METHOD1_EVALUATIVE_PASSAGES_V1_3.csv",
    ]
    manifest = {
        "experiment_id": "V1.3-GENRE-DILUTION-AND-HIERARCHICAL-DIAGNOSTIC",
        "verified_input_manifests": verified,
        "outputs": {name: {"sha256": sha256_file(OUT_DIR / name)} for name in out_files},
    }
    (OUT_DIR / "MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (OUT_DIR / "MANIFEST.sha256").write_text(
        "\n".join(f"{sha256_file(OUT_DIR / name)}  {name}" for name in out_files) + "\n",
        encoding="utf-8",
    )
    print("V1_3_GENRE_DILUTION_COMPLETE", OUT_DIR, flush=True)


if __name__ == "__main__":
    main()
