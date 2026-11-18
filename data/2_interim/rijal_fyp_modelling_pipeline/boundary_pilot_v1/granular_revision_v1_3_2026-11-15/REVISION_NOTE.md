# Granular boundary revision v1.3 (draft)

This is a new, non-destructive revision. The original reviewer CSV, v1.2 granular copy, and frozen v1 snapshot remain unchanged.

## What was corrected

- The v1.2 derivative used broad `nisba` and `kunya` subroles, which obscured the original reviewer's indexed labels. This draft restores `nisba`, `nisba_1`, `nisba_2`, `nisba_3`, `kunya`, `kunya_1`, and `kunya_2` where the original label order maps one-to-one to the revised spans.
- Every one of the 189 nonblank original reviewer label spans is preserved verbatim in `ORIGINAL_REVIEWER_LABEL_LEDGER.csv`, with case ID and exact character offsets into the original entry. `segment_N_original_label_refs` links the revised segmentation back to these original labels where spans overlap.
- For TB-022, `ثم الكوفي` is split into separate spans: `ثم` (`temporal_sequence_marker` / `temporal_transition`) and `الكوفي` (`narrator_name_or_identity` / `nisba_2`). The prior `المدني` span is restored as `nisba_1`.

## Label counts preserved

Original reviewer labels:

- `assessment_or_grade`: 5
- `assessment_qualification_or_scope`: 3
- `biographical_fact`: 8
- `biographical_fact_death`: 1
- `biographical_fact_occupation`: 7
- `biographical_fact_residence`: 4
- `death_age`: 3
- `death_location`: 1
- `death_year`: 14
- `disambiguation_note`: 2
- `full_name`: 24
- `generation_classification`: 19
- `grade_or_assessment`: 13
- `kunya`: 14
- `kunya_1`: 1
- `kunya_2`: 1
- `name_ism`: 1
- `nickname_laqab`: 1
- `nisba`: 13
- `nisba_1`: 9
- `nisba_2`: 9
- `nisba_3`: 1
- `pronunciation_guide`: 3
- `source_citation`: 14
- `source_citations`: 4
- `specific_criticism_or_attributed_report`: 11
- `status_or_companion_classification`: 3

Restored granular subrole counts:

- `kunya`: 13
- `kunya_1`: 1
- `kunya_2`: 1
- `nisba`: 13
- `nisba_1`: 9
- `nisba_2`: 9
- `nisba_3`: 1
- `temporal_transition`: 1

The indexed suffixes retain the original reviewer's ordering labels. They are not a new historical or geographic interpretation. The temporal label for TB-022 follows the user's instruction and does not assign a date or claim a more specific life event than the wording provides.

## Review status

`TAQRIB_BOUNDARY_ANNOTATIONS_GRANULAR_V1_3_DRAFT.csv` is a revised working copy pending the user's review. It is not a replacement for or modification of frozen v1.
