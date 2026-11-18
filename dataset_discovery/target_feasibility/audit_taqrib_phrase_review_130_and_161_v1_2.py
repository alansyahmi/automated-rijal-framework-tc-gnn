#!/usr/bin/env python3
"""Prepare a Step 4 audit for the remaining 130 phrase groups and 161 none-found rows (TODO line 16).

Joins rank_label_phrase_review_v1_1_2026-11-16 with empirical findings from
PER_CANDIDATE_PHRASE_REVIEW_COUNTS_V0_1.csv and v1.1 user precedents, leaves
all human decision columns blank, and writes to rank_label_phrase_review_v1_2_audit_2026-11-16/.
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
V11_DIR = PIPELINE / "rank_label_phrase_review_v1_1_2026-11-16"
REP_DIR = PIPELINE / "evaluation_statement_decisions_report_v0_1_2026-11-16"
OUT_DIR = PIPELINE / "rank_label_phrase_review_v1_2_audit_2026-11-16"


SPECIFIC_PHRASE_AUDIT: dict[str, tuple[str, str, str, str]] = {
    # Family 01 special repairs / guards
    "صحابية مشهور": (
        "revise",
        "صحابية مشهورة",
        "1_status_with_entry_guard",
        "AI truncated final ta marbuta; all local entries read 'صحابية مشهورة'. Revise exact span and guard against non-subject contexts.",
    ),
    "الصحابي": (
        "revise",
        "الصحابي الجليل || الصحابي المشهور || الصحابي",
        "1_status_conditional_or_revised_span",
        "E0943 reads 'الصحابي الجليل' and E5053 'الصحابي المشهور'; corpus hits include negation 'غير الصحابي' (SPAN-000447) and ancestor 'جد جده' (SPAN-000459). Keep word-bounded and subject-referent guarded.",
    ),
    "بدري": (
        "conditional",
        "بدري",
        "1_status_word_bounded_only",
        "In Consolidated v0.1, 6 of 11 direct 'بدري' cases were false substrings inside 'العبدري'/'العبدرية'. Must enforce Arabic-letter boundaries and verify Badr referent.",
    ),
    "خادم رسول الله ﷺ خدمه عشر سنين": (
        "revise",
        "خادم رسول الله ﷺ",
        "1_status_biographical_companion",
        "Trim duration clause 'خدمه عشر سنين' or retain full biographical Companion phrase for Anas b. Malik (E0565).",
    ),
    "شهد بدر": (
        "accept",
        "شهد بدر",
        "1_status_with_entry_guard",
        "Verbatim local spelling variant (missing accusative alif vs. 'شهد بدرا') in E3318; enforce word boundary and negation check ('فلم يشهد بدرا').",
    ),
    "له ولأبيه ولجده صحبه": (
        "accept",
        "له ولأبيه ولجده صحبه",
        "1_status_with_entry_guard",
        "Preserve verbatim local spelling ('صحبه' with final ha) in E6823.",
    ),
    "أم المؤمنين": (
        "conditional",
        "أم المؤمنين",
        "1_status_subject_referent_guard_required",
        "In Consolidated v0.1, 5 of 15 direct 'أم المؤمنين' cases referred to a relative (e.g., sister/aunt) rather than the entry subject. Require explicit subject-referent check.",
    ),
    "أحد العشرة": (
        "conditional",
        "أحد العشرة",
        "1_status_subject_referent_guard_required",
        "In Consolidated v0.1, SPAN-000020 ('أخو طلحة أحد العشرة') referred to Talhah rather than the entry subject. Require subject-referent check.",
    ),
    "صحابي معروف": (
        "conditional",
        "صحابي معروف",
        "1_status_subject_referent_guard_required",
        "In Consolidated v0.1, SPAN-003953 ('وأنس صحابي معروف') referred to Anas rather than the unnamed uncle subject. Require subject-referent check.",
    ),

    # Family 05 remaining 10 phrases
    "وثقها العجلي": (
        "accept",
        "وثقها العجلي",
        "3_attributed_proxy_if_first_complete_no_conflict",
        "Clean feminine counterpart to v1.1-accepted 'وثقه العجلي' (E8632); apply identical per-entry guard.",
    ),
    "وثقه يعقوب ابن": (
        "revise",
        "وثقه يعقوب ابن سفيان",
        "3_attributed_proxy_if_first_complete_no_conflict",
        "Truncated mid-name in index; E3643 reads 'وثقه يعقوب ابن سفيان'. Revise span and apply per-entry Rank 3 proxy guard.",
    ),
    "أجمعوا على ثقته": (
        "conditional",
        "أجمعوا على ثقته",
        "conditional_preceded_by_ruyah_and_attributed",
        "In E3265, preceded by 'له رؤية ولأبيه وجده صحبة' and attributed ('قال ابن عبد البر أجمعوا على ثقته'). Mirrors PHO-069/070 ruyah precedence tension.",
    ),
    "مجمع على ثقته": (
        "conditional",
        "مجمع على ثقته",
        "conditional_tabiin_and_ruyah_context",
        "In E4385, preceded by 'ولد على عهد النبي ﷺ قاله مسلم وعده غيره في كبار التابعين'; check Tabi'i/birth context before mapping.",
    ),
    "ثقات التابعين": (
        "conditional",
        "ثقات التابعين",
        "conditional_listing_not_direct_rank3_proxy",
        "Consistent with v1.1 decision on PHR-REV-092 ('ذكره ابن حبان في ثقات التابعين'): listing wording does not automatically inherit direct Rank 3 proxy.",
    ),
    "ذكره ابن حبان في الثقات": (
        "conditional",
        "ذكره ابن حبان في الثقات",
        "conditional_listing_not_direct_rank3_proxy",
        "Consistent with v1.1 decision on PHR-REV-092: Ibn Hibban Thiqat listing requires case-level review (E3649 is also tamyiz).",
    ),
    "ذكره جماعة في ثقات التابعين": (
        "conditional",
        "ذكره جماعة في ثقات التابعين",
        "conditional_listing_not_direct_rank3_proxy",
        "Consistent with v1.1 decision on PHR-REV-092: listing construction plus 'ولد في حياة النبي ﷺ' context.",
    ),
    "من كبار التابعين الثقات": (
        "conditional",
        "من كبار التابعين الثقات",
        "conditional_listing_not_direct_rank3_proxy",
        "Attributed to al-'Ijli in E3382 ('وذكره العجلي من كبار التابعين الثقات'); treat under listing/tabi'i review guard.",
    ),
    "وثقه": (
        "revise",
        "روى عنه النسائي ووثقه",
        "3_attributed_proxy_revise_span_or_word_bound",
        "Bare 'وثقه' omits the named critic ('روى عنه النسائي ووثقه' in E1329) and collides with 'أوثقه'/'وثقها' (14/79 corpus hits). Expand to include critic or keep guarded.",
    ),
    "وقد وثق": (
        "abstain",
        "",
        "exclude_not_first_grade_and_bracketed",
        "In E5214 ('ليس بمشهور [وقد وثق]'), 'ليس بمشهور' is the earlier phrase and '[وقد وثق]' is bracketed editorial addition.",
    ),

    # Family 04 span repairs
    "ضعفه الأزدي من الرابعة ق": (
        "revise",
        "ضعفه الأزدي",
        "8_conditional_attributed_weakness",
        "Trim trailing generation and sigla ('من الرابعة ق'); evaluate under Rank 8 preconditions.",
    ),
    "ضعفه يحيى ابن معين ورمي بالإرجاء من التاسعة مات سنة خمس عشرة ت": (
        "revise",
        "ضعفه يحيى ابن معين",
        "8_conditional_attributed_weakness_with_innovation_note",
        "Trim doctrinal clause, generation, death date, and sigla; keep 'ورمي بالإرجاء' in separate context layer.",
    ),
    "ليّن": (
        "conditional",
        "ليّن",
        "6_or_8_conditional_diacritic_variant",
        "Preserve exact shadda spelling ('ليّن'); check Rank 6/8 preconditions and preceding/following context in E4087.",
    ),

    # Family 06 praise / orthographic / compound
    "ثقه": (
        "revise",
        "ثقه",
        "3_or_2_orthographic_variant_word_bounded_only",
        "Orthographic variant of 'ثقة' (final ha); 79 of 84 raw corpus hits are inside 'وثقه'/'وثقها'/'أوثقه', and 2 of 4 no-hit entries are compounds ('ثقه مقل عابد', 'ثقه عابد'). Enforce word boundary and full-compound span.",
    ),
    "أحد الحفاط": (
        "revise",
        "أحد الحفاط",
        "conditional_memory_scholarship_source_typo",
        "Source typo in Shamela for 'أحد الحفاظ' (E5718 Abu Hatim al-Razi); preserve verbatim spelling and keep distinct from Rank 3 reliability wordings.",
    ),
    "حافظ": (
        "conditional",
        "حافظ",
        "conditional_memory_descriptor_not_unconditional_rank3",
        "Memory/scholarship descriptor: co-occurs with 'اتهموه بسرقة الحديث' (E7591), 'متروك' (SPAN-003299), and negation 'لم يكن بالحافظ'. Never map standalone 'حافظ' to Rank 3.",
    ),
    "أحد الحفاظ": (
        "conditional",
        "أحد الحفاظ",
        "conditional_memory_descriptor_check_context",
        "Scholarship descriptor; E2664 continues 'له غرائب'.",
    ),
    "أحد العلماء الأثبات الفقهاء الكبار": (
        "accept",
        "أحد العلماء الأثبات الفقهاء الكبار",
        "2_strong_praise_candidate_with_entry_guard",
        "Multi-attribute superlative praise aligned with Rank 2's combination-of-praise definition (Sa'id b. al-Musayyib, E2396).",
    ),
    "جبل الحفظ وإمام الدنيا في فقه الحديث": (
        "accept",
        "جبل الحفظ وإمام الدنيا في فقه الحديث",
        "2_strong_praise_candidate_with_entry_guard",
        "Multi-domain superlative praise aligned with Rank 2's combination-of-praise definition (al-Bukhari, E5727).",
    ),
    "ما به بأس": (
        "accept",
        "ما به بأس",
        "4_candidate_with_entry_guard",
        "Exact semantic/syntactic counterpart to Rank 4's 'ليس به بأس' / 'لا بأس به' (E7833).",
    ),

    # Family 07 lying / fabrication / abandonment
    "متهم بالكذب": (
        "accept",
        "متهم بالكذب",
        "11_candidate_with_entry_guard",
        "Direct morphological variant of Rank 11's 'اتهم بالكذب'; retain any trailing innovation notes (e.g., 'ورمي بالرفض' in E5901).",
    ),
    "ليس بأهل أن يروى عنه": (
        "abstain",
        "",
        "exclude_non_standard_historical_rejection",
        "Occurs in tamyiz/historical entries (al-Hajjaj b. Yusuf E1141, Yazid b. Muawiyah E7777); not one of Ibn Hajar's 12-rank examples.",
    ),
    "كذبه الشعبي في رأيه": (
        "abstain",
        "",
        "abstain_scoped_to_opinion_not_hadith_lying",
        "Qualified with 'في رأيه' (E1029) followed by 'ورمي بالرفض وفي حديثه ضعف'; do not collapse into Rank 11/12.",
    ),

    # Family 08 non-grade / vague
    "ثقات الأمراء": (
        "abstain",
        "",
        "exclude_non_grade_political_title",
        "E6937 reads 'من ثقات الأمراء' (trustworthy/capable military commanders), not a hadith reliability grade.",
    ),
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


def verify_package(directory: Path) -> None:
    manifest_path = directory / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    sidecar = (directory / "MANIFEST.sha256").read_text(encoding="ascii").split()[0]
    if digest(manifest_path) != sidecar:
        raise SystemExit(f"MANIFEST.sha256 mismatch in {directory}")
    for name, expected in manifest["outputs"].items():
        if digest(directory / name) != expected:
            raise SystemExit(f"Hash mismatch for {directory.name}/{name}")


def recommend_for_blank_phrase(row: dict[str, str], emp: dict[str, str] | None) -> tuple[str, str, str, str]:
    phrase = row["phrase_text_trimmed_for_grouping"]
    fam = row["construction_family"]
    if phrase in SPECIFIC_PHRASE_AUDIT:
        return SPECIFIC_PHRASE_AUDIT[phrase]

    emp_note = ""
    if emp:
        emp_note = (
            f" Empirical Consolidated v0.1: {emp['direct_selected_cases']} direct cases "
            f"({emp['direct_unrelated_substring']} unrelated_substring, {emp['direct_non_subject_referent_count']} non_subject_referent)."
        )

    if fam == "01_companion_status_direct":
        return (
            "accept",
            phrase,
            "1_status_with_entry_guard",
            f"Direct Companion status wording; require word boundary, subject referent, and no preceding/trailing refutation.{emp_note}",
        )
    if fam == "02_companion_status_disputed_or_ruyah":
        return (
            "conditional",
            phrase,
            "1_status_conditional_or_abstain",
            f"Disputed/hedged Companion or ruyah wording; consistent with v1.1 decision on 'له رؤية'/'لها رؤية'.{emp_note}",
        )
    if fam == "03_unknown_status_ranks_7_9_or_unnamed":
        return (
            "conditional",
            phrase,
            "7_or_9_conditional_pending_evidence",
            f"Unknownness wording requires transmitter-count and lack-of-authentication evidence (Rank 7 vs. Rank 9) plus referent check.{emp_note}",
        )
    if fam == "04_mild_or_attributed_weakness_ranks_6_8":
        if "لين" in phrase:
            return (
                "conditional",
                phrase,
                "6_conditional_pending_corroboration_and_context",
                f"Mild-weakness wording aligned with Rank 6; requires checking little-hadith and no-abandonment conditions.{emp_note}",
            )
        if phrase == "سيء الحفظ":
            return (
                "conditional",
                phrase,
                "5_or_8_conditional_standalone_memory",
                f"Rank 5 lists 'صدوق سيء الحفظ'; standalone 'سيء الحفظ' in E2600 includes 'يتشيع' and lacks 'صدوق'.{emp_note}",
            )
        return (
            "conditional",
            phrase,
            "8_conditional_pending_auth_check",
            f"Weakness wording requires absence of recognized authentication under Rank 8 and preservation of critic attribution.{emp_note}",
        )
    if fam == "06_praise_orthographic_and_compound_ranks_2_3_4":
        return (
            "conditional",
            phrase,
            "3_or_4_or_route_conditioned_check",
            f"Non-canonical praise/middling wording or route-qualified statement; review Rank 3 vs. 4 and exceptions.{emp_note}",
        )
    if fam == "07_lying_fabrication_abandonment_ranks_10_11_12":
        if phrase in {"تركه الدارقطني", "تركوه"}:
            return (
                "conditional",
                phrase,
                "10_conditional_pending_defect_and_auth",
                f"Abandonment wording; Rank 10 requires lack of authentication plus grounding defect (and E7862 also has 'وكذبه ابن معين').{emp_note}",
            )
        if phrase == "يسرق الحديث":
            return (
                "abstain",
                "",
                "abstain_transmission_theft_not_explicit_lying",
                f"Specific transmission-integrity criticism (al-Khalili, E4187); keep distinct from explicit Rank 11/12 lying/fabrication.{emp_note}",
            )
        return (
            "conditional",
            phrase,
            "11_vs_12_boundary_unresolved",
            f"Attributed lying/fabrication wording; Rank 11 (accusation) vs. Rank 12 (applied label) boundary remains unresolved.{emp_note}",
        )
    if fam == "08_general_criticism_innovation_or_non_grade":
        return (
            "abstain",
            "",
            "abstain_vague_or_affiliation_context_only",
            f"Vague criticism or standalone doctrinal/affiliation label without a direct 12-rank mapping.{emp_note}",
        )
    raise SystemExit(f"Unhandled family {fam} for {phrase}")


def audit_none_found(row: dict[str, str]) -> tuple[str, str, str]:
    tags = set(row["audit_tags"].split(";"))
    if "empty_entry_text" in tags:
        return ("abstain", "empty_entry_text_source_gap", "Empty numbered entry ('١٣٠١-'); no Arabic text to evaluate.")
    if "implicit_companion_or_prophetic_relation_cue" in tags:
        return ("conditional", "implicit_companion_prophetic_relation", "Contains 'رسول الله' relation/service cue (e.g., شاعر/سبط/مولى/بنت/ابن عم); candidate for Rank 1 status review without literal 'صحابي'.")
    if "explicit_no_companionship" in tags:
        return ("abstain", "explicit_non_companion_biographical", "Explicitly denies Companion status ('ليست له صحبة' / 'وهم من زعم...' / 'والصواب أنه تابعي') with no grade.")
    if "inline_html_tag" in tags:
        return ("conditional", "unnamed_narrator_with_html_tag_artifact", "Contains inline '<span ...>' HTML inside 'لم يسم' (E8509); treat as unnamed-narrator context note.")
    if "unnamed_narrator_lam_yusamma" in tags:
        return ("conditional", "unnamed_narrator_context_lam_yusamma", "Reports unnamed narrator ('لم يسم' / 'لم تسم'); retain as Rank 7/9 context cue only.")
    if "la_arif_statement" in tags:
        return ("conditional", "knowledge_gap_la_arif_no_narration_or_relative", "States 'لا أعرف له رواية' or unknown mother/grandmother; not a standalone narrator reliability rank.")
    if "tamiz_entry" in tags:
        return ("abstain", "tamiz_disambiguation_no_grade", "Identity-disambiguation ('تمييز') entry with no rank-bearing phrase.")
    if "biographical_eminence_or_scholarship_cue" in tags:
        return ("abstain", "biographical_eminence_not_12_rank_cue", "Biographical/scholarship eminence ('سيد التابعين', 'الحافظ صاحب السنن', 'رأس الطبقة التاسعة') without a 12-rank grade.")
    return ("abstain", "non_grade_biographical_or_crossref", "Biographical, generational, or cross-reference entry with no grade-bearing phrase.")


def main() -> None:
    if OUT_DIR.exists() and any(OUT_DIR.iterdir()):
        raise SystemExit(f"Refusing to overwrite existing audit package: {OUT_DIR}")

    verify_package(V11_DIR)
    verify_package(REP_DIR)

    phr_rows = read_csv(V11_DIR / "PHRASE_REVIEW_WORKSHEET_V1_1.csv")
    nf_rows = read_csv(V11_DIR / "NONE_FOUND_AUDIT_161.csv")
    emp_rows = read_csv(REP_DIR / "PER_CANDIDATE_PHRASE_REVIEW_COUNTS_V0_1.csv")
    emp_by_phrase = {r["phrase_candidate_exact"]: r for r in emp_rows}

    assert len(phr_rows) == 148 and len(nf_rows) == 161

    out_phr_rows: list[dict[str, Any]] = []
    for row in phr_rows:
        out = dict(row)
        if row["human_decision"].strip():
            out["v1_2_audit_scope"] = "already_decided_in_v1_1"
            out["recommended_human_decision"] = row["human_decision"]
            out["recommended_approved_span_exact"] = row["human_approved_span_exact"]
            out["recommended_rank_or_status_decision"] = row["human_rank_or_status_decision"]
            out["recommended_audit_rationale"] = row["human_notes"]
        else:
            emp = emp_by_phrase.get(row["phrase_text_trimmed_for_grouping"])
            rec_dec, rec_span, rec_rank, rec_rat = recommend_for_blank_phrase(row, emp)
            out["v1_2_audit_scope"] = "newly_audited_from_blank_130"
            out["recommended_human_decision"] = rec_dec
            out["recommended_approved_span_exact"] = rec_span
            out["recommended_rank_or_status_decision"] = rec_rank
            out["recommended_audit_rationale"] = rec_rat
        for k, v in out.items():
            assert_no_em_en_dash(str(v), f"{row['review_id']}.{k}")
        out_phr_rows.append(out)

    out_nf_rows: list[dict[str, Any]] = []
    for row in nf_rows:
        rec_dec, rec_cat, rec_rat = audit_none_found(row)
        out = dict(row)
        out["recommended_human_decision"] = rec_dec
        out["recommended_none_found_category"] = rec_cat
        out["recommended_rationale"] = rec_rat
        for k, v in out.items():
            assert_no_em_en_dash(str(v), f"{row['entry_id']}.{k}")
        out_nf_rows.append(out)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    phr_csv = OUT_DIR / "PHRASE_REVIEW_148_AUDIT_V1_2.csv"
    nf_csv = OUT_DIR / "NONE_FOUND_161_AUDIT_V1_2.csv"
    write_csv(phr_csv, out_phr_rows, list(out_phr_rows[0]))
    write_csv(nf_csv, out_nf_rows, list(out_nf_rows[0]))

    new_130 = [r for r in out_phr_rows if r["v1_2_audit_scope"] == "newly_audited_from_blank_130"]
    new_dec_counts = Counter(r["recommended_human_decision"] for r in new_130)
    all_dec_counts = Counter(r["recommended_human_decision"] for r in out_phr_rows)
    nf_dec_counts = Counter(r["recommended_human_decision"] for r in out_nf_rows)
    nf_cat_counts = Counter(r["recommended_none_found_category"] for r in out_nf_rows)

    summary_lines = [
        "# Phrase Review v1.2 Audit Summary: Remaining 130 Groups + 161 None-Found Entries (TODO Line 16)",
        "",
        "**Status:** second-pass audit prepared over `PHRASE_REVIEW_WORKSHEET_V1_1.csv` (`18` already decided + `130` newly audited) and `NONE_FOUND_AUDIT_161.csv` (`161` rows). All `130` blank phrase rows and `161` none-found rows keep `human_*` fields blank pending your approval.",
        "",
        "## 1. Remaining 130 Phrase Groups (`PHRASE_REVIEW_148_AUDIT_V1_2.csv`)",
        "",
        "Recommended dispositions for the **130** newly audited groups (applying v1.1 precedents + Consolidated v0.1 empirical findings):",
        *[f"- `{k}`: **{v}**" for k, v in sorted(new_dec_counts.items())],
        "",
        "Combined **148**-group totals if approved (`18` v1.1 + `130` v1.2):",
        *[f"- `{k}`: **{v}**" for k, v in sorted(all_dec_counts.items())],
        "",
        "### Key Highlights Across the 130 Groups",
        "- **Span repairs (`revise`):** `صحابية مشهور` -> `صحابية مشهورة`; `وثقه يعقوب ابن` -> `وثقه يعقوب ابن سفيان`; `ضعفه الأزدي من الرابعة ق` -> `ضعفه الأزدي`; `ضعفه يحيى ابن معين...` -> `ضعفه يحيى ابن معين`; `الصحابي` -> check `الصحابي الجليل` / `الصحابي المشهور`; `خادم رسول الله ﷺ خدمه عشر سنين` -> trim or keep biographical Rank 1; `ثقه` -> word-bounded variant only (79/84 corpus hits are substrings); `أحد الحفاط` -> flag source typo for `أحد الحفاظ`; `وثقه` -> `روى عنه النسائي ووثقه`.",
        "- **Non-subject referent / word-boundary traps (`conditional`):** `بدري` (6/11 direct Batch 02 hits were `العبدري`/`العبدرية`), `أم المؤمنين` (5/15 direct hits were relatives), `أحد العشرة` (Talhah in `SPAN-000020`), `صحابي معروف` (Anas in `SPAN-003953`).",
        "- **v1.1 Precedents Applied:** `وثقها العجلي` -> `accept` (matching `وثقه العجلي`); `ثقات التابعين`, `ذكره ابن حبان في الثقات`, `ذكره جماعة في ثقات التابعين`, `من كبار التابعين الثقات`, `أجمعوا على ثقته`, `مجمع على ثقته`, and all `13` remaining disputed Companion/`رؤية` phrases -> `conditional`; `وقد وثق` (`ليس بمشهور [وقد وثق]`), `ثقات الأمراء`, `ليس بأهل أن يروى عنه`, `كذبه الشعبي في رأيه`, `يسرق الحديث`, and vague Family 08 phrases -> `abstain`.",
        "- **Evidence-conditioned Ranks 6-12:** `متهم بالكذب` (`accept` Rank 11 candidate with entry guard) and `ما به بأس` (`accept` Rank 4 candidate); all `لين`/`ضعف`/`لا يعرف`/`كذبه ...`/`تركوه` forms stay `conditional` pending Rank 6-12 preconditions.",
        "",
        "## 2. 161 `none_found` Entries (`NONE_FOUND_161_AUDIT_V1_2.csv`)",
        "",
        *[f"- `{k}`: **{v}**" for k, v in sorted(nf_dec_counts.items())],
        "",
        "Category breakdown:",
        *[f"- `{k}`: **{v}**" for k, v in sorted(nf_cat_counts.items())],
        "",
    ]
    summary_text = "\n".join(summary_lines)
    assert_no_em_en_dash(summary_text, "AUDIT_SUMMARY_V1_2.md")
    summary_path = OUT_DIR / "AUDIT_SUMMARY_V1_2.md"
    summary_path.write_text(summary_text, encoding="utf-8", newline="\n")

    readme_text = "\n".join([
        "# Taqrīb Phrase Review Audit v1.2 (130 Remaining Groups + 161 None-Found)",
        "",
        "Prepares recommendations for the `130` blank phrase groups in `PHRASE_REVIEW_WORKSHEET_V1_1.csv` and all `161` rows in `NONE_FOUND_AUDIT_161.csv`, leaving `rank_label_phrase_review_v1_1_2026-11-16/` untouched and keeping human decision columns blank for the 130 + 161 rows.",
        "",
        "- [AUDIT_SUMMARY_V1_2.md](AUDIT_SUMMARY_V1_2.md): summary of dispositions, span repairs, and empirical guards.",
        "- [PHRASE_REVIEW_148_AUDIT_V1_2.csv](PHRASE_REVIEW_148_AUDIT_V1_2.csv): all 148 phrase groups (`18` v1.1 decided + `130` newly audited).",
        "- [NONE_FOUND_161_AUDIT_V1_2.csv](NONE_FOUND_161_AUDIT_V1_2.csv): all 161 `none_found` rows with recommended categories and blank human columns.",
        "- `MANIFEST.json` and `MANIFEST.sha256`: SHA-256 checksums.",
        "",
    ])
    assert_no_em_en_dash(readme_text, "README.md")
    readme_path = OUT_DIR / "README.md"
    readme_path.write_text(readme_text, encoding="utf-8", newline="\n")

    inputs = [
        V11_DIR / "PHRASE_REVIEW_WORKSHEET_V1_1.csv",
        V11_DIR / "NONE_FOUND_AUDIT_161.csv",
        V11_DIR / "MANIFEST.json",
        REP_DIR / "PER_CANDIDATE_PHRASE_REVIEW_COUNTS_V0_1.csv",
        REP_DIR / "MANIFEST.json",
        Path(__file__).resolve(),
    ]
    outputs = [phr_csv, nf_csv, summary_path, readme_path]
    manifest = {
        "package_id": OUT_DIR.name,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "Step 4 audit ready for remaining 130 phrase groups and 161 none-found rows; human decisions blank pending approval",
        "counts": {
            "total_phrase_groups": len(out_phr_rows),
            "already_decided_in_v1_1": 18,
            "newly_audited_blank_groups": len(new_130),
            "newly_audited_recommended_decisions": dict(new_dec_counts),
            "none_found_rows_audited": len(out_nf_rows),
            "none_found_recommended_decisions": dict(nf_dec_counts),
            "canonical_ranks_assigned": 0,
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
