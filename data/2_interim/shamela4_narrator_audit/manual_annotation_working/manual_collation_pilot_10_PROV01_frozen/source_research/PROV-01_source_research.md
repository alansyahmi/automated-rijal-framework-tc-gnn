# PROV-01 source research memo

**Date:** 2026-11-13  
**Scope:** Exploratory source collation for HadithDB narrator ID 17 and candidate *Taqrīb al-Tahdhīb* entry 871. This memo records source text, local dataset contents, and locator questions. It does not adjudicate identity, attribution, target suitability, or historical-input eligibility, and does not edit the working CSVs.

## 1. HadithDB record (dataset evidence)

The raw profile is `data/1_raw/hadithdb/narrators_db.json`, JSON object key `/17`. It stores the name `جَابِرَ بْنَ عَبْدِ اللهِ الْأَنْصَارِيَّ`, a longer lineage under `الاسم`, and nisbahs including `الخزرجي`, `الأنصاري`, `السلمي`, and `المدني`. The original value under `الرتبة عند ابن حجر` is `صحابي`. The same profile separately stores `طبقة رواة التقريب: صحابي`; these are two distinct dataset fields with the same value.

The profile's nested quotation/source material records, among other items, `له صحبة ... [الجرح والتعديل لابن أبي حاتم (2/ 492)]`, `صحابي [تقريب التهذيب (1/ 192)]`, and `صاحب رسول الله صلى الله عليه وسلم وابن صاحبه [تهذيب الكمال (4/ 443)]`. These strings document what the HadithDB record contains; they do not verify the cited editions, establish a derivation trail for the `الرتبة عند ابن حجر` value, or identify an independent historical witness.

## 2. Local Shamela corpus evidence

### *Taqrīb al-Tahdhīb*

The local transcription is `data/1_raw/Shamela4_Full_DB/26__التراجم-والطبقات/3076__تقريب-التهذيب/pages.jsonl`, record `page_id=2832395`, `page_num=136`, `sequence_num=863`. Its entry 871 reads:

> ٨٧١- جابر ابن عبد الله ابن عمرو ابن حرام بمهملة وراء الأنصاري ثم السلمي بفتحتين صحابي ابن صحابي غزا تسع عشرة غزوة ومات بالمدينة بعد السبعين وهو ابن أربع وتسعين ع

The adjacent clauses provide name/lineage and nisbah information, the phrase `صحابي ابن صحابي`, campaign and death details, and a collection symbol. The corpus `book_metadata.json` identifies Ibn Hajar as author and the Muhammad ʿAwwāma / Dār al-Rashīd first edition (1406 AH / 1986 CE); its metadata says the supplied pagination agrees with print. That metadata is not a visual check of the printed page. The local pages-file SHA-256 in `manifest.json` is `45c2f611cee35f7394da23f58ded71280fbf18d99be163347d1ad38b8fc824fa`.

HadithDB's nested citation gives *Taqrīb* `1/192`, while the local corpus places entry 871 on page 136. The searchable [Usul transcription of *Taqrīb*](https://usul.ai/ar/t/taqrib-tahdhib/62) reproduces entry 871 at `1 / 136` and identifies the ʿAwwāma / Dār al-Rashīd edition. This confirms the online text and local transcription agree, but they are not independent inspections of the printed page. The difference from HadithDB's `1/192` is unresolved; it could reflect another pagination convention/edition or a citation error. Do not silently replace either locator.

### *Al-Jarḥ wa-al-taʿdīl* by Ibn Abī Ḥātim

The local transcription is `data/1_raw/Shamela4_Full_DB/26__التراجم-والطبقات/1615__الجرح-والتعديل-ابن-أبي-حاتم/pages.jsonl`, part 2, page 492, record `page_id=1619765`, entry 2019. It reads:

> ٢٠١٩ - جابر بن عبد الله بن عمرو بن حرام أبو عبد الله ويقال أبو محمد السلمي الأنصاري له صحبة روى عنه سعيد بن المسيب وأبو سلمة وعطاء سمعت أبي يقول ذلك.

This earlier biographical entry supplies a matching name/lineage, kunyahs, nisbahs, and an explicit `له صحبة` statement. The wording ends `سمعت أبي يقول ذلك`; the entry presents this as the compiler's report of what he heard from his father. The source's precise attribution scope should be preserved as written rather than expanded into a claim about who first formulated the status statement. Local metadata attributes the work to Ibn Abī Ḥātim (d. 327 AH) and identifies the Hyderabad, 1371 AH / 1952 CE edition; the pages-file hash in the corpus manifest is `294de8576ead84287a50bb1107e4048fcbd692dc1dd23fbfcf87f72197d257e1`.

### *Tahdhīb al-Kamāl* by al-Mizzī

The local transcription is `data/1_raw/Shamela4_Full_DB/26__التراجم-والطبقات/1716__تهذيب-الكمال-في-أسماء-الرجال/pages.jsonl`, part 4, pages 443–444, entry 871. Page 443 begins `جابر بن عبد الله بن عمرو بن حرام بن ثعلبة`; page 444 continues the lineage and nisbahs and calls him `صاحب رسول الله ﷺ، وابن صاحبه`. Thus the HadithDB excerpt citing `4/443` and the local transcription place this particular phrase on the following local page, 444. As with the *Taqrīb* page difference, this may be a pagination/edition difference or a citation issue; it is not resolved here.

Al-Mizzī's entry supports comparison through lineage, nisbah, and kunya, and supplies source references in its footnotes, including Ibn Saʿd, Ibn Abī Ḥātim, and Ibn ʿAbd al-Barr. That bibliographic list is evidence of sources cited by al-Mizzī, not proof that the HadithDB field was derived from any one of them. Local metadata identifies al-Mizzī (d. 742 AH) as author and the Bashshār ʿAwwād Maʿrūf / Muʾassasat al-Risāla edition (1400–1413 AH / 1980–1992 CE); it states pagination agrees with print. The printed pages were not visually inspected for this memo.

## 3. Textual context and research boundaries

The relevant source wording is not just the isolated field value: *Taqrīb* has `صحابي ابن صحابي` followed by biographical material; Ibn Abī Ḥātim's entry has `له صحبة`; and al-Mizzī describes Jābir as `صاحب رسول الله ... وابن صاحبه`. These are source-level formulations relevant to interpreting the status phrase, not independent proof of how the HadithDB field was populated.

Ibn Hajar's [*Taqrīb* introduction](https://ar.wikisource.org/wiki/تقريب_التهذيب/المقدمة) separately describes the first **rank** as `الصحابة` and the first **generation/ṭabaqa** as `الصحابة`. This provides relevant authorial context for the two distinct HadithDB labels (`الرتبة عند ابن حجر` and `طبقة رواة التقريب`), while leaving open how this particular source record was mapped, whether the database values were copied from the same edition, and what downstream task they should serve. It is not an eligibility decision.

### What is established here

- The HadithDB profile has ID 17, the stated name and original `صحابي` value, and distinct rank and ṭabaqa fields that both contain that value.
- The local *Taqrīb* transcription contains entry 871 with the quoted wording at page 136.
- Earlier compiled biographical entries in the local corpus (*al-Jarḥ wa-al-taʿdīl* and *Tahdhīb al-Kamāl*) contain matching identifying material and explicit Companion-status language.
- The HadithDB citations and local corpus page locators differ for *Taqrīb* and for the cited al-Mizzī phrase; those differences remain unresolved.

### What is not established

This collation does not prove that ID 17 and candidate entry 871 are the same person, although the name, lineage, and nisbah correspondences provide evidence for that comparison. It does not establish which source HadithDB used, historical independence among the biographical compilations, the original author/transmitter of every statement, the exact printed-page reading, or suitability for a reliability-modelling target. No scan was inspected, no source route was reconstructed, and no annotation judgment was finalized.

## Sources

- Local dataset: `data/1_raw/hadithdb/narrators_db.json`, key `/17`.
- Local *Taqrīb*: `data/1_raw/Shamela4_Full_DB/26__التراجم-والطبقات/3076__تقريب-التهذيب/pages.jsonl`, `page_id=2832395`, entry 871; corresponding local metadata and manifest.
- Local *al-Jarḥ wa-al-taʿdīl*: `data/1_raw/Shamela4_Full_DB/26__التراجم-والطبقات/1615__الجرح-والتعديل-ابن-أبي-حاتم/pages.jsonl`, `page_id=1619765`, part 2, p.492, entry 2019; corresponding local metadata and manifest.
- Local *Tahdhīb al-Kamāl*: `data/1_raw/Shamela4_Full_DB/26__التراجم-والطبقات/1716__تهذيب-الكمال-في-أسماء-الرجال/pages.jsonl`, part 4, pp.443–444, entry 871; corresponding local metadata.
- [Usul digital text of *Taqrīb al-Tahdhīb*](https://usul.ai/ar/t/taqrib-tahdhib/62), entry 871 at 1/136 and edition metadata.
- [Wikisource digital text of the *Taqrīb* introduction](https://ar.wikisource.org/wiki/تقريب_التهذيب/المقدمة), for the author's distinction between the opening rank and opening generation.
