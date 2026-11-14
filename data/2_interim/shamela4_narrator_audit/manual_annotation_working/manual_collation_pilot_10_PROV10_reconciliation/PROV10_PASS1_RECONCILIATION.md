# PROV-10 Pass 1 Reconciliation Record

## Scope and preservation

This is a separate comparison record created after the PROV-10 first-pass snapshot was frozen. It does not alter either annotation version.

- Frozen first-pass package: `../manual_collation_pilot_10_PROV10_pass1_frozen/`
- Frozen first-pass manifest SHA-256: `0c6d0b85f2675b2abc80a18f344602993907e92763255209703b023517bb83ee`
- Earlier annotation: `dataset_discovery/target_feasibility/manual_collation_pilot_10/MANUAL_COLLATION_PILOT_10_WORKING.csv`, SHA-256 `4b3f731b5a799c1df499c57391f4b502fcee84f129c2bae2e77325e738a04548`
- Preserved field-by-field legacy extract: `data/2_interim/shamela4_narrator_audit/manual_annotation_working/manual_collation_pilot_10_v2_2_impl_r2/legacy_v1_values.csv`, SHA-256 `894e915746dfdf902ea38bc392608321339e9776aeedc4ecdca5822dd62611d7`

The earlier annotation was opened only after the first-pass snapshot and its manifest were created. The old CSV, legacy extract, and frozen snapshot were left unchanged.

## Comparison

| Topic | Earlier annotation | Frozen first pass | Reconciliation status |
| --- | --- | --- | --- |
| Entry and text match | Entry 3552, p. 319; `exact_verbatim` | Local corpus record 3076 / page 319 / sequence 3552; exact Arabic spans are linked | Compatible on text location and wording. The corpus check is not an independent printed-page inspection. |
| Identity | `exact_match`, high identity fidelity; rationale used lineage, affiliation, reported sighting and death chronology | `confirmed` using Ibn Saʿd lineage, Khazraj affiliation, and father-son evidence; grade excluded | Outcome is compatible, but the evidence basis changed. The earlier rationale's use of `يقال له رؤية` is not retained as identity evidence. |
| Grade | `ثقة` recorded as the grade | Separate S01, `ثقة`, as a standardized narrator-grade statement | Compatible as a transcription. The frozen record keeps target-task suitability and historical-input eligibility `not_assessed`. |
| Rank | `taqrib_rank_number=3` | S01 has blank rank and `rank_status=unranked` | **Unresolved disagreement.** The basis for assigning rank 3 was not re-established in this pass. Preserve both values; do not infer a rank mapping from the word alone. |
| Ruʾyah phrase | `يقال له رؤية (biographical)` was placed in a field named `taqrib_qualification_verbatim` | Separate S02, exact text `يقال له رؤية`, classified as `biographical_or_factual_statement` | The old field mixed source text with an English gloss and treated the phrase as a qualification. The frozen pass preserves only the Arabic wording and its report marker. It does not treat the phrase as proof of Companion status. |
| Death wording | Included in the full entry but not separately represented | Separate S03, `مات سنة سبع أو ثمان وتسعين`; no normalized date | Newly segmented. No date conversion or corroboration decision has been made. |
| Passage author and grade attribution | `assessment_author=Ibn Hajar`, `assessment_attribution_status=compiler_own_synthesis`, and `compiler_or_transmitter=Ibn Hajar`; attribution fidelity `high` | Work metadata names Ibn Hajar as author, but passage-level wording author is unknown; grade attribution, compiler authorship, and transmission route remain unresolved or unassessed | **Substantive disagreement.** Work-level authorship does not establish that Ibn Hajar formulated this grade as an original synthesis or identify an earlier evaluator. The old attribution is retained only in the old record. |
| Attribution excerpt | Combined entry text through `يقال له رؤية` | Separate exact evidence for each statement; S01's excerpt is only `ثقة` | The frozen evidence has narrower statement boundaries. Exact correspondence does not establish historical provenance. |
| Editorial material | `editorial_material_status=none` | Edition variant status remains `not_assessed` | **Unresolved disagreement.** The earlier negative finding was not independently re-established from an inspected printed witness. |
| Corroboration | `unresolved_corroboration` | `not_examined` | These are different states: the earlier record reports an unresolved assessment; the frozen pass records that corroboration was not examined in this pass. |
| Eligibility | `input_eligibility=target_evaluation_only`; disposition `verified_ibn_hajar_assessment` | `target_task_scope=not_assessed`; `historical_input_eligibility=not_assessed` | **Not directly mappable.** The older combined label is not silently translated into the two separate v2.2 decisions. No target or historical-input eligibility is accepted here. |
| Fidelity scores | Textual, attribution, and identity fidelity all `high` | Exact local corpus spans and explicit unresolved attribution fields | The earlier scores have no direct v2.2 equivalent. They are preserved as prior judgements, not adopted. |

## Current reconciliation decision

No earlier value has been copied into or used to overwrite the frozen first-pass tables. The frozen pass remains the source for its recorded first-pass decisions; the earlier CSV remains the source for its legacy decisions. The rank mapping, editorial-material claim, attribution/synthesis claim, and eligibility decision remain open for later review. Any resolution should be recorded as a new reconciliation decision with its evidence and rationale, not by editing either source version in place.
