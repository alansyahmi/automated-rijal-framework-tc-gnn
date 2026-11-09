# Shamela4 dataset discovery

Structural inspection and audit tooling for the Shamela4 narrator metadata dataset.

## Input

Default local source: data/1_raw/Shamela4_Full_DB/_meta/narrators.parquet

Dataset source: AuthenticIlm/Shamela4_Full_DB on Hugging Face. Check the upstream dataset card and licence before redistributing additional source material.

## Run

    python -m pip install pyarrow

    python .\dataset_discovery\Shamela4\audit_shamela_narrators.py .\data\1_raw\Shamela4_Full_DB\_meta\narrators.parquet

Optional output directory and larger samples:

    python .\dataset_discovery\Shamela4\audit_shamela_narrators.py .\data\1_raw\Shamela4_Full_DB\_meta\narrators.parquet --out .\data\2_interim\shamela4_narrator_audit --sample 100 --top 100

The script reads the Parquet input without modifying it. It writes occurrence-preserving CSV exports, source-ID/title collision reports, duplicate diagnostics, a JSON summary, and a Markdown profile report.

## Interpretation

- ghar group labels are raw grouping keys, not verified historical-speaker attribution.
- One quotation occurrence is not necessarily one independent evaluative statement.
- Source-ID/title matching is a string-level diagnostic and does not prove bibliographic identity.
- fwaed is retained separately from direct critical statements.
- Existing grades are not automatically clean target labels.

See SHAMELA4_AUDIT_FINDINGS.md for consolidated findings and unresolved questions.
