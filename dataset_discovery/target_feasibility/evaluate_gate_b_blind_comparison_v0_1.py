#!/usr/bin/env python3
"""Unseal Gate B machine proposals after human freeze and compute comparison report (TODO lines 40-46).

Verifies integrity of both:
1. gate_b_blind_human_only_labels_v0_1_2026-11-17/MANIFEST.json (frozen human labels)
2. gate_b_blind_manual_eval_v0_1_2026-11-17/MANIFEST.json (sealed machine proposals)

Records exact span agreement, disagreements by rank and construction, false/unsafe
anchor suggestions (e.g. Rank 6 مقبول without corroboration or Mubhamat non-subject
صحابية), abstentions, full denominators, and per-rank support across all 12 categories.
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
HUMAN_DIR = PIPELINE / "gate_b_blind_human_only_labels_v0_1_2026-11-17"
SEALED_DIR = PIPELINE / "gate_b_blind_manual_eval_v0_1_2026-11-17"
OUT_DIR = PIPELINE / "gate_b_evaluation_report_v0_1_2026-11-17"

DIACRITICS_RE = re.compile(r"[\u064b-\u065f\u0670\u0640]")


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


def verify_package(directory: Path) -> str:
    manifest_path = directory / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    sidecar = (directory / "MANIFEST.sha256").read_text(encoding="ascii").split()[0]
    m_hash = digest(manifest_path)
    if m_hash != sidecar:
        raise SystemExit(f"MANIFEST.sha256 mismatch in {directory}")
    for name, expected in manifest["outputs"].items():
        if digest(directory / name) != expected:
            raise SystemExit(f"Hash mismatch for {directory.name}/{name}")
    return m_hash


def compare_spans(human_span: str, machine_span: str) -> str:
    h = DIACRITICS_RE.sub("", human_span).strip(" []().،")
    m = DIACRITICS_RE.sub("", machine_span).strip(" []().،")
    if not h and not m:
        return "both_empty_abstain"
    if not h and m:
        return "machine_false_positive_non_grade"
    if h and not m:
        return "machine_missed_span"
    if h == m:
        return "exact_span_match"
    if h in m:
        return "machine_overextended_includes_context"
    if m in h:
        return "machine_underextended_truncated"
    return "span_mismatch_different_focus"


def compare_rank(human_rank: str, machine_anchor: str, machine_cat: str) -> str:
    if human_rank == "abstain_non_grade":
        if machine_anchor or machine_cat != "non_grade_or_abstain":
            return "false_suggestion_on_non_grade"
        return "agreed_non_grade_abstain"
    if human_rank == "abstain_precondition_unmet":
        if machine_anchor:
            return "unsafe_anchor_when_precondition_unmet"
        return "agreed_requires_review_or_conditional"
    if not machine_anchor:
        return "machine_unanchored_candidate_or_conditional"
    if human_rank == machine_anchor:
        return "exact_anchor_rank_match"
    return "rank_disagreement"


def main() -> None:
    if OUT_DIR.exists() and any(OUT_DIR.iterdir()):
        raise SystemExit(f"Refusing to overwrite existing Gate B report directory: {OUT_DIR}")

    human_manifest_hash = verify_package(HUMAN_DIR)
    sealed_manifest_hash = verify_package(SEALED_DIR)

    human_rows = read_csv(HUMAN_DIR / "HUMAN_ONLY_BLIND_LABELS_120_V0_1.csv")
    sealed_map = {r["eval_id"]: r for r in read_csv(SEALED_DIR / "SEALED_MACHINE_PROPOSALS_120_V0_1.csv")}
    assert len(human_rows) == 120 and len(sealed_map) == 120

    paired_rows: list[dict[str, Any]] = []
    for hrow in human_rows:
        eid = hrow["eval_id"]
        srow = sealed_map[eid]
        assert hrow["entry_id"] == srow["entry_id"]

        span_status = compare_spans(
            hrow["human_first_complete_target_span_exact"],
            srow["sealed_machine_target_span_exact"],
        )
        rank_status = compare_rank(
            hrow["human_source_rank_1_to_12_or_abstain"],
            srow["sealed_machine_matched_source_ranks"],
            srow["sealed_machine_gate_a_category"],
        )

        paired = {
            "eval_id": eid,
            "entry_id": hrow["entry_id"],
            "printed_page_num": hrow["printed_page_num"],
            "source_chunk_index": hrow["source_chunk_index"],
            "sealed_stratum": srow["hidden_stratum"],
            "human_entry_eligibility": hrow["human_entry_eligibility"],
            "human_first_complete_target_span_exact": hrow["human_first_complete_target_span_exact"],
            "sealed_machine_target_span_exact": srow["sealed_machine_target_span_exact"],
            "human_context_note_spans_exact": hrow["human_context_note_spans_exact"],
            "sealed_machine_context_span_exact": srow["sealed_machine_context_span_exact"],
            "human_source_rank_1_to_12_or_abstain": hrow["human_source_rank_1_to_12_or_abstain"],
            "sealed_machine_matched_source_ranks": srow["sealed_machine_matched_source_ranks"],
            "sealed_machine_gate_a_category": srow["sealed_machine_gate_a_category"],
            "span_match_status": span_status,
            "rank_anchor_comparison": rank_status,
            "human_notes": hrow["human_notes"],
            "entry_text_verbatim": hrow["entry_text_verbatim"],
        }
        for k, v in paired.items():
            assert_no_em_en_dash(str(v), f"{eid}.{k}")
        paired_rows.append(paired)

    rank_keys = [str(i) for i in range(1, 13)] + ["abstain_precondition_unmet", "abstain_non_grade"]
    per_rank_rows: list[dict[str, Any]] = []
    for rk in rank_keys:
        sub = [r for r in paired_rows if r["human_source_rank_1_to_12_or_abstain"] == rk]
        span_exact = sum(1 for r in sub if r["span_match_status"] == "exact_span_match")
        over = sum(1 for r in sub if r["span_match_status"] == "machine_overextended_includes_context")
        anchor_match = sum(1 for r in sub if r["rank_anchor_comparison"] == "exact_anchor_rank_match")
        per_rank_rows.append({
            "source_category": rk,
            "human_count": len(sub),
            "exact_span_matches": span_exact,
            "overextended_with_context": over,
            "exact_anchor_rank_matches": anchor_match,
            "disagreement_or_unanchored": len(sub) - anchor_match,
        })

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    paired_csv = OUT_DIR / "GATE_B_BLIND_VS_MACHINE_120_V0_1.csv"
    per_rank_csv = OUT_DIR / "GATE_B_PER_RANK_SUMMARY_V0_1.csv"
    write_csv(paired_csv, paired_rows, list(paired_rows[0]))
    write_csv(per_rank_csv, per_rank_rows, list(per_rank_rows[0]))

    span_counts = Counter(r["span_match_status"] for r in paired_rows)
    rank_comp_counts = Counter(r["rank_anchor_comparison"] for r in paired_rows)
    elig_counts = Counter(r["human_entry_eligibility"] for r in paired_rows)

    over_examples = [r for r in paired_rows if r["span_match_status"] == "machine_overextended_includes_context"]
    false_non_grade = [r for r in paired_rows if r["span_match_status"] == "machine_false_positive_non_grade"]
    under_or_mismatch = [
        r for r in paired_rows
        if r["span_match_status"] in {"machine_underextended_truncated", "span_mismatch_different_focus", "machine_missed_span"}
    ]
    rank_disagree = [r for r in paired_rows if r["rank_anchor_comparison"] == "rank_disagreement"]

    report_lines = [
        "# Gate B Blind Evaluation vs. Machine Proposals Report v0.1 (TODO Lines 40-46)",
        "",
        "**Scope Note (`TODO` line 40):** Single-researcher feasibility check over `120` previously unseen *Taqrīb* entries (`seed=20261119`, excluding all `1,405` development entries). Human labels in `HUMAN_ONLY_BLIND_LABELS_120_V0_1.csv` were frozen under SHA-256 (`{}`) BEFORE unsealing `SEALED_MACHINE_PROPOSALS_120_V0_1.csv` (`{}`). Inter-reviewer reliability is NOT claimed.".format(human_manifest_hash[:16], sealed_manifest_hash[:16]),
        "",
        "## 1. Full Denominators (`N = 120`)",
        f"- Total entries reviewed: `{len(paired_rows)}`",
        f"- Human eligibility breakdown: `{dict(sorted(elig_counts.items()))}`",
        "- Entries with human-assigned canonical Rank `1..12` (`preconditions satisfied`): "
        f"`{sum(1 for r in paired_rows if r['human_source_rank_1_to_12_or_abstain'].isdigit())}`",
        f"- Entries routed to `abstain_precondition_unmet`: `{sum(1 for r in paired_rows if r['human_source_rank_1_to_12_or_abstain'] == 'abstain_precondition_unmet')}`",
        f"- Entries routed to `abstain_non_grade`: `{sum(1 for r in paired_rows if r['human_source_rank_1_to_12_or_abstain'] == 'abstain_non_grade')}`",
        "",
        "## 2. Span Extraction Agreement (`first_complete_target_span_exact`)",
        f"- Counts: `{dict(sorted(span_counts.items()))}`",
        f"- Exact span match: **{span_counts['exact_span_match']} / 120** (`{span_counts['exact_span_match'] / 120 * 100:.1f}%`)",
        f"- Machine included attached qualifier/context without splitting (`machine_overextended_includes_context`): **{span_counts['machine_overextended_includes_context']}**",
        f"- Machine false positive on `non_grade` entry: **{span_counts['machine_false_positive_non_grade']}**",
        "",
        "## 3. Source-Rank & Precondition Comparison",
        f"- Counts: `{dict(sorted(rank_comp_counts.items()))}`",
        "- Notice `unsafe_anchor_when_precondition_unmet` (**{}** cases): exact lexical matches on Rank 6 (`مقبول`/`مقبولة`) or bracketed/doctrinal forms where assigning a label without external corroboration or context guards would violate Gate A preconditions.".format(rank_comp_counts["unsafe_anchor_when_precondition_unmet"]),
        "",
        "## 4. Per-Rank Support (`12` Original Categories Preserved; Zero Collapsing)",
    ]
    for pr in per_rank_rows:
        report_lines.append(
            f"- `{pr['source_category']}`: human=**{pr['human_count']}** | exact_span={pr['exact_span_matches']} | overextended={pr['overextended_with_context']} | exact_anchor_match={pr['exact_anchor_rank_matches']}"
        )

    report_lines.extend(["", "## 5. Detailed Disagreements & False Suggestions"])
    for r in false_non_grade:
        report_lines.append(
            f"- `[FALSE NON-GRADE]` `{r['eval_id']}` (`{r['entry_id']}`): machine=`{r['sealed_machine_target_span_exact']}` | {r['human_notes']}"
        )
    for r in under_or_mismatch:
        report_lines.append(
            f"- `[SPAN {r['span_match_status']}]` `{r['eval_id']}` (`{r['entry_id']}`): human=`{r['human_first_complete_target_span_exact']}` vs machine=`{r['sealed_machine_target_span_exact']}`"
        )
    for r in rank_disagree:
        report_lines.append(
            f"- `[RANK DISAGREE]` `{r['eval_id']}` (`{r['entry_id']}`): human=Rank {r['human_source_rank_1_to_12_or_abstain']} (`{r['human_first_complete_target_span_exact']}`) vs machine_anchor=Rank {r['sealed_machine_matched_source_ranks']} (`{r['sealed_machine_target_span_exact']}`)"
        )
    for r in over_examples:
        report_lines.append(
            f"- `[CONTEXT OVEREXTEND]` `{r['eval_id']}` (`{r['entry_id']}`, R{r['human_source_rank_1_to_12_or_abstain']}): human=`{r['human_first_complete_target_span_exact']}` vs machine=`{r['sealed_machine_target_span_exact']}`"
        )

    report_text = "\n".join(report_lines) + "\n"
    assert_no_em_en_dash(report_text, "GATE_B_FEASIBILITY_REPORT_V0_1.md")
    report_path = OUT_DIR / "GATE_B_FEASIBILITY_REPORT_V0_1.md"
    report_path.write_text(report_text, encoding="utf-8", newline="\n")

    timestamp = datetime.now(timezone.utc).isoformat()
    inputs = [
        HUMAN_DIR / "HUMAN_ONLY_BLIND_LABELS_120_V0_1.csv",
        HUMAN_DIR / "MANIFEST.json",
        SEALED_DIR / "SEALED_MACHINE_PROPOSALS_120_V0_1.csv",
        SEALED_DIR / "MANIFEST.json",
        Path(__file__).resolve(),
    ]
    outputs = [paired_csv, per_rank_csv, report_path]
    manifest = {
        "package_id": OUT_DIR.name,
        "generated_at_utc": timestamp,
        "human_manifest_sha256": human_manifest_hash,
        "sealed_manifest_sha256": sealed_manifest_hash,
        "counts": {
            "entries_evaluated": len(paired_rows),
            "span_match_counts": dict(sorted(span_counts.items())),
            "rank_anchor_comparison_counts": dict(sorted(rank_comp_counts.items())),
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
