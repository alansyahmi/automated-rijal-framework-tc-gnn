# Manual Collation Pilot 10: Round 1 Working Copy

This mutable copy supports review of the frozen packet in `../manual_collation_pilot_10_review_round_1_blinded/`. The frozen packet and its manifest are unchanged. Its original README and manifest are retained here as `SOURCE_PACKET_README.md` and `SOURCE_PACKET_MANIFEST.json`.

## PROV-10-C01 identity

`candidate_entries.csv` records `identity_match_status=confirmed`, supported by `EVID-PROV-10-C01-ID01` from Ibn Saʿd, *al-Ṭabaqāt al-Kubrā*, vol. 5, p. 272. The identity rationale uses the matching name, lineage, Khazraj affiliation, and father-son relationship. It excludes the source's concluding evaluation. HadithDB's `بن أبي القين` and Ibn Saʿd's `بن أبي كعب بن القين` remain preserved as different textual forms; neither has been normalized. No grade provenance is inferred.

The reviewer reports inspecting the scan image and confirms the printed locator. The assistant checked the searchable text layer, but did not independently inspect the page image.

## PROV-10-C01 statement segmentation

The local Taqrīb corpus record is `book_id=3076`, `page_num=319`, `sequence_num=3552`; its body contains the candidate entry text. `sources.csv` marks this local transcription `verified_in_corpus`. The local `book_metadata.json` identifies Ibn Hajar as work author, Muhammad Awwama as editor, the Dar al-Rashid 1406/1986 edition, and says the numbering matches print. This is corpus metadata, not an independent inspection of the printed page image. Metadata is linked through `EVID-PROV-10-C01-TAQRIB-META01`.

The entry is segmented in `statements.csv` as:

| Statement | Text | Working classification |
| --- | --- | --- |
| `PROV-10-C01-S01` | `ثقة` | Standardized narrator grade |
| `PROV-10-C01-S02` | `يقال له رؤية` | Reported biographical claim concerning possible ruʾyah; `يقال` is retained and this is not treated as proof of Companion status |
| `PROV-10-C01-S03` | `مات سنة سبع أو ثمان وتسعين` | Biographical or factual statement |

Each row links to an exact Taqrīb corpus span and a separate `passage_text` evidence record. The death wording remains verbatim: no date has been normalized and no `date_claims.csv` record has been added. The trailing `خ م د س ق` symbols remain in the full entry transcription; they have not been expanded or interpreted as statements.

## Attribution and provenance status

The grade passage names no evaluator. That observation does **not** establish that Ibn Hajar formulated the assessment as his own synthesis, identify an earlier evaluator, or reveal a transmission route. The local metadata records Ibn Hajar as author of the work, but that work-level metadata is not copied into the passage-level wording-author field. For S01, `attribution_form`, historical evaluator attribution, transmission route, and compiler authorship remain unclear, unresolved, or not assessed in `attribution_links.csv`.

For S02, the phrase `يقال` signals anonymous reporting, but the entry does not identify its source or route; no conclusion about Companion status is made. For S03, the entry gives a death report without naming its source. These fields remain unresolved or not assessed; no provenance is supplied by the database attachment. Taqrīb's exact wording and correspondence do not establish the historical source of any statement.

No target scope, historical-input eligibility, corroboration, narrator reliability, or graph/model decision is made here. This is an AI-assisted, single-reviewer feasibility working copy for the user's review, not independent scholarly validation or an inter-reviewer agreement result.

## Review limitation

Grade fields were visible in the source packet before the identity decision was recorded. The identity rationale used biographical evidence and excluded the grade, but this is not a genuinely grade-blind pass. The work remains a single-reviewer feasibility exercise.
