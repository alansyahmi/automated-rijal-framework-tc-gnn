# Stage 3: TC-GNN (Text-Classification-informed GNN) Ablation Report (v3)

- **Generated (UTC):** 2026-11-22 08:06:44Z
- **Elapsed:** 8603.3s | **Device:** MPS (`backend=mps_native`)
- **Clean Cohort (excluding `missing` + `suspect_alignment`):** `train = 5046`, `val = 1086`, `test = 1077`.
- **Ṭabaqah Chronology Pruning (`chrono_pruned`, Pure Sanad):** 42,011 → **37364** kept (`4647` pruned).
- **3-Run Determinism Check (`G4a`, `seed=42`):** `all_3_bit_exact = False`, `max_abs_diff = 0.00016499`.
- **Graph Homophily (`chrono_sanad`):** 12-rank edge=0.2725 (class=0.0474); 3-tier edge=0.5316 (class=0.1477).

## 1. 5-Seed Test Split Ablation Table (Mean ± Std + Ensemble)

| Model | Family | Rank MAE ↓ | QWK ↑ | Bin Acc ↑ | 3-Tier MF1 ↑ | Shift MF1 ↑ | R6 MAE ↓ | Ens MAE ↓ | Ens Shift MF1 ↑ |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `G0_Stage2_AraBERT_NoGraph` | `stage2_esa_anchor` | 0.6597±0.0000 | 0.8892±0.0000 | 0.8951±0.0000 | 0.7919±0.0000 | 0.7262±0.0000 | 1.4946±0.0000 | 0.6597 | 0.7262 |
| `G2a_Sem_Plus_SanadStruct_HistGBDT` | `tabular_with_struct` | 1.4076±0.0000 | 0.6432±0.0000 | 0.7892±0.0000 | 0.6146±0.0000 | 0.7162±0.0000 | 1.8519±0.0000 | 1.4076 | 0.7162 |
| `G1_GraphOnly_NoText` | `graph_only` | 1.3366±0.0108 | 0.7031±0.0030 | 0.8145±0.0042 | 0.6482±0.0030 | 0.5330±0.0037 | 1.7361±0.0093 | 1.3307 | 0.5339 |
| `G2b_Sem_Plus_SanadStruct_MLP` | `tabular_with_struct` | 0.6545±0.0010 | 0.8890±0.0006 | 0.9051±0.0021 | 0.7966±0.0043 | 0.7215±0.0048 | 1.4823±0.0055 | 0.6536 | 0.7194 |
| `G3a_Undirected_GCN` | `undirected_gnn` | 0.6679±0.0055 | 0.8891±0.0017 | 0.9075±0.0028 | 0.7980±0.0036 | 0.7175±0.0049 | 1.4745±0.0086 | 0.6653 | 0.7256 |
| `G3b_Undirected_GraphSAGE` | `undirected_gnn` | 0.6808±0.0176 | 0.8872±0.0017 | 0.9056±0.0033 | 0.7967±0.0025 | 0.7238±0.0018 | 1.4728±0.0194 | 0.6790 | 0.7218 |
| `G3c_Undirected_GATv2` | `undirected_gnn` | 0.6869±0.0083 | 0.8864±0.0006 | 0.9060±0.0027 | 0.7984±0.0058 | 0.7224±0.0055 | 1.4630±0.0124 | 0.6847 | 0.7248 |
| `G4a_Directed_TC_GNN_Sanad` | `directed_tc_gnn_primary` | 0.6825±0.0124 | 0.8865±0.0021 | 0.9044±0.0021 | 0.7973±0.0018 | 0.7208±0.0038 | 1.4796±0.0181 | 0.6801 | 0.7218 |
| `G4b_Directed_TC_GNN_UnprunedSanad` | `ablation_unpruned_edges` | 0.6872±0.0157 | 0.8853±0.0026 | 0.9049±0.0022 | 0.7965±0.0008 | 0.7230±0.0047 | 1.4750±0.0147 | 0.6839 | 0.7156 |
| `G4c_MV_TC_GNN_Sanad_Plus_kNN` | `ablation_semantic_knn` | 0.6731±0.0129 | 0.8879±0.0023 | 0.9045±0.0025 | 0.7935±0.0028 | 0.7253±0.0063 | 1.4897±0.0068 | 0.6714 | 0.7271 |
| `G4d_Directed_TC_GNN_Consolidated` | `ablation_consolidated_edges` | 0.6727±0.0191 | 0.8905±0.0031 | 0.9068±0.0046 | 0.7996±0.0039 | 0.7279±0.0021 | 1.4538±0.0091 | 0.6698 | 0.7287 |
