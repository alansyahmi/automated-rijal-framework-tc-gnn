# Task B Consolidated Graph Report v0.2: Method 1 + Method 2 (Sanadset 650k + Bukhari)

**Status:** consolidated classical encyclopedic transmission (`Method 1`: `1716`, `1615`, `4609`, `890`, `1976`) and empirical hadith chains (`Method 2`: `arbml/Sanadset` 650k across 956 books minus Ibn Hajar works + `Bukhari Sultania`) over the frozen `4,830`-node narrator-disjoint Task B splits.

## 1. Scale & Leakage Controls
- Sanadset summary: `{'eligible_hadiths_processed': 429742, 'excluded_ibn_hajar_or_prohibited_book': 7355, 'no_sanad': 158969, 'short_or_invalid_chain': 54920, 'total_rows': 650986}`
- Method 1 biographies parsed & linked: `{'method1_tahdhib_alkamal': 4835, 'method1_jarh_tadil': 192, 'method1_kamil': 1, 'method1_tarikh_kabir': 43}`
- Distinct directed edges across high-confidence Task A nodes: **49596** (**23386** with both endpoints inside `N=4,830` eligible cohort)
- Overall non-isolated eligible narrators: **3684 / 4830** (`76.3%`, up from `27.2%` in `v0.1`)

## 2. Rank-by-Rank Graph Connectivity (`Bukhari-only` vs. `Method 1` vs. `Method 2 Sanadset` vs. `Consolidated`)
- Rank **1** (N=373): Bukhari=46 (12.3%) | M1_Rijal=144 (38.6%) | M2_Sanadset=216 (57.9%) | **Consolidated=235 (63.0%)**
- Rank **2** (N=250): Bukhari=175 (70.0%) | M1_Rijal=173 (69.2%) | M2_Sanadset=209 (83.6%) | **Consolidated=227 (90.8%)**
- Rank **3** (N=1640): Bukhari=551 (33.6%) | M1_Rijal=1120 (68.3%) | M2_Sanadset=1224 (74.6%) | **Consolidated=1370 (83.5%)**
- Rank **4** (N=1083): Bukhari=115 (10.6%) | M1_Rijal=666 (61.5%) | M2_Sanadset=730 (67.4%) | **Consolidated=821 (75.8%)**
- Rank **5** (N=577): Bukhari=97 (16.8%) | M1_Rijal=410 (71.1%) | M2_Sanadset=446 (77.3%) | **Consolidated=474 (82.1%)**
- Rank **6** (N=91): Bukhari=0 (0.0%) | M1_Rijal=52 (57.1%) | M2_Sanadset=53 (58.2%) | **Consolidated=60 (65.9%)**
- Rank **7** (N=114): Bukhari=0 (0.0%) | M1_Rijal=44 (38.6%) | M2_Sanadset=56 (49.1%) | **Consolidated=66 (57.9%)**
- Rank **8** (N=302): Bukhari=2 (0.7%) | M1_Rijal=190 (62.9%) | M2_Sanadset=218 (72.2%) | **Consolidated=232 (76.8%)**
- Rank **9** (N=288): Bukhari=1 (0.3%) | M1_Rijal=85 (29.5%) | M2_Sanadset=105 (36.5%) | **Consolidated=118 (41.0%)**
- Rank **10** (N=91): Bukhari=0 (0.0%) | M1_Rijal=57 (62.6%) | M2_Sanadset=65 (71.4%) | **Consolidated=69 (75.8%)**
- Rank **11** (N=5): Bukhari=0 (0.0%) | M1_Rijal=4 (80.0%) | M2_Sanadset=4 (80.0%) | **Consolidated=4 (80.0%)**
- Rank **12** (N=16): Bukhari=1 (6.2%) | M1_Rijal=6 (37.5%) | M2_Sanadset=6 (37.5%) | **Consolidated=8 (50.0%)**
