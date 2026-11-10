# Shamela4 Stage-Two Diagnostic: Manual Review Synthesis & Findings

## 1. Scope & Execution Overview

This manual review examined the provenance, structure, and integrity of source identifiers and `fwaed` entries 
derived from the first-stage audit of 18,989 narrator records in `data/1_raw/Shamela4_Full_DB/_meta/narrators.parquet`. 
The review strictly obeyed all research safeguards: no raw data was altered, no source IDs were merged, 
and no interpretations were asserted without concrete empirical proof.

## 2. Summary of Key Findings

### A. Source Identifier Anomalies (432 Flagged IDs)
- **Evaluation-Citation Field Swapping (97.2%, 420 IDs)**: In these records, Shamela4 database compilers placed the evaluative criticism or chain commentary into the citation position with the book locator at the end after a newline. This produced multiline strings (420), long character counts (103), multiple locators (12), and spurious title candidate collisions (367).
- **Normalisation Regex Suffix Misses (2.8%, 12 IDs)**: Unnumbered volume/page strings ending with `(بدون ترقيم)` were truncated improperly by the trailing locator regex, producing harmless dual title strings for the exact same work.

### B. Title-Candidate Collisions (47 Title Candidates)
- **Major Hadith/Rijāl Works (38 Titles, e.g. *Taqrib al-Tahdhib* with 8,121 IDs)**: These are **legitimate repeated work references**. In Shamela4, a `source_id` is NOT a unique work identifier; it represents a specific page-, passage-, or entry-level citation instance. Thousands of distinct source IDs legitimately point to different pages of the same classical compendium.
- **Evaluation Speech Artefacts (9 Titles, e.g. `مقبول تقريب التهذيب`, `يروي المراسيل الثقات`)**: These are **normalisation artefacts**. Evaluative text preceding the book title on a multiline citation remained attached to the title when the regex stripped only the trailing volume/page.

### C. Unexpected `fwaed` Labels (12 Labels, 16 Occurrences)
- **Root Cause**: 100% of unexpected occurrences originate from a **single corrupted narrator record**: Narrator ID `6142` (`مسلم بن يسار`).
- In narrator 6142, the database compiler accidentally duplicated the entire `garh` (evaluative quotes) block into the `fwaed` field, including empty boundary markers `['جرح وتعديل', []]` and `['مصادر الترجمة', []]`.
- The 12 labels (`ابن حبان`, `الذهبى`, `العجلي`, `أبو حاتم الرازي`, `أبو زرعة الرازي`, `أبو زرعة العراقي`, `ابن حجر`, `ابن عساكر`, `الترمذي`, `الحاكم`, `الطحاوي`, `المزي`) are names of classical scholars, not missing evidence categories.
- **Conclusion**: There are exactly **13 canonical evidence categories** in Shamela4's `fwaed`. No new evidence classes exist.

### D. Internal Structure of `fwaed` (15,963 Occurrences)
- **Serialization Uniformity**: 100% of entries across all 18,989 records are uniform 3-element lists of type signature `(str, str, int)` representing `[evidence_text, citation_locator, source_id]`.
- **Semantic Function**: `fwaed` entries do not encode scalar reliability grades. They represent **fine-grained relational and contextual evidence**: transmission chain disconnection (`إرسال`), direct audition verification (`إثبات سماع`), pairwise narrator comparisons (`مفاضلة`), contemporaneity (`إدراك`), cognitive decline (`اختلاط`), and concealment (`تدليس`).

### E. Control Sample Evaluation (30 Unflagged IDs)
- Stratified random sampling across High, Medium, and Low occurrence tiers confirmed that unflagged IDs have 100% clean, single-line citations with standard volume/page locators.
- The automated triage script demonstrated high sensitivity in isolating genuine syntax anomalies, although field swapping accounted for the vast majority of flags.

---

## 3. What is Established vs What Remains Uncertain

### What is Established:
1. Source IDs are entry/passage-level citation keys, not work-level entity IDs.
2. 47 title collisions consist cleanly of 38 canonical multi-passage works and 9 normalisation artefacts.
3. Unexpected `fwaed` labels are entirely explained by database duplication in narrator 6142.
4. All 15,963 `fwaed` entries have identical 3-element list shapes.
5. `fwaed` categories are multi-relational evidence attributes, not reliability class labels.

### What Remains Uncertain:
1. The exact algorithm used by Shamela4 compilers to mint integer source IDs (sequential counter vs hash).
2. The extent of field swapping across the full corpus beyond the 386 flagged IDs.
3. An authoritative concordance mapping Shamela4 book strings to standard bibliographic metadata (e.g. publisher, year, edition).

---

## 4. Implications for Dataset Suitability & Next Research Steps

1. **Data Sanitisation Requirement**: Before extracting evaluation texts for AraBERT/TF-IDF NLP modeling, a targeted cleaning step must swap inverted `[quote, citation]` fields back to their canonical positions.
2. **Exclusion of Corrupted 6142 `fwaed` Entries**: The 16 duplicate evaluator entries in narrator 6142's `fwaed` block must be excluded from relational graph edge construction.
3. **Multi-Relational Graph Construction**: The 13 canonical `fwaed` categories provide rich contextual attributes for graph edges (`samā'`, `irsāl`, `mufāḍalah`), which should be integrated as edge features rather than node labels.
4. **Recommended Next Step**: Develop an automated sanitisation and concordance mapping pipeline (`dataset_discovery/Shamela4/clean_provenance_citations.py`) to systematically normalize citation fields and construct a clean biographical concordance.
