# Task B Historical Inputs, Narrator Linkage, and Zero-Leakage Audit v0.1 (TODO Lines 50-53)

**Status:** constructed eligible non-*Taqrīb* Task B inputs with hard Zero-Leakage Firewall (`تقريب التهذيب`, `تحرير التقريب`, `تهذيب التهذيب`, `لسان الميزان`, `الإصابة`, `تعجيل المنفعة`, `ابن حجر`, and `الرتبة عند ابن حجر` / `طبقة رواة التقريب` strictly excluded from all Task B feature columns).

## 1. Narrator Identity Resolution (`8,827` Taqrib Entries <-> `18,989` Shamela4 / `1,524` HadithDB)
- Taqrib-to-Shamela4 1-to-1 link stats: `{'unique_1to1_high_conf': 4407, 'unique_1to1_margin_resolved': 578, 'unlinked_or_ambiguous': 3842}`
- HadithDB (`1,524`) link stats: `{'linked_shamela_only': 62, 'linked_with_task_a': 608, 'unlinked': 854}`

## 2. Leakage Firewall & Historical Passage Filtering (from `165,862` Shamela4 evaluations)
- Passage disposition across linked narrators: `{'eligible_primary_historical_passage': 46193, 'eligible_secondary_summary_work': 3876, 'excluded_prohibited_taqrib_or_ibn_hajar': 34738}`
- Total retained Task B passages (`TASK_B_ELIGIBLE_HISTORICAL_PASSAGES_V0_1.csv`): **50069**
- Top 12 eligible non-Ibn-Hajar source works retained:
  - `تهذيب الكمال`: **18326** passages
  - `إكمال تهذيب الكمال`: **14336** passages
  - `الجرح والتعديل لابن أبي حاتم`: **6166** passages
  - `الكامل في الضعفاء`: **3983** passages
  - `الكاشف في معرفة من له رواية في الكتب الستة`: **3872** passages
  - `تحفة التحصيل في المراسيل`: **1231** passages
  - `الثقات`: **1043** passages
  - `الكواكب النيرات`: **363** passages
  - `سنن البيهقي الكبرى`: **132** passages
  - `الإعلام بسنته عليه الصلاة والسلام بشرح سنن ابن ماجه الإمام`: **111** passages
  - `مسند البزار`: **82** passages
  - `سنن الدارقطني`: **48** passages

## 3. Joint Task B Modelling Readiness (`assigned_rank` + `primary non-Taqrib text`)
- Narrator eligibility breakdown (`8,827` total): `{'eligible_assigned_secondary_only': 42, 'eligible_assigned_with_primary_text': 3030, 'not_eligible_missing_target_or_text': 5755}`
- Per-Rank (`1..12`) narrators having **BOTH** deterministic Task A rank AND `>=1` primary non-*Taqrīb* passage:
  - Rank **1**: `319`
  - Rank **2**: `149`
  - Rank **3**: `926`
  - Rank **4**: `670`
  - Rank **5**: `285`
  - Rank **6**: `77`
  - Rank **7**: `86`
  - Rank **8**: `223`
  - Rank **9**: `209`
  - Rank **10**: `75`
  - Rank **11**: `5`
  - Rank **12**: `6`
