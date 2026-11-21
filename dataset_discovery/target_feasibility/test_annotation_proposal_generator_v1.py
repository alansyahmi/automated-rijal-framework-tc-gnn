import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from generate_annotation_proposals_v1 import (
    PreflightError,
    build_proposals,
    read_csv as read_generated_csv,
    run_pipeline,
)


ROOT = Path(__file__).resolve().parents[2]
TARGET_DIR = ROOT / "dataset_discovery" / "target_feasibility"
REGISTRY = TARGET_DIR / "ANNOTATION_AUTOMATION_RULE_REGISTRY_V1.csv"
PILOT_DIR = (
    ROOT
    / "data"
    / "2_interim"
    / "shamela4_narrator_audit"
    / "manual_annotation_working"
    / "manual_collation_pilot_10_review_round_1_working"
)


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def input_paths(directory):
    return {
        "candidate_entries": directory / "candidate_entries.csv",
        "statements": directory / "statements.csv",
        "sources": directory / "sources.csv",
        "source_evidence": directory / "source_evidence.csv",
        "working_manifest": directory / "WORKING_COPY_MANIFEST.json",
    }


def tiny_packet(directory, text="ثقة", *, identity="confirmed", source_status="verified_in_corpus"):
    directory.mkdir(parents=True, exist_ok=True)
    candidates = [
        {
            "audit_record_id": "DEV-01",
            "candidate_entry_id": "DEV-01-C01",
            "dataset_narrator_id": "N-01",
            "dataset_narrator_name": "اسم الراوي",
            "identity_match_status": identity,
            "candidate_entry_text_status": "transcribed",
            "candidate_field_source_correspondence": "exact",
            "taqrib_source_record_id": "SRC-01",
            "taqrib_entry_text_verbatim": text,
        }
    ]
    statements = [
        {
            "audit_record_id": "DEV-01",
            "candidate_entry_id": "DEV-01-C01",
            "statement_id": "DEV-01-C01-S01",
            "statement_record_status": "reviewed_statement",
            "statement_text_verbatim": text,
            "statement_text_status": "transcribed",
            "taqrib_statement_validity": "supported_taqrib_statement",
            "statement_source_correspondence": "exact",
            "statement_source_span_verbatim": text,
            "statement_source_span_status": "transcribed",
            "statement_source_locator": "Taqrib p. 1, entry 1",
            "statement_source_evidence_record_id": "EV-01",
        }
    ]
    sources = [
        {
            "source_record_id": "SRC-01",
            "candidate_entry_id": "DEV-01-C01",
            "source_work_id": "3076",
            "source_verification_status": source_status,
            "source_locator_verbatim": "Taqrib p. 1, entry 1",
        }
    ]
    evidence = [
        {
            "evidence_record_id": "EV-01",
            "source_record_id": "SRC-01",
            "candidate_entry_id": "DEV-01-C01",
            "statement_id": "DEV-01-C01-S01",
            "evidence_role": "passage_text",
            "evidence_text_verbatim": text,
            "evidence_text_status": "transcribed",
            "source_locator": "Taqrib p. 1, entry 1",
        }
    ]
    tables = {
        "candidate_entries.csv": candidates,
        "statements.csv": statements,
        "sources.csv": sources,
        "source_evidence.csv": evidence,
    }
    for name, rows in tables.items():
        with (directory / name).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
    manifest = {
        "fixture": True,
        "source_packet_manifest_sha256": "fixture-source-manifest",
        "files": {
            name: {
                "bytes": (directory / name).stat().st_size,
                "sha256": hashlib.sha256((directory / name).read_bytes()).hexdigest(),
            }
            for name in tables
        },
    }
    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    (directory / "WORKING_COPY_MANIFEST.json").write_bytes(manifest_bytes)
    (directory / "WORKING_COPY_MANIFEST.sha256").write_text(
        f"{hashlib.sha256(manifest_bytes).hexdigest()} *WORKING_COPY_MANIFEST.json\n", encoding="ascii"
    )
    return input_paths(directory)


class TestAnnotationProposalGeneratorV1(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry_rows = read_csv(REGISTRY)

    def temp_dir(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        return Path(temp.name)

    def test_only_three_exact_rank_rules_propose(self):
        phrases = {
            "ثقة": ("RANK_THIQA_EXACT_001", "3"),
            "صدوق يخطىء": ("RANK_SADUQ_ERROR_EXACT_001", "5"),
            "صدوق اختلط في الآخر": ("RANK_SADUQ_IKHTILAT_EXACT_001", "5"),
        }
        for text, (rule_id, rank) in phrases.items():
            with self.subTest(text=text):
                inputs = tiny_packet(self.temp_dir(), text)
                rows = {name: read_csv(path) for name, path in inputs.items() if path.suffix == ".csv"}
                proposals = build_proposals(
                    rows["candidate_entries"],
                    rows["statements"],
                    rows["sources"],
                    rows["source_evidence"],
                    self.registry_rows,
                )
                self.assertEqual(len(proposals), 1)
                self.assertEqual(proposals[0]["proposal_status"], "proposed_for_human_review")
                self.assertEqual(proposals[0]["rule_id"], rule_id)
                self.assertEqual(proposals[0]["proposed_taqrib_rank_number"], rank)
                self.assertEqual(proposals[0]["auto_accept"], "false")

    def test_full_span_matching_and_disabled_candidate_rules_abstain(self):
        for text, reason in [
            ("ثقة له أفراد", "no_exact_enabled_rule_match"),
            ("وثقه النسائي", "no_exact_enabled_rule_match"),
            ("صدوق يخطئ", "no_exact_enabled_rule_match"),
            ("من العاشرة", "candidate_rule_not_enabled"),
            ("صحابي", "no_exact_enabled_rule_match"),
        ]:
            with self.subTest(text=text):
                packet = self.temp_dir()
                inputs = tiny_packet(packet, text)
                rows = {key: read_csv(value) for key, value in inputs.items() if value.suffix == ".csv"}
                proposals = build_proposals(
                    rows["candidate_entries"],
                    rows["statements"],
                    rows["sources"],
                    rows["source_evidence"],
                    self.registry_rows,
                )
                self.assertEqual(proposals[0]["proposal_status"], "abstain")
                self.assertEqual(proposals[0]["abstention_reason"], reason)
                self.assertEqual(proposals[0]["proposed_taqrib_rank_number"], "")

    def test_identity_source_and_evidence_gates_fail_closed(self):
        for kwargs, expected_reason in [
            ({"identity": "mismatch"}, "candidate_identity_not_confirmed"),
            ({"source_status": "unverified"}, "taqrib_source_not_verified"),
        ]:
            with self.subTest(expected_reason=expected_reason):
                packet = self.temp_dir()
                inputs = tiny_packet(packet, "ثقة", **kwargs)
                rows = {key: read_csv(value) for key, value in inputs.items() if value.suffix == ".csv"}
                proposals = build_proposals(
                    rows["candidate_entries"],
                    rows["statements"],
                    rows["sources"],
                    rows["source_evidence"],
                    self.registry_rows,
                )
                self.assertEqual(proposals[0]["proposal_status"], "abstain")
                self.assertEqual(proposals[0]["abstention_reason"], expected_reason)

        packet = self.temp_dir()
        inputs = tiny_packet(packet, "ثقة")
        evidence = read_csv(inputs["source_evidence"])
        evidence[0]["evidence_text_verbatim"] = "ثقة أخرى"
        proposals = build_proposals(
            read_csv(inputs["candidate_entries"]),
            read_csv(inputs["statements"]),
            read_csv(inputs["sources"]),
            evidence,
            self.registry_rows,
        )
        self.assertEqual(proposals[0]["proposal_status"], "abstain")
        self.assertEqual(proposals[0]["abstention_reason"], "statement_evidence_missing_or_mismatched")

        packet = self.temp_dir()
        inputs = tiny_packet(packet, "ثقة")
        candidates = read_csv(inputs["candidate_entries"])
        candidates[0]["taqrib_entry_text_verbatim"] = "نص مصدر مختلف"
        proposals = build_proposals(
            candidates,
            read_csv(inputs["statements"]),
            read_csv(inputs["sources"]),
            read_csv(inputs["source_evidence"]),
            self.registry_rows,
        )
        self.assertEqual(proposals[0]["proposal_status"], "abstain")
        self.assertEqual(proposals[0]["abstention_reason"], "statement_not_found_exactly_in_entry")

    @unittest.skipUnless(PILOT_DIR.is_dir(), "Legacy shamela4_narrator_audit archive pruned on taqrib-oriented")
    def test_pilot_development_run_excludes_placeholders_and_rejected_identity(self):
        rows = {
            name: read_csv(PILOT_DIR / f"{name}.csv")
            for name in ("candidate_entries", "statements", "sources", "source_evidence")
        }
        reviewed = [row for row in rows["statements"] if row["statement_record_status"] == "reviewed_statement"]
        placeholders = [row for row in rows["statements"] if row["statement_record_status"] != "reviewed_statement"]
        self.assertEqual(len(reviewed), 34)
        self.assertEqual(len(placeholders), 3)
        proposals = build_proposals(
            rows["candidate_entries"], rows["statements"], rows["sources"], rows["source_evidence"], self.registry_rows
        )
        self.assertEqual(len(proposals), 34)
        self.assertEqual(sum(row["proposal_status"] == "proposed_for_human_review" for row in proposals), 5)
        self.assertEqual(
            {row["rule_id"] for row in proposals if row["proposal_status"] == "proposed_for_human_review"},
            {"RANK_THIQA_EXACT_001", "RANK_SADUQ_ERROR_EXACT_001", "RANK_SADUQ_IKHTILAT_EXACT_001"},
        )
        self.assertFalse(any(row["candidate_entry_id"] == "PROV-04-C02" and row["proposal_status"] != "abstain" for row in proposals))

    def test_pipeline_preserves_arabic_newlines_blanks_human_fields_and_hashes(self):
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            source_dir = root / "input"
            original_text = "نص عربي، مع تشكيلٍ\nوسطر ثانٍ"
            inputs = tiny_packet(source_dir, original_text)
            before_hashes = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in inputs.items()}
            output = root / "output"
            manifest = run_pipeline(
                inputs,
                REGISTRY,
                output,
                generated_at_utc="2026-11-14T00:00:00Z",
                run_scope="unit_test_fixture",
            )
            proposals = read_csv(output / "ANNOTATION_AUTO_PROPOSALS.csv")
            human = read_csv(output / "HUMAN_REVIEW.csv")
            self.assertTrue((output / "ANNOTATION_AUTO_PROPOSALS.csv").read_bytes().startswith(b"\xef\xbb\xbf"))
            self.assertTrue((output / "HUMAN_REVIEW.csv").read_bytes().startswith(b"\xef\xbb\xbf"))
            self.assertEqual(proposals[0]["statement_text_verbatim"], original_text)
            self.assertEqual(human[0]["statement_text_verbatim"], original_text)
            self.assertTrue(all(human[0][field] == "" for field in ("human_decision", "human_rank_number", "reviewer_notes")))
            self.assertEqual(
                before_hashes,
                {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in inputs.items()},
            )
            sidecar = (output / "RUN_MANIFEST.sha256").read_text(encoding="ascii").split()[0]
            self.assertEqual(sidecar, hashlib.sha256((output / "RUN_MANIFEST.json").read_bytes()).hexdigest())
            self.assertEqual(manifest["scope"], "unit_test_fixture")
            proposal_headers, _ = read_generated_csv(output / "ANNOTATION_AUTO_PROPOSALS.csv")
            self.assertNotIn("historical_evaluator", proposal_headers)
            self.assertNotIn("target_task_scope", proposal_headers)
            self.assertNotIn("taqrib_rank_number", proposal_headers)
            snapshot = output / "RULE_REGISTRY_SNAPSHOT.csv"
            self.assertEqual(snapshot.read_bytes(), REGISTRY.read_bytes())
            for name, digest in manifest["output_sha256"].items():
                self.assertEqual(hashlib.sha256((output / name).read_bytes()).hexdigest(), digest)

    def test_reproducible_outputs_and_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            inputs = tiny_packet(root / "input", "ثقة")
            out_a = root / "out_a"
            out_b = root / "out_b"
            fixed = "2026-11-14T00:00:00Z"
            run_pipeline(inputs, REGISTRY, out_a, generated_at_utc=fixed, run_scope="unit_test_fixture")
            run_pipeline(inputs, REGISTRY, out_b, generated_at_utc=fixed, run_scope="unit_test_fixture")
            files_a = sorted(path.name for path in out_a.iterdir())
            files_b = sorted(path.name for path in out_b.iterdir())
            self.assertEqual(files_a, files_b)
            for name in files_a:
                self.assertEqual((out_a / name).read_bytes(), (out_b / name).read_bytes(), name)
            with self.assertRaises(FileExistsError):
                run_pipeline(inputs, REGISTRY, out_a, generated_at_utc=fixed, run_scope="unit_test_fixture")

    def test_development_scope_rejects_any_nonpilot_packet(self):
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            inputs = tiny_packet(root / "input", "ثقة")
            with self.assertRaises(PreflightError):
                run_pipeline(inputs, REGISTRY, root / "output", generated_at_utc="2026-11-14T00:00:00Z")
            self.assertFalse((root / "output").exists())


if __name__ == "__main__":
    unittest.main()
