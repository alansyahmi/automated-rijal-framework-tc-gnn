# Dataset Discovery and Source Audit

## Purpose

This directory records candidate datasets and the underlying primary sources. Discovery is not selection: no candidate is approved for modelling until it passes a record-level audit.

## Audit each candidate in this order

1. **Access and licence:** Can the data be accessed lawfully? What can be downloaded, transformed, stored, and redistributed?
2. **Schema:** What are the actual tables, fields, keys, and relations? Do not rely on promotional descriptions alone.
3. **Provenance:** Can each statement be traced to a named work, edition, and locator?
4. **Attribution:** Is the critic identified? Is the attribution explicit in the source or inferred by a pipeline?
5. **Narrator linking:** How is a statement linked to a narrator? Are aliases, homonyms, kunyas, nisbas, and name variants handled?
6. **Text integrity:** Is the original Arabic preserved? Are quotation boundaries and context retained? What normalisation was applied?
7. **Coverage and missingness:** What is included, omitted, unresolved, duplicated, or uncertain?
8. **Independence and leakage:** Does the candidate contain the same reference grades that will be predicted? Does it reproduce or derive from the target source?
9. **Reproducibility:** Can the source version and transformation pipeline be reconstructed?

## Sampling protocol

For each candidate, inspect a stratified sample that includes:

- clearly attributed positive and negative evaluations;
- ambiguous or compound expressions;
- multiple critics evaluating the same narrator;
- multiple narrators with similar names;
- missing or uncertain narrator links;
- records with and without source locators;
- cases where the candidate's grade appears to match the proposed target.

Record the sampling method, sample size, date, and all exceptions. Manually verify selected records against the underlying source text.

## Important separation

Maintain separate entities for source works, passages, critics, narrator identities, evaluative statements, reference grades, and transmission relations. A dataset's precomputed grade must not be silently treated as the same thing as a critic's statement.

## Current candidates

See [CANDIDATE_DATASETS.csv](CANDIDATE_DATASETS.csv) and record audited source details in [SOURCE_REGISTER_TEMPLATE.csv](SOURCE_REGISTER_TEMPLATE.csv).
