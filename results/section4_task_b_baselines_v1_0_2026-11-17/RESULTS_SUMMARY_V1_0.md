# Section 4 Task B Baseline and Fusion Evaluation Report (v1.0)

- **Cohort:** `N = 5,250` unique high-confidence narrators (`train=3,674`, `val=788`, `test=788`, zero narrator overlap).
- **Graph:** `29197` consolidated cohort edges (`Method 1 + Sanadset 650k + Bukhari`), `12-rank` edge homophily = `0.2384`, `3-tier` edge homophily = `0.4870`.
- **Device:** `cuda` (`torch 2.12.1+cu126`)
- **Top Held-Out Test Model (12-Rank Macro-F1):** `Fusion_arm3_v03_plus_fwaed_PlusTopo_ConcatDirGNN` (`Macro-F1=0.4272`, `Accuracy=0.5919`, `QWK=0.7396`).

## 1. Held-Out Test Performance Across All Models (`N = 788`)

| Model | Val Macro-F1 | Test Macro-F1 (12R) | Test R2-12 Macro-F1 | Test Acc | Test W-F1 | Test QWK | Test MAE | Aux 3-Tier Macro-F1 | Aux 3-Tier Acc |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `Ref_Dummy_most_frequent` | 0.0401 | 0.0401 | 0.0464 | 0.3173 | 0.1528 | 0.0000 | 1.8832 | 0.2038 | 0.4404 |
| `Ref_Dummy_stratified` | 0.0812 | 0.0763 | 0.0748 | 0.1726 | 0.1732 | -0.0135 | 2.5495 | 0.3239 | 0.3490 |
| `Text_arm1_strict_primary_LinearSVC` | 0.4299 | 0.4003 | 0.3551 | 0.6129 | 0.6061 | 0.7565 | 0.8553 | 0.7653 | 0.7716 |
| `Text_arm2_v03_all_LinearSVC` | 0.4472 | 0.4033 | 0.3583 | 0.6168 | 0.6047 | 0.7610 | 0.8477 | 0.7609 | 0.7678 |
| `Text_arm2_v03_all_LogReg` | 0.4607 | 0.4219 | 0.3773 | 0.6269 | 0.6092 | 0.7780 | 0.7855 | 0.7641 | 0.7665 |
| `Text_arm3_v03_plus_fwaed_LinearSVC` | 0.4271 | 0.4084 | 0.3615 | 0.6307 | 0.6124 | 0.7862 | 0.7678 | 0.7712 | 0.7741 |
| `Text_arm3_v03_plus_fwaed_LogReg` | 0.4570 | 0.4205 | 0.3746 | 0.6269 | 0.6077 | 0.7845 | 0.7779 | 0.7636 | 0.7665 |
| `Text_arm4_v03_plus_fwaed_plus_tahdhib_LinearSVC` | 0.4601 | 0.4166 | 0.3708 | 0.6459 | 0.6327 | 0.8130 | 0.7170 | 0.8010 | 0.8046 |
| `Graph_PureTopo_LinearSVC` | 0.1736 | 0.1638 | 0.1539 | 0.3299 | 0.3037 | 0.2122 | 2.1371 | 0.4498 | 0.4784 |
| `Graph_PureTopo_MLP` | 0.1925 | 0.1860 +/- 0.0045 | 0.1748 | 0.3195 | 0.3121 | 0.2554 | 2.2675 | 0.4807 | 0.4901 |
| `Graph_PureTopo_VanillaGCN` | 0.1950 | 0.1651 +/- 0.0022 | 0.1468 | 0.2980 | 0.2888 | 0.1985 | 2.2759 | 0.4718 | 0.4926 |
| `Graph_PureTopo_ConcatDirGNN` | 0.2228 | 0.2054 +/- 0.0097 | 0.1869 | 0.3315 | 0.3237 | 0.2711 | 2.1579 | 0.4898 | 0.5015 |
| `Fusion_arm2_v03_all_PlusTopo_LinearSVC` | 0.4545 | 0.4070 | 0.3612 | 0.6142 | 0.6032 | 0.7683 | 0.8464 | 0.7588 | 0.7652 |
| `Fusion_arm3_v03_plus_fwaed_PlusTopo_LinearSVC` | 0.4467 | 0.4064 | 0.3606 | 0.6180 | 0.6066 | 0.7641 | 0.8363 | 0.7669 | 0.7728 |
| `Fusion_arm4_v03_plus_fwaed_plus_tahdhib_PlusTopo_LinearSVC` | 0.4602 | 0.4181 | 0.3725 | 0.6434 | 0.6309 | 0.8080 | 0.7272 | 0.7977 | 0.7995 |
| `Fusion_arm2_v03_all_PlusTopo_EarlyMLP` | 0.4643 | 0.3950 +/- 0.0069 | 0.3480 | 0.5508 | 0.5608 | 0.7472 | 0.9619 | 0.7394 | 0.7424 |
| `Fusion_arm2_v03_all_PlusTopo_VanillaGCN` | 0.3641 | 0.3284 +/- 0.0071 | 0.2910 | 0.4426 | 0.4467 | 0.6256 | 1.3195 | 0.6792 | 0.6835 |
| `Fusion_arm2_v03_all_PlusTopo_ConcatDirGNN` | 0.4482 | 0.4130 +/- 0.0121 | 0.3678 | 0.5876 | 0.5782 | 0.7453 | 0.8784 | 0.7350 | 0.7373 |
| `Fusion_arm3_v03_plus_fwaed_PlusTopo_EarlyMLP` | 0.4653 | 0.3889 +/- 0.0158 | 0.3415 | 0.5409 | 0.5499 | 0.7466 | 0.9741 | 0.7348 | 0.7378 |
| `Fusion_arm3_v03_plus_fwaed_PlusTopo_VanillaGCN` | 0.3530 | 0.3264 +/- 0.0013 | 0.2906 | 0.4741 | 0.4721 | 0.6181 | 1.2452 | 0.6687 | 0.6734 |
| `Fusion_arm3_v03_plus_fwaed_PlusTopo_ConcatDirGNN` | 0.4470 | 0.4272 +/- 0.0099 | 0.3841 | 0.5919 | 0.5859 | 0.7396 | 0.8970 | 0.7351 | 0.7376 |
| `Fusion_arm3_v03_plus_fwaed_PlusTopoAndEvid_EarlyMLP` | 0.4558 | 0.4006 +/- 0.0099 | 0.3541 | 0.5881 | 0.5812 | 0.7638 | 0.8756 | 0.7511 | 0.7525 |
| `Fusion_arm3_v03_plus_fwaed_PlusTopoAndEvid_ConcatDirGNN` | 0.4499 | 0.4102 +/- 0.0082 | 0.3651 | 0.5812 | 0.5710 | 0.7394 | 0.8939 | 0.7359 | 0.7365 |

## 2. Subgroup Diagnostic: Primary-Quoted (`N=725`) vs Recovered Zero-Quote (`N=63`) in Held-Out Test

| Model | Quoted Macro-F1 | Quoted Acc | Zero-Quote Macro-F1 | Zero-Quote Acc |
| :--- | :---: | :---: | :---: | :---: |
| `Text_arm2_v03_all_LinearSVC` | 0.4051 | 0.6207 | 0.1018 | 0.5714 |
| `Text_arm3_v03_plus_fwaed_LinearSVC` | 0.4110 | 0.6359 | 0.1018 | 0.5714 |
| `Text_arm4_v03_plus_fwaed_plus_tahdhib_LinearSVC` | 0.4168 | 0.6455 | 0.2266 | 0.6508 |
| `Graph_PureTopo_MLP` | 0.1881 | 0.3145 | 0.0746 | 0.4286 |
| `Graph_PureTopo_VanillaGCN` | 0.1605 | 0.2979 | 0.0607 | 0.3175 |
| `Graph_PureTopo_ConcatDirGNN` | 0.2084 | 0.3352 | 0.0599 | 0.3968 |
| `Fusion_arm3_v03_plus_fwaed_PlusTopo_LinearSVC` | 0.4079 | 0.6221 | 0.1018 | 0.5714 |
| `Fusion_arm3_v03_plus_fwaed_PlusTopo_EarlyMLP` | 0.3865 | 0.5697 | 0.1098 | 0.4127 |
| `Fusion_arm3_v03_plus_fwaed_PlusTopo_VanillaGCN` | 0.3251 | 0.4731 | 0.1087 | 0.3968 |
| `Fusion_arm3_v03_plus_fwaed_PlusTopo_ConcatDirGNN` | 0.4083 | 0.5890 | 0.1242 | 0.5079 |

## 3. Paired Bootstrap Comparisons (`2,000` resamples on `test N=788`)

- **Fusion_arm3_LinearSVC_vs_Text_arm3_LinearSVC:** delta Macro-F1 = `-0.0020` (95% CI `[-0.0179, +0.0124]`, p=`0.8150`), delta Acc = `-0.0127` (p=`0.1630`)
- **Fusion_arm3_ConcatDirGNN_vs_Fusion_arm3_VanillaGCN:** delta Macro-F1 = `+0.0938` (95% CI `[+0.0544, +0.1306]`, p=`0.0000`), delta Acc = `+0.1155` (p=`0.0000`)
- **Fusion_arm3_EarlyMLP_vs_Fusion_arm3_VanillaGCN:** delta Macro-F1 = `+0.0691` (95% CI `[+0.0335, +0.1018]`, p=`0.0000`), delta Acc = `+0.0901` (p=`0.0000`)
- **Text_arm4_vs_Text_arm3_LinearSVC:** delta Macro-F1 = `+0.0081` (95% CI `[-0.0175, +0.0333]`, p=`0.5180`), delta Acc = `+0.0152` (p=`0.2290`)
- **Text_arm3_vs_Text_arm2_LinearSVC:** delta Macro-F1 = `+0.0052` (95% CI `[-0.0101, +0.0205]`, p=`0.5250`), delta Acc = `+0.0140` (p=`0.1360`)
