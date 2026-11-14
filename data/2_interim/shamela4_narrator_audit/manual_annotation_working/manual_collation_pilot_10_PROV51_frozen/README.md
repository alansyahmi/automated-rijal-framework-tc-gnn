# PROV-51-C01 first-pass freeze

**Status:** User approved for first-pass freezing on 2026-11-13.
**Scope:** PROV-51-C01 only. This package snapshots the full Round 1 working copy for relational context; other cases in the snapshot are not approved or frozen here.

## Frozen decisions

- **Identity:** confirmed from al-Mizzi, *Tahdhib al-Kamal*, entry 5067, using the name, lineage and al-ʿAnsi al-Himsi identification; evaluative wording was excluded. Preserve the differing name forms without normalization.
- **Candidate correspondence:** the original Shamela4 field wording matches Taqrib entry 5735 exactly in the local corpus transcription. The Taqrib entry is at local page 468; its page metadata says numbering matches print, but the Awwamah printed page image was not visually checked.
- **S01:** `عابوا عليه أنه حدث عن أبيه بغير سماع` is a specific transmission criticism, not a standardized grade. No numerical rank is assigned; target scope is `not_in_defined_task`.
- **S02:** `من العاشرة` is a generational classification, not reliability rank 10.
- **Attribution:** the `عابوا` collective remains unidentified; historical evaluator, route and compiler authorship remain unresolved.
- **Earlier reports:** Abū Ḥātim and the separate Abū Dāwūd report are preserved as candidate-level context evidence (`evidence_role=other`), not linked to S01’s attribution. Their semantic relationship does not establish attributional equivalence.
- **S00:** retained as a superseded placeholder. No legacy annotation values were introduced.
- **Eligibility:** neither statement is included in the defined supervised target; historical-input eligibility for S01 remains not assessed.

## Review and validation limits

This is an AI-assisted single-reviewer feasibility record approved by the user. It is not independent scholarly validation or an inter-reviewer agreement result. No narrator-reliability conclusion, historical source route, or grade provenance is established.

The regression suite passed (72 tests). The PROV-51 direct row/link integrity checks and all package file hashes passed. The strict package-wide validator remains blocked by pre-existing source metadata, evidence ownership and temporal-policy status inconsistencies in other cases; those records were not changed in this freeze.

The complete research memo is in `source_research/PROV-51_source_research.md`; the full working-copy snapshot is in `working_copy_snapshot/`.
