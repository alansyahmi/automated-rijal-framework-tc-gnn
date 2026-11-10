# Forensic verification summary

## Scope and inputs

The original `narrators.parquet` was available and read without modification (18,989 narrator rows). The classification uses the original `garh` three-element entries and preserves all flagged source-ID occurrences. This is a structural audit; it does not correct source data or establish historical speaker identity.

## Corrected counts

- Flagged source IDs in the previous queue: 432.
- Original source IDs with no matching well-formed three-element entry found: 0.
- Mutually exclusive source-ID classifications:
- `confirmed_citation_only_then_locator_bearing_prose`: 32
- `confirmed_non_reversal_or_compound_structure`: 16
- `confirmed_structure_present_with_mixed_occurrences`: 245
- `unnumbered_suffix_variant_without_reversal_evidence`: 12
- `unresolved_or_mixed_tuple_structure`: 127
- Total in exclusive classifications: 432.

### Classifier rule and examples

The confirmed slot pattern requires slot 0 to contain a volume/page locator without a recognized prose cue or newline. Slot 1 must contain a recognized prose cue before a newline, with a locator after that newline. This specifically distinguishes locator-bearing prose from citation-only fields. Cue matching uses whole Arabic tokens/phrases; cues are indicators, not a language model or bibliographic parser.

Representative original tuples in `test_forensic_verification_v2.py`: source ID 137006 is a positive slot-pattern case; 25200 is a normal prose-then-citation negative; 92839 is a compound citation-plus-commentary negative; the suffix-bearing 25200 tuple is a citation-only-pair negative. These establish classifier behavior on examples, not corpus-wide compiler intent.

### Confirmed structural patterns

- 32 IDs have only tuples matching the explicit pattern: citation-only slot 0 followed by locator-bearing prose in slot 1, with a newline before a later locator.
- 245 additional IDs contain at least one such tuple but also mixed, suspected, or unresolved tuple structures.
- Combined, 277 IDs contain 304 tuple occurrences matching this confirmed shape. This is structural confirmation under the documented cue rules, not proof of compiler intent or a safe swap instruction.
- `12` IDs contain the unnumbered suffix pattern with no detected reversal evidence.

### Suspected or unresolved patterns

- 0 IDs have at least one weaker suspected-reversal tuple and no confirmed reversal tuple; 0 suspected tuple occurrences also occur within mixed IDs that have confirmed tuple evidence.
- 16 IDs have only observed non-reversal/compound patterns under these rules.
- 127 IDs remain unresolved or internally mixed without a confirmed reversal tuple.
- Tuple-level pattern counts:
- `citation_only_pair`: 12
- `citation_only_then_locator_bearing_prose`: 304
- `locator_bearing_prose_then_citation_only`: 221
- `prose_then_locator_bearing_commentary`: 30
- `unresolved_tuple_structure`: 321
- Tuple-level certainty counts:
- `confirmed_non_reversal`: 263
- `confirmed_structure`: 304
- `unresolved`: 321
- The earlier 420 count is a multiline-feature count, not an inversion count. The earlier 386 detailed-inversion figure is not reproducible from a supplied per-ID rule. Both should be treated as unverified inversion counts.

## Controls, titles, and fwaed

- The same 30 IDs selected in the prior review were inspected in the original Parquet. Their per-record text, locator, newline, multiwork indicators, and other anomalies are in `CONTROL_SAMPLE_VERIFICATION.csv`. The prior single repeated observation string was not evidence and is withdrawn.
- All 47 title-collision candidates have compact case summaries in `VERIFIED_TITLE_COLLISIONS.csv`; source-ID/citation associations are in `TITLE_COLLISION_CITATION_VARIANTS.csv` (54642 rows, one association per row to avoid oversized cells). These are evidence inventories and conservative triage labels, not an independent expert review of all 47 cases. Canonical title, edition, and quotation-derived status remain open pending that review and bibliographic authority evidence. The v2 manifest records non-zero byte size and SHA-256 for both CSVs.
- Narrator 6142's complete `garh` and `fwaed` nested values were compared in `FWAED_VERIFICATION.md`. Raw labels, structure, and category counts are reported separately from semantic interpretations.

## Confirmed and unsupported claims

Confirmed: Parquet can be read; every exported classification traces to original tuple values; the third tuple element matches the source ID used to join each extracted entry; raw source text includes both normal-order and compound/multilocative structures; title candidates are normalized strings rather than verified authority records.

Unsupported: all non-suffix flags are field inversions; all 420 multiline IDs represent a single reversed template; every repeated title is a legitimate edition/page reference; all source IDs denote passages/pages/entries; the 13 expected `fwaed` labels are semantically verified relation types; category labels alone justify graph edges or node features.

## Remaining uncertainties and next step

Some records combine a primary locator with prose or a secondary bibliographic locator, so quotation/citation segmentation is not reliably recoverable by newline or string length alone. Several ID-level patterns are mixed across occurrences. Preserve raw fields and use a stratified expert review of ambiguous tuple templates plus a documented Shamela schema/concordance lookup before defining cleaning rules. Do not sanitize, deduplicate, merge IDs, construct a graph, define targets, or train a model from this review alone.
