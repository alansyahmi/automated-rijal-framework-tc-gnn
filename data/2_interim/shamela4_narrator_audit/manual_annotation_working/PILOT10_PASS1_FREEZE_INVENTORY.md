# Pilot 10 Pass 1 Freeze Inventory and Recovery Audit

**Generated UTC:** 2026-11-13T09:44:34Z  
**Working Copy Manifest SHA-256:** `8432809d989992503ad2935ec2fc04e5707afccc92b30142e6d61cbdb1b9bc1a` (sidecar and all listed file hashes verified)

## 1. Summary Counts (10 Cases)
- **Original contemporaneous Pass 1 freeze:** `7` (`PROV-10`, `PROV-56`, `PROV-24`, `PROV-51`, `PROV-01`, `PROV-02`, `PROV-04`)
- **Retrospectively reconstructed Pass 1 freeze:** `0`
- **Pass 1 working draft only:** `0`
- **Pass 1 snapshot missing or unrecoverable:** `3` (`PROV-37`, `PROV-39`, `PROV-40`)
- **Separate rank adjudication completed:** `5` (`PROV-10`, `PROV-40`, `PROV-39`, `PROV-56`, `PROV-37`)
- **Separate legacy reconciliation completed:** `1` (`PROV-10`)

## 2. Complete 10-Case Inventory

| Case | Record | `pass1_snapshot_status` | Pass 1 Directory / Manifest SHA-256 (Prefix) | Integrity (Sidecar & Files) | Pass 1 Rank / Target Scope | Separate Rank Adjudication | Legacy Reconciliation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `PROV-10` | `HadithDB 515` | `original_contemporaneous_pass1_freeze` | `manual_collation_pilot_10_PROV10_pass1_frozen` (`0c6d0b85f267`) | Verified (`2026-11-12T13:20:29Z`) | `unranked` / `not_assessed` | `completed_separate_adjudication` (`508102d0c1cf`) | `completed_separate_reconciliation` (`d6d7b7488db2`) |
| `PROV-40` | `Shamela4 1813` | `missing_unrecoverable` | None | N/A (no Pass 1 freeze) | `unranked` / `not_assessed` (current working copy) | `completed_separate_adjudication` (`c067c21a3414`) | `not_started` |
| `PROV-39` | `Shamela4 1811` | `missing_unrecoverable` | None | N/A (no Pass 1 freeze) | `unranked` / `not_assessed` (current working copy) | `completed_separate_adjudication` (`92b791ceec5a`) | `not_started` |
| `PROV-56` | `Shamela4 6996` | `original_contemporaneous_pass1_freeze` | `manual_collation_pilot_10_PROV56_frozen` (`f956303c51f5`) | Verified (`2026-11-12T16:48:39Z`) | `unranked` / `not_assessed` | `completed_separate_adjudication` (`12410a24d1f6`) | `not_started` |
| `PROV-37` | `Shamela4 1740` | `missing_unrecoverable` | None | N/A (no Pass 1 freeze) | `unranked` / `not_assessed` (current working copy) | `completed_separate_adjudication` (`f30569ceaeeb`) | `not_started` |
| `PROV-24` | `HadithDB 1214` | `original_contemporaneous_pass1_freeze` | `manual_collation_pilot_10_PROV24_frozen` (`d3494ce6189e`) | Verified (`2026-11-12T17:35:38Z`) | `not_applicable` / `not_assessed` | `not_started` | `not_started` |
| `PROV-51` | `Shamela4 5498` | `original_contemporaneous_pass1_freeze` | `manual_collation_pilot_10_PROV51_frozen` (`ad06502a2168`) | Verified (`2026-11-13T06:13:19Z`) | `unranked` / `not_in_defined_task` | `not_started` | `not_started` |
| `PROV-01` | `HadithDB 17` | `original_contemporaneous_pass1_freeze` | `manual_collation_pilot_10_PROV01_frozen` (`9ce208851679`) | Verified (`2026-11-13T07:24:08Z`) | `unranked` / `status_only_candidate` | `not_started` | `not_started` |
| `PROV-02` | `HadithDB 27` | `original_contemporaneous_pass1_freeze` | `manual_collation_pilot_10_PROV02_frozen` (`fc560725dbd1`) | Verified (`2026-11-13T09:44:34Z`) | `unranked` / `unresolved` | `not_started` | `not_started` |
| `PROV-04` | `HadithDB 278` | `original_contemporaneous_pass1_freeze` | `manual_collation_pilot_10_PROV04_frozen` (`51ea392bfafb`) | Verified (`2026-11-13T09:44:34Z`) | `unranked` / `C01: unresolved; C02: not_in_defined_task` | `not_started` | `not_started` |

## 3. Recovery Investigation for `PROV-37`, `PROV-39`, and `PROV-40`

**Decision:** Do **not** create retroactive Pass 1 freeze snapshots; record `pass1_snapshot_status = missing_unrecoverable` for all three cases.

### Evidence Examined
1. **Adjudication manifests (`ADJUDICATION_MANIFEST.json`)**:
   - `PROV-40` (`created_utc = 2026-11-12T14:50:51Z`)
   - `PROV-39` (`created_utc = 2026-11-12T15:20:00Z`)
   - `PROV-37` (`created_utc = 2026-11-12T16:13:43Z`)
   All three assert `"frozen_pass1_unchanged": true`, but **none** record a Pass 1 freeze directory, a `source_working_copy_manifest_sha256`, or any source CSV SHA-256 hashes.
2. **Git history**:
   `git log` on `data/2_interim/shamela4_narrator_audit/manual_annotation_working` stops at commit `2a1fdbf` (`research: establish v2.2.2 collation baseline`), before pilot-10 Pass 1 reviews and freezes began; no intermediate commits capture the pre-adjudication states of `PROV-40`, `PROV-39`, or `PROV-37`.
3. **Chronological archived snapshots**:
   - `PROV10_pass1_frozen` (`2026-11-12T13:20:29Z`) predates these three adjudications, but in that snapshot `PROV-37`, `PROV-39`, and `PROV-40` are still unreviewed `S00` placeholders (`provisional_work_item`).
   - `PROV56_frozen/working_copy_snapshot/` (`2026-11-12T16:48:39Z`) is the earliest archived snapshot containing reviewed, unranked rows for `PROV-37`, `PROV-39`, and `PROV-40`, **but it postdates all three adjudication timestamps by 35 to 118 minutes** and explicitly excludes non-`PROV-56` rows from approval (`scope_note`).
   - Moreover, subsequent schema and enum edits touched these rows: `PROV-39` and `PROV-40` `sources.csv` status values were updated in `field_status_migrations` between `PROV56_frozen` (`16:48:39Z`) and `PROV24_frozen` (`17:35:38Z`), and blank `legacy_rank_candidate` / `legacy_reviewer_notes_verbatim` columns were added to `candidate_entries.csv` before `PROV01_frozen` (`2026-11-13T07:24:08Z`).

### Conclusion
Because no pre-adjudication Pass 1 freeze package, recorded hash, or git commit establishes the exact state of `PROV-37`, `PROV-39`, or `PROV-40` prior to `14:50:51Z-16:13:43Z`, constructing a purported Pass 1 freeze from post-adjudication or current working-copy files would manufacture historical certainty. Their Pass 1 snapshots are therefore recorded honestly as **`missing_unrecoverable`**, while noting that `PROV56_frozen/working_copy_snapshot/` preserves their earliest archived post-adjudication unranked working-copy rows (`S01` blank rank, `rank_status=unranked`, zero legacy annotations).
