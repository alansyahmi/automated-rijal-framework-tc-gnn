#!/usr/bin/env python3
"""Generate Gold-50 and Rank-6 (Maqbul) Stepped Layered Score Showcases (v3).

Reads:
  - results/layered_experiments_v3_2026-11-21/FINAL_LAYERED_RIJAL_SCORES_8827_V3.csv
  - data/2_interim/rijal_fyp_modelling_pipeline/taqrib_v2_master_dataset_2026-11-20/TAQRIB_V2_MASTER_NODES_8827.csv
  - main:data/2_interim/rijal_fyp_modelling_pipeline/v2_gold50_adjudication_v2_1_2026-11-19/GOLD_50_ADJUDICATED_REFERENCE_V2_1.csv

Outputs under results/layered_experiments_v3_2026-11-21/showcases/:
  - GOLD50_LAYERED_SHOWCASE_V3.csv
  - GOLD50_STEPPED_LAYERS_CHART_V3.png
  - RANK6_MAQBUL_LAYERED_SHOWCASE_V3.csv
  - RANK6_MAQBUL_LAYERED_VIZ_V3.png
  - SHOWCASES_REPORT_V3.md
"""

from __future__ import annotations

import csv
import io
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from common.rank_scale import THRESHOLDS, rank_to_score, score_to_rank_cont  # noqa: E402
from experiments.visualize_rank6_maqbul_test_showcase import transliterate_short_name  # noqa: E402

FINAL_CSV = ROOT / "results/layered_experiments_v3_2026-11-21/FINAL_LAYERED_RIJAL_SCORES_8827_V3.csv"
MASTER_CSV = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline/taqrib_v2_master_dataset_2026-11-20/TAQRIB_V2_MASTER_NODES_8827.csv"
OUT_DIR = ROOT / "results/layered_experiments_v3_2026-11-21/showcases"
GOLD50_GIT_REF = (
    "main:data/2_interim/rijal_fyp_modelling_pipeline/"
    "v2_gold50_adjudication_v2_1_2026-11-19/GOLD_50_ADJUDICATED_REFERENCE_V2_1.csv"
)


def load_gold50() -> list[dict[str, str]]:
    raw = subprocess.check_output(["git", "show", GOLD50_GIT_REF], cwd=ROOT).decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(raw)))


def plot_gold50_stepped(matched_rows: list[dict[str, Any]], out_png: Path) -> None:
    groups = [
        ("1_highly_reliable", "Group 1: Highly Reliable Imāms"),
        ("2_nuanced_mixed", "Group 2: Nuanced / Mixed / Conditional"),
        ("3_criticised_weaker", "Group 3: Criticised / Weaker Narrators"),
    ]
    fig, axes = plt.subplots(3, 1, figsize=(13, 18), gridspec_kw={"height_ratios": [18, 17, 14]})
    for ax, (gk, title) in zip(axes, groups):
        sub = [r for r in matched_rows if r["group_profile"] == gk]
        sub = sorted(sub, key=lambda x: float(x["score_E2"]) if x["score_E2"] != "" else (float(x["score_B"]) if x["score_B"] != "" else -1.0))
        y = np.arange(len(sub))
        labels = [f"{r['gold_id']} {r['english_name'][:32]}" for r in sub]

        for idx, r in enumerate(sub):
            sb = float(r["score_B"]) if r["score_B"] != "" else None
            se1 = float(r["score_E1"]) if r["score_E1"] != "" else None
            se2 = float(r["score_E2"]) if r["score_E2"] != "" else None
            sg_est = float(r["score_G_estimate"]) if r["source"] == "model_estimate" and r["score_G_estimate"] != "" else None
            if sb is not None and se2 is not None:
                color = "#c0392b" if se2 < sb else ("#27ae60" if se2 > sb else "#7f8c8d")
                ax.plot([sb, se2], [idx, idx], color=color, linewidth=1.8, alpha=0.65, zorder=2)

        pts_b = [(i, float(r["score_B"])) for i, r in enumerate(sub) if r["score_B"] != ""]
        pts_e1 = [(i, float(r["score_E1"])) for i, r in enumerate(sub) if r["score_E1"] != "" and float(r["delta_E1"]) != 0.0]
        pts_e2 = [(i, float(r["score_E2"])) for i, r in enumerate(sub) if r["score_E2"] != ""]
        pts_g = [(i, float(r["score_G_estimate"])) for i, r in enumerate(sub) if r["source"] == "model_estimate" and r["score_G_estimate"] != ""]

        if pts_b:
            ax.scatter([p[1] for p in pts_b], [p[0] for p in pts_b], color="#2c3e50", s=55, marker="o", label="Layer B (Ibn Hajar Taqrib)", zorder=3)
        if pts_e1:
            ax.scatter([p[1] for p in pts_e1], [p[0] for p in pts_e1], color="#e67e22", s=60, marker="^", label="Layer B+E1 (Qualifiers)", zorder=4)
        if pts_e2:
            ax.scatter([p[1] for p in pts_e2], [p[0] for p in pts_e2], color="#2980b9", s=70, marker="s", label="Layer B+E1+E2 (Tahrir)", zorder=5)
        if pts_g:
            ax.scatter([p[1] for p in pts_g], [p[0] for p in pts_g], facecolors="none", edgecolors="#8e44ad", s=80, marker="D", label="G estimate (missing Tahrir only)", zorder=6)

        ax.set_yticks(y)
        ax.set_yticklabels(labels, fontsize=8.5)
        ax.set_xlim(-3, 104)
        for tname, tval, tcol in [("sahih=80", THRESHOLDS["hukm_v1"]["sahih"], "#27ae60"), ("accepted=50", THRESHOLDS["hukm_v1"]["accepted_alone"], "#e67e22"), ("itibar=25", THRESHOLDS["hukm_v1"]["itibar"], "#c0392b")]:
            ax.axvline(x=tval, color=tcol, linestyle=":", linewidth=1.0, alpha=0.55)
        ax.set_title(f"{title} (n={len(sub)})", fontsize=11, fontweight="bold")
        ax.grid(axis="x", linestyle="--", alpha=0.4)
        if gk == "1_highly_reliable":
            ax.legend(loc="lower left", fontsize=8.5, ncol=2)

    axes[-1].set_xlabel("Layered 0–100 Narrator Reliability Score (hukm_v1 scale)", fontsize=11)
    fig.suptitle("Gold-50 Well-Known Narrators: Stepped B -> B+E1 -> B+E1+E2 Trajectory (v3)", fontsize=13, fontweight="bold", y=0.995)
    fig.tight_layout()
    fig.savefig(out_png, dpi=180)
    plt.close(fig)


def plot_rank6_showcase(r6_rows: list[dict[str, Any]], out_png: Path) -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.2))
    r6_base = rank_to_score(6, "hukm_v1")  # 40.0 on hukm_v1

    vals_e2 = [float(r["score_E2"]) for r in r6_rows if r["score_E2"] != ""]
    counts = Counter(round(v, 2) for v in vals_e2)
    xs = sorted(counts.keys())
    ys = [counts[x] for x in xs]
    colors = ["#c0392b" if x < r6_base else ("#27ae60" if x > r6_base else "#7f8c8d") for x in xs]
    ax1.bar([str(x) for x in xs], ys, color=colors, edgecolor="#2c3e50", linewidth=0.7)
    r7_str = str(round(rank_to_score(7, "hukm_v1"), 2))
    if r7_str in [str(x) for x in xs]:
        ax1.axvline(x=[str(x) for x in xs].index(r7_str), color="#c0392b", linestyle="--", alpha=0.4)
    ax1.set_title(f"Unseen Clean Test Rank-6 Maqbul (N={len(r6_rows)})\nAll Start at Layer B = {r6_base:.1f} -> Resolved by E2", fontsize=10.5, fontweight="bold")
    ax1.set_xlabel("Layer B+E1+E2 Score (0–100, hukm_v1)", fontsize=10)
    ax1.set_ylabel("Narrator Count", fontsize=10)
    ax1.tick_params(axis="x", rotation=40, labelsize=8.5)

    # Panel B: al-Kashif external agreement on test Rank-6 narrators
    t3_counts = Counter()
    for r in r6_rows:
        kt3 = r["kashif_tier_3"].strip()
        e2_s = r["score_E2"].strip()
        if not kt3 or not e2_s:
            continue
        re2 = int(round(score_to_rank_cont(float(e2_s), "hukm_v1")))
        t3_e2 = "2" if re2 <= 3 else ("1" if re2 <= 6 else "0")
        t3_counts["B=Saduq matches Kashif" if kt3 == "1" else "B=Saduq misses Kashif"] += 1
        t3_counts["E2 matches Kashif" if kt3 == t3_e2 else "E2 misses Kashif"] += 1
    labels_b = ["Layer B\nMatches", "Layer B\nMisses", "Layer E2\nMatches", "Layer E2\nMisses"]
    vals_b = [
        t3_counts["B=Saduq matches Kashif"],
        t3_counts["B=Saduq misses Kashif"],
        t3_counts["E2 matches Kashif"],
        t3_counts["E2 misses Kashif"],
    ]
    ax2.bar(labels_b, vals_b, color=["#7f8c8d", "#bdc3c7", "#2980b9", "#d6eaf8"], edgecolor="#2c3e50", linewidth=0.7)
    ax2.set_title("Rank-6 Test Narrators Mapped in al-Kashif\n3-Tier External Agreement: B vs E2", fontsize=10.5, fontweight="bold")
    ax2.set_ylabel("Narrator Count", fontsize=10)
    for i, v in enumerate(vals_b):
        ax2.text(i, v + 1.0, str(v), ha="center", va="bottom", fontsize=9)

    fig.tight_layout()
    fig.savefig(out_png, dpi=180)
    plt.close(fig)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="notebook")

    with FINAL_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        final_rows = list(csv.DictReader(f))
    final_by_id = {r["entry_id"]: r for r in final_rows}
    with MASTER_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        master_by_id = {r["entry_id"]: r for r in csv.DictReader(f)}

    # Gold-50 showcase
    g50_ref = load_gold50()
    gold_out: list[dict[str, Any]] = []
    matched_gold: list[dict[str, Any]] = []
    for r in g50_ref:
        eid = r["entry_id"]
        fr = final_by_id.get(eid)
        if fr is None:
            gold_out.append({
                "gold_id": r["gold_id"], "group_profile": r["group_profile"], "english_name": r["english_name"],
                "entry_id": eid, "matched": False, "split": "unmatched",
                "score_B": "", "rank_B": "", "score_E1": "", "delta_E1": "",
                "score_E2": "", "rank_E2": "", "delta_E2": "", "status_E2": "",
                "score_G_estimate": "", "source": "", "kashif_tier_3": "", "kashif_tier_5": "",
            })
            continue
        row = {
            "gold_id": r["gold_id"], "group_profile": r["group_profile"], "english_name": r["english_name"],
            "entry_id": eid, "matched": True, "split": fr["split"],
            "score_B": fr["score_B"], "rank_B": fr["rank_B"],
            "score_E1": fr["score_E1"], "delta_E1": fr["delta_E1"],
            "score_E2": fr["score_E2"], "rank_E2": fr["rank_E2"],
            "delta_E2": fr["delta_E2"], "status_E2": fr["status_E2"],
            "score_G_estimate": fr["score_G_estimate"], "source": fr["source"],
            "kashif_tier_3": fr["kashif_tier_3"], "kashif_tier_5": fr["kashif_tier_5"],
        }
        gold_out.append(row)
        matched_gold.append(row)

    gold_csv = OUT_DIR / "GOLD50_LAYERED_SHOWCASE_V3.csv"
    with gold_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(gold_out[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(gold_out)
    plot_gold50_stepped(matched_gold, OUT_DIR / "GOLD50_STEPPED_LAYERS_CHART_V3.png")

    # Rank-6 clean test showcase
    r6_out: list[dict[str, Any]] = []
    for r in final_rows:
        if r["split"] == "test" and r["taqrib_is_conditional_maqbul"] == "True" and r["status_E2"] not in {"missing", "suspect_alignment"}:
            eid = r["entry_id"]
            mr = master_by_id[eid]
            r6_out.append({
                "entry_id": eid,
                "short_label": transliterate_short_name(mr["taqrib_text_verbatim"], eid.split("-")[-1]),
                "score_B": r["score_B"],
                "score_E1": r["score_E1"],
                "delta_E1": r["delta_E1"],
                "score_E2": r["score_E2"],
                "rank_E2": r["rank_E2"],
                "delta_E2": r["delta_E2"],
                "status_E2": r["status_E2"],
                "tahrir_disposition": r["tahrir_disposition"],
                "source": r["source"],
                "score_G_estimate": r["score_G_estimate"],
                "kashif_tier_3": r["kashif_tier_3"],
            })

    r6_csv = OUT_DIR / "RANK6_MAQBUL_LAYERED_SHOWCASE_V3.csv"
    with r6_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(r6_out[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(r6_out)
    plot_rank6_showcase(r6_out, OUT_DIR / "RANK6_MAQBUL_LAYERED_VIZ_V3.png")

    e6868 = next((x for x in gold_out if x["entry_id"] == "S3076-P545-C001-E6868"), {})
    md = [
        "# Layered 0–100 Narrator Score Showcases (v3)",
        "",
        f"- **Gold-50 Matched Narrators:** `{len(matched_gold)}` / `{len(gold_out)}` (1 Prophet-era/Sahabi edge case unmatched in Bilgin table).",
        f"- **Gold-50 `E6868` (Muqatil b. Sulayman):** `rank_B = {e6868.get('rank_B', '')}`, `score_B = {e6868.get('score_B', '')}`, `score_E2 = {e6868.get('score_E2', '')}` (`status_E2 = {e6868.get('status_E2', '')}`).",
        f"- **Rank-6 (`maqbul`) Unseen Clean Test Cohort:** `N = {len(r6_out)}` narrators starting at flat `score_B = {rank_to_score(6, 'hukm_v1'):.2f}` (`hukm_v1` scale).",
        "",
        "Generated files:",
        "- `GOLD50_LAYERED_SHOWCASE_V3.csv`",
        "- `GOLD50_STEPPED_LAYERS_CHART_V3.png`",
        "- `RANK6_MAQBUL_LAYERED_SHOWCASE_V3.csv`",
        "- `RANK6_MAQBUL_LAYERED_VIZ_V3.png`",
    ]
    (OUT_DIR / "SHOWCASES_REPORT_V3.md").write_bytes(("\n".join(md) + "\n").encode("utf-8"))
    print(f"Showcases generated -> {OUT_DIR}")


if __name__ == "__main__":
    main()
