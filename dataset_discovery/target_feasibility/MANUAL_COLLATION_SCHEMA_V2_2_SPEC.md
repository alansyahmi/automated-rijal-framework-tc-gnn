# Manual Collation Schema v2.2 Specification

**Status:** Proposed for approval; implementation pending
**Supersedes:** The applicable design proposals in `MANUAL_COLLATION_SCHEMA_V2_SPEC.md` and `MANUAL_COLLATION_SCHEMA_V2_1_AMENDMENT_AND_MIGRATION_SPEC.md`; both remain unchanged as historical proposals.
**Requirements baseline:** Formal audit dated 2026-11-12 and the subsequent schema-v2.0 review.
**Scope:** Final proposed schema definitions and a deterministic, non-destructive migration specification. No pilot annotations are migrated by this document.

## 1. Decisions incorporated

This specification retains the four-layer architecture and case → candidate entry → statement links, with these refinements:

1. Verbatim source fields contain only transcribed source text or a true null. Their review status is stored in a separate status field.
2. Passage-level naming of an evaluator, historical authenticity of that attribution, and transmission-route traceability are separate questions.
3. Source-work author/compiler and the person responsible for the particular surviving wording are separate roles.
4. `taqrib_statement_validity` asks whether wording is supported in the cited Taqrib passage; authorship and attribution are separate, and `target_task_scope` decides whether the statement enters a defined task. These decisions are statement-level.
5. Candidate-field comparison is against the corresponding assessment span, not the whole entry; statement-to-passage correspondence is a separate comparison.
6. Rank remains a nullable integer 1-12, with a separate status enum.
7. Temporal claims each cite their own evidence and the temporal policy/version used for input decisions is recorded.
8. No ordinal attribution-strength field is used.
9. Task A includes a strict feature-exclusion rule against target leakage from Ibn Hajar's own grade or dependent reproductions.

The target remains Ibn Hajar's narrator-level assessment in *Taqrib al-Tahdhib*, not objective narrator reliability, historical consensus, or a pooled critic score. Rank 1 / Companion status remains distinct from ordinary grade modeling. Task A (reproducing Ibn Hajar's classification) and Task B (analysing historical evaluative evidence) are related but distinct research questions.

## 2. Field-level amendments to v2.0

### 2.1 Verbatim text and missingness

Replace the v2.0 definition of `statement_text_verbatim` with:

| Field | Definition | Allowed representation | Requiredness and invariant |
|---|---|---|---|
| `statement_text_verbatim` | Exact Arabic statement text from the cited source; no English gloss, status code, or reviewer interpretation. | Actual transcription or null. | Required field. If `statement_text_status=transcribed`, value must be non-empty. For all other statuses, value must be null. |
| `statement_text_status` | State of transcription for this statement. | `transcribed`, `not_transcribed`, `unavailable`, `unresolved`, `not_assessed`. | Required. A missing statement text must never be represented by a literal string such as `not_transcribed`. |

Apply the same pattern to other verbatim/evidence fields. For example, `attribution_evidence_verbatim` and `identity_evidence_verbatim` contain source wording only or null. Each links to an evidence record with a separate status; status strings never occupy verbatim columns. Enum fields may contain status values; source-text fields may not.

Common `evidence_text_status` values: `transcribed`, `not_found_after_review`, `unavailable`, `unresolved`, `not_assessed`, `not_applicable`. When `transcribed`, the linked verbatim value must be non-empty; with every other status it must be null. `not_found_after_review` means the reviewer examined the stated scope and did not locate evidence; it is not interchangeable with `not_assessed`.

Common meanings:

- **Null + `not_assessed`:** the reviewer has not examined the field.
- **Null + `unavailable`:** the relevant source/evidence was unavailable.
- **Null + `unresolved`:** examination occurred but the evidence remains ambiguous or conflicting.
- **Null + `not_applicable`:** the field does not apply; use this status only where the field's own status enum permits it.
- **Non-empty text + `transcribed`:** exact source wording has been transcribed.
- **Unknown:** use only for a factual value that cannot be established, not as a substitute for a missing-text status.

Do not change the legacy v1 values in place. For example, the English parenthetical in PROV-10 remains in the immutable v1 annotation. A future reviewer may transcribe the Arabic phrase into a corrected derivative and separately record its interpretation.

### 2.2 Three distinct attribution questions

The following statuses must not be conflated:

| Question / field | Definition | Allowed values | What it establishes |
|---|---|---|---|
| `passage_evaluator_naming_status` | What the consulted passage says about the evaluator. | `explicit_individual_named`, `collective_only`, `no_evaluator_named`, `unclear`, `not_assessed`, `not_applicable`. | Textual fact about wording in the cited passage only. |
| `historical_evaluator_attribution_status` | Whether historical evidence supports attributing the judgment to that evaluator. | `supported_by_verified_source_or_route`, `explicitly_reported_but_historically_unverified`, `contradicted`, `unresolved`, `not_assessed`, `not_applicable`. | Historical attribution conclusion, based on inspected provenance evidence. |
| `transmission_route_status` | Whether the path by which the judgment reached the consulted wording is documented. | `documented_traceable`, `named_authority_route_unverified`, `route_examined_not_found`, `unresolved`, `not_assessed`, `not_applicable`. | Route conclusion only. A named authority alone is not a traceable route. |

For PROV-24, the passage may be recorded as explicitly naming al-Nasa'i even while historical attribution is `explicitly_reported_but_historically_unverified` and route status is `named_authority_route_unverified`. This records what is visible in Taqrib without certifying the underlying historical transmission.

Retain separate identity/role fields:

| Field | Definition | Allowed values / status handling |
|---|---|---|
| `named_historical_evaluator` | Historical critic whose judgment is named or claimed. | Canonical name plus original spelling when named; pair with `evaluator_value_status`: `identified`, `collective_unidentified`, `none_named`, `unknown`, `not_assessed`, `not_applicable`. |
| `intermediary_transmitter` | Person/source transmitting the judgment between evaluator and consulted wording, if evidenced. | Name/source or null; pair with `transmitter_value_status`: `identified`, `none_identified`, `unknown`, `not_assessed`, `not_applicable`. |
| `surviving_wording_author` | Person responsible for the particular formulation in the consulted passage. This is a passage-level role, not automatically copied from work metadata. | Name or null; pair with `wording_author_value_status`: `identified`, `unknown`, `not_assessed`, `not_applicable`. |
| `source_work_author_compiler` | Author/compiler assigned to the source work as a whole by the source metadata. | Source metadata value or null with `source_author_metadata_status`: `recorded`, `unknown`, `not_assessed`, `not_applicable`. |
| `compiler_authorship_status` | Whether the surviving wording is supported as the work/passage author's formulation. | `supported`, `contradicted`, `unresolved`, `not_assessed`, `not_applicable`. |

The source work author/compiler and the surviving wording author may be the same person, but the migration or annotator must not assume that they are identical for every passage. The named historical evaluator can be different from both.

`attribution_evidence_verbatim` is an exact quote or excerpt, not an evidence-strength label. Pair it with `attribution_evidence_text_status` and an evidence/source locator. A passage may explicitly name an evaluator while historical attribution remains unverified.

Remove `attribution_evidence_strength` from v2.0. Store direct evidence, locators, passage naming, historical attribution outcome, and route status instead. No overall ordinal score is proposed.

### 2.3 Taqrib statement validity versus target task scope

Use `taqrib_statement_validity` to answer only: **Is this wording supported in the cited *Taqrib* passage?** It does not determine who authored the judgment. Use `target_task_scope` to answer: **Can this statement enter the specifically defined prediction task?** Apply both at statement level.

| Field | Allowed values | Rules |
|---|---|---|
| `taqrib_statement_validity` | `supported_taqrib_statement`, `not_supported_in_taqrib`, `unresolved`, `not_assessed`. | Answers whether the specified wording is supported in the consulted Taqrib passage/span only. It does not imply Ibn Hajar authored the judgment, identity is resolved, or it is target-eligible. |
| `target_task_scope` | `ordinary_grade_candidate`, `status_only_candidate`, `not_in_defined_task`, `unresolved`, `not_assessed`. | Must name the applicable task/version in the analysis manifest. Rank 1 is never `ordinary_grade_candidate`. A separate status task is not assumed to exist. |

Taqrib statement validity, evaluator/compiler attribution, identity, and task scope are independent. PROV-24 may be supported as wording in Taqrib while attributing its judgment to al-Nasa'i rather than establishing an Ibn Hajar synthesis. PROV-01 may be a supported Taqrib status statement while remaining outside ordinary grade modeling. Task A's input firewall must be specified in its task manifest.

### 2.4 Correspondence comparisons

Replace the single ambiguous `source_text_correspondence` with two fields:

| Field | Comparison | Allowed values |
|---|---|---|
| `candidate_field_source_correspondence` | Original dataset grade field/value versus the corresponding grade/assessment span in the cited *Taqrib* entry. Do not compare a short grade string to the full biographical entry. | `exact`, `minor_variation`, `partial_or_truncated`, `substantial_difference`, `not_found`, `unresolved`, `not_assessed`. |
| `statement_source_correspondence` | One segmented statement row versus its specific cited passage span. | `exact`, `minor_variation`, `substantial_difference`, `not_found`, `unresolved`, `not_assessed`. |

The candidate-field comparison also requires:

| Field | Definition and rule |
|---|---|
| `candidate_comparison_source_span` | Exact Arabic assessment span selected from the cited entry, or null. It is source text, never a status string. |
| `candidate_comparison_source_span_status` | `transcribed`, `not_found_after_review`, `unavailable`, `unresolved`, `not_assessed`. Non-empty span iff `transcribed`; otherwise null. |
| `candidate_comparison_rationale` | Reviewer explanation for selecting the span and assigning correspondence. Required for every assessed comparison. |
| `candidate_comparison_locator` | Precise page/entry/passage locator for the span. Required for every assessed comparison. |

The locator identifies the span within the full entry; retain the full entry for identity and context. `statement_source_correspondence` compares a transcribed statement with its own passage span. A correct statement transcription does not erase a discrepancy in the original field, and the original-field comparison does not substitute for statement-level comparison.

Keep `identity_match_status` as an independent reviewer decision. Do not restore the old omnibus `textual_fidelity`, `attribution_fidelity`, or `identity_fidelity` scores.

### 2.5 Rank and edition status

- `taqrib_rank_number`: nullable integer, constrained to 1-12 only.
- `rank_status`: `assigned`, `unranked`, `not_applicable`, `not_assessed`, `unresolved`, `not_found`.
- Invariant: `rank_status=assigned` if and only if the integer is present. Every other status requires null.
- `edition_variant_status` remains separate from source-text correspondence. Preserve `variant_marked_in_edition_metadata` independently from `editorial_insertion_verified`; square brackets alone do not establish a modern editorial insertion.

### 2.6 Temporal provenance and policy

Keep evaluator lifespan/death, judgment date, source-work composition date, surviving witness date, and modern edition publication date as separate date claims. For each date claim, record a separate evidence reference: source ID/locator, evidence transcription status, and any exact quotation. A compact linked evidence table can hold `evidence_record_id`, source/witness ID, locator, `evidence_text_verbatim`, `evidence_text_status`, and evidence role. One evidence item may support multiple dates only when each date-to-evidence relationship is recorded separately. Do not use one shared text field as evidence for multiple dates without those links.

Each date claim has its own `date_claim_status`: `recorded_in_source`, `unknown`, `unresolved`, `not_assessed`, or `not_applicable`. An asserted date/range carries calendar, precision, and a link to its own evidence record; a non-asserted date has a null date value with its status. Never infer one date from a different date field.

Add to every historical-input decision:

| Field | Definition | Allowed values / rule |
|---|---|---|
| `temporal_policy_id` | Identifier for the explicit temporal inclusion rule used. | Required for an assessed input decision; e.g. a named provisional `T_le_365_AH` rule. |
| `temporal_policy_version` | Version/date/commit of the policy specification. | Required with `temporal_policy_id`; must identify a frozen rule document or policy manifest. |
| `temporal_policy_result` | Application result for this statement. | `passes_policy`, `fails_policy`, `cannot_assess`, `not_applicable`. |

The current `T <= 365 AH` boundary remains provisional. A cutoff pass does not establish attribution authenticity or route traceability. Do not infer the judgment date from an evaluator's death date or a witness date from work composition/publication.

### 2.7 Original-field preservation and Task A leakage rule

Preserve `candidate_grade_field`, `candidate_grade_verbatim`, and `candidate_grade_source_location` exactly as supplied by the source dataset, including its original field name, representation, punctuation, and any encoding/serialization needed to reconstruct the original value. Never replace these with normalized values.

Task A must carry a versioned `feature_exclusion_policy_id`. Exclude from model inputs:

- The original candidate grade field/value and all direct encodings of it.
- Taqrib grade, qualification, rank, target eligibility, or any label/derived feature computed from the target.
- Post-target or later-source text that simply reproduces Ibn Hajar's assessed wording as if it were independent early evidence.
- Any duplicate or transformed feature that leaks the target through a linked table, identifier, summary, or preprocessing artifact.

For each proposed feature source, record its source/statement link, temporal provenance, inclusion status (`included`, `excluded`, `quarantined`, `not_assessed`), and reason. Feature inclusion is a Task A design decision; source collation alone does not authorize a feature.

## 3. Consolidated field inventory for v2.2

This inventory supersedes conflicting v2.0 field definitions; it is not a request to build all fields as columns in one flat CSV.

| Logical table | Required identifiers/fields | Conditional fields and explicit status fields |
|---|---|---|
| Cases | `audit_record_id`, dataset name, dataset narrator ID/name, exact original field name/value/location | Original-value presence/serialization status if unavailable in source |
| Candidate entries | `candidate_entry_id`, `audit_record_id`, exact entry transcription/status, entry/page locator, `identity_match_status` | Identity evidence and evidence locator; candidate-field source correspondence, assessment source span, comparison rationale, and locator |
| Statements | `statement_id`, `candidate_entry_id`, statement type, statement text/status, Taqrib statement validity, target task scope | Grade base/qualification verbatim and status; numeric rank/rank status; statement-to-passage correspondence and rationale |
| Attribution links | `attribution_link_id`, `statement_id`, passage naming status, attribution form, historical attribution status, route status | Named evaluator, intermediary transmitter, surviving wording author, their separate value statuses, exact evidence/status/locator; compiler authorship status |
| Sources | `source_record_id`, work identifier/title where available, consulted edition/witness type, source locator, source verification status | Work author/compiler and metadata status; each date claim with value/status/evidence reference; variant status |
| Research use | `statement_id`, historical-input eligibility, target eligibility/task scope, corroboration status | Temporal policy ID/version/result; decision rationale; feature inclusion status/policy for Task A |

All enum fields use the values defined in this amendment. Exact source-text and evidence fields contain text or null, never enum/missingness strings.

## 4. Deterministic migration specification (design only)

### 4.1 Inputs and immutable baseline

The future migration has two **content inputs** and two **read-only provenance inputs**. Only the content inputs supply annotation/source values. The provenance inputs are used to verify recorded hashes and package history; they must never fill or infer annotations. The script must read:

**Content inputs**

1. `dataset_discovery/target_feasibility/manual_collation_pilot_10/MANUAL_COLLATION_PILOT_10.csv` - frozen, blank review packet.
2. `dataset_discovery/target_feasibility/manual_collation_pilot_10/MANUAL_COLLATION_PILOT_10_WORKING.csv` - current single-reviewer annotation record.

**Read-only provenance inputs**

3. `dataset_discovery/target_feasibility/manual_collation_pilot_10/MANUAL_COLLATION_PILOT_10_KEY.csv` - provenance/mapping audit only; not a source for annotation decisions.
4. `dataset_discovery/target_feasibility/manual_collation_pilot_10/MANUAL_COLLATION_PILOT_10_MANIFEST.json` - verify package history and recorded hashes only; not a source for annotation decisions.

Expected SHA-256 values for all four migration inputs at this audit baseline:

| Input | SHA-256 |
|---|---|
| Frozen packet | `78cb15eb72b04c1b2c0d2e350e375615236df22a2918c38256977ccccffae958` |
| Working annotations | `4b3f731b5a799c1df499c57391f4b502fcee84f129c2bae2e77325e738a04548` |
| Key (read-only provenance) | `9eccd4533cb4482390a41861955e3636453d1f0bc39e8aac544f748f4dcc0684` |
| Manifest (read-only provenance) | `9339ad77f1fa18e204b443e9a3ec888d6ec56924b801b85d94f3bb8ea49bf72d` |

The script must stop with a clear error if any of the four expected hashes differs unless an explicitly reviewed migration run supplies new expected hashes and documents why. It must not write to any input or to v1 outputs.

### 4.2 Preflight and join

Before producing any output, the script must:

1. Read both CSVs as UTF-8 with BOM handling and preserve all original cell strings.
2. Check exact expected headers/order and row counts: 11 source-entry rows, 10 distinct `audit_record_id` values.
3. Confirm the generator's pre-populated fields and original dataset context match row-for-row. The audit baseline found those pre-populated/context fields identical. Do **not** require the human-review columns to match: entry number, printed page, entry-name/grade/qualification transcription, identity/text match, attribution, fidelity, disposition, and eligibility fields are blank in the frozen template by design and populated in the working annotation record.
4. Confirm the two PROV-04 rows remain distinct by their full entry text/locator despite sharing one `audit_record_id`.
5. Derive `within_case_candidate_index` from the validated frozen packet order (1-based within `audit_record_id`) and require the expected order in the working file. Row order is a validation constraint, not a key by itself.
6. Require an exact one-to-one composite match: `audit_record_id + within_case_candidate_index + taqrib_entry_text_verbatim + canonical_source_locator_key`. Derive the frozen-side locator key mechanically from `taqrib_book_id`, `taqrib_printed_page_from_corpus`, and the entry number at the beginning of `taqrib_entry_text_verbatim`. Parse the working `source_locator` into the same book/page/entry tuple and require an exact tuple match. Preserve the working locator string unchanged as `source_locator_verbatim`; store the structured tuple as `canonical_source_locator_key`. Numeral normalization is permitted only to build this join key, not to alter any original field.
7. Reject missing, duplicated, or ambiguous composite keys and any difference in key components. Never choose the first match or use grade wording to break a tie. Use row order only to validate `within_case_candidate_index`, not as a substitute for the composite key.
8. Verify the key and manifest hashes against the provenance inputs and their recorded values, but do not use either file to infer or fill human decisions.

No case, candidate identity, statement segmentation, attribution, route, rank, or eligibility decision is inferred solely to make a join succeed. If the entry number cannot be mechanically parsed or the constructed locator does not match the working locator, stop for manual investigation; do not produce a partial derivative.

### 4.3 Outputs and deterministic identifiers

Write outputs only under a new directory, for example:

`data/2_interim/shamela4_narrator_audit/manual_annotation_working/manual_collation_pilot_10_v2_2/`

This path is a proposal; implementation must first check repository conventions and avoid overwriting any existing directory. Output names should identify schema version and be declared in a manifest.

Deterministic record identifiers:

- Keep existing `audit_record_id` unchanged.
- Create `candidate_entry_id` from the case ID and stable within-case row index based on the validated frozen input order, e.g. `PROV-04-C01`, `PROV-04-C02`. Include the full-entry text hash in the migration mapping so row identity is independently auditable.
- Create a provisional statement work item per candidate with `statement_id` ending `-S00`, `statement_text_status=not_transcribed`, null `statement_text_verbatim`, `statement_type=not_assessed`, and other reviewer-only fields set to `not_assessed` or `not_applicable` according to their documented conditional rules. This placeholder is not a scholarly statement and must be replaced by reviewed statement rows before analytical use.
- The migration script must not split PROV-10 or any other source entry automatically. It may create the provisional work item only; the reviewer decides segmentation.

### 4.4 What is copied, mapped, and left for review

**Copy unchanged:** case IDs; dataset identity/context; original candidate field name/value/source path; complete candidate-entry text; source locators/pages; current reviewer notes; and every original v1 annotation value. Preserve them in a linked immutable `legacy_v1_values` snapshot or equivalent migration audit file.

**Map mechanically only where semantics are identical:** stable case link; candidate-entry link; source record/link identifiers; verbatim source text already present in a source-text column; and exact locator strings. Record every source column-to-v2.2-field mapping in the manifest.

**Do not silently map or “repair”:** `assessment_author`, `assessment_attribution_status`, `compiler_or_transmitter`, `editorial_material_status`, old fidelity scores, disposition/eligibility values, text in a verbatim field containing an interpretation, rank strings, or any field whose v1 and v2.2 meanings differ. Copy the old value only into the legacy snapshot. Set the new decision field to `not_assessed` pending human reconciliation. Do not convert al-Nasai spelling, PROV-02 bracket status, PROV-24 route, PROV-51 statement type, or PROV-10 phrase segmentation without review.

For rank migration, preserve the exact old value in `legacy_v1_values`. A strict 1-12 integer may additionally be copied to `legacy_rank_candidate` for reviewer convenience, but never into the new assessed rank field. Initialize `taqrib_rank_number=null` and `rank_status=not_assessed` for every candidate. A reviewer assigns the new rank only after re-review under approved v2.2 definitions. Do not infer rank status from a blank, `none`, or other legacy value.

### 4.5 Manifest and reproducibility

The derivative manifest must include:

- Schema name/version and status (proposed/approved/implemented).
- Exact input paths, hashes, byte sizes, row counts, and encoding.
- Script path/version and runtime version once implementation occurs.
- Output file paths, hashes, byte sizes, and row counts.
- Input-row to case/candidate/statement mapping, including the PROV-04 two-candidate link.
- Column-level mapping: copied, mechanically transformed, legacy-only, or deferred for review.
- Counts of missingness/status values; no count may treat null or `not_assessed` as a positive decision.
- Temporal policy ID/version where a temporal eligibility decision is later made.
- Explicit statement that no annotations were inferred during mechanical migration.

Determinism requirement: with identical input bytes, schema version, configuration, and script version, the migration must produce byte-identical CSV outputs and equivalent manifest content apart from an explicitly separated generation timestamp. Prefer a fixed CSV dialect, UTF-8 encoding, stable row order, and sorted JSON keys.

### 4.6 Atomic output and rollback protection

The migration implementation must fail closed and publish outputs atomically:

1. Complete all input/hash/schema/key validation before writing any output.
2. Refuse to proceed if the final output directory already exists. Never merge, overwrite, or delete it.
3. Write all outputs to a uniquely named temporary staging directory on the same filesystem/volume as the final destination.
4. Validate the staged CSV schemas, row links, status invariants, hashes, and manifest before publication.
5. Publish only by an atomic same-volume directory rename into the absent final path. If the filesystem cannot provide that operation, stop without publishing; do not fall back to copying files into the destination.
6. On any failure, remove only the migration-created staging directory and lock/reservation artifacts. Leave both source CSVs, read-only provenance inputs, and all pre-existing repository files untouched.
7. Use an exclusive run lock or equivalent no-clobber reservation so concurrent runs cannot race to publish the same destination.

## 5. Validation tests required before implementation is accepted

Tests must target the produced v2.2 derivative and migration script, not only the original 60-row worksheet:

1. Hashes and byte sizes for both content CSVs and both read-only provenance inputs, headers, row counts, unique case count, and row-level join integrity.
2. Frozen and working source/context cells match; originals and v1 outputs remain byte-for-byte unchanged after migration.
3. All verbatim fields obey text/status invariants: transcribed iff non-empty; all non-transcribed statuses have null text.
4. Arabic, punctuation, quotes, BOM, and embedded newlines round-trip exactly.
5. Source-work author/compiler, surviving wording author, intermediary transmitter, and historical evaluator remain separate values/relationships.
6. Passage naming (`explicit_individual_named`) does not automatically yield verified historical attribution or `documented_traceable` route. Include PROV-24 as a regression case.
7. PROV-51 can be represented as collective attribution and specific transmission criticism without forced grade/rank.
8. PROV-02 variant metadata does not become a verified editorial insertion without evidence.
9. PROV-10's English gloss cannot enter `statement_text_verbatim`; segmentation is not automated.
10. `taqrib_statement_validity` is statement-level textual support and independent from authorship, identity, and `target_task_scope`; PROV-01 may be a supported Taqrib statement with status-only scope, not an ordinary grade target.
11. Numeric rank/null and `rank_status` constraints are enforced; Rank 1 cannot enter ordinary grade distributions. Legacy ranks are preserved as legacy values/candidates only; all new rank fields initialize to null/`not_assessed` until re-review.
12. `candidate_field_source_correspondence` compares against the cited grade/assessment span with required span/status/rationale/locator; `statement_source_correspondence` compares each segmented statement against its passage. They cannot substitute for each other.
13. Every date claim links to its own evidence; date-role values are not inferred from another date field.
14. Historical-input decisions record a temporal policy ID/version and do not pass solely because evaluator death date is before cutoff.
15. Task A feature audit excludes Taqrib grade/rank, original candidate grade, direct encodings, and later reproductions of the target as independent inputs.
16. **PROV-04 rejected candidate test:** rejected candidate is absent from both target distributions and model-input extracts; accepted candidate remains attached to the same case; two candidate rows never count as two narrators.
17. Running migration twice from identical inputs/configuration produces byte-identical outputs; a mismatch in any of the four input hashes or an ambiguous composite join stops without partial output.
18. Atomic-publication test: injected validation failure leaves no final directory and no partial files; an existing destination is never overwritten; successful publication is a same-volume atomic rename.

## 6. Outstanding review decisions

The following need approval or scholarly review; the schema does not answer them:

- Whether the text in PROV-24 can be historically traced to al-Nasa'i, beyond the passage explicitly naming him.
- Whether PROV-51's collective criticism can be traced to identifiable critics or sources.
- Whether and how PROV-10 should be segmented into grade and biographical statement records.
- Whether the Awwamah brackets in PROV-02 should receive any interpretive note beyond the edition's stated variant convention.
- Whether PROV-04's accepted identity determination is supported by sufficient independent biographical evidence.
- Whether Task A is limited to ordinary grades or includes a separately approved status task.
- Whether `T <= 365 AH` remains the input boundary and what explicit policy version governs it.
- What source feature set Task A permits after target leakage review.

The pilot remains single-reviewer. No claim of independent Arabic annotation, inter-reviewer agreement, historical consensus, objective reliability, corpus-wide validity, or model readiness follows from this specification.

## 7. Implementation gate

**Architecture:** approved in principle.
**Schema v2.2:** proposed by this specification, pending review.
**Migration:** specified, not implemented.
**Annotation:** unchanged; re-review is required after schema approval.
**Modeling:** out of scope.

Implementation may begin only after approval of the v2.2 definitions, missingness rules, candidate/statement mapping convention, temporal policy version, and Task A leakage policy. The migration must then produce a new hash-linked derivative, validate it, and present the ten records for human re-review under the approved definitions.
