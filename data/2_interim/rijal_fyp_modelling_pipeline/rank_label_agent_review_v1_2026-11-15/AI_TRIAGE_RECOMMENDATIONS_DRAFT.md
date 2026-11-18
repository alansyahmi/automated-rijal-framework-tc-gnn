# AI triage recommendations for the 12 priority cases

**Status:** analyst draft based on the three blinded AI review files and the repository's v0 rank-source inventory. These are candidate interpretations, not approved labels, expert judgements, or production rules. No frozen annotation or source entry was changed.

## Case-by-case recommendations

| Case | Source text to consider | Conservative recommendation |
|---|---|---|
| ARV1-003 | `صدوق`; `خلط بعد احتراق كتبه` | Keep the explicit `صدوق` span as a Rank 4 candidate. Preserve the later mixing-after-book-loss statement separately as an unlisted possible Rank 5 memory issue. Do not force the whole entry into one rank. |
| ARV1-008 | `متروك الحديث`; `أفرط فيه ابن معين فكذبه` | `متروك الحديث` is a Rank 10 candidate, but the definition's no-authentication and defect conditions are not established by this entry. Keep `فكذبه` separate as an attributed earlier judgement; this wording alone does not settle Rank 11 versus Rank 12. |
| ARV1-012 | `ثقة متقنا`; `طعن فيه برأي جهم ثم اعتذر وتاب` | Treat `ثقة متقنا` as a definition-based Rank 2 candidate (combined praise), not an exact listed example. Keep the Jahm-related report separate; the wording records criticism and repentance, not that he advocated the innovation. |
| ARV1-018 | `ثقة فقيه عابد`; `رمي بالتشيع` | Keep the praise cluster as a possible Rank 2 candidate and the innovation report as a separate possible Rank 5 feature. `رمي بالتشيع` does not establish advocacy, so do not collapse the entry to a single rank. |
| ARV1-019 | `ثقة متقن` | Rank 2 is supported by the definition's combination-of-praise basis, though this exact compound is not the inventory's cited example. Record it as a candidate wording for review, not an enabled rule. |
| ARV1-020 | `ثقة ثبت` | Same treatment as ARV1-019: definition-based Rank 2 candidate; retain the exact span and require review before rule activation. |
| ARV1-034 | `ثقة`; `رمي بالنصب` | `ثقة` is a Rank 3 candidate on its own. Keep `رمي بالنصب` separate as a possible Rank 5 innovation feature; the wording does not establish whether he advocated it. |
| ARV1-041 | `تغير بأخرة فلم يفحش اختلاطه` | Rank 5 candidate from the listed late-change wording. Preserve the limiting qualification `فلم يفحش اختلاطه` in the same span. Do not use a bare substring rule until the effect of that qualification is resolved. |
| ARV1-045 | `صدوق يخطىء` | Rank 5 candidate. Preserve the corpus spelling `يخطىء`; do not normalize it to the inventory spelling `يخطئ`. This is a useful observed orthographic variant, not proof that fuzzy matching is safe. |
| ARV1-046 | `منكر الحديث` | Possible unlisted Rank 8 weakness wording. The entry does not establish the definition's lack-of-authentication condition, so keep the rank conditional and unassigned. |
| ARV1-048 | `لا يعرف حالها` | Unknown-status wording, but the entry alone does not distinguish Rank 7 from Rank 9: transmitter count and authentication evidence are missing. Abstain pending external evidence. |
| ARV1-053 | `متروك`; `وكذبه ابن معين` | `متروك` is a Rank 10 candidate with definition conditions still unverified. Keep `وكذبه ابن معين` separate and attributed; do not choose Rank 11 or 12 by majority vote. |

## What this tells us

1. Several cases need phrase-level or statement-level representation. A single entry can contain a standardized praise phrase, a separate memory observation, and an attributed earlier judgement.
2. Exact lexical matches can identify candidate spans, but they cannot establish external preconditions such as corroboration, transmitter counts, authentication history, or advocacy of an innovation.
3. The two Rank 10 / Rank 12 disagreements (ARV1-008 and ARV1-053) must remain unresolved in an automated system. The apparent agreement of two reviewers on Rank 10 does not cancel the separately attributed wording.
4. The no-cue controls surfaced useful unlisted candidates (`منكر الحديث`, `لا يعرف حالها`). Zero exact hits for the inventory's Rank 11 and Rank 12 examples therefore does not mean the corpus has no potentially relevant wording.

## Recommended next step

Build a versioned phrase-inventory table from these reviewed examples with separate evidence statuses: `explicit_source_example`, `definition_based_candidate`, `observed_unlisted_candidate`, `context_dependent`, and `unresolved`. Include exact Arabic spans, full-entry locators, rank candidate(s), conditions required, and whether the phrase is eligible for a later shadow rule. Keep all entries in candidate-only mode. Do not turn the 55/60 AI rank unanimity count into accuracy or corpus coverage; there is no independent gold set.

The user does not need to re-annotate all 60 cases. The 12-case queue is a focused review set. Cases whose definitions require external evidence should stay unresolved until that evidence is separately examined.
