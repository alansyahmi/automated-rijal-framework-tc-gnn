#!/usr/bin/env python3
"""Map Taqrīb (3076) and Taḥrīr (8246) onto the Bilgin (2026)-grounded 12-rank taxonomy.

Reads:
  - data/2_interim/rijal_fyp_modelling_pipeline/tahrir_taqrib_alignment_v1_2026-11-20/TAHRIR_TAQRIB_ALIGNED_8827_V1.csv
  - data/2_interim/rijal_fyp_modelling_pipeline/task_a_deterministic_targets_v1_4_2026-11-19/TASK_A_DETERMINISTIC_TARGETS_8827_V1_4.csv

Outputs to:
  data/2_interim/rijal_fyp_modelling_pipeline/bilgin_grounded_targets_v2_2026-11-20/
    - BILGIN_GROUNDED_TAQRIB_TAHRIR_8827_V2.csv
    - BILGIN_GROUNDED_TARGETS_REPORT_V2.md
    - MANIFEST.json
    - MANIFEST.sha256
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
ALIGNED_V1 = PIPELINE / "tahrir_taqrib_alignment_v1_2026-11-20/TAHRIR_TAQRIB_ALIGNED_8827_V1.csv"
TASK_A_V14 = PIPELINE / "task_a_deterministic_targets_v1_4_2026-11-19/TASK_A_DETERMINISTIC_TARGETS_8827_V1_4.csv"
OUT_DIR = PIPELINE / "bilgin_grounded_targets_v2_2026-11-20"

DIACRITICS_RE = re.compile(r"[\u064b-\u065f\u0670\u0640]")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def map_tahrir_verdict_to_rank(
    verdict_lead: str, full_commentary: str, entry_id: str = ""
) -> tuple[str, str]:
    """Map Taḥrīr's `• بل:` verdict lead to Bilgin (2026) 1–12 rank + rule_id."""
    v = DIACRITICS_RE.sub("", verdict_lead).strip()
    if not v:
        return "", "TAHRIR-EMPTY-LEAD"

    # Guarded Shamela 8246 OCR typos (gated by exact entry_id + exact normalized lead)
    if entry_id == "S3076-P438-C002-E5284" and v == "ورقة":
        return "3", "TAHRIR-R3-OCR-TYPO-WARAQAH"
    if entry_id == "S3076-P466-C002-E5699" and v == "قوله":
        return "9", "TAHRIR-R9-OCR-TYPO-QAWLUHU"
    if entry_id == "S3076-P524-C010-E6546" and v == "جهول":
        return "9", "TAHRIR-R9-OCR-TYPO-JAHUL"

    # Rank 12: Kadhdhab / Wadda'
    if re.search(r"كذاب|كذبوه|وضاع|يضع\s+الحديث", v):
        return "12", "TAHRIR-R12-KADHDHAB"

    # Rank 11: Muttaham bi-l-kadhib / bi-l-wad'
    if re.search(r"متهم\s+بالكذب|متهم\s+بالوضع", v):
        return "11", "TAHRIR-R11-MUTTAHAM"

    # Rank 10: Matruk / Da'if jiddan / Wahin
    if re.search(r"متروك|ضعيف\s+جدا|واه\b|واهي|ساقط|ذاهب\s+الحديث", v):
        return "10", "TAHRIR-R10-MATRUK-OR-JIDDAN"

    # Rank 7: Da'if yu'tabaru bih / Mastur / Majhul al-hal / Layyin (checked BEFORE Rank 9 so مجهول الحال is never swallowed)
    if re.search(
        r"ضعيف\s+يعتبر\s+به|مستور|مجهول[ة]?\s+الحال|لين\s+الحديث|فيه\s+لين|يكتب\s+حديثه\s+مع\s+ضعفه",
        v,
    ):
        return "7", "TAHRIR-R7-YUTABAR-OR-MASTUR"

    # Rank 9: Majhul (excluding majhul al-hal)
    if re.search(r"^(?:هو\s+|هي\s+)?مجهول(?:ة)?(?:\s+العين|\s+كسابقه)?(?=$|[:,،])", v) or re.search(
        r"لا\s+يعرف\b|لا\s+تعرف\b", v
    ):
        return "9", "TAHRIR-R9-MAJHUL"

    # Rank 8: Da'if (unqualified / without yu'tabaru bih or jiddan)
    if re.search(r"ضعيف|منكر\s+الحديث", v):
        return "8", "TAHRIR-R8-DAIF"

    # Rank 6: Maqbul
    if re.search(
        r"^مقبول|(?:في\s+أحسن\s+أحواله|هو\s+مثل\s+الذي\s+قبله)\s*:\s*مقبول", v
    ):
        return "6", "TAHRIR-R6-MAQBUL"

    # Rank 5: Qualified Saduq (saduq yahim / yukhti / lahu awham / sayyi' al-hifz)
    if re.search(r"صدوق[ة]?\s+(?:يهم|يخطئ|له\s+أوهام|سيء\s+الحفظ|ربما)", v):
        return "5", "TAHRIR-R5-QUALIFIED-SADUQ"

    # Rank 4: Saduq / Saduq hasan al-hadith / La ba's bih
    if re.search(r"صدوق|لا\s+بأس\s+به|حسن\s+الحديث", v):
        return "4", "TAHRIR-R4-SADUQ-HASAN"

    # Rank 2: Compound / superlative Thiqah
    if re.search(r"ثقة\s+(?:ثقة|ثبت|حافظ|حجة|إمام|متقن|مأمون)", v):
        return "2", "TAHRIR-R2-COMPOUND-THIQAH"

    # Rank 3: Thiqah / Qawi
    if re.search(r"^(?:هو\s+)?ثقة|^قوي$|:\s*ثقة$", v):
        return "3", "TAHRIR-R3-THIQAH"

    # Rank 1: Sahabi
    if re.search(r"^صحابي|له\s+صحبة", v) and "لا تصح" not in v:
        return "1", "TAHRIR-R1-SAHABI"

    # Check if refuted companionship is followed by an explicit rank in the commentary
    if re.search(r"لا\s+تصح\s+(?:له\s+)?صحب[ةت]", v):
        c = DIACRITICS_RE.sub("", full_commentary)
        if re.search(r"مجهول\s+الحال", c):
            return "7", "TAHRIR-R7-NOT-SAHABI-MAJHUL-HAL"
        if re.search(r"(?:وهو|فهو)\s*:\s*مقبول", c):
            return "6", "TAHRIR-R6-NOT-SAHABI-MAQBUL"
        if re.search(r"(?:وهو|فهو)\s*:\s*(?:تابعي\s+)?صدوق", c):
            return "4", "TAHRIR-R4-NOT-SAHABI-SADUQ"
        if re.search(r"مجهول", c):
            return "9", "TAHRIR-R9-NOT-SAHABI-MAJHUL"
        if re.search(r"تابعي\s+ثقة|(?:وهو|فهو)\s*:\s*ثقة", c):
            return "3", "TAHRIR-R3-NOT-SAHABI-THIQAH"

    return "", "TAHRIR-UNMAPPED-LEAD"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with TASK_A_V14.open(encoding="utf-8-sig") as f:
        v14_by_id = {r["entry_id"]: r for r in csv.DictReader(f)}

    with ALIGNED_V1.open(encoding="utf-8-sig") as f:
        aligned_rows = list(csv.DictReader(f))

    out_rows: list[dict[str, Any]] = []
    taq_rank_counts: Counter[str] = Counter()
    tah_rank_counts: Counter[str] = Counter()
    tah_rule_counts: Counter[str] = Counter()
    unmapped_leads: Counter[str] = Counter()
    rank_shift_counts: Counter[str] = Counter()

    for row in aligned_rows:
        eid = row["entry_id"]
        v14 = v14_by_id.get(eid, {})
        v14_rule = v14.get("rule_id", "")
        v14_rank = row["taqrib_rank_1_to_12"].strip()

        # 1. Bilgin-grounded Taqrib Baseline (Score 1)
        is_cond_maqbul = False
        if v14_rule == "GUARD-R6-MAQBUL":
            taq_bilgin_rank = "6"
            taq_bilgin_rule = "BILGIN-R6-MAQBUL"
            is_cond_maqbul = True
        elif v14_rule == "RULE-R6-LAYYIN":
            taq_bilgin_rank = "7"
            taq_bilgin_rule = "BILGIN-R7-LAYYIN"
        elif v14_rank:
            taq_bilgin_rank = v14_rank
            taq_bilgin_rule = v14_rule
        else:
            taq_bilgin_rank = ""
            taq_bilgin_rule = v14_rule

        if taq_bilgin_rank:
            taq_rank_counts[taq_bilgin_rank] += 1

        # 2. Bilgin-grounded Tahrir Verdict (Score 2 Target)
        tahrir_disp = row["tahrir_disposition"]
        if tahrir_disp == "agreed_no_bullet":
            if is_cond_maqbul:
                # Tahrir Intro p. 45: uncommented Maqbul is treated as Da'if yu'tabaru bih (Rank 7)
                tah_bilgin_rank = "7"
                tah_rule = "TAHRIR-AGREED-MAQBUL-TO-R7"
            elif taq_bilgin_rank:
                tah_bilgin_rank = taq_bilgin_rank
                tah_rule = "TAHRIR-AGREED-AS-TAQRIB"
            else:
                tah_bilgin_rank = ""
                tah_rule = "TAHRIR-AGREED-UNRANKED-TAQRIB"
        elif tahrir_disp == "dissent_bal":
            tah_bilgin_rank, tah_rule = map_tahrir_verdict_to_rank(
                row["tahrir_verdict_lead"], row["tahrir_commentary_text"], eid
            )
            if not tah_bilgin_rank and row["tahrir_verdict_lead"]:
                unmapped_leads[row["tahrir_verdict_lead"]] += 1
        else:
            # qualification_qawluhu / other_commentary / unmatched
            tah_bilgin_rank = taq_bilgin_rank
            tah_rule = f"TAHRIR-{tahrir_disp.upper()}-KEEP-BASELINE" if taq_bilgin_rank else f"TAHRIR-{tahrir_disp.upper()}-UNRANKED"

        if tah_bilgin_rank:
            tah_rank_counts[tah_bilgin_rank] += 1
        tah_rule_counts[tah_rule] += 1

        if taq_bilgin_rank and tah_bilgin_rank:
            diff = int(tah_bilgin_rank) - int(taq_bilgin_rank)
            if diff == 0:
                rank_shift_counts["unchanged"] += 1
            elif diff < 0:
                rank_shift_counts["upgraded_more_reliable"] += 1
            else:
                rank_shift_counts["downgraded_less_reliable"] += 1

        out_rows.append(
            {
                **row,
                "taqrib_rank_bilgin_1_to_12": taq_bilgin_rank,
                "taqrib_bilgin_rule_id": taq_bilgin_rule,
                "taqrib_is_conditional_maqbul": is_cond_maqbul,
                "tahrir_rank_bilgin_1_to_12": tah_bilgin_rank,
                "tahrir_bilgin_rule_id": tah_rule,
            }
        )

    out_csv = OUT_DIR / "BILGIN_GROUNDED_TAQRIB_TAHRIR_8827_V2.csv"
    fieldnames = list(out_rows[0].keys())
    with out_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(out_rows)

    report_md = OUT_DIR / "BILGIN_GROUNDED_TARGETS_REPORT_V2.md"
    taq_total = sum(taq_rank_counts.values())
    tah_total = sum(tah_rank_counts.values())
    lines = [
        "# Bilgin (2026)-Grounded 12-Rank Targets Report (`v2`)",
        "",
        f"- **Generated (UTC):** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%SZ')}",
        f"- **Total entries:** {len(out_rows)}",
        f"- **Taqrīb Bilgin-grounded ranked (Score 1):** {taq_total} ({taq_total / len(out_rows) * 100:.2f}%)",
        f"- **Taḥrīr Bilgin-grounded ranked (Score 2 Target):** {tah_total} ({tah_total / len(out_rows) * 100:.2f}%)",
        "",
        "## Rank Distribution (1–12): Taqrīb Baseline vs. Taḥrīr Verdict",
        "",
        "| Rank | Taqrīb (Bilgin-Grounded) | Taḥrīr (Scholar Verdict) |",
        "|---:|---:|---:|",
    ]
    for r in range(1, 13):
        rs = str(r)
        lines.append(f"| {r} | {taq_rank_counts.get(rs, 0)} | {tah_rank_counts.get(rs, 0)} |")

    lines.extend(
        [
            "",
            "## Score 1 → Score 2 Direction (Among Entries Ranked on Both Sides)",
            "",
            "| Shift | Count |",
            "|---|---:|",
        ]
    )
    for k, v in rank_shift_counts.most_common():
        lines.append(f"| `{k}` | {v} |")

    if unmapped_leads:
        lines.extend(["", "## Top Unmapped `• بل:` Leads", "", "| Lead | Count |", "|---|---:|"])
        for k, v in unmapped_leads.most_common(20):
            lines.append(f"| `{k}` | {v} |")

    report_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    manifest_files = [out_csv, report_md]
    manifest = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "script": "dataset_discovery/target_feasibility/build_bilgin_grounded_targets_v2.py",
        "taqrib_ranked_total": taq_total,
        "tahrir_ranked_total": tah_total,
        "taqrib_rank_counts": dict(taq_rank_counts),
        "tahrir_rank_counts": dict(tah_rank_counts),
        "rank_shifts": dict(rank_shift_counts),
        "files": {p.name: {"sha256": sha256_file(p), "bytes": p.stat().st_size} for p in manifest_files},
    }
    manifest_json = OUT_DIR / "MANIFEST.json"
    manifest_json.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT_DIR / "MANIFEST.sha256").write_text(
        "\n".join(f"{sha256_file(p)}  {p.name}" for p in [*manifest_files, manifest_json]) + "\n",
        encoding="utf-8",
    )

    print("Taqrib Bilgin-grounded ranked:", taq_total, "/", len(out_rows))
    print("Tahrir Bilgin-grounded ranked:", tah_total, "/", len(out_rows))
    print("Rank shifts:", dict(rank_shift_counts))
    print("Unmapped dissent_bal leads:", sum(unmapped_leads.values()))


if __name__ == "__main__":
    main()
