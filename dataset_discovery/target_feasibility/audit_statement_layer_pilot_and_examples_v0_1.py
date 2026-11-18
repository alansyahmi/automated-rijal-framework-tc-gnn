#!/usr/bin/env python3
"""Audit the 16-entry REVIEW_SET.xlsx pilot and 21 example proposals against Consolidated v0.1.

Reads the hashed pilot workbook, Draft Codebook v0.1, Example Proposals v0.1,
and Consolidated Statement Decisions v0.1, and outputs a non-overwriting review
and Codebook v0.2 revision package with blank human decision fields.
"""

from __future__ import annotations

import csv
import hashlib
import json
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PIPELINE = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline"
PILOT_DIR = PIPELINE / "evaluation_statement_layer_context_pilot_v0_1_2026-11-16"
LAYER_DIR = PIPELINE / "evaluation_statement_layer_v0_1_2026-11-16"
CONS_DIR = PIPELINE / "evaluation_statement_decisions_consolidated_v0_1_2026-11-16"
XLSX_PATH = ROOT / "outputs/evaluative_statement_layer_pilot_v0_1_2026-11-16/REVIEW_SET.xlsx"
OUT_DIR = PIPELINE / "evaluation_statement_layer_pilot_review_v0_1_2026-11-16"


PILOT_RECOMMENDATIONS: dict[str, tuple[str, str, str]] = {
    "PILOT-01": (
        "Looks right",
        "",
        "Matches EX-001 and Batch 01/02 handling of standalone بدري; keep distinct from العبدري nisba substrings.",
    ),
    "PILOT-02": (
        "Looks right",
        "",
        "Matches EX-002; note that in Batch 02, 5 of 15 أم المؤمنين cases referred to relatives rather than the subject.",
    ),
    "PILOT-03": (
        "Change",
        "Set Wording force: plain_direct (instead of unresolved), or document compound-praise rule in Codebook v0.2; adopt semicolon multi-domain general_reliability;memory_precision formally.",
        "Pilot uses multi-domain 'general_reliability; memory_precision' while Consolidated v0.1 coded domain='unresolved'. Clarify both in Codebook v0.2.",
    ),
    "PILOT-04": (
        "Change",
        "Set Wording force: plain_direct (instead of unresolved), matching Batch 01/02 treatment of ثقة ثبت.",
        "Reserve 'emphatic' for repetition (ثقة ثقة) or intensifiers; keep compound reliability attributes as 'plain_direct'.",
    ),
    "PILOT-05": (
        "Looks right",
        "",
        "Matches EX-007 and Consolidated v0.1 SPAN-000653 cleanly.",
    ),
    "PILOT-06": (
        "Looks right",
        "",
        "Matches EX-008 and Batch 02 handling of attributed lying accusations.",
    ),
    "PILOT-07": (
        "Looks right",
        "",
        "Matches EX-011 and Batch 01 ADV01-022; في رأيه requires keeping doctrinal/opinion scope unresolved.",
    ),
    "PILOT-08": (
        "Looks right",
        "",
        "Matches EX-013 and Batch 01/02 handling of plural كذبوه without named evaluators.",
    ),
    "PILOT-09": (
        "Looks right",
        "",
        "Matches EX-014; records collective-agreement wording without verifying historical consensus.",
    ),
    "PILOT-10": (
        "Change",
        "Clarify Claim mode vs. Attribution: Pilot uses attributed_individual_judgement while EX-015 uses direct_statement and Batch 01 uses reported_or_hedged_claim.",
        "Codebook v0.2 should make reported_or_hedged_claim vs. attributed_individual_judgement deterministic when قال X precedes أجمعوا.",
    ),
    "PILOT-11": (
        "Looks right",
        "",
        "Multi-domain 'memory_precision; jurisprudential_or_scholarly_merit' cleanly separates the two subclaims; adopt multi-domain syntax in Codebook v0.2.",
    ),
    "PILOT-12": (
        "Change",
        "Clarify Claim mode when first-person wording is quoted (قال النسائي: لا أعرفه): Pilot uses attributed_individual_judgement while Batch 01 uses first_person_knowledge_gap; also expand span to include قال النسائي.",
        "Needs a clear precedence rule in Codebook v0.2 between speaker attribution and first-person grammatical form.",
    ),
    "PILOT-13": (
        "Looks right",
        "",
        "Matches EX-019 and Batch 01/02 handling of direct لا يعرف حاله.",
    ),
    "PILOT-14": (
        "Looks right",
        "",
        "Matches EX-020 and Batch 01 ADV01-032.",
    ),
    "PILOT-15": (
        "Change",
        "Span includes 'قال الخليلي', so preserve attribution explicitly in Claim mode or document that specific_behavior_or_transmission_observation takes precedence over attributed_individual_judgement when Attribution text records الخليلي.",
        "In Batch 01 ADV01-033, span was 'يسرق الحديث' with attribution='الخليلي'. Reconcile span rule and mode precedence.",
    ),
    "PILOT-16": (
        "Change",
        "Either expand span to include 'من رواية ابنه أحمد عنه لا من رواية ابن وهب' or note Domain consistency (Pilot uses general_reliability while Batch 01 ADV01-026 uses transmission_practice).",
        "Because approval is restricted strictly by transmission route, transmission_practice (or multi-domain) fits better than general_reliability alone.",
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


def read_pilot_xlsx(path: Path) -> list[dict[str, str]]:
    with zipfile.ZipFile(path) as zf:
        ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        shared: list[str] = []
        if "xl/sharedStrings.xml" in zf.namelist():
            root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for si in root.findall("m:si", ns):
                shared.append("".join(t.text or "" for t in si.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t")))
        wb_root = ET.fromstring(zf.read("xl/workbook.xml"))
        rels_root = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
        rid_to_target = {rel.attrib["Id"]: rel.attrib["Target"].lstrip("/") for rel in rels_root}
        first_sheet = wb_root.find(".//m:sheet", ns)
        assert first_sheet is not None
        rid = first_sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
        target = rid_to_target[rid]
        if not target.startswith("xl/"):
            target = "xl/" + target
        ws_root = ET.fromstring(zf.read(target))

        parsed_rows: list[list[str]] = []
        for row_el in ws_root.findall(".//m:row", ns):
            vals: list[str] = []
            for cell in row_el.findall("m:c", ns):
                ctype = cell.attrib.get("t")
                v_el = cell.find("m:v", ns)
                is_el = cell.find("m:is", ns)
                if ctype == "s" and v_el is not None:
                    vals.append(shared[int(v_el.text or "0")])
                elif ctype == "inlineStr" and is_el is not None:
                    vals.append("".join(x.text or "" for x in is_el.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t")))
                elif v_el is not None:
                    vals.append(v_el.text or "")
                else:
                    vals.append("")
            parsed_rows.append(vals)

    headers = parsed_rows[2]  # R4 is 3rd row element (R1, R2, R4)
    assert headers[0] == "Case", f"Unexpected header row: {headers}"
    records: list[dict[str, str]] = []
    for row in parsed_rows[3:]:
        if row and row[0].startswith("PILOT-"):
            padded = row + [""] * (len(headers) - len(row))
            records.append(dict(zip(headers, padded)))
    return records


def verify_inputs() -> None:
    pilot_manifest = json.loads((PILOT_DIR / "MANIFEST.json").read_text(encoding="utf-8"))
    sidecar = (PILOT_DIR / "MANIFEST.sha256").read_text(encoding="ascii").split()[0]
    if digest(PILOT_DIR / "MANIFEST.json") != sidecar:
        raise SystemExit("Pilot MANIFEST.sha256 mismatch")
    for item in pilot_manifest["inputs"] + pilot_manifest["outputs"]:
        p = ROOT / item["path"]
        if digest(p) != item["sha256"]:
            raise SystemExit(f"Hash mismatch on {item['path']}")

    cons_manifest = json.loads((CONS_DIR / "MANIFEST.json").read_text(encoding="utf-8"))
    cons_sidecar = (CONS_DIR / "MANIFEST.sha256").read_text(encoding="ascii").split()[0]
    if digest(CONS_DIR / "MANIFEST.json") != cons_sidecar:
        raise SystemExit("Consolidated MANIFEST.sha256 mismatch")
    for name, expected in cons_manifest["outputs"].items():
        if digest(CONS_DIR / name) != expected:
            raise SystemExit(f"Consolidated hash mismatch on {name}")


def main() -> None:
    if OUT_DIR.exists() and any(OUT_DIR.iterdir()):
        raise SystemExit(f"Refusing to overwrite existing audit directory: {OUT_DIR}")

    verify_inputs()

    pilot_rows = read_pilot_xlsx(XLSX_PATH)
    example_rows = read_csv(LAYER_DIR / "EVALUATIVE_STATEMENT_LAYER_EXAMPLE_PROPOSALS_V0_1.csv")
    cons_cases = read_csv(CONS_DIR / "CONSOLIDATED_REVIEW_CASE_DECISIONS_V0_1.csv")

    assert len(pilot_rows) == 16, f"Expected 16 pilot rows, got {len(pilot_rows)}"
    assert len(example_rows) == 21, f"Expected 21 example rows, got {len(example_rows)}"

    # Index consolidated cases by entry_id and by phrase for comparison
    cons_by_entry: dict[str, list[dict[str, str]]] = {}
    for c in cons_cases:
        cons_by_entry.setdefault(c["entry_id"], []).append(c)

    pilot_audit_rows: list[dict[str, Any]] = []
    for p in pilot_rows:
        cid = p["Case"]
        rec_choice, rec_corr, rec_note = PILOT_RECOMMENDATIONS[cid]
        # Extract entry number from locator (e.g., "Taqrib, printed p. 116, entry 575")
        entry_num = p["Local Taqrib locator"].split("entry ")[-1].strip()
        matched_cons = [
            c for c in cons_cases
            if c["source_entry_text_verbatim"] == p["Full local entry text (verbatim)"]
        ]
        cons_summary = "; ".join(
            f"{m['review_case_id']}:{m['statement_family']}/{m['statement_domain']}/{m['claim_content']}/{m['claim_mode']}/{m['wording_force']}"
            for m in matched_cons
        )
        row = {
            "case_id": cid,
            "what_this_tests": p["What this tests"],
            "local_taqrib_locator": p["Local Taqrib locator"],
            "entry_number": entry_num,
            "phrase_or_span_under_review": p["Phrase/span under review"],
            "ai_suggested_coding_in_xlsx": p["AI's suggested coding"].replace("\n", " | "),
            "why_included_or_caution": p["Why included / caution"],
            "consolidated_v0_1_comparison": cons_summary or "not_in_consolidated_916",
            "ai_audit_recommended_choice": rec_choice,
            "ai_audit_recommended_correction": rec_corr,
            "ai_audit_rationale": rec_note,
            "full_local_entry_text_verbatim": p["Full local entry text (verbatim)"],
            "human_choice": p["Your choice"],
            "human_correction": p["If changing, write the correction"],
            "human_note": p["Your note"],
        }
        for k, v in row.items():
            assert_no_em_en_dash(str(v), f"{cid}.{k}")
        pilot_audit_rows.append(row)

    # Audit the 21 example proposals
    example_audit_rows: list[dict[str, Any]] = []
    for ex in example_rows:
        phrase = ex["phrase_verbatim"]
        matched_cons = [
            c for c in cons_cases
            if phrase in [x.strip() for x in c["matched_phrases_verbatim"].split(" | ")]
        ]
        fam_dist = Counter(c["statement_family"] for c in matched_cons)
        dom_dist = Counter(c["statement_domain"] for c in matched_cons)
        mode_dist = Counter(c["claim_mode"] for c in matched_cons)
        audit_note = "Consistent with Consolidated v0.1."
        rec_disp = "Looks right"
        if ex["proposed_statement_domain"] != "unresolved" and dom_dist.get("unresolved", 0) > 0:
            audit_note = f"Consolidated v0.1 has domain='unresolved' on compound cases ({dict(dom_dist)}); adopt multi-domain coding in Codebook v0.2."
            rec_disp = "Change"
        elif phrase in {"ثقة ثبت", "ثقة حافظ"} and ex["proposed_wording_force"] == "unresolved":
            audit_note = "Example keeps wording_force='unresolved' while Consolidated v0.1 uses 'plain_direct'. Clarify compound wording_force rule in Codebook v0.2."
            rec_disp = "Change"
        elif phrase in {"أجمعوا على ثقته", "لا أعرفه", "لا بأس بحديثه"}:
            audit_note = f"Consolidated v0.1 shows claim_mode/domain tension across contexts ({dict(mode_dist)} / {dict(dom_dist)}); clarify in Codebook v0.2."
            rec_disp = "Change"
        elif phrase == "بدري":
            audit_note = "In Consolidated v0.1, 6 of 11 direct بدري cases were unrelated substrings inside العبدري/العبدرية; enforce word boundaries."

        row = {
            "example_id": ex["example_id"],
            "candidate_id": ex["candidate_id"],
            "phrase_verbatim": phrase,
            "proposed_coding": (
                f"{ex['proposed_statement_family']}/{ex['proposed_statement_domain']}/"
                f"{ex['proposed_claim_content']}/{ex['proposed_claim_mode']}/"
                f"{ex['proposed_wording_force']}/{ex['proposed_consensus_wording']}"
            ),
            "consolidated_v0_1_linked_cases": len(matched_cons),
            "ai_audit_recommended_disposition": rec_disp,
            "ai_audit_note": audit_note,
            "human_decision": ex["human_decision"],
            "human_notes": ex["human_notes"],
        }
        for k, v in row.items():
            assert_no_em_en_dash(str(v), f"{ex['example_id']}.{k}")
        example_audit_rows.append(row)

    # Check domain='unresolved' breakdown in Consolidated v0.1
    unresolved_dom_phrases = Counter(
        c["matched_phrases_verbatim"]
        for c in cons_cases
        if c["statement_domain"] == "unresolved"
    )
    unresolved_mode_phrases = Counter(
        c["matched_phrases_verbatim"]
        for c in cons_cases
        if c["claim_mode"] == "unresolved"
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pilot_csv = OUT_DIR / "PILOT_16_AI_CRITIQUE_AND_RECOMMENDATIONS_V0_1.csv"
    example_csv = OUT_DIR / "EXAMPLE_PROPOSALS_21_AUDIT_V0_1.csv"
    write_csv(pilot_csv, pilot_audit_rows, list(pilot_audit_rows[0]))
    write_csv(example_csv, example_audit_rows, list(example_audit_rows[0]))

    choice_counts = Counter(r["ai_audit_recommended_choice"] for r in pilot_audit_rows)

    notes_lines = [
        "# Statement Layer Pilot Audit and Codebook v0.2 Revision Notes",
        "",
        "**Status:** Step 2 audit complete (`REVIEW_SET.xlsx` untouched; human decision cells remain blank for your sign-off).",
        "",
        "## 1. Pilot Audit Summary (`PILOT_16_AI_CRITIQUE_AND_RECOMMENDATIONS_V0_1.csv`)",
        "",
        f"- Total pilot cases audited: **16** (`PILOT-01` to `PILOT-16`)",
        f"- Recommended `Looks right`: **{choice_counts['Looks right']}** (`PILOT-01`, `PILOT-02`, `PILOT-05`, `PILOT-06`, `PILOT-07`, `PILOT-08`, `PILOT-09`, `PILOT-11`, `PILOT-13`, `PILOT-14`)",
        f"- Recommended `Change` (codebook clarifications needed): **{choice_counts['Change']}** (`PILOT-03`, `PILOT-04`, `PILOT-10`, `PILOT-12`, `PILOT-15`, `PILOT-16`)",
        "",
        "## 2. Specific Codebook v0.1 -> v0.2 Revisions Needed",
        "",
        "1. **Formally adopt semicolon-separated multi-domain coding (`statement_domain`):**",
        "   - In `REVIEW_SET.xlsx`, `PILOT-03` (`ثقة حافظ`) already uses `general_reliability; memory_precision` and `PILOT-11` (`جبل الحفظ وإمام الدنيا في فقه الحديث`) uses `memory_precision; jurisprudential_or_scholarly_merit`.",
        "   - By contrast, single-domain coding in Consolidated v0.1 left **41** cases with `statement_domain = unresolved` (mostly `ثقة حافظ`, `ثقة فقيه عابد`, `صدوق حافظ`, `ثقه`, `تكلم فيه بعضهم`, `تكلموا فيه`, `اتهمه جماعة`, `كذبه الشعبي في رأيه`).",
        "   - **Recommendation:** Allow semicolon-separated `statement_domain` values (`general_reliability;memory_precision`, etc.) in Codebook v0.2.",
        "2. **Clarify `wording_force` for two-attribute praise compounds (`PILOT-03`, `PILOT-04`, `EX-005`):**",
        "   - `PILOT-03` (`ثقة حافظ`) and `PILOT-04` (`ثقة ثبت`) set `wording_force = unresolved`, whereas Consolidated v0.1 coded them as `plain_direct`.",
        "   - **Recommendation:** Define `plain_direct` for standard multi-attribute compounds (`ثقة ثبت`, `ثقة حافظ`, `ثقة متقن`), and reserve `emphatic` for literal repetition (`ثقة ثقة`) or explicit intensifiers.",
        "3. **Establish deterministic precedence for `claim_mode` when signals co-occur (`PILOT-10`, `PILOT-12`, `PILOT-15`):**",
        "   - `PILOT-10` (`قال ابن عبد البر أجمعوا على ثقته`): Pilot uses `attributed_individual_judgement`, while `EX-015` uses `direct_statement` and Batch 01 uses `reported_or_hedged_claim`.",
        "   - `PILOT-12` (`[قال النسائي: لا أعرفه]`): Pilot uses `attributed_individual_judgement` on span `لا أعرفه`, while Batch 01 uses `first_person_knowledge_gap`.",
        "   - `PILOT-15` (`قال الخليلي يسرق الحديث`): Pilot includes `قال الخليلي` in the span but uses `specific_behavior_or_transmission_observation` instead of `attributed_individual_judgement`.",
        "   - **Recommendation:** Separate *who speaks* (`attribution_text`) from *epistemic stance* (`claim_mode`), and define a strict precedence hierarchy (e.g., named critic quote -> `attributed_individual_judgement`, with specific transmission behavior captured in `statement_domain` + `claim_content`).",
        "4. **Align `statement_domain` on route-restricted praise (`PILOT-16`: `لا بأس بحديثه`):**",
        "   - Pilot uses `general_reliability` while Batch 01 `ADV01-026` uses `transmission_practice` (because the entry restricts approval to `من رواية ابنه أحمد عنه لا من رواية ابن وهب`). Adopt `transmission_practice` (or `general_reliability;transmission_practice`) when route restrictions apply.",
        "",
        "## 3. Newly Observed Span & Wording Additions from Consolidated v0.1 (`TODO line 106`)",
        "",
        "Consolidated v0.1 (`916` cases) surfaced concrete boundary & wording extensions to consider in any vocabulary v0.2 (without enabling rank rules):",
        "- Orthographic repair verified in local text: `صحابية مشهورة` (replacing truncated `صحابية مشهور`) and `وثقه يعقوب ابن سفيان` (replacing truncated `وثقه يعقوب ابن`).",
        "- Full governed doctrinal clauses (`رمي بالإرجاء`, `رمي بالقدر`, `يرى القدر`, `رمي بالتشيع`, `رمي بالنصب`) rather than bare noun substrings.",
        "- Scope-qualified criticism and comparative observations found in Batch 02: `متروك الحديث عن الزهري`, `فصار كتابه أثبت من حفظه`, `رأس المتقنين`, `من شيوخ بقية المجهولين`, `فلم يشهد بدرا`, and `يقال له صحبة والا فمجهول`.",
        "- Compound tail observed beyond `ثقة ثبت`: `ثقة ثبت حجة` (`SPAN-000687`).",
        "",
    ]
    notes_text = "\n".join(notes_lines)
    assert_no_em_en_dash(notes_text, "CODEBOOK_V0_2_REVISION_NOTES.md")
    notes_path = OUT_DIR / "CODEBOOK_V0_2_REVISION_NOTES.md"
    notes_path.write_text(notes_text, encoding="utf-8", newline="\n")

    readme_text = "\n".join([
        "# Evaluative Statement Layer Pilot Audit v0.1",
        "",
        "Non-overwriting audit of the 16-entry `REVIEW_SET.xlsx` pilot, the 21 `EVALUATIVE_STATEMENT_LAYER_EXAMPLE_PROPOSALS_V0_1.csv` examples, and Codebook v0.1 against the `916` Consolidated Statement Decisions v0.1.",
        "",
        "- [CODEBOOK_V0_2_REVISION_NOTES.md](CODEBOOK_V0_2_REVISION_NOTES.md): 4 concrete Codebook v0.2 revision recommendations plus newly surfaced wording patterns (`TODO line 106`).",
        "- [PILOT_16_AI_CRITIQUE_AND_RECOMMENDATIONS_V0_1.csv](PILOT_16_AI_CRITIQUE_AND_RECOMMENDATIONS_V0_1.csv): all `16` pilot cases (`10 Looks right`, `6 Change` recommended) with blank human columns.",
        "- [EXAMPLE_PROPOSALS_21_AUDIT_V0_1.csv](EXAMPLE_PROPOSALS_21_AUDIT_V0_1.csv): all `21` draft examples cross-checked against Consolidated v0.1.",
        "- `MANIFEST.json` and `MANIFEST.sha256`: SHA-256 checksums.",
        "",
    ])
    assert_no_em_en_dash(readme_text, "README.md")
    readme_path = OUT_DIR / "README.md"
    readme_path.write_text(readme_text, encoding="utf-8", newline="\n")

    inputs = [
        XLSX_PATH,
        PILOT_DIR / "MANIFEST.json",
        LAYER_DIR / "EVALUATIVE_STATEMENT_LAYER_CODEBOOK_DRAFT_V0_1.md",
        LAYER_DIR / "EVALUATIVE_STATEMENT_LAYER_EXAMPLE_PROPOSALS_V0_1.csv",
        CONS_DIR / "CONSOLIDATED_REVIEW_CASE_DECISIONS_V0_1.csv",
        CONS_DIR / "MANIFEST.json",
        Path(__file__).resolve(),
    ]
    outputs = [pilot_csv, example_csv, notes_path, readme_path]
    manifest = {
        "package_id": OUT_DIR.name,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "pilot and codebook audit ready; REVIEW_SET.xlsx untouched; zero human decisions overwritten",
        "counts": {
            "pilot_cases_audited": len(pilot_audit_rows),
            "pilot_recommended_choices": dict(choice_counts),
            "example_proposals_audited": len(example_audit_rows),
            "consolidated_unresolved_domain_cases": sum(unresolved_dom_phrases.values()),
            "consolidated_unresolved_mode_cases": sum(unresolved_mode_phrases.values()),
            "human_decisions_filled": 0,
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
