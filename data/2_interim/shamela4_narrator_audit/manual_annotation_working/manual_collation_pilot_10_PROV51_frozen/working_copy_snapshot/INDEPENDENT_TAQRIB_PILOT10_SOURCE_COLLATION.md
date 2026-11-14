# Independent Taqrib Source Collation Aid: Manual-Collation Pilot 10

**Status:** Independent source-collation aid; still requires user review. This records textual observations from the local primary-source corpus. It does not make identity, historical-attribution, or narrator-reliability judgments.

## Scope and source

I collated the ten case rows in `data/2_interim/shamela4_narrator_audit/manual_annotation_working/manual_collation_pilot_10_v2_2_impl_r2/cases.csv` against the raw local Shamela4 corpus for *Taqrib al-Tahdhib*, book 3076. The frozen case values supplied the dataset narrator name and `original_grade_verbatim`; the frozen candidate-entry values were used only to locate candidate page/entry positions, and each transcription below was checked against the raw `pages.jsonl` body. PROV-04 has two separate source entries, both transcribed below without accepting either as the dataset narrator.

The source is `data/1_raw/Shamela4_Full_DB/26__التراجم-والطبقات/3076__تقريب-التهذيب/pages.jsonl`, with book details in the adjacent `book_metadata.json`. The raw records expose `page_num`, `shamela_page_id`, `page_id`, and page-level `sequence_num`; the printed page numbers below are the corpus `page_num`. The book metadata identifies the text as *Taqrib al-Tahdhib*, edited by Muhammad Awwama, Dar al-Rashid, first edition (1406 AH / 1986), and says its page numbering follows the printed edition. It also says bracketed text marks differences from the Abu al-Ashbal edition. The corpus is an electronic extraction; this collation did not compare it with a physical copy or manuscript.

The checked source hashes are: `pages.jsonl` `45c2f611cee35f7394da23f58ded71280fbf18d99be163347d1ad38b8fc824fa`; `book_metadata.json` `bfa5cb7a35851ce33829cf1b6b137c094ef649216048ce433f7b420621087b88`; HadithDB narrator records `narrators_db.json` `67c183de90f779496f741a868120224c71fd32ff94525fb6a119ea8750b9c42a`; Shamela4 narrator export `narrators.csv` `5c7f04f1d82e5c5c09714a52fd2e9fa00e982ef33350853def84a0eff893087d`; frozen pilot packet `MANUAL_COLLATION_PILOT_10.csv` `78cb15eb72b04c1b2c0d2e350e375615236df22a2918c38256977ccccffae958`; and v2.2.2 package manifest `manifest.json` `e11d45cc1e6c11a3479767478766b23bf33070e15c8c76596d3852db8526dc45`.

## Collated records

### PROV-10 — dataset id 515

- Frozen name: `عَبْدِ اللهِ بْنِ كَعْبِ بْنِ مَالِكٍ،`
- Frozen grade field: `ثقة`
- Source locator: book 3076, printed page 319; raw page record `page_id=2832578`, `shamela_page_id=245`, page-level `sequence_num=3552`; entry 3552.
- Exact raw entry: `٣٥٥٢- عبد الله ابن كعب ابن مالك الأنصاري المدني ثقة يقال له رؤية مات سنة سبع أو ثمان وتسعين خ م د س ق`
- Text comparison: the source name uses `ابن` where the frozen name uses `بن`, and adds `المدني`. The grade string `ثقة` occurs verbatim in the entry; the entry continues with other text.
- Source alone establishes that this text appears in the local Taqrib page record at the stated locator. It does not establish how the dataset field was populated or independently establish that the dataset id maps to this entry.

### PROV-40 — dataset id 1813

- Frozen name: `خلف بن محمد بن عيسى`
- Frozen grade field: `ثقة`
- Source locator: book 3076, printed page 194; raw page record `page_id=2832453`, `shamela_page_id=120`, page-level `sequence_num=1725`; entry 1734.
- Exact raw entry: `١٧٣٤- خلف ابن محمد ابن عيسى الخشاب القافلاني بقاف ثم فاء مكسورة أبو الحسين ابن أبي عبد الله الواسطي لقبه كردوس بضم الكاف ثقة من الحادية عشرة مات سنة أربع وسبعين وله أكثر من ثمانين ق`
- Text comparison: the source name uses `ابن` where the frozen name uses `بن`, then continues with descriptors. The grade string `ثقة` occurs verbatim in the entry.
- Source alone establishes the wording and locator of this entry, not the mapping from dataset id 1813 to it or the dataset field's derivation.

### PROV-39 — dataset id 1811

- Frozen name: `خلف بن خليفة بن صاعد بن برام`
- Frozen grade field: `صدوق، اختلط في الآخر`
- Source locator: book 3076, printed page 194; raw page record `page_id=2832453`, `shamela_page_id=120`, page-level `sequence_num=1725`; entry 1731.
- Exact raw entry: `١٧٣١- خلف ابن خليفة ابن صاعد الأشجعي مولاهم أبو أحمد الكوفي نزل واسط ثم بغداد صدوق اختلط في الآخر وادعى أنه رأى عمرو ابن حريث الصحابي فأنكر عليه ذلك ابن عيينة وأحمد من الثامنة مات سنة إحدى وثمانين على الصحيح بخ م ٤`
- Text comparison: the source name has `ابن صاعد الأشجعي` and does not include `بن برام`; the frozen name has `بن صاعد بن برام`. The grade words `صدوق اختلط في الآخر` occur in the source, but the frozen string has an Arabic comma after `صدوق` that is absent from the source entry.
- Source alone establishes the recorded wording at this locator; it does not resolve the name-string difference or establish that dataset id 1811 maps to this entry.

### PROV-56 — dataset id 6996

- Frozen name: `يحيى بن محمد بن عبد الله بن مهران`
- Frozen grade field: `صدوق يخطئ.`
- Source locator: book 3076, printed page 596; raw page record `page_id=2832855`, `shamela_page_id=522`, page-level `sequence_num=7632`; entry 7638.
- Exact raw entry: `٧٦٣٨- يحيى ابن محمد ابن عبد الله ابن مهران المدني مولى بني نوفل يقال له الجاري بجيم وراء خفيفة صدوق يخطىء من كبار العاشرة د ت س`
- Text comparison: the source name uses `ابن` in place of frozen `بن` and adds `المدني مولى بني نوفل`. The grade phrase is rendered `صدوق يخطىء` in the source versus `صدوق يخطئ.` in the frozen field: the spelling differs at the hamza/alif-maqṣūra sequence, and the frozen value has a final period.
- Source alone establishes the phrase and locator as represented in this extraction; it does not establish dataset-field derivation or the dataset-id mapping.

### PROV-24 — dataset id 1214

- Frozen name: `أَبَا حَمْزَةَ،`
- Frozen grade field: `وثقه: النسائي`
- Source locator: book 3076, printed page 283; raw page record `page_id=2832542`, `shamela_page_id=209`, page-level `sequence_num=3028`; entry 3038.
- Exact raw entry: `٣٠٣٨- طلحة ابن يزيد الأيلي بفتح الهمزة وسكون الياء أبو حمزة مولى الأنصار نزل الكوفة وثقه النسائي من الثالثة خ ٤`
- Text comparison: the entry is headed by `طلحة ابن يزيد` and includes `أبو حمزة`; the frozen name is the kunya in a different grammatical form. The source phrase `وثقه النسائي` matches the frozen grade wording except the frozen field inserts a colon after `وثقه`.
- Source alone establishes the wording, including the kunya and praise phrase, but does not establish that dataset id 1214 is this entry or why the frozen field includes a colon.

### PROV-51 — dataset id 5498

- Frozen name: `محمد بن إسماعيل بن عياش بن سليم`
- Frozen grade field: `عابوا عليه أنه حدث عن أبيه بغير سماع`
- Source locator: book 3076, printed page 468; raw page record `page_id=2832727`, `shamela_page_id=394`, page-level `sequence_num=5727`; entry 5735.
- Exact raw entry: `٥٧٣٥- محمد ابن إسماعيل ابن عياش بالتحتانية والمعجمة الحمصي عابوا عليه أنه حدث عن أبيه بغير سماع من العاشرة ق`
- Text comparison: the source name text has `محمد ابن إسماعيل ابن عياش` followed by `بالتحتانية والمعجمة الحمصي`; it does not include `بن سليم` in this entry. The frozen grade string `عابوا عليه أنه حدث عن أبيه بغير سماع` occurs verbatim and contiguously in the source.
- Source alone establishes the source text at the locator; it does not resolve the difference between the frozen name and the entry text or establish the dataset-id mapping.

### PROV-01 — dataset id 17

- Frozen name: `جَابِرَ بْنَ عَبْدِ اللهِ الْأَنْصَارِيَّ`
- Frozen grade field: `صحابي`
- Source locator: book 3076, printed page 136; raw page record `page_id=2832395`, `shamela_page_id=62`, page-level `sequence_num=863`; entry 871.
- Exact raw entry: `٨٧١- جابر ابن عبد الله ابن عمرو ابن حرام بمهملة وراء الأنصاري ثم السلمي بفتحتين صحابي ابن صحابي غزا تسع عشرة غزوة ومات بالمدينة بعد السبعين وهو ابن أربع وتسعين ع`
- Text comparison: the source name continues `ابن عمرو ابن حرام` and other descriptors beyond the frozen name; it uses `ابن` in place of `بن`. The grade token `صحابي` occurs in the source as part of `صحابي ابن صحابي`.
- Source alone establishes the entry's wording at this locator, not that dataset id 17 maps to it or that the shorter frozen field was copied from this text.

### PROV-02 — dataset id 27

- Frozen name: `وَمَعْمَرٌ`
- Frozen grade field: `ثقة ثبت فاضل، إلا أن في روايته عن ثابت والأعمش وعاصم بن أبي النجود، وهشام بن عروة شيئا، وكذا فيما حدث به بالبصرة`
- Source locator: book 3076, printed page 541; raw page record `page_id=2832800`, `shamela_page_id=467`, page-level `sequence_num=6803`; entry 6809.
- Exact raw entry: `٦٨٠٩- معمر ابن راشد الأزدي مولاهم أبو عروة البصري نزيل اليمن ثقة ثبت فاضل إلا أن في روايته عن ثابت والأعمش [وعاصم بن أبي النجود] وهشام ابن عروة شيئا وكذا فيما حدث به بالبصرة من كبار السابعة مات سنة أربع وخمسين وهو ابن ثمان وخمسين سنة ع`
- Text comparison: the frozen grade and source share `ثقة ثبت فاضل` and the following wording, but they are not identical strings. The frozen field has Arabic commas absent from the source text; the source brackets `[وعاصم بن أبي النجود]`; and the source writes `هشام ابن عروة` where the frozen value has `هشام بن عروة`. The source continues beyond the frozen field.
- Source alone establishes the wording and bracketed text in this local edition record. It does not establish whether the frozen value was transcribed from this edition, another edition, or another source, nor the dataset-id mapping.

### PROV-04 — dataset id 278; two separate entries

Frozen name: `قَيْسُ بْنُ حَفْصٍ`  
Frozen grade field: `ثقة له أفراد`

Both entries occur on book 3076, printed page 456; raw page record `page_id=2832715`, `shamela_page_id=382`, page-level `sequence_num=5554`.

**Candidate entry 5569**

- Exact raw entry: `٥٥٦٩- قيس ابن حفص التميمي الدارمي أبو محمد البصري ثقة له أفراد من العاشرة مات سنة سبع وعشرين خ صد`
- Text comparison: the source name uses `ابن` in place of frozen `بن` and has additional descriptors. The grade phrase `ثقة له أفراد` matches the frozen grade string exactly as a contiguous phrase.

**Separate entry 5570**

- Exact raw entry: `٥٥٧٠- قيس ابن حفص آخر بصري سكن مصر يكنى أبا محمد مقبول من الثانية عشرة مات سنة إحدى وثمانين تمييز`
- Text comparison: this is a second entry headed `قيس ابن حفص`; it includes `آخر` and its text says `مقبول`, not the frozen grade phrase `ثقة له أفراد`.

The source therefore contains two distinct entries with this name on the same page. The raw text alone does not establish whether dataset id 278 corresponds to entry 5569, entry 5570, or neither; no candidate is accepted here.

### PROV-37 — dataset id 1740

- Frozen name: `خالد بن عبد الرحمن بن بكير`
- Frozen grade field: `صدوق يخطئ.`
- Source locator: book 3076, printed page 189; raw page record `page_id=2832448`, `shamela_page_id=115`, page-level `sequence_num=1647`; entry 1650.
- Exact raw entry: `١٦٥٠- خالد ابن عبد الرحمن ابن بكير السلمي أبو أمية البصري صدوق يخطىء من الثامنة خ ت س`
- Text comparison: the source name uses `ابن` where the frozen name uses `بن`, then continues with descriptors. The grade phrase is rendered `صدوق يخطىء` in the source versus `صدوق يخطئ.` in the frozen field: spelling differs at the hamza/alif-maqṣūra sequence, and the frozen value has a final period.
- Source alone establishes the text at this locator; it does not establish dataset-field derivation or the dataset-id mapping.

## Limits of this collation

This aid reports what the specified local Taqrib extraction contains at the page/entry locators. Similar or matching strings do not by themselves show that a frozen dataset value was sourced from this work, and a name match does not by itself establish an identifier-to-entry mapping. Differences may reflect transcription, normalization, edition, or field-selection choices; this extraction alone does not distinguish among those possibilities. PROV-04 is left unresolved between the two source entries. No conclusions are made about historical attribution or narrator reliability.

## Dataset-side identity context for manual comparison

The following names and biographical descriptors were read from the source dataset records, excluding their Ibn Hajar-grade and other evaluation fields. HadithDB details come from `data/1_raw/hadithdb/narrators_db.json`; Shamela4 details come from `data/2_interim/Shamela4/narrators.csv`. These are dataset context, not independent external identity evidence. The overlap notes below are comparison aids only; the reviewer must decide whether the identifier-to-entry match is sufficiently supported.

| Case | Dataset-side non-grade identity fields | Comparison with the Taqrib entry | What remains open |
|---|---|---|---|
| PROV-10, id 515 | Full name `عبد الله بن كعب بن مالك بن أبي القين`; kunya أبو فضالة; الأنصاري، السلمي، المدني; death reported 97/98 AH with alternatives. | Entry 3552 gives عبد الله ابن كعب ابن مالك الأنصاري المدني and reports death in 97 or 98 AH. | Strong name/affiliation/date overlap, but the dataset metadata's source route is not supplied here. |
| PROV-40, id 1813 | Long name extends to ابن أبي عبد الله; sobriquet كردوس; kunya أبو الحسين (an alternate Abu al-Hasan is noted); الخشاب، القافلاني، الواسطي; death 274 AH. | Entry 1734 has the same core name, nisbahs, kunya, sobriquet, Wasit association, and death year. | Multiple matching descriptors support this as a candidate; dataset-side provenance is not independently documented here. |
| PROV-39, id 1811 | Full dataset name includes ابن صاعد بن برام; kunya أبو أحمد; الأشجعي; Kufa, then Wasit and Baghdad; death reports around 179–185 AH. | Entry 1731 has ابن خليفة ابن صاعد, الأشجعي, أبو أحمد, Kufa then Wasit and Baghdad, and death in 181 AH; it omits `بن برام`. | Several attributes align; the omitted lineage element and source route should remain visible in the identity rationale. |
| PROV-56, id 6996 | Full name يحيى بن محمد بن عبد الله بن مهران; sobriquet الجاري; المدني and client affiliation to بني نوفل. | Entry 7638 gives the same core name, Madinan association, بني نوفل affiliation, and الجاري name. | Strong overlap, but the dataset record alone does not establish independent identity provenance. |
| PROV-24, id 1214 | The dataset display is only the kunya أبا حمزة; its full record gives طلحة بن يزيد, أبو حمزة, الأيلي, an Ansari client relationship, and Kufa. | Entry 3038 gives طلحة ابن يزيد الأيلي, أبو حمزة, مولى الأنصار, and Kufa. | The fuller dataset profile strongly narrows the candidate; the kunya-only display field is insufficient by itself. |
| PROV-51, id 5498 | Full name includes محمد بن إسماعيل بن عياش بن سليم; النسبة الحمصي/العنسي; death range 221–230 AH. | Entry 5735 gives محمد ابن إسماعيل ابن عياش, describes the name spelling, and says الحمصي; it omits `بن سليم`. | Name and Hims affiliation overlap, but the omitted lineage element and absence of an independently sourced link should be considered. |
| PROV-01, id 17 | Full name extends through عبد الله بن عمرو بن حرام; الخزرجي، الأنصاري، السلمي، المدني. | Entry 871 gives ابن عمرو ابن حرام, الأنصاري then السلمي, and Madinah as the death place. | Strong lineage/affiliation overlap; external provenance of the dataset biography has not been established here. |
| PROV-02, id 27 | Full name معمر بن راشد; kunya أبو عروة; الأزدي; Basra and Yemen/San'a associations; death range 150–155 AH. | Entry 6809 gives معمر ابن راشد, أبو عروة, الأزدي, Basra, Yemen, and death in 154 AH. | Strong multi-attribute overlap; dataset-side provenance is not independently documented here. |
| PROV-04, id 278 | Full name قيس بن حفص بن القعقاع; أبو محمد; التميمي، الدارمي، البصري; death 227 AH; tenth generation. | Entry 5569 matches the kunya, nisbahs, Basra, 10th generation, and death in 227 AH. Entry 5570 calls itself another Qays, places him in Egypt after Basra, and gives 12th generation and death in 281 AH. | The supplied dataset profile aligns much more closely with 5569; retain both candidates in the record and document why 5570 is rejected if the reviewer accepts the match. |
| PROV-37, id 1740 | Full name خالد بن عبد الرحمن بن بكير; أبو أمية; السلمي، البصري. | Entry 1650 gives the same lineage, kunya, and nisbahs. | Multiple identifiers overlap; dataset-side provenance is not independently documented here. |

These comparisons help a reviewer state why a locator is plausible. They do not make the database's identity metadata independent evidence, verify its historical source, establish that the original tuple was copied from Taqrib, or settle historical attribution. If the review protocol requires an independent biographical work and its passage, that evidence still needs to be consulted and recorded separately.
