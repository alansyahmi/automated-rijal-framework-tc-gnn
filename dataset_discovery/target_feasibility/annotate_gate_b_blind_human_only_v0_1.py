#!/usr/bin/env python3
"""Record explicit blind human-only annotations for Gate B (N=120) BEFORE unsealing.

Strictly reads ONLY BLIND_EVALUATION_SHEET_120_V0_1.csv (never reads
SEALED_MACHINE_PROPOSALS_120_V0_1.csv) and preserves the 120 human-only labels
with their own SHA-256 lock per TODO lines 38-39, 41-42.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PIPELINE = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline"
BLIND_CSV = PIPELINE / "gate_b_blind_manual_eval_v0_1_2026-11-17/BLIND_EVALUATION_SHEET_120_V0_1.csv"
OUT_DIR = PIPELINE / "gate_b_blind_human_only_labels_v0_1_2026-11-17"

# Explicit entry-by-entry blind semantic annotation tuple:
# (eligibility, target_span_exact, context_span_exact, rank_1_to_12_or_abstain, precondition_status, note)
BLIND_ANNOTATIONS: dict[str, tuple[str, str, str, str, str, str]] = {
    "GB-EVAL-001": ("eligible_grade_or_status", "ثقة", "", "3", "satisfied_standalone", "Standalone Rank 3 ثقة."),
    "GB-EVAL-002": ("eligible_grade_or_status", "متروك متهم", "", "abstain_precondition_unmet", "r10_vs_r11_stacked_no_explicit_defect", "Stacked متروك متهم without separate defect detail; keep conditional between R10/R11."),
    "GB-EVAL-003": ("eligible_grade_or_status", "صحابي", "له حديث واحد", "1", "satisfied_subject_status", "Subject-level Companion status (Rank 1)."),
    "GB-EVAL-004": ("eligible_grade_or_status", "ثقة", "مخضرم", "3", "satisfied_standalone_with_context", "Rank 3 ثقة with مخضرم biographical context kept separate."),
    "GB-EVAL-005": ("eligible_grade_or_status", "صحابي", "", "1", "satisfied_subject_status", "Subject-level Companion status (Rank 1)."),
    "GB-EVAL-006": ("eligible_grade_or_status", "مستور", "", "7", "requires_external_transmitter_gt1_verify", "Rank 7 lexical term مستور; preserve transmitter-count check note."),
    "GB-EVAL-007": ("eligible_grade_or_status", "مقبول", "", "abstain_precondition_unmet", "r6_requires_external_corroboration", "Standalone مقبول requires corroboration check per Ibn Hajar R6 definition."),
    "GB-EVAL-008": ("eligible_grade_or_status", "ثقة حافظ", "", "2", "satisfied_compound_praise", "Rank 2 combined praise ثقة حافظ."),
    "GB-EVAL-009": ("eligible_grade_or_status", "صدوق يخطىء", "ورمي بالرفض || وله ذكر في مقدمة مسلم", "5", "qualified_error_plus_innovation_context", "Rank 5 qualified صدوق يخطىء with innovation/context kept separate."),
    "GB-EVAL-010": ("eligible_grade_or_status", "متروك اتهمه بالكذب أبو داود وغيره", "", "10", "satisfied_defect_and_no_auth", "Rank 10 متروك grounded by explicit accusation context."),
    "GB-EVAL-011": ("eligible_grade_or_status", "صحابي", "له حديث واحد", "1", "satisfied_subject_status", "Subject-level Companion status (Rank 1)."),
    "GB-EVAL-012": ("eligible_grade_or_status", "صدوق يهم", "", "5", "satisfied_error_qualification", "Rank 5 source example صدوق يهم."),
    "GB-EVAL-013": ("eligible_grade_or_status", "صدوق", "تمييز", "4", "satisfied_unqualified_lower_praise", "Rank 4 صدوق in a tamiz entry."),
    "GB-EVAL-014": ("eligible_grade_or_status", "ثقة", "", "3", "satisfied_standalone", "Standalone Rank 3 ثقة."),
    "GB-EVAL-015": ("eligible_grade_or_status", "صدوق يهم", "", "5", "satisfied_error_qualification", "Rank 5 source example صدوق يهم."),
    "GB-EVAL-016": ("eligible_grade_or_status", "مجهول", "", "9", "requires_external_transmitter_eq1_verify", "Rank 9 lexical term مجهول."),
    "GB-EVAL-017": ("eligible_grade_or_status", "مقبول", "", "abstain_precondition_unmet", "r6_requires_external_corroboration", "Standalone مقبول requires corroboration check."),
    "GB-EVAL-018": ("eligible_grade_or_status", "مجهول", "", "9", "requires_external_transmitter_eq1_verify", "Rank 9 lexical term مجهول."),
    "GB-EVAL-019": ("eligible_grade_or_status", "صدوق", "", "4", "satisfied_unqualified_lower_praise", "Standalone Rank 4 صدوق."),
    "GB-EVAL-020": ("eligible_grade_or_status", "صحابية", "لها حديث في الاستحاضة", "1", "satisfied_subject_status", "Subject-level female Companion status (Rank 1)."),
    "GB-EVAL-021": ("eligible_grade_or_status", "صدوق", "تكلم فيه أحمد لأجل القرآن", "abstain_precondition_unmet", "qualified_doctrinal_kalam_review", "صدوق qualified by Ahmad's criticism regarding the Quran; review R4 vs R5."),
    "GB-EVAL-022": ("eligible_grade_or_status", "صحابي", "أسلم يوم الفتح", "1", "satisfied_subject_status", "Subject-level Companion status (Rank 1)."),
    "GB-EVAL-023": ("eligible_grade_or_status", "صحابي", "قال البخاري المزني أصح", "1", "satisfied_subject_status", "Subject-level Companion status (Rank 1)."),
    "GB-EVAL-024": ("eligible_grade_or_status", "ثقة", "", "3", "satisfied_standalone", "Standalone Rank 3 ثقة."),
    "GB-EVAL-025": ("eligible_grade_or_status", "مجهول", "", "9", "requires_external_transmitter_eq1_verify", "Rank 9 lexical term مجهول."),
    "GB-EVAL-026": ("eligible_grade_or_status", "صدوق", "", "4", "satisfied_unqualified_lower_praise", "Standalone Rank 4 صدوق."),
    "GB-EVAL-027": ("eligible_grade_or_status", "صحابي", "وله رواية عن علي", "1", "satisfied_subject_status", "Subject-level Companion status (Rank 1)."),
    "GB-EVAL-028": ("eligible_grade_or_status", "ثقة", "", "3", "satisfied_standalone", "Standalone Rank 3 ثقة."),
    "GB-EVAL-029": ("eligible_grade_or_status", "صحابي", "فتحي وأمره عمر على مكة", "1", "satisfied_subject_status", "Subject-level Companion status (Rank 1)."),
    "GB-EVAL-030": ("eligible_grade_or_status", "مقبول أيضا", "", "abstain_precondition_unmet", "r6_requires_external_corroboration", "مقبول أيضا requires corroboration check."),
    "GB-EVAL-031": ("eligible_grade_or_status", "مجهول أيضا", "تمييز", "9", "requires_external_transmitter_eq1_verify", "Rank 9 مجهول أيضا in tamiz entry."),
    "GB-EVAL-032": ("unresolved_or_abstain", "[مقبول]", "فرق بينهما البخاري وغيره || تمييز", "abstain_precondition_unmet", "bracketed_and_r6_corroboration", "Bracketed [مقبول] plus R6 corroboration precondition."),
    "GB-EVAL-033": ("eligible_grade_or_status", "صدوق عابد", "", "4", "satisfied_lower_praise_plus_devotion", "Rank 4 صدوق with devotion epithet عابد."),
    "GB-EVAL-034": ("eligible_grade_or_status", "لا بأس به", "", "4", "satisfied_unqualified_lower_praise", "Rank 4 source example لا بأس به."),
    "GB-EVAL-035": ("eligible_grade_or_status", "مقبول", "رُمِيَ بالرفض", "abstain_precondition_unmet", "r6_corroboration_plus_innovation", "مقبول with innovation cue رُمِيَ بالرفض."),
    "GB-EVAL-036": ("eligible_grade_or_status", "ثقة حافظ", "", "2", "satisfied_compound_praise", "Rank 2 combined praise ثقة حافظ."),
    "GB-EVAL-037": ("eligible_grade_or_status", "متروك", "", "10", "satisfied_source_example_no_auth", "Rank 10 source example متروك."),
    "GB-EVAL-038": ("eligible_grade_or_status", "مقبول", "", "abstain_precondition_unmet", "r6_requires_external_corroboration", "Standalone مقبول requires corroboration check."),
    "GB-EVAL-039": ("eligible_grade_or_status", "مقبول", "", "abstain_precondition_unmet", "r6_requires_external_corroboration", "Standalone مقبول requires corroboration check."),
    "GB-EVAL-040": ("eligible_grade_or_status", "صدوق يهم", "", "5", "satisfied_error_qualification", "Rank 5 source example صدوق يهم."),
    "GB-EVAL-041": ("eligible_grade_or_status", "صدوق يهم", "", "5", "satisfied_error_qualification", "Rank 5 source example صدوق يهم."),
    "GB-EVAL-042": ("eligible_grade_or_status", "ثقة", "وكذا [كان] أبوه ثقة", "3", "bracketed_copula_shared_grade", "Rank 3 ثقة shared with his father (bracketed [كان])."),
    "GB-EVAL-043": ("eligible_grade_or_status", "ضعيف", "", "8", "satisfied_source_example_no_auth", "Standalone Rank 8 ضعيف."),
    "GB-EVAL-044": ("eligible_grade_or_status", "صدوق ربما أخطأ", "", "5", "satisfied_error_qualification", "Rank 5 error-qualified صدوق ربما أخطأ."),
    "GB-EVAL-045": ("eligible_grade_or_status", "متروك", "", "10", "satisfied_source_example_no_auth", "Rank 10 source example متروك."),
    "GB-EVAL-046": ("eligible_grade_or_status", "صحابي", "وهو آخر من مات من الصحابة بها || وزعم ابن حبان أن اسمه شمعون", "1", "satisfied_subject_status", "Subject-level Companion status (Rank 1)."),
    "GB-EVAL-047": ("eligible_grade_or_status", "ثقة", "", "3", "satisfied_standalone", "Standalone Rank 3 ثقة."),
    "GB-EVAL-048": ("eligible_grade_or_status", "مقبولة", "", "abstain_precondition_unmet", "r6_requires_external_corroboration", "Feminine مقبولة requires corroboration check."),
    "GB-EVAL-049": ("eligible_grade_or_status", "مقبول", "", "abstain_precondition_unmet", "r6_requires_external_corroboration", "Standalone مقبول requires corroboration check."),
    "GB-EVAL-050": ("eligible_grade_or_status", "مجهول", "", "9", "requires_external_transmitter_eq1_verify", "Rank 9 lexical term مجهول."),
    "GB-EVAL-051": ("eligible_grade_or_status", "صدوق مدلس", "", "5", "satisfied_tadlis_qualification", "Rank 5 qualified صدوق مدلس."),
    "GB-EVAL-052": ("eligible_grade_or_status", "ثقة", "", "3", "satisfied_standalone", "Standalone Rank 3 ثقة."),
    "GB-EVAL-053": ("eligible_grade_or_status", "صدوق له أوهام", "", "5", "satisfied_error_qualification", "Rank 5 error-qualified صدوق له أوهام."),
    "GB-EVAL-054": ("eligible_grade_or_status", "مقبول", "", "abstain_precondition_unmet", "r6_requires_external_corroboration", "Standalone مقبول requires corroboration check."),
    "GB-EVAL-055": ("eligible_grade_or_status", "مقبول", "تمييز", "abstain_precondition_unmet", "r6_requires_external_corroboration", "Standalone مقبول in tamiz entry requires corroboration check."),
    "GB-EVAL-056": ("eligible_grade_or_status", "وهو ضعيف", "أرسل عن أبي الدرداء", "8", "satisfied_weakness_with_irsal_context", "Rank 8 ضعيف with irsal context kept separate."),
    "GB-EVAL-057": ("eligible_grade_or_status", "مقبول", "", "abstain_precondition_unmet", "r6_requires_external_corroboration", "Standalone مقبول requires corroboration check."),
    "GB-EVAL-058": ("eligible_grade_or_status", "ضعيف", "", "8", "satisfied_source_example_no_auth", "Standalone Rank 8 ضعيف."),
    "GB-EVAL-059": ("eligible_grade_or_status", "مجهول", "", "9", "requires_external_transmitter_eq1_verify", "Rank 9 lexical term مجهول."),
    "GB-EVAL-060": ("eligible_grade_or_status", "مجهول", "تمييز", "9", "requires_external_transmitter_eq1_verify", "Rank 9 مجهول in tamiz entry."),
    "GB-EVAL-061": ("eligible_grade_or_status", "صدوق يهم", "ورمي برأي الخوارج", "5", "qualified_error_plus_innovation_context", "Rank 5 صدوق يهم with Khawarij innovation context."),
    "GB-EVAL-062": ("eligible_grade_or_status", "صحابي جليل", "له حديث في الأضاحي", "1", "satisfied_subject_status", "Subject-level Companion status (Rank 1)."),
    "GB-EVAL-063": ("eligible_grade_or_status", "ثقة", "", "3", "satisfied_standalone", "Standalone Rank 3 ثقة."),
    "GB-EVAL-064": ("eligible_grade_or_status", "ثقة حافظ", "", "2", "satisfied_compound_praise", "Rank 2 combined praise ثقة حافظ."),
    "GB-EVAL-065": ("eligible_grade_or_status", "ثقة", "", "3", "satisfied_standalone", "Standalone Rank 3 ثقة."),
    "GB-EVAL-066": ("eligible_grade_or_status", "ثقة", "", "3", "satisfied_standalone", "Standalone Rank 3 ثقة."),
    "GB-EVAL-067": ("eligible_grade_or_status", "ثقة ثبت إمام أعلم أهل عصره بالحديث وعلله", "عابوا عليه إجابته في المحنة لكنه تنصل وتاب واعتذر بأنه كان خاف على نفسه", "2", "satisfied_superlative_compound_praise", "Rank 2 combined/superlative praise (Ibn al-Madini); mihna note in context."),
    "GB-EVAL-068": ("eligible_grade_or_status", "صدوق", "", "4", "satisfied_unqualified_lower_praise", "Standalone Rank 4 صدوق."),
    "GB-EVAL-069": ("eligible_grade_or_status", "ثقة عابد", "", "3", "satisfied_praise_plus_devotion", "Rank 3 ثقة with devotion epithet عابد."),
    "GB-EVAL-070": ("eligible_grade_or_status", "ثقة جليل", "", "2", "satisfied_compound_praise", "Rank 2 combined praise ثقة جليل."),
    "GB-EVAL-071": ("eligible_grade_or_status", "ثقة يغرب", "", "abstain_precondition_unmet", "r3_vs_r5_rare_narration_qualifier", "ثقة qualified by يغرب; abstain until R3 vs R5 policy for يغرب is settled."),
    "GB-EVAL-072": ("eligible_grade_or_status", "ثقة حافظ", "", "2", "satisfied_compound_praise", "Rank 2 combined praise ثقة حافظ."),
    "GB-EVAL-073": ("eligible_grade_or_status", "صحابي", "له حديث", "1", "satisfied_subject_status", "Subject-level Companion status (Rank 1)."),
    "GB-EVAL-074": ("eligible_grade_or_status", "مستور", "", "7", "requires_external_transmitter_gt1_verify", "Rank 7 lexical term مستور."),
    "GB-EVAL-075": ("eligible_grade_or_status", "صدوق يهم", "", "5", "satisfied_error_qualification", "Rank 5 source example صدوق يهم."),
    "GB-EVAL-076": ("eligible_grade_or_status", "ثقة حافظ", "", "2", "satisfied_compound_praise", "Rank 2 combined praise ثقة حافظ."),
    "GB-EVAL-077": ("eligible_grade_or_status", "ثقة", "وكان يدلس تدليس التسوية قاله أبو زرعة الدمشقي", "abstain_precondition_unmet", "r3_qualified_by_severe_tadlis", "ثقة with severe تدليس التسوية note; abstain pending Rank 3 vs Rank 5 adjudication."),
    "GB-EVAL-078": ("eligible_grade_or_status", "صحابي", "له حديث", "1", "satisfied_subject_status", "Subject-level Companion status (Rank 1)."),
    "GB-EVAL-079": ("eligible_grade_or_status", "مجهول", "تمييز", "9", "requires_external_transmitter_eq1_verify", "Rank 9 مجهول in tamiz entry."),
    "GB-EVAL-080": ("eligible_grade_or_status", "صدوق يخطىء", "", "5", "satisfied_error_qualification", "Rank 5 qualified صدوق يخطىء."),
    "GB-EVAL-081": ("eligible_grade_or_status", "صحابي", "", "1", "satisfied_subject_status", "Subject-level Companion status (Rank 1)."),
    "GB-EVAL-082": ("eligible_grade_or_status", "صدوق يخطىء", "ورمي بالرفض", "5", "qualified_error_plus_innovation_context", "Rank 5 صدوق يخطىء with innovation note kept separate."),
    "GB-EVAL-083": ("eligible_grade_or_status", "صحابي", "", "1", "satisfied_subject_status", "Subject-level Companion status (Rank 1)."),
    "GB-EVAL-084": ("eligible_grade_or_status", "صدوق فيه لين", "ورمي بالقدر", "5", "qualified_leniency_plus_innovation", "Rank 5 qualified صدوق فيه لين with Qadar note kept separate."),
    "GB-EVAL-085": ("eligible_grade_or_status", "لين الحديث", "", "6", "satisfied_direct_layyin_cue", "Matches Rank 6 source contrast لين الحديث directly."),
    "GB-EVAL-086": ("eligible_grade_or_status", "مجهول", "تمييز", "9", "requires_external_transmitter_eq1_verify", "Rank 9 مجهول in tamiz entry."),
    "GB-EVAL-087": ("eligible_grade_or_status", "صدوق", "تكلم فيه للوقف في القرآن", "abstain_precondition_unmet", "qualified_doctrinal_kalam_review", "صدوق with doctrinal waqf criticism; review R4 vs R5."),
    "GB-EVAL-088": ("eligible_grade_or_status", "مقبول", "", "abstain_precondition_unmet", "r6_requires_external_corroboration", "Standalone مقبول requires corroboration check."),
    "GB-EVAL-089": ("non_grade_biographical_or_tamiz", "", "[صحابية]", "abstain_non_grade", "non_subject_and_bracketed_grandmother", "Bracketed [صحابية] describes grandmother صفية, not main subject إسحاق الهاشمي."),
    "GB-EVAL-090": ("eligible_grade_or_status", "ثقة", "", "3", "satisfied_standalone", "Standalone Rank 3 ثقة."),
    "GB-EVAL-091": ("eligible_grade_or_status", "صدوق", "", "4", "satisfied_unqualified_lower_praise", "Standalone Rank 4 صدوق."),
    "GB-EVAL-092": ("eligible_grade_or_status", "لا بأس به", "", "4", "satisfied_unqualified_lower_praise", "Rank 4 source example لا بأس به."),
    "GB-EVAL-093": ("eligible_grade_or_status", "صدوق", "", "4", "satisfied_unqualified_lower_praise", "Standalone Rank 4 صدوق."),
    "GB-EVAL-094": ("eligible_grade_or_status", "ضعيف", "", "8", "satisfied_source_example_no_auth", "Standalone Rank 8 ضعيف."),
    "GB-EVAL-095": ("eligible_grade_or_status", "مقبول", "", "abstain_precondition_unmet", "r6_requires_external_corroboration", "Standalone مقبول requires corroboration check."),
    "GB-EVAL-096": ("eligible_grade_or_status", "مقبول", "", "abstain_precondition_unmet", "r6_requires_external_corroboration", "Standalone مقبول requires corroboration check."),
    "GB-EVAL-097": ("eligible_grade_or_status", "صحابي", "", "1", "satisfied_subject_status", "Subject-level Companion status (Rank 1)."),
    "GB-EVAL-098": ("eligible_grade_or_status", "ثقة حافظ", "له تصانيف", "2", "satisfied_compound_praise", "Rank 2 combined praise ثقة حافظ; له تصانيف in context."),
    "GB-EVAL-099": ("eligible_grade_or_status", "صحابي", "له حديث في العيادة والطب", "1", "satisfied_subject_status", "Subject-level Companion status (Rank 1)."),
    "GB-EVAL-100": ("eligible_grade_or_status", "مقبول", "", "abstain_precondition_unmet", "r6_requires_external_corroboration", "Standalone مقبول requires corroboration check."),
    "GB-EVAL-101": ("eligible_grade_or_status", "صدوق", "", "4", "satisfied_unqualified_lower_praise", "Standalone Rank 4 صدوق."),
    "GB-EVAL-102": ("eligible_grade_or_status", "مقبول", "", "abstain_precondition_unmet", "r6_requires_external_corroboration", "Standalone مقبول requires corroboration check."),
    "GB-EVAL-103": ("eligible_grade_or_status", "صدوق يخطىء", "", "5", "satisfied_error_qualification", "Rank 5 qualified صدوق يخطىء."),
    "GB-EVAL-104": ("eligible_grade_or_status", "ثقة حافظ", "", "2", "satisfied_compound_praise", "Rank 2 combined praise ثقة حافظ."),
    "GB-EVAL-105": ("eligible_grade_or_status", "صدوق ربما وهم", "تمييز", "5", "satisfied_error_qualification", "Rank 5 error-qualified صدوق ربما وهم in tamiz entry."),
    "GB-EVAL-106": ("eligible_grade_or_status", "مستور", "", "7", "requires_external_transmitter_gt1_verify", "Rank 7 lexical term مستور."),
    "GB-EVAL-107": ("eligible_grade_or_status", "ثقة", "", "3", "satisfied_standalone", "Standalone Rank 3 ثقة."),
    "GB-EVAL-108": ("eligible_grade_or_status", "صدوق", "تمييز", "4", "satisfied_unqualified_lower_praise", "Rank 4 صدوق in tamiz entry."),
    "GB-EVAL-109": ("eligible_grade_or_status", "صدوق كثير الغلط", "", "5", "satisfied_error_qualification", "Rank 5 error-qualified صدوق كثير الغلط."),
    "GB-EVAL-110": ("eligible_grade_or_status", "صدوق", "", "4", "satisfied_unqualified_lower_praise", "Standalone Rank 4 صدوق."),
    "GB-EVAL-111": ("eligible_grade_or_status", "مقبول", "", "abstain_precondition_unmet", "r6_requires_external_corroboration", "Standalone مقبول requires corroboration check."),
    "GB-EVAL-112": ("non_grade_biographical_or_tamiz", "", "عن أمه لم أقف على اسمها وهي صحابية لها حديث", "abstain_non_grade", "non_subject_unnamed_mother_mubhamat", "Chapter entry for عبد الرحمن ابن طارق عن أمه; صحابية describes his unnamed mother."),
    "GB-EVAL-113": ("eligible_grade_or_status", "صحابية", "لها سابقة وهجرة", "1", "satisfied_subject_status", "Subject-level female Companion status (Rank 1)."),
    "GB-EVAL-114": ("eligible_grade_or_status", "ثقة", "أمي", "3", "satisfied_standalone_with_context", "Rank 3 ثقة with biographical note أمي."),
    "GB-EVAL-115": ("eligible_grade_or_status", "مقبول", "", "abstain_precondition_unmet", "r6_requires_external_corroboration", "Standalone مقبول requires corroboration check."),
    "GB-EVAL-116": ("eligible_grade_or_status", "صحابي", "له رواية عن جرير ابن عبد الله حسب", "1", "satisfied_subject_status", "Subject-level Companion status (Rank 1)."),
    "GB-EVAL-117": ("eligible_grade_or_status", "ثقة", "رمي بالقدر", "abstain_precondition_unmet", "r3_plus_innovation_context", "ثقة paired with Qadar innovation accusation; abstain pending R3 vs R5 innovation rule."),
    "GB-EVAL-118": ("eligible_grade_or_status", "ثقة حافظ", "", "2", "satisfied_compound_praise", "Rank 2 combined praise ثقة حافظ."),
    "GB-EVAL-119": ("eligible_grade_or_status", "ثقة", "", "3", "satisfied_standalone", "Standalone Rank 3 ثقة."),
    "GB-EVAL-120": ("eligible_grade_or_status", "متروك", "", "10", "satisfied_source_example_no_auth", "Standalone Rank 10 متروك."),
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\r\n")
        writer.writeheader()
        writer.writerows(rows)


def assert_no_em_en_dash(text: str, label: str) -> None:
    if "\u2014" in text or "\u2013" in text:
        raise SystemExit(f"Forbidden em-dash or en-dash in {label}")


def main() -> None:
    if OUT_DIR.exists() and any(OUT_DIR.iterdir()):
        raise SystemExit(f"Refusing to overwrite existing human-only labels package: {OUT_DIR}")

    blind_rows = read_csv(BLIND_CSV)
    assert len(blind_rows) == 120
    assert set(BLIND_ANNOTATIONS.keys()) == {r["eval_id"] for r in blind_rows}

    timestamp = datetime.now(timezone.utc).isoformat()
    out_rows: list[dict[str, Any]] = []
    for row in blind_rows:
        eid = row["eval_id"]
        elig, t_span, c_span, rank_dec, precond, note = BLIND_ANNOTATIONS[eid]
        verbatim = row["entry_text_verbatim"]
        if t_span and t_span not in verbatim:
            raise SystemExit(f"Target span '{t_span}' not verbatim substring of {eid}: {verbatim}")
        out = dict(row)
        out["human_entry_eligibility"] = elig
        out["human_first_complete_target_span_exact"] = t_span
        out["human_context_note_spans_exact"] = c_span
        out["human_source_rank_1_to_12_or_abstain"] = rank_dec
        out["human_precondition_status"] = precond
        out["human_notes"] = note
        out["human_blind_recorded_utc"] = timestamp
        for k, v in out.items():
            assert_no_em_en_dash(str(v), f"{eid}.{k}")
        out_rows.append(out)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUT_DIR / "HUMAN_ONLY_BLIND_LABELS_120_V0_1.csv"
    write_csv(csv_path, out_rows, list(out_rows[0]))

    elig_counts = Counter(r["human_entry_eligibility"] for r in out_rows)
    rank_counts = Counter(r["human_source_rank_1_to_12_or_abstain"] for r in out_rows)
    tamiz_count = sum(1 for r in out_rows if "تمييز" in r["entry_text_verbatim"])

    summary_lines = [
        "# Gate B Human-Only Blind Evaluation Labels v0.1 (TODO Lines 38-39, 41-42)",
        "",
        "**Status:** completed strictly blind semantic reading of all `120` raw entries in `BLIND_EVALUATION_SHEET_120_V0_1.csv` WITHOUT opening `SEALED_MACHINE_PROPOSALS_120_V0_1.csv`. Single-researcher feasibility check; zero inter-reviewer reliability claimed. Pending user approval to freeze these human-only labels before unsealing machine proposals.",
        "",
        "## Full Denominators (`N = 120` entries reviewed)",
        f"- Eligibility counts: `{dict(sorted(elig_counts.items()))}`",
        f"- Entries carrying `تمييز` note: `{tamiz_count}`",
        f"- Non-empty `human_first_complete_target_span_exact`: `{sum(1 for r in out_rows if r['human_first_complete_target_span_exact'])}`",
        f"- Non-empty separated `human_context_note_spans_exact`: `{sum(1 for r in out_rows if r['human_context_note_spans_exact'])}`",
        "",
        "## Per-Rank & Abstention Distribution (12 Categories Preserved; Zero Collapsing)",
    ]
    for k, v in sorted(rank_counts.items(), key=lambda kv: (0 if kv[0].isdigit() else 1, int(kv[0]) if kv[0].isdigit() else 99, kv[0])):
        summary_lines.append(f"- `{k}`: **{v}**")
    summary_text = "\n".join(summary_lines) + "\n"
    assert_no_em_en_dash(summary_text, "HUMAN_ONLY_SUMMARY_V0_1.md")
    summary_path = OUT_DIR / "HUMAN_ONLY_SUMMARY_V0_1.md"
    summary_path.write_text(summary_text, encoding="utf-8", newline="\n")

    inputs = [BLIND_CSV, Path(__file__).resolve()]
    outputs = [csv_path, summary_path]
    manifest = {
        "package_id": OUT_DIR.name,
        "generated_at_utc": timestamp,
        "sealed_proposals_accessed": False,
        "counts": {
            "entries_reviewed": len(out_rows),
            "eligibility_counts": dict(sorted(elig_counts.items())),
            "per_rank_and_abstain_counts": dict(sorted(rank_counts.items())),
            "rules_enabled": 0,
        },
        "inputs": {path.relative_to(ROOT).as_posix(): digest(path) for path in inputs},
        "outputs": {path.name: digest(path) for path in outputs},
        "manifest_hash_policy": "MANIFEST.sha256 records this manifest hash separately; it is not recursively embedded.",
    }
    manifest_str = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    assert_no_em_en_dash(manifest_str, "MANIFEST.json")
    manifest_path = OUT_DIR / "MANIFEST.json"
    manifest_path.write_text(manifest_str, encoding="utf-8", newline="\n")
    (OUT_DIR / "MANIFEST.sha256").write_text(f"{digest(manifest_path)}  MANIFEST.json\n", encoding="ascii", newline="\n")

    print(json.dumps({"output": str(OUT_DIR), **manifest["counts"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
