#!/usr/bin/env python3
"""Prepare a small, source-linked AI advisory review batch from exact phrase hits.

The batch is a separate proposal artifact. It never writes to the occurrence
inventory or to a human annotation file, and it does not assign canonical ranks.
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PIPELINE = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline"
OCC_DIR = PIPELINE / "evaluation_statement_occurrence_inventory_v0_1_2026-11-16"
OCC_FILE = OCC_DIR / "PHRASE_OCCURRENCES_V0_1.csv"
OCC_MANIFEST = OCC_DIR / "MANIFEST.json"
CODEBOOK = PIPELINE / "evaluation_statement_layer_v0_1_2026-11-16/EVALUATIVE_STATEMENT_LAYER_CODEBOOK_DRAFT_V0_1.md"
PROPOSALS = PIPELINE / "evaluation_statement_layer_v0_1_2026-11-16/EVALUATIVE_STATEMENT_LAYER_EXAMPLE_PROPOSALS_V0_1.csv"
OUT = PIPELINE / "evaluation_statement_occurrence_review_v0_1_2026-11-16"

# family, domain, content, mode, wording force, consensus wording,
# referent note, span note, attribution, qualification, confidence, rationale
ADVISORY: dict[str, tuple[str, ...]] = {
    "بدري": (
        "status_or_biography", "companion_status", "status_assertion",
        "status_or_biographical_statement", "not_applicable", "not_applicable",
        "The entry subject (Aws ibn al-Samit).", "The cue is a complete token in this selected entry.",
        "", "", "medium",
        "The entry applies بدري to Aws in a biographical description. This is status information, not praise. It is a candidate status cue only; this review does not assign Rank 1 or verify the historical claim.",
    ),
    "أم المؤمنين": (
        "status_or_biography", "companion_status", "status_assertion",
        "status_or_biographical_statement", "not_applicable", "not_applicable",
        "Khadija, not the entry subject Hakim ibn Hizam.", "The phrase is a complete honorific but refers to another person.",
        "", "", "high",
        "In this occurrence, أم المؤمنين is an honorific for Khadija in the phrase ابن أخي خديجة. It does not assert this narrator's own status and must not be used as his Rank 1 cue.",
    ),
    "أفرط فيه ابن معين فكذبه": (
        "unresolved", "unresolved", "unresolved", "unresolved", "unresolved", "unresolved",
        "The entry subject is discussed; evaluator is Ibn Ma'in.", "Composite wording: compiler comment on severity plus an attributed liar accusation.",
        "ابن معين", "أفرط فيه", "low",
        "Do not turn أفرط فيه into a numeric decrement. The wording both characterizes Ibn Ma'in's judgement as excessive and reports فكذبه. Preserve the two components and leave their attributional/authorial relationship unresolved pending review.",
    ),
    "اتفق النقاد على تكذيبه": (
        "criticism", "honesty_veracity", "accusation_of_lying", "direct_statement",
        "plain_direct", "collective_agreement_claimed", "The entry subject.",
        "The phrase is a complete claim span in the selected entry.", "النقاد (unnamed collective)", "", "medium",
        "The text explicitly claims agreement among critics that the subject was called a liar. Record that wording as a claim of collective agreement; it does not independently establish consensus or calibrated confidence.",
    ),
    "أجمعوا على ثقته": (
        "praise", "general_reliability", "general_commendation", "reported_or_hedged_claim",
        "plain_direct", "unanimity_wording_claimed", "The entry subject.",
        "The phrase is nested under قال ابن عبد البر; retain the attribution with it.", "ابن عبد البر", "", "medium",
        "The local entry says قال ابن عبد البر before أجمعوا على ثقته. The proposal should therefore preserve a reported attribution, not code the phrase as an unqualified direct statement by the Taqrib compiler. The referents of أجمعوا remain unspecified, and the wording is not proof of independent consensus.",
    ),
    "ثبت": (
        "praise", "general_reliability", "general_commendation", "direct_statement",
        "plain_direct", "none", "The entry subject.",
        "In the selected passage this is part of ثقة ثبت, followed by a distinct transmission note.",
        "", "إلا أنه يرسل", "high",
        "The exact hit is not a complete standalone span here: it belongs to ثقة ثبت. Keep that compound intact for first-pass boundary review and record إلا أنه يرسل separately as potentially relevant transmission context.",
    ),
    "ثقة": (
        "praise", "general_reliability", "general_commendation", "direct_statement",
        "plain_direct", "none", "The entry subject.",
        "The exact hit is only one component of ثقة حافظ in the selected passage.",
        "", "حافظ", "high",
        "The occurrence supports a praise reading, but the exact hit is not the full assessment span. Preserve the compound ثقة حافظ; do not let a substring count stand for a complete statement.",
    ),
    "ثقة ثبت": (
        "praise", "general_reliability", "general_commendation", "direct_statement",
        "plain_direct", "none", "The entry subject.",
        "Complete compound grade phrase; inspect the following clause separately.",
        "", "إلا أنه يرسل", "high",
        "The phrase is a complete positive compound in this entry. The following إلا أنه يرسل is a distinct potentially relevant transmission note; it does not erase the positive wording or establish a rank by itself.",
    ),
    "ثقة ثقة": (
        "praise", "general_reliability", "general_commendation", "attributed_individual_judgement",
        "unresolved", "none", "The entry subject.",
        "The repeated wording is followed by قاله أحمد.", "أحمد", "", "medium",
        "The attribution قاله أحمد is explicit. Preserve the repeated form verbatim, but do not infer rhetorical emphasis from repetition; duplication or source-text convention remains possible.",
    ),
    "ثقة حافظ": (
        "praise", "unresolved", "general_commendation", "direct_statement",
        "plain_direct", "none", "The entry subject.",
        "Compound with at least a reliability attribute and a memory attribute; the single-domain codebook may not represent both cleanly.",
        "", "", "medium",
        "The text combines ثقة and حافظ. Retain the exact compound; consider linked subclaims or a documented multi-domain treatment rather than dropping حافظ. This selected entry has no attached adverse clause.",
    ),
    "صدوق حافظ": (
        "praise", "unresolved", "general_commendation", "direct_statement",
        "plain_direct", "none", "The entry subject.",
        "Compound praise; the same entry later contains a separate criticism attributed to Abu Hatim.",
        "أبو حاتم (for the later criticism only)", "له أغلاط ضعفها أبو حاتم", "medium",
        "Preserve both صدوق and حافظ. Do not discard حافظ. The subsequent clause reports errors and attributes a weakening judgement to Abu Hatim; it should not be merged into the praise span or silently treated as its negation.",
    ),
    "ثقة فقيه عابد": (
        "praise", "unresolved", "general_commendation", "direct_statement",
        "plain_direct", "none", "The entry subject.",
        "One phrase combines reliability, jurisprudential learning, and worship; segmentation or multi-domain representation needs review.",
        "", "", "medium",
        "The compound contains distinct praise dimensions (ثقة، فقيه، عابد). Preserve the whole wording and do not force all three into a single narrow domain without a codebook decision.",
    ),
    "ثقة لكنه تغير بأخرة فلم يفحش اختلاطه": (
        "mixed", "memory_precision", "mixed_assessment", "direct_statement",
        "qualified_limited", "none", "The entry subject.",
        "Retain the full grade and temporal qualification as linked wording.",
        "", "لكنه تغير بأخرة فلم يفحش اختلاطه", "high",
        "The passage gives a positive grade and a qualified late-life change statement. Preserve both halves and the explicit limitation فلم يفحش اختلاطه; do not collapse it to an unqualified ثقة label.",
    ),
    "ثقة متقن": (
        "praise", "memory_precision", "general_commendation", "direct_statement",
        "plain_direct", "none", "The entry subject.",
        "A compound reliability/precision phrase.", "", "", "medium",
        "Preserve ثقة متقن as written. The second attribute adds precision information; do not reduce it to ثقة alone.",
    ),
    "ثقة متقنا": (
        "praise", "memory_precision", "general_commendation", "direct_statement",
        "plain_direct", "none", "The entry subject.",
        "The grade phrase is followed by a separate doctrinal-criticism/repentance clause.",
        "", "طعن فيه برأي جهم ثم اعتذر وتاب", "medium",
        "Preserve the full inflected wording متقنا. In the selected entry, the later طعن فيه برأي جهم ثم اعتذر وتاب is a separate contextual statement and should not be folded into this praise phrase.",
    ),
    "ثقه": (
        "praise", "unresolved", "general_commendation", "direct_statement",
        "plain_direct", "none", "The entry subject.",
        "Preserve this exact orthographic form; the entry continues with additional praise and later-life memory change.",
        "", "عابد أثبت الناس في ثابت وتغير حفظه بأخرة", "medium",
        "Do not normalize ثقه to ثقة in the source span. The surrounding entry includes multiple distinct praise and memory statements that need separate boundaries.",
    ),
    "جبل الحفظ": (
        "praise", "memory_precision", "superlative_commendation", "direct_statement",
        "superlative", "none", "The entry subject al-Bukhari.",
        "One of two distinct praise clauses in the combined wording.", "", "", "high",
        "This is metaphorical superlative praise of memorization. Keep it distinct from the following إمام الدنيا في فقه الحديث clause, which concerns scholarly standing.",
    ),
    "إمام الدنيا في فقه الحديث": (
        "praise", "jurisprudential_or_scholarly_merit", "superlative_commendation", "direct_statement",
        "superlative", "none", "The entry subject al-Bukhari.",
        "A separate praise clause joined to the preceding phrase by attached و.", "", "", "high",
        "This praises scholarly standing in hadith jurisprudence. The Arabic-letter-boundary flag is no because و is attached; the hit is nevertheless a meaningful phrase component in the full entry. Split from جبل الحفظ if annotating one claim per distinct proposition.",
    ),
    "كذبه أبو زرعة": (
        "criticism", "honesty_veracity", "accusation_of_lying", "attributed_individual_judgement",
        "plain_direct", "none", "The entry subject.",
        "The selected entry also has a separate متروك grade and continues وغيره.",
        "أبو زرعة; وغيره is unspecified", "متروك (separate preceding assessment)", "high",
        "Record the accusation as attributed to Abu Zur'a, and retain وغيره as an additional unnamed source. The neighboring متروك is a distinct assessment; this wording does not prove independent corroboration or consensus.",
    ),
    "كذبه أحمد وغيره": (
        "criticism", "honesty_veracity", "accusation_of_lying", "attributed_individual_judgement",
        "plain_direct", "none", "The entry subject.",
        "A named attribution followed by an unspecified additional group.",
        "أحمد وغيره", "", "high",
        "Preserve Ahmad as the named evaluator and وغيره as unspecified. The wording reports an accusation, not a demonstrated transmission route or independent agreement.",
    ),
    "كذبه ابن حبان": (
        "criticism", "honesty_veracity", "accusation_of_lying", "attributed_individual_judgement",
        "plain_direct", "none", "The entry subject.", "Complete attributed phrase in this entry.",
        "ابن حبان", "", "high",
        "The local wording explicitly attributes the liar accusation to Ibn Hibban. This does not establish where Ibn Hajar obtained the report or that it is his own judgement.",
    ),
    "كذبه الشعبي في رأيه": (
        "unresolved", "unresolved", "unresolved", "unresolved", "unresolved", "none",
        "The entry subject; exact scope of رأيه requires interpretation.",
        "The phrase itself restricts the accusation with في رأيه; the surrounding entry has separate doctrine and hadith-related notes.",
        "الشعبي", "في رأيه", "low",
        "Do not treat this automatically as a general narrator-veracity grade. The scope may concern the subject's opinion; keep it unresolved until the construction and referent are reviewed.",
    ),
    "كذبه مالك وغيره": (
        "criticism", "honesty_veracity", "accusation_of_lying", "attributed_individual_judgement",
        "plain_direct", "none", "The entry subject.", "Named critic plus unspecified others; no explicit consensus formula.",
        "مالك وغيره", "", "medium",
        "Preserve Malik as the named attribution and وغيره as unspecified. The plural addition does not itself establish unanimity or an independent consensus.",
    ),
    "كذبوه": (
        "criticism", "honesty_veracity", "accusation_of_lying", "unresolved",
        "plain_direct", "scope_or_referents_unclear", "The entry subject.",
        "The group behind the plural verb is unnamed; plural wording alone is not unanimity.",
        "Unnamed plural group", "", "medium",
        "This is a direct plural accusation, but its evaluators are not identified. Do not read كذبوه as a consensus claim without explicit agreement wording or supporting evidence.",
    ),
    "لا أعرفه": (
        "unknownness", "unknownness_or_majhul_status", "unknownness_assertion", "first_person_knowledge_gap",
        "plain_direct", "none", "The pronoun referent is unresolved in this entry context.",
        "The wording occurs inside square brackets and is introduced by قال النسائي.",
        "النسائي", "", "medium",
        "Record an attributed knowledge-gap statement, retaining the brackets and the phrase قال النسائي. The referent of ـه needs review; do not automatically convert it to a narrator-level majhul label.",
    ),
    "لا بأس بحديثه": (
        "praise", "transmission_practice", "qualified_commendation", "direct_statement",
        "qualified_limited", "none", "The entry subject's transmissions.",
        "Keep the explicit route limitation attached to the positive statement.",
        "", "من رواية ابنه أحمد عنه لا من رواية ابن وهب", "high",
        "The approval is explicitly limited by transmission route: from his son Ahmad, not from Ibn Wahb. It should not be generalized to an unqualified narrator-wide praise statement.",
    ),
    "لا تعرف": (
        "unknownness", "unknownness_or_majhul_status", "unknownness_assertion", "unresolved",
        "plain_direct", "none", "Likely the female transmitter أم نهار, but confirm the referent.",
        "The same entry has a bracketed alternative: لا يعرف حالها.", "", "[لا يعرف حالها]", "low",
        "This occurrence is part of a female-transmitter entry and is followed by a bracketed alternative wording. Preserve both forms and verify editorial status and referent before assigning a precise unknownness subtype.",
    ),
    "لا يعرف": (
        "unknownness", "unknownness_or_majhul_status", "unknownness_assertion", "unresolved",
        "plain_direct", "none", "Likely the transmitter named in the preceding phrase, but confirm.",
        "In the selected entry, the phrase is followed by من السابعة and is not a complete object-level description.",
        "", "عن عائشة بنت سعد", "low",
        "This short phrase can express lack of identification or knowledge, but the full referent and intended sense require context. Do not treat the substring hit as a complete annotation or an automatic rank.",
    ),
    "لا يعرف حاله": (
        "unknownness", "unknownness_or_majhul_status", "unknownness_assertion", "direct_statement",
        "plain_direct", "none", "The entry subject عباس بن عثمان.", "Complete statement about an unknown condition/status.",
        "", "", "high",
        "The entry directly says the subject's condition is not known. This is a knowledge-status statement, not by itself a historical reliability judgement or a canonical-rank assignment.",
    ),
    "لا يعرف حالها": (
        "unknownness", "unknownness_or_majhul_status", "unknownness_assertion", "direct_statement",
        "plain_direct", "none", "The female entry subject أسماء بنت عابس.", "Complete statement about an unknown condition/status.",
        "", "", "high",
        "The entry directly describes the female subject's condition as unknown. Retain the feminine referent and do not generalize this one case to all لا يعرف constructions.",
    ),
    "لا يعرف ولم يسم": (
        "unknownness", "unknownness_or_majhul_status", "unknownness_assertion", "direct_statement",
        "plain_direct", "none", "The unnamed shaykh of Hilal ibn Yasaf.",
        "Contains two information gaps (not known; not named) followed by a reported alternative name.",
        "", "ويقال اسمه حيان ابن غالب", "medium",
        "Preserve both clauses and the following ويقال alternative. The entry's uncertainty and later reported name must remain visible rather than being normalized into a single identity decision.",
    ),
    "لم أقف على اسمها ولا على حالها": (
        "unknownness", "unknownness_or_majhul_status", "unknownness_assertion", "first_person_knowledge_gap",
        "qualified_limited", "none", "The woman in the preceding chain, likely أم فروة; verify exact referent.",
        "The first-person wording is followed by وهي من الثالثة, a separate generation statement.",
        "Unspecified first-person compiler voice", "", "low",
        "This records the speaker's stated lack of information, not an independently established property of the woman. Keep the generation clause separate and do not promote this phrase automatically to a formal majhul judgement.",
    ),
    "يسرق الحديث": (
        "criticism", "transmission_practice", "hadith_theft_or_appropriation",
        "specific_behavior_or_transmission_observation", "plain_direct", "none",
        "The entry subject عبد الملك بن الصباح.", "The phrase is explicitly introduced by قال الخليلي.",
        "الخليلي", "", "high",
        "The entry attributes a hadith-theft/appropriation criticism to al-Khalili. Keep this distinct from an explicit accusation of lying or fabrication; do not infer either without separate wording.",
    ),
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\r\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    target = list(ADVISORY)
    out_file = OUT / "AI_ADVISORY_REVIEW_BATCH_01.csv"
    if OUT.exists() and any(OUT.iterdir()):
        raise SystemExit(f"Refusing to overwrite an existing review package: {OUT}")

    occurrence_rows = read_rows(OCC_FILE)
    occurrence_by_phrase: dict[str, list[dict[str, str]]] = {}
    for row in occurrence_rows:
        occurrence_by_phrase.setdefault(row["phrase_candidate_exact"], []).append(row)
    proposals = {row["phrase_verbatim"]: row for row in read_rows(PROPOSALS)}

    review_rows: list[dict[str, Any]] = []
    for i, phrase in enumerate(target, start=1):
        hits = occurrence_by_phrase.get(phrase, [])
        if not hits:
            raise SystemExit(f"No exact occurrence in v0.1 inventory for advisory phrase: {phrase}")
        bounded = [row for row in hits if row["arabic_letter_bounded"] == "yes"]
        selected = bounded[0] if bounded else hits[0]
        family, domain, content, mode, force, consensus, referent, span_note, attribution, qualification, confidence, rationale = ADVISORY[phrase]
        proposal = proposals.get(phrase, {})
        review_rows.append({
            "advisory_id": f"ADV01-{i:03d}",
            "original_example_id": proposal.get("example_id", ""),
            "candidate_id": selected["candidate_id"],
            "phrase_candidate_exact": phrase,
            "exact_occurrences_in_local_index": len(hits),
            "arabic_letter_bounded_occurrences_in_local_index": len(bounded),
            "occurrence_selection": "First Arabic-letter-bounded hit in source-index order; if none, first exact hit. Illustrative, non-random selection.",
            "selected_occurrence_id": selected["occurrence_id"],
            "entry_id": selected["entry_id"],
            "printed_page_num": selected["printed_page_num"],
            "entry_number_verbatim": selected["entry_number_verbatim"],
            "match_start_char_zero_based": selected["match_start_char_zero_based"],
            "match_end_char_exclusive": selected["match_end_char_exclusive"],
            "arabic_letter_bounded": selected["arabic_letter_bounded"],
            "matched_text_verbatim": selected["matched_text_verbatim"],
            "entry_text_verbatim": selected["entry_text_verbatim"],
            "ai_advisory_status": "proposal_only_not_human_reviewed",
            "ai_statement_family": family,
            "ai_statement_domain": domain,
            "ai_claim_content": content,
            "ai_claim_mode": mode,
            "ai_wording_force": force,
            "ai_consensus_wording": consensus,
            "ai_referent_note": referent,
            "ai_span_boundary_note": span_note,
            "ai_attribution_text": attribution,
            "ai_qualification_or_scope_text": qualification,
            "ai_interpretation_confidence": confidence,
            "ai_rationale": rationale,
            "human_decision": "",
            "human_notes": "",
            "canonical_rank": "",
            "numeric_score": "",
        })

    OUT.mkdir(parents=True, exist_ok=True)
    fields = list(review_rows[0])
    write_csv(out_file, review_rows, fields)
    readme = f"""# AI advisory occurrence review — batch 01

**Status:** {len(review_rows)} source-linked, illustrative AI proposals. No human decisions are entered. The proposed descriptor values use the draft codebook and are not validated annotations.

## Scope

This batch covers the exact phrase constructions raised in the recent review discussion: Companion-status wording, praise and compound praise, attributed accusations, consensus wording, unknownness, and hadith-theft wording. Each row joins one exact phrase to one complete local entry from the Shamela4 Taqrīb index. The human decision and note fields are blank. No canonical rank or numeric score is proposed.

For each phrase, the file reports all exact-substring and Arabic-letter-bounded counts from the full v0.1 occurrence inventory. It selects only one illustrative occurrence: the first Arabic-letter-bounded hit in source-index order, or the first exact hit if none is letter-bounded. This is a deterministic convenience sample, not a random or representative sample. Common phrases such as ثقة (2,322 exact hits) and ثبت (211 exact hits) are not reviewed exhaustively; neither are the other repeated phrases.

## Reading the AI suggestions

The full entry text is included so the selected hit can be assessed as a complete claim, part of a compound, or an irrelevant use. Arabic-letter-bounded means only that an Arabic letter does not touch the match edge. It does not establish a statement boundary or referent. Conversely, attached conjunctions such as و can make a valid phrase fail this simple boundary check.

Several context-sensitive cautions surfaced in the examples:

- أم المؤمنين in the selected entry refers to Khadija, not the indexed narrator Hakim ibn Hizam.
- The selected لا أعرفه text is bracketed and attributed to al-Nasa'i; its pronoun referent remains unresolved.
- لا بأس بحديثه is explicitly limited by transmission route in the same entry.
- قال ابن عبد البر precedes أجمعوا على ثقته, so the wording is reported with an attribution; the consensus wording is not independent evidence of actual consensus.
- كذبه الشعبي في رأيه has a scope phrase requiring interpretation, while كذبوه names no evaluators. Neither should be converted automatically into a general reliability grade or an established consensus.
- أفرط فيه ابن معين فكذبه combines a comment on the critic's severity with a reported accusation. It does not support a numeric decrement.
- The combined praise for al-Bukhari contains two distinct propositions: جبل الحفظ and إمام الدنيا في فقه الحديث.

These are AI reading notes for review, not scholarly adjudications. Field-role or statement coding does not establish historical accuracy, authorship, transmission route, narrator reliability, or target eligibility.

## Next use

Review the proposed fields and rationale row by row. In `human_decision`, enter `accept` only if all proposed coding fields fit this selected entry; enter `change` and describe the correction in `human_notes`; enter `unsure` if the passage cannot be resolved. An `accept` applies to that row's selected occurrence only, not to every hit of the phrase. Preserve this AI proposal and the raw occurrence inventory unchanged. Expand to additional cases only in a new batch, with a documented sampling rule. Do not treat the examples as validation of all occurrences of the same phrase.
"""
    readme_path = OUT / "README.md"
    readme_path.write_text(readme, encoding="utf-8", newline="\n")

    input_paths = [OCC_FILE, OCC_MANIFEST, CODEBOOK, PROPOSALS, Path(__file__).resolve()]
    outputs = [out_file, readme_path]
    manifest = {
        "package_id": OUT.name,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "AI advisory only; no human decisions, canonical ranks, or numeric scores assigned",
        "sampling": "One illustrative occurrence per phrase; first Arabic-letter-bounded hit in source-index order, otherwise first exact hit; purposive and non-random.",
        "counts": {
            "phrase_examples": len(review_rows),
            "unique_source_entries": len({r["entry_id"] for r in review_rows}),
            "human_decisions_filled": 0,
            "canonical_ranks_assigned": 0,
            "numeric_scores_assigned": 0,
        },
        "inputs": {path.relative_to(ROOT).as_posix(): digest(path) for path in input_paths},
        "outputs": {path.name: digest(path) for path in outputs},
        "manifest_hash_policy": "MANIFEST.sha256 records the manifest hash separately; it is not recursively embedded.",
    }
    manifest_path = OUT / "MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    (OUT / "MANIFEST.sha256").write_text(f"{digest(manifest_path)}  MANIFEST.json\n", encoding="ascii", newline="\n")
    print(json.dumps({"output": str(OUT), **manifest["counts"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
