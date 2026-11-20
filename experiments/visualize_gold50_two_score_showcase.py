#!/usr/bin/env python3
"""Generate Gold-50 Well-Known Narrators Two-Score Showcase & Visualizations.

Reads:
  - main:data/2_interim/rijal_fyp_modelling_pipeline/v2_gold50_adjudication_v2_1_2026-11-19/GOLD_50_ADJUDICATED_REFERENCE_V2_1.csv
  - results/stage3_tc_gnn_benchmarks_v2_2026-11-20/FINAL_TWO_SCORE_RIJAL_REPRESENTATION_8827.csv

Outputs to:
  results/stage3_tc_gnn_benchmarks_v2_2026-11-20/gold50_showcase/
    - GOLD50_TWO_SCORE_SHOWCASE.csv
    - GOLD50_TWO_SCORE_DUMBBELL_CHART.png
    - GOLD50_UNCERTAINTY_AND_SHIFT_VIZ.png
    - GOLD50_SHOWCASE_REPORT.md
"""

from __future__ import annotations

import csv
import io
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import seaborn as sns


ROOT = Path(__file__).resolve().parents[1]
FINAL_CSV = ROOT / "results/stage3_tc_gnn_benchmarks_v2_2026-11-20/FINAL_TWO_SCORE_RIJAL_REPRESENTATION_8827.csv"
OUT_DIR = ROOT / "results/stage3_tc_gnn_benchmarks_v2_2026-11-20/gold50_showcase"
GOLD50_GIT_REF = (
    "main:data/2_interim/rijal_fyp_modelling_pipeline/"
    "v2_gold50_adjudication_v2_1_2026-11-19/GOLD_50_ADJUDICATED_REFERENCE_V2_1.csv"
)

GROUP_TITLES = {
    "1_highly_reliable": "Group 1: Highly Reliable Imāms (n=18)",
    "2_nuanced_mixed": "Group 2: Nuanced / Mixed / Conditional (n=17)",
    "3_criticised_weaker": "Group 3: Criticised / Weaker Narrators (n=14 matched)",
}


def load_gold50_from_main() -> list[dict[str, str]]:
    raw = subprocess.check_output(["git", "show", GOLD50_GIT_REF], cwd=ROOT).decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(raw)))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="notebook")

    g50_rows = load_gold50_from_main()
    with FINAL_CSV.open(encoding="utf-8-sig") as f:
        f2s_rows = list(csv.DictReader(f))
    f2s_by_id = {r["entry_id"]: r for r in f2s_rows}

    showcase_rows: list[dict[str, Any]] = []
    unmatched_rows: list[dict[str, Any]] = []

    for r in g50_rows:
        eid = r["entry_id"]
        f = f2s_by_id.get(eid)
        if f is None:
            row_out = {
                "gold_id": r["gold_id"],
                "group_profile": r["group_profile"],
                "english_name": r["english_name"],
                "entry_id": eid,
                "matched_in_taqrib": False,
                "split": "unmatched",
                "score1_ibn_hajar_rank": "",
                "tahrir_scholar_rank": "",
                "tahrir_disposition": "",
                "score2_tc_gnn_continuous": "",
                "score2_tc_gnn_rank": "",
                "score2_predicted_shift": "",
                "score2_rank_entropy": "",
                "tc_sanad_out_degree": "",
                "tc_sanad_in_degree": "",
            }
            showcase_rows.append(row_out)
            unmatched_rows.append(row_out)
            continue

        showcase_rows.append(
            {
                "gold_id": r["gold_id"],
                "group_profile": r["group_profile"],
                "english_name": r["english_name"],
                "entry_id": eid,
                "matched_in_taqrib": True,
                "split": f["split"],
                "score1_ibn_hajar_rank": f["score1_ibn_hajar_rank_1_to_12"],
                "tahrir_scholar_rank": f["tahrir_scholar_rank_1_to_12"],
                "tahrir_disposition": f["tahrir_disposition"],
                "score2_tc_gnn_continuous": float(f["score2_tc_gnn_continuous"]),
                "score2_tc_gnn_rank": int(f["score2_tc_gnn_rank_1_to_12"]),
                "score2_predicted_shift": f["score2_predicted_shift"],
                "score2_rank_entropy": float(f["score2_rank_entropy"]),
                "tc_sanad_out_degree": int(f["tc_sanad_out_degree"]),
                "tc_sanad_in_degree": int(f["tc_sanad_in_degree"]),
            }
        )

    matched = [r for r in showcase_rows if r["matched_in_taqrib"]]
    matched.sort(key=lambda r: (r["group_profile"], r["score2_tc_gnn_continuous"], r["english_name"]))
    ordered_all = matched + unmatched_rows

    out_csv = OUT_DIR / "GOLD50_TWO_SCORE_SHOWCASE.csv"
    with out_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(ordered_all[0].keys()))
        w.writeheader()
        w.writerows(ordered_all)

    # 1. Dumbbell Chart (3 stacked panels)
    groups = ["1_highly_reliable", "2_nuanced_mixed", "3_criticised_weaker"]
    by_grp = {g: [r for r in matched if r["group_profile"] == g] for g in groups}
    heights = [len(by_grp[g]) for g in groups]

    fig, axes = plt.subplots(
        3, 1, figsize=(13.5, 16.5), sharex=True, gridspec_kw={"height_ratios": heights, "hspace": 0.22}
    )

    for ax, g in zip(axes, groups):
        items = list(reversed(by_grp[g]))  # top item = lowest/strongest score2
        y_pos = np.arange(len(items))

        ax.axvspan(0.5, 6.5, color="#e8f5e9", alpha=0.45, zorder=0)
        ax.axvspan(6.5, 12.5, color="#ffebee", alpha=0.45, zorder=0)
        ax.axvline(6.5, color="#555555", linestyle="--", linewidth=1.2, zorder=1)

        ylabels = []
        for idx, it in enumerate(items):
            s2 = it["score2_tc_gnn_continuous"]
            s1 = float(it["score1_ibn_hajar_rank"]) if it["score1_ibn_hajar_rank"] else None
            th = float(it["tahrir_scholar_rank"]) if it["tahrir_scholar_rank"] else None

            xs = [x for x in (s1, th, s2) if x is not None]
            if len(xs) >= 2:
                ax.plot([min(xs), max(xs)], [idx, idx], color="#9aa5b1", linewidth=1.6, zorder=2)

            if s1 is not None:
                ax.scatter(s1, idx, s=75, facecolors="none", edgecolors="#1f77b4", linewidths=2.0, zorder=4)
            if th is not None:
                ax.scatter(th, idx, s=65, marker="D", color="#2ca02c", zorder=5, alpha=0.9)
            ax.scatter(s2, idx, s=80, color="#d62728", zorder=6)

            tag = ""
            if it["split"] == "test":
                tag = " [TEST]"
            elif it["split"] == "val":
                tag = " [VAL]"
            elif it["split"] == "excluded_unranked":
                tag = " [UNRANKED]"
            ylabels.append(f"{it['english_name']}{tag}")
            ax.text(12.25, idx, f"out={it['tc_sanad_out_degree']}", va="center", ha="left", fontsize=8.5, color="#4a5568")

        ax.set_yticks(y_pos)
        ax.set_yticklabels(ylabels, fontsize=9.5)
        ax.set_ylim(-0.6, len(items) - 0.4)
        ax.set_title(GROUP_TITLES[g], loc="left", fontsize=11.5, fontweight="bold", pad=14 if idx == 0 else 6)
        ax.grid(axis="x", linestyle=":", alpha=0.6)

    axes[0].set_title(GROUP_TITLES[groups[0]], loc="left", fontsize=11.5, fontweight="bold", pad=22)
    axes[-1].set_xlim(0.6, 13.15)
    axes[-1].set_xticks(range(1, 13))
    axes[-1].set_xlabel("Bilgin (2026) 12-Rank Scale   (1–6: Ta'dīl / Reliable   |   7–12: Jarḥ / Weak)", fontsize=11, fontweight="bold")

    axes[0].text(3.5, len(by_grp[groups[0]]) - 0.1, "Ta'dīl (Ranks 1–6)", ha="center", va="bottom", fontsize=9.5, color="#2e7d32", fontweight="bold")
    axes[0].text(9.5, len(by_grp[groups[0]]) - 0.1, "Jarḥ (Ranks 7–12)", ha="center", va="bottom", fontsize=9.5, color="#c62828", fontweight="bold")

    legend_handles = [
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor="none", markeredgecolor="#1f77b4", markeredgewidth=2.0, markersize=8, label="Score 1: Ibn Ḥajar Taqrīb Baseline"),
        plt.Line2D([0], [0], marker="D", color="w", markerfacecolor="#2ca02c", markersize=7.5, label="Taḥrīr Scholar Verdict (8246)"),
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor="#d62728", markersize=8.5, label="Score 2: TC-GNN Continuous Score (G4a)"),
    ]
    fig.legend(handles=legend_handles, loc="upper center", bbox_to_anchor=(0.56, 0.976), ncol=3, frameon=True, fontsize=9.5)
    fig.suptitle("Gold-50 Well-Known Narrators: Score 1 Baseline vs. Taḥrīr Verdict vs. Score 2 TC-GNN", fontsize=13.5, fontweight="bold", y=0.994)
    fig.subplots_adjust(left=0.28, right=0.95, top=0.925, bottom=0.045)

    dumbbell_png = OUT_DIR / "GOLD50_TWO_SCORE_DUMBBELL_CHART.png"
    fig.savefig(dumbbell_png, dpi=300)
    plt.close(fig)

    # 2. Uncertainty & Test Shift Scatter (2-panel)
    fig2, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.5, 6.2))

    grp_labels = {
        "1_highly_reliable": "Highly\nReliable",
        "2_nuanced_mixed": "Nuanced /\nMixed",
        "3_criticised_weaker": "Criticised /\nWeaker",
    }
    ent_data = [[r["score2_rank_entropy"] for r in by_grp[g]] for g in groups]
    sns.boxplot(data=ent_data, ax=ax1, width=0.45, palette=["#2e7d32", "#f57c00", "#c62828"], showfliers=False)
    sns.stripplot(data=ent_data, ax=ax1, color="#222222", size=5.5, alpha=0.75, jitter=0.12)
    ax1.set_xticks([0, 1, 2])
    ax1.set_xticklabels([grp_labels[g] for g in groups], fontsize=10)
    ax1.set_ylabel("TC-GNN Normalized Rank Entropy (0 = Certain, 1 = Max Uncertainty)", fontsize=10)
    ax1.set_title("A. Calibrated Uncertainty Across Gold-50 Profiles", fontsize=11.5, fontweight="bold")
    ax1.set_ylim(-0.02, max(max(x) for x in ent_data) + 0.08)

    # Right panel: held-out test split (N=1,089) + Gold-50 [TEST] overlay
    test_f2s = [r for r in f2s_rows if r["split"] == "test"]
    s1_te, s2_te, shift_te = [], [], []
    for r in test_f2s:
        r1 = float(r["score1_ibn_hajar_rank_1_to_12"])
        r2 = float(r["score2_tc_gnn_continuous"])
        rt = float(r["tahrir_scholar_rank_1_to_12"])
        sh = "upgraded" if rt < r1 else ("unchanged" if rt == r1 else "downgraded")
        s1_te.append(r1 + np.random.default_rng(abs(hash(r["entry_id"])) % (2**31)).uniform(-0.18, 0.18))
        s2_te.append(r2)
        shift_te.append(sh)

    palette_map = {"upgraded": "#1b9e77", "unchanged": "#8da0cb", "downgraded": "#e7298a"}
    for sh in ["unchanged", "downgraded", "upgraded"]:
        xs = [s1_te[i] for i, s in enumerate(shift_te) if s == sh]
        ys = [s2_te[i] for i, s in enumerate(shift_te) if s == sh]
        ax2.scatter(xs, ys, s=16, alpha=0.45, color=palette_map[sh], label=f"True Taḥrīr: {sh} (n={len(xs)})")

    ax2.plot([1, 12], [1, 12], "k--", alpha=0.5, linewidth=1.1, label="Score 2 = Score 1 (Identity)")

    # Overlay Gold-50 [TEST] narrators (spread labels around clusters so zero overlap)
    g50_test = [r for r in matched if r["split"] == "test" and r["score1_ibn_hajar_rank"]]
    custom_offsets = {
        "Abd al-Rahman ibn Mahdi": (32, -30),
        "Hammad ibn Zayd": (-12, 52),
        "Shu'bah ibn al-Hajjaj": (32, -14),
        "Hammad ibn Salamah": (34, 4),
        "Nafi' mawla Ibn Umar": (-12, 32),
        "Yahya ibn Abi Kathir": (32, -48),
        "Tawus ibn Kaysan": (16, 28),
        "Mujahid ibn Jabr": (48, -6),
        "Jabir ibn Yazid al-Ju'fi": (-16, 18),
        "Muhammad ibn al-Sa'ib al-Kalbi": (-14, -22),
    }
    for r in g50_test:
        x = float(r["score1_ibn_hajar_rank"])
        y = r["score2_tc_gnn_continuous"]
        ax2.scatter(x, y, s=95, color="#111111", edgecolor="white", linewidth=1.2, zorder=8)
        dx, dy = custom_offsets.get(r["english_name"], (10, 10))
        ha = "left" if dx >= 0 else "right"
        short_name = r["english_name"]
        if len(short_name) > 20:
            short_name = short_name.replace("Muhammad ibn al-Sa'ib al-Kalbi", "Ibn al-Kalbi").replace("Abd al-Rahman ibn Mahdi", "Ibn Mahdi").replace("Nafi' mawla Ibn Umar", "Nafi' (Mawla)").replace("Yahya ibn Abi Kathir", "Yahya b. Abi Kathir").replace("Shu'bah ibn al-Hajjaj", "Shu'bah").replace("Jabir ibn Yazid al-Ju'fi", "Jabir al-Ju'fi")
        ax2.annotate(
            short_name,
            xy=(x, y),
            xytext=(dx, dy),
            textcoords="offset points",
            fontsize=7.8,
            fontweight="bold",
            ha=ha,
            arrowprops=dict(arrowstyle="-", color="#555555", lw=0.75),
            bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="#888888", alpha=0.9),
            zorder=9,
        )

    ax2.set_xlim(0.5, 12.5)
    ax2.set_ylim(0.5, 12.5)
    ax2.set_xticks(range(1, 13))
    ax2.set_yticks(range(1, 13))
    ax2.set_xlabel("Score 1: Ibn Ḥajar Taqrīb Baseline Rank", fontsize=10)
    ax2.set_ylabel("Score 2: TC-GNN Continuous Score", fontsize=10)
    ax2.set_title("B. Held-Out Test Split (N=1,089) + Gold-50 [TEST] Overlay", fontsize=11.5, fontweight="bold")
    ax2.legend(loc="upper left", fontsize=8.2, frameon=True)

    fig2.tight_layout()
    uncert_png = OUT_DIR / "GOLD50_UNCERTAINTY_AND_SHIFT_VIZ.png"
    fig2.savefig(uncert_png, dpi=300)
    plt.close(fig2)

    # 3. Markdown Report + Metrics
    eval_items = [r for r in matched if r["tahrir_scholar_rank"]]
    g50_mae = float(np.mean([abs(float(r["tahrir_scholar_rank"]) - r["score2_tc_gnn_continuous"]) for r in eval_items]))
    g50_bin = float(
        np.mean(
            [
                (1 if int(r["tahrir_scholar_rank"]) <= 6 else 0) == (1 if r["score2_tc_gnn_rank"] <= 6 else 0)
                for r in eval_items
            ]
        )
    )
    te_items = [r for r in eval_items if r["split"] == "test"]
    te_mae = float(np.mean([abs(float(r["tahrir_scholar_rank"]) - r["score2_tc_gnn_continuous"]) for r in te_items]))
    te_bin = float(
        np.mean(
            [
                (1 if int(r["tahrir_scholar_rank"]) <= 6 else 0) == (1 if r["score2_tc_gnn_rank"] <= 6 else 0)
                for r in te_items
            ]
        )
    )

    lines = [
        "# Gold-50 Well-Known Narrators: Two-Score Showcase Report",
        "",
        f"- **Matched in `FINAL_TWO_SCORE_RIJAL_REPRESENTATION_8827.csv`:** {len(matched)} / {len(g50_rows)}",
        f"- **Unmatched Gold-50 entry (`1`):** "
        + (", ".join(f"`{u['entry_id']}` ({u['english_name']})" for u in unmatched_rows) if unmatched_rows else "None"),
        f"- **Gold-50 vs. Taḥrīr (`n={len(eval_items)}` ranked):** MAE = **{g50_mae:.4f}**, Binary *Taʿdīl*/*Jarḥ* Acc = **{g50_bin * 100:.2f}%**",
        f"- **Held-Out Gold-50 `[TEST]` Subset (`n={len(te_items)}`):** MAE = **{te_mae:.4f}**, Binary *Taʿdīl*/*Jarḥ* Acc = **{te_bin * 100:.2f}%**",
        "",
        "## Mean TC-GNN Rank Entropy by Gold-50 Profile",
        "",
        "| Profile | N | Mean Rank Entropy |",
        "|---|---:|---:|",
    ]
    for g in groups:
        ents = [r["score2_rank_entropy"] for r in by_grp[g]]
        lines.append(f"| `{g}` | {len(ents)} | {np.mean(ents):.4f} |")

    lines.extend(
        [
            "",
            "## Full Gold-50 Two-Score Table",
            "",
            "| Gold ID | Profile | Narrator | Split | Score 1 (Ibn Ḥajar) | Taḥrīr Verdict | Score 2 (TC-GNN Cont.) | Score 2 (Rank) | Pred. Shift | Entropy | TC-Sanad Out |",
            "|---|---|---|---|---:|---:|---:|---:|---|---:|---:|",
        ]
    )
    for r in ordered_all:
        if not r["matched_in_taqrib"]:
            lines.append(f"| `{r['gold_id']}` | `{r['group_profile']}` | {r['english_name']} (`{r['entry_id']}`) | `unmatched` | — | — | — | — | — | — | — |")
        else:
            s1 = r["score1_ibn_hajar_rank"] or "*(unranked)*"
            th = r["tahrir_scholar_rank"] or "*(unranked)*"
            lines.append(
                f"| `{r['gold_id']}` | `{r['group_profile']}` | {r['english_name']} | `{r['split']}` | {s1} | {th} | "
                f"{r['score2_tc_gnn_continuous']:.3f} | {r['score2_tc_gnn_rank']} | `{r['score2_predicted_shift']}` | "
                f"{r['score2_rank_entropy']:.3f} | {r['tc_sanad_out_degree']} |"
            )

    report_md = OUT_DIR / "GOLD50_SHOWCASE_REPORT.md"
    report_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Generated Gold-50 showcase in", OUT_DIR)
    print(f"All ranked ({len(eval_items)}): MAE={g50_mae:.4f}, BinAcc={g50_bin:.4f} | Test ({len(te_items)}): MAE={te_mae:.4f}, BinAcc={te_bin:.4f}")


if __name__ == "__main__":
    main()
