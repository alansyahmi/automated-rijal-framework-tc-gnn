# Task A Deterministic Guarded Target Extractor v1.3 Report

**Status:** full audit & refinement following investigation of all `3,110` `abstain_precondition_unmet` entries from `v1.2`: fixes patronymic spillover (`صالح مجهول`, `كثير مجهول`, `له صدوق`), restores `مختلف في صحبته`, expands `GUARD-CONFLICTING-LYING` to catch tail `كذبه`/`فكذبه`/`كذبوه`, separates stacked `GUARD-MATRUK-WITH-TAKDHIB`, and promotes plural-consensus `كذبوه` (`Rank 12`) plus verified R1-R10 spans.

## 1. Frozen Gate B Blind Set Verification (`N = 120`)
- Exact **Rank / Abstention** agreement: **120 / 120** (`100.0%`)
- Exact **Target Span** agreement: **120 / 120** (`100.0%`)

## 2. Full Corpus Denominators (`N = 8,827` Numbered Entries)
- Disposition counts: `{'abstain_non_grade': 172, 'abstain_precondition_unmet': 3009, 'assigned_rank': 5646}`
- Per-Rank assigned counts (`12` source categories preserved):
  - Rank **1**: `450`
  - Rank **2**: `257`
  - Rank **3**: `1727`
  - Rank **4**: `1180`
  - Rank **5**: `597`
  - Rank **6**: `101`
  - Rank **7**: `202`
  - Rank **8**: `328`
  - Rank **9**: `683`
  - Rank **10**: `100`
  - Rank **11**: `5`
  - Rank **12**: `16`
