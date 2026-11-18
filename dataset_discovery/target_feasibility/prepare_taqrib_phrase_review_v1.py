#!/usr/bin/env python3
"""Prepare a construction-grouped human review package for the 148 no-hit AI phrase candidates."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PIPELINE = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline"
SHADOW_DIR = PIPELINE / "rank_label_shadow_run_v1_2026-11-15"
INV_V02_DIR = PIPELINE / "rank_label_candidate_inventory_v0_2_2026-11-15"
AI_REVIEW_DIR = PIPELINE / "rank_label_no_hit_ai_review_v1_2026-11-15"
CONSOLIDATED_DIR = AI_REVIEW_DIR / "CONSOLIDATED_V1_3"
OUTPUT_DIR = PIPELINE / "rank_label_phrase_review_v1_2026-11-15"

ARABIC_LETTER = re.compile(r"[\u0621-\u064a\u066e-\u06d3\u06fa-\u06fc]")

FAMILY_ORDER = [
    "01_companion_status_direct",
    "02_companion_status_disputed_or_ruyah",
    "03_unknown_status_ranks_7_9_or_unnamed",
    "04_mild_or_attributed_weakness_ranks_6_8",
    "05_attributed_authentication_rank3_proxy",
    "06_praise_orthographic_and_compound_ranks_2_3_4",
    "07_lying_fabrication_abandonment_ranks_10_11_12",
    "08_general_criticism_innovation_or_non_grade",
]

FAMILIES: dict[str, set[str]] = {
    "01_companion_status_direct": {
        "صحابي", "له صحبة", "صحابي مشهور", "صحابية", "لها صحبة", "صحابي جليل",
        "صحابي صغير", "صحابي مقل", "له ولأبيه صحبة", "أم المؤمنين", "الصحابي",
        "أحد العشرة", "صحابي ابن صحابي", "صحابي شهير", "صحابي معروف", "صحابية مشهور",
        "من مسلمة الفتح", "أحد النقباء", "شهد أحدا", "صحابي بدري", "صحابي من أهل الصفة",
        "من السابقين الأولين", "وصحب", "أحد السابقين الأولين", "أحد العشرة المشهود لهم بالجنة",
        "أسلم قديما وهاجر الهجرتين", "الصديق الأكبر", "بدري", "ثم أسلم وصحب",
        "حاضنة النبي ﷺ", "خادم النبي ﷺ", "خادم رسول الله ﷺ خدمه عشر سنين",
        "شهد أحدا وما بعدها", "شهد بدر", "شهد بدرا", "شهد بدرا وغيرها", "شهد بدرا وهو مملوك",
        "شهد بيعة الرضوان", "صحابي كبير", "صحبا", "صحبه وحفظ عنه", "صحبه ولازمه",
        "فهو صحابي ابن صحابي", "له وفادة", "له ولأبويه صحبة", "له ولأبيه ولجده صحبه",
        "له ولابنه صحبة", "من السابقين الأولين هاجر الهجرتين وشهد المشاهد", "من قدماء المهاجرين",
        "مولى النبي ﷺ وخادمه", "وله صحبة",
    },
    "02_companion_status_disputed_or_ruyah": {
        "مختلف في صحبته", "يقال له صحبة", "له رؤية", "قيل له صحبة", "يقال له رؤية",
        "يقال لها صحبة", "البدري", "قيل إن له هو صحبة", "قيل لقهيد صحبة",
        "قيل له صحبة أو رؤية", "كأنها صحابية", "لها رؤية", "مختلف في وجوده فقيل صحابي",
        "وكأنها صحابية", "ويقال إن لها صحبة",
    },
    "03_unknown_status_ranks_7_9_or_unnamed": {
        "لا تعرف", "لا يعرف", "لا يعرف حاله", "لا يعرف ولم يسم", "لا أعرفه",
        "لم أقف على اسمها ولا على حالها", "ما عرف أبو حاتم حاله في الحديث",
    },
    "04_mild_or_attributed_weakness_ranks_6_8": {
        "فيه لين", "لين", "في حديثه لين", "ليّن", "فيه ضعف", "ضعف مع إمامته ومعرفته",
        "ضعفه أبو حاتم", "ضعفه أبو زرعة", "ضعفه الأزدي من الرابعة ق",
        "ضعفه يحيى ابن معين ورمي بالإرجاء من التاسعة مات سنة خمس عشرة ت",
        "ضعفوه لكثرة تدليسه", "ليس بالقوي", "ليس بالقوي وقد تغير في آخر عمره", "سيء الحفظ",
    },
    "05_attributed_authentication_rank3_proxy": {
        "وثقه النسائي", "وثقه العجلي", "وثقه ابن معين", "وثقه ابن حبان",
        "ذكره ابن حبان في ثقات التابعين", "ثقات التابعين", "ذكره ابن حبان في الثقات",
        "وثقه أبو داود وغيره", "وثقه أبو زرعة", "أجمعوا على ثقته",
        "ذكره جماعة في ثقات التابعين", "مجمع على ثقته", "من كبار التابعين الثقات",
        "وثقه", "وثقه أبو حاتم", "وثقه أبو زرعة في الحديث", "وثقه ابن سعد",
        "وثقه الأئمة", "وثقه الجمهور", "وثقه الخطيب", "وثقه الدارقطني",
        "وثقه الشافعي", "وثقه العجلي وجماعة", "وثقه يعقوب ابن", "وثقها العجلي",
        "وقد وثق",
    },
    "06_praise_orthographic_and_compound_ranks_2_3_4": {
        "ثقه", "صالح الحديث", "حافظ", "أحد الحفاط", "أحد الحفاظ",
        "أحد العلماء الأثبات الفقهاء الكبار", "جبل الحفظ وإمام الدنيا في فقه الحديث",
        "صالح الحديث إلا عن بقية", "قال ابن معين صالح", "لا بأس بحديثه", "ما به بأس",
        "مستقيم الحديث إلا في حديث واحد يقال إن ابنه محمدا أدخله عليه",
    },
    "07_lying_fabrication_abandonment_ranks_10_11_12": {
        "متهم بالكذب", "ليس بأهل أن يروى عنه", "اتفق النقاد على تكذيبه",
        "تركه الدارقطني", "تركوه", "رماه ابن معين بالكذب", "رموه بالوضع", "رمي بالوضع",
        "كذبه أبو زرعة", "كذبه أحمد وغيره", "كذبه ابن حبان", "كذبه الشعبي في رأيه",
        "كذبه مالك وغيره", "متهم بالوضع", "نسبه أبو حاتم إلى الكذب", "يسرق الحديث",
    },
    "08_general_criticism_innovation_or_non_grade": {
        "أثنى عليه", "اتهمه جماعة", "تكلم فيه بعضهم", "تكلموا فيه",
        "ثقات الأمراء", "رافضي", "عابوا عليه أنه حدث عن أبيه بغير سماع",
    },
}

SPAN_DEFECT_NOTES: dict[str, tuple[str, str]] = {
    "صحابية مشهور": (
        "span_truncated_missing_ta_marbuta",
        "AI dropped final ta marbuta; all 3 example entries read 'صحابية مشهورة'. Revise span to 'صحابية مشهورة' before adding to inventory.",
    ),
    "وثقه يعقوب ابن": (
        "span_truncated_mid_name",
        "AI span is truncated mid-name; entry S3076-P325-C007-E3643 reads 'وثقه يعقوب ابن سفيان'. Revise span to 'وثقه يعقوب ابن سفيان'.",
    ),
    "ضعفه الأزدي من الرابعة ق": (
        "span_includes_generation_and_sigla",
        "AI span appends generation and book sigla ('من الرابعة ق'). Revise span to 'ضعفه الأزدي'; evaluate under Rank 8 preconditions.",
    ),
    "ضعفه يحيى ابن معين ورمي بالإرجاء من التاسعة مات سنة خمس عشرة ت": (
        "span_includes_generation_death_sigla",
        "AI span merges grade, innovation note, generation, death date, and sigla. Revise target span to 'ضعفه يحيى ابن معين' and keep 'ورمي بالإرجاء' in the context layer.",
    ),
    "خادم رسول الله ﷺ خدمه عشر سنين": (
        "span_includes_duration_clause",
        "Biographical Companion wording for Anas b. Malik; optionally trim to 'خادم رسول الله ﷺ' or treat as biographical Rank 1 status.",
    ),
    "ثقات الأمراء": (
        "non_grade_political_title",
        "Entry S3076-P549-C006-E6937 reads 'من ثقات الأمراء' (trustworthy/capable commanders in war), not a hadith narrator reliability rank.",
    ),
    "وقد وثق": (
        "not_first_grade_phrase_and_bracketed",
        "Entry S3076-P433-C010-E5214 reads 'ليس بمشهور [وقد وثق]'; 'ليس بمشهور' is the earlier phrase and '[وقد وثق]' is bracketed editorial addition.",
    ),
    "أحد الحفاط": (
        "source_orthographic_typo",
        "Local Shamela text in S3076-P467-C006-E5718 reads 'أحد الحفاط' (typo for 'أحد الحفاظ') for Abu Hatim al-Razi; preserve verbatim if kept, and note memory/scholarship vs reliability rank.",
    ),
    "ثقه": (
        "orthographic_variant_and_compound_risk",
        "Local spelling variant with final ha instead of ta marbuta ('ثقه' vs 'ثقة'); 79 of 84 corpus hits are substrings of 'وثقه'/'أوثقه', and 2 of 4 no-hit entries read 'ثقه مقل عابد' / 'ثقه عابد' (compound praise).",
    ),
    "له ولأبيه ولجده صحبه": (
        "orthographic_variant_ha_for_ta_marbuta",
        "Local spelling in S3076-P542-C006-E6823 reads 'صحبه' with final ha instead of ta marbuta ('صحبة'). Preserve exact local spelling if retained.",
    ),
    "ليّن": (
        "diacritic_variant_shadda",
        "Contains shadda on ya ('ليّن'), distinct from unvocalized 'لين'. Evaluate with Rank 6 ('لين الحديث') / Rank 8 mild-weakness rules.",
    ),
    "الصحابي": (
        "compound_noun_and_negation_risk",
        "In E0943 and E5053 the full phrases are 'الصحابي الجليل' and 'الصحابي المشهور'; corpus scan also hits 'غير الصحابي' (contrastive negation).",
    ),
    "حافظ": (
        "scholarship_descriptor_not_unconditional_rank3",
        "In E6409 (Ibn Majah) the text reads 'أحد الأئمة حافظ'; in E7591 (al-Himmani) 'حافظ إلا أنهم اتهموه بسرقة الحديث'. 'حافظ' alone describes memory/scholarship, not Rank 3; corpus hits also include 'لم يكن بالحافظ'.",
    ),
    "بدري": (
        "high_nisba_collision_al_abdari",
        "23 of 33 corpus hits are substrings of the tribal nisba 'العبدري'. Any exact-match rule MUST enforce non-Arabic-letter boundaries.",
    ),
    "شهد بدر": (
        "orthographic_case_variant_of_shahida_badran",
        "Missing accusative alif ('شهد بدر' vs 'شهد بدرا' 27 hits). Only 1 word-bounded hit in corpus (E3318).",
    ),
    "كذبه الشعبي في رأيه": (
        "scoped_to_opinion_not_hadith_fabrication",
        "Entry S3076-P146-C012-E1029 says 'كذبه الشعبي في رأيه' (qualified to his opinion/creed, followed by 'ورمي بالرفض وفي حديثه ضعف'). Do not collapse into Rank 12 hadith fabrication.",
    ),
    "ليس بأهل أن يروى عنه": (
        "historical_political_figure_formula",
        "Appears on al-Hajjaj b. Yusuf (E1141) and Yazid b. Muawiyah (E7777) in tamyiz/historical entries; not one of Ibn Hajar's standard 12-rank examples.",
    ),
    "وثقه الجمهور": (
        "followed_by_weakness_and_late_change",
        "Entry S3076-P147-C009-E1041 continues 'وفي أحاديثه مناكير ضعفه بسببها الأزدي وابن حبان وغيرهما فلعله تغير حفظه في الآخر'. Keep Rank 3 proxy conditional/flagged by later notes.",
    ),
    "لا بأس بحديثه": (
        "transmitter_conditioned_la_basa",
        "Entry S3076-P263-C018-E2739 restricts the judgment: 'لا بأس بحديثه من رواية ابنه أحمد عنه لا من رواية ابن وهب'. Cannot be mapped to unconditional Rank 4.",
    ),
    "مستقيم الحديث إلا في حديث واحد يقال إن ابنه محمدا أدخله عليه": (
        "qualified_exception_span",
        "Full qualified praise with single-hadith exception ('إلا في حديث واحد...'); not a standard Rank 3/4 example.",
    ),
    "صالح الحديث إلا عن بقية": (
        "transmitter_exception_span",
        "Qualified 'صالح الحديث' restricted to transmissions other than Baqiyyah ('إلا عن بقية'). Keep full exception attached.",
    ),
    "ذكره ابن حبان في ثقات التابعين": (
        "check_preceding_context_and_brackets",
        "In E2214 this follows 'لأبيه صحبة ويقال له أيضا'; in E7196 it is bracketed '[ذكره ابن حبان في ثقات التابعين] وقيل له صحبة'. Also check Policy v0.2 on Ibn Hibban's Thiqat.",
    ),
}

DISPUTE_MARKERS = (
    "وقيل لا صحبة",
    "لا صحبة له",
    "نفاها",
    "لم يصح",
    "واهي",
    "مرسل",
    "وهم",
    "مختلف",
    "غير مشهور",
    "في حديثه ضعف",
    "ضعفه",
    "اتهموه",
    "يرمونه بالكذب",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def is_arabic_letter(text: str, pos: int) -> bool:
    return 0 <= pos < len(text) and bool(ARABIC_LETTER.fullmatch(text[pos]))


def verify_inputs() -> None:
    results_manifest = json.loads((CONSOLIDATED_DIR / "REVIEW_RESULTS_MANIFEST.json").read_text(encoding="utf-8"))
    for name, expected in results_manifest["outputs"].items():
        actual = sha256(CONSOLIDATED_DIR / name)
        if actual != expected:
            raise SystemExit(f"Consolidated AI review hash mismatch for {name}: {actual} != {expected}")

    v02_manifest = json.loads((INV_V02_DIR / "MANIFEST.json").read_text(encoding="utf-8"))
    for name, expected in v02_manifest["outputs"].items():
        actual = sha256(INV_V02_DIR / name)
        if actual != expected:
            raise SystemExit(f"Candidate inventory v0.2 hash mismatch for {name}: {actual} != {expected}")

    shadow_manifest = json.loads((SHADOW_DIR / "RUN_MANIFEST.json").read_text(encoding="utf-8"))
    for name, expected in shadow_manifest["outputs"].items():
        actual = sha256(SHADOW_DIR / name)
        if actual != expected:
            raise SystemExit(f"Shadow run hash mismatch for {name}: {actual} != {expected}")


def phrase_family_map(index_phrases: set[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for family, phrases in FAMILIES.items():
        for phrase in phrases:
            if phrase in mapping:
                raise SystemExit(f"Duplicate phrase in family map: {phrase}")
            mapping[phrase] = family
    missing = index_phrases - set(mapping.keys())
    extra = set(mapping.keys()) - index_phrases
    if missing or extra:
        raise SystemExit(f"Family map mismatch: missing={missing}, extra={extra}")
    return mapping


def corpus_stats_for_phrase(phrase: str, entries: list[dict[str, str]]) -> dict[str, int]:
    total_hits = 0
    word_bounded_hits = 0
    bounded_entries: set[str] = set()
    for entry in entries:
        text = entry["entry_text_verbatim"]
        offset = 0
        while True:
            idx = text.find(phrase, offset)
            if idx < 0:
                break
            total_hits += 1
            if not is_arabic_letter(text, idx - 1) and not is_arabic_letter(text, idx + len(phrase)):
                word_bounded_hits += 1
                bounded_entries.add(entry["entry_id"])
            offset = idx + 1
    return {
        "total_hits": total_hits,
        "word_bounded_hits": word_bounded_hits,
        "word_bounded_unique_entries": len(bounded_entries),
        "substring_only_hits": total_hits - word_bounded_hits,
    }


def classify_recommendation(
    phrase: str,
    family: str,
    group_rows: list[dict[str, str]],
    stats: dict[str, int],
) -> tuple[list[str], str, str, str]:
    flags: list[str] = []
    status_counts = Counter(r["ai_status"] for r in group_rows)
    rank_counts = Counter(r["ai_rank_candidate_1_to_12"] for r in group_rows)

    if len(status_counts) > 1 or len(rank_counts) > 1:
        flags.append("batch_divergence_in_ai_review")
    if stats["substring_only_hits"] > 0:
        flags.append("high_substring_overlap_risk" if stats["substring_only_hits"] >= stats["word_bounded_hits"] else "substring_overlap_present")
    if phrase in SPAN_DEFECT_NOTES:
        flags.append(SPAN_DEFECT_NOTES[phrase][0])

    has_trailing_dispute = any(
        any(marker in r["entry_text_verbatim"] for marker in DISPUTE_MARKERS)
        for r in group_rows
    )
    if has_trailing_dispute and family in {"01_companion_status_direct", "02_companion_status_disputed_or_ruyah", "05_attributed_authentication_rank3_proxy"}:
        flags.append("trailing_dispute_or_qualification_observed")

    if family == "01_companion_status_direct":
        flags.append("rank1_status_separate_from_reliability")
        if phrase in SPAN_DEFECT_NOTES:
            action = "revise_span_before_candidate"
            rank_scope = "1 (status category; revise exact span first)"
            note = SPAN_DEFECT_NOTES[phrase][1]
        elif has_trailing_dispute:
            action = "prepare_candidate_with_boundary_guard"
            rank_scope = "1 (status category; conditional when entry disputes companionship)"
            note = (
                "Direct Companion wording supports Rank 1 status, but one or more entries contain trailing dispute/qualification "
                "(e.g., 'وقيل لا صحبة له', 'لم يصح الإسناد إليه', 'نفاها بعضهم'). Enforce word boundaries and check trailing negation."
            )
        else:
            action = "prepare_candidate_with_boundary_guard"
            rank_scope = "1 (status category; separate from ordinary reliability grades)"
            note = (
                f"Direct Companion status wording ({stats['word_bounded_unique_entries']} word-bounded entries across full corpus). "
                "Eligible for Rank 1 status candidate with Arabic word-boundary and trailing-negation checks."
            )

    elif family == "02_companion_status_disputed_or_ruyah":
        flags.append("rank1_status_disputed_or_ruyah_boundary")
        action = "keep_conditional_pending_evidence"
        rank_scope = "1_conditional_or_abstain (disputed companionship or childhood ruyah)"
        if "رؤية" in phrase:
            note = (
                "Indicates seeing the Prophet (ruyah) rather than explicit 'صحابي'/'له صحبة'. Several entries cite Ibn Hibban listing them in "
                "Thiqat al-Tabi'in (e.g., E1909, E2010, E7540). Decide project policy on 'رؤية' vs Rank 1 before promoting."
            )
        else:
            note = (
                "Explicitly uncertain or disputed Companion wording ('مختلف في صحبته', 'يقال', 'قيل', 'كأنها'). "
                "Do not auto-assign Rank 1; keep conditional or abstain."
            )

    elif family == "03_unknown_status_ranks_7_9_or_unnamed":
        flags.append("requires_external_rank_condition")
        action = "keep_conditional_pending_evidence"
        rank_scope = "7_or_9_conditional (requires transmitter count and authentication check)"
        note = (
            "Unknown-status / unnamed wording. Ibn Hajar's Ranks 7 ('مستور'/'مجهول الحال', >1 transmitter) vs 9 ('مجهول', 1 transmitter) "
            "require transmitter-count and lack-of-authentication evidence not established by the phrase alone."
        )

    elif family == "04_mild_or_attributed_weakness_ranks_6_8":
        flags.append("requires_external_rank_condition")
        if phrase in SPAN_DEFECT_NOTES:
            action = "revise_span_before_candidate"
            rank_scope = "6_or_8_conditional (revise span; check Rank 6/8 conditions)"
            note = SPAN_DEFECT_NOTES[phrase][1]
        elif "لين" in phrase or "ليّن" in phrase:
            action = "keep_conditional_pending_evidence"
            rank_scope = "6_candidate_conditional (check corroboration, little-hadith, and no-abandonment conditions)"
            note = (
                "Mild-weakness wording aligned with Rank 6 ('فلين الحديث' / 'لين الحديث'), but Rank 6 requires little hadith and no established "
                "reason to abandon, and entries may include additional disqualifiers. Keep conditional pending context check."
            )
        elif phrase == "سيء الحفظ":
            action = "keep_conditional_pending_evidence"
            rank_scope = "5_or_8_check (Rank 5 lists 'صدوق سيء الحفظ'; standalone requires context)"
            note = "Rank 5 example is 'صدوق سيء الحفظ'. Standalone 'سيء الحفظ' in E2600 lacks 'صدوق' and includes 'يتشيع'; verify whether it maps to Rank 5 or below."
        else:
            action = "keep_conditional_pending_evidence"
            rank_scope = "8_conditional (requires absence of recognized authentication)"
            note = (
                "Weakness wording ('فيه ضعف', 'ضعفه ...', 'ليس بالقوي'). Rank 8 requires no authentication from a recognized authority in scope; "
                "also preserve explicit critic attribution and any trailing qualifications."
            )

    elif family == "05_attributed_authentication_rank3_proxy":
        if phrase in SPAN_DEFECT_NOTES:
            action = "revise_span_before_candidate" if phrase in {"وثقه يعقوب ابن"} else (
                "exclude_non_grade_or_not_first" if phrase == "وقد وثق" else "keep_conditional_pending_evidence"
            )
            rank_scope = "3_proxy_subject_to_policy_v0_2" if phrase != "وقد وثق" else "not_first_grade_phrase (preceded by ليس بمشهور)"
            note = SPAN_DEFECT_NOTES[phrase][1]
        else:
            action = "prepare_candidate_with_boundary_guard"
            rank_scope = "3 (attributed proxy under Policy v0.2; preserve critic attribution)"
            if "batch_divergence_in_ai_review" in flags:
                note = (
                    "AI batches diverged here: Batch 1 marked 'unresolved' because the wording is attributed, whereas Batches 2-3 proposed Rank 3 "
                    "under Policy v0.2 ('first complete grade-bearing phrase... even when attributed'). Confirm Policy v0.2 application and preserve attribution."
                )
            else:
                note = (
                    "Attributed commendation ('وثقه ...' / 'مجمع على ثقته' / 'ثقات التابعين'). Under Policy v0.2, eligible as Rank 3 proxy candidate "
                    "only if attribution is preserved and no conflicting weakness/context note overrides it."
                )

    elif family == "06_praise_orthographic_and_compound_ranks_2_3_4":
        if phrase in SPAN_DEFECT_NOTES:
            action = "revise_span_before_candidate" if phrase in {"ثقه", "أحد الحفاط"} else "keep_conditional_pending_evidence"
            rank_scope = "review_span_and_rank_basis"
            note = SPAN_DEFECT_NOTES[phrase][1]
        elif phrase in {"أحد العلماء الأثبات الفقهاء الكبار", "جبل الحفظ وإمام الدنيا في فقه الحديث"}:
            action = "prepare_candidate_with_boundary_guard"
            rank_scope = "2 (strong/compound praise candidate)"
            note = "Strong praise formulation aligned with Rank 2 ('combination of praise in meaning'); verify single-entry context before accepting."
        elif phrase == "ما به بأس":
            action = "prepare_candidate_with_boundary_guard"
            rank_scope = "4 (semantic variant of ليس به بأس / لا بأس به)"
            note = "Matches Rank 4 wording pattern ('ليس به بأس' / 'لا بأس به') in E7833 ('ما به بأس من كبار السابعة'). Confirm as Rank 4 candidate."
        else:
            action = "keep_conditional_pending_evidence"
            rank_scope = "3_or_4_unresolved (non-canonical wording; check critic attribution)"
            note = "Evaluative praise/middling wording ('صالح الحديث', 'قال ابن معين صالح', etc.) not explicitly listed in Ibn Hajar's 12-rank examples; review Rank 3 vs 4 boundary."

    elif family == "07_lying_fabrication_abandonment_ranks_10_11_12":
        flags.append("requires_external_rank_condition")
        if phrase in SPAN_DEFECT_NOTES:
            action = "exclude_non_grade_or_not_first" if phrase == "ليس بأهل أن يروى عنه" else "keep_unresolved_or_abstain"
            rank_scope = "non_standard_or_opinion_scoped"
            note = SPAN_DEFECT_NOTES[phrase][1]
        elif phrase == "متهم بالكذب":
            action = "prepare_candidate_with_boundary_guard"
            rank_scope = "11 (accusation of lying; check attribution and Rank 11/12 boundary)"
            note = "Direct morphological variant of Ibn Hajar's Rank 11 example 'اتهم بالكذب'. Check trailing notes (e.g., 'ورمي بالرفض' in E5901) before promoting."
        elif phrase in {"تركه الدارقطني", "تركوه"}:
            action = "keep_conditional_pending_evidence"
            rank_scope = "10_conditional (abandonment requires no-authentication + defect check)"
            note = "Attributed/plural abandonment ('تركوه', 'تركه الدارقطني'); Rank 10 requires lack of authentication plus a grounding defect, and E7862 also has 'وكذبه ابن معين'."
        else:
            action = "keep_unresolved_or_abstain"
            rank_scope = "11_vs_12_boundary_unresolved"
            note = (
                "Lying/fabrication/stealing wording ('كذبه ...', 'رماه ... بالكذب', 'رمي بالوضع', 'متهم بالوضع', 'اتفق النقاد على تكذيبه', 'يسرق الحديث'). "
                "Requires resolving Ibn Hajar's Rank 11 (accusation) vs Rank 12 (applied lying/fabrication label) boundary and critic attribution."
            )

    else:
        flags.append("non_grade_or_vague_criticism")
        if phrase in SPAN_DEFECT_NOTES:
            action = "exclude_non_grade_or_not_first"
            rank_scope = "exclude_non_grade"
            note = SPAN_DEFECT_NOTES[phrase][1]
        elif phrase == "رافضي":
            action = "keep_conditional_pending_evidence"
            rank_scope = "context_layer_affiliation (first grade-bearing note vs Rank 5 innovation advocacy)"
            note = "Standalone sect/innovation label in E2101 ('رافضي كذبه يحيى ابن معين'). Under Policy v0.2 and Rank 5, innovation advocacy and following 'كذبه يحيى ابن معين' require careful separation."
        else:
            action = "keep_unresolved_or_abstain"
            rank_scope = "abstain_vague_or_non_standard"
            note = "Vague or non-standard wording ('أثنى عليه', 'اتهمه جماعة', 'تكلم فيه بعضهم', 'تكلموا فيه', 'عابوا عليه...') without a clear rank-mapping cue in Ibn Hajar's 12 definitions."

    return flags, action, rank_scope, note


def assert_no_em_en_dash(text: str, label: str) -> None:
    if "\u2014" in text or "\u2013" in text:
        raise SystemExit(f"Forbidden em-dash or en-dash detected in {label}")


def audit_none_found_rows(all_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    audited: list[dict[str, str]] = []
    for row in all_rows:
        span = row["ai_first_grade_span_exact"]
        if span not in {"none_found", ""}:
            continue
        text = row["entry_text_verbatim"]
        tags: list[str] = []
        if not text.strip() or re.fullmatch(r"[\u0660-\u06690-9]+\s*-\s*", text.strip()):
            tags.append("empty_entry_text")
        if "<" in text and ">" in text:
            tags.append("inline_html_tag")
        if "رسول الله" in text:
            tags.append("implicit_companion_or_prophetic_relation_cue")
        if "تمييز" in text:
            tags.append("tamiz_entry")
        if "لم يسم" in text or "لم تسم" in text or "لم يسميا" in text:
            tags.append("unnamed_narrator_lam_yusamma")
        if "ليست له صحبة" in text or "لا صحبة له" in text or "وهم من زعم أن له صحبة" in text or "والصواب أنه تابعي" in text:
            tags.append("explicit_no_companionship")
        if "لا أعرف" in text:
            tags.append("la_arif_statement")
        if "سيد التابعين" in text or "الحافظ" in text or "رأس الطبقة" in text:
            tags.append("biographical_eminence_or_scholarship_cue")
        if not tags:
            tags.append("other_biographical_or_crossref")

        audited.append({
            "entry_id": row["entry_id"],
            "printed_page_num": row["printed_page_num"],
            "entry_number_verbatim": row["entry_number_verbatim"],
            "ai_status": row["ai_status"],
            "ai_context_note_spans_exact": row["ai_context_note_spans_exact"],
            "audit_tags": ";".join(tags),
            "ai_reason": row["ai_reason"],
            "entry_text_verbatim": text,
            "human_decision": "",
            "human_notes": "",
        })
    return audited


def main() -> None:
    if OUTPUT_DIR.exists():
        raise SystemExit(f"Refusing to overwrite existing review directory: {OUTPUT_DIR}")

    verify_inputs()

    _, idx_rows = read_csv(CONSOLIDATED_DIR / "AI_FIRST_PHRASE_REVIEW_INDEX.csv")
    _, all_rows = read_csv(CONSOLIDATED_DIR / "AI_REVIEW_ALL_1211.csv")
    _, entries = read_csv(SHADOW_DIR / "ENTRY_INDEX.csv")

    index_phrases = {r["phrase_text_trimmed_for_grouping"] for r in idx_rows}
    family_map = phrase_family_map(index_phrases)

    rows_by_phrase: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in all_rows:
        span = r["ai_first_grade_span_exact"]
        if span in {"none_found", ""}:
            continue
        cleaned = span[len("uncertain: "):].strip() if span.startswith("uncertain: ") else span.strip()
        rows_by_phrase[cleaned].append(r)

    family_rank = {fam: i for i, fam in enumerate(FAMILY_ORDER)}
    sorted_idx = sorted(
        idx_rows,
        key=lambda r: (
            family_rank[family_map[r["phrase_text_trimmed_for_grouping"]]],
            -int(r["entry_count"]),
            r["phrase_text_trimmed_for_grouping"],
        ),
    )

    worksheet_rows: list[dict[str, Any]] = []
    family_summary: dict[str, dict[str, int]] = {
        fam: {"phrases": 0, "no_hit_entries": 0, "corpus_bounded_entries": 0}
        for fam in FAMILY_ORDER
    }

    for num, idx_row in enumerate(sorted_idx, start=1):
        phrase = idx_row["phrase_text_trimmed_for_grouping"]
        family = family_map[phrase]
        group_rows = rows_by_phrase[phrase]
        stats = corpus_stats_for_phrase(phrase, entries)
        flags, action, rank_scope, note = classify_recommendation(phrase, family, group_rows, stats)

        div_ids = ""
        if "batch_divergence_in_ai_review" in flags:
            buckets: dict[str, list[str]] = defaultdict(list)
            for gr in sorted(group_rows, key=lambda x: x["entry_id"]):
                key = f"{gr['ai_status']}:{gr['ai_rank_candidate_1_to_12']}"
                if len(buckets[key]) < 2:
                    buckets[key].append(gr["entry_id"])
            div_ids = " | ".join(f"{k}=[{','.join(v)}]" for k, v in sorted(buckets.items()))

        family_summary[family]["phrases"] += 1
        family_summary[family]["no_hit_entries"] += int(idx_row["entry_count"])
        family_summary[family]["corpus_bounded_entries"] += stats["word_bounded_unique_entries"]

        record = {
            "review_id": f"PHR-REV-{num:03d}",
            "construction_family": family,
            "phrase_text_trimmed_for_grouping": phrase,
            "no_hit_entry_count": idx_row["entry_count"],
            "uncertain_status_count": idx_row["uncertain_status_count"],
            "corpus_total_exact_hits": stats["total_hits"],
            "corpus_word_bounded_hits": stats["word_bounded_hits"],
            "corpus_word_bounded_unique_entries": stats["word_bounded_unique_entries"],
            "corpus_substring_only_hits": stats["substring_only_hits"],
            "ai_status_counts": idx_row["ai_status_counts"],
            "rank_suggestion_counts_unverified": idx_row["rank_suggestion_counts_unverified"],
            "phrase_type_counts": idx_row["phrase_type_counts"],
            "audit_flags": ";".join(flags),
            "recommended_action": action,
            "recommended_rank_or_status_scope": rank_scope,
            "audit_note": note,
            "batch_divergence_example_ids": div_ids,
            "example_1_entry_id": idx_row["example_1_entry_id"],
            "example_1_entry_text": idx_row["example_1_entry_text"],
            "example_2_entry_id": idx_row["example_2_entry_id"],
            "example_2_entry_text": idx_row["example_2_entry_text"],
            "example_3_entry_id": idx_row["example_3_entry_id"],
            "example_3_entry_text": idx_row["example_3_entry_text"],
            "human_decision": "",
            "human_approved_span_exact": "",
            "human_rank_or_status_decision": "",
            "human_notes": "",
        }
        for k, v in record.items():
            assert_no_em_en_dash(str(v), f"{record['review_id']}.{k}")
        worksheet_rows.append(record)

    none_found_rows = audit_none_found_rows(all_rows)
    for r in none_found_rows:
        for k, v in r.items():
            assert_no_em_en_dash(str(v), f"none_found.{r['entry_id']}.{k}")

    OUTPUT_DIR.mkdir(parents=True)

    worksheet_fields = [
        "review_id", "construction_family", "phrase_text_trimmed_for_grouping",
        "no_hit_entry_count", "uncertain_status_count",
        "corpus_total_exact_hits", "corpus_word_bounded_hits",
        "corpus_word_bounded_unique_entries", "corpus_substring_only_hits",
        "ai_status_counts", "rank_suggestion_counts_unverified", "phrase_type_counts",
        "audit_flags", "recommended_action", "recommended_rank_or_status_scope",
        "audit_note", "batch_divergence_example_ids",
        "example_1_entry_id", "example_1_entry_text",
        "example_2_entry_id", "example_2_entry_text",
        "example_3_entry_id", "example_3_entry_text",
        "human_decision", "human_approved_span_exact",
        "human_rank_or_status_decision", "human_notes",
    ]
    worksheet_path = OUTPUT_DIR / "PHRASE_REVIEW_WORKSHEET_V1.csv"
    write_csv(worksheet_path, worksheet_rows, worksheet_fields)

    none_fields = [
        "entry_id", "printed_page_num", "entry_number_verbatim", "ai_status",
        "ai_context_note_spans_exact", "audit_tags", "ai_reason",
        "entry_text_verbatim", "human_decision", "human_notes",
    ]
    none_path = OUTPUT_DIR / "NONE_FOUND_AUDIT_161.csv"
    write_csv(none_path, none_found_rows, none_fields)

    action_counts = Counter(r["recommended_action"] for r in worksheet_rows)
    none_tag_counts = Counter(tag for r in none_found_rows for tag in r["audit_tags"].split(";"))

    briefing_lines = [
        "# Phrase Review v1 Briefing: 148 No-Hit AI Phrase Groups and 161 None-Found Entries",
        "",
        "**Status:** prepared for human review; zero human decisions or production rules approved.",
        "",
        "## 1. Construction-Family Overview (148 Phrases, 1,050 No-Hit Entries)",
        "",
        "| Construction Family | Phrases | No-Hit Entries | Sum of Corpus Word-Bounded Entry Hits |",
        "| --- | ---: | ---: | ---: |",
    ]
    for fam in FAMILY_ORDER:
        s = family_summary[fam]
        briefing_lines.append(
            f"| `{fam}` | {s['phrases']} | {s['no_hit_entries']} | {s['corpus_bounded_entries']} |"
        )
    briefing_lines.extend([
        "",
        "Note: corpus word-bounded entry sums can overlap across phrases (e.g., `صحابي` and `صحابي مشهور`) and are diagnostic counts, not label counts.",
        "",
        "## 2. Recommended Review Actions (Advisory Only)",
        "",
    ])
    for act, cnt in sorted(action_counts.items()):
        briefing_lines.append(f"- `{act}`: {cnt} phrases")
    briefing_lines.extend([
        "",
        "## 3. Concrete Defects and Traps Detected Before Rule Promotion",
        "",
        "1. **AI span truncations or over-long spans (must revise before promoting):**",
        "   - `صحابية مشهور` (3 entries): missing final `ة`; source entries read `صحابية مشهورة`.",
        "   - `وثقه يعقوب ابن` (`S3076-P325-C007-E3643`): truncated mid-name; full span is `وثقه يعقوب ابن سفيان`.",
        "   - `ضعفه الأزدي من الرابعة ق` (`S3076-P387-C009-E4528`): appends generation and sigla (`من الرابعة ق`).",
        "   - `ضعفه يحيى ابن معين ورمي بالإرجاء من التاسعة مات سنة خمس عشرة ت` (`S3076-P194-C002-E1726`): merges grade, innovation note, generation, death date, and sigla.",
        "2. **Non-grade or non-first-phrase spans:**",
        "   - `ثقات الأمراء` (`S3076-P549-C006-E6937`): reads `من ثقات الأمراء` (military/political leadership), not a hadith reliability grade.",
        "   - `وقد وثق` (`S3076-P433-C010-E5214`): preceded by `ليس بمشهور` and bracketed (`ليس بمشهور [وقد وثق]`).",
        "   - `ليس بأهل أن يروى عنه` (`E1141`, `E7777`): historical/tamyiz entries (al-Hajjaj b. Yusuf, Yazid b. Muawiyah).",
        "3. **AI batch divergences on identical constructions (17 phrases):**",
        "   - `وثقه النسائي` (10 Rank 3 vs 7 unresolved), `وثقه العجلي` (10 Rank 3 vs 6 unresolved), `وثقه ابن معين` (6 Rank 3 vs 5 unresolved), `وثقه ابن حبان` (5 Rank 3 vs 1 unresolved), `ذكره ابن حبان في ثقات التابعين` (4 Rank 3 vs 1 unresolved): Batch 1 treated attributed grades as unresolved while Batches 2-3 applied Policy v0.2.",
        "   - `لا تعرف` (18 conditional vs 10 unresolved) and `لا يعرف` (17 conditional vs 7 unresolved): same Rank 7 vs 9 evidence gap labeled inconsistently across batches.",
        "4. **Corpus substring collisions (never match without Arabic-letter boundaries):**",
        "   - `بدري`: 23 of 33 corpus hits are substrings of the tribal nisba `العبدري`.",
        "   - `ثقه`: 79 of 84 corpus hits are substrings of `وثقه` / `وثقها` / `أوثقه`; only 5 are standalone `ثقه` (orthographic variant of `ثقة`, including compounds `ثقه مقل عابد` and `ثقه عابد`).",
        "   - `حافظ`: 12 of 158 hits are inside `الحافظ` / `بالحافظ` (including negation `لم يكن بالحافظ`); in `E7591` (`حافظ إلا أنهم اتهموه بسرقة الحديث`) it co-occurs with an accusation of hadith theft.",
        "   - `صحابي`: 113 of 682 corpus hits are substrings (`الصحابي`, `صحابية`, `صحابيات`), including `غير الصحابي`, and 6 no-hit entries have trailing disputes (`وقيل لا صحبة له`, `نفاها بعضهم`, `لم يصح الإسناد إليه`).",
        "5. **Audit of the 161 `none_found` rows (`NONE_FOUND_AUDIT_161.csv`):**",
        "   - 138 `no_candidate` + 23 `unresolved` rows had `none_found` as `ai_first_grade_span_exact`.",
        "   - Tag summary: " + ", ".join(f"`{k}` ({v})" for k, v in sorted(none_tag_counts.items())),
        "   - Notable edge cases: 7 entries contain `رسول الله` (e.g., `شاعر رسول الله ﷺ`, `سبط رسول الله ﷺ`, `مولى رسول الله ﷺ`, `بنت رسول الله ﷺ`, `ابن عم رسول الله ﷺ`); `S3076-P164-C019-E1301` has empty text (`١٣٠١-`); `S3076-P732-C001-E8509` contains an inline HTML `<span data-type=\"title\" id=toc-208>` tag inside `لم يسم`.",
        "",
        "## 4. How to Complete Human Decisions",
        "",
        "Review [PHRASE_REVIEW_WORKSHEET_V1.csv](PHRASE_REVIEW_WORKSHEET_V1.csv) by `construction_family` and fill only the four trailing human columns:",
        "- `human_decision`: `accept`, `revise`, `conditional`, or `abstain`",
        "- `human_approved_span_exact`: required when `revise` (or confirming exact wording)",
        "- `human_rank_or_status_decision`: e.g. `1_status`, `3_attributed_proxy`, `7_or_9_conditional`, `exclude_non_grade`",
        "- `human_notes`: rationale or precondition notes",
        "",
    ])
    briefing_text = "\n".join(briefing_lines)
    assert_no_em_en_dash(briefing_text, "PHRASE_REVIEW_BRIEFING.md")
    briefing_path = OUTPUT_DIR / "PHRASE_REVIEW_BRIEFING.md"
    briefing_path.write_text(briefing_text, encoding="utf-8", newline="\n")

    readme_lines = [
        "# Taqrīb Phrase Review Package v1 (2026-11-15)",
        "",
        "Structured human-review workspace generated from `CONSOLIDATED_V1_3` (1,211 no-hit entries, 148 grouped phrase strings) and audited against all 8,827 numbered local entries in `ENTRY_INDEX.csv`.",
        "",
        "- [PHRASE_REVIEW_BRIEFING.md](PHRASE_REVIEW_BRIEFING.md): construction-family summary, detected span defects, batch divergences, and substring hazards.",
        "- [PHRASE_REVIEW_WORKSHEET_V1.csv](PHRASE_REVIEW_WORKSHEET_V1.csv): all 148 phrase groups sorted by construction family and frequency, with blank human decision columns.",
        "- [NONE_FOUND_AUDIT_161.csv](NONE_FOUND_AUDIT_161.csv): all 161 `none_found` entries (`138 no_candidate + 23 unresolved`) with deterministic audit tags and blank human decision columns.",
        "",
        "All prior files in `rank_label_no_hit_ai_review_v1_2026-11-15/` and `rank_label_candidate_inventory_v0_2_2026-11-15/` remain unmodified. Zero human labels or production rules are enabled here.",
        "",
    ]
    readme_text = "\n".join(readme_lines)
    assert_no_em_en_dash(readme_text, "README.md")
    readme_path = OUTPUT_DIR / "README.md"
    readme_path.write_text(readme_text, encoding="utf-8", newline="\n")

    outputs = [worksheet_path, none_path, briefing_path, readme_path]
    manifest = {
        "package": "Taqrib phrase review v1 (from no-hit AI review v1.3)",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "human review worksheet ready; zero human labels or production rules approved",
        "counts": {
            "phrase_groups_in_worksheet": len(worksheet_rows),
            "no_hit_entries_covered_by_phrases": sum(int(r["no_hit_entry_count"]) for r in worksheet_rows),
            "none_found_entries_audited": len(none_found_rows),
            "total_no_hit_entries_accounted_for": sum(int(r["no_hit_entry_count"]) for r in worksheet_rows) + len(none_found_rows),
            "family_summary": family_summary,
            "recommended_action_counts": dict(action_counts),
            "none_found_audit_tag_counts": dict(none_tag_counts),
        },
        "input_hashes": {
            "CONSOLIDATED_V1_3/REVIEW_RESULTS_MANIFEST.json": sha256(CONSOLIDATED_DIR / "REVIEW_RESULTS_MANIFEST.json"),
            "rank_label_candidate_inventory_v0_2_2026-11-15/MANIFEST.json": sha256(INV_V02_DIR / "MANIFEST.json"),
            "rank_label_shadow_run_v1_2026-11-15/RUN_MANIFEST.json": sha256(SHADOW_DIR / "RUN_MANIFEST.json"),
        },
        "outputs": {path.name: sha256(path) for path in outputs},
    }
    manifest_str = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    assert_no_em_en_dash(manifest_str, "MANIFEST.json")
    manifest_path = OUTPUT_DIR / "MANIFEST.json"
    manifest_path.write_text(manifest_str, encoding="utf-8", newline="\n")
    (OUTPUT_DIR / "MANIFEST.sha256").write_text(f"{sha256(manifest_path)}  MANIFEST.json\n", encoding="utf-8", newline="\n")

    print(f"Created {OUTPUT_DIR} with {len(worksheet_rows)} phrase groups and {len(none_found_rows)} none_found rows.")


if __name__ == "__main__":
    main()
