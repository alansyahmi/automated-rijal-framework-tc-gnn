# Comparison: `taqrib-oriented-v2` (`b8dd2d4`) vs. `taqrib-oriented-simplified`

**Baseline Snapshot:** `taqrib-oriented-v2` at `b8dd2d4` (untouched)  
**Simplified Build:** `taqrib-oriented-simplified` (`DEC-011`, `layer_rules_v3.json` `schema_version = 3.1`)  

---

## 1. Core Verification: Ordinal Targets & Splits Preserved

| Check | `b8dd2d4` (`v2`) | `simplified` (`v3.1`) | Status |
|---|---:|---:|---|
| Total rows (`LAYERED_SCORES_WIDE_V3.csv`) | 8,827 | 8,827 | Identical |
| Total evidence rows (`LAYER_EVIDENCE_LONG_V3.csv`) | 19,447 | 19,447 | Identical |
| Ordinal targets & status (`rank_B`, `rank_E2`, `status_B`, `status_E2`, `split`) | `5,046 / 1,086 / 1,077` (`first_grade = 211`) | `5,046 / 1,086 / 1,077` (`first_grade = 211`) | **100% Bit-Identical** |
| Stage 2 ESA & Stage 3 TC-GNN validity | Trained on `rank_E2` / `shift_class` | Zero target/split changes | **No Retraining Needed** |

---

## 2. Rule-Level & Score Differences

| Quantity | `b8dd2d4` (`v2`) | `simplified` (`v3.1`) | Why It Changed (`DEC-011`) |
|---|---:|---:|---|
| `status_E1 == "observed"` (numeric adjustments) | `231` | **`119`** (`-112`) | Zero-weight descriptive items (`22` outside-span `praise_faqih` + `qual_qalil_hadith`/`qual_rumiya_bidah`) are retained as `0.0`-delta evidence rows rather than numeric adjustments (`153` `E1-PRAISE_HAFIZ` + `142` `E1-PRAISE_FAQIH` total span matches in `LAYER_EVIDENCE_LONG_V3.csv`). |
| Narrators with changed `score_E1` | — | **`140`** | Switched from fixed `h = 4.5455` (`max |ΔE₁| = 4.09`) to `local_band_half_width` (`max |ΔE₁| = 11.25` at Rank 4 `70 → 45`, while Ranks 8 & 9 cap at `1.5` & `2.0` so no threshold is crossed). |
| Narrators with changed `score_E2` | — | **`121`** | Stopped implicit `E₁ → E₂` inheritance on *Taḥrīr* band replacements (`dissent_carry_e1_ranks = []` and `observed_maqbul_to_r7`). |

---

## 3. Empirical Metrics Delta (Safeguard-Checked)

| Metric | `b8dd2d4` (`v2`) | `simplified` (`v3.1`) | Difference |
|---|---:|---:|---|
| Clean test `Exp_B_Qualifiers_E1_Det` Rank MAE | `0.7248` | `0.7247` | `-0.0001` |
| Clean test `Exp_B_Qualifiers_E1_Det` R6 MAE | `1.9786` | `1.9783` | `-0.0003` |
| Clean test `Exp_B_Qualifiers_E1_Det` QWK / 3T-MF1 | `0.8603` / `0.6980` | `0.8603` / `0.6980` | `0.0000` |
| `E₁` sensitivity (`default / halved / doubled / off`) MAE | — | `0.7247 / 0.7240 / 0.7261 / 0.7233` | Strictly inside `±0.003`; `3T-MF1 = 0.6980` invariant |
| *al-Kāshif* `paired_clean` `E₁` (`N = 1,994`) 3T-Acc / QWK / 5T-Spearman | `0.6836 / 0.6796 / 0.7245` | `0.6836 / 0.6796 / 0.7250` | `+0.0005` Spearman |
| *al-Kāshif* `paired_clean` `E₂` (`N = 1,994`) 3T-Acc / QWK / 5T-Spearman | `0.6690 / 0.6757 / 0.7520` | `0.6690 / 0.6757 / 0.7527` | `+0.0007` Spearman |

### Methodological Interpretation (Safeguard)

Per [notes/v2_charter_audit.md](v2_charter_audit.md) §4, the tiny empirical metric differences above (`≤ 0.0007`) are **not** used as proof that `v3.1` is "better" in accuracy. Rather, `taqrib-oriented-simplified` establishes **methodological defensibility** (scale-local bounds never crossing `80 / 50 / 25` thresholds, zero praise-to-reliability overreach, and zero hidden inheritance across distinct scholarly sources) while preserving identical discrete labels, clean evaluation splits, and all Stage 2 / Stage 3 neural conclusions.
