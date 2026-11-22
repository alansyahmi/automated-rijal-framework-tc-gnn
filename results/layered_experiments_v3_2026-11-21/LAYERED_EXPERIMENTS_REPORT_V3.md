# Layered 0–100 Narrator Score: Experiments A–D Report (v3)

- **Generated (UTC):** 2026-11-22 17:35:23Z
- **Stage 2 Task Note:** Stage 2 (`Exp_B_ESA_Learned`) performs **entry-level evaluative stance classification** predicting *Taḥrīr* verdicts/shifts from full *Taqrīb* entries (`3076`) + metadata (not per-quote speaker/target extraction).
- **Stage 2 ESA Dir:** `results/stage2_esa_benchmarks_v3_2026-11-21`
- **Stage 3 TC-GNN Dir:** `results/stage3_tc_gnn_benchmarks_v3_2026-11-21`

## 0. Coverage, Missingness, and Exclusion Accounting (8,827 Narrators)

- **Layer B (`status_B`):** observed `7262`, abstained `1565`.
- **Layer E1 (`status_E1`):** observed qualifier adjustment `119`, not_applicable `7143`, abstained `1565` (within paired B+E2 clean cohort: shifted toward E2 `99`, unchanged distance `0`, away `18`).
- **Layer E2 (`status_E2`):** agreement `4177`, dissent `2398`, maqbul_to_r7 `398`, first_grade `211`, no_grade `181`, qualification `56`, abstained `1339`, **excluded `missing` (`10`) + `suspect_alignment` (`57`)**.
- **Rank Shift Audit (paired observed B & E2):** upgraded `1123`, unchanged `4466`, downgraded `1621`; binary band crossings (`1–6 <-> 7–12`): `31` upgrades, `1437` downgrades.

## 1. Experiments A–D Summary

| Experiment | Track | Model / Layer | Eval Target | Status | N | Rank MAE ↓ | QWK ↑ | 3-Tier Acc ↑ | 3-Tier MF1 ↑ | Shift MF1 ↑ | R6 MAE ↓ |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| `Exp_A_Majority_Baseline` | `Track_R_Deterministic` | `majority_class (train modal rank/shift)` | `tahrir_clean_test` | `COMPLETED` | 1077 | 2.4689 | 0.0 | 0.4067 | 0.1927 | 0.255 | 3.9207 |
| `Exp_A_LookupTable_Baseline` | `Track_R_Deterministic` | `lookup_table ((rank_B, maqbul) -> train mode)` | `tahrir_clean_test` | `COMPLETED` | 1077 | 0.6202 | 0.8749 | 0.8171 | 0.7901 | 0.6576 | 1.5066 |
| `Exp_A_Baseline_B` | `Track_R_Deterministic` | `score_B (Ibn Hajar Taqrib)` | `tahrir_clean_test_descriptive` | `COMPLETED` | 1077 | 0.7233 | 0.8603 | 0.7066 | 0.698 | 0.255 | 1.978 |
| `Exp_B_Qualifiers_E1_Det` | `Track_R_Deterministic` | `score_E1 (B + within-band E1 qualifiers)` | `tahrir_clean_test_descriptive` | `COMPLETED` | 1077 | 0.7247 | 0.8603 | 0.7066 | 0.698 | 0.255 | 1.9783 |
| `Exp_B_ESA_Learned` | `Track_L_ESA` | `M0_Identity_Baseline` | `tahrir_clean_test` | `COMPLETED` | 1077 | 0.7233 | 0.8603 | 0.7066 | 0.698 | 0.255 | 1.978 |
| `Exp_B_ESA_Learned` | `Track_L_ESA` | `M1a_Meta_Linear` | `tahrir_clean_test` | `COMPLETED` | 1077 | 0.7607 | 0.8833 | 0.7902 | 0.7679 | 0.6957 | 1.537 |
| `Exp_B_ESA_Learned` | `Track_L_ESA` | `M1b_Meta_HistGBDT` | `tahrir_clean_test` | `COMPLETED` | 1077 | 0.7194 | 0.8832 | 0.792 | 0.7727 | 0.6824 | 1.5224 |
| `Exp_B_ESA_Learned` | `Track_L_ESA` | `M1c_Meta_RandomForest` | `tahrir_clean_test` | `COMPLETED` | 1077 | 0.7097 | 0.8784 | 0.7939 | 0.7751 | 0.7166 | 1.5825 |
| `Exp_B_ESA_Learned` | `Track_L_ESA` | `M2a_TFIDF_Full_Linear` | `tahrir_clean_test` | `COMPLETED` | 1077 | 0.8095 | 0.8822 | 0.7679 | 0.7497 | 0.6996 | 1.5142 |
| `Exp_B_ESA_Learned` | `Track_L_ESA` | `M2b_TFIDF_Full_HistGBDT` | `tahrir_clean_test` | `COMPLETED` | 1077 | 0.7195 | 0.8911 | 0.8013 | 0.7808 | 0.6917 | 1.4943 |
| `Exp_B_ESA_Learned` | `Track_L_ESA` | `M2c_TFIDF_NameStripped_Linear` | `tahrir_clean_test` | `COMPLETED` | 1077 | 0.7891 | 0.879 | 0.7716 | 0.7515 | 0.6987 | 1.5351 |
| `Exp_B_ESA_Learned` | `Track_L_ESA` | `M3a_CAMeLBERT_Sentiment_Plus_Meta` | `tahrir_clean_test` | `COMPLETED` | 1077 | 0.7189 | 0.8865 | 0.7911 | 0.7704 | 0.6963 | 1.5576 |
| `Exp_B_ESA_Learned` | `Track_L_ESA` | `M3b_AraBERTv02_Full_DualHead` | `tahrir_clean_test` | `COMPLETED` | 1077 | 0.6597 | 0.8892 | 0.8115 | 0.7919 | 0.7262 | 1.4946 |
| `Exp_B_ESA_Learned` | `Track_L_ESA` | `M3c_AraBERTv02_NameStripped_DualHead` | `tahrir_clean_test` | `COMPLETED` | 1077 | 0.6485 | 0.891 | 0.8236 | 0.7997 | 0.7183 | 1.4663 |
| `Exp_C_Scholarly_E2` | `Track_R_Deterministic` | `score_E2 (B + E1 + Tahrir)` | `al_kashif_paired_clean` | `COMPLETED` | 1994 |  | 0.6757 | 0.669 | 0.651 |  |  |
| `Exp_D_TC_GNN` | `Track_L_TC_GNN` | `G0_Stage2_AraBERT_NoGraph` | `tahrir_clean_test_5seed_ens` | `COMPLETED` | 1077 | 0.6597 | 0.8892 | 0.8115 | 0.7919 | 0.7262 | 1.4946 |
| `Exp_D_TC_GNN` | `Track_L_TC_GNN` | `G2a_Sem_Plus_SanadStruct_HistGBDT` | `tahrir_clean_test_5seed_ens` | `COMPLETED` | 1077 | 1.4076 | 0.6432 | 0.6342 | 0.6146 | 0.7162 | 1.8519 |
| `Exp_D_TC_GNN` | `Track_L_TC_GNN` | `G1_GraphOnly_NoText` | `tahrir_clean_test_5seed_ens` | `COMPLETED` | 1077 | 1.3263 | 0.7087 | 0.6737 | 0.6517 | 0.5392 | 1.7368 |
| `Exp_D_TC_GNN` | `Track_L_TC_GNN` | `G2b_Sem_Plus_SanadStruct_MLP` | `tahrir_clean_test_5seed_ens` | `COMPLETED` | 1077 | 0.6558 | 0.8885 | 0.8214 | 0.7977 | 0.7247 | 1.4744 |
| `Exp_D_TC_GNN` | `Track_L_TC_GNN` | `G3a_Undirected_GCN` | `tahrir_clean_test_5seed_ens` | `COMPLETED` | 1077 | 0.6708 | 0.8882 | 0.8199 | 0.7969 | 0.7183 | 1.4779 |
| `Exp_D_TC_GNN` | `Track_L_TC_GNN` | `G3b_Undirected_GraphSAGE` | `tahrir_clean_test_5seed_ens` | `COMPLETED` | 1077 | 0.6799 | 0.8867 | 0.8171 | 0.7954 | 0.721 | 1.4758 |
| `Exp_D_TC_GNN` | `Track_L_TC_GNN` | `G3c_Undirected_GATv2` | `tahrir_clean_test_5seed_ens` | `COMPLETED` | 1077 | 0.676 | 0.886 | 0.8214 | 0.7994 | 0.7162 | 1.4741 |
| `Exp_D_TC_GNN` | `Track_L_TC_GNN` | `G4a_Directed_TC_GNN_Sanad` | `tahrir_clean_test_5seed_ens` | `COMPLETED` | 1077 | 0.676 | 0.8858 | 0.8191 | 0.7979 | 0.724 | 1.4847 |
| `Exp_D_TC_GNN` | `Track_L_TC_GNN` | `G4b_Directed_TC_GNN_UnprunedSanad` | `tahrir_clean_test_5seed_ens` | `COMPLETED` | 1077 | 0.6866 | 0.8852 | 0.8184 | 0.7979 | 0.7156 | 1.471 |
| `Exp_D_TC_GNN` | `Track_L_TC_GNN` | `G4c_MV_TC_GNN_Sanad_Plus_kNN` | `tahrir_clean_test_5seed_ens` | `COMPLETED` | 1077 | 0.6821 | 0.8862 | 0.8186 | 0.7969 | 0.7259 | 1.4888 |
| `Exp_D_TC_GNN` | `Track_L_TC_GNN` | `G4d_Directed_TC_GNN_Consolidated` | `tahrir_clean_test_5seed_ens` | `COMPLETED` | 1077 | 0.6613 | 0.8913 | 0.8191 | 0.7985 | 0.732 | 1.4586 |

## 2. External Validation vs al-Dhahabi's *al-Kāshif* (1616)

Primary subset: `paired_clean` (paired B/E2, al-Kashif span in neither Taqrib nor Tahrir, Tahrir does not cite al-Dhahabi). QWK and Macro-F1 are the primary agreement metrics; accuracy is secondary and must be read against the majority-class floor.

| Layer | Subset | N | 3-Tier Acc ↑ | Majority Acc | 3-Tier MF1 ↑ | 3-Tier QWK ↑ | 5-Tier QWK ↑ | 5-Tier Spearman ↑ |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `Exp_A_score_B` | `all_observed` | 3227 | 0.7075 | 0.5448 | 0.7116 | 0.6826 | 0.7577 | 0.7289 |
| `Exp_A_score_B` | `all_excl_sahabi` | 3009 | 0.6873 | 0.5118 | 0.6999 | 0.6645 | 0.7054 | 0.6720 |
| `Exp_A_score_B` | `paired_B_E2_common` | 3227 | 0.7075 | 0.5448 | 0.7116 | 0.6826 | 0.7577 | 0.7289 |
| `Exp_A_score_B` | `non_verbatim` | 2186 | 0.6702 | 0.4739 | 0.6831 | 0.6554 | 0.7388 | 0.7083 |
| `Exp_A_score_B` | `paired_non_verbatim_taqrib_only_v1` | 2508 | 0.6252 | 0.4860 | 0.6462 | 0.5964 | 0.7005 | 0.6661 |
| `Exp_A_score_B` | `paired_non_verbatim` | 2186 | 0.6702 | 0.4739 | 0.6831 | 0.6554 | 0.7388 | 0.7083 |
| `Exp_A_score_B` | `paired_non_verbatim_excl_sahabi` | 2087 | 0.6555 | 0.4490 | 0.6727 | 0.6404 | 0.7045 | 0.6713 |
| `Exp_A_score_B` | `paired_clean` | 1994 | 0.6836 | 0.4829 | 0.6932 | 0.6796 | 0.7557 | 0.7248 |
| `Exp_B_score_E1` | `all_observed` | 3227 | 0.7075 | 0.5448 | 0.7116 | 0.6826 | 0.7577 | 0.7286 |
| `Exp_B_score_E1` | `all_excl_sahabi` | 3009 | 0.6873 | 0.5118 | 0.6999 | 0.6645 | 0.7054 | 0.6717 |
| `Exp_B_score_E1` | `paired_B_E2_common` | 3227 | 0.7075 | 0.5448 | 0.7116 | 0.6826 | 0.7577 | 0.7286 |
| `Exp_B_score_E1` | `non_verbatim` | 2186 | 0.6702 | 0.4739 | 0.6831 | 0.6554 | 0.7388 | 0.7082 |
| `Exp_B_score_E1` | `paired_non_verbatim_taqrib_only_v1` | 2508 | 0.6252 | 0.4860 | 0.6462 | 0.5964 | 0.7005 | 0.6663 |
| `Exp_B_score_E1` | `paired_non_verbatim` | 2186 | 0.6702 | 0.4739 | 0.6831 | 0.6554 | 0.7388 | 0.7082 |
| `Exp_B_score_E1` | `paired_non_verbatim_excl_sahabi` | 2087 | 0.6555 | 0.4490 | 0.6727 | 0.6404 | 0.7045 | 0.6712 |
| `Exp_B_score_E1` | `paired_clean` | 1994 | 0.6836 | 0.4829 | 0.6932 | 0.6796 | 0.7557 | 0.7250 |
| `Exp_C_score_E2` | `all_observed` | 3304 | 0.7176 | 0.5442 | 0.6744 | 0.7099 | 0.7700 | 0.7707 |
| `Exp_C_score_E2` | `all_excl_sahabi` | 3083 | 0.6993 | 0.5115 | 0.6682 | 0.6999 | 0.7328 | 0.7287 |
| `Exp_C_score_E2` | `paired_B_E2_common` | 3227 | 0.7205 | 0.5448 | 0.6773 | 0.7141 | 0.7754 | 0.7766 |
| `Exp_C_score_E2` | `non_verbatim` | 2237 | 0.6464 | 0.4734 | 0.6242 | 0.6574 | 0.7386 | 0.7441 |
| `Exp_C_score_E2` | `paired_non_verbatim_taqrib_only_v1` | 2508 | 0.6571 | 0.4860 | 0.6331 | 0.6625 | 0.7360 | 0.7364 |
| `Exp_C_score_E2` | `paired_non_verbatim` | 2186 | 0.6468 | 0.4739 | 0.6248 | 0.6591 | 0.7412 | 0.7475 |
| `Exp_C_score_E2` | `paired_non_verbatim_excl_sahabi` | 2087 | 0.6310 | 0.4490 | 0.6171 | 0.6459 | 0.7102 | 0.7159 |
| `Exp_C_score_E2` | `paired_clean` | 1994 | 0.6690 | 0.4829 | 0.6510 | 0.6757 | 0.7542 | 0.7527 |
| `Exp_C_score_E2` | `observed_first_grade_abstained_B` | 77 | 0.5974 | 0.5195 | 0.5361 | 0.5614 | 0.5412 | 0.5138 |
| `Exp_D_G4a_All` | `all_observed` | 3706 | 0.6705 | 0.5556 | 0.6422 | 0.6599 | 0.7412 | 0.7508 |
| `Exp_D_G4a_All` | `all_excl_sahabi` | 3400 | 0.6421 | 0.5156 | 0.6293 | 0.6383 | 0.6796 | 0.6883 |
| `Exp_D_G4a_All` | `paired_B_E2_common` | 3227 | 0.6548 | 0.5448 | 0.6310 | 0.6415 | 0.7301 | 0.7420 |
| `Exp_D_G4a_All` | `non_verbatim` | 2537 | 0.6248 | 0.4876 | 0.6109 | 0.6349 | 0.7212 | 0.7322 |
| `Exp_D_G4a_All` | `paired_non_verbatim_taqrib_only_v1` | 2508 | 0.5614 | 0.4860 | 0.5604 | 0.5573 | 0.6715 | 0.6888 |
| `Exp_D_G4a_All` | `paired_non_verbatim` | 2186 | 0.6043 | 0.4739 | 0.5961 | 0.6107 | 0.7107 | 0.7231 |
| `Exp_D_G4a_All` | `paired_non_verbatim_excl_sahabi` | 2087 | 0.5865 | 0.4490 | 0.5857 | 0.5936 | 0.6732 | 0.6885 |
| `Exp_D_G4a_All` | `paired_clean` | 1994 | 0.6369 | 0.4829 | 0.6283 | 0.6438 | 0.7338 | 0.7384 |
| `Exp_D_G4a_All` | `observed_first_grade_abstained_B` | 77 | 0.6104 | 0.5195 | 0.6014 | 0.5318 | 0.6054 | 0.5875 |
| `Exp_D_G4a_EstimateOnly` | `all_observed` | 402 | 0.8085 | 0.6493 | 0.7023 | 0.8161 | 0.8026 | 0.7807 |
| `Exp_D_G4a_EstimateOnly` | `all_excl_sahabi` | 317 | 0.7603 | 0.5552 | 0.6889 | 0.8024 | 0.7361 | 0.6743 |
| `Exp_D_G4a_EstimateOnly` | `non_verbatim` | 300 | 0.7800 | 0.5933 | 0.6874 | 0.8063 | 0.7778 | 0.7462 |

### Paired Bootstrap E2 vs B on *al-Kāshif* ($B = 2000$, `seed = 42`)

| Subset | Metric | N | Δ (E2 − B) | 95% CI | Two-sided p |
|---|---|---:|---:|---|---:|
| `paired_B_E2_common` | `tier3_acc` | 3227 | +0.0130 | [-0.0025, +0.0291] | 0.1010 |
| `paired_B_E2_common` | `tier3_macro_f1` | 3227 | -0.0343 | [-0.0519, -0.0153] | 0.0000 |
| `paired_B_E2_common` | `tier3_qwk` | 3227 | +0.0315 | [+0.0151, +0.0486] | 0.0000 |
| `paired_B_E2_common` | `tier5_qwk` | 3227 | +0.0177 | [+0.0064, +0.0294] | 0.0030 |
| `paired_B_E2_common` | `tier5_spearman` | 3227 | +0.0477 | [+0.0358, +0.0597] | 0.0000 |
| `paired_non_verbatim` | `tier3_acc` | 2186 | -0.0233 | [-0.0421, -0.0037] | 0.0200 |
| `paired_non_verbatim` | `tier3_macro_f1` | 2186 | -0.0584 | [-0.0777, -0.0377] | 0.0000 |
| `paired_non_verbatim` | `tier3_qwk` | 2186 | +0.0038 | [-0.0156, +0.0234] | 0.6940 |
| `paired_non_verbatim` | `tier5_qwk` | 2186 | +0.0024 | [-0.0104, +0.0162] | 0.7250 |
| `paired_non_verbatim` | `tier5_spearman` | 2186 | +0.0392 | [+0.0262, +0.0530] | 0.0000 |
| `paired_non_verbatim_excl_sahabi` | `tier3_acc` | 2087 | -0.0244 | [-0.0436, -0.0043] | 0.0210 |
| `paired_non_verbatim_excl_sahabi` | `tier3_macro_f1` | 2087 | -0.0556 | [-0.0761, -0.0340] | 0.0000 |
| `paired_non_verbatim_excl_sahabi` | `tier3_qwk` | 2087 | +0.0055 | [-0.0140, +0.0270] | 0.5930 |
| `paired_non_verbatim_excl_sahabi` | `tier5_qwk` | 2087 | +0.0057 | [-0.0090, +0.0217] | 0.4550 |
| `paired_non_verbatim_excl_sahabi` | `tier5_spearman` | 2087 | +0.0446 | [+0.0291, +0.0611] | 0.0000 |
| `paired_clean` | `tier3_acc` | 1994 | -0.0145 | [-0.0321, +0.0040] | 0.1220 |
| `paired_clean` | `tier3_macro_f1` | 1994 | -0.0422 | [-0.0624, -0.0216] | 0.0000 |
| `paired_clean` | `tier3_qwk` | 1994 | -0.0039 | [-0.0234, +0.0162] | 0.6860 |
| `paired_clean` | `tier5_qwk` | 1994 | -0.0015 | [-0.0143, +0.0124] | 0.8180 |
| `paired_clean` | `tier5_spearman` | 1994 | +0.0279 | [+0.0143, +0.0420] | 0.0000 |

## 3. Graph Homophily (`TAQRIB_V2_GRAPH_EDGES.csv`, Pure Sanad)

- **Chronology Pruning (`chrono_pruned`):** `42011` -> `37364` edges (`4647` pruned).
- **Chronology-Pruned Sanad (E2 labels):** 12-rank edge=0.2725 (class=0.0474); 3-tier edge=0.5316 (class=0.1477).
- **Unpruned Sanad (E2 labels):** 12-rank edge=0.2679 (class=0.0441); 3-tier edge=0.5272 (class=0.1446).

## 4. Layer E₁ Sensitivity Analysis (`default`, `halved`, `doubled`, `off`)

| Preset | N Observed E1 | Test Rank MAE | Test Spearman | Test 3-Tier MF1 | Kashif Full 3T Acc | Kashif Full 3T MF1 | Kashif NV 3T Acc | Kashif NV 3T MF1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `default` | 119 | 0.7247 | 0.8926 | 0.6980 | 0.7075 | 0.7116 | 0.6702 | 0.6831 |
| `halved` | 119 | 0.7240 | 0.8926 | 0.6980 | 0.7075 | 0.7116 | 0.6702 | 0.6831 |
| `doubled` | 119 | 0.7261 | 0.8926 | 0.6980 | 0.7075 | 0.7116 | 0.6702 | 0.6831 |
| `off` | 0 | 0.7233 | 0.8930 | 0.6980 | 0.7075 | 0.7116 | 0.6702 | 0.6831 |

## 5. Slice Breakdowns (Clean Test & Subgroup Coverage)

| Slice | N | B vs E2 MAE | E1 vs E2 MAE | B vs E2 3T-MF1 | E1 vs E2 3T-MF1 | B vs E2 QWK | E1 vs E2 QWK |
|---|---:|---:|---:|---:|---:|---:|---:|
| `clean_test_cohort` | 1077 | 0.7233 | 0.7247 | 0.6980 | 0.6980 | 0.8603 | 0.8603 |
| `test_connected_chrono_sanad` | 689 | 0.6560 | 0.6580 | 0.7149 | 0.7149 | 0.8538 | 0.8538 |
| `test_isolated_chrono_sanad` | 388 | 0.8428 | 0.8431 | 0.6572 | 0.6572 | 0.8493 | 0.8493 |
| `test_rank6_maqbul` | 227 | 1.9780 | 1.9783 | 0.1164 | 0.1164 | 0.0000 | 0.0000 |
| `full_rank6_maqbul_paired` | 1569 | 1.9885 | 1.9884 | 0.1222 | 0.1222 | 0.0000 | 0.0000 |
