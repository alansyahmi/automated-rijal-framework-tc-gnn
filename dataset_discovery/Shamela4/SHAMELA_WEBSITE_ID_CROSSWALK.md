# Shamela narrator website ID cross-reference

**Status:** Initial sample validation completed  
**Date:** 2026-11-11  
**Related source:** `data/1_raw/Shamela4_Full_DB/_meta/narrators.parquet`

## Purpose

This note records the cross-reference between narrator IDs in the Shamela4 `narrators.parquet` dump and the public Shamela narrator pages at:

`https://shamela.ws/narrator/{id}`

The working assumption is that the public narrator pages expose records from the same Shamela narrator corpus represented in the full dump. The audit tests whether the Parquet `id` can be used directly in the website URL and whether the displayed narrator name agrees with the Parquet record.

## Initial sample

The sample contains 40 records selected from the sorted Parquet narrator table:

- Beginning: first 10 records.
- Lower-middle: 10 records centred around the 37.5% position.
- Upper-middle: 10 records centred around the 62.5% position.
- End: last 10 records.

The sample is range-stratified and deterministic given the source table. It is not a simple random sample and must not be used to estimate a corpus-wide mismatch rate.

| Segment | Parquet row index | Narrator ID | Parquet short name |
|---|---:|---:|---|
| Beginning | 0 | 2 | أبو ماعز الأسلمي، عبد الله بن سفيان |
| Beginning | 1 | 3 | آدم بن أبي إياس |
| Beginning | 2 | 4 | آدم بن سليمان |
| Beginning | 3 | 5 | آدم بن علي |
| Beginning | 4 | 6 | أم قيس بنت محصن الأسدية |
| Beginning | 5 | 7 | أم حرام |
| Beginning | 6 | 8 | أبان بن أبي عياش |
| Beginning | 7 | 9 | أبان بن إسحاق |
| Beginning | 8 | 10 | أبان بن تغلب بن رياح |
| Beginning | 9 | 11 | أبان بن صالح بن عمير بن عبيد |
| Lower-middle | 7115 | 7482 | ضرار بن الأزور |
| Lower-middle | 7116 | 7483 | فضيل بن زيد |
| Lower-middle | 7117 | 7484 | أبو زياد |
| Lower-middle | 7118 | 7485 | عمر بن كيسان |
| Lower-middle | 7119 | 7486 | وهب بن أبي مغيث |
| Lower-middle | 7120 | 7487 | عبد الرحمن بن الضحاك |
| Lower-middle | 7121 | 7488 | عبد الله بن حلام |
| Lower-middle | 7122 | 7490 | سليمان بن الربيع |
| Lower-middle | 7123 | 7491 | عبد الله بن جنادة |
| Lower-middle | 7124 | 7492 | إبراهيم بن ميمون |
| Upper-middle | 11863 | 13939 | شعيث بن محرز بن شعيث بن زيد بن أبي الزعراء |
| Upper-middle | 11864 | 13940 | الحر بن سليمان بن حيدرة |
| Upper-middle | 11865 | 13941 | الحسن بن سهل |
| Upper-middle | 11866 | 13942 | الحسن بن الحكم بن طهمان |
| Upper-middle | 11867 | 13943 | الحسن بن ناصح |
| Upper-middle | 11868 | 13944 | سعيد بن محمد بن محمد بن عطاف الهمداني |
| Upper-middle | 11869 | 13945 | أبو حفص عمر بن أحمد بن عثمان يزداد |
| Upper-middle | 11870 | 13946 | طاهر بن محمد بن طاهر بن علي |
| Upper-middle | 11871 | 13947 | محمد بن الحسين بن أحمد بن الهيثم |
| Upper-middle | 11872 | 13949 | القاسم بن أبي المنذر |
| End | 18979 | 22654 | محمد بن يوسف المقرئ |
| End | 18980 | 22655 | علي بن مسلم بن خباب |
| End | 18981 | 22656 | محمد بن أحمد بن يحيى بن شيرين |
| End | 18982 | 22657 | عبد الرحمن بن عمير |
| End | 18983 | 22663 | طلحة بن عثمان |
| End | 18984 | 22664 | محمد بن أحمد بن أنس |
| End | 18985 | 22665 | علي بن أحمد بن عبد العزيز |
| End | 18986 | 22666 | أبو شرقي |
| End | 18987 | 22667 | عمرو بن أبي عمرو |
| End | 18988 | 22668 | عمر بن شوذب |

## Result

The 40 sampled website pages were checked against the corresponding Parquet records. The reported outcome was **40/40 matching narrator names**.

One request for ID `7490` initially failed to load; a retry succeeded and the page name matched `سليمان بن الربيع`.

This supports the direct ID cross-reference:

`Parquet narrators.id = Shamela website /narrator/{id}`

It is also consistent with the working assumption that the public website and the full dump expose the same narrator corpus.

## Interpretation and limits

1. **ID correspondence:** The sample provides corroborating evidence that Parquet narrator IDs can be used as Shamela narrator-page IDs across the beginning, middle and end of the observed ID range.
2. **Not an exhaustive audit:** Forty matches do not establish that every one of the 18,989 records has a live page or that no exceptions exist.
3. **Not a version audit:** The comparison does not establish that the live website and the downloaded dump are from the exact same database snapshot or release.
4. **Not field-level validation:** Matching names do not independently validate every biography, classification, or criticism field.
5. **No historical attribution claim:** This cross-reference says nothing about whether a `garh` group label identifies the historical speaker of a judgement.

## Reproducible follow-up

For any sampled or individually inspected narrator:

1. Read the Parquet row by `id`.
2. Open `https://shamela.ws/narrator/{id}`.
3. Compare the displayed name with the Parquet `short_name` and, where needed, `long_name`.
4. Record the URL, observed title/name, outcome, date, and any normalization or spelling difference.
5. Preserve missing pages, transient fetch failures, and genuine mismatches as separate outcomes.

The next useful extension is an automated or semi-automated crosswalk audit over all IDs, with rate limiting, retries, and a durable result manifest. It should not be represented as complete until every record has an explicit outcome.
