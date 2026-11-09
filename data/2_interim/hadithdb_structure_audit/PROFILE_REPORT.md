# HadithDB duplicate-structure audit

- Extracted quotation occurrences: **40,524**
- Unique exact quotation strings: **35,216**
- Duplicate exact-text clusters: **3,639**
- Occurrences in duplicate clusters: **8,947**

## Duplicate cluster patterns

- within_record_multi_group: 3,240 clusters
- cross_record: 268 clusters
- within_record_same_group: 128 clusters
- mixed_within_and_cross_record: 3 clusters

## Structural validation

- JSON pointer checks: {'matched': 40524}
- Extracted/source record-name mismatches: 0

## Group-label literal-presence check

- Literal substring hits: 4,159 / 8,947 occurrence checks
- This is a string-presence signal after conservative Unicode, diacritic, and whitespace normalization. It is not evidence of speaker identity or resolved person identity.

## Interpretation

- within_record_multi_group: exact text occurs under multiple group labels within one biographical record.
- cross_record: exact text occurs in more than one biographical record.
- mixed_within_and_cross_record: a cluster spans records and has multiple labels within at least one record.
- within_record_same_group: repeated exact text occurs more than once under one record/group pair.
- These categories describe storage patterns only; they do not establish why the source repeated the text.
- Do not automatically deduplicate, discard occurrences, infer speaker identities, or assign ESA labels from these results.

## Output files

- duplicate_structure_summary.json: machine-readable summary.
- duplicate_structure_patterns.csv: one row per repeated exact quotation string.
- duplicate_group_key_examples.csv: occurrence-level details for repeated strings.
- record_group_semantics_sample.csv: records ranked by cross-group exact repetition.
