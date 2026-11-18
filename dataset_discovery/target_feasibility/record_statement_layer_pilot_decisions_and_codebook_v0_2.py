#!/usr/bin/env python3
"""Record user approval of Step 2 pilot audit and generate Codebook v0.2.

Leaves REVIEW_SET.xlsx, pilot review v0.1, and Draft Codebook v0.1 untouched.
Writes a separate versioned package at evaluation_statement_layer_v0_2_2026-11-16/.
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
PILOT_AUDIT_DIR = PIPELINE / "evaluation_statement_layer_pilot_review_v0_1_2026-11-16"
LAYER_V01_DIR = PIPELINE / "evaluation_statement_layer_v0_1_2026-11-16"
OUT_DIR = PIPELINE / "evaluation_statement_layer_v0_2_2026-11-16"


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


def verify_pilot_audit() -> None:
    manifest_path = PILOT_AUDIT_DIR / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    sidecar = (PILOT_AUDIT_DIR / "MANIFEST.sha256").read_text(encoding="ascii").split()[0]
    if digest(manifest_path) != sidecar:
        raise SystemExit("Pilot audit MANIFEST.sha256 mismatch")
    for name, expected in manifest["outputs"].items():
        if digest(PILOT_AUDIT_DIR / name) != expected:
            raise SystemExit(f"Pilot audit hash mismatch for {name}")


def main() -> None:
    if OUT_DIR.exists() and any(OUT_DIR.iterdir()):
        raise SystemExit(f"Refusing to overwrite existing v0.2 directory: {OUT_DIR}")

    verify_pilot_audit()

    pilot_audit = read_csv(PILOT_AUDIT_DIR / "PILOT_16_AI_CRITIQUE_AND_RECOMMENDATIONS_V0_1.csv")
    example_audit = read_csv(PILOT_AUDIT_DIR / "EXAMPLE_PROPOSALS_21_AUDIT_V0_1.csv")
    timestamp = datetime.now(timezone.utc).isoformat()

    pilot_decisions: list[dict[str, Any]] = []
    for row in pilot_audit:
        out = dict(row)
        out["human_choice"] = row["ai_audit_recommended_choice"]
        out["human_correction"] = row["ai_audit_recommended_correction"]
        out["human_note"] = f"User approved audit recommendation ({row['ai_audit_recommended_choice']}). {row['ai_audit_rationale']}"
        out["user_decision_recorded_utc"] = timestamp
        for k, v in out.items():
            assert_no_em_en_dash(str(v), f"{out['case_id']}.{k}")
        pilot_decisions.append(out)

    example_decisions: list[dict[str, Any]] = []
    for row in example_audit:
        out = dict(row)
        out["human_decision"] = row["ai_audit_recommended_disposition"]
        out["human_notes"] = f"User approved audit disposition ({row['ai_audit_recommended_disposition']}). {row['ai_audit_note']}"
        out["user_decision_recorded_utc"] = timestamp
        for k, v in out.items():
            assert_no_em_en_dash(str(v), f"{out['example_id']}.{k}")
        example_decisions.append(out)

    codebook_v02 = "\n".join([
        "# Evaluative Statement Layer: Codebook v0.2 (Pilot-Revised)",
        "",
        "**Date:** 2026-11-16",
        "**Status:** revised from Draft v0.1 after single-reviewer 16-entry pilot (`REVIEW_SET.xlsx`) and 916-case Batch 01+02 consolidation. Separate from the 12 canonical Taqrīb ranks; assigns zero ranks and zero numeric 0-1 scores.",
        "",
        "## 1. Scope and Boundary",
        "",
        "Describe a statement's evaluative family, domain(s), proposition content, presentation mode, wording force, and consensus wording while keeping the twelve canonical Taqrīb ranks, target policy v0.2, and Task B historical inputs strictly separate.",
        "",
        "## 2. Dimensions and Pilot-Approved Rules (v0.1 -> v0.2 Revisions)",
        "",
        "### 2.1 `statement_family`",
        "Allowed values: `praise`, `criticism`, `mixed`, `unknownness`, `status_or_biography`, `non_evaluative_other`, `unresolved`, `not_applicable` (for unrelated substrings).",
        "",
        "### 2.2 `statement_domain` (Revised: Multi-Domain Syntax Enabled)",
        "Allowed single values: `general_reliability`, `memory_precision`, `honesty_veracity`, `fabrication`, `transmission_practice`, `unknownness_or_majhul_status`, `companion_status`, `doctrinal_position`, `jurisprudential_or_scholarly_merit`, `biographical_information`, `other`, `unresolved`, `not_applicable`.",
        "",
        "- **v0.2 Revision (`PILOT-03`, `PILOT-11`, `PILOT-16`):** When a single phrase spans multiple distinct domains (e.g., `ثقة حافظ`, `صدوق حافظ`, `ثقة فقيه عابد`, `جبل الحفظ وإمام الدنيا في فقه الحديث`), encode semicolon-separated domains in order of appearance (e.g., `general_reliability;memory_precision` or `memory_precision;jurisprudential_or_scholarly_merit`) rather than forcing `unresolved`. For route-restricted praise (`لا بأس بحديثه من رواية ابنه...`), use `transmission_practice` (or `general_reliability;transmission_practice`).",
        "",
        "### 2.3 `claim_content`",
        "Allowed values: `general_commendation`, `qualified_commendation`, `superlative_commendation`, `general_criticism`, `accusation_of_lying`, `applied_liar_label`, `fabrication_label`, `specific_transmission_criticism`, `hadith_theft_or_appropriation`, `unknownness_assertion`, `status_assertion`, `biographical_fact`, `mixed_assessment`, `other`, `unresolved`, `not_applicable`.",
        "",
        "### 2.4 `claim_mode` (Revised: Deterministic Precedence Rules)",
        "Allowed values: `direct_statement`, `attributed_individual_judgement`, `reported_or_hedged_claim`, `specific_behavior_or_transmission_observation`, `first_person_knowledge_gap`, `status_or_biographical_statement`, `unresolved`, `not_applicable`.",
        "",
        "- **v0.2 Precedence Rule (`PILOT-10`, `PILOT-12`, `PILOT-15`):**",
        "  1. If a span is explicitly quoted from or attributed to a named critic (`قال ابن عبد البر أجمعوا...`, `قال النسائي: لا أعرفه`, `قال الخليلي يسرق الحديث`), record the named critic in `attribution_text` and prefer `attributed_individual_judgement` (or `reported_or_hedged_claim` when hedging/collective reporting is the primary framing, such as `قال ابن عبد البر أجمعوا...`).",
        "  2. Use `first_person_knowledge_gap` when the first-person compiler voice is unattributed (`لم أقف على اسمها ولا على حالها`).",
        "  3. Capture specific transmission actions (`يسرق الحديث`, `حدث عن أبيه بغير سماع`) in `statement_domain = transmission_practice` and `claim_content` (`hadith_theft_or_appropriation` / `specific_transmission_criticism`) without erasing named attribution.",
        "",
        "### 2.5 `wording_force` (Revised: Multi-Attribute Compounds)",
        "Allowed values: `qualified_limited`, `plain_direct`, `emphatic`, `superlative`, `unresolved`, `not_applicable`.",
        "",
        "- **v0.2 Revision (`PILOT-03`, `PILOT-04`):** Standard multi-attribute compounds (`ثقة ثبت`, `ثقة حافظ`, `ثقة متقن`) take `plain_direct` rather than `unresolved`. Reserve `emphatic` for literal repetition (`ثقة ثقة`) or explicit grammatical intensifiers, and `superlative` for exceptional/superlative formulations (`جبل الحفظ`, `رأس المتقنين`, `أوثق الناس`).",
        "",
        "### 2.6 `consensus_wording`",
        "Allowed values: `none`, `collective_agreement_claimed`, `unanimity_wording_claimed`, `scope_or_referents_unclear`, `unresolved`, `not_applicable`. Records only what the text claims, never verified historical consensus or calibrated confidence.",
        "",
        "## 3. Newly Documented Span and Context Guardrails (Consolidated v0.1)",
        "",
        "- Always enforce non-Arabic-letter boundaries or verify token expansion (`بدري` vs. `العبدري`, `ثبت` vs. `يثبت`/`أثبت`).",
        "- Separate referent checks (`أم المؤمنين`, `الصحابة`, `أحد العشرة`, `صحابي معروف`, `لا تعرف` referring to relatives/chain figures vs. the entry subject).",
        "- Track newly surfaced verbatim forms for future vocabulary collation without enabling rank rules: `صحابية مشهورة`, `وثقه يعقوب ابن سفيان`, governed doctrinal clauses (`رمي بالإرجاء`, `رمي بالقدر`, `يرى القدر`, `رمي بالتشيع`, `رمي بالنصب`), `متروك الحديث عن الزهري`, `فصار كتابه أثبت من حفظه`, `رأس المتقنين`, `من شيوخ بقية المجهولين`, `فلم يشهد بدرا`, `يقال له صحبة والا فمجهول`, and `ثقة ثبت حجة`.",
        "",
    ])
    assert_no_em_en_dash(codebook_v02, "EVALUATIVE_STATEMENT_LAYER_CODEBOOK_V0_2.md")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pilot_out = OUT_DIR / "HUMAN_DECISIONS_PILOT_16_V0_2.csv"
    example_out = OUT_DIR / "HUMAN_DECISIONS_EXAMPLE_PROPOSALS_21_V0_2.csv"
    cb_out = OUT_DIR / "EVALUATIVE_STATEMENT_LAYER_CODEBOOK_V0_2.md"

    write_csv(pilot_out, pilot_decisions, list(pilot_decisions[0]))
    write_csv(example_out, example_decisions, list(example_decisions[0]))
    cb_out.write_text(codebook_v02, encoding="utf-8", newline="\n")

    readme_text = "\n".join([
        "# Evaluative Statement Layer v0.2 (Pilot-Approved Revision)",
        "",
        "Records user approval of the Step 2 pilot audit (`10 Looks right`, `6 Change` across `PILOT-01`..`PILOT-16`) and the 21 draft example audits, and publishes [EVALUATIVE_STATEMENT_LAYER_CODEBOOK_V0_2.md](EVALUATIVE_STATEMENT_LAYER_CODEBOOK_V0_2.md).",
        "",
        "- [HUMAN_DECISIONS_PILOT_16_V0_2.csv](HUMAN_DECISIONS_PILOT_16_V0_2.csv): approved decisions for `PILOT-01`..`PILOT-16` (`REVIEW_SET.xlsx` remains unmodified).",
        "- [HUMAN_DECISIONS_EXAMPLE_PROPOSALS_21_V0_2.csv](HUMAN_DECISIONS_EXAMPLE_PROPOSALS_21_V0_2.csv): approved dispositions for `EX-001`..`EX-021`.",
        "- [EVALUATIVE_STATEMENT_LAYER_CODEBOOK_V0_2.md](EVALUATIVE_STATEMENT_LAYER_CODEBOOK_V0_2.md): revised codebook definitions (multi-domain syntax, `wording_force`, `claim_mode` precedence, and Consolidated v0.1 span guardrails).",
        "- `MANIFEST.json` and `MANIFEST.sha256`: SHA-256 checksums.",
        "",
    ])
    assert_no_em_en_dash(readme_text, "README.md")
    readme_out = OUT_DIR / "README.md"
    readme_out.write_text(readme_text, encoding="utf-8", newline="\n")

    inputs = [
        PILOT_AUDIT_DIR / "PILOT_16_AI_CRITIQUE_AND_RECOMMENDATIONS_V0_1.csv",
        PILOT_AUDIT_DIR / "EXAMPLE_PROPOSALS_21_AUDIT_V0_1.csv",
        PILOT_AUDIT_DIR / "MANIFEST.json",
        LAYER_V01_DIR / "EVALUATIVE_STATEMENT_LAYER_CODEBOOK_DRAFT_V0_1.md",
        Path(__file__).resolve(),
    ]
    outputs = [pilot_out, example_out, cb_out, readme_out]
    manifest = {
        "package_id": OUT_DIR.name,
        "generated_at_utc": timestamp,
        "status": "Step 2 pilot decisions recorded and Codebook v0.2 published; zero canonical ranks or numeric scores assigned",
        "counts": {
            "pilot_decisions_recorded": len(pilot_decisions),
            "pilot_looks_right": sum(r["human_choice"] == "Looks right" for r in pilot_decisions),
            "pilot_change": sum(r["human_choice"] == "Change" for r in pilot_decisions),
            "example_decisions_recorded": len(example_decisions),
            "canonical_ranks_assigned": 0,
            "numeric_scores_assigned": 0,
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
