# Gold-50 Well-Known Narrators: Two-Score Showcase Report (`0–100` Reliability Scale)

- **Scoring Conversion:** $S_{[0,1]}(r) = (12 - r)/11$ and $S_{[0,100]}(r) = 100\,(12 - r)/11$ (`100.0` = Rank 1 *Ṣaḥābah*, `50.0` = *Taʿdīl*/*Jarḥ* boundary $r=6.5$, `0.0` = Rank 12 *Kadhdhāb*).
- **Matched in `FINAL_TWO_SCORE_RIJAL_REPRESENTATION_8827.csv`:** 49 / 50
- **Unmatched Gold-50 entry (`1`):** `EXTERNAL-SH12587` (Amr ibn Shimr al-Ju'fi)
- **Gold-50 vs. Taḥrīr (`n=47` ranked):** `0–100` MAE = **3.55** (Rank MAE = **0.3900**), Binary *Taʿdīl*/*Jarḥ* Acc = **95.74%**
- **Held-Out Gold-50 `[TEST]` Subset (`n=10`):** `0–100` MAE = **3.37**, Binary *Taʿdīl*/*Jarḥ* Acc = **100.00%**

## Mean TC-GNN Rank Entropy by Gold-50 Profile

| Profile | N | Mean Rank Entropy |
|---|---:|---:|
| `1_highly_reliable` | 18 | 0.1486 |
| `2_nuanced_mixed` | 17 | 0.2364 |
| `3_criticised_weaker` | 14 | 0.4778 |

## Full Gold-50 Quantified Two-Score Table (`0–100` & `0–1` Scales)

| Gold ID | Profile | Narrator | Split | Score 1 (`0–100`) | Taḥrīr (`0–100`) | Score 2 (`0–100`) | Score 2 (`0–1`) | Δ (`0–100`) | Pred. Shift | Entropy | Out-Deg |
|---|---|---|---|---:|---:|---:|---:|---:|---|---:|---:|
| `6` | `1_highly_reliable` | Abd al-Rahman ibn Mahdi | `test` | 90.91 | 90.91 | **89.70** | 0.8970 | -1.21 | `unchanged` | 0.134 | 83 |
| `29` | `1_highly_reliable` | Isma'il ibn Ulayyah | `train` | 90.91 | 90.91 | **89.70** | 0.8970 | -1.21 | `unchanged` | 0.135 | 16 |
| `8` | `1_highly_reliable` | al-Layth ibn Sa'd | `train` | 90.91 | 90.91 | **89.67** | 0.8967 | -1.24 | `unchanged` | 0.133 | 103 |
| `23` | `1_highly_reliable` | Hammad ibn Zayd | `test` | 90.91 | 90.91 | **89.64** | 0.8964 | -1.27 | `unchanged` | 0.139 | 150 |
| `25` | `1_highly_reliable` | al-Fadl ibn Dukayn | `train` | 90.91 | 90.91 | **89.61** | 0.8961 | -1.30 | `unchanged` | 0.138 | 26 |
| `22` | `1_highly_reliable` | Waki' ibn al-Jarrah | `val` | 90.91 | 90.91 | **89.60** | 0.8960 | -1.30 | `unchanged` | 0.144 | 49 |
| `26` | `1_highly_reliable` | Abd Allah ibn Wahb | `train` | 90.91 | 90.91 | **89.59** | 0.8959 | -1.32 | `unchanged` | 0.144 | 23 |
| `3` | `1_highly_reliable` | Sufyan al-Thawri | `val` | 90.91 | 90.91 | **89.59** | 0.8959 | -1.32 | `unchanged` | 0.142 | 58 |
| `2` | `1_highly_reliable` | Shu'bah ibn al-Hajjaj | `test` | 90.91 | 90.91 | **89.58** | 0.8958 | -1.33 | `unchanged` | 0.142 | 84 |
| `5` | `1_highly_reliable` | Yahya ibn Sa'id al-Qattan | `train` | 90.91 | 90.91 | **89.56** | 0.8956 | -1.35 | `unchanged` | 0.148 | 15 |
| `28` | `1_highly_reliable` | Jarir ibn Abd al-Hamid | `train` | 90.91 | 90.91 | **89.55** | 0.8955 | -1.36 | `unchanged` | 0.155 | 57 |
| `1` | `1_highly_reliable` | Malik ibn Anas | `train` | 90.91 | 90.91 | **89.55** | 0.8955 | -1.36 | `unchanged` | 0.141 | 161 |
| `7` | `1_highly_reliable` | al-Awza'i | `train` | 90.91 | 90.91 | **89.55** | 0.8955 | -1.36 | `unchanged` | 0.160 | 15 |
| `21` | `1_highly_reliable` | Abd Allah ibn al-Mubarak | `train` | 90.91 | 90.91 | **89.53** | 0.8953 | -1.38 | `unchanged` | 0.144 | 65 |
| `30` | `1_highly_reliable` | Abu Dawud al-Tayalisi | `val` | 90.91 | 90.91 | **89.49** | 0.8949 | -1.42 | `unchanged` | 0.156 | 47 |
| `27` | `1_highly_reliable` | Yazid ibn Harun | `train` | 90.91 | 90.91 | **89.47** | 0.8947 | -1.44 | `unchanged` | 0.154 | 157 |
| `4` | `1_highly_reliable` | Sufyan ibn Uyaynah | `train` | 90.91 | 90.91 | **89.24** | 0.8924 | -1.67 | `unchanged` | 0.161 | 229 |
| `24` | `1_highly_reliable` | Hammad ibn Salamah | `test` | 90.91 | 90.91 | **88.88** | 0.8888 | -2.03 | `unchanged` | 0.203 | 182 |
| `35` | `2_nuanced_mixed` | Ikrimah mawla Ibn Abbas | `val` | 90.91 | 90.91 | **89.84** | 0.8984 | -1.07 | `unchanged` | 0.155 | 23 |
| `32` | `2_nuanced_mixed` | Nafi' mawla Ibn Umar | `test` | 90.91 | 90.91 | **89.75** | 0.8975 | -1.16 | `unchanged` | 0.144 | 36 |
| `13` | `2_nuanced_mixed` | Qatadah ibn Di'amah | `train` | 90.91 | 90.91 | **89.69** | 0.8969 | -1.22 | `unchanged` | 0.138 | 23 |
| `33` | `2_nuanced_mixed` | Amr ibn Dinar | `train` | 90.91 | 90.91 | **89.67** | 0.8967 | -1.23 | `unchanged` | 0.140 | 16 |
| `31` | `2_nuanced_mixed` | Muhammad ibn Shihab al-Zuhri | `val` | 90.91 | 90.91 | **89.51** | 0.8951 | -1.40 | `unchanged` | 0.153 | 36 |
| `12` | `2_nuanced_mixed` | al-A'mash | `val` | 90.91 | 72.73 | **89.41** | 0.8941 | -1.50 | `unchanged` | 0.160 | 38 |
| `34` | `2_nuanced_mixed` | Yahya ibn Abi Kathir | `test` | 90.91 | 90.91 | **89.09** | 0.8909 | -1.82 | `unchanged` | 0.193 | 85 |
| `14` | `2_nuanced_mixed` | Hisham ibn Urwah | `train` | 81.82 | 81.82 | **81.59** | 0.8159 | -0.23 | `unchanged` | 0.173 | 277 |
| `37` | `2_nuanced_mixed` | Tawus ibn Kaysan | `test` | 81.82 | 81.82 | **81.57** | 0.8157 | -0.24 | `unchanged` | 0.115 | 0 |
| `38` | `2_nuanced_mixed` | Mujahid ibn Jabr | `test` | 81.82 | 81.82 | **81.52** | 0.8152 | -0.29 | `unchanged` | 0.134 | 30 |
| `39` | `2_nuanced_mixed` | Sufyan ibn Husayn | `train` | 81.82 | 81.82 | **81.42** | 0.8142 | -0.40 | `unchanged` | 0.089 | 15 |
| `10` | `2_nuanced_mixed` | Abu Ishaq al-Sabi'i | `train` | 81.82 | 81.82 | **81.34** | 0.8134 | -0.48 | `unchanged` | 0.174 | 9 |
| `36` | `2_nuanced_mixed` | Ata ibn Abi Rabah | `train` | 81.82 | 81.82 | **81.14** | 0.8114 | -0.68 | `unchanged` | 0.195 | 172 |
| `9` | `2_nuanced_mixed` | Muhammad ibn Ishaq | `train` | 72.73 | 81.82 | **75.87** | 0.7587 | +3.15 | `upgraded` | 0.436 | 4 |
| `11` | `2_nuanced_mixed` | Ata ibn al-Sa'ib | `train` | 72.73 | 81.82 | **73.61** | 0.7361 | +0.88 | `upgraded` | 0.505 | 85 |
| `15` | `2_nuanced_mixed` | Abd Allah ibn Lahi'ah | `train` | 72.73 | 45.45 | **72.96** | 0.7296 | +0.24 | `upgraded` | 0.523 | 88 |
| `40` | `2_nuanced_mixed` | Isma'il ibn Ayyash | `train` | 72.73 | 72.73 | **70.02** | 0.7002 | -2.70 | `upgraded` | 0.590 | 108 |
| `17` | `3_criticised_weaker` | al-Harith al-A'war | `excluded_unranked` | *(unranked)* | *(unranked)* | **76.54** | 0.7654 | — | `unchanged` | 0.676 | 15 |
| `19` | `3_criticised_weaker` | Layth ibn Abi Sulaym | `val` | 72.73 | 72.73 | **72.98** | 0.7298 | +0.25 | `upgraded` | 0.548 | 0 |
| `50` | `3_criticised_weaker` | Hisham ibn Sa'd | `train` | 63.64 | 45.45 | **67.31** | 0.6731 | +3.67 | `upgraded` | 0.652 | 46 |
| `20` | `3_criticised_weaker` | al-Hajjaj ibn Artah | `train` | 63.64 | 72.73 | **62.03** | 0.6203 | -1.60 | `upgraded` | 0.726 | 26 |
| `41` | `3_criticised_weaker` | Muhammad ibn Abd al-Rahman ibn Abi Layla | `train` | 63.64 | 45.45 | **48.51** | 0.4851 | -15.13 | `downgraded` | 0.689 | 25 |
| `43` | `3_criticised_weaker` | Abu Bakr ibn Abi Maryam | `val` | 36.36 | 36.36 | **37.40** | 0.3740 | +1.04 | `unchanged` | 0.219 | 0 |
| `42` | `3_criticised_weaker` | Isma'il ibn Muslim al-Makki | `train` | 36.36 | 36.36 | **37.08** | 0.3708 | +0.72 | `unchanged` | 0.223 | 0 |
| `46` | `3_criticised_weaker` | Salih ibn Bashir al-Murri | `train` | 36.36 | 36.36 | **36.93** | 0.3693 | +0.57 | `unchanged` | 0.211 | 1 |
| `18` | `3_criticised_weaker` | Abd al-Rahman ibn Zayd ibn Aslam | `train` | 36.36 | 36.36 | **36.87** | 0.3687 | +0.51 | `unchanged` | 0.216 | 34 |
| `16` | `3_criticised_weaker` | Jabir ibn Yazid al-Ju'fi | `test` | 36.36 | 36.36 | **36.76** | 0.3676 | +0.40 | `unchanged` | 0.227 | 0 |
| `48` | `3_criticised_weaker` | Muqatil ibn Sulayman | `excluded_unranked` | *(unranked)* | *(unranked)* | **34.26** | 0.3426 | — | `unchanged` | 0.857 | 6 |
| `47` | `3_criticised_weaker` | Muhammad ibn al-Sa'ib al-Kalbi | `test` | 9.09 | 9.09 | **32.99** | 0.3299 | +23.90 | `unchanged` | 0.810 | 4 |
| `45` | `3_criticised_weaker` | Umar ibn Harun al-Balkhi | `train` | 18.18 | 18.18 | **22.19** | 0.2219 | +4.01 | `unchanged` | 0.329 | 2 |
| `44` | `3_criticised_weaker` | Abd Allah ibn Muharrar | `train` | 18.18 | 18.18 | **21.69** | 0.2169 | +3.51 | `unchanged` | 0.308 | 11 |
| `49` | `3_criticised_weaker` | Amr ibn Shimr al-Ju'fi (`EXTERNAL-SH12587`) | `unmatched` | — | — | — | — | — | — | — | — |
