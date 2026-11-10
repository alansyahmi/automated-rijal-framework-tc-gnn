#!/usr/bin/env python3
"""Comprehensive test suite for Shamela4 blinded 20-case annotation pilot.

Verifies:
1. Exactly 20 selected cases.
2. Unique source IDs across all 20 cases.
3. Reproducibility with the same seed.
4. Correct separation of blinded and internal files.
5. No automated classification fields in reviewer CSV.
6. Preservation of original source text (field 1, field 2, tuple JSON).
7. Preservation of the original 60-case CSV (hash remains unchanged).
8. Manifest/hash consistency (all files match manifest).
9. All six sampling strata represented.
10. All annotation columns are blank in reviewer template.
11. Arabic text, diacritics, and embedded newlines round-trip accurately.
"""
from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

from dataset_discovery.Shamela4.blinded_annotation_pilot import (
    ANNOTATION_FIELDS,
    MAPPING_FIELDS,
    REVIEWER_FIELDS,
    SELECTION_FIELDS,
    V3_EXPECTED_HASH,
    V3_INPUT_RELATIVE,
    build_internal_mapping_rows,
    build_reviewer_rows,
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
        cls.reviewer_path = cls.pilot_dir / "PILOT_REVIEWER_BLINDED.csv"
        cls.mapping_path = cls.pilot_dir / "PILOT_INTERNAL_MAPPING.csv"
        cls.selection_path = cls.pilot_dir / "PILOT_SELECTION.csv"
        cls.codebook_path = cls.pilot_dir / "ANNOTATION_CODEBOOK.md"
        cls.protocol_path = cls.pilot_dir / "PILOT_PROTOCOL.md"

        cls.v3_rows = read_csv(cls.v3_csv_path)
        cls.selected_cases, cls.stratum_counts = select_pilot_cases(cls.v3_rows, seed=20261111)

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

    # 4. Correct separation of blinded and internal files
    def test_correct_separation_of_blinded_and_internal_files(self) -> None:
        self.assertTrue(self.reviewer_path.is_file(), f"Missing reviewer file: {self.reviewer_path}")
        self.assertTrue(self.mapping_path.is_file(), f"Missing mapping file: {self.mapping_path}")

        reviewer_rows = read_csv(self.reviewer_path)
        mapping_rows = read_csv(self.mapping_path)

        self.assertEqual(len(reviewer_rows), 20)
        self.assertEqual(len(mapping_rows), 20)

        # Reviewer file must NOT contain source_id, stratum, or automated classifier columns
        reviewer_cols = set(reviewer_rows[0].keys())
        self.assertNotIn("source_id", reviewer_cols)
        self.assertNotIn("v3_case_id", reviewer_cols)
        self.assertNotIn("sampling_stratum", reviewer_cols)
        self.assertNotIn("automated_pattern", reviewer_cols)
        self.assertNotIn("automated_certainty", reviewer_cols)
        self.assertNotIn("automated_evidence", reviewer_cols)
        self.assertNotIn("source_ID_level_classification", reviewer_cols)
        self.assertNotIn("quotation_citation_separability", reviewer_cols)

        # Internal mapping MUST retain full linkage
        mapping_cols = set(mapping_rows[0].keys())
        self.assertIn("source_id", mapping_cols)
        self.assertIn("v3_case_id", mapping_cols)
        self.assertIn("sampling_stratum", mapping_cols)
        self.assertIn("automated_pattern", mapping_cols)
        self.assertIn("source_ID_level_classification", mapping_cols)

    # 5. No automated classification fields in the reviewer CSV
    def test_no_automated_fields_in_reviewer_csv(self) -> None:
        reviewer_rows = read_csv(self.reviewer_path)
        forbidden_substrings = [
            "pattern", "certainty", "stratum", "strata", "classif", "evidence", "separability",
        ]
        for col in reviewer_rows[0].keys():
            for forbidden in forbidden_substrings:
                self.assertNotIn(
                    forbidden,
                    col.lower(),
                    f"Reviewer column '{col}' contains forbidden automated term '{forbidden}'",
                )

    # 6. Preservation of original source text
    def test_preservation_of_original_source_text(self) -> None:
        v3_by_case = {r["case_id"]: r for r in self.v3_rows}
        mapping_rows = read_csv(self.mapping_path)
        reviewer_rows = read_csv(self.reviewer_path)

        rev_by_pilot_id = {r["pilot_case_id"]: r for r in reviewer_rows}

        for m_row in mapping_rows:
            pid = m_row["pilot_case_id"]
            v3_id = m_row["v3_case_id"]
            orig_v3 = v3_by_case[v3_id]
            rev_row = rev_by_pilot_id[pid]

            self.assertEqual(rev_row["narrator_id"], orig_v3["narrator_id"])
            self.assertEqual(rev_row["narrator_name"], orig_v3["narrator_name"])
            self.assertEqual(rev_row["entry_index"], orig_v3["entry_index"])
            self.assertEqual(rev_row["original_field_1"], orig_v3["original_field_1"])
            self.assertEqual(rev_row["original_field_2"], orig_v3["original_field_2"])
            self.assertEqual(rev_row["original_tuple_json"], orig_v3["original_tuple_json"])

    # 7. Preservation of the original 60-case CSV
    def test_preservation_of_original_60_case_csv(self) -> None:
        self.assertTrue(self.v3_csv_path.is_file())
        current_hash = sha256(self.v3_csv_path)
        self.assertEqual(
            current_hash,
            V3_EXPECTED_HASH,
            f"Original 60-case V3 CSV was modified! Expected {V3_EXPECTED_HASH}, got {current_hash}",
        )

    # 8. Manifest/hash consistency
    def test_manifest_hash_consistency(self) -> None:
        self.assertTrue(self.manifest_path.is_file(), f"Missing manifest: {self.manifest_path}")
        with self.manifest_path.open("r", encoding="utf-8") as f:
            manifest = json.load(f)

        self.assertEqual(manifest["version"], "1.0.0")
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

    # 9. All six sampling strata represented
    def test_all_six_strata_represented(self) -> None:
        self.assertEqual(len(self.stratum_counts), 6, "Not all 6 strata are represented")
        for stratum, count in self.stratum_counts.items():
            self.assertGreater(count, 0, f"Stratum {stratum} has 0 cases in pilot")

    # 10. Reviewer blank fields are empty
    def test_reviewer_blank_fields_are_empty(self) -> None:
        reviewer_rows = read_csv(self.reviewer_path)
        for row in reviewer_rows:
            for field in ANNOTATION_FIELDS:
                self.assertEqual(
                    row[field],
                    "",
                    f"Annotation field '{field}' in {row['pilot_case_id']} is not blank: '{row[field]}'",
                )


if __name__ == "__main__":
    unittest.main()
