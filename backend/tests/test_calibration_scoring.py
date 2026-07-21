"""Unit tests for the calibration scorer (PLAN_Calibration_Analytics Phase 2).

Pure-function tests: band edges, flat thresholds, Brier math, missing-KPI and
malformed-input cases. The scorer must never raise and never require I/O.
"""
import math

from pedagogical_engine import (
    TREASURY_BANDS, REPUTATION_DIRS,
    treasury_band_of, reputation_dir_of, score_prediction,
)


# ── Band edges ───────────────────────────────────────────────────────────────

def test_treasury_band_edges():
    assert treasury_band_of(-5_000_001) == "down_big"
    assert treasury_band_of(-5_000_000) == "down"      # -5M inclusive → down
    assert treasury_band_of(-1_000_001) == "down"
    assert treasury_band_of(-1_000_000) == "flat"      # ±1M inclusive → flat
    assert treasury_band_of(0) == "flat"
    assert treasury_band_of(1_000_000) == "flat"
    assert treasury_band_of(1_000_001) == "up"
    assert treasury_band_of(5_000_000) == "up"
    assert treasury_band_of(5_000_001) == "up_big"


def test_reputation_dir_edges():
    assert reputation_dir_of(-2.0) == "down"
    assert reputation_dir_of(-1.99) == "flat"
    assert reputation_dir_of(0) == "flat"
    assert reputation_dir_of(1.99) == "flat"
    assert reputation_dir_of(2.0) == "up"


def test_none_deltas_are_flat():
    assert treasury_band_of(None) == "flat"
    assert reputation_dir_of(None) == "flat"


# ── Hits and partial predictions ─────────────────────────────────────────────

def test_both_kpis_hit():
    s = score_prediction(
        {"treasury_band": "down", "reputation_dir": "up", "confidence": 0.8},
        treasury_delta=-3_000_000, reputation_delta=4,
    )
    assert s["treasury_hit"] is True and s["reputation_hit"] is True
    assert (s["hits"], s["of"]) == (2, 2)
    assert s["brier"] == round(((0.8 - 1) ** 2 + (0.8 - 1) ** 2) / 2, 4)


def test_one_hit_one_miss_brier():
    s = score_prediction(
        {"treasury_band": "up_big", "reputation_dir": "flat", "confidence": 0.7},
        treasury_delta=200_000, reputation_delta=0.5,
    )
    assert s["treasury_hit"] is False and s["reputation_hit"] is True
    assert (s["hits"], s["of"]) == (1, 2)
    expected = ((0.7 - 0) ** 2 + (0.7 - 1) ** 2) / 2
    assert math.isclose(s["brier"], round(expected, 4))


def test_skipped_kpi_not_counted():
    s = score_prediction(
        {"treasury_band": "flat", "reputation_dir": None, "confidence": 1.0},
        treasury_delta=0, reputation_delta=50,
    )
    assert s["reputation_hit"] is None
    assert (s["hits"], s["of"]) == (1, 1)
    assert s["brier"] == 0.0  # perfect confidence, perfect hit, single KPI


def test_no_confidence_means_no_brier_but_hits_count():
    s = score_prediction(
        {"treasury_band": "flat", "reputation_dir": "down"},
        treasury_delta=0, reputation_delta=-10,
    )
    assert s["brier"] is None
    assert (s["hits"], s["of"]) == (2, 2)


def test_malformed_bands_ignored_not_raised():
    s = score_prediction(
        {"treasury_band": "sideways", "reputation_dir": "up", "confidence": 0.9},
        treasury_delta=9_999_999, reputation_delta=3,
    )
    assert s["treasury_hit"] is None        # invalid band = not predicted
    assert (s["hits"], s["of"]) == (1, 1)


def test_confidence_clamped_into_unit_interval():
    s = score_prediction(
        {"treasury_band": "flat", "confidence": 1.7},
        treasury_delta=0, reputation_delta=0,
    )
    assert s["brier"] == 0.0  # clamped to 1.0, hit → (1-1)² = 0


def test_actual_bands_reported_for_ui():
    s = score_prediction(
        {"reputation_dir": "up", "confidence": 0.6},
        treasury_delta=-8_000_000, reputation_delta=-4,
    )
    assert s["actual_treasury_band"] == "down_big"
    assert s["actual_reputation_dir"] == "down"
    assert s["treasury_delta"] == -8_000_000
    assert s["reputation_delta"] == -4


def test_brier_is_proper_scoring_honesty_check():
    """Sanity: in a 50% hit-rate world, reporting 0.5 beats reporting 1.0."""
    preds_honest = [({"treasury_band": "flat", "confidence": 0.5}, 0, 0),
                    ({"treasury_band": "flat", "confidence": 0.5}, 9e6, 0)]
    preds_cocky = [({"treasury_band": "flat", "confidence": 1.0}, 0, 0),
                   ({"treasury_band": "flat", "confidence": 1.0}, 9e6, 0)]
    b = lambda ps: sum(score_prediction(p, t, r)["brier"] for p, t, r in ps) / len(ps)
    assert b(preds_honest) < b(preds_cocky)
