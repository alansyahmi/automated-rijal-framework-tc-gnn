#!/usr/bin/env python3
"""Version-two read-only forensic verification of the Shamela4 stage-two review.

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
PROSE_CUES = (
    "قال", "وقال", "حدثنا", "حدثني", "أخبرنا", "أخبرني", "سمعت",
    "يروي", "روى", "قلت", "أثبت", "لم يسمع", "لا يسمع",
)


def _locator_spans(text: str) -> list[tuple[int, int]]:
    return [m.span() for m in LOCATOR.finditer(text)]


def _has_prose_cue(text: str) -> bool:
    return any(re.search(
        rf"(?<![\u0600-\u06FF]){re.escape(cue)}(?![\u0600-\u06FF])", text
    ) for cue in PROSE_CUES)


def _citation_only(text: str) -> bool:
    """Conservative shape check; it does not validate bibliographic identity."""
    return bool(_locator_spans(text)) and not _has_prose_cue(text) and not any(c in text for c in "\n\r")


def _locator_bearing_prose(text: str) -> bool:
    return bool(_locator_spans(text)) and _has_prose_cue(text)


def _prose_precedes_secondary_locator(text: str) -> bool:
    """Require prose before the line break and a citation locator after it."""
    newline_positions = [p for p in (text.find("\n"), text.find("\r")) if p >= 0]
    if not newline_positions:
        return False
    boundary = min(newline_positions)
    before, after = text[:boundary], text[boundary + 1:]
    return _has_prose_cue(before) and not _locator_spans(before) and bool(_locator_spans(after))


def classify_tuple(first: str, second: str) -> dict[str, str]:
    """Classify slot shape, separating direct evidence from suspicion.

    "Confirmed" means the visible tuple pattern is unambiguous under these
    conservative lexical/locator rules. It does not establish compiler intent.
    """
    first, second = str(first or ""), str(second or "")
    first_citation = _citation_only(first)
    second_citation = _citation_only(second)
    first_prose = _has_prose_cue(first)
    second_prose = _has_prose_cue(second)
    first_locators, second_locators = _locator_spans(first), _locator_spans(second)
    if first_citation and _locator_bearing_prose(second) and _prose_precedes_secondary_locator(second):
        return {"pattern": "citation_only_then_locator_bearing_prose",
                "certainty": "confirmed_structure",
                "evidence": "slot 0 is locator-bearing without prose cues; slot 1 has prose cues and a later locator on a new line"}
    if first_citation and _locator_bearing_prose(second):
        return {"pattern": "citation_like_then_locator_bearing_prose",
                "certainty": "suspected_reversal",
                "evidence": "slot 0 is citation-like and slot 1 has prose cues plus a locator, but the boundary/order is not explicit enough"}
    if first_prose and second_citation:
        return {"pattern": "locator_bearing_prose_then_citation_only",
                "certainty": "confirmed_non_reversal",
                "evidence": "slot 0 contains prose cues and slot 1 is locator-bearing without prose cues"}
    if first_prose and second_locators and second_prose:
        return {"pattern": "prose_then_locator_bearing_commentary",
                "certainty": "confirmed_non_reversal",
                "evidence": "slot 0 contains prose cues; slot 1 begins as locator-bearing commentary, so the tuple does not show citation-only slot 0"}
    if first_citation and second_citation:
        return {"pattern": "citation_only_pair",
                "certainty": "confirmed_non_reversal",
                "evidence": "both slots are locator-bearing and have no detected prose cues"}
    if first_prose and second_locators:
        return {"pattern": "prose_then_locator_bearing_field",
                "certainty": "suspected_non_reversal",
                "evidence": "slot 0 has prose cues and slot 1 has a locator; slot 1 contains mixed/unclear text"}
    if first_locators and second_prose:
        return {"pattern": "locator_then_prose_without_clear_secondary_locator",
                "certainty": "suspected_reversal",
                "evidence": "slot 0 has a locator and slot 1 prose cues, but the required locator-bearing prose pattern is incomplete"}
    return {"pattern": "unresolved_tuple_structure", "certainty": "unresolved",
            "evidence": "locator and prose cues do not establish a stable field-order pattern"}


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
    out = (args.out or stage / "forensic_verification_v2").resolve()
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

    # Classify each actual tuple first, then aggregate only as far as evidence allows.
    classifications = []
    cat_counts = Counter()
    certainty_counts = Counter()
    tuple_pattern_counts = Counter()
    for sid, q in sorted(flagged.items(), key=lambda p: int(p[0])):
        entries = records.get(sid, [])
        pairs = [(str(e["entry"][0] or ""), str(e["entry"][1] or "")) for e in entries]
        tuple_reviews = []
        for e in entries:
            first, second = str(e["entry"][0] or ""), str(e["entry"][1] or "")
            result = classify_tuple(first, second)
            tuple_pattern_counts[result["pattern"]] += 1
            certainty_counts[result["certainty"]] += 1
            tuple_reviews.append({"narrator_id": e["narrator_id"], "group": e["group"],
                                  "entry_index": e["index"], "pattern": result["pattern"],
                                  "certainty": result["certainty"], "evidence": result["evidence"]})
        patterns = Counter(r["pattern"] for r in tuple_reviews)
        confirmed = patterns["citation_only_then_locator_bearing_prose"]
        suspected = sum(n for p, n in patterns.items() if p in {
            "citation_like_then_locator_bearing_prose",
            "locator_then_prose_without_clear_secondary_locator",
        })
        nonreversal = sum(n for p, n in patterns.items() if p in {
            "locator_bearing_prose_then_citation_only", "prose_then_locator_bearing_commentary",
            "citation_only_pair", "prose_then_locator_bearing_field",
        })
        unresolved = patterns["unresolved_tuple_structure"]
        suffix = any("بدون ترقيم" in a + b and "\n" not in a + b for a, b in pairs)
        if confirmed and (suspected or nonreversal or unresolved):
            category, confidence = "confirmed_structure_present_with_mixed_occurrences", "medium"
            rationale = "At least one tuple shows the confirmed citation-only slot 0 / locator-bearing prose slot 1 pattern; this ID also has suspected, non-reversal, or unresolved tuple structures."
        elif confirmed:
            category, confidence = "confirmed_citation_only_then_locator_bearing_prose", "high"
            rationale = "Every inspected tuple for this ID shows citation-only text in slot 0 and locator-bearing prose in slot 1. This confirms a slot pattern, not compiler intent or a safe automatic swap."
        elif suspected:
            category, confidence = "suspected_reversal_pattern", "low"
            rationale = "At least one tuple is citation-like in slot 0 and prose-bearing in slot 1, but the stronger citation-only / separated-secondary-locator evidence is absent."
        elif suffix and not confirmed and not suspected:
            category, confidence = "unnumbered_suffix_variant_without_reversal_evidence", "high"
            rationale = "At least one tuple contains the unnumbered suffix; other occurrences may be ordinary quote/citation pairs. No confirmed or suspected reversal tuple is present for this ID."
        elif nonreversal and not suspected and not unresolved:
            category, confidence = "confirmed_non_reversal_or_compound_structure", "medium"
            rationale = "The inspected tuples put prose in slot 0, or both slots are citation-only; some slot 1 fields contain commentary/multiple locators."
        else:
            category, confidence = "unresolved_or_mixed_tuple_structure", "low"
            rationale = "Tuple evidence does not establish a single stable citation/prose order; inspect the per-occurrence classifications and original arrays."
        cat_counts[category] += 1
        variants = sorted({p for pair in pairs for p in pair if p})
        ids_narrators = sorted({str(e["narrator_id"]) for e in entries}, key=lambda x: int(x))
        classifications.append({
            "source_id": sid, "occurrence_count_in_queue": q["occurrence_count"],
            "original_record_occurrences": len(entries), "narrator_ids": ids_narrators,
            "group_labels": sorted({e["group"] for e in entries}),
            "original_three_element_records": [e["entry"] for e in entries],
            "tuple_level_classifications": tuple_reviews,
            "tuple_pattern_counts": dict(patterns),
            "confirmed_reversal_structure_occurrences": confirmed,
            "suspected_reversal_occurrences": suspected,
            "non_reversal_or_compound_occurrences": nonreversal,
            "unresolved_occurrences": unresolved,
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
    title_variant_out = []
    source_refs = {r["source_id"]: r for r in read_csv(audit / "source_references.csv")}
    title_to_ids = defaultdict(set)
    for row in read_csv(audit / "source_references.csv"):
        for title in json.loads(row.get("normalised_titles_json") or "[]"):
            title_to_ids[title].add(row["source_id"])
    for row in title_rows:
        title = row["title_candidate"]
        ids = json.loads(row["source_ids"])
        citation_map = {sid: json.loads(source_refs.get(sid, {}).get("citation_variants_json") or "[]") for sid in ids}
        cits = sorted({c for variants in citation_map.values() for c in variants})
        title_variant_out.extend({"title_candidate": title, "source_id": sid, "citation_variant": citation}
                                for sid, variants in citation_map.items() for citation in variants)
        exact_leading = [c for c in cits if c.strip().startswith(title) and LOCATOR.search(c)]
        prose_lines = [c for c in cits if "\n" in c and c.split("\n", 1)[0].strip().startswith(title)]
        locators = sorted({m for c in cits for m in LOCATOR.findall(c)})
        suffix_variants = [c for c in cits if "بدون ترقيم" in c]
        multiline_variants = [c for c in cits if "\n" in c or "\r" in c]
        multi_locator_variants = [c for c in cits if len(LOCATOR.findall(c)) > 1]
        prose_cues_in_title = [cue for cue in ("مقبول", "ضعيف", "متروك", "وقال", "يروي", "سكتوا", "لا يتابع", "تغير", "اختلط", "لم يسمع", "لم يدرك") if cue in title]
        if prose_cues_in_title:
            cls, conf = "suspected_prose_or_evaluation_in_candidate", "low"
            rationale = ("Candidate contains a prose/evaluation cue and underlying locator-bearing variants; this makes quotation-text contamination plausible but does not prove it. "
                         "No authority source was available to verify a genuine title or separate editions.")
        elif exact_leading:
            cls, conf = "locator_bearing_candidate_title_unverified", "low"
            rationale = "Underlying variants include strings beginning with this candidate and a volume/page locator. This does not establish that the prefix is a genuine work title, edition, or locator-free title."
        else:
            cls, conf = "unresolved_title_or_normalisation_collision", "low"
            rationale = "Variants do not provide sufficient direct evidence to decide whether this candidate is a work title, edition/locator variant, or text-derived artefact."
        title_out.append({
            "title_candidate": title, "source_id_count": row["source_id_count"],
            "sample_source_ids": ids[:10],
            "variant_count": len(cits), "candidate_locator_prefix_variant_count": len(exact_leading),
            "newline_variant_count_starting_with_candidate": len(prose_lines),
            "sample_citation_variants": cits[:5],
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
            "review_status": "evidence_inventory_only; independent bibliographic review pending",
            "unresolved_questions": "Whether variants denote one work or multiple editions; no authority/concordance table is available; strings alone do not verify canonical title or edition.",
        })
    write_csv(out / "VERIFIED_TITLE_COLLISIONS.csv", title_out, list(title_out[0]))
    write_csv(out / "TITLE_COLLISION_CITATION_VARIANTS.csv", title_variant_out,
              ["title_candidate", "source_id", "citation_variant"])

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
    confirmed_reversal_ids = cat_counts["confirmed_citation_only_then_locator_bearing_prose"] + cat_counts["confirmed_structure_present_with_mixed_occurrences"]
    suspected_reversal_ids = cat_counts["suspected_reversal_pattern"]
    confirmed_reversal_occurrences = tuple_pattern_counts["citation_only_then_locator_bearing_prose"]
    suspected_reversal_occurrences = tuple_pattern_counts["citation_like_then_locator_bearing_prose"] + tuple_pattern_counts["locator_then_prose_without_clear_secondary_locator"]
    occurrence_patterns = "\n".join(f"- `{k}`: {v}" for k, v in sorted(tuple_pattern_counts.items()))
    occurrence_certainties = "\n".join(f"- `{k}`: {v}" for k, v in sorted(certainty_counts.items()))
    # Raw labels and category count summary in same final report.
    summary = f"""# Forensic verification summary

## Scope and inputs

The original `narrators.parquet` was available and read without modification ({pq.ParquetFile(source).metadata.num_rows:,} narrator rows). The classification uses the original `garh` three-element entries and preserves all flagged source-ID occurrences. This is a structural audit; it does not correct source data or establish historical speaker identity.

## Corrected counts

- Flagged source IDs in the previous queue: {len(flagged)}.
- Original source IDs with no matching well-formed three-element entry found: {unmatched}.
- Mutually exclusive source-ID classifications:
{categories}
- Total in exclusive classifications: {sum(cat_counts.values())}.

### Classifier rule and examples

The confirmed slot pattern requires slot 0 to contain a volume/page locator without a recognized prose cue or newline. Slot 1 must contain a recognized prose cue before a newline, with a locator after that newline. This specifically distinguishes locator-bearing prose from citation-only fields. Cue matching uses whole Arabic tokens/phrases; cues are indicators, not a language model or bibliographic parser.

Representative original tuples in `test_forensic_verification_v2.py`: source ID 137006 is a positive slot-pattern case; 25200 is a normal prose-then-citation negative; 92839 is a compound citation-plus-commentary negative; the suffix-bearing 25200 tuple is a citation-only-pair negative. These establish classifier behavior on examples, not corpus-wide compiler intent.

### Confirmed structural patterns

- {cat_counts['confirmed_citation_only_then_locator_bearing_prose']} IDs have only tuples matching the explicit pattern: citation-only slot 0 followed by locator-bearing prose in slot 1, with a newline before a later locator.
- {cat_counts['confirmed_structure_present_with_mixed_occurrences']} additional IDs contain at least one such tuple but also mixed, suspected, or unresolved tuple structures.
- Combined, {confirmed_reversal_ids} IDs contain {confirmed_reversal_occurrences} tuple occurrences matching this confirmed shape. This is structural confirmation under the documented cue rules, not proof of compiler intent or a safe swap instruction.
- `{cat_counts['unnumbered_suffix_variant_without_reversal_evidence']}` IDs contain the unnumbered suffix pattern with no detected reversal evidence.

### Suspected or unresolved patterns

- {suspected_reversal_ids} IDs have at least one weaker suspected-reversal tuple and no confirmed reversal tuple; {suspected_reversal_occurrences} suspected tuple occurrences also occur within mixed IDs that have confirmed tuple evidence.
- {cat_counts['confirmed_non_reversal_or_compound_structure']} IDs have only observed non-reversal/compound patterns under these rules.
- {cat_counts['unresolved_or_mixed_tuple_structure']} IDs remain unresolved or internally mixed without a confirmed reversal tuple.
- Tuple-level pattern counts:
{occurrence_patterns}
- Tuple-level certainty counts:
{occurrence_certainties}
- The earlier 420 count is a multiline-feature count, not an inversion count. The earlier 386 detailed-inversion figure is not reproducible from a supplied per-ID rule. Both should be treated as unverified inversion counts.

## Controls, titles, and fwaed

- The same 30 IDs selected in the prior review were inspected in the original Parquet. Their per-record text, locator, newline, multiwork indicators, and other anomalies are in `CONTROL_SAMPLE_VERIFICATION.csv`. The prior single repeated observation string was not evidence and is withdrawn.
- All {len(title_out)} title-collision candidates have compact case summaries in `VERIFIED_TITLE_COLLISIONS.csv`; source-ID/citation associations are in `TITLE_COLLISION_CITATION_VARIANTS.csv` ({len(title_variant_out)} rows, one association per row to avoid oversized cells). These are evidence inventories and conservative triage labels, not an independent expert review of all 47 cases. Canonical title, edition, and quotation-derived status remain open pending that review and bibliographic authority evidence. The v2 manifest records non-zero byte size and SHA-256 for both CSVs.
- Narrator 6142's complete `garh` and `fwaed` nested values were compared in `FWAED_VERIFICATION.md`. Raw labels, structure, and category counts are reported separately from semantic interpretations.

## Confirmed and unsupported claims

Confirmed: Parquet can be read; every exported classification traces to original tuple values; the third tuple element matches the source ID used to join each extracted entry; raw source text includes both normal-order and compound/multilocative structures; title candidates are normalized strings rather than verified authority records.

Unsupported: all non-suffix flags are field inversions; all 420 multiline IDs represent a single reversed template; every repeated title is a legitimate edition/page reference; all source IDs denote passages/pages/entries; the 13 expected `fwaed` labels are semantically verified relation types; category labels alone justify graph edges or node features.

## Remaining uncertainties and next step

Some records combine a primary locator with prose or a secondary bibliographic locator, so quotation/citation segmentation is not reliably recoverable by newline or string length alone. Several ID-level patterns are mixed across occurrences. Preserve raw fields and use a stratified expert review of ambiguous tuple templates plus a documented Shamela schema/concordance lookup before defining cleaning rules. Do not sanitize, deduplicate, merge IDs, construct a graph, define targets, or train a model from this review alone.
"""
    (out / "FORENSIC_VERIFICATION_SUMMARY.md").write_text(summary, encoding="utf-8")

    inputs = [source, old_script, root / "dataset_discovery/Shamela4/forensic_verification_v2.py",
              root / "dataset_discovery/Shamela4/test_forensic_verification_v2.py",
              stage / "source_id_review_queue.csv", stage / "title_candidate_review_queue.csv",
              stage / "manual_review/UNFLAGGED_CONTROL_SAMPLE.csv", audit / "evaluations_raw.csv",
              audit / "source_references.csv", audit / "fwaed_raw.csv"]
    outputs = sorted(p for p in out.iterdir() if p.is_file() and p.name != "verification_manifest.json")
    manifest = {
        "verification_script": "dataset_discovery/Shamela4/forensic_verification_v2.py",
        "script_version": "2.0.0",
        "script_sha256": sha(root / "dataset_discovery/Shamela4/forensic_verification_v2.py"),
        "execution_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version,
        "source_parquet_read_only": True,
        "inputs": {str(p.relative_to(root)): {"bytes": p.stat().st_size, "sha256": sha(p)} for p in inputs},
        "outputs": {p.name: {"bytes": p.stat().st_size, "sha256": sha(p)} for p in outputs},
    }
    (out / "verification_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(out), "categories": dict(cat_counts),
                      "tuple_pattern_counts": dict(tuple_pattern_counts), "flagged": len(flagged),
                      "controls": len(control_rows), "title_collisions": len(title_out), "fwaed_labels": len(all_fwaed)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
