#!/usr/bin/env python3
"""Run a read-only, exact-string shadow scan over local Taqrib entries.

Every hit is a cue occurrence only. The program does not assign ranks, accept
labels, normalize Arabic, or infer statement boundaries or required context.
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import re
import shutil
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BOOK_DIR = (
    ROOT
    / "data"
    / "1_raw"
    / "Shamela4_Full_DB"
    / "26__التراجم-والطبقات"
    / "3076__تقريب-التهذيب"
)
PAGES_PATH = BOOK_DIR / "pages.jsonl"
SOURCE_MANIFEST_PATH = BOOK_DIR / "manifest.json"
RANK_INVENTORY_PATH = ROOT / "data" / "2_interim" / "rijal_fyp_modelling_pipeline" / "IBN_HAJAR_12_RANK_SOURCE_INVENTORY_V0.md"
RULE_REGISTRY_PATH = ROOT / "dataset_discovery" / "target_feasibility" / "ANNOTATION_AUTOMATION_RULE_REGISTRY_V1.csv"
FREEZE_DIR = (
    ROOT
    / "data"
    / "2_interim"
    / "rijal_fyp_modelling_pipeline"
    / "boundary_pilot_v1"
    / "frozen_2026-11-15"
)
FROZEN_ANNOTATIONS_PATH = FREEZE_DIR / "TAQRIB_BOUNDARY_ANNOTATIONS_FROZEN_V1.csv"
FREEZE_MANIFEST_PATH = FREEZE_DIR / "FREEZE_MANIFEST.json"
OUTPUT_DIR = ROOT / "data" / "2_interim" / "rijal_fyp_modelling_pipeline" / "rank_label_shadow_run_v1_2026-11-15"

EXPECTED_PAGES_SHA256 = "45c2f611cee35f7394da23f58ded71280fbf18d99be163347d1ad38b8fc824fa"
EXPECTED_FROZEN_ANNOTATIONS_SHA256 = "c7d808496802ba6ba04aac2bc2778f4acf0a04f5996e7866458b92e46d59a05f"
EXPECTED_FROZEN_MANIFEST_SHA256 = "f12e8aa07920915149daec9b62b11cffe58767ea61daf39f4eb22e4437f866d3"
BOOK_ID = 3076
SHAMELA_BOOK_ID = 8609
ENTRY_PREFIX = re.compile(r"^\s*([0-9٠-٩۰-۹]+)\s*[-–]")
ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")

# Exact short examples and cues copied into the repository's v0 source inventory.
# These are not a complete vocabulary and are not rules for automatic rank labels.
RANK_CUES = (
    (1, "الصحابة", "status anchor; distinguish from ordinary reliability grades", "status"),
    (2, "أوثق الناس", "source example; full construction required", "assessment"),
    (2, "ثقة ثقة", "source example; repetition and full construction required", "assessment"),
    (2, "ثقة حافظ", "source example; compound praise; do not use as standalone rank 3", "assessment"),
    (3, "ثقة", "single-attribute example; complete-span and context check required", "assessment"),
    (3, "متقن", "single-attribute example; complete-span and context check required", "assessment"),
    (3, "ثبت", "single-attribute example; complete-span and context check required", "assessment"),
    (3, "عدل", "single-attribute example; complete-span and context check required", "assessment"),
    (4, "صدوق", "source example; qualified or compound forms need full context", "assessment"),
    (4, "لا بأس به", "source example; complete construction required", "assessment"),
    (4, "ليس به بأس", "source example; complete construction required", "assessment"),
    (5, "صدوق سيء الحفظ", "source example; preserve full qualification", "assessment"),
    (5, "صدوق يهم", "source example; preserve full qualification", "assessment"),
    (5, "له أوهام", "source cue; requires complete statement and context", "assessment"),
    (5, "يخطئ", "source spelling; do not normalize corpus spellings", "assessment"),
    (5, "تغير بأخرة", "source-edition example; preserve edition spelling", "assessment"),
    (5, "التشيع", "source cue; innovation type/advocacy context required", "contextual_assessment"),
    (5, "القدر", "source cue; innovation type/advocacy context required", "contextual_assessment"),
    (5, "النصب", "source cue; innovation type/advocacy context required", "contextual_assessment"),
    (5, "الإرجاء", "source cue; innovation type/advocacy context required", "contextual_assessment"),
    (5, "التجهم", "source cue; innovation type/advocacy context required", "contextual_assessment"),
    (6, "مقبول", "conditional example; corroboration and other conditions required", "contextual_assessment"),
    (6, "فلين الحديث", "definition wording; complete construction/context required", "contextual_assessment"),
    (7, "مستور", "source example; transmitter count and authentication evidence required", "contextual_assessment"),
    (7, "مجهول الحال", "source example; transmitter count and authentication evidence required", "contextual_assessment"),
    (8, "ضعيف", "source example; authentication/weakness evidence required", "contextual_assessment"),
    (9, "مجهول", "source example; one-transmitter and authentication evidence required", "contextual_assessment"),
    (10, "متروك", "source example; complete construction/defect evidence required", "contextual_assessment"),
    (10, "متروك الحديث", "source example; complete construction/defect evidence required", "contextual_assessment"),
    (10, "واهي الحديث", "source example; complete construction/defect evidence required", "contextual_assessment"),
    (10, "ساقط", "source example; complete construction/defect evidence required", "contextual_assessment"),
    (11, "اتهم بالكذب", "accusation example; distinguish from applied label", "contextual_assessment"),
    (12, "أطلق عليه اسم الكذب والوضع", "applied-label example; distinguish from accusation", "contextual_assessment"),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def is_arabic_letter(char: str) -> bool:
    return bool(char) and unicodedata.category(char).startswith("L") and "ARABIC" in unicodedata.name(char, "")


def find_occurrences(text: str, needle: str):
    start = 0
    while True:
        index = text.find(needle, start)
        if index < 0:
            break
        yield index, index + len(needle)
        start = index + 1


def load_entries() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    actual_hash = sha256(PAGES_PATH)
    if actual_hash != EXPECTED_PAGES_SHA256:
        raise RuntimeError(f"Unexpected pages.jsonl SHA-256: {actual_hash}")
    source_manifest = json.loads(SOURCE_MANIFEST_PATH.read_text(encoding="utf-8"))
    recorded = next(
        (item.get("sha256") for item in source_manifest.get("files", []) if item.get("path") == "pages.jsonl"),
        None,
    )
    if recorded != EXPECTED_PAGES_SHA256:
        raise RuntimeError("Source manifest does not record the expected pages.jsonl hash")

    entries: list[dict[str, Any]] = []
    locator_counts: Counter[tuple[int, int]] = Counter()
    skipped_nonempty_chunks = 0
    numbered_page_count: set[int] = set()
    with PAGES_PATH.open(encoding="utf-8", newline="") as handle:
        for line in handle:
            page = json.loads(line)
            for chunk_index, chunk in enumerate(page.get("body", "").split("\r"), start=1):
                match = ENTRY_PREFIX.match(chunk)
                if not match:
                    if chunk.strip():
                        skipped_nonempty_chunks += 1
                    continue
                entry_number_verbatim = match.group(1)
                entry_number = int(entry_number_verbatim.translate(ARABIC_DIGITS))
                locator = (int(page["page_num"]), entry_number)
                locator_counts[locator] += 1
                numbered_page_count.add(int(page["page_num"]))
                entry_id = (
                    f"S{BOOK_ID}-P{int(page['page_num']):03d}-"
                    f"C{chunk_index:03d}-E{entry_number:04d}"
                )
                entries.append(
                    {
                        "entry_id": entry_id,
                        "local_book_id": BOOK_ID,
                        "shamela_book_id": SHAMELA_BOOK_ID,
                        "local_page_id": page["page_id"],
                        "shamela_page_id": page["shamela_page_id"],
                        "printed_page_num": page["page_num"],
                        "entry_number_numeric": entry_number,
                        "entry_number_verbatim": entry_number_verbatim,
                        "source_chunk_index": chunk_index,
                        "duplicate_printed_entry_number_on_page": "",
                        "entry_text_verbatim": chunk,
                    }
                )
    for entry in entries:
        locator = (int(entry["printed_page_num"]), int(entry["entry_number_numeric"]))
        entry["duplicate_printed_entry_number_on_page"] = "yes" if locator_counts[locator] > 1 else "no"
    entries.sort(key=lambda row: (int(row["printed_page_num"]), row["source_chunk_index"]))
    stats = {
        "source_page_rows": source_manifest.get("page_count"),
        "numbered_entries": len(entries),
        "pages_containing_numbered_entries": len(numbered_page_count),
        "duplicate_page_entry_number_keys": sum(1 for count in locator_counts.values() if count > 1),
        "extra_rows_with_duplicate_page_entry_number": sum(count - 1 for count in locator_counts.values() if count > 1),
        "nonempty_unnumbered_chunks_excluded": skipped_nonempty_chunks,
    }
    return entries, stats


def cue_inventory_rows() -> list[dict[str, Any]]:
    rows = []
    for rank, text, note, family in RANK_CUES:
        rows.append(
            {
                "cue_id": f"R{rank:02d}-C{sum(1 for x in rows if x['source_rank_anchor'] == rank) + 1:02d}",
                "source_rank_anchor": rank,
                "cue_text_exact": text,
                "cue_family": family,
                "source_note": note,
                "source": "repository v0 inventory; introductory examples/cues, not exhaustive",
            }
        )
    return rows


def cue_occurrences(entries: list[dict[str, Any]], cues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    by_entry: dict[str, list[dict[str, Any]]] = defaultdict(list)
    counter = 0
    for entry in entries:
        text = entry["entry_text_verbatim"]
        for cue in cues:
            cue_text = cue["cue_text_exact"]
            for start, end in find_occurrences(text, cue_text):
                counter += 1
                occurrence = {
                    "occurrence_id": f"CUE-{counter:07d}",
                    **{key: entry[key] for key in (
                        "entry_id", "local_book_id", "shamela_book_id", "local_page_id",
                        "shamela_page_id", "printed_page_num", "entry_number_verbatim",
                        "source_chunk_index", "duplicate_printed_entry_number_on_page",
                    )},
                    "cue_id": cue["cue_id"],
                    "source_rank_anchor": cue["source_rank_anchor"],
                    "cue_text_exact": cue_text,
                    "cue_family": cue["cue_family"],
                    "match_start_char": start,
                    "match_end_char": end,
                    "context_before": text[max(0, start - 45) : start],
                    "matched_text": text[start:end],
                    "context_after": text[end : end + 45],
                    "left_adjacent_arabic_letter": is_arabic_letter(text[start - 1]) if start else False,
                    "right_adjacent_arabic_letter": is_arabic_letter(text[end]) if end < len(text) else False,
                    "shadow_status": "cue_occurrence_only_unreviewed",
                    "rank_assignment": "",
                    "human_disposition": "",
                    "abstention_reason": "Entry-level phrase search does not establish a complete assessment span or rank-definition preconditions.",
                }
                rows.append(occurrence)
                by_entry[entry["entry_id"]].append(occurrence)

    for occurrences in by_entry.values():
        for occurrence in occurrences:
            overlapping = [
                other["cue_id"]
                for other in occurrences
                if other["occurrence_id"] != occurrence["occurrence_id"]
                and max(occurrence["match_start_char"], other["match_start_char"])
                < min(occurrence["match_end_char"], other["match_end_char"])
            ]
            occurrence["overlapping_cue_ids"] = ";".join(sorted(set(overlapping)))
    return rows


def load_registry_rules() -> tuple[list[dict[str, str]], list[str]]:
    with RULE_REGISTRY_PATH.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        all_rows = list(reader)
        headers = list(reader.fieldnames or [])
    eligible = [
        row
        for row in all_rows
        if row.get("rule_status") == "candidate_not_enabled"
        and row.get("rule_family") in {"taxonomy_rank", "generation_status"}
    ]
    return eligible, headers


def registry_hits(entries: list[dict[str, Any]], rules: list[dict[str, str]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    hits: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    hit_counter = 0
    for rule in rules:
        phrase = rule.get("exact_complete_span", "")
        if not phrase:
            continue
        try:
            proposed = json.loads(rule.get("proposed_fields_json", "{}") or "{}")
        except json.JSONDecodeError:
            proposed = {}
        rank = proposed.get("taqrib_rank_number")
        count = 0
        unique_entries: set[str] = set()
        for entry in entries:
            text = entry["entry_text_verbatim"]
            for start, end in find_occurrences(text, phrase):
                hit_counter += 1
                count += 1
                unique_entries.add(entry["entry_id"])
                hits.append(
                    {
                        "rule_hit_id": f"RULE-{hit_counter:07d}",
                        "rule_id": rule["rule_id"],
                        "rule_version": rule["rule_version"],
                        "rule_status": rule["rule_status"],
                        "rule_family": rule["rule_family"],
                        "rule_exact_string": phrase,
                        "candidate_rank_from_registry": rank if rank is not None else "",
                        "candidate_statement_type_from_registry": proposed.get("statement_type", ""),
                        **{key: entry[key] for key in (
                            "entry_id", "local_book_id", "shamela_book_id", "local_page_id",
                            "shamela_page_id", "printed_page_num", "entry_number_verbatim",
                            "source_chunk_index", "duplicate_printed_entry_number_on_page",
                        )},
                        "match_start_char": start,
                        "match_end_char": end,
                        "context_before": text[max(0, start - 45) : start],
                        "matched_text": text[start:end],
                        "context_after": text[end : end + 45],
                        "statement_boundary_confirmed": "no",
                        "auto_accept": "false",
                        "proposal_status": "shadow_candidate_only_unreviewed",
                        "assigned_rank": "",
                        "human_disposition": "",
                        "abstention_reason": "Exact string occurs in an entry, but the complete statement span, identity, and rule preconditions are unconfirmed.",
                    }
                )
        summaries.append(
            {
                "rule_id": rule["rule_id"],
                "rule_version": rule["rule_version"],
                "rule_status": rule["rule_status"],
                "rule_family": rule["rule_family"],
                "exact_rule_string": phrase,
                "candidate_rank_from_registry": rank if rank is not None else "",
                "candidate_statement_type_from_registry": proposed.get("statement_type", ""),
                "entry_level_occurrence_count": count,
                "unique_entry_count": len(unique_entries),
                "auto_accept": "false",
                "applied_labels": 0,
            }
        )
    return hits, summaries


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    if fields is None:
        fields = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def sha_map(paths: list[Path]) -> dict[str, str]:
    return {path.name: sha256(path) for path in paths}


def main() -> None:
    required = [
        PAGES_PATH,
        SOURCE_MANIFEST_PATH,
        RANK_INVENTORY_PATH,
        RULE_REGISTRY_PATH,
        FROZEN_ANNOTATIONS_PATH,
        FREEZE_MANIFEST_PATH,
    ]
    for path in required:
        if not path.is_file():
            raise FileNotFoundError(path)
    if OUTPUT_DIR.exists():
        raise FileExistsError(f"Refusing to overwrite shadow-run directory: {OUTPUT_DIR}")
    if sha256(FROZEN_ANNOTATIONS_PATH) != EXPECTED_FROZEN_ANNOTATIONS_SHA256:
        raise RuntimeError("Frozen annotation file hash differs from expected")
    if EXPECTED_FROZEN_MANIFEST_SHA256 and sha256(FREEZE_MANIFEST_PATH) != EXPECTED_FROZEN_MANIFEST_SHA256:
        raise RuntimeError("Frozen annotation manifest hash differs from expected")

    entries, entry_stats = load_entries()
    cues = cue_inventory_rows()
    cue_hits = cue_occurrences(entries, cues)
    rules, registry_headers = load_registry_rules()
    rule_hits, rule_summaries = registry_hits(entries, rules)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=False)
    write_csv(OUTPUT_DIR / "ENTRY_INDEX.csv", entries)
    write_csv(OUTPUT_DIR / "RANK_CUE_INVENTORY.csv", cues)
    write_csv(OUTPUT_DIR / "CUE_OCCURRENCES.csv", cue_hits)
    write_csv(OUTPUT_DIR / "CANDIDATE_RULE_HITS.csv", rule_hits)
    write_csv(OUTPUT_DIR / "CANDIDATE_RULE_COUNTS.csv", rule_summaries)
    shutil.copyfile(RULE_REGISTRY_PATH, OUTPUT_DIR / "RULE_REGISTRY_SNAPSHOT.csv")

    counts_by_rank = Counter(int(row["source_rank_anchor"]) for row in cue_hits)
    unique_entries_by_rank: dict[int, set[str]] = defaultdict(set)
    for row in cue_hits:
        unique_entries_by_rank[int(row["source_rank_anchor"])].add(row["entry_id"])
    cue_count_rows = [
        {
            "source_rank_anchor": rank,
            "defined_cue_count": sum(1 for cue in cues if int(cue["source_rank_anchor"]) == rank),
            "exact_string_occurrence_count": counts_by_rank.get(rank, 0),
            "unique_entry_count_with_one_or_more_cues": len(unique_entries_by_rank.get(rank, set())),
            "interpretation": "Observed exact source-cue occurrences only; not rank-label or coverage counts.",
        }
        for rank in range(1, 13)
    ]
    write_csv(OUTPUT_DIR / "CUE_COUNTS_BY_RANK.csv", cue_count_rows)

    output_files = [
        OUTPUT_DIR / name
        for name in (
            "ENTRY_INDEX.csv",
            "RANK_CUE_INVENTORY.csv",
            "CUE_OCCURRENCES.csv",
            "CANDIDATE_RULE_HITS.csv",
            "CANDIDATE_RULE_COUNTS.csv",
            "RULE_REGISTRY_SNAPSHOT.csv",
            "CUE_COUNTS_BY_RANK.csv",
        )
    ]
    manifest = {
        "run": "Taqrib rank-cue shadow scan v1",
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "status": "shadow only; no labels auto-assigned or accepted",
        "source": {
            "local_book_id": BOOK_ID,
            "shamela_book_id": SHAMELA_BOOK_ID,
            "source_file": PAGES_PATH.relative_to(ROOT).as_posix(),
            "page_count_in_source_manifest": entry_stats["source_page_rows"],
            "entry_extraction": "split each source body on the recorded carriage-return delimiter; keep chunks beginning with printed Arabic/Western numeral plus hyphen",
            **entry_stats,
        },
        "inputs": {
            PAGES_PATH.name: {"path": PAGES_PATH.relative_to(ROOT).as_posix(), "sha256": sha256(PAGES_PATH)},
            SOURCE_MANIFEST_PATH.name: {"path": SOURCE_MANIFEST_PATH.relative_to(ROOT).as_posix(), "sha256": sha256(SOURCE_MANIFEST_PATH)},
            RANK_INVENTORY_PATH.name: {"path": RANK_INVENTORY_PATH.relative_to(ROOT).as_posix(), "sha256": sha256(RANK_INVENTORY_PATH)},
            RULE_REGISTRY_PATH.name: {"path": RULE_REGISTRY_PATH.relative_to(ROOT).as_posix(), "sha256": sha256(RULE_REGISTRY_PATH)},
            FROZEN_ANNOTATIONS_PATH.name: {"path": FROZEN_ANNOTATIONS_PATH.relative_to(ROOT).as_posix(), "sha256": sha256(FROZEN_ANNOTATIONS_PATH)},
            FREEZE_MANIFEST_PATH.name: {"path": FREEZE_MANIFEST_PATH.relative_to(ROOT).as_posix(), "sha256": sha256(FREEZE_MANIFEST_PATH)},
        },
        "matching": {
            "normalization": "none; exact Unicode substring matching only",
            "entry_text_mutated": False,
            "entry_statement_boundaries_inferred": False,
            "rank_assignment": False,
            "auto_accept": False,
            "source_rank_cues_are_exhaustive": False,
            "contextual_rank_preconditions_checked": False,
            "human_dispositions_recorded": False,
        },
        "counts": {
            **entry_stats,
            "source_cue_definitions": len(cues),
            "source_cue_occurrences": len(cue_hits),
            "source_cue_occurrence_entries": len({row["entry_id"] for row in cue_hits}),
            "registry_candidate_rules_scanned": len(rules),
            "registry_rule_occurrences": len(rule_hits),
            "registry_rule_hit_entries": len({row["entry_id"] for row in rule_hits}),
            "rank_assignments": 0,
            "auto_accepted_labels": 0,
        },
        "outputs": {path.name: sha256(path) for path in output_files},
        "limitations": [
            "The source inventory's examples are illustrative, not an exhaustive phrase dictionary.",
            "The local page extraction begins at printed page 75 and omits the rank-introduction passage; the source inventory is a separate edition-aligned searchable digital-text reference, not a scan.",
            "Occurrences are located in whole entry text, not confirmed complete assessment spans.",
            "A cue hit does not satisfy rank-definition conditions or establish identity, statement type, attribution, truth, or target eligibility.",
            "Raw occurrence and unique-entry counts are not label counts, precision, recall, automation coverage, or model performance.",
        ],
    }
    manifest_path = OUTPUT_DIR / "RUN_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    (OUTPUT_DIR / "RUN_MANIFEST.sha256").write_text(
        f"{sha256(manifest_path)}  {manifest_path.name}\n",
        encoding="ascii",
        newline="\n",
    )

    report = [
        "# Taqrīb Rank-Cue Shadow Run v1",
        "",
        "**Status:** shadow scan complete; no rank labels were assigned or accepted.",
        "",
        "## What was scanned",
        "",
        f"- Local source pages: {entry_stats['source_page_rows']}",
        f"- Numbered entry strings extracted: {entry_stats['numbered_entries']}",
        f"- Duplicate printed page/entry-number keys: {entry_stats['duplicate_page_entry_number_keys']} "
        f"({entry_stats['extra_rows_with_duplicate_page_entry_number']} extra numbered rows; IDs also use source-chunk position)",
        f"- Nonempty unnumbered chunks excluded from the entry scan: {entry_stats['nonempty_unnumbered_chunks_excluded']}",
        f"- Source-defined cue examples searched: {len(cues)} across the twelve ranks",
        f"- Exact source-cue occurrences: {len(cue_hits)} across {len({row['entry_id'] for row in cue_hits})} entries",
        f"- Existing candidate registry rules scanned: {len(rules)}",
        f"- Candidate-registry phrase occurrences: {len(rule_hits)} across {len({row['entry_id'] for row in rule_hits})} entries",
        "",
        "## How to read the results",
        "",
        "The scanner searched exact strings without spelling, punctuation, diacritic, or orthographic normalization. It retained local page IDs, Shamela page IDs, printed page numbers, entry numbers, character offsets, and surrounding source text. It also records overlapping cue matches so that a shorter cue inside a compound is not silently treated as a standalone phrase.",
        "",
        "Every row in `CUE_OCCURRENCES.csv` and `CANDIDATE_RULE_HITS.csv` is an unreviewed lexical occurrence. `rank_assignment` / `assigned_rank` stays blank, and `auto_accept` is false. A full entry occurrence does not prove that the matched phrase is a complete assessment statement. Context-dependent ranks need the extra evidence stated in the source definition.",
        "",
        "## Source-cue occurrences by rank anchor",
        "",
        "| Rank anchor | Cue strings | Exact occurrences | Entries with at least one hit |",
        "| ---: | ---: | ---: | ---: |",
        *[
            f"| {row['source_rank_anchor']} | {row['defined_cue_count']} | {row['exact_string_occurrence_count']} | {row['unique_entry_count_with_one_or_more_cues']} |"
            for row in cue_count_rows
        ],
        "",
        "These are lexical occurrence counts. They are not counts of assigned labels or rank coverage.",
        "",
        "## Existing candidate-rule occurrence counts",
        "",
        "| Rule | Exact occurrences | Entries | Rule state |",
        "| --- | ---: | ---: | --- |",
        *[
            f"| `{row['rule_id']}` | {row['entry_level_occurrence_count']} | {row['unique_entry_count']} | `{row['rule_status']}` |"
            for row in rule_summaries
        ],
        "",
        "Every candidate-rule occurrence remains unreviewed; the registry rules remain disabled and no labels were applied.",
        "",
        "## Files",
        "",
        "- `ENTRY_INDEX.csv`: numbered local source entries, copied verbatim.",
        "- `RANK_CUE_INVENTORY.csv`: source-defined examples and cue notes used for the scan.",
        "- `CUE_OCCURRENCES.csv`: every exact cue occurrence and overlap/context indicators.",
        "- `CUE_COUNTS_BY_RANK.csv`: occurrence and unique-entry counts, not label counts.",
        "- `CANDIDATE_RULE_HITS.csv`: exact occurrences of existing, still-disabled candidate registry rules.",
        "- `CANDIDATE_RULE_COUNTS.csv`: per-rule occurrence counts, including zero-hit rules.",
        "- `RULE_REGISTRY_SNAPSHOT.csv`: registry input copied for this run.",
        "- `RUN_MANIFEST.json` and its checksum: input/output hashes, counts, and scope limits.",
        "",
        "No data source, frozen annotation, rule registry, or rank label was modified. This run is an inventory aid for human review, not an evaluation of the rules or evidence that a model can be trained.",
    ]
    report_path = OUTPUT_DIR / "RUN_REPORT.md"
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8", newline="\n")
    manifest["outputs"][report_path.name] = sha256(report_path)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    (OUTPUT_DIR / "RUN_MANIFEST.sha256").write_text(
        f"{sha256(manifest_path)}  {manifest_path.name}\n",
        encoding="ascii",
        newline="\n",
    )
    print(f"Shadow run created: {OUTPUT_DIR}")
    print(f"Entries: {entry_stats['numbered_entries']}; cue hits: {len(cue_hits)}; registry hits: {len(rule_hits)}")
    print("Assigned ranks: 0; auto-accepted labels: 0")


if __name__ == "__main__":
    main()
