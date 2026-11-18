"""v1.2 Stage 1 Clean Method 1 Biography Package, Provenance, & Train-Only Feasibility.

Respects all user-mandated methodological safeguards:
1. Immutable upstream: v1.0, v1.1, and audit_v1_1 remain untouched.
2. Validation-set protection: All rank-conditioned statistics and feature
   feasibility checks run STRICTLY on train (N=3,674); val (788) and test (788)
   labels are never inspected for feature engineering.
3. Editorial contamination quarantine: Strips separate footnotes, Vol. 1 editor
   frontmatter by verified sequence_num bounds, inline ____ separators, and
   editorial/post-classical sentences/parentheticals mentioning Ibn Hajar,
   Taqrib, Tahrir, Tahdhib al-Tahdhib, Kashif, Dhahabi, or Bashar commentary,
   while preserving legitimate classical homographs (e.g., Wa'il ibn Hujr,
   Ali ibn Hujr, Muhammad ibn Bashshar Bundar).
4. Explicit identity confidence & missingness: Retains unmatched and ambiguous
   book mentions separately (is_linked, is_ambiguous) rather than conflating
   unmatched records with confirmed historical absence.
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

ROOT = Path(__file__).resolve().parents[2]
PIPELINE_DIR = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline"
V03_INPUT_DIR = PIPELINE_DIR / "task_b_historical_inputs_v0_3_2026-11-17"
V04_INPUT_DIR = PIPELINE_DIR / "task_b_historical_inputs_v0_4_2026-11-17"
V03_GRAPH_DIR = PIPELINE_DIR / "task_b_consolidated_graph_v0_3_2026-11-17"
SH_NARRATORS = ROOT / "data/2_interim/shamela4_narrator_audit/narrators.csv"
SHAMELA_BOOKS_DIR = ROOT / "data/1_raw/Shamela4_Full_DB/26__التراجم-والطبقات"
OUT_DIR = PIPELINE_DIR / "task_b_method1_clean_bios_v1_2_2026-11-18"

DIACRITICS_RE = re.compile(r"[\u064b-\u065f\u0670\u0640\u200c]")
STOP_TOKS = {"ابن", "ابو", "ابي", "ابا", "ام", "بنت", "بن", "عبد", "مولى", "ال", "في", "عن", "من"}

# Exact verified frontmatter cutoffs (sequence_num where classical entries/Taqdimah begin)
BOOKS_SPEC = [
    (
        "1716",
        "method1_tahdhib_alkamal",
        204,
        re.compile(
            r'(?:^|\r|\n)(?:[٠-٩\d]+\s*-\s*(?:[^:\r\n<]{0,14}:?\s*)?(?:<span[^>]*data-type=[\'"]title[\'"][^>]*>([^<]{3,140})</span>|([^\r\n.<]{4,120}))|<span[^>]*data-type=[\'"]title[\'"][^>]*>([^<]{3,140})</span>)'
        ),
    ),
    (
        "1615",
        "method1_jarh_tadil",
        34,
        re.compile(r"(?:^|\r|\n)[٠-٩\d]+\s*-\s*([^\r\n]{4,160})"),
    ),
    (
        "1976",
        "method1_thiqat_ibn_hibban",
        658,
        re.compile(r"(?:^|\r|\n)\u2022\s+([^\r\n]{4,160})"),
    ),
    (
        "890",
        "method1_tarikh_kabir",
        1,
        re.compile(
            r'<span[^>]*data-type=[\'"]title[\'"][^>]*>\s*(?:[٠-٩\d]+\s*-\s*)?([^<]{4,160})</span>'
        ),
    ),
    (
        "1981",
        "method1_thiqat_ijli",
        1,
        re.compile(r"(?:^|\r|\n)[٠-٩\d]+\s*-\s*([^\r\n]{4,140})"),
    ),
    (
        "4609",
        "method1_kamil",
        191,
        re.compile(
            r'<span[^>]*data-type=[\'"]title[\'"][^>]*>\s*(?:[٠-٩\d]+\s*-\s*)?([^<]{4,160})</span>'
        ),
    ),
]

# Editorial commentary patterns to strip safely without touching classical homographs
EDITORIAL_PATTERNS = [
    ("inline_bashar_comment", re.compile(r"قال\s+(?:أفقر\s+العباد\s+)?(?:أبو\s+محمد\s+)?بشار[^.!؟\n:]*:[^.!؟\n]*[.!؟]?")),
    ("inline_muallimi_gloss", re.compile(r"قال\s+(?:الشيخ\s+)?(?:عبد\s+الرحمن\s+)?المعلمي[^.!؟\n]*[.!؟]?")),
    ("paren_ibn_hajar_gloss", re.compile(r"\([^)]*(?:ابن\s+حجر|التقريب|تقريب\s+التهذيب|تحرير|تهذيب\s+التهذيب|الكاشف|الذهبي)[^)]*\)")),
    ("quote_ibn_hajar_clause", re.compile(r"(?:قال|وذكر|اعتبره|ضبطه|أرخ|أما\s+قول)\s+(?:مغلطاي\s+و\s*)?(?:الحافظ\s+)?ابن\s+حجر[^.!\n]*[.!\n]?")),
    ("clause_prohibited_titles", re.compile(r"[^.!؟\n]*(?:تقريب\s+التهذيب|في\s+[\"«]?التقريب[\"»]?|تحرير\s+التقريب|تهذيب\s+التهذيب|تذهيب\s+التهذيب|[\"«]?الكاشف[\"»]?\s*:)[^.!؟\n]*[.!؟]?")),
    ("clause_dhahabi_comment", re.compile(r"(?:قال|ذكره)\s+(?:الإمام\s+)?الذهبي[^.!؟\n]*[.!؟]?")),
]

# Strict post-cleaning prohibited markers (safe against classical Wail/Ali ibn Hujr and Bundar)
POST_CLEAN_FORBIDDEN_REGEXES = [
    ("hafiz_ibn_hajar", re.compile(r"(?:الحافظ|قال|ذكره|وهم\s+من|قول|ضبطه)\s+(?:الحافظ\s+)?ابن\s+حجر")),
    ("ibn_hajar_al_asqalani", re.compile(r"ابن\s+حجر\s+العسقلاني")),
    ("taqrib_title", re.compile(r"تقريب(?:\s+التهذيب)?|في\s+[\"«]?التقريب[\"»]?")),
    ("tahrir_title", re.compile(r"تحرير\s+التقريب")),
    ("tahdhib_al_tahdhib", re.compile(r"تهذيب\s+التهذيب")),
    ("kashif_title", re.compile(r"الكاشف")),
    ("bashar_awwad", re.compile(r"بشار\s+بن\s+عواد|قال\s+(?:أفقر\s+العباد[^:]*|بشار)")),
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


def strip_page_breaks_and_clean_entry(raw_entry: str) -> tuple[str, list[str], list[tuple[str, str]]]:
    """Strip inline ____ footnotes, HTML tags, and editorial contamination safely."""
    actions = []
    quarantined: list[tuple[str, str]] = []

    # 1. Line-level inline footnote strip per page
    lines = raw_entry.splitlines()
    kept_lines = []
    in_fn = False
    fn_dropped_lines = 0
    for ln in lines:
        s = ln.strip()
        if s.startswith("__PAGE_META:"):
            in_fn = False
            continue
        if re.match(r"^[_\-ـ]{4,}$", s):
            in_fn = True
            fn_dropped_lines += 1
            continue
        if in_fn:
            fn_dropped_lines += 1
            continue
        kept_lines.append(ln)
    if fn_dropped_lines > 0:
        actions.append(f"stripped_inline_fn_lines:{fn_dropped_lines}")

    text = "\n".join(kept_lines)
    # Remove HTML span tags (preserving inner header text cleanly)
    text = re.sub(r"<[^>]+>", " ", text)
    text_no_diac = DIACRITICS_RE.sub("", text)

    # 2. Surgical editorial clause/gloss removal on diacritic-stripped copy & raw copy
    # Normalize only Alef forms lightly during regex check, strip exact matches
    cleaned = re.sub(r"\s+", " ", text_no_diac).strip()
    for pat_name, rx in EDITORIAL_PATTERNS:
        for m in rx.finditer(cleaned):
            quarantined.append((pat_name, m.group(0)[:220]))
        if rx.search(cleaned):
            cleaned = rx.sub(" ", cleaned)
            actions.append(f"quarantined:{pat_name}")

    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned, actions, quarantined


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with (V03_GRAPH_DIR / "TASK_B_NODE_STRUCTURAL_FEATURES_V0_3.csv").open(
        encoding="utf-8-sig", newline=""
    ) as f:
        cohort_rows = list(csv.DictReader(f))
    assert len(cohort_rows) == 5250
    cohort_by_eid = {r["entry_id"]: r for r in cohort_rows}
    train_eids = {r["entry_id"] for r in cohort_rows if r["split"] == "train"}
    assert len(train_eids) == 3674

    with SH_NARRATORS.open(encoding="utf-8-sig", newline="") as f:
        sh_raw = list(csv.DictReader(f))
    unique_exact, cand_map = build_name_lookup(sh_raw, cohort_rows)

    bio_rows = []
    quarantine_rows = []
    # Track 3-state linkage per (entry_id, source_label)
    linked_bios_count: defaultdict[tuple[str, str], int] = defaultdict(int)
    linked_clean_chars: defaultdict[tuple[str, str], int] = defaultdict(int)
    ambig_cands_count: defaultdict[tuple[str, str], int] = defaultdict(int)

    book_stats = []
    train_samples_by_book: defaultdict[str, list[dict]] = defaultdict(list)

    bio_seq = 0
    for prefix, src_label, min_seq, hdr_re in BOOKS_SPEC:
        book_dir = next(SHAMELA_BOOKS_DIR.glob(prefix + "__*"))
        pages = []
        with (book_dir / "pages.jsonl").open(encoding="utf-8") as f:
            for line in f:
                p = json.loads(line)
                if int(p.get("sequence_num") or 0) >= min_seq:
                    pages.append(p)

        # Build text with reversible page offset map
        chunks = []
        page_spans = []  # (char_start, char_end, page_id, part, page_num, seq_num)
        cur = 0
        for p in pages:
            marker = f"\n__PAGE_META:{p['page_id']}__\n"
            body = p.get("body") or ""
            seg = marker + body
            chunks.append(seg)
            page_spans.append((cur, cur + len(seg), str(p["page_id"]), str(p.get("part") or ""), str(p.get("page_num") or ""), str(p.get("sequence_num") or "")))
            cur += len(seg)
        full_text = "".join(chunks)

        # Binary search page helper
        starts = [ps[0] for ps in page_spans]

        def find_page_info(pos: int):
            import bisect
            i = max(0, bisect.bisect_right(starts, pos) - 1)
            return page_spans[i]

        hdrs = list(hdr_re.finditer(full_text))
        matched_cnt = 0
        ambig_cnt = 0
        quarantined_cnt = 0

        for idx, hm in enumerate(hdrs):
            raw_hdr = next((g for g in hm.groups() if g), "")
            if not raw_hdr or any(
                skip in raw_hdr for skip in ("باب", "المجلد", "مقدمة", "خطبة", "حرف ", "كتاب ")
            ):
                continue
            hdr_norm = clean_book_header_name(raw_hdr)
            subj_eid, cands, status = resolve_mention_tokens(hdr_norm, unique_exact, cand_map)

            if status == "ambiguous_candidate":
                ambig_cnt += 1
                for ceid in cands:
                    if ceid in cohort_by_eid:
                        ambig_cands_count[(ceid, src_label)] += 1
                continue

            if not subj_eid:
                continue

            matched_cnt += 1
            start_pos = hm.start() if prefix in {"1615", "1976", "1981"} else hm.end()
            end_pos = hdrs[idx + 1].start() if idx + 1 < len(hdrs) else min(len(full_text), start_pos + 15000)
            raw_slice = full_text[start_pos:end_pos]
            p_start = find_page_info(start_pos)
            p_end = find_page_info(max(start_pos, end_pos - 1))

            clean_text, actions, q_items = strip_page_breaks_and_clean_entry(raw_slice)

            # Assert ZERO prohibited editorial markers remain after cleaning!
            for rname, rx in POST_CLEAN_FORBIDDEN_REGEXES:
                if rx.search(clean_text):
                    # Quarantine whole offending clause sentence and assert again
                    hit = rx.search(clean_text)
                    quarantine_rows.append({
                        "book_id": prefix,
                        "source_label": src_label,
                        "entry_id": subj_eid,
                        "page_id_start": p_start[2],
                        "pattern": f"residual_{rname}",
                        "removed_text": clean_text[max(0, hit.start()-40):hit.end()+60],
                    })
                    clean_text = rx.sub(" ", clean_text)
                    actions.append(f"residual_strip:{rname}")
                    clean_text = re.sub(r"\s+", " ", clean_text).strip()
                    assert not rx.search(clean_text), f"Residual leakage {rname} in {subj_eid}"

            for qpat, qtxt in q_items:
                quarantined_cnt += 1
                quarantine_rows.append({
                    "book_id": prefix,
                    "source_label": src_label,
                    "entry_id": subj_eid,
                    "page_id_start": p_start[2],
                    "pattern": qpat,
                    "removed_text": qtxt,
                })

            bio_seq += 1
            bio_id = f"M1B-{bio_seq:05d}"
            bio_rows.append({
                "bio_id": bio_id,
                "entry_id": subj_eid,
                "shamela_narrator_id": cohort_by_eid[subj_eid]["shamela_narrator_id"],
                "book_id": prefix,
                "source_label": src_label,
                "part": p_start[3],
                "page_num_start": p_start[4],
                "page_id_start": p_start[2],
                "page_id_end": p_end[2],
                "seq_start": p_start[5],
                "seq_end": p_end[5],
                "raw_char_len": len(raw_slice),
                "clean_char_len": len(clean_text),
                "cleaning_actions": ";".join(actions) if actions else "clean_direct",
                "clean_bio_text": clean_text,
            })
            linked_bios_count[(subj_eid, src_label)] += 1
            linked_clean_chars[(subj_eid, src_label)] += len(clean_text)

            # Collect representative train-ONLY manual verification samples (NEVER val/test!)
            if subj_eid in train_eids and (actions or len(train_samples_by_book[src_label]) < 4):
                if len(train_samples_by_book[src_label]) < 5:
                    train_samples_by_book[src_label].append({
                        "bio_id": bio_id,
                        "train_entry_id": subj_eid,
                        "page_id": p_start[2],
                        "part": p_start[3],
                        "page_num": p_start[4],
                        "actions": ";".join(actions) if actions else "clean_direct",
                        "clean_preview": clean_text[:320],
                    })

        book_stats.append({
            "book_id": prefix,
            "source_label": src_label,
            "min_seq": min_seq,
            "unique_bios_extracted": matched_cnt,
            "ambiguous_headers_logged": ambig_cnt,
            "editorial_quarantine_events": quarantined_cnt,
        })
        print(f"[clean-extract] {src_label}: bios={matched_cnt}, ambig_hdrs={ambig_cnt}, quarantined={quarantined_cnt}", flush=True)

    # Write TASK_B_METHOD1_CLEAN_BIOS_V1_2.csv
    bio_fp = OUT_DIR / "TASK_B_METHOD1_CLEAN_BIOS_V1_2.csv"
    with bio_fp.open("w", encoding="utf-8-sig", newline="") as f:
        fields = [
            "bio_id", "entry_id", "shamela_narrator_id", "book_id", "source_label",
            "part", "page_num_start", "page_id_start", "page_id_end", "seq_start", "seq_end",
            "raw_char_len", "clean_char_len", "cleaning_actions", "clean_bio_text",
        ]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(bio_rows)

    # Write METHOD1_CLEANING_QUARANTINE_LOG_V1_2.csv
    q_fp = OUT_DIR / "METHOD1_CLEANING_QUARANTINE_LOG_V1_2.csv"
    with q_fp.open("w", encoding="utf-8-sig", newline="") as f:
        fields = ["book_id", "source_label", "entry_id", "page_id_start", "pattern", "removed_text"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(quarantine_rows)

    # Write TASK_B_METHOD1_BOOK_INDICATORS_V1_2.csv (3-state provenance for all 5,250 narrators!)
    book_labels = [b[1] for b in BOOKS_SPEC]
    ind_fp = OUT_DIR / "TASK_B_METHOD1_BOOK_INDICATORS_V1_2.csv"
    ind_fields = ["entry_id", "shamela_narrator_id", "split", "has_early_critic_quote", "n_books_linked", "n_books_ambiguous", "log1p_total_m1_clean_chars"]
    for bl in book_labels:
        ind_fields.extend([f"status_{bl}", f"is_linked_{bl}", f"is_ambig_{bl}", f"log1p_chars_{bl}"])

    with ind_fp.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=ind_fields)
        w.writeheader()
        for r in cohort_rows:
            eid = r["entry_id"]
            out_r = {
                "entry_id": eid,
                "shamela_narrator_id": r["shamela_narrator_id"],
                "split": r["split"],
                "has_early_critic_quote": r["has_early_critic_quote"],
            }
            n_linked = 0
            n_ambig = 0
            tot_chars = 0
            for bl in book_labels:
                lc = linked_bios_count.get((eid, bl), 0)
                cc = linked_clean_chars.get((eid, bl), 0)
                ac = ambig_cands_count.get((eid, bl), 0)
                if lc > 0:
                    st = "linked_unique"
                    is_l, is_a = 1, 0
                    n_linked += 1
                    tot_chars += cc
                elif ac > 0:
                    st = "ambiguous_candidate"
                    is_l, is_a = 0, 1
                    n_ambig += 1
                else:
                    st = "unmatched_in_book"
                    is_l, is_a = 0, 0
                out_r[f"status_{bl}"] = st
                out_r[f"is_linked_{bl}"] = is_l
                out_r[f"is_ambig_{bl}"] = is_a
                out_r[f"log1p_chars_{bl}"] = f"{math.log1p(cc):.4f}"
            out_r["n_books_linked"] = n_linked
            out_r["n_books_ambiguous"] = n_ambig
            out_r["log1p_total_m1_clean_chars"] = f"{math.log1p(tot_chars):.4f}"
            w.writerow(out_r)

    # Write CLEANING_VERIFICATION_SAMPLES_V1_2.md (train-ONLY samples from all 6 books!)
    samp_lines = [
        "# v1.2 Cleaning Verification Samples (Train Partition Only, All 6 Method 1 Books)",
        "",
        "All entries below belong strictly to `split == 'train'` (`val` and `test` untouched).",
        "",
    ]
    for bl in book_labels:
        samp_lines.append(f"## `{bl}`")
        for s in train_samples_by_book[bl]:
            samp_lines.append(
                f"- `{s['bio_id']}` (`{s['train_entry_id']}`, page_id=`{s['page_id']}`, part=`{s['part']}`, p=`{s['page_num']}`, actions=`{s['actions']}`): `{s['clean_preview']}`"
            )
        samp_lines.append("")
    (OUT_DIR / "CLEANING_VERIFICATION_SAMPLES_V1_2.md").write_text(
        "\n".join(samp_lines), encoding="utf-8"
    )

    # Write TRAIN-ONLY Feature Feasibility Report (N = 3,674 ONLY! Zero val/test label access!)
    v03_tr: defaultdict[str, list[dict]] = defaultdict(list)
    with (V03_INPUT_DIR / "TASK_B_ELIGIBLE_HISTORICAL_PASSAGES_V0_3.csv").open(
        encoding="utf-8-sig", newline=""
    ) as f:
        for r in csv.DictReader(f):
            if r["entry_id"] in train_eids:
                v03_tr[r["entry_id"]].append(r)

    tr_rows = [r for r in cohort_rows if r["split"] == "train"]
    train_feas_rows = []
    for rk in [str(i) for i in range(1, 13)]:
        rk_eids = [r["entry_id"] for r in tr_rows if r["task_a_rank_1_to_12"] == rk]
        # Method 1 coverage
        m1_any = sum(1 for eid in rk_eids if any(linked_bios_count.get((eid, bl), 0) > 0 for bl in book_labels))
        m1_tahdhib = sum(1 for eid in rk_eids if linked_bios_count.get((eid, "method1_tahdhib_alkamal"), 0) > 0)
        m1_thiqat_ih = sum(1 for eid in rk_eids if linked_bios_count.get((eid, "method1_thiqat_ibn_hibban"), 0) > 0)
        # Critic stats in train ONLY
        crit_counts = []
        conflict_cnt = 0
        for eid in rk_eids:
            cs, p_c, c_c = set(), set(), set()
            for pr in v03_tr.get(eid, []):
                cr = (pr.get("historical_attribution_critic") or "").strip()
                tx = pr.get("quotation_text_exact", "")
                cs.add(cr)
                hp = any(k in tx for k in PRAISE_CUES)
                hc = any(k in tx for k in CRIT_CUES)
                hm = any(k in tx for k in MIXED_QUAL_CUES)
                if hp and not hc and not hm:
                    p_c.add(cr)
                elif hc and not hp:
                    c_c.add(cr)
            crit_counts.append(len(cs))
            if p_c and c_c:
                conflict_cnt += 1
        train_feas_rows.append({
            "rank": rk,
            "train_n": len(rk_eids),
            "m1_any_pct": round(100.0 * m1_any / max(len(rk_eids), 1), 1),
            "m1_tahdhib_pct": round(100.0 * m1_tahdhib / max(len(rk_eids), 1), 1),
            "m1_thiqat_ih_pct": round(100.0 * m1_thiqat_ih / max(len(rk_eids), 1), 1),
            "mean_critics_v03": round(float(np.mean(crit_counts)), 2),
            "conflict_pct_v03": round(100.0 * conflict_cnt / max(len(rk_eids), 1), 1),
        })

    tf_lines = [
        "# v1.2 Training-Only Feature Feasibility Report (`split == 'train'`, N = 3,674 Only)",
        "",
        "Generated strictly on `train` (`N = 3,674`) to correct prior `val` (`N = 788`) exposure before freezing Stage 2 and Phase B feature specifications. `val` and `test` labels were never accessed.",
        "",
        "| Rank | `train` N | M1 Any Book % | M1 `Tahdhib al-Kamal` % | M1 `Thiqat Ibn Hibban` % | `v0.3` Mean Critics | `v0.3` Critic Conflict % |",
        "| :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]
    for trf in train_feas_rows:
        tf_lines.append(
            f"| R{trf['rank']} | {trf['train_n']} | {trf['m1_any_pct']}% | {trf['m1_tahdhib_pct']}% | "
            f"{trf['m1_thiqat_ih_pct']}% | {trf['mean_critics_v03']} | {trf['conflict_pct_v03']}% |"
        )
    (OUT_DIR / "TRAIN_ONLY_FEATURE_FEASIBILITY_V1_2.md").write_text(
        "\n".join(tf_lines) + "\n", encoding="utf-8"
    )
    (OUT_DIR / "TRAIN_ONLY_FEATURE_FEASIBILITY_V1_2.json").write_text(
        json.dumps({"book_stats": book_stats, "train_only_rank_feasibility": train_feas_rows}, indent=2),
        encoding="utf-8",
    )

    out_files = [
        "TASK_B_METHOD1_CLEAN_BIOS_V1_2.csv",
        "TASK_B_METHOD1_BOOK_INDICATORS_V1_2.csv",
        "METHOD1_CLEANING_QUARANTINE_LOG_V1_2.csv",
        "CLEANING_VERIFICATION_SAMPLES_V1_2.md",
        "TRAIN_ONLY_FEATURE_FEASIBILITY_V1_2.md",
        "TRAIN_ONLY_FEATURE_FEASIBILITY_V1_2.json",
    ]
    manifest = {
        "package_id": "TASK_B_METHOD1_CLEAN_BIOS_V1_2",
        "outputs": {name: {"sha256": sha256_file(OUT_DIR / name)} for name in out_files},
    }
    (OUT_DIR / "MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (OUT_DIR / "MANIFEST.sha256").write_text(
        "\n".join(f"{sha256_file(OUT_DIR / name)}  {name}" for name in out_files) + "\n",
        encoding="utf-8",
    )
    print("V1_2_CLEAN_BIOS_PACKAGE_COMPLETE", OUT_DIR, flush=True)


if __name__ == "__main__":
    main()
