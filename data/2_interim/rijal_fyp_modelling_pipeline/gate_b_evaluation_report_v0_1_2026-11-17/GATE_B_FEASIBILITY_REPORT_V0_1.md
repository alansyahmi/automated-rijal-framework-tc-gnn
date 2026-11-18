# Gate B Blind Evaluation vs. Machine Proposals Report v0.1 (TODO Lines 40-46)

**Scope Note (`TODO` line 40):** Single-researcher feasibility check over `120` previously unseen *Taqrīb* entries (`seed=20261119`, excluding all `1,405` development entries). Human labels in `HUMAN_ONLY_BLIND_LABELS_120_V0_1.csv` were frozen under SHA-256 (`65a340157627005d`) BEFORE unsealing `SEALED_MACHINE_PROPOSALS_120_V0_1.csv` (`85e88e05ad601fc1`). Inter-reviewer reliability is NOT claimed.

## 1. Full Denominators (`N = 120`)
- Total entries reviewed: `120`
- Human eligibility breakdown: `{'eligible_grade_or_status': 117, 'non_grade_biographical_or_tamiz': 2, 'unresolved_or_abstain': 1}`
- Entries with human-assigned canonical Rank `1..12` (`preconditions satisfied`): `93`
- Entries routed to `abstain_precondition_unmet`: `25`
- Entries routed to `abstain_non_grade`: `2`

## 2. Span Extraction Agreement (`first_complete_target_span_exact`)
- Counts: `{'exact_span_match': 90, 'machine_false_positive_non_grade': 2, 'machine_overextended_includes_context': 26, 'machine_underextended_truncated': 2}`
- Exact span match: **90 / 120** (`75.0%`)
- Machine included attached qualifier/context without splitting (`machine_overextended_includes_context`): **26**
- Machine false positive on `non_grade` entry: **2**

## 3. Source-Rank & Precondition Comparison
- Counts: `{'agreed_requires_review_or_conditional': 7, 'exact_anchor_rank_match': 53, 'false_suggestion_on_non_grade': 2, 'machine_unanchored_candidate_or_conditional': 39, 'rank_disagreement': 1, 'unsafe_anchor_when_precondition_unmet': 18}`
- Notice `unsafe_anchor_when_precondition_unmet` (**18** cases): exact lexical matches on Rank 6 (`مقبول`/`مقبولة`) or bracketed/doctrinal forms where assigning a label without external corroboration or context guards would violate Gate A preconditions.

## 4. Per-Rank Support (`12` Original Categories Preserved; Zero Collapsing)
- `1`: human=**18** | exact_span=3 | overextended=15 | exact_anchor_match=0
- `2`: human=**10** | exact_span=8 | overextended=2 | exact_anchor_match=7
- `3`: human=**16** | exact_span=13 | overextended=3 | exact_anchor_match=12
- `4`: human=**12** | exact_span=12 | overextended=0 | exact_anchor_match=11
- `5`: human=**16** | exact_span=11 | overextended=4 | exact_anchor_match=5
- `6`: human=**1** | exact_span=1 | overextended=0 | exact_anchor_match=0
- `7`: human=**3** | exact_span=3 | overextended=0 | exact_anchor_match=3
- `8`: human=**4** | exact_span=3 | overextended=0 | exact_anchor_match=4
- `9`: human=**9** | exact_span=9 | overextended=0 | exact_anchor_match=8
- `10`: human=**4** | exact_span=4 | overextended=0 | exact_anchor_match=3
- `11`: human=**0** | exact_span=0 | overextended=0 | exact_anchor_match=0
- `12`: human=**0** | exact_span=0 | overextended=0 | exact_anchor_match=0
- `abstain_precondition_unmet`: human=**25** | exact_span=23 | overextended=2 | exact_anchor_match=0
- `abstain_non_grade`: human=**2** | exact_span=0 | overextended=0 | exact_anchor_match=0

## 5. Detailed Disagreements & False Suggestions
- `[FALSE NON-GRADE]` `GB-EVAL-089` (`S3076-P761-C005-E8789`): machine=`صحابية]` | Bracketed [صحابية] describes grandmother صفية, not main subject إسحاق الهاشمي.
- `[FALSE NON-GRADE]` `GB-EVAL-112` (`S3076-P762-C014-E8801`): machine=`صحابية لها حديث` | Chapter entry for عبد الرحمن ابن طارق عن أمه; صحابية describes his unnamed mother.
- `[SPAN machine_underextended_truncated]` `GB-EVAL-053` (`S3076-P501-C007-E6213`): human=`صدوق له أوهام` vs machine=`صدوق`
- `[SPAN machine_underextended_truncated]` `GB-EVAL-056` (`S3076-P243-C015-E2434`): human=`وهو ضعيف` vs machine=`ضعيف`
- `[RANK DISAGREE]` `GB-EVAL-053` (`S3076-P501-C007-E6213`): human=Rank 5 (`صدوق له أوهام`) vs machine_anchor=Rank 4 (`صدوق`)
- `[CONTEXT OVEREXTEND]` `GB-EVAL-003` (`S3076-P154-C009-E1151`, R1): human=`صحابي` vs machine=`صحابي له حديث واحد`
- `[CONTEXT OVEREXTEND]` `GB-EVAL-004` (`S3076-P318-C016-E3547`, R3): human=`ثقة` vs machine=`ثقة مخضرم`
- `[CONTEXT OVEREXTEND]` `GB-EVAL-005` (`S3076-P409-C002-E4845`, R1): human=`صحابي` vs machine=`صحابي نزل الكوفة وتأخر إلى بعد السبعين`
- `[CONTEXT OVEREXTEND]` `GB-EVAL-009` (`S3076-P145-C014-E1018`, R5): human=`صدوق يخطىء` vs machine=`صدوق يخطىء ورمي بالرفض`
- `[CONTEXT OVEREXTEND]` `GB-EVAL-011` (`S3076-P130-C007-E0796`, R1): human=`صحابي` vs machine=`صحابي له حديث واحد`
- `[CONTEXT OVEREXTEND]` `GB-EVAL-020` (`S3076-P751-C015-E8651`, R1): human=`صحابية` vs machine=`صحابية لها حديث في الاستحاضة`
- `[CONTEXT OVEREXTEND]` `GB-EVAL-023` (`S3076-P114-C003-E0542`, R1): human=`صحابي` vs machine=`صحابي قال البخاري المزني أصح`
- `[CONTEXT OVEREXTEND]` `GB-EVAL-027` (`S3076-P123-C005-E0686`, R1): human=`صحابي` vs machine=`صحابي وله رواية عن علي`
- `[CONTEXT OVEREXTEND]` `GB-EVAL-029` (`S3076-P558-C007-E7076`, R1): human=`صحابي` vs machine=`صحابي فتحي وأمره عمر على مكة قأقام بها إلى أن مات`
- `[CONTEXT OVEREXTEND]` `GB-EVAL-035` (`S3076-P128-C002-E0761`, Rabstain_precondition_unmet): human=`مقبول` vs machine=`مقبول رُمِيَ بالرفض`
- `[CONTEXT OVEREXTEND]` `GB-EVAL-042` (`S3076-P565-C006-E7172`, R3): human=`ثقة` vs machine=`يعرف بالمجمر بسكون الجيم وضم الميم [الأولى] وكسر الثانية وكذا [كان] أبوه ثقة`
- `[CONTEXT OVEREXTEND]` `GB-EVAL-046` (`S3076-P617-C006-E7924`, R1): human=`صحابي` vs machine=`صحابي نزل بيت المقدس وهو آخر من مات من الصحابة بها وزعم ابن حبان أن اسمه شمعون`
- `[CONTEXT OVEREXTEND]` `GB-EVAL-061` (`S3076-P429-C010-E5154`, R5): human=`صدوق يهم` vs machine=`صدوق يهم ورمي برأي الخوارج`
- `[CONTEXT OVEREXTEND]` `GB-EVAL-062` (`S3076-P434-C007-E5227`, R1): human=`صحابي جليل` vs machine=`صحابي جليل له حديث في الأضاحي`
- `[CONTEXT OVEREXTEND]` `GB-EVAL-067` (`S3076-P403-C003-E4760`, R2): human=`ثقة ثبت إمام أعلم أهل عصره بالحديث وعلله` vs machine=`ثقة ثبت إمام أعلم أهل عصره بالحديث وعلله حتى قال البخاري ما استصغرت نفسي إلا عند علي ابن المديني`
- `[CONTEXT OVEREXTEND]` `GB-EVAL-073` (`S3076-P620-C005-E7948`, R1): human=`صحابي` vs machine=`صحابي له حديث`
- `[CONTEXT OVEREXTEND]` `GB-EVAL-077` (`S3076-P276-C013-E2934`, Rabstain_precondition_unmet): human=`ثقة` vs machine=`ثقة وكان`
- `[CONTEXT OVEREXTEND]` `GB-EVAL-078` (`S3076-P225-C013-E2165`, R1): human=`صحابي` vs machine=`صحابي له حديث ذكر أبو موسي المديني أن اسم أبيه بولا بموحدة وكان عبدا نوبيا`
- `[CONTEXT OVEREXTEND]` `GB-EVAL-081` (`S3076-P453-C011-E5515`, R1): human=`صحابي` vs machine=`صحابي سكن البصرة`
- `[CONTEXT OVEREXTEND]` `GB-EVAL-082` (`S3076-P613-C006-E7903`, R5): human=`صدوق يخطىء` vs machine=`صدوق يخطىء ورمي بالرفض`
- `[CONTEXT OVEREXTEND]` `GB-EVAL-084` (`S3076-P474-C007-E5819`, R5): human=`صدوق فيه لين` vs machine=`صدوق فيه لين ورمي بالقدر`
- `[CONTEXT OVEREXTEND]` `GB-EVAL-098` (`S3076-P084-C008-E0103`, R2): human=`ثقة حافظ` vs machine=`ثقة حافظ له تصانيف`
- `[CONTEXT OVEREXTEND]` `GB-EVAL-099` (`S3076-P231-C002-E2235`, R1): human=`صحابي` vs machine=`صحابي له حديث في العيادة والطب أخرجه أبو داود عن سعد غير منسوب فذكره المزي تبعا لغيره في مسند سعد ابن أبي وقاص وأفرده ابن حبان والطبراني والباوردي`
- `[CONTEXT OVEREXTEND]` `GB-EVAL-113` (`S3076-P744-C009-E8544`, R1): human=`صحابية` vs machine=`صحابية لها سابقة وهجرة عاشت إلى خلافة معاوية`
- `[CONTEXT OVEREXTEND]` `GB-EVAL-114` (`S3076-P178-C005-E1496`, R3): human=`ثقة` vs machine=`ثقة أمي`
- `[CONTEXT OVEREXTEND]` `GB-EVAL-116` (`S3076-P678-C007-E8410`, R1): human=`صحابي` vs machine=`صحابي له رواية عن جرير ابن عبد الله حسب`
