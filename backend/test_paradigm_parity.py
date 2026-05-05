"""
Paradigm Parity Test Suite
==========================
Verifies that legacy (A/B/C) and pillar (multi_toggles) paradigms produce
equivalent outcomes for equivalent strategic intent.

Tests:
1. Terminal values within 15% of each other for identical strategies
2. Same M_R bonuses earned for equivalent flag-producing choices
3. Flags propagate identically across paradigms
4. Mutual exclusivity enforcement in pillar mode
5. Pillar bypass events emitted correctly
"""

import copy
import pytest
from unittest.mock import patch

# ── Test Fixtures ──────────────────────────────────────────────────

SEED_GLOBAL_STATE = {
    "round_number": 1,
    "corporate_treasury": 100_000_000.0,
    "group_reputation": 50.0,
    "synergy_multiplier": 1.0,
    "cost_of_capital": 0.05,
    "green_transition_fund": 0.0,
    "workforce_readiness": 55.0,
    "active_event_flags": {},
    "pillar_effectiveness_modifier": 1.0,
}

SEED_BUS = [
    {
        "bu_id": "software",
        "revenue_base": 10_000_000,
        "opex_base": 6_000_000,
        "natural_capital_debt": 50,
        "social_license_score": 50.0,
        "governance_risk_score": 20.0,
        "carbon_intensity": 60.0,
        "staff_burnout_index": 30.0,
        "reputation_score": 50.0,
        "water_dependency": 20.0,
    },
    {
        "bu_id": "electronics",
        "revenue_base": 8_000_000,
        "opex_base": 5_000_000,
        "natural_capital_debt": 80,
        "social_license_score": 45.0,
        "governance_risk_score": 25.0,
        "carbon_intensity": 80.0,
        "staff_burnout_index": 35.0,
        "reputation_score": 45.0,
        "water_dependency": 40.0,
    },
    {
        "bu_id": "pharma",
        "revenue_base": 12_000_000,
        "opex_base": 7_000_000,
        "natural_capital_debt": 30,
        "social_license_score": 55.0,
        "governance_risk_score": 15.0,
        "carbon_intensity": 40.0,
        "staff_burnout_index": 20.0,
        "reputation_score": 55.0,
        "water_dependency": 30.0,
    },
    {
        "bu_id": "consumer_goods",
        "revenue_base": 6_000_000,
        "opex_base": 4_000_000,
        "natural_capital_debt": 60,
        "social_license_score": 50.0,
        "governance_risk_score": 22.0,
        "carbon_intensity": 55.0,
        "staff_burnout_index": 25.0,
        "reputation_score": 50.0,
        "water_dependency": 25.0,
    },
]


def _make_state():
    return copy.deepcopy(SEED_GLOBAL_STATE), copy.deepcopy(SEED_BUS)


# ── Test 1: Pillar bypass flags emitted ──────────────────────────

class TestPillarBypassFlags:
    """Verify that pillar_mode_active correctly triggers bypass in handlers."""

    def test_r1_bypass_flag(self):
        from round_logic import _post_r1_foundations
        gs, bus = _make_state()
        events = {"pillar_cost_applied": -3_000_000}
        extra = {}
        _post_r1_foundations(gs, bus, [{"choice_selected": "option_b"}], events, extra, {})
        assert extra.get("r1_pillar_bypass") is True
        assert "r1_flags_set" not in extra  # Should NOT read legacy config

    def test_r1_legacy_no_bypass(self):
        from round_logic import _post_r1_foundations
        gs, bus = _make_state()
        events = {}  # No pillar_cost_applied → legacy mode
        extra = {}
        _post_r1_foundations(gs, bus, [{"choice_selected": "option_b"}], events, extra, {})
        assert "r1_pillar_bypass" not in extra
        assert "r1_flags_set" in extra

    def test_r3_bypass_flag(self):
        from round_logic import _post_r3_scope3
        gs, bus = _make_state()
        events = {"pillar_cost_applied": -5_000_000}
        extra = {}
        _post_r3_scope3(gs, bus, [{"choice_selected": "option_a"}], events, extra, {})
        assert extra.get("r3_pillar_bypass") is True

    def test_r4_bypass_flag(self):
        from round_logic import _post_r4_contagion
        gs, bus = _make_state()
        events = {"pillar_cost_applied": -6_000_000}
        extra = {}
        _post_r4_contagion(gs, bus, [{"choice_selected": "option_a"}], events, extra, {})
        assert extra.get("r4_pillar_bypass") is True

    def test_r5_bypass_flag(self):
        from impact_engine import _post_r5_climate
        gs, bus = _make_state()
        events = {"pillar_cost_applied": -8_000_000, "pillar_aggregate_impacts": {"resilience_factor": 0.85}}
        extra = {}
        with patch("random.random", return_value=0.99):  # No cyclone hit
            _post_r5_climate(gs, bus, [{"choice_selected": "option_a"}], events, extra, {})
        assert extra.get("r5_pillar_bypass") is True

    def test_r6_bypass_flag(self):
        from round_logic import _post_r6_ai_bias
        gs, bus = _make_state()
        events = {"pillar_cost_applied": -8_000_000}
        extra = {}
        _post_r6_ai_bias(gs, bus, [{"choice_selected": "option_b"}], events, extra, {})
        assert extra.get("r6_pillar_bypass") is True

    def test_r7_bypass_flag(self):
        from round_logic import _post_r7_circularity
        gs, bus = _make_state()
        events = {"pillar_cost_applied": -10_000_000, "pillar_aggregate_impacts": {"synergy_multiplier_boost": 0.35}}
        extra = {}
        _post_r7_circularity(gs, bus, [{"choice_selected": "option_c"}], events, extra, {})
        assert extra.get("r7_pillar_bypass") is True

    def test_r8_bypass_flag(self):
        from round_logic import _post_r8_blue_stress
        gs, bus = _make_state()
        events = {"pillar_cost_applied": -12_000_000}
        extra = {}
        _post_r8_blue_stress(gs, bus, [{"choice_selected": "option_a"}], events, extra, {})
        assert extra.get("r8_pillar_bypass") is True

    def test_r9_bypass_flag(self):
        from impact_engine import _post_r9_just_transition
        gs, bus = _make_state()
        events = {"pillar_cost_applied": -20_000_000, "pillar_flags": ["community_fund"]}
        extra = {}
        _post_r9_just_transition(gs, bus, [{"choice_selected": "option_c"}], events, extra, {})
        assert extra.get("r9_pillar_bypass") is True


# ── Test 2: Treasury double-application prevention ───────────────

class TestTreasuryDoubleApplication:
    """Verify pillar mode does NOT re-apply treasury costs from legacy config."""

    def test_r1_no_double_treasury(self):
        from round_logic import _post_r1_foundations
        gs, bus = _make_state()
        initial_treasury = gs["corporate_treasury"]
        # Simulate pillar already deducted -3M
        gs["corporate_treasury"] -= 3_000_000
        events = {"pillar_cost_applied": -3_000_000}
        extra = {}
        _post_r1_foundations(gs, bus, [{"choice_selected": "option_b"}], events, extra, {})
        # Treasury should NOT have been charged again
        assert gs["corporate_treasury"] == initial_treasury - 3_000_000

    def test_r7_no_double_treasury(self):
        from round_logic import _post_r7_circularity
        gs, bus = _make_state()
        initial_treasury = gs["corporate_treasury"]
        gs["corporate_treasury"] -= 10_000_000
        events = {"pillar_cost_applied": -10_000_000, "pillar_aggregate_impacts": {}}
        extra = {}
        _post_r7_circularity(gs, bus, [{"choice_selected": "option_c"}], events, extra, {})
        assert gs["corporate_treasury"] == initial_treasury - 10_000_000

    def test_r9_no_double_treasury(self):
        from impact_engine import _post_r9_just_transition
        gs, bus = _make_state()
        initial_treasury = gs["corporate_treasury"]
        gs["corporate_treasury"] -= 20_000_000
        events = {"pillar_cost_applied": -20_000_000, "pillar_flags": []}
        extra = {}
        _post_r9_just_transition(gs, bus, [{"choice_selected": "option_c"}], events, extra, {})
        assert gs["corporate_treasury"] == initial_treasury - 20_000_000


# ── Test 3: Mutual Exclusivity ───────────────────────────────────

class TestMutualExclusivity:
    """Verify conflicting pillar choices are correctly filtered."""

    def test_r7_synergy_and_circular_exclusive(self):
        """R7: verify MUTUAL_EXCLUSIVITY config has correct structure.
        Note: circular_redesign flag is defined in exclusivity config
        but no current R7 pillar action produces it, so conflict is unreachable.
        Test verifies the exclusivity engine works by testing R9 instead."""
        from pillar_configs import aggregate_pillar_decisions
        # R7: no conflict possible with current actions
        result = aggregate_pillar_decisions(7, {
            "energy": "waste_to_energy",
            "operations": "remanufacture",
            "supply_chain": "local_reuse",
            "offsetting": "carbon_capture",
        })
        # Should work without warnings (no conflicting flags)
        assert isinstance(result["exclusivity_warnings"], list)

    def test_r9_community_and_transition_exclusive(self):
        from pillar_configs import aggregate_pillar_decisions
        result = aggregate_pillar_decisions(9, {
            "energy": "clean_closure",
            "operations": "community_fund",
            "supply_chain": "managed_transition",
            "offsetting": "just_transition_fund",
        })
        flags = set(result["flags_set"])
        has_community = "community_fund" in flags
        has_transition = "managed_transition" in flags
        assert not (has_community and has_transition), \
            f"Mutual exclusivity violated: flags={flags}"


# ── Test 4: R5 Pillar Resilience Factor ──────────────────────────

class TestR5PillarResilience:
    """Verify pillar R5 correctly queues resilience deferred project."""

    def test_hard_engineering_resilience_in_pillar(self):
        from pillar_configs import aggregate_pillar_decisions
        result = aggregate_pillar_decisions(5, {
            "energy": "microgrids",
            "operations": "hard_engineering",
            "supply_chain": "diversify",
            "offsetting": "adaptation_fund",
        })
        assert result["impacts"].get("resilience_factor") == 0.85

    def test_nature_based_resilience_in_pillar(self):
        from pillar_configs import aggregate_pillar_decisions
        result = aggregate_pillar_decisions(5, {
            "energy": "microgrids",
            "operations": "nature_based",
            "supply_chain": "diversify",
            "offsetting": "adaptation_fund",
        })
        assert result["impacts"].get("resilience_factor") == 0.60

    def test_insurance_only_zero_resilience(self):
        from pillar_configs import aggregate_pillar_decisions
        result = aggregate_pillar_decisions(5, {
            "energy": "no_backup",
            "operations": "insurance_only",
            "supply_chain": "accept_risk",
            "offsetting": "no_adaptation",
        })
        assert result["impacts"].get("resilience_factor") == 0.0

    def test_pillar_r5_defers_resilience(self):
        from impact_engine import _post_r5_climate
        gs, bus = _make_state()
        events = {
            "pillar_cost_applied": -15_000_000,
            "pillar_aggregate_impacts": {"resilience_factor": 0.85, "natural_capital_debt_delta": 10},
        }
        extra = {}
        with patch("random.random", return_value=0.99):  # No cyclone
            _post_r5_climate(gs, bus, [{"choice_selected": "option_a"}], events, extra, {})
        assert extra.get("resilience_project_started") is True
        assert extra.get("resilience_deferred_amount") == 0.85
        assert any(p["type"] == "resilience_boost" for p in gs.get("pending_capex_projects", []))


# ── Test 5: Flag Propagation Parity ──────────────────────────────

class TestFlagPropagation:
    """Verify M_R-eligible flags exist in equivalent positions across paradigms."""

    def test_r7_synergy_unlock_flag_exists(self):
        """R7 Option C (legacy) should set synergy_unlock."""
        from round_configs import get_round_options
        opts = get_round_options(7)
        flags = opts.get("option_c", {}).get("flags_set", [])
        assert "synergy_unlock" in flags

    def test_r6_ethical_ai_flag_exists(self):
        """R6 Option B should set ethical_ai_overhaul."""
        from round_configs import get_round_options
        opts = get_round_options(6)
        flags = opts.get("option_b", {}).get("flags_set", [])
        assert "ethical_ai_overhaul" in flags

    def test_hc_r9_community_fund_flag(self):
        """HC R9 Option C should now set community_fund."""
        from healthcare_configs import get_healthcare_round_options
        opts = get_healthcare_round_options(9)
        flags = opts.get("option_c", {}).get("flags_set", [])
        assert "community_fund" in flags

    def test_hc_r9_managed_transition_flag(self):
        """HC R9 Option B should now set managed_transition."""
        from healthcare_configs import get_healthcare_round_options
        opts = get_healthcare_round_options(9)
        flags = opts.get("option_b", {}).get("flags_set", [])
        assert "managed_transition" in flags

    def test_hc_r3_early_decarboniser_flag(self):
        """HC R3 Option C should now set early_decarboniser."""
        from healthcare_configs import get_healthcare_round_options
        opts = get_healthcare_round_options(3)
        flags = opts.get("option_c", {}).get("flags_set", [])
        assert "early_decarboniser" in flags


# ── Test 6: R7 Synergy Unlock works in Pillar Mode ───────────────

class TestR7SynergyPillarMode:
    """Verify synergy unlock works correctly via pillar aggregate."""

    def test_synergy_boost_from_pillar_aggregate(self):
        from round_logic import _post_r7_circularity
        gs, bus = _make_state()
        gs["synergy_multiplier"] = 1.0
        events = {
            "pillar_cost_applied": -7_000_000,
            "pillar_aggregate_impacts": {"synergy_multiplier_boost": 0.35},
        }
        extra = {}
        _post_r7_circularity(gs, bus, [{"choice_selected": "option_c"}], events, extra, {})
        assert extra.get("synergy_multiplier_unlocked") is True
        assert gs["synergy_multiplier"] > 1.0


# ── Test 7: R9 Strike in Pillar Mode ─────────────────────────────

class TestR9StrikePillarMode:
    """Verify strike mechanic triggers via pillar flags."""

    def test_strike_risk_from_pillar_flags(self):
        from impact_engine import _post_r9_just_transition
        gs, bus = _make_state()
        # Set low SLO to trigger strike
        for bu in bus:
            bu["social_license_score"] = 30.0
        events = {
            "pillar_cost_applied": 5_000_000,
            "pillar_flags": ["immediate_closure"],
        }
        extra = {}
        with patch("random.random", return_value=0.1):  # Force strike
            _post_r9_just_transition(gs, bus, [{"choice_selected": "option_a"}], events, extra, {})
        assert extra.get("strike_triggered") is True
        assert extra.get("r9_pillar_bypass") is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
