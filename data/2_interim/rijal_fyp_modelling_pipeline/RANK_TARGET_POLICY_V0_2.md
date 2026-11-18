# Rank Target Policy v0.2

**Status:** current project policy for target construction and context annotation. It refines v0.1 by requiring potentially relevant notes to be preserved in a separate context layer.

## 1. Primary target

For this project, the target candidate is the rank of the first **complete grade-bearing phrase** in a Taqrīb entry. Apply this convention even if the phrase explicitly attributes the grade to an earlier critic, such as `صدوق عند النسائي`.

This is an operational target-selection assumption. It does not by itself prove that Ibn Ḥajar personally formulated or agreed with every attributed judgement. Preserve the exact attribution when it appears in the target phrase or elsewhere in the entry. In reporting, describe the outcome as a **Taqrīb first-grade proxy target**, not a historically verified statement of Ibn Ḥajar's personal agreement.

The target is the first complete evaluative unit, not the first matching word. Keep a modifier or qualification attached when the text makes it part of that unit. For example, do not cut `ثقة لكنه تغير بأخرة فلم يفحش اختلاطه` down to `ثقة` without recording the qualification and its possible effect on the rank.

## 2. Context-note layer

Do not discard notes merely because they are not separate rank labels. Preserve exact note text and record, at a broad level:

- `note_type`: examples include attached qualification, memory or transmission note, affiliation/innovation reference, attributed judgement, or biographical context;
- `relation_to_target`: `attached_qualifier`, `separate_context`, or `unclear`;
- `rank_relevance`: `potentially_rank_relevant`, `context_only`, or `unresolved`;
- `required_evidence`: any missing evidence needed by the twelve-rank definition.

These fields are contextual annotations, not extra target categories or scores. Detailed affiliation subtypes such as naṣb and tashayyuʿ are not separate prediction labels. Their exact wording remains in the source text, and a broad affiliation/innovation note can be recorded when it may affect rank interpretation.

## 3. Rank definition and evidence rules

- Use Ibn Ḥajar's original twelve categories only. Do not add, merge, or renumber ranks.
- Preserve the full first grade-bearing phrase and attached qualifiers. Later separate notes do not replace the primary target, but they may affect whether the target can be assigned confidently.
- Do not infer missing conditions. If a category requires corroboration, narrator counts, authentication history, a defect, innovation advocacy, or another fact not established by the text in scope, retain a conditional candidate or abstain until evidence is recorded.
- Keep explicit evaluator attribution, compiler wording, and target selection as separate metadata. The project convention does not resolve historical authorship.
- Treat ranks as categorical/ordinal classes. Do not assume equal numerical distances between rank numbers.
- Taqrīb-derived text and context annotations are for target construction and audit. They must not become Task B model features.

## 4. Review states

Use `candidate`, `conditional`, `unresolved`, or `abstain` while the phrase inventory is under review. AI consensus does not establish correctness. No candidate becomes an enabled rule or production label until its complete phrase, rank basis, note relationship, and required evidence have been checked.

This policy does not modify the frozen boundary annotations. It governs the next candidate-inventory and shadow-review stages.
