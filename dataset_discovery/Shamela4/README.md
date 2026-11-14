# Shamela4 Research Workspace

This folder contains the Shamela4 source-audit and tuple-validation tools. It describes the research workflow; generated audit and review files are kept separately under `data/2_interim/shamela4_narrator_audit/` so versioned evidence is not mixed with scripts.

## Current status

- **Schema:** v2.5 claim-level annotation schema is frozen for the pilot.
- **Pilot:** 20 purposively selected cases are prepared from the frozen 60-case validation pool.
- **Review capacity:** One Arabic-competent reviewer is currently available. The pilot can assess feasibility and protocol clarity, but it cannot measure inter-reviewer agreement or establish corpus-wide reliability.
- **Next milestone:** Complete Pass 1, freeze it, then perform per-claim Pass 2 reconciliation.

## Read this first

1. [Consolidated audit findings](SHAMELA4_AUDIT_FINDINGS.md) — evidence, limitations, and unresolved questions.
2. [Website ID crosswalk](SHAMELA_WEBSITE_ID_CROSSWALK.md) — documented mapping investigation and its limits.
3. [Stage-two manual review](stage2_manual_review.py) and [forensic verification tools](forensic_verification.py) — historical pipeline stages; use the versioned outputs and their manifests as the audit record.
4. [Tuple validation v3](tuple_validation_v3.py) and [v4](tuple_validation_v4.py) — diagnostic validation over tuple patterns. The v4 protocol and manifest are in `data/2_interim/shamela4_narrator_audit/stage2_diagnostics/forensic_verification_v4/`.
5. [Blinded annotation pilot generator](blinded_annotation_pilot.py) — generates the current claim-level pilot package.

## Dataset audit workflow

Run commands from the repository root. The scripts read the raw source and write generated results to `data/2_interim/`.

### 1. Inspect the source structure

Input: `data/1_raw/Shamela4_Full_DB/_meta/narrators.parquet`. The upstream dataset is [AuthenticIlm/Shamela4_Full_DB](https://huggingface.co/datasets/AuthenticIlm/Shamela4_Full_DB); verify the current dataset card and licence before redistributing source material.

Install the Parquet reader and run the structural audit:

```powershell
python -m pip install pyarrow
python .\dataset_discovery\Shamela4\audit_shamela_narrators.py .\data\1_raw\Shamela4_Full_DB\_meta\narrators.parquet --out .\data\2_interim\shamela4_narrator_audit
```

Optional: add `--sample 100 --top 100` for larger diagnostic samples. The audit is read-only with respect to the input.

### 2. Review source-ID and label diagnostics

```powershell
python .\dataset_discovery\Shamela4\diagnose_source_ids_and_fwaed.py .\data\2_interim\shamela4_narrator_audit
```

These outputs are triage aids, not corrections. An integer source ID is opaque unless supported by independent schema evidence; title matches and scholar-name string cues do not establish historical identity or attribution.

### 3. Inspect tuple structures

The forensic and tuple-validation scripts record successive analyses. Their outputs are versioned in `data/2_interim/shamela4_narrator_audit/stage2_diagnostics/`. Treat older versions as historical evidence; do not overwrite them to reflect later interpretations. The latest tuple-validation package is `forensic_verification_v4`; it is a diagnostic sample, not human-validated ground truth.

### 4. Use the frozen v2.5 human pilot

The current package is [blinded_annotation_pilot_20_v2_5](../../data/2_interim/shamela4_narrator_audit/stage2_diagnostics/blinded_annotation_pilot_20_v2_5/). It includes:

- `PILOT_PASS1_TEXT_BLINDED.csv` — tuple text without source ID or attached narrator identity.
- `PILOT_CLAIMS_BLANK.csv` — blank claim-level annotation table. The starter row is `C01`; add `C02`, `C03`, and so on for additional distinct claims in a tuple.
- `PILOT_PASS2_RECONCILIATION_BLANK.csv` — identity reconciliation by claim after Pass 1 is frozen.
- `PILOT_PROVENANCE_RECONCILIATION_BLANK.csv` — separate, blank documentary provenance review.
- `ANNOTATION_CODEBOOK.md` and `PILOT_PROTOCOL.md` — field definitions and reviewer workflow.
- `PILOT_SELECTION.csv`, `PILOT_INTERNAL_MAPPING.csv`, and `pilot_manifest.json` — selection, restricted case key, and integrity record. Keep the internal mapping from Pass 1 reviewers.

The generator defaults to writing a new v2.5 package here:

```powershell
python .\dataset_discovery\Shamela4\blinded_annotation_pilot.py
```

#### Single-reviewer workflow

1. Make dated working copies of the Pass 1 input and claims template. Leave the committed package unchanged.
2. Annotate claims from Pass 1 text only. Record uncertainty rather than forcing an interpretation.
3. Save the completed Pass 1 file and record its SHA-256. Treat it as frozen before opening Pass 2 or the internal mapping.
4. In Pass 2, create one row per frozen claim ID and compare each claim subject separately with the attached narrator.
5. Record feasibility, unresolved cases, time required, and protocol difficulties. With one reviewer, report no inter-reviewer agreement statistic and make no corpus-wide reliability claim.

Run the Shamela4 discovery tests from the repository root:

```powershell
python -m unittest discover -s dataset_discovery/Shamela4 -p "test_*.py" -v
```

## Historical artifacts and interpretation limits

Earlier forensic scripts and generated packages are retained so their manifests and findings remain inspectable. Some older reports recommend workflows that have since been superseded; consult the latest versioned protocol before acting on such recommendations. Do not edit or replace historical outputs in place.

- `ghar` group labels are database grouping keys, not verified historical evaluators.
- A tuple attachment does not prove that every claim in the tuple concerns the attached narrator.
- A source ID, title string, or locator does not by itself establish work identity.
- These discovery and validation stages do not construct a narrator graph, assign reliability labels, or train models.
