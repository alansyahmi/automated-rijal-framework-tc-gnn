# Shamela4 narrator audit

- Audit timestamp UTC: 2026-11-09T17:31:59.101373+00:00
- Input file: C:\Projects\automated-rijal-framework-tc-gnn\data\1_raw\Shamela4_Full_DB\_meta\narrators.parquet
- File bytes: 7,963,509
- SHA-256: 82657fbae4e73a6514258102293b95be4e6031ab45faa65d69dad14cdc51ef34
- Parquet rows / iterated: 18,989 / 18,989

## JSON and missingness

- Biography JSON statuses: {'valid': 18989}
- Criticism JSON statuses: {'null': 3829, 'valid': 15160}
- Null narrator_type: 9,799
- Null criticism_text: 3,829

## Biography field coverage

| Field | Records |
|---|---:|
| النسب | 16,885 |
| الكنية | 10,323 |
| تاريخ الوفاة | 9,499 |
| الرتبة عند ابن حجر | 8,185 |
| طبقة رواة التقريب | 8,178 |
| علاقات الراوي | 7,492 |
| الرتبة عند الذهبي | 5,370 |
| بلد الإقامة | 4,326 |
| بلد الوفاة | 2,057 |
| اللقب | 1,733 |
| بلد الرحلة | 1,699 |
| تاريخ الميلاد | 1,429 |
| الشهرة | 1,291 |
| المذهب العقدي | 936 |
| بلد الميلاد | 240 |
| تاريخ الرحلة | 211 |

## Quotation and group structure

- ghar occurrences: 165,862
- Unique exact quotes: 108,904
- Repeated exact quote strings: 16,504
- Occurrences in repeated quote strings: 73,462
- Evaluator-group quotation occurrences: 165,862
- Distinct narrator/evaluator-group appearances: 87,463
- Distinct group labels: 2,804
- fwaed occurrences: 15,963

## Source ID/title string checks

- Source IDs with citations: 54,334
- IDs associated with multiple normalised titles: 355
- Normalised titles associated with multiple IDs: 47

These are string-level diagnostics, not proof of bibliographic identity.

## Duplicate diagnostics

- Unique narrator/group/quote/source combinations: 164,983
- Repeated documentary combinations: 736
- Excess duplicate occurrences: 879
- Same narrator + quote + source assigned to multiple groups: 11,900

Do not automatically delete these records.

## Shape warnings

- None detected.

## Interpretation cautions

- Group labels are not verified historical-speaker attribution.
- One quotation occurrence is not necessarily one independent evaluation.
- Normalised title matching is heuristic, not bibliographic authority control.
- Existing grades are not automatically clean target labels.
- Raw Parquet input was not modified.
