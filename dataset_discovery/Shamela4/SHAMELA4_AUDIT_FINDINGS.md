# Shamela4 Narrator Corpus — Discovery and Audit Findings

**Status:** Candidate corpus under audit; not approved for modelling  
**Dataset:** AuthenticIlm/Shamela4_Full_DB, file _meta/narrators.parquet  
**Repository snapshot reviewed:** 34a787b (2026-11-09)  
**Research context:** FYP2 rebuild; Evaluative Stance Analysis (ESA) and narrator-level reliability analysis

> This document consolidates exploratory findings reported in prior conversations and local audit outputs. The figures below are historical observations, not all independently regenerated in this environment. The accompanying audit script is intended to regenerate structural counts and exports. Manual findings and unresolved questions are labelled accordingly.

## 1. Executive assessment

Shamela4 is currently the leading candidate for the primary narrator-evidence corpus because it combines narrator profiles, grouped critical quotations (garh), analytical evidence (fwaed), citation strings, and source identifiers. It is not yet a validated gold-standard dataset.

The research opportunity is to construct a provenance-aware evidence representation that separates:
1. narrator identity and biographical profile;
2. a documentary quotation occurrence;
3. the historical speaker or critic to whom a judgement is attributed;
4. the compiler or author transmitting that judgement;
5. the source work and locator;
6. the evaluative content and its target.

A group label is not automatically proof of the historical speaker. A quotation occurrence is not automatically one independent evaluation. Existing grades are not automatically valid targets or permissible input features.

**Current decision:** continue auditing Shamela as a promising candidate. Do not begin model training, graph construction, or target-label mapping until source semantics, attribution, identity resolution, and target provenance have been investigated.

## 2. Dataset identity and Parquet schema

Local path: data/1_raw/Shamela4_Full_DB/_meta/narrators.parquet

Reported Parquet metadata:

| Property | Observed value |
|---|---:|
| Rows | 18,989 |
| Row groups | 1 |
| Columns | 6 |
| File size | 7,963,509 bytes (~7.96 MB) |

| Field | Type | Notes |
|---|---|---|
| id | int64, nullable | Dataset narrator record identifier |
| short_name | binary / large_string | Arabic short name |
| long_name | binary / large_string | Arabic long name |
| narrator_type | int64, nullable | Semantics unresolved; appears associated with death-year metadata |
| biography_text | binary / large_string | JSON-encoded biography object stored as a string |
| criticism_text | binary / large_string | JSON-encoded criticism object stored as a string |

The two *_text columns are JSON-encoded strings, not native nested Parquet structures. Parse them separately and count malformed/null cases rather than silently discarding them.

### 2.1 Biography fields observed

Arabic keys seen include:
- النسب — lineage / attribution information
- الكنية — kunya
- تاريخ الوفاة — death-date information
- الرتبة عند ابن حجر — Ibn Hajar assessment
- طبقة رواة التقريب — Taqrīb narrator class / generation field
- علاقات الراوي — narrator relationships
- الرتبة عند الذهبي — al-Dhahabi assessment
- بلد الإقامة, بلد الوفاة, بلد الرحلة, بلد الميلاد
- تاريخ الميلاد, تاريخ الرحلة
- اللقب, الشهرة, المذهب العقدي

The biography object also contains a summary list in observed records. Do not assume all records share identical keys or nested structures.

### 2.2 Criticism object

Observed criticism structure includes:
- ghar: quotation/evaluation material grouped under evaluator-like names;
- fwaed: analytical material grouped under subject/category labels.

In observed ghar entries, a quotation was represented as a three-element sequence:

[quotation_text, source_work_and_volume_page, source_identifier]

This is an observed pattern, not a guaranteed schema invariant. Preserve raw values and report unexpected shapes.

## 3. Coverage and missingness — previous local audit

Reported full-corpus counts:

| Measure | Count |
|---|---:|
| Narrator records | 18,989 |
| Valid biography JSON | 18,989 |
| Valid criticism JSON | 15,160 |
| Null criticism text | 3,829 |
| Null narrator_type | 9,799 |
| ghar quotation occurrences | 165,862 |
| ghar evaluator-group appearances | 87,696 |
| Distinct evaluator strings | 2,821 |
| Distinct exact source citation strings | 31,696 |
| Unique source identifiers | 54,334 |

The 87,696 evaluator-group appearances are group appearances across narrator records, not unique critics or independent judgements. The 31,696 citation strings include volume/page variants and must not be described as 31,696 distinct source works.

### 3.1 Biography-field coverage

| Field | Records |
|---|---:|
| النسب | 16,885 |
| الكنية | 10,323 |
| تاريخ الوفاة | 9,499 |
| الرتبة عند ابن حجر | 8,185 |
| طبقة رواة التقريب | 8,178 |
| علاقات الراوي | 7,492 |
| الرتبة عند الذهبي | 5,370 |
| بلد الإقامة | 4,326 |
| بلد الوفاة | 2,057 |
| اللقب | 1,733 |
| بلد الرحلة | 1,699 |
| تاريخ الميلاد | 1,429 |
| الشهرة | 1,291 |
| المذهب العقدي | 936 |
| بلد الميلاد | 240 |
| تاريخ الرحلة | 211 |

### 3.2 Existing assessment coverage

Ibn Hajar field:
- Present for 8,185 / 18,989 records (43.1%).
- 1,343 distinct raw strings reported.
- Frequent strings: ثقة (1,411), مقبول (1,255), صدوق (876), مجهول (522), صحابي (355), ضعيف (295).

Al-Dhahabi field:
- Present for 5,370 / 18,989 records (28.3%).
- 1,694 distinct raw strings reported.
- Frequent strings: ثقة (968), وثق (673), صدوق (292), صحابي (194), له صحبة (140).

These are raw-string frequencies, not validated reliability classes. صحابي is a status; حافظ and عابد may describe attributes; مقبول in Taqrīb has a technical meaning. Do not map strings directly into a simple ordinal scale without a source-grounded protocol.

### 3.3 Evaluator-group frequency

The previous audit reported 2,821 distinct evaluator strings. Frequent labels included Ibn Hajar, Ibn Hibban, al-Dhahabi, Abu Hatim al-Razi, Yahya ibn Ma'in, al-Nasa'i, al-Bukhari, al-Mizzi, al-Daraqutni, al-Hakim, Ahmad ibn Hanbal, Ibn 'Adi, Abu Zur'ah al-Razi, al-'Ijli, Muhammad ibn Sa'd, Abu Dawud, Ibn Khalfun, al-'Uqayli, al-Khatib al-Baghdadi, and Ibn Abi Hatim.

These are labels used by the dataset grouping mechanism, not a verified critic registry.

## 4. Preliminary interpretation of narrator_type

A previous comparison found 9,190 records with both narrator_type and death-date metadata. Examples:
- narrator_type=220 with death date 220 AH, possibly 221 AH;
- narrator_type=131 with death range 131–140 AH;
- narrator_type=51 with death range 51–60 AH;
- narrator_type=153 with death date 153 AH.

This suggests narrator_type may encode a death-year value, perhaps a representative year or bucket. Its exact semantics remain **unverified**. Do not treat it as narrator type, tabaqah, or a clean death-year label until edge cases and upstream documentation are checked.

## 5. Quotation duplication and occurrence semantics

Previous exact-text audit:

| Measure | Count |
|---|---:|
| ghar quotation occurrences | 165,862 |
| Unique exact quotation strings | 108,904 |
| Repeated exact quotation strings | 16,504 |
| Occurrences belonging to repeated-string clusters | 73,462 |

Repeated text is not automatically erroneous. A formula such as قال أبو داود: ثقة may legitimately apply to multiple narrators. The same historical judgement may also be reproduced in multiple later works.

A previous mutually prioritised pattern classification reported:

| Pattern | Repeated-string clusters |
|---|---:|
| Same narrator, multiple evaluator groups | 10,892 |
| Multiple narrators | 4,123 |
| Same narrator/evaluator, multiple sources | 961 |
| Same narrator/evaluator/source ID | 528 |

These are counts of repeated quotation strings assigned to one prioritised category, not counts of occurrences or independent historical evaluations. The categories can overlap conceptually; classification priority determines the displayed bucket.

### 5.1 Exact documentary-entry duplicates

A later audit grouped entries by narrator, evaluator group, exact quotation, and source identifier:
- Unique combinations: 164,985
- Combinations occurring more than once: 734
- Excess duplicate occurrences: 877

The 877 excess occurrences are approximately 0.53% of 165,862 quotation occurrences. This is a small but non-zero extraction/indexing duplication signal. Preserve the raw corpus; flag duplicates in derived outputs. Do not delete them automatically.

### 5.2 Same passage assigned to multiple evaluator groups

A separate audit found 11,900 cases where the same narrator + exact quotation + source identifier was assigned to more than one evaluator group.

Examples included a passage associated with narrator ID 3 assigned to both Adam ibn Abi Iyas and Ahmad ibn Hanbal; another passage assigned to Ibn Hibban, al-Hakim, and al-'Ijli; and passages about several transmitters or scholars assigned to multiple group labels.

This is strong evidence that the group label cannot safely be interpreted as the one actual historical speaker. It may reflect a named person mentioned in the passage, an index key, an evaluator association, or a compiler-derived grouping. The exact mechanism remains unresolved.

### 5.3 Long and compound passages

Some quotation strings contain multiple statements, nested attributions, several transmitters, comparisons, qualifications, or biographical narrative. One quotation row therefore need not equal one evaluative act. ESA annotation may need clause-level or span-level units, while preserving the complete source passage and its context.

## 6. Source identifiers and citation provenance

Observed citation strings include:
- تهذيب التهذيب (1/ 101)
- الجرح والتعديل لابن أبي حاتم (2/ 268)
- تهذيب الكمال
- الكاشف
- إكمال تهذيب الكمال

Numeric source identifiers (examples: 464600, 685186, 441139) accompany citation strings.

Previous counts: 31,696 distinct exact citation strings and 54,334 unique source identifiers. These figures do **not** establish the identifier-to-work relationship. The source-ID-to-title and title-to-source-ID output was not included in the earlier shared audit output. Unresolved questions:
1. Can one source ID map to multiple normalised work titles?
2. Can one normalised title map to multiple source IDs?
3. Does the ID identify a Shamela book record, edition, volume, or another object?
4. Are title variants due to orthography, edition, or genuinely different works?
5. Can the identifier be resolved against upstream Shamela metadata?

The audit script emits both mappings and collision reports. It cannot independently prove what an ID means without external metadata or source verification.

## 7. fwaed categories

Previous category-frequency output included:

| Category | Count reported |
|---|---:|
| إثبات سماع الراوي | 1,630 |
| الإرسال | 1,571 |
| التوثيق الضمني | 1,442 |
| المفاضلة بين الرواة | 732 |
| الإدراك | 655 |
| الاختلاف في سماع الراوي | 282 |
| التدليس | 159 |
| الاختلاط | 150 |
| التضعيف الاستثنائي | 141 |
| المفاضلة بين الرواة في راو | 121 |
| التضعيف الضمني | 74 |
| التوثيق الاستثنائي | 58 |
| المفاضلة بين الرواة في بلد | 24 |

These were reported as category appearances and must not be treated as counts of independent quotations or narrator judgements until the nested fwaed structure is regenerated and clarified.

Keep fwaed separate from direct jarh/ta'dil statements. Evidence about hearing, irsal, tadlis, ikhtilat, and implicit accreditation may be relevant, but is not interchangeable with a direct reliability grade.

## 8. Research risks and controls

### Attribution risk
Do not equate the ghar group key with the historical speaker. Store it as group_label_raw or candidate_attribution until verified. Human review must identify speaker, quoted speaker, compiler, and evaluated narrator separately.

### Unit-of-analysis risk
Do not assume one quotation record is one evaluation. A long passage may contain multiple evaluative propositions. Preserve the full passage, and create separately annotated spans only after a documented segmentation protocol.

### Duplicate and dependence risk
Do not deduplicate by exact text alone. Repeated text across narrators may be valid; repeated text across works may be copied from one earlier source; repeated identical documentary entries may be extraction duplicates. Preserve occurrence-level provenance and add duplicate flags/clusters.

### Target leakage risk
The biography contains pre-existing Ibn Hajar and al-Dhahabi grades. If either is used as the prediction target, exclude that target field and all direct derivatives or restatements from model inputs. Assess whether ghar passages reproduce the target assessment, whether the target source is represented in the quotation corpus, and whether the source text itself generated the biography field.

A citation to a work is not proof that a quoted statement is the target author's independent judgement. A later compilation may reproduce earlier scholars' statements. Source author, compiler, historical speaker, and target-label authority must remain distinct.

### Identity risk
Do not merge narrators based on name similarity alone. Preserve the Shamela ID as the source-local identifier. Cross-source linking to HadithDB requires explicit evidence and confidence; ambiguous matches remain unresolved.

### Graph semantics risk
Do not infer a teacher–student edge merely because two narrators co-occur in a quotation or hadith chain. Distinguish reported relationship, chain adjacency, direct audition, and uncertain/indirect association. Each graph edge needs provenance and an explicit semantic definition.

## 9. Manual review protocol proposed

Create a stratified review sample including:
- short formulaic judgements;
- positive, negative, qualified, and ambiguous expressions;
- passages assigned to one evaluator group;
- the same passage assigned to two groups;
- passages assigned to three or more groups;
- long passages with nested attributions;
- same quote repeated across narrators;
- same quote repeated across source works;
- same narrator/evaluator/source duplicate entries;
- records with missing criticism or source metadata;
- records containing Ibn Hajar/al-Dhahabi grades and matching quotation text.

For each reviewed passage, record:
1. narrator discussed and identity confidence;
2. actual historical speaker;
3. quoted/intermediate speaker, if any;
4. compiler/author of the source work;
5. exact evaluative span(s);
6. stance and qualification;
7. direct, transmitted, paraphrased, or unclear status;
8. source work, edition, volume/page or stable locator;
9. exact, normalised, truncated, or uncertain transcription;
10. adjudication and reviewer notes.

A pilot sample of around 100 passages is a practical starting point, not a statistically justified final sample size. Revise the annotation guide after the pilot and report inter-annotator agreement if multiple annotators are involved.

## 10. Relationship to HadithDB

HadithDB remains a complementary candidate source; the user explicitly decided to keep its two JSON files in the repository.

Previously reported:
- 1,524 narrator records;
- 40,524 quotation occurrences;
- 35,216 unique exact quotation strings;
- 8,095 citation strings;
- 222 extracted work-title strings;
- 3,639 duplicate exact-text clusters;
- 8,947 occurrences in those clusters.

Duplicate pattern counts:
| Pattern | Clusters |
|---|---:|
| Within record, multiple group labels | 3,240 |
| Cross-record | 268 |
| Within record, same group | 128 |
| Mixed | 3 |

A documented example showed one passage about Idris ibn Abd al-Karim al-Muqri' and Ahmad ibn Hanbal duplicated under 19 group labels. Group keys therefore cannot automatically be interpreted as independent evaluators.

HadithDB's الجرح والتعديل structure groups plain quotation strings under scholar-like keys, with citations embedded in text and no separate citation metadata. Its quotation collection is not automatically gold-standard evaluator-attribution data.

The prior comparison of HadithDB Ibn Hajar and al-Dhahabi fields found 1,156 records in both, 352 only Ibn Hajar, 9 only al-Dhahabi, and 7 neither. Exact/normalised string agreement was 204 (17.65% of the overlap). This is not evidence that the scholars disagreed in 82.35% of cases; the fields may differ in purpose, granularity, and content.

Prior HadithDB leakage audit found many target strings repeated in quotations, including in Taqrīb-citing material. These were substring matches and citation associations, not proof that every matching passage was an independent evaluation or that every non-Taqrīb match was leakage. Source-level review is required.

## 11. Current research decisions

1. Shamela is the leading candidate evidence corpus, but remains under audit.
2. HadithDB is retained as a complementary corpus; its raw files remain tracked by explicit user decision.
3. Preserve raw datasets and quotation occurrences. Do not overwrite or destructively deduplicate.
4. Treat group labels as candidate attribution metadata, not verified historical speakers.
5. Treat source IDs as opaque identifiers until mapped and verified.
6. Keep ghar and fwaed conceptually separate.
7. Do not map raw grade strings directly into ordinal classes.
8. Do not train a model before target provenance, identity resolution, and leakage controls are documented.
9. Preserve the approved FYP objectives and obtain supervisor approval before formal scope changes.
10. Use narrator-disjoint evaluation where appropriate, with duplicate/source leakage checks and per-class metrics.

## 12. Immediate next actions

1. Run audit_shamela_narrators.py against the committed Parquet file.
2. Review coverage, source-ID/title mappings, collision tables, duplicate reports, and samples.
3. Resolve narrator_type and source-identifier semantics.
4. Manually verify a stratified sample against identifiable source works.
5. Define an annotation schema for attribution and evaluative spans.
6. Only after these gates, finalise the prediction target and graph representation.

## 13. Reproduction

Install dependency:

    python -m pip install pyarrow

Run from repository root:

    python .\dataset_discovery\Shamela4\audit_shamela_narrators.py .\data\1_raw\Shamela4_Full_DB\_meta\narrators.parquet

By default, outputs are written to data/2_interim/shamela4_narrator_audit/. The script prints principal findings and writes CSV/JSON/Markdown artefacts. The raw Parquet file is read-only.

## 14. Limitations

- Counts originate from previous local audit outputs shared in conversation; not every count has been independently rerun during documentation.
- The source-ID-to-title and title-to-source-ID output was missing from the previously shared output.
- No primary-source passage has yet been manually verified in this consolidated audit.
- No formal licence conclusion is recorded. Check the dataset card and upstream terms before further redistribution.
- No label schema, graph schema, or model architecture is approved by this report.
