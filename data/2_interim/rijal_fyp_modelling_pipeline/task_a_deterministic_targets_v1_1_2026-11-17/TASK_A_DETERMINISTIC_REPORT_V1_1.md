# Task A Deterministic Guarded Target Extractor v1.1 Report

**Status:** thorough refinement of `v1.0` across all `8,827` numbered local *Taqrīb* entries, fixing clause-opener expansion (`له صحبة`, `قيل له صحبة`, `فيه لين`, `من كبار الصحابة`), named precondition guards (`GUARD-QUALIFIED-THIQAH`, `GUARD-CONFLICTING-LYING`, `GUARD-MILD-WEAKNESS`), and verified Ranks 1-12 promotions.

## 1. Verification Against Frozen Gate B Blind Set (`N = 120` Unseen Entries)
- Exact **Rank / Abstention** agreement (`human_label == deterministic_label`): **120 / 120** (`100.0%`)
- Exact **Target Span** agreement (`human_span == deterministic_span`): **120 / 120** (`100.0%`)
- Remaining mismatches (`0` rows):

## 2. Full Corpus Denominators (`N = 8,827` Numbered Entries)
- Disposition counts: `{'abstain_non_grade': 264, 'abstain_precondition_unmet': 3026, 'assigned_rank': 5537}`
- Per-Rank assigned counts (`12` source categories preserved):
  - Rank **1**: `430`
  - Rank **2**: `257`
  - Rank **3**: `1715`
  - Rank **4**: `1162`
  - Rank **5**: `573`
  - Rank **6**: `100`
  - Rank **7**: `202`
  - Rank **8**: `320`
  - Rank **9**: `676`
  - Rank **10**: `96`
  - Rank **11**: `5`
  - Rank **12**: `1`
