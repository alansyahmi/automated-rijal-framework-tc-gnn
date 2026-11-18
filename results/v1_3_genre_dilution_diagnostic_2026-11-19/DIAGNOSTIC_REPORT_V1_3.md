# v1.3 Diagnostic Report: Genre Mismatch, Feature Dilution, Evaluative Passage Filtering, and Hierarchical Fusion

Analyses 1, 2, and 3 plus the evaluative clause extraction rules were developed strictly on `split == 'train'` (`N = 3,674`).

## 1. Analysis 1: Vocabulary Overlap (`train`, tokens with corpus freq >= 3)

- **`Arm 4` vocab size:** `11449` | **Method 1 Full Bio vocab size:** `12429` | **Shared:** `7471` (Jaccard = `0.4554`)
- **Method 1 Filtered Evaluative vocab size:** `4898` (Jaccard vs `Arm 4` = `0.3609`)
- **Fraction of Method 1 vocabulary NOT in `Arm 4`:** `39.9%` of unique types (`3.4%` of total Method 1 token occurrences).
- **Top tokens enriched in Method 1 vs `Arm 4` (log-odds, word, M1 count, Arm 4 count):** `[(6.532, 'ومئة', 710, 0), (6.457, 'ومئتين', 659, 0), (5.302, 'الغنائم', 207, 0), (5.238, 'اسمعيل', 194, 0), (4.921, 'دس', 141, 0), (4.892, 'اخبرتنا', 137, 0), (4.848, 'ريذة', 131, 0), (4.628, 'الدرجي', 211, 1), (4.585, 'بدلا', 405, 3), (4.492, 'بدرجتين', 184, 1)]`
- **Top tokens enriched in `Arm 4` vs Method 1:** `[(7.128, 'خلفون', 1202, 0), (6.57, 'والحاكم', 688, 0), (5.904, 'والطوسي', 353, 0), (5.84, 'والدارمي', 331, 0), (5.645, 'مستدركه', 272, 0), (5.549, 'وثق', 247, 0), (5.392, 'برقم', 211, 0), (5.353, 'والعقيلي', 203, 0), (5.239, 'المزي', 727, 3), (5.228, 'العلائي', 179, 0)]`

## 2. Analysis 2: Evaluative Vocabulary and Clause Density (`train`)

| Evidence Corpus (`train`) | Mean Tokens/Doc | Median Tokens/Doc | Evaluative Token Density % | Evaluative Clause Share % |
| :--- | :---: | :---: | :---: | :---: |
| `Arm 4` (extracted critic quotes) | 296.5 | 123.0 | **83.9%** | **68.3%** |
| Method 1 Full Biographies | 436.8 | 289.5 | 24.9% | 22.0% |
| Method 1 Filtered Evaluative Passages | 116.4 | 60.0 | (filtered stream) | 100% retained |

## 3. Analysis 3: Source-Specific Distribution Across the 6 Classical Books (`train`)

- **Jensen-Shannon Divergence vs `Arm 4` (`m1_eval_filtered` vs `Arm 4` = `0.0712`)**

| Book (`train`) | Bios | Mean Tokens/Bio | Eval Token Density % | Eval Clause Share % | JSD vs `Arm 4` |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `method1_tahdhib_alkamal` | 2375 | 298.7 | 23.1% | 21.3% | 0.105 |
| `method1_jarh_tadil` | 2232 | 62.2 | 31.8% | 27.8% | 0.1436 |
| `method1_thiqat_ibn_hibban` | 2186 | 29.3 | 17.2% | 11.8% | 0.2145 |
| `method1_tarikh_kabir` | 1748 | 34.6 | 12.7% | 7.3% | 0.1606 |
| `method1_thiqat_ijli` | 534 | 19.9 | 61.6% | 37.8% | 0.1993 |
| `method1_kamil` | 361 | 403.2 | 32.6% | 27.7% | 0.1272 |

## 4. Analysis 4: Length-Controlled Evaluative Passage Ablation and Hierarchical Fusion (`test N = 788`, 5-Seed Means)

| Model | Val F1 | Test Macro-F1 | Test R2-12 F1 | Test Acc | Test QWK | 3-Tier F1 | R7 F1 / R7->R9 | ZQ Conn F1 / Acc |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `Abl1_Arm4_BaseText_LogReg` | 0.4791 | 0.4528 | 0.4099 | 0.6637 | 0.8313 | 0.8060 | 0.1622 / 21.0 | 0.1067 / 0.6538 |
| `Abl1_Arm4_EarlyMLP` | 0.5280 | 0.4601 +/- 0.0119 | 0.4184 | 0.6569 | 0.8444 | 0.8185 | 0.0276 / 24.0 | 0.1237 / 0.6615 |
| `Abl1_Arm4_ConcatDirGNN` | 0.4955 | 0.4649 +/- 0.0153 | 0.4231 | 0.6157 | 0.8030 | 0.7964 | 0.2553 / 16.8 | 0.2230 / 0.6538 |
| `Abl2_Arm4PlusM1Full_BaseText_LogReg` | 0.4621 | 0.4470 | 0.4063 | 0.6485 | 0.8069 | 0.7952 | 0.2222 / 18.0 | 0.1213 / 0.5769 |
| `Abl2_Arm4PlusM1Full_EarlyMLP` | 0.5157 | 0.4306 +/- 0.0158 | 0.3881 | 0.6160 | 0.8063 | 0.7967 | 0.1689 / 17.6 | 0.1257 / 0.5846 |
| `Abl2_Arm4PlusM1Full_ConcatDirGNN` | 0.5272 | 0.4428 +/- 0.0102 | 0.4012 | 0.6282 | 0.8136 | 0.7974 | 0.2062 / 15.4 | 0.1765 / 0.5462 |
| `Abl3_Arm4PlusM1EvalPassages_BaseText_LogReg` | 0.4949 | 0.4549 | 0.4129 | 0.6548 | 0.8120 | 0.8012 | 0.2128 / 18.0 | 0.1000 / 0.3846 |
| `Abl3_Arm4PlusM1EvalPassages_EarlyMLP` | 0.5432 | 0.4552 +/- 0.0121 | 0.4135 | 0.6388 | 0.8223 | 0.8118 | 0.0743 / 23.0 | 0.1029 / 0.5462 |
| `Abl3_Arm4PlusM1EvalPassages_ConcatDirGNN` | 0.5421 | 0.4751 +/- 0.0102 | 0.4356 | 0.6487 | 0.8187 | 0.8049 | 0.2108 / 18.8 | 0.1631 / 0.5462 |
| `Abl4_Arm4PlusMetaAndStruct_EarlyMLP` | 0.5545 | 0.4648 +/- 0.0104 | 0.4230 | 0.6541 | 0.8441 | 0.8251 | 0.0890 / 22.2 | 0.1243 / 0.6615 |
| `Abl4_Arm4PlusMetaAndStruct_ConcatDirGNN` | 0.5509 | 0.4746 +/- 0.0109 | 0.4312 | 0.6525 | 0.8414 | 0.8102 | 0.2695 / 17.4 | 0.2135 / 0.6231 |
| `Abl5_HierStreams_TextOnlyPlusTopo_ConcatDirGNN` | 0.5605 | 0.4764 +/- 0.0079 | 0.4355 | 0.6604 | 0.8401 | 0.8183 | 0.2002 / 20.2 | 0.2284 / 0.6923 |
| `Abl5_HierStreams_FullWithMeta_EarlyMLP` | 0.5578 | 0.4706 +/- 0.0055 | 0.4299 | 0.6437 | 0.8451 | 0.8240 | 0.2239 / 17.0 | 0.1733 / 0.6692 |
| `Abl5_HierStreams_FullWithMeta_ConcatDirGNN` | 0.5541 | 0.4724 +/- 0.0093 | 0.4302 | 0.6508 | 0.8300 | 0.8067 | 0.2750 / 16.0 | 0.2105 / 0.6308 |

## 5. Five-Seed Paired Bootstrap Comparisons (`2,000` resamples on `test N = 788`)

- **Abl3_M1EvalPassages_ConcatDirGNN_vs_Abl2_M1Full_ConcatDirGNN:** delta Macro-F1 = `+0.0323` (95% CI `[+0.0104, +0.0535]`, p=`0.0040`), delta Acc = `+0.0206` (p=`0.0280`), delta QWK = `+0.0051` (p=`0.6150`)
- **Abl3_M1EvalPassages_LogReg_vs_Abl2_M1Full_LogReg:** delta Macro-F1 = `+0.0079` (95% CI `[-0.0272, +0.0413]`, p=`0.6420`), delta Acc = `+0.0063` (p=`0.6060`), delta QWK = `+0.0050` (p=`0.7430`)
- **Abl3_M1EvalPassages_ConcatDirGNN_vs_Abl1_Arm4_ConcatDirGNN:** delta Macro-F1 = `+0.0102` (95% CI `[-0.0121, +0.0317]`, p=`0.4050`), delta Acc = `+0.0330` (p=`0.0010`), delta QWK = `+0.0157` (p=`0.3060`)
- **Abl5_HierTextStream_ConcatDirGNN_vs_Abl2_M1Full_ConcatDirGNN:** delta Macro-F1 = `+0.0336` (95% CI `[+0.0122, +0.0553]`, p=`0.0010`), delta Acc = `+0.0322` (p=`0.0010`), delta QWK = `+0.0265` (p=`0.0400`)
- **Abl5_HierFullWithMeta_ConcatDirGNN_vs_Abl1_Arm4_ConcatDirGNN:** delta Macro-F1 = `+0.0075` (95% CI `[-0.0220, +0.0384]`, p=`0.6320`), delta Acc = `+0.0350` (p=`0.0030`), delta QWK = `+0.0269` (p=`0.0880`)
- **Abl4_Arm4PlusMetaAndStruct_ConcatDirGNN_vs_Abl1_Arm4_ConcatDirGNN:** delta Macro-F1 = `+0.0097` (95% CI `[-0.0175, +0.0369]`, p=`0.5330`), delta Acc = `+0.0368` (p=`0.0000`), delta QWK = `+0.0383` (p=`0.0140`)

## 6. Sample Train-Only Filtered Method 1 Evaluative Passages

- `M1B-00002` (`S3076-P077-C004-E0002`, `method1_tahdhib_alkamal`, clauses=`2/8`, chars=`939/2151`): `وابي توبة الربيع بن نافع الحلبي، وسعيد بن حفص النفيلي الحراني، وسليمان ابن عبد الرحمن الدمشقي، ابن بنت شرحبيل، وعامر بن اسماعيل البغدادي، وعباد بن موسي الختلي، وعبد الله بن احمد بن بشير بن ذكوان الدمشقي المقرئ، وعبد الله بن ربيعة المصيصي، وعبد الله بن محمد بن `
- `M1B-00003` (`S3076-P077-C008-E0005`, `method1_tahdhib_alkamal`, clauses=`39/153`, chars=`4075/16449`): `وعبد الله بن العباس الطيالسي البغدادي، وعبد الله بن عبد الرحمن الدارمي، وابو محمد عبد الله بن محمد بن الحسن بن الشرقي النيسابوري، وعبد الرحمن بن يوسف بن خراش الحافظ، وابو زرعة عبيد الله بن عبد الكريم الرازي، وابو حاتم محمد ابن ادريس الرازي، وابو بكر محمد بن اس`
- `M1B-13067` (`S3076-P077-C008-E0005`, `method1_kamil`, clauses=`5/18`, chars=`596/1569`): `قال لنا عليك الرازي: جاء يحيي بن معين فوقف علي رفقة فيهم ابو الازهر , ببغداد , . قال لهم: ايما الكذاب منكم , الذي روي عن عبد الرزاق , عن معمر , عن الزهري , عن عبد الله بن عباس , ان النبي ﷺ , . قال يحيي: يا بيراينت نبايذ . اخبرني معمر , فذكر هذا الحديث , فلما ق`
- `M1B-03429` (`S3076-P077-C015-E0012`, `method1_jarh_tadil`, clauses=`2/6`, chars=`106/232`): `سمعت ابي وابا زرعة يقولان ذلك . قال ابو محمد وقدمنا همذان وهو قاضيها فلم يقض لي السماع منه (٤) ومحله الصدق`
- `M1B-13066` (`S3076-P077-C015-E0012`, `method1_kamil`, clauses=`2/4`, chars=`246/447`): `يروي عن حفص بن غياث وغيره مناكير . قال الشيخ: وهذا الحديث بهذا الاسناد لا اعلم رواه غير احمد بن بديل، ولاحمد بن بديل احاديث لا يتابع عليها عن قوم ثقات، وهو ممن يكتب حديثه مع ضعفه، وليس هذا الحديث محفوظا عن حفص، ولا في احاديث الاعمش، عن ابي الزبير`
- `M1B-00004` (`S3076-P078-C001-E0013`, `method1_tahdhib_alkamal`, clauses=`9/35`, chars=`655/2892`): `قلت: ذاك الشيخ احمد بن بشير، قال: هذا؟ . قال عثمان: احمد بن بشير كان من اهل الكوفة ثم قدم بغداد وهو متروك . قال الحافظ ابو بكر الخطيب: ليس احمد بن بشير الذي روي عن عطاء بن المبارك مولي عمرو بن حريث الكوفي، ذاك بغدادي (١) ، واما احمد بن بشير الكوفي، فليست حاله `
- `M1B-03428` (`S3076-P078-C001-E0013`, `method1_jarh_tadil`, clauses=`6/19`, chars=`210/781`): `سمعت ابي وابا زرعة يقولان ذلك حدثنا عبد الرحمن . سمعت ابي وسالته عنه ف . قال محله الصدق حدثنا عبد الرحمن . سمعت ابا زرعة يقول احمد بن بشير صدوق ١٥ . سالت ابي عنه وعرضت عليه حديثه ف . قال حديث صحيح، وهو لا يعرفه`
- `M1B-13065` (`S3076-P078-C001-E0013`, `method1_kamil`, clauses=`13/36`, chars=`1075/3226`): `قلت: ذاك الشيخ احمد بن بشير قال: كانه يتعجب من ذكري احمد بن بشير؟ . قال عثمان: احمد بن بشير كان من اهل الكوفة ثم قدم بغداد، وهو متروك . ذكر احاديثه المنكرة . قال الشيخ: وهذا حديث منكر، لا يرويه بهذا الاسناد غير احمد بن بشير، وقد روي هذا الحديث الحسين بن عبد ال`
