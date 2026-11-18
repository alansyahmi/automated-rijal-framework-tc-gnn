# Annotation automation v1.0.1 dry-run evaluation — corrected review interpretation

**Date:** 2026-11-14  
**Review set:** 34 statement rows from the 10-case pilot  
**Input:** [reconciled human review CSV](./HUMAN_REVIEW_reconciled.csv)  
**Record status:** This v2 interpretation supersedes the v1 report's treatment of five `accept` entries as family-only confirmation. The v1 package is preserved unchanged.

## Corrected result

The user's `accept` on five machine-abstained generation-status rows means the proposed rule family and output value were confirmed as correct. The abstention was therefore false in those five cases: the rule should have emitted its known output rather than abstaining. That output is `statement_type=descriptive_or_generational_status`, `taqrib_rank_number=null`, and `rank_status=not_applicable`. These are status statements, not narrator reliability ranks.

| Review outcome | Count | Interpretation |
| --- | ---: | --- |
| Rank proposals | 5 | All were Rank 3 or Rank 5 taxonomy suggestions. |
| Rank proposals marked `accept` in the user's file | 3 | PROV-40, PROV-39 and PROV-10; their explicit `human_rank_number` cells remain blank. |
| Rank 5 mappings confirmed after source check | 2 | PROV-56 and PROV-37; original Rank 6 entries are preserved in the audit column. |
| Machine abstentions | 29 | Five are now explicitly marked as false abstentions; 24 remain unreviewed for abstention correctness. |
| False abstentions confirmed | 5 | All have `generation_status` rule-family values and accepted statement-type outputs. |
| Other `generation_status` abstentions | 4 | No reviewer decision about these abstentions or outputs. |
| Blank rule-family abstentions | 20 | No reviewer decision about these abstentions or outputs. |

The five false-abstention records are: PROV-40-C01-S02, PROV-04-C01-S02, PROV-56-C01-S02, PROV-24-C01-S02, PROV-51-C01-S02. The four other `generation_status` rows and twenty blank-family rows remain unassessed. Values elsewhere in those abstention rows were not treated as abstention review unless the user's clarified `accept` explicitly confirmed the rule output.

The Rank 5 decision for `صدوق يخطىء` is consistent with the separate Rank 5 taxonomy decisions in the [PROV-56 adjudication](../manual_annotation_working/manual_collation_pilot_10_PROV56_frozen/adjudication/PROV-56-C01_ADJUDICATION.md) and [PROV-37 adjudication](../manual_annotation_working/manual_collation_pilot_10_PROV37_adjudication/PROV-37-C01_ADJUDICATION.md). Those records rely on the local transcription; the printed page image was not visually inspected.

## What this dry run establishes

- In this purposive sample, the reviewer accepted five exact generation-status rule outputs that the automation had withheld because those candidate rules were not enabled.
- The five accepted outputs do not assign narrator ranks: they classify a statement as descriptive/generational and mark rank as not applicable.
- The five Rank 3/5 suggestions align with the recorded dispositions after the Rank 5 source correction for PROV-56 and PROV-37.

## What remains unknown

- Whether the 24 remaining abstentions were appropriate, or whether any are additional false abstentions.
- General precision, recall, coverage, or performance outside this 10-case purposive pilot.
- Independent or inter-reviewer agreement. One reviewer made these decisions, with AI assistance in preparing the rules.
- Historical attribution, narrator reliability, target suitability, or eligibility for model training.

The 34 statement rows are nested within cases and candidate entries, not 34 independent observations. The five confirmed false abstentions describe this selected pilot only; they are not a corpus-level false-abstention rate.

## Recommended operating status

Keep the rules in **proposal-only review mode** with `auto_accept=false`. Do not promote the candidate generation rules to automatic acceptance solely from five cases. The exact output is confirmed for these five rows, but broader rule scope and false-abstention behavior have not been reviewed. Do not use this pilot to train a model.

If you continue the review, the next useful set is the four remaining `generation_status` abstentions and a few blank-family examples with different text constructions. For each, decide whether the same status-only output is clearly correct or whether the system should abstain. Preserve uncertain cases as unresolved.

## Reconciliation and provenance

This v2 package uses the unchanged canonical generated CSV and the user's original reviewed CSV. It preserves original entries in `human_decision_as_entered` and `human_rank_number_as_entered`, records accepted rule output separately, and leaves the original review file and the v1 reconciliation package unchanged. Hashes and exact change scope are in [the v2 manifest](./RECONCILIATION_MANIFEST.json).
