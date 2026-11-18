# Six-case consistency repeat: reviewer copy

This is a single-researcher repeat packet. It contains no prior annotation values, rank adjudications, source rationales, evidence-role labels, or machine suggestions. It is not an independent or fully blinded review: the researcher has seen these records before, and dataset names/IDs remain visible where needed for the source task.

## Use the stages in order

1. **Pass A, identity only.** Open only `01_PASS_A_IDENTITY_ONLY/PASS_A_IDENTITY_INPUT.csv` and `01_PASS_A_IDENTITY_ONLY/PASS_A_IDENTITY_DECISIONS_BLANK.csv`. Do not open the `02_PASS_B_OPEN_AFTER_PASS_A_FREEZE` folder yet. The original grade field and full Taqrīb entries are intentionally withheld. The masked Taqrīb view is a derived aid, not a source transcription; bracketed text marks the removed evaluation/criticism wording. Record candidate identity from grade-independent evidence and save the completed decision CSV.
2. **Freeze Pass A.** Save a dated copy and record its SHA-256 before opening any `PASS_B_*` file.
3. **Pass B.** Then open `02_PASS_B_OPEN_AFTER_PASS_A_FREEZE/PASS_B_CASES.csv`, `PASS_B_CANDIDATES.csv`, and `PASS_B_SOURCE_REFERENCES.csv`. These contain raw source values and full candidate entry text, but no prior decisions. Complete the blank candidate, statement, attribution, and source templates in that same folder. Use one statement row per claim; duplicate the starter rows as needed. Add attribution and evidence rows only after assigning new statement IDs.
4. **Freeze Pass B.** Save the completed files and hashes. Do not open the internal reconciliation key or earlier Pass 1 packages until both passes are frozen.
5. **Compare afterward.** Compare Pass A and Pass B against the original records dimension by dimension. Preserve all three records and explain each change; do not overwrite Pass 1.

The frozen Protocol v1.0 calls for a delay of roughly two to four weeks after its 2026-11-14 freeze. This packet is prepared ahead of that window. If retaining the delayed consistency design, begin no earlier than 2026-11-28; the approximate window ends 2026-12-12. Preparing the files does not count as starting the reassessment.

## What this packet preserves and omits

- Six selected cases are presented in a shuffled repeat order under `RPT-*` aliases. Candidate rows are relabeled `CAND-*`; the PROV mapping is in the separate `INTERNAL_AFTER_REPEAT_ONLY` folder.
- Source record IDs, narrator IDs/names, original grade strings, full Taqrīb text, and source locators are retained where appropriate.
- Previous identity/correspondence decisions, statement segmentation, rank decisions, attribution fields, rationales, reviewer notes, and classifier suggestions are not copied into reviewer templates.
- The listed external source references were inherited from the earlier source packets. They are citations to re-open, not a fresh or exhaustive source search. Verify the source and locator again when using it.
- Exact-match candidate passages were masked in the Pass A identity view using the previous source-span mapping. The mask is a temporary grade-blind aid only; use the unaltered full text in Pass B.

## Limitation

Because the same researcher previously handled these records, familiarity and memory can influence decisions even with aliases and a shuffled order. Report this as a within-researcher consistency reassessment, not independent validation or inter-annotator reliability. Do not ask an AI system for case-specific labels until Pass B is saved and frozen.
