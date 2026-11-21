# Implementation Plan: Layered 0–100 Narrator Score (ESA + TC-GNN)

**For:** the AI engineer working on `alansyahmi/automated-rijal-framework-tc-gnn`
**Prepared:** 2026-11-21, from a read-only review of `main` (HEAD `7a4e16a`) and `taqrib-oriented` (HEAD `935bd09`, frozen as tag `v2.0-taqrib-frozen`)
**Active Branch:** `taqrib-oriented-v2` (branched from `origin/taqrib-oriented` at `935bd09`)
**Thesis title (controlling):** *A Multi-Modal Framework for Quantifying Narrator Reliability in ʿIlm ar-Rijāl Using Evaluative Stance and Graph Neural Networks*

---

## 0. Read this first

### 0.1 The goal in one paragraph

Turn each narrator's classical evaluation into a traceable number from 0 to 100. Start from Ibn Ḥajar's *Taqrīb* grade (Baseline, **B**). Then add, as separate layers:

- **E₁**: the extra qualifiers inside the *Taqrīb* entry.
- **E₂**: the editorial verdicts of *Taḥrīr Taqrīb al-Tahdhīb* (al-Arnāʾūṭ and Maʿrūf).
- **G**: what a graph neural network over the sanad (transmission) graph can add.

Every layer must be traceable to Arabic source text. No layer may count the same evidence twice. A narrator with no evidence for a layer must be marked *missing*, not treated as "no change" and never as negative evidence.

### 0.2 Key design decision: which layers are computed and which are learned

The current `taqrib-oriented` branch trains every model to **predict the *Taḥrīr* rank**. In Alan's layered design, *Taḥrīr* is an **input layer**. You cannot do both for the same column: if *Taḥrīr* is used as an input, the graph layer has nothing independent to learn against, and the result becomes circular.

This plan therefore uses **two tracks**:

| Track | Layers | Learned? | Purpose |
|---|---|---|---|
| **R — Representation** | B → B+E₁ → B+E₁+E₂ | No. Fixed rules only | The 0–100 score with a full audit trail |
| **L — Learning / validation** | ESA text classifier + TC-GNN | Yes | Tests whether text and graph evidence *explain where Taḥrīr disagrees with Ibn Ḥajar*. Also produces a clearly labelled *estimate* for narrators that Taḥrīr does not cover |

What the graph layer (G) may and may not do:

- G **never overwrites or adds to** an observed *Taḥrīr* verdict.
- Where *Taḥrīr* is observed, G is reported only as a diagnostic: "the model agrees or disagrees with the scholars".
- Where *Taḥrīr* is missing or unmappable, G supplies a **model estimate** with an uncertainty value, in its own columns, flagged `source = model_estimate`.

This rule follows the advice Alan received: "the GNN should not automatically increase or decrease a narrator's score simply because of their network position".

### 0.3 Naming decisions (apply everywhere)

| Old (on `taqrib-oriented`) | New | Reason |
|---|---|---|
| "TC-GNN = Directional **Temporal-Causal** GNN" | **TC-GNN = Text-Classification-informed GNN**: the Stage 2 ESA text-classifier outputs are the GNN's node inputs | This is what Alan intended. It also matches the architecture as built (Stage 2 out-of-fold (OOF) features → Stage 3) |
| "TC-Pruning" (removing edges where Δṭabaqah ≤ −2) | **Ṭabaqah chronology pruning** (`chrono_pruned`) | Keeps the method but gives it its own name, so the "TC" acronym is free |
| Stage 2 "Semantic Sentiment / Stance Analysis" | **Stage 2: Evaluative Stance Analysis (ESA)** | Matches the title and the existing decision DEC-001 |
| `M3a_CAMeLBERT_Sentiment_Plus_Meta` | Keep the run, relabel it **"generic-sentiment baseline"** | It is weaker than the ESA model (MAE 0.725 vs 0.660), which is evidence that sentiment ≠ evaluative stance |
| "Score 1" / "Score 2" (Score 2 currently means *both* the Taḥrīr target *and* the model output) | `score_B`, `score_E1`, `score_E2`, `score_G_estimate` | Removes the ambiguity |

### 0.4 Out of scope / do not do

- Do not run the 120-narrator dual-reviewer ESA pilot described in `main`'s v2.0 report. It is dropped (see §6 and DEC-007).
- Do not rewrite git history, force-push, or delete the branches `frozen-v1` or `frozen-v2-taqrib-oriented`, or the tag `v2.0-taqrib-frozen`.
- Do not use any field from Shamela `narrators.csv` / `narrators.parquet` as a model input. The `طبقة رواة التقريب` and `الرتبة عند ابن حجر` fields are verbatim *Taqrīb* leaks, already documented in `main`'s v2.0 audit, Part D.3.
- Do not change the frozen v1/v2 artefacts. Build new versioned folders (`*_v3_<date>`).

---

## 1. Branch and order of work

1. Create the branch `taqrib-oriented-v2` from `origin/taqrib-oriented` (tip `935bd09`).
   - `git fetch origin taqrib-oriented && git checkout -b taqrib-oriented-v2 origin/taqrib-oriented`
2. Do the phases in this order. Each phase ends with a commit and a green test run.

| Phase | Content | Depends on |
|---|---|---|
| P0 | Environment, test portability, CI | — |
| P1 | Governance + naming realignment (docs only) | P0 |
| P2 | Deterministic layer builder (B, E₁, E₂) + evidence table | P0 |
| P3 | al-Kashif external validation set | P0 |
| P4 | Re-run Stage 2 ESA and Stage 3 TC-GNN under the new names and target rules | P2 |
| P5 | Experiments A–D + external validation report | P2, P3, P4 |
| P6 | Final deliverable, README, thesis mapping, PR to `main` | P5 |

P2 and P3 can run in parallel.

---

## P0. Environment, test portability, CI

**Problem found:**

- On `main`, 13 of 142 tests fail on Linux (129 pass). The causes are:
  - Pinned SHA-256 hashes were computed on Windows files with CRLF line endings. For example, `MANUAL_COLLATION_PILOT_10_WORKING.csv` hashes to the expected value only after converting LF→CRLF. Checking out on Linux produces LF, because `.gitattributes` forces `eol=lf`.
  - Manifests store Windows paths such as `data\1_raw\Shamela4_Full_DB\...`.
  - There is no requirements file (`pyarrow` was missing).
- `taqrib-oriented` has 8 test files. They were not run in this review.

**Steps:**

1. Add `requirements.txt`. Pin versions to the environment that produced the results. Known so far: torch `2.12.1+cu126`. Also needed: pandas, numpy, pyarrow, scikit-learn, torch_geometric, transformers, matplotlib, pytest. Add `requirements-cpu.txt` for CI.
2. Line endings:
   - Add one shared helper, `common/hashing.py::sha256_text_normalized(path)`, that hashes bytes after `\r\n → \n`.
   - Use it in every manifest writer and every hash test.
   - Regenerate the affected manifests once, on LF, and record this in the changelog as "hash method change, content unchanged".
   - Alternative: mark frozen artefacts `-text` in `.gitattributes` so git never converts them. Choose one approach and apply it consistently.
3. Paths: store `local_path` in manifests as POSIX relative paths (`PurePosixPath`). Readers must accept both forms (`Path(p.replace("\\", "/"))`).
4. Replace hard-coded `file:///C:/Projects/...` links in Markdown reports with relative links. Find them with `git grep -n "file:///C:"`.
5. Add `.github/workflows/tests.yml`. It should run `pytest -q` on `ubuntu-latest` with Python 3.13 and CPU-only requirements, and skip GPU tests with a marker (`@pytest.mark.gpu`).
6. Remove the tracked `__pycache__/` files (9 are tracked on `main`) and the `scratch/` scripts, if this branch still carries them.

**Acceptance:**

- `pytest -q` passes on Linux and Windows with zero failures.
- CI is green on the branch.
- No manifest contains a backslash path.

---

## P1. Governance and naming realignment (docs only)

**Files:**

- `governance/DECISION_LOG.md`: add these entries, each with rationale, alternatives and consequences, using the existing table format:
  - **DEC-004**: Pivot from early-critic Task B to the *Taqrīb* → *Taḥrīr* two-score paradigm (`taqrib-oriented`, 2026-11-20).
  - **DEC-005**: Layered representation B/E₁/E₂ is deterministic. The learned components (ESA, TC-GNN) are validated against *Taḥrīr* shift and never overwrite observed scholarly verdicts.
  - **DEC-006**: TC-GNN = Text-Classification-informed GNN. Δṭabaqah pruning is renamed "chronology pruning".
  - **DEC-007**: Drop the dual-reviewer ESA annotation pilot. Labels come from *Taqrīb* (rule-mapped per Bilgin 2026) and *Taḥrīr* (scholar-authored). Validation is extraction-accuracy QA plus external agreement with al-Dhahabī's *al-Kāshif*.
  - **DEC-008**: Raw-corpus handling decision (see P6.4).
- `governance/CHANGELOG.md`: add entries for 2026-11-20 (taqrib-oriented) and for this branch.
- `research_protocol/RESEARCH_PROTOCOL.md`:
  - §1 title: use the exact thesis title.
  - §5: insert PO1–PO3. Use the old wording plus the proposed revision from §9 of this plan, **once Alan and his supervisor have approved the revision**. Until then, mark it "awaiting approval".
  - Map each PO to the layers, experiments and outputs in this plan.
- `notes/STAGE3_TC_GNN_METHODOLOGY.md`: rewrite §1. Remove "Temporal-Causal", define TC-GNN as above, and keep the chronology-pruning evidence (42,011 → 37,364 edges) as a sub-section.
- `notes/STAGE1_AND_STAGE2_METHODOLOGY.md`, `notes/README.md`, `notes/FLAGSHIP_LITERATURE_SYNTHESIS.md`, `notes/BILGIN_2026_COMPARISON.md`, `notes/METHODOLOGY_AND_VIVA_DEFENSE.md`: apply the naming table in §0.3.
- `experiments/run_stage2_semantic_benchmarks_v2.py`: change only the docstring and labels in this phase. Rename the file to `run_stage2_esa_benchmarks_v3.py` in P4.

Inventory command: `git grep -n -i "temporal.causal\|TC-GNN\|tc_gnn\|tc_sanad\|sentiment"`. On `taqrib-oriented` this currently matches about 16 non-CSV files.

**Acceptance:**

- `git grep -i "temporal-causal"` returns nothing outside frozen result folders.
- Every new decision is logged.
- PO1–PO3 are either filled in verbatim or explicitly marked "awaiting Alan".

---

## P2. Deterministic layer builder (B, E₁, E₂)

**New script:** `dataset_discovery/target_feasibility/build_layered_scores_v3.py`
**Inputs (already on the branch):**

- `data/2_interim/rijal_fyp_modelling_pipeline/bilgin_grounded_targets_v2_2026-11-20/BILGIN_GROUNDED_TAQRIB_TAHRIR_8827_V2.csv`. Columns used: `taqrib_rank_bilgin_1_to_12`, `taqrib_bilgin_rule_id`, `taqrib_is_conditional_maqbul`, `taqrib_target_span`, `taqrib_context_note_spans`, `tahrir_disposition`, `tahrir_verdict_lead`, `tahrir_commentary_text`, `tahrir_rank_bilgin_1_to_12`, `tahrir_bilgin_rule_id`, `tahrir_part`, `tahrir_page_num`.
- `data/2_interim/rijal_fyp_modelling_pipeline/taqrib_v2_master_dataset_2026-11-20/TAQRIB_V2_MASTER_NODES_8827.csv`. Columns used: `qual_*`, `taqrib_has_context_note`, `printed_page_num_3076`, `split`.

**New config:** `dataset_discovery/target_feasibility/layer_rules_v3.json`. Versioned and hashed into the manifest. It holds every numeric constant, so nothing is buried in code.

**Outputs:** `data/2_interim/rijal_fyp_modelling_pipeline/layered_scores_v3_<date>/`

- `LAYER_EVIDENCE_LONG_V3.csv`: one row per piece of evidence. Columns:
  - `entry_id`, `layer` (B/E1/E2)
  - `source_book_id` (3076 / 8246), `part`, `printed_page`
  - `arabic_span` (verbatim), `rule_id`
  - `delta_0_100`
  - `status` (observed / not_applicable / missing / abstained)
  - `double_count_check` (which earlier evidence this span overlaps, if any)
- `LAYERED_SCORES_WIDE_V3.csv`: one row per narrator. Columns:
  - `score_B`, `score_E1`, `score_E2` (cumulative)
  - `delta_E1`, `delta_E2`
  - `status_B`, `status_E1`, `status_E2`
  - `rank_B`, `rank_E2`
  - `n_evidence_rows`
- `LAYERED_SCORES_REPORT_V3.md` and `MANIFEST.json` / `MANIFEST.sha256`.

### P2.1 Scale: rank bands

- Keep the branch's mapping for band centres: `S(r) = 100 × (12 − r) / 11`. Rank 1 = 100, rank 12 = 0, and the taʿdīl/jarḥ boundary at r = 6.5 sits at 50.
- Each rank owns a **band** of half-width `h = 100 / 22 ≈ 4.545` around its centre. Bands touch and do not overlap.
- **Rule: only a scholar's explicit re-grade may move a narrator into another band.** That means a *Taḥrīr* `بل:` verdict. *Taqrīb* qualifiers (E₁) may move a narrator *within* Ibn Ḥajar's band, never across it, because Ibn Ḥajar already took them into account when choosing the rank.
- Record a caveat in the report: rank 1 (*Ṣaḥābah*) is a status category, not a graded reliability judgement. Report results with and without rank 1.

### P2.2 Layer B: baseline

- `score_B = S(taqrib_rank_bilgin_1_to_12)`, `status_B = observed`. Keep the evidence row (`taqrib_target_span`, `taqrib_bilgin_rule_id`, page).
- Where *Taqrīb* abstained (`abstain_precondition_unmet` / `abstain_non_grade`, or unranked), set `score_B = NaN` and `status_B = abstained`. **Do not impute.**
- Conditional *maqbūl* (`taqrib_is_conditional_maqbul = True`, rank 6) is scored at rank 6 with the flag `conditional = True`. Ibn Ḥajar defined *maqbūl* as acceptable *if corroborated*, so it is not resolved at this layer.

### P2.3 Layer E₁: *Taqrīb* textual enrichment

- **Evidence:** qualifiers in the entry text: `qual_yudallis`, `qual_yursil`, `qual_yukhti_yahim`, `qual_ikhtalata`, `qual_rumiya_bidah`, `qual_sayyi_hifz`, `qual_lin`, `qual_qalil_hadith`, plus `taqrib_context_note_spans`.
- **No double-counting.** If a qualifier's span sits inside `taqrib_target_span`, or is part of the rank-defining phrase matched by `taqrib_bilgin_rule_id` (for example, `صدوق يخطئ` already *defines* rank 5), then `delta = 0`, `status = not_applicable`, and `double_count_check = "inside_rank_span"`. Only qualifiers *outside* the rank-defining span count.
- **Weights:**
  - Put fixed per-qualifier weights in `layer_rules_v3.json`, as fractions of the band half-width.
  - Example default: `ikhtalata −0.5h`, `yudallis −0.25h`, `yursil −0.15h`, `sayyi_hifz −0.5h`, `lin −0.5h`, `yukhti_yahim −0.4h`, `qalil_hadith 0`.
  - `rumiya_bidah` defaults to **0**: doctrinal accusation is not transmission precision. Keep it as a flag.
  - Cap the sum at `±h`, so the score stays inside the band.
  - Add one optional positive set for praise epithets outside the rank span (for example `حافظ`, `فقيه`) at `+0.25h` each, also capped.
- **Sensitivity analysis is required.** These weights are a modelling choice, not a classical fact. Re-run P5 with (a) the defaults, (b) all weights halved, (c) all weights doubled (still capped), and (d) E₁ switched off. Report whether any conclusion changes. This replaces expert weighting with transparency.
- `status_E1`:
  - `observed` if at least one counted qualifier exists.
  - `not_applicable` if the entry exists but has no extra qualifiers.
  - `missing` if the entry has no text (`taqrib_char_len == 0`).

### P2.4 Layer E₂: *Taḥrīr* editorial enrichment

Rules by `tahrir_disposition` (counts from the alignment: 5,766 / 2,621 / 111 / 325 / 4 unmatched):

| Disposition | Effect | Double-count rule |
|---|---|---|
| `agreed_no_bullet` | `delta_E2 = 0`, `status = observed_agreement` | **Agreement is not extra evidence.** Do not add a bonus. Record it as corroboration in its own boolean `tahrir_confirms_B` |
| `dissent_bal` (`• بل:`) | **Replace** the band: `score_E2 = S(tahrir_rank) + offset`. The offset carries E₁ only if the E₁ qualifiers still apply under the new verdict; otherwise the offset is 0 | `delta_E2 = score_E2 − score_E1`. Never `S(tahrir) + delta_E1 + S(taqrib)`-style addition |
| `qualification_qawluhu` (`• قوله`) | No band change unless `tahrir_rank_bilgin_1_to_12` differs from B. If a qualification text exists, an optional within-band offset of at most ±0.5h, from the same config | Log the phrase being qualified, from `tahrir_commentary_text` |
| `other_commentary` | `delta = 0`, `status = observed_no_grade` | — |
| `unmatched_in_tahrir` (4) / unmappable non-grade (6) | `score_E2 = score_E1`, `status_E2 = missing` | Missing ≠ agreement |
| *Taqrīb* abstained but *Taḥrīr* graded (about 1,349 entries) | `score_B = NaN`. `score_E2 = S(tahrir_rank)`, `status_E2 = observed_first_grade` | Report this group separately in every table |

Also:

- Uncommented *maqbūl* in *Taḥrīr* resolves to rank 7 (*Taḥrīr* introduction, p. 45; already implemented in the Bilgin mapper). Keep the citation in `rule_id`.
- Known digitisation noise (from `notes/METHODOLOGY_AND_VIVA_DEFENSE.md` §3, about 45 rows):
  - Fix the ASCII `* بل:` / `° بل:` overrides that are currently read as agreement (`E0138`, `E0143`–`E0145`, `E0153`, `E0155`, `E0159`, …).
  - Flag `E2615`/`E2616` (page-break bleed) and the 28 name-fallback collision pairs with `status = suspect_alignment`, and exclude them from evaluation.

### P2.5 Tests

**New test file:** `test_layered_scores_v3.py`. It must cover:

- `score_*` stays within [0, 100], and `score_E1` stays within B's band.
- Recomputing `score_E2` from `LAYER_EVIDENCE_LONG_V3.csv` reproduces the wide table exactly (provenance closure).
- No evidence row with `double_count_check = inside_rank_span` has a non-zero delta.
- `agreed_no_bullet` rows have `delta_E2 == 0`.
- `status = missing` rows have `delta == 0` and are never counted as "unchanged" in metrics.
- Golden cases from Gold-50 (`v2_gold50_adjudication_v2_1`), for example:
  - Ikrimah: rank 2.
  - Sufyān b. Ḥusayn: the `في غير الزهري` correction.
  - Muqātil b. Sulaymān: rank 12.
  - Layth b. Abī Sulaym: rank 4 with an `اختلط` E₁ penalty.
- Running twice gives byte-identical output.

**Acceptance:**

- All tests pass.
- The report lists the counts per status per layer and the distribution of `delta_E1` and `delta_E2` by rank.
- The 4 unmatched and 6 unmappable entries appear as `missing`.

---

## P3. External validation: al-Dhahabī's *al-Kāshif*

**Why:** this is an existing, scholar-authored classification, so it avoids new expert annotation. It is **not independent** of Ibn Ḥajar: al-Dhahabī (d. 748 AH) predates Ibn Ḥajar (d. 852 AH), Ibn Ḥajar drew on him, and `main`'s v2.0 audit found about 24.8% of al-Dhahabī grades appear as an exact substring in *Taqrīb*. Treat agreement as *convergent* evidence, not independent ground truth.

**Sources:**

- The raw book `1616__الكاشف-في-معرفة-من-له-رواية-في-الكتب-الستة/pages.jsonl` (already in `data/1_raw/Shamela4_Full_DB/26__التراجم-والطبقات/`).
- The `الرتبة عند الذهبي` field in `data/2_interim/Shamela4/narrators.csv`. **First verify which al-Dhahabī work that field comes from** (*al-Kāshif*, *Mīzān*, or *al-Mughnī*). Use it only if it is confirmed to be *al-Kāshif*. Otherwise extract the grades from 1616 directly.

**New script:** `dataset_discovery/target_feasibility/build_kashif_validation_v1.py`

**Outputs:** `data/2_interim/rijal_fyp_modelling_pipeline/kashif_validation_v1_<date>/`

- `KASHIF_ENTRIES_V1.csv` (entry, name, verdict span, page).
- `KASHIF_TAQRIB_LINK_V1.csv` (link method, confidence).
- `KASHIF_GRADE_MAP_V1.json`.
- `KASHIF_OVERLAP_AUDIT_V1.csv`.
- `REPORT.md` and `MANIFEST`.

**Steps:**

1. Parse the *al-Kāshif* entries and their verdict phrase.
2. Link entries to *Taqrīb* `entry_id`. Both cover the Six Books narrators. Use the existing Shamela narrator ID crosswalk first (`dataset_discovery/Shamela4/SHAMELA_WEBSITE_ID_CROSSWALK.md`), then a normalised-name plus sigil match. Keep only unambiguous links and report the link rate.
3. Map al-Dhahabī's terms to a **coarse ordinal scale**, defined in `KASHIF_GRADE_MAP_V1.json` with a cited source for each term:
   - 3-tier: thiqah-level / ṣadūq-level / weak-and-below.
   - Optionally 5-tier.
   - **Do not force al-Dhahabī onto Ibn Ḥajar's 12 ranks**, because his vocabulary differs.
   - Terms that cannot be mapped are recorded as `unmapped`, not guessed.
4. Overlap audit: for each linked pair, flag `verbatim_overlap = True` if the *Kāshif* verdict string appears inside `taqrib_text_verbatim`, after normalisation.

**Acceptance:**

- The link rate and the mapped-term coverage are reported.
- The overlap rate is reported. It should be roughly the 24.8% found earlier; explain it if it differs.
- Every P5 agreement figure is reported on **both** the full linked set and the **non-verbatim subset**. The non-verbatim figure is the one to quote in the thesis.

---

## P4. Re-run Stage 2 (ESA) and Stage 3 (TC-GNN)

### P4.1 Stage 2: ESA text classification

- Rename `experiments/run_stage2_semantic_benchmarks_v2.py` to `experiments/run_stage2_esa_benchmarks_v3.py`. Output goes to `results/stage2_esa_benchmarks_v3_<date>/`.
- Keep the model ladder: M0 identity, M1 metadata, M2 TF-IDF, M3 AraBERTv02 dual-head (rank + shift). Also keep the name-stripped ablation and CAMeLBERT relabelled as the generic-sentiment baseline.
- **Target stays *Taḥrīr*** (`tahrir_rank_bilgin_1_to_12` and `shift_class`).
- **Evaluation excludes** rows with `status_E2 ∈ {missing, suspect_alignment}`.
- Report the "*Taqrīb* abstained, *Taḥrīr* graded" group as its own slice.
- Export 5-fold OOF features exactly as before: `STAGE2_OOF_ESA_FEATURES_8827_V3.csv`.
- Keep the existing split (`seed=42`, 70/15/15, stratified by Taḥrīr rank × shift; train 5,080 / val 1,089 / test 1,089) so results stay comparable with v2.

### P4.2 Stage 3: TC-GNN

- Rename `experiments/run_stage3_tc_gnn_benchmarks_v2.py` to `experiments/run_stage3_tc_gnn_benchmarks_v3.py`. Output goes to `results/stage3_tc_gnn_benchmarks_v3_<date>/`.
- Inputs: the Stage 2 v3 OOF ESA features + *Taqrīb* metadata + sanad structure features (unchanged). The *Taḥrīr* columns must not appear in node features. Assert this in code, as Stage 2 already does.
- Keep the model ladder and its labels, renamed:
  - `G0` no-graph; `G1` graph-only; `G2b` MLP with 1-hop sanad features; `G3c` undirected GATv2.
  - `G4a` directed TC-GNN on chronology-pruned sanad.
  - `G4b` unpruned; `G4c` + semantic kNN; `G4d` consolidated graph.
- **Determinism:** `main`'s v2.0 audit showed CUDA sparse ops are not bit-reproducible.
  - Set `torch.use_deterministic_algorithms(True)` and `CUBLAS_WORKSPACE_CONFIG=:4096:8`.
  - Run the primary model 3 times with the same seed and check SHA-256 equality of the predictions.
  - If GATv2 scatter ops still drift, document the tolerance and select configurations by **5-seed mean validation score**, never by the single seed 42.
- **Model-estimate output:** for narrators with `status_E2 ∈ {missing, abstained-both}` (about 1,569 unranked plus the missing ones), emit `score_G_estimate`, `score_G_rank`, `score_G_entropy` and `source = model_estimate`. For observed narrators, emit `G_agrees_with_tahrir` (bool) and `G_residual = score_G − score_E2` as diagnostics only.

### P4.3 Column renames (decision for Alan; default is option A)

- **Option A (recommended, since P4 re-runs anyway):** rename at source.
  - `score2_tc_gnn_*` → `score_G_*`
  - `tc_sanad_*` → `sanad_chrono_pruned_*`
  - `score1_*` → `score_B_*`
  - `tahrir_reliability_*` → `score_E2_*`
  - Regenerate the manifests.
- **Option B:** keep the old v2 names in the frozen v2 results, and add `results/COLUMN_GLOSSARY.md` mapping old to new names.

Either way, the frozen v2 folders stay untouched.

**Acceptance:**

- Both scripts run end to end from a clean checkout using `requirements.txt`.
- The manifests list input hashes, including `layer_rules_v3.json` and `LAYERED_SCORES_WIDE_V3.csv`.
- The assertion "no Taḥrīr column in features" passes.
- The 3-run determinism check result is written into the results summary.

---

## P5. Experiments A–D and validation report

**New script:** `experiments/run_layered_experiments_v3.py`
**Outputs:** `results/layered_experiments_v3_<date>/`

| Exp | Information | What is measured | Against |
|---|---|---|---|
| **A** | `score_B` only | Baseline agreement | *Taḥrīr* (test split) and *al-Kāshif* |
| **B** | A + E₁ (`score_E1`). Learned version: ESA text classifier M3 | Does *Taqrīb*'s own extra wording move scores toward the scholars? | *Taḥrīr* shift; *al-Kāshif* |
| **C** | B + E₂ (`score_E2`, deterministic) | How far *Taḥrīr* moves scores: Δ distribution by rank, number of band crossings; agreement with *al-Kāshif* before vs after E₂ | *al-Kāshif* only. **C cannot be evaluated against *Taḥrīr*, because it contains *Taḥrīr*** |
| **D** | B + E₁ + ESA + graph (TC-GNN `G4a`) predicting the *Taḥrīr* shift | The graph's added value **over `G2b`** (MLP with 1-hop features), not only over no-graph `G0` | *Taḥrīr* (test); *al-Kāshif* on the estimate-only group |

**Metrics:**

- Ordinal: rank MAE, QWK, Spearman, exact and within-1 accuracy.
- Binary *taʿdīl*/*jarḥ*: accuracy and weighted F1 (Wahba 2026 alignment).
- 3-class shift: Macro-F1 and active Macro-F1 (StanceEval alignment).
- For *al-Kāshif*: 3-tier Macro-F1, Cohen's κ (weighted), and Spearman. Report these on the full linked set and on the non-verbatim subset.
- Slices: rank 6 *maqbūl*; *Taqrīb*-abstained; isolated vs connected nodes; rank 1 excluded.

**Statistics:**

- Paired bootstrap, B = 2,000, two-sided p-value and 95% CI.
- Compare each experiment with the one before it (A→B, B→D) and D with `G2b`.
- 5 seeds for all learned models.

**Missing-evidence rule in all metrics:** rows where a layer's status is `missing` are excluded from that layer's comparison and counted in a separate "coverage" line. They are never scored as "unchanged".

**Honesty requirement (from the v2 results):** v2 found that `G2b` (an MLP with 1-hop features) matched most of the graph gain: MAE 0.6527 vs `G4d` 0.6523, with binary accuracy p values around 0.01–0.05. The report must state plainly whether **multi-hop message passing** beats `G2b`, and claim a GNN benefit only if it does.

**Sensitivity:** repeat A–C under the four E₁ weight settings from P2.3 and include a one-table summary.

**Acceptance:**

- `LAYERED_EXPERIMENTS_REPORT_V3.md` contains one table per experiment, the slices, the significance results, the sensitivity table, and a short "what each layer contributed" paragraph written to be reused in the thesis.
- All numbers trace back to CSVs in the same folder.

---

## P6. Deliverable, documentation, licence, merge

### P6.1 Final deliverable

`results/layered_experiments_v3_<date>/FINAL_LAYERED_RIJAL_SCORES_8827_V3.csv`. One row per *Taqrīb* entry, with:

- `entry_id`, `entry_number`, `split`
- `rank_B`, `score_B`, `status_B`
- `score_E1`, `delta_E1`, `status_E1`, `e1_rules_applied`
- `rank_E2`, `score_E2`, `delta_E2`, `status_E2`, `tahrir_disposition`, `tahrir_confirms_B`
- `score_final_observed`: equal to `score_E2`, else `score_E1`, else NaN
- `score_G_estimate`, `score_G_entropy`, `G_agrees_with_tahrir`, `source`
- `kashif_tier`, `kashif_verbatim_overlap`
- `n_evidence_rows`

The evidence table (`LAYER_EVIDENCE_LONG_V3.csv`) ships alongside it. The intended use: "pick any narrator → see exactly which Arabic span moved the score, by how much, and under which rule."

Rework the Gold-50 and Rank-6 showcases (`experiments/visualize_*`) to use the new columns. Show B → E₁ → E₂ as a stepped chart per narrator, with the G estimate drawn separately.

### P6.2 README and thesis mapping

- Rewrite `README.md` around the title, the two tracks, and the layer diagram. Add a "Quick start" section with the 4 commands that rebuild P2 → P5.
- Add `notes/THESIS_MAPPING.md` with the table: title term → component → file → result:
  - "Multi-modal" = text (ESA) + *Taqrīb* metadata + sanad graph.
  - "Quantifying" = the 0–100 layered score.
  - "Evaluative Stance" = Stage 2 ESA.
  - "GNN" = TC-GNN.
- Also map PO1–PO3 to the experiments.
- Update `notes/METHODOLOGY_AND_VIVA_DEFENSE.md` §1 with the DEC-007 justification:
  - Labels are rule-based operationalisations of Ibn Ḥajar's and *Taḥrīr*'s own taxonomies.
  - The only human checking is **extraction QA**: the existing blind 120/120 sample, the 99.95% alignment, and the Gold-50 adjudication. This is not annotation.

### P6.3 Dropping the expert pilot

- Mark `main`'s v2.0 "STOP-AND-APPROVE" ESA pilot (120 narrators, about 826 units, dual-reviewer IRR) as **superseded by DEC-007**. Do this in the decision log, not by deleting files.
- Keep `TRAIN_120_STRATIFIED_ESA_PILOT_WORKSHEET_V2_0.csv` as an archived artefact.

### P6.4 Raw corpus licence (needs Alan's decision before merge)

- **Finding:** about 133 MB of raw Shamela book text (`data/1_raw/Shamela4_Full_DB/26__التراجم-والطبقات/*/pages.jsonl`, 40 tracked files on `main`) is committed. The files were force-added past `.gitignore`, which only allows `narrators.parquet`. They include modern critical editions: *Taḥrīr* (1997) and Bashshār ʿAwwād's edition of *Tahdhīb al-Kamāl*. The README says not to commit copyrighted corpora.
- **Steps:**
  1. Check the repo's visibility and Shamela's terms.
  2. Record the outcome as DEC-008.
  3. If removal is needed:
     - `git rm --cached` the `pages.jsonl` / `toc.jsonl` files on the new branch, keeping `book_metadata.json` and `manifest.json`.
     - Add `data/1_raw/README.md` with the Shamela book IDs, the expected SHA-256 values (already in `rijal_reference_corpus_manifest.json`), and a fetch/placement script.
     - Make the tests skip with a clear message when the raw files are absent.
- Removing the files from **history** needs `git filter-repo` and a force-push, which cannot be undone. **Do not do this without Alan's explicit approval.**

### P6.5 Merge

- Open a PR `taqrib-oriented-v2` → `main`. Merging will remove the legacy v1 files from `main`'s tree. This is expected, because they are preserved on `frozen-v1` (`7dd7a4d`). Say so in the PR description.
- Before merging: CI green, all phase acceptance criteria met, and Alan's review.

---

## 7. Open items that need Alan (not the engineer)

1. **Supervisor approval of the revised PO1–PO3** in §9. Alan chose PO3 option A (replace with layer validation) on 2026-11-21 (P1).
2. **Supervisor confirmation:**
   - The pivot to the *Taqrīb*/*Taḥrīr* two-score design.
   - Dropping the expert pilot (DEC-007).
   - The "TC = Text Classification" wording in the title (the title itself does not change).
3. **Column-rename option** A or B (P4.3). Default is A.
4. **Raw-corpus decision** (P6.4), including whether the repo is public.
5. **E₁ default weights**: approve the defaults in `layer_rules_v3.json` or adjust them. The sensitivity analysis protects the conclusions either way.

---

## 8. Reference: current facts this plan relies on

- *Taqrīb* entries: 8,827. v1.4 deterministic ranks: 5,680 assigned, 2,975 precondition-unmet, 172 non-grade. The Bilgin v2 mapper assigns ranks to 7,261.
- *Taḥrīr* alignment: 8,823 / 8,827 (99.95%). Dispositions: agreed 5,766, `بل` 2,621, other 325, `قوله` 111, unmatched 4.
- Core both-ranked cohort: 7,258 (unchanged 61.97%, downgraded 22.58%, upgraded 15.45%). Split: 5,080 / 1,089 / 1,089.
- Graph: 59,864 directed edges, 42,011 pure sanad/Bukhārī, 37,364 after chronology pruning.
- v2 Stage 2 best: AraBERTv02 dual-head (MAE 0.660, QWK 0.890, shift MF1 0.714).
- v2 Stage 3: `G4d` MAE 0.6535, QWK 0.8903. `G4a` shift MF1 0.7246. `G2b` MLP MAE 0.6544. All 5-seed.

---

## 9. Objectives: old wording vs this plan (added 2026-11-21)

Old PO1–PO3 are from the earlier project version, as supplied by Alan. They are not stated anywhere in the repo.

| Old objective | Status on `taqrib-oriented` + this plan | Gap to close |
|---|---|---|
| **PO1**: NLP classification model mapping Jarḥ wa Taʿdīl judgements to a reliability index S ∈ [0, 1] and a 3-tier ordinal class y ∈ {0, 1, 2}, under zero leakage | **Mostly covered.** Stage 2 (ESA) is the classifier. The final CSV already has `*_reliability_0_1` (the 0–100 score is just 100·S). OOF features and the Taḥrīr firewall cover zero leakage | Add **3-tier metrics** derived from the 12 ranks: 1–3 / 4–6 / 7–12, as already defined on `main` (E.3 of the v2.0 report). The branch currently reports binary taʿdīl/jarḥ instead. Add them to P4.1 and P5 |
| **PO2**: Audited narrator transmission KG + controlled multi-arm ablation; do structural features help, or does heterophily hurt? | **Covered.** Graph: 59,864 edges, chronology audit 42,011 → 37,364. Ablation: G0–G4d, 5 seeds, bootstrap | The branch does **not report homophily/heterophily**. `main` v1.0 did (edge homophily 0.2384 on 12 ranks, 0.4870 on 3 tiers). Add edge and class homophily for the v3 graph to P5, and discuss it next to the G2b-vs-G4 result |
| **PO3**: Isnād-level scores (weakest-link + preliminary mutābaʿāt/shawāhid) vs al-Albānī and Darussalam hadith grades | **Dropped.** There is no code or data for it on any branch. The only hit is "الألباني" in a list of critic names in `experiments/audit_v1_2_stage1_method1_and_critics.py`. It also conflicts with the README guardrail on chain-level claims | Choose: **(A)** replace PO3 with the layered-validation objective below (recommended), or **(B)** keep it as a small downstream case study. B needs hadith-chain and grade data that is not in the repo, plus a new phase P5b |

### Proposed revised wording (needs supervisor approval)

- **PO1.** To develop an Evaluative Stance Analysis (ESA) text-classification model, together with a deterministic, provenance-traceable layered scoring scheme, that maps Ibn Ḥajar's Jarḥ wa Taʿdīl judgements in *Taqrīb al-Tahdhīb* and the editorial verdicts of *Taḥrīr Taqrīb al-Tahdhīb* onto a standardised reliability index (S ∈ [0, 1], also reported on a 0–100 scale), Ibn Ḥajar's 12-rank ordinal scale, and a 3-tier classification, under strict zero-leakage conditions.
- **PO2.** To construct an audited, chronology-checked knowledge graph of narrator transmission relationships, and to run a controlled multi-arm ablation study testing whether a Text-Classification-informed Graph Neural Network (TC-GNN) explains the *Taḥrīr* editors' revisions of Ibn Ḥajar's grades beyond text-only and simple graph-feature baselines, including an analysis of transmission-network heterophily.
- **PO3 (chosen by Alan on 2026-11-21: option A).** To evaluate the validity of the resulting reliability scores by measuring the incremental contribution of each enrichment layer (*Taqrīb* baseline, *Taqrīb* qualifiers, *Taḥrīr* verdicts, graph) and their agreement with an independent existing scholarly classification (al-Dhahabī's *al-Kāshif*), with explicit treatment of missing evidence and source overlap.
- ~~**PO3 (option B).**~~ Not chosen. As above, plus a preliminary case study comparing weakest-link isnād scores built from the layered narrator scores with published hadith grades, presented as a computational analysis and not as hadith authentication.
