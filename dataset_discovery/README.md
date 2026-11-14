# Dataset Discovery

Use this directory to assess candidate datasets and audit their source evidence before dataset construction or modelling. Discovery is not approval: each candidate needs a record-level review of schema, provenance, attribution, identity linking, text integrity, coverage, leakage, and reproducibility.

## Start here

1. Review the [candidate dataset register](CANDIDATE_DATASETS.csv) to see what is under consideration.
2. Record access, licence, source version, and audit findings in the [source register template](SOURCE_REGISTER_TEMPLATE.csv).
3. Open the dataset guide below for its current evidence, tools, and next research step.

## Dataset workspaces

| Dataset | What is here | Current guide |
| --- | --- | --- |
| **Shamela4** | Narrator metadata audits, tuple-structure analysis, and the frozen claim-level human annotation pilot. | [Shamela4 guide](Shamela4/README.md) |
| **HadithDB** | Quote extraction, profiling, duplicate-structure audits, and audit findings. | [HadithDB audit](hadithdb/HADITHDB_AUDIT.md) |
| **HKG** | Audit findings for the HKG candidate dataset. | [HKG audit](HKG/HKG_AUDIT.md) |

Dataset-specific scripts and reference documents remain in their dataset folder. Generated analyses and versioned review packages belong under `data/2_interim/`, not alongside the source scripts.

## Evidence standards

- Preserve raw Arabic and make transformations traceable to their input and script versions.
- Distinguish a database attachment or group label from a historically attributed speaker or claim subject.
- Do not treat a citation, source ID, precomputed grade, or repeated quotation as proof of bibliographic identity or independent evaluation.
- Keep unresolved findings explicit. Automated diagnostics organize review; they do not make historical judgements.

## Research sequence

**Source and schema audit → manual evidence validation → target definition → dataset construction → graph design → modelling.** Do not build labels or a graph until the evidence and research target have been defined and validated.
