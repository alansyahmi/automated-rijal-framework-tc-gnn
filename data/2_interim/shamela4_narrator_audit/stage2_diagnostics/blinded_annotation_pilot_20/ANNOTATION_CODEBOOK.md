# Shamela4 Narrator Criticism Annotation Codebook

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
