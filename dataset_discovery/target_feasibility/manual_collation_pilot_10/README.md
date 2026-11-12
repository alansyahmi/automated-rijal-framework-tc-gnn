# 10-Record Manual Collation Pilot

This package prepares ten distinct cases from the frozen 60-record sample for your source review. It contains eleven locator rows because `PROV-04` has two same-name candidate entries in the source text. The extra row preserves that ambiguity; it does not choose an identity.

## What to open

1. Start with `MANUAL_COLLATION_PILOT_10.csv`. It contains the original record context, candidate Taqrīb page/entry locators, exact text transcribed from the local Shamela Taqrīb corpus, and blank human-review fields. Automated flags and review categories are omitted from this reviewer copy.
2. Verify the candidate locators in the cited print edition. The local book metadata says its pagination matches the print; the CSV uses the corpus page number.
3. Compare the full entry with the original dataset field. Preserve qualifications and wording. Record your source findings and judgments in the blank fields only after inspecting the evidence.
4. Leave `corroboration_status` blank unless you actually examine the relevant source-dependence evidence. Its allowed values describe findings, not assumptions.
5. Keep target suitability and historical-input eligibility as separate decisions. If evidence is unclear, record unresolved and explain why.

## Cases requiring special care

- `PROV-04`: two Taqrīb entries with the same name are included. Do not select one from name similarity alone.
- `PROV-24`: the dataset name is a kunya only. The supplied Taqrīb entry is a locator candidate based on the kunya and phrase, not a verified identity match.
- All other supplied entries are retrieval candidates. A text search is not proof of narrator identity, authorship, attribution, or historical accuracy.

The local source is the Shamela digital text for *Taqrīb al-Tahdhīb*, Book ID 3076, edited by Muhammad Awwamah. This packet does not independently inspect a physical edition or manuscript witness. No human findings have been pre-filled.

`MANUAL_COLLATION_PILOT_10_KEY.csv` contains the internal case-to-review-focus mapping and automated flag snapshot. Keep it closed during an initial unaided pass if you want to reduce flag-driven confirmation bias. It is an audit aid, not a source of scholarly conclusions. The frozen 60-record worksheet is not modified by this pilot.
