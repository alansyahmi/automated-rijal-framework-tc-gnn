# Gate A Morphological Candidate Scan v0.1 (Declensions + Verb Derivations)

**Status:** discovery-only morphological scan over all `8,827` numbered local *Taqrīb* entries (`ENTRY_INDEX.csv`). Zero canonical ranks assigned and zero rules enabled.

## Corpus-Wide Results
- Entries scanned: `8827`
- Entries with at least one word-bounded morphological candidate hit: `8506`
- Morphological families scanned: `25`
- Distinct surface forms observed: `177` (`10588` total occurrences)
- **New surface forms beyond v0.1 exact token vocabulary (`203` strings):** `124` distinct forms (`1297` occurrences)
- Entries from the `161` `none_found` set with at least one morphological hit: `44`

## Files
- [MORPHOLOGICAL_FAMILY_SUMMARY_V0_1.csv](MORPHOLOGICAL_FAMILY_SUMMARY_V0_1.csv): per-root family summary (unique entries, distinct surface forms, new forms beyond v0.1).
- [MORPHOLOGICAL_SURFACE_FORMS_V0_1.csv](MORPHOLOGICAL_SURFACE_FORMS_V0_1.csv): every observed declension/derivation surface form with verbatim examples, local context windows, and blank `human_census_disposition` for Gate A review.
- [NONE_FOUND_161_MORPH_HITS_V0_1.csv](NONE_FOUND_161_MORPH_HITS_V0_1.csv): subset of the `161` `none_found` entries matched by the expanded morphological scan for manual inspection.
