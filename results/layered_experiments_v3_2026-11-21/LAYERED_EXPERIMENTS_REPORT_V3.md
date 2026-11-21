# Layered 0–100 Narrator Score: Experiments A–D Report (v3)

- **Generated (UTC):** 2026-11-21 11:47:33Z
- **Stage 2 ESA Dir:** `NOT YET RUN (CUDA GPU required)`
- **Stage 3 TC-GNN Dir:** `NOT YET RUN (CUDA GPU required)`

## 0. Coverage, Missingness, and Exclusion Accounting (8,827 Narrators)

- **Layer B (`status_B`):** observed `7262`, abstained `1565`.
- **Layer E1 (`status_E1`):** observed qualifier adjustment `231`, not_applicable `7031`, abstained `1565` (within paired B+E2 clean cohort: shifted toward E2 `119`, unchanged distance `91`, away `19`).
- **Layer E2 (`status_E2`):** agreement `4177`, dissent `2398`, maqbul_to_r7 `398`, first_grade `211`, no_grade `181`, qualification `56`, abstained `1339`, **excluded `missing` (`10`) + `suspect_alignment` (`57`)**.
- **Rank Shift Audit (paired observed B & E2):** upgraded `1123`, unchanged `4466`, downgraded `1621`; binary band crossings (`1–6 <-> 7–12`): `31` upgrades, `1437` downgrades.

## 1. Experiments A–D Summary

| Experiment | Track | Model / Layer | Eval Target | Status | N | Rank MAE ↓ | QWK ↑ | 3-Tier Acc ↑ | 3-Tier MF1 ↑ | Shift MF1 ↑ | R6 MAE ↓ |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| `Exp_A_Baseline_B` | `Track_R_Deterministic` | `score_B (Ibn Hajar Taqrib)` | `tahrir_clean_test_descriptive` | `COMPLETED` | 1077 | 0.7233 | 0.8603 | 0.7066 | 0.698 | 0.255 | 1.978 |
| `Exp_B_Qualifiers_E1_Det` | `Track_R_Deterministic` | `score_E1 (B + within-band E1 qualifiers)` | `tahrir_clean_test_descriptive` | `COMPLETED` | 1077 | 0.7253 | 0.8603 | 0.7066 | 0.698 | 0.255 | 1.9783 |
| `Exp_B_ESA_Learned` | `Track_L_ESA` | `M3b_AraBERTv02_Full / M3a_GenericSentiment` | `tahrir_clean_test` | `PENDING_CUDA_GPU` | 1077 |  |  |  |  |  |  |
| `Exp_C_Scholarly_E2` | `Track_R_Deterministic` | `score_E2 (B + E1 + Tahrir)` | `al_kashif_paired_non_verbatim` | `COMPLETED` | 2566 |  | 0.4867 | 0.6422 | 0.5839 |  |  |
| `Exp_D_TC_GNN` | `Track_L_TC_GNN` | `G4a_Directed_TC_GNN_Sanad (vs G2b & G0)` | `tahrir_clean_test_5seed_ens` | `PENDING_CUDA_GPU` | 1077 |  |  |  |  |  |  |

## 2. External Validation vs al-Dhahabi's *al-Kāshif* (1616)

| Layer | Subset | N | 3-Tier Acc ↑ | 3-Tier MF1 ↑ | 3-Tier QWK ↑ | 5-Tier QWK ↑ | 5-Tier Spearman ↑ |
|---|---|---:|---:|---:|---:|---:|---:|
| `Exp_A_score_B` | `all_observed` | 3300 | 0.6294 | 0.6225 | 0.5774 | 0.6786 | 0.6436 |
| `Exp_A_score_B` | `paired_B_E2_common` | 3300 | 0.6294 | 0.6225 | 0.5774 | 0.6786 | 0.6436 |
| `Exp_A_score_B` | `non_verbatim` | 2566 | 0.5257 | 0.5427 | 0.4912 | 0.6174 | 0.5927 |
| `Exp_A_score_B` | `paired_non_verbatim` | 2566 | 0.5257 | 0.5427 | 0.4912 | 0.6174 | 0.5927 |
| `Exp_A_score_B` | `paired_non_verbatim_excl_sahabi` | 2460 | 0.5065 | 0.5325 | 0.4792 | 0.5803 | 0.5436 |
| `Exp_B_score_E1` | `all_observed` | 3300 | 0.6294 | 0.6225 | 0.5774 | 0.6786 | 0.6431 |
| `Exp_B_score_E1` | `paired_B_E2_common` | 3300 | 0.6294 | 0.6225 | 0.5774 | 0.6786 | 0.6431 |
| `Exp_B_score_E1` | `non_verbatim` | 2566 | 0.5257 | 0.5427 | 0.4912 | 0.6174 | 0.5928 |
| `Exp_B_score_E1` | `paired_non_verbatim` | 2566 | 0.5257 | 0.5427 | 0.4912 | 0.6174 | 0.5928 |
| `Exp_B_score_E1` | `paired_non_verbatim_excl_sahabi` | 2460 | 0.5065 | 0.5325 | 0.4792 | 0.5803 | 0.5438 |
| `Exp_C_score_E2` | `all_observed` | 3378 | 0.7060 | 0.6391 | 0.5516 | 0.6582 | 0.6623 |
| `Exp_C_score_E2` | `paired_B_E2_common` | 3300 | 0.7082 | 0.6418 | 0.5523 | 0.6615 | 0.6665 |
| `Exp_C_score_E2` | `non_verbatim` | 2633 | 0.6430 | 0.5838 | 0.4911 | 0.6115 | 0.6189 |
| `Exp_C_score_E2` | `paired_non_verbatim` | 2566 | 0.6422 | 0.5839 | 0.4867 | 0.6111 | 0.6192 |
| `Exp_C_score_E2` | `paired_non_verbatim_excl_sahabi` | 2460 | 0.6280 | 0.5779 | 0.4768 | 0.5781 | 0.5740 |
| `Exp_C_score_E2` | `observed_first_grade_abstained_B` | 78 | 0.6154 | 0.5110 | 0.5132 | 0.5161 | 0.4802 |

### Paired Bootstrap E2 vs B on *al-Kāshif* ($B = 2000$, `seed = 42`)

| Subset | Metric | N | Δ (E2 − B) | 95% CI | Two-sided p |
|---|---|---:|---:|---|---:|
| `paired_B_E2_common` | `tier3_acc` | 3300 | +0.0788 | [+0.0652, +0.0933] | 0.0000 |
| `paired_B_E2_common` | `tier3_macro_f1` | 3300 | +0.0193 | [+0.0038, +0.0358] | 0.0130 |
| `paired_B_E2_common` | `tier3_qwk` | 3300 | -0.0252 | [-0.0444, -0.0039] | 0.0220 |
| `paired_B_E2_common` | `tier5_qwk` | 3300 | -0.0171 | [-0.0313, -0.0018] | 0.0220 |
| `paired_B_E2_common` | `tier5_spearman` | 3300 | +0.0229 | [+0.0104, +0.0365] | 0.0000 |
| `paired_non_verbatim` | `tier3_acc` | 2566 | +0.1165 | [+0.1002, +0.1337] | 0.0000 |
| `paired_non_verbatim` | `tier3_macro_f1` | 2566 | +0.0412 | [+0.0230, +0.0590] | 0.0000 |
| `paired_non_verbatim` | `tier3_qwk` | 2566 | -0.0045 | [-0.0274, +0.0187] | 0.7030 |
| `paired_non_verbatim` | `tier5_qwk` | 2566 | -0.0064 | [-0.0231, +0.0109] | 0.4640 |
| `paired_non_verbatim` | `tier5_spearman` | 2566 | +0.0266 | [+0.0107, +0.0431] | 0.0020 |
| `paired_non_verbatim_excl_sahabi` | `tier3_acc` | 2460 | +0.1215 | [+0.1041, +0.1394] | 0.0000 |
| `paired_non_verbatim_excl_sahabi` | `tier3_macro_f1` | 2460 | +0.0454 | [+0.0272, +0.0633] | 0.0000 |
| `paired_non_verbatim_excl_sahabi` | `tier3_qwk` | 2460 | -0.0024 | [-0.0261, +0.0220] | 0.8300 |
| `paired_non_verbatim_excl_sahabi` | `tier5_qwk` | 2460 | -0.0022 | [-0.0199, +0.0161] | 0.8060 |
| `paired_non_verbatim_excl_sahabi` | `tier5_spearman` | 2460 | +0.0305 | [+0.0123, +0.0491] | 0.0000 |

## 3. Graph Homophily (`TAQRIB_V2_GRAPH_EDGES.csv`, Pure Sanad)

- **Chronology Pruning (`chrono_pruned`):** `42011` -> `37364` edges (`4647` pruned).
- **Chronology-Pruned Sanad (E2 labels):** 12-rank edge=0.2725 (class=0.0474); 3-tier edge=0.5316 (class=0.1477).
- **Unpruned Sanad (E2 labels):** 12-rank edge=0.2679 (class=0.0441); 3-tier edge=0.5272 (class=0.1446).

## 4. Layer E₁ Sensitivity Analysis (`default`, `halved`, `doubled`, `off`)

| Preset | N Observed E1 | Test Rank MAE | Test Spearman | Test 3-Tier MF1 | Kashif Full 3T Acc | Kashif Full 3T MF1 | Kashif NV 3T Acc | Kashif NV 3T MF1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `default` | 231 | 0.7253 | 0.8923 | 0.6980 | 0.6294 | 0.6225 | 0.5257 | 0.5427 |
| `halved` | 231 | 0.7243 | 0.8923 | 0.6980 | 0.6294 | 0.6225 | 0.5257 | 0.5427 |
| `doubled` | 231 | 0.7272 | 0.8923 | 0.6966 | 0.6291 | 0.6226 | 0.5253 | 0.5429 |
| `off` | 231 | 0.7233 | 0.8930 | 0.6980 | 0.6294 | 0.6225 | 0.5257 | 0.5427 |

## 5. Slice Breakdowns (Clean Test & Subgroup Coverage)

| Slice | N | B vs E2 MAE | E1 vs E2 MAE | B vs E2 3T-MF1 | E1 vs E2 3T-MF1 | B vs E2 QWK | E1 vs E2 QWK |
|---|---:|---:|---:|---:|---:|---:|---:|
| `clean_test_cohort` | 1077 | 0.7233 | 0.7253 | 0.6980 | 0.6980 | 0.8603 | 0.8603 |
| `test_connected_chrono_sanad` | 689 | 0.6560 | 0.6585 | 0.7149 | 0.7149 | 0.8538 | 0.8538 |
| `test_isolated_chrono_sanad` | 388 | 0.8428 | 0.8438 | 0.6572 | 0.6572 | 0.8493 | 0.8493 |
| `test_rank6_maqbul` | 227 | 1.9780 | 1.9783 | 0.1164 | 0.1164 | 0.0000 | 0.0000 |
| `full_rank6_maqbul_paired` | 1569 | 1.9885 | 1.9884 | 0.1222 | 0.1222 | 0.0000 | 0.0000 |
