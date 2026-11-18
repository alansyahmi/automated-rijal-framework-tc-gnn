#!/usr/bin/env python3
"""Prepare a reproducible, blinded AI-review sample from the Taqrib shadow scan.

This creates review materials only. It does not assign or modify rank labels.
"""

from __future__ import annotations

import csv
import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SHADOW_DIR = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline/rank_label_shadow_run_v1_2026-11-15"
OUTPUT_DIR = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline/rank_label_agent_review_v1_2026-11-15"
SAMPLE_SEED = 20261115
PER_RANK = 5
NO_CUE_CONTROLS = 10


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    if OUTPUT_DIR.exists():
        raise SystemExit(f"Refusing to overwrite existing review package: {OUTPUT_DIR}")

    run_manifest_path = SHADOW_DIR / "RUN_MANIFEST.json"
    run_manifest = json.loads(run_manifest_path.read_text(encoding="utf-8"))
    expected = run_manifest["outputs"]
    input_names = ["ENTRY_INDEX.csv", "CUE_OCCURRENCES.csv", "CANDIDATE_RULE_HITS.csv"]
    for name in input_names:
        actual = hashlib.sha256((SHADOW_DIR / name).read_bytes()).hexdigest()
        if expected.get(name) != actual:
            raise SystemExit(f"Shadow-run input hash mismatch for {name}: {actual}")

    entries = read_csv(SHADOW_DIR / "ENTRY_INDEX.csv")
    occurrences = read_csv(SHADOW_DIR / "CUE_OCCURRENCES.csv")
    rule_hits = read_csv(SHADOW_DIR / "CANDIDATE_RULE_HITS.csv")
    entry_by_id = {row["entry_id"]: row for row in entries}
    cue_rows_by_rank: dict[int, list[dict[str, str]]] = defaultdict(list)
    cue_ids_by_entry: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in occurrences:
        rank = int(row["source_rank_anchor"])
        cue_rows_by_rank[rank].append(row)
        cue_ids_by_entry[row["entry_id"]].append(row)

    rank_rule_ids_by_entry: dict[str, list[str]] = defaultdict(list)
    for row in rule_hits:
        if row.get("rule_family") == "taxonomy_rank":
            rank_rule_ids_by_entry[row["entry_id"]].append(row["rule_id"])

    rng = random.Random(SAMPLE_SEED)
    selected: list[tuple[str, dict[str, str] | None, str]] = []
    used_entry_ids: set[str] = set()
    anchor_ranks_with_hits: list[int] = []
    for rank in range(1, 13):
        rank_rows = cue_rows_by_rank.get(rank, [])
        if not rank_rows:
            continue
        anchor_ranks_with_hits.append(rank)
        by_cue: dict[str, list[str]] = defaultdict(list)
        for row in rank_rows:
            by_cue[row["cue_id"]].append(row["entry_id"])
        cue_ids = list(by_cue)
        rng.shuffle(cue_ids)
        picks: list[tuple[str, dict[str, str]]] = []
        while len(picks) < PER_RANK:
            made_progress = False
            for cue_id in cue_ids:
                candidates = sorted(set(by_cue[cue_id]) - used_entry_ids)
                rng.shuffle(candidates)
                if not candidates:
                    continue
                entry_id = candidates[0]
                occurrence = next(
                    row for row in rank_rows
                    if row["cue_id"] == cue_id and row["entry_id"] == entry_id
                )
                picks.append((entry_id, occurrence))
                used_entry_ids.add(entry_id)
                made_progress = True
                if len(picks) == PER_RANK:
                    break
            if not made_progress:
                raise SystemExit(f"Could not obtain {PER_RANK} unique entries for rank anchor {rank}")
        selected.extend((entry_id, occurrence, f"rank_{rank:02d}_cue") for entry_id, occurrence in picks)

    no_cue_ids = [
        row["entry_id"] for row in entries
        if row["entry_id"] not in cue_ids_by_entry
        and row["entry_id"] not in rank_rule_ids_by_entry
        and row["entry_id"] not in used_entry_ids
    ]
    rng.shuffle(no_cue_ids)
    if len(no_cue_ids) < NO_CUE_CONTROLS:
        raise SystemExit("Not enough no-cue control entries")
    selected.extend((entry_id, None, "no_exact_rank_cue_control") for entry_id in no_cue_ids[:NO_CUE_CONTROLS])

    rng.shuffle(selected)
    OUTPUT_DIR.mkdir(parents=True)
    reviewer_fields = [
        "case_id", "local_book_id", "shamela_book_id", "local_page_id", "shamela_page_id",
        "printed_page_num", "entry_number_verbatim", "source_chunk_index",
        "duplicate_printed_entry_number_on_page", "entry_text_verbatim",
    ]
    reviewer_rows: list[dict[str, Any]] = []
    key_rows: list[dict[str, Any]] = []
    for index, (entry_id, selected_occurrence, group) in enumerate(selected, start=1):
        case_id = f"ARV1-{index:03d}"
        source = entry_by_id[entry_id]
        reviewer_rows.append({
            "case_id": case_id,
            **{field: source[field] for field in reviewer_fields if field != "case_id"},
        })
        all_occurrences = cue_ids_by_entry.get(entry_id, [])
        key_rows.append({
            "case_id": case_id,
            "entry_id": entry_id,
            "sample_group_internal": group,
            "sampling_anchor_rank_internal": (
                selected_occurrence["source_rank_anchor"] if selected_occurrence else ""
            ),
            "sampling_anchor_cue_id_internal": selected_occurrence["cue_id"] if selected_occurrence else "",
            "sampling_anchor_cue_text_internal": selected_occurrence["cue_text_exact"] if selected_occurrence else "",
            "all_source_cue_anchors_internal": ";".join(sorted({row["source_rank_anchor"] for row in all_occurrences})),
            "all_source_cue_ids_internal": ";".join(sorted({row["cue_id"] for row in all_occurrences})),
            "all_exact_cue_texts_internal": " || ".join(sorted({row["cue_text_exact"] for row in all_occurrences})),
            "all_rank_registry_rule_ids_internal": ";".join(sorted(set(rank_rule_ids_by_entry.get(entry_id, [])))),
            "selected_match_offsets_internal": (
                f"{selected_occurrence['match_start_char']}:{selected_occurrence['match_end_char']}"
                if selected_occurrence else ""
            ),
        })

    template_fields = [
        "case_id", "case_type", "candidate_rank_1_to_12_or_none_or_abstain",
        "candidate_status", "assessment_span_exact", "complete_span_from_entry",
        "definition_conditions_supported_by_entry", "external_evidence_needed",
        "unlisted_candidate_span_exact", "confidence_high_medium_low", "reviewer_rationale",
    ]
    template_rows = [{"case_id": row["case_id"], **{field: "" for field in template_fields[1:]}} for row in reviewer_rows]
    write_csv(OUTPUT_DIR / "BLINDED_REVIEW_PACKET.csv", reviewer_rows, reviewer_fields)
    write_csv(OUTPUT_DIR / "AI_REVIEW_TEMPLATE_BLANK.csv", template_rows, template_fields)
    write_csv(OUTPUT_DIR / "INTERNAL_SAMPLE_KEY.csv", key_rows, list(key_rows[0]))

    readme = f"""# Taqrīb rank-cue AI review pilot v1

**Purpose:** blinded AI-assisted review of a small sample of full local Taqrīb entries. The reviewers propose a candidate interpretation or abstain; they do not create approved labels.

## Sample

- {len(reviewer_rows)} entries total: {len(anchor_ranks_with_hits) * PER_RANK} exact-cue cases ({PER_RANK} per source rank anchor with hits) and {NO_CUE_CONTROLS} entries without any exact rank-inventory cue or active rank-candidate registry phrase.
- Source rank anchors represented: {', '.join(map(str, anchor_ranks_with_hits))}. The v0 inventory had no exact occurrences for ranks 11 and 12, so those ranks are not tested by this sample.
- Source entries are unique in the sample. Sampling seed: {SAMPLE_SEED}.
- No-cue controls are not asserted to be negative examples; they may contain unlisted rank wording.

## Blinding and review

Give each reviewer only `BLINDED_REVIEW_PACKET.csv`, `AI_REVIEW_TEMPLATE_BLANK.csv`, and the rank definitions in `IBN_HAJAR_12_RANK_SOURCE_INVENTORY_V0.md`. Do not give them `INTERNAL_SAMPLE_KEY.csv`, the shadow-run cue hits, or other reviewers' results before their first pass. The source text is shown in full with its locators. Record a candidate rank separately from whether the entry itself establishes every condition in the definition. If required evidence is absent, mark the proposal as requiring external evidence or abstain; never force a rank.

## Interpretation limits

AI reviewers are not Arabic-trained human experts, and agreement among AI agents is not independent human validation. Their outputs are proposals for triage. This purposive sample cannot estimate corpus-wide precision, recall, or coverage. Do not overwrite frozen annotations, assign production labels, infer narrator reliability, or use the sample as model-training data.

`INTERNAL_SAMPLE_KEY.csv` maps cases to the hidden sample strata and exact shadow-run cues. Keep it separate until all blinded first-pass outputs are saved.
"""
    (OUTPUT_DIR / "README.md").write_text(readme, encoding="utf-8", newline="\n")

    files = [
        "BLINDED_REVIEW_PACKET.csv", "AI_REVIEW_TEMPLATE_BLANK.csv", "INTERNAL_SAMPLE_KEY.csv", "README.md"
    ]
    manifest = {
        "package": "Taqrib rank-cue AI review pilot v1",
        "generated_by": "dataset_discovery/target_feasibility/prepare_taqrib_rank_agent_review_v1.py",
        "sample_seed": SAMPLE_SEED,
        "sample_size": len(reviewer_rows),
        "exact_cue_cases_per_source_rank_anchor": PER_RANK,
        "no_exact_rank_cue_controls": NO_CUE_CONTROLS,
        "source_rank_anchors_represented": anchor_ranks_with_hits,
        "source_rank_anchors_not_represented_due_to_zero_exact_cue_hits": [rank for rank in range(1, 13) if rank not in anchor_ranks_with_hits],
        "unique_entry_ids": len({row["entry_id"] for row in key_rows}),
        "input_hashes": {name: expected[name] for name in input_names},
        "outputs": {name: hashlib.sha256((OUTPUT_DIR / name).read_bytes()).hexdigest() for name in files},
        "rank_labels_assigned": 0,
        "auto_accept": False,
    }
    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    (OUTPUT_DIR / "REVIEW_MANIFEST.json").write_bytes(manifest_bytes)
    manifest_hash = sha256_bytes(manifest_bytes)
    (OUTPUT_DIR / "REVIEW_MANIFEST.sha256").write_text(
        f"{manifest_hash}  REVIEW_MANIFEST.json\n", encoding="ascii", newline="\n"
    )
    print(json.dumps({
        "output_dir": str(OUTPUT_DIR),
        "sample_size": len(reviewer_rows),
        "anchor_ranks": anchor_ranks_with_hits,
        "unique_entry_ids": len({row["entry_id"] for row in key_rows}),
        "manifest_sha256": manifest_hash,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
