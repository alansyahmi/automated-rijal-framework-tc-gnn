# Section 4 Final Experimental Audit Report (v1.0 and v1.1)

## 1. Test Narrator and Label Integrity (Checklist Item 1)
- Verified exact identity of all `788` held-out test narrators (`entry_id`, `shamela_narrator_id`, `task_a_rank_1_to_12`, `has_early_critic_quote`) across `TASK_B_NODE_STRUCTURAL_FEATURES_V0_3.csv`, `TEST_PREDICTIONS_V1_0.csv`, and `TEST_PREDICTIONS_V1_1.csv`: **PASS**.
- Breakdown: `725` primary-quoted narrators (`has_early_critic_quote=1`) + `63` recovered zero-quote narrators (`has_early_critic_quote=0`).
- Rare long-tail counts in held-out test (`N=788`): Rank 11 = `1`, Rank 12 = `2`, Rank 6 = `14`, Rank 10 = `14`.

## 2. Five-Seed Paired Bootstrap Comparisons (Checklist Items 2 and 3)

Mean paired difference across all 5 seeds (`[42, 123, 456, 789, 101112]`), 2,000 bootstrap resamples on `test N=788`:

| Comparison | Mean Delta Macro-F1 | 95% CI (Delta F1) | p (F1) | Mean Delta Acc | p (Acc) | Mean Delta QWK | p (QWK) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `arm2_v03_all__ConcatDirGNN_vs_BaseTextLogReg` | `+0.0169` | `[-0.0187, +0.0529]` | `0.3500` | `+0.0074` | `0.6080` | `+0.0277` | `0.0780` |
| `arm2_v03_all__ConcatDirGNN_vs_OOFTextOnlyMLP` | `-0.0319` | `[-0.0708, +0.0299]` | `0.6580` | `+0.0003` | `0.9740` | `+0.0045` | `0.6710` |
| `arm2_v03_all__ConcatDirGNN_vs_EarlyMLP` | `+0.0190` | `[-0.0016, +0.0406]` | `0.0610` | `+0.0109` | `0.1670` | `+0.0015` | `0.8250` |
| `arm2_v03_all__ConcatDirGNN_FullInfer_vs_EnsInfer` | `+0.0004` | `[-0.0126, +0.0139]` | `0.8910` | `+0.0025` | `0.7040` | `-0.0009` | `0.9300` |
| `arm3_v03_plus_fwaed__ConcatDirGNN_vs_BaseTextLogReg` | `+0.0153` | `[-0.0210, +0.0515]` | `0.4070` | `-0.0000` | `0.9840` | `+0.0183` | `0.2500` |
| `arm3_v03_plus_fwaed__ConcatDirGNN_vs_OOFTextOnlyMLP` | `-0.0028` | `[-0.0357, +0.0339]` | `0.9780` | `+0.0033` | `0.7700` | `-0.0148` | `0.1870` |
| `arm3_v03_plus_fwaed__ConcatDirGNN_vs_EarlyMLP` | `+0.0086` | `[-0.0155, +0.0330]` | `0.5050` | `+0.0074` | `0.3850` | `-0.0046` | `0.5990` |
| `arm3_v03_plus_fwaed__ConcatDirGNN_FullInfer_vs_EnsInfer` | `+0.0024` | `[-0.0079, +0.0140]` | `0.6800` | `+0.0010` | `0.8270` | `+0.0019` | `0.6850` |
| `arm4_v03_plus_fwaed_plus_tahdhib__ConcatDirGNN_vs_BaseTextLogReg` | `+0.0228` | `[-0.0157, +0.0598]` | `0.2230` | `-0.0005` | `0.9950` | `+0.0134` | `0.2500` |
| `arm4_v03_plus_fwaed_plus_tahdhib__ConcatDirGNN_vs_OOFTextOnlyMLP` | `+0.0118` | `[-0.0132, +0.0367]` | `0.3520` | `+0.0048` | `0.6910` | `-0.0080` | `0.4130` |
| `arm4_v03_plus_fwaed_plus_tahdhib__ConcatDirGNN_vs_EarlyMLP` | `+0.0101` | `[-0.0134, +0.0334]` | `0.4120` | `-0.0015` | `0.8640` | `-0.0089` | `0.3200` |
| `arm4_v03_plus_fwaed_plus_tahdhib__ConcatDirGNN_FullInfer_vs_EnsInfer` | `-0.0069` | `[-0.0154, +0.0012]` | `0.1090` | `-0.0010` | `0.8500` | `-0.0074` | `0.1510` |

## 3. Seed-by-Seed Rare-Class Audit (`OOFTextOnly_MLP` vs `ConcatDirGNN`)

Shows why `OOFTextOnly_arm2_MLP` exhibits high variance (`std=0.0286`) across seeds (`R11` and `R12` support = `1` and `2` in test):

| Model | Seed | Macro-F1 | Acc | R6 F1 | R7 F1 | R10 F1 | R11 F1 (`n=1`) | R12 F1 (`n=2`) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `arm2_v03_all__OOFTextOnly_MLP` | 42 | 0.4345 | 0.6294 | 0.1143 | 0.0000 | 0.5366 | 0.0000 | 0.0000 |
| `arm2_v03_all__OOFTextOnly_MLP` | 123 | 0.5091 | 0.6485 | 0.1250 | 0.0000 | 0.6286 | 0.0000 | 0.6667 |
| `arm2_v03_all__OOFTextOnly_MLP` | 456 | 0.4965 | 0.6345 | 0.1176 | 0.0000 | 0.5500 | 0.0000 | 0.6667 |
| `arm2_v03_all__OOFTextOnly_MLP` | 789 | 0.4904 | 0.6332 | 0.1176 | 0.0000 | 0.5000 | 0.0000 | 0.6667 |
| `arm2_v03_all__OOFTextOnly_MLP` | 101112 | 0.4815 | 0.6180 | 0.1053 | 0.0000 | 0.5366 | 0.0000 | 0.6667 |
| `arm2_v03_all__FusionOOF_ConcatDirGNN` | 42 | 0.4623 | 0.6332 | 0.2222 | 0.0930 | 0.6000 | 0.0000 | 0.0000 |
| `arm2_v03_all__FusionOOF_ConcatDirGNN` | 123 | 0.4502 | 0.6371 | 0.1667 | 0.0513 | 0.5455 | 0.0000 | 0.0000 |
| `arm2_v03_all__FusionOOF_ConcatDirGNN` | 456 | 0.4496 | 0.6256 | 0.1429 | 0.1429 | 0.5333 | 0.0000 | 0.0000 |
| `arm2_v03_all__FusionOOF_ConcatDirGNN` | 789 | 0.4458 | 0.6358 | 0.1379 | 0.1000 | 0.4828 | 0.0000 | 0.0000 |
| `arm2_v03_all__FusionOOF_ConcatDirGNN` | 101112 | 0.4447 | 0.6332 | 0.2308 | 0.1026 | 0.4286 | 0.0000 | 0.0000 |
| `arm3_v03_plus_fwaed__OOFTextOnly_MLP` | 42 | 0.4393 | 0.6244 | 0.1463 | 0.0714 | 0.4571 | 0.0000 | 0.0000 |
| `arm3_v03_plus_fwaed__OOFTextOnly_MLP` | 123 | 0.4475 | 0.6231 | 0.1290 | 0.0000 | 0.2857 | 0.0000 | 0.3333 |
| `arm3_v03_plus_fwaed__OOFTextOnly_MLP` | 456 | 0.4349 | 0.6218 | 0.1538 | 0.0000 | 0.4667 | 0.0000 | 0.0000 |
| `arm3_v03_plus_fwaed__OOFTextOnly_MLP` | 789 | 0.4342 | 0.6244 | 0.1538 | 0.0000 | 0.4667 | 0.0000 | 0.0000 |
| `arm3_v03_plus_fwaed__OOFTextOnly_MLP` | 101112 | 0.4763 | 0.6244 | 0.0588 | 0.0588 | 0.4828 | 0.0000 | 0.5000 |
| `arm3_v03_plus_fwaed__FusionOOF_ConcatDirGNN` | 42 | 0.4383 | 0.6231 | 0.1379 | 0.1818 | 0.4167 | 0.0000 | 0.0000 |
| `arm3_v03_plus_fwaed__FusionOOF_ConcatDirGNN` | 123 | 0.4463 | 0.6345 | 0.1600 | 0.1633 | 0.4167 | 0.0000 | 0.0000 |
| `arm3_v03_plus_fwaed__FusionOOF_ConcatDirGNN` | 456 | 0.4463 | 0.6269 | 0.1429 | 0.1429 | 0.4800 | 0.0000 | 0.0000 |
| `arm3_v03_plus_fwaed__FusionOOF_ConcatDirGNN` | 789 | 0.4440 | 0.6269 | 0.1429 | 0.1818 | 0.4000 | 0.0000 | 0.0000 |
| `arm3_v03_plus_fwaed__FusionOOF_ConcatDirGNN` | 101112 | 0.4431 | 0.6231 | 0.1600 | 0.2174 | 0.4167 | 0.0000 | 0.0000 |
| `arm4_v03_plus_fwaed_plus_tahdhib__OOFTextOnly_MLP` | 42 | 0.4702 | 0.6599 | 0.2051 | 0.0690 | 0.5641 | 0.0000 | 0.0000 |
| `arm4_v03_plus_fwaed_plus_tahdhib__OOFTextOnly_MLP` | 123 | 0.4642 | 0.6586 | 0.1538 | 0.0690 | 0.5556 | 0.0000 | 0.0000 |
| `arm4_v03_plus_fwaed_plus_tahdhib__OOFTextOnly_MLP` | 456 | 0.4671 | 0.6599 | 0.2000 | 0.0000 | 0.5946 | 0.0000 | 0.0000 |
| `arm4_v03_plus_fwaed_plus_tahdhib__OOFTextOnly_MLP` | 789 | 0.4671 | 0.6624 | 0.2051 | 0.0000 | 0.5854 | 0.0000 | 0.0000 |
| `arm4_v03_plus_fwaed_plus_tahdhib__OOFTextOnly_MLP` | 101112 | 0.4612 | 0.6574 | 0.1500 | 0.0645 | 0.5714 | 0.0000 | 0.0000 |
| `arm4_v03_plus_fwaed_plus_tahdhib__FusionOOF_ConcatDirGNN` | 42 | 0.4871 | 0.6688 | 0.1481 | 0.2564 | 0.5517 | 0.0000 | 0.0000 |
| `arm4_v03_plus_fwaed_plus_tahdhib__FusionOOF_ConcatDirGNN` | 123 | 0.4785 | 0.6624 | 0.1667 | 0.2381 | 0.5517 | 0.0000 | 0.0000 |
| `arm4_v03_plus_fwaed_plus_tahdhib__FusionOOF_ConcatDirGNN` | 456 | 0.4741 | 0.6713 | 0.1481 | 0.1053 | 0.5882 | 0.0000 | 0.0000 |
| `arm4_v03_plus_fwaed_plus_tahdhib__FusionOOF_ConcatDirGNN` | 789 | 0.4749 | 0.6561 | 0.1429 | 0.1951 | 0.5625 | 0.0000 | 0.0000 |
| `arm4_v03_plus_fwaed_plus_tahdhib__FusionOOF_ConcatDirGNN` | 101112 | 0.4742 | 0.6637 | 0.0769 | 0.2727 | 0.5333 | 0.0000 | 0.0000 |

## 4. OOF (80% Fit) vs Full-Train (100% Fit) Confidence Distribution Audit (Checklist Item 4)

| Arm | Train OOF `max_p` / `entropy` | Test Full-Train `max_p` / `entropy` (KS p vs OOF) | Test 5-Fold Ens `max_p` / `entropy` (KS p vs OOF) | Scaled L2 Norm (Train / Test Full / Test Ens) |
| :--- | :---: | :---: | :---: | :---: |
| `arm2_v03_all` | `0.5407` / `1.3155` | `0.5476` / `1.3061` (`p=0.118` / `0.0839`) | `0.5272` / `1.3482` (`p=0.00738` / `0.00196`) | `2.724` / `2.701` / `2.611` |
| `arm3_v03_plus_fwaed` | `0.5366` / `1.3443` | `0.5400` / `1.3270` (`p=0.11` / `0.192`) | `0.5243` / `1.3730` (`p=0.0137` / `0.0599`) | `2.798` / `2.902` / `2.758` |
| `arm4_v03_plus_fwaed_plus_tahdhib` | `0.5584` / `1.2840` | `0.5660` / `1.2680` (`p=0.305` / `0.458`) | `0.5444` / `1.3223` (`p=0.0569` / `0.0332`) | `2.884` / `2.957` / `2.738` |

## 5. Zero-Quote Subgroup Ablation (`N = 63` Total: `Connected = 25`, `Isolated = 38`) (Checklist Item 5)

| Evidence | Model | Graph | All ZQ (`N=63`) F1 / Acc | Connected ZQ (`N=25`) F1 / Acc | Isolated ZQ (`N=38`) F1 / Acc |
| :--- | :--- | :--- | :---: | :---: | :---: |
| `arm2_v03_all` | `BaseText_LogReg` | No (Base Sparse LogReg) | `0.1018` / `0.5714` | `0.0635` / `0.6154` | `0.1131` / `0.5405` |
| `arm2_v03_all` | `OOFTextOnly_MLP` | No (Neural OOF-Text Only) | `0.1019` / `0.5714` | `0.0638` / `0.6154` | `0.1131` / `0.5405` |
| `arm2_v03_all` | `FusionOOF_EarlyMLP` | Tabular Topo Only (No Msg Pass) | `0.1223` / `0.5841` | `0.1314` / `0.6462` | `0.1131` / `0.5405` |
| `arm2_v03_all` | `FusionOOF_ConcatDirGNN` | Yes (Directional Graph Fusion) | `0.1335` / `0.5524` | `0.1491` / `0.5692` | `0.1131` / `0.5405` |
| `arm3_v03_plus_fwaed` | `BaseText_LogReg` | No (Base Sparse LogReg) | `0.1018` / `0.5714` | `0.0635` / `0.6154` | `0.1131` / `0.5405` |
| `arm3_v03_plus_fwaed` | `OOFTextOnly_MLP` | No (Neural OOF-Text Only) | `0.1072` / `0.5746` | `0.0811` / `0.6231` | `0.1131` / `0.5405` |
| `arm3_v03_plus_fwaed` | `FusionOOF_EarlyMLP` | Tabular Topo Only (No Msg Pass) | `0.1149` / `0.5778` | `0.1027` / `0.6308` | `0.1131` / `0.5405` |
| `arm3_v03_plus_fwaed` | `FusionOOF_ConcatDirGNN` | Yes (Directional Graph Fusion) | `0.1446` / `0.5556` | `0.1740` / `0.5769` | `0.1131` / `0.5405` |
| `arm4_v03_plus_fwaed_plus_tahdhib` | `BaseText_LogReg` | No (Base Sparse LogReg) | `0.2217` / `0.6349` | `0.1067` / `0.6538` | `0.2426` / `0.6216` |
| `arm4_v03_plus_fwaed_plus_tahdhib` | `OOFTextOnly_MLP` | No (Neural OOF-Text Only) | `0.2269` / `0.6508` | `0.1230` / `0.6923` | `0.2446` / `0.6216` |
| `arm4_v03_plus_fwaed_plus_tahdhib` | `FusionOOF_EarlyMLP` | Tabular Topo Only (No Msg Pass) | `0.2298` / `0.6444` | `0.1302` / `0.6769` | `0.2466` / `0.6216` |
| `arm4_v03_plus_fwaed_plus_tahdhib` | `FusionOOF_ConcatDirGNN` | Yes (Directional Graph Fusion) | `0.2698` / `0.6571` | `0.2211` / `0.7077` | `0.2526` / `0.6216` |

## 6. Model Selection and Research Boundaries (Checklist Items 6 and 7)
- **Validation-only / OOF-only selection verified:** In `run_section4_task_b_baselines_v1_0.py`, linear and neural configs were selected strictly on `val` (`N=788`) Macro-F1; in `run_section4_oof_text_gnn_v1_1.py`, TF-IDF `LogReg` hyperparameters (`C=2.0`, `class_weight='sqrt'`) were selected strictly on `train` 5-fold OOF Macro-F1 (`N=3,674`), and downstream neural/GNN checkpoints and hyperparameters were selected strictly on `val` (`N=788`) Macro-F1.
- **Rare-class limitation:** Ranks 11 (`test n=1`, `train n=3`) and 12 (`test n=2`, `train n=12`) are heavily under-powered in 12-rank Macro-F1; single-instance predictions on Rank 11/12 shift 12-class Macro-F1 by up to `~0.04` to `0.08` between seeds.
- **Research scope boundary:** All models predict Ibn Hajar's historical *Taqrib al-Tahdhib* 12-rank classifications from pre-existing classical *rijal* criticism and *sanad* network topology; they do not establish actual moral/scholarly reliability of narrators and do not authenticate Hadith.
- **Transformer deferral (`TODO.md` line 67):** Pretrained Arabic transformers (`CAMeLBERT-CA` / `AraBERT`) are formally deferred as future work / out of scope for the current experimental cycle.
