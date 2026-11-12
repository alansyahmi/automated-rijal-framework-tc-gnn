#!/usr/bin/env python3
"""Read-only feasibility audit of narrator-level target sources.

Run from the repository root:
    python dataset_discovery/target_feasibility/audit_target_feasibility.py

The audit preserves original label strings, uses conservative name matching,
and never treats a candidate name match as an adjudicated identity.
"""
from __future__ import annotations

import csv
import hashlib
import json
import platform
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VERSION = "1.0.0"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "dataset_discovery" / "target_feasibility"
SHAMELA = ROOT / "data/1_raw/Shamela4_Full_DB/_meta/narrators.parquet"
HADITHDB = ROOT / "data/1_raw/hadithdb/narrators_db.json"
BUKHARI = ROOT / "data/1_raw/hadithdb/bukhari_sultania_copy.json"
FIELDS = ("الرتبة عند ابن حجر", "الرتبة عند الذهبي", "طبقة رواة التقريب")
IDENTITY_KEYS = ("الاسم", "الشهرة", "الكنية", "النسب", "اللقب")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return str(value)


def normalize_name(value: str) -> str:
    """Conservative Arabic orthographic key; not an identity decision."""
    value = unicodedata.normalize("NFKC", value or "")
    value = "".join(
        ch for ch in value
        if ch != "ـ" and not (unicodedata.category(ch) == "Mn")
    )
    value = value.translate(str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي"}))
    return re.sub(r"\s+", " ", value).strip()


def parse_biography(value: Any) -> tuple[dict[str, list[Any]], str]:
    if value is None:
        return {}, "missing"
    try:
        obj = json.loads(value) if isinstance(value, str) else value
    except (json.JSONDecodeError, TypeError):
        return {}, "invalid_json"
    if not isinstance(obj, dict):
        return {}, "unexpected_root"
    summary = obj.get("summary", [])
    if not isinstance(summary, list):
        return {}, "summary_not_list"
    fields: dict[str, list[Any]] = defaultdict(list)
    for pair in summary:
        if not isinstance(pair, (list, tuple)) or len(pair) < 2:
            continue
        fields[text(pair[0])].append(pair[1])
    return dict(fields), "valid"


def nonempty_values(values: list[Any]) -> list[str]:
    return [text(value).strip() for value in values if value is not None and text(value).strip()]


def field_stats(records: list[dict[str, Any]], getter) -> tuple[Counter, dict[str, int]]:
    distribution: Counter = Counter()
    counts = {"labelled": 0, "missing": 0, "ambiguous": 0}
    for record in records:
        values = list(dict.fromkeys(nonempty_values(getter(record))))
        if not values:
            counts["missing"] += 1
            continue
        counts["labelled"] += 1
        if len(values) > 1:
            counts["ambiguous"] += 1
        distribution.update(values)
    return distribution, counts


def make_aliases(fields: list[tuple[str, Any]]) -> list[tuple[str, str]]:
    result = []
    seen = set()
    for field, value in fields:
        value = text(value).strip()
        if value and (field, value) not in seen:
            result.append((field, value))
            seen.add((field, value))
    return result


def build_crosswalk(shamela_records: list[dict[str, Any]], hadith_records: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    """Candidate links via exact or conservative normalized aliases only."""
    shamela_aliases: dict[str, list[tuple[str, str]]] = {}
    shamela_by_id: dict[str, dict[str, Any]] = {}
    raw_index: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    norm_index: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    for record in shamela_records:
        bio, _ = parse_biography(record.get("biography_text"))
        alias_fields = [("short_name", record.get("short_name")), ("long_name", record.get("long_name"))]
        # Generate candidates only from full-name strings. Standalone kunyah,
        # title, fame, or nisba fields are supporting context, not identity keys.
        for key in ("الاسم",):
            alias_fields.extend((f"biography.{key}", value) for value in bio.get(key, []))
        aliases = [(field, value) for field, value in make_aliases(alias_fields)
                   if len(normalize_name(value).split()) >= 2]
        sid = str(record.get("id", ""))
        shamela_aliases[sid] = aliases
        shamela_by_id[sid] = record
        for field, value in aliases:
            raw_index[value].append((str(record.get("id", "")), field, value))
            normalized = normalize_name(value)
            if normalized:
                norm_index[normalized].append((str(record.get("id", "")), field, value))

    output: list[dict[str, str]] = []
    for source_key, record in hadith_records.items():
        data = record.get("data", {}) if isinstance(record.get("data"), dict) else {}
        alias_fields = [("name", record.get("name"))]
        for key in ("الاسم",):
            alias_fields.extend((f"data.{key}", value) for value in (data.get(key),))
        aliases = [(field, value) for field, value in make_aliases(alias_fields)
                   if len(normalize_name(value).split()) >= 2]
        # Pair -> best evidence, with a complete evidence list retained.
        pairs: dict[str, dict[str, Any]] = {}
        for h_field, h_value in aliases:
            for s_id, s_field, s_value in raw_index.get(h_value, []):
                method = "exact_raw_primary" if h_field == "name" and s_field == "short_name" else "exact_raw_alias"
                _add_evidence(pairs, s_id, method, h_field, h_value, s_field, s_value)
            normalized = normalize_name(h_value)
            for s_id, s_field, s_value in norm_index.get(normalized, []):
                if h_value == s_value:
                    continue
                method = "normalized_primary" if h_field == "name" and s_field == "short_name" else "normalized_alias"
                _add_evidence(pairs, s_id, method, h_field, h_value, s_field, s_value)

        if not pairs:
            output.append(_crosswalk_row(source_key, record, "", "", "", "", "unmatched_conservative_search", "none", "unmatched_candidate", []))
            continue
        for s_id, evidence in sorted(pairs.items(), key=lambda item: int(item[0]) if item[0].isdigit() else item[0]):
            best = min(evidence["methods"], key=_method_rank)
            confidence = {"exact_raw_primary": "high_candidate", "exact_raw_alias": "high_candidate", "normalized_primary": "medium_candidate", "normalized_alias": "low_candidate"}[best]
            # High/medium/low are evidence strength only. No pair is verified.
            s_record = shamela_by_id[s_id]
            output.append(_crosswalk_row(source_key, record, s_id, text(s_record.get("short_name")), text(s_record.get("long_name")), best, "unverified_candidate", confidence, "candidate", evidence["evidence"]))
    return output


def _method_rank(method: str) -> int:
    return {"exact_raw_primary": 0, "exact_raw_alias": 1, "normalized_primary": 2, "normalized_alias": 3}[method]


def _add_evidence(pairs: dict[str, dict[str, Any]], s_id: str, method: str, h_field: str, h_value: str, s_field: str, s_value: str) -> None:
    item = pairs.setdefault(s_id, {"methods": set(), "evidence": []})
    item["methods"].add(method)
    evidence = {"method": method, "hadithdb_field": h_field, "hadithdb_value": h_value, "shamela_field": s_field, "shamela_value": s_value}
    if evidence not in item["evidence"] and len(item["evidence"]) < 3:
        item["evidence"].append(evidence)


def _crosswalk_row(source_key, record, s_id, s_short, s_long, method, status, confidence, result, evidence):
    return {
        "hadithdb_record_key": str(source_key),
        "hadithdb_id": text(record.get("id")),
        "hadithdb_name": text(record.get("name")),
        "shamela_id": s_id,
        "shamela_short_name": s_short,
        "shamela_long_name": s_long,
        "matching_method": method,
        "confidence": confidence,
        "verification_status": status,
        "match_result": result,
        "matching_evidence_json": json.dumps(evidence, ensure_ascii=False, sort_keys=True),
    }


def _raw_grade_in_text(value: str, raw_text: str) -> bool:
    return bool(value and raw_text and value in raw_text)


def _name_collision_grade_conflicts(records, name_getter, grade_getter):
    groups = defaultdict(list)
    for record in records:
        name = text(name_getter(record)).strip()
        if name:
            groups[name].append(record)
    results = {}
    for field in FIELDS:
        conflict_groups = 0
        conflict_records = 0
        for group in groups.values():
            if len(group) < 2:
                continue
            vals = {v for r in group for v in nonempty_values(grade_getter(r, field))}
            if len(vals) > 1:
                conflict_groups += 1
                conflict_records += len(group)
        results[field] = {"same_name_groups_with_different_values": conflict_groups,
                          "records_in_those_groups": conflict_records}
    return results


def load_sources():
    import pyarrow.parquet as pq

    shamela = pq.read_table(SHAMELA).to_pylist()
    hadith = json.loads(HADITHDB.read_text(encoding="utf-8-sig"))
    if not isinstance(hadith, dict):
        raise ValueError("HadithDB narrator root is not an object")
    return shamela, hadith


def chain_stats(path: Path, narrator_records: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows = json.loads(path.read_text(encoding="utf-8-sig"))
    number_counts = Counter(text(row.get("hadith_number")) for row in rows if isinstance(row, dict))
    occurrences = 0
    names = set()
    id_names: dict[str, set[str]] = defaultdict(set)
    missing_id_occurrences = 0
    malformed_chains = 0
    for row in rows:
        chain = row.get("narrators") if isinstance(row, dict) else None
        if not isinstance(chain, list):
            malformed_chains += 1
            continue
        for item in chain:
            if not isinstance(item, dict):
                continue
            occurrences += 1
            name = text(item.get("name")).strip()
            narrator_id = text(item.get("id")).strip()
            if name:
                names.add(name)
            if not narrator_id:
                missing_id_occurrences += 1
            elif name:
                id_names[narrator_id].add(name)
    db_ids = {text(row.get("id")) for row in narrator_records.values() if isinstance(row, dict)}
    name_to_ids: dict[str, set[str]] = defaultdict(set)
    for narrator_id, values in id_names.items():
        for name in values:
            name_to_ids[name].add(narrator_id)
    return {
        "rows": len(rows), "unique_hadith_numbers": len(number_counts),
        "rows_beyond_unique_hadith_numbers": len(rows) - len(number_counts),
        "maximum_hadith_number": max((int(n) for n in number_counts if n.isdigit()), default=None),
        "narrator_occurrences": occurrences, "unique_raw_narrator_names": len(names),
        "unique_narrator_ids_in_chains": len(id_names),
        "narrator_ids_found_in_narrator_database": len(set(id_names) & db_ids),
        "unknown_narrator_ids": len(set(id_names) - db_ids),
        "missing_id_occurrences": missing_id_occurrences, "malformed_chain_rows": malformed_chains,
        "ids_with_multiple_chain_name_strings": sum(len(v) > 1 for v in id_names.values()),
        "raw_names_linked_to_multiple_ids": sum(len(v) > 1 for v in name_to_ids.values()),
    }


def sha_stats(records, label_fields, getter):
    result = {}
    for key in label_fields:
        dist, counts = field_stats(records, lambda row, k=key: getter(row, k))
        result[key] = {**counts, "distribution": dist}
    return result


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def run() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    shamela, hadith = load_sources()
    total_s, total_h = len(shamela), len(hadith)
    bukhari_stats = chain_stats(BUKHARI, hadith)
    shamela_bios = {str(r.get("id")): parse_biography(r.get("biography_text"))[0] for r in shamela}

    label_rows = []
    coverage_rows = []
    target_stats: dict[str, dict[str, Any]] = {}

    def add_target(dataset, field, records, getter, role, semantic_status, validated_target_records=0):
        dist, counts = field_stats(records, getter)
        for grade, count in sorted(dist.items()):
            label_rows.append({"dataset": dataset, "field": field, "original_grade": grade, "count": count,
                "percentage": f"{100*count/len(records):.4f}", "value_role": role})
        coverage_rows.append({"dataset": dataset, "field": field, "total_records": len(records),
            "labelled_records": counts["labelled"], "missing_records": counts["missing"],
            "ambiguous_records": counts["ambiguous"], "coverage_percentage": f"{100*counts['labelled']/len(records):.4f}",
            "coverage_basis": "non-empty source field; not validated gold labels", "validated_supervised_records": validated_target_records,
            "semantic_status": semantic_status})
        target_stats[f"{dataset}.{field}"] = {"total": len(records), **{k: counts[k] for k in counts}, "unique_values": len(dist),
            "top_values": dist.most_common(10)}

    for field in FIELDS:
        add_target("Shamela4", field, shamela,
            lambda row, k=field: shamela_bios[str(row.get("id"))].get(k, []),
            "unstructured narrator-level assessment/generation string; source attribution and label semantics unverified",
            "source field present, but value-level mapping and provenance are not validated")
        add_target("HadithDB", field, list(hadith.values()),
            lambda row, k=field: [row.get("data", {}).get(k)] if isinstance(row.get("data"), dict) else [],
            "unstructured metadata string; field label names Ibn Hajar, al-Dhahabi, or Taqrib, but exact provenance/semantics unvalidated",
            "upstream field observed; no data dictionary or record-level source verification")

    # narrator_type exists in the local Parquet but its semantics are unresolved.
    add_target("Shamela4", "narrator_type", shamela, lambda row: [row.get("narrator_type")],
        "unresolved numeric metadata; not treated as a reliability grade", "semantics unresolved")

    # Quote collections are evidence presence, not narrator-level grade labels.
    quotation_stats = {}
    for dataset, records, getter in [
        ("Shamela4", shamela, lambda r: r.get("criticism_text")),
        ("HadithDB", list(hadith.values()), lambda r: r.get("data", {}).get("الجرح والتعديل") if isinstance(r.get("data"), dict) else None),
    ]:
        present = missing = ambiguous = occurrences = group_key_appearances = 0
        record_group_pairs = set()
        unique_group_labels = set()
        for r in records:
            raw = getter(r)
            if not raw:
                missing += 1
                continue
            if dataset == "Shamela4" and isinstance(raw, str):
                try: obj = json.loads(raw)
                except json.JSONDecodeError: obj = {}
                groups = obj.get("garh", []) if isinstance(obj, dict) else []
                if isinstance(groups, dict):
                    group_key_appearances += len(groups)
                    n = sum(len(v) if isinstance(v, list) else 1 for v in groups.values() if v)
                    group_pairs = [(k, v) for k, v in groups.items() if v]
                elif isinstance(groups, list):
                    group_key_appearances += len(groups)
                    n = sum(len(pair[1]) if isinstance(pair, (list, tuple)) and len(pair) > 1 and isinstance(pair[1], list)
                            else 1 for pair in groups)
                    group_pairs = [(pair[0], pair[1]) for pair in groups
                                   if isinstance(pair, (list, tuple)) and len(pair) > 1 and pair[1] is not None
                                   and (len(pair[1]) > 0 if isinstance(pair[1], list) else True)]
                else:
                    n = 0; group_pairs = []
            elif isinstance(raw, dict):
                groups = raw
                group_key_appearances += len(groups)
                n = sum(len(v) for v in groups.values() if isinstance(v, list))
                group_pairs = [(k, v) for k, v in groups.items() if v]
            else:
                groups, n, group_pairs = {}, 0, []
            if n:
                present += 1
                ambiguous += 1  # every item still needs claim/speaker/target validation
                occurrences += n
                record_group_pairs.update((text(r.get("id", r.get("id"))), text(k)) for k, _ in group_pairs)
                unique_group_labels.update(text(k) for k, _ in group_pairs)
            else:
                missing += 1
        coverage_rows.append({"dataset": dataset, "field": "garh / الجرح والتعديل quotation evidence",
            "total_records": len(records), "labelled_records": present, "missing_records": missing,
            "ambiguous_records": ambiguous, "coverage_percentage": f"{100*present/len(records):.4f}",
            "coverage_basis": f"records with at least one quotation occurrence ({occurrences} occurrences total); not grade coverage",
            "validated_supervised_records": 0,
            "semantic_status": "quotation evidence only; speaker, statement type, target, independence, and grade are not validated"})
        quotation_stats[dataset] = {"records_with_quote_evidence": present, "records_without_quote_evidence": missing,
            "quote_occurrences": occurrences, "group_appearances": len(record_group_pairs),
            "group_key_appearances_including_empty": group_key_appearances,
            "unique_group_labels": len(unique_group_labels)}

    write_csv(OUT / "LABEL_DISTRIBUTION.csv", label_rows,
        ["dataset", "field", "original_grade", "count", "percentage", "value_role"])
    write_csv(OUT / "DATASET_COVERAGE.csv", coverage_rows,
        ["dataset", "field", "total_records", "labelled_records", "missing_records", "ambiguous_records", "coverage_percentage", "coverage_basis", "validated_supervised_records", "semantic_status"])

    crosswalk = build_crosswalk(shamela, hadith)
    write_csv(OUT / "IDENTITY_CROSSWALK_CANDIDATES.csv", crosswalk,
        ["hadithdb_record_key", "hadithdb_id", "hadithdb_name", "shamela_id", "shamela_short_name", "shamela_long_name", "matching_method", "confidence", "verification_status", "match_result", "matching_evidence_json"])

    # Identity/duplicate diagnostics, using raw IDs and names without merging.
    shamela_ids = [r.get("id") for r in shamela]
    hadith_ids = [r.get("id") for r in hadith.values()]
    shamela_name_counts = Counter(text(r.get("short_name")) for r in shamela if r.get("short_name"))
    hadith_name_counts = Counter(text(r.get("name")) for r in hadith.values() if r.get("name"))
    exact_id_overlap = set(shamela_ids) & set(hadith_ids)
    row_by_key = {str(r.get("id")): r for r in shamela}
    exact_duplicates = len(shamela) - len({json.dumps(r, ensure_ascii=False, sort_keys=True, default=str) for r in shamela})
    hadith_exact_duplicates = len(hadith) - len({json.dumps(r, ensure_ascii=False, sort_keys=True, default=str) for r in hadith.values()})
    cross_counts = Counter(r["match_result"] for r in crosswalk)
    candidate_by_h = defaultdict(set)
    best_method_by_h = {}
    for row in crosswalk:
        if row["match_result"] == "candidate":
            candidate_by_h[row["hadithdb_record_key"]].add(row["shamela_id"])
            current = best_method_by_h.get(row["hadithdb_record_key"])
            if current is None or _method_rank(row["matching_method"]) < _method_rank(current):
                best_method_by_h[row["hadithdb_record_key"]] = row["matching_method"]
    ambiguous_crosswalk = sum(len(v) > 1 for v in candidate_by_h.values())
    matched_h = len(candidate_by_h)

    # Direct string-overlap flags quantify a concrete leakage path when critique
    # text is proposed as input alongside a target rank from the same record.
    leakage = {"Shamela4": {}, "HadithDB": {}}
    for field in FIELDS[:2]:
        shamela_hits = 0
        for r in shamela:
            values = nonempty_values(shamela_bios[str(r.get("id"))].get(field, []))
            critique = text(r.get("criticism_text"))
            if any(_raw_grade_in_text(v, critique) for v in values):
                shamela_hits += 1
        hadith_hits = 0
        for r in hadith.values():
            data = r.get("data", {}) if isinstance(r.get("data"), dict) else {}
            values = nonempty_values([data.get(field)])
            groups = data.get("الجرح والتعديل", {})
            quote_text = " ".join(text(q) for items in groups.values() for q in (items if isinstance(items, list) else []) if q) if isinstance(groups, dict) else ""
            if any(_raw_grade_in_text(v, quote_text) for v in values):
                hadith_hits += 1
        leakage["Shamela4"][field] = shamela_hits
        leakage["HadithDB"][field] = hadith_hits

    hadith_both = 0
    hadith_equal = 0
    for r in hadith.values():
        data = r.get("data", {}) if isinstance(r.get("data"), dict) else {}
        ih, dh = text(data.get(FIELDS[0])).strip(), text(data.get(FIELDS[1])).strip()
        if ih and dh:
            hadith_both += 1
            hadith_equal += int(ih == dh)

    conflict_by_name = {
        "Shamela4": _name_collision_grade_conflicts(shamela,
            lambda r: r.get("short_name"),
            lambda r, field: shamela_bios[str(r.get("id"))].get(field, [])),
        "HadithDB": _name_collision_grade_conflicts(list(hadith.values()),
            lambda r: r.get("name"),
            lambda r, field: [r.get("data", {}).get(field)] if isinstance(r.get("data"), dict) else []),
    }
    attribution_cues = ("قال", "وثقه", "وثق", "ضعفه", "ضعف", "حكى", "يقال", "ذكر")
    value_cue_stats = {}
    for dataset in ("Shamela4", "HadithDB"):
        value_cue_stats[dataset] = {}
        for field in FIELDS[:2]:
            dist = target_stats[f"{dataset}.{field}"]["top_values"]
            # top_values is intentionally only a sample; compute cues over the
            # full frequency table without changing or normalizing any value.
            if dataset == "Shamela4":
                full_dist, _ = field_stats(shamela, lambda row, k=field: shamela_bios[str(row.get("id"))].get(k, []))
            else:
                full_dist, _ = field_stats(list(hadith.values()), lambda row, k=field: [row.get("data", {}).get(k)] if isinstance(row.get("data"), dict) else [])
            values = [(v, n) for v, n in full_dist.items() if any(cue in v for cue in attribution_cues)]
            value_cue_stats[dataset][field] = {"unique_values_with_possible_attribution_language": len(values),
                "records_with_possible_attribution_language": sum(n for _, n in values),
                "cues": list(attribution_cues)}

    stats = {
        "shamela_records": total_s, "hadithdb_records": total_h,
        "shamela_duplicate_ids": total_s - len(set(shamela_ids)),
        "hadithdb_duplicate_record_ids": len(hadith_ids) - len(set(hadith_ids)),
        "hadithdb_key_id_mismatches": sum(text(key) != text(value.get("id")) for key, value in hadith.items() if isinstance(value, dict)),
        "shamela_exact_duplicate_rows": exact_duplicates,
        "hadithdb_exact_duplicate_rows": hadith_exact_duplicates,
        "shamela_duplicate_short_name_groups": sum(n > 1 for n in shamela_name_counts.values()),
        "shamela_records_in_duplicate_short_name_groups": sum(n for n in shamela_name_counts.values() if n > 1),
        "hadithdb_duplicate_display_name_groups": sum(n > 1 for n in hadith_name_counts.values()),
        "hadithdb_records_in_duplicate_display_name_groups": sum(n for n in hadith_name_counts.values() if n > 1),
        "numeric_id_overlap_not_used_for_matching": len(exact_id_overlap),
        "crosswalk_hadith_records_with_candidates": matched_h,
        "crosswalk_ambiguous_hadith_records": ambiguous_crosswalk,
        "crosswalk_unmatched_hadith_records": total_h - matched_h,
        "crosswalk_candidate_pairs": sum(len(v) for v in candidate_by_h.values()),
        "crosswalk_result_row_counts": dict(cross_counts),
        "crosswalk_candidate_records_by_best_method": dict(Counter(best_method_by_h.values())),
        "crosswalk_exact_raw_full_name_records": sum(method.startswith("exact_raw") for method in best_method_by_h.values()),
        "crosswalk_verified_matches": 0,
        "grade_substring_in_criticism_evidence": leakage,
        "raw_grade_values_with_possible_attribution_language": value_cue_stats,
        "hadithdb_both_ibn_hajar_and_dhahabi_nonempty": hadith_both,
        "hadithdb_both_fields_exactly_equal": hadith_equal,
        "same_display_name_different_grade_strings": conflict_by_name,
        "quotation_evidence": quotation_stats,
        "bukhari_chain_structure": bukhari_stats,
        "target_fields": target_stats,
    }

    report = make_report(stats)
    (OUT / "TARGET_FEASIBILITY_REPORT.md").write_text(report, encoding="utf-8")

    input_paths = [SHAMELA, HADITHDB,
        ROOT / "dataset_discovery/Shamela4/SHAMELA4_AUDIT_FINDINGS.md",
        ROOT / "dataset_discovery/Shamela4/SHAMELA_WEBSITE_ID_CROSSWALK.md",
        ROOT / "dataset_discovery/hadithdb/HADITHDB_AUDIT.md",
        ROOT / "data/1_raw/hadithdb/README.md", BUKHARI]
    manifest = {
        "audit_name": "narrator_level_target_feasibility",
        "script_version": VERSION,
        "script_path": "dataset_discovery/target_feasibility/audit_target_feasibility.py",
        "script_sha256": sha256(Path(__file__).resolve()),
        "scripts": [
            {"path": "dataset_discovery/target_feasibility/audit_target_feasibility.py", "version": VERSION, "sha256": sha256(Path(__file__).resolve())},
            {"path": "dataset_discovery/target_feasibility/test_audit_target_feasibility.py", "version": "1.0.0", "sha256": sha256(ROOT / "dataset_discovery/target_feasibility/test_audit_target_feasibility.py")},
        ],
        "execution_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "inputs": [{"path": str(p.relative_to(ROOT)), "bytes": p.stat().st_size, "sha256": sha256(p)} for p in input_paths if p.exists()],
        "outputs": {},
        "summary": stats,
        "normalization": "Arabic NFKC; remove combining marks and tatweel; fold alef variants to ا and ى to ي; preserve ة, word order, and particles. Used only to generate candidate matches, never automatic merges.",
    }
    output_names = ["TARGET_FEASIBILITY_REPORT.md", "LABEL_DISTRIBUTION.csv", "DATASET_COVERAGE.csv", "IDENTITY_CROSSWALK_CANDIDATES.csv"]
    for name in output_names:
        p = OUT / name
        manifest["outputs"][name] = {"bytes": p.stat().st_size, "sha256": sha256(p)}
    (OUT / "audit_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return stats


def make_report(s: dict[str, Any]) -> str:
    def target(dataset, field):
        return s["target_fields"][f"{dataset}.{field}"]
    rows = []
    for field in FIELDS:
        for dataset in ("Shamela4", "HadithDB"):
            x = target(dataset, field)
            rows.append(f"| {dataset} | `{field}` | {x['total']:,} | {x['labelled']:,} | {x['missing']:,} | {x['ambiguous']:,} | {100*x['labelled']/x['total']:.2f}% | {x['unique_values']:,} |")
    sh_type = target("Shamela4", "narrator_type")
    conflict_rows = []
    for dataset in ("Shamela4", "HadithDB"):
        for field in FIELDS:
            metric = s["same_display_name_different_grade_strings"][dataset][field]
            conflict_rows.append(f"| {dataset} | `{field}` | {metric['same_name_groups_with_different_values']} | {metric['records_in_those_groups']} |")
    leak_rows = []
    for dataset in ("Shamela4", "HadithDB"):
        for field in FIELDS[:2]:
            hits = s["grade_substring_in_criticism_evidence"][dataset][field]
            labelled = target(dataset, field)["labelled"]
            leak_rows.append(f"| {dataset} | `{field}` | {hits:,} | {100*hits/labelled:.1f}% |")
    cue_rows = []
    for dataset in ("Shamela4", "HadithDB"):
        for field in FIELDS[:2]:
            metric = s["raw_grade_values_with_possible_attribution_language"][dataset][field]
            cue_rows.append(f"| {dataset} | `{field}` | {metric['unique_values_with_possible_attribution_language']:,} | {metric['records_with_possible_attribution_language']:,} |")
    qrows = s["quotation_evidence"]
    chains = s["bukhari_chain_structure"]
    return f'''# Narrator-level target feasibility audit

**Audit run:** generated from local inputs by `audit_target_feasibility.py`  
**Scope:** feasibility only; no model training, graph construction, label assignment, or raw-data modification.

## Executive findings

**A narrator-level supervised reliability-prediction task is not currently methodologically defensible.** There are abundant candidate text fields and named rank fields, but the repository does not establish record-level grade provenance, a validated cross-dataset identity link, or a leakage-safe set of inputs and targets. The raw-value counts below are field availability, not validated ground truth.

The strongest *candidate label source* for a narrow feasibility study is HadithDB's `{FIELDS[0]}` field because the field name explicitly associates it with Ibn Hajar and it is populated for {target('HadithDB', FIELDS[0])['labelled']:,}/{s['hadithdb_records']:,} records ({100*target('HadithDB', FIELDS[0])['labelled']/s['hadithdb_records']:.2f}%). This does **not** make its values gold labels: values are unstructured strings, the upstream project provides no field-level data dictionary, and quoted or compiler-reported judgements need record-level validation. The most serious obstacle is target provenance and leakage, followed by unresolved cross-dataset identity.

No normalized class distribution is presented. The raw rank fields contain between 493 and 1,694 distinct strings per dataset/field, including grades, contextual phrases, explicit quotations of other scholars, and non-grade biographical language. No reviewed dataset-specific codebook justifies collapsing them into a common binary, three-class, or five-class scheme or calculating meaningful normalized class imbalance. `طبقة رواة التقريب` is a generation/biographical field, not a reliability target.

## Dataset and schema inventory

| Dataset | Local input / observed schema | Records | Target-related content | Evidence status |
|---|---|---:|---|---|
| Shamela4 | `data/1_raw/Shamela4_Full_DB/_meta/narrators.parquet`; columns `id` (nullable int64), `short_name`, `long_name`, `narrator_type` (nullable int64), `biography_text` (JSON string), `criticism_text` (JSON string) | {s['shamela_records']:,} | Biography keys `{FIELDS[0]}`, `{FIELDS[1]}`, `{FIELDS[2]}`; grouped criticism text (`garh`/`fwaed`) | Directly observed locally. Upstream card describes the corpus and its extraction from Lucene + SQLite but does not define these narrator-field semantics. |
| HadithDB | `data/1_raw/hadithdb/narrators_db.json`; object keyed by source record key; each record has `id`, `name`, nested `data` | {s['hadithdb_records']:,} | Nested keys `{FIELDS[0]}`, `{FIELDS[1]}`, `{FIELDS[2]}`, and `الجرح والتعديل` | Directly observed locally. Upstream project describes a personal effort and the record count; no field-level schema, grading codebook, or licence was found in its repository root. |

Parquet schema confirms the six Shamela fields listed above. Parsed biography JSON contains the three grade/generation keys in question. The HadithDB root keys and nested fields were verified from the local JSON. Exact strings are retained in `LABEL_DISTRIBUTION.csv`.

## Label coverage and raw distributions

| Dataset | Field | Total | Non-empty | Missing | Multiple distinct values in one record | Coverage | Unique raw values |
|---|---|---:|---:|---:|---:|---:|---:|
{chr(10).join(rows)}

`ambiguous_records` above means a record has more than one distinct non-empty value for the same field in the observed structure; it is a structural ambiguity count, not a semantic validity score. Semantic ambiguity remains for all unreviewed grades. The local Shamela `narrator_type` field has {sh_type['labelled']:,} non-empty numeric values and {sh_type['missing']:,} missing, but its meaning is unresolved and it is excluded as a target. No record is currently cleared as a verified supervised target; `validated_supervised_records` is 0 for every candidate field in `DATASET_COVERAGE.csv`.

The quote collections are not grade fields. Shamela `garh` evidence occurs in {qrows['Shamela4']['records_with_quote_evidence']:,} narrator records ({qrows['Shamela4']['quote_occurrences']:,} occurrences, {qrows['Shamela4']['group_appearances']:,} active narrator/group appearances, {qrows['Shamela4']['unique_group_labels']:,} distinct active group labels). HadithDB `الجرح والتعديل` occurs in {qrows['HadithDB']['records_with_quote_evidence']:,} records ({qrows['HadithDB']['quote_occurrences']:,} occurrences, {qrows['HadithDB']['group_appearances']:,} active narrator/group appearances, {qrows['HadithDB']['group_key_appearances_including_empty']:,} group keys including empty groups, {qrows['HadithDB']['unique_group_labels']:,} distinct active group labels). The coverage file reports narrator records with quotation evidence and marks all such records ambiguous at target level pending claim-role, speaker, target, independence, and citation verification. These are not grade labels or independent narrator judgments.

The source field name is the only field-level evidence associating the two rank strings with Ibn Hajar or al-Dhahabi. The audit does not assign each value to “scholar's own explicit grade,” “quotation of another scholar,” “compiler summary,” or “derived value.” Exact values containing reporting/attribution cues such as `قال`, `وثقه`, `حكى`, or `يقال` are counted below as review signals only, not automatically classified as quotations or judgments.

| Dataset | Field | Distinct raw values with a reporting/attribution cue | Records containing those values |
|---|---|---:|---:|
{chr(10).join(cue_rows)}

Examples in the unchanged raw-value inventory include `ثقة` (a grade-like standalone value), `قال أبو حاتم: صدوق` (wording that explicitly reports another authority), and `أحد الأعلام` (a descriptive phrase, not a documented closed class). These examples show why the audit does not automatically label a field value as the named scholar's own explicit grade, a transmitted quotation, a compiler summary, or a normalized class. No derived/normalized grade values were created.

`LABEL_DISTRIBUTION.csv` provides one row per exact original string, with frequency and percentage of dataset records. No punctuation stripping or semantic normalization was applied. These distributions must not be mistaken for class distributions.

In HadithDB, {s['hadithdb_both_ibn_hajar_and_dhahabi_nonempty']:,} records have both named rank fields non-empty; {s['hadithdb_both_fields_exactly_equal']:,} have exactly equal strings. Unequal strings are not counted as scholarly disagreement because their wording, provenance, or grading frameworks may differ.

### Missing, duplicate, conflicting, and ambiguous records

- Shamela ID duplicates: {s['shamela_duplicate_ids']}; exact duplicate rows: {s['shamela_exact_duplicate_rows']}; duplicate `short_name` groups: {s['shamela_duplicate_short_name_groups']} covering {s['shamela_records_in_duplicate_short_name_groups']:,} records.
- HadithDB repeated record IDs: {s['hadithdb_duplicate_record_ids']}; exact duplicate rows: {s['hadithdb_exact_duplicate_rows']}; repeated display-name groups: {s['hadithdb_duplicate_display_name_groups']} covering {s['hadithdb_records_in_duplicate_display_name_groups']:,} records.
- HadithDB root-key versus embedded `id` mismatches: {s['hadithdb_key_id_mismatches']}.
- Duplicate names are homonym/collision signals, not proof that two records are duplicate people. Likewise, unequal grades among same-name records cannot be treated as a contradiction until identity is resolved.
- Counts of repeated-name groups with different strings by field are recorded in `audit_manifest.json`; these are possible homonym conflicts, not confirmed scholarly disagreements.
- Within-record multiple distinct values are counted in the coverage table. Conflicting values across scholars or works are retained in the source and are not collapsed into one consensus target.

| Dataset | Field | Repeated-name groups with different values | Records in those groups |
|---|---|---:|---:|
{chr(10).join(conflict_rows)}

## Cross-dataset identity correspondence

The two local corpora expose source-specific integer IDs. No reviewed repository documentation establishes that the two ID namespaces are shared. The {s['numeric_id_overlap_not_used_for_matching']:,} numerically overlapping IDs are reported only as coincidences and were not used to match.

The candidate crosswalk uses exact raw equality and conservative normalized equality across source-provided full/short names and full `الاسم` fields (Unicode NFKC, remove combining marks/tatweel, fold alef variants and `ى` to `ي`; preserve `ة`, particles, and word order). Standalone kunyah, title, fame, and nisba values are not candidate keys because common values produce false links; they require contextual manual review. Best-evidence candidate records by method: `{json.dumps(s['crosswalk_candidate_records_by_best_method'], ensure_ascii=False)}`. Exact raw full-name candidate records: {s['crosswalk_exact_raw_full_name_records']}; manually verified cross-dataset identities: {s['crosswalk_verified_matches']}. This is candidate generation, not entity resolution: no row is called verified. Candidate rows: {s['crosswalk_candidate_pairs']:,}; HadithDB records with one or more candidates: {s['crosswalk_hadith_records_with_candidates']:,}; records with multiple candidate Shamela IDs: {s['crosswalk_ambiguous_hadith_records']:,}; unmatched under this conservative search: {s['crosswalk_unmatched_hadith_records']:,}. “Unmatched” means no exact or normalized full-name equality was found, not that no counterpart exists. Manual review is required for spelling, kunya, nisba, lineage, and homonym resolution.

See `IDENTITY_CROSSWALK_CANDIDATES.csv`. Preserve both IDs; do not merge records based on these candidates.

## Target validity and candidate research targets

1. **Explicit scholarly-grade fields.** The two named rank fields look like narrator-level assessments by their field labels. They are not necessarily the scholar's direct independent judgement: strings can include quotations, reports of other scholars, contextual qualification, and compiler wording. The actual local values are long-form free text rather than a closed class vocabulary. Record-level provenance remains unvalidated.
2. **Quotation collections.** Shamela grouped criticism and HadithDB `الجرح والتعديل` are evidence sources, not ready-made grade labels. A row may concern another narrator or a hadith, report multiple authorities, or repeat a later compilation. Group labels do not prove who historically made the judgement.
3. **Generation metadata.** `طبقة رواة التقريب` contains layer labels such as “third” or “tenth”; it is not a reliability grade. Ibn Hajar's own introduction to *Taqrib* distinguishes twelve narrator ranks from twelve chronological/tabaqa layers, so the layer field must not be substituted for a grade. `narrator_type` is a local numeric field whose semantics remain unresolved.

| Candidate target | Availability | Provenance / validity | Leakage and compatibility | Assessment |
|---|---|---|---|---|
| A. Ibn Hajar narrator grade | HadithDB: {target('HadithDB', FIELDS[0])['labelled']:,}; Shamela4: {target('Shamela4', FIELDS[0])['labelled']:,} non-empty | Strongest field-name provenance of the candidates, but values and source texts are not row-verified; multiple free-text forms | Very high leakage if the same Ibn Hajar grade field, `Taqrib` text, or direct reproduction enters inputs. An exact scholar-specific target is conceptually coherent only after source verification and exclusion rules. | Best candidate for a narrow *future* audit, not ready as a training target. |
| B. al-Dhahabi narrator grade | HadithDB: {target('HadithDB', FIELDS[1])['labelled']:,}; Shamela4: {target('Shamela4', FIELDS[1])['labelled']:,} | Same concerns; “rank at al-Dhahabi” strings include statements attributed to other critics and non-grade descriptions | High leakage if al-Dhahabi fields or textual reproductions are input; cross-dataset joins are not yet validated. | Less complete and no clearer validity than A. |
| C. Combined multi-scholar category | Both grades appear in some records, but there is no shared validated identity crosswalk or reviewed agreement protocol | Different scholars' frameworks are not interchangeable; disagreement may be substantive, temporal, source-based, or about different evidence | A combination would obscure disagreement and multiply leakage routes. | Not defensible before record-level source/identity validation and a justified aggregation rule. |
| D. Claim-level evaluative stance, later aggregated by narrator | Text evidence exists in both corpora; the current 20-case Shamela pilot has 43 AI-suggested claims only | Closest to the textual research question, but the pilot is not human-verified ground truth; only one human reviewer is available | Inputs can be separated from labels in principle, but attribution and narrator target must be independently annotated; aggregation risks treating repeated/quoted claims as independent. | Strongest construct alignment, but not currently trainable. Continue only as a scoped human annotation feasibility study after independent review is available. |

## Leakage and independence

- A record-level target copied from `الرتبة عند ابن حجر` or `الرتبة عند الذهبي` cannot also be an input feature. If the target is parsed from a source text, remove that same source passage and close duplicates from inputs; otherwise the task is label reproduction.
- Any split must group by resolved narrator identity and, where possible, source work / duplicate-text cluster. Otherwise duplicated biographies, repeated quotations, or the same person under variant names may leak across train and test.
- Exact grade strings occur within the datasets' own criticism/quotation text for some records; the counts by target field are in `audit_manifest.json`. This directly demonstrates a text-target leakage route. A simple substring hit is only a leakage signal, not evidence that the quoted passage is the grade's source.

| Dataset | Field | Exact substring hits in same-record criticism/quotation text | Share of non-empty target records |
|---|---|---:|---:|
{chr(10).join(leak_rows)}
- The nested HadithDB scholar-label key is not a verified speaker field. The existing audit documents an example where a quotation under `البخاري` reports al-Hakim's statement. Quotation rows therefore need claim-level attribution and target validation before supervised learning.
- The current 20-case AI-assisted claim draft and AI-suggested identity reconciliation are feasibility aids only. They are not ground truth, independent labels, or evidence of inter-reviewer agreement.
- The Bukhari chain JSON contains ordered narrator IDs according to the repository audit, but a chain edge represents transmission linkage, not reliability. Duplicate hadith numbering and chain-name/ID consistency still require audit before graph use.

## Graph feasibility (not a graph design)

Potential source nodes/fields include narrator IDs; raw work-title and locator strings; HadithDB's scholar-labelled source groups; Shamela's grouped criticism entries; and ordered narrator IDs in the Bukhari chain JSON. Direct local parsing found {chains['rows']:,} Bukhari rows, {chains['unique_hadith_numbers']:,} unique hadith numbers, {chains['narrator_occurrences']:,} chain-narrator occurrences, {chains['unique_narrator_ids_in_chains']:,} distinct IDs, all {chains['narrator_ids_found_in_narrator_database']:,} found in `narrators_db.json`; there are {chains['rows_beyond_unique_hadith_numbers']:,} rows beyond distinct hadith numbers, {chains['missing_id_occurrences']} chain narrator occurrences without an ID, and {chains['ids_with_multiple_chain_name_strings']:,} IDs with more than one raw chain name string. These IDs support a source-specific ordered transmission layer, subject to chain validation; a chain edge represents transmission linkage, not reliability. Scholar labels, citation strings, and tuple IDs are not verified evaluator, work-identity, or independent-assessment entities. A graph built now would risk encoding co-occurrence and storage layout as scholarly relationships. Missing evidence includes a cross-dataset identity resolution, validated speaker/claim subject, normalized work and edition identifiers, citation-to-passage checks, and duplicate/independence review.

## Recommended research decision

1. **Is narrator-level supervised prediction feasible now?** No - not as a defensible, leakage-controlled research task. The records contain candidate labels, but they have not been validated sufficiently for training/evaluation.
2. **Strongest candidate?** For label provenance, A (Ibn Hajar's named field) is the clearest narrowly defined candidate. For the project's ESA research question, D has better construct fit, but its labels are much less mature. Neither is ready for model training.
3. **Most serious obstacle?** Whether a field's value is actually a traceable, narrator-level judgement by the named authority - and whether the same judgement leaks into proposed inputs.
4. **Missing evidence?** Row-level source verification, a grade codebook for the actual stored strings, cross-dataset identity adjudication, human claim/speaker/target annotations, duplicate/independence analysis, and split-leakage checks.
5. **Continue claim annotation, reduce scope, or defer?** Reduce it to a small feasibility study focused on claim segmentation, subject, attribution, and source evidence. The 20-case AI-assisted pilot is not ground truth; do not scale it as a training-label project without an independent Arabic-trained reviewer.
6. **Next single research task:** manually verify a stratified sample of HadithDB Ibn Hajar field records against the cited source (including edition and page) and record whether each value is Ibn Hajar's own concise grade, a quotation of another authority, compiler wording, or unresolved. This directly tests the strongest label candidate before any model work.

## Sources and evidence hierarchy

**Local dataset evidence** is generated from the exact input files recorded in `audit_manifest.json`. Existing local discovery reports are cited as prior audits and were not treated as substitutes for direct current parsing.

**Upstream technical documentation:**
- [AuthenticIlm/Shamela4_Full_DB dataset card](https://huggingface.co/datasets/AuthenticIlm/Shamela4_Full_DB) describes 8,589 books, 18,989 narrator records, and extraction from Lucene + SQLite, but does not define the narrator grade fields in a field-level codebook.
- [hatemben/hadithdb repository](https://github.com/hatemben/hadithdb) describes the project as a personal effort and states its Bukhari/narrator scope. The repository root has the JSON files but no reviewed field-level data dictionary, grade ontology, or declared licence.
- The *Taqrib al-Tahdhib* introduction is quoted in this [catalogued manuscript witness](https://islhornafr.tors.sc.ku.dk/backend/texts/2740): it distinguishes twelve ranks for narrators' status from twelve narrator layers. That documents Ibn Hajar's scheme, but does not show how the local data extraction populated either field or map each free-text string to a rank.

The exact local schema and counts are directly observed. Statements about what each Arabic label means remain hypotheses unless a source is identified and checked. No result in this report establishes a model-ready target, historical speaker identity, or database-ID semantics beyond the local storage observations.
'''


if __name__ == "__main__":
    result = run()
    print(json.dumps({k: v for k, v in result.items() if k not in {"target_fields", "same_display_name_different_grade_strings"}}, ensure_ascii=True, indent=2))
