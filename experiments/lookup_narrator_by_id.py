"""Read-only narrator lookup CLI across the full Shamela4 DB and Task A/B/v2 artifacts.

Supports lookup by:
- ``--id`` (`shamela_narrator_id` in `narrators.parquet`, 18,989 narrators)
- ``--entry-id`` (Taqrib `entry_id`, e.g. `S3076-P077-C003-E0001`)
- ``--gold-id`` (Gold-50 validation ID 1..50)
- ``--name`` (exact or substring match on `short_name` / `long_name` in `narrators.parquet`)

Optional ``--v2-profile`` displays Task A v1.3 vs v1.4 segmentation, post-tabaqa
qualifiers, Stage 1 baseline B, and Stage 2 atomic 6D multidimensional ESA
summaries & double-counting counts.

Does not modify any datasets, frozen results, or governance files.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline"
NARRATORS_PARQUET = ROOT / "data/1_raw/Shamela4_Full_DB/_meta/narrators.parquet"
TASK_B_SPLITS_CSV = (
    PIPELINE / "task_b_graph_and_splits_v0_1_2026-11-17/TASK_B_SPLITS_ELIGIBLE_NARRATORS_V0_1.csv"
)
LINKAGE_V03_CSV = (
    PIPELINE / "task_b_historical_inputs_v0_3_2026-11-17/TASK_B_NARRATOR_LINKAGE_AND_ELIGIBILITY_8827_V0_3.csv"
)
TASK_A_TARGETS_CSV = (
    PIPELINE / "task_a_deterministic_targets_v1_3_2026-11-17/TASK_A_DETERMINISTIC_TARGETS_8827_V1_3.csv"
)
TASK_A_V14_CSV = (
    PIPELINE / "task_a_deterministic_targets_v1_4_2026-11-19/TASK_A_DETERMINISTIC_TARGETS_8827_V1_4.csv"
)
GOLD50_CSV = (
    PIPELINE / "v2_gold50_adjudication_v2_1_2026-11-19/GOLD_50_ADJUDICATED_REFERENCE_V2_1.csv"
)
GOLD50_CLAIMS_CSV = (
    PIPELINE / "v2_gold50_and_atomic_esa_v0_2_2026-11-19/GOLD_50_ATOMIC_STAGE2_CLAIMS_V2_0.csv"
)
TEST_PREDS_V1_1_CSV = (
    ROOT / "results/section4_oof_text_gnn_v1_1_2026-11-17/TEST_PREDICTIONS_V1_1.csv"
)


def _clean_val(val: Any) -> Any:
    if pd.isna(val):
        return None
    if hasattr(val, "item"):
        return val.item()
    return val


def _row_to_dict(row: pd.Series) -> dict[str, Any]:
    return {k: _clean_val(v) for k, v in row.items()}


def _truncate(text: Any, limit: int, full_text: bool) -> str:
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return ""
    s = str(text)
    if full_text or len(s) <= limit:
        return s
    return s[:limit] + f"... [truncated {len(s) - limit} chars; pass --full-text]"


def build_record(
    shamela_row: dict[str, Any] | None,
    split_row: dict[str, Any] | None,
    task_a_row: dict[str, Any] | None,
    pred_row: dict[str, Any] | None,
    v2_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rec: dict[str, Any] = {
        "shamela4_db": shamela_row,
        "task_b_split": split_row,
        "task_a_target": task_a_row,
        "v1_1_test_predictions": pred_row,
    }
    if v2_profile is not None:
        rec["v2_profile"] = v2_profile
    return rec


def lookup(
    *,
    shamela_id: int | None = None,
    entry_id: str | None = None,
    gold_id: int | None = None,
    name_query: str | None = None,
    exact_name: bool = False,
    limit: int = 10,
    include_v2_profile: bool = False,
) -> list[dict[str, Any]]:
    narrators = pd.read_parquet(NARRATORS_PARQUET)
    splits = pd.read_csv(TASK_B_SPLITS_CSV)
    linkage = pd.read_csv(LINKAGE_V03_CSV)
    task_a = pd.read_csv(TASK_A_TARGETS_CSV)
    preds = pd.read_csv(TEST_PREDS_V1_1_CSV)

    task_a_v14 = pd.read_csv(TASK_A_V14_CSV) if (include_v2_profile and TASK_A_V14_CSV.exists()) else None
    gold50 = pd.read_csv(GOLD50_CSV) if ((gold_id is not None or include_v2_profile) and GOLD50_CSV.exists()) else None
    gold_claims = (
        pd.read_csv(GOLD50_CLAIMS_CSV)
        if (include_v2_profile and GOLD50_CLAIMS_CSV.exists())
        else None
    )

    matched_ids: list[tuple[int | None, str | None, int | None]] = []

    if gold_id is not None:
        if gold50 is None:
            raise SystemExit(f"Gold-50 file not found: {GOLD50_CSV}")
        g_hit = gold50[gold50["gold_id"] == gold_id]
        if not g_hit.empty:
            gr = g_hit.iloc[0]
            sid = int(gr["shamela_narrator_id"]) if pd.notna(gr["shamela_narrator_id"]) else None
            eid = str(gr["entry_id"]) if pd.notna(gr["entry_id"]) else None
            matched_ids.append((sid, eid, gold_id))
    elif shamela_id is not None:
        matched_ids.append((shamela_id, None, None))
    elif entry_id is not None:
        sid = None
        split_hit = splits[splits["entry_id"] == entry_id]
        if not split_hit.empty and pd.notna(split_hit.iloc[0]["shamela_narrator_id"]):
            sid = int(split_hit.iloc[0]["shamela_narrator_id"])
        else:
            lnk_hit = linkage[linkage["entry_id"] == entry_id]
            if not lnk_hit.empty and pd.notna(lnk_hit.iloc[0]["shamela_narrator_id"]):
                sid = int(lnk_hit.iloc[0]["shamela_narrator_id"])
        matched_ids.append((sid, entry_id, None))
    elif name_query is not None:
        q = name_query.strip()
        if exact_name:
            mask = (narrators["short_name"].fillna("") == q) | (
                narrators["long_name"].fillna("") == q
            )
        else:
            mask = narrators["short_name"].fillna("").str.contains(q, regex=False) | (
                narrators["long_name"].fillna("").str.contains(q, regex=False)
            )
        hits = narrators[mask].head(limit)
        for sid in hits["id"].tolist():
            matched_ids.append((int(sid), None, None))

    records: list[dict[str, Any]] = []
    for sid, eid, gid in matched_ids:
        shamela_row = None
        if sid is not None:
            s_hit = narrators[narrators["id"] == sid]
            if not s_hit.empty:
                shamela_row = _row_to_dict(s_hit.iloc[0])

        split_row = None
        if eid is not None and eid != "EXTERNAL-SH12587":
            sp_hit = splits[splits["entry_id"] == eid]
        elif sid is not None:
            sp_hit = splits[splits["shamela_narrator_id"] == sid]
        else:
            sp_hit = splits.iloc[0:0]

        if not sp_hit.empty:
            split_row = _row_to_dict(sp_hit.iloc[0])
            eid = eid or split_row.get("entry_id")

        if eid is None and sid is not None:
            lnk_hit = linkage[linkage["shamela_narrator_id"] == sid]
            if not lnk_hit.empty:
                eid = str(lnk_hit.iloc[0]["entry_id"])

        task_a_row = None
        if eid is not None:
            ta_hit = task_a[task_a["entry_id"] == eid]
            if not ta_hit.empty:
                task_a_row = _row_to_dict(ta_hit.iloc[0])

        pred_row = None
        if eid is not None:
            pr_hit = preds[preds["entry_id"] == eid]
            if not pr_hit.empty:
                pred_row = _row_to_dict(pr_hit.iloc[0])
        elif sid is not None:
            pr_hit = preds[preds["shamela_narrator_id"] == sid]
            if not pr_hit.empty:
                pred_row = _row_to_dict(pr_hit.iloc[0])

        v2_profile = None
        if include_v2_profile:
            v14_row = None
            if task_a_v14 is not None and eid is not None:
                v14_hit = task_a_v14[task_a_v14["entry_id"] == eid]
                if not v14_hit.empty:
                    v14_row = _row_to_dict(v14_hit.iloc[0])

            gold_row = None
            if gold50 is not None:
                if gid is not None:
                    gh = gold50[gold50["gold_id"] == gid]
                elif eid is not None:
                    gh = gold50[gold50["entry_id"] == eid]
                elif sid is not None:
                    gh = gold50[gold50["shamela_narrator_id"] == sid]
                else:
                    gh = gold50.iloc[0:0]
                if not gh.empty:
                    gold_row = _row_to_dict(gh.iloc[0])

            stage2_summary = None
            if gold_claims is not None and gold_row is not None:
                gc = gold_claims[gold_claims["gold_id"] == gold_row["gold_id"]]
                if not gc.empty:
                    elig = gc[gc["weight_eligible"] == 1]
                    sample_units = [
                        {
                            "atomic_unit_id": r["atomic_unit_id"],
                            "speaker_canonical": r["speaker_canonical"],
                            "source_work_normalised": r["source_work_normalised"],
                            "statement_family": r["statement_family"],
                            "primary_reliability_dimension": r["primary_reliability_dimension"],
                            "conditional_scope": r["conditional_scope"],
                            "double_count_status": r["double_count_status"],
                            "weight_eligible": int(r["weight_eligible"]),
                            "clause_text_verbatim": r["clause_text_verbatim"],
                        }
                        for _, r in gc.head(8).iterrows()
                    ]
                    stage2_summary = {
                        "total_atomic_units": int(len(gc)),
                        "weight_eligible_units": int(len(elig)),
                        "double_count_breakdown": {
                            str(k): int(v) for k, v in gc["double_count_status"].value_counts().items()
                        },
                        "eligible_dimension_counts": {
                            str(k): int(v)
                            for k, v in elig["primary_reliability_dimension"].value_counts().items()
                        },
                        "eligible_family_counts": {
                            str(k): int(v) for k, v in elig["statement_family"].value_counts().items()
                        },
                        "sample_units": sample_units,
                    }

            v2_profile = {
                "task_a_v1_4": v14_row,
                "gold_50_entry": gold_row,
                "stage2_atomic_esa_summary": stage2_summary,
            }

        if shamela_row or split_row or task_a_row or pred_row or v2_profile:
            records.append(build_record(shamela_row, split_row, task_a_row, pred_row, v2_profile))

    return records


def print_human(records: list[dict[str, Any]], full_text: bool = False) -> None:
    if not records:
        print("No matching narrator found.")
        return

    for idx, rec in enumerate(records, start=1):
        if idx > 1:
            print("\n" + "=" * 72)
        s = rec["shamela4_db"]
        sp = rec["task_b_split"]
        ta = rec["task_a_target"]
        pr = rec["v1_1_test_predictions"]
        v2 = rec.get("v2_profile")

        print(f"--- Narrator Match #{idx} ---")
        if s:
            print(f"Shamela ID      : {s['id']}")
            print(f"Short Name      : {s['short_name']}")
            print(f"Long Name       : {s['long_name']}")
            print(f"Narrator Type   : {s['narrator_type']}")
            print(f"Biography Text  : {_truncate(s['biography_text'], 300, full_text)}")
            print(f"Criticism Text  : {_truncate(s['criticism_text'], 300, full_text)}")
        else:
            print("Shamela4 DB     : Not found in narrators.parquet")

        if sp:
            print("\n[Task B Modeling Cohort]")
            print(
                f"entry_id={sp['entry_id']} | split={sp['split']} | "
                f"task_a_rank_1_to_12={sp['task_a_rank_1_to_12']} | "
                f"passages={sp['eligible_primary_passage_count']} | "
                f"graph_degree={sp['eligible_graph_degree']}"
            )
        else:
            print("\n[Task B Modeling Cohort] Not in the 5,250-narrator Task B split.")

        if ta:
            print("\n[Task A v1.3 Deterministic Target]")
            print(
                f"disposition={ta['deterministic_disposition']} | "
                f"rank={ta['deterministic_rank_1_to_12']} | "
                f"span={ta['first_complete_target_span_exact']}"
            )

        if v2:
            v14 = v2.get("task_a_v1_4")
            g50 = v2.get("gold_50_entry")
            st2 = v2.get("stage2_atomic_esa_summary")
            print("\n[v2 Phase 1 Profile]")
            if v14:
                print(
                    f"Task A v1.4     : disposition={v14['deterministic_disposition']} | "
                    f"rank={v14['deterministic_rank_1_to_12']} | rule={v14['rule_id']}"
                )
                print(f"v1.4 Target Span: {v14['first_complete_target_span_exact']}")
                print(f"v1.4 Context    : {v14['context_note_spans_exact']}")
                print(f"v1.4 Post-Tabaqa: {v14['post_tabaqa_context_spans']}")
            if g50:
                print(
                    f"Gold-50 ID      : #{g50['gold_id']} ({g50['english_name']}, {g50['group_profile']})"
                )
                print(
                    f"Adjudicated (B) : stage1_rank={g50['adjudicated_stage1_rank']} "
                    f"(B={g50['adjudicated_stage1_baseline_B']}) | "
                    f"effective_tier={g50['adjudicated_effective_tier']}"
                )
                print(
                    f"Adjudication    : {g50['adjudication_status']} - {g50['adjudication_rationale']}"
                )
            if st2:
                print(
                    f"Stage 2 Units   : {st2['total_atomic_units']} atomic units "
                    f"({st2['weight_eligible_units']} weight-eligible)"
                )
                print(f"Double-Counting : {st2['double_count_breakdown']}")
                print(f"6-Dim Counts    : {st2['eligible_dimension_counts']}")
                print(f"Family Counts   : {st2['eligible_family_counts']}")
                print("Sample Stage 2 Claims (first 8):")
                for su in st2["sample_units"]:
                    print(
                        f"  [{su['atomic_unit_id']}] {su['speaker_canonical']} ({su['source_work_normalised']}) | "
                        f"{su['statement_family']} | {su['primary_reliability_dimension']} | "
                        f"scope={su['conditional_scope']} | elig={su['weight_eligible']} ({su['double_count_status']})"
                    )
                    print(f"    {su['clause_text_verbatim']}")

        if pr:
            print(
                f"\n[Frozen v1.1 Test Predictions (True Rank = {pr['true_rank_1_to_12']})]"
            )
            for col, val in pr.items():
                if col.startswith("pred_") and "_arm4_" in col:
                    print(f"  {col}: {val}")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Lookup a narrator by Shamela ID, entry_id, Gold-50 ID, or Arabic name."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--id", type=int, help="shamela_narrator_id (18,989-row DB)")
    group.add_argument("--entry-id", type=str, help="Taqrib entry_id (e.g. S3076-P077-C003-E0001)")
    group.add_argument("--gold-id", type=int, help="Gold-50 validation ID (1..50)")
    group.add_argument("--name", type=str, help="Arabic name query against short_name / long_name")
    parser.add_argument("--exact-name", action="store_true", help="Require exact match for --name")
    parser.add_argument("--limit", type=int, default=10, help="Max matches for --name (default: 10)")
    parser.add_argument("--full-text", action="store_true", help="Print full biography/criticism text")
    parser.add_argument("--v2-profile", action="store_true", help="Include v2 Stage 1/2 profile & Gold-50 reconciliation")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    args = parser.parse_args()

    records = lookup(
        shamela_id=args.id,
        entry_id=args.entry_id,
        gold_id=args.gold_id,
        name_query=args.name,
        exact_name=args.exact_name,
        limit=args.limit,
        include_v2_profile=args.v2_profile or (args.gold_id is not None),
    )
    if args.json:
        print(json.dumps(records, ensure_ascii=False, indent=2))
    else:
        print_human(records, full_text=args.full_text)


if __name__ == "__main__":
    main()
