#!/usr/bin/env python3
"""Build Consolidated Task B Graph v0.2: Method 1 (Rijal Books) + Method 2 (Sanadset 650k + Bukhari).

1. Extracts encyclopedic teacher-student edges (روى عن / روى عنه) across ALL
   numbered & span-headed entries of:
   - 1716__تهذيب-الكمال-في-أسماء-الرجال
   - 1615__الجرح-والتعديل-ابن-أبي-حاتم
   - 4609__الكامل-في-ضعفاء-الرجال
   - 890__التاريخ-الكبير-للبخاري
   - 1976__الثقات-لابن-حبان
2. Streams all 650,986 hadiths in data/1_raw/sanadset/data/*.parquet (956 books),
   strictly excluding any Ibn Hajar / Taqrib titles, and resolves Sanad chains
   against both globally unique Task A narrators and Method-1-disambiguated links.
3. Reuses the exact frozen 70/15/15 narrator-disjoint splits from v0.1 (N=4,830)
   and outputs a side-by-side rank-by-rank (Ranks 1-12) coverage comparison
   between Bukhari-only, Method 1, Method 2 (Sanadset 650k), and Consolidated.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[2]
PIPELINE = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline"
TASK_B_V03 = PIPELINE / "task_b_historical_inputs_v0_3_2026-11-17"
SPLITS_V01 = PIPELINE / "task_b_graph_and_splits_v0_1_2026-11-17/TASK_B_SPLITS_ELIGIBLE_NARRATORS_V0_1.csv"
SH_NARRATORS = ROOT / "data/2_interim/shamela4_narrator_audit/narrators.csv"
SHAMELA_BOOKS_DIR = ROOT / "data/1_raw/Shamela4_Full_DB/26__التراجم-والطبقات"
HDB_BUKHARI = ROOT / "data/1_raw/hadithdb/bukhari_sultania_copy.json"
SANADSET_DIR = ROOT / "data/1_raw/sanadset/data"
OUT_DIR = PIPELINE / "task_b_consolidated_graph_v0_2_2026-11-17"

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
    # Strip trailing standalone preposition/sigil fragments
    s = re.sub(r"\s+(?:عن|في|من|و)$", "", s).strip()
    return s


def build_name_lookup(
    sh_raw: list[dict[str, str]],
    high_conf_nodes: dict[str, dict[str, str]],
) -> tuple[dict[str, str], dict[str, set[str]], dict[str, str]]:
    """Return (unique_exact_map, multi_cand_map, unique_ism_father_map) targeting high_conf entry_ids."""
    nid_to_eid = {r["shamela_narrator_id"]: r["entry_id"] for r in high_conf_nodes.values()}

    all_sn_eids: defaultdict[str, set[str]] = defaultdict(set)
    all_key_eids: defaultdict[str, set[str]] = defaultdict(set)
    all_shamela_sn: Counter[str] = Counter()

    for sr in sh_raw:
        sn = norm_ar(sr["short_name"])
        all_shamela_sn[sn] += 1
        toks = sn.split()
        if len(toks) >= 2:
            if_key = extract_ism_father_key(toks)
            nid = sr["id"]
            if nid in nid_to_eid:
                eid = nid_to_eid[nid]
                all_sn_eids[sn].add(eid)
                all_key_eids[sn].add(eid)
                all_key_eids[if_key].add(eid)
                if len(toks) >= 3:
                    all_key_eids[" ".join(toks[:3])].add(eid)
                # Also index kunya / shuhra if unambiguous in biography_json
                bj = dict(json.loads(sr["biography_json"])["summary"])
                for field in ("الشهرة", "الكنية"):
                    val = norm_ar(bj.get(field, ""))
                    if val and len(val) >= 4:
                        all_key_eids[val].add(eid)
            else:
                # Track non-Task-A Shamela collision count with dummy marker so ambiguous names stay cautious
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

    return unique_exact, cand_map, {k: next(iter(v)) for k, v in all_sn_eids.items() if len(v) == 1}


def resolve_mention_tokens(
    clean_name: str,
    unique_exact: dict[str, str],
    cand_map: dict[str, set[str]],
) -> tuple[str, set[str]]:
    """Resolve a normalized Arabic narrator mention to (unique_eid_or_empty, candidate_eid_set)."""
    if not clean_name:
        return "", set()
    if clean_name in unique_exact:
        return unique_exact[clean_name], {unique_exact[clean_name]}
    toks = clean_name.split()
    # Try longest prefix keys & core (Ism + Father) key
    if_key = extract_ism_father_key(toks)
    tries = [clean_name]
    if len(toks) >= 4:
        tries.append(" ".join(toks[:4]))
    if len(toks) >= 3:
        tries.append(" ".join(toks[:3]))
    if if_key and if_key not in tries:
        tries.append(if_key)
    # Strip trailing nisba token starting with ال
    if len(toks) >= 3 and toks[-1].startswith("ال"):
        tries.append(" ".join(toks[:-1]))

    for k in tries:
        if k in unique_exact:
            return unique_exact[k], {unique_exact[k]}
    for k in tries:
        if k in cand_map:
            return "", cand_map[k]
    return "", set()


def parse_method1_books(
    unique_exact: dict[str, str],
    cand_map: dict[str, set[str]],
) -> tuple[Counter[tuple[str, str, str]], dict[str, set[str]], dict[str, int]]:
    book_specs = [
        ("1716__تهذيب-الكمال-في-أسماء-الرجال", "method1_tahdhib_alkamal"),
        ("1615__الجرح-والتعديل-ابن-أبي-حاتم", "method1_jarh_tadil"),
        ("4609__الكامل-في-ضعفاء-الرجال", "method1_kamil"),
        ("890__التاريخ-الكبير-للبخاري-ت-المعلمي-اليماني", "method1_tarikh_kabir"),
        ("1976__الثقات-لابن-حبان", "method1_thiqat"),
    ]
    # Header pattern matching both <span data-type="title">...</span> AND numbered Shamela headings
    hdr_re = re.compile(
        r'(?:^|\r|\n)(?:[٠-٩\d]+\s*-\s*(?:[^:\r\n<]{0,16}:?\s*)?)?(?:<span[^>]*data-type="title"[^>]*>([^\n<]{3,140})</span>|([أ-ي\u0621-\u064a][^\r\n]{4,110}))(?=\r|\n|$)'
    )
    m1_edges: Counter[tuple[str, str, str]] = Counter()
    adj_neighbors: defaultdict[str, set[str]] = defaultdict(set)
    matched_bios: Counter[str] = Counter()

    for folder, src_label in book_specs:
        matches = list(SHAMELA_BOOKS_DIR.glob(folder.split("__")[0] + "__*"))
        if not matches:
            continue
        pages_path = matches[0] / "pages.jsonl"
        chunks: list[str] = []
        with pages_path.open(encoding="utf-8") as fh:
            for line in fh:
                chunks.append(json.loads(line).get("body", ""))
        text = "\n".join(chunks)

        # Locate biography headers cleanly using <span> OR numbered '^N - Name'
        num_hdr_re = re.compile(
            r'(?:^|\r|\n)(?:[٠-٩\d]+\s*-\s*(?:[^:\r\n<]{0,14}:?\s*)?(?:<span[^>]*data-type="title"[^>]*>([^<]{3,140})</span>|([^\r\n.<]{4,120}))|<span[^>]*data-type="title"[^>]*>([^<]{3,140})</span>)'
        )
        hdrs = list(num_hdr_re.finditer(text))
        for idx, hm in enumerate(hdrs):
            raw_title = hm.group(1) or hm.group(2) or hm.group(3) or ""
            title_head = re.split(r"[،,:\.]", raw_title)[0]
            subj_eid, _ = resolve_mention_tokens(norm_ar(title_head), unique_exact, cand_map)
            if not subj_eid:
                continue
            start_pos = hm.end()
            end_pos = hdrs[idx + 1].start() if idx + 1 < len(hdrs) else min(len(text), start_pos + 6000)
            body = text[start_pos:min(end_pos, start_pos + 6000)]
            matched_bios[src_label] += 1

            # Extract روى عن (teacher -> subj)
            m_t = re.search(r"(?:رَوَى\s+عَن|روى\s+عن|سمع\s+من)\s*:?\s*(.*?)(?=رَوَى\s+عَنه|روى\s+عنه|قال\s+|وَقَال|\r\n\r\n|$)", body, flags=re.S)
            if m_t:
                for item in re.split(r"[،.\r\n]+", m_t.group(1)):
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

            # Extract روى عنه (subj -> student)
            m_s = re.search(r"(?:رَوَى\s+عَنه|روى\s+عنه|وعنه)\s*:?\s*(.*?)(?=ذكره\s+|قال\s+|وَقَال|\r\n\r\n|$)", body, flags=re.S)
            if m_s:
                for item in re.split(r"[،.\r\n]+", m_s.group(1)):
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
        raise SystemExit(f"Refusing to overwrite existing consolidated graph package: {OUT_DIR}")

    narrator_rows = read_csv(TASK_B_V03 / "TASK_B_NARRATOR_LINKAGE_AND_ELIGIBILITY_8827_V0_3.csv")
    hdb_rows = read_csv(TASK_B_V03 / "TASK_B_HADITHDB_NARRATOR_LINKS_1524_V0_3.csv")
    splits = read_csv(SPLITS_V01)
    eligible_eids = {r["entry_id"] for r in splits}
    rank_by_eid = {r["entry_id"]: r["task_a_rank_1_to_12"] for r in splits}

    high_conf_nodes = {
        r["entry_id"]: r
        for r in narrator_rows
        if r["identity_link_status"] == "unique_1to1_high_conf"
    }
    sh_raw = read_csv(SH_NARRATORS)
    unique_exact, cand_map, _ = build_name_lookup(sh_raw, high_conf_nodes)

    # 1. Bukhari edges (Method 2 Sahihayn baseline)
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

    # 2. Method 1 encyclopedic teacher-student extraction
    m1_edges, m1_neighbors, m1_bio_counts = parse_method1_books(unique_exact, cand_map)
    for k, v in m1_neighbors.items():
        m1_neighbors_plus_buk[k].update(v)

    # 3. Method 2: Sanadset 650k across 950+ books (excluding any Ibn Hajar / Taqrib books)
    parquet_files = sorted(SANADSET_DIR.glob("*.parquet"))
    mention_cache: dict[str, tuple[str, set[str]]] = {}
    sanadset_stats = Counter()
    san_unique_edges: Counter[tuple[str, str]] = Counter()
    san_m1_edges: Counter[tuple[str, str]] = Counter()
    san_non_sahihayn: Counter[tuple[str, str]] = Counter()
    san_books_per_edge: defaultdict[tuple[str, str], set[str]] = defaultdict(set)

    def get_mention_res(raw_mention: str) -> tuple[str, set[str]]:
        res = mention_cache.get(raw_mention)
        if res is None:
            res = resolve_mention_tokens(norm_ar(raw_mention), unique_exact, cand_map)
            mention_cache[raw_mention] = res
        return res

    for pf in parquet_files:
        table = pq.read_table(pf, columns=["Book", "Sanad"])
        books_col = table["Book"].to_pylist()
        sanad_col = table["Sanad"].to_pylist()
        for book, raw_s in zip(books_col, sanad_col):
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
                # Edge direction: teacher (t) -> student (s)
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

    # Consolidate edges into single master edge table
    all_pairs: set[tuple[str, str]] = set(bukhari_edges) | set(san_unique_edges) | set(san_m1_edges)
    m1_pair_weights: defaultdict[tuple[str, str], int] = defaultdict(int)
    m1_pair_sources: defaultdict[tuple[str, str], set[str]] = defaultdict(set)
    for (u, v, src), w in m1_edges.items():
        all_pairs.add((u, v))
        m1_pair_weights[(u, v)] += w
        m1_pair_sources[(u, v)].add(src)

    edge_rows: list[dict[str, Any]] = []
    for u, v in sorted(all_pairs):
        bw = bukhari_edges.get((u, v), 0)
        suw = san_unique_edges.get((u, v), 0)
        sm1w = san_m1_edges.get((u, v), 0)
        m1w = m1_pair_weights.get((u, v), 0)
        edge_rows.append({
            "teacher_entry_id": u,
            "student_entry_id": v,
            "bukhari_isnad_weight": bw,
            "sanadset_unique_weight": suw,
            "sanadset_method1_disambig_weight": sm1w,
            "sanadset_non_sahihayn_weight": san_non_sahihayn.get((u, v), 0),
            "sanadset_distinct_books": len(san_books_per_edge.get((u, v), ())),
            "method1_rijal_weight": m1w,
            "method1_sources": "|".join(sorted(m1_pair_sources.get((u, v), ()))),
            "total_consolidated_weight": bw + suw + sm1w + m1w,
            "both_in_eligible_cohort": "yes" if (u in eligible_eids and v in eligible_eids) else "no",
        })

    # Compute Rank 1..12 connectivity comparison across graph ablation tiers (within N=4,830 eligible nodes)
    deg_buk = Counter()
    deg_m1 = Counter()
    deg_san = Counter()
    deg_cons = Counter()
    for er in edge_rows:
        if er["both_in_eligible_cohort"] != "yes":
            continue
        u, v = er["teacher_entry_id"], er["student_entry_id"]
        if er["bukhari_isnad_weight"] > 0:
            deg_buk[u] += 1; deg_buk[v] += 1
        if er["method1_rijal_weight"] > 0:
            deg_m1[u] += 1; deg_m1[v] += 1
        if er["sanadset_unique_weight"] + er["sanadset_method1_disambig_weight"] > 0:
            deg_san[u] += 1; deg_san[v] += 1
        deg_cons[u] += 1; deg_cons[v] += 1

    comparison_rows: list[dict[str, Any]] = []
    for rk in [str(i) for i in range(1, 13)]:
        rk_nodes = [eid for eid, r in rank_by_eid.items() if r == rk]
        n = len(rk_nodes)
        c_buk = sum(1 for e in rk_nodes if deg_buk[e] > 0)
        c_m1 = sum(1 for e in rk_nodes if deg_m1[e] > 0)
        c_san = sum(1 for e in rk_nodes if deg_san[e] > 0)
        c_cons = sum(1 for e in rk_nodes if deg_cons[e] > 0)
        comparison_rows.append({
            "rank_1_to_12": rk,
            "eligible_nodes": n,
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
    edges_csv = OUT_DIR / "TASK_B_CONSOLIDATED_GRAPH_EDGES_V0_2.csv"
    comp_csv = OUT_DIR / "TASK_B_METHOD1_VS_METHOD2_COMPARISON_V0_2.csv"
    write_csv(edges_csv, edge_rows, list(edge_rows[0]))
    write_csv(comp_csv, comparison_rows, list(comparison_rows[0]))

    elig_edges = [er for er in edge_rows if er["both_in_eligible_cohort"] == "yes"]
    tot_elig = len(eligible_eids)
    all_cons_pct = sum(r["consolidated_connected"] for r in comparison_rows) / tot_elig * 100

    report_lines = [
        "# Task B Consolidated Graph Report v0.2: Method 1 + Method 2 (Sanadset 650k + Bukhari)",
        "",
        "**Status:** consolidated classical encyclopedic transmission (`Method 1`: `1716`, `1615`, `4609`, `890`, `1976`) and empirical hadith chains (`Method 2`: `arbml/Sanadset` 650k across 956 books minus Ibn Hajar works + `Bukhari Sultania`) over the frozen `4,830`-node narrator-disjoint Task B splits.",
        "",
        "## 1. Scale & Leakage Controls",
        f"- Sanadset summary: `{dict(sorted(sanadset_stats.items()))}`",
        f"- Method 1 biographies parsed & linked: `{m1_bio_counts}`",
        f"- Distinct directed edges across high-confidence Task A nodes: **{len(edge_rows)}** (**{len(elig_edges)}** with both endpoints inside `N=4,830` eligible cohort)",
        f"- Overall non-isolated eligible narrators: **{sum(r['consolidated_connected'] for r in comparison_rows)} / {tot_elig}** (`{all_cons_pct:.1f}%`, up from `27.2%` in `v0.1`)",
        "",
        "## 2. Rank-by-Rank Graph Connectivity (`Bukhari-only` vs. `Method 1` vs. `Method 2 Sanadset` vs. `Consolidated`)",
    ]
    for cr in comparison_rows:
        report_lines.append(
            f"- Rank **{cr['rank_1_to_12']}** (N={cr['eligible_nodes']}): Bukhari={cr['bukhari_only_connected']} ({cr['bukhari_only_pct']}) | M1_Rijal={cr['method1_rijal_connected']} ({cr['method1_rijal_pct']}) | M2_Sanadset={cr['method2_sanadset_connected']} ({cr['method2_sanadset_pct']}) | **Consolidated={cr['consolidated_connected']} ({cr['consolidated_pct']})**"
        )

    report_text = "\n".join(report_lines) + "\n"
    assert_no_em_en_dash(report_text, "TASK_B_CONSOLIDATED_GRAPH_REPORT_V0_2.md")
    report_path = OUT_DIR / "TASK_B_CONSOLIDATED_GRAPH_REPORT_V0_2.md"
    report_path.write_text(report_text, encoding="utf-8", newline="\n")

    timestamp = datetime.now(timezone.utc).isoformat()
    inputs = [
        TASK_B_V03 / "TASK_B_NARRATOR_LINKAGE_AND_ELIGIBILITY_8827_V0_3.csv",
        TASK_B_V03 / "MANIFEST.json",
        SPLITS_V01,
        HDB_BUKHARI,
        Path(__file__).resolve(),
    ]
    outputs = [edges_csv, comp_csv, report_path]
    manifest = {
        "package_id": OUT_DIR.name,
        "generated_at_utc": timestamp,
        "counts": {
            "sanadset_stats": dict(sorted(sanadset_stats.items())),
            "method1_matched_biographies": m1_bio_counts,
            "total_consolidated_directed_edges": len(edge_rows),
            "eligible_subgraph_edges": len(elig_edges),
            "eligible_nodes_connected_consolidated": sum(r["consolidated_connected"] for r in comparison_rows),
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
