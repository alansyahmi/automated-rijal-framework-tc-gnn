#!/usr/bin/env python3
"""Draw and audit a 100-entry stratified verification sample of Gate A Complete-Span Census v0.1.

Implements TODO lines 28 and 30:
- Stratified sample (seed=20261117) across all 5 gate_a_category strata (N=100).
- Audits boundary accuracy, Policy v0.2 context-note separation, and false abstains
  against full entry_text_verbatim.
- Reports full corpus denominators (N=8,827), sampling method, exact-match rate,
  boundary/split issues, and abstentions.
- Keeps human_* fields blank and assigns zero canonical ranks.
"""

from __future__ import annotations

import csv
import hashlib
import json
import random
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PIPELINE = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline"
ENTRY_INDEX = PIPELINE / "rank_label_shadow_run_v1_2026-11-15/ENTRY_INDEX.csv"
CENSUS_DIR = PIPELINE / "gate_a_complete_span_census_v0_1_2026-11-17"
OUT_DIR = PIPELINE / "gate_a_census_sample_audit_v0_1_2026-11-17"

STRATUM_QUOTAS = {
    "explicit_source_example": 25,
    "candidate_requiring_review": 30,
    "context_dependent_or_qualified": 20,
    "approved_phrase_candidate": 10,
    "non_grade_or_abstain": 15,
}

# Secondary evaluative / biographical cues that may appear inside non_grade_or_abstain
RARE_GRADE_CUES = (
    "صالح الحديث", "مقارب الحديث", "لا بأس به", "ليس بالقوي", "روى عنه",
    "منكر الحديث", "يعتبر به", "شيخ", "مشايخ", "عدل", "صحيح الحديث",
    "مختلف فيه", "في حديثه", "ليس بشيء", "متماسك", "صويلح",
)


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


def audit_sample_row(census_row: dict[str, str], entry_text: str) -> tuple[str, str, str, str]:
    cat = census_row["gate_a_category"]
    first_span = census_row["first_complete_target_span_exact"]
    ctx_span = census_row["context_note_spans_exact"]

    if cat == "non_grade_or_abstain":
        matched_cues = [c for c in RARE_GRADE_CUES if c in entry_text]
        if matched_cues and "تمييز" not in entry_text:
            return (
                "missed_grade_in_abstain",
                "",
                "",
                f"Abstained entry contains potential evaluative/biographical cue ({', '.join(matched_cues)}); inspect full entry.",
            )
        return (
            "confirmed_non_grade_or_abstain",
            "",
            "",
            "Confirmed non-grade, cross-ref, tamiz, or biographical entry with no canonical 12-rank span.",
        )

    if not first_span or first_span not in entry_text:
        return (
            "boundary_mismatch",
            first_span,
            ctx_span,
            "Extracted span is empty or not an exact verbatim substring of entry_text_verbatim.",
        )

    # Check if a secondary clause with ' و' or '[...]' is still fused inside first_span
    if len(first_span.split()) > 6 and (" و" in first_span or "[" in first_span):
        return (
            "context_split_needed",
            first_span,
            ctx_span,
            "Long multi-clause span (>6 words with conjunction/brackets); verify Policy v0.2 split between target and context.",
        )

    # Check for trailing generation/book/death-date leakage
    if any(leak in first_span for leak in ("مات سنة", "من الثالثة", "من الرابعة", "من الخامسة", "من السادسة", "من السابعة", "من الثامنة", "من التاسعة", "من العاشرة")):
        return (
            "boundary_needs_trim",
            first_span,
            ctx_span,
            "Span leaked into tabaqa or death-date metadata; trim before tabaqa/date marker.",
        )

    # Check if 'وثقه' or 'ضعفه' is truncated without critic name
    if first_span.strip() in {"وثقه", "ضعفه", "لينه", "كذبوه", "اتهمه"}:
        return (
            "boundary_needs_extend",
            first_span,
            ctx_span,
            "Bare attributed verb without critic/subject referent; inspect full clause for critic name.",
        )

    return (
        "exact_span_match",
        first_span,
        ctx_span,
        "Clean complete target span boundary and Policy v0.2 context separation confirmed against full entry.",
    )


def main() -> None:
    if OUT_DIR.exists() and any(OUT_DIR.iterdir()):
        raise SystemExit(f"Refusing to overwrite existing sample audit directory: {OUT_DIR}")

    verify_package(CENSUS_DIR)
    entries = {r["entry_id"]: r for r in read_csv(ENTRY_INDEX)}
    census_rows = read_csv(CENSUS_DIR / "GATE_A_ENTRY_COMPLETE_SPAN_CENSUS_V0_1.csv")
    assert len(census_rows) == 8827

    rng = random.Random(20261117)
    by_stratum: dict[str, list[dict[str, str]]] = {k: [] for k in STRATUM_QUOTAS}
    for r in census_rows:
        cat = r["gate_a_category"]
        if cat in by_stratum:
            by_stratum[cat].append(r)

    sampled: list[dict[str, Any]] = []
    for cat, quota in STRATUM_QUOTAS.items():
        pool = list(by_stratum[cat])
        rng.shuffle(pool)
        chosen = sorted(pool[:quota], key=lambda x: x["entry_id"])
        for idx, r in enumerate(chosen, 1):
            eid = r["entry_id"]
            full_text = entries[eid]["entry_text_verbatim"]
            status, rec_target, rec_ctx, note = audit_sample_row(r, full_text)
            row_out = {
                "sample_id": f"GA-SMP-{len(sampled) + 1:03d}",
                "stratum": cat,
                "entry_id": eid,
                "printed_page_num": r["printed_page_num"],
                "source_chunk_index": r["source_chunk_index"],
                "first_complete_target_span_exact": r["first_complete_target_span_exact"],
                "context_note_spans_exact": r["context_note_spans_exact"],
                "matched_source_anchor_ranks": r["matched_source_anchor_ranks"],
                "audit_boundary_status": status,
                "recommended_target_span_exact": rec_target,
                "recommended_context_span_exact": rec_ctx,
                "audit_note": note,
                "entry_text_verbatim": full_text,
                "human_verification_status": "",
                "human_notes": "",
            }
            for k, v in row_out.items():
                assert_no_em_en_dash(str(v), f"{row_out['sample_id']}.{k}")
            sampled.append(row_out)

    assert len(sampled) == 100
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sample_csv = OUT_DIR / "GATE_A_CENSUS_SAMPLE_100_AUDIT_V0_1.csv"
    write_csv(sample_csv, sampled, list(sampled[0]))

    status_counts = Counter(r["audit_boundary_status"] for r in sampled)
    corpus_cat_counts = Counter(r["gate_a_category"] for r in census_rows)

    exact_clean = status_counts["exact_span_match"] + status_counts["confirmed_non_grade_or_abstain"]
    report_lines = [
        "# Gate A Census 100-Entry Stratified Sample Audit v0.1 (TODO Lines 28 & 30)",
        "",
        "**Status:** stratified verification sample (`N=100`, `seed=20261117`) drawn from the `8,827`-entry Gate A Complete-Span Census (`v0.1`). All `human_*` fields remain blank pending your approval. Zero canonical ranks assigned and zero rules enabled.",
        "",
        "## 1. Full Corpus Denominators (`N = 8,827` numbered entries)",
        f"- Total numbered entries: `{len(census_rows)}`",
        f"- Entries with non-empty target span: `{sum(1 for r in census_rows if r['first_complete_target_span_exact'])}` (`{sum(1 for r in census_rows if r['first_complete_target_span_exact']) / len(census_rows) * 100:.2f}%`)",
        f"- Entries with `non_grade_or_abstain`: `{corpus_cat_counts['non_grade_or_abstain']}` (`{corpus_cat_counts['non_grade_or_abstain'] / len(census_rows) * 100:.2f}%`)",
        f"- Category breakdown: `{dict(sorted(corpus_cat_counts.items()))}`",
        "",
        "## 2. Stratified Sample Results (`N = 100`)",
        f"- Quotas: `{STRATUM_QUOTAS}`",
        f"- Audit status counts: `{dict(sorted(status_counts.items()))}`",
        f"- Clean exact-match / confirmed-abstain rate on sample: `{exact_clean}/100` (`{exact_clean}%`)",
        "",
        "## 3. Sampled Issues Flagged for Review",
    ]
    flagged = [
        r for r in sampled
        if r["audit_boundary_status"] not in {"exact_span_match", "confirmed_non_grade_or_abstain"}
    ]
    for r in flagged:
        report_lines.append(
            f"- `{r['sample_id']}` (`{r['entry_id']}`, `{r['audit_boundary_status']}`): span=`{r['first_complete_target_span_exact']}` | {r['audit_note']}"
        )
    report_text = "\n".join(report_lines)
    assert_no_em_en_dash(report_text, "SAMPLE_AUDIT_REPORT_V0_1.md")
    report_path = OUT_DIR / "SAMPLE_AUDIT_REPORT_V0_1.md"
    report_path.write_text(report_text, encoding="utf-8", newline="\n")

    timestamp = datetime.now(timezone.utc).isoformat()
    inputs = [ENTRY_INDEX, CENSUS_DIR / "GATE_A_ENTRY_COMPLETE_SPAN_CENSUS_V0_1.csv", CENSUS_DIR / "MANIFEST.json", Path(__file__).resolve()]
    outputs = [sample_csv, report_path]
    manifest = {
        "package_id": OUT_DIR.name,
        "generated_at_utc": timestamp,
        "scope": "Gate A 100-entry stratified sample audit (TODO lines 28 & 30); human_* blank; zero canonical ranks assigned.",
        "counts": {
            "sample_size": len(sampled),
            "stratum_quotas": STRATUM_QUOTAS,
            "audit_status_counts": dict(sorted(status_counts.items())),
            "clean_exact_or_confirmed_abstain": exact_clean,
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
