"""
Muressons — Regulatory Sandbox Controller Tests
Validates the full middleware intercept, Pigouvian penalties,
Carbon Minsky Moment, Coasian friction, polycentric governance,
exogenous events, and agent cross-wiring.
"""
import sys, os, unittest, copy
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from regulatory_sandbox import (
    create_sandbox_state,
    activate_regulation,
    apply_sandbox_effects,
    calc_pigouvian_penalty_per_bu,
    check_carbon_minsky_moment,
    calc_coasian_friction,
    calc_polycentric_burden,
    intercept_state_transition,
    crosswire_sandbox_to_agents,
    trigger_exogenous_event,
    EXOGENOUS_EVENTS,
    REGULATORY_INSTRUMENTS,
)


def _make_sandbox(active=True, regulations=None):
    s = create_sandbox_state()
    s["sandbox_mode"] = active
    if regulations:
        s["active_regulations"] = regulations
    return s


def _make_gs(**overrides):
    gs = {
        "corporate_treasury": 25_000_000,
        "group_reputation": 50,
        "cost_of_capital": 0.05,
        "biodiversity_state": {"ecosystem_health_index": 50, "water_stress_index": 0.4},
        "autonomous_agents": {
            "agents": {
                "the_regulator": {
                    "tolerance": 75,
                    "escalation_stage": "dormant",
                    "triggered_round": None,
                },
                "the_institutional_investor": {
                    "tolerance": 80,
                    "escalation_stage": "dormant",
                    "triggered_round": None,
                },
                "the_community_activist": {
                    "tolerance": 65,
                    "escalation_stage": "dormant",
                    "triggered_round": None,
                },
                "the_journalist": {
                    "tolerance": 72,
                    "escalation_stage": "dormant",
                    "triggered_round": None,
                },
            },
            "cascade_log": [],
            "total_triggers": 0,
        },
    }
    gs.update(overrides)
    return gs


def _make_bus(count=4):
    templates = [
        {"bu_id": "pharma", "revenue_base": 18_000_000, "opex_base": 11_500_000,
         "carbon_intensity": 45, "natural_capital_debt": 5000,
         "social_license_score": 70, "governance_risk_score": 15, "water_dependency": 0.6},
        {"bu_id": "electronics", "revenue_base": 22_000_000, "opex_base": 14_000_000,
         "carbon_intensity": 60, "natural_capital_debt": 3800,
         "social_license_score": 65, "governance_risk_score": 25, "water_dependency": 0.8},
        {"bu_id": "consumer_goods", "revenue_base": 15_000_000, "opex_base": 9_000_000,
         "carbon_intensity": 30, "natural_capital_debt": 2100,
         "social_license_score": 78, "governance_risk_score": 10, "water_dependency": 0.3},
        {"bu_id": "software", "revenue_base": 20_000_000, "opex_base": 8_000_000,
         "carbon_intensity": 10, "natural_capital_debt": 500,
         "social_license_score": 85, "governance_risk_score": 5, "water_dependency": 0.1},
    ]
    return [copy.deepcopy(t) for t in templates[:count]]


class TestPigouvianPenalty(unittest.TestCase):
    """Verify per-BU Pigouvian penalty calculation."""

    def test_penalty_scales_with_ci(self):
        high_ci = {"bu_id": "electronics", "carbon_intensity": 60, "revenue_base": 22_000_000}
        low_ci = {"bu_id": "software", "carbon_intensity": 10, "revenue_base": 20_000_000}
        pen_high, _ = calc_pigouvian_penalty_per_bu(high_ci, 85)
        pen_low, _ = calc_pigouvian_penalty_per_bu(low_ci, 85)
        self.assertGreater(pen_high, pen_low)

    def test_penalty_at_85_per_ton(self):
        bu = {"bu_id": "electronics", "carbon_intensity": 60, "revenue_base": 22_000_000}
        penalty, diag = calc_pigouvian_penalty_per_bu(bu, 85)
        # 60 × 22M / 1M = 1320 tonnes; × $85 = $112,200
        self.assertEqual(diag["estimated_tonnes_co2e"], 1320.0)
        self.assertEqual(penalty, 112200.0)
        self.assertIn("Pigou", diag["theory"])

    def test_zero_ci_zero_penalty(self):
        bu = {"bu_id": "clean", "carbon_intensity": 0, "revenue_base": 10_000_000}
        penalty, _ = calc_pigouvian_penalty_per_bu(bu, 100)
        self.assertEqual(penalty, 0)


class TestCarbonMinskyMoment(unittest.TestCase):
    """Verify Carbon Minsky Moment trigger logic."""

    def test_below_threshold_no_trigger(self):
        bu = {"bu_id": "pharma", "natural_capital_debt": 150}
        triggered, diag = check_carbon_minsky_moment(bu, ncd_threshold=200)
        self.assertFalse(triggered)
        self.assertEqual(diag["bps_increase"], 0)

    def test_above_threshold_triggers(self):
        bu = {"bu_id": "electronics", "natural_capital_debt": 300}
        triggered, diag = check_carbon_minsky_moment(bu, ncd_threshold=200, bps_increase=200)
        self.assertTrue(triggered)
        self.assertEqual(diag["bps_increase"], 200)
        self.assertAlmostEqual(diag["interest_rate_increase"], 0.02)

    def test_exact_threshold_no_trigger(self):
        bu = {"bu_id": "pharma", "natural_capital_debt": 200}
        triggered, _ = check_carbon_minsky_moment(bu, ncd_threshold=200)
        self.assertFalse(triggered, "Exact threshold should NOT trigger (> not >=)")


class TestCoasianFriction(unittest.TestCase):
    """Verify Coasian property rights friction."""

    def test_low_water_stress_low_friction(self):
        bu = {"bu_id": "software", "water_dependency": 0.1, "opex_base": 8_000_000}
        cost, diag = calc_coasian_friction(bu, water_stress=0.3)
        self.assertGreater(cost, 0)
        self.assertLess(diag["friction_rate"], 0.05)

    def test_high_water_dep_high_friction(self):
        bu = {"bu_id": "electronics", "water_dependency": 0.8, "opex_base": 14_000_000}
        cost, diag = calc_coasian_friction(bu, water_stress=0.7)
        self.assertGreater(diag["friction_rate"], 0.03)

    def test_legal_dispute_doubles_friction(self):
        bu = {"bu_id": "pharma", "water_dependency": 0.6, "opex_base": 11_500_000}
        _, diag_no_legal = calc_coasian_friction(bu, 0.5, False)
        _, diag_legal = calc_coasian_friction(bu, 0.5, True)
        self.assertAlmostEqual(
            diag_legal["friction_rate"],
            min(diag_no_legal["friction_rate"] * 2.0, 0.20),
            places=4,
        )

    def test_friction_capped_at_20_pct(self):
        bu = {"bu_id": "test", "water_dependency": 1.0, "opex_base": 10_000_000}
        _, diag = calc_coasian_friction(bu, water_stress=1.0, legal_dispute_active=True)
        self.assertLessEqual(diag["friction_rate"], 0.20)


class TestPolycentricBurden(unittest.TestCase):
    """Verify polycentric asymmetric burden calculation."""

    def test_high_ci_gets_higher_burden(self):
        high_ci = {"bu_id": "electronics", "carbon_intensity": 60, "water_dependency": 0.8, "revenue_base": 22_000_000}
        low_ci = {"bu_id": "software", "carbon_intensity": 10, "water_dependency": 0.1, "revenue_base": 20_000_000}
        b_high, _ = calc_polycentric_burden(high_ci, {})
        b_low, _ = calc_polycentric_burden(low_ci, {})
        self.assertGreater(b_high, b_low, "Electronics should bear higher polycentric burden")

    def test_burden_proportional_to_revenue(self):
        bu = {"bu_id": "test", "carbon_intensity": 50, "water_dependency": 0.5, "revenue_base": 10_000_000}
        burden, diag = calc_polycentric_burden(bu, {})
        self.assertGreater(burden, 0)
        self.assertIn("Ostrom", diag["theory"])


class TestMiddlewareIntercept(unittest.TestCase):
    """Verify the full middleware intercept pipeline."""

    def test_inactive_sandbox_returns_empty(self):
        sandbox = _make_sandbox(active=False)
        gs = _make_gs()
        bus = _make_bus()
        result = intercept_state_transition(sandbox, gs, bus, {}, 7)
        self.assertEqual(result, {})

    def test_active_sandbox_with_carbon_tax(self):
        sandbox = _make_sandbox(active=True, regulations=[{
            "instrument_id": "carbon_tax",
            "parameters": {"rate_per_tonne": 85, "annual_escalation_pct": 5},
            "activated_round": 5,
        }])
        gs = _make_gs()
        bus = _make_bus()
        original_opex = [bu["opex_base"] for bu in bus]

        result = intercept_state_transition(sandbox, gs, bus, {}, 7)

        self.assertEqual(len(result["pigouvian_penalties"]), 4)
        # OPEX should have increased for all BUs
        for i, bu in enumerate(bus):
            self.assertGreater(bu["opex_base"], original_opex[i])

    def test_minsky_fires_when_ncd_exceeds_threshold(self):
        sandbox = _make_sandbox(active=True, regulations=[{
            "instrument_id": "carbon_tax",
            "parameters": {"rate_per_tonne": 85, "annual_escalation_pct": 5},
            "activated_round": 5,
        }])
        gs = _make_gs()
        bus = _make_bus()
        # Push electronics NCD above threshold
        bus[1]["natural_capital_debt"] = 300

        result = intercept_state_transition(sandbox, gs, bus, {}, 7)

        minsky_electronics = next(
            m for m in result["minsky_triggers"] if m["bu_id"] == "electronics"
        )
        self.assertTrue(minsky_electronics["triggered"])
        self.assertGreater(bus[1]["natural_capital_debt"], 300)


class TestExogenousEvents(unittest.TestCase):
    """Verify exogenous event trigger logic."""

    def test_carbon_minsky_fires_in_r7_r9(self):
        for event_id, cfg in EXOGENOUS_EVENTS.items():
            if event_id == "carbon_minsky_moment":
                self.assertIn(7, cfg["trigger_rounds"])
                self.assertIn(9, cfg["trigger_rounds"])

    def test_polycentric_water_shock_only_r8(self):
        cfg = EXOGENOUS_EVENTS["polycentric_water_shock"]
        self.assertEqual(cfg["trigger_rounds"], [8])

    def test_god_mode_force_trigger(self):
        sandbox = _make_sandbox(active=True)
        gs = _make_gs()
        bus = _make_bus()
        events = {}

        result = trigger_exogenous_event(
            "carbon_minsky_moment", sandbox, gs, bus, events, 7
        )
        self.assertIn("event_id", result)
        self.assertTrue(result.get("forced", False) or "breaching_bus" in result)
        self.assertTrue(sandbox.get("exogenous_carbon_minsky_moment_fired"))

    def test_double_trigger_blocked(self):
        sandbox = _make_sandbox(active=True)
        sandbox["exogenous_csddd_enforcement_fired"] = 7
        gs = _make_gs()
        bus = _make_bus()

        result = trigger_exogenous_event(
            "csddd_enforcement", sandbox, gs, bus, {}, 8
        )
        self.assertIn("error", result)

    def test_csddd_fires_on_low_reputation(self):
        import random
        random.seed(42)  # Deterministic
        sandbox = _make_sandbox(active=True)
        gs = _make_gs(group_reputation=30)
        bus = _make_bus()
        events = {}

        result = trigger_exogenous_event(
            "csddd_enforcement", sandbox, gs, bus, events, 8
        )
        # Should fire (rep=30 < 40 threshold)
        self.assertNotIn("error", result)
        self.assertLess(gs["corporate_treasury"], 25_000_000)


class TestAgentCrosswiring(unittest.TestCase):
    """Verify sandbox → autonomous agent cross-wiring."""

    def test_inactive_sandbox_no_triggers(self):
        sandbox = _make_sandbox(active=False)
        gs = _make_gs()
        result = crosswire_sandbox_to_agents(sandbox, gs, _make_bus(), {}, 7)
        self.assertEqual(result, {})

    def test_eleanor_carson_fires_on_high_governance_risk(self):
        sandbox = _make_sandbox(active=True)
        gs = _make_gs()
        bus = _make_bus()
        # Push governance risk above 55
        for bu in bus:
            bu["governance_risk_score"] = 60
        events = {}

        result = crosswire_sandbox_to_agents(sandbox, gs, bus, events, 7)

        triggers = result.get("agent_crosswire_triggers", [])
        self.assertTrue(any(t["agent"] == "the_regulator" for t in triggers))
        # Treasury should be reduced by 4% of total revenue
        self.assertLess(gs["corporate_treasury"], 25_000_000)

    def test_marcus_fires_on_negative_ebitda(self):
        sandbox = _make_sandbox(active=True)
        gs = _make_gs()
        bus = _make_bus()
        # Make EBITDA negative by inflating OPEX
        for bu in bus:
            bu["opex_base"] = bu["revenue_base"] + 1_000_000
        events = {}

        result = crosswire_sandbox_to_agents(sandbox, gs, bus, events, 7)

        triggers = result.get("agent_crosswire_triggers", [])
        self.assertTrue(any(t["agent"] == "the_institutional_investor" for t in triggers))
        # 8% treasury hit
        self.assertLess(gs["corporate_treasury"], 25_000_000)

    def test_no_double_trigger_after_agent_fired(self):
        sandbox = _make_sandbox(active=True)
        gs = _make_gs()
        gs["autonomous_agents"]["agents"]["the_regulator"]["triggered_round"] = 6
        bus = _make_bus()
        for bu in bus:
            bu["governance_risk_score"] = 70
        events = {}

        result = crosswire_sandbox_to_agents(sandbox, gs, bus, events, 7)

        triggers = result.get("agent_crosswire_triggers", [])
        self.assertFalse(any(t["agent"] == "the_regulator" for t in triggers))

    def test_cascade_multiplier_regulator_to_journalist(self):
        """When Eleanor Carson fires, Jay Buffet loses 10 tolerance."""
        sandbox = _make_sandbox(active=True)
        gs = _make_gs()
        bus = _make_bus()
        for bu in bus:
            bu["governance_risk_score"] = 60  # push avg > 55
        events = {}

        original_journalist_tol = gs["autonomous_agents"]["agents"]["the_journalist"]["tolerance"]
        result = crosswire_sandbox_to_agents(sandbox, gs, bus, events, 7)

        triggers = result.get("agent_crosswire_triggers", [])
        # Carson should fire
        self.assertTrue(any(t["agent"] == "the_regulator" for t in triggers))
        # Cascade multiplier should fire on journalist
        journalist_cascades = [t for t in triggers if t["agent"] == "the_journalist"]
        self.assertEqual(len(journalist_cascades), 1)
        self.assertEqual(
            journalist_cascades[0]["cascade_source"], "the_regulator"
        )
        # Tolerance should drop by exactly 10
        new_tol = gs["autonomous_agents"]["agents"]["the_journalist"]["tolerance"]
        self.assertEqual(new_tol, original_journalist_tol - 10)
        # Narrative event should be injected
        swan_titles = [e["title"] for e in events.get("custom_black_swans", [])]
        self.assertTrue(any("Press Cascade" in t for t in swan_titles))

    def test_cascade_multiplier_skips_triggered_journalist(self):
        """If Jay Buffet already triggered, cascade multiplier does not fire."""
        sandbox = _make_sandbox(active=True)
        gs = _make_gs()
        gs["autonomous_agents"]["agents"]["the_journalist"]["triggered_round"] = 6
        bus = _make_bus()
        for bu in bus:
            bu["governance_risk_score"] = 60
        events = {}

        result = crosswire_sandbox_to_agents(sandbox, gs, bus, events, 7)

        triggers = result.get("agent_crosswire_triggers", [])
        # Carson fires but cascade should NOT fire on already-triggered journalist
        self.assertFalse(any(t["agent"] == "the_journalist" for t in triggers))


class TestExistingSandboxIntegrity(unittest.TestCase):
    """Ensure the new additions don't break existing sandbox functions."""

    def test_create_sandbox_state(self):
        s = create_sandbox_state()
        self.assertFalse(s["sandbox_mode"])
        self.assertEqual(s["active_regulations"], [])

    def test_activate_regulation(self):
        s = create_sandbox_state()
        result = activate_regulation(s, "carbon_tax", {"rate_per_tonne": 85}, 3)
        self.assertNotIn("error", result)
        self.assertEqual(len(s["active_regulations"]), 1)
        self.assertEqual(s["active_regulations"][0]["parameters"]["rate_per_tonne"], 85)

    def test_apply_sandbox_effects_disabled(self):
        s = create_sandbox_state()
        gs = _make_gs()
        bus = _make_bus()
        result = apply_sandbox_effects(s, gs, bus, 5)
        self.assertEqual(result, {})

    def test_instruments_registry_complete(self):
        self.assertIn("carbon_tax", REGULATORY_INSTRUMENTS)
        self.assertIn("emissions_trading", REGULATORY_INSTRUMENTS)
        self.assertIn("mandatory_disclosure", REGULATORY_INSTRUMENTS)
        self.assertIn("due_diligence", REGULATORY_INSTRUMENTS)
        self.assertIn("nature_regulation", REGULATORY_INSTRUMENTS)
        self.assertIn("just_transition_fund", REGULATORY_INSTRUMENTS)


if __name__ == "__main__":
    unittest.main()
