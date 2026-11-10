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

## Stage-two diagnostics

After running the first-stage audit, inspect source-ID citation patterns and
unexpected fwaed labels with:

    python .\dataset_discovery\Shamela4\diagnose_source_ids_and_fwaed.py .\data\2_interim\shamela4_narrator_audit

The script writes a separate stage2_diagnostics directory containing:
- source_id_review_queue.csv — opaque IDs with multiple title candidates or citation-shape warnings;
- title_candidate_review_queue.csv — title candidates associated with multiple IDs;
- fwaed_unexpected_labels.csv — labels outside the currently observed core category set, with examples;
- fwaed_entry_shapes.csv — serialized entry-shape counts and examples;
- STAGE2_REPORT.md and STAGE2_SUMMARY.json.

These are triage outputs, not automatic corrections. In particular, a title candidate
is not a verified bibliographic identity, an unexpected fwaed label is not necessarily
an error, and scholar-name detection is only a weak string heuristic. Resolve meanings
against upstream Shamela metadata and primary-source inspection before using these
fields in a target, feature set, or graph.

## Blinded human annotation pilot

Generate the 20-case blinded pilot from the frozen 60-case validation sample:

    python .\dataset_discovery\Shamela4\blinded_annotation_pilot.py

Run test suite:

    python -m unittest dataset_discovery/Shamela4/test_blinded_annotation_pilot.py

Outputs are saved to `data/2_interim/shamela4_narrator_audit/stage2_diagnostics/blinded_annotation_pilot_20`:
- `PILOT_SELECTION.csv` — selected 20 cases with stratum and selection rationale;
- `PILOT_REVIEWER_BLINDED.csv` — reviewer-facing copy with original text and blank annotation fields, strictly omitting all automated/stratum labels;
- `PILOT_INTERNAL_MAPPING.csv` — quarantined key mapping blinded pilot case IDs (`PILOT01`–`PILOT20`) to original source IDs and classifications;
- `ANNOTATION_CODEBOOK.md` — comprehensive field-by-field definitions, allowed values, and rules;
- `PILOT_PROTOCOL.md` — protocol detailing research questions, sampling design, anti-leakage firewall, and limitations;
- `pilot_manifest.json` — cryptographic hashes, input verification, seed, and purposive sampling declaration.

