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
