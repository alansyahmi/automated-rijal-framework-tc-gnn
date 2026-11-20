#!/usr/bin/env python3
"""Build Stage 1 Master Zero-Leakage Taqrib (3076) Feature + Graph Dataset & Splits (v2).

Reads:
  - data/2_interim/rijal_fyp_modelling_pipeline/bilgin_grounded_targets_v2_2026-11-20/BILGIN_GROUNDED_TAQRIB_TAHRIR_8827_V2.csv
  - data/2_interim/rijal_fyp_modelling_pipeline/task_a_deterministic_targets_v1_4_2026-11-19/TASK_A_DETERMINISTIC_TARGETS_8827_V1_4.csv
  - data/2_interim/rijal_fyp_modelling_pipeline/task_b_consolidated_graph_v0_3_2026-11-17/TASK_B_CONSOLIDATED_GRAPH_EDGES_V0_3.csv

Outputs to:
  data/2_interim/rijal_fyp_modelling_pipeline/taqrib_v2_master_dataset_2026-11-20/
    - TAQRIB_V2_MASTER_NODES_8827.csv
    - TAQRIB_V2_GRAPH_EDGES.csv
    - TAQRIB_V2_MASTER_REPORT.md
    - MANIFEST.json
    - MANIFEST.sha256
"""

from __future__ import annotations

import csv
import hashlib
import json
import random
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PIPELINE = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline"
BILGIN_V2 = PIPELINE / "bilgin_grounded_targets_v2_2026-11-20/BILGIN_GROUNDED_TAQRIB_TAHRIR_8827_V2.csv"
TASK_A_V14 = PIPELINE / "task_a_deterministic_targets_v1_4_2026-11-19/TASK_A_DETERMINISTIC_TARGETS_8827_V1_4.csv"
GRAPH_EDGES_IN = PIPELINE / "task_b_consolidated_graph_v0_3_2026-11-17/TASK_B_CONSOLIDATED_GRAPH_EDGES_V0_3.csv"
OUT_DIR = PIPELINE / "taqrib_v2_master_dataset_2026-11-20"

DIACRITICS_RE = re.compile(r"[\u064b-\u065f\u0670\u0640]")

# Multi-word 11/12 checked BEFORE 2 so الثانية عشرة is never misparsed as 2
ORDINAL_ITEMS = [
    ("الحادية عشرة", 11),
    ("الثانية عشرة", 12),
    ("الأولى", 1),
    ("الثانية", 2),
    ("الثالثة", 3),
    ("الرابعة", 4),
    ("الخامسة", 5),
    ("السادسة", 6),
    ("السابعة", 7),
    ("الثامنة", 8),
    ("التاسعة", 9),
    ("العاشرة", 10),
]
ORDINAL_PATTERN = "|".join(re.escape(k) for k, _ in ORDINAL_ITEMS)
ORDINAL_TO_INT = dict(ORDINAL_ITEMS)

TABAQA_MIN_RE = re.compile(
    rf"من\s+(?:(?:كبار|صغار|أوساط|رؤوس|قدماء)\s+)?(?:الطبقة\s+)?({ORDINAL_PATTERN})\b"
)
TABAQA_FALLBACK_RE = re.compile(rf"\b({ORDINAL_PATTERN})\b")
TABAQA_SUBTIER_RE = re.compile(r"\b(كبار|رؤوس|قدماء|أوساط|صغار)\b")

SIGIL_VOCAB = {
    "ع", "خ", "م", "د", "ت", "س", "ق", "٤", "4",
    "بخ", "خت", "عخ", "تخ", "مد", "دس", "دت", "مدت",
    "قد", "فق", "ل", "ز", "سي", "كن", "ص", "عس",
    "سق", "مق", "ر", "ي", "تمييز",
}

QUAL_PATTERNS = {
    "qual_yudallis": re.compile(r"يدلس|تدليس|مدلس"),
    "qual_yursil": re.compile(r"يرسل|إرسال|كثير\s+الإرسال"),
    "qual_yukhti_yahim": re.compile(r"يهم|أوهام|يخطئ|يخطىء|خطأ|غلط|تغلط"),
    "qual_ikhtalata": re.compile(r"اختلط|خلط|خولط|تغير"),
    "qual_rumiya_bidah": re.compile(r"رمي\s+ب|رمى\s+ب|تشيع|قدر|إرجاء|نصب|خوارج|تجهم|ابتداع"),
    "qual_sayyi_hifz": re.compile(r"سيء\s+الحفظ|سوء\s+حفظ|رديء\s+الحفظ"),
    "qual_lin": re.compile(r"لين|فيه\s+لين|بعض\s+لين"),
    "qual_qalil_hadith": re.compile(r"قليل\s+الحديث|مقل"),
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_tabaqa(text: str) -> tuple[str, str]:
    s = DIACRITICS_RE.sub("", text)
    tab_num = ""
    m = TABAQA_MIN_RE.search(s)
    if m:
        tab_num = str(ORDINAL_TO_INT[m.group(1)])
    else:
        m2 = TABAQA_FALLBACK_RE.search(s)
        if m2:
            tab_num = str(ORDINAL_TO_INT[m2.group(1)])
        elif ("صحابي" in s or "صحابية" in s) and "لا صحبة" not in s and "لا تصح" not in s:
            tab_num = "1"

    subtier = "unspecified"
    ms = TABAQA_SUBTIER_RE.search(s)
    if ms:
        tok = ms.group(1)
        if tok in {"كبار", "رؤوس", "قدماء"}:
            subtier = "kibar"
        elif tok == "أوساط":
            subtier = "awsat"
        elif tok == "صغار":
            subtier = "sighar"

    return tab_num, subtier


def extract_sigils(text: str) -> dict[str, Any]:
    s = DIACRITICS_RE.sub("", text).strip()
    raw_tokens = s.split()
    matched: list[str] = []
    for tok in reversed(raw_tokens):
        cleaned = tok.strip("[]().،:؛")
        if not cleaned:
            continue
        if cleaned in SIGIL_VOCAB:
            matched.append(cleaned)
        else:
            break
    matched.reverse()
    tok_set = set(matched)

    has_ayn = 1 if "ع" in tok_set else 0
    has_four = 1 if ("٤" in tok_set or "4" in tok_set) else 0
    b_bukhari = 1 if ("خ" in tok_set or has_ayn) else 0
    b_muslim = 1 if ("م" in tok_set or has_ayn) else 0
    b_abudawud = 1 if ("د" in tok_set or has_four or has_ayn) else 0
    b_tirmidhi = 1 if ("ت" in tok_set or has_four or has_ayn) else 0
    b_nasai = 1 if ("س" in tok_set or has_four or has_ayn) else 0
    b_ibnmajah = 1 if ("ق" in tok_set or has_four or has_ayn) else 0
    book_cnt = b_bukhari + b_muslim + b_abudawud + b_tirmidhi + b_nasai + b_ibnmajah
    is_tamyiz = 1 if "تمييز" in tok_set else 0
    has_aux_only = 1 if (matched and book_cnt == 0 and not is_tamyiz) else 0

    return {
        "sigil_bukhari": b_bukhari,
        "sigil_muslim": b_muslim,
        "sigil_abudawud": b_abudawud,
        "sigil_tirmidhi": b_tirmidhi,
        "sigil_nasai": b_nasai,
        "sigil_ibnmajah": b_ibnmajah,
        "sigil_in_sahihayn": 1 if (b_bukhari or b_muslim) else 0,
        "sigil_canonical_book_count": book_cnt,
        "sigil_has_ayn": has_ayn,
        "sigil_has_four": has_four,
        "sigil_is_tamyiz": is_tamyiz,
        "sigil_has_aux_only": has_aux_only,
        "sigil_tokens_raw": " ".join(matched),
    }


def extract_qualifiers(text: str, ctx_spans: str, post_tab_spans: str) -> dict[str, Any]:
    s = DIACRITICS_RE.sub("", text)
    out: dict[str, Any] = {
        "taqrib_has_context_note": 1 if (ctx_spans.strip() or post_tab_spans.strip()) else 0,
    }
    for col, pat in QUAL_PATTERNS.items():
        out[col] = 1 if pat.search(s) else 0
    out["taqrib_char_len"] = len(text)
    out["taqrib_word_count"] = len(text.split())
    return out


def assign_stratified_splits(core_rows: list[dict[str, Any]], seed: int = 42) -> dict[str, str]:
    rng = random.Random(seed)
    by_pair: dict[tuple[str, str], list[str]] = defaultdict(list)
    for r in core_rows:
        by_pair[(r["tahrir_rank_bilgin_1_to_12"], r["shift_class"])].append(r["entry_id"])

    by_rank_fallback: dict[str, list[str]] = defaultdict(list)
    strata: dict[Any, list[str]] = {}
    for (rk, sc), eids in sorted(by_pair.items()):
        if len(eids) >= 3:
            strata[(rk, sc)] = sorted(eids)
        else:
            by_rank_fallback[rk].extend(eids)

    for rk, eids in sorted(by_rank_fallback.items()):
        strata[("fallback_rank", rk)] = sorted(eids)

    split_map: dict[str, str] = {}
    for _, eids in sorted(strata.items(), key=lambda x: str(x[0])):
        items = list(eids)
        rng.shuffle(items)
        n = len(items)
        if n == 1:
            split_map[items[0]] = "train"
            continue
        if n == 2:
            split_map[items[0]] = "train"
            split_map[items[1]] = "test"
            continue
        n_val = max(1, round(n * 0.15))
        n_test = max(1, round(n * 0.15))
        if n_val + n_test >= n:
            n_val = 1
            n_test = 1
        n_train = n - n_val - n_test
        for eid in items[:n_train]:
            split_map[eid] = "train"
        for eid in items[n_train : n_train + n_val]:
            split_map[eid] = "val"
        for eid in items[n_train + n_val :]:
            split_map[eid] = "test"

    return split_map


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with TASK_A_V14.open(encoding="utf-8-sig") as f:
        v14_by_id = {r["entry_id"]: r for r in csv.DictReader(f)}

    with BILGIN_V2.open(encoding="utf-8-sig") as f:
        v2_rows = list(csv.DictReader(f))

    assert len(v2_rows) == 8827, f"Expected 8827 rows, got {len(v2_rows)}"
    assert len({r["entry_id"] for r in v2_rows}) == 8827, "Duplicate entry_id found"
    assert set(v2_rows_ids := {r["entry_id"] for r in v2_rows}) == set(v14_by_id.keys()), (
        "entry_id mismatch against v1.4"
    )

    # Leakage assertion on input Taqrib text ("تحرير التقريب" and "•" must never appear; E2865 has Ibn Hajar's own "هذا تحريره")
    for r in v2_rows:
        txt = r["taqrib_text_verbatim"]
        assert "تحرير التقريب" not in txt and "•" not in txt, f"Leakage marker in {r['entry_id']}"

    score1_by_id: dict[str, int] = {}
    core_ids: set[str] = set()
    for r in v2_rows:
        eid = r["entry_id"]
        if r["taqrib_rank_bilgin_1_to_12"].strip():
            score1_by_id[eid] = int(r["taqrib_rank_bilgin_1_to_12"])
        if r["taqrib_rank_bilgin_1_to_12"].strip() and r["tahrir_rank_bilgin_1_to_12"].strip():
            core_ids.add(eid)

    assert len(core_ids) == 7258, f"Expected 7258 core cohort rows, got {len(core_ids)}"

    # Load and process graph edges
    with GRAPH_EDGES_IN.open(encoding="utf-8-sig") as f:
        raw_edges = list(csv.DictReader(f))

    sanad_out_deg: Counter[str] = Counter()
    sanad_in_deg: Counter[str] = Counter()
    sanad_out_wt: Counter[str] = Counter()
    sanad_in_wt: Counter[str] = Counter()
    sanad_max_books: Counter[str] = Counter()
    bukhari_out_deg: Counter[str] = Counter()
    bukhari_in_deg: Counter[str] = Counter()

    graph_out_deg: Counter[str] = Counter()
    graph_in_deg: Counter[str] = Counter()
    graph_out_wt: Counter[str] = Counter()
    graph_in_wt: Counter[str] = Counter()
    graph_m1_out_deg: Counter[str] = Counter()
    graph_m1_in_deg: Counter[str] = Counter()

    out_neighbors: dict[str, list[str]] = defaultdict(list)
    in_neighbors: dict[str, list[str]] = defaultdict(list)

    annotated_edges: list[dict[str, Any]] = []
    for e in raw_edges:
        t = e["teacher_entry_id"]
        s = e["student_entry_id"]
        buk_w = int(e["bukhari_isnad_weight"])
        su_w = int(e["sanadset_unique_weight"])
        sm_w = int(e["sanadset_method1_disambig_weight"])
        sdb = int(e["sanadset_distinct_books"])
        m1_w = int(e["method1_rijal_weight"])
        tot_w = int(e["total_consolidated_weight"])

        sanad_w = su_w + sm_w + buk_w
        is_sanad = 1 if sanad_w > 0 else 0
        both_core = 1 if (t in core_ids and s in core_ids) else 0

        graph_out_deg[t] += 1
        graph_in_deg[s] += 1
        graph_out_wt[t] += tot_w
        graph_in_wt[s] += tot_w
        if m1_w > 0:
            graph_m1_out_deg[t] += 1
            graph_m1_in_deg[s] += 1

        if is_sanad:
            sanad_out_deg[t] += 1
            sanad_in_deg[s] += 1
            sanad_out_wt[t] += sanad_w
            sanad_in_wt[s] += sanad_w
            if sdb > sanad_max_books[t]:
                sanad_max_books[t] = sdb
            if sdb > sanad_max_books[s]:
                sanad_max_books[s] = sdb

        if buk_w > 0:
            bukhari_out_deg[t] += 1
            bukhari_in_deg[s] += 1

        out_neighbors[t].append(s)
        in_neighbors[s].append(t)

        annotated_edges.append(
            {
                **e,
                "both_in_core_7258": both_core,
                "sanad_only_edge": is_sanad,
            }
        )

    # First pass for targets & core rows (needed for stratified splits)
    enriched_rows: list[dict[str, Any]] = []
    core_rows_for_split: list[dict[str, Any]] = []
    tabaqa_covered = 0
    sigil_covered = 0

    for r in v2_rows:
        eid = r["entry_id"]
        v14 = v14_by_id[eid]
        txt = r["taqrib_text_verbatim"]
        post_tab_spans = v14.get("post_tabaqa_context_spans", "")

        tab_num, tab_subtier = extract_tabaqa(txt)
        if tab_num:
            tabaqa_covered += 1
        sig = extract_sigils(txt)
        if sig["sigil_tokens_raw"]:
            sigil_covered += 1
        qual = extract_qualifiers(txt, r["taqrib_context_note_spans"], post_tab_spans)

        # Neighbor Score-1 stats (ZERO Score-2 leakage)
        out_ranks = [score1_by_id[n] for n in out_neighbors.get(eid, []) if n in score1_by_id]
        in_ranks = [score1_by_id[n] for n in in_neighbors.get(eid, []) if n in score1_by_id]
        out_thiqah = sum(1 for rk in out_ranks if rk <= 3)
        in_thiqah = sum(1 for rk in in_ranks if rk <= 3)

        g_out = graph_out_deg[eid]
        g_in = graph_in_deg[eid]
        g_tot = g_out + g_in

        in_core = 1 if eid in core_ids else 0
        if in_core:
            delta = int(r["tahrir_rank_bilgin_1_to_12"]) - int(r["taqrib_rank_bilgin_1_to_12"])
            shift_cls = "upgraded" if delta < 0 else ("unchanged" if delta == 0 else "downgraded")
            rank_delta_str = str(delta)
        else:
            shift_cls = ""
            rank_delta_str = ""

        row_obj = {
            "entry_id": eid,
            "entry_number_numeric": r["entry_number_numeric"],
            "printed_page_num_3076": r["printed_page_num_3076"],
            "taqrib_text_verbatim": txt,
            "taqrib_rank_bilgin_1_to_12": r["taqrib_rank_bilgin_1_to_12"],
            "taqrib_bilgin_rule_id": r["taqrib_bilgin_rule_id"],
            "taqrib_is_conditional_maqbul": r["taqrib_is_conditional_maqbul"],
            "tahrir_rank_bilgin_1_to_12": r["tahrir_rank_bilgin_1_to_12"],
            "tahrir_bilgin_rule_id": r["tahrir_bilgin_rule_id"],
            "tahrir_disposition": r["tahrir_disposition"],
            "tahrir_is_dissent": 1 if r["tahrir_disposition"] == "dissent_bal" else 0,
            "in_core_cohort_7258": in_core,
            "rank_delta": rank_delta_str,
            "shift_class": shift_cls,
            "tabaqa_1_to_12": tab_num,
            "tabaqa_subtier": tab_subtier,
            **sig,
            "taqrib_context_note_spans": r["taqrib_context_note_spans"],
            "post_tabaqa_context_spans": post_tab_spans,
            **qual,
            "sanad_out_degree": sanad_out_deg[eid],
            "sanad_in_degree": sanad_in_deg[eid],
            "sanad_total_degree": sanad_out_deg[eid] + sanad_in_deg[eid],
            "sanad_out_weight": sanad_out_wt[eid],
            "sanad_in_weight": sanad_in_wt[eid],
            "sanad_max_distinct_books": sanad_max_books[eid],
            "bukhari_out_degree": bukhari_out_deg[eid],
            "bukhari_in_degree": bukhari_in_deg[eid],
            "graph_out_degree": g_out,
            "graph_in_degree": g_in,
            "graph_total_degree": g_tot,
            "graph_out_weight": graph_out_wt[eid],
            "graph_in_weight": graph_in_wt[eid],
            "graph_is_isolated": 1 if g_tot == 0 else 0,
            "graph_out_ge2": 1 if g_out >= 2 else 0,
            "graph_m1_out_degree": graph_m1_out_deg[eid],
            "graph_m1_in_degree": graph_m1_in_deg[eid],
            "nbr_out_ranked_count": len(out_ranks),
            "nbr_out_mean_taqrib_rank": f"{sum(out_ranks)/len(out_ranks):.4f}" if out_ranks else "",
            "nbr_out_thiqah_count": out_thiqah,
            "nbr_out_thiqah_ratio": f"{out_thiqah/len(out_ranks):.4f}" if out_ranks else "",
            "nbr_in_ranked_count": len(in_ranks),
            "nbr_in_mean_taqrib_rank": f"{sum(in_ranks)/len(in_ranks):.4f}" if in_ranks else "",
            "nbr_in_thiqah_count": in_thiqah,
            "nbr_in_thiqah_ratio": f"{in_thiqah/len(in_ranks):.4f}" if in_ranks else "",
        }
        enriched_rows.append(row_obj)
        if in_core:
            core_rows_for_split.append(row_obj)

    split_map = assign_stratified_splits(core_rows_for_split, seed=42)
    split_counts: Counter[str] = Counter()
    for row_obj in enriched_rows:
        sp = split_map.get(row_obj["entry_id"], "excluded_unranked")
        row_obj["split"] = sp
        split_counts[sp] += 1

    # Assertions
    assert tabaqa_covered / len(enriched_rows) >= 0.95, f"Low tabaqa coverage: {tabaqa_covered}"
    assert sigil_covered / len(enriched_rows) >= 0.95, f"Low sigil coverage: {sigil_covered}"
    assert split_counts["train"] + split_counts["val"] + split_counts["test"] == 7258
    assert split_counts["excluded_unranked"] == 8827 - 7258

    # Rank 6 Maqbul graph_out_ge2 verification
    r6_up = [r for r in enriched_rows if r["taqrib_rank_bilgin_1_to_12"] == "6" and r["shift_class"] == "upgraded"]
    r6_down = [r for r in enriched_rows if r["taqrib_rank_bilgin_1_to_12"] == "6" and r["shift_class"] == "downgraded"]
    r6_up_ge2 = sum(r["graph_out_ge2"] for r in r6_up) / len(r6_up)
    r6_down_ge2 = sum(r["graph_out_ge2"] for r in r6_down) / len(r6_down)
    assert r6_up_ge2 > r6_down_ge2, "Expected Rank 6 upgraded out>=2 rate > downgraded"

    # Write outputs
    nodes_csv = OUT_DIR / "TAQRIB_V2_MASTER_NODES_8827.csv"
    node_fields = list(enriched_rows[0].keys())
    with nodes_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=node_fields)
        w.writeheader()
        w.writerows(enriched_rows)

    edges_csv = OUT_DIR / "TAQRIB_V2_GRAPH_EDGES.csv"
    edge_fields = list(annotated_edges[0].keys())
    with edges_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=edge_fields)
        w.writeheader()
        w.writerows(annotated_edges)

    shift_counts = Counter(r["shift_class"] for r in core_rows_for_split)
    core_non_isolated = sum(1 for r in core_rows_for_split if r["graph_is_isolated"] == 0)
    core_sanad_connected = sum(1 for r in core_rows_for_split if r["sanad_total_degree"] > 0)

    report_md = OUT_DIR / "TAQRIB_V2_MASTER_REPORT.md"
    report_lines = [
        "# Taqrīb v2 Master Feature + Graph Dataset Report (Stage 1)",
        "",
        f"- **Generated (UTC):** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%SZ')}",
        f"- **Total Taqrīb entries (`TAQRIB_V2_MASTER_NODES_8827.csv`):** {len(enriched_rows)}",
        f"- **Core supervised cohort (`in_core_cohort_7258 == 1`):** {len(core_rows_for_split)}",
        f"- **Total directed edges (`TAQRIB_V2_GRAPH_EDGES.csv`):** {len(annotated_edges)}",
        f"- **Edges with both endpoints in core 7,258:** {sum(e['both_in_core_7258'] for e in annotated_edges)}",
        f"- **Pure Sanad/Bukhari edges (`sanad_only_edge == 1`):** {sum(e['sanad_only_edge'] for e in annotated_edges)}",
        "",
        "## 1. Zero-Leakage Guarantee",
        "- All textual, *ṭabaqah*, sigil, and qualifier features are extracted strictly from Ibn Ḥajar's *Taqrīb al-Tahdhīb* (`3076`).",
        "- Verified `0` occurrences of `تحرير التقريب` or `•` in `taqrib_text_verbatim`.",
        "- All graph neighbor baseline aggregations (`nbr_out_*`, `nbr_in_*`) use **only Score 1 (`taqrib_rank_bilgin_1_to_12`)**, which precedes *Taḥrīr* (`1417 AH`) — zero Score 2 (`tahrir_rank`) leakage.",
        "",
        "## 2. Feature & Graph Coverage",
        f"- ***Ṭabaqah* extracted (`tabaqa_1_to_12`):** {tabaqa_covered} / {len(enriched_rows)} ({tabaqa_covered / len(enriched_rows) * 100:.2f}%)",
        f"- **Canonical sigils extracted (`sigil_tokens_raw`):** {sigil_covered} / {len(enriched_rows)} ({sigil_covered / len(enriched_rows) * 100:.2f}%)",
        f"- **Core 7,258 non-isolated in consolidated graph:** {core_non_isolated} / 7258 ({core_non_isolated / 7258 * 100:.2f}%)",
        f"- **Core 7,258 connected via pure Sanad/Bukhari edges:** {core_sanad_connected} / 7258 ({core_sanad_connected / 7258 * 100:.2f}%)",
        "",
        "## 3. Stratified Split Distribution (seed=42)",
        "| Split | Count | Share of 7,258 |",
        "|---|---:|---:|",
        f"| `train` | {split_counts['train']} | {split_counts['train'] / 7258 * 100:.2f}% |",
        f"| `val` | {split_counts['val']} | {split_counts['val'] / 7258 * 100:.2f}% |",
        f"| `test` | {split_counts['test']} | {split_counts['test'] / 7258 * 100:.2f}% |",
        f"| `excluded_unranked` | {split_counts['excluded_unranked']} | — |",
        "",
        "## 4. Core Shift Class Distribution (`Score 1 → Score 2`)",
        "| Shift Class | Count | Share |",
        "|---|---:|---:|",
    ]
    for sc, cnt in shift_counts.most_common():
        report_lines.append(f"| `{sc}` | {cnt} | {cnt / 7258 * 100:.2f}% |")

    report_lines.extend(
        [
            "",
            "## 5. Rank 6 (*Maqbūl*) Graph Out-Degree Signal Check",
            f"- `upgraded` (n={len(r6_up)}): `graph_out_ge2` = **{r6_up_ge2 * 100:.2f}%**",
            f"- `downgraded` (n={len(r6_down)}): `graph_out_ge2` = **{r6_down_ge2 * 100:.2f}%**",
        ]
    )
    report_md.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    manifest_files = [nodes_csv, edges_csv, report_md]
    manifest = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "script": "dataset_discovery/target_feasibility/build_taqrib_v2_master_dataset_and_splits.py",
        "total_nodes": len(enriched_rows),
        "core_cohort": len(core_rows_for_split),
        "total_edges": len(annotated_edges),
        "splits": dict(split_counts),
        "shift_counts": dict(shift_counts),
        "tabaqa_covered": tabaqa_covered,
        "sigil_covered": sigil_covered,
        "files": {p.name: {"sha256": sha256_file(p), "bytes": p.stat().st_size} for p in manifest_files},
    }
    manifest_json = OUT_DIR / "MANIFEST.json"
    manifest_json.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT_DIR / "MANIFEST.sha256").write_text(
        "\n".join(f"{sha256_file(p)}  {p.name}" for p in [*manifest_files, manifest_json]) + "\n",
        encoding="utf-8",
    )

    print("Wrote", nodes_csv)
    print("Splits:", dict(split_counts))
    print("Tabaqa:", tabaqa_covered, "| Sigils:", sigil_covered, "| Core non-isolated:", core_non_isolated)
    print(f"R6 Maqbul out>=2: upgraded={r6_up_ge2*100:.1f}% vs downgraded={r6_down_ge2*100:.1f}%")


if __name__ == "__main__":
    main()
