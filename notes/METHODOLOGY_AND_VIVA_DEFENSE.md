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

---

## 2. *Taḥrīr* (`8246`) ↔ *Taqrīb* (`3076`) Alignment Coverage (`v1`)

- **Matched:** `8,823 / 8,827` (**99.95%**) via `extract_tahrir_taqrib_alignment_v1.py`.
- **Audit of the Remaining 4 Unmatched Entries (`0.05%`):**
  1. `E4397` (*ʿUbayd b. Naḍlah*): Present in `8246` Part 2, p. 423 with digit swap + spelling variant (`٣٤٩٧ - عبيد بن نضيلة`); no `•` bullet (*Taḥrīr* agrees: `ثقة`).
  2. `E7859` (*Yūsuf b. al-Ḥakam b. Abī ʿAqīl*): Present in `8246` Part 4, p. 132 as `٧٨٥٩ ب -`; no `•` bullet (*Taḥrīr* agrees: `مقبول`).
  3. `E8522` & `E8523`: *Mubhamāt* (unnamed narrators) formatted as `° -` cross-references in `8246`.
