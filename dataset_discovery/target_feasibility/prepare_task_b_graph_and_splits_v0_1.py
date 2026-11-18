#!/usr/bin/env python3
"""Build Task B transmission graph (Bukhari + Tahdhib al-Kamal), narrator-disjoint splits, and Gate C checks v0.1.

Implements TODO lines 54-55 and Gate C:
1. Extracts validated Bukhari isnad transmission edges from bukhari_sultania_copy.json
   mapped onto high-confidence HadithDB <-> Task A links.
2. Extracts precision-filtered teacher-student edges (روى عن / روى عنه) from
   1716__تهذيب-الكمال-في-أسماء-الرجال/pages.jsonl (non-Taqrib source) restricted
   to unambiguous single-match Shamela4/Task A narrators.
3. Plans stratified narrator-disjoint 70/15/15 Train/Val/Test splits (seed=20261117)
   over the eligible primary-text Task B cohort, preserving all 12 ranks.
4. Verifies strict zero-overlap across splits and zero prohibited Taqrib leakage.
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
TASK_B_V03 = PIPELINE / "task_b_historical_inputs_v0_3_2026-11-17"
HDB_BUKHARI = ROOT / "data/1_raw/hadithdb/bukhari_sultania_copy.json"
TK_PAGES = ROOT / "data/1_raw/Shamela4_Full_DB/26__التراجم-والطبقات/1716__تهذيب-الكمال-في-أسماء-الرجال/pages.jsonl"
SH_NARRATORS = ROOT / "data/2_interim/shamela4_narrator_audit/narrators.csv"
OUT_DIR = PIPELINE / "task_b_graph_and_splits_v0_1_2026-11-17"

DIACRITICS_RE = re.compile(r"[\u064b-\u065f\u0670\u0640\u200c]")
ENTRY_SPLIT_RE = re.compile(r'(?:^|\r|\n)(?:[٠-٩\d]+\s*-\s*[^:\n]{0,12}:?\s*)?<span[^>]*data-type="title"[^>]*>(.*?)</span>')


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


def clean_tk_item(item: str) -> str:
    # Strip trailing editorial notes after '-' or '(' or 'في ...'
    s = re.sub(r"\([^)]*\)", " ", item)
    s = re.split(r"\s-\s|\sوصحح|\sوهو\s|\sفي\s|\sإن\s+كان|\sعلى\s+خلاف|\sقال\s+", s)[0]
    return norm_ar(s)


def main() -> None:
    if OUT_DIR.exists() and any(OUT_DIR.iterdir()):
        raise SystemExit(f"Refusing to overwrite existing Task B graph/splits package: {OUT_DIR}")

    narrator_rows = read_csv(TASK_B_V03 / "TASK_B_NARRATOR_LINKAGE_AND_ELIGIBILITY_8827_V0_3.csv")
    hdb_rows = read_csv(TASK_B_V03 / "TASK_B_HADITHDB_NARRATOR_LINKS_1524_V0_3.csv")
    passages = read_csv(TASK_B_V03 / "TASK_B_ELIGIBLE_HISTORICAL_PASSAGES_V0_3.csv")

    # 1. Leakage check on passages before doing anything
    for p in passages:
        t = p["source_work_normalised"]
        g = p["historical_attribution_critic"]
        assert not any(k in t for k in ("تقريب", "تحرير", "تهذيب التهذيب", "لسان الميزان", "الإصابة", "تعجيل")), f"Leakage work found: {t}"
        assert "ابن حجر" not in g, f"Leakage critic found: {g}"

    high_conf_nodes = {
        r["entry_id"]: r
        for r in narrator_rows
        if r["identity_link_status"] == "unique_1to1_high_conf"
    }
    eligible_nodes = {
        eid: r
        for eid, r in high_conf_nodes.items()
        if r["task_b_feature_eligibility"] == "eligible_assigned_with_primary_text"
    }

    # Build Shamela short_name exact index strictly for unique unambiguous matching
    sh_raw = read_csv(SH_NARRATORS)
    nid_to_eid = {r["shamela_narrator_id"]: r["entry_id"] for r in high_conf_nodes.values()}
    exact_sn_to_eids: defaultdict[str, list[str]] = defaultdict(list)
    for sr in sh_raw:
        nid = sr["id"]
        if nid in nid_to_eid:
            sn = norm_ar(sr["short_name"])
            if len(sn.split()) >= 2:
                exact_sn_to_eids[sn].append(nid_to_eid[nid])

    # Keep ONLY globally unique normalized short_name -> single entry_id for TK edge matching!
    unique_name_to_eid: dict[str, str] = {
        name: eids[0] for name, eids in exact_sn_to_eids.items() if len(set(eids)) == 1
    }

    # 2. Extract Bukhari isnad edges
    hdb_to_eid = {
        r["hadithdb_narrator_id"]: r["task_a_entry_id"]
        for r in hdb_rows
        if r["task_a_entry_id"] in high_conf_nodes and int(r["link_score"] or 0) >= 21
    }
    bukhari = json.loads(HDB_BUKHARI.read_text(encoding="utf-8"))
    edge_weights: Counter[tuple[str, str, str]] = Counter()
    for h in bukhari:
        nids = [str(n["id"]) for n in h.get("narrators", []) if n.get("id")]
        for teacher_or_student_a, b in zip(nids, nids[1:]):
            ea = hdb_to_eid.get(teacher_or_student_a)
            eb = hdb_to_eid.get(b)
            if ea and eb and ea != eb:
                edge_weights[(ea, eb, "bukhari_isnad_edge")] += 1

    # 3. Parse Tahdhib al-Kamal entries & extract teacher (روى عن) / student (روى عنه) edges
    full_chunks: list[str] = []
    with TK_PAGES.open(encoding="utf-8") as fh:
        for line in fh:
            full_chunks.append(json.loads(line).get("body", ""))
    tk_text = "\n".join(full_chunks)
    parts = ENTRY_SPLIT_RE.split(tk_text)
    # parts[1::2] = titles, parts[2::2] = bodies
    tk_entries_matched = 0
    for title_raw, body in zip(parts[1::2], parts[2::2]):
        t_norm = norm_ar(re.sub(r"[،,].*$", "", title_raw))
        subj_eid = unique_name_to_eid.get(t_norm)
        if not subj_eid:
            # Also try prefix 3 or 4 words of title
            tw = t_norm.split()
            for klen in (4, 3, 2):
                if len(tw) >= klen and " ".join(tw[:klen]) in unique_name_to_eid:
                    subj_eid = unique_name_to_eid[" ".join(tw[:klen])]
                    break
        if not subj_eid:
            continue
        tk_entries_matched += 1

        # Normalize section labels cleanly
        m_teachers = re.search(r"رَوَى عَن:\s*(.*?)(?=رَوَى عَنه:|قال |وَقَال |$)", body, flags=re.S)
        if m_teachers:
            t_block = m_teachers.group(1)
            for item in re.split(r"[،.\r\n]+", t_block):
                nm = clean_tk_item(item)
                nm = re.sub(r"^و", "", nm).strip() if nm.startswith("و") and nm not in unique_name_to_eid else nm
                if nm in unique_name_to_eid:
                    teacher_eid = unique_name_to_eid[nm]
                    if teacher_eid != subj_eid:
                        edge_weights[(teacher_eid, subj_eid, "tahdhib_alkamal_rawa_an")] += 1

        m_students = re.search(r"رَوَى عَنه:\s*(.*?)(?=ذكره |قال |وَقَال |$)", body, flags=re.S)
        if m_students:
            s_block = m_students.group(1)
            for item in re.split(r"[،.\r\n]+", s_block):
                nm = clean_tk_item(item)
                nm = re.sub(r"^و", "", nm).strip() if nm.startswith("و") and nm not in unique_name_to_eid else nm
                if nm in unique_name_to_eid:
                    student_eid = unique_name_to_eid[nm]
                    if student_eid != subj_eid:
                        edge_weights[(subj_eid, student_eid, "tahdhib_alkamal_rawa_anhu")] += 1

    edge_rows: list[dict[str, Any]] = []
    for (u, v, src), w in sorted(edge_weights.items()):
        edge_rows.append({
            "source_entry_id": u,
            "target_entry_id": v,
            "edge_source": src,
            "weight": w,
            "both_in_eligible_cohort": "yes" if (u in eligible_nodes and v in eligible_nodes) else "no",
        })

    # 4. Stratified 70/15/15 Narrator-Disjoint Train/Val/Test splits over eligible_nodes (seed=20261117)
    rng = random.Random(20261117)
    by_rank: defaultdict[str, list[str]] = defaultdict(list)
    for eid, r in sorted(eligible_nodes.items()):
        by_rank[r["task_a_rank_1_to_12"]].append(eid)

    split_map: dict[str, str] = {}
    split_rank_table: list[dict[str, Any]] = []
    for rk in [str(i) for i in range(1, 13)]:
        pool = list(by_rank.get(rk, []))
        rng.shuffle(pool)
        n = len(pool)
        n_test = max(1, round(n * 0.15)) if n >= 5 else (1 if n >= 3 else 0)
        n_val = max(1, round(n * 0.15)) if n >= 6 else (1 if n >= 4 else 0)
        n_train = n - n_test - n_val
        for eid in pool[:n_train]:
            split_map[eid] = "train"
        for eid in pool[n_train:n_train + n_val]:
            split_map[eid] = "val"
        for eid in pool[n_train + n_val:]:
            split_map[eid] = "test"
        split_rank_table.append({
            "rank_1_to_12": rk,
            "total_eligible": n,
            "train_count": n_train,
            "val_count": n_val,
            "test_count": n_test,
        })

    # Strict disjointness check across splits on entry_id and shamela_narrator_id
    splits_by_eid = defaultdict(set)
    splits_by_nid = defaultdict(set)
    for eid, sp in split_map.items():
        splits_by_eid[sp].add(eid)
        splits_by_nid[sp].add(eligible_nodes[eid]["shamela_narrator_id"])
    assert not (splits_by_eid["train"] & splits_by_eid["val"])
    assert not (splits_by_eid["train"] & splits_by_eid["test"])
    assert not (splits_by_eid["val"] & splits_by_eid["test"])
    assert not (splits_by_nid["train"] & splits_by_nid["val"])
    assert not (splits_by_nid["train"] & splits_by_nid["test"])
    assert not (splits_by_nid["val"] & splits_by_nid["test"])

    split_rows: list[dict[str, Any]] = []
    deg_elig = Counter()
    for er in edge_rows:
        if er["both_in_eligible_cohort"] == "yes":
            deg_elig[er["source_entry_id"]] += 1
            deg_elig[er["target_entry_id"]] += 1
    for eid, r in sorted(eligible_nodes.items()):
        split_rows.append({
            "entry_id": eid,
            "shamela_narrator_id": r["shamela_narrator_id"],
            "hadithdb_narrator_id": r["hadithdb_narrator_id"],
            "task_a_rank_1_to_12": r["task_a_rank_1_to_12"],
            "eligible_primary_passage_count": r["eligible_primary_passage_count"],
            "eligible_graph_degree": deg_elig.get(eid, 0),
            "split": split_map[eid],
        })

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    edges_csv = OUT_DIR / "TASK_B_GRAPH_EDGES_V0_1.csv"
    splits_csv = OUT_DIR / "TASK_B_SPLITS_ELIGIBLE_NARRATORS_V0_1.csv"
    rank_dist_csv = OUT_DIR / "TASK_B_SPLIT_PER_RANK_SUMMARY_V0_1.csv"
    write_csv(edges_csv, edge_rows, list(edge_rows[0]))
    write_csv(splits_csv, split_rows, list(split_rows[0]))
    write_csv(rank_dist_csv, split_rank_table, list(split_rank_table[0]))

    edge_src_counts = Counter(r["edge_source"] for r in edge_rows)
    elig_edge_src_counts = Counter(r["edge_source"] for r in edge_rows if r["both_in_eligible_cohort"] == "yes")
    nodes_with_edge = sum(1 for r in split_rows if int(r["eligible_graph_degree"]) > 0)
    split_counts = Counter(r["split"] for r in split_rows)

    report_lines = [
        "# Task B Graph, Narrator-Disjoint Splits, and Gate C Readiness Report v0.1 (TODO Lines 54-59)",
        "",
        "**Status:** constructed zero-leakage transmission graph (`Bukhari` isnads + `Tahdhib al-Kamal` teacher/student lists) and narrator-disjoint stratified `70/15/15` Train/Val/Test splits (`seed=20261117`). Leakage and split-disjointness assertions passed.",
        "",
        "## 1. Validated Graph Coverage",
        f"- Total directed edges across high-confidence Task A nodes (`7,961`): **{len(edge_rows)}** (`{dict(sorted(edge_src_counts.items()))}`)",
        f"- Edges with BOTH endpoints inside the `4,830`-node eligible Task B cohort: **{sum(elig_edge_src_counts.values())}** (`{dict(sorted(elig_edge_src_counts.items()))}`)",
        f"- Eligible narrators with graph degree `>= 1`: **{nodes_with_edge} / {len(split_rows)}** (`{nodes_with_edge / len(split_rows) * 100:.1f}%`)",
        f"- *Tahdhīb al-Kamāl* (`1716`) entries matched uniquely: `{tk_entries_matched}`",
        "",
        "## 2. Narrator-Disjoint Stratified Splits (`N = 4,830` Eligible Narrators)",
        f"- Partition totals: `{dict(sorted(split_counts.items()))}` (`0` overlap on `entry_id` or `shamela_narrator_id`)",
        "- Source-work overlap note (`TODO` line 54): the same classical reference collections (especially `تهذيب الكمال` and `الجرح والتعديل`) supply independent non-*Taqrīb* passages across partitions; all narrator identities and *Taqrīb*-derived text remain strictly disjoint and excluded.",
        "",
        "## 3. Per-Rank Split Distribution (`12` Original Ranks Preserved)",
    ]
    for sr in split_rank_table:
        report_lines.append(
            f"- Rank **{sr['rank_1_to_12']}**: total=`{sr['total_eligible']}` | train=`{sr['train_count']}` | val=`{sr['val_count']}` | test=`{sr['test_count']}`"
        )

    report_text = "\n".join(report_lines) + "\n"
    assert_no_em_en_dash(report_text, "TASK_B_GATE_C_READINESS_REPORT_V0_1.md")
    report_path = OUT_DIR / "TASK_B_GATE_C_READINESS_REPORT_V0_1.md"
    report_path.write_text(report_text, encoding="utf-8", newline="\n")

    timestamp = datetime.now(timezone.utc).isoformat()
    inputs = [
        TASK_B_V03 / "TASK_B_NARRATOR_LINKAGE_AND_ELIGIBILITY_8827_V0_3.csv",
        TASK_B_V03 / "TASK_B_HADITHDB_NARRATOR_LINKS_1524_V0_3.csv",
        TASK_B_V03 / "MANIFEST.json",
        HDB_BUKHARI,
        Path(__file__).resolve(),
    ]
    outputs = [edges_csv, splits_csv, rank_dist_csv, report_path]
    manifest = {
        "package_id": OUT_DIR.name,
        "generated_at_utc": timestamp,
        "counts": {
            "eligible_narrators": len(split_rows),
            "split_counts": dict(sorted(split_counts.items())),
            "total_directed_edges": len(edge_rows),
            "eligible_subgraph_edges": sum(elig_edge_src_counts.values()),
            "eligible_nodes_with_degree_ge_1": nodes_with_edge,
            "edge_source_counts": dict(sorted(edge_src_counts.items())),
            "leakage_checks_passed": True,
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
