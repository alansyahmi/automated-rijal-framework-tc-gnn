# Stage 3 Methodology: TC-GNN Graph Enrichment & Controlled Ablation (`taqrib-oriented` v2)

- **Script:** [run_stage3_tc_gnn_benchmarks_v2.py](../experiments/run_stage3_tc_gnn_benchmarks_v2.py)
- **Results:** [STAGE3_RESULTS_SUMMARY_V2.md](../results/stage3_tc_gnn_benchmarks_v2_2026-11-20/STAGE3_RESULTS_SUMMARY_V2.md) | [STAGE3_SUBGROUP_AND_SIGNIFICANCE_V2.csv](../results/stage3_tc_gnn_benchmarks_v2_2026-11-20/STAGE3_SUBGROUP_AND_SIGNIFICANCE_V2.csv)
- **Final Deliverable:** [FINAL_TWO_SCORE_RIJAL_REPRESENTATION_8827.csv](../results/stage3_tc_gnn_benchmarks_v2_2026-11-20/FINAL_TWO_SCORE_RIJAL_REPRESENTATION_8827.csv)

---

## 1. Domain Justification & Temporal-Causal Pruning Discovery

Why use a **Directional Temporal-Causal Graph Neural Network (TC-GNN)** rather than a standard undirected GCN?

1. **Asymmetric Scholarly Corroboration (`Teacher → Student` vs. `Student → Teacher`):**
   - In *Taḥrīr Taqrīb al-Tahdhīb* (`8246`), upgrading ambiguous narrators (especially the `1,581` Rank 6 *Maqbūl* entries) depends on **student out-degree corroboration** (*mutābaʿāt* / `روى عنه جمع من الثقات`) rather than merely narrating from a strong teacher.
   - Stage 1 already verified that among Rank 6 *Maqbūl* entries, `graph_out_ge2` is **51.13%** for `upgraded` narrators vs. **26.09%** for `downgraded` narrators.

2. **Empirical Temporal-Causal Pruning on Pure Sanad/Bukhārī Edges (`42,011` → `37,364`):**
   - Auditing the generational delta $\Delta\text{ṭabaqah} = \text{ṭabaqah}_{\text{student}} - \text{ṭabaqah}_{\text{teacher}}$ across all `42,011` pure Sanad/Bukhārī edges revealed:
     - `28,516` (**67.9%**) strictly forward ($\Delta > 0$)
     - `3,981` (**9.5%**) peer narrations (*riwāyat al-aqrān*, $\Delta = 0$)
     - `1,962` (**4.7%**) adjacent generational overlap ($\Delta = -1$)
     - **`4,647` (11.1%) chronologically impossible ($\Delta \le -2$)** — Sanadset disambiguation noise (`2,905` missing *ṭabaqah*).
   - **TC-Pruning Rule:** Remove edges where both endpoints have known *ṭabaqah* and $\Delta\text{ṭabaqah} \le -2$, retaining **`37,364` TC-clean pure Sanad edges** for the primary graph (`G4a`).

---

## 2. Architecture, Zero-Leakage Node Features & Edge Conditioning

- **Transductive Topology, Strict Split Isolation:** Message passing operates over all `8,827` nodes, but loss & gradients are computed **strictly on `train` (`5,080`)**, early stopping monitors `val` (`1,089`), and `test` (`1,089`) remains untouched.
- **Node Features (all standardized strictly on `train`):**
  1. `X_meta` (`39` dims): Stage 2 *Taqrīb* metadata (Score 1 + 12-dim one-hot, `is_conditional_maqbul`, *ṭabaqah* + subtier, 12 sigils, 9 qualifiers, char/word counts).
  2. `X_sem` (`56` dims): Stage 2 **5-fold OOF** semantic features from [STAGE2_OOF_SEMANTIC_FEATURES_8827_V2.csv](../results/stage2_semantic_benchmarks_v2_2026-11-20/STAGE2_OOF_SEMANTIC_FEATURES_8827_V2.csv) (`CAMeLBERT` sentiment 4, `M2` OOF 4, `AraBERTv02` OOF 16, `AraBERTv02` CLS PCA-32 fitted strictly on `train`).
  3. `X_struct_sanad` (`17` dims): Recomputed strictly on the active Sanad graph (`log1p` degrees/weights, distinct books, Bukhārī degrees, `is_isolated`, `out_ge2`, and Score-1-only neighbor aggregations — **zero Score-2 leakage**).
- **5-Dim Directed Edge Attributes:**
  $$e_{u \to v} = \left[\log(1 + w_{uv}),\; \log(1 + \text{books}_{uv}),\; \frac{\text{clip}(\Delta\text{ṭabaqah}, -5, 10)}{10},\; \mathbb{I}(\text{peer}),\; \mathbb{I}(\text{missing\_ṭabaqah})\right]$$
- **Residual-Gated Directional `GATv2` (`G4`):**
  - Two message-passing layers with separate **Forward (`Teacher → Student`)** and **Reverse (`Student → Teacher`)** `GATv2Conv` (`4` heads, `edge_dim=5`, `add_self_loops=False`) plus an optional 3rd **Semantic kNN (`k=8`)** branch (`G4c`, per Zeng et al., 2024).
  - Node-wise learned sigmoid gates $\mathbf{g}_{\text{fwd}}, \mathbf{g}_{\text{rev}}$ adaptively control neighborhood aggregation while skip connections (`LayerNorm` + concatenation `[h_0 || h_2]`) preserve isolated nodes' Stage 2 semantics.
  - Identical Dual-Head loss as Stage 2 ($\text{CE}_{\text{rank}} + 0.35\,\text{SmoothL1}(\hat{r}_{\text{exp}}, r) + \text{WeightedCE}_{\text{shift}}$), `AdamW` (`lr=1.5e-3`, `weight_decay=2e-2`), `200` max epochs, patience `30`, across **5 seeds (`42–46`)**.

---

## 3. Verified 5-Seed Test Results (`N = 1,089`) & Statistical Significance

| Model | Rank MAE ↓ | QWK ↑ | Bin Acc ↑ | Shift MF1 ↑ | R6 *Maqbūl* MAE ↓ | Ens MAE ↓ | Ens Shift MF1 ↑ |
|---|---:|---:|---:|---:|---:|---:|---:|
| `G0_Stage2_AraBERT_NoGraph` | 0.6600 | 0.8899 | 0.8916 | 0.7136 | 1.5120 | 0.6600 | 0.7136 |
| `G1_GraphOnly_NoText` *(No text / No Score 1)* | 1.3329±0.0136 | 0.7044±0.0059 | 0.8110±0.0034 | 0.5381±0.0071 | 1.7493±0.0153 | 1.3249 | 0.5363 |
| `G2b_Sem_Plus_SanadStruct_MLP` | 0.6544±0.0028 | 0.8892±0.0010 | **0.9052**±0.0017 | 0.7156±0.0056 | 1.4715±0.0063 | 0.6527 | 0.7166 |
| `G3c_Undirected_GATv2` | 0.6720±0.0114 | 0.8861±0.0023 | 0.9012±0.0025 | 0.7184±0.0061 | 1.4773±0.0056 | 0.6697 | 0.7267 |
| **`G4a_Directed_TC_GNN_Sanad`** *(Primary)* | 0.6815±0.0124 | 0.8854±0.0016 | 0.9029±0.0020 | **0.7246**±0.0034 | 1.4760±0.0047 | 0.6789 | **0.7301** |
| `G4b_Directed_TC_GNN_UnprunedSanad` | 0.6826±0.0131 | 0.8854±0.0013 | 0.9028±0.0023 | 0.7195±0.0043 | 1.4767±0.0111 | 0.6792 | 0.7269 |
| `G4c_MV_TC_GNN_Sanad_Plus_kNN` *(Zeng 2024)* | 0.6682±0.0017 | 0.8878±0.0008 | 0.9047±0.0014 | 0.7156±0.0096 | 1.4772±0.0059 | 0.6673 | 0.7196 |
| **`G4d_Directed_TC_GNN_Consolidated`** | **0.6535**±0.0023 | **0.8903**±0.0008 | 0.9047±0.0009 | 0.7216±0.0064 | **1.4495**±0.0041 | **0.6523** | 0.7243 |

### Key Analytical Findings (Paired Bootstrap `B = 2,000` vs. `G0`)
1. **Pure Graph Signal (`G1`):** Without text or Score 1, pure TC-Sanad topology + *ṭabaqah*/sigils achieves **81.10% Binary *Taʿdīl*/*Jarḥ* accuracy** (`QWK = 0.7044`), proving Sanad topology carries strong reliability signal.
2. **Temporal-Causal Pruning Benefit (`G4a` vs. `G4b`):** Pruning the `4,647` impossible edges improves Shift Macro-F1 (`0.7246` / ens **`0.7301`** vs. `0.7195` / ens `0.7269`).
3. **Statistically Significant Binary Gains over Stage 2 (`G0`):**
   - `G4a` (TC-Sanad): `BinAcc = 0.9054` (`+0.0138`, **p = 0.017**) and highest Shift Macro-F1 (**`0.7301`**, `+0.0165`, `p = 0.076`).
   - `G4c` (+kNN): `BinAcc = 0.9063` (`+0.0147`, **p = 0.009**) and stabilizes MAE variance (`std = 0.0017`).
   - `G4d` (Consolidated): `BinAcc = 0.9045` (**p = 0.048**), lowest Rank MAE (**`0.6523`**), highest QWK (**`0.8903`**), and lowest R6 *Maqbūl* MAE (**`1.4477`**).
4. **Honest Non-GNN vs. GNN Attribution (`G2b` vs. `G4`):** `G2b` (`MLP + 1-hop Sanad features`) reaches `MAE = 0.6527` and `BinAcc = 0.9073` (`p = 0.011`), demonstrating that **1-hop Sanad degree & Score-1 neighbor features** drive most of the rank/binary improvement, while **multi-hop Directional TC-GNN** achieves the highest Shift Macro-F1 (`G4a: 0.7301` vs. `0.7166`) and lowest R6 *Maqbūl* MAE (`G4d: 1.4477` vs. `1.4672`).

---

## 4. Final Two-Score Deliverable (`8,827 × 17` Columns, `0` NaNs)

Exported to [FINAL_TWO_SCORE_RIJAL_REPRESENTATION_8827.csv](../results/stage3_tc_gnn_benchmarks_v2_2026-11-20/FINAL_TWO_SCORE_RIJAL_REPRESENTATION_8827.csv) from the 5-seed ensemble of primary flagship `G4a_Directed_TC_GNN_Sanad`:
- **Ibn Ḥajar Baseline (Preserved Untouched):** `score1_ibn_hajar_rank_1_to_12`, `taqrib_is_conditional_maqbul`.
- **Scholarly Reference (When Available):** `tahrir_scholar_rank_1_to_12`, `tahrir_disposition`.
- **TC-GNN Computational Enrichment:** `score2_tc_gnn_continuous`, `score2_tc_gnn_rank_1_to_12`, `score2_predicted_shift`, `score2_p_upgraded`, `score2_p_unchanged`, `score2_p_downgraded`, `score2_rank_entropy` (normalized Shannon uncertainty), and `tc_sanad_out_degree` / `tc_sanad_in_degree` / `tc_sanad_is_isolated`.
