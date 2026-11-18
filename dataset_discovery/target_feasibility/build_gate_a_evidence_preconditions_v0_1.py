#!/usr/bin/env python3
"""Build Gate A Evidence Preconditions Registry v0.1 for Ranks 1-12 (TODO line 29).

Encodes Ibn Hajar's source-defined category preconditions (e.g. corroboration for
Rank 6; transmitter count and lack of authentication for Ranks 7 & 9; authentication
and weakness evidence for Ranks 8 & 10; accusation vs. applied label for Ranks 11 & 12;
memory/error/innovation context for Rank 5), quantifies how many entries in Gate A
Complete-Span Census v0.2 touch each precondition-sensitive construction, and keeps
all rules disabled pending Gate B evaluation.
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
SOURCE_ANCHORS = PIPELINE / "rank_vocabulary_candidate_inventory_v0_1_2026-11-16/SOURCE_RANK_ANCHORS_V0_1.csv"
CENSUS_V02 = PIPELINE / "gate_a_complete_span_census_v0_2_2026-11-17/GATE_A_ENTRY_COMPLETE_SPAN_CENSUS_V0_2.csv"
OUT_DIR = PIPELINE / "gate_a_evidence_preconditions_v0_1_2026-11-17"

DIACRITICS_RE = re.compile(r"[\u064b-\u065f\u0670\u0640]")

RANK_PRECONDITIONS = [
    {
        "rank": "1",
        "category_label": "Companionship status (الصحابة)",
        "precondition_class": "status_and_subject_referent",
        "required_evidence": "Subject-level Companion status (e.g. صحابي, بدري); keep separate from ordinary reliability grades and exclude disputed رؤية or non-subject relatives.",
        "abstention_or_context_triggers": "مختلف في صحبته | قيل له صحبة | له رؤية | unnamed relative or father | bracketed insertion",
        "text_alone_sufficient": "only_when_unqualified_subject_status",
        "rule_activation_allowed": "false",
    },
    {
        "rank": "2",
        "category_label": "Highest praise / repetition / superlative",
        "precondition_class": "complete_compound_construction",
        "required_evidence": "Full combined praise or superlative span (أوثق الناس, ثقة ثقة, ثقة حافظ, ثقة ثبت); do not reduce inner ثقة to Rank 3.",
        "abstention_or_context_triggers": "negation | critic conflict | later weakness/ikhtilat qualifier",
        "text_alone_sufficient": "complete_span_with_negation_guard",
        "rule_activation_allowed": "false",
    },
    {
        "rank": "3",
        "category_label": "Single commendatory attribute (ثقة, متقن, ثبت, عدل)",
        "precondition_class": "standalone_or_guarded_attributed",
        "required_evidence": "Unqualified standalone attribute, or guarded single-critic وثقه without contradicting weakness clause.",
        "abstention_or_context_triggers": "combined Rank 2 praise | ثقة + memory/error/innovation Rank 5 qualifier | conflicting critics | [وقد وثق] | non-grade ثقات",
        "text_alone_sufficient": "only_when_standalone_and_unqualified",
        "rule_activation_allowed": "false",
    },
    {
        "rank": "4",
        "category_label": "Lower praise below Rank 3 (صدوق, لا بأس به, ليس به بأس)",
        "precondition_class": "unqualified_lower_praise",
        "required_evidence": "Complete wording preserving absence of Rank 5 memory, error, or innovation qualifiers.",
        "abstention_or_context_triggers": "صدوق + يهم/يخطئ/سيء الحفظ/له أوهام/رمي ببدعة | later اختلط/تدليس notes",
        "text_alone_sufficient": "only_when_unqualified",
        "rule_activation_allowed": "false",
    },
    {
        "rank": "5",
        "category_label": "Qualifiedصدوق / memory error / late change / innovation",
        "precondition_class": "attached_qualifier_and_innovation_context",
        "required_evidence": "Explicit memory/error/ikhtilat wording (سيء الحفظ, يهم, له أوهام, تغير بأخرة) OR innovation term with heresy type and advocacy (داعية vs غير داعية) context.",
        "abstention_or_context_triggers": "bare innovation term without advocacy/reliability frame | later book-specific confusion (خلط في غيره)",
        "text_alone_sufficient": "requires_full_qualifier_clause",
        "rule_activation_allowed": "false",
    },
    {
        "rank": "6",
        "category_label": "Conditional acceptability (مقبول vs فلين الحديث)",
        "precondition_class": "external_corroboration_dependent",
        "required_evidence": "Word مقبول/مقبولة requires external corroboration (متابعة) across isnad chains; absent corroboration, Ibn Hajar's definition maps to لين الحديث.",
        "abstention_or_context_triggers": "no_graph_or_chain_corroboration_evidence_in_Taqrib_text_alone",
        "text_alone_sufficient": "no_requires_external_corroboration",
        "rule_activation_allowed": "false",
    },
    {
        "rank": "7",
        "category_label": "Masked / status unknown (>1 transmitter: مستور, مجهول الحال)",
        "precondition_class": "transmitter_count_gt1_and_no_tawthiq",
        "required_evidence": "More than one transmitter narrating from the person AND absence of recognized authentication.",
        "abstention_or_context_triggers": "single transmitter (Rank 9) | presence of recognized authentication | Ibn Hibban only mention",
        "text_alone_sufficient": "no_requires_transmitter_count_and_absence_check",
        "rule_activation_allowed": "false",
    },
    {
        "rank": "8",
        "category_label": "Unqualified weakness (ضعيف)",
        "precondition_class": "absence_of_tawthiq_plus_expressed_weakness",
        "required_evidence": "Expressed weakness (ضعيف / ضعف) combined with absence of recognized authentication; resolve attributed critic conflicts before assigning.",
        "abstention_or_context_triggers": "conflicting authentication (وثقه X وضعفه Y) | severity elevating to Rank 10",
        "text_alone_sufficient": "conditional_check_absence_of_tawthiq",
        "rule_activation_allowed": "false",
    },
    {
        "rank": "9",
        "category_label": "Unknown entity (مجهول)",
        "precondition_class": "transmitter_count_eq1_and_no_tawthiq",
        "required_evidence": "Only one known transmitter AND absence of recognized authentication.",
        "abstention_or_context_triggers": "more than one transmitter (Rank 7) | لا يعرف اسمه without named narrator identification",
        "text_alone_sufficient": "no_requires_transmitter_count_eq1_and_absence_check",
        "rule_activation_allowed": "false",
    },
    {
        "rank": "10",
        "category_label": "Abandoned / severe defect (متروك, متروك الحديث, واهي الحديث, ساقط)",
        "precondition_class": "no_tawthiq_plus_expressed_defect",
        "required_evidence": "Absence of authentication PLUS an expressed defect grounding abandonment/severe weakness (and distinguish edition variant بقدح vs بقادح).",
        "abstention_or_context_triggers": "present authentication overriding defect | ambiguous defect clause",
        "text_alone_sufficient": "conditional_check_defect_and_no_tawthiq",
        "rule_activation_allowed": "false",
    },
    {
        "rank": "11",
        "category_label": "Accused of lying (من اتهم بالكذب, متهم بالكذب/بالوضع)",
        "precondition_class": "accusation_not_applied_fabrication",
        "required_evidence": "Explicit accusation phrasing (اتهم بالكذب / متهم بالكذب / رمي بالكذب/بالوضع), strictly separated from applied fabrication labels.",
        "abstention_or_context_triggers": "non-hadith accusation | ambiguous hearsay without critic attribution",
        "text_alone_sufficient": "requires_accusation_marker",
        "rule_activation_allowed": "false",
    },
    {
        "rank": "12",
        "category_label": "Applied lying / fabrication label (كذاب, وضاع)",
        "precondition_class": "applied_lying_or_fabrication_label",
        "required_evidence": "Direct applied lying/fabrication term (كذاب, وضاع, يضع الحديث, يكذب); keep distinct from Rank 11 accusation and non-hadith disputes (كذبه في رأيه).",
        "abstention_or_context_triggers": "accusation-only phrasing (Rank 11) | non-hadith dispute",
        "text_alone_sufficient": "requires_applied_label_check",
        "rule_activation_allowed": "false",
    },
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


def main() -> None:
    if OUT_DIR.exists() and any(OUT_DIR.iterdir()):
        raise SystemExit(f"Refusing to overwrite existing precondition package: {OUT_DIR}")

    census = read_csv(CENSUS_V02)
    assert len(census) == 8827
    anchors = read_csv(SOURCE_ANCHORS)
    anchor_counts = Counter(r["rank"] for r in anchors)

    exposure_checks = [
        ("EXP-R1_COMPANION_DISPUTED", "1", "Disputed companionship / رؤية / مختلف في صحبته", lambda s: any(k in s for k in ("مختلف في صحبته", "رؤية", "يقال له صحبة"))),
        ("EXP-R2_COMPOUND_PRAISE", "2", "Superlative or repeated/combined praise (ثقة حافظ, ثقة ثبت, ثقة ثقة, أوثق الناس)", lambda s: any(k in s for k in ("أوثق", "ثقة ثقة", "ثقة حافظ", "ثقة ثبت"))),
        ("EXP-R3_STANDALONE_THIQAH", "3", "Exact standalone ثقة / متقن / ثبت / عدل", lambda s: DIACRITICS_RE.sub("", s).strip() in {"ثقة", "متقن", "ثبت", "عدل"}),
        ("EXP-R3_ATTRIBUTED_WATHAQA", "3", "Attributed critic authentication (وثقه ...)", lambda s: "وثق" in s),
        ("EXP-R4_LOWER_PRAISE", "4", "Exact صدوق / لا بأس به / ليس به بأس / ما به بأس", lambda s: DIACRITICS_RE.sub("", s).strip() in {"صدوق", "لا بأس به", "ليس به بأس", "ما به بأس"}),
        ("EXP-R5_QUALIFIED_OR_INNOVATION", "5", "Memory/error/ikhtilat/innovation qualifiers (يهم, يخطىء, سيء الحفظ, أوهام, اختلط, التشيع, القدر, النصب, الإرجاء, التجهم)", lambda s: any(k in s for k in ("يهم", "يخط", "سيء الحفظ", "أوهام", "اختلط", "تغير", "تشيع", "قدر", "نصب", "إرجاء", "تجهم"))),
        ("EXP-R6_MAQBUL_CORROBORATION", "6", "Rank 6 corroboration-dependent (مقبول / مقبولة)", lambda s: "مقبول" in s),
        ("EXP-R7_MASTUR_GT1", "7", "Rank 7 transmitter-count + no-auth (مستور / مجهول الحال)", lambda s: "مستور" in s or "مجهول الحال" in s),
        ("EXP-R8_DAIF_NO_TAWTHIQ", "8", "Rank 8 weakness requiring no-authentication check (ضعيف / ضعفه)", lambda s: "ضعيف" in s or "ضعفه" in s),
        ("EXP-R9_MAJHUL_EQ1", "9", "Rank 9 single-transmitter + no-auth (مجهول without الحال)", lambda s: "مجهول" in s and "مجهول الحال" not in s),
        ("EXP-R10_MATRUK_DEFECT", "10", "Rank 10 abandonment/defect (متروك, واهي, ساقط, هالك)", lambda s: any(k in s for k in ("متروك", "واه", "ساقط", "هالك", "بقدح", "بقادح"))),
        ("EXP-R11_ACCUSATION", "11", "Rank 11 accusation of lying/fabrication (متهم, اتهم, رمي ب)", lambda s: any(k in s for k in ("متهم", "اتهم", "رمي بالوضع", "رمي بالكذب", "رموه بالوضع"))),
        ("EXP-R12_APPLIED_LYING", "12", "Rank 12 applied lying/fabrication (كذاب, وضاع, يضع, يكذب, كذبوه)", lambda s: any(k in s for k in ("كذاب", "وضاع", "يضع", "يكذب", "كذبوه", "يسرق الحديث"))),
    ]

    exposure_rows: list[dict[str, Any]] = []
    for exp_id, rank, desc, pred in exposure_checks:
        matched = [r for r in census if r["first_complete_target_span_exact"] and pred(r["first_complete_target_span_exact"])]
        exposure_rows.append({
            "exposure_id": exp_id,
            "source_rank": rank,
            "construction_scope": desc,
            "census_v0_2_entry_count": len(matched),
            "census_v0_2_pct_of_8827": f"{len(matched) / len(census) * 100:.2f}%",
            "example_spans": " | ".join(list(dict.fromkeys(r["first_complete_target_span_exact"] for r in matched))[:3]),
        })

    for row in RANK_PRECONDITIONS:
        row["source_anchor_count"] = str(anchor_counts.get(row["rank"], 0))
        row["human_approval_status"] = ""

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    precond_csv = OUT_DIR / "RANK_EVIDENCE_PRECONDITIONS_V0_1.csv"
    exp_csv = OUT_DIR / "CENSUS_PRECONDITION_EXPOSURE_V0_1.csv"
    write_csv(precond_csv, RANK_PRECONDITIONS, list(RANK_PRECONDITIONS[0]))
    write_csv(exp_csv, exposure_rows, list(exposure_rows[0]))

    report_lines = [
        "# Gate A Source-Defined Evidence Preconditions & Exposure Report v0.1 (TODO Line 29)",
        "",
        "**Status:** source-defined preconditions encoded for all `12` Ibn Ḥajar ranks alongside empirical exposure counts across the `8,827`-entry Gate A Complete-Span Census (`v0.2`). All `rule_activation_allowed` flags remain `false`, zero canonical ranks are assigned, and zero rules are enabled.",
        "",
        "## Corpus Exposure to Precondition-Sensitive Constructions (`v0.2` Census)",
    ]
    for e in exposure_rows:
        report_lines.append(
            f"- **Rank {e['source_rank']}** (`{e['exposure_id']}`): **{e['census_v0_2_entry_count']}** entries (`{e['census_v0_2_pct_of_8827']}`) | {e['construction_scope']}"
        )
    report_lines.extend([
        "",
        "## Gate A Operational Consequence",
        "- **`مقبول` / `مقبولة` (`Rank 6`):** absent external isnād corroboration inside standalone *Taqrīb* prose, direct production assignment must abstain or preserve explicit corroboration-conditional status.",
        "- **`مستور` / `مجهول الحال` (`Rank 7`) vs. `مجهول` (`Rank 9`):** require transmitter-count (`>1` vs. `1`) plus absence of recognized authentication.",
        "- **`ضعيف` (`Rank 8`) & `متروك`/`ساقط` (`Rank 10`):** require absence of overriding authentication (plus expressed defect for Rank 10).",
        "- **`اتهم/متهم` (`Rank 11`) vs. `كذاب/وضاع` (`Rank 12`):** must stay strictly separated between accusation and applied label.",
        "",
    ])
    report_text = "\n".join(report_lines)
    assert_no_em_en_dash(report_text, "PRECONDITION_REPORT_V0_1.md")
    report_path = OUT_DIR / "PRECONDITION_REPORT_V0_1.md"
    report_path.write_text(report_text, encoding="utf-8", newline="\n")

    for row in RANK_PRECONDITIONS + exposure_rows:
        for k, v in row.items():
            assert_no_em_en_dash(str(v), f"{k}")

    timestamp = datetime.now(timezone.utc).isoformat()
    inputs = [SOURCE_ANCHORS, CENSUS_V02, Path(__file__).resolve()]
    outputs = [precond_csv, exp_csv, report_path]
    manifest = {
        "package_id": OUT_DIR.name,
        "generated_at_utc": timestamp,
        "counts": {
            "ranks_documented": len(RANK_PRECONDITIONS),
            "exposure_checks_computed": len(exposure_rows),
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
