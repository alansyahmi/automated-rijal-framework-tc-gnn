# Evaluative Statement Layer: Codebook v0.2 (Pilot-Revised)

**Date:** 2026-11-16
**Status:** revised from Draft v0.1 after single-reviewer 16-entry pilot (`REVIEW_SET.xlsx`) and 916-case Batch 01+02 consolidation. Separate from the 12 canonical Taqrīb ranks; assigns zero ranks and zero numeric 0-1 scores.

## 1. Scope and Boundary

Describe a statement's evaluative family, domain(s), proposition content, presentation mode, wording force, and consensus wording while keeping the twelve canonical Taqrīb ranks, target policy v0.2, and Task B historical inputs strictly separate.

## 2. Dimensions and Pilot-Approved Rules (v0.1 -> v0.2 Revisions)

### 2.1 `statement_family`
Allowed values: `praise`, `criticism`, `mixed`, `unknownness`, `status_or_biography`, `non_evaluative_other`, `unresolved`, `not_applicable` (for unrelated substrings).

### 2.2 `statement_domain` (Revised: Multi-Domain Syntax Enabled)
Allowed single values: `general_reliability`, `memory_precision`, `honesty_veracity`, `fabrication`, `transmission_practice`, `unknownness_or_majhul_status`, `companion_status`, `doctrinal_position`, `jurisprudential_or_scholarly_merit`, `biographical_information`, `other`, `unresolved`, `not_applicable`.

- **v0.2 Revision (`PILOT-03`, `PILOT-11`, `PILOT-16`):** When a single phrase spans multiple distinct domains (e.g., `ثقة حافظ`, `صدوق حافظ`, `ثقة فقيه عابد`, `جبل الحفظ وإمام الدنيا في فقه الحديث`), encode semicolon-separated domains in order of appearance (e.g., `general_reliability;memory_precision` or `memory_precision;jurisprudential_or_scholarly_merit`) rather than forcing `unresolved`. For route-restricted praise (`لا بأس بحديثه من رواية ابنه...`), use `transmission_practice` (or `general_reliability;transmission_practice`).

### 2.3 `claim_content`
Allowed values: `general_commendation`, `qualified_commendation`, `superlative_commendation`, `general_criticism`, `accusation_of_lying`, `applied_liar_label`, `fabrication_label`, `specific_transmission_criticism`, `hadith_theft_or_appropriation`, `unknownness_assertion`, `status_assertion`, `biographical_fact`, `mixed_assessment`, `other`, `unresolved`, `not_applicable`.

### 2.4 `claim_mode` (Revised: Deterministic Precedence Rules)
Allowed values: `direct_statement`, `attributed_individual_judgement`, `reported_or_hedged_claim`, `specific_behavior_or_transmission_observation`, `first_person_knowledge_gap`, `status_or_biographical_statement`, `unresolved`, `not_applicable`.

- **v0.2 Precedence Rule (`PILOT-10`, `PILOT-12`, `PILOT-15`):**
  1. If a span is explicitly quoted from or attributed to a named critic (`قال ابن عبد البر أجمعوا...`, `قال النسائي: لا أعرفه`, `قال الخليلي يسرق الحديث`), record the named critic in `attribution_text` and prefer `attributed_individual_judgement` (or `reported_or_hedged_claim` when hedging/collective reporting is the primary framing, such as `قال ابن عبد البر أجمعوا...`).
  2. Use `first_person_knowledge_gap` when the first-person compiler voice is unattributed (`لم أقف على اسمها ولا على حالها`).
  3. Capture specific transmission actions (`يسرق الحديث`, `حدث عن أبيه بغير سماع`) in `statement_domain = transmission_practice` and `claim_content` (`hadith_theft_or_appropriation` / `specific_transmission_criticism`) without erasing named attribution.

### 2.5 `wording_force` (Revised: Multi-Attribute Compounds)
Allowed values: `qualified_limited`, `plain_direct`, `emphatic`, `superlative`, `unresolved`, `not_applicable`.

- **v0.2 Revision (`PILOT-03`, `PILOT-04`):** Standard multi-attribute compounds (`ثقة ثبت`, `ثقة حافظ`, `ثقة متقن`) take `plain_direct` rather than `unresolved`. Reserve `emphatic` for literal repetition (`ثقة ثقة`) or explicit grammatical intensifiers, and `superlative` for exceptional/superlative formulations (`جبل الحفظ`, `رأس المتقنين`, `أوثق الناس`).

### 2.6 `consensus_wording`
Allowed values: `none`, `collective_agreement_claimed`, `unanimity_wording_claimed`, `scope_or_referents_unclear`, `unresolved`, `not_applicable`. Records only what the text claims, never verified historical consensus or calibrated confidence.

## 3. Newly Documented Span and Context Guardrails (Consolidated v0.1)

- Always enforce non-Arabic-letter boundaries or verify token expansion (`بدري` vs. `العبدري`, `ثبت` vs. `يثبت`/`أثبت`).
- Separate referent checks (`أم المؤمنين`, `الصحابة`, `أحد العشرة`, `صحابي معروف`, `لا تعرف` referring to relatives/chain figures vs. the entry subject).
- Track newly surfaced verbatim forms for future vocabulary collation without enabling rank rules: `صحابية مشهورة`, `وثقه يعقوب ابن سفيان`, governed doctrinal clauses (`رمي بالإرجاء`, `رمي بالقدر`, `يرى القدر`, `رمي بالتشيع`, `رمي بالنصب`), `متروك الحديث عن الزهري`, `فصار كتابه أثبت من حفظه`, `رأس المتقنين`, `من شيوخ بقية المجهولين`, `فلم يشهد بدرا`, `يقال له صحبة والا فمجهول`, and `ثقة ثبت حجة`.
