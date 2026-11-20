# Stage 2: Semantic Sentiment / Stance Analysis Benchmark Report (v2)

- **Generated (UTC):** 2026-11-20 07:26:18Z
- **Elapsed:** 827.2s | **Device:** CUDA (NVIDIA GeForce RTX 2070 with Max-Q Design)
- **Cohort:** `N = 7,258` (`train = 5,080`, `val = 1,089`, `test = 1,089`), ZERO graph columns & ZERO *Taḥrīr* leakage.

## 1. Test Split Benchmark Table (`N = 1,089`)

| Model | Family | Rank MAE ↓ | QWK ↑ | Exact Acc ↑ | Bin Acc (Wahba) ↑ | Bin w-F1 (Wahba) ↑ | Shift MF1 (StanceEval) ↑ | Active MF1 ↑ | R6 Maqbūl MAE ↓ |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `M0_Identity_Baseline` | `baseline` | 0.7181 | 0.8606 | 0.6208 | 0.7998 | 0.7810 | 0.2553 | 0.0000 | 1.9694 |
| `M1a_Meta_Linear` | `metadata_only` | 0.7572 | 0.8832 | 0.6088 | 0.9027 | 0.9027 | 0.6944 | 0.6107 | 1.5259 |
| `M1b_Meta_HistGBDT` | `metadata_only` | 0.7229 | 0.8831 | 0.6180 | 0.8898 | 0.8884 | 0.6758 | 0.5724 | 1.5206 |
| `M1c_Meta_RandomForest` | `metadata_only` | 0.7068 | 0.8789 | 0.6208 | 0.8815 | 0.8799 | 0.7137 | 0.6273 | 1.5746 |
| `M2a_TFIDF_Full_Linear` | `tfidf_plus_meta` | 0.8079 | 0.8803 | 0.5216 | 0.8972 | 0.8965 | 0.6975 | 0.6070 | 1.5024 |
| `M2b_TFIDF_Full_HistGBDT` | `tfidf_plus_meta` | 0.7281 | 0.8848 | 0.6162 | 0.8889 | 0.8876 | 0.7058 | 0.6104 | 1.5396 |
| `M2c_TFIDF_NameStripped_Linear` | `name_stripped_ablation` | 0.7871 | 0.8801 | 0.5629 | 0.8935 | 0.8929 | 0.6928 | 0.6014 | 1.5242 |
| `M3a_CAMeLBERT_Sentiment_Plus_Meta` | `arabic_transformer` | 0.7252 | 0.8861 | 0.6070 | 0.8861 | 0.8846 | 0.6895 | 0.5886 | 1.5776 |
| `M3b_AraBERTv02_Full_DualHead` | `arabic_transformer` | 0.6600 | 0.8899 | 0.6364 | 0.8916 | 0.8903 | 0.7136 | 0.6208 | 1.5120 |
| `M3c_AraBERTv02_NameStripped_DualHead` | `name_stripped_ablation` | 0.6631 | 0.8868 | 0.6382 | 0.9036 | 0.9037 | 0.7145 | 0.6277 | 1.4762 |
