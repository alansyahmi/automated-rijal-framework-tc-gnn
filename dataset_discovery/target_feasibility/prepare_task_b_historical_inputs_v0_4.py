#!/usr/bin/env python3
"""Prepare Task B Historical Inputs v0.4 (Refinements 2, 3, and 4).

Builds cleanly on verified v0.3 1-to-1 narrator linkage while adding:
- Refinement 2: Extracts non-Ibn-Hajar analytical passages from fwaed_raw.csv
  (15,963 rows total; preserves Irsal, Ikhtilat, Tadlis, Ilqa, etc.).
- Refinement 3: Fixes Rank 7 & 9 selection bias by retaining all ~5,246
  unique_1to1_high_conf + assigned_rank narrators (explicitly flagging
  has_early_critic_quote=no rather than censoring Majhul/Mastur narrators).
- Refinement 4: Produces an optional Early-Speaker-via-Tahdhib-al-Tahdhib
  ablation file (strictly excluding Taqrib, Tahrir, Ibn Hajar speaker rows,
  and 'قلت'/'قال المؤلف' commentary) kept separate from the Strict Book Firewall.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PIPELINE = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline"
V03_DIR = PIPELINE / "task_b_historical_inputs_v0_3_2026-11-17"
SH_EVALS = ROOT / "data/2_interim/shamela4_narrator_audit/evaluations_raw.csv"
SH_FWAED = ROOT / "data/2_interim/shamela4_narrator_audit/fwaed_raw.csv"
OUT_DIR = PIPELINE / "task_b_historical_inputs_v0_4_2026-11-17"

PROHIBITED_FWAED_WORK_KEYS = (
    "تقريب", "التقريب", "تحرير", "تهذيب التهذيب", "لسان الميزان",
    "تعجيل المنفعة", "الإصابة", "تعريف أهل التقديس", "المجمع المؤسس",
    "إتحاف المهرة", "تغليق التعليق", "هدي الساري", "فتح الباري",
)

PROHIBITED_EVER_KEYS = ("تقريب", "التقريب", "تحرير")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\r\n")
        writer.writeheader()
        writer.writerows(rows)


def assert_no_em_en_dash(text: str, label: str) -> None:
    if "\u2014" in text or "\u2013" in text:
        raise SystemExit(f"Forbidden em-dash or en-dash in {label}")


def verify_package(directory: Path) -> None:
    manifest_path = directory / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    sidecar = (directory / "MANIFEST.sha256").read_text(encoding="ascii").split()[0]
    if digest(manifest_path) != sidecar:
        raise SystemExit(f"MANIFEST.sha256 mismatch in {directory}")
    for name, expected in manifest["outputs"].items():
        if digest(directory / name) != expected:
            raise SystemExit(f"Hash mismatch for {directory.name}/{name}")


def main() -> None:
    if OUT_DIR.exists() and any(OUT_DIR.iterdir()):
        raise SystemExit(f"Refusing to overwrite existing Task B v0.4 directory: {OUT_DIR}")

    verify_package(V03_DIR)
    narr_v03 = read_csv(V03_DIR / "TASK_B_NARRATOR_LINKAGE_AND_ELIGIBILITY_8827_V0_3.csv")
    passages_v03 = read_csv(V03_DIR / "TASK_B_ELIGIBLE_HISTORICAL_PASSAGES_V0_3.csv")

    nid_to_row = {
        r["shamela_narrator_id"]: r
        for r in narr_v03
        if r["shamela_narrator_id"]
    }

    # 1. Process fwaed_raw.csv under strict zero-Ibn-Hajar-book firewall
    fwaed_kept: list[dict[str, Any]] = []
    fwaed_counts: Counter[str] = Counter()
    fwaed_by_eid: Counter[str] = Counter()

    for r in read_csv(SH_FWAED):
        nid = r["narrator_id"]
        if nid not in nid_to_row:
            fwaed_counts["excluded_unlinked_narrator"] += 1
            continue
        arr = json.loads(r["entry_json"])
        text = str(arr[0]) if len(arr) > 0 else ""
        cit = str(arr[1]) if len(arr) > 1 else ""
        src_id = str(arr[2]) if len(arr) > 2 else ""
        if any(k in cit for k in PROHIBITED_FWAED_WORK_KEYS):
            fwaed_counts["excluded_prohibited_taqrib_or_ibn_hajar"] += 1
            continue
        if not text.strip():
            fwaed_counts["excluded_empty"] += 1
            continue
        fwaed_counts["eligible_non_ibn_hajar_fwaed"] += 1
        eid = nid_to_row[nid]["entry_id"]
        fwaed_by_eid[eid] += 1
        fwaed_kept.append({
            "fwaed_id": f"TB4-FWD-{len(fwaed_kept) + 1:05d}",
            "entry_id": eid,
            "shamela_narrator_id": nid,
            "fwaed_category": r["category_raw"],
            "source_citation_exact": cit,
            "source_id_raw": src_id,
            "fwaed_text_exact": text,
        })

    # 2. Extract optional Early-Speaker-in-Tahdhib ablation rows (strictly excluding Taqrib/Ibn Hajar voice)
    ablation_rows: list[dict[str, Any]] = []
    ablation_by_eid: Counter[str] = Counter()
    for r in read_csv(SH_EVALS):
        nid = r["narrator_id"]
        if nid not in nid_to_row:
            continue
        title = r["normalised_title_candidate"]
        cit = r["source_citation_raw"]
        grp = r["group_label_raw"]
        qtext = r["quotation_text"]
        if "تهذيب التهذيب" not in title and "تهذيب التهذيب" not in cit:
            continue
        if any(k in f"{title} || {cit}" for k in PROHIBITED_EVER_KEYS):
            continue
        if "ابن حجر" in grp or "قلت" in qtext or "قال المؤلف" in qtext:
            continue
        if not qtext.strip():
            continue
        eid = nid_to_row[nid]["entry_id"]
        ablation_by_eid[eid] += 1
        ablation_rows.append({
            "ablation_passage_id": f"TB4-ABL-{len(ablation_rows) + 1:06d}",
            "entry_id": eid,
            "shamela_narrator_id": nid,
            "historical_attribution_critic": grp,
            "source_work_normalised": title,
            "source_citation_exact": cit,
            "source_id_raw": r["source_id_raw"],
            "quotation_text_exact": qtext,
        })

    # 3. Build upgraded narrator eligibility table retaining ALL unique_1to1_high_conf + assigned_rank
    prim_by_eid = Counter(
        p["entry_id"] for p in passages_v03 if p["historical_input_eligibility"] == "eligible_primary_historical_passage"
    )
    sec_by_eid = Counter(
        p["entry_id"] for p in passages_v03 if p["historical_input_eligibility"] == "eligible_secondary_summary_work"
    )

    narr_v04: list[dict[str, Any]] = []
    for r in narr_v03:
        eid = r["entry_id"]
        n_prim = prim_by_eid.get(eid, 0)
        n_sec = sec_by_eid.get(eid, 0)
        n_fwd = fwaed_by_eid.get(eid, 0)
        n_abl = ablation_by_eid.get(eid, 0)
        is_high_conf_assigned = (
            r["identity_link_status"] == "unique_1to1_high_conf"
            and r["target_suitability_task_a"] == "assigned_rank"
        )
        out = dict(r)
        out["eligible_primary_passage_count"] = n_prim
        out["eligible_secondary_passage_count"] = n_sec
        out["eligible_fwaed_passage_count"] = n_fwd
        out["ablation_tahdhib_early_count"] = n_abl
        out["has_early_critic_quote"] = "yes" if n_prim > 0 else "no"
        out["has_any_non_taqrib_text"] = "yes" if (n_prim + n_sec + n_fwd) > 0 else "no"
        if is_high_conf_assigned and (n_prim > 0):
            tier = "eligible_primary_quote_present"
        elif is_high_conf_assigned and (n_sec + n_fwd) > 0:
            tier = "eligible_fwaed_or_secondary_only"
        elif is_high_conf_assigned:
            tier = "eligible_structural_or_zero_quote"
        else:
            tier = "excluded_unlinked_or_no_task_a_target"
        out["task_b_v04_cohort_tier"] = tier
        narr_v04.append(out)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    narr_csv = OUT_DIR / "TASK_B_NARRATOR_ELIGIBILITY_8827_V0_4.csv"
    fwaed_csv = OUT_DIR / "TASK_B_FWAED_PASSAGES_V0_4.csv"
    abl_csv = OUT_DIR / "TASK_B_EARLY_SPEAKER_ABLATION_PASSAGES_V0_4.csv"
    write_csv(narr_csv, narr_v04, list(narr_v04[0]))
    write_csv(fwaed_csv, fwaed_kept, list(fwaed_kept[0]))
    write_csv(abl_csv, ablation_rows, list(ablation_rows[0]))

    tier_counts = Counter(r["task_b_v04_cohort_tier"] for r in narr_v04)
    full_high_conf_ranks = Counter(
        r["task_a_rank_1_to_12"]
        for r in narr_v04
        if r["task_b_v04_cohort_tier"] != "excluded_unlinked_or_no_task_a_target"
    )
    zero_quote_ranks = Counter(
        r["task_a_rank_1_to_12"]
        for r in narr_v04
        if r["task_b_v04_cohort_tier"] in {"eligible_fwaed_or_secondary_only", "eligible_structural_or_zero_quote"}
    )

    report_lines = [
        "# Task B Historical Inputs v0.4 Report (Fwaed + Majhul Bias Fix + Early-Speaker Ablation)",
        "",
        "**Status:** refined Task B inputs preserving `v0.3` untouched while integrating `fwaed_raw.csv`, recovering zero-quote `Majhul`/`Mastur` high-confidence narrators, and isolating optional early-speaker-in-Tahdhib ablation rows.",
        "",
        "## 1. Non-Ibn-Hajar Fwaed Passages (`fwaed_raw.csv`)",
        f"- Filter breakdown: `{dict(sorted(fwaed_counts.items()))}`",
        f"- Retained strict zero-leakage `fwaed` passages: **{len(fwaed_kept)}**",
        "",
        "## 2. Optional Early-Speaker-in-Tahdhib-al-Tahdhib Ablation Tier",
        f"- Early non-Ibn-Hajar speaker quotes extracted cleanly from `تهذيب التهذيب` (excluding `قلت`/`قال المؤلف`/`تقريب`): **{len(ablation_rows)}** passages",
        "",
        "## 3. Full High-Confidence Cohort (Fixing Rank 7 & 9 Selection Bias)",
        f"- All `8,827` entries by `task_b_v04_cohort_tier`: `{dict(sorted(tier_counts.items()))}`",
        f"- Total `unique_1to1_high_conf` + `assigned_rank` cohort: **{sum(full_high_conf_ranks.values())}** (up from `4,830`)",
        f"- Recovered narrators without primary `ghar` critic quotes (`has_early_critic_quote=no`): **{sum(zero_quote_ranks.values())}** (`{dict(sorted(zero_quote_ranks.items()))}`)",
        "- Per-Rank counts across the full high-confidence cohort (`1..12`):",
    ]
    for i in range(1, 13):
        report_lines.append(
            f"  - Rank **{i}**: total=`{full_high_conf_ranks.get(str(i), 0)}` (recovered zero-quote=`{zero_quote_ranks.get(str(i), 0)}`)"
        )

    report_text = "\n".join(report_lines) + "\n"
    assert_no_em_en_dash(report_text, "TASK_B_INPUTS_REPORT_V0_4.md")
    report_path = OUT_DIR / "TASK_B_INPUTS_REPORT_V0_4.md"
    report_path.write_text(report_text, encoding="utf-8", newline="\n")

    timestamp = datetime.now(timezone.utc).isoformat()
    inputs = [
        V03_DIR / "TASK_B_NARRATOR_LINKAGE_AND_ELIGIBILITY_8827_V0_3.csv",
        V03_DIR / "TASK_B_ELIGIBLE_HISTORICAL_PASSAGES_V0_3.csv",
        V03_DIR / "MANIFEST.json",
        SH_FWAED,
        SH_EVALS,
        Path(__file__).resolve(),
    ]
    outputs = [narr_csv, fwaed_csv, abl_csv, report_path]
    manifest = {
        "package_id": OUT_DIR.name,
        "generated_at_utc": timestamp,
        "counts": {
            "fwaed_retained": len(fwaed_kept),
            "ablation_tahdhib_early_retained": len(ablation_rows),
            "cohort_tier_counts": dict(sorted(tier_counts.items())),
            "full_high_conf_assigned_cohort": sum(full_high_conf_ranks.values()),
            "zero_quote_recovered_counts": dict(sorted(zero_quote_ranks.items())),
        },
        "inputs": {path.relative_to(ROOT).as_posix(): digest(path) for path in inputs},
        "outputs": {path.name: digest(path) for path in outputs},
        "manifest_hash_policy": "MANIFEST.sha256 records this manifest hash separately; it is not recursively embedded.",
    }
    manifest_str = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    assert_no_em_en_dash(manifest_str, "MANIFEST.json")
    manifest_path = OUT_DIR / "MANIFEST.json"
    manifest_path.write_text(manifest_str, encoding="utf-8", newline="\n")
    (OUT_DIR / "MANIFEST.sha256").write_text(f"{digest(manifest_path)}  MANIFEST.json\n", encoding="ascii", newline="\n")

    print(json.dumps({"output": str(OUT_DIR), **manifest["counts"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
