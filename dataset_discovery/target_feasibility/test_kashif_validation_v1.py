"""Unit and integrity tests for al-Kashif (1616) external validation v1."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from dataset_discovery.target_feasibility.build_kashif_validation_v1 import DEFAULT_OUT_DIR, extract_kashif_verdict


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_kashif_entries_and_grade_map_integrity() -> None:
    entries = _read_csv(DEFAULT_OUT_DIR / "KASHIF_ENTRIES_V1.csv")
    assert len(entries) >= 7000
    grade_map = json.loads((DEFAULT_OUT_DIR / "KASHIF_GRADE_MAP_V1.json").read_text(encoding="utf-8"))
    allowed_t3 = set(grade_map["tier_3_labels"].keys())
    allowed_t5 = set(grade_map["tier_5_labels"].keys())
    for row in entries:
        assert row["kashif_tier_3"] in allowed_t3
        assert row["kashif_tier_5"] in allowed_t5
        if row["kashif_tier_3"] == "":
            assert row["kashif_tier_3_label"] == "unmapped"


def test_kashif_taqrib_links_are_strictly_one_to_one() -> None:
    links = _read_csv(DEFAULT_OUT_DIR / "KASHIF_TAQRIB_LINK_V1.csv")
    assert len(links) >= 5000
    k_ids = [r["kashif_uid"] for r in links]
    t_ids = [r["entry_id"] for r in links]
    assert len(k_ids) == len(set(k_ids)), "Duplicate kashif_uid in link table"
    assert len(t_ids) == len(set(t_ids)), "Duplicate Taqrib entry_id in link table"


def test_kashif_overlap_audit_and_manifest() -> None:
    overlap = _read_csv(DEFAULT_OUT_DIR / "KASHIF_OVERLAP_AUDIT_V1.csv")
    assert len(overlap) >= 5000
    mapped = [r for r in overlap if r["kashif_tier_3"] != ""]
    verb_true = [r for r in mapped if r["verbatim_overlap"] == "True"]
    verb_false = [r for r in mapped if r["verbatim_overlap"] == "False"]
    assert len(verb_true) > 500
    assert len(verb_false) > 2000

    manifest_text = (DEFAULT_OUT_DIR / "MANIFEST.json").read_text(encoding="utf-8")
    assert "\\" not in manifest_text


def test_kashif_links_exclude_weak_name_keys() -> None:
    links = _read_csv(DEFAULT_OUT_DIR / "KASHIF_TAQRIB_LINK_V1.csv")
    methods = {r["link_method"] for r in links}
    assert not any(m.startswith("n2_") for m in methods), methods
    assert "n3_sigil_subset" not in methods


def test_kashif_overlap_audit_is_symmetric() -> None:
    overlap = _read_csv(DEFAULT_OUT_DIR / "KASHIF_OVERLAP_AUDIT_V1.csv")
    for r in overlap:
        expected = r["verbatim_overlap_taqrib"] == "True" or r["verbatim_overlap_tahrir"] == "True"
        assert (r["verbatim_overlap"] == "True") == expected
        assert r["tahrir_cites_dhahabi"] in {"True", "False"}


_STUB = "١- فلان بن فلان الكوفي عن أبيه وعنه ابنه "


@pytest.mark.parametrize(
    "verdict, tier_3",
    [
        ("صدوق", "1"),
        ("صدوق حافظ", "1"),  # title must not override an explicit grade
        ("حافظ صدوق", "1"),
        ("صدوق وثقه أحمد", "1"),  # al-Dhahabi's own leading verdict beats a quoted tawthiq
        ("قال أحمد ثقة وقال أبو حاتم صدوق", ""),  # two quoted critics disagree: unmapped
        ("ثقة", "2"),
        ("ثقة حافظ", "2"),
    ],
)
def test_kashif_verdict_rule_order(verdict: str, tier_3: str) -> None:
    assert extract_kashif_verdict(_STUB + verdict + " مات ٢٠٠ د")["tier_3"] == tier_3


def test_kashif_title_only_in_name_region_is_fallback() -> None:
    v = extract_kashif_verdict("١- فلان بن فلان الحافظ عن أبيه وعنه ابنه ضعفوه مات ٢٠٠ د")
    assert v["tier_3"] == "0"


def test_kashif_wuththiqa_policy_switch() -> None:
    text = _STUB + "وثق مات ٢٠٠ د"
    assert extract_kashif_verdict(text, wuththiqa_policy="thiqah")["tier_3"] == "2"
    v = extract_kashif_verdict(text, wuththiqa_policy="maqbul_r6")
    assert (v["tier_3"], v["tier_5"], v["rule_id"]) == ("1", "3", "KASHIF-T3-1-WUTHTHIQA-MAQBUL")
    with pytest.raises(ValueError):
        extract_kashif_verdict(text, wuththiqa_policy="other")
