# Gate A Census 100-Entry Stratified Sample Audit v0.1 (TODO Lines 28 & 30)

**Status:** stratified verification sample (`N=100`, `seed=20261117`) drawn from the `8,827`-entry Gate A Complete-Span Census (`v0.1`). All `human_*` fields remain blank pending your approval. Zero canonical ranks assigned and zero rules enabled.

## 1. Full Corpus Denominators (`N = 8,827` numbered entries)
- Total numbered entries: `8827`
- Entries with non-empty target span: `8459` (`95.83%`)
- Entries with `non_grade_or_abstain`: `368` (`4.17%`)
- Category breakdown: `{'approved_phrase_candidate': 109, 'candidate_requiring_review': 2290, 'context_dependent_or_qualified': 686, 'explicit_source_example': 5374, 'non_grade_or_abstain': 368}`

## 2. Stratified Sample Results (`N = 100`)
- Quotas: `{'explicit_source_example': 25, 'candidate_requiring_review': 30, 'context_dependent_or_qualified': 20, 'approved_phrase_candidate': 10, 'non_grade_or_abstain': 15}`
- Audit status counts: `{'confirmed_non_grade_or_abstain': 7, 'context_split_needed': 7, 'exact_span_match': 78, 'missed_grade_in_abstain': 8}`
- Clean exact-match / confirmed-abstain rate on sample: `85/100` (`85%`)

## 3. Sampled Issues Flagged for Review
- `GA-SMP-031` (`S3076-P260-C016-E2700`, `context_split_needed`): span=`صحابي شهد أحدا وما بعدها ما روى عنه سوى بشير ابن يسار` | Long multi-clause span (>6 words with conjunction/brackets); verify Policy v0.2 split between target and context.
- `GA-SMP-038` (`S3076-P384-C008-E4481`, `context_split_needed`): span=`ضعيف قاله أبو داود وقال الترمذي الصواب الضحاك ابن عثمان يعني أنه قلب` | Long multi-clause span (>6 words with conjunction/brackets); verify Policy v0.2 split between target and context.
- `GA-SMP-048` (`S3076-P572-C010-E7289`, `context_split_needed`): span=`ثقة من أثبت الناس في ابن سيرين وفي روايته عن الحسن وعطاء مقال لأنه قيل كان يرسل عنهما` | Long multi-clause span (>6 words with conjunction/brackets); verify Policy v0.2 split between target and context.
- `GA-SMP-053` (`S3076-P682-C002-E8433`, `context_split_needed`): span=`صحابي قيل اسمه الحارث ابن مالك وقيل ابن عوف وقيل اسمه عوف ابن الحارث` | Long multi-clause span (>6 words with conjunction/brackets); verify Policy v0.2 split between target and context.
- `GA-SMP-062` (`S3076-P296-C012-E3222`, `context_split_needed`): span=`وثقه ابن معين واضطرب فيه كلام ابن حبان [من الثامنة] د ت ق [] عبد الله ابن بحينة هو ابن مالك يأتي` | Long multi-clause span (>6 words with conjunction/brackets); verify Policy v0.2 split between target and context.
- `GA-SMP-063` (`S3076-P336-C001-E3794`, `context_split_needed`): span=`صحابي صغير وكان في عهد عمر رجلا وكان على خراسان لعلي` | Long multi-clause span (>6 words with conjunction/brackets); verify Policy v0.2 split between target and context.
- `GA-SMP-065` (`S3076-P361-C007-E4156`, `context_split_needed`): span=`ضعيف له في البخاري زيادة في أول قيام الليل من طريق سفيان عن سليمان الأحول عن طاوس عن ابن عباس في الذكر عند القيام قال سفيان زاد عبد الكريم فذكر شيئا وهذا موصول وعلم له المزي علامة التعليق [وليس هو معلقاً] وله ذكرفي مقدمة مسلم وما روى له النسائي إلا قليلا` | Long multi-clause span (>6 words with conjunction/brackets); verify Policy v0.2 split between target and context.
- `GA-SMP-086` (`S3076-P158-C012-E1209`, `missed_grade_in_abstain`): span=`` | Abstained entry contains potential evaluative/biographical cue (لا بأس به); inspect full entry.
- `GA-SMP-087` (`S3076-P159-C011-E1223`, `missed_grade_in_abstain`): span=`` | Abstained entry contains potential evaluative/biographical cue (لا بأس به); inspect full entry.
- `GA-SMP-089` (`S3076-P207-C001-E1899`, `missed_grade_in_abstain`): span=`` | Abstained entry contains potential evaluative/biographical cue (لا بأس به); inspect full entry.
- `GA-SMP-093` (`S3076-P329-C007-E3703`, `missed_grade_in_abstain`): span=`` | Abstained entry contains potential evaluative/biographical cue (لا بأس به); inspect full entry.
- `GA-SMP-095` (`S3076-P360-C011-E4144`, `missed_grade_in_abstain`): span=`` | Abstained entry contains potential evaluative/biographical cue (لا بأس به); inspect full entry.
- `GA-SMP-096` (`S3076-P366-C021-E4238`, `missed_grade_in_abstain`): span=`` | Abstained entry contains potential evaluative/biographical cue (لا بأس به); inspect full entry.
- `GA-SMP-098` (`S3076-P523-C011-E6528`, `missed_grade_in_abstain`): span=`` | Abstained entry contains potential evaluative/biographical cue (لا بأس به); inspect full entry.
- `GA-SMP-099` (`S3076-P605-C006-E7777`, `missed_grade_in_abstain`): span=`` | Abstained entry contains potential evaluative/biographical cue (روى عنه); inspect full entry.