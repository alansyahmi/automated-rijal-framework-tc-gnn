# Stage 3: TC-GNN (Text-Classification-informed GNN) Ablation Report (v3)

- **Generated (UTC):** 2026-11-22 15:37:54Z
- **Elapsed:** 4537.1s | **Device:** CPU (`backend=mps_native`)
- **Clean Cohort (excluding `missing` + `suspect_alignment`):** `train = 5046`, `val = 1086`, `test = 1077`.
- **Ṭabaqah Chronology Pruning (`chrono_pruned`, Pure Sanad):** 42,011 → **37364** kept (`4647` pruned).
- **3-Run Determinism Check (`G4a`, `seed=42`):** `all_3_bit_exact = True`, `max_abs_diff = 0.0`.
- **Graph Homophily (`chrono_sanad`):** 12-rank edge=0.2725 (class=0.0474); 3-tier edge=0.5316 (class=0.1477).

## 1. 5-Seed Test Split Ablation Table (Mean ± Std + Ensemble)

| Model | Family | Rank MAE ↓ | QWK ↑ | Bin Acc ↑ | 3-Tier MF1 ↑ | Shift MF1 ↑ | R6 MAE ↓ | Ens MAE ↓ | Ens Shift MF1 ↑ |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `G0_Stage2_AraBERT_NoGraph` | `stage2_esa_anchor` | 0.6597±0.0000 | 0.8892±0.0000 | 0.8951±0.0000 | 0.7919±0.0000 | 0.7262±0.0000 | 1.4946±0.0000 | 0.6597 | 0.7262 |
| `G2a_Sem_Plus_SanadStruct_HistGBDT` | `tabular_with_struct` | 1.4076±0.0000 | 0.6432±0.0000 | 0.7892±0.0000 | 0.6146±0.0000 | 0.7162±0.0000 | 1.8519±0.0000 | 1.4076 | 0.7162 |
| `G1_GraphOnly_NoText` | `graph_only` | 1.3331±0.0133 | 0.7087±0.0042 | 0.8162±0.0020 | 0.6517±0.0018 | 0.5335±0.0049 | 1.7368±0.0159 | 1.3263 | 0.5392 |
| `G2b_Sem_Plus_SanadStruct_MLP` | `tabular_with_struct` | 0.6577±0.0038 | 0.8885±0.0018 | 0.9058±0.0007 | 0.7977±0.0023 | 0.7216±0.0065 | 1.4744±0.0118 | 0.6558 | 0.7247 |
| `G3a_Undirected_GCN` | `undirected_gnn` | 0.6747±0.0155 | 0.8882±0.0026 | 0.9075±0.0020 | 0.7969±0.0027 | 0.7200±0.0052 | 1.4779±0.0113 | 0.6708 | 0.7183 |
| `G3b_Undirected_GraphSAGE` | `undirected_gnn` | 0.6819±0.0187 | 0.8867±0.0024 | 0.9038±0.0042 | 0.7954±0.0026 | 0.7246±0.0019 | 1.4758±0.0233 | 0.6799 | 0.7210 |
| `G3c_Undirected_GATv2` | `undirected_gnn` | 0.6784±0.0114 | 0.8860±0.0017 | 0.9053±0.0038 | 0.7994±0.0056 | 0.7177±0.0058 | 1.4741±0.0240 | 0.6760 | 0.7162 |
| `G4a_Directed_TC_GNN_Sanad` | `directed_tc_gnn_primary` | 0.6784±0.0172 | 0.8858±0.0023 | 0.9064±0.0028 | 0.7979±0.0015 | 0.7214±0.0060 | 1.4847±0.0187 | 0.6760 | 0.7240 |
| `G4b_Directed_TC_GNN_UnprunedSanad` | `ablation_unpruned_edges` | 0.6900±0.0156 | 0.8852±0.0038 | 0.9066±0.0025 | 0.7979±0.0018 | 0.7227±0.0070 | 1.4710±0.0104 | 0.6866 | 0.7156 |
| `G4c_MV_TC_GNN_Sanad_Plus_kNN` | `ablation_semantic_knn` | 0.6846±0.0187 | 0.8862±0.0018 | 0.9053±0.0015 | 0.7969±0.0021 | 0.7222±0.0059 | 1.4888±0.0137 | 0.6821 | 0.7259 |
| `G4d_Directed_TC_GNN_Consolidated` | `ablation_consolidated_edges` | 0.6626±0.0055 | 0.8913±0.0019 | 0.9055±0.0026 | 0.7985±0.0026 | 0.7286±0.0031 | 1.4586±0.0102 | 0.6613 | 0.7320 |
