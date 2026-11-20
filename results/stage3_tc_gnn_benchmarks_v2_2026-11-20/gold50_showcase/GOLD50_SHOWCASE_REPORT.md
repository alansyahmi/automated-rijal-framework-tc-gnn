# Gold-50 Well-Known Narrators: Two-Score Showcase Report

- **Matched in `FINAL_TWO_SCORE_RIJAL_REPRESENTATION_8827.csv`:** 49 / 50
- **Unmatched Gold-50 entry (`1`):** `EXTERNAL-SH12587` (Amr ibn Shimr al-Ju'fi)
- **Gold-50 vs. Taḥrīr (`n=47` ranked):** MAE = **0.3900**, Binary *Taʿdīl*/*Jarḥ* Acc = **95.74%**
- **Held-Out Gold-50 `[TEST]` Subset (`n=10`):** MAE = **0.3702**, Binary *Taʿdīl*/*Jarḥ* Acc = **100.00%**

## Mean TC-GNN Rank Entropy by Gold-50 Profile

| Profile | N | Mean Rank Entropy |
|---|---:|---:|
| `1_highly_reliable` | 18 | 0.1486 |
| `2_nuanced_mixed` | 17 | 0.2364 |
| `3_criticised_weaker` | 14 | 0.4778 |

## Full Gold-50 Two-Score Table

| Gold ID | Profile | Narrator | Split | Score 1 (Ibn Ḥajar) | Taḥrīr Verdict | Score 2 (TC-GNN Cont.) | Score 2 (Rank) | Pred. Shift | Entropy | TC-Sanad Out |
|---|---|---|---|---:|---:|---:|---:|---|---:|---:|
| `29` | `1_highly_reliable` | Isma'il ibn Ulayyah | `train` | 2 | 2 | 2.133 | 2 | `unchanged` | 0.135 | 16 |
| `6` | `1_highly_reliable` | Abd al-Rahman ibn Mahdi | `test` | 2 | 2 | 2.133 | 2 | `unchanged` | 0.134 | 83 |
| `8` | `1_highly_reliable` | al-Layth ibn Sa'd | `train` | 2 | 2 | 2.137 | 2 | `unchanged` | 0.133 | 103 |
| `23` | `1_highly_reliable` | Hammad ibn Zayd | `test` | 2 | 2 | 2.140 | 2 | `unchanged` | 0.139 | 150 |
| `25` | `1_highly_reliable` | al-Fadl ibn Dukayn | `train` | 2 | 2 | 2.143 | 2 | `unchanged` | 0.138 | 26 |
| `22` | `1_highly_reliable` | Waki' ibn al-Jarrah | `val` | 2 | 2 | 2.143 | 2 | `unchanged` | 0.144 | 49 |
| `26` | `1_highly_reliable` | Abd Allah ibn Wahb | `train` | 2 | 2 | 2.145 | 2 | `unchanged` | 0.144 | 23 |
| `3` | `1_highly_reliable` | Sufyan al-Thawri | `val` | 2 | 2 | 2.145 | 2 | `unchanged` | 0.142 | 58 |
| `2` | `1_highly_reliable` | Shu'bah ibn al-Hajjaj | `test` | 2 | 2 | 2.146 | 2 | `unchanged` | 0.142 | 84 |
| `5` | `1_highly_reliable` | Yahya ibn Sa'id al-Qattan | `train` | 2 | 2 | 2.148 | 2 | `unchanged` | 0.148 | 15 |
| `1` | `1_highly_reliable` | Malik ibn Anas | `train` | 2 | 2 | 2.149 | 2 | `unchanged` | 0.141 | 161 |
| `7` | `1_highly_reliable` | al-Awza'i | `train` | 2 | 2 | 2.149 | 2 | `unchanged` | 0.160 | 15 |
| `28` | `1_highly_reliable` | Jarir ibn Abd al-Hamid | `train` | 2 | 2 | 2.150 | 2 | `unchanged` | 0.155 | 57 |
| `21` | `1_highly_reliable` | Abd Allah ibn al-Mubarak | `train` | 2 | 2 | 2.152 | 2 | `unchanged` | 0.144 | 65 |
| `30` | `1_highly_reliable` | Abu Dawud al-Tayalisi | `val` | 2 | 2 | 2.156 | 2 | `unchanged` | 0.156 | 47 |
| `27` | `1_highly_reliable` | Yazid ibn Harun | `train` | 2 | 2 | 2.159 | 2 | `unchanged` | 0.154 | 157 |
| `4` | `1_highly_reliable` | Sufyan ibn Uyaynah | `train` | 2 | 2 | 2.183 | 2 | `unchanged` | 0.161 | 229 |
| `24` | `1_highly_reliable` | Hammad ibn Salamah | `test` | 2 | 2 | 2.224 | 2 | `unchanged` | 0.203 | 182 |
| `35` | `2_nuanced_mixed` | Ikrimah mawla Ibn Abbas | `val` | 2 | 2 | 2.118 | 2 | `unchanged` | 0.155 | 23 |
| `32` | `2_nuanced_mixed` | Nafi' mawla Ibn Umar | `test` | 2 | 2 | 2.127 | 2 | `unchanged` | 0.144 | 36 |
| `13` | `2_nuanced_mixed` | Qatadah ibn Di'amah | `train` | 2 | 2 | 2.135 | 2 | `unchanged` | 0.138 | 23 |
| `33` | `2_nuanced_mixed` | Amr ibn Dinar | `train` | 2 | 2 | 2.136 | 2 | `unchanged` | 0.140 | 16 |
| `31` | `2_nuanced_mixed` | Muhammad ibn Shihab al-Zuhri | `val` | 2 | 2 | 2.154 | 2 | `unchanged` | 0.153 | 36 |
| `12` | `2_nuanced_mixed` | al-A'mash | `val` | 2 | 4 | 2.165 | 2 | `unchanged` | 0.160 | 38 |
| `34` | `2_nuanced_mixed` | Yahya ibn Abi Kathir | `test` | 2 | 2 | 2.200 | 2 | `unchanged` | 0.193 | 85 |
| `14` | `2_nuanced_mixed` | Hisham ibn Urwah | `train` | 3 | 3 | 3.025 | 3 | `unchanged` | 0.173 | 277 |
| `37` | `2_nuanced_mixed` | Tawus ibn Kaysan | `test` | 3 | 3 | 3.027 | 3 | `unchanged` | 0.115 | 0 |
| `38` | `2_nuanced_mixed` | Mujahid ibn Jabr | `test` | 3 | 3 | 3.032 | 3 | `unchanged` | 0.134 | 30 |
| `39` | `2_nuanced_mixed` | Sufyan ibn Husayn | `train` | 3 | 3 | 3.044 | 3 | `unchanged` | 0.089 | 15 |
| `10` | `2_nuanced_mixed` | Abu Ishaq al-Sabi'i | `train` | 3 | 3 | 3.053 | 3 | `unchanged` | 0.174 | 9 |
| `36` | `2_nuanced_mixed` | Ata ibn Abi Rabah | `train` | 3 | 3 | 3.075 | 3 | `unchanged` | 0.195 | 172 |
| `9` | `2_nuanced_mixed` | Muhammad ibn Ishaq | `train` | 4 | 3 | 3.654 | 4 | `upgraded` | 0.436 | 4 |
| `11` | `2_nuanced_mixed` | Ata ibn al-Sa'ib | `train` | 4 | 3 | 3.903 | 4 | `upgraded` | 0.505 | 85 |
| `15` | `2_nuanced_mixed` | Abd Allah ibn Lahi'ah | `train` | 4 | 7 | 3.974 | 4 | `upgraded` | 0.523 | 88 |
| `40` | `2_nuanced_mixed` | Isma'il ibn Ayyash | `train` | 4 | 4 | 4.297 | 4 | `upgraded` | 0.590 | 108 |
| `17` | `3_criticised_weaker` | al-Harith al-A'war | `excluded_unranked` | *(unranked)* | *(unranked)* | 3.581 | 4 | `unchanged` | 0.676 | 15 |
| `19` | `3_criticised_weaker` | Layth ibn Abi Sulaym | `val` | 4 | 4 | 3.972 | 4 | `upgraded` | 0.548 | 0 |
| `50` | `3_criticised_weaker` | Hisham ibn Sa'd | `train` | 5 | 7 | 4.596 | 5 | `upgraded` | 0.652 | 46 |
| `20` | `3_criticised_weaker` | al-Hajjaj ibn Artah | `train` | 5 | 4 | 5.176 | 5 | `upgraded` | 0.726 | 26 |
| `41` | `3_criticised_weaker` | Muhammad ibn Abd al-Rahman ibn Abi Layla | `train` | 5 | 7 | 6.664 | 7 | `downgraded` | 0.689 | 25 |
| `43` | `3_criticised_weaker` | Abu Bakr ibn Abi Maryam | `val` | 8 | 8 | 7.886 | 8 | `unchanged` | 0.219 | 0 |
| `42` | `3_criticised_weaker` | Isma'il ibn Muslim al-Makki | `train` | 8 | 8 | 7.921 | 8 | `unchanged` | 0.223 | 0 |
| `46` | `3_criticised_weaker` | Salih ibn Bashir al-Murri | `train` | 8 | 8 | 7.937 | 8 | `unchanged` | 0.211 | 1 |
| `18` | `3_criticised_weaker` | Abd al-Rahman ibn Zayd ibn Aslam | `train` | 8 | 8 | 7.944 | 8 | `unchanged` | 0.216 | 34 |
| `16` | `3_criticised_weaker` | Jabir ibn Yazid al-Ju'fi | `test` | 8 | 8 | 7.957 | 8 | `unchanged` | 0.227 | 0 |
| `48` | `3_criticised_weaker` | Muqatil ibn Sulayman | `excluded_unranked` | *(unranked)* | *(unranked)* | 8.232 | 8 | `unchanged` | 0.857 | 6 |
| `47` | `3_criticised_weaker` | Muhammad ibn al-Sa'ib al-Kalbi | `test` | 11 | 11 | 8.371 | 8 | `unchanged` | 0.810 | 4 |
| `45` | `3_criticised_weaker` | Umar ibn Harun al-Balkhi | `train` | 10 | 10 | 9.559 | 10 | `unchanged` | 0.329 | 2 |
| `44` | `3_criticised_weaker` | Abd Allah ibn Muharrar | `train` | 10 | 10 | 9.614 | 10 | `unchanged` | 0.308 | 11 |
| `49` | `3_criticised_weaker` | Amr ibn Shimr al-Ju'fi (`EXTERNAL-SH12587`) | `unmatched` | — | — | — | — | — | — | — |
