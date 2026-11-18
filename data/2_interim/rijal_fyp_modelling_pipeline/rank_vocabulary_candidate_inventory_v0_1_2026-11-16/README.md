# Twelve-rank candidate vocabulary inventory v0.1

**Status:** source-anchored candidate inventory; no entry ranks assigned and no production rules enabled.

## What is included

- 33 exact source cues from the twelve-rank introduction, with rank-definition conditions: `SOURCE_RANK_ANCHORS_V0_1.csv`.
- 55 phrases from candidate inventory v0.2.
- 148 phrase groups discovered in the three-batch no-hit AI review v1.3.
- 203 unique exact phrase strings across these inputs, joined without Arabic normalization and scanned in 8827 numbered local Taqrīb entries.
- Broad literal cue searches with examples: `SOURCE_CUE_SCAN_V0_1.csv` and `SOURCE_CUE_EXAMPLES_V0_1.csv`.
- Up to three corpus examples for each candidate phrase: `CANDIDATE_EXAMPLE_HITS_V0_1.csv`.
- Primary-source/edition verification: `SOURCE_ANCHOR_VERIFICATION.md`.

The 33 source cues include status, praise, weakness, unknownness, abandonment, accusation, and lying/fabrication. The candidate list is a work inventory, not every expression Ibn Ḥajar may use. The search is anchored to existing source examples, the v0.2 candidate inventory, and the 148 no-hit AI phrase groups.

## Read the columns carefully

- `source_rank_anchor_numbers` records where an exact phrase is named in the introduction.
- `v02_*_unverified` and `ai_nohit_*_unverified` preserve prior candidate suggestions; they are not accepted ranks.
- `phrase_policy_decision_v1_1` records only the phrase-level decisions from v1.1; it does not label each matching entry.
- `corpus_exact_substring_occurrences` counts literal occurrences. Arabic-letter-bounded counts help identify some substring collisions but do not establish semantic boundaries. Counts across phrase rows overlap and are not rank totals or coverage.
- `rank_assignment` is blank and `auto_accept` is false for every phrase.

## Rank safeguards

The introduction’s examples are illustrative, not exhaustive. A word hit cannot satisfy contextual definitions by itself. For example, Rank 6 `مقبول` depends on corroboration; Ranks 7 and 9 depend on different transmitter counts; Ranks 8 and 10 require distinct authentication/weakness conditions; Rank 11 accusation must remain distinct from Rank 12 applied lying/fabrication labels. Rank 5 memory terms and innovation descriptions need their full qualification. Rank 1 is status, separate from ordinary reliability. Generation wording such as `من العاشرة` is not reliability Rank 10.

The broad cue scan is literal substring discovery. It may hit negation, compounds, biography, or unrelated material; inspect the example contexts before adding a phrase. No stemming, normalization, or automatic classification is performed.

## Edition and corpus limits

The local numbered-entry index has 8,827 entries and begins at printed page 75; it excludes 3,459 nonempty unnumbered chunks. The opening rank introduction is absent from the local pages, so its anchors come from the separately documented Dorar/ʿAwwāma digital text. Preserve the rank 5 variant `تغير بأخرة` versus Alifta’s `تغير بآخره`, and the rank 10 variant `بقدح` versus `بقادح`. The searchable text is not a scan.

## Next review

Review candidates by rank and construction, not by frequency alone. For each observed phrase, record whether it is an exact introduction example, an observed candidate, context-dependent, non-grade/status material, or unresolved. Preserve complete source spans and counterexamples. Do not change the twelve ranks, infer historical attribution from lexical similarity, or enable a rule from this inventory alone.

See `MANIFEST.json` and `MANIFEST.sha256` for input/output hashes. Phrase-level decision counts copied from v1.1: {'conditional': 7, 'accept': 11}. Discovery-source row counts (overlap allowed): {'ai_nohit_phrase_review_v1_3_grouped_candidate': 148, 'candidate_inventory_v0_2': 55, 'source_inventory_v0_exact_anchor': 33}.
