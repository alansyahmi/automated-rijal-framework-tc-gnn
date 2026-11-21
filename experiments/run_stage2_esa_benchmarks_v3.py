#!/usr/bin/env python3
"""Stage 2: Evaluative Stance Analysis (ESA) Benchmarks (taqrib-oriented-v2 / v3).

Evaluates strictly on Ibn Hajar's Taqrib al-Tahdhib (3076) text + structured metadata
(ZERO graph columns, ZERO Tahrir text/verdict leakage) for Dual-Target prediction:
  - Target A (Tahrir Ordinal): Tahrir Bilgin-grounded 1-12 rank (score_E2 target)
  - Target B (3-Class Shift): upgraded / unchanged / downgraded vs Baseline B (score_B)

Key v3 updates (P4.1):
  - Excludes rows with status_E2 in {missing, suspect_alignment} from train/val/test evaluation.
  - Reports 3-tier ordinal metrics (1-3 / 4-6 / 7-12) per PO1 alongside 12-rank, binary, and shift metrics.
  - Reports the 'Taqrib abstained, Tahrir graded' (observed_first_grade) slice separately.
  - Relabels M3a_CAMeLBERT_Sentiment_Plus_Meta as the generic-sentiment baseline.
  - Exports 5-fold zero-leakage OOF ESA features across all 8,827 rows for Stage 3 TC-GNN.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import random
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
from sklearn.decomposition import PCA, TruncatedSVD
from sklearn.ensemble import (
    HistGradientBoostingClassifier,
    HistGradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import precision_recall_fscore_support
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import FeatureUnion
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModel, AutoModelForSequenceClassification, AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from common.hashing import sha256_text_normalized, to_posix_relative
from experiments.mps_layers import empty_device_cache, select_device
from experiments.v3_common import (
    DIACRITICS_RE,
    EXCLUDED_E2_STATUSES,
    SHIFT_LABELS,
    SHIFT_TO_ID,
    WHITESPACE_RE,
    build_meta_matrix,
    compute_metrics,
    normalize_text,
)

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

PIPELINE = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline"
MASTER_NODES = PIPELINE / "taqrib_v2_master_dataset_2026-11-20/TAQRIB_V2_MASTER_NODES_8827.csv"
TASK_A_V14 = PIPELINE / "task_a_deterministic_targets_v1_4_2026-11-19/TASK_A_DETERMINISTIC_TARGETS_8827_V1_4.csv"
LAYERED_WIDE = PIPELINE / "layered_scores_v3_2026-11-21/LAYERED_SCORES_WIDE_V3.csv"
LAYER_RULES = ROOT / "dataset_discovery/target_feasibility/layer_rules_v3.json"
DEFAULT_OUT_DIR = ROOT / "results/stage2_esa_benchmarks_v3_2026-11-21"

SEED = 42
ARABERT_ID = "aubmindlab/bert-base-arabertv02"
CAMEL_ID = "CAMeL-Lab/bert-base-arabic-camelbert-msa-sentiment"


def set_seed(seed: int = SEED) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    if hasattr(torch, "mps") and hasattr(torch.mps, "manual_seed"):
        torch.mps.manual_seed(seed)


def build_name_stripped_text(row: dict[str, str], target_span: str) -> str:
    full = normalize_text(row["taqrib_text_verbatim"])
    span_norm = DIACRITICS_RE.sub("", target_span).strip()
    if span_norm and span_norm in full:
        idx = full.index(span_norm)
        stripped = full[idx:].strip()
        if stripped:
            return stripped

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


def extract_camelbert_zero_shot(
    texts: list[str],
    batch_size: int = 32,
    local_files_only: bool = True,
    device: torch.device | None = None,
) -> np.ndarray:
    """Run zero-shot generic-sentiment baseline (CAMeLBERT-MSA-sentiment) over all 8,827 Taqrib entries."""
    dev = device or select_device("auto")
    tok = AutoTokenizer.from_pretrained(CAMEL_ID, local_files_only=local_files_only)
    model = AutoModelForSequenceClassification.from_pretrained(CAMEL_ID, local_files_only=local_files_only).to(dev)
    model.eval()
    id2label = {int(k): v.lower() for k, v in model.config.id2label.items()}
    pos_idx = next(k for k, v in id2label.items() if "pos" in v)
    neg_idx = next(k for k, v in id2label.items() if "neg" in v)
    neu_idx = next(k for k, v in id2label.items() if "neu" in v)

    probs_all = []
    with torch.no_grad():
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            enc = tok(batch, padding=True, truncation=True, max_length=96, return_tensors="pt").to(dev)
            with torch.cuda.amp.autocast(dtype=torch.float16, enabled=(dev.type == "cuda")):
                logits = model(**enc).logits
            probs = torch.softmax(logits.float(), dim=-1).cpu().numpy()
            probs_all.append(probs)
    raw = np.vstack(probs_all)
    p_pos = raw[:, pos_idx : pos_idx + 1]
    p_neu = raw[:, neu_idx : neu_idx + 1]
    p_neg = raw[:, neg_idx : neg_idx + 1]
    polarity = p_pos - p_neg
    del model
    empty_device_cache(dev)
    return np.hstack([p_pos, p_neu, p_neg, polarity]).astype(np.float32)


class TaqribBertDataset(Dataset):
    def __init__(
        self,
        token_ids_list: list[list[int]],
        meta: np.ndarray,
        y_rank: np.ndarray | None = None,
        y_shift: np.ndarray | None = None,
    ) -> None:
        self.token_ids = token_ids_list
        self.meta = torch.tensor(meta, dtype=torch.float32)
        self.y_rank = torch.tensor(y_rank - 1, dtype=torch.long) if y_rank is not None else None
        self.y_shift = torch.tensor(y_shift, dtype=torch.long) if y_shift is not None else None

    def __len__(self) -> int:
        return len(self.token_ids)

    def __getitem__(self, idx: int) -> dict[str, Any]:
        item: dict[str, Any] = {
            "ids": self.token_ids[idx],
            "meta": self.meta[idx],
        }
        if self.y_rank is not None and self.y_shift is not None:
            item["y_rank"] = self.y_rank[idx]
            item["y_shift"] = self.y_shift[idx]
        return item


def make_dynamic_collate(pad_id: int):
    def collate(batch: list[dict[str, Any]]) -> dict[str, torch.Tensor]:
        max_len = max(len(b["ids"]) for b in batch)
        input_ids = torch.full((len(batch), max_len), pad_id, dtype=torch.long)
        attention_mask = torch.zeros((len(batch), max_len), dtype=torch.long)
        for i, b in enumerate(batch):
            seq = b["ids"]
            input_ids[i, : len(seq)] = torch.tensor(seq, dtype=torch.long)
            attention_mask[i, : len(seq)] = 1
        out: dict[str, torch.Tensor] = {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "meta": torch.stack([b["meta"] for b in batch], dim=0),
        }
        if "y_rank" in batch[0]:
            out["y_rank"] = torch.stack([b["y_rank"] for b in batch], dim=0)
            out["y_shift"] = torch.stack([b["y_shift"] for b in batch], dim=0)
        return out

    return collate


class AraBERTDualHead(nn.Module):
    def __init__(self, meta_dim: int, dropout: float = 0.2, local_files_only: bool = True) -> None:
        super().__init__()
        self.bert = AutoModel.from_pretrained(ARABERT_ID, local_files_only=local_files_only)
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
    grad_accum: int = 1,
    max_length: int = 96,
    seed: int = SEED,
    local_files_only: bool = True,
    device: torch.device | None = None,
) -> tuple[dict[str, dict[str, np.ndarray]], dict[str, Any]]:
    set_seed(seed)
    dev = device or select_device("auto")
    tok = AutoTokenizer.from_pretrained(ARABERT_ID, local_files_only=local_files_only)
    pad_id = tok.pad_token_id if tok.pad_token_id is not None else 0
    collate_fn = make_dynamic_collate(pad_id)

    scaler = StandardScaler()
    tr_meta_sc = scaler.fit_transform(train_meta).astype(np.float32)

    tr_ids = tok(train_texts, truncation=True, max_length=max_length)["input_ids"]
    tr_ds = TaqribBertDataset(tr_ids, tr_meta_sc, train_rank, train_shift)
    tr_loader = DataLoader(tr_ds, batch_size=batch_size, shuffle=True, collate_fn=collate_fn)

    eval_bs = 32 if dev.type == "mps" else 64
    eval_loaders = {}
    for name, (txts, m_arr) in eval_batches.items():
        ids_list = tok(txts, truncation=True, max_length=max_length)["input_ids"]
        ds = TaqribBertDataset(ids_list, scaler.transform(m_arr).astype(np.float32))
        eval_loaders[name] = DataLoader(ds, batch_size=eval_bs, shuffle=False, collate_fn=collate_fn)

    model = AraBERTDualHead(meta_dim=train_meta.shape[1], local_files_only=local_files_only).to(dev)

    cnts = np.bincount(train_shift, minlength=3).astype(np.float32)
    sw = np.sqrt(cnts.sum() / (3.0 * np.maximum(cnts, 1.0)))
    sw = torch.tensor(sw / sw.mean(), dtype=torch.float32, device=dev)

    ce_rank = nn.CrossEntropyLoss()
    ce_shift = nn.CrossEntropyLoss(weight=sw)
    smooth_l1 = nn.SmoothL1Loss()
    rank_vals = torch.arange(1, 13, dtype=torch.float32, device=dev)

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
    steps_per_epoch = max(1, math.ceil(len(tr_loader) / max(1, grad_accum)))
    total_steps = steps_per_epoch * epochs
    warmup_steps = max(1, int(0.1 * total_steps))

    def lr_lambda(step: int) -> float:
        if step < warmup_steps:
            return float(step + 1) / float(warmup_steps)
        progress = float(step - warmup_steps) / float(max(1, total_steps - warmup_steps))
        return max(0.05, 0.5 * (1.0 + math.cos(math.pi * progress)))

    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)
    use_cuda_amp = dev.type == "cuda"
    grad_scaler = torch.cuda.amp.GradScaler(enabled=use_cuda_amp)

    best_score = -1e9
    best_state = None
    best_epoch = 0

    def run_infer(loader: DataLoader) -> dict[str, np.ndarray]:
        model.eval()
        r_probs_list, s_probs_list, cls_list = [], [], []
        with torch.no_grad():
            for b in loader:
                ids = b["input_ids"].to(dev)
                mask = b["attention_mask"].to(dev)
                meta = b["meta"].to(dev)
                with torch.cuda.amp.autocast(dtype=torch.float16, enabled=use_cuda_amp):
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
        optimizer.zero_grad()
        n_batches = len(tr_loader)
        for b_idx, b in enumerate(tr_loader):
            ids = b["input_ids"].to(dev)
            mask = b["attention_mask"].to(dev)
            meta = b["meta"].to(dev)
            yr = b["y_rank"].to(dev)
            ys = b["y_shift"].to(dev)
            with torch.cuda.amp.autocast(dtype=torch.float16, enabled=use_cuda_amp):
                r_log, s_log, _ = model(ids, mask, meta)
                r_probs = torch.softmax(r_log.float(), dim=-1)
                r_exp = (r_probs * rank_vals).sum(dim=-1)
                loss_r = ce_rank(r_log.float(), yr) + 0.35 * smooth_l1(r_exp, (yr + 1).float())
                loss_s = ce_shift(s_log.float(), ys)
                loss = (loss_r + 1.0 * loss_s) / float(max(1, grad_accum))
            grad_scaler.scale(loss).backward()
            if (b_idx + 1) % grad_accum == 0 or (b_idx + 1) == n_batches:
                grad_scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                grad_scaler.step(optimizer)
                grad_scaler.update()
                optimizer.zero_grad()
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
    model.load_state_dict({k: v.to(dev) for k, v in best_state.items()})
    outputs = {name: run_infer(ldr) for name, ldr in eval_loaders.items()}
    del model
    empty_device_cache(dev)
    return outputs, {"best_epoch": best_epoch, "best_val_composite": round(best_score, 4)}


def load_v3_stage2_inputs(
    master_csv: Path = MASTER_NODES,
    layered_csv: Path = LAYERED_WIDE,
) -> dict[str, Any]:
    """Load master nodes + v3 layered statuses, excluding missing/suspect_alignment from splits."""
    with master_csv.open(encoding="utf-8-sig") as f:
        all_rows = list(csv.DictReader(f))
    with layered_csv.open(encoding="utf-8-sig") as f:
        layered_by_id = {r["entry_id"]: r for r in csv.DictReader(f)}

    assert len(all_rows) == 8827 and len(layered_by_id) == 8827

    statuses_e2 = np.array([layered_by_id[r["entry_id"]]["status_E2"] for r in all_rows])
    splits = np.array([r["split"] for r in all_rows])
    eligible_eval = np.array([st not in EXCLUDED_E2_STATUSES for st in statuses_e2])

    idx_train = np.where((splits == "train") & eligible_eval)[0]
    idx_val = np.where((splits == "val") & eligible_eval)[0]
    idx_test = np.where((splits == "test") & eligible_eval)[0]
    idx_first_grade = np.where(statuses_e2 == "observed_first_grade")[0]

    # Use v3 rank_E2 (which fixes the 11 ASCII overrides and excludes unmatched/unmappable)
    y_rank_all = np.array(
        [
            int(layered_by_id[r["entry_id"]]["rank_E2"])
            if layered_by_id[r["entry_id"]]["rank_E2"]
            else -1
            for r in all_rows
        ]
    )
    score_b_all = np.array(
        [
            int(layered_by_id[r["entry_id"]]["rank_B"])
            if layered_by_id[r["entry_id"]]["rank_B"]
            else -1
            for r in all_rows
        ]
    )
    y_shift_all = np.full(len(all_rows), -1, dtype=int)
    for i in range(len(all_rows)):
        if score_b_all[i] > 0 and y_rank_all[i] > 0:
            diff = y_rank_all[i] - score_b_all[i]
            y_shift_all[i] = 0 if diff < 0 else (1 if diff == 0 else 2)

    is_maqbul_all = np.array([1 if r["taqrib_is_conditional_maqbul"] == "True" else 0 for r in all_rows])
    return {
        "all_rows": all_rows,
        "layered_by_id": layered_by_id,
        "statuses_e2": statuses_e2,
        "splits": splits,
        "eligible_eval": eligible_eval,
        "idx_train": idx_train,
        "idx_val": idx_val,
        "idx_test": idx_test,
        "idx_first_grade": idx_first_grade,
        "y_rank_all": y_rank_all,
        "score_b_all": score_b_all,
        "y_shift_all": y_shift_all,
        "is_maqbul_all": is_maqbul_all,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Stage 2 ESA Benchmarks (v3).")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--device", type=str, default="auto", choices=["auto", "mps", "cuda", "cpu"])
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=0, help="0 = auto (16 on MPS for 4GB VRAM, 32 on CUDA/CPU).")
    parser.add_argument("--grad-accum", type=int, default=0, help="0 = auto (2 on MPS -> eff bs 32, 1 on CUDA/CPU).")
    parser.add_argument("--max-length", type=int, default=96)
    parser.add_argument("--resume", action="store_true", help="Resume from cached fold/checkpoint files inside out-dir.")
    parser.add_argument("--allow-hf-download", action="store_true", help="Allow downloading HF models if not cached locally.")
    args = parser.parse_args()

    t0 = time.time()
    set_seed(SEED)
    device = select_device(args.device)
    batch_size = args.batch_size if args.batch_size > 0 else (16 if device.type == "mps" else 32)
    grad_accum = args.grad_accum if args.grad_accum > 0 else (2 if device.type == "mps" else 1)
    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    ckpt_dir = out_dir / "checkpoints"
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    local_only = not args.allow_hf_download
    print(f"Stage 2 v3 device={device.type}, batch_size={batch_size}, grad_accum={grad_accum}, epochs={args.epochs}")

    with TASK_A_V14.open(encoding="utf-8-sig") as f:
        v14_spans = {r["entry_id"]: r["first_complete_target_span_exact"] for r in csv.DictReader(f)}

    data = load_v3_stage2_inputs()
    all_rows = data["all_rows"]
    statuses_e2 = data["statuses_e2"]
    idx_train = data["idx_train"]
    idx_val = data["idx_val"]
    idx_test = data["idx_test"]
    idx_first_grade = data["idx_first_grade"]
    y_rank_all = data["y_rank_all"]
    score_b_all = data["score_b_all"]
    y_shift_all = data["y_shift_all"]
    is_maqbul_all = data["is_maqbul_all"]

    assert all(statuses_e2[i] not in EXCLUDED_E2_STATUSES for i in [*idx_train, *idx_val, *idx_test])
    assert all(y_rank_all[i] > 0 and y_shift_all[i] >= 0 for i in [*idx_train, *idx_val, *idx_test])

    texts_full = [normalize_text(r["taqrib_text_verbatim"]) for r in all_rows]
    texts_stripped = [build_name_stripped_text(r, v14_spans.get(r["entry_id"], "")) for r in all_rows]
    assert all(len(t) > 0 for t in texts_stripped)

    X_meta_all, _ = build_meta_matrix(all_rows)

    comparison_rows: list[dict[str, Any]] = []
    test_preds: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    first_grade_rows: list[dict[str, Any]] = []

    def record_model(
        name: str,
        family: str,
        vr_cont: np.ndarray,
        vs_pred: np.ndarray,
        tr_cont: np.ndarray,
        ts_pred: np.ndarray,
        notes: str = "",
        fg_cont: np.ndarray | None = None,
    ) -> None:
        vm = compute_metrics(y_rank_all[idx_val], y_shift_all[idx_val], vr_cont, vs_pred, is_maqbul_all[idx_val])
        tm = compute_metrics(y_rank_all[idx_test], y_shift_all[idx_test], tr_cont, ts_pred, is_maqbul_all[idx_test])
        test_preds[name] = (tr_cont, ts_pred)
        for sp_name, metrics in [("val", vm), ("test", tm)]:
            comparison_rows.append({"model": name, "family": family, "split": sp_name, **metrics, "notes": notes})
        if fg_cont is not None and len(idx_first_grade) > 0:
            fg_m = compute_metrics(
                y_rank_all[idx_first_grade],
                np.ones(len(idx_first_grade), dtype=int),
                fg_cont,
                np.ones(len(idx_first_grade), dtype=int),
                is_maqbul_all[idx_first_grade],
            )
            first_grade_rows.append(
                {
                    "model": name,
                    "n": len(idx_first_grade),
                    "rank_mae": fg_m["rank_mae"],
                    "rank_qwk": fg_m["rank_qwk"],
                    "rank_exact_acc": fg_m["rank_exact_acc"],
                    "bin_acc": fg_m["bin_acc"],
                    "tier3_macro_f1": fg_m["tier3_macro_f1"],
                }
            )
        print(
            f"[{name}] TEST (N={len(idx_test)}) | MAE={tm['rank_mae']:.4f} QWK={tm['rank_qwk']:.4f} "
            f"BinAcc={tm['bin_acc']:.4f} Tier3MF1={tm['tier3_macro_f1']:.4f} ShiftMF1={tm['shift_macro_f1']:.4f}"
        )

    # 1. M0 Identity Baseline
    record_model(
        "M0_Identity_Baseline",
        "baseline",
        score_b_all[idx_val].astype(float),
        np.ones(len(idx_val), dtype=int),
        score_b_all[idx_test].astype(float),
        np.ones(len(idx_test), dtype=int),
        "Predicts score_B and unchanged",
    )

    # 2. M1 Metadata-Only Models
    scaler_m = StandardScaler()
    Xm_tr = scaler_m.fit_transform(X_meta_all[idx_train])
    Xm_va = scaler_m.transform(X_meta_all[idx_val])
    Xm_te = scaler_m.transform(X_meta_all[idx_test])
    Xm_fg = scaler_m.transform(X_meta_all[idx_first_grade])

    m1a_reg = Ridge(alpha=1.0, random_state=SEED).fit(Xm_tr, y_rank_all[idx_train])
    m1a_cls = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=SEED).fit(Xm_tr, y_shift_all[idx_train])
    record_model(
        "M1a_Meta_Linear",
        "metadata_only",
        np.clip(m1a_reg.predict(Xm_va), 1, 12),
        m1a_cls.predict(Xm_va),
        np.clip(m1a_reg.predict(Xm_te), 1, 12),
        m1a_cls.predict(Xm_te),
        "X_meta only (Ridge + Balanced LogReg)",
        fg_cont=np.clip(m1a_reg.predict(Xm_fg), 1, 12),
    )

    m1b_reg = HistGradientBoostingRegressor(max_iter=250, learning_rate=0.05, random_state=SEED).fit(X_meta_all[idx_train], y_rank_all[idx_train])
    m1b_cls = HistGradientBoostingClassifier(max_iter=250, learning_rate=0.05, class_weight="balanced", random_state=SEED).fit(X_meta_all[idx_train], y_shift_all[idx_train])
    record_model(
        "M1b_Meta_HistGBDT",
        "metadata_only",
        np.clip(m1b_reg.predict(X_meta_all[idx_val]), 1, 12),
        m1b_cls.predict(X_meta_all[idx_val]),
        np.clip(m1b_reg.predict(X_meta_all[idx_test]), 1, 12),
        m1b_cls.predict(X_meta_all[idx_test]),
        "X_meta only (HistGBDT)",
        fg_cont=np.clip(m1b_reg.predict(X_meta_all[idx_first_grade]), 1, 12),
    )

    m1c_reg = RandomForestRegressor(n_estimators=200, min_samples_leaf=3, random_state=SEED, n_jobs=-1).fit(X_meta_all[idx_train], y_rank_all[idx_train])
    m1c_cls = RandomForestClassifier(n_estimators=200, min_samples_leaf=3, class_weight="balanced_subsample", random_state=SEED, n_jobs=-1).fit(X_meta_all[idx_train], y_shift_all[idx_train])
    record_model(
        "M1c_Meta_RandomForest",
        "metadata_only",
        np.clip(m1c_reg.predict(X_meta_all[idx_val]), 1, 12),
        m1c_cls.predict(X_meta_all[idx_val]),
        np.clip(m1c_reg.predict(X_meta_all[idx_test]), 1, 12),
        m1c_cls.predict(X_meta_all[idx_test]),
        "X_meta only (RandomForest)",
        fg_cont=np.clip(m1c_reg.predict(X_meta_all[idx_first_grade]), 1, 12),
    )

    # 3. M2 Classical TF-IDF + Metadata
    from scipy.sparse import csr_matrix, hstack

    def fit_tfidf_linear(text_list: list[str]):
        vec = FeatureUnion(
            [
                ("word", TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=20000, sublinear_tf=True)),
                ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=3, max_features=25000, sublinear_tf=True)),
            ]
        )
        X_txt_tr = vec.fit_transform([text_list[i] for i in idx_train])
        X_txt_va = vec.transform([text_list[i] for i in idx_val])
        X_txt_te = vec.transform([text_list[i] for i in idx_test])
        X_txt_fg = vec.transform([text_list[i] for i in idx_first_grade])

        Xtr = hstack([X_txt_tr, csr_matrix(Xm_tr)])
        Xva = hstack([X_txt_va, csr_matrix(Xm_va)])
        Xte = hstack([X_txt_te, csr_matrix(Xm_te)])
        Xfg = hstack([X_txt_fg, csr_matrix(Xm_fg)])

        reg = Ridge(alpha=3.0, random_state=SEED).fit(Xtr, y_rank_all[idx_train])
        cls = LogisticRegression(C=1.5, max_iter=1000, class_weight="balanced", random_state=SEED).fit(Xtr, y_shift_all[idx_train])
        return reg, cls, X_txt_tr, X_txt_va, X_txt_te, X_txt_fg, Xva, Xte, Xfg

    reg_f, cls_f, Xtxt_tr_f, Xtxt_va_f, Xtxt_te_f, Xtxt_fg_f, Xva_f, Xte_f, Xfg_f = fit_tfidf_linear(texts_full)
    record_model(
        "M2a_TFIDF_Full_Linear",
        "tfidf_plus_meta",
        np.clip(reg_f.predict(Xva_f), 1, 12),
        cls_f.predict(Xva_f),
        np.clip(reg_f.predict(Xte_f), 1, 12),
        cls_f.predict(Xte_f),
        "Word(1-2)+Char(3-5) TF-IDF + X_meta (Ridge + LogReg)",
        fg_cont=np.clip(reg_f.predict(Xfg_f), 1, 12),
    )

    svd = TruncatedSVD(n_components=64, random_state=SEED)
    Ztr_f = np.hstack([svd.fit_transform(Xtxt_tr_f), X_meta_all[idx_train]])
    Zva_f = np.hstack([svd.transform(Xtxt_va_f), X_meta_all[idx_val]])
    Zte_f = np.hstack([svd.transform(Xtxt_te_f), X_meta_all[idx_test]])
    Zfg_f = np.hstack([svd.transform(Xtxt_fg_f), X_meta_all[idx_first_grade]])
    m2b_reg = HistGradientBoostingRegressor(max_iter=250, learning_rate=0.05, random_state=SEED).fit(Ztr_f, y_rank_all[idx_train])
    m2b_cls = HistGradientBoostingClassifier(max_iter=250, learning_rate=0.05, class_weight="balanced", random_state=SEED).fit(Ztr_f, y_shift_all[idx_train])
    record_model(
        "M2b_TFIDF_Full_HistGBDT",
        "tfidf_plus_meta",
        np.clip(m2b_reg.predict(Zva_f), 1, 12),
        m2b_cls.predict(Zva_f),
        np.clip(m2b_reg.predict(Zte_f), 1, 12),
        m2b_cls.predict(Zte_f),
        "SVD-64 TF-IDF + X_meta (HistGBDT)",
        fg_cont=np.clip(m2b_reg.predict(Zfg_f), 1, 12),
    )

    reg_ns, cls_ns, _, _, _, _, Xva_ns, Xte_ns, Xfg_ns = fit_tfidf_linear(texts_stripped)
    record_model(
        "M2c_TFIDF_NameStripped_Linear",
        "name_stripped_ablation",
        np.clip(reg_ns.predict(Xva_ns), 1, 12),
        cls_ns.predict(Xva_ns),
        np.clip(reg_ns.predict(Xte_ns), 1, 12),
        cls_ns.predict(Xte_ns),
        "Name-stripped TF-IDF + X_meta",
        fg_cont=np.clip(reg_ns.predict(Xfg_ns), 1, 12),
    )

    # 4. M3a CAMeLBERT Zero-Shot Generic-Sentiment Baseline + Meta
    camel_cache = ckpt_dir / "camelbert_feats.npy"
    if args.resume and camel_cache.exists():
        print("Loaded cached CAMeLBERT generic-sentiment features:", camel_cache)
        camel_feats = np.load(camel_cache)
    else:
        print("Running generic-sentiment baseline (CAMeLBERT) inference on 8,827 entries...")
        camel_bs = 32 if device.type == "mps" else 64
        camel_feats = extract_camelbert_zero_shot(
            texts_full, batch_size=camel_bs, local_files_only=local_only, device=device
        )
        np.save(camel_cache, camel_feats)
    Xcm_tr = np.hstack([X_meta_all[idx_train], camel_feats[idx_train]])
    Xcm_va = np.hstack([X_meta_all[idx_val], camel_feats[idx_val]])
    Xcm_te = np.hstack([X_meta_all[idx_test], camel_feats[idx_test]])
    Xcm_fg = np.hstack([X_meta_all[idx_first_grade], camel_feats[idx_first_grade]])
    m3a_reg = HistGradientBoostingRegressor(max_iter=250, learning_rate=0.05, random_state=SEED).fit(Xcm_tr, y_rank_all[idx_train])
    m3a_cls = HistGradientBoostingClassifier(max_iter=250, learning_rate=0.05, class_weight="balanced", random_state=SEED).fit(Xcm_tr, y_shift_all[idx_train])
    record_model(
        "M3a_CAMeLBERT_Sentiment_Plus_Meta",
        "generic_sentiment_baseline",
        np.clip(m3a_reg.predict(Xcm_va), 1, 12),
        m3a_cls.predict(Xcm_va),
        np.clip(m3a_reg.predict(Xcm_te), 1, 12),
        m3a_cls.predict(Xcm_te),
        "Generic-sentiment baseline: zero-shot CAMeLBERT-MSA-sentiment + X_meta (HistGBDT)",
        fg_cont=np.clip(m3a_reg.predict(Xcm_fg), 1, 12),
    )

    # 5. M3b AraBERTv02 Full Dual-Head & 5-Fold OOF inside clean train
    skf_strata = [f"{y_rank_all[i]}_{y_shift_all[i]}" for i in idx_train]
    cnt_str = Counter(skf_strata)
    skf_labels = [
        skf_strata[k] if cnt_str[skf_strata[k]] >= 5 else str(y_rank_all[idx_train[k]])
        for k in range(len(idx_train))
    ]
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)

    train_set = set(idx_train.tolist())
    idx_non_train = np.array([i for i in range(len(all_rows)) if i not in train_set], dtype=int)

    m2_oof_rank = np.zeros(len(all_rows), dtype=np.float32)
    m2_oof_sprobs = np.zeros((len(all_rows), 3), dtype=np.float32)
    for _fold_id, (f_tr_rel, f_va_rel) in enumerate(skf.split(idx_train, skf_labels)):
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
        cl_k = LogisticRegression(C=1.5, max_iter=1000, class_weight="balanced", random_state=SEED).fit(Xt_tr, y_shift_all[f_tr])
        m2_oof_rank[f_va] = np.clip(rk_k.predict(Xt_va), 1, 12)
        m2_oof_sprobs[f_va] = cl_k.predict_proba(Xt_va)
        m2_oof_rank[idx_non_train] += np.clip(rk_k.predict(Xt_nt), 1, 12) / 5.0
        m2_oof_sprobs[idx_non_train] += cl_k.predict_proba(Xt_nt) / 5.0

    arabert_oof_rank_exp = np.zeros(len(all_rows), dtype=np.float32)
    arabert_oof_rprobs = np.zeros((len(all_rows), 12), dtype=np.float32)
    arabert_oof_sprobs = np.zeros((len(all_rows), 3), dtype=np.float32)
    arabert_oof_cls = np.zeros((len(all_rows), 768), dtype=np.float32)
    fold_epochs = []

    for fold_id, (f_tr_rel, f_va_rel) in enumerate(skf.split(idx_train, skf_labels)):
        f_tr = idx_train[f_tr_rel]
        f_va = idx_train[f_va_rel]
        fold_ckpt = ckpt_dir / f"m3b_fold_{fold_id}.npz"
        if args.resume and fold_ckpt.exists():
            print(f"  Loaded cached AraBERTv02 ESA Fold {fold_id + 1}/5 from {fold_ckpt.name}")
            z = np.load(fold_ckpt)
            fold_epochs.append(int(z["best_epoch"]))
            arabert_oof_rank_exp[f_va] = z["va_rank_exp"]
            arabert_oof_rprobs[f_va] = z["va_rank_probs"]
            arabert_oof_sprobs[f_va] = z["va_shift_probs"]
            arabert_oof_cls[f_va] = z["va_cls"]
            arabert_oof_rank_exp[idx_non_train] += z["nt_rank_exp"] / 5.0
            arabert_oof_rprobs[idx_non_train] += z["nt_rank_probs"] / 5.0
            arabert_oof_sprobs[idx_non_train] += z["nt_shift_probs"] / 5.0
            arabert_oof_cls[idx_non_train] += z["nt_cls"] / 5.0
            continue

        print(f"  Training AraBERTv02 ESA Fold {fold_id + 1}/5 (tr={len(f_tr)}, fold_val={len(f_va)})...")
        eval_b = {
            "fold_val": ([texts_full[i] for i in f_va], X_meta_all[f_va]),
            "non_train": ([texts_full[i] for i in idx_non_train], X_meta_all[idx_non_train]),
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
            epochs=args.epochs,
            batch_size=batch_size,
            grad_accum=grad_accum,
            max_length=args.max_length,
            seed=SEED + fold_id,
            local_files_only=local_only,
            device=device,
        )
        fold_epochs.append(info["best_epoch"])
        arabert_oof_rank_exp[f_va] = outs["fold_val"]["rank_exp"]
        arabert_oof_rprobs[f_va] = outs["fold_val"]["rank_probs"]
        arabert_oof_sprobs[f_va] = outs["fold_val"]["shift_probs"]
        arabert_oof_cls[f_va] = outs["fold_val"]["cls"]

        arabert_oof_rank_exp[idx_non_train] += outs["non_train"]["rank_exp"] / 5.0
        arabert_oof_rprobs[idx_non_train] += outs["non_train"]["rank_probs"] / 5.0
        arabert_oof_sprobs[idx_non_train] += outs["non_train"]["shift_probs"] / 5.0
        arabert_oof_cls[idx_non_train] += outs["non_train"]["cls"] / 5.0
        np.savez(
            fold_ckpt,
            best_epoch=np.array(info["best_epoch"]),
            va_rank_exp=outs["fold_val"]["rank_exp"],
            va_rank_probs=outs["fold_val"]["rank_probs"],
            va_shift_probs=outs["fold_val"]["shift_probs"],
            va_cls=outs["fold_val"]["cls"],
            nt_rank_exp=outs["non_train"]["rank_exp"],
            nt_rank_probs=outs["non_train"]["rank_probs"],
            nt_shift_probs=outs["non_train"]["shift_probs"],
            nt_cls=outs["non_train"]["cls"],
        )

    record_model(
        "M3b_AraBERTv02_Full_DualHead",
        "esa_arabic_transformer",
        arabert_oof_rank_exp[idx_val],
        arabert_oof_sprobs[idx_val].argmax(axis=1),
        arabert_oof_rank_exp[idx_test],
        arabert_oof_sprobs[idx_test].argmax(axis=1),
        f"5-fold train-ensemble Dual-Head AraBERTv02 ESA + X_meta (best epochs: {fold_epochs})",
        fg_cont=arabert_oof_rank_exp[idx_first_grade],
    )

    # 6. M3c AraBERTv02 Name-Stripped ESA Ablation
    m3c_ckpt = ckpt_dir / "m3c_stripped.npz"
    if args.resume and m3c_ckpt.exists():
        print(f"Loaded cached AraBERTv02 Name-Stripped from {m3c_ckpt.name}")
        zns = np.load(m3c_ckpt)
        info_ns = {"best_epoch": int(zns["best_epoch"])}
        outs_ns = {
            "val": {"rank_exp": zns["val_rank_exp"], "shift_probs": zns["val_shift_probs"]},
            "test": {"rank_exp": zns["test_rank_exp"], "shift_probs": zns["test_shift_probs"]},
            "fg": {"rank_exp": zns["fg_rank_exp"]},
        }
    else:
        print("Training AraBERTv02 Name-Stripped ESA Dual-Head...")
        outs_ns, info_ns = train_and_eval_arabert(
            [texts_stripped[i] for i in idx_train],
            X_meta_all[idx_train],
            y_rank_all[idx_train],
            y_shift_all[idx_train],
            {
                "val": ([texts_stripped[i] for i in idx_val], X_meta_all[idx_val]),
                "test": ([texts_stripped[i] for i in idx_test], X_meta_all[idx_test]),
                "fg": ([texts_stripped[i] for i in idx_first_grade], X_meta_all[idx_first_grade]),
            },
            val_key="val",
            val_rank=y_rank_all[idx_val],
            val_shift=y_shift_all[idx_val],
            val_is_maqbul=is_maqbul_all[idx_val],
            epochs=args.epochs,
            batch_size=batch_size,
            grad_accum=grad_accum,
            max_length=args.max_length,
            seed=SEED,
            local_files_only=local_only,
            device=device,
        )
        np.savez(
            m3c_ckpt,
            best_epoch=np.array(info_ns["best_epoch"]),
            val_rank_exp=outs_ns["val"]["rank_exp"],
            val_shift_probs=outs_ns["val"]["shift_probs"],
            test_rank_exp=outs_ns["test"]["rank_exp"],
            test_shift_probs=outs_ns["test"]["shift_probs"],
            fg_rank_exp=outs_ns["fg"]["rank_exp"],
        )
    record_model(
        "M3c_AraBERTv02_NameStripped_DualHead",
        "name_stripped_ablation",
        outs_ns["val"]["rank_exp"],
        outs_ns["val"]["shift_probs"].argmax(axis=1),
        outs_ns["test"]["rank_exp"],
        outs_ns["test"]["shift_probs"].argmax(axis=1),
        f"Name-stripped AraBERTv02 ESA + X_meta (best ep={info_ns['best_epoch']})",
        fg_cont=outs_ns["fg"]["rank_exp"],
    )

    # Fit 32-dim PCA strictly on clean train CLS embeddings
    pca = PCA(n_components=32, random_state=SEED)
    pca.fit(arabert_oof_cls[idx_train])
    cls_pca32 = pca.transform(arabert_oof_cls).astype(np.float32)

    oof_csv = out_dir / "STAGE2_OOF_ESA_FEATURES_8827_V3.csv"
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
        w = csv.writer(f, lineterminator="\n")
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

    comp_csv = out_dir / "STAGE2_MODEL_COMPARISON_V3.csv"
    with comp_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(comparison_rows[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(comparison_rows)

    fg_csv = out_dir / "STAGE2_ABSTAINED_FIRST_GRADE_SLICE_V3.csv"
    with fg_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(first_grade_rows[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(first_grade_rows)

    pred_csv = out_dir / "STAGE2_TEST_PREDICTIONS_V3.csv"
    pred_fields = ["entry_id", "score_B_rank_1_to_12", "score_E2_rank_1_to_12", "shift_class", "taqrib_is_conditional_maqbul"]
    for m_name in test_preds:
        pred_fields.extend([f"{m_name}_rank_pred", f"{m_name}_shift_pred"])
    with pred_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=pred_fields, lineterminator="\n")
        w.writeheader()
        for k, gi in enumerate(idx_test):
            r = all_rows[gi]
            row_d = {
                "entry_id": r["entry_id"],
                "score_B_rank_1_to_12": int(score_b_all[gi]),
                "score_E2_rank_1_to_12": int(y_rank_all[gi]),
                "shift_class": SHIFT_LABELS[int(y_shift_all[gi])],
                "taqrib_is_conditional_maqbul": r["taqrib_is_conditional_maqbul"],
            }
            for m_name, (rc, sp) in test_preds.items():
                row_d[f"{m_name}_rank_pred"] = f"{rc[k]:.4f}"
                row_d[f"{m_name}_shift_pred"] = SHIFT_LABELS[int(sp[k])]
            w.writerow(row_d)

    per_cls_rows = []
    for m_name in [
        "M0_Identity_Baseline",
        "M1b_Meta_HistGBDT",
        "M2a_TFIDF_Full_Linear",
        "M3b_AraBERTv02_Full_DualHead",
        "M3c_AraBERTv02_NameStripped_DualHead",
    ]:
        rc, sp = test_preds[m_name]
        r_disc = np.clip(np.rint(rc), 1, 12).astype(int)
        p, rec, f1, sup = precision_recall_fscore_support(y_rank_all[idx_test], r_disc, labels=list(range(1, 13)), zero_division=0)
        for idx_r in range(12):
            per_cls_rows.append({"model": m_name, "task": "rank_1_to_12", "class_label": str(idx_r + 1), "precision": round(float(p[idx_r]), 4), "recall": round(float(rec[idx_r]), 4), "f1": round(float(f1[idx_r]), 4), "support": int(sup[idx_r])})
        ps, recs, f1s, sups = precision_recall_fscore_support(y_shift_all[idx_test], sp, labels=[0, 1, 2], zero_division=0)
        for idx_s in range(3):
            per_cls_rows.append({"model": m_name, "task": "shift_3class", "class_label": SHIFT_LABELS[idx_s], "precision": round(float(ps[idx_s]), 4), "recall": round(float(recs[idx_s]), 4), "f1": round(float(f1s[idx_s]), 4), "support": int(sups[idx_s])})

    per_cls_csv = out_dir / "STAGE2_PER_RANK_AND_SHIFT_METRICS_V3.csv"
    with per_cls_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(per_cls_rows[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(per_cls_rows)

    test_rows = [r for r in comparison_rows if r["split"] == "test"]
    dev_label = (
        "CUDA (" + torch.cuda.get_device_name(0) + ")"
        if device.type == "cuda"
        else ("MPS (AMD Radeon / Apple Metal)" if device.type == "mps" else "CPU")
    )
    md_lines = [
        "# Stage 2: Evaluative Stance Analysis (ESA) Benchmark Report (v3)",
        "",
        f"- **Generated (UTC):** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%SZ')}",
        f"- **Elapsed:** {time.time() - t0:.1f}s | **Device:** {dev_label}",
        f"- **Clean Cohort (excluding `missing` + `suspect_alignment`):** `train = {len(idx_train)}`, `val = {len(idx_val)}`, `test = {len(idx_test)}`.",
        f"- **Taqrīb Abstained / Taḥrīr Graded (`observed_first_grade`) Slice:** `N = {len(idx_first_grade)}`.",
        "",
        "## 1. Test Split Benchmark Table",
        "",
        "| Model | Family | Rank MAE ↓ | QWK ↑ | Exact Acc ↑ | Bin Acc ↑ | 3-Tier MF1 ↑ | Shift MF1 ↑ | Active MF1 ↑ | R6 MAE ↓ |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in test_rows:
        md_lines.append(
            f"| `{r['model']}` | `{r['family']}` | {r['rank_mae']:.4f} | {r['rank_qwk']:.4f} | {r['rank_exact_acc']:.4f} | "
            f"{r['bin_acc']:.4f} | {r['tier3_macro_f1']:.4f} | {r['shift_macro_f1']:.4f} | {r['shift_active_macro_f1']:.4f} | {r['r6_rank_mae']:.4f} |"
        )
    md_lines.extend(
        [
            "",
            "## 2. Taqrīb Abstained / Taḥrīr Graded Slice (`observed_first_grade`)",
            "",
            "| Model | N | Rank MAE ↓ | QWK ↑ | Exact Acc ↑ | Bin Acc ↑ | 3-Tier MF1 ↑ |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for fr in first_grade_rows:
        md_lines.append(
            f"| `{fr['model']}` | {fr['n']} | {fr['rank_mae']:.4f} | {fr['rank_qwk']:.4f} | {fr['rank_exact_acc']:.4f} | {fr['bin_acc']:.4f} | {fr['tier3_macro_f1']:.4f} |"
        )
    report_md = out_dir / "STAGE2_RESULTS_SUMMARY_V3.md"
    report_md.write_bytes(("\n".join(md_lines) + "\n").encode("utf-8"))

    manifest_files = [comp_csv, per_cls_csv, fg_csv, pred_csv, oof_csv, report_md]
    manifest = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "script": to_posix_relative(Path(__file__), ROOT),
        "elapsed_sec": round(time.time() - t0, 2),
        "inputs": {
            "layer_rules_v3.json": {"path": to_posix_relative(LAYER_RULES, ROOT), "sha256": sha256_text_normalized(LAYER_RULES)},
            "LAYERED_SCORES_WIDE_V3.csv": {"path": to_posix_relative(LAYERED_WIDE, ROOT), "sha256": sha256_text_normalized(LAYERED_WIDE)},
            "TAQRIB_V2_MASTER_NODES_8827.csv": {"path": to_posix_relative(MASTER_NODES, ROOT), "sha256": sha256_text_normalized(MASTER_NODES)},
        },
        "clean_split_counts": {"train": int(len(idx_train)), "val": int(len(idx_val)), "test": int(len(idx_test)), "observed_first_grade": int(len(idx_first_grade))},
        "test_summary": test_rows,
        "files": {p.name: {"sha256": sha256_text_normalized(p), "bytes": p.stat().st_size} for p in manifest_files},
    }
    manifest_json = out_dir / "MANIFEST.json"
    manifest_json.write_bytes((json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    (out_dir / "MANIFEST.sha256").write_bytes(
        ("\n".join(f"{sha256_text_normalized(p)}  {p.name}" for p in [*manifest_files, manifest_json]) + "\n").encode("ascii")
    )
    print("Stage 2 v3 complete in", round(time.time() - t0, 1), "s ->", out_dir)


if __name__ == "__main__":
    main()
