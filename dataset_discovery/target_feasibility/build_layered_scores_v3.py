#!/usr/bin/env python3
"""Deterministic Layered Score Builder (B, E1, E2) for taqrib-oriented-v2 (v3).

Track R (Representation): deterministic, span-traceable 0-100 scoring with
zero double-counting and explicit missingness:
  - Layer B: Ibn Hajar's Taqrib (3076) Bilgin-grounded 12-rank baseline
  - Layer E1: Within-band Taqrib textual qualifiers strictly outside rank span
  - Layer E2: Tahrir Taqrib al-Tahdhib (8246) editorial verdicts & qualifications

Reads:
  - dataset_discovery/target_feasibility/layer_rules_v3.json
  - data/2_interim/rijal_fyp_modelling_pipeline/bilgin_grounded_targets_v2_2026-11-20/BILGIN_GROUNDED_TAQRIB_TAHRIR_8827_V2.csv
  - data/2_interim/rijal_fyp_modelling_pipeline/taqrib_v2_master_dataset_2026-11-20/TAQRIB_V2_MASTER_NODES_8827.csv

Outputs (default):
  data/2_interim/rijal_fyp_modelling_pipeline/layered_scores_v3_2026-11-21/
    - LAYER_EVIDENCE_LONG_V3.csv
    - LAYERED_SCORES_WIDE_V3.csv
    - LAYERED_SCORES_REPORT_V3.md
    - MANIFEST.json
    - MANIFEST.sha256
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from common.hashing import sha256_text_normalized, to_posix_relative
from common.rank_scale import (
    SCALES,
    check_scale,
    local_band_half_width,
    rank_to_score,
    tahrir_daif_no_itibar_score,
)
from dataset_discovery.target_feasibility.build_bilgin_grounded_targets_v2 import (
    map_tahrir_verdict_to_rank,
)

PIPELINE = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline"
DEFAULT_RULES_PATH = ROOT / "dataset_discovery/target_feasibility/layer_rules_v3.json"
DEFAULT_BILGIN_CSV = PIPELINE / "bilgin_grounded_targets_v2_2026-11-20/BILGIN_GROUNDED_TAQRIB_TAHRIR_8827_V2.csv"
DEFAULT_MASTER_CSV = PIPELINE / "taqrib_v2_master_dataset_2026-11-20/TAQRIB_V2_MASTER_NODES_8827.csv"
DEFAULT_OUT_DIR = PIPELINE / "layered_scores_v3_2026-11-21"

DIACRITICS_RE = re.compile(r"[\u064b-\u065f\u0670\u0640]")
ASCII_BAL_RE = re.compile(r"[\*°]\s*بل\s*[:：]?\s*([^،.\n]+)")
QAWLUHU_QUOTE_RE = re.compile(r"•\s*قوله\s*[:：]?\s*[«\"]([^»\"\n]+)[»\"]")
TABAQA_BOUNDARY_RE = re.compile(r"\bمن\s+(?:(?:كبار|صغار|أوساط|رؤوس|قدماء)\s+)?(?:الطبقة\s+)?(?:الأولى|الثانية|الثالثة|الرابعة|الخامسة|السادسة|السابعة|الثامنة|التاسعة|العاشرة|الحادية\s+عشرة|الثانية\s+عشرة)\b")

# Word/boundary-safe Arabic qualifier patterns for span-grounded E1 detection
E1_QUALIFIER_PATTERNS: dict[str, re.Pattern[str]] = {
    "qual_ikhtalata": re.compile(r"(?:^|\s)(?:اختلط|خلط|خولط|تغير|مخلط)(?=$|\s|[،.])"),
    "qual_yudallis": re.compile(r"(?:^|\s)(?:يدلس|التدليس|تدليس|مدلس)(?=$|\s|[،.])"),
    "qual_yursil": re.compile(r"(?:^|\s)(?:يرسل|الإرسال|إرسال|كثير\s+الإرسال)(?=$|\s|[،.])"),
    "qual_sayyi_hifz": re.compile(r"(?:^|\s)(?:سيء\s+الحفظ|سوء\s+حفظ|رديء\s+الحفظ)(?=$|\s|[،.])"),
    "qual_lin": re.compile(r"(?:^|\s)(?:لين(?:\s+الحديث)?|فيه\s+(?:بعض\s+)?لين|بعض\s+لين|لينه)(?=$|\s|[،.])"),
    "qual_yukhti_yahim": re.compile(r"(?:^|\s)(?:يهم|أوهام|له\s+أوهام|يخطئ|يخطىء|خطأ|أخطأ|غلط|تغلط|أغلاط)(?=$|\s|[،.])"),
    "qual_qalil_hadith": re.compile(r"(?:^|\s)(?:قليل\s+الحديث|مقل)(?=$|\s|[،.])"),
    "qual_rumiya_bidah": re.compile(r"(?:^|\s)(?:رمي\s+ب\S+|رمى\s+ب\S+|تشيع|قدر|إرجاء|نصب|خوارج|تجهم|ابتداع|مرجئ|قدري|ناصبي|رافضي|شيعي|خارجي)(?=$|\s|[،.])"),
}

E1_PRAISE_PATTERNS: dict[str, re.Pattern[str]] = {
    "praise_hafiz": re.compile(r"(?:^|\s)(?:حافظ|الحافظ)(?=$|\s|[،.])"),
    "praise_faqih": re.compile(r"(?:^|\s)(?:فقيه|الفقيه)(?=$|\s|[،.])"),
}

# Patterns indicating Tahrir explicitly mentions or refutes a qualifier
TAHRIR_ABSORBS_OR_REFUTES: dict[str, re.Pattern[str]] = {
    "qual_ikhtalata": re.compile(r"اختلط|اختلاط|خلط|تغير"),
    "qual_yudallis": re.compile(r"يدلس|تدليس|مدلس"),
    "qual_yursil": re.compile(r"يرسل|إرسال|مرسل"),
    "qual_sayyi_hifz": re.compile(r"سيء\s+الحفظ|سوء\s+حفظ|حفظ"),
    "qual_lin": re.compile(r"(?:^|\s)(?:لين|ليّن)"),
    "qual_yukhti_yahim": re.compile(r"يهم|أوهام|يخطئ|خطأ|غلط"),
}


def norm_ar(text: str) -> str:
    return re.sub(r"\s+", " ", DIACRITICS_RE.sub("", text or "")).strip()


def rank_to_score_0_100(rank: int, scale: str = "linear_v1") -> float:
    """Rank -> 0-100 on the chosen scale (see common/rank_scale.py)."""
    return rank_to_score(rank, scale)


# Tahrir intro p. 47: a bare "ضعيف" (no "يعتبر به") is not usable for i'tibar.
TAHRIR_ITIBAR_RE = re.compile(r"(?<!لا )يعتبر به")


def tahrir_marks_itibar(tahrir_commentary: str) -> bool:
    """True when the opening of the Tahrir note grades the man "يعتبر به"."""
    return bool(TAHRIR_ITIBAR_RE.search(norm_ar(tahrir_commentary)[:100]))


def clamp_score(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def fmt_float(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.6f}"


def _extract_eval_region(taqrib_text: str, target_span: str) -> str:
    """Return the evaluative/post-name portion of Taqrib text for praise matching."""
    norm_txt = norm_ar(taqrib_text)
    norm_span = norm_ar(target_span)
    if norm_span and norm_span in norm_txt:
        idx = norm_txt.index(norm_span)
        # Include from target_span onward; also include up to 15 chars before if pre-verdict epithet (e.g. فقيه صدوق)
        pre = norm_txt[max(0, idx - 25):idx]
        if "فقيه" in pre or "حافظ" in pre:
            return norm_txt[max(0, idx - 25):]
        return norm_txt[idx:]
    m = TABAQA_BOUNDARY_RE.search(norm_txt)
    if m:
        return norm_txt[max(0, m.start() - 40):]
    return norm_txt


def _detect_collision_ids(bilgin_rows: list[dict[str, str]]) -> set[str]:
    """Identify the 28 duplicate Tahrir alignment signature collision pairs."""
    by_sig: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    for r in bilgin_rows:
        if r.get("tahrir_matched") == "True":
            sig = (
                r.get("tahrir_part", "").strip(),
                r.get("tahrir_page_num", "").strip(),
                norm_ar(r.get("tahrir_matn_text", ""))[:60],
            )
            if sig[2]:
                by_sig[sig].append(r["entry_id"])
    suspect: set[str] = set()
    for eids in by_sig.values():
        if len(eids) > 1:
            suspect.update(eids)
    return suspect


def _build_evidence_row(
    entry_id: str,
    layer: str,
    source_book_id: str,
    part: str,
    printed_page: str,
    arabic_span: str,
    rule_id: str,
    delta_0_100: float,
    status: str,
    double_count_check: str,
) -> dict[str, str]:
    return {
        "entry_id": entry_id,
        "layer": layer,
        "source_book_id": source_book_id,
        "part": part,
        "printed_page": printed_page,
        "arabic_span": arabic_span,
        "rule_id": rule_id,
        "delta_0_100": fmt_float(delta_0_100),
        "status": status,
        "double_count_check": double_count_check,
    }


def compute_layered_scores(
    bilgin_rows: list[dict[str, str]],
    master_by_id: dict[str, dict[str, str]],
    rules: dict[str, Any],
    *,
    e1_preset: str = "default",
    qawluhu_offset_in_h: float | None = None,
    rank_scale: str | None = None,
) -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, Any]]:
    """Compute Track R layered scores (wide) and span-traceable evidence (long)."""
    scale = check_scale(rank_scale or rules["scale"].get("active", "linear_v1"))
    daif_no_itibar = tahrir_daif_no_itibar_score(scale)

    def r2s(rank: int) -> float:
        return rank_to_score(rank, scale)

    cap_in_h = float(rules["layer_E1"]["cap_in_h"])
    clamp_min = float(rules["scale"]["clamp_min"])
    clamp_max = float(rules["scale"]["clamp_max"])
    qual_weights_h: dict[str, float] = rules["layer_E1"]["qualifier_weights_in_h"]
    praise_weights_h: dict[str, float] = rules["layer_E1"]["praise_weights_in_h"]
    preset_mult = float(rules["layer_E1"]["sensitivity_presets"][e1_preset])

    gold50_overrides: dict[str, dict[str, Any]] = rules["layer_B"]["gold50_rank_overrides"]
    unmappable_ids = set(rules["layer_E2"]["unmappable_entry_ids"])
    bleed_ids = set(rules["layer_E2"]["page_break_bleed_ids"])
    collision_ids = _detect_collision_ids(bilgin_rows)
    dissent_carry_ranks = set(rules["layer_E2"]["dissent_carry_e1_ranks"])
    qawl_off_h = (
        float(rules["layer_E2"]["qawluhu_offset_in_h"])
        if qawluhu_offset_in_h is None
        else float(qawluhu_offset_in_h)
    )
    qawl_max_h = float(rules["layer_E2"]["qawluhu_max_abs_in_h"])
    if abs(qawl_off_h) > qawl_max_h + 1e-9:
        raise ValueError(f"qawluhu_offset_in_h {qawl_off_h} exceeds +/-{qawl_max_h}")

    wide_rows: list[dict[str, str]] = []
    evidence_rows: list[dict[str, str]] = []

    stats: dict[str, Any] = {
        "total_entries": len(bilgin_rows),
        "e1_preset": e1_preset,
        "e1_multiplier": preset_mult,
        "rank_scale": scale,
        "tahrir_daif_no_itibar_count": 0,
        "status_B": Counter(),
        "status_E1": Counter(),
        "status_E2": Counter(),
        "ascii_bal_fixed_count": 0,
        "suspect_alignment_count": 0,
        "band_crossings_E2": 0,
        "delta_E1_by_rank_B": defaultdict(list),
        "delta_E2_by_rank_B": defaultdict(list),
    }

    for brow in bilgin_rows:
        eid = brow["entry_id"]
        mrow = master_by_id[eid]
        taq_text = brow["taqrib_text_verbatim"]
        taq_span = brow["taqrib_target_span"]
        taq_page = brow["printed_page_num_3076"]
        taq_char_len = int(mrow.get("taqrib_char_len") or len(taq_text))
        is_cond_maqbul = brow["taqrib_is_conditional_maqbul"] == "True"

        # ------------------------------------------------------------------
        # Layer B: Baseline
        # ------------------------------------------------------------------
        rank_B_str = brow["taqrib_rank_bilgin_1_to_12"].strip()
        rule_B = brow["taqrib_bilgin_rule_id"].strip()
        span_B = taq_span
        if eid in gold50_overrides and not rank_B_str:
            ov = gold50_overrides[eid]
            rank_B_str = str(ov["rank"])
            rule_B = str(ov["rule_id"])
            span_B = str(ov["span"])

        entry_ev: list[dict[str, str]] = []
        if rank_B_str:
            rank_B = int(rank_B_str)
            score_B: float | None = r2s(rank_B)
            status_B = "observed"
            entry_ev.append(
                _build_evidence_row(
                    eid, "B", "3076", "", taq_page, span_B, rule_B,
                    score_B, "observed", "none",
                )
            )
        else:
            rank_B = None
            score_B = None
            status_B = "abstained"
            entry_ev.append(
                _build_evidence_row(
                    eid, "B", "3076", "", taq_page, span_B or norm_ar(taq_text)[:80],
                    rule_B or "TAQRIB-ABSTAINED", 0.0, "abstained", "none",
                )
            )
        stats["status_B"][status_B] += 1

        # ------------------------------------------------------------------
        # Layer E1: Taqrib Textual Enrichment (No double-counting)
        # ------------------------------------------------------------------
        norm_txt = norm_ar(taq_text)
        norm_span = norm_ar(span_B)
        eval_region = _extract_eval_region(taq_text, span_B)

        e1_applied_rules: list[str] = []
        e1_carried_items: list[tuple[str, float]] = []
        delta_E1 = 0.0

        if taq_char_len == 0:
            status_E1 = "missing"
            score_E1: float | None = score_B
            entry_ev.append(
                _build_evidence_row(
                    eid, "E1", "3076", "", taq_page, "", "E1-MISSING-TEXT",
                    0.0, "missing", "none",
                )
            )
        else:
            candidate_items: list[tuple[str, str, float, bool]] = []
            # Check qualifiers across normalized text
            for qname, pat in E1_QUALIFIER_PATTERNS.items():
                m_txt = pat.search(norm_txt)
                if m_txt:
                    inside = bool(norm_span and pat.search(norm_span))
                    w_h = float(qual_weights_h[qname])
                    candidate_items.append((qname, m_txt.group(0).strip(), w_h, inside))

            # Check positive praise epithets in evaluation region
            for pname, pat in E1_PRAISE_PATTERNS.items():
                m_ev = pat.search(eval_region)
                if m_ev:
                    inside = bool(norm_span and pat.search(norm_span))
                    w_h = float(praise_weights_h[pname])
                    candidate_items.append((pname, m_ev.group(0).strip(), w_h, inside))

            has_counted_outside = False
            running_delta = 0.0
            down_cap = (
                cap_in_h * local_band_half_width(rank_B, -1.0, scale)
                if rank_B is not None
                else 0.0
            )
            up_cap = (
                cap_in_h * local_band_half_width(rank_B, 1.0, scale)
                if rank_B is not None
                else 0.0
            )

            for cname, matched_span, w_h, inside in candidate_items:
                if inside:
                    entry_ev.append(
                        _build_evidence_row(
                            eid, "E1", "3076", "", taq_page, matched_span,
                            f"E1-{cname.upper()}", 0.0, "not_applicable", "inside_rank_span",
                        )
                    )
                    continue

                if score_B is None or rank_B is None:
                    entry_ev.append(
                        _build_evidence_row(
                            eid, "E1", "3076", "", taq_page, matched_span,
                            f"E1-{cname.upper()}", 0.0, "not_applicable", "baseline_abstained",
                        )
                    )
                    continue

                if w_h == 0.0:
                    entry_ev.append(
                        _build_evidence_row(
                            eid, "E1", "3076", "", taq_page, matched_span,
                            f"E1-{cname.upper()}", 0.0, "observed", "descriptive_evidence_only",
                        )
                    )
                    continue

                item_h = local_band_half_width(rank_B, -1.0 if w_h < 0.0 else 1.0, scale)
                raw_delta = w_h * item_h * preset_mult
                # Enforce scale-local ordinal gap + threshold bounds AND [0, 100] limits
                proposed_delta = max(-down_cap, min(up_cap, running_delta + raw_delta))
                proposed_score = clamp_score(score_B + proposed_delta, clamp_min, clamp_max)
                effective_delta = proposed_score - (score_B + running_delta)
                running_delta += effective_delta

                if effective_delta != 0.0:
                    has_counted_outside = True
                    e1_applied_rules.append(f"{cname}:{effective_delta:+.3f}")
                    e1_carried_items.append((cname, effective_delta))

                ev_status = "observed" if effective_delta != 0.0 else "not_applicable"
                entry_ev.append(
                    _build_evidence_row(
                        eid, "E1", "3076", "", taq_page, matched_span,
                        f"E1-{cname.upper()}", effective_delta, ev_status, "none",
                    )
                )

            delta_E1 = running_delta
            if score_B is None:
                score_E1 = None
                status_E1 = "abstained"
            elif has_counted_outside:
                score_E1 = clamp_score(score_B + delta_E1, clamp_min, clamp_max)
                status_E1 = "observed"
            else:
                score_E1 = score_B
                status_E1 = "not_applicable"

        stats["status_E1"][status_E1] += 1
        if rank_B is not None:
            stats["delta_E1_by_rank_B"][rank_B].append(delta_E1)

        # ------------------------------------------------------------------
        # Layer E2: Tahrir Editorial Enrichment
        # ------------------------------------------------------------------
        tah_part = brow["tahrir_part"].strip()
        tah_page = brow["tahrir_page_num"].strip()
        tah_disp = brow["tahrir_disposition"].strip()
        tah_lead = brow["tahrir_verdict_lead"].strip()
        tah_matn = brow["tahrir_matn_text"]
        tah_comm = brow["tahrir_commentary_text"]
        tah_rank_str = brow["tahrir_rank_bilgin_1_to_12"].strip()
        tah_rule = brow["tahrir_bilgin_rule_id"].strip()

        # Fix ASCII * بل: / ° بل: overrides misclassified as agreed_no_bullet
        ascii_fixed = False
        if tah_disp == "agreed_no_bullet":
            m_asc = ASCII_BAL_RE.search(tah_matn)
            if m_asc:
                tah_disp = "dissent_bal"
                tah_lead = norm_ar(m_asc.group(1))
                tah_comm = tah_matn[m_asc.start():].strip()
                tah_rank_str, tah_rule = map_tahrir_verdict_to_rank(tah_lead, tah_comm, eid)
                tah_rule = f"{tah_rule}|ASCII-BULLET-FIXED"
                ascii_fixed = True
                stats["ascii_bal_fixed_count"] += 1

        suspect_reason = ""
        if eid in bleed_ids:
            suspect_reason = "page_break_bleed"
        elif eid in collision_ids:
            suspect_reason = "name_fallback_collision"

        tahrir_confirms_B = False
        rank_E2: int | None = None
        score_E2: float | None = None
        delta_E2: float | None = None

        if suspect_reason:
            status_E2 = "suspect_alignment"
            rank_E2 = rank_B
            score_E2 = score_E1
            delta_E2 = 0.0 if score_E1 is not None else None
            stats["suspect_alignment_count"] += 1
            entry_ev.append(
                _build_evidence_row(
                    eid, "E2", "8246", tah_part, tah_page,
                    norm_ar(tah_comm or tah_matn)[:120],
                    f"TAHRIR-SUSPECT-{suspect_reason.upper()}", 0.0,
                    "suspect_alignment", "none",
                )
            )
        elif tah_disp == "unmatched_in_tahrir" or eid in unmappable_ids or (tah_disp == "dissent_bal" and not tah_rank_str):
            status_E2 = "missing"
            rank_E2 = None
            score_E2 = score_E1
            delta_E2 = 0.0 if score_E1 is not None else None
            entry_ev.append(
                _build_evidence_row(
                    eid, "E2", "8246", tah_part, tah_page,
                    tah_lead or norm_ar(tah_comm)[:100],
                    tah_rule or "TAHRIR-MISSING-OR-UNMAPPABLE", 0.0,
                    "missing", "none",
                )
            )
        elif tah_disp == "agreed_no_bullet":
            if is_cond_maqbul and rank_B is not None and score_E1 is not None:
                # Tahrir intro p. 45: uncommented maqbul resolves to Rank 7 (no E1 carry on band replacement)
                rank_E2 = 7
                score_E2 = clamp_score(r2s(rank_E2), clamp_min, clamp_max)
                delta_E2 = score_E2 - score_E1
                status_E2 = "observed_maqbul_to_r7"
                tahrir_confirms_B = False
                entry_ev.append(
                    _build_evidence_row(
                        eid, "E2", "8246", tah_part, tah_page,
                        "مقبول [Intro p. 45: ضعيف يعتبر به]",
                        rules["layer_E2"]["maqbul_uncommented_rule_id"],
                        delta_E2, "observed_maqbul_to_r7", "band_replaced_maqbul_p45_no_e1_inheritance",
                    )
                )
            elif score_E1 is not None and rank_B is not None:
                rank_E2 = rank_B
                score_E2 = score_E1
                delta_E2 = 0.0
                status_E2 = "observed_agreement"
                tahrir_confirms_B = True
                entry_ev.append(
                    _build_evidence_row(
                        eid, "E2", "8246", tah_part, tah_page,
                        norm_ar(tah_matn)[:120],
                        "TAHRIR-AGREED-AS-TAQRIB", 0.0,
                        "observed_agreement", "none",
                    )
                )
            else:
                status_E2 = "abstained"
                entry_ev.append(
                    _build_evidence_row(
                        eid, "E2", "8246", tah_part, tah_page,
                        norm_ar(tah_matn)[:120],
                        "TAHRIR-AGREED-UNRANKED-TAQRIB", 0.0,
                        "abstained", "none",
                    )
                )
        elif tah_disp == "dissent_bal":
            rank_E2 = int(tah_rank_str)
            base_E2 = r2s(rank_E2)
            if score_E1 is None:
                # Taqrib abstained, Tahrir graded
                score_E2 = base_E2
                delta_E2 = None
                status_E2 = "observed_first_grade"
                entry_ev.append(
                    _build_evidence_row(
                        eid, "E2", "8246", tah_part, tah_page,
                        tah_lead or norm_ar(tah_comm)[:120],
                        tah_rule, score_E2, "observed_first_grade", "none",
                    )
                )
            else:
                norm_comm = norm_ar(tah_comm)
                e1_carry = 0.0
                if rank_E2 in dissent_carry_ranks:
                    down_e2 = cap_in_h * local_band_half_width(rank_E2, -1.0, scale)
                    up_e2 = cap_in_h * local_band_half_width(rank_E2, 1.0, scale)
                    for qname, qdelta in e1_carried_items:
                        abs_pat = TAHRIR_ABSORBS_OR_REFUTES.get(qname)
                        if abs_pat is not None and abs_pat.search(norm_comm):
                            continue
                        e1_carry += qdelta
                    e1_carry = max(-down_e2, min(up_e2, e1_carry))
                score_E2 = clamp_score(base_E2 + e1_carry, clamp_min, clamp_max)
                delta_E2 = score_E2 - score_E1
                status_E2 = "observed_dissent"
                tahrir_confirms_B = (rank_E2 == rank_B)
                dc_flag = (
                    "band_replaced_no_e1_inheritance"
                    if not dissent_carry_ranks
                    else ("band_replaced_e1_carried" if e1_carry != 0.0 else "band_replaced_e1_filtered")
                )
                entry_ev.append(
                    _build_evidence_row(
                        eid, "E2", "8246", tah_part, tah_page,
                        tah_lead or norm_ar(tah_comm)[:120],
                        tah_rule, delta_E2, "observed_dissent", dc_flag,
                    )
                )
        elif tah_disp == "qualification_qawluhu":
            m_q = QAWLUHU_QUOTE_RE.search(tah_comm)
            q_phrase = m_q.group(1).strip() if m_q else norm_ar(tah_comm)[:120]
            if score_E1 is not None and rank_B is not None:
                rank_E2 = rank_B
                band_lo = max(clamp_min, r2s(rank_B) - local_band_half_width(rank_B, -1.0, scale))
                band_hi = min(clamp_max, r2s(rank_B) + local_band_half_width(rank_B, 1.0, scale))
                q_step = local_band_half_width(rank_B, qawl_off_h, scale)
                score_E2 = clamp_score(score_E1 + qawl_off_h * q_step, band_lo, band_hi)
                delta_E2 = score_E2 - score_E1
                status_E2 = "observed_qualification"
                tahrir_confirms_B = True
                entry_ev.append(
                    _build_evidence_row(
                        eid, "E2", "8246", tah_part, tah_page,
                        q_phrase, "TAHRIR-QUALIFICATION-QAWLUHU",
                        delta_E2, "observed_qualification", "none",
                    )
                )
            else:
                status_E2 = "abstained"
                entry_ev.append(
                    _build_evidence_row(
                        eid, "E2", "8246", tah_part, tah_page,
                        q_phrase, "TAHRIR-QUALIFICATION-QAWLUHU-UNRANKED",
                        0.0, "abstained", "none",
                    )
                )
        else:  # other_commentary
            if score_E1 is not None and rank_B is not None:
                rank_E2 = rank_B
                score_E2 = score_E1
                delta_E2 = 0.0
                status_E2 = "observed_no_grade"
                tahrir_confirms_B = True
                entry_ev.append(
                    _build_evidence_row(
                        eid, "E2", "8246", tah_part, tah_page,
                        norm_ar(tah_comm)[:120], "TAHRIR-OTHER-COMMENTARY",
                        0.0, "observed_no_grade", "none",
                    )
                )
            else:
                status_E2 = "abstained"
                entry_ev.append(
                    _build_evidence_row(
                        eid, "E2", "8246", tah_part, tah_page,
                        norm_ar(tah_comm)[:120], "TAHRIR-OTHER-COMMENTARY-UNRANKED",
                        0.0, "abstained", "none",
                    )
                )

        # Tahrir intro p. 47: Tahrir's bare "ضعيف" (agreed by silence or written
        # without "يعتبر به") is below the i'tibar line, unlike Ibn Hajar's rank 8.
        tahrir_itibar = ""
        if rank_E2 == 8 and score_E2 is not None and status_E2 not in {"missing", "suspect_alignment", "abstained"}:
            tahrir_itibar = str(tahrir_marks_itibar(tah_comm))
            if daif_no_itibar is not None and tahrir_itibar == "False":
                shift = daif_no_itibar - r2s(8)
                score_E2 = clamp_score(score_E2 + shift, clamp_min, clamp_max)
                delta_E2 = (score_E2 - score_E1) if score_E1 is not None else delta_E2
                stats["tahrir_daif_no_itibar_count"] += 1
                entry_ev.append(
                    _build_evidence_row(
                        eid, "E2", "8246", tah_part, tah_page,
                        "ضعيف [Intro p. 47: لا يصلح للمتابعات والشواهد]",
                        "TAHRIR-DAIF-NO-ITIBAR-P47", shift,
                        status_E2, "score_shift_daif_no_itibar",
                    )
                )
        stats["status_E2"][status_E2] += 1
        if rank_B is not None and rank_E2 is not None and rank_B != rank_E2 and status_E2 not in {"missing", "suspect_alignment"}:
            stats["band_crossings_E2"] += 1
        if rank_B is not None and delta_E2 is not None and status_E2 not in {"missing", "suspect_alignment"}:
            stats["delta_E2_by_rank_B"][rank_B].append(delta_E2)

        evidence_rows.extend(entry_ev)
        wide_rows.append(
            {
                "entry_id": eid,
                "entry_number_numeric": brow["entry_number_numeric"],
                "split": mrow["split"],
                "score_B": fmt_float(score_B),
                "score_E1": fmt_float(score_E1),
                "score_E2": fmt_float(score_E2),
                "delta_E1": fmt_float(delta_E1),
                "delta_E2": fmt_float(delta_E2),
                "status_B": status_B,
                "status_E1": status_E1,
                "status_E2": status_E2,
                "rank_B": str(rank_B) if rank_B is not None else "",
                "rank_E2": str(rank_E2) if rank_E2 is not None else "",
                "taqrib_is_conditional_maqbul": str(is_cond_maqbul),
                "e1_rules_applied": ";".join(e1_applied_rules),
                "tahrir_disposition": tah_disp,
                "tahrir_confirms_B": str(tahrir_confirms_B),
                "tahrir_r8_itibar": tahrir_itibar,
                "rank_scale": scale,
                "suspect_alignment_reason": suspect_reason,
                "n_evidence_rows": str(len(entry_ev)),
            }
        )

    return wide_rows, evidence_rows, stats


def write_csv_lf(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_report(stats: dict[str, Any], rules: dict[str, Any]) -> str:
    bw_mode = rules["layer_E1"].get("band_width_mode", "local_ordinal_gap")
    lines = [
        "# Layered Score Builder Report (v3: Layers B, E1, E2)",
        "",
        f"- **Total entries:** `{stats['total_entries']:,}`",
        f"- **Rank scale:** `{stats['rank_scale']}` (Tahrir bare ضعيف below i'tibar: `{stats['tahrir_daif_no_itibar_count']}`)",
        f"- **E1 preset:** `{stats['e1_preset']}` (multiplier `{stats['e1_multiplier']}`, band_width_mode `{bw_mode}`)",
        f"- **ASCII `* بل:` / `° بل:` overrides fixed:** `{stats['ascii_bal_fixed_count']}`",
        f"- **Suspect alignments flagged (`E2615/E2616` + collision pairs):** `{stats['suspect_alignment_count']}`",
        f"- **E2 band crossings (`rank_E2 != rank_B`, excluding missing/suspect):** `{stats['band_crossings_E2']:,}`",
        "",
        "> **Caveat on Rank 1 (*Ṣaḥābah*):** Rank 1 (`score_B = 100.0`) is a status category rather than a graded transmission-precision judgement; downstream experiments report results both with and without Rank 1.",
        "",
        "## 1. Status Counts by Layer",
        "",
        "| Layer | Status | Count |",
        "|---|---|---:|",
    ]
    for layer_name, key in [("B", "status_B"), ("E1", "status_E1"), ("E2", "status_E2")]:
        for st, cnt in sorted(stats[key].items()):
            lines.append(f"| {layer_name} | `{st}` | {cnt:,} |")

    lines.extend([
        "",
        "## 2. Distribution of `delta_E1` and `delta_E2` by Baseline Rank (`rank_B`)",
        "",
        "| `rank_B` | `n` | `delta_E1` non-zero | `delta_E1` mean | `delta_E1` min / max | `delta_E2` non-zero | `delta_E2` mean | `delta_E2` min / max |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for rk in range(1, 13):
        d1 = stats["delta_E1_by_rank_B"].get(rk, [])
        d2 = stats["delta_E2_by_rank_B"].get(rk, [])
        n = len(d1)
        nz1 = sum(1 for x in d1 if abs(x) > 1e-9)
        m1 = sum(d1) / n if n else 0.0
        mn1, mx1 = (min(d1), max(d1)) if d1 else (0.0, 0.0)
        nz2 = sum(1 for x in d2 if abs(x) > 1e-9)
        m2 = sum(d2) / len(d2) if d2 else 0.0
        mn2, mx2 = (min(d2), max(d2)) if d2 else (0.0, 0.0)
        lines.append(
            f"| {rk} | {n:,} | {nz1:,} | {m1:+.4f} | {mn1:+.2f} / {mx1:+.2f} | {nz2:,} | {m2:+.4f} | {mn2:+.2f} / {mx2:+.2f} |"
        )
    lines.append("")
    return "\n".join(lines)


def run_build(
    *,
    rules_path: Path = DEFAULT_RULES_PATH,
    bilgin_csv: Path = DEFAULT_BILGIN_CSV,
    master_csv: Path = DEFAULT_MASTER_CSV,
    out_dir: Path = DEFAULT_OUT_DIR,
    e1_preset: str = "default",
    qawluhu_offset_in_h: float | None = None,
    rank_scale: str | None = None,
) -> dict[str, Any]:
    rules = json.loads(rules_path.read_text(encoding="utf-8"))
    with bilgin_csv.open("r", encoding="utf-8-sig", newline="") as f:
        bilgin_rows = list(csv.DictReader(f))
    with master_csv.open("r", encoding="utf-8-sig", newline="") as f:
        master_by_id = {r["entry_id"]: r for r in csv.DictReader(f)}

    wide_rows, evidence_rows, stats = compute_layered_scores(
        bilgin_rows, master_by_id, rules, e1_preset=e1_preset, qawluhu_offset_in_h=qawluhu_offset_in_h,
        rank_scale=rank_scale,
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    wide_path = out_dir / "LAYERED_SCORES_WIDE_V3.csv"
    ev_path = out_dir / "LAYER_EVIDENCE_LONG_V3.csv"
    report_path = out_dir / "LAYERED_SCORES_REPORT_V3.md"

    write_csv_lf(wide_path, list(wide_rows[0].keys()), wide_rows)
    write_csv_lf(ev_path, list(evidence_rows[0].keys()), evidence_rows)
    report_path.write_bytes(build_report(stats, rules).encode("utf-8"))

    output_files = [ev_path, wide_path, report_path]
    manifest = {
        "schema_version": rules["schema_version"],
        "script": to_posix_relative(Path(__file__), ROOT),
        "e1_preset": e1_preset,
        "rank_scale": stats["rank_scale"],
        "rank_scale_scores": {str(k): v for k, v in SCALES[stats["rank_scale"]].items()},
        "tahrir_daif_no_itibar_score": tahrir_daif_no_itibar_score(stats["rank_scale"]),
        "inputs": {
            "layer_rules_v3.json": {
                "path": to_posix_relative(rules_path, ROOT),
                "sha256": sha256_text_normalized(rules_path),
            },
            "bilgin_grounded_targets_v2": {
                "path": to_posix_relative(bilgin_csv, ROOT),
                "sha256": sha256_text_normalized(bilgin_csv),
            },
            "taqrib_v2_master_nodes": {
                "path": to_posix_relative(master_csv, ROOT),
                "sha256": sha256_text_normalized(master_csv),
            },
        },
        "counts": {
            "wide_rows": len(wide_rows),
            "evidence_rows": len(evidence_rows),
            "status_B": dict(stats["status_B"]),
            "status_E1": dict(stats["status_E1"]),
            "status_E2": dict(stats["status_E2"]),
            "ascii_bal_fixed_count": stats["ascii_bal_fixed_count"],
            "suspect_alignment_count": stats["suspect_alignment_count"],
            "band_crossings_E2": stats["band_crossings_E2"],
            "tahrir_daif_no_itibar": stats["tahrir_daif_no_itibar_count"],
        },
        "files": {
            p.name: {"sha256": sha256_text_normalized(p), "bytes": p.stat().st_size}
            for p in output_files
        },
    }
    manifest_path = out_dir / "MANIFEST.json"
    manifest_path.write_bytes((json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    sha_lines = "\n".join(
        f"{sha256_text_normalized(p)}  {p.name}" for p in [*output_files, manifest_path]
    ) + "\n"
    (out_dir / "MANIFEST.sha256").write_bytes(sha_lines.encode("ascii"))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Build deterministic layered scores (B, E1, E2) v3.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--e1-preset", choices=["default", "halved", "doubled", "off"], default="default")
    parser.add_argument(
        "--rank-scale", choices=sorted(SCALES), default=None,
        help="0-100 rank scale (default: layer_rules_v3.json scale.active). linear_v1 reproduces the pre-2026-11-22 scores.",
    )
    args = parser.parse_args()
    manifest = run_build(out_dir=args.out_dir, e1_preset=args.e1_preset, rank_scale=args.rank_scale)
    print(json.dumps(manifest["counts"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
