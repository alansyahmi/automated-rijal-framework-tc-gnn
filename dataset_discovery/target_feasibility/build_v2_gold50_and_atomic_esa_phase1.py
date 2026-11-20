#!/usr/bin/env python3
"""Phase 1 v2 Engine: Reconciled Gold-50 Validation Set, Canonical Provenance Dedup,
Atomic Clause Segmentation, 6D Multidimensional ESA, Double-Counting Guard,
and Train-Only Stratified 120-Narrator Pilot Worksheet.

Reads v1.3, v1.4, v0.3/v0.4 historical passages, and Shamela4 narrators/evaluations
in strictly read-only mode, and writes versioned v2 Phase 1 artifacts.
"""

from __future__ import annotations

import csv
import hashlib
import json
import random
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

csv.field_size_limit(10_000_000)

ROOT = Path(__file__).resolve().parents[2]
PIPELINE = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline"

ENTRY_INDEX_FP = PIPELINE / "rank_label_shadow_run_v1_2026-11-15/ENTRY_INDEX.csv"
TASK_A_V13_FP = PIPELINE / "task_a_deterministic_targets_v1_3_2026-11-17/TASK_A_DETERMINISTIC_TARGETS_8827_V1_3.csv"
TASK_A_V14_FP = PIPELINE / "task_a_deterministic_targets_v1_4_2026-11-19/TASK_A_DETERMINISTIC_TARGETS_8827_V1_4.csv"
LINKAGE_V03_FP = PIPELINE / "task_b_historical_inputs_v0_3_2026-11-17/TASK_B_NARRATOR_LINKAGE_AND_ELIGIBILITY_8827_V0_3.csv"
SPLITS_V01_FP = PIPELINE / "task_b_graph_and_splits_v0_1_2026-11-17/TASK_B_SPLITS_ELIGIBLE_NARRATORS_V0_1.csv"

V03_PASSAGES_FP = PIPELINE / "task_b_historical_inputs_v0_3_2026-11-17/TASK_B_ELIGIBLE_HISTORICAL_PASSAGES_V0_3.csv"
V04_ABL_FP = PIPELINE / "task_b_historical_inputs_v0_4_2026-11-17/TASK_B_EARLY_SPEAKER_ABLATION_PASSAGES_V0_4.csv"
V04_FWD_FP = PIPELINE / "task_b_historical_inputs_v0_4_2026-11-17/TASK_B_FWAED_PASSAGES_V0_4.csv"

SH_NARRATORS_FP = ROOT / "data/2_interim/shamela4_narrator_audit/narrators.csv"
SH_EVALS_FP = ROOT / "data/2_interim/shamela4_narrator_audit/evaluations_raw.csv"

OUT_DIR = PIPELINE / "v2_gold50_and_atomic_esa_v0_2_2026-11-19"

DIACRITICS_RE = re.compile(r"[\u064b-\u065f\u0670\u0640\u200c]")
BRACKET_SEG_RE = re.compile(r"\s*\[[^\]]+\]")
TAKHRIIJ_SWAP_RE = re.compile(r"^\s*(?:برقم\s*:|انظر\s*:|\(\d+\s*/\s*\d+\))")

PROHIBITED_SOURCE_SUBSTRINGS = (
    "تقريب", "التقريب", "تحرير", "تهذيب التهذيب", "لسان الميزان",
    "تعجيل المنفعة", "الإصابة", "تعريف أهل التقديس", "المجمع المؤسس",
    "إتحاف المهرة", "تغليق التعليق", "هدي الساري", "فتح الباري", "الرتبة عند ابن حجر",
)
PROHIBITED_GROUP_SUBSTRINGS = ("ابن حجر",)
SUMMARY_WORK_SUBSTRINGS = ("الكاشف",)

CLAUSE_SPLIT_RE = re.compile(
    r"(?:(?<=^)|(?<=[\s،.:؛]))(?=(?:وقال|قال|وسئل|سئل|وذكر|ذكره|سمعت|سألت)\s+)"
)
EXPLICIT_SPEAKER_RE = re.compile(
    r"^(?:وقال|قال|وسئل|سئل|وذكر|ذكره|وثقه|ضعفه)\s+"
    r"((?:أبو|ابو|ابن|أحمد|احمد|يحيى|يحيي|علي|محمد|البخاري|النسائي|النسايي|"
    r"الدارقطني|الترمذي|مسلم|شعبة|سفيان|مالك|الشافعي|العجلي|الساجي|الذهلي|"
    r"العقيلي|الفضل|الفلاس|العلائي|أبي|ابراهيم|إبراهيم|يزيد|عبد|مغلطاي|الدولابي)"
    r"(?:\s+\S+){0,4}?)\s*(?:[:،]|أن|ان|في\b|عند)"
)
PRONOM_ABU_HATIM_RE = re.compile(r"(?:سمعت\s+أبي|سألت\s+أبي|عن\s+أبي)")
PRONOM_AHMAD_RE = re.compile(r"(?:عبد\s+الله\s+بن\s+أحمد|أبي)\s*.*(?:سألت\s+أبي|قال\s+أبي)")


# Gold-50 Master Specification (1..50)
# Format: (gold_id, group_profile, english_name, entry_id, shamela_id_override,
#          user_sheet_rank, intro_literal_rank, recon_status, recon_note)
GOLD_50_SPEC: list[tuple[int, str, str, str, int | None, str, str, str, str]] = [
    # Group 1: Highly reliable narrators (1-8 from Gold-20, 21-30 from Gold 21-50)
    (1, "1_highly_reliable", "Malik ibn Anas", "S3076-P516-C004-E6425", None, "2", "2", "resolved_v1_4_promoted", "Abstained in v1.3 (GUARD-UNCOVERED-COMPLEX); promoted in v1.4 via RULE-R2-IMAM-SUPERLATIVE."),
    (2, "1_highly_reliable", "Shu'bah ibn al-Hajjaj", "S3076-P266-C013-E2790", None, "2", "2", "resolved_v1_4_promoted", "Abstained in v1.3; promoted in v1.4 via RULE-R2-IMAM-SUPERLATIVE."),
    (3, "1_highly_reliable", "Sufyan al-Thawri", "S3076-P244-C011-E2445", None, "2", "2", "resolved_v1_4_promoted", "Abstained in v1.3; promoted in v1.4 via RULE-R2-IMAM-SUPERLATIVE; post-tabaqa tadlis note extracted."),
    (4, "1_highly_reliable", "Sufyan ibn Uyaynah", "S3076-P245-C001-E2451", None, "2", "2", "resolved_v1_4_promoted", "Abstained in v1.3; promoted in v1.4 via RULE-R2-IMAM-SUPERLATIVE; late-life change & tadlis in context."),
    (5, "1_highly_reliable", "Yahya ibn Sa'id al-Qattan", "S3076-P591-C002-E7557", None, "2", "2", "resolved_v1_4_promoted", "Abstained in v1.3; promoted in v1.4 via RULE-R2-IMAM-SUPERLATIVE."),
    (6, "1_highly_reliable", "Abd al-Rahman ibn Mahdi", "S3076-P351-C006-E4018", None, "2", "2", "confirmed_exact", "Rank 2 compound praise in both v1.3 and v1.4."),
    (7, "1_highly_reliable", "al-Awza'i", "S3076-P347-C016-E3967", None, "2", "2", "confirmed_exact", "Rank 2 compound praise (ثقة جليل) in both v1.3 and v1.4."),
    (8, "1_highly_reliable", "al-Layth ibn Sa'd", "S3076-P464-C009-E5684", None, "2", "2", "confirmed_exact", "Rank 2 compound praise in both v1.3 and v1.4."),
    (21, "1_highly_reliable", "Abd Allah ibn al-Mubarak", "S3076-P320-C005-E3570", None, "2", "2", "confirmed_exact", "Rank 2 compound praise in both v1.3 and v1.4."),
    (22, "1_highly_reliable", "Waki' ibn al-Jarrah", "S3076-P581-C007-E7414", None, "2", "2", "confirmed_exact", "Rank 2 compound praise in both v1.3 and v1.4."),
    (23, "1_highly_reliable", "Hammad ibn Zayd", "S3076-P178-C007-E1498", None, "2", "2", "confirmed_exact", "Rank 2 compound praise in both v1.3 and v1.4."),
    (24, "1_highly_reliable", "Hammad ibn Salamah", "S3076-P178-C008-E1499", None, "2", "2", "resolved_v1_4_promoted", "Abstained in v1.3; promoted in v1.4 to Rank 2 with late-life change (وتغير حفظه بأخرة) in context."),
    (25, "1_highly_reliable", "al-Fadl ibn Dukayn", "S3076-P446-C001-E5401", None, "2", "2", "confirmed_exact", "Rank 2 compound praise (ثقة ثبت) in both v1.3 and v1.4."),
    (26, "1_highly_reliable", "Abd Allah ibn Wahb", "S3076-P328-C015-E3694", None, "2", "2", "confirmed_exact", "Rank 2 compound praise in both v1.3 and v1.4."),
    (27, "1_highly_reliable", "Yazid ibn Harun", "S3076-P606-C001-E7789", None, "2", "2", "confirmed_exact", "Rank 2 compound praise in both v1.3 and v1.4."),
    (28, "1_highly_reliable", "Jarir ibn Abd al-Hamid", "S3076-P139-C002-E0916", None, "2", "2", "resolved_v1_4_promoted", "Baseline ثقة صحيح الكتاب (Rank 2) separated from late-life memory qualifier (قيل كان في آخر عمره يهم من حفظه)."),
    (29, "1_highly_reliable", "Isma'il ibn Ulayyah", "S3076-P105-C011-E0416", None, "2", "2", "confirmed_exact", "Rank 2 compound praise (ثقة حافظ) in both v1.3 and v1.4."),
    (30, "1_highly_reliable", "Abu Dawud al-Tayalisi", "S3076-P250-C019-E2550", None, "2", "2", "resolved_v1_4_promoted", "Baseline ثقة حافظ (Rank 2) separated from error qualifier (غلط في أحاديث) in v1.4."),

    # Group 2: Nuanced / mixed assessments (9-15 from Gold-20, 31-40 from Gold 21-50)
    (9, "2_nuanced_mixed", "Muhammad ibn Ishaq", "S3076-P467-C014-E5725", None, "4", "4", "confirmed_exact", "Rank 4 (صدوق) with context qualifiers (يدلس ورمي بالتشيع والقدر)."),
    (10, "2_nuanced_mixed", "Abu Ishaq al-Sabi'i", "S3076-P423-C018-E5065", None, "3", "3", "resolved_v1_4_promoted", "Promoted to Rank 3 (ثقة مكثر عابد) in v1.4; post-tabaqa اختلط بأخرة extracted separately."),
    (11, "2_nuanced_mixed", "Ata ibn al-Sa'ib", "S3076-P391-C009-E4592", None, "4", "4", "confirmed_exact", "Rank 4 (صدوق) with context qualifier (اختلط)."),
    (12, "2_nuanced_mixed", "al-A'mash", "S3076-P254-C018-E2615", None, "2", "2", "resolved_v1_4_promoted", "Abstained in v1.3 (GUARD-BRACKET-01 on [بالقراءة]); promoted to Rank 2 in v1.4 with تدليس in context."),
    (13, "2_nuanced_mixed", "Qatadah ibn Di'amah", "S3076-P453-C014-E5518", None, "2", "2", "confirmed_exact", "Rank 2 compound praise (ثقة ثبت) in v1.3 and v1.4; note tadlis lies in external quotes."),
    (14, "2_nuanced_mixed", "Hisham ibn Urwah", "S3076-P573-C007-E7302", None, "3", "3", "resolved_v1_4_promoted", "Promoted to Rank 3 (ثقة فقيه) in v1.4 with ربما دلس separated into context."),
    (15, "2_nuanced_mixed", "Abd Allah ibn Lahi'ah", "S3076-P319-C013-E3563", None, "4", "4", "confirmed_exact", "Rank 4 (صدوق); post-tabaqa post-fire mixing & student-conditional reliability extracted."),
    (31, "2_nuanced_mixed", "Muhammad ibn Shihab al-Zuhri", "S3076-P506-C020-E6296", None, "2", "2", "resolved_v1_4_promoted", "Abstained in v1.3 (GUARD-BRACKET-01 on [وثبته]); promoted to Rank 2 in v1.4."),
    (32, "2_nuanced_mixed", "Nafi' mawla Ibn Umar", "S3076-P559-C003-E7086", None, "2", "2", "confirmed_exact", "Rank 2 compound praise (ثقة ثبت فقيه) in v1.3 and v1.4."),
    (33, "2_nuanced_mixed", "Amr ibn Dinar", "S3076-P421-C004-E5024", None, "2", "2", "confirmed_exact", "Rank 2 compound praise (ثقة ثبت) in v1.3 and v1.4."),
    (34, "2_nuanced_mixed", "Yahya ibn Abi Kathir", "S3076-P596-C001-E7632", None, "2", "2", "confirmed_exact", "Rank 2 (ثقة ثبت) with context qualifiers (لكنه يدلس ويرسل)."),
    (35, "2_nuanced_mixed", "Ikrimah mawla Ibn Abbas", "S3076-P397-C001-E4673", None, "2", "2", "fixed_v1_3_bug_false_r12", "v1.3 falsely assigned Rank 12 due to unsplit لم يثبت تكذيبه; fixed in v1.4 to Rank 2 with refuted accusation in context."),
    (36, "2_nuanced_mixed", "Ata ibn Abi Rabah", "S3076-P391-C008-E4591", None, "3*", "3", "pending_intro_review_r2_vs_r3", "Assigned Rank 3 (ثقة فقيه فاضل) with context كثير الإرسال and post-tabaqa late-life note; verify R3 vs R2 scholarly-epithet policy."),
    (37, "2_nuanced_mixed", "Tawus ibn Kaysan", "S3076-P281-C015-E3009", 2980, "3*", "3", "fixed_shamela_link_and_r3_review", "Fixed Shamela4 link from grandson 20152 to 2980 (طاووس بن كيسان); explicitly Rank 3 (ثقة فقيه فاضل)."),
    (38, "2_nuanced_mixed", "Mujahid ibn Jabr", "S3076-P520-C006-E6481", None, "3*", "3", "pending_intro_review_r2_vs_r3", "Promoted in v1.4 to conservative Rank 3 (ثقة إمام في التفسير وفي العلم); verify R2 vs R3 intro wording."),
    (39, "2_nuanced_mixed", "Sufyan ibn Husayn", "S3076-P244-C002-E2437", None, "3*", "3", "pending_intro_review_r3_conditional", "Promoted in v1.4 to Rank 3 conditional on non-Zuhri narrations (ثقة في غير الزهري باتفاقهم)."),
    (40, "2_nuanced_mixed", "Isma'il ibn Ayyash", "S3076-P109-C008-E0473", None, "4", "4", "resolved_v1_4_conditional_scope", "Baseline صدوق في روايته عن أهل بلده (Rank 4) + context مخلط في غيرهم; key test case for teacher/region-conditional reliability."),

    # Group 3: Criticised / weaker narrators (16-20 from Gold-20, 41-50 from Gold 21-50)
    (16, "3_criticised_weaker", "Jabir ibn Yazid al-Ju'fi", "S3076-P137-C002-E0878", None, "9", "8", "needs_rank8_vs_rank9_reconciliation", "Text is ضعيف رافضي. Literal Taqrib intro defines Rank 8 as ضعيف and Rank 9 as مجهول; user candidate sheet assigns 9."),
    (17, "3_criticised_weaker", "al-Harith al-A'war", "S3076-P146-C012-E1029", None, "abstain_conflicted", "abstain_conflicted", "abstain_for_adjudication", "Text is كذبه الشعبي في رأيه ورمي بالرفض وفي حديثه ضعف; retained as abstained conflicted case for Gold adjudication."),
    (18, "3_criticised_weaker", "Abd al-Rahman ibn Zayd ibn Aslam", "S3076-P340-C014-E3865", None, "9", "8", "needs_rank8_vs_rank9_reconciliation", "Text is ضعيف. Literal Taqrib intro Rank 8 vs user candidate sheet Rank 9."),
    (19, "3_criticised_weaker", "Layth ibn Abi Sulaym", "S3076-P464-C010-E5685", 5347, "4", "4", "fixed_shamela_link_needs_context_adj", "Fixed Shamela4 link to 5347 (الليث <-> ليث); Task A assigns Rank 4 on initial صدوق while context states اختلط جدا ولم يتميز حديثه فترك."),
    (20, "3_criticised_weaker", "al-Hajjaj ibn Artah", "S3076-P152-C015-E1119", None, "5", "5", "confirmed_exact", "Rank 5 (صدوق كثير الخطأ والتدليس) in v1.3 and v1.4."),
    (41, "3_criticised_weaker", "Muhammad ibn Abd al-Rahman ibn Abi Layla", "S3076-P493-C002-E6081", None, "5", "5", "confirmed_exact", "Rank 5 (صدوق سيء الحفظ جدا) in v1.3 and v1.4."),
    (42, "3_criticised_weaker", "Isma'il ibn Muslim al-Makki", "S3076-P110-C004-E0484", None, "9", "8", "needs_rank8_vs_rank9_reconciliation", "Text is ضعيف الحديث. Literal Taqrib intro Rank 8 vs user candidate sheet Rank 9."),
    (43, "3_criticised_weaker", "Abu Bakr ibn Abi Maryam", "S3076-P623-C010-E7974", None, "9", "8", "needs_rank8_vs_rank9_reconciliation", "Text is ضعيف + context وكان قد سرق بيته فاختلط. Literal Taqrib intro Rank 8 vs user sheet Rank 9."),
    (44, "3_criticised_weaker", "Abd Allah ibn Muharrar", "S3076-P320-C008-E3573", None, "10", "10", "confirmed_exact", "Rank 10 (متروك) in v1.3 and v1.4."),
    (45, "3_criticised_weaker", "Umar ibn Harun al-Balkhi", "S3076-P417-C018-E4979", None, "10", "10", "confirmed_exact", "Rank 10 (متروك) with positive memory note (وكان حافظا) in context."),
    (46, "3_criticised_weaker", "Salih ibn Bashir al-Murri", "S3076-P271-C007-E2845", None, "9", "8", "needs_rank8_vs_rank9_reconciliation", "Text is ضعيف. Literal Taqrib intro Rank 8 vs user candidate sheet Rank 9."),
    (47, "3_criticised_weaker", "Muhammad ibn al-Sa'ib al-Kalbi", "S3076-P479-C017-E5901", None, "11", "11", "confirmed_exact", "Rank 11 (متهم بالكذب) with sectarian note (ورمي بالرفض) in context."),
    (48, "3_criticised_weaker", "Muqatil ibn Sulayman", "S3076-P545-C001-E6868", None, "Pending: 11 or 12", "Pending: 11 or 12", "pending_r11_vs_r12_adjudication", "Text is كذبوه وهجروه ورمى بالتجسيم; held in v1.4 for explicit adjudication between Rank 11 and Rank 12."),
    (49, "3_criticised_weaker", "Amr ibn Shimr al-Ju'fi", "EXTERNAL-SH12587", 12587, "External da'if (al-Ghada'iri)", "N/A (not in Taqrib)", "external_source_exception", "Absent from Taqrib; linked to Shamela4 ID 12587 plus external Imami rijal record from al-Ghada'iri Kitab al-Du'afa' (1/3/3: ضعيف)."),
    (50, "3_criticised_weaker", "Hisham ibn Sa'd", "S3076-P572-C015-E7294", None, "5", "5", "confirmed_exact", "Rank 5 (صدوق له أوهام) with context (ورمي بالتشيع)."),
]

# Ordered idiom patterns for 6D ESA + 6 internal reliability dimensions
# Tuple: (pattern_regex, matched_label, family, domain, content, mode, force, negation, scope, dimension)
ESA_PATTERNS: list[tuple[str, str, str, str, str, str, str, int, str, str]] = [
    (r"أوثق\s+(?:الناس|أصحاب)|أثبت\s+(?:الناس\s+في|أصحاب)|أمير\s+المؤمنين\s+في\s+الحديث|إمام\s+حجة|متفق\s+على\s+جلالته|أعلم\s+(?:أهل\s+عصره|الناس)|أحفظ\s+الناس|أصح\s+الأسانيد", "superlative_imam_praise", "praise", "general_reliability;memory_precision", "superlative_praise", "attributed_individual_judgement", "superlative", 0, "none", "dim_dabt_precision"),
    (r"ثقة\s+(?:ثبت|حافظ|متقن|مأمون|حجة|إمام|ثقة|جليل|صحيح\s+الكتاب)|أطلق\s+.*بتوثيقه|أجمعوا\s+على\s+توثيقه", "compound_thiqah_praise", "praise", "general_reliability;memory_precision", "compound_trustworthiness", "attributed_individual_judgement", "emphatic", 0, "none", "dim_dabt_precision"),
    (r"ثقة\s+في\s+(?:غير\s+)?(?:الزهري|حديث|\S+)", "teacher_scoped_thiqah", "praise", "general_reliability", "conditional_teacher_strength", "attributed_individual_judgement", "qualified_limited", 0, "geographic_or_teacher_specific", "dim_conditional_scope_reliability"),
    (r"صدوق\s+في\s+روايته\s+عن\s+أهل\s+بلده|لا\s+بأس\s+بحديثه\s+إذا\s+حدث\s+عن\s+\S+", "regional_scoped_saduq", "praise", "honesty_veracity;memory_precision", "conditional_regional_reliability", "attributed_individual_judgement", "qualified_limited", 0, "geographic_or_teacher_specific", "dim_conditional_scope_reliability"),
    (r"مخلط\s+في\s+غيرهم|خلط\s+في\s+غيرهم|غلط\s+في\s+حديث\s+(?:الحجازيين|العراقيين|أهل\s+\S+)|ضعف\s+روايته\s+عن\s+غير\s+\S+|رواية\s+\S+\s+عنه\s+أعدل|في\s+روايته\s+عن\s+\S+\s+(?:اضطراب|شيء)", "conditional_mixing_by_origin", "criticism", "memory_precision;temporal_deterioration", "conditional_teacher_weakness", "attributed_individual_judgement", "qualified_limited", 0, "geographic_or_teacher_specific", "dim_conditional_scope_reliability"),
    (r"سرق\s+بيته\s+فاختلط|بعد\s+احتراق\s+كتبه", "post_fire_or_theft_ikhtilat", "criticism", "temporal_deterioration;memory_precision", "temporal_ikhtilat", "specific_behavior_or_transmission_observation", "qualified_limited", 0, "post_book_fire", "dim_temporal_ikhtilat"),
    (r"اختلط(?:\s+جدا|\s+بأخرة|\s+في\s+آخر\s+عمره)?|تغير\s+(?:حفظه\s+)?بأخرة|في\s+آخر\s+عمره\s+يهم|سمع\s+.*بأخرة", "late_life_ikhtilat_or_change", "criticism", "temporal_deterioration;memory_precision", "temporal_ikhtilat", "attributed_individual_judgement", "qualified_limited", 0, "temporal_late_life", "dim_temporal_ikhtilat"),
    (r"كثير\s+التدليس|كان\s+يدلس|ربما\s+دلس|لكنه\s+يدلس|يدلس|مدلس|أخذ\s+كتب\s+الناس\s+فيضعها\s+في\s+كتبه", "tadlis_practice", "criticism", "transmission_practice", "tadlis_practice", "specific_behavior_or_transmission_observation", "qualified_limited", 0, "none", "dim_tadlis_transmission"),
    (r"كثير\s+الإرسال|يرسل|مرسل|لم\s+يلق|لم\s+يسمع\s+من|لم\s+يرو\s+له\s+السماع|إنما\s+هي\s+مناولة|مناولة", "irsal_or_non_audition", "criticism", "transmission_practice", "irsal_practice", "specific_behavior_or_transmission_observation", "qualified_limited", 0, "none", "dim_tadlis_transmission"),
    (r"لم\s+يثبت\s+تكذيبه|لم\s+يثبت\s+أن|لا\s+تثبت\s+عنه\s+بدعة", "refuted_accusation", "praise", "honesty_veracity", "refuted_charge", "attributed_individual_judgement", "plain_direct", 1, "none", "dim_adalah_veracity"),
    (r"كذاب|وضاع|يضع\s+(?:الحديث|للروافض)|يروي\s+الموضوعات|كذبوه|كذبه\s+\S+", "lying_or_fabrication_applied", "criticism", "fabrication;honesty_veracity", "lying_or_fabrication", "attributed_individual_judgement", "emphatic", 0, "none", "dim_adalah_veracity"),
    (r"متهم\s+بالكذب|متهم\s+بالوضع|اتهم\s+بالكذب", "lying_accusation", "criticism", "fabrication;honesty_veracity", "lying_accusation", "attributed_individual_judgement", "emphatic", 0, "none", "dim_adalah_veracity"),
    (r"متروك(?:\s+الحديث)?|واهي\s+الحديث|ساقط|هالك|سكتوا\s+عنه", "severe_abandonment_matruk", "criticism", "authority_for_ihtijaj;general_reliability", "critical_silence_abandonment", "attributed_individual_judgement", "emphatic", 0, "none", "dim_corroboration_and_knownness"),
    (r"منكر\s+الحديث|يروي\s+المناكير|حدث\s+بالمناكير|له\s+مناكير|يأتي\s+بالمناكير", "munkar_or_manakir", "criticism", "corroboration_and_isolation;memory_precision", "corroboration_deficit", "attributed_individual_judgement", "emphatic", 0, "none", "dim_corroboration_and_knownness"),
    (r"لا\s+يتابع(?:\s+عليه|\s+على\s+أكثره)?|عامة\s+ما\s+يرويه\s+غير\s+محفوظ|غير\s+محفوظ|يتفرد\s+به|تفرد\s+به", "isolation_or_non_corroboration", "criticism", "corroboration_and_isolation", "corroboration_deficit", "attributed_individual_judgement", "plain_direct", 0, "none", "dim_corroboration_and_knownness"),
    (r"لا\s+يحتج\s+به|ليس\s+بحجة|لا\s+يكتب\s+حديثه", "negated_ihtijaj_authority", "criticism", "authority_for_ihtijaj", "ihtijaj_authority", "attributed_individual_judgement", "negated_strength", 1, "none", "dim_corroboration_and_knownness"),
    (r"يحتج\s+به|يكتب\s+حديثه|استشهد\s+به|أستدل\s+به|يعتبر\s+به|أخرج\s+له\s+(?:البخاري|مسلم|في\s+الصحيح)", "ihtijaj_or_canonical_usage", "authority_or_proof", "authority_for_ihtijaj", "ikhtibar_writing_permission", "attributed_individual_judgement", "qualified_limited", 0, "none", "dim_corroboration_and_knownness"),
    (r"ليس\s+بثقة|ليس\s+بشيء|لا\s+شيء(?:\s+البتة)?|فيه\s+نظر|ليس\s+هو\s+محكم\s+الحديث", "severe_negated_trustworthiness", "criticism", "general_reliability", "negated_trustworthiness", "attributed_individual_judgement", "negated_strength", 1, "none", "dim_dabt_precision"),
    (r"ليس\s+بالقوي|ليس\s+بذاك|لين(?:\s+الحديث)?|فيه\s+ضعف|ضعيف(?:\s+الحديث|\s+جدا)?|ضعفه|ضعفوه|في\s+(?:كتاب\s+)?(?:«|\")?الضعفاء", "general_weakness_daif", "criticism", "general_reliability;memory_precision", "weakness_daif", "attributed_individual_judgement", "plain_direct", 0, "none", "dim_dabt_precision"),
    (r"سي[ءئ]\s+الحفظ|كثير\s+الخطأ|كثير\s+الغلط|غلط\s+في\s+(?:أحاديث|حديث)|له\s+أوهام|يخط[ئى]|يهم|يضطرب|مضطرب", "memory_and_error_deficit", "criticism", "memory_precision", "memory_or_error_qualification", "attributed_individual_judgement", "plain_direct", 0, "none", "dim_dabt_precision"),
    (r"رمي\s+ب(?:التشيع|القدر|الرفض|التجسيم|الإرجاء|النصب)|رمى\s+ب(?:التشيع|القدر|الرفض|التجسيم)|رافضي|شيعي", "doctrinal_innovation_note", "criticism", "doctrinal_position;honesty_veracity", "doctrinal_innovation", "attributed_individual_judgement", "plain_direct", 0, "none", "dim_adalah_veracity"),
    (r"مجهول(?:\s+الحال)?|مستور|لا\s+أعرفه|لا\s+يعرف", "unknownness_jahalah", "unknownness", "unknownness_or_majhul_status", "unknownness_status", "first_person_knowledge_gap", "plain_direct", 0, "none", "dim_corroboration_and_knownness"),
    (r"لا\s+بأس\s+ب(?:ه|حديثه|روايته)|ليس\s+به\s+بأس|محله\s+الصدق|صالح(?:\s+الحديث)?|صدوق", "moderate_saduq_or_la_bas", "praise", "honesty_veracity;general_reliability", "moderate_truthfulness", "attributed_individual_judgement", "plain_direct", 0, "none", "dim_adalah_veracity"),
    (r"ثقة|ثقه|ثبت|حافظ|متقن|عدل|صح[ي]?ح\s+الكتاب|وثقه|في\s+(?:كتاب\s+)?(?:«|\")?الثقات|أحب\s+إلي|أجل\s+من|عنده\s+الأصول|الصواب\s+في\s+يد", "standalone_thiqah_praise", "praise", "general_reliability;memory_precision", "trustworthiness", "attributed_individual_judgement", "plain_direct", 0, "none", "dim_dabt_precision"),
    (r"له\s+صحبة|صحابي|له\s+وفادة|له\s+رؤية|كتاب\s+الصحابة|روى\s+عنه|سمع\s+من|سمع\s+.*من\s+أصحاب|قتل\s+يوم|مات\s+سنة|يسكن\s+|يختم\s+القرآن|يصوم\s+الدهر|صلاة\s+وصياما|من\s+خيار\s+عباد|من\s+عباد\s+أهل|من\s+سادات\s+التابعين|عابد|زاهد|فاضل|ورع|فقيه|عالم|إمام\s+في\s+التفسير|مشهور|شيخ|رواه\s+(?:الإمام\s+)?أحمد|رواه\s+ابن\s+ماجه", "biographical_piety_or_isnad_status", "status_or_biography", "biographical_information", "scholarly_or_biographical_attribute", "status_or_biographical_statement", "plain_direct", 0, "none", "dim_corroboration_and_knownness"),
]
COMPILED_ESA_PATTERNS = [(re.compile(pat), *rest) for pat, *rest in ESA_PATTERNS]


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


def sanitize_dashes(text: str) -> str:
    return (text or "").replace("\u2014", "-").replace("\u2013", "-")


def normalize_arabic(text: str) -> str:
    s = DIACRITICS_RE.sub("", text or "")
    s = s.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ى", "ي").replace("ة", "ه")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def linear_baseline_B(rank_str: str) -> str:
    if rank_str.endswith("*"):
        rank_str = rank_str[:-1]
    if rank_str.isdigit():
        r = int(rank_str)
        if 1 <= r <= 12:
            return f"{1.0 - (r - 1) / 11.0:.4f}"
    return ""


def extract_full_name_arabic(entry_text: str, target_span: str) -> str:
    text = re.sub(r"^[٠-٩\d]+\s*-\s*", "", entry_text).strip()
    if target_span:
        pos = text.find(target_span)
        if pos > 0:
            prefix = text[:pos].strip(" ،.-")
            # Strip common inline dabt/glosses? Preserve clean Arabic header up to target span
            return prefix
    # Fallback: stop before tabaqa or death phrase
    m = re.search(r"\s+(?:من\s+(?:الأولى|الثانية|الثالثة|الرابعة|الخامسة|السادسة|السابعة|الثامنة|التاسعة|العاشرة)|مات\s+سنة)", text)
    return text[:m.start()].strip() if m else text[:120].strip()


DANGLING_PREAMBLE_RE = re.compile(
    r"^(?:وقال|قال|وسئل|سئل|وذكر|ذكره|سمعت|سألت|حدثنا|نا|ثنا|أخبرنا|أنا|وفي)\b.*?(?:قال|يقول|أيضا|إلي|أبي)\s*$"
)


def split_clauses_and_resolve_speaker(
    passage_text: str, header_critic: str, source_work: str, group_labels_set: str
) -> list[dict[str, str]]:
    raw = passage_text.strip()
    if not raw:
        return []
    raw_parts = [p.strip(" ،.:؛") for p in CLAUSE_SPLIT_RE.split(raw) if p and p.strip(" ،.:؛")]
    if not raw_parts:
        raw_parts = [raw]

    # Merge dangling attribution preambles (e.g. "نا عبد الرحمن قال", "وقال أيضا") into next clause
    parts: list[str] = []
    i = 0
    while i < len(raw_parts):
        cur = raw_parts[i]
        cur_clean = DIACRITICS_RE.sub("", cur).strip()
        if (
            i + 1 < len(raw_parts)
            and len(cur_clean) < 110
            and ":" not in cur_clean
            and (DANGLING_PREAMBLE_RE.match(cur_clean) or cur_clean in {"قال", "وقال", "يقول", "قال أيضا", "وقال أيضا"})
        ):
            raw_parts[i + 1] = f"{cur}: {raw_parts[i + 1]}"
        else:
            parts.append(cur)
        i += 1
    if not parts:
        parts = raw_parts

    resolved_units: list[dict[str, str]] = []
    for clause in parts:
        c_norm = DIACRITICS_RE.sub("", clause)
        speaker = header_critic or "UNATTRIBUTED"
        reporter = ""
        attr_method = "header_single" if header_critic and header_critic != "غير منسوب" else "unattributed"

        if "الجرح والتعديل" in source_work and PRONOM_ABU_HATIM_RE.search(c_norm):
            speaker = "أبو حاتم الرازي"
            reporter = "ابن أبي حاتم"
            attr_method = "pronominal_resolved"
        elif PRONOM_AHMAD_RE.search(c_norm):
            speaker = "أحمد بن حنبل"
            reporter = "عبد الله بن أحمد"
            attr_method = "pronominal_resolved"
        else:
            m_exp = EXPLICIT_SPEAKER_RE.match(c_norm)
            if m_exp:
                speaker = m_exp.group(1).strip(" :،")
                attr_method = "explicit_internal" if len(parts) == 1 else "compound_split"
            elif len(parts) > 1 and header_critic and header_critic != "غير منسوب":
                attr_method = "compound_split"

        resolved_units.append({
            "clause_text_verbatim": clause,
            "speaker_canonical": speaker,
            "reporter_or_transmitter": reporter,
            "attribution_method": attr_method,
            "shamela_group_labels_set": group_labels_set,
        })
    return resolved_units


def tag_6d_esa_and_dimension(clause: str, source_work: str, stage1_span: str) -> dict[str, Any]:
    clean = re.sub(r"\s+", " ", DIACRITICS_RE.sub("", clause)).strip()
    hits = []
    for pat, label, fam, dom, content, mode, force, neg, scope, dim in COMPILED_ESA_PATTERNS:
        if pat.search(clean):
            hits.append((label, fam, dom, content, mode, force, neg, scope, dim))

    if not hits:
        return {
            "matched_cue_or_idiom": "",
            "statement_family": "unresolved",
            "statement_domain": "unresolved",
            "claim_content": "unresolved",
            "claim_mode": "attributed_individual_judgement",
            "wording_force": "not_applicable",
            "consensus_wording": "collective_agreement_claimed" if any(k in clean for k in ("اتفق", "أجمعوا", "باتفاقهم", "كذبوه", "سكتوا")) else "none",
            "negation_flag": 1 if re.search(r"(?:^|\s)(?:لا|لم|ليس|غير)\s+", clean) else 0,
            "conditional_scope": "none",
            "referent_target": "narrator_subject",
            "primary_reliability_dimension": "dim_dabt_precision",
        }

    # Primary hit is highest priority pattern; merge domains across all hits
    label, fam, _, content, mode, force, neg, scope, dim = hits[0]
    families = {h[1] for h in hits}
    if "praise" in families and "criticism" in families:
        fam = "mixed"
    domains = ";".join(dict.fromkeys(d for h in hits for d in h[2].split(";")))
    scopes = [h[7] for h in hits if h[7] != "none"]
    final_scope = scopes[0] if scopes else "none"
    consensus = "collective_agreement_claimed" if any(k in clean for k in ("اتفق", "أجمعوا", "باتفاقهم", "كذبوه", "سكتوا")) else "none"
    referent = "specific_report_or_teacher" if final_scope in {"geographic_or_teacher_specific", "partial_hadith"} else "narrator_subject"

    return {
        "matched_cue_or_idiom": ";".join(dict.fromkeys(h[0] for h in hits)),
        "statement_family": fam,
        "statement_domain": domains,
        "claim_content": content,
        "claim_mode": mode,
        "wording_force": force,
        "consensus_wording": consensus,
        "negation_flag": neg,
        "conditional_scope": final_scope,
        "referent_target": referent,
        "primary_reliability_dimension": dim,
    }


def compute_double_counting_flag(
    extraction_channel: str,
    clause: str,
    stage1_span: str,
    esa: dict[str, Any],
    seen_scholar_dim: set[tuple[str, str, str]],
    speaker: str,
) -> tuple[str, int]:
    if esa["statement_family"] == "status_or_biography":
        return "biographical_context_not_reliability_adjustment", 0

    if not stage1_span:
        key = (speaker, esa["primary_reliability_dimension"], esa["claim_content"])
        if key in seen_scholar_dim:
            return "duplicate_scholar_dimension_citation", 0
        seen_scholar_dim.add(key)
        return "external_critic_statement", 1

    clean_clause = normalize_arabic(clause)
    clean_s1 = normalize_arabic(stage1_span)

    if extraction_channel == "taqrib_baseline_span":
        return "already_encoded_in_stage1_baseline_span", 0

    if extraction_channel in {"taqrib_context_note", "taqrib_post_tabaqa_qualifier"}:
        if clean_clause and clean_clause in clean_s1:
            return "already_encoded_in_stage1_baseline_span", 0
        return "taqrib_qualifier_distinct_from_baseline_rank", 1

    # External historical critic passage
    key = (speaker, esa["primary_reliability_dimension"], esa["claim_content"])
    if key in seen_scholar_dim:
        return "duplicate_scholar_dimension_citation", 0
    seen_scholar_dim.add(key)

    if clean_clause in clean_s1 or (esa["claim_content"] == "trustworthiness" and "ثقه" in clean_s1 and esa["statement_family"] == "praise"):
        return "corroborates_stage1_same_polarity_do_not_double_count", 0

    return "external_critic_additional_evidence", 1


def load_supplementary_shamela_evals(target_sids: set[str]) -> dict[str, list[dict[str, str]]]:
    by_sid: dict[str, list[dict[str, str]]] = defaultdict(list)
    with SH_EVALS_FP.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            nid = r["narrator_id"]
            if nid not in target_sids:
                continue
            title = r["normalised_title_candidate"]
            cit = r["source_citation_raw"]
            grp = r["group_label_raw"]
            qtext = r["quotation_text"].strip()
            blob = f"{title} || {cit}"
            if any(k in blob for k in PROHIBITED_SOURCE_SUBSTRINGS) or any(k in grp for k in PROHIBITED_GROUP_SUBSTRINGS):
                continue
            if not qtext:
                continue
            by_sid[nid].append({
                "entry_id": "",
                "shamela_narrator_id": nid,
                "extraction_channel": "shamela4_eval_supplement_firewall_clean",
                "historical_attribution_critic": grp,
                "source_work_normalised": title,
                "source_citation_exact": cit,
                "text": qtext,
            })
    return by_sid


def deduplicate_passages(raw_passages: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for p in raw_passages:
        txt = sanitize_dashes(p["text"]).strip()
        if not txt or TAKHRIIJ_SWAP_RE.match(DIACRITICS_RE.sub("", txt)):
            continue
        wrk = sanitize_dashes(p["source_work_normalised"])
        cit = sanitize_dashes(p["source_citation_exact"])
        crit = sanitize_dashes(p["historical_attribution_critic"]).strip()
        key = (
            p["target_id"],
            normalize_arabic(wrk),
            normalize_arabic(cit),
            normalize_arabic(txt),
        )
        if key not in grouped:
            grouped[key] = {
                **p,
                "text": txt,
                "source_work_normalised": wrk,
                "source_citation_exact": cit,
                "historical_attribution_critic": crit,
                "group_labels": set([crit] if crit else []),
            }
        else:
            if crit:
                grouped[key]["group_labels"].add(crit)
    deduped = []
    for idx, item in enumerate(grouped.values(), start=1):
        item["canonical_passage_id"] = f"CP-{idx:06d}"
        item["shamela_group_labels_set"] = " | ".join(sorted(item.pop("group_labels")))
        deduped.append(item)
    return deduped


def main() -> None:
    if OUT_DIR.exists() and any(OUT_DIR.iterdir()):
        raise SystemExit(f"Refusing to overwrite existing output directory: {OUT_DIR}")

    entry_map = {r["entry_id"]: r for r in read_csv(ENTRY_INDEX_FP)}
    ta_v13 = {r["entry_id"]: r for r in read_csv(TASK_A_V13_FP)}
    ta_v14 = {r["entry_id"]: r for r in read_csv(TASK_A_V14_FP)}
    lnk_v03 = {r["entry_id"]: r for r in read_csv(LINKAGE_V03_FP)}
    splits_v01 = {r["entry_id"]: r for r in read_csv(SPLITS_V01_FP)}
    sh_narrs = {r["id"]: r for r in read_csv(SH_NARRATORS_FP)}

    # Load supplementary Shamela4 passages for fixed/external Gold-50 SIDs (Layth 5347, Tawus 2980, Amr 12587)
    supp_sids = {"5347", "2980", "12587"}
    supp_evals = load_supplementary_shamela_evals(supp_sids)

    # Index existing v0.3 + v0.4 passages by entry_id
    passages_by_eid: dict[str, list[dict[str, str]]] = defaultdict(list)
    for fp, chan in [
        (V03_PASSAGES_FP, "v03_eval"),
        (V04_ABL_FP, "v04_abl"),
        (V04_FWD_FP, "v04_fwaed"),
    ]:
        for r in read_csv(fp):
            eid = r["entry_id"]
            txt = r.get("fwaed_text_exact", "") if chan == "v04_fwaed" else r.get("quotation_text_exact", "")
            spk = r.get("fwaed_category", "") if chan == "v04_fwaed" else r.get("historical_attribution_critic", "")
            wrk = "Fwaed (Shamela4)" if chan == "v04_fwaed" else r.get("source_work_normalised", "")
            passages_by_eid[eid].append({
                "target_id": eid,
                "shamela_narrator_id": r["shamela_narrator_id"],
                "extraction_channel": chan,
                "historical_attribution_critic": spk,
                "source_work_normalised": wrk,
                "source_citation_exact": r.get("source_citation_exact", ""),
                "text": txt,
            })

    # 1. Build Gold-50 Reconciled Table & Collect Gold-50 Stage 2 Atomic Claims
    gold_rows: list[dict[str, Any]] = []
    gold_atomic_rows: list[dict[str, Any]] = []
    gold_eids_in_taqrib: set[str] = set()

    for (
        gold_id, group_profile, eng_name, eid, sid_override,
        user_rk, intro_rk, recon_status, recon_note
    ) in GOLD_50_SPEC:
        if eid != "EXTERNAL-SH12587":
            gold_eids_in_taqrib.add(eid)
            e_row = entry_map[eid]
            r13 = ta_v13[eid]
            r14 = ta_v14[eid]
            l_row = lnk_v03[eid]
            sp_row = splits_v01.get(eid, {})
            sid = str(sid_override) if sid_override is not None else l_row["shamela_narrator_id"]
            full_text = e_row["entry_text_verbatim"]
            full_name_ar = extract_full_name_arabic(full_text, r14["first_complete_target_span_exact"])
            v13_disp = r13["deterministic_disposition"]
            v13_rk = r13["deterministic_rank_1_to_12"]
            v13_span = r13["first_complete_target_span_exact"]
            v13_ctx = r13["context_note_spans_exact"]
            v13_rule = r13["rule_id"]
            v14_disp = r14["deterministic_disposition"]
            v14_rk = r14["deterministic_rank_1_to_12"]
            v14_span = r14["first_complete_target_span_exact"]
            v14_ctx = r14["context_note_spans_exact"]
            v14_post = r14["post_tabaqa_context_spans"]
            v14_rule = r14["rule_id"]
            task_b_split = sp_row.get("split", "not_in_task_b_5250_split")
        else:
            sid = str(sid_override)
            sh_r = sh_narrs[sid]
            full_name_ar = "عمرو بن شمر، أبو عبد الله، الجعفي"
            full_text = (
                "External Imami Rijal Source (al-Ghada'iri, Kitab al-Du'afa', 1/3/3): "
                "3 - عمرو بن شمر، أبو عبد الله، الجعفي. روى عن أبي عبد الله (عليه السلام) وجابر. ضعيف."
            )
            v13_disp = v14_disp = "external_no_taqrib_entry"
            v13_rk = v14_rk = ""
            v13_span = v14_span = ""
            v13_ctx = v14_ctx = v14_post = ""
            v13_rule = v14_rule = "EXTERNAL-NO-TAQRIB"
            task_b_split = "external_only"

        # Gather Stage 2 passages for this Gold narrator
        raw_stage2: list[dict[str, str]] = []
        if v14_ctx:
            for c_seg in v14_ctx.split(" || "):
                if c_seg.strip() and c_seg.strip() != "تمييز":
                    raw_stage2.append({
                        "target_id": eid,
                        "shamela_narrator_id": sid,
                        "extraction_channel": "taqrib_context_note",
                        "historical_attribution_critic": "ابن حجر العسقلاني (Taqrib Context)",
                        "source_work_normalised": "تقريب التهذيب",
                        "source_citation_exact": eid,
                        "text": c_seg.strip(),
                    })
        if v14_post:
            for p_seg in v14_post.split(" || "):
                if p_seg.strip():
                    raw_stage2.append({
                        "target_id": eid,
                        "shamela_narrator_id": sid,
                        "extraction_channel": "taqrib_post_tabaqa_qualifier",
                        "historical_attribution_critic": "ابن حجر العسقلاني (Taqrib Post-Tabaqa)",
                        "source_work_normalised": "تقريب التهذيب",
                        "source_citation_exact": eid,
                        "text": p_seg.strip(),
                    })

        if sid_override is not None:
            for sp in supp_evals.get(str(sid_override), []):
                raw_stage2.append({**sp, "target_id": eid})
        else:
            raw_stage2.extend(passages_by_eid.get(eid, []))

        if eid == "EXTERNAL-SH12587":
            raw_stage2.append({
                "target_id": eid,
                "shamela_narrator_id": sid,
                "extraction_channel": "external_user_supplied_imami_source",
                "historical_attribution_critic": "ابن الغضائري",
                "source_work_normalised": "كتاب الضعفاء للغضائري",
                "source_citation_exact": "Vol. 1, Sec. 3, Part Ayn, No. 3",
                "text": "روى عن أبي عبد الله (عليه السلام) وجابر. ضعيف.",
            })

        deduped = deduplicate_passages(raw_stage2)
        seen_scholar_dim: set[tuple[str, str, str]] = set()
        narrator_units = []
        for p in deduped:
            clauses = split_clauses_and_resolve_speaker(
                p["text"],
                p["historical_attribution_critic"],
                p["source_work_normalised"],
                p["shamela_group_labels_set"],
            )
            for c_idx, cu in enumerate(clauses, start=1):
                esa = tag_6d_esa_and_dimension(cu["clause_text_verbatim"], p["source_work_normalised"], v14_span)
                dc_status, w_elig = compute_double_counting_flag(
                    p["extraction_channel"],
                    cu["clause_text_verbatim"],
                    v14_span,
                    esa,
                    seen_scholar_dim,
                    cu["speaker_canonical"],
                )
                unit = {
                    "atomic_unit_id": f"G{gold_id:02d}-{p['canonical_passage_id']}-U{c_idx:02d}",
                    "gold_id": gold_id,
                    "english_name": eng_name,
                    "entry_id": eid,
                    "shamela_narrator_id": sid,
                    "canonical_passage_id": p["canonical_passage_id"],
                    "extraction_channel": p["extraction_channel"],
                    "source_work_normalised": p["source_work_normalised"],
                    "source_citation_exact": p["source_citation_exact"],
                    "speaker_canonical": cu["speaker_canonical"],
                    "reporter_or_transmitter": cu["reporter_or_transmitter"],
                    "attribution_method": cu["attribution_method"],
                    "shamela_group_labels_set": cu["shamela_group_labels_set"],
                    "clause_text_verbatim": cu["clause_text_verbatim"],
                    "matched_cue_or_idiom": esa["matched_cue_or_idiom"],
                    "statement_family": esa["statement_family"],
                    "statement_domain": esa["statement_domain"],
                    "claim_content": esa["claim_content"],
                    "claim_mode": esa["claim_mode"],
                    "wording_force": esa["wording_force"],
                    "consensus_wording": esa["consensus_wording"],
                    "negation_flag": esa["negation_flag"],
                    "conditional_scope": esa["conditional_scope"],
                    "referent_target": esa["referent_target"],
                    "primary_reliability_dimension": esa["primary_reliability_dimension"],
                    "double_count_status": dc_status,
                    "weight_eligible": w_elig,
                }
                for k, v in unit.items():
                    assert_no_em_en_dash(str(v), f"{unit['atomic_unit_id']}.{k}")
                narrator_units.append(unit)
                gold_atomic_rows.append(unit)

        dim_counts = Counter(u["primary_reliability_dimension"] for u in narrator_units if u["weight_eligible"] == 1)
        fam_counts = Counter(u["statement_family"] for u in narrator_units if u["weight_eligible"] == 1)

        g_row = {
            "gold_id": gold_id,
            "group_profile": group_profile,
            "english_name": eng_name,
            "entry_id": eid,
            "shamela_narrator_id": sid,
            "task_b_split": task_b_split,
            "full_name_arabic": full_name_ar,
            "entry_text_verbatim": full_text,
            "v1_3_disposition": v13_disp,
            "v1_3_rank_1_to_12": v13_rk,
            "v1_3_target_span": v13_span,
            "v1_3_context_span": v13_ctx,
            "v1_3_rule_id": v13_rule,
            "v1_4_disposition": v14_disp,
            "v1_4_rank_1_to_12": v14_rk,
            "v1_4_target_span": v14_span,
            "v1_4_context_span": v14_ctx,
            "v1_4_post_tabaqa_qualifiers": v14_post,
            "v1_4_rule_id": v14_rule,
            "taqrib_intro_literal_rank_1_to_12": intro_rk,
            "user_candidate_sheet_rank": user_rk,
            "stage1_baseline_B_intro": linear_baseline_B(intro_rk),
            "stage1_baseline_B_user_sheet": linear_baseline_B(user_rk),
            "dedup_stage2_passages_n": len(deduped),
            "atomic_stage2_units_n": len(narrator_units),
            "weight_eligible_units_n": sum(1 for u in narrator_units if u["weight_eligible"] == 1),
            "eligible_family_counts": json.dumps(dict(fam_counts), ensure_ascii=False),
            "eligible_dimension_counts": json.dumps(dict(dim_counts), ensure_ascii=False),
            "reconciliation_status": recon_status,
            "reconciliation_note": recon_note,
        }
        for k, v in g_row.items():
            assert_no_em_en_dash(str(v), f"G{gold_id:02d}.{k}")
        gold_rows.append(g_row)

    # 2. Build Strictly Train-Only Stratified 120-Narrator Pilot Worksheet (60 Dual-Reviewer IRR)
    rng = random.Random(42)
    train_rows = [r for r in splits_v01.values() if r["split"] == "train" and r["entry_id"] not in gold_eids_in_taqrib]
    by_rank: dict[int, list[dict[str, str]]] = defaultdict(list)
    for r in train_rows:
        by_rank[int(r["task_a_rank_1_to_12"])].append(r)

    quotas = {1: 6, 2: 10, 3: 14, 4: 14, 5: 14, 6: 12, 7: 12, 8: 12, 9: 12, 10: 10, 11: 1, 12: 3}
    selected_pilot: list[dict[str, str]] = []
    for rk in range(1, 13):
        pool = sorted(by_rank[rk], key=lambda x: (-int(x["eligible_primary_passage_count"]), x["entry_id"]))
        with_text = [r for r in pool if int(r["eligible_primary_passage_count"]) >= 2]
        cand = with_text if len(with_text) >= quotas[rk] else pool
        rng.shuffle(cand)
        selected_pilot.extend(cand[: quotas[rk]])

    # Flag 60 stratified narrators for Dual-Reviewer IRR
    selected_pilot.sort(key=lambda x: (int(x["task_a_rank_1_to_12"]), x["entry_id"]))
    irr_eids = {r["entry_id"] for idx, r in enumerate(selected_pilot) if idx % 2 == 0}

    pilot_rows: list[dict[str, Any]] = []
    for r in selected_pilot:
        eid = r["entry_id"]
        sid = r["shamela_narrator_id"]
        r14 = ta_v14[eid]
        raw_p = [p for p in passages_by_eid.get(eid, [])]
        deduped = deduplicate_passages(raw_p)[:6]  # Cap at 6 passages per narrator (~500-600 atomic units)
        seen_sd: set[tuple[str, str, str]] = set()
        for p in deduped:
            clauses = split_clauses_and_resolve_speaker(
                p["text"],
                p["historical_attribution_critic"],
                p["source_work_normalised"],
                p["shamela_group_labels_set"],
            )
            for c_idx, cu in enumerate(clauses, start=1):
                esa = tag_6d_esa_and_dimension(cu["clause_text_verbatim"], p["source_work_normalised"], "")
                dc_status, _ = compute_double_counting_flag(
                    p["extraction_channel"],
                    cu["clause_text_verbatim"],
                    "",
                    esa,
                    seen_sd,
                    cu["speaker_canonical"],
                )
                prow = {
                    "pilot_unit_id": f"PILOT-{eid}-{p['canonical_passage_id']}-U{c_idx:02d}",
                    "entry_id": eid,
                    "shamela_narrator_id": sid,
                    "split": "train",
                    "task_a_v1_4_rank": r14["deterministic_rank_1_to_12"],
                    "irr_dual_review_subset": "yes" if eid in irr_eids else "no",
                    "extraction_channel": p["extraction_channel"],
                    "source_work_normalised": p["source_work_normalised"],
                    "source_citation_exact": p["source_citation_exact"],
                    "speaker_canonical": cu["speaker_canonical"],
                    "reporter_or_transmitter": cu["reporter_or_transmitter"],
                    "attribution_method": cu["attribution_method"],
                    "clause_text_verbatim": cu["clause_text_verbatim"],
                    "proposed_statement_family": esa["statement_family"],
                    "proposed_statement_domain": esa["statement_domain"],
                    "proposed_claim_content": esa["claim_content"],
                    "proposed_wording_force": esa["wording_force"],
                    "proposed_negation_flag": esa["negation_flag"],
                    "proposed_conditional_scope": esa["conditional_scope"],
                    "proposed_primary_dimension": esa["primary_reliability_dimension"],
                    "double_count_status": dc_status,
                    "human_speaker_ok": "",
                    "human_family_override": "",
                    "human_dimension_override": "",
                    "human_scope_override": "",
                    "human_notes": "",
                }
                for k, v in prow.items():
                    assert_no_em_en_dash(str(v), f"{prow['pilot_unit_id']}.{k}")
                pilot_rows.append(prow)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    gold50_csv = OUT_DIR / "GOLD_50_RECONCILED_VALIDATION_SET_V2_0.csv"
    gold50_claims_csv = OUT_DIR / "GOLD_50_ATOMIC_STAGE2_CLAIMS_V2_0.csv"
    gold50_adj_csv = OUT_DIR / "GOLD_50_ADJUDICATION_QUEUE_V2_0.csv"
    pilot_csv = OUT_DIR / "TRAIN_120_STRATIFIED_ESA_PILOT_WORKSHEET_V2_0.csv"

    adj_rows = [
        {
            "gold_id": r["gold_id"],
            "english_name": r["english_name"],
            "entry_id": r["entry_id"],
            "shamela_narrator_id": r["shamela_narrator_id"],
            "v1_4_rank_1_to_12": r["v1_4_rank_1_to_12"],
            "taqrib_intro_literal_rank_1_to_12": r["taqrib_intro_literal_rank_1_to_12"],
            "user_candidate_sheet_rank": r["user_candidate_sheet_rank"],
            "reconciliation_status": r["reconciliation_status"],
            "reconciliation_note": r["reconciliation_note"],
            "v1_4_target_span": r["v1_4_target_span"],
            "v1_4_context_span": r["v1_4_context_span"],
            "human_final_adjudicated_rank": "",
            "human_adjudication_rationale": "",
        }
        for r in gold_rows
        if r["reconciliation_status"]
        in {
            "needs_rank8_vs_rank9_reconciliation",
            "pending_intro_review_r2_vs_r3",
            "pending_intro_review_r3_conditional",
            "fixed_shamela_link_and_r3_review",
            "pending_r11_vs_r12_adjudication",
            "abstain_for_adjudication",
            "fixed_shamela_link_needs_context_adj",
            "external_source_exception",
        }
    ]

    write_csv(gold50_csv, gold_rows, list(gold_rows[0]))
    write_csv(gold50_claims_csv, gold_atomic_rows, list(gold_atomic_rows[0]))
    write_csv(gold50_adj_csv, adj_rows, list(adj_rows[0]))
    write_csv(pilot_csv, pilot_rows, list(pilot_rows[0]))

    # Build Markdown Reconciliation Report
    n_v14_assigned = sum(1 for r in gold_rows if r["v1_4_disposition"] == "assigned_rank")
    n_v13_assigned = sum(1 for r in gold_rows if r["v1_3_disposition"] == "assigned_rank")
    n_r8_r9_diff = sum(1 for r in gold_rows if r["reconciliation_status"] == "needs_rank8_vs_rank9_reconciliation")

    report_lines = [
        "# Gold-50 Reconciled Validation Set & Phase 1 v2 Atomic 6D ESA Report",
        "",
        "**Status:** Phase 1 complete (Gold-50 reconciled + Stage 1/Stage 2 atomic provenance & 6D multidimensional ESA extraction + strictly train-only 120-narrator Pilot Worksheet).",
        "",
        "## 1. Gold-50 Reconciliation Summary",
        f"- Total Gold candidates retained: **{len(gold_rows)}** (`49` in *Taqrib al-Tahdhib*, `1` external non-Taqrib `#49 Amr ibn Shimr` in Shamela4 ID `12587` + al-Ghada'iri *Kitab al-Du'afa'* `1/3/3`).",
        f"- All **50 / 50** linked to canonical `shamela_narrator_id` (fixing Tawus `#37 -> 2980` and Layth ibn Abi Sulaym `#19 -> 5347`).",
        f"- Task A automatic assignment coverage on the 49 Taqrib entries: `v1.3` assigned **{n_v13_assigned} / 49** vs `v1.4` assigned **{n_v14_assigned} / 49** (fixed Ikrimah `#35` false Rank 12 -> Rank 2; promoted unambiguous Rank 2/3/4 entries).",
        f"- Rank 8 vs Rank 9 (`ضعيف` vs `مجهول`) reconciliation items flagged: **{n_r8_r9_diff}** narrators (`#16, #18, #42, #43, #46`). Literal *Taqrib* introduction wording places `ضعيف` at Rank 8 and `مجهول` at Rank 9, while external user candidate sheets place `ضعيف` at Rank 9. Both columns (`taqrib_intro_literal_rank_1_to_12` and `user_candidate_sheet_rank`) are preserved pending final adjudication.",
        "",
        "## 2. Stage 2 Atomic 6D Multidimensional ESA & Double-Counting Summary (Gold-50)",
        f"- Total deduplicated Stage 2 passages across Gold-50: **{sum(r['dedup_stage2_passages_n'] for r in gold_rows)}**",
        f"- Total atomic `Narrator -> Speaker -> Claim` units extracted: **{len(gold_atomic_rows)}**",
        f"- Weight-eligible (non-double-counted) atomic units: **{sum(r['weight_eligible_units_n'] for r in gold_rows)}**",
        "",
        "## 3. Strictly Train-Only Stratified Pilot (`N = 120` Narrators)",
        f"- Pilot narrators selected strictly from `train`: **{len(selected_pilot)}** (`60` flagged `irr_dual_review_subset = yes`)",
        f"- Total atomic review units in Pilot Worksheet: **{len(pilot_rows)}** (`{sum(1 for r in pilot_rows if r['irr_dual_review_subset'] == 'yes')}` in Dual-Reviewer IRR subset)",
    ]
    report_text = "\n".join(report_lines) + "\n"
    assert_no_em_en_dash(report_text, "GOLD_50_RECONCILIATION_REPORT_V2_0.md")
    report_path = OUT_DIR / "GOLD_50_RECONCILIATION_REPORT_V2_0.md"
    report_path.write_text(report_text, encoding="utf-8", newline="\n")

    timestamp = datetime.now(timezone.utc).isoformat()
    inputs = [ENTRY_INDEX_FP, TASK_A_V13_FP, TASK_A_V14_FP, LINKAGE_V03_FP, SPLITS_V01_FP, Path(__file__).resolve()]
    outputs = [gold50_csv, gold50_claims_csv, gold50_adj_csv, pilot_csv, report_path]
    manifest = {
        "package_id": OUT_DIR.name,
        "generated_at_utc": timestamp,
        "counts": {
            "gold_50_total": len(gold_rows),
            "gold_50_taqrib_entries": len(gold_eids_in_taqrib),
            "gold_50_adjudication_queue": len(adj_rows),
            "gold_50_v1_3_assigned": n_v13_assigned,
            "gold_50_v1_4_assigned": n_v14_assigned,
            "gold_50_atomic_units": len(gold_atomic_rows),
            "gold_50_weight_eligible_units": sum(r["weight_eligible_units_n"] for r in gold_rows),
            "pilot_narrators": len(selected_pilot),
            "pilot_irr_narrators": len(irr_eids),
            "pilot_atomic_units": len(pilot_rows),
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
