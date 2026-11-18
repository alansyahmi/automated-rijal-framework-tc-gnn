#!/usr/bin/env python3
"""Report per-candidate-phrase and reviewed-statement counts over consolidated v0.1.

Documents explicit inclusion rules and denominators across Batch 01 + Batch 02
(916 unique review cases across 866 unique source entries; 922 lossless ledger
rows) without assigning canonical ranks or numeric scores.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PIPELINE = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline"
CONS_DIR = PIPELINE / "evaluation_statement_decisions_consolidated_v0_1_2026-11-16"
B2_FRAME_DIR = PIPELINE / "evaluation_statement_occurrence_review_batch_02_v0_1_2026-11-16"
INV_DIR = PIPELINE / "evaluation_statement_occurrence_inventory_v0_1_2026-11-16"
OUT_DIR = PIPELINE / "evaluation_statement_decisions_report_v0_1_2026-11-16"


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


def verify_package(directory: Path) -> dict[str, Any]:
    manifest_path = directory / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    sidecar = (directory / "MANIFEST.sha256").read_text(encoding="ascii").split()[0]
    if digest(manifest_path) != sidecar:
        raise SystemExit(f"MANIFEST.sha256 mismatch in {directory}")
    for name, expected in manifest["outputs"].items():
        if digest(directory / name) != expected:
            raise SystemExit(f"Output hash mismatch for {directory.name}/{name}")
    return manifest


def stratum_note(stratum: str) -> str:
    if stratum == "rare_phrase_exhaustive":
        return "Exhaustive rare-phrase stratum (<=15 corpus entries; all remaining hits included). Suitable for within-phrase counts, not corpus prevalence."
    if stratum == "common_phrase_sampled":
        return "Deterministic 10-entry sample of common phrase (>15 corpus entries). Do not extrapolate raw counts to corpus-wide totals."
    return "Zero exact occurrences in the 8,827-entry local Taqrib index; retained in vocabulary only."


def format_counter(counts: Counter[str]) -> str:
    return ";".join(f"{k}:{v}" for k, v in sorted(counts.items()))


def main() -> None:
    if OUT_DIR.exists() and any(OUT_DIR.iterdir()):
        raise SystemExit(f"Refusing to overwrite existing report package: {OUT_DIR}")

    verify_package(CONS_DIR)
    verify_package(B2_FRAME_DIR)
    verify_package(INV_DIR)

    cons_cases = read_csv(CONS_DIR / "CONSOLIDATED_REVIEW_CASE_DECISIONS_V0_1.csv")
    cons_ledger = read_csv(CONS_DIR / "CONSOLIDATED_DECISION_LEDGER_922_ROWS_V0_1.csv")
    links = read_csv(B2_FRAME_DIR / "PHRASE_HIT_TO_REVIEW_CASE_LINKS_V0_1.csv")
    plan = read_csv(B2_FRAME_DIR / "BATCH_02_PHRASE_SAMPLING_PLAN_V0_1.csv")
    occ_summary = read_csv(INV_DIR / "PHRASE_OCCURRENCE_SUMMARY_V0_1.csv")

    case_by_id = {r["review_case_id"]: r for r in cons_cases}
    occ_sum_by_cid = {r["candidate_id"]: r for r in occ_summary}
    plan_by_cid = {r["candidate_id"]: r for r in plan}

    # Map candidate_id -> linked hits inside the 916 consolidated review cases
    links_in_reviewed: dict[str, list[dict[str, str]]] = defaultdict(list)
    for link in links:
        if link["review_case_id"] in case_by_id:
            links_in_reviewed[link["candidate_id"]].append(link)

    # Also track Batch 01 direct occurrence_ids per candidate_id
    b1_ledger_by_cid: dict[str, list[dict[str, str]]] = defaultdict(list)
    for lr in cons_ledger:
        if lr["batch_source"] == "batch_01":
            # Look up candidate_id via link table
            occ_id = lr["source_occurrence_ids"]
            matched_links = [lk for lk in links if lk["occurrence_id"] == occ_id]
            assert len(matched_links) == 1, f"Missing link for B1 {occ_id}"
            b1_ledger_by_cid[matched_links[0]["candidate_id"]].append(lr)

    phrase_report_rows: list[dict[str, Any]] = []
    for cid, p_row in sorted(plan_by_cid.items()):
        s_row = occ_sum_by_cid[cid]
        c_links = links_in_reviewed.get(cid, [])
        b1_hits = [lk for lk in c_links if lk["prior_user_decision"] == "accept"]
        b2_sel_hits = [lk for lk in c_links if lk["phrase_hit_selected_for_batch_02"] == "yes"]
        co_hits = [
            lk for lk in c_links
            if lk["prior_user_decision"] != "accept" and lk["phrase_hit_selected_for_batch_02"] != "yes"
        ]

        reviewed_case_ids = sorted({lk["review_case_id"] for lk in c_links})
        direct_case_ids = sorted({lk["review_case_id"] for lk in b1_hits + b2_sel_hits})
        reviewed_entries = sorted({case_by_id[rc]["entry_id"] for rc in reviewed_case_ids})

        direct_match_use = Counter(case_by_id[rc]["statement_match_use"] for rc in direct_case_ids)
        direct_family = Counter(case_by_id[rc]["statement_family"] for rc in direct_case_ids)
        all_match_use = Counter(case_by_id[rc]["statement_match_use"] for rc in reviewed_case_ids)
        all_family = Counter(case_by_id[rc]["statement_family"] for rc in reviewed_case_ids)

        direct_attr = sum(bool(case_by_id[rc]["attribution"].strip()) for rc in direct_case_ids)
        direct_qual = sum(bool(case_by_id[rc]["qualification"].strip()) for rc in direct_case_ids)
        direct_non_subj = sum(
            bool(case_by_id[rc]["referent"].strip())
            and not case_by_id[rc]["referent"].startswith("The entry subject")
            for rc in direct_case_ids
        )

        record = {
            "candidate_id": cid,
            "phrase_candidate_exact": p_row["phrase_candidate_exact"],
            "selection_stratum": p_row["selection_stratum"],
            "sampling_method": p_row["sampling_method"],
            "corpus_exact_occurrences": int(s_row["exact_substring_occurrences"]),
            "corpus_unique_source_entries": int(s_row["entries_with_exact_substring"]),
            "corpus_arabic_letter_bounded_occurrences": int(s_row["arabic_letter_bounded_occurrences"]),
            "batch_01_accepted_hits": len(b1_hits),
            "batch_02_selected_hits": len(b2_sel_hits),
            "co_occurring_unselected_hits_in_reviewed_cases": len(co_hits),
            "total_linked_hits_in_reviewed_cases": len(c_links),
            "direct_selected_cases": len(direct_case_ids),
            "reviewed_distinct_cases": len(reviewed_case_ids),
            "reviewed_distinct_entries": len(reviewed_entries),
            "direct_complete_statement": direct_match_use["complete_statement"],
            "direct_component_of_larger_statement": direct_match_use["component_of_larger_statement"],
            "direct_unrelated_substring": direct_match_use["unrelated_substring"],
            "direct_unresolved": direct_match_use["unresolved"],
            "direct_family_counts": format_counter(direct_family),
            "all_linked_cases_match_use_counts": format_counter(all_match_use),
            "all_linked_cases_family_counts": format_counter(all_family),
            "direct_attribution_count": direct_attr,
            "direct_qualification_count": direct_qual,
            "direct_non_subject_referent_count": direct_non_subj,
            "inclusion_and_denominator_note": stratum_note(p_row["selection_stratum"]),
        }
        for k, v in record.items():
            assert_no_em_en_dash(str(v), f"{cid}.{k}")
        phrase_report_rows.append(record)

    stratum_rank = {"rare_phrase_exhaustive": 0, "common_phrase_sampled": 1, "no_exact_occurrences": 2}
    phrase_report_rows.sort(
        key=lambda r: (stratum_rank[r["selection_stratum"]], -r["reviewed_distinct_cases"], r["candidate_id"])
    )

    # Group reviewed statement texts across the 916 consolidated cases
    stmt_groups: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for c in cons_cases:
        key = (
            c["statement_match_use"],
            c["statement_text_verbatim"],
            c["statement_family"],
            c["statement_domain"],
            c["claim_content"],
            c["claim_mode"],
            c["wording_force"],
        )
        stmt_groups[key].append(c)

    stmt_rows: list[dict[str, Any]] = []
    for key, group in sorted(stmt_groups.items(), key=lambda kv: (-len(kv[1]), kv[0][0], kv[0][1])):
        match_use, stmt_text, family, domain, content, mode, force = key
        record = {
            "statement_match_use": match_use,
            "statement_text_verbatim": stmt_text,
            "statement_family": family,
            "statement_domain": domain,
            "claim_content": content,
            "claim_mode": mode,
            "wording_force": force,
            "reviewed_case_count": len(group),
            "reviewed_distinct_entries": len({g["entry_id"] for g in group}),
            "cases_with_attribution": sum(bool(g["attribution"].strip()) for g in group),
            "cases_with_qualification": sum(bool(g["qualification"].strip()) for g in group),
            "cases_with_non_subject_referent": sum(
                bool(g["referent"].strip()) and not g["referent"].startswith("The entry subject")
                for g in group
            ),
            "sample_review_case_ids": ";".join(g["review_case_id"] for g in group[:5]),
        }
        for k, v in record.items():
            assert_no_em_en_dash(str(v), f"stmt.{k}")
        stmt_rows.append(record)

    assert sum(r["reviewed_case_count"] for r in stmt_rows) == len(cons_cases)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    phrase_csv = OUT_DIR / "PER_CANDIDATE_PHRASE_REVIEW_COUNTS_V0_1.csv"
    stmt_csv = OUT_DIR / "REVIEWED_STATEMENT_TEXT_COUNTS_V0_1.csv"
    write_csv(phrase_csv, phrase_report_rows, list(phrase_report_rows[0]))
    write_csv(stmt_csv, stmt_rows, list(stmt_rows[0]))

    # Diagnostics for markdown report
    total_linked_hits = sum(r["total_linked_hits_in_reviewed_cases"] for r in phrase_report_rows)
    total_direct_hits = sum(r["batch_01_accepted_hits"] + r["batch_02_selected_hits"] for r in phrase_report_rows)
    total_co_hits = sum(r["co_occurring_unselected_hits_in_reviewed_cases"] for r in phrase_report_rows)
    stratum_counts = Counter(r["selection_stratum"] for r in phrase_report_rows)

    phrases_with_unrelated = [r for r in phrase_report_rows if r["direct_unrelated_substring"] > 0]
    phrases_with_non_subj = [r for r in phrase_report_rows if r["direct_non_subject_referent_count"] > 0]
    high_component_common = [
        r for r in phrase_report_rows
        if r["selection_stratum"] == "common_phrase_sampled" and r["direct_component_of_larger_statement"] >= 5
    ]

    report_lines = [
        "# Evaluative Statement Phrase and Statement Count Report v0.1",
        "",
        "**Status:** verified count report over consolidated Batch 01 + Batch 02 user decisions (`916` unique review cases; `866` unique source entries). Zero canonical ranks or numeric scores assigned.",
        "",
        "## 1. Inclusion Rules and Denominators (Read Before Interpreting Any Count)",
        "",
        "1. **Corpus inventory denominator (`PHRASE_OCCURRENCES_V0_1.csv`):** `8,827` numbered local *Taqrib* entries yielded `11,478` raw exact-substring hits across `205` candidate phrase strings (`203` from candidate vocabulary v0.1 + `2` discussion praise modifiers). Deduplicating overlapping character intervals within each entry produced `9,508` overlap-span cases (`UNIQUE_OVERLAP_SPAN_REVIEW_FRAME_V0_1.csv`).",
        "2. **Reviewed sample inclusion rules:**",
        "   - **Batch 01 (`33` occurrences):** purposive illustrative selection (first Arabic-letter-bounded hit, or first exact hit) for 33 discussion phrases, mapping onto `30` overlap-span cases (`3` of which overlap Batch 02 selections).",
        "   - **Batch 02 (`889` overlap-span cases):** stratified selection excluding the `33` Batch 01 accepted `occurrence_id`s:",
        f"     - `rare_phrase_exhaustive` (**{stratum_counts['rare_phrase_exhaustive']}** phrases, `<= 15` distinct corpus entries): **all** remaining hits included exhaustively.",
        f"     - `common_phrase_sampled` (**{stratum_counts['common_phrase_sampled']}** phrases, `> 15` distinct corpus entries): **up to 10** distinct entries sampled deterministically via SHA-256 ordering (`seed = shamela4-occ-review-batch02-v0.1-2026-11-16`), one earliest occurrence per entry.",
        f"     - `no_exact_occurrences` (**{stratum_counts['no_exact_occurrences']}** phrases): `0` hits in the local numbered-entry index.",
        "3. **Consolidated reviewed denominator:** `916` unique overlap-span `review_case_id`s (`866` distinct source entries; `922` lossless decision ledger rows). Inside those `916` cases, **`{0}`** total raw phrase hits are linked (`{1}` directly selected/accepted hits + `{2}` co-occurring overlapping hits).".format(total_linked_hits, total_direct_hits, total_co_hits),
        "4. **Non-independence warning:** Because phrase hits overlap (e.g., `ثقة`, `حافظ`, and `ثقة حافظ` all fire on the same span) and common phrases are capped at `10` entries while rare phrases are exhaustive, **do not sum per-phrase counts** or treat sample shares as corpus-wide prevalence.",
        "",
        "## 2. Key Per-Phrase Findings (`PER_CANDIDATE_PHRASE_REVIEW_COUNTS_V0_1.csv`)",
        "",
        "### A. Phrases with Direct `unrelated_substring` False Positives",
        "",
        *[
            f"- `{r['candidate_id']}` (`{r['phrase_candidate_exact']}`, `{r['selection_stratum']}`): **{r['direct_unrelated_substring']}** of `{r['direct_selected_cases']}` direct cases (`{r['corpus_exact_occurrences']}` raw corpus hits vs. `{r['corpus_arabic_letter_bounded_occurrences']}` word-bounded hits)."
            for r in phrases_with_unrelated
        ],
        "",
        "### B. Phrases with Non-Subject Referents (Relatives or Third Parties in Direct Cases)",
        "",
        *[
            f"- `{r['candidate_id']}` (`{r['phrase_candidate_exact']}`): **{r['direct_non_subject_referent_count']}** of `{r['direct_selected_cases']}` direct cases refer to someone other than the entry subject (e.g., sister/aunt `أم المؤمنين`, father/ancestor `الصحابة`/`الصحابي`, Talhah `أحد العشرة`, Anas `صحابي معروف`, unnamed chain woman `لا تعرف`, or Baqiyyah's teachers `مجهول`)."
            for r in phrases_with_non_subj
        ],
        "",
        "### C. Common Sampled Phrases Frequently Embedded Inside Larger Statements (`>= 5` of `10` direct cases)",
        "",
        *[
            f"- `{r['candidate_id']}` (`{r['phrase_candidate_exact']}`): **{r['direct_component_of_larger_statement']}** `component_of_larger_statement` vs. **{r['direct_complete_statement']}** `complete_statement` out of `{r['direct_selected_cases']}` direct cases."
            for r in high_component_common
        ],
        "",
        "## 3. Reviewed Statement-Text Summary (`REVIEWED_STATEMENT_TEXT_COUNTS_V0_1.csv`)",
        "",
        f"- Distinct `(statement_match_use, statement_text_verbatim, family, domain, content, mode, force)` combinations across the `916` reviewed cases: **{len(stmt_rows)}**.",
        "- Top 15 reviewed statement forms in the sample (counts reflect sampling cap of 10 per common phrase plus overlap co-occurrence):",
        "",
        "| `statement_text_verbatim` (or blank if unrelated) | `statement_match_use` | `statement_family` | Cases | Entries |",
        "| --- | --- | --- | ---: | ---: |",
        *[
            f"| `{sr['statement_text_verbatim'] or '(unrelated_substring)'}` | `{sr['statement_match_use']}` | `{sr['statement_family']}` | {sr['reviewed_case_count']} | {sr['reviewed_distinct_entries']} |"
            for sr in stmt_rows[:15]
        ],
        "",
    ]
    report_text = "\n".join(report_lines)
    assert_no_em_en_dash(report_text, "PHRASE_AND_STATEMENT_COUNT_REPORT_V0_1.md")
    report_path = OUT_DIR / "PHRASE_AND_STATEMENT_COUNT_REPORT_V0_1.md"
    report_path.write_text(report_text, encoding="utf-8", newline="\n")

    readme_text = "\n".join([
        "# Evaluative Statement Phrase and Statement Count Report v0.1",
        "",
        "Per-candidate-phrase (`205` phrases) and per-statement-text (`916` consolidated review cases) count tables with explicit inclusion rules, sampling strata, and denominators.",
        "",
        "- [PHRASE_AND_STATEMENT_COUNT_REPORT_V0_1.md](PHRASE_AND_STATEMENT_COUNT_REPORT_V0_1.md): inclusion rules, denominators, false-positive/referent findings, and top reviewed statement forms.",
        "- [PER_CANDIDATE_PHRASE_REVIEW_COUNTS_V0_1.csv](PER_CANDIDATE_PHRASE_REVIEW_COUNTS_V0_1.csv): all `205` candidate phrases with corpus vs. Batch 01/02 counts and direct-case vs. all-linked-case breakdowns.",
        "- [REVIEWED_STATEMENT_TEXT_COUNTS_V0_1.csv](REVIEWED_STATEMENT_TEXT_COUNTS_V0_1.csv): grouped statement-text counts across all `916` consolidated cases.",
        "- `MANIFEST.json` and `MANIFEST.sha256`: input and output SHA-256 digests.",
        "",
    ])
    assert_no_em_en_dash(readme_text, "README.md")
    readme_path = OUT_DIR / "README.md"
    readme_path.write_text(readme_text, encoding="utf-8", newline="\n")

    inputs = [
        CONS_DIR / "CONSOLIDATED_REVIEW_CASE_DECISIONS_V0_1.csv",
        CONS_DIR / "CONSOLIDATED_DECISION_LEDGER_922_ROWS_V0_1.csv",
        CONS_DIR / "MANIFEST.json",
        B2_FRAME_DIR / "PHRASE_HIT_TO_REVIEW_CASE_LINKS_V0_1.csv",
        B2_FRAME_DIR / "BATCH_02_PHRASE_SAMPLING_PLAN_V0_1.csv",
        B2_FRAME_DIR / "MANIFEST.json",
        INV_DIR / "PHRASE_OCCURRENCE_SUMMARY_V0_1.csv",
        INV_DIR / "MANIFEST.json",
        Path(__file__).resolve(),
    ]
    outputs = [phrase_csv, stmt_csv, report_path, readme_path]
    manifest = {
        "package_id": OUT_DIR.name,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "verified per-phrase and reviewed-statement count report over consolidated v0.1; zero canonical ranks or numeric scores assigned",
        "counts": {
            "candidate_phrases_reported": len(phrase_report_rows),
            "consolidated_review_cases": len(cons_cases),
            "unique_source_entries": len({r["entry_id"] for r in cons_cases}),
            "total_linked_phrase_hits_in_reviewed_cases": total_linked_hits,
            "direct_selected_or_b1_hits": total_direct_hits,
            "co_occurring_unselected_hits": total_co_hits,
            "distinct_statement_text_groups": len(stmt_rows),
            "phrases_with_unrelated_substring": len(phrases_with_unrelated),
            "phrases_with_non_subject_referent": len(phrases_with_non_subj),
            "canonical_ranks_assigned": 0,
            "numeric_scores_assigned": 0,
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
