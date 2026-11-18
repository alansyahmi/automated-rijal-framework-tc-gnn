# Evaluative statement layer v0.1

**Status:** draft annotation layer for review. It is not a frozen schema, a rank dictionary, a production rule set, or a numeric scoring model.

## Purpose

This package separates statement-level praise, criticism, status, and unknownness from the existing target label. Ibn Ḥajar's original twelve categories remain the only rank taxonomy. The new dimensions describe what a statement says and how it is worded; they do not add ranks or change an entry's canonical rank.

## Files

- [Draft codebook](EVALUATIVE_STATEMENT_LAYER_CODEBOOK_DRAFT_V0_1.md) defines the proposed annotation dimensions, values, and safeguards.
- [Illustrative proposal rows](EVALUATIVE_STATEMENT_LAYER_EXAMPLE_PROPOSALS_V0_1.csv) apply the draft dimensions to phrases raised during review. These are AI suggestions for discussion; all human-decision columns are blank.
- [Blank annotation template](EVALUATIVE_STATEMENT_LAYER_TEMPLATE_V0_1.csv) provides the proposed columns without prefilled decisions.

## How to use this draft

Review the codebook and example proposals before using the template on corpus statements. Preserve exact Arabic spans and attribution. Keep claims of consensus separate from wording force and reviewer confidence. An accusation, an applied label, and a claim of collective agreement are distinct statement forms.

The draft has no numeric strength values and assigns no ranks. Do not convert its ordinal wording-force descriptions into a 0–1 score. Any future scoring method would need a separate research question, operational definitions, and validation.

## Source-context pilot

The first 16-entry [source-context review pilot](../evaluation_statement_layer_context_pilot_v0_1_2026-11-16/README.md) applies the draft categories to complete local entries. The [workbook](../../../../outputs/evaluative_statement_layer_pilot_v0_1_2026-11-16/REVIEW_SET.xlsx) keeps reviewer decisions blank and does not ask for rank labels.
