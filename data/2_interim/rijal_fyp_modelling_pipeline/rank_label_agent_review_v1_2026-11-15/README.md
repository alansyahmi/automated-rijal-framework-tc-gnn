# Taqrīb rank-cue AI review pilot v1

**Purpose:** blinded AI-assisted review of a small sample of full local Taqrīb entries. The reviewers propose a candidate interpretation or abstain; they do not create approved labels.

## Sample

- 60 entries total: 50 exact-cue cases (5 per source rank anchor with hits) and 10 entries without any exact rank-inventory cue or active rank-candidate registry phrase.
- Source rank anchors represented: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10. The v0 inventory had no exact occurrences for ranks 11 and 12, so those ranks are not tested by this sample.
- Source entries are unique in the sample. Sampling seed: 20261115.
- No-cue controls are not asserted to be negative examples; they may contain unlisted rank wording.

## Blinding and review

Give each reviewer only `BLINDED_REVIEW_PACKET.csv`, `AI_REVIEW_TEMPLATE_BLANK.csv`, and the rank definitions in `IBN_HAJAR_12_RANK_SOURCE_INVENTORY_V0.md`. Do not give them `INTERNAL_SAMPLE_KEY.csv`, the shadow-run cue hits, or other reviewers' results before their first pass. The source text is shown in full with its locators. Record a candidate rank separately from whether the entry itself establishes every condition in the definition. If required evidence is absent, mark the proposal as requiring external evidence or abstain; never force a rank.

## Interpretation limits

AI reviewers are not Arabic-trained human experts, and agreement among AI agents is not independent human validation. Their outputs are proposals for triage. This purposive sample cannot estimate corpus-wide precision, recall, or coverage. Do not overwrite frozen annotations, assign production labels, infer narrator reliability, or use the sample as model-training data.

`INTERNAL_SAMPLE_KEY.csv` maps cases to the hidden sample strata and exact shadow-run cues. Keep it separate until all blinded first-pass outputs are saved.
