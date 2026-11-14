# PROV-02-C01 first-pass freeze

**Status:** User approved for case-scoped Pass 1 freezing on 2026-11-13.
**Scope:** PROV-02-C01 only. The full Round 1 working copy is included under `working_copy_snapshot/` for relational context; no other case is approved or frozen by this package. No rank adjudication or legacy reconciliation is included.

## Frozen annotation

- **Identity:** `confirmed` for HadithDB narrator 27, `وَمَعْمَرٌ`, matched to Taqrib entry 6809. Supported by a two-sided non-grade bridge: `EVID-PROV-02-C01-ID02` (grade-free HadithDB `/27` biographical extract, excluding `الرتبة عند ابن حجر`, `طبقة رواة التقريب`, `الرتبة عند الذهبي`, and `الجرح والتعديل`) and `EVID-PROV-02-C01-ID01` (`al-Jarh wa-al-taʿdil` vol. 8, p. 255, entry 1165). Unmodified `/27` raw record is retained separately in `EVID-PROV-02-C01-DATA01`.
- **Candidate-field correspondence:** `minor_variation`; shares grade and qualification wording with Taqrib entry 6809, while the local Taqrib corpus brackets `[وعاصم بن أبي النجود]` and HadithDB presents it unbracketed with minor punctuation differences.
- **S01:** `ثقة ثبت فاضل إلا أن في روايته عن ثابت والأعمش [وعاصم بن أبي النجود] وهشام ابن عروة شيئا وكذا فيما حدث به بالبصرة`, `qualified_narrator_grade` (base `ثقة ثبت فاضل`, qualification preserving the complete exception clause), blank rank number, `rank_status=unranked`, `target_task_scope=unresolved`, `historical_input_eligibility=not_assessed`, `corroboration_status=unresolved_corroboration`.
- **S02:** `من كبار السابعة`, `descriptive_or_generational_status` (generation 7, not rank 7), `rank_status=not_applicable`, `target_task_scope=not_in_defined_task`.
- **S03:** `مات سنة أربع وخمسين`, `biographical_or_factual_statement`, `rank_status=not_applicable`, `target_task_scope=not_in_defined_task`, `temporal_policy_result=cannot_assess`.
- **S04:** `وهو ابن ثمان وخمسين سنة`, `biographical_or_factual_statement`, `rank_status=not_applicable`, `target_task_scope=not_in_defined_task`.
- **Attribution:** `S01` has `evaluator_value_status=none_named`, `passage_evaluator_naming_status=no_evaluator_named`, `attribution_form=unclear`, `wording_author_value_status=unknown`, `compiler_authorship_status=unresolved`, `transmission_route_status=unresolved`. Evaluator-specific fields for `S02-S04` are `not_applicable`.
- **Historical context & textual note:** Al-Mizzi `Tahdhib al-Kamal` entry 6104 reports concerning Thabit, al-Aʿmash, Hisham ibn ʿUrwa, and Basra are preserved as contextual evidence (`EVID-PROV-02-C01-HIST-CONTEXT01`), not collapsed into one undifferentiated weakness and not treated as an inferred source route for Ibn Hajar. The Awwamah digital transcription footnote on `[وعاصم بن أبي النجود]` is preserved in `EVID-PROV-02-C01-TAQRIB-EDITORIAL01`.

## Validation and limits

- PROV-02 case-scoped schema, enum, and row-link checks: passed.
- Working-copy manifest and SHA-256 sidecar verified before snapshot copy.
- Printed page images were not visually inspected; single-reviewer AI-assisted Pass 1 feasibility record; does not establish rank, target suitability, or historical-input eligibility.
