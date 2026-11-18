# Taqrīb phrase occurrence review v1

This package is the entry-level follow-up to phrase review v1.1. It lists 81 distinct local Taqrīb entries whose first-grade AI-review span exactly matches one of the 18 phrase groups with a user-recorded phrase-level decision. It is a review package, not an annotation output.

## Files

- [Blank human review copy](ENTRY_LEVEL_REVIEW_V1.csv): full Arabic source text, source locators, and blank human decision fields. Save a dated copy when annotating so this template remains available.
- [Separate AI suggestions](AI_SUGGESTIONS_V1.csv): the same 81 cases with full text and Codex’s first-pass suggestions. This is advisory and has not been accepted as human annotation.
- [Manifest](MANIFEST.json) and [checksum](MANIFEST.sha256): input and output hashes.

## What the AI pass suggests

- 44 entries are straightforward candidates under the Rank 3 attributed-proxy convention.
- 8 are candidates with a context note to preserve.
- 23 remain conditional for status ambiguity, identity uncertainty, or conflicting evaluations.
- 5 Ibn Ḥibbān listing phrases should not inherit the direct-attribution Rank 3 mapping.
- 1 bracketed span needs boundary review.

These are suggestions about the local entry wording only. They do not establish historical authorship, transmission provenance, target suitability, or a final rank label. The 52 candidate suggestions still need human confirmation before use. If you want to assess human-only agreement, hide the AI file until the human copy is frozen.

## How to review

Read the full Arabic source entry in each row. The row’s phrase-group decision records the phrase-level policy; the entry-level human fields are deliberately blank. Do not copy a phrase-level decision into an entry-level label without checking the full entry.

Fill the six `human_...` fields in the blank copy:

- `human_phrase_role_in_context`: grade, status, biographical, context, or unresolved.
- `human_is_first_complete_target_phrase`: yes, no, or unclear under target policy v0.2. Consider earlier grade/status wording as well as this phrase.
- `human_qualification_or_conflict`: none, present, or unclear; quote the relevant Arabic wording in reviewer notes.
- `human_critic_attribution`: preserved, missing, not_applicable, or unclear.
- `human_entry_disposition`: retain_as_candidate, conditional, abstain, exclude_later_phrase, or needs_repair. This is a review disposition, not a production rank label.
- `human_reviewer_notes`: brief rationale, especially exact earlier/later spans and source-text issues.

The `phrase_first_char_offset_zero_based` is only a mechanical location of the exact phrase in the entry text. The source `entry_id`, printed page, number, and full text were joined from the local corpus index. The generator checked that source entry text exactly matches the text in the no-hit review input. AI rank suggestions and confidence were omitted; the AI file contains only textual/context suggestions and full source entries.

See the decision limits in [phrase review v1.1](../rank_label_phrase_review_v1_1_2026-11-16/HUMAN_DECISION_LOG_V1_1.md).
