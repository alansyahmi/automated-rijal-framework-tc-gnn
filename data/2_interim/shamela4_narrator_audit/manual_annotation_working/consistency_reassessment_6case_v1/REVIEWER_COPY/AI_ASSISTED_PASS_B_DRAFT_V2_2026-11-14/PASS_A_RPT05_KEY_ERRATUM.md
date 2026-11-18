# Pass A RPT-05 candidate-key erratum

**Status:** Additive erratum; the frozen Pass A CSV and its manifest are unchanged.

## Recorded mismatch

The six-case source packet defines the RPT-05 keys as:

| Packet key | Taqrib locator | Entry identity wording |
|---|---|---|
| CAND-01 | local corpus page 456, entry 5570 | `قيس ابن حفص آخر بصري سكن مصر يكنى أبا محمد` |
| CAND-02 | local corpus page 456, entry 5569 | `قيس ابن حفص التميمي الدارمي أبو محمد البصري` |

The frozen Pass A file records CAND-01 as confirmed using locator `3076; 382; 5569` and evidence text from entry 5569. It records CAND-02 as unresolved using locator `3076; 383; 5570` and text from entry 5570. Thus the evidence and locators in the two rows are associated with the opposite packet keys. This is a key-association defect in the frozen annotation record; it is not repaired here.

## Local evidence checked for this erratum

- HadithDB record 278: `قيس بن حفص بن القعقاع`; kunya `أبو محمد`; affiliation `التميمي, الدارمي مولاهم, البصري`; death `227 هـ`; stored Ibn Hajar field `ثقة له أفراد`.
- Taqrib entry 5569: `قيس ابن حفص التميمي الدارمي أبو محمد البصري ثقة له أفراد من العاشرة مات سنة سبع وعشرين`.
- Taqrib entry 5570: `قيس ابن حفص آخر بصري سكن مصر يكنى أبا محمد مقبول من الثانية عشرة مات سنة إحدى وثمانين تمييز`.
- The packet's identity excerpt for entry 5570 quotes al-Mizzi's Tamyiz entry 4900, describing the Basran who settled in Egypt and died in 281 AH. The excerpt is inherited packet text; this erratum did not independently reopen the cited al-Mizzi page.

## Provisional implication

The HadithDB biographical fields and original grade correspond to packet candidate CAND-02 / Taqrib 5569. Candidate CAND-01 / Taqrib 5570 is a distinct homonym candidate. This strongly suggests the Pass A identity values were attached to the wrong candidate keys. It does not authorize swapping cells in the frozen record. If the researcher confirms the packet key and source row, record a new dated correction/addendum linked to the original SHA-256; preserve the original freeze unchanged.
