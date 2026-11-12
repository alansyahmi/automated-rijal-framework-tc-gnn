# Manual Collation Pilot: Reviewer Guide

This guide supplements the frozen 10-case packet. It does not change the sample, the packet, the internal key, or the blank review fields. The case-specific cautions below are prompts for checking evidence, not completed scholarly decisions.

## Source consulted

- Work: *Taqrib al-Tahdhib* (تقريب التهذيب)
- Author: Ibn Hajar al-Asqalani
- Edition metadata: Muhammad Awwamah, Dar al-Rashid, first edition, 1406 AH / 1986 CE
- Text consulted: Shamela digital transcription, Book ID 3076
- Locator: corpus page number and entry number, with the edition metadata stating that book pagination matches the printed pagination

The packet does not establish that a physical printed copy or manuscript witness was inspected. Describe the source as the Shamela digital transcription unless you personally consult and verify the print edition.

## Review order

Use the existing blank human fields in `manual_collation_pilot_10/MANUAL_COLLATION_PILOT_10.csv`.

1. **Resolve identity without using the grade.** Compare names, lineage, kunya, tribal and geographic identifiers, generation, dates, teachers, students, and other biographical details. Record the evidence used. Do not select an entry because its grade matches the dataset value.
2. **Freeze the identity decision for the pass.** If evidence is insufficient, keep identity unresolved. For `PROV-04`, compare both candidate entries without using `ثقة له أفراد` or `مقبول` as identity evidence.
3. **Compare the text.** Read the complete candidate entry and compare the original dataset wording. Preserve spelling, qualifications, exceptions, and editorial marks. Record the printed page and entry locator after checking the source.
4. **Classify the statement and its voice.** Decide whether it is an assessment, biography or status description, a reported opinion, a transmission criticism, editorial material, or another kind of statement. Then identify whose words or judgment the text presents. Do not assume every sentence in Taqrib is Ibn Hajar's own evaluation.
5. **Record qualifications and source evidence.** Keep a reported earlier critic's view distinct from Ibn Hajar's own synthesis. Leave corroboration unresolved until the source dependence has actually been examined.
6. **Make separate research decisions.** Assess target-candidate suitability and historical-input eligibility independently. Do not convert a phrase directly into a reliability class.

## Case prompts

These are issues to inspect, not conclusions:

| Case | Review prompt |
| --- | --- |
| PROV-10 | Check the full name and biographical identifiers, not only the shared personal name. |
| PROV-40 | Compare the dataset record with the full entry's identifiers, aliases, lineage, and location. |
| PROV-39 | Compare lineage, tribal affiliation, geography, and other biographical details. Preserve `اختلط في الآخر`. |
| PROV-56 | Preserve the distinction between `صدوق` and `يخطئ`; do not drop the qualification. |
| PROV-24 | The dataset gives only `أبو حمزة`. The candidate Taqrib entry says `وثقه النسائي`, which explicitly reports al-Nasa'i's view. Review identity and statement voice separately. |
| PROV-51 | `عابوا عليه أنه حدث عن أبيه بغير سماع` describes criticism of a transmission practice. Decide what kind of statement it is; do not automatically map it to a standardized negative grade. |
| PROV-01 | `صحابي` is a Companion-status description. Do not automatically treat it as a conventional grade. |
| PROV-02 | Inspect `[وعاصم بن أبي النجود]`. The edition metadata says square brackets mark differences from another edition. Check the note and context; do not remove or normalize the text. |
| PROV-04 | Two same-name entries are supplied. Resolve identity using non-grade identifiers; if unresolved, retain both candidates and document why. |
| PROV-37 | Compare the full name and biographical identifiers, and preserve the qualification `يخطئ`. |

## Suggested sequence

Begin with `PROV-10`, `PROV-39`, `PROV-56`, and `PROV-37` for identity and text comparison. Then review `PROV-40`, `PROV-01`, and `PROV-02`. Finish with the more attribution-sensitive or identity-ambiguous cases: `PROV-24`, `PROV-04`, and `PROV-51`.

A case that cannot be resolved is still a useful pilot result. Record what evidence is missing, keep the relevant field unresolved, and do not infer historical accuracy, independent corroboration, narrator reliability, or speaker attribution from wording similarity alone. This is a single-reviewer feasibility pilot; it does not establish inter-reviewer agreement or corpus-wide reliability.
