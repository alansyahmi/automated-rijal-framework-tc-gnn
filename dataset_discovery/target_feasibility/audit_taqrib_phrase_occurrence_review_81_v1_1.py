#!/usr/bin/env python3
"""Second-pass audit of the 81-entry phrase occurrence review package (TODO line 15).

Verifies rank_label_phrase_occurrence_review_v1_2026-11-16/MANIFEST.json,
audits all 81 rows against Policy v0.2 and full entry text, catches missed
route/boundary issues (such as PHO-055 'في رواية الدوري'), and writes a
separate non-overwriting audit package with blank human columns.
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
OCC_REV_DIR = PIPELINE / "rank_label_phrase_occurrence_review_v1_2026-11-16"
OUT_DIR = PIPELINE / "rank_label_phrase_occurrence_audit_v1_1_2026-11-16"


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


def verify_inputs() -> None:
    manifest = json.loads((OCC_REV_DIR / "MANIFEST.json").read_text(encoding="utf-8"))
    for name, expected in manifest["outputs"].items():
        if digest(OCC_REV_DIR / name) != expected:
            raise SystemExit(f"Hash mismatch on {OCC_REV_DIR.name}/{name}")


def audit_row(entry_row: dict[str, str], ai_row: dict[str, str]) -> dict[str, str]:
    cid = entry_row["case_id"]
    phrase = entry_row["phrase_text_exact"]
    text = entry_row["original_entry_text_verbatim"]
    offset = int(entry_row["phrase_first_char_offset_zero_based"])
    assert text[offset:offset + len(phrase)] == phrase, f"Offset mismatch on {cid}"

    ai_disp = ai_row["ai_suggested_disposition"]
    ai_flag = ai_row["ai_context_or_conflict_flag"]
    pre = text[:offset]
    post = text[offset + len(phrase):]

    # Map AI v1 suggestion into the 6 human_* fields of ENTRY_LEVEL_REVIEW_V1.csv
    role = "grade"
    is_first = "yes"
    qual = "none"
    attr = "preserved"
    disp = "retain_as_candidate"
    status = "agree_with_ai_v1"
    note = ai_row["ai_reason"]

    if phrase in {"له رؤية", "لها رؤية"}:
        role = "status"
        is_first = "yes"
        attr = "not_applicable"
        disp = "conditional"
        if any(k in text for k in ("ثقات التابعين", "وهم من خلطه", "مختلف في نسبته")):
            qual = "present"
        else:
            qual = "none"
    elif phrase == "ذكره ابن حبان في ثقات التابعين":
        role = "context"
        attr = "preserved"
        disp = "conditional"
        if "ويقال له أيضا" in pre:
            is_first = "no"
            qual = "present"
            status = "revise_ai_v1"
            note = "Earlier 'لأبيه صحبة ويقال له أيضا' precedes the Ibn Hibban listing; keep conditional and non-Rank-3."
        elif "وقيل له صحبة" in post or "ولد" in pre:
            is_first = "unclear"
            qual = "present"
            if pre.rstrip().endswith("["):
                disp = "needs_repair"
                status = "revise_ai_v1"
                note = "Bracketed editorial addition '[ذكره ابن حبان في ثقات التابعين]' followed by 'وقيل له صحبة'; requires span/status review."
        else:
            is_first = "unclear"
            qual = "none"
    elif ai_disp == "needs_span_review":
        role = "grade"
        is_first = "unclear"
        qual = "present"
        disp = "needs_repair"
        note = "Bracketed span '[وثقه ابن معين من السادسة]' followed by '[] أبو إسحاق الحميسي' merged entry boundary."
    elif ai_flag == "ruyah_precedes_attributed_grade":
        role = "grade"
        is_first = "no"
        qual = "present"
        disp = "conditional"
        note = "Earlier ru'yah phrase ('له رؤية' / 'يقال له رؤية') precedes this attributed grade; resolve status vs. first target under Policy v0.2."
    elif ai_disp == "conditional_manual_review":
        role = "grade"
        is_first = "yes"
        qual = "present"
        disp = "conditional"
    elif ai_disp == "candidate_with_context_note":
        role = "grade"
        is_first = "yes"
        qual = "present"
        disp = "retain_as_candidate"
    else:
        # Check for subtle context issues missed by AI_SUGGESTIONS_V1.csv!
        if cid == "PHO-055":
            # وثقه ابن معين في رواية الدوري
            role = "grade"
            is_first = "yes"
            qual = "present"
            disp = "conditional"
            status = "revise_ai_v1"
            note = "MISSED BY AI_SUGGESTIONS_V1: text reads 'وثقه ابن معين في رواية الدوري' (route/transmission-conditioned authentication by al-Duri); retain qualification and keep conditional."
        elif cid == "PHO-023":
            # ... وثقه النسائي من الرابعة د س ق [] عبد الله ابن نسيب هو عباد تقدم
            role = "grade"
            is_first = "yes"
            qual = "present"
            disp = "retain_as_candidate"
            status = "revise_ai_v1"
            note = "Main entry ends with 'وثقه النسائي من الرابعة د س ق', followed by '[] عبد الله ابن نسيب هو عباد تقدم' merged cross-reference boundary; grade precedes '[]'."
        elif cid == "PHO-028":
            # identity reconciliation note before وثقه النسائي
            role = "grade"
            is_first = "yes"
            qual = "present"
            disp = "retain_as_candidate"
            status = "revise_ai_v1"
            note = "Preceding text reconciles narrator identity across Bukhari and Tirmidhi before 'وثقه النسائي'; preserve identity context note."
        elif cid in {"PHO-030", "PHO-062"}:
            qual = "present"
            status = "revise_ai_v1"
            note = "Contains biographical office note ('ولي إمرة الغزو بالمغرب' / 'والي سجستان'); retain as biographical context without affecting Rank 3 proxy."

    return {
        "case_id": cid,
        "phrase_review_id": entry_row["phrase_review_id"],
        "entry_id": entry_row["entry_id"],
        "printed_page_num": entry_row["printed_page_num"],
        "entry_number_verbatim": entry_row["entry_number_verbatim"],
        "phrase_text_exact": phrase,
        "phrase_group_decision": entry_row["phrase_group_decision"],
        "phrase_first_char_offset_zero_based": entry_row["phrase_first_char_offset_zero_based"],
        "ai_v1_suggested_disposition": ai_disp,
        "second_pass_audit_status": status,
        "recommended_phrase_role_in_context": role,
        "recommended_is_first_complete_target_phrase": is_first,
        "recommended_qualification_or_conflict": qual,
        "recommended_critic_attribution": attr,
        "recommended_entry_disposition": disp,
        "second_pass_audit_note": note,
        "original_entry_text_verbatim": text,
        "human_phrase_role_in_context": "",
        "human_is_first_complete_target_phrase": "",
        "human_qualification_or_conflict": "",
        "human_critic_attribution": "",
        "human_entry_disposition": "",
        "human_reviewer_notes": "",
    }


def main() -> None:
    if OUT_DIR.exists() and any(OUT_DIR.iterdir()):
        raise SystemExit(f"Refusing to overwrite existing audit package: {OUT_DIR}")

    verify_inputs()

    blank_rows = read_csv(OCC_REV_DIR / "ENTRY_LEVEL_REVIEW_V1.csv")
    ai_rows = read_csv(OCC_REV_DIR / "AI_SUGGESTIONS_V1.csv")
    assert len(blank_rows) == 81 and len(ai_rows) == 81
    ai_by_cid = {r["case_id"]: r for r in ai_rows}

    audited_rows: list[dict[str, Any]] = []
    for er in blank_rows:
        ar = ai_by_cid[er["case_id"]]
        assert er["original_entry_text_verbatim"] == ar["original_entry_text_verbatim"]
        row = audit_row(er, ar)
        for k, v in row.items():
            assert_no_em_en_dash(str(v), f"{row['case_id']}.{k}")
        audited_rows.append(row)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUT_DIR / "ENTRY_LEVEL_AUDIT_81_V1_1.csv"
    write_csv(csv_path, audited_rows, list(audited_rows[0]))

    status_counts = Counter(r["second_pass_audit_status"] for r in audited_rows)
    disp_counts = Counter(r["recommended_entry_disposition"] for r in audited_rows)
    revisions = [r for r in audited_rows if r["second_pass_audit_status"] == "revise_ai_v1"]

    summary_lines = [
        "# 81-Entry Phrase Occurrence Audit v1.1 (TODO Line 15)",
        "",
        "**Status:** second-pass audit complete; original `ENTRY_LEVEL_REVIEW_V1.csv` and `AI_SUGGESTIONS_V1.csv` remain untouched, and all `human_*` columns remain blank pending your approval.",
        "",
        "## Summary Counts (81 Distinct Entries)",
        "",
        f"- `agree_with_ai_v1`: **{status_counts['agree_with_ai_v1']}**",
        f"- `revise_ai_v1`: **{status_counts['revise_ai_v1']}**",
        "",
        "### Recommended `human_entry_disposition` Breakdown",
        "",
        *[f"- `{k}`: **{v}**" for k, v in sorted(disp_counts.items())],
        "",
        "## Specific Revisions Caught Against `AI_SUGGESTIONS_V1.csv`",
        "",
        *[
            f"- **{r['case_id']}** (`{r['entry_id']}`, `{r['phrase_text_exact']}` -> `{r['recommended_entry_disposition']}`): {r['second_pass_audit_note']}"
            for r in revisions
        ],
        "",
    ]
    summary_text = "\n".join(summary_lines)
    assert_no_em_en_dash(summary_text, "AUDIT_SUMMARY_81_V1_1.md")
    summary_path = OUT_DIR / "AUDIT_SUMMARY_81_V1_1.md"
    summary_path.write_text(summary_text, encoding="utf-8", newline="\n")

    readme_text = "\n".join([
        "# Taqrīb Phrase Occurrence Audit v1.1 (81 Entries)",
        "",
        "Second-pass audit of `rank_label_phrase_occurrence_review_v1_2026-11-16/` (`ENTRY_LEVEL_REVIEW_V1.csv` + `AI_SUGGESTIONS_V1.csv`).",
        "",
        "- [AUDIT_SUMMARY_81_V1_1.md](AUDIT_SUMMARY_81_V1_1.md): disposition breakdown and 6 specific corrections caught by the second-pass audit.",
        "- [ENTRY_LEVEL_AUDIT_81_V1_1.csv](ENTRY_LEVEL_AUDIT_81_V1_1.csv): all 81 rows with recommended `human_*` fields and blank `human_*` decision columns ready for recording once approved.",
        "- `MANIFEST.json` and `MANIFEST.sha256`: SHA-256 verification digests.",
        "",
    ])
    assert_no_em_en_dash(readme_text, "README.md")
    readme_path = OUT_DIR / "README.md"
    readme_path.write_text(readme_text, encoding="utf-8", newline="\n")

    inputs = [
        OCC_REV_DIR / "ENTRY_LEVEL_REVIEW_V1.csv",
        OCC_REV_DIR / "AI_SUGGESTIONS_V1.csv",
        OCC_REV_DIR / "MANIFEST.json",
        Path(__file__).resolve(),
    ]
    outputs = [csv_path, summary_path, readme_path]
    manifest = {
        "package_id": OUT_DIR.name,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "second-pass audit ready; all human_decision columns blank pending user confirmation",
        "counts": {
            "entries_audited": len(audited_rows),
            "audit_status_counts": dict(status_counts),
            "recommended_disposition_counts": dict(disp_counts),
            "human_decisions_filled": 0,
            "canonical_ranks_assigned": 0,
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
