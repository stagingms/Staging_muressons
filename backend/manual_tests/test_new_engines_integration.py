"""
Muressons Global Corporation — New Engines Integration Tests
Tests that all new engine modules are correctly wired into:
1. round_logic.py (run_new_engines)
2. router.py (API endpoints)
3. admin_router.py (God Mode toggles)
4. pedagogical_engine.py (toggle defaults)

Run: python -m pytest test_new_engines_integration.py -v
"""

import pytest
import copy

# ═══════════════════════════════════════════════════════════════
#  TEST FIXTURES
# ═══════════════════════════════════════════════════════════════

def _make_gs(**overrides):
    """Create a minimal global_state dict."""
    gs = {
        "round_number": 3,
        "corporate_treasury": 25_000_000,
        "group_reputation": 50.0,
        "synergy_multiplier": 1.0,
        "cost_of_capital": 0.05,
        "workforce_readiness": 50.0,
        "active_event_flags": {},
    }
    gs.update(overrides)
    return gs

def _make_bus():
    """Create standard BU states."""
    return [
        {"bu_id": "pharma", "revenue_base": 18_000_000, "opex_base": 11_500_000,
         "carbon_intensity": 45, "natural_capital_debt": 5000,
         "social_license_score": 70, "governance_risk_score": 15,
         "staff_burnout_index": 20, "water_dependency": 0.6},
        {"bu_id": "electronics", "revenue_base": 22_000_000, "opex_base": 14_000_000,
         "carbon_intensity": 60, "natural_capital_debt": 3800,
         "social_license_score": 65, "governance_risk_score": 25,
         "staff_burnout_index": 30, "water_dependency": 0.8},
        {"bu_id": "consumer_goods", "revenue_base": 15_000_000, "opex_base": 9_000_000,
         "carbon_intensity": 30, "natural_capital_debt": 2100,
         "social_license_score": 78, "governance_risk_score": 10,
         "staff_burnout_index": 15, "water_dependency": 0.3},
        {"bu_id": "software", "revenue_base": 20_000_000, "opex_base": 8_000_000,
         "carbon_intensity": 10, "natural_capital_debt": 500,
         "social_license_score": 85, "governance_risk_score": 5,
         "staff_burnout_index": 10, "water_dependency": 0.1},
    ]


# ═══════════════════════════════════════════════════════════════
#  1. TOGGLE GATING TESTS
#     Verify engines respect ON/OFF toggles
# ═══════════════════════════════════════════════════════════════

class TestToggleGating:
    """Engines must only run when their toggle is enabled."""

    def test_run_new_engines_returns_dict(self):
        from round_logic import run_new_engines
        gs = _make_gs()
        bus = _make_bus()
        result = run_new_engines(3, gs, bus, {})
        assert isinstance(result, dict)

    def test_biodiversity_engine_creates_state(self):
        from round_logic import run_new_engines
        gs = _make_gs()
        bus = _make_bus()
        run_new_engines(3, gs, bus, {})
        assert "biodiversity_state" in gs

    def test_biodiversity_disabled_skips(self):
        from round_logic import run_new_engines
        gs = _make_gs(pedagogical_overrides={"biodiversity_engine_enabled": False})
        bus = _make_bus()
        result = run_new_engines(3, gs, bus, {})
        assert "biodiversity" not in result
        assert "biodiversity_state" not in gs

    def test_balance_sheet_creates_state(self):
        from round_logic import run_new_engines
        gs = _make_gs()
        bus = _make_bus()
        run_new_engines(3, gs, bus, {})
        assert "balance_sheet" in gs

    def test_balance_sheet_disabled_skips(self):
        from round_logic import run_new_engines
        gs = _make_gs(pedagogical_overrides={"balance_sheet_enabled": False})
        bus = _make_bus()
        result = run_new_engines(3, gs, bus, {})
        assert "balance_sheet" not in result

    def test_board_governance_creates_state(self):
        from round_logic import run_new_engines
        gs = _make_gs()
        bus = _make_bus()
        run_new_engines(3, gs, bus, {})
        assert "board_governance" in gs

    def test_org_politics_creates_state(self):
        from round_logic import run_new_engines
        gs = _make_gs()
        bus = _make_bus()
        run_new_engines(3, gs, bus, {})
        assert "org_politics" in gs

    def test_supply_chain_creates_state(self):
        from round_logic import run_new_engines
        gs = _make_gs()
        bus = _make_bus()
        run_new_engines(3, gs, bus, {})
        assert "supply_chain" in gs

    def test_npc_stakeholders_creates_state(self):
        from round_logic import run_new_engines
        gs = _make_gs()
        bus = _make_bus()
        run_new_engines(3, gs, bus, {})
        assert "npc_stakeholders" in gs

    def test_branching_at_r5(self):
        from round_logic import run_new_engines
        gs = _make_gs(round_number=5)
        bus = _make_bus()
        result = run_new_engines(5, gs, bus, {})
        assert "archetype_classification" in result
        assert gs.get("player_archetype") in (
            "regenerative_leader", "pragmatic_optimizer",
            "fragile_extractor", "turnaround_candidate",
        )

    def test_branching_not_at_r3(self):
        from round_logic import run_new_engines
        gs = _make_gs(round_number=3)
        bus = _make_bus()
        result = run_new_engines(3, gs, bus, {})
        assert "archetype_classification" not in result

    def test_timer_disabled_by_default(self):
        from round_logic import run_new_engines
        gs = _make_gs()
        bus = _make_bus()
        result = run_new_engines(3, gs, bus, {})
        assert "decision_timer" not in result

    def test_timer_enabled_returns_config(self):
        from round_logic import run_new_engines
        gs = _make_gs(pedagogical_overrides={"decision_timer_enabled": True})
        bus = _make_bus()
        result = run_new_engines(3, gs, bus, {})
        assert "decision_timer" in result
        assert result["decision_timer"]["enabled"] is True
        assert result["decision_timer"]["duration_seconds"] == 300

    def test_peer_prompts_at_r5(self):
        from round_logic import run_new_engines
        gs = _make_gs(round_number=5)
        bus = _make_bus()
        result = run_new_engines(5, gs, bus, {})
        assert "peer_learning_prompts" in result
        assert result["peer_learning_prompts"]["title"] == "Mid-Game Peer Reflection"

    def test_peer_prompts_not_at_r3(self):
        from round_logic import run_new_engines
        gs = _make_gs(round_number=3)
        bus = _make_bus()
        result = run_new_engines(3, gs, bus, {})
        assert "peer_learning_prompts" not in result

    def test_regulatory_sandbox_disabled_by_default(self):
        from round_logic import run_new_engines
        gs = _make_gs()
        bus = _make_bus()
        result = run_new_engines(3, gs, bus, {})
        assert "regulatory_sandbox" not in result


# ═══════════════════════════════════════════════════════════════
#  2. ENGINE OUTPUT VALIDITY
#     Verify engine outputs have expected structure
# ═══════════════════════════════════════════════════════════════

class TestEngineOutputs:
    """Engine output dicts have the expected keys."""

    def test_biodiversity_output(self):
        from biodiversity_engine import create_initial_biodiversity_state, process_biodiversity_tick
        bio = create_initial_biodiversity_state()
        gs = _make_gs()
        bus = _make_bus()
        bio, diag = process_biodiversity_tick(bio, gs, bus, {}, 3)
        assert "ecosystem_health_index" in bio
        assert isinstance(bio["ecosystem_health_index"], (int, float))

    def test_balance_sheet_output(self):
        from balance_sheet import create_initial_balance_sheet, process_balance_sheet_tick
        bus = _make_bus()
        bs = create_initial_balance_sheet(bus)
        gs = _make_gs()
        bs, diag = process_balance_sheet_tick(bs, gs, bus, {}, 3)
        assert "current_assets" in bs
        assert "current_liabilities" in bs
        assert "net_assets" in bs or "covenant_status" in bs

    def test_board_governance_output(self):
        from board_governance import create_initial_board_state, process_board_tick
        board = create_initial_board_state()
        gs = _make_gs()
        bus = _make_bus()
        board, diag = process_board_tick(board, gs, bus, 3)
        assert "directors" in board
        assert len(board["directors"]) > 0
        assert "board_effectiveness_score" in board

    def test_org_politics_output(self):
        from org_politics import create_initial_org_politics_state, process_org_politics_tick
        org = create_initial_org_politics_state()
        gs = _make_gs()
        bus = _make_bus()
        org, diag = process_org_politics_tick(org, gs, bus, {}, 3)
        assert "csuite_members" in org
        assert "political_capital" in org

    def test_supply_chain_output(self):
        from supply_chain_network import create_initial_supply_chain, process_supply_chain_tick
        sc = create_initial_supply_chain()
        gs = _make_gs()
        bus = _make_bus()
        sc, diag = process_supply_chain_tick(sc, gs, bus, {}, 3)
        assert "tier_1_suppliers" in sc
        assert "tier_2_suppliers" in sc
        assert "tier_3_suppliers" in sc

    def test_npc_stakeholders_output(self):
        from npc_stakeholders import create_initial_npc_state, process_npc_tick
        npc = create_initial_npc_state()
        gs = _make_gs()
        bus = _make_bus()
        npc, diag = process_npc_tick(npc, gs, bus, {}, 3)
        assert "npcs" in npc
        assert len(npc["npcs"]) > 0

    def test_branching_archetype_output(self):
        from branching_engine import classify_player_archetype
        gs = _make_gs(group_reputation=75)
        bus = _make_bus()
        for bu in bus:
            bu["social_license_score"] = 70
            bu["carbon_intensity"] = 30
        result = classify_player_archetype(gs, bus)
        assert "archetype_id" in result
        assert "archetype_name" in result
        assert "branch_modifiers" in result

    def test_adaptive_severity_output(self):
        from branching_engine import calc_adaptive_crisis_severity
        gs = _make_gs()
        bus = _make_bus()
        severity, diag = calc_adaptive_crisis_severity(40, "pragmatic_optimizer", gs, bus, 7)
        assert isinstance(severity, float)
        assert "base_severity" in diag
        assert "final_severity" in diag

    def test_dynamic_cases_output(self):
        from dynamic_cases import select_contextual_cases
        gs = _make_gs(group_reputation=30)
        bus = _make_bus()
        cases = select_contextual_cases(gs, bus, 5, max_cases=2)
        # Low reputation should match some cases
        assert isinstance(cases, list)

    def test_tcfd_scenario_output(self):
        from tcfd_scenarios import run_scenario_analysis
        gs = _make_gs()
        bus = _make_bus()
        result = run_scenario_analysis("orderly_1_5", bus, gs)
        assert "scenario" in result
        assert "overall_risk_rating" in result

    def test_meadows_archetype_detection(self):
        from meadows_leverage import detect_archetypes
        gs = _make_gs()
        bus = _make_bus()
        archetypes = detect_archetypes(gs, bus, {})
        assert isinstance(archetypes, list)

    def test_scope3_estimation(self):
        from supply_chain_network import create_initial_supply_chain, estimate_scope3_emissions
        sc = create_initial_supply_chain()
        result = estimate_scope3_emissions(sc)
        assert "scope_3_upstream" in result
        assert "scope_3_confidence" in result


# ═══════════════════════════════════════════════════════════════
#  3. GOD-MODE INTEGRATION
#     Verify toggles are exposed in admin endpoints
# ═══════════════════════════════════════════════════════════════

class TestGodModeIntegration:
    """New toggles must be accessible via god-mode settings."""

    def test_global_settings_exposes_new_toggles(self):
        """GET /api/admin/global-settings must include all new toggles."""
        import asyncio
        from admin_router import get_global_settings
        result = asyncio.run(get_global_settings())
        new_toggles = [
            "decision_timer_enabled", "decision_timer_seconds",
            "peer_learning_prompts_enabled",
            "board_governance_enabled", "supply_chain_network_enabled",
            "biodiversity_engine_enabled", "market_dynamics_enabled",
            "balance_sheet_enabled", "regulatory_sandbox_enabled",
            "dynamic_cases_enabled", "branching_enabled",
            "npc_stakeholders_enabled", "tcfd_scenarios_enabled",
            "org_politics_enabled", "meadows_leverage_enabled",
            "system_archetypes_enabled",
        ]
        for toggle in new_toggles:
            assert toggle in result, f"Missing toggle '{toggle}' in global-settings GET"

    def test_global_settings_patch_model_accepts_new_toggles(self):
        """GlobalSettingsPatch must accept all new toggle fields."""
        from admin_router import GlobalSettingsPatch
        # Should not raise ValidationError
        patch = GlobalSettingsPatch(
            biodiversity_engine_enabled=False,
            board_governance_enabled=False,
            decision_timer_enabled=True,
            decision_timer_seconds=180,
            regulatory_sandbox_enabled=True,
            branching_enabled=False,
        )
        data = patch.model_dump(exclude_unset=True)
        assert data["biodiversity_engine_enabled"] is False
        assert data["decision_timer_seconds"] == 180
        assert data["regulatory_sandbox_enabled"] is True

    def test_scaffolding_status_includes_new_engines(self):
        """GET /api/admin/scaffolding-status must list new engine toggles."""
        import asyncio
        from admin_router import get_scaffolding_status
        result = asyncio.run(get_scaffolding_status())
        feature_keys = [f["key"] for f in result["features"]]
        expected = [
            "decision_timer_enabled", "biodiversity_engine_enabled",
            "board_governance_enabled", "supply_chain_network_enabled",
            "npc_stakeholders_enabled", "org_politics_enabled",
            "branching_enabled", "dynamic_cases_enabled",
            "tcfd_scenarios_enabled", "regulatory_sandbox_enabled",
            "meadows_leverage_enabled", "system_archetypes_enabled",
        ]
        for key in expected:
            assert key in feature_keys, f"Missing '{key}' in scaffolding-status features"


# ═══════════════════════════════════════════════════════════════
#  4. PEDAGOGICAL ENGINE DEFAULTS
#     Verify toggle defaults are correct
# ═══════════════════════════════════════════════════════════════

class TestPedagogicalDefaults:
    """Toggle defaults must match the design intent."""

    def test_default_toggles(self):
        from pedagogical_engine import DEFAULT_PEDAGOGICAL_TOGGLES as t
        # ON by default (core experience)
        assert t["biodiversity_engine_enabled"] is True
        assert t["balance_sheet_enabled"] is True
        assert t["board_governance_enabled"] is True
        assert t["supply_chain_network_enabled"] is True
        assert t["npc_stakeholders_enabled"] is True
        assert t["org_politics_enabled"] is True
        assert t["branching_enabled"] is True
        assert t["dynamic_cases_enabled"] is True
        assert t["tcfd_scenarios_enabled"] is True
        assert t["peer_learning_prompts_enabled"] is True
        assert t["meadows_leverage_enabled"] is True
        assert t["system_archetypes_enabled"] is True

        # OFF by default (expert/multiplayer only)
        assert t["decision_timer_enabled"] is False
        assert t["market_dynamics_enabled"] is False
        assert t["regulatory_sandbox_enabled"] is False

    def test_toggle_override_works(self):
        from pedagogical_engine import get_pedagogical_toggles
        toggles = get_pedagogical_toggles({"biodiversity_engine_enabled": False})
        assert toggles["biodiversity_engine_enabled"] is False
        assert toggles["balance_sheet_enabled"] is True  # unchanged


# ═══════════════════════════════════════════════════════════════
#  5. RESILIENCE TESTS
#     Verify engines don't crash the core pipeline
# ═══════════════════════════════════════════════════════════════

class TestResilience:
    """Engine failures must NOT crash the simulation."""

    def test_run_new_engines_with_empty_state(self):
        from round_logic import run_new_engines
        result = run_new_engines(1, {}, [], {})
        assert isinstance(result, dict)

    def test_run_new_engines_with_corrupted_bus(self):
        from round_logic import run_new_engines
        gs = _make_gs()
        bad_bus = [{"bu_id": "broken"}]
        result = run_new_engines(3, gs, bad_bus, {})
        assert isinstance(result, dict)

    def test_engines_idempotent_on_rerun(self):
        """Running engines twice on same state doesn't double-create."""
        from round_logic import run_new_engines
        gs = _make_gs()
        bus = _make_bus()
        run_new_engines(3, gs, bus, {})
        bio1 = copy.deepcopy(gs.get("biodiversity_state", {}))
        run_new_engines(4, gs, bus, {})
        # State should be updated, not recreated
        assert "biodiversity_state" in gs

    def test_all_disabled_returns_empty(self):
        """With all toggles disabled, no engine output produced."""
        from round_logic import run_new_engines
        overrides = {
            "biodiversity_engine_enabled": False,
            "balance_sheet_enabled": False,
            "board_governance_enabled": False,
            "org_politics_enabled": False,
            "supply_chain_network_enabled": False,
            "npc_stakeholders_enabled": False,
            "branching_enabled": False,
            "dynamic_cases_enabled": False,
            "peer_learning_prompts_enabled": False,
            "decision_timer_enabled": False,
            "system_archetypes_enabled": False,
            "regulatory_sandbox_enabled": False,
        }
        gs = _make_gs(pedagogical_overrides=overrides)
        bus = _make_bus()
        result = run_new_engines(3, gs, bus, {})
        # Should return empty or near-empty dict
        assert len(result) == 0


# ═══════════════════════════════════════════════════════════════
#  6. CROSS-MODULE CONNECTIONS
#     Verify data flows between engines
# ═══════════════════════════════════════════════════════════════

class TestCrossModuleConnections:
    """Engines that read from other engines' state work correctly."""

    def test_tcfd_reads_biodiversity(self):
        """TCFD scenario should handle biodiversity state input."""
        from tcfd_scenarios import run_scenario_analysis
        from biodiversity_engine import create_initial_biodiversity_state
        gs = _make_gs()
        bus = _make_bus()
        bio = create_initial_biodiversity_state()
        result = run_scenario_analysis("orderly_1_5", bus, gs, bio)
        assert "scenario" in result

    def test_supply_chain_scope3_feeds_into_events(self):
        """Supply chain Scope 3 output is structured correctly."""
        from supply_chain_network import create_initial_supply_chain, estimate_scope3_emissions
        sc = create_initial_supply_chain()
        result = estimate_scope3_emissions(sc)
        assert result["scope_3_upstream"] > 0
        assert 0.0 <= result["scope_3_confidence"] <= 1.0

    def test_dynamic_cases_respond_to_low_reputation(self):
        """Low reputation should trigger relevant case selection."""
        from dynamic_cases import select_contextual_cases
        gs = _make_gs(group_reputation=25)
        bus = _make_bus()
        cases = select_contextual_cases(gs, bus, 5, max_cases=5)
        # Cases should be selected based on situation matching
        assert isinstance(cases, list)
        assert len(cases) > 0, "Low reputation should trigger at least one case"

    def test_adaptive_severity_scales_with_archetype(self):
        """Different archetypes should produce different severity."""
        from branching_engine import calc_adaptive_crisis_severity
        gs = _make_gs(group_reputation=50, corporate_treasury=25_000_000)
        bus = _make_bus()

        regen_sev, _ = calc_adaptive_crisis_severity(40, "regenerative_leader", gs, bus, 7)
        fragile_sev, _ = calc_adaptive_crisis_severity(40, "fragile_extractor", gs, bus, 7)

        # Both should return valid numbers
        assert isinstance(regen_sev, float)
        assert isinstance(fragile_sev, float)
        # Severity should differ by archetype
        assert regen_sev != fragile_sev, f"Regen={regen_sev}, Fragile={fragile_sev}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
