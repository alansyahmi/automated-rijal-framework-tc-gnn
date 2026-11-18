# Gate A Morphological Second-Pass Audit v0.1

**Status:** second-pass audit over `177` morphological surface forms and `44` `none_found` morphological hits. All `human_*` columns remain blank pending your approval. Zero canonical ranks assigned and zero rules enabled.

## 1. Morphological Surface Forms (`177` total; `124` new beyond `v0.1`)
- All `177` forms by audit category: `{'context_dependent_mixed_form': 21, 'exclude_homograph_or_collision': 12, 'existing_v0_1_evaluative_token': 49, 'new_evaluative_declension_or_derivation': 95}`
- All `177` forms by recommended Gate A action: `{'abstain': 12, 'conditional': 21, 'promote_to_gate_a_census_candidate': 95, 'retain_with_clause_guard': 49}`
- **New `124` forms only** by audit category: `{'context_dependent_mixed_form': 17, 'exclude_homograph_or_collision': 12, 'new_evaluative_declension_or_derivation': 95}`

### Notable New Evaluative Declensions / Verb Derivations Surfaced
- `MF-09_QABIL` `مقبولة` (`n=65`): e.g. `S3076-P743-C009-E8530`
- `MF-12_JAHIL` `فمجهول` (`n=33`): e.g. `S3076-P154-C004-E1146`
- `MF-08_HUJJA` `حجة` (`n=32`): e.g. `S3076-P081-C013-E0065`
- `MF-23_KHALAT` `اختلط` (`n=22`): e.g. `S3076-P120-C007-E0638`
- `MF-04_THABAT` `أثبت` (`n=14`): e.g. `S3076-P077-C008-E0005`
- `MF-01_WATHAQ` `ووثقه` (`n=13`): e.g. `S3076-P091-C003-E0199`
- `MF-06_HAFIZ` `الحافظ` (`n=10`): e.g. `S3076-P080-C010-E0047`
- `MF-03_SAHIB` `صحابيا` (`n=9`): e.g. `S3076-P384-C007-E4480`
- `MF-22_GHALAT` `أغلاط` (`n=8`): e.g. `S3076-P080-C014-E0051`
- `MF-24_NAKAR` `مناكير` (`n=8`): e.g. `S3076-P091-C011-E0207`
- `MF-10_LAYIN` `لينه` (`n=7`): e.g. `S3076-P118-C008-E0613`
- `MF-22_GHALAT` `الغلط` (`n=7`): e.g. `S3076-P122-C010-E0674`
- `MF-23_KHALAT` `واختلط` (`n=6`): e.g. `S3076-P239-C009-E2365`
- `MF-22_GHALAT` `يغلط` (`n=5`): e.g. `S3076-P143-C002-E0979`
- `MF-04_THABAT` `تثبت` (`n=5`): e.g. `S3076-P192-C020-E1706`

### Notable Homograph / Clitic Collisions Filtered Out (`abstain`)
- `قبله` (`170`), `قبل` (`166`): temporal/cross-ref ('before' / `الذي قبله`), not `MF-09_QABIL`.
- `صاحب` (`129`): book/place/person association (`صاحب السنن`, `صاحب الاستيعاب`), not Companion status.
- `المعروف` (`65`): 'known as' (`المعروف بالمروزي`), not `لا يعرف`.
- `فلان` (`6`): `ف + لان` ('so-and-so'), not `MF-10_LAYIN`.
- `فيهم` (`1`): `ف + يهم` ('among them'), not `MF-19_WAHAM`.

## 2. `44` `none_found` Entries Hit by Morphological Scan (`NONE_FOUND_44_MORPH_AUDIT_V0_1.csv`)
- By audit category: `{'book_specific_memory_qualification': 1, 'homograph_or_biographical_false_positive': 33, 'newly_discovered_subject_grade_candidate': 1, 'non_subject_or_unnamed_narrator_cue': 5, 'unnamed_narrator_la_yarif': 4}`
- By recommended disposition: `{'keep_abstain': 33, 'keep_conditional': 10, 'revise_to_candidate': 1}`
- **1** genuine subject-level Rank 1 discovery: `S3076-P217-C003-E2037` (`زنباع ابن روح ... صحابي له حديثان ق`).
- **5** non-subject / unnamed-narrator companionship cues (`conditional`), **4** `لا يعرف` unnamed-narrator entries (`conditional`), **1** book-specific mixing note (`E0009` `conditional`), and **33** homograph/biographical/tamiz false positives (`abstain`).
