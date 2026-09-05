"""
Unit tests for round_logic.py and round_configs.py
Tests the round-specific pre_tick / post_tick state mutations.
"""

import sys
import os
import random

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from round_configs import get_round_config, get_round_options, get_round_crisis, ROUND_CONFIGS
from round_logic import pre_tick, post_tick, _get_primary_choice


# ── Fixtures ──────────────────────────────────────────────────────

def make_global(round_number=1, treasury=50_000_000, reputation=50,
                synergy=1.0, flags=None):
    return {
        "round_number": round_number,
        "corporate_treasury": treasury,
        "group_reputation": reputation,
        "synergy_multiplier": synergy,
        "cost_of_capital": 0.05,
        "active_event_flags": flags or {},
    }


def make_bus():
    return [
        {"bu_id": "pharma", "revenue_base": 18_000_000, "opex_base": 11_500_000,
         "natural_capital_debt": 0, "social_license_score": 55, "reputation_score": 52,
         "governance_risk_score": 15, "water_dependency": 82, "carbon_intensity": 45,
         "risk_factors": {}},
        {"bu_id": "electronics", "revenue_base": 16_500_000, "opex_base": 10_800_000,
         "natural_capital_debt": 0, "social_license_score": 48, "reputation_score": 50,
         "governance_risk_score": 20, "water_dependency": 58, "carbon_intensity": 72,
         "risk_factors": {}},
        {"bu_id": "consumer_goods", "revenue_base": 10_500_000, "opex_base": 7_800_000,
         "natural_capital_debt": 0, "social_license_score": 52, "reputation_score": 53,
         "governance_risk_score": 10, "water_dependency": 65, "carbon_intensity": 38,
         "risk_factors": {}},
        {"bu_id": "software", "revenue_base": 8_500_000, "opex_base": 4_200_000,
         "natural_capital_debt": 0, "social_license_score": 60, "reputation_score": 58,
         "governance_risk_score": 8, "water_dependency": 12, "carbon_intensity": 28,
         "risk_factors": {}},
    ]


def make_decisions(choice="option_a"):
    return [
        {"bu_id": "pharma", "investment_ratio": 0.25, "capex_allocated": 1_000_000,
         "choice_selected": choice, "decision_node_id": "pharma_water_invest",
         "time_to_decision_seconds": 10, "team_consensus": "majority"},
        {"bu_id": "electronics", "investment_ratio": 0.25, "capex_allocated": 1_000_000,
         "choice_selected": choice, "decision_node_id": "electronics_supply_chain",
         "time_to_decision_seconds": 10, "team_consensus": "majority"},
        {"bu_id": "consumer_goods", "investment_ratio": 0.25, "capex_allocated": 1_000_000,
         "choice_selected": choice, "decision_node_id": "consumer_goods_packaging",
         "time_to_decision_seconds": 10, "team_consensus": "majority"},
        {"bu_id": "software", "investment_ratio": 0.25, "capex_allocated": 1_000_000,
         "choice_selected": choice, "decision_node_id": "software_data_privacy",
         "time_to_decision_seconds": 10, "team_consensus": "majority"},
    ]


# ═════════════════════════════════════════════════════════════════
#  ROUND CONFIGS TESTS
# ═════════════════════════════════════════════════════════════════

class TestRoundConfigs:
    def test_all_10_rounds_defined(self):
        for r in range(1, 11):
            cfg = get_round_config(r)
            assert cfg is not None, f"Round {r} config missing"
            assert "title" in cfg
            assert "options" in cfg
            assert len(cfg["options"]) == 3

    def test_noise_within_bounds(self):
        """Inflation noise must be within ±0.4% (6-month period)."""
        from engine import calc_macro_noise
        for _ in range(100):
            result = calc_macro_noise(5)
            assert -0.004 <= result["inflation_noise"] <= 0.004
            assert -0.07 <= result["carbon_price_noise_pct"] <= 0.07

    def test_each_round_has_crisis(self):
        for r in range(1, 11):
            crisis = get_round_crisis(r)
            assert crisis is not None, f"Round {r} has no crisis"
            assert "id" in crisis
            assert "title" in crisis
            assert "description" in crisis

    def test_options_have_required_fields(self):
        for r in range(1, 11):
            opts = get_round_options(r)
            for key, opt in opts.items():
                assert "label" in opt, f"R{r} {key} missing label"
                assert "title" in opt, f"R{r} {key} missing title"
                assert "description" in opt, f"R{r} {key} missing description"

    def test_invalid_round(self):
        assert get_round_config(0) is None
        assert get_round_config(11) is None


# ═════════════════════════════════════════════════════════════════
#  PRE-TICK TESTS
# ═════════════════════════════════════════════════════════════════

class TestPreTick:
    def test_r2_cfo_gate_blocks_bad_node(self):
        """Round 2 should reject allocations to non-materiality nodes."""
        gs = make_global(round_number=2)
        bus = make_bus()
        decs = make_decisions("option_a")
        # Tamper one decision to have a non-approved node
        decs[0]["decision_node_id"] = "pharma_office_party"

        result = pre_tick(2, gs, bus, decs, crisis_severity=0)
        assert "validation_error" in result
        assert "CFO Override" in result["validation_error"]

    def test_r2_cfo_gate_allows_good_nodes(self):
        """Round 2 should allow allocations to high-impact nodes."""
        gs = make_global(round_number=2)
        bus = make_bus()
        decs = make_decisions("option_a")
        # Use the actual approved materiality node IDs
        decs[0]["decision_node_id"] = "round_2_pharma"
        decs[1]["decision_node_id"] = "round_2_electronics"
        decs[2]["decision_node_id"] = "round_2_consumer_goods"
        decs[3]["decision_node_id"] = "round_2_software"

        result = pre_tick(2, gs, bus, decs, crisis_severity=0)
        assert "validation_error" not in result

    def test_r4_blindspot_doubles_crisis(self):
        """Round 4 with electronics_blindspot flag should double crisis."""
        gs = make_global(round_number=4, flags={"electronics_blindspot": True})
        bus = make_bus()
        decs = make_decisions()

        result = pre_tick(4, gs, bus, decs, crisis_severity=20)
        assert result["crisis_severity"] == 80  # base 40 * 2
        assert result["pre_events"]["electronics_blindspot_triggered"] is True

    def test_r4_deep_audit_normal_crisis(self):
        """Round 4 with deep_audit_completed should NOT double crisis."""
        gs = make_global(round_number=4, flags={"deep_audit_completed": True})
        bus = make_bus()
        decs = make_decisions()

        result = pre_tick(4, gs, bus, decs, crisis_severity=20)
        assert result["crisis_severity"] == 40  # base severity, not doubled
        assert result["pre_events"]["deep_audit_protected"] is True

    def test_no_pre_hook_passthrough(self):
        """Rounds without pre hooks should pass through crisis severity."""
        gs = make_global(round_number=1)
        bus = make_bus()
        decs = make_decisions()

        result = pre_tick(1, gs, bus, decs, crisis_severity=25)
        assert result["crisis_severity"] == 25  # unchanged


# ═════════════════════════════════════════════════════════════════
#  POST-TICK TESTS
# ═════════════════════════════════════════════════════════════════

class TestPostTick:
    def test_r1_option_a_sets_blindspot_flag(self):
        """Round 1 Option A should set electronics_blindspot flag."""
        gs = make_global(round_number=2, treasury=50_000_000, reputation=50)
        gs["active_event_flags"] = {}
        bus = make_bus()
        decs = make_decisions("option_a")

        extra = post_tick(1, gs, bus, decs, {}, {})
        assert "flags_set_r1" in extra
        assert "electronics_blindspot" in extra["flags_set_r1"]

    def test_r1_option_b_sets_deep_audit(self):
        """Round 1 Option B should set deep_audit_completed and cost treasury."""
        gs = make_global(round_number=2, treasury=50_000_000)
        gs["active_event_flags"] = {}
        bus = make_bus()
        decs = make_decisions("option_b")

        extra = post_tick(1, gs, bus, decs, {}, {})
        assert "flags_set_r1" in extra
        assert "deep_audit_completed" in extra["flags_set_r1"]
        assert gs["corporate_treasury"] == 50_000_000 - 3_000_000

    def test_r3_option_a_supply_chain_disruption(self):
        """R3 Option A should increase governance risk for pharma/electronics."""
        gs = make_global(round_number=4, treasury=50_000_000)
        gs["active_event_flags"] = {}
        bus = make_bus()
        decs = make_decisions("option_a")

        extra = post_tick(3, gs, bus, decs, {}, {})
        assert extra.get("supply_chain_disruption_applied") is True
        pharma = next(b for b in bus if b["bu_id"] == "pharma")
        assert pharma["governance_risk_score"] == 22  # 15 + 10 (disruption) - 3 (option governance_risk_delta)

    def test_r3_option_b_lowers_ncd(self):
        """R3 Option B should reduce Natural Capital Debt."""
        gs = make_global(round_number=4, treasury=50_000_000)
        gs["active_event_flags"] = {}
        bus = make_bus()
        for bu in bus:
            bu["natural_capital_debt"] = 20
        decs = make_decisions("option_b")

        extra = post_tick(3, gs, bus, decs, {}, {})
        # FLAG-10.3 (audit 2026-09-04, WP-24): "over 3 rounds" — 5 now, 5 at
        # the R4 tick, 5 at the R5 tick (ncd_drop projects), 15 in total.
        for bu in bus:
            assert bu["natural_capital_debt"] == 15  # 20 - 5
        drops = [p for p in gs["pending_capex_projects"] if p["type"] == "ncd_drop"]
        assert sorted(p["rounds_remaining"] for p in drops) == [1, 2]
        assert sum(p["amount"] for p in drops) == -10

    def test_r5_stochastic_event_with_hard_engineering(self):
        """R5 with roll < 0.75 should apply full damage because R5 resilience is delayed."""
        random.seed(42)  # seed for reproducible roll
        gs = make_global(round_number=6, treasury=50_000_000)
        gs["active_event_flags"] = {}
        bus = make_bus()
        decs = make_decisions("option_a")  # Creates pending resilience

        extra = post_tick(5, gs, bus, decs, {}, {})
        assert "stochastic_roll" in extra
        # The cyclone hits before the infrastructure is built (Delayed CapEx)
        if extra.get("climate_event_struck"):
            assert extra["actual_damage"] == 12_000_000.0

    def test_r5_hard_engineering_adds_ncd(self):
        """R5 Option A should queue a pending project for +10 Natural Capital Debt."""
        random.seed(100)
        gs = make_global(round_number=6, treasury=50_000_000)
        gs["active_event_flags"] = {}
        bus = make_bus()
        decs = make_decisions("option_a")

        post_tick(5, gs, bus, decs, {}, {})
        # Impacts shouldn't apply immediately
        for bu in bus:
            assert bu["natural_capital_debt"] == 0
        
        # Determine it queued successfully
        assert "pending_capex_projects" in gs
        has_ncd = any(p["type"] == "ncd_drop" for p in gs["pending_capex_projects"])
        assert has_ncd is True

    def test_r6_option_a_revenue_boost_rep_drop(self):
        """R6 Option A: +$10M software revenue, -20 reputation."""
        gs = make_global(round_number=7, treasury=50_000_000, reputation=60)
        gs["active_event_flags"] = {}
        bus = make_bus()
        decs = make_decisions("option_a")

        extra = post_tick(6, gs, bus, decs, {}, {})
        sw = next(b for b in bus if b["bu_id"] == "software")
        assert sw["revenue_base"] == 8_500_000 + 10_000_000
        # 60 - 20 (base) = 40, then the C-3 social-media velocity amplifier
        # (R6 multiplier 1.3x, rep < 60): -(60-40)*0.1*0.3 = -0.6 -> 39.4,
        # then -10 (contagion spike, generic applier) -> 29.4.
        assert gs["group_reputation"] == 29.4
        assert extra.get("contagion_spike_triggered") is True

    def test_r6_option_b_social_license_boost(self):
        """R6 Option B: -$8M treasury, +15 social licence."""
        gs = make_global(round_number=7, treasury=50_000_000)
        gs["active_event_flags"] = {}
        bus = make_bus()
        decs = make_decisions("option_b")

        post_tick(6, gs, bus, decs, {}, {})
        assert gs["corporate_treasury"] == 50_000_000 - 8_000_000
        for bu in bus:
            assert bu["social_license_score"] >= 60  # all boosted by +15

    def test_r7_option_c_unlocks_synergy(self):
        """R7 Option C should boost synergy multiplier by 0.30 (Fix #4: harmonised to M_R)."""
        gs = make_global(round_number=8, synergy=1.0, treasury=50_000_000)
        gs["active_event_flags"] = {}
        bus = make_bus()
        decs = make_decisions("option_c")

        extra = post_tick(7, gs, bus, decs, {}, {})
        assert gs["synergy_multiplier"] == 1.30  # Fix #4: was 1.35 (boost now 0.30 not 0.35)
        assert extra.get("synergy_multiplier_unlocked") is True

    def test_r8_option_b_severe_social_drop(self):
        """R8 Option B drops social license severely for pharma/consumer_goods when
        electronics_water_priority flag is explicitly in the round's pillar choices."""
        gs = make_global(round_number=9, treasury=50_000_000)
        gs["active_event_flags"] = {}
        bus = make_bus()
        decs = make_decisions("option_b")
        # Fix #8: Pass electronics_water_priority flag so the guard condition fires
        events_with_flag = {"pillar_flags": ["electronics_water_priority"]}

        post_tick(8, gs, bus, decs, events_with_flag, {})
        pharma = next(b for b in bus if b["bu_id"] == "pharma")
        cg = next(b for b in bus if b["bu_id"] == "consumer_goods")
        assert pharma["social_license_score"] == 30  # 55 - 25
        assert cg["social_license_score"] == 27  # 52 - 25

    def test_r8_option_c_desalination_cost_and_ncd(self):
        """R8 Option C: -$30M treasury, queues Delayed-Yield CapEx for NCD reduction."""
        gs = make_global(round_number=9, treasury=50_000_000)
        gs["active_event_flags"] = {}
        bus = make_bus()
        for bu in bus:
            bu["natural_capital_debt"] = 40
        decs = make_decisions("option_c")

        post_tick(8, gs, bus, decs, {}, {})
        assert gs["corporate_treasury"] == 20_000_000  # 50M - 30M
        
        # NCD shouldn't drop immediately due to Delayed-Yield CapEx queue
        for bu in bus:
            assert bu["natural_capital_debt"] == 40
            
        assert "pending_capex_projects" in gs
        has_water = any(p["type"] == "ncd_drop" for p in gs["pending_capex_projects"])
        assert has_water is True

    def test_r9_option_a_strike_with_low_sl(self):
        """R9 Option A with low social licence should potentially trigger strike."""
        random.seed(1)  # seed for reproducible roll
        gs = make_global(round_number=10, treasury=50_000_000, reputation=50)
        gs["active_event_flags"] = {}
        bus = make_bus()
        for bu in bus:
            bu["social_license_score"] = 30  # low SL
        decs = make_decisions("option_a")

        extra = post_tick(9, gs, bus, decs, {}, {})
        assert "regulatory_friction" in extra
        assert extra["regulatory_friction"] > 0
        # With low SL, strike should have been evaluated
        assert "strike_roll" in extra

    def test_r9_regulatory_friction_calc(self):
        """R9 Regulatory Friction = 1 / avg_SL (after SL delta applied)."""
        gs = make_global(round_number=10, treasury=50_000_000)
        gs["active_event_flags"] = {}
        bus = make_bus()
        # avg SL = 40, but Option A applies -20 delta → avg = 20
        for bu in bus:
            bu["social_license_score"] = 40
        decs = make_decisions("option_a")

        extra = post_tick(9, gs, bus, decs, {}, {})
        # After -20 delta: avg_SL = 20, friction = 1/20 = 0.05
        assert extra["regulatory_friction"] == round(1.0 / 20, 4)

    def test_r10_ebitda_and_terminal_value(self):
        """R10: verify Terminal_EBITDA = Σ(Rev-OPEX) - CarbonTonnage×$250."""
        gs = make_global(round_number=11, treasury=50_000_000, reputation=60, synergy=1.2)
        gs["active_event_flags"] = {}
        bus = make_bus()
        decs = make_decisions("option_b")  # Spin-off

        extra = post_tick(10, gs, bus, decs, {}, {})

        assert "terminal_ebitda" in extra
        assert "terminal_value" in extra
        assert "regenerative_multiple" in extra
        assert "profile" in extra
        assert "profile_title" in extra

        # Verify EBITDA formula
        total_rev = sum(b["revenue_base"] for b in bus)
        total_opex = sum(b["opex_base"] for b in bus)
        carbon_tonnage = sum(b.get("carbon_intensity", 0) for b in bus)
        # Note: spinoff zeros the weakest BU, so we need to check after mutation
        assert extra["carbon_tax_per_ton"] == 250
        assert extra["terminal_ebitda"] is not None

    def test_r10_regenerative_multiple_all_bonuses(self):
        """R10: MR structure with all bonuses via community_fund path.
        community_fund (+0.18) > managed_transition (+0.12) — budget arbitrage eliminated.
        Bonus path: base(1.0) + synergy(+0.15) + resilience(+0.2) + truth(+0.15)
                    + community_champion(+0.18) + burnout_wellbeing(+0.05) = 1.73."""
        gs = make_global(round_number=11, treasury=50_000_000, reputation=60, synergy=1.2)
        gs["active_event_flags"] = {}
        bus = make_bus()
        # Set high SL to avoid instability discount. DEEP-2 (single arbiter):
        # the discount is now a GAME-2 ramp (0 at SLO>=80, full at <=70), and
        # R10 option_b applies its own -5 SLO in-handler — start at 86 so the
        # closing average (81) sits cleanly above the ramp band.
        for bu in bus:
            bu["social_license_score"] = 86
            # burnout_index not set → defaults to 0.0 → wellbeing bonus active
        decs = make_decisions("option_b")

        prev_flags = {
            "synergy_unlock": True,          # R7 synergy → +0.15
            "ethical_ai_overhaul": True,     # R6 truth premium → +0.15
            "community_fund": True,          # R9 community champion → +0.18
            # No insurance_only or electronics_water_priority → +0.2
        }

        extra = post_tick(10, gs, bus, decs, {}, prev_flags)
        assert extra.get("mr_synergy_bonus") is True
        assert extra.get("mr_resilience_bonus") is True
        assert extra.get("mr_truth_premium") is True
        assert extra.get("mr_community_champion_bonus") is True  # community_fund → +0.18
        assert extra.get("mr_just_transition_bonus") is None     # managed_transition NOT set
        assert extra.get("mr_wellbeing_bonus") is True           # burnout=0 < 20 → +0.05
        assert extra.get("mr_instability_discount") is None      # SL >= 75
        # 1.0 + 0.15 + 0.2 + 0.15 + 0.18 + 0.05 = 1.73
        assert extra["regenerative_multiple"] == 1.73

    def test_r10_instability_discount(self):
        """R10: Social License < 75 applies -0.4 instability discount.
        Default bus fixture has burnout=0, so wellbeing bonus (+0.05) is active."""
        gs = make_global(round_number=11, treasury=50_000_000, reputation=60, synergy=1.2)
        gs["active_event_flags"] = {}
        bus = make_bus()
        # Default SL is ~53 avg, well below 75
        decs = make_decisions("option_b")

        extra = post_tick(10, gs, bus, decs, {}, {})
        assert extra.get("mr_instability_discount") is True
        # Base 1.0 + 0.2 (no bailout flags) + 0.05 (burnout=0) - 0.4 = 0.85
        assert extra["regenerative_multiple"] == 0.85

    def test_r10_profile_regenerative_titan(self):
        """R10: MR >= 1.8 -> 'The Regenerative Titan' (Here 1.67 -> 'The De-risked Safe-Haven' due to synergy rebalance).
        managed_transition → +0.12 (split from community_fund at +0.18).
        Wellbeing bonus (+0.05) active since default burnout=0.
        Total: 1.0+0.15+0.2+0.15+0.12+0.05 = 1.67 exactly."""
        gs = make_global(round_number=11, treasury=50_000_000, reputation=60, synergy=1.2)
        gs["active_event_flags"] = {}
        bus = make_bus()
        for bu in bus:
            bu["social_license_score"] = 90  # avoid instability discount
        decs = make_decisions("option_b")

        # synergy(+0.15) + resilience(+0.2) + truth(+0.15) + managed_transition(+0.12) + wellbeing(+0.05) = 1.67
        prev_flags = {
            "synergy_unlock": True,
            "ethical_ai_overhaul": True,
            "managed_transition": True,   # +0.12 (rebalanced)
        }
        extra = post_tick(10, gs, bus, decs, {}, prev_flags)
        assert extra["regenerative_multiple"] == 1.67
        assert extra["profile"] == "derisked_safe_haven"
        assert extra["profile_title"] == "The De-risked Safe-Haven"

    def test_r10_profile_regenerative_titan_with_workforce_bonus(self):
        """R10: All bonuses including workforce readiness → MR = 1.83.
        community_fund(+0.18) + workforce(+0.10) + wellbeing(+0.05) = peak along with synergy+resilience+truth."""
        gs = make_global(round_number=11, treasury=50_000_000, reputation=60, synergy=1.2)
        gs["active_event_flags"] = {}
        gs["workforce_readiness"] = 80.0  # Above 75 threshold for +0.10 bonus
        bus = make_bus()
        for bu in bus:
            bu["social_license_score"] = 90  # avoid instability discount
            # burnout not set → 0.0 → wellbeing bonus active
        decs = make_decisions("option_b")

        # All 6 bonuses: synergy(+0.15) + resilience(+0.2) + truth(+0.15)
        #   + community_champion(+0.18) + workforce(+0.10) + wellbeing(+0.05) = 1.83
        prev_flags = {
            "synergy_unlock": True,
            "ethical_ai_overhaul": True,
            "community_fund": True,          # +0.18 (rebalanced)
        }
        extra = post_tick(10, gs, bus, decs, {}, prev_flags)
        assert extra["regenerative_multiple"] == 1.83
        assert extra.get("mr_workforce_bonus") is True
        assert extra.get("mr_wellbeing_bonus") is True
        assert extra.get("mr_community_champion_bonus") is True
        assert extra["profile"] == "regenerative_titan"

    def test_r10_profile_pragmatic_operator(self):
        """AR-B: MR < 0.8 but SOLVENT → 'The Pragmatic Operator'.
        DMAV = treasury(+50M) x MR(0.65) - NCD(0) > 0, so the solvency gate keeps
        the earned solvent label instead of demoting to Stranded Relic (which is
        now reserved for value destruction).
        Wellbeing bonus (+0.05) active since default burnout=0."""
        gs = make_global(round_number=11, treasury=50_000_000, reputation=60, synergy=1.2)
        gs["active_event_flags"] = {}
        bus = make_bus()
        # Low social license → instability discount
        for bu in bus:
            bu["social_license_score"] = 30
        decs = make_decisions("option_b")

        # Bailout flags to remove resilience bonus
        prev_flags = {"insurance_only": True}
        extra = post_tick(10, gs, bus, decs, {}, prev_flags)
        # MR = 1.0 + 0 (no synergy) + 0 (bailout) + 0 (no truth) + 0.05 (burnout=0) - 0.4 = 0.65
        assert extra["regenerative_multiple"] == 0.65
        assert extra["profile"] == "pragmatic_operator"
        assert extra["profile_title"] == "The Pragmatic Operator"

    def test_r10_profile_stranded_relic_when_insolvent(self):
        """AR-B: MR < 0.8 AND value-destroyed (negative treasury → DMAV <= 0) →
        the solvency gate demotes the Pragmatic Operator to 'The Stranded Relic'.
        This is the honest floor; the same low-M_R strategy that stays solvent is
        a Pragmatic Operator (see test above)."""
        gs = make_global(round_number=11, treasury=-50_000_000, reputation=60, synergy=1.2)
        gs["active_event_flags"] = {}
        bus = make_bus()
        for bu in bus:
            bu["social_license_score"] = 30
        decs = make_decisions("option_b")

        prev_flags = {"insurance_only": True}
        extra = post_tick(10, gs, bus, decs, {}, prev_flags)
        assert extra["regenerative_multiple"] == 0.65
        assert extra["profile"] == "stranded_relic"
        assert extra["profile_title"] == "The Stranded Relic"

    def test_r10_option_a_synergy_gate_blocked(self):
        """R10 Option A blocked when Synergy ≤ 80 (score = multiplier×100)."""
        gs = make_global(round_number=11, treasury=50_000_000, synergy=0.5)
        gs["active_event_flags"] = {}
        bus = make_bus()
        decs = make_decisions("option_a")

        extra = post_tick(10, gs, bus, decs, {}, {})
        assert extra.get("synergy_gate_blocked") is True
        # Should fallback to option_b
        assert extra["r10_choice"] == "option_b"

    def test_r10_option_c_divest_wipes_synergy(self):
        """R10 Option C wipes synergy (0.0 — VAL-07, WP-24: a reset to 1.0
        passed the synergy gate) and adds treasury."""
        gs = make_global(round_number=11, treasury=50_000_000, synergy=1.5)
        gs["active_event_flags"] = {}
        bus = make_bus()
        decs = make_decisions("option_c")

        extra = post_tick(10, gs, bus, decs, {}, {})
        assert extra.get("synergy_wiped") is True
        assert gs["synergy_multiplier"] == 0.0
        assert gs["corporate_treasury"] == 50_000_000 + 25_000_000


# ═════════════════════════════════════════════════════════════════
#  HELPER TESTS
# ═════════════════════════════════════════════════════════════════

class TestHelpers:
    def test_get_primary_choice(self):
        decs = make_decisions("option_c")
        assert _get_primary_choice(decs) == "option_c"

    def test_get_primary_choice_default(self):
        decs = [{"bu_id": "pharma", "choice_selected": "none"}]
        assert _get_primary_choice(decs) == "option_b"  # default


# =================================================================
#  HR MECHANICS TESTS
# =================================================================

class TestHRMechanics:
    """Tests for new burnout and workforce readiness engine functions."""

    def test_burnout_accumulation_no_investment(self):
        """Burnout should drift up by +3 per round with no HR investment."""
        from engine import calc_burnout_accumulation
        new_burnout, diag = calc_burnout_accumulation(0.0, 0.0, natural_drift=3.0)
        assert new_burnout == 3.0
        assert diag["opex_penalty_active"] is False

    def test_burnout_accumulation_high_investment(self):
        """High HR investment should reduce burnout and reset drift."""
        from engine import calc_burnout_accumulation
        new_burnout, diag = calc_burnout_accumulation(30.0, -10.0, natural_drift=0.0)
        assert new_burnout == 20.0
        assert diag["opex_penalty_active"] is False

    def test_burnout_accumulation_opex_penalty_threshold(self):
        """Burnout > 20 should trigger OPEX penalty on a graded curve."""
        from engine import calc_burnout_accumulation
        new_burnout, diag = calc_burnout_accumulation(30.0, 0.0, natural_drift=3.0)
        assert new_burnout == 33.0
        assert diag["opex_penalty_active"] is True
        assert diag["opex_penalty_rate"] > 0

    def test_burnout_accumulation_critical_threshold(self):
        """Burnout > 70 should trigger critical burnout flag."""
        from engine import calc_burnout_accumulation
        new_burnout, diag = calc_burnout_accumulation(70.0, 5.0, natural_drift=3.0)
        assert new_burnout == 78.0
        assert diag["critical_burnout"] is True

    def test_burnout_clamped_to_zero(self):
        """Burnout cannot go below 0."""
        from engine import calc_burnout_accumulation
        new_burnout, _ = calc_burnout_accumulation(5.0, -20.0, natural_drift=0.0)
        assert new_burnout == 0.0

    def test_burnout_clamped_to_hundred(self):
        """Burnout cannot exceed 100."""
        from engine import calc_burnout_accumulation
        new_burnout, _ = calc_burnout_accumulation(95.0, 10.0, natural_drift=3.0)
        assert new_burnout == 100.0

    def test_workforce_readiness_high_investment(self):
        """High HR quality should increase readiness by +16."""
        from engine import calc_workforce_readiness
        new_readiness, diag = calc_workforce_readiness(50.0, True, "high")
        assert new_readiness == 66.0  # 50 + 16 (high tier delta)
        assert diag["hr_quality_tier"] == "high"


    def test_workforce_readiness_no_investment_decay(self):
        """No HR investment should decay readiness by -10."""
        from engine import calc_workforce_readiness
        new_readiness, diag = calc_workforce_readiness(50.0, False, "none")
        assert new_readiness == 40.0  # 50 - 10 (skills atrophy)
        assert diag["low_readiness_penalty"] is False  # 40 is NOT < 40

    def test_workforce_readiness_low_penalty_threshold(self):
        """Readiness < 40 should flag low_readiness_penalty."""
        from engine import calc_workforce_readiness
        new_readiness, diag = calc_workforce_readiness(35.0, False, "none")
        assert new_readiness == 25.0  # 35 - 10
        assert diag["low_readiness_penalty"] is True


    def test_workforce_readiness_high_bonus_threshold(self):
        """Readiness > 75 should flag high_readiness_bonus."""
        from engine import calc_workforce_readiness
        new_readiness, diag = calc_workforce_readiness(74.0, True, "high")
        assert new_readiness == 90.0  # 74 + 16
        assert diag["high_readiness_bonus"] is True
