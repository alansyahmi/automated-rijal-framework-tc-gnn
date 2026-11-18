# Task B Consolidated Graph, Structural Features, and Splits Report v0.3

**Status:** full implementation of all 5 Task B refinements across `N = 5,250` high-confidence narrators (`train=3,674`, `val=788`, `test=788`), unlocking all 6 classical Method 1 books (`1716`, `1615`, `4609`, `890`, `1976`, `1981`), consolidating with `Sanadset 650k` (`429,742` eligible chains) + `Bukhari`, recovering `+420` zero-quote `Majhul`/`Mastur` narrators, and adding explicit structural node features.

## 1. Method 1 + Method 2 Graph Scale
- Method 1 biographies parsed & linked across 6 books: `{'method1_jarh_tadil': 4345, 'method1_kamil': 710, 'method1_tahdhib_alkamal': 4785, 'method1_tarikh_kabir': 3514, 'method1_thiqat_ibn_hibban': 4339, 'method1_thiqat_ijli': 1034}`
- Total directed edges: **59864** (**29197** within `N=5,250` cohort)
- Non-isolated `5,250`-cohort narrators: **3987 / 5,250** (`75.9%`)
- Split counts: `{'test': 788, 'train': 3674, 'val': 788}` (`0` overlap on `entry_id` or `shamela_narrator_id`)

## 2. Rank-by-Rank Connectivity (`N = 5,250` Uncensored Cohort)
- Rank **1** (N=393): Bukhari=49 (12.5%) | M1_Rijal=186 (47.3%) | M2_Sanadset=229 (58.3%) | **Consolidated=249 (63.4%)**
- Rank **2** (N=251): Bukhari=175 (69.7%) | M1_Rijal=184 (73.3%) | M2_Sanadset=212 (84.5%) | **Consolidated=229 (91.2%)**
- Rank **3** (N=1665): Bukhari=551 (33.1%) | M1_Rijal=1229 (73.8%) | M2_Sanadset=1272 (76.4%) | **Consolidated=1420 (85.3%)**
- Rank **4** (N=1130): Bukhari=116 (10.3%) | M1_Rijal=790 (69.9%) | M2_Sanadset=792 (70.1%) | **Consolidated=885 (78.3%)**
- Rank **5** (N=582): Bukhari=97 (16.7%) | M1_Rijal=443 (76.1%) | M2_Sanadset=464 (79.7%) | **Consolidated=492 (84.5%)**
- Rank **6** (N=94): Bukhari=0 (0.0%) | M1_Rijal=62 (66.0%) | M2_Sanadset=58 (61.7%) | **Consolidated=67 (71.3%)**
- Rank **7** (N=178): Bukhari=1 (0.6%) | M1_Rijal=81 (45.5%) | M2_Sanadset=82 (46.1%) | **Consolidated=100 (56.2%)**
- Rank **8** (N=312): Bukhari=2 (0.6%) | M1_Rijal=215 (68.9%) | M2_Sanadset=227 (72.8%) | **Consolidated=238 (76.3%)**
- Rank **9** (N=531): Bukhari=1 (0.2%) | M1_Rijal=182 (34.3%) | M2_Sanadset=186 (35.0%) | **Consolidated=220 (41.4%)**
- Rank **10** (N=93): Bukhari=0 (0.0%) | M1_Rijal=63 (67.7%) | M2_Sanadset=70 (75.3%) | **Consolidated=74 (79.6%)**
- Rank **11** (N=5): Bukhari=0 (0.0%) | M1_Rijal=4 (80.0%) | M2_Sanadset=4 (80.0%) | **Consolidated=4 (80.0%)**
- Rank **12** (N=16): Bukhari=1 (6.2%) | M1_Rijal=6 (37.5%) | M2_Sanadset=7 (43.8%) | **Consolidated=9 (56.2%)**
