# Audit of `taqrib-oriented-v2` Against the Simplified Research Charter

**Branch audited:** `taqrib-oriented-v2` (`b8dd2d4`)  
**Target branch:** `taqrib-oriented-simplified` (`7891432` baseline)  
**Charter reference:** [notes/simplified_research_direction.md](simplified_research_direction.md)  
**Date:** 2026-11-23  

---

## 1. Purpose of This Audit

Before modifying any code on `taqrib-oriented-simplified`, this document classifies every major component of `taqrib-oriented-v2` against the working charter in [notes/simplified_research_direction.md](simplified_research_direction.md) (§4–§9) and records four concrete methodological/code friction points discovered during inspection. `taqrib-oriented-v2` remains frozen intact at `b8dd2d4` as our comparison snapshot.

---

## 2. Component Classification Against Charter §8–§9

| Classification | Components in `taqrib-oriented-v2` (`b8dd2d4`) | Assessment Against Charter |
|---|---|---|
| **Essential** | • `3076 ↔ 8246` deterministic entry alignment (`99.95%`, `extract_tahrir_taqrib_alignment_v1.py`) and explicit `missing` / `suspect_alignment` quarantine (`10` missing, `57` suspect)<br>• Deterministic Layer `B` (`7,262` observed, `1,565` explicit `abstained`) & Layer `E₂` (*Taḥrīr* verdicts) with row-level provenance (`LAYER_EVIDENCE_LONG_V3.csv`)<br>• Versioned `0–100` rank mapping in [common/rank_scale.py](../common/rank_scale.py) (`hukm_v1` anchored on *ṣaḥīḥ* `= 80`, *accepted alone* `= 50`, *iʿtibār* `= 25`, bare `ضعيف` p. 47 `= 22.0`; `linear_v1` preserved for reproducibility)<br>• Non-overwrite `observed_scholarly` (`7,421`) vs. `model_estimate` (`1,406`) separation (`DEC-005`)<br>• Deterministic simple baselines (`Exp_A_Majority_Baseline`, `Exp_A_Baseline_B`, `Exp_A_LookupTable_Baseline`)<br>• Hashing, contract tests, and governance log (`DEC-001`–`DEC-010`) | Directly satisfies Charter §2, §3.1–§3.2, §4, and §8 ("Essential"). |
| **Supporting** | • **Stage 2 ESA (`M0–M3c`):** Earns supporting value via editorial **Shift Macro-F1** (`M3b`: `0.7262` vs. LookupTable `0.6576` & `M3a` `0.6963`) and ungraded **`observed_first_grade`** narrators (`N = 211`: `M3c` `BinAcc = 69.67%` vs. `47.39%` Majority)<br>• **1-hop structural MLP (`G2b`) & `chrono_pruned` homophily audit (`0.0474`):** Tests whether teacher-student topology adds value over non-graph `G0` (`BinAcc = 0.9090` vs. `0.8951`, `p = 0.031`)<br>• ***al-Kāshif* (`1616`) external comparison (`DEC-010`):** `paired_clean` (`N = 1,994` vs. `0.4829` majority floor) + `model_estimate` check (`76.03%` non-Companion `N = 317`) framed as comparative evidence (§7.6)<br>• **v3 Showcases ([visualize_layered_showcases_v3.py](../experiments/visualize_layered_showcases_v3.py)):** Demonstrates ordinal behavior on Gold-50 and test Rank-6 *maqbūl* (`N = 227`) | Keep as **Supporting** per Charter §6 & §8; tighten ESA task phrasing (Conflict #4). |
| **Exploratory** | • **2-hop TC-GNNs (`G4a–G4d`):** Retained strictly as an honest **heterophily negative result** (`G4a` ensemble `MAE = 0.6760` vs. 1-hop `G2b` `0.6558`, `p = 0.000`), consistent with Charter §6 (*"If graph learning does not provide a meaningful and robust improvement over simpler methods, that is a valid research finding"*)<br>• **Layer `E₁` numerical adjustments (`231` rows):** Currently violates three Charter §4.2 / §5 rules (Conflicts #1–#3) and must be converted to an **evidence-first** design with scale-local bounds and zero semantic overreach | Must not be overclaimed; resolve Conflicts #1–#3 before regenerating Track R. |
| **Deferred** | • Additional biographical collections (*Tahdhīb al-Kamāl*, *al-Jarḥ wa-l-Taʿdīl* `1615`)<br>• Fine-grained critic/speaker/span extraction from raw quotes<br>• Probabilistic score calibration & isnād-level *ḥadīth* authentication<br>• Signed or heterophilic GNN architectures (`H2GCN`)<br>• Legacy frozen `v2` standalone scripts (`visualize_gold50_two_score_showcase.py`, `visualize_rank6_maqbul_test_showcase.py`) | Explicitly outside undergraduate scope per Charter §8. |

---

## 3. Four Concrete Conflicts Found in Code & Documentation

1. **Inherited `linear_v1` half-width `h = 4.5455` applied to `hukm_v1` (Charter §4.2 — Ordinal Preservation)**
   - **Location:** [dataset_discovery/target_feasibility/build_layered_scores_v3.py](../dataset_discovery/target_feasibility/build_layered_scores_v3.py) (`lines 190–193`, `336–339`, `518–520`) and [dataset_discovery/target_feasibility/layer_rules_v3.json](../dataset_discovery/target_feasibility/layer_rules_v3.json) (`line 11`).
   - **Issue:** `cap_abs = cap_in_h * h = 4.5455` derives from equal-interval `100 / 22`. On `hukm_v1`, adjacent rank gaps shrink to `5.0` (Ranks 5–8) and **`3.0` (Rank 8 `30.0` → Rank 9 `27.0`)**, and thresholds (`80`, `50`, `25`) sit close to ranks (`Rank 3 = 85`, `Rank 5 = 45`, `Rank 9 = 27`). A `±4.5455` shift can cross an adjacent rank midpoint or push Rank 9 (`27.0`) below the `25.0` *iʿtibār* floor (`27 - 4.5455 = 22.45`, below *Taḥrīr* bare `ضعيف = 22.0`).
2. **Semantic overreach in `E1_PRAISE_PATTERNS` (Charter §5 — "No semantic overreach")**
   - **Location:** `build_layered_scores_v3.py` (`lines 68–71`) and `layer_rules_v3.json` (`lines 37–40`).
   - **Issue:** `praise_hafiz` (`حافظ`) and `praise_faqih` (`فقيه`) currently add `+0.25h` numeric boosts to transmission reliability scores. Per Charter §5, scholarly distinction and jurisprudential expertise are not transmission precision and must remain descriptive evidence (`0.0` numeric delta).
3. **Implicit `E₁ → E₂` inheritance into *Taḥrīr* dissents (Charter §5 — "No hidden inheritance")**
   - **Location:** `build_layered_scores_v3.py` (`lines 439–440` for `agreed_no_bullet` *maqbūl* → R7; `lines 493–501` via `dissent_carry_e1_ranks` for `dissent_bal`) and `layer_rules_v3.json` (`line 51`).
   - **Issue:** *Taqrīb* `E₁` qualifier deltas are implicitly carried into *Taḥrīr*'s `score_E2` unless a regex matches a phrase inside *Taḥrīr*'s comment. Where *Taḥrīr* replaces the rank band (`observed_dissent`, `observed_maqbul_to_r7`), carrying Ibn Ḥajar's qualifier mixes distinct scholarly sources without explicit justification.
4. **Overbroad ESA framing relative to implemented task (Charter §6 — Role of NLP)**
   - **Location:** [README.md](../README.md), [notes/THESIS_MAPPING.md](THESIS_MAPPING.md), [notes/STAGE1_AND_STAGE2_METHODOLOGY.md](STAGE1_AND_STAGE2_METHODOLOGY.md), [notes/RESULTS_AND_DISCUSSION_DRAFT.md](RESULTS_AND_DISCUSSION_DRAFT.md), and Stage 2/P5 summaries.
   - **Issue:** Stage 2 models (`M3b`/`M3c`) predict *Taḥrīr*'s entry-level 12-rank ordinal verdict and 3-class editorial shift from full *Taqrīb* entries (`+ X_meta`); they do **not** segment individual critic spans, attribute quoted speakers, or resolve internal targets. Docs must state **entry-level evaluative stance classification** explicitly.

---

## 4. Methodological Safeguard on Metric Changes

> Changes in downstream metrics (for example, lower or higher agreement between `score_E1` and `score_E2` after removing `E₁ → E₂` inheritance or zeroing praise weights) **do not** prove or disprove the correctness of a rule change. We evaluate **methodological defensibility** (source fidelity, ordinal bounds, absence of hidden inheritance) separately from **empirical performance**.
