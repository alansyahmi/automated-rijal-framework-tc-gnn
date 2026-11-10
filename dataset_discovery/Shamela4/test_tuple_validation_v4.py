#!/usr/bin/env python3
"""Comprehensive test suite for Shamela4 blinded validation package (v4).

Verifies:
- Stratum sizes (10 per stratum, total 60 cases across 6 strata)
- Source-ID uniqueness (60 distinct source IDs)
- Stable sampling with fixed seed (20261111)
- Exact CSV round-trip of Arabic text, diacritics, and embedded newlines
- Reviewer copy omits all automated/classifier fields and stratum labels
- Reviewer copy retains required context and leaves human annotation fields blank
- Separate key maps every case (TV001-TV060) correctly
- Overlap metrics (53 narrator IDs, 7 recurring, 19 group labels, 10/10 suffix variants)
- Unchanged output hashes for prior versions v1, v2, and v3
- Heuristic regression cases from v2/v3
"""
from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from dataset_discovery.Shamela4.tuple_validation_v4 import (
    HUMAN_FIELDS,
    KEY_FIELDS,
    REVIEWER_FIELDS,
    V1_EXPECTED_HASHES,
    V2_EXPECTED_HASHES,
    V3_EXPECTED_HASHES,
    classify_tuple,
    quotation_citation_separability,
    read_csv,
    sample_v4_cases,
    sha256,
    verify_prior_versions,
    write_csv,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class TestTupleValidationV4(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = PROJECT_ROOT
        cls.stage_dir = cls.root / "data/2_interim/shamela4_narrator_audit/stage2_diagnostics"
        cls.parquet_path = cls.root / "data/1_raw/Shamela4_Full_DB/_meta/narrators.parquet"
        cls.v2_class_path = cls.stage_dir / "forensic_verification_v2/VERIFIED_SOURCE_ID_CLASSIFICATION.csv"
        cls.v3_csv_path = cls.stage_dir / "forensic_verification_v3/TUPLE_MANUAL_VALIDATION.csv"
        cls.v4_dir = cls.stage_dir / "forensic_verification_v4"

        # Run sampling once for memory tests
        cls.selected, cls.pool_sizes, cls.selected_counts = sample_v4_cases(
            parquet_path=cls.parquet_path,
            v2_classification_path=cls.v2_class_path,
            seed=20261111,
            per_stratum=10,
        )

    # 1. Stratum sizes and count
    def test_stratum_sizes_and_total_count(self) -> None:
        self.assertEqual(len(self.selected), 60)
        self.assertEqual(len(self.selected_counts), 6)
        for stratum, count in self.selected_counts.items():
            self.assertEqual(count, 10, f"Stratum {stratum} count is {count}, expected 10")

    # 2. Source-ID uniqueness
    def test_source_id_uniqueness(self) -> None:
        source_ids = [r["source_id"] for r in self.selected]
        self.assertEqual(len(source_ids), 60)
        self.assertEqual(len(set(source_ids)), 60, "Found duplicate source_id in sample")

    # 3. Stable sampling with fixed seed
    def test_stable_sampling_with_fixed_seed(self) -> None:
        rerun_selected, _, _ = sample_v4_cases(
            parquet_path=self.parquet_path,
            v2_classification_path=self.v2_class_path,
            seed=20261111,
            per_stratum=10,
        )
        self.assertEqual(
            [r["source_id"] for r in self.selected],
            [r["source_id"] for r in rerun_selected],
        )
        self.assertEqual(
            [r["entry_index"] for r in self.selected],
            [r["entry_index"] for r in rerun_selected],
        )
        self.assertEqual(
            [r["first"] for r in self.selected],
            [r["first"] for r in rerun_selected],
        )

    # 4. Exact CSV round-trip with Arabic text and embedded newlines
    def test_exact_csv_round_trip_arabic_and_newlines(self) -> None:
        tmp_csv = self.stage_dir / "_temp_roundtrip_test.csv"
        try:
            write_csv(tmp_csv, self.selected, ["source_id", "first", "second", "group_label", "narrator_name"])
            roundtrip_rows = read_csv(tmp_csv)
            self.assertEqual(len(roundtrip_rows), len(self.selected))

            newline_count = 0
            for orig, loaded in zip(self.selected, roundtrip_rows):
                self.assertEqual(orig["source_id"], loaded["source_id"])
                self.assertEqual(orig["first"], loaded["first"])
                self.assertEqual(orig["second"], loaded["second"])
                self.assertEqual(orig["group_label"], loaded["group_label"])
                self.assertEqual(orig["narrator_name"], loaded["narrator_name"])
                if "\n" in orig["second"]:
                    newline_count += 1
                    self.assertIn("\n", loaded["second"])
                    self.assertEqual(orig["second"].count("\n"), loaded["second"].count("\n"))

            self.assertGreater(newline_count, 15, "Expected multiple rows with embedded newlines")
        finally:
            if tmp_csv.is_file():
                tmp_csv.unlink()

    # 5. Reviewer copy structure (blinded, omits classifier and stratum fields, retains context, blank human fields)
    def test_reviewer_copy_structure(self) -> None:
        reviewer_csv_path = self.v4_dir / "TUPLE_MANUAL_VALIDATION_REVIEWER.csv"
        if not reviewer_csv_path.is_file():
            # If not yet generated on disk, test in-memory construction
            from dataset_discovery.Shamela4.tuple_validation_v4 import main
            main()

        rows = read_csv(reviewer_csv_path)
        self.assertEqual(len(rows), 60)

        with reviewer_csv_path.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.reader(stream)
            header = next(reader)

        self.assertEqual(header, REVIEWER_FIELDS)

        # Confirm omissions
        forbidden_fields = [
            "sampling_stratum",
            "automated_pattern",
            "automated_certainty",
            "automated_evidence",
            "source_ID_level_classification",
            "quotation_citation_separability",
        ]
        for f in forbidden_fields:
            self.assertNotIn(f, header, f"Forbidden classifier/stratum field {f!r} found in reviewer header")

        # Confirm all human fields are blank
        for r in rows:
            for hf in HUMAN_FIELDS:
                self.assertEqual(r[hf], "", f"Expected blank human field {hf!r} in case {r['case_id']}")
            # Context fields are populated
            self.assertTrue(r["case_id"].startswith("TV"))
            self.assertTrue(r["source_id"].isdigit())
            self.assertTrue(len(r["original_field_1"]) > 0)
            self.assertTrue(len(r["original_field_2"]) > 0)
            parsed_tuple = json.loads(r["original_tuple_json"])
            self.assertEqual(len(parsed_tuple), 3)

    # 6. Separate internal key maps every case correctly
    def test_key_maps_every_case_correctly(self) -> None:
        reviewer_csv_path = self.v4_dir / "TUPLE_MANUAL_VALIDATION_REVIEWER.csv"
        key_csv_path = self.v4_dir / "TUPLE_VALIDATION_KEY.csv"

        reviewer_rows = read_csv(reviewer_csv_path)
        key_rows = read_csv(key_csv_path)

        self.assertEqual(len(key_rows), 60)

        with key_csv_path.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.reader(stream)
            key_header = next(reader)

        self.assertEqual(key_header, KEY_FIELDS)

        key_by_case = {r["case_id"]: r for r in key_rows}
        for r_row in reviewer_rows:
            cid = r_row["case_id"]
            self.assertIn(cid, key_by_case)
            k_row = key_by_case[cid]
            self.assertEqual(r_row["source_id"], k_row["source_id"])
            self.assertEqual(r_row["narrator_id"], k_row["narrator_id"])
            self.assertEqual(r_row["group_label"], k_row["group_label"])
            self.assertEqual(r_row["entry_index"], k_row["entry_index"])
            self.assertTrue(len(k_row["sampling_stratum"]) > 0)
            self.assertTrue(len(k_row["automated_pattern"]) > 0)
            self.assertTrue(len(k_row["automated_certainty"]) > 0)

    # 7. Overlap metrics and limits in report
    def test_overlap_metrics_and_limitations(self) -> None:
        from collections import Counter

        narrator_counts = Counter(r["narrator_id"] for r in self.selected)
        group_counts = Counter(r["group_label"] for r in self.selected)
        recurring_nids = {k: v for k, v in narrator_counts.items() if v > 1}

        self.assertEqual(len(narrator_counts), 53)
        self.assertEqual(len(recurring_nids), 7)
        for nid, count in recurring_nids.items():
            self.assertEqual(count, 2, f"Narrator {nid} count is {count}, expected 2")

        self.assertEqual(len(group_counts), 19)

        # Formatting stratum checks
        fmt_rows = [r for r in self.selected if r["sampling_stratum"] == "suffix_format_validation_only"]
        self.assertEqual(len(fmt_rows), 10)
        suffix_matches = [r for r in fmt_rows if "بدون ترقيم" in r["first"] + r["second"]]
        self.assertEqual(len(suffix_matches), 10, "All 10 formatting cases must be بدون ترقيم variants")
        self.assertEqual(self.pool_sizes["suffix_format_validation_only"], 12)

        # Check overlap report text
        report_path = self.v4_dir / "OVERLAP_REPORT.md"
        report_text = report_path.read_text(encoding="utf-8")
        self.assertIn("بدون ترقيم", report_text)
        self.assertIn("12 eligible", report_text)
        self.assertIn("suffix-format", report_text.lower())
        self.assertIn("observed strings do not establish work identity", report_text.lower())
        self.assertIn("independent cases", report_text.lower())
        self.assertIn("tuple interpretation", report_text.lower())

    # 8. Unchanged hashes for v1, v2, v3
    def test_unchanged_v1_v2_v3_hashes(self) -> None:
        verifications = verify_prior_versions(self.stage_dir)
        self.assertEqual(set(verifications.keys()), {"v1", "v2", "v3"})
        for v_name, files in verifications.items():
            for fname, meta in files.items():
                self.assertTrue(meta["verified"], f"Integrity check failed for {v_name}/{fname}")

    # 9. Regressions from v2/v3
    def test_suffix_category_has_suffix_specific_separability_metadata(self) -> None:
        self.assertEqual(
            quotation_citation_separability("unnumbered_suffix_variant_without_reversal_evidence"),
            "suffix_occurrences_are_locator_variants; other tuples under this ID may differ",
        )

    def test_arabic_prose_cues_precede_secondary_locator(self) -> None:
        result = classify_tuple(
            "سنن البيهقي الكبرى: (7/ 318) برقم: (14987)",
            "وقال أبو عمرو بن العلاء كان يعاب على قتادة، وعمرو بن شعيب أنهما كانا لا يسمعان شيئا إلا حدثا به\nتهذيب التهذيب (3/ 277)",
        )
        self.assertEqual(result["pattern"], "citation_only_then_locator_bearing_prose")

    def test_citation_only_pair_is_not_prose(self) -> None:
        result = classify_tuple(
            "صحيح ابن خزيمة: (1/ 470) (بدون ترقيم)",
            "صحيح ابن خزيمة (1/ 470) (بدون ترقيم)",
        )
        self.assertEqual(result["pattern"], "citation_only_pair")

    def test_compound_multiline_citation_and_commentary_is_not_reversal(self) -> None:
        result = classify_tuple(
            "أشعث بن إسحاق أسقطه أحمد بن صالح حين حدثنا به، فحدثني به عنه موسى بن سهل الرملي",
            "سنن أبي داود (3/ 45) برقم (2775) \nسمعت عبدان الأهوازي يقول سمعت أبا داود السجستاني يقول أحمد بن صالح ليس هو كما يتوهم الناس، يعني ليس بذلك في الجلالة. \nالكامل في الضعفاء (1/ 295)",
        )
        self.assertEqual(result["pattern"], "prose_then_locator_bearing_commentary")

    def test_unrecognised_prose_pattern_remains_unresolved(self) -> None:
        result = classify_tuple(
            "المنتقى: (1/ 143) برقم: (396)",
            "صدوق اختلف قول ابن معين فيه\nالكاشف في معرفة من له رواية في الكتب الستة (2/ 117)",
        )
        self.assertEqual(result["pattern"], "unresolved_tuple_structure")


if __name__ == "__main__":
    unittest.main()
