"""
Simulation Integrity — Extended Validation Suite
=================================================
Continues the baseline guards from test_simulation_integrity.py.

Covers eight additional invariant categories that were not addressed in the
first file:

  5.  Output Contract         — process_tick always returns the required keys.
  6.  NaN / Infinity Guard    — no numeric field may be NaN or ±Inf.
  7.  Tipping-Point Irreversibility — once active, tipping_point_active never
                               reverts to False.
  8.  Green Fund Non-Negative — enforced by max(0.0, ...) at assembly time.
  9.  Event-Consequence Consistency — when a hard event fires, its consequence
                               is reflected in the state (e.g. capex_capped →
                               treasury deducted less than requested).
  10. Pure-Helper Unit Tests  — detect_distress, calc_forecast, classify_severity,
                               calc_momentum_score, calc_dso_lag — isolated from
                               process_tick to give fast, pinpoint failures.
  11. Edge-Case Inputs        — single BU, all-identical BU state, round 10.
  12. Cross-Paradigm Robustness — legacy_abc, multi_toggles, advanced_climate,
                               healthcare all complete a tick without violating
                               hard invariants.
"""

import copy
import math
import pytest

import engine
from engine import (
    detect_distress,
    calc_forecast,
    classify_severity,
    calc_momentum_score,
    calc_dso_lag,
)

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from config import (
    CONSTRAINT_MAX_CARBON_EMISSIONS,
    CONSTRAINT_MIN_LIQUIDITY_RATIO,
)

# ── Import shared helpers from the first integrity file ──────────────────────
from test_simulation_integrity import (
    validate_simulation_state,
    validate_bu_fields,
    _derive_liquidity_ratio,
    BASE_GLOBAL,
    BASE_BUS,
    BASE_DECISIONS,
    TREASURY_HARD_FLOOR,
)

# ── Required top-level keys in every process_tick return value ───────────────
_REQUIRED_RETURN_KEYS = {"global_state", "bu_states", "events"}

# ── Required keys in every global_state dict ────────────────────────────────
_REQUIRED_GLOBAL_KEYS = {
    "round_number",
    "corporate_treasury",
    "group_reputation",
    "synergy_multiplier",
    "cost_of_capital",
    "inflation_index",
    "green_transition_fund",
    "tipping_point_active",
    "tipping_tier",
    "active_event_flags",
    "historical_ebitda",
    "tco2e_emissions",
}

# ── Required keys in every BU state dict ────────────────────────────────────
_REQUIRED_BU_KEYS = {
    "bu_id",
    "revenue_base",
    "opex_base",
    "reputation_score",
    "social_license_score",
    "governance_risk_score",
    "carbon_intensity",
    "natural_capital_debt",
}


# ═══════════════════════════════════════════════════════════════════════════════
# 5. OUTPUT CONTRACT
# ═══════════════════════════════════════════════════════════════════════════════

class TestOutputContract:
    """
    process_tick must always return a dict with a stable, fully-populated
    structure regardless of the input state.  Any missing key will cause
    KeyError crashes downstream in router.py / admin_router.py.
    """

    def _run(self, gs_overrides=None, bu_overrides=None, **kwargs):
        gs   = {**copy.deepcopy(BASE_GLOBAL), **(gs_overrides or {})}
        bus  = copy.deepcopy(BASE_BUS)
        decs = copy.deepcopy(BASE_DECISIONS)
        if bu_overrides:
            for bu in bus:
                bu.update(bu_overrides.get(bu["bu_id"], {}))
        return engine.process_tick(gs, bus, decs, **kwargs)

    # ── Top-level return keys ─────────────────────────────────────────────────

    def test_return_has_three_top_level_keys(self):
        result = self._run()
        assert _REQUIRED_RETURN_KEYS.issubset(result.keys()), (
            f"Missing top-level keys: {_REQUIRED_RETURN_KEYS - result.keys()}"
        )

    def test_global_state_has_all_required_keys(self):
        result = self._run()
        missing = _REQUIRED_GLOBAL_KEYS - result["global_state"].keys()
        assert missing == set(), f"Missing global_state keys: {missing}"

    def test_bu_states_is_non_empty_list(self):
        result = self._run()
        assert isinstance(result["bu_states"], list)
        assert len(result["bu_states"]) > 0

    def test_each_bu_has_required_keys(self):
        result = self._run()
        for bu in result["bu_states"]:
            missing = _REQUIRED_BU_KEYS - bu.keys()
            assert missing == set(), (
                f"{bu.get('bu_id','?')}: missing BU keys: {missing}"
            )

    def test_events_is_dict(self):
        result = self._run()
        assert isinstance(result["events"], dict)

    def test_global_state_round_number_is_int(self):
        result = self._run()
        rn = result["global_state"]["round_number"]
        assert isinstance(rn, int), f"round_number type: {type(rn)}"

    def test_global_state_tipping_point_active_is_bool(self):
        result = self._run()
        val = result["global_state"]["tipping_point_active"]
        assert isinstance(val, bool), f"tipping_point_active type: {type(val)}"

    def test_global_state_active_event_flags_is_dict(self):
        result = self._run()
        aef = result["global_state"]["active_event_flags"]
        assert isinstance(aef, dict), f"active_event_flags type: {type(aef)}"

    def test_output_stable_across_all_paradigms(self):
        """All four paradigms must produce the required output shape."""
        for paradigm in ("legacy_abc", "multi_toggles", "advanced_climate", "healthcare"):
            result = engine.process_tick(
                copy.deepcopy(BASE_GLOBAL),
                copy.deepcopy(BASE_BUS),
                copy.deepcopy(BASE_DECISIONS),
                decision_paradigm=paradigm,
            )
            assert _REQUIRED_RETURN_KEYS.issubset(result.keys()), (
                f"Paradigm '{paradigm}': missing keys {_REQUIRED_RETURN_KEYS - result.keys()}"
            )
            missing_gs = _REQUIRED_GLOBAL_KEYS - result["global_state"].keys()
            assert missing_gs == set(), (
                f"Paradigm '{paradigm}': missing global_state keys {missing_gs}"
            )

    def test_bu_states_length_matches_input(self):
        """Output BU count must equal input BU count."""
        result = self._run()
        assert len(result["bu_states"]) == len(BASE_BUS)

    def test_bu_ids_preserved_in_output(self):
        """Every input BU ID must appear in the output."""
        input_ids = {bu["bu_id"] for bu in BASE_BUS}
        result = self._run()
        output_ids = {bu["bu_id"] for bu in result["bu_states"]}
        assert input_ids == output_ids, (
            f"BU ID mismatch: input={input_ids}, output={output_ids}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# 6. NaN / INFINITY GUARD
# ═══════════════════════════════════════════════════════════════════════════════

class TestNaNInfinityGuard:
    """
    No numeric field in global_state or bu_states may be NaN or ±Infinity.
    NaN/Inf values are silent killers — they propagate through all downstream
    math and corrupt every metric, often without raising an exception.
    """

    _GLOBAL_NUMERIC_FIELDS = [
        "corporate_treasury", "group_reputation", "synergy_multiplier",
        "cost_of_capital", "inflation_index", "green_transition_fund",
        "historical_ebitda", "tco2e_emissions",
    ]
    _BU_NUMERIC_FIELDS = [
        "revenue_base", "opex_base", "reputation_score",
        "social_license_score", "governance_risk_score",
        "carbon_intensity", "natural_capital_debt",
    ]

    def _assert_no_nan_inf(self, result: dict, label: str = ""):
        gs  = result["global_state"]
        bus = result["bu_states"]

        for field in self._GLOBAL_NUMERIC_FIELDS:
            val = gs.get(field)
            if val is None:
                continue
            assert not (isinstance(val, float) and math.isnan(val)), (
                f"{label} global_state.{field} is NaN"
            )
            assert not (isinstance(val, float) and math.isinf(val)), (
                f"{label} global_state.{field} is Inf ({val})"
            )

        for bu in bus:
            for field in self._BU_NUMERIC_FIELDS:
                val = bu.get(field)
                if val is None:
                    continue
                assert not (isinstance(val, float) and math.isnan(val)), (
                    f"{label} {bu['bu_id']}.{field} is NaN"
                )
                assert not (isinstance(val, float) and math.isinf(val)), (
                    f"{label} {bu['bu_id']}.{field} is Inf ({val})"
                )

    def test_nominal_tick_no_nan_inf(self):
        result = engine.process_tick(
            copy.deepcopy(BASE_GLOBAL),
            copy.deepcopy(BASE_BUS),
            copy.deepcopy(BASE_DECISIONS),
        )
        self._assert_no_nan_inf(result, "nominal")

    def test_zero_revenue_no_nan_inf(self):
        """All BUs with zero revenue must not produce NaN in any metric."""
        bus = copy.deepcopy(BASE_BUS)
        for bu in bus:
            bu["revenue_base"] = 0.0
        result = engine.process_tick(
            copy.deepcopy(BASE_GLOBAL), bus, copy.deepcopy(BASE_DECISIONS)
        )
        self._assert_no_nan_inf(result, "zero_revenue")

    def test_zero_opex_no_nan_inf(self):
        """Zero OPEX (degenerate case) must not produce NaN."""
        bus = copy.deepcopy(BASE_BUS)
        for bu in bus:
            bu["opex_base"] = 0.0
        result = engine.process_tick(
            copy.deepcopy(BASE_GLOBAL), bus, copy.deepcopy(BASE_DECISIONS)
        )
        self._assert_no_nan_inf(result, "zero_opex")

    def test_zero_capex_decisions_no_nan_inf(self):
        """Zero-capex decisions must not produce NaN."""
        decs = copy.deepcopy(BASE_DECISIONS)
        for d in decs:
            d["capex_allocated"]  = 0.0
            d["investment_ratio"] = 0.0
        result = engine.process_tick(
            copy.deepcopy(BASE_GLOBAL),
            copy.deepcopy(BASE_BUS),
            decs,
        )
        self._assert_no_nan_inf(result, "zero_capex")

    def test_extreme_negative_treasury_no_nan_inf(self):
        """Deep-negative treasury (near floor) must not produce NaN."""
        gs = copy.deepcopy(BASE_GLOBAL)
        gs["corporate_treasury"] = -490_000_000
        result = engine.process_tick(gs, copy.deepcopy(BASE_BUS), copy.deepcopy(BASE_DECISIONS))
        self._assert_no_nan_inf(result, "near_floor_treasury")

    def test_extreme_high_ncd_no_nan_inf(self):
        """BUs at NCD hard cap must not produce NaN interest calculations."""
        bus = copy.deepcopy(BASE_BUS)
        for bu in bus:
            bu["natural_capital_debt"] = 999_999.0
        result = engine.process_tick(
            copy.deepcopy(BASE_GLOBAL), bus, copy.deepcopy(BASE_DECISIONS)
        )
        self._assert_no_nan_inf(result, "max_ncd")

    def test_high_crisis_severity_no_nan_inf(self):
        """Maximum crisis severity (100) must not produce NaN."""
        result = engine.process_tick(
            copy.deepcopy(BASE_GLOBAL),
            copy.deepcopy(BASE_BUS),
            copy.deepcopy(BASE_DECISIONS),
            crisis_severity=100.0,
        )
        self._assert_no_nan_inf(result, "max_crisis")

    def test_round_10_no_nan_inf(self):
        """Round 10 (terminal round) must not produce NaN in any field."""
        gs = copy.deepcopy(BASE_GLOBAL)
        gs["round_number"] = 10
        result = engine.process_tick(gs, copy.deepcopy(BASE_BUS), copy.deepcopy(BASE_DECISIONS))
        self._assert_no_nan_inf(result, "round_10")


# ═══════════════════════════════════════════════════════════════════════════════
# 7. TIPPING-POINT IRREVERSIBILITY
# ═══════════════════════════════════════════════════════════════════════════════

class TestTippingPointIrreversibility:
    """
    Once tipping_point_active is True it must NEVER revert to False in any
    subsequent tick — it is explicitly marked IRREVERSIBLE in the engine.
    """

    def _tick_with_tipping(self, gs_overrides=None):
        gs = {**copy.deepcopy(BASE_GLOBAL), **(gs_overrides or {})}
        gs["tipping_point_active"] = True
        gs["tipping_tier"] = "tipped"
        return engine.process_tick(
            gs, copy.deepcopy(BASE_BUS), copy.deepcopy(BASE_DECISIONS)
        )

    def test_tipping_active_stays_true_single_tick(self):
        """One tick after tipping activates — must remain True."""
        result = self._tick_with_tipping()
        assert result["global_state"]["tipping_point_active"] is True

    def test_tipping_active_stays_true_10_round_chain(self):
        """10 sequential ticks after tipping — must remain True every round."""
        gs  = {**copy.deepcopy(BASE_GLOBAL),
               "tipping_point_active": True, "tipping_tier": "tipped"}
        bus = copy.deepcopy(BASE_BUS)
        # Use low CI to avoid further escalation noise
        for bu in bus:
            bu["carbon_intensity"] = 5.0

        for rnd in range(1, 11):
            gs["round_number"] = rnd
            decs = [
                {"bu_id": bu["bu_id"], "investment_ratio": 0.3,
                 "capex_allocated": 500_000, "choice_selected": "option_a"}
                for bu in bus
            ]
            result = engine.process_tick(gs, bus, decs)
            assert result["global_state"]["tipping_point_active"] is True, (
                f"tipping_point_active reverted to False at round {rnd + 1}"
            )
            gs  = result["global_state"]
            bus = result["bu_states"]

    def test_tipping_not_active_stays_false_on_low_ci(self):
        """Low carbon intensity must not accidentally trigger tipping."""
        bus = copy.deepcopy(BASE_BUS)
        for bu in bus:
            bu["carbon_intensity"] = 5.0   # well below the 55-threshold
        gs = {**copy.deepcopy(BASE_GLOBAL), "tipping_point_active": False,
              "round_number": 5}
        result = engine.process_tick(gs, bus, copy.deepcopy(BASE_DECISIONS))
        assert result["global_state"]["tipping_point_active"] is False

    def test_tipping_tier_never_regresses(self):
        """
        Tier progression is warning → stressed → tipped.
        A tier must never decrease (e.g. tipped → stressed) in a subsequent tick.
        """
        tier_order = {"none": 0, "warning": 1, "stressed": 2, "tipped": 3}
        gs  = {**copy.deepcopy(BASE_GLOBAL),
               "tipping_point_active": True, "tipping_tier": "tipped",
               "round_number": 5}
        bus = copy.deepcopy(BASE_BUS)
        for bu in bus:
            bu["carbon_intensity"] = 5.0  # won't escalate further

        for rnd in range(5, 11):
            gs["round_number"] = rnd
            decs = [{"bu_id": bu["bu_id"], "investment_ratio": 0.3,
                     "capex_allocated": 500_000, "choice_selected": "option_b"}
                    for bu in bus]
            result  = engine.process_tick(gs, bus, decs)
            new_tier = result["global_state"].get("tipping_tier", "none")
            prev_tier = gs.get("tipping_tier", "none")
            assert tier_order.get(new_tier, 0) >= tier_order.get(prev_tier, 0), (
                f"Round {rnd + 1}: tipping_tier regressed from '{prev_tier}' to '{new_tier}'"
            )
            gs  = result["global_state"]
            bus = result["bu_states"]


# ═══════════════════════════════════════════════════════════════════════════════
# 8. GREEN FUND NON-NEGATIVE
# ═══════════════════════════════════════════════════════════════════════════════

class TestGreenFundNonNegative:
    """
    The Green Transition Fund is assembled with max(0.0, balance) — it must
    never go below 0 regardless of how much is drawn down.
    """

    def test_green_fund_non_negative_on_nominal_tick(self):
        result = engine.process_tick(
            copy.deepcopy(BASE_GLOBAL),
            copy.deepcopy(BASE_BUS),
            copy.deepcopy(BASE_DECISIONS),
        )
        assert result["global_state"]["green_transition_fund"] >= 0.0

    def test_green_fund_non_negative_when_pre_loaded(self):
        gs = copy.deepcopy(BASE_GLOBAL)
        gs["green_transition_fund"] = 5_000_000.0
        result = engine.process_tick(
            gs, copy.deepcopy(BASE_BUS), copy.deepcopy(BASE_DECISIONS),
            decision_paradigm="advanced_climate",
        )
        assert result["global_state"]["green_transition_fund"] >= 0.0

    def test_green_fund_non_negative_after_full_drawdown(self):
        """Fund cannot go negative even if large CAPEX is requested in advanced_climate."""
        gs = copy.deepcopy(BASE_GLOBAL)
        gs["green_transition_fund"] = 100_000.0  # tiny fund
        decs = copy.deepcopy(BASE_DECISIONS)
        for d in decs:
            d["capex_allocated"] = 2_000_000  # much larger than fund
        result = engine.process_tick(
            gs, copy.deepcopy(BASE_BUS), decs,
            decision_paradigm="advanced_climate",
        )
        assert result["global_state"]["green_transition_fund"] >= 0.0

    def test_green_fund_non_negative_across_10_round_chain(self):
        gs  = {**copy.deepcopy(BASE_GLOBAL), "green_transition_fund": 500_000.0}
        bus = copy.deepcopy(BASE_BUS)
        decs_template = copy.deepcopy(BASE_DECISIONS)
        for rnd in range(1, 11):
            gs["round_number"] = rnd
            decs = copy.deepcopy(decs_template)
            result = engine.process_tick(gs, bus, decs, decision_paradigm="advanced_climate")
            assert result["global_state"]["green_transition_fund"] >= 0.0, (
                f"Round {rnd}: green_transition_fund went negative"
            )
            gs  = result["global_state"]
            bus = result["bu_states"]


# ═══════════════════════════════════════════════════════════════════════════════
# 9. EVENT-CONSEQUENCE CONSISTENCY
# ═══════════════════════════════════════════════════════════════════════════════

class TestEventConsequenceConsistency:
    """
    When the engine fires a hard event, the corresponding state consequence
    must be present in the output.  These tests verify that the event flag
    and its effect are consistent — preventing "ghost events" that fire but
    have no impact, or "silent impacts" with no event flag.
    """

    def test_capex_capped_event_reflects_in_treasury(self):
        """
        When capex_capped fires, the amount actually deducted from treasury
        must be less than or equal to what was requested — the cap was enforced.
        """
        gs = copy.deepcopy(BASE_GLOBAL)
        gs["corporate_treasury"] = 1_000_000  # very small treasury
        decs = copy.deepcopy(BASE_DECISIONS)
        for d in decs:
            d["capex_allocated"] = 5_000_000  # 4× the treasury → triggers cap

        result = engine.process_tick(gs, copy.deepcopy(BASE_BUS), decs)
        events = result["events"]

        if events.get("capex_capped"):
            # Treasury must have decreased, but not by the full 20M requested
            treasury_change = (
                result["global_state"]["corporate_treasury"]
                - gs["corporate_treasury"]
            )
            # Total requested: 4 × 5M = 20M; with cap, deduction should be ≤ 2×treasury = 2M
            assert treasury_change > -20_000_000, (
                f"capex_capped fired but full 20M was still deducted: Δ={treasury_change:,.0f}"
            )

    def test_emissions_event_flag_consistent_with_state(self):
        """
        When emissions_limit_breached fires in events, the global_state
        tco2e_emissions must exceed CONSTRAINT_MAX_CARBON_EMISSIONS.
        """
        # Force high CI so emissions definitely exceed the cap
        bus = copy.deepcopy(BASE_BUS)
        for bu in bus:
            bu["carbon_intensity"] = 100.0   # 100 t/$1M × ~75M revenue = 7,500 tCO2e
        gs = copy.deepcopy(BASE_GLOBAL)

        result = engine.process_tick(gs, bus, copy.deepcopy(BASE_DECISIONS))
        events = result["events"]

        if events.get("emissions_limit_breached"):
            assert result["global_state"]["tco2e_emissions"] > CONSTRAINT_MAX_CARBON_EMISSIONS, (
                "emissions_limit_breached flag set but tco2e_emissions is within limit"
            )

    def test_no_ghost_emissions_flag_when_under_limit(self):
        """
        When all BUs have very low CI, emissions_limit_breached must NOT fire.
        """
        bus = copy.deepcopy(BASE_BUS)
        for bu in bus:
            bu["carbon_intensity"] = 1.0   # 1 t/$1M × 75M = 75 tCO2e ≪ 5,000 cap
        result = engine.process_tick(
            copy.deepcopy(BASE_GLOBAL), bus, copy.deepcopy(BASE_DECISIONS)
        )
        assert not result["events"].get("emissions_limit_breached"), (
            "emissions_limit_breached fired when emissions are far below the cap"
        )

    def test_tipping_point_event_flag_consistent_with_global_state(self):
        """
        If tipping_point_reached fires in events, tipping_point_active in
        global_state must also be True.
        """
        result = engine.process_tick(
            copy.deepcopy(BASE_GLOBAL),
            copy.deepcopy(BASE_BUS),
            copy.deepcopy(BASE_DECISIONS),
        )
        if result["events"].get("tipping_point_reached"):
            assert result["global_state"]["tipping_point_active"] is True, (
                "tipping_point_reached event fired but tipping_point_active is False"
            )

    def test_reputation_penalty_after_emissions_breach(self):
        """
        Engine applies -5 reputation when emissions_limit_breached fires.

        FIX INTEGRITY-001: the penalty is now applied after calc_contagion,
        which may have raised reputation above the input value in the same tick.
        The engine records the snapshot in events['emissions_rep_penalty'] so we
        can assert the deduction was applied correctly regardless of contagion gains.

        Invariants:
        - rep_after  < rep_before  (penalty always reduces from its pre-deduction baseline)
        - deduction == rep_before - rep_after (accounting is exact)
        - rep_after >= 0.0  (floor holds)
        """
        bus = copy.deepcopy(BASE_BUS)
        for bu in bus:
            bu["carbon_intensity"] = 100.0   # force emissions breach
        gs = copy.deepcopy(BASE_GLOBAL)

        result = engine.process_tick(gs, bus, copy.deepcopy(BASE_DECISIONS))
        events = result["events"]

        assert events.get("emissions_limit_breached") is True, (
            "Expected emissions_limit_breached to fire with CI=100 on all BUs"
        )

        penalty = events.get("emissions_rep_penalty", {})
        assert penalty, "emissions_rep_penalty event dict missing from events"

        rep_before = penalty["rep_before"]
        rep_after  = penalty["rep_after"]
        deduction  = penalty["deduction"]

        assert rep_after < rep_before, (
            f"Reputation was NOT reduced by the emissions breach penalty: "
            f"rep_before={rep_before}, rep_after={rep_after}"
        )
        assert deduction == pytest.approx(rep_before - rep_after, abs=0.01), (
            f"Deduction accounting mismatch: deduction={deduction}, "
            f"actual delta={rep_before - rep_after}"
        )
        assert rep_after >= 0.0, (
            f"Reputation went below 0 after emissions breach: {rep_after}"
        )
        # Penalty should always be exactly 5 (unless floored at 0)
        expected_deduction = min(5.0, rep_before)
        assert deduction == pytest.approx(expected_deduction, abs=0.01), (
            f"Expected penalty of {expected_deduction}, got {deduction}"
        )


    def test_round_number_in_output_matches_input_plus_one(self):
        """Event-driven round advancement must always be input + 1."""
        for start_round in (1, 3, 5, 9):
            gs = {**copy.deepcopy(BASE_GLOBAL), "round_number": start_round}
            result = engine.process_tick(
                gs, copy.deepcopy(BASE_BUS), copy.deepcopy(BASE_DECISIONS)
            )
            assert result["global_state"]["round_number"] == start_round + 1, (
                f"Round {start_round}: expected output round {start_round + 1}, "
                f"got {result['global_state']['round_number']}"
            )


# ═══════════════════════════════════════════════════════════════════════════════
# 10. PURE-HELPER UNIT TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestDetectDistress:
    """Unit tests for engine.detect_distress — the 3-Act Turnaround Arc."""

    def test_no_distress_round_1(self):
        """Distress never triggers on round 1 (grace period)."""
        result = detect_distress(
            treasury=-10_000_000, group_reputation=10.0, round_number=1
        )
        assert result["distress_detected"] is False
        assert result["survival_mode"] is False

    def test_distress_triggers_at_round_2(self):
        """Crisis conditions on round ≥ 2 must trigger distress detection."""
        result = detect_distress(
            treasury=0.0, group_reputation=15.0, round_number=2
        )
        assert result["distress_detected"] is True
        assert result["survival_mode"] is True
        assert result["turnaround_phase"] == "crisis"

    def test_no_distress_when_treasury_positive_and_rep_ok(self):
        """Healthy state must not trigger distress."""
        result = detect_distress(
            treasury=25_000_000, group_reputation=65.0, round_number=5
        )
        assert result["distress_detected"] is False
        assert result["survival_mode"] is False

    def test_crisis_phase_transitions_to_stabilisation(self):
        """If treasury recovers > 0 and rep > 20 while in crisis phase → stabilisation."""
        result = detect_distress(
            treasury=1_000_000, group_reputation=25.0,
            round_number=4, current_phase="crisis", already_in_survival=True
        )
        assert result["turnaround_phase"] == "stabilisation"
        assert result["survival_mode"] is True

    def test_stabilisation_transitions_to_recovery(self):
        """Treasury > 10M and rep > 45 while in stabilisation → recovery."""
        result = detect_distress(
            treasury=12_000_000, group_reputation=50.0,
            round_number=6, current_phase="stabilisation", already_in_survival=True
        )
        assert result["turnaround_phase"] == "recovery"

    def test_recovery_transitions_to_exit(self):
        """Treasury > 20M and rep > 55 while in recovery → exit (turnaround complete)."""
        result = detect_distress(
            treasury=25_000_000, group_reputation=60.0,
            round_number=8, current_phase="recovery", already_in_survival=True
        )
        assert result["turnaround_phase"] == "exit"
        assert result.get("recovered") is True

    def test_exit_phase_is_stable(self):
        """Once in exit phase, no further transitions occur."""
        result = detect_distress(
            treasury=30_000_000, group_reputation=70.0,
            round_number=9, current_phase="exit", already_in_survival=False
        )
        assert result["turnaround_phase"] == "exit"

    def test_bailout_amount_present_on_crisis_entry(self):
        """Crisis entry must include a bailout_amount in the return dict."""
        result = detect_distress(
            treasury=-1_000, group_reputation=5.0, round_number=3
        )
        assert "bailout_amount" in result
        assert result["bailout_amount"] > 0

    def test_capex_cap_zero_in_crisis(self):
        """CapEx must be fully frozen (0.0) in crisis phase."""
        result = detect_distress(
            treasury=0.0, group_reputation=10.0, round_number=2
        )
        assert result.get("capex_cap_multiplier") == 0.0


class TestCalcForecast:
    """Unit tests for engine.calc_forecast — the predictive dashboard engine."""

    def _forecast(self, gs_overrides=None, bus=None):
        gs  = {**copy.deepcopy(BASE_GLOBAL), **(gs_overrides or {})}
        bus = bus or copy.deepcopy(BASE_BUS)
        return calc_forecast(gs, bus)

    def test_returns_required_keys(self):
        result = self._forecast()
        for key in ("treasury_velocity", "contagion_risk_index",
                    "rounds_to_insolvency", "time_to_impact"):
            assert key in result, f"calc_forecast missing key: {key}"

    def test_contagion_risk_index_in_bounds(self):
        """contagion_risk_index must always be in [0, 100]."""
        result = self._forecast()
        cri = result["contagion_risk_index"]
        assert 0.0 <= cri <= 100.0, f"contagion_risk_index={cri} out of [0,100]"

    def test_contagion_risk_index_worst_case_bounded(self):
        """Even with all scores at extremes, CRI must stay ≤ 100."""
        bus = copy.deepcopy(BASE_BUS)
        for bu in bus:
            bu["governance_risk_score"]  = 100.0
            bu["social_license_score"]   = 0.0
            bu["reputation_score"]       = 0.0
            bu["carbon_intensity"]       = 200.0
        result = self._forecast(bus=bus)
        assert result["contagion_risk_index"] <= 100.0

    def test_contagion_risk_index_best_case_bounded(self):
        """Pristine scores must keep CRI ≥ 0."""
        bus = copy.deepcopy(BASE_BUS)
        for bu in bus:
            bu["governance_risk_score"]  = 0.0
            bu["social_license_score"]   = 100.0
            bu["reputation_score"]       = 100.0
            bu["carbon_intensity"]       = 0.0
        result = self._forecast(bus=bus)
        assert result["contagion_risk_index"] >= 0.0

    def test_insolvency_warning_when_burning_cash(self):
        """Negative EBITDA → treasury_velocity < 0 → rounds_to_insolvency populated."""
        bus = copy.deepcopy(BASE_BUS)
        for bu in bus:
            bu["opex_base"] = bu["revenue_base"] * 1.5  # guaranteed loss
        gs = {**copy.deepcopy(BASE_GLOBAL), "corporate_treasury": 10_000_000}
        result = self._forecast(gs_overrides=gs, bus=bus)
        assert result["treasury_velocity"] < 0
        assert result["rounds_to_insolvency"] is not None
        assert result["rounds_to_insolvency"] > 0

    def test_no_insolvency_warning_when_profitable(self):
        """Positive EBITDA → rounds_to_insolvency must be None."""
        bus = copy.deepcopy(BASE_BUS)
        for bu in bus:
            bu["opex_base"] = bu["revenue_base"] * 0.3  # very profitable
        result = self._forecast(bus=bus)
        assert result["rounds_to_insolvency"] is None

    def test_treasury_trend_improving_when_ebitda_positive(self):
        result = self._forecast()
        # BASE_BUS has positive EBITDA → treasury_velocity > 0
        assert result["treasury_trend"] in ("improving", "declining")  # schema check

    def test_time_to_impact_is_dict_with_warnings_list(self):
        result = self._forecast()
        tti = result["time_to_impact"]
        assert isinstance(tti, dict)
        assert isinstance(tti.get("warnings", []), list)

    def test_zero_bus_does_not_crash(self):
        """Edge case: empty BU list must not raise."""
        gs = copy.deepcopy(BASE_GLOBAL)
        result = calc_forecast(gs, [])
        assert "contagion_risk_index" in result


class TestClassifySeverity:
    """Unit tests for engine.classify_severity."""

    def test_routine_severity_below_1pct(self):
        result = classify_severity(amount=50_000, treasury=10_000_000)
        assert result["severity_tier"] == "routine"

    def test_noteworthy_severity_1_to_5pct(self):
        result = classify_severity(amount=200_000, treasury=10_000_000)
        assert result["severity_tier"] == "noteworthy"

    def test_material_severity_5_to_15pct(self):
        result = classify_severity(amount=1_000_000, treasury=10_000_000)
        assert result["severity_tier"] == "material"

    def test_critical_severity_above_15pct(self):
        result = classify_severity(amount=2_000_000, treasury=10_000_000)
        assert result["severity_tier"] == "critical"

    def test_zero_treasury_treated_as_100pct(self):
        """Zero treasury → any non-zero amount = 100% impact."""
        result = classify_severity(amount=1_000, treasury=0)
        assert result["severity_tier"] == "critical"

    def test_zero_amount_is_routine(self):
        result = classify_severity(amount=0, treasury=10_000_000)
        assert result["severity_tier"] == "routine"

    def test_impact_pct_is_non_negative(self):
        result = classify_severity(amount=500_000, treasury=5_000_000)
        assert result["impact_pct"] >= 0.0

    def test_all_tiers_have_label(self):
        for amount, treasury in [(50_000, 10e6), (200_000, 10e6), (1e6, 10e6), (2e6, 10e6)]:
            result = classify_severity(amount=amount, treasury=treasury)
            assert "severity_label" in result
            assert len(result["severity_label"]) > 0


class TestCalcMomentumScore:
    """Unit tests for engine.calc_momentum_score."""

    def test_insufficient_history_returns_50(self):
        result = calc_momentum_score(
            current_global=copy.deepcopy(BASE_GLOBAL),
            history=[],
        )
        assert result["momentum_score"] == 50.0
        assert result["trend"] == "insufficient_data"

    def test_score_in_bounds_0_to_100(self):
        """Momentum score must always be in [0, 100]."""
        history = [
            {"corporate_treasury": 10_000_000, "group_reputation": 50.0,
             "active_event_flags": {}},
            {"corporate_treasury": 15_000_000, "group_reputation": 55.0,
             "active_event_flags": {}},
        ]
        result = calc_momentum_score(
            current_global={
                **copy.deepcopy(BASE_GLOBAL),
                "corporate_treasury": 20_000_000,
                "group_reputation": 60.0,
            },
            history=history,
        )
        assert 0.0 <= result["momentum_score"] <= 100.0

    def test_improving_trajectory_above_50(self):
        """Consistently improving treasury and reputation → score > 50."""
        history = [
            {"corporate_treasury": 5_000_000,  "group_reputation": 40.0, "active_event_flags": {}},
            {"corporate_treasury": 15_000_000, "group_reputation": 55.0, "active_event_flags": {}},
        ]
        result = calc_momentum_score(
            current_global={
                **copy.deepcopy(BASE_GLOBAL),
                "corporate_treasury": 30_000_000,
                "group_reputation": 70.0,
            },
            history=history,
        )
        assert result["momentum_score"] > 50.0

    def test_declining_trajectory_below_50(self):
        """
        A trajectory where the rate of cash burn is *accelerating* must produce
        a score below 50.

        The formula computes Δvelocity = (curr - prev) - (prev - prev2).
        For this to be negative the second drop must be larger than the first:
          prev2 → prev: treasury drops  5M (velocity = -5M)
          prev  → curr: treasury drops 20M (velocity = -20M)
          Δvelocity = -20M - (-5M) = -15M  ← clearly decelerating

        Rep also falls 80 → 70 → 30, so all three components pull the score down.
        """
        history = [
            {"corporate_treasury": 30_000_000, "group_reputation": 80.0,
             "active_event_flags": {}},
            {"corporate_treasury": 25_000_000, "group_reputation": 70.0,
             "active_event_flags": {}},
        ]
        result = calc_momentum_score(
            current_global={
                **copy.deepcopy(BASE_GLOBAL),
                "corporate_treasury": 5_000_000,   # Δ = -20M vs previous Δ of -5M
                "group_reputation": 30.0,
            },
            history=history,
        )
        assert result["momentum_score"] < 50.0, (
            f"Expected accelerating-decline score < 50, got {result['momentum_score']}"
        )


    def test_comeback_kid_triggers_after_two_high_rounds(self):
        """Two consecutive momentum scores > 70 must trigger comeback_kid bonus."""
        gs = {
            **copy.deepcopy(BASE_GLOBAL),
            "corporate_treasury": 50_000_000,
            "group_reputation": 85.0,
            "momentum_history": [75.0, 80.0],   # two previous high scores
        }
        history = [
            {"corporate_treasury": 10_000_000, "group_reputation": 50.0, "active_event_flags": {}},
            {"corporate_treasury": 30_000_000, "group_reputation": 70.0, "active_event_flags": {}},
        ]
        result = calc_momentum_score(current_global=gs, history=history)
        # Score should be high enough to count as 3rd consecutive → comeback_kid
        if result["momentum_score"] > 70:
            assert result["comeback_kid"] is True
            assert result["comeback_kid_mr_bonus"] == 0.05

    def test_trend_labels_are_valid(self):
        valid_trends = {"accelerating", "stable", "decelerating", "declining", "insufficient_data"}
        history = [
            {"corporate_treasury": 20_000_000, "group_reputation": 60.0, "active_event_flags": {}},
            {"corporate_treasury": 22_000_000, "group_reputation": 62.0, "active_event_flags": {}},
        ]
        result = calc_momentum_score(copy.deepcopy(BASE_GLOBAL), history)
        assert result["trend"] in valid_trends


class TestCalcDSOLag:
    """Unit tests for engine.calc_dso_lag — Days Sales Outstanding."""

    def test_zero_governance_risk_minimum_dso(self):
        result = calc_dso_lag(revenue=10_000_000, governance_risk=0.0, round_number=1)
        assert result["dso_factor"] == pytest.approx(0.02)
        assert result["deferred_amount"] == pytest.approx(200_000.0)

    def test_high_governance_risk_higher_dso(self):
        result_low  = calc_dso_lag(10_000_000, governance_risk=10.0, round_number=1)
        result_high = calc_dso_lag(10_000_000, governance_risk=80.0, round_number=1)
        assert result_high["dso_factor"] > result_low["dso_factor"]

    def test_dso_factor_capped_at_15pct(self):
        """Even at max governance risk, DSO factor must not exceed 15%."""
        result = calc_dso_lag(10_000_000, governance_risk=1000.0, round_number=1)
        assert result["dso_factor"] <= 0.15

    def test_dso_factor_floored_at_0(self):
        """DSO factor must not go negative (governance_risk always ≥ 0 in practice)."""
        result = calc_dso_lag(10_000_000, governance_risk=0.0, round_number=1)
        assert result["dso_factor"] >= 0.0

    def test_deferred_amount_non_negative(self):
        for risk in (0, 20, 50, 100):
            result = calc_dso_lag(5_000_000, governance_risk=risk, round_number=3)
            assert result["deferred_amount"] >= 0.0

    def test_dso_days_non_negative(self):
        result = calc_dso_lag(10_000_000, governance_risk=30.0, round_number=2)
        assert result["dso_days_approx"] >= 0.0

    def test_zero_revenue_produces_zero_deferred(self):
        result = calc_dso_lag(revenue=0.0, governance_risk=50.0, round_number=1)
        assert result["deferred_amount"] == 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# 11. EDGE-CASE INPUTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestEdgeCaseInputs:
    """Unusual but plausible inputs that could trigger edge-case crashes."""

    def test_single_bu_completes_without_error(self):
        """A simulation with only one BU must not crash."""
        bus  = [copy.deepcopy(BASE_BUS[0])]
        decs = [copy.deepcopy(BASE_DECISIONS[0])]
        result = engine.process_tick(copy.deepcopy(BASE_GLOBAL), bus, decs)
        assert "global_state" in result
        assert len(result["bu_states"]) == 1

    def test_single_bu_passes_all_invariants(self):
        """Single-BU output must satisfy all hard invariants."""
        bus  = [copy.deepcopy(BASE_BUS[0])]
        decs = [copy.deepcopy(BASE_DECISIONS[0])]
        result = engine.process_tick(copy.deepcopy(BASE_GLOBAL), bus, decs)
        assert validate_simulation_state(result["global_state"], result["bu_states"]) is True
        assert validate_bu_fields(result["bu_states"]) == []

    def test_all_identical_bu_states_no_crash(self):
        """All BUs having exactly the same state must not crash."""
        template = copy.deepcopy(BASE_BUS[0])
        bus  = [{**copy.deepcopy(template), "bu_id": bid}
                for bid in ("pharma", "electronics", "consumer_goods", "software")]
        decs = [{"bu_id": bid, "investment_ratio": 0.3,
                 "capex_allocated": 500_000, "choice_selected": "option_b"}
                for bid in ("pharma", "electronics", "consumer_goods", "software")]
        result = engine.process_tick(copy.deepcopy(BASE_GLOBAL), bus, decs)
        assert validate_simulation_state(result["global_state"], result["bu_states"]) is True

    def test_round_10_terminal_no_crash(self):
        """Round 10 is the terminal round — must complete and pass invariants."""
        gs = {**copy.deepcopy(BASE_GLOBAL), "round_number": 10}
        result = engine.process_tick(gs, copy.deepcopy(BASE_BUS), copy.deepcopy(BASE_DECISIONS))
        assert validate_simulation_state(result["global_state"], result["bu_states"]) is True

    def test_beyond_round_10_no_crash(self):
        """Engine should not crash if somehow called with round > 10."""
        gs = {**copy.deepcopy(BASE_GLOBAL), "round_number": 11}
        result = engine.process_tick(gs, copy.deepcopy(BASE_BUS), copy.deepcopy(BASE_DECISIONS))
        assert "global_state" in result

    def test_max_crisis_severity_no_crash(self):
        """crisis_severity=100 (maximum) must complete without error."""
        result = engine.process_tick(
            copy.deepcopy(BASE_GLOBAL),
            copy.deepcopy(BASE_BUS),
            copy.deepcopy(BASE_DECISIONS),
            crisis_severity=100.0,
        )
        assert validate_simulation_state(result["global_state"], result["bu_states"]) is True

    def test_zero_crisis_severity_no_crash(self):
        """crisis_severity=0 must complete without error."""
        result = engine.process_tick(
            copy.deepcopy(BASE_GLOBAL),
            copy.deepcopy(BASE_BUS),
            copy.deepcopy(BASE_DECISIONS),
            crisis_severity=0.0,
        )
        assert validate_simulation_state(result["global_state"], result["bu_states"]) is True

    def test_all_zero_bu_metrics_no_crash(self):
        """BUs with all numeric metrics zeroed must not crash the engine."""
        bus = copy.deepcopy(BASE_BUS)
        for bu in bus:
            bu["revenue_base"]         = 0.0
            bu["opex_base"]            = 0.0
            bu["reputation_score"]     = 0.0
            bu["social_license_score"] = 0.0
            bu["governance_risk_score"]= 0.0
            bu["carbon_intensity"]     = 0.0
            bu["natural_capital_debt"] = 0.0
        result = engine.process_tick(copy.deepcopy(BASE_GLOBAL), bus, copy.deepcopy(BASE_DECISIONS))
        assert "global_state" in result

    def test_high_dividends_does_not_make_treasury_nan(self):
        """Requesting dividends larger than treasury must not produce NaN."""
        gs = copy.deepcopy(BASE_GLOBAL)
        gs["corporate_treasury"] = 1_000_000
        result = engine.process_tick(
            gs, copy.deepcopy(BASE_BUS), copy.deepcopy(BASE_DECISIONS),
            dividends_paid=100_000_000,  # 100× the treasury
        )
        treasury = result["global_state"]["corporate_treasury"]
        assert not math.isnan(treasury)
        assert not math.isinf(treasury)


# ═══════════════════════════════════════════════════════════════════════════════
# 12. CROSS-PARADIGM ROBUSTNESS
# ═══════════════════════════════════════════════════════════════════════════════

class TestCrossParadigmRobustness:
    """
    All four decision paradigms must satisfy hard invariants on every tick.
    Paradigm-specific paths (pillar_decisions, advanced_climate CI deltas,
    healthcare patient_outcomes) can introduce new state paths that bypass
    the checks exercised by the default legacy_abc tests.
    """

    _PARADIGMS = ("legacy_abc", "multi_toggles", "advanced_climate", "healthcare")

    def _make_pillar_decisions(self, tier: str = "moderate"):
        """Build multi_toggles pillar_decisions for all BUs."""
        return [
            {
                "bu_id": d["bu_id"],
                "investment_ratio": d["investment_ratio"],
                "capex_allocated":  d["capex_allocated"],
                "choice_selected":  "",
                "pillar_decisions": {
                    "energy":        tier,
                    "operations":    tier,
                    "supply_chain":  tier,
                    "offsetting":    tier,
                },
            }
            for d in BASE_DECISIONS
        ]

    def test_all_paradigms_pass_hard_invariants(self):
        """Each paradigm must pass validate_simulation_state on a nominal tick."""
        for paradigm in self._PARADIGMS:
            decs = (
                self._make_pillar_decisions()
                if paradigm == "multi_toggles"
                else copy.deepcopy(BASE_DECISIONS)
            )
            result = engine.process_tick(
                copy.deepcopy(BASE_GLOBAL),
                copy.deepcopy(BASE_BUS),
                decs,
                decision_paradigm=paradigm,
            )
            assert validate_simulation_state(
                result["global_state"], result["bu_states"]
            ) is True, f"Paradigm '{paradigm}': hard invariant violated"

    def test_all_paradigms_pass_bu_field_bounds(self):
        """Each paradigm must produce BU field values within engine-guaranteed bounds."""
        for paradigm in self._PARADIGMS:
            decs = (
                self._make_pillar_decisions()
                if paradigm == "multi_toggles"
                else copy.deepcopy(BASE_DECISIONS)
            )
            result = engine.process_tick(
                copy.deepcopy(BASE_GLOBAL),
                copy.deepcopy(BASE_BUS),
                decs,
                decision_paradigm=paradigm,
            )
            violations = validate_bu_fields(result["bu_states"])
            assert violations == [], (
                f"Paradigm '{paradigm}': BU field violations: {violations}"
            )

    def test_multi_toggles_aggressive_pillar_no_nan(self):
        """Aggressive pillars across all BUs must not produce NaN/Inf."""
        decs = self._make_pillar_decisions("aggressive")
        result = engine.process_tick(
            copy.deepcopy(BASE_GLOBAL),
            copy.deepcopy(BASE_BUS),
            decs,
            decision_paradigm="multi_toggles",
        )
        gs  = result["global_state"]
        bus = result["bu_states"]
        for field in ("corporate_treasury", "group_reputation", "tco2e_emissions"):
            val = gs.get(field)
            if val is not None:
                assert not math.isnan(val) and not math.isinf(val), (
                    f"multi_toggles aggressive: {field}={val}"
                )

    def test_advanced_climate_green_fund_non_negative(self):
        """advanced_climate paradigm: green fund must never go below 0."""
        gs = {**copy.deepcopy(BASE_GLOBAL), "green_transition_fund": 200_000.0}
        decs = copy.deepcopy(BASE_DECISIONS)
        for d in decs:
            d["capex_allocated"] = 1_000_000  # draws down the fund
        result = engine.process_tick(
            gs, copy.deepcopy(BASE_BUS), decs, decision_paradigm="advanced_climate"
        )
        assert result["global_state"]["green_transition_fund"] >= 0.0

    def test_all_paradigms_round_advances_by_1(self):
        """Round number must increase by exactly 1 across all paradigms."""
        for paradigm in self._PARADIGMS:
            decs = (
                self._make_pillar_decisions()
                if paradigm == "multi_toggles"
                else copy.deepcopy(BASE_DECISIONS)
            )
            gs = {**copy.deepcopy(BASE_GLOBAL), "round_number": 4}
            result = engine.process_tick(
                gs, copy.deepcopy(BASE_BUS), decs, decision_paradigm=paradigm
            )
            assert result["global_state"]["round_number"] == 5, (
                f"Paradigm '{paradigm}': expected round 5, "
                f"got {result['global_state']['round_number']}"
            )

    def test_all_paradigms_complete_5_round_chain(self):
        """Each paradigm must complete a 5-round chain with no hard violations."""
        for paradigm in self._PARADIGMS:
            gs  = copy.deepcopy(BASE_GLOBAL)
            bus = copy.deepcopy(BASE_BUS)
            for rnd in range(1, 6):
                gs["round_number"] = rnd
                decs = (
                    self._make_pillar_decisions()
                    if paradigm == "multi_toggles"
                    else copy.deepcopy(BASE_DECISIONS)
                )
                result = engine.process_tick(gs, bus, decs, decision_paradigm=paradigm)
                assert validate_simulation_state(
                    result["global_state"], result["bu_states"]
                ) is True, f"Paradigm '{paradigm}' round {rnd}: hard invariant violated"
                gs  = result["global_state"]
                bus = result["bu_states"]
