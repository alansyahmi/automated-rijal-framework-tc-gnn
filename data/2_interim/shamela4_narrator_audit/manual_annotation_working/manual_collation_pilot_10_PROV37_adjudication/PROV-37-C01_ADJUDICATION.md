# PROV-37-C01 post-first-pass adjudication

## Decision summary

| Item | Decision |
|---|---|
| Dataset record | Shamela4 narrator `1740`, `خالد بن عبد الرحمن بن بكير` |
| Dataset field | `صدوق يخطئ.` in `biography_json["summary"]["الرتبة عند ابن حجر"]` |
| Candidate | Taqrib entry 1650, corpus page 189 |
| Identity | Confirmed from lineage, kunya, nisbah, and biographical cross-check |
| Candidate-field correspondence | `minor_variation`; both source forms are preserved |
| Frozen Pass 1 | S01 has a blank rank and `rank_status=unranked` |
| Separate adjudication | Rank 5 |

## 1. Candidate and identity resolution

The local Taqrib transcription gives entry 1650 as:

> ١٦٥٠- خالد ابن عبد الرحمن ابن بكير السلمي أبو أمية البصري صدوق يخطىء من الثامنة خ ت س

The dataset record provides the same full lineage. Its summary also gives `أبو أمية`, `السلمي، البصري`, and `الثامنة`; Taqrib entry 1650 gives the same identifiers and `من الثامنة`. Al-Mizzi's *Tahdhib al-Kamal*, vol. 8, p. 119, entry 1628, also records `خالد بن عبد الرحمن بن بكير السلمي`, `أبو أمية`, and the Basran identification.

The adjacent Taqrib entry 1652 is `خالد ابن عبد الرحمن ابن خالد ابن سلمة المخزومي المكي`, with different lineage, affiliation, and generation. It is not the candidate. The grade was not used to establish identity. The identifier match is strong, but it does not establish that the dataset field was copied from Taqrib or that the sources are literarily independent.

## 2. Statement segmentation

1. `PROV-37-C01-S01`: `صدوق يخطىء`, a standardized narrator grade with base `صدوق` and qualification `يخطىء`. The source span differs from the dataset field `صدوق يخطئ.` in hamza spelling and terminal punctuation.
2. `PROV-37-C01-S02`: `من الثامنة`, a generational classification, recorded separately from the grade.

S01 remains unranked in Pass 1. S02 has `rank_status=not_applicable`.

## 3. Attribution boundary

The Taqrib entry does not name a narrator-specific earlier evaluator or transmission route. Taqrib is authored by Ibn Hajar according to its bibliographic metadata, but that work-level authorship does not establish the historical source or derivation of this particular formula. The evaluator attribution and transmission route therefore remain unresolved or not assessed.

## 4. Rank adjudication

The separate Rank 5 mapping uses the same Taqrib introduction text documented in the approved PROV-56 adjudication. Its fifth-rank definition includes formulations such as `صدوق يخطئ`. The printed page image was not independently inspected. This is a post-first-pass taxonomy mapping; it does not alter the blank Pass 1 rank.

Rank 5 is a qualitative category below Rank 4, characterized by qualifications such as weak retention, occasional error, or later-life deterioration. It should not be interpreted as a uniform numerical interval on a scalar reliability scale.

## 5. Historical reports and source limits

Al-Mizzi's *Tahdhib al-Kamal* entry reports Abu Hatim as saying `صدوق لا بأس به`, and says Ibn Hibban included the narrator in *al-Thiqat* with the wording `يخطئ`. Its footnote also records al-Uqayli's `يخالف في حديثه`, a report through al-Hakim of Abu al-Hasan saying `لا بأس به`, and Abu Zur'a's `لا أحدث عنه` as cited through al-Baji. These are reports preserved by al-Mizzi; the cited works were not all independently inspected.

The local transcription of Ibn Abi Hatim's *al-Jarh wa al-ta'dil*, entry 1539, states that the compiler heard his father Abu Hatim discuss the narrator and that Abu Hatim said `لا بأس به`. The direct local wording does not include `صدوق`, which appears in al-Mizzi's summary. This difference is preserved. The distinct phrases `يخطئ`, `يخالف في حديثه`, `لا بأس به`, and `لا أحدث عنه` are not collapsed into one meaning. No precise relationship between any of these reports and Ibn Hajar's later formula has been established.

## 6. Remaining limits

- The dataset-to-Taqrib source route and any literary dependence remain unresolved.
- The local Thiqāt, al-Uqayli, Daraqutni, and al-Baji reports cited by al-Mizzi were not independently verified against those works.
- Printed pages were not inspected.
