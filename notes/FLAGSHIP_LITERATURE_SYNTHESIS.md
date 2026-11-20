# Flagship Literature Synthesis (`taqrib-oriented`)

Critical comparative synthesis positioning our `taqrib-oriented` framework against the 6 flagship references registered in [FLAGSHIP_REFERENCES_REGISTER.csv](../literature/flagship_references/FLAGSHIP_REFERENCES_REGISTER.csv).

---

## 1. Comparative Positioning Matrix

| Reference | Domain / Task | Dataset & Scale | Core Method | Key Reported Metrics | Key Limitation Addressed by Our Framework |
|---|---|---|---|---|---|
| **Bilgin (2026)** (*OMÜİFD*) | Descriptive census of *Taqrīb al-Tahdhīb* | `8,826` entries (`8,260` assigned across 12 *marātib*) | Manual document analysis & descriptive statistics | Counts & % shares across 6 *Taʿdīl* + 6 *Jarḥ* ranks | Purely descriptive; cites *Taḥrīr* only qualitatively (p. 243) without quantifying overrides or modeling transmission graphs. |
| **Wahba et al. (2026)** (*Discover AI*) | Hadith narrator reliability classification (6-tier / binary) | Small curated corpus from 3 classical texts (explicitly notes dataset-size limitation, p. 25) | Classical lexicon rules + NB, SVM, RF, CNN | Test Acc = `88.89%`, Prec = `79.48%`, Rec = `88.89%` | Small dataset, bag-of-words/CNN without modern Arabic transformers (`AraBERTv02`), and no transmission graph structure. |
| **Alturayeif et al. (2024)** (*ArabicNLP — StanceEval*) | Arabic stance detection (`Favor / Against / None`) | `MAWQIF` (`4,121` Arabic tweets) | Shared task; top systems fine-tuned Arabic transformers (`AraBERT` / `MARBERT`) + TF-IDF fusion | Macro-F1 (`84.38%` top shared-task score) | Social-media MSA/dialectal text only; no ordinal rank hierarchy or graph structure. |
| **Mahmoud et al. (2024)** (*Neural Comput. & Appl.*) | Narrator disambiguation in Sanad chains | `AR-Sanad 280K-v2` + `NarratorsKG` | Sanad graph querying + `AraBERT` re-ranking | `94.6%` disambiguation accuracy | Resolves *who* a narrator is in a chain, not *how reliable* they are or whether classical *Taqrīb* grades require revision. |
| **Zeng et al. (2024)** (*Data Sci. & Eng.*) | Multi-view heterogeneous GNN (`MV-HGNN`) for node classification | Citation networks (`ACM`, `DBLP`) | Graph diffusion + global feature similarity (`kNN`) + transformer view aggregation | Micro/Macro-F1 on node classification | General citation/academic benchmark; untested on asymmetric historical transmission chains with temporal impossibility noise. |
| **OUP DSH (2025)** *(Paywalled — metadata/abstract only)* | Knowledge graph-transformer narrator disambiguation | Hadith networks | Knowledge graph + Transformer | *Full text unavailable (paywalled)* | Targets entity disambiguation rather than scholar-verified *Taqrīb* vs. *Taḥrīr* reliability enrichment. |

---

## 2. How Our `taqrib-oriented` Pipeline Extends Each Reference

1. **Quantifying Bilgin (2026)'s Qualitative *Taḥrīr* Critique:**
   - We adopt Bilgin (2026)'s peer-reviewed 12-rank *Taqrīb* taxonomy directly as **Score 1**, then operationalize what Bilgin leaves qualitative: aligning **8,823 / 8,827 (99.95%)** *Taqrīb* entries with al-Arnāʾūṭ & Maʿrūf's *Taḥrīr Taqrīb al-Tahdhīb* (`8246`) to produce `7,469` scholar-verified **Score 2 targets** (`N = 7,258` both-ranked core cohort) with **zero subjective self-annotation**.

2. **Scaling & Upgrading Wahba et al. (2026):**
   - Instead of a small manually compiled set, we evaluate across **`N = 7,258` narrators** (`test = 1,089`) with strict split isolation and name-stripped ablations (`M3c`).
   - On the aligned Binary *Taʿdīl* (`1–6`) vs. *Jarḥ* (`7–12`) benchmark, our fine-tuned **Name-Stripped AraBERTv02 (`0.9036`)** and **Stage 3 TC-GNN (`0.9054–0.9073`)** exceed Wahba et al.'s `0.8889` test accuracy while also predicting full **12-rank ordinal grades (`MAE = 0.6523`, `QWK = 0.8903`)**.

3. **Adapting Alturayeif et al. (2024 — StanceEval) to Evaluative Shift:**
   - We cast *Taḥrīr*'s revision relative to Ibn Ḥajar as a 3-class evaluative stance/shift task (`upgraded` / `unchanged` / `downgraded`) and evaluate with **3-class Macro-F1** and **Active-Shift Macro-F1** ($\frac{1}{2}(\text{F1}_{\text{up}} + \text{F1}_{\text{down}})$), reaching **`0.7301` Shift Macro-F1** (`G4a` ensemble).

4. **Extending Mahmoud et al. (2024) from Identity to Temporal-Causal Reliability:**
   - Whereas Mahmoud et al. combine Sanad graphs with `AraBERT` for narrator *identification*, we pair 5-fold OOF `AraBERTv02` representations with **temporal-causal pruning** ($\Delta\text{ṭabaqah} \le -2$, removing `4,647` noisy edges) and **directional edge-conditioned `GATv2`** (`Teacher → Student` + `Student → Teacher` corroboration) for narrator *reliability enrichment*.

5. **Validating Zeng et al. (2024)'s Multi-View Similarity Insight on Sparse Historians:**
   - Because `34.2%` of core narrators are isolated in pure Sanad chains, adding Zeng et al.'s **Semantic kNN (`k=8`) view (`G4c`)** reduces 5-seed Rank MAE variance (`0.0124 → 0.0017`) and significantly boosts Binary Accuracy over Stage 2 (`0.9063`, `p = 0.009`), while keeping pure historical edges (`G4a`) cleanly separated for interpretability.
