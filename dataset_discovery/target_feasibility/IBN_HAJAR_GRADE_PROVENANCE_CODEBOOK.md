# Ibn Hajar Grade Provenance Investigation Codebook

## 1. Investigation Purpose and Epistemological Framework

This codebook governs the human source-validation investigation of candidate Ibn Hajar grade strings (`الرتبة عند ابن حجر`) across HadithDB and Shamela4. The primary objective is to determine whether stored dataset values represent authentic, traceable evaluations by Shihab al-Din Abu al-Fadl Ahmad ibn Ali ibn Muhammad al-Kinani al-Asqalani, known as **Ibn Hajar al-Asqalani (773-852 AH)**, in his canonical biographical synthesis, ***Taqrib al-Tahdhib***.

### 1.1 Independent Verification Dimensions

The investigation audits each candidate record across three independent validity dimensions:

```
+-----------------------------------------------------------------------------------+
|                       INDEPENDENT VERIFICATION DIMENSIONS                        |
+-----------------------------------+-----------------------------------------------+
| Dimension                         | Core Research Question                        |
+-----------------------------------+-----------------------------------------------+
| 1. Textual Fidelity               | Does the stored string reproduce the verbatim |
|    (textual_fidelity)             | phrasing of the entry in Taqrib al-Tahdhib?   |
+-----------------------------------+-----------------------------------------------+
| 2. Attribution Fidelity           | Is the judgment genuinely attributable to     |
|    (attribution_fidelity)         | Ibn Hajar, or is it a quoted early critic, a  |
|                                   | compiler summary, or modern editorial text?  |
+-----------------------------------+-----------------------------------------------+
| 3. Identity Fidelity              | Does the source entry describe the identical  |
|    (identity_fidelity)            | historical narrator as the dataset record?    |
| 4. Historical Input Eligibility   | Does provenance satisfy the separate input    |
|    (input_eligibility)            | inclusion rule?                               |
| 5. Target Candidate Suitability   | Is the record suitable as a candidate target? |
|    (record_disposition)           |                                                |
| 6. Construct Validity              | Does this operational measure support the     |
|                                   | intended research construct?                  |
+-----------------------------------+-----------------------------------------------+
```

### 1.2 Construct Validity Disclaimer

Textual collation and attribution verification against *Taqrib al-Tahdhib* confirm source fidelity and attribution fidelity; **they do not independently establish construct validity or machine-learning target suitability**.

Confirming that Ibn Hajar wrote a specific appraisal (e.g. `ثقة` or `صدوق يهم`) validates that the historical text has been faithfully transcribed. It does not prove that Ibn Hajar's 9th-century Hijri standardized appraisal is an unproblematic gold-standard ground truth for supervised machine learning, nor does it resolve historical disagreements among earlier classical critics.

These dimensions must remain separate. `record_disposition` is a target-candidate disposition, not an input-eligibility decision. A verified Ibn Hajar assessment is not automatically a valid historical input. An early critic attribution is not eligible without provenance verification. A verified candidate does not prove construct validity or objective narrator reliability.

### 1.3 Sampling Scope and Interpretation of Counts

The 60 records are a purposive, quota-based diagnostic stress test. They were selected to expose difficult cases, not to represent either database. Sample flag counts and overlap proportions describe only the selected 60; they cannot estimate candidate-pool prevalence or dataset-wide error rates. Population flag counts in the manifest are descriptive diagnostics computed from the full candidate pools, not estimates of annotation error.

Primary selection category counts record the selection pass that picked each record. Row-level diagnostic counts are recomputed from non-exclusive Boolean flags. Therefore, records selected in a `general` pass can also satisfy a row-level definition that has a `without conventional grade` condition. The primary `attributed_pure` allocation is 6, while the row-level count `flag_explicit_attributed_quote = TRUE` and `flag_conventional_grade = FALSE` is 12. Similarly, the primary `descriptive_pure` allocation is 6, while the row-level descriptive-without-conventional-grade count is 12. These are different operational measures, not a count discrepancy.

The operational uncomplicated conventional-grade baseline is defined exactly as: `flag_conventional_grade = TRUE` AND `flag_compound_qualified_grade = FALSE` AND `flag_descriptive_non_grade = FALSE` AND `flag_explicit_attributed_quote = FALSE` AND `flag_ambiguous_truncated_editorial = FALSE`. Criticism-text overlap is allowed, so the count of 16 is not a leakage-clean count. Applying the additional condition `flag_criticism_text_overlap = FALSE` yields 10 in this selected sample. Primary selection allocated 8 records under this baseline category. These counts describe this sample only.

---

## 2. Methodological Safeguards

### 2.1 Safeguard 1: Attribution vs. Textual Witness Firewall

An evaluator attribution within the provisional 365 AH operational boundary is **not automatic proof of an eligible historical input passage**, nor does transmission through a later compilation automatically render an earlier attributed judgment permanently ineligible.

The audit enforces five mutually exclusive attribution categories for `assessment_attribution_status`:

```
+-------------------------------------------------------------------------------------------------------+
|                                    SAFEGUARD 1 ATTRIBUTION TAXONOMY                                  |
+-------------------------------------------+-----------------------------------+-----------------------+
| Category                                  | Definition                        | Input Eligibility     |
+-------------------------------------------+-----------------------------------+-----------------------+
| 1. directly_transmitted_historical_       | An early critic appraisal         | eligible_historical_  |
|    judgment                               | (within the provisional T <= 365 AH operational boundary) transmitted with an | input                 |
|                                           | identifiable direct isnad or in a |                       |
|                                           | primary early witness.            |                       |
+-------------------------------------------+-----------------------------------+-----------------------+
| 2. traceable_intermediary_historical_     | An early critic judgment quoted   | quarantined_          |
|    judgment                               | by an intermediate compiler (e.g. | intermediary_input    |
|                                           | al-Mizzi, Ibn Hajar) citing an    | (promoted to eligible |
|                                           | identifiable source or chain.     | upon audit)           |
+-------------------------------------------+-----------------------------------+-----------------------+
| 3. insufficient_evidence_historical_      | An early judgment where the       | quarantined_          |
|    judgment                               | intermediary citation is vague,   | insufficient_evidence |
|                                           | passive ('ruwiya'), or lost.      |                       |
+-------------------------------------------+-----------------------------------+-----------------------+
| 4. compiler_own_synthesis                 | The post-365 AH compiler's own    | target_evaluation_    |
|                                           | editorial verdict (e.g. Ibn       | only (strictly        |
|                                           | Hajar's summary in Taqrib). Valid | ineligible for early  |
|                                           | ONLY as a target reference.       | historical input)     |
+-------------------------------------------+-----------------------------------+-----------------------+
| 5. modern_editorial_material              | Footnotes, brackets, emendations, | ineligible_editorial_ |
|                                           | or commentary by modern editors   | material              |
|                                           | (e.g. Awwamah, Arna'ut, Bashshar).|                       |
+-------------------------------------------+-----------------------------------+-----------------------+
```

#### Evidentiary Criteria to Move from Quarantine to Eligibility
An intermediary-preserved judgment (`traceable_intermediary_historical_judgment`) is initially held in `quarantined_intermediary_input`. It may be promoted to `eligible_historical_input` when all four of the following evidentiary criteria are satisfied:
1. **Explicit Attribution and Provisional Temporal Rule**: Identify the historical evaluator. Under this project's provisional operational inclusion rule, the evaluator's death date is at or before 365 AH. This boundary requires historical justification and is not a universal historical division. It does not establish the date of a particular judgment.
2. **Traceable Transmission Lineage in Intermediary Text**: The intermediary compilation (e.g. al-Mizzi in *Tahdhib al-Kamal* or Ibn Hajar in *Tahdhib al-Tahdhib*) cites a verifiable primary source collection (e.g. *Su'alat*, *al-Tarikh al-Kabir*, *al-Jarh wa al-Ta'dil*) or a documented transmission isnad, rather than an unattributed passive verb.
3. **Corroboration Status**: Record whether corroboration is independent, dependent, or unresolved. Multiple compilations are not independent merely because there are multiple books; a later work may reproduce the same underlying source.
4. **Editorial Integrity Verification**: The wording is verified to be the early critic's authentic assessment, rather than an editorial gloss, paraphrased summary, or abridgment introduced by the compiler.

#### Separate the Relevant Dates

Record or discuss these dates independently when evidence permits: (1) the critic's lifespan and death date; (2) approximate date of the judgment, if known; (3) composition date of the source work preserving it; (4) date of the surviving manuscript or textual witness; and (5) modern editor and edition date. Do not infer a judgment date from a critic's death date, or a witness date from a work's composition date. A modern edition date is not the date of its manuscript witness. A physical witness dated before 365 AH is not an absolute eligibility requirement.

### 2.2 Safeguard 2: Overlapping Multi-Label Sampling

The six diagnostic categories are **non-exclusive and multi-label**. A record can exhibit multiple properties simultaneously. The 60-record quota sample intentionally enriches for difficult patterns, so its flags do not mirror or estimate the full population's distribution.

The generator script evaluates all six flags independently as boolean values:

1. `flag_conventional_grade`: Contains standard, terse classical grades from Ibn Hajar's 12 ranks (e.g. `ثقة`, `صدوق`, `ضعيف`, `متروك`, `مجهول`, `مقبول`, `لين الحديث`, `كذاب`, `وضاع`, `لا بأس به`, `ليس بالقوي`, `مجهول الحال`, `مستور`, `ثبت`, `حجة`, `صالح`).
2. `flag_compound_qualified_grade`: Contains qualifications, defect markers, or conditions (e.g. `يهم`, `يخطئ`, `سيئ الحفظ`, `له أوهام`, `حيث يتابع`, `رمي بالتشيع`, `تغير بأخرة`, `فيه لين`, `يعتبر به`, `أفراد`, `دلس`, `يرسل`).
3. `flag_descriptive_non_grade`: Contains generational, biographical, or honorific descriptions (e.g. `صحابي`, `من كبار التابعين`, `أحد الأعلام`, `فقيه`, `حافظ`, `إمام`, `عابد`, `فاضل`, `مخضرم`, `أمير المؤمنين في الحديث`, `عالم`).
4. `flag_explicit_attributed_quote`: Contains explicit attribution verbs or scholar names (e.g. `قال أبو حاتم:`, `وثقه ابن معين`, `قال أحمد`, `ضعفه النسائي`, `ذكره ابن حبان`, `قال البخاري`, `مشاه`).
5. `flag_criticism_text_overlap`: The candidate grade string appears verbatim inside the narrator's criticism text (`الجرح والتعديل` in HadithDB or `garh`/`fwaed` in Shamela4), demonstrating that extracted grades often originate as raw quote slices.
6. `flag_ambiguous_truncated_editorial`: Contains brackets `[` or `]`, question marks `?` or `؟`, ellipses `...`, editorial markers (`تحقيق`, `حاشية`, `نسخة`, `كذا`), parenthesized volume/page citations, or anomalous string length (> 80 characters).

---

## 3. Detailed Worksheet Schema Specification

The worksheet contains 37 columns. Columns 1 to 14 are pre-populated by the generator script. Columns 15 to 37 are reserved for human review and must be left blank in the initial worksheet template.

### 3.1 Pre-Populated Dataset Identity & Extraction Fields (Columns 1 to 14)

#### Column 1: `audit_record_id`
- **Data Type**: String (`PROV-01` to `PROV-60`)
- **Initial State**: Pre-populated
- **Definition**: Unique identifier for the audit record, formatted sequentially with leading zero.

#### Column 2: `dataset_name`
- **Data Type**: Enum (`HadithDB`, `Shamela4`)
- **Initial State**: Pre-populated
- **Definition**: The source dataset from which the candidate record was extracted. Exactly 30 records originate from HadithDB and 30 from Shamela4.

#### Column 3: `dataset_narrator_id`
- **Data Type**: String / Integer
- **Initial State**: Pre-populated
- **Definition**: The primary key / identifier of the narrator in the source dataset (`id` in HadithDB; `id` in Shamela4 `narrators.parquet`).

#### Column 4: `dataset_narrator_name`
- **Data Type**: String (Arabic)
- **Initial State**: Pre-populated
- **Definition**: The name string stored in the source dataset (`name` in HadithDB; `short_name` or `long_name` in Shamela4).

#### Column 5: `candidate_grade_field`
- **Data Type**: String
- **Initial State**: Pre-populated (`الرتبة عند ابن حجر`)
- **Definition**: The exact field name in the dataset designated as Ibn Hajar's grade.

#### Column 6: `candidate_grade_verbatim`
- **Data Type**: String (Arabic)
- **Initial State**: Pre-populated
- **Definition**: The exact verbatim string extracted from `candidate_grade_field` without any modification, truncation, or normalization.

#### Column 7: `candidate_grade_source_location`
- **Data Type**: String
- **Initial State**: Pre-populated
- **Definition**: The JSON or schema path to the field (e.g. `data["الرتبة عند ابن حجر"]` for HadithDB; `biography_text["summary"]["الرتبة عند ابن حجر"]` for Shamela4).

#### Columns 8 to 13: Diagnostic Boolean Flags
- `flag_conventional_grade`: String (`TRUE`, `FALSE`)
- `flag_compound_qualified_grade`: String (`TRUE`, `FALSE`)
- `flag_descriptive_non_grade`: String (`TRUE`, `FALSE`)
- `flag_explicit_attributed_quote`: String (`TRUE`, `FALSE`)
- `flag_criticism_text_overlap`: String (`TRUE`, `FALSE`)
- `flag_ambiguous_truncated_editorial`: String (`TRUE`, `FALSE`)
- **Initial State**: Pre-populated
- **Definition**: Evaluates whether the candidate grade exhibits each diagnostic condition.

#### Column 14: `diagnostic_flags_summary`
- **Data Type**: String
- **Initial State**: Pre-populated
- **Definition**: Semicolon-separated list of active diagnostic flags for rapid human reference (e.g. `conventional; compound; overlap`).

---

### 3.2 Human Audit Fields: Taqrib Verification (Columns 15 to 22)

All columns in this section are **strictly empty (`""`)** in the initial worksheet.

#### Column 15: `taqrib_entry_number`
- **Data Type**: Integer / Empty
- **Allowed Values**: Positive integer matching the entry number in *Taqrib al-Tahdhib* (e.g. `3320`, `13`, `7837`), or `not_found`.
- **Definition**: The numerical identifier assigned to the biography entry in the printed edition and in Book ID 3076.

#### Column 16: `taqrib_printed_page`
- **Data Type**: Integer / Empty
- **Allowed Values**: Page number in Book ID 3076 / Awwamah edition (e.g. `303`, `78`, `487`), or `not_found`.
- **Definition**: The page number where the biographical entry begins.

#### Column 17: `taqrib_entry_name_verbatim`
- **Data Type**: String (Arabic) / Empty
- **Definition**: The full name, lineage, nisbah, and kunyah of the narrator as printed at the head of the entry in *Taqrib*.

#### Column 18: `taqrib_grade_verbatim`
- **Data Type**: String (Arabic) / Empty
- **Definition**: The primary grade words recorded by Ibn Hajar in the entry (e.g. `ثقة حافظ فقيه`, `صدوق يهم`, `مقبول`, `ضعيف`).

#### Column 19: `taqrib_qualification_verbatim`
- **Data Type**: String (Arabic) / Empty
- **Definition**: Any secondary qualifications, conditions, chronological restrictions, or sectarian notes recorded by Ibn Hajar (e.g. `أجل أصحاب ابن عيينة`, `تغير بأخرة`, `رمي بالتشيع`, `له أفراد`). If none, enter `none`.

#### Column 20: `taqrib_rank_number`
- **Data Type**: String / Empty
- **Allowed Values**: `Rank 1` through `Rank 12` matching Ibn Hajar's authentic 12 ranks (from `PROVENANCE_AND_TEMPORAL_FIREWALL_SPEC.md`), or `unranked`, `composite`, `not_found`.
- **Definition**: The corresponding rank number among Ibn Hajar's 12 hierarchical tiers.

#### Column 21: `taqrib_identity_match_status`
- **Data Type**: Enum / Empty
- **Allowed Values**:
  - `exact_match`: Full name, lineage, generation, and teacher/student circle match exactly.
  - `variant_spelling`: Minor orthographic or patronymic difference, but confirmed to be the identical biographical subject.
  - `conflicting_identity`: The dataset record matches a homonym or distinct narrator with a similar name.
  - `unresolved`: Ambiguous evidence; multiple plausible candidates exist.
  - `not_in_taqrib`: The narrator does not appear in *Taqrib al-Tahdhib* (e.g. outside the Six Books).

#### Column 22: `taqrib_text_match_status`
- **Data Type**: Enum / Empty
- **Allowed Values**:
  - `exact_verbatim`: Stored grade matches the printed *Taqrib* text letter-for-letter (ignoring punctuation).
  - `minor_variation`: Minor word order change, missing particle, or slight orthographic shift that does not alter meaning.
  - `substantial_difference`: Stored grade omits crucial qualifications, adds words not in *Taqrib*, or substitutes different terms.
  - `not_found`: The stored text does not correspond to any passage in the *Taqrib* entry.

---

### 3.3 Human Audit Fields: Attribution Verification (Columns 23 to 29)

#### Column 23: `assessment_author`
- **Data Type**: String / Empty
- **Allowed Values**: `Ibn Hajar`, `Abu Hatim al-Razi`, `Ahmad ibn Hanbal`, `Yahya ibn Ma'in`, `Al-Dhahabi`, `Al-Ijli`, `Ibn Hibban`, `Al-Bukhari`, `Al-Nasa'i`, `Modern Editor`, `Multiple Authors`, `Unclear`.
- **Definition**: The historical individual or modern editor who actually formulated the evaluative statement.

#### Column 24: `assessment_attribution_status`
- **Data Type**: Enum / Empty
- **Allowed Values**:
  - `directly_transmitted_historical_judgment`: Early critic evaluation within the provisional T <= 365 AH operational boundary, transmitted with direct isnad or in a primary early witness.
  - `traceable_intermediary_historical_judgment`: Early critic evaluation quoted through a traceable intermediary compiler citing an identifiable source or chain.
  - `insufficient_evidence_historical_judgment`: Early critic evaluation lacking clear intermediary transmission or source evidence.
  - `compiler_own_synthesis`: Post-365 AH compiler's own synthesized assessment (e.g. Ibn Hajar 852 AH in Taqrib).
  - `modern_editorial_material`: Text added by modern editors, footnote annotators, or bracketed corrections.

#### Column 25: `compiler_or_transmitter`
- **Data Type**: String / Empty
- **Allowed Values**: `Ibn Hajar`, `Al-Mizzi`, `Ibn Abi Hatim`, `Al-Dhahabi`, `Al-Khatib al-Baghdadi`, `N/A`.
- **Definition**: The compiler or intermediary author through whose surviving work the statement was transmitted.

#### Column 26: `editorial_material_status`
- **Data Type**: Enum / Empty
- **Allowed Values**:
  - `none`: Text is purely classical compilation text.
  - `bracketed_addition`: Text contains modern editor additions in square brackets `[...]`.
  - `editorial_footnote`: Text is taken from a modern editorial footnote or marginal apparatus.
  - `modern_editor_reassessment`: Text represents a modern editorial dispute or commentary (e.g. Tahrir al-Taqrib).

#### Column 27: `attribution_evidence_verbatim`
- **Data Type**: String (Arabic) / Empty
- **Definition**: Verbatim excerpt from the entry or footnote supporting the attribution classification.

#### Column 28: `source_locator`
- **Data Type**: String / Empty
- **Definition**: Specific citation string (e.g. `Taqrib 1/303 entry 3320`, `Tahdhib al-Kamal 14/512`, `al-Jarh wa al-Ta'dil 5/56`).

#### Column 29: `source_verification_status`
- **Data Type**: Enum / Empty
- **Allowed Values**:
  - `verified_in_corpus`: Verified directly against downloaded reference corpus files (Book ID 3076, 1716, etc.).
  - `verified_in_external_edition`: Verified in reputable printed edition outside the immediate repository files.
  - `unverified`: Could not be located or confirmed.
  - `contradicted`: Disproved by primary text collation.

---

### 3.4 Human Audit Fields: Three Validity Dimensions (Columns 30 to 32)

#### Column 30: `textual_fidelity`
- **Data Type**: Enum / Empty
- **Allowed Values**: `high`, `moderate`, `low`, `failed`, `unresolved`.
- **Criteria**:
  - `high`: Exact verbatim match or negligible whitespace difference with *Taqrib*.
  - `moderate`: Minor differences in particles or syntax; core grade and conditions fully intact.
  - `low`: Substantial truncation, omitted conditions, or spliced fragments.
  - `failed`: Fabricated, completely different grade, or not present in *Taqrib*.
  - `unresolved`: Textual ambiguity prevents conclusive determination.

#### Column 31: `attribution_fidelity`
- **Data Type**: Enum / Empty
- **Allowed Values**: `high`, `moderate`, `low`, `failed`, `unresolved`.
- **Criteria**:
  - `high`: Genuinely represents Ibn Hajar's own standardized appraisal in *Taqrib*.
  - `moderate`: Attributed to Ibn Hajar, but quotes an earlier critic as the sole justification.
  - `low`: An earlier critic's quote wrongly labeled as Ibn Hajar's personal grade.
  - `failed`: Modern editorial note, compiler note from someone else, or misattributed quote.
  - `unresolved`: Author cannot be definitively established.

#### Column 32: `identity_fidelity`
- **Data Type**: Enum / Empty
- **Allowed Values**: `high`, `moderate`, `low`, `failed`, `unresolved`.
- **Criteria**:
  - `high`: Verified beyond doubt as the same individual (matching lineage, tabaqah, death date, transmitters).
  - `moderate`: High likelihood of identity, but minor variations in kunyah or patronymic.
  - `low`: Multiple homonymous candidates exist; differentiation is uncertain.
  - `failed`: Clear narrator collision / identity mismatch (grade of narrator A assigned to narrator B).
  - `unresolved`: Insufficient biographical details to adjudicate identity.

---

### 3.5 Human Audit Fields: Final Disposition & Eligibility (Columns 33 to 37)

#### Column 33: `record_disposition`
- **Data Type**: Enum / Empty
- **Allowed Values**:
  - `verified_ibn_hajar_assessment`: Textually and biographically verified as Ibn Hajar's authentic standardized appraisal in *Taqrib al-Tahdhib*. Confirms source and attribution fidelity; does not pre-judge construct validity or machine-learning target suitability.
  - `excluded_not_a_grade`: The stored value is a biographical, generational, or honorific description (e.g. `صحابي`, `أمير المؤمنين`, `فقيه`) rather than a reliability grade.
  - `excluded_not_ibn_hajar`: The stored value is an attributed quotation from an earlier critic (e.g. `وثقه ابن معين`, `قال أبو حاتم`), not Ibn Hajar's own appraisal.
  - `excluded_editorial_material`: The stored value originates from modern editorial notes, brackets, or footnote disputes.
  - `excluded_identity_mismatch`: The dataset record does not match the historical subject in *Taqrib*.
  - `excluded_textual_corruption`: Severe textual distortion, garbling, or truncation making evaluation impossible.
  - `quarantined_unattributed_synthesis`: A synthesized assessment or compiler summary whose textual witness or attribution cannot be confirmed in *Taqrib*.
  - `quarantined_uncertain`: Unresolved identity, attribution, or textual discrepancies requiring further scholarly collation.

#### Column 34: `input_eligibility`
- **Data Type**: Enum / Empty
- **Allowed Values**:
  - `eligible_historical_input`: Directly transmitted early critic judgments within the provisional T <= 365 AH operational boundary, and traceable intermediary-preserved judgments where attribution and source evidence are verified.
  - `quarantined_intermediary_input`: Intermediary-preserved early critic judgment held in quarantine pending verification of intermediary transmission and source evidence.
  - `quarantined_insufficient_evidence`: Early judgment held in quarantine due to vague, uncorroborated, or disputed transmission evidence.
  - `target_evaluation_only`: Ibn Hajar's own 852 AH synthesis; eligible ONLY as a reference target evaluation for model benchmarking, strictly forbidden as early historical input.
  - `ineligible_compiler_synthesis`: Post-365 AH compilation verdict outside the reference target role; strictly ineligible as early input.
  - `ineligible_editorial_material`: Modern editorial text; strictly ineligible for both input and target.

#### Column 35: `exclusion_or_quarantine_reason`
- **Data Type**: String / Empty
- **Definition**: Terse, precise rationale if quarantined or excluded (e.g. `grade is verbatim quote from Abu Hatim in Jarh wa Ta'dil, not Ibn Hajar's own judgment`). If verified, enter `none`.

#### Column 36: `reviewer_notes`
- **Data Type**: String / Empty
- **Definition**: Optional free-text notes, observations on editorial anomalies, or cross-references to other biographical works.

#### Column 37: `corroboration_status`
- **Data Type**: Enum / Empty
- **Allowed Values**: `independent_corroboration`, `dependent_corroboration`, `unresolved_corroboration`.
- **Definition**: Relationship between the passage and any proposed corroborating source or witness. Use `independent_corroboration` only where a separately traceable source or transmission route is supported. Use `dependent_corroboration` where a later compilation reproduces an earlier source or compilation. Use `unresolved_corroboration` where dependence cannot be established. Do not infer independence from a count of compilations.

---

## 4. Invariant Rules and Compliance Checks

1. **Zero Raw Data Tampering**: Never modify `data/1_raw/hadithdb/narrators_db.json`, `data/1_raw/Shamela4_Full_DB/_meta/narrators.parquet`, or any files in `data/1_raw/`.
2. **Zero Forbidden Dashes**: Strictly ZERO em-dash (`\u2014`) and ZERO en-dash (`\u2013`) across all files, code, comments, tables, and notes. Use standard ASCII `-`.
3. **Blank Initial Fields**: All human audit fields (columns 15 to 37) must remain strictly blank in the generated template until audited.
4. **No Git Commit/Push**: Do not stage, commit, or push files without explicit user instruction.
