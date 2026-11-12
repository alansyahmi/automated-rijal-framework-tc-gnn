# Narrator-level target feasibility audit

**Audit run:** generated from local inputs by `audit_target_feasibility.py`  
**Scope:** feasibility only; no model training, graph construction, label assignment, or raw-data modification.

## Executive findings

**A narrator-level supervised reliability-prediction task is not currently methodologically defensible.** There are abundant candidate text fields and named rank fields, but the repository does not establish record-level grade provenance, a validated cross-dataset identity link, or a leakage-safe set of inputs and targets. The raw-value counts below are field availability, not validated ground truth.

The strongest *candidate label source* for a narrow feasibility study is HadithDB's `الرتبة عند ابن حجر` field because the field name explicitly associates it with Ibn Hajar and it is populated for 1,508/1,524 records (98.95%). This does **not** make its values gold labels: values are unstructured strings, the upstream project provides no field-level data dictionary, and quoted or compiler-reported judgements need record-level validation. The most serious obstacle is target provenance and leakage, followed by unresolved cross-dataset identity.

No normalized class distribution is presented. The raw rank fields contain between 493 and 1,694 distinct strings per dataset/field, including grades, contextual phrases, explicit quotations of other scholars, and non-grade biographical language. No reviewed dataset-specific codebook justifies collapsing them into a common binary, three-class, or five-class scheme or calculating meaningful normalized class imbalance. `طبقة رواة التقريب` is a generation/biographical field, not a reliability target.

## Dataset and schema inventory

| Dataset | Local input / observed schema | Records | Target-related content | Evidence status |
|---|---|---:|---|---|
| Shamela4 | `data/1_raw/Shamela4_Full_DB/_meta/narrators.parquet`; columns `id` (nullable int64), `short_name`, `long_name`, `narrator_type` (nullable int64), `biography_text` (JSON string), `criticism_text` (JSON string) | 18,989 | Biography keys `الرتبة عند ابن حجر`, `الرتبة عند الذهبي`, `طبقة رواة التقريب`; grouped criticism text (`garh`/`fwaed`) | Directly observed locally. Upstream card describes the corpus and its extraction from Lucene + SQLite but does not define these narrator-field semantics. |
| HadithDB | `data/1_raw/hadithdb/narrators_db.json`; object keyed by source record key; each record has `id`, `name`, nested `data` | 1,524 | Nested keys `الرتبة عند ابن حجر`, `الرتبة عند الذهبي`, `طبقة رواة التقريب`, and `الجرح والتعديل` | Directly observed locally. Upstream project describes a personal effort and the record count; no field-level schema, grading codebook, or licence was found in its repository root. |

Parquet schema confirms the six Shamela fields listed above. Parsed biography JSON contains the three grade/generation keys in question. The HadithDB root keys and nested fields were verified from the local JSON. Exact strings are retained in `LABEL_DISTRIBUTION.csv`.

## Label coverage and raw distributions

| Dataset | Field | Total | Non-empty | Missing | Multiple distinct values in one record | Coverage | Unique raw values |
|---|---|---:|---:|---:|---:|---:|---:|
| Shamela4 | `الرتبة عند ابن حجر` | 18,989 | 8,185 | 10,804 | 0 | 43.10% | 1,343 |
| HadithDB | `الرتبة عند ابن حجر` | 1,524 | 1,508 | 16 | 0 | 98.95% | 493 |
| Shamela4 | `الرتبة عند الذهبي` | 18,989 | 5,370 | 13,619 | 0 | 28.28% | 1,694 |
| HadithDB | `الرتبة عند الذهبي` | 1,524 | 1,165 | 359 | 0 | 76.44% | 601 |
| Shamela4 | `طبقة رواة التقريب` | 18,989 | 8,178 | 10,811 | 0 | 43.07% | 294 |
| HadithDB | `طبقة رواة التقريب` | 1,524 | 1,500 | 24 | 0 | 98.43% | 145 |

`ambiguous_records` above means a record has more than one distinct non-empty value for the same field in the observed structure; it is a structural ambiguity count, not a semantic validity score. Semantic ambiguity remains for all unreviewed grades. The local Shamela `narrator_type` field has 9,190 non-empty numeric values and 9,799 missing, but its meaning is unresolved and it is excluded as a target. No record is currently cleared as a verified supervised target; `validated_supervised_records` is 0 for every candidate field in `DATASET_COVERAGE.csv`.

The quote collections are not grade fields. Shamela `garh` evidence occurs in 14,968 narrator records (165,862 occurrences, 87,463 active narrator/group appearances, 2,804 distinct active group labels). HadithDB `الجرح والتعديل` occurs in 1,521 records (40,524 occurrences, 18,964 active narrator/group appearances, 18,966 group keys including empty groups, 1,307 distinct active group labels). The coverage file reports narrator records with quotation evidence and marks all such records ambiguous at target level pending claim-role, speaker, target, independence, and citation verification. These are not grade labels or independent narrator judgments.

The source field name is the only field-level evidence associating the two rank strings with Ibn Hajar or al-Dhahabi. The audit does not assign each value to “scholar's own explicit grade,” “quotation of another scholar,” “compiler summary,” or “derived value.” Exact values containing reporting/attribution cues such as `قال`, `وثقه`, `حكى`, or `يقال` are counted below as review signals only, not automatically classified as quotations or judgments.

| Dataset | Field | Distinct raw values with a reporting/attribution cue | Records containing those values |
|---|---|---:|---:|
| Shamela4 | `الرتبة عند ابن حجر` | 169 | 231 |
| Shamela4 | `الرتبة عند الذهبي` | 851 | 2,145 |
| HadithDB | `الرتبة عند ابن حجر` | 45 | 45 |
| HadithDB | `الرتبة عند الذهبي` | 241 | 322 |

Examples in the unchanged raw-value inventory include `ثقة` (a grade-like standalone value), `قال أبو حاتم: صدوق` (wording that explicitly reports another authority), and `أحد الأعلام` (a descriptive phrase, not a documented closed class). These examples show why the audit does not automatically label a field value as the named scholar's own explicit grade, a transmitted quotation, a compiler summary, or a normalized class. No derived/normalized grade values were created.

`LABEL_DISTRIBUTION.csv` provides one row per exact original string, with frequency and percentage of dataset records. No punctuation stripping or semantic normalization was applied. These distributions must not be mistaken for class distributions.

In HadithDB, 1,156 records have both named rank fields non-empty; 204 have exactly equal strings. Unequal strings are not counted as scholarly disagreement because their wording, provenance, or grading frameworks may differ.

### Missing, duplicate, conflicting, and ambiguous records

- Shamela ID duplicates: 0; exact duplicate rows: 0; duplicate `short_name` groups: 1032 covering 2,874 records.
- HadithDB repeated record IDs: 0; exact duplicate rows: 0; repeated display-name groups: 31 covering 103 records.
- HadithDB root-key versus embedded `id` mismatches: 0.
- Duplicate names are homonym/collision signals, not proof that two records are duplicate people. Likewise, unequal grades among same-name records cannot be treated as a contradiction until identity is resolved.
- Counts of repeated-name groups with different strings by field are recorded in `audit_manifest.json`; these are possible homonym conflicts, not confirmed scholarly disagreements.
- Within-record multiple distinct values are counted in the coverage table. Conflicting values across scholars or works are retained in the source and are not collapsed into one consensus target.

| Dataset | Field | Repeated-name groups with different values | Records in those groups |
|---|---|---:|---:|
| Shamela4 | `الرتبة عند ابن حجر` | 342 | 1202 |
| Shamela4 | `الرتبة عند الذهبي` | 121 | 503 |
| Shamela4 | `طبقة رواة التقريب` | 329 | 1189 |
| HadithDB | `الرتبة عند ابن حجر` | 29 | 98 |
| HadithDB | `الرتبة عند الذهبي` | 18 | 76 |
| HadithDB | `طبقة رواة التقريب` | 29 | 99 |

## Cross-dataset identity correspondence

The two local corpora expose source-specific integer IDs. No reviewed repository documentation establishes that the two ID namespaces are shared. The 1,498 numerically overlapping IDs are reported only as coincidences and were not used to match.

The candidate crosswalk uses exact raw equality and conservative normalized equality across source-provided full/short names and full `الاسم` fields (Unicode NFKC, remove combining marks/tatweel, fold alef variants and `ى` to `ي`; preserve `ة`, particles, and word order). Standalone kunyah, title, fame, and nisba values are not candidate keys because common values produce false links; they require contextual manual review. Best-evidence candidate records by method: `{"normalized_primary": 261}`. Exact raw full-name candidate records: 0; manually verified cross-dataset identities: 0. This is candidate generation, not entity resolution: no row is called verified. Candidate rows: 494; HadithDB records with one or more candidates: 261; records with multiple candidate Shamela IDs: 70; unmatched under this conservative search: 1,263. “Unmatched” means no exact or normalized full-name equality was found, not that no counterpart exists. Manual review is required for spelling, kunya, nisba, lineage, and homonym resolution.

See `IDENTITY_CROSSWALK_CANDIDATES.csv`. Preserve both IDs; do not merge records based on these candidates.

## Target validity and candidate research targets

1. **Explicit scholarly-grade fields.** The two named rank fields look like narrator-level assessments by their field labels. They are not necessarily the scholar's direct independent judgement: strings can include quotations, reports of other scholars, contextual qualification, and compiler wording. The actual local values are long-form free text rather than a closed class vocabulary. Record-level provenance remains unvalidated.
2. **Quotation collections.** Shamela grouped criticism and HadithDB `الجرح والتعديل` are evidence sources, not ready-made grade labels. A row may concern another narrator or a hadith, report multiple authorities, or repeat a later compilation. Group labels do not prove who historically made the judgement.
3. **Generation metadata.** `طبقة رواة التقريب` contains layer labels such as “third” or “tenth”; it is not a reliability grade. Ibn Hajar's own introduction to *Taqrib* distinguishes twelve narrator ranks from twelve chronological/tabaqa layers, so the layer field must not be substituted for a grade. `narrator_type` is a local numeric field whose semantics remain unresolved.

| Candidate target | Availability | Provenance / validity | Leakage and compatibility | Assessment |
|---|---|---|---|---|
| A. Ibn Hajar narrator grade | HadithDB: 1,508; Shamela4: 8,185 non-empty | Strongest field-name provenance of the candidates, but values and source texts are not row-verified; multiple free-text forms | Very high leakage if the same Ibn Hajar grade field, `Taqrib` text, or direct reproduction enters inputs. An exact scholar-specific target is conceptually coherent only after source verification and exclusion rules. | Best candidate for a narrow *future* audit, not ready as a training target. |
| B. al-Dhahabi narrator grade | HadithDB: 1,165; Shamela4: 5,370 | Same concerns; “rank at al-Dhahabi” strings include statements attributed to other critics and non-grade descriptions | High leakage if al-Dhahabi fields or textual reproductions are input; cross-dataset joins are not yet validated. | Less complete and no clearer validity than A. |
| C. Combined multi-scholar category | Both grades appear in some records, but there is no shared validated identity crosswalk or reviewed agreement protocol | Different scholars' frameworks are not interchangeable; disagreement may be substantive, temporal, source-based, or about different evidence | A combination would obscure disagreement and multiply leakage routes. | Not defensible before record-level source/identity validation and a justified aggregation rule. |
| D. Claim-level evaluative stance, later aggregated by narrator | Text evidence exists in both corpora; the current 20-case Shamela pilot has 43 AI-suggested claims only | Closest to the textual research question, but the pilot is not human-verified ground truth; only one human reviewer is available | Inputs can be separated from labels in principle, but attribution and narrator target must be independently annotated; aggregation risks treating repeated/quoted claims as independent. | Strongest construct alignment, but not currently trainable. Continue only as a scoped human annotation feasibility study after independent review is available. |

## Leakage and independence

- A record-level target copied from `الرتبة عند ابن حجر` or `الرتبة عند الذهبي` cannot also be an input feature. If the target is parsed from a source text, remove that same source passage and close duplicates from inputs; otherwise the task is label reproduction.
- Any split must group by resolved narrator identity and, where possible, source work / duplicate-text cluster. Otherwise duplicated biographies, repeated quotations, or the same person under variant names may leak across train and test.
- Exact grade strings occur within the datasets' own criticism/quotation text for some records; the counts by target field are in `audit_manifest.json`. This directly demonstrates a text-target leakage route. A simple substring hit is only a leakage signal, not evidence that the quoted passage is the grade's source.

| Dataset | Field | Exact substring hits in same-record criticism/quotation text | Share of non-empty target records |
|---|---|---:|---:|
| Shamela4 | `الرتبة عند ابن حجر` | 7,513 | 91.8% |
| Shamela4 | `الرتبة عند الذهبي` | 4,755 | 88.5% |
| HadithDB | `الرتبة عند ابن حجر` | 1,362 | 90.3% |
| HadithDB | `الرتبة عند الذهبي` | 981 | 84.2% |
- The nested HadithDB scholar-label key is not a verified speaker field. The existing audit documents an example where a quotation under `البخاري` reports al-Hakim's statement. Quotation rows therefore need claim-level attribution and target validation before supervised learning.
- The current 20-case AI-assisted claim draft and AI-suggested identity reconciliation are feasibility aids only. They are not ground truth, independent labels, or evidence of inter-reviewer agreement.
- The Bukhari chain JSON contains ordered narrator IDs according to the repository audit, but a chain edge represents transmission linkage, not reliability. Duplicate hadith numbering and chain-name/ID consistency still require audit before graph use.

## Graph feasibility (not a graph design)

Potential source nodes/fields include narrator IDs; raw work-title and locator strings; HadithDB's scholar-labelled source groups; Shamela's grouped criticism entries; and ordered narrator IDs in the Bukhari chain JSON. Direct local parsing found 7,233 Bukhari rows, 7,166 unique hadith numbers, 37,094 chain-narrator occurrences, 1,524 distinct IDs, all 1,524 found in `narrators_db.json`; there are 67 rows beyond distinct hadith numbers, 28 chain narrator occurrences without an ID, and 1,091 IDs with more than one raw chain name string. These IDs support a source-specific ordered transmission layer, subject to chain validation; a chain edge represents transmission linkage, not reliability. Scholar labels, citation strings, and tuple IDs are not verified evaluator, work-identity, or independent-assessment entities. A graph built now would risk encoding co-occurrence and storage layout as scholarly relationships. Missing evidence includes a cross-dataset identity resolution, validated speaker/claim subject, normalized work and edition identifiers, citation-to-passage checks, and duplicate/independence review.

## Recommended research decision

1. **Is narrator-level supervised prediction feasible now?** No - not as a defensible, leakage-controlled research task. The records contain candidate labels, but they have not been validated sufficiently for training/evaluation.
2. **Strongest candidate?** For label provenance, A (Ibn Hajar's named field) is the clearest narrowly defined candidate. For the project's ESA research question, D has better construct fit, but its labels are much less mature. Neither is ready for model training.
3. **Most serious obstacle?** Whether a field's value is actually a traceable, narrator-level judgement by the named authority - and whether the same judgement leaks into proposed inputs.
4. **Missing evidence?** Row-level source verification, a grade codebook for the actual stored strings, cross-dataset identity adjudication, human claim/speaker/target annotations, duplicate/independence analysis, and split-leakage checks.
5. **Continue claim annotation, reduce scope, or defer?** Reduce it to a small feasibility study focused on claim segmentation, subject, attribution, and source evidence. The 20-case AI-assisted pilot is not ground truth; do not scale it as a training-label project without an independent Arabic-trained reviewer.
6. **Next single research task:** manually verify a stratified sample of HadithDB Ibn Hajar field records against the cited source (including edition and page) and record whether each value is Ibn Hajar's own concise grade, a quotation of another authority, compiler wording, or unresolved. This directly tests the strongest label candidate before any model work.

## Sources and evidence hierarchy

**Local dataset evidence** is generated from the exact input files recorded in `audit_manifest.json`. Existing local discovery reports are cited as prior audits and were not treated as substitutes for direct current parsing.

**Upstream technical documentation:**
- [AuthenticIlm/Shamela4_Full_DB dataset card](https://huggingface.co/datasets/AuthenticIlm/Shamela4_Full_DB) describes 8,589 books, 18,989 narrator records, and extraction from Lucene + SQLite, but does not define the narrator grade fields in a field-level codebook.
- [hatemben/hadithdb repository](https://github.com/hatemben/hadithdb) describes the project as a personal effort and states its Bukhari/narrator scope. The repository root has the JSON files but no reviewed field-level data dictionary, grade ontology, or declared licence.
- The *Taqrib al-Tahdhib* introduction is quoted in this [catalogued manuscript witness](https://islhornafr.tors.sc.ku.dk/backend/texts/2740): it distinguishes twelve ranks for narrators' status from twelve narrator layers. That documents Ibn Hajar's scheme, but does not show how the local data extraction populated either field or map each free-text string to a rank.

The exact local schema and counts are directly observed. Statements about what each Arabic label means remain hypotheses unless a source is identified and checked. No result in this report establishes a model-ready target, historical speaker identity, or database-ID semantics beyond the local storage observations.
