# Shamela4 Narrator Criticism Annotation Codebook (Evaluation-Level & Two-Pass Design)

## 1. Research Context and Purpose

This codebook provides precise instructions for human annotators validating narrator criticism (`garh`) entries extracted from the Shamela4 database (`narrators.parquet`).

The objective is to establish the ground-truth interpretation of criticism tuples before any automated classification rules, representation models (such as AraBERT), or Graph Neural Networks (GNNs) are trained.

### Core Safeguards
1. **Zero Fabrication**: Never guess or invent an attribution, stance, or date not justified by the verbatim text.
2. **Preserve Verbatim Text**: Never normalize or edit Arabic quotations in verbatim fields.
3. **No Group Label Conflation**: Do not assume the database `group_label` (e.g. `البخاري`, `الدارقطني`) is the historical evaluator. Many entries transmit quotes from other scholars.
4. **No Binary Sentiment Forcing**: Do not force nuanced or ambiguous statements into binary positive or negative categories. Factual transmission disconnect (*inqita'*) or hadith-level rejection must not be silently converted into general narrator unreliability.
5. **Separation of Entities**: Keep historical speaker attribution, intermediate transmission, source work authorship, narrator identity, and evaluative stance strictly distinct.

---

## 2. Unit of Analysis: Evaluation-Level Records

A single criticism tuple consists of two text fields (`field_1`, `field_2`) and an opaque `source_id`.
- **Core Principle**: A single tuple may contain **multiple distinct evaluations**, different historical evaluators, multiple evaluated individuals, or nested attributions.
- **Record Structure**: Annotations are recorded in `PILOT_EVALUATIONS_BLANK.csv`. Each row represents **one distinct evaluative claim** and links to its parent tuple via `pilot_case_id`.
- **Multiple Evaluations per Tuple**:
  - If a tuple contains only one evaluation, complete row `{pilot_case_id}_E01`.
  - If a tuple quotes multiple critics (e.g., Malik and Yahya b. Ma'in) or evaluates multiple individuals, insert a new row with the same `pilot_case_id` and an incremented `evaluation_id` (e.g., `{pilot_case_id}_E02`, `{pilot_case_id}_E03`).
  - There is no upper limit on the number of evaluation rows per tuple.
- **Non-Evaluative Entries**: If a tuple contains only bibliographic citations, book numbers, or hadith locators without human evaluative prose, annotate a single row with `contains_evaluation = no` and mark evaluative fields as `not_applicable`.

---

## 3. Two-Pass Blinding Protocol

To eliminate confirmation bias and prevent metadata contamination, annotation proceeds in two strictly decoupled stages:

### Pass 1: Blinded Text-Only Extraction
1. The annotator opens `PILOT_PASS1_TEXT_BLINDED.csv` and `PILOT_EVALUATIONS_BLANK.csv`.
2. `PILOT_PASS1_TEXT_BLINDED.csv` exposes **only** `pilot_case_id`, `entry_index`, `original_field_1`, `original_field_2`, and `original_tuple_json`.
3. The annotator **does not see** the database-attached `narrator_id` or `narrator_name`.
4. Based solely on the verbatim Arabic text, the annotator identifies:
   - Evaluated person as written in the text.
   - Evaluator, intermediate transmitter, and compiler.
   - Exact evaluative span, stance, and evaluation target.
   - Documentary citations and locators.

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

### Section B: Historical Evaluator and Attribution Provenance
Annotators must rigorously distinguish five distinct roles:
1. **Immediate Compiler / Source Author**: Author of the book holding the text (e.g., al-Tirmidhi, al-Bayhaqi, al-Bazzar).
2. **Cited Classical Work**: Classical compilation cited inside the passage (e.g., *al-Tarikh al-Kabir*, *al-Jarh wa al-Ta'dil*, *Tahdhib al-Tahdhib*).
3. **Historical Evaluator**: Scholar whose personal judgement is reported (e.g., Ahmad b. Hanbal, Yahya b. Ma'in, al-Bukhari, Malik).
4. **Intermediate Transmitter**: Authority who reported the critic's statement (e.g., Uthman al-Darimi asking Ibn Ma'in; Abu Talib from Ahmad).
5. **Other Quoted Speaker**: Secondary scholars mentioned in isnad commentary.

- `historical_evaluator_as_written`:
  - **Definition**: Verbatim name of the scholar to whom the judgment is attributed.
  - **Allowed Values**: Exact Arabic string from text (e.g., `أحمد بن حنبل`, `مالك بن أنس`, `يحيى بن معين`), or `[المصنف]` (if spoken directly by compiler without attribution), or `[مجهول/صيغة تمريض]` (for passive/collective verbs like `كذبوه`).
  - **Rule**: Do NOT copy the database group label unless the text explicitly confirms that scholar spoke it.
- `historical_evaluator_normalized`:
  - **Definition**: Standardized classical Arabic scholarly name.
  - **Allowed Values**: Canonical name (e.g., `أحمد بن حنبل`, `يحيى بن معين`, `الدارقطني`, `علي بن المديني`, `ابن حجر العسقلاني`, `مجهول/غير محدد`).
- `intermediate_transmitter_as_written`:
  - **Definition**: Name of the intermediate reporter conveying the statement.
  - **Allowed Values**: Verbatim Arabic name (e.g., `عثمان الدارمي`, `أبو طالب`, `عبد الله بن أحمد`), `none`, or `unclear`.
- `compiler_or_source_author`:
  - **Definition**: Immediate compiler of the physical source passage.
  - **Allowed Values**: Canonical compiler name (e.g., `الترمذي`, `البيهقي`, `ابن عدي`, `الطحاوي`, `البزار`, `ابن حجر`).
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

### Section C: Evaluative Content and Stance Nuance
- `contains_evaluation`:
  - **Definition**: Does this specific claim contain a qualitative evaluation of reliability, memory, or transmission?
  - **Allowed Values**: `yes`, `no`, `unclear`.
- `evaluative_span_verbatim`:
  - **Definition**: Exact verbatim Arabic substring containing the evaluative judgement.
  - **Examples**: `ضعيف`, `كذبوه`, `ليس بالقوي`, `لا أعرفه`, `متروك الحديث`, `هو أحد أئمة المسلمين إلا أنه لما كبر ساء حفظه`.
- `stance`:
  - **Definition**: Scholarly orientation of the specific claim.
  - **Allowed Values**:
    - `positive`: Explicit praise or endorsement (e.g., `ثقة`, `صدوق`, `حجة`, `أحب إلي كلاهما`).
    - `negative`: Severe moral or foundational reliability rejection (e.g., `كذاب`, `متروك`, `كذبوه`, `ساقط`).
    - `memory_criticism`: Specific mnemonic defect or precision criticism without total moral rejection (e.g., `ساء حفظه`, `فيه لين`, `يخلط`, `تكلم فيه من قبل حفظه`, `ليس بالقوي`).
    - `inqita_or_transmission_disconnect`: Factual or chronological non-hearing/disconnection (e.g., `لم يسمع من فلان`, `لم يدرك النبي صلى الله عليه وسلم`, `مرسل`, `منقطع`).
    - `hadith_level_rejection`: Invalidation of the specific report/narration rather than the narrator (e.g., `هذا لا يثبت`, `لا يصح عن الزهري`, `حديث منكر`, `تفرد به`).
    - `mixed`: Co-presence of praise and criticism in the same claim (e.g., `هو أحد أئمة المسلمين إلا أنه لما كبر ساء حفظه`).
    - `qualified`: Restricted validity or conditional acceptance (e.g., reliable in a specific teacher or book, but weak in others).
    - `neutral_descriptive`: Descriptive factual observation without evaluative force.
    - `unclear`: Ambiguous wording that defies clear stance interpretation.
    - `not_applicable`: When `contains_evaluation = no`.
  - **Critical Scholarly Rule**: Do NOT force `لم يسمع من فلان`, `تفرد به`, or `لا يصح` into `negative` narrator reliability. In classical *rijal* criticism, transmission disconnect is distinct from moral unreliability.
- `evaluation_target`:
  - **Definition**: What exact entity is evaluated by this claim?
  - **Allowed Values**:
    - `narrator_overall`: General status of the narrator across all transmissions.
    - `specific_transmission_link`: Contact or hearing between two specific individuals (e.g., `لم يسمع من عكرمة`).
    - `specific_hadith_text`: Flaw or invalidation of a specific report (e.g., `هذا حديث لا يثبت`).
    - `memory_or_precision`: Cognitive retention or book-keeping accuracy.
    - `commentary_or_legal_discussion`: Legal or factual commentary that is not an evaluation of transmission reliability.
    - `documentary_citation_only`: Non-evaluative locator or title.
    - `not_applicable`: When `contains_evaluation = no`.
- `qualification_or_context`:
  - **Definition**: Specific contextual scope, condition, or limitation placed on the evaluation.
  - **Allowed Values**: Explanatory text (e.g., `في حفظه لا في عدالته`, `لما كبر في السن`, `عن عطاء خاصة`), or `none`.

### Section D: Documentary Provenance
- `source_work_as_written`: Title of cited book as written in the text or locator span.
- `source_work_normalized`: Canonical title of the referenced work.
- `source_locator_as_written`: Verbatim volume, page, or hadith number string (e.g. `(1/ 23) برقم: (81)`).

### Section E: Annotation Quality
- `transcription_confidence`: `high`, `medium`, `low`, `unresolved`.
- `interpretation_confidence`: `high`, `medium`, `low`, `unresolved`.
- `unresolved_ambiguity`: Concise description of competing interpretations, or `none`.
- `reviewer_notes`: Free-text observations, cross-references, or historical anomalies.

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
