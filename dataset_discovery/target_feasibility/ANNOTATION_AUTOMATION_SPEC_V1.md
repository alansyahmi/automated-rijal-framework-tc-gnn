# Annotation Automation Specification v1.0

| Item | Value |
| --- | --- |
| Status | Proposed design; implementation not authorized by this specification |
| Schema baseline | Frozen Manual Collation Schema v2.2 |
| Annotation protocol | Frozen Pilot Evaluation and Annotation Protocol v1.0 |
| Protocol v1.0 SHA-256 | `D64B0658071C2A1796E6EDA593A295CE551A38AA10E85D42AC669F9AEA87ED20` |
| Date | 2026-11-14 |

## 1. Purpose and decision

This specification defines a conservative human-in-the-loop workflow for automating repetitive extraction and proposing annotations only when explicit, reviewable rules apply. Unsupported or complex cases must be routed to human review. This document does not implement an annotation engine, approve new labels, alter frozen records, change Schema v2.2, or authorize model training.

**Recommendation:** proceed with selective automation, initially as deterministic extraction plus rule-based suggestions. Do not let suggestions silently become accepted annotations. Keep final v2.2 annotation records separate from machine proposals until the researcher has reviewed them.

The intended research target remains Ibn Ḥajar's classification in *Taqrīb al-Tahdhīb*. That is a prediction target defined by the research design; it is not a claim that the system establishes historical truth or narrator reliability. Extracting a target from *Taqrīb* is a data-preparation operation. Predicting that target from eligible historical evidence is a separate machine-learning operation.

## 2. Current evidence and limits

The local target-feasibility report identifies 18,989 Shamela4 narrator records, of which 8,185 have a non-empty `الرتبة عند ابن حجر` field. Those values include 1,343 distinct raw strings. The report marks **zero** records as validated supervised targets. The HadithDB field is populated for 1,508 of 1,524 records, but its upstream field-level semantics and record-level provenance are likewise not established. These are raw field-availability counts, not a count of straightforward, correct, or eligible labels. See [TARGET_FEASIBILITY_REPORT.md](TARGET_FEASIBILITY_REPORT.md), [DATASET_COVERAGE.csv](DATASET_COVERAGE.csv), and [LABEL_DISTRIBUTION.csv](LABEL_DISTRIBUTION.csv).

The ten-case pilot has 10 source cases, 11 candidate entries, and 34 substantive reviewed statements, with three superseded placeholders excluded from the statement count. Seven cases have recoverable contemporaneous Pass 1 snapshots; PROV-37, PROV-39, and PROV-40 do not. Five separate rank adjudications exist. The cases are purposive and selected to expose difficult issues; they cannot estimate automation coverage, corpus-wide error, or accuracy. The frozen [Protocol v1.0](../../data/2_interim/shamela4_narrator_audit/manual_annotation_working/PILOT_EVALUATION_AND_ANNOTATION_PROTOCOL_V1.md) explicitly distinguishes the pilot's incomplete archival history and remaining interpretive uncertainty.

### Existing scripts inspected

| Existing artifact | Current role | Automation implication |
| --- | --- | --- |
| [audit_target_feasibility.py](audit_target_feasibility.py) | Read-only inventory, raw-value counts, and candidate crosswalk suggestions. Its normalized name keys are retrieval aids; the script explicitly does not adjudicate identity. | Reuse for candidate discovery and audit statistics only. Do not promote a name match or grade substring into a confirmed identity or label. |
| [generate_grade_provenance_worksheet.py](generate_grade_provenance_worksheet.py) | Extracts candidate strings, computes diagnostic flags, samples records, and writes blank human-review fields. Its categories are explicitly diagnostic, not estimates of annotation error. | Reuse its extraction/sampling ideas after review. Diagnostic flags must not become statement-type, attribution, or target decisions. |
| [migrate_manual_collation_v2_2_impl_2_2_2.py](migrate_manual_collation_v2_2_impl_2_2_2.py) | Non-destructive v2.2 migration scaffold, structured output, and validators. It does not infer human annotation decisions and records that annotations were not inferred. | Reuse its schema, relationships, fail-closed guard, hash checks, and package validation. Do not repurpose migration as a general semantic annotator. |
| [establish_rijal_reference_corpus.py](establish_rijal_reference_corpus.py) | Retrieves and inventories source texts and checks corpus structure and metadata. | Supports source retrieval and reproducible inventories; it does not establish a narrator match or historical attribution. |

The source specifications remain authoritative: [Schema v2.2 final specification](MANUAL_COLLATION_SCHEMA_V2_2_FINAL.md), [Schema v2.2 field specification](MANUAL_COLLATION_SCHEMA_V2_2_SPEC.md), [Pilot review guide](MANUAL_COLLATION_PILOT_10_REVIEW_GUIDE.md), and [provenance and temporal firewall](PROVENANCE_AND_TEMPORAL_FIREWALL_SPEC.md).

## 3. Output and annotation states

Automation must use three separate states:

1. **Extracted source data:** verbatim values and deterministic metadata copied from a hashed source artifact. This is not a scholarly annotation.
2. **Machine proposal:** a rule-linked suggestion or an explicit abstention. It is provisional and is not an approved v2.2 decision.
3. **Human-reviewed annotation:** the researcher's decision, entered into a working derivative and promoted only through the existing reviewed/freeze process.

Do not add an `auto_approved` status to the frozen v2.2 schema. Store proposals in a separate, versioned staging table such as `ANNOTATION_AUTO_PROPOSALS_V1.csv`, with a manifest. A proposal row should contain, at minimum:

- `proposal_id`, source dataset and record ID;
- `candidate_entry_id` and `statement_id`, when those have already been established;
- input artifact path and SHA-256, source work/edition/corpus artifact, locator, and exact matched text span;
- `proposal_type` (`deterministic_extraction`, `rule_suggestion`, or `abstention`);
- proposed v2.2 field and value, or null when abstaining;
- `rule_id` and rule-set version; for extraction, the parser/extractor version;
- gate result and a concise rationale;
- abstention reason, when applicable;
- human disposition (`unreviewed`, `accepted`, `corrected`, `rejected`, `deferred`) and reviewer note/date.

The staging file is append-only for a run. A correction creates a new proposal/review event or a new versioned output; it does not erase the original machine suggestion. The manifest records input hashes, rule-set hash, software version, run date, output hash, and counts by proposal type, rule, disposition, and abstention reason. It must state that suggestions were not promoted automatically.

The existing schema has no dedicated annotation-origin field. Keeping machine proposals outside v2.2 avoids silently changing the frozen schema and preserves the distinction between an algorithmic suggestion and a human decision.

## 4. Automation levels

### Level 1 — Deterministic extraction and validation

These operations may be automated when they preserve source information exactly:

- Read dataset IDs, record keys, original Arabic values, original field names, existing source locators, and corpus metadata.
- Extract an entry by an already verified book/entry key or an existing, reviewed crosswalk. If the key is absent or non-unique, abstain and produce candidate search results only.
- Copy a source passage and compute exact-string comparison results. Report differences without changing the original string.
- Compute diagnostic comparison keys for punctuation or orthographic differences only if the raw strings remain untouched and the transformation is fully logged. A comparison key must never replace the raw evidence or independently establish meaning.
- Validate CSV/JSON structure, required values/status pairs, IDs and foreign keys, evidence links, enum values, hashes, and the current analytical eligibility invariants.
- Count results and report overlap, duplicate, missingness, and abstention statistics with explicit denominators.

An existing normalized name match can identify records to inspect; it is not a verified identifier. A source integer has no assumed meaning as a quote, page, passage, or bibliographic entity. Candidate identity may be auto-confirmed only if a separately verified, persistent identifier unambiguously joins the records and the crosswalk itself is hash-linked and documented. In the current project, name/lineage-based joins remain candidate matches for human identity review.

### Level 2 — Rule-based suggestions requiring human confirmation

Suggestions may be generated only from a versioned allowlist of exact patterns with recorded Arabic span, rule rationale, and exclusions. The first rule set should be deliberately small. Initial candidates for evaluation, based on existing case adjudications, are:

| Proposed rule family | Exact pilot evidence | Permitted proposal | Explicit exclusions |
| --- | --- | --- | --- |
| Standalone `ثقة` | PROV-10-C01-S01 and PROV-40-C01-S01 have separate rank-3 taxonomy adjudications citing Ibn Ḥajar's introduction. | Suggest `standardized_narrator_grade`; suggest rank 3 only for the exact, complete statement span `ثقة`, after the Taqrīb candidate and span have been confirmed. | Do not match the substring inside `وثقه النسائي`, `ثقة له أفراد`, or a compound phrase. Do not infer target scope, authorship, or historical-input eligibility. |
| Exact `صدوق` plus approved error/change qualifier | PROV-37, PROV-39, and PROV-56 have separate rank-5 adjudications for `صدوق يخطىء` / `صدوق اختلط في الآخر` in the cited spans. | Suggest a grade statement with its base and qualification preserved; suggest rank 5 only for an exact rule entry supported by the taxonomy and adjudication record. | Do not strip the qualifier; do not generalize to unseen synonyms, spelling variants, or other compounds; do not infer broad unreliability or target eligibility. |
| Explicit generation phrase | Pilot spans include forms such as `من الثالثة`, `من العاشرة`, `من كبار السابعة`, and `من الثامنة`. | A future exact grammar may suggest `descriptive_or_generational_status` and parse the generation into a separate field if the schema/task requires it. | Never turn a generation number into a reliability rank. Unknown ordinal wording, mixed clauses, or malformed text abstains. |

These are **candidate rules for evaluation, not enabled production rules**. Before enabling one, record its exact accepted string/span forms, source requirement, rule ID, known counterexamples, and human review outcome. Five case-level rank adjudications do not establish coverage or accuracy across 1,343 distinct raw strings.

Segmentation, statement type, grade base/qualification, and candidate identity can receive suggestions only when the input span has been extracted without loss and a human has confirmed the source entry. During the first pilot, require human confirmation for each such suggestion. Simple punctuation checks may be deterministic diagnostics, but punctuation changes are not a substitute for scholarly text comparison.

### Level 3 — Human decision required

The following cannot be finalized automatically under the current evidence and schema:

- Confirming narrator identity from names, lineage, geography, generation, or source dependence when no verified persistent crosswalk exists.
- Resolving homonyms or choosing among multiple candidate entries.
- Interpreting compound or qualified assessments not covered by an exact approved rule.
- Distinguishing a grade from biography, status, a report of another critic, specific transmission criticism, editorial matter, or a mixed passage when the exact structural rule has not been validated.
- Establishing passage-level wording authorship, historical evaluator attribution, intermediaries, transmission route, literary dependence, or independent corroboration.
- Assessing edition variants, whether an editor introduced a reading, or whether a printed page locator matches the consulted scan.
- Assigning `ordinary_grade_candidate`, `status_only_candidate`, historical-input eligibility, or final analytical inclusion.
- Resolving conflicting evidence, unknown source semantics, or any case where an automated proposal depends on meaning rather than literal matching.

AI may help retrieve passages, compare transcription, or point out a possible conflict after the researcher has recorded an independent decision. AI output is assistance, not an independent annotator, source, or validation reference.

## 5. Fail-closed suggestion gate

A rule-based suggestion may be emitted only when every applicable condition below passes:

1. Source record and original value are tied to a recorded input artifact hash.
2. The candidate entry is unique by a verified key or has already been confirmed by the researcher using non-grade evidence.
3. The exact Taqrīb entry text and locator are available with the actual verification status recorded.
4. The statement span is either researcher-confirmed or produced by a separately validated exact segmentation rule.
5. The complete span exactly matches a versioned rule, not merely a substring within a larger statement.
6. The rule does not rely on source assumptions, normalized-away text, an unreviewed orthographic equivalence, or a free-form model confidence score.
7. No unhandled qualifier, exception, attribution cue, multiple claim, bracket, footnote, textual variant, conflict, or alternative candidate is present.
8. The proposed field is within the rule's declared scope. A rank rule cannot assign evaluator, identity, target-scope, or historical-input fields.

If a condition fails or cannot be checked, the system emits `abstention` with a reason and routes the record to manual review. Missingness is never converted into a positive label. `unknown`, `unresolved`, `not_assessed`, and `not_applicable` retain their v2.2 meanings.

No numeric confidence threshold is proposed for v1.0. Model confidence is not calibrated for these scholarly distinctions, and no reviewed corpus establishes a threshold. If a statistical model later proposes annotations, it must have a separately measured selective-prediction curve and a reviewed holdout before any threshold is considered. Selective prediction research supports allowing systems to abstain, but does not validate any particular threshold or Arabic rijāl classifier here ([Xin et al., ACL 2021](https://aclanthology.org/2021.acl-long.84/)).

## 6. Target extraction and target leakage firewall

### Target extraction

Target preparation may copy the exact classification span from a confirmed *Taqrīb* entry and propose a taxonomy mapping under an approved rule. Record the exact label source, entry/statement ID, source text, locator, rule ID, and input hashes. Keep taxonomy rank separate from identity, passage attribution, task eligibility, and historical-input eligibility. The v2.2 ordinary-grade guard remains controlling; the proposal stage cannot bypass it or promote an unresolved statement.

### Predictive inputs

For a task that predicts the *Taqrīb* classification, prohibit from input features:

- The target phrase, original dataset grade field when it duplicates the target, assigned rank, or any encoded/normalized derivative of them.
- The target *Taqrīb* entry itself, its identity-bearing grade span, or a later source that merely repeats the target as if it were independent historical evidence.
- IDs, filenames, row order, group keys, or metadata that reveal the label through storage or extraction conventions.
- A graph edge or node attribute derived from the target, a later copy of the target, or a target-informed identity resolution.

All proposed features must be linked to their source, subject/candidate, date/provenance evidence, exclusion-policy version, and inclusion rationale. The current migration validator already rejects the target source/work as an independent Task A feature and checks explicit feature-source relationships. The future automation system must preserve those checks rather than reimplementing a weaker gate. Unlabelled records may be considered for permitted unsupervised or graph construction only under a separate leakage review; they are never labelled examples merely because a suggestion exists.

## 7. Dry-run against the ten pilot cases

This matrix tests the **design logic only** against existing records. It does not run a program, rescore the cases, or change their annotations.

| Case | Proposed automation behavior | Why / required human boundary |
| --- | --- | --- |
| PROV-10 | After confirmed candidate and exact span, `ثقة` could receive a rank-3 suggestion. | The separate rank adjudication supports that taxonomy mapping. `يقال له رؤية` contains a reported-claim cue and remains human-reviewed; the death statement is not a grade. Target scope and attribution do not follow from rank. |
| PROV-40 | The isolated `ثقة` span is a candidate for the same rank-3 suggestion. | Candidate biography and literary relationship require human/source review. Its Pass 1 snapshot is missing, so it is not a recoverable frozen reference case for measuring automation agreement. |
| PROV-39 | The exact grade span `صدوق اختلط في الآخر` could receive a rank-5 suggestion after span confirmation. | Full-entry segmentation, the sighting claim, the criticism attributed to Ibn ʿUyaynah and Aḥmad, and their scope require human review. The missing Pass 1 snapshot also limits use as a frozen reference. |
| PROV-56 | The exact Taqrīb span `صدوق يخطىء` could receive a rank-5 suggestion. | Do not normalize the dataset spelling/punctuation to force a match. Human-confirm identity, exact source correspondence, and span first. Rank does not resolve historical provenance or target eligibility. |
| PROV-24 | `وثقه النسائي` routes to human attribution review; `من الثالثة` may receive a generation-type suggestion only after an exact grammar is approved. | The passage names al-Nasāʾī, but the historical route and source remain unresolved. The generation phrase is not a reliability rank, and the locator discrepancy remains. |
| PROV-51 | Abstain to human review. | `عابوا عليه` is a specific criticism with an unidentified collective; related Abū Ḥātim/Abū Dāwūd reports do not identify that collective or establish a route. `من العاشرة` is not a rank. |
| PROV-01 | Do not send `صحابي` to an ordinary-grade rule. A status-type suggestion may be considered later, but keep target scope for human decision. | Companion status is distinct from ordinary reliability rank. The five separate claims, evidence relationships, and locator/source dependence need claim-level handling. |
| PROV-02 | Abstain to human review. | One compound qualified assessment includes teacher/Basra-specific limitations and a bracketed Asim phrase. Do not split or normalize it using the current simple rules. |
| PROV-04 | Abstain on candidate identity and annotation; route both C01/C02 through the human homonym review. | C02 is a rejected homonym, and C01's `ثقة له أفراد` is not the standalone `ثقة` rule. Preserve the rejected candidate and exclude it from target extraction. |
| PROV-37 | The exact grade span `صدوق يخطىء` is a candidate rank-5 suggestion only after fresh human confirmation. | Its original Pass 1 snapshot is missing. Do not use the later row or adjudication as if it were a contemporaneous automation reference. Identity and adjacent homonym resolution remain human decisions. |

The dry-run shows a useful but narrow role for automation: copy and validate exact data; make a few taxonomy proposals after identity/span confirmation; abstain on attribution, compound text, target eligibility, and the cases whose preserved first-pass reference is incomplete. It does not demonstrate a 60–70% automation rate. That percentage remains illustrative and must not appear as a forecast.

## 8. Evaluation plan for a first automation pilot

### Before running

1. Freeze the rule registry and its examples/exclusions. Do not tune rules against the same review decisions later reported as an evaluation set.
2. Select a new, stratified batch from the eligible candidate pool. Include exact simple patterns and likely failure modes; do not use the ten purposive cases to estimate population accuracy.
3. For an evaluation subset, the researcher records annotations from the source material before seeing machine proposals. Because the researcher has seen the existing pilot and this is a single-reviewer study, call the results a within-researcher comparison, not expert gold or independent validation.
4. Keep source inputs, proposal output, human review, and final accepted annotations in separate, hash-linked artifacts.

### Report per rule and per field

- **Candidate-pool denominator:** number of source rows considered and number with non-empty raw values.
- **Automation coverage:** proposals divided by an explicit eligible denominator; also report abstentions and reasons. Do not use 8,185 populated strings as an eligible denominator without saying it is raw-field coverage only.
- **Exact acceptance:** suggestions accepted without edit divided by reviewed suggestions.
- **Correction and rejection:** number/rate corrected or rejected, with direction and error type.
- **Abstention rate:** rows routed to human review divided by the same explicit denominator.
- **Severity:** separately count identity errors, target leakage, statement-role/segmentation errors, rank errors, attribution/provenance errors, and formatting-only differences. Do not treat them as equal-cost errors.
- **Time:** record review time for comparable manual-only and assisted cases; estimate saved time only if both workflows were observed on comparable work.
- **Distribution:** report results per rule, class, statement type, and relevant construction/format stratum, not only one aggregate.

Human acceptance of a suggestion is not independent ground truth, especially if the suggestion was visible before annotation. Initial rule proposals therefore remain human-confirmed. If auto-only values are later used for model fitting, mark them as machine-labelled/silver data and evaluate on a separate human-reviewed set; do not present machine-generated targets as a validated test set.

Automatic pre-annotation can improve speed in some controlled annotation tasks, but it can also affect how annotators label. One LREC 2022 experiment studied dependency-syntax annotation, not historical Arabic interpretation; it is a reason to measure efficiency and bias in this project, not evidence that these rules are accurate here ([Mikulová et al., LREC 2022](https://aclanthology.org/2022.lrec-1.312/)).

## 9. Implementation gates and non-goals

Implementation should start only after the researcher approves the precise rule registry and output contract. The first executable version should be a read-only dry-run that writes a new versioned proposal directory, refuses to overwrite existing outputs, records source hashes, and never writes to raw inputs or frozen packages.

Required implementation checks, when code is later requested:

- Exact Arabic CSV round-trip, including punctuation, diacritics, and embedded newlines.
- Stable, deterministic output for fixed inputs/rules.
- Each suggestion links to an exact source span, rule ID/version, and input hash.
- Unmatched, multiply matched, unsupported, and malformed cases abstain.
- No model-confidence threshold or silent `auto_approved` value.
- The existing v2.2 links, enum constraints, target guard, temporal firewall, and no-leakage checks still pass.
- Existing raw data, frozen snapshots, and prior versioned outputs remain unchanged.

This specification does not authorize: automatic historical attribution; automatic source-independence decisions; automatic resolution of identities from names alone; automatic target/historical-input eligibility; rewriting of source text; training; graph construction; or an asserted automation coverage percentage.

## 10. Current recommendation

Proceed in this order:

1. Complete the short consistency check under the current project decision. If it occurs immediately, describe it as an immediate within-researcher process check, not a delayed or blinded reassessment. Keep frozen Protocol v1.0 unchanged and record any timing deviation separately.
2. Approve this automation specification and the initial exact rule registry.
3. Generate a read-only proposal dry-run on a new stratified sample; manually review every suggestion and every abstention in the pilot.
4. Report rule-specific coverage, acceptance, corrections, rejection, abstention, error severity, and review time.
5. Only then decide whether limited auto-acceptance is justified. Until it is, final annotations require human review.

No model architecture dictates which records qualify. If the supported and manually reviewed subset is small, report the feasibility limit rather than weakening the inclusion or provenance rules.

## Related project artifacts

- [Frozen Protocol v1.0](../../data/2_interim/shamela4_narrator_audit/manual_annotation_working/PILOT_EVALUATION_AND_ANNOTATION_PROTOCOL_V1.md)
- [Round 1 working packet and case annotations](../../data/2_interim/shamela4_narrator_audit/manual_annotation_working/manual_collation_pilot_10_review_round_1_working/README.md)
- [Pass 1 freeze inventory](../../data/2_interim/shamela4_narrator_audit/manual_annotation_working/PILOT10_PASS1_FREEZE_INVENTORY.md)
- [Frozen Schema v2.2 final specification](MANUAL_COLLATION_SCHEMA_V2_2_FINAL.md)
- [Schema v2.2 details](MANUAL_COLLATION_SCHEMA_V2_2_SPEC.md)
- [Target feasibility report](TARGET_FEASIBILITY_REPORT.md)
