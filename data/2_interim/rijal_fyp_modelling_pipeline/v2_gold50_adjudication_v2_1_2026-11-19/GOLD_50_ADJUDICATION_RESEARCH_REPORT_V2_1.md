# Gold-50 Adjudication & Source Reconciliation Report (v2.1)

**Status:** All 13 Gold-50 queue items researched against primary Arabic sources (`Taqrib al-Tahdhib` Awwama 1406 & Alifta 1413 introductions, `Shamela4` critic dossiers, `Tahrir Taqrib al-Tahdhib` summaries, and al-Ghada'iri `Kitab al-Du'afa'`) and resolved into a unified reference table.

## 1. Key Source Findings
- **Rank 8 vs Rank 9 (`ضعيف` vs `مجهول`):** Both published Arabic editions of Ibn Hajar's introduction (Awwama 1406 / Dorar / Wikisource and Abu al-Ashbal 1413 / Alifta) explicitly define **Rank 8 = `ضعيف`** and **Rank 9 = `مجهول`**. The Rank 9 = `ضعيف` numbering on Wikimedia stemmed from an OCR-shifted scan (`فطبقة عشرة`). All 5 `ضعيف` entries (`#16, #18, #42, #43, #46`) are adjudicated to **Rank 8** (`B = 0.3636`), matching all 330 `ضعيف` entries in Task A v1.4.
- **Sufyan ibn Husayn (`#39`, `E2437`) Text Correction:** Local Taqrib text reads `ثقة في غير الزهري باتفاقهم` (*trustworthy in narrations OTHER THAN al-Zuhri*), not *in al-Zuhri*; corroborated by Ahmad ibn Hanbal in Shamela4 (`2467`).
- **Rank 3 Scholarly Epithets (`#36, #37, #38`):** `ثقة فقيه فاضل` (`#36` Ata, `#37` Tawus) and `ثقة إمام في التفسير وفي العلم` (`#38` Mujahid) are adjudicated to **Rank 3** because `فقيه`, `فاضل`, and `إمام في التفسير` denote juristic/exegetical eminence rather than reinforced hadith transmission precision.
- **Muqatil ibn Sulayman (`#48`, `E6868`):** Adjudicated to **Rank 12** (`كذبوه وهجروه`), matching all 13 other standalone `كذبوه` entries in Taqrib and corroborated by severe fabrication/isnad-switching reports in Shamela4 (`11017`).
- **al-Harith al-A'war (`#17`, `E1029`):** Adjudicated to **Rank 8** (`وفي حديثه ضعف`), because Ibn Hajar restricts al-Sha'bi's accusation to partisan opinion (`كذبه الشعبي في رأيه`), while automated Task A v1.4 intentionally preserves abstention (`GUARD-UNCOVERED-COMPLEX`).
- **Layth ibn Abi Sulaym (`#19`, `E5685`) & Amr ibn Shimr (`#49`, `sid=12587`):** Layth retains Stage 1 Baseline **Rank 4** (`صدوق`, `B = 0.7273`) with mandatory Stage 2 fatal *ikhtilat* penalty (`اختلط جدا ولم يتميز حديثه فترك`); Amr ibn Shimr remains `EXTERNAL` (absent from Taqrib; al-Ghada'iri `1/3/3` `ضعيف` + 21 Sunni jarh clauses in Shamela4 `12587`).

## 2. Adjudicated Stage 1 Rank Counts (`N = 50`)
- Adjudication status counts: `{'adjudicated_from_queue': 13, 'confirmed_automated_and_source_aligned': 37}`
- Stage 1 Rank distribution: `{'10': 2, '11': 1, '12': 1, '2': 25, '3': 6, '4': 5, '5': 3, '8': 6, 'EXTERNAL': 1}`
