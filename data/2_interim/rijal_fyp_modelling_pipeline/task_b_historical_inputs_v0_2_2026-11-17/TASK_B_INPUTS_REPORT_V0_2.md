# Task B Historical Inputs, Narrator Linkage, and Zero-Leakage Audit v0.2 (TODO Lines 50-53)

**Status:** upgraded 1-to-1 global bipartite entity resolution (`8,827` Taqrib entries <-> `18,989` Shamela4 / `1,524` HadithDB) with strict Task B Zero-Leakage Firewall (`تقريب التهذيب`, `تحرير التقريب`, `تهذيب التهذيب`, `لسان الميزان`, `الإصابة`, `تعجيل المنفعة`, `ابن حجر`, `الرتبة عند ابن حجر`, `طبقة رواة التقريب` strictly excluded).

## 1. Narrator Identity Resolution
- Taqrib-to-Shamela4 1-to-1 link stats: `{'unique_1to1_high_conf': 7994, 'unique_1to1_standard': 259, 'unlinked_or_ambiguous': 574}`
- HadithDB (`1,524`) link stats: `{'linked_shamela_only': 31, 'linked_with_task_a': 1485, 'unlinked': 8}`

## 2. Leakage Firewall & Historical Passage Filtering
- Passage disposition across linked narrators: `{'eligible_primary_historical_passage': 74302, 'eligible_secondary_summary_work': 6279, 'excluded_prohibited_taqrib_or_ibn_hajar': 55729}`
- Total retained Task B passages: **80581**
- Top 10 retained non-Ibn-Hajar source works:
  - `تهذيب الكمال`: **29661** passages
  - `إكمال تهذيب الكمال`: **22610** passages
  - `الجرح والتعديل لابن أبي حاتم`: **10031** passages
  - `الكاشف في معرفة من له رواية في الكتب الستة`: **6270** passages
  - `الكامل في الضعفاء`: **6158** passages
  - `تحفة التحصيل في المراسيل`: **1968** passages
  - `الثقات`: **1716** passages
  - `الكواكب النيرات`: **507** passages
  - `تاريخ الإسلام`: **212** passages
  - `سير أعلام النبلاء`: **203** passages

## 3. Joint Task B Modelling Readiness (`assigned_rank` + `primary non-Taqrib text`)
- Narrator eligibility breakdown (`8,827` total): `{'eligible_assigned_secondary_only': 65, 'eligible_assigned_with_primary_text': 4944, 'not_eligible_missing_target_or_text': 3818}`
- Per-Rank (`1..12`) narrators having **BOTH** deterministic Task A rank AND `>=1` primary non-*Taqrīb* passage:
  - Rank **1**: `396`
  - Rank **2**: `251`
  - Rank **3**: `1661`
  - Rank **4**: `1099`
  - Rank **5**: `586`
  - Rank **6**: `93`
  - Rank **7**: `116`
  - Rank **8**: `305`
  - Rank **9**: `324`
  - Rank **10**: `94`
  - Rank **11**: `5`
  - Rank **12**: `14`
