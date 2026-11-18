# Phrase Review v1 Briefing: 148 No-Hit AI Phrase Groups and 161 None-Found Entries

**Status:** prepared for human review; zero human decisions or production rules approved.

## 1. Construction-Family Overview (148 Phrases, 1,050 No-Hit Entries)

| Construction Family | Phrases | No-Hit Entries | Sum of Corpus Word-Bounded Entry Hits |
| --- | ---: | ---: | ---: |
| `01_companion_status_direct` | 51 | 715 | 1058 |
| `02_companion_status_disputed_or_ruyah` | 15 | 76 | 130 |
| `03_unknown_status_ranks_7_9_or_unnamed` | 7 | 67 | 126 |
| `04_mild_or_attributed_weakness_ranks_6_8` | 14 | 68 | 297 |
| `05_attributed_authentication_rank3_proxy` | 26 | 80 | 186 |
| `06_praise_orthographic_and_compound_ranks_2_3_4` | 12 | 18 | 165 |
| `07_lying_fabrication_abandonment_ranks_10_11_12` | 16 | 19 | 21 |
| `08_general_criticism_innovation_or_non_grade` | 7 | 7 | 15 |

Note: corpus word-bounded entry sums can overlap across phrases (e.g., `صحابي` and `صحابي مشهور`) and are diagnostic counts, not label counts.

## 2. Recommended Review Actions (Advisory Only)

- `exclude_non_grade_or_not_first`: 3 phrases
- `keep_conditional_pending_evidence`: 45 phrases
- `keep_unresolved_or_abstain`: 17 phrases
- `prepare_candidate_with_boundary_guard`: 71 phrases
- `revise_span_before_candidate`: 12 phrases

## 3. Concrete Defects and Traps Detected Before Rule Promotion

1. **AI span truncations or over-long spans (must revise before promoting):**
   - `صحابية مشهور` (3 entries): missing final `ة`; source entries read `صحابية مشهورة`.
   - `وثقه يعقوب ابن` (`S3076-P325-C007-E3643`): truncated mid-name; full span is `وثقه يعقوب ابن سفيان`.
   - `ضعفه الأزدي من الرابعة ق` (`S3076-P387-C009-E4528`): appends generation and sigla (`من الرابعة ق`).
   - `ضعفه يحيى ابن معين ورمي بالإرجاء من التاسعة مات سنة خمس عشرة ت` (`S3076-P194-C002-E1726`): merges grade, innovation note, generation, death date, and sigla.
2. **Non-grade or non-first-phrase spans:**
   - `ثقات الأمراء` (`S3076-P549-C006-E6937`): reads `من ثقات الأمراء` (military/political leadership), not a hadith reliability grade.
   - `وقد وثق` (`S3076-P433-C010-E5214`): preceded by `ليس بمشهور` and bracketed (`ليس بمشهور [وقد وثق]`).
   - `ليس بأهل أن يروى عنه` (`E1141`, `E7777`): historical/tamyiz entries (al-Hajjaj b. Yusuf, Yazid b. Muawiyah).
3. **AI batch divergences on identical constructions (17 phrases):**
   - `وثقه النسائي` (10 Rank 3 vs 7 unresolved), `وثقه العجلي` (10 Rank 3 vs 6 unresolved), `وثقه ابن معين` (6 Rank 3 vs 5 unresolved), `وثقه ابن حبان` (5 Rank 3 vs 1 unresolved), `ذكره ابن حبان في ثقات التابعين` (4 Rank 3 vs 1 unresolved): Batch 1 treated attributed grades as unresolved while Batches 2-3 applied Policy v0.2.
   - `لا تعرف` (18 conditional vs 10 unresolved) and `لا يعرف` (17 conditional vs 7 unresolved): same Rank 7 vs 9 evidence gap labeled inconsistently across batches.
4. **Corpus substring collisions (never match without Arabic-letter boundaries):**
   - `بدري`: 23 of 33 corpus hits are substrings of the tribal nisba `العبدري`.
   - `ثقه`: 79 of 84 corpus hits are substrings of `وثقه` / `وثقها` / `أوثقه`; only 5 are standalone `ثقه` (orthographic variant of `ثقة`, including compounds `ثقه مقل عابد` and `ثقه عابد`).
   - `حافظ`: 12 of 158 hits are inside `الحافظ` / `بالحافظ` (including negation `لم يكن بالحافظ`); in `E7591` (`حافظ إلا أنهم اتهموه بسرقة الحديث`) it co-occurs with an accusation of hadith theft.
   - `صحابي`: 113 of 682 corpus hits are substrings (`الصحابي`, `صحابية`, `صحابيات`), including `غير الصحابي`, and 6 no-hit entries have trailing disputes (`وقيل لا صحبة له`, `نفاها بعضهم`, `لم يصح الإسناد إليه`).
5. **Audit of the 161 `none_found` rows (`NONE_FOUND_AUDIT_161.csv`):**
   - 138 `no_candidate` + 23 `unresolved` rows had `none_found` as `ai_first_grade_span_exact`.
   - Tag summary: `biographical_eminence_or_scholarship_cue` (3), `empty_entry_text` (1), `explicit_no_companionship` (3), `implicit_companion_or_prophetic_relation_cue` (7), `inline_html_tag` (1), `la_arif_statement` (5), `other_biographical_or_crossref` (99), `tamiz_entry` (32), `unnamed_narrator_lam_yusamma` (12)
   - Notable edge cases: 7 entries contain `رسول الله` (e.g., `شاعر رسول الله ﷺ`, `سبط رسول الله ﷺ`, `مولى رسول الله ﷺ`, `بنت رسول الله ﷺ`, `ابن عم رسول الله ﷺ`); `S3076-P164-C019-E1301` has empty text (`١٣٠١-`); `S3076-P732-C001-E8509` contains an inline HTML `<span data-type="title" id=toc-208>` tag inside `لم يسم`.

## 4. How to Complete Human Decisions

Review [PHRASE_REVIEW_WORKSHEET_V1.csv](PHRASE_REVIEW_WORKSHEET_V1.csv) by `construction_family` and fill only the four trailing human columns:
- `human_decision`: `accept`, `revise`, `conditional`, or `abstain`
- `human_approved_span_exact`: required when `revise` (or confirming exact wording)
- `human_rank_or_status_decision`: e.g. `1_status`, `3_attributed_proxy`, `7_or_9_conditional`, `exclude_non_grade`
- `human_notes`: rationale or precondition notes
