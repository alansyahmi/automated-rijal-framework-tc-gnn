import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from migrate_manual_collation_v2_2 import (
    EXPECTED_INPUT_HASHES,
    MigrationError,
    assert_unique_composite_keys,
    migrate_package,
    ordinary_grade_candidate_conditions_pass,
    write_csv_file,
)


ROOT = Path(__file__).resolve().parents[2]
INPUT_DIR = ROOT / "dataset_discovery" / "target_feasibility" / "manual_collation_pilot_10"


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class ManualCollationV22MigrationTests(unittest.TestCase):
    def test_all_four_pinned_inputs_match_the_frozen_baseline(self):
        for filename, expected in EXPECTED_INPUT_HASHES.items():
            with self.subTest(filename=filename):
                digest = hashlib.sha256((INPUT_DIR / filename).read_bytes()).hexdigest()
                self.assertEqual(digest, expected)

    def test_composite_join_rejects_duplicate_keys(self):
        key = ("PROV-04", 1, "entry text", (3076, 456, 5569))
        with self.assertRaisesRegex(MigrationError, "duplicate composite key"):
            assert_unique_composite_keys([key, key])

    def test_identity_mismatch_can_never_pass_ordinary_grade_invariant(self):
        candidate = {
            "identity_match_status": "mismatch",
            "candidate_field_source_correspondence": "exact",
            "candidate_comparison_source_span_status": "transcribed",
        }
        statement = {
            "statement_record_status": "reviewed_statement",
            "statement_text_status": "transcribed",
            "statement_type": "standardized_narrator_grade",
            "taqrib_statement_validity": "supported_taqrib_statement",
            "statement_source_correspondence": "exact",
            "taqrib_rank_number": "3",
            "rank_status": "assigned",
            "target_task_scope": "ordinary_grade_candidate",
        }
        attribution = {
            "surviving_wording_author": "Ibn Hajar",
            "wording_author_value_status": "identified",
            "compiler_authorship_status": "supported",
            "attribution_form": "compiler_synthesis",
        }
        source = {
            "source_verification_status": "verified_in_corpus",
            "edition_variant_status": "no_variant_marked",
        }
        self.assertFalse(ordinary_grade_candidate_conditions_pass(candidate, statement, attribution, source))

    def test_hash_mismatch_fails_before_output_or_staging(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "published"
            wrong_hashes = dict(EXPECTED_INPUT_HASHES)
            wrong_hashes["MANUAL_COLLATION_PILOT_10_WORKING.csv"] = "0" * 64
            with self.assertRaisesRegex(MigrationError, "hash mismatch"):
                migrate_package(INPUT_DIR, output, expected_hashes=wrong_hashes)
            self.assertFalse(output.exists())
            self.assertEqual(list(root.iterdir()), [])

    def test_migration_scaffolds_ten_cases_eleven_candidates_and_provisional_items(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "published"
            manifest = migrate_package(INPUT_DIR, output)

            cases = read_csv(output / "cases.csv")
            candidates = read_csv(output / "candidate_entries.csv")
            statements = read_csv(output / "statements.csv")
            legacy = read_csv(output / "legacy_v1_values.csv")

            self.assertEqual(len(cases), 10)
            self.assertEqual(len(candidates), 11)
            self.assertEqual(len(statements), 11)
            self.assertEqual(len({r["audit_record_id"] for r in cases}), 10)
            prov04 = [r for r in candidates if r["audit_record_id"] == "PROV-04"]
            self.assertEqual(len(prov04), 2)
            self.assertEqual([r["candidate_entry_id"] for r in prov04], ["PROV-04-C01", "PROV-04-C02"])
            self.assertEqual(len(legacy), 11 * 34 * 2)

            for statement in statements:
                self.assertEqual(statement["statement_record_status"], "provisional_work_item")
                self.assertEqual(statement["statement_type"], "not_assessed")
                self.assertEqual(statement["statement_text_status"], "not_transcribed")
                self.assertEqual(statement["statement_text_verbatim"], "")
                self.assertEqual(statement["taqrib_rank_number"], "")
                self.assertEqual(statement["rank_status"], "not_assessed")
                self.assertEqual(statement["taqrib_statement_validity"], "not_assessed")
                self.assertEqual(statement["target_task_scope"], "not_assessed")

            prov04_legacy_ranks = [
                row["legacy_value"]
                for row in legacy
                if row["audit_record_id"] == "PROV-04"
                and row["source_file"] == "MANUAL_COLLATION_PILOT_10_WORKING.csv"
                and row["field_name"] == "taqrib_rank_number"
            ]
            self.assertEqual(prov04_legacy_ranks, ["3", "6"])
            self.assertEqual(manifest["counts"]["cases"], 10)
            self.assertEqual(manifest["counts"]["candidate_entries"], 11)
            self.assertEqual(manifest["counts"]["provisional_work_items"], 11)
            self.assertEqual(
                manifest["status_counts"]["statements.csv"]["target_task_scope"],
                {"not_assessed": 11},
            )
            self.assertFalse(manifest["not_assessed_counts_are_decisions"])
            self.assertFalse(any(row["target_task_scope"] == "ordinary_grade_candidate" for row in statements))
            self.assertEqual(read_csv(output / "feature_sources.csv"), [])

            legacy_index = {
                (row["source_file"], int(row["input_row_index"]), row["field_name"]): row["legacy_value"]
                for row in legacy
            }
            for filename in ("MANUAL_COLLATION_PILOT_10.csv", "MANUAL_COLLATION_PILOT_10_WORKING.csv"):
                for row_index, source_row in enumerate(read_csv(INPUT_DIR / filename), start=1):
                    for field_name, value in source_row.items():
                        self.assertEqual(legacy_index[(filename, row_index, field_name)], value)

    def test_arabic_and_newlines_round_trip_and_original_inputs_are_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "published"
            before = {name: (INPUT_DIR / name).read_bytes() for name in EXPECTED_INPUT_HASHES}
            migrate_package(INPUT_DIR, output)
            candidates = read_csv(output / "candidate_entries.csv")
            self.assertTrue(any("قيس ابن حفص" in row["taqrib_entry_text_verbatim"] for row in candidates))
            legacy = read_csv(output / "legacy_v1_values.csv")
            after = {name: (INPUT_DIR / name).read_bytes() for name in EXPECTED_INPUT_HASHES}
            self.assertEqual(before, after)

    def test_arabic_and_embedded_newline_csv_round_trip(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "roundtrip.csv"
            original = [{"arabic": "هذا نص عربي، فيه ترقيم: ؛؟", "notes": 'line one, "quoted"\nالسطر الثاني: «قيس ابن حفص»'}]
            write_csv_file(path, original, ["arabic", "notes"])
            path.write_bytes(b"\xef\xbb\xbf" + path.read_bytes())
            self.assertEqual(read_csv(path), original)

    def test_manifest_excludes_self_hash_and_checksum_from_data_hashes(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "published"
            migrate_package(INPUT_DIR, output)
            manifest_path = output / "manifest.json"
            checksum_path = output / "MANIFEST.sha256"
            expected = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
            self.assertTrue(checksum_path.read_text(encoding="ascii").startswith(expected + "  "))
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            output_hashes = manifest["outputs_sha256"]
            self.assertNotIn("manifest.json", output_hashes)
            self.assertNotIn("MANIFEST.sha256", output_hashes)
            for filename, digest in output_hashes.items():
                self.assertEqual(hashlib.sha256((output / filename).read_bytes()).hexdigest(), digest)

    def test_identical_inputs_produce_byte_identical_packages(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = root / "first"
            second = root / "second"
            migrate_package(INPUT_DIR, first)
            migrate_package(INPUT_DIR, second)
            first_bytes = {p.name: p.read_bytes() for p in first.iterdir()}
            second_bytes = {p.name: p.read_bytes() for p in second.iterdir()}
            self.assertEqual(first_bytes, second_bytes)

    def test_existing_output_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "published"
            output.mkdir()
            marker = output / "user-file.txt"
            marker.write_text("keep", encoding="utf-8")
            with self.assertRaisesRegex(MigrationError, "already exists"):
                migrate_package(INPUT_DIR, output)
            self.assertEqual(marker.read_text(encoding="utf-8"), "keep")
            self.assertEqual(list(output.iterdir()), [marker])

    def test_validation_failure_cleans_only_its_staging_and_lock(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "published"
            def reject_staging(_stage, _tables):
                raise ValueError("deliberate validation error")

            with self.assertRaisesRegex(MigrationError, "staged package validation failed"):
                migrate_package(INPUT_DIR, output, validator=reject_staging)
            self.assertFalse(output.exists())
            self.assertEqual(list(Path(temp).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
