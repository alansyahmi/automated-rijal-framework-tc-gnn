# Taqrīb two-layer rank-candidate inventory v0.1

**Status:** full numbered-entry phrase scan complete; no rank labels assigned or accepted.

## Scope

- Local numbered entry strings scanned: 8,827.
- Exact candidate phrase definitions searched: 50.
- Candidate-role occurrence rows: 8,555.
- Context-note occurrence rows: 3,777.
- Candidate definitions come from the source inventory's illustrative examples, existing inactive rank registry phrases, and exact forms observed in the priority-12 AI pilot. They are not exhaustive.
- Matching is exact Unicode substring matching only: no orthographic normalization, fuzzy matching, or semantic classification.

## Reading the candidate outputs

`ENTRY_FIRST_CANDIDATE_SUMMARY.csv` reports the earliest lexical candidate hit in each numbered entry. It does **not** establish that the hit is the first complete grade-bearing phrase. Some strings are substrings of longer words, compounds, qualifications, or attributed/contextual notes. Review boundary flags, overlaps, full source text, and the separate context-note file before deciding.

Source rank anchors and pilot rank proposals are explicitly unverified. `rank_assignment` and `human_disposition` remain blank in occurrence outputs; no candidate rule was enabled or auto-accepted. Entries without an exact hit are not proven to lack a rank phrase, because the inventory is incomplete.

The two layers are:

- **Grade/target candidates:** exact source-anchor, inactive-rule, and pilot target phrases that may be the first grade-bearing phrase.
- **Context-note candidates:** exact source or pilot phrases that may be an attached qualification, affiliation/innovation reference, transmission note, or attributed judgement. Their relation to a target is not inferred by this scan.

## Source and coverage limits

The scan uses the previously hashed local `pages.jsonl` extraction: it starts at printed page 75, omits the rank introduction, and contains 688 page rows. It includes 8,827 numbered entry strings; 3,459 nonempty unnumbered chunks were not included in that numbered-entry index. The rank introduction's cue list is illustrative, not exhaustive. These results are occurrence counts, not rank counts, label coverage, precision, recall, or model performance.

## Files

- `PHRASE_INVENTORY.csv`: exact phrase definitions, sources, candidate roles, and occurrence counts.
- `GRADE_CUE_OCCURRENCES.csv`: exact candidate occurrences and context windows.
- `CONTEXT_NOTE_OCCURRENCES.csv`: exact context-note candidate occurrences; relations are not assigned.
- `ENTRY_FIRST_CANDIDATE_SUMMARY.csv`: one row per numbered entry, with earliest lexical candidate and full source entry.
- `PHRASE_COUNTS.csv`: exact occurrence and unique-entry counts by phrase.
- `MANIFEST.json` and checksum: input/output hashes and scope metadata.

No frozen annotation, source entry, rank assignment, or automation registry state was modified.
