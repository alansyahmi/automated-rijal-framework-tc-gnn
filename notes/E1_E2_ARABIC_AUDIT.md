# Complete Arabic Evidence Audit: `E₁` Qualifiers & Changed `E₂` Scores (`DEC-012`)

**Branch:** `taqrib-oriented-simplified` (frozen baseline tag: `v3.1-simplified-audited`)  
**Audited Against:** Original Arabic text in `TAQRIB_V2_MASTER_NODES_8827.csv` and `BILGIN_GROUNDED_TAQRIB_TAHRIR_8827_V2.csv`  
**Audit Date:** 2026-11-23  

---

## 1. Executive Summary for Examiners (Dr Lai & Dr Tan)

A full line-by-line audit of all `123` numeric `E₁` rule firings (`119` narrators after `DEC-011`) uncovered **`31` numeric false positives** (plus `4` additional matches inside abstained/unadjusted entries = **`35` total guard exclusions**) caused by context-free keyword matching:

- Explicit Arabic **negations** (`وكان لا يدلس` on *Manṣūr b. al-Muʿtamir*, `E6908`; `لا يخطىء ولا يدلس`, `E7454`; `لم يخطىء إلا في حديث واحد`, `E6802`), which inverted praise into penalties.
- **Wrong grammatical subject** (`25` numeric cases in `qual_yukhti_yahim`), where Ibn Ḥajar corrected *another scholar's mistake* about the narrator (`أخطأ من عده في الصحابة`, `غلط من تكلم فيه`, `أخطأ ابن حزم في تضعيفه`).
- **Wrong person / mitigated *ikhtilāṭ*** (`E5986`: teacher Ibn ʿUyaynah confused, not the narrator; `E0191` & `E0911`: explicitly did not narrate during confusion).
- **Refuted *līn* criticism** (`E7793`: `وهم من لينه`, *"whoever weakened him erred"*).

Linguistic context guards (`_e1_qualifier_exclusion_reason` in [build_layered_scores_v3.py](../dataset_discovery/target_feasibility/build_layered_scores_v3.py)) eliminated all audited false positives while retaining **`91` narrators (`92` rule firings)** and logging every excluded match at `delta = 0.0` with its exact exclusion code in `LAYER_EVIDENCE_LONG_V3.csv`.

---

## 2. Pre-Fix vs. Post-Guard `E₁` Audit Table

| Rule | Pre-Guard (`ab072cf`) | Guard Exclusions Logged (`LAYER_EVIDENCE_LONG_V3.csv`) | Post-Guard Verified (`v3.1`) | Examples Verified on Arabic Text |
|---|---:|---:|---:|---|
| `qual_yursil` | 22 | 0 | **22** | `E0182` (`إلا أنه يرسل`), `E0269`, `E1227`, `E2170` |
| `qual_yudallis` | 30 | **3** (`negated_qualifier`) | **28** *(incl. 1 non-numeric abstained fixed)* | Excluded: `E6908` (`وكان لا يدلس`), `E7454` (`لا يخطىء ولا يدلس`), `E5112`; Kept: `E2615`, `E5725` |
| `qual_ikhtalata` | 31 | **3** (`2` `mitigated_no_narration_after_ikhtilat`, `1` `teacher_confusion`) | **28** | Excluded: `E5986` (`بعد أن تغير` = Ibn ʿUyaynah), `E0191`, `E0911` (`بعد ما اختلط لكن لم يحدث`); Kept: `E5685` |
| `qual_lin` | 6 | **1** (`refuted_criticism`) | **5** | Excluded: `E7793` (`وهم من لينه`); Kept: `E5384`, `E7684` |
| `qual_yukhti_yahim` | 34 | **28** (`18` `third_party_subject`, `8` `third_party_or_identity_error`, `2` `negated_qualifier`) | **9** | Excluded: `E6904`, `E2684`, `E6802`, `E7454`; Kept all 9 true cases: `E0048`, `E0911`, `E0916`, `E2424`, `E2550`, `E3446`, `E4275`, `E6017`, `E7919` |
| **Total** | **123** *(119 narrators)* | **35 total matches excluded** | **92 firings (`91` narrators)** | Clean positive/negative regression suite in `test_e1_arabic_linguistic_guards()` |

---

## 3. Audit of the `121` Changed `score_E2` Values vs. `taqrib-oriented-v2` (`b8dd2d4`)

Relative to `taqrib-oriented-v2` (`b8dd2d4`), **`121` narrators** have different continuous `score_E2` values (with zero changes to `rank_B`, `rank_E2`, `status_B`, `status_E2`, or `split`):

1. **`18` direct band-replacement fixes (`17` `observed_dissent`, `1` `observed_maqbul_to_r7`):** Removing implicit `E₁ → E₂` inheritance ensures *Taḥrīr*'s independent grade stands on its own terms:
   - **`E4281` (*ʿUbayd Allāh b. Abī Jaʿfar*):** *Taḥrīr* explicitly rejects *līn* reports (`• بل: هو ثقة مطلقًا...`); previously `82.73`, now cleanly **`85.00`**.
   - **`E4174`:** Previously boosted by `praise_faqih` (`23.14`) despite *Taḥrīr*'s `• بل: ضعيفٌ في الحديث... لم يكن له علم بالحديث`; now cleanly **`22.00`**.
   - **`E1659` & `E2907`:** Previously carried `qual_yukhti_yahim` false positives (`83.18`, `33.18`); now cleanly **`85.00`** and **`35.00`**.
2. **`103` downstream silent-continuity updates (`70` `observed_agreement`, `18` `observed_no_grade`, `13` `observed_qualification`, `2` `suspect_alignment`):** Changed strictly because *Taḥrīr* affirmed Ibn Ḥajar (`tahrir_confirms_B` / `observed_agreement`) while `score_E1` became `hukm_v1`-bounded, zeroed for `hafiz`/`faqih`, and guarded against negations/third-party errors (`DEC-011`, `DEC-012`).

---

## 4. Examiner-Facing Claim Separation

To maintain clarity during thesis examination, all claims are explicitly separated into three distinct research questions:

1. **Representation (Track R — `score_B`, `score_E1`, `score_E2`):** How faithfully and transparently can classical *Taqrīb* (`3076`) and *Taḥrīr* (`8246`) narrator verdicts be encoded as rule-traceable, abstention-aware `0–100` data on classical *ḥukm* thresholds (`hukm_v1`), without hidden cross-source inheritance or descriptive title overreach?
2. **Prediction (Track L Stage 2 — Entry-Level ESA):** When evaluated fairly against Majority and deterministic Lookup-Table (`0.6202` static Rank MAE) baselines, do entry-level Arabic text models (`AraBERTv02`) add measurable skill on **editorial revisions** (`Shift Macro-F1 = 0.7262` vs. `0.6576` Lookup-Table) and **ungraded entries** (`observed_first_grade` `N = 211`: `BinAcc = 69.67%` vs. `47.39%` Majority)?
3. **Relational Analysis (Track L Stage 3 — Sanad Graph):** Does adding teacher–student topology improve verdict prediction over text + 1-hop structural features (`G2b` `BinAcc = 0.9090` vs. `G0` `0.8951`, `p = 0.031`), or does low 12-rank homophily (`0.0474`) limit multi-hop GNNs (`G4a` `MAE = 0.6760` vs. `G2b` `0.6558`, `p = 0.000`, reported explicitly as a qualified negative finding alongside `score_G_estimate`'s `76.03%` non-Companion agreement vs. *al-Kāshif*)?
