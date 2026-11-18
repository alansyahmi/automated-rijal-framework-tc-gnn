# Task B Historical Inputs, Precision-Hardened Narrator Linkage, and Zero-Leakage Audit v0.3 (TODO Lines 50-53)

**Status:** ordered Ism + Immediate-Father 1-to-1 narrator resolution (`8,827` Taqrib entries <-> `18,989` Shamela4 / `1,524` HadithDB) with strict Task B Zero-Leakage Firewall (`تقريب التهذيب`, `تحرير التقريب`, `تهذيب التهذيب`, `لسان الميزان`, `الإصابة`, `تعجيل المنفعة`, `ابن حجر`, `الرتبة عند ابن حجر`, `طبقة رواة التقريب` excluded).

## 1. Narrator Identity Resolution
- Taqrib-to-Shamela4 1-to-1 link stats: `{'unique_1to1_high_conf': 7961, 'unique_1to1_standard': 104, 'unlinked_or_ambiguous': 762}`
- HadithDB (`1,524`) link stats: `{'linked_shamela_only': 59, 'linked_with_task_a': 1464, 'unlinked': 1}`

## 2. Leakage Firewall & Historical Passage Filtering
- Passage disposition across linked narrators: `{'eligible_primary_historical_passage': 73419, 'eligible_secondary_summary_work': 6178, 'excluded_prohibited_taqrib_or_ibn_hajar': 54968}`
- Total retained Task B passages: **79597**
- Top 10 retained non-Ibn-Hajar source works:
  - `تهذيب الكمال`: **29389** passages
  - `إكمال تهذيب الكمال`: **22479** passages
  - `الجرح والتعديل لابن أبي حاتم`: **9910** passages
  - `الكاشف في معرفة من له رواية في الكتب الستة`: **6169** passages
  - `الكامل في الضعفاء`: **6037** passages
  - `تحفة التحصيل في المراسيل`: **1967** passages
  - `الثقات`: **1673** passages
  - `الكواكب النيرات`: **501** passages
  - `سنن البيهقي الكبرى`: **201** passages
  - `الإعلام بسنته عليه الصلاة والسلام بشرح سنن ابن ماجه الإمام`: **178** passages

## 3. Joint Task B Modelling Readiness (`assigned_rank` + `primary non-Taqrib text`)
- Narrator eligibility breakdown (`8,827` total): `{'eligible_assigned_secondary_only': 63, 'eligible_assigned_with_primary_text': 4845, 'not_eligible_missing_target_or_text': 3919}`
- Per-Rank (`1..12`) narrators having **BOTH** deterministic Task A rank AND `>=1` primary non-*Taqrīb* passage:
  - Rank **1**: `376`
  - Rank **2**: `250`
  - Rank **3**: `1643`
  - Rank **4**: `1084`
  - Rank **5**: `578`
  - Rank **6**: `91`
  - Rank **7**: `114`
  - Rank **8**: `302`
  - Rank **9**: `295`
  - Rank **10**: `91`
  - Rank **11**: `5`
  - Rank **12**: `16`
