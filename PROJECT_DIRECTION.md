# Project Direction and Masterplan

**Status:** Controlling document for all work on this repository. Adopted 2026-11-21.
**Owner:** Alan (`alansyahmi`)
**Supervisor sign-off:** *pending* (see §10)
**Detailed implementation steps:** [`research_protocol/IMPLEMENTATION_PLAN_LAYERED_SCORE_V3.md`](research_protocol/IMPLEMENTATION_PLAN_LAYERED_SCORE_V3.md)

> **Rule of use.** Any change to the title, objectives, target, data sources, layer rules or evaluation protocol must first be recorded in [`governance/DECISION_LOG.md`](governance/DECISION_LOG.md) and then reflected here. Work that does not serve an objective in §3 is out of scope until this document is amended.

---

## 1. Thesis title

**A Multi-Modal Framework for Quantifying Narrator Reliability in ʿIlm ar-Rijāl Using Evaluative Stance and Graph Neural Networks**

How each part of the title maps to the work:

| Title term | Meaning in this project | Component |
|---|---|---|
| Multi-modal | Three input types, each tested on its own: text, structured *Taqrīb* metadata, and the sanad transmission graph | Stage 2 + Stage 3 |
| Quantifying narrator reliability | A traceable 0–100 score (equivalently S ∈ [0, 1]) that encodes **scholars' assessments** of narrator reliability. It does not claim to measure reliability independently of those scholars | Layered score B → E₁ → E₂ (§4) |
| ʿIlm ar-Rijāl | Sources are *Taqrīb al-Tahdhīb* (Ibn Ḥajar) and *Taḥrīr Taqrīb al-Tahdhīb* (al-Arnāʾūṭ and Maʿrūf) | Stage 1 |
| Evaluative Stance | Evaluative Stance Analysis (ESA), defined in §2.2 | Stage 2 |
| Graph Neural Networks | TC-GNN, defined in §2.1 | Stage 3 |

## 2. Definitions

### 2.1 TC-GNN

**TC-GNN = Text-Classification-informed Graph Neural Network.** The node features of the graph model include the out-of-fold outputs of the Stage 2 ESA text classifier, together with *Taqrīb* metadata and sanad structure features. The graph is a directed teacher → student transmission graph.

Earlier branch documents expanded "TC" as "Temporal-Causal". That expansion is **retired**. The step that removes chronologically impossible edges (where the student's ṭabaqah is two or more generations earlier than the teacher's) is called **ṭabaqah chronology pruning**.

### 2.2 Evaluative Stance Analysis (ESA)

ESA is the analysis of the evaluative judgement a scholar expresses about a narrator. It is not generic sentiment or positive/negative polarity (DEC-001). In this project ESA has two parts:

- **(a) Verdict stance.** The strength of Ibn Ḥajar's verdict on his 12-rank scale, plus the qualifiers that limit it (for example *yudallis*, *ikhtalaṭa*, *yukhṭiʾ*).
- **(b) Editorial stance.** The stance of the *Taḥrīr* editors towards Ibn Ḥajar's verdict: **agree**, **upgrade** or **downgrade**. This is a 3-class stance task of the kind used in StanceEval 2024.

A generic Arabic sentiment model (CAMeLBERT-sentiment) is kept only as a **baseline**, to show that sentiment is not evaluative stance.

### 2.3 Score scale

- Rank r ∈ {1, …, 12} (Ibn Ḥajar's *marātib*, operationalised following Bilgin 2026) maps to the centre of a band: `S(r) = 100 × (12 − r) / 11`.
- Each rank owns a band of half-width 100/22 around its centre. The taʿdīl/jarḥ boundary (r = 6.5) falls at 50.
- The 3-tier class is derived from the rank: 1–3 / 4–6 / 7–12.
- Rank 1 (*Ṣaḥābah*) is a status category, not a graded judgement. Results are reported with and without it.

## 3. Objectives

Revised from the earlier project version. **The revised wording is pending supervisor sign-off.**

- **PO1.** To develop an Evaluative Stance Analysis (ESA) text-classification model, together with a deterministic, provenance-traceable layered scoring scheme, that maps Ibn Ḥajar's Jarḥ wa Taʿdīl judgements in *Taqrīb al-Tahdhīb* and the editorial verdicts of *Taḥrīr Taqrīb al-Tahdhīb* onto a standardised reliability index (S ∈ [0, 1], also reported on a 0–100 scale), Ibn Ḥajar's 12-rank ordinal scale and a 3-tier classification, under strict zero-leakage conditions.
- **PO2.** To construct an audited, chronology-checked knowledge graph of narrator transmission relationships, and to run a controlled multi-arm ablation study testing whether a Text-Classification-informed Graph Neural Network (TC-GNN) explains the *Taḥrīr* editors' revisions of Ibn Ḥajar's grades beyond text-only and simple graph-feature baselines, including an analysis of transmission-network heterophily.
- **PO3.** To evaluate the validity of the resulting reliability scores by measuring the incremental contribution of each enrichment layer (*Taqrīb* baseline, *Taqrīb* qualifiers, *Taḥrīr* verdicts, graph) and their agreement with an independent existing scholarly classification (al-Dhahabī's *al-Kāshif*), with explicit treatment of missing evidence and source overlap.

The earlier PO3 (comparing isnād-level scores with al-Albānī and Darussalam hadith grades) was **replaced** on 2026-11-21 by the owner's decision. No code or data for it exists in this repository.

## 4. Framework design: the layered score

Two tracks are kept strictly apart.

| Track | Layers | How it is produced | Role |
|---|---|---|---|
| **R — Representation** | **B** → **E₁** → **E₂** | Fixed, versioned rules. Nothing is learned | The 0–100 score with an evidence trail |
| **L — Learning / validation** | ESA classifier, then **G** (TC-GNN) | Trained models | Tests what text and graph evidence can explain. Supplies labelled estimates where scholarly evidence is missing |

| Layer | Source | Effect on the score |
|---|---|---|
| **B: Baseline** | Ibn Ḥajar's grade in *Taqrīb* | Sets the narrator's rank band. Immutable |
| **E₁: Textual enrichment** | Qualifiers in the *Taqrīb* entry **outside** the rank-defining phrase | Moves the score **within** B's band only, capped, with weights fixed in a versioned config |
| **E₂: Editorial enrichment** | *Taḥrīr* dispositions: agreed / `• بل:` / `• قوله` / other | `بل:` **replaces** the band with the editors' rank. Agreement adds nothing (it is corroboration, recorded as a flag). Other comments change the score only where a grade is stated |
| **G: Relational enrichment** | TC-GNN over the chronology-pruned sanad graph | **Never alters an observed scholarly verdict.** Where *Taḥrīr* is observed, G is reported only as a diagnostic (agrees / residual). Where it is missing, G supplies `score_G_estimate` with an uncertainty value, flagged as a model estimate |

### 4.1 Safeguards (binding)

1. **Provenance.** Every score change is a row in an evidence table: entry, layer, source book, part and page, verbatim Arabic span, rule ID and delta. The final score must be reproducible from that table alone.
2. **No double-counting.** A qualifier that is part of the phrase defining the rank gets zero weight. *Taḥrīr* agreement is not extra evidence. A `بل:` verdict replaces the band rather than adding to it.
3. **Missing ≠ negative ≠ unchanged.** Every layer has its own status for each narrator: `observed`, `not_applicable`, `missing`, `abstained` or `suspect_alignment`. Rows with missing evidence are excluded from that layer's metrics and reported as coverage.
4. **Representation ≠ truth.** A score of 85 is a position on this project's defined scale. It is not a probability that a narrator is reliable, and it is not a ruling on any hadith.
5. **Zero leakage.** *Taḥrīr* columns never appear in model inputs. The Shamela `narrators.csv`/`.parquet` grade and ṭabaqah fields are banned as inputs, because they are verbatim *Taqrīb* text. Preprocessing is fitted on the training split only, and text features are out-of-fold.
6. **Sensitivity over authority.** The E₁ weights are a modelling choice. Every conclusion is re-checked with the weights halved, with them doubled, and with E₁ removed.
7. **Determinism.** Seeds are fixed. Model configurations are selected by the 5-seed mean validation score. Every result folder carries a manifest of input hashes.

## 5. Experiments

| Exp | Information included | Evaluated against |
|---|---|---|
| **A** | B only | *Taḥrīr* (test split), *al-Kāshif* |
| **B** | A + E₁; learned form: ESA text classifier | *Taḥrīr* shift, *al-Kāshif* |
| **C** | B + E₂ (deterministic) | *al-Kāshif* only. C contains *Taḥrīr*, so it cannot be scored against it. Reports how far *Taḥrīr* moves scores |
| **D** | B + E₁ + ESA + graph (TC-GNN) predicting the *Taḥrīr* shift | *Taḥrīr* (test). Must be compared with the **MLP + 1-hop graph-feature baseline**, not only with the no-graph model |

**Statistics:** 5 seeds, paired bootstrap (B = 2,000), 95% CI. Comparisons run A→B and B→D, and D against the graph-feature baseline. A GNN benefit is claimed **only** if multi-hop message passing beats the graph-feature baseline.

**Metrics:**

- Ordinal: rank MAE, QWK, Spearman.
- Binary taʿdīl/jarḥ.
- 3-tier Macro-F1.
- 3-class shift Macro-F1.
- Edge and class homophily of the graph.
- Slices: rank 6 *maqbūl*, *Taqrīb*-abstained entries, isolated vs connected narrators.

## 6. Data sources

| Source | Shamela ID | Role |
|---|---|---|
| Ibn Ḥajar, *Taqrīb al-Tahdhīb* (ed. ʿAwwāma, 1406/1986) | 3076 | Layer B, E₁; text input |
| al-Arnāʾūṭ and Maʿrūf, *Taḥrīr Taqrīb al-Tahdhīb* (1417/1997) | 8246 | Layer E₂; target for Track L |
| al-Dhahabī, *al-Kāshif* | 1616 | External validation only (PO3) |
| Sanad / Bukhārī transmission edges (existing pipeline) | — | Graph for Layer G |
| Bilgin (2026), *OMÜİFD* 60 | — | Grounding for the 12-rank mapping |

Al-Dhahabī predates Ibn Ḥajar, and Ibn Ḥajar drew on him: about a quarter of al-Dhahabī's grades appear word for word in *Taqrīb*. Agreement with *al-Kāshif* is therefore reported both on all linked narrators and on the subset that does **not** overlap verbatim. Only the second figure counts as convergent evidence.

## 7. No-expert-annotation stance

This project does **not** create new expert labels.

- **Taqrīb labels** are Ibn Ḥajar's own taxonomy, applied by deterministic rules.
- **Taḥrīr labels** are verdicts already written by two named hadith scholars.
- **al-Kāshif** is an existing classical classification.

Human checking is limited to **extraction QA**: confirming that the parser reads the Arabic correctly. That work is the blind 120-entry check (120/120), the 99.95% *Taqrīb*–*Taḥrīr* alignment, and the Gold-50 source adjudication. The dual-reviewer ESA annotation pilot proposed on `main` (v2.0 report) is **superseded** and will not be run.

## 8. Out of scope

- Authenticating hadith, or grading isnāds or chains. Any chain-level output would be a computational analysis, not a scholarly ruling.
- Claiming that a model output is an independent judgement of a narrator's reliability.
- Using the GNN to raise or lower a narrator's score on network position alone.
- Statement-level stance analysis of early critics (the `main` Task B line). It is preserved on `frozen-v1` and `main` but not continued.
- Creating new expert annotations (§7).
- Rewriting git history or changing frozen artefacts (`frozen-v1`, `frozen-v2-taqrib-oriented`, tag `v2.0-taqrib-frozen`).

## 9. Branches and order of work

- **`taqrib-oriented-v2`** is the active line for this direction. It was branched from `taqrib-oriented` at `935bd09`, which stays frozen as `frozen-v2-taqrib-oriented` and tag `v2.0-taqrib-frozen`. `main` holds the older Task A/B work, and `frozen-v1` preserves it.
- Work proceeds in the phases P0–P6 of the [implementation plan](research_protocol/IMPLEMENTATION_PLAN_LAYERED_SCORE_V3.md):
  - P0: test portability and CI
  - P1: governance and naming
  - P2: layer builder
  - P3: *al-Kāshif* validation
  - P4: re-run ESA and TC-GNN
  - P5: experiments A–D
  - P6: deliverable, documentation and merge to `main`

## 10. Pending decisions

| Item | Owner | Status |
|---|---|---|
| Supervisor sign-off on revised PO1–PO3 and on dropping the expert pilot | Alan + supervisor | Pending |
| Raw Shamela corpus kept in the repo or removed (licence, repo visibility) | Alan | Pending |
| Output column renaming (rename at source vs glossary) | Alan | Default: rename at source |
| E₁ default weights | Alan | Defaults proposed in plan P2.3 |
| PO3 choice | Alan | **Decided 2026-11-21:** layer validation + *al-Kāshif* |
