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
6. **No Unsupported Immediate-Source Attribution**: The appearance of a book title or locator within a tuple does not automatically establish that it was the immediate compilation from which the excerpt was extracted. Pass 1 annotates textual evidence; it cannot establish documentary provenance absent from the text. Where independent external or bibliographic evidence is absent, record `immediate_source_work_verified = unresolved`.

---

## 2. Unit of Analysis: Evaluation-Level Records

A single criticism tuple consists of two text fields (`field_1`, `field_2`) and an opaque `source_id`.
- **Core Principle**: A single tuple may contain **multiple distinct evaluations**, different historical evaluators, multiple evaluated individuals, or nested attributions.
- **Record Structure**: Annotations are recorded in `PILOT_EVALUATIONS_BLANK.csv`. Each row represents **one distinct evaluative claim** and links to its parent tuple via `pilot_case_id`.
- **Multiple Evaluations per Tuple**:
  - If a tuple contains only one evaluation, complete row `{pilot_case_id}_E01`.
  - If a tuple quotes multiple critics (e.g., Malik and Yahya b. Ma'in) or evaluates multiple individuals, insert a new row with the same `pilot_case_id` and an incremented `evaluation_id` (e.g., `{pilot_case_id}_E02`, `{pilot_case_id}_E03`).
  - There is no upper limit on the number of evaluation rows per tuple.
- **Non-Evaluative Entries**: If a tuple contains only bibliographic citations, book numbers, or hadith locators without human evaluative prose, annotate a single row with `contains_evaluation = no`, `statement_function = documentary_citation`, and `evaluative_orientation = not_applicable`.

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
4. Based solely on the verbatim Arabic text, the annotator identifies:
   - Evaluated person as written in the text.
   - Immediate source work vs cited classical work.
   - Historical evaluator, intermediate transmitter, and compiler.
   - Statement function and evaluative orientation.
   - Verbatim evaluative span and locators.

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
  - **Definition**: Verbatim Arabic name of the person evaluated in this specific claim.
  - **Allowed Values**: Exact Arabic string from text, or `[غير مصرح به]` (unnamed/implicit pronoun), or `[ليس راويا]` (if target is hadith text or book).
  - **Examples**: `معارك بن عباد العبدي`, `أبو جابر البياضي`, `حارثة`.
- `evaluated_person_identity_confidence`:
  - **Definition**: Confidence that the text refers to the identified individual.
  - **Allowed Values**: `high`, `medium`, `low`, `unresolved`.

### Section B: Provenance and Attribution Architecture
Annotators must rigorously distinguish separate provenance roles:
1. **Immediate Source Work**: The specific compilation from which this Shamela excerpt was extracted.
2. **Compiler / Source Author**: The author of the immediate source work.
3. **Mentioned Work Title & Role**: The title of any work appearing in the text or citation header and its operational role.
4. **Immediate Source Work Verification**: Explicit confirmation of whether the immediate source work is independently verified.
5. **Cited Work**: A separate historical compilation mentioned or quoted inside the passage.
6. **Historical Evaluator**: The scholar whose personal judgement is reported.
7. **Intermediate Transmitter**: The reporter who conveyed the critic's statement.
8. **Other Quoted Speaker**: Secondary scholars mentioned in chain analysis.

- `immediate_source_work_as_written`:
  - **Definition**: Title of the immediate excerpted work as written in the text or locator string.
  - **Allowed Values**: Verbatim Arabic string (e.g., `سنن البيهقي الكبرى`, `شرح مشكل الآثار`, `جامع الترمذي`), or `unresolved` if ambiguous.
- `immediate_source_work_normalized`:
  - **Definition**: Canonical title of the immediate excerpted work.
  - **Allowed Values**: Standard title (e.g., `سنن البيهقي الكبرى`, `شرح مشكل الآثار`, `جامع الترمذي`, `مسند البزار`), or `unresolved`.
- `compiler_or_source_author`:
  - **Definition**: Immediate author of the excerpted source work.
  - **Allowed Values**: Canonical compiler name (e.g., `البيهقي`, `الطحاوي`, `الترمذي`, `البزار`, `ابن حبان`), or `unresolved`.
  - **Rule**: Do NOT assume compiler, cited-work author, and historical evaluator are the same person.
- `work_title_as_written`:
  - **Definition**: Verbatim title of any work appearing in the text, citation header, or locator string.
  - **Allowed Values**: Exact Arabic text (e.g. `سنن البيهقي الكبرى`, `شرح مشكل الآثار`, `تقريب التهذيب`, `الأحاديث المختارة`), or `none`.
- `work_role`:
  - **Definition**: The operational role of the mentioned work within the passage.
  - **Allowed Values**:
    - `immediate_source_work`: The compilation from which the Shamela passage was extracted (use ONLY if verified or explicitly stated).
    - `cited_work`: A separate historical work quoted or cited inside the passage.
    - `other_referenced_work`: A work mentioned in passing as comparison or cross-reference.
    - `unclear`: Ambiguous role that cannot be determined with certainty from text.
- `immediate_source_work_verified`:
  - **Definition**: Whether independent documentary or external evidence verifies that the work was the immediate extraction source.
  - **Allowed Values**: `yes`, `no`, `unresolved`.
  - **Mandatory Guidance**: Annotators must **not** infer the immediate source work solely from a title or locator appearing in the tuple. Where independent evidence is unavailable, record `unresolved`. Pass 1 text cannot establish documentary provenance that is absent from its text.
- `cited_work_as_written`:
  - **Definition**: Title of any distinct secondary or earlier classical work cited inside the passage.
  - **Allowed Values**: Verbatim Arabic string (e.g., `لسان الميزان`, `تقريب التهذيب`, `الجرح والتعديل`, `صحيح مسلم`, `سنن الدارقطني`), or `none` if no secondary work is cited.
- `cited_work_normalized`:
  - **Definition**: Canonical title of the secondary cited work.
  - **Allowed Values**: Standard title (e.g., `لسان الميزان`, `تقريب التهذيب`, `الجرح والتعديل لابن أبي حاتم`, `صحيح مسلم`), or `none`.
- `source_locator_as_written`:
  - **Definition**: Verbatim volume, page, or hadith number string (e.g. `(1/ 23) برقم: (81)`, `(12/ 362) (بدون ترقيم)`).
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
2. `evaluation_target` (what entity/aspect is appraised)
3. `statement_function` (classical hadith function)
4. `evaluative_orientation` (qualitative stance/valence)

- `contains_evaluation`:
  - **Definition**: Does this specific claim contain a qualitative appraisal of a narrator, transmission link, or report? Explicitly distinguishes qualitative appraisal from factual, descriptive, or documentary observations.
  - **Allowed Values**:
    - `yes`: A qualitative appraisal is made (evaluating narrator reliability, character, memory retention, or hadith validity).
    - `no`: The statement is factual, descriptive, biographical, or documentary without qualitative appraisal.
    - `unclear`: The distinction between qualitative appraisal and factual observation cannot be established confidently.
  - **Mandatory Guidance**: A `transmission_observation` does **not** automatically imply `contains_evaluation = yes`. For example, `لم يسمع من عنبسة شيئا` is a factual observation of isnad disconnection (*inqita'*), not a qualitative evaluation of the narrator's character or trustworthiness (`contains_evaluation = no`).
- `evaluation_target`:
  - **Definition**: The specific entity or aspect to which the claim's appraisal is directed. Keep strictly distinct from the person named (`evaluated_person_as_written`), the function of the statement (`statement_function`), and its evaluative orientation (`evaluative_orientation`).
  - **Allowed Values**:
    - `narrator_overall`: General moral integrity, religious reliability, truthfulness, or foundational trustworthiness of the narrator (e.g. `ثقة`, `كذاب`, `متروك`, `ضعيف`, `لا يحتج به`).
    - `memory_or_precision`: Cognitive retention, book precision, senility/confusion in old age, or accuracy in specific contexts (e.g. `ساء حفظه لما كبر`, `فيه لين`, `تكلم فيه من قبل حفظه`).
    - `specific_transmission_link`: Specific isnad audition (*sama'*), meeting (*liqā'*), generational non-contiguity (*inqita'*), or teacher-student transmission link (e.g. `لم يسمع من فلان`, `تفرد به فلان عن فلان`, `لم يدرك النبي صلى الله عليه وسلم`).
    - `specific_hadith_or_report`: Assessment directed at a specific narration, matn, or particular hadith wording rather than general narrator character (e.g. `هذا لا يثبت`, `لا يصح عن الزهري`, `حديث منكر`).
    - `comparative_narrator_assessment`: Relational evaluation or relative standing between two or more narrators (e.g. `يونس أحب إليك في الحسن أو حميد ؟ فقال كلاهما`).
    - `not_applicable`: When `contains_evaluation = no` (e.g. pure documentary citations, pure book locators, non-evaluative biographical statements).
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
  - **Definition**: The qualitative orientation/valence conveyed by this specific claim in context.
  - **Allowed Values**:
    - `positive`: Explicit praise or favorable validation (e.g., `ثقة`, `صدوق`, `حجة`).
    - `negative`: Explicit criticism or disparagement (e.g., `ضعيف`, `كذاب`, `متروك`, `كذبوه`).
    - `mixed`: Co-presence of praise and criticism in the same claim (e.g., `هو أحد أئمة المسلمين إلا أنه لما كبر ساء حفظه`).
    - `qualified`: Restricted validity or conditional acceptance (e.g., reliable in a specific teacher, but weak in others; or `ليس بالقوي`).
    - `neutral`: Purely descriptive, non-evaluative statement (e.g., biographical notes, chronological inqita without disparagement, pure documentary citations).
    - `unclear`: Ambiguous orientation.
    - `not_applicable`: When `contains_evaluation = no`.

#### Contextual Interpretation Guidelines:
1. **`تفرد به` (Singularity of Transmission)**:
   - `statement_function`: `transmission_observation`
   - `evaluation_target`: `specific_transmission_link`
   - `evaluative_orientation`: `neutral` or `qualified` depending on context. In classical criticism, *tafarrud* by an acceptable narrator is not inherently negative; it indicates uniqueness. Do NOT automatically classify as `negative`.
2. **`لا أعرفه` (Non-Recognition)**:
   - `statement_function`: `narrator_appraisal` or `transmission_observation`
   - `evaluation_target`: `narrator_overall` or `specific_transmission_link`
   - `evaluative_orientation`: `neutral`, `qualified`, or `negative` depending on whether it denotes total obscurity (*jahalah*) or local non-familiarity. Do not treat as a formal grade of deliberate weakness without context.
3. **`أحب إليك... فقال كلاهما` (Comparative Preference)**:
   - `statement_function`: `comparative_preference`
   - `evaluation_target`: `comparative_narrator_assessment`
   - `evaluative_orientation`: `neutral` or `unclear` (or `positive`/`qualified` only if context explicitly establishes praise). Allow `neutral` or `unclear` orientation unless surrounding text establishes a positive or negative judgement. Do **not** infer that both narrators are independently reliable merely because the response is `كلاهما`.
4. **`لم يسمع من فلان` (Transmission Disconnect)**:
   - `contains_evaluation`: `no` (when stating factual non-audition without qualitative moral/memory appraisal).
   - `statement_function`: `transmission_observation`
   - `evaluation_target`: `specific_transmission_link`
   - `evaluative_orientation`: `neutral` (or `not_applicable`). It establishes *inqita'* (lack of direct hearing), not moral unreliability or fabrication.
5. **`لا يصح عن الزهري` (Narration Invalidation)**:
   - `contains_evaluation`: `yes`
   - `statement_function`: `hadith_or_report_appraisal`
   - `evaluation_target`: `specific_hadith_or_report`
   - `evaluative_orientation`: `negative` (directed at the hadith, not necessarily narrator unreliability).

#### Inter-Field Relationship and Examples Matrix
| Arabic Statement | `contains_evaluation` | `evaluation_target` | `statement_function` | `evaluative_orientation` | Contextual Explanation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `أبو جابر البياضي كذاب` | `yes` | `narrator_overall` | `narrator_appraisal` | `negative` | Direct qualitative impugnment of narrator truthfulness. |
| `عمرو بن شعيب ثقة` | `yes` | `narrator_overall` | `narrator_appraisal` | `positive` | Direct qualitative validation of foundational reliability. |
| `تكلم فيه من قبل حفظه` | `yes` | `memory_or_precision` | `memory_or_precision_observation` | `negative` | Qualitative evaluation targeted specifically at memory retention. |
| `لما كبر ساء حفظه` | `yes` | `memory_or_precision` | `memory_or_precision_observation` | `qualified` | Qualified appraisal: reliable earlier, cognitive impairment in old age. |
| `مكحول لم يسمع من عنبسة شيئا` | `no` | `specific_transmission_link` | `transmission_observation` | `neutral` | Factual observation of isnad disconnection (*inqita'*); no qualitative appraisal. |
| `عامر بن مسعود لم يدرك النبي` | `no` | `specific_transmission_link` | `transmission_observation` | `neutral` | Factual historical/generational statement of non-contiguity. |
| `تفرد به عبد العزيز...` | `unclear` | `specific_transmission_link` | `transmission_observation` | `unclear` | Singularity of transmission; evaluative force depends strictly on surrounding context. |
| `هذا حديث لا يثبت` | `yes` | `specific_hadith_or_report` | `hadith_or_report_appraisal` | `negative` | Qualitative invalidation directed at specific hadith text, not general narrator character. |
| `أحب إليك... فقال كلاهما` | `yes` | `comparative_narrator_assessment` | `comparative_preference` | `neutral` | Relative preference query; responding `كلاهما` does not imply independent unconditional reliability. |
| `سنن البيهقي الكبرى: (3/ 176)` | `no` | `not_applicable` | `documentary_citation` | `not_applicable` | Pure bibliographic book locator; zero evaluative content. |
| `أبو الرجال اسمه محمد` | `no` | `not_applicable` | `biographical_description` | `neutral` | Purely factual biographical name clarification; zero evaluative content. |

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
