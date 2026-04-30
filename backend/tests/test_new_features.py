"""
Muressons Global Command — New Feature Tests
Tests for Features 24-28 (Expert Recommendations)
Run: pytest tests/test_new_features.py -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine import (
    calc_macro_noise,
    detect_distress,
    calc_forecast,
    calc_sdg_impact,
    process_tick,
)
from terminal_valuation import determine_archetype, calculate_mr
from admin_shared import (
    get_marketplace_state,
    purchase_carbon_credits,
    hire_green_talent,
    _shared_marketplace,
)

# ── Fixtures ─────────────────────────────────────────────────────

SEED_BUS = [
    {"bu_id": "pharma", "revenue_base": 18_000_000, "opex_base": 11_500_000,
     "natural_capital_debt": 200, "social_license_score": 55, "reputation_score": 52,
     "governance_risk_score": 15, "water_dependency": 0.6, "carbon_intensity": 45, "risk_factors": {}},
    {"bu_id": "electronics", "revenue_base": 16_500_000, "opex_base": 10_800_000,
     "natural_capital_debt": 150, "social_license_score": 48, "reputation_score": 50,
     "governance_risk_score": 20, "water_dependency": 0.8, "carbon_intensity": 72, "risk_factors": {}},
    {"bu_id": "consumer_goods", "revenue_base": 10_500_000, "opex_base": 7_800_000,
     "natural_capital_debt": 100, "social_license_score": 52, "reputation_score": 53,
     "governance_risk_score": 10, "water_dependency": 0.3, "carbon_intensity": 38, "risk_factors": {}},
    {"bu_id": "software", "revenue_base": 8_500_000, "opex_base": 4_200_000,
     "natural_capital_debt": 50, "social_license_score": 60, "reputation_score": 58,
     "governance_risk_score": 8, "water_dependency": 0.1, "carbon_intensity": 28, "risk_factors": {}},
]

SEED_GLOBAL = {
    "round_number": 1,
    "corporate_treasury": 50_000_000,
    "group_reputation": 50,
    "synergy_multiplier": 1.0,
    "cost_of_capital": 0.05,
    "inflation_index": 0.025,
    "competitor_ebitda": 13_200_000,
    "active_event_flags": {},
}


# ═════════════════════════════════════════════════════════════════
#  FEATURE 24: Macro-Economic Noise
# ═════════════════════════════════════════════════════════════════

class TestMacroNoise:
    def test_noise_returns_all_fields(self):
        result = calc_macro_noise(1)
        assert "inflation_noise" in result
        assert "carbon_price_noise_pct" in result
        assert "micro_strike_triggered" in result
        assert "noise_message" in result

    def test_noise_within_bounds(self):
        """Inflation noise must be within ±0.2%."""
        for _ in range(100):
            result = calc_macro_noise(5)
            assert -0.002 <= result["inflation_noise"] <= 0.002
            assert -0.05 <= result["carbon_price_noise_pct"] <= 0.05

    def test_seeded_determinism(self):
        """Same seed produces same noise."""
        r1 = calc_macro_noise(3, seed=42)
        r2 = calc_macro_noise(3, seed=42)
        assert r1["inflation_noise"] == r2["inflation_noise"]
        assert r1["carbon_price_noise_pct"] == r2["carbon_price_noise_pct"]

    def test_macro_noise_in_tick(self):
        """Macro noise should appear in tick events."""
        decisions = [
            {"bu_id": "pharma", "investment_ratio": 0.0, "capex_allocated": 1},
            {"bu_id": "electronics", "investment_ratio": 0.0, "capex_allocated": 1},
            {"bu_id": "consumer_goods", "investment_ratio": 0.0, "capex_allocated": 1},
            {"bu_id": "software", "investment_ratio": 0.0, "capex_allocated": 1},
        ]
        result = process_tick(SEED_GLOBAL, SEED_BUS, decisions)
        assert "macro_noise" in result["events"]
        assert "inflation_noise" in result["events"]["macro_noise"]


# ═════════════════════════════════════════════════════════════════
#  FEATURE 25: Turnaround Pathway
# ═════════════════════════════════════════════════════════════════

class TestTurnaroundPathway:
    def test_no_distress_healthy_company(self):
        result = detect_distress(50_000_000, 60, round_number=5)
        assert result["distress_detected"] is False
        assert result["survival_mode"] is False

    def test_too_early_for_distress(self):
        """Distress detection disabled before Round 3."""
        result = detect_distress(-5_000_000, 20, round_number=2)
        assert result["distress_detected"] is False

    def test_distress_triggers_bailout(self):
        """Treasury ≤ 0 AND reputation < 30 triggers Phase 1 (Crisis) bailout."""
        result = detect_distress(-5_000_000, 25, round_number=5)
        assert result["distress_detected"] is True
        assert result["survival_mode"] is True
        assert result["bailout_amount"] == 3_000_000  # 3-act: reduced from 5M
        assert result["mr_cap"] == 0.60  # Crisis phase cap
        assert result["turnaround_phase"] == "crisis"

    def test_only_treasury_not_enough(self):
        """Negative treasury alone doesn't trigger — need low reputation too."""
        result = detect_distress(-5_000_000, 60, round_number=5)
        assert result["distress_detected"] is False

    def test_crisis_to_stabilisation(self):
        """Team progresses from Crisis to Stabilisation when treasury > 0 and rep > 20."""
        result = detect_distress(1_000_000, 25, round_number=6,
                                 already_in_survival=True, current_phase="crisis")
        assert result["survival_mode"] is True
        assert result["turnaround_phase"] == "stabilisation"
        assert result.get("phase_transition") is True

    def test_stabilisation_to_recovery(self):
        """Team progresses from Stabilisation to Recovery."""
        result = detect_distress(15_000_000, 50, round_number=7,
                                 already_in_survival=True, current_phase="stabilisation")
        assert result["turnaround_phase"] == "recovery"
        assert result.get("phase_transition") is True

    def test_recovery_to_exit(self):
        """Team fully exits turnaround arc with treasury > $20M and rep > 55."""
        result = detect_distress(25_000_000, 60, round_number=8,
                                 already_in_survival=True, current_phase="recovery")
        assert result["survival_mode"] is False
        assert result["recovered"] is True
        assert result["turnaround_phase"] == "exit"
        assert result.get("mr_bonus", 0) == 0.10

    def test_still_in_crisis(self):
        """Team stays in Crisis if conditions not met."""
        result = detect_distress(-2_000_000, 15, round_number=6,
                                 already_in_survival=True, current_phase="crisis")
        assert result["survival_mode"] is True
        assert result["turnaround_phase"] == "crisis"

    def test_turnaround_archetype(self):
        """Survival mode forces Turnaround Manager archetype."""
        result = determine_archetype(1.5, survival_mode=True)
        assert result["key"] == "turnaround_manager"
        assert result["mr_capped"] is True

    def test_normal_archetype_without_survival(self):
        """Without survival mode, normal archetypes apply."""
        result = determine_archetype(1.5, survival_mode=False)
        assert result["key"] == "derisked_safe_haven"

    def test_distress_in_tick(self):
        """Distress detection should appear in tick events."""
        decisions = [
            {"bu_id": "pharma", "investment_ratio": 0.0, "capex_allocated": 1},
            {"bu_id": "electronics", "investment_ratio": 0.0, "capex_allocated": 1},
            {"bu_id": "consumer_goods", "investment_ratio": 0.0, "capex_allocated": 1},
            {"bu_id": "software", "investment_ratio": 0.0, "capex_allocated": 1},
        ]
        result = process_tick(SEED_GLOBAL, SEED_BUS, decisions)
        assert "distress_detection" in result["events"]


# ═════════════════════════════════════════════════════════════════
#  FEATURE 26: Predictive Forecast
# ═════════════════════════════════════════════════════════════════

class TestPredictiveForecast:
    def test_forecast_structure(self):
        result = calc_forecast(SEED_GLOBAL, SEED_BUS)
        assert "treasury_velocity" in result
        assert "contagion_risk_index" in result
        assert "contagion_risk_label" in result
        assert "rounds_to_insolvency" in result
        assert "ncd_acceleration" in result

    def test_positive_treasury_no_insolvency(self):
        """Healthy company has no insolvency warning."""
        result = calc_forecast(SEED_GLOBAL, SEED_BUS)
        assert result["treasury_trend"] == "improving"
        assert result["insolvency_warning"] is False

    def test_contagion_risk_bounded(self):
        """Contagion risk index must be 0-100."""
        result = calc_forecast(SEED_GLOBAL, SEED_BUS)
        assert 0 <= result["contagion_risk_index"] <= 100

    def test_forecast_in_tick(self):
        """Forecast should appear in tick events."""
        decisions = [
            {"bu_id": "pharma", "investment_ratio": 0.0, "capex_allocated": 1},
            {"bu_id": "electronics", "investment_ratio": 0.0, "capex_allocated": 1},
            {"bu_id": "consumer_goods", "investment_ratio": 0.0, "capex_allocated": 1},
            {"bu_id": "software", "investment_ratio": 0.0, "capex_allocated": 1},
        ]
        result = process_tick(SEED_GLOBAL, SEED_BUS, decisions)
        assert "forecast" in result["events"]
        forecast = result["events"]["forecast"]
        assert "contagion_risk_index" in forecast
        assert "treasury_velocity" in forecast


# ═════════════════════════════════════════════════════════════════
#  FEATURE 27: SDG Impact Report
# ═════════════════════════════════════════════════════════════════

class TestSDGImpact:
    def test_sdg_covers_all_17_goals(self):
        result = calc_sdg_impact(SEED_BUS, {})
        assert len(result["sdg_scores"]) == 17
        for i in range(1, 18):
            assert i in result["sdg_scores"]

    def test_sdg_index_bounded(self):
        result = calc_sdg_impact(SEED_BUS, {})
        assert 0 <= result["sdg_index"] <= 100

    def test_sdg_grade_exists(self):
        result = calc_sdg_impact(SEED_BUS, {})
        assert result["sdg_grade"] in ("A+", "A", "B", "C", "D", "F")

    def test_flag_bonuses_applied(self):
        result = calc_sdg_impact(SEED_BUS, {"community_fund": True, "ethical_ai_overhaul": True})
        assert len(result["bonus_sdgs"]) >= 2

    def test_sdg_status_classification(self):
        result = calc_sdg_impact(SEED_BUS, {})
        total = result["total_sdgs_on_track"] + result["total_sdgs_at_risk"] + result["total_sdgs_off_track"]
        assert total == 17

    def test_sdg_in_tick(self):
        """SDG impact should appear in tick events."""
        decisions = [
            {"bu_id": "pharma", "investment_ratio": 0.0, "capex_allocated": 1},
            {"bu_id": "electronics", "investment_ratio": 0.0, "capex_allocated": 1},
            {"bu_id": "consumer_goods", "investment_ratio": 0.0, "capex_allocated": 1},
            {"bu_id": "software", "investment_ratio": 0.0, "capex_allocated": 1},
        ]
        result = process_tick(SEED_GLOBAL, SEED_BUS, decisions)
        assert "sdg_impact" in result["events"]
        assert "sdg_scores" in result["events"]["sdg_impact"]
        assert "sdg_index" in result["events"]["sdg_impact"]


# ═════════════════════════════════════════════════════════════════
#  FEATURE 28: Shared Marketplace
# ═════════════════════════════════════════════════════════════════

class TestSharedMarketplace:
    def setup_method(self):
        """Reset marketplace state before each test."""
        _shared_marketplace["carbon_credit_pool"]["purchased"] = {}
        _shared_marketplace["carbon_credit_pool"]["price_history"] = [50_000]
        _shared_marketplace["green_talent_pool"]["hired"] = {}
        _shared_marketplace["green_talent_pool"]["cost_history"] = [200_000]

    def test_marketplace_state_structure(self):
        state = get_marketplace_state()
        assert "carbon_credits" in state
        assert "green_talent" in state
        assert state["carbon_credits"]["remaining"] == 500
        assert state["green_talent"]["remaining"] == 100

    def test_purchase_carbon_credits_success(self):
        result = purchase_carbon_credits("team_1", 10)
        assert result["success"] is True
        assert result["quantity"] == 10
        assert result["remaining_in_pool"] == 490
        assert result["total_cost"] > 0

    def test_purchase_carbon_credits_exceeds_pool(self):
        result = purchase_carbon_credits("team_1", 501)
        assert result["success"] is False
        assert "remaining" in result

    def test_purchase_carbon_credits_invalid_quantity(self):
        result = purchase_carbon_credits("team_1", 0)
        assert result["success"] is False

    def test_scarcity_pricing(self):
        """Prices should increase as more credits are purchased."""
        r1 = purchase_carbon_credits("team_1", 50)
        r2 = purchase_carbon_credits("team_2", 50)
        # Team 2 pays more per unit due to scarcity
        assert r2["unit_price"] > r1["unit_price"]

    def test_hire_green_talent_success(self):
        result = hire_green_talent("team_1", 5)
        assert result["success"] is True
        assert result["quantity"] == 5
        assert result["remaining_in_pool"] == 95

    def test_hire_green_talent_exceeds_pool(self):
        result = hire_green_talent("team_1", 101)
        assert result["success"] is False

    def test_marketplace_cross_team_visibility(self):
        """One team's purchases should be visible to others via state."""
        purchase_carbon_credits("team_A", 20)
        state = get_marketplace_state()
        assert state["carbon_credits"]["remaining"] == 480
        assert state["carbon_credits"]["purchases_by_team"]["team_A"] == 20

    def test_talent_scarcity_pricing(self):
        """Green talent cost should increase with hires."""
        r1 = hire_green_talent("team_1", 10)
        r2 = hire_green_talent("team_2", 10)
        assert r2["unit_cost"] > r1["unit_cost"]
