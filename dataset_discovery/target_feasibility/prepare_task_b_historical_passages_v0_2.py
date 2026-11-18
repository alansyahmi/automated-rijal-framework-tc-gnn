#!/usr/bin/env python3
"""Prepare Task B non-Taqrib historical passages, upgraded 1-to-1 narrator links, and zero-leakage firewall v0.2.

Upgrades v0.1 entity resolution while keeping v0.1 untouched:
1. Indexes Shamela4 narrators across non-particle given/father name tokens
   (fixing kunya-first headings like 'أبو عبد الملك أحمد بن إبراهيم').
2. Scores candidates using kunya, nisba, death-year digits, ordered bigrams,
   and cross-verified Taqrib rank/tabaqa/quote checks, solved via greedy 1-to-1
   bipartite assignment ordered by descending confidence score.
3. Links HadithDB narrators (1,524) using structured data['الاسم'] + Kunya +
   Nisba + Death Date rather than raw display header alone.

Enforces the exact same Zero-Leakage Firewall: rejects ALL Taqrib, Tahrir, and
Ibn Hajar works/attributions from Task B passage and metadata features.
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
OUT_DIR = PIPELINE / "task_b_historical_inputs_v0_2_2026-11-17"

DIACRITICS_RE = re.compile(r"[\u064b-\u065f\u0670\u0640\u200c]")
STOP_NAME_TOKS = {"ابن", "ابو", "ابي", "ام", "بنت", "بن", "عبد", "مولى", "ال", "في", "عن"}
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


def resolve_taqrib_to_shamela_v2(
    entries: list[dict[str, str]],
    task_a: dict[str, dict[str, str]],
    sh_info: dict[str, dict[str, Any]],
    tok_index: dict[str, list[str]],
) -> tuple[dict[str, tuple[str, int, str]], dict[str, int]]:
    pairs: list[tuple[int, str, str]] = []

    for e in entries:
        eid = e["entry_id"]
        txt = norm_ar(e["entry_text_verbatim"])
        toks = [w for w in txt.split() if not w.isdigit() and w not in DABT_WORDS]
        if not toks:
            continue
        span = norm_ar(task_a[eid]["first_complete_target_span_exact"])
        head_toks = toks[:18]
        head_set = set(head_toks)
        head_bigrams = set(zip(head_toks, head_toks[1:]))
        is_tamiz = "تمييز" in txt

        # Gather candidate Shamela4 IDs sharing >=1 key non-stop token in the first 5 name tokens
        key_toks = [w for w in head_toks[:6] if w not in STOP_NAME_TOKS and len(w) >= 2]
        cand_counts: Counter[str] = Counter()
        for kt in key_toks[:4]:
            for nid in tok_index.get(kt, ()):
                cand_counts[nid] += 1

        # Evaluate top candidates sharing >=2 name tokens (or >=1 for single-word rare names)
        min_hits = 2 if len(key_toks) >= 2 else 1
        cands = [nid for nid, cnt in cand_counts.items() if cnt >= min_hits]
        if not cands and key_toks:
            cands = tok_index.get(key_toks[0], [])[:250]

        for nid in cands:
            info = sh_info[nid]
            sn_w = info["sn_words"]
            key_sn = info["sn_key_words"]
            if not key_sn:
                continue
            key_overlap = sum(1 for w in key_sn if w in head_set)
            if key_overlap == 0:
                continue
            if len(key_sn) >= 2 and key_overlap < 2 and key_sn[0] != head_toks[0]:
                continue

            score = key_overlap * 4
            # Bigram continuity boost
            score += sum(3 for bg in zip(sn_w, sn_w[1:]) if bg in head_bigrams)
            if info["has_taqrib"]:
                score += 6
            if info["rank_str"] and (info["rank_str"] == span or info["rank_str"] in txt):
                score += 7
            if info["tabaqa_str"] and info["tabaqa_str"] in txt:
                score += 3
            if any(q and q in txt for q in info["quotes"]):
                score += 6
            if info["kunya_norm"] and info["kunya_norm"] in txt:
                score += 3
            nisba_hits = sum(1 for nw in info["nisba_words"] if nw in txt)
            score += min(nisba_hits, 3) * 2
            if info["death_digits"] and info["death_digits"] in txt:
                score += 3
            # Penalize matching a non-tamiz Shamela entry onto a tamiz entry if non-tamiz has rank mismatch
            if is_tamiz and info["rank_str"] and info["rank_str"] not in txt:
                score -= 4
            if score >= 13:
                pairs.append((score, eid, nid))

    # Global greedy 1-to-1 matching by highest confidence score
    pairs.sort(key=lambda x: (-x[0], x[1], x[2]))
    resolved: dict[str, tuple[str, int, str]] = {}
    used_entries: set[str] = set()
    used_nids: set[str] = set()

    for sc, eid, nid in pairs:
        if eid in used_entries or nid in used_nids:
            continue
        used_entries.add(eid)
        used_nids.add(nid)
        tier = "unique_1to1_high_conf" if sc >= 20 else "unique_1to1_standard"
        resolved[eid] = (nid, sc, tier)

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
        raise SystemExit(f"Refusing to overwrite existing Task B v0.2 directory: {OUT_DIR}")

    entries = read_csv(ENTRY_INDEX)
    assert len(entries) == 8827
    task_a = {r["entry_id"]: r for r in read_csv(TASK_A_V13)}
    sh_narrs_raw = read_csv(SH_NARRATORS)
    assert len(sh_narrs_raw) == 18989

    taqrib_nids: set[str] = set()
    taqrib_quote_map: dict[str, list[str]] = defaultdict(list)
    eval_rows_raw = read_csv(SH_EVALS)
    for r in eval_rows_raw:
        if "تقريب التهذيب" in r["normalised_title_candidate"] or "تقريب التهذيب" in r["source_citation_raw"]:
            taqrib_nids.add(r["narrator_id"])
            taqrib_quote_map[r["narrator_id"]].append(norm_ar(r["quotation_text"]))

    tok_index: dict[str, list[str]] = defaultdict(list)
    sh_info: dict[str, dict[str, Any]] = {}
    for row in sh_narrs_raw:
        nid = row["id"]
        bj = dict(json.loads(row["biography_json"])["summary"])
        sn = norm_ar(row["short_name"])
        ln = norm_ar(row["long_name"])
        sn_words = sn.split()
        sn_key_words = [w for w in sn_words if w not in STOP_NAME_TOKS and len(w) >= 2]
        kunya_norm = norm_ar(bj.get("الكنية", ""))
        nisba_raw = bj.get("النسب", "")
        nisba_words = [w for w in norm_ar(nisba_raw).split() if len(w) >= 3]
        death_raw = bj.get("تاريخ الوفاة", "")
        digits_m = re.findall(r"\d{2,3}", death_raw)

        sh_info[nid] = {
            "short_name": row["short_name"],
            "sn": sn,
            "sn_words": sn_words,
            "sn_key_words": sn_key_words,
            "has_taqrib": nid in taqrib_nids or bool(bj.get("الرتبة عند ابن حجر")),
            "rank_str": norm_ar(bj.get("الرتبة عند ابن حجر", "")),
            "tabaqa_str": norm_ar(bj.get("طبقة رواة التقريب", "")),
            "kunya_norm": kunya_norm,
            "nisba_words": nisba_words,
            "death_digits": digits_m[0] if digits_m else "",
            "quotes": taqrib_quote_map.get(nid, []),
            "relations_raw": bj.get("علاقات الراوي", ""),
            "madhhab_raw": bj.get("المذهب العقدي", ""),
            "residence_raw": bj.get("بلد الإقامة", ""),
            "nisba_raw": nisba_raw,
        }
        seen_t: set[str] = set()
        for tok in sn_key_words + [w for w in ln.split()[:6] if w not in STOP_NAME_TOKS and len(w) >= 2]:
            if tok not in seen_t:
                tok_index[tok].append(nid)
                seen_t.add(tok)

    resolved_map, link_stats = resolve_taqrib_to_shamela_v2(entries, task_a, sh_info, tok_index)
    nid_to_entry = {v[0]: k for k, v in resolved_map.items()}

    eligible_passages: list[dict[str, Any]] = []
    exclusion_counts: Counter[str] = Counter()
    source_work_counts: Counter[str] = Counter()

    for r in eval_rows_raw:
        nid = r["narrator_id"]
        if nid not in nid_to_entry:
            continue
        entry_id = nid_to_entry[nid]
        title = r["normalised_title_candidate"]
        cit = r["source_citation_raw"]
        grp = r["group_label_raw"]
        qtext = r["quotation_text"]

        elig, _ = classify_passage_eligibility(title, cit, grp, qtext)
        exclusion_counts[elig] += 1
        if elig.startswith("excluded_"):
            continue

        assert not any(k in title for k in ("تقريب", "تحرير", "تهذيب التهذيب", "لسان الميزان", "الإصابة", "تعجيل")), f"Leak in title: {title}"
        assert "ابن حجر" not in grp, f"Leak in group: {grp}"
        source_work_counts[title or cit[:40]] += 1

        eligible_passages.append({
            "passage_id": f"TB2-PAS-{len(eligible_passages) + 1:06d}",
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

    # Link HadithDB narrators (1,524) using data['الاسم'] + الكنية + النسب + تاريخ الوفاة
    hdb_data = json.loads(HDB_NARRATORS.read_text(encoding="utf-8"))
    hdb_pairs: list[tuple[int, str, str]] = []
    for hid_str, payload in hdb_data.items():
        d = payload.get("data", {})
        ism_norm = norm_ar(d.get("الاسم", "") or payload.get("name", ""))
        full_blob = norm_ar(" ".join([payload.get("name", ""), d.get("الاسم", ""), d.get("الكنية", ""), d.get("النسب", ""), d.get("تاريخ الوفاة", "")]))
        blob_set = set(full_blob.split())
        key_toks = [w for w in ism_norm.split()[:6] if w not in STOP_NAME_TOKS and len(w) >= 2]
        cand_counts: Counter[str] = Counter()
        for kt in key_toks[:4]:
            for nid in tok_index.get(kt, ()):
                cand_counts[nid] += 1
        for nid, ov_cnt in cand_counts.most_common(40):
            info = sh_info[nid]
            ov = sum(1 for w in info["sn_key_words"] if w in blob_set)
            if ov < min(len(info["sn_key_words"]), 2):
                continue
            sc = ov * 4
            if info["kunya_norm"] and info["kunya_norm"] in full_blob:
                sc += 3
            sc += min(sum(1 for nw in info["nisba_words"] if nw in full_blob), 3) * 2
            if info["death_digits"] and info["death_digits"] in full_blob:
                sc += 3
            if nid in nid_to_entry:
                sc += 3
            if sc >= 10:
                hdb_pairs.append((sc, hid_str, nid))

    hdb_pairs.sort(key=lambda x: (-x[0], x[1], x[2]))
    used_hdb: set[str] = set()
    used_hdb_nids: set[str] = set()
    hdb_matched: dict[str, tuple[str, int]] = {}
    for sc, hid_str, nid in hdb_pairs:
        if hid_str in used_hdb or nid in used_hdb_nids:
            continue
        used_hdb.add(hid_str)
        used_hdb_nids.add(nid)
        hdb_matched[hid_str] = (nid, sc)

    hdb_links: list[dict[str, Any]] = []
    for hid_str, payload in hdb_data.items():
        matched_nid, sc = hdb_matched.get(hid_str, ("", 0))
        matched_eid = nid_to_entry.get(matched_nid, "") if matched_nid else ""
        hdb_links.append({
            "hadithdb_narrator_id": hid_str,
            "hadithdb_display_name": payload.get("name", ""),
            "shamela_narrator_id": matched_nid,
            "task_a_entry_id": matched_eid,
            "link_score": sc,
            "link_status": "linked_with_task_a" if matched_eid else ("linked_shamela_only" if matched_nid else "unlinked"),
        })

    primary_cnt_by_entry = Counter(r["entry_id"] for r in eligible_passages if r["historical_input_eligibility"] == "eligible_primary_historical_passage")
    all_cnt_by_entry = Counter(r["entry_id"] for r in eligible_passages)
    hdb_by_eid = {r["task_a_entry_id"]: r["hadithdb_narrator_id"] for r in hdb_links if r["task_a_entry_id"]}

    narrator_table: list[dict[str, Any]] = []
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
    passages_csv = OUT_DIR / "TASK_B_ELIGIBLE_HISTORICAL_PASSAGES_V0_2.csv"
    narrators_csv = OUT_DIR / "TASK_B_NARRATOR_LINKAGE_AND_ELIGIBILITY_8827_V0_2.csv"
    hdb_csv = OUT_DIR / "TASK_B_HADITHDB_NARRATOR_LINKS_1524_V0_2.csv"
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
        "# Task B Historical Inputs, Narrator Linkage, and Zero-Leakage Audit v0.2 (TODO Lines 50-53)",
        "",
        "**Status:** upgraded 1-to-1 global bipartite entity resolution (`8,827` Taqrib entries <-> `18,989` Shamela4 / `1,524` HadithDB) with strict Task B Zero-Leakage Firewall (`تقريب التهذيب`, `تحرير التقريب`, `تهذيب التهذيب`, `لسان الميزان`, `الإصابة`, `تعجيل المنفعة`, `ابن حجر`, `الرتبة عند ابن حجر`, `طبقة رواة التقريب` strictly excluded).",
        "",
        "## 1. Narrator Identity Resolution",
        f"- Taqrib-to-Shamela4 1-to-1 link stats: `{link_stats}`",
        f"- HadithDB (`1,524`) link stats: `{dict(sorted(hdb_link_counts.items()))}`",
        "",
        "## 2. Leakage Firewall & Historical Passage Filtering",
        f"- Passage disposition across linked narrators: `{dict(sorted(exclusion_counts.items()))}`",
        f"- Total retained Task B passages: **{len(eligible_passages)}**",
        "- Top 10 retained non-Ibn-Hajar source works:",
    ]
    for src, cnt in source_work_counts.most_common(10):
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
    assert_no_em_en_dash(report_text, "TASK_B_INPUTS_REPORT_V0_2.md")
    report_path = OUT_DIR / "TASK_B_INPUTS_REPORT_V0_2.md"
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
