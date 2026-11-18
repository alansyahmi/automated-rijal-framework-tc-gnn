# Experiment Record: Section 4 Targeted OOF Text + ConcatDirGNN (v1.1)

- Experiment ID: `EXP-SEC4-OOF-GNN-V1.1`
- Date: `2026-11-17`
- Research question / objective: Test whether feeding 12-dimensional narrator-level out-of-fold TF-IDF LogisticRegression log-probabilities plus pure graph topology into ConcatDirGNN resolves the TruncatedSVD(256) compression loss observed in v1.0.
- Leakage controls: OOF folds inside `train` (`3,674`) asserted narrator-disjoint on both `entry_id` and `shamela_narrator_id`; `C` and `class_weight` tuned solely on train OOF Macro-F1; `val` and `test` features generated strictly by full-`train` LogReg; all Ibn Hajar / Taqrib / Tahrir exclusions asserted at load time.
- Software and hardware environment: Python, scikit-learn, PyTorch `2.12.1+cu126`, device `cuda`.
