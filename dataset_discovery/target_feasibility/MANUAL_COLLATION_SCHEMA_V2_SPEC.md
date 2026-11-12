# Manual Collation Schema v2.0 (Proposal)

**Status:** Proposed for review; not implemented
**Scope:** Design specification for a corrected derivative of the ten-case manual source-collation pilot.
**Baseline:** `MANUAL_COLLATION_PILOT_10_FORMAL_AUDIT.md` (2026-11-12) and the current pilot/codebook.
**Change boundary:** This document does not alter the frozen packet, working annotations, codebook, generator, tests, source data, or Git history.

## 1. Research boundary

The candidate target is **Ibn Hajar's narrator-level assessment in *Taqrib al-Tahdhib***. It is a source-specific scholarly classification, not objective narrator reliability, historical consensus, or a pooled critic score. The twelve ranks remain Ibn Hajar's source-specific taxonomy. Rank 1 / Companion status is retained as descriptive status and is not treated as an ordinary evaluative grade.

Keep two research questions separate:

- **Task A: reproducing Ibn Hajar's classification.** Any future prediction target is Ibn Hajar's classification. Inputs must not include Ibn Hajar's own assessment or later reproductions of it in a way that makes prediction circular.
- **Task B: analysing historical evaluative evidence.** Identify statement type, evaluator, transmission, source, and temporal provenance. A later compiler's report of an earlier critic is not automatically a traceable or eligible historical input.

The pilot schema supports source audit and feasibility. It does not decide whether both tasks become model objectives or establish construct validity.

## 2. Design principles

1. Keep four logical layers distinct: identity, statement, attribution/source, and research use.
2. Represent **case → candidate entry → statement** explicitly. A case may have multiple candidate entries; an entry may contain multiple statements.
3. Store the historical evaluator, intermediary transmitter, and author/compiler of the consulted wording as distinct roles. A role may be unknown or inapplicable.
4. Do not turn every field into a mandatory human interpretation. Record source facts from metadata or cited sources; record interpretations only where review is required.
5. Do not use an ordinal `attribution_evidence_strength` field in v2.0. Preserve the evidence itself, its locator, route status, and separate attribution outcomes. Reconsider a summary score only if a later study demonstrates a need and supplies a reproducible rubric.
6. Keep target eligibility independent from historical-input eligibility.
7. Keep originals byte-for-byte unchanged. A v2.0 derivative is a new, hash-linked artifact.

### Evidence versus interpretation

**Source/structural facts** include source work identifiers and titles, entry/page locators, exact transcribed Arabic, edition metadata, and dates as stated in a cited metadata source. Store the citation or metadata path that supports each fact. A fact may still be unknown or unverified.

**Reviewer interpretations** include statement type, identity match, who formulated a judgment, whether a historical attribution is supported, whether a route is traceable, source-text correspondence, and research-use eligibility. These require a reviewer decision and a recorded rationale/evidence. Do not make them look like directly observed metadata.

## 3. Record structure

This is a logical schema, not a requirement to build a database. A small set of linked CSV sheets is sufficient:

1. **Cases:** one row per source-dataset narrator record.
2. **Candidate entries:** one row per candidate *Taqrib* entry for that case. PROV-04 therefore has two linked candidate rows.
3. **Statements:** one row per distinct statement within a candidate entry. PROV-10 may need separate grade and biographical-statement rows after reviewer confirmation.
4. **Sources and attribution links:** one row per source/attribution relationship when multiple authorities, transmitters, works, or witnesses are involved. These can be combined in a compact sheet for this pilot if relationships remain explicit.

Recommended stable keys: `audit_record_id`, `candidate_entry_id`, `statement_id`, `source_record_id`, and `attribution_link_id`. IDs identify records; they do not imply scholarly conclusions.

## 4. Field specification

All derivative rows must encode missingness explicitly. `not_assessed` means review has not been done; `unknown` means the fact could not be established; `unresolved` means evidence remains ambiguous or conflicting; `not_applicable` means the concept does not apply to that record. Empty cells are prohibited in required v2.0 fields. Preserve legacy blanks only in the immutable input copy.

### 4.1 Case and identity layer

| Field | Type and definition | Allowed values / missingness | Required? | Eligibility effect |
|---|---|---|---|---|
| `audit_record_id` | Stable ID of the source-dataset case; retain current ID. | Existing case ID. | Yes. | None by itself. |
| `candidate_entry_id` | Unique candidate *Taqrib* entry under a case. | Stable unique ID, e.g. `PROV-04-A`. | Yes. | Enables accepted/rejected candidate filtering. |
| `dataset_name`, `dataset_narrator_id`, `dataset_narrator_name` | Original dataset identity/context values. | Preserve source values verbatim; do not normalize in place. | Yes when present in source. | None by themselves. |
| `candidate_grade_field`, `candidate_grade_verbatim`, `candidate_grade_source_location` | Original extracted field, exact source value, and source path. | Preserve byte/text content from input; null only if absent in source, with absence recorded. | Yes for source cases. | None; never use grade to resolve identity. |
| `identity_match_status` | Reviewer decision whether the dataset narrator and candidate entry identify the same person. | `confirmed`, `probable`, `unresolved`, `mismatch`, `not_found`, `not_assessed`. | Yes per candidate. | `mismatch` excludes target and input; `unresolved` prevents target inclusion pending review. |
| `identity_evidence` | Independent biographical identifiers and their locators. | Text or structured list; `not_assessed` / `insufficient_evidence` where appropriate. | Required for a positive or mismatch decision; otherwise status explicit. | Supports identity decision; does not itself confer eligibility. |

Identity evidence may include lineage, kunya, nisbah, geography, teachers/students, tabaqah, dates, and other biography. The target grade under evaluation is prohibited as identity evidence.

### 4.2 Statement layer

| Field | Type and definition | Allowed values / missingness | Required? | Eligibility effect |
|---|---|---|---|---|
| `statement_id` | Stable ID for one distinct statement within an entry. | Unique ID, e.g. `PROV-10-A-S1`. | Yes per statement row. | Enables statement-level decisions. |
| `statement_text_verbatim` | Exact Arabic text for the statement as found in the consulted source. Keep interpretation outside this field. | UTF-8 text; exact transcription or `not_transcribed` pending review. | Yes; no translated glosses in the verbatim string. | Source evidence only. |
| `statement_type` | Reviewer classification of what the statement does. | `standardized_narrator_grade`, `qualified_narrator_grade`, `attributed_earlier_critic_judgment`, `descriptive_or_generational_status`, `specific_transmission_criticism`, `biographical_or_factual_statement`, `mixed_or_unclear`, `not_assessed`. | Yes per statement row. | Helps determine use; eligibility remains a separate decision. |
| `grade_base_verbatim` | Exact base-grade wording where a grade exists. | Arabic source text; `not_applicable`, `not_assessed`, or `unresolved`. | Conditional: required for standardized/qualified grades. | Can form target content only when attribution, identity, and source support it. |
| `grade_qualification_verbatim` | Exact qualifying phrase attached to a grade. Keep commentary out. | Arabic source text; `not_applicable`, `not_assessed`, or `unresolved`. | Conditional: required when a qualification exists; otherwise explicit N/A. | Must remain attached to the target interpretation. |
| `taqrib_rank_number` | Numeric value for Ibn Hajar's twelve-rank scheme. | Nullable integer `1` through `12` only. | Conditional; null if not assigned. | Rank 1 is a status designation, excluded from ordinary grade modeling. |
| `rank_status` | Explains the nullable rank. | `assigned`, `unranked`, `not_applicable`, `not_assessed`, `unresolved`, `not_found`. | Yes. `assigned` requires integer 1-12; every other status requires null rank. | Prevents status codes being treated as rank numbers. |

Do not force several clauses into a single grade field. If a clause cannot yet be segmented or classified, retain the exact full text and use `mixed_or_unclear`; do not silently split it.

### 4.3 Attribution, source, and temporal layer

#### Attribution relationship fields

| Field | Type and definition | Allowed values / missingness | Required? | Eligibility effect |
|---|---|---|---|---|
| `named_historical_evaluator` | Historical critic explicitly named as the evaluator, not necessarily the speaker/compiler of the extant wording. | Canonical name plus source spelling; status field distinguishes `named`, `collective_unidentified`, `none_named`, `unknown`, `not_assessed`, `not_applicable`. | Status required; name conditional. | A name alone does not establish a traceable route or historical-input eligibility. |
| `intermediary_transmitter` | Person/source transmitting the evaluator's judgment between evaluator and consulted wording, if identifiable. | Canonical name/source; status: `identified`, `none_identified`, `unknown`, `not_assessed`, `not_applicable`. | Status required; value conditional. | Route evidence may support input eligibility but is not sufficient alone. |
| `surviving_wording_author` | Author/compiler responsible for the wording in the source actually consulted. | Canonical person/work attribution; status: `identified`, `unknown`, `not_assessed`, `not_applicable`. | Status required; value conditional. | Supports source authorship, distinct from evaluator identity. |
| `attribution_form` | How the consulted text presents the judgment. | `direct_quotation`, `explicit_attribution`, `collective_attribution`, `compiler_synthesis`, `unclear`, `not_applicable`, `not_assessed`. | Yes. | Descriptive only; does not automatically determine input eligibility. |
| `transmission_route_status` | Whether a route from the historical evaluator to the consulted witness is documented. | `documented_traceable`, `named_authority_route_unverified`, `route_examined_not_found`, `unresolved`, `not_assessed`, `not_applicable`. | Yes when historical attribution is relevant; otherwise N/A. | `documented_traceable` requires cited source/route evidence; a named evaluator by itself is not enough. |
| `compiler_authorship_status` | Whether the surviving wording is supported as authored/compiled by the named surviving-wording author. | `supported`, `contradicted`, `unresolved`, `not_assessed`, `not_applicable`. | Yes when a wording author is claimed. | Source/authorship evidence; not the same as evaluator attribution. |
| `historical_evaluator_attribution_status` | Whether evidence supports the judgment's attribution to the named evaluator. | `supported_in_cited_passage`, `supported_by_verified_route`, `contradicted`, `unresolved`, `not_assessed`, `not_applicable`. | Yes when an evaluator is named or implied. | Supports input review; does not itself establish temporal eligibility. |
| `attribution_evidence_verbatim` | Exact passage/formula supporting the attribution relationship. | Verbatim source excerpt; `not_found`, `not_assessed`, or N/A as applicable. | Required when status is supported/contradicted. | Evidence only. |

There is **no `attribution_evidence_strength` score in v2.0**. Record what was observed and its locator. If evidence strength is later needed, define and validate a separate rubric before collecting it.

#### Linked source and temporal metadata

Store source metadata once per source/work/witness and link it to statements. Do not duplicate dates into every statement when a stable source link suffices.

| Field | Type and definition | Allowed values / missingness | Required? | Eligibility effect |
|---|---|---|---|---|
| `source_record_id` | Stable key for a consulted source/edition/witness record. | Unique ID. | Yes for every cited source link. | Enables provenance joins. |
| `source_work_id`, `source_work_title` | Repository/upstream ID and title of the work consulted. | Preserve identifier/title from source metadata; `unknown` if absent. | Required when source is identified. | None alone. |
| `source_work_author_compiler` | Author/compiler of the source work, as source metadata reports it. | Name or `unknown` / `not_assessed`. | Required when available; cite metadata. | Must not be confused with historical evaluator. |
| `source_work_composition_date` | Work composition/compilation date or range, with calendar/precision stated. | Date/range or `unknown`, `unresolved`, `not_assessed`. | Required field; explicit status if unknown. | Relevant to temporal firewall; not a witness date. |
| `surviving_witness_id`, `surviving_witness_date` | The manuscript/digital text witness actually consulted and its date, if established. | ID/date or `unknown`, `unresolved`, `not_assessed`, `not_applicable` for a non-witness metadata record. | Required status; never infer date from work composition. | Relevant to source provenance; not an evaluator date. |
| `source_locator` | Page, volume, entry, or stable passage locator in the cited source. | Exact locator or `not_found` / `not_assessed`. | Required for claims marked verified. | Supports verification. |
| `edition_editor`, `edition_publisher`, `edition_publication_date` | Modern edition consulted and publication metadata. | Bibliographic values as printed/metadata; `unknown` / `not_assessed` where absent. | Required when a modern edition is the consulted source. | Distinguishes modern edition from historical witness. |
| `historical_evaluator_lifespan_or_death` | Evaluator lifespan/death date with source locator. | Date/range or `unknown`, `unresolved`, `not_assessed`, `not_applicable`. | Conditional on named evaluator. | Temporal policy evidence; does not date a specific utterance. |
| `approximate_judgment_date` | Date/range for the judgment itself, only if evidence supports it. | Date/range or `unknown`, `unresolved`, `not_assessed`, `not_applicable`. | Conditional; may remain unresolved. | Temporal analysis; never derive from death date alone. |
| `temporal_metadata_evidence` | Citation/path for each temporal claim, including date precision and source. | Locator or explicit `not_assessed` / `not_available`. | Required when any date is asserted. | Supports temporal-firewall decision. |
| `source_text_correspondence` | Reviewer comparison between original dataset string and cited text. | `exact`, `minor_variation`, `substantial_difference`, `not_found`, `unresolved`, `not_assessed`. | Yes per candidate statement. | Affects target candidacy for corrupted/absent text. |
| `edition_variant_status` | What edition metadata/text says about variants or editorial material. | `no_variant_marked`, `variant_marked_in_edition_metadata`, `editorial_insertion_verified`, `editorial_note_or_footnote`, `unclear`, `not_assessed`, `not_applicable`. | Yes for bracket/apparatus cases; otherwise N/A or no variant marked. | Editorial insertion may be ineligible; a variant marker alone is not an insertion. |
| `source_verification_status` | Whether the source claim was checked against the cited material. | `verified_in_corpus`, `verified_external_edition`, `unverified`, `contradicted`, `not_assessed`. | Yes. | Unverified/contradicted claims may require quarantine/exclusion. |
| `corroboration_status` | Dependence relationship to proposed supporting witnesses. | `independent_corroboration`, `dependent_corroboration`, `unresolved_corroboration`, `not_examined`, `not_applicable`. | Yes; no default to independent. | Corroboration claim only; not an eligibility shortcut. |

Maintain these dates separately: evaluator lifespan/death, judgment date, source-work composition date, surviving witness date, and modern edition publication date. The project's provisional `T <= 365 AH` input boundary is a policy rule that still requires historical justification. It is not a universal periodization and does not make an attribution traceable by itself.

### 4.4 Research-use layer

| Field | Type and definition | Allowed values / missingness | Required? | Eligibility effect |
|---|---|---|---|---|
| `target_eligibility` | Whether the source-supported statement is an Ibn Hajar reference assessment candidate, independent of which research task may later use it. | `eligible_ibn_hajar_assessment`, `not_an_ibn_hajar_assessment`, `excluded_identity_mismatch`, `excluded_editorial_material`, `quarantined_unresolved`, `not_assessed`. | Yes per statement. | Records source/author candidacy; it does not itself place a row in an analysis extract. |
| `target_task_scope` | Whether and how a candidate fits a separately defined target task. | `ordinary_grade_candidate`, `status_only_candidate`, `not_target`, `unresolved`, `not_assessed`. | Yes. | Rank 1 / Companion status is never an ordinary grade candidate. A status-only task requires separate research approval. |
| `historical_input_eligibility` | Separate decision about using the passage as early historical input. | `eligible`, `quarantined_pending_verification`, `ineligible`, `not_applicable`, `not_assessed`. | Yes per statement. | Directly controls input extract, independently of target status. |
| `target_eligibility_reason`, `input_eligibility_reason` | Reason and evidence for each use decision. | Text with citations; for non-applicable use, say why. | Required for exclude/quarantine/eligible decisions. | Audit trail and reproducibility. |
| `reviewer_notes` | Interpretation or unresolved questions, not verbatim source content. | Free text; `none` only if explicitly reviewed and no note is needed. | Optional for routine cases; required for unresolved or mixed cases. | None directly. |

Target and input decisions must not be inferred from each other. A post-365 AH Ibn Hajar synthesis may be target-only; an earlier critic statement reported by Ibn Hajar may be target-excluded and input-quarantined at the same time. A source-supported Ibn Hajar status statement such as Rank 1 may be preserved as a reference assessment while excluded from the ordinary grade task; do not silently turn that into an approved status-prediction task.

## 5. Temporal firewall and source-role rules

The v2.0 fields operationalize, and do not replace, [`PROVENANCE_AND_TEMPORAL_FIREWALL_SPEC.md`](PROVENANCE_AND_TEMPORAL_FIREWALL_SPEC.md):

- `named_historical_evaluator` identifies whose judgment is claimed.
- `intermediary_transmitter` records the reporting link, if identifiable.
- `surviving_wording_author` identifies who composed/compiled the consulted wording.
- The linked source record identifies the consulted work, edition, locator, and witness.
- The evaluator's lifespan/death, judgment date, work date, witness date, and edition date remain separate.
- Route status is based on documented evidence and locator, not on whether a critic is named.
- The evaluator's death date at/before the provisional cutoff is necessary under the current input policy but is not sufficient for eligibility.
- Do not infer a judgment date from an evaluator's death date, or a witness date from a work's composition date.

For example, PROV-24 can encode al-Nasa'i as the named evaluator, Ibn Hajar as the surviving wording author, explicit attribution in the Taqrib passage, an unverified transmission route, target exclusion, and input quarantine at once. Those values describe different relationships and are not contradictory.

## 6. Cross-field validation rules

1. Every statement links to exactly one candidate entry; every candidate entry links to exactly one audit case. One case may link to multiple candidates, and one entry may link to multiple statements.
2. `taqrib_rank_number` is a nullable integer 1-12 only. `rank_status=assigned` iff an integer exists. Other statuses require a null integer.
3. Grade base/qualification fields are not used for biography or criticism statements. Such a statement may be adjacent to a grade, but it must have its own statement row if the reviewer confirms it is distinct.
4. A named historical evaluator does not imply `documented_traceable`. That status requires source/route evidence and a locator.
5. `compiler_authorship_status` and `historical_evaluator_attribution_status` are independent. A verified compiler wording can coexist with an unresolved historical attribution.
6. `source_text_correspondence`, compiler authorship, evaluator attribution, identity, edition variant, target eligibility, and input eligibility are independent assessments with separate rationales.
7. Rank 1 / Companion status cannot enter an ordinary grade distribution. A separately defined status task is a research decision, not an automatic extension.
8. A candidate with `identity_match_status=mismatch` cannot have eligible target or input status.
9. An ordinary grade-target candidate must be a source-supported Ibn Hajar evaluative grade attached to the accepted identity. A status statement such as Rank 1 is kept separate unless a status task is explicitly defined. This is a target-reference decision, not a claim of objective reliability.
10. An eligible historical input requires the applicable temporal rule plus verified attribution/source/route evidence and editorial integrity. If those are incomplete, quarantine or ineligibility must be explicit.
11. `edition_variant_status=variant_marked_in_edition_metadata` must not be converted to `editorial_insertion_verified` without separate evidence.
12. Every excluded/quarantined outcome needs a reason. No missingness code may be interpreted as eligible.

## 7. Migration boundary and future derivative

This specification does **not** migrate any current row. After review/approval, a migration should:

- Keep the frozen `MANUAL_COLLATION_PILOT_10.csv` and annotated working CSV unchanged as v1 inputs.
- Record and verify their input SHA-256 values before transformation. The audit baseline for the working file is `4b3f731b5a799c1df499c57391f4b502fcee84f129c2bae2e77325e738a04548`; the frozen packet SHA-256 is `78cb15eb72b04c1b2c0d2e350e375615236df22a2918c38256977ccccffae958`.
- Write only to a new versioned derivative directory, with schema version, script/version, input/output hashes, case/candidate/statement counts, and a row-level mapping key.
- Preserve every original field/value in an immutable legacy section or linked source file. Never overwrite Arabic source text with normalized text or English interpretation.
- Record each transformed/derived value with its mapping rule. Any human correction must have reviewer, date, reason, and evidence; do not silently infer it from the old enum.
- Keep the rejected PROV-04 candidate linked to its case and exclude it from target and model-input extracts.

## 8. Required tests for a later v2 derivative

These tests should be added and run against the **actual derivative**, not only the original 60-record worksheet:

1. Schema, keys, allowed values, conditional requiredness, and explicit missingness statuses.
2. Input hashes match the frozen packet and working CSV; originals remain byte-for-byte unchanged.
3. UTF-8 Arabic, punctuation, quotes, and embedded newlines survive CSV round-trip exactly.
4. Case → candidate → statement links are valid; PROV-04 has two candidate rows under one case; PROV-10 can have multiple statement rows without duplicate case identity.
5. Numeric rank values are integer/null only and obey `rank_status`; rank 1 is excluded from ordinary grade distributions.
6. PROV-24 can record al-Nasa'i as named authority and Ibn Hajar as wording author while route remains unverified; it remains target-excluded and input-quarantined until evidence changes.
7. PROV-51 is representable as collective-attribution-specific-transmission-criticism, without forced grade/rank or unsupported evaluator identity.
8. PROV-02's edition-variant marker is not automatically classified as a modern editorial insertion.
9. PROV-10's exact source string contains no English interpretation; interpretation is stored separately only if reviewed.
10. **PROV-04's rejected candidate can never enter target distributions or model inputs.** Assert it is absent from both derived extracts, the accepted candidate remains linked to the same case, and two candidate rows do not count as two narrators.
11. Identity matching cannot use grade text as a feature or decision rule.
12. Temporal date fields are not copied across roles; unknown work/witness/judgment dates remain explicitly unknown/unresolved, not inferred from evaluator death or publication date.
13. Target eligibility and historical-input eligibility are independently validated and can take different valid values for one statement.

## 9. Approval status and remaining scholarly decisions

This v2.0 specification incorporates the requested design changes, but it remains a proposal until reviewed. No annotation should resume under it before approval.

Schema questions addressed here: distinct evaluator/transmitter/wording-author roles; removal of evidence-strength scoring; separate compiler-authorship and evaluator-attribution outcomes; numeric rank plus rank status; explicit linked temporal source metadata; and independent target/input eligibility.

Scholarly questions remain separate from schema design: the source route behind PROV-24; the identities of critics collectively referenced in PROV-51; whether and how to segment PROV-10's adjacent biography; the source-level interpretation of PROV-02's edition variant; and the evidence supporting each PROV-04 identity decision. Unresolved answers must remain unresolved in the derivative.

The ten-case work remains a single-reviewer feasibility pilot. This specification makes no claim of independent reproducibility, inter-rater agreement, corpus-wide validity, or suitability for model training.
