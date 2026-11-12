# Ibn Hajar Grade Provenance Investigation Protocol

## 1. Protocol Overview and Scope

This protocol specifies the standard operating procedure (SOP) for conducting human source collation on the 60 candidate records in:

`dataset_discovery/target_feasibility/IBN_HAJAR_GRADE_PROVENANCE_WORKSHEET.csv`

The purpose of this investigation is to check source text, attribution, and narrator identity for candidate strings stored under `الرتبة عند ابن حجر` in HadithDB and Shamela4 against ***Taqrib al-Tahdhib***. It does not establish objective narrator reliability or automatically qualify a record as a model target or historical input.

### 1.1 Construct Validity Boundary
Textual and biographical verification establishes that an entry has been faithfully transcribed and correctly attributed to Ibn Hajar. **It does not independently establish construct validity or target ground-truth suitability for machine learning.** Verified records reflect Ibn Hajar's 9th-century Hijri synthesis and are categorized as reference evaluation candidates, not unquestioned historical consensus.

---

## 2. Purposive Sample and Count Interpretation

The 60 records are a purposive, quota-based diagnostic stress test, not a representative sample. Sample flag counts and overlap proportions describe only the selected records; they cannot estimate population prevalence or dataset-wide error rates. Population flag counts in the manifest are descriptive diagnostics computed over each full candidate pool, not estimates of annotation error.

Primary selection categories count which selection pass selected a record. Row-level diagnostic counts recompute non-exclusive Boolean flag combinations. Thus `attributed_pure` has 6 primary allocations while 12 records satisfy the row-level condition `flag_explicit_attributed_quote = TRUE` and `flag_conventional_grade = FALSE`; similarly, `descriptive_pure` has 6 primary allocations while 12 satisfy the corresponding descriptive condition. General-pass selections may also satisfy these row-level conditions.

The operational uncomplicated conventional-grade baseline is: `flag_conventional_grade = TRUE` AND `flag_compound_qualified_grade = FALSE` AND `flag_descriptive_non_grade = FALSE` AND `flag_explicit_attributed_quote = FALSE` AND `flag_ambiguous_truncated_editorial = FALSE`. Criticism-text overlap may remain, so this is not a leakage-clean category. This Boolean yields 16 sample records. Adding `flag_criticism_text_overlap = FALSE` yields 10. The primary selection quota allocated 8 records to this category. All are selected-sample counts only.

## 3. Reference Corpus Specifications

### 3.1 Primary Target Reference Work
- **Title**: *Taqrib al-Tahdhib* (تقريب التهذيب)
- **Author**: Shihab al-Din Abu al-Fadl Ahmad ibn Ali ibn Muhammad al-Kinani al-Asqalani (Ibn Hajar, 773-852 AH)
- **Editor**: Shaykh Muhammad Awwamah
- **Repository Book ID**: `3076`
- **Location on Disk**: `data/1_raw/Shamela4_Full_DB/26__التراجم-والطبقات/3076__تقريب-التهذيب/`
- **Primary Collation File**: `pages.jsonl` (contains entry text with page and part numbers)

### 3.2 Secondary and Contextual References
- **Tahdhib al-Kamal fi Asma al-Rijal** by Jamal al-Din al-Mizzi (d. 742 AH), edited by Dr Bashshar Awwad Ma'ruf (Book ID `1716`). Used when verifying whether a quoted judgment was transmitted via al-Mizzi.
- **Kitab al-Jarh wa al-Ta'dil** by Ibn Abi Hatim al-Razi (d. 327 AH), Book ID `1711`. Used when verifying directly transmitted early critic judgments (within the provisional T <= 365 AH operational boundary).
- **Tahrir Taqrib al-Tahdhib** by Dr Bashshar Awwad Ma'ruf and Shu'ayb al-Arna'ut. Used exclusively for cross-checking modern editorial variants and reassessments.

---

## 4. Navigation and Lookup Procedure in Taqrib al-Tahdhib

Biographical entries in *Taqrib al-Tahdhib* are arranged systematically according to the following conventions:

### 4.1 Entry Structure
Each biographical notice begins with a sequential entry number in Arabic-Indic numerals, followed by the narrator's name, patronymic, kunyah, descriptive titles, tabaqah (generational tier), reliability appraisal, death date, and canonical transmission symbols:

```
[Entry Number]- [Full Name & Lineage] [Kunyah/Nisbah] [Appraisal / Grade] [Tabaqah] [Death Date] [Symbols]
```

*Example (Entry 3320, Page 303):*
```
٣٣٢٠- عبد الله ابن الزبير ابن عيسى القرشي الأسدي الحميدي المكي أبو بكر ثقة حافظ فقيه أجل أصحاب ابن عيينة من العاشرة مات بمكة سنة تسع عشرة وقيل بعدها... خ م د ت س فق
```

### 4.2 Finding Entries in pages.jsonl
To inspect an entry in the downloaded corpus:
1. Locate the entry by searching `pages.jsonl` using Python or standard search tools.
2. Search primarily by proper name and prominent patronymic (e.g. `عبد الله ابن الزبير`).
3. Note that Shamela transcriptions frequently represent the patronymic particle as `ابن` rather than `بن`.
4. If a narrator is renowned by a kunyah (e.g. `أبو هريرة`), check the *Kunā* section towards the end of the text (around pages 620-680).
5. Female narrators are grouped in the *Kitab al-Nisa'* at the conclusion of the work (pages 740-760).

---

## 5. Five-Phase Human Collation Workflow

For each of the 60 records in `IBN_HAJAR_GRADE_PROVENANCE_WORKSHEET.csv`, the reviewer executes the following five phases:

```
+-------------------------------------------------------------------------------+
|                        FIVE-PHASE REVIEW WORKFLOW                             |
+-------------------------------------------------------------------------------+
| Phase 1: Identity Reconciliation    -> Verify same historical individual      |
| Phase 2: Textual Collation          -> Collate grade wording letter-for-letter|
| Phase 3: Attribution Analysis       -> Apply Safeguard 1 firewall             |
| Phase 4: Validity Grading           -> Assign textual/attribution/identity    |
| Phase 5: Final Disposition          -> Set disposition and input eligibility  |
+-------------------------------------------------------------------------------+
```

### Phase 1: Identity Reconciliation
1. Compare `dataset_narrator_name` against the *Taqrib* heading.
2. Confirm biographical indicators:
   - Father's and grandfather's names.
   - Tribal, regional, or occupational nisbah (e.g. `الحميدي`, `القرشي`, `الأسدي`, `البصري`).
   - Generation / tabaqah number (1 to 12).
   - Death year (Hijri date).
   - Prominent teachers and students.
3. Record `taqrib_entry_number`, `taqrib_printed_page`, and `taqrib_entry_name_verbatim`.
4. Select `taqrib_identity_match_status`:
   - `exact_match`: All indicators align perfectly.
   - `variant_spelling`: Identical subject with minor orthographic variation.
   - `conflicting_identity`: Dataset record conflates two distinct historical persons.
   - `unresolved`: Evidence is insufficient to differentiate candidates.
   - `not_in_taqrib`: The narrator is absent from *Taqrib*.

### Phase 2: Textual Collation
1. Read the complete text of the *Taqrib* entry.
2. Identify the evaluative judgment string.
3. Transcribe the primary grade terms into `taqrib_grade_verbatim`.
4. Transcribe any qualifying conditions (e.g. `تغير بأخرة`, `له أفراد`, `أجل أصحاب ابن عيينة`) into `taqrib_qualification_verbatim`.
5. Identify the rank tier from Ibn Hajar's authentic 12 ranks and enter into `taqrib_rank_number` (e.g. `Rank 2`, `Rank 3`, `Rank 6`).
6. Compare `candidate_grade_verbatim` with `taqrib_grade_verbatim` and select `taqrib_text_match_status`:
   - `exact_verbatim`
   - `minor_variation`
   - `substantial_difference`
   - `not_found`

### Phase 3: Attribution Analysis (Safeguard 1)
1. Scrutinize the statement to identify the true author:
   - Does Ibn Hajar pronounce this judgment in his own voice (`compiler_own_synthesis`)?
   - Does the entry quote an earlier critic (e.g. `وثقه العجلي`, `قال ابن معين`, `قال أبو حاتم`) through a traceable transmission path (`traceable_intermediary_historical_judgment`)?
   - Does the entry cite an unattributed or vague report (`insufficient_evidence_historical_judgment`)?
   - Does the text originate in a modern editor's bracket or footnote (`modern_editorial_material`)?
2. Record `assessment_author` (e.g. `Ibn Hajar`, `Al-Ijli`, `Abu Hatim`).
3. Select `assessment_attribution_status`:
   - `directly_transmitted_historical_judgment`
   - `traceable_intermediary_historical_judgment`
   - `insufficient_evidence_historical_judgment`
   - `compiler_own_synthesis`
   - `modern_editorial_material`
4. Record `compiler_or_transmitter` (e.g. `Ibn Hajar`, `Al-Mizzi`, `Ibn Abi Hatim`, `N/A`).
5. Select `editorial_material_status` (`none`, `bracketed_addition`, `editorial_footnote`, `modern_editor_reassessment`).
6. Paste the supporting Arabic text into `attribution_evidence_verbatim`.
7. Enter the exact volume and page into `source_locator`.
8. Set `source_verification_status` (`verified_in_corpus`, `verified_in_external_edition`, `unverified`, `contradicted`).

### Phase 4: Validity Grading
Assign three discrete fidelity grades (`high`, `moderate`, `low`, `failed`, `unresolved`):
- `textual_fidelity`: Degree of verbatim preservation of the *Taqrib* text.
- `attribution_fidelity`: Validity of attributing the grade to Ibn Hajar.
- `identity_fidelity`: Confidence in narrator identity match.

### Phase 5: Final Disposition & Input Eligibility
1. Assess `record_disposition` as the target-candidate decision only:
   - `verified_ibn_hajar_assessment`: Confirmed authentic standardized appraisal in *Taqrib al-Tahdhib*.
   - `excluded_not_a_grade`: Biographical, generational, or honorific description rather than a reliability grade.
   - `excluded_not_ibn_hajar`: Attributed quotation from an earlier critic, not Ibn Hajar's own appraisal.
   - `excluded_editorial_material`: Text originating from modern editorial notes or apparatus.
   - `excluded_identity_mismatch`: Narrator mismatch / homonym confusion.
   - `excluded_textual_corruption`: Severe textual corruption or garbling.
   - `quarantined_unattributed_synthesis`: Compiler summary whose textual witness cannot be confirmed in *Taqrib*.
   - `quarantined_uncertain`: Unresolved textual or attribution ambiguity.
2. Independently assess `input_eligibility` according to Safeguard 1. Do not derive it from `record_disposition`:
   - `eligible_historical_input`: Directly transmitted early critic judgments within the provisional T <= 365 AH operational boundary, and traceable intermediary-preserved judgments where attribution and source evidence are verified.
   - `quarantined_intermediary_input`: Intermediary-preserved early critic judgment held in quarantine pending verification.
   - `quarantined_insufficient_evidence`: Early judgment held in quarantine due to vague or disputed transmission evidence.
   - `target_evaluation_only`: Ibn Hajar's own 852 AH synthesis. Valid as target reference; strictly forbidden as early historical input.
   - `ineligible_compiler_synthesis`: Post-boundary compiler synthesis; not eligible under the provisional input rule.
   - `ineligible_editorial_material`: Modern editorial text; forbidden for both input and target.
3. If quarantined or excluded, document the exact reason in `exclusion_or_quarantine_reason`.
4. Provide any contextual remarks in `reviewer_notes`.

---

## 6. Moving Intermediary Judgments from Quarantine to Eligibility

A traceable intermediary-preserved judgment may be considered for historical input eligibility only after its attribution, transmission path, source evidence, and editorial integrity have been reviewed. Record corroboration as one of:

- `independent_corroboration`: a separately traceable source or transmission route supports the passage.
- `dependent_corroboration`: a later compilation reproduces an earlier source or compilation; this is not independent confirmation.
- `unresolved_corroboration`: the dependence relationship cannot be established.

Do not infer independence from the number of compilations. Do not require a physical manuscript witness dated before 365 AH as an absolute rule. Assess surviving evidence, the traceable route, and uncertainty.

The project's `T <= 365 AH` boundary is a provisional operational inclusion rule requiring historical justification, not a universal historical division. Keep these dates distinct: (1) critic lifespan and death; (2) approximate judgment date, if known; (3) source-work composition date; (4) surviving manuscript or textual-witness date; and (5) modern editor and edition date. Do not infer the judgment date from the critic's death, or witness date from work composition.

Keep verification dimensions independent: textual fidelity, attribution fidelity, narrator identity resolution, historical input eligibility, target-candidate suitability, and construct validity. `record_disposition` is a target-candidate disposition, not an input-eligibility decision. A verified Ibn Hajar assessment is not automatically a valid historical input; an attributed early judgment is not automatically eligible without provenance verification; and a verified target candidate does not establish construct validity.

## 7. Date and Corroboration Recording Rules

Use `corroboration_status` as follows:

- `independent_corroboration`: a separately traceable source or transmission route supports the passage.
- `dependent_corroboration`: a later compilation reproduces an earlier source or compilation.
- `unresolved_corroboration`: source dependence cannot be established.

Multiple compilations do not by themselves demonstrate independent corroboration. A physical manuscript witness dated before 365 AH is not an absolute requirement; assess the surviving evidence and record uncertainty.

Keep five dates distinct: critic lifespan and death; approximate judgment date if known; source-work composition date; surviving manuscript or textual-witness date; and modern editor/edition date. Do not infer judgment date from death date or witness date from work composition date. The `T <= 365 AH` boundary is a provisional operational inclusion rule requiring historical justification, not a universal historical division.

The review dimensions are separate: textual fidelity, attribution fidelity, narrator identity resolution, historical input eligibility, target-candidate suitability, and construct validity. A verified Ibn Hajar assessment is not automatically a valid historical input. An attributed early judgment needs provenance verification before eligibility. Verification of a target candidate does not establish construct validity. `record_disposition` addresses target-candidate status; `input_eligibility` addresses a separate decision.

## 7. Methodological Limitations and Blinding Note

1. **Single-Reviewer Limitation**: Initial completion of this worksheet by a single reviewer serves as a preliminary diagnostic benchmark. It does not establish formal inter-annotator agreement (IAA / Cohen's Kappa).
2. **Second-Pass Verification Requirement**: Before final inclusion in thesis chapters or formal empirical evaluation benchmarks, an independent second-pass annotation of a blinded subset must be conducted by a qualified independent reviewer to quantify inter-annotator agreement.
3. **Audit Trail Immutability**: The initial worksheet template must preserve empty human review fields until formal review commences. All completed review versions must be preserved with timestamps and Git tracking.
