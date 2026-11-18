#!/usr/bin/env python3
"""Prepare a non-overwriting AI advisory proposal package for Batch 02 (889 cases).

Reads the verified Batch 02 review package and Draft Codebook v0.1, checks local
Arabic token boundaries, negations, referent shifts, attributions, and trailing
qualifications, and writes a separate AI advisory file without touching any
human worksheet or assigning canonical ranks or numeric scores.
"""

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
B2_DIR = PIPELINE / "evaluation_statement_occurrence_review_batch_02_v0_1_2026-11-16"
CODEBOOK_PATH = PIPELINE / "evaluation_statement_layer_v0_1_2026-11-16/EVALUATIVE_STATEMENT_LAYER_CODEBOOK_DRAFT_V0_1.md"
OUT_DIR = PIPELINE / "evaluation_statement_occurrence_advisory_batch_02_v0_1_2026-11-16"

ARABIC_LETTER = re.compile(r"[\u0621-\u064a\u066e-\u06d3\u06fa-\u06fc]")

ALLOWED_MATCH_USE = {
    "complete_statement",
    "component_of_larger_statement",
    "unrelated_substring",
    "unresolved",
}
ALLOWED_FAMILY = {
    "praise",
    "criticism",
    "mixed",
    "unknownness",
    "status_or_biography",
    "non_evaluative_other",
    "unresolved",
    "not_applicable",
}
ALLOWED_DOMAIN = {
    "general_reliability",
    "memory_precision",
    "honesty_veracity",
    "fabrication",
    "transmission_practice",
    "unknownness_or_majhul_status",
    "companion_status",
    "doctrinal_position",
    "jurisprudential_or_scholarly_merit",
    "biographical_information",
    "other",
    "unresolved",
    "not_applicable",
}
ALLOWED_CONTENT = {
    "general_commendation",
    "qualified_commendation",
    "superlative_commendation",
    "general_criticism",
    "accusation_of_lying",
    "applied_liar_label",
    "fabrication_label",
    "specific_transmission_criticism",
    "hadith_theft_or_appropriation",
    "unknownness_assertion",
    "status_assertion",
    "biographical_fact",
    "mixed_assessment",
    "other",
    "unresolved",
    "not_applicable",
}
ALLOWED_MODE = {
    "direct_statement",
    "attributed_individual_judgement",
    "reported_or_hedged_claim",
    "specific_behavior_or_transmission_observation",
    "first_person_knowledge_gap",
    "status_or_biographical_statement",
    "unresolved",
    "not_applicable",
}
ALLOWED_FORCE = {
    "qualified_limited",
    "plain_direct",
    "emphatic",
    "superlative",
    "unresolved",
    "not_applicable",
}
ALLOWED_CONSENSUS = {
    "none",
    "collective_agreement_claimed",
    "unanimity_wording_claimed",
    "scope_or_referents_unclear",
    "unresolved",
    "not_applicable",
}
ALLOWED_CONFIDENCE = {"high", "medium", "low"}

# Base descriptor template per canonical phrase:
# (family, domain, content, mode, force, consensus, confidence, base_attribution, base_rationale)
# More specific/longer phrases take precedence when multiple overlap in a case.
PHRASE_TEMPLATES: dict[str, tuple[str, str, str, str, str, str, str, str, str]] = {
    # --- Superlative & compound praise ---
    "جبل الحفظ وإمام الدنيا في فقه الحديث": (
        "praise", "unresolved", "superlative_commendation", "direct_statement", "superlative", "none", "medium", "",
        "Combines metaphorical memorization praise (جبل الحفظ) and scholarly standing (إمام الدنيا في فقه الحديث); keep distinct subclaims visible.",
    ),
    "أحد العلماء الأثبات الفقهاء الكبار": (
        "praise", "unresolved", "superlative_commendation", "direct_statement", "superlative", "none", "medium", "",
        "Multi-domain superlative/compound praise covering scholarship, reliability (أثبات), and jurisprudence (فقهاء).",
    ),
    "ثقة لكنه تغير بأخرة فلم يفحش اختلاطه": (
        "mixed", "memory_precision", "mixed_assessment", "direct_statement", "qualified_limited", "none", "high", "",
        "Combines positive reliability with a bounded late-life memory change qualification (فلم يفحش اختلاطه).",
    ),
    "لكنه تغير بأخرة فلم يفحش اختلاطه": (
        "mixed", "memory_precision", "mixed_assessment", "direct_statement", "qualified_limited", "none", "high", "",
        "Temporal memory qualification attached to the preceding reliability grade.",
    ),
    "ثقة فقيه عابد": (
        "praise", "unresolved", "general_commendation", "direct_statement", "plain_direct", "none", "medium", "",
        "Compound praise combining reliability (ثقة), fiqh learning (فقيه), and devotion (عابد); preserve all dimensions.",
    ),
    "ثقة ثبت": (
        "praise", "general_reliability", "general_commendation", "direct_statement", "plain_direct", "none", "high", "",
        "Compound reliability commendation; inspect surrounding entry for attached qualifications or doctrinal notes.",
    ),
    "ثقة متقن": (
        "praise", "memory_precision", "general_commendation", "direct_statement", "plain_direct", "none", "high", "",
        "Compound praise combining reliability and precision; preserve both components.",
    ),
    "ثقة متقنا": (
        "praise", "memory_precision", "general_commendation", "direct_statement", "plain_direct", "none", "high", "",
        "Inflected compound praise combining reliability and precision.",
    ),
    "ثقة حافظ": (
        "praise", "unresolved", "general_commendation", "direct_statement", "plain_direct", "none", "medium", "",
        "Combines general reliability (ثقة) with memorization standing (حافظ); preserve both dimensions.",
    ),
    "ثقة ثقة": (
        "praise", "general_reliability", "general_commendation", "direct_statement", "emphatic", "none", "medium", "",
        "Repeated commendation wording (ثقة ثقة); check entry for explicit critic attribution or trailing notes.",
    ),
    "صدوق حافظ": (
        "praise", "unresolved", "general_commendation", "direct_statement", "plain_direct", "none", "medium", "",
        "Compound praise combining truthfulness (صدوق) and memorization (حافظ); check entry for later errors or critic notes.",
    ),
    "صدوق يخطىء": (
        "mixed", "memory_precision", "mixed_assessment", "direct_statement", "qualified_limited", "none", "high", "",
        "Combines positive truthfulness (صدوق) with an error qualification (يخطىء); preserve both parts together.",
    ),
    "صدوق يهم": (
        "mixed", "memory_precision", "mixed_assessment", "direct_statement", "qualified_limited", "none", "high", "",
        "Combines positive truthfulness (صدوق) with a delusion/error qualification (يهم); preserve both parts together.",
    ),
    "صدوق سيء الحفظ": (
        "mixed", "memory_precision", "mixed_assessment", "direct_statement", "qualified_limited", "none", "high", "",
        "Combines positive truthfulness (صدوق) with poor memory qualification (سيء الحفظ); preserve both parts together.",
    ),
    "مستقيم الحديث إلا في حديث واحد يقال إن ابنه محمدا أدخله عليه": (
        "mixed", "memory_precision", "qualified_commendation", "direct_statement", "qualified_limited", "none", "high", "",
        "Positive hadith-integrity claim explicitly bounded by a single-hadith exception attributed to his son's insertion.",
    ),
    "صالح الحديث إلا عن بقية": (
        "mixed", "transmission_practice", "qualified_commendation", "direct_statement", "qualified_limited", "none", "high", "",
        "Positive assessment explicitly limited by an exception on transmissions from Baqiyyah.",
    ),
    "مجمع على ثقته": (
        "praise", "general_reliability", "general_commendation", "direct_statement", "plain_direct", "unanimity_wording_claimed", "medium", "",
        "Reports unanimity wording on reliability (مجمع على ثقته); records text claim only, not verified historical consensus.",
    ),
    "أجمعوا على ثقته": (
        "praise", "general_reliability", "general_commendation", "reported_or_hedged_claim", "plain_direct", "unanimity_wording_claimed", "medium", "",
        "Reports unanimity wording; check preceding attribution.",
    ),
    "من كبار التابعين الثقات": (
        "praise", "general_reliability", "general_commendation", "direct_statement", "plain_direct", "none", "medium", "",
        "Combines Tabi'i generational standing with reliability praise; check for critic attribution (e.g., العجلي).",
    ),
    "ذكره ابن حبان في ثقات التابعين": (
        "praise", "general_reliability", "general_commendation", "attributed_individual_judgement", "plain_direct", "none", "medium", "ابن حبان",
        "Reports Ibn Hibban's inclusion of the narrator in Thiqat al-Tabi'in; preserve attribution to Ibn Hibban.",
    ),
    "ذكره جماعة في ثقات التابعين": (
        "praise", "general_reliability", "general_commendation", "reported_or_hedged_claim", "plain_direct", "scope_or_referents_unclear", "medium", "جماعة (unnamed group)",
        "Reports inclusion in Thiqat al-Tabi'in by an unnamed group (جماعة).",
    ),
    "ذكره ابن حبان في الثقات": (
        "praise", "general_reliability", "general_commendation", "attributed_individual_judgement", "plain_direct", "none", "medium", "ابن حبان",
        "Reports Ibn Hibban's inclusion of the narrator in al-Thiqat; preserve attribution.",
    ),
    "ثقات التابعين": (
        "praise", "general_reliability", "general_commendation", "reported_or_hedged_claim", "plain_direct", "none", "medium", "",
        "Refers to trusted Tabi'in lists; inspect surrounding text for the citing authority (e.g., Ibn Hibban, al-'Ijli).",
    ),
    "وثقه أبو زرعة في الحديث": (
        "praise", "general_reliability", "qualified_commendation", "attributed_individual_judgement", "qualified_limited", "none", "high", "أبو زرعة",
        "Attributes authentication in hadith specifically to Abu Zur'a; check following political/character notes.",
    ),
    "وثقه أبو داود وغيره": (
        "praise", "general_reliability", "general_commendation", "attributed_individual_judgement", "plain_direct", "none", "medium", "أبو داود وغيره",
        "Attributes authentication to Abu Dawud plus unspecified others (وغيره).",
    ),
    "وثقه العجلي وجماعة": (
        "praise", "general_reliability", "general_commendation", "attributed_individual_judgement", "plain_direct", "scope_or_referents_unclear", "medium", "العجلي وجماعة",
        "Attributes authentication to al-'Ijli plus an unnamed group (وجماعة).",
    ),
    "وثقه الأئمة": (
        "praise", "general_reliability", "general_commendation", "reported_or_hedged_claim", "plain_direct", "scope_or_referents_unclear", "medium", "الأئمة (unnamed collective)",
        "Reports authentication by 'the Imams' without naming individuals; check entry for dissenting critics.",
    ),
    "وثقه الجمهور": (
        "praise", "general_reliability", "general_commendation", "reported_or_hedged_claim", "plain_direct", "collective_agreement_claimed", "medium", "الجمهور (unnamed majority)",
        "Reports authentication by 'the majority'; check entry for following weakness or memory-change notes.",
    ),
    "وثقه ابن معين": (
        "praise", "general_reliability", "general_commendation", "attributed_individual_judgement", "plain_direct", "none", "high", "ابن معين",
        "Explicitly attributed authentication by Ibn Ma'in.",
    ),
    "وثقه النسائي": (
        "praise", "general_reliability", "general_commendation", "attributed_individual_judgement", "plain_direct", "none", "high", "النسائي",
        "Explicitly attributed authentication by al-Nasa'i.",
    ),
    "وثقه العجلي": (
        "praise", "general_reliability", "general_commendation", "attributed_individual_judgement", "plain_direct", "none", "high", "العجلي",
        "Explicitly attributed authentication by al-'Ijli.",
    ),
    "وثقها العجلي": (
        "praise", "general_reliability", "general_commendation", "attributed_individual_judgement", "plain_direct", "none", "high", "العجلي",
        "Explicitly attributed authentication of a female narrator by al-'Ijli.",
    ),
    "وثقه ابن حبان": (
        "praise", "general_reliability", "general_commendation", "attributed_individual_judgement", "plain_direct", "none", "high", "ابن حبان",
        "Explicitly attributed authentication by Ibn Hibban.",
    ),
    "وثقه أبو زرعة": (
        "praise", "general_reliability", "general_commendation", "attributed_individual_judgement", "plain_direct", "none", "high", "أبو زرعة",
        "Explicitly attributed authentication by Abu Zur'a.",
    ),
    "وثقه أبو حاتم": (
        "praise", "general_reliability", "general_commendation", "attributed_individual_judgement", "plain_direct", "none", "high", "أبو حاتم",
        "Explicitly attributed authentication by Abu Hatim.",
    ),
    "وثقه الدارقطني": (
        "praise", "general_reliability", "general_commendation", "attributed_individual_judgement", "plain_direct", "none", "high", "الدارقطني",
        "Explicitly attributed authentication by al-Daraqutni.",
    ),
    "وثقه الشافعي": (
        "praise", "general_reliability", "general_commendation", "attributed_individual_judgement", "plain_direct", "none", "high", "الشافعي",
        "Explicitly attributed authentication by al-Shafi'i.",
    ),
    "وثقه ابن سعد": (
        "praise", "general_reliability", "general_commendation", "attributed_individual_judgement", "plain_direct", "none", "high", "ابن سعد",
        "Explicitly attributed authentication by Ibn Sa'd.",
    ),
    "وثقه الخطيب": (
        "praise", "general_reliability", "general_commendation", "attributed_individual_judgement", "plain_direct", "none", "high", "الخطيب",
        "Explicitly attributed authentication by al-Khatib al-Baghdadi.",
    ),
    "وثقه يعقوب ابن": (
        "praise", "general_reliability", "general_commendation", "attributed_individual_judgement", "plain_direct", "none", "high", "يعقوب ابن سفيان",
        "Truncated span in source index; full entry phrase is وثقه يعقوب ابن سفيان.",
    ),
    "وثقه": (
        "praise", "general_reliability", "general_commendation", "attributed_individual_judgement", "plain_direct", "none", "medium", "",
        "Verb 'authenticated him'; expand to the full critic name or clause in the entry.",
    ),
    "وقد وثق": (
        "praise", "general_reliability", "general_commendation", "reported_or_hedged_claim", "plain_direct", "none", "medium", "",
        "Passive authentication claim ('has been authenticated'), often bracketed or paired with an unknownness/obscurity note.",
    ),
    "أحد الحفاظ": (
        "praise", "memory_precision", "general_commendation", "direct_statement", "plain_direct", "none", "medium", "",
        "Memory/scholarship descriptor ('one of the huffaz'); inspect entry for any following oddity or criticism.",
    ),
    "أحد الحفاط": (
        "praise", "memory_precision", "general_commendation", "direct_statement", "plain_direct", "none", "medium", "",
        "Source-text orthographic variant for أحد الحفاظ; preserve exact spelling.",
    ),
    "حافظ": (
        "praise", "memory_precision", "general_commendation", "direct_statement", "plain_direct", "none", "medium", "",
        "Memory/scholarship descriptor (حافظ); check whether standalone praise or paired with adverse notes.",
    ),
    "ثقة": (
        "praise", "general_reliability", "general_commendation", "direct_statement", "plain_direct", "none", "high", "",
        "Standard direct reliability commendation; check surrounding entry for attached qualifications.",
    ),
    "ثقه": (
        "praise", "general_reliability", "general_commendation", "direct_statement", "plain_direct", "none", "high", "",
        "Orthographic variant of ثقة (final ha); preserve verbatim and check following attributes.",
    ),
    "ثبت": (
        "praise", "general_reliability", "general_commendation", "direct_statement", "plain_direct", "none", "high", "",
        "Reliability/firmness commendation; verify full compound or attached context.",
    ),
    "متقن": (
        "praise", "memory_precision", "general_commendation", "direct_statement", "plain_direct", "none", "high", "",
        "Precision commendation; check whether part of a compound praise phrase.",
    ),
    "عدل": (
        "praise", "general_reliability", "general_commendation", "direct_statement", "plain_direct", "none", "medium", "",
        "Reliability/uprightness commendation; verify exact word boundary.",
    ),
    "صدوق": (
        "praise", "general_reliability", "general_commendation", "direct_statement", "plain_direct", "none", "high", "",
        "Direct truthfulness commendation; check entry for attached memory or transmission qualifications.",
    ),
    "لا بأس به": (
        "praise", "general_reliability", "general_commendation", "direct_statement", "plain_direct", "none", "high", "",
        "Standard middling/positive reliability phrase; check entry for attached exceptions or attributions.",
    ),
    "ليس به بأس": (
        "praise", "general_reliability", "general_commendation", "direct_statement", "plain_direct", "none", "high", "",
        "Standard middling/positive reliability phrase.",
    ),
    "ما به بأس": (
        "praise", "general_reliability", "general_commendation", "direct_statement", "plain_direct", "none", "high", "",
        "Middling/positive reliability phrase equivalent in form to لا بأس به.",
    ),
    "لا بأس بحديثه": (
        "praise", "transmission_practice", "qualified_commendation", "direct_statement", "qualified_limited", "none", "high", "",
        "Hadith-transmission praise; inspect entry for route-specific restrictions.",
    ),
    "صالح الحديث": (
        "praise", "general_reliability", "qualified_commendation", "direct_statement", "plain_direct", "none", "medium", "",
        "Middling/acceptable hadith-level commendation; check for attached exceptions or critic attributions.",
    ),
    "قال ابن معين صالح": (
        "praise", "general_reliability", "qualified_commendation", "attributed_individual_judgement", "plain_direct", "none", "medium", "ابن معين",
        "Attributed commendation by Ibn Ma'in (صالح); preserve attribution and exact wording.",
    ),
    "أثنى عليه": (
        "praise", "other", "general_commendation", "attributed_individual_judgement", "plain_direct", "none", "medium", "",
        "General praise verb ('praised him'); expand to capture any named subject/critic.",
    ),
    "مقبول": (
        "praise", "general_reliability", "qualified_commendation", "direct_statement", "qualified_limited", "none", "medium", "",
        "Taqrib conditional-acceptance term (مقبول); keep separate from unqualified reliability.",
    ),
    "ثقات الأمراء": (
        "status_or_biography", "biographical_information", "biographical_fact", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Biographical/political description ('among trustworthy commanders'), not a hadith narrator reliability grade.",
    ),

    # --- Companion status (direct vs disputed/ruyah) ---
    "من السابقين الأولين هاجر الهجرتين وشهد المشاهد": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Direct Companion biographical/status assertion combining precedence, migrations, and battles.",
    ),
    "أحد العشرة المشهود لهم بالجنة": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Companion status assertion identifying one of the ten promised Paradise.",
    ),
    "أحد السابقين الأولين": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Companion status assertion identifying one of the foremost early Muslims.",
    ),
    "من السابقين الأولين": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Companion status assertion identifying an early Muslim.",
    ),
    "من قدماء المهاجرين": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Companion status assertion identifying an early Emigrant (Muhajir).",
    ),
    "أسلم قديما وهاجر الهجرتين": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Companion status assertion describing early conversion and both migrations.",
    ),
    "خادم رسول الله ﷺ خدمه عشر سنين": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Companion biographical assertion describing prolonged service to the Prophet.",
    ),
    "مولى النبي ﷺ وخادمه": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Companion biographical assertion identifying a freedman and attendant of the Prophet.",
    ),
    "حاضنة النبي ﷺ": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Companion biographical assertion identifying the Prophet's nursemaid/caretaker.",
    ),
    "خادم النبي ﷺ": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Companion biographical assertion identifying an attendant of the Prophet.",
    ),
    "الصديق الأكبر": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Honorific Companion title for Abu Bakr al-Siddiq.",
    ),
    "أحد العشرة": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Companion status title identifying one of the ten promised Paradise.",
    ),
    "أحد النقباء": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Companion status assertion identifying one of the Ansari leaders (nuqaba).",
    ),
    "أم المؤمنين": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Status honorific for a wife of the Prophet; verify whether referent is the entry subject or a relative.",
    ),
    "صحابي من أهل الصفة": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Direct Companion status assertion specifying Ahl al-Suffah.",
    ),
    "فهو صحابي ابن صحابي": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Direct Companion status assertion for both subject and father.",
    ),
    "صحابي ابن صحابي": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Direct Companion status assertion for both subject and father.",
    ),
    "صحابي مشهور": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Direct Companion status assertion with renown descriptor.",
    ),
    "صحابية مشهور": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Truncated span in index; full entry text reads صحابية مشهورة.",
    ),
    "صحابي جليل": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Direct Companion status assertion with honorific modifier.",
    ),
    "صحابي شهير": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Direct Companion status assertion with renown modifier.",
    ),
    "صحابي معروف": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Direct Companion status assertion.",
    ),
    "صحابي كبير": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Direct Companion status assertion indicating senior Companion.",
    ),
    "صحابي صغير": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Direct Companion status assertion indicating young/junior Companion.",
    ),
    "صحابي مقل": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Direct Companion status assertion with few-narrations biographical note.",
    ),
    "صحابي بدري": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Direct Companion status assertion specifying participation at Badr.",
    ),
    "الصحابي الجليل": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Direct Companion status assertion.",
    ),
    "الصحابي": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Companion status noun; check for following modifier (الجليل/المشهور) or negation (غير الصحابي).",
    ),
    "صحابية": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Direct female Companion status assertion.",
    ),
    "صحابي": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Direct Companion status assertion; check entry for any trailing dispute or negation.",
    ),
    "الصحابة": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "medium", "",
        "Plural noun 'the Companions'; inspect context to check whether attributing companionship to subject, a relative, or refuting it.",
    ),
    "له ولأبويه صحبة": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Direct Companion status assertion for the subject and both parents.",
    ),
    "له ولأبيه ولجده صحبه": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Direct Companion status assertion across three generations (preserving spelling صحبه).",
    ),
    "له ولأبيه صحبة": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Direct Companion status assertion for subject and father.",
    ),
    "له ولابنه صحبة": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Direct Companion status assertion for subject and son.",
    ),
    "له صحبة": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Direct Companion status assertion; verify no preceding negation or trailing dispute.",
    ),
    "وله صحبة": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Direct Companion status assertion.",
    ),
    "لها صحبة": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Direct female Companion status assertion.",
    ),
    "له وفادة": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Biographical/status assertion indicating delegation visit to the Prophet.",
    ),
    "من مسلمة الفتح": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Companion status assertion identifying conversion at the Conquest of Makkah.",
    ),
    "شهد بيعة الرضوان": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Companion status assertion recording presence at Bay'at al-Ridwan.",
    ),
    "شهد بدرا وهو مملوك": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Companion biographical/status assertion recording Badr attendance while enslaved.",
    ),
    "شهد بدرا وغيرها": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Companion status assertion recording Badr and subsequent battles.",
    ),
    "شهد بدرا": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Companion status assertion recording attendance at Badr (verify not negated).",
    ),
    "شهد بدر": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Companion status assertion recording attendance at Badr.",
    ),
    "شهد أحدا وما بعدها": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Companion status assertion recording Uhud and subsequent battles.",
    ),
    "شهد أحدا": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Companion status assertion recording attendance at Uhud.",
    ),
    "البدري": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "medium", "",
        "Badr-participant status epithet (check context when plural البدريين or disputed identity).",
    ),
    "بدري": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Badr-participant status epithet when standalone token; watch for tribal nisba العبدري.",
    ),
    "ثم أسلم وصحب": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Biographical/status clause recording conversion and Companionship.",
    ),
    "صحبه وحفظ عنه": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Direct companionship and retention/narration assertion.",
    ),
    "صحبه ولازمه": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Direct companionship and prolonged accompaniment assertion.",
    ),
    "وصحب": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Companionship assertion ('and accompanied'); inspect surrounding clause.",
    ),
    "صحبا": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "not_applicable", "not_applicable", "high", "",
        "Dual verb assertion ('both accompanied' - subject and father).",
    ),

    # --- Disputed Companion / Ruyah ---
    "مختلف في وجوده فقيل صحابي": (
        "status_or_biography", "companion_status", "status_assertion", "reported_or_hedged_claim", "qualified_limited", "none", "low", "",
        "Disputed existence and companionship ('differed on his existence, some said Companion'); keep hedged/disputed.",
    ),
    "مختلف في صحبته": (
        "status_or_biography", "companion_status", "status_assertion", "reported_or_hedged_claim", "qualified_limited", "none", "medium", "",
        "Explicit dispute over Companion status; do not treat as established Rank 1 status.",
    ),
    "قيل له صحبة أو رؤية": (
        "status_or_biography", "companion_status", "status_assertion", "reported_or_hedged_claim", "qualified_limited", "none", "low", "",
        "Hedged/disputed claim offering either companionship or childhood sighting (رؤية).",
    ),
    "قيل إن له هو صحبة": (
        "status_or_biography", "companion_status", "status_assertion", "reported_or_hedged_claim", "qualified_limited", "none", "low", "",
        "Hedged passive report ('it was said he himself has companionship').",
    ),
    "قيل لقهيد صحبة": (
        "status_or_biography", "companion_status", "status_assertion", "reported_or_hedged_claim", "qualified_limited", "none", "low", "",
        "Hedged passive report attributing companionship to Qubayd/Quhayd.",
    ),
    "يقال له صحبة": (
        "status_or_biography", "companion_status", "status_assertion", "reported_or_hedged_claim", "qualified_limited", "none", "medium", "",
        "Hedged report ('he is said to have companionship'); check entry for corroborating or refuting notes.",
    ),
    "يقال لها صحبة": (
        "status_or_biography", "companion_status", "status_assertion", "reported_or_hedged_claim", "qualified_limited", "none", "medium", "",
        "Hedged report ('she is said to have companionship').",
    ),
    "ويقال إن لها صحبة": (
        "status_or_biography", "companion_status", "status_assertion", "reported_or_hedged_claim", "qualified_limited", "none", "medium", "",
        "Hedged report ('and it is said she has companionship').",
    ),
    "قيل له صحبة": (
        "status_or_biography", "companion_status", "status_assertion", "reported_or_hedged_claim", "qualified_limited", "none", "medium", "",
        "Hedged passive report ('it was said he has companionship').",
    ),
    "يقال له رؤية": (
        "status_or_biography", "companion_status", "status_assertion", "reported_or_hedged_claim", "qualified_limited", "none", "low", "",
        "Hedged report of seeing the Prophet (رؤية), distinct from established companionship.",
    ),
    "له رؤية": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "qualified_limited", "none", "medium", "",
        "Sighting of the Prophet (رؤية, often in childhood); keep distinct from full صحبة wording, especially when listed in Thiqat al-Tabi'in.",
    ),
    "لها رؤية": (
        "status_or_biography", "companion_status", "status_assertion", "status_or_biographical_statement", "qualified_limited", "none", "medium", "",
        "Female narrator's sighting of the Prophet (رؤية); keep distinct from full صحبة wording.",
    ),
    "وكأنها صحابية": (
        "status_or_biography", "companion_status", "status_assertion", "reported_or_hedged_claim", "qualified_limited", "none", "low", "",
        "Conjectural/hedged Companion inference ('and as if she were a Companion').",
    ),
    "كأنها صحابية": (
        "status_or_biography", "companion_status", "status_assertion", "reported_or_hedged_claim", "qualified_limited", "none", "low", "",
        "Conjectural/hedged Companion inference ('as if she were a Companion').",
    ),

    # --- Unknownness ---
    "لم أقف على اسمها ولا على حالها": (
        "unknownness", "unknownness_or_majhul_status", "unknownness_assertion", "first_person_knowledge_gap", "qualified_limited", "none", "low", "Unspecified first-person compiler voice",
        "First-person knowledge-gap statement covering both name and status; do not promote automatically to formal majhul rank.",
    ),
    "ما عرف أبو حاتم حاله في الحديث": (
        "unknownness", "unknownness_or_majhul_status", "unknownness_assertion", "attributed_individual_judgement", "qualified_limited", "none", "medium", "أبو حاتم",
        "Attributed unknownness statement scoped to his status in hadith according to Abu Hatim.",
    ),
    "لا يعرف ولم يسم": (
        "unknownness", "unknownness_or_majhul_status", "unknownness_assertion", "direct_statement", "plain_direct", "none", "medium", "",
        "Combined unknownness and unnamed-narrator assertion; check entry for tentative identifications.",
    ),
    "لا يعرف حاله": (
        "unknownness", "unknownness_or_majhul_status", "unknownness_assertion", "direct_statement", "plain_direct", "none", "high", "",
        "Direct unknown-condition statement; distinct from narrator-count resolution (Rank 7 vs Rank 9).",
    ),
    "لا يعرف حالها": (
        "unknownness", "unknownness_or_majhul_status", "unknownness_assertion", "direct_statement", "plain_direct", "none", "high", "",
        "Direct unknown-condition statement for a female narrator.",
    ),
    "مجهول الحال": (
        "unknownness", "unknownness_or_majhul_status", "unknownness_assertion", "direct_statement", "plain_direct", "none", "high", "",
        "Explicit unknown-condition descriptor (مجهول الحال).",
    ),
    "مستور": (
        "unknownness", "unknownness_or_majhul_status", "unknownness_assertion", "direct_statement", "plain_direct", "none", "high", "",
        "Explicit concealed/unknown-condition descriptor (مستور).",
    ),
    "مجهول": (
        "unknownness", "unknownness_or_majhul_status", "unknownness_assertion", "direct_statement", "plain_direct", "none", "high", "",
        "Explicit unknown narrator descriptor (مجهول); verify referent and context.",
    ),
    "لا أعرفه": (
        "unknownness", "unknownness_or_majhul_status", "unknownness_assertion", "first_person_knowledge_gap", "plain_direct", "none", "medium", "",
        "First-person knowledge-gap statement; check preceding attribution (e.g., قال النسائي) and pronoun referent.",
    ),
    "لا تعرف": (
        "unknownness", "unknownness_or_majhul_status", "unknownness_assertion", "direct_statement", "plain_direct", "none", "medium", "",
        "Unknownness assertion for a female narrator; verify exact referent in entry.",
    ),
    "لا يعرف": (
        "unknownness", "unknownness_or_majhul_status", "unknownness_assertion", "direct_statement", "plain_direct", "none", "medium", "",
        "Unknownness assertion; verify referent and check whether part of لا يعرف حاله or similar.",
    ),

    # --- Memory, mild weakness, weakness, & transmission notes ---
    "خلط بعد احتراق كتبه": (
        "criticism", "memory_precision", "specific_transmission_criticism", "direct_statement", "qualified_limited", "none", "high", "",
        "Specific event-conditioned memory-mixing note (after his books burned).",
    ),
    "مخلط في غيرهم": (
        "criticism", "memory_precision", "specific_transmission_criticism", "direct_statement", "qualified_limited", "none", "high", "",
        "Route/region-scoped mixing criticism (in transmissions other than his local circle).",
    ),
    "خلط في غيره": (
        "criticism", "memory_precision", "specific_transmission_criticism", "direct_statement", "qualified_limited", "none", "high", "",
        "Scope-restricted mixing criticism (mixed in material other than the specified book/source).",
    ),
    "ورواية ابن المبارك وابن وهب عنه أعدل من غيرهما": (
        "mixed", "transmission_practice", "qualified_commendation", "specific_behavior_or_transmission_observation", "qualified_limited", "none", "high", "",
        "Comparative transmission-route note favoring Ibn al-Mubarak and Ibn Wahb's narrations from him.",
    ),
    "تغير بأخرة": (
        "criticism", "memory_precision", "specific_transmission_criticism", "direct_statement", "qualified_limited", "none", "high", "",
        "Temporal memory-change observation (changed in later life).",
    ),
    "له أوهام": (
        "criticism", "memory_precision", "specific_transmission_criticism", "direct_statement", "plain_direct", "none", "high", "",
        "Memory/error note recording occurrences of delusions/errors (له أوهام).",
    ),
    "يخطىء": (
        "criticism", "memory_precision", "specific_transmission_criticism", "direct_statement", "plain_direct", "none", "medium", "",
        "Error-proneness observation; check whether part of صدوق يخطىء.",
    ),
    "يخطئ": (
        "criticism", "memory_precision", "specific_transmission_criticism", "direct_statement", "plain_direct", "none", "medium", "",
        "Error-proneness observation.",
    ),
    "سيء الحفظ": (
        "criticism", "memory_precision", "general_criticism", "direct_statement", "plain_direct", "none", "high", "",
        "Explicit poor-memory criticism; check whether paired with صدوق.",
    ),
    "عابوا عليه أنه حدث عن أبيه بغير سماع": (
        "criticism", "transmission_practice", "specific_transmission_criticism", "reported_or_hedged_claim", "plain_direct", "scope_or_referents_unclear", "medium", "Unnamed plural critics",
        "Specific transmission criticism regarding narrating from his father without direct hearing.",
    ),
    "ضعف مع إمامته ومعرفته": (
        "mixed", "general_reliability", "mixed_assessment", "direct_statement", "qualified_limited", "none", "high", "",
        "Mixed wording pairing weakness (ضعف) with scholarly eminence and knowledge.",
    ),
    "ضعفوه لكثرة تدليسه": (
        "criticism", "transmission_practice", "specific_transmission_criticism", "reported_or_hedged_claim", "plain_direct", "scope_or_referents_unclear", "medium", "Unnamed plural critics",
        "Reasoned plural weakness attribution citing excessive tadlis.",
    ),
    "ضعفه يحيى ابن معين ورمي بالإرجاء من التاسعة مات سنة خمس عشرة ت": (
        "criticism", "general_reliability", "general_criticism", "attributed_individual_judgement", "plain_direct", "none", "high", "يحيى ابن معين",
        "Over-long span in index; trim target statement to ضعفه يحيى ابن معين and treat ورمي بالإرجاء separately.",
    ),
    "ضعفه الأزدي من الرابعة ق": (
        "criticism", "general_reliability", "general_criticism", "attributed_individual_judgement", "plain_direct", "none", "high", "الأزدي",
        "Over-long span in index; trim target statement to ضعفه الأزدي (excluding generation and sigla).",
    ),
    "ضعفه أبو حاتم": (
        "criticism", "general_reliability", "general_criticism", "attributed_individual_judgement", "plain_direct", "none", "high", "أبو حاتم",
        "Explicitly attributed weakness judgment by Abu Hatim.",
    ),
    "ضعفه أبو زرعة": (
        "criticism", "general_reliability", "general_criticism", "attributed_individual_judgement", "plain_direct", "none", "high", "أبو زرعة",
        "Explicitly attributed weakness judgment by Abu Zur'a.",
    ),
    "ليس بالقوي وقد تغير في آخر عمره": (
        "criticism", "memory_precision", "general_criticism", "direct_statement", "qualified_limited", "none", "high", "",
        "Combined weakness and late-life memory change statement.",
    ),
    "ليس بالقوي": (
        "criticism", "general_reliability", "general_criticism", "direct_statement", "qualified_limited", "none", "high", "",
        "Direct mild/moderate weakness phrase ('not strong').",
    ),
    "فيه ضعف": (
        "criticism", "general_reliability", "general_criticism", "direct_statement", "qualified_limited", "none", "high", "",
        "Direct weakness phrase ('there is weakness in him').",
    ),
    "في حديثه لين": (
        "criticism", "transmission_practice", "specific_transmission_criticism", "direct_statement", "qualified_limited", "none", "high", "",
        "Mild weakness scoped specifically to his hadith ('softness in his hadith').",
    ),
    "لين الحديث": (
        "criticism", "general_reliability", "general_criticism", "direct_statement", "qualified_limited", "none", "high", "",
        "Standard mild-weakness phrase ('mild/soft in hadith').",
    ),
    "فيه لين": (
        "criticism", "general_reliability", "general_criticism", "direct_statement", "qualified_limited", "none", "high", "",
        "Mild-weakness phrase ('there is softness in him').",
    ),
    "ليّن": (
        "criticism", "general_reliability", "general_criticism", "direct_statement", "qualified_limited", "none", "high", "",
        "Vocalized mild-weakness adjective (ليّن).",
    ),
    "لين": (
        "criticism", "general_reliability", "general_criticism", "direct_statement", "qualified_limited", "none", "medium", "",
        "Mild-weakness term (لين); check surrounding context for route restriction (e.g., لين في غيره).",
    ),
    "ضعيف": (
        "criticism", "general_reliability", "general_criticism", "direct_statement", "plain_direct", "none", "high", "",
        "Standard weakness label (ضعيف); inspect entry for any qualifiers or attributions.",
    ),
    "منكر الحديث": (
        "criticism", "transmission_practice", "specific_transmission_criticism", "direct_statement", "plain_direct", "none", "high", "",
        "Transmission-criticism phrase denoting rejected/anomalous hadith (منكر الحديث).",
    ),

    # --- Severe criticism, lying, fabrication, abandonment ---
    "متروك الحديث": (
        "criticism", "general_reliability", "general_criticism", "direct_statement", "plain_direct", "none", "high", "",
        "Severe abandonment label scoped to hadith transmission (متروك الحديث).",
    ),
    "متروك": (
        "criticism", "general_reliability", "general_criticism", "direct_statement", "plain_direct", "none", "high", "",
        "Severe abandonment label (متروك).",
    ),
    "تركه الدارقطني": (
        "criticism", "general_reliability", "general_criticism", "attributed_individual_judgement", "plain_direct", "none", "high", "الدارقطني",
        "Attributed abandonment judgment by al-Daraqutni.",
    ),
    "تركوه": (
        "criticism", "general_reliability", "general_criticism", "reported_or_hedged_claim", "plain_direct", "scope_or_referents_unclear", "medium", "Unnamed plural critics",
        "Plural abandonment verb without named critics.",
    ),
    "ليس بأهل أن يروى عنه": (
        "criticism", "transmission_practice", "specific_transmission_criticism", "direct_statement", "plain_direct", "none", "medium", "",
        "Rejection of transmission eligibility ('not fit to be narrated from'), occurring in historical/tamyiz entries.",
    ),
    "متهم بالكذب": (
        "criticism", "honesty_veracity", "accusation_of_lying", "direct_statement", "plain_direct", "none", "high", "",
        "Direct accusation-of-lying phrase (متهم بالكذب).",
    ),
    "متهم بالوضع": (
        "criticism", "fabrication", "fabrication_label", "direct_statement", "plain_direct", "none", "high", "",
        "Direct accusation of fabrication (متهم بالوضع).",
    ),
    "رموه بالوضع": (
        "criticism", "fabrication", "fabrication_label", "reported_or_hedged_claim", "plain_direct", "scope_or_referents_unclear", "medium", "Unnamed plural critics",
        "Plural accusation of fabrication without named critics.",
    ),
    "رمي بالوضع": (
        "criticism", "fabrication", "fabrication_label", "reported_or_hedged_claim", "plain_direct", "scope_or_referents_unclear", "medium", "Unnamed source",
        "Passive accusation of fabrication (رمي بالوضع).",
    ),
    "رماه ابن معين بالكذب": (
        "criticism", "honesty_veracity", "accusation_of_lying", "attributed_individual_judgement", "plain_direct", "none", "high", "ابن معين",
        "Attributed accusation of lying by Ibn Ma'in.",
    ),
    "نسبه أبو حاتم إلى الكذب": (
        "criticism", "honesty_veracity", "accusation_of_lying", "attributed_individual_judgement", "plain_direct", "none", "high", "أبو حاتم",
        "Attributed charge attributing lying to Abu Hatim.",
    ),
    "وكذبه ابن معين": (
        "criticism", "honesty_veracity", "accusation_of_lying", "attributed_individual_judgement", "plain_direct", "none", "high", "ابن معين",
        "Attributed accusation of lying by Ibn Ma'in.",
    ),
    "كذبه أبو زرعة": (
        "criticism", "honesty_veracity", "accusation_of_lying", "attributed_individual_judgement", "plain_direct", "none", "high", "أبو زرعة",
        "Attributed accusation of lying by Abu Zur'a.",
    ),
    "كذبه الشعبي في رأيه": (
        "unresolved", "unresolved", "unresolved", "unresolved", "unresolved", "none", "low", "الشعبي",
        "Accusation scoped with في رأيه; requires interpretation of opinion vs hadith veracity.",
    ),
    "كذبوه": (
        "criticism", "honesty_veracity", "accusation_of_lying", "unresolved", "plain_direct", "scope_or_referents_unclear", "medium", "Unnamed plural critics",
        "Plural accusation of lying without named evaluators; plural verb does not establish unanimity.",
    ),
    "يسرق الحديث": (
        "criticism", "transmission_practice", "hadith_theft_or_appropriation", "specific_behavior_or_transmission_observation", "plain_direct", "none", "high", "",
        "Specific transmission criticism (hadith theft/appropriation); distinct from explicit lying/fabrication.",
    ),

    # --- Doctrinal / general vague criticism ---
    "طعن فيه برأي جهم ثم اعتذر وتاب": (
        "mixed", "doctrinal_position", "mixed_assessment", "reported_or_hedged_claim", "qualified_limited", "none", "medium", "",
        "Doctrinal criticism regarding Jahmi opinion paired with explicit apology and repentance.",
    ),
    "رمي بالتشيع": (
        "criticism", "doctrinal_position", "general_criticism", "reported_or_hedged_claim", "plain_direct", "none", "medium", "Unnamed source",
        "Passive doctrinal/affiliation report (رمي بالتشيع); keep distinct from general reliability unless advocacy is stated.",
    ),
    "رمي بالنصب": (
        "criticism", "doctrinal_position", "general_criticism", "reported_or_hedged_claim", "plain_direct", "none", "medium", "Unnamed source",
        "Passive doctrinal/affiliation report (رمي بالنصب).",
    ),
    "التشيع": (
        "criticism", "doctrinal_position", "general_criticism", "reported_or_hedged_claim", "plain_direct", "none", "medium", "",
        "Doctrinal affiliation cue (التشيع); inspect preceding verb (e.g., رمي بالتشيع / فيه تشيع).",
    ),
    "الإرجاء": (
        "criticism", "doctrinal_position", "general_criticism", "reported_or_hedged_claim", "plain_direct", "none", "medium", "",
        "Doctrinal affiliation cue (الإرجاء); inspect preceding verb (e.g., رمي بالإرجاء).",
    ),
    "القدر": (
        "criticism", "doctrinal_position", "general_criticism", "reported_or_hedged_claim", "plain_direct", "none", "medium", "",
        "Doctrinal affiliation cue (القدر); inspect preceding verb (e.g., رمي بالقدر / يرى القدر).",
    ),
    "النصب": (
        "criticism", "doctrinal_position", "general_criticism", "reported_or_hedged_claim", "plain_direct", "none", "medium", "",
        "Doctrinal affiliation cue (النصب); inspect preceding verb (e.g., رمي بالنصب).",
    ),
    "رافضي": (
        "criticism", "doctrinal_position", "general_criticism", "direct_statement", "plain_direct", "none", "medium", "",
        "Doctrinal/sectarian label (رافضي); keep separate from reliability unless linked to hadith rejection.",
    ),
    "اتهمه جماعة": (
        "unresolved", "unresolved", "general_criticism", "reported_or_hedged_claim", "plain_direct", "scope_or_referents_unclear", "low", "جماعة (unnamed group)",
        "Unspecified accusation ('a group accused him') without stating the object of accusation in the span.",
    ),
    "تكلم فيه بعضهم": (
        "criticism", "unresolved", "general_criticism", "reported_or_hedged_claim", "qualified_limited", "scope_or_referents_unclear", "low", "بعضهم (unnamed subset)",
        "Vague partial criticism ('some criticized him') with unspecified critics and grounds.",
    ),
    "تكلموا فيه": (
        "criticism", "unresolved", "general_criticism", "reported_or_hedged_claim", "plain_direct", "scope_or_referents_unclear", "low", "Unnamed plural critics",
        "Vague plural criticism ('they criticized him') with unspecified critics and grounds.",
    ),
}

PRECEDING_NEGATIONS = (
    ("وهم من ذكره في ", "Refutes prior claim attributing Companionship ('وهم من ذكره في الصحابة')."),
    ("أخطأ من عده في ", "Refutes prior claim attributing Companionship ('أخطأ من عده في الصحابة')."),
    ("وهم من عده في ", "Refutes prior claim attributing Companionship ('وهم من عده في الصحابة')."),
    ("وهم من زعم أن ", "Refutes prior claim attributing Companionship ('وهم من زعم أن له صحبة')."),
    ("وهم من جعله ", "Refutes prior claim attributing Companionship ('وهم من جعله صحابيا')."),
    ("وهم من قال ", "Refutes prior claim attributing Companionship ('وهم من قال له صحبة')."),
    ("غير ", "Contrastive negation ('غير ...')."),
    ("فلم ي", "Negated verb clause ('فلم يشهد ...')."),
    ("لم ي", "Negated verb clause."),
    ("لا ي", "Negated verb clause."),
    ("ليس ب", "Negated predicate."),
)

CRITIC_PATTERNS = [
    (re.compile(r"(قال|ذكره)\s+(ابن عبد البر|ابن حبان|ابن معين|ابن سعد|أبو حاتم|أبو زرعة|النسائي|البخاري|أحمد|العجلي|الدارقطني|الخليلي|الواقدي|مسلم|الذهبي|المزي)\s*:?\s*$"), "preceding"),
    (re.compile(r"^\s*(قاله|وثقه|ضعفه)\s+(يحيى ابن معين|مسلم وغيره|أحمد|ابن معين|النسائي|أبو حاتم|أبو زرعة|ابن حبان|العجلي|الدارقطني)"), "following"),
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\r\n")
        writer.writeheader()
        writer.writerows(rows)


def is_ar(text: str, pos: int) -> bool:
    return 0 <= pos < len(text) and bool(ARABIC_LETTER.fullmatch(text[pos]))


def expand_token_bounds(text: str, start: int, end: int) -> tuple[int, int]:
    while start > 0 and is_ar(text, start - 1):
        start -= 1
    while end < len(text) and is_ar(text, end):
        end += 1
    return start, end


def assert_no_em_en_dash(text: str, label: str) -> None:
    if "\u2014" in text or "\u2013" in text:
        raise SystemExit(f"Forbidden em-dash or en-dash in {label}")


def verify_batch_02_inputs() -> dict[str, Any]:
    manifest_path = B2_DIR / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    sidecar = (B2_DIR / "MANIFEST.sha256").read_text(encoding="ascii").split()[0]
    if sha256(manifest_path) != sidecar:
        raise SystemExit("Batch 02 MANIFEST.sha256 mismatch")
    for name, expected in manifest["outputs"].items():
        if sha256(B2_DIR / name) != expected:
            raise SystemExit(f"Batch 02 output hash mismatch for {name}")
    return manifest


def choose_primary_phrase(case: dict[str, str], case_links: list[dict[str, str]]) -> str:
    phrases = [p.strip() for p in case["matched_phrases_verbatim"].split(" | ") if p.strip()]
    # Prefer longest known template phrase in the cluster (or selected link if tied)
    selected_phrases = {
        l["phrase_candidate_exact"]
        for l in case_links
        if l["phrase_hit_selected_for_batch_02"] == "yes"
    }
    known = [p for p in phrases if p in PHRASE_TEMPLATES]
    if not known:
        raise SystemExit(f"No template found for phrases in {case['review_case_id']}: {phrases}")
    known.sort(key=lambda p: (len(p), p in selected_phrases, p), reverse=True)
    return known[0]


def analyze_case(case: dict[str, str], case_links: list[dict[str, str]]) -> dict[str, Any]:
    text = case["source_entry_text_verbatim"]
    span_start = int(case["review_span_start_char_zero_based"])
    span_end = int(case["review_span_end_char_exclusive"])
    span_text = case["review_span_text_verbatim"]
    primary_phrase = choose_primary_phrase(case, case_links)

    tok_start, tok_end = expand_token_bounds(text, span_start, span_end)
    full_tokens = text[tok_start:tok_end]
    pre = text[max(0, span_start - 45):span_start]
    post = text[span_end:min(len(text), span_end + 60)]

    # Start with template defaults
    family, domain, content, mode, force, consensus, confidence, attribution, rationale = PHRASE_TEMPLATES[primary_phrase]
    match_use = "complete_statement" if int(case["number_of_overlapping_phrase_hits"]) == 1 else "component_of_larger_statement"
    stmt_start: int | str = span_start
    stmt_end: int | str = span_end
    referent = "The entry subject."
    qualification = ""
    span_note = "Exact span matches the full candidate phrase." if match_use == "complete_statement" else f"Grouped overlap span ({case['matched_phrases_verbatim']})."

    # 1. False-positive substring detections
    if primary_phrase == "بدري" and ("العبدري" in full_tokens or "العبدرية" in full_tokens):
        return {
            "ai_match_use": "unrelated_substring",
            "ai_statement_role": "not_applicable",
            "ai_statement_start_char_zero_based": "",
            "ai_statement_end_char_exclusive": "",
            "ai_statement_text_verbatim": "",
            "ai_statement_family": "not_applicable",
            "ai_statement_domain": "not_applicable",
            "ai_claim_content": "not_applicable",
            "ai_claim_mode": "not_applicable",
            "ai_wording_force": "not_applicable",
            "ai_consensus_wording": "not_applicable",
            "ai_referent": "",
            "ai_attribution": "",
            "ai_qualification": "",
            "ai_interpretation_confidence": "high",
            "ai_span_boundary_note": f"False-positive substring inside tribal nisba '{full_tokens}'.",
            "ai_rationale": f"The match 'بدري' is an internal substring of the nisba '{full_tokens}', not a Badr-participant status statement.",
        }

    if primary_phrase == "ثبت" and ("يثبت" in full_tokens or "تثبت" in full_tokens):
        return {
            "ai_match_use": "unrelated_substring",
            "ai_statement_role": "not_applicable",
            "ai_statement_start_char_zero_based": "",
            "ai_statement_end_char_exclusive": "",
            "ai_statement_text_verbatim": "",
            "ai_statement_family": "not_applicable",
            "ai_statement_domain": "not_applicable",
            "ai_claim_content": "not_applicable",
            "ai_claim_mode": "not_applicable",
            "ai_wording_force": "not_applicable",
            "ai_consensus_wording": "not_applicable",
            "ai_referent": "",
            "ai_attribution": "",
            "ai_qualification": "",
            "ai_interpretation_confidence": "high",
            "ai_span_boundary_note": f"False-positive substring inside verb '{full_tokens}'.",
            "ai_rationale": f"The match 'ثبت' is part of the verb '{full_tokens}' ('is established'), not the reliability commendation 'ثبت'.",
        }

    # 2. Specific lexical/structural adjustments on token expansions
    if primary_phrase == "ثبت" and "أثبت" in full_tokens:
        family, domain, content, mode, force, consensus, confidence = (
            "mixed", "memory_precision", "biographical_fact", "specific_behavior_or_transmission_observation",
            "qualified_limited", "none", "medium",
        )
        match_use = "component_of_larger_statement"
        m_cmp = re.search(r"فصار كتابه أثبت من حفظه", text)
        if m_cmp:
            stmt_start, stmt_end = m_cmp.start(), m_cmp.end()
        else:
            stmt_start, stmt_end = tok_start, tok_end
        span_note = f"Expanded from substring 'ثبت' inside '{full_tokens}'."
        rationale = "Comparative memory/written-record observation ('his book became more reliable than his memory'), not standalone 'ثبت'."

    elif primary_phrase == "متقن" and "المتقنين" in full_tokens:
        match_use = "component_of_larger_statement"
        m_super = re.search(r"رأس المتقنين(?:\s+وكبير المتثبتين)?", text)
        if m_super:
            stmt_start, stmt_end = m_super.start(), m_super.end()
        else:
            stmt_start, stmt_end = tok_start, tok_end
        force = "superlative"
        content = "superlative_commendation"
        span_note = f"Expanded from substring inside '{full_tokens}'."
        rationale = "Part of the superlative praise expression 'رأس المتقنين' ('head of the meticulous scholars')."

    elif primary_phrase == "مجهول" and "المجهولين" in full_tokens:
        match_use = "component_of_larger_statement"
        m_sh = re.search(r"من شيوخ بقية المجهولين", text)
        if m_sh:
            stmt_start, stmt_end = m_sh.start(), m_sh.end()
        else:
            stmt_start, stmt_end = tok_start, tok_end
        domain = "transmission_practice"
        content = "specific_transmission_criticism"
        referent = "Baqiyyah's unknown teachers (collective), characterizing this narrator's transmission circle."
        span_note = "Expanded to transmission-circle phrase 'من شيوخ بقية المجهولين'."
        rationale = "Plural 'المجهولين' describes Baqiyyah's anonymous shaykhs in this transmission characterization."

    elif primary_phrase == "صحابية مشهور" and tok_end > span_end and text[span_end:tok_end] == "ة":
        stmt_end = tok_end
        match_use = "component_of_larger_statement"
        span_note = "Expanded 1 char right to restore final ta marbuta ('صحابية مشهورة')."
        rationale = "Direct female Companion status assertion; source index truncated final 'ة'."

    elif primary_phrase == "وثقه يعقوب ابن" and post.startswith(" سفيان"):
        stmt_end = span_end + len(" سفيان")
        match_use = "component_of_larger_statement"
        span_note = "Expanded right to complete critic name ('وثقه يعقوب ابن سفيان')."

    elif primary_phrase == "ضعفه الأزدي من الرابعة ق":
        m_sub = re.match(r"ضعفه الأزدي", span_text)
        if m_sub:
            stmt_start, stmt_end = span_start, span_start + len("ضعفه الأزدي")
            match_use = "component_of_larger_statement"
            span_note = "Trimmed trailing generation and book sigla ('من الرابعة ق') from over-long index span."

    elif primary_phrase == "ضعفه يحيى ابن معين ورمي بالإرجاء من التاسعة مات سنة خمس عشرة ت":
        stmt_start, stmt_end = span_start, span_start + len("ضعفه يحيى ابن معين")
        match_use = "component_of_larger_statement"
        qualification = "ورمي بالإرجاء (separate doctrinal clause in same entry)"
        span_note = "Trimmed doctrinal clause, generation, death date, and sigla; keep 'ورمي بالإرجاء' as separate claim."

    elif primary_phrase in {"الإرجاء", "القدر", "النصب", "التشيع"}:
        # Check preceding "رمي بـ" / "ورمي بـ" / "وبـ" / "يرى "
        m_doct = re.search(r"(?:ورمي ب|رمي ب|يرى |وب)$", text[max(0, span_start - 12):span_start])
        if m_doct:
            prefix_len = len(m_doct.group(0))
            if m_doct.group(0).startswith("و"):
                # Exclude leading conjunction و when cleaner, or keep if attached to رمي
                if m_doct.group(0) == "وب":
                    stmt_start = span_start - 1  # ب...
                else:
                    stmt_start = span_start - prefix_len + 1  # رمي ب...
            else:
                stmt_start = span_start - prefix_len
            match_use = "component_of_larger_statement"
            span_note = f"Expanded left to include governing verb/preposition ('{text[stmt_start:stmt_end]}')."
        elif tok_start < span_start:
            stmt_start = tok_start
            match_use = "component_of_larger_statement"
            span_note = f"Expanded left to include attached prefix ('{full_tokens}')."

    elif primary_phrase == "البدري" and full_tokens == "البدريين":
        stmt_start, stmt_end = tok_start, tok_end
        match_use = "component_of_larger_statement"
        span_note = "Expanded to plural token 'البدريين'; inspect preceding verb (e.g., مات من البدريين / ذكره في البدريين)."

    elif primary_phrase == "حافظ" and full_tokens == "الحافظ":
        stmt_start, stmt_end = tok_start, tok_end
        match_use = "component_of_larger_statement"
        span_note = "Expanded to definite noun 'الحافظ'."

    elif primary_phrase == "حافظ" and full_tokens == "حافظا":
        stmt_start, stmt_end = tok_start, tok_end
        match_use = "component_of_larger_statement"
        span_note = "Expanded to accusative 'حافظا' (following وكان)."

    # 3. Check preceding negation / refutation / conditional disjunction
    if pre.endswith("والا ف") and primary_phrase == "مجهول":
        match_use = "component_of_larger_statement"
        mode = "reported_or_hedged_claim"
        force = "qualified_limited"
        confidence = "low"
        qualification = "Conditional alternative following 'يقال له صحبة والا فمجهول'"
        rationale = "Conditional disjunction: unknownness applies only if the preceding Companionship report does not hold."

    for neg_pat, neg_note in PRECEDING_NEGATIONS:
        if pre.endswith(neg_pat) or (neg_pat.strip() in pre and primary_phrase in {"الصحابة", "له صحبة", "شهد بدرا", "صحابي"} and any(k in pre for k in ("وهم من", "أخطأ من", "فلم "))):
            match_use = "component_of_larger_statement"
            confidence = "low" if "الصحابة" in primary_phrase or "صحبة" in primary_phrase or primary_phrase == "صحابي" else "medium"
            if primary_phrase == "شهد بدرا" and "فلم " in pre:
                content = "biographical_fact"
                qualification = "Negated: فلم يشهد بدرا"
                m_neg = re.search(r"فلم يشهد بدرا|لم يشهد بدرا", text[max(0, span_start - 10):span_end])
                if m_neg:
                    stmt_start = max(0, span_start - 10) + m_neg.start()
                    stmt_end = max(0, span_start - 10) + m_neg.end()
                span_note = "Negated attendance at Badr ('did not witness Badr')."
                rationale = "Explicitly negates Badr participation; do not treat as positive Badr status."
            else:
                qualification = f"Negated/refuted in preceding context: {pre.strip()}"
                rationale = f"{neg_note} Do not treat the inner span as an affirmative assertion for the entry subject."
            break

    # 4. Check referent shift for relatives or third parties
    if primary_phrase in {"أم المؤمنين", "الصحابة"}:
        rel_match = re.search(r"(أخو|أخت|ابن أخي|ابن أخت|عمته|خالته|زوجة|أبوه|أبيه|بنت)\s+([^\s]+\s+)?$", pre)
        if rel_match or ("أمه " in pre and primary_phrase == "أم المؤمنين") or ("أبوه من كبار" in pre and primary_phrase == "الصحابة"):
            referent = f"Relative mentioned in the entry ({pre.strip()}), NOT the entry subject."
            match_use = "component_of_larger_statement"
            confidence = "high"
            rationale = f"In this entry, '{primary_phrase}' refers to a relative ({pre.strip()}), not the indexed narrator."
    if primary_phrase == "أحد العشرة" and "أخو طلحة" in pre:
        referent = "Talhah (brother of the subject's grandfather Uthman), NOT the entry subject."
        match_use = "component_of_larger_statement"
        confidence = "high"
        rationale = "Biographical pedigree note identifying Talhah as one of the Ten; the entry subject is graded separately afterward."
    if primary_phrase == "الصحابي" and post.lstrip().startswith("جد جده"):
        referent = "The subject's great-great-grandfather ('جد جده'), NOT the entry subject."
        match_use = "component_of_larger_statement"
        confidence = "high"
        rationale = "Explains that the Companion was an ancestor sharing the name, while the entry subject was erroneously called a Companion."
    if primary_phrase == "صحابي معروف" and pre.rstrip().endswith("وأنس"):
        referent = "Anas ibn Malik al-Ka'bi (mentioned in the entry), NOT the unnamed uncle who is the subject."
        match_use = "component_of_larger_statement"
        confidence = "high"
        rationale = "Companionship belongs to Anas, whereas the entry's subject is the unnamed uncle ('عن عمه لم يسم')."
    if primary_phrase == "لا تعرف" and "امرأة من أهله" in pre:
        referent = "An unnamed woman from Zuhayr's family ('امرأة من أهله'), NOT the head name Zuhayr b. Muawiyah."
        match_use = "component_of_larger_statement"
        confidence = "high"
        rationale = "Unknownness refers to the unnamed female transmitter in the chain."
    if primary_phrase == "لين الحديث" and "فأبو غرارة" in pre:
        referent = "Abu Ghirarah (if distinct from al-Jud'ani, as noted by 'وقيل إن أبا غرارة غير الجدعاني')."
        match_use = "component_of_larger_statement"
        confidence = "low"
        qualification = "Identity-conditional: وقيل إن أبا غرارة غير الجدعاني ... والجدعاني متروك"
        rationale = "Mild weakness applies to Abu Ghirarah under an unresolved identity distinction against al-Jud'ani ('متروك')."

    # 5. Check explicit critic attribution before/after span
    if not attribution:
        for pat, side in CRITIC_PATTERNS:
            target_ctx = pre if side == "preceding" else post
            m_attr = pat.search(target_ctx)
            if m_attr:
                critic = m_attr.group(2)
                attribution = critic
                if family in {"praise", "criticism", "status_or_biography"} and mode in {"direct_statement", "status_or_biographical_statement"}:
                    mode = "attributed_individual_judgement" if critic not in {"ابن عبد البر", "مسلم وغيره"} else "reported_or_hedged_claim"
                rationale = f"{rationale} Explicitly attributed to {critic} in nearby context."
                break

    # 6. Check trailing disputes / qualifications / exceptions in post-context
    if primary_phrase == "متروك الحديث" and post.lstrip().startswith("عن الزهري"):
        m_az = re.match(r"^\s*عن الزهري", post)
        if m_az and isinstance(stmt_end, int):
            stmt_end = span_end + m_az.end()
        match_use = "component_of_larger_statement"
        domain = "transmission_practice"
        force = "qualified_limited"
        confidence = "medium"
        qualification = "Scoped strictly to narrations from al-Zuhri; followed by 'لين في غيره'"
        span_note = "Expanded right to include transmission scope 'عن الزهري'."
        rationale = "Transmission-scoped abandonment ('متروك الحديث عن الزهري') contrasted with 'لين في غيره'; not narrator-wide متروك."

    trailing_patterns = [
        (r"^\s*(إلا أنه[^\n،؛]*?(?=من ال|مات |و?قال |$))", "Exception clause following span"),
        (r"^\s*(إلا في حديث[^\n]*?(?=قاله|من ال|مات |$))", "Hadith-specific exception following span"),
        (r"^\s*(من رواية[^\n]*?(?=من صغار|من ال|مات |$))", "Transmission-route restriction following span"),
        (r"^\s*(وقيل لا صحبة له|ونفاها بعضهم|ولا يثبت(?:\s*\[تثبت\])?|لم يصح الإسناد إليه|إلا أن الإسناد إليه بذلك واهي|ولم يصح شهوده بدرا)", "Dispute/negation immediately following status claim"),
        (r"^\s*(وفي إسناد حديثه اضطراب|لكن في حديثه اضطراب|في حديثه ضعف|وفي أحاديثه مناكير|له أغلاط[^\n]*?(?=وهو من|مات |$))", "Adverse transmission/error note following span"),
        (r"^\s*(وقال العجلي من كبار التابعين)", "Contrary classification following span"),
        (r"^\s*(الا فمجهول)", "Conditional disjunction"),
    ]
    for pat_str, label in trailing_patterns:
        m_tr = re.match(pat_str, post)
        if m_tr:
            tr_txt = m_tr.group(1).strip()
            qualification = f"{qualification}; {tr_txt}".strip("; ") if qualification else tr_txt
            if any(k in label for k in ("Dispute", "Conditional", "Contrary")):
                confidence = "low" if confidence == "high" else confidence
            rationale = f"{rationale} {label}: '{tr_txt}'."
            break

    if pre.endswith("[") and post.startswith("]"):
        qualification = f"{qualification}; bracketed editorial text [...]".strip("; ")
        span_note = f"{span_note} Enclosed in editorial square brackets in local text."

    # Special case: "ثقة" followed by "حجة" or other compound in post context, or "لا بأس به إلا في..."
    if primary_phrase == "لا بأس به" and post.lstrip().startswith("إلا"):
        family = "mixed"
        content = "qualified_commendation"
        force = "qualified_limited"

    if primary_phrase == "حافظ" and ("متروك" in pre or "لم يكن ب" in pre):
        confidence = "low"
        qualification = f"{qualification}; preceded by '{pre.strip()}'".strip("; ")
        rationale = f"{rationale} Preceding context ('{pre.strip()}') must be preserved separately."

    # Verify exact statement slice
    assert isinstance(stmt_start, int) and isinstance(stmt_end, int)
    stmt_text = text[stmt_start:stmt_end]
    if not stmt_text:
        raise SystemExit(f"Empty statement slice for {case['review_case_id']}")

    return {
        "ai_match_use": match_use,
        "ai_statement_role": family,
        "ai_statement_start_char_zero_based": stmt_start,
        "ai_statement_end_char_exclusive": stmt_end,
        "ai_statement_text_verbatim": stmt_text,
        "ai_statement_family": family,
        "ai_statement_domain": domain,
        "ai_claim_content": content,
        "ai_claim_mode": mode,
        "ai_wording_force": force,
        "ai_consensus_wording": consensus,
        "ai_referent": referent,
        "ai_attribution": attribution,
        "ai_qualification": qualification,
        "ai_interpretation_confidence": confidence,
        "ai_span_boundary_note": span_note,
        "ai_rationale": rationale,
    }


def validate_row(row: dict[str, Any]) -> None:
    assert row["ai_match_use"] in ALLOWED_MATCH_USE, f"Invalid ai_match_use: {row['ai_match_use']}"
    assert row["ai_statement_role"] in ALLOWED_FAMILY, f"Invalid ai_statement_role: {row['ai_statement_role']}"
    assert row["ai_statement_family"] in ALLOWED_FAMILY, f"Invalid ai_statement_family: {row['ai_statement_family']}"
    assert row["ai_statement_domain"] in ALLOWED_DOMAIN, f"Invalid ai_statement_domain: {row['ai_statement_domain']}"
    assert row["ai_claim_content"] in ALLOWED_CONTENT, f"Invalid ai_claim_content: {row['ai_claim_content']}"
    assert row["ai_claim_mode"] in ALLOWED_MODE, f"Invalid ai_claim_mode: {row['ai_claim_mode']}"
    assert row["ai_wording_force"] in ALLOWED_FORCE, f"Invalid ai_wording_force: {row['ai_wording_force']}"
    assert row["ai_consensus_wording"] in ALLOWED_CONSENSUS, f"Invalid ai_consensus_wording: {row['ai_consensus_wording']}"
    assert row["ai_interpretation_confidence"] in ALLOWED_CONFIDENCE, f"Invalid confidence: {row['ai_interpretation_confidence']}"
    if row["ai_statement_start_char_zero_based"] != "":
        s = int(row["ai_statement_start_char_zero_based"])
        e = int(row["ai_statement_end_char_exclusive"])
        assert row["source_entry_text_verbatim"][s:e] == row["ai_statement_text_verbatim"], (
            f"Slice mismatch in {row['review_case_id']}"
        )
    for k, v in row.items():
        assert_no_em_en_dash(str(v), f"{row['review_case_id']}.{k}")


def main() -> None:
    if OUT_DIR.exists() and any(OUT_DIR.iterdir()):
        raise SystemExit(f"Refusing to overwrite existing advisory package: {OUT_DIR}")

    verify_batch_02_inputs()

    cases = read_csv(B2_DIR / "BATCH_02_REVIEW_CASES_V0_1.csv")
    links = read_csv(B2_DIR / "PHRASE_HIT_TO_REVIEW_CASE_LINKS_V0_1.csv")
    links_by_case: dict[str, list[dict[str, str]]] = defaultdict(list)
    for link in links:
        links_by_case[link["review_case_id"]].append(link)

    advisory_rows: list[dict[str, Any]] = []
    for idx, case in enumerate(cases, start=1):
        case_links = links_by_case[case["review_case_id"]]
        analysis = analyze_case(case, case_links)
        row = {
            "advisory_id": f"ADV02-{idx:04d}",
            "review_case_id": case["review_case_id"],
            "entry_id": case["entry_id"],
            "printed_page_num": case["printed_page_num"],
            "entry_number_verbatim": case["entry_number_verbatim"],
            "review_span_start_char_zero_based": case["review_span_start_char_zero_based"],
            "review_span_end_char_exclusive": case["review_span_end_char_exclusive"],
            "review_span_text_verbatim": case["review_span_text_verbatim"],
            "source_entry_text_verbatim": case["source_entry_text_verbatim"],
            "number_of_overlapping_phrase_hits": case["number_of_overlapping_phrase_hits"],
            "matched_candidate_ids": case["matched_candidate_ids"],
            "matched_phrases_verbatim": case["matched_phrases_verbatim"],
            "matched_occurrence_ids": case["matched_occurrence_ids"],
            "batch_02_selection_basis": case["batch_02_selection_basis"],
            "prior_batch_01_accepted_occurrence_ids": case["prior_batch_01_accepted_occurrence_ids"],
            "ai_advisory_status": "proposal_only_not_human_reviewed",
            **analysis,
            "human_decision": "",
            "human_match_use": "",
            "human_statement_role": "",
            "human_statement_start_char_zero_based": "",
            "human_statement_end_char_exclusive": "",
            "human_referent": "",
            "human_attribution": "",
            "human_qualification": "",
            "human_confidence": "",
            "human_notes": "",
            "canonical_rank": "",
            "numeric_score": "",
        }
        validate_row(row)
        advisory_rows.append(row)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUT_DIR / "AI_ADVISORY_REVIEW_BATCH_02_V0_1.csv"
    write_csv(csv_path, advisory_rows, list(advisory_rows[0]))

    match_use_counts = Counter(r["ai_match_use"] for r in advisory_rows)
    family_counts = Counter(r["ai_statement_family"] for r in advisory_rows)
    conf_counts = Counter(r["ai_interpretation_confidence"] for r in advisory_rows)

    summary_lines = [
        "# AI Advisory Occurrence Review Summary: Batch 02 (889 Cases)",
        "",
        "**Status:** provisional AI advisory proposals using Draft Codebook v0.1; zero human decisions, canonical ranks, or numeric scores assigned.",
        "",
        "## Counts",
        "",
        f"- Total Batch 02 cases reviewed: **{len(advisory_rows):,}**",
        f"- Unique source entries represented: **{len({r['entry_id'] for r in advisory_rows}):,}**",
        f"- Cases with prior Batch 01 accepted occurrences overlapping the span: **{sum(bool(r['prior_batch_01_accepted_occurrence_ids']) for r in advisory_rows)}**",
        "",
        "### Proposed `ai_match_use`",
        "",
        *[f"- `{k}`: {v}" for k, v in sorted(match_use_counts.items())],
        "",
        "### Proposed `ai_statement_family`",
        "",
        *[f"- `{k}`: {v}" for k, v in sorted(family_counts.items())],
        "",
        "### Proposed `ai_interpretation_confidence`",
        "",
        *[f"- `{k}`: {v}" for k, v in sorted(conf_counts.items())],
        "",
        "## Context-Sensitive Patterns Flagged in Batch 02",
        "",
        "- **Unrelated substrings (`unrelated_substring`):** `بدري` inside the tribal nisba `العبدري`/`العبدرية`, and `ثبت` inside the verb `يثبت` (`لا يثبت`).",
        "- **Negated or refuted status claims:** `فلم يشهد بدرا`, `وهم من ذكره في الصحابة`, `أخطأ من عده في الصحابة`, `وهم من زعم أن له صحبة`, `وهم من قال له صحبة`, `غير الصحابي`.",
        "- **Referent shifts:** `أم المؤمنين` and `الصحابة` referring to named relatives (`أخو`, `أخت`, `ابن أخي`, `ابن أخت`, `عمته`, `أبوه`) rather than the entry subject.",
        "- **Span repairs from v0.1:** `صحابية مشهور` expanded to `صحابية مشهورة`; `وثقه يعقوب ابن` expanded to `وثقه يعقوب ابن سفيان`; `ضعفه الأزدي من الرابعة ق` and `ضعفه يحيى ابن معين ...` trimmed of generation/death/sigla; doctrinal nouns (`بالإرجاء`, `بالقدر`, `بالتشيع`, `بالنصب`) expanded left to their governing verb when present.",
        "",
    ]
    summary_text = "\n".join(summary_lines)
    assert_no_em_en_dash(summary_text, "AI_ADVISORY_SUMMARY_V0_1.md")
    summary_path = OUT_DIR / "AI_ADVISORY_SUMMARY_V0_1.md"
    summary_path.write_text(summary_text, encoding="utf-8", newline="\n")

    readme_text = "\n".join([
        "# AI Advisory Occurrence Review: Batch 02",
        "",
        "**Status:** 889 source-linked AI advisory proposals matching `BATCH_02_REVIEW_CASES_V0_1.csv`. Zero human decisions, canonical ranks, or numeric scores are assigned. The original Batch 02 review CSV remains unmodified.",
        "",
        "## Files",
        "",
        "- [AI_ADVISORY_REVIEW_BATCH_02_V0_1.csv](AI_ADVISORY_REVIEW_BATCH_02_V0_1.csv): all 889 Batch 02 review cases with Draft Codebook v0.1 advisory proposals, exact statement spans, referent/attribution/qualification notes, and blank human decision/override columns.",
        "- [AI_ADVISORY_SUMMARY_V0_1.md](AI_ADVISORY_SUMMARY_V0_1.md): counts by match use, statement family, and confidence, plus key context-sensitive traps.",
        "- `MANIFEST.json` and `MANIFEST.sha256`: input and output checksums.",
        "",
        "## Next use",
        "",
        "Review `AI_ADVISORY_REVIEW_BATCH_02_V0_1.csv` row by row (or record decisions into a separate dated decision package, following the Batch 01 workflow). Enter `accept`, `change`, or `unsure` in `human_decision`, and use the `human_*` override columns whenever `change` is needed. Acceptance applies only to the reviewed `review_case_id` row, never to unselected corpus occurrences.",
        "",
    ])
    assert_no_em_en_dash(readme_text, "README.md")
    readme_path = OUT_DIR / "README.md"
    readme_path.write_text(readme_text, encoding="utf-8", newline="\n")

    inputs = [
        B2_DIR / "BATCH_02_REVIEW_CASES_V0_1.csv",
        B2_DIR / "PHRASE_HIT_TO_REVIEW_CASE_LINKS_V0_1.csv",
        B2_DIR / "MANIFEST.json",
        CODEBOOK_PATH,
        Path(__file__).resolve(),
    ]
    outputs = [csv_path, summary_path, readme_path]
    manifest = {
        "package_id": OUT_DIR.name,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "AI advisory only for Batch 02; no human decisions, canonical ranks, or numeric scores assigned",
        "counts": {
            "batch_02_cases": len(advisory_rows),
            "unique_source_entries": len({r["entry_id"] for r in advisory_rows}),
            "match_use_counts": dict(match_use_counts),
            "statement_family_counts": dict(family_counts),
            "confidence_counts": dict(conf_counts),
            "human_decisions_filled": 0,
            "canonical_ranks_assigned": 0,
            "numeric_scores_assigned": 0,
        },
        "inputs": {p.relative_to(ROOT).as_posix(): sha256(p) for p in inputs},
        "outputs": {p.name: sha256(p) for p in outputs},
        "manifest_hash_policy": "MANIFEST.sha256 records this manifest hash separately; it is not recursively embedded.",
    }
    manifest_str = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    assert_no_em_en_dash(manifest_str, "MANIFEST.json")
    manifest_path = OUT_DIR / "MANIFEST.json"
    manifest_path.write_text(manifest_str, encoding="utf-8", newline="\n")
    (OUT_DIR / "MANIFEST.sha256").write_text(f"{sha256(manifest_path)}  MANIFEST.json\n", encoding="ascii", newline="\n")

    print(json.dumps({"output": str(OUT_DIR), **manifest["counts"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
