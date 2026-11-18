# Boundary Pilot Annotation Audit — 15 November 2026

## Audited artifact

- Reviewed copy: `BOUNDARY_PILOT_REVIEWER_ANNOTATED_2026-11-15.csv`
- SHA-256: `c8eb9d73e04cb180d02e0fbba886f7474d94c1c91400da2a9613845ca15e1645`
- Audit scope: source fidelity, span coverage/order, field completion, and consistency with `REVIEW_GUIDE.md`.
- No annotation cells or the reviewed CSV were changed during this audit.

## Summary

The annotation is a useful first pass. All 25 `entry_text_verbatim` values exactly match their corresponding entries in the local frozen `pages.jsonl` source. Every nonblank segment is itself present in the corresponding source entry and the segments occur in source order. No added Arabic wording was detected.

However, none of the 25 rows currently reconstructs the complete source entry when the segment fields are concatenated in order. Under the current guide, every row must include the numbered entry prefix and preserve spaces and punctuation, so this is a mechanical completeness issue before the work can be treated as complete. Nine rows also omit non-whitespace source content beyond the entry prefix.

## Checks and findings

| Check | Result |
| --- | --- |
| Cases and source locators | 25 cases; 25 distinct locators |
| Original source strings | 25/25 match the local source exactly |
| Entered span text | All spans are exact substrings in source order |
| Exact full-entry reconstruction | 0/25 under the current guide |
| Human completion values | All rows say `complete`; all confidence values say `100%` |
| Segment role for every filled span | No: TB-011 segment 7 has text but a blank role |

All rows omit their entry-number prefix (`١-`, `٣-`, etc.). Spaces between spans are also missing in many rows. If entry prefixes are meant to be treated only as locators, amend the protocol explicitly; as currently written, the full entry must be segmented and reconstructable.

### Additional source text omitted

Besides each entry prefix and spacing, these rows omit source content:

| Case | Omitted source text |
| --- | --- |
| TB-001 | trailing reference symbols `د فق` |
| TB-006 | `آخر` in `البغدادي آخر متروك` |
| TB-007 | generation phrase `من العاشرة` |
| TB-010 | `زاهد من الحادية عشرة` |
| TB-011 | brackets around `[الوهبي]` and the word `يكنى` before `أبا عبيد الله` |
| TB-016 | trailing reference symbols `ت س` |
| TB-020 | trailing reference symbol `ق` |
| TB-022 | conjunction `ثم` in `المدني ثم الكوفي` |
| TB-024 | brackets around `[ذو البطين]` and the conjunction `و` in `وهو ابن خمس وسبعين` |

These are transcription-coverage findings, not rank decisions.

## Role and metadata consistency

The guide specifies broad role labels, but the CSV uses a more granular, informal vocabulary such as `full_name`, `nisba`, `kunya`, `death_year`, `source_citation`, `source_citations`, `assessment_or_grade`, and `grade_or_assessment`. Fine-grained name and biography labels may be useful, but they should be documented as subroles or mapped consistently to the guide before quantitative analysis. In particular, `assessment_or_grade` and `grade_or_assessment` should not remain duplicate labels, and source symbols should use one consistent label corresponding to `source_or_transmission_symbol`.

Specific cases for review:

- **TB-009:** `عن يزيد ابن هارون` is included in `full_name`, while the possible identification `يحتمل أن يكون هو ابن خالد الخلال` is called a biographical fact. Consider separating the name from the transmission/identification wording and treating the latter as an identity-disambiguation note or `uncertain`.
- **TB-011:** segment 7 contains `من الحادية عشرة` but has no role. The brackets in `[الوهبي]` and `يكنى` are missing from the segmentation.
- **TB-014:** `فقيه` is labelled as occupation and `حجة` as a qualification. These role assignments are not self-evident from the guide; `حجة` appears assessment-like rather than a qualifier. Keep the assessment cluster together or mark the boundary/role uncertain pending a clearer rule.
- **TB-015:** `صاحب حديث` is labelled as an assessment qualification. It may be a descriptive status rather than wording that qualifies `صدوق`; use `other_text` or `uncertain` unless the codebook defines it more precisely.
- **TB-016:** `آبي اللحم بالمد ... من الإباء` is labelled partly as a kunya/status span. The entry presents an epithet with a pronunciation/word explanation, followed by the separate status `صحابي`. Re-segment that distinction; do not infer a death year from the event reference in this boundary task.
- **TB-018:** `خت` is included in the generation span `من السابعة أيضا خت`; separate the generation wording from the trailing reference symbol.
- **TB-021 and TB-022:** trailing symbols (`ت ق`, `ت س`) are labelled as biographical facts. They are reference/transmission symbols; use the source-symbol role. TB-022 also needs `ثم` restored.
- **TB-023:** `تفرد الحسن بالرواية عنه` is a transmission statement. The text alone does not make it an explicit criticism, so avoid assigning the criticism role without a stated reason; `other_text` or `uncertain` is safer for this pilot.
- **TB-024:** the note that `الأمير` means commander is based on a quick web search, and the TB-016 note infers a death year from the event. These are outside the boundary task. Keep such interpretations separate and explicitly provisional; the CSV should capture source wording and span roles only.
- **TB-020:** the proposed alternate full name is an interpretation of `وقيل اسم أبيه إسماعيل`, not wording present as a complete alternate name in the entry. Preserve the phrase as written and label the proposed reconstruction as a hypothesis if retained in notes.

The entries use `boundary_review_complete=complete` and `boundary_confidence=100%`, while the guide asks for `yes` and one of `high`, `medium`, or `low`. The current values communicate certainty, but are outside the documented response values. Once the segmentation is repaired, use the guide's values or update the guide to accept the intended alternatives.

## Recommended next step from the initial audit

Keep this reviewed copy immutable. Make a separate corrected working copy; restore omitted source text and spacing, ensure the ordered segments concatenate exactly to the original entry, add the missing TB-011 role, and harmonize or document the role vocabulary. Revisit the flagged role decisions without assigning any of Ibn Ḥajar's twelve ranks. Then rerun the same mechanical checks before freezing a revised annotation snapshot.

This audit assesses textual segmentation only. It does not establish historical attribution, the truth of any biographical statement, narrator reliability, or suitability as a model target.

## Follow-up repair

At the user's request, a separate corrected draft was prepared while preserving the reviewed submission above byte-for-byte.

- Corrected copy: `BOUNDARY_PILOT_REVIEW_CORRECTED_2026-11-15.csv`
- Guide addendum: `REVIEW_GUIDE_ADDENDUM_V1_1.md`
- Corrected-copy SHA-256: `cd664598d5a3573b863e2d79467b6069cf77927248a9a371be9c018cab0b3e6b`
- Verification: all 25 segment sequences reconstruct their local source entry exactly; all roles are populated and use the documented vocabulary plus `source_entry_number`.
- Human confirmation remains pending in the corrected copy. The original values `complete` and `100%` are preserved in separate columns and are not carried over as confirmation of the repairs.

Repairs restored the numbered entry marker, exact spacing, punctuation, omitted content, and trailing reference symbols. Clear assessment/qualification boundaries and reference-symbol roles were regularized. The possible identification in TB-009, reported name wording in TB-016, and external/inferential reviewer notes remain explicitly uncertain or out of scope. No rank was assigned.

## Follow-up: granular-role copy v1.2

Following the reviewer's request to retain fine-grained distinctions, a second derivative copy adds `segment_N_subrole` beside each broad `segment_N_role`:

- Copy: `BOUNDARY_PILOT_REVIEW_CORRECTED_GRANULAR_2026-11-15.csv`
- Guide: `REVIEW_GUIDE_ADDENDUM_V1_2_GRANULAR.md`
- SHA-256: `168d7f3ad5b9ea77bc19b56215e69d2acee157719038424ce01c5dd73eedcafe`
- Verification: 25 cases, 228 nonblank spans, all 25 rows reconstruct the exact source entry, and every span has both a parent role and a subrole.

This preserves details such as name/lineage, kunya, nisba, residence, death wording, assessment qualifiers, and source symbols while keeping the broad role set comparable. The subroles are structural metadata. The 25-case purposive pilot is not a training or evaluation sample, and its detailed labels do not add or replace any of Ibn Ḥajar's twelve ranks. The v1.2 copy also remains pending human confirmation; the original reviewer values and v1.1 corrected copy remain unchanged.

## User-approved freeze and shadow run

The user then explicitly authorized freezing the AI-assisted boundary annotations. The immutable snapshot is `frozen_2026-11-15/TAQRIB_BOUNDARY_ANNOTATIONS_FROZEN_V1.csv`; its manifest records the user authorization, preserved uncertainty, and confidence mapping. The frozen CSV SHA-256 is `c7d808496802ba6ba04aac2bc2778f4acf0a04f5996e7866458b92e46d59a05f`.

The subsequent full-source cue shadow scan is documented in `../rank_label_shadow_run_v1_2026-11-15/RUN_REPORT.md`. It extracted 8,827 numbered entry strings from the 688-page local file, observed three repeated page/entry-number keys (so internal entry IDs include source-chunk position), and recorded 8,332 exact occurrences of the 33 source-inventory cue strings plus 5,831 occurrences of the existing disabled registry rules. These are cue occurrences, not rank labels or rank-coverage counts. Zero labels were assigned or auto-accepted; exact statement boundaries and contextual rank conditions remain unresolved by the scan.
