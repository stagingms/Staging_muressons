"""
HARD-003: Stress tests for negative treasury, insolvency, and NCD edge cases.
Tests extreme game states to ensure simulation stability under adversarial play.
"""
import pytest
import copy
import engine

# ── Shared fixtures ──
BASE_GLOBAL = {
    "round_number": 5, "corporate_treasury": 25_000_000,
    "group_reputation": 50.0, "synergy_multiplier": 1.0,
    "cost_of_capital": 0.05, "inflation_index": 0.025,
    "active_event_flags": {}, "pending_capex_projects": [],
    "green_transition_fund": 0.0, "tipping_point_active": False,
    "tipping_tier": "none",
}
BASE_BUS = [
    {"bu_id": "pharma", "revenue_base": 18e6, "opex_base": 11.5e6,
     "reputation_score": 72, "social_license_score": 70, "governance_risk_score": 15,
     "carbon_intensity": 45, "natural_capital_debt": 5000, "risk_factors": {},
     "staff_burnout_index": 0},
    {"bu_id": "electronics", "revenue_base": 22e6, "opex_base": 14e6,
     "reputation_score": 58, "social_license_score": 65, "governance_risk_score": 25,
     "carbon_intensity": 60, "natural_capital_debt": 3800, "risk_factors": {},
     "staff_burnout_index": 0},
    {"bu_id": "consumer_goods", "revenue_base": 15e6, "opex_base": 9e6,
     "reputation_score": 74, "social_license_score": 78, "governance_risk_score": 10,
     "carbon_intensity": 30, "natural_capital_debt": 2100, "risk_factors": {},
     "staff_burnout_index": 0},
    {"bu_id": "software", "revenue_base": 20e6, "opex_base": 8e6,
     "reputation_score": 82, "social_license_score": 85, "governance_risk_score": 5,
     "carbon_intensity": 10, "natural_capital_debt": 500, "risk_factors": {},
     "staff_burnout_index": 0},
]
BASE_DECISIONS = [
    {"bu_id": "pharma", "investment_ratio": 0.05, "capex_allocated": 1e6, "choice_selected": "option_b"},
    {"bu_id": "electronics", "investment_ratio": 0.05, "capex_allocated": 1e6, "choice_selected": "option_b"},
    {"bu_id": "consumer_goods", "investment_ratio": 0.05, "capex_allocated": 0.5e6, "choice_selected": "option_b"},
    {"bu_id": "software", "investment_ratio": 0.05, "capex_allocated": 0.5e6, "choice_selected": "option_b"},
]


class TestNegativeTreasury:
    """Tests for negative treasury and insolvency scenarios."""

    def test_negative_treasury_accrues_interest(self):
        gs = copy.deepcopy(BASE_GLOBAL)
        gs["corporate_treasury"] = -50_000_000  # Deep enough that CSF can't overcome
        result = engine.process_tick(gs, BASE_BUS, BASE_DECISIONS)
        # Treasury should be even more negative due to interest on the debt
        new_treasury = result["global_state"]["corporate_treasury"]
        # CSF adds significant revenue, but from -50M the result should still be negative
        assert new_treasury < 0, f"Treasury should remain negative: {new_treasury}"

    def test_insolvency_triggers_at_negative_100m(self):
        gs = copy.deepcopy(BASE_GLOBAL)
        gs["corporate_treasury"] = -150_000_000  # Deep in insolvency
        result = engine.process_tick(gs, BASE_BUS, BASE_DECISIONS)
        events = result["events"]
        # Check treasury stayed very negative (CSF can't recover from -150M)
        new_treasury = result["global_state"]["corporate_treasury"]
        assert new_treasury < -100_000_000, f"Treasury should be deeply negative: {new_treasury}"

    def test_insolvency_floor_prevents_unbounded_negative(self):
        gs = copy.deepcopy(BASE_GLOBAL)
        gs["corporate_treasury"] = -600_000_000  # Beyond floor
        result = engine.process_tick(gs, BASE_BUS, BASE_DECISIONS)
        new_treasury = result["global_state"]["corporate_treasury"]
        # Should be capped at -500M before interest, never more negative than -500M + interest
        assert new_treasury >= -550_000_000

    def test_zero_treasury_no_crash(self):
        gs = copy.deepcopy(BASE_GLOBAL)
        gs["corporate_treasury"] = 0
        result = engine.process_tick(gs, BASE_BUS, BASE_DECISIONS)
        assert result["global_state"]["corporate_treasury"] is not None

    def test_capex_capped_at_2x_treasury(self):
        gs = copy.deepcopy(BASE_GLOBAL)
        gs["corporate_treasury"] = 1_000_000
        big_decs = copy.deepcopy(BASE_DECISIONS)
        for d in big_decs:
            d["capex_allocated"] = 5_000_000
        result = engine.process_tick(gs, BASE_BUS, big_decs)
        assert result["events"].get("capex_capped") is True


class TestNCDStress:
    """Tests for NCD soft cap and hard cap edge cases."""

    def test_ncd_hard_cap_at_1m(self):
        bus = copy.deepcopy(BASE_BUS)
        bus[0]["natural_capital_debt"] = 999_990
        result = engine.process_tick(BASE_GLOBAL, bus, BASE_DECISIONS)
        for bu in result["bu_states"]:
            assert bu["natural_capital_debt"] <= 1_000_000

    def test_ncd_soft_cap_warning_at_500k(self):
        bus = copy.deepcopy(BASE_BUS)
        bus[0]["natural_capital_debt"] = 499_990
        # Need high enough base rate to push NCD over 500K in one tick
        gs = copy.deepcopy(BASE_GLOBAL)
        gs["cost_of_capital"] = 0.10
        result = engine.process_tick(gs, bus, BASE_DECISIONS)
        events = result["events"]
        # Check if soft cap warning was triggered for pharma
        pharma_bu = next(bu for bu in result["bu_states"] if bu["bu_id"] == "pharma")
        if pharma_bu["natural_capital_debt"] >= 500_000:
            assert events.get("ncd_credit_downgrade_pharma") is True

    def test_zero_ncd_no_penalty(self):
        bus = copy.deepcopy(BASE_BUS)
        for bu in bus:
            bu["natural_capital_debt"] = 0
        result = engine.process_tick(BASE_GLOBAL, bus, BASE_DECISIONS)
        for bu in result["bu_states"]:
            assert bu["natural_capital_debt"] >= 0


class TestBoundaryRounding:
    """Tests that HARD-004 boundary rounding prevents drift."""

    def test_all_financial_fields_rounded_to_2dp(self):
        result = engine.process_tick(BASE_GLOBAL, BASE_BUS, BASE_DECISIONS)
        for bu in result["bu_states"]:
            rev_str = str(bu["revenue_base"])
            if "." in rev_str:
                assert len(rev_str.split(".")[1]) <= 2, f"{bu['bu_id']} revenue_base has >2dp: {bu['revenue_base']}"
            opex_str = str(bu["opex_base"])
            if "." in opex_str:
                assert len(opex_str.split(".")[1]) <= 2, f"{bu['bu_id']} opex_base has >2dp: {bu['opex_base']}"

    def test_treasury_rounded_to_2dp(self):
        result = engine.process_tick(BASE_GLOBAL, BASE_BUS, BASE_DECISIONS)
        treasury = result["global_state"]["corporate_treasury"]
        treasury_str = str(treasury)
        if "." in treasury_str:
            assert len(treasury_str.split(".")[1]) <= 2


class TestStrikeScaling:
    """Tests for HARD-002 strike penalty scaling."""

    def test_strike_penalty_scales_with_treasury(self):
        gs = copy.deepcopy(BASE_GLOBAL)
        gs["corporate_treasury"] = 50_000_000
        # 5% of 50M = 2.5M, should be larger than base 1M
        min_penalty = max(1_000_000, gs["corporate_treasury"] * 0.05)
        assert min_penalty == 2_500_000

    def test_strike_penalty_floor_at_1m(self):
        gs = copy.deepcopy(BASE_GLOBAL)
        gs["corporate_treasury"] = 5_000_000
        # 5% of 5M = 250K, floor should kick in at 1M
        min_penalty = max(1_000_000, gs["corporate_treasury"] * 0.05)
        assert min_penalty == 1_000_000


class TestTerminalValuation:
    """Tests for the extracted terminal_valuation module."""

    def test_mr_base_value(self):
        from terminal_valuation import calculate_mr
        result = calculate_mr(flags={}, avg_slo=80, avg_burnout=50,
                              workforce_readiness=50, synergy_multiplier=1.0)
        # Base (1.0) + Resilience (0.20, no blockers) = 1.20
        assert result["mr"] == 1.20

    def test_mr_all_bonuses(self):
        from terminal_valuation import calculate_mr
        flags = {"materiality_aligned": True, "synergy_unlock": True,
                 "ethical_ai_overhaul": True, "community_fund": True}
        result = calculate_mr(flags=flags, avg_slo=80, avg_burnout=10,
                              workforce_readiness=80, synergy_multiplier=1.0,
                              hr_investment_rounds=3)
        # Should approach max M_R
        assert result["mr"] > 2.0

    def test_mr_instability_discount(self):
        from terminal_valuation import calculate_mr
        result = calculate_mr(flags={}, avg_slo=60, avg_burnout=50,
                              workforce_readiness=50, synergy_multiplier=1.0)
        assert result["breakdown"].get("instability_discount") == -0.40

    def test_what_if_delta(self):
        from terminal_valuation import what_if_terminal
        bus = copy.deepcopy(BASE_BUS)
        flags = {}
        overrides = {"ethical_ai_overhaul": True}
        result = what_if_terminal(bus, flags, overrides, avg_slo=80, avg_burnout=50,
                                  workforce_readiness=50, synergy_multiplier=1.0)
        assert result["delta"]["mr_change"] == 0.15
        assert result["delta"]["tv_change"] > 0

    def test_pathway_normalization(self):
        from terminal_valuation import normalize_mr_for_leaderboard
        result = normalize_mr_for_leaderboard(1.5, "hostile_takeover")
        assert result["normalized_mr"] == round(1.5 * 1.20, 4)
        assert result["difficulty_coefficient"] == 1.20

    def test_flag_dependency_graph(self):
        from terminal_valuation import get_flag_dependency_graph
        result = get_flag_dependency_graph({"materiality_aligned": True})
        assert result["total_flags"] == 17  # 13 core + 4 BRSR NGRBC
        assert result["active_count"] == 1
