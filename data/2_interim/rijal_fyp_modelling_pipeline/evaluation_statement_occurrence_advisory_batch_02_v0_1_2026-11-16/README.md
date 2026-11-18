# AI Advisory Occurrence Review: Batch 02

**Status:** 889 source-linked AI advisory proposals matching `BATCH_02_REVIEW_CASES_V0_1.csv`. Zero human decisions, canonical ranks, or numeric scores are assigned. The original Batch 02 review CSV remains unmodified.

## Files

- [AI_ADVISORY_REVIEW_BATCH_02_V0_1.csv](AI_ADVISORY_REVIEW_BATCH_02_V0_1.csv): all 889 Batch 02 review cases with Draft Codebook v0.1 advisory proposals, exact statement spans, referent/attribution/qualification notes, and blank human decision/override columns.
- [AI_ADVISORY_SUMMARY_V0_1.md](AI_ADVISORY_SUMMARY_V0_1.md): counts by match use, statement family, and confidence, plus key context-sensitive traps.
- `MANIFEST.json` and `MANIFEST.sha256`: input and output checksums.

## Next use

Review `AI_ADVISORY_REVIEW_BATCH_02_V0_1.csv` row by row (or record decisions into a separate dated decision package, following the Batch 01 workflow). Enter `accept`, `change`, or `unsure` in `human_decision`, and use the `human_*` override columns whenever `change` is needed. Acceptance applies only to the reviewed `review_case_id` row, never to unselected corpus occurrences.
