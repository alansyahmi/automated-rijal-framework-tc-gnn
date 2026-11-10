# Shamela4 20-Case Blinded Manual Annotation Pilot Protocol (Two-Pass & Claim-Level)

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
- `unnumbered_suffix_or_formatting`: 3 cases
- `compound_or_multiple_locator`: 3 cases
- `mixed_source_ID`: 4 cases
- `suspected_or_unresolved`: 4 cases
- `normal_prose_then_citation`: 3 cases
- `citation_only_then_locator_bearing_prose`: 3 cases

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
- An initial template row `{pilot_case_id}_C01` is provided for each pilot case.
- When an entry contains several claims (e.g. it combines transmission commentary, a narrator appraisal, and factual biography):
  1. Insert a new row directly beneath the primary row.
  2. Set `pilot_case_id` to the parent case ID (e.g. `PILOT01`).
  3. Set `claim_id` to `{pilot_case_id}_C02` (then `_C03`, etc.).
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
