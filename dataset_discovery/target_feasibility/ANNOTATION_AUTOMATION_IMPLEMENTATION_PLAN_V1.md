# Annotation Automation Implementation Plan v1.0

| Item | Value |
| --- | --- |
| Status | Approved for v1 implementation by user-provided authorization dated 2026-11-14 |
| Design baseline | [Annotation Automation Specification v1.0](ANNOTATION_AUTOMATION_SPEC_V1.md) |
| Rule registry | [Annotation Automation Rule Registry v1](ANNOTATION_AUTOMATION_RULE_REGISTRY_V1.csv) |
| Frozen baselines | Schema v2.2 and Protocol v1.0; neither will be edited by this plan |

## 1. Approved implementation scope

The user approved this plan for a small, read-only Python proposal generator, subject to the clarifications in the implementation authorization. It will not use an LLM to decide scholarly labels, write into existing v2.2 annotations, modify source data, or accept machine suggestions automatically.

The first build will test a narrow set of exact rule candidates and abstentions. It will not attempt to automate all annotation dimensions or process all 8,185 non-empty Shamela grade fields as if they were valid targets.

## 2. Clarifications carried into implementation

1. **Measure separate operations separately.** Exact extraction, candidate identity, statement segmentation, statement type, grade/base/qualification parsing, taxonomy mapping, and target eligibility have distinct outputs and evaluation denominators. A correct extracted string cannot be counted as a correct identity or annotation.
2. **Treat the pilot rules as candidates.** The three rank mappings in the registry may be used in a controlled dry-run after the registry is frozen. Their supporting adjudications do not validate them across the corpus. There will be no production auto-accept status in v1.
3. **Use new records for evaluation.** The ten existing cases are rule-development examples only. The evaluation sample will be selected from other narrator IDs and manually annotated from the sources before the reviewer sees machine proposals.
4. **Preserve missing evidence as missing.** Failure to detect a named evaluator does not establish compiler authorship, absence of an earlier critic, historical ineligibility, or a failed transmission route. Only the textual naming status may be recorded when the inspected passage supports it; the historical conclusions remain separate.
5. **Keep the first implementation small.** Use Python, CSV, JSON manifests, existing source files and v2.2 validators. No LLM agent, confidence model, database, annotation platform, graph construction, or model training.

## 3. Proposed pipeline and data flow

### Inputs

- A read-only snapshot of the Shamela4 narrator table and its SHA-256.
- A read-only snapshot/manifest for the local *Taqrīb al-Tahdhīb* text and edition metadata used for retrieval, including source book ID and entry/page identifiers.
- The approved rule registry, copied into the run package with its SHA-256.
- A new evaluation sample manifest. It must identify narrator IDs, selection method/seed, raw source hashes, and exclude all ten PROV pilot records from the evaluation split.
- Researcher-confirmed candidate identity and statement spans for the manual-first evaluation records. Name-match results from the existing crosswalk can help locate candidates but cannot satisfy this input requirement by themselves.

The raw `الرتبة عند ابن حجر` field is a discovery/sampling input and a candidate target source. It is not a validated target label or a model feature. The proposed generator will not assume any integer source ID denotes a quotation, page, passage, or bibliographic record.

### Processing stages

1. **Read-only preflight:** verify input paths, schemas, source metadata, hashes, unique identifiers, and the frozen rule registry. Fail if any expected input or registry value is missing or changed.
2. **Deterministic extraction:** copy original IDs, values, entry text, and locators without normalization; compute exact span comparisons and diagnostics without overwriting source text.
3. **Suggestion pass:** apply exact full-span rules only to researcher-confirmed candidate and statement spans. Emit rank-only suggestions for the three rank rules and statement-type suggestions for the exact generation phrases. No identity or eligibility decision is made by these rules.
4. **Fail-closed routing:** any unverified candidate, missing span, multiple match, unsupported form, alteration, qualifier, conflict, attribution issue, or unknown pattern results in an abstention with a reason.
5. **Human review:** the reviewer copy shows the source material and proposal after manual-first annotations are recorded. Human disposition is saved separately from the original proposal.
6. **Validation and manifest:** validate referential integrity, allowed values, exact text preservation, one-to-one proposal-to-rule traceability, and absence of writes to inputs. Record output hashes and counts by operation/rule/disposition/abstention reason.

### Proposed artifacts

Implementation, after approval, should create a new directory and refuse to overwrite it, for example:

```text
data/2_interim/shamela4_narrator_audit/annotation_automation_v1_0_1_development_dry_run/
  INPUT_SAMPLE_MANIFEST.json
  RULE_REGISTRY_SNAPSHOT.csv
  ANNOTATION_AUTO_PROPOSALS.csv
  HUMAN_REVIEW.csv
  RUN_MANIFEST.json
  RUN_MANIFEST.sha256
```

The existing `ANNOTATION_AUTO_PROPOSALS_V1.csv` is a proposed staging contract, not an approved final annotation table. If implementation reveals that the current columns cannot preserve a necessary distinction, stop and document the issue instead of modifying Schema v2.2 in code.

## 4. Rule registry handling

The current registry contains three candidate taxonomy rules:

- Full statement span `ثقة` → proposed rank 3.
- Full statement span `صدوق يخطىء` → proposed rank 5.
- Full statement span `صدوق اختلط في الآخر` → proposed rank 5.

It also contains exact generation-phrase candidates, with proposed status/generation classification only and no reliability rank. The generation rows are optional for the first executable version; they may be disabled if they add complexity without useful review-time savings.

All registry rows are currently `candidate_not_enabled` or `mandatory_guard`. Before running, freeze a copy of the exact rules, preconditions, supporting artifacts, and abstentions. Rank suggestions must not be copied into a frozen Pass 1 field; if accepted later, they belong in an explicit, evidence-linked post-first-pass adjudication record. Statement-type suggestions remain proposals until a human accepts them.

Do not match a grade token as a substring. For example, `ثقة` does not trigger the standalone rule inside `وثقه النسائي` or `ثقة له أفراد`. Exact rule matching applies to the whole researcher-confirmed statement span. Taqrīb spelling is compared as recorded; dataset spelling such as `يخطئ` is not normalized to `يخطىء` unless a separately reviewed comparison rule is approved. Such a comparison can report a minor textual variation, but cannot rewrite either source.

The absence guard is mandatory. A missing name or attribution marker must not generate `compiler_synthesis`, `surviving_wording_author=Ibn Hajar`, a negative historical claim, or historical-input ineligibility. If the relevant passage or scope has not been reviewed, preserve `not_assessed`; if it was examined and remains unclear, preserve `unresolved`.

## 5. New-sample design and manual-first evaluation

### Development and evaluation split

- Use the ten PROV cases only to draft the rule registry and define likely failure cases. Do not calculate rule precision/accuracy on them.
- Generate a read-only count of exact candidate-rule matches and near-matches across the source frame. This is a coverage scan, not annotation.
- Select evaluation records with narrator IDs not in the ten-case pilot. Record the fixed selection seed and sampling criteria before proposals are visible.
- Include, where available, exact candidate spans for each rule; hard negatives such as compound grades, attributed phrases, status-only text, punctuation/orthographic variants, and unknown patterns; and records likely to trigger abstention.
- Set the sample size only after inspecting per-rule population counts and the review budget. If a rule has too few independent records to evaluate, report that rule as unevaluated rather than borrowing its development examples or implying corpus-wide reliability.
- The researcher manually records candidate identity, span, statement type, grade base/qualification, rank, and relevant uncertainty from the source material first. Save and hash that manual-first record. Only then reveal the machine proposal and compare. This is single-researcher evaluation, not expert ground truth or independent validation.

### Operation-specific evaluation

| Operation | Comparison | Required reporting |
| --- | --- | --- |
| Exact text extraction | Exact character-level match to the cited local source text; punctuation/diacritic preservation reported separately. | Attempted extractions, exact matches, corrected transcriptions, missing/unavailable text, locator mismatches. |
| Candidate identity | Proposed/selected candidate versus the researcher's manually resolved candidate and status. | Confirmed/probable/unresolved/mismatch separately; never treat name-search recall as identity accuracy. |
| Statement segmentation | Proposed boundaries versus manually drawn boundaries. | Exact span match, partial boundary match, missed/split/merged statement; explain boundary changes. |
| Statement classification | Field-by-field comparison for `statement_type`, base grade, qualification, and status. | Exact agreement and correction/rejection by field and rule; keep identity/attribution separate. |
| Taxonomy mapping | Rank proposal versus the manual taxonomy decision with its cited rule. | Exact rank agreement among applicable spans; incorrect rank and abstention counts by rule. |
| Target eligibility | Manual decision under the frozen v2.2 guard. | Human-adjudicated eligible/excluded/unresolved/not-assessed counts and rationale. No automatic target eligibility metric is claimed because v1 rules do not decide it. |
| Historical attribution and input eligibility | Source-based human determination only. | Report unresolved/not-assessed status and evidence checked; no automation score for an unimplemented scholarly decision. |

Also report, per rule and per field:

- **Coverage:** proposals divided by a stated eligible denominator, plus counts against the raw non-empty field pool. Do not describe 8,185 as eligible targets.
- **Human acceptance:** accepted without edits / proposals reviewed.
- **Correction and rejection:** counts, rates, direction, and error category.
- **Abstention:** counts/rate with reasons; report separately for unsupported, multi-match, identity, textual, and attribution conditions.
- **Severity:** identity, target leakage, role/segmentation, rank, attribution/provenance, and formatting-only errors remain separate. Do not combine them as equally consequential.
- **Review time:** compare manual-only with assisted work only on comparable records; include setup and correction time.

Human acceptance is not independent truth. Do not claim a precision threshold from the single-reviewer comparison. Do not set a 60–70% coverage target before measuring it.

## 6. Leakage, provenance, and version controls

- Keep target preparation separate from model-feature construction. Exclude target phrases, ranks, original grade fields duplicating the target, target-derived encodings, and dependent later reproductions from predictive inputs.
- Carry forward the existing v2.2 Task A feature firewall and evidence-bearing eligibility guard. A proposal script may not bypass or weaken either one.
- Record source work, consulted edition/corpus artifact, entry/page locator, exact evidence span, verification mode, and input hash. A local digital corpus transcription is not described as printed-page verification unless the image was checked.
- Keep candidate identity evidence independent of grade wording. A name-derived link is only a search candidate.
- Keep case-level source evidence and statement-level evidence linked to their actual scope. Do not transfer an evidence match to every statement in an entry.
- Every run uses a new versioned output path; it refuses to overwrite. Original source data, v1/v2.2 annotation packages, Pass 1 freezes, and adjudications are read-only inputs.

## 7. Implementation acceptance checks

After approval and implementation, the first run is accepted only if:

1. Every proposal references one frozen rule ID/version and an exact source span.
2. Unsupported, substring-only, multiply matched, unverified, or altered inputs abstain.
3. The rank rules cannot change identity, statement authorship, attribution, target scope, or historical-input eligibility.
4. Generation phrases never receive reliability ranks.
5. Missing attribution evidence never produces a positive or negative historical conclusion.
6. All source text round-trips exactly through CSV, including Arabic, punctuation, diacritics, and embedded newlines.
7. Fixed input and rule hashes produce deterministic outputs; a second run refuses to overwrite the first.
8. v2.2 package validation and feature/target leakage invariants are preserved.
9. Input hashes before/after are identical, and the manifest clearly says no annotations were auto-approved.
10. The new-sample evaluation has manual-first labels saved before machine proposals are revealed; the report separates every operation listed in Section 5.

Tests for the implementation should include exact full-span positives, substring negatives (`وثقه النسائي`, `ثقة له أفراد`), the two exact Rank-5 phrases, generation-versus-rank separation, spelling variation abstention, no-evaluator negative-inference guard, rejected-homonym exclusion, ambiguous-source abstention, deterministic rerun, overwrite refusal, and CSV/Arabic round-trip integrity. These are planned tests only; none have been implemented or run in this planning step.

## 8. Out of scope

This plan does not implement a script, generate proposals, alter Schema v2.2 or Protocol v1.0, change the rule registry after user approval, modify existing annotations or frozen packages, produce an eligible-target count, build a narrator graph, or train/evaluate a model.

## Related artifacts

- [Annotation Automation Specification v1.0](ANNOTATION_AUTOMATION_SPEC_V1.md)
- [Candidate Rule Registry v1](ANNOTATION_AUTOMATION_RULE_REGISTRY_V1.csv)
- [Frozen Schema v2.2](MANUAL_COLLATION_SCHEMA_V2_2_FINAL.md)
- [Frozen Protocol v1.0](../../data/2_interim/shamela4_narrator_audit/manual_annotation_working/PILOT_EVALUATION_AND_ANNOTATION_PROTOCOL_V1.md)
- [Target feasibility report](TARGET_FEASIBILITY_REPORT.md)
