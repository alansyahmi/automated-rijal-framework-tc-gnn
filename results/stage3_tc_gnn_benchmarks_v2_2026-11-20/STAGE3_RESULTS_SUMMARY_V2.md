# Stage 3: TC-GNN Graph Enrichment & Controlled Ablation Report (v2)

- **Generated (UTC):** 2026-11-20 08:09:17Z
- **Elapsed:** 408.3s | **Device:** CUDA
- **Temporal-Causal Pruning Audit (Pure Sanad):** 42,011 total → **4647** impossible edges (`Δṭabaqah ≤ -2`) pruned → **37364** TC-clean edges.
- **Primary Two-Score Deliverable Generator:** `G4a_Directed_TC_GNN_Sanad` (5-seed ensemble).

## 1. 5-Seed Test Split Ablation Table (`N = 1,089`, Mean ± Std + Ensemble)

| Model | Family | Rank MAE ↓ | QWK ↑ | Bin Acc ↑ | Shift MF1 ↑ | R6 Maqbūl MAE ↓ | Ens MAE ↓ | Ens Shift MF1 ↑ |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `G0_Stage2_AraBERT_NoGraph` | `stage2_text_anchor` | 0.6600±0.0000 | 0.8899±0.0000 | 0.8916±0.0000 | 0.7136±0.0000 | 1.5120±0.0000 | 0.6600 | 0.7136 |
| `G2a_Sem_Plus_SanadStruct_HistGBDT` | `tabular_with_struct` | 1.5953±0.0000 | 0.5452±0.0000 | 0.7594±0.0000 | 0.7143±0.0000 | 2.8170±0.0000 | 1.5953 | 0.7143 |
| `G1_GraphOnly_NoText` | `graph_only` | 1.3329±0.0136 | 0.7044±0.0059 | 0.8110±0.0034 | 0.5381±0.0071 | 1.7493±0.0153 | 1.3249 | 0.5363 |
| `G2b_Sem_Plus_SanadStruct_MLP` | `tabular_with_struct` | 0.6544±0.0028 | 0.8892±0.0010 | 0.9052±0.0017 | 0.7156±0.0056 | 1.4715±0.0063 | 0.6527 | 0.7166 |
| `G3a_Undirected_GCN` | `undirected_gnn` | 0.6622±0.0028 | 0.8882±0.0021 | 0.9052±0.0022 | 0.7116±0.0082 | 1.4679±0.0018 | 0.6609 | 0.7078 |
| `G3b_Undirected_GraphSAGE` | `undirected_gnn` | 0.6657±0.0035 | 0.8881±0.0013 | 0.9023±0.0044 | 0.7183±0.0027 | 1.4821±0.0131 | 0.6644 | 0.7192 |
| `G3c_Undirected_GATv2` | `undirected_gnn` | 0.6720±0.0114 | 0.8861±0.0023 | 0.9012±0.0025 | 0.7184±0.0061 | 1.4773±0.0056 | 0.6697 | 0.7267 |
| `G4a_Directed_TC_GNN_Sanad` | `directed_tc_gnn_primary` | 0.6815±0.0124 | 0.8854±0.0016 | 0.9029±0.0020 | 0.7246±0.0034 | 1.4760±0.0047 | 0.6789 | 0.7301 |
| `G4b_Directed_TC_GNN_UnprunedSanad` | `ablation_unpruned_edges` | 0.6826±0.0131 | 0.8854±0.0013 | 0.9028±0.0023 | 0.7195±0.0043 | 1.4767±0.0111 | 0.6792 | 0.7269 |
| `G4c_MV_TC_GNN_Sanad_Plus_kNN` | `ablation_semantic_knn` | 0.6682±0.0017 | 0.8878±0.0008 | 0.9047±0.0014 | 0.7156±0.0096 | 1.4772±0.0059 | 0.6673 | 0.7196 |
| `G4d_Directed_TC_GNN_Consolidated` | `ablation_consolidated_edges` | 0.6535±0.0023 | 0.8903±0.0008 | 0.9047±0.0009 | 0.7216±0.0064 | 1.4495±0.0041 | 0.6523 | 0.7243 |

## 2. Connected vs. Isolated Subgroup Breakdown (`test`, Ensemble)

| Model | Subgroup | N | Rank MAE ↓ | QWK ↑ | Bin Acc ↑ | Shift MF1 ↑ | R6 MAE ↓ |
|---|---|---:|---:|---:|---:|---:|---:|
| `G0_Stage2_AraBERT_NoGraph` | `connected_sanad` | 694 | 0.6306 | 0.8756 | 0.9006 | 0.6924 | 1.6173 |
| `G0_Stage2_AraBERT_NoGraph` | `isolated_sanad` | 395 | 0.7117 | 0.8925 | 0.8759 | 0.7264 | 1.4093 |
| `G2b_Sem_Plus_SanadStruct_MLP` | `connected_sanad` | 694 | 0.6303 | 0.8750 | 0.9092 | 0.6914 | 1.6052 |
| `G2b_Sem_Plus_SanadStruct_MLP` | `isolated_sanad` | 395 | 0.6920 | 0.8921 | 0.9038 | 0.7320 | 1.3327 |
| `G3c_Undirected_GATv2` | `connected_sanad` | 694 | 0.6492 | 0.8741 | 0.9006 | 0.7090 | 1.6148 |
| `G3c_Undirected_GATv2` | `isolated_sanad` | 395 | 0.7057 | 0.8899 | 0.9013 | 0.7239 | 1.3339 |
| `G4a_Directed_TC_GNN_Sanad` | `connected_sanad` | 694 | 0.6570 | 0.8741 | 0.9092 | 0.7094 | 1.6106 |
| `G4a_Directed_TC_GNN_Sanad` | `isolated_sanad` | 395 | 0.7172 | 0.8870 | 0.8987 | 0.7370 | 1.3378 |
| `G4c_MV_TC_GNN_Sanad_Plus_kNN` | `connected_sanad` | 694 | 0.6479 | 0.8713 | 0.9078 | 0.6993 | 1.6251 |
| `G4c_MV_TC_GNN_Sanad_Plus_kNN` | `isolated_sanad` | 395 | 0.7014 | 0.8914 | 0.9038 | 0.7232 | 1.3311 |

## 3. Learned Directional Gate Activations

- `G1_GraphOnly_NoText`: g_fwd_connected=0.4611, g_fwd_isolated=0.4906, g_rev_connected=0.4417, g_rev_isolated=0.4870
- `G4a_Directed_TC_GNN_Sanad`: g_fwd_connected=0.4572, g_fwd_isolated=0.4954, g_rev_connected=0.4486, g_rev_isolated=0.4944
- `G4b_Directed_TC_GNN_UnprunedSanad`: g_fwd_connected=0.4584, g_fwd_isolated=0.4943, g_rev_connected=0.4517, g_rev_isolated=0.4942
- `G4c_MV_TC_GNN_Sanad_Plus_kNN`: g_fwd_connected=0.4614, g_fwd_isolated=0.4990, g_rev_connected=0.4529, g_rev_isolated=0.4971, g_knn_all=0.5008
- `G4d_Directed_TC_GNN_Consolidated`: g_fwd_connected=0.4590, g_fwd_isolated=0.4938, g_rev_connected=0.4502, g_rev_isolated=0.4909
