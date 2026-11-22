# Stage 2: Evaluative Stance Analysis (ESA) Benchmark Report (v3)

- **Generated (UTC):** 2026-11-22 05:43:10Z
- **Elapsed:** 9842.9s | **Device:** MPS (AMD Radeon / Apple Metal)
- **Clean Cohort (excluding `missing` + `suspect_alignment`):** `train = 5046`, `val = 1086`, `test = 1077`.
- **Taqrīb Abstained / Taḥrīr Graded (`observed_first_grade`) Slice:** `N = 211`.

## 1. Test Split Benchmark Table

| Model | Family | Rank MAE ↓ | QWK ↑ | Exact Acc ↑ | Bin Acc ↑ | 3-Tier MF1 ↑ | Shift MF1 ↑ | Active MF1 ↑ | R6 MAE ↓ |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `M0_Identity_Baseline` | `baseline` | 0.7233 | 0.8603 | 0.6193 | 0.7994 | 0.6980 | 0.2550 | 0.0000 | 1.9780 |
| `M1a_Meta_Linear` | `metadata_only` | 0.7607 | 0.8833 | 0.6119 | 0.9025 | 0.7679 | 0.6957 | 0.6110 | 1.5370 |
| `M1b_Meta_HistGBDT` | `metadata_only` | 0.7194 | 0.8832 | 0.6147 | 0.8877 | 0.7727 | 0.6824 | 0.5799 | 1.5224 |
| `M1c_Meta_RandomForest` | `metadata_only` | 0.7097 | 0.8784 | 0.6240 | 0.8812 | 0.7751 | 0.7166 | 0.6299 | 1.5825 |
| `M2a_TFIDF_Full_Linear` | `tfidf_plus_meta` | 0.8095 | 0.8822 | 0.5237 | 0.8997 | 0.7497 | 0.6996 | 0.6101 | 1.5142 |
| `M2b_TFIDF_Full_HistGBDT` | `tfidf_plus_meta` | 0.7195 | 0.8911 | 0.6221 | 0.8932 | 0.7808 | 0.6917 | 0.5895 | 1.4943 |
| `M2c_TFIDF_NameStripped_Linear` | `name_stripped_ablation` | 0.7891 | 0.8790 | 0.5580 | 0.8932 | 0.7515 | 0.6987 | 0.6088 | 1.5351 |
| `M3a_CAMeLBERT_Sentiment_Plus_Meta` | `generic_sentiment_baseline` | 0.7189 | 0.8865 | 0.6082 | 0.8877 | 0.7704 | 0.6963 | 0.6005 | 1.5576 |
| `M3b_AraBERTv02_Full_DualHead` | `esa_arabic_transformer` | 0.6597 | 0.8892 | 0.6314 | 0.8951 | 0.7919 | 0.7262 | 0.6410 | 1.4946 |
| `M3c_AraBERTv02_NameStripped_DualHead` | `name_stripped_ablation` | 0.6485 | 0.8910 | 0.6425 | 0.9053 | 0.7997 | 0.7183 | 0.6314 | 1.4663 |

## 2. Taqrīb Abstained / Taḥrīr Graded Slice (`observed_first_grade`)

| Model | N | Rank MAE ↓ | QWK ↑ | Exact Acc ↑ | Bin Acc ↑ | 3-Tier MF1 ↑ |
|---|---:|---:|---:|---:|---:|---:|
| `M1a_Meta_Linear` | 211 | 3.4754 | 0.0682 | 0.0900 | 0.4739 | 0.1987 |
| `M1b_Meta_HistGBDT` | 211 | 4.5852 | 0.0096 | 0.0000 | 0.4739 | 0.1607 |
| `M1c_Meta_RandomForest` | 211 | 4.5486 | 0.0132 | 0.0000 | 0.4739 | 0.1607 |
| `M2a_TFIDF_Full_Linear` | 211 | 3.4128 | 0.0938 | 0.1090 | 0.4739 | 0.1976 |
| `M2b_TFIDF_Full_HistGBDT` | 211 | 4.5704 | 0.0023 | 0.0000 | 0.4739 | 0.1607 |
| `M2c_TFIDF_NameStripped_Linear` | 211 | 3.2953 | 0.0881 | 0.1137 | 0.4739 | 0.2083 |
| `M3a_CAMeLBERT_Sentiment_Plus_Meta` | 211 | 4.5450 | 0.0178 | 0.0000 | 0.4739 | 0.1607 |
| `M3b_AraBERTv02_Full_DualHead` | 211 | 1.9893 | 0.3218 | 0.1374 | 0.6730 | 0.3505 |
| `M3c_AraBERTv02_NameStripped_DualHead` | 211 | 2.0599 | 0.2950 | 0.1896 | 0.6967 | 0.3998 |
