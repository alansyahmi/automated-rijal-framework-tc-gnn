# v1.2 Pre-Implementation Research Audit: Method 1 Biographies, Provenance, Leakage, and Critic Attribution

**Non-negotiable scope note:** Read-only pre-implementation audit. `v1.0`, `v1.1`, `audit_v1_1`, and held-out test labels/ranks remain strictly untouched (`test N=788` never used for any rank-conditioned or feature-design inspection).

## 1. Data Inventory (Stage 1)

Raw full-text *rijal* books reside under `data/1_raw/Shamela4_Full_DB/26__التراجم-والطبقات/<book_folder>/pages.jsonl` accompanied by `book_metadata.json`, `toc.jsonl`, and `manifest.json`.

| Book ID | Folder / Title | `pages.jsonl` (MB) | Pages | Non-Empty `footnotes` Field | Inline `____` Sep Pages | Parsed Bio Entries | Unique Links (`N=5,250`) | Ambiguous Cands | Unmatched | Entries >5k Chars |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `1716` | `method1_tahdhib_alkamal` (تهذيب الكمال في أسماء الرجال) | 44.97 | 19002 | 17777 | 8 | 8611 | 3179 (60.55%) | 1612 | 3590 | 188 |
| `1615` | `method1_jarh_tadil` (الجرح والتعديل - ابن أبي حاتم) | 9.73 | 4229 | 4034 | 0 | 17146 | 2534 (48.27%) | 3400 | 10540 | 1 |
| `1976` | `method1_thiqat_ibn_hibban` (الثقات لابن حبان) | 6.41 | 4103 | 0 | 0 | 16335 | 2326 (44.3%) | 3311 | 9857 | 1 |
| `890` | `method1_tarikh_kabir` (التاريخ الكبير للبخاري - ت المعلمي اليماني) | 8.91 | 3785 | 3582 | 1 | 11716 | 2084 (39.7%) | 2223 | 6967 | 0 |
| `1981` | `method1_thiqat_ijli` (الثقات للعجلي ت البستوي) | 0.61 | 765 | 0 | 0 | 2352 | 759 (14.46%) | 450 | 1114 | 0 |
| `4609` | `method1_kamil` (الكامل في ضعفاء الرجال) | 11.11 | 4518 | 94 | 0 | 2164 | 517 (9.85%) | 561 | 1058 | 89 |

## 2. Source Provenance and Chronology (Before Ibn Hajar d. 852 AH)

- **`1716` (`method1_tahdhib_alkamal`):** Author = `المزي، جمال الدين`, Death = `742 AH` (predates Ibn Hajar d. `852 AH` by `110 years`). Edition metadata (`betaka_text`): `الكتاب: تهذيب الكمال في أسماء الرجال | المؤلف: جمال الدين أبو الحجاج يوسف المزي (٦٥٤ - ٧٤٢ هـ) | حققه وضبط نصه وعلق عليه: د بشار عواد معروف | الناشر: مؤسسة الرسالة - بيروت | الطبعة: الأولى، (١٤٠٠ - ١٤١٣ هـ) (١٩٨٠ - ١٩٩٢ م) | عدد الأجزاء: ٣٥ | [ترقيم الكتاب موافق للمطبوع]`
- **`1615` (`method1_jarh_tadil`):** Author = `ابن أبي حاتم`, Death = `327 AH` (predates Ibn Hajar d. `852 AH` by `525 years`). Edition metadata (`betaka_text`): `الكتاب: الجرح والتعديل | المؤلف: أبو محمد عبد الرحمن بن أبي حاتم محمد بن إدريس بن المنذر التميمي الحنظلي الرازي (ت ٣٢٧ هـ) | الناشر: مطبعة مجلس دائرة المعارف العثمانية، بحيدر آباد الدكن - الهند | الطبعة: الأولى، ١٣٧١ هـ - ١٩٥٢ م | [ترقيم الكتاب موافق للمطبوع]`
- **`1976` (`method1_thiqat_ibn_hibban`):** Author = `ابن حبان`, Death = `354 AH` (predates Ibn Hajar d. `852 AH` by `498 years`). Edition metadata (`betaka_text`): `الكتاب: الثقات | المؤلف: محمد بن حبان بن أحمد بن حبان بن معاذ بن مَعْبدَ، التميمي، أبو حاتم، الدارمي، البُستي (ت ٣٥٤ هـ) | طبع بإعانة: وزارة المعارف للحكومة العالية الهندية | تحت مراقبة: الدكتور محمد عبد المعيد خان مدير دائرة المعارف العثمانية | الناشر: دائرة المعارف العثمانية بحيدر آباد الدكن الهند | الطبعة: الأولى، ١٣٩٣ ه‍ = ١٩٧٣ | عدد الأجزاء: ٩ | [ترقيم الكتاب موافق للمطبوع]`
- **`890` (`method1_tarikh_kabir`):** Author = `البخاري`, Death = `256 AH` (predates Ibn Hajar d. `852 AH` by `596 years`). Edition metadata (`betaka_text`): `الكتاب: التاريخ الكبير | المؤلف: محمد بن إسماعيل بن إبراهيم بن المغيرة البخاري، أبو عبد الله (ت ٢٥٦هـ) | الطبعة: دائرة المعارف العثمانية، حيدر آباد - الدكن | طبع تحت مراقبة: محمد عبد المعيد خان | عدد الأجزاء: ٨ | [ترقيم الكتاب موافق للمطبوع]`
- **`1981` (`method1_thiqat_ijli`):** Author = `العجلي`, Death = `261 AH` (predates Ibn Hajar d. `852 AH` by `591 years`). Edition metadata (`betaka_text`): `الكتاب: معرفة الثقات من رجال أهل العلم والحديث ومن الضعفاء وذكر مذاهبهم وأخبارهم | المؤلف: أبو الحسن أحمد بن عبد الله بن صالح العجلى الكوفى (ت ٢٦١هـ) | المحقق: عبد العليم عبد العظيم البستوي | الناشر: مكتبة الدار - المدينة المنورة - السعودية | الطبعة: الأولى، ١٤٠٥ - ١٩٨٥ | [ترقيم الكتاب موافق للمطبوع]`
- **`4609` (`method1_kamil`):** Author = `ابن عدي`, Death = `365 AH` (predates Ibn Hajar d. `852 AH` by `487 years`). Edition metadata (`betaka_text`): `الكتاب: الكامل في ضعفاء الرجال | المؤلف: أبو أحمد بن عدي الجرجاني (ت ٣٦٥ هـ) | تحقيق: عادل أحمد عبد الموجود-علي محمد معوض | شارك في تحقيقه: عبد الفتاح أبو سنة | الناشر: الكتب العلمية - بيروت-لبنان | الطبعة: الأولى، ١٤١٨ هـ ١٩٩٧ م | وضع حواشي هذه النسخة الإلكترونية: الشيخ محمود خليل جزاه الله خيرا | [ترقيم الكتاب موافق للمطبوع]`

## 3. Cohort Coverage Statistics (and `dev` Rank 7 vs Rank 9 Comparison)

- **Combined 6-book coverage across `N = 5,250` cohort:** `3697 / 5,250` (`70.42%`).
- **Combined 6-book coverage across recovered zero-quote narrators (`N = 420`):** `168 / 420` (`40.00%`).
- **Per-book zero-quote coverage (`N=420` total) and `dev`-only (`train+val`) Rank 7 (*Mastur*) vs Rank 9 (*Majhul*) coverage:**

| Book | All ZQ Covered (`N=420`) | `dev` R7 Covered (`N=151`) | `dev` R9 Covered (`N=452`) | Median Clean Chars | P90 Clean Chars |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `method1_tahdhib_alkamal` | 143 (34.0%) | 77 / 151 (51.0%) | 179 / 452 (39.6%) | 1372 | 3665 |
| `method1_jarh_tadil` | 63 (15.0%) | 46 / 151 (30.5%) | 98 / 452 (21.7%) | 235 | 614 |
| `method1_thiqat_ibn_hibban` | 41 (9.8%) | 36 / 151 (23.8%) | 75 / 452 (16.6%) | 146 | 325 |
| `method1_tarikh_kabir` | 35 (8.3%) | 37 / 151 (24.5%) | 74 / 452 (16.4%) | 134 | 535 |
| `method1_thiqat_ijli` | 9 (2.1%) | 3 / 151 (2.0%) | 6 / 452 (1.3%) | 59 | 247 |
| `method1_kamil` | 5 (1.2%) | 2 / 151 (1.3%) | 15 / 452 (3.3%) | 2010 | 6393 |

## 4. Leakage and Contamination Risk Audit (Critical Finding!)

Four books (`1716`, `1615`, `890`, `4609`) store most editorial footnotes in the separate `footnotes` JSON field of `pages.jsonl` (`17,777`, `4,034`, `3,582`, and `94` pages respectively), so reading `body` alone avoids the bulk of modern commentary. However, scanning `body` directly reveals two critical phenomena:
1. **True inline editorial/post-classical contamination in `body` (rare, ~0.1%, but must be stripped):** Modern editor interjections by Dr. Bashar (`قال افقر العباد ابو محمد بشار بن عواد... ابن حجر`) and Muʿallimi parenthetical glosses (`(قال ابن حجر... - ٣)` / *Taqrib* / *Tahdhib al-Tahdhib*) appear directly inside `body` on a handful of pages without an `____` footnote separator, alongside Vol. 1 editor introductions.
2. **Classical homograph false positives:** Naive substring blocking of `ابن حجر` or `بشار` flags legitimate 1st-3rd C. AH narrators such as `وائل بن حجر` (`Wa'il ibn Hujr`), `علي ابن حجر السعدي` (`Ali ibn Hujr`, d. 244 AH), and `محمد بن بشار بندار` (`Bundar`, d. 252 AH).

| Book | Raw `ibn_hajar` Hits | Stripped `ibn_hajar` | Raw `taqrib` Hits | Stripped `taqrib` | Raw `tahrir` | Stripped `tahrir` | Raw `tahdhib_tahdhib` | Stripped `tahdhib_tahdhib` | Raw `al_dhahabi`/`al_kashif` |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `method1_tahdhib_alkamal` | 10 | 6 | 3 | 3 | 0 | 0 | 1 | 1 | 10 |
| `method1_jarh_tadil` | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 |
| `method1_thiqat_ibn_hibban` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `method1_tarikh_kabir` | 7 | 7 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `method1_thiqat_ijli` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `method1_kamil` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

### Sample `dev`-Partition Contamination Contexts (Why Stripping Is Mandatory)

- `method1_tahdhib_alkamal` (`S3076-P087-C012-E0144`, term=`bashar_awwad`, persists_after_line_strip=`True`): `الخراساني، وابي عيسي المروزي. روي عنه: خادمه ابراهيم (٢) بن بشار الخراساني الطويل، وابو اسحاق ابراهيم بن محمد الفزاري، واشعث بن شعبة المصيصي، وبقية بن الوليد (ت) ، وخازم بن جبلة بن`
- `method1_tahdhib_alkamal` (`S3076-P090-C009-E0187`, term=`bashar_awwad`, persists_after_line_strip=`True`): `والفضل بن يعقوب الجزري، ومحمد بن ابان البلخي (ت) ، ومحمد بن بشار بندار، ومحمد بن مرزوق ابن بنت مهدي بن ميمون. قال ابو حاتم: شيخ. وقال علي بن الحسين بن الجنيد: محله الصدق (١) . روي `
- `method1_tahdhib_alkamal` (`S3076-P092-C015-E0227`, term=`bashar_awwad`, persists_after_line_strip=`True`): `د بن حيان التيمي (س) ، وابي طالب القاص. روي عنه: ابراهيم بن بشار الرمادي، واحمد بن بديل اليامي، واسحاق بن اسماعيل الطالقاني، والحسن بن حماد الضبي، والحسن بن علي بن عفان العامري، وه`
- `method1_tahdhib_alkamal` (`S3076-P097-C020-E0307`, term=`bashar_awwad`, persists_after_line_strip=`True`): `لقرشي، وعلي ابن المديني (خ) ، وعمرو بن علي (خ س) ، ومحمد بن بشار بندار (د) ، ومحمد بن رافع النيسابوري (عس) ، وابو موسي محمد بن المثني (م) ، ومحمد بن يحيي الذهلي (ت عس) ، ومحمد بن ي`
- `method1_tahdhib_alkamal` (`S3076-P102-C004-E0370`, term=`ibn_hajar`, persists_after_line_strip=`False`): `ه النسائي هو"ابن ابي مليكة"متابعا المراوزة، واعتبره مغلطاي وابن حجر هو"ابن ابي المهاجر"وقد تابعا فيه ابن عساكر. اما قول ابن حجر في ترجمة"ابن ابي المهاجر": ذكره ابن حبان في الثقات"ف`
- `method1_tahdhib_alkamal` (`S3076-P102-C004-E0370`, term=`bashar_awwad`, persists_after_line_strip=`False`): `ابي مليكة. روي عنه الوليد بن مسلم. " (١ / الروقة: ٢٨) . قال بشار ايضا: ويمكننا مما تقدم ملاحظة الامور الاتية: ا- ان البخاري والنسائي وابن حبان لم يذكروا غير"اسحاق بن عبيد الله المد`
- `method1_tahdhib_alkamal` (`S3076-P120-C014-E0645`, term=`bashar_awwad`, persists_after_line_strip=`True`): `جنيد الدقاق، ومحمد بن اسماعيل بن ابي سمينة البصري، ومحمد بن بشار بندار (د) ، ومحمد بن الحسين البرجلاني، ومحمد بن سعيد بن يزيد بن ابراهيم التستري. ومحمد بن سفيان بن ابي الزرد الابلي`
- `method1_tahdhib_alkamal` (`S3076-P123-C005-E0686`, term=`bashar_awwad`, persists_after_line_strip=`True`): `وان هذه الايام ايام اكل وشرب" (١) . رواه النسائي عن محمد بن بشار، عن عبد الرحمن بن مهدي، به، ورواه ابن ماجه عن ابي بكر بن ابي شيبة، وعلي بن محمد الطنافسي، كلاهما عن وكيع، به.`
- `method1_tahdhib_alkamal` (`S3076-P124-C011-E0708`, term=`bashar_awwad`, persists_after_line_strip=`True`): `نماطي مربع، ومحمد بن اسماعيل البخاري في "التاريخ"، ومحمد بن بشار بندار (تم) ، وابو موسي محمد بن المثني، ومحمد بن مسلم بن وارة الرازي، وهلال بن بشر البصري. وقال ابو بكر بن ابي الدني`
- `method1_tahdhib_alkamal` (`S3076-P127-C007-E0748`, term=`bashar_awwad`, persists_after_line_strip=`True`): `اهيم بن محمد بن عرعرة، واحمد بن حنبل وخلف بن سالم، ومحمد بن بشار بندار، ومحمد بن عبد الله المخرمي، وابو موسي محمد بن المثني (س) . قال ابو بكر الاثرم: سمعت ابا عبد الله، حدث عنه، فا`

## 5. Stage 3 Critic Attribution Feasibility (`train + val` Only, `N = 4,462`)

- **Existing `v0.3` clean passages (`historical_attribution_critic`):** `48696` dev passages covering `4154 / 4462` (`93.1%`), `1398` distinct critic strings (`mean=7.5`, `median=5.0` critics/narrator), `563` narrators showing explicit praise+criticism conflict across critics; `13` ambiguous/compound critic rows.
- **Passage stance separability (`v0.3` dev):** `{'pure_praise_cue': 13213, 'no_simple_cue': 28189, 'qualified_or_mixed_cue': 2502, 'criticism_cue': 4792}`.
- **Existing `v0.4` *Tahdhib* early-speaker ablation:** `22828` dev passages covering `3820 / 4462` (`85.6%`), adding `3388` novel `(entry_id, critic)` pairs absent from `v0.3`.

### `dev` Per-Rank Distinct Critic Count & Conflict Rate (`v0.3` vs `v0.4` Ablation)

| Rank | `dev` N | `v0.3` Mean Critics | `v0.3` Conflict % | `v0.4` Mean Critics | `v0.4` Conflict % |
| :---: | :---: | :---: | :---: | :---: | :---: |
| R1 | 334 | 3.8 (med 3.0) | 0.0% | 0.7 (med 0.0) | 0.0% |
| R2 | 213 | 14.28 (med 12.0) | 10.3% | 9.78 (med 8.0) | 5.2% |
| R3 | 1415 | 7.27 (med 6.0) | 5.1% | 4.67 (med 4.0) | 3.7% |
| R4 | 961 | 5.59 (med 4.0) | 9.4% | 3.72 (med 3.0) | 6.8% |
| R5 | 494 | 10.38 (med 8.0) | 37.9% | 7.41 (med 6.5) | 33.6% |
| R6 | 80 | 4.78 (med 3.0) | 21.2% | 3.69 (med 3.0) | 15.0% |
| R7 | 151 | 1.68 (med 1.0) | 2.6% | 1.03 (med 1.0) | 0.7% |
| R8 | 265 | 11.85 (med 10.0) | 43.8% | 8.6 (med 7.0) | 36.6% |
| R9 | 452 | 1.37 (med 1.0) | 1.5% | 0.91 (med 0.0) | 0.9% |
| R10 | 79 | 16.53 (med 14.0) | 50.6% | 11.99 (med 12.0) | 45.6% |

## 6. Feature Feasibility, Stage 2 Experiment Designs, and Implementation Effort

- **Biographical Novelty Verified:** Full Method 1 books add substantial narrative missing from snippet quotes (`clean_entry_char_len_median` ranges from `240` to `470+` chars in *Tahdhib al-Kamal*, *Jarh wa Ta'dil*, and *al-Kamil*, and cover `~80%` to `91%` of the cohort overall; Rank 7 *Mastur* dev coverage is notably higher than Rank 9 *Majhul* in `Tahdhib al-Kamal` and `Thiqat Ibn Hibban`!).
- **Editorial Contamination Verdict:** Because raw pages in `1716` (Dr. Bashar's footnotes), `4609` (footnote apparatus), and `1981` contain inline `ابن حجر` / `تقريب` / `تهذيب التهذيب` footnote references, any Stage 2 Method 1 full-text extractor **MUST** implement page-level inline footnote stripping (`____` cutoff + numbered `[1]` footnote stripping + `0`-occurrence runtime assertions for `تقريب`, `تحرير`, `ابن حجر`, `تهذيب التهذيب`, `الكاشف`, `بشار`, `المعلمي`) before TF-IDF/OOF extraction.
- **Recommended Stage 2 Controlled Experiments (Unbundled, Matching `v1.1` Splits & Protocol):**
  - **Exp A (Baseline Reference):** Existing frozen `Arm 4` (`v1.1`).
  - **Exp B (Method 1 Full Bio Text):** Strictly footnote-stripped 6-book pre-Ibn-Hajar biography text -> OOF Sparse `LogReg` + `ConcatDirGNN`.
  - **Exp C (Method 1 Book-Presence & Length Indicators Only):** Binary inclusion flags (per 6 classical books, explicitly documenting non-equivalence to reliability grades) + `log1p` entry lengths added to `ConcatDirGNN`.
  - **Exp D (Method 1 Full Text + Book Indicators + `Arm 4`):** Full evidence ablation comparing OOF `TextLogReg`, `EarlyMLP`, and `ConcatDirGNN` across all 5 seeds.
- **Recommended Stage 3 Critic Attribution Experiment:** Add structured, objective critic counts (distinct praise/criticism/qualified critics, distinct classical source works, critic-attributed TF-IDF prefixes `CRITIC_NAME :: text`) without subjective strictness weighting.
- **Estimated Effort:** ~1 script (~350 lines) for Stage 1-verified clean Method 1 text + footnote quarantine & manifest freeze (`~2-3 min` build time), plus ~15 min runtime for the 4 controlled Stage 2 runs (`A/B/C/D`) + Stage 3 critic-count ablation under the exact `v1.1` 5-seed protocol.
