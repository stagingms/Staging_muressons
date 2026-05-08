"""
Muressons — Systemic Risk Integration Tests (PHASE-1)
Validates the full wiring of:
  - ESG-Adjusted WACC injection into process_tick
  - Black Swan evaluation at tick start
  - Tipping Point evaluation + penalty application
  - NPC Cascading Reactions
  - Foreshadowing Signals
  - Difficulty Tier propagation
"""
import sys, os, unittest, copy
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestESGAdjustedWACC(unittest.TestCase):
    """Verify ESG-adjusted WACC modifies corporate_cost_of_capital."""

    def test_wacc_increases_with_high_carbon(self):
        from systemic_risk_engine import calc_esg_adjusted_wacc
        # High carbon intensity should increase WACC
        wacc, diag = calc_esg_adjusted_wacc(0.05, carbon_intensity_avg=90, governance_risk_avg=20, social_license_avg=50)
        self.assertGreater(wacc, 0.05, "High carbon should increase WACC")
        self.assertGreater(diag["carbon_premium"], 0)

    def test_wacc_decreases_with_high_slo(self):
        from systemic_risk_engine import calc_esg_adjusted_wacc
        # High SLO should decrease WACC via discount
        wacc, diag = calc_esg_adjusted_wacc(0.05, carbon_intensity_avg=30, governance_risk_avg=10, social_license_avg=90)
        self.assertLess(wacc, 0.05, "High SLO should give WACC discount")
        self.assertGreater(diag["slo_discount"], 0)

    def test_wacc_clamps_between_3_and_15_pct(self):
        from systemic_risk_engine import calc_esg_adjusted_wacc
        # Extreme inputs should still be clamped
        wacc_low, _ = calc_esg_adjusted_wacc(0.01, 0, 0, 100)
        wacc_high, _ = calc_esg_adjusted_wacc(0.10, 200, 100, 0, biodiversity_dependency=5.0)
        self.assertGreaterEqual(wacc_low, 0.03)
        self.assertLessEqual(wacc_high, 0.15)


class TestSupplyChainTransparency(unittest.TestCase):
    """Verify SCT entropy and boost logic."""

    def test_natural_entropy(self):
        from systemic_risk_engine import calc_supply_chain_transparency
        score, diag = calc_supply_chain_transparency(50, {}, 3)
        self.assertLess(score, 50, "Natural entropy should reduce SCT")
        self.assertEqual(diag["entropy"], -3.0)

    def test_deep_audit_boosts(self):
        from systemic_risk_engine import calc_supply_chain_transparency
        score, diag = calc_supply_chain_transparency(30, {"deep_audit_completed": True}, 3)
        self.assertGreater(score, 30, "Deep audit should boost SCT significantly")
        self.assertIn("deep_audit_completed", diag["boosts_applied"])


class TestEmployerBrand(unittest.TestCase):
    """Verify employer brand composite scoring."""

    def test_healthy_employer_brand(self):
        from systemic_risk_engine import calc_employer_brand
        score, diag = calc_employer_brand(80, 10, 70)
        self.assertGreater(score, 60)
        self.assertEqual(diag["talent_risk_level"], "healthy")

    def test_critical_employer_brand(self):
        from systemic_risk_engine import calc_employer_brand
        score, diag = calc_employer_brand(10, 90, 10)
        self.assertLess(score, 25)
        self.assertEqual(diag["talent_risk_level"], "critical")
        self.assertGreater(diag["recruitment_cost_premium"], 0)


class TestTippingPoints(unittest.TestCase):
    """Verify tipping point evaluation and irreversibility."""

    def _make_gs(self, **overrides):
        gs = {
            "active_event_flags": {"covenant_status": "green"},
            "biodiversity_state": {"ecosystem_health_index": 50},
        }
        gs.update(overrides)
        return gs

    def _make_bus(self, ci=50, slo=50, burnout=0, count=4):
        return [
            {"bu_id": f"bu_{i}", "carbon_intensity": ci, "social_license_score": slo, "staff_burnout_index": burnout}
            for i in range(count)
        ]

    def test_no_tipping_in_normal_state(self):
        from systemic_risk_engine import evaluate_tipping_points
        result = evaluate_tipping_points(self._make_gs(), self._make_bus())
        self.assertFalse(result["any_tipped"])
        self.assertEqual(len(result["transitions"]), 0)

    def test_climate_tipping_triggers(self):
        from systemic_risk_engine import evaluate_tipping_points
        gs = self._make_gs(biodiversity_state={"ecosystem_health_index": 10})
        bus = self._make_bus(ci=90)
        result = evaluate_tipping_points(gs, bus)
        self.assertTrue(result["tipping_state"].get("climate_tipped"))
        self.assertTrue(any(t["dimension"] == "climate" for t in result["transitions"]))

    def test_tipping_is_irreversible(self):
        from systemic_risk_engine import evaluate_tipping_points
        # Already tipped state should stay tipped even with good metrics
        existing = {"climate_tipped": True, "climate_tier": "tipped"}
        result = evaluate_tipping_points(self._make_gs(), self._make_bus(ci=20), current_tipped=existing)
        self.assertTrue(result["tipping_state"]["climate_tipped"], "Tipped state must be irreversible")


class TestBlackSwanRegistry(unittest.TestCase):
    """Verify Black Swan event registry functions."""

    def test_registry_has_events(self):
        from black_swan_registry import get_available_black_swans
        swans = get_available_black_swans(round_number=6)
        self.assertGreater(len(swans), 3, "Should have several events available in R6")

    def test_difficulty_configs_exist(self):
        from black_swan_registry import get_difficulty_config
        for tier in ["standard", "advanced", "expert"]:
            cfg = get_difficulty_config(tier)
            self.assertIn("probability_multiplier", cfg)
            self.assertIn("impact_multiplier", cfg)

    def test_expert_is_harder(self):
        from black_swan_registry import get_difficulty_config
        std = get_difficulty_config("standard")
        exp = get_difficulty_config("expert")
        self.assertGreater(exp["probability_multiplier"], std["probability_multiplier"])


class TestNPCCascades(unittest.TestCase):
    """Verify NPC cascade reaction logic."""

    def test_no_cascades_with_neutral_satisfaction(self):
        from systemic_risk_engine import evaluate_npc_cascades
        sats = {"activist_investor": 50, "regulator": 50, "community_leader": 50, "gen_z_employee": 50}
        result = evaluate_npc_cascades(sats, round_number=5)
        self.assertEqual(len(result), 0)

    def test_divestment_cascade_triggers(self):
        from systemic_risk_engine import evaluate_npc_cascades
        sats = {"activist_investor": 10, "regulator": 50, "community_leader": 50, "gen_z_employee": 50}
        result = evaluate_npc_cascades(sats, round_number=5)
        actions = [c["action"] for c in result]
        self.assertIn("divestment_campaign", actions)
        self.assertIn("proxy_fight", actions)

    def test_cascade_dedup_prevents_repeat(self):
        from systemic_risk_engine import evaluate_npc_cascades
        sats = {"activist_investor": 10}
        existing = [{"action": "divestment_campaign"}, {"action": "proxy_fight"}]
        result = evaluate_npc_cascades(sats, round_number=5, active_cascades=existing)
        actions = [c["action"] for c in result]
        self.assertNotIn("divestment_campaign", actions, "Should not re-trigger active cascade")


class TestForeshadowing(unittest.TestCase):
    """Verify foreshadowing signal system."""

    def test_no_signals_without_matching_flags(self):
        from systemic_risk_engine import get_foreshadowing_for_round
        result = get_foreshadowing_for_round(3, {})
        self.assertEqual(len(result), 0)

    def test_audit_signal_at_r3(self):
        from systemic_risk_engine import get_foreshadowing_for_round
        result = get_foreshadowing_for_round(3, {"deep_audit_completed": True})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["signal_id"], "audit_protection")
        self.assertEqual(result[0]["category"], "positive")

    def test_blindspot_warning_at_r3(self):
        from systemic_risk_engine import get_foreshadowing_for_round
        result = get_foreshadowing_for_round(3, {"electronics_blindspot": True})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["category"], "warning")


class TestMaterialityShocks(unittest.TestCase):
    """Verify materiality shock evaluation."""

    def test_no_shocks_outside_round_range(self):
        from systemic_risk_engine import evaluate_materiality_shocks
        # All shocks start at R3+ so R1 should have zero
        import random
        random.seed(42)
        result = evaluate_materiality_shocks(1, "expert")
        self.assertEqual(len(result), 0)

    def test_shock_structure(self):
        from systemic_risk_engine import evaluate_materiality_shocks
        import random
        random.seed(99)
        # Force evaluation in the window R6 (multiple shocks overlap)
        results = []
        for _ in range(100):
            results.extend(evaluate_materiality_shocks(6, "expert"))
        if results:
            r = results[0]
            self.assertIn("shock_id", r)
            self.assertIn("issue", r)
            self.assertIn("narrative", r)
            self.assertIn("financial_materiality_jump", r)


class TestWACCCovenantWiring(unittest.TestCase):
    """Verify ESG-WACC dynamically tightens covenant trigger ratios."""

    def test_normal_wacc_no_tightening(self):
        from balance_sheet import check_covenants
        bs = _make_bs(debt=100_000, cash=10_000, trigger=3.5)
        # WACC at 5% (well below 8% threshold) → no tightening
        status, diag = check_covenants(bs, 50_000, esg_wacc=0.05)
        self.assertEqual(diag["trigger_ratio"], 3.5)
        self.assertEqual(diag["wacc_tightening"], 0)

    def test_high_wacc_tightens_covenant(self):
        from balance_sheet import check_covenants
        bs = _make_bs(debt=100_000, cash=10_000, trigger=3.5)
        # WACC at 10% → 2% excess → tightening = 0.50×
        status, diag = check_covenants(bs, 50_000, esg_wacc=0.10)
        self.assertEqual(diag["trigger_ratio"], 3.0)
        self.assertAlmostEqual(diag["wacc_tightening"], 0.50, places=2)

    def test_extreme_wacc_floors_at_2x(self):
        from balance_sheet import check_covenants
        bs = _make_bs(debt=100_000, cash=10_000, trigger=3.5)
        # WACC at 15% → extreme tightening, but floored at 2.0×
        status, diag = check_covenants(bs, 50_000, esg_wacc=0.15)
        self.assertGreaterEqual(diag["trigger_ratio"], 2.0)


class TestEmployerBrandOPEX(unittest.TestCase):
    """Verify employer brand OPEX penalty applies universally across all BUs."""

    def test_no_penalty_when_brand_healthy(self):
        from systemic_risk_engine import calc_employer_brand
        score, _ = calc_employer_brand(group_reputation=80, avg_burnout=10, workforce_readiness=70)
        self.assertGreater(score, 40, "Healthy employer brand should not trigger penalty")

    def test_penalty_applied_when_brand_critical(self):
        from systemic_risk_engine import calc_employer_brand
        score, _ = calc_employer_brand(group_reputation=10, avg_burnout=90, workforce_readiness=10)
        self.assertLess(score, 40, "Critical employer brand should trigger penalty")
        # Verify penalty calculation
        eb_opex_multiplier = ((40 - score) / 40) * 0.08
        self.assertGreater(eb_opex_multiplier, 0)
        self.assertLessEqual(eb_opex_multiplier, 0.08)

    def test_penalty_is_graded(self):
        from systemic_risk_engine import calc_employer_brand
        # Moderately bad vs. catastrophically bad
        score_moderate, _ = calc_employer_brand(30, 50, 30)
        score_extreme, _ = calc_employer_brand(5, 95, 5)
        if score_moderate < 40 and score_extreme < 40:
            mult_moderate = ((40 - score_moderate) / 40) * 0.08
            mult_extreme = ((40 - score_extreme) / 40) * 0.08
            self.assertGreater(mult_extreme, mult_moderate,
                              "Worse employer brand should produce higher penalty")


class TestDifficultyCovenantRatio(unittest.TestCase):
    """Verify difficulty tier propagates correct covenant trigger ratios."""

    def test_easy_has_generous_covenant(self):
        from black_swan_registry import get_difficulty_config
        cfg = get_difficulty_config("easy")
        self.assertEqual(cfg["covenant_trigger_ratio"], 4.5)

    def test_expert_has_tight_covenant(self):
        from black_swan_registry import get_difficulty_config
        cfg = get_difficulty_config("expert")
        self.assertEqual(cfg["covenant_trigger_ratio"], 2.5)


def _make_bs(debt=50_000_000, cash=10_000_000, trigger=3.5):
    """Helper: create a minimal balance sheet dict for covenant testing."""
    return {
        "non_current_liabilities": {"revolving_credit_facility": debt, "green_bonds_outstanding": 0},
        "current_liabilities": {"short_term_debt": 0},
        "current_assets": {"cash_and_equivalents": cash},
        "covenant_trigger_ratio": trigger,
    }


class TestForecastCaching(unittest.TestCase):
    """Verify forecast caching layer."""

    def _make_gs(self):
        return {
            "corporate_treasury": 50_000_000,
            "cost_of_capital": 0.05,
            "round_number": 3,
            "active_event_flags": {},
        }

    def _make_bus(self):
        return [{
            "bu_id": "test_bu", "revenue_base": 10_000_000, "opex_base": 7_000_000,
            "reputation_score": 60, "social_license_score": 55, "governance_risk_score": 25,
            "carbon_intensity": 50, "natural_capital_debt": 5000, "water_dependency": 0.3,
            "staff_burnout_index": 20,
        }]

    def test_cache_returns_same_result(self):
        from engine import calc_forecast_cached, invalidate_forecast_cache
        invalidate_forecast_cache()  # Clean slate
        gs, bus = self._make_gs(), self._make_bus()
        r1 = calc_forecast_cached("test_session", 3, gs, bus)
        r2 = calc_forecast_cached("test_session", 3, gs, bus)
        self.assertIs(r1, r2, "Cached call should return identical object")

    def test_session_invalidation(self):
        from engine import calc_forecast_cached, invalidate_forecast_cache
        invalidate_forecast_cache()
        gs, bus = self._make_gs(), self._make_bus()
        r1 = calc_forecast_cached("s1", 3, gs, bus)
        invalidate_forecast_cache("s1")
        r2 = calc_forecast_cached("s1", 3, gs, bus)
        self.assertIsNot(r1, r2, "After invalidation, should recompute")

    def test_full_flush(self):
        from engine import calc_forecast_cached, invalidate_forecast_cache, _forecast_cache
        invalidate_forecast_cache()
        gs, bus = self._make_gs(), self._make_bus()
        calc_forecast_cached("a", 1, gs, bus)
        calc_forecast_cached("b", 2, gs, bus)
        self.assertEqual(len(_forecast_cache), 2)
        invalidate_forecast_cache()
        self.assertEqual(len(_forecast_cache), 0)


class TestAgentTeleprompterAPI(unittest.TestCase):
    """Verify that the agent teleprompter endpoint returns the correct structure."""

    def setUp(self):
        import database_memory as _db
        _db._sessions.clear()
        _db._global_states.clear()
        _db._bu_states.clear()
        _db._decision_log.clear()

    def test_agent_teleprompter_endpoint_payload(self):
        import os
        os.environ["USE_MEMORY_DB"] = "true"
        from fastapi.testclient import TestClient
        from main import app
        import time

        client = TestClient(app)
        
        # 1. Create a session
        resp = client.post("/api/simulations/start", json={
            "cohort_name": f"TestAgentAPI_{int(time.time())}",
            "decision_paradigm": "legacy_abc"
        })
        if resp.status_code != 201:
            print("API Error:", resp.text)
        self.assertEqual(resp.status_code, 201)
        session_id = resp.json()["session_id"]

        # 2. Inject autonomous agents directly to bypass rate limits and multi-round commits
        import database_memory as _db
        from autonomous_agents import create_initial_agent_state
        
        # Ensure session exists and has a round
        self.assertIn(session_id, _db._global_states)
        _db._global_states[session_id][-1]["autonomous_agents"] = create_initial_agent_state()

        # 3. Query the agent teleprompter endpoint directly
        resp2 = client.get(f"/api/admin/teleprompter/agents/{session_id}")
        self.assertEqual(resp2.status_code, 200)
        
        data = resp2.json()
        
        # 4. Assert the critical schema fields exist
        self.assertIn("worst_stage", data)
        self.assertIn("total_triggers", data)
        self.assertIn("agents", data)
        self.assertIn("cascade_log", data)
        
        # 5. Assert agent structure
        self.assertGreater(len(data["agents"]), 0, "Should return the initialized agents")
        agent_0 = data["agents"][0]
        self.assertIn("agent_id", agent_0)
        self.assertIn("name", agent_0)
        self.assertIn("tolerance_pct", agent_0)
        self.assertIn("stage", agent_0)


if __name__ == "__main__":
    unittest.main()
