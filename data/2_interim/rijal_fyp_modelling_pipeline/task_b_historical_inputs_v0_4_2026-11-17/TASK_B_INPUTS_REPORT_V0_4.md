# Task B Historical Inputs v0.4 Report (Fwaed + Majhul Bias Fix + Early-Speaker Ablation)

**Status:** refined Task B inputs preserving `v0.3` untouched while integrating `fwaed_raw.csv`, recovering zero-quote `Majhul`/`Mastur` high-confidence narrators, and isolating optional early-speaker-in-Tahdhib ablation rows.

## 1. Non-Ibn-Hajar Fwaed Passages (`fwaed_raw.csv`)
- Filter breakdown: `{'eligible_non_ibn_hajar_fwaed': 9458, 'excluded_prohibited_taqrib_or_ibn_hajar': 4307, 'excluded_unlinked_narrator': 2198}`
- Retained strict zero-leakage `fwaed` passages: **9458**

## 2. Optional Early-Speaker-in-Tahdhib-al-Tahdhib Ablation Tier
- Early non-Ibn-Hajar speaker quotes extracted cleanly from `تهذيب التهذيب` (excluding `قلت`/`قال المؤلف`/`تقريب`): **36673** passages

## 3. Full High-Confidence Cohort (Fixing Rank 7 & 9 Selection Bias)
- All `8,827` entries by `task_b_v04_cohort_tier`: `{'eligible_fwaed_or_secondary_only': 62, 'eligible_primary_quote_present': 4830, 'eligible_structural_or_zero_quote': 358, 'excluded_unlinked_or_no_task_a_target': 3577}`
- Total `unique_1to1_high_conf` + `assigned_rank` cohort: **5250** (up from `4,830`)
- Recovered narrators without primary `ghar` critic quotes (`has_early_critic_quote=no`): **420** (`{'1': 20, '10': 2, '2': 1, '3': 25, '4': 47, '5': 5, '6': 3, '7': 64, '8': 10, '9': 243}`)
- Per-Rank counts across the full high-confidence cohort (`1..12`):
  - Rank **1**: total=`393` (recovered zero-quote=`20`)
  - Rank **2**: total=`251` (recovered zero-quote=`1`)
  - Rank **3**: total=`1665` (recovered zero-quote=`25`)
  - Rank **4**: total=`1130` (recovered zero-quote=`47`)
  - Rank **5**: total=`582` (recovered zero-quote=`5`)
  - Rank **6**: total=`94` (recovered zero-quote=`3`)
  - Rank **7**: total=`178` (recovered zero-quote=`64`)
  - Rank **8**: total=`312` (recovered zero-quote=`10`)
  - Rank **9**: total=`531` (recovered zero-quote=`243`)
  - Rank **10**: total=`93` (recovered zero-quote=`2`)
  - Rank **11**: total=`5` (recovered zero-quote=`0`)
  - Rank **12**: total=`16` (recovered zero-quote=`0`)
