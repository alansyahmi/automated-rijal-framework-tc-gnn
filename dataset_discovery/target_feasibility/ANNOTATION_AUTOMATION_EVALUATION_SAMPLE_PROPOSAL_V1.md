# Annotation Automation v1: Manual-First Evaluation Sample Proposal

| Item | Value |
| --- | --- |
| Status | Proposal only; no evaluation records selected or annotated |
| Development package | `data/2_interim/shamela4_narrator_audit/annotation_automation_v1_0_1_development_dry_run/` |
| Current reviewer capacity | One researcher; results must be described as a within-researcher comparison |
| Pilot exclusion | All ten PROV narrator IDs listed below |

## Purpose and limits

The next sample would examine whether the three narrow, exact Taqrīb rank proposals behave as intended on new, manually reviewed records, and whether the generator abstains on representative difficult cases. It would not establish historical attribution, narrator reliability, expert validity, inter-reviewer agreement, or corpus-wide performance. The sample is purposive and rule-stratified; its counts must not be generalized to the full Shamela4 corpus.

The existing ten-case PROV packet remains development material only. Do not use it to estimate agreement or as part of the evaluation denominator.

## Proposed sample

Use at most 20 distinct Shamela4 narrator IDs, subject to a read-only enumeration of the eligible source pool and the researcher's review budget:

| Stratum | Proposed allocation | Selection purpose |
| --- | ---: | --- |
| Exact standalone `ثقة` | Up to 5 | Exercise the rank-3 proposal rule on new source entries |
| Exact `صدوق يخطىء` | Up to 5 | Exercise the first rank-5 proposal rule |
| Exact `صدوق اختلط في الآخر` | Up to 5 | Exercise the second rank-5 proposal rule |
| Abstention challenges | Up to 5 | Include available compound/qualified text, attributed criticism, Companion/status wording, generation wording, spelling variation, or unresolved identity/source cases |
| **Maximum** | **20** | Feasibility sample only |

The proposed allocation is conditional, not a quota to force. If fewer than five distinct eligible narrators exist in a rule stratum, include the available cases and report that rule as thinly represented or unevaluated. Do not replace missing cases with members of the PROV pilot. Select one primary Taqrīb candidate entry per narrator ID; record any unavoidable work/source overlap in the internal sample key.

Before selecting records, enumerate the available exact-span and challenge pools from the verified local Taqrīb corpus. Treat the raw Shamela4 grade field only as a discovery aid. A phrase match does not establish identity, correct segmentation, target suitability, or historical provenance. Do not infer the semantics of an integer source ID.

After the eligible frame and exclusions are frozen, use a recorded deterministic seed (`20261114` is proposed) to choose within each stratum. Save the frame hash, selected ID list, seed, and selection code or command in a separate internal key. Hide the stratum labels and all machine-rule fields from the first-pass reviewer copy.

## IDs excluded from evaluation

Exclude the ten distinct narrator IDs in the existing PROV pilot, including the rejected-candidate row associated with PROV-04:

| Case | Shamela4 narrator ID |
| --- | ---: |
| PROV-10 | 515 |
| PROV-40 | 1813 |
| PROV-39 | 1811 |
| PROV-56 | 6996 |
| PROV-24 | 1214 |
| PROV-51 | 5498 |
| PROV-01 | 17 |
| PROV-02 | 27 |
| PROV-04 | 278 |
| PROV-37 | 1740 |

## Manual-first workflow

1. Freeze the eligible source frame, sample key, seed, and exclusion list. The internal key may contain stratum and rule-candidate information; the reviewer copy must not.
2. Prepare a separate blank manual-first sheet containing source and identity context, exact entry text and locator, and blank fields for the researcher's identity decision, statement spans, statement roles, verbatim wording, grade base/qualification, taxonomy rank, uncertainty, and notes. Do not include rule IDs, automated pattern labels, proposed ranks, or stratum labels.
3. The researcher checks the source entry and identity, segments statements, records exact wording, and completes the manual fields without seeing proposals. Preserve unresolved identity, text, rank, or attribution as unresolved.
4. Save the completed manual-first sheet and calculate its SHA-256 before generating or opening any machine proposal. Record that hash and timestamp in a separate evaluation manifest.
5. Only after the manual-first snapshot is frozen, run a separately scoped evaluation process. The current v1 command is deliberately restricted to the registered PROV development packet; do not point it at evaluation records or relabel a development run. A future evaluation-mode change must verify the non-PROV IDs and the frozen manual-first hash before revealing proposals.
6. Compare by operation and by rule. Preserve manual-first values, machine proposals, and any later human reconciliation in separate files.

## Reporting after the review

Report case-wise counts with explicit denominators, separately for:

- Exact source text extraction and locator checks.
- Candidate identity status and unresolved/mismatch decisions.
- Statement boundary agreement, including exact, partial, split, and missed spans.
- Statement role and grade/qualification parsing.
- Taxonomy rank decisions for applicable rule cases, by rule ID.
- Proposal accepted unchanged, corrected, rejected, or unresolved.
- Abstention decisions and reasons in each challenge stratum.
- Any changes between manual-first and later reconciliation, with reasons.

Do not collapse these dimensions into one agreement score. Do not call the researcher's own manual-first decisions expert ground truth. Do not claim corpus-wide accuracy, precision, or coverage from this purposive sample. Target suitability, historical-input eligibility, attribution, and transmission-route questions remain separate human decisions and are not proposed by the generator.

## Decision still open

This proposal does not select the 20 records. The next preparation step is to inspect the exact-match population counts and the reviewer's available time, then freeze the eligible frame and create the blinded manual-first materials. Until then, no evaluation proposals are generated.
