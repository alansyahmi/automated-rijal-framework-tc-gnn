# Pilot Evaluation and Annotation Protocol v1.0

**Status:** Research protocol for a single-reviewer feasibility pilot
**Schema baseline:** Manual Collation Schema v2.2
**Prepared:** 2026-11-14
**Scope:** Ten purposively selected narrator records in the Round 1 pilot

## 1. Purpose and decision

This document evaluates what the ten-record manual-collation pilot has shown about the usability of the annotation process and sets out an operational protocol for future records. It is a research document, not a new data migration or schema version. Schema v2.2 remains the data-structure baseline; this protocol clarifies how to use it and how to preserve uncertainty.

The pilot supports a limited conclusion: a single researcher, with AI used as research assistance, can organize a small set of records into candidate entries, distinct statements, source evidence, attribution links, and explicit unresolved decisions. The cases also show that this work requires choices that cannot safely be made from a database row or grade string alone.

The pilot does **not** establish expert validity, inter-annotator reliability, narrator reliability, the historical accuracy of a reported judgement, the independence of sources, or a sufficient number of model targets. No case in the current working table has been cleared as an eligible supervised target. Do not build the narrator graph, assign reliability outcomes, or train a model on the basis of this pilot.

## 2. Evidence base and accounting

The counts below were checked against the Round 1 working CSVs and the pass-one freeze inventory. The current working-copy manifest records SHA-256 `8432809d989992503ad2935ec2fc04e5707afccc92b30142e6d61cbdb1b9bc1a`.

| Measure | Current accounting | Interpretation |
| --- | ---: | --- |
| Original cases | 10 | Ten source records in the purposive pilot. |
| Candidate entries | 11 | PROV-04 has two candidates for one source record. |
| Substantive reviewed statements | 34 | Statement rows with `reviewed_statement` status. |
| Superseded placeholders | 3 | S00 rows for PROV-01, PROV-24, and PROV-51; excluded from statement totals. |
| Contemporaneous Pass 1 snapshots | 7 | PROV-10, PROV-56, PROV-24, PROV-51, PROV-01, PROV-02, and PROV-04. |
| Missing or unrecoverable Pass 1 snapshots | 3 | PROV-37, PROV-39, and PROV-40. Their later annotation and adjudication records remain available. |
| Separate rank adjudications | 5 | PROV-10 (rank 3), PROV-40 (rank 3), PROV-39 (rank 5), PROV-56 (rank 5), and PROV-37 (rank 5). These do not rewrite Pass 1. |

### Case-by-case inventory

| Case | Candidate entries | Reviewed statements | Pass 1 snapshot | Main annotation issue and current boundary |
| --- | ---: | ---: | --- | --- |
| PROV-10 | 1 | 3 | Recoverable | `ثقة`, reported ruʾyah, and death date are separate. Rank 3 was added later in a separate taxonomy adjudication; attribution and target scope remain open. |
| PROV-40 | 1 | 3 | Missing/unrecoverable | `ثقة`, generation, and death/longevity are distinct. Rank 3 is separately adjudicated; the available biography is related to al-Mizzī and is not independent corroboration. |
| PROV-39 | 1 | 5 | Missing/unrecoverable | A qualified grade, disputed sighting claim, criticism of that sighting attributed to Ibn ʿUyaynah and Aḥmad, generation, and death are distinct. Rank 5 is a later taxonomy adjudication. |
| PROV-56 | 1 | 2 | Recoverable | The grade `صدوق يخطىء` is kept with its qualification; the generation is separate. Dataset spelling/punctuation differs slightly. Rank 5 is a later taxonomy adjudication. |
| PROV-24 | 1 | 2 | Recoverable | `وثقه النسائي` is an explicitly reported earlier-critic judgement, while `من الثالثة` is a generation. Historical verification, route, and printed-page locator remain unresolved. |
| PROV-51 | 1 | 2 | Recoverable | The specific no-audition criticism `عابوا عليه` does not identify its collective; `من العاشرة` is separate. Related Abū Ḥātim/Abū Dāwūd reports are not substituted for that collective. |
| PROV-01 | 1 | 5 | Recoverable | Companion status, parentage, campaign history, death, and age are separate. `صحابي` is status-only, not an ordinary reliability grade; source dependence and locators remain open. |
| PROV-02 | 1 | 4 | Recoverable | One qualified assessment is kept intact with teacher/Basra limitations; generation, death, and age are separate. A bracketed Asim phrase remains a textual issue, not an established editorial or historical claim. |
| PROV-04 | 2 | 6 | Recoverable | C01 is the confirmed candidate with `ثقة له أفراد`; C02 is a rejected homonym and remains in the audit record but outside target extraction. The qualification is preserved without forcing its meaning. |
| PROV-37 | 1 | 2 | Missing/unrecoverable | `صدوق يخطىء` and generation are separate; a nearby homonym was distinguished using non-grade identifiers. Rank 5 is a later taxonomy adjudication. |

The candidate and statement totals above sum to 11 and 34. The three S00 placeholders are separate superseded rows in PROV-01, PROV-24, and PROV-51; they are not the three cases with missing Pass 1 snapshots.

The 34 substantive statements comprise 6 `standardized_narrator_grade`, 2 `qualified_narrator_grade`, 1 `attributed_earlier_critic_judgment`, 2 `specific_transmission_criticism`, 8 `descriptive_or_generational_status`, and 15 `biographical_or_factual_statement` rows. These are nested within 11 candidate entries and ten source cases; they are not 34 independent observations.

Current `target_task_scope` values among the 34 substantive rows are: 17 `not_assessed`, 2 `unresolved`, 14 `not_in_defined_task`, and 1 `status_only_candidate`. Current `historical_input_eligibility` values are 20 `not_assessed` and 14 `not_applicable`. These are workflow statuses, not measured task feasibility. In particular, `not_assessed` is not a negative eligibility decision, and none of these counts is a count of confirmed training targets.

### Three separate dimensions of completion

1. **Annotation completion:** the current working table contains reviewed statement rows for all ten cases.
2. **Archival completeness:** contemporaneous Pass 1 snapshots are recoverable for seven cases. For PROV-37, PROV-39, and PROV-40, later adjudication manifests say Pass 1 was unchanged, but no pre-adjudication snapshot or source-table hashes establish the original contents. Those three snapshots remain missing and must not be reconstructed as if contemporaneous.
3. **Interpretive certainty:** individual identity, wording, attribution, provenance, and target decisions have different evidence limits. A complete snapshot does not resolve them; an unresolved interpretation does not mean the annotation failed.

Earlier project verification reports 72 passing unit tests; several case manifests also record a 72-test pass and case-scoped structural checks. This document did not rerun the suite. The PROV-02 and PROV-04 manifests record case-scoped checks but do not themselves record a fresh full-suite run. The strict package-wide validator has previously failed on a pre-existing PROV-10 source row with a blank `source_work_id`; the mutable packet also omits migration and legacy tables expected by that validator. Case-level success must not be reported as package-wide validation. See the [freeze inventory](PILOT10_PASS1_FREEZE_INVENTORY.md), the [working-copy README and case notes](manual_collation_pilot_10_review_round_1_working/README.md), and the case-specific freeze manifests.

There is a documentation-status mismatch to clean up separately: the case-freeze manifests and directories identify PROV-02 and PROV-04 as user-approved freezes, while the mutable working-copy README still labels their sections “working draft” and “not frozen.” For freeze status, this report follows the scope and approval recorded in each `CASE_FREEZE_MANIFEST.json`; the stale README wording should not be copied into future status summaries.

## 3. What the pilot demonstrated

### Decisions that were operationally straightforward

- Candidate matching is stronger when it uses several grade-independent identifiers, such as lineage, kunya, nisbah, geography, relationships, and chronology. The working table records ten confirmed candidates and one rejected PROV-04 homonym candidate. PROV-04-C02 remains in the audit record but is excluded from target extraction.
- Exact Arabic spans can be recorded separately from dataset-field correspondence. The candidate-level comparison records six exact correspondences, four minor variations, and one substantial difference associated with the rejected homonym. Orthographic differences and punctuation were preserved rather than silently normalized.
- Separating statements prevented generational, chronological, and biographical information from being mistaken for reliability grades. The five claims in PROV-01, for example, keep Companion status, parentage, campaign history, death, and age distinct.
- The statement model can retain a base grade and its qualification together when they form one assessment. PROV-02 keeps `ثقة ثبت فاضل` and its teacher/Basra qualification in one qualified-grade statement; PROV-39 and PROV-56 preserve late-life change or error qualifications rather than reducing them to an unqualified base grade.
- A candidate identity decision can be supported without relying on the grade under review. The PROV-10, PROV-02, and PROV-04 records document grade-free identity evidence and retain lineage or name-form differences.

These are workflow observations from this selected set, not evidence that every case can be resolved this way.

### Decisions requiring interpretation

- Whether a phrase is a grade, a qualified grade, a factual claim, a generational label, a report of an earlier critic, or a specific transmission criticism.
- Whether to preserve multiple clauses as one qualified assessment or split them into distinct claims. The decision must follow the claim's meaning, not a fixed punctuation rule.
- Whether a criticism is limited to a particular report or transmission context. PROV-39's criticism by Ibn ʿUyaynah and Aḥmad concerns the narrator's claimed sighting of ʿAmr ibn Ḥurayth; it is not a blanket rejection of his narrator reliability. PROV-51's `عابوا عليه` identifies an unnamed collective and a specific audition issue, not a standardized general grade.
- How to represent Companion status. PROV-01's `صحابي` is a status classification and at most a status-only task candidate; it is not an ordinary narrator-reliability grade. Likewise, `من الثالثة`, `من العاشرة`, and similar phrases denote generations, not reliability ranks.
- Whether contextual earlier reports corroborate a Taqrīb statement and whether their routes are independent. Textual similarity or appearance in multiple compilations does not establish independence or provenance.

### Questions the available evidence did not resolve

Several records retain unresolved or not-assessed fields for legitimate reasons:

- A named evaluator in Taqrīb establishes what the consulted passage reports, but does not by itself establish a historically verified attribution or a traceable route. PROV-24 names al-Nasāʾī, while the source of the exact report and its route remain unresolved.
- An unnamed collective in PROV-51 cannot be equated with Abū Ḥātim or Abū Dāwūd merely because related reports occur in earlier or later works.
- No named evaluator does not prove that Ibn Ḥajar formulated a new synthesis. Conversely, naming an earlier critic does not prove the whole sentence is a verbatim quotation.
- Work-level authorship by Ibn Ḥajar does not establish passage-level wording authorship or the historical origin of each assessment.
- Local digital corpus text and metadata support transcription and a corpus locator. They do not automatically establish the printed edition's page, the absence of editorial intervention, or direct consultation of an earlier cited work. The case files explicitly retain cases where printed page images were not inspected and where HadithDB and local corpus locators differ.
- Related evidence can support identity or textual correspondence without being independent corroboration. For example, dependence between Taqrīb and al-Mizzī's compilation is a live consideration in several cases.
- PROV-02's bracketed Asim phrase is retained as a textual/editorial issue. Its presence alone does not identify who added it or establish an independent historical statement.

## 4. Operational protocol v1.0

Use this workflow in order. Preserve prior states; do not write a later interpretation back into an earlier pass.

### Step 1: Open a case and establish the source record

Record the source dataset and exact record ID, the original narrator name and grade field, the raw value, and its original location. Preserve the source record verbatim. Do not normalize Arabic, remove punctuation, or treat database field names as scholarly semantics.

Treat a **case** as the source record under review. A **candidate entry** is a possible matching Taqrīb entry. A case may have multiple candidates. A **statement** is one distinct claim in a candidate entry, whether evaluative or factual. These units are linked but are not interchangeable.

### Step 2: Resolve candidate identity without grade evidence

Compare grade-independent identifiers: full lineage, kunya, nisbah, relationships, geography, chronology, and other explicit biographical details. Record the exact evidence and locator. Do not use the grade, rank, or evaluative claim as an identity key.

- Use `confirmed` only when the non-grade evidence adequately supports the match under the frozen schema.
- Use `probable` only when evidence is strong but falls short of the confirmation rule.
- Use `unresolved` when candidates cannot be distinguished with the available evidence.
- Use `mismatch` for a candidate positively identified as a different person; retain that rejected candidate and its evidence in the audit trail.

Preserve different lineage and name forms as variants. Do not label a difference a contradiction unless the evidence warrants that conclusion. If two candidates remain plausible, keep both; never choose one because its grade resembles the dataset value.

### Step 3: Collate the source text

Transcribe the full relevant entry and the exact span corresponding to the original dataset field. Record the work, edition or corpus artifact, locator, and the kind of verification actually performed.

Use correspondence values to describe the text comparison only. Exact or near-exact wording does not prove the dataset's extraction route, the historical evaluator, or the truth of the claim. Keep dataset-field correspondence separate from statement-to-passage correspondence. Preserve differences in spelling, punctuation, omitted words, brackets, and page citations; explain them rather than harmonizing them.

If the checked source is a local searchable corpus, say so. Do not describe the text as verified against a printed page image unless that image was inspected. Record unresolved pagination differences without choosing a preferred citation by assumption.

### Step 4: Segment claims

Create one statement row for each distinct claim. Use the exact Arabic wording, with a linked source span and evidence record.

- Keep a grade and its meaningful qualification together when the qualification modifies that grade: for example, `صدوق` plus `يخطئ` or `اختلط في الآخر`.
- Record a separate statement for an unrelated generational label, death date, age, parentage, or other biographical fact.
- Record a specifically described transmission problem as a specific criticism, not as a generic weak/unreliable label, unless the source itself makes that broader claim.
- Record a judgement explicitly attributed to an earlier critic as an attributed judgement. Do not turn it into Ibn Ḥajar's own grade or into a verified historical report without separate evidence.
- Preserve disputed or reported wording such as `يقال` and `ادعى`; do not convert a report or allegation into an unqualified fact.
- Keep full-entry symbols or abbreviations in the transcription. Expand them only when the annotation question requires it and a source supports the expansion.

If the boundary between two claims is uncertain, preserve the full phrase, describe the competing segmentation in notes, and leave the decision unresolved pending review. Do not split solely to increase row counts or merge solely to simplify the dataset.

### Step 5: Record voice and attribution as separate questions

For each relevant statement, distinguish:

1. **Work author/compiler:** the person identified as responsible for the source work as a whole.
2. **Surviving wording author:** the person supported as responsible for this passage's wording.
3. **Passage evaluator naming:** whether the passage names an evaluator, names a collective, or names none.
4. **Historical evaluator attribution:** whether historical evidence supports the claimed evaluator.
5. **Intermediary transmitter:** a person or source in an evidenced route between evaluator and surviving wording.
6. **Transmission route:** whether the path into the surviving passage is documented.

Do not copy the work author into passage-level authorship. Do not infer compiler synthesis from silence about an earlier evaluator. Do not infer verbatim quotation from a named evaluator. A person named in the passage may be recorded as passage-named while historical attribution and route remain `unresolved` or otherwise appropriately qualified. Keep contextual reports separate from the Taqrīb statement unless a direct relationship is evidenced.

For intermediary-preserved reports, record the compiler or transmitter as the preserver of the consulted report when supported; keep the historically attributed evaluator and route in their own fields. A chain of citations is not a proven chain of transmission unless each link is evidenced.

### Step 6: Keep taxonomy rank, target scope, and historical-input eligibility separate

Preserve the first-pass rank decision as made. If a later mapping to Ibn Ḥajar's taxonomy is supported, add a separately dated and sourced adjudication; do not change the frozen first-pass row. Cite the exact introductory rule and record the category's meaning.

Rank is a taxonomy classification, not automatically a scalar measure. Rank 1/Companion status must remain distinct from ordinary reliability-grade targets. Generational tier numbers must never be entered as reliability ranks. A rank mapping does not establish historical provenance, target suitability, or narrator truth.

Decide target scope only against a written, pre-specified task definition. Decide historical-input eligibility separately, based on the evidence allowed for inputs and the temporal/provenance rules. A Taqrīb match or an earlier-source quotation is not automatically a target or eligible input. Leave these decisions `not_assessed` until they have actually been evaluated; use `unresolved` when evidence was examined but remains inconclusive.

### Step 7: Record evidence, corroboration, and uncertainty

Link source evidence to the case, candidate, statement, or attribution that it supports. Preserve the exact excerpt, source locator, and evidence role. Contextual evidence does not automatically support every statement in an entry.

Distinguish textual support from independent corroboration. Use independent/dependent corroboration only when the source relationship is examined and justified; otherwise leave it unresolved. The current schema lacks a dedicated corroboration evidence role. Where a statement-specific supporting excerpt must be linked using `other`, explain its exact function in that case. Do not redefine `other` as a general corroboration label. Do not force a schema workaround if the intended evidence relationship cannot be represented honestly; log the limitation instead.

Apply missingness statuses consistently:

- `not_assessed`: the question has not been examined.
- `unknown`: examination did not establish the factual value.
- `unresolved`: evidence was examined but is ambiguous or conflicting.
- `not_applicable`: the question does not apply to this statement.
- A blank/null source value is not itself a decision and must not be treated as a positive result.

When evidence is insufficient, record what was checked, what remains missing, and what conclusion is therefore withheld. Do not turn unresolved into an error or force a best guess.

### Step 8: Freeze and adjudicate with separate records

Before freezing, check identity evidence, statement boundaries, verbatim text, source links/locators, attribution roles, enum values, candidate/statement relationships, and whether any old annotation has leaked into the first pass. Freeze only the case or candidate scope explicitly approved. Record input and output hashes and the validation scope.

Use a separate adjudication file for later taxonomy mapping or other post-first-pass decisions. It must cite its evidence, preserve the prior snapshot, say which fields it changes or leaves open, and carry its own hash. Never construct a retrospective freeze from a later working copy when the contemporaneous snapshot is missing.

## 5. Ambiguous cases and disagreement handling

Treat a case as ambiguous when one or more of these conditions holds:

- Identity depends on the disputed grade, or grade-free evidence does not distinguish homonyms.
- Source wording or locator differs in a way that could change the interpretation and the difference cannot be resolved.
- It is unclear whether the text is a grade, a qualified grade, a factual/status claim, an attributed report, or a specific criticism.
- The subject, evaluator, wording author, transmitter, or transmission route cannot be established separately.
- Multiple source accounts appear similar, but dependence or independence is unproven.
- A target or historical-input eligibility decision would require assumptions not supported by cited evidence.
- A textual variant or editorial intervention is suspected but the consulted witness or apparatus cannot establish it.

For this single-reviewer pilot, record the initial decision, evidence, uncertainty, and exact question that remains open. Do not create AI-generated agreement or treat AI review as an independent annotator. AI may help locate texts, compare passages, summarize alternatives, and challenge contradictions; the researcher remains responsible for the annotation and must document when AI suggestions influenced a decision.

If a second human reviewer becomes available later, both reviewers should annotate the same versioned input independently before seeing each other's decisions. Preserve both versions. Compare disagreements field by field, document evidence and rationale, and use a third qualified reviewer for adjudication where available. Keep the pre-adjudication choices and adjudication record; do not silently overwrite either reviewer.

## 6. Single-annotator consistency reassessment

Before expanding the sample, conduct a delayed repeat annotation on a small, varied subset drawn from recoverable snapshots. A practical starting subset is six cases covering an unqualified grade (PROV-10), a compound qualification (PROV-02), an attributed earlier judgement (PROV-24), status-only material (PROV-01), a specific transmission criticism (PROV-51), and a two-candidate homonym decision (PROV-04). This is a proposed diagnostic subset, not a new sampling claim.

After a delay of roughly two to four weeks, prepare a clean reviewer copy with the previous annotation values, adjudications, and case-order cues hidden. The researcher has already encountered these records, so this cannot be described as fully blinded; record that familiarity as a limitation. Do not ask AI to propose labels before the researcher completes the repeat pass. AI can be used afterward to check source retrieval or identify contradictions, with its contribution logged.

Compare the repeated decisions against the first pass for identity, segmentation, statement type, base/qualification, exact source correspondence, attribution components, rank taxonomy, target scope, historical-input eligibility, and uncertainty status. For each changed decision, record whether the change came from new evidence, clarified rules, a transcription correction, memory/attention, or a still-open disagreement. Investigate the reasons rather than relying on one aggregate agreement percentage. This exercise measures within-researcher operational consistency only; it does not establish expert validity or inter-annotator reliability.

## 7. Target feasibility and dataset implications

The current 34-statement inventory contains eight grade-form statements (six standardized and two qualified), one attributed earlier-critic judgement, two specific transmission criticisms, eight generational/status statements, and fifteen factual/biographical statements. These numbers describe annotation types in a purposive ten-case pilot. They do not estimate corpus-wide prevalence, independent judgements, or final target counts.

After protocol stability and repeat assessment, conduct a separate target-feasibility pass. Count unique candidate statements, not source cases or database rows, and report the denominator and exclusions. At minimum, separate:

- ordinary standardized or qualified narrator-grade candidates;
- compound/qualified grades whose taxonomy mapping or task scope remains unresolved;
- attributed earlier-critic reports, which may be outside a task predicting Taqrīb's classification;
- status-only records such as Companion status;
- descriptive, generational, and biographical statements;
- specific transmission criticisms;
- identity mismatches and unresolved identities;
- records with missing provenance or insufficient source support.

Do not count placeholders, rejected homonyms, or multiple statements from one entry as independent narrator cases. Do not count historical evidence as independent inputs merely because it appears in a different compilation. Report target-task eligibility and historical-input eligibility as separate filters with separate denominators. The current statuses show that feasibility is not yet established: 17 statements have target scope not assessed, two are unresolved, one is status-only, and no row is cleared as a supervised target.

### Proposed task framing for later study

If the feasibility study supports proceeding, the task may be framed as:

> Given eligible historical textual and relational evidence about a narrator, can a computational framework reproduce Ibn Ḥajar's narrator classification in *Taqrīb al-Tahdhīb*?

This is a proposal, not a settled model specification. It predicts a compiler's taxonomy as documented in a source; it does not claim to determine historical truth or narrator reliability independently. Only after eligible cases and leakage controls are established should text-only, relation-only, and combined systems be compared. AraBERT and a GNN are possible later components, not findings from this pilot.

## 8. Next-stage decision

Do not expand data collection yet. First:

1. Preserve the seven contemporaneous snapshots and the three missing-snapshot classifications without retrospective reconstruction.
2. Keep the five rank mappings in their separate adjudication records and keep Pass 1 unchanged.
3. Complete the delayed within-researcher consistency reassessment using the protocol above.
4. Resolve only documentation or validation defects that block a transparent record; do not modify historical annotations to make package-wide checks appear clean.
5. Reassess whether the target and provenance rules are usable, then produce a denominator-based target-feasibility report.
6. Seek an Arabic-trained subject specialist before making expert-validity claims or scaling consequential annotation. Until then, label the work single-researcher, AI-assisted feasibility research.

Expansion is justified only if the repeat assessment shows that the rules can be applied consistently enough for the intended research question, the source and identity evidence can be collected at acceptable cost, the eligible target pool is adequate, and unresolved cases can remain explicitly unresolved without being forced into labels.

## 9. Record status and related artifacts

This protocol does not change Schema v2.2, any CSV annotation, any freeze package, rank adjudication, source value, or model input. It records an operational interpretation of the current pilot and identifies limits for the next phase.

- [Pass 1 freeze inventory and recovery audit](PILOT10_PASS1_FREEZE_INVENTORY.md)
- [Round 1 working packet and case notes](manual_collation_pilot_10_review_round_1_working/README.md)
- [Frozen schema v2.2 specification](../../../../dataset_discovery/target_feasibility/MANUAL_COLLATION_SCHEMA_V2_2_SPEC.md)
- [Round 1 review guide](../../../../dataset_discovery/target_feasibility/MANUAL_COLLATION_PILOT_10_REVIEW_GUIDE.md)
- [PROV-10 separate rank adjudication](manual_collation_pilot_10_PROV10_adjudication/PROV-10-C01_ADJUDICATION.md)
- [PROV-37 separate rank adjudication](manual_collation_pilot_10_PROV37_adjudication/PROV-37-C01_ADJUDICATION.md)
- [PROV-39 separate rank adjudication](manual_collation_pilot_10_PROV39_adjudication/PROV-39-C01_ADJUDICATION.md)
- [PROV-40 separate rank adjudication](manual_collation_pilot_10_PROV40_adjudication/PROV-40-C01_ADJUDICATION.md)
- [PROV-56 separate rank adjudication](manual_collation_pilot_10_PROV56_adjudication/PROV-56-C01_ADJUDICATION.md)
