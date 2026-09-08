"""One SDG quantity — the Phase 4 unification, and the trap it avoids.

WHAT WAS WRONG
    The simulation carried TWO SDG numbers that had never been connected.

      sdg_index          engine.calc_sdg_impact, 0-100, recomputed every round
                         from BU metrics across all 17 goals. Consumed by one
                         event key and a narrative line. Graded nothing.
      sdg_impact_score   side_tracks/corporate_sdg, -11..105, written only by
                         that track. The SOLE input to M_SDG, which multiplies
                         terminal value directly. Zero in every session that did
                         not play the track — so for almost every cohort the whole
                         SDG dimension was inert, while a full SDG report sat
                         beside it doing nothing.

WHY THE OBVIOUS FIX IS A TRAP
    Feeding sdg_index to the old formula looks like a one-line correction. It is
    not: the formula is anchored at ZERO, and the index is ~73.5 for a team that
    has done nothing at all — measured identical on six of the seven golden-matrix
    paths at R1. So the naive wire multiplies EVERY session's terminal value by
    about 1.22, including every session already played and debriefed, and it does
    it for standing still. test_the_naive_wire_would_inflate_every_session_and_is_not_what_we_did
    keeps that number in front of whoever reads this next.

THE FIX
    One quantity: the index, with the side track folded into it at
    config.SDG_TRACK_WEIGHT per point. One formula, with a neutral point:
    M_SDG = 1 + (index − SDG_INDEX_NEUTRAL)/100 × SDG_MULTIPLIER_COEFF. The
    coefficient is left at the value the original design chose, so the only thing
    2026.10 changes is what it is applied to.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

_BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND))
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault("USE_MEMORY_DB", "true")

import golden_matrix_harness as H                      # noqa: E402
import rules as R                                      # noqa: E402
from config import (SDG_INDEX_NEUTRAL, SDG_MULTIPLIER_COEFF,   # noqa: E402
                    SDG_TRACK_WEIGHT)
from engine import calc_sdg_impact                     # noqa: E402
from terminal_valuation import calculate_sdg_multiplier  # noqa: E402

_BUS = [{"bu_id": "x", "carbon_intensity": 30, "social_license_score": 60,
         "natural_capital_debt": 40, "governance_risk_score": 20,
         "water_dependency": 30, "revenue_base": 10_000_000,
         "opex_base": 6_000_000, "staff_burnout_index": 15}]


# ═══════════════════════════════════════════════════════════════════
#  THE COMPATIBILITY GUARANTEE
# ═══════════════════════════════════════════════════════════════════

def test_the_formula_is_bit_identical_at_the_old_defaults():
    """calculate_sdg_multiplier gained two parameters. With neutral=0 it must be
    the function it was, to the last decimal, or every past session's terminal
    value moves."""
    assert calculate_sdg_multiplier(0.0)["m_sdg"] == 1.0
    assert calculate_sdg_multiplier(105.0)["m_sdg"] == 1.2625
    assert calculate_sdg_multiplier(-11.0)["m_sdg"] == 0.9725
    for score in (0, 12.5, 37, 68, 105, -11):
        assert calculate_sdg_multiplier(score)["m_sdg"] == round(
            1.0 + (score / 100.0) * 0.25, 4)


def test_the_baseline_keeps_the_two_quantities_apart():
    """Under 2026.09 the index must not move when the side track scores, and the
    track must remain the only thing M_SDG sees."""
    without = calc_sdg_impact(_BUS, {})
    with_track = calc_sdg_impact(_BUS, {"sdg_impact_score": 80})
    assert without["sdg_index"] == with_track["sdg_index"], (
        "the side track is leaking into the index under the baseline rules")
    assert with_track["sdg_track_contribution"] == 0.0


# ═══════════════════════════════════════════════════════════════════
#  THE TRAP
# ═══════════════════════════════════════════════════════════════════

def test_the_naive_wire_would_inflate_every_session_and_is_not_what_we_did():
    """The number that justifies the neutral point. Keep it measured, not
    remembered: if the index's resting level ever moves, this fails and the
    calibration needs revisiting rather than the test needs relaxing."""
    resting = [H.run_path(name)[0]["sdg_index"] for name in H.PATHS]
    typical = max(set(resting), key=resting.count)
    assert typical == pytest.approx(SDG_INDEX_NEUTRAL, abs=1.5), (
        f"the opening SDG index is now {typical}, and config.SDG_INDEX_NEUTRAL is "
        f"{SDG_INDEX_NEUTRAL}. The neutral point is what stops a do-nothing team "
        "collecting an SDG bonus; re-derive it.")

    naive = calculate_sdg_multiplier(typical)["m_sdg"]              # anchored at 0
    ours = calculate_sdg_multiplier(typical, neutral=SDG_INDEX_NEUTRAL)["m_sdg"]
    assert naive > 1.18, f"the naive wire's uplift has changed: {naive}"
    assert ours == 1.0, (
        "a team that has done nothing must land on a neutral multiplier; it is "
        f"landing on {ours}")


def test_a_session_without_the_side_track_is_not_penalised():
    """The other half of the trap. A missing SDG report must read as "no opinion",
    never as an index of zero — which would be M_SDG 0.82, a savage penalty for a
    cohort that simply did not play the optional track."""
    import round_logic
    neutral_state = {"active_event_flags": {R.RULES_FLAG: "2026.10"}}
    assert round_logic._sdg_multiplier_for(neutral_state)["m_sdg"] == 1.0
    # …and the naive alternative, for contrast.
    assert calculate_sdg_multiplier(0.0, neutral=SDG_INDEX_NEUTRAL)["m_sdg"] < 0.83


# ═══════════════════════════════════════════════════════════════════
#  THE UNIFICATION
# ═══════════════════════════════════════════════════════════════════

def test_the_side_track_folds_into_the_index():
    base = calc_sdg_impact(_BUS, {R.RULES_FLAG: "2026.10"})
    folded = calc_sdg_impact(_BUS, {R.RULES_FLAG: "2026.10", "sdg_impact_score": 80})
    assert folded["sdg_track_contribution"] == pytest.approx(80 * SDG_TRACK_WEIGHT)
    assert folded["sdg_index"] == pytest.approx(
        base["sdg_index"] + 80 * SDG_TRACK_WEIGHT, abs=0.1)
    # A track-less session is untouched — the property that makes the fold safe.
    assert calc_sdg_impact(_BUS, {R.RULES_FLAG: "2026.10"})["sdg_index"] == base["sdg_index"]


def test_the_fold_respects_the_index_ceiling():
    """The index is a 0-100 score. A maxed side track on an already-high index
    must not produce 112."""
    high = [dict(_BUS[0], carbon_intensity=0, social_license_score=100,
                 natural_capital_debt=0, governance_risk_score=0)]
    out = calc_sdg_impact(high, {R.RULES_FLAG: "2026.10", "sdg_impact_score": 105})
    assert 0.0 <= out["sdg_index"] <= 100.0, out["sdg_index"]


def test_the_sdg_dimension_now_discriminates_between_paths():
    """The point of the change. Under the baseline M_SDG is 1.0 for every matrix
    session, because none plays the side track — the whole dimension is inert.
    Under 2026.10 it separates them."""
    baseline = set()
    revived = {}
    for name in H.PATHS:
        gs09, _ = H.final_state(name, rules_version="2026.09")
        gs10, _ = H.final_state(name, rules_version="2026.10")
        baseline.add((gs09["active_event_flags"] or {}).get("sdg_multiplier"))
        revived[name] = (gs10["active_event_flags"] or {}).get("sdg_multiplier")

    assert baseline == {1.0}, (
        f"the baseline M_SDG is no longer uniformly inert: {baseline}")
    assert len(set(revived.values())) > 1, (
        "M_SDG is the same for every path under the revived rules; the dimension "
        "is still not discriminating")
    assert min(revived.values()) < 1.0 < max(revived.values()), (
        f"the multiplier should cut both ways: {revived}")


def test_the_authority_of_the_lever_is_recorded_for_phase_5():
    """PROVISIONAL CALIBRATION, pinned so it is a decision rather than a drift.

    The inherited coefficient over the index's measured range gives a NARROWER
    lever than the side track had. That may be right — a score every team has
    should probably swing less than an optional deep-dive track — but it is a
    calibration judgement and Phase 5 owns it. This test exists so that moving
    config.SDG_MULTIPLIER_COEFF is a deliberate act.
    """
    assert SDG_MULTIPLIER_COEFF == 0.25, (
        "the SDG coefficient has moved — that is the Phase 5 calibration, and it "
        "needs a delta report and a rules version, not a green test")
    indices = [rec["sdg_index"] for name in H.PATHS
               for rec in H.run_path(name, rules_version="2026.10")[:-1]]
    lo = calculate_sdg_multiplier(min(indices), neutral=SDG_INDEX_NEUTRAL)["m_sdg"]
    hi = calculate_sdg_multiplier(max(indices), neutral=SDG_INDEX_NEUTRAL)["m_sdg"]
    assert 0.85 < lo < 1.0 < hi < 1.15, (
        f"the achievable M_SDG range is now {lo}..{hi}; the old side-track lever "
        "was 0.97..1.26. If this has moved a long way, re-read the calibration "
        "note in config.py before adjusting anything.")


def test_the_projection_and_the_award_read_the_same_quantity():
    """F-15's lesson, applied here. The Consequence-DNA projection showing a team
    an M_SDG derived from a number the finale does not use would be the Mirror
    Debrief bug again in a new place."""
    import ast
    source = (_BACKEND / "consequence_dna_api.py").read_text(encoding="utf-8")
    assert "sdg_single_quantity" in source, (
        "the DNA projection does not consult the rule set, so it will show the "
        "old quantity to a session graded on the new one")
    ast.parse(source)
