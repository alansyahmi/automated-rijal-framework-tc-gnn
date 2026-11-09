# Shamela4 stage-two diagnostics

## Source-reference diagnostics

- Source IDs examined: 54,334
- IDs flagged for manual review: 432
- Title candidates linked to multiple IDs: 47

| Citation-shape flag | Count |
|---|---:|
| simple_single_line_candidate | 54,260 |
| multiline | 462 |
| long_citation_string | 107 |
| possible_multiple_work_or_clause | 13 |
| multiple_volume_page_locators | 12 |

Flags are triage heuristics; they do not establish whether an identifier refers
to a book, volume, page, or passage.

## fwaed diagnostics

- Occurrences: 15,963
- Distinct raw labels: 25
- Unexpected labels: 12
- Occurrences under unexpected labels: 16

| Entry JSON type | Count |
|---|---:|
| list | 15,963 |

Unexpected labels are retained verbatim. Scholar-name detection is a weak
heuristic. Human inspection must decide whether a label is a person, subtopic,
malformed category, or legitimate additional evidence class. JSON types describe
serialization shape, not semantic function.

## Outputs

- source_id_review_queue.csv
- title_candidate_review_queue.csv
- fwaed_unexpected_labels.csv
- fwaed_entry_shapes.csv
- STAGE2_SUMMARY.json

No raw input is modified and no source ID, category, or quotation is recoded.
