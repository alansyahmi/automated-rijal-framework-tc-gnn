# Human decision log — Taqrīb phrase review v1.1

**Decision date:** 2026-11-16
**Decision source:** user accepted the recommendations in this Codex review.
**Scope:** phrase-group review decisions only. No entry-level rank labels, production annotation, or active automation rules were created.

## Decisions recorded

### Ru’yah phrases remain conditional

- `PHR-REV-054` (`له رؤية`) and `PHR-REV-063` (`لها رؤية`) are conditional for Rank 1 / Companion status. Ru’yah wording alone does not settle the status. Review the complete entry and retain competing evidence, including a Tabiʿin listing, without silently reconciling it.

### Direct attributed authentication phrases

The following 11 groups are accepted as **Rank 3 attributed-proxy candidates**, with a per-entry guard: the phrase must be the first complete grade-bearing phrase, the named critic must remain explicit, and the complete entry must be checked for later or surrounding qualifications/conflicts. This is a project annotation convention, not a finding about Ibn Ḥajar’s personal authorship, historical provenance, or transmission route. No entry-level output was generated.

- `PHR-REV-088` — `ووثقه النسائي`
- `PHR-REV-089` — `ووثقه العجلي`
- `PHR-REV-090` — `ووثقه ابن معين`
- `PHR-REV-095` — `ووثقه أبو داود وغيره`
- `PHR-REV-096` — `ووثقه أبو زرعة`
- `PHR-REV-103` — `ووثقه أبو زرعة في الحديث`
- `PHR-REV-104` — `ووثقه ابن سعد`
- `PHR-REV-107` — `ووثقه الخطيب`
- `PHR-REV-108` — `ووثقه الدارقطني`
- `PHR-REV-109` — `ووثقه الشافعي`
- `PHR-REV-110` — `ووثقه العجلي وجماعة`

The phrase-group decision does not assert that every grouped occurrence meets the guard. Human review of each complete entry remains necessary before any entry-level label is considered.

### Groups kept conditional because examples show conflicts

- `PHR-REV-091` (`ووثقه ابن حبان`): an example continues with `وفيه ضعف`.
- `PHR-REV-102` (`ووثقه أبو حاتم`): an example continues with al-Nasāʾī’s `ليس بالقوي`.
- `PHR-REV-105` (`ووثقه الأئمة`): an example continues with contrary evaluations.
- `PHR-REV-106` (`ووثقه الجمهور`): the example includes hadith-specific defects and a possible late change in memory.

These stay conditional; the initial praise is not converted to an unqualified rank. A broad automated dispute flag is only a cue and does not prove that each phrase occurrence is qualified.

### Distinct Ibn Ḥibbān listing construction

- `PHR-REV-092` (`ذكره ابن حبان في ثقات التابعين`) is conditional and does not inherit the direct `وثقه <critic>` Rank 3 proxy convention. Its function and surrounding status evidence require case-level review.

## Explicitly untouched

All other phrase groups remain blank. In particular, the truncated `وثقه يعقوب ابن` span, bare `ووثقه` without a named critic, and feminine `ووثقها العجلي` variant were not decided by this approval. All 161 rows in `NONE_FOUND_AUDIT_161.csv` remain untouched with their human fields blank.

## Interpretation limit

The package builder marks a trailing-dispute/qualification flag when a marker occurs anywhere in the full entry. That flag does not establish that the marker follows or qualifies the reviewed phrase. Check exact wording and position in the complete entry; treat the flag as a broad cue only.

These decisions establish the current human policy for selected phrase patterns only. They do not establish the correctness of the complete phrase inventory, the meaning of every occurrence, corpus-wide annotation reliability, or readiness for training.
