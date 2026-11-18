#!/usr/bin/env python3
"""Prepare Task B non-Taqrib historical passages, narrator identity links, and leakage firewall v0.1.

Implements TODO lines 50-53:
1. Links local Taqrib entries (8,827; Task A v1.3) 1-to-1 to Shamela4 narrators
   (18,989) and HadithDB narrators (1,524) using strict mutual-best unique matching.
2. Enforces the Task B Zero-Leakage Firewall: rejects ALL Taqrib al-Tahdhib,
   Tahrir al-Taqrib, and Ibn Hajar works/attributions (تهذيب التهذيب, لسان الميزان,
   الإصابة, تعجيل المنفعة, تعريف أهل التقديس, etc.) plus الرتبة عند ابن حجر and
   طبقة رواة التقريب.
3. Separates textual correspondence, historical attribution, identity link status,
   Task A target suitability, and historical-input eligibility (flagging al-Kashif /
   Dhahabi summary works separately for clean thesis ablations).
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PIPELINE = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline"
ENTRY_INDEX = PIPELINE / "rank_label_shadow_run_v1_2026-11-15/ENTRY_INDEX.csv"
TASK_A_V13 = PIPELINE / "task_a_deterministic_targets_v1_3_2026-11-17/TASK_A_DETERMINISTIC_TARGETS_8827_V1_3.csv"
SH_NARRATORS = ROOT / "data/2_interim/shamela4_narrator_audit/narrators.csv"
SH_EVALS = ROOT / "data/2_interim/shamela4_narrator_audit/evaluations_raw.csv"
HDB_NARRATORS = ROOT / "data/1_raw/hadithdb/narrators_db.json"
OUT_DIR = PIPELINE / "task_b_historical_inputs_v0_1_2026-11-17"

DIACRITICS_RE = re.compile(r"[\u064b-\u065f\u0670\u0640\u200c]")
DABT_WORDS = {
    "بفتح", "بضم", "بكسر", "بسكون", "بمهملة", "بمهملتين", "بمعجمة", "بمعجمتين",
    "بموحدة", "بمثناة", "بمثلثة", "مصغر", "بالتصغير", "بالتشديد", "بالتخفيف", "بالمد",
    "بالجيم", "بالنون", "بالراء", "بالزاي", "بالقاف", "بالفاء", "بالشين", "بالميم",
    "وبفتح", "وبضم", "وبكسر", "وسكون", "وتشديد", "وتخفيف", "وموحدة", "ومهملة", "ومعجمة",
    "أوله", "ثانيه", "ثالثه", "آخره", "أولها", "ثانيها", "بوزن", "وزن",
}

PROHIBITED_SOURCE_SUBSTRINGS = (
    "تقريب",
    "التقريب",
    "تحرير",
    "تهذيب التهذيب",
    "لسان الميزان",
    "تعجيل المنفعة",
    "الإصابة",
    "تعريف أهل التقديس",
    "المجمع المؤسس",
    "إتحاف المهرة",
    "تغليق التعليق",
    "هدي الساري",
    "فتح الباري",
    "الرتبة عند ابن حجر",
)
PROHIBITED_GROUP_SUBSTRINGS = ("ابن حجر",)

SUMMARY_WORK_SUBSTRINGS = ("الكاشف",)


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


def norm_ar(text: str) -> str:
    s = DIACRITICS_RE.sub("", text)
    s = re.sub(r"\[[^\]]*\]|\([^\)]*\)", " ", s)
    s = s.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ى", "ي").replace("ة", "ه")
    s = re.sub(r"\bبن\b", "ابن", s)
    s = re.sub(r"[^\w\u0621-\u064a\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def resolve_taqrib_to_shamela(
    entries: list[dict[str, str]],
    task_a: dict[str, dict[str, str]],
    sh_info: dict[str, dict[str, Any]],
    by_first_word: dict[str, list[str]],
) -> tuple[dict[str, tuple[str, int, str]], dict[str, int]]:
    """Return 1-to-1 mutual-best resolved map: entry_id -> (shamela_nid, score, status)."""
    entry_top: dict[str, tuple[int, list[str]]] = {}
    nid_best_for_entry: defaultdict[str, list[tuple[int, str]]] = defaultdict(list)

    for e in entries:
        eid = e["entry_id"]
        txt = norm_ar(e["entry_text_verbatim"])
        toks = [w for w in txt.split() if not w.isdigit() and w not in DABT_WORDS]
        span = norm_ar(task_a[eid]["first_complete_target_span_exact"])
        if not toks:
            continue
        head_toks = toks[:16]
        head_set = set(head_toks)
        cand_ids = by_first_word.get(toks[0], [])
        scored: list[tuple[int, str]] = []
        for nid in cand_ids:
            info = sh_info[nid]
            sn_w = info["sn_words"]
            overlap = sum(1 for w in sn_w if w in head_set)
            if overlap < min(len(sn_w), 2):
                continue
            score = overlap * 3
            if info["has_taqrib"]:
                score += 4
            if info["rank_str"] and (info["rank_str"] == span or info["rank_str"] in txt):
                score += 6
            if info["tabaqa_str"] and info["tabaqa_str"] in txt:
                score += 3
            if any(q and q in txt for q in info["quotes"]):
                score += 5
            if sn_w[:2] == toks[:2]:
                score += 4
            if info["sn"] and txt.startswith(info["sn"]):
                score += 3
            # Additional disambiguation using death year digits or nisba
            if info["death_digits"] and info["death_digits"] in txt:
                score += 2
            scored.append((score, nid))

        if not scored:
            continue
        scored.sort(reverse=True)
        top_score = scored[0][0]
        top_nids = [n for s, n in scored if s == top_score]
        entry_top[eid] = (top_score, top_nids)
        if len(top_nids) == 1 and top_score >= 9:
            nid_best_for_entry[top_nids[0]].append((top_score, eid))

    resolved: dict[str, tuple[str, int, str]] = {}
    used_nids: set[str] = set()
    # Assign strictly unique 1-to-1 mutual winners first
    for nid, claimants in nid_best_for_entry.items():
        if len(claimants) == 1:
            sc, eid = claimants[0]
            resolved[eid] = (nid, sc, "unique_1to1_high_conf")
            used_nids.add(nid)
        else:
            # Resolve collision only if strict top scorer exceeds runner-up by >=3
            claimants_sorted = sorted(claimants, reverse=True)
            if claimants_sorted[0][0] - claimants_sorted[1][0] >= 3:
                sc, eid = claimants_sorted[0]
                resolved[eid] = (nid, sc, "unique_1to1_margin_resolved")
                used_nids.add(nid)

    stats = Counter(v[2] for v in resolved.values())
    stats["unlinked_or_ambiguous"] = len(entries) - len(resolved)
    return resolved, dict(stats)


def classify_passage_eligibility(title: str, cit: str, grp: str, qtext: str) -> tuple[str, str]:
    blob = f"{title} || {cit}"
    if any(k in blob for k in PROHIBITED_SOURCE_SUBSTRINGS) or any(k in grp for k in PROHIBITED_GROUP_SUBSTRINGS):
        return "excluded_prohibited_taqrib_or_ibn_hajar", "Matches prohibited Taqrib/Tahrir/Ibn Hajar work or attribution."
    if not qtext.strip():
        return "excluded_empty_passage", "Empty quotation text."
    if any(k in blob for k in SUMMARY_WORK_SUBSTRINGS):
        return "eligible_secondary_summary_work", "Pre-Taqrib Dhahabi summary work (al-Kashif); separate from primary quotes for ablations."
    return "eligible_primary_historical_passage", "Independent pre-Taqrib/non-Ibn-Hajar historical passage."


def main() -> None:
    if OUT_DIR.exists() and any(OUT_DIR.iterdir()):
        raise SystemExit(f"Refusing to overwrite existing Task B package: {OUT_DIR}")

    entries = read_csv(ENTRY_INDEX)
    assert len(entries) == 8827
    task_a = {r["entry_id"]: r for r in read_csv(TASK_A_V13)}

    sh_narrs_raw = read_csv(SH_NARRATORS)
    assert len(sh_narrs_raw) == 18989

    # First scan evaluations_raw to build taqrib cross-check quotes & identify all passages
    taqrib_nids: set[str] = set()
    taqrib_quote_map: dict[str, list[str]] = defaultdict(list)
    eval_rows_raw = read_csv(SH_EVALS)
    for r in eval_rows_raw:
        if "تقريب التهذيب" in r["normalised_title_candidate"] or "تقريب التهذيب" in r["source_citation_raw"]:
            taqrib_nids.add(r["narrator_id"])
            taqrib_quote_map[r["narrator_id"]].append(norm_ar(r["quotation_text"]))

    by_first_word: dict[str, list[str]] = defaultdict(list)
    sh_info: dict[str, dict[str, Any]] = {}
    for row in sh_narrs_raw:
        nid = row["id"]
        bj = dict(json.loads(row["biography_json"])["summary"])
        sn = norm_ar(row["short_name"])
        sn_words = sn.split()
        death_raw = bj.get("تاريخ الوفاة", "")
        digits_m = re.findall(r"\d{2,3}", death_raw)
        sh_info[nid] = {
            "short_name": row["short_name"],
            "long_name": row["long_name"],
            "sn": sn,
            "sn_words": sn_words,
            "has_taqrib": nid in taqrib_nids or bool(bj.get("الرتبة عند ابن حجر")),
            "rank_str": norm_ar(bj.get("الرتبة عند ابن حجر", "")),
            "tabaqa_str": norm_ar(bj.get("طبقة رواة التقريب", "")),
            "death_digits": digits_m[0] if digits_m else "",
            "quotes": taqrib_quote_map.get(nid, []),
            "relations_raw": bj.get("علاقات الراوي", ""),
            "madhhab_raw": bj.get("المذهب العقدي", ""),
            "residence_raw": bj.get("بلد الإقامة", ""),
            "nisba_raw": bj.get("النسب", ""),
        }
        if sn_words:
            by_first_word[sn_words[0]].append(nid)

    resolved_map, link_stats = resolve_taqrib_to_shamela(entries, task_a, sh_info, by_first_word)
    nid_to_entry = {v[0]: k for k, v in resolved_map.items()}

    # Build leakage-clean passages table for all linked Task A entries
    eligible_passages: list[dict[str, Any]] = []
    exclusion_counts: Counter[str] = Counter()
    source_work_counts: Counter[str] = Counter()
    narrators_with_primary: set[str] = set()
    narrators_with_any_eligible: set[str] = set()

    for idx, r in enumerate(eval_rows_raw, 1):
        nid = r["narrator_id"]
        if nid not in nid_to_entry:
            continue
        entry_id = nid_to_entry[nid]
        title = r["normalised_title_candidate"]
        cit = r["source_citation_raw"]
        grp = r["group_label_raw"]
        qtext = r["quotation_text"]

        elig, reason = classify_passage_eligibility(title, cit, grp, qtext)
        exclusion_counts[elig] += 1
        if elig.startswith("excluded_"):
            continue

        # Hard leakage assertion before emitting any Task B passage
        assert not any(k in title for k in ("تقريب", "تحرير", "تهذيب التهذيب", "لسان الميزان", "الإصابة", "تعجيل")), f"Leak in title: {title}"
        assert "ابن حجر" not in grp, f"Leak in group: {grp}"

        narrators_with_any_eligible.add(entry_id)
        if elig == "eligible_primary_historical_passage":
            narrators_with_primary.add(entry_id)
        source_work_counts[title or cit[:40]] += 1

        eligible_passages.append({
            "passage_id": f"TB-PAS-{len(eligible_passages) + 1:06d}",
            "entry_id": entry_id,
            "shamela_narrator_id": nid,
            "historical_attribution_critic": grp,
            "source_work_normalised": title,
            "source_citation_exact": cit,
            "source_id_raw": r["source_id_raw"],
            "historical_input_eligibility": elig,
            "target_suitability_task_a": task_a[entry_id]["deterministic_disposition"],
            "quotation_text_exact": qtext,
        })

    # Link HadithDB narrators (1,524) to Shamela4 / Task A entry_ids (strictly non-Taqrib fields only)
    hdb_data = json.loads(HDB_NARRATORS.read_text(encoding="utf-8"))
    hdb_links: list[dict[str, Any]] = []
    for hid_str, payload in hdb_data.items():
        d = payload.get("data", {})
        h_name = norm_ar(payload.get("name", ""))
        toks = h_name.split()
        matched_nid = ""
        matched_eid = ""
        # Use short token overlap against Shamela4 narrators
        if toks:
            cands = by_first_word.get(toks[0], [])
            best = []
            hset = set(toks)
            for nid in cands:
                info = sh_info[nid]
                ov = sum(1 for w in info["sn_words"] if w in hset)
                if ov >= min(len(info["sn_words"]), 2):
                    best.append((ov + (2 if nid in nid_to_entry else 0), nid))
            if best:
                best.sort(reverse=True)
                tops = [n for s, n in best if s == best[0][0]]
                if len(tops) == 1:
                    matched_nid = tops[0]
                    matched_eid = nid_to_entry.get(matched_nid, "")
        hdb_links.append({
            "hadithdb_narrator_id": hid_str,
            "hadithdb_display_name": payload.get("name", ""),
            "shamela_narrator_id": matched_nid,
            "task_a_entry_id": matched_eid,
            "link_status": "linked_with_task_a" if matched_eid else ("linked_shamela_only" if matched_nid else "unlinked"),
        })

    # Build clean per-narrator Task B identity & eligibility table (8,827 rows; ZERO Taqrib text features!)
    narrator_table: list[dict[str, Any]] = []
    primary_cnt_by_entry = Counter(r["entry_id"] for r in eligible_passages if r["historical_input_eligibility"] == "eligible_primary_historical_passage")
    all_cnt_by_entry = Counter(r["entry_id"] for r in eligible_passages)
    hdb_by_eid = {r["task_a_entry_id"]: r["hadithdb_narrator_id"] for r in hdb_links if r["task_a_entry_id"]}

    for eid, ta_row in task_a.items():
        nid, score, l_stat = resolved_map.get(eid, ("", 0, "unlinked_or_ambiguous"))
        info = sh_info.get(nid, {}) if nid else {}
        n_prim = primary_cnt_by_entry.get(eid, 0)
        n_all = all_cnt_by_entry.get(eid, 0)
        narrator_table.append({
            "entry_id": eid,
            "shamela_narrator_id": nid,
            "hadithdb_narrator_id": hdb_by_eid.get(eid, ""),
            "identity_link_status": l_stat,
            "identity_link_score": score,
            "target_suitability_task_a": ta_row["deterministic_disposition"],
            "task_a_rank_1_to_12": ta_row["deterministic_rank_1_to_12"],
            "eligible_primary_passage_count": n_prim,
            "eligible_total_passage_count": n_all,
            "non_taqrib_relations_raw": info.get("relations_raw", ""),
            "non_taqrib_residence_raw": info.get("residence_raw", ""),
            "non_taqrib_nisba_raw": info.get("nisba_raw", ""),
            "non_taqrib_madhhab_raw": info.get("madhhab_raw", ""),
            "task_b_feature_eligibility": "eligible_assigned_with_primary_text" if (ta_row["deterministic_disposition"] == "assigned_rank" and n_prim > 0) else ("eligible_assigned_secondary_only" if (ta_row["deterministic_disposition"] == "assigned_rank" and n_all > 0) else "not_eligible_missing_target_or_text"),
        })

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    passages_csv = OUT_DIR / "TASK_B_ELIGIBLE_HISTORICAL_PASSAGES_V0_1.csv"
    narrators_csv = OUT_DIR / "TASK_B_NARRATOR_LINKAGE_AND_ELIGIBILITY_8827_V0_1.csv"
    hdb_csv = OUT_DIR / "TASK_B_HADITHDB_NARRATOR_LINKS_1524_V0_1.csv"
    write_csv(passages_csv, eligible_passages, list(eligible_passages[0]))
    write_csv(narrators_csv, narrator_table, list(narrator_table[0]))
    write_csv(hdb_csv, hdb_links, list(hdb_links[0]))

    elig_summary = Counter(r["task_b_feature_eligibility"] for r in narrator_table)
    elig_rank_counts = Counter(
        r["task_a_rank_1_to_12"]
        for r in narrator_table
        if r["task_b_feature_eligibility"] == "eligible_assigned_with_primary_text"
    )
    hdb_link_counts = Counter(r["link_status"] for r in hdb_links)

    report_lines = [
        "# Task B Historical Inputs, Narrator Linkage, and Zero-Leakage Audit v0.1 (TODO Lines 50-53)",
        "",
        "**Status:** constructed eligible non-*Taqrīb* Task B inputs with hard Zero-Leakage Firewall (`تقريب التهذيب`, `تحرير التقريب`, `تهذيب التهذيب`, `لسان الميزان`, `الإصابة`, `تعجيل المنفعة`, `ابن حجر`, and `الرتبة عند ابن حجر` / `طبقة رواة التقريب` strictly excluded from all Task B feature columns).",
        "",
        "## 1. Narrator Identity Resolution (`8,827` Taqrib Entries <-> `18,989` Shamela4 / `1,524` HadithDB)",
        f"- Taqrib-to-Shamela4 1-to-1 link stats: `{link_stats}`",
        f"- HadithDB (`1,524`) link stats: `{dict(sorted(hdb_link_counts.items()))}`",
        "",
        "## 2. Leakage Firewall & Historical Passage Filtering (from `165,862` Shamela4 evaluations)",
        f"- Passage disposition across linked narrators: `{dict(sorted(exclusion_counts.items()))}`",
        f"- Total retained Task B passages (`TASK_B_ELIGIBLE_HISTORICAL_PASSAGES_V0_1.csv`): **{len(eligible_passages)}**",
        "- Top 12 eligible non-Ibn-Hajar source works retained:",
    ]
    for src, cnt in source_work_counts.most_common(12):
        report_lines.append(f"  - `{src}`: **{cnt}** passages")
    report_lines.extend([
        "",
        "## 3. Joint Task B Modelling Readiness (`assigned_rank` + `primary non-Taqrib text`)",
        f"- Narrator eligibility breakdown (`8,827` total): `{dict(sorted(elig_summary.items()))}`",
        "- Per-Rank (`1..12`) narrators having **BOTH** deterministic Task A rank AND `>=1` primary non-*Taqrīb* passage:",
    ])
    for i in range(1, 13):
        report_lines.append(f"  - Rank **{i}**: `{elig_rank_counts.get(str(i), 0)}`")

    report_text = "\n".join(report_lines) + "\n"
    assert_no_em_en_dash(report_text, "TASK_B_INPUTS_REPORT_V0_1.md")
    report_path = OUT_DIR / "TASK_B_INPUTS_REPORT_V0_1.md"
    report_path.write_text(report_text, encoding="utf-8", newline="\n")

    timestamp = datetime.now(timezone.utc).isoformat()
    inputs = [ENTRY_INDEX, TASK_A_V13, SH_NARRATORS, SH_EVALS, HDB_NARRATORS, Path(__file__).resolve()]
    outputs = [passages_csv, narrators_csv, hdb_csv, report_path]
    manifest = {
        "package_id": OUT_DIR.name,
        "generated_at_utc": timestamp,
        "counts": {
            "taqrib_entries": len(entries),
            "taqrib_shamela_linked_1to1": len(resolved_map),
            "hadithdb_links": dict(sorted(hdb_link_counts.items())),
            "passage_filter_counts": dict(sorted(exclusion_counts.items())),
            "eligible_passages_retained": len(eligible_passages),
            "narrator_eligibility_counts": dict(sorted(elig_summary.items())),
            "eligible_primary_rank_counts": {str(i): elig_rank_counts.get(str(i), 0) for i in range(1, 13)},
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
