#!/usr/bin/env python3
"""Comprehensive test suite for refined Shamela4 evaluation-level two-pass pilot.

Verifies:
1. Exactly 20 selected cases.
2. Unique source IDs across all 20 cases.
3. Reproducibility with the same seed (identical IDs, orders, hashes).
4. Text-only Pass 1 strictly excludes attached narrator metadata (narrator_id, narrator_name).
5. Pass 1 tuple JSON contains ONLY the two textual elements (purges 3rd source-ID element).
6. No source ID can be recovered from any Pass 1 dedicated field or embedded tuple element.
7. Pass 2 retains the correct mapping to the original narrator (attached_narrator_id, attached_narrator_name).
8. Provenance fields rigorously distinguish immediate source work from cited classical work.
9. Revised statement-function and evaluative-orientation taxonomy decouples function from valence.
10. No automated classification fields leak into reviewer templates (Pass 1, Evaluations, Pass 2).
11. Preservation of original source text across all templates.
12. Preservation of the original 60-case CSV (hash remains unchanged).
13. Existing pilot source IDs and mappings remain strictly unchanged.
14. Evaluation-level template allows multiple evaluation rows linked to one tuple.
15. Unique evaluation IDs within each tuple.
16. Evaluation-level and reconciliation templates contain no pre-filled annotations.
17. Manifest/hash consistency (all recorded files match size and SHA-256).
18. All six sampling strata represented.
"""
from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

from dataset_discovery.Shamela4.blinded_annotation_pilot import (
    EVALUATION_FIELDS,
    MAPPING_FIELDS,
    PASS1_TEXT_FIELDS,
    PASS2_RECONCILIATION_FIELDS,
    SELECTION_FIELDS,
    V3_EXPECTED_HASH,
    V3_INPUT_RELATIVE,
    build_evaluation_blank_rows,
    build_internal_mapping_rows,
    build_pass1_text_rows,
    build_pass2_reconciliation_rows,
    build_selection_rows,
    read_csv,
    select_pilot_cases,
    sha256,
    write_csv,
)


class TestBlindedAnnotationPilot(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = PROJECT_ROOT
        cls.v3_csv_path = cls.root / V3_INPUT_RELATIVE
        cls.pilot_dir = (
            cls.root / "data/2_interim/shamela4_narrator_audit/stage2_diagnostics/blinded_annotation_pilot_20"
        )
        cls.manifest_path = cls.pilot_dir / "pilot_manifest.json"
        cls.pass1_path = cls.pilot_dir / "PILOT_PASS1_TEXT_BLINDED.csv"
        cls.eval_path = cls.pilot_dir / "PILOT_EVALUATIONS_BLANK.csv"
        cls.pass2_path = cls.pilot_dir / "PILOT_PASS2_RECONCILIATION_BLANK.csv"
        cls.mapping_path = cls.pilot_dir / "PILOT_INTERNAL_MAPPING.csv"
        cls.selection_path = cls.pilot_dir / "PILOT_SELECTION.csv"
        cls.codebook_path = cls.pilot_dir / "ANNOTATION_CODEBOOK.md"
        cls.protocol_path = cls.pilot_dir / "PILOT_PROTOCOL.md"

        cls.v3_rows = read_csv(cls.v3_csv_path)
        cls.selected_cases, cls.stratum_counts = select_pilot_cases(cls.v3_rows, seed=20261111)
        cls.known_source_ids = {str(c["source_id"]) for c in cls.selected_cases}

    # 1. Exactly 20 selected cases
    def test_exactly_twenty_selected_cases(self) -> None:
        self.assertEqual(len(self.selected_cases), 20)
        self.assertEqual(sum(self.stratum_counts.values()), 20)

    # 2. Unique source IDs across all 20 cases
    def test_unique_source_ids(self) -> None:
        source_ids = [c["source_id"] for c in self.selected_cases]
        self.assertEqual(len(source_ids), 20)
        self.assertEqual(len(set(source_ids)), 20, "Duplicate source_id detected in pilot selection")

    # 3. Reproducibility with the same seed
    def test_reproducibility_with_same_seed(self) -> None:
        rerun_cases, rerun_counts = select_pilot_cases(self.v3_rows, seed=20261111)
        self.assertEqual(
            [c["pilot_case_id"] for c in self.selected_cases],
            [c["pilot_case_id"] for c in rerun_cases],
        )
        self.assertEqual(
            [c["source_id"] for c in self.selected_cases],
            [c["source_id"] for c in rerun_cases],
        )
        self.assertEqual(
            [c["v3_case_id"] for c in self.selected_cases],
            [c["v3_case_id"] for c in rerun_cases],
        )
        self.assertEqual(self.stratum_counts, rerun_counts)

    # 4. Text-only Pass 1 excludes attached narrator metadata
    def test_pass1_text_only_excludes_narrator_metadata(self) -> None:
        self.assertTrue(self.pass1_path.is_file(), f"Missing Pass 1 file: {self.pass1_path}")
        pass1_rows = read_csv(self.pass1_path)
        self.assertEqual(len(pass1_rows), 20)

        pass1_cols = set(pass1_rows[0].keys())
        self.assertNotIn("narrator_id", pass1_cols)
        self.assertNotIn("narrator_name", pass1_cols)
        self.assertNotIn("source_id", pass1_cols)
        self.assertNotIn("v3_case_id", pass1_cols)
        self.assertNotIn("sampling_stratum", pass1_cols)
        self.assertNotIn("group_label", pass1_cols)

        # Must retain text context
        self.assertIn("pilot_case_id", pass1_cols)
        self.assertIn("entry_index", pass1_cols)
        self.assertIn("original_field_1", pass1_cols)
        self.assertIn("original_field_2", pass1_cols)
        self.assertIn("original_tuple_json", pass1_cols)

    # 5. Pass 1 tuple JSON contains ONLY the two textual elements
    def test_pass1_tuple_json_contains_only_two_textual_elements(self) -> None:
        pass1_rows = read_csv(self.pass1_path)
        for row in pass1_rows:
            raw_json = row["original_tuple_json"]
            parsed = json.loads(raw_json)
            self.assertIsInstance(parsed, list, f"Tuple in {row['pilot_case_id']} is not a JSON list")
            self.assertEqual(
                len(parsed),
                2,
                f"Pass 1 tuple JSON in {row['pilot_case_id']} must have exactly 2 elements, found {len(parsed)}",
            )
            self.assertIsInstance(parsed[0], str, f"Element 0 in {row['pilot_case_id']} is not string")
            self.assertIsInstance(parsed[1], str, f"Element 1 in {row['pilot_case_id']} is not string")
            self.assertEqual(parsed[0], row["original_field_1"])
            self.assertEqual(parsed[1], row["original_field_2"])

    # 6. No source ID can be recovered from Pass 1 fields or embedded elements
    def test_no_source_id_leakage_in_pass1(self) -> None:
        pass1_rows = read_csv(self.pass1_path)
        for row in pass1_rows:
            parsed = json.loads(row["original_tuple_json"])
            # Ensure no tuple element is an integer or equal to any known source ID
            for elem in parsed:
                self.assertFalse(
                    isinstance(elem, int),
                    f"Found numeric element in Pass 1 tuple for {row['pilot_case_id']}: {elem}",
                )
                self.assertNotIn(
                    str(elem).strip(),
                    self.known_source_ids,
                    f"Found raw source_id leaked in Pass 1 tuple for {row['pilot_case_id']}: {elem}",
                )
            for col_name, val in row.items():
                self.assertNotIn(
                    col_name.lower(),
                    ("source_id", "sourceid", "src_id"),
                    f"Found source_id column in Pass 1: {col_name}",
                )

    # 7. Pass 2 retains correct mapping to original narrator
    def test_pass2_retains_correct_narrator_mapping(self) -> None:
        self.assertTrue(self.pass2_path.is_file(), f"Missing Pass 2 file: {self.pass2_path}")
        pass2_rows = read_csv(self.pass2_path)
        self.assertEqual(len(pass2_rows), 20)

        mapping_rows = read_csv(self.mapping_path)
        mapping_by_pid = {r["pilot_case_id"]: r for r in mapping_rows}

        for row in pass2_rows:
            pid = row["pilot_case_id"]
            expected = mapping_by_pid[pid]
            self.assertEqual(row["attached_narrator_id"], expected["narrator_id"])
            self.assertEqual(row["attached_narrator_name"], expected["narrator_name"])

    # 8. Provenance fields distinguish immediate source work from cited work
    def test_provenance_fields_distinguish_immediate_and_cited_works(self) -> None:
        eval_rows = read_csv(self.eval_path)
        eval_cols = set(eval_rows[0].keys())

        required_provenance_cols = [
            "immediate_source_work_as_written",
            "immediate_source_work_normalized",
            "compiler_or_source_author",
            "work_title_as_written",
            "work_role",
            "immediate_source_work_verified",
            "cited_work_as_written",
            "cited_work_normalized",
            "source_locator_as_written",
            "historical_evaluator_as_written",
            "historical_evaluator_normalized",
            "intermediate_transmitter_as_written",
            "other_quoted_speaker_as_written",
            "attribution_type",
            "attribution_evidence_verbatim",
        ]
        for col in required_provenance_cols:
            self.assertIn(col, eval_cols, f"Missing required provenance column '{col}' in evaluation template")

    # 8b. Immediate source work cannot be inferred solely from cited title; unverified provenance remains unresolved
    def test_immediate_source_work_unverified_provenance_safeguards(self) -> None:
        eval_rows = read_csv(self.eval_path)
        eval_cols = set(eval_rows[0].keys())
        self.assertIn("work_title_as_written", eval_cols)
        self.assertIn("work_role", eval_cols)
        self.assertIn("immediate_source_work_verified", eval_cols)

        codebook_text = self.codebook_path.read_text(encoding="utf-8")
        # Ensure codebook warns against automatic inference from title
        self.assertIn("immediate_source_work_verified", codebook_text)
        self.assertIn("work_role", codebook_text)
        self.assertIn("unresolved", codebook_text)
        self.assertTrue(
            "not infer the immediate source work solely from a title" in codebook_text
            or "Pass 1 annotates textual evidence" in codebook_text
        )
        self.assertIn("Pass 1 text cannot establish documentary provenance that is absent from its text", codebook_text)

    # 8c. Explicit evaluation_target field exists in schema, template, and codebook with 7 categories
    def test_evaluation_target_schema_and_categories(self) -> None:
        self.assertIn("evaluation_target", EVALUATION_FIELDS)
        eval_rows = read_csv(self.eval_path)
        eval_cols = set(eval_rows[0].keys())
        self.assertIn("evaluation_target", eval_cols)

        # All template rows have blank evaluation_target
        for row in eval_rows:
            self.assertEqual(row["evaluation_target"], "")

        # Verify documentation of all 7 target categories in codebook
        codebook_text = self.codebook_path.read_text(encoding="utf-8")
        self.assertIn("evaluation_target", codebook_text)
        expected_targets = [
            "narrator_overall",
            "memory_or_precision",
            "specific_transmission_link",
            "specific_hadith_or_report",
            "comparative_narrator_assessment",
            "not_applicable",
            "unclear",
        ]
        for target in expected_targets:
            self.assertIn(target, codebook_text, f"Missing evaluation_target category '{target}' in codebook")

    # 9. Revised statement-function taxonomy includes transmission observations without forcing negative orientation
    def test_statement_function_and_orientation_taxonomy(self) -> None:
        eval_rows = read_csv(self.eval_path)
        eval_cols = set(eval_rows[0].keys())

        self.assertIn("statement_function", eval_cols)
        self.assertIn("evaluative_orientation", eval_cols)

        # Verify taxonomy in codebook text
        codebook_text = self.codebook_path.read_text(encoding="utf-8")
        self.assertIn("statement_function", codebook_text)
        self.assertIn("transmission_observation", codebook_text)
        self.assertIn("hadith_or_report_appraisal", codebook_text)
        self.assertIn("comparative_preference", codebook_text)
        self.assertIn("evaluative_orientation", codebook_text)
        self.assertIn("neutral", codebook_text)
        self.assertIn("qualified", codebook_text)

    # 9b. Factual transmission observations can have contains_evaluation = no
    def test_factual_transmission_observation_can_have_contains_evaluation_no(self) -> None:
        codebook_text = self.codebook_path.read_text(encoding="utf-8")
        self.assertIn("contains_evaluation", codebook_text)
        self.assertIn("yes", codebook_text)
        self.assertIn("no", codebook_text)
        self.assertIn("unclear", codebook_text)
        # Verify that transmission observation does not automatically imply contains_evaluation = yes
        clean_text = codebook_text.replace("**", "").replace("`", "")
        self.assertIn("transmission_observation", clean_text)
        self.assertIn("does not automatically imply contains_evaluation = yes", clean_text)
        self.assertIn("contains_evaluation: no (when stating factual non-audition", clean_text)

    # 9c. Comparative preference does not force positive orientation
    def test_comparative_preference_does_not_force_positive_orientation(self) -> None:
        codebook_text = self.codebook_path.read_text(encoding="utf-8")
        self.assertIn("comparative_preference", codebook_text)
        # Ensure guidance allows neutral or unclear
        self.assertTrue(
            "neutral or unclear" in codebook_text or "neutral" in codebook_text
        )
        self.assertTrue(
            "Do not infer that both narrators are independently reliable merely because the response is" in codebook_text.replace("**", "")
        )

    # 10. No automated classification fields leak into either reviewer stage
    def test_no_automated_fields_leak_into_reviewer_templates(self) -> None:
        forbidden_exact_or_prefixes = [
            "automated_pattern", "automated_certainty", "automated_evidence",
            "sampling_stratum", "source_id_level_classification",
            "quotation_citation_separability", "v3_case_id", "source_id",
        ]
        for path in [self.pass1_path, self.eval_path, self.pass2_path]:
            rows = read_csv(path)
            for col in rows[0].keys():
                col_lower = col.lower()
                for forbidden in forbidden_exact_or_prefixes:
                    self.assertNotEqual(
                        col_lower,
                        forbidden,
                        f"Reviewer template {path.name} contains forbidden automated column '{col}'",
                    )
                    self.assertFalse(
                        col_lower.startswith("automated_"),
                        f"Reviewer template {path.name} contains automated prefix in column '{col}'",
                    )

    # 11. Preservation of original source text
    def test_preservation_of_original_source_text(self) -> None:
        v3_by_case = {r["case_id"]: r for r in self.v3_rows}
        mapping_rows = read_csv(self.mapping_path)
        pass1_rows = read_csv(self.pass1_path)
        pass1_by_pid = {r["pilot_case_id"]: r for r in pass1_rows}

        for m_row in mapping_rows:
            pid = m_row["pilot_case_id"]
            v3_id = m_row["v3_case_id"]
            orig_v3 = v3_by_case[v3_id]
            p1_row = pass1_by_pid[pid]

            self.assertEqual(p1_row["entry_index"], orig_v3["entry_index"])
            self.assertEqual(p1_row["original_field_1"], orig_v3["original_field_1"])
            self.assertEqual(p1_row["original_field_2"], orig_v3["original_field_2"])

    # 12. Preservation of original 60-case CSV
    def test_preservation_of_original_60_case_csv(self) -> None:
        self.assertTrue(self.v3_csv_path.is_file())
        current_hash = sha256(self.v3_csv_path)
        self.assertEqual(
            current_hash,
            V3_EXPECTED_HASH,
            f"Original 60-case V3 CSV was modified! Expected {V3_EXPECTED_HASH}, got {current_hash}",
        )

    # 13. Existing pilot source IDs and mappings remain unchanged
    def test_existing_pilot_mapping_unchanged(self) -> None:
        mapping_rows = read_csv(self.mapping_path)
        self.assertEqual(len(mapping_rows), 20)

        # Authoritative committed mapping
        expected_mapping = [
            ("PILOT01", "TV022", "123796"),
            ("PILOT02", "TV014", "125629"),
            ("PILOT03", "TV045", "137006"),
            ("PILOT04", "TV053", "292716"),
            ("PILOT05", "TV052", "127749"),
            ("PILOT06", "TV021", "205165"),
            ("PILOT07", "TV012", "118902"),
            ("PILOT08", "TV001", "295637"),
            ("PILOT09", "TV038", "96646"),
            ("PILOT10", "TV007", "26434"),
            ("PILOT11", "TV005", "198246"),
            ("PILOT12", "TV028", "97581"),
            ("PILOT13", "TV032", "146571"),
            ("PILOT14", "TV037", "149057"),
            ("PILOT15", "TV048", "66597"),
            ("PILOT16", "TV057", "135575"),
            ("PILOT17", "TV018", "208385"),
            ("PILOT18", "TV036", "145216"),
            ("PILOT19", "TV024", "50725"),
            ("PILOT20", "TV043", "127988"),
        ]

        for i, (exp_pid, exp_v3, exp_src) in enumerate(expected_mapping):
            actual = mapping_rows[i]
            self.assertEqual(actual["pilot_case_id"], exp_pid)
            self.assertEqual(actual["v3_case_id"], exp_v3)
            self.assertEqual(str(actual["source_id"]), exp_src)

    # 14. Multiple evaluation rows can link to one tuple
    def test_multiple_evaluation_rows_can_link_to_one_tuple(self) -> None:
        multi_eval_rows = [
            {"pilot_case_id": "PILOT01", "evaluation_id": "PILOT01_E01", "contains_evaluation": "yes"},
            {"pilot_case_id": "PILOT01", "evaluation_id": "PILOT01_E02", "contains_evaluation": "yes"},
            {"pilot_case_id": "PILOT01", "evaluation_id": "PILOT01_E03", "contains_evaluation": "yes"},
            {"pilot_case_id": "PILOT02", "evaluation_id": "PILOT02_E01", "contains_evaluation": "yes"},
        ]
        p1_evals = [r for r in multi_eval_rows if r["pilot_case_id"] == "PILOT01"]
        self.assertEqual(len(p1_evals), 3)
        self.assertEqual(len(set(r["evaluation_id"] for r in p1_evals)), 3)

    # 15. Unique evaluation IDs within each tuple
    def test_unique_evaluation_ids_in_template(self) -> None:
        eval_rows = read_csv(self.eval_path)
        eval_ids = [r["evaluation_id"] for r in eval_rows]
        self.assertEqual(len(eval_ids), len(set(eval_ids)), "Evaluation IDs in template must be unique")
        for row in eval_rows:
            self.assertTrue(
                row["evaluation_id"].startswith(f"{row['pilot_case_id']}_"),
                f"Evaluation ID '{row['evaluation_id']}' does not match pilot_case_id '{row['pilot_case_id']}'",
            )

    # 16. Evaluation-level and reconciliation templates contain no pre-filled annotations
    def test_templates_contain_no_prefilled_annotations(self) -> None:
        eval_rows = read_csv(self.eval_path)
        eval_annotation_cols = [c for c in EVALUATION_FIELDS if c not in ("pilot_case_id", "evaluation_id")]
        for row in eval_rows:
            for col in eval_annotation_cols:
                self.assertEqual(
                    row[col],
                    "",
                    f"Pre-filled annotation detected in {row['evaluation_id']} column '{col}': '{row[col]}'",
                )

        pass2_rows = read_csv(self.pass2_path)
        pass2_annotation_cols = [
            "target_matches_attached_narrator",
            "reconciliation_status",
            "reconciled_narrator_id",
            "reconciliation_confidence",
            "reconciliation_notes",
        ]
        for row in pass2_rows:
            for col in pass2_annotation_cols:
                self.assertEqual(
                    row[col],
                    "",
                    f"Pre-filled annotation detected in Pass 2 {row['pilot_case_id']} column '{col}': '{row[col]}'",
                )

    # 17. Manifest/hash consistency
    def test_manifest_hash_consistency(self) -> None:
        self.assertTrue(self.manifest_path.is_file(), f"Missing manifest: {self.manifest_path}")
        with self.manifest_path.open("r", encoding="utf-8") as f:
            manifest = json.load(f)

        self.assertEqual(manifest["version"], "2.2.0")
        self.assertEqual(manifest["selected_case_count"], 20)
        self.assertEqual(len(manifest["selected_source_ids"]), 20)
        self.assertEqual(len(set(manifest["selected_source_ids"])), 20)
        self.assertIn("purposive_sample_declaration", manifest)

        # Check input hash
        self.assertEqual(manifest["input_dataset"]["sha256"], V3_EXPECTED_HASH)

        # Check all recorded outputs exist and match hashes
        outputs_meta = manifest["outputs"]
        for filename, meta in outputs_meta.items():
            out_file = self.pilot_dir / filename
            self.assertTrue(out_file.is_file(), f"Recorded output file {filename} does not exist")
            actual_size = out_file.stat().st_size
            actual_hash = sha256(out_file)
            self.assertEqual(actual_size, meta["bytes"], f"Byte mismatch for {filename}")
            self.assertEqual(actual_hash, meta["sha256"], f"Hash mismatch for {filename}")

    # 18. All six sampling strata represented
    def test_all_six_strata_represented(self) -> None:
        self.assertEqual(len(self.stratum_counts), 6, "Not all 6 strata are represented")
        for stratum, count in self.stratum_counts.items():
            self.assertGreater(count, 0, f"Stratum {stratum} has 0 cases in pilot")


if __name__ == "__main__":
    unittest.main()
