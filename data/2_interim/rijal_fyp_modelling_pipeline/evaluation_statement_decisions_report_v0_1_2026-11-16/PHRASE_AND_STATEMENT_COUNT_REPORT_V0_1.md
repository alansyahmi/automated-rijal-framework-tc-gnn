# Evaluative Statement Phrase and Statement Count Report v0.1

**Status:** verified count report over consolidated Batch 01 + Batch 02 user decisions (`916` unique review cases; `866` unique source entries). Zero canonical ranks or numeric scores assigned.

## 1. Inclusion Rules and Denominators (Read Before Interpreting Any Count)

1. **Corpus inventory denominator (`PHRASE_OCCURRENCES_V0_1.csv`):** `8,827` numbered local *Taqrib* entries yielded `11,478` raw exact-substring hits across `205` candidate phrase strings (`203` from candidate vocabulary v0.1 + `2` discussion praise modifiers). Deduplicating overlapping character intervals within each entry produced `9,508` overlap-span cases (`UNIQUE_OVERLAP_SPAN_REVIEW_FRAME_V0_1.csv`).
2. **Reviewed sample inclusion rules:**
   - **Batch 01 (`33` occurrences):** purposive illustrative selection (first Arabic-letter-bounded hit, or first exact hit) for 33 discussion phrases, mapping onto `30` overlap-span cases (`3` of which overlap Batch 02 selections).
   - **Batch 02 (`889` overlap-span cases):** stratified selection excluding the `33` Batch 01 accepted `occurrence_id`s:
     - `rare_phrase_exhaustive` (**142** phrases, `<= 15` distinct corpus entries): **all** remaining hits included exhaustively.
     - `common_phrase_sampled` (**55** phrases, `> 15` distinct corpus entries): **up to 10** distinct entries sampled deterministically via SHA-256 ordering (`seed = shamela4-occ-review-batch02-v0.1-2026-11-16`), one earliest occurrence per entry.
     - `no_exact_occurrences` (**8** phrases): `0` hits in the local numbered-entry index.
3. **Consolidated reviewed denominator:** `916` unique overlap-span `review_case_id`s (`866` distinct source entries; `922` lossless decision ledger rows). Inside those `916` cases, **`1614`** total raw phrase hits are linked (`1009` directly selected/accepted hits + `605` co-occurring overlapping hits).
4. **Non-independence warning:** Because phrase hits overlap (e.g., `ثقة`, `حافظ`, and `ثقة حافظ` all fire on the same span) and common phrases are capped at `10` entries while rare phrases are exhaustive, **do not sum per-phrase counts** or treat sample shares as corpus-wide prevalence.

## 2. Key Per-Phrase Findings (`PER_CANDIDATE_PHRASE_REVIEW_COUNTS_V0_1.csv`)

### A. Phrases with Direct `unrelated_substring` False Positives

- `VOC-033` (`ثبت`, `common_phrase_sampled`): **5** of `11` direct cases (`211` raw corpus hits vs. `149` word-bounded hits).
- `VOC-027` (`بدري`, `common_phrase_sampled`): **6** of `11` direct cases (`33` raw corpus hits vs. `10` word-bounded hits).

### B. Phrases with Non-Subject Referents (Relatives or Third Parties in Direct Cases)

- `VOC-013` (`أم المؤمنين`): **5** of `15` direct cases refer to someone other than the entry subject (e.g., sister/aunt `أم المؤمنين`, father/ancestor `الصحابة`/`الصحابي`, Talhah `أحد العشرة`, Anas `صحابي معروف`, unnamed chain woman `لا تعرف`, or Baqiyyah's teachers `مجهول`).
- `VOC-081` (`صحابي معروف`): **1** of `9` direct cases refer to someone other than the entry subject (e.g., sister/aunt `أم المؤمنين`, father/ancestor `الصحابة`/`الصحابي`, Talhah `أحد العشرة`, Anas `صحابي معروف`, unnamed chain woman `لا تعرف`, or Baqiyyah's teachers `مجهول`).
- `VOC-006` (`أحد العشرة`): **1** of `8` direct cases refer to someone other than the entry subject (e.g., sister/aunt `أم المؤمنين`, father/ancestor `الصحابة`/`الصحابي`, Talhah `أحد العشرة`, Anas `صحابي معروف`, unnamed chain woman `لا تعرف`, or Baqiyyah's teachers `مجهول`).
- `VOC-128` (`لا يعرف ولم يسم`): **1** of `7` direct cases refer to someone other than the entry subject (e.g., sister/aunt `أم المؤمنين`, father/ancestor `الصحابة`/`الصحابي`, Talhah `أحد العشرة`, Anas `صحابي معروف`, unnamed chain woman `لا تعرف`, or Baqiyyah's teachers `مجهول`).
- `VOC-121` (`لا أعرفه`): **1** of `3` direct cases refer to someone other than the entry subject (e.g., sister/aunt `أم المؤمنين`, father/ancestor `الصحابة`/`الصحابي`, Talhah `أحد العشرة`, Anas `صحابي معروف`, unnamed chain woman `لا تعرف`, or Baqiyyah's teachers `مجهول`).
- `VOC-130` (`لم أقف على اسمها ولا على حالها`): **1** of `1` direct cases refer to someone other than the entry subject (e.g., sister/aunt `أم المؤمنين`, father/ancestor `الصحابة`/`الصحابي`, Talhah `أحد العشرة`, Anas `صحابي معروف`, unnamed chain woman `لا تعرف`, or Baqiyyah's teachers `مجهول`).
- `VOC-145` (`لين`): **1** of `10` direct cases refer to someone other than the entry subject (e.g., sister/aunt `أم المؤمنين`, father/ancestor `الصحابة`/`الصحابي`, Talhah `أحد العشرة`, Anas `صحابي معروف`, unnamed chain woman `لا تعرف`, or Baqiyyah's teachers `مجهول`).
- `VOC-125` (`لا يعرف`): **1** of `11` direct cases refer to someone other than the entry subject (e.g., sister/aunt `أم المؤمنين`, father/ancestor `الصحابة`/`الصحابي`, Talhah `أحد العشرة`, Anas `صحابي معروف`, unnamed chain woman `لا تعرف`, or Baqiyyah's teachers `مجهول`).
- `VOC-127` (`لا يعرف حالها`): **1** of `11` direct cases refer to someone other than the entry subject (e.g., sister/aunt `أم المؤمنين`, father/ancestor `الصحابة`/`الصحابي`, Talhah `أحد العشرة`, Anas `صحابي معروف`, unnamed chain woman `لا تعرف`, or Baqiyyah's teachers `مجهول`).
- `VOC-146` (`لين الحديث`): **1** of `10` direct cases refer to someone other than the entry subject (e.g., sister/aunt `أم المؤمنين`, father/ancestor `الصحابة`/`الصحابي`, Talhah `أحد العشرة`, Anas `صحابي معروف`, unnamed chain woman `لا تعرف`, or Baqiyyah's teachers `مجهول`).
- `VOC-124` (`لا تعرف`): **2** of `11` direct cases refer to someone other than the entry subject (e.g., sister/aunt `أم المؤمنين`, father/ancestor `الصحابة`/`الصحابي`, Talhah `أحد العشرة`, Anas `صحابي معروف`, unnamed chain woman `لا تعرف`, or Baqiyyah's teachers `مجهول`).
- `VOC-022` (`الصحابة`): **1** of `10` direct cases refer to someone other than the entry subject (e.g., sister/aunt `أم المؤمنين`, father/ancestor `الصحابة`/`الصحابي`, Talhah `أحد العشرة`, Anas `صحابي معروف`, unnamed chain woman `لا تعرف`, or Baqiyyah's teachers `مجهول`).
- `VOC-023` (`الصحابي`): **1** of `10` direct cases refer to someone other than the entry subject (e.g., sister/aunt `أم المؤمنين`, father/ancestor `الصحابة`/`الصحابي`, Talhah `أحد العشرة`, Anas `صحابي معروف`, unnamed chain woman `لا تعرف`, or Baqiyyah's teachers `مجهول`).

### C. Common Sampled Phrases Frequently Embedded Inside Larger Statements (`>= 5` of `10` direct cases)

- `VOC-044` (`ثقه`): **10** `component_of_larger_statement` vs. **1** `complete_statement` out of `11` direct cases.
- `VOC-173` (`وثقه`): **10** `component_of_larger_statement` vs. **0** `complete_statement` out of `10` direct cases.
- `VOC-145` (`لين`): **8** `component_of_larger_statement` vs. **2** `complete_statement` out of `10` direct cases.
- `VOC-125` (`لا يعرف`): **8** `component_of_larger_statement` vs. **3** `complete_statement` out of `11` direct cases.
- `VOC-133` (`له صحبة`): **7** `component_of_larger_statement` vs. **3** `complete_statement` out of `10` direct cases.
- `VOC-048` (`حافظ`): **10** `component_of_larger_statement` vs. **0** `complete_statement` out of `10` direct cases.
- `VOC-126` (`لا يعرف حاله`): **10** `component_of_larger_statement` vs. **1** `complete_statement` out of `11` direct cases.
- `VOC-033` (`ثبت`): **5** `component_of_larger_statement` vs. **1** `complete_statement` out of `11` direct cases.
- `VOC-084` (`صحابية`): **10** `component_of_larger_statement` vs. **0** `complete_statement` out of `10` direct cases.
- `VOC-199` (`يخطىء`): **7** `component_of_larger_statement` vs. **3** `complete_statement` out of `10` direct cases.
- `VOC-021` (`التشيع`): **6** `component_of_larger_statement` vs. **4** `complete_statement` out of `10` direct cases.
- `VOC-039` (`ثقة حافظ`): **11** `component_of_larger_statement` vs. **0** `complete_statement` out of `11` direct cases.
- `VOC-127` (`لا يعرف حالها`): **10** `component_of_larger_statement` vs. **1** `complete_statement` out of `11` direct cases.
- `VOC-035` (`ثقات التابعين`): **8** `component_of_larger_statement` vs. **2** `complete_statement` out of `10` direct cases.
- `VOC-063` (`سيء الحفظ`): **8** `component_of_larger_statement` vs. **2** `complete_statement` out of `10` direct cases.
- `VOC-152` (`متقن`): **8** `component_of_larger_statement` vs. **2** `complete_statement` out of `10` direct cases.
- `VOC-092` (`صدوق يخطىء`): **10** `component_of_larger_statement` vs. **0** `complete_statement` out of `10` direct cases.
- `VOC-066` (`شهد بدر`): **10** `component_of_larger_statement` vs. **0** `complete_statement` out of `10` direct cases.
- `VOC-067` (`شهد بدرا`): **10** `component_of_larger_statement` vs. **0** `complete_statement` out of `10` direct cases.
- `VOC-091` (`صدوق سيء الحفظ`): **10** `component_of_larger_statement` vs. **0** `complete_statement` out of `10` direct cases.
- `VOC-054` (`ذكره ابن حبان في ثقات التابعين`): **10** `component_of_larger_statement` vs. **0** `complete_statement` out of `10` direct cases.
- `VOC-059` (`رمي بالتشيع`): **10** `component_of_larger_statement` vs. **0** `complete_statement` out of `10` direct cases.
- `VOC-146` (`لين الحديث`): **10** `component_of_larger_statement` vs. **0** `complete_statement` out of `10` direct cases.
- `VOC-188` (`وثقه النسائي`): **10** `component_of_larger_statement` vs. **0** `complete_statement` out of `10` direct cases.
- `VOC-037` (`ثقة ثبت`): **11** `component_of_larger_statement` vs. **0** `complete_statement` out of `11` direct cases.
- `VOC-108` (`فيه لين`): **10** `component_of_larger_statement` vs. **0** `complete_statement` out of `10` direct cases.
- `VOC-112` (`قيل له صحبة`): **10** `component_of_larger_statement` vs. **0** `complete_statement` out of `10` direct cases.
- `VOC-157` (`مجهول الحال`): **10** `component_of_larger_statement` vs. **0** `complete_statement` out of `10` direct cases.
- `VOC-018` (`الإرجاء`): **10** `component_of_larger_statement` vs. **0** `complete_statement` out of `10` direct cases.
- `VOC-078` (`صحابي صغير`): **10** `component_of_larger_statement` vs. **0** `complete_statement` out of `10` direct cases.
- `VOC-202` (`يقال له صحبة`): **10** `component_of_larger_statement` vs. **0** `complete_statement` out of `10` direct cases.
- `VOC-023` (`الصحابي`): **10** `component_of_larger_statement` vs. **0** `complete_statement` out of `10` direct cases.
- `VOC-025` (`القدر`): **10** `component_of_larger_statement` vs. **0** `complete_statement` out of `10` direct cases.
- `VOC-076` (`صحابي جليل`): **10** `component_of_larger_statement` vs. **0** `complete_statement` out of `10` direct cases.
- `VOC-080` (`صحابي مشهور`): **10** `component_of_larger_statement` vs. **0** `complete_statement` out of `10` direct cases.
- `VOC-093` (`صدوق يهم`): **10** `component_of_larger_statement` vs. **0** `complete_statement` out of `10` direct cases.
- `VOC-186` (`وثقه العجلي`): **10** `component_of_larger_statement` vs. **0** `complete_statement` out of `10` direct cases.

## 3. Reviewed Statement-Text Summary (`REVIEWED_STATEMENT_TEXT_COUNTS_V0_1.csv`)

- Distinct `(statement_match_use, statement_text_verbatim, family, domain, content, mode, force)` combinations across the `916` reviewed cases: **230**.
- Top 15 reviewed statement forms in the sample (counts reflect sampling cap of 10 per common phrase plus overlap co-occurrence):

| `statement_text_verbatim` (or blank if unrelated) | `statement_match_use` | `statement_family` | Cases | Entries |
| --- | --- | --- | ---: | ---: |
| `ثقة حافظ` | `component_of_larger_statement` | `praise` | 19 | 19 |
| `لا يعرف حالها` | `component_of_larger_statement` | `unknownness` | 18 | 18 |
| `صدوق يخطىء` | `component_of_larger_statement` | `mixed` | 17 | 17 |
| `صدوق سيء الحفظ` | `component_of_larger_statement` | `mixed` | 16 | 16 |
| `كذبوه` | `complete_statement` | `criticism` | 15 | 15 |
| `ذكره ابن حبان في ثقات التابعين` | `component_of_larger_statement` | `praise` | 15 | 15 |
| `رمي بالتشيع` | `component_of_larger_statement` | `criticism` | 14 | 14 |
| `لين الحديث` | `component_of_larger_statement` | `criticism` | 14 | 14 |
| `ثقة ثبت` | `component_of_larger_statement` | `praise` | 13 | 13 |
| `ثقة متقن` | `component_of_larger_statement` | `praise` | 13 | 13 |
| `شهد بدرا` | `component_of_larger_statement` | `status_or_biography` | 13 | 13 |
| `صحابي مقل` | `component_of_larger_statement` | `status_or_biography` | 13 | 13 |
| `فيه لين` | `component_of_larger_statement` | `criticism` | 13 | 13 |
| `وثقه النسائي` | `component_of_larger_statement` | `praise` | 13 | 13 |
| `من مسلمة الفتح` | `complete_statement` | `status_or_biography` | 12 | 12 |
