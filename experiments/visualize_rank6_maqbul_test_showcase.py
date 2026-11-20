#!/usr/bin/env python3
"""Generate Rank 6 (Maqbul) Held-Out [TEST] Showcase & Visualizations (0-100 Reliability Scale).

Demonstrates how Stage 3 TC-GNN resolves Ibn Hajar's flat conditional Rank 6 ('Maqbul' = 54.55)
into calibrated Ta'dil vs. Jarh scores across N = 229 unseen held-out test narrators.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


ROOT = Path(__file__).resolve().parents[1]
MASTER_CSV = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline/taqrib_v2_master_dataset_2026-11-20/TAQRIB_V2_MASTER_NODES_8827.csv"
FINAL_CSV = ROOT / "results/stage3_tc_gnn_benchmarks_v2_2026-11-20/FINAL_TWO_SCORE_RIJAL_REPRESENTATION_8827.csv"
TEST_PREDS_CSV = ROOT / "results/stage3_tc_gnn_benchmarks_v2_2026-11-20/STAGE3_TEST_PREDICTIONS_V2.csv"
OUT_DIR = ROOT / "results/stage3_tc_gnn_benchmarks_v2_2026-11-20/rank6_maqbul_showcase"

DIACRITICS_RE = re.compile(r"[\u064b-\u065f\u0670\u0640]")
LEAD_NUM_RE = re.compile(r"^[٠-٩0-9]+\s*[-–]\s*")

AR_CHAR_MAP = {
    "ا": "a", "أ": "a", "إ": "i", "آ": "a", "ب": "b", "ت": "t", "ث": "th",
    "ج": "j", "ح": "h", "خ": "kh", "د": "d", "ذ": "dh", "ر": "r", "ز": "z",
    "س": "s", "ش": "sh", "ص": "s", "ض": "d", "ط": "t", "ظ": "z", "ع": "'",
    "غ": "gh", "ف": "f", "ق": "q", "ك": "k", "ل": "l", "م": "m", "ن": "n",
    "ه": "h", "ة": "h", "و": "w", "ي": "y", "ى": "a", "ئ": "'", "ؤ": "'", "ء": "'",
}

SPECIAL_WORDS = {
    "عبد": "Abd", "الله": "Allah", "الرحمن": "al-Rahman", "أبو": "Abu", "أبي": "Abi",
    "ابن": "b.", "بن": "b.", "بنت": "bt.", "أم": "Umm", "مولى": "mawla", "مولاة": "mawlat",
    "محمد": "Muhammad", "أحمد": "Ahmad", "إبراهيم": "Ibrahim", "إسماعيل": "Isma'il",
    "إسحاق": "Ishaq", "يعقوب": "Ya'qub", "يوسف": "Yusuf", "يحيى": "Yahya",
    "عيسى": "Isa", "موسى": "Musa", "علي": "Ali", "عمر": "Umar", "عثمان": "Uthman",
    "سعيد": "Sa'id", "سعد": "Sa'd", "زيد": "Zayd", "عمرو": "Amr", "سليمان": "Sulayman",
    "داود": "Dawud", "الحسن": "al-Hasan", "الحسين": "al-Husayn", "ميمون": "Maymun",
    "الأصبغ": "al-Asbagh", "يزيد": "Yazid", "عبيد": "Ubayd", "عباد": "Abbad",
    "خالد": "Khalid", "صالح": "Salih", "بكر": "Bakr", "مالك": "Malik",
}


def transliterate_short_name(verbatim: str, eid_short: str, max_words: int = 4) -> str:
    txt = LEAD_NUM_RE.sub("", DIACRITICS_RE.sub("", verbatim)).strip()
    # Strip editorial brackets & stop before grade/tabaqa keywords
    txt = re.sub(r"\[[^\]]*\]", "", txt)
    raw_words = txt.split()
    kept = []
    for w in raw_words:
        if w in ("مقبول", "مقبولة", "من", "عن", "غير", "بفتح", "بضم", "بكسر", "بسكون", "بالتصغير", "بموحدة", "بمهملة", "بمعجمة"):
            break
        kept.append(w)
        if len(kept) >= max_words:
            break
    if not kept:
        kept = raw_words[:3]

    out_words = []
    for w in kept:
        clean = w.strip("،.:؛()")
        if not clean:
            continue
        if clean in SPECIAL_WORDS:
            out_words.append(SPECIAL_WORDS[clean])
        elif clean.startswith("ال") and len(clean) > 2:
            rest = "".join(AR_CHAR_MAP.get(c, c) for c in clean[2:])
            out_words.append("al-" + rest.capitalize())
        else:
            tr = "".join(AR_CHAR_MAP.get(c, c) for c in clean)
            out_words.append(tr.capitalize() if not tr.startswith("'") else tr)
    label = " ".join(out_words)
    if len(label) > 26:
        label = label[:24].rstrip() + ".."
    return f"{eid_short}: {label}"


def rank_to_100(r_val: float) -> float:
    return 100.0 * (12.0 - r_val) / 11.0


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="notebook")

    with MASTER_CSV.open(encoding="utf-8-sig") as f:
        nodes_by_id = {r["entry_id"]: r for r in csv.DictReader(f)}
    with TEST_PREDS_CSV.open(encoding="utf-8-sig") as f:
        g0_by_id = {r["entry_id"]: r for r in csv.DictReader(f)}
    with FINAL_CSV.open(encoding="utf-8-sig") as f:
        r6_rows = [
            r for r in csv.DictReader(f)
            if r["split"] == "test" and r["taqrib_is_conditional_maqbul"] == "True"
        ]

    assert len(r6_rows) == 229, f"Expected 229 Rank 6 test entries, got {len(r6_rows)}"

    out_records: list[dict[str, Any]] = []
    for r in r6_rows:
        eid = r["entry_id"]
        n = nodes_by_id[eid]
        g0 = g0_by_id[eid]
        g0_rank = float(g0["G0_Stage2_AraBERT_NoGraph_rank_pred"])
        g0_100 = rank_to_100(g0_rank)
        tah_rank = int(r["tahrir_scholar_rank_1_to_12"])
        tah_100 = float(r["tahrir_reliability_0_100"])
        s2_rank_cont = float(r["score2_tc_gnn_continuous"])
        s2_rank_disc = int(r["score2_tc_gnn_rank_1_to_12"])
        s2_100 = float(r["score2_reliability_0_100"])
        s1_100 = float(r["score1_reliability_0_100"])

        if tah_rank < 6:
            outcome = "Upgraded (R3–5)"
        elif tah_rank == 6:
            outcome = "Kept (R6)"
        elif tah_rank == 7:
            outcome = "Downgraded (R7)"
        else:
            outcome = "Downgraded (R8+)"

        out_records.append({
            "entry_id": eid,
            "short_label": transliterate_short_name(n["taqrib_text_verbatim"], eid.split("-")[-1]),
            "taqrib_text_verbatim": n["taqrib_text_verbatim"],
            "sigil_tokens_raw": n["sigil_tokens_raw"],
            "tabaqa_1_to_12": n["tabaqa_1_to_12"],
            "tc_sanad_out_degree": int(r["tc_sanad_out_degree"]),
            "tc_sanad_in_degree": int(r["tc_sanad_in_degree"]),
            "score1_reliability_0_100": round(s1_100, 2),
            "tahrir_scholar_rank_1_to_12": tah_rank,
            "tahrir_reliability_0_100": round(tah_100, 2),
            "tahrir_outcome_group": outcome,
            "g0_arabert_reliability_0_100": round(g0_100, 2),
            "g0_arabert_rank_cont": round(g0_rank, 4),
            "score2_tc_gnn_reliability_0_100": round(s2_100, 2),
            "score2_tc_gnn_continuous": round(s2_rank_cont, 4),
            "score2_tc_gnn_rank_1_to_12": s2_rank_disc,
            "score2_predicted_shift": r["score2_predicted_shift"],
            "score2_rank_entropy": float(r["score2_rank_entropy"]),
        })

    out_records.sort(key=lambda x: (-x["score2_tc_gnn_reliability_0_100"], x["entry_id"]))
    csv_path = OUT_DIR / "RANK6_MAQBUL_TEST_229.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out_records[0].keys()))
        w.writeheader()
        w.writerows(out_records)

    # Metrics across N = 229 unseen Maqbul
    y_rank = np.array([r["tahrir_scholar_rank_1_to_12"] for r in out_records])
    y_100 = np.array([r["tahrir_reliability_0_100"] for r in out_records])
    y_bin = (y_rank <= 6).astype(int)

    s1_rank = np.full(len(out_records), 6.0)
    s1_100 = np.array([r["score1_reliability_0_100"] for r in out_records])
    s1_bin = np.ones(len(out_records), dtype=int)

    g0_rank = np.array([r["g0_arabert_rank_cont"] for r in out_records])
    g0_100 = np.array([r["g0_arabert_reliability_0_100"] for r in out_records])
    g0_bin = (np.clip(np.rint(g0_rank), 1, 12) <= 6).astype(int)

    s2_rank = np.array([r["score2_tc_gnn_continuous"] for r in out_records])
    s2_100 = np.array([r["score2_tc_gnn_reliability_0_100"] for r in out_records])
    s2_bin = (np.array([r["score2_tc_gnn_rank_1_to_12"] for r in out_records]) <= 6).astype(int)

    def eval_arr(rk_hat: np.ndarray, sc_hat: np.ndarray, bn_hat: np.ndarray) -> tuple[float, float, float]:
        return (
            float(np.mean(np.abs(y_rank - rk_hat))),
            float(np.mean(np.abs(y_100 - sc_hat))),
            float(np.mean(y_bin == bn_hat)),
        )

    m_s1 = eval_arr(s1_rank, s1_100, s1_bin)
    m_g0 = eval_arr(g0_rank, g0_100, g0_bin)
    m_s2 = eval_arr(s2_rank, s2_100, s2_bin)

    # Figure: 2-panel visualization
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15.5, 7.6), gridspec_kw={"width_ratios": [1.0, 1.25], "wspace": 0.34})

    # Panel A: Distribution of Score 2 across the 229 unseen Maqbul outcomes
    order = ["Upgraded (R3–5)", "Kept (R6)", "Downgraded (R7)", "Downgraded (R8+)"]
    pal = {"Upgraded (R3–5)": "#2e7d32", "Kept (R6)": "#1f77b4", "Downgraded (R7)": "#f57c00", "Downgraded (R8+)": "#c62828"}
    grouped_vals = [[r["score2_tc_gnn_reliability_0_100"] for r in out_records if r["tahrir_outcome_group"] == o] for o in order]

    sns.boxplot(data=grouped_vals, ax=ax1, width=0.48, palette=[pal[o] for o in order], showfliers=False)
    sns.stripplot(data=grouped_vals, ax=ax1, color="#1a202c", size=3.8, alpha=0.55, jitter=0.18)
    ax1.axhline(54.55, color="#1f77b4", linestyle="--", linewidth=1.4, label="Score 1 Flat Baseline (54.55)")
    ax1.axhline(50.00, color="#444444", linestyle=":", linewidth=1.3, label="Ta'dil / Jarh Boundary (50.00)")

    for i, vals in enumerate(grouped_vals):
        ax1.text(i, max(vals) + 1.8, f"n={len(vals)}\nmean={np.mean(vals):.1f}", ha="center", va="bottom", fontsize=8.5, fontweight="bold")

    ax1.set_xticks([0, 1, 2, 3])
    ax1.set_xticklabels(["Upgraded\n(R3–5)", "Kept\n(R6)", "Downgraded\n(R7)", "Downgraded\n(R8+)"], fontsize=9.5)
    ax1.set_ylim(24, 80)
    ax1.set_ylabel("Score 2: TC-GNN Reliability Score (0–100)", fontsize=10.5, fontweight="bold")
    ax1.set_title("A. Unseen [TEST] Maqbūl Resolution (N = 229)", fontsize=11.5, fontweight="bold")
    ax1.legend(loc="lower left", fontsize=8.5, frameon=True)

    # Panel B: Spotlight Top 10 Upgraded vs Top 10 Downgraded unseen [TEST] Maqbul
    top_up = sorted(
        [r for r in out_records if r["tahrir_scholar_rank_1_to_12"] < 6],
        key=lambda x: -x["score2_tc_gnn_reliability_0_100"],
    )[:10]
    top_dn = sorted(
        [r for r in out_records if r["tahrir_scholar_rank_1_to_12"] >= 7],
        key=lambda x: x["score2_tc_gnn_reliability_0_100"],
    )[:10]
    spotlight = top_up + list(reversed(top_dn))  # top half = upgraded, bottom half = downgraded

    y_pos = np.arange(len(spotlight))
    ax2.axvspan(20, 50.0, color="#ffebee", alpha=0.45, zorder=0)
    ax2.axvspan(50.0, 88, color="#e8f5e9", alpha=0.45, zorder=0)
    ax2.axvline(54.55, color="#1f77b4", linestyle="--", linewidth=1.4, zorder=2, label="Score 1: Maqbūl Baseline (54.55)")
    ax2.axvline(50.00, color="#555555", linestyle=":", linewidth=1.2, zorder=2, label="Ta'dil / Jarh Boundary (50.00)")
    ax2.axhline(9.5, color="#888888", linestyle="-", linewidth=0.9, alpha=0.7)

    ylabels = []
    for idx, r in enumerate(reversed(spotlight)):
        s1 = 54.55
        s2 = r["score2_tc_gnn_reliability_0_100"]
        th = r["tahrir_reliability_0_100"]
        col = "#2e7d32" if s2 >= s1 else "#c62828"
        ax2.plot([s1, s2], [idx, idx], color=col, linewidth=2.4, alpha=0.85, zorder=3)
        ax2.scatter(th, idx, s=55, marker="D", color="#222222", alpha=0.75, zorder=4)
        ax2.scatter(s2, idx, s=75, color=col, edgecolor="white", linewidth=0.8, zorder=5)
        ylabels.append(r["short_label"])
        ax2.text(85.2, idx, f"out={r['tc_sanad_out_degree']}", va="center", ha="left", fontsize=8.0, color="#4a5568")

    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(ylabels, fontsize=8.3)
    ax2.set_xlim(22, 92.5)
    ax2.set_ylim(-0.6, len(spotlight) - 0.4)
    ax2.set_xlabel("Quantified Reliability Score (0–100)", fontsize=10.5, fontweight="bold")
    ax2.set_title("B. Diverging Shifts from Flat 54.55 (Top 10 Up vs. Top 10 Down)", fontsize=11.5, fontweight="bold")

    handles2 = [
        plt.Line2D([0], [0], color="#1f77b4", linestyle="--", lw=1.4, label="Score 1 Baseline (54.55)"),
        plt.Line2D([0], [0], marker="D", color="w", markerfacecolor="#222222", markersize=6.5, label="Taḥrīr Scholar Verdict"),
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor="#2e7d32", markersize=7.5, label="Score 2 Upgraded"),
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor="#c62828", markersize=7.5, label="Score 2 Downgraded"),
    ]
    ax2.legend(handles=handles2, loc="lower right", fontsize=7.8, frameon=True)

    fig.suptitle("Resolving Ibn Ḥajar's Conditional 'Maqbūl' (Rank 6) on Unseen Held-Out [TEST] Narrators", fontsize=13.5, fontweight="bold", y=0.98)
    fig.subplots_adjust(left=0.06, right=0.97, top=0.90, bottom=0.09)
    png_path = OUT_DIR / "RANK6_MAQBUL_TEST_SHOWCASE_VIZ.png"
    fig.savefig(png_path, dpi=300)
    plt.close(fig)

    # Markdown Report
    md = [
        "# Rank 6 (*Maqbūl*) Held-Out `[TEST]` Showcase (`N = 229` Unseen Narrators)",
        "",
        "All `229` entries below belong strictly to the untouched **`test` split** and carry Ibn Ḥajar's single flat conditional label `مقبول` (`Score 1 = 54.55` / Rank 6).",
        "",
        "## 1. Quantitative Resolution Comparison (`N = 229` Unseen *Maqbūl*)",
        "",
        "| Model | Rank MAE ↓ | `0–100` MAE ↓ | Binary *Taʿdīl*/*Jarḥ* Acc ↑ |",
        "|---|---:|---:|---:|",
        f"| `Score 1` (Ibn Ḥajar Flat `54.55`) | {m_s1[0]:.4f} | {m_s1[1]:.2f} | {m_s1[2]*100:.2f}% |",
        f"| `Stage 2 G0` (AraBERTv02, No Graph) | {m_g0[0]:.4f} | {m_g0[1]:.2f} | {m_g0[2]*100:.2f}% |",
        f"| **`Stage 3 G4a` (TC-GNN Score 2)** | **{m_s2[0]:.4f}** | **{m_s2[1]:.2f}** | **{m_s2[2]*100:.2f}%** |",
        "",
        "## 2. True *Taḥrīr* Outcome Subgroups (`N = 229`)",
        "",
        "| True *Taḥrīr* Group | N | Mean Score 2 (`0–100`) | Mean TC-Sanad Out-Deg |",
        "|---|---:|---:|---:|",
    ]
    for o in order:
        sub = [r for r in out_records if r["tahrir_outcome_group"] == o]
        md.append(
            f"| `{o}` | {len(sub)} | {np.mean([r['score2_tc_gnn_reliability_0_100'] for r in sub]):.2f} | "
            f"{np.mean([r['tc_sanad_out_degree'] for r in sub]):.2f} |"
        )

    md.extend([
        "",
        "## 3. Spotlight: Top 10 Upgraded vs. Top 10 Downgraded Unseen `[TEST]` Narrators",
        "",
        "| Entry ID | Short Name | Sigils | Out-Deg | Score 1 | *Taḥrīr* (`0–100`) | Score 2 (`0–100`) | Entropy | *Taqrīb* Verbatim Snippet |",
        "|---|---|---|---:|---:|---:|---:|---:|---|",
    ])
    for r in spotlight:
        md.append(
            f"| `{r['entry_id']}` | {r['short_label'].split(': ', 1)[1]} | `{r['sigil_tokens_raw']}` | {r['tc_sanad_out_degree']} | "
            f"54.55 | {r['tahrir_reliability_0_100']:.2f} | **{r['score2_tc_gnn_reliability_0_100']:.2f}** | "
            f"{r['score2_rank_entropy']:.3f} | {r['taqrib_text_verbatim'][:70]} |"
        )

    (OUT_DIR / "RANK6_MAQBUL_TEST_SHOWCASE_REPORT.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("Generated Rank 6 showcase in", OUT_DIR)
    print(f"N=229 | S1 BinAcc={m_s1[2]*100:.2f}% (MAE100={m_s1[1]:.2f}) -> G0 BinAcc={m_g0[2]*100:.2f}% (MAE100={m_g0[1]:.2f}) -> TC-GNN BinAcc={m_s2[2]*100:.2f}% (MAE100={m_s2[1]:.2f})")


if __name__ == "__main__":
    main()
