# v1.2 Controlled Phase A (Method 1), Phase B (Critic Attribution), and Phase C Error Analysis Report

- **Methodological Correction Applied:** Prior `audit_v1_2` (`train+val N=4,462`) was superseded for feature feasibility by strictly `train`-only (`N=3,674`) statistics in `TRAIN_ONLY_FEATURE_FEASIBILITY_V1_2.md`. All OOF text tuning ran strictly inside `train`, checkpoint/hyperparameter tuning strictly on `val` (`N=788`), and held-out `test` (`N=788`) evaluated identically across 5 seeds (`[42, 123, 456, 789, 101112]`).

## 1. Phase A, Phase B, and Exploratory Test Results (`N = 788`, 5-Seed Means)

| Model | Phase | Val Macro-F1 | Test Macro-F1 | Test R2-12 F1 | Test Acc | Test W-F1 | Test QWK | Test MAE | 3-Tier F1 / Acc |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `PhaseA_ExpA_Arm4_BaseText_LogReg` | PhaseA_Baseline | 0.4791 | 0.4528 | 0.4099 | 0.6637 | 0.6469 | 0.8313 | 0.6459 | 0.8060 / 0.8033 |
| `PhaseA_ExpA_Arm4_EarlyMLP` | PhaseA_Baseline | 0.5280 | 0.4601 +/- 0.0119 | 0.4184 | 0.6569 | 0.6470 | 0.8444 | 0.6449 | 0.8185 / 0.8147 |
| `PhaseA_ExpA_Arm4_ConcatDirGNN` | PhaseA_Baseline | 0.5555 | 0.4762 +/- 0.0088 | 0.4350 | 0.6662 | 0.6607 | 0.8425 | 0.6371 | 0.8158 / 0.8129 |
| `PhaseA_ExpB_Arm4PlusM1Bios_BaseText_LogReg` | PhaseA_M1Bios | 0.4621 | 0.4470 | 0.4063 | 0.6485 | 0.6322 | 0.8069 | 0.6980 | 0.7952 / 0.7931 |
| `PhaseA_ExpB_Arm4PlusM1Bios_OOFTextOnly_MLP` | PhaseA_M1Bios | 0.5180 | 0.4290 +/- 0.0098 | 0.3873 | 0.6084 | 0.6086 | 0.8022 | 0.7830 | 0.7987 / 0.7980 |
| `PhaseA_ExpB_Arm4PlusM1Bios_EarlyMLP` | PhaseA_M1Bios | 0.5156 | 0.4248 +/- 0.0152 | 0.3813 | 0.6109 | 0.6117 | 0.8035 | 0.7782 | 0.7932 / 0.7924 |
| `PhaseA_ExpB_Arm4PlusM1Bios_ConcatDirGNN` | PhaseA_M1Bios | 0.5230 | 0.4371 +/- 0.0065 | 0.3945 | 0.6259 | 0.6235 | 0.8117 | 0.7335 | 0.7957 / 0.7949 |
| `PhaseA_ExpC_Arm4PlusBookInd_EarlyMLP` | PhaseA_BookInd | 0.5473 | 0.4638 +/- 0.0071 | 0.4221 | 0.6553 | 0.6470 | 0.8514 | 0.6307 | 0.8202 / 0.8162 |
| `PhaseA_ExpC_Arm4PlusBookInd_ConcatDirGNN` | PhaseA_BookInd | 0.5336 | 0.4676 +/- 0.0061 | 0.4239 | 0.6530 | 0.6500 | 0.8344 | 0.6624 | 0.8094 / 0.8069 |
| `PhaseA_ExpD_Arm4PlusM1BiosAndBookInd_EarlyMLP` | PhaseA_M1BiosAndBookInd | 0.5280 | 0.4480 +/- 0.0147 | 0.4070 | 0.6190 | 0.6205 | 0.8191 | 0.7251 | 0.8008 / 0.7995 |
| `PhaseA_ExpD_Arm4PlusM1BiosAndBookInd_ConcatDirGNN` | PhaseA_M1BiosAndBookInd | 0.4892 | 0.4466 +/- 0.0098 | 0.4038 | 0.6348 | 0.6321 | 0.8188 | 0.7084 | 0.8019 / 0.8000 |
| `PhaseB_AblA_Arm4PlusCriticCounts_EarlyMLP` | PhaseB_CriticCounts | 0.5471 | 0.4727 +/- 0.0071 | 0.4315 | 0.6602 | 0.6512 | 0.8504 | 0.6241 | 0.8264 / 0.8216 |
| `PhaseB_AblA_Arm4PlusCriticCounts_ConcatDirGNN` | PhaseB_CriticCounts | 0.5616 | 0.4911 +/- 0.0101 | 0.4502 | 0.6596 | 0.6571 | 0.8447 | 0.6327 | 0.8133 / 0.8091 |
| `PhaseB_AblB_Arm4CriticPrefixed_BaseText_LogReg` | PhaseB_CriticPrefixed | 0.4578 | 0.4523 | 0.4076 | 0.6574 | 0.6397 | 0.8355 | 0.6510 | 0.7989 / 0.7957 |
| `PhaseB_AblB_Arm4CriticPrefixed_EarlyMLP` | PhaseB_CriticPrefixed | 0.4911 | 0.4567 +/- 0.0051 | 0.4132 | 0.6525 | 0.6440 | 0.8523 | 0.6317 | 0.8206 / 0.8178 |
| `PhaseB_AblB_Arm4CriticPrefixed_ConcatDirGNN` | PhaseB_CriticPrefixed | 0.5561 | 0.4723 +/- 0.0118 | 0.4299 | 0.6566 | 0.6520 | 0.8412 | 0.6497 | 0.8152 / 0.8135 |
| `PhaseB_AblC_CombinedCriticCountsAndPrefixed_EarlyMLP` | PhaseB_CombinedCritic | 0.5465 | 0.4661 +/- 0.0108 | 0.4239 | 0.6492 | 0.6426 | 0.8496 | 0.6325 | 0.8215 / 0.8185 |
| `PhaseB_AblC_CombinedCriticCountsAndPrefixed_ConcatDirGNN` | PhaseB_CombinedCritic | 0.5544 | 0.4831 +/- 0.0092 | 0.4417 | 0.6538 | 0.6501 | 0.8369 | 0.6495 | 0.8125 / 0.8104 |
| `Exploratory_AllV12Evidence_EarlyMLP` | Exploratory_Combined | 0.5563 | 0.4667 +/- 0.0118 | 0.4267 | 0.6332 | 0.6336 | 0.8327 | 0.6759 | 0.8166 / 0.8150 |
| `Exploratory_AllV12Evidence_ConcatDirGNN` | Exploratory_Combined | 0.5388 | 0.4701 +/- 0.0065 | 0.4293 | 0.6429 | 0.6401 | 0.8246 | 0.6779 | 0.8114 / 0.8107 |

## 2. Phase C Targeted Error Analysis (5-Seed Averages on `test N = 788`)

| Model | R7 F1 (`n=27`) | R7->R9 Err (`mean /27`) | R3<->R4 Err | R4<->R5 Err | ZQ All (`63`) F1 / Acc | ZQ Conn (`25`) F1 / Acc | ZQ Iso (`38`) F1 / Acc |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `PhaseA_ExpA_Arm4_BaseText_LogReg` | 0.1622 | 21.0 | 83.0 | 35.0 | 0.2217 / 0.6349 | 0.1067 / 0.6538 | 0.2426 / 0.6216 |
| `PhaseA_ExpA_Arm4_EarlyMLP` | 0.0276 | 24.0 | 75.2 | 34.8 | 0.2294 / 0.6381 | 0.1237 / 0.6615 | 0.2511 / 0.6216 |
| `PhaseA_ExpA_Arm4_ConcatDirGNN` | 0.2185 | 20.2 | 73.4 | 32.6 | 0.2731 / 0.6635 | 0.2317 / 0.7231 | 0.2526 / 0.6216 |
| `PhaseA_ExpB_Arm4PlusM1Bios_BaseText_LogReg` | 0.2222 | 18.0 | 79.0 | 39.0 | 0.2303 / 0.6190 | 0.1213 / 0.5769 | 0.2677 / 0.6486 |
| `PhaseA_ExpB_Arm4PlusM1Bios_OOFTextOnly_MLP` | 0.1407 | 18.2 | 69.2 | 43.6 | 0.2083 / 0.6032 | 0.1017 / 0.5615 | 0.2606 / 0.6324 |
| `PhaseA_ExpB_Arm4PlusM1Bios_EarlyMLP` | 0.1545 | 17.8 | 74.0 | 38.0 | 0.2230 / 0.6063 | 0.1422 / 0.5846 | 0.2506 / 0.6216 |
| `PhaseA_ExpB_Arm4PlusM1Bios_ConcatDirGNN` | 0.1999 | 15.4 | 75.8 | 39.0 | 0.2414 / 0.5841 | 0.1743 / 0.5308 | 0.2506 / 0.6216 |
| `PhaseA_ExpC_Arm4PlusBookInd_EarlyMLP` | 0.0780 | 22.6 | 79.2 | 36.4 | 0.2479 / 0.6476 | 0.1775 / 0.6846 | 0.2553 / 0.6216 |
| `PhaseA_ExpC_Arm4PlusBookInd_ConcatDirGNN` | 0.2509 | 17.8 | 74.4 | 35.4 | 0.2666 / 0.6444 | 0.2288 / 0.6923 | 0.2533 / 0.6108 |
| `PhaseA_ExpD_Arm4PlusM1BiosAndBookInd_EarlyMLP` | 0.2488 | 15.4 | 77.8 | 40.0 | 0.2289 / 0.6127 | 0.1586 / 0.6077 | 0.2442 / 0.6162 |
| `PhaseA_ExpD_Arm4PlusM1BiosAndBookInd_ConcatDirGNN` | 0.1945 | 16.2 | 74.0 | 37.8 | 0.2492 / 0.6032 | 0.1712 / 0.5692 | 0.2584 / 0.6270 |
| `PhaseB_AblA_Arm4PlusCriticCounts_EarlyMLP` | 0.0523 | 23.2 | 73.2 | 41.2 | 0.2232 / 0.6349 | 0.1067 / 0.6538 | 0.2506 / 0.6216 |
| `PhaseB_AblA_Arm4PlusCriticCounts_ConcatDirGNN` | 0.2885 | 17.8 | 76.2 | 37.8 | 0.2663 / 0.6254 | 0.2029 / 0.6308 | 0.2526 / 0.6216 |
| `PhaseB_AblB_Arm4CriticPrefixed_BaseText_LogReg` | 0.1053 | 22.0 | 82.0 | 41.0 | 0.2451 / 0.6508 | 0.1917 / 0.6923 | 0.2399 / 0.6216 |
| `PhaseB_AblB_Arm4CriticPrefixed_EarlyMLP` | 0.0366 | 23.4 | 73.0 | 41.6 | 0.2389 / 0.6444 | 0.1647 / 0.6769 | 0.2426 / 0.6216 |
| `PhaseB_AblB_Arm4CriticPrefixed_ConcatDirGNN` | 0.1998 | 19.8 | 74.6 | 36.4 | 0.2666 / 0.6381 | 0.2261 / 0.6615 | 0.2466 / 0.6216 |
| `PhaseB_AblC_CombinedCriticCountsAndPrefixed_EarlyMLP` | 0.1225 | 20.8 | 72.2 | 43.8 | 0.2229 / 0.6349 | 0.1054 / 0.6538 | 0.2486 / 0.6216 |
| `PhaseB_AblC_CombinedCriticCountsAndPrefixed_ConcatDirGNN` | 0.2975 | 17.4 | 74.0 | 42.4 | 0.2547 / 0.6159 | 0.1878 / 0.6231 | 0.2451 / 0.6108 |
| `Exploratory_AllV12Evidence_EarlyMLP` | 0.2670 | 14.6 | 68.4 | 48.8 | 0.2621 / 0.6349 | 0.1934 / 0.6692 | 0.2530 / 0.6108 |
| `Exploratory_AllV12Evidence_ConcatDirGNN` | 0.2873 | 14.6 | 68.6 | 45.4 | 0.2583 / 0.6032 | 0.2183 / 0.5846 | 0.2499 / 0.6162 |

## 3. Five-Seed Paired Bootstrap Tests (`2,000` resamples on `test N = 788`)

- **PhaseA_ExpB_M1Bios_ConcatDirGNN_vs_ExpA_Arm4_ConcatDirGNN:** delta Macro-F1 = `-0.0391` (95% CI `[-0.0614, -0.0184]`, p=`0.0000`), delta Acc = `-0.0404` (p=`0.0000`), delta QWK = `-0.0308` (p=`0.0050`)
- **PhaseA_ExpC_BookInd_ConcatDirGNN_vs_ExpA_Arm4_ConcatDirGNN:** delta Macro-F1 = `-0.0086` (95% CI `[-0.0330, +0.0145]`, p=`0.4850`), delta Acc = `-0.0132` (p=`0.1670`), delta QWK = `-0.0081` (p=`0.2280`)
- **PhaseA_ExpD_M1BiosAndBookInd_ConcatDirGNN_vs_ExpA_Arm4_ConcatDirGNN:** delta Macro-F1 = `-0.0296` (95% CI `[-0.0572, -0.0032]`, p=`0.0240`), delta Acc = `-0.0315` (p=`0.0080`), delta QWK = `-0.0237` (p=`0.0770`)
- **PhaseA_ExpD_M1BiosAndBookInd_ConcatDirGNN_vs_ExpD_EarlyMLP:** delta Macro-F1 = `-0.0014` (95% CI `[-0.0246, +0.0217]`, p=`0.9400`), delta Acc = `+0.0157` (p=`0.0750`), delta QWK = `-0.0003` (p=`0.9990`)
- **PhaseB_AblA_CriticCounts_ConcatDirGNN_vs_ExpA_Arm4_ConcatDirGNN:** delta Macro-F1 = `+0.0149` (95% CI `[-0.0051, +0.0363]`, p=`0.1540`), delta Acc = `-0.0066` (p=`0.3700`), delta QWK = `+0.0022` (p=`0.7950`)
- **PhaseB_AblB_CriticPrefixed_ConcatDirGNN_vs_ExpA_Arm4_ConcatDirGNN:** delta Macro-F1 = `-0.0039` (95% CI `[-0.0165, +0.0090]`, p=`0.5580`), delta Acc = `-0.0096` (p=`0.1180`), delta QWK = `-0.0013` (p=`0.8520`)
- **PhaseB_AblC_CombinedCritic_ConcatDirGNN_vs_ExpA_Arm4_ConcatDirGNN:** delta Macro-F1 = `+0.0068` (95% CI `[-0.0151, +0.0282]`, p=`0.5540`), delta Acc = `-0.0124` (p=`0.1370`), delta QWK = `-0.0056` (p=`0.4700`)
- **Exploratory_AllV12Evidence_ConcatDirGNN_vs_ExpA_Arm4_ConcatDirGNN:** delta Macro-F1 = `-0.0061` (95% CI `[-0.0354, +0.0233]`, p=`0.6890`), delta Acc = `-0.0234` (p=`0.0680`), delta QWK = `-0.0179` (p=`0.2150`)
- **Exploratory_AllV12Evidence_ConcatDirGNN_vs_ExpA_BaseTextLogReg:** delta Macro-F1 = `+0.0174` (95% CI `[-0.0224, +0.0558]`, p=`0.3750`), delta Acc = `-0.0208` (p=`0.1680`), delta QWK = `-0.0067` (p=`0.6950`)
