# Gate B Blind Manual-First Evaluation Guide v0.1 (TODO Lines 38-42)

**Protocol Rule:** annotate [BLIND_EVALUATION_SHEET_120_V0_1.csv](BLIND_EVALUATION_SHEET_120_V0_1.csv) strictly BEFORE opening `SEALED_MACHINE_PROPOSALS_120_V0_1.csv`. Freeze the human-only sheet first with its own SHA-256 hash before comparing against machine proposals.

## Sampling & Exclusion Guarantee
- Total numbered corpus: `8827`
- Excluded development/prior-review entries: `1405` (boundary pilot `25`, priority-12, evaluative statements `866`, phrase occurrence `81`, none-found `161`, worksheet/scan example triplets, and both Gate A `100`-entry sample audits).
- Eligible completely unseen pool: `7422`
- Blind sample drawn (`N=120`, `seed=20261119`, shuffled display order): `{'anchor_rank_2_5_10': 15, 'anchor_rank_3_4': 25, 'anchor_rank_6_corroboration': 15, 'anchor_rank_7_8_9': 15, 'companion_status_cue': 10, 'rare_rank_11_12': 5, 'tamiz_boundary': 5, 'unanchored_multiword_or_qualified': 30}`

## Annotation Instructions (12 Ranks Preserved; Zero Silent Collapsing)
1. `human_entry_eligibility`: `eligible_grade_or_status` | `non_grade_biographical_or_tamiz` | `unresolved_or_abstain`
2. `human_first_complete_target_span_exact`: copy exact verbatim Arabic of the first complete grade/status phrase (Policy v0.2), or leave blank for non-grade.
3. `human_context_note_spans_exact`: copy any attached/later qualifiers kept separate from the target label.
4. `human_source_rank_1_to_12_or_abstain`: assign `1`..`12` ONLY when source-definition preconditions are satisfied; otherwise use `abstain_precondition_unmet` (e.g. Rank 6 `مقبول` without corroboration, Rank 7/9 without transmitter evidence, disputed `رؤية`), `abstain_non_grade`, or `abstain_ambiguous`.
5. Single-researcher scope (`TODO` line 40): report agreement, rank/construction disagreements, false suggestions, and abstentions as a single-researcher feasibility check; do not claim inter-reviewer reliability.
