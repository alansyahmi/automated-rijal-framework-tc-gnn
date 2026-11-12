# Manual-collation Schema v2.2.2 attribution amendment

**Date:** 2026-11-12  
**Status:** Narrow implementation correction; frozen Schema v2.2 unchanged.

## Finding

The v2.2.1 ordinary-grade guard and table validator treated named earlier-evaluator wording as incompatible with `attribution_form=compiler_synthesis`. This was stricter than the frozen v2.2 rule. A Taqrib passage can name an earlier evaluator while Ibn Hajar's surviving wording presents a compiler synthesis. Naming an earlier evaluator does not, by itself, settle who formulated the surviving assessment.

The defect caused two false negatives: the ordinary-grade eligibility helper rejected a supported synthesis with a named evaluator, and staged validation rejected the same internally consistent attribution record.

## Correction

Implementation 2.2.2 removes the blanket conflict between `compiler_synthesis` and named or collective evaluator wording. The ordinary-grade guard still requires all frozen-schema target conditions, including:

- Ibn Hajar is the identified surviving wording author.
- `compiler_authorship_status=supported`.
- `attribution_form=compiler_synthesis`.
- The passage naming status is assessed and consistent with its evaluator value/name fields.
- Required candidate, statement, source, identity, and passage evidence is linked and verified.

An explicitly attributed earlier-critic statement still fails the ordinary-grade guard because its attribution form is not `compiler_synthesis`. The passage-naming and historical-attribution fields remain separate: accepting a compiler synthesis that names an earlier evaluator does not establish that evaluator's historical attribution, a traceable transmission route, independent corroboration, or the accuracy of the quoted judgment.

No field, enum, cross-field schema rule, input annotation, or original source value was changed. The v2.2.1 script, package, and implementation record remain preserved as historical artifacts.

## Versioned implementation and verification

The corrected script is `migrate_manual_collation_v2_2_impl_2_2_2.py`. It generated a separate, non-overwriting package at:

`data/2_interim/shamela4_narrator_audit/manual_annotation_working/manual_collation_pilot_10_v2_2_impl_r2/`

The package contains 10 cases, 11 candidate entries, and 11 provisional work items. It contains zero reviewed scholarly statements and no newly populated human judgments. The package manifest records hashes for all inputs and outputs; its own checksum is stored separately in `MANIFEST.sha256`.

### Regression and suite results

- Three focused 2.2.2 attribution regressions passed. Before the correction, the two positive regressions failed on the guard and validator respectively.
- Full target-feasibility suite: **72 tests passed** with `python -m unittest discover -s dataset_discovery/target_feasibility -p "test*.py" -v`.
- `git diff --check`: passed. Git emitted only the pre-existing LF-to-CRLF warnings for the two modified README files.
- Independent package check: all 12 manifest-listed output hashes matched for both v2.2.1 and v2.2.2; both manifest checksums matched. No v2.2.1 output mismatch was found.

## Preservation hashes

The frozen specification, original v2.2.1 script, and v2.2.1 manifest still match their established SHA-256 values:

| Artifact | SHA-256 |
|---|---|
| Frozen v2.2 specification | `2bcba2ade81ce57ec9075bd587c3ab62eafb09845183cfa1d44b6e709d38c860` |
| v2.2.1 migration script | `92dce857fa4931075d67cac9ba78c6ddf89d339ccfbf63fe2ccc8ae27220c3ca` |
| v2.2.1 package manifest | `708390595ab807406234aa04a0f8bba0657fb0c485eac4ed13e628e2a87bbe48` |

The four pinned inputs still match the v2.2.1 baseline:

| Input | SHA-256 |
|---|---|
| Frozen pilot packet | `78cb15eb72b04c1b2c0d2e350e375615236df22a2918c38256977ccccffae958` |
| Working annotation record | `4b3f731b5a799c1df499c57391f4b502fcee84f129c2bae2e77325e738a04548` |
| Provenance key | `9eccd4533cb4482390a41861955e3636453d1f0bc39e8aac544f748f4dcc0684` |
| Input manifest | `9339ad77f1fa18e204b443e9a3ec888d6ec56924b801b85d94f3bb8ea49bf72d` |

The new implementation and package hashes are:

| Artifact | SHA-256 |
|---|---|
| v2.2.2 migration script | `b50d18579c8c57f6fc95668fe29ad6c5003a130be4be0827313daf55be600d55` |
| v2.2.2 package manifest | `e11d45cc1e6c11a3479767478766b23bf33070e15c8c76596d3852db8526dc45` |

Per-file v2.2.2 output hashes are recorded in the new package manifest and verified against the published files.

## Research boundary

This correction addresses software eligibility logic only. It does not determine whether any of the ten records is actually Ibn Hajar's synthesis, historically accurate, independent of earlier authorities, or suitable as a research target. Those remain evidence-based human review decisions. The package is still a scaffold, not a scholarly judgment set or model-ready data.
