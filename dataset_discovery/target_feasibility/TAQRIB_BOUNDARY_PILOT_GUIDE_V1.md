# Taqrīb Textual-Boundary Pilot v1

## Purpose

This pilot comes before building the rank vocabulary. It asks where the text of a local *Taqrīb al-Tahdhīb* entry moves between a narrator's identifying information, assessment wording, qualifications, reported criticism, status or generation information, biography, and reference symbols.

The local entries often place assessment wording after a long name and identifying description, but position is only a cue. Identity clarifications can continue after the core name; a qualification or attributed comment can follow an assessment; and generation, dates, and transmission symbols may appear later. The pilot records boundaries without assigning Ibn Ḥajar rank numbers or proposing automated rules.

## Files and source

- `BOUNDARY_PILOT_REVIEW.csv` is the blank reviewer sheet. It contains 25 exact entry strings and source locators. All segment and review fields are blank.
- `MANIFEST.json` records the local input hash and generated-file hashes.
- The source is the repository's local `pages.jsonl` extraction for book ID 3076, associated in its metadata with Shamela book ID 8609. The pilot preserves each selected entry segment as stored in that extraction. It does not verify the printed edition or establish the history of the text.

## How to annotate

Review one entry at a time. Keep the raw `entry_text_verbatim` visible and do not edit it. Divide the complete entry into up to ten consecutive, non-overlapping text segments, in source order. Copy each segment exactly into `segment_N_text_verbatim`, preserving Arabic spelling, brackets, punctuation, and spaces. Assign one role to each segment in `segment_N_role`.

Use these role names:

- `narrator_name_or_identity` — name, lineage, kunya, nisba, or wording that identifies or distinguishes the narrator.
- `assessment_or_grade` — a direct assessment formula or evaluative description. Record wording only; do not assign one of the twelve ranks.
- `assessment_qualification_or_scope` — wording that qualifies, limits, or specifies the scope of an assessment.
- `specific_criticism_or_attributed_report` — a criticism, report, or evaluative statement explicitly attributed or reported in the entry.
- `status_or_companion_classification` — Companion, mukhadram, or another biographical status classification.
- `generation_classification` — wording such as `من العاشرة`.
- `biographical_fact` — dates, geography, teachers, students, life events, and other descriptive biography.
- `source_or_transmission_symbol` — trailing source abbreviations or transmission/reference symbols.
- `other_text` — text that does not fit the roles above but can be described without guessing.
- `uncertain` — a segment whose role or boundary cannot be decided confidently.

The role names are review labels for this pilot, not claims that Ibn Ḥajar used these as formal categories. A phrase such as `مجهول` should be segmented as written and classified by its local function; do not infer a numerical rank from it. If a qualification may instead be a separate criticism, choose the most defensible segmentation, use `uncertain` where appropriate, and explain the alternative in `reviewer_notes`.

Assign all text to a segment. Include punctuation and inter-word spaces in one of the adjacent spans so that joining the segment text fields in order reproduces `entry_text_verbatim` exactly. Do not normalize spelling, punctuation, or diacritics. If an entry needs more than ten segments, stop and note that in `reviewer_notes` rather than merging unlike material to fit the template.

Set `boundary_review_complete` to `yes` only after checking the whole entry. Use `high`, `medium`, or `low` for `boundary_confidence`; confidence concerns the segmentation and role labels, not whether the historical statement is true. Use `unassigned_or_overlapping_text_notes` to flag any characters you could not assign cleanly or any competing boundary; use `reviewer_notes` for the reason.

## Ambiguous cases

Mark a segment or boundary uncertain when, for example:

- the identifying name and explanatory wording cannot be separated confidently;
- it is unclear whether a phrase qualifies the preceding assessment or introduces a distinct criticism;
- a status expression could be read as either status or evaluation in its immediate context;
- an attributed report's boundary is unclear;
- punctuation or layout does not settle whether adjacent words belong together;
- the extracted entry itself appears incomplete or malformed.

Do not resolve uncertainty by looking up a preferred rank phrase or by forcing every phrase into a grade. Record the competing readings briefly. We can revise the boundary guide after reviewing the pilot; no original source wording should be changed.

## Sample and interpretation limits

The 25 entries are a fixed, purposive boundary-challenge sample selected from the local extract. They include short and long identifying blocks, simple and compound assessment wording, qualifications, attributed criticism, status and generation statements, biographical material, and entries with no obvious ordinary grade. They are not a random sample and cannot estimate how frequent each construction is across the book.

This exercise can help establish whether a human can apply a repeatable segmentation procedure to these source strings. It cannot establish the correctness of historical attribution, the truth of an assessment, narrator reliability, independent corroboration, or the suitability of records as machine-learning targets. It also does not validate an automated rank classifier. Only after the boundary decisions and rules are reviewed should we build the phrase inventory and count its coverage.
