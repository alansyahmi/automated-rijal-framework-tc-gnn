# Taqrīb Rank-Cue Shadow Run v1

**Status:** shadow scan complete; no rank labels were assigned or accepted.

## What was scanned

- Local source pages: 688
- Numbered entry strings extracted: 8827
- Duplicate printed page/entry-number keys: 3 (3 extra numbered rows; IDs also use source-chunk position)
- Nonempty unnumbered chunks excluded from the entry scan: 3459
- Source-defined cue examples searched: 33 across the twelve ranks
- Exact source-cue occurrences: 8332 across 7445 entries
- Existing candidate registry rules scanned: 10
- Candidate-registry phrase occurrences: 5831 across 4696 entries

## How to read the results

The scanner searched exact strings without spelling, punctuation, diacritic, or orthographic normalization. It retained local page IDs, Shamela page IDs, printed page numbers, entry numbers, character offsets, and surrounding source text. It also records overlapping cue matches so that a shorter cue inside a compound is not silently treated as a standalone phrase.

Every row in `CUE_OCCURRENCES.csv` and `CANDIDATE_RULE_HITS.csv` is an unreviewed lexical occurrence. `rank_assignment` / `assigned_rank` stays blank, and `auto_accept` is false. A full entry occurrence does not prove that the matched phrase is a complete assessment statement. Context-dependent ranks need the extra evidence stated in the source definition.

## Source-cue occurrences by rank anchor

| Rank anchor | Cue strings | Exact occurrences | Entries with at least one hit |
| ---: | ---: | ---: | ---: |
| 1 | 1 | 118 | 117 |
| 2 | 3 | 131 | 131 |
| 3 | 4 | 2553 | 2358 |
| 4 | 3 | 1965 | 1963 |
| 5 | 10 | 367 | 343 |
| 6 | 2 | 1600 | 1599 |
| 7 | 2 | 223 | 223 |
| 8 | 1 | 422 | 422 |
| 9 | 1 | 795 | 794 |
| 10 | 4 | 158 | 145 |
| 11 | 1 | 0 | 0 |
| 12 | 1 | 0 | 0 |

These are lexical occurrence counts. They are not counts of assigned labels or rank coverage.

## Existing candidate-rule occurrence counts

| Rule | Exact occurrences | Entries | Rule state |
| --- | ---: | ---: | --- |
| `RANK_THIQA_EXACT_001` | 2322 | 2313 | `candidate_not_enabled` |
| `RANK_SADUQ_ERROR_EXACT_001` | 147 | 147 | `candidate_not_enabled` |
| `RANK_SADUQ_IKHTILAT_EXACT_001` | 1 | 1 | `candidate_not_enabled` |
| `GEN_FROM_THIRD_EXACT_001` | 1314 | 1314 | `candidate_not_enabled` |
| `GEN_FROM_TENTH_EXACT_001` | 773 | 773 | `candidate_not_enabled` |
| `GEN_FROM_SENIOR_TENTH_EXACT_001` | 108 | 108 | `candidate_not_enabled` |
| `GEN_FROM_SENIOR_SEVENTH_EXACT_001` | 31 | 31 | `candidate_not_enabled` |
| `GEN_FROM_EIGHTH_EXACT_001` | 510 | 510 | `candidate_not_enabled` |
| `GEN_FROM_ELEVENTH_EXACT_001` | 534 | 534 | `candidate_not_enabled` |
| `GEN_FROM_TWELFTH_EXACT_001` | 91 | 91 | `candidate_not_enabled` |

Every candidate-rule occurrence remains unreviewed; the registry rules remain disabled and no labels were applied.

## Files

- `ENTRY_INDEX.csv`: numbered local source entries, copied verbatim.
- `RANK_CUE_INVENTORY.csv`: source-defined examples and cue notes used for the scan.
- `CUE_OCCURRENCES.csv`: every exact cue occurrence and overlap/context indicators.
- `CUE_COUNTS_BY_RANK.csv`: occurrence and unique-entry counts, not label counts.
- `CANDIDATE_RULE_HITS.csv`: exact occurrences of existing, still-disabled candidate registry rules.
- `CANDIDATE_RULE_COUNTS.csv`: per-rule occurrence counts, including zero-hit rules.
- `RULE_REGISTRY_SNAPSHOT.csv`: registry input copied for this run.
- `RUN_MANIFEST.json` and its checksum: input/output hashes, counts, and scope limits.

No data source, frozen annotation, rule registry, or rank label was modified. This run is an inventory aid for human review, not an evaluation of the rules or evidence that a model can be trained.
