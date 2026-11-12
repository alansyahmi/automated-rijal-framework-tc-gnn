#!/usr/bin/env python3
"""Unit tests for Shamela4 Rijāl Reference Corpus Manifest, Files, and Integrity.

Verifies:
1. Manifest validation: exactly 9 target books present with required metadata and research roles.
2. File existence and SHA-256 hash integrity.
3. JSONL record structure and error-free parsing across pages and TOC.
4. Page continuity, page-number bounds, and absence of malformed/empty pages.
5. Deep verification of Taqrīb al-Tahdhīb (ID 3076): entry 1, entry 8826, preface, colophon, and ʿAwwāmah edition metadata.
6. Markdown inventory deliverable presence and structure.
"""
from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "dataset_discovery/target_feasibility"
MANIFEST_PATH = OUTPUT_DIR / "rijal_reference_corpus_manifest.json"
REPORT_PATH = OUTPUT_DIR / "RIJAL_REFERENCE_CORPUS_INVENTORY.md"
SPEC_PATH = OUTPUT_DIR / "PROVENANCE_AND_TEMPORAL_FIREWALL_SPEC.md"
SCRIPT_PATH = OUTPUT_DIR / "establish_rijal_reference_corpus.py"
RAW_BASE_DIR = PROJECT_ROOT / "data/1_raw/Shamela4_Full_DB/26__التراجم-والطبقات"

EXPECTED_BOOK_IDS = {3076, 8246, 1716, 1615, 890, 4609, 1976, 1981, 1616}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


class TestRijalReferenceCorpus(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = PROJECT_ROOT
        cls.manifest_path = MANIFEST_PATH
        cls.report_path = REPORT_PATH
        cls.raw_base_dir = RAW_BASE_DIR

        if not cls.manifest_path.is_file():
            raise FileNotFoundError(f"Manifest not found: {cls.manifest_path}")

        with cls.manifest_path.open("r", encoding="utf-8") as f:
            cls.manifest = json.load(f)

    # 1. Manifest structure and book count
    def test_manifest_structure_and_book_count(self) -> None:
        self.assertEqual(self.manifest["manifest_version"], "1.0.0")
        self.assertEqual(self.manifest["dataset_repository"], "AuthenticIlm/Shamela4_Full_DB")
        self.assertIn("retrieval_timestamp_utc", self.manifest)
        self.assertEqual(self.manifest["total_books_audited"], 9)
        self.assertEqual(len(self.manifest["books"]), 9)

        observed_ids = {b["spec"]["book_id"] for b in self.manifest["books"]}
        self.assertEqual(observed_ids, EXPECTED_BOOK_IDS, "Manifest does not contain all 9 expected book IDs")

    # 2. Research roles and tiers assigned and valid
    def test_research_roles_and_tiers_assigned(self) -> None:
        valid_roles = {
            "candidate_reference_target",
            "later_scholarly_reassessment",
            "biographical_synthesis_and_source_tracing",
            "earlier_historical_criticism",
            "earlier_synthesis_and_abridgement",
        }
        valid_tiers = {1, 2, 3, 4, 5}
        for b in self.manifest["books"]:
            role = b["spec"]["research_role"]
            self.assertIn(role, valid_roles, f"Invalid research role '{role}' for book {b['spec']['book_id']}")
            tier = b["spec"].get("tier")
            self.assertIn(tier, valid_tiers, f"Invalid tier '{tier}' for book {b['spec']['book_id']}")
            self.assertTrue(len(b["spec"]["role_rationale"]) > 20)

    # 3. File existence and cryptographic hash integrity
    def test_file_existence_and_hash_integrity(self) -> None:
        for b in self.manifest["books"]:
            spec = b["spec"]
            book_dir = self.raw_base_dir / spec["folder_name"]
            self.assertTrue(book_dir.is_dir(), f"Missing book directory: {book_dir}")

            for comp, finfo in b["files"].items():
                file_path = self.root / finfo["local_path"]
                self.assertTrue(file_path.is_file(), f"Missing file: {file_path}")
                self.assertEqual(
                    file_path.stat().st_size,
                    finfo["bytes"],
                    f"Size mismatch for {file_path}",
                )
                actual_hash = sha256_file(file_path)
                self.assertEqual(
                    actual_hash,
                    finfo["sha256"],
                    f"SHA-256 mismatch for {file_path}",
                )

    # 4. JSONL record structure and parsing
    def test_jsonl_record_structure(self) -> None:
        for b in self.manifest["books"]:
            audit = b["integrity_audit"]
            self.assertEqual(
                audit["malformed_json_lines"],
                0,
                f"Malformed JSONL lines detected in book {b['spec']['book_id']}",
            )
            self.assertGreater(audit["actual_page_count"], 0)
            self.assertGreater(audit["actual_toc_count"], 0)
            # Pages must match manifest declared pages
            self.assertEqual(
                audit["actual_page_count"],
                b["manifest_meta"]["declared_page_count"],
                f"Page count mismatch in book {b['spec']['book_id']}",
            )

    # 5. Page continuity and content absence of empty bodies
    def test_page_continuity_and_body_content(self) -> None:
        for b in self.manifest["books"]:
            audit = b["integrity_audit"]
            self.assertIsNotNone(audit["min_page_num"])
            self.assertIsNotNone(audit["max_page_num"])
            self.assertGreaterEqual(audit["max_page_num"], audit["min_page_num"])
            # The vast majority of pages must have non-empty bodies
            empty_ratio = audit["empty_body_pages"] / audit["actual_page_count"]
            self.assertLess(
                empty_ratio,
                0.05,
                f"Excessive empty page bodies in book {b['spec']['book_id']}: {empty_ratio:.2%}",
            )

    # 6. Deep audit of Taqrib al-Tahdhib (ID 3076)
    def test_taqrib_deep_audit(self) -> None:
        self.assertIn("taqrib_deep_audit", self.manifest)
        t_audit = self.manifest["taqrib_deep_audit"]

        self.assertEqual(t_audit["completeness_verdict"], "complete_unabridged_text")
        self.assertTrue(t_audit["has_intro_layers"], "Taqrib intro layers missing")
        self.assertTrue(t_audit["has_entry_1"], "Taqrib entry 1 missing")
        self.assertTrue(t_audit["has_entry_8825"], "Taqrib entry 8825 missing")
        self.assertTrue(t_audit["has_entry_8826"], "Taqrib entry 8826 missing")
        self.assertTrue(t_audit["has_authentic_colophon"], "Taqrib colophon missing")

        # Verify sample entries across alphabet
        for sample in t_audit["sample_alphabetical_checks"]:
            self.assertTrue(
                sample["verified"],
                f"Alphabetical sample '{sample['target']}' not verified in Taqrib",
            )

    # 7. Markdown report deliverable exists and has corrected content
    def test_markdown_report_deliverable(self) -> None:
        self.assertTrue(self.report_path.is_file(), f"Missing report: {self.report_path}")
        content = self.report_path.read_text(encoding="utf-8")
        self.assertIn("Shamela4 Rijāl Reference Corpus Inventory", content)
        self.assertIn("5-Tier Epistemic Architecture", content)
        self.assertIn("The Dr. Bashshār ʿAwwād Maʿrūf Editorial Connection", content)
        self.assertIn("Source-Dependence & Provenance Map", content)
        self.assertIn("The Epistemological Firewall", content)
        self.assertIn("Passage-Level Provenance & Temporal Firewall Rules", content)
        self.assertIn("Ibn Ḥajar's Assessment is Not Historical Consensus", content)
        self.assertIn("standardized scholarly assessment, used as a reference target for computational emulation", content)
        self.assertIn("3076", content)
        self.assertIn("8246", content)
        self.assertIn("1716", content)
        self.assertIn("1615", content)
        self.assertIn("890", content)
        self.assertIn("4609", content)
        self.assertIn("1976", content)
        self.assertIn("1981", content)
        self.assertIn("1616", content)
        self.assertIn("Muḥammad ʿAwwāmah", content)

    # 8. Provenance and Temporal Firewall Specification deliverable exists and defines date separation
    def test_provenance_and_firewall_spec_deliverable(self) -> None:
        self.assertTrue(SPEC_PATH.is_file(), f"Missing specification: {SPEC_PATH}")
        content = SPEC_PATH.read_text(encoding="utf-8")
        required_schema_fields = [
            "source_work_id",
            "source_work_title",
            "source_work_author",
            "source_work_date",
            "source_edition",
            "source_page_or_entry",
            "passage_verbatim",
            "attributed_evaluator",
            "historical_evaluator_date",
            "reporting_authority",
            "textual_speaker",
            "attribution_evidence",
            "editorial_material_status",
            "input_eligibility",
            "eligibility_reason",
            "verification_status",
        ]
        for fld in required_schema_fields:
            self.assertIn(fld, content, f"Missing required schema field '{fld}' in {SPEC_PATH.name}")

        self.assertIn("Separate the Relevant Dates", content)
        self.assertIn("Source-work composition date", content)
        self.assertIn("Surviving manuscript or textual-witness date", content)
        self.assertIn("independent_corroboration", content)
        self.assertIn("dependent_corroboration", content)
        self.assertIn("unresolved_corroboration", content)
        self.assertIn("Ibn Ḥajar's 12-Rank Classification System", content)
        self.assertIn("Audit of Previous Numerical Claims", content)
        self.assertIn("Operational Workflow for Passage Extraction", content)

    # 9. Verification of Ibn Hajar's 12-rank definition accuracy and distinctness
    def test_taqrib_twelve_ranks_accuracy(self) -> None:
        content = SPEC_PATH.read_text(encoding="utf-8")
        # Rank 1: Companions (restrained description, not absolute transmission integrity)
        self.assertIn("فأولها: الصحابةُ", content)
        self.assertNotIn("Absolute transmission integrity (*ʿadālah*)", content)

        # Rank 6: Maqbul is conditional upon corroboration
        self.assertIn("مقبول، حيث يتابع، وإلا فَليِّنُ الحديث", content)

        # Rank 8: Da'if (unelaborated weakness without recognized authentication)
        self.assertIn("الثامنة: مَن لم يوجد فيه توثيق لمعتبر، ووُجد فيه إطلاق الضعف", content)
        self.assertIn("ضعيف", content)

        # Rank 9: Majhul (solitary transmission without authentication)
        self.assertIn("التاسعة: مَن لم يَرْو عنه غيرُ واحد، ولم يُوثق", content)
        self.assertIn("مجهول", content)

        # Rank 10: Matruk / Saqit (discarded / abandoned)
        self.assertIn("العاشرة: من لم يوَثق البتة، وضُعِّف مع ذلك بقادحٍ", content)
        self.assertIn("متروك", content)

        # Rank 11: Accused of lying
        self.assertIn("الحادية عشرةَ: مَن اتُّهم بالكذب", content)

        # Rank 12: Liar / Fabricator (without extreme systemic fabrication gloss)
        self.assertIn("الثانية عشرةَ: من أُطلِق عليه اسمُ الكذب، والوضع", content)
        self.assertNotIn("Extreme fabricator; deliberate systemic corruption", content)

    # 10. Al-Dhahabi relationship to al-Mizzi is qualified as abridgement drawing on Tahdhib
    def test_al_dhahabi_lineage_to_al_mizzi(self) -> None:
        for fpath in [self.report_path, SPEC_PATH]:
            content = fpath.read_text(encoding="utf-8")
            self.assertIn("drawing substantially on al-Mizzī's *Tahdhīb al-Kamāl*", content)
            # Ensure "independent synthesis" is not asserted without qualification
            self.assertNotIn("earlier independent synthesis", content.lower())

    # 11. Unsupported numerical claims are purged from corpus inventory and manifest
    def test_unsupported_numerical_claims_purged(self) -> None:
        unsupported_strings = [
            "75.63%",
            "58 documented consensus divergences",
            "p = 0.0215",
        ]
        for fpath in [self.report_path, self.manifest_path]:
            content = fpath.read_text(encoding="utf-8")
            for uns in unsupported_strings:
                self.assertNotIn(
                    uns,
                    content,
                    f"Unsupported numerical claim '{uns}' still present in {fpath.name}",
                )

    # 12. Strict policy: Zero em-dashes and zero en-dashes across all deliverables
    def test_zero_em_dash_en_dash_policy(self) -> None:
        forbidden = ["\u2013", "\u2014"]  # en-dash, em-dash
        files_to_check = [
            self.report_path,
            self.manifest_path,
            SPEC_PATH,
            SCRIPT_PATH,
            Path(__file__),
        ]
        for fpath in files_to_check:
            self.assertTrue(fpath.is_file(), f"File does not exist: {fpath}")
            text = fpath.read_text(encoding="utf-8")
            for char in forbidden:
                self.assertNotIn(
                    char,
                    text,
                    f"Forbidden dash character U+{ord(char):04X} detected in {fpath.name}",
                )


if __name__ == "__main__":
    unittest.main()

