# Research Protocol

**Version:** 0.1 (initial working protocol)  
**Status:** Draft — requires review and approval where changes affect approved FYP scope.

## 1. Research identity

**Working research area:** Computational analysis of narrator evaluations in ʿIlm al-Rijāl.

**Working title:** A Multi-Modal Framework for Quantifying Narrator Reliability in ʿIlm al-Rijāl Using Evaluative Stance Analysis and Graph Neural Networks.

The approved title and PO1–PO3 remain controlling academic requirements. This working wording records the terminology change from “Semantic Sentiment Analysis” to **“Evaluative Stance Analysis (ESA)”**; confirm any formal title change with the supervisor before submission.

## 2. Problem framing

Classical rijāl literature contains evaluative statements about narrators, biographical information, and accounts of teacher–student transmission. These materials are heterogeneous: statements differ in wording, critic attribution, source context, specificity, and the identity certainty of the narrator being discussed.

A computational study must therefore establish how source evidence is collected, linked to narrators, represented, and evaluated before selecting a model. The research must not assume that digitised records are complete, correctly attributed, or mutually independent.

## 3. Unit of analysis and prediction target

**Provisional prediction unit:** an individual narrator (rāwī).

**Potential target:** a source-derived narrator grade or grade category, with the exact reference work, edition, mapping rules, and exclusions specified before modelling.

The following must remain distinct:

1. **Evidence statement:** the exact evaluative wording attributed to a critic.
2. **Evaluative stance:** the interpretation of the critic's judgement expressed in that statement and context.
3. **Reference label:** a grade assigned or reported by a named scholarly source under a documented protocol.
4. **Model prediction:** the category predicted by the computational system.

A prediction against a reference label measures agreement with that operationalised source target. It does not establish an absolute, independent judgement of historical reliability.

## 4. Provisional research questions

These are working questions for refinement against the approved objectives:

- **RQ1 — Evidence and representation:** How can classical jarḥ wa taʿdīl statements be collected, attributed, contextualised, and represented for computational analysis?
- **RQ2 — Evaluative stance:** To what extent can ESA representations capture distinctions in narrator-directed scholarly evaluations beyond simple lexical or polarity features?
- **RQ3 — Relational information:** Does adding a documented narrator transmission graph improve narrator-grade prediction over appropriate text-only and non-graph baselines?
- **RQ4 — Reliability of the evidence pipeline:** How do source provenance, narrator identity resolution, missingness, and label construction affect the validity of the resulting experiments?

Do not treat these questions as approved replacements for PO1–PO3. Map each question to the existing objectives and obtain supervisor approval before changing formal scope.

## 5. Research objectives

Copy the exact approved PO1, PO2, and PO3 wording into this section before finalising the protocol. For each objective, record:

- the research question it addresses;
- the evidence and data required;
- the method used;
- the measurable output;
- the acceptance or completion criteria;
- known limitations.

**Approved objective wording:** TODO — insert verbatim from the approved proposal.

## 6. Scope boundaries

- Focus on narrator-level computational analysis, not automatic authentication of complete hadith.
- Treat classical scholarly judgements as historically situated source evidence.
- Do not collapse disagreement between critics into a single label without a documented aggregation rule.
- Do not infer narrator identity from name similarity alone.
- Do not infer a valid teacher–student relationship solely from co-occurrence in a chain.
- Do not claim that graph edges establish continuity or direct transmission.
- Do not describe model outputs as fatwa, takhrīj, or classical scholarly verdicts.

## 7. Evidence and data requirements

Every retained record should, where available, preserve:

- original Arabic text;
- critic identity and authority attribution;
- narrator identity and canonical identifier;
- source work, author, edition, volume, page, and stable locator;
- quotation boundaries and surrounding context;
- transcription or digitisation method;
- normalisation and transformation history;
- confidence or uncertainty flags;
- licence and permitted-use information.

Missing fields must be represented explicitly. Unknown is not equivalent to false, absent, or negative.

## 8. Methodology decision gates

| Gate | Required evidence before proceeding |
|---|---|
| G1 — Research framing | Approved objectives mapped to questions, scope, and measurable outputs |
| G2 — Source selection | Source provenance, access, licence, edition, and suitability assessed |
| G3 — Dataset construction | Schema, inclusion/exclusion rules, identity resolution, and quality audit documented |
| G4 — Target validity | Reference label source, mapping rules, disagreement, and leakage risks documented |
| G5 — Method selection | ESA and graph components have theoretical and empirical justification |
| G6 — Experimental validity | Baselines, split strategy, metrics, seeds, and ablations specified |
| G7 — Claims and reporting | Results reproducible; limitations and failure cases reported |

A gate is not passed merely because code runs.

## 9. Experimental principles

- Use narrator-disjoint splits when the research question requires generalisation to unseen narrators.
- Prevent duplicate statements, alternate spellings, or related records from leaking across partitions.
- Fit preprocessing and learned transformations on training data only.
- Report class distribution and per-class performance alongside aggregate metrics.
- Use Macro-F1 when class imbalance makes equal class weighting appropriate; also report the confusion matrix and per-class precision/recall/F1.
- Compare against simple, defensible baselines before claiming value from ESA or graph learning.
- Use ablations to isolate the contribution of each modality.
- Record random seeds, software versions, hardware, hyperparameters, and exact data snapshots.
- Report failed experiments and limitations, not only the best result.

## 10. Change control

Any change to the prediction target, label source, dataset population, objective mapping, graph definition, or evaluation protocol must be entered in `governance/DECISION_LOG.md` and `governance/CHANGELOG.md`, with rationale and impact. Changes affecting approved FYP scope require supervisor confirmation.
