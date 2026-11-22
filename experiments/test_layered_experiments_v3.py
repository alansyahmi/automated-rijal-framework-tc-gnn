"""Tests for P5 layered experiments report, invariants, and external validation."""

from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from common.hashing import sha256_text_normalized

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "results" / "layered_experiments_v3_2026-11-21"


class LayeredExperimentsV3Tests(unittest.TestCase):
    def test_manifest_hashes_and_posix_paths(self) -> None:
        manifest = json.loads((OUT_DIR / "MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["homophily"]["sanad_edges_raw"], 42011)
        self.assertEqual(manifest["homophily"]["sanad_edges_chrono_kept"], 37364)
        self.assertEqual(manifest["homophily"]["sanad_edges_chrono_pruned"], 4647)
        for fname, info in manifest["files"].items():
            fpath = OUT_DIR / fname
            self.assertTrue(fpath.exists())
            self.assertEqual(sha256_text_normalized(fpath), info["sha256"])

    def test_exp_c_never_evaluates_on_tahrir(self) -> None:
        with (OUT_DIR / "EXPERIMENT_A_TO_D_METRICS_V3.csv").open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        exp_c = [r for r in rows if r["experiment"] == "Exp_C_Scholarly_E2"]
        self.assertGreaterEqual(len(exp_c), 1)
        for r in exp_c:
            self.assertNotIn("tahrir", r["eval_target"].lower())
            self.assertIn("kashif", r["eval_target"].lower())

    def test_final_table_8827_provenance_and_g_non_overwrite(self) -> None:
        with (OUT_DIR / "FINAL_LAYERED_RIJAL_SCORES_8827_V3.csv").open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 8827)
        for r in rows:
            if r["source"] == "observed_scholarly":
                self.assertEqual(r["score_G_estimate"], "")
            else:
                self.assertIn(r["source"], {"model_estimate", "pending_stage3_gpu"})

    def test_sensitivity_slices_and_kashif_bootstrap(self) -> None:
        with (OUT_DIR / "E1_SENSITIVITY_SUMMARY_V3.csv").open("r", encoding="utf-8-sig", newline="") as f:
            sens = {r["e1_preset"]: r for r in csv.DictReader(f)}
        self.assertEqual(set(sens.keys()), {"default", "halved", "doubled", "off"})

        with (OUT_DIR / "SLICE_METRICS_V3.csv").open("r", encoding="utf-8-sig", newline="") as f:
            slices = {r["slice"]: r for r in csv.DictReader(f)}
        self.assertEqual(int(slices["clean_test_cohort"]["n"]), 1077)
        self.assertEqual(int(slices["test_rank6_maqbul"]["n"]), 227)
        self.assertEqual(
            int(slices["test_connected_chrono_sanad"]["n"]) + int(slices["test_isolated_chrono_sanad"]["n"]),
            1077,
        )

        with (OUT_DIR / "KASHIF_PAIRED_BOOTSTRAP_V3.csv").open("r", encoding="utf-8-sig", newline="") as f:
            boot = {(r["subset"], r["metric"]): r for r in csv.DictReader(f)}
        # Do not pin the direction or size of the E2-vs-B effect here: a test must not enforce a result.
        acc_nv = boot[("paired_non_verbatim", "tier3_acc")]
        acc_clean = boot[("paired_clean", "tier3_acc")]
        self.assertGreater(int(acc_clean["n_common"]), 1500)
        self.assertLessEqual(int(acc_clean["n_common"]), int(acc_nv["n_common"]))
        for key in [("paired_clean", m) for m in ("tier3_acc", "tier3_macro_f1", "tier3_qwk", "tier5_qwk")]:
            self.assertIn(key, boot)

        with (OUT_DIR / "KASHIF_AGREEMENT_V3.csv").open("r", encoding="utf-8-sig", newline="") as f:
            agree = list(csv.DictReader(f))
        for r in agree:
            self.assertNotEqual(r["majority_tier3_acc"], "", "every al-Kashif row must carry its majority-class floor")
