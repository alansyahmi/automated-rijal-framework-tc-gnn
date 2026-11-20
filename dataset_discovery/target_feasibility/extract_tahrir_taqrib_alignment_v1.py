#!/usr/bin/env python3
"""Extract and align Taḥrīr Taqrīb al-Tahdhīb (Book 8246) with Taqrīb al-Tahdhīb (Book 3076).

Reads:
  - data/1_raw/Shamela4_Full_DB/26__التراجم-والطبقات/8246__تحرير-تقريب-التهذيب/pages.jsonl
  - data/2_interim/rijal_fyp_modelling_pipeline/rank_label_shadow_run_v1_2026-11-15/ENTRY_INDEX.csv
  - data/2_interim/rijal_fyp_modelling_pipeline/task_a_deterministic_targets_v1_4_2026-11-19/TASK_A_DETERMINISTIC_TARGETS_8827_V1_4.csv

Outputs to:
  data/2_interim/rijal_fyp_modelling_pipeline/tahrir_taqrib_alignment_v1_2026-11-20/
    - TAHRIR_TAQRIB_ALIGNED_8827_V1.csv
    - TAHRIR_TAQRIB_ALIGNMENT_REPORT_V1.md
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
TAHRIR_PAGES = (
    ROOT
    / "data/1_raw/Shamela4_Full_DB/26__التراجم-والطبقات/8246__تحرير-تقريب-التهذيب/pages.jsonl"
)
PIPELINE = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline"
ENTRY_INDEX = PIPELINE / "rank_label_shadow_run_v1_2026-11-15/ENTRY_INDEX.csv"
TASK_A_V14 = (
    PIPELINE
    / "task_a_deterministic_targets_v1_4_2026-11-19/TASK_A_DETERMINISTIC_TARGETS_8827_V1_4.csv"
)
OUT_DIR = PIPELINE / "tahrir_taqrib_alignment_v1_2026-11-20"

ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
HTML_TAG_RE = re.compile(r"<[^>]+>")
ENTRY_HEADER_RE = re.compile(r"^(?:[\"\'“”]|و(?=\d|[٠-٩]))?\s*([٠-٩0-9]+)\s*(?:[°\*]|د)?\s*[-–]\s*(.+)$")
CROSSREF_RE = re.compile(r"^[°\*o]\s*[-–]\s*")
BAL_LEAD_RE = re.compile(r"•\s*بل\s*[:：]?\s*([^،.\n]+)")
DIACRITICS_RE = re.compile(r"[\u064b-\u065f\u0670\u0640]")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_arabic_name(text: str, n_words: int = 4) -> str:
    s = ENTRY_HEADER_RE.sub(r"\2", text.strip())
    s = DIACRITICS_RE.sub("", s)
    s = s.split(":", 1)[0]
    s = re.sub(r"[أإآ]", "ا", s)
    s = s.replace("ى", "ي").replace("ة", "ه")
    s = re.sub(r"[^\w\s]", " ", s)
    tokens = ["بن" if t == "ابن" else t for t in s.split()]
    return " ".join(tokens[:n_words])


def load_tahrir_entries() -> list[dict[str, Any]]:
    with TAHRIR_PAGES.open(encoding="utf-8") as f:
        pages = [json.loads(line) for line in f]

    # Sort by (volume/part, shamela_page_id) to restore exact printed book order
    pages.sort(key=lambda p: (int(p["part"]), int(p["shamela_page_id"])))
    start_idx = next(i for i, p in enumerate(pages) if p["page_id"] == 7234541)

    entries: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    for p in pages[start_idx:]:
        body = p.get("body") or ""
        for raw_line in body.splitlines():
            line = HTML_TAG_RE.sub("", raw_line).strip()
            if not line:
                continue

            m = ENTRY_HEADER_RE.match(line)
            if m:
                raw_num_str = m.group(1).translate(ARABIC_DIGITS)
                num = int(raw_num_str)
                prev_num = current["num"] if current is not None else 0

                # Handle occasional Shamela reversed-digit OCR/typing typos (e.g. 91 between 18 and 20)
                if current is not None and not (prev_num - 15 <= num <= prev_num + 25):
                    rev_num = int(raw_num_str[::-1])
                    if prev_num <= rev_num <= prev_num + 5:
                        num = rev_num

                if 1 <= num <= 8827 and (
                    current is None
                    or prev_num - 15 <= num <= prev_num + 25
                    or (len(m.group(2).strip()) >= 8 and ":" in m.group(2))
                    or (len(m.group(2).strip()) >= 12 and "،" in m.group(2))
                ):
                    if current is not None:
                        entries.append(current)
                    current = {
                        "num": num,
                        "part": p["part"],
                        "page_num": p["page_num"],
                        "page_id": p["page_id"],
                        "lines": [line],
                    }
                    continue

            if CROSSREF_RE.match(line):
                if current is not None:
                    entries.append(current)
                    current = None
                continue

            if current is not None:
                current["lines"].append(line)

    if current is not None:
        entries.append(current)

    for e in entries:
        e["norm4"] = normalize_arabic_name(e["lines"][0], 4)
        e["norm3"] = normalize_arabic_name(e["lines"][0], 3)

    return entries


def split_tahrir_entry(entry: dict[str, Any]) -> dict[str, Any]:
    full_text = "\n".join(entry["lines"])
    if "•" not in full_text:
        return {
            "tahrir_matched": True,
            "tahrir_part": entry["part"],
            "tahrir_page_num": entry["page_num"],
            "tahrir_has_bullet": False,
            "tahrir_bullet_count": 0,
            "tahrir_disposition": "agreed_no_bullet",
            "tahrir_verdict_lead": "",
            "tahrir_matn_text": full_text,
            "tahrir_commentary_text": "",
        }

    idx = full_text.index("•")
    matn = full_text[:idx].strip()
    commentary = full_text[idx:].strip()
    bullet_count = commentary.count("•")

    bal_match = BAL_LEAD_RE.search(commentary)
    if bal_match:
        disposition = "dissent_bal"
        verdict_lead = DIACRITICS_RE.sub("", bal_match.group(1)).strip()
    elif re.search(r"•\s*قوله", commentary):
        disposition = "qualification_qawluhu"
        verdict_lead = ""
    else:
        disposition = "other_commentary"
        verdict_lead = ""

    return {
        "tahrir_matched": True,
        "tahrir_part": entry["part"],
        "tahrir_page_num": entry["page_num"],
        "tahrir_has_bullet": True,
        "tahrir_bullet_count": bullet_count,
        "tahrir_disposition": disposition,
        "tahrir_verdict_lead": verdict_lead,
        "tahrir_matn_text": matn,
        "tahrir_commentary_text": commentary,
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    tahrir_entries = load_tahrir_entries()
    by_num: dict[int, list[dict[str, Any]]] = {}
    by_norm4: dict[str, list[dict[str, Any]]] = {}
    by_norm3: dict[str, list[dict[str, Any]]] = {}
    for e in tahrir_entries:
        by_num.setdefault(e["num"], []).append(e)
        if e["norm4"]:
            by_norm4.setdefault(e["norm4"], []).append(e)
        if e["norm3"]:
            by_norm3.setdefault(e["norm3"], []).append(e)

    with TASK_A_V14.open(encoding="utf-8-sig") as f:
        task_a_by_id = {row["entry_id"]: row for row in csv.DictReader(f)}

    with ENTRY_INDEX.open(encoding="utf-8-sig") as f:
        index_rows = list(csv.DictReader(f))

    out_rows: list[dict[str, Any]] = []
    disp_counts: Counter[str] = Counter()
    match_method_counts: Counter[str] = Counter()
    verdict_counts: Counter[str] = Counter()
    matched_count = 0

    for row in index_rows:
        entry_id = row["entry_id"]
        num = int(row["entry_number_numeric"])
        ta = task_a_by_id.get(entry_id, {})
        taqrib_norm4 = normalize_arabic_name(row["entry_text_verbatim"], 4)
        taqrib_norm3 = normalize_arabic_name(row["entry_text_verbatim"], 3)

        chosen = None
        match_method = "unmatched"
        candidates = by_num.get(num, [])
        if candidates:
            chosen = next((c for c in candidates if c["norm3"] == taqrib_norm3), candidates[0])
            match_method = "exact_entry_number"
        else:
            name_cands = [
                c for c in by_norm4.get(taqrib_norm4, []) if abs(c["num"] - num) <= 100
            ]
            if not name_cands and len(by_norm4.get(taqrib_norm4, [])) == 1:
                name_cands = by_norm4[taqrib_norm4]
            if not name_cands:
                name_cands = [
                    c for c in by_norm3.get(taqrib_norm3, []) if abs(c["num"] - num) <= 100
                ]
            if not name_cands and len(by_norm3.get(taqrib_norm3, [])) == 1:
                name_cands = by_norm3[taqrib_norm3]
            if name_cands:
                chosen = min(name_cands, key=lambda c: abs(c["num"] - num))
                match_method = "normalized_name_fallback"

        if chosen is not None:
            parsed = split_tahrir_entry(chosen)
            matched_count += 1
        else:
            parsed = {
                "tahrir_matched": False,
                "tahrir_part": "",
                "tahrir_page_num": "",
                "tahrir_has_bullet": False,
                "tahrir_bullet_count": 0,
                "tahrir_disposition": "unmatched_in_tahrir",
                "tahrir_verdict_lead": "",
                "tahrir_matn_text": "",
                "tahrir_commentary_text": "",
            }

        disp_counts[parsed["tahrir_disposition"]] += 1
        match_method_counts[match_method] += 1
        if parsed["tahrir_verdict_lead"]:
            verdict_counts[parsed["tahrir_verdict_lead"]] += 1

        out_rows.append(
            {
                "entry_id": entry_id,
                "entry_number_numeric": num,
                "printed_page_num_3076": row["printed_page_num"],
                "taqrib_text_verbatim": row["entry_text_verbatim"],
                "taqrib_disposition_v1_4": ta.get("deterministic_disposition", ""),
                "taqrib_rank_1_to_12": ta.get("deterministic_rank_1_to_12", ""),
                "taqrib_target_span": ta.get("first_complete_target_span_exact", ""),
                "taqrib_context_note_spans": ta.get("context_note_spans_exact", ""),
                "tahrir_matched": parsed["tahrir_matched"],
                "tahrir_match_method": match_method,
                "tahrir_part": parsed["tahrir_part"],
                "tahrir_page_num": parsed["tahrir_page_num"],
                "tahrir_has_bullet": parsed["tahrir_has_bullet"],
                "tahrir_bullet_count": parsed["tahrir_bullet_count"],
                "tahrir_disposition": parsed["tahrir_disposition"],
                "tahrir_verdict_lead": parsed["tahrir_verdict_lead"],
                "tahrir_matn_text": parsed["tahrir_matn_text"],
                "tahrir_commentary_text": parsed["tahrir_commentary_text"],
            }
        )

    out_csv = OUT_DIR / "TAHRIR_TAQRIB_ALIGNED_8827_V1.csv"
    fieldnames = list(out_rows[0].keys())
    with out_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(out_rows)

    report_md = OUT_DIR / "TAHRIR_TAQRIB_ALIGNMENT_REPORT_V1.md"
    lines = [
        "# Taḥrīr Taqrīb al-Tahdhīb (8246) ↔ Taqrīb al-Tahdhīb (3076) Alignment Report (v1)",
        "",
        f"- **Generated (UTC):** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%SZ')}",
        f"- **Total Taqrīb entries (3076):** {len(index_rows)}",
        f"- **Matched in Taḥrīr (8246):** {matched_count} ({matched_count / len(index_rows) * 100:.2f}%)",
        "",
        "## Disposition Breakdown",
        "",
        "| Disposition | Count | Share |",
        "|---|---:|---:|",
    ]
    for disp, cnt in disp_counts.most_common():
        lines.append(f"| `{disp}` | {cnt} | {cnt / len(index_rows) * 100:.2f}% |")

    lines.extend(
        [
            "",
            "## Top 25 `• بل:` Verdict Leads (Diacritics Stripped)",
            "",
            "| Verdict Lead | Count |",
            "|---|---:|",
        ]
    )
    for v, cnt in verdict_counts.most_common(25):
        lines.append(f"| `{v}` | {cnt} |")

    report_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    manifest_files = [out_csv, report_md]
    manifest = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "script": "dataset_discovery/target_feasibility/extract_tahrir_taqrib_alignment_v1.py",
        "total_entries": len(out_rows),
        "matched_entries": matched_count,
        "dispositions": dict(disp_counts),
        "files": {p.name: {"sha256": sha256_file(p), "bytes": p.stat().st_size} for p in manifest_files},
    }
    manifest_json = OUT_DIR / "MANIFEST.json"
    manifest_json.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    sha_lines = [f"{sha256_file(p)}  {p.name}" for p in [*manifest_files, manifest_json]]
    (OUT_DIR / "MANIFEST.sha256").write_text("\n".join(sha_lines) + "\n", encoding="utf-8")

    print(f"Wrote {len(out_rows)} aligned rows to {out_csv}")
    print("Matched:", matched_count, "/", len(index_rows))
    print("Dispositions:", dict(disp_counts))


if __name__ == "__main__":
    main()
