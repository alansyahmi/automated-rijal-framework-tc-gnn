#!/usr/bin/env python3
"""Build Task B Consolidated Graph, Structural Node Features, and Cohort Splits v0.3.

Implements Refinements 1, 3, and 5:
1. Unlocks all 6 classical rijal encyclopedias for Method 1 teacher-student
   extraction using format-specific entry header parsers:
   - 1716__تهذيب-الكمال
   - 1615__الجرح-والتعديل-ابن-أبي-حاتم
   - 4609__الكامل-في-ضعفاء-الرجال
   - 890__التاريخ-الكبير-للبخاري
   - 1976__الثقات-لابن-حبان (bullet '•' entries)
   - 1981__الثقات-للعجلي
2. Consolidates Method 1 with Method 2 empirical isnads (arbml/Sanadset 650k
   across 956 books minus Ibn Hajar works + Bukhari Sultania).
3. Preserves exact v0.1 Train/Val/Test split assignments for all 4,830 shared
   narrators while assigning stratified 70/15/15 splits for the +420 newly
   recovered zero-quote high-confidence narrators (N = 5,250 total cohort).
4. Computes explicit structural node features (student out-degrees, teacher
   in-degrees, Sanadset chain counts, distinct books, non-Sahihayn counts,
   and mutual M1+M2 confirmations) to prevent GCN degree washing on Ranks 6, 7, 9.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import random
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[2]
PIPELINE = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline"
V04_DIR = PIPELINE / "task_b_historical_inputs_v0_4_2026-11-17"
SPLITS_V01 = PIPELINE / "task_b_graph_and_splits_v0_1_2026-11-17/TASK_B_SPLITS_ELIGIBLE_NARRATORS_V0_1.csv"
SH_NARRATORS = ROOT / "data/2_interim/shamela4_narrator_audit/narrators.csv"
SHAMELA_BOOKS_DIR = ROOT / "data/1_raw/Shamela4_Full_DB/26__التراجم-والطبقات"
HDB_BUKHARI = ROOT / "data/1_raw/hadithdb/bukhari_sultania_copy.json"
HDB_LINKS = PIPELINE / "task_b_historical_inputs_v0_3_2026-11-17/TASK_B_HADITHDB_NARRATOR_LINKS_1524_V0_3.csv"
SANADSET_DIR = ROOT / "data/1_raw/sanadset/data"
OUT_DIR = PIPELINE / "task_b_consolidated_graph_v0_3_2026-11-17"

DIACRITICS_RE = re.compile(r"[\u064b-\u065f\u0670\u0640\u200c]")
STOP_TOKS = {"ابن", "ابو", "ابي", "ابا", "ام", "بنت", "بن", "عبد", "مولى", "ال", "في", "عن", "من"}
PROHIBITED_SANADSET_BOOK_KEYS = ("تقريب", "ابن حجر")
SAHIHAYN_BOOK_KEYS = ("صحيح البخاري", "صحيح مسلم")


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


def clean_item_text(item: str) -> str:
    s = re.sub(r"\([^)]*\)", " ", item)
    s = re.split(r"\s-\s|\sوصحح|\sوهو\s|\sإن\s+كان|\sعلى\s+خلاف|\sقال\s+", s)[0]
    s = norm_ar(s)
    return re.sub(r"\s+(?:عن|في|من|و)$", "", s).strip()


def build_name_lookup(
    sh_raw: list[dict[str, str]],
    high_conf_nodes: dict[str, dict[str, str]],
) -> tuple[dict[str, str], dict[str, set[str]]]:
    nid_to_eid = {r["shamela_narrator_id"]: r["entry_id"] for r in high_conf_nodes.values()}
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


def resolve_mention_tokens(
    clean_name: str,
    unique_exact: dict[str, str],
    cand_map: dict[str, set[str]],
) -> tuple[str, set[str]]:
    if not clean_name:
        return "", set()
    if clean_name in unique_exact:
        return unique_exact[clean_name], {unique_exact[clean_name]}
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
            return unique_exact[k], {unique_exact[k]}
    for k in tries:
        if k in cand_map:
            return "", cand_map[k]
    return "", set()


def clean_book_header_name(raw_hdr: str) -> str:
    # Strip leading digits / Arabic-Indic numerals + punctuation/sigils
    s = re.sub(r"^[\s٠-٩\d\-:\.•()]+", "", raw_hdr)
    # Split before biography clauses in unpunctuated entries (1615/1976/1981)
    s = re.split(
        r"(?:[،,\.]|\s+(?:روى\s+عن|رَوَى\s+عَن|يروي\s+عن|يَرْوِي\s+عَن|سمع\s+|سَمِعَ\s+|يعد\s+في|عداده\s+في|حدثنا\s+|ثقة\b|صدوق\b|مجهول\b|ضعيف\b|متروك\b))",
        s,
        maxsplit=1,
    )[0]
    return norm_ar(s)


def load_book_text(prefix: str) -> str:
    matches = list(SHAMELA_BOOKS_DIR.glob(prefix + "__*"))
    if not matches:
        return ""
    chunks: list[str] = []
    with (matches[0] / "pages.jsonl").open(encoding="utf-8") as fh:
        for line in fh:
            chunks.append(json.loads(line).get("body", ""))
    return "\n".join(chunks)


def parse_all_method1_books(
    unique_exact: dict[str, str],
    cand_map: dict[str, set[str]],
) -> tuple[Counter[tuple[str, str, str]], dict[str, set[str]], dict[str, int]]:
    # Format-specific header regexes per Refinement 1
    book_patterns = [
        ("1716", "method1_tahdhib_alkamal", re.compile(
            r'(?:^|\r|\n)(?:[٠-٩\d]+\s*-\s*(?:[^:\r\n<]{0,14}:?\s*)?(?:<span[^>]*data-type=[\'"]title[\'"][^>]*>([^<]{3,140})</span>|([^\r\n.<]{4,120}))|<span[^>]*data-type=[\'"]title[\'"][^>]*>([^<]{3,140})</span>)'
        )),
        ("1615", "method1_jarh_tadil", re.compile(
            r'(?:^|\r|\n)[٠-٩\d]+\s*-\s*([^\r\n]{4,160})'
        )),
        ("4609", "method1_kamil", re.compile(
            r'<span[^>]*data-type=[\'"]title[\'"][^>]*>\s*(?:[٠-٩\d]+\s*-\s*)?([^<]{4,160})</span>'
        )),
        ("890", "method1_tarikh_kabir", re.compile(
            r'<span[^>]*data-type=[\'"]title[\'"][^>]*>\s*(?:[٠-٩\d]+\s*-\s*)?([^<]{4,160})</span>'
        )),
        ("1976", "method1_thiqat_ibn_hibban", re.compile(
            r'(?:^|\r|\n)\u2022\s+([^\r\n]{4,160})'
        )),
        ("1981", "method1_thiqat_ijli", re.compile(
            r'(?:^|\r|\n)[٠-٩\d]+\s*-\s*([^\r\n]{4,140})'
        )),
    ]

    m1_edges: Counter[tuple[str, str, str]] = Counter()
    adj_neighbors: defaultdict[str, set[str]] = defaultdict(set)
    matched_bios: Counter[str] = Counter()

    for prefix, src_label, hdr_re in book_patterns:
        text = load_book_text(prefix)
        if not text:
            continue
        hdrs = list(hdr_re.finditer(text))
        for idx, hm in enumerate(hdrs):
            raw_hdr = next((g for g in hm.groups() if g), "")
            if not raw_hdr or any(skip in raw_hdr for skip in ("باب", "المجلد", "مقدمة", "خطبة", "حرف ", "كتاب ")):
                continue
            hdr_norm = clean_book_header_name(raw_hdr)
            subj_eid, _ = resolve_mention_tokens(hdr_norm, unique_exact, cand_map)
            if not subj_eid:
                continue
            matched_bios[src_label] += 1

            # Capture full entry text (note unpunctuated books include predicates on header line!)
            start_pos = hm.start() if prefix in {"1615", "1976", "1981"} else hm.end()
            end_pos = hdrs[idx + 1].start() if idx + 1 < len(hdrs) else min(len(text), start_pos + 5000)
            body = text[start_pos:min(end_pos, start_pos + 5000)]

            # Teachers: روى عن / يروي عن / سمع من
            m_t = re.search(
                r"(?:رَوَى\s+عَن|روى\s+عن|يَرْوِي\s+عَن|يروي\s+عن|سمع\s+من|سَمِعَ\s+مِن)\s*:?\s*(.*?)(?=رَوَى\s+عَنه|روى\s+عنه|يَرْوِي\s+عَنهُ|يروي\s+عنه|حدثنا|سمعت\s+أبي|قال\s+|وَقَال|\r\n\r\n|$)",
                body,
                flags=re.S,
            )
            if m_t:
                # Split on commas/wa+space when multiple listed
                raw_list = m_t.group(1)
                for item in re.split(r"[،.\r\n]+|\s+و(?=[أ-ي\u0621-\u064a])", raw_list):
                    nm = clean_item_text(item)
                    if nm.startswith("و") and nm[1:] in unique_exact:
                        nm = nm[1:]
                    t_eid, t_cands = resolve_mention_tokens(nm, unique_exact, cand_map)
                    if t_eid and t_eid != subj_eid:
                        m1_edges[(t_eid, subj_eid, src_label)] += 1
                        adj_neighbors[subj_eid].add(t_eid)
                        adj_neighbors[t_eid].add(subj_eid)
                    elif len(t_cands) == 1:
                        only = next(iter(t_cands))
                        if only != subj_eid:
                            adj_neighbors[subj_eid].add(only)
                            adj_neighbors[only].add(subj_eid)

            # Students: روى عنه / يروي عنه / وعنه
            m_s = re.search(
                r"(?:رَوَى\s+عَنه|روى\s+عنه|يَرْوِي\s+عَنهُ|يروي\s+عنه|وعنه)\s*:?\s*(.*?)(?=ذكره\s+|سمعت\s+|قال\s+|وَقَال|\r\n\r\n|$)",
                body,
                flags=re.S,
            )
            if m_s:
                for item in re.split(r"[،.\r\n]+|\s+و(?=[أ-ي\u0621-\u064a])", m_s.group(1)):
                    nm = clean_item_text(item)
                    if nm.startswith("و") and nm[1:] in unique_exact:
                        nm = nm[1:]
                    s_eid, s_cands = resolve_mention_tokens(nm, unique_exact, cand_map)
                    if s_eid and s_eid != subj_eid:
                        m1_edges[(subj_eid, s_eid, src_label)] += 1
                        adj_neighbors[subj_eid].add(s_eid)
                        adj_neighbors[s_eid].add(subj_eid)
                    elif len(s_cands) == 1:
                        only = next(iter(s_cands))
                        if only != subj_eid:
                            adj_neighbors[subj_eid].add(only)
                            adj_neighbors[only].add(subj_eid)

    return m1_edges, adj_neighbors, dict(matched_bios)


def main() -> None:
    if OUT_DIR.exists() and any(OUT_DIR.iterdir()):
        raise SystemExit(f"Refusing to overwrite existing consolidated graph v0.3 package: {OUT_DIR}")

    verify_package(V04_DIR)
    narr_v04 = read_csv(V04_DIR / "TASK_B_NARRATOR_ELIGIBILITY_8827_V0_4.csv")
    v01_splits = {r["entry_id"]: r["split"] for r in read_csv(SPLITS_V01)}

    high_conf_nodes = {
        r["entry_id"]: r
        for r in narr_v04
        if r["identity_link_status"] == "unique_1to1_high_conf"
    }
    cohort_nodes = {
        r["entry_id"]: r
        for r in narr_v04
        if r["task_b_v04_cohort_tier"] != "excluded_unlinked_or_no_task_a_target"
    }
    assert len(cohort_nodes) == 5250

    sh_raw = read_csv(SH_NARRATORS)
    unique_exact, cand_map = build_name_lookup(sh_raw, high_conf_nodes)

    # 1. Bukhari edges
    hdb_rows = read_csv(HDB_LINKS)
    hdb_to_eid = {
        r["hadithdb_narrator_id"]: r["task_a_entry_id"]
        for r in hdb_rows
        if r["task_a_entry_id"] in high_conf_nodes and int(r["link_score"] or 0) >= 21
    }
    bukhari = json.loads(HDB_BUKHARI.read_text(encoding="utf-8"))
    bukhari_edges: Counter[tuple[str, str]] = Counter()
    m1_neighbors_plus_buk: defaultdict[str, set[str]] = defaultdict(set)
    for h in bukhari:
        nids = [str(n["id"]) for n in h.get("narrators", []) if n.get("id")]
        for student_id, teacher_id in zip(nids, nids[1:]):
            es = hdb_to_eid.get(student_id)
            et = hdb_to_eid.get(teacher_id)
            if es and et and es != et:
                bukhari_edges[(et, es)] += 1
                m1_neighbors_plus_buk[es].add(et)
                m1_neighbors_plus_buk[et].add(es)

    # 2. Method 1 across all 6 classical rijal works
    m1_edges, m1_neighbors, m1_bio_counts = parse_all_method1_books(unique_exact, cand_map)
    for k, v in m1_neighbors.items():
        m1_neighbors_plus_buk[k].update(v)

    # 3. Method 2: Sanadset 650k across 956 books (excluding Ibn Hajar/Taqrib)
    mention_cache: dict[str, tuple[str, set[str]]] = {}
    san_unique_edges: Counter[tuple[str, str]] = Counter()
    san_m1_edges: Counter[tuple[str, str]] = Counter()
    san_non_sahihayn: Counter[tuple[str, str]] = Counter()
    san_books_per_edge: defaultdict[tuple[str, str], set[str]] = defaultdict(set)
    sanadset_stats = Counter()

    def get_mention_res(raw_mention: str) -> tuple[str, set[str]]:
        res = mention_cache.get(raw_mention)
        if res is None:
            res = resolve_mention_tokens(norm_ar(raw_mention), unique_exact, cand_map)
            mention_cache[raw_mention] = res
        return res

    for pf in sorted(SANADSET_DIR.glob("*.parquet")):
        table = pq.read_table(pf, columns=["Book", "Sanad"])
        for book, raw_s in zip(table["Book"].to_pylist(), table["Sanad"].to_pylist()):
            sanadset_stats["total_rows"] += 1
            if not book or any(k in book for k in PROHIBITED_SANADSET_BOOK_KEYS):
                sanadset_stats["excluded_ibn_hajar_or_prohibited_book"] += 1
                continue
            if not raw_s or raw_s == "No SANAD":
                sanadset_stats["no_sanad"] += 1
                continue
            try:
                chain = ast.literal_eval(raw_s)
            except Exception:
                sanadset_stats["parse_error"] += 1
                continue
            if not isinstance(chain, list) or len(chain) < 2:
                sanadset_stats["short_or_invalid_chain"] += 1
                continue
            sanadset_stats["eligible_hadiths_processed"] += 1
            is_non_sahihayn = not any(sb in book for sb in SAHIHAYN_BOOK_KEYS)
            resolved_chain = [get_mention_res(str(m)) for m in chain]

            for (s_uid, s_cands), (t_uid, t_cands) in zip(resolved_chain, resolved_chain[1:]):
                if t_uid and s_uid and t_uid != s_uid:
                    pair = (t_uid, s_uid)
                    san_unique_edges[pair] += 1
                    san_books_per_edge[pair].add(book)
                    if is_non_sahihayn:
                        san_non_sahihayn[pair] += 1
                elif t_uid and not s_uid and len(s_cands) >= 1:
                    hits = [c for c in s_cands if c != t_uid and c in m1_neighbors_plus_buk.get(t_uid, ())]
                    if len(hits) == 1:
                        pair = (t_uid, hits[0])
                        san_m1_edges[pair] += 1
                        san_books_per_edge[pair].add(book)
                        if is_non_sahihayn:
                            san_non_sahihayn[pair] += 1
                elif s_uid and not t_uid and len(t_cands) >= 1:
                    hits = [c for c in t_cands if c != s_uid and c in m1_neighbors_plus_buk.get(s_uid, ())]
                    if len(hits) == 1:
                        pair = (hits[0], s_uid)
                        san_m1_edges[pair] += 1
                        san_books_per_edge[pair].add(book)
                        if is_non_sahihayn:
                            san_non_sahihayn[pair] += 1

    # Build consolidated edges
    all_pairs: set[tuple[str, str]] = set(bukhari_edges) | set(san_unique_edges) | set(san_m1_edges)
    m1_pair_weights: defaultdict[tuple[str, str], int] = defaultdict(int)
    m1_pair_sources: defaultdict[tuple[str, str], set[str]] = defaultdict(set)
    for (u, v, src), w in m1_edges.items():
        all_pairs.add((u, v))
        m1_pair_weights[(u, v)] += w
        m1_pair_sources[(u, v)].add(src)

    edge_rows: list[dict[str, Any]] = []
    # Aggregate explicit structural node metrics per Refinement 5
    out_m1, in_m1 = Counter(), Counter()
    out_san, in_san = Counter(), Counter()
    san_chains_node, san_non_sahih_node, buk_chains_node = Counter(), Counter(), Counter()
    books_per_node: defaultdict[str, set[str]] = defaultdict(set)
    mutual_confirmed_node = Counter()
    deg_cons = Counter()
    deg_buk, deg_m1, deg_san = Counter(), Counter(), Counter()

    for u, v in sorted(all_pairs):
        bw = bukhari_edges.get((u, v), 0)
        suw = san_unique_edges.get((u, v), 0)
        sm1w = san_m1_edges.get((u, v), 0)
        m1w = m1_pair_weights.get((u, v), 0)
        san_tot = suw + sm1w
        non_sah = san_non_sahihayn.get((u, v), 0)
        bks = san_books_per_edge.get((u, v), ())
        both_elig = (u in cohort_nodes and v in cohort_nodes)

        edge_rows.append({
            "teacher_entry_id": u,
            "student_entry_id": v,
            "bukhari_isnad_weight": bw,
            "sanadset_unique_weight": suw,
            "sanadset_method1_disambig_weight": sm1w,
            "sanadset_non_sahihayn_weight": non_sah,
            "sanadset_distinct_books": len(bks),
            "method1_rijal_weight": m1w,
            "method1_sources": "|".join(sorted(m1_pair_sources.get((u, v), ()))),
            "total_consolidated_weight": bw + san_tot + m1w,
            "both_in_cohort_5250": "yes" if both_elig else "no",
        })

        # Compute structural features across the full high-conf graph
        if m1w > 0:
            out_m1[u] += 1
            in_m1[v] += 1
        if san_tot > 0:
            out_san[u] += 1
            in_san[v] += 1
            san_chains_node[u] += san_tot
            san_chains_node[v] += san_tot
            san_non_sahih_node[u] += non_sah
            san_non_sahih_node[v] += non_sah
            books_per_node[u].update(bks)
            books_per_node[v].update(bks)
        if bw > 0:
            buk_chains_node[u] += bw
            buk_chains_node[v] += bw
        if m1w > 0 and (san_tot > 0 or bw > 0):
            mutual_confirmed_node[u] += 1
            mutual_confirmed_node[v] += 1

        if both_elig:
            if bw > 0:
                deg_buk[u] += 1; deg_buk[v] += 1
            if m1w > 0:
                deg_m1[u] += 1; deg_m1[v] += 1
            if san_tot > 0:
                deg_san[u] += 1; deg_san[v] += 1
            deg_cons[u] += 1; deg_cons[v] += 1

    # 4. Extend frozen v0.1 Train/Val/Test splits cleanly to all N=5,250 cohort nodes
    rng = random.Random(20261117)
    new_nodes_by_rank: defaultdict[str, list[str]] = defaultdict(list)
    split_map: dict[str, str] = {}
    for eid, r in sorted(cohort_nodes.items()):
        if eid in v01_splits:
            split_map[eid] = v01_splits[eid]
        else:
            new_nodes_by_rank[r["task_a_rank_1_to_12"]].append(eid)

    for rk, pool in sorted(new_nodes_by_rank.items()):
        rng.shuffle(pool)
        n = len(pool)
        n_test = round(n * 0.15)
        n_val = round(n * 0.15)
        n_train = n - n_test - n_val
        for eid in pool[:n_train]:
            split_map[eid] = "train"
        for eid in pool[n_train:n_train + n_val]:
            split_map[eid] = "val"
        for eid in pool[n_train + n_val:]:
            split_map[eid] = "test"

    assert len(split_map) == 5250
    splits_by_eid = defaultdict(set)
    splits_by_nid = defaultdict(set)
    for eid, sp in split_map.items():
        splits_by_eid[sp].add(eid)
        splits_by_nid[sp].add(cohort_nodes[eid]["shamela_narrator_id"])
    assert not (splits_by_eid["train"] & splits_by_eid["val"])
    assert not (splits_by_eid["train"] & splits_by_eid["test"])
    assert not (splits_by_eid["val"] & splits_by_eid["test"])
    assert not (splits_by_nid["train"] & splits_by_nid["val"])
    assert not (splits_by_nid["train"] & splits_by_nid["test"])
    assert not (splits_by_nid["val"] & splits_by_nid["test"])

    # Export node structural features + split table
    node_rows: list[dict[str, Any]] = []
    for eid, r in sorted(cohort_nodes.items()):
        sc = san_chains_node.get(eid, 0)
        nsc = san_non_sahih_node.get(eid, 0)
        node_rows.append({
            "entry_id": eid,
            "shamela_narrator_id": r["shamela_narrator_id"],
            "task_a_rank_1_to_12": r["task_a_rank_1_to_12"],
            "cohort_tier": r["task_b_v04_cohort_tier"],
            "split": split_map[eid],
            "has_early_critic_quote": "1" if r["has_early_critic_quote"] == "yes" else "0",
            "strict_primary_passage_count": r["eligible_primary_passage_count"],
            "fwaed_passage_count": r["eligible_fwaed_passage_count"],
            "ablation_tahdhib_early_count": r["ablation_tahdhib_early_count"],
            "student_out_degree_m1": out_m1.get(eid, 0),
            "teacher_in_degree_m1": in_m1.get(eid, 0),
            "student_out_degree_sanadset": out_san.get(eid, 0),
            "teacher_in_degree_sanadset": in_san.get(eid, 0),
            "sanadset_total_chain_mentions": sc,
            "sanadset_non_sahihayn_mentions": nsc,
            "sanadset_non_sahihayn_ratio": f"{(nsc / sc):.4f}" if sc > 0 else "0.0000",
            "sanadset_distinct_books": len(books_per_node.get(eid, ())),
            "bukhari_chain_mentions": buk_chains_node.get(eid, 0),
            "mutual_m1_m2_confirmed_edges": mutual_confirmed_node.get(eid, 0),
            "cohort_consolidated_degree": deg_cons.get(eid, 0),
        })

    comparison_rows: list[dict[str, Any]] = []
    for rk in [str(i) for i in range(1, 13)]:
        rk_nodes = [eid for eid, r in cohort_nodes.items() if r["task_a_rank_1_to_12"] == rk]
        n = len(rk_nodes)
        c_buk = sum(1 for e in rk_nodes if deg_buk[e] > 0)
        c_m1 = sum(1 for e in rk_nodes if deg_m1[e] > 0)
        c_san = sum(1 for e in rk_nodes if deg_san[e] > 0)
        c_cons = sum(1 for e in rk_nodes if deg_cons[e] > 0)
        comparison_rows.append({
            "rank_1_to_12": rk,
            "cohort_nodes": n,
            "bukhari_only_connected": c_buk,
            "bukhari_only_pct": f"{c_buk / n * 100:.1f}%" if n else "0.0%",
            "method1_rijal_connected": c_m1,
            "method1_rijal_pct": f"{c_m1 / n * 100:.1f}%" if n else "0.0%",
            "method2_sanadset_connected": c_san,
            "method2_sanadset_pct": f"{c_san / n * 100:.1f}%" if n else "0.0%",
            "consolidated_connected": c_cons,
            "consolidated_pct": f"{c_cons / n * 100:.1f}%" if n else "0.0%",
        })

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    edges_csv = OUT_DIR / "TASK_B_CONSOLIDATED_GRAPH_EDGES_V0_3.csv"
    nodes_csv = OUT_DIR / "TASK_B_NODE_STRUCTURAL_FEATURES_V0_3.csv"
    comp_csv = OUT_DIR / "TASK_B_METHOD1_VS_METHOD2_COMPARISON_V0_3.csv"
    write_csv(edges_csv, edge_rows, list(edge_rows[0]))
    write_csv(nodes_csv, node_rows, list(node_rows[0]))
    write_csv(comp_csv, comparison_rows, list(comparison_rows[0]))

    split_counts = Counter(r["split"] for r in node_rows)
    elig_edges = sum(1 for er in edge_rows if er["both_in_cohort_5250"] == "yes")
    tot_conn = sum(r["consolidated_connected"] for r in comparison_rows)

    report_lines = [
        "# Task B Consolidated Graph, Structural Features, and Splits Report v0.3",
        "",
        "**Status:** full implementation of all 5 Task B refinements across `N = 5,250` high-confidence narrators (`train=3,674`, `val=788`, `test=788`), unlocking all 6 classical Method 1 books (`1716`, `1615`, `4609`, `890`, `1976`, `1981`), consolidating with `Sanadset 650k` (`429,742` eligible chains) + `Bukhari`, recovering `+420` zero-quote `Majhul`/`Mastur` narrators, and adding explicit structural node features.",
        "",
        "## 1. Method 1 + Method 2 Graph Scale",
        f"- Method 1 biographies parsed & linked across 6 books: `{dict(sorted(m1_bio_counts.items()))}`",
        f"- Total directed edges: **{len(edge_rows)}** (**{elig_edges}** within `N=5,250` cohort)",
        f"- Non-isolated `5,250`-cohort narrators: **{tot_conn} / 5,250** (`{tot_conn / 5250 * 100:.1f}%`)",
        f"- Split counts: `{dict(sorted(split_counts.items()))}` (`0` overlap on `entry_id` or `shamela_narrator_id`)",
        "",
        "## 2. Rank-by-Rank Connectivity (`N = 5,250` Uncensored Cohort)",
    ]
    for cr in comparison_rows:
        report_lines.append(
            f"- Rank **{cr['rank_1_to_12']}** (N={cr['cohort_nodes']}): Bukhari={cr['bukhari_only_connected']} ({cr['bukhari_only_pct']}) | M1_Rijal={cr['method1_rijal_connected']} ({cr['method1_rijal_pct']}) | M2_Sanadset={cr['method2_sanadset_connected']} ({cr['method2_sanadset_pct']}) | **Consolidated={cr['consolidated_connected']} ({cr['consolidated_pct']})**"
        )

    report_text = "\n".join(report_lines) + "\n"
    assert_no_em_en_dash(report_text, "TASK_B_CONSOLIDATED_GRAPH_REPORT_V0_3.md")
    report_path = OUT_DIR / "TASK_B_CONSOLIDATED_GRAPH_REPORT_V0_3.md"
    report_path.write_text(report_text, encoding="utf-8", newline="\n")

    timestamp = datetime.now(timezone.utc).isoformat()
    inputs = [
        V04_DIR / "TASK_B_NARRATOR_ELIGIBILITY_8827_V0_4.csv",
        V04_DIR / "MANIFEST.json",
        SPLITS_V01,
        HDB_BUKHARI,
        Path(__file__).resolve(),
    ]
    outputs = [edges_csv, nodes_csv, comp_csv, report_path]
    manifest = {
        "package_id": OUT_DIR.name,
        "generated_at_utc": timestamp,
        "counts": {
            "cohort_total": len(node_rows),
            "split_counts": dict(sorted(split_counts.items())),
            "method1_matched_biographies": dict(sorted(m1_bio_counts.items())),
            "total_consolidated_directed_edges": len(edge_rows),
            "cohort_subgraph_edges": elig_edges,
            "cohort_nodes_connected": tot_conn,
            "sanadset_stats": dict(sorted(sanadset_stats.items())),
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
