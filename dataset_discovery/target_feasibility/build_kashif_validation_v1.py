#!/usr/bin/env python3
"""Build external validation dataset from al-Dhahabi's al-Kashif (Book 1616).

Verifies Shamela4 `narrators.csv` `الرتبة عند الذهبي` provenance against Book 1616,
extracts all numbered entries directly from 1616/pages.jsonl, links entries
unambiguously to Taqrib `entry_id` (Shamela crosswalk first, then normalized-name
+ Six-Books sigils), maps al-Dhahabi's verdicts onto a coarse 3-tier (and 5-tier)
ordinal scale without forcing Ibn Hajar's 12 ranks, and audits verbatim overlap
against `taqrib_text_verbatim`.

Outputs to:
  data/2_interim/rijal_fyp_modelling_pipeline/kashif_validation_v1_2026-11-21/
    - KASHIF_ENTRIES_V1.csv
    - KASHIF_TAQRIB_LINK_V1.csv
    - KASHIF_GRADE_MAP_V1.json
    - KASHIF_OVERLAP_AUDIT_V1.csv
    - REPORT.md
    - MANIFEST.json
    - MANIFEST.sha256
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from common.hashing import sha256_file, sha256_text_normalized, to_posix_relative

KASHIF_PAGES = (
    ROOT
    / "data/1_raw/Shamela4_Full_DB/26__التراجم-والطبقات/1616__الكاشف-في-معرفة-من-له-رواية-في-الكتب-الستة/pages.jsonl"
)
SHAMELA_NARRATORS_CSV = ROOT / "data/2_interim/Shamela4/narrators.csv"
PIPELINE = ROOT / "data/2_interim/rijal_fyp_modelling_pipeline"
TASK_B_NODES = PIPELINE / "task_b_consolidated_graph_v0_3_2026-11-17/TASK_B_NODE_STRUCTURAL_FEATURES_V0_3.csv"
MASTER_NODES = PIPELINE / "taqrib_v2_master_dataset_2026-11-20/TAQRIB_V2_MASTER_NODES_8827.csv"
LAYERED_WIDE = PIPELINE / "layered_scores_v3_2026-11-21/LAYERED_SCORES_WIDE_V3.csv"
TAHRIR_ALIGNED = PIPELINE / "tahrir_taqrib_alignment_v1_2026-11-20/TAHRIR_TAQRIB_ALIGNED_8827_V1.csv"
DEFAULT_OUT_DIR = PIPELINE / "kashif_validation_v1_2026-11-21"

AR_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
DIACRITICS_RE = re.compile(r"[\u064b-\u065f\u0670\u0640]")
HTML_RE = re.compile(r"<[^>]+>")
ENTRY_RE = re.compile(r"^([٠-٩0-9]+)\s*[-–]\s*(.+)$")
SIGIL_VOCAB = {
    "ع", "خ", "م", "د", "ت", "س", "ق", "٤", "4",
    "بخ", "خت", "عخ", "تخ", "مد", "دس", "دت", "مدت",
    "قد", "فق", "ل", "ز", "سي", "كن", "ص", "عس",
    "سق", "مق", "ر", "ي", "تمييز", "خد", "كد", "صد", "تم",
}

GRADE_MAP_SPEC: dict[str, Any] = {
    "schema_version": "1.0",
    "source_work": {
        "book_id": 1616,
        "title": "الكاشف في معرفة من له رواية في الكتب الستة",
        "author": "شمس الدين أبو عبد الله محمد بن أحمد بن عثمان الذهبي (ت 748 هـ)",
        "editor": "محمد عوامة وأحمد محمد نمر الخطيب (دار القبلة / مؤسسة علوم القرآن، 1413 هـ / 1992 م)",
    },
    "scale_design_policy": (
        "Al-Dhahabi's vocabulary in al-Kashif differs from Ibn Hajar's 12 maratib in Taqrib. "
        "We map explicit verdicts onto a coarse 3-tier scale (2=thiqah_level, 1=saduq_level, 0=weak_and_below) "
        "and an optional 5-tier scale (5=superlative/sahabi, 4=thiqah, 3=saduq, 2=mild_weak_or_majhul, 1=severe_weak_or_abandoned). "
        "Silent entries (~2,500) and mixed/contested entries are recorded as 'unmapped', never guessed."
    ),
    "tier_3_labels": {
        "2": "thiqah_level",
        "1": "saduq_level",
        "0": "weak_and_below",
        "": "unmapped",
    },
    "tier_5_labels": {
        "5": "superlative_thiqah_or_sahabi",
        "4": "thiqah_or_wuththiqa",
        "3": "saduq_or_salih_level",
        "2": "mild_weak_or_majhul",
        "1": "severe_weak_matruk_or_kadhdhab",
        "": "unmapped",
    },
    "rules": [
        {
            "rule_id": "KASHIF-CONTESTED-UNMAPPED",
            "tier_3": "",
            "tier_5": "",
            "terms": ["mixed praise and jarh in the same verdict span"],
            "citation": "Methodology §P3: contested entries recorded as unmapped rather than guessed",
        },
        {
            "rule_id": "KASHIF-MIXED-PRAISE-UNMAPPED",
            "tier_3": "",
            "tier_5": "",
            "terms": ["thiqah-level and saduq-level praise in the same region with no own leading verdict by al-Dhahabi"],
            "citation": "Review 2026-11-22 (rule-order fix): quoted critics and titles must not override al-Dhahabi's own verdict",
        },
        {
            "rule_id": "KASHIF-T3-2-SAHABI",
            "tier_3": "2",
            "tier_5": "5",
            "terms": ["صحابي", "صحابية", "الصحابي", "الصحابية", "له صحبة", "لها صحبة"],
            "citation": "Classical Sahabah adālah convention; al-Kashif entries before عن/سمع",
        },
        {
            "rule_id": "KASHIF-T3-2-SUPERLATIVE",
            "tier_3": "2",
            "tier_5": "5",
            "terms": ["ثقة ثبت", "ثقة حجة", "ثقة حافظ", "ثقة متقن", "حجة", "ثبت", "متقن", "أوثق"],
            "citation": "Muhammad Awwamah, Muqaddimat al-Kashif (1616, Part 1, pp. 25-28); al-Dhahabi, al-Muqizah pp. 77-78",
        },
        {
            "rule_id": "KASHIF-T3-2-THIQAH",
            "tier_3": "2",
            "tier_5": "4",
            "terms": ["ثقة", "الثقة", "وثقه", "وثقها", "وثقوه"],
            "citation": "Awwamah, Muqaddimat al-Kashif (1616, Part 1, p. 29: 'ومن ألفاظ التعديل في الكتاب: وثقه فلان...')",
        },
        {
            "rule_id": "KASHIF-T3-2-TITLE",
            "tier_3": "2",
            "tier_5": "5",
            "terms": ["إمام", "الإمام", "حافظ", "الحافظ", "حافظا"],
            "citation": "Titles count only when no explicit grade term is present (review 2026-11-22)",
        },
        {
            "rule_id": "KASHIF-WUTHTHIQA (policy-dependent)",
            "tier_3": "thiqah: 2 | maqbul_r6: 1",
            "tier_5": "thiqah: 4 | maqbul_r6: 3",
            "terms": ["وثق", "وثق حب"],
            "citation": "Passive tawthiq, often Ibn Hibban-only. Policy maqbul_r6 maps it to Ibn Hajar rank 6 (maqbul, saduq tier); policy thiqah keeps the v1 mapping. Supervisor sign-off pending.",
        },
        {
            "rule_id": "KASHIF-T3-1-SADUQ",
            "tier_3": "1",
            "tier_5": "3",
            "terms": ["صدوق", "لا بأس به", "ليس به بأس", "ليس بحديثه بأس", "حسن الحديث", "صالح الحديث", "صالح", "محله الصدق", "شيخ", "مقارب الحديث"],
            "citation": "al-Dhahabi, al-Muqizah pp. 78-81; Awwamah, Muqaddimat al-Kashif (1616, Part 1, pp. 30-34)",
        },
        {
            "rule_id": "KASHIF-T3-0-MILD-WEAK",
            "tier_3": "0",
            "tier_5": "2",
            "terms": ["ضعيف", "ضعفه", "ضعفوه", "ضعف", "فيه ضعف", "في حديثه ضعف", "لين", "فيه لين", "لين الحديث", "مجهول", "يجهل", "لا يعرف", "لا يدرى", "مستور", "ليس بالقوي", "ليس بذاك", "منكر الحديث", "في حفظه شيء"],
            "citation": "al-Dhahabi, al-Muqizah pp. 81-84; Awwamah, Muqaddimat al-Kashif (1616, Part 1, pp. 34-37)",
        },
        {
            "rule_id": "KASHIF-T3-0-SEVERE-WEAK",
            "tier_3": "0",
            "tier_5": "1",
            "terms": ["متروك", "تركوه", "ترك", "واه", "واهي", "ساقط", "ذاهب الحديث", "هالك", "ليس بشيء", "متهم", "اتهمه", "اتهموه", "كذاب", "كذبوه", "وضاع", "يضع الحديث"],
            "citation": "al-Dhahabi, al-Muqizah pp. 83-85; Bilgin (2026) severity alignment",
        },
    ],
}

# Compiled verdict patterns (operating on normalized Arabic without diacritics/hamza variants)
PAT_SAHABI = re.compile(r"(?:^|\s)(?:صحابي|صحابيه|الصحابي|الصحابيه|له\s+صحبه|لها\s+صحبه)(?=$|\s)")
PAT_WEAK_SEV = re.compile(
    r"(?:^|\s)(?:متروك|تركوه|ترك|واه|واهي|ساقط|ذاهب\s+الحديث|هالك|ليس\s+بشيء|متهم|اتهمه|اتهموه|كذاب|كذبوه|وضاع|يضع\s+الحديث)(?=$|\s)"
)
PAT_WEAK_MLD = re.compile(
    r"(?:^|\s)(?:ضعيف|ضعفه|ضعفوه|ضعف|فيه\s+ضعف|في\s+حديثه\s+ضعف|لين|فيه\s+لين|لين\s+الحديث|مجهول|يجهل|لا\s+يعرف|لا\s+يدري|لا\s+يدرى|مستور|ليس\s+بالقوي|ليس\s+بذاك|منكر\s+الحديث|في\s+حفظه\s+شيء)(?=$|\s)"
)
PAT_SADUQ = re.compile(
    r"(?:^|\s)(?:صدوق|لا\s+باس\s+به|ليس\s+به\s+باس|ليس\s+بحديثه\s+باس|حسن\s+الحديث|صالح\s+الحديث|محله\s+الصدق|مقارب\s+الحديث"
    r"|(?<!\bبن\s)(?<!\bابن\s)(?<!\bابي\s)(?<!\bابو\s)(?<!\bقال\s)(?<!\bوقال\s)صالح(?!\s+(?:بن|ابن|بنت|مولي|مولى|جزره|العجلي|السدوسي|الهمداني))"
    r"|(?<!\bبن\s)(?<!\bابن\s)شيخ(?!\s+(?:الاسلام|البلد|بن|ابن)))(?=$|\s)"
)
PAT_THIQAH_SUP = re.compile(r"(?:^|\s)(?:ثقه\s+ثبت|ثقه\s+حجه|ثقه\s+حافظ|ثقه\s+متقن|حجه|ثبت|متقن|اوثق)(?=$|\s)")
# Honorific titles: a grade only when no explicit grade term is present (review 2026-11-22).
PAT_TITLE = re.compile(
    r"(?:^|\s)(?:امام|الامام|(?<!\bبن\s)(?<!\bابن\s)(?<!\bابي\s)حافظ(?!\s+(?:بن|ابن))|الحافظ|حافظا)(?=$|\s)"
)
PAT_THIQAH = re.compile(r"(?:^|\s)(?:ثقه|الثقه)(?=$|\s)")
# Tawthiq attributed to a named critic (وثقه أحمد): reported, not al-Dhahabi's own verdict.
PAT_THIQAH_QUOTED = re.compile(r"(?:^|\s)(?:وثقه|وثقها|وثقوه)(?=$|\s)")
# Passive وثق / وثق حب: policy-dependent (see WUTHTHIQA_POLICIES).
PAT_WUTHTHIQA = re.compile(r"(?:^|\s)وثق(?=$|\s)")
PAT_QUOTE_LEAD = re.compile(r"(?:^|\s)(?:قال|وقال|قاله)\s+(?:\S+\s+){0,3}$")

WUTHTHIQA_POLICIES = ("maqbul_r6", "thiqah")
DEFAULT_WUTHTHIQA_POLICY = "maqbul_r6"
# Tahrir commentary that cites al-Dhahabi or one of his rijal works.
PAT_TAHRIR_CITES_DHAHABI = re.compile(r"الذهبي|الكاشف|الميزان|المغني في الضعفاء|ديوان الضعفاء|سير اعلام")


def norm_ar(text: str) -> str:
    s = DIACRITICS_RE.sub("", text or "")
    s = re.sub(r"[أإآ]", "ا", s).replace("ى", "ي").replace("ة", "ه")
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def strip_sigils(text: str) -> tuple[str, tuple[str, ...]]:
    toks = (text or "").strip().split()
    matched: list[str] = []
    while toks and toks[-1].strip("[]().،:؛") in SIGIL_VOCAB:
        matched.append(toks.pop().strip("[]().،:؛"))
    matched.reverse()
    return " ".join(toks), tuple(matched)


def canon_sigil_books(sigils: tuple[str, ...]) -> frozenset[str]:
    books: set[str] = set()
    for t in sigils:
        if t == "ع":
            books.update({"خ", "م", "د", "ت", "س", "ق"})
        elif t in {"٤", "4"}:
            books.update({"د", "ت", "س", "ق"})
        else:
            for ch in t:
                if ch in {"خ", "م", "د", "ت", "س", "ق"}:
                    books.add(ch)
    return frozenset(books)


def extract_name_tokens(text: str) -> list[str]:
    s = ENTRY_RE.sub(r"\2", (text or "").strip())
    s = re.sub(r"\[[^\]]*\]", " ", s)
    s = DIACRITICS_RE.sub("", s)
    s = re.split(
        r"\s+(?:عن|سمع|روى|ثقة|صدوق|ضعيف|متروك|مجهول|صحابي|صحابية|وثق|وثقه|وثقها|ضعف|ضعفه|مستور|مقبول|شيخ|"
        r"من\s+ال|من\s+كبار|من\s+صغار|من\s+أوساط|قيل|المعروف|نزل|سكن|مولى|كوفي|بصري|مدني|شامي|مصري|مكي|"
        r"بغدادي|واسطي|خراساني|دمشقي|حمصي|ثبت|إمام|حافظ|لين|لا\s+بأس|مات|توفي)\b",
        s,
        maxsplit=1,
    )[0]
    toks = ["بن" if t == "ابن" else t for t in norm_ar(s).split()]
    return toks


def parse_kashif_entries(pages_path: Path = KASHIF_PAGES) -> list[dict[str, Any]]:
    with pages_path.open("r", encoding="utf-8") as f:
        pages = [json.loads(line) for line in f]
    pages.sort(key=lambda r: (int(r["part"]), int(r["shamela_page_id"])))
    idx0 = next(i for i, r in enumerate(pages) if r["page_id"] == 1623279)

    entries: list[dict[str, Any]] = []
    cur: dict[str, Any] | None = None
    for pg in pages[idx0:]:
        for raw_line in (pg.get("body") or "").splitlines():
            line = HTML_RE.sub("", raw_line).strip()
            if not line:
                continue
            m = ENTRY_RE.match(line)
            if m:
                num = int(m.group(1).translate(AR_DIGITS))
                prev = cur["num"] if cur else 0
                if 1 <= num <= 7200 and (cur is None or prev - 20 <= num <= prev + 50):
                    if cur is not None:
                        entries.append(cur)
                    cur = {
                        "num": num,
                        "part": str(pg["part"]),
                        "page_num": str(pg["page_num"]),
                        "lines": [line],
                    }
                    continue
            if line in {"فصل", "النساء", "الكنى"} or line.startswith("فصل ") or line.startswith("ذكر من "):
                if cur is not None:
                    entries.append(cur)
                    cur = None
                continue
            if cur is not None:
                cur["lines"].append(line)
    if cur is not None:
        entries.append(cur)
    return entries


def extract_kashif_verdict(full_text: str, wuththiqa_policy: str = DEFAULT_WUTHTHIQA_POLICY) -> dict[str, str]:
    if wuththiqa_policy not in WUTHTHIQA_POLICIES:
        raise ValueError(f"wuththiqa_policy must be one of {WUTHTHIQA_POLICIES}")
    body_no_sig, sigils = strip_sigils(full_text)
    s = ENTRY_RE.sub(r"\2", body_no_sig)
    s = DIACRITICS_RE.sub("", s)
    s = re.sub(r"(?<!\s)(وعنه|وعنها)", r" \1", s)
    s = re.sub(r"\bوعنبن\b", "وعنه بن", s)

    m_pre = re.search(r"\s+(?:عن|سمع|وعنه|وعنها|روى\s+عنه|روت\s+عنه|عنه|عنها)\s+", s)
    pre_part = s[: m_pre.start()].strip() if m_pre else s.strip()
    m_post = re.search(r"\s+(?:وعنه|وعنها|روى\s+عنه|روت\s+عنه|عنه|عنها)\s+", s)
    post_part = s[m_post.end() :].strip() if m_post else ""

    pre_n = norm_ar(pre_part)
    post_n = norm_ar(post_part)
    full_n = norm_ar(s)

    is_sahabi = (
        bool(PAT_SAHABI.search(pre_n))
        and "لا صحبه" not in full_n
        and "لا تصح" not in full_n
    )
    pre_safe = " ".join(
        re.findall(r"\b(?:ثقه|الثقه|صدوق|ضعيف|متروك|مجهول|الحافظ|حافظ|الامام|امام|ثبت|حجه|لين)\b", pre_n)
    )
    # al-Dhahabi's verdict sits after the student list. Name-region words (titles such as
    # الحافظ/الامام) are used only when the post region has no verdict cue at all.
    all_pats = (PAT_WEAK_SEV, PAT_WEAK_MLD, PAT_SADUQ, PAT_THIQAH_SUP, PAT_TITLE, PAT_THIQAH, PAT_THIQAH_QUOTED, PAT_WUTHTHIQA)
    post_has_cue = any(p.search(post_n) for p in all_pats)
    combined = post_n if post_has_cue else f"{pre_safe} {post_n}".strip()

    m_ws = PAT_WEAK_SEV.search(combined)
    m_wm = PAT_WEAK_MLD.search(combined)
    m_sad = PAT_SADUQ.search(combined)
    m_ts = PAT_THIQAH_SUP.search(combined)
    m_title = PAT_TITLE.search(combined)
    m_th = PAT_THIQAH.search(combined)
    m_thq = PAT_THIQAH_QUOTED.search(combined)
    m_wu = PAT_WUTHTHIQA.search(combined)

    has_praise = is_sahabi or any(bool(m) for m in (m_ts, m_title, m_th, m_thq, m_wu, m_sad))
    has_weak = bool(m_ws) or bool(m_wm)

    # Extract concise verbatim span around the matched verdict for overlap & provenance
    verdict_span = ""
    region_src = "none"
    if is_sahabi:
        m_s = PAT_SAHABI.search(pre_n)
        verdict_span = m_s.group(0).strip() if m_s else "صحابي"
        region_src = "pre_teacher_sahabi"
    elif post_part:
        # Clean leading student names up to first evaluative/critic cue if present
        m_cue = re.search(
            r"(?:قال|وقال|ذكره|وثق|وثقه|وثقها|وثقوه|ضعف|ضعفه|ضعفوه|ثقة|الثقة|صدوق|صالح|لا\s+بأس|ليس\s+به\s+بأس|ليس\s+بحديثه\s+بأس|"
            r"ضعيف|متروك|تركوه|واه|واهي|ساقط|مجهول|يجهل|لا\s+يعرف|لا\s+يدرى|مستور|منكر|متهم|اتهمه|كذاب|وضاع|"
            r"لين|فيه\s+لين|إمام|حجة|ثبت|متقن|حافظ|الحافظ|شيخ|ليس\s+بشيء|ليس\s+بالقوي|ليس\s+بذاك|في\s+حفظه)",
            post_part,
        )
        if m_cue:
            span_raw = post_part[m_cue.start() :].strip()
            # Trim trailing death year clause if after verdict
            span_raw = re.split(r"\s+(?:مات|توفي|توفيت|استشهد|قتل)\s+[٠-٩0-9]+", span_raw, maxsplit=1)[0]
            verdict_span = span_raw.strip()
            region_src = "post_student"
    if not verdict_span and pre_safe:
        verdict_span = pre_safe
        region_src = "pre_teacher_title"

    if has_praise and has_weak:
        return {
            "verdict_span": verdict_span or post_part[:100],
            "region_src": region_src,
            "tier_3": "",
            "tier_3_label": "unmapped",
            "tier_5": "",
            "rule_id": "KASHIF-CONTESTED-UNMAPPED",
            "is_sahabi": str(is_sahabi),
            "sigils_raw": " ".join(sigils),
        }
    if is_sahabi:
        return {
            "verdict_span": verdict_span,
            "region_src": region_src,
            "tier_3": "2",
            "tier_3_label": "thiqah_level",
            "tier_5": "5",
            "rule_id": "KASHIF-T3-2-SAHABI",
            "is_sahabi": "True",
            "sigils_raw": " ".join(sigils),
        }
    if has_praise:
        wu_t3, wu_t5, wu_rule = (
            ("1", "3", "KASHIF-T3-1-WUTHTHIQA-MAQBUL") if wuththiqa_policy == "maqbul_r6" else ("2", "4", "KASHIF-T3-2-WUTHTHIQA")
        )
        # (level, match, tier_3, tier_5, rule_id), highest priority first within a tier
        levels = [
            ("sup", m_ts, "2", "5", "KASHIF-T3-2-SUPERLATIVE"),
            ("thiqah", m_th, "2", "4", "KASHIF-T3-2-THIQAH"),
            ("thiqah_quoted", m_thq, "2", "4", "KASHIF-T3-2-THIQAH"),
            ("wuththiqa", m_wu, wu_t3, wu_t5, wu_rule),
            ("saduq", m_sad, "1", "3", "KASHIF-T3-1-SADUQ"),
        ]
        present = [lv for lv in levels if lv[1]]
        if not present and m_title:
            present = [("title", m_title, "2", "5", "KASHIF-T3-2-TITLE")]
        chosen = None
        if len({lv[2] for lv in present}) == 1:
            chosen = present[0]
        else:
            # Mixed thiqah/saduq-level praise: use al-Dhahabi's own leading verdict, i.e. the
            # earliest cue that is not a named critic's tawthiq (وثقه فلان) and not inside a
            # "قال فلان ..." quotation. Without one, the entry is recorded as unmapped.
            own = [
                lv for lv in present
                if lv[0] != "thiqah_quoted" and not PAT_QUOTE_LEAD.search(combined[: lv[1].start() + 1])
            ]
            if own:
                lead = min(own, key=lambda lv: lv[1].start())
                chosen = (lead[0], lead[1], lead[2], lead[3], lead[4] + "-OWN-LEAD")
        if chosen is None:
            return {
                "verdict_span": verdict_span,
                "region_src": region_src,
                "tier_3": "",
                "tier_3_label": "unmapped",
                "tier_5": "",
                "rule_id": "KASHIF-MIXED-PRAISE-UNMAPPED",
                "is_sahabi": "False",
                "sigils_raw": " ".join(sigils),
            }
        return {
            "verdict_span": verdict_span,
            "region_src": region_src,
            "tier_3": chosen[2],
            "tier_3_label": {"2": "thiqah_level", "1": "saduq_level"}[chosen[2]],
            "tier_5": chosen[3],
            "rule_id": chosen[4],
            "is_sahabi": "False",
            "sigils_raw": " ".join(sigils),
        }
    if m_ws:
        return {
            "verdict_span": verdict_span,
            "region_src": region_src,
            "tier_3": "0",
            "tier_3_label": "weak_and_below",
            "tier_5": "1",
            "rule_id": "KASHIF-T3-0-SEVERE-WEAK",
            "is_sahabi": "False",
            "sigils_raw": " ".join(sigils),
        }
    if m_wm:
        return {
            "verdict_span": verdict_span,
            "region_src": region_src,
            "tier_3": "0",
            "tier_3_label": "weak_and_below",
            "tier_5": "2",
            "rule_id": "KASHIF-T3-0-MILD-WEAK",
            "is_sahabi": "False",
            "sigils_raw": " ".join(sigils),
        }
    return {
        "verdict_span": "",
        "region_src": "silent_or_biographical",
        "tier_3": "",
        "tier_3_label": "unmapped",
        "tier_5": "",
        "rule_id": "KASHIF-NO-EXPLICIT-GRADE",
        "is_sahabi": "False",
        "sigils_raw": " ".join(sigils),
    }


def verify_narrators_csv_provenance(k_entries: list[dict[str, Any]]) -> dict[str, Any]:
    """Verify whether `الرتبة عند الذهبي` in Shamela4 narrators.csv comes from al-Kashif (1616)."""
    kashif_corpus_norm = " ".join(norm_ar(" ".join(e["lines"])) for e in k_entries)
    total = 0
    found_in_1616 = 0
    with SHAMELA_NARRATORS_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            bio = json.loads(row["biography_text"]) if row.get("biography_text") else {}
            sm = dict(bio.get("summary", []))
            dh = sm.get("الرتبة عند الذهبي", "").strip()
            if dh:
                total += 1
                dh_n = norm_ar(dh)
                dh_bn = " ".join("بن" if t == "ابن" else t for t in dh_n.split())
                if dh_n in kashif_corpus_norm or dh_bn in kashif_corpus_norm:
                    found_in_1616 += 1
    return {
        "narrators_csv_with_dhahabi_field": total,
        "matched_in_1616_kashif_body": found_in_1616,
        "match_rate": round(found_in_1616 / total, 4) if total else 0.0,
    }


def rank_to_tier3(rank_str: str) -> str:
    if not rank_str:
        return ""
    r = int(rank_str)
    if r <= 3:
        return "2"  # thiqah_level
    if r <= 6:
        return "1"  # saduq_level
    return "0"      # weak_and_below


def write_csv_lf(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def run_build(out_dir: Path = DEFAULT_OUT_DIR, wuththiqa_policy: str = DEFAULT_WUTHTHIQA_POLICY) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    k_entries = parse_kashif_entries(KASHIF_PAGES)
    prov_check = verify_narrators_csv_provenance(k_entries)

    # Load Taqrib master + layered scores
    with MASTER_NODES.open("r", encoding="utf-8-sig", newline="") as f:
        t_rows = list(csv.DictReader(f))
    t_by_id = {r["entry_id"]: r for r in t_rows}

    with LAYERED_WIDE.open("r", encoding="utf-8-sig", newline="") as f:
        l_by_id = {r["entry_id"]: r for r in csv.DictReader(f)}

    # Tahrir commentary, for the symmetric overlap check and the al-Dhahabi citation flag
    with TAHRIR_ALIGNED.open("r", encoding="utf-8-sig", newline="") as f:
        tahrir_comm_by_id = {r["entry_id"]: r.get("tahrir_commentary_text", "") or "" for r in csv.DictReader(f)}

    with TASK_B_NODES.open("r", encoding="utf-8-sig", newline="") as f:
        eid_to_sid = {r["entry_id"]: r["shamela_narrator_id"] for r in csv.DictReader(f) if r["shamela_narrator_id"]}
    sid_to_eid = {v: k for k, v in eid_to_sid.items()}

    sid_info: dict[str, tuple[str, str, str]] = {}
    with SHAMELA_NARRATORS_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row["id"] in sid_to_eid:
                bio = json.loads(row["biography_text"]) if row.get("biography_text") else {}
                sm = dict(bio.get("summary", []))
                sid_info[row["id"]] = (row["short_name"], row["long_name"], sm.get("الرتبة عند الذهبي", ""))

    # Build Kashif entry table + index
    k_parsed_rows: list[dict[str, str]] = []
    k_meta: list[tuple[int, str, str, tuple[str, ...], frozenset[str], tuple[str, ...], dict[str, str]]] = []
    k_by_n3: dict[tuple[str, ...], list[int]] = defaultdict(list)
    k_by_n2: dict[tuple[str, ...], list[int]] = defaultdict(list)

    for idx, ke in enumerate(k_entries):
        full = " ".join(ke["lines"])
        toks = extract_name_tokens(full)
        _, raw_sig = strip_sigils(full)
        cb = canon_sigil_books(raw_sig)
        vinfo = extract_kashif_verdict(full, wuththiqa_policy=wuththiqa_policy)
        name_hdr = " ".join(toks[:6])
        k_uid = f"K1616-{idx+1:04d}-E{ke['num']:04d}"
        ke["k_uid"] = k_uid
        k_meta.append((idx, full, norm_ar(full), tuple(toks), cb, raw_sig, vinfo))
        if len(toks) >= 3:
            k_by_n3[tuple(toks[:3])].append(idx)
        if len(toks) >= 2:
            k_by_n2[tuple(toks[:2])].append(idx)

        k_parsed_rows.append(
            {
                "kashif_uid": k_uid,
                "kashif_entry_num": str(ke["num"]),
                "part": ke["part"],
                "printed_page": ke["page_num"],
                "name_header": name_hdr,
                "verdict_span": vinfo["verdict_span"],
                "verdict_region_source": vinfo["region_src"],
                "kashif_tier_3": vinfo["tier_3"],
                "kashif_tier_3_label": vinfo["tier_3_label"],
                "kashif_tier_5": vinfo["tier_5"],
                "kashif_rule_id": vinfo["rule_id"],
                "is_sahabi": vinfo["is_sahabi"],
                "sigils_raw": vinfo["sigils_raw"],
                "full_text": full,
            }
        )

    # Index Taqrib for Pass 2
    t_idx: dict[str, tuple[str, tuple[str, ...], frozenset[str], tuple[str, ...]]] = {}
    t_by_n4: dict[tuple[str, ...], list[Any]] = defaultdict(list)
    t_by_n3: dict[tuple[str, ...], list[Any]] = defaultdict(list)
    t_by_n2: dict[tuple[str, ...], list[Any]] = defaultdict(list)
    for r in t_rows:
        toks = extract_name_tokens(r["taqrib_text_verbatim"])
        _, raw_s = strip_sigils(r["taqrib_text_verbatim"])
        cb = canon_sigil_books(raw_s)
        item = (r["entry_id"], tuple(toks), cb, raw_s)
        t_idx[r["entry_id"]] = item
        if len(toks) >= 4:
            t_by_n4[tuple(toks[:4])].append(item)
        if len(toks) >= 3:
            t_by_n3[tuple(toks[:3])].append(item)
        if len(toks) >= 2:
            t_by_n2[tuple(toks[:2])].append(item)

    # Link Pass 1: Shamela narrator ID crosswalk
    k_to_t: dict[int, tuple[str, str, str]] = {}
    used_t: set[str] = set()
    cw_pairs: list[tuple[int, str]] = []
    for sid, (sname, _lname, dh) in sid_info.items():
        eid = sid_to_eid[sid]
        t_item = t_idx[eid]
        sn_toks = tuple("بن" if t == "ابن" else t for t in norm_ar(sname).split())
        dh_n = norm_ar(dh)
        cands: list[int] = []
        if len(sn_toks) >= 3:
            cands = k_by_n3.get(sn_toks[:3], [])
        if not cands and len(sn_toks) >= 2:
            cands = k_by_n2.get(sn_toks[:2], [])
        if len(cands) > 1 and dh_n:
            cands2 = [ci for ci in cands if dh_n in k_meta[ci][2]]
            if cands2:
                cands = cands2
        if len(cands) > 1 and t_item[2]:
            cands2 = [ci for ci in cands if k_meta[ci][4] == t_item[2]]
            if cands2:
                cands = cands2
        if len(cands) == 1:
            ci = cands[0]
            if k_meta[ci][3][:2] == t_item[1][:2] or (t_item[2] and k_meta[ci][4] == t_item[2]):
                cw_pairs.append((ci, eid))

    ci_cnt = Counter(ci for ci, _ in cw_pairs)
    eid_cnt = Counter(eid for _, eid in cw_pairs)
    for ci, eid in cw_pairs:
        if ci_cnt[ci] == 1 and eid_cnt[eid] == 1:
            k_to_t[ci] = (eid, "shamela_crosswalk", "high")
            used_t.add(eid)

    # Link Pass 2: Normalized-name + Six-Books sigil match
    p2_cands: dict[str, list[tuple[int, str, str]]] = defaultdict(list)
    for idx, _full, _full_n, toks, cb, _raw_s, _vinfo in k_meta:
        if idx in k_to_t:
            continue
        # n2 keys (usually just "first name + بن") produced mostly wrong links (review 2026-11-21, M4): dropped.
        for kname, key, mp in [("n4", toks[:4], t_by_n4), ("n3", toks[:3], t_by_n3)]:
            if len(key) < int(kname[1]):
                continue
            cands = [c for c in mp.get(key, []) if c[0] not in used_t]
            if not cands:
                continue
            if len(cands) == 1 and kname in {"n4", "n3"} and (
                not cb or not cands[0][2] or cb == cands[0][2] or cb.issubset(cands[0][2]) or cands[0][2].issubset(cb)
            ):
                p2_cands[cands[0][0]].append((idx, f"{kname}_unique", "high" if kname == "n4" else "medium"))
                break
            if cb:
                sc = [c for c in cands if c[2] == cb]
                if len(sc) == 1:
                    p2_cands[sc[0][0]].append((idx, f"{kname}_sigil_canon", "high"))
                    break
                # Sigil-subset matching only with a 4-token name key (n3_sigil_subset links were all wrong).
                sc2 = [c for c in cands if cb.issubset(c[2]) or c[2].issubset(cb)] if kname == "n4" else []
                if len(sc2) == 1:
                    p2_cands[sc2[0][0]].append((idx, f"{kname}_sigil_subset", "medium"))
                    break

    for eid, hits in p2_cands.items():
        if len(hits) == 1:
            ci, meth, conf = hits[0]
            k_to_t[ci] = (eid, meth, conf)

    # Build Link table & Overlap audit
    link_rows: list[dict[str, str]] = []
    overlap_rows: list[dict[str, str]] = []
    link_methods = Counter()
    tier3_counts = Counter()
    mapped_overlap_true = 0
    mapped_total = 0

    for idx, _full, _full_n, toks, _cb, raw_sig, vinfo in k_meta:
        if idx not in k_to_t:
            continue
        eid, meth, conf = k_to_t[idx]
        link_methods[meth] += 1
        trow = t_by_id[eid]
        lrow = l_by_id[eid]
        taq_norm = norm_ar(trow["taqrib_text_verbatim"])
        vspan = vinfo["verdict_span"]
        vspan_norm = norm_ar(vspan)

        # Symmetric verbatim overlap (review 2026-11-21, H1): the al-Kashif span counts as copied
        # if it appears in the Taqrib text OR in the Tahrir commentary, so neither B nor E2 is favoured.
        tahrir_comm = tahrir_comm_by_id.get(eid, "")
        tahrir_norm = norm_ar(tahrir_comm)
        ov_taqrib = bool(vspan_norm and vspan_norm in taq_norm)
        ov_tahrir = bool(vspan_norm and vspan_norm in tahrir_norm)
        verbatim_ov = ov_taqrib or ov_tahrir
        cites_dh = bool(PAT_TAHRIR_CITES_DHAHABI.search(DIACRITICS_RE.sub("", tahrir_comm).replace("أ", "ا").replace("إ", "ا")))
        if vinfo["tier_3"] != "":
            mapped_total += 1
            if verbatim_ov:
                mapped_overlap_true += 1
        tier3_counts[vinfo["tier_3_label"]] += 1

        link_rows.append(
            {
                "kashif_uid": k_parsed_rows[idx]["kashif_uid"],
                "kashif_entry_num": k_parsed_rows[idx]["kashif_entry_num"],
                "entry_id": eid,
                "link_method": meth,
                "confidence": conf,
                "kashif_name": " ".join(toks[:6]),
                "taqrib_name": " ".join(t_idx[eid][1][:6]),
                "kashif_sigils": " ".join(raw_sig),
                "taqrib_sigils": " ".join(t_idx[eid][3]),
            }
        )
        overlap_rows.append(
            {
                "kashif_uid": k_parsed_rows[idx]["kashif_uid"],
                "kashif_entry_num": k_parsed_rows[idx]["kashif_entry_num"],
                "entry_id": eid,
                "verdict_span": vspan,
                "verdict_span_norm": vspan_norm,
                "verbatim_overlap": str(verbatim_ov),
                "verbatim_overlap_taqrib": str(ov_taqrib),
                "verbatim_overlap_tahrir": str(ov_tahrir),
                "tahrir_cites_dhahabi": str(cites_dh),
                "link_method": meth,
                "kashif_tier_3": vinfo["tier_3"],
                "kashif_tier_3_label": vinfo["tier_3_label"],
                "kashif_tier_5": vinfo["tier_5"],
                "kashif_rule_id": vinfo["rule_id"],
                "is_sahabi": vinfo["is_sahabi"],
                "rank_B": lrow["rank_B"],
                "taqrib_tier_3": rank_to_tier3(lrow["rank_B"]),
                "rank_E2": lrow["rank_E2"],
                "tahrir_tier_3": rank_to_tier3(lrow["rank_E2"]),
                "status_E2": lrow["status_E2"],
            }
        )

    # Preview 3-tier exact agreement on linked mapped rows (full vs non-verbatim)
    def agreement(sub: list[dict[str, str]], col: str) -> tuple[int, int, float]:
        valid = [r for r in sub if r["kashif_tier_3"] != "" and r[col] != "" and r["status_E2"] not in {"missing", "suspect_alignment"}]
        match = sum(1 for r in valid if r["kashif_tier_3"] == r[col])
        return match, len(valid), (match / len(valid) if valid else 0.0)

    non_verb = [r for r in overlap_rows if r["verbatim_overlap"] == "False"]
    ag_b_full = agreement(overlap_rows, "taqrib_tier_3")
    ag_e2_full = agreement(overlap_rows, "tahrir_tier_3")
    ag_b_nv = agreement(non_verb, "taqrib_tier_3")
    ag_e2_nv = agreement(non_verb, "tahrir_tier_3")

    entries_csv = out_dir / "KASHIF_ENTRIES_V1.csv"
    link_csv = out_dir / "KASHIF_TAQRIB_LINK_V1.csv"
    map_json = out_dir / "KASHIF_GRADE_MAP_V1.json"
    overlap_csv = out_dir / "KASHIF_OVERLAP_AUDIT_V1.csv"
    report_md = out_dir / "REPORT.md"

    write_csv_lf(entries_csv, list(k_parsed_rows[0].keys()), k_parsed_rows)
    write_csv_lf(link_csv, list(link_rows[0].keys()), link_rows)
    map_json.write_bytes((json.dumps(GRADE_MAP_SPEC, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    write_csv_lf(overlap_csv, list(overlap_rows[0].keys()), overlap_rows)

    ov_rate = mapped_overlap_true / mapped_total if mapped_total else 0.0
    report_lines = [
        "# External Validation Dataset Report: al-Dhahabi's *al-Kashif* (Book 1616)",
        "",
        "## 1. Provenance Verification of Shamela4 `narrators.csv` (`الرتبة عند الذهبي`)",
        "",
        f"- Verified **`{prov_check['matched_in_1616_kashif_body']:,} / {prov_check['narrators_csv_with_dhahabi_field']:,}` ({100*prov_check['match_rate']:.2f}%)** of Shamela4 `narrators.csv` `الرتبة عند الذهبي` strings directly inside Book `1616` (*al-Kashif*) after normalizing `بن`/`ابن`.",
        "- Because `narrators.csv` covers only `5,370` narrators and occasionally truncates multi-clause verdicts (e.g., *Ibrahim b. Tahman*), this dataset extracts all **`7,181`** entries directly from raw `1616__الكاشف.../pages.jsonl` with printed volume/page provenance.",
        "",
        "## 2. Parsing, Linking & Mapped-Term Coverage",
        "",
        f"- **Total *al-Kāshif* entries parsed:** `{len(k_parsed_rows):,}`",
        f"- **Unambiguously linked to *Taqrīb* `entry_id`:** `{len(link_rows):,} / {len(k_parsed_rows):,}` (**{100*len(link_rows)/len(k_parsed_rows):.2f}%** of *al-Kāshif*, **{100*len(link_rows)/len(t_rows):.2f}%** of *Taqrīb*)",
        f"- **Linked entries with mapped 3-tier grade:** `{mapped_total:,} / {len(link_rows):,}` (**{100*mapped_total/len(link_rows):.2f}%**); remaining `{len(link_rows) - mapped_total:,}` are silent/biographical or mixed/contested (`unmapped`, never guessed).",
        "",
        "| Link Method | Count |",
        "|---|---:|",
    ]
    for mname, mcnt in link_methods.most_common():
        report_lines.append(f"| `{mname}` | {mcnt:,} |")

    report_lines.extend([
        "",
        "| Mapped 3-Tier Label (Linked Set) | Count |",
        "|---|---:|",
    ])
    for tlabel, tcnt in tier3_counts.most_common():
        report_lines.append(f"| `{tlabel}` | {tcnt:,} |")

    report_lines.extend([
        "",
        "## 3. Verbatim Overlap Audit vs `taqrib_text_verbatim`",
        "",
        f"- **Mapped linked entries with `verbatim_overlap = True`:** `{mapped_overlap_true:,} / {mapped_total:,}` (**{100*ov_rate:.2f}%**).",
        "- **Comparison with `main` v2.0 `24.8%` finding:** In `main` v2.0 Part D.3, `24.8%` measured exact substring overlap of Shamela `narrators.csv` `الرتبة عند الذهبي` (short editorial snippets) inside `taqrib_text_verbatim`. Extracting full multi-word verdict spans directly from `1616` (e.g., `قال أحمد ثبت في كل المشايخ`) reduces exact full-span verbatim overlap while short single-word verdicts (`ثقة`, `صدوق`, `ضعيف`, `صحابي`) still match verbatim in *Taqrīb*; both the full linked set and the strict **non-verbatim subset** are preserved for P5 evaluation.",
        "",
        "## 4. Preview 3-Tier Convergent Agreement (`B` vs `E2` vs *al-Kāshif*)",
        "",
        "| Subset | `score_B` (Ibn Hajar) Match | `score_E2` (Tahrir) Match |",
        "|---|---:|---:|",
        f"| Full linked mapped set | `{ag_b_full[0]:,}/{ag_b_full[1]:,}` (**{100*ag_b_full[2]:.2f}%**) | `{ag_e2_full[0]:,}/{ag_e2_full[1]:,}` (**{100*ag_e2_full[2]:.2f}%**) |",
        f"| Non-verbatim subset (`verbatim_overlap=False`) | `{ag_b_nv[0]:,}/{ag_b_nv[1]:,}` (**{100*ag_b_nv[2]:.2f}%**) | `{ag_e2_nv[0]:,}/{ag_e2_nv[1]:,}` (**{100*ag_e2_nv[2]:.2f}%**) |",
        "",
    ])
    report_md.write_bytes("\n".join(report_lines).encode("utf-8"))

    output_files = [entries_csv, link_csv, map_json, overlap_csv, report_md]
    manifest = {
        "schema_version": "1.1",
        "script": to_posix_relative(Path(__file__), ROOT),
        "wuththiqa_policy": wuththiqa_policy,
        "narrators_csv_provenance_check": prov_check,
        "counts": {
            "kashif_entries_total": len(k_parsed_rows),
            "linked_unambiguous": len(link_rows),
            "link_rate_kashif": round(len(link_rows) / len(k_parsed_rows), 4),
            "mapped_linked_total": mapped_total,
            "mapped_coverage_of_linked": round(mapped_total / len(link_rows), 4) if link_rows else 0.0,
            "verbatim_overlap_count": mapped_overlap_true,
            "verbatim_overlap_rate": round(ov_rate, 4),
            "link_methods": dict(link_methods),
            "tier3_linked_counts": dict(tier3_counts),
            "verbatim_overlap_taqrib_count": sum(1 for r in overlap_rows if r["kashif_tier_3"] != "" and r["verbatim_overlap_taqrib"] == "True"),
            "verbatim_overlap_tahrir_count": sum(1 for r in overlap_rows if r["kashif_tier_3"] != "" and r["verbatim_overlap_tahrir"] == "True"),
            "tahrir_cites_dhahabi_count": sum(1 for r in overlap_rows if r["tahrir_cites_dhahabi"] == "True"),
        },
        "inputs": {
            "1616_pages_jsonl": {
                "path": to_posix_relative(KASHIF_PAGES, ROOT),
                "sha256": sha256_file(KASHIF_PAGES),
            },
            "taqrib_v2_master_nodes": {
                "path": to_posix_relative(MASTER_NODES, ROOT),
                "sha256": sha256_text_normalized(MASTER_NODES),
            },
            "layered_scores_wide_v3": {
                "path": to_posix_relative(LAYERED_WIDE, ROOT),
                "sha256": sha256_text_normalized(LAYERED_WIDE),
            },
        },
        "files": {
            p.name: {"sha256": sha256_text_normalized(p), "bytes": p.stat().st_size}
            for p in output_files
        },
    }
    manifest_path = out_dir / "MANIFEST.json"
    manifest_path.write_bytes((json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    sha_lines = "\n".join(
        f"{sha256_text_normalized(p)}  {p.name}" for p in [*output_files, manifest_path]
    ) + "\n"
    (out_dir / "MANIFEST.sha256").write_bytes(sha_lines.encode("ascii"))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Build al-Kashif (1616) external validation set v1.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument(
        "--wuththiqa-policy",
        choices=WUTHTHIQA_POLICIES,
        default=DEFAULT_WUTHTHIQA_POLICY,
        help="How to map al-Dhahabi's passive وثق: maqbul_r6 (rank 6, saduq tier) or thiqah (v1 mapping).",
    )
    args = parser.parse_args()
    manifest = run_build(out_dir=args.out_dir, wuththiqa_policy=args.wuththiqa_policy)
    print(json.dumps(manifest["counts"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
