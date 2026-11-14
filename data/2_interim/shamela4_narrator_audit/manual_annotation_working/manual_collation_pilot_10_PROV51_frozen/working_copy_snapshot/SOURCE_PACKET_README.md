# Manual Collation Pilot 10: Review Round 1

This is a clean reviewer copy of the v2.2.2 scaffold. It keeps the frozen case order and both PROV-04 candidates. It omits old annotation values so you can make this first pass before reconciling it with the earlier work. The original v2.2.2 package remains preserved separately.

## Start here

Open these files in order:

1. `cases.csv` shows the original dataset name, narrator ID/name, and exact tuple field.
2. `candidate_entries.csv` shows the possible Taqrib entries, their full Arabic text, and their locators. Treat these as candidates to verify, not as a confirmed identity match.
3. `INDEPENDENT_TAQRIB_PILOT10_SOURCE_COLLATION.md` shows that each candidate text occurs in the local Taqrib corpus and compares the tuple string with the passage. It does not decide the narrator match or historical attribution.
4. `statements.csv` is where each separate claim or description from the entry is recorded. Its `-S00` rows are empty work placeholders, not claims.
5. `attribution_links.csv` records who is named as the source of a judgment, who authored the surviving wording, and whether a historical route is actually established.

`sources.csv` holds source metadata. Add exact source passages and locators to `source_evidence.csv` only after checking them. `date_claims.csv` and `feature_sources.csv` are empty schema tables for this round.

## Case order

Work in the packet's existing order: `PROV-10`, `PROV-40`, `PROV-39`, `PROV-56`, `PROV-24`, `PROV-51`, `PROV-01`, `PROV-02`, `PROV-04` (both candidates), then `PROV-37`.

## What to decide

For each candidate, decide separately whether the narrator identity and entry match are supported. Then split the entry into distinct evaluative or factual claims. Preserve exact Arabic wording, including qualifications and bracketed text. Do not treat a generation, date, or transmission symbol as a grade.

Use the frozen [Schema v2.2](../../../../../dataset_discovery/target_feasibility/MANUAL_COLLATION_SCHEMA_V2_2_FINAL.md) for the field definitions and allowed values.

For each statement, distinguish the named evaluator, the author of the wording, the attribution form, and any transmission route. A named earlier critic does not by itself prove a route or make the whole passage a verbatim quotation. Keep textual correspondence, ordinary-grade target suitability, and historical-input eligibility as separate decisions. If the evidence does not settle a field, use the schema's unresolved or not-assessed value and explain why.

Do not open prior working annotations until this first pass is frozen. They remain available separately for reconciliation. This is a single-reviewer feasibility exercise; it cannot establish inter-reviewer agreement or corpus-wide reliability.

The legacy rank and reviewer-note columns and the `legacy_v1_values.csv` table are omitted. `not_assessed` and `provisional_work_item` values are scaffold defaults, not completed judgments. This copy is a review workspace, not a publication-ready validated package. Preserve the original v2.2.2 output and this copy; reconcile later by `audit_record_id`, `candidate_entry_id`, and `statement_id`.
