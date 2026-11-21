"""CPU contract tests for the v3 Stage 2 ESA and Stage 3 TC-GNN scripts."""

from __future__ import annotations

import csv
import unittest
from pathlib import Path

import numpy as np
import pytest

from experiments.v3_common import (
    EXCLUDED_E2_STATUSES,
    assert_no_tahrir_leakage,
    build_meta_matrix,
    compute_graph_homophily,
    compute_metrics,
    rank_to_0_1,
    rank_to_0_100,
    rank_to_tier3_id,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
MASTER_CSV = (
    REPO_ROOT
    / "data"
    / "2_interim"
    / "rijal_fyp_modelling_pipeline"
    / "taqrib_v2_master_dataset_2026-11-20"
    / "TAQRIB_V2_MASTER_NODES_8827.csv"
)
LAYERED_WIDE_CSV = (
    REPO_ROOT
    / "data"
    / "2_interim"
    / "rijal_fyp_modelling_pipeline"
    / "layered_scores_v3_2026-11-21"
    / "LAYERED_SCORES_WIDE_V3.csv"
)
STAGE2_V3 = REPO_ROOT / "experiments" / "run_stage2_esa_benchmarks_v3.py"
STAGE3_V3 = REPO_ROOT / "experiments" / "run_stage3_tc_gnn_benchmarks_v3.py"


class V3CommonContractTests(unittest.TestCase):
    def test_rank_scaling_and_tier3_mapping(self) -> None:
        self.assertAlmostEqual(rank_to_0_1(1.0), 1.0)
        self.assertAlmostEqual(rank_to_0_1(12.0), 0.0)
        self.assertAlmostEqual(rank_to_0_100(1.0), 100.0)
        self.assertAlmostEqual(rank_to_0_100(12.0), 0.0)
        self.assertEqual(rank_to_tier3_id(1), 2)
        self.assertEqual(rank_to_tier3_id(3), 2)
        self.assertEqual(rank_to_tier3_id(4), 1)
        self.assertEqual(rank_to_tier3_id(6), 1)
        self.assertEqual(rank_to_tier3_id(7), 0)
        self.assertEqual(rank_to_tier3_id(12), 0)

    def test_build_meta_matrix_zero_leakage_and_width(self) -> None:
        with MASTER_CSV.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            sample_rows = [row for _, row in zip(range(8), reader)]
        matrix, feat_names = build_meta_matrix(sample_rows)
        self.assertEqual(matrix.shape, (8, 42))
        self.assertEqual(len(feat_names), 42)
        assert_no_tahrir_leakage(feat_names)

        for leaked in (
            "tahrir_rank_bilgin_1_to_12",
            "score_E2",
            "rank_E2",
            "delta_E2",
            "status_E2",
            "score2_rank",
        ):
            with self.assertRaises(AssertionError):
                assert_no_tahrir_leakage(feat_names + [leaked])

    def test_compute_metrics_perfect_and_r6(self) -> None:
        y_rank = np.array([1.0, 4.0, 6.0, 9.0, 12.0])
        y_shift = np.array([1, 0, 2, 1, 2])
        y_pred_cont = np.array([1.0, 4.0, 6.0, 9.0, 12.0])
        y_pred_shift = np.array([1, 0, 2, 1, 2])
        is_maqbul = np.array([0, 0, 1, 0, 0], dtype=bool)
        m = compute_metrics(y_rank, y_shift, y_pred_cont, y_pred_shift, is_maqbul)
        self.assertAlmostEqual(m["rank_mae"], 0.0)
        self.assertAlmostEqual(m["rank_qwk"], 1.0)
        self.assertAlmostEqual(m["tier3_acc"], 1.0)
        self.assertAlmostEqual(m["tier3_macro_f1"], 1.0)
        self.assertAlmostEqual(m["bin_acc"], 1.0)
        self.assertAlmostEqual(m["shift_macro_f1"], 1.0)
        self.assertEqual(int(m["r6_n"]), 1)
        self.assertAlmostEqual(m["r6_rank_mae"], 0.0)

    def test_compute_graph_homophily(self) -> None:
        # 4 nodes, labels [2, 2, 0, 1], node 3 masked out.
        labels = np.array([2, 2, 0, 1], dtype=np.int64)
        valid = np.array([True, True, True, False])
        # Edges among valid nodes: (0->1 same), (1->2 diff), (0->3 ignored), (3->1 ignored)
        res = compute_graph_homophily([0, 1, 0, 3], [1, 2, 3, 1], labels, valid)
        self.assertEqual(res["n_labeled_edges"], 2)
        self.assertAlmostEqual(res["edge_homophily"], 0.5)
        self.assertFalse(np.isnan(res["class_homophily"]))


class V3DatasetAndScriptContractTests(unittest.TestCase):
    def test_v3_split_counts_after_suspect_and_missing_exclusion(self) -> None:
        with LAYERED_WIDE_CSV.open("r", encoding="utf-8-sig", newline="") as f:
            layered = list(csv.DictReader(f))
        self.assertEqual(len(layered), 8827)

        split_obs_counts = {"train": 0, "val": 0, "test": 0, "excluded_unranked": 0}
        first_grade_obs = 0
        for row in layered:
            st = row["status_E2"]
            rk = row["rank_E2"].strip()
            if st == "missing":
                self.assertEqual(rk, "")
                continue
            if st in EXCLUDED_E2_STATUSES:
                continue
            if rk:
                split_obs_counts[row["split"]] += 1
                if st == "observed_first_grade":
                    first_grade_obs += 1
        self.assertEqual(split_obs_counts["train"], 5046)
        self.assertEqual(split_obs_counts["val"], 1086)
        self.assertEqual(split_obs_counts["test"], 1077)
        self.assertEqual(first_grade_obs, 211)

    def test_v3_scripts_use_aligned_terminology(self) -> None:
        for path in (STAGE2_V3, STAGE3_V3):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("Temporal-Causal", text)
            self.assertNotIn("temporal_causal", text)
            self.assertNotIn("Score 1", text)
            self.assertNotIn("Score 2", text)
        s2_text = STAGE2_V3.read_text(encoding="utf-8")
        self.assertIn("build_meta_matrix", s2_text)
        s3_text = STAGE3_V3.read_text(encoding="utf-8")
        self.assertIn("assert_no_tahrir_leakage", s3_text)
        self.assertIn("chrono_pruned", s3_text)
        self.assertIn("score_G_estimate", s3_text)
        self.assertIn("model_estimate", s3_text)


@pytest.mark.gpu
def test_v3_stage2_and_stage3_imports_when_torch_present() -> None:
    pytest.importorskip("torch")
    pytest.importorskip("transformers")
    pytest.importorskip("torch_geometric")
    from experiments import run_stage2_esa_benchmarks_v3 as s2
    from experiments import run_stage3_tc_gnn_benchmarks_v3 as s3

    data = s2.load_v3_stage2_inputs()
    assert len(data["entry_ids"]) == 8827
    assert s3.PRUNING_COLUMN_MAP["sanad_chrono_pruned_adj"] == "chrono_pruned_adj"
