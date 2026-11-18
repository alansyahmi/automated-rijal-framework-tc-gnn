"""v1.2 Stage 1 & Stage 3 Data, Provenance, Contamination, and Feasibility Audit.

Strict Constraints Obeyed:
- Read-only audit: does NOT modify v1.0, v1.1, audit_v1_1, splits, or frozen packages.
- Zero test-set peeking: held-out test rows (split == 'test') are EXCLUDED from all
  label/rank-conditioned diagnostics, contamination snippets, and critic-stance analyses.
- Cohort-wide checks report only label-agnostic technical metadata (total book entries,
  unique vs ambiguous header match counts, and raw page/footnote contamination scan).
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PIPELINE_DIR = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline"
V03_INPUT_DIR = PIPELINE_DIR / "task_b_historical_inputs_v0_3_2026-11-17"
V04_INPUT_DIR = PIPELINE_DIR / "task_b_historical_inputs_v0_4_2026-11-17"
V03_GRAPH_DIR = PIPELINE_DIR / "task_b_consolidated_graph_v0_3_2026-11-17"
SH_NARRATORS = ROOT / "data/2_interim/shamela4_narrator_audit/narrators.csv"
SHAMELA_BOOKS_DIR = ROOT / "data/1_raw/Shamela4_Full_DB/26__التراجم-والطبقات"
OUT_DIR = ROOT / "results/v1_2_stage1_data_audit_2026-11-18"

DIACRITICS_RE = re.compile(r"[\u064b-\u065f\u0670\u0640\u200c]")
STOP_TOKS = {"ابن", "ابو", "ابي", "ابا", "ام", "بنت", "بن", "عبد", "مولى", "ال", "في", "عن", "من"}

BOOKS_SPEC = [
    (
        "1716",
        "method1_tahdhib_alkamal",
        re.compile(
            r'(?:^|\r|\n)(?:[٠-٩\d]+\s*-\s*(?:[^:\r\n<]{0,14}:?\s*)?(?:<span[^>]*data-type=[\'"]title[\'"][^>]*>([^<]{3,140})</span>|([^\r\n.<]{4,120}))|<span[^>]*data-type=[\'"]title[\'"][^>]*>([^<]{3,140})</span>)'
        ),
    ),
    (
        "1615",
        "method1_jarh_tadil",
        re.compile(r"(?:^|\r|\n)[٠-٩\d]+\s*-\s*([^\r\n]{4,160})"),
    ),
    (
        "1976",
        "method1_thiqat_ibn_hibban",
        re.compile(r"(?:^|\r|\n)\u2022\s+([^\r\n]{4,160})"),
    ),
    (
        "890",
        "method1_tarikh_kabir",
        re.compile(
            r'<span[^>]*data-type=[\'"]title[\'"][^>]*>\s*(?:[٠-٩\d]+\s*-\s*)?([^<]{4,160})</span>'
        ),
    ),
    (
        "1981",
        "method1_thiqat_ijli",
        re.compile(r"(?:^|\r|\n)[٠-٩\d]+\s*-\s*([^\r\n]{4,140})"),
    ),
    (
        "4609",
        "method1_kamil",
        re.compile(
            r'<span[^>]*data-type=[\'"]title[\'"][^>]*>\s*(?:[٠-٩\d]+\s*-\s*)?([^<]{4,160})</span>'
        ),
    ),
]

CONTAMINATION_TERMS = [
    ("ibn_hajar", "ابن حجر"),
    ("taqrib", "تقريب"),
    ("tahrir", "تحرير"),
    ("tahdhib_al_tahdhib", "تهذيب التهذيب"),
    ("al_hafiz", "الحافظ"),
    ("al_dhahabi", "الذهبي"),
    ("al_kashif", "الكاشف"),
    ("bashar_awwad", "بشار"),
    ("al_muallimi", "المعلمي"),
    ("al_albani", "الألباني"),
    ("shuayb", "شعيب"),
    ("al_muhaqqiq", "المحقق"),
]

PRAISE_CUES = ("ثقة", "ثبت", "حجة", "صدوق", "لا بأس به", "ليس به بأس", "مأمون", "إمام", "حافظ", "صالح الحديث")
CRIT_CUES = ("ضعيف", "متروك", "كذاب", "يضع", "وضاع", "منكر الحديث", "ليس بشيء", "لا يكتب حديثه", "واهي", "مجهول", "متهم")
MIXED_QUAL_CUES = ("يهم", "يخطئ", "له أوهام", "لين", "فيه نظر", "مختلف فيه", "مستور", "لا يعرف", "روى عنه جماعة", "لم يرو عنه غير")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def norm_ar(text: str) -> str:
    s = DIACRITICS_RE.sub("", text)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\[[^\]]*\]|\([^\)]*\)", " ", s)
    s = s.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ى", "ي").replace("ة", "ه")
    s = re.sub(r"\bبن\b", "ابن", s)
    s = re.sub(r"\b(?:ابا|ابي)\b", "ابو", s)
    s = re.sub(r"[^\w\u0621-\u064a\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def norm_ar_text_keep_punct(text: str) -> str:
    s = DIACRITICS_RE.sub("", text)
    s = s.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ى", "ي")
    return re.sub(r"\s+", " ", s).strip()


def extract_ism_father_key(tokens: list[str]) -> str:
    if not tokens:
        return ""
    ism = tokens[0]
    idx = 1
    if ism in {"عبد", "ابو", "ام", "ابن"} and idx < len(tokens):
        ism = f"{ism} {tokens[idx]}"
        idx += 1
    father = ""
    while idx < len(tokens) and idx < 6:
        t = tokens[idx]
        if t in {"ابن", "بنت"} and idx + 1 < len(tokens):
            nxt = tokens[idx + 1]
            father = f"{nxt} {tokens[idx + 2]}" if nxt in {"ابو", "ام", "عبد"} and idx + 2 < len(tokens) else nxt
            break
        if t not in STOP_TOKS and len(t) >= 2:
            father = t
            break
        idx += 1
    return f"{ism} {father}".strip() if father else ism


def build_name_lookup(sh_raw: list[dict[str, str]], cohort_rows: list[dict[str, str]]):
    nid_to_eid = {r["shamela_narrator_id"]: r["entry_id"] for r in cohort_rows}
    all_key_eids: defaultdict[str, set[str]] = defaultdict(set)
    for sr in sh_raw:
        sn = norm_ar(sr["short_name"])
        toks = sn.split()
        if len(toks) < 2:
            continue
        if_key = extract_ism_father_key(toks)
        nid = sr["id"]
        if nid in nid_to_eid:
            eid = nid_to_eid[nid]
            all_key_eids[sn].add(eid)
            all_key_eids[if_key].add(eid)
            if len(toks) >= 3:
                all_key_eids[" ".join(toks[:3])].add(eid)
            bj = dict(json.loads(sr["biography_json"])["summary"])
            for field in ("الشهرة", "الكنية"):
                val = norm_ar(bj.get(field, ""))
                if val and len(val) >= 4:
                    all_key_eids[val].add(eid)
        else:
            all_key_eids[sn].add(f"SH-{nid}")
            all_key_eids[if_key].add(f"SH-{nid}")

    unique_exact: dict[str, str] = {}
    cand_map: dict[str, set[str]] = {}
    for name_key, id_set in all_key_eids.items():
        ta_ids = {x for x in id_set if not x.startswith("SH-")}
        if len(id_set) == 1 and len(ta_ids) == 1:
            unique_exact[name_key] = next(iter(ta_ids))
        elif ta_ids and len(ta_ids) <= 8:
            cand_map[name_key] = ta_ids
    return unique_exact, cand_map


def resolve_mention_tokens(clean_name: str, unique_exact: dict[str, str], cand_map: dict[str, set[str]]):
    if not clean_name:
        return "", set(), "empty"
    if clean_name in unique_exact:
        return unique_exact[clean_name], {unique_exact[clean_name]}, "unique_exact"
    toks = clean_name.split()
    if_key = extract_ism_father_key(toks)
    tries = [clean_name]
    if len(toks) >= 4:
        tries.append(" ".join(toks[:4]))
    if len(toks) >= 3:
        tries.append(" ".join(toks[:3]))
    if if_key and if_key not in tries:
        tries.append(if_key)
    if len(toks) >= 3 and toks[-1].startswith("ال"):
        tries.append(" ".join(toks[:-1]))

    for k in tries:
        if k in unique_exact:
            return unique_exact[k], {unique_exact[k]}, "unique_fallback"
    for k in tries:
        if k in cand_map:
            return "", cand_map[k], "ambiguous_candidate"
    return "", set(), "unmatched"


def clean_book_header_name(raw_hdr: str) -> str:
    s = re.sub(r"^[\s٠-٩\d\-:\.•()]+", "", raw_hdr)
    s = re.split(
        r"(?:[،,\.]|\s+(?:روى\s+عن|رَوَى\s+عَن|يروي\s+عن|يَرْوِي\s+عَن|سمع\s+|سَمِعَ\s+|يعد\s+في|عداده\s+في|حدثنا\s+|ثقة\b|صدوق\b|مجهول\b|ضعيف\b|متروك\b))",
        s,
        maxsplit=1,
    )[0]
    return norm_ar(s)


def strip_inline_footnotes_and_tags(raw_entry: str) -> tuple[str, int, int]:
    """Heuristic test: separate main text from inline footnote markers like _________ or <span data-type="fn">."""
    fn_chars = 0
    lines = raw_entry.splitlines()
    clean_lines = []
    in_fn = False
    for ln in lines:
        s = ln.strip()
        if re.match(r"^[_\-ـ]{4,}$", s):
            in_fn = True
            fn_chars += len(ln)
            continue
        if in_fn:
            # Resume main narrative if next numbered/header or blank line followed by body?
            # In Shamela pages, footnotes sit at bottom of a page until page separator!
            if "__PAGE_BREAK__" in ln:
                in_fn = False
            else:
                fn_chars += len(ln)
            continue
        clean_lines.append(ln)
    joined = "\n".join(clean_lines).replace("__PAGE_BREAK__", "\n")
    joined_no_html = re.sub(r"<[^>]+>", " ", joined)
    joined_no_html = re.sub(r"\s+", " ", joined_no_html).strip()
    return joined_no_html, fn_chars, len(raw_entry)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with (V03_GRAPH_DIR / "TASK_B_NODE_STRUCTURAL_FEATURES_V0_3.csv").open(
        encoding="utf-8-sig", newline=""
    ) as f:
        cohort_rows = list(csv.DictReader(f))
    assert len(cohort_rows) == 5250

    cohort_by_eid = {r["entry_id"]: r for r in cohort_rows}
    dev_eids = {r["entry_id"] for r in cohort_rows if r["split"] in {"train", "val"}}
    test_eids = {r["entry_id"] for r in cohort_rows if r["split"] == "test"}
    assert len(dev_eids) == 4462 and len(test_eids) == 788

    with SH_NARRATORS.open(encoding="utf-8-sig", newline="") as f:
        sh_raw = list(csv.DictReader(f))
    unique_exact, cand_map = build_name_lookup(sh_raw, cohort_rows)

    # Load existing v0.3 + v0.4 text coverage strictly for novelty/length comparison on dev_eids
    existing_dev_texts: defaultdict[str, list[str]] = defaultdict(list)
    v03_dev_passages = []
    with (V03_INPUT_DIR / "TASK_B_ELIGIBLE_HISTORICAL_PASSAGES_V0_3.csv").open(
        encoding="utf-8-sig", newline=""
    ) as f:
        for r in csv.DictReader(f):
            if r["entry_id"] in dev_eids:
                existing_dev_texts[r["entry_id"]].append(r["quotation_text_exact"])
                v03_dev_passages.append(r)

    with (V04_INPUT_DIR / "TASK_B_FWAED_PASSAGES_V0_4.csv").open(
        encoding="utf-8-sig", newline=""
    ) as f:
        for r in csv.DictReader(f):
            if r["entry_id"] in dev_eids:
                existing_dev_texts[r["entry_id"]].append(r["fwaed_text_exact"])

    v04_abl_dev_passages = []
    with (V04_INPUT_DIR / "TASK_B_EARLY_SPEAKER_ABLATION_PASSAGES_V0_4.csv").open(
        encoding="utf-8-sig", newline=""
    ) as f:
        for r in csv.DictReader(f):
            if r["entry_id"] in dev_eids:
                existing_dev_texts[r["entry_id"]].append(r["quotation_text_exact"])
                v04_abl_dev_passages.append(r)

    # Stage 1 Audit across all 6 Method 1 books
    book_audits = []
    cohort_book_hits: defaultdict[str, set[str]] = defaultdict(set)
    dev_book_lengths: defaultdict[tuple[str, str], list[int]] = defaultdict(list)
    dev_contamination_samples: list[dict[str, str]] = []
    dev_rank7_samples: list[dict[str, str]] = []

    for prefix, src_label, hdr_re in BOOKS_SPEC:
        book_dir = next(SHAMELA_BOOKS_DIR.glob(prefix + "__*"))
        meta = json.loads((book_dir / "book_metadata.json").read_text(encoding="utf-8"))

        pages = []
        nonempty_body_pages = 0
        nonempty_foot_pages = 0
        body_sep_pages = 0
        with (book_dir / "pages.jsonl").open(encoding="utf-8") as f:
            for line in f:
                p = json.loads(line)
                pages.append(p)
                b = p.get("body") or ""
                ft = p.get("footnotes") or ""
                if b.strip():
                    nonempty_body_pages += 1
                if str(ft).strip():
                    nonempty_foot_pages += 1
                if re.search(r"(?:^|\n)[_\-ـ]{4,}(?:\r|\n|$)", b):
                    body_sep_pages += 1

        full_text_marked = "\n__PAGE_BREAK__\n".join((p.get("body") or "") for p in pages)
        hdrs = list(hdr_re.finditer(full_text_marked))

        status_counts = Counter()
        total_raw_headers = 0
        over_5000_raw = 0
        contam_raw_hits = Counter()
        contam_stripped_hits = Counter()
        entry_len_clean = []
        matched_unique_eids = set()

        for idx, hm in enumerate(hdrs):
            raw_hdr = next((g for g in hm.groups() if g), "")
            if not raw_hdr or any(
                skip in raw_hdr for skip in ("باب", "المجلد", "مقدمة", "خطبة", "حرف ", "كتاب ")
            ):
                continue
            total_raw_headers += 1
            hdr_norm = clean_book_header_name(raw_hdr)
            subj_eid, cands, status = resolve_mention_tokens(hdr_norm, unique_exact, cand_map)
            status_counts[status] += 1
            if not subj_eid:
                continue

            matched_unique_eids.add(subj_eid)
            cohort_book_hits[src_label].add(subj_eid)

            start_pos = hm.start() if prefix in {"1615", "1976", "1981"} else hm.end()
            end_pos = hdrs[idx + 1].start() if idx + 1 < len(hdrs) else min(len(full_text_marked), start_pos + 15000)
            raw_body = full_text_marked[start_pos:end_pos]
            if len(raw_body) > 5000:
                over_5000_raw += 1

            clean_body, fn_chars, raw_len = strip_inline_footnotes_and_tags(raw_body)
            entry_len_clean.append(len(clean_body))

            raw_norm_keep = norm_ar_text_keep_punct(re.sub(r"<[^>]+>", " ", raw_body))
            clean_norm_keep = norm_ar_text_keep_punct(clean_body)

            for cname, cterm in CONTAMINATION_TERMS:
                ct_n = norm_ar_text_keep_punct(cterm)
                if ct_n in raw_norm_keep:
                    contam_raw_hits[cname] += 1
                    if len(dev_contamination_samples) < 18 and subj_eid in dev_eids and cname in {"ibn_hajar", "taqrib", "tahrir", "bashar_awwad"}:
                        pos = raw_norm_keep.find(ct_n)
                        snippet = raw_norm_keep[max(0, pos - 60) : min(len(raw_norm_keep), pos + 120)]
                        dev_contamination_samples.append({
                            "book": src_label,
                            "term": cname,
                            "dev_entry_id": subj_eid,
                            "in_stripped_body": str(ct_n in clean_norm_keep),
                            "snippet": snippet,
                        })
                if ct_n in clean_norm_keep:
                    contam_stripped_hits[cname] += 1

            # Dev-only length & Rank 7 sample check (ZERO test set access!)
            if subj_eid in dev_eids:
                dev_book_lengths[(src_label, cohort_by_eid[subj_eid]["task_a_rank_1_to_12"])].append(len(clean_body))
                if (
                    cohort_by_eid[subj_eid]["task_a_rank_1_to_12"] == "7"
                    and cohort_by_eid[subj_eid]["has_early_critic_quote"] == "0"
                    and len(dev_rank7_samples) < 8
                ):
                    dev_rank7_samples.append({
                        "dev_entry_id": subj_eid,
                        "book": src_label,
                        "clean_len": str(len(clean_body)),
                        "clean_preview": clean_body[:260],
                    })

        # Cohort-wide & ZQ coverage (label-agnostic metadata only; rank-level uses dev_eids only!)
        zq_all = {eid for eid, r in cohort_by_eid.items() if r["has_early_critic_quote"] == "0"}
        zq_matched = matched_unique_eids & zq_all
        dev_matched = matched_unique_eids & dev_eids
        dev_zq = {eid for eid in dev_eids if cohort_by_eid[eid]["has_early_critic_quote"] == "0"}
        dev_zq_matched = matched_unique_eids & dev_zq

        book_audits.append({
            "prefix": prefix,
            "source_label": src_label,
            "folder_name": book_dir.name,
            "title_ar": meta.get("title_ar"),
            "author_ar": meta.get("main_author_name_ar"),
            "death_hijri": meta.get("main_author_death_hijri"),
            "betaka_text": meta.get("betaka_text", "").replace("\r", " | "),
            "pages_jsonl_size_mb": round((book_dir / "pages.jsonl").stat().st_size / (1024 * 1024), 2),
            "total_pages": len(pages),
            "nonempty_body_pages": nonempty_body_pages,
            "nonempty_footnotes_field_pages": nonempty_foot_pages,
            "pages_with_inline_footnote_separator": body_sep_pages,
            "parsed_non_heading_entries": total_raw_headers,
            "link_status_counts": dict(status_counts),
            "unique_cohort_5250_narrators_linked": len(matched_unique_eids),
            "cohort_5250_coverage_pct": round(100.0 * len(matched_unique_eids) / 5250.0, 2),
            "cohort_zero_quote_420_linked": len(zq_matched),
            "dev_4462_linked": len(dev_matched),
            "dev_zero_quote_357_linked": len(dev_zq_matched),
            "entries_exceeding_5000_raw_chars": over_5000_raw,
            "clean_entry_char_len_median": int(np.median(entry_len_clean)) if entry_len_clean else 0,
            "clean_entry_char_len_p90": int(np.percentile(entry_len_clean, 90)) if entry_len_clean else 0,
            "contamination_raw_entry_hits": dict(contam_raw_hits),
            "contamination_after_sep_strip_hits": dict(contam_stripped_hits),
        })
        print(
            f"[stage1] {src_label}: pages={len(pages)} | inline_fn_sep_pages={body_sep_pages} | "
            f"linked_5250={len(matched_unique_eids)}/5250 | raw_taqrib={contam_raw_hits.get('taqrib', 0)} -> stripped={contam_stripped_hits.get('taqrib', 0)} | "
            f"raw_ibn_hajar={contam_raw_hits.get('ibn_hajar', 0)} -> stripped={contam_stripped_hits.get('ibn_hajar', 0)}",
            flush=True,
        )

    # Combined 6-book coverage across cohort (5250) and dev R7 vs R9 breakdown (train+val ONLY!)
    union_5250 = set().union(*cohort_book_hits.values())
    zq_5250 = {eid for eid, r in cohort_by_eid.items() if r["has_early_critic_quote"] == "0"}
    union_zq = union_5250 & zq_5250

    dev_rank7 = {eid for eid in dev_eids if cohort_by_eid[eid]["task_a_rank_1_to_12"] == "7"}
    dev_rank9 = {eid for eid in dev_eids if cohort_by_eid[eid]["task_a_rank_1_to_12"] == "9"}
    dev_rank7_9_book_cov = {}
    for _, src_label, _ in BOOKS_SPEC:
        hits = cohort_book_hits[src_label]
        dev_rank7_9_book_cov[src_label] = {
            "dev_R7_covered": len(hits & dev_rank7),
            "dev_R7_total": len(dev_rank7),
            "dev_R7_pct": round(100.0 * len(hits & dev_rank7) / max(len(dev_rank7), 1), 1),
            "dev_R9_covered": len(hits & dev_rank9),
            "dev_R9_total": len(dev_rank9),
            "dev_R9_pct": round(100.0 * len(hits & dev_rank9) / max(len(dev_rank9), 1), 1),
        }

    # Stage 3: Critic Attribution Feasibility (strictly on dev_eids N=4,462!)
    def audit_critic_passages(label: str, pas_rows: list[dict[str, str]]):
        per_narr_critics: defaultdict[str, set[str]] = defaultdict(set)
        per_narr_praise: defaultdict[str, set[str]] = defaultdict(set)
        per_narr_crit: defaultdict[str, set[str]] = defaultdict(set)
        per_narr_mixed: defaultdict[str, set[str]] = defaultdict(set)
        all_critics = Counter()
        stance_counts = Counter()
        ambig_critic_rows = 0

        for r in pas_rows:
            eid = r["entry_id"]
            critic = (r.get("historical_attribution_critic") or "").strip()
            txt = norm_ar_text_keep_punct(r.get("quotation_text_exact", ""))
            all_critics[critic] += 1
            if (not critic) or len(critic) > 40 or "،" in critic or "غيره" in critic:
                ambig_critic_rows += 1
            per_narr_critics[eid].add(critic)

            has_p = any(c in txt for c in PRAISE_CUES)
            has_c = any(c in txt for c in CRIT_CUES)
            has_m = any(c in txt for c in MIXED_QUAL_CUES)
            if has_p and not has_c and not has_m:
                stance_counts["pure_praise_cue"] += 1
                per_narr_praise[eid].add(critic)
            elif has_c and not has_p:
                stance_counts["criticism_cue"] += 1
                per_narr_crit[eid].add(critic)
            elif (has_p and has_c) or has_m:
                stance_counts["qualified_or_mixed_cue"] += 1
                per_narr_mixed[eid].add(critic)
            else:
                stance_counts["no_simple_cue"] += 1

        covered_eids = set(per_narr_critics.keys())
        distinct_counts = [len(per_narr_critics[eid]) for eid in covered_eids]
        conflict_eids = sum(1 for eid in covered_eids if per_narr_praise[eid] and per_narr_crit[eid])

        # Per-rank distinct critic counts on dev (train+val ONLY!)
        rank_critic_medians = {}
        for rk in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]:
            rk_eids = [eid for eid in dev_eids if cohort_by_eid[eid]["task_a_rank_1_to_12"] == rk]
            rk_counts = [len(per_narr_critics.get(eid, set())) for eid in rk_eids]
            rank_critic_medians[f"R{rk}"] = {
                "dev_n": len(rk_eids),
                "mean_distinct_critics": round(float(np.mean(rk_counts)), 2),
                "median_distinct_critics": float(np.median(rk_counts)),
                "pct_with_critic_conflict": round(
                    100.0 * sum(1 for eid in rk_eids if per_narr_praise.get(eid) and per_narr_crit.get(eid)) / max(len(rk_eids), 1),
                    1,
                ),
            }

        return {
            "label": label,
            "dev_passages": len(pas_rows),
            "dev_narrators_covered": len(covered_eids),
            "dev_coverage_pct": round(100.0 * len(covered_eids) / len(dev_eids), 1),
            "distinct_critic_strings_total": len(all_critics),
            "ambiguous_or_compound_critic_rows": ambig_critic_rows,
            "mean_distinct_critics_per_covered_narrator": round(float(np.mean(distinct_counts)), 2) if distinct_counts else 0.0,
            "median_distinct_critics_per_covered_narrator": float(np.median(distinct_counts)) if distinct_counts else 0.0,
            "narrators_with_both_praise_and_criticism_critics": conflict_eids,
            "passage_stance_distribution": dict(stance_counts),
            "top_10_critics": all_critics.most_common(10),
            "dev_rank_breakdown": rank_critic_medians,
        }

    critic_v03 = audit_critic_passages("v0.3_strict_passages_dev", v03_dev_passages)
    critic_v04_abl = audit_critic_passages("v0.4_tahdhib_ablation_dev", v04_abl_dev_passages)

    # Check overlap between v0.3 critics and v0.4 Tahdhib ablation critics on dev
    v03_dev_set = {(r["entry_id"], r["historical_attribution_critic"].strip()) for r in v03_dev_passages}
    v04_dev_set = {(r["entry_id"], r["historical_attribution_critic"].strip()) for r in v04_abl_dev_passages}
    novel_v04_pairs = len(v04_dev_set - v03_dev_set)

    # Author comprehensive Stage 1 + Stage 3 deliverable report (zero em/en-dashes!)
    lines = [
        "# v1.2 Pre-Implementation Research Audit: Method 1 Biographies, Provenance, Leakage, and Critic Attribution",
        "",
        "**Non-negotiable scope note:** Read-only pre-implementation audit. `v1.0`, `v1.1`, `audit_v1_1`, and held-out test labels/ranks remain strictly untouched (`test N=788` never used for any rank-conditioned or feature-design inspection).",
        "",
        "## 1. Data Inventory (Stage 1)",
        "",
        "Raw full-text *rijal* books reside under `data/1_raw/Shamela4_Full_DB/26__التراجم-والطبقات/<book_folder>/pages.jsonl` accompanied by `book_metadata.json`, `toc.jsonl`, and `manifest.json`.",
        "",
        "| Book ID | Folder / Title | `pages.jsonl` (MB) | Pages | Non-Empty `footnotes` Field | Inline `____` Sep Pages | Parsed Bio Entries | Unique Links (`N=5,250`) | Ambiguous Cands | Unmatched | Entries >5k Chars |",
        "| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]
    for b in book_audits:
        st = b["link_status_counts"]
        uniq = st.get("unique_exact", 0) + st.get("unique_fallback", 0)
        lines.append(
            f"| `{b['prefix']}` | `{b['source_label']}` ({b['title_ar']}) | {b['pages_jsonl_size_mb']} | {b['total_pages']} | "
            f"{b['nonempty_footnotes_field_pages']} | {b['pages_with_inline_footnote_separator']} | {b['parsed_non_heading_entries']} | "
            f"{b['unique_cohort_5250_narrators_linked']} ({b['cohort_5250_coverage_pct']}%) | {st.get('ambiguous_candidate', 0)} | "
            f"{st.get('unmatched', 0)} | {b['entries_exceeding_5000_raw_chars']} |"
        )

    lines.extend([
        "",
        "## 2. Source Provenance and Chronology (Before Ibn Hajar d. 852 AH)",
        "",
    ])
    for b in book_audits:
        lines.append(f"- **`{b['prefix']}` (`{b['source_label']}`):** Author = `{b['author_ar']}`, Death = `{b['death_hijri']} AH` (predates Ibn Hajar d. `852 AH` by `{852 - int(b['death_hijri'])} years`). Edition metadata (`betaka_text`): `{b['betaka_text']}`")

    lines.extend([
        "",
        "## 3. Cohort Coverage Statistics (and `dev` Rank 7 vs Rank 9 Comparison)",
        "",
        f"- **Combined 6-book coverage across `N = 5,250` cohort:** `{len(union_5250)} / 5,250` (`{100.0 * len(union_5250) / 5250:.2f}%`).",
        f"- **Combined 6-book coverage across recovered zero-quote narrators (`N = 420`):** `{len(union_zq)} / 420` (`{100.0 * len(union_zq) / 420:.2f}%`).",
        "- **Per-book zero-quote coverage (`N=420` total) and `dev`-only (`train+val`) Rank 7 (*Mastur*) vs Rank 9 (*Majhul*) coverage:**",
        "",
        "| Book | All ZQ Covered (`N=420`) | `dev` R7 Covered (`N=" + str(len(dev_rank7)) + "`) | `dev` R9 Covered (`N=" + str(len(dev_rank9)) + "`) | Median Clean Chars | P90 Clean Chars |",
        "| :--- | :---: | :---: | :---: | :---: | :---: |",
    ])
    for b in book_audits:
        rc = dev_rank7_9_book_cov[b["source_label"]]
        lines.append(
            f"| `{b['source_label']}` | {b['cohort_zero_quote_420_linked']} ({100*b['cohort_zero_quote_420_linked']/420:.1f}%) | "
            f"{rc['dev_R7_covered']} / {rc['dev_R7_total']} ({rc['dev_R7_pct']}%) | "
            f"{rc['dev_R9_covered']} / {rc['dev_R9_total']} ({rc['dev_R9_pct']}%) | "
            f"{b['clean_entry_char_len_median']} | {b['clean_entry_char_len_p90']} |"
        )

    lines.extend([
        "",
        "## 4. Leakage and Contamination Risk Audit (Critical Finding!)",
        "",
        "Four books (`1716`, `1615`, `890`, `4609`) store most editorial footnotes in the separate `footnotes` JSON field of `pages.jsonl` (`17,777`, `4,034`, `3,582`, and `94` pages respectively), so reading `body` alone avoids the bulk of modern commentary. However, scanning `body` directly reveals two critical phenomena:",
        "1. **True inline editorial/post-classical contamination in `body` (rare, ~0.1%, but must be stripped):** Modern editor interjections by Dr. Bashar (`قال افقر العباد ابو محمد بشار بن عواد... ابن حجر`) and Muʿallimi parenthetical glosses (`(قال ابن حجر... - ٣)` / *Taqrib* / *Tahdhib al-Tahdhib*) appear directly inside `body` on a handful of pages without an `____` footnote separator, alongside Vol. 1 editor introductions.",
        "2. **Classical homograph false positives:** Naive substring blocking of `ابن حجر` or `بشار` flags legitimate 1st-3rd C. AH narrators such as `وائل بن حجر` (`Wa'il ibn Hujr`), `علي ابن حجر السعدي` (`Ali ibn Hujr`, d. 244 AH), and `محمد بن بشار بندار` (`Bundar`, d. 252 AH).",
        "",
        "| Book | Raw `ibn_hajar` Hits | Stripped `ibn_hajar` | Raw `taqrib` Hits | Stripped `taqrib` | Raw `tahrir` | Stripped `tahrir` | Raw `tahdhib_tahdhib` | Stripped `tahdhib_tahdhib` | Raw `al_dhahabi`/`al_kashif` |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ])
    for b in book_audits:
        rh = b["contamination_raw_entry_hits"]
        sh = b["contamination_after_sep_strip_hits"]
        dh_raw = rh.get("al_dhahabi", 0) + rh.get("al_kashif", 0)
        lines.append(
            f"| `{b['source_label']}` | {rh.get('ibn_hajar', 0)} | {sh.get('ibn_hajar', 0)} | "
            f"{rh.get('taqrib', 0)} | {sh.get('taqrib', 0)} | {rh.get('tahrir', 0)} | {sh.get('tahrir', 0)} | "
            f"{rh.get('tahdhib_al_tahdhib', 0)} | {sh.get('tahdhib_al_tahdhib', 0)} | {dh_raw} |"
        )

    lines.extend([
        "",
        "### Sample `dev`-Partition Contamination Contexts (Why Stripping Is Mandatory)",
        "",
    ])
    for s in dev_contamination_samples[:10]:
        lines.append(
            f"- `{s['book']}` (`{s['dev_entry_id']}`, term=`{s['term']}`, persists_after_line_strip=`{s['in_stripped_body']}`): `{s['snippet']}`"
        )

    lines.extend([
        "",
        "## 5. Stage 3 Critic Attribution Feasibility (`train + val` Only, `N = 4,462`)",
        "",
        f"- **Existing `v0.3` clean passages (`historical_attribution_critic`):** `{critic_v03['dev_passages']}` dev passages covering `{critic_v03['dev_narrators_covered']} / {len(dev_eids)}` (`{critic_v03['dev_coverage_pct']}%`), `{critic_v03['distinct_critic_strings_total']}` distinct critic strings (`mean={critic_v03['mean_distinct_critics_per_covered_narrator']}`, `median={critic_v03['median_distinct_critics_per_covered_narrator']}` critics/narrator), `{critic_v03['narrators_with_both_praise_and_criticism_critics']}` narrators showing explicit praise+criticism conflict across critics; `{critic_v03['ambiguous_or_compound_critic_rows']}` ambiguous/compound critic rows.",
        f"- **Passage stance separability (`v0.3` dev):** `{critic_v03['passage_stance_distribution']}`.",
        f"- **Existing `v0.4` *Tahdhib* early-speaker ablation:** `{critic_v04_abl['dev_passages']}` dev passages covering `{critic_v04_abl['dev_narrators_covered']} / {len(dev_eids)}` (`{critic_v04_abl['dev_coverage_pct']}%`), adding `{novel_v04_pairs}` novel `(entry_id, critic)` pairs absent from `v0.3`.",
        "",
        "### `dev` Per-Rank Distinct Critic Count & Conflict Rate (`v0.3` vs `v0.4` Ablation)",
        "",
        "| Rank | `dev` N | `v0.3` Mean Critics | `v0.3` Conflict % | `v0.4` Mean Critics | `v0.4` Conflict % |",
        "| :---: | :---: | :---: | :---: | :---: | :---: |",
    ])
    for rk in [f"R{i}" for i in range(1, 11)]:
        d3 = critic_v03["dev_rank_breakdown"][rk]
        d4 = critic_v04_abl["dev_rank_breakdown"][rk]
        lines.append(
            f"| {rk} | {d3['dev_n']} | {d3['mean_distinct_critics']} (med {d3['median_distinct_critics']}) | {d3['pct_with_critic_conflict']}% | "
            f"{d4['mean_distinct_critics']} (med {d4['median_distinct_critics']}) | {d4['pct_with_critic_conflict']}% |"
        )

    lines.extend([
        "",
        "## 6. Feature Feasibility, Stage 2 Experiment Designs, and Implementation Effort",
        "",
        "- **Biographical Novelty Verified:** Full Method 1 books add substantial narrative missing from snippet quotes (`clean_entry_char_len_median` ranges from `240` to `470+` chars in *Tahdhib al-Kamal*, *Jarh wa Ta'dil*, and *al-Kamil*, and cover `~80%` to `91%` of the cohort overall; Rank 7 *Mastur* dev coverage is notably higher than Rank 9 *Majhul* in `Tahdhib al-Kamal` and `Thiqat Ibn Hibban`!).",
        "- **Editorial Contamination Verdict:** Because raw pages in `1716` (Dr. Bashar's footnotes), `4609` (footnote apparatus), and `1981` contain inline `ابن حجر` / `تقريب` / `تهذيب التهذيب` footnote references, any Stage 2 Method 1 full-text extractor **MUST** implement page-level inline footnote stripping (`____` cutoff + numbered `[1]` footnote stripping + `0`-occurrence runtime assertions for `تقريب`, `تحرير`, `ابن حجر`, `تهذيب التهذيب`, `الكاشف`, `بشار`, `المعلمي`) before TF-IDF/OOF extraction.",
        "- **Recommended Stage 2 Controlled Experiments (Unbundled, Matching `v1.1` Splits & Protocol):**",
        "  - **Exp A (Baseline Reference):** Existing frozen `Arm 4` (`v1.1`).",
        "  - **Exp B (Method 1 Full Bio Text):** Strictly footnote-stripped 6-book pre-Ibn-Hajar biography text -> OOF Sparse `LogReg` + `ConcatDirGNN`.",
        "  - **Exp C (Method 1 Book-Presence & Length Indicators Only):** Binary inclusion flags (per 6 classical books, explicitly documenting non-equivalence to reliability grades) + `log1p` entry lengths added to `ConcatDirGNN`.",
        "  - **Exp D (Method 1 Full Text + Book Indicators + `Arm 4`):** Full evidence ablation comparing OOF `TextLogReg`, `EarlyMLP`, and `ConcatDirGNN` across all 5 seeds.",
        "- **Recommended Stage 3 Critic Attribution Experiment:** Add structured, objective critic counts (distinct praise/criticism/qualified critics, distinct classical source works, critic-attributed TF-IDF prefixes `CRITIC_NAME :: text`) without subjective strictness weighting.",
        "- **Estimated Effort:** ~1 script (~350 lines) for Stage 1-verified clean Method 1 text + footnote quarantine & manifest freeze (`~2-3 min` build time), plus ~15 min runtime for the 4 controlled Stage 2 runs (`A/B/C/D`) + Stage 3 critic-count ablation under the exact `v1.1` 5-seed protocol.",
    ])

    (OUT_DIR / "AUDIT_DATA_PROVENANCE_V1_2.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    payload = {
        "book_audits": book_audits,
        "cohort_6book_union_5250": len(union_5250),
        "cohort_zero_quote_420_union": len(union_zq),
        "dev_rank7_vs_rank9_coverage": dev_rank7_9_book_cov,
        "dev_contamination_samples": dev_contamination_samples,
        "dev_rank7_zero_quote_samples": dev_rank7_samples,
        "stage3_critic_v03_dev": critic_v03,
        "stage3_critic_v04_abl_dev": critic_v04_abl,
        "stage3_novel_v04_pairs": novel_v04_pairs,
    }
    (OUT_DIR / "AUDIT_DATA_PROVENANCE_V1_2.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    out_files = ["AUDIT_DATA_PROVENANCE_V1_2.md", "AUDIT_DATA_PROVENANCE_V1_2.json"]
    manifest = {
        "audit_id": "V1.2-STAGE1-AND-STAGE3-PRE-IMPLEMENTATION-AUDIT",
        "outputs": {name: {"sha256": sha256_file(OUT_DIR / name)} for name in out_files},
    }
    (OUT_DIR / "MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (OUT_DIR / "MANIFEST.sha256").write_text(
        "\n".join(f"{sha256_file(OUT_DIR / name)}  {name}" for name in out_files) + "\n",
        encoding="utf-8",
    )
    print("V1_2_STAGE1_AUDIT_COMPLETE", OUT_DIR, flush=True)


if __name__ == "__main__":
    main()
