# Gate A Census v0.2 100-Entry Stratified Sample Audit (TODO Lines 28 & 30)

**Status:** stratified verification sample (`N=100`, `seed=20261118`) drawn from Gate A Complete-Span Census `v0.2` (`N=8,827`). Zero canonical ranks assigned and zero rules enabled.

## 1. Full Corpus Denominators (`N = 8,827` numbered entries)
- Total numbered entries: `8827`
- Entries with non-empty target span: `8668` (`98.20%`)
- Entries with `non_grade_or_abstain`: `159` (`1.80%`)
- Category breakdown: `{'approved_phrase_candidate': 102, 'candidate_requiring_review': 2204, 'context_dependent_or_qualified': 847, 'explicit_source_example': 5515, 'non_grade_or_abstain': 159}`

## 2. Stratified Sample Results (`N = 100`)
- Audit status counts: `{'confirmed_non_grade_or_abstain': 14, 'context_split_needed': 7, 'exact_span_match': 78, 'missed_grade_in_abstain': 1}`
- Clean exact-match / confirmed-abstain rate on sample: `92/100` (`92%` vs. `85%` in `v0.1`)

## 3. Any Remaining Issues Flagged
- `GA2-SMP-029` (`S3076-P205-C001-E1869`, `context_split_needed`): span=`صحابي شهد الحديبية والفتح ومعه لواء جهينة` | Long multi-clause span (>6 words with conjunction/brackets); check Policy v0.2 split.
- `GA2-SMP-035` (`S3076-P246-C008-E2474`, `context_split_needed`): span=`صحبة ولاه عمر قضاء الكوفة وغزا أرمينية في زمن عثمان فاستشهد` | Long multi-clause span (>6 words with conjunction/brackets); check Policy v0.2 split.
- `GA2-SMP-054` (`S3076-P681-C009-E8428`, `context_split_needed`): span=`مجهول قيل اسمه إبراهيم ابن ميمون الصائغ وإلا فهو مجهول` | Long multi-clause span (>6 words with conjunction/brackets); check Policy v0.2 split.
- `GA2-SMP-059` (`S3076-P180-C014-E1537`, `context_split_needed`): span=`ووهم من زعم أنه ابن نصير ابن الفرج ذاك طرسوسي وذا مصري مقبول` | Long multi-clause span (>6 words with conjunction/brackets); check Policy v0.2 split.
- `GA2-SMP-067` (`S3076-P333-C005-E3757`, `context_split_needed`): span=`صدوق ربما أخط قال أبو حاتم كان كاتب ديوان ولم يكن صاحب حديث` | Long multi-clause span (>6 words with conjunction/brackets); check Policy v0.2 split.
- `GA2-SMP-068` (`S3076-P356-C012-E4087`, `context_split_needed`): span=`ليّن قال العجلي لم يسمع من عائشة وأخطأ خصيف فصرح بسماعه` | Long multi-clause span (>6 words with conjunction/brackets); check Policy v0.2 split.
- `GA2-SMP-075` (`S3076-P761-C012-E8792`, `context_split_needed`): span=`لم أعرف اسمها وهي صحابية لها حديث` | Long multi-clause span (>6 words with conjunction/brackets); check Policy v0.2 split.
- `GA2-SMP-094` (`S3076-P324-C003-E3626`, `missed_grade_in_abstain`): span=`` | Contains evaluative cue (له رؤية); inspect full entry.