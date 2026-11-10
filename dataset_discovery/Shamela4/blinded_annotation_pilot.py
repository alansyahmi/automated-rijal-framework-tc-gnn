#!/usr/bin/env python3
"""Reproducible generation of Shamela4 20-case blinded human annotation pilot.

Integrity-hardened architecture (v2.5.0):
1. Strict Pass 1 Blinding:
   - Exposes only the two textual tuple elements in original_tuple_json (purges 3rd source-ID element).
   - Strictly omits attached narrator metadata (narrator_id, narrator_name), source_id,
     v3_case_id, automated classifier labels, and stratum labels.
2. Separated Textual Mentions & Documentary Provenance:
   - Pass 1 records visible work-title/locator mentions and their textual roles only.
   - Independent documentary provenance is handled in a separate blank reconciliation template.
   - No title in tuple text is assumed to be the immediate extraction source.
3. Explicit Claim Target:
   - Distinguishes the entity or aspect a statement concerns (narrator_overall, memory_or_precision,
     specific_transmission_link, specific_hadith_or_report, comparative_narrator_assessment,
     narrator_identity_or_biography, not_applicable, unclear) from the claim subject, function, and stance.
4. Claim-Level Unit:
   - Each row represents one distinct proposition, factual or evaluative; contains_evaluation determines whether it is evaluative.
5. Clarified Qualitative Appraisal vs Factual Transmission Observations:
   - contains_evaluation distinguishes qualitative appraisals (yes) from factual/descriptive/documentary
     observations (no) or ambiguous claims (unclear).
   - Factual transmission disconnects (inqita, nafy al-sama) can have contains_evaluation = no.
6. Correct Comparative-Preference Guidance:
   - Comparative preference statements allow neutral or unclear orientation; annotators must
     not infer that both narrators are independently reliable merely from responses like 'كلاهما'.
7. Quarantined Full Provenance:
   - Full 3-element tuple [field_1, field_2, source_id] preserved in PILOT_INTERNAL_MAPPING.csv.
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

# Pass 1: Text-only context fields (strictly excluding attached narrator metadata, source_id, and classifier labels)
PASS1_TEXT_FIELDS = [
    "pilot_case_id",
    "entry_index",
    "original_field_1",
    "original_field_2",
    "original_tuple_json",
]

# Claim-level annotation fields (Integrity-audited schema v2.5.0)
CLAIM_FIELDS = [
    # Linking identifiers
    "pilot_case_id",
    "claim_id",
    # Claim subject
    "claim_subject_as_written",
    "claim_subject_identity_confidence",
    # Claim function, evaluation status, target & stance
    "contains_evaluation",
    "claim_target",
    "statement_function",
    "evaluative_orientation",
    "evaluative_span_verbatim",
    "qualification_or_context",
    # Textual mentions only; documentary source identity is reconciled separately.
    "work_title_as_written",
    "work_role",
    "source_locator_as_written",
    # Historical attribution & transmitters
    "historical_evaluator_as_written",
    "historical_evaluator_normalized",
    "intermediate_transmitter_as_written",
    "other_quoted_speaker_as_written",
    "attribution_type",
    "attribution_evidence_verbatim",
    # Quality & notes
    "transcription_confidence",
    "interpretation_confidence",
    "unresolved_ambiguity",
    "reviewer_notes",
]

# Allowed claim-target vocabulary; this defines categories but does not classify records.
CLAIM_TARGET_CATEGORIES = [
    "narrator_overall",
    "memory_or_precision",
    "narrator_identity_or_biography",
    "specific_transmission_link",
    "specific_hadith_or_report",
    "comparative_narrator_assessment",
    "not_applicable",
    "unclear",
]

# Separate post-Pass-1 documentary provenance reconciliation; no values are prefilled.
PROVENANCE_RECONCILIATION_FIELDS = [
    "pilot_case_id",
    "documentary_source_work_title",
    "documentary_source_work_identifier",
    "documentary_evidence_reference",
    "provenance_status",
    "provenance_confidence",
    "reviewer_notes",
]

DEFAULT_OUTPUT_RELATIVE = "data/2_interim/shamela4_narrator_audit/stage2_diagnostics/blinded_annotation_pilot_20_v2_5"

# Pass 2: Identity reconciliation fields
PASS2_RECONCILIATION_FIELDS = [
    "pilot_case_id",
    "claim_id",
    "attached_narrator_id",
    "attached_narrator_name",
    "claim_subject_as_written",
    "entry_index",
    "original_field_1",
    "original_field_2",
    "claim_subject_matches_attached_narrator",
    "reconciliation_status",
    "reconciled_narrator_id",
    "reconciliation_confidence",
    "reconciliation_notes",
]

MAPPING_FIELDS = [
    "pilot_case_id",
    "v3_case_id",
    "source_id",
    "narrator_id",
    "narrator_name",
    "group_label",
    "entry_index",
    "original_tuple_3element_json",
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


def build_pass1_text_rows(selected_cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build Pass 1 text-only context rows strictly excluding attached narrator metadata and source_id.
    
    The original_tuple_json exposes ONLY the two textual elements [field_1, field_2], completely
    purging the 3rd source-ID integer to ensure strict blinding.
    """
    pass1_rows = []
    for case in selected_cases:
        # Create sanitized 2-element textual tuple JSON
        safe_2element_tuple = [case["original_field_1"], case["original_field_2"]]
        pass1_rows.append({
            "pilot_case_id": case["pilot_case_id"],
            "entry_index": case["entry_index"],
            "original_field_1": case["original_field_1"],
            "original_field_2": case["original_field_2"],
            "original_tuple_json": json.dumps(safe_2element_tuple, ensure_ascii=False),
        })
    return pass1_rows


def build_claim_blank_rows(selected_cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build claim-level blank template with one extendable starter row per tuple."""
    claim_rows = []
    for case in selected_cases:
        row = {
            "pilot_case_id": case["pilot_case_id"],
            "claim_id": f"{case['pilot_case_id']}_C01",
        }
        for field in CLAIM_FIELDS:
            if field not in row:
                row[field] = ""
        claim_rows.append(row)
    return claim_rows


def build_provenance_reconciliation_rows(selected_cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build a separate blank template for documentary provenance checks after Pass 1."""
    return [
        {field: (case["pilot_case_id"] if field == "pilot_case_id" else "")
         for field in PROVENANCE_RECONCILIATION_FIELDS}
        for case in selected_cases
    ]


def build_pass2_reconciliation_rows(selected_cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build Pass 2 starter rows for claim-level identity reconciliation."""
    pass2_rows = []
    for case in selected_cases:
        pass2_rows.append({
            "pilot_case_id": case["pilot_case_id"],
            "claim_id": f"{case['pilot_case_id']}_C01",
            "attached_narrator_id": case["narrator_id"],
            "attached_narrator_name": case["narrator_name"],
            "claim_subject_as_written": "",
            "entry_index": case["entry_index"],
            "original_field_1": case["original_field_1"],
            "original_field_2": case["original_field_2"],
            "claim_subject_matches_attached_narrator": "",
            "reconciliation_status": "",
            "reconciled_narrator_id": "",
            "reconciliation_confidence": "",
            "reconciliation_notes": "",
        })
    return pass2_rows


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
            "original_tuple_3element_json": case["original_tuple_json"],
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
    return """# Shamela4 Narrator Criticism Annotation Codebook (Claim-Level & Two-Pass Design)

## 1. Research Context and Purpose

This codebook provides instructions for human annotators validating narrator criticism (`garh`) entries extracted from the Shamela4 database (`narrators.parquet`).

The objective is to establish the ground-truth interpretation of criticism tuples before any automated classification rules, representation models (such as AraBERT), or Graph Neural Networks (GNNs) are trained.

### Core Safeguards
1. **Zero Fabrication**: Never guess or invent an attribution, stance, or date not justified by the verbatim text.
2. **Preserve Verbatim Text**: Never normalize or edit Arabic quotations in verbatim fields.
3. **No Group Label Conflation**: Do not assume the database `group_label` (e.g. `البخاري`, `الدارقطني`) is the historical evaluator. Many entries transmit quotes from other scholars.
4. **No Forced Binary Sentiment**: Do not force descriptive transmission observations or nuanced qualifications into binary positive or negative categories. Factual transmission disconnect (*inqita'*) or hadith-level rejection must not be silently converted into general narrator unreliability.
5. **Separation of Entities**: Keep historical speaker attribution, intermediate transmission, source work authorship, narrator identity, and evaluative stance strictly distinct.
6. **Separate Textual Mentions from Documentary Provenance**: Pass 1 records only visible work-title mentions, locators, and their textual roles. It does not identify the extraction source. Documentary provenance is recorded in the separate `PILOT_PROVENANCE_RECONCILIATION_BLANK.csv`; absent documentary evidence remains `unresolved`.

---

## 2. Unit of Analysis: Claim-Level Records

A single criticism tuple consists of two text fields (`field_1`, `field_2`) and an opaque `source_id`.
- **Core Principle**: A tuple may express multiple distinct propositions, including factual biography, transmission observations, evaluations, reports, or nested attributions. Different claims in one tuple may have different subjects.
- **Record Structure**: Annotations are recorded in `PILOT_CLAIMS_BLANK.csv`. Each row represents **one distinct claim**, whether factual or evaluative, and links to its tuple via `pilot_case_id`.
- **Multiple Claims per Tuple**:
  - The starter row uses `{pilot_case_id}_C01`.
  - Add a separate row for each additional distinct claim, using `{pilot_case_id}_C02`, `{pilot_case_id}_C03`, and so on.
  - `contains_evaluation` determines whether a claim is evaluative; factual claims remain in the table and do not contribute to evaluative analysis.
  - Do not combine claims only because they concern the same narrator or occur in the same tuple. Do not assume every claim concerns the database-attached narrator.
- **Non-Evaluative Entries**: If a tuple contains only bibliographic citations, book numbers, or hadith locators without human evaluative prose, annotate a single row with `contains_evaluation = no`, an appropriate `claim_target` (usually `not_applicable` for a pure citation), `statement_function = documentary_citation`, and `evaluative_orientation = not_applicable`.

---

## 3. Two-Pass Blinding Protocol

To eliminate confirmation bias and prevent metadata contamination, annotation proceeds in two strictly decoupled stages:

### Pass 1: Blinded Text-Only Extraction
1. The annotator opens `PILOT_PASS1_TEXT_BLINDED.csv` and `PILOT_CLAIMS_BLANK.csv`.
2. `PILOT_PASS1_TEXT_BLINDED.csv` exposes **only**:
   - `pilot_case_id`
   - `entry_index`
   - `original_field_1`
   - `original_field_2`
   - `original_tuple_json` (sanitized 2-element array `[field_1, field_2]` with no source ID).
3. The annotator **does not see** the database-attached `narrator_id`, `narrator_name`, or `source_id`.
4. Based solely on the verbatim Arabic text, the annotator records visible textual mentions and roles, not external provenance:
   - Claim subject as written, which may differ across claims in the same tuple.
   - Work titles and locators appearing in the passage, with textual role (`cited_work`, `other_referenced_work`, or `unclear`).
   - Historical evaluator and intermediate transmitter only when explicitly represented in the text.
   - Statement function, whether a qualitative evaluation is present, claim target, and orientation.
   - Verbatim claim span, quotation boundary, and citation boundary where identifiable.
5. Do not infer which work the database extracted from. Documentary verification happens separately in `PILOT_PROVENANCE_RECONCILIATION_BLANK.csv`, after Pass 1; unresolved evidence stays unresolved.

### Pass 2: Attached Identity Reconciliation
1. After completing Pass 1, the annotator opens `PILOT_PASS2_RECONCILIATION_BLANK.csv`.
2. This template reveals `attached_narrator_id` and `attached_narrator_name` alongside the text.
3. Create one Pass 2 row for every claim in the frozen Pass 1 table, preserving its `claim_id` and copying `claim_subject_as_written` from that claim row. The generated C01 row is a starter; add rows for C02, C03, etc. where needed.
4. Reconcile each claim subject separately against the attached narrator. A tuple may contain claims about multiple people, so the attachment must not be assigned as the subject of every claim.

---

## 4. Claim-Level Schema and Field Definitions (`PILOT_CLAIMS_BLANK.csv`)

### Identifiers
- `pilot_case_id`: Blinded identifier linking to Pass 1 tuple context (e.g. `PILOT01` to `PILOT20`).
- `claim_id`: Unique identifier for a claim, whether factual or evaluative (e.g. `PILOT01_C01`, `PILOT01_C02`).

### Section A: Claim Subject
- `claim_subject_as_written`:
  - **Definition**: Verbatim Arabic name of the person or entity that is the subject of this specific claim, whether or not the claim evaluates them.
  - **Allowed Values**: Exact Arabic string or description from the text, or `[غير مصرح به]` for an unnamed/implicit subject. A report or route may be recorded as the textual subject where appropriate.
  - **Examples**: `معارك بن عباد العبدي`, `أبو جابر البياضي`, `حارثة`.
- `claim_subject_identity_confidence`:
  - **Definition**: Confidence that the text refers to the identified individual as the claim subject.
  - **Allowed Values**: `high`, `medium`, `low`, `unresolved`.

### Section B: Textual Mentions and Attribution
Pass 1 annotates textual mentions and roles only. It does not establish the extraction source, compiler identity, or external documentary provenance.
- `work_title_as_written`:
  - **Definition**: Verbatim title of a work explicitly appearing in the tuple text.
  - **Allowed Values**: Exact Arabic text, `none`, or `unclear`; do not infer a title from the database group or source ID.
- `work_role`:
  - **Definition**: The role the text itself assigns to the mentioned work.
  - **Allowed Values**:
    - `cited_work`: A separate work quoted or cited inside the passage.
    - `other_referenced_work`: A work mentioned in passing as comparison or cross-reference.
    - `unclear`: Ambiguous role that cannot be determined with certainty from text.
- `source_locator_as_written`:
  - **Definition**: Verbatim volume, page, or hadith number string (e.g. `(1/ 23) برقم: (81)`, `(12/ 362) (بدون ترقيم)`).
- Documentary provenance reconciliation is a separate post-Pass-1 task. Use `PILOT_PROVENANCE_RECONCILIATION_BLANK.csv` to record a candidate extraction work, documentary identifier/evidence, status (`verified`, `contradicted`, or `unresolved`), confidence, and notes. Do not populate it from tuple text alone; unresolved remains an acceptable outcome.
- `historical_evaluator_as_written`:
  - **Definition**: Verbatim name of the critic whose judgment is reported.
  - **Allowed Values**: Exact Arabic string from text (e.g., `أحمد بن حنبل`, `مالك بن أنس`, `يحيى بن معين`), or `[المصنف]` (if spoken directly by compiler without attribution), or `[مجهول/صيغة تمريض]` (for passive/collective verbs like `كذبوه`).
  - **Rule**: Do NOT infer the historical evaluator from the database group label without explicit textual attribution.
- `historical_evaluator_normalized`:
  - **Definition**: Standardized classical Arabic scholarly name.
  - **Allowed Values**: Canonical name (e.g., `أحمد بن حنبل`, `يحيى بن معين`, `الدارقطني`, `علي بن المديني`, `ابن حجر العسقلاني`, `مجهول/غير محدد`).
- `intermediate_transmitter_as_written`:
  - **Definition**: Name of the intermediate reporter conveying the statement.
  - **Allowed Values**: Verbatim Arabic name (e.g., `عثمان الدارمي`, `أبو طالب`, `عبد الله بن أحمد`), `none`, or `unclear`.
- `other_quoted_speaker_as_written`:
  - **Definition**: Other secondary speakers, isnad authorities, or interlocutors quoted in the passage.
  - **Allowed Values**: Verbatim Arabic names (e.g., `سفيان الثوري`, `شعبة`), `none`, or `unclear`.
- `attribution_type`:
  - **Definition**: Nature of speech attribution.
  - **Allowed Values**:
    - `direct`: The author speaks directly without reporting chain (e.g., `قلت: ...`, `لا نعرفه إلا من هذا الوجه`).
    - `transmitted`: Quoting another scholar with an explicit reporting verb (e.g., `قال أحمد: ضعيف`, `سألت يحيى بن معين فقال...`).
    - `paraphrased`: Summary or loose restatement of another critic's opinion without verbatim claim.
    - `nested_attribution`: Reporting an evaluation through an explicit isnad chain of two or more links (e.g., `حدثنا فلان قال نا فلان قال سمعت أبا طالب قال قال أحمد...`).
    - `unclear`: Passive or ambiguous attribution without explicit agent (e.g., `كذبوه`, `تكلم فيه`).
    - `not_applicable`: When `contains_evaluation = no`.
- `attribution_evidence_verbatim`:
  - **Definition**: The exact Arabic phrase demonstrating attribution (e.g., `قال أحمد بن حنبل`, `حدثنا عبد الرحمن نا محمد... سمعت أبا طالب قال قال أحمد`, `كان يحيى بن معين يقول`).

### Section C: Evaluative Content, Target, Function, and Orientation
Annotators must rigorously separate:
1. `contains_evaluation` (whether this claim is an appraisal or a factual proposition)
2. `claim_target` (the entity or aspect the claim concerns, whether factual or evaluative)
3. `statement_function` (the claim's function in context)
4. `evaluative_orientation` (qualitative stance/valence only when `contains_evaluation = yes`)

- `contains_evaluation`:
  - **Definition**: Does this specific claim contain a qualitative appraisal of a narrator, transmission link, or report? Explicitly distinguishes qualitative appraisal from factual, descriptive, or documentary observations.
  - **Allowed Values**:
    - `yes`: A qualitative appraisal is made (evaluating narrator reliability, character, memory retention, or hadith validity).
    - `no`: The statement is factual, descriptive, biographical, or documentary without qualitative appraisal.
    - `unclear`: The distinction between qualitative appraisal and factual observation cannot be established confidently.
  - **Mandatory Guidance**: A `transmission_observation` does **not** automatically imply `contains_evaluation = yes`. For example, `لم يسمع من عنبسة شيئا` is a factual observation of isnad disconnection (*inqita'*), not a qualitative evaluation of the narrator's character or trustworthiness (`contains_evaluation = no`).
- `claim_target`:
  - **Definition**: The entity or aspect that the claim is about. It is distinct from the claim subject (`claim_subject_as_written`), the function (`statement_function`), and the orientation (`evaluative_orientation`). This field applies to factual claims as well as appraisals.
  - **Allowed Values**:
    - `narrator_overall`: General moral integrity, religious reliability, truthfulness, or foundational trustworthiness of the narrator (e.g. `ثقة`, `كذاب`, `متروك`, `ضعيف`, `لا يحتج به`).
    - `memory_or_precision`: Cognitive retention, book precision, senility/confusion in old age, or accuracy in specific contexts (e.g. `ساء حفظه لما كبر`, `فيه لين`, `تكلم فيه من قبل حفظه`).
    - `narrator_identity_or_biography`: Factual identity, naming, lineage, or biographical information about a narrator (e.g. `أبو الرجال اسمه محمد`). This target does not imply a qualitative evaluation.
    - `specific_transmission_link`: Specific isnad audition (*sama'*), meeting (*liqā'*), generational non-contiguity (*inqita'*), or teacher-student transmission link (e.g. `لم يسمع من فلان`, `تفرد به فلان عن فلان`, `لم يدرك النبي صلى الله عليه وسلم`).
    - `specific_hadith_or_report`: Assessment directed at a specific narration, matn, or particular hadith wording rather than general narrator character (e.g. `هذا لا يثبت`, `لا يصح عن الزهري`, `حديث منكر`).
    - `comparative_narrator_assessment`: Relational evaluation or relative standing between two or more narrators (e.g. `يونس أحب إليك في الحسن أو حميد ؟ فقال كلاهما`).
    - `not_applicable`: `not_applicable` is reserved for claims with no identifiable subject, such as a standalone bibliographic citation or locator.
    - `unclear`: When the evaluation target cannot be established with confidence.
- `statement_function`:
  - **Definition**: What function is the statement performing in classical *hadith* scholarship?
  - **Allowed Values**:
    - `narrator_appraisal`: General moral, religious, or foundational reliability verdict on a narrator (e.g., `ثقة`, `كذاب`, `متروك`, `لا يحتج به`).
    - `memory_or_precision_observation`: Specific assessment of cognitive retention, book-keeping, or senility (e.g., `ساء حفظه`, `فيه لين`, `يخلط`, `تكلم فيه من قبل حفظه`).
    - `transmission_observation`: Descriptive observation of hearing, meeting, generational contiguity, or singularity (e.g., `لم يسمع من فلان`, `لم يدرك النبي صلى الله عليه وسلم`, `تفرد به فلان`, `مرسل`, `منقطع`).
    - `hadith_or_report_appraisal`: Assessment directed at a specific text or narration rather than general narrator character (e.g., `هذا حديث لا يثبت`, `لا يصح عن الزهري`, `حديث منكر`).
    - `comparative_preference`: Inquiring or ranking relative standing between two or more transmitters (e.g., `أحب إليك... فقال كلاهما`).
    - `biographical_description`: Factual biographical remark (e.g., birth, death, residence, identity clarification like `أبو الرجال اسمه محمد`).
    - `legal_or_other_commentary`: Juristic deduction or topical discussion not evaluating transmission.
    - `documentary_citation`: Pure book title, chapter, or locator notation.
    - `unclear`: Ambiguous function that cannot be determined with certainty.
- `evaluative_orientation`:
  - **Definition**: The qualitative orientation/valence of an actual evaluative claim. Use `not_applicable` when the claim is factual or documentary and contains no qualitative appraisal; neutral is reserved for an actual evaluation whose orientation is genuinely non-directional.
  - **Allowed Values**:
    - `positive`: Explicit praise or favorable validation (e.g., `ثقة`, `صدوق`, `حجة`).
    - `negative`: Explicit criticism or disparagement (e.g., `ضعيف`, `كذاب`, `متروك`, `كذبوه`).
    - `mixed`: Co-presence of praise and criticism in the same claim (e.g., `هو أحد أئمة المسلمين إلا أنه لما كبر ساء حفظه`).
    - `qualified`: Restricted validity or conditional acceptance (e.g., reliable in a specific teacher, but weak in others; or `ليس بالقوي`).
    - `neutral`: An actual evaluative comparison or appraisal that conveys no clear positive or negative direction.
    - `unclear`: Ambiguous orientation.
    - `not_applicable`: When `contains_evaluation = no`.

#### Contextual Interpretation Guidelines:
1. **`تفرد به` (Singularity of Transmission)**:
   - `statement_function`: `transmission_observation`
   - `claim_target`: `specific_transmission_link`
   - `contains_evaluation`: `no` if it is a bare factual singularity observation; `yes` only if context adds qualitative appraisal; otherwise `unclear`.
   - `evaluative_orientation`: `not_applicable` for factual observation; `neutral`, `qualified`, or another orientation only if an actual evaluation is present. Do NOT automatically classify as `negative`.
2. **`لا أعرفه` (Non-Recognition)**:
   - `statement_function`: `narrator_appraisal` or `transmission_observation`
   - `claim_target`: `narrator_overall` or `specific_transmission_link`
   - `evaluative_orientation`: use `not_applicable` if it is a factual observation with `contains_evaluation = no`; otherwise use `neutral`, `qualified`, or `negative` according to context. Do not treat as a formal grade of deliberate weakness without context.
3. **`أحب إليك... فقال كلاهما` (Comparative Preference)**:
   - `statement_function`: `comparative_preference`
   - `claim_target`: `comparative_narrator_assessment`
   - `contains_evaluation`: `yes` only if the comparison expresses a relative appraisal; use `unclear` if the text does not establish this.
   - `evaluative_orientation`: `neutral` or `unclear` (or `positive`/`qualified` only if context explicitly establishes praise). Do **not** infer that both narrators are independently reliable merely because the response is `كلاهما`.
4. **`لم يسمع من فلان` (Transmission Disconnect)**:
   - `contains_evaluation`: `no` (when stating factual non-audition without qualitative moral/memory appraisal).
   - `statement_function`: `transmission_observation`
   - `claim_target`: `specific_transmission_link`
   - `evaluative_orientation`: `not_applicable` when the statement is factual (`contains_evaluation = no`). It establishes *inqita'* (lack of direct hearing), not moral unreliability or fabrication.
5. **`لا يصح عن الزهري` (Narration Invalidation)**:
   - `contains_evaluation`: `yes`
   - `statement_function`: `hadith_or_report_appraisal`
   - `claim_target`: `specific_hadith_or_report`
   - `evaluative_orientation`: `negative` (directed at the hadith, not necessarily narrator unreliability).

#### Inter-Field Relationship and Examples Matrix
| Arabic Statement | `contains_evaluation` | `claim_target` | `statement_function` | `evaluative_orientation` | Contextual Explanation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `أبو جابر البياضي كذاب` | `yes` | `narrator_overall` | `narrator_appraisal` | `negative` | Direct qualitative impugnment of narrator truthfulness. |
| `عمرو بن شعيب ثقة` | `yes` | `narrator_overall` | `narrator_appraisal` | `positive` | Direct qualitative validation of foundational reliability. |
| `تكلم فيه من قبل حفظه` | `yes` | `memory_or_precision` | `memory_or_precision_observation` | `negative` | Qualitative evaluation targeted specifically at memory retention. |
| `لما كبر ساء حفظه` | `yes` | `memory_or_precision` | `memory_or_precision_observation` | `qualified` | Qualified appraisal: reliable earlier, cognitive impairment in old age. |
| `مكحول لم يسمع من عنبسة شيئا` | `no` | `specific_transmission_link` | `transmission_observation` | `not_applicable` | Factual observation of isnad disconnection (*inqita'*); no qualitative appraisal. |
| `عامر بن مسعود لم يدرك النبي` | `no` | `specific_transmission_link` | `transmission_observation` | `not_applicable` | Factual historical/generational statement of non-contiguity. |
| `تفرد به عبد العزيز...` | `no` | `specific_transmission_link` | `transmission_observation` | `not_applicable` | Bare factual singularity observation; surrounding context may add an appraisal, which should be recorded as a separate claim. |
| `هذا حديث لا يثبت` | `yes` | `specific_hadith_or_report` | `hadith_or_report_appraisal` | `negative` | Qualitative invalidation directed at specific hadith text, not general narrator character. |
| `أحب إليك... فقال كلاهما` | `yes` | `comparative_narrator_assessment` | `comparative_preference` | `neutral` | Relative preference query; responding `كلاهما` does not imply independent unconditional reliability. |
| `سنن البيهقي الكبرى: (3/ 176)` | `no` | `not_applicable` | `documentary_citation` | `not_applicable` | Pure bibliographic book locator; zero evaluative content. |
| `أبو الرجال اسمه محمد` | `no` | `narrator_identity_or_biography` | `biographical_description` | `not_applicable` | Factual identity claim about Abu al-Rijal; an identifiable subject is present, but no qualitative evaluation is made. |

- `evaluative_span_verbatim`: Exact verbatim Arabic substring containing the evaluative judgement (or blank if none).
- `qualification_or_context`: Specific contextual limitation (e.g., `في حفظه لا في عدالته`, `لما كبر في السن`, `عن عطاء خاصة`), or `none`.

### Section D: Quality & Notes
- `transcription_confidence`: `high`, `medium`, `low`, `unresolved`.
- `interpretation_confidence`: `high`, `medium`, `low`, `unresolved`.
- `unresolved_ambiguity`: Description of competing interpretations, or `none`.
- `reviewer_notes`: Free-text observations, anomalies, or historical context.

---

## 5. Pass 2 Schema and Field Definitions (`PILOT_PASS2_RECONCILIATION_BLANK.csv`)

- `pilot_case_id`: Blinded identifier linking to the tuple in Pass 1.
- `claim_id`: Claim identifier copied from the frozen Pass 1 claim table. Start with `{{pilot_case_id}}_C01`; add a row for every additional claim after Pass 1 is frozen.
- `attached_narrator_id`: Numeric ID of the narrator to whom the tuple was attached in `narrators.parquet`.
- `attached_narrator_name`: Short name of the narrator from the database.
- `claim_subject_as_written`: Copy the subject from the matching frozen Pass 1 claim row; do not infer it from the attached narrator.
- `entry_index`, `original_field_1`, `original_field_2`: Verbatim text retained for review.
- `claim_subject_matches_attached_narrator`:
  - `exact_match`: The claim subject in Pass 1 is unambiguously the attached narrator.
  - `different_person`: The claim concerns another person (e.g., father, teacher, or narrator partner).
    - `multiple_narrators_as_subject`: This claim concerns multiple narrators.
  - `no_narrator_subject`: The claim concerns a report or is a pure documentary citation.
  - `unresolved`: Textual ambiguity prevents conclusive determination.
- `reconciliation_status`:
  - `confirmed_target`: Verified correct database attachment.
  - `false_attachment_in_database`: This claim is about a different subject; this alone does not establish that the tuple is incorrectly attached if another claim in the tuple concerns the attached narrator.
  - `isnad_partner_evaluated`: This claim concerns another link in the transmission chain.
  - `contextual_mention_only`: Attached narrator is mentioned only as a background reference.
  - `unclear`: Unresolved relationship.
- `reconciled_narrator_id`: Confirmed narrator ID if resolved, or blank if external/unlinked.
- `reconciliation_confidence`: `high`, `medium`, `low`, `unresolved`.
- `reconciliation_notes`: Free-text explanation of how the attached identity relates to the passage.

### Multi-Claim Unit Example
A tuple may contain a report comment, a narrator memory appraisal, and a factual identity statement. Record each as its own claim row, with its own subject and target. If a clause's target or evaluative force cannot be resolved from context, preserve that uncertainty rather than borrowing the subject or interpretation from an adjacent clause. The database-attached narrator identifies the tuple's attachment only; it does not determine each claim's subject.
"""


def generate_protocol(stratum_counts: dict[str, int], seed: int) -> str:
    """Generate the Markdown protocol document for the pilot study."""
    strata_lines = "\n".join(f"- `{stratum}`: {count} cases" for stratum, count in stratum_counts.items())
    return f"""# Shamela4 20-Case Blinded Manual Annotation Pilot Protocol (Two-Pass & Claim-Level)

## 1. Objectives

This pilot study evaluates the feasibility, clarity, and precision of the human annotation codebook on a purposive sample of 20 criticism tuples extracted from Shamela4.

Specific research questions investigated by this pilot:
1. **Evaluative Content vs Factual Transmission**: Can annotators reliably distinguish between genuine qualitative appraisals (`contains_evaluation=yes`), factual transmission observations (`contains_evaluation=no` like `لم يسمع`), hadith rulings, and pure documentary citations?
2. **Claim-Level Granularity**: Can tuples containing multiple propositions, including factual claims, be decomposed into distinct claim records with claim-specific subjects?
3. **Explicit Claim Target**: Can annotators identify what a factual or evaluative claim concerns (`claim_target`) separately from the person named, statement function, and orientation?
4. **Textual Mentions vs Documentary Provenance**: Can annotators record visible work-title/locator mentions and textual roles without inferring the extraction source? External provenance checks are recorded separately and may remain unresolved.
5. **Statement Function vs Orientation**: Can functional categories be separated from orientation, using `not_applicable` for factual claims with no appraisal and reserving `neutral` for actual non-directional evaluations?
6. **Attribution Type**: Can direct statements, nested isnads, and passive consensus phrases (`كذبوه`) be systematically differentiated?
7. **Blinded Reconciliation**: For each Pass 1 claim, does the database-attached narrator match that claim's subject when reconciled only after Pass 1 is frozen?
8. **Automated Concordance**: Do existing automated heuristic patterns align with human semantic understanding? This is a tuple-interpretation comparison only, not historical attribution or narrator reliability validation.

---

## 2. Sampling Design and Rationale

The 20 cases are purposively drawn from the frozen 60-case sample (`TUPLE_MANUAL_VALIDATION.csv` in `forensic_verification_v3`).

### Stratification Representation
All six validation strata are represented in the pilot:
{strata_lines}

### Purposive Selection Criteria
Cases were selected to maximize semantic, structural, and grammatical diversity:
- **Short formulaic negative evaluations**: e.g., `PILOT19` (`TV012`: `قال الدارقطني ضعيف`) and `PILOT17` (`TV018`: passive `كذبوه`).
- **Comparative and favorable ratings**: e.g., `PILOT04` (`TV053`: Uthman al-Darimi asking Ibn Ma'in `يونس أحب إليك في الحسن أو حميد ؟ فقال كلاهما`).
- **Nuanced and qualified stances**: e.g., `PILOT05` (`TV052`: Hammad b. Salamah praised as an imam but qualified by late-life memory decline `لما كبر ساء حفظه`).
- **Deep nested attributions**: e.g., `PILOT02` (`TV014`: 4-link isnad through Abu Talib to Ahmad b. Hanbal).
- **Compound and multi-evaluator entries**: e.g., `PILOT01` (`TV022`: co-occurrence of inqita, Malik, and Yahya b. Ma'in in one entry).
- **Mixed evaluation and biography**: e.g., `PILOT10` (`TV038`: memory criticism of Haritha mixed with name clarification of his father Abu al-Rijal).
- **Ambiguous targets**: e.g., `PILOT20` (`TV043`: single-word common name `عبد الله`).
- **Pure citation variants**: e.g., `PILOT08`, `PILOT11`, `PILOT13` (unnumbered suffix pairs without prose to test false-positive resistance).

> [!IMPORTANT]
> **Non-Prevalence Declaration**: This 20-case pilot is purposive and stratified. It is designed to test protocol edge cases and boundary conditions. It is **not** a statistically representative random sample of the 18,989 narrators in Shamela4 and must not be used to infer corpus-wide error prevalence.

---

## 3. Two-Pass Blinding Architecture

To prevent metadata leakage and confirmation bias:
1. **Pass 1 (Text-Only Inspection)**:
   - Annotator reads `PILOT_PASS1_TEXT_BLINDED.csv`.
   - Attached narrator metadata (`narrator_id`, `narrator_name`) is **completely absent**.
   - Database `source_id` is completely purged from all fields and tuple elements (`original_tuple_json` is strictly a 2-element array `[field_1, field_2]`).
   - Automated classifier labels and sampling strata are **strictly excluded**.
   - Annotations are recorded in `PILOT_CLAIMS_BLANK.csv`.
   - All distinct factual and evaluative claims are recorded as separate rows sharing `pilot_case_id` with incremented `claim_id`.
2. **Pass 2 (Identity Reconciliation)**:
   - After completing Pass 1, annotator opens `PILOT_PASS2_RECONCILIATION_BLANK.csv`.
   - Attached narrator metadata (`attached_narrator_id`, `attached_narrator_name`) is revealed alongside the original text.
   - Annotator reconciles the attached narrator separately against each frozen claim subject, not against the tuple as a single undivided unit.
   - Automated classifier labels and source IDs remain strictly blinded.

---

## 4. Multi-Claim Recording Instructions

Annotators must adhere to this rule: **One distinct claim per row, whether factual or evaluative**.
- An initial template row `{{pilot_case_id}}_C01` is provided for each pilot case.
- When an entry contains several claims (e.g. it combines transmission commentary, a narrator appraisal, and factual biography):
  1. Insert a new row directly beneath the primary row.
  2. Set `pilot_case_id` to the parent case ID (e.g. `PILOT01`).
  3. Set `claim_id` to `{{pilot_case_id}}_C02` (then `_C03`, etc.).
  4. Record that claim's subject, target, function, evaluation status, attribution, and orientation where applicable.
- `evaluative_orientation` does not apply to claims marked `contains_evaluation = no`. Keep all distinct claims; use `contains_evaluation` to identify which claims are evaluative.
- There is no arbitrary maximum number of claim rows.

---

## 5. Limitations

- **Sample Size**: $N = 20$ evaluates codebook clarity and annotation feasibility, but cannot estimate overall corpus error rates.
- **Research Boundary**: This protocol tests tuple interpretation. It cannot establish historical attribution accuracy, original speaker identity, narrator reliability, or the number of independent historical evaluations. Agreement on field roles or boundaries is not evidence for those separate claims.
- **Pilot Scope**: Twenty cases support feasibility and protocol refinement only; they are insufficient to establish robust corpus-wide annotation reliability or error rates.
- **Independent Review**: Two Arabic-competent reviewers should annotate independently; a third reviewer should adjudicate difficult cases after both first-pass records are frozen. Report agreement separately for claim/field roles, quotation/citation boundaries, and automated-pattern correspondence. Describe disagreements by Arabic construction and formatting.
- **Documentary Provenance**: Tuple text alone does not resolve the entity represented by the integer source ID. Work/record identity remains unresolved until documentary evidence is reviewed.
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
    output_dir = (args.output_dir or root / DEFAULT_OUTPUT_RELATIVE).resolve()

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

    # 2. PILOT_INTERNAL_MAPPING.csv (preserves 3-element tuple in quarantined artifact)
    mapping_rows = build_internal_mapping_rows(selected_cases)
    mapping_path = output_dir / "PILOT_INTERNAL_MAPPING.csv"
    write_csv(mapping_path, mapping_rows, MAPPING_FIELDS)

    # 3. PILOT_PASS1_TEXT_BLINDED.csv (Pass 1 text-only context, NO narrator metadata, NO source_id in tuple)
    pass1_rows = build_pass1_text_rows(selected_cases)
    pass1_path = output_dir / "PILOT_PASS1_TEXT_BLINDED.csv"
    write_csv(pass1_path, pass1_rows, PASS1_TEXT_FIELDS)

    # 4. PILOT_CLAIMS_BLANK.csv (claim-level blank template)
    claim_rows = build_claim_blank_rows(selected_cases)
    claims_path = output_dir / "PILOT_CLAIMS_BLANK.csv"
    write_csv(claims_path, claim_rows, CLAIM_FIELDS)

    # 5. Separate documentary provenance reconciliation, populated only after blinded text review
    provenance_rows = build_provenance_reconciliation_rows(selected_cases)
    provenance_path = output_dir / "PILOT_PROVENANCE_RECONCILIATION_BLANK.csv"
    write_csv(provenance_path, provenance_rows, PROVENANCE_RECONCILIATION_FIELDS)

    # 6. PILOT_PASS2_RECONCILIATION_BLANK.csv (Pass 2 identity reconciliation template)
    pass2_rows = build_pass2_reconciliation_rows(selected_cases)
    pass2_path = output_dir / "PILOT_PASS2_RECONCILIATION_BLANK.csv"
    write_csv(pass2_path, pass2_rows, PASS2_RECONCILIATION_FIELDS)

    # Clean up obsolete single-row unseparated template if present
    old_reviewer_path = output_dir / "PILOT_REVIEWER_BLINDED.csv"
    if old_reviewer_path.is_file():
        old_reviewer_path.unlink()

    # 7. ANNOTATION_CODEBOOK.md
    codebook_content = generate_codebook()
    codebook_path = output_dir / "ANNOTATION_CODEBOOK.md"
    codebook_path.write_text(codebook_content, encoding="utf-8")

    # 8. PILOT_PROTOCOL.md
    protocol_content = generate_protocol(stratum_counts, seed=args.seed)
    protocol_path = output_dir / "PILOT_PROTOCOL.md"
    protocol_path.write_text(protocol_content, encoding="utf-8")

    # 9. pilot_manifest.json
    output_files = [
        selection_path,
        mapping_path,
        pass1_path,
        claims_path,
        provenance_path,
        pass2_path,
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
        "version": "2.5.0",
        "schema_version": "2.5.0",
        "description": "Blinded 20-case annotation pilot (claim targets include factual identity/biography; provenance is separated from textual mentions)",
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
        "version": "2.5.0",
        "output_directory": str(output_dir),
        "selected_count": len(selected_cases),
        "unique_source_ids": len(set(case["source_id"] for case in selected_cases)),
        "strata_breakdown": stratum_counts,
        "case_mapping": [
            {
                "pilot_case_id": case["pilot_case_id"],
                "v3_case_id": case["v3_case_id"],
                "source_id": case["source_id"],
                "narrator_name": case["narrator_name"],
                "stratum": case["sampling_stratum"],
            }
            for case in selected_cases
        ],
    }, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
