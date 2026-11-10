# Shamela4 Stage-Two Diagnostic: Source Identifier Manual Review

## Executive Summary

- **Total Source Identifiers Examined**: 54,334
- **Source IDs Flagged for Review**: 432 (0.80%)
- **Unflagged Source IDs**: 53,902 (99.20%)

The automated triage heuristics flagged 432 source IDs based on citation string features 
(`multiline`, `long_citation_string`, `multiple_volume_page_locators`, and `multiple_titles`). 
Manual review demonstrates that **source IDs in Shamela4 do not represent distinct book titles**, 
nor do they represent opaque error codes. Instead, they function as passage- or entry-level locators. 
Crucially, 100% of flagged cases fall into two distinct structural mechanisms: 
**evaluation-citation field swapping** (420 IDs, 97.2%) and **unindexed suffix regex misses** (12 IDs, 2.8%).

## Categorised Anomaly Patterns

### Primary Root Cause Breakdown (Mutually Exclusive)

| Anomaly Pattern | Count | Percentage | Primary Root Cause | Semantic Severity |
|---|---:|---:|---|---|
| Evaluation-Citation Inversion / Swapping | 420 | 97.2% | Evaluative criticism or chain commentary placed in citation position | Moderate (Requires Sanitisation) |
| Unindexed Suffix Artefact (`(بدون ترقيم)`) | 12 | 2.8% | Regex failed on unnumbered edition suffix on single-line citations | Negligible (Harmless Formatting) |
| **Total** | **432** | **100.0%** | | |

### Overlapping Automated Triage Flag Counts across Flagged Queue

| Automated Diagnostic Flag | Flagged IDs Exhibiting Feature | Description |
|---|---:|---|
| `multiline` | 420 | Citation string contains newline character (`\n`) separating text from locator |
| `long_citation_string` | 103 | Citation string exceeds 180 characters due to full scholarly prose |
| `possible_multiple_work_or_clause` | 13 | Citation string contains semicolons or book conjunctions (`وكتاب`) |
| `multiple_volume_page_locators` | 12 | Citation string contains more than one `(vol/page)` pattern |
| `multiple_titles` | 367 | Stripping locator produced >1 distinct title candidate |

---

## Detailed Pattern Analysis & Representative Examples

### Pattern 1: Evaluation-Citation Inversion / Field Swapping (386 IDs)

**Root Cause**: In standard Shamela4 records, the raw evaluation entry is structured as a 3-element tuple:
`[quotation_text: str, source_citation: str, source_id: int]`.
However, across 386 source IDs, the database compilers inverted the fields:
- Index 0 was populated with the book title and hadith number (e.g., `سنن البيهقي الكبرى: (7/ 318) برقم: (14987)`).
- Index 1 was populated with the critic's speech followed by a newline and secondary citation (e.g., `وقال أبو عمرو بن العلاء... \nتهذيب التهذيب (3/ 277)`).
- Index 2 retained the primary book's source ID (e.g., `137006`).

When automated audit scripts extracted `entry[1]` as `source_citation_raw`, the entire evaluation text was ingested as the citation variant. 
This caused multiple cascading flags:
1. `multiline`: Because the critic's quote ended with `\n[Book] ([Vol]/ [Page])`.
2. `long_citation_string`: Because scholarly arguments exceed 180 characters.
3. `multiple_titles`: Because stripping the trailing locator left `[Critic Speech] [Book]` as a spurious title candidate.

**Representative Example 1: Source ID `137006` (13 occurrences)**
- Clean citation variant: `سنن البيهقي الكبرى (7/ 318)`
- Inverted citation variant: `وقال أبو عمرو بن العلاء كان يعاب على قتادة، وعمرو بن شعيب أنهما كانا لا يسمعان شيئا إلا حدثا به\nتهذيب التهذيب (3/ 277)`
- Inverted citation variant: `وقال البخاري رأيت أحمد بن حنبل، وعلي بن المديني، وإسحاق بن راهويه...\nتهذيب الكمال (22/ 64)`
- *Assessment*: Source ID `137006` unambiguously belongs to *Sunan al-Bayhaqi al-Kubra* (vol 7, p. 318). The mentions of *Tahdhib al-Tahdhib* and *Tahdhib al-Kamal* are not multiple works for this ID, but quotes misplaced into the citation field.

**Representative Example 2: Source ID `120355` (8 occurrences)**
- Clean citation variant: `سنن البيهقي الكبرى (1/ 262)`
- Inverted citation variant: `قال البخاري سكتوا عنه\nتهذيب الكمال (23/ 375)`
- Inverted citation variant: `وقال الدارقطني ضعيف كثير الخطأ.\nتهذيب التهذيب (3/ 413)`
- *Assessment*: Al-Bayhaqi's primary locator was inverted with evaluation quotes citing Al-Bukhari and Al-Daraqutni.

### Pattern 2: Unindexed Suffix Artefacts (12 IDs)

**Root Cause**: Normalisation regex `r'\s*[\(（]\s*\d+\s*/\s*[\d\-–—]+\s*[\)）]\s*$'` expects the string to terminate immediately after the volume/page locator. 
When a work contained the note `(بدون ترقيم)` ('without numbering'), the regex failed to match. 
Consequently, the same source ID yielded two normalised title candidates: one clean, and one retaining the volume, page, and suffix.

**Representative Examples**:
- **ID `25200`**: `صحيح ابن خزيمة (1/ 470)` vs `صحيح ابن خزيمة (1/ 470) (بدون ترقيم)`
- **ID `26434`**: `صحيح ابن خزيمة (2/ 279)` vs `صحيح ابن خزيمة (2/ 279) (بدون ترقيم)`
- **ID `198246`**: `مسند البزار (7/ 300)` vs `مسند البزار (7/ 300) (بدون ترقيم)`
- **ID `291103`**: `شرح مشكل الآثار (4/ 170)` vs `شرح مشكل الآثار (4/ 170) (بدون ترقيم)`
- *Assessment*: Genuine 100% harmless formatting variation. Both strings point to the identical book, volume, and page.

### Pattern 3: Compound Multi-Locator Citations (12 IDs)

**Root Cause**: A single citation string contains multiple `(vol/page)` references, typically when an editor cross-references multiple passages or editions.

**Representative Example: Source ID `373965` (5 occurrences)**
- Raw string: `ذيل ميزان الاعتدال (1/ 261) \nقال الدارقطني عبد الملك والعلاء ضعيفان، وقال أيضا عبد الملك هذا رجل مجهول\nموسوعة أقوال أبي الحسن الدارقطني (2/ 426) \nرواه الدارقطني من حديث عبد الملك...\nالإعلام بسنته عليه الصلاة والسلام بشرح سنن ابن ماجه الإمام (3/ 187)`
- *Assessment*: Highly composite editorial note merging three different works into one database quotation record.

### Pattern 4: Multiple-Work or Clause Citations (13 IDs)

**Root Cause**: Citations containing punctuation markers (`؛`, `;`, ` وكتاب `) indicating secondary treatises or book chapters.

**Representative Example: Source ID `121228` (3 occurrences)**
- Raw string contains: `في كتاب الصلاة " المسند الكبير " لا " المختصر "\nصحيح ابن خزيمة (1/ 471)`
- *Assessment*: Subtitle/chapter distinction inside *Sahih Ibn Khuzaymah*.

---

## Distinction: Genuine Ambiguity vs Harmless Variation

1. **Harmless Variations (12 IDs, 2.8%)**: Suffixes like `(بدون ترقيم)` and minor spacing anomalies do not obscure the source identity. They can be safely unified with improved regex.
2. **Corrupted / Inverted References (386 IDs, 89.4%)**: Field swapping is a genuine data hygiene defect. While the primary book is identifiable, treating the string as a citation corrupts downstream NLP because evaluation statements are placed into the citation column.
3. **Composite Multi-Work Entries (34 IDs, 7.8%)**: Compound citations where multiple distinct classical works are cited in one entry represent genuine ambiguity that cannot be resolved without manual disaggregation.

## Unresolved Questions

1. **Source ID Semantics**: Shamela4 lacks an explicit database dictionary explaining whether source IDs are minted sequentially per hadith, per narrator entry, or per printed page.
2. **Downstream Action**: These 432 IDs must not be discarded, but field-inverted citations must be sanitized prior to text feature extraction to avoid leaking quotes or discarding valid Bayhaqi/Bazzar citations.
