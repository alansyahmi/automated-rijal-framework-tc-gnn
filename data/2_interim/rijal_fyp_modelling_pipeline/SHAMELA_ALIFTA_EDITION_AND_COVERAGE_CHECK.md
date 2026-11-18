# Shamela and Alifta Taqrīb Edition Check

**Checked:** 2026-11-14

**Scope:** compare the local Shamela extraction’s bibliographic metadata and available text with the official Shamela online record and the Alifta rank introduction.

## Finding

The local extraction and Shamela’s online book record identify the **same stated edition** of *Taqrīb al-Tahdhīb*: Muḥammad ʿAwwāma’s edition, published by Dār al-Rashīd in 1406/1986. Alifta’s book record identifies a **different edition**: edited by Abū al-Ashbāl Ṣaghīr Aḥmad Shāghif al-Pākistānī, Dār al-ʿĀṣimah, 1413 AH. They are presentations of the same work, but not the same stated published edition.

The rank introduction was absent from the local `pages.jsonl`/`toc.jsonl` snapshot and from the Shamela page sequence inspected, which starts at printed page 75 with generation material. However, a full searchable text copy attributed to Dorar.net states that it is based on the 1406 Muḥammad ʿAwwāma / Dār al-Rashīd edition and includes the twelve-rank introduction. Shamela’s own record identifies Dorar.net as its source. This explains how the rank passage can belong to the stated source text while being missing from this extracted/page-browsing segment.

The Alifta copy remains useful as a cross-edition comparison, not as the sole wording authority for the local edition. The two digital presentations show at least these rank-introduction variants: rank 5 has `تغير بأخرة` in the Dorar/ʿAwwāma text versus `تغير بآخره` in Alifta; rank 10 has `بقدح` versus `بقادح`. Preserve such differences rather than normalizing them. The Dorar copy is searchable text, not a scan of the 1406 printed pages, so printed-edition verification remains open.

## Evidence

### Local extraction

- `manifest.json` associates local book ID `3076` with Shamela ID `8609`. `book_metadata.json` identifies editor Muḥammad ʿAwwāma, Dār al-Rashīd, first edition 1406/1986, and 765 printed pages.
- The extraction manifest records 688 `pages.jsonl` rows. The first row has `shamela_page_id: 1` and `page_num: 75`; its body begins with `الطبقة الثانية عشرة` and describes generations. The rank-introduction anchors `فأما المراتب`, `أوثق الناس`, and `من أفرد بصفة` were not found in either local `pages.jsonl` or `toc.jsonl`.

### Official Shamela record

- The official [Shamela book record, ID 8609](https://shamela.ws/book/8609) lists Muḥammad ʿAwwāma, Dār al-Rashīd, first edition 1406/1986, 765 pages, and says the numbering follows the printed edition. This matches the local metadata.
- The official [Shamela text page 1](https://shamela.ws/book/8609/1) is labeled `ص75` and displays the generation-introduction passage that begins `الطبقة الثانية عشرة`. It does not display the twelve-rank introduction. The record’s visible table of contents begins with the alphabetical sections.
- Shamela’s book record says that differences from the Abū al-Ashbāl edition are attached in brackets and identifies the source as Dorar.net. The Shamela web sequence and this repository’s extracted page table do not expose the opening matter before printed page 75.

### Full Dorar text copy identified as the ʿAwwāma edition

- This [searchable PDF copy of the Dorar.net text](https://www.cia.gov/library/abbottabad-compound/D5/D5A0E6577B005798BF51654AFC60BB09_%C3%B3%CF%84%E2%8C%90%E2%88%A9%C3%A1%20%C6%92%CE%98%C3%B3%E2%88%9E%C2%BF%E2%88%A9%C3%A1%20%CE%A9%CE%B4%20%C6%92%CE%98%C3%9C%CE%98%CF%83%20%C2%A5%CE%98%CE%B5%20%C6%92%CE%98%C2%BD%E2%88%A9%CE%B4.pdf) states that it relies on the Muḥammad ʿAwwāma, Dār al-Rashīd, first edition 1406 AH, and that differences from the Abū al-Ashbāl 1416 edition are bracketed. Its searchable text includes `فأما المراتب` and all twelve definitions.
- This provides an edition-aligned digital text for transcription comparison. It is not a publisher-hosted scan and does not establish that every transcription detail matches the printed copy.

### Alifta record and rank text

- Alifta’s [book-details page](https://sunna.alifta.gov.sa/Book/Details?bookId=51) identifies its version as edited by Abū al-Ashbāl Ṣaghīr Aḥmad Shāghif al-Pākistānī, published by Dār al-ʿĀṣimah in 1413 AH.
- Alifta’s [author-introduction page](https://sunna.alifta.gov.sa/BookToc/ViewServicePage?bookId=51&mainId=506655) displays `فأما المراتب` and the twelve rank definitions, including the examples `أوثق الناس` and `من أفرد بصفة`.

## Limits and next source check

The metadata and text copies establish the declared edition/source chain, not direct physical-page verification. The full Dorar transcription is edition-aligned by its own note and by Shamela’s source statement, but it is not a printed scan. Before claiming visual verification of the 1406 edition, inspect its printed pages or a scan. Preserve the rank 5 and rank 10 textual variants rather than silently treating the Alifta and Dorar transcriptions as interchangeable.
