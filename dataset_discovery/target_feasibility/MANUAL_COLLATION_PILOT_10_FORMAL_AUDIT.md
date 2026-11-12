# Formal audit: 10-record manual source-collation pilot

**Audit date:** 2026-11-12  
**Scope:** Read-only review of the annotated working sheet, frozen packet, key, manifest, codebook/protocol, relevant local source metadata, and available tests. This report is a new audit artifact. It does not change the annotation, codebook, source data, or existing outputs.

## Executive assessment

The pilot is a useful feasibility exercise and demonstrates that the annotator is distinguishing several important cases: Ibn Hajar’s own synthesized grades, an explicitly attributed earlier judgment, a reported criticism that is not a standardized grade, a Companion-status description, a qualified grade, and a same-name collision. The records also preserve the crucial separation between target-candidate disposition and historical-input eligibility in most cases.

**Disposition: proceed with caution; do not treat the working sheet as a validated, internally consistent target/provenance table yet.** Before extending this collation or using its values downstream, resolve the codebook conflicts below and preserve the present annotations as an immutable audit snapshot. This audit does not make the scholarly decisions for the reviewer.

The intended target, if later used, must be described as **Ibn Hajar’s narrator-level assessment in *Taqrib al-Tahdhib***, not objective narrator reliability, historical consensus, or an independent count of evaluations. The project’s codebook, protocol, and reference-corpus documentation state this boundary. Source collation alone does not establish construct validity.

This is a single-reviewer pilot. My audit is a methodological review, not a second independent Arabic-trained annotation; no inter-reviewer agreement can be calculated from these materials.

## Materials and integrity checks

Reviewed:

- `dataset_discovery/target_feasibility/manual_collation_pilot_10/MANUAL_COLLATION_PILOT_10_WORKING.csv`
- Frozen `MANUAL_COLLATION_PILOT_10.csv`, internal key, and manifest in the same directory
- `IBN_HAJAR_GRADE_PROVENANCE_CODEBOOK.md` and `IBN_HAJAR_GRADE_PROVENANCE_PROTOCOL.md`
- `PROVENANCE_AND_TEMPORAL_FIREWALL_SPEC.md` and the local *Taqrib* book metadata
- The test definitions under `dataset_discovery/target_feasibility/`

Integrity observations:

- The working sheet has **11 entry rows for 10 distinct audit IDs**. PROV-04 has two candidate entries, one accepted and one rejected as a homonym; it must remain a two-row audit case, not two narrator targets.
- All 11 rows’ pre-populated/context columns match the frozen packet exactly. The 23 human-review columns contain 248 of 253 possible values; five cells remain blank, each in a context that appears intentionally not applicable or rejected (listed below). Blanks should not be silently interpreted as missing evidence.
- Frozen packet SHA-256: `78cb15eb72b04c1b2c0d2e350e375615236df22a2918c38256977ccccffae958` — matches its manifest.
- Working sheet SHA-256: `4b3f731b5a799c1df499c57391f4b502fcee84f129c2bae2e77325e738a04548`.
- Key SHA-256: `9eccd4533cb4482390a41861955e3636453d1f0bc39e8aac544f748f4dcc0684` — matches its manifest.
- The manifest records all source worksheet corroboration cells blank at generation; the working annotations now say unresolved for ten rows, while the rejected PROV-04 homonym’s corroboration and eligibility cells remain blank. That is not evidence of independent corroboration.

Blank annotation cells: PROV-24 `taqrib_qualification_verbatim` and `taqrib_rank_number`; PROV-51 `taqrib_rank_number`; rejected PROV-04 entry 5570 `input_eligibility` and `corroboration_status`. Treat these as intentional not-applicable/filtered values only where the reviewer’s rationale supports that interpretation; preferably document the convention in future data handling rather than inferring it from an empty cell.

## Findings requiring attention

### High: PROV-24 conflates named authority with traceable transmission

The row identifies al-Nasa’i in the Taqrib phrase `وثقه النسائي`, but its reviewer note explicitly says that the transmission route and verbatim quotation status have not been established. The codebook defines `traceable_intermediary_historical_judgment` as requiring a traceable intermediary source or chain. A named authority in Ibn Hajar’s wording supports recording the named attribution; by itself it does not establish the route or source witness. The row’s `assessment_attribution_status` therefore overstates the evidence as currently described.

There are two additional codebook mismatches in this row:

- `assessment_author = al-Nasai` is outside the codebook’s allowed literal `Al-Nasa'i` (and should use one consistent canonical spelling if retained).
- `attribution_fidelity = high` conflicts with the codebook definition of `high` as an Ibn Hajar-authored standardized appraisal, while the same row is classified `excluded_not_ibn_hajar` and says the phrase is an earlier critic’s attributed judgment.

The row correctly keeps the record out of Ibn Hajar target evaluations and quarantines it as input. Do not treat the mention of Sunan al-Nasa’i as inspected corroboration; the note appropriately calls it a candidate for later primary inspection.

### High: PROV-51 uses categories that do not describe its evidence

The Arabic statement `عابوا عليه أنه حدث عن أبيه بغير سماع` reports a criticism of a specific transmission practice. It is not, on the evidence recorded here, a standardized narrator-level grade. The sheet’s `excluded_not_a_grade` rationale is directionally sensible, but the codebook currently defines that value only for biographical, generational, or honorific descriptions. The current allowed dispositions do not clearly represent a specific non-standardized transmission criticism.

The row records `assessment_attribution_status = insufficient_evidence_historical_judgment` but `input_eligibility = quarantined_intermediary_input`; the codebook reserves `quarantined_insufficient_evidence` for insufficiently supported attributions. Its `assessment_author` value (`Unidentified earlier critics (collective attribution)`) is also not one of the codebook’s allowed values. Finally, `attribution_fidelity = high` is inconsistent with both the unidentified collective attribution and the codebook’s Ibn Hajar-assessment definition of `high`.

The annotation note appropriately keeps this out of conventional reliability-grade target modeling and states that parallels in other works have not been independently collated. Those cautions should remain attached to the case.

### High: PROV-02 overstates what square brackets mean

The local *Taqrib* metadata for the Awwamah edition says that differences from the Abi al-Ashbal edition are shown in square brackets. It does not say that bracketed words are modern-editor additions. Yet the working sheet labels the passage `bracketed_addition`, whose codebook definition specifically means modern-editor additions. The separate firewall specification already has the more appropriate concept `variant_reading_note`, but the worksheet codebook does not.

Therefore the current value does not follow the available edition metadata. The note should describe this as an edition-variant marker unless direct collation establishes a different editorial status. Also replace claims that the bracketed wording was “lost” from HadithDB with the narrower observation that the dataset field omits the bracket/variant-status marker; omission of a marker does not by itself establish which reading is preferable or whether editorial intervention occurred.

### Moderate: the fidelity dimensions are not applied consistently

The codebook defines `textual_fidelity = high` as exact wording or negligible whitespace difference. PROV-37 and PROV-56 are marked `taqrib_text_match_status = minor_variation` for orthographic differences, but `textual_fidelity = high`. PROV-02 also has a minor-variation text match and high fidelity. The reviewer may intend the two fields to answer different questions, but the definitions do not explain that distinction clearly enough to make these combinations reproducible.

More broadly, the working sheet has 11 `attribution_fidelity = high` values, including the attributed judgment, collective criticism, and Companion-status description. That is incompatible with the field’s current definition as fidelity to Ibn Hajar’s own standardized appraisal. The field appears to be used at times for source/text authorship and at times for assessment attribution. These are separate questions and should not be collapsed when this sheet is used analytically.

### Moderate: PROV-10’s “verbatim” qualification includes interpretation

`taqrib_qualification_verbatim` contains `يقال له رؤية (biographical)`. The Arabic portion is source wording; `(biographical)` is an English interpretation, not verbatim source text. The note makes the interpretation transparently and appropriately distinguishes it from a grade qualification, but a column labeled `verbatim` should contain only the source string. Keep interpretation in reviewer notes or a separately defined annotation field; do not alter this record as part of this audit.

### Moderate: PROV-04 is a good circularity safeguard, with a downstream counting risk

The two candidate entries have different grades (`ثقة له أفراد` and `مقبول`). The accepted identity rationale cites independent biographical identifiers rather than grade agreement, which follows the protocol’s safeguard against using the expected target to resolve identity. The rejected entry is correctly marked `excluded_identity_mismatch`, with low identity/text fidelity.

The working file is entry-level and includes the rejected row. Any later count or modeling extract must explicitly exclude that row and avoid counting both rows as two people or two assessments. Its blank eligibility field does not make it eligible; the disposition and identity finding control. No current test verifies this downstream filtering.

### Moderate: PROV-01’s rank is descriptive, not an ordinary grade target

`صحابي` / `ابن صحابي` identifies status and biography. The annotation correctly excludes it from the ordinary reliability-grade target while recording Rank 1 under the project’s twelve-rank scheme. Keep that rank in a descriptive/source-collation record if useful, but do not count it as an ordinary eligible grade without an explicit research definition that includes status categories. The project’s firewall documentation also distinguishes Rank 1 from ordinary jarh/taʿdil evaluation.

## Case-level observations

| Case | Audit observation |
| --- | --- |
| PROV-10 | Full-entry reading distinguishes `يقال له رؤية` as biographical information. The “verbatim” qualification field nevertheless contains the English gloss `(biographical)`. |
| PROV-40 | The note uses multiple identifiers and records the kunya variant in the local biographical record. Identity is supported by more than the shared name; the note should keep its cited source fields/locator explicit for reproducibility. |
| PROV-39 | The row preserves `اختلط في الآخر` as a qualification and does not collapse it into the base grade. Historical implications for particular transmissions remain outside what this collation alone establishes. |
| PROV-56 | The row preserves `يخطىء` separately from `صدوق`; note the `minor_variation` versus `high` fidelity ambiguity above. |
| PROV-24 | Candidate identity is supported by more than the kunya, but historical authority and transmission route remain different evidentiary questions; see high finding. |
| PROV-51 | Specific transmission-practice criticism; no standardized rank. Category and provenance enum conflicts; see high finding. |
| PROV-01 | Companion status is treated as non-grade, appropriately separated from ordinary reliability assessment. |
| PROV-02 | Qualified grade is retained; square brackets are documented as edition differences by local metadata, not necessarily modern additions. |
| PROV-04 | Two candidate entries remain visible and the rejected homonym is kept out of target use. Preserve that exclusion in any derivative table. |
| PROV-37 | Qualification `يخطئ` is preserved; identity note differentiates the nearby homonym using biographical attributes. Fidelity category ambiguity remains. |

These observations concern the internal support and consistency of the recorded annotations. They are not a new independent scholarly collation of every cited earlier source, a manuscript review, or a verification against a physical copy of the edition.

## Target and provenance model implications

The current material supports only a **case-level feasibility assessment**, not population-wide conclusions. The 10 cases are purposively selected from the fixed 60-case sample; they are not representative of the source corpus. The 11 rows are candidate entry records, not 11 narrators or independent historical evaluations.

A later research table should keep distinct:

1. **Target candidate:** Ibn Hajar’s own narrator-level evaluative classification in *Taqrib*, including its original wording and qualifications. This is a historical author’s classification, not objective reliability truth.
2. **Statement/claim type:** evaluative grade, attributed earlier judgment, descriptive biography/status, specific transmission criticism, or other text.
3. **Attribution evidence:** who is named as the source of a judgment versus who transmits or compiles the surviving wording; whether the route/source is actually traceable.
4. **Eligibility/quarantine:** what may be considered as a historical input, separately from whether it is a valid target candidate.
5. **Identity evidence:** match decisions based on independent identifiers, never on agreement with the grade being evaluated.

The present codebook captures parts of this architecture but has category gaps for non-standardized criticism, variant readings, and distinct attribution dimensions. This is a finding from the pilot, not a request to expand the automated classifier.

## Test and verification limits

The recorded test run used `python -B -m unittest discover -s dataset_discovery/target_feasibility -p 'test_*.py' -v`: **36 tests passed**. A pytest invocation could not start because pytest is not installed in the active Python environment (`No module named pytest`); this is an environment limitation, not a test assertion failure.

The tests provide useful coverage for the generated 60-record worksheet, helper logic, and local reference corpus. They do **not** validate the human working sheet’s annotation values: the relevant test setup loads the frozen 60-record worksheet, not `MANUAL_COLLATION_PILOT_10_WORKING.csv`. Thus the passing suite does not establish that the 10-case annotations obey the codebook or that PROV-04’s rejected row will be excluded from downstream analysis. No test failure is inferred from the absence of these checks.

## Go/no-go recommendation

**No-go for treating this pilot as a finalized, analysis-ready provenance/target table or expanding the same annotation scheme at scale without reconciliation.** The main blockers are PROV-24 and PROV-51’s incompatible attribution/eligibility categories, PROV-02’s edition-variant status, and inconsistent use of fidelity fields.

**Go for retaining this as a completed feasibility pilot and using it to refine the human protocol.** The pilot has already exposed useful distinctions and preserved the originals. Before further source collation, the reviewer should reconcile the identified conflicts against the codebook, retain a dated audit trail of any changes, and confirm that any downstream extract filters the rejected PROV-04 candidate. Do not infer reliability, historical truth, independent evaluations, or corroboration from this pilot.

## Review status

Read-only audit completed. No annotation, codebook, protocol, source record, test, manifest, or prior output was changed. No commit or push was made.
