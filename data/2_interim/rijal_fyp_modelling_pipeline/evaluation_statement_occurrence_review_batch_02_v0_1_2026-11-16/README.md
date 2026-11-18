# Evaluative statement occurrence review — batch 02

**Purpose:** reduce duplicated review effort while preserving every raw phrase match. This package organizes source text; it does not classify or label statements.

## How overlap deduplication works

The raw occurrence inventory has 11,478 phrase-hit rows. This package groups hits within the same entry when their character intervals overlap. Each connected interval group becomes one `review_case_id`; the link table retains every original `occurrence_id`, exact phrase, offset, boundary flag, and prior Batch 01 acceptance. Adjacent but non-overlapping intervals remain separate cases.

The grouped span is only the union of overlapping lexical matches. It is **not** asserted to be a complete scholarly statement boundary. The human reviewer should use the full entry text and record corrected span offsets when needed. The case can include substrings and compounds; the link table is the audit trail back to each candidate cue.

## Batch 02 selection

Frequency is measured by distinct source entries per exact phrase. Phrases appearing in at most 15 distinct entries are included exhaustively, except for exact occurrence IDs already accepted in Batch 01. For each more frequent phrase, the package selects up to 10 distinct entries using SHA-256 ordering with fixed seed `shamela4-occ-review-batch02-v0.1-2026-11-16`; at most one occurrence of that phrase is selected per entry. Exact Batch 01 accepted occurrence IDs are excluded from new selections in both strata. When a selected span overlaps other candidate phrases, all its phrase associations remain visible.

This is a reproducible review workload, not a probability sample designed to estimate corpus-wide accuracy. Phrase strata overlap, and the same case may be selected for more than one cue. Do not add per-phrase sample sizes to estimate unique statements.

## Files

- `UNIQUE_OVERLAP_SPAN_REVIEW_FRAME_V0_1.csv`: all deduplicated overlap groups, with full source entries and blank human fields.
- `PHRASE_HIT_TO_REVIEW_CASE_LINKS_V0_1.csv`: lossless mapping of all raw phrase hits to review cases, including every exact span and any previous accepted occurrence.
- `BATCH_02_REVIEW_CASES_V0_1.csv`: the selected cases for review; blank human fields are ready for annotation.
- `BATCH_02_PHRASE_SAMPLING_PLAN_V0_1.csv`: each phrase's frequency, stratum, method, and selected counts.
- `MANIFEST.json` and `MANIFEST.sha256`: input/output checksums and counts.

## Human fields

Record whether the cue is a complete statement, a component of a larger statement, an unrelated substring, or unresolved; then identify the statement role and exact full statement span in the source entry. Record the referent, attribution, qualification, confidence, and notes only when supported by the text. Leave a field blank rather than infer it. No rank, historical truth, source independence, narrator reliability, or numeric score is assigned here.

The AI proposals accepted in Batch 01 remain limited to their 33 selected occurrences. They are shown as prior decisions in the link table and do not transfer to other occurrences of those phrases.
