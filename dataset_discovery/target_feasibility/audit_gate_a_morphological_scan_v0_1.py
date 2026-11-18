#!/usr/bin/env python3
"""Second-pass Gate A audit of morphological surface forms (177) and none-found hits (44).

Verifies gate_a_morphological_candidate_scan_v0_1_2026-11-16/MANIFEST.json,
classifies every observed surface form (separating true evaluative declensions and
verb derivations from Arabic homographs/clitic collisions such as فلان, فيهم, قبله),
audits the 44 none_found entries hit by the morphological scan, and leaves all
human_* columns blank pending user review. Assigns zero canonical ranks.
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
SCAN_DIR = PIPELINE / "gate_a_morphological_candidate_scan_v0_1_2026-11-16"
OUT_DIR = PIPELINE / "gate_a_morphological_audit_v0_1_2026-11-16"

# Explicit homograph / clitic-collision surface forms (false positives for grade discovery)
FALSE_POSITIVE_SURFACES = {
    "قبله", "قبل", "قبلها", "قبلهم", "فقبله", "وقبله",
    "فلان", "وفيهم", "فيهم",
    "صاحب", "وصاحب", "فصاحب", "لصاحب", "بصاحب", "الصاحب",
    "المعروف", "ومعروف", "معروفة", "عارف",
    "ثقاته", "المجهولين", "الضعفاء", "أصحابه", "صحابة", "أصحاب",
}

# Surface forms that require clause/referent context because they can be either
# narrator-grade cues or critic/biographical/tamiz notes.
CONTEXT_DEPENDENT_SURFACES = {
    "وهم", "ووهم", "فوهم", "وهمه",
    "غلط", "فغلط", "وغلط",
    "عرف", "يعرف", "ويعرف", "عرفت", "تعرف",
    "ترك", "تركت", "وضع", "وضعت",
    "احتج", "يحتج", "يحتجون",
    "عدول", "عدالة", "قبول",
    "صحب", "صحبه", "يصحب",
    "حفظ", "يحفظ", "حفظه",
    "يثبت", "ثبتت", "فأثبت",
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


def verify_package(directory: Path) -> None:
    manifest_path = directory / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    sidecar = (directory / "MANIFEST.sha256").read_text(encoding="ascii").split()[0]
    if digest(manifest_path) != sidecar:
        raise SystemExit(f"MANIFEST.sha256 mismatch in {directory}")
    for name, expected in manifest["outputs"].items():
        if digest(directory / name) != expected:
            raise SystemExit(f"Hash mismatch for {directory.name}/{name}")


def classify_surface(row: dict[str, str]) -> tuple[str, str, str]:
    surf = row["surface_form_no_diacritics"]
    fam = row["family_id"]
    seen = row["seen_in_v0_1_exact_tokens"]

    if surf in FALSE_POSITIVE_SURFACES:
        if surf == "فلان":
            note = "Clitic collision: ف + لان ('so-and-so'), not MF-10_LAYIN."
        elif surf in {"فيهم", "وفيهم"}:
            note = "Clitic collision: ف + يهم ('among them'), not MF-19_WAHAM."
        elif surf.startswith("قبل") or "قبل" in surf:
            note = "Temporal/cross-reference preposition ('before' / 'الذي قبله'), not MF-09_QABIL."
        else:
            note = "Non-grade biographical/book/nisba/plural-group homograph; exclude from grade candidate promotion."
        return "exclude_homograph_or_collision", "abstain", note

    if surf in CONTEXT_DEPENDENT_SURFACES:
        return (
            "context_dependent_mixed_form",
            "conditional",
            "Appears in both narrator-grade clauses and scholar-error/tamiz/biographical clauses; require full-clause Gate A rule.",
        )

    if seen == "yes":
        return (
            "existing_v0_1_evaluative_token",
            "retain_with_clause_guard",
            f"Already represented in v0.1 exact token set under {fam}; keep subject/negation/attribution guards.",
        )

    return (
        "new_evaluative_declension_or_derivation",
        "promote_to_gate_a_census_candidate",
        f"Valid declension or verb derivation under {fam} surfaced beyond v0.1 exact tokens; include in Gate A complete-span census with clause guard.",
    )


def classify_none_found_hit(row: dict[str, str]) -> tuple[str, str, str]:
    eid = row["entry_id"]
    text = row["entry_text_verbatim"]
    hits = row["morph_hits"]

    if eid == "S3076-P217-C003-E2037":
        return (
            "newly_discovered_subject_grade_candidate",
            "revise_to_candidate",
            "Subject-level Rank 1 candidate ('صحابي له حديثان') missed earlier because it was not in exact-hit v0.2.",
        )
    if eid == "S3076-P077-C012-E0009":
        return (
            "book_specific_memory_qualification",
            "keep_conditional",
            "Book-specific note ('سماعه للموطأ صحيح وخلط في غيره'); keep conditional in context layer.",
        )
    if any(cue in text for cue in ("صحابي", "صحابية", "صحابيات")) and (
        "لم أقف" in text or "عن رجل" in text or "عن امرأة" in text or "فصحابي" in text or "[بن ثابت" in text
    ):
        return (
            "non_subject_or_unnamed_narrator_cue",
            "keep_conditional",
            "Companionship cue applies to an unnamed chain narrator, father, or bracketed insertion rather than the main named subject.",
        )
    if "لا يعرف" in text:
        return (
            "unnamed_narrator_la_yarif",
            "keep_conditional",
            "Contains 'لا يعرف اسمه' / 'لا يعرف ولم يسم'; keep conditional for unnamed/tamiz inspection.",
        )
    return (
        "homograph_or_biographical_false_positive",
        "keep_abstain",
        f"Morphological hit ({hits}) is a non-grade biographical, book-title, tamiz cross-ref ('الذي قبله'), or scholar-error ('وهم') token.",
    )


def main() -> None:
    if OUT_DIR.exists() and any(OUT_DIR.iterdir()):
        raise SystemExit(f"Refusing to overwrite existing audit directory: {OUT_DIR}")

    verify_package(SCAN_DIR)
    surface_rows = read_csv(SCAN_DIR / "MORPHOLOGICAL_SURFACE_FORMS_V0_1.csv")
    none_rows = read_csv(SCAN_DIR / "NONE_FOUND_161_MORPH_HITS_V0_1.csv")

    assert len(surface_rows) == 177
    assert len(none_rows) == 44

    audited_surface: list[dict[str, Any]] = []
    for row in surface_rows:
        cat, action, note = classify_surface(row)
        out = dict(row)
        out["audit_category"] = cat
        out["recommended_gate_a_action"] = action
        out["audit_rationale"] = note
        for k, v in out.items():
            assert_no_em_en_dash(str(v), f"{row['surface_form_no_diacritics']}.{k}")
        audited_surface.append(out)

    audited_none: list[dict[str, Any]] = []
    for row in none_rows:
        cat, action, note = classify_none_found_hit(row)
        out = dict(row)
        out["audit_category"] = cat
        out["recommended_disposition"] = action
        out["audit_rationale"] = note
        out["human_decision"] = ""
        out["human_notes"] = ""
        for k, v in out.items():
            assert_no_em_en_dash(str(v), f"{row['entry_id']}.{k}")
        audited_none.append(out)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    surf_csv = OUT_DIR / "MORPHOLOGICAL_SURFACE_FORMS_AUDIT_V0_1.csv"
    none_csv = OUT_DIR / "NONE_FOUND_44_MORPH_AUDIT_V0_1.csv"
    write_csv(surf_csv, audited_surface, list(audited_surface[0]))
    write_csv(none_csv, audited_none, list(audited_none[0]))

    surf_cat_counts = Counter(r["audit_category"] for r in audited_surface)
    surf_action_counts = Counter(r["recommended_gate_a_action"] for r in audited_surface)
    new_only_counts = Counter(
        r["audit_category"] for r in audited_surface if r["seen_in_v0_1_exact_tokens"] == "no"
    )
    none_cat_counts = Counter(r["audit_category"] for r in audited_none)
    none_action_counts = Counter(r["recommended_disposition"] for r in audited_none)

    top_new_promotes = [
        r for r in audited_surface
        if r["audit_category"] == "new_evaluative_declension_or_derivation"
    ][:15]

    summary_lines = [
        "# Gate A Morphological Second-Pass Audit v0.1",
        "",
        "**Status:** second-pass audit over `177` morphological surface forms and `44` `none_found` morphological hits. All `human_*` columns remain blank pending your approval. Zero canonical ranks assigned and zero rules enabled.",
        "",
        "## 1. Morphological Surface Forms (`177` total; `124` new beyond `v0.1`)",
        f"- All `177` forms by audit category: `{dict(sorted(surf_cat_counts.items()))}`",
        f"- All `177` forms by recommended Gate A action: `{dict(sorted(surf_action_counts.items()))}`",
        f"- **New `124` forms only** by audit category: `{dict(sorted(new_only_counts.items()))}`",
        "",
        "### Notable New Evaluative Declensions / Verb Derivations Surfaced",
    ]
    for r in top_new_promotes:
        summary_lines.append(
            f"- `{r['family_id']}` `{r['surface_form_no_diacritics']}` (`n={r['occurrence_count']}`): e.g. `{r['example_1_entry_id']}`"
        )
    summary_lines.extend([
        "",
        "### Notable Homograph / Clitic Collisions Filtered Out (`abstain`)",
        "- `قبله` (`170`), `قبل` (`166`): temporal/cross-ref ('before' / `الذي قبله`), not `MF-09_QABIL`.",
        "- `صاحب` (`129`): book/place/person association (`صاحب السنن`, `صاحب الاستيعاب`), not Companion status.",
        "- `المعروف` (`65`): 'known as' (`المعروف بالمروزي`), not `لا يعرف`.",
        "- `فلان` (`6`): `ف + لان` ('so-and-so'), not `MF-10_LAYIN`.",
        "- `فيهم` (`1`): `ف + يهم` ('among them'), not `MF-19_WAHAM`.",
        "",
        "## 2. `44` `none_found` Entries Hit by Morphological Scan (`NONE_FOUND_44_MORPH_AUDIT_V0_1.csv`)",
        f"- By audit category: `{dict(sorted(none_cat_counts.items()))}`",
        f"- By recommended disposition: `{dict(sorted(none_action_counts.items()))}`",
        "- **1** genuine subject-level Rank 1 discovery: `S3076-P217-C003-E2037` (`زنباع ابن روح ... صحابي له حديثان ق`).",
        "- **5** non-subject / unnamed-narrator companionship cues (`conditional`), **4** `لا يعرف` unnamed-narrator entries (`conditional`), **1** book-specific mixing note (`E0009` `conditional`), and **33** homograph/biographical/tamiz false positives (`abstain`).",
        "",
    ])
    summary_text = "\n".join(summary_lines)
    assert_no_em_en_dash(summary_text, "AUDIT_SUMMARY_V0_1.md")
    summary_path = OUT_DIR / "AUDIT_SUMMARY_V0_1.md"
    summary_path.write_text(summary_text, encoding="utf-8", newline="\n")

    timestamp = datetime.now(timezone.utc).isoformat()
    inputs = [
        SCAN_DIR / "MORPHOLOGICAL_SURFACE_FORMS_V0_1.csv",
        SCAN_DIR / "NONE_FOUND_161_MORPH_HITS_V0_1.csv",
        SCAN_DIR / "MANIFEST.json",
        Path(__file__).resolve(),
    ]
    outputs = [surf_csv, none_csv, summary_path]
    manifest = {
        "package_id": OUT_DIR.name,
        "generated_at_utc": timestamp,
        "scope": "Gate A second-pass audit of 177 morphological surface forms and 44 none_found hits; human_* columns left blank; zero canonical ranks assigned.",
        "counts": {
            "surface_forms_audited": len(audited_surface),
            "surface_audit_categories": dict(sorted(surf_cat_counts.items())),
            "new_124_surface_categories": dict(sorted(new_only_counts.items())),
            "none_found_hits_audited": len(audited_none),
            "none_found_audit_categories": dict(sorted(none_cat_counts.items())),
            "canonical_ranks_assigned": 0,
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
