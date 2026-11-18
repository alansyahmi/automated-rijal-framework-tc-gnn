# Evaluative Statement Layer — Draft Codebook v0.1

**Date:** 2026-11-16
**Status:** proposed dimensions for a small annotation pilot; not frozen or validated.

## 1. Scope and boundary

Use this layer to describe a statement's evaluative content, domain, attribution form, and wording force. It is an additional statement-level description. It does not replace or modify Ibn Ḥajar's twelve-rank taxonomy, the existing target policy, the textual-boundary annotations, or the source-provenance workflow.

Keep four questions separate:

1. **What does the statement claim?** For example, praise, an accusation, a specific transmission criticism, or lack of biographical knowledge.
2. **What wording force does it use?** For example, qualified wording, a direct assessment, emphatic praise, or superlative praise.
3. **Who is said to make the claim, and does the text claim agreement?** Preserve the named attribution or collective wording.
4. **Does a separate, source-grounded rule assign one of the twelve canonical ranks?** This layer does not do so.

The unit is one distinct statement or claim span. Split clauses when they make distinct claims; preserve a grade's attached qualification and time scope in linked fields. Keep exact Arabic, punctuation, and surrounding context available. Do not silently normalize wording.

## 2. Proposed dimensions

### 2.1 `statement_family`

Choose the main function of the span:

- `praise`: an affirmative assessment of a narrator or an ability.
- `criticism`: an adverse assessment, allegation, or identified defect.
- `mixed`: a positive and adverse propositions occur together.
- `unknownness`: the statement reports lack of knowledge about identity, status, or condition. This is not automatically an adverse reliability grade.
- `status_or_biography`: Companion status, generation, lineage, date, affiliation, or other biographical information without a narrator-quality judgement.
- `non_evaluative_other`: another descriptive statement.
- `unresolved`: the span or its function cannot yet be determined.

Use `mixed` only when the statement itself contains both an assessment and a meaningful qualification. Do not use it merely because the researcher is unsure.

### 2.2 `statement_domain`

Record the subject of the claim. Suggested values:

- `general_reliability`
- `memory_precision`
- `honesty_veracity`
- `fabrication`
- `transmission_practice`
- `unknownness_or_majhul_status`
- `companion_status`
- `doctrinal_position`
- `jurisprudential_or_scholarly_merit`
- `biographical_information`
- `other`
- `unresolved`
- `not_applicable`

Use the closest supported domain and retain the source wording. Do not infer that a specific transmission criticism establishes a general reliability grade.

### 2.3 `claim_content`

Describe the proposition, not its truth:

- `general_commendation`
- `qualified_commendation`
- `superlative_commendation`
- `general_criticism`
- `accusation_of_lying`
- `applied_liar_label`
- `fabrication_label`
- `specific_transmission_criticism`
- `hadith_theft_or_appropriation`
- `unknownness_assertion`
- `status_assertion`
- `biographical_fact`
- `mixed_assessment`
- `other`
- `unresolved`
- `not_applicable`

Keep an attributed accusation such as `كذبه أبو زرعة` distinct from an applied description such as `كذاب` or `وضاع`. Keep `يسرق الحديث` in the transmission-practice family unless the source separately states lying or fabrication.

### 2.4 `claim_mode`

Record how the claim is presented:

- `direct_statement`
- `attributed_individual_judgement`
- `reported_or_hedged_claim`
- `specific_behavior_or_transmission_observation`
- `first_person_knowledge_gap`
- `status_or_biographical_statement`
- `unresolved`
- `not_applicable`

Preserve the exact attributed critic or uncertainty marker in separate text fields. Record collective-agreement language in consensus_wording, independently of claim_mode. A reported judgement is not automatically the compiler's own judgement.

### 2.5 `wording_force`

This is an ordinal description of the wording's rhetorical form, not a numeric score and not a measure of whether the claim is true:

- `qualified_limited`: hedged, temporally limited, or explicitly restricted wording.
- `plain_direct`: a direct, unmarked assessment or assertion.
- `emphatic`: wording explicitly intensifies or repeats an assessment.
- `superlative`: exceptional or highest-order praise/criticism in the words themselves.
- `unresolved`
- `not_applicable`

Do not treat these values as equal intervals. Do not infer `emphatic` merely from the seriousness of an allegation. Record the proposition type and attribution separately. A claim of consensus is also separate from wording force.

### 2.6 `consensus_wording`

Record what the span says about collective agreement:

- `none`
- `collective_agreement_claimed`
- `unanimity_wording_claimed`
- `scope_or_referents_unclear`
- `unresolved`
- `not_applicable`

This field captures the text's claim. For example, `اتفق النقاد` or `أجمعوا` can be recorded as collective/unanimity wording while the scope and supporting sources remain unverified. Do not convert consensus wording directly into calibrated model confidence or assume a historical consensus has been independently established.

### 2.7 Attribution, qualification, and reviewer confidence

Preserve these as separate fields:

- `attribution_text`: exact named critic, group, or other attribution in the source.
- `qualification_or_scope_text`: exact temporal, conditional, or limiting wording.
- `reviewer_confidence`: the annotator's confidence in this coding, not the statement's force, truth, or historical reliability.
- `reviewer_notes`: unresolved questions and source evidence.

## 3. Relationship to the twelve ranks

The canonical rank remains a separate label in the existing rank workflow. Rank 1 is Companion status and must remain distinct from ordinary reliability grades. A status cue such as `بدري` or `أم المؤمنين` can support a Rank 1 decision only when the phrase refers to the identified narrator and the status claim is established. It does not become a praise-intensity score.

An exact source-introduction example can be recorded as a phrase-level anchor. It is not an entry-level rank assignment by itself. In particular:

- A named critic's accusation is not automatically Ibn Ḥajar's adopted Rank 11 or Rank 12 judgement.
- An applied liar or fabricator label must remain distinguishable from an accusation that a named critic called someone a liar.
- Praise force, critic attribution, consensus wording, and reviewer confidence do not create extra ranks.
- This draft assigns no numeric value from 0.0 to 1.0.

## 4. Proposed columns for annotation

The blank template includes exact-span and source-context fields plus the dimensions above. Keep any existing statement ID and entry ID so annotations can be joined without changing frozen records. Do not populate the template from substring matches alone; inspect the full entry and resolve the span and referent first.

## 5. Examples requiring human review

The companion CSV contains illustrative AI proposals based on phrases raised in the discussion. These examples are not adjudicated annotations. In particular, `لا أعرفه`, `لا تعرف`, and similar forms, including "لا يعرف حاله", need referent and construction review before being described as *majhūl*; `لم أقف على اسمها ولا على حالها` is a knowledge-gap statement and remains low-confidence as a status inference. The example for `ثقة لكنه تغير بأخرة فلم يفحش اختلاطه` preserves the positive grade wording and temporal qualification instead of collapsing them.

## 6. Validation before use

Before using these dimensions in corpus annotation:

1. Review the proposed example rows against complete Taqrīb entries.
2. Revise definitions where a reviewer cannot apply a value consistently.
3. Annotate a small set manually and record disagreements by dimension.
4. Keep phrase-level interpretation separate from case-level attribution and canonical-rank decisions.
5. Only consider a numeric score in a later, separately validated design. The ordinal descriptors here do not establish numerical distances or a 0–1 mapping.

