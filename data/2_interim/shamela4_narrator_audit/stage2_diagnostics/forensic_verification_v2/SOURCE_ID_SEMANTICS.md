# Source-ID semantics: evidence and limits

## A. Not unique work identifiers

Established at the observed-string level: one source ID can be associated with multiple citation strings (355 IDs in the occurrence export), and the same exact citation string is associated with multiple source IDs (10480 citation strings). Therefore the integer is not a unique work-title identifier. This says nothing by itself about a higher-level database entity.

## B. Apparent occurrence/record behavior

160 IDs occur across more than one narrator row in the extracted `garh` entries. This shows reuse across records. The integer appears as the third element of the original three-element arrays, alongside the two text fields; that placement is direct observation. It is consistent with an occurrence/citation-record key, but does not prove whether the key identifies a citation, a passage, a document row, or a compiler-level source object.

IDs span 23275–832551 in observed values. Among 54,334 distinct numeric IDs in extracted entries, adjacent sorted values differ by 1 for 0.2% of neighboring pairs; common observed gaps include `[(2, 30095), (4, 7814), (6, 3115), (3, 2267), (8, 1714), (10, 1100), (5, 935), (12, 747)]`. This arithmetic pattern alone does not prove sequential allocation or insertion order. The available Parquet columns are `id`, `short_name`, `long_name`, `narrator_type`, `biography_text`, and `criticism_text`; no identifier dictionary or source-ID metadata column is present in this file.

## C. Confirmed entity semantics

Not established. No external Shamela source-ID schema, database table definition, or compiler documentation is included in the inspected corpus files. Thus a specific database entity cannot be named confidently.

Counts above describe extracted string/tuple associations, not bibliographic truth. Multiline and multi-locator records may contain multiple works or quotation excerpts; they were not merged or corrected.
