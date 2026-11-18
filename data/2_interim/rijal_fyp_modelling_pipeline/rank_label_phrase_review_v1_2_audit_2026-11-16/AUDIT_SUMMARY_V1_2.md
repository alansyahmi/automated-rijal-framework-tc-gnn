# Phrase Review v1.2 Audit Summary: Remaining 130 Groups + 161 None-Found Entries (TODO Line 16)

**Status:** second-pass audit prepared over `PHRASE_REVIEW_WORKSHEET_V1_1.csv` (`18` already decided + `130` newly audited) and `NONE_FOUND_AUDIT_161.csv` (`161` rows). All `130` blank phrase rows and `161` none-found rows keep `human_*` fields blank pending your approval.

## 1. Remaining 130 Phrase Groups (`PHRASE_REVIEW_148_AUDIT_V1_2.csv`)

Recommended dispositions for the **130** newly audited groups (applying v1.1 precedents + Consolidated v0.1 empirical findings):
- `abstain`: **11**
- `accept`: **49**
- `conditional`: **61**
- `revise`: **9**

Combined **148**-group totals if approved (`18` v1.1 + `130` v1.2):
- `abstain`: **11**
- `accept`: **60**
- `conditional`: **68**
- `revise`: **9**

### Key Highlights Across the 130 Groups
- **Span repairs (`revise`):** `صحابية مشهور` -> `صحابية مشهورة`; `وثقه يعقوب ابن` -> `وثقه يعقوب ابن سفيان`; `ضعفه الأزدي من الرابعة ق` -> `ضعفه الأزدي`; `ضعفه يحيى ابن معين...` -> `ضعفه يحيى ابن معين`; `الصحابي` -> check `الصحابي الجليل` / `الصحابي المشهور`; `خادم رسول الله ﷺ خدمه عشر سنين` -> trim or keep biographical Rank 1; `ثقه` -> word-bounded variant only (79/84 corpus hits are substrings); `أحد الحفاط` -> flag source typo for `أحد الحفاظ`; `وثقه` -> `روى عنه النسائي ووثقه`.
- **Non-subject referent / word-boundary traps (`conditional`):** `بدري` (6/11 direct Batch 02 hits were `العبدري`/`العبدرية`), `أم المؤمنين` (5/15 direct hits were relatives), `أحد العشرة` (Talhah in `SPAN-000020`), `صحابي معروف` (Anas in `SPAN-003953`).
- **v1.1 Precedents Applied:** `وثقها العجلي` -> `accept` (matching `وثقه العجلي`); `ثقات التابعين`, `ذكره ابن حبان في الثقات`, `ذكره جماعة في ثقات التابعين`, `من كبار التابعين الثقات`, `أجمعوا على ثقته`, `مجمع على ثقته`, and all `13` remaining disputed Companion/`رؤية` phrases -> `conditional`; `وقد وثق` (`ليس بمشهور [وقد وثق]`), `ثقات الأمراء`, `ليس بأهل أن يروى عنه`, `كذبه الشعبي في رأيه`, `يسرق الحديث`, and vague Family 08 phrases -> `abstain`.
- **Evidence-conditioned Ranks 6-12:** `متهم بالكذب` (`accept` Rank 11 candidate with entry guard) and `ما به بأس` (`accept` Rank 4 candidate); all `لين`/`ضعف`/`لا يعرف`/`كذبه ...`/`تركوه` forms stay `conditional` pending Rank 6-12 preconditions.

## 2. 161 `none_found` Entries (`NONE_FOUND_161_AUDIT_V1_2.csv`)

- `abstain`: **136**
- `conditional`: **25**

Category breakdown:
- `biographical_eminence_not_12_rank_cue`: **3**
- `empty_entry_text_source_gap`: **1**
- `explicit_non_companion_biographical`: **3**
- `implicit_companion_prophetic_relation`: **7**
- `knowledge_gap_la_arif_no_narration_or_relative`: **5**
- `non_grade_biographical_or_crossref`: **99**
- `tamiz_disambiguation_no_grade`: **30**
- `unnamed_narrator_context_lam_yusamma`: **12**
- `unnamed_narrator_with_html_tag_artifact`: **1**
