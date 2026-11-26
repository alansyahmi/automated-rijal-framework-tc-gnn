# Results consolidation — Brief 1

The inventory counts distinct version/model rows with saved test metrics. `n_seeds` follows each result set’s stated seed protocol. No model was trained, rerun, or rescored.

Primary thesis metric: test R2-12 Macro-F1 (Ranks 2-12). Rank 1 is Companion status, not a reliability grade. The 12-rank, 3-tier, accuracy, and QWK values are also retained in the inventory. Validation selection uses R2-12 Macro-F1 when present; the saved comparison files have no validation R2-12 column, so all four versions use the 12-rank `val_macro_f1` fallback.

## Test-set inventory and validation selection

- **v1.0:** 23 distinct model evaluations. Validation selected `Fusion_arm3_v03_plus_fwaed_PlusTopo_EarlyMLP` using `val_12rank_macro_f1` (0.4653); its test R2-12 Macro-F1 is 0.3415.
- **v1.1:** 15 distinct model evaluations. Validation selected `FusionOOF_arm4_v03_plus_fwaed_plus_tahdhib_PlusTopo_ConcatDirGNN` using `val_12rank_macro_f1` (0.5625); its test R2-12 Macro-F1 is 0.4365.
- **v1.2:** 20 distinct model evaluations. Validation selected `PhaseB_AblA_Arm4PlusCriticCounts_ConcatDirGNN` using `val_12rank_macro_f1` (0.5616); its test R2-12 Macro-F1 is 0.4502.
- **v1.3:** 14 distinct model evaluations. Validation selected `Abl5_HierStreams_TextOnlyPlusTopo_ConcatDirGNN` using `val_12rank_macro_f1` (0.5605); its test R2-12 Macro-F1 is 0.4355.

All v1.0 rows are marked `superseded_leak` as directed. Its validation-selected row is still recorded but is not treated as canonical.

## Paired-bootstrap Macro-F1 comparisons

Holm correction was applied separately to all Macro-F1 comparisons in each source report. Accuracy and QWK rows remain in `BOOTSTRAP_HOLM.csv` with raw p-values; they are outside the specified Holm family. The CSV marks every Macro-F1 comparison that did not survive correction as `False`.

- **v1.0 / section4_task_b_baselines_v1_0_2026-11-17:** 2/5 remained significant: Fusion_arm3_ConcatDirGNN_vs_Fusion_arm3_VanillaGCN; Fusion_arm3_EarlyMLP_vs_Fusion_arm3_VanillaGCN. The other 3 did not.
- **v1.1 / section4_audit_v1_1_2026-11-17:** 0/12 remained significant; all 12 did not.
- **v1.1 / section4_oof_text_gnn_v1_1_2026-11-17:** 3/9 remained significant: Arm2_OOF_ConcatDirGNN_vs_Arm2_OOF_EarlyMLP; Arm2_OOF_ConcatDirGNN_vs_V10_Text_arm2_LinearSVC; Arm3_OOF_ConcatDirGNN_vs_Arm3_OOF_VanillaGCN. The other 6 did not.
- **v1.2 / v1_2_controlled_experiments_2026-11-18:** 1/9 remained significant: PhaseA_ExpB_M1Bios_ConcatDirGNN_vs_ExpA_Arm4_ConcatDirGNN. The other 8 did not.
  - Raw-significant but not Holm-significant: `PhaseA_ExpD_M1BiosAndBookInd_ConcatDirGNN_vs_ExpA_Arm4_ConcatDirGNN` (p=0.024, adjusted p=0.192).
- **v1.3 / v1_3_genre_dilution_diagnostic_2026-11-19:** 2/6 remained significant: Abl3_M1EvalPassages_ConcatDirGNN_vs_Abl2_M1Full_ConcatDirGNN; Abl5_HierTextStream_ConcatDirGNN_vs_Abl2_M1Full_ConcatDirGNN. The other 4 did not.

## Parsing

All targeted model-comparison CSVs, per-rank CSVs, and paired-comparison JSON/Markdown files parsed; no file failures were recorded.
