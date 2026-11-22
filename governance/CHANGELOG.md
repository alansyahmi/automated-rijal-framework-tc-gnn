# Research Change Log

This log records meaningful changes to the research workspace and methodology. It is not a substitute for Git history.

## 2026-11-06 — Initial research workspace

- Established the repository as an exploratory research development workspace.
- Added a draft research protocol and methodology design requirements.
- Added a preliminary dataset candidate register and source provenance template.
- Added data management and governance documentation.
- Adopted Evaluative Stance Analysis (ESA) as the working terminology.
- No dataset or model architecture has been selected by this initial scaffold.

## 2026-11-21 — P0: Environment, test portability, and CI (`taqrib-oriented-v2`)

- Added `requirements.txt`, `requirements-cpu.txt`, `pyproject.toml`, and `.github/workflows/tests.yml` (CPU `pytest -q -m "not gpu"` on Python 3.13).
- Added `common/hashing.py` (`sha256_text_normalized`, `sha256_bytes_normalized`, `normalize_manifest_path`) so text digests are invariant across CRLF and LF checkouts.
- Regenerated affected target-feasibility manifests and pinned input digests on LF: **hash method change, content unchanged** (`ibn_hajar_grade_provenance_manifest.json`, `EXPECTED_INPUT_HASHES` in `migrate_manual_collation_v2_2*.py`).
- Converted Windows backslash manifest paths to POSIX relative paths (`rijal_reference_corpus_manifest.json`, `audit_manifest.json`) and replaced `file:///C:` links in `RIJAL_REFERENCE_CORPUS_INVENTORY.md` and its generator with relative links.
- Removed tracked `dataset_discovery/target_feasibility/scratch/*.py` scripts and added `.venv/`, `.pytest_cache/`, and `scratch/` to `.gitignore`.

## 2026-11-20 — `taqrib-oriented` v2 two-score pipeline (retrospective entry)

- Pivoted to the *Taqrīb al-Tahdhīb* (`3076`) → *Taḥrīr Taqrīb al-Tahdhīb* (`8246`) two-score paradigm (DEC-004), aligned `8,823 / 8,827` (99.95%) entries, and built Bilgin (2026)-grounded 12-rank targets (`N = 7,258` core cohort, `5,080 / 1,089 / 1,089` stratified split).
- Constructed the zero-leakage master node/edge dataset (`59,864` edges; `42,011` pure Sanad/Bukhārī → `37,364` chronology-pruned edges) and ran Stage 2 NLP benchmarks (M0–M3c) and Stage 3 GNN ablations (G0–G4d, 5 seeds) on `taqrib-oriented` (frozen as `v2.0-taqrib-frozen` at `935bd09`).

## 2026-11-21 — P1: Governance & naming realignment (`taqrib-oriented-v2`)

- Logged `DEC-004` through `DEC-008` in `governance/DECISION_LOG.md` (covering the two-score pivot, deterministic Track R vs learned Track L separation, TC-GNN = Text-Classification-informed GNN + chronology pruning naming, dropping the dual-reviewer ESA pilot in favor of extraction QA + *al-Kāshif* validation, and raw-corpus licensing review).
- Updated `research_protocol/RESEARCH_PROTOCOL.md` with the controlling thesis title, old and proposed revised PO1–PO3 wording (noting Alan's 2026-11-21 selection of PO3 Option A, awaiting supervisor approval), and layer/experiment mappings.
- Applied §0.3 naming realignment across `notes/*.md` and `experiments/run_stage2_semantic_benchmarks_v2.py` / `experiments/run_stage3_tc_gnn_benchmarks_v2.py` docstrings/labels without modifying frozen `v2` outputs.

## 2026-11-21 — P2–P6: Layered 0–100 Architecture, *al-Kāshif* Validation, and Showcase Suite (`taqrib-oriented-v2`)

- **P2 (Deterministic Layer Builder):** Added `dataset_discovery/target_feasibility/layer_rules_v3.json`, `build_layered_scores_v3.py`, and `test_layered_scores_v3.py`, producing `layered_scores_v3_2026-11-21/` (`8,827` wide rows, `18,984` span-level evidence rows, `11` ASCII `* بل:` fixes, `E6868` Rank 12 resolution, explicit `missing` / `suspect_alignment` flags).
- **P3 (*al-Kāshif* External Validation):** Added `build_kashif_validation_v1.py` and `test_kashif_validation_v1.py`, extracting `7,181` entries directly from Shamela Book `1616`, linking `5,807` unambiguously to *Taqrīb*, mapping `3,789` onto 3-tier/5-tier scales, and flagging `843` verbatim overlaps (`2,566` non-verbatim paired common narrators).
- **P4 (Track L v3 Pipelines):** Added `experiments/v3_common.py`, renamed and updated `run_stage2_esa_benchmarks_v3.py` and `run_stage3_tc_gnn_benchmarks_v3.py` (excluding `missing` + `suspect_alignment`, reporting 3-tier metrics + `observed_first_grade` slice, enforcing non-overwrite Option-A `score_G_estimate`), plus CPU contract tests (`test_v3_pipeline_contracts.py`).
- **P5 (Unified Experiment Suite):** Added `run_layered_experiments_v3.py` and `test_layered_experiments_v3.py`, running Track R Exp A–C, paired bootstrap ($B = 2{,}000$) on *al-Kāshif*, E₁ sensitivity (`default`, `halved`, `doubled`, `off`), pure-*sanad* homophily (`42,011 → 37,364`), and coverage/slice reports under `results/layered_experiments_v3_2026-11-21/`. *(Stage 2/3 GPU runs marked `PENDING_CUDA_GPU` for execution on Alan's CUDA workstation.)*
- **P6 (Showcases & Thesis Documentation):** Added `visualize_layered_showcases_v3.py` (Gold-50 stepped chart + Rank-6 `maqbūl` showcase), `notes/THESIS_MAPPING.md`, `DEC-007` archival note in `notes/METHODOLOGY_AND_VIVA_DEFENSE.md`, and rewrote `README.md`.

## 2026-11-22 — AMD Radeon Pro 5500M (macOS Metal/MPS) Pipeline & End-to-End Track L Execution (`taqrib-oriented-v2`)

- **MPS Compatibility & Layer Parity:** Added `requirements-macos-mps.txt`, pure-PyTorch `index_add` graph layers (`experiments/mps_layers.py` bypassing PyG's unsupported `aten::scatter_reduce.two_out` on MPS), `experiments/test_mps_layers.py`, and end-to-end orchestrator `experiments/run_radeon_mps_pipeline.py`.
- **Stage 2/3 MPS Fixes:** Resolved `CAMeLBERT` `.bin` loading block on `torch==2.2.2` / `transformers==4.57.6` via HuggingFace Safetensors `refs/pr/1`; fixed Stage 2 Metal `6.77 GB` OOM via `--batch-size 8 --grad-accum 4`, `quantum=16` dynamic padding, and `empty_device_cache` cleanup; added `--resume` checkpoints in both Stage 2 and Stage 3 (`results/*/checkpoints/` gitignored).
- **Full GPU Execution Completed (`MPS`):** Ran Stage 2 ESA (`9,842.9s`), Stage 3 TC-GNN 5-seed ablations (`8,603.3s`, `backend=mps_native`), Stage 4 (`run_layered_experiments_v3.py` with `tier3_acc` + `rank_spearman` populated for `Exp_D_TC_GNN`), and Stage 5 showcases (`source=model_estimate` on `1,406` narrators, `observed_scholarly` on `7,421` narrators).
