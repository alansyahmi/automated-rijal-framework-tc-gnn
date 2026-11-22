"""Unit and integration tests for deterministic layered scores (B, E1, E2) v3."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

from dataset_discovery.target_feasibility.build_layered_scores_v3 import (
    DEFAULT_OUT_DIR,
    DEFAULT_RULES_PATH,
    run_build,
)
from common.rank_scale import (
    THRESHOLDS,
    local_band_half_width,
    rank_to_score,
    tahrir_daif_no_itibar_score,
)

WIDE_CSV = DEFAULT_OUT_DIR / "LAYERED_SCORES_WIDE_V3.csv"
EVIDENCE_CSV = DEFAULT_OUT_DIR / "LAYER_EVIDENCE_LONG_V3.csv"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_scores_within_bounds_and_e1_inside_band() -> None:
    rules = json.loads(DEFAULT_RULES_PATH.read_text(encoding="utf-8"))
    cap_mult = float(rules["layer_E1"]["cap_in_h"])
    wide = _read_csv(WIDE_CSV)
    assert len(wide) == 8827

    for row in wide:
        sc = row["rank_scale"]
        for col in ("score_B", "score_E1", "score_E2"):
            val = row[col]
            if val != "":
                num = float(val)
                assert 0.0 - 1e-6 <= num <= 100.0 + 1e-6, f"{row['entry_id']} {col}={num}"
        if row["score_B"] != "" and row["score_E1"] != "":
            sb = float(row["score_B"])
            se1 = float(row["score_E1"])
            r_b = int(row["rank_B"])
            down_cap = cap_mult * local_band_half_width(r_b, -1.0, sc)
            up_cap = cap_mult * local_band_half_width(r_b, 1.0, sc)
            diff = se1 - sb
            assert -down_cap - 1e-5 <= diff <= up_cap + 1e-5, (
                f"{row['entry_id']} E1 exceeded local band [-{down_cap}, +{up_cap}]: diff={diff}"
            )
            for thr in THRESHOLDS[sc].values():
                assert (sb >= thr) == (se1 >= thr), (
                    f"{row['entry_id']} E1 crossed threshold {thr}: score_B={sb}, score_E1={se1}"
                )


def test_provenance_closure_from_evidence_table() -> None:
    wide = _read_csv(WIDE_CSV)
    evidence = _read_csv(EVIDENCE_CSV)
    ev_by_id: dict[str, list[dict[str, str]]] = defaultdict(list)
    for ev in evidence:
        ev_by_id[ev["entry_id"]].append(ev)

    for row in wide:
        eid = row["entry_id"]
        evs = ev_by_id[eid]
        assert int(row["n_evidence_rows"]) == len(evs)

        sum_b_e1 = sum(float(e["delta_0_100"]) for e in evs if e["layer"] in {"B", "E1"})
        sum_all = sum(float(e["delta_0_100"]) for e in evs)
        if row["score_E1"] != "":
            assert abs(sum_b_e1 - float(row["score_E1"])) < 1e-4, f"{eid} score_E1 closure failed"
        if row["score_E2"] != "":
            assert abs(sum_all - float(row["score_E2"])) < 1e-4, f"{eid} score_E2 closure failed"


def test_no_double_counting_inside_rank_span() -> None:
    evidence = _read_csv(EVIDENCE_CSV)
    inside_rows = [e for e in evidence if e["double_count_check"] == "inside_rank_span"]
    assert len(inside_rows) > 0
    for ev in inside_rows:
        assert abs(float(ev["delta_0_100"])) == 0.0, f"{ev['entry_id']} double-counted {ev['rule_id']}"


def test_agreed_no_bullet_and_maqbul_rules() -> None:
    wide = _read_csv(WIDE_CSV)
    agreed = [r for r in wide if r["status_E2"] == "observed_agreement"]
    assert len(agreed) > 3000
    for row in agreed:
        assert row["tahrir_disposition"] == "agreed_no_bullet"
        assert row["tahrir_confirms_B"] == "True"
        if row["tahrir_r8_itibar"] == "False" and row["rank_scale"] == "hukm_v1":
            # Tahrir intro p. 47: silent agreement with "ضعيف" = not usable for i'tibar
            assert abs(float(row["delta_E2"]) - (tahrir_daif_no_itibar_score("hukm_v1") - rank_to_score(8, "hukm_v1"))) < 1e-6
        else:
            assert abs(float(row["delta_E2"])) == 0.0

    maqbul_r7 = [r for r in wide if r["status_E2"] == "observed_maqbul_to_r7"]
    assert len(maqbul_r7) > 300
    for row in maqbul_r7:
        assert row["rank_B"] == "6"
        assert row["rank_E2"] == "7"
        assert row["taqrib_is_conditional_maqbul"] == "True"


def test_missing_and_suspect_rows_never_counted_as_agreement() -> None:
    wide = _read_csv(WIDE_CSV)
    evidence = _read_csv(EVIDENCE_CSV)

    missing_wide = [r for r in wide if r["status_E2"] == "missing"]
    assert len(missing_wide) == 10
    for row in missing_wide:
        assert row["tahrir_confirms_B"] == "False"
        assert row["rank_E2"] == ""
        if row["delta_E2"] != "":
            assert abs(float(row["delta_E2"])) == 0.0

    suspect_wide = [r for r in wide if r["status_E2"] == "suspect_alignment"]
    assert len(suspect_wide) == 57
    for row in suspect_wide:
        assert row["tahrir_confirms_B"] == "False"
        if row["delta_E2"] != "":
            assert abs(float(row["delta_E2"])) == 0.0
        else:
            assert row["status_B"] == "abstained"

    for ev in evidence:
        if ev["status"] == "missing":
            assert abs(float(ev["delta_0_100"])) == 0.0


def test_gold50_golden_cases() -> None:
    wide = {r["entry_id"]: r for r in _read_csv(WIDE_CSV)}
    ev_by_id: dict[str, list[dict[str, str]]] = defaultdict(list)
    for ev in _read_csv(EVIDENCE_CSV):
        ev_by_id[ev["entry_id"]].append(ev)

    # Ikrimah: rank 2
    ikrimah = wide["S3076-P397-C001-E4673"]
    assert ikrimah["rank_B"] == "2"
    assert ikrimah["rank_E2"] == "2"

    # Sufyan b. Husayn: في غير الزهري correction (rank 3, conditional scope)
    sufyan = wide["S3076-P244-C002-E2437"]
    assert sufyan["rank_B"] == "3"
    assert any("في غير الزهري" in e["arabic_span"] for e in ev_by_id["S3076-P244-C002-E2437"])

    # Muqatil b. Sulayman: rank 12
    muqatil = wide["S3076-P545-C001-E6868"]
    assert muqatil["rank_B"] == "12"
    assert abs(float(muqatil["score_B"]) - 0.0) < 1e-6

    # Layth b. Abi Sulaym: rank 4 with اختلط E1 penalty
    layth = wide["S3076-P464-C010-E5685"]
    assert layth["rank_B"] == "4"
    assert float(layth["delta_E1"]) < 0.0
    assert "qual_ikhtalata" in layth["e1_rules_applied"]


def test_deterministic_byte_identical_rebuild(tmp_path: Path) -> None:
    out_a = tmp_path / "run_a"
    out_b = tmp_path / "run_b"
    run_build(out_dir=out_a)
    run_build(out_dir=out_b)

    files_a = {p.name: p.read_bytes() for p in sorted(out_a.iterdir())}
    files_b = {p.name: p.read_bytes() for p in sorted(out_b.iterdir())}
    assert files_a == files_b


def test_rank_scales_monotone_and_invertible() -> None:
    from common.rank_scale import SCALES, THRESHOLDS, score_to_rank_cont

    for name, m in SCALES.items():
        vals = [m[r] for r in range(1, 13)]
        assert all(a > b for a, b in zip(vals, vals[1:])), name
        for r in range(1, 13):
            assert abs(score_to_rank_cont(rank_to_score(r, name), name) - r) < 1e-9
    hk = SCALES["hukm_v1"]
    t = THRESHOLDS["hukm_v1"]
    # Alan, 2026-11-22: rank 5 below the accepted-alone line; ranks 5-9 usable for i'tibar
    assert hk[4] >= t["accepted_alone"] > hk[5]
    assert all(t["itibar"] <= hk[r] < t["accepted_alone"] for r in range(5, 10))
    assert hk[10] < t["itibar"]
    d = tahrir_daif_no_itibar_score("hukm_v1")
    assert hk[10] < d < t["itibar"]
    # still reads back as rank 9 so ordinal/tier metrics are unchanged
    assert round(score_to_rank_cont(d, "hukm_v1")) == 9
    assert tahrir_daif_no_itibar_score("linear_v1") is None


def test_linear_scale_reproduces_original_formula() -> None:
    for r in range(1, 13):
        assert abs(rank_to_score(r, "linear_v1") - 100.0 * (12 - r) / 11.0) < 1e-12


def test_local_band_half_width_respects_gaps_and_thresholds() -> None:
    for r in range(2, 12):
        assert abs(local_band_half_width(r, -1.0, "linear_v1") - 100.0 / 22.0) < 1e-9
        # Rank 7 sits 100/22 below the 50.0 midpoint threshold and is shaved by 1e-6 so S(7)+delta < 50.
        tol = 2e-6 if r == 7 else 1e-9
        assert abs(local_band_half_width(r, 1.0, "linear_v1") - 100.0 / 22.0) < tol
        if r == 7:
            assert rank_to_score(r, "linear_v1") + local_band_half_width(r, 1.0, "linear_v1") < 50.0
    # hukm_v1: Rank 8->9 gap is 3.0 -> half=1.5; Rank 9 is 27 with i'tibar threshold 25 -> cap 2.0
    assert abs(local_band_half_width(8, -1.0, "hukm_v1") - 1.5) < 1e-9
    assert abs(local_band_half_width(9, -1.0, "hukm_v1") - 2.0) < 1e-9
    assert abs(local_band_half_width(3, -1.0, "hukm_v1") - 5.0) < 1e-9
    assert rank_to_score(5, "hukm_v1") + local_band_half_width(5, 1.0, "hukm_v1") < 50.0


def test_praise_is_evidence_only_and_e2_band_replacements_do_not_inherit_e1() -> None:
    evidence = _read_csv(EVIDENCE_CSV)
    praise_obs = [
        ev for ev in evidence
        if ev["rule_id"] in {"E1-PRAISE_HAFIZ", "E1-PRAISE_FAQIH"} and ev["status"] == "observed"
    ]
    assert len(praise_obs) > 0
    for ev in praise_obs:
        assert abs(float(ev["delta_0_100"])) == 0.0
        assert ev["double_count_check"] == "descriptive_evidence_only"

    wide = _read_csv(WIDE_CSV)
    for row in wide:
        st = row["status_E2"]
        sc = row["rank_scale"]
        if st in {"observed_dissent", "observed_maqbul_to_r7"}:
            r2 = int(row["rank_E2"])
            if row["tahrir_r8_itibar"] == "False" and sc == "hukm_v1":
                expected = tahrir_daif_no_itibar_score("hukm_v1")
            else:
                expected = rank_to_score(r2, sc)
            assert expected is not None
            assert abs(float(row["score_E2"]) - expected) < 1e-6, (
                f"{row['entry_id']} ({st}) unexpectedly inherited E1 delta into score_E2"
            )


def test_e1_arabic_linguistic_guards() -> None:
    wide = {r["entry_id"]: r for r in _read_csv(WIDE_CSV)}
    ev_by_id: dict[str, list[dict[str, str]]] = defaultdict(list)
    for ev in _read_csv(EVIDENCE_CSV):
        ev_by_id[ev["entry_id"]].append(ev)

    excluded_expectations = [
        ("S3076-P547-C009-E6908", "E1-QUAL_YUDALLIS", "negated_qualifier"),
        ("S3076-P583-C019-E7454", "E1-QUAL_YUDALLIS", "negated_qualifier"),
        ("S3076-P583-C019-E7454", "E1-QUAL_YUKHTI_YAHIM", "negated_qualifier"),
        ("S3076-P540-C015-E6802", "E1-QUAL_YUKHTI_YAHIM", "negated_qualifier"),
        ("S3076-P547-C005-E6904", "E1-QUAL_YUKHTI_YAHIM", "third_party_subject"),
        ("S3076-P259-C015-E2684", "E1-QUAL_YUKHTI_YAHIM", "third_party_subject"),
        ("S3076-P606-C005-E7793", "E1-QUAL_LIN", "refuted_criticism"),
        ("S3076-P485-C015-E5986", "E1-QUAL_IKHTALATA", "teacher_confusion"),
        ("S3076-P138-C018-E0911", "E1-QUAL_IKHTALATA", "mitigated_no_narration_after_ikhtilat"),
    ]
    for eid, rule_id, reason in excluded_expectations:
        matches = [e for e in ev_by_id[eid] if e["rule_id"] == rule_id]
        assert len(matches) == 1, f"Missing excluded evidence row {rule_id} for {eid}"
        assert matches[0]["status"] == "not_applicable"
        assert matches[0]["double_count_check"] == reason
        assert abs(float(matches[0]["delta_0_100"])) == 0.0
        rule_key = rule_id.removeprefix("E1-").lower()
        assert rule_key not in wide[eid]["e1_rules_applied"]

    # E0911 still receives qual_yukhti_yahim while qual_ikhtalata is excluded
    assert "qual_yukhti_yahim" in wide["S3076-P138-C018-E0911"]["e1_rules_applied"]
    # Positive controls remain observed and numeric
    assert "qual_yukhti_yahim" in wide["S3076-P243-C003-E2424"]["e1_rules_applied"]
    assert "qual_yukhti_yahim" in wide["S3076-P139-C002-E0916"]["e1_rules_applied"]
    assert "qual_ikhtalata" in wide["S3076-P464-C010-E5685"]["e1_rules_applied"]
