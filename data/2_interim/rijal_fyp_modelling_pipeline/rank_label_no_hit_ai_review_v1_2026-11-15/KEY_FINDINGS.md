# Key findings from the no-hit AI review

**Status:** provisional AI triage; no human-approved ranks or vocabulary rules.

## What the review covered

The v0.2 exact phrase inventory had no exact hit in 1,211 of the 8,827 numbered local entries. Three AI reviewers inspected disjoint batches. Every input entry is represented once in the consolidated file. The AI proposed a first-phrase candidate for 767 entries, a conditional result for 203, an unresolved result for 103, and no grade candidate for 138.

The suggestions include 701 Rank 1/Companion-status candidates. Other direct rank suggestions are limited: 60 Rank 3, 4 Rank 11, 2 Rank 2, and 1 Rank 4. The remaining 443 entries are conditional, unresolved, or marked not applicable. These are AI suggestions only. No accuracy, corpus-wide coverage, expert agreement, or production-label claim follows from these counts.

The review reduces the blank-entry inspection burden to a phrase-level index of 148 phrase strings, with provisional status/rank distributions and up to three full-entry examples for each phrase. Frequencies refer only to this no-hit review population. Grouping trims the `uncertain:` marker and surrounding whitespace; the row-level review file retains each extracted span.

The most frequent proposed wording is `صحابي` (504 entries), followed by `له صحبة` (28), `لا تعرف` (28), `صحابي مشهور` (25), `صحابية` (25), `فيه لين` (25), `لا يعرف` (24), and `مختلف في صحبته` (23). Some entries are uncertain or descriptive rather than ordinary grade phrases, so frequency does not mean rank correctness.

## Your three flagged examples

| Entry ID | Current treatment | What remains unresolved |
| --- | --- | --- |
| `S3076-P077-C012-E0009` | The AI found no narrator-grade target. It preserved `سماعه للموطأ صحيح` and `وخلط في غيره` as transmission/context notes. | Whether either note affects the target under the research policy. The target field remains blank pending human confirmation. |
| `S3076-P094-C006-E0252` | v0.2 now records exact `لين الحديث`; the full-corpus exact scan finds 115 occurrences. | Rank 6 is a candidate only. The source definition has conditions, and this entry also says `رفع موقوفات`; do not turn the phrase match into an unconditional rank. |
| `S3076-P094-C012-E0257` | v0.2 now records exact `كذبوه`; the full-corpus exact scan finds 15 occurrences. | Rank 11 accusation versus Rank 12 applied-lying wording remains a boundary question. The exact word is not an enabled rule. |

The compound `صدوق حافظ` is now a separate exact candidate found in four entries. The shorter overlapping `صدوق` occurrence remains in the occurrence table, while the compound is visible in the earliest-candidate summary. Its rank mapping remains unresolved; do not infer Rank 2 solely from the different source example `ثقة حافظ`.

## How to use the results

Start with [the sample-backed phrase review index](CONSOLIDATED_V1_3/AI_FIRST_PHRASE_REVIEW_INDEX.csv) instead of reading all 1,211 entries row by row. Check a phrase's example entries, exact wording, attached qualification, attribution, and the twelve-rank definition. Keep a phrase unresolved when the wording is specialized or when the definition requires evidence outside the entry. The [consolidated rows](CONSOLIDATED_V1_3/AI_REVIEW_ALL_1211.csv) retain every source entry and the complete AI rationale for deeper review.
