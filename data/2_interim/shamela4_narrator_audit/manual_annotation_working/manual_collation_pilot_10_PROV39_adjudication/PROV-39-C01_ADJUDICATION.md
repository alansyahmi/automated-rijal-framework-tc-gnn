# PROV-39-C01 Adjudication: Taqrīb Rank Mapping & Historical Investigation

**Status:** Post-first-pass adjudication, 2026-11-12  
**Scope:** PROV-39-C01-S01 only. This addendum preserves the frozen Pass 1 package and records the independent taxonomy mapping and refined historical investigation.

## 1. Adjudicated mapping

The compound Taqrīb grade statement with temporal qualification `صدوق اختلط في الآخر` in S01 maps to **rank 5 in Ibn Ḥajar's Taqrīb taxonomy**.

| Field | Adjudicated value |
| --- | --- |
| `taqrib_rank_number` | `5` |
| `rank_status` | `assigned` |
| `grade_base_verbatim` | `صدوق` |
| `grade_qualification_verbatim` | `اختلط في الآخر` |
| Frozen Pass 1 value | Blank rank; `rank_status=unranked`, preserved unchanged |

This is an explicit taxonomy mapping: it records how Ibn Ḥajar's introduction classifies narrators described by `صدوق` combined with deterioration qualifications such as `اختلط في الآخر`. It does not establish who first formulated this narrator-specific assessment, how the assessment reached the surviving compilation, or whether the grade is suitable as a machine-learning research target without modeling transmission-level audition chronology.

## 2. Primary-source citation

Ibn Ḥajar al-ʿAsqalānī, *Taqrīb al-Tahdhīb*, edited by Muḥammad ʿAwwāma (Dār al-Rashīd, first edition, 1406 AH / 1986 CE), introduction, section **أما المراتب**, fifth rank, pp. 74-75:

> الخامسة: من قصر عن الرابعة قليلا، وعليه تدور عبارة: صدوق سيء الحفظ، أو صدوق يهم، أو له أوهام، أو يخطئ، أو تغير بأخرة، أو اختلط في الآخر.

Translation for this decision: "The fifth [rank] is one who falls slightly short of the fourth, and around this revolve the expressions: ṣadūq sayyiʾ al-ḥifẓ, or ṣadūq yahim, or lahu awhām, or yukhṭiʾ, or taghayyara bi-akharah, or ikhtalaṭa fī al-ākhir."

The introductory taxonomy explicitly enumerates `أو اختلط في الآخر` as an exemplifying formula defining rank 5. S01 combines the base grade `صدوق` with the temporal qualification `اختلط في الآخر`, which directly and literally corresponds to Ibn Ḥajar's fifth rank rule.

The local Shamela4 book metadata identifies the represented edition as Muḥammad ʿAwwāma, Dār al-Rashīd, first edition, 1406 AH / 1986 CE, and states that book pagination matches the print.

## 3. Attribution scope and statement boundaries

Entry 1731 comprises five distinct, atomized statements with separate analytical functions:

1. `PROV-39-C01-S01` (`صدوق اختلط في الآخر`): Standardized narrator grade with temporal qualification.
2. `PROV-39-C01-S02` (`وادعى أنه رأى عمرو ابن حريث الصحابي`): Disputed biographical claim of sighting a Companion.
3. `PROV-39-C01-S03` (`فأنكر عليه ذلك ابن عيينة وأحمد`): Specific transmission criticism reporting an attributed historical response by named critics.
4. `PROV-39-C01-S04` (`من الثامنة`): Generational classification (8th tabaqah).
5. `PROV-39-C01-S05` (`مات سنة إحدى وثمانين على الصحيح`): Biographical chronological statement (death date 181 AH).

Attribution boundaries are strictly maintained:
- **S01 (`صدوق اختلط في الآخر`)**: The passage names no evaluator (`none_named`). Work-level metadata (`Ibn Hajar`) is recorded in `sources.csv`, but passage-level wording author remains `unknown`, attribution form is `unclear`, and historical evaluator attribution, transmission route, and compiler authorship remain `unresolved` or `not_assessed`. Unattributed compilation text must not be converted into a positive claim of compiler personal authorship.
- **S03 (`فأنكر عليه ذلك ابن عيينة وأحمد`)**: Explicitly names historical evaluators: Sufyān ibn ʿUyaynah and Aḥmad ibn Ḥanbal (`evaluator_value_status=identified`, `passage_evaluator_naming_status=explicit_individual_named`, `attribution_form=explicit_attribution`). The criticism reported is strictly restricted to the claim of having seen the Companion ʿAmr ibn Ḥurayth; it does not constitute an evaluation of general narrator reliability.
- **S02, S04, S05**: Attribution fields are `not_applicable` or `unresolved`.

## 4. Refined historical investigation of ikhtilāṭ

Early biographical sources report substantial material concerning Khalaf's condition late in life:

> Early biographical reports provide evidence that Khalaf experienced significant deterioration late in life. Aḥmad's reported observation in 177 AH provides a chronological anchor for his condition, but does not independently establish the exact onset of ikhtilāṭ or classify every subsequent transmission. The reliability of individual narrations therefore requires consideration of the student's audition period and the specific transmission. The relationship between these reports and Ibn Hajar's formulation remains unestablished.

The analytical framework distinguishes three separate propositions regarding ikhtilāṭ:
1. **The occurrence of deterioration**: Khalaf experienced ikhtilāṭ (memory deterioration due to age or illness).
2. **The temporal placement**: The deterioration occurred late in life (`في الآخر`).
3. **The impact on transmission**: Particular transmissions were affected by the condition. This constitutes a chronological transmission-quality problem requiring student- and report-level examination, rather than an automatic blanket rejection of all post-onset transmissions.

Early attestations documented in al-Mizzī's *Tahdhīb al-Kamāl* (vol. 8, pp. 284-289, entry 1707) include:
- Aḥmad ibn Ḥanbal's reported direct observation: `رأيت خلف بن خليفة وهو مفلوج سنة سبع وسبعين ومئة، قد حمل وكان لا يفهم فمن كتب عنه قديما فسماعه صحيح` (reported through ʿAbd Allāh ibn Aḥmad, with an additional report through al-Athram: `قد أتيته فلم أفهم عنه`).
- Muḥammad ibn Saʿd: `كان ثقة، مات ببغداد سنة إحدى وثمانين ومئة وهو ابن تسعين سنة أو نحوها`.
- Abū Ḥātim al-Rāzī: `صدوق`.
- Yaḥyā ibn Maʿīn: `ليس به بأس` (via al-Dūrī, Ibn Abī Khaythamah, and ʿAbd al-Khāliq ibn Manṣūr, who added `صدوق`).
- Ibn ʿAdī (*al-Kāmil*): `أرجو أنه لا بأس به، ولا أبرئه من أن يخطئ في بعض الأحايين في بعض رواياته`.

These reports constitute multiple reported early attestations whose transmission routes and source independence remain unresolved. They provide qualitative and chronological context, but they do not establish a fixed date for the onset of ikhtilāṭ or determine the provenance of Ibn Ḥajar's specific phrasing.

## 5. Identity resolution and literary dependence note

The identity of Shamela4 narrator 1811 with Taqrīb entry 1731 (`خلف ابن خليفة ابن صاعد الأشجعي مولاهم أبو أحمد الكوفي نزل واسط ثم بغداد...`) is confirmed using convergent biographical attributes:
- Full lineage: `خلف بن خليفة بن صاعد بن برام`
- Kunyah: `أبو أحمد`
- Tribal affiliation & patronage: `الأشجعي مولاهم`
- Regional trajectory: Kufa to Wasit to Baghdad (`كان بالكوفة ثم انتقل إلى واسط فسكنها مدة ثم تحول إلى بغداد فأقام بها إلى حين وفاته`)
- Generation: 8th tabaqah
- Canonical transmission symbols: al-Bukhārī in *al-Adab al-Mufrad*, Muslim, and the four Sunan compilers (`بخ م ٤`)
- Death chronology: 181 AH

**Methodological Qualification**: While al-Mizzī's *Tahdhīb al-Kamāl* (vol. 8, pp. 284-285, entry 1707) provides matching biographical details, this correspondence represents convergent biographical evidence under potential literary compilation dependence, because Ibn Ḥajar drew heavily upon al-Mizzī's compilation. It confirms historical identity resolution without claiming multiple strictly independent primary witnesses.
