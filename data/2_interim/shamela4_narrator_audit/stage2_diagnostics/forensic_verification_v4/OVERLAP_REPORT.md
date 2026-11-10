# Shamela4 tuple validation sample: Overlap and dependency report (v4)

## Executive summary

- **Sample size**: 60 original tuples, exactly 10 per stratum across 6 strata.
- **Source ID uniqueness**: 60 distinct source IDs across 60 sampled cases (100% unique source IDs).
- **Narrator representation**: 53 distinct narrator records (7 narrators recur; 46 appear once).
- **Grouping representation**: 19 distinct `garh` group labels (top 5 groups cover 61.7% of the sample).
- **Formatting stratum scope**: 10 of 10 cases in `suffix_format_validation_only` are `بدون ترقيم` variants, sampled from 12 eligible source IDs.
- **Evaluation boundary**: This sample is designed exclusively for **tuple interpretation** (segmenting slots and locating boundaries), **not** for historical speaker attribution, canonical edition identification, or independent statistical evaluation.

## Recurring narrator records (Narrator ID overlaps)

While all 60 tuples have distinct `source_id` values, 7 narrator records appear twice in the sample.
Because sampling was conditioned on `source_id` rather than narrator ID, prominent transmitters and disputed narrators with multiple flagged source IDs co-occur in the sample.

| Narrator ID | Narrator Name | Occurrences | Case IDs | Sampling Strata | Overlap Type |
| :--- | :--- | :---: | :--- | :--- | :--- |
| `1309` | حجاج بن أرطأة | 2 | TV037, TV041 | suspected_or_unresolved, normal_prose_then_citation | Inter-stratum cross-occurrence |
| `1580` | الحكم بن عتيبة | 2 | TV004, TV029 | suffix_format_validation_only, mixed_source_ID | Inter-stratum cross-occurrence |
| `3234` | عبد الرحمن بن أبي ليلى | 2 | TV009, TV016 | suffix_format_validation_only, compound_or_multiple_locator | Inter-stratum cross-occurrence |
| `4541` | علي بن زيد بن عبد الله بن أبي مليكة | 2 | TV039, TV055 | suspected_or_unresolved, citation_only_then_locator_bearing_prose | Inter-stratum cross-occurrence |
| `5177` | قبيصة بن ذؤيب بن حلحلة | 2 | TV047, TV056 | normal_prose_then_citation, citation_only_then_locator_bearing_prose | Inter-stratum cross-occurrence |
| `5398` | مبشر بن عبيد | 2 | TV040, TV046 | suspected_or_unresolved, normal_prose_then_citation | Inter-stratum cross-occurrence |
| `7345` | الحسن بن عمارة بن المضرب | 2 | TV033, TV034 | suspected_or_unresolved, suspected_or_unresolved | Intra-stratum overlap |

> [!NOTE]
> Narrator `7345` (*al-Hasan b. 'Umarah b. al-Mudarrib*) has two distinct occurrences (`TV033` and `TV034`) within the **same** stratum (`suspected_or_unresolved`). Both cases originate from different `source_id` values (`195879` and `140933`) and evaluate different textual cues.

## Group label frequency distribution

The 60 sampled tuples span 19 distinct group labels from the raw `criticism_text.garh` entries.
The distribution reflects compiler concentration in the underlying database:

| Rank | Group Label | Absolute Count | Proportion (%) | Cumulative (%) |
| :---: | :--- | :---: | :---: | :---: |
| 1 | الدارقطني | 10 | 16.7% | 16.7% |
| 2 | الطحاوي | 9 | 15.0% | 31.7% |
| 3 | البيهقي | 7 | 11.7% | 43.3% |
| 4 | البزار | 6 | 10.0% | 53.3% |
| 5 | الترمذي | 5 | 8.3% | 61.7% |
| 6 | أحمد بن حنبل | 3 | 5.0% | 66.7% |
| 7 | النسائي | 3 | 5.0% | 71.7% |
| 8 | يحيى بن معين | 3 | 5.0% | 76.7% |
| 9 | ابن حجر | 2 | 3.3% | 80.0% |
| 10 | البخاري | 2 | 3.3% | 83.3% |
| 11 | شعبة بن الحجاج | 2 | 3.3% | 86.7% |
| 12 | ابن خزيمة | 1 | 1.7% | 88.3% |
| 13 | محمد بن يحيى الذهلي | 1 | 1.7% | 90.0% |
| 14 | العقيلي | 1 | 1.7% | 91.7% |
| 15 | الحاكم | 1 | 1.7% | 93.3% |
| 16 | سفيان الثوري | 1 | 1.7% | 95.0% |
| 17 | علي ابن المديني | 1 | 1.7% | 96.7% |
| 18 | ابن عدي | 1 | 1.7% | 98.3% |
| 19 | الفلاس | 1 | 1.7% | 100.0% |

The top 5 group labels (`الدارقطني`, `الطحاوي`, `البيهقي`, `البزار`, `الترمذي`) account for **37 of 60 cases (61.7%)**.
This reflects the dominance of these authorities in the flagged source-ID population rather than a balanced historical corpus.

## Per-stratum composition and overlaps

| Stratum | Case Range | Target / Eligible | Unique Source IDs | Unique Narrators | Recurring Narrators Present | Group Labels Count | Predominant Group |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `suffix_format_validation_only` | TV001–TV010 | 10 / 12 | 10 | 10 | 1580 (الحكم بن عتيبة), 3234 (عبد الرحمن بن أبي ليلى) | 4 | الطحاوي (7) |
| `compound_or_multiple_locator` | TV011–TV020 | 10 / 420 | 10 | 10 | 3234 (عبد الرحمن بن أبي ليلى) | 7 | الدارقطني (3) |
| `mixed_source_ID` | TV021–TV030 | 10 / 239 | 10 | 10 | 1580 (الحكم بن عتيبة) | 8 | شعبة بن الحجاج (2) |
| `suspected_or_unresolved` | TV031–TV040 | 10 / 228 | 10 | 9 | 1309 (حجاج بن أرطأة), 4541 (علي بن زيد بن عبد الله بن أبي مليكة), 5398 (مبشر بن عبيد), 7345 (الحسن بن عمارة بن المضرب) | 6 | الدارقطني (4) |
| `normal_prose_then_citation` | TV041–TV050 | 10 / 157 | 10 | 10 | 1309 (حجاج بن أرطأة), 5177 (قبيصة بن ذؤيب بن حلحلة), 5398 (مبشر بن عبيد) | 9 | البيهقي (2) |
| `citation_only_then_locator_bearing_prose` | TV051–TV060 | 10 / 245 | 10 | 10 | 4541 (علي بن زيد بن عبد الله بن أبي مليكة), 5177 (قبيصة بن ذؤيب بن حلحلة) | 6 | البيهقي (3) |

### Group distributions within each stratum

#### Stratum `suffix_format_validation_only` (TV001–TV010)
- Group labels (4): `الطحاوي`: 7, `البزار`: 1, `ابن خزيمة`: 1, `محمد بن يحيى الذهلي`: 1

#### Stratum `compound_or_multiple_locator` (TV011–TV020)
- Group labels (7): `الدارقطني`: 3, `ابن حجر`: 2, `الترمذي`: 1, `أحمد بن حنبل`: 1, `النسائي`: 1, `البزار`: 1, `البخاري`: 1

#### Stratum `mixed_source_ID` (TV021–TV030)
- Group labels (8): `شعبة بن الحجاج`: 2, `الطحاوي`: 2, `البزار`: 1, `يحيى بن معين`: 1, `أحمد بن حنبل`: 1, `البيهقي`: 1, `الترمذي`: 1, `النسائي`: 1

#### Stratum `suspected_or_unresolved` (TV031–TV040)
- Group labels (6): `الدارقطني`: 4, `البزار`: 2, `البيهقي`: 1, `العقيلي`: 1, `الترمذي`: 1, `الحاكم`: 1

#### Stratum `normal_prose_then_citation` (TV041–TV050)
- Group labels (9): `البيهقي`: 2, `البخاري`: 1, `سفيان الثوري`: 1, `علي ابن المديني`: 1, `ابن عدي`: 1, `يحيى بن معين`: 1, `الدارقطني`: 1, `النسائي`: 1, `البزار`: 1

#### Stratum `citation_only_then_locator_bearing_prose` (TV051–TV060)
- Group labels (6): `البيهقي`: 3, `الترمذي`: 2, `الدارقطني`: 2, `أحمد بن حنبل`: 1, `يحيى بن معين`: 1, `الفلاس`: 1

## Suffix-format stratum characterization

All 10 cases in stratum `suffix_format_validation_only` (`TV001` through `TV010`) were drawn from 12 eligible source IDs.
**100% of selected cases (10 / 10)** feature the literal unnumbered suffix string `(بدون ترقيم)` or `بدون ترقيم`.

Because zero non-suffix formatting cases were selected from this pool, this stratum validates **suffix-format variation only**.
It must not be construed as an evaluation of arbitrary whitespace formatting, general punctuation anomalies, or general layout defects.

## Critical methodological limits & independence caveat

> [!IMPORTANT]
> ### 1. Observed strings do NOT establish work identity
> Literal text in `original_field_1` and `original_field_2` (e.g., `شرح مشكل الآثار: (12/ 362)`) provides observed strings from the database. These strings do **not** verify:
> - Canonical work identity or edition provenance.
> - Whether the volume/page pagination matches a specific published print edition.
> - Whether citations under identical text strings refer to identical manuscript traditions.

> [!WARNING]
> ### 2. Sampled units are NOT statistically independent cases
> The 60 review cases must **not** be treated as independent, identically distributed ($i.i.d.$) observations:
> - Seven narrator IDs appear in multiple cases.
> - Five compilers account for over 61% of group labels.
> - Tuples from the same compiler frequently inherit identical typographic conventions, punctuation habits, and delimiter choices.
> - Any statistical test that assumes observational independence will produce deflated standard errors and spurious precision.

> [!CAUTION]
> ### 3. Interpretation vs attribution vs reliability
> This package evaluates **tuple interpretation** only:
> - **Field roles & boundaries**: Can human readers distinguish quotation/evaluation text from bibliographic locators, and mark their spans?
> - **Speaker attribution**: The `group_label` is an internal database grouping key; it does **not** prove who historically uttered the statement.
> - **Historical accuracy**: Whether the narrator was actually criticized or praised is entirely outside the scope of this annotation task.
> - **Narrator reliability**: Annotators are **not** assessing narrator trustworthiness (`ta'dil`/`jarh`).

## Upstream integer semantics finding retained

As established in forensic verification v1–v3, no reviewed upstream documentation (Shamela official portal, AuthenticIlm dataset card, ragaeeb/shamela reverse engineering repository) establishes the entity semantics of the integer stored in tuple element 3.
It remains documented strictly as an observed `source_id` integer.
