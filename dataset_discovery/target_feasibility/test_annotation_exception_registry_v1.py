import copy
import csv
import hashlib
import json
import unittest
from pathlib import Path

from annotation_exception_rules_v1 import (
    ExceptionRegistryError,
    inspect_exception_rules,
    load_exception_registry,
    validate_exception_registry,
)
from generate_annotation_proposals_v1 import build_proposals


ROOT = Path(__file__).resolve().parents[2]
TARGET_DIR = ROOT / "dataset_discovery" / "target_feasibility"
REGISTRY_PATH = TARGET_DIR / "annotation_rules" / "EXCEPTION_RULE_REGISTRY_V1.json"
SCHEMA_PATH = TARGET_DIR / "annotation_rules" / "EXCEPTION_RULE_SCHEMA_V1.json"
BASE_RULE_REGISTRY = TARGET_DIR / "ANNOTATION_AUTOMATION_RULE_REGISTRY_V1.csv"
PILOT_DIR = (
    ROOT
    / "data"
    / "2_interim"
    / "shamela4_narrator_audit"
    / "manual_annotation_working"
    / "manual_collation_pilot_10_review_round_1_working"
)
DRY_RUN_DIR = (
    ROOT
    / "data"
    / "2_interim"
    / "shamela4_narrator_audit"
    / "annotation_automation_v1_0_1_development_dry_run"
)


def read_dicts(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def verified_context():
    return {
        "candidate_identity_confirmed": True,
        "statement_span_human_confirmed": True,
        "source_text_verified": True,
    }


class TestAnnotationExceptionRegistryV1(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = load_exception_registry(REGISTRY_PATH)

    def test_registry_schema_and_version_are_valid_and_inactive(self):
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(schema["properties"]["schema_version"]["const"], "1.0")
        approval_schema = schema["$defs"]["exceptionRule"]["properties"]["approval"]
        guards = {
            guard["if"]["properties"]["status"]["const"]: guard["then"]["properties"]
            for guard in approval_schema["allOf"]
        }
        self.assertEqual(guards["not_approved"]["approved_by"]["type"], "null")
        self.assertEqual(guards["not_approved"]["approved_on"]["type"], "null")
        self.assertEqual(guards["not_approved"]["approval_reference"]["type"], "null")
        self.assertEqual(guards["approved"]["approved_by"]["type"], "string")
        self.assertEqual(guards["approved"]["approval_reference"]["type"], "string")
        registry_guards = {
            guard["if"]["properties"]["status"]["const"]: guard["then"]["properties"]["rules"]
            for guard in schema["allOf"]
        }
        self.assertEqual(registry_guards["inactive"]["items"]["properties"]["active"]["const"], False)
        self.assertEqual(registry_guards["active"]["minContains"], 1)
        self.assertIs(registry_guards["active"]["contains"]["properties"]["active"]["const"], True)
        self.assertEqual(self.registry["schema_version"], "1.0")
        self.assertEqual(self.registry["registry_version"], "1.0")
        self.assertEqual(self.registry["status"], "inactive")
        self.assertEqual(len(self.registry["rules"]), 5)
        self.assertTrue(all(rule["status"] == "proposed" for rule in self.registry["rules"]))
        self.assertTrue(all(rule["active"] is False for rule in self.registry["rules"]))
        self.assertTrue(all(rule["approval"]["status"] == "not_approved" for rule in self.registry["rules"]))
        self.assertTrue(all(rule["scope"]["target_eligibility"] == "not_assessed" for rule in self.registry["rules"]))
        validate_exception_registry(self.registry)

    def test_registry_rejects_activation_without_explicit_human_approval(self):
        registry = copy.deepcopy(self.registry)
        registry["status"] = "active"
        registry["rules"][0]["active"] = True
        registry["rules"][0]["status"] = "approved"
        with self.assertRaisesRegex(ExceptionRegistryError, "(?i)approval"):
            validate_exception_registry(registry)

    def test_inactive_registry_cannot_contain_an_active_rule(self):
        registry = copy.deepcopy(self.registry)
        rule = registry["rules"][0]
        rule["active"] = True
        rule["status"] = "approved"
        rule["approval"] = {
            "status": "approved",
            "approved_by": "reviewer-test",
            "approved_on": "2026-11-14",
            "approval_reference": "TEST-APPROVAL-001",
        }
        with self.assertRaisesRegex(ExceptionRegistryError, "Inactive registry"):
            validate_exception_registry(registry)

    def test_registry_activation_requires_a_complete_human_approval_record(self):
        registry = copy.deepcopy(self.registry)
        registry["status"] = "active"
        rule = registry["rules"][0]
        rule["active"] = True
        rule["status"] = "approved"
        rule["approval"] = {
            "status": "approved",
            "approved_by": "reviewer-test",
            "approved_on": "2026-11-14",
            "approval_reference": "TEST-APPROVAL-001",
        }
        validate_exception_registry(registry)

        for missing_field in ("approved_by", "approved_on", "approval_reference"):
            with self.subTest(missing_field=missing_field):
                incomplete = copy.deepcopy(registry)
                incomplete_rule = incomplete["rules"][0]
                incomplete_rule["approval"][missing_field] = None
                with self.assertRaisesRegex(ExceptionRegistryError, "Approval evidence"):
                    validate_exception_registry(incomplete)

    def test_not_approved_rule_cannot_carry_approval_metadata(self):
        registry = copy.deepcopy(self.registry)
        registry["rules"][0]["approval"] = {
            "status": "not_approved",
            "approved_by": "reviewer-test",
            "approved_on": "2026-11-14",
            "approval_reference": "TEST-APPROVAL-001",
        }
        with self.assertRaisesRegex(ExceptionRegistryError, "must be null"):
            validate_exception_registry(registry)

    def test_inactive_registry_is_a_noop_without_explicit_preview(self):
        base_result = {"proposed_taqrib_rank_number": "3", "rank_status": "assigned"}
        result = inspect_exception_rules(
            "ثقة له أفراد",
            self.registry,
            context=verified_context(),
            base_result=base_result,
        )
        self.assertEqual(result["status"], "inactive")
        self.assertEqual(result["matched_exception_ids"], [])
        self.assertEqual(result["proposed_actions"], [])
        self.assertFalse(result["actions_applied_to_generator"])
        self.assertEqual(result["base_result_before"], base_result)

    def test_exception_preview_requires_confirmed_identity_span_and_source(self):
        result = inspect_exception_rules(
            "ثقة له أفراد",
            self.registry,
            context={"candidate_identity_confirmed": True},
            base_result={"proposed_taqrib_rank_number": "3"},
            simulate_proposed=True,
        )
        self.assertEqual(result["status"], "preconditions_not_met")
        self.assertEqual(result["proposed_actions"], ["abstain_for_review"])
        self.assertEqual(result["simulated_effect"]["decision"], "abstain_for_review")

    def test_exception_triggers_do_not_match_as_substrings(self):
        result = inspect_exception_rules(
            "وقال وثقه النسائي في موضع آخر",
            self.registry,
            context=verified_context(),
            simulate_proposed=True,
        )
        self.assertEqual(result["status"], "no_match")
        self.assertEqual(result["matched_exception_ids"], [])
        self.assertEqual(result["proposed_actions"], [])

    def test_all_five_pilot_patterns_are_proposed_without_applying_actions(self):
        expected = {
            "ثقة له أفراد": (
                "EXC_PROV04_COMPOUND_THIQA_AFRAAD_001",
                ["suppress_base_match", "abstain_for_review"],
            ),
            "وثقه النسائي": (
                "EXC_PROV24_ATTRIBUTED_NASAI_001",
                ["suppress_base_match", "preserve_attributed_judgement", "abstain_for_review"],
            ),
            "صدوق اختلط في الآخر": (
                "EXC_PROV39_PRESERVE_IKHTILAT_QUALIFICATION_001",
                ["preserve_qualification"],
            ),
            "صحابي": (
                "EXC_PROV01_COMPANION_STATUS_001",
                ["suppress_base_match", "separate_status_from_reliability", "abstain_for_review"],
            ),
            "عابوا عليه أنه حدث عن أبيه بغير سماع": (
                "EXC_PROV51_SPECIFIC_TRANSMISSION_CRITICISM_001",
                ["suppress_base_match", "classify_specific_criticism", "abstain_for_review"],
            ),
        }
        for span, (exception_id, actions) in expected.items():
            with self.subTest(span=span):
                base_result = {"proposed_taqrib_rank_number": "3", "rank_status": "assigned"}
                result = inspect_exception_rules(
                    span,
                    self.registry,
                    context=verified_context(),
                    base_result=base_result,
                    simulate_proposed=True,
                )
                self.assertEqual(result["status"], "proposed_match")
                self.assertEqual(result["matched_exception_ids"], [exception_id])
                self.assertEqual(result["proposed_actions"], actions)
                self.assertFalse(result["actions_applied_to_generator"])
                self.assertEqual(result["base_result_before"], base_result)
                self.assertEqual(base_result["proposed_taqrib_rank_number"], "3")
                self.assertNotIn("rank_override", result)

    def test_compound_thiqa_exception_proposes_suppression_and_review(self):
        base_result = {
            "rule_id": "RANK_THIQA_EXACT_001",
            "proposed_taqrib_rank_number": "3",
            "rank_status": "assigned",
        }
        result = inspect_exception_rules(
            "ثقة له أفراد",
            self.registry,
            context=verified_context(),
            base_result=base_result,
            simulate_proposed=True,
        )
        self.assertEqual(result["simulated_effect"]["decision"], "abstain_for_review")
        self.assertTrue(result["simulated_effect"]["base_match_suppressed"])
        self.assertIsNone(result["simulated_effect"]["taqrib_rank_number"])
        self.assertEqual(result["base_result_before"], base_result)

    def test_prov39_preserves_rank_five_and_qualification_without_override(self):
        base_result = {
            "taqrib_rank_number": 5,
            "rank_status": "assigned",
            "qualification_verbatim": "اختلط في الآخر",
        }
        result = inspect_exception_rules(
            "صدوق اختلط في الآخر",
            self.registry,
            context=verified_context(),
            base_result=base_result,
            simulate_proposed=True,
        )
        self.assertEqual(result["simulated_effect"]["decision"], "preserve_base_result")
        self.assertEqual(result["simulated_effect"]["base_result"], base_result)
        self.assertEqual(result["base_result_before"], base_result)
        self.assertNotIn("rank_override", result["simulated_effect"])
        self.assertEqual(base_result["taqrib_rank_number"], 5)

    def test_companion_status_is_not_emitted_as_an_ordinary_reliability_rank(self):
        base_result = {"proposed_reliability_rank": 1, "target": "ordinary_reliability"}
        result = inspect_exception_rules(
            "صحابي",
            self.registry,
            context=verified_context(),
            base_result=base_result,
            simulate_proposed=True,
        )
        self.assertIn("separate_status_from_reliability", result["proposed_actions"])
        self.assertEqual(result["simulated_effect"]["decision"], "abstain_for_review")
        self.assertIsNone(result["simulated_effect"]["taqrib_rank_number"])
        self.assertEqual(result["base_result_before"], base_result)

    def test_attributed_judgement_and_specific_criticism_remain_unresolved(self):
        cases = [
            ("وثقه النسائي", "preserve_attributed_judgement"),
            ("عابوا عليه أنه حدث عن أبيه بغير سماع", "classify_specific_criticism"),
        ]
        for span, expected_action in cases:
            with self.subTest(span=span):
                result = inspect_exception_rules(
                    span,
                    self.registry,
                    context=verified_context(),
                    base_result={"historical_evaluator": "unresolved", "transmission_route": "unresolved"},
                    simulate_proposed=True,
                )
                self.assertIn(expected_action, result["proposed_actions"])
                self.assertEqual(result["simulated_effect"]["decision"], "abstain_for_review")
                self.assertEqual(result["base_result_before"]["historical_evaluator"], "unresolved")
                self.assertEqual(result["base_result_before"]["transmission_route"], "unresolved")

    def test_conflicting_matching_rules_fail_closed(self):
        registry = copy.deepcopy(self.registry)
        conflicting = copy.deepcopy(registry["rules"][0])
        conflicting["exception_id"] = "EXC_TEST_CONFLICT_001"
        conflicting["actions"] = ["preserve_qualification"]
        registry["rules"].append(conflicting)
        result = inspect_exception_rules(
            "ثقة له أفراد",
            registry,
            context=verified_context(),
            base_result={"proposed_taqrib_rank_number": "3"},
            simulate_proposed=True,
        )
        self.assertEqual(result["status"], "conflict_abstain")
        self.assertEqual(len(result["matched_exception_ids"]), 2)
        self.assertEqual(result["proposed_actions"], [])
        self.assertEqual(result["simulated_effect"]["decision"], "abstain_for_review")
        self.assertIsNone(result["simulated_effect"]["taqrib_rank_number"])

    def test_prov02_compound_span_has_no_exception_match_and_base_generator_abstains(self):
        compound_span = (
            "ثقة ثبت فاضل إلا أن في روايته عن ثابت والأعمش "
            "[وعاصم بن أبي النجود] وهشام ابن عروة شيئا وكذا فيما حدث به بالبصرة"
        )
        result = inspect_exception_rules(
            compound_span,
            self.registry,
            context=verified_context(),
            simulate_proposed=True,
        )
        self.assertEqual(result["status"], "no_match")
        self.assertEqual(result["proposed_actions"], [])

        candidates = read_dicts(PILOT_DIR / "candidate_entries.csv")
        statements = read_dicts(PILOT_DIR / "statements.csv")
        sources = read_dicts(PILOT_DIR / "sources.csv")
        evidence = read_dicts(PILOT_DIR / "source_evidence.csv")
        statements = [row for row in statements if row["statement_id"] == "PROV-02-C01-S01"]
        candidate_ids = {row["candidate_entry_id"] for row in statements}
        candidates = [row for row in candidates if row["candidate_entry_id"] in candidate_ids]
        source_ids = {row["taqrib_source_record_id"] for row in candidates}
        sources = [row for row in sources if row["source_record_id"] in source_ids]
        statement_ids = {row["statement_id"] for row in statements}
        evidence = [row for row in evidence if row["statement_id"] in statement_ids]
        proposal = build_proposals(candidates, statements, sources, evidence, read_dicts(BASE_RULE_REGISTRY))[0]
        self.assertEqual(proposal["proposal_status"], "abstain")
        self.assertEqual(proposal["abstention_reason"], "no_exact_enabled_rule_match")
        self.assertEqual(proposal["proposed_taqrib_rank_number"], "")

    def test_inactive_registry_does_not_change_existing_generator_output_or_review_files(self):
        input_rows = {
            name: read_dicts(PILOT_DIR / f"{name}.csv")
            for name in ("candidate_entries", "statements", "sources", "source_evidence")
        }
        recorded = read_dicts(DRY_RUN_DIR / "ANNOTATION_AUTO_PROPOSALS.csv")
        manifest = json.loads((DRY_RUN_DIR / "RUN_MANIFEST.json").read_text(encoding="utf-8"))
        output_path = DRY_RUN_DIR / "ANNOTATION_AUTO_PROPOSALS.csv"
        human_path = DRY_RUN_DIR / "HUMAN_REVIEW.csv"
        reviewed_input_path = DRY_RUN_DIR / "HUMAN_REVIEW_reviewed.csv"
        statements_path = PILOT_DIR / "statements.csv"
        before = {
            str(output_path): hashlib.sha256(output_path.read_bytes()).hexdigest(),
            str(human_path): hashlib.sha256(human_path.read_bytes()).hexdigest(),
            str(reviewed_input_path): hashlib.sha256(reviewed_input_path.read_bytes()).hexdigest(),
            str(statements_path): hashlib.sha256(statements_path.read_bytes()).hexdigest(),
        }
        proposals = build_proposals(
            input_rows["candidate_entries"],
            input_rows["statements"],
            input_rows["sources"],
            input_rows["source_evidence"],
            read_dicts(BASE_RULE_REGISTRY),
        )
        self.assertEqual(proposals, recorded)
        self.assertEqual(before[str(output_path)], manifest["output_sha256"][output_path.name])
        self.assertEqual(before[str(human_path)], manifest["output_sha256"][human_path.name])
        self.assertEqual(before[str(output_path)], hashlib.sha256(output_path.read_bytes()).hexdigest())
        self.assertEqual(before[str(human_path)], hashlib.sha256(human_path.read_bytes()).hexdigest())
        self.assertEqual(before[str(reviewed_input_path)], hashlib.sha256(reviewed_input_path.read_bytes()).hexdigest())
        self.assertEqual(before[str(statements_path)], hashlib.sha256(statements_path.read_bytes()).hexdigest())
        self.assertFalse(any(row["auto_accept"] != "false" for row in proposals))


if __name__ == "__main__":
    unittest.main()
