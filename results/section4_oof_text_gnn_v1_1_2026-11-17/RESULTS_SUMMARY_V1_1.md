# Section 4 Targeted Experiment v1.1: ConcatDirGNN + Out-of-Fold Sparse TF-IDF LogReg Features

- **Protocol:** 5-fold stratified narrator-disjoint OOF log-probabilities inside `train` (`N=3,674`; `C` and `class_weight` selected solely by `train` OOF Macro-F1); `val` (`N=788`) and `test` (`N=788`) receive predictions from one TF-IDF LogisticRegression model trained exclusively on `train`.

## 1. Model Comparison on Held-Out Test (`N = 788`)

| Model | Val Macro-F1 | Test Macro-F1 (12R) | Test R2-12 Macro-F1 | Test Acc | Test W-F1 | Test QWK | Test MAE | Aux 3-Tier Macro-F1 | Aux 3-Tier Acc |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `BaseText_arm2_v03_all_OOFSelectedLogReg` | 0.4602 | 0.4336 | 0.3901 | 0.6256 | 0.6116 | 0.7758 | 0.7931 | 0.7623 | 0.7652 |
| `OOFTextOnly_arm2_v03_all_MLP` | 0.4831 | 0.4824 +/- 0.0286 | 0.4429 | 0.6327 | 0.6233 | 0.7991 | 0.7759 | 0.7819 | 0.7843 |
| `FusionOOF_arm2_v03_all_PlusTopo_EarlyMLP` | 0.4717 | 0.4315 +/- 0.0049 | 0.3878 | 0.6221 | 0.6109 | 0.8020 | 0.7680 | 0.7832 | 0.7840 |
| `FusionOOF_arm2_v03_all_PlusTopo_VanillaGCN` | 0.3748 | 0.3533 +/- 0.0124 | 0.3129 | 0.5015 | 0.4954 | 0.6866 | 1.1030 | 0.6947 | 0.6982 |
| `FusionOOF_arm2_v03_all_PlusTopo_ConcatDirGNN` | 0.5434 | 0.4502 +/- 0.0073 | 0.4073 | 0.6327 | 0.6267 | 0.8035 | 0.7599 | 0.7759 | 0.7774 |
| `BaseText_arm3_v03_plus_fwaed_OOFSelectedLogReg` | 0.4514 | 0.4283 | 0.3831 | 0.6269 | 0.6112 | 0.7768 | 0.7855 | 0.7652 | 0.7665 |
| `OOFTextOnly_arm3_v03_plus_fwaed_MLP` | 0.5124 | 0.4464 +/- 0.0175 | 0.4029 | 0.6236 | 0.6155 | 0.8099 | 0.7401 | 0.7865 | 0.7860 |
| `FusionOOF_arm3_v03_plus_fwaed_PlusTopo_EarlyMLP` | 0.4953 | 0.4350 +/- 0.0090 | 0.3910 | 0.6195 | 0.6121 | 0.7996 | 0.7675 | 0.7777 | 0.7789 |
| `FusionOOF_arm3_v03_plus_fwaed_PlusTopo_VanillaGCN` | 0.3693 | 0.3675 +/- 0.0127 | 0.3278 | 0.5104 | 0.5065 | 0.6829 | 1.0810 | 0.6951 | 0.6977 |
| `FusionOOF_arm3_v03_plus_fwaed_PlusTopo_ConcatDirGNN` | 0.5438 | 0.4439 +/- 0.0034 | 0.3993 | 0.6277 | 0.6226 | 0.7959 | 0.7693 | 0.7755 | 0.7782 |
| `BaseText_arm4_v03_plus_fwaed_plus_tahdhib_OOFSelectedLogReg` | 0.4811 | 0.4549 | 0.4122 | 0.6650 | 0.6485 | 0.8266 | 0.6536 | 0.8051 | 0.8033 |
| `OOFTextOnly_arm4_v03_plus_fwaed_plus_tahdhib_MLP` | 0.5338 | 0.4659 +/- 0.0034 | 0.4251 | 0.6596 | 0.6529 | 0.8480 | 0.6365 | 0.8359 | 0.8325 |
| `FusionOOF_arm4_v03_plus_fwaed_plus_tahdhib_PlusTopo_EarlyMLP` | 0.5180 | 0.4677 +/- 0.0088 | 0.4261 | 0.6660 | 0.6551 | 0.8490 | 0.6277 | 0.8270 | 0.8239 |
| `FusionOOF_arm4_v03_plus_fwaed_plus_tahdhib_PlusTopo_VanillaGCN` | 0.3772 | 0.3576 +/- 0.0159 | 0.3157 | 0.5218 | 0.5138 | 0.7224 | 1.0038 | 0.7164 | 0.7152 |
| `FusionOOF_arm4_v03_plus_fwaed_plus_tahdhib_PlusTopo_ConcatDirGNN` | 0.5625 | 0.4778 +/- 0.0055 | 0.4365 | 0.6645 | 0.6590 | 0.8400 | 0.6447 | 0.8132 | 0.8112 |

## 2. Quoted (`N=725`) vs Zero-Quote (`N=63`) Subgroup Diagnostics

| Model | Quoted Macro-F1 | Quoted Acc | Zero-Quote Macro-F1 | Zero-Quote Acc |
| :--- | :---: | :---: | :---: | :---: |
| `BaseText_arm2_v03_all_OOFSelectedLogReg` | 0.4366 | 0.6303 | 0.1018 | 0.5714 |
| `OOFTextOnly_arm2_v03_all_MLP` | 0.4348 | 0.6345 | 0.1018 | 0.5714 |
| `FusionOOF_arm2_v03_all_PlusTopo_EarlyMLP` | 0.4258 | 0.6276 | 0.1018 | 0.5714 |
| `FusionOOF_arm2_v03_all_PlusTopo_VanillaGCN` | 0.3732 | 0.5159 | 0.1210 | 0.4603 |
| `FusionOOF_arm2_v03_all_PlusTopo_ConcatDirGNN` | 0.4603 | 0.6400 | 0.1370 | 0.5556 |
| `BaseText_arm3_v03_plus_fwaed_OOFSelectedLogReg` | 0.4305 | 0.6317 | 0.1018 | 0.5714 |
| `OOFTextOnly_arm3_v03_plus_fwaed_MLP` | 0.4438 | 0.6290 | 0.1018 | 0.5714 |
| `FusionOOF_arm3_v03_plus_fwaed_PlusTopo_EarlyMLP` | 0.4211 | 0.6138 | 0.1018 | 0.5714 |
| `FusionOOF_arm3_v03_plus_fwaed_PlusTopo_VanillaGCN` | 0.3795 | 0.5214 | 0.1316 | 0.4762 |
| `FusionOOF_arm3_v03_plus_fwaed_PlusTopo_ConcatDirGNN` | 0.4306 | 0.6262 | 0.1493 | 0.5873 |
| `BaseText_arm4_v03_plus_fwaed_plus_tahdhib_OOFSelectedLogReg` | 0.4564 | 0.6676 | 0.2217 | 0.6349 |
| `OOFTextOnly_arm4_v03_plus_fwaed_plus_tahdhib_MLP` | 0.4714 | 0.6607 | 0.2266 | 0.6508 |
| `FusionOOF_arm4_v03_plus_fwaed_plus_tahdhib_PlusTopo_EarlyMLP` | 0.4688 | 0.6703 | 0.2474 | 0.6508 |
| `FusionOOF_arm4_v03_plus_fwaed_plus_tahdhib_PlusTopo_ConcatDirGNN` | 0.4746 | 0.6676 | 0.2838 | 0.6825 |

## 3. Paired Bootstrap Tests (`2,000` resamples, representative `seed=42` for neural models)

- **Arm2_OOF_ConcatDirGNN_vs_V10_Text_arm2_LinearSVC:** delta Macro-F1 = `+0.0591` (95% CI `[+0.0210, +0.0971]`, p=`0.0030`), delta Acc = `+0.0165` (p=`0.2990`), delta QWK = `+0.0438` (p=`0.0150`)
- **Arm2_OOF_ConcatDirGNN_vs_Arm2_BaseText_LogReg:** delta Macro-F1 = `+0.0287` (95% CI `[-0.0102, +0.0664]`, p=`0.1490`), delta Acc = `+0.0076` (p=`0.6330`), delta QWK = `+0.0290` (p=`0.0800`)
- **Arm2_OOF_ConcatDirGNN_vs_Arm2_OOF_EarlyMLP:** delta Macro-F1 = `+0.0372` (95% CI `[+0.0102, +0.0666]`, p=`0.0060`), delta Acc = `+0.0102` (p=`0.3630`), delta QWK = `-0.0023` (p=`0.8560`)
- **Arm3_OOF_ConcatDirGNN_vs_V10_SVD256_ConcatDirGNN:** delta Macro-F1 = `+0.0194` (95% CI `[-0.0221, +0.0610]`, p=`0.3730`), delta Acc = `+0.0406` (p=`0.0120`), delta QWK = `+0.0632` (p=`0.0000`)
- **Arm3_OOF_ConcatDirGNN_vs_Arm3_BaseText_LogReg:** delta Macro-F1 = `+0.0101` (95% CI `[-0.0278, +0.0476]`, p=`0.5950`), delta Acc = `-0.0038` (p=`0.8180`), delta QWK = `+0.0148` (p=`0.3620`)
- **Arm3_OOF_ConcatDirGNN_vs_Arm3_OOF_EarlyMLP:** delta Macro-F1 = `+0.0152` (95% CI `[-0.0145, +0.0439]`, p=`0.2990`), delta Acc = `+0.0127` (p=`0.2910`), delta QWK = `+0.0083` (p=`0.4810`)
- **Arm3_OOF_ConcatDirGNN_vs_Arm3_OOF_VanillaGCN:** delta Macro-F1 = `+0.0592` (95% CI `[+0.0225, +0.0973]`, p=`0.0010`), delta Acc = `+0.1053` (p=`0.0000`), delta QWK = `+0.1163` (p=`0.0000`)
- **Arm4_OOF_ConcatDirGNN_vs_Arm4_BaseText_LogReg:** delta Macro-F1 = `+0.0322` (95% CI `[-0.0064, +0.0690]`, p=`0.1030`), delta Acc = `+0.0038` (p=`0.8000`), delta QWK = `+0.0143` (p=`0.3160`)
- **Arm4_OOF_ConcatDirGNN_vs_Arm4_OOF_EarlyMLP:** delta Macro-F1 = `+0.0157` (95% CI `[-0.0158, +0.0455]`, p=`0.3240`), delta Acc = `+0.0000` (p=`1.0000`), delta QWK = `-0.0104` (p=`0.3770`)
