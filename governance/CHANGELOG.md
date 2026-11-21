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
