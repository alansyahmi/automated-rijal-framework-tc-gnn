# DS-001 — Hadith Knowledge Graph (HKG) Initial Audit

**Audit date:** 2026-11-07  
**Status:** Under audit — not selected  
**Scope of this pass:** Public repository documentation, SQLite schema definition, database build script, and published data-quality report.  
**Important limitation:** The released SQLite database itself has not yet been downloaded and queried in this pass. All counts below are source-reported, not independently recomputed by this project.

## 1. Source identity and lineage

The project describes the canonical database as being built from a MongoDB BSON dump of the `hadithdb/hadith/` collections, identified in the build script as a `mongodump Oct 2017`, plus a separate `rawa_cat.csv` file for meaning groups.

The project README states that the original raw 2017 source dump is not distributed. The published SQLite database is therefore a transformed derivative, and the released build pipeline cannot be fully reconstructed from the publicly described source assets alone.

Sources:
- [HKG repository README](https://github.com/emadjumaah/hadith/blob/main/README.md)
- [HKG build script](https://github.com/emadjumaah/hadith/blob/main/build_hkg.py)
- [HKG dataset card](https://huggingface.co/datasets/emadjumaah/hadith-kg)

## 2. Relevant schema

The build script defines these relevant tables:

| Table | Relevant fields | Research role |
|---|---|---|
| `rawis` | `id`, `name`, `nickname`, `rank_no`, `rank`, `tabaka`, dates, `has_ikhtilat`, `has_tadlis` | Narrator registry and biographical / grading fields |
| `alems` | `id`, names, `tabaka`, `death_year`, `rank_no`, `rank`, `aqwal_qty` | Critic registry |
| `aqwal` | `id`, `alem_id`, `rawi_id`, `qawl` | Critic-attributed evaluative statement linked to a narrator |
| `sanads` | `id`, `hadith_id`, `hukum`, `group_id`, `max_rank`, `length` | Chain-level records |
| `sanad_rawis` | `sanad_id`, `pos`, `rawi_id` | Ordered narrator membership in a chain |

The build script maps the source BSON fields for an aqwal record directly as:

- `id` ← `d['id']`
- `alem_id` ← `d['alem_no']`
- `rawi_id` ← `d['rawi_no']`
- `qawl` ← `d['qawl']`

This is useful structural information: the released data distinguishes the critic, narrator, and statement text. It is not, however, enough to establish the full textual provenance of each statement.

Source: [build_hkg.py](https://github.com/emadjumaah/hadith/blob/main/build_hkg.py).

## 3. Critical finding: statement-level provenance is missing from the released schema

The `aqwal` table has no fields for:

- original classical work or compilation;
- author of the work (as distinct from the critic);
- edition, publisher, or publication details;
- volume, page, folio, hadith/biography number, or stable passage locator;
- exact surrounding context or quotation boundaries;
- whether the statement is a direct quotation, paraphrase, or later transmission;
- transcription / extraction method or source-specific confidence.

Consequently, a row can tell us *which critic is attributed as speaking*, *which narrator is being evaluated*, and *what text is stored*, but it cannot independently show *where that wording occurs in a primary source*.

This is a major limitation for ESA. A critic-attributed sentence is not fully auditable merely because the critic and narrator IDs are linked. We need to establish the source passage, context, and attribution before treating the row as reliable training or evaluation evidence.

**Implication:** HKG may be useful for discovery, candidate sampling, and exploratory analysis. It is not yet suitable as the sole source of gold-standard ESA annotations without additional provenance work.

## 4. Critical finding: potential target leakage through narrator grades

The `rawis` table includes `rank_no` and `rank`. The build script imports these directly from the rawi BSON records. The schema comment identifies examples of rank values such as `ثقة`, `صدوق`, `ضعيف`, and `صحابي`.

If these fields are used to define the narrator-classification target, they must be excluded from the model's input features. The same applies to derived fields that reproduce or encode the target label.

Before defining the target, investigate:

1. the full distribution and meaning of `rank_no` and `rank`;
2. whether rank is a single source judgement, a platform-level aggregation, or another derived field;
3. the exact mapping from rank codes to labels;
4. whether narrator flags or metadata were themselves derived from the same grading process;
5. whether any `aqwal` text duplicates or directly restates the target grade.

**Current decision:** treat `rawis.rank` and `rawis.rank_no` as candidate target fields only. Do not treat their meaning, provenance, or validity as established ground truth yet.

## 5. Published quality-report observations

The repository's `DATA_REPORT.md`, generated on 2026-07-09, reports:

| Check | Reported result | Why it matters |
|---|---:|---|
| `aqwal` records | 127,863 | Potential statement corpus size; not a measure of valid ESA examples |
| `alems` records | 1,015 | Critic entities |
| Exact duplicate `(alem, rawi, qawl)` triples | 6 | Small reported duplicate count, but semantic duplicates are not assessed |
| Critics with `aqwal_qty` differing from actual statement count | 135 / 1,015 | Internal metadata inconsistency |
| Same-name / same-nickname narrator groups | 421 | Name-only entity matching is unsafe |
| Stub narrators created during cleanup | 25 | Some chain-linked narrator records lacked source biographies |
| Narrators unused in chains, mentions, and aqwal | 89 | Registry includes entities not used in the main relation tables |
| Narrator mentions still null | 6,302 | Hadith-text mention resolution issue |
| Narrator mentions still unknown | 2,028 | Identity-resolution issue |
| Unrepairable mentions | 8,309 | Further chain/text reconciliation needed |

These figures come from the project's own quality report. They do not establish that the aqwal statements themselves are correctly attributed or textually verified.

A further inconsistency requires clarification: the README and dataset card report 49,819 narrator biographies, while the quality report and schema audit report 49,844 rows in `rawis`. This may reflect different build stages or counting conventions, but it must be reconciled before citing a definitive narrator count.

Source: [DATA_REPORT.md](https://github.com/emadjumaah/hadith/blob/main/DATA_REPORT.md).

## 6. Preliminary suitability assessment

| Research component | Initial assessment | Reason |
|---|---|---|
| ESA statement discovery | Promising, conditional | Large attributed statement table, but no source locators in released schema |
| Critic attribution | Structurally promising | `aqwal.alem_id` links to `alems`; correctness still needs sampling |
| Narrator attribution | Structurally promising | `aqwal.rawi_id` links to `rawis`; homonyms and entity resolution need review |
| Narrator-grade target | Unverified | `rawis.rank` / `rank_no` available, but semantics and provenance need investigation |
| Transmission graph | Promising but separate audit needed | Chain relations are represented in `sanad_rawis`; chain evidence is not equivalent to direct teacher-student proof |
| Primary-source verification | Insufficient as released | Aqwal rows lack work / edition / page / passage provenance |
| Reproducibility | Partial | Build code is available, but original 2017 BSON source dump is not distributed |

## 7. Decisions

1. Keep DS-001 at **Under audit**. Do not select it as the definitive research corpus yet.
2. Use HKG as a candidate discovery and exploratory resource, subject to licensing and record-level checks.
3. Do not use `rawis.rank` or `rank_no` as input features when predicting a label derived from those fields.
4. Do not treat `aqwal` as gold-standard ESA data until a sampled set is checked against identifiable primary-source passages.
5. Keep chain graph validation separate from the ESA statement audit.
6. Record the discrepancy between reported narrator counts (49,819 vs 49,844) for resolution.

## 8. Next audit tasks

### A. Download and inspect the SQLite database

Run read-only SQL queries to independently verify:
- table names and schema from `sqlite_master` and `PRAGMA table_info`;
- actual row counts;
- null and empty-string rates in `aqwal.qawl`;
- distribution of statement lengths and repeated texts;
- number of unique critics and narrators represented in aqwal;
- distribution of `rawis.rank` / `rank_no`;
- relation integrity and orphan records;
- samples stratified by critic, narrator, and apparent evaluation wording.

### B. Manually verify a sample

Select a small, documented sample of aqwal rows. For each, attempt to locate the exact Arabic wording in a named classical work and record:
- source work and author;
- edition and page / stable locator;
- exact wording and surrounding context;
- critic attribution;
- narrator identity;
- whether the HKG text is exact, normalised, truncated, or paraphrased;
- verification outcome and reviewer notes.

Do not silently repair discrepancies. Record them.

### C. Investigate target semantics

Determine where the `rawis.rank` categories originate, whether the rank is an aggregated field, and how it relates to the individual aqwal records. Construct a label mapping only after this investigation.

## 9. Open questions

- Which original rijāl sources were used to populate each aqwal record?
- Does the underlying 2017 application expose source citations not retained in this SQLite export?
- Are aqwal statements direct quotations or extracted snippets?
- How are conflicting critic statements represented?
- How are the rawi rank fields generated and ordered?
- Does the public dataset licence cover the transformed database only, or are there additional source-specific restrictions to observe?

**Conclusion:** HKG is a potentially valuable relational resource, but the absence of statement-level primary-source provenance is a serious constraint for a rigorous ESA study. It should remain a discovery / exploratory candidate until these issues are resolved.
