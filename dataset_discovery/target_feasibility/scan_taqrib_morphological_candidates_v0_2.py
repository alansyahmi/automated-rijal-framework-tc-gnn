#!/usr/bin/env python3
"""Gate A morphological candidate scanner v0.2 over the 8,827 numbered Taqrib entries.

Extends v0.1 by:
1. Correctly handling construct ta marbuta (ة -> ت) before attached pronoun
   clitics (e.g. ثقة -> ثقته/ثقتهم, صحبة -> صحبته, رؤية -> رؤيته).
2. Adding missing source-anchored & evaluative root families discovered during
   the v0.1 100-entry sample audit (لا بأس به/ليس به بأس, ليس بالقوي, صالح الحديث,
   مستقيم الحديث, مقارب الحديث, تكلموا فيه, لا أعرفه, له رؤية, صحبا, الوضع,
   أثنى عليه, يسرق الحديث, and explicit Companion-tier expressions).
Discovery-only: zero canonical ranks assigned and zero rules enabled.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PIPELINE = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline"
ENTRY_INDEX = PIPELINE / "rank_label_shadow_run_v1_2026-11-15/ENTRY_INDEX.csv"
VOCAB_INVENTORY = PIPELINE / "rank_vocabulary_candidate_inventory_v0_1_2026-11-16/CANDIDATE_VOCABULARY_V0_1.csv"
V01_SCAN_CSV = PIPELINE / "gate_a_morphological_candidate_scan_v0_1_2026-11-16/MORPHOLOGICAL_SURFACE_FORMS_V0_1.csv"
OUT_DIR = PIPELINE / "gate_a_morphological_candidate_scan_v0_2_2026-11-17"

DIACRITICS_RE = re.compile(r"[\u064b-\u065f\u0670\u0640]")
ARABIC_LETTER = r"[\u0621-\u064a\u066e-\u06d3\u06fa-\u06fc]"
PROCLITICS = r"(?:و|ف|ب|ل|ك)?(?:ال|لل)?"
NOUN_ADJ_CASE_SUFFIXES = r"(?:ا|اً|ة|تان|تين|ات|ون|ين|ان)?"
PRONOUN_CLITICS = r"(?:ه|ها|هم|هما|هن)"


@dataclass(frozen=True)
class MorphFamily:
    family_id: str
    root_label: str
    domain_role: str
    noun_adj_stems: tuple[str, ...]
    verb_or_multiword_forms: tuple[str, ...]
    notes: str


FAMILIES_V0_2: tuple[MorphFamily, ...] = (
    MorphFamily("MF-01_WATHAQ", "و-ث-ق", "authentication_trustworthiness", ("ثقة", "ثقه", "ثقات", "ثقتان", "ثقتين", "أوثق", "اوثق", "موثق", "موثوق"), ("وثق", "وثقت", "وثقا", "وثقوا", "يوثق", "توثق", "يوثقون", "وثقه", "وثقها", "وثقهم", "وثقوه", "يوثقه", "يوثقوه", "توثيق"), "Includes Rank 2/3 praise and attributed authentication; construct ثقته now supported."),
    MorphFamily("MF-02_SADAQ", "ص-د-ق", "truthfulness_rank4_5", ("صدوق", "صدوقة", "صدوقان", "صدوقين", "صدوقون", "صادق", "صادقة", "أصدق", "اصدق"), ("صدق", "صدقت", "صدقه", "صدقوه", "يصدق", "يصدقون"), "Rank 4 and qualified Rank 5 truthfulness."),
    MorphFamily("MF-03_SAHIB", "ص-ح-ب", "companionship_status_rank1", ("صحابي", "صحابية", "صحابيان", "صحابيين", "صحابيون", "صحابة", "صحبة", "صاحب"), ("صحب", "صحبت", "صحبا", "صحبوا", "صحبه", "صحبوه", "يصحب", "اصطحب"), "Construct صحبته and dual صحبا now supported."),
    MorphFamily("MF-04_THABAT", "ث-ب-ت", "precision_firmness_rank2_3", ("ثبت", "ثبتان", "ثبتون", "أثبت", "اثبت"), ("ثبت", "ثبتت", "ثبته", "يثبت", "تثبت"), "Rank 2/3 firmness."),
    MorphFamily("MF-05_ATQAN", "ت-ق-ن", "mastery_precision_rank3", ("متقن", "متقنة", "متقنان", "متقنون", "إتقان", "اتقان"), ("أتقن", "اتقن", "يتقن"), "Rank 3 mastery."),
    MorphFamily("MF-06_HAFIZ", "ح-ف-ظ", "memory_rank2_or_5", ("حافظ", "حافظة", "حفاظ", "حفاط", "حفظ"), ("حفظ", "حفظت", "يحفظ", "تحفظ"), "Memory quality or Rank 2 praise."),
    MorphFamily("MF-07_ADL", "ع-د-ل", "uprightness_rank3", ("عدل", "عدول", "عدالة"), ("عدل", "عدله", "عدلوه", "يعدل"), "Rank 3 uprightness."),
    MorphFamily("MF-08_HUJJA", "ح-ج-ج", "authority_rank2_3", ("حجة", "حجج", "محتج"), ("احتج", "احتجوا", "يحتج", "يحتجون"), "Authority."),
    MorphFamily("MF-09_QABIL", "ق-ب-ل", "rank6_conditional_acceptance", ("مقبول", "مقبولة", "مقبولان", "مقبولون", "قبول"), ("قبل", "قبلت", "قبله", "قبلوه", "يقبل", "يقبلون"), "Rank 6 conditional acceptance; filter temporal قبله/قبل."),
    MorphFamily("MF-10_LAYIN", "ل-ي-ن", "leniency_weakness_rank6_8", ("لين", "لينة", "لينون", "ألين", "الين"), ("لان", "يلين", "لين", "لينه", "يلينه"), "Leniency; filter فلان collision."),
    MorphFamily("MF-11_DAIF", "ض-ع-ف", "weakness_rank8_10", ("ضعيف", "ضعيفة", "ضعيفان", "ضعيفين", "ضعفاء", "أضعف", "اضعف", "ضعف", "مضعف", "مضعفون"), ("ضعف", "ضعفت", "ضعفه", "ضعفها", "ضعفهم", "ضعفوه", "يضعف", "يضعفه", "يضعفون", "يضعفوه"), "Weakness."),
    MorphFamily("MF-12_JAHIL", "ج-ه-ل", "unknownness_rank7_9", ("مجهول", "مجهولة", "مجهولان", "مجهولون", "مجهولين", "جهالة", "جهول"), ("جهل", "جهلت", "جهله", "جهلوه", "يجهل"), "Unknownness."),
    MorphFamily("MF-13_SATAR", "س-ت-ر", "mastur_rank7", ("مستور", "مستورة", "مستوران", "مستورون", "مستورين"), ("ستر", "يستتر"), "Mastur."),
    MorphFamily("MF-14_ARAF", "ع-ر-ف", "knownness_and_negation", ("معروف", "معروفة", "معروفون", "عارف"), ("عرف", "عرفت", "عرفه", "عرفوه", "يعرف", "يعرفه", "يعرفون", "يعرفوه", "تعرف", "أعرف", "أعرفه", "اعرف", "اعرفه"), "Added 1sg أعرف / أعرفه."),
    MorphFamily("MF-15_TARAK", "ت-ر-ك", "abandonment_rank10", ("متروك", "متروكة", "متروكون", "متروكين", "تارك"), ("ترك", "تركت", "تركه", "تركها", "تركوه", "يترك", "يتركه", "يتركوه"), "Abandonment."),
    MorphFamily("MF-16_SAQAT", "س-ق-ط", "severe_weakness_rank10", ("ساقط", "ساقطة", "ساقطون"), ("سقط", "سقطت", "يسقط"), "Severe weakness."),
    MorphFamily("MF-17_HALAK", "ه-ل-ك", "perished_rank10", ("هالك", "هالكة", "هالكون"), ("هلك", "هلكت", "يهلك"), "Severe weakness."),
    MorphFamily("MF-18_TAHAM", "ت-ه-م", "accusation_rank11", ("متهم", "متهمة", "متهمون", "متهمين", "اتهام"), ("اتهم", "اتهمت", "اتهمه", "اتهموه", "يتهم", "يتهمه", "يتهمون"), "Accusation."),
    MorphFamily("MF-19_WAHAM", "و-ه-م", "error_rank5", ("وهم", "أوهام", "اوهام", "موهم"), ("وهم", "وهمت", "يهم", "يهمون", "تهم"), "Error; filter فيهم."),
    MorphFamily("MF-20_KADHAB", "ك-ذ-ب", "lying_rank11_12", ("كذاب", "كذابة", "كذابون", "كاذب", "كاذبة", "كذوب", "كذب", "مكذب", "مكذوب"), ("كذب", "كذبت", "كذبه", "كذبها", "كذبوه", "يكذب", "يكذبه", "يكذبون"), "Lying."),
    MorphFamily("MF-21_WADA", "و-ض-ع", "fabrication_rank11_12", ("وضاع", "وضاعة", "موضوع", "موضوعة", "موضوعات", "واضع", "وضع"), ("وضعت", "وضعه", "وضعوه", "يضع", "يضعه", "يضعون", "رموه بالوضع"), "Includes definite الوضع / رموه بالوضع."),
    MorphFamily("MF-22_GHALAT", "غ-ل-ط", "error_rank5_10", ("غلط", "أغلاط", "اغلاط", "مغلط"), ("غلطت", "يغلط", "يغلطون"), "Error."),
    MorphFamily("MF-23_KHALAT", "خ-ل-ط", "confusion_ikhtilat_rank5", ("مخلط", "مخلطون", "مختلط", "اختلاط"), ("خلط", "خلطت", "يخلط", "اختلط", "يختلط"), "Confusion / ikhtilat."),
    MorphFamily("MF-24_NAKAR", "ن-ك-ر", "munkar_rank10", ("منكر", "منكرة", "منكرات", "مناكير"), ("أنكر", "انكر", "أنكره", "أنكروه", "ينكر"), "Munkar."),
    MorphFamily("MF-25_QADAH", "ق-د-ح", "defect_rank10", ("قدح", "قادح"), ("قدحوا", "يقدح"), "Defect."),
    MorphFamily("MF-26_BAAS", "ب-أ-س", "no_harm_rank4", (), ("لا بأس به", "لا بأس بها", "لا بأس بحديثه", "ليس به بأس", "ليس بها بأس", "ما به بأس", "لا بأس"), "Explicit Rank 4 source-anchored phrase family."),
    MorphFamily("MF-27_SALAH", "ص-ل-ح", "righteousness_rank4_5", ("صويلح",), ("صالح الحديث", "صالح في الحديث"), "Restricted from bare personal name صالح to evaluative clauses."),
    MorphFamily("MF-28_QAWIY", "ق-و-ي", "strength_negated_or_affirmed", (), ("ليس بالقوي", "قوي الحديث", "ليس بقوي"), "Evaluative strength clauses."),
    MorphFamily("MF-29_SHAY", "ش-ي-ء", "worthlessness_rank10", (), ("ليس بشيء", "لا شيء"), "Guarded against generic شيء."),
    MorphFamily("MF-30_QARAB_QAWAM", "ق-ر-ب/ق-و-م", "near_straight_hadith", ("متماسك",), ("مقارب الحديث", "مستقيم الحديث"), "Rare evaluative qualifiers."),
    MorphFamily("MF-31_KALAM", "ك-ل-م", "criticized_kalam", (), ("تكلم فيه", "تكلموا فيه", "فيه مقال"), "Attributed or general criticism clauses."),
    MorphFamily("MF-32_RUYA", "ر-أ-ي", "prophetic_sight_ruyah", ("رؤية",), (), "Conditional/disputed companionship cue (includes رؤيته construct)."),
    MorphFamily("MF-33_COMPANION_TIER", "ب-د-ر/س-ب-ق", "companion_tier_and_service", ("بدري", "مخضرم"), ("شهد بدرا", "شهد بدر", "شهد أحدا", "أحد العشرة", "أحد النقباء", "السابقين الأولين", "قدماء المهاجرين", "مسلمة الفتح", "أم المؤمنين", "خليفة رسول الله", "خادم النبي", "خادم رسول الله", "بيعة الرضوان"), "Explicit Companion/seniority status phrases."),
    MorphFamily("MF-34_THANA_SARAQ_AYB", "ث-ن-ي/س-ر-ق/ع-ي-ب", "rare_praise_or_severe_criticism", (), ("أثنى عليه", "يثني عليه", "يسرق الحديث", "سرق الحديث", "عابوا عليه"), "Rare verb-based evaluative clauses."),
)


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


def strip_diacritics_with_map(text: str) -> tuple[str, list[int]]:
    clean_chars: list[str] = []
    index_map: list[int] = []
    for idx, ch in enumerate(text):
        if DIACRITICS_RE.match(ch):
            continue
        clean_chars.append(ch)
        index_map.append(idx)
    return "".join(clean_chars), index_map


def build_family_regex(family: MorphFamily) -> re.Pattern[str]:
    forms: list[str] = []
    for stem in family.noun_adj_stems:
        clean_stem = DIACRITICS_RE.sub("", stem)
        forms.append(f"{PROCLITICS}{re.escape(clean_stem)}{NOUN_ADJ_CASE_SUFFIXES}")
        # Construct ta marbuta (ة -> ت) before attached pronoun clitics
        if clean_stem.endswith("ة"):
            construct = clean_stem[:-1] + "ت"
            forms.append(f"{PROCLITICS}{re.escape(construct)}{PRONOUN_CLITICS}")
        else:
            forms.append(f"{PROCLITICS}{re.escape(clean_stem)}{PRONOUN_CLITICS}")
    for vform in family.verb_or_multiword_forms:
        clean_v = DIACRITICS_RE.sub("", vform)
        if " " in clean_v:
            escaped = r"\s+".join(re.escape(tok) for tok in clean_v.split())
            forms.append(f"(?:و|ف)?{escaped}")
        else:
            forms.append(f"(?:و|ف|ل|س|قد)?{re.escape(clean_v)}")
    forms.sort(key=len, reverse=True)
    pattern = rf"(?<!{ARABIC_LETTER})(?:{'|'.join(forms)})(?!{ARABIC_LETTER})"
    return re.compile(pattern)


def context_window(text: str, start: int, end: int, pad: int = 35) -> str:
    return text[max(0, start - pad):min(len(text), end + pad)].strip()


def main() -> None:
    if OUT_DIR.exists() and any(OUT_DIR.iterdir()):
        raise SystemExit(f"Refusing to overwrite existing output directory: {OUT_DIR}")

    entries = read_csv(ENTRY_INDEX)
    assert len(entries) == 8827
    vocab_rows = read_csv(VOCAB_INVENTORY)
    existing_exact_tokens = {
        tok
        for r in vocab_rows
        if (r.get("phrase_candidate_exact") or "").strip()
        for tok in re.findall(rf"{ARABIC_LETTER}+", DIACRITICS_RE.sub("", r["phrase_candidate_exact"]))
    }
    v01_surfaces = {r["surface_form_no_diacritics"] for r in read_csv(V01_SCAN_CSV)}

    compiled = [(fam, build_family_regex(fam)) for fam in FAMILIES_V0_2]
    surface_counter: Counter[tuple[str, str, str]] = Counter()
    surface_examples: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    entries_with_any_hit: set[str] = set()

    for entry in entries:
        eid = entry["entry_id"]
        verbatim = entry["entry_text_verbatim"]
        clean_text, idx_map = strip_diacritics_with_map(verbatim)
        for fam, regex in compiled:
            for m in regex.finditer(clean_text):
                v_start = idx_map[m.start()]
                v_end = idx_map[m.end() - 1] + 1
                while v_end < len(verbatim) and DIACRITICS_RE.match(verbatim[v_end]):
                    v_end += 1
                surface_clean = re.sub(r"\s+", " ", m.group(0)).strip()
                key = (fam.family_id, fam.root_label, surface_clean)
                surface_counter[key] += 1
                entries_with_any_hit.add(eid)
                if len(surface_examples[key]) < 2:
                    surface_examples[key].append({
                        "entry_id": eid,
                        "surface_verbatim": verbatim[v_start:v_end],
                        "context": context_window(verbatim, v_start, v_end),
                    })

    surface_rows: list[dict[str, Any]] = []
    new_vs_v01 = 0
    for (fam_id, root_label, surf), count in surface_counter.most_common():
        in_v01 = surf in v01_surfaces
        if not in_v01:
            new_vs_v01 += 1
        ex = surface_examples[(fam_id, root_label, surf)]
        surface_rows.append({
            "family_id": fam_id,
            "root_label": root_label,
            "surface_form_no_diacritics": surf,
            "occurrence_count": count,
            "seen_in_v0_1_exact_tokens": "yes" if surf in existing_exact_tokens else "no",
            "seen_in_morph_v0_1": "yes" if in_v01 else "no",
            "example_1_entry_id": ex[0]["entry_id"] if ex else "",
            "example_1_context": ex[0]["context"] if ex else "",
            "example_2_entry_id": ex[1]["entry_id"] if len(ex) > 1 else "",
            "human_census_disposition": "",
            "human_notes": "",
        })

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    surf_csv = OUT_DIR / "MORPHOLOGICAL_SURFACE_FORMS_V0_2.csv"
    write_csv(surf_csv, surface_rows, list(surface_rows[0]))

    readme_text = "\n".join([
        "# Gate A Morphological Candidate Scan v0.2",
        "",
        "**Status:** discovery-only v0.2 morphological scan over `8,827` numbered entries, adding `ة -> ت` pronoun constructs (`ثقته`, `صحبته`, `رؤيته`) and 9 newly uncovered evaluative families (`لا بأس به`, `ليس بالقوي`, `صالح الحديث`, `تكلموا فيه`, `له رؤية`, `البدري`, etc.). Zero canonical ranks assigned and zero rules enabled.",
        "",
        f"- Entries with any hit: `{len(entries_with_any_hit)} / {len(entries)}`",
        f"- Families scanned: `{len(FAMILIES_V0_2)}`",
        f"- Distinct surface forms observed: `{len(surface_rows)}` (`{new_vs_v01}` newly surfaced beyond morph v0.1)",
        "",
    ])
    assert_no_em_en_dash(readme_text, "README.md")
    readme_path = OUT_DIR / "README.md"
    readme_path.write_text(readme_text, encoding="utf-8", newline="\n")

    timestamp = datetime.now(timezone.utc).isoformat()
    inputs = [ENTRY_INDEX, VOCAB_INVENTORY, V01_SCAN_CSV, Path(__file__).resolve()]
    outputs = [surf_csv, readme_path]
    manifest = {
        "package_id": OUT_DIR.name,
        "generated_at_utc": timestamp,
        "counts": {
            "entries_scanned": len(entries),
            "entries_with_any_hit": len(entries_with_any_hit),
            "families_scanned": len(FAMILIES_V0_2),
            "distinct_surface_forms": len(surface_rows),
            "total_occurrences": sum(surface_counter.values()),
            "newly_surfaced_beyond_morph_v0_1": new_vs_v01,
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
