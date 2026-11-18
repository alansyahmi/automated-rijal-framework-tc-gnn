# AI review instructions: entries with no exact inventory hit

This is a candidate-discovery review of the complete local Arabic entry strings. These rows had no exact hit in the current phrase inventory. That does not mean they lack an evaluative phrase.

For every row, complete the matching `BATCH_NN_AI_REVIEW.csv` and preserve all source columns byte-for-byte at the text level. Use only the entry text and repository's `IBN_HAJAR_12_RANK_SOURCE_INVENTORY_V0.md` plus `RANK_TARGET_POLICY_V0_2.md` as the rank framework. Do not use earlier annotations or external biographical claims.

## Output fields

- `ai_first_grade_span_exact`: exact contiguous substring of the entry text for the first complete grade-bearing/evaluative phrase. Use `none_found` if none; use `uncertain: <exact candidate substring>` if unsure.
- `ai_rank_candidate_1_to_12`: a rank number only when the wording and the source definition support it; otherwise `unresolved`, `not_applicable`, or `conditional`.
- `ai_phrase_type`: `standardized_grade`, `specialized_evaluation`, `status_or_biography`, `non_grade_description`, or `uncertain`.
- `ai_attached_qualifier_exact`: exact contiguous qualification attached to the candidate, `none_observed`, or `uncertain`.
- `ai_context_note_spans_exact`: exact relevant note spans, separated by ` || `; use `none_observed` if none. Do not invent fine-grained affiliation labels.
- `ai_context_note_types`: broad terms such as `memory_or_transmission`, `attribution`, `affiliation_or_innovation`, `biographical`, `generation`, or `other`; use `none` if none.
- `ai_status`: `candidate`, `conditional`, `unresolved`, or `no_candidate`.
- `ai_confidence`: `high`, `moderate`, or `low`.
- `ai_reason`: short reason tied to wording and the rank definition; state missing conditions.

Do not turn a lexical cue into a rank when the definition needs evidence not present in the entry. In particular, rank 6, 7, 8, 9, 10, 11, and 12 have context or evidence distinctions; the source inventory describes them. Keep rank 1 status separate from ordinary grade. Preserve the full first phrase and qualifications. Do not normalize Arabic, rewrite the entry, or assign a final label.

All results are AI suggestions for human review. They do not establish historical attribution, identity, target eligibility, accuracy, or annotation reliability.
