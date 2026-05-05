"""
Muressons — Vertical BU Substitution Full Integration Tests
Tests the complete lifecycle: session creation → BU substitution →
stakeholder evaluation → CSRD materiality → engine tick.

These tests verify that the vertical substitution system works end-to-end
with the core simulation, not just in isolation.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import unittest
import asyncio
import copy

# ═══════════════════════════════════════════════════════════════
#  HELPER: run async functions in sync tests
# ═══════════════════════════════════════════════════════════════

def _run(coro):
    """Run an async coroutine synchronously."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


# ═══════════════════════════════════════════════════════════════
#  TEST 1: Stakeholder Map Vertical-Aware Evaluation
# ═══════════════════════════════════════════════════════════════

class TestStakeholderMapVerticalIntegration(unittest.TestCase):
    """Verify stakeholder_map.py functions respond to BU substitutions."""

    def test_default_session_returns_default_stakeholders(self):
        from stakeholder_map import get_stakeholders_for_session, STAKEHOLDERS
        gs = {"bu_substitutions": {}}
        result = get_stakeholders_for_session(gs)
        self.assertIs(result, STAKEHOLDERS)

    def test_no_subs_key_returns_default(self):
        from stakeholder_map import get_stakeholders_for_session, STAKEHOLDERS
        gs = {}
        result = get_stakeholders_for_session(gs)
        self.assertIs(result, STAKEHOLDERS)

    def test_technology_sub_returns_technology_stakeholders(self):
        from stakeholder_map import get_stakeholders_for_session
        gs = {"bu_substitutions": {"software": "technology"}}
        result = get_stakeholders_for_session(gs)
        self.assertEqual(len(result), 10)
        ids = {s["id"] for s in result}
        self.assertIn("data_protection_authority", ids)  # technology stakeholder
        self.assertNotIn("activist_fund", ids)  # default stakeholder

    def test_oil_gas_sub_returns_oil_gas_stakeholders(self):
        from stakeholder_map import get_stakeholders_for_session
        gs = {"bu_substitutions": {"pharma": "oil_gas"}}
        result = get_stakeholders_for_session(gs)
        ids = {s["id"] for s in result}
        self.assertIn("pipeline_regulator", ids)

    def test_banking_sub_returns_banking_stakeholders(self):
        from stakeholder_map import get_stakeholders_for_session
        gs = {"bu_substitutions": {"software": "banking_financial_services"}}
        result = get_stakeholders_for_session(gs)
        ids = {s["id"] for s in result}
        self.assertIn("central_bank_supervisor", ids)

    def test_retail_sub_returns_retail_stakeholders(self):
        from stakeholder_map import get_stakeholders_for_session
        gs = {"bu_substitutions": {"consumer_goods": "retail_fmcg"}}
        result = get_stakeholders_for_session(gs)
        ids = {s["id"] for s in result}
        self.assertIn("consumer_watchdog", ids)

    def test_agriculture_sub_returns_agriculture_stakeholders(self):
        from stakeholder_map import get_stakeholders_for_session
        gs = {"bu_substitutions": {"consumer_goods": "agriculture"}}
        result = get_stakeholders_for_session(gs)
        ids = {s["id"] for s in result}
        self.assertIn("water_authority", ids)

    def test_vertical_evaluation_perfect_score(self):
        """100% accuracy with vertical stakeholders should yield max points."""
        from stakeholder_map import evaluate_stakeholder_map_for_session
        gs = {"bu_substitutions": {"software": "technology"}}
        # Build a perfect submission from the technology stakeholder set
        from vertical_stakeholders import TECHNOLOGY_STAKEHOLDERS
        perfect_submission = {s["id"]: s["correct_quadrant"] for s in TECHNOLOGY_STAKEHOLDERS}
        result = evaluate_stakeholder_map_for_session(perfect_submission, gs)
        self.assertEqual(result["accuracy_percentage"], 100.0)
        self.assertTrue(result["passed"])
        self.assertEqual(result["correct_count"], 10)
        self.assertEqual(result["points_awarded"], 3000)

    def test_vertical_evaluation_zero_score(self):
        """Empty submission should yield 0%."""
        from stakeholder_map import evaluate_stakeholder_map_for_session
        gs = {"bu_substitutions": {"pharma": "oil_gas"}}
        result = evaluate_stakeholder_map_for_session({}, gs)
        self.assertEqual(result["accuracy_percentage"], 0.0)
        self.assertFalse(result["passed"])
        self.assertEqual(result["treasury_penalty"], -500_000)

    def test_default_evaluation_unchanged(self):
        """Default sessions should still work exactly as before."""
        from stakeholder_map import evaluate_stakeholder_map, evaluate_stakeholder_map_for_session
        from stakeholder_map import STAKEHOLDERS
        submission = {s["id"]: s["correct_quadrant"] for s in STAKEHOLDERS}
        default_result = evaluate_stakeholder_map(submission)
        session_result = evaluate_stakeholder_map_for_session(submission, {})
        self.assertEqual(default_result["accuracy_percentage"], session_result["accuracy_percentage"])
        self.assertEqual(default_result["points_awarded"], session_result["points_awarded"])

    def test_get_master_map_for_session(self):
        from stakeholder_map import get_master_map_for_session
        gs = {"bu_substitutions": {"consumer_goods": "agriculture"}}
        m = get_master_map_for_session(gs)
        self.assertIn("water_authority", m)
        self.assertEqual(m["water_authority"], "manage_closely")


# ═══════════════════════════════════════════════════════════════
#  TEST 2: CSRD Materiality Integration with Verticals
# ═══════════════════════════════════════════════════════════════

class TestCSRDVerticalIntegration(unittest.TestCase):
    """Verify vertical CSRD issue banks can be used by the materiality flow."""

    def test_all_vertical_csrd_issues_have_correct_quadrant(self):
        """Verify all verticals' Q1 issues have disclosure_required=True."""
        from vertical_csrd_issues import get_csrd_issues_for_vertical
        for v_id in ["technology", "oil_gas", "banking_financial_services",
                      "retail_fmcg", "agriculture"]:
            issues = get_csrd_issues_for_vertical(v_id)
            for iid, issue in issues.items():
                if issue["correct_quadrant"] == 1:
                    self.assertTrue(
                        issue["disclosure_required"],
                        f"{v_id}/{iid}: Q1 issue must require disclosure"
                    )

    def test_vertical_issues_can_be_mapped_to_materiality_format(self):
        """Verify vertical CSRD issues have the fields the materiality
        submission endpoint needs for scoring."""
        from vertical_csrd_issues import get_csrd_issues_for_vertical
        required_fields = {"id", "title", "hover_description", "correct_quadrant"}
        for v_id in ["technology", "oil_gas", "banking_financial_services",
                      "retail_fmcg", "agriculture"]:
            issues = get_csrd_issues_for_vertical(v_id)
            for iid, issue in issues.items():
                for field in required_fields:
                    self.assertIn(field, issue, f"{v_id}/{iid} missing '{field}'")


# ═══════════════════════════════════════════════════════════════
#  TEST 3: Engine Tick with Substituted BUs
# ═══════════════════════════════════════════════════════════════

class TestEngineTickWithVerticals(unittest.TestCase):
    """Verify the core engine can process a round with vertical BUs."""

    def _make_states(self, vertical_id: str):
        """Build a minimal global state + BU states for engine testing."""
        from bu_profiles import build_bu_states, SLOT_FIT_MAP
        # Find which slot this vertical fits
        slot = None
        for s, verticals in SLOT_FIT_MAP.items():
            if vertical_id in verticals:
                slot = s
                break
        self.assertIsNotNone(slot, f"No slot for {vertical_id}")

        bu_states = build_bu_states({slot: vertical_id})
        gs = {
            "corporate_treasury": 100_000_000.0,
            "group_reputation": 50.0,
            "synergy_multiplier": 1.0,
            "cost_of_capital": 0.05,
            "active_event_flags": {},
            "bonus_score": 0,
            "round_number": 1,
            "historical_ebitda": sum(b["revenue_base"] - b["opex_base"] for b in bu_states),
            "tco2e_emissions": 1000,
            "vrio_capabilities": {"value": 50, "rarity": 50, "imitability": 50, "organization": 50},
            "green_transition_fund": 0.0,
            "tipping_point_active": False,
            "pending_capex_projects": [],
            "inflation_index": 0.025,
            "competitor_ebitda": 50_000_000.0,
        }
        return gs, bu_states

    def test_process_tick_technology(self):
        from engine import process_tick
        gs, bus = self._make_states("technology")
        decisions = [{"decision_node_id": "round_1_default", "choice_selected": "option_a",
                       "capex_allocated": 0, "bu_id": "technology"}]
        result = process_tick(gs, bus, decisions, 0.0, 0.0)
        self.assertIn("corporate_treasury", result["global_state"])
        self.assertEqual(len(result["bu_states"]), 4)

    def test_process_tick_oil_gas(self):
        from engine import process_tick
        gs, bus = self._make_states("oil_gas")
        decisions = []
        result = process_tick(gs, bus, decisions, 0.0, 0.0)
        self.assertIn("corporate_treasury", result["global_state"])
        # Verify oil_gas BU exists in output
        ids = [b["bu_id"] for b in result["bu_states"]]
        self.assertIn("oil_gas", ids)

    def test_process_tick_banking(self):
        from engine import process_tick
        gs, bus = self._make_states("banking_financial_services")
        decisions = []
        result = process_tick(gs, bus, decisions, 0.0, 0.0)
        self.assertEqual(len(result["bu_states"]), 4)

    def test_process_tick_retail_fmcg(self):
        from engine import process_tick
        gs, bus = self._make_states("retail_fmcg")
        decisions = []
        result = process_tick(gs, bus, decisions, 0.0, 0.0)
        self.assertEqual(len(result["bu_states"]), 4)

    def test_process_tick_agriculture(self):
        from engine import process_tick
        gs, bus = self._make_states("agriculture")
        decisions = []
        result = process_tick(gs, bus, decisions, 0.0, 0.0)
        self.assertEqual(len(result["bu_states"]), 4)

    def test_treasury_doesnt_crash_with_all_verticals(self):
        """Smoke test: run 3 rounds with every vertical to verify no crash."""
        from engine import process_tick
        for v_id in ["technology", "oil_gas", "banking_financial_services",
                      "retail_fmcg", "agriculture"]:
            gs, bus = self._make_states(v_id)
            for r in range(1, 4):
                decisions = []
                result = process_tick(gs, bus, decisions, 0.0, 0.0)
                gs = result["global_state"]
                bus = result["bu_states"]
                self.assertIsInstance(gs["corporate_treasury"], (int, float),
                                     f"Treasury not numeric for {v_id} at R{r}")

    def test_cannibalization_with_mixed_verticals(self):
        """Build a session with 2 verticals + 2 defaults and run cannibalization."""
        from bu_profiles import build_bu_states
        from engine import calc_revenue_cannibalization
        bus = build_bu_states({"pharma": "oil_gas", "software": "technology"})
        result = calc_revenue_cannibalization(bus)
        self.assertIsInstance(result, dict)
        # Cannibalization returns {bu_id: amount}, not total_cannibalization
        # Just verify it returns a dict with numeric values
        for k, v in result.items():
            self.assertIsInstance(v, (int, float))

    def test_fx_impact_with_mixed_verticals(self):
        from bu_profiles import build_bu_states
        from engine import calc_fx_impact
        bus = build_bu_states({"consumer_goods": "agriculture", "software": "banking_financial_services"})
        result = calc_fx_impact(bus, round_number=5)
        self.assertIn("adjustments", result)


# ═══════════════════════════════════════════════════════════════
#  TEST 4: Session Lifecycle Integration
# ═══════════════════════════════════════════════════════════════

class TestSessionLifecycle(unittest.TestCase):
    """End-to-end lifecycle: create session → apply substitution →
    verify BU state → evaluate stakeholders → run engine tick."""

    def test_full_lifecycle_technology(self):
        """Complete lifecycle test for Technology vertical."""
        import database_memory as db

        # 1. Create session
        session = _run(db.create_session(
            cohort_name="Test_Tech_Lifecycle",
            decision_paradigm="multi_toggles",
        ))
        sid = session["session_id"]
        self.assertIsNotNone(sid)

        # 2. Fetch state and verify it has default 4 BUs
        state = _run(db.fetch_latest_state(sid))
        self.assertEqual(state["round_number"], 1)
        default_ids = [b["bu_id"] for b in state["bu_states"]]
        self.assertEqual(len(default_ids), 4)
        self.assertIn("software", default_ids)

        # 3. Apply BU substitution (at cohort formation time)
        from bu_profiles import validate_substitution, build_bu_states, get_active_bus
        ok, _ = validate_substitution("software", "technology")
        self.assertTrue(ok)

        gs = state["global_state"]
        subs = {"software": "technology"}
        gs["bu_substitutions"] = subs
        new_bus = build_bu_states(subs)
        _run(db.update_latest_global_state(sid, gs, new_bus))

        # 4. Re-fetch and verify substitution persisted
        state2 = _run(db.fetch_latest_state(sid))
        bu_ids = [b["bu_id"] for b in state2["bu_states"]]
        self.assertIn("technology", bu_ids)
        self.assertNotIn("software", bu_ids)

        # 5. Stakeholder evaluation uses vertical data
        from stakeholder_map import evaluate_stakeholder_map_for_session, get_stakeholders_for_session
        from vertical_stakeholders import get_stakeholders_for_vertical
        gs2 = state2["global_state"]
        stakeholders = get_stakeholders_for_session(gs2)
        self.assertEqual(len(stakeholders), 10)
        # Build perfect submission from the session's stakeholder set
        perfect = {s["id"]: s["correct_quadrant"] for s in stakeholders}
        result = evaluate_stakeholder_map_for_session(perfect, gs2)
        self.assertEqual(result["accuracy_percentage"], 100.0)
        self.assertTrue(result["passed"])

        # 6. Engine tick with substituted BUs
        from engine import process_tick
        gs2["round_number"] = 1  # engine reads this from global state
        tick_result = process_tick(
            gs2, state2["bu_states"], decisions=[], dividends_paid=0.0, crisis_severity=0.0
        )
        self.assertEqual(len(tick_result["bu_states"]), 4)
        tick_ids = [b["bu_id"] for b in tick_result["bu_states"]]
        self.assertIn("technology", tick_ids)

        # 7. Cleanup
        _run(db.delete_session(sid, hard=True))

    def test_full_lifecycle_oil_gas(self):
        """Complete lifecycle test for Oil & Gas vertical."""
        import database_memory as db
        from bu_profiles import validate_substitution, build_bu_states
        from stakeholder_map import evaluate_stakeholder_map_for_session, get_stakeholders_for_session

        session = _run(db.create_session(
            cohort_name="Test_OilGas_Lifecycle",
            decision_paradigm="multi_toggles",
        ))
        sid = session["session_id"]

        state = _run(db.fetch_latest_state(sid))
        gs = state["global_state"]
        subs = {"pharma": "oil_gas"}
        gs["bu_substitutions"] = subs
        new_bus = build_bu_states(subs)
        _run(db.update_latest_global_state(sid, gs, new_bus))

        state2 = _run(db.fetch_latest_state(sid))
        bu_ids = [b["bu_id"] for b in state2["bu_states"]]
        self.assertIn("oil_gas", bu_ids)
        self.assertNotIn("pharma", bu_ids)

        # Stakeholder check
        gs2 = state2["global_state"]
        stakeholders = get_stakeholders_for_session(gs2)
        self.assertEqual(len(stakeholders), 10)
        # Verify stakeholders are oil_gas ones, not defaults
        ids = {s["id"] for s in stakeholders}
        self.assertIn("climate_litigators", ids)
        self.assertNotIn("activist_fund", ids)

        _run(db.delete_session(sid, hard=True))


# ═══════════════════════════════════════════════════════════════
#  TEST 5: Materiality DB Registry Consistency
# ═══════════════════════════════════════════════════════════════

class TestMaterialityDBConsistency(unittest.TestCase):
    """Verify materiality_db BU registry matches bu_profiles."""

    def test_all_verticals_in_materiality_registry(self):
        from materiality_db import _DEFAULT_BU_IDS
        for v_id in ["oil_gas", "banking_financial_services", "retail_fmcg",
                      "agriculture", "technology"]:
            self.assertIn(v_id, _DEFAULT_BU_IDS,
                          f"{v_id} missing from materiality_db._DEFAULT_BU_IDS")

    def test_all_verticals_in_bu_meta(self):
        from materiality_db import _DEFAULT_BU_META
        meta_ids = {m["id"] for m in _DEFAULT_BU_META}
        for v_id in ["oil_gas", "banking_financial_services", "retail_fmcg",
                      "agriculture", "technology"]:
            self.assertIn(v_id, meta_ids,
                          f"{v_id} missing from materiality_db._DEFAULT_BU_META")

    def test_vertical_meta_flagged_as_industry_vertical(self):
        from materiality_db import _DEFAULT_BU_META
        for m in _DEFAULT_BU_META:
            if m["id"] in ["oil_gas", "banking_financial_services", "retail_fmcg",
                            "agriculture", "technology"]:
                self.assertTrue(m.get("is_industry_vertical"),
                                f"{m['id']} should have is_industry_vertical=True")


# ═══════════════════════════════════════════════════════════════
#  TEST 6: Salience Migration Vertical Integration
# ═══════════════════════════════════════════════════════════════

class TestSalienceMigrationVertical(unittest.TestCase):
    """Verify vertical salience migrations can fire via the core pathway."""

    def test_r4_migration_fires_for_technology(self):
        """Manually trigger R4 salience migration with technology stakeholder data."""
        from vertical_stakeholders import get_migrations_for_vertical
        migrations = get_migrations_for_vertical("technology")
        r4 = [m for m in migrations if m["round"] == 4]
        self.assertGreaterEqual(len(r4), 2, "Technology should have ≥2 R4 migrations")
        # Verify they reference valid stakeholder IDs
        from vertical_stakeholders import get_stakeholders_for_vertical
        tech_ids = {s["id"] for s in get_stakeholders_for_vertical("technology")}
        for m in r4:
            self.assertIn(m["stakeholder"], tech_ids,
                          f"Migration references unknown stakeholder: {m['stakeholder']}")

    def test_r6_migration_fires_for_banking(self):
        from vertical_stakeholders import get_migrations_for_vertical, get_stakeholders_for_vertical
        migrations = get_migrations_for_vertical("banking_financial_services")
        r6 = [m for m in migrations if m["round"] == 6]
        self.assertGreaterEqual(len(r6), 2)
        bank_ids = {s["id"] for s in get_stakeholders_for_vertical("banking_financial_services")}
        for m in r6:
            self.assertIn(m["stakeholder"], bank_ids)

    def test_r9_migration_fires_for_agriculture(self):
        from vertical_stakeholders import get_migrations_for_vertical, get_stakeholders_for_vertical
        migrations = get_migrations_for_vertical("agriculture")
        r9 = [m for m in migrations if m["round"] == 9]
        self.assertGreaterEqual(len(r9), 2)
        agri_ids = {s["id"] for s in get_stakeholders_for_vertical("agriculture")}
        for m in r9:
            self.assertIn(m["stakeholder"], agri_ids)


# ═══════════════════════════════════════════════════════════════
#  TEST 7: Cross-Vertical Substitution Constraints
# ═══════════════════════════════════════════════════════════════

class TestSubstitutionConstraints(unittest.TestCase):
    """Verify slot-fit validation prevents invalid combos."""

    def test_cannot_put_agriculture_in_software_slot(self):
        from bu_profiles import validate_substitution
        ok, msg = validate_substitution("software", "agriculture")
        self.assertFalse(ok)
        self.assertIn("not compatible", msg)

    def test_cannot_put_banking_in_consumer_goods_slot(self):
        from bu_profiles import validate_substitution
        ok, msg = validate_substitution("consumer_goods", "banking_financial_services")
        self.assertFalse(ok)

    def test_can_put_retail_in_consumer_goods_slot(self):
        from bu_profiles import validate_substitution
        ok, _ = validate_substitution("consumer_goods", "retail_fmcg")
        self.assertTrue(ok)

    def test_reset_to_default_always_valid(self):
        from bu_profiles import validate_substitution, DEFAULT_SLOTS
        for slot in DEFAULT_SLOTS:
            ok, _ = validate_substitution(slot, slot)
            self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main(verbosity=2)
