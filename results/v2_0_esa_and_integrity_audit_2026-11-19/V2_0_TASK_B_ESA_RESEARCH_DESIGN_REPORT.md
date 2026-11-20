# Task B Evaluative Stance Analysis (ESA) & Experimental Integrity Research-Design Report (v2.0 Pre-Implementation Audit)

**Status:** Read-only analytical investigation and research-design specification on `main` (`v2`), completed after freezing `v1.0` to `v1.3` on branch `frozen-v1` (commit `7dd7a4d`).
**Scope Constraints Observed:** Zero modifications to `v1.0` to `v1.3` datasets, scripts, benchmark results, or `governance/` files. Zero `v1.4`/`v2` training runs executed. All Part B to D feature, idiom, segmentation, and contamination analyses were executed strictly on the training partition (`train N = 3,674`); `val (N = 788)` and `test (N = 788)` remained sealed for all discovery.

---

## Executive Epistemic Summary: Verified Facts vs Hypotheses vs Recommendations

| Category | Core Points Grounded in This Investigation |
| :--- | :--- |
| **Verified Facts (Directly Observed)** | 1. **CUDA Reproducibility Root Cause (Part A):** Enabling `torch.use_deterministic_algorithms(True)` with `torch.sparse.mm` on CUDA raises no error yet remains **non-deterministic** (`3` identical `seed=42` runs on `Arm 4 ConcatDirGNN` diverged: `val_f1 = 0.5638 / 0.5638 / 0.5689`, `test_f1 = 0.4768 / 0.4768 / 0.4746`, `bit_exact = false`). Precomputing 1-hop graph propagation on CPU (`[X \|\| adj_t2s @ X \|\| adj_s2t @ X]`) matches `ConcatDirGNN` forward logits to `3.576e-7` max absolute diff and yields **100% bit-exact CUDA runs** (`3/3` identical SHA-256 predictions, `test_f1 = 0.476831`).<br>2. **Benchmark Drift Root Cause (Part A):** `v1.1` vs `v1.2` `BaseText_LogReg` (`0.4549` vs `0.4528`) came from `max_features=30000, max_iter=150` (`v1.1`) vs `35000, 160` (`v1.2`). `v1.2 Exp A` vs `v1.3 Abl 1` `ConcatDirGNN` (`0.4762` vs `0.4649`) came strictly from CUDA `torch.sparse.mm` non-determinism plus single-seed (`seed=42`) `val` selection (`EarlyMLP` reproduced `0.4601` bit-for-bit).<br>3. **Quote Duplication Anatomy (Part B):** Of `10,597` excess `(entry_id, norm_text)` rows in `v0.3` (`79,597` total vs `69,000` unique text) and `4,115` in `v0.4` Tahdhib ablation (`36,673` total vs `32,558` unique), **`9,702` (`91.55%`)** in `v0.3` and **`3,963` (`96.31%`)** in `v0.4` are **Shamela4 multi-group indexing duplicates** sharing the identical `(entry_id, source_work, source_citation, text)` under multiple critic `group_label_raw` entries, while `502` (`v0.3`) and `147` (`v0.4`) are exact duplicates and `92 + 6 + 295` (`v0.3`) reflect cross-work/distinct-citation attestation.<br>4. **Task B Segmentation & Vocabulary Gap on `train` (Parts B & C):** Across `58,101` provenance-dedup quote passages on `train`, `75.77%` are single-speaker (`41.58%` explicit internal, `34.19%` header-attributed), `12.55%` are regex-splittable multi-clause passages (`~73,204` estimated atomic units total), `11.37%` involve pronominal (`سمعت أبي`) or nested isnad chains, and `0.31%` are unattributed bio lines. Critically, **`61.27%` (`38,260 / 62,442`)** of `train` Arm 4 passages contain **zero match** to the `205` Taqrib Task A phrases; high-impact early idioms (`صالح` `3,323`, `سمعت أبي` `1,316`, `شيخ` `1,064`, `يكتب حديثه` `739`, `ليس بشيء` `617`, `ضعيف الحديث` `589`, `يحتج به` `314`, `ليس بذاك` `198`, `ثقة مأمون` `185`, `اختلط` `172`, `فيه نظر` `152`, `محله الصدق` `149`, `لا يحتج به` `85`, `سكتوا عنه` `23` at `100%` Rank 10) lie outside the `205`-phrase Taqrib inventory.<br>5. **Unrestricted `روى عنه` Signal on `train` (Part D):** In Method 1 linked `train` biographies, **`Rank 7` (`مستور`, `n=74` linked) has `>= 2` named students in `67.6%` (`50/74`, median `2.0`, `0` zero-student)** vs **`Rank 9` (`مجهول`, `n=176` linked) at `22.7%` (`40/176`, `69.9%` with `== 1` student, median `1.0`)**, a `44.9` percentage-point separation largely erased by cohort-only graph edges (`23.0%` vs `10.8%`).<br>6. **Shamela `narrators.csv` Contamination on `train` (Part D):** `طبقة رواة التقريب` (`98.5%` exact substring in Taqrib, `99.5%` token overlap) and `الرتبة عند ابن حجر` (`91.6%` exact, `99.6%` token overlap) are direct Taqrib leaks; `الرتبة عند الذهبي` (`24.8%` exact in Taqrib + anachronistic Mamluk grade) is historically inadmissible for Task B. |
| **Hypotheses (To Be Tested Empirically in `v2`)** | 1. Moving from flat bag-of-words TF-IDF (`v1.0` to `v1.3`) to structured atomic **`Narrator -> Speaker -> Claim` with 6D Task B ESA + polarity/qualification** will improve both calibration on qualified praise/criticism (`R3` vs `R4` vs `R5` vs `R8`) and rare-rank sensitivity.<br>2. Injecting **unrestricted Method 1 biographical assertions** (student count buckets `0 / 1 / >=2`, teacher counts, verdict-absent vs verdict-present indicators) alongside non-leaking 3-state book indicators will substantially reduce `Rank 7 -> Rank 9` confusion.<br>3. Replacing runtime `torch.sparse.mm` with deterministic `PrecomputedConcatDirGNN` and `5-seed mean val` config selection will eliminate artificial cross-version variance cleanly. |
| **Recommendations (Design Decisions Awaiting Approval)** | 1. **Freeze deterministic `v2` architecture rules** (`PrecomputedConcatDirGNN`, `5-seed mean val` selection) before any new training.<br>2. **Deduplicate before clause splitting** at `(entry_id, normalized_source_work, normalized_source_citation, normalized_text)` preserving multi-group critic metadata, then split into atomic `Narrator -> Speaker -> Claim` units.<br>3. **Execute a train-only Stratified Pilot (`120` narrators / `~500-600` atomic units) with Dual-Reviewer IRR (`~300` shared units)** to validate the hybrid Rule + Schema-Validated Extractor before scaling Task B ESA.<br>4. **Run the 5-rung controlled `v2` ablation ladder (`v2-M0` through `v2-M4`)** only after passing the Pilot IRR Gate. |

---

## Part A: Reproducibility & Baseline Integrity Check

### A.1 Root Cause of Cross-Version Drift & CUDA Non-Determinism Proof

Empirical measurements in [AUDIT_V2_0_PARTS_A_TO_D.json](file:///C:/Projects/automated-rijal-framework-tc-gnn/results/v2_0_esa_and_integrity_audit_2026-11-19/AUDIT_V2_0_PARTS_A_TO_D.json) resolve all three baseline discrepancies observed across `v1.0` to `v1.3`:

1. **`v1.0` to `v1.1` (`0.4272` -> `0.4778`):** `v1.0` suffered from non-OOF text feature leakage and uncalibrated SVC scores (`AUDIT_REPORT_V1_1.md`). `v1.1` fixed this with strict 5-fold narrator-disjoint OOF LogReg (`train` only).
2. **`v1.1` vs `v1.2` `BaseText_LogReg` (`0.4549` vs `0.4528`):** Caused purely by deterministic sklearn vectorizer/solver config differences (`v1.1`: `max_features=30000`, `max_iter=150`; `v1.2`: `max_features=35000`, `max_iter=160`).
3. **`v1.2 PhaseA_ExpA` (`0.4762 +/- 0.0088`) vs `v1.3 Abl1` (`0.4649 +/- 0.0153`) `ConcatDirGNN`:** Even with identical `Arm 4` OOF + topology features (`EarlyMLP` reproduced `0.4601` identically in both `v1.2` and `v1.3`), CUDA `torch.sparse.mm` backward atomic scatter-add is **non-deterministic** on NVIDIA RTX 2070 even when `torch.use_deterministic_algorithms(True)` and `CUBLAS_WORKSPACE_CONFIG=:4096:8` are set cleanly. Combined with single-seed (`seed=42`) config selection on `val`, two runs select different hyperparameters or stopping epochs.

Because `ConcatDirGNN` applies **one linear hop** (`ego_fc(x)`, `t2s_fc(adj_t2s @ x)`, `s2t_fc(adj_s2t @ x)`) with **no activation prior to message passing**, CPU-precomputing `X_concat = [X || adj_t2s @ X || adj_s2t @ X]` once before CUDA training is **algebraically identical**:

| Experiment Check (`v1.2 Arm 4`, CUDA `RTX 2070`) | Forward Logit Max Abs Diff | Run 1 `val_f1` / `test_f1` | Run 2 `val_f1` / `test_f1` | Run 3 `val_f1` / `test_f1` | 3-Run Bit-Exact Preds? |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Original `ConcatDirGNN` (`torch.sparse.mm` on CUDA, `seed=42`) | reference | `0.5638 / 0.4768` | `0.5638 / 0.4768` | **`0.5689 / 0.4746`** | **No (`2/3` match)** |
| `PrecomputedConcatDirGNN` (`CPU sparse @ X` -> dense CUDA, `seed=42`) | **`3.576e-7`** | `0.5638 / 0.4768` | `0.5638 / 0.4768` | `0.5638 / 0.4768` | **Yes (`3/3` SHA-256 identical)** |

### A.2 Config Selection Sensitivity (`seed=42` vs `5-Seed Mean val_f1`)

Using deterministic `PrecomputedConcatDirGNN` across the 3 `v1.2 Exp A` candidate configurations on `Arm 4`:

| Config | Hyperparameters | `seed=42 val_f1` | `5-Seed Mean val_f1 +/- std` | `5-Seed Mean test_f1 +/- std` | `5-Seed Mean test_acc` |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `cfg_1` | `hidden=128, drop=0.4, lr=5e-3, cw=sqrt` | `0.5638` | `0.5512 +/- 0.0153` | `0.4674 +/- 0.0126` | `0.6589` |
| `cfg_2` | `hidden=256, drop=0.4, lr=5e-3, cw=sqrt` | **`0.5676`** | **`0.5648 +/- 0.0165`** | **`0.4763 +/- 0.0096`** | **`0.6596`** |
| `cfg_3` | `hidden=128, drop=0.5, lr=3e-3, cw=balanced` | `0.4823` | `0.4856 +/- 0.0267` | `0.4543 +/- 0.0078` | `0.6129` |

**Design Decision for `v2`:** All graph models in `v2` MUST use deterministic CPU-precomputed propagation (or deterministic PyG/cuSPARSE check only when bit-exactness passes 3/3) AND select configs by **5-seed mean `val_macro_f1`**, never single-seed `seed=42`.

### A.3 Complete Benchmark Classification (`v1.0` to `v1.3`)

Full 72-row classification saved in [AUDIT_V2_0_BENCHMARK_CLASSIFICATION.csv](file:///C:/Projects/automated-rijal-framework-tc-gnn/results/v2_0_esa_and_integrity_audit_2026-11-19/AUDIT_V2_0_BENCHMARK_CLASSIFICATION.csv):

- **Superseded Exploratory (`v1.0`, 17 text/fusion models):** Superseded due to validation-peeking TF-IDF leak / uncalibrated SVC (`Ref_Dummy_*` & `Graph_PureTopo_*` remain valid low-water reference anchors).
- **Canonical Frozen Baseline (`v1.1`, 15 models):** First zero-leakage OOF pipeline (`FusionOOF_arm4_PlusTopo_ConcatDirGNN` = `0.4778 +/- 0.0055`, `OOFTextOnly_arm2_MLP` = `0.4824 +/- 0.0286` high variance), note GNN rows subject to CUDA `sparse.mm` variance.
- **`v1.2` Controlled Protocol (20 models):**
  - *Confirmatory Matched Baseline:* `PhaseA_ExpA_Arm4` (`LogReg 0.4528`, `EarlyMLP 0.4601`, `ConcatDirGNN 0.4762 +/- 0.0088`).
  - *Controlled Phase A:* `ExpB` (`+M1 bios`, `0.4371`), `ExpC` (`+book ind`, `0.4676`), `ExpD` (`0.4466`).
  - *Phase B Ablations:* `AblA` (`+9 critic struct`, `0.4911 +/- 0.0101`, `p=0.1540` vs `ExpA`, not yet independently significant), `AblB` (`0.4723`), `AblC` (`0.4831`).
  - *Exploratory:* `Exploratory_AllV12Evidence` (`0.4701`).
- **`v1.3` Genre-Dilution Diagnostic (14 models):** Matched causal ablation (`Abl1` to `Abl5`) proving full-bio degradation is `3.4x` evaluative dilution (`Abl3` filtered `0.4751`, `Abl5` hierarchical fusion `0.4764`, `p=0.0010` vs `Abl2 0.4428`).

---

## Part B: Task B Historical Statement & Attribution Integrity Audit

### B.1 Duplicate Quote Anatomy & Canonical Provenance-Preserving Deduplication Key

Full breakdown saved in [AUDIT_V2_0_TASK_B_DUPLICATE_BREAKDOWN.csv](file:///C:/Projects/automated-rijal-framework-tc-gnn/results/v2_0_esa_and_integrity_audit_2026-11-19/AUDIT_V2_0_TASK_B_DUPLICATE_BREAKDOWN.csv):

| Dataset | Total Rows | Unique `(eid, norm_text)` | Excess Rows | Class 1: Shamela Multi-Group Same Cit, Diff Critic Label | Class 1b: Exact Same Critic, Work, Cit & Text | Class 2: Same Critic, Distinct Work (Preserve!) | Class 3: Same Critic & Work, Distinct Cit | Class 4: Distinct Critic & Distinct/Parallel Work (Preserve!) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `v0.3` Eligible Passages | `79,597` (`39,840` train) | `69,000` | `10,597` | **`9,702`** (`4,942` train) | **`502`** (`266` train) | `92` (`38` train) | `6` (`2` train) | `295` (`138` train) |
| `v0.4` Tahdhib Early Ablation | `36,673` (`18,673` train) | `32,558` | `4,115` | **`3,963`** (`2,098` train) | **`147`** (`68` train) | `0` | `0` | `5` (`3` train) |
| `v0.4` Fwaed Passages | `9,458` (`4,341` train) | `9,053` | `405` | `0` | **`398`** (`145` train) | `0` | `7` (`2` train) | `0` |

**Critical Methodological Discovery:**
1. **`91.55%` (`v0.3`) and `96.31%` (`v0.4`)** of excess duplicate rows exist purely because Shamela4 emits one passage row per indexed `group_label_raw` whenever one physical sentence mentions multiple critics (e.g., `"وقال العجلي، والنسائي: ثقة."` stored twice; or `"وقال له رجل: سمعت أحمد..."` stored under both `أحمد` and `آدم بن أبي إياس`).
2. **Naive key trap:** Including `critic_label` in the dedup key retains `7,040` (`4,942 + 2,098`) `class1` multi-group duplicates on `train` (reducing `train` by only `412` rows from `62,854` to `62,442`) and would cause compound-clause splitters to **duplicate every multi-critic sentence `k` times**! Conversely, deduplicating globally on `(entry_id, norm_text)` destroys `393` (`class2` + `class3` + `class4`) genuine cross-work confirmations.
3. **Anomaly observed in `v0.4` Tahdhib `evaluations_raw`:** Rare rows in `v04_abl` (`class4` examples) exhibit Shamela HTML extraction swaps where evaluation prose leaked into `source_citation_raw` and takhrij book citations sat in `quotation_text_exact`; pre-extraction sanitation must filter takhrij-only footnotes matching `برقم: (` when `critic_text` was misaligned.

**Mandatory Canonical Deduplication Key (Apply BEFORE Atomic Segmentation):**
```
canonical_passage_key = (
    entry_id,
    normalize_arabic(source_work_normalised),
    normalize_arabic(source_citation_exact),
    normalize_arabic(quotation_text_exact_or_fwaed)
)
```
While collapsing `class1` and `class1b` duplicates under this key, aggregate all attached `historical_attribution_critic` (`group_label_raw`) entries into `shamela_group_labels_set` as candidate-speaker metadata before splitting compound sentences!

### B.2 Speaker Attribution & Atomic Segmentation Audit (`train` `58,101` Provenance-Dedup Quote Passages)

| Segmentation Category (`train` non-Fwaed Quote Passages) | Count | Share (%) | Handling Needed for Atomic `Narrator -> Speaker -> Claim` |
| :--- | :---: | :---: | :--- |
| `clean_atomic_explicit_speaker` | `24,161` | **`41.58%`** | Direct regex binding (`قال/وقال/ذكره <Speaker>: <Claim>`). |
| `clean_atomic_header_attributed` | `19,866` | **`34.19%`** | Bind `speaker = historical_attribution_critic` (single-speaker verdict text). |
| `splittable_compound_multi_clause` | `7,291` | **`12.55%`** | Deterministic clause split on discourse connectors (`وقال`, `وسئل`, `وذكر`). |
| `ambiguous_pronominal_or_nested_isnad` | `6,605` | **`11.37%`** | Needs coreference (`سمعت أبي` -> Abū Ḥātim inside `1615`/`al-Jarḥ wa-l-Taʿdīl`) or nested isnād chain stripping (`حدثنا X عن Y قال:` -> `Y` or target critic `Z`). |
| `biographical_or_transmission_mix_no_internal_speaker` | `178` | **`0.31%`** | Separate `روى عن` bio segment from speaker-attributed claim or tag `transmission_practice`. |
| **Total Quote Passages / Estimated Atomic Units** | **`58,101`** | **`100%`** | Yields **~`73,204` atomic units** before `class1` cross-group collapse (~`66k` after full citation dedup + `4,194` `v0.4` Fwaed + filtered `M1` evaluative sentences). |

Notice that **`88.32%` (`41.58% + 34.19% + 12.55%`)** segment cleanly via deterministic Arabic syntax rules, while **`11.37%`** require book-aware pronominal coreference (`سمعت أبي` -> `أبو حاتم الرازي` reported by `ابن أبي حاتم`) and nested isnad chain resolution.

---

## Part C: Task B ESA Representation Spec & Pilot Feasibility (`train N = 3,674`)

### C.1 Empirical Coverage Gap of Task A (`Taqrīb`) Vocabulary on Task B (`train`)

Testing exact space-bounded normalized matches against all **`205` candidate phrases** in [PHRASE_OCCURRENCE_SUMMARY_V0_1.csv](file:///C:/Projects/automated-rijal-framework-tc-gnn/data/2_interim/rijal_fyp_modelling_pipeline/evaluation_statement_occurrence_inventory_v0_1_2026-11-16/PHRASE_OCCURRENCE_SUMMARY_V0_1.csv) on the `62,442` provenance-dedup `train` Arm 4 passages:
- Passages hitting `>= 1` Task A *Taqrīb* phrase: **`24,182` (`38.73%`)**, covering `3,171 / 3,491` `train` narrators with Arm 4 text.
- Passages with **ZERO hit** to Task A phrases: **`38,260` (`61.27%`)**.

Full 43-idiom frequency & rank profile saved in [AUDIT_V2_0_TASK_B_IDIOM_GAP_TOP_TRAIN.csv](file:///C:/Projects/automated-rijal-framework-tc-gnn/results/v2_0_esa_and_integrity_audit_2026-11-19/AUDIT_V2_0_TASK_B_IDIOM_GAP_TOP_TRAIN.csv). Critical Task B early-critic idioms **absent** from the `205`-phrase *Taqrīb* inventory yet vital on `train` include:

| Idiom (`train`) | Dedup Passages (`train`) | Unique Narrators (`train`) | Top 3 Target Ranks (`train`) | Semantic / ESA Gap Role |
| :--- | :---: | :---: | :--- | :--- |
| `صالح` (bare) | `3,323` | `921` | `R3:1007; R5:800; R4:714` | General soundness (`صالح الحديث` `532` is in 205; bare `صالح` missing) |
| `سمعت أبي` | `1,316` | `877` | `R3:410; R4:215; R5:178` | Nested son-to-father attribution marker (*al-Jarḥ wa-l-Taʿdīl*) |
| `شيخ` | `1,064` | `414` | `R4:325; R5:234; R3:210` | Intermediate *taʿdīl* / generational status marker |
| `يكتب حديثه` | `739` | `251` | `R8:241; R5:190; R10:125` | Conditional transmission / *iʿtibār* allowance |
| `ليس بشيء` | `617` | `188` | `R8:238; R10:159; R5:112` | Severe negated rejection |
| `ضعيف الحديث` | `589` | `193` | `R8:309; R10:124; R5:87` | Hadith-domain weakness |
| `يحتج به` / `لا يحتج به` | `314` / `85` | `140` / `59` | `R5:140; R4:76` / `R5:37; R4:22` | Legal/canonical authority polarity (`لا يحتج به` = negated authority!) |
| `ليس بذاك` | `198` | `81` | `R5:86; R8:68; R4:23` | Mitigated weakness |
| `ثقة مأمون` | `185` | `97` | `R3:85; R2:70; R4:14` | Compound praise |
| `اختلط` / `تغير` / `بأخرة` | `172` / `147` / `118` | `28` / `25` / `25` | `R4:79; R5:30; R8` | Temporal memory deterioration (domain/qualification modifier) |
| `فيه نظر` | `152` | `60` | `R8:75; R5:42; R4:17` | Classical al-Bukhārī adverse criticism idiom |
| `محله الصدق` | `149` | `55` | `R4:64; R5:55; R3:17` | Restrained truthfulness |
| `لا يتابع عليه` | `103` | `53` | `R5:35; R10:26; R8:26` | Corroboration deficit |
| `سكتوا عنه` | `23` | `6` | **`R10:23` (`100%` Rank 10)** | Unanimous critical abandonment |
| `إن شاء الله` / `أرجو أنه` | `95` / `54` | `56` / `24` | `R3..R5` | Epistemic hedging / modal qualifier |

### C.2 Exact Task B Atomic Schema & Extended 6D ESA Specification

Every extracted historical claim is represented as an atomic tuple grounded in Task A's piloted schema ([EVALUATIVE_STATEMENT_LAYER_CODEBOOK_V0_2.md](file:///C:/Projects/automated-rijal-framework-tc-gnn/data/2_interim/rijal_fyp_modelling_pipeline/evaluation_statement_layer_v0_2_2026-11-16/EVALUATIVE_STATEMENT_LAYER_CODEBOOK_V0_2.md)):

1. **Identity & Provenance Fields (7 fields):** `atomic_unit_id`, `entry_id`, `shamela_narrator_id`, `canonical_passage_id`, `extraction_channel` (`v03_eval | v04_abl | v04_fwaed | m1_eval_filtered`), `source_work_normalised`, `source_citation_exact`.
2. **Attribution Fields (5 fields):** `speaker_canonical` (resolved early critic ID, e.g. `أبو حاتم الرازي`), `reporter_or_transmitter` (e.g. `ابن أبي حاتم` in `سمعت أبي`), `attribution_method` (`explicit_internal | header_single | compound_split | pronominal_resolved | unattributed`), `shamela_group_labels_set`, `clause_text_verbatim`.
3. **Task B 6D Evaluative Stance Dimensions (plus explicit Polarity/Scope flags):**
   - `statement_family`: `praise | criticism | mixed | unknownness | status_or_biography | authority_or_proof | unresolved`
   - `statement_domain` (semicolon multi-value): `general_reliability | memory_precision | honesty_veracity | unknownness_or_majhul_status | transmission_practice | corroboration_and_isolation | authority_for_ihtijaj | temporal_deterioration | doctrinal_position | companion_status | fabrication | biographical_information | unresolved`
   - `claim_content`: retains all `14` Task A values + Task B early-critic additions (`ihtijaj_authority`, `ikhtibar_writing_permission`, `corroboration_deficit`, `critical_silence_abandonment`, `temporal_ikhtilat`, `conditional_teacher_or_hadith_scope`).
   - `claim_mode`: `attributed_individual_judgement | reported_or_hedged_claim | first_person_knowledge_gap | collective_or_consensus_report | specific_behavior_or_transmission_observation | status_or_biographical_statement`
   - `wording_force`: `superlative | emphatic | plain_direct | mitigated_hedged | negated_strength | qualified_limited | not_applicable`
   - `consensus_wording`: `none | collective_agreement_claimed | unanimity_wording_claimed | critic_disagreement_noted | scope_or_referents_unclear | not_applicable`
   - `negation_flag` (`0/1`), `conditional_scope` (`none | temporal_late | specific_teacher | partial_hadith`), `referent_target` (`narrator_subject | specific_report_or_teacher | non_target_other`).

---

## Part D: Biographical Assertions & Zero-Leakage Firewall Audit (`train N = 3,674`)

### D.1 Unrestricted vs Cohort-Only Student Counts (`Rank 7` vs `Rank 9`)

Full 12-rank table saved in [AUDIT_V2_0_STUDENT_TEACHER_BY_RANK_TRAIN.csv](file:///C:/Projects/automated-rijal-framework-tc-gnn/results/v2_0_esa_and_integrity_audit_2026-11-19/AUDIT_V2_0_STUDENT_TEACHER_BY_RANK_TRAIN.csv):

| Rank (`train`) | `train N` | Early Quote (%) | M1 Linked `n` | Cohort M1 Edge Students `>=2` (`%` of linked) | Unrestricted Bio `روى عنه` `>=2` (`%` of linked) | Unrestricted Bio `== 1` Student (`n`) | Median Bio Students (Linked) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`Rank 6`** (`مقبول` / `لين`) | `66` | `95.5%` | `44` | `26` (`59.1%`) | `37` (`84.1%`) | `6` | `4.0` |
| **`Rank 7`** (`مستور`) | `124` | `64.5%` | `74` | `17` (`23.0%`) | **`50` (`67.6%`)** | `24` | **`2.0`** |
| **`Rank 9`** (`مجهول`) | `373` | `54.2%` | `176` | `19` (`10.8%`) | **`40` (`22.7%`)** | **`123` (`69.9%` of linked)** | **`1.0`** |

**Interpretation:** Restricting student edges to the `5,250` labeled cohort destroys `2/3` of `Rank 7`'s defining evidence (`>= 2` students). Extracting unrestricted named students directly from Method 1 `روى عنه:` segments yields a **`44.9` percentage-point separation (`67.6%` vs `22.7%`)** matching *Taqrīb* Rank definitions (`مستور` = known `>= 2` students without documentation vs `مجهول` = `<= 1` student), while `Rank 6` is NOT zero-quote (`95.5%` have early quotes; its bottleneck is lower median student breadth `4.0` vs `7.0` to `21.0` in `R2` to `R5`/`R8`).

### D.2 3-State Book Indicators & Missing-Not-At-Random Structure

From `book_indicator_status_by_rank_r1_to_r12` in [AUDIT_V2_0_PARTS_A_TO_D.json](file:///C:/Projects/automated-rijal-framework-tc-gnn/results/v2_0_esa_and_integrity_audit_2026-11-19/AUDIT_V2_0_PARTS_A_TO_D.json):
- Book absence is **book-genre conditioned**, not uniform obscurity: *al-Kāmil* (`method1_kamil`, weakness compilation) is `unmatched_in_book` for `267/275 (97.1%)` of `R1` and `979/1165 (84.0%)` of `R3`, whereas it links `91/218 (41.7%)` of `R8` and `31/65 (47.7%)` of `R10`.
- Ambiguous links (`ambiguous_candidate`) account for `26%` to `35%` across books in `R7` (`37/124` in Tahdhīb al-Kamāl) and `R9` (`97/373`). Modeling **three explicit states** (`linked_unique`, `ambiguous_candidate`, `unmatched_in_book`) plus distinguishing **biographical encyclopedias** (`1716`, `1615`, `890`) from **praise collections** (`1976`, `1981`) and **weakness collections** (`4609`) prevents false negative inference.

### D.3 Shamela `narrators.csv` Contamination & Zero-Leakage Policy (`train`)

Full 16-field overlap audit saved in [AUDIT_V2_0_NARRATORS_TAQRIB_OVERLAP_TRAIN.csv](file:///C:/Projects/automated-rijal-framework-tc-gnn/results/v2_0_esa_and_integrity_audit_2026-11-19/AUDIT_V2_0_NARRATORS_TAQRIB_OVERLAP_TRAIN.csv):

| Shamela Summary Field | `train` Non-Empty `n` | Exact Substring in *Taqrīb* (%) | `>=50%` Token Overlap in *Taqrīb* (%) | Exact in Method 1 Bios (%) | Firewall Decision for `v2` |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `طبقة رواة التقريب` | `3,585` | **`98.5%`** | **`99.5%`** | `1.2%` | **BANNED** (Direct Taqrib stratum) |
| `الرتبة عند ابن حجر` | `3,585` | **`91.6%`** | **`99.6%`** | `25.5%` | **BANNED** (Direct target label!) |
| `الرتبة عند الذهبي` | `2,513` | `24.8%` | `30.0%` | `19.6%` | **BANNED** (Late Mamluk synthetic grade + 25% Taqrib overlap) |
| `الشهرة` / `الكنية` / `اللقب` | `271 / 2,337 / 464` | `75.3% / 59.7% / 44.0%` | `78.6% / 70.7% / 45.3%` | `43.2% / 38.3% / 37.1%` | **DO NOT USE from `narrators.csv`** (Derived heavily from Taqrib entries) |
| `بلد الإقامة` / `بلد الوفاة` / `المذهب العقدي` | `1,118 / 636 / 241` | `36.3% / 30.3% / 20.7%` | `29.2% / 17.3% / 23.2%` | `45.1% / 55.3% / 17.4%` | **Quarantine unattributed `narrators.csv` rows**; extract ONLY directly from Method 1 / `fwaed` non-Taqrib text |
| `علاقات الراوي` / `تاريخ الوفاة` | `2,038 / 2,626` | `3.9% / 0.7%` | `16.7% / 5.0%` | `13.6% / 1.0%` | Prefer extracting relational & chronological assertions **directly from Method 1 clean bios** (`فقد مات` / `روى عنه`) to avoid Shamela editorial compilation artifacts |

---

## Part E: Proposed `v2` Implementation Plan, Architecture & Evaluation Protocol

### E.1 Hybrid Rule + Schema-Validated Extractor & Mandatory Train-Only Pilot Gate

To scale Task B ESA cleanly across ~`66k` deduplicated historical passages without losing classical *jarḥ wa-taʿdīl* nuance:
1. **Stage 1 (Deterministic Provenance Deduplication & Clause Segmentation):** Apply the Part B textual-citation dedup key (`class1` collapse with `group_labels_set` retention), discard known Shamela footnote-swapped takhrij noise, split compound sentences on discourse boundaries (`~88.32%` direct/compound), and apply book-specific pronominal rules (`ابن أبي حاتم` / `سمعت أبي` -> `أبو حاتم الرازي`).
2. **Stage 2 (Hybrid Rule + AI-Advisory 6D ESA Extractor):**
   - High-precision lexical/syntactic parser handles unambiguous single-formula early verdicts (`ثقة`, `صدوق`, `لا بأس به`, `ضعيف الحديث`, `ليس بشيء`, `مجهول`, etc.) with explicit negation & qualification guards.
   - Schema-validated LLM/structured advisory extraction (`strict JSON enum validation` + `source quote span grounding`) handles complex `~20%` to `30%` multi-clause, conditional (`إذا روى عن...`), and hedged prose passages.
3. **Stage 3 (Mandatory Human Pilot Gate BEFORE Full-Corpus Extraction):**
   - Draw a **strictly `train`-only stratified pilot (`N = 120` narrators, ~`500-600` atomic claims)**: oversample `R6`, `R7`, `R9`, `R10`, `R11-12` plus high-conflict `R4`/`R5`/`R8` narrators.
   - **Dual-Reviewer Inter-Rater Reliability (IRR):** Two reviewers independently annotate a `60`-narrator (`~300`-unit) overlap set across `speaker_binding`, `statement_family`, `statement_domain`, `wording_force`, and `negation_flag`.
   - **Pass Criterion:** Proceed to full extraction ONLY if human IRR reaches `kappa / alpha >= 0.80` on `statement_family` and `negation_flag` (`>= 0.75` on `wording_force`), AND hybrid extractor agreement against adjudicated gold exceeds `>= 0.85` macro-F1 on core stance fields.

### E.2 Controlled `v2` Model & Ablation Ladder (Locked Pre-Experiment Matrix)

All models run under deterministic CUDA (`PrecomputedConcatDirGNN` + `CUBLAS_WORKSPACE_CONFIG=:4096:8` + `5-seed mean val_f1` selection) on the frozen `3,674 / 788 / 788` narrator-disjoint split:

| Run ID | Evidence & Representation | Architecture | Research Question Answered |
| :--- | :--- | :--- | :--- |
| **`v2-M0`** | `Arm 4` deduplicated plain text (`class1` collapsed) + `11` cohort topo features | Deterministic `LogReg`, `EarlyMLP`, `PrecomputedConcatDirGNN` | Clean reproducible matched baseline (`v1.2 Exp A` equivalent without CUDA `sparse.mm` drift or `class1` overcounting) |
| **`v2-M1`** | `v2-M0` + filtered Method 1 evaluative passages (hierarchical fusion per `v1.3 Abl5`) | Hierarchical Multi-Stream + `PrecomputedConcatDirGNN` | Causal delta from genre-filtered Method 1 evaluative text under deterministic pipeline |
| **`v2-M2`** | `v2-M1` + **Biographical Assertions** (unrestricted `روى عنه` student count `0/1/>=2`, `روى عن` teacher count, non-leaking 3-state book indicators) | Hierarchical Multi-Stream + `PrecomputedConcatDirGNN` | Does explicit transmission-breadth evidence solve `Rank 7 -> Rank 9`? |
| **`v2-M3`** | `v2-M2` + **Pooled Atomic Task B 6D ESA Features** (counts/proportions over family, domain, force, negation, temporal/conditional qualification, critic disagreement entropy) | `EarlyMLP` + `PrecomputedConcatDirGNN` | Does structured 6D ESA outperform flat text + heuristic cues (`v1.2 Phase B Abl A`)? |
| **`v2-M4`** | `v2-M2` + **Critic-Conditioned Attention Pooling over Atomic `(Speaker, 6D ESA)` Units** | Critic-Conditioned Attention Encoder + `PrecomputedConcatDirGNN` | Does preserving critic-identity x stance interactions improve over pooled ESA summaries? |

### E.3 Primary, Secondary & Statistical Evaluation Protocol

- **Primary Benchmark Metrics:** `12-class Macro-F1`, `R2-12 Macro-F1`, `Accuracy`, `QWK`, `MAE`, `3-Tier Macro-F1` (`Praise [1-3] / Moderate [4-6] / Weak-Unknown [7-12]`).
- **Diagnostic Secondary Metrics:** Per-rank `F1` (`R6`, `R7`, `R9`, `R10`), **`R7 -> R9` confusion count/rate**, `Zero-Quote Connected` (`n=130` test), `Zero-Quote Isolated` (`n=161` test), and `Multi-Critic Conflict` slice F1.
- **Significance Gate:** Paired multi-seed bootstrap (`2,000` resamples, `seed=42`, two-sided p-value + 95% CI) comparing every rung sequentially against `v2-M0` and its immediate predecessor.

### E.4 Risks & Explicit Mitigations

| Methodological Risk | Observed Evidence | Pre-Committed Mitigation |
| :--- | :--- | :--- |
| **Multi-group double counting** | `13,665` `class1` copies (`v0.3 + v0.4`) | Canonical `(entry_id, work, cit, text)` dedup BEFORE splitting clauses |
| **Shamela takhrij/footnote swaps** | Observed in `v04_abl` `class4` rows | Regex screen rejecting pure `برقم: (` takhrij citation lines prior to ESA |
| **Method 1 unlinked ~40% gap in `R7`/`R9`** | `50/124` (`R7`) & `197/373` (`R9`) unlinked in `train` | Explicit `missing_link` vs `ambiguous_candidate` vs `0/1` student flags + Sanadset unrestricted student fallback check |
| **Critic identity long-tail overfitting** | Dozens of rare critics (`< 5` train narrators) | Explicit frequency cutoff (`top-K` canonical critics or `OTHER_CRITIC` bucket) + critic-type grouping (early Iraq/Hijaz vs compiler) |
| **Summary-field Taqrib leakage** | `98.5%` / `91.6%` exact overlap in `narrators.csv` | Hard firewall banning all `narrators.csv` `bio_*`/`summary` fields unless independently extracted from Method 1 / `fwaed` non-Taqrib text |

---

**STOP-AND-APPROVE GATE:** No `v2` extraction or model training has begun. Awaiting supervisor/user review and approval of Parts A to E before initiating the `train`-only Stratified Pilot (`Stage 3`).
