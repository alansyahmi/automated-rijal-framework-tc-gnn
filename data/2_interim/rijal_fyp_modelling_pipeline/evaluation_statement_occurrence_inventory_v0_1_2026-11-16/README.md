# Evaluative statement phrase occurrences v0.1

**Status:** exact-string occurrence index for discovery and source review. No human statement descriptors, ranks, or numeric scores are assigned.

## Scope and method

The scan covers 8,827 numbered entries in the local Taqrib entry index. It records every exact Unicode substring occurrence for the 203 phrase strings in the current rank-vocabulary candidate inventory plus two separately identified praise cues: جبل الحفظ and إمام الدنيا في فقه الحديث. The combined praise wording جبل الحفظ وإمام الدنيا في فقه الحديث remains in the original phrase inventory; the two added cues let the reviewer inspect each component as well.

No Arabic normalization, stemming, fuzzy matching, or semantic classification is performed. Character offsets are zero-based Python Unicode character positions; the end position is exclusive. The Arabic-letter-bounded flag only indicates whether an Arabic letter directly touches the match boundary. It does not establish a semantic word or statement boundary.

## Files

- PHRASE_OCCURRENCES_V0_1.csv contains the full local entry text, exact matched text, entry/page locator, offsets, short neighboring context, and blank human review fields.
- PHRASE_OCCURRENCE_SUMMARY_V0_1.csv gives exact and Arabic-letter-bounded occurrence counts by candidate phrase.
- MANIFEST.json and MANIFEST.sha256 record the source and output hashes.

Candidate strings can overlap in one entry. For example, a standalone praise cue can also match inside a longer compound. Counts across candidate strings therefore overlap and are not counts of distinct claims, narrators, or independent observations. The candidate list remains a seed inventory, not an exhaustive census of all praise or criticism wording.

The candidate inventory's rank suggestions and source anchors are preserved only as unverified discovery metadata. The human statement-family, domain, claim-content, claim-mode, wording-force, consensus-wording, review-status, and note columns are blank. This package does not update the 12-rank labels or enable extraction rules.

## Source limits

The source is the local numbered-entry index from the Shamela4 Taqrib extraction. Its text is a digital transcription, not a visual check against printed page images. The inventory excludes unnumbered page chunks. Phrase occurrence counts must not be presented as total corpus coverage or as the number of validated evaluation statements.

## Next review

Review phrases and full entry contexts by statement construction. Add or revise candidate strings in a later version only after preserving exact wording and provenance. Then manually code the statement-level descriptors; keep canonical rank decisions and any numeric scoring separate.
