#!/usr/bin/env python3
"""Resolve the 13-item Gold-50 Adjudication Queue using primary source evidence
and produce the reconciled Gold-50 Reference Set v2.1.

Reads v2_gold50_and_atomic_esa_v0_2_2026-11-19 read-only and writes to
v2_gold50_adjudication_v2_1_2026-11-19 with full provenance and checksums.
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
V02_DIR = PIPELINE / "v2_gold50_and_atomic_esa_v0_2_2026-11-19"
GOLD50_V02_FP = V02_DIR / "GOLD_50_RECONCILED_VALIDATION_SET_V2_0.csv"
OUT_DIR = PIPELINE / "v2_gold50_adjudication_v2_1_2026-11-19"

# Explicit primary-source adjudication rulings for the 13 queue items
ADJUDICATIONS: dict[int, tuple[str, str, str, str]] = {
    # gold_id: (adjudicated_stage1_rank, adjudicated_effective_tier, adjudication_basis, rationale)
    16: (
        "8",
        "8 (daif)",
        "Taqrib intro literal Rank 8 (Awwama 1406 / Alifta 1413)",
        "Entry text is ضعيف رافضي. Both published Arabic editions of Ibn Hajar's Taqrib introduction define Rank 8 as ضعيف and Rank 9 as مجهول; the Rank 9 reading on Wikimedia came from an OCR-shifted scan.",
    ),
    18: (
        "8",
        "8 (daif)",
        "Taqrib intro literal Rank 8 (Awwama 1406 / Alifta 1413)",
        "Entry text is ضعيف. Follows verbatim Taqrib introduction Rank 8 = ضعيف (matching all 330 Rank 8 entries in Task A v1.4).",
    ),
    42: (
        "8",
        "8 (daif)",
        "Taqrib intro literal Rank 8 (Awwama 1406 / Alifta 1413)",
        "Entry text is ضعيف الحديث. Follows verbatim Taqrib introduction Rank 8 = ضعيف.",
    ),
    43: (
        "8",
        "8 (daif + post-theft ikhtilat)",
        "Taqrib intro literal Rank 8 (Awwama 1406 / Alifta 1413)",
        "Entry text is ضعيف وكان قد سرق بيته فاختلط. Stage 1 baseline = Rank 8; Stage 2 preserves post-theft ikhtilat under dim_temporal_ikhtilat.",
    ),
    46: (
        "8",
        "8 (daif)",
        "Taqrib intro literal Rank 8 (Awwama 1406 / Alifta 1413)",
        "Entry text is ضعيف. Follows verbatim Taqrib introduction Rank 8 = ضعيف.",
    ),
    36: (
        "3",
        "3 (thiqah + kathir al-irsal + minor late-life note)",
        "Taqrib intro Rank 3 + corpus consistency (5/5 ثقة فقيه فاضل)",
        "فقيه فاضل expresses jurisprudential stature and piety, not reinforced hadith dabt; consistent with all 5 ثقة فقيه فاضل entries in Taqrib. Stage 2 captures كثير الإرسال and minor late-life تغير.",
    ),
    37: (
        "3",
        "3 (thiqah)",
        "Taqrib intro Rank 3 + Shamela4 link fixed (2980)",
        "Explicitly ثقة فقيه فاضل (Rank 3); Shamela4 link corrected from grandson 20152 to 2980 (طاووس بن كيسان).",
    ),
    38: (
        "3",
        "3 (thiqah, imam in tafsir/knowledge)",
        "Taqrib intro Rank 3 (scoped scholarly epithet)",
        "Text is ثقة إمام في التفسير وفي العلم. The imam epithet is explicitly scoped to tafsir and general knowledge rather than hadith transmission precision, keeping conservative Rank 3.",
    ),
    39: (
        "3",
        "3_conditional (thiqah outside al-Zuhri)",
        "Local Taqrib text E2437 + Ahmad ibn Hanbal in Shamela4 2467",
        "SOURCE CORRECTION: Local Taqrib E2437 reads ثقة في غير الزهري باتفاقهم (trustworthy OTHER THAN al-Zuhri), corroborated by Ahmad (في حديثه عن الزهري شيء). Baseline Rank 3 with mandatory teacher-conditional scope in Stage 2.",
    ),
    17: (
        "8",
        "8 (daif fi al-hadith; partisan takhdib excluded)",
        "Taqrib E1029 + Ahmad b. Salih / Ibn Abd al-Barr / al-Dhahabi / Tahrir",
        "Text is كذبه الشعبي في رأيه ورمي بالرفض وفي حديثه ضعف. Classical critics (Ahmad b. Salih, Ibn Abd al-Barr, al-Dhahabi) explain al-Sha'bi's charge targeted partisan opinion, not hadith fabrication; Ibn Hajar's hadith verdict is وفي حديثه ضعف (Rank 8). Automated Task A v1.4 intentionally keeps abstaining to test complex-guard behavior.",
    ),
    19: (
        "4",
        "4_baseline -> 8/10_effective (fatal unseparated ikhtilat)",
        "Taqrib E5685 + Shamela4 5347 (al-Nasa'i, Ibn Ma'in, Ibn Sa'd)",
        "Key two-stage stress test: initial baseline word صدوق gives Stage 1 Rank 4 (B=0.7273), while Stage 2 context اختلط جدا ولم يتميز حديثه فترك (plus Ibn Ma'in/al-Nasa'i ضعيف) drives a severe negative adjustment under dim_temporal_ikhtilat.",
    ),
    48: (
        "12",
        "12 (applied lying label: kadhabuhu wa hajaruhu)",
        "Taqrib E6868 + corpus 13/13 RULE-R12-PLURAL-KADHABUHU + Shamela4 11017",
        "Text is كذبوه وهجروه ورمى بالتجسيم. Consistent with all 13 other standalone كذبوه entries in Taqrib (Rank 12: plural applied lying), and corroborated by Shamela4 11017 (al-Mahdi fabricated-hadith offer, Isa b. Yunus isnad-switching, Ibn Ma'in/al-Nasa'i/al-Juzajani).",
    ),
    49: (
        "EXTERNAL",
        "external_daif_imami (al-Ghada'iri) / severe_jarh_sunni (sid=12587)",
        "al-Ghada'iri Kitab al-Du'afa' 1/3/3 + Shamela4 12587",
        "Absent from Taqrib (no Stage 1 Taqrib baseline B). External Imami primary source rates Amr b. Shimr as ضعيف (1/3/3); Shamela4 12587 records 21 Sunni jarh clauses (al-Bukhari منكر الحديث, Ibn Ma'in ضعيف لا يكتب حديثه, al-Nasa'i/al-Daraqutni متروك الحديث).",
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


def linear_B(rank_str: str) -> str:
    if rank_str.isdigit():
        r = int(rank_str)
        if 1 <= r <= 12:
            return f"{1.0 - (r - 1) / 11.0:.4f}"
    return ""


def main() -> None:
    if OUT_DIR.exists() and any(OUT_DIR.iterdir()):
        raise SystemExit(f"Refusing to overwrite existing adjudication directory: {OUT_DIR}")

    gold_rows = read_csv(GOLD50_V02_FP)
    assert len(gold_rows) == 50

    resolved_rows: list[dict[str, Any]] = []
    status_counts: Counter[str] = Counter()
    rank_counts: Counter[str] = Counter()

    for r in gold_rows:
        gid = int(r["gold_id"])
        if gid in ADJUDICATIONS:
            adj_rank, eff_tier, basis, rationale = ADJUDICATIONS[gid]
            adj_status = "adjudicated_from_queue"
        else:
            adj_rank = r["taqrib_intro_literal_rank_1_to_12"]
            eff_tier = adj_rank
            basis = f"Task A {r['v1_4_rule_id']} verified against Taqrib introduction"
            rationale = r["reconciliation_note"]
            adj_status = "confirmed_automated_and_source_aligned"

        status_counts[adj_status] += 1
        rank_counts[adj_rank] += 1

        out_row = {
            **r,
            "adjudicated_stage1_rank": adj_rank,
            "adjudicated_stage1_baseline_B": linear_B(adj_rank),
            "adjudicated_effective_tier": eff_tier,
            "adjudication_status": adj_status,
            "adjudication_source_basis": basis,
            "adjudication_rationale": rationale,
        }
        for k, v in out_row.items():
            assert_no_em_en_dash(str(v), f"G{gid:02d}.{k}")
        resolved_rows.append(out_row)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_csv = OUT_DIR / "GOLD_50_ADJUDICATED_REFERENCE_V2_1.csv"
    write_csv(out_csv, resolved_rows, list(resolved_rows[0]))

    report_lines = [
        "# Gold-50 Adjudication & Source Reconciliation Report (v2.1)",
        "",
        "**Status:** All 13 Gold-50 queue items researched against primary Arabic sources (`Taqrib al-Tahdhib` Awwama 1406 & Alifta 1413 introductions, `Shamela4` critic dossiers, `Tahrir Taqrib al-Tahdhib` summaries, and al-Ghada'iri `Kitab al-Du'afa'`) and resolved into a unified reference table.",
        "",
        "## 1. Key Source Findings",
        "- **Rank 8 vs Rank 9 (`ضعيف` vs `مجهول`):** Both published Arabic editions of Ibn Hajar's introduction (Awwama 1406 / Dorar / Wikisource and Abu al-Ashbal 1413 / Alifta) explicitly define **Rank 8 = `ضعيف`** and **Rank 9 = `مجهول`**. The Rank 9 = `ضعيف` numbering on Wikimedia stemmed from an OCR-shifted scan (`فطبقة عشرة`). All 5 `ضعيف` entries (`#16, #18, #42, #43, #46`) are adjudicated to **Rank 8** (`B = 0.3636`), matching all 330 `ضعيف` entries in Task A v1.4.",
        "- **Sufyan ibn Husayn (`#39`, `E2437`) Text Correction:** Local Taqrib text reads `ثقة في غير الزهري باتفاقهم` (*trustworthy in narrations OTHER THAN al-Zuhri*), not *in al-Zuhri*; corroborated by Ahmad ibn Hanbal in Shamela4 (`2467`).",
        "- **Rank 3 Scholarly Epithets (`#36, #37, #38`):** `ثقة فقيه فاضل` (`#36` Ata, `#37` Tawus) and `ثقة إمام في التفسير وفي العلم` (`#38` Mujahid) are adjudicated to **Rank 3** because `فقيه`, `فاضل`, and `إمام في التفسير` denote juristic/exegetical eminence rather than reinforced hadith transmission precision.",
        "- **Muqatil ibn Sulayman (`#48`, `E6868`):** Adjudicated to **Rank 12** (`كذبوه وهجروه`), matching all 13 other standalone `كذبوه` entries in Taqrib and corroborated by severe fabrication/isnad-switching reports in Shamela4 (`11017`).",
        "- **al-Harith al-A'war (`#17`, `E1029`):** Adjudicated to **Rank 8** (`وفي حديثه ضعف`), because Ibn Hajar restricts al-Sha'bi's accusation to partisan opinion (`كذبه الشعبي في رأيه`), while automated Task A v1.4 intentionally preserves abstention (`GUARD-UNCOVERED-COMPLEX`).",
        "- **Layth ibn Abi Sulaym (`#19`, `E5685`) & Amr ibn Shimr (`#49`, `sid=12587`):** Layth retains Stage 1 Baseline **Rank 4** (`صدوق`, `B = 0.7273`) with mandatory Stage 2 fatal *ikhtilat* penalty (`اختلط جدا ولم يتميز حديثه فترك`); Amr ibn Shimr remains `EXTERNAL` (absent from Taqrib; al-Ghada'iri `1/3/3` `ضعيف` + 21 Sunni jarh clauses in Shamela4 `12587`).",
        "",
        "## 2. Adjudicated Stage 1 Rank Counts (`N = 50`)",
        f"- Adjudication status counts: `{dict(sorted(status_counts.items()))}`",
        f"- Stage 1 Rank distribution: `{dict(sorted(rank_counts.items()))}`",
    ]
    report_text = "\n".join(report_lines) + "\n"
    assert_no_em_en_dash(report_text, "GOLD_50_ADJUDICATION_RESEARCH_REPORT_V2_1.md")
    report_fp = OUT_DIR / "GOLD_50_ADJUDICATION_RESEARCH_REPORT_V2_1.md"
    report_fp.write_text(report_text, encoding="utf-8", newline="\n")

    timestamp = datetime.now(timezone.utc).isoformat()
    inputs = [GOLD50_V02_FP, Path(__file__).resolve()]
    outputs = [out_csv, report_fp]
    manifest = {
        "package_id": OUT_DIR.name,
        "generated_at_utc": timestamp,
        "counts": {
            "gold_50_total": len(resolved_rows),
            "adjudication_status_counts": dict(sorted(status_counts.items())),
            "adjudicated_stage1_rank_counts": dict(sorted(rank_counts.items())),
        },
        "inputs": {path.relative_to(ROOT).as_posix(): digest(path) for path in inputs},
        "outputs": {path.name: digest(path) for path in outputs},
        "manifest_hash_policy": "MANIFEST.sha256 records this manifest hash separately; it is not recursively embedded.",
    }
    manifest_str = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    assert_no_em_en_dash(manifest_str, "MANIFEST.json")
    manifest_fp = OUT_DIR / "MANIFEST.json"
    manifest_fp.write_text(manifest_str, encoding="utf-8", newline="\n")
    (OUT_DIR / "MANIFEST.sha256").write_text(f"{digest(manifest_fp)}  MANIFEST.json\n", encoding="ascii", newline="\n")

    print(json.dumps({"output": str(OUT_DIR), **manifest["counts"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
