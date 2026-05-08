"""
Tests for the Consequence DNA Visualizer backend data aggregation.
"""
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from consequence_dna_api import (
    compute_per_decision_impact,
    build_consequence_dna_data,
    DECISION_LP_MAP,
    AGENT_FLOW_MAP,
)


class TestComputePerDecisionImpact:
    """Verify leverage point impact scoring formula."""

    def test_deep_intervention_r2_option_a(self):
        """R2 Option A is LP3 → Impact = base × (13-3) = base × 10."""
        decisions = [{"round_number": 2, "primary_choice": "option_a", "capex_total": 5_000_000}]
        results = compute_per_decision_impact(decisions)
        assert len(results) == 1
        assert results[0]["leverage_level"] == 3
        assert results[0]["category"] == "deep"
        assert results[0]["category_label"] == "Shifting Organizational Goals"
        assert results[0]["impact_score"] == 50.0  # 5 × 10

    def test_shallow_intervention_r1_option_c(self):
        """R1 Option C is LP12 → Impact = base × (13-12) = base × 1."""
        decisions = [{"round_number": 1, "primary_choice": "option_c", "capex_total": 3_000_000}]
        results = compute_per_decision_impact(decisions)
        assert results[0]["leverage_level"] == 12
        assert results[0]["category"] == "shallow"
        assert results[0]["impact_score"] == 3.0  # 3 × 1

    def test_medium_intervention_r3_option_a(self):
        """R3 Option A is LP8 → Impact = base × 5."""
        decisions = [{"round_number": 3, "primary_choice": "option_a", "capex_total": 2_000_000}]
        results = compute_per_decision_impact(decisions)
        assert results[0]["leverage_level"] == 8
        assert results[0]["category"] == "medium"

    def test_unknown_round_defaults_to_lp12(self):
        """Rounds not in DECISION_LP_MAP default to LP12."""
        decisions = [{"round_number": 4, "primary_choice": "option_b", "capex_total": 1_000_000}]
        results = compute_per_decision_impact(decisions)
        assert results[0]["leverage_level"] == 12

    def test_multiple_decisions(self):
        """Multiple decisions across rounds produce correct count."""
        decisions = [
            {"round_number": 1, "primary_choice": "option_a", "capex_total": 1_000_000},
            {"round_number": 5, "primary_choice": "option_b", "capex_total": 2_000_000},
            {"round_number": 9, "primary_choice": "option_b", "capex_total": 1_000_000},
        ]
        results = compute_per_decision_impact(decisions)
        assert len(results) == 3
        deep = [r for r in results if r["category"] == "deep"]
        assert len(deep) >= 1  # R9 option_b is LP2 (deep)


class TestBuildConsequenceDnaData:
    """Integration test for the full Sankey data builder."""

    @pytest.fixture
    def sample_state(self):
        return {
            "round_number": 6,
            "group_reputation": 55,
            "corporate_treasury": 30_000_000,
            "workforce_readiness": 60,
            "synergy_multiplier": 1.1,
            "hr_investment_rounds": 3,
            "active_event_flags": {
                "shadow_board_completed": True,
                "electronics_blindspot": True,
                "materiality_aligned": True,
                "r1_choice": "option_c",
                "r2_choice": "option_a",
            },
            "autonomous_agents": {
                "agents": {
                    "the_regulator": {
                        "tolerance_zone": 40,
                        "escalation_stage": "agitated",
                        "grievance_memory": [],
                        "cascade_chain": [],
                    },
                    "the_journalist": {
                        "tolerance_zone": 65,
                        "escalation_stage": "watching",
                        "grievance_memory": [],
                        "cascade_chain": [],
                    },
                },
                "cascade_log": [],
                "total_triggers": 0,
                "events_this_round": [],
            },
        }

    @pytest.fixture
    def sample_bus(self):
        return [
            {"bu_id": "pharma", "social_license_score": 60, "staff_burnout_index": 25,
             "revenue_base": 10_000_000, "opex_base": 7_000_000, "carbon_intensity": 45,
             "natural_capital_debt": 5},
            {"bu_id": "electronics", "social_license_score": 55, "staff_burnout_index": 30,
             "revenue_base": 8_000_000, "opex_base": 6_000_000, "carbon_intensity": 60,
             "natural_capital_debt": 8},
        ]

    @pytest.fixture
    def sample_history(self):
        return [
            {"round_number": 1, "global_state": {"active_event_flags": {"r1_choice": "option_c"}}},
            {"round_number": 2, "global_state": {"active_event_flags": {"r2_choice": "option_a"}}},
        ]

    def test_basic_structure(self, sample_state, sample_bus, sample_history):
        result = build_consequence_dna_data("test-123", sample_state, sample_bus, sample_history)
        assert "sankey_nodes" in result
        assert "sankey_links" in result
        assert "mr_projection" in result
        assert "leverage_summary" in result
        assert "agents" in result

    def test_ignition_requires_shadow_board(self, sample_state, sample_bus, sample_history):
        result = build_consequence_dna_data("test-123", sample_state, sample_bus, sample_history)
        assert result["ignited"] is True
        assert result["shadow_board_completed"] is True

        # Without shadow board
        state_no_sb = {**sample_state, "active_event_flags": {**sample_state["active_event_flags"]}}
        del state_no_sb["active_event_flags"]["shadow_board_completed"]
        result2 = build_consequence_dna_data("test-456", state_no_sb, sample_bus, sample_history)
        assert result2["ignited"] is False

    def test_conflict_nodes_present(self, sample_state, sample_bus, sample_history):
        result = build_consequence_dna_data("test-123", sample_state, sample_bus, sample_history)
        conflicts = result["sankey_nodes"]["conflict_nodes"]
        assert len(conflicts) > 0
        # Regulator should be agitated
        reg = next((c for c in conflicts if c["agent_id"] == "the_regulator"), None)
        assert reg is not None
        assert reg["stage"] == "agitated"
        assert reg["constriction_factor"] > 0

    def test_mr_projection_present(self, sample_state, sample_bus, sample_history):
        result = build_consequence_dna_data("test-123", sample_state, sample_bus, sample_history)
        mr = result["mr_projection"]
        assert "mr" in mr
        assert "breakdown" in mr
        assert isinstance(mr["mr"], (int, float))

    def test_no_agents_graceful(self, sample_bus, sample_history):
        """If no autonomous_agents in state, should still build without error."""
        state = {
            "round_number": 3,
            "group_reputation": 50,
            "active_event_flags": {},
            "workforce_readiness": 50,
            "synergy_multiplier": 1.0,
            "hr_investment_rounds": 0,
        }
        result = build_consequence_dna_data("test-789", state, sample_bus, sample_history)
        assert result["sankey_nodes"]["conflict_nodes"] == []
        assert result["agents"] == []


class TestAgentFlowMap:
    """Verify all 5 agents have flow mappings."""

    def test_all_agents_mapped(self):
        expected = {"the_regulator", "the_journalist", "the_institutional_investor",
                    "the_community_activist", "the_gen_z_employee"}
        assert set(AGENT_FLOW_MAP.keys()) == expected

    def test_each_has_required_fields(self):
        for aid, mapping in AGENT_FLOW_MAP.items():
            assert "flow_source" in mapping, f"{aid} missing flow_source"
            assert "flow_target" in mapping, f"{aid} missing flow_target"
            assert "leak_label" in mapping, f"{aid} missing leak_label"


class TestDecisionLPMap:
    """Verify leverage point classifications are consistent."""

    def test_deep_interventions_exist(self):
        """At least some decisions should be classified as deep (LP 1-3)."""
        deep = []
        for rnum, choices in DECISION_LP_MAP.items():
            for choice, lp in choices.items():
                if lp <= 3:
                    deep.append((rnum, choice, lp))
        assert len(deep) >= 2, f"Expected at least 2 deep interventions, found {len(deep)}"

    def test_shallow_interventions_exist(self):
        """At least some decisions should be shallow (LP 10-12)."""
        shallow = []
        for rnum, choices in DECISION_LP_MAP.items():
            for choice, lp in choices.items():
                if lp >= 10:
                    shallow.append((rnum, choice, lp))
        assert len(shallow) >= 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
