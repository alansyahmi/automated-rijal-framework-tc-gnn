import unittest

import migrate_manual_collation_v2_2_impl_2_2_2 as migration
import test_manual_collation_v2_2_hardening as fixtures


class ManualCollationV222AttributionTests(unittest.TestCase):
    def test_supported_compiler_synthesis_can_name_an_earlier_evaluator(self):
        candidate, statement, attribution, source, identity_source, evidence = fixtures.valid_grade_records()
        attribution.update(
            {
                "named_historical_evaluator": "al-Nasa'i",
                "evaluator_value_status": "identified",
                "attribution_form": "compiler_synthesis",
                "passage_evaluator_naming_status": "explicit_individual_named",
                "historical_evaluator_attribution_status": "explicitly_reported_but_historically_unverified",
                "transmission_route_status": "named_authority_route_unverified",
            }
        )
        self.assertTrue(
            migration.ordinary_grade_candidate_conditions_pass(
                candidate,
                statement,
                attribution,
                source,
                evidence_by_id=evidence,
                sources_by_id={source["source_record_id"]: source, identity_source["source_record_id"]: identity_source},
            )
        )

    def test_guard_still_requires_supported_compiler_authorship_and_resolved_form(self):
        for field, value in (
            ("compiler_authorship_status", "unresolved"),
            ("compiler_authorship_status", "not_assessed"),
            ("attribution_form", "explicit_attribution"),
            ("attribution_form", "unclear"),
            ("passage_evaluator_naming_status", "unclear"),
            ("passage_evaluator_naming_status", "explicit_individual_named"),
        ):
            with self.subTest(field=field, value=value):
                candidate, statement, attribution, source, identity_source, evidence = fixtures.valid_grade_records()
                attribution[field] = value
                if value == "explicit_individual_named":
                    attribution["named_historical_evaluator"] = ""
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

    def test_table_validator_accepts_synthesis_with_consistent_named_evaluator(self):
        tables = fixtures.input_tables()
        attribution = tables["attribution_links.csv"][0]
        candidate = next(
            row
            for row in tables["candidate_entries.csv"]
            if row["candidate_entry_id"] == next(
                statement["candidate_entry_id"]
                for statement in tables["statements.csv"]
                if statement["statement_id"] == attribution["statement_id"]
            )
        )
        source_id = candidate["taqrib_source_record_id"]
        attribution.update(
            {
                "named_historical_evaluator": "al-Nasa'i",
                "evaluator_value_status": "identified",
                "surviving_wording_author": "Ibn Hajar",
                "wording_author_value_status": "identified",
                "attribution_form": "compiler_synthesis",
                "passage_evaluator_naming_status": "explicit_individual_named",
                "historical_evaluator_attribution_status": "explicitly_reported_but_historically_unverified",
                "transmission_route_status": "named_authority_route_unverified",
                "compiler_authorship_status": "supported",
                "attribution_evidence_verbatim": "SYNTHETIC TEST FIXTURE, not source text",
                "attribution_evidence_text_status": "transcribed",
                "attribution_evidence_record_id": "EV-NAMED-SYNTHESIS",
                "attribution_evidence_locator": "synthetic locator",
            }
        )
        tables["source_evidence.csv"].append(
            {
                "evidence_record_id": "EV-NAMED-SYNTHESIS",
                "source_record_id": source_id,
                "candidate_entry_id": "",
                "statement_id": "",
                "attribution_link_id": attribution["attribution_link_id"],
                "evidence_role": "passage_text",
                "evidence_text_verbatim": "SYNTHETIC TEST FIXTURE, not source text",
                "evidence_text_status": "transcribed",
                "source_locator": "synthetic locator",
            }
        )

        migration.validate_package_tables(tables)


if __name__ == "__main__":
    unittest.main()
