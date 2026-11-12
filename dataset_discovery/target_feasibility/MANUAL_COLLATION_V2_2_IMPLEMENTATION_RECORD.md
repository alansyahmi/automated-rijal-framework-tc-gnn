# Manual Collation Schema v2.2 Implementation Record

**Schema baseline:** v2.2, frozen in `MANUAL_COLLATION_SCHEMA_V2_2_FINAL.md`
**Migration implementation:** 2.2.1
**Status:** implemented, generated, and independently checked
**Review status:** no new human annotations or scholarly decisions were created

## Scope and preservation

The frozen v2.2 specification and inputs were not changed. The earlier derivative at `data/2_interim/shamela4_narrator_audit/manual_annotation_working/manual_collation_pilot_10_v2_2/` remains an **incomplete implementation retained as historical audit evidence**; it is not represented as compliant. The corrected package was generated separately at:

`data/2_interim/shamela4_narrator_audit/manual_annotation_working/manual_collation_pilot_10_v2_2_impl_r1/`

The package contains 10 cases, 11 candidate entries, 11 provisional `-S00` work items, 748 legacy input-cell values, and zero reviewed scholarly statements. All new annotation and eligibility decisions remain unfilled. PROV-04's two candidate entries remain separate under the same case.

## Corrections implemented

- The ordinary-grade guard now requires linked, transcribed, independently sourced identity evidence; a non-empty comparison span, rationale, and locator; reviewed and transcribed statement text; passage support with linked evidence; supported Ibn Hajar compiler synthesis; explicit no-earlier-evaluator wording; a verified source and acceptable edition status; rank 2–12 with `rank_status=assigned`; and `historical_input_eligibility=not_applicable` for a Task A target. Missing, unresolved, contradictory, placeholder, rank-1, and excluded cases fail closed.
- Staged validation now checks every declared table shape, required values, enums, primary keys, text/status pairs, rank/status pairs, case/candidate/statement/attribution/source/evidence/date/feature references, candidate and row-map order, exact legacy-cell coverage, source locator relationships, attribution roles, date evidence, and feature-source constraints before publication.
- The field registry inventories every concrete field in the frozen logical-table inventory, output table, type, enum values, nullability, and validation rule. It also marks implementation-support fields separately. All 32 enum definitions were compared with the frozen v2.2 registry.
- The manifest records all four pinned input hashes, sizes, row counts, encodings and headers; script path/version/hash and runtime; output hashes, byte sizes, row counts and headers; source-column and input-row mappings; status/missingness counts; validation outcomes; and explicit non-inference statements. `manifest.json` and `MANIFEST.sha256` remain excluded from the data-output hash list; the checksum file records the manifest hash.
- Reusable analytical filters omit provisional and superseded placeholders from counts and exports. Target/training/evaluation extracts also require verified passage provenance and the strict ordinary-grade guard. Replacing S00 text alone cannot promote it.
- Historical-input decisions require policy ID/version and rationale, statement-linked temporal evidence, verified sources, and separate recorded evaluator-death and approximate-judgment date claims before an eligible/ineligible result can pass. No such decision or date was inferred for this pilot.
- The v2.2 specification was left unchanged. This record documents implementation state separately.

## Acceptance matrix

Each row corresponds to one of the 19 required validation items in frozen specification section 5. “Passed” describes implementation/test evidence, not scholarly acceptance of the 10 cases.

| # | Frozen v2.2 requirement | Implementation and test evidence | Result |
|---:|---|---|---|
| 1 | Verify all four input hashes and metadata; verify output hashes and separate manifest checksum. | `_verify_inputs`, `_validate_manifest_metadata`, `_validate_staged_package`; `test_all_four_pinned_inputs_match_the_frozen_baseline`, `test_hash_mismatch_fails_before_output_or_staging`, `test_manifest_excludes_self_hash_and_checksum_from_data_hashes`; independent final hash/size/header/row-count check. | Passed |
| 2 | Preserve frozen/working source context, original values, and prior outputs. | Exact 748-cell `legacy_v1_values.csv`; `test_migration_scaffolds_ten_cases_eleven_candidates_and_provisional_items`, `test_arabic_and_newlines_round_trip_and_original_inputs_are_preserved`, `test_previous_derivative_is_unchanged_and_new_destination_is_distinct`; independent hash verification of all 10 prior derivative data files. | Passed |
| 3 | Enforce all verbatim-text/status invariants. | `TEXT_STATUS_PAIRS`, `_status_text_valid`, `validate_package_tables`; `test_validator_rejects_invalid_enum_text_status_rank_and_edition_claim`, `test_ordinary_guard_requires_nonempty_span_text_and_locator_rationale`. | Passed |
| 4 | Round-trip Arabic, punctuation, quotes, BOM, and embedded newlines exactly. | `read_csv` uses UTF-8 BOM handling; CSV writer uses UTF-8 and fixed dialect; `test_arabic_and_embedded_newline_csv_round_trip` covers Arabic punctuation, quotes, BOM, and multiline text. | Passed |
| 5 | Keep compiler/work author, surviving wording author, transmitter, and evaluator roles separate. | Separate columns in `sources.csv` and `attribution_links.csv`; `test_special_pilot_cases_remain_unassessed_and_roles_are_separate`. | Passed |
| 6 | Passage naming must not imply historical attribution or a traceable route; include PROV-24 regression. | Attribution status fields and evidence checks; `test_prov24_and_prov51_attributions_do_not_force_historical_route_or_grade` keeps reported naming separate from unverified attribution and route. | Passed |
| 7 | Represent PROV-51 collective transmission criticism without forcing a grade or rank. | Frozen statement/attribution enums and separate fields; same PROV-51 regression verifies rank is blank/unranked and target scope is out of ordinary-grade analysis. | Passed |
| 8 | Do not promote PROV-02 variant markings to verified editorial insertion without evidence. | Edition metadata evidence requirement; `test_special_pilot_cases_remain_unassessed_and_roles_are_separate` checks PROV-02 remains `not_assessed` with no evidence link. | Passed |
| 9 | Do not insert the PROV-10 English gloss into statement text or segment it automatically. | Migration creates only textless S00 work items; `test_special_pilot_cases_remain_unassessed_and_roles_are_separate` checks PROV-10 remains blank, and scaffold tests check all 11 S00 rows. | Passed |
| 10 | Keep statement validity independent from authorship, identity, and task scope; allow PROV-01 status-only representation. | Statement-level support and target fields; `test_prov01_status_only_scope_is_separate_from_text_support_and_ordinary_grade` uses an explicitly synthetic structural fixture to show supported text with rank 1/status-only scope is not an ordinary target. Actual PROV-01 remains unassessed. | Passed |
| 11 | Enforce rank/null status, rank-1 exclusion, and preserve legacy rank strings without assigning them. | Rank validator and legacy snapshot; `test_ordinary_guard_rank_boundaries_and_positive_cases`, `test_validator_rejects_invalid_enum_text_status_rank_and_edition_claim`, scaffold assertions for null rank/`not_assessed`. | Passed |
| 12 | Keep candidate-field comparison separate from statement-to-passage comparison, each with its own span/rationale/locator. | Separate candidate and statement columns and evidence links; `test_ordinary_guard_requires_nonempty_span_text_and_locator_rationale`, `test_reviewed_statement_requires_full_provenance_before_analysis`. | Passed |
| 13 | Give each date claim its own evidence; do not infer one date from another. | `date_claims.csv` and temporal evidence validation; `test_recorded_date_claim_has_its_own_temporal_evidence_link`, `test_temporal_eligibility_requires_linked_judgment_and_evaluator_dates`. Output date table is empty because no dates were reviewed. | Passed |
| 14 | Record temporal policy and prevent eligibility based only on evaluator death. | `validate_historical_input_decision` requires policy, rationale, linked evidence, verified source, evaluator-death and approximate-judgment claims; temporal regression rejects death-only support. No temporal eligibility is assigned in the output. | Passed |
| 15 | Exclude direct target leakage and Taqrib target sources from Task A features. | `validate_feature_source_record` requires date provenance, policy/version and rationale; blocks named grade/target fields and the Taqrib source/work; `test_task_a_feature_firewall_rejects_direct_names_and_taqrib_sources`. No feature rows are included in this package. | Passed with limit¹ |
| 16 | Keep rejected PROV-04 candidate mismatch out of target extracts; keep two entries under one case. | `ordinary_grade_candidate_conditions_pass` and analytical filter; `test_prov04_rejected_candidate_is_absent_from_target_extract` verifies two candidate entries in one case but only the accepted synthetic candidate in the target extract. Existing actual candidate decisions remain unassessed in the package. | Passed |
| 17 | Ensure deterministic output, stop on any input-hash mismatch or ambiguous join. | Fixed CSV dialect/order, sorted JSON, composite-key rejection, pinned hashes; `test_identical_inputs_produce_byte_identical_packages`, `test_composite_join_rejects_duplicate_keys`, `test_hash_mismatch_fails_before_output_or_staging`. | Passed |
| 18 | Publish atomically, refuse overwrite, and clean only owned staging artifacts. | Same-parent staging and `os.rename`; `test_validation_failure_cleans_only_its_staging_and_lock`, `test_existing_output_is_never_overwritten`, `test_broken_staged_join_fails_without_publishing_or_leaving_temp_files`; successful generated package validated before publication. | Passed |
| 19 | Exclude provisional/superseded S00 from counts, distributions, completion denominators, training and evaluation even after text replacement. | `filter_analytical_rows`, `annotation_completion_counts`, `export_analytical_rows`; `test_s00_and_text_replacement_are_excluded_from_analytical_rows`, `test_reviewed_statement_requires_full_provenance_before_analysis`, plus output count/status verification. | Passed |

¹ The structural checks reject named direct leakage and Taqrib source/work reuse. They cannot infer whether an otherwise separate compilation silently reproduces the target assessment. That dependence decision requires documented source review; this package contains no included feature sources.

## Verification results

- Command: `python -B -m unittest discover -s dataset_discovery/target_feasibility -p 'test_*.py' -v`
- Result: **69 tests passed**.
- `git diff --check`: passed; Git printed only existing LF-to-CRLF warnings for the two previously modified README files.
- Independent package validation: passed. It rechecked the published manifest checksum, every output hash and size, all CSV headers and row counts, every enum value against the frozen registry, all 32 frozen enums, the 10/11/11/748 row counts, and the S00/non-inference flags.
- Prior derivative: unchanged. Its manifest hash, checksum hash, and all 10 manifest-listed data-output hashes match the pre-edit baseline.
- Frozen inputs/specification: unchanged and still match their pinned hashes.
- No commit or push was made.

## Hash record

The manifest hash is stored separately in `MANIFEST.sha256`; the checksum file does not hash itself. Per-output hashes below also appear in the package manifest.

| Artifact | SHA-256 |
|---|---|
| Frozen v2.2 specification | `2bcba2ade81ce57ec9075bd587c3ab62eafb09845183cfa1d44b6e709d38c860` |
| Frozen packet | `78cb15eb72b04c1b2c0d2e350e375615236df22a2918c38256977ccccffae958` |
| Working annotations | `4b3f731b5a799c1df499c57391f4b502fcee84f129c2bae2e77325e738a04548` |
| Provenance key | `9eccd4533cb4482390a41861955e3636453d1f0bc39e8aac544f748f4dcc0684` |
| Input manifest | `9339ad77f1fa18e204b443e9a3ec888d6ec56924b801b85d94f3bb8ea49bf72d` |
| Migration script | `92dce857fa4931075d67cac9ba78c6ddf89d339ccfbf63fe2ccc8ae27220c3ca` |
| New package manifest | `708390595ab807406234aa04a0f8bba0657fb0c485eac4ed13e628e2a87bbe48` |
| `attribution_links.csv` | `45e94a675df7b25de782f175b8aeb1cd6a884d71b66e6e87f319b49fe00d3e9e` |
| `candidate_entries.csv` | `8371a9b81c851fba61c0943af9ed179c720f6c2e7b3f7e3c532f5d5c72ba149b` |
| `cases.csv` | `fce014299bcbd59594adcd047305c654866ad6671734deb3aa232cb27f5bb5ae` |
| `column_mapping.csv` | `7781f4c9779bd3573061f47414dcbfcbc2f1b8f858789a13f6a7c8e57001b0c0` |
| `date_claims.csv` | `4fed65cb0b7015a9fdc0e6c46f4529daeee70d51ea8275bfd39fb6a32c11daab` |
| `feature_sources.csv` | `f60f0a40fc58a9a56647edd2e984d151551b8f88e2f4de8eb691944d828bf4f1` |
| `legacy_v1_values.csv` | `894e915746dfdf902ea38bc392608321339e9776aeedc4ecdca5822dd62611d7` |
| `migration_mapping.csv` | `5dba0c3f973cfdb3064a4e6f74a54986e6036b6cc999596b71a719a3d98c2634` |
| `schema_field_registry.json` | `e5be54b6f58355601e5b3b94b2dab121fd645d5a41794c78a97e37cea20841bf` |
| `source_evidence.csv` | `169bc1c0dcc62655fc858ccd9790e6cb02d8c1ebbe05f55c528867587e9489fc` |
| `sources.csv` | `1cf432096c94c85851f73bdb8af02aa355878088f4dc49ae1759732dd1edebda` |
| `statements.csv` | `da0c10816b544d33ce72440b635e17ace40849e1ce7784fc0d9008a85a32bbfe` |

## Known limits and next review gate

- The 11 statement rows are operational placeholders, not 11 scholarly statements. No identity, statement segmentation, attribution, route, rank, corroboration, or historical-input decision was inferred.
- The pinned upstream pilot manifest records hashes for the frozen packet and provenance key but does not record a working-CSV hash. The working CSV is independently pinned in the migration script and recorded in this new manifest. The input manifest's own hash is pinned externally; it cannot contain its own hash.
- The new package copies bibliographic metadata from the pinned corpus manifest. This does not establish a manuscript witness, historical attribution, or independent corroboration. The integer source-ID semantics were not established by upstream documentation in the reviewed repository materials.
- The feature firewall catches explicit/name-based direct leakage and re-use of the Taqrib target source/work. It cannot establish that an apparently separate later compilation is textually independent without scholarly source comparison.
- Temporal eligibility now fails closed without separately evidenced evaluator and approximate judgment dates plus a versioned policy. No such source review or policy decision has been completed here.
- This is a deterministic migration scaffold, not a scholarly review of the ten cases, a narrator-reliability dataset, or a model-ready dataset. The next gate is human re-review of the ten candidates under v2.2 before analytical use.
