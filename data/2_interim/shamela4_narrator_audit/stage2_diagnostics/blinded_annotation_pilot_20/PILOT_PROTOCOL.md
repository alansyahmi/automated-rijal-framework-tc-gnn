# Shamela4 20-Case Blinded Manual Annotation Pilot Protocol (Two-Pass & Evaluation-Level)

## 1. Objectives

This pilot study evaluates the feasibility, clarity, and precision of the human annotation codebook on a purposive sample of 20 criticism tuples extracted from Shamela4.

Specific research questions investigated by this pilot:
1. **Evaluative Content**: Can annotators reliably distinguish between genuine evaluative judgements, factual inqita statements, hadith rulings, and pure documentary citations?
2. **Evaluation-Level Granularity**: Can complex tuples containing multiple evaluators or multiple evaluated persons be cleanly decomposed into distinct evaluation records?
3. **Attribution Boundaries**: Can historical critics (e.g., Ahmad, Yahya b. Ma'in) be reliably differentiated from compilers (e.g., al-Tirmidhi, al-Bayhaqi) and intermediate transmitters?
4. **Attribution Type**: Can direct statements, nested isnads, and passive consensus phrases (`كذبوه`) be systematically differentiated?
5. **Span Isolation**: Can the evaluative span be isolated from surrounding biographical notes, isnad commentary, and legal debates?
6. **Blinded Reconciliation**: Does the database-attached narrator identity match the person actually evaluated in the text when evaluated without metadata bias?
7. **Automated Concordance**: Do existing automated heuristic patterns align with human semantic understanding?

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
   - Opaque database `source_id` and all automated classifier labels/strata are **strictly excluded**.
   - Annotations are recorded in `PILOT_EVALUATIONS_BLANK.csv`.
   - Multiple evaluations per tuple are recorded as multiple rows sharing `pilot_case_id` with incremented `evaluation_id`.
2. **Pass 2 (Identity Reconciliation)**:
   - After completing Pass 1, annotator opens `PILOT_PASS2_RECONCILIATION_BLANK.csv`.
   - Attached narrator metadata (`attached_narrator_id`, `attached_narrator_name`) is revealed alongside the original text.
   - Annotator reconciles whether the attached narrator is the true target, an isnad partner, or a false attachment.
   - Automated classifier labels and source IDs remain strictly blinded.

---

## 4. Multi-Evaluation Recording Instructions

Annotators must adhere to this rule: **One evaluative claim per row**.
- An initial template row `{pilot_case_id}_E01` is provided for each pilot case.
- When an entry contains several evaluations (e.g. `PILOT01` quotes Malik and Yahya b. Ma'in; `PILOT03` quotes 5+ critics):
  1. Insert a new row directly beneath the primary row.
  2. Set `pilot_case_id` to the parent case ID (e.g. `PILOT01`).
  3. Set `evaluation_id` to `{pilot_case_id}_E02` (then `_E03`, etc.).
  4. Fill in the specific evaluated person, historical evaluator, evaluative span, stance, and target for that distinct claim.
- There is no arbitrary maximum number of evaluation rows.

---

## 5. Limitations

- **Sample Size**: $N = 20$ evaluates codebook clarity and annotation feasibility, but cannot estimate overall corpus error rates.
- **Digital Ingestion Artifacts**: Shamela4 tuples reflect digital book extractions whose upstream Lucene/SQLite provenance remains unverified by official documentation.
- **Secondary Citations**: Many classical criticism entries quote earlier authorities through later encyclopedic works (e.g. *Tahdhib al-Tahdhib*, *Lisan al-Mizan*); annotators must carefully separate the historical authority from the immediate compiler.
