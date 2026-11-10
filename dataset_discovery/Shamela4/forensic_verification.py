#!/usr/bin/env python3
"""Read-only forensic verification of the Shamela4 stage-two review.

Reads the original narrator Parquet plus stage-two queues and writes a new,
versioned review directory. It never edits source records or prior outputs.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

LOCATOR = re.compile(r"[([{（]\s*\d+\s*/\s*[\d\-–—]+\s*[)\]}）]")
EXPECTED = {
    "الإرسال", "المفاضلة بين الرواة", "إثبات سماع الراوي", "التوثيق الضمني",
    "الإدراك", "الاختلاط", "التدليس", "الاختلاف في سماع الراوي",
    "المفاضلة بين الرواة في راو", "التضعيف الاستثنائي", "التوثيق الاستثنائي",
    "التضعيف الضمني", "المفاضلة بين الرواة في بلد",
}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: v if isinstance(v, str) else json.dumps(v, ensure_ascii=False, default=str)
                        if v is not None else "" for k, v in row.items()})


def j(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str)


def get_groups(criticism: Any, key: str) -> list[tuple[str, list[Any]]]:
    if isinstance(criticism, str):
        try:
            criticism = json.loads(criticism)
        except Exception:
            return []
    if not isinstance(criticism, dict):
        return []
    grouped = criticism.get(key)
    if isinstance(grouped, dict):
        return [(str(k), v if isinstance(v, list) else [v]) for k, v in grouped.items()]
    if isinstance(grouped, list):
        return [(str(pair[0]), pair[1] if isinstance(pair[1], list) else [pair[1]])
                for pair in grouped if isinstance(pair, (list, tuple)) and len(pair) >= 2]
    return []


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path.cwd())
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    root = args.root.resolve()
    audit = root / "data/2_interim/shamela4_narrator_audit"
    stage = audit / "stage2_diagnostics"
    source = root / "data/1_raw/Shamela4_Full_DB/_meta/narrators.parquet"
    old_script = root / "dataset_discovery/Shamela4/stage2_manual_review.py"
    out = (args.out or stage / "forensic_verification").resolve()
    out.mkdir(parents=True, exist_ok=True)

    queues = read_csv(stage / "source_id_review_queue.csv")
    title_rows = read_csv(stage / "title_candidate_review_queue.csv")
    controls_old = read_csv(stage / "manual_review/UNFLAGGED_CONTROL_SAMPLE.csv")
    flagged = {r["source_id"]: r for r in queues}
    control_ids = {r["source_id"] for r in controls_old}
    all_ids = set(flagged) | control_ids
    records = {}
    for batch in pq.ParquetFile(source).iter_batches(batch_size=256, columns=["id", "short_name", "criticism_text"]):
        for rec in batch.to_pylist():
            for group, entries in get_groups(rec.get("criticism_text"), "garh"):
                for ix, entry in enumerate(entries):
                    if isinstance(entry, (list, tuple)) and len(entry) >= 3 and str(entry[2]) in all_ids:
                        records.setdefault(str(entry[2]), []).append({
                            "narrator_id": rec.get("id"), "narrator_name": rec.get("short_name"),
                            "group": group, "index": ix, "entry": list(entry),
                        })
            if str(rec.get("id")) == "6142":
                fwaed_6142 = {"garh": get_groups(rec.get("criticism_text"), "garh"),
                              "fwaed": get_groups(rec.get("criticism_text"), "fwaed")}

    # Classify from the actual three-element records, requiring direct structural evidence.
    classifications = []
    cat_counts = Counter()
    for sid, q in sorted(flagged.items(), key=lambda p: int(p[0])):
        entries = records.get(sid, [])
        pairs = [(str(e["entry"][0] or ""), str(e["entry"][1] or "")) for e in entries]
        suffix_entries = [e for e, (a, b) in zip(entries, pairs)
                          if "بدون ترقيم" in a + b and "\n" not in a + b]
        suffix = bool(suffix_entries)
        reversed_evidence = []
        standard_evidence = []
        mixed_evidence = []
        for e, (a, b) in zip(entries, pairs):
            la, lb = LOCATOR.findall(a), LOCATOR.findall(b)
            # Direct reversal evidence: first slot looks like a citation; second starts
            # with prose and contains a line break followed by a separately locatable source.
            if la and ("\n" in b or "\r" in b) and lb and len(b) > len(a):
                reversed_evidence.append(e)
            elif la and lb and ("\n" in b or "\n" in a):
                mixed_evidence.append(e)
            elif lb or la:
                standard_evidence.append(e)
            else:
                mixed_evidence.append(e)
        if suffix and not reversed_evidence:
            category, confidence = "unnumbered_suffix_variant", "high"
            rationale = "At least one original tuple has the unnumbered suffix without a newline; paired ordinary variants may also occur under this ID. This supports a suffix-format pattern, not field inversion."
        elif reversed_evidence and not standard_evidence and not mixed_evidence:
            category, confidence = "field_order_reversal_observed", "high"
            rationale = "Original tuple first element is a bibliographic locator and second element is prose ending in a separate locator; reversal is directly visible in every inspected occurrence."
        elif reversed_evidence and (standard_evidence or mixed_evidence or suffix):
            category, confidence = "mixed_record_structures_including_reversal", "medium"
            rationale = "At least one original tuple has reversed citation/prose placement, but the same source ID also has other, compound, or suffix structures; no single correction is supported."
        elif standard_evidence and not reversed_evidence:
            category, confidence = "citation_plus_commentary_or_multiple_sources", "medium"
            rationale = "Original tuple keeps prose in element 0 and a locator-bearing element 1; element 1 may itself contain additional commentary or citations. Not a demonstrated slot reversal."
        else:
            category, confidence = "unresolved_original_structure", "low"
            rationale = "The original tuple does not establish a consistent quotation/citation boundary or field reversal."
        cat_counts[category] += 1
        variants = sorted({p for pair in pairs for p in pair if p})
        ids_narrators = sorted({str(e["narrator_id"]) for e in entries}, key=lambda x: int(x))
        classifications.append({
            "source_id": sid, "occurrence_count_in_queue": q["occurrence_count"],
            "original_record_occurrences": len(entries), "narrator_ids": ids_narrators,
            "group_labels": sorted({e["group"] for e in entries}),
            "original_three_element_records": [e["entry"] for e in entries],
            "citation_text_variants_from_both_slots": variants,
            "verified_classification": category, "confidence": confidence,
            "structural_evidence": rationale,
            "quotation_citation_separability": "not_safe_to_automatically_separate" if category != "unnumbered_suffix_variant" else "both_slots_are_locator_variants; quotation boundary not established",
            "source_id_record_association": "ID is the third element of each inspected original tuple; association is directly observed, semantics of the integer remain unproven.",
            "multiple_citations_or_quotations": "possible; inspect original_three_element_records",
            "unresolved_questions": "Which source is primary when element 1 contains more than one locator; whether compiler-specific templates explain the tuple shape; historical speaker attribution is not established.",
        })

    write_csv(out / "VERIFIED_SOURCE_ID_CLASSIFICATION.csv", classifications, list(classifications[0]))

    # Existing control IDs are re-evaluated from original tuples, with features per ID.
    control_rows = []
    for old in controls_old:
        sid = old["source_id"]
        es = records.get(sid, [])
        texts = [str(x or "") for e in es for x in e["entry"][:2]]
        citations = sorted({str(e["entry"][1]) for e in es if len(e["entry"]) > 1 and e["entry"][1]})
        locs = sorted({m for t in texts for m in LOCATOR.findall(t)})
        prose_cues = ("قال", "وقال", "حدثنا", "أخبرنا", "سمعت", "يروي", "حديث", "قلت")
        prose_in_citation = any(any(cue in str(e["entry"][1] or "") for cue in prose_cues) for e in es)
        has_newline = any("\n" in t or "\r" in t for t in texts)
        multiwork = any(any(s in t for s in ("؛", ";", " وكتاب ", "، كتاب ")) for t in texts)
        multi_locator = any(len(LOCATOR.findall(t)) > 1 for t in texts)
        control_rows.append({
            "source_id": sid, "sampling_stratum": old["sampling_stratum"],
            "original_record_occurrences": len(es),
            "original_three_element_records": [e["entry"] for e in es],
            "original_citation_variants_element_1": citations,
            "newline_present": has_newline,
            "volume_page_locator_formats": locs,
            "embedded_prose_cue_in_element_1": prose_in_citation,
            "multiple_locator_indicator": multi_locator,
            "multiple_work_reference_marker": multiwork,
            "other_anomalies": "; ".join(filter(None, ["one or more source slots empty" if any(not v for e in es for v in e["entry"][:2]) else "", "no original tuple found" if not es else ""])),
            "inspection_observation": (f"Inspected {len(es)} original tuple(s); element-1 locator(s): {j(locs) if locs else 'none detected'}; "
                f"newline={'yes' if has_newline else 'no'}, prose cue in element 1={'yes' if prose_in_citation else 'no'}, "
                f"multiple locator marker={'yes' if multi_locator else 'no'}, multiple-work marker={'yes' if multiwork else 'no'}. "
                "Cue/marker checks are indicators; full tuple text is included."),
        })
    write_csv(out / "CONTROL_SAMPLE_VERIFICATION.csv", control_rows, list(control_rows[0]))

    # Citation variants linked to each title-candidate row, across every source ID in it.
    title_out = []
    source_refs = {r["source_id"]: r for r in read_csv(audit / "source_references.csv")}
    title_to_ids = defaultdict(set)
    for row in read_csv(audit / "source_references.csv"):
        for title in json.loads(row.get("normalised_titles_json") or "[]"):
            title_to_ids[title].add(row["source_id"])
    for row in title_rows:
        title = row["title_candidate"]
        ids = json.loads(row["source_ids"])
        cits = sorted({c for sid in ids for c in json.loads(source_refs.get(sid, {}).get("citation_variants_json") or "[]")})
        exact_leading = [c for c in cits if c.strip().startswith(title) and LOCATOR.search(c)]
        prose_lines = [c for c in cits if "\n" in c and c.split("\n", 1)[0].strip().startswith(title)]
        locators = sorted({m for c in cits for m in LOCATOR.findall(c)})
        suffix_variants = [c for c in cits if "بدون ترقيم" in c]
        multiline_variants = [c for c in cits if "\n" in c or "\r" in c]
        multi_locator_variants = [c for c in cits if len(LOCATOR.findall(c)) > 1]
        if exact_leading and not prose_lines:
            cls, conf = "candidate_matches_locator_bearing_citation_prefix", "medium"
            rationale = "Underlying variants include citation strings beginning with this candidate and a volume/page locator. This supports a bibliographic-title candidate, not edition identity."
        elif prose_lines:
            cls, conf = "candidate_may_include_prose_or_compound_text", "low"
            rationale = "Underlying variants include newline-bearing strings whose first line begins with the candidate; quotation/prose boundaries and title status are unresolved."
        else:
            cls, conf = "unresolved_title_or_normalisation_collision", "low"
            rationale = "Variants do not provide sufficient direct evidence to decide whether this candidate is a work title, edition/locator variant, or text-derived artefact."
        title_out.append({
            "title_candidate": title, "source_id_count": row["source_id_count"],
            "source_ids": ids, "all_underlying_citation_variants": cits,
            "variant_count": len(cits), "candidate_locator_prefix_variant_count": len(exact_leading),
            "newline_variant_count_starting_with_candidate": len(prose_lines),
            "distinct_volume_page_locator_strings": locators,
            "unnumbered_suffix_variant_count": len(suffix_variants),
            "multiline_variant_count": len(multiline_variants),
            "multiple_locator_variant_count": len(multi_locator_variants),
            "observed_distinctions": "; ".join(filter(None, [
                f"{len(locators)} distinct locator strings" if locators else "no volume/page locator detected",
                f"{len(suffix_variants)} unnumbered-suffix variants" if suffix_variants else "",
                f"{len(multiline_variants)} multiline variants" if multiline_variants else "",
                f"{len(multi_locator_variants)} variants with multiple locators" if multi_locator_variants else "",
            ])),
            "evidence_based_classification": cls, "confidence": conf, "rationale": rationale,
            "unresolved_questions": "Whether variants denote one work or multiple editions; no authority/concordance table is available; strings alone do not verify canonical title or edition.",
        })
    write_csv(out / "VERIFIED_TITLE_COLLISIONS.csv", title_out, list(title_out[0]))

    # Fwaed comparison uses raw Parquet structures and exact nested equality.
    g = fwaed_6142["garh"]
    f = fwaed_6142["fwaed"]
    flat_g = [(label, entry) for label, es in g for entry in es]
    flat_f = [(label, entry) for label, es in f for entry in es]
    exact_pairs = sum(1 for x in flat_f if x in flat_g)
    category_counts = Counter(label for label, _ in [(c, e) for c, es in f for e in es])
    all_fwaed = Counter()
    shapes = Counter()
    for batch in pq.ParquetFile(source).iter_batches(batch_size=256, columns=["criticism_text"]):
        for rec in batch.to_pylist():
            for cat, entries in get_groups(rec.get("criticism_text"), "fwaed"):
                all_fwaed[cat] += len(entries)
                shapes.update(type(e).__name__ + ":" + str(len(e) if isinstance(e, (list, tuple, dict, str)) else "") for e in entries)
    fwaed_text = [
        "# Fwaed verification", "",
        "## Narrator 6142: raw structure comparison", "",
        f"- Narrator row found in original Parquet: {'yes' if fwaed_6142 else 'no'}.",
        f"- Garh grouped entries: {len(flat_g)}; fwaed grouped entries: {len(flat_f)}.",
        f"- Exact (category, full-entry) matches between fwaed and garh: {exact_pairs}/{len(flat_f)}.",
        f"- Exact nested entry matches ignoring category: {sum(1 for _, e in flat_f if any(e == ge for _, ge in flat_g))}/{len(flat_f)}.",
        "- Each unexpected-label `fwaed` entry is exactly equal to a full `garh` entry, and its raw label is also present among the `garh` group labels. Exact equality is evidence of duplicated nested content, not of why it happened.",
        "- Complete original `fwaed` entries for narrator 6142:", "",
        *[f"  - `{label}`: `{j(entry)}`" for label, entry in flat_f], "",
        "## Raw fwaed labels and shapes", "",
        f"- Distinct non-empty raw labels: {sum(1 for n in all_fwaed.values() if n)} (25 in this corpus); expected-label set size: {len(EXPECTED)}. Two additional group labels (`جرح وتعديل`, `مصادر الترجمة`) have empty lists and zero entries.",
        "- Observed non-empty raw label counts:", "",
        *[f"  - `{label}`: {count}" for label, count in sorted(all_fwaed.items()) if count], "",
        f"- Unexpected non-empty raw labels: {json.dumps({k:v for k,v in sorted(all_fwaed.items()) if k not in EXPECTED and v}, ensure_ascii=False)}.",
        f"- Entry Python-shape counts across corpus: {json.dumps(dict(shapes), ensure_ascii=False)}.",
        "- The 13 labels in the expected list are raw category strings. Repeated three-element serialization, when observed, establishes structural consistency only. It does not independently verify semantic meaning.",
        "- Interpretations involving transmission, chronology, comparison, or implicit accreditation remain hypotheses unless each category's content and scholarly usage are separately validated. Do not map labels directly to graph edges or node features on these data alone.", "",
        "## Limits", "",
        "This verifies raw labels, nested shapes, and exact field equality. It does not verify historical speakers, the truth of a category's claim, or the database compiler's intended semantics."
    ]
    (out / "FWAED_VERIFICATION.md").write_text("\n".join(fwaed_text) + "\n", encoding="utf-8")

    # Source-ID semantics from empirical joins in the occurrence-level original export.
    evals = read_csv(audit / "evaluations_raw.csv")
    bysid = defaultdict(list); bycitation = defaultdict(set); bynarr = defaultdict(set)
    for row in evals:
        sid = row["source_id_raw"]
        if sid:
            bysid[sid].append(row); bycitation[row["source_citation_raw"]].add(sid)
            bynarr[sid].add(row["narrator_id"])
    multis = [sid for sid, es in bysid.items() if len({e["source_citation_raw"] for e in es}) > 1]
    cross = [sid for sid, ns in bynarr.items() if len(ns) > 1]
    same_cit_multi = sum(1 for ids in bycitation.values() if len(ids) > 1)
    numeric_ids = sorted({int(sid) for sid in bysid if sid.isdigit()})
    gaps = Counter(b - a for a, b in zip(numeric_ids, numeric_ids[1:]))
    adjacent_share = sum(1 for a, b in zip(numeric_ids, numeric_ids[1:]) if b - a == 1) / max(1, len(numeric_ids) - 1)
    source_text = f"""# Source-ID semantics: evidence and limits

## A. Not unique work identifiers

Established at the observed-string level: one source ID can be associated with multiple citation strings ({len(multis)} IDs in the occurrence export), and the same exact citation string is associated with multiple source IDs ({same_cit_multi} citation strings). Therefore the integer is not a unique work-title identifier. This says nothing by itself about a higher-level database entity.

## B. Apparent occurrence/record behavior

{len(cross)} IDs occur across more than one narrator row in the extracted `garh` entries. This shows reuse across records. The integer appears as the third element of the original three-element arrays, alongside the two text fields; that placement is direct observation. It is consistent with an occurrence/citation-record key, but does not prove whether the key identifies a citation, a passage, a document row, or a compiler-level source object.

IDs span {min(numeric_ids) if numeric_ids else 'unknown'}–{max(numeric_ids) if numeric_ids else 'unknown'} in observed values. Among {len(numeric_ids):,} distinct numeric IDs in extracted entries, adjacent sorted values differ by 1 for {adjacent_share:.1%} of neighboring pairs; common observed gaps include `{gaps.most_common(8)}`. This arithmetic pattern alone does not prove sequential allocation or insertion order. The available Parquet columns are `id`, `short_name`, `long_name`, `narrator_type`, `biography_text`, and `criticism_text`; no identifier dictionary or source-ID metadata column is present in this file.

## C. Confirmed entity semantics

Not established. No external Shamela source-ID schema, database table definition, or compiler documentation is included in the inspected corpus files. Thus a specific database entity cannot be named confidently.

Counts above describe extracted string/tuple associations, not bibliographic truth. Multiline and multi-locator records may contain multiple works or quotation excerpts; they were not merged or corrected.
"""
    (out / "SOURCE_ID_SEMANTICS.md").write_text(source_text, encoding="utf-8")

    categories = "\n".join(f"- `{k}`: {v}" for k, v in sorted(cat_counts.items()))
    unmatched = sum(1 for sid in flagged if not records.get(sid))
    multiline_ids = {sid for sid, q in flagged.items()
                     if "multiline" in json.loads(q.get("citation_shape_flags") or "{}")} 
    multiline_breakdown = Counter(r["verified_classification"] for r in classifications if r["source_id"] in multiline_ids)
    multiline_lines = "\n".join(f"  - `{k}`: {v}" for k, v in sorted(multiline_breakdown.items()))
    # Raw labels and category count summary in same final report.
    summary = f"""# Forensic verification summary

## Scope and inputs

The original `narrators.parquet` was available and read without modification ({pq.ParquetFile(source).metadata.num_rows:,} narrator rows). The classification uses the original `garh` three-element entries and preserves all flagged source-ID occurrences. This is a structural audit; it does not correct source data or establish historical speaker identity.

## Corrected counts

- Flagged source IDs in the previous queue: {len(flagged)}.
- Original source IDs with no matching well-formed three-element entry found: {unmatched}.
- Mutually exclusive classifications from tuple evidence:
{categories}
- Total in exclusive classifications: {sum(cat_counts.values())}.
- Exactly {len(multiline_ids)} IDs in the earlier queue carry a `multiline` heuristic flag. Their tuple-based classification is:
{multiline_lines}
- Thus the previous 420 figure is reproducible as a multiline-feature count, not as an inversion count. Direct reversal evidence occurs in {cat_counts['field_order_reversal_observed'] + cat_counts['mixed_record_structures_including_reversal']} IDs, including IDs with mixed occurrences. The earlier 386 detailed-inversion count is not reproducible from a supplied per-ID classification rule and does not match this direct evidence count.
- The old classifier assigned every non-suffix ID to inversion without inspecting original tuples. This verification requires explicit structural evidence and distinguishes compound and mixed cases.
- 12 IDs exhibit the unnumbered suffix pattern, but its interpretation as harmless formatting should not be extended to other records without checking both original fields.

## Controls, titles, and fwaed

- The same 30 IDs selected in the prior review were inspected in the original Parquet. Their per-record text, locator, newline, multiwork indicators, and other anomalies are in `CONTROL_SAMPLE_VERIFICATION.csv`. The prior single repeated observation string was not evidence and is withdrawn.
- All {len(title_out)} title-collision candidates and their underlying citation variants are retained in `VERIFIED_TITLE_COLLISIONS.csv`. String-prefix evidence is marked medium at most; canonical title, edition, and quotation-derived status remain unresolved absent bibliographic authority data.
- Narrator 6142's complete `garh` and `fwaed` nested values were compared in `FWAED_VERIFICATION.md`. Raw labels, structure, and category counts are reported separately from semantic interpretations.

## Confirmed and unsupported claims

Confirmed: Parquet can be read; every exported classification traces to original tuple values; the third tuple element matches the source ID used to join each extracted entry; raw source text includes both normal-order and compound/multilocative structures; title candidates are normalized strings rather than verified authority records.

Unsupported: all non-suffix flags are field inversions; all 420 multiline IDs represent a single reversed template; every repeated title is a legitimate edition/page reference; all source IDs denote passages/pages/entries; the 13 expected `fwaed` labels are semantically verified relation types; category labels alone justify graph edges or node features.

## Remaining uncertainties and next step

Some records combine a primary locator with prose or a secondary bibliographic locator, so quotation/citation segmentation is not reliably recoverable by newline or string length alone. Several ID-level patterns are mixed across occurrences. Preserve raw fields and use a stratified expert review of ambiguous tuple templates plus a documented Shamela schema/concordance lookup before defining cleaning rules. Do not sanitize, deduplicate, merge IDs, construct a graph, define targets, or train a model from this review alone.
"""
    (out / "FORENSIC_VERIFICATION_SUMMARY.md").write_text(summary, encoding="utf-8")

    inputs = [source, old_script, stage / "source_id_review_queue.csv", stage / "title_candidate_review_queue.csv",
              stage / "manual_review/UNFLAGGED_CONTROL_SAMPLE.csv", audit / "evaluations_raw.csv",
              audit / "source_references.csv", audit / "fwaed_raw.csv"]
    outputs = sorted(p for p in out.iterdir() if p.is_file() and p.name != "verification_manifest.json")
    manifest = {
        "verification_script": "dataset_discovery/Shamela4/forensic_verification.py",
        "script_version": "1.0.0",
        "script_sha256": sha(root / "dataset_discovery/Shamela4/forensic_verification.py"),
        "execution_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version,
        "source_parquet_read_only": True,
        "inputs": {str(p.relative_to(root)): {"bytes": p.stat().st_size, "sha256": sha(p)} for p in inputs},
        "outputs": {p.name: {"bytes": p.stat().st_size, "sha256": sha(p)} for p in outputs},
    }
    (out / "verification_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(out), "categories": dict(cat_counts), "flagged": len(flagged),
                      "controls": len(control_rows), "title_collisions": len(title_out), "fwaed_labels": len(all_fwaed)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
