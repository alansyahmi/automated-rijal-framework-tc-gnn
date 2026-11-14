# PROV-02 source research and first-pass draft

**Status:** AI-assisted single-reviewer feasibility draft, pending user review. No legacy annotation values were consulted. This memo supports the working rows; it is not an expert adjudication, independent source-authentication, or historical attribution decision.

## Dataset evidence

The local HadithDB raw record is `/27`, display name `وَمَعْمَرٌ`. It separately records `الرتبة عند ابن حجر` as `ثقة ثبت فاضل، إلا أن في روايته عن ثابت والأعمش وعاصم بن أبي النجود، وهشام بن عروة شيئا، وكذا فيما حدث به بالبصرة` and `طبقة رواة التقريب` as `كبار السابعة`. The grade aggregate also cites Taqrib as `1/961`. These are dataset values and citations, not independent historical sources. The raw identity fields give the name, kunya, nisbahs, residence, and variant death dates.

## Taqrib text and editorial addition

The local Shamela corpus locates entry 6809 on page 541, sequence 6803. Its transcription reads: `٦٨٠٩- معمر ابن راشد الأزدي مولاهم أبو عروة البصري نزيل اليمن ثقة ثبت فاضل إلا أن في روايته عن ثابت والأعمش [وعاصم بن أبي النجود] وهشام ابن عروة شيئا وكذا فيما حدث به بالبصرة من كبار السابعة مات سنة أربع وخمسين وهو ابن ثمان وخمسين سنة ع`. The text is verified in the local digital corpus; no printed page image was inspected.

A separate digital transcription identified as the Awwamah edition prints a page 542 note stating that `وعاصم بن أبي النجود` is to be added, as it appears at the end of the entry in *Tahdhib*. This supports treating the bracketed phrase as editorially supplied in that transcription, rather than silently attributing every character to Ibn Hajar. The HadithDB value contains the phrase without brackets and with different punctuation. Candidate-field correspondence is therefore recorded as `minor_variation`. The online transcription is text, not a visually checked printed page. [Awwamah digital transcription, pp. 541-542](https://scribetools.com/ar/library/rijal/1957-%D8%AA%D9%82%D8%B1%D9%8A%D8%A8-%D8%A7%D9%84%D8%AA%D9%87%D8%B0%D9%8A%D8%A8-%D8%B9%D9%88%D8%A7%D9%85%D8%A9-%D9%83%D8%AA%D8%A7%D8%A8-%D8%A7%D9%82%D8%B1%D8%A7-%D8%A7%D9%88%D9%86%D9%84%D8%A7%D9%8A%D9%86-6ee55649/text/0028).

## Identity evidence

A dedicated grade-free HadithDB evidence record (`EVID-PROV-02-C01-ID02`, derived from `SRC-PROV-02-C01-DATA01`, JSON pointer `/27`) isolates the non-grade biographical fields for narrator ID `27`: `الاسم` (`معمر بن راشد`), `الكنية` (`أبو عروة`), `النسب` (`الأزدي مولاهم، الحداني مولاهم، البصري، المهلبي`), `بلد الإقامة` (`اليمن، صنعاء، البصرة`), `علاقات الراوي`, `تاريخ الوفاة`, `بلد الوفاة`, and `بلد الرحلة`. It explicitly excludes `الرتبة عند ابن حجر`, `طبقة رواة التقريب`, `الرتبة عند الذهبي`, and `الجرح والتعديل`, while preserving the complete raw record separately in `EVID-PROV-02-C01-DATA01`.

On the biographical-source side, `EVID-PROV-02-C01-ID01` (al-Jarh wa-al-taʿdil entry 1165, local vol. 8, p. 255) identifies `معمر بن راشد أبو عروة`, a mawla of al-Azd who settled in Yemen, and says he is Maʿmar ibn Abi ʿAmr. Al-Mizzi's *Tahdhib al-Kamal* entry 6104 (local vol. 28, beginning p. 303; the online transcription marks p. 304) gives the fuller form `معمر بن راشد الأزدي الحداني ... أبو عروة ابن أبي عمرو البصري` and the mawla relationship. Together with `EVID-PROV-02-C01-ID02` and the non-grade Taqrib entry 6809 identifiers, these form a two-sided non-grade bridge confirming record-to-entry identity (`identity_match_status=confirmed`). They do not establish source independence or grade provenance. [Ibn Abi Hatim, *al-Jarh wa-al-taʿdil* 8/255](https://islamport.com/l/trj/4634/3502.htm), [al-Mizzi, *Tahdhib al-Kamal*, vol. 28, entry 6104](https://www.islamweb.net/ar/library/content/1001/7356/%D9%85%D8%B9%D9%85%D8%B1-%D8%A8%D9%86-%D8%B1%D8%A7%D8%B4%D8%AF-%D8%A7%D9%84%D8%A3%D8%B2%D8%AF%D9%8A-%D8%A7%D9%84%D8%AD%D8%AF%D8%A7%D9%86%D9%8A-%D8%A3%D8%A8%D9%88-%D8%B9%D8%B1%D9%88%D8%A9-%D8%A8%D9%86-%D8%A3%D8%A8%D9%8A-%D8%B9%D9%85%D8%B1%D9%88-%D8%A7%D9%84%D8%A8%D8%B5%D8%B1%D9%8A).

## Related historical reports: context, not attribution proof

Al-Mizzi's entry preserves multiple reports relevant to parts of the Taqrib qualification: a report from Yahya ibn Maʿin that Maʿmar's transmission from Thabit was weak, and a report from Abu Hatim that what Maʿmar narrated in Basra contained errors while he remained صالح الحديث. These reports show semantic correspondence with portions of the later qualification, subject to the following analytical cautions:

- The reports concerning Thabit, al-Aʿmash, and Hisham ibn ʿUrwa should not be treated as one undifferentiated body of criticism; historical support must remain differentiated by critic, subject, and transmission context.
- Abu Hatim's Basra observation concerns a particular transmission context, not necessarily every narration Maʿmar transmitted.
- The reports preserved by al-Mizzi do not establish Ibn Hajar's exact source route, nor do they prove that either critic supplied Ibn Hajar's exact wording.
- The bracketed ʿAsim phrase (`[وعاصم بن أبي النجود]`) is an editorial/textual issue, not evidence of a separate historical attribution.
- Do not assume the qualifications map neatly onto one ordinary Taqrib rank; the separate rank adjudication must examine how Ibn Hajar's introduction handles compound assessments.

The source route and claim-level wording author remain unresolved. [Al-Mizzi, *Tahdhib al-Kamal*, vol. 28, entry 6104](https://www.islamweb.net/ar/library/content/1001/7356/%D9%85%D8%B9%D9%85%D8%B1-%D8%A8%D9%86-%D8%B1%D8%A7%D8%B4%D8%AF-%D8%A7%D9%84%D8%A3%D8%B2%D8%AF%D9%8A-%D8%A7%D9%84%D8%AD%D8%AF%D8%A7%D9%86%D9%8A-%D8%A3%D8%A8%D9%88-%D8%B9%D8%B1%D9%88%D8%A9-%D8%A8%D9%86-%D8%A3%D8%A8%D9%8A-%D8%B9%D9%85%D8%B1%D9%88-%D8%A7%D9%84%D8%A8%D8%B5%D8%B1%D9%8A).

## Working segmentation

1. `ثقة ثبت فاضل إلا أن في روايته عن ثابت والأعمش [وعاصم بن أبي النجود] وهشام ابن عروة شيئا وكذا فيما حدث به بالبصرة`: one qualified grade statement. Base and qualification are separate schema fields in S01; keep every named teacher and the Basra clause.
2. `من كبار السابعة`: generational classification, not rank 7.
3. `مات سنة أربع وخمسين`: death wording, no century/date normalization.
4. `وهو ابن ثمان وخمسين سنة`: age wording, no independent age calculation.

S01 remains unranked in the first pass. Its target scope remains unresolved pending a separate rank/task decision; it must not be promoted into an ordinary-grade target if later mapped to Rank 1. Historical-input eligibility remains not assessed. The other three statements are outside the defined task.

## Limits

This is a case-level digital-text review. It does not verify a printed page image, establish who historically originated the grade, trace a route from any earlier critic to Ibn Hajar, determine source independence, or justify a blanket reliability claim. No rank mapping or legacy reconciliation was performed.
