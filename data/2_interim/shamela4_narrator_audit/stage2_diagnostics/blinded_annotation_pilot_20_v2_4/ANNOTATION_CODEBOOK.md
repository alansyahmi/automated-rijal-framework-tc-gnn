# Shamela4 Narrator Criticism Annotation Codebook (Evaluation-Level & Two-Pass Design)

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

## 2. Unit of Analysis: Evaluation-Level Records

A single criticism tuple consists of two text fields (`field_1`, `field_2`) and an opaque `source_id`.
- **Core Principle**: A single tuple may contain **multiple distinct evaluations**, different historical evaluators, multiple evaluated individuals, or nested attributions.
- **Record Structure**: Annotations are recorded in `PILOT_EVALUATIONS_BLANK.csv`. Each row represents **one distinct evaluative claim** and links to its parent tuple via `pilot_case_id`.
- **Multiple Evaluations per Tuple**:
  - If a tuple contains only one evaluation, complete row `{pilot_case_id}_E01`.
  - If a tuple quotes multiple critics (e.g., Malik and Yahya b. Ma'in) or evaluates multiple individuals, insert a new row with the same `pilot_case_id` and an incremented `evaluation_id` (e.g., `{pilot_case_id}_E02`, `{pilot_case_id}_E03`).
  - There is no upper limit on the number of evaluation rows per tuple.
- **Non-Evaluative Entries**: If a tuple contains only bibliographic citations, book numbers, or hadith locators without human evaluative prose, annotate a single row with `contains_evaluation = no`, an appropriate `claim_target` (usually `not_applicable` for a pure citation), `statement_function = documentary_citation`, and `evaluative_orientation = not_applicable`.

---

## 3. Two-Pass Blinding Protocol

To eliminate confirmation bias and prevent metadata contamination, annotation proceeds in two strictly decoupled stages:

### Pass 1: Blinded Text-Only Extraction
1. The annotator opens `PILOT_PASS1_TEXT_BLINDED.csv` and `PILOT_EVALUATIONS_BLANK.csv`.
2. `PILOT_PASS1_TEXT_BLINDED.csv` exposes **only**:
   - `pilot_case_id`
   - `entry_index`
   - `original_field_1`
   - `original_field_2`
   - `original_tuple_json` (sanitized 2-element array `[field_1, field_2]` with no source ID).
3. The annotator **does not see** the database-attached `narrator_id`, `narrator_name`, or `source_id`.
4. Based solely on the verbatim Arabic text, the annotator records visible textual mentions and roles, not external provenance:
   - Person or entity referred to by each claim, as written.
   - Work titles and locators appearing in the passage, with textual role (`cited_work`, `other_referenced_work`, or `unclear`).
   - Historical evaluator and intermediate transmitter only when explicitly represented in the text.
   - Statement function, whether a qualitative evaluation is present, claim target, and orientation.
   - Verbatim claim span, quotation boundary, and citation boundary where identifiable.
5. Do not infer which work the database extracted from. Documentary verification happens separately in `PILOT_PROVENANCE_RECONCILIATION_BLANK.csv`, after Pass 1; unresolved evidence stays unresolved.

### Pass 2: Attached Identity Reconciliation
1. After completing Pass 1, the annotator opens `PILOT_PASS2_RECONCILIATION_BLANK.csv`.
2. This template reveals `attached_narrator_id` and `attached_narrator_name` alongside the text.
3. The annotator reconciles their Pass 1 findings against the database attachment:
   - Does the attached narrator match the person actually evaluated in the text?
   - Is the entry an evaluation of an isnad partner, teacher, or hadith text?
   - Was the database attachment a false attachment or contextual mention?

---

## 4. Evaluation-Level Schema and Field Definitions (`PILOT_EVALUATIONS_BLANK.csv`)

### Identifiers
- `pilot_case_id`: Blinded identifier linking to Pass 1 tuple context (e.g. `PILOT01` to `PILOT20`).
- `evaluation_id`: Unique identifier for the evaluative claim (e.g. `PILOT01_E01`, `PILOT01_E02`).

### Section A: Evaluated Person
- `evaluated_person_as_written`:
  - **Definition**: Verbatim Arabic name of the person who is the subject of this specific claim, whether or not the claim evaluates them.
  - **Allowed Values**: Exact Arabic string from text, or `[غير مصرح به]` (unnamed/implicit pronoun), or `[ليس راويا]` (if target is hadith text or book).
  - **Examples**: `معارك بن عباد العبدي`, `أبو جابر البياضي`, `حارثة`.
- `evaluated_person_identity_confidence`:
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
1. `contains_evaluation` (qualitative appraisal vs factual observation)
2. `claim_target` (the entity or aspect the claim concerns, whether factual or evaluative)
3. `statement_function` (classical hadith function)
4. `evaluative_orientation` (qualitative stance/valence)

- `contains_evaluation`:
  - **Definition**: Does this specific claim contain a qualitative appraisal of a narrator, transmission link, or report? Explicitly distinguishes qualitative appraisal from factual, descriptive, or documentary observations.
  - **Allowed Values**:
    - `yes`: A qualitative appraisal is made (evaluating narrator reliability, character, memory retention, or hadith validity).
    - `no`: The statement is factual, descriptive, biographical, or documentary without qualitative appraisal.
    - `unclear`: The distinction between qualitative appraisal and factual observation cannot be established confidently.
  - **Mandatory Guidance**: A `transmission_observation` does **not** automatically imply `contains_evaluation = yes`. For example, `لم يسمع من عنبسة شيئا` is a factual observation of isnad disconnection (*inqita'*), not a qualitative evaluation of the narrator's character or trustworthiness (`contains_evaluation = no`).
- `claim_target`:
  - **Definition**: The entity or aspect that the claim is about. It is distinct from the person named (`evaluated_person_as_written`), the function (`statement_function`), and the orientation (`evaluative_orientation`). This field applies to factual claims as well as appraisals.
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

- `pilot_case_id`: Blinded identifier linking to Pass 1.
- `attached_narrator_id`: Numeric ID of the narrator to whom the tuple was attached in `narrators.parquet`.
- `attached_narrator_name`: Short name of the narrator from the database.
- `entry_index`, `original_field_1`, `original_field_2`: Verbatim text retained for review.
- `target_matches_attached_narrator`:
  - `exact_match`: The evaluated person in Pass 1 is unambiguously the attached narrator.
  - `different_person`: The text evaluates another person (e.g., father, teacher, narrator partner).
  - `multiple_narrators_evaluated`: The text evaluates both the attached narrator and others.
  - `no_narrator_evaluated`: The text evaluates a hadith text or is a pure documentary citation.
  - `unresolved`: Textual ambiguity prevents conclusive determination.
- `reconciliation_status`:
  - `confirmed_target`: Verified correct database attachment.
  - `false_attachment_in_database`: The tuple was attached to a narrator not evaluated in the text.
  - `isnad_partner_evaluated`: The evaluation belongs to another link in the transmission chain.
  - `contextual_mention_only`: Attached narrator is mentioned only as a background reference.
  - `unclear`: Unresolved relationship.
- `reconciled_narrator_id`: Confirmed narrator ID if resolved, or blank if external/unlinked.
- `reconciliation_confidence`: `high`, `medium`, `low`, `unresolved`.
- `reconciliation_notes`: Free-text explanation of how the attached identity relates to the passage.
