# Methodology Design

This directory will contain the conceptual framework, operational definitions, mathematical formulation, and experimental design. Do not choose an architecture before the data and prediction target are validated.

## Required conceptual distinctions

### Evaluative Stance Analysis (ESA)

ESA concerns the evaluative judgement expressed by a critic about a narrator. It is not interchangeable with generic sentiment analysis.

The methodology must define:
- the unit being analysed (statement, clause, or contextual passage);
- the target of the evaluation (the narrator, not an unrelated entity);
- stance categories or dimensions and their theoretical basis;
- how technical rijāl terminology, negation, qualification, disagreement, and context are handled;
- how critic identity and source context are represented;
- how ambiguous, compound, or conflicting statements are handled;
- the annotation and adjudication protocol, if human labels are created.

Do not assume that every phrase can be reduced to positive/negative polarity or a single ordinal score.

### Narrator classification

Specify the target label source and its exact operational mapping. Distinguish a source's reported grade from a researcher's derived class. Document disagreement, missing labels, and uncertainty.

### Transmission graph

Specify:
- node types and canonical identity rules;
- edge types and direction;
- whether an edge means reported teacher–student relation, chain adjacency, or another relation;
- source and locator for each edge;
- chronology and identity confidence;
- handling of uncertain, disputed, or indirect relations.

A graph convolutional network is justified only if the graph represents relevant information and improves a properly controlled comparison. A graph is not automatically useful because the data can be drawn as nodes and edges.

## Minimum experimental comparisons

Before claiming benefit from a multimodal or graph model, design comparisons such as:

1. majority-class and/or stratified simple baseline;
2. lexical or TF-IDF baseline;
3. text encoder without graph information;
4. structured-feature baseline, if metadata is justified;
5. graph-only baseline, if meaningful;
6. text + graph model;
7. ablations that remove each input modality.

The final comparison set depends on the validated data and approved objectives.

## Evaluation requirements

Pre-register or document:
- prediction unit and target label;
- split unit and leakage controls;
- class distribution;
- primary and secondary metrics;
- model-selection procedure;
- random seeds and repeated-run policy;
- confidence intervals or uncertainty reporting where feasible;
- error analysis and limitations.

Macro-F1 may be appropriate for imbalanced multiclass classification, but it must be accompanied by per-class metrics and a confusion matrix. Metric choice must follow the research question rather than convenience.
