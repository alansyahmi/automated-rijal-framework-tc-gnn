#!/usr/bin/env python3
"""Gate A morphological candidate scanner over the 8,827 numbered Taqrib entries.

Expands core narrator-evaluation lemmas across Arabic noun/adjective declensions
(gender, number, definiteness, tanwin/case endings, clitics) and verb derivations
and conjugations (perfect/imperfect/passive, person/number, object pronouns),
strictly bounded by Arabic letter boundaries.

Discovery-only: preserves exact verbatim Arabic spans and local context windows,
assigns zero canonical ranks, and enables zero rules.
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
NONE_FOUND_V1_2 = PIPELINE / "rank_label_phrase_review_user_decisions_v1_2_2026-11-16/NONE_FOUND_USER_DECISIONS_161_V1_2.csv"
OUT_DIR = PIPELINE / "gate_a_morphological_candidate_scan_v0_1_2026-11-16"

DIACRITICS_RE = re.compile(r"[\u064b-\u065f\u0670\u0640]")
ARABIC_LETTER = r"[\u0621-\u064a\u066e-\u06d3\u06fa-\u06fc]"
PROCLITICS = r"(?:و|ف|ب|ل|ك)?(?:ال|لل)?"

NOUN_ADJ_CASE_SUFFIXES = r"(?:ا|اً|ة|تان|تين|ات|ون|ين|ان)?"
PRONOUN_CLITICS = r"(?:ه|ها|هم|هما|هن)?"


@dataclass(frozen=True)
class MorphFamily:
    family_id: str
    root_label: str
    domain_role: str
    noun_adj_stems: tuple[str, ...]
    verb_forms: tuple[str, ...]
    notes: str


FAMILIES: tuple[MorphFamily, ...] = (
    MorphFamily(
        family_id="MF-01_WATHAQ",
        root_label="و-ث-ق",
        domain_role="authentication_trustworthiness",
        noun_adj_stems=("ثقة", "ثقه", "ثقات", "ثقتان", "ثقتين", "أوثق", "اوثق", "موثق", "موثوق"),
        verb_forms=("وثق", "وثقت", "وثقا", "وثقوا", "يوثق", "توْثق", "توثق", "يوثقون", "وثقه", "وثقها", "وثقهم", "وثقوه", "يوثقه", "يوثقوه", "توثيق"),
        notes="Includes Rank 2/3 praise, attributed authentication, and non-grade usages like ثقات الأمراء; requires clause context.",
    ),
    MorphFamily(
        family_id="MF-02_SADAQ",
        root_label="ص-د-ق",
        domain_role="truthfulness_rank4_5",
        noun_adj_stems=("صدوق", "صدوقة", "صدوقان", "صدوقين", "صدوقون", "صادق", "صادقة", "أصدق", "اصدق"),
        verb_forms=("صدق", "صدقت", "صدقه", "صدقوه", "يصدق", "يصدقون"),
        notes="Covers Rank 4 صدوق and Rank 5 qualified صدوق forms.",
    ),
    MorphFamily(
        family_id="MF-03_SAHIB",
        root_label="ص-ح-ب",
        domain_role="companionship_status_rank1",
        noun_adj_stems=("صحابي", "صحابية", "صحابيان", "صحابيين", "صحابيون", "صحابة", "صحبة", "صاحب"),
        verb_forms=("صحب", "صحبت", "صحبه", "صحبوه", "يصحب", "اصطحب"),
        notes="Companion status (Rank 1) vs. disputed companionship or general accompaniment.",
    ),
    MorphFamily(
        family_id="MF-04_THABAT",
        root_label="ث-ب-ت",
        domain_role="precision_firmness_rank2_3",
        noun_adj_stems=("ثبت", "ثبتان", "ثبتون", "أثبت", "اثبت"),
        verb_forms=("ثبت", "ثبتت", "ثبته", "يثبت", "تثبت"),
        notes="Rank 2/3 firmness; check against non-grade uses of ثبت.",
    ),
    MorphFamily(
        family_id="MF-05_ATQAN",
        root_label="ت-ق-ن",
        domain_role="mastery_precision_rank3",
        noun_adj_stems=("متقن", "متقنة", "متقنان", "متقنون", "إتقان", "اتقان"),
        verb_forms=("أتقن", "اتقن", "يتقن"),
        notes="Rank 3 precision term.",
    ),
    MorphFamily(
        family_id="MF-06_HAFIZ",
        root_label="ح-ف-ظ",
        domain_role="memory_rank2_or_5",
        noun_adj_stems=("حافظ", "حافظة", "حفاظ", "حفاط", "حفظ"),
        verb_forms=("حفظ", "حفظت", "يحفظ", "تحفظ"),
        notes="Appears in Rank 2 ثقة حافظ and Rank 5 سيء الحفظ.",
    ),
    MorphFamily(
        family_id="MF-07_ADL",
        root_label="ع-د-ل",
        domain_role="uprightness_rank3",
        noun_adj_stems=("عدل", "عدول", "عدالة"),
        verb_forms=("عدل", "عدله", "عدلوه", "يعدل"),
        notes="Rank 3 uprightness; exclude non-grade phrases unless evaluative.",
    ),
    MorphFamily(
        family_id="MF-08_HUJJA",
        root_label="ح-ج-ج",
        domain_role="authority_rank2_3",
        noun_adj_stems=("حجة", "حجج", "محتج"),
        verb_forms=("احتج", "احتجوا", "يحتج", "يحتجون"),
        notes="Includes احتج به / لم يحتج به.",
    ),
    MorphFamily(
        family_id="MF-09_QABIL",
        root_label="ق-ب-ل",
        domain_role="rank6_conditional_acceptance",
        noun_adj_stems=("مقبول", "مقبولة", "مقبولان", "مقبولون", "قبول"),
        verb_forms=("قبل", "قبلت", "قبله", "قبلوه", "يقبل", "يقبلون"),
        notes="Rank 6 مقبول depends on corroboration.",
    ),
    MorphFamily(
        family_id="MF-10_LAYIN",
        root_label="ل-ي-ن",
        domain_role="leniency_weakness_rank6_8",
        noun_adj_stems=("لين", "لينة", "لينون", "ألين", "الين"),
        verb_forms=("لان", "يلين", "لين", "لينه", "يلينه"),
        notes="Covers لين الحديث and related leniency cues.",
    ),
    MorphFamily(
        family_id="MF-11_DAIF",
        root_label="ض-ع-ف",
        domain_role="weakness_rank8_10",
        noun_adj_stems=("ضعيف", "ضعيفة", "ضعيفان", "ضعيفين", "ضعفاء", "أضعف", "اضعف", "ضعف", "مضعف", "مضعفون"),
        verb_forms=("ضعف", "ضعفت", "ضعفه", "ضعفها", "ضعفهم", "ضعفوه", "يضعف", "يضعفه", "يضعفون", "يضعفوه"),
        notes="Covers standalone ضعف/ضعيف and attributed critic weakness.",
    ),
    MorphFamily(
        family_id="MF-12_JAHIL",
        root_label="ج-ه-ل",
        domain_role="unknownness_rank7_9",
        noun_adj_stems=("مجهول", "مجهولة", "مجهولان", "مجهولون", "مجهولين", "جهالة", "جهول"),
        verb_forms=("جهل", "جهلت", "جهله", "جهلوه", "يجهل"),
        notes="Rank 9 unknownness; check transmitter count conditions.",
    ),
    MorphFamily(
        family_id="MF-13_SATAR",
        root_label="س-ت-ر",
        domain_role="mastur_rank7",
        noun_adj_stems=("مستور", "مستورة", "مستوران", "مستورون", "مستورين"),
        verb_forms=("ستر", "يستتر"),
        notes="Rank 7 mastur; check transmitter count and lack of authentication.",
    ),
    MorphFamily(
        family_id="MF-14_ARAF",
        root_label="ع-ر-ف",
        domain_role="knownness_and_negation",
        noun_adj_stems=("معروف", "معروفة", "معروفون", "عارف"),
        verb_forms=("عرف", "عرفت", "عرفه", "عرفوه", "يعرف", "يعرفه", "يعرفون", "يعرفوه", "تعرف"),
        notes="Captures لا يعرف / لم يعرف / معروف / لا أعرف; negation context is essential.",
    ),
    MorphFamily(
        family_id="MF-15_TARAK",
        root_label="ت-ر-ك",
        domain_role="abandonment_rank10",
        noun_adj_stems=("متروك", "متروكة", "متروكون", "متروكين", "تارك"),
        verb_forms=("ترك", "تركت", "تركه", "تركها", "تركوه", "يترك", "يتركه", "يتركوه"),
        notes="Rank 10 abandonment.",
    ),
    MorphFamily(
        family_id="MF-16_SAQAT",
        root_label="س-ق-ط",
        domain_role="severe_weakness_rank10",
        noun_adj_stems=("ساقط", "ساقطة", "ساقطون"),
        verb_forms=("سقط", "سقطت", "يسقط"),
        notes="Rank 10 severe weakness cue.",
    ),
    MorphFamily(
        family_id="MF-17_HALAK",
        root_label="ه-ل-ك",
        domain_role="perished_rank10",
        noun_adj_stems=("هالك", "هالكة", "هالكون"),
        verb_forms=("هلك", "هلكت", "يهلك"),
        notes="Rank 10 severe weakness cue.",
    ),
    MorphFamily(
        family_id="MF-18_TAHAM",
        root_label="ت-ه-م",
        domain_role="accusation_rank11",
        noun_adj_stems=("متهم", "متهمة", "متهمون", "متهمين", "اتهام"),
        verb_forms=("اتهم", "اتهمت", "اتهمه", "اتهموه", "يتهم", "يتهمه", "يتهمون"),
        notes="Rank 11 accusation of lying or fabrication.",
    ),
    MorphFamily(
        family_id="MF-19_WAHAM",
        root_label="و-ه-م",
        domain_role="error_rank5",
        noun_adj_stems=("وهم", "أوهام", "اوهام", "موهم"),
        verb_forms=("وهم", "وهمت", "يهم", "يهمون", "تهم"),
        notes="Rank 5 error qualification (e.g. صدوق يهم).",
    ),
    MorphFamily(
        family_id="MF-20_KADHAB",
        root_label="ك-ذ-ب",
        domain_role="lying_rank11_12",
        noun_adj_stems=("كذاب", "كذابة", "كذابون", "كاذب", "كاذبة", "كذوب", "كذب", "مكذب", "مكذوب"),
        verb_forms=("كذب", "كذبت", "كذبه", "كذبها", "كذبوه", "يكذب", "يكذبه", "يكذبون"),
        notes="Distinguish Rank 12 applied lying from Rank 11 accusation and non-hadith disputes.",
    ),
    MorphFamily(
        family_id="MF-21_WADA",
        root_label="و-ض-ع",
        domain_role="fabrication_rank11_12",
        noun_adj_stems=("وضاع", "وضاعة", "موضوع", "موضوعة", "موضوعات", "واضع"),
        verb_forms=("وضع", "وضعت", "وضعه", "وضعوه", "يضع", "يضعه", "يضعون"),
        notes="Distinguish applied fabrication from non-grade uses of وضع.",
    ),
    MorphFamily(
        family_id="MF-22_GHALAT",
        root_label="غ-ل-ط",
        domain_role="error_rank5_10",
        noun_adj_stems=("غلط", "أغلاط", "اغلاط", "مغلط"),
        verb_forms=("غلط", "غلطت", "يغلط", "يغلطون"),
        notes="Preserves error qualifiers such as كثير الغلط / يغلط.",
    ),
    MorphFamily(
        family_id="MF-23_KHALAT",
        root_label="خ-ل-ط",
        domain_role="confusion_ikhtilat_rank5",
        noun_adj_stems=("مخلط", "مخلطون", "مختلط", "اختلاط"),
        verb_forms=("خلط", "خلطت", "يخلط", "اختلط", "يختلط"),
        notes="Preserves memory-confusion qualifiers such as اختلط بأخرة / خلط في غيره.",
    ),
    MorphFamily(
        family_id="MF-24_NAKAR",
        root_label="ن-ك-ر",
        domain_role="munkar_rank10",
        noun_adj_stems=("منكر", "منكرة", "منكرات", "مناكير"),
        verb_forms=("أنكر", "انكر", "أنكره", "أنكروه", "ينكر"),
        notes="Includes منكر الحديث and critic rejection clauses.",
    ),
    MorphFamily(
        family_id="MF-25_QADAH",
        root_label="ق-د-ح",
        domain_role="defect_rank10",
        noun_adj_stems=("قدح", "قادح"),
        verb_forms=("قدح", "قدحوا", "يقدح"),
        notes="Covers بقدح / بقادح (edition variant in Rank 10 definition).",
    ),
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
        forms.append(f"{PROCLITICS}{re.escape(clean_stem)}{NOUN_ADJ_CASE_SUFFIXES}{PRONOUN_CLITICS}")
    for vform in family.verb_forms:
        clean_verb = DIACRITICS_RE.sub("", vform)
        forms.append(f"(?:و|ف|ل|س|قد)?{re.escape(clean_verb)}")
    # Sort longest first inside alternation
    forms.sort(key=len, reverse=True)
    pattern = rf"(?<!{ARABIC_LETTER})(?:{'|'.join(forms)})(?!{ARABIC_LETTER})"
    return re.compile(pattern)


def context_window(text: str, start: int, end: int, pad: int = 35) -> str:
    left = max(0, start - pad)
    right = min(len(text), end + pad)
    return text[left:right].strip()


def main() -> None:
    if OUT_DIR.exists() and any(OUT_DIR.iterdir()):
        raise SystemExit(f"Refusing to overwrite existing output directory: {OUT_DIR}")

    entries = read_csv(ENTRY_INDEX)
    assert len(entries) == 8827, f"Expected 8827 entries, got {len(entries)}"

    vocab_rows = read_csv(VOCAB_INVENTORY)
    existing_exact_phrases = {
        DIACRITICS_RE.sub("", (r.get("phrase_candidate_exact") or "").strip())
        for r in vocab_rows
        if (r.get("phrase_candidate_exact") or "").strip()
    }
    existing_exact_tokens: set[str] = set()
    for phrase in existing_exact_phrases:
        for tok in re.findall(rf"{ARABIC_LETTER}+", phrase):
            existing_exact_tokens.add(tok)

    none_found_rows = read_csv(NONE_FOUND_V1_2)
    none_found_ids = {r["entry_id"] for r in none_found_rows}

    compiled = [(fam, build_family_regex(fam)) for fam in FAMILIES]

    surface_counter: Counter[tuple[str, str, str]] = Counter()
    surface_examples: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    family_entry_sets: dict[str, set[str]] = defaultdict(set)
    entries_with_any_hit: set[str] = set()
    none_found_newly_hit: list[dict[str, str]] = []

    for entry in entries:
        entry_id = entry["entry_id"]
        verbatim = entry["entry_text_verbatim"]
        clean_text, idx_map = strip_diacritics_with_map(verbatim)

        entry_hits_summary: list[str] = []
        for fam, regex in compiled:
            for m in regex.finditer(clean_text):
                c_start, c_end = m.start(), m.end()
                v_start = idx_map[c_start]
                v_end = idx_map[c_end - 1] + 1
                # Include trailing diacritic if attached to final char
                while v_end < len(verbatim) and DIACRITICS_RE.match(verbatim[v_end]):
                    v_end += 1
                surface_verbatim = verbatim[v_start:v_end]
                surface_clean = m.group(0)
                key = (fam.family_id, fam.root_label, surface_clean)
                surface_counter[key] += 1
                family_entry_sets[fam.family_id].add(entry_id)
                entries_with_any_hit.add(entry_id)
                if len(surface_examples[key]) < 3:
                    surface_examples[key].append({
                        "entry_id": entry_id,
                        "printed_page_num": entry["printed_page_num"],
                        "surface_verbatim": surface_verbatim,
                        "context": context_window(verbatim, v_start, v_end),
                    })
                if entry_id in none_found_ids:
                    entry_hits_summary.append(f"{fam.family_id}:{surface_verbatim}")

        if entry_id in none_found_ids and entry_hits_summary:
            none_found_newly_hit.append({
                "entry_id": entry_id,
                "printed_page_num": entry["printed_page_num"],
                "entry_number_verbatim": entry["entry_number_verbatim"],
                "morph_hits": " || ".join(entry_hits_summary),
                "entry_text_verbatim": verbatim,
            })

    surface_rows: list[dict[str, Any]] = []
    newly_surfaced_forms = 0
    newly_surfaced_occurrences = 0
    for (fam_id, root_label, surface_clean), count in surface_counter.most_common():
        in_v0_1_tokens = surface_clean in existing_exact_tokens
        if not in_v0_1_tokens:
            newly_surfaced_forms += 1
            newly_surfaced_occurrences += count
        ex = surface_examples[(fam_id, root_label, surface_clean)]
        surface_rows.append({
            "family_id": fam_id,
            "root_label": root_label,
            "surface_form_no_diacritics": surface_clean,
            "occurrence_count": count,
            "seen_in_v0_1_exact_tokens": "yes" if in_v0_1_tokens else "no",
            "example_1_entry_id": ex[0]["entry_id"] if len(ex) > 0 else "",
            "example_1_surface_verbatim": ex[0]["surface_verbatim"] if len(ex) > 0 else "",
            "example_1_context": ex[0]["context"] if len(ex) > 0 else "",
            "example_2_entry_id": ex[1]["entry_id"] if len(ex) > 1 else "",
            "example_2_context": ex[1]["context"] if len(ex) > 1 else "",
            "human_census_disposition": "",
            "human_notes": "",
        })

    family_summary_rows: list[dict[str, Any]] = []
    for fam in FAMILIES:
        fam_surface = [(k, v) for k, v in surface_counter.items() if k[0] == fam.family_id]
        total_occ = sum(v for _, v in fam_surface)
        new_forms = sum(1 for k, _ in fam_surface if k[2] not in existing_exact_tokens)
        new_occ = sum(v for k, v in fam_surface if k[2] not in existing_exact_tokens)
        family_summary_rows.append({
            "family_id": fam.family_id,
            "root_label": fam.root_label,
            "domain_role": fam.domain_role,
            "unique_entries_matched": len(family_entry_sets[fam.family_id]),
            "total_occurrences": total_occ,
            "distinct_surface_forms": len(fam_surface),
            "new_surface_forms_beyond_v0_1": new_forms,
            "new_occurrences_beyond_v0_1": new_occ,
            "notes": fam.notes,
        })

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    surface_csv = OUT_DIR / "MORPHOLOGICAL_SURFACE_FORMS_V0_1.csv"
    family_csv = OUT_DIR / "MORPHOLOGICAL_FAMILY_SUMMARY_V0_1.csv"
    none_hits_csv = OUT_DIR / "NONE_FOUND_161_MORPH_HITS_V0_1.csv"

    write_csv(surface_csv, surface_rows, list(surface_rows[0]))
    write_csv(family_csv, family_summary_rows, list(family_summary_rows[0]))
    if none_found_newly_hit:
        write_csv(none_hits_csv, none_found_newly_hit, list(none_found_newly_hit[0]))
    else:
        write_csv(
            none_hits_csv,
            [],
            ["entry_id", "printed_page_num", "entry_number_verbatim", "morph_hits", "entry_text_verbatim"],
        )

    summary_lines = [
        "# Gate A Morphological Candidate Scan v0.1 (Declensions + Verb Derivations)",
        "",
        "**Status:** discovery-only morphological scan over all `8,827` numbered local *Taqrīb* entries (`ENTRY_INDEX.csv`). Zero canonical ranks assigned and zero rules enabled.",
        "",
        "## Corpus-Wide Results",
        f"- Entries scanned: `{len(entries)}`",
        f"- Entries with at least one word-bounded morphological candidate hit: `{len(entries_with_any_hit)}`",
        f"- Morphological families scanned: `{len(FAMILIES)}`",
        f"- Distinct surface forms observed: `{len(surface_rows)}` (`{sum(surface_counter.values())}` total occurrences)",
        f"- **New surface forms beyond v0.1 exact token vocabulary (`203` strings):** `{newly_surfaced_forms}` distinct forms (`{newly_surfaced_occurrences}` occurrences)",
        f"- Entries from the `161` `none_found` set with at least one morphological hit: `{len(none_found_newly_hit)}`",
        "",
        "## Files",
        "- [MORPHOLOGICAL_FAMILY_SUMMARY_V0_1.csv](MORPHOLOGICAL_FAMILY_SUMMARY_V0_1.csv): per-root family summary (unique entries, distinct surface forms, new forms beyond v0.1).",
        "- [MORPHOLOGICAL_SURFACE_FORMS_V0_1.csv](MORPHOLOGICAL_SURFACE_FORMS_V0_1.csv): every observed declension/derivation surface form with verbatim examples, local context windows, and blank `human_census_disposition` for Gate A review.",
        "- [NONE_FOUND_161_MORPH_HITS_V0_1.csv](NONE_FOUND_161_MORPH_HITS_V0_1.csv): subset of the `161` `none_found` entries matched by the expanded morphological scan for manual inspection.",
        "",
    ]
    summary_text = "\n".join(summary_lines)
    assert_no_em_en_dash(summary_text, "README.md")
    readme_path = OUT_DIR / "README.md"
    readme_path.write_text(summary_text, encoding="utf-8", newline="\n")

    for row in surface_rows + family_summary_rows + none_found_newly_hit:
        for k, v in row.items():
            assert_no_em_en_dash(str(v), f"{k}")

    timestamp = datetime.now(timezone.utc).isoformat()
    inputs = [ENTRY_INDEX, VOCAB_INVENTORY, NONE_FOUND_V1_2, Path(__file__).resolve()]
    outputs = [surface_csv, family_csv, none_hits_csv, readme_path]
    manifest = {
        "package_id": OUT_DIR.name,
        "generated_at_utc": timestamp,
        "scope": "Gate A morphological discovery scan (noun/adjective declensions + verb derivations) over 8,827 numbered Taqrib entries; zero canonical ranks assigned.",
        "counts": {
            "entries_scanned": len(entries),
            "entries_with_any_hit": len(entries_with_any_hit),
            "families_scanned": len(FAMILIES),
            "distinct_surface_forms": len(surface_rows),
            "total_occurrences": sum(surface_counter.values()),
            "new_surface_forms_beyond_v0_1": newly_surfaced_forms,
            "new_occurrences_beyond_v0_1": newly_surfaced_occurrences,
            "none_found_161_with_morph_hit": len(none_found_newly_hit),
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
