# Taqrīb v2 Master Feature + Graph Dataset Report (Stage 1)

- **Generated (UTC):** 2026-11-20 06:51:15Z
- **Total Taqrīb entries (`TAQRIB_V2_MASTER_NODES_8827.csv`):** 8827
- **Core supervised cohort (`in_core_cohort_7258 == 1`):** 7258
- **Total directed edges (`TAQRIB_V2_GRAPH_EDGES.csv`):** 59864
- **Edges with both endpoints in core 7,258:** 36994
- **Pure Sanad/Bukhari edges (`sanad_only_edge == 1`):** 42011

## 1. Zero-Leakage Guarantee
- All textual, *ṭabaqah*, sigil, and qualifier features are extracted strictly from Ibn Ḥajar's *Taqrīb al-Tahdhīb* (`3076`).
- Verified `0` occurrences of `تحرير التقريب` or `•` in `taqrib_text_verbatim`.
- All graph neighbor baseline aggregations (`nbr_out_*`, `nbr_in_*`) use **only Score 1 (`taqrib_rank_bilgin_1_to_12`)**, which precedes *Taḥrīr* (`1417 AH`) — zero Score 2 (`tahrir_rank`) leakage.

## 2. Feature & Graph Coverage
- ***Ṭabaqah* extracted (`tabaqa_1_to_12`):** 8544 / 8827 (96.79%)
- **Canonical sigils extracted (`sigil_tokens_raw`):** 8705 / 8827 (98.62%)
- **Core 7,258 non-isolated in consolidated graph:** 5101 / 7258 (70.28%)
- **Core 7,258 connected via pure Sanad/Bukhari edges:** 4776 / 7258 (65.80%)

## 3. Stratified Split Distribution (seed=42)
| Split | Count | Share of 7,258 |
|---|---:|---:|
| `train` | 5080 | 69.99% |
| `val` | 1089 | 15.00% |
| `test` | 1089 | 15.00% |
| `excluded_unranked` | 1569 | — |

## 4. Core Shift Class Distribution (`Score 1 → Score 2`)
| Shift Class | Count | Share |
|---|---:|---:|
| `unchanged` | 4498 | 61.97% |
| `downgraded` | 1639 | 22.58% |
| `upgraded` | 1121 | 15.45% |

## 5. Rank 6 (*Maqbūl*) Graph Out-Degree Signal Check
- `upgraded` (n=397): `graph_out_ge2` = **51.13%**
- `downgraded` (n=1146): `graph_out_ge2` = **26.09%**
