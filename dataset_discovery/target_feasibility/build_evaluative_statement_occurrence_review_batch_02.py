#!/usr/bin/env python3
"""Build a deduplicated, phrase-stratified context-review frame and batch 02."""
from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PIPELINE = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline"
OCC_DIR = PIPELINE / "evaluation_statement_occurrence_inventory_v0_1_2026-11-16"
OCC_FILE = OCC_DIR / "PHRASE_OCCURRENCES_V0_1.csv"
OCC_SUMMARY = OCC_DIR / "PHRASE_OCCURRENCE_SUMMARY_V0_1.csv"
OCC_MANIFEST = OCC_DIR / "MANIFEST.json"
DECISION_DIR = PIPELINE / "evaluation_statement_occurrence_user_decisions_batch_01_v0_1_2026-11-16"
DECISIONS = DECISION_DIR / "HUMAN_DECISIONS_BATCH_01.csv"
DECISION_MANIFEST = DECISION_DIR / "MANIFEST.json"
OUTPUT = PIPELINE / "evaluation_statement_occurrence_review_batch_02_v0_1_2026-11-16"
SEED = "shamela4-occ-review-batch02-v0.1-2026-11-16"
RARE_ENTRY_THRESHOLD = 15
COMMON_SAMPLE_PER_PHRASE = 10

HUMAN_FIELDS = [
    "human_match_use",
    "human_statement_role",
    "human_statement_start_char_zero_based",
    "human_statement_end_char_exclusive",
    "human_referent",
    "human_attribution",
    "human_qualification",
    "human_confidence",
    "human_notes",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\r\n")
        writer.writeheader()
        writer.writerows(rows)


def stable_key(candidate_id: str, entry_id: str) -> str:
    raw = f"{SEED}|{candidate_id}|{entry_id}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def verify_package(directory: Path, manifest_name: str, sidecar_name: str) -> dict[str, Any]:
    manifest_path = directory / manifest_name
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = (directory / sidecar_name).read_text(encoding="ascii").split()[0]
    if sha256(manifest_path) != expected:
        raise SystemExit(f"Input manifest checksum mismatch: {manifest_path}")
    for name, checksum in manifest.get("outputs", {}).items():
        output_path = directory / name
        if not output_path.is_file() or sha256(output_path) != checksum:
            raise SystemExit(f"Input package output hash mismatch: {output_path}")
    return manifest


def main() -> None:
    if OUTPUT.exists() and any(OUTPUT.iterdir()):
        raise SystemExit(f"Refusing to overwrite an existing review package: {OUTPUT}")

    occurrence_manifest = verify_package(OCC_DIR, "MANIFEST.json", "MANIFEST.sha256")
    decision_manifest = verify_package(DECISION_DIR, "MANIFEST.json", "MANIFEST.sha256")
    if sha256(OCC_FILE) != occurrence_manifest["outputs"][OCC_FILE.name]:
        raise SystemExit("Occurrence inventory input hash mismatch")
    if sha256(OCC_SUMMARY) != occurrence_manifest["outputs"][OCC_SUMMARY.name]:
        raise SystemExit("Occurrence summary input hash mismatch")
    if sha256(DECISIONS) != decision_manifest["outputs"][DECISIONS.name]:
        raise SystemExit("Prior decision input hash mismatch")

    raw_hits = read_csv(OCC_FILE)
    accepted_rows = read_csv(DECISIONS)
    accepted_occurrence_ids = {
        row["selected_occurrence_id"]
        for row in accepted_rows
        if row["human_decision"] == "accept"
    }
    if len(accepted_rows) != 33 or len(accepted_occurrence_ids) != 33:
        raise SystemExit("Expected 33 unique accepted occurrence decisions from batch 01")

    # Build connected components of overlapping phrase-match intervals within each entry.
    by_entry: dict[str, list[dict[str, str]]] = defaultdict(list)
    for hit in raw_hits:
        by_entry[hit["entry_id"]].append(hit)
    clusters: list[dict[str, Any]] = []
    hit_to_cluster: dict[str, dict[str, Any]] = {}
    for entry_id, hits in by_entry.items():
        ordered = sorted(hits, key=lambda row: (int(row["match_start_char_zero_based"]), int(row["match_end_char_exclusive"]), row["occurrence_id"]))
        active: list[dict[str, str]] = []
        active_end = -1
        for hit in ordered:
            start = int(hit["match_start_char_zero_based"])
            end = int(hit["match_end_char_exclusive"])
            if active and start >= active_end:
                cluster = {"entry_id": entry_id, "hits": active, "start": min(int(r["match_start_char_zero_based"]) for r in active), "end": max(int(r["match_end_char_exclusive"]) for r in active)}
                clusters.append(cluster)
                for member in active:
                    hit_to_cluster[member["occurrence_id"]] = cluster
                active = []
                active_end = -1
            active.append(hit)
            active_end = max(active_end, end)
        if active:
            cluster = {"entry_id": entry_id, "hits": active, "start": min(int(r["match_start_char_zero_based"]) for r in active), "end": max(int(r["match_end_char_exclusive"]) for r in active)}
            clusters.append(cluster)
            for member in active:
                hit_to_cluster[member["occurrence_id"]] = cluster

    entry_order: dict[str, int] = {entry_id: i for i, entry_id in enumerate(by_entry)}
    clusters.sort(key=lambda c: (entry_order[c["entry_id"]], c["start"], c["end"]))
    case_id_by_object = {id(cluster): f"SPAN-{i:06d}" for i, cluster in enumerate(clusters, start=1)}

    # Phrase frequency is defined by distinct source entries, not hit count.
    by_phrase: dict[str, list[dict[str, str]]] = defaultdict(list)
    phrase_meta: dict[str, dict[str, str]] = {}
    for hit in raw_hits:
        by_phrase[hit["phrase_candidate_exact"]].append(hit)
        phrase_meta[hit["phrase_candidate_exact"]] = hit

    selected_hit_ids: set[str] = set()
    phrase_plan: list[dict[str, Any]] = []
    for summary_row in read_csv(OCC_SUMMARY):
        phrase = summary_row["phrase_candidate_exact"]
        hits = by_phrase.get(phrase, [])
        candidate_id = summary_row["candidate_id"]
        if not hits:
            phrase_plan.append({
                "candidate_id": candidate_id,
                "phrase_candidate_exact": phrase,
                "exact_occurrences": 0,
                "unique_source_entries": 0,
                "selection_stratum": "no_exact_occurrences",
                "sampling_method": "No exact hit in the numbered-entry inventory; retain for future review only.",
                "sample_entry_limit": 0,
                "prior_batch_01_accepted_occurrences_not_reselected": 0,
                "selected_phrase_hits": 0,
                "selected_unique_entries": 0,
                "seed": SEED,
            })
            continue
        unique_entries = sorted({row["entry_id"] for row in hits}, key=lambda entry: stable_key(candidate_id, entry))
        prior_accepted_hits = [row for row in hits if row["occurrence_id"] in accepted_occurrence_ids]
        eligible_hits = [row for row in hits if row["occurrence_id"] not in accepted_occurrence_ids]
        if len(unique_entries) <= RARE_ENTRY_THRESHOLD:
            method = "exhaustive_all_exact_occurrences_not_already_accepted_in_batch_01"
            chosen = eligible_hits
        else:
            method = f"deterministic_sample_one_occurrence_from_{COMMON_SAMPLE_PER_PHRASE}_distinct_entries"
            already_accepted = {row["entry_id"] for row in prior_accepted_hits}
            eligible_entries = [entry for entry in unique_entries if entry not in already_accepted]
            selected_entries = set(eligible_entries[:COMMON_SAMPLE_PER_PHRASE])
            chosen = []
            for entry_id in selected_entries:
                entry_hits = [row for row in hits if row["entry_id"] == entry_id]
                chosen.append(min(entry_hits, key=lambda row: (int(row["match_start_char_zero_based"]), int(row["match_end_char_exclusive"]), row["occurrence_id"])))
        selected_hit_ids.update(row["occurrence_id"] for row in chosen)
        phrase_plan.append({
            "candidate_id": candidate_id,
            "phrase_candidate_exact": phrase,
            "exact_occurrences": len(hits),
            "unique_source_entries": len({row["entry_id"] for row in hits}),
            "selection_stratum": "rare_phrase_exhaustive" if len({row["entry_id"] for row in hits}) <= RARE_ENTRY_THRESHOLD else "common_phrase_sampled",
            "sampling_method": method,
            "sample_entry_limit": "all" if len({row["entry_id"] for row in hits}) <= RARE_ENTRY_THRESHOLD else COMMON_SAMPLE_PER_PHRASE,
            "prior_batch_01_accepted_occurrences_not_reselected": len(prior_accepted_hits),
            "selected_phrase_hits": len(chosen),
            "selected_unique_entries": len({row["entry_id"] for row in chosen}),
            "seed": SEED,
        })

    selected_cluster_sources: dict[int, set[str]] = defaultdict(set)
    for hit_id in selected_hit_ids:
        cluster = hit_to_cluster[hit_id]
        selected_cluster_sources[id(cluster)].add(hit_id)
    selected_clusters = [cluster for cluster in clusters if id(cluster) in selected_cluster_sources]

    case_rows: list[dict[str, Any]] = []
    link_rows: list[dict[str, Any]] = []
    frame_rows: list[dict[str, Any]] = []
    for index, cluster in enumerate(clusters, start=1):
        case_id = case_id_by_object[id(cluster)]
        hits = sorted(cluster["hits"], key=lambda row: (int(row["match_start_char_zero_based"]), int(row["match_end_char_exclusive"]), row["candidate_id"]))
        entry_text = hits[0]["entry_text_verbatim"]
        start, end = cluster["start"], cluster["end"]
        associated_phrases = sorted({row["phrase_candidate_exact"] for row in hits})
        associated_candidates = sorted({row["candidate_id"] for row in hits})
        accepted_ids = [row["occurrence_id"] for row in hits if row["occurrence_id"] in accepted_occurrence_ids]
        selected_ids = selected_cluster_sources.get(id(cluster), set())
        selection_labels = sorted({
            f"{row['candidate_id']}:{'rare_exhaustive' if next(p for p in phrase_plan if p['candidate_id']==row['candidate_id'])['selection_stratum']=='rare_phrase_exhaustive' else 'common_sample'}"
            for row in hits if row["occurrence_id"] in selected_ids
        })
        base = {
            "review_case_id": case_id,
            "entry_id": cluster["entry_id"],
            "printed_page_num": hits[0]["printed_page_num"],
            "entry_number_verbatim": hits[0]["entry_number_verbatim"],
            "review_span_start_char_zero_based": start,
            "review_span_end_char_exclusive": end,
            "review_span_text_verbatim": entry_text[start:end],
            "source_entry_text_verbatim": entry_text,
            "number_of_overlapping_phrase_hits": len(hits),
            "matched_candidate_ids": ";".join(associated_candidates),
            "matched_phrases_verbatim": " | ".join(associated_phrases),
            "matched_occurrence_ids": ";".join(row["occurrence_id"] for row in hits),
            "batch_02_selected": "yes" if id(cluster) in selected_cluster_sources else "no",
            "batch_02_selection_basis": ";".join(selection_labels),
            "prior_batch_01_accepted_occurrence_ids": ";".join(accepted_ids),
        }
        frame = dict(base)
        frame.update({field: "" for field in HUMAN_FIELDS})
        frame_rows.append(frame)
        if id(cluster) in selected_cluster_sources:
            case = dict(base)
            case.update({field: "" for field in HUMAN_FIELDS})
            case_rows.append(case)

        for hit in hits:
            meta = phrase_meta[hit["phrase_candidate_exact"]]
            link_rows.append({
                "review_case_id": case_id,
                "occurrence_id": hit["occurrence_id"],
                "candidate_id": hit["candidate_id"],
                "phrase_candidate_exact": hit["phrase_candidate_exact"],
                "phrase_hit_start_char_zero_based": hit["match_start_char_zero_based"],
                "phrase_hit_end_char_exclusive": hit["match_end_char_exclusive"],
                "phrase_match_arabic_letter_bounded": hit["arabic_letter_bounded"],
                "phrase_hit_selected_for_batch_02": "yes" if hit["occurrence_id"] in selected_ids else "no",
                "prior_user_decision": "accept" if hit["occurrence_id"] in accepted_occurrence_ids else "",
                "candidate_source": meta["candidate_source"],
            })

    # Assert a lossless mapping between raw phrase hits and review cases.
    if len(link_rows) != len(raw_hits) or {r["occurrence_id"] for r in link_rows} != {r["occurrence_id"] for r in raw_hits}:
        raise SystemExit("Phrase-hit links are not a lossless mapping to the raw occurrence inventory")
    if any(any(row[field] for field in HUMAN_FIELDS) for row in frame_rows + case_rows):
        raise SystemExit("Human annotation fields must remain blank")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    frame_path = OUTPUT / "UNIQUE_OVERLAP_SPAN_REVIEW_FRAME_V0_1.csv"
    links_path = OUTPUT / "PHRASE_HIT_TO_REVIEW_CASE_LINKS_V0_1.csv"
    cases_path = OUTPUT / "BATCH_02_REVIEW_CASES_V0_1.csv"
    plan_path = OUTPUT / "BATCH_02_PHRASE_SAMPLING_PLAN_V0_1.csv"
    write_csv(frame_path, frame_rows, list(frame_rows[0]))
    write_csv(links_path, link_rows, list(link_rows[0]))
    write_csv(cases_path, case_rows, list(case_rows[0]))
    write_csv(plan_path, phrase_plan, list(phrase_plan[0]))

    prior_accepted_cases = sum(bool(row["prior_batch_01_accepted_occurrence_ids"]) for row in case_rows)
    readme = f"""# Evaluative statement occurrence review — batch 02

**Purpose:** reduce duplicated review effort while preserving every raw phrase match. This package organizes source text; it does not classify or label statements.

## How overlap deduplication works

The raw occurrence inventory has {len(raw_hits):,} phrase-hit rows. This package groups hits within the same entry when their character intervals overlap. Each connected interval group becomes one `review_case_id`; the link table retains every original `occurrence_id`, exact phrase, offset, boundary flag, and prior Batch 01 acceptance. Adjacent but non-overlapping intervals remain separate cases.

The grouped span is only the union of overlapping lexical matches. It is **not** asserted to be a complete scholarly statement boundary. The human reviewer should use the full entry text and record corrected span offsets when needed. The case can include substrings and compounds; the link table is the audit trail back to each candidate cue.

## Batch 02 selection

Frequency is measured by distinct source entries per exact phrase. Phrases appearing in at most {RARE_ENTRY_THRESHOLD} distinct entries are included exhaustively, except for exact occurrence IDs already accepted in Batch 01. For each more frequent phrase, the package selects up to {COMMON_SAMPLE_PER_PHRASE} distinct entries using SHA-256 ordering with fixed seed `{SEED}`; at most one occurrence of that phrase is selected per entry. Exact Batch 01 accepted occurrence IDs are excluded from new selections in both strata. When a selected span overlaps other candidate phrases, all its phrase associations remain visible.

This is a reproducible review workload, not a probability sample designed to estimate corpus-wide accuracy. Phrase strata overlap, and the same case may be selected for more than one cue. Do not add per-phrase sample sizes to estimate unique statements.

## Files

- `UNIQUE_OVERLAP_SPAN_REVIEW_FRAME_V0_1.csv`: all deduplicated overlap groups, with full source entries and blank human fields.
- `PHRASE_HIT_TO_REVIEW_CASE_LINKS_V0_1.csv`: lossless mapping of all raw phrase hits to review cases, including every exact span and any previous accepted occurrence.
- `BATCH_02_REVIEW_CASES_V0_1.csv`: the selected cases for review; blank human fields are ready for annotation.
- `BATCH_02_PHRASE_SAMPLING_PLAN_V0_1.csv`: each phrase's frequency, stratum, method, and selected counts.
- `MANIFEST.json` and `MANIFEST.sha256`: input/output checksums and counts.

## Human fields

Record whether the cue is a complete statement, a component of a larger statement, an unrelated substring, or unresolved; then identify the statement role and exact full statement span in the source entry. Record the referent, attribution, qualification, confidence, and notes only when supported by the text. Leave a field blank rather than infer it. No rank, historical truth, source independence, narrator reliability, or numeric score is assigned here.

The AI proposals accepted in Batch 01 remain limited to their 33 selected occurrences. They are shown as prior decisions in the link table and do not transfer to other occurrences of those phrases.
"""
    readme_path = OUTPUT / "README.md"
    readme_path.write_text(readme, encoding="utf-8", newline="\n")

    timestamp = datetime.now(timezone.utc).isoformat()
    inputs = [OCC_FILE, OCC_SUMMARY, OCC_MANIFEST, DECISIONS, DECISION_MANIFEST, Path(__file__).resolve()]
    outputs = [frame_path, links_path, cases_path, plan_path, readme_path]
    counts = {
        "raw_phrase_hits": len(raw_hits),
        "deduplicated_overlap_span_cases": len(frame_rows),
        "batch_02_selected_review_cases": len(case_rows),
        "candidate_phrase_strings": len(phrase_plan),
        "rare_phrase_strings_selected_exhaustively": sum(row["selection_stratum"] == "rare_phrase_exhaustive" for row in phrase_plan),
        "common_phrase_strings_sampled": sum(row["selection_stratum"] == "common_phrase_sampled" for row in phrase_plan),
        "phrase_strings_with_no_exact_hits": sum(row["selection_stratum"] == "no_exact_occurrences" for row in phrase_plan),
        "batch_02_cases_containing_prior_batch_01_acceptance": prior_accepted_cases,
        "human_annotation_fields_filled": 0,
        "rank_assignments": 0,
        "numeric_scores_assigned": 0,
    }
    manifest = {
        "package_id": OUTPUT.name,
        "generated_at_utc": timestamp,
        "status": "deduplicated lexical review frame and deterministic phrase-stratified sample; no statement classifications assigned",
        "method": {
            "deduplication": "Within an entry, match intervals connected by strict overlap are grouped into one review case; each raw hit remains in a separate lossless link table.",
            "rare_phrase_threshold_distinct_entries": RARE_ENTRY_THRESHOLD,
            "common_phrase_sample_distinct_entries_per_phrase": COMMON_SAMPLE_PER_PHRASE,
            "sample_seed": SEED,
            "common_phrase_selection": "Sort eligible entry IDs by SHA-256(seed|candidate_id|entry_id); choose first 10 and one earliest occurrence per chosen entry.",
            "batch_01_decisions": "Exact accepted occurrence IDs are excluded from new sample selections in both strata and marked in the link table. Rare phrase strata exhaustively include all remaining, not-yet-accepted exact occurrences.",
        },
        "counts": counts,
        "inputs": {path.relative_to(ROOT).as_posix(): sha256(path) for path in inputs},
        "outputs": {path.name: sha256(path) for path in outputs},
        "manifest_hash_policy": "MANIFEST.sha256 records this manifest hash separately; it is not recursively embedded.",
    }
    manifest_path = OUTPUT / "MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    (OUTPUT / "MANIFEST.sha256").write_text(f"{sha256(manifest_path)}  MANIFEST.json\n", encoding="ascii", newline="\n")
    print(json.dumps({"output": str(OUTPUT), **counts}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
