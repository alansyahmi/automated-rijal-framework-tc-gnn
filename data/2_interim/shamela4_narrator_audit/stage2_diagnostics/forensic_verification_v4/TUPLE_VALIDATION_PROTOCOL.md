# Shamela4 tuple validation protocol (version 4 - Blinded Review Package)

## Purpose and boundary

This package establishes a **blinded, human-in-the-loop review materials package** for Shamela4 narrator tuple validation. It prepares materials for two Arabic-trained reviewers to annotate independently, with a third senior reviewer available to adjudicate difficult cases.

### Core non-destructive boundaries
- The work prepares review materials; it does **not** fill in expert judgments, contact reviewers, or fabricate human responses.
- The raw source database (`narrators.parquet`) is strictly read-only.
- All v1, v2, and v3 outputs and reports remain unchanged.
- The sample is designed for **tuple interpretation**, not for narrator graph construction, target assignment, source-field modification, or model training.

## Review package structure and blinding design

To eliminate cognitive bias and prevent anchoring against heuristic classifications:

1. **Reviewer CSV (`TUPLE_MANUAL_VALIDATION_REVIEWER.csv`)**:
   - Preserves all necessary contextual fields: `case_id`, `source_id`, `narrator_id`, `narrator_name`, `group_label`, `entry_index`, `original_tuple_json`, `original_field_1`, and `original_field_2`.
   - Leaves all seven human annotation columns blank: `human_field_1_role`, `human_field_2_role`, `quotation_boundary`, `citation_boundary`, `number_of_works_referenced`, `interpretation_confidence`, and `reviewer_notes`.
   - **Blinding**: Completely omits `sampling_stratum`, `automated_pattern`, `automated_certainty`, `automated_evidence`, `source_ID_level_classification`, and `quotation_citation_separability`.
2. **Internal Key File (`TUPLE_VALIDATION_KEY.csv`)**:
   - Stored separately from the reviewer copy.
   - Maps each `case_id` to its `sampling_stratum`, `automated_pattern`, `automated_certainty`, `automated_evidence`, `source_ID_level_classification`, and `quotation_citation_separability`.
   - Kept hidden from reviewers until all human annotations and adjudications are completed and frozen.
3. **Multi-Reviewer Workflow**:
   - Two independent reviewers with training in classical Arabic and Islamic bio-bibliographical literature annotate `TUPLE_MANUAL_VALIDATION_REVIEWER.csv` independently without communication.
   - A third reviewer with domain expertise in hadith/rijāl bibliography serves as adjudicator for cases where Reviewer 1 and Reviewer 2 differ on slot role or boundary offsets.
   - The original v3 CSV (`TUPLE_MANUAL_VALIDATION.csv`) is preserved as the permanent unblinded audit baseline.

## Crucial distinctions in human annotation

Annotators and researchers must maintain strict boundaries between four fundamentally different concepts:

1. **Field-role and boundary judgments vs Speaker attribution**:
   - Annotators determine whether a text slot contains biographical commentary, quotation, or bibliographic locator.
   - The raw `group_label` (e.g., `الطحاوي`, `الدارقطني`, `أحمد بن حنبل`) is a database grouping key, **not** a verified historical speaker attribution.
   - Internal attribution markers (such as «وقال ابن معين» or «روى البخاري») represent internal text citations or compiler commentary; annotators must not assume the group label or internal cue names the sole historical authority without contextual analysis.
2. **Field-role and boundary judgments vs Historical accuracy**:
   - Annotators evaluate syntactic and bibliographic slot boundaries. They do **not** evaluate whether the historical scholar's judgment was accurate, authentic, or accepted in Islamic jurisprudence.
3. **Field-role and boundary judgments vs Narrator reliability**:
   - Annotators do **not** rate or quantify whether the narrator is trustworthy (`thiqah`), weak (`da'if`), or abandoned (`matruk`).
4. **Purposive sample interpretability vs Statistical independence**:
   - The 60 sampled cases are purposively drawn across 6 structural strata to assess boundary interpretability.
   - The sample is **not** an independent, identically distributed ($i.i.d.$) sample. Seven narrators recur, compilers cluster heavily, and tuples co-occur under identical works.
   - Agreement on this sample establishes feasibility of tuple interpretation under the defined strata, **not** corpus-wide error prevalence.

## Sample design and stratum definitions

The validation set was selected with fixed seed `20261111`, exactly `10` tuples from each of six strata (total `60` tuples):

Available unused source IDs at selection time: `{"suffix_format_validation_only": 12, "compound_or_multiple_locator": 420, "mixed_source_ID": 239, "suspected_or_unresolved": 228, "normal_prose_then_citation": 157, "citation_only_then_locator_bearing_prose": 245}`.
Selected counts: `{"suffix_format_validation_only": 10, "compound_or_multiple_locator": 10, "mixed_source_ID": 10, "suspected_or_unresolved": 10, "normal_prose_then_citation": 10, "citation_only_then_locator_bearing_prose": 10}`.

The 6 strata are defined as follows:

1. `suffix_format_validation_only`:
   - 10 cases selected from 12 eligible IDs. All 10 cases feature `(بدون ترقيم)` or unnumbered locator suffixes.
   - Validates human interpretation of unnumbered suffix variants specifically; does not validate general formatting variations.
2. `compound_or_multiple_locator`:
   - Tuples where field 2 contains multiple volume/page locators (`locator_count > 1`) or prose combined with commentary/locators across multiple lines.
3. `mixed_source_ID`:
   - Tuples originating from source IDs that exhibit multiple heterogeneous pattern shapes across their occurrences in `narrators.parquet`.
4. `suspected_or_unresolved`:
   - Tuples where automated cue heuristics yielded weak certainty (`suspected_reversal`, `suspected_non_reversal`) or unrecognised syntactic structures (`unresolved_tuple_structure`).
5. `normal_prose_then_citation`:
   - Canonical structure: field 1 contains recognised evaluation prose cues, while field 2 contains locator(s) without prose cues.
6. `citation_only_then_locator_bearing_prose`:
   - Reversed structure: field 1 contains volume/page locator without prose cues, while field 2 contains prose cues followed by secondary locator text.

## Human annotation guidelines

Annotate directly in the reviewer CSV from the exact preserved text:

1. `human_field_1_role` and `human_field_2_role`:
   - Select one or more of: `quotation/evaluation text`, `bibliographic citation`, `volume/page locator`, `secondary citation`, `commentary/editorial text`, `mixed`, `other`, or `unclear`.
   - Provide rationale in `reviewer_notes` for composite or unclear cases.
2. `quotation_boundary` and `citation_boundary`:
   - Record spans as `field_1:start-end` or `field_2:start-end` using zero-based Unicode code-point offsets with an exclusive end index.
   - Disjoint spans may be semicolon-separated (e.g., `field_2:0-45;field_2:80-120`).
   - If no span exists, record `not present`. If boundaries cannot be determined, record `unclear`.
3. `number_of_works_referenced`:
   - Integer count of distinct literary works referenced in the tuple. Multiple volume/page locators referencing parts of the same work count as 1 work.
   - Use `unknown` if the text does not permit unambiguous enumeration.
4. `interpretation_confidence`:
   - Rate as `high`, `medium`, or `low`, based on visible textual evidence and clarity of delimiters.
5. `reviewer_notes`:
   - Record edition questions, ambiguous syntax, newline misalignments, or external bibliographic reference checks. Do not infer speaker from `group_label` alone.

## Post-annotation evaluation and agreement framework

Once independent annotations and adjudication are completed, evaluate agreement along four explicit dimensions:

1. **Field-Role Agreement**:
   - Compute percentage agreement and Cohen's kappa ($\kappa$) for `human_field_1_role` and `human_field_2_role` between Reviewer 1 and Reviewer 2.
   - Compute Fleiss' kappa if three annotators contribute across all cases.
2. **Quotation and Citation Boundary Agreement**:
   - Assess character-level and token-level span agreement for `quotation_boundary` and `citation_boundary`.
   - Measure Exact Span Match (EM) and span Intersection-over-Union (IoU / Jaccard similarity) on offset ranges.
3. **Automated-Pattern Agreement**:
   - Compare adjudicated human consensus roles against the heuristic classifications in `TUPLE_VALIDATION_KEY.csv`.
   - Measure heuristic precision and recall across regular and reversed patterns.
4. **Stratified Disagreement Analysis**:
   - Disaggregate agreement metrics across the 6 sampling strata.
   - Compare disagreement rates between construction strata (`compound_or_multiple_locator`, `mixed_source_ID`, `suspected_or_unresolved`) and the format stratum (`suffix_format_validation_only`).

> [!NOTE]
> Agreement between annotators is evidence regarding **tuple interpretation only**. It demonstrates that human readers can (or cannot) systematically disambiguate biographical text from citations in this database format; it does not validate historical facts or compiler accuracy.

## Dataset evidence, upstream documentation search, and hypotheses

### Direct evidence from this dataset
The input is `narrators.parquet` with columns `id`, `short_name`, `long_name`, `narrator_type`, `biography_text`, and `criticism_text`. The Arrow schema contains no key-value metadata or relational DDL. The `criticism_text` JSON contains `garh` groups with three-element tuples: two text values followed by an integer. The integer is stored in element 3 and is used as `source_id` in repository extraction. The database file contains no dictionary, foreign key definition, or entity descriptor for this integer.

### Upstream documentation search
1. **Official Shamela Portal**: Search found no published schema, entity-relationship diagram, or technical documentation defining the `garh` tuple structure or the third-element integer.
2. **AuthenticIlm Dataset Card**: Documents the HuggingFace extraction from Shamela Lucene/SQLite files, describing book, page, and table of contents schemas, but provides no relational specification for narrator `garh` integer attributes.
3. **ragaeeb/shamela Repository**: Reverse engineering tool documentation describes extraction of tables from `S1.db` but does not define foreign key targets or entity semantics for the `garh` third element.

### Hypotheses to keep separate
It is plausible that the integer links the occurrence to a specific bibliographic record, compilation passage, or quotation entry. However, no reviewed documentation establishes whether it designates a book ID, page ID, quotation ID, passage ID, or compiler-specific index. The integer must remain identified strictly as `source_id` until official upstream schema or relational joins establish its true entity semantics.

## Reproducibility

Run `python dataset_discovery/Shamela4/tuple_validation_v4.py` from the repository root.
The output directory will contain:
- `TUPLE_MANUAL_VALIDATION_REVIEWER.csv`
- `TUPLE_VALIDATION_KEY.csv`
- `OVERLAP_REPORT.md`
- `TUPLE_VALIDATION_PROTOCOL.md`
- `validation_manifest.json`

The manifest cryptographically records all inputs, outputs, sampling parameters, overlap metrics, and verified hashes of prior audit versions (v1, v2, v3).
