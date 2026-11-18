# Review Guide Addendum v1.2 — Broad Roles and Fine Subroles

This addendum applies to `BOUNDARY_PILOT_REVIEW_CORRECTED_GRANULAR_2026-11-15.csv`. It preserves the corrected v1.1 copy, the original reviewer submission, and the original guide.

## Why the CSV has two role levels

Each span has:

- `segment_N_role`: a broad, consistent parent role for high-level comparisons and for distinguishing assessment text from identity, biography, status, generation, and source symbols.
- `segment_N_subrole`: a more specific description, such as `full_name_or_lineage`, `kunya`, `nisba`, `death_year`, `assessment_qualifier`, or `source_reference_symbol`.

The two levels preserve useful detail without treating every detailed label as a separate rank or unrelated top-level class. Segment order and exact span text remain the primary record; role and subrole are annotations about those spans.

## Intended uses and limits

Granular subroles can help document which entry components a boundary procedure must separate, and may later support a sequence-tagging or auxiliary extraction task if the corpus is annotated at sufficient scale. Separating an assessment formula from a qualification is especially useful when evaluating how a complete phrase relates to Ibn Ḥajar's definitions.

These 25 purposively selected cases are too few and too construction-focused to train or evaluate a model reliably. Subroles do not themselves provide more examples of the twelve ranks, and name, biography, generation, and source-symbol subroles must not be mistaken for rank labels. Rank assignment remains a separate future step grounded in Ibn Ḥajar's original twelve categories and their contextual definitions.

## Confirmation state

The two-level labels in this file are AI-assisted structural proposals based on the preserved reviewer submission and the local text. The original reviewer role values remain in the dated submission. All corrected rows are still marked `boundary_review_complete=no`, with post-correction confidence blank, until the reviewer confirms or amends the draft.
