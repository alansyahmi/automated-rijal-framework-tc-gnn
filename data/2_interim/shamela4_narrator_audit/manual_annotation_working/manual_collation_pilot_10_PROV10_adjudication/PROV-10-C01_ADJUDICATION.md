# PROV-10-C01 Adjudication: Taqrīb Rank Mapping

**Status:** Post-first-pass adjudication, 2026-11-12  
**Scope:** PROV-10-C01-S01 only. This addendum does not modify the frozen Pass 1 package or the earlier annotation.

## Adjudicated mapping

The standalone Taqrīb grade statement `ثقة` in S01 maps to **rank 3 in Ibn Ḥajar's Taqrīb taxonomy**.

| Field | Adjudicated value |
| --- | --- |
| `taqrib_rank_number` | `3` |
| `rank_status` | `assigned` |
| Frozen Pass 1 value | Blank rank; `rank_status=unranked`, preserved unchanged |

This is a taxonomy mapping: it records how Ibn Ḥajar's introduction classifies a single descriptor such as `ثقة`. It does not establish who first made this narrator-specific judgement, how the judgement reached the surviving text, or whether the grade is suitable as a research target.

## Primary-source citation

Ibn Ḥajar al-ʿAsqalānī, *Taqrīb al-Tahdhīb*, edited by Muḥammad ʿAwwāma (Dār al-Rashīd, first edition, 1406 AH / 1986 CE), introduction, section **أما المراتب**, third rank, p. 74:

> الثالثة: من أفرد بصفة، كثقة، أو متقن، أو ثبت، أو عدل.

Translation for this decision: “The third [rank] is one described by a single attribute, such as thiqah, mutqin, thabt, or ʿadl.” The example `كثقة` explicitly places the single descriptor `ثقة` in rank 3. S01 is the separate, standalone `ثقة` statement in the entry, so the taxonomy mapping is rank 3.

The exact wording appears on the page labelled 74 in the [Awwāma text transcription of the introduction](https://scribetools.com/ar/library/rijal/1957-%D8%AA%D9%82%D8%B1%D9%8A%D8%A8-%D8%A7%D9%84%D8%AA%D9%87%D8%B0%D9%8A%D8%A8-%D8%B9%D9%88%D8%A7%D9%85%D8%A9-%D9%83%D8%AA%D8%A7%D8%A8-%D8%A7%D9%82%D8%B1%D8%A7-%D8%A7%D9%88%D9%86%D9%84%D8%A7%D9%8A%D9%86-6ee55649/text/0005). The local Shamela4 [book metadata](</C:/Projects/automated-rijal-framework-tc-gnn/data/1_raw/Shamela4_Full_DB/26__التراجم-والطبقات/3076__تقريب-التهذيب/book_metadata.json>) identifies the represented edition as Muḥammad ʿAwwāma, Dār al-Rashīd, first edition, 1406/1986, and states that its numbering matches the printed edition. The assistant verified the wording and page label in searchable text, not from a physical page image. The local `pages.jsonl` entry transcription does not contain this introduction passage.

## Relationship to earlier records

The frozen Pass 1 snapshot correctly records what had been decided at that stage: S01 was `unranked`, with no numeric rank entered. This document records the later taxonomy adjudication and its evidence without revising that first-pass state.

The earlier annotation's rank value `3` is substantively supported as a taxonomy mapping. That earlier row did not preserve this introductory citation or distinguish taxonomy rank from target suitability and historical provenance; this addendum supplies that missing basis. The earlier attribution fields remain a legacy interpretation, not corroborating evidence for the rank mapping.

## Decisions that remain open

- **Target suitability:** not assessed. Rank 3 does not make S01 an approved modelling target.
- **Historical-input eligibility:** not assessed.
- **Passage-level wording author and compiler authorship:** unresolved. Work-level metadata naming Ibn Ḥajar does not show that he personally formulated this specific assessment.
- **Historical evaluator:** no evaluator is named in the S01 passage; attribution of the judgement remains unresolved.
- **Transmission route:** not assessed.
- **Editorial questions:** the local corpus transcription supports that the phrase occurs in the corpus entry. Edition variants, possible editorial intervention in the entry, and the phrase's status in an inspected printed witness remain separate questions and are not resolved by the introduction's taxonomy.
- **Corroboration:** not examined in Pass 1.

S02 remains the reported biographical claim `يقال له رؤية`, not proof of Companion status. S03 remains `مات سنة سبع أو ثمان وتسعين`, verbatim and without date normalization.
