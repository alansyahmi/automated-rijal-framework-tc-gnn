# AI-assisted Pass B annotation draft

**Status:** draft for researcher review; not a human annotation, not blinded, not independent validation, and not a consistency-repeat result.
**Created:** 2026-11-14
**Schema basis:** Manual Collation Schema v2.2.

## What this package contains

This draft applies Pass B segmentation and source comparison to the six-case packet: 6 cases, 7 candidate-entry rows, 22 statement rows, and 6 attribution links. It preserves every original field and the supplied Taqrib text. It does not edit the blank reviewer templates, the frozen Pass A file, source data, or prior audit outputs.

The annotator is an AI system that has already seen earlier discussion of these cases. This work therefore cannot be treated as a blind repeat by the researcher or as a second independent annotator. Do not calculate inter-reviewer agreement or delayed within-researcher consistency from these files. Use them only as a concrete AI proposal for the researcher to accept, correct, or reject.

## RPT-05 key correction requiring attention

The packet candidate key says **CAND-01 = Taqrib entry 5570** and **CAND-02 = entry 5569**. The frozen Pass A rows instead attach entry 5569 evidence to CAND-01 and entry 5570 evidence to CAND-02. That is a key mismatch in the frozen submission; the frozen file is preserved unchanged and a separate `PASS_A_RPT05_KEY_ERRATUM.md` records the discrepancy.

The local HadithDB record 278 gives Qays ibn Hafs ibn al-Qaʿqaʿ, kunya Abū Muḥammad, al-Tamīmī/al-Dārimī, al-Baṣrī, and death 227 AH. Those identifiers correspond to Taqrib entry 5569 (packet CAND-02), whose text is `قيس ابن حفص التميمي الدارمي أبو محمد البصري ثقة له أفراد من العاشرة مات سنة سبع وعشرين`. Entry 5570 (packet CAND-01) explicitly says “another” Qays ibn Hafs, settled in Egypt, with a different generation/date description and the grade `مقبول`. The human's intended identity match appears to be supported for CAND-02; CAND-01 is the homonym candidate. This is a proposed correction to the alias mapping, not a silent modification of Pass A.

**Do not reconcile the two rows by swapping them in place.** If you agree, add a dated correction record after reviewing the packet-to-source key, preserving the frozen Pass A bytes and hashes.

## Annotation summary and qualifications

- **RPT-01:** one qualified grade, `ثقة ثبت فاضل` with the teacher/Basra qualification kept intact; separate generation, death-year, and age statements. Rank 2 is an AI-proposed analogy to the introduction's semantic-affirmation example `ثقة حافظ`; the phrase is not listed verbatim, so review this mapping.
- **RPT-02:** `وثقه النسائي` is an earlier-critic judgement explicitly reported as al-Nasa'i's, not treated as Ibn Hajar's own grade. `من الثالثة` is a generation label, not rank 3. The historical route remains unverified.
- **RPT-03:** the no-audition criticism is a specific transmission criticism and `من العاشرة` is generation information. The collective behind `عابوا` is not identified, and no related report is substituted for its route.
- **RPT-04:** five separate claims are preserved: Companion status, parentage, campaigns, death/location, and age. `صحابي` receives rank 1 only as Taqrib taxonomy/status, never as an ordinary reliability grade. A separate status-task specification is not approved.
- **RPT-05 CAND-01 / entry 5570:** `مقبول` maps to rank 6 in the introduction, but the candidate does not match the original dataset grade field; the statement must not be attached to narrator ID 278.
- **RPT-05 CAND-02 / entry 5569:** `ثقة له أفراد` matches the original field. Rank 3 is mapped from the explicit descriptor `ثقة`; `له أفراد` is preserved and not assigned an assumed severity. Attribution remains unresolved.
- **RPT-06:** `ثقة` maps to rank 3; `يقال له رؤية` stays a reported biographical claim and is not converted into Companion status; the alternative death years remain verbatim.

## Source and eligibility boundaries

The local corpus confirms that the cited Taqrib spans are present in the local transcription. The book metadata records the Awwāma/Dār al-Rashīd edition and explains square-bracketed differences; the printed page images were not inspected in this AI review. The rank excerpts were checked in the official Alifta digital text of Taqrib's introduction. These sources establish text and taxonomy rules only; they do not establish historical authorship, the origin of a judgement, or a traceable route.

Only the local source records needed for these comparisons and the Taqrib introduction were checked for this draft. Other bibliographic references inherited in `PASS_B_SOURCE_REFERENCES.csv` were not re-opened. Corroboration is `not_examined`; historical-input eligibility is `not_assessed` throughout. No statement is cleared as a training target. Target-scope values are provisional diagnostics against the proposed ordinary narrator-grade task; no versioned target-task manifest is frozen.

## Human review order

1. Resolve the RPT-05 alias-key discrepancy in a separate correction record before using either candidate's identity outcome.
2. Review the statement boundaries and exact Arabic spans, especially RPT-01's composite rank-2 mapping and RPT-04's five factual/status claims.
3. Review the attribution rows. Keep work-level authorship distinct from wording authorship and historical evaluator attribution.
4. Keep all target and historical-input eligibility fields open unless the task manifest and required provenance evidence are established.
5. If you disagree, edit a separate researcher-reviewed copy and record why; retain this AI draft unchanged.
