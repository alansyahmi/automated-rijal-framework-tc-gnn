# PROV-40-C01 Adjudication: Taqrīb Rank Mapping & Attribution Scope

**Status:** Post-first-pass adjudication, 2026-11-12  
**Scope:** PROV-40-C01-S01 only. This addendum preserves the frozen Pass 1 package and records the independent taxonomy mapping.

## 1. Adjudicated mapping

The standalone Taqrīb grade statement `ثقة` in S01 maps to **rank 3 in Ibn Ḥajar's Taqrīb taxonomy**.

| Field | Adjudicated value |
| --- | --- |
| `taqrib_rank_number` | `3` |
| `rank_status` | `assigned` |
| Frozen Pass 1 value | Blank rank; `rank_status=unranked`, preserved unchanged |

This is a taxonomy mapping: it records how Ibn Ḥajar's introduction classifies a single descriptor such as `ثقة`. It does not establish who first made this narrator-specific judgement, how the judgement reached the surviving compilation, or whether the grade is suitable as a machine-learning research target.

## 2. Primary-source citation

Ibn Ḥajar al-ʿAsqalānī, *Taqrīb al-Tahdhīb*, edited by Muḥammad ʿAwwāma (Dār al-Rashīd, first edition, 1406 AH / 1986 CE), introduction, section **أما المراتب**, third rank, p. 74:

> الثالثة: من أفرد بصفة، كثقة، أو متقن، أو ثبت، أو عدل.

Translation for this decision: "The third [rank] is one described by a single attribute, such as thiqah, mutqin, thabt, or ʿadl." The example `كثقة` explicitly places the single descriptor `ثقة` in rank 3. S01 is the separate, standalone `ثقة` statement in the entry, so the taxonomy mapping is rank 3.

The local Shamela4 book metadata identifies the represented edition as Muḥammad ʿAwwāma, Dār al-Rashīd, first edition, 1406 AH / 1986 CE, and states that book pagination matches the print.

## 3. Narrow attribution amendment

The passage-level attribution for `PROV-40-C01-S01` (`ثقة`) is formally maintained under the following boundaries:

1. **Work author**: Ibn Ḥajar is the author and compiler of the overarching work (*Taqrīb al-Tahdhīb*), supported by bibliographic metadata.
2. **Passage-level wording author**: Unresolved. Work-level authorship must not be used to assert passage-level authorship. The absence of an explicit citation cue in the entry does not establish that Ibn Ḥajar formulated the assessment himself.
3. **Historical evaluator**: Not named in the passage (`none_named`). The entry does not identify who originated the evaluation.
4. **Attribution form & compiler authorship**: Both remain `unresolved` / `unclear`. An unattributed statement in a compilation may represent independent compiler synthesis, reproduction of an unnamed earlier critic's judgement, condensation of an intermediary source, or a synthesis of multiple authorities. The passage alone does not distinguish these possibilities.
5. **Transmission route**: Not assessed. No transmission chain or citation route is stated in the entry.
6. **Eligibility and target scope**: Both remain `not_assessed`. Target suitability and historical-input eligibility are not established by taxonomy rank.

## 4. Identity evidence and literary dependence note

The identity of Shamela4 narrator 1813 with Taqrīb entry 1734 (`خلف ابن محمد ابن عيسى الخشاب القافلاني`) is confirmed using convergent biographical attributes:
- Full lineage: `خلف بن محمد بن عيسى بن أبي عبد الله`
- Kunyah: `أبو الحسين` (dataset alias `أبو الحسن` noted)
- Occupational & regional nisbah: `الخشاب القافلاني الواسطي`
- Sobriquet (*laqab*): `كردوس`
- Generation: 11th tabaqah
- Canonical transmission symbol: Sunan Ibn Mājah (`ق`)
- Death chronology: Mid-Dhū al-Ḥijjah 274 AH at Wasit, aged over 80

**Methodological Qualification**: While al-Mizzī's *Tahdhīb al-Kamāl* (vol. 8, pp. 294-295, entry 1710) provides detailed matching biographical information, this correspondence represents convergent biographical evidence under potential literary compilation dependence, because Ibn Ḥajar drew heavily upon al-Mizzī's compilation. It confirms historical identity resolution without claiming multiple strictly independent source attestations.
