# 81-Entry Phrase Occurrence Audit v1.1 (TODO Line 15)

**Status:** second-pass audit complete; original `ENTRY_LEVEL_REVIEW_V1.csv` and `AI_SUGGESTIONS_V1.csv` remain untouched, and all `human_*` columns remain blank pending your approval.

## Summary Counts (81 Distinct Entries)

- `agree_with_ai_v1`: **74**
- `revise_ai_v1`: **7**

### Recommended `human_entry_disposition` Breakdown

- `conditional`: **28**
- `needs_repair`: **2**
- `retain_as_candidate`: **51**

## Specific Revisions Caught Against `AI_SUGGESTIONS_V1.csv`

- **PHO-023** (`S3076-P326-C018-E3665`, `وثقه النسائي` -> `retain_as_candidate`): Main entry ends with 'وثقه النسائي من الرابعة د س ق', followed by '[] عبد الله ابن نسيب هو عباد تقدم' merged cross-reference boundary; grade precedes '[]'.
- **PHO-028** (`S3076-P350-C001-E4001`, `وثقه النسائي` -> `retain_as_candidate`): Preceding text reconciles narrator identity across Bukhari and Tirmidhi before 'وثقه النسائي'; preserve identity context note.
- **PHO-030** (`S3076-P542-C012-E6829`, `وثقه النسائي` -> `retain_as_candidate`): Contains biographical office note ('ولي إمرة الغزو بالمغرب' / 'والي سجستان'); retain as biographical context without affecting Rank 3 proxy.
- **PHO-055** (`S3076-P382-C003-E4449`, `وثقه ابن معين` -> `conditional`): MISSED BY AI_SUGGESTIONS_V1: text reads 'وثقه ابن معين في رواية الدوري' (route/transmission-conditioned authentication by al-Duri); retain qualification and keep conditional.
- **PHO-062** (`S3076-P290-C002-E3127`, `وثقه ابن حبان` -> `retain_as_candidate`): Contains biographical office note ('ولي إمرة الغزو بالمغرب' / 'والي سجستان'); retain as biographical context without affecting Rank 3 proxy.
- **PHO-064** (`S3076-P229-C008-E2214`, `ذكره ابن حبان في ثقات التابعين` -> `conditional`): Earlier 'لأبيه صحبة ويقال له أيضا' precedes the Ibn Hibban listing; keep conditional and non-Rank-3.
- **PHO-068** (`S3076-P566-C013-E7196`, `ذكره ابن حبان في ثقات التابعين` -> `needs_repair`): Bracketed editorial addition '[ذكره ابن حبان في ثقات التابعين]' followed by 'وقيل له صحبة'; requires span/status review.
