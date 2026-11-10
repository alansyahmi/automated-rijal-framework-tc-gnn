# Forensic verification summary

## Scope and inputs

The original `narrators.parquet` was available and read without modification (18,989 narrator rows). The classification uses the original `garh` three-element entries and preserves all flagged source-ID occurrences. This is a structural audit; it does not correct source data or establish historical speaker identity.

## Corrected counts

- Flagged source IDs in the previous queue: 432.
- Original source IDs with no matching well-formed three-element entry found: 0.
- Mutually exclusive classifications from tuple evidence:
- `citation_plus_commentary_or_multiple_sources`: 28
- `field_order_reversal_observed`: 52
- `mixed_record_structures_including_reversal`: 316
- `unnumbered_suffix_variant`: 12
- `unresolved_original_structure`: 24
- Total in exclusive classifications: 432.
- Exactly 420 IDs in the earlier queue carry a `multiline` heuristic flag. Their tuple-based classification is:
  - `citation_plus_commentary_or_multiple_sources`: 28
  - `field_order_reversal_observed`: 52
  - `mixed_record_structures_including_reversal`: 316
  - `unresolved_original_structure`: 24
- Thus the previous 420 figure is reproducible as a multiline-feature count, not as an inversion count. Direct reversal evidence occurs in 368 IDs, including IDs with mixed occurrences. The earlier 386 detailed-inversion count is not reproducible from a supplied per-ID classification rule and does not match this direct evidence count.
- The old classifier assigned every non-suffix ID to inversion without inspecting original tuples. This verification requires explicit structural evidence and distinguishes compound and mixed cases.
- 12 IDs exhibit the unnumbered suffix pattern, but its interpretation as harmless formatting should not be extended to other records without checking both original fields.

## Controls, titles, and fwaed

- The same 30 IDs selected in the prior review were inspected in the original Parquet. Their per-record text, locator, newline, multiwork indicators, and other anomalies are in `CONTROL_SAMPLE_VERIFICATION.csv`. The prior single repeated observation string was not evidence and is withdrawn.
- All 47 title-collision candidates and their underlying citation variants are retained in `VERIFIED_TITLE_COLLISIONS.csv`. String-prefix evidence is marked medium at most; canonical title, edition, and quotation-derived status remain unresolved absent bibliographic authority data.
- Narrator 6142's complete `garh` and `fwaed` nested values were compared in `FWAED_VERIFICATION.md`. Raw labels, structure, and category counts are reported separately from semantic interpretations.

## Confirmed and unsupported claims

Confirmed: Parquet can be read; every exported classification traces to original tuple values; the third tuple element matches the source ID used to join each extracted entry; raw source text includes both normal-order and compound/multilocative structures; title candidates are normalized strings rather than verified authority records.

Unsupported: all non-suffix flags are field inversions; all 420 multiline IDs represent a single reversed template; every repeated title is a legitimate edition/page reference; all source IDs denote passages/pages/entries; the 13 expected `fwaed` labels are semantically verified relation types; category labels alone justify graph edges or node features.

## Remaining uncertainties and next step

Some records combine a primary locator with prose or a secondary bibliographic locator, so quotation/citation segmentation is not reliably recoverable by newline or string length alone. Several ID-level patterns are mixed across occurrences. Preserve raw fields and use a stratified expert review of ambiguous tuple templates plus a documented Shamela schema/concordance lookup before defining cleaning rules. Do not sanitize, deduplicate, merge IDs, construct a graph, define targets, or train a model from this review alone.
