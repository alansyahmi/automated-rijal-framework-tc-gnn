# Consolidated Evaluative Statement Decisions v0.1 (Batch 01 + Batch 02)

**Status:** consolidated single-reviewer acceptance across Batch 01 (`33` occurrence rows) and Batch 02 (`889` overlap-span cases). Zero canonical ranks or numeric scores assigned.

## Headline Counts

- Lossless decision ledger rows (`CONSOLIDATED_DECISION_LEDGER_922_ROWS_V0_1.csv`): **922** (`33` Batch 01 + `889` Batch 02)
- Unique deduplicated review cases (`CONSOLIDATED_REVIEW_CASE_DECISIONS_V0_1.csv`): **916** out of `9,508` overlap-span cases in the local Taqrīb inventory
- Batch overlap breakdown: `batch_02_only` (**886**), `batch_01_only` (**27**), `batch_01_and_batch_02` (**3**: `SPAN-000001`, `SPAN-000653`, `SPAN-001217`)
- Unique source entries covered: **866** out of `8,827` numbered local entries
- Cases with non-empty `attribution`: **164**
- Cases with non-empty `qualification`: **39**

## Distributions Across the 916 Consolidated Review Cases

### `statement_match_use`
- `complete_statement`: 376
- `component_of_larger_statement`: 529
- `unrelated_substring`: 11

### `statement_family`
- `criticism`: 229
- `mixed`: 51
- `not_applicable`: 11
- `praise`: 221
- `status_or_biography`: 321
- `unknownness`: 80
- `unresolved`: 3

### `statement_domain`
- `biographical_information`: 1
- `companion_status`: 320
- `doctrinal_position`: 57
- `fabrication`: 5
- `general_reliability`: 249
- `honesty_veracity`: 30
- `memory_precision`: 99
- `not_applicable`: 11
- `other`: 2
- `transmission_practice`: 22
- `unknownness_or_majhul_status`: 79
- `unresolved`: 41

### `claim_content`
- `accusation_of_lying`: 30
- `biographical_fact`: 3
- `fabrication_label`: 5
- `general_commendation`: 202
- `general_criticism`: 151
- `hadith_theft_or_appropriation`: 1
- `mixed_assessment`: 46
- `not_applicable`: 11
- `qualified_commendation`: 20
- `specific_transmission_criticism`: 44
- `status_assertion`: 319
- `superlative_commendation`: 3
- `unknownness_assertion`: 79
- `unresolved`: 2

### `claim_mode`
- `attributed_individual_judgement`: 105
- `direct_statement`: 383
- `first_person_knowledge_gap`: 4
- `not_applicable`: 11
- `reported_or_hedged_claim`: 129
- `specific_behavior_or_transmission_observation`: 3
- `status_or_biographical_statement`: 262
- `unresolved`: 19

### `wording_force`
- `emphatic`: 5
- `not_applicable`: 263
- `plain_direct`: 439
- `qualified_limited`: 203
- `superlative`: 3
- `unresolved`: 3

### `consensus_wording`
- `collective_agreement_claimed`: 2
- `none`: 619
- `not_applicable`: 263
- `scope_or_referents_unclear`: 29
- `unanimity_wording_claimed`: 2
- `unresolved`: 1

### `reviewer_confidence`
- `high`: 606
- `low`: 37
- `medium`: 273

## Scope and Limitations

- Decisions reflect single-reviewer acceptance of AI advisory proposals on the selected Batch 01 and Batch 02 spans only; they do not generalize automatically to unselected corpus occurrences.
- Because Batch 02 exhaustively selected rare phrases (`<= 15` distinct entries) and deterministically sampled 10 distinct entries per common phrase, these percentages reflect the review sample rather than corpus-wide prevalence.
- `canonical_rank` and `numeric_score` remain completely blank (`0` assigned).
