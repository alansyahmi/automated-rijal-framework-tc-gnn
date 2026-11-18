# AI rank-cue review pilot: results summary

**Status:** three independent AI review passes completed. Results are proposals only; no production rank labels were assigned or accepted.

## Design

Three AI subagents reviewed the same 60 full Taqrīb entries independently. During first pass, each saw the blinded review packet and the v0 source inventory, but not the internal sample key, cue hits, or another reviewer's answer. The sample contains 5 cases for each exact source-cue anchor R1–R10 and 10 entries with no exact cue from the inventory or rank-candidate registry. The 60 entry IDs are unique. Ranks 11 and 12 had zero hits for their listed exact cues in the source scan and are not represented as cue strata; any agent proposal for those ranks arose from interpreting full entry wording, not from a rank-11/12 cue selection.

## Three-agent exact agreement

These are simple unanimity counts across three AI responses, **not accuracy, expert agreement, or inter-annotator reliability**.

| Dimension | Unanimous cases |
|---|---:|
| Candidate rank / none / abstain | 55/60 |
| Candidate status | 50/60 |
| Broad case type | 54/60 |
| Exact assessment span | 39/60 |
| Whether the entry's complete span was identified | 59/60 |
| Definition conditions supported by the entry | 25/60 |

There are 12 cases in `HUMAN_TRIAGE_QUEUE.csv` because at least one reviewer disagreed on rank, candidate status, broad type, abstained, or proposed unlisted wording. Exact span or condition disagreements also occur outside this priority queue; the full matrix in `AI_REVIEW_COMPARISON.csv` preserves them.

## Key limitation surfaced

Several definitions require evidence not available from a Taqrīb entry alone: corroboration, transmitter counts, authentication history, an underlying defect, or whether a narrator advocated an innovation. Reviewers often marked these conditions unverified. Such cases must remain conditional or unresolved; phrase matches alone cannot supply missing evidence.

At least two cases triggered a rank-10 versus rank-12 disagreement: one reviewer read wording as a direct rank-12-type label while the other two retained rank 10. These cases need careful review of exact formulation and the source definition; do not resolve by majority vote.

## What to do with these outputs

1. Review the 12 priority cases first, using the full entry and the rank definitions.
2. For unanimous proposals, spot-check entries before treating any as labels. Unanimity does not make them gold data.
3. Keep required external conditions unresolved unless separately documented.
4. Preserve all three reviewer files and this comparison. Do not overwrite frozen boundary annotations or assign production labels from this pilot.

The sample is purposive and cue-balanced, with no-cue controls. It cannot estimate corpus-wide precision, recall, or automation coverage. These agents are AI reviewers, not Arabic-trained human experts.
