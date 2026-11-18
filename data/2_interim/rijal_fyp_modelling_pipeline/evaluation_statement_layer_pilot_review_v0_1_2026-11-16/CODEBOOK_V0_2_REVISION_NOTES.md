# Statement Layer Pilot Audit and Codebook v0.2 Revision Notes

**Status:** Step 2 audit complete (`REVIEW_SET.xlsx` untouched; human decision cells remain blank for your sign-off).

## 1. Pilot Audit Summary (`PILOT_16_AI_CRITIQUE_AND_RECOMMENDATIONS_V0_1.csv`)

- Total pilot cases audited: **16** (`PILOT-01` to `PILOT-16`)
- Recommended `Looks right`: **10** (`PILOT-01`, `PILOT-02`, `PILOT-05`, `PILOT-06`, `PILOT-07`, `PILOT-08`, `PILOT-09`, `PILOT-11`, `PILOT-13`, `PILOT-14`)
- Recommended `Change` (codebook clarifications needed): **6** (`PILOT-03`, `PILOT-04`, `PILOT-10`, `PILOT-12`, `PILOT-15`, `PILOT-16`)

## 2. Specific Codebook v0.1 -> v0.2 Revisions Needed

1. **Formally adopt semicolon-separated multi-domain coding (`statement_domain`):**
   - In `REVIEW_SET.xlsx`, `PILOT-03` (`ثقة حافظ`) already uses `general_reliability; memory_precision` and `PILOT-11` (`جبل الحفظ وإمام الدنيا في فقه الحديث`) uses `memory_precision; jurisprudential_or_scholarly_merit`.
   - By contrast, single-domain coding in Consolidated v0.1 left **41** cases with `statement_domain = unresolved` (mostly `ثقة حافظ`, `ثقة فقيه عابد`, `صدوق حافظ`, `ثقه`, `تكلم فيه بعضهم`, `تكلموا فيه`, `اتهمه جماعة`, `كذبه الشعبي في رأيه`).
   - **Recommendation:** Allow semicolon-separated `statement_domain` values (`general_reliability;memory_precision`, etc.) in Codebook v0.2.
2. **Clarify `wording_force` for two-attribute praise compounds (`PILOT-03`, `PILOT-04`, `EX-005`):**
   - `PILOT-03` (`ثقة حافظ`) and `PILOT-04` (`ثقة ثبت`) set `wording_force = unresolved`, whereas Consolidated v0.1 coded them as `plain_direct`.
   - **Recommendation:** Define `plain_direct` for standard multi-attribute compounds (`ثقة ثبت`, `ثقة حافظ`, `ثقة متقن`), and reserve `emphatic` for literal repetition (`ثقة ثقة`) or explicit intensifiers.
3. **Establish deterministic precedence for `claim_mode` when signals co-occur (`PILOT-10`, `PILOT-12`, `PILOT-15`):**
   - `PILOT-10` (`قال ابن عبد البر أجمعوا على ثقته`): Pilot uses `attributed_individual_judgement`, while `EX-015` uses `direct_statement` and Batch 01 uses `reported_or_hedged_claim`.
   - `PILOT-12` (`[قال النسائي: لا أعرفه]`): Pilot uses `attributed_individual_judgement` on span `لا أعرفه`, while Batch 01 uses `first_person_knowledge_gap`.
   - `PILOT-15` (`قال الخليلي يسرق الحديث`): Pilot includes `قال الخليلي` in the span but uses `specific_behavior_or_transmission_observation` instead of `attributed_individual_judgement`.
   - **Recommendation:** Separate *who speaks* (`attribution_text`) from *epistemic stance* (`claim_mode`), and define a strict precedence hierarchy (e.g., named critic quote -> `attributed_individual_judgement`, with specific transmission behavior captured in `statement_domain` + `claim_content`).
4. **Align `statement_domain` on route-restricted praise (`PILOT-16`: `لا بأس بحديثه`):**
   - Pilot uses `general_reliability` while Batch 01 `ADV01-026` uses `transmission_practice` (because the entry restricts approval to `من رواية ابنه أحمد عنه لا من رواية ابن وهب`). Adopt `transmission_practice` (or `general_reliability;transmission_practice`) when route restrictions apply.

## 3. Newly Observed Span & Wording Additions from Consolidated v0.1 (`TODO line 106`)

Consolidated v0.1 (`916` cases) surfaced concrete boundary & wording extensions to consider in any vocabulary v0.2 (without enabling rank rules):
- Orthographic repair verified in local text: `صحابية مشهورة` (replacing truncated `صحابية مشهور`) and `وثقه يعقوب ابن سفيان` (replacing truncated `وثقه يعقوب ابن`).
- Full governed doctrinal clauses (`رمي بالإرجاء`, `رمي بالقدر`, `يرى القدر`, `رمي بالتشيع`, `رمي بالنصب`) rather than bare noun substrings.
- Scope-qualified criticism and comparative observations found in Batch 02: `متروك الحديث عن الزهري`, `فصار كتابه أثبت من حفظه`, `رأس المتقنين`, `من شيوخ بقية المجهولين`, `فلم يشهد بدرا`, and `يقال له صحبة والا فمجهول`.
- Compound tail observed beyond `ثقة ثبت`: `ثقة ثبت حجة` (`SPAN-000687`).
