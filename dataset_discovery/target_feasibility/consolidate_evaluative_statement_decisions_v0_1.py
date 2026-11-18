#!/usr/bin/env python3
"""Consolidate Batch 01 (33) and Batch 02 (889) user decisions into v0.1.

Verifies input manifests, preserves a lossless 922-row decision ledger, builds
a deduplicated 916-row review-case table aligned to UNIQUE_OVERLAP_SPAN_REVIEW_FRAME_V0_1,
and keeps canonical_rank and numeric_score strictly blank.
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
B1_DIR = PIPELINE / "evaluation_statement_occurrence_user_decisions_batch_01_v0_1_2026-11-16"
B2_DIR = PIPELINE / "evaluation_statement_occurrence_user_decisions_batch_02_v0_1_2026-11-16"
FRAME_DIR = PIPELINE / "evaluation_statement_occurrence_review_batch_02_v0_1_2026-11-16"
OUT_DIR = PIPELINE / "evaluation_statement_decisions_consolidated_v0_1_2026-11-16"


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


def main() -> None:
    if OUT_DIR.exists() and any(OUT_DIR.iterdir()):
        raise SystemExit(f"Refusing to overwrite existing consolidated package: {OUT_DIR}")

    verify_package(B1_DIR)
    verify_package(B2_DIR)
    verify_package(FRAME_DIR)

    b1_rows = read_csv(B1_DIR / "HUMAN_DECISIONS_BATCH_01.csv")
    b2_rows = read_csv(B2_DIR / "HUMAN_DECISIONS_BATCH_02_V0_1.csv")
    frame_rows = read_csv(FRAME_DIR / "UNIQUE_OVERLAP_SPAN_REVIEW_FRAME_V0_1.csv")
    link_rows = read_csv(FRAME_DIR / "PHRASE_HIT_TO_REVIEW_CASE_LINKS_V0_1.csv")

    occ_to_case = {r["occurrence_id"]: r["review_case_id"] for r in link_rows}
    frame_by_case = {r["review_case_id"]: r for r in frame_rows}

    b1_by_case: dict[str, list[dict[str, str]]] = defaultdict(list)
    b2_by_case: dict[str, dict[str, str]] = {}

    ledger_rows: list[dict[str, Any]] = []

    for r in b1_rows:
        assert r["human_decision"] == "accept", f"Unexpected B1 decision: {r['human_decision']}"
        assert not r["canonical_rank"] and not r["numeric_score"]
        cid = occ_to_case[r["selected_occurrence_id"]]
        b1_by_case[cid].append(r)
        s = int(r["match_start_char_zero_based"])
        e = int(r["match_end_char_exclusive"])
        assert r["entry_text_verbatim"][s:e] == r["matched_text_verbatim"]
        ledger_rows.append({
            "decision_record_id": r["advisory_id"],
            "batch_source": "batch_01",
            "review_case_id": cid,
            "entry_id": r["entry_id"],
            "printed_page_num": r["printed_page_num"],
            "entry_number_verbatim": r["entry_number_verbatim"],
            "source_occurrence_ids": r["selected_occurrence_id"],
            "phrase_candidates_verbatim": r["phrase_candidate_exact"],
            "human_decision": r["human_decision"],
            "statement_match_use": "complete_statement" if r["phrase_candidate_exact"] not in {"ثبت", "ثقة", "جبل الحفظ", "إمام الدنيا في فقه الحديث"} else "component_of_larger_statement",
            "statement_start_char_zero_based": s,
            "statement_end_char_exclusive": e,
            "statement_text_verbatim": r["matched_text_verbatim"],
            "statement_family": r["ai_statement_family"],
            "statement_domain": r["ai_statement_domain"],
            "claim_content": r["ai_claim_content"],
            "claim_mode": r["ai_claim_mode"],
            "wording_force": r["ai_wording_force"],
            "consensus_wording": r["ai_consensus_wording"],
            "referent": r["ai_referent_note"],
            "attribution": r["ai_attribution_text"],
            "qualification": r["ai_qualification_or_scope_text"],
            "reviewer_confidence": r["ai_interpretation_confidence"],
            "span_boundary_note": r["ai_span_boundary_note"],
            "rationale": r["ai_rationale"],
            "user_decision_recorded_utc": r["user_decision_recorded_utc"],
            "user_decision_scope": r["user_decision_scope"],
            "canonical_rank": "",
            "numeric_score": "",
        })

    for r in b2_rows:
        assert r["human_decision"] == "accept", f"Unexpected B2 decision: {r['human_decision']}"
        assert not r["canonical_rank"] and not r["numeric_score"]
        cid = r["review_case_id"]
        assert cid not in b2_by_case
        b2_by_case[cid] = r
        ledger_rows.append({
            "decision_record_id": r["advisory_id"],
            "batch_source": "batch_02",
            "review_case_id": cid,
            "entry_id": r["entry_id"],
            "printed_page_num": r["printed_page_num"],
            "entry_number_verbatim": r["entry_number_verbatim"],
            "source_occurrence_ids": r["matched_occurrence_ids"],
            "phrase_candidates_verbatim": r["matched_phrases_verbatim"],
            "human_decision": r["human_decision"],
            "statement_match_use": r["human_match_use"],
            "statement_start_char_zero_based": r["human_statement_start_char_zero_based"],
            "statement_end_char_exclusive": r["human_statement_end_char_exclusive"],
            "statement_text_verbatim": r["ai_statement_text_verbatim"],
            "statement_family": r["ai_statement_family"],
            "statement_domain": r["ai_statement_domain"],
            "claim_content": r["ai_claim_content"],
            "claim_mode": r["ai_claim_mode"],
            "wording_force": r["ai_wording_force"],
            "consensus_wording": r["ai_consensus_wording"],
            "referent": r["human_referent"],
            "attribution": r["human_attribution"],
            "qualification": r["human_qualification"],
            "reviewer_confidence": r["human_confidence"],
            "span_boundary_note": r["ai_span_boundary_note"],
            "rationale": r["ai_rationale"],
            "user_decision_recorded_utc": r["user_decision_recorded_utc"],
            "user_decision_scope": r["user_decision_scope"],
            "canonical_rank": "",
            "numeric_score": "",
        })

    all_case_ids = sorted(set(b1_by_case) | set(b2_by_case))
    case_rows: list[dict[str, Any]] = []
    for cid in all_case_ids:
        frame = frame_by_case[cid]
        b1_items = b1_by_case.get(cid, [])
        b2_item = b2_by_case.get(cid)
        if b1_items and b2_item:
            batches = "batch_01_and_batch_02"
        elif b1_items:
            batches = "batch_01_only"
        else:
            batches = "batch_02_only"

        source_ids = [x["advisory_id"] for x in b1_items] + ([b2_item["advisory_id"]] if b2_item else [])
        b1_occ_ids = [x["selected_occurrence_id"] for x in b1_items]

        if b2_item is not None:
            stmt_match_use = b2_item["human_match_use"]
            stmt_role = b2_item["human_statement_role"]
            stmt_start = b2_item["human_statement_start_char_zero_based"]
            stmt_end = b2_item["human_statement_end_char_exclusive"]
            stmt_text = b2_item["ai_statement_text_verbatim"]
            stmt_family = b2_item["ai_statement_family"]
            stmt_domain = b2_item["ai_statement_domain"]
            claim_content = b2_item["ai_claim_content"]
            claim_mode = b2_item["ai_claim_mode"]
            wording_force = b2_item["ai_wording_force"]
            consensus_wording = b2_item["ai_consensus_wording"]
            referent = b2_item["human_referent"]
            attribution = b2_item["human_attribution"]
            qualification = b2_item["human_qualification"]
            confidence = b2_item["human_confidence"]
            span_note = b2_item["ai_span_boundary_note"]
            rationale = b2_item["ai_rationale"]
            if b1_items:
                b1_note = "; ".join(f"{x['advisory_id']}({x['phrase_candidate_exact']})" for x in b1_items)
                span_note = f"{span_note} Also overlaps Batch 01 accepted rows: {b1_note}."
            recorded_utc = b2_item["user_decision_recorded_utc"]
        else:
            # Batch 01 only; if 2 rows in same span (SPAN-000675, SPAN-001011), prefer longer compound row
            primary = max(b1_items, key=lambda x: (len(x["matched_text_verbatim"]), x["advisory_id"]))
            stmt_match_use = "complete_statement" if len(b1_items) == 1 else "component_of_larger_statement"
            stmt_role = primary["ai_statement_family"]
            stmt_start = primary["match_start_char_zero_based"]
            stmt_end = primary["match_end_char_exclusive"]
            stmt_text = primary["matched_text_verbatim"]
            stmt_family = primary["ai_statement_family"]
            stmt_domain = primary["ai_statement_domain"]
            claim_content = primary["ai_claim_content"]
            claim_mode = primary["ai_claim_mode"]
            wording_force = primary["ai_wording_force"]
            consensus_wording = primary["ai_consensus_wording"]
            referent = primary["ai_referent_note"]
            attribution = primary["ai_attribution_text"]
            qualification = primary["ai_qualification_or_scope_text"]
            confidence = primary["ai_interpretation_confidence"]
            span_note = primary["ai_span_boundary_note"]
            rationale = primary["ai_rationale"]
            if len(b1_items) > 1:
                others = "; ".join(f"{x['advisory_id']}({x['phrase_candidate_exact']})" for x in b1_items if x is not primary)
                span_note = f"{span_note} Co-located Batch 01 row: {others}."
            recorded_utc = primary["user_decision_recorded_utc"]

        if stmt_start != "":
            s_i, e_i = int(stmt_start), int(stmt_end)
            assert frame["source_entry_text_verbatim"][s_i:e_i] == stmt_text, f"Slice mismatch on {cid}"

        record = {
            "review_case_id": cid,
            "entry_id": frame["entry_id"],
            "printed_page_num": frame["printed_page_num"],
            "entry_number_verbatim": frame["entry_number_verbatim"],
            "review_span_start_char_zero_based": frame["review_span_start_char_zero_based"],
            "review_span_end_char_exclusive": frame["review_span_end_char_exclusive"],
            "review_span_text_verbatim": frame["review_span_text_verbatim"],
            "source_entry_text_verbatim": frame["source_entry_text_verbatim"],
            "matched_candidate_ids": frame["matched_candidate_ids"],
            "matched_phrases_verbatim": frame["matched_phrases_verbatim"],
            "matched_occurrence_ids": frame["matched_occurrence_ids"],
            "decision_batches": batches,
            "source_decision_ids": ";".join(source_ids),
            "batch_01_accepted_occurrence_ids": ";".join(b1_occ_ids),
            "batch_02_selection_basis": frame["batch_02_selection_basis"],
            "human_decision": "accept",
            "statement_match_use": stmt_match_use,
            "statement_role": stmt_role,
            "statement_start_char_zero_based": stmt_start,
            "statement_end_char_exclusive": stmt_end,
            "statement_text_verbatim": stmt_text,
            "statement_family": stmt_family,
            "statement_domain": stmt_domain,
            "claim_content": claim_content,
            "claim_mode": claim_mode,
            "wording_force": wording_force,
            "consensus_wording": consensus_wording,
            "referent": referent,
            "attribution": attribution,
            "qualification": qualification,
            "reviewer_confidence": confidence,
            "span_boundary_note": span_note,
            "rationale": rationale,
            "user_decision_recorded_utc": recorded_utc,
            "user_decision_scope": "Selected review case in this row only; no phrase-wide generalization.",
            "canonical_rank": "",
            "numeric_score": "",
        }
        for k, v in record.items():
            assert_no_em_en_dash(str(v), f"{cid}.{k}")
        case_rows.append(record)

    for lr in ledger_rows:
        for k, v in lr.items():
            assert_no_em_en_dash(str(v), f"{lr['decision_record_id']}.{k}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cases_path = OUT_DIR / "CONSOLIDATED_REVIEW_CASE_DECISIONS_V0_1.csv"
    ledger_path = OUT_DIR / "CONSOLIDATED_DECISION_LEDGER_922_ROWS_V0_1.csv"
    write_csv(cases_path, case_rows, list(case_rows[0]))
    write_csv(ledger_path, ledger_rows, list(ledger_rows[0]))

    batch_counts = Counter(r["decision_batches"] for r in case_rows)
    match_use_counts = Counter(r["statement_match_use"] for r in case_rows)
    family_counts = Counter(r["statement_family"] for r in case_rows)
    domain_counts = Counter(r["statement_domain"] for r in case_rows)
    content_counts = Counter(r["claim_content"] for r in case_rows)
    mode_counts = Counter(r["claim_mode"] for r in case_rows)
    force_counts = Counter(r["wording_force"] for r in case_rows)
    consensus_counts = Counter(r["consensus_wording"] for r in case_rows)
    conf_counts = Counter(r["reviewer_confidence"] for r in case_rows)

    unique_entries = len({r["entry_id"] for r in case_rows})
    attributed_nonblank = sum(bool(r["attribution"].strip()) for r in case_rows)
    qualified_nonblank = sum(bool(r["qualification"].strip()) for r in case_rows)

    summary_lines = [
        "# Consolidated Evaluative Statement Decisions v0.1 (Batch 01 + Batch 02)",
        "",
        "**Status:** consolidated single-reviewer acceptance across Batch 01 (`33` occurrence rows) and Batch 02 (`889` overlap-span cases). Zero canonical ranks or numeric scores assigned.",
        "",
        "## Headline Counts",
        "",
        f"- Lossless decision ledger rows (`CONSOLIDATED_DECISION_LEDGER_922_ROWS_V0_1.csv`): **{len(ledger_rows):,}** (`33` Batch 01 + `889` Batch 02)",
        f"- Unique deduplicated review cases (`CONSOLIDATED_REVIEW_CASE_DECISIONS_V0_1.csv`): **{len(case_rows):,}** out of `9,508` overlap-span cases in the local Taqrīb inventory",
        f"- Batch overlap breakdown: `batch_02_only` (**{batch_counts['batch_02_only']}**), `batch_01_only` (**{batch_counts['batch_01_only']}**), `batch_01_and_batch_02` (**{batch_counts['batch_01_and_batch_02']}**: `SPAN-000001`, `SPAN-000653`, `SPAN-001217`)",
        f"- Unique source entries covered: **{unique_entries:,}** out of `8,827` numbered local entries",
        f"- Cases with non-empty `attribution`: **{attributed_nonblank}**",
        f"- Cases with non-empty `qualification`: **{qualified_nonblank}**",
        "",
        "## Distributions Across the 916 Consolidated Review Cases",
        "",
        "### `statement_match_use`",
        *[f"- `{k}`: {v}" for k, v in sorted(match_use_counts.items())],
        "",
        "### `statement_family`",
        *[f"- `{k}`: {v}" for k, v in sorted(family_counts.items())],
        "",
        "### `statement_domain`",
        *[f"- `{k}`: {v}" for k, v in sorted(domain_counts.items())],
        "",
        "### `claim_content`",
        *[f"- `{k}`: {v}" for k, v in sorted(content_counts.items())],
        "",
        "### `claim_mode`",
        *[f"- `{k}`: {v}" for k, v in sorted(mode_counts.items())],
        "",
        "### `wording_force`",
        *[f"- `{k}`: {v}" for k, v in sorted(force_counts.items())],
        "",
        "### `consensus_wording`",
        *[f"- `{k}`: {v}" for k, v in sorted(consensus_counts.items())],
        "",
        "### `reviewer_confidence`",
        *[f"- `{k}`: {v}" for k, v in sorted(conf_counts.items())],
        "",
        "## Scope and Limitations",
        "",
        "- Decisions reflect single-reviewer acceptance of AI advisory proposals on the selected Batch 01 and Batch 02 spans only; they do not generalize automatically to unselected corpus occurrences.",
        "- Because Batch 02 exhaustively selected rare phrases (`<= 15` distinct entries) and deterministically sampled 10 distinct entries per common phrase, these percentages reflect the review sample rather than corpus-wide prevalence.",
        "- `canonical_rank` and `numeric_score` remain completely blank (`0` assigned).",
        "",
    ]
    summary_text = "\n".join(summary_lines)
    assert_no_em_en_dash(summary_text, "COVERAGE_AND_SUMMARY_V0_1.md")
    summary_path = OUT_DIR / "COVERAGE_AND_SUMMARY_V0_1.md"
    summary_path.write_text(summary_text, encoding="utf-8", newline="\n")

    readme_text = "\n".join([
        "# Consolidated Evaluative Statement Decisions v0.1",
        "",
        "Unified, hash-verified consolidation of Batch 01 (`33` rows) and Batch 02 (`889` rows) human-accepted evaluative statement annotations.",
        "",
        "- [CONSOLIDATED_REVIEW_CASE_DECISIONS_V0_1.csv](CONSOLIDATED_REVIEW_CASE_DECISIONS_V0_1.csv): **916** unique `review_case_id` rows aligned to `UNIQUE_OVERLAP_SPAN_REVIEW_FRAME_V0_1.csv`, covering **866** unique source entries.",
        "- [CONSOLIDATED_DECISION_LEDGER_922_ROWS_V0_1.csv](CONSOLIDATED_DECISION_LEDGER_922_ROWS_V0_1.csv): lossless **922**-row ledger preserving every original Batch 01 (`33`) and Batch 02 (`889`) decision record.",
        "- [COVERAGE_AND_SUMMARY_V0_1.md](COVERAGE_AND_SUMMARY_V0_1.md): full distributions across Draft Codebook v0.1 dimensions and scope caveats.",
        "- `MANIFEST.json` and `MANIFEST.sha256`: SHA-256 verification digests.",
        "",
    ])
    assert_no_em_en_dash(readme_text, "README.md")
    readme_path = OUT_DIR / "README.md"
    readme_path.write_text(readme_text, encoding="utf-8", newline="\n")

    inputs = [
        B1_DIR / "HUMAN_DECISIONS_BATCH_01.csv",
        B1_DIR / "MANIFEST.json",
        B2_DIR / "HUMAN_DECISIONS_BATCH_02_V0_1.csv",
        B2_DIR / "MANIFEST.json",
        FRAME_DIR / "UNIQUE_OVERLAP_SPAN_REVIEW_FRAME_V0_1.csv",
        FRAME_DIR / "PHRASE_HIT_TO_REVIEW_CASE_LINKS_V0_1.csv",
        FRAME_DIR / "MANIFEST.json",
        Path(__file__).resolve(),
    ]
    outputs = [cases_path, ledger_path, summary_path, readme_path]
    manifest = {
        "package_id": OUT_DIR.name,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "consolidated single-reviewer accepted statement-layer decisions; zero canonical ranks or numeric scores assigned",
        "counts": {
            "ledger_rows": len(ledger_rows),
            "unique_review_cases": len(case_rows),
            "unique_source_entries": unique_entries,
            "decision_batch_counts": dict(batch_counts),
            "statement_match_use_counts": dict(match_use_counts),
            "statement_family_counts": dict(family_counts),
            "reviewer_confidence_counts": dict(conf_counts),
            "attributed_cases": attributed_nonblank,
            "qualified_cases": qualified_nonblank,
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
