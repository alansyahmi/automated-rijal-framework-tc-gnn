#!/usr/bin/env python3
"""Stage 2: Evaluative Stance Analysis (ESA) Benchmarks (taqrib-oriented v2; v3-aligned naming).

Evaluates strictly on Ibn Hajar's Taqrib al-Tahdhib (3076) text + structured metadata
(ZERO graph columns, ZERO Tahrir text/verdict leakage) for Dual-Target prediction:
  - Target A (Tahrir Ordinal): Tahrir Bilgin-grounded 1-12 rank (score_E2 target)
  - Target B (3-Class Shift): upgraded / unchanged / downgraded vs Baseline B (score_B)

Aligned with:
  - Wahba et al. (2026): Weighted Precision/Recall/F1, Accuracy (12-class + Binary Ta'dil/Jarh)
  - Alturayeif et al. (2024, StanceEval): Macro-F1 & Active Macro-F1 across 3 shift classes
  - Bilgin (2026): 12-rank ordinal scale & Rank 6 Maqbul subgroup resolution

Exports 5-fold zero-leakage OOF ESA features across all 8,827 rows for Stage 3 TC-GNN (Text-Classification-informed GNN).
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import random
import re
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
from scipy.stats import spearmanr
from sklearn.decomposition import PCA, TruncatedSVD
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor, RandomForestClassifier, RandomForestRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score,
    cohen_kappa_score,
    f1_score,
    mean_absolute_error,
    precision_recall_fscore_support,
    root_mean_squared_error,
)
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import FeatureUnion
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModel, AutoModelForSequenceClassification, AutoTokenizer


os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline"
MASTER_NODES = PIPELINE / "taqrib_v2_master_dataset_2026-11-20/TAQRIB_V2_MASTER_NODES_8827.csv"
TASK_A_V14 = PIPELINE / "task_a_deterministic_targets_v1_4_2026-11-19/TASK_A_DETERMINISTIC_TARGETS_8827_V1_4.csv"
OUT_DIR = ROOT / "results/stage2_semantic_benchmarks_v2_2026-11-20"

SEED = 42
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

ARABERT_ID = "aubmindlab/bert-base-arabertv02"
CAMEL_ID = "CAMeL-Lab/bert-base-arabic-camelbert-msa-sentiment"


def set_seed(seed: int = SEED) -> None:
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


def normalize_text(s: str) -> str:
    s = LEAD_NUM_RE.sub("", s.strip())
    s = DIACRITICS_RE.sub("", s)
    return WHITESPACE_RE.sub(" ", s).strip()


def build_name_stripped_text(row: dict[str, str], target_span: str) -> str:
    full = normalize_text(row["taqrib_text_verbatim"])
    span_norm = DIACRITICS_RE.sub("", target_span).strip()
    if span_norm and span_norm in full:
        idx = full.index(span_norm)
        stripped = full[idx:].strip()
        if stripped:
            return stripped

    # Fallback: slice from tabaqa or context cue or sahabi
    for pat in [
        r"(?:من\s+(?:كبار|صغار|أوساط|رؤوس|قدماء)?\s*(?:الطبقة\s+)?(?:الحادية|الثانية|الثالثة|الرابعة|الخامسة|السادسة|السابعة|الثامنة|التاسعة|العاشرة|الأولى))",
        r"صحاب[ية]|له\s+صحبة",
    ]:
        m = re.search(pat, full)
        if m:
            parts = []
            if row.get("taqrib_context_note_spans", "").strip():
                parts.append(DIACRITICS_RE.sub("", row["taqrib_context_note_spans"]))
            parts.append(full[m.start() :])
            out = WHITESPACE_RE.sub(" ", " ".join(parts)).strip()
            if out:
                return out

    tokens = []
    if row["tabaqa_1_to_12"]:
        tokens.append(f"طبقة {row['tabaqa_1_to_12']}")
    if row["sigil_tokens_raw"]:
        tokens.append(row["sigil_tokens_raw"])
    return " ".join(tokens).strip() or "غير محدد"


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
    # Zero-leakage check on feature names
    for fn in feat_names:
        assert not any(
            bad in fn for bad in ("tahrir", "graph_", "sanad_", "bukhari_out", "bukhari_in", "nbr_")
        ), f"Leakage feature detected: {fn}"

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


def extract_camelbert_zero_shot(texts: list[str], batch_size: int = 64) -> np.ndarray:
    """Run zero-shot CAMeLBERT-sentiment over all 8,827 Taqrib entries on CUDA."""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(CAMEL_ID, local_files_only=True)
    model = AutoModelForSequenceClassification.from_pretrained(CAMEL_ID, local_files_only=True).to(device)
    model.eval()
    id2label = {int(k): v.lower() for k, v in model.config.id2label.items()}
    pos_idx = next(k for k, v in id2label.items() if "pos" in v)
    neg_idx = next(k for k, v in id2label.items() if "neg" in v)
    neu_idx = next(k for k, v in id2label.items() if "neu" in v)

    probs_all = []
    with torch.no_grad():
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            enc = tok(batch, padding=True, truncation=True, max_length=96, return_tensors="pt").to(device)
            with torch.amp.autocast("cuda", dtype=torch.float16, enabled=(device == "cuda")):
                logits = model(**enc).logits
            probs = torch.softmax(logits.float(), dim=-1).cpu().numpy()
            probs_all.append(probs)
    raw = np.vstack(probs_all)
    p_pos = raw[:, pos_idx : pos_idx + 1]
    p_neu = raw[:, neu_idx : neu_idx + 1]
    p_neg = raw[:, neg_idx : neg_idx + 1]
    polarity = p_pos - p_neg
    del model
    if device == "cuda":
        torch.cuda.empty_cache()
    return np.hstack([p_pos, p_neu, p_neg, polarity]).astype(np.float32)


class TaqribBertDataset(Dataset):
    def __init__(
        self,
        encodings: dict[str, torch.Tensor],
        meta: np.ndarray,
        y_rank: np.ndarray | None = None,
        y_shift: np.ndarray | None = None,
    ) -> None:
        self.input_ids = encodings["input_ids"]
        self.attention_mask = encodings["attention_mask"]
        self.meta = torch.tensor(meta, dtype=torch.float32)
        self.y_rank = torch.tensor(y_rank - 1, dtype=torch.long) if y_rank is not None else None
        self.y_shift = torch.tensor(y_shift, dtype=torch.long) if y_shift is not None else None

    def __len__(self) -> int:
        return self.input_ids.size(0)

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
        item = {
            "input_ids": self.input_ids[idx],
            "attention_mask": self.attention_mask[idx],
            "meta": self.meta[idx],
        }
        if self.y_rank is not None and self.y_shift is not None:
            item["y_rank"] = self.y_rank[idx]
            item["y_shift"] = self.y_shift[idx]
        return item


class AraBERTDualHead(nn.Module):
    def __init__(self, meta_dim: int, dropout: float = 0.2) -> None:
        super().__init__()
        self.bert = AutoModel.from_pretrained(ARABERT_ID, local_files_only=True)
        h_dim = self.bert.config.hidden_size
        self.meta_proj = nn.Sequential(
            nn.Linear(meta_dim, 64),
            nn.LayerNorm(64),
            nn.ReLU(),
            nn.Dropout(dropout),
        )
        fused_dim = h_dim + 64
        self.trunk = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(fused_dim, 256),
            nn.LayerNorm(256),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        self.rank_head = nn.Linear(256, 12)
        self.shift_head = nn.Linear(256, 3)

    def forward(
        self, input_ids: torch.Tensor, attention_mask: torch.Tensor, meta: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        out = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        cls_emb = out.last_hidden_state[:, 0, :]
        m_emb = self.meta_proj(meta)
        h = self.trunk(torch.cat([cls_emb, m_emb], dim=-1))
        return self.rank_head(h), self.shift_head(h), cls_emb


def train_and_eval_arabert(
    train_texts: list[str],
    train_meta: np.ndarray,
    train_rank: np.ndarray,
    train_shift: np.ndarray,
    eval_batches: dict[str, tuple[list[str], np.ndarray]],
    val_key: str,
    val_rank: np.ndarray,
    val_shift: np.ndarray,
    val_is_maqbul: np.ndarray,
    epochs: int = 5,
    batch_size: int = 32,
    seed: int = SEED,
) -> tuple[dict[str, dict[str, np.ndarray]], dict[str, Any]]:
    set_seed(seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(ARABERT_ID, local_files_only=True)

    scaler = StandardScaler()
    tr_meta_sc = scaler.fit_transform(train_meta).astype(np.float32)

    tr_enc = tok(train_texts, padding="max_length", truncation=True, max_length=96, return_tensors="pt")
    tr_ds = TaqribBertDataset(tr_enc, tr_meta_sc, train_rank, train_shift)
    tr_loader = DataLoader(tr_ds, batch_size=batch_size, shuffle=True)

    eval_loaders = {}
    for name, (txts, m_arr) in eval_batches.items():
        enc = tok(txts, padding="max_length", truncation=True, max_length=96, return_tensors="pt")
        ds = TaqribBertDataset(enc, scaler.transform(m_arr).astype(np.float32))
        eval_loaders[name] = DataLoader(ds, batch_size=64, shuffle=False)

    model = AraBERTDualHead(meta_dim=train_meta.shape[1]).to(device)

    # Balanced sqrt inverse frequency weights for 3-class shift head
    cnts = np.bincount(train_shift, minlength=3).astype(np.float32)
    sw = np.sqrt(cnts.sum() / (3.0 * np.maximum(cnts, 1.0)))
    sw = torch.tensor(sw / sw.mean(), dtype=torch.float32, device=device)

    ce_rank = nn.CrossEntropyLoss()
    ce_shift = nn.CrossEntropyLoss(weight=sw)
    smooth_l1 = nn.SmoothL1Loss()
    rank_vals = torch.arange(1, 13, dtype=torch.float32, device=device)

    optimizer = torch.optim.AdamW(
        [
            {"params": model.bert.parameters(), "lr": 2.5e-5},
            {"params": model.meta_proj.parameters(), "lr": 1e-3},
            {"params": model.trunk.parameters(), "lr": 1e-3},
            {"params": model.rank_head.parameters(), "lr": 1e-3},
            {"params": model.shift_head.parameters(), "lr": 1e-3},
        ],
        weight_decay=0.01,
    )
    total_steps = len(tr_loader) * epochs
    warmup_steps = max(1, int(0.1 * total_steps))

    def lr_lambda(step: int) -> float:
        if step < warmup_steps:
            return float(step + 1) / float(warmup_steps)
        progress = float(step - warmup_steps) / float(max(1, total_steps - warmup_steps))
        return max(0.05, 0.5 * (1.0 + math.cos(math.pi * progress)))

    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)
    grad_scaler = torch.amp.GradScaler("cuda", enabled=(device == "cuda"))

    best_score = -1e9
    best_state = None
    best_epoch = 0

    def run_infer(loader: DataLoader) -> dict[str, np.ndarray]:
        model.eval()
        r_probs_list, s_probs_list, cls_list = [], [], []
        with torch.no_grad():
            for b in loader:
                ids = b["input_ids"].to(device)
                mask = b["attention_mask"].to(device)
                meta = b["meta"].to(device)
                with torch.amp.autocast("cuda", dtype=torch.float16, enabled=(device == "cuda")):
                    r_log, s_log, cls_e = model(ids, mask, meta)
                r_probs_list.append(torch.softmax(r_log.float(), dim=-1).cpu().numpy())
                s_probs_list.append(torch.softmax(s_log.float(), dim=-1).cpu().numpy())
                cls_list.append(cls_e.float().cpu().numpy())
        r_probs = np.vstack(r_probs_list)
        s_probs = np.vstack(s_probs_list)
        cls_arr = np.vstack(cls_list)
        r_exp = (r_probs * np.arange(1, 13, dtype=np.float32)).sum(axis=1)
        return {"rank_probs": r_probs, "rank_exp": r_exp, "shift_probs": s_probs, "cls": cls_arr}

    for ep in range(1, epochs + 1):
        model.train()
        for b in tr_loader:
            optimizer.zero_grad()
            ids = b["input_ids"].to(device)
            mask = b["attention_mask"].to(device)
            meta = b["meta"].to(device)
            yr = b["y_rank"].to(device)
            ys = b["y_shift"].to(device)
            with torch.amp.autocast("cuda", dtype=torch.float16, enabled=(device == "cuda")):
                r_log, s_log, _ = model(ids, mask, meta)
                r_probs = torch.softmax(r_log.float(), dim=-1)
                r_exp = (r_probs * rank_vals).sum(dim=-1)
                loss_r = ce_rank(r_log.float(), yr) + 0.35 * smooth_l1(r_exp, (yr + 1).float())
                loss_s = ce_shift(s_log.float(), ys)
                loss = loss_r + 1.0 * loss_s
            grad_scaler.scale(loss).backward()
            grad_scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            grad_scaler.step(optimizer)
            grad_scaler.update()
            scheduler.step()

        val_out = run_infer(eval_loaders[val_key])
        val_m = compute_metrics(
            val_rank,
            val_shift,
            val_out["rank_exp"],
            val_out["shift_probs"].argmax(axis=1),
            val_is_maqbul,
        )
        comp = val_m["shift_macro_f1"] - 0.1 * val_m["rank_mae"]
        if comp > best_score:
            best_score = comp
            best_epoch = ep
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}

    assert best_state is not None
    model.load_state_dict({k: v.to(device) for k, v in best_state.items()})
    outputs = {name: run_infer(ldr) for name, ldr in eval_loaders.items()}
    del model
    if device == "cuda":
        torch.cuda.empty_cache()
    return outputs, {"best_epoch": best_epoch, "best_val_composite": round(best_score, 4)}


def main() -> None:
    t0 = time.time()
    set_seed(SEED)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with TASK_A_V14.open(encoding="utf-8-sig") as f:
        v14_spans = {r["entry_id"]: r["first_complete_target_span_exact"] for r in csv.DictReader(f)}

    with MASTER_NODES.open(encoding="utf-8-sig") as f:
        all_rows = list(csv.DictReader(f))

    assert len(all_rows) == 8827

    texts_full = [normalize_text(r["taqrib_text_verbatim"]) for r in all_rows]
    texts_stripped = [build_name_stripped_text(r, v14_spans.get(r["entry_id"], "")) for r in all_rows]
    assert all(len(t) > 0 for t in texts_stripped), "Empty name-stripped text found"

    X_meta_all, meta_names = build_meta_matrix(all_rows)
    splits = np.array([r["split"] for r in all_rows])
    idx_train = np.where(splits == "train")[0]
    idx_val = np.where(splits == "val")[0]
    idx_test = np.where(splits == "test")[0]
    idx_core = np.where(splits != "excluded_unranked")[0]
    assert len(idx_train) == 5080 and len(idx_val) == 1089 and len(idx_test) == 1089

    y_rank_all = np.array([int(r["tahrir_rank_bilgin_1_to_12"]) if r["tahrir_rank_bilgin_1_to_12"] else -1 for r in all_rows])
    y_shift_all = np.array([SHIFT_TO_ID[r["shift_class"]] if r["shift_class"] else -1 for r in all_rows])
    score1_all = np.array([int(r["taqrib_rank_bilgin_1_to_12"]) if r["taqrib_rank_bilgin_1_to_12"] else -1 for r in all_rows])
    is_maqbul_all = np.array([1 if r["taqrib_is_conditional_maqbul"] == "True" else 0 for r in all_rows])

    comparison_rows: list[dict[str, Any]] = []
    test_preds: dict[str, tuple[np.ndarray, np.ndarray]] = {}

    def record_model(
        name: str,
        family: str,
        vr_cont: np.ndarray,
        vs_pred: np.ndarray,
        tr_cont: np.ndarray,
        ts_pred: np.ndarray,
        notes: str = "",
    ) -> None:
        vm = compute_metrics(y_rank_all[idx_val], y_shift_all[idx_val], vr_cont, vs_pred, is_maqbul_all[idx_val])
        tm = compute_metrics(y_rank_all[idx_test], y_shift_all[idx_test], tr_cont, ts_pred, is_maqbul_all[idx_test])
        test_preds[name] = (tr_cont, ts_pred)
        for sp_name, metrics in [("val", vm), ("test", tm)]:
            comparison_rows.append({"model": name, "family": family, "split": sp_name, **metrics, "notes": notes})
        print(
            f"[{name}] TEST | MAE={tm['rank_mae']:.4f} QWK={tm['rank_qwk']:.4f} "
            f"Exact={tm['rank_exact_acc']:.4f} BinAcc={tm['bin_acc']:.4f} "
            f"ShiftMF1={tm['shift_macro_f1']:.4f} ActiveMF1={tm['shift_active_macro_f1']:.4f} "
            f"R6_MAE={tm['r6_rank_mae']:.4f}"
        )

    # 1. M0 Identity Baseline
    record_model(
        "M0_Identity_Baseline",
        "baseline",
        score1_all[idx_val].astype(float),
        np.ones(len(idx_val), dtype=int),
        score1_all[idx_test].astype(float),
        np.ones(len(idx_test), dtype=int),
        "Predicts Score 1 and unchanged",
    )

    # 2. M1 Metadata-Only Models
    scaler_m = StandardScaler()
    Xm_tr = scaler_m.fit_transform(X_meta_all[idx_train])
    Xm_va = scaler_m.transform(X_meta_all[idx_val])
    Xm_te = scaler_m.transform(X_meta_all[idx_test])

    m1a_reg = Ridge(alpha=1.0, random_state=SEED).fit(Xm_tr, y_rank_all[idx_train])
    m1a_cls = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=SEED).fit(
        Xm_tr, y_shift_all[idx_train]
    )
    record_model(
        "M1a_Meta_Linear",
        "metadata_only",
        np.clip(m1a_reg.predict(Xm_va), 1, 12),
        m1a_cls.predict(Xm_va),
        np.clip(m1a_reg.predict(Xm_te), 1, 12),
        m1a_cls.predict(Xm_te),
        "X_meta only (Ridge + Balanced LogReg)",
    )

    m1b_reg = HistGradientBoostingRegressor(max_iter=250, learning_rate=0.05, random_state=SEED).fit(
        X_meta_all[idx_train], y_rank_all[idx_train]
    )
    m1b_cls = HistGradientBoostingClassifier(
        max_iter=250, learning_rate=0.05, class_weight="balanced", random_state=SEED
    ).fit(X_meta_all[idx_train], y_shift_all[idx_train])
    record_model(
        "M1b_Meta_HistGBDT",
        "metadata_only",
        np.clip(m1b_reg.predict(X_meta_all[idx_val]), 1, 12),
        m1b_cls.predict(X_meta_all[idx_val]),
        np.clip(m1b_reg.predict(X_meta_all[idx_test]), 1, 12),
        m1b_cls.predict(X_meta_all[idx_test]),
        "X_meta only (HistGBDT)",
    )

    m1c_reg = RandomForestRegressor(n_estimators=200, min_samples_leaf=3, random_state=SEED, n_jobs=-1).fit(
        X_meta_all[idx_train], y_rank_all[idx_train]
    )
    m1c_cls = RandomForestClassifier(
        n_estimators=200, min_samples_leaf=3, class_weight="balanced_subsample", random_state=SEED, n_jobs=-1
    ).fit(X_meta_all[idx_train], y_shift_all[idx_train])
    record_model(
        "M1c_Meta_RandomForest",
        "metadata_only",
        np.clip(m1c_reg.predict(X_meta_all[idx_val]), 1, 12),
        m1c_cls.predict(X_meta_all[idx_val]),
        np.clip(m1c_reg.predict(X_meta_all[idx_test]), 1, 12),
        m1c_cls.predict(X_meta_all[idx_test]),
        "X_meta only (RandomForest)",
    )

    # 3. M2 Classical TF-IDF + Metadata (Full & Name-Stripped Ablation)
    def fit_tfidf_linear(text_list: list[str]):
        from scipy.sparse import hstack, csr_matrix

        vec = FeatureUnion(
            [
                ("word", TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=20000, sublinear_tf=True)),
                ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=3, max_features=25000, sublinear_tf=True)),
            ]
        )
        X_txt_tr = vec.fit_transform([text_list[i] for i in idx_train])
        X_txt_va = vec.transform([text_list[i] for i in idx_val])
        X_txt_te = vec.transform([text_list[i] for i in idx_test])

        Xtr = hstack([X_txt_tr, csr_matrix(Xm_tr)])
        Xva = hstack([X_txt_va, csr_matrix(Xm_va)])
        Xte = hstack([X_txt_te, csr_matrix(Xm_te)])

        reg = Ridge(alpha=3.0, random_state=SEED).fit(Xtr, y_rank_all[idx_train])
        cls = LogisticRegression(C=1.5, max_iter=1000, class_weight="balanced", random_state=SEED).fit(
            Xtr, y_shift_all[idx_train]
        )
        return vec, reg, cls, X_txt_tr, X_txt_va, X_txt_te, Xva, Xte

    vec_f, reg_f, cls_f, Xtxt_tr_f, Xtxt_va_f, Xtxt_te_f, Xva_f, Xte_f = fit_tfidf_linear(texts_full)
    record_model(
        "M2a_TFIDF_Full_Linear",
        "tfidf_plus_meta",
        np.clip(reg_f.predict(Xva_f), 1, 12),
        cls_f.predict(Xva_f),
        np.clip(reg_f.predict(Xte_f), 1, 12),
        cls_f.predict(Xte_f),
        "Word(1-2)+Char(3-5) TF-IDF + X_meta (Ridge + LogReg)",
    )

    svd = TruncatedSVD(n_components=64, random_state=SEED)
    Ztr_f = np.hstack([svd.fit_transform(Xtxt_tr_f), X_meta_all[idx_train]])
    Zva_f = np.hstack([svd.transform(Xtxt_va_f), X_meta_all[idx_val]])
    Zte_f = np.hstack([svd.transform(Xtxt_te_f), X_meta_all[idx_test]])
    m2b_reg = HistGradientBoostingRegressor(max_iter=250, learning_rate=0.05, random_state=SEED).fit(
        Ztr_f, y_rank_all[idx_train]
    )
    m2b_cls = HistGradientBoostingClassifier(
        max_iter=250, learning_rate=0.05, class_weight="balanced", random_state=SEED
    ).fit(Ztr_f, y_shift_all[idx_train])
    record_model(
        "M2b_TFIDF_Full_HistGBDT",
        "tfidf_plus_meta",
        np.clip(m2b_reg.predict(Zva_f), 1, 12),
        m2b_cls.predict(Zva_f),
        np.clip(m2b_reg.predict(Zte_f), 1, 12),
        m2b_cls.predict(Zte_f),
        "SVD-64 TF-IDF + X_meta (HistGBDT)",
    )

    _, reg_ns, cls_ns, _, _, _, Xva_ns, Xte_ns = fit_tfidf_linear(texts_stripped)
    record_model(
        "M2c_TFIDF_NameStripped_Linear",
        "name_stripped_ablation",
        np.clip(reg_ns.predict(Xva_ns), 1, 12),
        cls_ns.predict(Xva_ns),
        np.clip(reg_ns.predict(Xte_ns), 1, 12),
        cls_ns.predict(Xte_ns),
        "Decision 2 Ablation: Name-stripped TF-IDF + X_meta",
    )

    # 4. M3a CAMeLBERT Zero-Shot Generic-Sentiment Baseline + Meta
    print("Running CAMeLBERT zero-shot generic-sentiment baseline inference on 8,827 entries...")
    camel_feats = extract_camelbert_zero_shot(texts_full, batch_size=64)
    Xcm_tr = np.hstack([X_meta_all[idx_train], camel_feats[idx_train]])
    Xcm_va = np.hstack([X_meta_all[idx_val], camel_feats[idx_val]])
    Xcm_te = np.hstack([X_meta_all[idx_test], camel_feats[idx_test]])
    m3a_reg = HistGradientBoostingRegressor(max_iter=250, learning_rate=0.05, random_state=SEED).fit(
        Xcm_tr, y_rank_all[idx_train]
    )
    m3a_cls = HistGradientBoostingClassifier(
        max_iter=250, learning_rate=0.05, class_weight="balanced", random_state=SEED
    ).fit(Xcm_tr, y_shift_all[idx_train])
    record_model(
        "M3a_CAMeLBERT_Sentiment_Plus_Meta",
        "arabic_transformer",
        np.clip(m3a_reg.predict(Xcm_va), 1, 12),
        m3a_cls.predict(Xcm_va),
        np.clip(m3a_reg.predict(Xcm_te), 1, 12),
        m3a_cls.predict(Xcm_te),
        "Generic-sentiment baseline: zero-shot CAMeLBERT-MSA-sentiment + X_meta (HistGBDT)",
    )

    # 5. M3b AraBERTv02 Full Dual-Head & 5-Fold OOF inside train
    print("Running 5-Fold OOF AraBERTv02 Dual-Head (Full) + M2a 5-Fold OOF inside train=5,080...")
    skf_strata = [
        f"{y_rank_all[i]}_{y_shift_all[i]}" for i in idx_train
    ]
    cnt_str = Counter(skf_strata)
    skf_labels = [
        skf_strata[k] if cnt_str[skf_strata[k]] >= 5 else str(y_rank_all[idx_train[k]])
        for k in range(len(idx_train))
    ]
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)

    # M2a 5-fold OOF arrays
    from scipy.sparse import hstack, csr_matrix

    m2_oof_rank = np.zeros(len(all_rows), dtype=np.float32)
    m2_oof_sprobs = np.zeros((len(all_rows), 3), dtype=np.float32)
    idx_non_train = np.where(splits != "train")[0]

    for fold_id, (f_tr_rel, f_va_rel) in enumerate(skf.split(idx_train, skf_labels)):
        f_tr = idx_train[f_tr_rel]
        f_va = idx_train[f_va_rel]
        sc_f = StandardScaler()
        Xm_f_tr = sc_f.fit_transform(X_meta_all[f_tr])
        Xm_f_va = sc_f.transform(X_meta_all[f_va])
        Xm_f_nt = sc_f.transform(X_meta_all[idx_non_train])

        vec_k = FeatureUnion(
            [
                ("word", TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=20000, sublinear_tf=True)),
                ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=3, max_features=25000, sublinear_tf=True)),
            ]
        )
        Xt_tr = hstack([vec_k.fit_transform([texts_full[i] for i in f_tr]), csr_matrix(Xm_f_tr)])
        Xt_va = hstack([vec_k.transform([texts_full[i] for i in f_va]), csr_matrix(Xm_f_va)])
        Xt_nt = hstack([vec_k.transform([texts_full[i] for i in idx_non_train]), csr_matrix(Xm_f_nt)])

        rk_k = Ridge(alpha=3.0, random_state=SEED).fit(Xt_tr, y_rank_all[f_tr])
        cl_k = LogisticRegression(C=1.5, max_iter=1000, class_weight="balanced", random_state=SEED).fit(
            Xt_tr, y_shift_all[f_tr]
        )
        m2_oof_rank[f_va] = np.clip(rk_k.predict(Xt_va), 1, 12)
        m2_oof_sprobs[f_va] = cl_k.predict_proba(Xt_va)
        m2_oof_rank[idx_non_train] += np.clip(rk_k.predict(Xt_nt), 1, 12) / 5.0
        m2_oof_sprobs[idx_non_train] += cl_k.predict_proba(Xt_nt) / 5.0

    # M3b 5-Fold OOF AraBERTv02 Full Dual-Head
    arabert_oof_rank_exp = np.zeros(len(all_rows), dtype=np.float32)
    arabert_oof_rprobs = np.zeros((len(all_rows), 12), dtype=np.float32)
    arabert_oof_sprobs = np.zeros((len(all_rows), 3), dtype=np.float32)
    arabert_oof_cls = np.zeros((len(all_rows), 768), dtype=np.float32)
    fold_epochs = []

    for fold_id, (f_tr_rel, f_va_rel) in enumerate(skf.split(idx_train, skf_labels)):
        f_tr = idx_train[f_tr_rel]
        f_va = idx_train[f_va_rel]
        print(f"  Training AraBERTv02 Full Fold {fold_id + 1}/5 (tr={len(f_tr)}, fold_val={len(f_va)})...")
        eval_b = {
            "fold_val": ([texts_full[i] for i in f_va], X_meta_all[f_va]),
            "val": ([texts_full[i] for i in idx_val], X_meta_all[idx_val]),
            "test": ([texts_full[i] for i in idx_test], X_meta_all[idx_test]),
            "excl": ([texts_full[i] for i in np.where(splits == "excluded_unranked")[0]], X_meta_all[splits == "excluded_unranked"]),
        }
        outs, info = train_and_eval_arabert(
            [texts_full[i] for i in f_tr],
            X_meta_all[f_tr],
            y_rank_all[f_tr],
            y_shift_all[f_tr],
            eval_b,
            val_key="fold_val",
            val_rank=y_rank_all[f_va],
            val_shift=y_shift_all[f_va],
            val_is_maqbul=is_maqbul_all[f_va],
            epochs=5,
            batch_size=32,
            seed=SEED + fold_id,
        )
        fold_epochs.append(info["best_epoch"])
        arabert_oof_rank_exp[f_va] = outs["fold_val"]["rank_exp"]
        arabert_oof_rprobs[f_va] = outs["fold_val"]["rank_probs"]
        arabert_oof_sprobs[f_va] = outs["fold_val"]["shift_probs"]
        arabert_oof_cls[f_va] = outs["fold_val"]["cls"]

        for key, idxs in [("val", idx_val), ("test", idx_test), ("excl", np.where(splits == "excluded_unranked")[0])]:
            arabert_oof_rank_exp[idxs] += outs[key]["rank_exp"] / 5.0
            arabert_oof_rprobs[idxs] += outs[key]["rank_probs"] / 5.0
            arabert_oof_sprobs[idxs] += outs[key]["shift_probs"] / 5.0
            arabert_oof_cls[idxs] += outs[key]["cls"] / 5.0

    record_model(
        "M3b_AraBERTv02_Full_DualHead",
        "arabic_transformer",
        arabert_oof_rank_exp[idx_val],
        arabert_oof_sprobs[idx_val].argmax(axis=1),
        arabert_oof_rank_exp[idx_test],
        arabert_oof_sprobs[idx_test].argmax(axis=1),
        f"5-fold train-ensemble Dual-Head AraBERTv02 + X_meta (best epochs: {fold_epochs})",
    )

    # 6. M3c AraBERTv02 Name-Stripped Ablation (single train->val/test fit)
    print("Training AraBERTv02 Name-Stripped Dual-Head (Decision 2 Ablation)...")
    outs_ns, info_ns = train_and_eval_arabert(
        [texts_stripped[i] for i in idx_train],
        X_meta_all[idx_train],
        y_rank_all[idx_train],
        y_shift_all[idx_train],
        {
            "val": ([texts_stripped[i] for i in idx_val], X_meta_all[idx_val]),
            "test": ([texts_stripped[i] for i in idx_test], X_meta_all[idx_test]),
        },
        val_key="val",
        val_rank=y_rank_all[idx_val],
        val_shift=y_shift_all[idx_val],
        val_is_maqbul=is_maqbul_all[idx_val],
        epochs=5,
        batch_size=32,
        seed=SEED,
    )
    record_model(
        "M3c_AraBERTv02_NameStripped_DualHead",
        "name_stripped_ablation",
        outs_ns["val"]["rank_exp"],
        outs_ns["val"]["shift_probs"].argmax(axis=1),
        outs_ns["test"]["rank_exp"],
        outs_ns["test"]["shift_probs"].argmax(axis=1),
        f"Decision 2 Ablation: Name-stripped AraBERTv02 + X_meta (best ep={info_ns['best_epoch']})",
    )

    # Fit 32-dim PCA strictly on train CLS embeddings
    pca = PCA(n_components=32, random_state=SEED)
    pca.fit(arabert_oof_cls[idx_train])
    cls_pca32 = pca.transform(arabert_oof_cls).astype(np.float32)

    # Write STAGE2_OOF_SEMANTIC_FEATURES_8827_V2.csv
    oof_csv = OUT_DIR / "STAGE2_OOF_SEMANTIC_FEATURES_8827_V2.csv"
    oof_cols = (
        ["entry_id", "split", "in_core_cohort_7258"]
        + ["camel_p_pos", "camel_p_neu", "camel_p_neg", "camel_polarity"]
        + ["m2_oof_rank_pred", "m2_oof_p_up", "m2_oof_p_unch", "m2_oof_p_down"]
        + ["arabert_oof_rank_exp"]
        + [f"arabert_p_r{k}" for k in range(1, 13)]
        + ["arabert_p_up", "arabert_p_unch", "arabert_p_down"]
        + [f"arabert_cls_pca_{d:02d}" for d in range(32)]
    )
    with oof_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(oof_cols)
        for i, r in enumerate(all_rows):
            row_vals = (
                [r["entry_id"], r["split"], r["in_core_cohort_7258"]]
                + [f"{camel_feats[i, j]:.6f}" for j in range(4)]
                + [f"{m2_oof_rank[i]:.6f}"]
                + [f"{m2_oof_sprobs[i, j]:.6f}" for j in range(3)]
                + [f"{arabert_oof_rank_exp[i]:.6f}"]
                + [f"{arabert_oof_rprobs[i, j]:.6f}" for j in range(12)]
                + [f"{arabert_oof_sprobs[i, j]:.6f}" for j in range(3)]
                + [f"{cls_pca32[i, j]:.6f}" for j in range(32)]
            )
            assert not any(math.isnan(float(x)) for x in row_vals[3:]), f"NaN in OOF row {i}"
            w.writerow(row_vals)

    # Write STAGE2_MODEL_COMPARISON_V2.csv
    comp_csv = OUT_DIR / "STAGE2_MODEL_COMPARISON_V2.csv"
    with comp_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(comparison_rows[0].keys()))
        w.writeheader()
        w.writerows(comparison_rows)

    # Write STAGE2_TEST_PREDICTIONS_V2.csv
    pred_csv = OUT_DIR / "STAGE2_TEST_PREDICTIONS_V2.csv"
    pred_fields = [
        "entry_id",
        "taqrib_rank_bilgin_1_to_12",
        "tahrir_rank_bilgin_1_to_12",
        "shift_class",
        "taqrib_is_conditional_maqbul",
    ]
    for m_name in test_preds:
        pred_fields.extend([f"{m_name}_rank_pred", f"{m_name}_shift_pred"])
    with pred_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=pred_fields)
        w.writeheader()
        for k, gi in enumerate(idx_test):
            r = all_rows[gi]
            row_d = {
                "entry_id": r["entry_id"],
                "taqrib_rank_bilgin_1_to_12": r["taqrib_rank_bilgin_1_to_12"],
                "tahrir_rank_bilgin_1_to_12": r["tahrir_rank_bilgin_1_to_12"],
                "shift_class": r["shift_class"],
                "taqrib_is_conditional_maqbul": r["taqrib_is_conditional_maqbul"],
            }
            for m_name, (rc, sp) in test_preds.items():
                row_d[f"{m_name}_rank_pred"] = f"{rc[k]:.4f}"
                row_d[f"{m_name}_shift_pred"] = SHIFT_LABELS[int(sp[k])]
            w.writerow(row_d)

    # Per-rank and shift detailed breakdown on test for key models
    per_cls_rows = []
    for m_name in ["M0_Identity_Baseline", "M1b_Meta_HistGBDT", "M2a_TFIDF_Full_Linear", "M3b_AraBERTv02_Full_DualHead", "M3c_AraBERTv02_NameStripped_DualHead"]:
        rc, sp = test_preds[m_name]
        r_disc = np.clip(np.rint(rc), 1, 12).astype(int)
        p, rec, f1, sup = precision_recall_fscore_support(y_rank_all[idx_test], r_disc, labels=list(range(1, 13)), zero_division=0)
        for idx_r in range(12):
            per_cls_rows.append({"model": m_name, "task": "rank_1_to_12", "class_label": str(idx_r + 1), "precision": round(float(p[idx_r]), 4), "recall": round(float(rec[idx_r]), 4), "f1": round(float(f1[idx_r]), 4), "support": int(sup[idx_r])})
        ps, recs, f1s, sups = precision_recall_fscore_support(y_shift_all[idx_test], sp, labels=[0, 1, 2], zero_division=0)
        for idx_s in range(3):
            per_cls_rows.append({"model": m_name, "task": "shift_3class", "class_label": SHIFT_LABELS[idx_s], "precision": round(float(ps[idx_s]), 4), "recall": round(float(recs[idx_s]), 4), "f1": round(float(f1s[idx_s]), 4), "support": int(sups[idx_s])})

    per_cls_csv = OUT_DIR / "STAGE2_PER_RANK_AND_SHIFT_METRICS_V2.csv"
    with per_cls_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(per_cls_rows[0].keys()))
        w.writeheader()
        w.writerows(per_cls_rows)

    # Write Markdown Report
    test_rows = [r for r in comparison_rows if r["split"] == "test"]
    md_lines = [
        "# Stage 2: Evaluative Stance Analysis (ESA) Benchmark Report (v2)",
        "",
        f"- **Generated (UTC):** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%SZ')}",
        f"- **Elapsed:** {time.time() - t0:.1f}s | **Device:** {'CUDA (' + torch.cuda.get_device_name(0) + ')' if torch.cuda.is_available() else 'CPU'}",
        "- **Cohort:** `N = 7,258` (`train = 5,080`, `val = 1,089`, `test = 1,089`), ZERO graph columns & ZERO *Taḥrīr* leakage.",
        "",
        "## 1. Test Split Benchmark Table (`N = 1,089`)",
        "",
        "| Model | Family | Rank MAE ↓ | QWK ↑ | Exact Acc ↑ | Bin Acc (Wahba) ↑ | Bin w-F1 (Wahba) ↑ | Shift MF1 (StanceEval) ↑ | Active MF1 ↑ | R6 Maqbūl MAE ↓ |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in test_rows:
        md_lines.append(
            f"| `{r['model']}` | `{r['family']}` | {r['rank_mae']:.4f} | {r['rank_qwk']:.4f} | {r['rank_exact_acc']:.4f} | "
            f"{r['bin_acc']:.4f} | {r['bin_weighted_f1']:.4f} | {r['shift_macro_f1']:.4f} | {r['shift_active_macro_f1']:.4f} | {r['r6_rank_mae']:.4f} |"
        )
    report_md = OUT_DIR / "STAGE2_RESULTS_SUMMARY_V2.md"
    report_md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    manifest_files = [comp_csv, per_cls_csv, pred_csv, oof_csv, report_md]
    manifest = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "script": "experiments/run_stage2_semantic_benchmarks_v2.py",
        "elapsed_sec": round(time.time() - t0, 2),
        "test_summary": test_rows,
        "files": {p.name: {"sha256": sha256_file(p), "bytes": p.stat().st_size} for p in manifest_files},
    }
    manifest_json = OUT_DIR / "MANIFEST.json"
    manifest_json.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT_DIR / "MANIFEST.sha256").write_text(
        "\n".join(f"{sha256_file(p)}  {p.name}" for p in [*manifest_files, manifest_json]) + "\n",
        encoding="utf-8",
    )
    print("Stage 2 complete in", round(time.time() - t0, 1), "s ->", OUT_DIR)


if __name__ == "__main__":
    main()
