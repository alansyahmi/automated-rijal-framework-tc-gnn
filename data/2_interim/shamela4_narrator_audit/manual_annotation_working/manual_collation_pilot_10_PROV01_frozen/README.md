# PROV-01-C01 first-pass freeze

**Status:** User approved for first-pass freezing on 2026-11-13 after validation.
**Scope:** PROV-01-C01 only. The full Round 1 working copy is included under `working_copy_snapshot/` for relational context; no other case is approved or frozen by this package. No legacy annotation values were imported.

## Frozen annotation

- **Identity:** `confirmed` for HadithDB narrator 17, `جَابِرَ بْنَ عَبْدِ اللهِ الْأَنْصَارِيَّ`, matched to Taqrīb entry 871. Identity evidence is al-Jarḥ wa-al-taʿdīl entry 2019; the identity rationale excludes `له صحبة`.
- **Candidate-field correspondence:** `exact`; the original `صحابي` value matches the Taqrīb status phrase `صحابي` in the local corpus. This records textual correspondence, not the historical origin of the HadithDB value.
- **S01:** `صحابي`, `descriptive_or_generational_status`, blank rank number, `rank_status=unranked`, `target_task_scope=status_only_candidate`. It is a Companion-status classification, not an ordinary reliability grade. Any first-category/rank mapping is reserved for separate adjudication.
- **S02:** `ابن صحابي`, `biographical_or_factual_statement`, `rank_status=not_applicable`, outside the defined task.
- **S03:** `غزا تسع عشرة غزوة`, biographical/factual statement, outside the defined task.
- **S04:** `ومات بالمدينة بعد السبعين`, biographical/factual statement; wording preserved without date normalization.
- **S05:** `وهو ابن أربع وتسعين`, biographical/factual statement; wording preserved without age normalization.
- **S00:** retained as a superseded placeholder.
- **Attribution:** evaluator fields are `not_applicable` for these non-evaluative statements. For S01-S05, wording author is `unknown`, compiler authorship is `unresolved`, and historical provenance route is `unresolved`. Ibn Hajar remains recorded as author/compiler of Taqrīb in source metadata; this does not establish claim-level wording authorship.
- **Statement evidence:** al-Jarḥ `له صحبة` and al-Mizzī `صاحب رسول الله ﷺ` are linked to S01; al-Mizzī `وابن صاحبه` is linked to S02. The frozen schema has no corroboration-specific evidence role, so these statement-level links use `other` for these specific supporting excerpts; this does not redefine `other` generally. `unresolved_corroboration` is retained because source dependence is not traced. HadithDB is dataset evidence, not independent historical corroboration.
- **Locators:** HadithDB's Taqrīb citation `1/192` vs local corpus p. 136 remains unresolved. HadithDB's al-Mizzī citation `4/443` vs local phrase on p. 444 remains unresolved. Printed page images were not visually inspected.

## Validation and limits

- Full test suite: 72 tests passed.
- PROV-01 schema, enum, and row-link checks: passed.
- The strict package-wide validator did not pass: it stopped at pre-existing `sources.csv` row 13 (`SRC-PROV-10-C01-ID01`, blank `source_work_id`), outside this freeze scope. The mutable working copy also does not include the migration mapping and legacy snapshot tables required by that package-wide validator. No unrelated records were changed.
- AI-assisted single-reviewer feasibility annotation; not independent expert validation or inter-reviewer agreement.
- This freeze establishes neither historical attribution nor source independence, narrator reliability, or historical-input eligibility.

The research memo and complete working-copy snapshot are included in this package.
