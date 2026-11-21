# Layered Score Builder Report (v3: Layers B, E1, E2)

- **Total entries:** `8,827`
- **E1 preset:** `default` (multiplier `1.0`, half-width `h = 4.5455`)
- **ASCII `* بل:` / `° بل:` overrides fixed:** `11`
- **Suspect alignments flagged (`E2615/E2616` + collision pairs):** `57`
- **E2 band crossings (`rank_E2 != rank_B`, excluding missing/suspect):** `2,744`

> **Caveat on Rank 1 (*Ṣaḥābah*):** Rank 1 (`score_B = 100.0`) is a status category rather than a graded transmission-precision judgement; downstream experiments report results both with and without Rank 1.

## 1. Status Counts by Layer

| Layer | Status | Count |
|---|---|---:|
| B | `abstained` | 1,565 |
| B | `observed` | 7,262 |
| E1 | `abstained` | 1,565 |
| E1 | `not_applicable` | 7,031 |
| E1 | `observed` | 231 |
| E2 | `abstained` | 1,339 |
| E2 | `missing` | 10 |
| E2 | `observed_agreement` | 4,177 |
| E2 | `observed_dissent` | 2,398 |
| E2 | `observed_first_grade` | 211 |
| E2 | `observed_maqbul_to_r7` | 398 |
| E2 | `observed_no_grade` | 181 |
| E2 | `observed_qualification` | 56 |
| E2 | `suspect_alignment` | 57 |

## 2. Distribution of `delta_E1` and `delta_E2` by Baseline Rank (`rank_B`)

| `rank_B` | `n` | `delta_E1` non-zero | `delta_E1` mean | `delta_E1` min / max | `delta_E2` non-zero | `delta_E2` mean | `delta_E2` min / max |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 450 | 0 | +0.0000 | +0.00 / +0.00 | 4 | -0.6494 | -72.73 / +0.00 |
| 2 | 280 | 27 | -0.0933 | -2.95 / +1.14 | 2 | -0.1313 | -18.18 / +0.00 |
| 3 | 1,734 | 44 | -0.0312 | -4.09 / +1.14 | 103 | -1.2406 | -54.55 / +0.00 |
| 4 | 1,183 | 46 | -0.0586 | -4.09 / +1.14 | 491 | +0.2017 | -45.45 / +11.36 |
| 5 | 597 | 8 | +0.0008 | -1.14 / +1.14 | 472 | -0.6444 | -45.45 / +18.18 |
| 6 | 1,581 | 4 | -0.0032 | -1.82 / +0.00 | 1,533 | -7.9020 | -27.27 / +27.27 |
| 7 | 303 | 1 | -0.0060 | -1.82 / +0.00 | 101 | -2.3939 | -18.18 / +36.36 |
| 8 | 330 | 6 | -0.0234 | -2.27 / +1.14 | 21 | -0.4408 | -18.18 / +9.09 |
| 9 | 683 | 2 | -0.0060 | -2.27 / +0.00 | 17 | +0.5891 | +0.00 / +54.55 |
| 10 | 100 | 2 | -0.0227 | -1.14 / +0.00 | 0 | +0.0000 | +0.00 / +0.00 |
| 11 | 5 | 0 | +0.0000 | +0.00 / +0.00 | 0 | +0.0000 | +0.00 / +0.00 |
| 12 | 16 | 0 | +0.0000 | +0.00 / +0.00 | 0 | +0.0000 | +0.00 / +0.00 |
