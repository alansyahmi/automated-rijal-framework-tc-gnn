import csv
import hashlib
import re
import tempfile
import unittest
from pathlib import Path

import migrate_manual_collation_v2_2 as migration


ROOT = Path(__file__).resolve().parents[2]
INPUT_DIR = ROOT / "dataset_discovery" / "target_feasibility" / "manual_collation_pilot_10"
PRIOR_OUTPUT = (
    ROOT
    / "data"
    / "2_interim"
    / "shamela4_narrator_audit"
    / "manual_annotation_working"
    / "manual_collation_pilot_10_v2_2"
)
PRIOR_MANIFEST_SHA256 = "74d9aac1ef7ad356d5a84c08dbc782a2de384a053a9bee83064128ffbae3ed82"
PRIOR_CHECKSUM_SHA256 = "c1967ea08df73400683e5373ca30cae0d0f75c9bf62ea2b08c81041ded4ed5f3"


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def input_tables():
    frozen_headers, frozen_rows = migration.read_csv(INPUT_DIR / migration.FROZEN_NAME)
    working_headers, working_rows = migration.read_csv(INPUT_DIR / migration.WORKING_NAME)
    assert frozen_headers == migration.EXPECTED_HEADERS
    assert working_headers == migration.EXPECTED_HEADERS
    hashes = {
        name: hashlib.sha256((INPUT_DIR / name).read_bytes()).hexdigest()
        for name in migration.EXPECTED_INPUT_HASHES
    }
    source_metadata = migration._validate_manifest_metadata(
        (INPUT_DIR / migration.MANIFEST_NAME).read_bytes(), hashes[migration.FROZEN_NAME], hashes[migration.KEY_NAME]
    )
    tables = migration._build_tables(migration._validate_and_join(frozen_rows, working_rows), source_metadata)
    tables["column_mapping.csv"] = migration._build_column_mapping(frozen_headers, working_headers, source_metadata)
    return tables


def valid_grade_records(rank="2"):
    candidate = {
        "audit_record_id": "PROV-TEST",
        "candidate_entry_id": "PROV-TEST-C01",
        "original_grade_field": "grade_score",
        "taqrib_source_record_id": "SRC-TAQRIB",
        "candidate_entry_text_status": "transcribed",
        "taqrib_entry_text_verbatim": "123 - entry",
        "identity_match_status": "confirmed",
        "identity_evidence_verbatim": "Identity evidence text",
        "identity_evidence_text_status": "transcribed",
        "identity_evidence_record_id": "EV-IDENTITY",
        "identity_evidence_locator": "work 2, entry 4",
        "identity_evidence_independence_rationale": "Distinct biographical work was checked.",
        "candidate_field_source_correspondence": "exact",
        "candidate_comparison_source_span": "ثقة",
        "candidate_comparison_source_span_status": "transcribed",
        "candidate_comparison_rationale": "The cited span is the assessment corresponding to the input field.",
        "candidate_comparison_locator": "Taqrib p. 2, entry 123",
    }
    statement = {
        "audit_record_id": "PROV-TEST",
        "candidate_entry_id": candidate["candidate_entry_id"],
        "statement_id": "PROV-TEST-C01-S01",
        "statement_record_status": "reviewed_statement",
        "statement_type": "standardized_narrator_grade",
        "statement_text_verbatim": "ثقة",
        "statement_text_status": "transcribed",
        "grade_base_verbatim": "ثقة",
        "grade_base_text_status": "transcribed",
        "grade_qualification_verbatim": "",
        "grade_qualification_text_status": "not_assessed",
        "taqrib_rank_number": rank,
        "rank_status": "assigned" if rank else "not_assessed",
        "taqrib_statement_validity": "supported_taqrib_statement",
        "target_task_scope": "ordinary_grade_candidate",
        "target_task_scope_rationale": "All ordinary-grade conditions were checked.",
        "statement_source_correspondence": "exact",
        "statement_source_span_verbatim": "ثقة",
        "statement_source_span_status": "transcribed",
        "statement_source_correspondence_rationale": "The statement matches the cited source span.",
        "statement_source_locator": "Taqrib p. 2, entry 123",
        "statement_source_evidence_record_id": "EV-STATEMENT",
        "historical_input_eligibility": "not_applicable",
        "historical_input_eligibility_rationale": "Task A target; no historical feature decision made.",
        "corroboration_status": "not_examined",
        "temporal_policy_id": "",
        "temporal_policy_version": "",
        "temporal_policy_result": "not_applicable",
    }
    attribution = {
        "attribution_link_id": "PROV-TEST-C01-S01-A01",
        "statement_id": statement["statement_id"],
        "named_historical_evaluator": "",
        "evaluator_value_status": "none_named",
        "intermediary_transmitter": "",
        "transmitter_value_status": "none_identified",
        "surviving_wording_author": "Ibn Hajar",
        "wording_author_value_status": "identified",
        "attribution_form": "compiler_synthesis",
        "passage_evaluator_naming_status": "no_evaluator_named",
        "historical_evaluator_attribution_status": "not_applicable",
        "transmission_route_status": "not_applicable",
        "compiler_authorship_status": "supported",
        "attribution_evidence_verbatim": "Taqrib passage evidence",
        "attribution_evidence_text_status": "transcribed",
        "attribution_evidence_record_id": "EV-ATTRIBUTION",
        "attribution_evidence_locator": "Taqrib p. 2, entry 123",
        "transmission_route_evidence_record_id": "",
    }
    target_source = {
        "source_record_id": "SRC-TAQRIB",
        "candidate_entry_id": candidate["candidate_entry_id"],
        "source_work_id": "3076",
        "source_work_title": "تقريب التهذيب",
        "consulted_edition": "Digital corpus text",
        "consulted_editor": "",
        "consulted_witness_id": "",
        "consulted_witness_type": "",
        "source_work_author_compiler": "Ibn Hajar",
        "source_author_metadata_status": "recorded",
        "source_locator_verbatim": "Taqrib, p. 2, entry 123",
        "canonical_source_locator_key": "3076:2:123",
        "source_verification_status": "verified_in_corpus",
        "edition_variant_status": "no_variant_marked",
    }
    identity_source = {
        "source_record_id": "SRC-BIO",
        "candidate_entry_id": candidate["candidate_entry_id"],
        "source_work_id": "BIO-WORK-2",
        "source_work_title": "Independent biographical source",
        "consulted_edition": "Edition 1",
        "consulted_editor": "",
        "consulted_witness_id": "",
        "consulted_witness_type": "",
        "source_work_author_compiler": "",
        "source_author_metadata_status": "not_assessed",
        "source_locator_verbatim": "work 2, entry 4",
        "canonical_source_locator_key": "",
        "source_verification_status": "verified_external_edition",
        "edition_variant_status": "not_assessed",
    }
    evidence = {
        "EV-IDENTITY": {
            "evidence_record_id": "EV-IDENTITY",
            "source_record_id": "SRC-BIO",
            "candidate_entry_id": candidate["candidate_entry_id"],
            "statement_id": "",
            "attribution_link_id": "",
            "evidence_role": "identity",
            "evidence_text_verbatim": "Identity evidence text",
            "evidence_text_status": "transcribed",
            "source_locator": "work 2, entry 4",
        },
        "EV-STATEMENT": {
            "evidence_record_id": "EV-STATEMENT",
            "source_record_id": "SRC-TAQRIB",
            "candidate_entry_id": "",
            "statement_id": statement["statement_id"],
            "attribution_link_id": "",
            "evidence_role": "passage_text",
            "evidence_text_verbatim": "ثقة",
            "evidence_text_status": "transcribed",
            "source_locator": "Taqrib p. 2, entry 123",
        },
        "EV-ATTRIBUTION": {
            "evidence_record_id": "EV-ATTRIBUTION",
            "source_record_id": "SRC-TAQRIB",
            "candidate_entry_id": "",
            "statement_id": "",
            "attribution_link_id": attribution["attribution_link_id"],
            "evidence_role": "passage_text",
            "evidence_text_verbatim": "Taqrib passage evidence",
            "evidence_text_status": "transcribed",
            "source_locator": "Taqrib p. 2, entry 123",
        },
    }
    return candidate, statement, attribution, target_source, identity_source, evidence


class ManualCollationV22HardeningTests(unittest.TestCase):
    def test_ordinary_guard_rejects_confirmed_identity_without_evidence(self):
        candidate, statement, attribution, source, _identity, evidence = valid_grade_records()
        candidate["identity_evidence_text_status"] = "not_assessed"
        candidate["identity_evidence_verbatim"] = ""
        evidence.pop("EV-IDENTITY")
        self.assertFalse(
            migration.ordinary_grade_candidate_conditions_pass(
                candidate,
                statement,
                attribution,
                source,
                evidence_by_id=evidence,
                sources_by_id={"SRC-TAQRIB": source},
            )
        )

    def test_ordinary_guard_requires_nonempty_span_text_and_locator_rationale(self):
        adversarial_updates = (
            {"candidate_comparison_source_span": ""},
            {"candidate_comparison_rationale": ""},
            {"candidate_comparison_locator": ""},
            {"statement_text_verbatim": ""},
        )
        for update in adversarial_updates:
            with self.subTest(update=update):
                candidate, statement, attribution, source, identity_source, evidence = valid_grade_records()
                if "statement_text_verbatim" in update:
                    statement.update(update)
                else:
                    candidate.update(update)
                self.assertFalse(
                    migration.ordinary_grade_candidate_conditions_pass(
                        candidate,
                        statement,
                        attribution,
                        source,
                        evidence_by_id=evidence,
                        sources_by_id={source["source_record_id"]: source, identity_source["source_record_id"]: identity_source},
                    )
                )

    def test_ordinary_guard_rank_boundaries_and_positive_cases(self):
        for rank, expected in (("1", False), ("2", True), ("12", True), ("", False), ("13", False), ("3.0", False)):
            with self.subTest(rank=rank):
                candidate, statement, attribution, source, identity_source, evidence = valid_grade_records(rank)
                self.assertEqual(
                    migration.ordinary_grade_candidate_conditions_pass(
                        candidate,
                        statement,
                        attribution,
                        source,
                        evidence_by_id=evidence,
                        sources_by_id={source["source_record_id"]: source, identity_source["source_record_id"]: identity_source},
                    ),
                    expected,
                )

    def test_ordinary_guard_rejects_unresolved_or_contradictory_statuses(self):
        mutations = (
            ("candidate", "identity_evidence_text_status", "not_assessed"),
            ("candidate", "identity_match_status", "unresolved"),
            ("statement", "historical_input_eligibility", "ineligible"),
            ("statement", "historical_input_eligibility", "not_assessed"),
            ("statement", "statement_record_status", "provisional_work_item"),
            ("statement", "rank_status", "unranked"),
            ("attribution", "passage_evaluator_naming_status", "not_assessed"),
            ("attribution", "evaluator_value_status", "not_assessed"),
        )
        for target, field, value in mutations:
            with self.subTest(target=target, field=field, value=value):
                candidate, statement, attribution, source, identity_source, evidence = valid_grade_records()
                {"candidate": candidate, "statement": statement, "attribution": attribution}[target][field] = value
                self.assertFalse(
                    migration.ordinary_grade_candidate_conditions_pass(
                        candidate,
                        statement,
                        attribution,
                        source,
                        evidence_by_id=evidence,
                        sources_by_id={source["source_record_id"]: source, identity_source["source_record_id"]: identity_source},
                    )
                )

    def test_statement_evidence_must_belong_to_candidate_taqrib_source(self):
        tables = input_tables()
        statement = tables["statements.csv"][0]
        candidate = next(row for row in tables["candidate_entries.csv"] if row["candidate_entry_id"] == statement["candidate_entry_id"])
        target_source_id = candidate["taqrib_source_record_id"]
        wrong_source_id = next(row["source_record_id"] for row in tables["sources.csv"] if row["source_record_id"] != target_source_id)
        statement.update({
            "statement_source_span_verbatim": "نص تجريبي",
            "statement_source_span_status": "transcribed",
            "statement_source_evidence_record_id": "EV-WRONG-SOURCE",
            "statement_source_locator": "synthetic locator",
        })
        tables["source_evidence.csv"].append({
            "evidence_record_id": "EV-WRONG-SOURCE",
            "source_record_id": wrong_source_id,
            "candidate_entry_id": "",
            "statement_id": statement["statement_id"],
            "attribution_link_id": "",
            "evidence_role": "passage_text",
            "evidence_text_verbatim": "نص تجريبي",
            "evidence_text_status": "transcribed",
            "source_locator": "synthetic locator",
        })
        with self.assertRaisesRegex(migration.MigrationError, "candidate's Taqrib source"):
            migration.validate_package_tables(tables)

    def test_staged_package_validator_rejects_broken_attribution_reference(self):
        tables = input_tables()
        tables["attribution_links.csv"][0]["statement_id"] = "MISSING-STATEMENT"
        with self.assertRaisesRegex(migration.MigrationError, "attribution_links.csv.*statement_id"):
            migration.validate_package_tables(tables)

    def test_staged_package_validator_rejects_bad_references_in_each_relation(self):
        mutations = (
            ("candidate_entries.csv", "audit_record_id", "MISSING-CASE"),
            ("statements.csv", "candidate_entry_id", "MISSING-CANDIDATE"),
            ("attribution_links.csv", "statement_id", "MISSING-STATEMENT"),
            ("sources.csv", "candidate_entry_id", "MISSING-CANDIDATE"),
            ("migration_mapping.csv", "candidate_entry_id", "MISSING-CANDIDATE"),
            ("legacy_v1_values.csv", "candidate_entry_id", "MISSING-CANDIDATE"),
        )
        for filename, field, bad_value in mutations:
            with self.subTest(filename=filename, field=field):
                tables = input_tables()
                tables[filename][0][field] = bad_value
                with self.assertRaises(migration.MigrationError):
                    migration.validate_package_tables(tables)

    def test_validator_rejects_broken_evidence_date_and_feature_references(self):
        cases = [
            ("source_evidence.csv", {
                "evidence_record_id": "EV-BAD", "source_record_id": "MISSING-SOURCE", "candidate_entry_id": "PROV-10-C01",
                "statement_id": "", "attribution_link_id": "", "evidence_role": "identity",
                "evidence_text_verbatim": "", "evidence_text_status": "not_assessed", "source_locator": "",
            }),
            ("date_claims.csv", {
                "date_claim_id": "DATE-BAD", "date_subject_role": "evaluator", "date_kind": "evaluator_lifespan_or_death",
                "date_value": "100", "date_calendar": "AH", "date_precision": "year",
                "date_claim_status": "recorded_in_source", "evidence_record_id": "MISSING-EVIDENCE",
            }),
            ("feature_sources.csv", {
                "feature_source_id": "FEAT-BAD", "statement_id": "PROV-10-C01-S00", "source_record_id": "MISSING-SOURCE",
                "feature_input_name": "biographical_text", "temporal_date_claim_id": "MISSING-DATE", "feature_inclusion_status": "excluded",
                "feature_exclusion_policy_id": "policy-test", "feature_exclusion_policy_version": "1", "decision_rationale": "Test-only fixture.",
            }),
        ]
        for filename, row in cases:
            with self.subTest(filename=filename):
                tables = input_tables()
                tables[filename].append(row)
                with self.assertRaises(migration.MigrationError):
                    migration.validate_package_tables(tables)

    def test_task_a_feature_firewall_rejects_direct_names_and_taqrib_sources(self):
        candidate, statement, attribution, source, identity_source, evidence = valid_grade_records()
        date_claim = {
            "date_claim_id": "DATE-TEST",
            "date_subject_role": "source_work",
            "date_kind": "source_work_composition_date",
            "date_value": "",
            "date_calendar": "",
            "date_precision": "",
            "date_claim_status": "unknown",
            "evidence_record_id": "",
        }
        sources = {source["source_record_id"]: source, identity_source["source_record_id"]: identity_source}
        statements = {statement["statement_id"]: statement}
        candidates = {candidate["candidate_entry_id"]: candidate}
        date_claims = {date_claim["date_claim_id"]: date_claim}

        def row(feature_name, source_id):
            return {
                "feature_source_id": f"FS-{feature_name}",
                "statement_id": statement["statement_id"],
                "source_record_id": source_id,
                "feature_input_name": feature_name,
                "temporal_date_claim_id": date_claim["date_claim_id"],
                "feature_inclusion_status": "included",
                "feature_exclusion_policy_id": "TASK-A-v1",
                "feature_exclusion_policy_version": "1.0",
                "decision_rationale": "Synthetic firewall regression fixture.",
            }

        for feature_name, source_id, message in (
            ("original_grade_field", identity_source["source_record_id"], "target-derived feature"),
            ("biographical_text", source["source_record_id"], "Taqrib target source"),
        ):
            with self.subTest(feature_name=feature_name):
                with self.assertRaisesRegex(migration.MigrationError, message):
                    migration.validate_feature_source_record(
                        row(feature_name, source_id),
                        statements=statements,
                        candidates=candidates,
                        sources=sources,
                        date_claims=date_claims,
                        evidence=evidence,
                    )

    def test_recorded_date_claim_has_its_own_temporal_evidence_link(self):
        tables = input_tables()
        source = tables["sources.csv"][0]
        source["source_verification_status"] = "verified_in_corpus"
        tables["source_evidence.csv"].append({
            "evidence_record_id": "EV-DATE-TEST",
            "source_record_id": source["source_record_id"],
            "candidate_entry_id": "",
            "statement_id": "",
            "attribution_link_id": "",
            "evidence_role": "temporal_date",
            "evidence_text_verbatim": "نص تاريخي منقول للفحص البنيوي",
            "evidence_text_status": "transcribed",
            "source_locator": "synthetic date locator",
        })
        tables["date_claims.csv"].append({
            "date_claim_id": "DATE-TEST",
            "date_subject_role": "source_work",
            "date_kind": "source_work_composition_date",
            "date_value": "300",
            "date_calendar": "AH",
            "date_precision": "year",
            "date_claim_status": "recorded_in_source",
            "evidence_record_id": "EV-DATE-TEST",
        })
        migration.validate_package_tables(tables)
        tables["date_claims.csv"][0]["evidence_record_id"] = "MISSING-DATE-EVIDENCE"
        with self.assertRaisesRegex(migration.MigrationError, "date_claims.csv.*evidence_record_id"):
            migration.validate_package_tables(tables)

    def test_temporal_eligibility_requires_linked_judgment_and_evaluator_dates(self):
        candidate, statement, attribution, source, identity_source, evidence = valid_grade_records()
        statement.update({
            "historical_input_eligibility": "eligible",
            "historical_input_eligibility_rationale": "Synthetic temporal-policy fixture.",
            "temporal_policy_id": "T_LE_365",
            "temporal_policy_version": "test-1",
            "temporal_policy_result": "passes_policy",
        })
        for claim_id, kind in (
            ("DATE-DEATH", "evaluator_lifespan_or_death"),
            ("DATE-JUDGMENT", "approximate_judgment_date"),
        ):
            evidence_id = f"EV-{claim_id}"
            evidence[evidence_id] = {
                "evidence_record_id": evidence_id,
                "source_record_id": identity_source["source_record_id"],
                "candidate_entry_id": "",
                "statement_id": statement["statement_id"],
                "attribution_link_id": "",
                "evidence_role": "temporal_date",
                "evidence_text_verbatim": f"SYNTHETIC DATE EVIDENCE {kind}",
                "evidence_text_status": "transcribed",
                "source_locator": f"Synthetic date locator {kind}",
            }
        claims = {
            "DATE-DEATH": {
                "date_claim_id": "DATE-DEATH", "date_subject_role": "evaluator", "date_kind": "evaluator_lifespan_or_death",
                "date_value": "200", "date_calendar": "AH", "date_precision": "year",
                "date_claim_status": "recorded_in_source", "evidence_record_id": "EV-DATE-DEATH",
            },
            "DATE-JUDGMENT": {
                "date_claim_id": "DATE-JUDGMENT", "date_subject_role": "judgement", "date_kind": "approximate_judgment_date",
                "date_value": "250", "date_calendar": "AH", "date_precision": "year",
                "date_claim_status": "recorded_in_source", "evidence_record_id": "EV-DATE-JUDGMENT",
            },
        }
        migration.validate_historical_input_decision(
            statement,
            date_claims=claims,
            evidence=evidence,
            sources={source["source_record_id"]: source, identity_source["source_record_id"]: identity_source},
        )
        claims.pop("DATE-JUDGMENT")
        with self.assertRaisesRegex(migration.MigrationError, "cannot rest on evaluator death alone"):
            migration.validate_historical_input_decision(
                statement,
                date_claims=claims,
                evidence=evidence,
                sources={source["source_record_id"]: source, identity_source["source_record_id"]: identity_source},
            )

    def test_broken_staged_join_fails_without_publishing_or_leaving_temp_files(self):
        original_build = migration._build_tables

        def broken_build(joined, source_metadata=None):
            tables = original_build(joined, source_metadata)
            tables["attribution_links.csv"][0]["statement_id"] = "MISSING-STATEMENT"
            return tables

        migration._build_tables = broken_build
        try:
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                output = root / "published"
                with self.assertRaises(migration.MigrationError):
                    migration.migrate_package(INPUT_DIR, output)
                self.assertFalse(output.exists())
                self.assertEqual(list(root.iterdir()), [])
        finally:
            migration._build_tables = original_build

    def test_manifest_contains_machine_readable_schema_and_column_mapping(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "published"
            manifest = migration.migrate_package(INPUT_DIR, output)
            self.assertIn("schema_field_registry.json", manifest["outputs_sha256"])
            self.assertIn("column_mapping.csv", manifest["outputs_sha256"])
            self.assertIn("column_mapping_file", manifest)
            self.assertIn("script_sha256", manifest)
            self.assertIn("implementation_version", manifest)
            for item in manifest["input_files"].values():
                self.assertIn("encoding", item)
                self.assertIn("row_count", item)
                self.assertIn("headers", item)
            mappings = read_csv(output / "column_mapping.csv")
            frozen_headers, _ = migration.read_csv(INPUT_DIR / migration.FROZEN_NAME)
            working_headers, _ = migration.read_csv(INPUT_DIR / migration.WORKING_NAME)
            for filename, headers in ((migration.FROZEN_NAME, frozen_headers), (migration.WORKING_NAME, working_headers)):
                mapped = {r["source_column"] for r in mappings if r["source_file"] == filename}
                self.assertEqual(mapped, set(headers))

    def test_schema_field_registry_covers_every_declared_output_column_and_enum(self):
        registry = migration.build_schema_field_registry()
        for table_name, columns in migration.OUTPUT_TABLES.items():
            self.assertEqual(set(registry["tables"][table_name]), set(columns))
        for enum_name, values in migration.FIELD_ENUMS.items():
            self.assertTrue(values, enum_name)
            self.assertIn(enum_name, registry["enums"])
            self.assertEqual(set(registry["enums"][enum_name]), set(values))
        output_columns = {field for columns in migration.OUTPUT_TABLES.values() for field in columns}
        for section_fields in migration.SPEC_INVENTORY_FIELDS.values():
            self.assertTrue(set(section_fields).issubset(output_columns))
        spec_text = (ROOT / "dataset_discovery/target_feasibility/MANUAL_COLLATION_SCHEMA_V2_2_FINAL.md").read_text(encoding="utf-8")
        enum_block = spec_text.split("### 3.1 Consolidated enum registry", 1)[1].split("#### Ordinary-grade target invariant", 1)[0]
        spec_enums = {}
        for line in enum_block.splitlines():
            match = re.match(r"\| `([^`]+)` \| (.+) \|$", line)
            if match:
                spec_enums[match.group(1)] = tuple(re.findall(r"`([^`]+)`", match.group(2)))
        self.assertEqual(spec_enums, migration.FIELD_ENUMS)
        for item in registry["fields"]:
            self.assertIn(item["field_type"], {"string", "enum", "integer", "nullable_integer", "date_or_range_text", "sha256_hex", "boolean"})
            self.assertIn("nullable", item)
            self.assertTrue(item["validation_rule"])

    def test_special_pilot_cases_remain_unassessed_and_roles_are_separate(self):
        tables = input_tables()
        candidates = tables["candidate_entries.csv"]
        statements = tables["statements.csv"]
        attributions = tables["attribution_links.csv"]
        sources = tables["sources.csv"]
        prov04 = [row for row in candidates if row["audit_record_id"] == "PROV-04"]
        self.assertEqual(len(prov04), 2)
        self.assertEqual(len({row["audit_record_id"] for row in prov04}), 1)
        self.assertEqual(len(tables["cases.csv"]), 10)
        self.assertEqual(migration.filter_analytical_rows(tables, "ordinary_grade_target"), [])

        for case_id in ("PROV-24", "PROV-51", "PROV-02", "PROV-10", "PROV-01"):
            case_statements = [row for row in statements if row["audit_record_id"] == case_id]
            self.assertTrue(case_statements)
            self.assertTrue(all(row["statement_record_status"] == "provisional_work_item" for row in case_statements))
        self.assertEqual(migration.FIELD_ENUMS["statement_type"][4], "specific_transmission_criticism")
        self.assertEqual(migration.FIELD_ENUMS["attribution_form"][2], "collective_attribution")
        self.assertEqual(migration.FIELD_ENUMS["target_task_scope"][1], "status_only_candidate")
        prov02_source = next(row for row in sources if row["candidate_entry_id"].startswith("PROV-02-"))
        self.assertEqual(prov02_source["edition_variant_status"], "not_assessed")
        self.assertEqual(prov02_source["edition_metadata_evidence_record_id"], "")
        prov10_statement = next(row for row in statements if row["audit_record_id"] == "PROV-10")
        self.assertEqual(prov10_statement["statement_text_verbatim"], "")
        self.assertFalse(any(row["surviving_wording_author"] == row.get("source_work_author_compiler") for row in attributions))
        self.assertNotIn("source_work_author_compiler", migration.OUTPUT_TABLES["attribution_links.csv"])
        self.assertIn("source_work_author_compiler", migration.OUTPUT_TABLES["sources.csv"])

    def test_prov01_status_only_scope_is_separate_from_text_support_and_ordinary_grade(self):
        tables = input_tables()
        candidate = next(row for row in tables["candidate_entries.csv"] if row["audit_record_id"] == "PROV-01")
        original = next(row for row in tables["statements.csv"] if row["candidate_entry_id"] == candidate["candidate_entry_id"])
        original["statement_record_status"] = "superseded_placeholder"
        statement = dict(original)
        statement_id = f"{candidate['candidate_entry_id']}-S01"
        synthetic_text = "SYNTHETIC TEST FIXTURE, not source text: Companion-status statement"
        statement.update({
            "statement_id": statement_id,
            "statement_record_status": "reviewed_statement",
            "statement_type": "descriptive_or_generational_status",
            "statement_text_verbatim": synthetic_text,
            "statement_text_status": "transcribed",
            "grade_base_text_status": "not_applicable",
            "grade_qualification_text_status": "not_applicable",
            "taqrib_rank_number": "1",
            "rank_status": "assigned",
            "taqrib_statement_validity": "supported_taqrib_statement",
            "target_task_scope": "status_only_candidate",
            "target_task_scope_rationale": "Synthetic status-only schema fixture.",
            "statement_source_correspondence": "exact",
            "statement_source_span_verbatim": synthetic_text,
            "statement_source_span_status": "transcribed",
            "statement_source_correspondence_rationale": "Synthetic source correspondence fixture.",
            "statement_source_locator": "Synthetic source locator.",
            "statement_source_evidence_record_id": "EV-STATUS-ONLY",
            "historical_input_eligibility": "not_applicable",
            "historical_input_eligibility_rationale": "Not a historical input feature.",
            "temporal_policy_id": "",
            "temporal_policy_version": "",
            "temporal_policy_result": "not_applicable",
        })
        tables["statements.csv"].append(statement)
        original_attribution = next(row for row in tables["attribution_links.csv"] if row["statement_id"] == original["statement_id"])
        attribution = dict(original_attribution)
        attribution.update({"statement_id": statement_id, "attribution_link_id": f"{statement_id}-A01"})
        tables["attribution_links.csv"].append(attribution)
        source = next(row for row in tables["sources.csv"] if row["candidate_entry_id"] == candidate["candidate_entry_id"])
        source["source_verification_status"] = "verified_in_corpus"
        tables["source_evidence.csv"].append({
            "evidence_record_id": "EV-STATUS-ONLY",
            "source_record_id": source["source_record_id"],
            "candidate_entry_id": "",
            "statement_id": statement_id,
            "attribution_link_id": "",
            "evidence_role": "passage_text",
            "evidence_text_verbatim": synthetic_text,
            "evidence_text_status": "transcribed",
            "source_locator": "Synthetic source locator.",
        })
        migration.validate_package_tables(tables)
        self.assertEqual(statement["taqrib_statement_validity"], "supported_taqrib_statement")
        self.assertEqual(statement["target_task_scope"], "status_only_candidate")
        self.assertNotEqual(statement["target_task_scope"], "ordinary_grade_candidate")
        self.assertEqual(migration.filter_analytical_rows(tables, "ordinary_grade_target"), [])

    def test_prov24_and_prov51_attributions_do_not_force_historical_route_or_grade(self):
        def reviewed_test_record(case_id, statement_type, passage_status, evaluator_status, evaluator_name, attribution_form):
            tables = input_tables()
            candidate = next(row for row in tables["candidate_entries.csv"] if row["audit_record_id"] == case_id)
            original_statement = next(row for row in tables["statements.csv"] if row["candidate_entry_id"] == candidate["candidate_entry_id"])
            original_statement["statement_record_status"] = "superseded_placeholder"
            statement = dict(original_statement)
            statement_id = f"{candidate['candidate_entry_id']}-S01"
            statement.update({
                "statement_id": statement_id,
                "statement_record_status": "reviewed_statement",
                "statement_type": statement_type,
                "statement_text_verbatim": "SYNTHETIC TEST FIXTURE, not source text",
                "statement_text_status": "transcribed",
                "grade_base_text_status": "not_applicable",
                "grade_qualification_text_status": "not_applicable",
                "rank_status": "unranked",
                "taqrib_statement_validity": "supported_taqrib_statement",
                "target_task_scope": "not_in_defined_task",
                "target_task_scope_rationale": "Synthetic structural test only.",
                "statement_source_correspondence": "exact",
                "statement_source_span_verbatim": "SYNTHETIC TEST FIXTURE, not source text",
                "statement_source_span_status": "transcribed",
                "statement_source_correspondence_rationale": "Synthetic structural test only.",
                "statement_source_locator": "synthetic locator",
                "statement_source_evidence_record_id": f"EV-{case_id}-STMT",
                "historical_input_eligibility": "not_assessed",
                "historical_input_eligibility_rationale": "No historical-input decision in this fixture.",
                "temporal_policy_id": "",
                "temporal_policy_version": "",
                "temporal_policy_result": "cannot_assess",
            })
            tables["statements.csv"].append(statement)
            original_attribution = next(row for row in tables["attribution_links.csv"] if row["statement_id"] == original_statement["statement_id"])
            attribution = dict(original_attribution)
            attribution["statement_id"] = statement_id
            attribution["attribution_link_id"] = f"{statement_id}-A01"
            attribution.update({
                "named_historical_evaluator": evaluator_name,
                "evaluator_value_status": evaluator_status,
                "surviving_wording_author": "",
                "wording_author_value_status": "not_assessed",
                "attribution_form": attribution_form,
                "passage_evaluator_naming_status": passage_status,
                "historical_evaluator_attribution_status": "explicitly_reported_but_historically_unverified",
                "transmission_route_status": "named_authority_route_unverified",
                "compiler_authorship_status": "not_assessed",
                "attribution_evidence_verbatim": "SYNTHETIC TEST FIXTURE, not source text",
                "attribution_evidence_text_status": "transcribed",
                "attribution_evidence_record_id": f"EV-{case_id}-ATTR",
                "attribution_evidence_locator": "synthetic locator",
            })
            tables["attribution_links.csv"].append(attribution)
            source = next(row for row in tables["sources.csv"] if row["candidate_entry_id"] == candidate["candidate_entry_id"])
            source["source_verification_status"] = "verified_in_corpus"
            source["edition_variant_status"] = "no_variant_marked"
            for suffix, owner_field, owner_id in (("STMT", "statement_id", statement_id), ("ATTR", "attribution_link_id", attribution["attribution_link_id"])):
                tables["source_evidence.csv"].append({
                    "evidence_record_id": f"EV-{case_id}-{suffix}",
                    "source_record_id": source["source_record_id"],
                    "candidate_entry_id": "",
                    "statement_id": owner_id if owner_field == "statement_id" else "",
                    "attribution_link_id": owner_id if owner_field == "attribution_link_id" else "",
                    "evidence_role": "passage_text",
                    "evidence_text_verbatim": "SYNTHETIC TEST FIXTURE, not source text",
                    "evidence_text_status": "transcribed",
                    "source_locator": "synthetic locator",
                })
            migration.validate_package_tables(tables)
            return tables, statement

        prov24, row24 = reviewed_test_record(
            "PROV-24", "attributed_earlier_critic_judgment", "explicit_individual_named", "identified", "al-Nasa'i", "explicit_attribution"
        )
        link24 = next(row for row in prov24["attribution_links.csv"] if row["statement_id"] == row24["statement_id"])
        self.assertEqual(link24["historical_evaluator_attribution_status"], "explicitly_reported_but_historically_unverified")
        self.assertEqual(link24["transmission_route_status"], "named_authority_route_unverified")
        self.assertEqual(row24["rank_status"], "unranked")

        prov51, row51 = reviewed_test_record(
            "PROV-51", "specific_transmission_criticism", "collective_only", "collective_unidentified", "", "collective_attribution"
        )
        self.assertEqual(row51["rank_status"], "unranked")
        self.assertEqual(row51["taqrib_rank_number"], "")
        self.assertEqual(row51["target_task_scope"], "not_in_defined_task")
        self.assertEqual(migration.filter_analytical_rows(prov51, "training"), [])

    def test_validator_rejects_invalid_enum_text_status_rank_and_edition_claim(self):
        mutations = (
            ("statements.csv", "target_task_scope", "probably_eligible"),
            ("statements.csv", "rank_status", "assigned"),
            ("candidate_entries.csv", "identity_evidence_text_status", "transcribed"),
            ("sources.csv", "edition_variant_status", "editorial_insertion_verified"),
        )
        for filename, field, value in mutations:
            with self.subTest(filename=filename, field=field):
                tables = input_tables()
                tables[filename][0][field] = value
                with self.assertRaises(migration.MigrationError):
                    migration.validate_package_tables(tables)

    def test_s00_and_text_replacement_are_excluded_from_analytical_rows(self):
        tables = input_tables()
        self.assertEqual(migration.filter_analytical_rows(tables, "statement_count"), [])
        tables["statements.csv"][0]["statement_text_verbatim"] = "عبارة أضيفت بعد إنشاء العنصر المؤقت"
        tables["statements.csv"][0]["statement_text_status"] = "transcribed"
        self.assertEqual(migration.filter_analytical_rows(tables, "statement_count"), [])
        self.assertEqual(migration.filter_analytical_rows(tables, "annotation_completion"), [])
        self.assertEqual(migration.filter_analytical_rows(tables, "training"), [])
        self.assertEqual(migration.filter_analytical_rows(tables, "evaluation"), [])
        self.assertEqual(migration.filter_analytical_rows(tables, "grade_distribution"), [])
        self.assertEqual(migration.annotation_completion_counts(tables), {"denominator": 0, "complete": 0})

    def test_reviewed_statement_requires_full_provenance_before_analysis(self):
        candidate, statement, attribution, source, identity_source, evidence = valid_grade_records()
        tables = input_tables()
        tables["cases.csv"] = [row for row in tables["cases.csv"] if row["audit_record_id"] != "PROV-10"]
        tables["candidate_entries.csv"] = [candidate]
        tables["statements.csv"] = [statement]
        tables["attribution_links.csv"] = [attribution]
        tables["sources.csv"] = [source, identity_source]
        tables["source_evidence.csv"] = list(evidence.values())
        tables["date_claims.csv"] = []
        tables["feature_sources.csv"] = []
        tables["migration_mapping.csv"] = []
        tables["legacy_v1_values.csv"] = []
        self.assertEqual(len(migration.filter_analytical_rows(tables, "training")), 1)
        statement["statement_record_status"] = "superseded_placeholder"
        self.assertEqual(migration.filter_analytical_rows(tables, "training"), [])

    def test_prov04_rejected_candidate_is_absent_from_target_extract(self):
        candidate, statement, attribution, source, identity_source, evidence = valid_grade_records()
        candidate.update({
            "audit_record_id": "PROV-04", "candidate_entry_id": "PROV-04-C01", "dataset_narrator_id": "278",
            "taqrib_source_record_id": "SRC-PROV04-ACCEPTED",
        })
        statement.update({"audit_record_id": "PROV-04", "candidate_entry_id": "PROV-04-C01", "statement_id": "PROV-04-C01-S01"})
        attribution.update({"statement_id": "PROV-04-C01-S01", "attribution_link_id": "PROV-04-C01-S01-A01"})
        source.update({"candidate_entry_id": "PROV-04-C01", "source_record_id": "SRC-PROV04-ACCEPTED"})
        identity_source.update({"candidate_entry_id": "PROV-04-C01", "source_record_id": "SRC-PROV04-BIO"})
        evidence["EV-IDENTITY"].update({"candidate_entry_id": "PROV-04-C01", "source_record_id": "SRC-PROV04-BIO"})
        evidence["EV-STATEMENT"].update({"statement_id": "PROV-04-C01-S01", "source_record_id": "SRC-PROV04-ACCEPTED"})
        evidence["EV-ATTRIBUTION"].update({"attribution_link_id": "PROV-04-C01-S01-A01", "source_record_id": "SRC-PROV04-ACCEPTED"})

        rejected_candidate = dict(candidate)
        rejected_candidate.update({
            "candidate_entry_id": "PROV-04-C02",
            "identity_match_status": "mismatch",
            "identity_evidence_verbatim": "",
            "identity_evidence_text_status": "not_assessed",
            "identity_evidence_record_id": "",
            "identity_evidence_locator": "",
            "identity_evidence_independence_rationale": "",
            "taqrib_source_record_id": "SRC-PROV04-REJECTED",
        })
        rejected_statement = dict(statement)
        rejected_statement.update({
            "candidate_entry_id": "PROV-04-C02",
            "statement_id": "PROV-04-C02-S01",
            "statement_source_evidence_record_id": "EV-PROV04-REJECTED-STMT",
        })
        rejected_attribution = dict(attribution)
        rejected_attribution.update({
            "statement_id": "PROV-04-C02-S01",
            "attribution_link_id": "PROV-04-C02-S01-A01",
            "attribution_evidence_record_id": "EV-PROV04-REJECTED-ATTR",
        })
        rejected_source = dict(source)
        rejected_source.update({"candidate_entry_id": "PROV-04-C02", "source_record_id": "SRC-PROV04-REJECTED"})
        rejected_evidence = [
            {
                **evidence["EV-STATEMENT"], "evidence_record_id": "EV-PROV04-REJECTED-STMT",
                "statement_id": "PROV-04-C02-S01",
            },
            {
                **evidence["EV-ATTRIBUTION"], "evidence_record_id": "EV-PROV04-REJECTED-ATTR",
                "attribution_link_id": "PROV-04-C02-S01-A01",
            },
        ]
        tables = {
            "candidate_entries.csv": [candidate, rejected_candidate],
            "statements.csv": [statement, rejected_statement],
            "attribution_links.csv": [attribution, rejected_attribution],
            "sources.csv": [source, identity_source, rejected_source],
            "source_evidence.csv": [*evidence.values(), *rejected_evidence],
        }

        prov04_candidates = [row for row in tables["candidate_entries.csv"] if row["audit_record_id"] == "PROV-04"]
        self.assertEqual(len(prov04_candidates), 2)
        self.assertEqual({row["audit_record_id"] for row in prov04_candidates}, {"PROV-04"})
        extracted = migration.filter_analytical_rows(tables, "training")
        self.assertEqual([row["candidate_entry_id"] for row in extracted], ["PROV-04-C01"])
        self.assertEqual({row["audit_record_id"] for row in extracted}, {"PROV-04"})

    def test_previous_derivative_is_unchanged_and_new_destination_is_distinct(self):
        manifest_path = PRIOR_OUTPUT / "manifest.json"
        checksum_path = PRIOR_OUTPUT / "MANIFEST.sha256"
        self.assertEqual(hashlib.sha256(manifest_path.read_bytes()).hexdigest(), PRIOR_MANIFEST_SHA256)
        self.assertEqual(hashlib.sha256(checksum_path.read_bytes()).hexdigest(), PRIOR_CHECKSUM_SHA256)
        self.assertNotEqual(migration.DEFAULT_OUTPUT_DIR, PRIOR_OUTPUT)
        self.assertIn("impl", migration.DEFAULT_OUTPUT_DIR.name)


if __name__ == "__main__":
    unittest.main()
