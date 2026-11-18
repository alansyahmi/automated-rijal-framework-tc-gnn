# Task A Deterministic Guarded Target Extractor v1.0 Report

**Status:** verified deterministic three-way extractor (`assigned_rank` vs. `abstain_precondition_unmet` vs. `abstain_non_grade`) applied across all `8,827` numbered local *Taqrīb* entries, incorporating all 4 Gate B blind-eval fixes.

## 1. Verification Against Frozen Gate B Blind Set (`N = 120` Unseen Entries)
- Exact **Rank / Abstention** agreement (`human_label == deterministic_label`): **119 / 120** (`99.2%`)
- Exact **Target Span** agreement (`human_span == deterministic_span`): **118 / 120** (`98.3%`, up from `90/120 = 75.0%`)
- Remaining mismatches (`3` rows):
  - `GB-EVAL-035` (`S3076-P128-C002-E0761`): label `abstain_precondition_unmet` vs `abstain_precondition_unmet` | span `مقبول` vs `مقبول رُمِيَ بالرفض` (`GUARD-R6-MAQBUL`)
  - `GB-EVAL-067` (`S3076-P403-C003-E4760`): label `2` vs `2` | span `ثقة ثبت إمام أعلم أهل عصره بالحديث وعلله` vs `ثقة ثبت إمام أعلم أهل عصره بالحديث وعلله حتى قال البخاري ما استصغرت نفسي إلا عند علي ابن المديني` (`RULE-R2-COMPOUND`)
  - `GB-EVAL-084` (`S3076-P474-C007-E5819`): label `5` vs `abstain_precondition_unmet` | span `صدوق فيه لين` vs `صدوق فيه لين` (`GUARD-CTX-QUALIFIER`)

## 2. Full Corpus Denominators (`N = 8,827` Numbered Entries)
- Disposition counts: `{'abstain_non_grade': 264, 'abstain_precondition_unmet': 3400, 'assigned_rank': 5163}`
- Per-Rank assigned counts (`12` source categories preserved):
  - Rank **1**: `336`
  - Rank **2**: `235`
  - Rank **3**: `1614`
  - Rank **4**: `1131`
  - Rank **5**: `492`
  - Rank **6**: `100`
  - Rank **7**: `198`
  - Rank **8**: `313`
  - Rank **9**: `659`
  - Rank **10**: `80`
  - Rank **11**: `5`
  - Rank **12**: `0`
