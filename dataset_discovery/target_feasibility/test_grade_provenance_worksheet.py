#!/usr/bin/env python3
"""Unit test suite for the 60-Record Ibn Hajar Grade Provenance Investigation package.

Tests verify:
  1. Row count: Exactly 60 records in the worksheet.
  2. Dataset distribution: Exactly 30 records from HadithDB and 30 from Shamela4.
  3. Unique identifiers: PROV-01 to PROV-60 without duplicates or collisions.
  4. Human fields blank: All 23 human review fields are strictly empty strings.
  5. Pre-populated integrity: All metadata and verbatim fields are non-empty and valid.
  6. Diagnostic flag representation: All 6 flags are boolean and represented by >= 10 records.
  7. Manifest consistency: File hashes, counts, and overlap metrics match the worksheet.
  8. Documentation presence: Codebook and Protocol files exist and document all fields.
  9. Reconciled taxonomy: Validates reconciled dispositions and attribution statuses.
  10. Intermediary promotion criteria: Verifies documented quarantine-to-eligibility rules.
  11. Sampling diversity: Verifies presence of pure descriptive, pure attributed, and non-overlap cases.
  12. Dash policy: Strictly ZERO em-dash (\\u2014) and ZERO en-dash (\\u2013) across all deliverables.
"""
import csv
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET_DIR = ROOT / "dataset_discovery" / "target_feasibility"
CSV_PATH = TARGET_DIR / "IBN_HAJAR_GRADE_PROVENANCE_WORKSHEET.csv"
MANIFEST_PATH = TARGET_DIR / "ibn_hajar_grade_provenance_manifest.json"
CODEBOOK_PATH = TARGET_DIR / "IBN_HAJAR_GRADE_PROVENANCE_CODEBOOK.md"
PROTOCOL_PATH = TARGET_DIR / "IBN_HAJAR_GRADE_PROVENANCE_PROTOCOL.md"
GENERATOR_PATH = TARGET_DIR / "generate_grade_provenance_worksheet.py"

FLAG_COLS = [
    "flag_conventional_grade",
    "flag_compound_qualified_grade",
    "flag_descriptive_non_grade",
    "flag_explicit_attributed_quote",
    "flag_criticism_text_overlap",
    "flag_ambiguous_truncated_editorial",
]

PREPOPULATED_COLS = [
    "audit_record_id",
    "dataset_name",
    "dataset_narrator_id",
    "dataset_narrator_name",
    "candidate_grade_field",
    "candidate_grade_verbatim",
    "candidate_grade_source_location",
    "flag_conventional_grade",
    "flag_compound_qualified_grade",
    "flag_descriptive_non_grade",
    "flag_explicit_attributed_quote",
    "flag_criticism_text_overlap",
    "flag_ambiguous_truncated_editorial",
    "diagnostic_flags_summary",
]

BLANK_HUMAN_COLS = [
    "taqrib_entry_number",
    "taqrib_printed_page",
    "taqrib_entry_name_verbatim",
    "taqrib_grade_verbatim",
    "taqrib_qualification_verbatim",
    "taqrib_rank_number",
    "taqrib_identity_match_status",
    "taqrib_text_match_status",
    "assessment_author",
    "assessment_attribution_status",
    "compiler_or_transmitter",
    "editorial_material_status",
    "attribution_evidence_verbatim",
    "source_locator",
    "source_verification_status",
    "textual_fidelity",
    "attribution_fidelity",
    "identity_fidelity",
    "record_disposition",
    "input_eligibility",
    "exclusion_or_quarantine_reason",
    "reviewer_notes",
    "corroboration_status",
]

EXPECTED_COLUMNS = PREPOPULATED_COLS + BLANK_HUMAN_COLS

RECONCILED_DISPOSITIONS = [
    "verified_ibn_hajar_assessment",
    "excluded_not_a_grade",
    "excluded_not_ibn_hajar",
    "excluded_editorial_material",
    "excluded_identity_mismatch",
    "excluded_textual_corruption",
    "quarantined_unattributed_synthesis",
    "quarantined_uncertain",
]


class TestGradeProvenanceWorksheet(unittest.TestCase):
    """Test suite for the 60-record Ibn Hajar grade provenance worksheet."""

    @classmethod
    def setUpClass(cls):
        if not CSV_PATH.is_file():
            raise FileNotFoundError(f"Missing worksheet CSV at {CSV_PATH}")
        with CSV_PATH.open(encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            cls.fieldnames = list(reader.fieldnames or [])
            cls.rows = list(reader)

        if not MANIFEST_PATH.is_file():
            raise FileNotFoundError(f"Missing manifest JSON at {MANIFEST_PATH}")
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    def test_worksheet_row_count(self):
        """Invariant 1: Exactly 60 records in the CSV."""
        self.assertEqual(len(self.rows), 60, "Worksheet must contain exactly 60 records.")

    def test_worksheet_column_schema(self):
        """Invariant 2: Exactly 37 columns matching expected schema."""
        self.assertEqual(len(self.fieldnames), 37, "Worksheet must contain exactly 37 columns.")
        self.assertEqual(self.fieldnames, EXPECTED_COLUMNS, "Column names and order must match specification.")

    def test_dataset_balance(self):
        """Invariant 3: Exactly 30 records from HadithDB and 30 from Shamela4."""
        hadithdb_rows = [r for r in self.rows if r["dataset_name"] == "HadithDB"]
        shamela_rows = [r for r in self.rows if r["dataset_name"] == "Shamela4"]
        self.assertEqual(len(hadithdb_rows), 30, "HadithDB must have exactly 30 records.")
        self.assertEqual(len(shamela_rows), 30, "Shamela4 must have exactly 30 records.")

    def test_unique_record_identifiers(self):
        """Invariant 4: PROV-01 to PROV-60 sequentially with zero duplicates."""
        ids = [r["audit_record_id"] for r in self.rows]
        self.assertEqual(len(ids), len(set(ids)), "All audit_record_id values must be unique.")
        expected_ids = [f"PROV-{i:02d}" for i in range(1, 61)]
        self.assertEqual(ids, expected_ids, "Identifiers must be PROV-01 through PROV-60.")

    def test_no_duplicate_narrator_ids_per_dataset(self):
        """Invariant 5: No duplicate narrator IDs within either dataset."""
        for ds_name in ["HadithDB", "Shamela4"]:
            ds_ids = [r["dataset_narrator_id"] for r in self.rows if r["dataset_name"] == ds_name]
            self.assertEqual(len(ds_ids), len(set(ds_ids)), f"Duplicate narrator IDs found in {ds_name}.")

    def test_human_fields_initially_blank(self):
        """Invariant 6: All 23 human review fields are strictly empty strings in every row."""
        for idx, row in enumerate(self.rows, start=1):
            for col in BLANK_HUMAN_COLS:
                val = row[col]
                self.assertEqual(
                    val,
                    "",
                    f"Row {idx} ({row['audit_record_id']}) has non-blank human review field '{col}': {val!r}",
                )

    def test_prepopulated_fields_non_empty(self):
        """Invariant 7: Pre-populated metadata fields are non-empty and valid."""
        for idx, row in enumerate(self.rows, start=1):
            for col in PREPOPULATED_COLS:
                val = row[col].strip()
                self.assertTrue(
                    len(val) > 0,
                    f"Row {idx} ({row['audit_record_id']}) has empty pre-populated field '{col}'.",
                )
            self.assertEqual(row["candidate_grade_field"], "الرتبة عند ابن حجر")

    def test_diagnostic_flags_valid_booleans(self):
        """Invariant 8: All flag columns contain either 'TRUE' or 'FALSE'."""
        for row in self.rows:
            for flag in FLAG_COLS:
                self.assertIn(
                    row[flag],
                    ["TRUE", "FALSE"],
                    f"Invalid flag value '{row[flag]}' for {flag} in {row['audit_record_id']}",
                )

    def test_flag_representation_coverage(self):
        """Invariant 9: Every diagnostic flag is represented by at least 10 records."""
        for flag in FLAG_COLS:
            count = sum(1 for r in self.rows if r[flag] == "TRUE")
            self.assertGreaterEqual(
                count,
                10,
                f"Flag {flag} has only {count} records, expected >= 10.",
            )

    def test_manifest_consistency_with_worksheet(self):
        """Invariant 10: Manifest sample statistics match worksheet values."""
        sample_stats = self.manifest.get("sample_statistics", {})
        self.assertEqual(sample_stats.get("sample_size"), 60)
        self.assertEqual(sample_stats.get("hadithdb_count"), 30)
        self.assertEqual(sample_stats.get("shamela_count"), 30)

        flag_rep = sample_stats.get("flag_representation", {})
        for flag in FLAG_COLS:
            ws_count = sum(1 for r in self.rows if r[flag] == "TRUE")
            mf_count = flag_rep.get(flag, {}).get("total_count")
            self.assertEqual(
                ws_count,
                mf_count,
                f"Count mismatch for {flag}: worksheet={ws_count}, manifest={mf_count}",
            )

    def test_reconciled_taxonomy_dispositions(self):
        """Invariant 11: Reconciled dispositions match in manifest and codebook."""
        manifest_dispositions = self.manifest.get("reconciled_taxonomy", {}).get("record_disposition_allowed_values", [])
        self.assertEqual(manifest_dispositions, RECONCILED_DISPOSITIONS)

        codebook_content = CODEBOOK_PATH.read_text(encoding="utf-8")
        for disp in RECONCILED_DISPOSITIONS:
            self.assertIn(disp, codebook_content, f"Disposition {disp} missing in codebook")

    def test_quarantine_to_eligibility_criteria_documented(self):
        """Invariant 12: Intermediary promotion criteria documented in manifest and codebook."""
        safeguards = self.manifest.get("methodological_safeguards", {}).get("safeguard_1_attribution_vs_textual_witness", {})
        self.assertIn("quarantine_to_eligibility_criteria", safeguards)
        self.assertEqual(len(safeguards["quarantine_to_eligibility_criteria"]), 4)

        codebook_content = CODEBOOK_PATH.read_text(encoding="utf-8")
        self.assertIn("Evidentiary Criteria to Move from Quarantine to Eligibility", codebook_content)

    def test_sampling_diversity_metrics(self):
        """Invariant 13: Manifest distinguishes allocated strata from row-level flag criteria."""
        sample_stats = self.manifest.get("sample_statistics", {})
        self.assertEqual(sample_stats.get("diagnostic_descriptive_without_conventional_grade_count"), 12)
        self.assertEqual(sample_stats.get("diagnostic_attributed_without_conventional_grade_count"), 12)
        self.assertEqual(sample_stats.get("uncomplicated_conventional_grade_baseline_count"), 16)
        self.assertEqual(sample_stats.get("strict_conventional_grade_baseline_without_criticism_overlap_count"), 10)
        uncomplicated_rows = [
            row for row in self.rows
            if row["flag_conventional_grade"] == "TRUE"
            and row["flag_compound_qualified_grade"] == "FALSE"
            and row["flag_descriptive_non_grade"] == "FALSE"
            and row["flag_explicit_attributed_quote"] == "FALSE"
            and row["flag_ambiguous_truncated_editorial"] == "FALSE"
        ]
        strict_rows = [row for row in uncomplicated_rows if row["flag_criticism_text_overlap"] == "FALSE"]
        self.assertEqual(len(uncomplicated_rows), 16)
        self.assertEqual(len(strict_rows), 10)
        allocated = sample_stats.get("primary_selection_category_counts", {}).get("combined", {})
        self.assertEqual(allocated.get("attributed_pure"), 6)
        self.assertEqual(allocated.get("descriptive_pure"), 6)
        self.assertEqual(allocated.get("uncomplicated_conventional_grade_baseline"), 8)
        self.assertGreaterEqual(sample_stats.get("non_overlap_with_criticism_text_count", 0), 10)

    def test_corroboration_enum_and_temporal_qualification(self):
        """Corroboration values and temporal limitations remain explicit."""
        allowed = [
            "independent_corroboration",
            "dependent_corroboration",
            "unresolved_corroboration",
        ]
        safeguard = self.manifest["methodological_safeguards"]["safeguard_1_attribution_vs_textual_witness"]
        self.assertEqual(safeguard["corroboration_status_allowed_values"], allowed)
        self.assertIn("corroboration_status", self.fieldnames)
        self.assertIn("provisional operational inclusion boundary", self.manifest["sampling_interpretation"]["design"] + " " + str(safeguard).lower())

    def test_sampling_scope_and_dimension_separation_documented(self):
        """The sample and independent verification decisions are not overinterpreted."""
        protocol = PROTOCOL_PATH.read_text(encoding="utf-8")
        self.assertIn("cannot estimate population prevalence", protocol)
        self.assertIn("critic's death", protocol)
        self.assertIn("witness date from work composition", protocol)
        self.assertIn("record_disposition` is a target-candidate disposition", protocol)
        firewall_spec = (TARGET_DIR / "PROVENANCE_AND_TEMPORAL_FIREWALL_SPEC.md").read_text(encoding="utf-8")
        for field in ["approximate_judgment_date", "source_work_date", "surviving_witness_date", "source_edition"]:
            self.assertIn(field, firewall_spec)

    def test_manifest_output_hashes_match_current_deliverables(self):
        """Every recorded deliverable hash matches its current file bytes."""
        expected_paths = {
            "worksheet_csv": CSV_PATH,
            "codebook_md": CODEBOOK_PATH,
            "protocol_md": PROTOCOL_PATH,
            "firewall_spec_md": TARGET_DIR / "PROVENANCE_AND_TEMPORAL_FIREWALL_SPEC.md",
            "generator_script_py": GENERATOR_PATH,
            "test_suite_py": TARGET_DIR / "test_grade_provenance_worksheet.py",
        }
        for key, path in expected_paths.items():
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(self.manifest["output_hashes"][key], digest, f"Hash mismatch for {key}")

    def test_documentation_files_present(self):
        """Invariant 14: Codebook and Protocol files exist and are non-empty."""
        self.assertTrue(CODEBOOK_PATH.is_file(), f"Missing {CODEBOOK_PATH}")
        self.assertGreater(CODEBOOK_PATH.stat().st_size, 1000, "Codebook is too small.")
        self.assertTrue(PROTOCOL_PATH.is_file(), f"Missing {PROTOCOL_PATH}")
        self.assertGreater(PROTOCOL_PATH.stat().st_size, 1000, "Protocol is too small.")

    def test_zero_forbidden_dashes_across_all_deliverables(self):
        """Invariant 15: Strictly ZERO em-dash (\\u2014) and ZERO en-dash (\\u2013)."""
        files_to_check = [
            CSV_PATH,
            MANIFEST_PATH,
            CODEBOOK_PATH,
            PROTOCOL_PATH,
            GENERATOR_PATH,
            Path(__file__),
        ]
        for fpath in files_to_check:
            content = fpath.read_text(encoding="utf-8")
            self.assertNotIn("\u2014", content, f"Forbidden em-dash (\\u2014) found in {fpath.name}")
            self.assertNotIn("\u2013", content, f"Forbidden en-dash (\\u2013) found in {fpath.name}")


if __name__ == "__main__":
    unittest.main()
