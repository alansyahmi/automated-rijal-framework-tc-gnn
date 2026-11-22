# Methodology Framing & Viva Defense Notes (`taqrib-oriented`)

## 1. "Did You Annotate the Dataset Yourself?" (Label Provenance Defense)

**Short Answer:** **No.** Neither the *Taqrīb* baseline ranks nor the *Taḥrīr* verdict labels are manually invented or subjectively annotated by us.

### A. *Taqrīb al-Tahdhīb* (`3076`) Baseline Ranks (`5,680 / 8,827`)
- **Source of Standard:** Ibn Ḥajar al-ʿAsqalānī explicitly defined the 12 *marātib* (ranks `1–12`) and their canonical Arabic terms in the introduction of *Taqrīb al-Tahdhīb*.
- **Operationalization:** `build_task_a_deterministic_targets_v1_4.py` performs **deterministic rule-based mapping** of unambiguous entries onto Ibn Ḥajar's own 12-rank taxonomy (matching the quantitative approach in Bilgin, 2026).
- **Anti-Guessing Guard:** Rather than forcing subjective labels onto conditional or compound entries, `v1.4` **intentionally abstains** on `3,147` entries (e.g., `GUARD-R6-MAQBUL`: `1,581` entries where `مقبول` is conditional on corroboration; `GUARD-UNCOVERED-COMPLEX`: `813` multi-clause entries).

### B. *Taḥrīr Taqrīb al-Tahdhīb* (`8246`) Scholar-Authored Labels
- **Source of Labels:** Co-authored by Shaykh Shuʿayb al-Arnāʾūṭ and Dr. Bashshār ʿAwwād Maʿrūf, *Taḥrīr* systematically audits *Taqrīb* entry-by-entry using an explicit editorial convention stated in its introduction:
  - **No `•` bullet (`agreed_no_bullet`):** Explicit agreement with Ibn Ḥajar's *Taqrīb* entry (`5,766` entries).
  - **`• بل:` (`dissent_bal`):** Explicit scholarly override with a revised verdict (`2,621` entries, including `1,349` entries where *Taqrīb* `v1.4` abstained).
  - **`• قوله` / `•` (`qualification_qawluhu` / `other_commentary`):** Phrase-level qualification or correction (`111` + `325` entries).
- **Framing for Thesis & Viva:** Describe this as **"rule-based operationalization of classical and scholarly taxonomies"** (not manual annotation). The only empirical check required is **extraction accuracy** (verifying the parser reads the Arabic text accurately — already verified at `120/120` on the blind `v1.4` sample, and `99.95%` alignment with *Taḥrīr*).

### C. Why `main` v2.0's 120-Narrator Dual-Reviewer ESA Pilot Is Dropped (`DEC-007`)
- **Archival Notice:** Prior to the `taqrib-oriented` pivot (`DEC-004`), `origin/main` drafted a 120-narrator manual ESA pilot (`TRAIN_120_STRATIFIED_ESA_PILOT_WORKSHEET_V2_0.csv` with a `STOP-AND-APPROVE` gate under the earlier critic-level Task B framing). That pilot is **formally superseded (`DEC-007`)**.
- **Justification:** In the *Taqrīb* → *Taḥrīr* paradigm, reliability grades and overrides are authored directly by named classical and modern *ḥadīth* authorities (Ibn Ḥajar, al-Arnāʾūṭ, Maʿrūf), so inventing subjective dual-reviewer labels on modern summaries would replace scholarly ground truth with annotator opinion. Instead, label validity rests on: (1) blind extraction QA (`120/120` Bilgin rules, `99.95%` `3076↔8246` alignment, Gold-50 adjudication), and (2) independent external validation against al-Dhahabī's *al-Kāshif* (`1616`, `N = 1,994` `paired_clean` non-verbatim / non-citing narrators out of `5,640` linked).

---

## 2. *Taḥrīr* (`8246`) ↔ *Taqrīb* (`3076`) Alignment Coverage (`v1`)

- **Matched:** `8,823 / 8,827` (**99.95%**) via `extract_tahrir_taqrib_alignment_v1.py`.
- **Audit of the Remaining 4 Unmatched Entries (`0.05%`):**
  1. `E4397` (*ʿUbayd b. Naḍlah*): Present in `8246` Part 2, p. 423 with digit swap + spelling variant (`٣٤٩٧ - عبيد بن نضيلة`); no `•` bullet (*Taḥrīr* agrees: `ثقة`).
  2. `E7859` (*Yūsuf b. al-Ḥakam b. Abī ʿAqīl*): Present in `8246` Part 4, p. 132 as `٧٨٥٩ ب -`; no `•` bullet (*Taḥrīr* agrees: `مقبول`).
  3. `E8522` & `E8523`: *Mubhamāt* (unnamed narrators) formatted as `° -` cross-references in `8246`.

---

## 3. Corpus Alignment Digitization-Noise Audit (< 0.6%)

A systematic audit across all `8,827` aligned rows in `TAHRIR_TAQRIB_ALIGNED_8827_V1.csv` confirmed **>99.4%** structural cleanliness, with total Shamela `8246` digitization edge cases confined to ~45 entries (< 0.6%):
1. **Swallowed out-of-range OCR entry headers (`3` rows):** `E1803` swallowed `١١٨٠٤` (`1804`), `E5509` swallowed `٩٣١٠` (`5510`), and `E5339` swallowed `٩٣٤٠` (`5340`).
2. **Page-break missing-header bleed-over (`E2615` / `E2616`):** On `E2615` (*al-Aʿmash*), Shamela `8246` dropped the opening header of `E2616` (*Sulaymān b. Mūsā al-Ashdaq*) at a page break, attaching `2616`'s commentary (`• بل: فقيه صدوق حسن الحديث`) onto `E2615`. (In frozen v2, TC-GNN still scored *al-Aʿmash* accurately at `89.41`; in `v3`, `E2615`/`E2616` and the 28 name-fallback pairs are flagged `suspect_alignment` and excluded from evaluation.)
3. **ASCII `* بل:` / `° بل:` overrides (`11` rows):** Early entries (`E0138`, `E0143`–`E0145`, `E0153`, `E0155`, `E0159`, etc.) used ASCII `*` instead of Unicode `•`, leaving them marked `agreed_no_bullet`.
4. **Duplicate `normalized_name_fallback` collisions (`28` pairs = `56` rows):** Adjacent namesakes matched to an already-claimed `exact_entry_number` entry when the target entry's number was missing/corrupted in `8246`.

