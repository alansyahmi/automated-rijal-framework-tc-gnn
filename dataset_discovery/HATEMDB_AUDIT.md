# HATEMDB — Initial Dataset Audit

**Audit date:** 2026-11-07  
**Status:** Under audit — promising pilot source, not yet selected for redistribution or gold-standard labels  
**Repository:** https://github.com/hatemben/hadithdb  
**Inspection method:** GitHub repository metadata, recursive file tree, and direct parsing of both JSON blobs. Counts in this report were independently computed from the downloaded GitHub blob contents in this audit session.

## 1. Repository and files

The repository description says the project provides an open-format hadith database. Its first available book is Sahih al-Bukhari, described as containing 7,563 hadiths and 1,524 narrators.

The repository root contains two JSON files:

| File | Repository-reported size | Observed structure |
|---|---:|---|
| `narrators_db.json` | 12,402,630 bytes | Object keyed by narrator ID; 1,524 records |
| `bukhari_sultania_copy.json` | 13,649,651 bytes | Array of hadith records; 7,233 rows |

No README, data dictionary, schema documentation, or LICENSE file was present in the repository root at the time of audit. GitHub repository metadata reports no declared licence (`license: null`). Public accessibility must not be treated as permission to redistribute or create a derivative public dataset.

## 2. Narrator database structure

Each narrator record contains an integer ID, a display name, and a nested Arabic data object. Common fields include:

- `الاسم` — fuller name / biographical name;
- `الكنية` — kunya;
- `اللقب` — title;
- `النسب` — lineage / affiliation;
- `بلد الإقامة`, `بلد الوفاة`, `بلد الرحلة` — places;
- `تاريخ الميلاد`, `تاريخ الوفاة` — dates;
- `طبقة رواة التقريب` — tabaqa field associated with Taqrib;
- `الرتبة عند ابن حجر` — Ibn Hajar rank;
- `الرتبة عند الذهبي` — al-Dhahabi rank;
- `الجرح والتعديل` — nested scholar-labelled quotation groups.

### Independently computed counts

| Check | Result |
|---|---:|
| Narrator records | 1,524 |
| Narrators with at least one entry under `الجرح والتعديل` | 1,521 |
| Unique scholar-label keys across the dataset | 1,307 |
| Narrator × scholar-label groups | 18,966 |
| Quotation-string occurrences | 40,524 |
| Unique exact quotation strings | 35,216 |
| Occurrences with a trailing bracketed citation | 40,522 |
| Occurrences without a trailing bracketed citation | 2 |
| Unique full bracketed citation strings (work + locator) | 8,095 |
| Distinct work-title strings parsed from citations | 222 |

These counts describe the JSON representation. They do not establish that all 40,524 strings are independent judgements, correctly attributed, or suitable training examples.

### Citation coverage

Most quotation strings end with a reference in the form `[work title (volume/page)]`. This is a significant advantage over HKG's released `aqwal` schema, which does not retain a statement-level work/page locator.

However, the citation is embedded in the quotation string rather than represented in separate structured fields. The project does not provide a normalised source table, edition metadata, publisher, publication year, stable digital identifier, or passage-level URL. A volume/page reference is a useful lead, not complete verification.

The most frequently cited work-title strings include:

- `تهذيب التهذيب` — 12,635 quotation occurrences;
- `تهذيب الكمال` — 9,527;
- `إكمال تهذيب الكمال` — 7,151;
- `الجرح والتعديل لابن أبي حاتم` — 3,431;
- `تقريب التهذيب` — 1,656;
- `الكاشف في معرفة من له رواية في الكتب الستة` — 1,597.

These are counts of citation occurrences, not unique statements or independently verified passages.

## 3. Critical issue: scholar-label key is not a safe speaker/critic field

The nested `الجرح والتعديل` object uses scholar names as keys, with arrays of quotation strings as values. There is no separate structured field for:

- the person who originally made the judgement;
- the person transmitting or reporting that judgement;
- the author/compiler of the cited work;
- the authorial voice of a later comment (e.g. `قلت`);
- whether the passage is direct quotation, paraphrase, summary, or contextual biography.

A concrete counterexample occurs in narrator record 1, under the key `البخاري`. One quotation begins `قال الحاكم` and reports what al-Hakim said about al-Bukhari's practice. The key therefore cannot safely be interpreted as the actual speaker of every quotation in the group.

Other entries contain multiple named scholars in one quotation, or later authors' commentary about earlier critics. Some are biographical or historical rather than evaluative. Therefore, a row in this dataset is initially a **quotation occurrence associated with a narrator and a scholar-labelled bucket**, not automatically a validated critic judgement.

**Decision:** retain the original group key as `source_group_label` (or equivalent), not as a confirmed `critic_id`. Add a separate `attributed_speaker_id` only after quote-level extraction and human/source verification.

## 4. Source hierarchy and secondary compilation

The 222 work-title strings include important classical rijal works, including:

- `الجرح والتعديل` by Ibn Abi Hatim;
- `تهذيب الكمال` by al-Mizzi;
- `تهذيب التهذيب` by Ibn Hajar;
- `تقريب التهذيب` by Ibn Hajar;
- `الكامل في الضعفاء` by Ibn ʿAdi;
- `الثقات` by Ibn Hibban.

They also include later compilations, commentaries, and works that quote earlier authorities. This is useful for evidence discovery, but the source cited in a record is not necessarily the earliest source of the judgement.

For example, a statement by an early critic reproduced in *Tahdhīb al-Tahdhīb* is a later transmission of that statement. We should preserve both:
1. the source actually cited by the dataset; and
2. the original authority/source if independently established.

Do not silently rewrite a later citation as if the original early work had been directly consulted.

## 5. Reference-grade leakage risk

The narrator records include `الرتبة عند ابن حجر` in 1,508 records, `الرتبة عند الذهبي` in 1,165, and `طبقة رواة التقريب` in 1,500.

These fields may be valuable reference assessments, but they create a serious leakage risk if the prediction target is derived from Ibn Hajar's *Taqrib al-Tahdhib* or al-Dhahabi's works. Any target-derived grade, tabaqa, or proxy field must be excluded from model inputs. We must document the exact target source and mapping before deciding whether these fields are targets, auxiliary annotations, or prohibited inputs.

## 6. Bukhari hadith / chain file

The file `bukhari_sultania_copy.json` contains records with:

- `hadith_number`;
- Arabic `text`;
- `narrators` as an ordered array of `name` and `id` objects;
- `categories` for book/chapter hierarchy.

### Independently computed counts

| Check | Result |
|---|---:|
| Hadith rows | 7,233 |
| Unique hadith numbers | 7,166 |
| Rows beyond the unique hadith-number count | 67 |
| Maximum hadith number | 7,563 |
| Narrator mentions across rows | 37,094 |
| Unique raw narrator-name strings in hadith chains | 5,698 |
| Narrator IDs matched to narrator database | 1,524 |
| Narrator mention without a usable ID | 1 |

The repository description's claim of 7,563 hadiths does not match the 7,233 JSON rows. The maximum hadith number is 7,563, but this is not the same as the number of rows. There are 67 rows beyond the unique hadith-number count, which may represent repeated numbering, variants, or another convention. This requires inspection before treating the file as a complete canonical Bukhari collection.

The chain file can be useful for a Bukhari-focused transmission layer, but it should not be treated as a complete, fully validated isnad graph until duplicate numbering, missing narrator IDs, name-to-ID consistency, and chain segmentation are audited.

## 7. Identity and duplication observations

The narrator database contains five exact duplicate biographical-name groups. Examples include repeated short names such as `: سلمان`, `: يزيد`, `: محمد بن زياد`, and `: عبد الله بن يزيد`, as well as one longer repeated name.

This is a direct warning against using exact name equality as an entity-resolution rule. Identical names may refer to different people, while one person may appear under multiple name forms.

The hadith chain file contains 5,698 unique raw narrator-name strings, whereas the narrator database has 1,524 profile records. The relationship between these two representations must be inspected; do not assume every chain name is already resolved simply because an ID field is present.

## 8. Lineage and overlap

The Itqan project explicitly lists `hatemben/hadithdb` as an upstream input, describing it as 1,524 narrator records with multiple scholar opinions. Itqan also integrates KASHAF, AR-Sanad, and classical texts parsed from OpenITI.

Consequently:
- HATEMDB and Itqan records are not independent observations;
- the same quotation may appear in HATEMDB, Itqan, and a separate classical-text extraction;
- source-level deduplication and lineage tracking are mandatory;
- Itqan should be treated as an integration/discovery resource, not a second independent confirmation of HATEMDB.

Reference: https://github.com/R3GENESI5/Itqan

## 9. Preliminary suitability

| Research component | Assessment | Reason |
|---|---|---|
| Narrator discovery | Promising, bounded | 1,524 profiles tied to a Bukhari-focused collection |
| ESA statement discovery | Strong pilot potential | 40,524 quote occurrences and extensive cited work/page strings |
| Critic attribution | Unverified | Scholar bucket key is not a reliable speaker field |
| Source traceability | Better than HKG export | Work/volume/page strings are retained, but embedded and edition details absent |
| Gold-standard ESA labels | Not ready | Requires speaker extraction, context, source verification, and annotation |
| Reference grades | Potentially useful but leakage-sensitive | Ibn Hajar and al-Dhahabi grade fields are already present |
| Chain graph | Promising but not validated | Ordered narrator references exist; numbering and identity anomalies remain |
| Redistribution | Not cleared | Repository has no declared data licence |

## 10. Recommended next tasks

### A. Build a quote-level extraction table

Do not flatten away the raw structure. Create one row per quotation occurrence, retaining at minimum:

- `source_dataset_id` = HATEMDB;
- `source_record_id` = narrator record ID;
- `raw_narrator_name`;
- `source_group_label` = original JSON scholar key;
- `raw_quote_text`;
- `parsed_citation_text`;
- `cited_work_title_raw`;
- `cited_volume_raw`;
- `cited_page_raw`;
- `speaker_attribution_status`;
- `source_verification_status`;
- `duplicate_cluster_id`;
- `raw_record_hash`.

Keep raw text immutable. Any normalisation or parsing must be stored in additional fields.

### B. Manually verify a stratified sample

Select examples from:
- early primary works such as Ibn Abi Hatim's *al-Jarh wa al-taʿdil*;
- later compendia such as *Tahdhīb al-Tahdhīb*;
- entries with multiple speakers in one quotation;
- entries where the group key differs from the named speaker;
- non-evaluative biographical statements;
- repeated exact quotation strings.

For each example, verify the cited work, edition, volume/page, actual passage, speaker, narrator, and evaluative meaning. Record mismatches without silently repairing them.

### C. Resolve licensing

Contact the repository owner or identify an explicit licence/permission statement before redistributing the JSON, extracted quotations, or a derivative public dataset. Public GitHub availability alone is not a licence.

### D. Reconcile the hadith record count

Investigate why the file has 7,233 rows but a maximum hadith number of 7,563, including the 67 rows with repeated numbers.

## 11. Preliminary decision

**Keep HATEMDB as Under audit.** It is currently a strong candidate for a small-scale ESA extraction and annotation pilot because it preserves many quotation occurrences with bibliographic locator strings.

It is not yet a gold-standard dataset. Its most important limitation is that the speaker attribution is embedded in unstructured text and cannot safely be inferred from the scholar-group key. Its redistribution rights are also unresolved.

The next step should be to build and validate a quote-level parser and a small manual verification sample—not to train a model yet.


## 12. First manual source check — narrator record 1

**Record:** narrator ID 1, al-Ḥumaydī (ʿAbd Allāh ibn al-Zubayr).  
**HATEMDB group:** `أبو حاتم الرازي`.  
**HATEMDB citation:** `الجرح والتعديل لابن أبي حاتم (5/ 56)`.

A targeted lookup found the corresponding entry for ʿAbd Allāh ibn al-Zubayr al-Ḥumaydī in Ibn Abī Ḥātim's *al-Jarḥ wa al-Taʿdīl*. The online text contains the same evaluative content attributed to Abū Ḥātim: al-Ḥumaydī is described as the most reliable transmitter from Sufyān ibn ʿUyaynah and as a trustworthy imam. The entry also includes the separate report that al-Ḥumaydī himself accompanied Ibn ʿUyaynah for nineteen years or so.

Online references:
- [HadithWeb — al-Jarḥ wa al-Taʿdīl, entry 264](https://sunna.alifta.gov.sa/BookToc/ViewServicePage?bookId=61&mainId=699528) displays the passage with locator 5/57.
- [AB Library — al-Jarḥ wa al-Taʿdīl, page 57](https://ablibrary.net/book_content/b/3108/58?lang=ar) displays the corresponding wording and identifies the book and publisher metadata.

**Outcome:** wording and broad attribution are corroborated by an accessible text of the cited work. The page locator is not yet reconciled: HATEMDB gives 5/56, while the online copies consulted show 5/57. This may be an edition or pagination difference; it is not enough evidence to declare the HATEMDB locator wrong.

**Research lesson:** this is exactly why the extraction schema must preserve the citation as supplied, record the edition separately when known, and distinguish (a) text match, (b) speaker attribution, and (c) exact bibliographic locator verification. One successful wording match does not validate the entire corpus.
