#!/usr/bin/env python3
"""Create a stratified, human-annotatable set from original Shamela4 tuples.

This script selects review cases only. It never edits or normalizes source data.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dataset_discovery.Shamela4.forensic_verification_v2 import classify_tuple

SUFFIX_CATEGORY = "unnumbered_suffix_variant_without_reversal_evidence"
LOCATOR_RE = re.compile(r"[([{（]\s*\d+\s*/\s*[\d\-–—]+\s*[)\]}）]")
HUMAN_FIELDS = [
    "human_field_1_role", "human_field_2_role", "quotation_boundary",
    "citation_boundary", "number_of_works_referenced",
    "interpretation_confidence", "reviewer_notes",
]


def quotation_citation_separability(category: str) -> str:
    """Return corrected source-ID-level metadata without overreading the class."""
    if category == SUFFIX_CATEGORY:
        return "suffix_occurrences_are_locator_variants; other tuples under this ID may differ"
    if category.startswith("confirmed_") or category == "confirmed_structure_present_with_mixed_occurrences":
        return "not_established_at_source_ID_level; inspect each original tuple"
    return "unresolved_from_automated_pattern; human boundary annotation required"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({
                field: value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, default=str)
                if value is not None else ""
                for field, value in row.items()
            })


def read_criticism(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def grouped_entries(criticism: dict[str, Any]) -> list[tuple[str, list[Any]]]:
    grouped = criticism.get("garh")
    if isinstance(grouped, dict):
        return [(str(label), value if isinstance(value, list) else [value]) for label, value in grouped.items()]
    if isinstance(grouped, list):
        return [(str(item[0]), item[1] if isinstance(item[1], list) else [item[1]])
                for item in grouped if isinstance(item, (list, tuple)) and len(item) >= 2]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--seed", type=int, default=20261111)
    parser.add_argument("--per-stratum", type=int, default=10)
    args = parser.parse_args()

    root = args.root.resolve()
    audit = root / "data/2_interim/shamela4_narrator_audit"
    stage = audit / "stage2_diagnostics"
    v2 = stage / "forensic_verification_v2"
    parquet_path = root / "data/1_raw/Shamela4_Full_DB/_meta/narrators.parquet"
    v2_classification_path = v2 / "VERIFIED_SOURCE_ID_CLASSIFICATION.csv"
    output_dir = (args.out or stage / "forensic_verification_v3").resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    classifications = read_csv(v2_classification_path)
    source_class = {row["source_id"]: row["verified_classification"] for row in classifications}
    flagged_ids = set(source_class)
    occurrences: list[dict[str, Any]] = []
    parquet = pq.ParquetFile(parquet_path)
    for batch in parquet.iter_batches(batch_size=256, columns=["id", "short_name", "criticism_text"]):
        for record in batch.to_pylist():
            narrator_id = record.get("id")
            criticism = read_criticism(record.get("criticism_text"))
            for group_label, entries in grouped_entries(criticism):
                for entry_index, entry in enumerate(entries):
                    if not isinstance(entry, (list, tuple)) or len(entry) != 3:
                        continue
                    first, second, source_id = entry
                    sid = str(source_id)
                    if sid not in flagged_ids or not isinstance(first, str) or not isinstance(second, str):
                        continue
                    result = classify_tuple(first, second)
                    locator_count = len(LOCATOR_RE.findall(first)) + len(LOCATOR_RE.findall(second))
                    suffix = "بدون ترقيم" in first + second
                    occurrences.append({
                        "source_id": sid,
                        "narrator_id": narrator_id,
                        "narrator_name": record.get("short_name") or "",
                        "group_label": group_label,
                        "entry_index": entry_index,
                        "entry": list(entry),
                        "first": first,
                        "second": second,
                        "pattern": result["pattern"],
                        "certainty": result["certainty"],
                        "evidence": result["evidence"],
                        "source_classification": source_class[sid],
                        "locator_count": locator_count,
                        "suffix": suffix,
                    })

    # Put narrow strata first so common cases cannot consume the limited suffix/compound IDs.
    def is_formatting(row: dict[str, Any]) -> bool:
        return row["suffix"] or row["pattern"] == "citation_only_pair"

    def is_compound(row: dict[str, Any]) -> bool:
        return row["pattern"] == "prose_then_locator_bearing_commentary" or row["locator_count"] > 1

    strata = {
        "unnumbered_suffix_or_formatting": lambda row: is_formatting(row),
        "compound_or_multiple_locator": lambda row: is_compound(row) and not is_formatting(row),
        "mixed_source_ID": lambda row: row["source_classification"] == "confirmed_structure_present_with_mixed_occurrences"
            and row["pattern"] != "citation_only_then_locator_bearing_prose",
        "suspected_or_unresolved": lambda row: row["certainty"] in ("suspected_reversal", "suspected_non_reversal", "unresolved"),
        "normal_prose_then_citation": lambda row: row["pattern"] == "locator_bearing_prose_then_citation_only",
        "citation_only_then_locator_bearing_prose": lambda row: row["pattern"] == "citation_only_then_locator_bearing_prose",
    }
    rng = random.Random(args.seed)
    used_ids: set[str] = set()
    selected: list[dict[str, Any]] = []
    pool_sizes: dict[str, int] = {}
    selected_counts: dict[str, int] = {}
    for stratum, predicate in strata.items():
        pool = [row for row in occurrences if predicate(row)]
        by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in pool:
            by_id[row["source_id"]].append(row)
        eligible_ids = [sid for sid in by_id if sid not in used_ids]
        rng.shuffle(eligible_ids)
        pool_sizes[stratum] = len(eligible_ids)
        chosen_ids = eligible_ids[:args.per_stratum]
        if len(chosen_ids) < args.per_stratum:
            raise RuntimeError(
                f"Stratum {stratum!r} has only {len(chosen_ids)} unused source IDs; "
                f"need {args.per_stratum}. Adjust the design before exporting."
            )
        for sid in chosen_ids:
            options = by_id[sid]
            rng.shuffle(options)
            row = options[0].copy()
            row["sampling_stratum"] = stratum
            selected.append(row)
            used_ids.add(sid)
        selected_counts[stratum] = len(chosen_ids)

    output_rows = []
    for case_number, row in enumerate(selected, start=1):
        output_rows.append({
            "case_id": f"TV{case_number:03d}",
            "sampling_stratum": row["sampling_stratum"],
            "source_id": row["source_id"],
            "narrator_id": row["narrator_id"],
            "narrator_name": row["narrator_name"],
            "group_label": row["group_label"],
            "entry_index": row["entry_index"],
            "original_tuple_json": json.dumps(row["entry"], ensure_ascii=False, separators=(",", ":")),
            "original_field_1": row["first"],
            "original_field_2": row["second"],
            "automated_pattern": row["pattern"],
            "automated_certainty": row["certainty"],
            "automated_evidence": row["evidence"],
            "source_ID_level_classification": row["source_classification"],
            "quotation_citation_separability": quotation_citation_separability(row["source_classification"]),
            **{field: "" for field in HUMAN_FIELDS},
        })
    fields = [
        "case_id", "sampling_stratum", "source_id", "narrator_id", "narrator_name", "group_label",
        "entry_index", "original_tuple_json", "original_field_1", "original_field_2",
        "automated_pattern", "automated_certainty", "automated_evidence",
        "source_ID_level_classification", "quotation_citation_separability", *HUMAN_FIELDS,
    ]
    csv_path = output_dir / "TUPLE_MANUAL_VALIDATION.csv"
    write_csv(csv_path, output_rows, fields)

    protocol = f"""# Shamela4 tuple validation protocol (version 3)

## Purpose and boundary

This is a human-validation sample, not a new general-purpose classifier. It asks whether annotators can consistently identify the roles and boundaries of the first two text fields in the original three-element `garh` entries. No field is corrected, swapped, normalized, or deduplicated. The Parquet source and v1/v2 audit outputs remain unchanged. Do not use this exercise to build the narrator graph, set reliability targets, or train models.

## Sample design

The script selected {len(output_rows)} tuples with seed `{args.seed}`, {args.per_stratum} from each of six strata. It samples from the 432 flagged source IDs, uses one tuple per source ID across the sample, and prioritizes the narrow formatting and compound strata before larger pools to reduce overlap. Available unused source IDs at selection time by stratum were: `{json.dumps(pool_sizes, ensure_ascii=False)}`. Selected counts: `{json.dumps(selected_counts, ensure_ascii=False)}`. This is a purposive validation set, not a prevalence sample; its proportions must not be generalized to the corpus.

Each row preserves the source ID, narrator record ID/name, raw `garh` group label, entry index, exact three-element tuple JSON, and exact first/second field strings. The group label is a raw grouping key and must not be assumed to name the historical speaker.

## Structural pattern definitions

- `citation_only_then_locator_bearing_prose`: v2's strict visible pattern: field 1 has a volume/page locator without a recognized prose cue or newline; field 2 has a recognized prose cue before a newline and a locator after it. This is a confirmed tuple shape, not proof of intended field semantics.
- `locator_bearing_prose_then_citation_only`: prose cues occur in field 1 and field 2 has a locator without detected prose cues.
- `prose_then_locator_bearing_commentary`: field 1 contains prose cues, while field 2 contains both locator(s) and prose cues. Multiple citations or editorial/commentary text may coexist.
- `citation_only_pair`: both fields appear locator-bearing and contain no recognized prose cues. This includes some formatting variants; it does not mean two citations to separate works.
- `unresolved_tuple_structure`: the current cue/locator rules do not establish a role or stable boundary. This includes prose without a recognized cue.
- A `mixed_source_ID` sample row comes from an ID with more than one tuple pattern; the row's own automated pattern is still recorded separately.
- `suspected_*` patterns mean a weaker cue combination. They are not confirmation. The validation set includes suspected cases if available and unresolved cases otherwise.

## Human annotation instructions

Annotate from the preserved original fields. Use the full exact text, including line breaks, punctuation, Arabic spelling, and suffixes.

1. `human_field_1_role` and `human_field_2_role`: use one or more of `quotation/evaluation text`, `bibliographic citation`, `volume/page locator`, `secondary citation`, `commentary/editorial text`, `mixed`, `other`, or `unclear`. Explain non-obvious choices in reviewer notes.
2. `quotation_boundary` and `citation_boundary`: record each span as `field_1:start-end` or `field_2:start-end`, with zero-based Unicode code-point offsets and an exclusive end. Multiple disjoint spans may be separated by semicolons. If a boundary cannot be assigned, record `unclear`; if no such span exists, record `not present`.
3. `number_of_works_referenced`: count distinct works only when separable from the text. Multiple volume/page locators within one work count as one work. Use `unknown` when the text does not support a defensible count; do not treat every locator as a separate work.
4. `interpretation_confidence`: use `high`, `medium`, or `low`, based on the visible boundary evidence, not familiarity with a title.
5. `reviewer_notes`: record ambiguity, alternate readings, edition questions, and any external reference consulted. Do not infer the speaker from `group_label` alone.

The annotation columns are intentionally blank in the delivered CSV. `automated_*` fields are machine-generated and must not be copied into human fields.

## Ambiguous cases

Mark a case ambiguous when prose and citation are interleaved; the locator could belong to either text field; more than one work or edition may be present; a newline does not align with a semantic boundary; a work title resembles prose; the prose cue inventory misses the syntax; spelling/formatting changes alter segmentation; or source context is insufficient to identify quotation boundaries. Preserve alternatives in reviewer notes rather than forcing a single interpretation.

## Reviewer agreement and adjudication

Use two Arabic-trained reviewers independently. To reduce anchoring, hide `automated_pattern`, `automated_certainty`, and `source_ID_level_classification` during first-pass annotation, then reveal them only after the human fields are frozen. Compare role labels, boundary offsets, and work counts. Send every disagreement affecting role or boundary to a third reviewer with expertise in hadith/rijāl bibliographic conventions. Retain both initial annotations, the adjudicated result, the rationale, and unresolved dissent in a separate versioned file; do not overwrite this blank template.

Report agreement separately for each field and stratum. Boundary agreement should be measured on span overlap/exactness, not only on categorical labels. Do not resolve disagreement by majority vote when the underlying text supports multiple readings; retain an ambiguous category.

## Dataset evidence, upstream documentation, and hypotheses

### Direct evidence from this dataset

The local input is `narrators.parquet` with columns `id`, `short_name`, `long_name`, `narrator_type`, `biography_text`, and `criticism_text`; its Arrow schema has no key-value metadata. The records' `criticism_text` JSON contains `garh` groups whose observed entries include three elements: two text values followed by an integer. The integer is directly observed as element 3 and is used as `source_id` in the repository's extraction. This confirms storage position and observed association only. The local file does not include a dictionary, foreign-key declaration, or table definition for that integer.

Repository search found earlier prose in `stage2_manual_review.py` asserting entry/page/passage semantics, but those are generated reviewer conclusions, not source metadata. Do not treat them as corroboration. The current v2 semantics note correctly leaves the entity unidentified.

### Upstream and technical documentation search

The official Shamela site was searched for public technical schema/source-ID documentation; no narrator-tuple or `garh` source-ID definition was located. Absence from this search is not proof that private, downloadable, or undocumented schema material does not exist.

The [AuthenticIlm Shamela4 dataset card](https://huggingface.co/datasets/AuthenticIlm/Shamela4_Full_DB) describes its corpus as extracted from Shamela's Lucene/SQLite data and lists a `narrators.parquet` artifact; its published schema examples describe books, pages, and TOC, not the semantics of this `garh` integer. It is a dataset publisher's technical description, not official Shamela documentation.

The third-party [ragaeeb/shamela library](https://github.com/ragaeeb/shamela) documents Shamela v4 master/book database access and mentions narrator export tooling from `S1.db`; the pages inspected do not define the specific `garh` tuple or source-ID foreign key. It is reverse-engineering context, not an upstream authority.

### Hypotheses to keep separate

It is plausible that the integer links an extracted quotation/citation occurrence to some upstream record, because it co-occurs with two text fields in the tuple and repeats in the observed data. It could instead refer to a broader document, source record, or compiler-specific entity. No reviewed evidence establishes which. Do not label it quotation ID, page ID, passage ID, or bibliographic record ID until an upstream DDL/schema or a documented foreign-key join verifies that claim.

## Conclusions this validation can support

If reviewers reliably agree on field roles and boundaries for the sample, the result supports feasibility for those sampled structural strata under the documented protocol. It does not establish error prevalence in all 432 IDs, compiler intent, historical speaker attribution, canonical work/edition identity, source-ID entity semantics, or accuracy of every record. Expand the sample if disagreement clusters by pattern, and obtain the actual upstream schema before defining automated transformations.

## Reproducibility

Run `python dataset_discovery/Shamela4/tuple_validation_v3.py` from the repository root. The manifest records the source and v2-classification hashes, script/test hashes, seed, output hashes, and timestamp. Human annotation should be performed on a copy with a new version identifier.
"""
    protocol_path = output_dir / "TUPLE_VALIDATION_PROTOCOL.md"
    protocol_path.write_text(protocol, encoding="utf-8")

    script_path = root / "dataset_discovery/Shamela4/tuple_validation_v3.py"
    test_path = root / "dataset_discovery/Shamela4/test_tuple_validation_v3.py"
    inputs = [parquet_path, v2_classification_path, root / "dataset_discovery/Shamela4/forensic_verification_v2.py",
              root / "dataset_discovery/Shamela4/test_forensic_verification_v2.py", script_path, test_path]
    outputs = [csv_path, protocol_path]
    manifest = {
        "version": "3.0.0",
        "script": "dataset_discovery/Shamela4/tuple_validation_v3.py",
        "execution_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version,
        "sampling_seed": args.seed,
        "per_stratum_target": args.per_stratum,
        "selected_tuple_count": len(output_rows),
        "selected_unique_source_id_count": len({row["source_id"] for row in output_rows}),
        "selected_strata": selected_counts,
        "eligible_unique_source_ids_before_each_stratum": pool_sizes,
        "source_parquet_read_only": True,
        "inputs": {str(path.relative_to(root)): {"bytes": path.stat().st_size, "sha256": sha256(path)} for path in inputs},
        "outputs": {path.name: {"bytes": path.stat().st_size, "sha256": sha256(path)} for path in outputs},
    }
    (output_dir / "validation_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({"output": str(output_dir), "selected": len(output_rows),
                      "unique_source_ids": len({row['source_id'] for row in output_rows}),
                      "strata": selected_counts, "eligible_unique_source_ids": pool_sizes},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
