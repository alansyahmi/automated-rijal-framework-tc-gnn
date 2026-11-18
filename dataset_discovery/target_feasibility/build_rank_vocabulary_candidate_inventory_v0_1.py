#!/usr/bin/env python3
"""Build a non-labeling, source-anchored Taqrib phrase vocabulary inventory v0.1."""
from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PIPELINE = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline"
OUTPUT = PIPELINE / "rank_vocabulary_candidate_inventory_v0_1_2026-11-16"
ENTRY_INDEX = PIPELINE / "rank_label_shadow_run_v1_2026-11-15/ENTRY_INDEX.csv"
V02_DIR = PIPELINE / "rank_label_candidate_inventory_v0_2_2026-11-15"
AI_DIR = PIPELINE / "rank_label_no_hit_ai_review_v1_2026-11-15/CONSOLIDATED_V1_3"
PHRASE_REVIEW_DIR = PIPELINE / "rank_label_phrase_review_v1_1_2026-11-16"
SOURCE_INVENTORY = PIPELINE / "IBN_HAJAR_12_RANK_SOURCE_INVENTORY_V0.md"
ANCHOR_VERIFICATION = OUTPUT / "SOURCE_ANCHOR_VERIFICATION.md"
ARABIC_LETTER = re.compile(r"[\u0621-\u064a\u066e-\u06d3\u06fa-\u06fc]")

RANK_NOTES = {
    1: "Companion status; keep separate from ordinary reliability grades.",
    2: "Superlative, repetition, or praise combined in meaning; the complete construction matters.",
    3: "A single commendatory attribute; distinguish from compounds, negation, quotation, and attribution.",
    4: "A description below rank 3; preserve complete wording and qualification.",
    5: "Preserve memory/error qualification. Innovation cues require type and advocacy context.",
    6: "مقبول requires corroboration; otherwise the definition indicates لين الحديث. Other definition conditions apply.",
    7: "Requires more than one transmitter and lack of authentication.",
    8: "Requires lack of recognized authentication and an expressed weakness.",
    9: "Requires only one known transmitter and lack of authentication.",
    10: "Requires lack of authentication plus a defect grounding weakness.",
    11: "Accusation of lying; distinguish from an applied label.",
    12: "Applied lying/fabrication label; distinguish from accusation.",
}

# These exact cues are copied from the repository's source inventory v0.
# Innovation terms are context cues inside Rank 5's definition, not standalone mappings.
ANCHORS = [
    (1, "الصحابة", "status_category", "Explicit category name; status, not ordinary reliability."),
    (2, "أوثق الناس", "source_example", "Superlative construction; full span required."),
    (2, "ثقة ثقة", "source_example", "Literal repetition of the praise."),
    (2, "ثقة حافظ", "source_example", "Combined praise; do not treat ثقة alone inside it as Rank 3."),
    (3, "ثقة", "source_example", "Single commendatory attribute when standalone."),
    (3, "متقن", "source_example", "Single commendatory attribute when standalone."),
    (3, "ثبت", "source_example", "Single commendatory attribute when standalone."),
    (3, "عدل", "source_example", "Single commendatory attribute when standalone."),
    (4, "صدوق", "source_example", "Complete phrase and qualifications matter."),
    (4, "لا بأس به", "source_example", "Complete phrase and qualifications matter."),
    (4, "ليس به بأس", "source_example", "Complete phrase and qualifications matter."),
    (5, "صدوق سيء الحفظ", "source_example", "Preserve the entire memory qualification."),
    (5, "صدوق يهم", "source_example", "Preserve the entire error qualification."),
    (5, "له أوهام", "source_example", "Preserve span and context."),
    (5, "يخطئ", "source_example", "Preserve span and context."),
    (5, "تغير بأخرة", "source_example_1406_text", "Preserve source spelling; Alifta comparator reads تغير بآخره."),
    (5, "التشيع", "innovation_context_cue", "Not a standalone Rank 5 label; type/advocacy context required."),
    (5, "القدر", "innovation_context_cue", "Not a standalone Rank 5 label; type/advocacy context required."),
    (5, "النصب", "innovation_context_cue", "Not a standalone Rank 5 label; type/advocacy context required."),
    (5, "الإرجاء", "innovation_context_cue", "Not a standalone Rank 5 label; type/advocacy context required."),
    (5, "التجهم", "innovation_context_cue", "Not a standalone Rank 5 label; type/advocacy context required."),
    (6, "مقبول", "definition_cue", "Conditional on corroboration; do not map by word alone."),
    (6, "فلين الحديث", "definition_cue", "Definition's contrast where corroboration is absent."),
    (7, "مستور", "source_example", "Definition requires transmitter-count and no-authentication evidence."),
    (7, "مجهول الحال", "source_example", "Definition requires transmitter-count and no-authentication evidence."),
    (8, "ضعيف", "source_example", "Definition also requires absence of recognized authentication."),
    (9, "مجهول", "source_example", "Definition requires one known transmitter and no authentication."),
    (10, "متروك", "source_example", "Definition requires no authentication plus a defect."),
    (10, "متروك الحديث", "source_example", "Definition requires no authentication plus a defect."),
    (10, "واهي الحديث", "source_example", "Definition requires no authentication plus a defect."),
    (10, "ساقط", "source_example", "Definition requires no authentication plus a defect."),
    (11, "اتهم بالكذب", "definition_cue", "Within من اتهم بالكذب; an accusation, not an applied label."),
    (12, "أطلق عليه اسم الكذب والوضع", "definition_cue", "Applied label; distinguish from the Rank 11 accusation."),
]

# Literal search strings for broad discovery only. These are not morphological roots
# and their hits are never rank assignments.
SEARCH_CUES = [
    ("الصحابة", "1"), ("أوثق", "2"), ("ثقة", "2;3"), ("متقن", "3"),
    ("ثبت", "3"), ("عدل", "3"), ("صدوق", "4;5"), ("بأس", "4"),
    ("أوهام", "5"), ("يهم", "5"), ("يخطئ", "5"), ("تغير", "5"),
    ("التشيع", "5"), ("القدر", "5"), ("النصب", "5"), ("الإرجاء", "5"),
    ("التجهم", "5"), ("مقبول", "6"), ("لين", "6"), ("مستور", "7"),
    ("مجهول", "7;9"), ("ضعيف", "8"), ("متروك", "10"), ("واهي", "10"),
    ("ساقط", "10"), ("اتهم بالكذب", "11"), ("كذب", "11;12"), ("وضع", "12"),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\r\n")
        w.writeheader()
        w.writerows(rows)


def arabic_letter_at(text: str, pos: int) -> bool:
    return 0 <= pos < len(text) and bool(ARABIC_LETTER.fullmatch(text[pos]))


def matches(text: str, phrase: str) -> list[tuple[int, int, bool]]:
    found: list[tuple[int, int, bool]] = []
    pos = 0
    while phrase and (start := text.find(phrase, pos)) >= 0:
        end = start + len(phrase)
        bounded = not arabic_letter_at(text, start - 1) and not arabic_letter_at(text, end)
        found.append((start, end, bounded))
        pos = start + 1
    return found


def verify_package(directory: Path, manifest_name: str, checksum_name: str) -> dict[str, Any]:
    manifest_path = directory / manifest_name
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    checksum_path = directory / checksum_name
    if checksum_path.is_file():
        expected = checksum_path.read_text(encoding="ascii").split()[0]
        actual = sha256(manifest_path)
        if actual != expected:
            raise SystemExit(f"Manifest sidecar mismatch: {manifest_path}")
    for name, expected in manifest.get("outputs", {}).items():
        path = directory / name
        if not path.is_file() or sha256(path) != expected:
            raise SystemExit(f"Input package output mismatch: {path}")
    return manifest


def main() -> None:
    if OUTPUT.exists() and any((OUTPUT / name).exists() for name in (
        "SOURCE_RANK_ANCHORS_V0_1.csv", "CANDIDATE_VOCABULARY_V0_1.csv",
        "SOURCE_CUE_SCAN_V0_1.csv", "CANDIDATE_EXAMPLE_HITS_V0_1.csv",
        "MANIFEST.json", "README.md",
    )):
        raise SystemExit(f"Refusing to overwrite existing generated package: {OUTPUT}")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    if not ANCHOR_VERIFICATION.is_file():
        raise SystemExit(f"Required source verification note not found: {ANCHOR_VERIFICATION}")

    v02_manifest = verify_package(V02_DIR, "MANIFEST.json", "MANIFEST.sha256")
    ai_manifest = verify_package(AI_DIR, "REVIEW_RESULTS_MANIFEST.json", "REVIEW_RESULTS_MANIFEST.sha256")
    review_manifest = verify_package(PHRASE_REVIEW_DIR, "MANIFEST.json", "MANIFEST.sha256")
    shadow_dir = PIPELINE / "rank_label_shadow_run_v1_2026-11-15"
    shadow_manifest = verify_package(shadow_dir, "RUN_MANIFEST.json", "RUN_MANIFEST.sha256")
    if sha256(ENTRY_INDEX) != shadow_manifest["outputs"]["ENTRY_INDEX.csv"]:
        raise SystemExit("ENTRY_INDEX hash differs from the shadow-run manifest")

    source_text = SOURCE_INVENTORY.read_text(encoding="utf-8")
    source_hash = sha256(SOURCE_INVENTORY)
    if source_hash != shadow_manifest["inputs"]["IBN_HAJAR_12_RANK_SOURCE_INVENTORY_V0.md"]["sha256"]:
        raise SystemExit("Source inventory differs from the source hash recorded in the shadow-run manifest")

    entries = read_csv(ENTRY_INDEX)
    if len(entries) != 8827 or len({r["entry_id"] for r in entries}) != len(entries):
        raise SystemExit("Expected 8,827 unique numbered local entries")
    inventory_rows = read_csv(V02_DIR / "PHRASE_INVENTORY.csv")
    nohit_rows = read_csv(AI_DIR / "AI_FIRST_PHRASE_REVIEW_INDEX.csv")
    policy_rows = read_csv(PHRASE_REVIEW_DIR / "PHRASE_REVIEW_WORKSHEET_V1_1.csv")
    policy_by_phrase = {r["phrase_text_trimmed_for_grouping"]: r for r in policy_rows}

    # Verify hand-listed anchors appear in the local source inventory text.
    for rank, phrase, kind, note in ANCHORS:
        if phrase not in source_text:
            raise SystemExit(f"Source cue not present in source inventory text: {phrase}")

    records: dict[str, dict[str, Any]] = {}
    def record_for(phrase: str) -> dict[str, Any]:
        rec = records.setdefault(phrase, {
            "phrase": phrase, "sources": set(), "source_ranks": set(), "anchor_kinds": set(),
            "anchor_notes": set(), "v02_source_ranks": set(), "v02_pilot_ranks": set(),
            "ai_rank_suggestions": set(), "ai_phrase_types": set(), "v02_notes": set(),
            "ai_phrase_group": "", "phrase_policy_decision": "", "phrase_policy_scope": "",
        })
        return rec

    for rank, phrase, kind, note in ANCHORS:
        rec = record_for(phrase)
        rec["sources"].add("source_inventory_v0_exact_anchor")
        rec["source_ranks"].add(str(rank))
        rec["anchor_kinds"].add(kind)
        rec["anchor_notes"].add(note)
    for row in inventory_rows:
        rec = record_for(row["phrase_exact_verbatim"])
        rec["sources"].add("candidate_inventory_v0_2")
        rec["v02_source_ranks"].update(x for x in row.get("source_rank_anchor_candidates", "").split(";") if x)
        rec["v02_pilot_ranks"].update(x for x in row.get("pilot_rank_proposals_unverified", "").split(";") if x)
        rec["v02_notes"].update(x for x in row.get("source_notes", "").split(" || ") if x)
    for row in nohit_rows:
        phrase = row["phrase_text_trimmed_for_grouping"]
        rec = record_for(phrase)
        rec["sources"].add("ai_nohit_phrase_review_v1_3_grouped_candidate")
        rec["ai_rank_suggestions"].add(row.get("rank_suggestion_counts_unverified", ""))
        rec["ai_phrase_types"].add(row.get("phrase_type_counts", ""))
        rec["ai_phrase_group"] = "nohit_phrase_index_v1_3"
        if phrase in policy_by_phrase:
            pol = policy_by_phrase[phrase]
            if pol.get("human_decision", ""):
                rec["phrase_policy_decision"] = pol["human_decision"]
                rec["phrase_policy_scope"] = pol["human_rank_or_status_decision"]

    source_anchor_rows = []
    for i, (rank, phrase, kind, note) in enumerate(ANCHORS, 1):
        source_anchor_rows.append({
            "anchor_id": f"SRC-{i:03d}", "rank": rank,
            "source_example_or_cue_exact": phrase, "anchor_kind": kind,
            "source_definition_summary": RANK_NOTES[rank], "precondition_or_caution": note,
            "rank_assignment": "",
        })
    anchor_fields = list(source_anchor_rows[0].keys())
    write_csv(OUTPUT / "SOURCE_RANK_ANCHORS_V0_1.csv", source_anchor_rows, anchor_fields)

    candidate_rows = []
    example_rows = []
    for idx, phrase in enumerate(sorted(records), 1):
        rec = records[phrase]
        all_hits: list[tuple[dict[str, str], int, int, bool]] = []
        for entry in entries:
            for start, end, bounded in matches(entry["entry_text_verbatim"], phrase):
                all_hits.append((entry, start, end, bounded))
        bounded_hits = [h for h in all_hits if h[3]]
        example_source = bounded_hits if bounded_hits else all_hits
        sample_hits = example_source[:3]
        for ex_index, (entry, start, end, bounded) in enumerate(sample_hits, 1):
            text = entry["entry_text_verbatim"]
            example_rows.append({
                "candidate_id": f"VOC-{idx:03d}", "example_index": ex_index,
                "phrase_candidate_exact": phrase, "entry_id": entry["entry_id"],
                "printed_page_num": entry["printed_page_num"],
                "entry_number_verbatim": entry["entry_number_verbatim"],
                "match_start_char": start, "match_end_char": end,
                "arabic_letter_bounded": "yes" if bounded else "no",
                "context_before": text[max(0, start - 70):start],
                "matched_text": text[start:end],
                "context_after": text[end:min(len(text), end + 70)],
                "entry_text_verbatim": text,
            })
        bounded_entry_ids = {h[0]["entry_id"] for h in bounded_hits}
        all_entry_ids = {h[0]["entry_id"] for h in all_hits}
        non_anchor_sources = sorted(rec["sources"] - {"source_inventory_v0_exact_anchor"})
        if rec["source_ranks"]:
            basis = "explicit_source_anchor_and_or_candidate"
        else:
            basis = "corpus_candidate_unverified"
        candidate_rows.append({
            "candidate_id": f"VOC-{idx:03d}",
            "phrase_candidate_exact": phrase,
            "candidate_basis": basis,
            "discovery_sources": ";".join(sorted(rec["sources"])),
            "source_rank_anchor_numbers": ";".join(sorted(rec["source_ranks"], key=int)),
            "source_anchor_kinds": ";".join(sorted(rec["anchor_kinds"])),
            "v02_source_rank_candidates_unverified": ";".join(sorted(rec["v02_source_ranks"])),
            "v02_pilot_rank_proposals_unverified": ";".join(sorted(rec["v02_pilot_ranks"])),
            "ai_nohit_rank_suggestions_unverified": " || ".join(sorted(x for x in rec["ai_rank_suggestions"] if x)),
            "ai_nohit_phrase_types": " || ".join(sorted(x for x in rec["ai_phrase_types"] if x)),
            "phrase_group_id": rec["ai_phrase_group"],
            "phrase_policy_decision_v1_1": rec["phrase_policy_decision"],
            "phrase_policy_scope_v1_1": rec["phrase_policy_scope"],
            "corpus_exact_substring_occurrences": len(all_hits),
            "corpus_entries_with_exact_substring": len(all_entry_ids),
            "corpus_arabic_letter_bounded_occurrences": len(bounded_hits),
            "corpus_entries_with_bounded_match": len(bounded_entry_ids),
            "substring_only_occurrences": len(all_hits) - len(bounded_hits),
            "example_entry_ids": ";".join(h[0]["entry_id"] for h in sample_hits),
            "source_precondition_and_notes": " || ".join(sorted(rec["anchor_notes"] | rec["v02_notes"])),
            "rank_assignment": "",
            "auto_accept": "false",
        })
    candidate_fields = list(candidate_rows[0].keys())
    write_csv(OUTPUT / "CANDIDATE_VOCABULARY_V0_1.csv", candidate_rows, candidate_fields)

    cue_rows = []
    cue_example_rows = []
    for cue_index, (cue, ranks) in enumerate(SEARCH_CUES, 1):
        hits: list[tuple[dict[str, str], int, int, bool]] = []
        for entry in entries:
            for start, end, bounded in matches(entry["entry_text_verbatim"], cue):
                hits.append((entry, start, end, bounded))
        bounded_hits = [h for h in hits if h[3]]
        cue_rows.append({
            "cue_id": f"CUE-{cue_index:03d}", "literal_search_cue": cue,
            "related_rank_scopes_unverified": ranks,
            "substring_occurrences": len(hits),
            "entries_with_substring": len({h[0]["entry_id"] for h in hits}),
            "arabic_letter_bounded_occurrences": len(bounded_hits),
            "entries_with_bounded_match": len({h[0]["entry_id"] for h in bounded_hits}),
            "interpretation": "Discovery search string only; hits may be compounds, negation, biography, or unrelated wording.",
        })
        examples = (bounded_hits or hits)[:3]
        for ex_index, (entry, start, end, bounded) in enumerate(examples, 1):
            text = entry["entry_text_verbatim"]
            cue_example_rows.append({
                "cue_id": f"CUE-{cue_index:03d}", "literal_search_cue": cue,
                "example_index": ex_index, "entry_id": entry["entry_id"],
                "printed_page_num": entry["printed_page_num"],
                "match_start_char": start, "match_end_char": end,
                "arabic_letter_bounded": "yes" if bounded else "no",
                "context_before": text[max(0, start - 70):start],
                "matched_text": text[start:end],
                "context_after": text[end:min(len(text), end + 70)],
                "entry_text_verbatim": text,
            })
    write_csv(OUTPUT / "SOURCE_CUE_SCAN_V0_1.csv", cue_rows, list(cue_rows[0].keys()))
    write_csv(OUTPUT / "CANDIDATE_EXAMPLE_HITS_V0_1.csv", example_rows, list(example_rows[0].keys()))
    write_csv(OUTPUT / "SOURCE_CUE_EXAMPLES_V0_1.csv", cue_example_rows, list(cue_example_rows[0].keys()))

    decision_counts = Counter(r["phrase_policy_decision_v1_1"] for r in candidate_rows if r["phrase_policy_decision_v1_1"])
    source_counts = Counter(source for r in candidate_rows for source in r["discovery_sources"].split(";") if source)
    readme = f"""# Twelve-rank candidate vocabulary inventory v0.1\n\n**Status:** source-anchored candidate inventory; no entry ranks assigned and no production rules enabled.\n\n## What is included\n\n- {len(ANCHORS)} exact source cues from the twelve-rank introduction, with rank-definition conditions: `SOURCE_RANK_ANCHORS_V0_1.csv`.\n- {len(inventory_rows)} phrases from candidate inventory v0.2.\n- {len(nohit_rows)} phrase groups discovered in the three-batch no-hit AI review v1.3.\n- {len(candidate_rows)} unique exact phrase strings across these inputs, joined without Arabic normalization and scanned in {len(entries)} numbered local Taqrīb entries.\n- Broad literal cue searches with examples: `SOURCE_CUE_SCAN_V0_1.csv` and `SOURCE_CUE_EXAMPLES_V0_1.csv`.\n- Up to three corpus examples for each candidate phrase: `CANDIDATE_EXAMPLE_HITS_V0_1.csv`.\n- Primary-source/edition verification: `SOURCE_ANCHOR_VERIFICATION.md`.\n\nThe {len(ANCHORS)} source cues include status, praise, weakness, unknownness, abandonment, accusation, and lying/fabrication. The candidate list is a work inventory, not every expression Ibn Ḥajar may use. The search is anchored to existing source examples, the v0.2 candidate inventory, and the 148 no-hit AI phrase groups.\n\n## Read the columns carefully\n\n- `source_rank_anchor_numbers` records where an exact phrase is named in the introduction.\n- `v02_*_unverified` and `ai_nohit_*_unverified` preserve prior candidate suggestions; they are not accepted ranks.\n- `phrase_policy_decision_v1_1` records only the phrase-level decisions from v1.1; it does not label each matching entry.\n- `corpus_exact_substring_occurrences` counts literal occurrences. Arabic-letter-bounded counts help identify some substring collisions but do not establish semantic boundaries. Counts across phrase rows overlap and are not rank totals or coverage.\n- `rank_assignment` is blank and `auto_accept` is false for every phrase.\n\n## Rank safeguards\n\nThe introduction’s examples are illustrative, not exhaustive. A word hit cannot satisfy contextual definitions by itself. For example, Rank 6 `مقبول` depends on corroboration; Ranks 7 and 9 depend on different transmitter counts; Ranks 8 and 10 require distinct authentication/weakness conditions; Rank 11 accusation must remain distinct from Rank 12 applied lying/fabrication labels. Rank 5 memory terms and innovation descriptions need their full qualification. Rank 1 is status, separate from ordinary reliability. Generation wording such as `من العاشرة` is not reliability Rank 10.\n\nThe broad cue scan is literal substring discovery. It may hit negation, compounds, biography, or unrelated material; inspect the example contexts before adding a phrase. No stemming, normalization, or automatic classification is performed.\n\n## Edition and corpus limits\n\nThe local numbered-entry index has 8,827 entries and begins at printed page 75; it excludes 3,459 nonempty unnumbered chunks. The opening rank introduction is absent from the local pages, so its anchors come from the separately documented Dorar/ʿAwwāma digital text. Preserve the rank 5 variant `تغير بأخرة` versus Alifta’s `تغير بآخره`, and the rank 10 variant `بقدح` versus `بقادح`. The searchable text is not a scan.\n\n## Next review\n\nReview candidates by rank and construction, not by frequency alone. For each observed phrase, record whether it is an exact introduction example, an observed candidate, context-dependent, non-grade/status material, or unresolved. Preserve complete source spans and counterexamples. Do not change the twelve ranks, infer historical attribution from lexical similarity, or enable a rule from this inventory alone.\n\nSee `MANIFEST.json` and `MANIFEST.sha256` for input/output hashes. Phrase-level decision counts copied from v1.1: {dict(decision_counts)}. Discovery-source row counts (overlap allowed): {dict(source_counts)}.\n"""
    (OUTPUT / "README.md").write_text(readme, encoding="utf-8", newline="\n")

    input_paths = {
        "source_rank_inventory": SOURCE_INVENTORY,
        "entry_index": ENTRY_INDEX,
        "v02_phrase_inventory": V02_DIR / "PHRASE_INVENTORY.csv",
        "v02_manifest": V02_DIR / "MANIFEST.json",
        "ai_nohit_phrase_index": AI_DIR / "AI_FIRST_PHRASE_REVIEW_INDEX.csv",
        "ai_review_results_manifest": AI_DIR / "REVIEW_RESULTS_MANIFEST.json",
        "phrase_review_v1_1_worksheet": PHRASE_REVIEW_DIR / "PHRASE_REVIEW_WORKSHEET_V1_1.csv",
        "phrase_review_v1_1_manifest": PHRASE_REVIEW_DIR / "MANIFEST.json",
        "source_anchor_verification": ANCHOR_VERIFICATION,
        "generator_script": Path(__file__).resolve(),
    }
    manifest = {
        "package": "Ibn Hajar twelve-rank candidate vocabulary inventory v0.1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "candidate inventory only; zero rank assignments; zero rules enabled",
        "method": "Union exact source anchors, candidate inventory v0.2 phrases, and AI no-hit phrase-group strings. Count exact Unicode substring and Arabic-letter-bounded hits in ENTRY_INDEX without normalization. Preserve prior rank suggestions as unverified metadata.",
        "counts": {
            "source_rank_anchors": len(ANCHORS), "v02_phrases": len(inventory_rows),
            "ai_nohit_phrase_groups": len(nohit_rows), "unique_phrase_candidates": len(candidate_rows),
            "numbered_local_entries_scanned": len(entries), "rank_assignments": 0,
            "auto_accepts": 0, "phrase_policy_decisions_copied_from_v1_1": dict(decision_counts),
            "candidate_rows_by_discovery_source": dict(source_counts),
            "search_cues": len(cue_rows), "source_cue_examples": len(cue_example_rows),
        },
        "inputs": {name: {"path": str(path.relative_to(ROOT)).replace("\\", "/"), "sha256": sha256(path)} for name, path in input_paths.items()},
        "input_package_manifests": {
            "candidate_inventory_v0_2": {"sha256": sha256(V02_DIR / "MANIFEST.json")},
            "nohit_ai_review_v1_3": {"sha256": sha256(AI_DIR / "REVIEW_RESULTS_MANIFEST.json")},
            "phrase_review_v1_1": {"sha256": sha256(PHRASE_REVIEW_DIR / "MANIFEST.json")},
            "shadow_run_v1": {"sha256": sha256(shadow_dir / "RUN_MANIFEST.json")},
        },
        "outputs": {},
        "manifest_hash_note": "MANIFEST.json is not in its own outputs map; MANIFEST.sha256 hashes it.",
    }
    for path in sorted(OUTPUT.iterdir()):
        if path.is_file() and path.name not in {"MANIFEST.json", "MANIFEST.sha256"}:
            manifest["outputs"][path.name] = sha256(path)
    (OUTPUT / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    (OUTPUT / "MANIFEST.sha256").write_text(f"{sha256(OUTPUT / 'MANIFEST.json')}  MANIFEST.json\n", encoding="ascii", newline="\n")
    print(json.dumps({"output": str(OUTPUT), "source_anchors": len(ANCHORS), "v02_phrases": len(inventory_rows), "ai_nohit_groups": len(nohit_rows), "unique_phrase_candidates": len(candidate_rows), "entries_scanned": len(entries), "rank_assignments": 0, "auto_accepts": 0, "manifest_sha256": sha256(OUTPUT / "MANIFEST.json")}, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
