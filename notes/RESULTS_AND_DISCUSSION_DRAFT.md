# Thesis Draft: Results & Discussion Chapters (`taqrib-oriented-v2`)

> **Scope & Provenance Notice:** All quantitative figures below come directly from the post-audit `taqrib-oriented-v2` runs (`hukm_v1` scale, symmetric *al-Kāshif* `paired_clean`, Stage 2 `AraBERTv02` on AMD Radeon Pro 5500M MPS, Stage 3 `GATv2Conv` `x_l`-fixed `mps_native` on CPU with bit-exact parity `max_abs_diff = 0.0`, and P5/P6 layered evaluation). Pending supervisor sign-off items (`wuththiqa_policy="maqbul_r6"`, PO1–PO3 wording) are noted explicitly.

---

## Chapter 4: Results

### 4.1 Deterministic Layered Representation (Track R) & *Hukm*-Anchored Calibration (`hukm_v1`)

Across the `8,827` narrators of *Taqrīb al-Tahdhīb* (`3076`), Track R decomposes quantitative reliability without learned parameter drift into three auditable layers stored in [LAYERED_SCORES_WIDE_V3.csv](../data/2_interim/rijal_fyp_modelling_pipeline/layered_scores_v3_2026-11-21/LAYERED_SCORES_WIDE_V3.csv) and [FINAL_LAYERED_RIJAL_SCORES_8827_V3.csv](../results/layered_experiments_v3_2026-11-21/FINAL_LAYERED_RIJAL_SCORES_8827_V3.csv):

1. **Layer B (`score_B`):** Maps Ibn Ḥajar's 12 *marātib* onto the classical *ḥadīth*-ruling (`hukm_v1`) `0–100` scale (`100, 95, 85, 70, 45, 40, 35, 30, 27, 15, 5, 0`, anchored at thresholds `80 = ṣaḥīḥ`, `50 = accepted alone`, `25 = usable for iʿtibār` per `DEC-009`), assigning explicit scores to `7,262` narrators and explicitly recording `1,565` abstentions (`abstained`) rather than forcing guesses on conditional or multi-clause entries.
2. **Layer B + E₁ (`score_E1`):** Extracts bounded within-band qualifier adjustments outside the grade span for `231` narrators (`E₁` sensitivity check across `default`, `halved`, `doubled`, and `off` shows zero rank-order changes and identical `3T-Acc = 0.8805` / `QWK = 0.9038` against `score_E2` on `paired_clean`, confirming bounded intra-band expressiveness without distorting *marātib* boundaries).
3. **Layer B + E₁ + E₂ (`score_E2`):** Aligns *Taḥrīr Taqrīb al-Tahdhīb* (`8246`, `8,823 / 8,827 = 99.95%` structural match) to resolve `4,177` scholarly agreements, `2,398` dissents, `398` agreed conditional *maqbūl* narrators moved to rank 7 (*ḍaʿīf yuʿtabaru bih*, `35.0`), `463` bare *ḍaʿīf* entries (`Taḥrīr` p. 47, excluded from *iʿtibār*, assigned `22.0` under `hukm_v1`), and `211` first-time grades where *Taqrīb* abstained (`10` `missing` and `57` `suspect_alignment` rows quarantined). In total, `8,827` narrators comprise `7,421` `observed_scholarly` (`score_E2` preserved untouched) and `1,406` lacking observed *Taḥrīr* where Track L emits a non-overwrite `score_G_estimate` (`source = model_estimate`).

On the Gold-50 qualitative adjudication cohort (`49/50` matched in Bilgin's table) and the unseen clean test Rank-6 *maqbūl* cohort (`N = 227`), `score_E2` cleanly resolves flat baseline ambiguity (`score_B = 40.00` on `hukm_v1`) into upgraded independent *taʿdīl* (`≥ 70.0`), retained rank-6 (`40.0`), rank-7 *iʿtibār* (`35.0`), and uncorroborated rejection (`≤ 22.0`), including Muqātil b. Sulaymān (`E6868` → `0.00`) ([SHOWCASES_REPORT_V3.md](../results/layered_experiments_v3_2026-11-21/showcases/SHOWCASES_REPORT_V3.md)).

---

### 4.2 Stage 2 Evaluative Stance Analysis (ESA) vs. Simple Baselines

To prevent overstated neural gains on largely static entries (where `62%` of *Taqrīb* ranks remain unchanged in *Taḥrīr* and agreed *maqbūl* systematically shifts to rank 7), Table 4.1 evaluates deterministic baselines alongside Stage 2 models (`M0–M3c`) on the clean held-out test set (`N = 1,077`, source: [STAGE2_RESULTS_SUMMARY_V3.md](../results/stage2_esa_benchmarks_v3_2026-11-21/STAGE2_RESULTS_SUMMARY_V3.md), [LAYERED_EXPERIMENTS_REPORT_V3.md](../results/layered_experiments_v3_2026-11-21/LAYERED_EXPERIMENTS_REPORT_V3.md)).

**Table 4.1 — Clean Held-Out Test Set (`N = 1,077`): Baselines & Stage 2 ESA Models**

| Model | Rank MAE ↓ | Rank QWK ↑ | Exact Acc ↑ | Bin Acc (*Taʿdīl/Jarḥ*) ↑ | 3-Tier MF1 ↑ | **Shift MF1 ↑** | Active Shift MF1 ↑ | R6 MAE ↓ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `Exp_A_Majority_Baseline` | 2.4689 | 0.0000 | — | 0.6054 | 0.1927 | 0.2550 | — | 3.9207 |
| `Exp_A_Baseline_B` (`M0_Identity`) | 0.7233 | 0.8603 | 0.6184 | 0.7994 | 0.6980 | 0.2550 | 0.0000 | 1.9780 |
| `Exp_A_LookupTable_Baseline` (`(rank_B, maqbul) -> mode`) | **0.6202** | 0.8749 | — | 0.8988 | 0.7901 | 0.6576 | — | 1.5066 |
| `M1b_Meta_HistGBDT` | 0.7194 | — | — | — | 0.7727 | 0.6824 | — | — |
| `M1c_Meta_RandomForest` | 0.7097 | — | — | — | 0.7751 | 0.7166 | — | — |
| `M2b_TFIDF_Full_HistGBDT` | 0.7195 | **0.8911** | — | — | 0.7808 | 0.6917 | — | 1.4943 |
| `M3a_CAMeLBERT_Sentiment_Plus_Meta` | 0.7189 | 0.8865 | — | 0.8877 | 0.7704 | 0.6963 | — | 1.5576 |
| **`M3b_AraBERTv02_Full_DualHead`** | 0.6597 | 0.8892 | 0.6314 | 0.8951 | 0.7919 | **0.7262** | **0.6410** | 1.4946 |
| **`M3c_AraBERTv02_NameStripped_DualHead`** | 0.6485 | 0.8910 | **0.6425** | **0.9053** | **0.7997** | 0.7183 | — | **1.4663** |

Three empirical findings emerge from Table 4.1:
1. **Static Rank MAE Is Dominated by Priors, Whereas Shift Prediction Needs ESA:** The 2-feature Lookup-Table (`(rank_B, maqbul) -> train mode`) achieves `MAE = 0.6202` and `3T-MF1 = 0.7901` without neural text modelling, showing that raw Rank MAE alone conflates static copying (`M0`: `61.84%` exact match) with editorial revision detection. When isolating **editorial Shift Macro-F1**, `AraBERTv02` DualHead (`M3b`) improves to **`0.7262`** (`+6.86 pp` over the Lookup-Table's `0.6576`, `+47.12 pp` over `Majority`/`M0` `0.2550`, and `+2.99 pp` over zero-shot generic Arabic sentiment `M3a` at `0.6963`).
2. **Evaluative Stance Exceeds Generic Sentiment and Resists Name Memorization:** Removing narrator names/lineages (`M3c`) improves `Rank MAE` (`0.6597 → 0.6485`), `BinAcc` (`0.8951 → 0.9053`), `3T-MF1` (`0.7919 → 0.7997`), and `R6 MAE` (`1.4946 → 1.4663`), demonstrating that Classical Arabic evaluative clues—not proper-name memorization—drive predictions.
3. **Resolving *Taqrīb*-Abstained Narrators (`observed_first_grade`, `N = 211`):** On held-out entries where Ibn Ḥajar abstained (`score_B` unavailable) and *Taḥrīr* supplied an original grade, the Majority baseline (`M1b`/`M1c`/`M2b`/`M3a` also collapse to majority) achieves `BinAcc = 0.4739`, `3T-Acc = 0.3175`, `3T-MF1 = 0.1607`, and `Exact = 0.0000`. Fine-tuned transformers recover meaningful signal (`M3c`: **`BinAcc = 0.6967`**, **`3T-MF1 = 0.3998`**, **`Exact = 0.1896`**; `M3b`: `BinAcc = 0.6730`, `3T-MF1 = 0.3505`, `QWK = 0.3218`).

---

### 4.3 Stage 3 TC-GNN Ablations & Graph Heterophily (CPU `mps_native`, Bit-Exact Parity)

After fixing the `MPSGATv2Conv` message indexing bug (`x_l.index_select(0, src)` matching PyG `max_abs_diff = 0.0` across all 3 parity tests) and benchmarking CPU vs. MPS (`2,908 ms/epoch` on 8-thread CPU vs. `13,126 ms/epoch` on Radeon MPS—a **4.5× speedup** via `bench_stage3_devices.py`), Stage 3 was re-executed end-to-end across 5 random seeds in `4,537.3 s` ([STAGE3_RESULTS_SUMMARY_V3.md](../results/stage3_tc_gnn_benchmarks_v3_2026-11-21/STAGE3_RESULTS_SUMMARY_V3.md)).

First, structural homophily measurement on `chrono_pruned` (`42,011 → 37,364` pure-*sanad* edges; `4,647` chronologically invalid edges pruned) reveals **strong transmission heterophily**: `score_E2` 12-rank edge homophily is **`0.2725`** and class homophily is **`0.0474`** (3-tier edge homophily **`0.5316`**, class homophily **`0.1477`**). Reliable (*thiqah*) masters frequently transmit to weak students and vice versa. Table 4.2 summarizes the controlled Stage 3 ablations (`N = 1,077`).

**Table 4.2 — Stage 3 TC-GNN Ablation Summary (`N = 1,077` Clean Test, 5 Seeds & Ensemble)**

| Model / Graph Arm | 5-Seed Mean MAE ± SD | Ens MAE ↓ | Ens QWK ↑ | Ens BinAcc ↑ | Ens 3T-MF1 ↑ | **Ens Shift MF1 ↑** | Ens R6 MAE ↓ |
|---|---|---:|---:|---:|---:|---:|---:|
| `G0` (`NoGraph`, `M3b` Stage 2 OOF) | — | 0.6597 | 0.8892 | 0.8951 | 0.7919 | 0.7262 | 1.4946 |
| `G1_GraphOnly_NoText` (`chrono_pruned`) | 1.3331 ± 0.0133 | — | 0.7087 | 0.8162 | 0.6517 | 0.5392 | — |
| **`G2b_Sem_Plus_SanadStruct_MLP` (1-hop, no GNN)** | **0.6577 ± 0.0038** | **0.6558** | 0.8877 | **0.9090** | 0.7957 | 0.7247 | 1.4713 |
| `G4a_Directed_TC_GNN_Sanad` (`chrono_pruned`) | 0.6784 ± 0.0172 | 0.6760 | 0.8861 | 0.9062 | 0.7983 | 0.7240 | 1.4750 |
| `G4b_Directed_TC_GNN_UnprunedSanad` (`42,011` edges) | 0.6900 ± 0.0156 | 0.6866 | 0.8842 | 0.9034 | 0.7924 | 0.7156 | 1.4956 |
| `G4c_MV_TC_GNN_Sanad_Plus_kNN` (multi-view) | 0.6846 ± — | 0.6821 | 0.8834 | 0.9053 | 0.7929 | 0.7259 | — |
| **`G4d_Directed_TC_GNN_Consolidated`** (`59,864` edges) | 0.6626 ± 0.0055 | 0.6613 | **0.8925** | 0.9081 | **0.7999** | **0.7320** | **1.4563** |

Paired bootstrap significance tests ($B = 2{,}000$, [STAGE3_SUBGROUP_AND_SIGNIFICANCE_V3.csv](../results/stage3_tc_gnn_benchmarks_v3_2026-11-21/STAGE3_SUBGROUP_AND_SIGNIFICANCE_V3.csv)) establish three balanced conclusions:
- **Explicit Heterophily Negative Result:** Comparing 2-hop GNN message passing (`G4a`) directly against the 1-hop structural-feature baseline (`G2b`), `G4a` suffers higher `Rank MAE` (`0.6760` vs. `0.6558`, `p = 0.000`) with no significant `3T-MF1` (`0.7983` vs. `0.7957`, `p = 0.601`) or `Shift MF1` (`0.7240` vs. `0.7247`, `p = 0.955`) gain. Simply adding 1-hop summary degrees and rank statistics (`G2b`) outperforms multi-hop smoothing (`p = 0.031` binary accuracy gain over `G0`: `0.9090` vs. `0.8951`).
- **Chronology Pruning Preserves Shift Signal:** Removing `4,647` anachronistic edges reduces error and raises ensemble `Shift MF1` (`G4a` `0.7240` vs. unpruned `G4b` `0.7156`; `MAE` `0.6760` vs. `0.6866`).
- **Consolidated Topology Gains Only in Secondary Metrics:** With the full `59,864`-edge consolidated graph, `G4d` improves ensemble `QWK` over `G2b` (`0.8925` vs. `0.8877`, `p = 0.032`) and achieves the numerically highest ensemble `Shift MF1` (`0.7320`, `p = 0.293` vs. `G2b` — non-significant) and lowest `R6 MAE` (`1.4563`), while still trailing `G2b` slightly on `MAE` (`0.6613` vs. `0.6558`, `p = 0.288`).

---

### 4.4 Independent External Validation Against *al-Kāshif* (`1616`) & Ungraded Narrators

Under the audited *al-Kāshif* protocol ([build_kashif_validation_v1.py](../dataset_discovery/target_feasibility/build_kashif_validation_v1.py), `DEC-010`: `5,640` linked, `3,706` mapped, `wuththiqa_policy="maqbul_r6"`, low-precision `n2`/`n3_sigil_subset` links removed, symmetric overlap checked in both *Taqrīb* and *Taḥrīr* [`1,169` rows], and `549` *Taḥrīr* citations of al-Dhahabī tracked):

1. **Clean Paired Comparison (`paired_clean`, `N = 1,994`):** Excluding all verbatim overlaps and al-Dhahabī citations removes the spurious `+11.65 pp` artifact from earlier asymmetric filtering. Against a **`0.4829` majority-class floor**, both *Taqrīb* `score_B` (`3T-Acc = 0.6836`, `3T-MF1 = 0.6932`, `3T-QWK = 0.6796`, `5T-QWK = 0.7557`, `5T-Spearman = 0.7248`) and *Taḥrīr* `score_E2` (`3T-Acc = 0.6690`, `p = 0.1220`; `3T-MF1 = 0.6510`, `p = 0.0000`; `3T-QWK = 0.6757`, `p = 0.6860`; `5T-QWK = 0.7542`, `p = 0.8100`; `5T-Spearman = 0.7520`, `Δ = +0.0272`, `p = 0.0000`) exhibit substantial convergent agreement (`+18.6–20.1 pp` above majority).
2. **Grading Unannotated / Missing-*Taḥrīr* Narrators (`Exp_D_G4a_EstimateOnly`):** On narrators where *Taḥrīr* supplied no mapped grade (`source = model_estimate`, `N = 1,406` overall; mapped in *al-Kāshif*: `402` overall, `317` excluding *Ṣaḥābah*, `300` non-verbatim), `G4a`'s non-overwrite `score_G_estimate` achieves:
   - **`all_excl_sahabi` (`N = 317`):** **`76.03%`** (`0.7603`) 3-tier accuracy (`+20.51 pp` over the `55.52%` majority floor), `3T-MF1 = 0.6889`, `3T-QWK = 0.8024`, `5T-QWK = 0.7361`, `Spearman = 0.6743`. *(Note: prior to the CPU `x_l` GATv2 parity fix, the provisional MPS figure on the pre-fix run was `76.66%`.)*
   - **`all_observed` (`N = 402`):** **`80.85%`** (`0.8085`) 3-tier accuracy (`+15.92 pp` over the `64.93%` majority floor), `3T-MF1 = 0.7023`, `3T-QWK = 0.8161`, `5T-QWK = 0.8026`, `Spearman = 0.7807`.
   - **`non_verbatim` (`N = 300`):** **`78.00%`** (`0.7800`) 3-tier accuracy (`+18.67 pp` over the `59.33%` majority floor), `3T-MF1 = 0.6874`, `3T-QWK = 0.8063`, `5T-QWK = 0.7778`, `Spearman = 0.7462`.
   - **`observed_first_grade` Subset (`N = 77`):** `59.74%` agreement (`3T-MF1 = 0.5620`, `3T-QWK = 0.5944`) vs. `51.95%` majority floor.

---

## Chapter 5: Discussion

### 5.1 Why Evaluative Stance Succeeds Where Generic Sentiment and Lookup Tables Stop

Two common failure modes in computational humanities are (i) equalling static label copying with NLP skill and (ii) equating domain-specific stance with generic sentiment polarity. Our added baselines confirm both risks: because `~62%` of *Taḥrīr* entries affirm Ibn Ḥajar (`unchanged`) and agreed *maqbūl* maps deterministically to rank 7, a trivial 2-key lookup table reaches `0.6202` Rank MAE. Evaluating only Rank MAE would falsely suggest transformers add little (`0.6485–0.6597` MAE). Shifting evaluation to **editorial revision detection (`Shift Macro-F1`)** and **ungraded narrators (`observed_first_grade` and `model_estimate`)** isolates the true textual value of Stage 2 ESA: `AraBERTv02` (`0.7262` Shift MF1; `0.6967` Binary Acc on `observed_first_grade`) extracts nuanced technical verdicts—such as implicit weaknesses inside conditional formulations, isnād-scope qualifiers, and editorial tension markers—that neither generic social-media sentiment (`CAMeLBERT` `M3a`, `0.6963`) nor metadata trees (`0.6824–0.7166`) capture. The name-stripped ablation (`M3c`, `0.6485` MAE, `0.9053` BinAcc) confirms these gains come from classical terminology rather than overfitting to prominent narrator names.

### 5.2 Transmission-Network Heterophily as a Substantive Scientific Finding

A naive graph hypothesis in *ʿIlm ar-Rijāl* assumes "guilt (or trustworthiness) by association"—that reliable narrators primarily transmit to reliable narrators. Our homophily audit refutes this mathematically on the *Taqrīb* *sanad* graph: 12-rank class homophily is near zero (`0.0474`, edge homophily `0.2725`). Historically and pedagogically, major *imām*s taught vast circles that inevitably included weak or opportunistic students (*ḍuʿafāʾ*), while even criticized transmitters occasionally relayed material from towering masters (requiring scholars to test corroboration rather than propagate global node reliability). Consequently:
1. Smooth 2-hop neighborhood averaging (`G4a`, `G4b`, `G4c`) degrades ordinal point accuracy relative to a non-message-passing 1-hop summary MLP (`G2b`: `0.6558` vs. `G4a`: `0.6760` MAE, `p = 0.000`), constituting a clean, instructive **heterophily negative result**.
2. Structural summary features—such as pure-*sanad* student count and corroborating teacher count (`G2b` `BinAcc = 0.9090`, `p = 0.031` vs. `G0`)—directly mirror *ḥadīth* methodology (*iʿtibār* / *mutābaʿāt* availability) without smoothing dissimilar neighbors' ranks together.
3. Chronological pruning (`chrono_pruned`, `-4,647` edges) and consolidated connectivity (`G4d`) help stabilize shift classification and QWK (`0.8925`), indicating that graph value lies in schema-aware structural diagnostics and non-overwrite estimation (`source = model_estimate`), not unconstrained label propagation.

### 5.3 Methodological Rigour: Fixing the *al-Kāshif* Validation Artifact & Preserving Scholarly Authority

Retiring the earlier `+11.65 pp` external-validation claim (`DEC-010`) illustrates why provenance-aware auditing matters in computational historical work. Asymmetric overlap filtering (stripping verbatim *Taqrīb* matches while keeping *Taḥrīr* quotations that copied al-Dhahabī verbatim), together with permissive `n2`/`n3` links and unqualified `وثق -> thiqah` mapping, artificially depressed `score_B` and inflated `score_E2`. Under clean symmetric deduplication (`paired_clean`, `N = 1,994`), *Taqrīb* and *Taḥrīr* show near-identical 3-tier agreement and QWK (`~0.68`) against al-Dhahabī, with *Taḥrīr* gaining in fine-grained 5-tier rank correlation (`+0.0272` Spearman, `p = 0.0000`) while experiencing mild 3-tier macro-F1 compression (`0.6510` vs. `0.6932`) precisely because *Taḥrīr* shifts `398` mid-tier *maqbūl* entries across the binary boundary into tier `0` (rank 7 *iʿtibār*) whereas *al-Kāshif* often leaves equivocal `وثق` narrators in tier `1`/`2`. Separating **Track R** (scholarly facts) from **Track L** (`source = model_estimate`) guarantees that computational outputs assist scholarship on ungraded entries (`76.03%–80.85%` external agreement) without ever altering canonical verdicts.

### 5.4 Limitations & Pending Decisions

1. **Conservative `wuththiqa_policy="maqbul_r6"` Operationalization (`DEC-010`):** In *al-Kāshif*, **active** endorsements (`ثقة`, `وثقه`, `وثقوه`) denote explicit verification and map to Tier 2 (`thiqah`), whereas **bare passive** *wuththiqa* (`وثق` / `وثق حب` — "deemed trustworthy", frequently reflecting uncorroborated inclusion by Ibn Ḥibbān) indicates conditional status. Following classical usage (*Muqaddimat al-Kāshif*, p. 29; Ibn Ḥajar's Rank 6 *maqbūl*) and the non-inflation rule in [RESEARCH_PROTOCOL.md](../research_protocol/RESEARCH_PROTOCOL.md) §7 (uncertain evidence must not be promoted to the strongest certainty class), `maqbul_r6` conservatively assigns bare `وثق` to Tier 1 (`1`) rather than Tier 2 (`2`). For reproducibility, the alternative remains exposed via `--wuththiqa-policy thiqah`, while revised `PO1–PO3` framing awaits formal protocol sign-off.
2. **Stage 2/3 Hardware Split:** Stage 2 (`M0–M3c`) ran on AMD Radeon Pro 5500M MPS (`9,842.9 s`), whereas Stage 3 (`G0–G4d`) ran on 8-core CPU (`4,537.3 s`) after benchmarking showed PyTorch MPS sparse-scatter overhead made GPU execution `4.5×` slower for graph workloads, with bit-exact parity (`max_abs_diff = 0.0`) verified between backends.
3. **1-Hop Structural Priors vs. Deeper Heterophilic Architectures:** Future work beyond FYP scope could replace residual `GATv2` with signed or rank-difference-conditioned message functions (`H2GCN` / Signed-GNN) rather than standard nonnegative attention, and evaluate multi-critic *rijāl* triangulation (Ibn Abī Ḥātim's *al-Jarḥ wa-l-Taʿdīl* `1615`, al-Mizzī's *Tahdhīb al-Kamāl*) using the same symmetric overlap protocol.
