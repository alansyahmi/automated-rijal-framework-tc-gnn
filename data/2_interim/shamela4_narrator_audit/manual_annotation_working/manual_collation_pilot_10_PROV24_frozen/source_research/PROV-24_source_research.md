# PROV-24 source research memo

**Date:** 2026-11-13  
**Scope:** Source collation for HadithDB narrator ID 1214 and candidate *Taqrīb* entry 3038. This memo records text and source layers only; it does not adjudicate identity or provenance and does not edit the working CSVs.

## Local record and candidate text

The raw HadithDB record is `data/1_raw/hadithdb/narrators_db.json`, JSON key/pointer `/1214`. It stores `id: 1214`, `name: "أَبَا حَمْزَةَ،"`, and these identity fields: `الاسم: ": طلحة بن يزيد"`, `الشهرة`/`الكنية: "أبو حمزة"`, `النسب: "الأيلي، الأنصاري مولاهم، الكوفي"`, `بلد الإقامة: "الكوفة"`, and `علاقات الراوي: "مولى قرظة بن كعب الأنصارى"`. These are the source's identity claims, including the leading colon in `الاسم` and final comma in `name`.

The same record has `الرتبة عند ابن حجر: "وثقه: النسائي"`. Under `الجرح والتعديل` → `النسائي` it stores five distinct strings:

1. `روايته عن حذيفة عند النسائي وابن ماجه. وقال النسائي: هذا عندي مرسل، طلحة بن يزيد لا أعلمه سمع من حذيفة شيئا، وغير العلاء بن المسيب قال في هذا الحديث: عن طلحة عن رجل عن حذيفة[تحفة التحصيل في المراسيل (1/ 212)]`
2. `قال النسائي في كتاب السنن تأليفه: إثر حديث: قرأ البقرة وآل عمران والنساء في ركعة طلحة هذا ثقة، وكذا قاله أبو عمر في الاستغناء. وذكره ابن خلفون في الثقات.[إكمال تهذيب الكمال (7/ 88)]`
3. `قلت: قال النسائي: لما أخرج حديثه عن رجل عن حذيفة في صلاة الليل: هذا الرجل يشبه أن يكون صلة بن زفر، وطلحة هذا ثقة[تهذيب التهذيب (2/ 245)]`
4. `وثقه النسائي[تقريب التهذيب (1/ 465)]`
5. `هذا الحديث عندي مرسل، وطلحة بن يزيد لا أعلمه سمع من حذيفة شيئا، وغير العلاء بن المسيب قال في هذا الحديث: عن طلحة، عن رجل عن حذيفة[سنن النسائي (1/ 355)]`

The local source README (`data/1_raw/hadithdb/README.md`, §§3, 5) describes this JSON's fields and cautions that nested group labels are not verified speaker identities, that quotation subjects can differ from biography subjects, and that the trailing citation does not identify an edition or establish textual accuracy. It records a local input hash, but no field-level derivation trail for the grade value. The exact text match with *Taqrīb* below therefore does **not** establish how HadithDB acquired that value.

The local *Taqrīb al-Tahdhīb* transcription is in `data/1_raw/Shamela4_Full_DB/26__التراجم-والطبقات/3076__تقريب-التهذيب/pages.jsonl`, record `page_id=2832542`, `page_num=283`, `sequence_num=3028` (the body itself numbers the entry 3038). Its exact entry text is:

> ٣٠٣٨- طلحة ابن يزيد الأيلي بفتح الهمزة وسكون الياء أبو حمزة مولى الأنصار نزل الكوفة وثقه النسائي من الثالثة خ ٤

The associated `book_metadata.json` identifies Ibn Hajar as author and reports the Muhammad Awwamah / Dar al-Rashid, first edition, 1406 AH / 1986 CE text, with a note that the supplied pagination matches print. The online searchable transcription on [Wikisource, *Taqrīb*, letter Ṭāʾ](https://ar.wikisource.org/wiki/%D8%AA%D9%82%D8%B1%D9%8A%D8%A8_%D8%A7%D9%84%D8%AA%D9%87%D8%B0%D9%8A%D8%A8/%D8%AD%D8%B1%D9%81_%D8%A7%D9%84%D8%B7%D8%A7%D8%A1_%D8%A7%D9%84%D9%85%D9%87%D9%85%D9%84%D8%A9) has the same entry at lines 180–181. That is a text transcription, not a page image of the Awwamah edition.

For identity/source-layer context, the local *Tahdhīb al-Kamāl* transcription (`data/1_raw/Shamela4_Full_DB/26__التراجم-والطبقات/1716__تهذيب-الكمال-في-أسماء-الرجال/pages.jsonl`) places entry 2986, `طلحة بن يزيد الأنصاري، أبو حمزة الكوفي، مولى قرظة بن كعب الأنصاري`, at part 13, p.446. Its following-page footnote (part 13, p.447, note 2) says Ibn Hajar's *Tahdhīb* (5/29) reports Nasa’i's remark, “... وطلحة هذا ثقة”, and separately cites Ibn Hajar's *Taqrīb*. Local metadata identifies this *Tahdhīb al-Kamāl* text as the Bashshar Awwad / Mu'assasat al-Risalah edition (1400–1413 AH). This is al-Mizzī's compiled biography and a later footnote citing Ibn Hajar, not a direct Nasa’i text.

An online scan of *Tahdhīb al-Tahdhīb*, vol. 5, in the Hyderabad 1326 AH edition is available [as a PDF](https://upload.wikimedia.org/wikisource/ar/8/83/%D8%AA%D9%87%D8%B0%D9%8A%D8%A8_%D8%A7%D9%84%D8%AA%D9%87%D8%B0%D9%8A%D8%A805.pdf); the [Wikisource file description](https://ar.wikisource.org/wiki/%D9%85%D9%84%D9%81%3A%D8%AA%D9%87%D8%B0%D9%8A%D8%A8_%D8%A7%D9%84%D8%AA%D9%87%D8%B0%D9%8A%D8%A805.pdf) identifies the edition. The printed p.29 is the cited locator; its PDF-page index was not matched visually in this pass.

## Attribution and transmission layers

The grade field is explicitly nested under **“الرتبة عند ابن حجر”**; its value reports Nasa’i as the source of the positive assessment. The raw quotation group key **“النسائي”** contains different cited works and different kinds of material, including an *isnād* caveat, later biographical compilations, a *Taqrīb* summary, and a *Sunan al-Nasāʾī* passage. Preserve those as separate textual/transmission records; the group label alone does not make every string a direct Nasa’i utterance.

The *Sunan al-Nasāʾī* quote at 1/355 is searchable online as no. 1665 and reads, in the relevant part, “هذا الحديث عندي مرسل وطلحة بن يزيد لا أعلمه سمع من حذيفة شيئا”. It comments on the reported connection to Hudhayfa in that hadith. The online [no. 1665 transcription](https://quranislam.github.io/hadith/nisay1665.html) is a digital text, not a scan.

The al-Nasa’i *Sunan al-Kubrā* no. 1383 transcription identifies the narrator in the chain as Abu Hamza, “طلحة بن يزيد”, and says the unnamed man resembles Sila b. Zufar; see the [digital text of no. 1383](https://hadithunlocked.com/nasai-kubra%3A1383). The displayed text does not include “وطلحة هذا ثقة”. A modern source-collation note in al-Muʿallimī’s *al-Wuḥdān*, entry 61, p.112, explicitly says the printed *Kubrā* text at no. 1383 contains the correction “صلة بن زفر” but not the clause “وطلحة هذا ثقة”; it also distinguishes the *Mujtabā* report no. 1665 from the *Kubrā* report no. 1383. See the [edited *al-Wuḥdān* text and edition metadata](https://usul.ai/ar/t/al-whidan/152) (author ʿAbd al-Raḥmān al-Muʿallimī; editor ʿAlī Muḥammad al-ʿUmrān; Dār ʿĀlam al-Fawāʾid, first edition, 1434 AH). This is editorial collation, not Nasa’i's own text.

Thus the available transcription chain preserves a later report attributed to Nasa’i, while the cited *Kubrā* passage and the *Mujtabā* passage have different wording and context. Whether the positive sentence belongs to another location, an earlier copy, or a transmission/quotation conflation is unresolved here. The *Taqrīb* report is evidence for what Ibn Hajar's entry says; it is not independent proof of HadithDB's field provenance.

## Locator and source limitations

- Local *Taqrīb* row: `page_num=283`, `page_id=2832542`, body entry 3038. HadithDB's embedded *Taqrīb* citation is 1/465; the *Tahdhīb al-Kamāl* footnote lists *Taqrīb* 1/380. These locators do not agree. They may reflect different pagination or source conventions, but no scan was located here to reconcile them. Treat `page_num=283` as the local extraction locator until edition pagination is checked.
- Local *Tahdhīb al-Kamāl* pages give a useful compiled biography and Ibn Hajar citation, but not the underlying Nasa’i manuscript or a field-level provenance trail for HadithDB.
- Online *Taqrīb* and Sunan texts located here are searchable transcriptions. The available *al-Wuḥdān* edition note is valuable for locating the discrepancy, but it is a modern editor's report rather than a substitute for collation against the relevant printed pages or manuscripts.

