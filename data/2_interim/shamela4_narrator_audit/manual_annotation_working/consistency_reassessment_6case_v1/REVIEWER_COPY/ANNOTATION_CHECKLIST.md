# Annotation checklist for the six-case repeat

This is the list of decisions to record, not a set of prefilled answers. Do not use AI-proposed case labels during the repeat. Use the frozen Schema v2.2 and Protocol v1.0 enums; preserve unresolved evidence as unresolved.

## Pass A: identity, before opening Pass B

For every candidate row:

- Decide `identity_match_status` using only grade-independent identifiers.
- Record the exact identity evidence and locator you relied on.
- Explain why the lineage, kunya, nisbah, relationship, geography, chronology, or other evidence supports or fails to support the match.
- For multiple candidates, assess each candidate separately; retain plausible alternatives and positively identified homonyms.
- Preserve spelling and lineage differences verbatim. Do not normalize them or treat a difference as a contradiction without evidence.
- Record confidence and any unresolved question. Do not use the masked Pass A excerpt as a source quotation.

## Pass B: source correspondence and annotation

For each candidate:

- Compare the original field to the full Taqrīb entry. Record the exact corresponding source span, textual differences, locator, and rationale. Textual correspondence does not establish historical provenance.
- Segment the entry into distinct claims. Add one `PASS_B_STATEMENT_DECISIONS_BLANK.csv` row per claim; preserve exact Arabic wording, including qualifications, reported markers, punctuation, brackets, and alternatives.
- Classify the statement under Schema v2.2. Keep a meaningful grade qualification with its grade; separate unrelated status, generational, date, age, parentage, and other factual claims.
- Record any taxonomy rank only with the supporting Taqrīb-introduction rule and citation. Keep Companion status separate from ordinary reliability ranks. Do not reuse later adjudication values from memory or the old files; re-derive and cite the rule.
- Complete attribution as separate questions: named evaluator, wording author, compiler authorship, attribution form, intermediary, historical evaluator attribution, and transmission route. Do not infer one from another.
- Add source metadata and evidence rows with exact excerpts and locators. Distinguish local-corpus transcription from inspected print witnesses and record what you actually checked.
- Assess target-task scope separately from historical-input eligibility. Do not make either decision from a plausible grade string alone.
- Record corroboration only when source relationships are examined. Similar wording or appearance in multiple works does not establish independent corroboration.
- Where evidence is missing or ambiguous, record what remains unknown and why. A blank, `not_assessed`, `unknown`, `unresolved`, and `not_applicable` are not interchangeable.

## Freeze and later comparison

- Keep the original Pass 1 files unchanged.
- Freeze Pass A before opening Pass B; freeze Pass B before viewing the internal key or original annotations.
- Compare identity, candidate matching, segmentation, statement type, base/qualification, rank taxonomy, text correspondence, attribution dimensions, target scope, historical-input eligibility, and uncertainty status separately.
- For every changed decision, record whether the cause was new evidence, clarified interpretation, transcription correction, memory/attention, or a remaining disagreement.
- Report this as a within-researcher operational consistency check. Six cases cannot establish expert validity, inter-reviewer agreement, corpus-wide reliability, or ML readiness.
