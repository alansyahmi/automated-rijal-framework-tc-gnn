#!/usr/bin/env python3
"""Reproducible generation of Shamela4 20-case blinded human annotation pilot.

Selects 20 purposive cases from the frozen 60-case validation sample
(TUPLE_MANUAL_VALIDATION.csv in forensic_verification_v3), ensuring semantic diversity
across all 6 strata while enforcing strict reviewer blinding.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]

V3_INPUT_RELATIVE = "data/2_interim/shamela4_narrator_audit/stage2_diagnostics/forensic_verification_v3/TUPLE_MANUAL_VALIDATION.csv"
V3_EXPECTED_HASH = "b798f472da05ce58cb16a1588f00325ae74bc70f1e62fa5407a3524c35fd8325"

# Annotation fields required by Section 6 of the specification
ANNOTATION_FIELDS = [
    # A. Evaluated narrator
    "evaluated_narrator_id",
    "evaluated_narrator_name_as_written",
    "evaluated_narrator_confidence",
    # B. Historical evaluator and attribution
    "historical_evaluator_as_written",
    "historical_evaluator_normalized",
    "intermediate_quoted_speaker",
    "compiler_or_source_author",
    "attribution_type",
    # C. Evaluative content
    "contains_evaluation",
    "evaluative_span_verbatim",
    "stance",
    "qualification_or_context",
    "evaluation_target",
    # D. Documentary provenance
    "source_work_as_written",
    "source_work_normalized",
    "source_locator_as_written",
    "quotation_boundary",
    "citation_boundary",
    "number_of_works_referenced",
    # E. Annotation quality
    "transcription_confidence",
    "interpretation_confidence",
    "unresolved_ambiguity",
    "reviewer_notes",
]

REVIEWER_FIELDS = [
    "pilot_case_id",
    "narrator_id",
    "narrator_name",
    "entry_index",
    "original_field_1",
    "original_field_2",
    "original_tuple_json",
    *ANNOTATION_FIELDS,
]

MAPPING_FIELDS = [
    "pilot_case_id",
    "v3_case_id",
    "source_id",
    "narrator_id",
    "narrator_name",
    "group_label",
    "entry_index",
    "sampling_stratum",
    "automated_pattern",
    "automated_certainty",
    "source_ID_level_classification",
    "quotation_citation_separability",
]

SELECTION_FIELDS = [
    "pilot_case_id",
    "v3_case_id",
    "source_id",
    "sampling_stratum",
    "narrator_id",
    "narrator_name",
    "group_label",
    "target_phenomenon",
    "selection_rationale",
]

# Purposive selection specification from the 60-case validation pool
PILOT_CASE_SPECS = [
    # Stratum 1: unnumbered_suffix_or_formatting (3 cases)
    {
        "v3_case_id": "TV001",
        "target_phenomenon": "Unnumbered suffix citation variant without evaluative text",
        "selection_rationale": "Archetypal locator variant bearing unnumbered suffix (بدون ترقيم) and colon discrepancy in Sharh Mushkil al-Athar; non-evaluative citation test case.",
    },
    {
        "v3_case_id": "TV005",
        "target_phenomenon": "Cross-work unnumbered suffix format in Musnad al-Bazzar",
        "selection_rationale": "Second distinct classical compiler (al-Bazzar) verifying cross-collection uniformity of the unnumbered suffix format.",
    },
    {
        "v3_case_id": "TV007",
        "target_phenomenon": "Third compiler unnumbered suffix in Sahih Ibn Khuzayma",
        "selection_rationale": "Third compiler/work testing unnumbered suffix format across different collection genres without prose.",
    },
    # Stratum 2: compound_or_multiple_locator (3 cases)
    {
        "v3_case_id": "TV012",
        "target_phenomenon": "Short formulaic negative with explicit critic name and secondary citation",
        "selection_rationale": "Formulaic negative statement ('قال الدارقطني ضعيف') transmitted across multiple works (Sunan al-Bayhaqi and Lisan al-Mizan).",
    },
    {
        "v3_case_id": "TV014",
        "target_phenomenon": "Deep nested attribution isnad with negative non-recognition judgment",
        "selection_rationale": "Multi-tier isnad chain (Ibn Abi Hatim -> Abd al-Rahman -> Muhammad -> Abu Talib -> Ahmad) declaring lack of knowledge ('لا أعرفه').",
    },
    {
        "v3_case_id": "TV018",
        "target_phenomenon": "Ultra-short collective passive formulaic negative",
        "selection_rationale": "Single passive plural verb ('كذبوه') from Taqrib al-Tahdhib attached to hadith locator in al-Matalib al-Aliyah; tests collective attribution.",
    },
    # Stratum 3: mixed_source_ID (4 cases)
    {
        "v3_case_id": "TV021",
        "target_phenomenon": "Authorial internal cross-reference and retrospective qualification",
        "selection_rationale": "Compiler (al-Bazzar) referring back to earlier treatment of narrator weakness ('تقدم ذكرنا له بلينه'); tests authorial voice.",
    },
    {
        "v3_case_id": "TV022",
        "target_phenomenon": "Multiple historical evaluators with compounding severity",
        "selection_rationale": "Single entry containing inqita ruling plus conflicting/compound critics: Malik ('لا يرتضيه') and Yahya b. Ma'in ('كذاب').",
    },
    {
        "v3_case_id": "TV024",
        "target_phenomenon": "Complex isnad hearing denial combined with shahid citation",
        "selection_rationale": "Multi-layered transmission discussion citing Sahih Muslim shahid, Shu'bah on hearing disconnect, and compiler commentary ('قلت:').",
    },
    {
        "v3_case_id": "TV028",
        "target_phenomenon": "Pure generational inqita statement without moral/memory disparagement",
        "selection_rationale": "Chronological non-contiguity statement ('لم يدرك النبي صلى الله عليه وسلم'); tests distinction between neutral chronology and negative stance.",
    },
    # Stratum 4: suspected_or_unresolved (4 cases)
    {
        "v3_case_id": "TV032",
        "target_phenomenon": "Transmission singularity (tafarrud) combined with qualified negative grade",
        "selection_rationale": "Joint tafarrud notation ('تفرد به...') and nuanced negative appraisal ('وليس بالقوي'); tests context qualification.",
    },
    {
        "v3_case_id": "TV036",
        "target_phenomenon": "Composite narrator-level rejection and hadith-level textual invalidation",
        "selection_rationale": "Simultaneous narrator impugnment ('منكر الحديث') with nickname/title and hadith-level invalidation ('ولا يصح عن الزهري').",
    },
    {
        "v3_case_id": "TV037",
        "target_phenomenon": "Compound legal verdict, hadith invalidation, and narrator disqualification",
        "selection_rationale": "Compound statement combining hadith invalidation ('لا يثبت'), narrator rejection ('لا يحتج به'), and comparative isnad preference.",
    },
    {
        "v3_case_id": "TV038",
        "target_phenomenon": "Mixed narrator memory criticism and biographical identification of father",
        "selection_rationale": "Entry mixing specific memory criticism ('قد تكلم فيه من قبل حفظه') with independent biographical clarification of another person's name.",
    },
    # Stratum 5: normal_prose_then_citation (3 cases)
    {
        "v3_case_id": "TV043",
        "target_phenomenon": "Ambiguous single-name narrator target in transmitted hearing denial",
        "selection_rationale": "Transmitted hearing denial targeting an ambiguous single token ('عبد الله'); tests evaluator and narrator identification bounds.",
    },
    {
        "v3_case_id": "TV045",
        "target_phenomenon": "Monumental multi-scholar classical debate with favorable proof argument",
        "selection_rationale": "Major multi-scholar classical evaluation quoting Bukhari, Ahmad, Ishaq b. Rahawayh, Abu Amr b. al-Ala, and al-Humaydi with conflicting views on Amr b. Shu'ayb.",
    },
    {
        "v3_case_id": "TV048",
        "target_phenomenon": "Concise classical formulaic inqita statement",
        "selection_rationale": "Clear, concise, single-evaluator transmission disconnect by al-Nasa'i ('مكحول لم يسمع من عنبسة شيئا').",
    },
    # Stratum 6: citation_only_then_locator_bearing_prose (3 cases)
    {
        "v3_case_id": "TV052",
        "target_phenomenon": "Nuanced/mixed appraisal with cognitive decline qualification in old age",
        "selection_rationale": "High leadership praise ('أحد أئمة المسلمين') qualified by late-life memory decline ('لما كبر ساء حفظه') and Bukhari exclusion; tests qualified stance.",
    },
    {
        "v3_case_id": "TV053",
        "target_phenomenon": "Comparative preference inquiry between two prominent narrators",
        "selection_rationale": "Uthman al-Darimi asking Ibn Ma'in which of two narrators is more beloved ('أحب إليك... فقال كلاهما'); tests comparative stance.",
    },
    {
        "v3_case_id": "TV057",
        "target_phenomenon": "Multi-critic joint attribution across multiple distinct classical works",
        "selection_rationale": "Cross-work attribution quoting al-Darqutni (Sunan) and al-Bayhaqi (al-Ma'rifah) inside a tertiary compiler (Ikmal Tahdhib al-Kamal).",
    },
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({
                field: row.get(field, "") if row.get(field) is not None else ""
                for field in fields
            })


def select_pilot_cases(
    v3_rows: list[dict[str, str]],
    seed: int = 20261111,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Select 20 cases according to specification and assign blinded IDs deterministically."""
    v3_by_case = {row["case_id"]: row for row in v3_rows}
    
    # Verify all requested cases exist in v3
    selected: list[dict[str, Any]] = []
    stratum_counts: dict[str, int] = {}
    for spec in PILOT_CASE_SPECS:
        cid = spec["v3_case_id"]
        if cid not in v3_by_case:
            raise KeyError(f"Requested pilot case {cid} not found in V3 dataset")
        v3_row = v3_by_case[cid]
        stratum = v3_row["sampling_stratum"]
        stratum_counts[stratum] = stratum_counts.get(stratum, 0) + 1
        
        selected.append({
            "v3_case_id": cid,
            "source_id": v3_row["source_id"],
            "narrator_id": v3_row["narrator_id"],
            "narrator_name": v3_row["narrator_name"],
            "group_label": v3_row["group_label"],
            "entry_index": v3_row["entry_index"],
            "original_tuple_json": v3_row["original_tuple_json"],
            "original_field_1": v3_row["original_field_1"],
            "original_field_2": v3_row["original_field_2"],
            "sampling_stratum": stratum,
            "automated_pattern": v3_row["automated_pattern"],
            "automated_certainty": v3_row["automated_certainty"],
            "source_ID_level_classification": v3_row["source_ID_level_classification"],
            "quotation_citation_separability": v3_row["quotation_citation_separability"],
            "target_phenomenon": spec["target_phenomenon"],
            "selection_rationale": spec["selection_rationale"],
        })
    
    # Shuffle presentation order using documented seed to prevent stratum-block leakage
    rng = random.Random(seed)
    shuffled_indices = list(range(len(selected)))
    rng.shuffle(shuffled_indices)
    
    # Assign blinded Pilot Case IDs (PILOT01 to PILOT20)
    for rank, idx in enumerate(shuffled_indices, start=1):
        selected[idx]["pilot_case_id"] = f"PILOT{rank:02d}"
        selected[idx]["presentation_order"] = rank

    # Sort selected items by presentation order (PILOT01..PILOT20)
    selected.sort(key=lambda x: x["presentation_order"])
    return selected, stratum_counts


def build_reviewer_rows(selected_cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build blinded reviewer copy omitting all automated/stratum labels and leaving annotation fields blank."""
    reviewer_rows = []
    for case in selected_cases:
        row = {
            "pilot_case_id": case["pilot_case_id"],
            "narrator_id": case["narrator_id"],
            "narrator_name": case["narrator_name"],
            "entry_index": case["entry_index"],
            "original_field_1": case["original_field_1"],
            "original_field_2": case["original_field_2"],
            "original_tuple_json": case["original_tuple_json"],
        }
        for field in ANNOTATION_FIELDS:
            row[field] = ""
        reviewer_rows.append(row)
    return reviewer_rows


def build_internal_mapping_rows(selected_cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build full mapping from blinded pilot IDs to original source IDs and automated metadata."""
    mapping_rows = []
    for case in selected_cases:
        mapping_rows.append({
            "pilot_case_id": case["pilot_case_id"],
            "v3_case_id": case["v3_case_id"],
            "source_id": case["source_id"],
            "narrator_id": case["narrator_id"],
            "narrator_name": case["narrator_name"],
            "group_label": case["group_label"],
            "entry_index": case["entry_index"],
            "sampling_stratum": case["sampling_stratum"],
            "automated_pattern": case["automated_pattern"],
            "automated_certainty": case["automated_certainty"],
            "source_ID_level_classification": case["source_ID_level_classification"],
            "quotation_citation_separability": case["quotation_citation_separability"],
        })
    return mapping_rows


def build_selection_rows(selected_cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build documentation table recording sampling stratum and selection rationale."""
    selection_rows = []
    for case in selected_cases:
        selection_rows.append({
            "pilot_case_id": case["pilot_case_id"],
            "v3_case_id": case["v3_case_id"],
            "source_id": case["source_id"],
            "sampling_stratum": case["sampling_stratum"],
            "narrator_id": case["narrator_id"],
            "narrator_name": case["narrator_name"],
            "group_label": case["group_label"],
            "target_phenomenon": case["target_phenomenon"],
            "selection_rationale": case["selection_rationale"],
        })
    return selection_rows


def generate_codebook() -> str:
    """Generate the comprehensive Markdown annotation codebook."""
    return """# Shamela4 Narrator Criticism Annotation Codebook

## 1. Research Context and Purpose

This codebook provides precise instructions for human annotators validating narrator criticism (`garh`) entries extracted from the Shamela4 database (`narrators.parquet`).

The objective is to establish the ground truth interpretation of criticism tuples before any automated classification rules, representation models (such as AraBERT), or Graph Neural Networks (GNNs) are trained.

### Core Ground Rules
1. **Zero Fabrication**: Never guess or invent an attribution, stance, or date not justified by the text.
2. **Preserve Verbatim Text**: Never normalize or edit Arabic quotations in verbatim fields.
3. **No Group Label Conflation**: Do not assume the `group_label` (e.g. `البخاري`, `الدارقطني`) is the historical speaker. Many entries transmit quotes from other scholars.
4. **No Binary Forcing**: Do not force nuanced or ambiguous statements into binary positive or negative categories.
5. **Separation of Entities**: Keep historical speaker attribution, source work authorship, narrator identity, and evaluative stance strictly distinct.

---

## 2. Unit of Analysis Policy

A single tuple consists of two text fields (`field_1`, `field_2`) and an opaque `source_id`.
- **Default Assumption**: One tuple usually represents one record in the compiler's database, but it **does not** necessarily contain exactly one evaluation.
- **Multiple Evaluations in One Tuple**: When an entry quotes multiple critics (e.g., Malik and Yahya b. Ma'in) or evaluates multiple individuals, annotate the primary evaluation in the main columns and document the secondary evaluations in `reviewer_notes` and `unresolved_ambiguity`.
- **Non-Evaluative Entries**: If a tuple contains only bibliographic citations, book numbers, or hadith locators without human evaluative prose, mark `contains_evaluation = no` and set evaluative fields to `not_applicable`.

---

## 3. Schema and Field Definitions

### Section A: Evaluated Narrator

#### `evaluated_narrator_id`
- **Definition**: The internal numeric narrator ID in `narrators.parquet` if the text clearly evaluates the entity to which the entry is attached.
- **Allowed Values**: Integer string (e.g. `12467`), or blank if the text evaluates a different person or identity is unlinked.
- **Rule**: If the entry actually evaluates a different narrator mentioned in the chain (e.g., father, teacher, or hadith partner), record the target person's name in `evaluated_narrator_name_as_written` and leave `evaluated_narrator_id` blank unless verified.

#### `evaluated_narrator_name_as_written`
- **Definition**: Verbatim Arabic name of the evaluated person appearing directly within the text span.
- **Allowed Values**: Exact Arabic string from text, or `[غير مصرح به]` (unnamed/implicit) if the name is omitted by pronoun or context.
- **Example**: `معارك بن عباد العبدي`, `أبو جابر البياضي`, `حارثة`.

#### `evaluated_narrator_confidence`
- **Definition**: Confidence that the text evaluates the identified individual.
- **Allowed Values**: `high`, `medium`, `low`, `unresolved`.

---

### Section B: Historical Evaluator and Attribution

#### `historical_evaluator_as_written`
- **Definition**: The verbatim scholar or critic name to whom the judgment is attributed in the text.
- **Allowed Values**: Exact Arabic string from text (e.g., `أحمد بن حنبل`, `مالك بن أنس`, `يحيى بن معين`), or `[المؤلف/المصنف]` if spoken directly by the work's author without attribution, or `[مجهول/صيغة تمريض]` for passive phrases like `كذبوه` or `قيل`.

#### `historical_evaluator_normalized`
- **Definition**: Standardized classical scholarly name of the evaluator for cross-record analysis.
- **Allowed Values**: Canonical Arabic name (e.g., `أحمد بن حنبل`, `يحيى بن معين`, `الدارقطني`, `علي بن المديني`, `ابن حجر العسقلاني`).

#### `intermediate_quoted_speaker`
- **Definition**: Intermediate transmitter through whom the evaluation was received, if nested transmission is present.
- **Allowed Values**: Name of the transmitter (e.g., `عثمان الدارمي`, `أبو طالب`, `عبد الله بن أحمد`), `none`, or `unclear`.

#### `compiler_or_source_author`
- **Definition**: The classical author/compiler of the physical book containing the text.
- **Allowed Values**: Canonical author name (e.g., `الترمذي`, `البيهقي`, `ابن عدي`, `الطحاوي`, `البزار`).

#### `attribution_type`
- **Definition**: The structural nature of the speech attribution.
- **Allowed Values**:
  - `direct`: The author/evaluator speaks directly in their own book without chain (e.g., `قلت: ...`, `لا نعرفه إلا من هذا الوجه`).
  - `transmitted`: Quoting another scholar with an explicit reporting verb (e.g., `قال أحمد: ضعيف`, `سألت يحيى بن معين فقال...`).
  - `paraphrased`: A summary or loose restatement of another critic's opinion without verbatim claim.
  - `nested_attribution`: Quoting an evaluation through an explicit isnad chain of two or more links (e.g., `حدثنا فلان قال نا فلان قال سمعت أبا طالب قال قال أحمد...`).
  - `unclear`: Ambiguous speaker or passive formulation without clear agent (e.g., `كذبوه`, `تكلم فيه`).
  - `not_applicable`: Non-evaluative entries (e.g., pure book citations).

---

### Section C: Evaluative Content

#### `contains_evaluation`
- **Definition**: Does the entry contain an actual qualitative assessment of a narrator's character, memory, reliability, or transmission validity?
- **Allowed Values**: `yes`, `no`, `unclear`.
- **Note**: Pure citations (e.g., `شرح مشكل الآثار (12/ 362) (بدون ترقيم)`) must be annotated as `no`.

#### `evaluative_span_verbatim`
- **Definition**: The exact, verbatim Arabic substring expressing the appraisal.
- **Allowed Values**: Verbatim substring, or blank if `contains_evaluation = no`.
- **Examples**: `ضعيف`, `كذبوه`, `ليس بالقوي`, `لا أعرفه`, `متروك الحديث`, `هو أحد أئمة المسلمين إلا أنه لما كبر ساء حفظه`.

#### `stance`
- **Definition**: Overall scholarly orientation towards the subject.
- **Allowed Values**:
  - `positive`: Explicit praise or endorsement (e.g., `ثقة`, `صدوق`, `حجة`, `أحب إلي كلاهما`).
  - `negative`: Explicit criticism or disparagement (e.g., `ضعيف`, `كذاب`, `متروك`, `منكر الحديث`, `كذبوه`).
  - `mixed`: Co-presence of positive and negative remarks in the same evaluation (e.g., `هو أحد أئمة المسلمين إلا أنه لما كبر ساء حفظه`).
  - `qualified`: Restricted validity or conditional acceptance (e.g., `ليس بالقوي`, `قد تكلم فيه من قبل حفظه`, `ضعيف في فلان دون فلان`).
  - `neutral_descriptive`: Factual isnad observation without moral/memory criticism (e.g., `لم يسمع من فلان`, `لم يدرك النبي صلى الله عليه وسلم`, `تفرد به فلان`).
  - `unclear`: Ambiguous wording that defies clear stance interpretation.
  - `not_applicable`: When `contains_evaluation = no`.

#### `qualification_or_context`
- **Definition**: Specific contextual boundaries, conditions, or scopes placed on the judgment.
- **Allowed Values**: Text string describing the limitation (e.g., `في حفظه لا في عدالته`, `لما كبر في السن`, `عن عطاء دون غيره`, `في رواية هذا الحديث خاصة`), or `none`.

#### `evaluation_target`
- **Definition**: What exact entity is being evaluated?
- **Allowed Values**:
  - `narrator_overall`: General status of the narrator across all transmissions.
  - `specific_transmission_link`: Contact or hearing between two specific individuals (e.g., `لم يسمع من عكرمة`).
  - `specific_hadith_text`: Quality or flaw in a single specific narration (e.g., `هذا حديث لا يثبت`).
  - `book_or_manuscript`: Accuracy of the narrator's written notes or copies.
  - `not_applicable`: When `contains_evaluation = no`.

---

### Section D: Documentary Provenance

#### `source_work_as_written`
- **Definition**: Title of the source book as written in the text or locator span.
- **Allowed Values**: Verbatim Arabic title (e.g., `سنن البيهقي الكبرى`, `شرح مشكل الآثار`, `جامع الترمذي`, `لسان الميزان`).

#### `source_work_normalized`
- **Definition**: Canonical title of the referenced work.
- **Allowed Values**: Standard Arabic book title (e.g., `سنن البيهقي الكبرى`, `شرح مشكل الآثار`, `جامع الترمذي`, `لسان الميزان`, `تقريب التهذيب`, `الجرح والتعديل لابن أبي حاتم`).

#### `source_locator_as_written`
- **Definition**: Verbatim volume, page, or hadith number string.
- **Allowed Values**: Verbatim string (e.g., `(1/ 23) برقم: (81)`, `(12/ 362) (بدون ترقيم)`, `(7/ 144) برقم: (1316)`).

#### `quotation_boundary`
- **Definition**: Description of where the quotation starts and ends within the fields.
- **Allowed Values**: Descriptive note (e.g., `entire_field_1`, `field_2_before_citation`, `field_1_middle_span`, `none`).

#### `citation_boundary`
- **Definition**: Description of where the documentary citation occurs.
- **Allowed Values**: Descriptive note (e.g., `field_1_locator_only`, `trailing_in_field_2`, `both_fields_citation_only`, `none`).

#### `number_of_works_referenced`
- **Definition**: Total count of distinct published classical works cited in the tuple.
- **Allowed Values**: Non-negative integer (`0`, `1`, `2`, `3`).

---

### Section E: Annotation Quality

#### `transcription_confidence`
- **Definition**: Confidence that the raw digital text faithfully reflects standard Arabic typography without OCR/ingestion corruption.
- **Allowed Values**: `high`, `medium`, `low`, `unresolved`.

#### `interpretation_confidence`
- **Definition**: Confidence in your understanding of the classical Arabic terminology and grammatical attribution.
- **Allowed Values**: `high`, `medium`, `low`, `unresolved`.

#### `unresolved_ambiguity`
- **Definition**: Specific questions, competing interpretations, or structural paradoxes.
- **Allowed Values**: Concise explanatory text, or `none`.

#### `reviewer_notes`
- **Definition**: Any free-text notes, anomalies, cross-references, or historical observations.
- **Allowed Values**: Free-text string.
"""


def generate_protocol(stratum_counts: dict[str, int], seed: int) -> str:
    """Generate the Markdown protocol document for the pilot study."""
    strata_lines = "\n".join(f"- `{stratum}`: {count} cases" for stratum, count in stratum_counts.items())
    return f"""# Shamela4 20-Case Blinded Manual Annotation Pilot Protocol

## 1. Objectives

The purpose of this pilot study is to evaluate the feasibility, clarity, and precision of the human annotation codebook on a purposive sample of 20 criticism tuples extracted from Shamela4.

Specific research questions investigated by this pilot:
1. **Evaluative Content**: Can human annotators reliably distinguish between genuine evaluative judgements and purely documentary citations?
2. **Narrator Disambiguation**: Is the evaluated individual clearly identifiable, especially in ambiguous or compound names?
3. **Attribution Boundaries**: Can historical critics (e.g., Ahmad, Yahya b. Ma'in) be reliably distinguished from compilers (e.g., al-Tirmidhi, al-Bayhaqi) and intermediate transmitters?
4. **Attribution Type**: Can direct statements, nested transmissions, and passive consensus phrases be systematically differentiated?
5. **Span Isolation**: Can the evaluative span be isolated from surrounding biographical notes, isnad commentary, and legal debates?
6. **Compound Occurrences**: How frequently do multiple evaluators, judgements, or works co-occur within a single tuple?
7. **Automated Concordance**: Do existing automated heuristic patterns align with human semantic understanding?

---

## 2. Sampling Design and Rationale

The 20 cases are purposively drawn from the frozen 60-case sample (`TUPLE_MANUAL_VALIDATION.csv` in `forensic_verification_v3`).

### Stratification Representation
All six validation strata are represented in the pilot:
{strata_lines}

### Purposive Selection Criteria
Cases were selected to maximize semantic, structural, and grammatical diversity:
- **Short formulaic negative evaluations**: e.g., `PILOT` case with `قال الدارقطني ضعيف` and passive `كذبوه`.
- **Comparative and favorable ratings**: e.g., Uthman al-Darimi asking Ibn Ma'in `يونس أحب إليك في الحسن أو حميد ؟ فقال كلاهما`.
- **Nuanced and qualified stances**: e.g., Hammad b. Salamah's praise as an imam qualified by memory decline in old age (`لما كبر ساء حفظه`).
- **Deep nested attributions**: e.g., multi-step isnads through Abu Talib to Ahmad b. Hanbal.
- **Compound and multi-evaluator entries**: e.g., co-occurrence of Malik, Yahya b. Ma'in, and inqita rulings in a single entry.
- **Mixed evaluation and biography**: e.g., memory criticism of Haritha b. Abi al-Rijal mixed with name clarification of his father Abu al-Rijal.
- **Ambiguous targets**: e.g., single-word name `عبد الله`.
- **Pure citation variants**: e.g., unnumbered suffix pairs without prose to test false-positive resistance.

> [!IMPORTANT]
> **Non-Prevalence Declaration**: This 20-case pilot is purposive and stratified. It is designed to test protocol edge cases and boundary conditions. It is **not** a statistically representative random sample of the 18,989 narrators in Shamela4 and must not be used to infer corpus-wide error prevalence.

---

## 3. Blinding and Anti-Leakage Protocol

To ensure unbiased human annotation:
1. **Reviewer Copy Separation**: The reviewer inspects only `PILOT_REVIEWER_BLINDED.csv`.
2. **Suppression of Automated Labels**: All automated classifier labels (`automated_pattern`, `automated_certainty`, `automated_evidence`, `source_ID_level_classification`, `quotation_citation_separability`) and sampling stratum labels are completely removed.
3. **Suppression of Source IDs**: The opaque database `source_id` is omitted from the reviewer file to prevent cross-referencing with unblinded audit files.
4. **Deterministic Shuffling**: Case presentation order is shuffled using fixed seed `{seed}`, producing blinded identifiers `PILOT01` through `PILOT20`.
5. **Internal Key Retention**: The unblinded mapping is strictly quarantined in `PILOT_INTERNAL_MAPPING.csv`.

---

## 4. Annotation Workflow

Annotators must adhere to the following workflow:
1. Read the accompanying [ANNOTATION_CODEBOOK.md](ANNOTATION_CODEBOOK.md) thoroughly before beginning.
2. Open `PILOT_REVIEWER_BLINDED.csv` in a UTF-8 compatible spreadsheet or CSV editor.
3. For each case (`PILOT01` to `PILOT20`):
   - Read `original_field_1` and `original_field_2` alongside `original_tuple_json`.
   - Determine whether the tuple contains an evaluation (`contains_evaluation`).
   - If `no`, mark evaluative fields as `not_applicable` and complete documentary provenance fields.
   - If `yes`, identify the evaluated narrator, historical evaluator, attribution type, verbatim evaluative span, and stance.
   - Record any residual doubt or compound complexity in `unresolved_ambiguity` and `reviewer_notes`.
4. Save the completed file under a new annotated filename (e.g., `PILOT_REVIEWER_ANNOTATED_REVIEWER1.csv`).
5. Never edit the template `PILOT_REVIEWER_BLINDED.csv` directly.

---

## 5. Limitations

- **Sample Size**: $N = 20$ is sufficient to test codebook clarity and annotation feasibility, but cannot estimate overall data quality.
- **Digital Ingestion Artifacts**: Shamela4 tuples reflect digital book extractions whose upstream Lucene/SQLite provenance remains unverified by official documentation.
- **Secondary Citations**: Many classical criticism entries quote earlier authorities through later encyclopedic works (e.g. *Tahdhib al-Tahdhib*, *Lisan al-Mizan*); annotators must carefully separate the historical authority from the immediate compiler.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT, help="Project root directory")
    parser.add_argument("--input-csv", type=Path, default=None, help="Path to input 60-case validation CSV")
    parser.add_argument("--output-dir", type=Path, default=None, help="Directory to write pilot deliverables")
    parser.add_argument("--seed", type=int, default=20261111, help="Sampling seed for deterministic shuffling")
    args = parser.parse_args()

    root = args.root.resolve()
    input_csv = (args.input_csv or root / V3_INPUT_RELATIVE).resolve()
    output_dir = (args.output_dir or root / "data/2_interim/shamela4_narrator_audit/stage2_diagnostics/blinded_annotation_pilot_20").resolve()

    if not input_csv.is_file():
        raise FileNotFoundError(f"Input validation CSV not found: {input_csv}")

    # Verify input integrity against expected hash
    input_hash = sha256(input_csv)
    if input_hash != V3_EXPECTED_HASH:
        raise ValueError(f"Input CSV integrity mismatch: expected {V3_EXPECTED_HASH}, got {input_hash}")

    v3_rows = read_csv(input_csv)
    if len(v3_rows) != 60:
        raise ValueError(f"Expected exactly 60 cases in input, found {len(v3_rows)}")

    # Perform deterministic purposive selection and blinded ID assignment
    selected_cases, stratum_counts = select_pilot_cases(v3_rows, seed=args.seed)
    if len(selected_cases) != 20:
        raise ValueError(f"Expected exactly 20 pilot cases, selected {len(selected_cases)}")

    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. PILOT_SELECTION.csv
    selection_rows = build_selection_rows(selected_cases)
    selection_path = output_dir / "PILOT_SELECTION.csv"
    write_csv(selection_path, selection_rows, SELECTION_FIELDS)

    # 2. PILOT_REVIEWER_BLINDED.csv
    reviewer_rows = build_reviewer_rows(selected_cases)
    reviewer_path = output_dir / "PILOT_REVIEWER_BLINDED.csv"
    write_csv(reviewer_path, reviewer_rows, REVIEWER_FIELDS)

    # 3. PILOT_INTERNAL_MAPPING.csv
    mapping_rows = build_internal_mapping_rows(selected_cases)
    mapping_path = output_dir / "PILOT_INTERNAL_MAPPING.csv"
    write_csv(mapping_path, mapping_rows, MAPPING_FIELDS)

    # 4. ANNOTATION_CODEBOOK.md
    codebook_content = generate_codebook()
    codebook_path = output_dir / "ANNOTATION_CODEBOOK.md"
    codebook_path.write_text(codebook_content, encoding="utf-8")

    # 5. PILOT_PROTOCOL.md
    protocol_content = generate_protocol(stratum_counts, seed=args.seed)
    protocol_path = output_dir / "PILOT_PROTOCOL.md"
    protocol_path.write_text(protocol_content, encoding="utf-8")

    # 6. pilot_manifest.json
    output_files = [
        selection_path,
        reviewer_path,
        mapping_path,
        codebook_path,
        protocol_path,
    ]
    outputs_meta = {
        p.name: {
            "bytes": p.stat().st_size,
            "sha256": sha256(p),
        }
        for p in output_files
    }

    manifest = {
        "version": "1.0.0",
        "description": "Blinded 20-case human manual annotation pilot from Shamela4 tuple validation pool",
        "purposive_sample_declaration": (
            "This 20-case pilot is purposively sampled from the 60-case validation pool to evaluate "
            "codebook clarity, semantic diversity, and annotation feasibility across all six strata. "
            "It is NOT a prevalence-representative or corpus-wide random sample."
        ),
        "execution_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "sampling_seed": args.seed,
        "input_dataset": {
            "path": str(input_csv.relative_to(root)),
            "bytes": input_csv.stat().st_size,
            "sha256": input_hash,
            "total_input_cases": len(v3_rows),
        },
        "selected_case_count": len(selected_cases),
        "stratum_counts": stratum_counts,
        "selected_source_ids": [case["source_id"] for case in selected_cases],
        "selected_pilot_case_ids": [case["pilot_case_id"] for case in selected_cases],
        "outputs": outputs_meta,
    }

    manifest_path = output_dir / "pilot_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "status": "success",
        "output_directory": str(output_dir),
        "selected_count": len(selected_cases),
        "unique_source_ids": len(set(case["source_id"] for case in selected_cases)),
        "strata_breakdown": stratum_counts,
        "pilot_case_ids": [case["pilot_case_id"] for case in selected_cases],
    }, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
