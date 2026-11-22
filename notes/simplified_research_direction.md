# Simplified Research Direction

**Status:** Working research charter for discussion and methodological alignment  
**Branch:** `taqrib-oriented-simplified`  
**Baseline preserved:** `taqrib-oriented-v2`  
**Last updated:** 2026-11-23

> This document clarifies the intended research contribution. It is not, by itself, an amendment to the supervisor-approved title, objectives, research questions, or methodology. Any formal changes must be discussed with and approved by the supervisor.

## 1. Research identity

### Core purpose

This project aims to develop a structured, traceable, and machine-readable numerical representation of narrator evaluations recorded in *Taqrīb al-Tahdhīb*, with carefully governed enrichment from additional textual evaluations and relevant scholarly commentary.

The framework is intended to make existing scholarly assessments easier to organise, compare, query, and reuse in future computational research. It does **not** aim to independently determine the objectively true reliability of each narrator, replace classical scholarship, or issue new authoritative *jarḥ wa-taʿdīl* judgements.

### Central research question (working formulation)

**How can the qualitative narrator evaluations recorded in *Taqrīb al-Tahdhīb* be represented as traceable numerical data, and how can additional textual evaluations and narrator relationships enrich that representation without obscuring their scholarly provenance?**

This is a working formulation to guide the research. It does not supersede any formally approved research question.

## 2. What the project produces

The principal output is not simply a classifier or a single score column. It is a structured representation in which a numerical value can be traced back to the scholarly judgement, source passage, attribution, and transformation rule from which it was derived.

At minimum, the representation should preserve:

- The narrator's identity and the evidence used to align records across sources.
- The original wording and classification in *Taqrīb al-Tahdhīb*.
- The source and attribution of each additional evaluative statement.
- The rule or mapping used to derive a numerical value.
- Whether a value is directly source-derived, editorially enriched, inferred, predicted, uncertain, or unavailable.
- The distinction between an original scholarly judgement and a computational interpretation of that judgement.

A numerical representation is useful only if users can inspect what it represents and how it was produced.

## 3. Scope and source hierarchy

### 3.1 Primary source: *Taqrīb al-Tahdhīb*

*Taqrīb* is the starting point and baseline of the project. Its narrator classifications and relevant additional statements are represented while retaining the original Arabic text and source attribution.

The baseline should remain recoverable even after enrichment. It must never be silently overwritten by a later layer.

### 3.2 Editorial enrichment: *Taḥrīr Taqrīb al-Tahdhīb*

*Taḥrīr* may provide editorial assessment, qualification, correction, or disagreement relevant to the baseline. These should be represented as a distinct layer, with the editorial source and the nature of the intervention recorded.

An editorial assessment is not to be presented as though it were Ibn Hajar's original wording. Agreement, disagreement, qualification, and absence of comment should remain distinguishable.

### 3.3 Other commentaries and scholarly sources

Relevant *shurūḥ*, *ḥawāshī*, or other scholarly works may be incorporated where their identity, textual evidence, attribution, and relevance can be established.

Their inclusion must be evidence-led. A source should not be treated as a commentary on *Taqrīb* merely because it discusses the same narrator or repeats a similar judgement. If no suitable commentary is available or verifiable for a particular record, the project should record that limitation rather than fill the gap through unsupported inference.

### 3.4 Narrator relationships

Narrator relationships can provide structural context and support computational exploration. They do not automatically constitute evidence that one narrator is reliable or unreliable.

A relationship edge must have a defined meaning, source, direction where applicable, and provenance. For example, a documented teacher–student or transmission relationship is not itself a positive or negative reliability judgement.

## 4. Numerical representation

### 4.1 What a score means

The proposed 0–100 value is an **operational numerical representation of a source-based scholarly classification**, not a measured probability that a narrator is reliable, a new hadith grade, or an independent verdict on historical truth.

The original Arabic classification must always be retained alongside the numerical value.

### 4.2 Mapping principles

A defensible mapping should:

1. Preserve the ordering and distinctions expressed by the source as far as the source permits.
2. Explain the rationale for meaningful score intervals and thresholds.
3. Avoid implying that ordinal categories have naturally equal numerical distances.
4. Distinguish the source's category from any finer-grained numerical interpretation introduced by the project.
5. Make every mapping rule explicit, versioned, and reproducible.
6. Support sensitivity analysis where the exact numerical spacing is a methodological choice rather than a value specified by the source.

The score must not be described as calibrated or probabilistic unless a separate calibration study justifies that claim.

### 4.3 Keep layers separate

The data model should preserve, at minimum:

- **Baseline representation:** derived from the primary *Taqrīb* classification.
- **Enriched representation:** incorporates eligible additional statements and editorial assessments, with each change traceable to evidence.
- **Model estimate (if used):** a separate prediction or estimate, never silently substituted for a source-derived value.

A downstream application may choose which layer to use, but the dataset should not conceal the distinction.

## 5. Enrichment without distortion

Additional evidence should refine the representation only when its meaning and relationship to the narrator are sufficiently clear.

For every proposed adjustment, record:

- The exact text span or source passage.
- The speaker or author to whom the judgement is attributed, where known.
- The narrator being evaluated.
- The evaluative meaning and its direction.
- The source and editorial context.
- The transformation rule and resulting change.
- Any uncertainty, ambiguity, disagreement, or exclusion decision.

Important safeguards:

- **No double-counting:** repeated, dependent, or derivative statements should not automatically count as independent evidence.
- **No argument from silence:** absence of a comment is not evidence of a negative judgement or proof that an editor ignored a qualification.
- **No semantic overreach:** biographical praise, scholarly status, jurisprudential expertise, and transmission reliability are not interchangeable concepts.
- **No forced resolution:** conflicting scholarly assessments should remain visible rather than being collapsed into an apparently unanimous label.
- **No unsupported completion:** missing evidence should remain missing or explicitly uncertain.
- **No hidden inheritance:** an earlier layer's adjustment should not carry into a later source's judgement unless the methodology provides a defensible reason.

Where the evidence cannot support a confident adjustment, preserve the statement as structured evidence without forcing it into a score.

## 6. Role of NLP and graph learning

NLP and graph methods are supporting computational techniques, not independent sources of scholarly authority.

### Evaluative Stance Analysis (ESA)

ESA may assist in identifying, classifying, or organising evaluative language and its stance. Its predictions should be assessed against appropriately defined annotations or source-derived targets.

A model that predicts an editorial category from an entire entry is not necessarily extracting individual evaluative statements, identifying their speakers, or resolving their targets. The claims made about ESA must match the actual task implemented and evaluated.

### Graph methods and TC-GNN

Graph methods may investigate whether narrator relationships and structural context provide useful additional information. Their contribution must be demonstrated against suitable non-graph baselines.

Graph proximity, degree, centrality, or message passing must not be interpreted as scholarly evidence by themselves. A model prediction remains a model prediction, even when it is informed by a graph of historically grounded relationships.

If graph learning does not provide a meaningful and robust improvement over simpler methods, that is a valid research finding. The project should not retain a complex model merely to justify its presence in the title.

## 7. Evaluation: what would make the representation useful?

Evaluation should be aligned with the claims being made. No single metric can establish that a numerical representation is historically or religiously authoritative.

Potential evaluation dimensions include:

1. **Source fidelity:** Can each record and score be traced to the relevant source text, attribution, and rule?
2. **Coverage and alignment:** How much of the target source can be represented, and how many cross-source alignments are reliable?
3. **Rule consistency:** Do the same explicit source conditions produce the same representation under the documented rules?
4. **Ordinal behaviour:** Does the numerical ordering preserve the distinctions and ordering intended by the source?
5. **Enrichment analysis:** What changes when additional statements or editorial assessments are incorporated, and can those changes be explained?
6. **External comparison:** Where an independent scholarly source is available, how does the representation compare with it? Agreement should be interpreted as comparative evidence, not proof of an absolute gold standard.
7. **Model utility:** Do NLP or graph methods add measurable value over transparent, simpler baselines for a clearly specified task?

Evaluation should report limitations, disagreements, missing data, and cases where enrichment does not improve agreement with a comparison source. A result should not be presented as universally better merely because it improves one metric.

## 8. Undergraduate project boundary

The project should prioritise a coherent, defensible contribution over the number or sophistication of computational modules.

### Essential

- Define the representation and its intended interpretation.
- Establish a reproducible *Taqrīb* baseline.
- Preserve original labels, Arabic evidence, attribution, and provenance.
- Implement and justify a transparent numerical mapping.
- Incorporate only clearly defined and traceable enrichment.
- Evaluate coverage, consistency, source fidelity, and the behaviour of the resulting representation.
- Explain limitations and avoid claims that exceed the evidence.

### Supporting or conditional

- ESA experiments, if they answer a clearly defined research question and can be evaluated appropriately.
- Graph feature and GNN experiments, if their incremental value can be tested against simpler baselines.
- External scholarly comparisons, where source alignment and category mapping are defensible.
- Additional commentaries, where suitable texts and reliable attribution are available.

### Outside the present claim

- Independently re-grading all narrators as though the project can determine the objectively true judgement.
- Replacing classical scholarly methodology with model predictions.
- Treating every narrator relationship as reliability evidence.
- Claiming a complete automated *jarḥ wa-taʿdīl* pipeline.
- Treating a 0–100 score as a calibrated probability without the necessary validation.
- Resolving all historical disagreements or filling every gap in the source tradition.

These are not necessarily unworthy future research directions. They are simply beyond what this project needs to claim.

## 9. Practical decision test

Before adding a dataset, rule, model, or experiment, ask:

1. Does it help produce or evaluate the source-grounded numerical representation?
2. Is its evidence and provenance clear?
3. Does it preserve the distinction between scholarly judgement and computational inference?
4. Can its contribution be explained and defended within the project's scope?
5. Would removing it make the central research contribution materially weaker?

If the answer to these questions is mostly no, the component should be deferred, treated as exploratory, or documented as future work.

## 10. Working explanation of the project

A concise explanation for discussion with the supervisor or examiners:

> This research investigates how narrator evaluations in *ʿIlm al-Rijāl* can be represented as structured numerical data while preserving their original scholarly sources and meanings. It establishes a baseline from Ibn Hajar's *Taqrīb al-Tahdhīb*, explores traceable enrichment through additional evaluations and editorial commentary, and investigates whether computational analysis of evaluative text and narrator relationships can provide useful supporting information. The aim is to improve the machine-readability and reusability of existing scholarly assessments, not to replace or independently overrule them.

## 11. Immediate next steps

1. Confirm this research identity and boundary with the supervisor before changing any formally approved title, objective, or research question.
2. Map each approved objective to a concrete deliverable and evaluation method.
3. Audit the current implementation against the charter, classifying components as essential, supporting, exploratory, or deferred.
4. Review the numerical mapping and every enrichment rule for source fidelity, interpretability, and double-counting.
5. Define a minimum defensible experimental plan before adding further model complexity.
6. Keep the existing `taqrib-oriented-v2` branch intact as a preserved implementation snapshot; develop the simplified direction separately.

---

**Guiding principle:** Preserve the scholarship first. Formalise what the sources actually say. Use computation to make that evidence more structured and useful, not to claim authority the computation does not possess.
