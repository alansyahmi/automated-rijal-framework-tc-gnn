# Automated Rijal Framework: Evaluative Stance Analysis and Graph Neural Networks

A research workspace for investigating computational methods in **ʿIlm al-Rijāl**, with an initial focus on:

- **Evaluative Stance Analysis (ESA):** identifying and representing the evaluative judgement expressed in classical narrator criticism (*al-Jarḥ wa al-Taʿdīl*).
- **Narrator classification:** studying how source-grounded scholarly assessments can be represented as classification targets.
- **Transmission graphs:** investigating whether teacher–student relations provide defensible contextual information for computational analysis.

> **Research status:** exploratory. No dataset, label mapping, model architecture, or empirical claim in this repository should be treated as final until it has passed source, methodological, and validation review.

## Research principles

1. **Source before model.** Establish the provenance, edition, context, and traceability of every scholarly statement before using it as data.
2. **Separate evidence from labels.** A critic's statement, a narrator's reference grade, and a model's prediction are different data objects.
3. **Avoid circular evaluation.** Do not use a reference grade, or text that directly reproduces it, as an input feature when predicting that same grade.
4. **Preserve uncertainty.** Ambiguous narrator identity, disputed evaluations, missing attribution, and uncertain chronology must be recorded rather than silently resolved.
5. **Justify every modality.** Text, metadata, and graph structure must each have a clear research purpose and be evaluated against simpler alternatives.
6. **Do not overclaim.** A model prediction is not an independent classical ruling on narrator reliability or hadith authenticity.
7. **Reproducibility.** Record data versions, transformations, splits, random seeds, configurations, and experiment outputs.

## Repository map

| Path | Purpose |
|---|---|
| `research_protocol/` | Research framing, scope, questions, and decision gates |
| `literature/` | Search strategy, literature register, and synthesis |
| `dataset_discovery/` | Candidate datasets, source register, and audit records |
| `data/` | Data documentation and schemas; raw data is not committed by default |
| `methodology/` | Conceptual framework, operational definitions, and experimental design |
| `experiments/` | Reproducible experiment specifications and run records |
| `results/` | Result tables, analysis, and interpretation |
| `governance/` | Decision log, change log, risks, and research integrity |

## Getting started

1. Read [the research protocol](research_protocol/RESEARCH_PROTOCOL.md).
2. Review the [dataset discovery register](dataset_discovery/CANDIDATE_DATASETS.csv).
3. Record every source in the [source register template](dataset_discovery/SOURCE_REGISTER_TEMPLATE.csv).
4. Document methodological decisions in [the decision log](governance/DECISION_LOG.md).
5. Do not begin model implementation until the relevant data and methodology gates have been met.

## Current guardrails

- The intended prediction unit is **the individual narrator (rāwī)**, unless the approved research objectives are explicitly revised.
- Any three-level narrator-grade mapping must be documented with its exact source, mapping rules, exclusions, and limitations. It is not automatically a universal or uncontested ground truth.
- ESA is not generic emotion or positive/negative sentiment classification. It concerns the semantic and contextual interpretation of a critic's evaluative stance.
- A teacher–student edge records a transmission relationship; it does not by itself prove direct audition, chronological possibility, continuity, or narrator reliability.
- Chain-level outputs, if explored, must be described as computational analyses and not as authoritative hadith authenticity judgements.

## Data, ethics, and licensing

Do not commit copyrighted source corpora, personal credentials, API keys, private data, or large raw datasets. Record the licence and permitted use of each external source before downloading, transforming, or redistributing it. Keep source-level licensing separate from the licence of this repository.

## Status

This repository is the research development workspace. Previous project versions and submitted academic artefacts should remain preserved separately and should not be silently overwritten by exploratory work.
