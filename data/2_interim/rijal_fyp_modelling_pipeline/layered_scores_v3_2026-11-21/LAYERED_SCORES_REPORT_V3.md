# Layered Score Builder Report (v3: Layers B, E1, E2)

- **Total entries:** `8,827`
- **Rank scale:** `hukm_v1` (Tahrir bare ضعيف below i'tibar: `463`)
- **E1 preset:** `default` (multiplier `1.0`, band_width_mode `local_ordinal_gap`)
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
| E1 | `not_applicable` | 7,143 |
| E1 | `observed` | 119 |
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
| 1 | 450 | 0 | +0.0000 | +0.00 / +0.00 | 4 | -0.6518 | -73.00 / +0.00 |
| 2 | 280 | 21 | -0.1295 | -3.25 / +0.00 | 2 | -0.1805 | -25.00 / +0.00 |
| 3 | 1,734 | 39 | -0.0386 | -4.50 / +0.00 | 105 | -1.7355 | -63.00 / +2.50 |
| 4 | 1,183 | 41 | -0.1743 | -11.25 / +0.00 | 491 | +1.8167 | -48.00 / +21.25 |
| 5 | 597 | 4 | -0.0038 | -0.62 / +0.00 | 472 | +10.4911 | -30.00 / +40.00 |
| 6 | 1,581 | 4 | -0.0017 | -1.00 / +0.00 | 1,533 | +1.7721 | -18.00 / +45.00 |
| 7 | 303 | 1 | -0.0033 | -1.00 / +0.00 | 101 | -0.4333 | -13.00 / +50.00 |
| 8 | 330 | 5 | -0.0089 | -0.75 / +0.00 | 328 | -7.8394 | -15.00 / +5.00 |
| 9 | 683 | 2 | -0.0026 | -1.00 / +0.00 | 17 | +0.3387 | -5.00 / +58.00 |
| 10 | 100 | 2 | -0.0250 | -1.25 / +0.00 | 0 | +0.0000 | +0.00 / +0.00 |
| 11 | 5 | 0 | +0.0000 | +0.00 / +0.00 | 0 | +0.0000 | +0.00 / +0.00 |
| 12 | 16 | 0 | +0.0000 | +0.00 / +0.00 | 0 | +0.0000 | +0.00 / +0.00 |
