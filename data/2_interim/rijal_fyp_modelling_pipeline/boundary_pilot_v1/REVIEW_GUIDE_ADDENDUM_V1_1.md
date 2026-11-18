# Review Guide Addendum v1.1 — Corrected Draft

This addendum applies only to `BOUNDARY_PILOT_REVIEW_CORRECTED_2026-11-15.csv`. The original reviewer submission and original `REVIEW_GUIDE.md` remain unchanged.

## Entry-number span

The corrected copy includes the printed/listed prefix (for example, `١٢-`) as its own first segment with role `source_entry_number`. It is a source-layout marker, not narrator identity, assessment wording, or a rank. Whitespace after the marker is preserved with the following text span.

## Lossless segmentation

The corrected copy has 15 segment slots to accommodate the full entry plus separate qualifications, commentary, and reference symbols. Concatenate the nonblank `segment_N_text_verbatim` fields in numeric order to recover `entry_text_verbatim` exactly. Spaces and punctuation belong to an adjacent segment; no text should be discarded.

## Role normalization

The corrected copy uses the guide's broad role labels. The original reviewer's more detailed labels have been retained in the untouched submission and mapped in the corrected copy as follows:

- Names, lineage, kunya, nisba, and nicknames → `narrator_name_or_identity`.
- Life dates, location, occupation, and other biographical details → `biographical_fact`.
- `source_citation` / `source_citations` → `source_or_transmission_symbol`.
- `grade_or_assessment` → `assessment_or_grade`.
- Qualifications such as `له أوهام`, `تغير بأخرة`, `يغرب`, and `يخطىء` are separated from the adjacent assessment where the phrase boundary is clear.
- Reported or possible identity claims whose resolution is not established remain `uncertain`.
- Descriptive transmission wording that is not plainly an explicit criticism uses `other_text` rather than being promoted to a criticism label.

These role choices are structural suggestions for the boundary pilot. They assign none of Ibn Ḥajar's twelve ranks and do not establish historical attribution or factual truth.

## Confirmation state

`boundary_review_complete` is `no` and `boundary_confidence` is blank in the corrected copy. The original reviewer values are preserved separately as `original_reviewer_completion_value` and `original_reviewer_confidence_value`. The corrected copy is an AI-assisted draft; those original values do not mean the reviewer has confirmed the repairs.
