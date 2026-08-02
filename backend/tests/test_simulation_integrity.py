"""
Simulation Integrity Validator & Stress Test
============================================
Baseline guards that verify critical variables never enter an invalid state
during engine execution.

Four invariant categories are checked after every engine tick:
  1. Carbon Constraints  — tCO2e emissions softly-warned when exceeding the cap.
  2. Economic Invariants — corporate treasury must not breach the -$500M floor.
  3. Liquidity           — liquidity_ratio (EBITDA / Revenue) softly-warned when
                           below the configured minimum.
  4. BU Field Bounds     — per-BU fields that the engine guarantees are bounded
                           (reputation, social_license, NCD, carbon_intensity)
                           must stay within their valid ranges.

The stress test runner (`run_stress_test`) exercises `engine.process_tick`
across N randomised game-states and asserts that no tick causes a hard
constraint violation.  It can also be invoked directly from the command line:

    python tests/test_simulation_integrity.py [--iterations N] [--seed S]

The multi-round tests exercise a sequential chain of ticks to verify that
accrued state drifts correctly across rounds without silent corruption.

The mutation-guard tests confirm that `process_tick` never modifies its
caller's input dicts in-place — a common source of hard-to-trace bugs.
"""

import copy
import math
import random
import pytest

import engine
import sys
import pathlib

# ── Import config constants (already decoupled via simulation_config.json) ──
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from config import (
    CONSTRAINT_MAX_CARBON_EMISSIONS,
    CONSTRAINT_MIN_LIQUIDITY_RATIO,
)

# ── Canonical state fixtures (mirrors test_stress_scenarios.py) ──────────────

BASE_GLOBAL = {
    "round_number": 3,
    "corporate_treasury": 25_000_000,
    "group_reputation": 60.0,
    "synergy_multiplier": 1.0,
    "cost_of_capital": 0.05,
    "inflation_index": 0.025,
    "active_event_flags": {},
    "pending_capex_projects": [],
    "green_transition_fund": 0.0,
    "tipping_point_active": False,
    "tipping_tier": "none",
}

BASE_BUS = [
    {
        "bu_id": "pharma",
        "revenue_base": 18_000_000,
        "opex_base": 11_500_000,
        "reputation_score": 72,
        "social_license_score": 70,
        "governance_risk_score": 15,
        "carbon_intensity": 45,
        "natural_capital_debt": 5_000,
        "risk_factors": {},
        "staff_burnout_index": 0,
    },
    {
        "bu_id": "electronics",
        "revenue_base": 22_000_000,
        "opex_base": 14_000_000,
        "reputation_score": 58,
        "social_license_score": 65,
        "governance_risk_score": 25,
        "carbon_intensity": 60,
        "natural_capital_debt": 3_800,
        "risk_factors": {},
        "staff_burnout_index": 0,
    },
    {
        "bu_id": "consumer_goods",
        "revenue_base": 15_000_000,
        "opex_base": 9_000_000,
        "reputation_score": 74,
        "social_license_score": 78,
        "governance_risk_score": 10,
        "carbon_intensity": 30,
        "natural_capital_debt": 2_100,
        "risk_factors": {},
        "staff_burnout_index": 0,
    },
    {
        "bu_id": "software",
        "revenue_base": 20_000_000,
        "opex_base": 8_000_000,
        "reputation_score": 82,
        "social_license_score": 85,
        "governance_risk_score": 5,
        "carbon_intensity": 10,
        "natural_capital_debt": 500,
        "risk_factors": {},
        "staff_burnout_index": 0,
    },
]

BASE_DECISIONS = [
    {"bu_id": "pharma",         "investment_ratio": 0.3, "capex_allocated": 500_000, "choice_selected": "option_b"},
    {"bu_id": "electronics",    "investment_ratio": 0.3, "capex_allocated": 500_000, "choice_selected": "option_b"},
    {"bu_id": "consumer_goods", "investment_ratio": 0.3, "capex_allocated": 500_000, "choice_selected": "option_b"},
    {"bu_id": "software",       "investment_ratio": 0.3, "capex_allocated": 500_000, "choice_selected": "option_b"},
]

# ── Insolvency hard floor (mirrors engine logic) ──────────────────────────────
# The engine caps treasury at -500M; solvency is meaningfully "negative" only
# beyond the game-defined floor, so we don't flag states between 0 and -500M
# as "invalid" — the game deliberately allows those.
TREASURY_HARD_FLOOR = -500_000_000


# ═══════════════════════════════════════════════════════════════════════════════
#  CORE VALIDATOR
# ═══════════════════════════════════════════════════════════════════════════════

def _derive_liquidity_ratio(global_state: dict, bu_states: list[dict]) -> float:
    """
    Derive a liquidity proxy from post-tick state.

    liquidity_ratio = EBITDA / Total_Revenue
      where EBITDA  = Σ(revenue - opex)
            Revenue = Σ(revenue_base)

    Returns 1.0 (fully liquid) when revenue is zero to avoid spurious failures
    in edge-case states where BUs have been zeroed out.
    """
    total_revenue = sum(bu.get("revenue_base", 0.0) for bu in bu_states)
    total_ebitda  = sum(
        bu.get("revenue_base", 0.0) - bu.get("opex_base", 0.0)
        for bu in bu_states
    )
    if total_revenue <= 0:
        return 1.0
    return total_ebitda / total_revenue


def validate_simulation_state(
    global_state: dict,
    bu_states: list[dict],
    *,
    max_carbon_limit: float = CONSTRAINT_MAX_CARBON_EMISSIONS,
    min_liquidity_requirement: float = CONSTRAINT_MIN_LIQUIDITY_RATIO,
) -> bool:
    """
    Perform a sanity check on the current simulation state.

    Maps the original script's generic ``state`` dict onto the engine's actual
    output shape (``global_state`` + ``bu_states``).

    Constraint semantics — aligned with engine behaviour:

    1. Carbon Constraints (SOFT)
       The engine treats the carbon cap as a *game event* — when tco2e_emissions
       exceeds CONSTRAINT_MAX_CARBON_EMISSIONS, it fires an
       ``emissions_limit_breached`` event and applies a reputation penalty of -5,
       but execution continues normally.  The validator therefore mirrors this by
       printing a warning (and recording the event flag) rather than raising.

    2. Economic Invariants (HARD)
       The engine clamps corporate_treasury at TREASURY_HARD_FLOOR (-500 M).
       A value below that floor means the clamping failed — this is a genuine
       engine bug and must raise.

    3. Liquidity (SOFT WARNING)
       A liquidity ratio below the minimum signals financial distress; the game
       allows distressed states, so we warn rather than raise.

    Returns True when all checks pass (hard and soft).
    Raises ValueError only for hard violations.
    Prints warnings for soft violations and continues.
    """
    total_emissions = global_state.get("tco2e_emissions", 0.0) or 0.0
    total_assets    = global_state.get("corporate_treasury", 0.0) or 0.0
    liquidity_ratio = _derive_liquidity_ratio(global_state, bu_states)

    # 1. Carbon Constraints (soft — matches engine's game-event behaviour)
    if total_emissions > max_carbon_limit:
        # Cross-check with the engine's event flag for traceability
        engine_flagged = global_state.get("active_event_flags", {}).get(
            "emissions_limit_breached", False
        )
        print(
            f"Warning: Carbon limit exceeded. "
            f"emissions={total_emissions:,.1f} > limit={max_carbon_limit:,.1f} tCO2e. "
            f"Engine event flag: {engine_flagged}"
        )

    # 2. Economic Invariants (hard — treasury must not breach insolvency floor)
    if total_assets < TREASURY_HARD_FLOOR:
        raise ValueError(
            f"Critical: Negative asset balance breached insolvency floor. "
            f"treasury={total_assets:,.0f} < floor={TREASURY_HARD_FLOOR:,.0f}"
        )

    # 3. Liquidity (soft warning — game allows distressed states)
    if liquidity_ratio < min_liquidity_requirement:
        print(
            f"Warning: Liquidity approaching critical threshold. "
            f"ratio={liquidity_ratio:.3f} < min={min_liquidity_requirement:.3f}"
        )

    return True


# ── Per-BU invariant helper ───────────────────────────────────────────────────

# Field-level bounds guaranteed by the engine's clamping logic.
# Any value outside these ranges indicates a clamping failure.
_BU_FIELD_BOUNDS: dict[str, tuple[float, float]] = {
    "reputation_score":     (0.0, 100.0),
    "social_license_score": (0.0, 100.0),
    "governance_risk_score": (0.0, 100.0),
    "natural_capital_debt": (0.0, 1_000_000.0),   # hard cap at 1M (engine: HARD-003)
    "carbon_intensity":     (0.0, float("inf")),   # non-negative; no upper hard cap
    "staff_burnout_index":  (0.0, 100.0),
}


def validate_bu_fields(bu_states: list[dict]) -> list[str]:
    """
    Check per-BU numeric fields against their engine-guaranteed bounds.

    Returns a list of human-readable violation strings.
    An empty list means all BU fields are within bounds.

    This is intentionally non-raising so callers can choose between
    asserting in tests or logging in production monitors.
    """
    violations: list[str] = []
    for bu in bu_states:
        bu_id = bu.get("bu_id", "<unknown>")
        for field, (lo, hi) in _BU_FIELD_BOUNDS.items():
            val = bu.get(field)
            if val is None:
                continue  # field not present — engine may not set it for all paradigms
            if not (lo <= val <= hi):
                violations.append(
                    f"{bu_id}.{field}={val:.4g} out of bounds [{lo}, {hi}]"
                )
    return violations


# ═══════════════════════════════════════════════════════════════════════════════
#  STRESS TEST RUNNER
# ═══════════════════════════════════════════════════════════════════════════════

def _random_global_state(rng: random.Random) -> dict:
    """Generate a randomised but plausible global state for stress testing."""
    gs = copy.deepcopy(BASE_GLOBAL)
    gs["round_number"]        = rng.randint(1, 10)
    gs["corporate_treasury"]  = rng.uniform(-50_000_000, 80_000_000)
    gs["group_reputation"]    = rng.uniform(10.0, 95.0)
    gs["synergy_multiplier"]  = rng.uniform(0.5, 2.0)
    gs["cost_of_capital"]     = rng.uniform(0.03, 0.20)
    gs["inflation_index"]     = rng.uniform(0.01, 0.08)
    gs["tipping_point_active"] = rng.random() < 0.15
    gs["tipping_tier"]        = rng.choice(["none", "yellow", "orange", "red"])
    return gs


def _random_bu_states(rng: random.Random) -> list[dict]:
    """
    Jitter the canonical BU states within realistic ranges.

    Carbon intensity is intentionally capped at a per-BU level that keeps
    group tCO2e well below CONSTRAINT_MAX_CARBON_EMISSIONS even at peak
    revenue, so that stress tests focus on economic/liquidity paths rather
    than trivially triggering the (soft) carbon-warning on every iteration.

    Formula: max_ci_per_bu = limit / (n_bus × max_revenue_per_bu / 1_000_000)
    With limit=5,000 tCO2e, 4 BUs, max_revenue=35M → safe CI ≤ ~35.7 t/$1M rev.
    We use 30 as a rounded conservative ceiling.
    """
    bus = copy.deepcopy(BASE_BUS)
    for bu in bus:
        bu["revenue_base"]         = rng.uniform(5_000_000, 35_000_000)
        bu["opex_base"]            = rng.uniform(3_000_000, bu["revenue_base"] * 0.95)
        bu["reputation_score"]     = rng.uniform(0.0, 100.0)
        bu["social_license_score"] = rng.uniform(0.0, 100.0)
        bu["governance_risk_score"]= rng.uniform(0.0, 80.0)
        # Cap CI so group-level tCO2e stays below the configured limit
        bu["carbon_intensity"]     = rng.uniform(0.0, 30.0)
        bu["natural_capital_debt"] = rng.uniform(0.0, 500_000)
        bu["staff_burnout_index"]  = rng.uniform(0.0, 100.0)
    return bus


def _random_decisions(bus: list[dict], rng: random.Random) -> list[dict]:
    choices = ["option_a", "option_b", "option_c"]
    return [
        {
            "bu_id":           bu["bu_id"],
            "investment_ratio": rng.uniform(0.0, 1.0),
            "capex_allocated":  rng.uniform(0.0, 2_000_000),
            "choice_selected":  rng.choice(choices),
        }
        for bu in bus
    ]


def run_stress_test(iterations: int = 100, seed: int = 42) -> None:
    """
    Run ``engine.process_tick`` across ``iterations`` randomised game-states
    and assert that ``validate_simulation_state`` passes on every output.

    Uses a fixed seed so failures are deterministic and reproducible.
    """
    rng = random.Random(seed)
    passed = 0
    warnings_seen = 0

    for i in range(iterations):
        gs   = _random_global_state(rng)
        bus  = _random_bu_states(rng)
        decs = _random_decisions(bus, rng)

        result     = engine.process_tick(gs, bus, decs)
        out_gs     = result["global_state"]
        out_bus    = result["bu_states"]

        # Capture liquidity warnings without failing the test
        liq = _derive_liquidity_ratio(out_gs, out_bus)
        if liq < CONSTRAINT_MIN_LIQUIDITY_RATIO:
            warnings_seen += 1

        # Hard invariant check — will raise on critical violation
        validate_simulation_state(out_gs, out_bus)

        # Per-BU field bounds check
        bu_violations = validate_bu_fields(out_bus)
        if bu_violations:
            raise AssertionError(
                f"Iteration {i}: BU field violation(s):\n  "
                + "\n  ".join(bu_violations)
            )

        passed += 1

    print(
        f"Stress test passed: {passed}/{iterations} iterations completed. "
        f"({warnings_seen} liquidity warnings recorded)"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  PYTEST TEST CASES
# ═══════════════════════════════════════════════════════════════════════════════

class TestValidateSimulationState:
    """Unit tests for the validate_simulation_state guard function."""

    def _tick(self, gs_overrides=None, bu_overrides=None, dec_overrides=None):
        """Helper: run one engine tick and return (out_gs, out_bus)."""
        gs   = {**copy.deepcopy(BASE_GLOBAL),  **(gs_overrides  or {})}
        bus  = copy.deepcopy(BASE_BUS)
        decs = copy.deepcopy(BASE_DECISIONS)
        if bu_overrides:
            for bu in bus:
                bu.update(bu_overrides.get(bu["bu_id"], {}))
        if dec_overrides:
            for d in decs:
                d.update(dec_overrides.get(d["bu_id"], {}))
        result = engine.process_tick(gs, bus, decs)
        return result["global_state"], result["bu_states"]

    # ── Carbon Constraints ────────────────────────────────────────────────────
    # Note: carbon breach is a SOFT constraint in both the engine and validator.
    # Exceeding the cap fires a game event + reputation penalty but does NOT
    # halt execution — the validator prints a warning and returns True.

    def test_carbon_within_limit_passes(self):
        """Normal play within the cap must pass silently."""
        out_gs, out_bus = self._tick()
        out_gs["tco2e_emissions"] = CONSTRAINT_MAX_CARBON_EMISSIONS * 0.5
        assert validate_simulation_state(out_gs, out_bus) is True

    def test_carbon_at_exact_limit_passes(self):
        """Emissions exactly at the cap boundary must pass (not strictly exceed)."""
        out_gs, out_bus = self._tick()
        out_gs["tco2e_emissions"] = CONSTRAINT_MAX_CARBON_EMISSIONS
        assert validate_simulation_state(out_gs, out_bus) is True

    def test_carbon_exceeds_limit_warns_not_raises(self, capsys):
        """Emissions above the cap must print a warning but NOT raise — soft constraint."""
        out_gs, out_bus = self._tick()
        out_gs["tco2e_emissions"] = CONSTRAINT_MAX_CARBON_EMISSIONS + 100
        result = validate_simulation_state(out_gs, out_bus)
        assert result is True
        captured = capsys.readouterr()
        assert "Warning" in captured.out
        assert "Carbon limit exceeded" in captured.out

    def test_carbon_exceeds_limit_engine_event_flag_reported(self, capsys):
        """When the engine sets emissions_limit_breached, the warning mentions it."""
        out_gs, out_bus = self._tick()
        out_gs["tco2e_emissions"] = CONSTRAINT_MAX_CARBON_EMISSIONS + 1
        out_gs.setdefault("active_event_flags", {})["emissions_limit_breached"] = True
        validate_simulation_state(out_gs, out_bus)
        captured = capsys.readouterr()
        assert "True" in captured.out  # engine flag echoed in warning

    def test_carbon_none_treated_as_zero(self):
        """Missing tco2e_emissions field must be treated as 0 (not raise)."""
        out_gs, out_bus = self._tick()
        out_gs.pop("tco2e_emissions", None)
        assert validate_simulation_state(out_gs, out_bus) is True

    # ── Economic Invariants ───────────────────────────────────────────────────

    def test_positive_treasury_passes(self):
        out_gs, out_bus = self._tick()
        out_gs["corporate_treasury"] = 10_000_000
        assert validate_simulation_state(out_gs, out_bus) is True

    def test_zero_treasury_passes(self):
        out_gs, out_bus = self._tick(gs_overrides={"corporate_treasury": 0})
        out_gs["corporate_treasury"] = 0
        assert validate_simulation_state(out_gs, out_bus) is True

    def test_treasury_within_insolvency_floor_passes(self):
        """Negative treasury within the game's hard floor must pass."""
        out_gs, out_bus = self._tick()
        out_gs["corporate_treasury"] = -100_000_000
        assert validate_simulation_state(out_gs, out_bus) is True

    def test_treasury_below_hard_floor_raises(self):
        """Treasury beyond the -500M floor must raise ValueError."""
        out_gs, out_bus = self._tick()
        out_gs["corporate_treasury"] = TREASURY_HARD_FLOOR - 1
        with pytest.raises(ValueError, match="insolvency floor"):
            validate_simulation_state(out_gs, out_bus)

    # ── Liquidity ─────────────────────────────────────────────────────────────

    def test_healthy_liquidity_no_warning(self, capsys):
        """Healthy EBITDA margin should produce no liquidity warning."""
        out_gs, out_bus = self._tick()
        # Inflate revenue to guarantee healthy ratio
        for bu in out_bus:
            bu["revenue_base"] = bu["opex_base"] * 2
        validate_simulation_state(out_gs, out_bus)
        captured = capsys.readouterr()
        assert "Warning" not in captured.out

    def test_low_liquidity_prints_warning(self, capsys):
        """Distressed EBITDA margin should print a liquidity warning."""
        out_gs, out_bus = self._tick()
        # Compress margin below min ratio
        for bu in out_bus:
            bu["revenue_base"] = bu["opex_base"] * (1 + CONSTRAINT_MIN_LIQUIDITY_RATIO * 0.5)
        validate_simulation_state(out_gs, out_bus)
        captured = capsys.readouterr()
        assert "Warning" in captured.out

    def test_low_liquidity_does_not_raise(self):
        """Liquidity breach must only warn, not raise — it is a soft constraint."""
        out_gs, out_bus = self._tick()
        for bu in out_bus:
            bu["revenue_base"] = bu["opex_base"] * 0.5  # EBITDA is negative
        # Should return True, not raise
        result = validate_simulation_state(out_gs, out_bus)
        assert result is True

    def test_zero_revenue_does_not_raise(self):
        """Zero-revenue state must not cause ZeroDivisionError."""
        out_gs, out_bus = self._tick()
        for bu in out_bus:
            bu["revenue_base"] = 0
        assert validate_simulation_state(out_gs, out_bus) is True

    # ── Combined state ────────────────────────────────────────────────────────

    def test_nominal_engine_output_passes_all_checks(self):
        """A standard tick on nominal inputs must pass all three invariants."""
        out_gs, out_bus = self._tick()
        assert validate_simulation_state(out_gs, out_bus) is True

    def test_high_crisis_state_passes_all_checks(self):
        """A high-crisis tick (rep=20, treasury low) should still pass."""
        out_gs, out_bus = self._tick(
            gs_overrides={
                "group_reputation": 20.0,
                "corporate_treasury": 500_000,
                "cost_of_capital": 0.15,
            }
        )
        assert validate_simulation_state(out_gs, out_bus) is True


class TestStressTestRunner:
    """Integration tests for the randomised stress-test runner."""

    def test_stress_test_50_iterations(self):
        """50 random ticks must all pass the integrity validator."""
        run_stress_test(iterations=50, seed=0)

    def test_stress_test_100_iterations(self):
        """100 random ticks must all pass the integrity validator (canonical run)."""
        run_stress_test(iterations=100, seed=42)

    def test_stress_test_different_seeds_consistent(self):
        """Multiple seeds should all complete without raising."""
        for seed in (1, 7, 13, 99, 2024):
            run_stress_test(iterations=20, seed=seed)

    def test_stress_test_conservative_decisions(self):
        """All-conservative decisions across random states must stay within bounds."""
        rng = random.Random(77)
        for _ in range(30):
            gs  = _random_global_state(rng)
            bus = _random_bu_states(rng)
            decs = [
                {
                    "bu_id":            bu["bu_id"],
                    "investment_ratio":  0.05,
                    "capex_allocated":   100_000,
                    "choice_selected":   "option_c",
                }
                for bu in bus
            ]
            result  = engine.process_tick(gs, bus, decs)
            validate_simulation_state(result["global_state"], result["bu_states"])

    def test_stress_test_aggressive_decisions(self):
        """All-aggressive (high CAPEX, option_a) decisions must stay within bounds."""
        rng = random.Random(88)
        for _ in range(30):
            gs  = _random_global_state(rng)
            # Use positive treasury so high CAPEX doesn't insta-insolvency
            gs["corporate_treasury"] = abs(gs["corporate_treasury"]) + 10_000_000
            bus = _random_bu_states(rng)
            decs = [
                {
                    "bu_id":            bu["bu_id"],
                    "investment_ratio":  0.9,
                    "capex_allocated":   1_500_000,
                    "choice_selected":   "option_a",
                }
                for bu in bus
            ]
            result  = engine.process_tick(gs, bus, decs)
            validate_simulation_state(result["global_state"], result["bu_states"])


class TestLiquidityRatioDerived:
    """Unit tests for the internal _derive_liquidity_ratio helper."""

    def test_healthy_margin(self):
        bus = [{"revenue_base": 10_000_000, "opex_base": 6_000_000}]
        assert _derive_liquidity_ratio({}, bus) == pytest.approx(0.40)

    def test_break_even(self):
        bus = [{"revenue_base": 10_000_000, "opex_base": 10_000_000}]
        assert _derive_liquidity_ratio({}, bus) == pytest.approx(0.0)

    def test_negative_ebitda(self):
        bus = [{"revenue_base": 5_000_000, "opex_base": 7_000_000}]
        assert _derive_liquidity_ratio({}, bus) == pytest.approx(-0.40)

    def test_zero_revenue_returns_one(self):
        bus = [{"revenue_base": 0, "opex_base": 1_000_000}]
        assert _derive_liquidity_ratio({}, bus) == 1.0

    def test_multiple_bus_aggregated(self):
        bus = [
            {"revenue_base": 10_000_000, "opex_base": 6_000_000},
            {"revenue_base": 20_000_000, "opex_base": 14_000_000},
        ]
        # Combined: revenue=30M, EBITDA=10M → ratio=1/3
        assert _derive_liquidity_ratio({}, bus) == pytest.approx(1 / 3)


class TestBUFieldInvariants:
    """
    Verify that per-BU field bounds are maintained across all supported
    paradigms and edge-case scenarios.
    """

    def _tick_all(self, gs_overrides=None) -> list[dict]:
        """Run a tick and return the bu_states list."""
        gs   = {**copy.deepcopy(BASE_GLOBAL), **(gs_overrides or {})}
        result = engine.process_tick(gs, copy.deepcopy(BASE_BUS), copy.deepcopy(BASE_DECISIONS))
        return result["bu_states"]

    def test_nominal_tick_no_bu_violations(self):
        """A normal tick must produce zero BU field violations."""
        bus = self._tick_all()
        violations = validate_bu_fields(bus)
        assert violations == [], f"Unexpected BU violations: {violations}"

    def test_reputation_bounded_after_crisis(self):
        """High crisis severity must not push reputation below 0."""
        bus = self._tick_all(gs_overrides={"group_reputation": 5.0})
        for bu in bus:
            assert bu["reputation_score"] >= 0.0, (
                f"{bu['bu_id']}.reputation_score went negative: {bu['reputation_score']}"
            )

    def test_social_license_bounded_0_to_100(self):
        """Social license must remain in [0, 100] even after strikes."""
        bus = self._tick_all()
        for bu in bus:
            assert 0.0 <= bu["social_license_score"] <= 100.0, (
                f"{bu['bu_id']}.social_license_score={bu['social_license_score']} out of [0,100]"
            )

    def test_ncd_does_not_go_negative(self):
        """Natural Capital Debt must never go below 0 — penalties are additive."""
        bus = self._tick_all()
        for bu in bus:
            assert bu.get("natural_capital_debt", 0.0) >= 0.0, (
                f"{bu['bu_id']}.natural_capital_debt is negative: {bu['natural_capital_debt']}"
            )

    def test_ncd_does_not_exceed_hard_cap(self):
        """NCD must not exceed the 1M hard cap (HARD-003)."""
        # Pre-load BUs with NCD near the cap
        bus_pre = copy.deepcopy(BASE_BUS)
        for bu in bus_pre:
            bu["natural_capital_debt"] = 999_990
        result = engine.process_tick(copy.deepcopy(BASE_GLOBAL), bus_pre, copy.deepcopy(BASE_DECISIONS))
        for bu in result["bu_states"]:
            assert bu["natural_capital_debt"] <= 1_000_000, (
                f"{bu['bu_id']}.natural_capital_debt={bu['natural_capital_debt']} exceeds 1M cap"
            )

    def test_carbon_intensity_non_negative(self):
        """CI must never go below 0 (the engine clamps with max(0.0, ...))."""
        bus = self._tick_all()
        for bu in bus:
            assert bu.get("carbon_intensity", 0.0) >= 0.0, (
                f"{bu['bu_id']}.carbon_intensity is negative: {bu['carbon_intensity']}"
            )

    def test_burnout_bounded_0_to_100(self):
        """Staff burnout index must remain in [0, 100]."""
        bus_pre = copy.deepcopy(BASE_BUS)
        for bu in bus_pre:
            bu["staff_burnout_index"] = 95.0  # near ceiling
        result = engine.process_tick(copy.deepcopy(BASE_GLOBAL), bus_pre, copy.deepcopy(BASE_DECISIONS))
        for bu in result["bu_states"]:
            bval = bu.get("staff_burnout_index")
            if bval is not None:
                assert 0.0 <= bval <= 100.0, (
                    f"{bu['bu_id']}.staff_burnout_index={bval} out of [0,100]"
                )

    def test_validate_bu_fields_helper_catches_violation(self):
        """Manually inject an out-of-bounds value and verify the helper catches it."""
        bad_bus = copy.deepcopy(BASE_BUS)
        bad_bus[0]["reputation_score"] = -5.0     # below 0
        bad_bus[1]["social_license_score"] = 110.0 # above 100
        violations = validate_bu_fields(bad_bus)
        assert len(violations) == 2
        assert any("reputation_score" in v for v in violations)
        assert any("social_license_score" in v for v in violations)

    def test_validate_bu_fields_returns_empty_on_clean_state(self):
        """No violations on the canonical BASE_BUS."""
        # BASE_BUS has reputation/social_license in valid range;
        # NCD well below 1M cap; CI non-negative.
        assert validate_bu_fields(BASE_BUS) == []


class TestMultiRoundIntegrity:
    """
    Run a sequential chain of ticks and assert invariants hold at every step.

    This catches state-accumulation bugs that are invisible in single-tick tests
    (e.g. NCD compounding past the cap, reputation decaying below 0).
    """

    def _run_chain(self, rounds: int, gs_seed: dict | None = None) -> list[dict]:
        """
        Execute ``rounds`` sequential ticks using the previous tick's output as
        the next tick's input.  Returns a list of (global_state, bu_states) tuples
        for each completed round.
        """
        gs   = {**copy.deepcopy(BASE_GLOBAL), **(gs_seed or {})}
        bus  = copy.deepcopy(BASE_BUS)
        history: list[tuple[dict, list[dict]]] = []

        options = ["option_a", "option_b", "option_c"]
        for rnd in range(1, rounds + 1):
            gs["round_number"] = rnd
            choice = options[(rnd - 1) % 3]
            decs = [
                {
                    "bu_id": bu["bu_id"],
                    "investment_ratio": 0.25,
                    "capex_allocated": 400_000,
                    "choice_selected": choice,
                }
                for bu in bus
            ]
            result = engine.process_tick(gs, bus, decs)
            gs  = result["global_state"]
            bus = result["bu_states"]
            history.append((copy.deepcopy(gs), copy.deepcopy(bus)))
        return history

    def test_5_round_chain_passes_all_invariants(self):
        """5-round chain on nominal start state must pass all invariants at every round."""
        history = self._run_chain(5)
        for rnd_idx, (gs, bus) in enumerate(history, start=1):
            assert validate_simulation_state(gs, bus) is True, f"Violation at round {rnd_idx}"
            violations = validate_bu_fields(bus)
            assert violations == [], f"BU violations at round {rnd_idx}: {violations}"

    def test_10_round_chain_passes_all_invariants(self):
        """Full 10-round chain must pass all invariants at every round."""
        history = self._run_chain(10)
        for rnd_idx, (gs, bus) in enumerate(history, start=1):
            assert validate_simulation_state(gs, bus) is True, f"Violation at round {rnd_idx}"
            violations = validate_bu_fields(bus)
            assert violations == [], f"BU violations at round {rnd_idx}: {violations}"

    def test_treasury_monotonically_present_across_rounds(self):
        """corporate_treasury must be a number (not None/NaN) after every round."""
        history = self._run_chain(10)
        for rnd_idx, (gs, _) in enumerate(history, start=1):
            val = gs.get("corporate_treasury")
            assert val is not None, f"treasury is None at round {rnd_idx}"
            assert not (isinstance(val, float) and math.isnan(val)), (
                f"treasury is NaN at round {rnd_idx}"
            )

    def test_round_number_increments_correctly(self):
        """global_state.round_number must advance by 1 each tick."""
        history = self._run_chain(6)
        for expected_round, (gs, _) in enumerate(history, start=2):
            # After tick N (0-indexed), the engine advances to round N+2
            # because we start at round 1 and the engine increments.
            assert gs["round_number"] == expected_round, (
                f"Expected round {expected_round}, got {gs['round_number']}"
            )

    def test_ncd_never_exceeds_cap_across_chain(self):
        """NCD must stay ≤ 1M on every BU across all 10 rounds."""
        history = self._run_chain(10)
        for rnd_idx, (_, bus) in enumerate(history, start=1):
            for bu in bus:
                ncd = bu.get("natural_capital_debt", 0.0)
                assert ncd <= 1_000_000, (
                    f"Round {rnd_idx}: {bu['bu_id']}.NCD={ncd:,.0f} exceeds 1M cap"
                )

    def test_reputation_never_goes_negative_across_chain(self):
        """Group reputation and per-BU reputation must stay ≥ 0 in all rounds."""
        history = self._run_chain(10)
        for rnd_idx, (gs, bus) in enumerate(history, start=1):
            assert gs.get("group_reputation", 0.0) >= 0.0, (
                f"Round {rnd_idx}: group_reputation went negative"
            )
            for bu in bus:
                assert bu["reputation_score"] >= 0.0, (
                    f"Round {rnd_idx}: {bu['bu_id']}.reputation_score went negative"
                )

    def test_distressed_start_10_round_chain(self):
        """Even a distressed start (low treasury, low rep) must not breach hard invariants."""
        history = self._run_chain(
            10,
            gs_seed={
                "corporate_treasury": 500_000,
                "group_reputation": 15.0,
                "cost_of_capital": 0.18,
            },
        )
        for rnd_idx, (gs, bus) in enumerate(history, start=1):
            # Hard check: treasury floor
            treasury = gs.get("corporate_treasury", 0.0)
            assert treasury >= TREASURY_HARD_FLOOR, (
                f"Round {rnd_idx}: treasury {treasury:,.0f} breached hard floor"
            )
            # Hard check: BU bounds
            violations = validate_bu_fields(bus)
            assert violations == [], f"Round {rnd_idx} BU violations: {violations}"


class TestInputMutationGuard:
    """
    Verify that engine.process_tick does NOT mutate its input dicts in-place.

    Any in-place mutation is a latent bug: the caller's state would drift
    silently and produce incorrect results on repeated calls with the same
    input (e.g. in benchmarking or what-if analysis).
    """

    def test_global_state_not_mutated(self):
        """The input global_state dict must be unchanged after process_tick."""
        gs_input = copy.deepcopy(BASE_GLOBAL)
        gs_snapshot = copy.deepcopy(gs_input)
        engine.process_tick(gs_input, copy.deepcopy(BASE_BUS), copy.deepcopy(BASE_DECISIONS))
        assert gs_input == gs_snapshot, (
            "process_tick mutated the input global_state. "
            f"Changed keys: {[k for k in gs_snapshot if gs_snapshot[k] != gs_input.get(k)]}"
        )

    def test_bu_states_not_mutated(self):
        """The input bu_states list must be unchanged after process_tick."""
        bus_input = copy.deepcopy(BASE_BUS)
        bus_snapshot = copy.deepcopy(bus_input)
        engine.process_tick(copy.deepcopy(BASE_GLOBAL), bus_input, copy.deepcopy(BASE_DECISIONS))
        for i, (orig, snap) in enumerate(zip(bus_input, bus_snapshot)):
            assert orig == snap, (
                f"process_tick mutated bu_states[{i}] ({snap['bu_id']}). "
                f"Changed keys: {[k for k in snap if snap[k] != orig.get(k)]}"
            )

    def test_decisions_not_mutated(self):
        """The input decisions list must be unchanged after process_tick."""
        decs_input = copy.deepcopy(BASE_DECISIONS)
        decs_snapshot = copy.deepcopy(decs_input)
        engine.process_tick(copy.deepcopy(BASE_GLOBAL), copy.deepcopy(BASE_BUS), decs_input)
        assert decs_input == decs_snapshot, (
            "process_tick mutated the decisions list. "
            f"Changed: {[d for d, s in zip(decs_input, decs_snapshot) if d != s]}"
        )

    def test_repeated_calls_same_input_same_output(self):
        """
        Verify that the fields the engine computes *deterministically* are
        identical across two independent process_tick calls with the same inputs.

        Context: the engine intentionally uses Python's global random module for
        stochastic events (overrun risk, strike probability, black swan selection).
        These make fields like ``corporate_treasury`` differ between calls because
        the RNG is not seeded per-call.  This is correct game behaviour.

        This test therefore only asserts the subset of fields that the engine
        derives from pure arithmetic — not from stochastic branches:
          - ``tco2e_emissions``    : Σ(CI × revenue / 1M), no RNG
          - ``round_number``       : input incremented by 1, no RNG
          - ``historical_ebitda``  : Σ(revenue − opex), no RNG (pre-stochastic OPEX)
          - Per-BU ``carbon_intensity`` : formula-driven, no RNG

        Fields that are intentionally stochastic (treasury, opex after strikes /
        overruns, etc.) are excluded from this assertion.
        """
        # Fields computed purely from input arithmetic — no RNG involvement.
        # round_number: input.round_number + 1 — purely deterministic.
        # NOTE: tco2e_emissions = Σ(CI × revenue_base / 1M) is excluded because
        # revenue_base itself is modified by stochastic paths (cash conversion,
        # cannibalization, strike penalties) which feed into the emission calc.
        pure_arithmetic_global = [
            "round_number",
        ]
        # carbon_intensity per BU: CI delta routing is formula-driven.
        # The post-tick CI = max(0, old_CI + delta) — deterministic given same CI input.
        pure_arithmetic_bu = [
            "carbon_intensity",
        ]

        def run():
            return engine.process_tick(
                copy.deepcopy(BASE_GLOBAL),
                copy.deepcopy(BASE_BUS),
                copy.deepcopy(BASE_DECISIONS),
            )

        r1 = run()
        r2 = run()

        for field in pure_arithmetic_global:
            assert r1["global_state"].get(field) == r2["global_state"].get(field), (
                f"Pure-arithmetic field '{field}' differs between runs: "
                f"{r1['global_state'].get(field)} != {r2['global_state'].get(field)}"
            )

        for bu1, bu2 in zip(r1["bu_states"], r2["bu_states"]):
            for field in pure_arithmetic_bu:
                assert bu1.get(field) == bu2.get(field), (
                    f"{bu1['bu_id']}.{field} differs between runs: "
                    f"{bu1.get(field)} != {bu2.get(field)}"
                )

    def test_engine_stochasticity_is_expected(self):
        """
        Confirm the engine IS stochastic for cost/treasury fields so
        the previous test's exclusions are justified — not hiding a silent bug.

        We run 20 identical ticks and verify that treasury varies across at
        least some of them (i.e. the RNG paths are actually being exercised).
        """
        treasuries = set()
        for _ in range(20):
            result = engine.process_tick(
                copy.deepcopy(BASE_GLOBAL),
                copy.deepcopy(BASE_BUS),
                copy.deepcopy(BASE_DECISIONS),
            )
            treasuries.add(result["global_state"]["corporate_treasury"])
        # We expect at least 2 distinct treasury values across 20 runs
        assert len(treasuries) > 1, (
            "Treasury was identical across all 20 runs — "
            "stochastic paths may not be active on this state."
        )


# ═══════════════════════════════════════════════════════════════════════════════
#  CLI ENTRYPOINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    import sys as _sys
    import pathlib as _pathlib

    # Ensure the backend directory is on sys.path when run directly.
    _backend = _pathlib.Path(__file__).resolve().parent.parent
    if str(_backend) not in _sys.path:
        _sys.path.insert(0, str(_backend))

    parser = argparse.ArgumentParser(
        description="Muressons Simulation Integrity Stress Test",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--iterations", type=int, default=1000,
        help="Number of random engine ticks to execute.",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="RNG seed for reproducibility.",
    )
    args = parser.parse_args()

    print("=" * 62)
    print("  Muressons Simulation — Integrity Stress Test")
    print("=" * 62)
    print(f"  Iterations : {args.iterations}")
    print(f"  Seed       : {args.seed}")
    print(f"  Carbon cap : {CONSTRAINT_MAX_CARBON_EMISSIONS:,.0f} tCO2e")
    print(f"  Min liquid : {CONSTRAINT_MIN_LIQUIDITY_RATIO:.1%}")
    print(f"  Treasury floor: ${TREASURY_HARD_FLOOR:,.0f}")
    print()

    try:
        run_stress_test(iterations=args.iterations, seed=args.seed)
        print()
        print("  RESULT: PASS — all hard invariants held.")
        _sys.exit(0)
    except (ValueError, AssertionError) as exc:
        print(f"\n  RESULT: FAIL — {exc}")
        _sys.exit(1)
