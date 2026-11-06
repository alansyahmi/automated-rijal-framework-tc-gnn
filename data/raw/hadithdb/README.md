# HadithDB Raw Source — Dataset Description

**Internal dataset ID:** `hadithdb`  
**Upstream project:** [hatemben/hadithdb](https://github.com/hatemben/hadithdb)  
**Source file documented here:** `narrators_db.json`  
**Local snapshot inspected:** 2026-11-07  
**Research status:** Under audit; candidate source for quotation discovery and an ESA annotation pilot  
**Redistribution status:** Not cleared

> This file documents the local raw source. The upstream JSON corpus is intentionally not committed to this repository. Public availability on GitHub is not evidence of an open licence or permission to redistribute the source or derivative quotation data.

## 1. Description

HadithDB is a structured Arabic hadith-related database. The narrator file contains biographical records, narrator metadata, and nested quotation material grouped under the Arabic field `الجرح والتعديل`. The quotations frequently include a trailing bracketed reference to a work and volume/page locator.

For this project, the file is being investigated as a source for discovering attributed evaluative statements about narrators. It is not yet a validated dataset of critic statements, and it is not a gold-standard ESA corpus.

## 2. Source provenance and local snapshot

- Upstream repository: [https://github.com/hatemben/hadithdb](https://github.com/hatemben/hadithdb)
- File: `narrators_db.json`
- Local SHA-256 observed during extraction: `67c183de90f779496f741a868120224c71fd32ff94525fb6a119ea8750b9c42a`
- Local snapshot and extraction run: 2026-11-07
- Upstream repository had no declared licence or accompanying data dictionary when inspected. Confirm rights with the source maintainer and check underlying editions before redistribution or publication of substantial derived content.

The checksum identifies the exact local input used for the reported extraction. Recompute it whenever the source file is replaced; do not silently overwrite or mutate the raw snapshot.

## 3. Record structure

The inspected JSON root is an object keyed by narrator-record ID. A record contains:

- `id`: record identifier;
- `name`: display name;
- `data`: nested biographical fields.

The `data` object includes identity and biographical fields such as name, kunya, lineage, residence, birth/death dates, and travel/death locations. It also includes fields such as:

- `طبقة رواة التقريب` — a narrator-generation/tabaqa field associated with *Taqrīb*;
- `الرتبة عند ابن حجر` — rank attributed to Ibn Hajar;
- `الرتبة عند الذهبي` — rank attributed to al-Dhahabi;
- `الجرح والتعديل` — nested groups containing quotation strings.

The nested `الجرح والتعديل` object maps group labels to arrays of quotation strings. The quotation strings may contain direct statements, transmitted reports, summaries, biographical/historical passages, or compiler commentary.

## 4. Local extraction profile

The following figures come from the local extraction and profiling run on 2026-11-07. They describe the extracted representation, not independently verified historical statements.

| Measure | Observed count |
|---|---:|
| Narrator records in source JSON | 1,524 |
| Records represented in extracted quotation table | 1,521 |
| Extracted quotation occurrences | 40,524 |
| Unique exact quotation strings | 35,216 |
| Distinct exact strings occurring more than once | 3,639 |
| Excess occurrences beyond the first copy of each exact string | 5,308 |
| Distinct source-group labels | 1,307 |
| Distinct parsed cited-work-title strings in the current profiler | 49 |
| Trailing citations parsed into work/locator fields | 40,385 |
| Bracketed citations found but not parsed into expected format | 137 |
| No trailing bracketed citation found | 2 |

Citation parsing success is syntactic only. It does not verify that a work exists under that exact title, that the volume/page is correct, that the cited edition is known, or that the quotation matches the cited passage.

The profiler's 49 work-title count refers to titles successfully parsed by its current pattern. It should not be conflated with counts of distinct full citation strings or bibliographic variants produced by other parsing methods.

## 5. Important structural and attribution cautions

### 5.1 Group labels are not verified speaker identities

Preserve the original nested key as `source_group_label`. Do not automatically convert it into a critic/speaker identity.

Inspection shows heterogeneous grouping semantics: some keys correspond to critics or authorities associated with statements, while others correspond to people mentioned in a passage, compilers, or unclear categories. A quotation may also name a speaker different from the group key, report an intermediary's transmission, or contain several authorities.

For example, narrator record `1312` is the biography of Aḥmad ibn Ḥanbal. One identical passage from *Tahdhīb al-Kamāl* (1/437) occurs 19 times under 19 different group labels. The passage names multiple scholars; in this instance the labels appear to index people associated with the passage rather than 19 independent evaluations. This is a confirmed example, not a claim that every group follows the same pattern.

### 5.2 A quotation occurrence is not necessarily an independent judgement

Exact repetitions can occur within a single biography and across different group labels. Do not count every extracted row as an independent critic judgement or independent evidence item. Preserve occurrence-level provenance and create duplicate clusters for later analysis.

### 5.3 The biography subject is not necessarily the statement subject

The narrator record ID identifies the biographical record in which a quotation is stored. It does not prove that every person discussed or evaluated in every quotation is that record's subject. A future annotation schema should distinguish the biography subject from the subject of the quoted statement.

### 5.4 Reference-grade leakage

The source includes Ibn Hajar and al-Dhahabi rank fields. If a prediction target is derived from either authority, the corresponding grade fields and direct textual reproductions must not be used as model inputs. Target source and leakage exclusions must be declared before modelling.

### 5.5 Citation and source hierarchy

The trailing citation usually provides a work-title string and volume/page locator, but the source does not provide a fully normalised bibliography or edition-level metadata in the extracted quotation row. A later compilation may quote an earlier critic. Preserve the cited work separately from the original speaker and any earlier source only when independently established.

## 6. Current extraction artifacts

Generated locally; do not place these outputs in the raw-source directory.

- Extraction script: `dataset_discovery/hadithdb/extract_hadithdb_quotes.py`
- Profiling script: `dataset_discovery/hadithdb/profile_hadithdb_quotes.py`
- Quote-occurrence CSV: `data/interim/hadithdb_quote_occurrences.csv`
- Profile outputs: `data/interim/hadithdb_profile/`

The extraction table retains the raw quote, source record ID, original group label, JSON pointer, source-file hash, record hash, parsed citation fields, and explicit unreviewed/unverified statuses. Raw source values are not edited in place.

Example commands from the repository root:

```powershell
python .\dataset_discovery\hadithdb\extract_hadithdb_quotes.py `
  .\data\raw\hadithdb\narrators_db.json `
  --out .\data\interim\hadithdb_quote_occurrences.csv

python .\dataset_discovery\hadithdb\profile_hadithdb_quotes.py `
  .\data\interim\hadithdb_quote_occurrences.csv `
  --out-dir .\data\interim\hadithdb_profile
```

## 7. Recommended handling and next validation work

1. Keep the downloaded source file immutable and record its checksum.
2. Keep the raw JSON local until redistribution rights are clarified.
3. Retain `source_group_label` verbatim; do not infer speaker identity from it.
4. Separate biography subject, statement subject, quoted speaker, intermediary/transmitter, cited work, and cited locator during annotation.
5. Inspect duplicate structures before deduplicating. Repetition may reflect source indexing and should not be silently deleted.
6. Manually verify a stratified sample against the cited works, including edition and locator where possible.
7. Annotate statement type before ESA stance; not every quotation is evaluative.
8. Document target-source exclusions and leakage checks before using any grade field in model development.

**Current decision:** retain HadithDB as an under-audit candidate for quotation discovery and a small manual ESA annotation pilot. Do not yet treat it as a verified speaker-attributed corpus, gold-standard label source, or cleared redistributable dataset.
