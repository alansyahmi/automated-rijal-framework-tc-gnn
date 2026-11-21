# Research Protocol

**Version:** 0.1 (initial working protocol)  
**Status:** Draft — requires review and approval where changes affect approved FYP scope.

## 1. Research identity

**Working research area:** Computational analysis of narrator evaluations in ʿIlm al-Rijāl.

**Thesis title (controlling):** *A Multi-Modal Framework for Quantifying Narrator Reliability in ʿIlm ar-Rijāl Using Evaluative Stance and Graph Neural Networks*.

The controlling thesis title and supervisor-approved PO1–PO3 govern the formal FYP scope. This protocol records the aligned terminology: **Evaluative Stance Analysis (ESA)** (reclassifying generic polarity models as a generic-sentiment baseline, per `DEC-001` and `DEC-006`) and **TC-GNN = Text-Classification-informed Graph Neural Network** (`DEC-006`).

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

> **Approval status:** **Awaiting supervisor approval** for the revised PO1–PO3 wording below (Alan selected **PO3 Option A** on 2026-11-21; see [IMPLEMENTATION_PLAN_LAYERED_SCORE_V3.md](IMPLEMENTATION_PLAN_LAYERED_SCORE_V3.md) §9). Until formal supervisor confirmation is recorded, both the earlier project objectives and the proposed revisions are preserved side-by-side.

### 5.1 Earlier project objectives (historical baseline)

- **Old PO1:** NLP classification model mapping *Jarḥ wa Taʿdīl* judgements to a reliability index $S \in [0, 1]$ and a 3-tier ordinal class $y \in \{0, 1, 2\}$, under zero leakage.
- **Old PO2:** Audited narrator transmission knowledge graph + controlled multi-arm ablation testing whether structural features help or heterophily hurts.
- **Old PO3 *(dropped per DEC-007 / Option A)*:** Isnād-level scores (weakest-link + preliminary *mutābaʿāt*/*shawāhid*) vs al-Albānī and Darussalam hadith grades (conflicts with §6 scope boundary against automatic hadith authentication; no data/code exists in the workspace).

### 5.2 Proposed revised objectives (awaiting supervisor approval)

- **PO1:** To develop an Evaluative Stance Analysis (ESA) text-classification model, together with a deterministic, provenance-traceable layered scoring scheme, that maps Ibn Ḥajar's *Jarḥ wa Taʿdīl* judgements in *Taqrīb al-Tahdhīb* and the editorial verdicts of *Taḥrīr Taqrīb al-Tahdhīb* onto a standardised reliability index ($S \in [0, 1]$, also reported on a 0–100 scale), Ibn Ḥajar's 12-rank ordinal scale, and a 3-tier classification (`1–3 / 4–6 / 7–12`), under strict zero-leakage conditions.
- **PO2:** To construct an audited, chronology-checked knowledge graph of narrator transmission relationships, and to run a controlled multi-arm ablation study testing whether a Text-Classification-informed Graph Neural Network (TC-GNN) explains the *Taḥrīr* editors' revisions of Ibn Ḥajar's grades beyond text-only and simple graph-feature baselines, including an analysis of transmission-network heterophily.
- **PO3 *(chosen by Alan on 2026-11-21: Option A — awaiting supervisor approval)*:** To evaluate the validity of the resulting reliability scores by measuring the incremental contribution of each enrichment layer (*Taqrīb* baseline, *Taqrīb* qualifiers, *Taḥrīr* verdicts, graph) and their agreement with an independent existing scholarly classification (al-Dhahabī's *al-Kāshif*), with explicit treatment of missing evidence and source overlap.

### 5.3 Objective-to-pipeline mapping (`taqrib-oriented-v2`)

| Objective | RQs | Track / Layers | Experiments & Scripts | Measurable Outputs & Acceptance |
|---|---|---|---|---|
| **PO1** | RQ1, RQ2 | **Track R:** `B` (`score_B`), `E₁` (`score_E1`) + **Track L:** Stage 2 ESA (`M0–M3c`) | P2 (`build_layered_scores_v3.py`), P4.1 (`run_stage2_esa_benchmarks_v3.py`), P5 (`Exp A`, `Exp B`) | `LAYER_EVIDENCE_LONG_V3.csv`, `LAYERED_SCORES_WIDE_V3.csv`, 12-rank MAE/QWK/Macro-F1, 3-tier (`1–3/4–6/7–12`) Macro-F1, binary *taʿdīl*/*jarḥ*, 3-class shift Macro-F1, zero-leakage assertions |
| **PO2** | RQ3 | **Track L:** Audited Sanad KG (`chrono_pruned`: 42,011 → 37,364) + Stage 3 TC-GNN (`G0–G4d`) | P4.2 (`run_stage3_tc_gnn_benchmarks_v3.py`), P5 (`Exp D`: `G4` vs `G2b` & `G0`, plus edge/class homophily) | 5-seed mean metrics + paired bootstrap ($B = 2{,}000$), explicit `G4` vs `G2b` 1-hop baseline comparison, homophily/heterophily diagnostics, `score_G_estimate` (`source = model_estimate` only where *Taḥrīr* is missing/abstained) |
| **PO3 (Opt A)** | RQ1, RQ4 | **Track R + L:** `B → B+E₁ → B+E₁+E₂` + *al-Kāshif* (`1616`) external validation | P2, P3 (`build_kashif_validation_v1.py`), P5 (`Exp A–D`, E₁ weight sensitivity) | Per-layer Δ & missingness audit, E₁ sensitivity table, convergent 3-tier Macro-F1 / κ / Spearman vs *al-Kāshif* reported on both full linked set and non-verbatim subset, `FINAL_LAYERED_RIJAL_SCORES_8827_V3.csv` |

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
