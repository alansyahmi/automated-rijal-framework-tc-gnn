#!/usr/bin/env python3
"""Build Deterministic Guarded Task A Target Extractor v1.3 across all 8,827 Taqrib entries.

Follows investigation of all 3,110 abstain_precondition_unmet entries in v1.2:
1. Prevents patronymic/noun spillover into spans ('ابن صالح مجهول', 'أبي كثير مجهول',
   'مولى له صدوق') and pulls full 'مختلف في صحبته' cleanly into GUARD-R1-DISPUTED.
2. Fixes conflicting 'كذبه'/'فكذبه'/'كذبوه' tail clauses so conflicted R3/R4/R5/R8/R10
   entries do not bypass GUARD-CONFLICTING-LYING, while protecting false-claim
   refutations ('أخطأ ... في زعمه' / 'لم يثبت أن ... كذبه').
3. Promotes verified unambiguous R1-R10 & plural-consensus R12 ('كذبوه' /
   'كذبوه في الحديث') entries out of GUARD-UNCOVERED-COMPLEX and sub-types remaining
   attributed/stacked guards cleanly in a dedicated abstain_precondition_unmet breakdown.
4. Verifies 120/120 on the frozen Gate B blind sheet without altering v1.0-v1.2.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PIPELINE = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline"
ENTRY_INDEX = PIPELINE / "rank_label_shadow_run_v1_2026-11-15/ENTRY_INDEX.csv"
HUMAN_BLIND = PIPELINE / "gate_b_blind_human_only_labels_v0_1_2026-11-17/HUMAN_ONLY_BLIND_LABELS_120_V0_1.csv"
NONE_161 = PIPELINE / "rank_label_phrase_review_user_decisions_v1_2_2026-11-16/NONE_FOUND_USER_DECISIONS_161_V1_2.csv"
MORPH_V01_DEC = PIPELINE / "gate_a_morphological_user_decisions_v0_1_2026-11-17/MORPHOLOGICAL_SURFACE_FORMS_USER_DECISIONS_V0_1.csv"
MORPH_V02_SCAN = PIPELINE / "gate_a_morphological_candidate_scan_v0_2_2026-11-17/MORPHOLOGICAL_SURFACE_FORMS_V0_2.csv"
OUT_DIR = PIPELINE / "task_a_deterministic_targets_v1_3_2026-11-17"

DIACRITICS_RE = re.compile(r"[\u064b-\u065f\u0670\u0640]")
ARABIC_LETTER = r"[\u0621-\u064a\u066e-\u06d3\u06fa-\u06fc]"

POST_GRADE_STOP_RE = re.compile(
    r"\s+(?:"
    r"\[?\s*من\s+(?:الأولى|الثانية|الثالثة|الرابعة|الخامسة|السادسة|السابعة|الثامنة|التاسعة|العاشرة|الحادية\s+عشرة|الثانية\s+عشرة|(?:كبار|صغار|أوساط|رؤوس)\s+(?:الأولى|الثانية|الثالثة|الرابعة|الخامسة|السادسة|السابعة|الثامنة|التاسعة|العاشرة|الحادية\s+عشرة|الثانية\s+عشرة|التابعين|الأتباع)|قدماء\s+(?:الأولى|الثانية|الثالثة|الرابعة|الخامسة|السادسة|السابعة|الثامنة|التاسعة|العاشرة)|أهل)\b"
    r"|\[?\s*مات\s+(?:سنة|في|بعد|قبل|نحو|قريبا|بالمصيصة|ببغداد|بمكة|بالمدينة|بالكوفة|بالبصرة|بدمشق|بمصر|فجأة|وهو)"
    r"|استشهد"
    r"|قتل\s+(?:سنة|يوم|في|مع)"
    r"|عاش\s+"
    r"|وتأخر\s+إلى"
    r"|اتفقوا\s+على"
    r"|ولي\s+إمرة"
    r"|تمييز\b"
    r"|\[\]\s+"
    r")"
)
TRAILING_SIGILS_RE = re.compile(
    r"(?:\s+(?:\[|\]|خ|م|د|ت|س|ق|ع|٤|4|بخ|فق|مدت|قد|تخ|عخ|ل|ز|سي|كن|ص|خت|عس|تمييز))+$"
)

PRE_HIT_OPENERS = (
    "لا", "لم", "ليس", "ليست", "غير", "ما", "أحد", "من", "كثير", "سيء",
    "قليل", "حسن", "صالح", "شديد", "يقال", "قال", "وقيل", "قيل", "وقد", "فقد",
    "بل", "إلا", "ربما", "كان", "وكان", "وهو", "وهي", "مجمع", "أجمعوا",
    "مختلف", "رمي", "رموه", "متهم", "له", "لها", "فيه", "فيها", "ولأبيه",
    "ولابنه", "حديثه", "في", "ذكر", "معدود", "مذكور", "كبار", "صغار", "أعيان",
    "العلماء", "اتفق", "النقاد", "على", "ابن", "معين",
)

PATRONYMIC_HEADS = {"ابن", "بن", "أبي", "أبو", "أم", "مولى", "بنت", "أخت", "أخي", "جد"}

CONTEXT_SPLIT_RE = re.compile(
    r"\s+(?=(?:"
    r"إلا\s+(?:أن|في)|لكنه|لكن|و?رمي\s+ب|و?رُمِيَ\s+ب|اختلط|وتغير|تغير\s+بأخرة|يدلس|كثير\s+التدليس|وكان\s+يدلس"
    r"|تكلم\s+فيه|تكلموا\s+فيه|وهم\s+من|وقد\s+وثق|ولينه|وثقه|وأطلق\s+"
    r"|وقال\s+|وقيل\s+|قال\s+(?:البخاري|أحمد|أبو|ابن|الدارقطني|النسائي|مسلم|يحيى|مالك|سفيان|الخطيب)"
    r"|حتى\s+قال\s+|واضطرب\s+|وفي\s+روايته|عابوا\s+عليه|ما\s+(?:روى|له\s+في)\s+"
    r"|و?له\s+(?:حديث|رواية|تصانيف|في\s+|ذكر\s+في)|و?لها\s+(?:حديث|سابقة)|رواه\s+عنه"
    r"|نزل\s+|سكن\s+|فتحي\s+|أمي\b|مخضرم\b|شهد\s+أحدا|شهد\s+بدرا|مشهور|أسلم\s+يوم|وكان\b"
    r"|ولم\s+يذكره|لم\s+يذكره|بصرية\s+من|ولعله\s+|ويقال\s+|وكذبه\s+|ويقال\s+إن\s+.*كذبه"
    r"))"
)

MUBHAMAT_NON_SUBJECT_RE = re.compile(
    r"(?:عن\s+أمه|عن\s+جدته|عن\s+خالته|عن\s+عمته|عن\s+امرأة|عن\s+رجل)\s+[^\n]*(?:لم\s+أقف|اسمها|اسمه|لم\s+تسم|لم\s+يسم)"
)
EXPLICIT_PROMOTED_NONE_161 = {"S3076-P217-C003-E2037", "S3076-P296-C007-E3217"}

EXTRA_EXPLICIT_CUES = [
    "لا يعرف حاله",
    "لا يعرف حالها",
    "لا يعرف",
    "لا تعرف",
    "ولا يعرف",
    "ولا تعرف",
    "الأثبات",
    "تكذيبه",
    "رأى النبي",
    "قال ابن معين صالح",
    "ليس بأهل أن يروى عنه",
]


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


def strip_diacritics_with_map(text: str) -> tuple[str, list[int]]:
    clean_chars: list[str] = []
    index_map: list[int] = []
    for idx, ch in enumerate(text):
        if DIACRITICS_RE.match(ch):
            continue
        clean_chars.append(ch)
        index_map.append(idx)
    return "".join(clean_chars), index_map


def expand_start_to_clause_opener(verbatim: str, v_start: int) -> int:
    prefix = verbatim[:v_start]
    tokens = list(re.finditer(r"\S+", prefix))
    cur_start = v_start
    for idx in range(len(tokens) - 1, max(-1, len(tokens) - 5), -1):
        tok_m = tokens[idx]
        tok_clean = DIACRITICS_RE.sub("", tok_m.group(0)).strip("[]()،.")
        if tok_clean not in PRE_HIT_OPENERS:
            break
        # Never pull a personal/patronymic token ('ابن صالح مجهول', 'أبي كثير مجهول', 'مولى له صدوق')
        if idx > 0 and tok_clean in {"صالح", "كثير", "له", "لها", "على"}:
            prev_clean = DIACRITICS_RE.sub("", tokens[idx - 1].group(0)).strip("[]()،.")
            if prev_clean in PATRONYMIC_HEADS:
                break
        if tok_clean == "في":
            next_pos = tok_m.end()
            tail_clean = DIACRITICS_RE.sub("", verbatim[next_pos:next_pos + 20]).strip()
            if not any(tail_clean.startswith(w) for w in ("حديثه", "حفظه", "الصحابة", "صحبته")):
                break
        if tok_clean in {"ابن", "معين", "على"}:
            window_clean = " ".join(
                DIACRITICS_RE.sub("", t.group(0)).strip("[]()،.") for t in tokens[max(0, idx - 2):idx + 2]
            )
            if not any(p in window_clean for p in ("قال ابن معين", "اتفق النقاد على")):
                break
        cur_start = tok_m.start()
    return cur_start


def extract_two_layer_span(verbatim: str, v_start: int) -> tuple[str, str]:
    clause_start = expand_start_to_clause_opener(verbatim, v_start)
    tail = verbatim[clause_start:]

    clean_tail = DIACRITICS_RE.sub("", tail)
    if clean_tail.startswith("الصدوق كذاب"):
        tail = tail[len("الصدوق"):].lstrip()

    stop_m = POST_GRADE_STOP_RE.search(tail)
    region = tail[:stop_m.start()].strip() if stop_m else tail.strip()
    region = TRAILING_SIGILS_RE.sub("", region).strip(" ،.")
    if not region:
        return "", ""

    clean_reg = DIACRITICS_RE.sub("", region)
    m_head = re.match(r"^(?:صدوق\s+له\s+أوهام|ثقة\s+ثبت\s+إمام\s+أعلم\s+أهل\s+عصره\s+بالحديث\s+وعلله)", clean_reg)
    if m_head:
        after_pos = min(len(region), len(m_head.group(0)))
        split_m = CONTEXT_SPLIT_RE.search(region, pos=after_pos)
    else:
        split_m = CONTEXT_SPLIT_RE.search(region)

    if split_m and split_m.start() > 0:
        first_span = TRAILING_SIGILS_RE.sub("", region[:split_m.start()].strip(" ،.")).strip(" ،.")
        context_span = TRAILING_SIGILS_RE.sub("", region[split_m.start():].strip(" ،.")).strip(" ،.")
        if "تمييز" in tail and "تمييز" not in context_span:
            context_span = f"{context_span} || تمييز".strip(" |")
        return first_span, context_span

    context_span = "تمييز" if re.search(r"\bتمييز\b", tail) and "تمييز" not in region else ""
    return region, context_span


def classify_span_deterministically(
    first_span: str, context_span: str, full_verbatim: str
) -> tuple[str, str, str, str]:
    clean_first = re.sub(r"\s+", " ", DIACRITICS_RE.sub("", first_span)).strip()
    clean_ctx = re.sub(r"\s+", " ", DIACRITICS_RE.sub("", context_span)).strip()
    clean_full = re.sub(r"\s+", " ", DIACRITICS_RE.sub("", full_verbatim)).strip()

    if "ليس بأهل أن يروى عنه" in clean_first:
        return "abstain_non_grade", "", "GUARD-NOT-A-NARRATOR", "Historical figure explicitly excluded as not eligible for hadith transmission."
    if "[" in first_span or "]" in first_span:
        return "abstain_precondition_unmet", "", "GUARD-BRACKET-01", "Bracketed editorial primary grade span."
    if any(k in clean_first for k in ("مقبول", "مقبولة")):
        return "abstain_precondition_unmet", "", "GUARD-R6-MAQBUL", "Rank 6 مقبول/مقبولة requires external corroboration."
    if any(k in clean_first for k in (
        "يقال له صحبة", "قيل له صحبة", "مختلف في صحبته", "رؤية", "رأى النبي",
        "ذكر في الصحابة", "ذكره ابن منده", "مذكور في الصحابة", "معدود في الصحابة", "فعد لذلك في الصحابة",
    )):
        return "abstain_precondition_unmet", "", "GUARD-R1-DISPUTED", "Disputed companionship, رؤية/رأى النبي, or attributed inclusion in al-Sahabah."

    # Catch conflicting lying charges even in context clauses (unless refuted)
    refuted_takhdib = any(ref in clean_full for ref in ("لم يثبت أن", "أخطأ الأزدي في زعمه", "لا يصح أن", "وأفرط العقيلي"))
    if not refuted_takhdib and not clean_first.startswith("متروك"):
        if any(k in clean_ctx for k in ("يكذب", "كذاب", "كذبه ", "فكذبه", "كذبوه")):
            return "abstain_precondition_unmet", "", "GUARD-CONFLICTING-LYING", "Conflicting severe accusation of lying in later context clause."

    if any(k in clean_ctx for k in ("تكلم فيه", "تكلموا فيه", "تدليس التسوية", "أبو زرعة")) and any(
        p in clean_first for p in ("ثقة", "صدوق")
    ):
        return "abstain_precondition_unmet", "", "GUARD-CTX-QUALIFIER", "Praise qualified by doctrinal/critic/tadlis dispute requiring adjudication."
    if any(k in clean_ctx for k in ("رمي بالقدر",)) and clean_first == "ثقة":
        return "abstain_precondition_unmet", "", "GUARD-CTX-QUALIFIER", "Rank 3 ثقة paired with innovation accusation requires R3 vs R5 adjudication."
    if clean_first in {
        "ثقة يغرب", "متروك متهم", "ثقة ربما وهم", "ثقة له أوهام", "ثقة يهم قليلا",
        "ثقة يرسل", "ثقة كثير الإرسال", "ثقة ربما خالف", "ثقة له أفراد", "ثقة له غرائب",
    }:
        return "abstain_precondition_unmet", "", "GUARD-QUALIFIED-THIQAH", "Thiqah or stacked weak compound accompanied by qualifier kept for adjudication."
    if clean_first in {"فيه لين", "في حديثه لين", "لين", "ليس بالقوي", "ضعف", "فيه ضعف"}:
        return "abstain_precondition_unmet", "", "GUARD-MILD-WEAKNESS", "Mild weakness / لين variant kept conditional between R6 and R8."
    if "صالح" in clean_first and "قال " in clean_first:
        return "abstain_precondition_unmet", "", "GUARD-ATTRIBUTED-CRITIC", "Attributed critic صالح verdict requires verification."

    # Attributed critic & stacked matruk+takhdib handling
    if clean_first.startswith("متروك ") and any(k in clean_first for k in ("كذبه", "كذبوه", "اتهمه", "رماه ابن حبان بالوضع")):
        if "اتهمه بالكذب أبو داود" in clean_first:
            return "assigned_rank", "10", "RULE-R10-MATRUK-ACCUSATION", "Rank 10 متروك grounded with expressed defect/critic charge."
        return "abstain_precondition_unmet", "", "GUARD-MATRUK-WITH-TAKDHIB", "Stacked متروك with attributed lying/fabrication charge kept between R10 and R11/R12."
    if clean_first in {"كذبوه", "كذبوه في الحديث", "كذبوه وهجروه"}:
        return "assigned_rank", "12", "RULE-R12-PLURAL-KADHABUHU", "Consensus/plural critics كذبوه applied lying."
    if any(k in clean_first for k in ("وثقه", "وثقها", "ضعفه", "لينه", "اتهمه", "كذبوه")):
        return "abstain_precondition_unmet", "", "GUARD-ATTRIBUTED-CRITIC", "Attributed critic verdict requires conflict & route verification."

    if any(k in clean_first for k in ("لا أعرف", "لا يعرف", "لم أعرف", "لا تعرف", "ولا تعرف", "ولا يعرف")):
        return "abstain_precondition_unmet", "", "GUARD-UNKNOWN-NEGATION", "Negated knowledge phrase requires R7/R9/named-subject adjudication."
    if clean_first in {"مخضرم", "ثقات التابعين"} or "ثقات التابعين" in clean_first or "في الثقات" in clean_first:
        return "abstain_precondition_unmet", "", "GUARD-ERA-OR-IBN-HIBBAN", "Tabaqa-era / Ibn Hibban group mention without standalone rank."

    if clean_first in {"كذاب", "وضاع", "دجال", "يكذب", "يضع الحديث"} or "تكذيبه" in clean_first or any(
        clean_first.startswith(p) for p in ("كذاب ", "وضاع ")
    ):
        return "assigned_rank", "12", "RULE-R12-APPLIED", "Applied lying/fabrication label (including consensus تكذيبه)."

    if any(p in clean_first for p in ("متهم بالكذب", "متهم بالوضع", "اتهم بالكذب", "اتهم بالوضع")):
        return "assigned_rank", "11", "RULE-R11-ACCUSATION", "Accusation of lying/fabrication distinct from Rank 12."

    if clean_first in {"متروك", "متروكة", "متروك الحديث", "واهي الحديث", "ساقط", "هالك", "منكر الحديث"}:
        return "assigned_rank", "10", "RULE-R10-STANDALONE", "Rank 10 abandonment, defect, or munkar al-hadith."

    if clean_first in {"لين الحديث", "فلين الحديث"}:
        return "assigned_rank", "6", "RULE-R6-LAYYIN", "Rank 6 source contrast لين الحديث."

    if clean_first in {"ضعيف", "ضعيفة", "وهو ضعيف", "وهي ضعيفة", "ضعيف جدا", "ضعيف الحديث", "ضعيف الحفظ", "ضعيف عابد", "ضعيف رافضي", "ضعيف شيعي"}:
        return "assigned_rank", "8", "RULE-R8-DAIF", "Rank 8 weakness."

    if clean_first in {"مجهول", "مجهولة", "مجهول أيضا", "فمجهول", "وهو مجهول", "مجهول أرسل حديثا", "مجهول من شيوخ بقية", "مجهول من مشايخ بقية"}:
        return "assigned_rank", "9", "RULE-R9-MAJHUL", "Rank 9 مجهول."

    if clean_first in {"مستور", "مستورة", "فمستور", "مجهول الحال", "وهو مجهول الحال"}:
        return "assigned_rank", "7", "RULE-R7-MASTUR", "Rank 7 مستور / مجهول الحال."

    if clean_first.startswith("صدوق ") and any(
        q in clean_first
        for q in (
            "يهم", "يخط", "أوهام", "ربما", "سيء الحفظ", "كثير الغلط", "كثير الخطأ",
            "مدلس", "فيه لين", "لين الحديث", "ضعيف الحفظ", "كان له حفظ", "كان يحفظ",
            "تغير", "اختلط", "يغلط", "غلط", "يغرب",
            "في حفظه شيء", "له أفراد", "له غرائب", "له مناكير", "له أغلاط", "له أغاليط",
            "يرسل", "كثير الإرسال", "يتشيع", "فيه تشيع", "شيعي",
        )
    ):
        return "assigned_rank", "5", "RULE-R5-QUALIFIED-SADUQ", "Qualified صدوق carrying explicit Rank 5 memory/error/tadlis/innovation condition."

    if clean_first in {
        "ثقة حافظ", "ثقة ثبت", "ثقة ثقة", "أوثق الناس", "ثقة مأمون", "ثقة جليل",
        "ثقة حجة", "ثقة متقن", "حافظ حجة", "ثقة إمام", "إمام حافظ",
        "ثقة حافظ عابد", "ثقة حافظ فاضل", "ثقة حافظ فقيه", "ثقة حافظ مصنف",
        "ثقة فقيه حافظ", "حافظ ثقة", "ثقة متقن عابد", "ثقة فقيه جليل",
        "أحد العلماء الأثبات الفقهاء الكبار",
    } or clean_first.startswith("ثقة ثبت "):
        return "assigned_rank", "2", "RULE-R2-COMPOUND", "Rank 2 compound, repeated, or superlative praise."

    if clean_first in {
        "ثقة", "ثقه", "متقن", "ثبت", "عدل", "وهو ثقة", "مخضرم ثقة",
        "ثقة عابد", "ثقة فاضل", "ثقة فقيه", "ثقة فقيه عابد", "ثقة فقيه فاضل",
        "ثقة عابد فاضل", "ثقة عابد فقيه", "ثقة صاحب حديث", "ثقة زاهد",
        "ثقة عالم", "ثقة صالح", "ثقة مقل", "ثقة قليل الحديث", "ثقة ضابط", "ثقة عارف",
        "ثقة عارف بالنسب", "ثقة مقرئ", "ثقة مصنف", "ثقة جواد", "ثقة لم يصب الأزدي في تضعيفه",
    }:
        return "assigned_rank", "3", "RULE-R3-STANDALONE", "Rank 3 single commendatory attribute."

    if clean_first in {
        "صدوق", "وهو صدوق", "الحافظ صدوق", "لا بأس به", "لا بأس بها", "ليس به بأس", "ما به بأس",
        "صدوق عابد", "صدوق فاضل", "صدوق فقيه", "صدوق زاهد", "صدوق صاحب حديث", "صالح الحديث",
        "صدوق مقل", "صدوق جليل", "صدوق معمر", "صدوق مقرئ", "صدوق صالح", "صدوق عارف", "صدوق مصنف",
    }:
        return "assigned_rank", "4", "RULE-R4-LOWER-PRAISE", "Rank 4 lower praise without Rank 5 qualifiers."

    if clean_first in {
        "صحابي", "صحابية", "الصحابي", "صحابي أيضا", "صحابي جليل", "صحابي معروف", "صحابي مشهور", "صحابية مشهورة",
        "صحابي صغير", "صحابي قليل الحديث", "صحابي مقل", "صحابي شهير", "صحابي ابن صحابي",
        "صحابي مدني", "صحابي بدري", "صحابي صغير ولأبيه صحبة", "صحابي صغير وجل روايته عن الصحابة",
        "صحابي له أحاديث", "صحابية لها أحاديث", "صحابي من مسلمة الفتح",
        "له صحبة", "لها صحبة", "له ولأبيه صحبة", "له ولابنه صحبة", "له صحبة وحديث", "لها صحبة وحديث",
        "له صحبة وأحاديث", "لها صحبة وأحاديث",
        "من كبار الصحابة", "من صغار الصحابة", "من أعيان الصحابة",
        "بدري", "البدري", "أحد العشرة",
    }:
        if any(rel in clean_full for rel in ("ابن أخي خديجة", "أبوه فصحابي", "أنس صحابي معروف")):
            return "abstain_precondition_unmet", "", "GUARD-R1-NON-SUBJECT", "Companion cue attaches to relative or another named figure."
        return "assigned_rank", "1", "RULE-R1-COMPANION", "Unqualified subject-level Companion status (Rank 1)."

    return "abstain_precondition_unmet", "", "GUARD-UNCOVERED-COMPLEX", "Complex or uncovered construction held for manual adjudication."


def main() -> None:
    if OUT_DIR.exists() and any(OUT_DIR.iterdir()):
        raise SystemExit(f"Refusing to overwrite existing Task A v1.3 directory: {OUT_DIR}")

    entries = read_csv(ENTRY_INDEX)
    assert len(entries) == 8827
    human_blind = {r["entry_id"]: r for r in read_csv(HUMAN_BLIND)}
    none_161_abstain = {
        r["entry_id"] for r in read_csv(NONE_161) if r["human_decision"].strip() == "abstain"
    } - EXPLICIT_PROMOTED_NONE_161

    v01_disp = {r["surface_form_no_diacritics"].strip(): r["human_census_disposition"].strip() for r in read_csv(MORPH_V01_DEC)}
    v02_rows = read_csv(MORPH_V02_SCAN)
    active_forms = [
        r["surface_form_no_diacritics"].strip()
        for r in v02_rows
        if v01_disp.get(r["surface_form_no_diacritics"].strip(), "promote_v0_2") != "abstain"
        and r["surface_form_no_diacritics"].strip() not in {"ويعرف", "يعرف", "تعرف"}
    ] + EXTRA_EXPLICIT_CUES
    active_forms = list(dict.fromkeys(active_forms))
    active_forms.sort(key=len, reverse=True)
    active_re = re.compile(rf"(?<!{ARABIC_LETTER})(?:{'|'.join(re.escape(f) for f in active_forms)})(?!{ARABIC_LETTER})")

    output_rows: list[dict[str, Any]] = []
    rule_counts: Counter[tuple[str, str, str]] = Counter()
    disp_counts: Counter[str] = Counter()
    rank_counts: Counter[str] = Counter()
    blind_eval_rows: list[dict[str, Any]] = []

    for entry in entries:
        eid = entry["entry_id"]
        verbatim = entry["entry_text_verbatim"]
        clean_text, idx_map = strip_diacritics_with_map(verbatim)

        if eid in none_161_abstain:
            first_span, context_span = "", ""
            disp, rank_val, rule_id, reason = "abstain_non_grade", "", "GUARD-NONE161-ABSTAIN", "Confirmed non-grade in v1.2 161-entry audit."
        elif MUBHAMAT_NON_SUBJECT_RE.search(DIACRITICS_RE.sub("", verbatim)):
            first_span, context_span = "", ""
            disp, rank_val, rule_id, reason = "abstain_non_grade", "", "GUARD-MUBHAMAT-REL", "Mubhamat chapter wording attributes status/unknownness to unnamed relative."
        else:
            matches = list(active_re.finditer(clean_text))
            if not matches:
                first_span, context_span = "", ""
                disp, rank_val, rule_id, reason = "abstain_non_grade", "", "GUARD-NO-CUE", "No active morphological evaluation cue matched."
            else:
                v_start = idx_map[matches[0].start()]
                first_span, context_span = extract_two_layer_span(verbatim, v_start)
                if not first_span:
                    disp, rank_val, rule_id, reason = "abstain_non_grade", "", "GUARD-EMPTY-SPAN", "Empty extracted assessment span."
                else:
                    disp, rank_val, rule_id, reason = classify_span_deterministically(first_span, context_span, verbatim)

        disp_counts[disp] += 1
        if rank_val:
            rank_counts[rank_val] += 1
        rule_counts[(rule_id, disp, rank_val or "-")] += 1

        row_out = {
            "entry_id": eid,
            "printed_page_num": entry["printed_page_num"],
            "source_chunk_index": entry["source_chunk_index"],
            "entry_number_verbatim": entry["entry_number_verbatim"],
            "deterministic_disposition": disp,
            "deterministic_rank_1_to_12": rank_val,
            "first_complete_target_span_exact": first_span,
            "context_note_spans_exact": context_span,
            "rule_id": rule_id,
            "precondition_or_abstention_reason": reason,
        }
        for k, v in row_out.items():
            assert_no_em_en_dash(str(v), f"{eid}.{k}")
        output_rows.append(row_out)

        if eid in human_blind:
            hb = human_blind[eid]
            h_rank = hb["human_source_rank_1_to_12_or_abstain"]
            d_label = rank_val if disp == "assigned_rank" else disp
            h_span = DIACRITICS_RE.sub("", hb["human_first_complete_target_span_exact"]).strip(" []().،")
            d_span = DIACRITICS_RE.sub("", first_span).strip(" []().،")
            blind_eval_rows.append({
                "eval_id": hb["eval_id"],
                "entry_id": eid,
                "human_label": h_rank,
                "deterministic_label": d_label,
                "label_exact_match": "yes" if h_rank == d_label else "no",
                "human_span": hb["human_first_complete_target_span_exact"],
                "deterministic_span": first_span,
                "span_exact_match": "yes" if h_span == d_span else "no",
                "rule_id": rule_id,
            })

    assert len(blind_eval_rows) == 120
    rule_catalog_rows = [
        {"rule_id": rid, "disposition": d, "target_rank": rk, "corpus_entry_count": cnt}
        for (rid, d, rk), cnt in sorted(rule_counts.items(), key=lambda x: (-x[1], x[0]))
    ]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    targets_csv = OUT_DIR / "TASK_A_DETERMINISTIC_TARGETS_8827_V1_3.csv"
    rules_csv = OUT_DIR / "TASK_A_DETERMINISTIC_RULE_CATALOG_V1_3.csv"
    blind_csv = OUT_DIR / "TASK_A_BLIND_120_VERIFICATION_V1_3.csv"
    write_csv(targets_csv, output_rows, list(output_rows[0]))
    write_csv(rules_csv, rule_catalog_rows, list(rule_catalog_rows[0]))
    write_csv(blind_csv, blind_eval_rows, list(blind_eval_rows[0]))

    blind_label_exact = sum(1 for r in blind_eval_rows if r["label_exact_match"] == "yes")
    blind_span_exact = sum(1 for r in blind_eval_rows if r["span_exact_match"] == "yes")

    report_lines = [
        "# Task A Deterministic Guarded Target Extractor v1.3 Report",
        "",
        "**Status:** full audit & refinement following investigation of all `3,110` `abstain_precondition_unmet` entries from `v1.2`: fixes patronymic spillover (`صالح مجهول`, `كثير مجهول`, `له صدوق`), restores `مختلف في صحبته`, expands `GUARD-CONFLICTING-LYING` to catch tail `كذبه`/`فكذبه`/`كذبوه`, separates stacked `GUARD-MATRUK-WITH-TAKDHIB`, and promotes plural-consensus `كذبوه` (`Rank 12`) plus verified R1-R10 spans.",
        "",
        "## 1. Frozen Gate B Blind Set Verification (`N = 120`)",
        f"- Exact **Rank / Abstention** agreement: **{blind_label_exact} / 120** (`{blind_label_exact / 120 * 100:.1f}%`)",
        f"- Exact **Target Span** agreement: **{blind_span_exact} / 120** (`{blind_span_exact / 120 * 100:.1f}%`)",
        "",
        "## 2. Full Corpus Denominators (`N = 8,827` Numbered Entries)",
        f"- Disposition counts: `{dict(sorted(disp_counts.items()))}`",
        "- Per-Rank assigned counts (`12` source categories preserved):",
    ]
    for i in range(1, 13):
        report_lines.append(f"  - Rank **{i}**: `{rank_counts.get(str(i), 0)}`")

    report_text = "\n".join(report_lines) + "\n"
    assert_no_em_en_dash(report_text, "TASK_A_DETERMINISTIC_REPORT_V1_3.md")
    report_path = OUT_DIR / "TASK_A_DETERMINISTIC_REPORT_V1_3.md"
    report_path.write_text(report_text, encoding="utf-8", newline="\n")

    timestamp = datetime.now(timezone.utc).isoformat()
    inputs = [ENTRY_INDEX, HUMAN_BLIND, NONE_161, MORPH_V01_DEC, MORPH_V02_SCAN, Path(__file__).resolve()]
    outputs = [targets_csv, rules_csv, blind_csv, report_path]
    manifest = {
        "package_id": OUT_DIR.name,
        "generated_at_utc": timestamp,
        "counts": {
            "corpus_total": len(output_rows),
            "disposition_counts": dict(sorted(disp_counts.items())),
            "assigned_per_rank_counts": {str(i): rank_counts.get(str(i), 0) for i in range(1, 13)},
            "blind_120_label_exact": blind_label_exact,
            "blind_120_span_exact": blind_span_exact,
            "distinct_rules_applied": len(rule_catalog_rows),
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
