#!/usr/bin/env python3
"""Create a post-freeze, non-destructive v1.3 boundary annotation revision."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline/boundary_pilot_v1"
ORIGINAL_PATH = BASE / "BOUNDARY_PILOT_REVIEWER_ANNOTATED_2026-11-15.csv"
GRANULAR_PATH = BASE / "BOUNDARY_PILOT_REVIEW_CORRECTED_GRANULAR_2026-11-15.csv"
FROZEN_PATH = BASE / "frozen_2026-11-15/TAQRIB_BOUNDARY_ANNOTATIONS_FROZEN_V1.csv"
OUTPUT_DIR = BASE / "granular_revision_v1_3_2026-11-15"
MAX_SEGMENTS = 15


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def segments_from(row: dict[str, str]) -> list[dict[str, str]]:
    result = []
    for index in range(1, MAX_SEGMENTS + 1):
        text = row.get(f"segment_{index}_text_verbatim", "")
        if not text:
            continue
        result.append({
            "text": text,
            "role": row.get(f"segment_{index}_role", ""),
            "subrole": row.get(f"segment_{index}_subrole", ""),
            "original_label_refs": "",
        })
    return result


def spans_from_segments(source: str, segments: list[dict[str, str]]) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    cursor = 0
    for segment in segments:
        text = segment["text"]
        if not source.startswith(text, cursor):
            raise ValueError(f"Segment does not match source at character {cursor}: {text!r}")
        start = cursor
        cursor += len(text)
        spans.append((start, cursor))
    if cursor != len(source):
        raise ValueError(f"Segments reconstruct {cursor} of {len(source)} source characters")
    return spans


def original_label_spans(row: dict[str, str]) -> list[dict[str, Any]]:
    source = row["entry_text_verbatim"]
    cursor = 0
    output = []
    for index in range(1, 13):
        text = row.get(f"segment_{index}_text_verbatim", "")
        label = row.get(f"segment_{index}_role", "")
        if not text.strip() or not label.strip():
            continue
        start = source.find(text, cursor)
        if start < 0:
            raise ValueError(f"Original segment not found sequentially: {row['case_id']} segment {index}")
        end = start + len(text)
        output.append({
            "reviewer_label_id": f"{row['case_id']}-ORIG-L{index:02d}",
            "case_id": row["case_id"],
            "original_segment_index": index,
            "original_segment_text_verbatim": text,
            "original_reviewer_label": label,
            "source_start_char": start,
            "source_end_char": end,
            "alignment_status": "exact_substring_in_original_entry",
        })
        cursor = end
    return output


def split_tb022(segments: list[dict[str, str]]) -> list[dict[str, str]]:
    output = []
    split_count = 0
    for segment in segments:
        text = segment["text"]
        marker = "ثم"
        if segment["subrole"] == "nisba" and marker in text:
            start = text.find(marker)
            end = start + len(marker)
            if text[end:].strip():
                output.append({
                    "text": text[:end],
                    "role": "temporal_sequence_marker",
                    "subrole": "temporal_transition",
                    "original_label_refs": "",
                })
                output.append({
                    "text": text[end:],
                    "role": "narrator_name_or_identity",
                    "subrole": "nisba",
                    "original_label_refs": "",
                })
                split_count += 1
                continue
        output.append(segment.copy())
    if split_count != 1:
        raise ValueError(f"Expected exactly one ثم + nisba split in TB-022; got {split_count}")
    return output


def restore_indexed_labels(
    case_id: str,
    segments: list[dict[str, str]],
    segment_spans: list[tuple[int, int]],
    label_rows: list[dict[str, Any]],
    family: str,
) -> None:
    original = sorted(
        [
            r for r in label_rows
            if r["case_id"] == case_id
            and r["original_reviewer_label"].startswith(family)
            and r["original_reviewer_label"] != family
        ],
        key=lambda r: r["source_start_char"],
    )
    if not original:
        return
    current = [
        i for i, segment in enumerate(segments)
        if segment["subrole"] == family
    ]
    if len(original) != len(current):
        raise ValueError(
            f"Cannot restore {family} sequence in {case_id}: {len(original)} original labels vs {len(current)} current spans"
        )
    for label_row, segment_index in zip(original, current):
        seg_start, seg_end = segment_spans[segment_index]
        if max(seg_start, label_row["source_start_char"]) >= min(seg_end, label_row["source_end_char"]):
            raise ValueError(f"{family} labels are not in the same sequence in {case_id}")
        segments[segment_index]["subrole"] = label_row["original_reviewer_label"]


def main() -> None:
    if OUTPUT_DIR.exists():
        raise SystemExit(f"Refusing to overwrite existing revision: {OUTPUT_DIR}")
    _, original_rows = read_csv(ORIGINAL_PATH)
    _, granular_rows = read_csv(GRANULAR_PATH)
    frozen_headers, frozen_rows = read_csv(FROZEN_PATH)
    original_by_id = {row["case_id"]: row for row in original_rows}
    granular_by_id = {row["case_id"]: row for row in granular_rows}
    if set(original_by_id) != set(granular_by_id) or set(granular_by_id) != {row["case_id"] for row in frozen_rows}:
        raise ValueError("Input case IDs do not match across original, granular, and frozen inputs")

    ledger: list[dict[str, Any]] = []
    segment_map: dict[str, list[dict[str, str]]] = {}
    for row in original_rows:
        ledger.extend(original_label_spans(row))
    for frozen in frozen_rows:
        case_id = frozen["case_id"]
        segments = segments_from(granular_by_id[case_id])
        if case_id == "TB-022":
            segments = split_tb022(segments)
        source = frozen["entry_text_verbatim"]
        spans = spans_from_segments(source, segments)
        for family in ("nisba", "kunya"):
            restore_indexed_labels(case_id, segments, spans, ledger, family)
        # Recalculate spans after adding/refining labels; text is unchanged.
        spans = spans_from_segments(source, segments)
        for segment_index, (seg_start, seg_end) in enumerate(spans):
            refs = [
                label["reviewer_label_id"] for label in ledger
                if label["case_id"] == case_id
                and max(seg_start, label["source_start_char"]) < min(seg_end, label["source_end_char"])
            ]
            segments[segment_index]["original_label_refs"] = ";".join(refs)
        segment_map[case_id] = segments

    OUTPUT_DIR.mkdir(parents=True)
    segment_fields = []
    for index in range(1, MAX_SEGMENTS + 1):
        segment_fields.extend([
            f"segment_{index}_text_verbatim",
            f"segment_{index}_role",
            f"segment_{index}_subrole",
            f"segment_{index}_original_label_refs",
        ])
    non_segment_fields = [
        field for field in frozen_headers
        if not any(field.startswith(f"segment_{index}_") for index in range(1, MAX_SEGMENTS + 1))
        and field not in {"freeze_status"}
    ]
    output_fields = non_segment_fields + segment_fields + [
        "prior_freeze_status", "revision_status", "revision_notes"
    ]
    revised_rows = []
    for frozen in frozen_rows:
        case_id = frozen["case_id"]
        segments = segment_map[case_id]
        revised = {field: frozen.get(field, "") for field in non_segment_fields}
        revised["prior_freeze_status"] = frozen.get("freeze_status", "")
        revised["revision_status"] = "revised_copy_pending_user_review"
        revised["revision_notes"] = (
            "User-requested TB-022 split:ثم classified as temporal_transition; الكوفي retained as nisba_2. "
            "Original reviewer labels are linked in the ledger; ordered nisba/kunya labels are restored as subroles."
            if case_id == "TB-022"
            else "Original reviewer labels are linked in the ledger; ordered nisba/kunya labels are restored as subroles."
        )
        for index in range(1, MAX_SEGMENTS + 1):
            segment = segments[index - 1] if index <= len(segments) else {"text": "", "role": "", "subrole": "", "original_label_refs": ""}
            revised[f"segment_{index}_text_verbatim"] = segment["text"]
            revised[f"segment_{index}_role"] = segment["role"]
            revised[f"segment_{index}_subrole"] = segment["subrole"]
            revised[f"segment_{index}_original_label_refs"] = segment["original_label_refs"]
        if len(segments) > MAX_SEGMENTS:
            raise ValueError(f"Too many segments after revision for {case_id}: {len(segments)}")
        revised_rows.append(revised)

    ledger_fields = [
        "reviewer_label_id", "case_id", "original_segment_index", "original_segment_text_verbatim",
        "original_reviewer_label", "source_start_char", "source_end_char", "alignment_status",
    ]
    write_csv(OUTPUT_DIR / "TAQRIB_BOUNDARY_ANNOTATIONS_GRANULAR_V1_3_DRAFT.csv", revised_rows, output_fields)
    write_csv(OUTPUT_DIR / "ORIGINAL_REVIEWER_LABEL_LEDGER.csv", ledger, ledger_fields)

    role_counts = Counter(row["original_reviewer_label"] for row in ledger)
    subrole_counts = Counter(
        segment["subrole"]
        for segments in segment_map.values()
        for segment in segments
        if segment["subrole"]
    )
    tb022 = next(row for row in revised_rows if row["case_id"] == "TB-022")
    tb022_segments = [
        {"index": i, "text": tb022.get(f"segment_{i}_text_verbatim", ""),
         "role": tb022.get(f"segment_{i}_role", ""),
         "subrole": tb022.get(f"segment_{i}_subrole", "")}
        for i in range(1, MAX_SEGMENTS + 1)
        if tb022.get(f"segment_{i}_text_verbatim", "")
    ]
    if not any(x["text"].strip() == "ثم" and x["subrole"] == "temporal_transition" for x in tb022_segments):
        raise ValueError("TB-022 temporal transition was not recorded")
    if not any(x["text"].strip() == "الكوفي" and x["subrole"] == "nisba_2" for x in tb022_segments):
        raise ValueError("TB-022 al-Kufi was not recorded as nisba_2")

    note = f"""# Granular boundary revision v1.3 (draft)

This is a new, non-destructive revision. The original reviewer CSV, v1.2 granular copy, and frozen v1 snapshot remain unchanged.

## What was corrected

- The v1.2 derivative used broad `nisba` and `kunya` subroles, which obscured the original reviewer's indexed labels. This draft restores `nisba`, `nisba_1`, `nisba_2`, `nisba_3`, `kunya`, `kunya_1`, and `kunya_2` where the original label order maps one-to-one to the revised spans.
- Every one of the {len(ledger)} nonblank original reviewer label spans is preserved verbatim in `ORIGINAL_REVIEWER_LABEL_LEDGER.csv`, with case ID and exact character offsets into the original entry. `segment_N_original_label_refs` links the revised segmentation back to these original labels where spans overlap.
- For TB-022, `ثم الكوفي` is split into separate spans: `ثم` (`temporal_sequence_marker` / `temporal_transition`) and `الكوفي` (`narrator_name_or_identity` / `nisba_2`). The prior `المدني` span is restored as `nisba_1`.

## Label counts preserved

Original reviewer labels:

{chr(10).join(f'- `{label}`: {count}' for label, count in sorted(role_counts.items()))}

Restored granular subrole counts:

{chr(10).join(f'- `{label}`: {count}' for label, count in sorted(subrole_counts.items()) if label.startswith(('nisba', 'kunya', 'temporal_transition')))}

The indexed suffixes retain the original reviewer's ordering labels. They are not a new historical or geographic interpretation. The temporal label for TB-022 follows the user's instruction and does not assign a date or claim a more specific life event than the wording provides.

## Review status

`TAQRIB_BOUNDARY_ANNOTATIONS_GRANULAR_V1_3_DRAFT.csv` is a revised working copy pending the user's review. It is not a replacement for or modification of frozen v1.
"""
    (OUTPUT_DIR / "REVISION_NOTE.md").write_text(note, encoding="utf-8", newline="\n")
    readme = """# Taqrīb boundary annotation granular revision v1.3

This folder contains a post-freeze draft that restores the original reviewer's detailed segment labels and applies the requested TB-022 split. Use the BOM-encoded CSVs for Excel. Frozen v1 and all earlier outputs remain unchanged.

- `TAQRIB_BOUNDARY_ANNOTATIONS_GRANULAR_V1_3_DRAFT.csv`: revised 25-case segmentation, broad role, granular subrole, and original-label references.
- `ORIGINAL_REVIEWER_LABEL_LEDGER.csv`: all original nonblank reviewer segment labels, exact text, and source offsets.
- `REVISION_NOTE.md`: changes, counts, and status.
- `REVISION_MANIFEST.json` plus checksum: input/output SHA-256 values.
"""
    (OUTPUT_DIR / "README.md").write_text(readme, encoding="utf-8", newline="\n")

    outputs = [
        "TAQRIB_BOUNDARY_ANNOTATIONS_GRANULAR_V1_3_DRAFT.csv",
        "ORIGINAL_REVIEWER_LABEL_LEDGER.csv", "REVISION_NOTE.md", "README.md",
    ]
    inputs = [ORIGINAL_PATH, GRANULAR_PATH, FROZEN_PATH]
    manifest = {
        "package": "Taqrib boundary annotation granular revision v1.3 draft",
        "status": "revised_copy_pending_user_review; frozen_v1_preserved",
        "generated_by": "dataset_discovery/target_feasibility/revise_taqrib_boundary_granularity_v1_3.py",
        "case_count": len(revised_rows),
        "original_labeled_span_count": len(ledger),
        "original_label_counts": dict(sorted(role_counts.items())),
        "restored_subrole_counts": {k: v for k, v in sorted(subrole_counts.items()) if k.startswith(("nisba", "kunya", "temporal_transition"))},
        "tb022_split": tb022_segments,
        "inputs": {str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path) for path in inputs},
        "outputs": {name: sha256(OUTPUT_DIR / name) for name in outputs},
        "source_reconstruction": "all revised segment sequences checked against the original verbatim entry text",
        "original_label_alignment": "all labeled original snippets found sequentially as exact substrings; offsets stored in ledger",
        "no_rank_labels_assigned": True,
    }
    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    manifest_path = OUTPUT_DIR / "REVISION_MANIFEST.json"
    manifest_path.write_bytes(manifest_bytes)
    (OUTPUT_DIR / "REVISION_MANIFEST.sha256").write_text(
        f"{hashlib.sha256(manifest_bytes).hexdigest()}  REVISION_MANIFEST.json\n",
        encoding="ascii", newline="\n",
    )
    print(json.dumps({
        "output_dir": str(OUTPUT_DIR),
        "case_count": len(revised_rows),
        "original_label_spans": len(ledger),
        "nisba_subroles": {k: v for k, v in sorted(subrole_counts.items()) if k.startswith("nisba")},
        "kunya_subroles": {k: v for k, v in sorted(subrole_counts.items()) if k.startswith("kunya")},
        "tb022": tb022_segments,
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
    }, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
