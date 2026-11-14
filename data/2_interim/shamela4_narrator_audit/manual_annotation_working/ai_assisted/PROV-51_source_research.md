# PROV-51-C01 source research memo

**Date:** 2026-11-13  
**Scope:** Shamela4 narrator 5498; compare local *Taqrīb*, *Tahdhīb al-Kamāl*, and *al-Jarḥ wa-al-taʿdīl* passages, with accessible online witnesses. Exploratory source collation only; no CSV edits or annotation decisions.

## Local corpus passages and edition metadata

The local narrator record (data/2_interim/shamela4_narrator_audit/narrators.csv, ID 5498) stores the field الرتبة عند ابن حجر as عابوا عليه أنه حدث عن أبيه بغير سماع. That is a dataset field/value; the source wording is independently present in *Taqrīb* entry 5735.

In local *Taqrīb* (data/1_raw/Shamela4_Full_DB/26__التراجم-والطبقات/3076__تقريب-التهذيب/pages.jsonl, page_id=2832727, printed page 468, body entry 5735):

> ٥٧٣٥- محمد ابن إسماعيل ابن عياش بالتحتانية والمعجمة الحمصي عابوا عليه أنه حدث عن أبيه بغير سماع من العاشرة ق

Local book_metadata.json identifies Ibn Hajar, ed. Muhammad ʿAwwāma, Dar al-Rashid, first edition, 1406/1986, and says pagination matches print. An online searchable transcription at [IslamDB, page 398](https://books.islam-db.com/book/%D8%AA%D9%82%D8%B1%D9%8A%D8%A8_%D8%A7%D9%84%D8%AA%D9%87%D8%B0%D9%8A%D8%A8/398) reproduces entry 5735, but “398” is the site's page locator, not the cited print page. A [Shamela PDF transcription of the Dar al-ʿĀṣima edition](https://shamela.org/gen/5e84b15d979ad791fc88d6a960d84bea_gen.pdf) also contains the entry and exact clause; it is a different edition, and its PDF folio is not the local Awwāma print locator. I did not visually collate an image of Awwāma p.468.

In local *Tahdhīb al-Kamāl* (data/1_raw/Shamela4_Full_DB/26__التراجم-والطبقات/1716__تهذيب-الكمال-في-أسماء-الرجال/pages.jsonl), entry 5067 begins at part 24, p.483 (page_id=1765334) and continues at p.484 (page_id=1765335). The text identifies محمد بن إسماعيل بن عياش بن سليم العنسي الحمصي, then states:

> قال أبو حاتم: لم يسمع من أبيه شيئا، حملوه على أن يحدث فحدث.
>
> وقال أبو عبيد الآجري: سئل أبو داود عنه فقال: لم يكن بذاك، قد رأيته، ودخلت حمص غير مرة وهو حي، وسألت عمرو بن عثمان عنه، فدفعه.

The local metadata identifies the Bashshār ʿAwwād / Muʾassasat al-Risāla edition (35 vols., first edition, 1400–1413 AH / 1980–1992 CE). The online [IslamWeb entry](https://www.islamweb.net/ar/library/content/1001/6200/%D9%85%D8%AD%D9%85%D8%AF-%D8%A8%D9%86-%D8%A5%D8%B3%D9%85%D8%A7%D8%B9%D9%8A%D9%84-%D8%A8%D9%86-%D8%B9%D9%8A%D8%A7%D8%B4-%D8%A8%D9%86-%D8%B3%D9%84%D9%8A%D9%85-%D8%A7%D9%84%D8%B9%D9%86%D8%B3%D9%8A-%D8%A7%D9%84%D8%AD%D9%85%D8%B5%D9%8A) marks the entry at p.484 and gives these two reports. A [digitized vol. 24 PDF](https://www.cia.gov/library/abbottabad-compound/34/3494D3AA851B5C032A3C7356E7BD5407vol24.pdf) also has entry [5067] and both reports; its visible front matter identifies only “Tahdhīb al-Kamāl, 24/35,” not the editor/publisher, so I cannot establish it is the Awwād printing. Its OCR reads قال أبو حاتم ... حملوه على أن يحدث (no عنه) and attributes the second report to “أبو عبد الأجري,” an OCR/transcription corruption of al-Ajurri.

Local *al-Jarḥ wa-al-taʿdīl* (data/1_raw/Shamela4_Full_DB/26__التراجم-والطبقات/1615__الجرح-والتعديل-ابن-أبي-حاتم/pages.jsonl) has entry 1078 split over part 7, pp.189–190 (page_id=1621975 and 1621976). It reads, across the page break:

> ١٠٧٨ - محمد بن اسمعيل بن عياش روى عن أبيه روى عنه محمد بن عوف وأبو زرعة، نا عبد الرحمن قال سألت أبي عنه فقال لم يسمع من ابيه شيئا حملو على ان يحدث عنه فحدث.

Local metadata identifies the Hyderabad, Maṭbaʿat Majlis Dāʾirat al-Maʿārif al-ʿUthmāniyya, first edition, 1371/1952. A [digitized vol. 7 PDF](https://www.cia.gov/library/abbottabad-compound/12/124A6E4BB43394330217C40424B96328%C6%92%CE%98%C3%B1%E2%8C%90%C3%91%20%CF%86%C6%92%CE%98%C3%B3%CF%80%C2%BA%E2%88%A9%CE%98%207.pdf) visibly marks print pp.189–190 and places entry 1078 across them. Its OCR reads حملوا على أن يحدث عنه فحدث; the local transcription lacks the final alif in حملو. This small orthographic/transcription difference does not change the clause's attribution to the report framed as ʿAbd al-Raḥmān asking his father Abū Ḥātim.

## Wording and attribution layers

The earlier *al-Jarḥ* report does **not** use *Taqrīb*'s exact wording عابوا عليه أنه حدث عن أبيه بغير سماع; it reports Abū Ḥātim's no-audition statement and the induced transmission clause. Al-Mizzī's *Tahdhīb* likewise gives Abū Ḥātim's distinct wording, and separately transmits through al-Ajurri a report about Abū Dāwūd's evaluation and visit to Ḥimṣ. Its modern-edition footnote (3) explicitly says وقال ابن حجر في "التقريب": عابوا عليه أنه حدث عن أبيه بغير سماع; that is an editorial citation to Ibn Hajar's later *Taqrīb*, not al-Mizzī's earlier authorial text.

Accordingly, among the direct earlier passages checked here, the exact *Taqrīb* wording is absent. Its semantic connection to Abū Ḥātim's no-audition report is visible, but the collective عابوا names no individual or group. The separate al-Ajurri/Abū Dāwūd report must not be used to identify that collective. This memo makes no conclusion about how the dataset field was populated.
