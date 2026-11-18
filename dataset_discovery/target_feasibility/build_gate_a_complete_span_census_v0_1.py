#!/usr/bin/env python3
"""Build Gate A Complete-Span Census v0.1 across all 8,827 numbered Taqrib entries.

Implements TODO lines 25-27:
- Preserves exact Arabic, printed_page_num, source_chunk_index, and frequency.
- Integrates 33 source rank anchors, 148 v1.2 phrase decisions, and 165 active
  morphological surface forms (excluding 12 homograph abstains).
- Separates first complete grade-bearing target candidate from attached
  qualifiers and context notes per Rank Target Policy v0.2.
- Compares each observed span with the 12 source-defined categories.
- Leaves all human_* verification fields blank and assigns zero canonical ranks.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PIPELINE = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline"
ENTRY_INDEX = PIPELINE / "rank_label_shadow_run_v1_2026-11-15/ENTRY_INDEX.csv"
SOURCE_ANCHORS = PIPELINE / "rank_vocabulary_candidate_inventory_v0_1_2026-11-16/SOURCE_RANK_ANCHORS_V0_1.csv"
PHRASE_V1_2 = PIPELINE / "rank_label_phrase_review_user_decisions_v1_2_2026-11-16/PHRASE_REVIEW_USER_DECISIONS_148_V1_2.csv"
MORPH_DECISIONS = PIPELINE / "gate_a_morphological_user_decisions_v0_1_2026-11-17/MORPHOLOGICAL_SURFACE_FORMS_USER_DECISIONS_V0_1.csv"
NONE_161 = PIPELINE / "rank_label_phrase_review_user_decisions_v1_2_2026-11-16/NONE_FOUND_USER_DECISIONS_161_V1_2.csv"
NONE_44 = PIPELINE / "gate_a_morphological_user_decisions_v0_1_2026-11-17/NONE_FOUND_44_MORPH_USER_DECISIONS_V0_1.csv"
OUT_DIR = PIPELINE / "gate_a_complete_span_census_v0_1_2026-11-17"

DIACRITICS_RE = re.compile(r"[\u064b-\u065f\u0670\u0640]")
ARABIC_LETTER = r"[\u0621-\u064a\u066e-\u06d3\u06fa-\u06fc]"

# Post-grade structural boundaries in Taqrib
POST_GRADE_STOP_RE = re.compile(
    r"\s+(?:"
    r"من\s+(?:الأولى|الثانية|الثالثة|الرابعة|الخامسة|السادسة|السابعة|الثامنة|التاسعة|العاشرة|الحادية\s+عشرة|الثانية\s+عشرة|كبار|صغار|أوساط|رؤوس|أهل)"
    r"|مات\s+(?:سنة|في|بعد|قبل|نحو|قريبا|بالمصيصة|ببغداد|بمكة|بالمدينة|بالكوفة|بالبصرة|بدمشق|بمصر|فجأة|وهو)"
    r"|استشهد"
    r"|قتل\s+(?:سنة|يوم|في|مع)"
    r"|عاش\s+"
    r"|تمييز\b"
    r")"
)
TRAILING_SIGILS_RE = re.compile(
    r"(?:\s+(?:خ|م|د|ت|س|ق|ع|٤|4|بخ|فق|مدت|قد|تخ|عخ|ل|ز|سي|كن|ص|خت|عس|تمييز))+$"
)

# Pre-hit clause openers that belong with the complete evaluative phrase
PRE_HIT_OPENERS = (
    "لا", "لم", "ليس", "ليست", "غير", "ما", "أحد", "من", "كثير", "سيء",
    "قليل", "حسن", "صالح", "شديد", "يقال", "قال", "وقيل", "قيل", "وقد",
    "بل", "إلا", "ربما", "كان", "وكان",
)

# Context-note / secondary clause splitters (Policy v0.2)
CONTEXT_SPLIT_RE = re.compile(
    r"\s+(?=(?:إلا\s+أن|لكنه|لكن|رمي\s+ب|اختلط|وتغير|تغير\s+بأخرة|يدلس|كثير\s+التدليس|تكلم\s+فيه|وله\s+أوهام|له\s+أوهام|له\s+مناكير|في\s+حديثه|وهم\s+من|وقد\s+وثق|ولينه|وثقه))"
)


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


def strip_diacritics_with_map(text: str) -> tuple[str, list[int]]:
    clean_chars: list[str] = []
    index_map: list[int] = []
    for idx, ch in enumerate(text):
        if DIACRITICS_RE.match(ch):
            continue
        clean_chars.append(ch)
        index_map.append(idx)
    return "".join(clean_chars), index_map


def expand_start_to_clause_opener(verbatim: str, v_start: int) -> int:
    prefix = verbatim[:v_start]
    tokens = list(re.finditer(r"\S+", prefix))
    if not tokens:
        return v_start
    # Pull up to 2 immediately preceding opener tokens if they are grammatical modifiers
    cur_start = v_start
    for tok_m in reversed(tokens[-2:]):
        tok_clean = DIACRITICS_RE.sub("", tok_m.group(0)).strip("[]()،.")
        if tok_clean in PRE_HIT_OPENERS:
            cur_start = tok_m.start()
        else:
            break
    return cur_start


def extract_assessment_region(verbatim: str, v_start: int) -> tuple[str, str]:
    clause_start = expand_start_to_clause_opener(verbatim, v_start)
    tail = verbatim[clause_start:]
    stop_m = POST_GRADE_STOP_RE.search(tail)
    if stop_m:
        region = tail[:stop_m.start()].strip()
    else:
        region = tail.strip()
    region = TRAILING_SIGILS_RE.sub("", region).strip(" ،.")
    if not region:
        return "", ""

    split_m = CONTEXT_SPLIT_RE.search(region)
    if split_m and split_m.start() > 0:
        first_span = region[:split_m.start()].strip(" ،.")
        context_span = region[split_m.start():].strip(" ،.")
        return first_span, context_span
    return region, ""


def main() -> None:
    if OUT_DIR.exists() and any(OUT_DIR.iterdir()):
        raise SystemExit(f"Refusing to overwrite existing census directory: {OUT_DIR}")

    entries = read_csv(ENTRY_INDEX)
    assert len(entries) == 8827

    anchor_rows = read_csv(SOURCE_ANCHORS)
    anchor_map: dict[str, list[str]] = defaultdict(list)
    for r in anchor_rows:
        exact = DIACRITICS_RE.sub("", r["source_example_or_cue_exact"].strip())
        anchor_map[exact].append(r["rank"])

    phrase_rows = read_csv(PHRASE_V1_2)
    accepted_phrases: set[str] = set()
    conditional_phrases: set[str] = set()
    for r in phrase_rows:
        p = DIACRITICS_RE.sub("", (r.get("human_approved_span_exact") or r["phrase_text_trimmed_for_grouping"]).strip())
        dec = r["human_decision"].strip()
        if dec == "accept":
            accepted_phrases.add(p)
        elif dec in {"conditional", "revise"}:
            conditional_phrases.add(p)

    morph_rows = read_csv(MORPH_DECISIONS)
    active_forms: list[str] = []
    conditional_forms: set[str] = set()
    form_to_family: dict[str, str] = {}
    for r in morph_rows:
        disp = r["human_census_disposition"].strip()
        surf = r["surface_form_no_diacritics"].strip()
        if disp == "abstain":
            continue
        active_forms.append(surf)
        form_to_family[surf] = r["family_id"]
        if disp == "conditional":
            conditional_forms.add(surf)

    active_forms.sort(key=len, reverse=True)
    active_re = re.compile(rf"(?<!{ARABIC_LETTER})(?:{'|'.join(re.escape(f) for f in active_forms)})(?!{ARABIC_LETTER})")

    none_161_abstain = {
        r["entry_id"] for r in read_csv(NONE_161) if r["human_decision"].strip() == "abstain"
    }
    none_44_map = {r["entry_id"]: r["human_decision"].strip() for r in read_csv(NONE_44)}

    entry_census_rows: list[dict[str, Any]] = []
    unique_span_counts: Counter[str] = Counter()
    unique_span_cats: dict[str, Counter[str]] = defaultdict(Counter)
    unique_span_examples: dict[str, list[str]] = defaultdict(list)
    unique_span_ranks: dict[str, str] = {}

    for entry in entries:
        eid = entry["entry_id"]
        verbatim = entry["entry_text_verbatim"]
        clean_text, idx_map = strip_diacritics_with_map(verbatim)

        # Respect confirmed none_found abstains unless explicitly revised to candidate (E2037)
        if eid in none_161_abstain and none_44_map.get(eid) != "revise_to_candidate":
            first_span, context_span = "", ""
            gate_a_cat = "non_grade_or_abstain"
            matched_ranks = ""
            matched_families = ""
            first_hit_surface = ""
        else:
            matches = list(active_re.finditer(clean_text))
            if not matches:
                first_span, context_span = "", ""
                gate_a_cat = "non_grade_or_abstain"
                matched_ranks = ""
                matched_families = ""
                first_hit_surface = ""
            else:
                m0 = matches[0]
                v_start = idx_map[m0.start()]
                first_hit_surface = m0.group(0)
                matched_families = "|".join(sorted({form_to_family[m.group(0)] for m in matches}))
                first_span, context_span = extract_assessment_region(verbatim, v_start)
                first_clean = DIACRITICS_RE.sub("", first_span).strip()

                ranks_found = anchor_map.get(first_clean, [])
                matched_ranks = "|".join(ranks_found)

                if first_clean in anchor_map:
                    gate_a_cat = "explicit_source_example"
                elif first_clean in accepted_phrases and not context_span and "[" not in first_span:
                    gate_a_cat = "approved_phrase_candidate"
                elif (
                    context_span
                    or first_hit_surface in conditional_forms
                    or first_clean in conditional_phrases
                    or "[" in first_span
                    or any(neg in first_clean for neg in ("لا ", "لم ", "ليس ", "غير "))
                ):
                    gate_a_cat = "context_dependent_or_qualified"
                else:
                    gate_a_cat = "candidate_requiring_review"

        if first_span:
            unique_span_counts[first_span] += 1
            unique_span_cats[first_span][gate_a_cat] += 1
            if len(unique_span_examples[first_span]) < 3:
                unique_span_examples[first_span].append(eid)
            if first_span not in unique_span_ranks:
                unique_span_ranks[first_span] = matched_ranks

        row_out = {
            "entry_id": eid,
            "printed_page_num": entry["printed_page_num"],
            "source_chunk_index": entry["source_chunk_index"],
            "entry_number_verbatim": entry["entry_number_verbatim"],
            "first_complete_target_span_exact": first_span,
            "context_note_spans_exact": context_span,
            "earliest_morph_token": first_hit_surface,
            "matched_morph_families": matched_families,
            "matched_source_anchor_ranks": matched_ranks,
            "gate_a_category": gate_a_cat,
            "human_verification_status": "",
            "human_notes": "",
        }
        for k, v in row_out.items():
            assert_no_em_en_dash(str(v), f"{eid}.{k}")
        entry_census_rows.append(row_out)

    unique_rows: list[dict[str, Any]] = []
    for span, freq in unique_span_counts.most_common():
        dominant_cat = unique_span_cats[span].most_common(1)[0][0]
        u_row = {
            "first_complete_target_span_exact": span,
            "frequency": freq,
            "gate_a_category": dominant_cat,
            "matched_source_anchor_ranks": unique_span_ranks.get(span, ""),
            "example_entry_ids": " | ".join(unique_span_examples[span]),
            "human_review_decision": "",
            "human_notes": "",
        }
        for k, v in u_row.items():
            assert_no_em_en_dash(str(v), f"unique.{k}")
        unique_rows.append(u_row)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    entry_csv = OUT_DIR / "GATE_A_ENTRY_COMPLETE_SPAN_CENSUS_V0_1.csv"
    unique_csv = OUT_DIR / "GATE_A_UNIQUE_SPAN_INVENTORY_V0_1.csv"
    write_csv(entry_csv, entry_census_rows, list(entry_census_rows[0]))
    write_csv(unique_csv, unique_rows, list(unique_rows[0]))

    cat_counts = Counter(r["gate_a_category"] for r in entry_census_rows)
    summary_lines = [
        "# Gate A Complete-Span Census v0.1 (TODO Lines 25-27)",
        "",
        "**Status:** complete-span census across all `8,827` numbered local *Taqrīb* entries (`ENTRY_INDEX.csv`), integrating approved `v1.2` phrase decisions and `v0.1` morphological declension/derivation decisions. All `human_*` verification fields remain blank pending sample review (`TODO` line 28). Zero canonical ranks assigned and zero rules enabled.",
        "",
        "## Entry-Level Distribution (`8,827` entries)",
        f"- Category counts: `{dict(sorted(cat_counts.items()))}`",
        f"- Entries with a non-empty first complete target span: `{sum(1 for r in entry_census_rows if r['first_complete_target_span_exact'])}`",
        f"- Entries with a separated Policy v0.2 context-note span: `{sum(1 for r in entry_census_rows if r['context_note_spans_exact'])}`",
        f"- Distinct exact complete target spans observed: `{len(unique_rows)}`",
        "",
        "## Top 15 Complete Spans by Frequency",
    ]
    for u in unique_rows[:15]:
        summary_lines.append(
            f"- `{u['first_complete_target_span_exact']}` (`n={u['frequency']}`, `{u['gate_a_category']}`)"
        )
    summary_text = "\n".join(summary_lines)
    assert_no_em_en_dash(summary_text, "CENSUS_SUMMARY_V0_1.md")
    summary_path = OUT_DIR / "CENSUS_SUMMARY_V0_1.md"
    summary_path.write_text(summary_text, encoding="utf-8", newline="\n")

    timestamp = datetime.now(timezone.utc).isoformat()
    inputs = [ENTRY_INDEX, SOURCE_ANCHORS, PHRASE_V1_2, MORPH_DECISIONS, NONE_161, NONE_44, Path(__file__).resolve()]
    outputs = [entry_csv, unique_csv, summary_path]
    manifest = {
        "package_id": OUT_DIR.name,
        "generated_at_utc": timestamp,
        "scope": "Gate A complete-span census v0.1 across 8,827 numbered Taqrib entries (Policy v0.2 two-layer split); human_* blank; zero canonical ranks assigned.",
        "counts": {
            "entries_total": len(entry_census_rows),
            "gate_a_category_counts": dict(sorted(cat_counts.items())),
            "entries_with_target_span": sum(1 for r in entry_census_rows if r["first_complete_target_span_exact"]),
            "entries_with_context_span": sum(1 for r in entry_census_rows if r["context_note_spans_exact"]),
            "distinct_complete_spans": len(unique_rows),
            "canonical_ranks_assigned": 0,
            "rules_enabled": 0,
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
