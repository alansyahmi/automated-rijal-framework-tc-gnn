# Shamela4 tuple validation protocol (version 3)

## Purpose and boundary

This is a human-validation sample, not a new general-purpose classifier. It asks whether annotators can consistently identify the roles and boundaries of the first two text fields in the original three-element `garh` entries. No field is corrected, swapped, normalized, or deduplicated. The Parquet source and v1/v2 audit outputs remain unchanged. Do not use this exercise to build the narrator graph, set reliability targets, or train models.

## Sample design

The script selected 60 tuples with seed `20261111`, 10 from each of six strata. It samples from the 432 flagged source IDs, uses one tuple per source ID across the sample, and prioritizes the narrow formatting and compound strata before larger pools to reduce overlap. Available unused source IDs at selection time by stratum were: `{"unnumbered_suffix_or_formatting": 12, "compound_or_multiple_locator": 420, "mixed_source_ID": 239, "suspected_or_unresolved": 228, "normal_prose_then_citation": 157, "citation_only_then_locator_bearing_prose": 245}`. Selected counts: `{"unnumbered_suffix_or_formatting": 10, "compound_or_multiple_locator": 10, "mixed_source_ID": 10, "suspected_or_unresolved": 10, "normal_prose_then_citation": 10, "citation_only_then_locator_bearing_prose": 10}`. This is a purposive validation set, not a prevalence sample; its proportions must not be generalized to the corpus.

Each row preserves the source ID, narrator record ID/name, raw `garh` group label, entry index, exact three-element tuple JSON, and exact first/second field strings. The group label is a raw grouping key and must not be assumed to name the historical speaker.

## Structural pattern definitions

- `citation_only_then_locator_bearing_prose`: v2's strict visible pattern: field 1 has a volume/page locator without a recognized prose cue or newline; field 2 has a recognized prose cue before a newline and a locator after it. This is a confirmed tuple shape, not proof of intended field semantics.
- `locator_bearing_prose_then_citation_only`: prose cues occur in field 1 and field 2 has a locator without detected prose cues.
- `prose_then_locator_bearing_commentary`: field 1 contains prose cues, while field 2 contains both locator(s) and prose cues. Multiple citations or editorial/commentary text may coexist.
- `citation_only_pair`: both fields appear locator-bearing and contain no recognized prose cues. This includes some formatting variants; it does not mean two citations to separate works.
- `unresolved_tuple_structure`: the current cue/locator rules do not establish a role or stable boundary. This includes prose without a recognized cue.
- A `mixed_source_ID` sample row comes from an ID with more than one tuple pattern; the row's own automated pattern is still recorded separately.
- `suspected_*` patterns mean a weaker cue combination. They are not confirmation. The validation set includes suspected cases if available and unresolved cases otherwise.

## Human annotation instructions

Annotate from the preserved original fields. Use the full exact text, including line breaks, punctuation, Arabic spelling, and suffixes.

1. `human_field_1_role` and `human_field_2_role`: use one or more of `quotation/evaluation text`, `bibliographic citation`, `volume/page locator`, `secondary citation`, `commentary/editorial text`, `mixed`, `other`, or `unclear`. Explain non-obvious choices in reviewer notes.
2. `quotation_boundary` and `citation_boundary`: record each span as `field_1:start-end` or `field_2:start-end`, with zero-based Unicode code-point offsets and an exclusive end. Multiple disjoint spans may be separated by semicolons. If a boundary cannot be assigned, record `unclear`; if no such span exists, record `not present`.
3. `number_of_works_referenced`: count distinct works only when separable from the text. Multiple volume/page locators within one work count as one work. Use `unknown` when the text does not support a defensible count; do not treat every locator as a separate work.
4. `interpretation_confidence`: use `high`, `medium`, or `low`, based on the visible boundary evidence, not familiarity with a title.
5. `reviewer_notes`: record ambiguity, alternate readings, edition questions, and any external reference consulted. Do not infer the speaker from `group_label` alone.

The annotation columns are intentionally blank in the delivered CSV. `automated_*` fields are machine-generated and must not be copied into human fields.

## Ambiguous cases

Mark a case ambiguous when prose and citation are interleaved; the locator could belong to either text field; more than one work or edition may be present; a newline does not align with a semantic boundary; a work title resembles prose; the prose cue inventory misses the syntax; spelling/formatting changes alter segmentation; or source context is insufficient to identify quotation boundaries. Preserve alternatives in reviewer notes rather than forcing a single interpretation.

## Reviewer agreement and adjudication

Use two Arabic-trained reviewers independently. To reduce anchoring, hide `automated_pattern`, `automated_certainty`, and `source_ID_level_classification` during first-pass annotation, then reveal them only after the human fields are frozen. Compare role labels, boundary offsets, and work counts. Send every disagreement affecting role or boundary to a third reviewer with expertise in hadith/rijāl bibliographic conventions. Retain both initial annotations, the adjudicated result, the rationale, and unresolved dissent in a separate versioned file; do not overwrite this blank template.

Report agreement separately for each field and stratum. Boundary agreement should be measured on span overlap/exactness, not only on categorical labels. Do not resolve disagreement by majority vote when the underlying text supports multiple readings; retain an ambiguous category.

## Dataset evidence, upstream documentation, and hypotheses

### Direct evidence from this dataset

The local input is `narrators.parquet` with columns `id`, `short_name`, `long_name`, `narrator_type`, `biography_text`, and `criticism_text`; its Arrow schema has no key-value metadata. The records' `criticism_text` JSON contains `garh` groups whose observed entries include three elements: two text values followed by an integer. The integer is directly observed as element 3 and is used as `source_id` in the repository's extraction. This confirms storage position and observed association only. The local file does not include a dictionary, foreign-key declaration, or table definition for that integer.

Repository search found earlier prose in `stage2_manual_review.py` asserting entry/page/passage semantics, but those are generated reviewer conclusions, not source metadata. Do not treat them as corroboration. The current v2 semantics note correctly leaves the entity unidentified.

### Upstream and technical documentation search

The official Shamela site was searched for public technical schema/source-ID documentation; no narrator-tuple or `garh` source-ID definition was located. Absence from this search is not proof that private, downloadable, or undocumented schema material does not exist.

The [AuthenticIlm Shamela4 dataset card](https://huggingface.co/datasets/AuthenticIlm/Shamela4_Full_DB) describes its corpus as extracted from Shamela's Lucene/SQLite data and lists a `narrators.parquet` artifact; its published schema examples describe books, pages, and TOC, not the semantics of this `garh` integer. It is a dataset publisher's technical description, not official Shamela documentation.

The third-party [ragaeeb/shamela library](https://github.com/ragaeeb/shamela) documents Shamela v4 master/book database access and mentions narrator export tooling from `S1.db`; the pages inspected do not define the specific `garh` tuple or source-ID foreign key. It is reverse-engineering context, not an upstream authority.

### Hypotheses to keep separate

It is plausible that the integer links an extracted quotation/citation occurrence to some upstream record, because it co-occurs with two text fields in the tuple and repeats in the observed data. It could instead refer to a broader document, source record, or compiler-specific entity. No reviewed evidence establishes which. Do not label it quotation ID, page ID, passage ID, or bibliographic record ID until an upstream DDL/schema or a documented foreign-key join verifies that claim.

## Conclusions this validation can support

If reviewers reliably agree on field roles and boundaries for the sample, the result supports feasibility for those sampled structural strata under the documented protocol. It does not establish error prevalence in all 432 IDs, compiler intent, historical speaker attribution, canonical work/edition identity, source-ID entity semantics, or accuracy of every record. Expand the sample if disagreement clusters by pattern, and obtain the actual upstream schema before defining automated transformations.

## Reproducibility

Run `python dataset_discovery/Shamela4/tuple_validation_v3.py` from the repository root. The manifest records the source and v2-classification hashes, script/test hashes, seed, output hashes, and timestamp. Human annotation should be performed on a copy with a new version identifier.
