# Comparison: `taqrib-oriented-v2` (`b8dd2d4`) vs. `taqrib-oriented-simplified`

**Baseline Snapshot:** `taqrib-oriented-v2` at `b8dd2d4` (untouched)  
**Simplified Build:** `taqrib-oriented-simplified` (`DEC-011`, `DEC-012`, `layer_rules_v3.json` `schema_version = 3.1`)  

---

## 1. Core Verification: Ordinal Targets & Splits Preserved

| Check | `b8dd2d4` (`v2`) | `simplified` (`v3.1`) | Status |
|---|---:|---:|---|
| Total rows (`LAYERED_SCORES_WIDE_V3.csv`) | 8,827 | 8,827 | Identical |
| Total evidence rows (`LAYER_EVIDENCE_LONG_V3.csv`) | 19,447 | 19,432 | Guard-excluded matches tracked (`35` non-numeric rows) |
| Ordinal targets & status (`rank_B`, `rank_E2`, `status_B`, `status_E2`, `split`) | `5,046 / 1,086 / 1,077` (`first_grade = 211`) | `5,046 / 1,086 / 1,077` (`first_grade = 211`) | **100% Bit-Identical** |
| Stage 2 ESA & Stage 3 TC-GNN validity | Trained on `rank_E2` / `shift_class` | Zero target/split changes | **No Retraining Needed** |

---

## 2. Rule-Level & Score Differences

| Quantity | `b8dd2d4` (`v2`) | `simplified` (`v3.1`) | Why It Changed (`DEC-011`, `DEC-012`) |
|---|---:|---:|---|
| `status_E1 == "observed"` (numeric adjustments) | `231` | **`91`** (`92` firings; `-140`) | `DEC-011` moved `22` outside-span `praise_faqih` + zero-weight items to `0.0` descriptive evidence (`119`); `DEC-012` excluded `35` Arabic false positives (negations `لا يدلس`, third-party errors `أخطأ من عده في الصحابة`, teacher confusion `E5986`, mitigated *ikhtilāṭ* `E0191`/`E0911`, refuted `وهم من لينه` `E7793`), preserving all `9` genuine `qual_yukhti_yahim` entries. |
| Narrators with changed `score_E1` | — | **`140`** | `local_band_half_width` bounds + zeroed praise weights + syntactic guards (`DEC-011`, `DEC-012`). |
| Narrators with changed `score_E2` | — | **`121`** | `18` removed `E₁ → E₂` inheritance on band replacements + `103` silent-continuity propagation of cleaner `score_E1` (`DEC-011`, `DEC-012`). |

---

## 3. Empirical Metrics Delta (Safeguard-Checked)

| Metric | `b8dd2d4` (`v2`) | `simplified` (`v3.1`) | Difference |
|---|---:|---:|---|
| Clean test `Exp_B_Qualifiers_E1_Det` Rank MAE | `0.7248` | `0.7244` | `-0.0004` |
| Clean test `Exp_B_Qualifiers_E1_Det` R6 MAE | `1.9786` | `1.9783` | `-0.0003` |
| Clean test `Exp_B_Qualifiers_E1_Det` QWK / 3T-MF1 | `0.8603` / `0.6980` | `0.8603` / `0.6980` | `0.0000` |
| `E₁` sensitivity (`default / halved / doubled / off`) MAE | — | `0.7244 / 0.7238 / 0.7254 / 0.7233` | Strictly inside `±0.0021`; `3T-MF1 = 0.6980` invariant |
| *al-Kāshif* `paired_clean` `E₁` (`N = 1,994`) 3T-Acc / QWK / 5T-Spearman | `0.6836 / 0.6796 / 0.7245` | `0.6836 / 0.6796 / 0.7249` | `+0.0004` Spearman |
| *al-Kāshif* `paired_clean` `E₂` (`N = 1,994`) 3T-Acc / QWK / 5T-Spearman | `0.6690 / 0.6757 / 0.7520` | `0.6690 / 0.6757 / 0.7528` | `+0.0008` Spearman |

### Methodological Interpretation (Safeguard)

Per [notes/v2_charter_audit.md](v2_charter_audit.md) §4, the tiny empirical metric differences above (`≤ 0.0007`) are **not** used as proof that `v3.1` is "better" in accuracy. Rather, `taqrib-oriented-simplified` establishes **methodological defensibility** (scale-local bounds never crossing `80 / 50 / 25` thresholds, zero praise-to-reliability overreach, and zero hidden inheritance across distinct scholarly sources) while preserving identical discrete labels, clean evaluation splits, and all Stage 2 / Stage 3 neural conclusions.
