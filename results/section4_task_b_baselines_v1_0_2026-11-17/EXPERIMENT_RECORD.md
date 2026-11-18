# Experiment Record: Section 4 Task B Baselines and Fusion (v1.0)

- Experiment ID: `EXP-SEC4-TASKB-V1.0`
- Date: `2026-11-17`
- Research question / objective: Evaluate single-modality text baselines (TF-IDF + LinearSVC/LogReg across strict and expanded historical arms), graph topology vs GCN message-passing baselines, and Text + Graph fusion models on the zero-leakage N=5,250 12-rank narrator benchmark.
- Dataset version and checksums: `task_b_historical_inputs_v0_3_2026-11-17`, `task_b_historical_inputs_v0_4_2026-11-17`, and `task_b_consolidated_graph_v0_3_2026-11-17` (all SHA-256 verified at runtime).
- Prediction unit and target: Narrator entry (`entry_id`), Ibn Hajar 12 categories (`task_a_rank_1_to_12`), keeping Rank 1 separate in `r2_12_macro_f1` diagnostics.
- Inclusion / exclusion rules: `unique_1to1_high_conf` + `assigned_rank` (`N=5,250`, including `420` recovered zero-quote `Majhul`/`Mastur` narrators).
- Train / validation / test split and split unit: Narrator-disjoint stratified splits (`3,674 / 788 / 788`, zero overlap on `entry_id` and `shamela_narrator_id`).
- Leakage checks: Verified `0` `تقريب`, `تحرير`, or `ابن حجر` occurrences across all text passages (`v0.3`, `v0.4 fwaed`, `v0.4 ablation`) and `0` `قلت` / `قال المؤلف` in `v0.4 ablation`.
- Random seed(s): Deterministic linear baselines (`seed=42`); 5 deterministic seeds `[42, 123, 456, 789, 101112]` for all PyTorch MLP/GCN/ConcatDirGNN models.
- Software and hardware environment: Python, scikit-learn, PyTorch `2.12.1+cu126`, device `cuda`.
- Primary and secondary metrics: Primary 12-rank Macro-F1; secondary R2-12 Macro-F1, Accuracy, Weighted-F1, Quadratic Weighted Kappa (QWK), MAE, auxiliary 3-tier rollup.
