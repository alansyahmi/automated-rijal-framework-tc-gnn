# PROV-04 first-pass freeze (PROV-04-C01 and PROV-04-C02)

**Status:** User approved for case-scoped Pass 1 freezing on 2026-11-13.
**Scope:** PROV-04 (`PROV-04-C01` and `PROV-04-C02`) only. The full Round 1 working copy is included under `working_copy_snapshot/` for relational context; no other case is approved or frozen by this package. No rank adjudication or legacy reconciliation is included.

## Frozen annotation

### Candidate 1: PROV-04-C01 (Taqrib 5569, confirmed match)
- **Identity:** `confirmed` for HadithDB narrator 278, `قَيْسُ بْنُ حَفْصٍ`, matched to Taqrib entry 5569 (p. 456, sequence 5554). Supported by a two-sided non-grade bridge: `EVID-PROV-04-C01-ID02` (grade-free HadithDB `/278` biographical extract excluding `الرتبة عند ابن حجر`, `طبقة رواة التقريب`, and `الجرح والتعديل`) and `EVID-PROV-04-C01-ID01` (`al-Jarh wa-al-taʿdil` vol. 7, p. 95, entry 546). Al-Mizzi `Tahdhib al-Kamal` entry 4899 (`24/21-23`) provides biographical correspondence with potential literary dependence between al-Mizzi and Taqrib explicitly noted. Raw `/278` snapshot is kept separately in `EVID-PROV-04-C01-DATA01`.
- **Candidate-field correspondence:** `exact` (`ثقة له أفراد`).
- **S01:** `ثقة له أفراد`, `qualified_narrator_grade` (base `ثقة`, qualification `له أفراد` preserved open in Arabic without assuming negative qualification), blank rank number, `rank_status=unranked`, `target_task_scope=unresolved`, `historical_input_eligibility=not_assessed`, `corroboration_status=unresolved_corroboration`.
- **S02:** `من العاشرة`, `descriptive_or_generational_status`, `rank_status=not_applicable`, `target_task_scope=not_in_defined_task`.
- **S03:** `مات سنة سبع وعشرين`, `biographical_or_factual_statement`, `rank_status=not_applicable`, `target_task_scope=not_in_defined_task`, `temporal_policy_result=cannot_assess`.
- **Attribution & historical context:** `S01` has `evaluator_value_status=none_named`, `passage_evaluator_naming_status=no_evaluator_named`, `wording_author_value_status=unknown`, `compiler_authorship_status=unresolved`, `transmission_route_status=unresolved`. Earlier reports collected in al-Mizzi `4899` (`ثقة`, `لا بأس به، كتبت عنه شيئا يسيرا`, `شيخ`) remain distinct contextual evidence (`EVID-PROV-04-C01-HIST-CONTEXT01`).

### Candidate 2: PROV-04-C02 (Taqrib 5570, rejected homonym mismatch)
- **Identity:** `mismatch`, supported by `EVID-PROV-04-C02-ID01` (`Tahdhib al-Kamal` vol. 24, p. 24, entry 4900 `تمييز`, Basran who settled in Egypt and died in 281 AH), distinguishing entry 5570 from HadithDB 278 (d. 227 AH).
- **Candidate-field correspondence:** `substantial_difference` (`مقبول` vs `ثقة له أفراد`).
- **S01-S03 (`مقبول`, `من الثانية عشرة`, `مات سنة إحدى وثمانين`):** retained strictly for audit completeness of rejected candidate `5570`; `S01` remains `unranked` (no Rank 6 assigned) and all `PROV-04-C02` statements carry `target_task_scope=not_in_defined_task` and `historical_input_eligibility=not_applicable`.

## Validation and limits

- PROV-04 case-scoped schema, enum, and row-link checks: passed.
- Target-extraction filter (`filter_analytical_rows` / `ordinary_grade_candidate_conditions_pass`): strictly excludes `PROV-04-C02` (and `PROV-04-C01` while unranked/unresolved in Pass 1).
- Printed page images were not visually inspected; single-reviewer AI-assisted Pass 1 feasibility record; does not establish rank, target suitability, or historical-input eligibility.
