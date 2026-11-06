#!/usr/bin/env python3
"""Read-only structural audit of HATEMDB JSON files.

Usage:
  python audit_hatemdb_json.py narrators_db.json bukhari_sultania_copy.json

Discovers the JSON structure before assuming a schema. Does not modify inputs.
"""
import collections, hashlib, json, pathlib, sys

def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def describe(x, depth=0):
    if isinstance(x, dict):
        keys = list(x)
        out = {"type": "object", "key_count": len(keys), "keys_sample": [str(k) for k in keys[:50]]}
        if depth < 2 and keys:
            out["value_shapes"] = {str(k): describe(x[k], depth + 1) for k in keys[:15]}
        return out
    if isinstance(x, list):
        return {"type": "array", "length": len(x), "first_item_shape": describe(x[0], depth + 1) if x else None}
    return {"type": type(x).__name__}

def audit(filename):
    p = pathlib.Path(filename)
    print(f"\n## {p.name}\nbytes={p.stat().st_size}\nsha256={digest(p)}")
    with p.open(encoding="utf-8-sig") as f:
        data = json.load(f)
    print("top_level_shape:")
    print(json.dumps(describe(data), ensure_ascii=False, indent=2))
    records = list(data.values()) if isinstance(data, dict) else data if isinstance(data, list) else []
    print(f"top_level_record_count={len(records)}")
    if records:
        sample = json.dumps(records[0], ensure_ascii=False, default=str)
        print("first_record_sample=" + sample[:700] + ("…" if len(sample) > 700 else ""))
    keys = collections.Counter()
    nulls = collections.Counter()
    empties = collections.Counter()
    seen, duplicates = set(), 0
    for rec in records:
        if not isinstance(rec, dict):
            continue
        for k, v in rec.items():
            keys[str(k)] += 1
            if v is None: nulls[str(k)] += 1
            if v == "": empties[str(k)] += 1
        canonical = json.dumps(rec, sort_keys=True, ensure_ascii=False, default=str)
        if canonical in seen: duplicates += 1
        seen.add(canonical)
    print("field_occurrences=" + json.dumps(keys.most_common(), ensure_ascii=False))
    print("null_counts=" + json.dumps(nulls.most_common(), ensure_ascii=False))
    print("empty_string_counts=" + json.dumps(empties.most_common(), ensure_ascii=False))
    print(f"exact_duplicate_top_level_records={duplicates}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    for arg in sys.argv[1:]:
        audit(arg)
