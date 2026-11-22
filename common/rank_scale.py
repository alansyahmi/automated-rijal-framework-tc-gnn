"""Ibn Hajar 12-rank -> 0-100 reliability scale (single source of truth).

Two scales are available:

* ``linear_v1``: the original equal-interval map, ``100 * (12 - rank) / 11``.
  Kept so earlier results can be reproduced exactly.
* ``hukm_v1`` (default): anchored on the hadith-grade consequence (hukm) of each
  rank. Three lines are fixed: 80 = sahih, 50 = accepted when it stands alone
  (maqbul vs mardud), 25 = usable for i'tibar (corroboration). Rank 5 sits
  below the 50 line (45), following Tahrir Taqrib al-Tahdhib, introduction
  pp. 46-48 (uncommented "صدوق يهم" and "مقبول" are "ضعيف يعتبر به").
  Rationale and sources: reviews/ibn-hajar-12-rank-0-100-scale-2026-11-22.md.

Tahrir's bare "ضعيف" is stricter than Ibn Hajar's rank 8: the Tahrir editors
say that a "ضعيف" they leave uncommented, or write without "يعتبر به", is not
usable for corroboration (Tahrir intro p. 47). Under ``hukm_v1`` that verdict
keeps rank 8 as its ordinal label but gets ``TAHRIR_DAIF_NO_ITIBAR_SCORE``
(below the 25 line). It sits above the midpoint between ranks 9 and 10, so the
inverse map still reads it as rank 9 and no ordinal/tier metric moves.
Under ``linear_v1`` there is no split (old behaviour).
"""
from __future__ import annotations

import os

import numpy as np

SCALES: dict[str, dict[int, float]] = {
    "linear_v1": {r: 100.0 * (12.0 - r) / 11.0 for r in range(1, 13)},
    "hukm_v1": {
        1: 100.0,  # Companions: status category (display only; flag is_sahabi)
        2: 95.0,
        3: 85.0,   # sahih line = 80
        4: 70.0,   # accepted-alone line = 50
        5: 45.0,
        6: 40.0,
        7: 35.0,
        8: 30.0,
        9: 27.0,   # i'tibar line = 25
        10: 15.0,
        11: 5.0,
        12: 0.0,
    },
}

# Thresholds for each scale (score >= threshold).
THRESHOLDS: dict[str, dict[str, float]] = {
    "linear_v1": {"tadil_jarh_wording": 50.0},
    "hukm_v1": {"sahih": 80.0, "accepted_alone": 50.0, "itibar": 25.0},
}

# Score for Tahrir's bare "ضعيف" (not usable for i'tibar). None = no split.
TAHRIR_DAIF_NO_ITIBAR_SCORE: dict[str, float | None] = {
    "linear_v1": None,
    "hukm_v1": 22.0,
}

DEFAULT_SCALE = os.environ.get("RIJAL_RANK_SCALE", "hukm_v1")


def check_scale(scale: str) -> str:
    if scale not in SCALES:
        raise ValueError(f"unknown rank scale {scale!r}; choose from {sorted(SCALES)}")
    return scale


def _xy(scale: str) -> tuple[np.ndarray, np.ndarray]:
    m = SCALES[check_scale(scale)]
    ranks = np.arange(1, 13, dtype=float)
    scores = np.array([m[r] for r in range(1, 13)], dtype=float)
    return ranks, scores


def rank_to_score(rank: float, scale: str = DEFAULT_SCALE) -> float:
    """Map a (possibly fractional) rank in [1, 12] to 0-100, piecewise linear."""
    ranks, scores = _xy(scale)
    return float(np.interp(float(rank), ranks, scores))


def score_to_rank_cont(score: float, scale: str = DEFAULT_SCALE) -> float:
    """Inverse of ``rank_to_score``: continuous rank in [1, 12]."""
    ranks, scores = _xy(scale)
    # np.interp needs increasing x: scores decrease with rank, so reverse both.
    return float(np.interp(float(score), scores[::-1], ranks[::-1]))


def tahrir_daif_no_itibar_score(scale: str = DEFAULT_SCALE) -> float | None:
    return TAHRIR_DAIF_NO_ITIBAR_SCORE[check_scale(scale)]


def band_half_width(scale: str = DEFAULT_SCALE) -> float:
    """Half of one linear step (100/22). Kept identical across scales so the
    E1/E2 qualifier weights (expressed in h) keep the same size in points."""
    check_scale(scale)
    return 100.0 / 22.0
