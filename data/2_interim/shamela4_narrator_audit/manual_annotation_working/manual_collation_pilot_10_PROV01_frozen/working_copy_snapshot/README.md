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


## PROV-40-C01 identity

`candidate_entries.csv` records `identity_match_status=confirmed`, supported by `EVID-PROV-40-C01-ID01` from al-Mizzi, *Tahdhib al-Kamal*, vol. 8, pp. 294-295, entry 1710. The identity rationale uses the matching full lineage (خلف بن محمد بن عيسى بن أبي عبد الله), kunyah (أبو الحسين, with alias أبو الحسن noted), occupational and regional nisbahs (الخشاب القافلاني الواسطي), sobriquet (كردوس), 11th tabaqah, canonical transmission symbol (Sunan Ibn Majah, ق), and precise death chronology (mid-Dhu al-Hijjah 274 AH at Wasit, aged >80). This decision uses convergent biographical details only, excluding the evaluative grade.

**Note on source dependence**: Because Ibn Hajar drew substantially upon al-Mizzi's *Tahdhib al-Kamal* in compiling *Taqrib al-Tahdhib*, this correspondence reflects literary compilation dependence rather than multiple independent historical attestations.

## PROV-40-C01 statement segmentation

The local Taqrib corpus record is `book_id=3076`, `page_num=194`, `sequence_num=1734`; its body contains the candidate entry text. `sources.csv` marks this local transcription `verified_in_corpus`.

The entry is segmented in `statements.csv` as:

| Statement | Text | Working classification |
| --- | --- | --- |
| `PROV-40-C01-S01` | `ثقة` | Standardized narrator grade |
| `PROV-40-C01-S02` | `من الحادية عشرة` | Biographical or generational classification |
| `PROV-40-C01-S03` | `مات سنة أربع وسبعين وله أكثر من ثمانين` | Biographical or chronological statement |

Each row links to an exact Taqrib corpus span and a separate `passage_text` evidence record.

## PROV-40-C01 attribution amendment and provenance status

The grade passage names no evaluator (`none_named`). That observation does **not** establish that Ibn Hajar formulated the assessment as his own synthesis, identify an earlier evaluator, or reveal a transmission route. Work-level metadata (`Ibn Hajar`) is preserved in `sources.csv`, but is not copied into the passage-level wording-author field. For S01, passage-level wording author, historical evaluator attribution, transmission route, and compiler authorship remain `unresolved`, `unclear`, or `not_assessed` in `attribution_links.csv`.

For S02 and S03, attribution fields are `not_applicable` or `unresolved`. Taqrib's exact wording and correspondence do not establish the historical source of any statement.

## PROV-40-C01 rank-3 adjudication

In a separate post-first-pass adjudication (`manual_collation_pilot_10_PROV40_adjudication/PROV-40-C01_ADJUDICATION.md`), the standalone descriptor `ثقة` in S01 is adjudicated to **rank 3 in Ibn Hajar's Taqrib taxonomy**, supported by Ibn Hajar's introductory definition:

> الثالثة: من أفرد بصفة، كثقة، أو متقن، أو ثبت، أو عدل.

The frozen Pass 1 record in `statements.csv` preserves `rank_status=unranked` (blank rank) unchanged. This adjudication establishes a taxonomy mapping; it does not decide target suitability, historical-input eligibility, historical evaluator identity, or transmission routes.

## PROV-39-C01 identity

`candidate_entries.csv` records `identity_match_status=confirmed`, supported by `EVID-PROV-39-C01-ID01` from al-Mizzi, *Tahdhib al-Kamal*, vol. 8, pp. 284-285, entry 1707. The identity rationale uses the matching full lineage (خلف بن خليفة بن صاعد بن برام), kunyah (أبو أحمد), tribal affiliation and patronage (الأشجعي مولاهم), geographical trajectory from Kufa to Wasit to Baghdad (كان بالكوفة ثم انتقل إلى واسط فسكنها مدة ثم تحول إلى بغداد فأقام بها إلى حين وفاته), 8th tabaqah, canonical transmission symbols (بخ م ٤: al-Bukhari in al-Adab al-Mufrad, Muslim, and the four Sunan compilers), and death in 181 AH. This decision uses convergent biographical details only, excluding the evaluative grade.

**Note on source dependence**: Convergence between *Taqrib al-Tahdhib* and *Tahdhib al-Kamal* represents strong biographical correspondence under potential literary compilation dependence, because Ibn Hajar drew heavily upon al-Mizzi's compilation. It confirms historical identity resolution without claiming multiple strictly independent primary witnesses.

## PROV-39-C01 statement segmentation

The local Taqrib corpus record is `book_id=3076`, `page_num=194`, `sequence_num=1731`; its body contains the candidate entry text. `sources.csv` marks this local transcription `verified_in_corpus`.

The entry is segmented in `statements.csv` into 5 atomic statements:

| Statement | Text | Working classification |
| --- | --- | --- |
| `PROV-39-C01-S01` | `صدوق اختلط في الآخر` | Standardized narrator grade (base `صدوق`, qualification `اختلط في الآخر`) |
| `PROV-39-C01-S02` | `وادعى أنه رأى عمرو ابن حريث الصحابي` | Disputed biographical claim of sighting a Companion |
| `PROV-39-C01-S03` | `فأنكر عليه ذلك ابن عيينة وأحمد` | Specific transmission criticism (attributed historical response to sighting claim) |
| `PROV-39-C01-S04` | `من الثامنة` | Biographical or generational classification |
| `PROV-39-C01-S05` | `مات سنة إحدى وثمانين على الصحيح` | Biographical or chronological statement |

Each row links to an exact Taqrib corpus span and a separate `passage_text` evidence record.

## PROV-39-C01 attribution and provenance status

For S01 (`صدوق اختلط في الآخر`), the passage names no evaluator (`none_named`). Work-level metadata (`Ibn Hajar`) is preserved in `sources.csv`, but passage-level wording author is `unknown`, attribution form is `unclear`, and historical evaluator attribution, transmission route, and compiler authorship remain `unresolved` or `not_assessed` in `attribution_links.csv`.

For S02, S04, and S05, attribution fields are `not_applicable` or `unresolved`.

For S03 (`فأنكر عليه ذلك ابن عيينة وأحمد`), the passage explicitly names earlier historical critics: Sufyan ibn Uyaynah and Ahmad ibn Hanbal (`evaluator_value_status=identified`, `passage_evaluator_naming_status=explicit_individual_named`, `attribution_form=explicit_attribution`). The criticism reported is strictly restricted to the claim of having seen the Companion Amr ibn Hurayth, not a blanket rejection of general narrator reliability. Transmission route is `named_authority_route_unverified` and compiler authorship is `unresolved`.

## PROV-39-C01 rank-5 adjudication and historical investigation

In a separate post-first-pass adjudication (`manual_collation_pilot_10_PROV39_adjudication/PROV-39-C01_ADJUDICATION.md`), the compound grade descriptor `صدوق اختلط في الآخر` in S01 is adjudicated to **rank 5 in Ibn Hajar's Taqrib taxonomy**, supported by Ibn Hajar's introductory definition:

> الخامسة: من قصر عن الرابعة قليلا، وعليه تدور عبارة: صدوق سيء الحفظ، أو صدوق يهم، أو له أوهام، أو يخطئ، أو تغير بأخرة، أو اختلط في الآخر.

The frozen Pass 1 record in `statements.csv` preserves `rank_status=unranked` (blank rank) unchanged.

Regarding the chronological defect and early attestations:

> Early biographical reports provide evidence that Khalaf experienced significant deterioration late in life. Ahmad's reported observation in 177 AH provides a chronological anchor for his condition, but does not independently establish the exact onset of ikhtilat or classify every subsequent transmission. The reliability of individual narrations therefore requires consideration of the student's audition period and the specific transmission. The relationship between these reports and Ibn Hajar's formulation remains unestablished.

The analytical framework distinguishes three separate propositions regarding ikhtilat:
1. The narrator experienced ikhtilat (memory deterioration).
2. The deterioration occurred late in life (في الآخر).
3. Particular transmissions were affected by it (a chronological transmission-quality problem requiring student- and report-level examination, rather than an automatic blanket rejection of all post-onset transmissions).


## PROV-56-C01 identity, collation, and adjudication

The candidate is Shamela4 narrator 6996, `يحيى بن محمد بن عبد الله بن مهران`. The Taqrib candidate is entry 7638 on local corpus page 596. Identity is confirmed against al-Mizzi, *Tahdhib al-Kamal*, vol. 31, pp. 522-524, entry 6913, using lineage, the al-Jari sobriquet, Banu Nawfal patronage, and Hijazi identification. The source explains al-Jar as a port; no more precise geography is inferred. Literary dependence remains possible, so this is not treated as independent attestation.

The source grade span is transcribed as `صدوق يخطىء`. The original dataset field `صدوق يخطئ.` is preserved as supplied. The hamza spelling and terminal punctuation differ, so candidate-field correspondence is recorded as `minor_variation`. Statement S01 retains the exact Taqrib spelling, base grade `صدوق`, and qualification `يخطىء`; its working-table rank remains blank and `unranked`. The separate post-first-pass adjudication assigns Rank 5. S02, `من كبار العاشرة`, is separately recorded as a generational classification.

The historical discussion in the adjudication package treats assessments as reports preserved by al-Mizzi, not as independently inspected primary-source statements. No claim is made that they were the sources of Ibn Hajar's formulation. The local Taqrib and Tahdhib transcriptions and book metadata were checked; printed page images were not independently inspected.


## PROV-37-C01 identity, collation, and adjudication

- Dataset record: Shamela4 narrator `1740`, `خالد بن عبد الرحمن بن بكير`. The grade is recorded in `biography_json["summary"]["الرتبة عند ابن حجر"]` as `صدوق يخطئ.`; the existing case location was corrected from `biography_text`.
- Candidate: Ibn Hajar, *Taqrib al-Tahdhib*, corpus page 189, entry 1650: `١٦٥٠- خالد ابن عبد الرحمن ابن بكير السلمي أبو أمية البصري صدوق يخطىء من الثامنة خ ت س`
- Identity: confirmed from the matching lineage, `السلمي`, `أبو أمية`, and Basran identification, with al-Mizzi's *Tahdhib al-Kamal* entry 1628 as additional biographical evidence. The nearby Taqrib entry 1652 is a different al-Makhzumi al-Makki with a different lineage and generation. The grade was excluded from identity matching.
- Candidate-field correspondence: `minor_variation`. Dataset `صدوق يخطئ.` and Taqrib `صدوق يخطىء` are preserved verbatim; hamza spelling and final punctuation differ.
- S01: `صدوق يخطىء`, base `صدوق`, qualification `يخطىء`, Pass 1 remains blank and `unranked`.
- S02: `من الثامنة`, a separate generational classification, with rank status `not_applicable`.
- Separate adjudication: Rank 5, based on the same Taqrib taxonomy source reviewed for PROV-56. Rank 5 remains a qualitative category, not a uniform interval on a scalar reliability scale.
- Historical evidence: Ibn Abi Hatim's *al-Jarh wa al-ta'dil* locally records his father Abu Hatim's `لا بأس به`. Al-Mizzi's *Tahdhib al-Kamal* expands this as `صدوق لا بأس به` and reports Ibn Hibban's `يخطئ`. Al-Mizzi's footnote also reports distinct wording from al-Uqayli and others. Those cited works were not all independently inspected; no derivation of Ibn Hajar's wording from any one report is established.
- Limits: local corpus transcriptions and metadata were checked. Printed pages were not inspected. The original dataset-to-source route and literary dependence remain unresolved.

## PROV-24-C01 identity, text collation, and attribution draft

**Status:** User-approved, AI-assisted single-reviewer first-pass feasibility record. No target-task, historical-input, or model eligibility decision has been made.

- Dataset record: HadithDB narrator ID `1214`, display name `أَبَا حَمْزَةَ،`. The exact raw record fields are preserved in the case packet and `source_evidence.csv`; the leading colon in `الاسم` and display-name punctuation are not normalized. The original field remains `وثقه: النسائي` under `الرتبة عند ابن حجر`.
- Candidate: Taqrib entry `3038`, local corpus `page_num=283`, `sequence_num=3028`: `٣٠٣٨- طلحة ابن يزيد الأيلي بفتح الهمزة وسكون الياء أبو حمزة مولى الأنصار نزل الكوفة وثقه النسائي من الثالثة خ ٤`. The candidate-field comparison is `minor_variation` because the dataset inserts a colon; the original field is unchanged.
- Identity draft: `confirmed`, based on personal name, kunya, Ansari affiliation, Kufa residence, and the patronage relationship to Quraza ibn Ka'b. Al-Mizzi's Tahdhib al-Kamal, vol. 13, p. 446, entry 2986 identifies `طلحة بن يزيد الأنصاري، أبو حمزة الكوفي، مولى قرظة بن كعب الأنصاري`. The forms `الأيلي` and `الأنصاري` are preserved as found; no normalization or geographical explanation is inferred. The grade was excluded from identity matching. The two compilations are not treated as independent witnesses.
- S01: `وثقه النسائي`, classified as `attributed_earlier_critic_judgment`. This is exact wording in Taqrib, explicitly naming al-Nasa'i in the consulted passage. The historical evaluator status remains `explicitly_reported_but_historically_unverified`; transmission route is `named_authority_route_unverified`; wording author is unknown; compiler authorship is unresolved. No rank is assigned from this attributed report.
- S02: `من الثالثة`, recorded separately as a descriptive/generational classification, not a narrator-grade rank. The trailing `خ ٤` symbols remain only in the full entry and are not expanded here.
- Locator limitation: the local Taqrib metadata says pagination matches print, but the local locator `page_num=283` differs from HadithDB's embedded citation `1/465` and an al-Mizzi footnote's citation `1/380`. Record 283 as the local corpus locator and do not claim visual verification of the printed page. The printed page image has not been checked.
- Historical context: the separate research memo records local and digital-source probes. The available Nasa'i Sunan report at 1/355 (no. 1665) addresses whether this narrator heard from Hudhayfa in that report; it is not treated as a general narrator evaluation. The available Sunan al-Kubra no. 1383 text identifies Abu Hamza/Talha but does not display the phrase `وطلحة هذا ثقة`; the exact earlier source for Taqrib's report remains unresolved. These probes do not establish or refute the historical attribution.
- `target_task_scope=not_assessed`, `historical_input_eligibility=not_assessed`, and `corroboration_status=unresolved_corroboration`. The external-text probes are exploratory and leave corroboration unresolved; they are not a completed transmission-route adjudication.

Source-research notes and direct digital-source links: `../ai_assisted/PROV-24_source_research.md`. The user approved the identity match and two-statement segmentation on 2026-11-13, with the attribution, route, and locator limitations above retained.

## Controlled source-status labels

For `SRC-PROV-39-C01`, `SRC-PROV-39-C01-ID01`, `SRC-PROV-40-C01`, and `SRC-PROV-40-C01-ID01`, the mutable working table now uses the frozen v2.2 enum labels `recorded` and `verified_in_corpus`. This mechanically replaces the earlier labels `transcribed_from_source_metadata` and `verified_local_corpus`; the cited evidence, source text, and case decisions are unchanged. The mapping is recorded in `WORKING_COPY_MANIFEST.json`.


## PROV-51-C01 identity and source collation (approved first-pass freeze)

This is an AI-assisted, single-reviewer feasibility record approved by the user for first-pass freezing on 2026-11-13. It is not independent scholarly validation or inter-reviewer agreement. The dataset record is Shamela4 narrator 5498, `محمد بن إسماعيل بن عياش بن سليم`, with attached nisbahs `العنسي، الحمصي`. Local Taqrīb entry 5735 (p. 468, page record 5727) contains the exact field wording and identifies the narrator as al-Himsi. Identity is marked confirmed from al-Mizzi's earlier *Tahdhīb al-Kamāl* entry 5067, where the name continues `بن سليم العنسي الحمصي`. The identity rationale excludes the criticism text. Preserve the dataset/Taqrīb name-length difference and do not normalize it. This is a distinct work but may be part of Taqrīb's literary source tradition; it is not counted as an independent historical attestation.

The Taqrīb wording is split into two statements:

| Statement | Exact text | Draft classification |
| --- | --- | --- |
| `PROV-51-C01-S01` | `عابوا عليه أنه حدث عن أبيه بغير سماع` | Specific transmission criticism; the collective is unnamed; no grade or numeric rank |
| `PROV-51-C01-S02` | `من العاشرة` | Generational classification, separate from criticism and rank |

The trailing `ق` remains in the full entry as a bibliographic symbol and is not expanded into a statement. The exact criticism phrase in Taqrīb is textual correspondence only. Its `عابوا` wording identifies an unnamed collective: do not identify that collective as Abū Ḥātim or Abū Dāwūd. Local *al-Jarḥ wa-al-taʿdīl* 7/189-190 and *Tahdhīb al-Kamāl* 24/483-484 preserve related but differently worded reports: Abū Ḥātim's no-audition report, and al-Mizzī's separate report from al-Ajurri about Abū Dāwūd. Al-Mizzī's modern editor footnote explicitly cites Ibn Hajar's later Taqrīb wording; that footnote is not an earlier witness to the phrase. Evaluator attribution and route therefore remain unresolved, and corroboration is not classified as independent or dependent.

The working rows use local digital corpus transcriptions and edition metadata. The exploratory memo [`PROV-51_source_research.md`](../ai_assisted/PROV-51_source_research.md) records additional online transcription/PDF checks and their limits. No Awwāma printed page image was visually collated. Target scope is `not_in_defined_task` for S01 and S02; historical-input eligibility is not assessed for S01 and not applicable for S02. No narrator-reliability conclusion is made.


## PROV-01-C01 first-pass annotation (approved for freeze)

This is an AI-assisted, single-reviewer first-pass annotation approved by the user for freezing after validation on 2026-11-13. It is not independent expert review or inter-reviewer agreement. The dataset source is HadithDB ID 17, `جَابِرَ بْنَ عَبْدِ اللهِ الْأَنْصَارِيَّ`. The raw HadithDB record separately contains `الرتبة عند ابن حجر: صحابي` and `طبقة رواة التقريب: صحابي`; do not collapse these fields.

The local Taqrīb entry 871 (page 136, sequence 863) is transcribed as: `٨٧١- جابر ابن عبد الله ابن عمرو ابن حرام بمهملة وراء الأنصاري ثم السلمي بفتحتين صحابي ابن صحابي غزا تسع عشرة غزوة ومات بالمدينة بعد السبعين وهو ابن أربع وتسعين ع`. The draft splits the phrase into five claims: `صحابي` (Companion-status candidate), `ابن صحابي` (father relationship/status), `غزا تسع عشرة غزوة` (campaign statement), `ومات بالمدينة بعد السبعين` (death place/chronology), and `وهو ابن أربع وتسعين` (reported age). The trailing `ع` is retained in the full source entry and not expanded.

The proposed identity match is supported by al-Jarh wa-al-taʿdil entry 2019, which gives the same full name/lineage, kunyas and al-Sulami al-Ansari nisbahs. The identity rationale excludes `له صحبة`. Al-Mizzi's entry 871 is recorded separately as context. The S01 Companion-status phrase is a status-only candidate, not an ordinary reliability-grade target. First-pass `rank_status` is left `unranked`; Ibn Hajar's introduction discusses the Companions under both the first rank and first generation, but any case-level rank mapping should be a separate post-first-pass adjudication.

Locator differences remain open: HadithDB cites Taqrīb 1/192 while the local corpus places entry 871 at p.136; HadithDB cites al-Mizzi 4/443 while the phrase `صاحب رسول الله ... وابن صاحبه` is on local p.444. No printed page image was inspected. See [`PROV-01_source_research.md`](../ai_assisted/PROV-01_source_research.md) for local corpus text, upstream digital text checks, metadata, and evidence limits. These records do not establish historical source dependence, the origin of HadithDB's value, or historical-input eligibility.


### PROV-01 draft revision 1: attribution and corroboration links

Following reviewer feedback, the five statement texts and their classifications are unchanged. The S01-S05 attribution rows now record `wording_author_value_status=unknown`, `compiler_authorship_status=unresolved`, and `transmission_route_status=unresolved`. Evaluator-related fields remain `not_applicable` because these are not evaluator judgements. Ibn Hajar remains recorded as the author/compiler of the Taqrib work in `sources.csv`; that bibliographic fact is not copied into passage-level authorship. No historical source or transmitter is asserted.

Three statement-level evidence rows now link the relevant earlier wording: Ibn Abi Hatim's `له صحبة` to S01; al-Mizzi's `صاحب رسول الله ﷺ` to S01; and al-Mizzi's `وابن صاحبه` to S02. The frozen schema has no corroboration-specific evidence role, so these statement-linked records use the allowed role `other` to serve as corroborating textual evidence for these specific claims. This is a case-specific use for linked evidence, not a redefinition of `other` as a general corroboration category. The full source passages remain preserved in the earlier candidate-level context rows. `corroboration_status=unresolved_corroboration` remains for S01 and S02: related textual evidence is linked, but source dependence is not established, so no independent-corroboration claim is made. The HadithDB record remains dataset evidence only.

User approved this draft for first-pass freezing after validation on 2026-11-13. The frozen snapshot is case-scoped; other cases in the included working-copy context are not approved by this decision.
