# Shamela4 20-Case Blinded Manual Annotation Pilot Protocol

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
- `unnumbered_suffix_or_formatting`: 3 cases
- `compound_or_multiple_locator`: 3 cases
- `mixed_source_ID`: 4 cases
- `suspected_or_unresolved`: 4 cases
- `normal_prose_then_citation`: 3 cases
- `citation_only_then_locator_bearing_prose`: 3 cases

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
4. **Deterministic Shuffling**: Case presentation order is shuffled using fixed seed `20261111`, producing blinded identifiers `PILOT01` through `PILOT20`.
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
