# Annotation automation v1.0.1 dry-run evaluation

**Date:** 2026-11-14  
**Review set:** 34 statement rows from the 10-case pilot  
**Input:** [reconciled human review CSV](./HUMAN_REVIEW_reconciled.csv)

## Result

The rule set produced five Rank 3 or Rank 5 suggestions. All five now align with the recorded review disposition in this pilot: three were marked `accept` in the user's review file, and the two disputed `صدوق يخطىء` rows were confirmed as Rank 5 after checking the source. The earlier Rank 6 entries remain visible in `human_rank_number_as_entered` for audit.

This is **5/5 observed alignment in a small, purposively selected pilot**, not a general accuracy estimate. The reviewed statements are nested within cases and candidate entries, so they are not 34 independent observations.

| Review outcome | Count | Interpretation |
| --- | ---: | --- |
| Rank proposals | 5 | All were Rank 3 or Rank 5 taxonomy proposals. |
| Proposals marked `accept` in the original review file | 3 | PROV-40, PROV-39 and PROV-10; their `human_rank_number` cells remain blank. |
| Rank 5 confirmations after source check | 2 | PROV-56 and PROV-37; the original entered Rank 6 is retained separately. |
| Automated abstentions | 29 | The user did not review whether abstaining was correct. |
| Abstentions with rule family explicitly confirmed | 5 | These five confirm `generation_status` only; they do not validate the abstention. |
| Other `generation_status` abstentions without explicit family confirmation | 4 | No conclusion recorded about these family labels or the abstentions. |
| Abstentions with blank rule family | 20 | No rule-family confirmation recorded. |

The rank mapping is consistent with the separate Rank 5 taxonomy decisions in the [PROV-56 adjudication](../manual_annotation_working/manual_collation_pilot_10_PROV56_frozen/adjudication/PROV-56-C01_ADJUDICATION.md) and [PROV-37 adjudication](../manual_annotation_working/manual_collation_pilot_10_PROV37_adjudication/PROV-37-C01_ADJUDICATION.md). Those records rely on the local transcription; the printed page image was not visually inspected.

## What this dry run establishes

- The tested taxonomy rules can produce Rank 3 and Rank 5 proposals that the reviewer accepted or confirmed in these five rows.
- The reviewer distinguished confirmation of a `rule_family` label from review of an abstention. Those are now recorded separately.
- The reconciliation does not establish that the 29 abstentions were appropriate. Some abstention rows also contain other reviewer-entered fields; those fields were not counted as review of the abstention itself.

## What it does not establish

- General precision, recall, coverage, or performance on records outside this purposive pilot.
- Correctness of the abstention decisions or whether the rules missed other straightforward cases.
- Independent or inter-reviewer agreement. One reviewer made these decisions, with AI assistance in preparing the rules.
- Historical attribution, narrator reliability, target suitability, or eligibility for model training.

## Recommended operating status

Keep the rules in **proposal-only dry-run mode**. The canonical input has `auto_accept=false`; do not enable automatic acceptance on this evidence. Do not use this pilot to train a model.

If abstention behavior is to be evaluated next, review a small targeted set: first the 4 `generation_status` rows without explicit family confirmation, then a few blank-family abstentions with different text constructions. The review question should be whether a clear existing rule applies or the system should continue to abstain. Do not broaden the rules until those cases have been examined.

## Reconciliation and provenance

This report uses only the new reconciliation copy. The original user-edited CSV, canonical generated CSV, frozen annotations, and prior audit outputs were left unchanged. See [the reconciliation manifest](./RECONCILIATION_MANIFEST.json) for input and output hashes and the exact treatment of reviewer-entered values.
