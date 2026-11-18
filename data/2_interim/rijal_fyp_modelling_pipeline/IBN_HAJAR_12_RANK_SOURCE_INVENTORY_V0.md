# Ibn Ḥajar’s Twelve Ranks: Source Inventory v0

**Status:** edition-aligned digital-text working reference; not an approved automation dictionary

**Source checked:** 2026-11-14

## Purpose and boundary

This note records the structure and a small set of exact lexical anchors from Ibn Ḥajar’s introduction to *Taqrīb al-Tahdhīb*. The readings below follow a searchable Dorar.net text copy that identifies its basis as the Muḥammad ʿAwwāma / Dār al-Rashīd 1406 edition; Shamela’s book record identifies Dorar.net as its source. This aligns with the edition declared in the local dataset metadata. The local `pages.jsonl` extract still omits the opening rank introduction. The introduction gives definitions and examples; it does not claim that the examples below are every possible wording, nor that every occurrence of a listed expression determines a rank by itself.

The Dorar copy is not a scan of the printed 1406 edition. Alifta’s rank page is from a different edition and is retained only as a cross-edition comparator; see [the source comparison note](SHAMELA_ALIFTA_EDITION_AND_COVERAGE_CHECK.md).

Rank assignment must follow the stated definition and its conditions. Context-dependent cases should remain unresolved until the relevant evidence is checked. This document does not authorize new rank mappings, activate registry rules, establish target eligibility, or change any frozen annotation.

## The twelve ranks in the introduction

The Arabic anchors below are short examples copied from the source. Definitions are paraphrased. The examples are illustrative, not exhaustive.

| Rank | Ibn Ḥajar’s stated basis, summarized | Exact Arabic cue(s) shown in the introduction | Context needed before any rule could be proposed |
|---:|---|---|---|
| 1 | The Companions, identified separately because of their distinction. | `الصحابة` | Companion status is a biographical/status category, not an ordinary reliability grade. Do not infer it from a grade word. |
| 2 | Stronger praise, expressed by a superlative, literal repetition, or a combination of praise in meaning. | `أوثق الناس`; `ثقة ثقة`; `ثقة حافظ` | The construction and full span matter. A single praise word is not enough to infer rank 2. The source example `ثقة حافظ` does not automatically decide every other compound. |
| 3 | A single commendatory attribute. | `ثقة`; `متقن`; `ثبت`; `عدل` | Confirm that the complete statement is a standalone attribute rather than part of a compound phrase, quotation, negation, or other construction. |
| 4 | A description slightly below rank 3. | `صدوق`; `لا بأس به`; `ليس به بأس` | Interpret the complete wording and context; do not classify a substring inside a qualified statement as rank 4. |
| 5 | Slightly below rank 4; includes specified memory/error qualifications and kinds of innovation, with whether the person advocates it distinguished. | `صدوق سيء الحفظ`; `صدوق يهم`; `له أوهام`; `يخطئ`; `تغير بأخرة`; `التشيع`; `القدر`; `النصب`; `الإرجاء`; `التجهم` | Preserve the full qualification. For innovation, the introduction requires distinguishing its type and whether the person advocates it. These short cues are not sufficient by themselves to establish a complete rank-5 statement. Alifta’s separate edition reads `تغير بآخره`; do not normalize the difference. |
| 6 | A narrator with little hadith, with no established reason to abandon his hadith; `مقبول` is indicated where followed by corroboration, otherwise he is mild in hadith. | `مقبول`; `فلين الحديث` (in the definition’s conditional contrast) | The source explicitly makes the application of `مقبول` conditional on corroboration. Check the entry and corroboration context; never map by the word alone. |
| 7 | More than one person transmitted from the narrator, but the narrator was not authenticated. | `مستور`; `مجهول الحال` | Requires transmitter-count and authentication evidence; the label alone does not establish the definition’s conditions. |
| 8 | No authentication from a recognized authority was found, while a weakness description was found, even if unexplained. | `ضعيف` | Requires checking the authentication and weakness evidence in scope. Do not treat any occurrence as a rank label without resolving statement function and attribution. |
| 9 | Only one transmitter is known, and the narrator was not authenticated. | `مجهول` | Requires evidence for the one-transmitter condition and lack of authentication. Distinguish from the rank 7 condition. |
| 10 | No authentication, together with a defect that grounds weakness. | `متروك`; `متروك الحديث`; `واهي الحديث`; `ساقط` | Requires both parts of the definition. Check the complete statement and the defect; do not infer rank 10 from an isolated substring. |
| 11 | The narrator was accused of lying. | `اتهم بالكذب` (within `من اتهم بالكذب`) | Accusation is distinct from an unqualified declaration that the person lied. Resolve wording, attribution, and scope. |
| 12 | The terms lying or fabrication were applied to the narrator. | `أطلق عليه اسم الكذب والوضع` | Resolve the complete formulation and its attribution; distinguish accusation (rank 11) from an applied label (rank 12). |

## What this source supports

- Ibn Ḥajar presents twelve ordered categories and gives definitions and examples for them.
- Several categories depend on evidence outside a short lexical span, including corroboration, number of transmitters, authentication, a defect, or whether a person advocates an innovation.
- Rank 1 is Companion status and should remain distinct from ordinary narrator-reliability ranks.
- The introduction’s examples can seed a source-anchored vocabulary inventory, but they do not establish coverage of the local corpus or an exhaustive list of all expressions used in *Taqrīb*.
- The Dorar text’s rank-10 definition reads `وضعف مع ذلك بقدح`; Alifta’s separate edition reads `وضعف مع ذلك بقادح`. This is another textual variant to preserve during source collation.

## What remains to investigate in the local corpus

The next inventory step is to enumerate the exact complete assessment spans in the repository’s local *Taqrīb* text, preserve their original Arabic, and count their frequencies. Each span should be reviewed against this introduction and classified as one of:

1. an exact example explicitly listed by Ibn Ḥajar;
2. a candidate wording whose relationship to a rank needs human review;
3. context-dependent or structurally compound wording;
4. unresolved / abstain.

Only after that census and manual review should any additional exact-span rule be proposed. Report measured coverage on a defined, manually checked sample; do not assume a coverage percentage in advance. Longer phrases can be inspected before shorter overlapping terms, but exact span, context, and the definition’s preconditions still govern. Conflicts and unsupported cases should abstain.

## Edition-aligned digital text and cross-edition comparator

The searchable Dorar.net text copy (see [the source comparison note](SHAMELA_ALIFTA_EDITION_AND_COVERAGE_CHECK.md)) states that it relies on the Muḥammad ʿAwwāma, Dār al-Rashīd first edition, 1406 AH, and that differences from the Abū al-Ashbāl edition are bracketed. Shamela’s [official book record, ID 8609](https://shamela.ws/book/8609), likewise identifies the ʿAwwāma edition and names Dorar.net as its source. The archived text is not a scan of the printed edition.

Alifta’s official [book details](https://sunna.alifta.gov.sa/Book/Details?bookId=51) identify a different edition (Abū al-Ashbāl al-Pākistānī, Dār al-ʿĀṣimah, 1413 AH). Its [rank introduction](https://sunna.alifta.gov.sa/BookToc/ViewServicePage?bookId=51&mainId=506655) is useful for comparison, but its exact text should not be represented as the local ʿAwwāma edition without collation.

The comparison found these readings: rank 5 `تغير بأخرة` in the Dorar/ʿAwwāma text versus `تغير بآخره` in Alifta; rank 10 `بقدح` versus `بقادح`. Verify against a printed page image before describing either reading as visually checked in the 1406 edition.
