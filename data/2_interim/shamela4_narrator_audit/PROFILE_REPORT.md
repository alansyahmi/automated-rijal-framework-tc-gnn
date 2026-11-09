# Shamela4 narrator audit

- Audit timestamp UTC: 2026-11-09T17:27:14.605201+00:00
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
| النسب | 0 |
| الكنية | 0 |
| تاريخ الوفاة | 0 |
| الرتبة عند ابن حجر | 0 |
| طبقة رواة التقريب | 0 |
| علاقات الراوي | 0 |
| الرتبة عند الذهبي | 0 |
| بلد الإقامة | 0 |
| بلد الوفاة | 0 |
| اللقب | 0 |
| بلد الرحلة | 0 |
| تاريخ الميلاد | 0 |
| الشهرة | 0 |
| المذهب العقدي | 0 |
| بلد الميلاد | 0 |
| تاريخ الرحلة | 0 |

## Quotation and group structure

- ghar occurrences: 0
- Unique exact quotes: 0
- Repeated exact quote strings: 0
- Occurrences in repeated quote strings: 0
- Evaluator-group quotation occurrences: 0
- Distinct narrator/evaluator-group appearances: 0
- Distinct group labels: 0
- fwaed occurrences: 0

## Source ID/title string checks

- Source IDs with citations: 0
- IDs associated with multiple normalised titles: 0
- Normalised titles associated with multiple IDs: 0

These are string-level diagnostics, not proof of bibliographic identity.

## Duplicate diagnostics

- Unique narrator/group/quote/source combinations: 0
- Repeated documentary combinations: 0
- Excess duplicate occurrences: 0
- Same narrator + quote + source assigned to multiple groups: 0

Do not automatically delete these records.

## Shape warnings

- garh_not_dict:list: 15,159
- fwaed_not_dict:list: 4,864

## Interpretation cautions

- Group labels are not verified historical-speaker attribution.
- One quotation occurrence is not necessarily one independent evaluation.
- Normalised title matching is heuristic, not bibliographic authority control.
- Existing grades are not automatically clean target labels.
- Raw Parquet input was not modified.
