"""
Muressons — BU Substitution Integration Tests
Tests the BU vertical substitution system in isolation.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import unittest
from bu_profiles import (
    BU_PROFILES, DEFAULT_SLOTS, SLOT_FIT_MAP,
    validate_substitution, get_active_bus, build_bu_states,
    VERTICAL_MARKET_OVERLAP, VERTICAL_BLINDSPOT_FLAGS,
)
from vertical_stakeholders import (
    TECHNOLOGY_STAKEHOLDERS, TECHNOLOGY_SALIENCE_MIGRATIONS,
    get_stakeholders_for_vertical, get_migrations_for_vertical,
)
from vertical_csrd_issues import (
    TECHNOLOGY_CSRD_ISSUES, get_csrd_issues_for_vertical,
)


class TestBUProfiles(unittest.TestCase):
    """Test BU profile registry and slot-fit validation."""

    def test_all_profiles_have_required_fields(self):
        required = {"label", "icon", "slot", "revenue_base", "opex_base",
                     "carbon_intensity", "water_dependency", "fx_exposure",
                     "emissions_baseline"}
        for bu_id, profile in BU_PROFILES.items():
            for field in required:
                self.assertIn(field, profile, f"{bu_id} missing '{field}'")

    def test_default_slots_exist_as_profiles(self):
        for slot in DEFAULT_SLOTS:
            self.assertIn(slot, BU_PROFILES)

    def test_slot_fit_only_allows_valid_verticals(self):
        # software slot: banking_financial_services, technology
        ok, _ = validate_substitution("software", "technology")
        self.assertTrue(ok)
        ok, _ = validate_substitution("software", "banking_financial_services")
        self.assertTrue(ok)
        # software slot rejects oil_gas
        ok, msg = validate_substitution("software", "oil_gas")
        self.assertFalse(ok)
        self.assertIn("not compatible", msg)

    def test_pharma_slot_accepts_oil_gas(self):
        ok, _ = validate_substitution("pharma", "oil_gas")
        self.assertTrue(ok)

    def test_consumer_goods_slot_accepts_retail_and_agriculture(self):
        ok, _ = validate_substitution("consumer_goods", "retail_fmcg")
        self.assertTrue(ok)
        ok, _ = validate_substitution("consumer_goods", "agriculture")
        self.assertTrue(ok)

    def test_reset_to_default_always_valid(self):
        for slot in DEFAULT_SLOTS:
            ok, _ = validate_substitution(slot, slot)
            self.assertTrue(ok, f"Reset to default should be valid for {slot}")

    def test_invalid_slot_rejected(self):
        ok, msg = validate_substitution("nonexistent", "technology")
        self.assertFalse(ok)

    def test_get_active_bus_no_subs(self):
        result = get_active_bus()
        self.assertEqual(result, DEFAULT_SLOTS)

    def test_get_active_bus_with_subs(self):
        result = get_active_bus({"software": "technology", "pharma": "oil_gas"})
        self.assertEqual(result, ["oil_gas", "electronics", "consumer_goods", "technology"])

    def test_build_bu_states_default(self):
        states = build_bu_states()
        self.assertEqual(len(states), 4)
        ids = [s["bu_id"] for s in states]
        self.assertEqual(ids, DEFAULT_SLOTS)

    def test_build_bu_states_with_substitution(self):
        states = build_bu_states({"software": "technology"})
        self.assertEqual(len(states), 4)
        ids = [s["bu_id"] for s in states]
        self.assertIn("technology", ids)
        self.assertNotIn("software", ids)
        # Verify technology profile values
        tech = next(s for s in states if s["bu_id"] == "technology")
        self.assertEqual(tech["revenue_base"], 15_000_000)
        self.assertEqual(tech["carbon_intensity"], 15)

    def test_nine_profiles_total(self):
        self.assertEqual(len(BU_PROFILES), 9)

    def test_all_verticals_have_blindspot_flags(self):
        for bu_id in BU_PROFILES:
            self.assertIn(bu_id, VERTICAL_BLINDSPOT_FLAGS,
                          f"{bu_id} missing blindspot flag")


class TestTechnologyStakeholders(unittest.TestCase):
    """Test Technology vertical stakeholder set."""

    def test_correct_count(self):
        self.assertEqual(len(TECHNOLOGY_STAKEHOLDERS), 10)

    def test_quadrant_distribution(self):
        quads = {}
        for s in TECHNOLOGY_STAKEHOLDERS:
            q = s["correct_quadrant"]
            quads[q] = quads.get(q, 0) + 1
        self.assertEqual(quads.get("manage_closely", 0), 2)
        self.assertEqual(quads.get("keep_informed", 0), 3)
        self.assertEqual(quads.get("keep_satisfied", 0), 2)
        self.assertEqual(quads.get("monitor", 0), 3)  # 2 + 1 ambiguous

    def test_ambiguous_stakeholder_exists(self):
        ambiguous = [s for s in TECHNOLOGY_STAKEHOLDERS if s.get("alternate_quadrant")]
        self.assertEqual(len(ambiguous), 1)
        self.assertEqual(ambiguous[0]["id"], "tech_journalist")

    def test_manage_closely_have_tactics(self):
        mc = [s for s in TECHNOLOGY_STAKEHOLDERS if s["correct_quadrant"] == "manage_closely"]
        for s in mc:
            self.assertIn("engagement_tactics", s, f"{s['id']} missing tactics")
            self.assertGreater(len(s["engagement_tactics"]), 0)

    def test_all_have_required_fields(self):
        required = {"id", "name", "icon", "description", "correct_quadrant",
                     "urgency", "legitimacy", "intel_dossier"}
        for s in TECHNOLOGY_STAKEHOLDERS:
            for field in required:
                self.assertIn(field, s, f"{s['id']} missing '{field}'")

    def test_salience_migrations_cover_key_rounds(self):
        rounds = {m["round"] for m in TECHNOLOGY_SALIENCE_MIGRATIONS}
        self.assertIn(4, rounds)
        self.assertIn(6, rounds)
        self.assertIn(9, rounds)

    def test_registry_lookup(self):
        result = get_stakeholders_for_vertical("technology")
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 10)
        self.assertIsNone(get_stakeholders_for_vertical("nonexistent"))


class TestTechnologyCSRDIssues(unittest.TestCase):
    """Test Technology vertical CSRD issue bank."""

    def test_correct_count(self):
        self.assertEqual(len(TECHNOLOGY_CSRD_ISSUES), 20)

    def test_quadrant_distribution(self):
        quads = {}
        for iid, issue in TECHNOLOGY_CSRD_ISSUES.items():
            q = issue["correct_quadrant"]
            quads[q] = quads.get(q, 0) + 1
        self.assertEqual(quads.get(1, 0), 6, "Q1 should have 6 issues")
        self.assertEqual(quads.get(2, 0), 4, "Q2 should have 4 issues")
        self.assertEqual(quads.get(3, 0), 4, "Q3 should have 4 issues")
        self.assertEqual(quads.get(4, 0), 6, "Q4 should have 6 issues")

    def test_q1_issues_have_disclosure_required(self):
        for iid, issue in TECHNOLOGY_CSRD_ISSUES.items():
            if issue["correct_quadrant"] == 1:
                self.assertTrue(issue["disclosure_required"],
                                f"Q1 issue {iid} should require disclosure")

    def test_q4_issues_no_disclosure(self):
        for iid, issue in TECHNOLOGY_CSRD_ISSUES.items():
            if issue["correct_quadrant"] == 4:
                self.assertFalse(issue["disclosure_required"],
                                 f"Q4 issue {iid} should NOT require disclosure")

    def test_all_issues_have_required_fields(self):
        required = {"id", "title", "hover_description", "correct_quadrant",
                     "severity", "likelihood", "time_horizon", "disclosure_required"}
        for iid, issue in TECHNOLOGY_CSRD_ISSUES.items():
            for field in required:
                self.assertIn(field, issue, f"{iid} missing '{field}'")

    def test_electronics_sensitive_issues_exist(self):
        sensitive = [i for i in TECHNOLOGY_CSRD_ISSUES.values()
                     if i.get("electronics_sensitive")]
        self.assertGreater(len(sensitive), 0, "Should have BU-sensitive issues")

    def test_registry_lookup(self):
        result = get_csrd_issues_for_vertical("technology")
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 20)
        self.assertIsNone(get_csrd_issues_for_vertical("nonexistent"))


class TestEngineVerticalParameters(unittest.TestCase):
    """Test that engine parameter tables include vertical BU IDs."""

    def test_fx_exposure_has_all_verticals(self):
        from engine import _BU_FX_EXPOSURE
        for v_id in ["oil_gas", "banking_financial_services", "retail_fmcg",
                      "agriculture", "technology"]:
            self.assertIn(v_id, _BU_FX_EXPOSURE,
                          f"{v_id} missing from _BU_FX_EXPOSURE")

    def test_market_overlap_has_vertical_entries(self):
        from engine import _MARKET_OVERLAP
        all_bus_in_overlap = set()
        for pair in _MARKET_OVERLAP:
            all_bus_in_overlap.update(pair)
        for v_id in ["technology", "banking_financial_services", "retail_fmcg",
                      "agriculture", "oil_gas"]:
            self.assertIn(v_id, all_bus_in_overlap,
                          f"{v_id} missing from _MARKET_OVERLAP")

    def test_cannibalization_works_with_verticals(self):
        from engine import calc_revenue_cannibalization
        bus = [
            {"bu_id": "technology", "revenue_base": 15_000_000},
            {"bu_id": "oil_gas", "revenue_base": 22_000_000},
            {"bu_id": "agriculture", "revenue_base": 9_000_000},
            {"bu_id": "retail_fmcg", "revenue_base": 12_000_000},
        ]
        result = calc_revenue_cannibalization(bus)
        self.assertIsInstance(result, dict)

    def test_fx_works_with_verticals(self):
        from engine import calc_fx_impact
        bus = [
            {"bu_id": "technology", "revenue_base": 15_000_000},
            {"bu_id": "banking_financial_services", "revenue_base": 14_000_000},
        ]
        result = calc_fx_impact(bus, 3)
        self.assertIn("technology", result["adjustments"])
        self.assertIn("banking_financial_services", result["adjustments"])


# ═══════════════════════════════════════════════════════════════
#  ALL-VERTICALS PARAMETRIC TESTS
# ═══════════════════════════════════════════════════════════════

ALL_VERTICAL_IDS = ["technology", "oil_gas", "banking_financial_services",
                     "retail_fmcg", "agriculture"]

STAKEHOLDER_REQUIRED_FIELDS = {"id", "name", "icon", "description",
                                "correct_quadrant", "urgency", "legitimacy",
                                "intel_dossier"}

CSRD_REQUIRED_FIELDS = {"id", "title", "hover_description", "correct_quadrant",
                         "severity", "likelihood", "time_horizon",
                         "disclosure_required"}


class TestAllVerticalStakeholders(unittest.TestCase):
    """Parametric tests across all 5 vertical stakeholder sets."""

    def test_all_verticals_registered(self):
        for v_id in ALL_VERTICAL_IDS:
            result = get_stakeholders_for_vertical(v_id)
            self.assertIsNotNone(result, f"{v_id} stakeholders not registered")

    def test_all_have_10_stakeholders(self):
        for v_id in ALL_VERTICAL_IDS:
            s = get_stakeholders_for_vertical(v_id)
            self.assertEqual(len(s), 10, f"{v_id} has {len(s)} stakeholders, expected 10")

    def test_quadrant_distribution_all_verticals(self):
        for v_id in ALL_VERTICAL_IDS:
            stakeholders = get_stakeholders_for_vertical(v_id)
            quads = {}
            for s in stakeholders:
                q = s["correct_quadrant"]
                quads[q] = quads.get(q, 0) + 1
            self.assertEqual(quads.get("manage_closely", 0), 2,
                             f"{v_id}: expected 2 MC, got {quads.get('manage_closely', 0)}")
            self.assertEqual(quads.get("keep_informed", 0), 3,
                             f"{v_id}: expected 3 KI, got {quads.get('keep_informed', 0)}")
            self.assertEqual(quads.get("keep_satisfied", 0), 2,
                             f"{v_id}: expected 2 KS, got {quads.get('keep_satisfied', 0)}")
            self.assertEqual(quads.get("monitor", 0), 3,
                             f"{v_id}: expected 3 MON, got {quads.get('monitor', 0)}")

    def test_all_have_required_fields(self):
        for v_id in ALL_VERTICAL_IDS:
            for s in get_stakeholders_for_vertical(v_id):
                for field in STAKEHOLDER_REQUIRED_FIELDS:
                    self.assertIn(field, s,
                                  f"{v_id}/{s.get('id','?')} missing '{field}'")

    def test_manage_closely_all_have_tactics(self):
        for v_id in ALL_VERTICAL_IDS:
            mc = [s for s in get_stakeholders_for_vertical(v_id)
                  if s["correct_quadrant"] == "manage_closely"]
            for s in mc:
                self.assertIn("engagement_tactics", s,
                              f"{v_id}/{s['id']} MC stakeholder missing tactics")
                self.assertGreaterEqual(len(s["engagement_tactics"]), 2,
                                        f"{v_id}/{s['id']} needs ≥2 tactics")

    def test_exactly_one_ambiguous_per_vertical(self):
        for v_id in ALL_VERTICAL_IDS:
            ambiguous = [s for s in get_stakeholders_for_vertical(v_id)
                         if s.get("alternate_quadrant")]
            self.assertEqual(len(ambiguous), 1,
                             f"{v_id}: expected 1 ambiguous, got {len(ambiguous)}")

    def test_unique_ids_within_vertical(self):
        for v_id in ALL_VERTICAL_IDS:
            ids = [s["id"] for s in get_stakeholders_for_vertical(v_id)]
            self.assertEqual(len(ids), len(set(ids)),
                             f"{v_id}: duplicate stakeholder IDs")

    def test_unique_ids_across_verticals(self):
        all_ids = []
        for v_id in ALL_VERTICAL_IDS:
            all_ids.extend([s["id"] for s in get_stakeholders_for_vertical(v_id)])
        self.assertEqual(len(all_ids), len(set(all_ids)),
                         "Duplicate stakeholder IDs across verticals")

    def test_salience_migrations_cover_key_rounds(self):
        for v_id in ALL_VERTICAL_IDS:
            migrations = get_migrations_for_vertical(v_id)
            rounds = {m["round"] for m in migrations}
            self.assertIn(4, rounds, f"{v_id}: missing R4 migration")
            self.assertIn(6, rounds, f"{v_id}: missing R6 migration")
            self.assertIn(9, rounds, f"{v_id}: missing R9 migration")

    def test_salience_migrations_minimum_count(self):
        for v_id in ALL_VERTICAL_IDS:
            migrations = get_migrations_for_vertical(v_id)
            self.assertGreaterEqual(len(migrations), 6,
                                    f"{v_id}: expected ≥6 migrations, got {len(migrations)}")


class TestAllVerticalCSRDIssues(unittest.TestCase):
    """Parametric tests across all 5 vertical CSRD issue banks."""

    def test_all_verticals_registered(self):
        for v_id in ALL_VERTICAL_IDS:
            result = get_csrd_issues_for_vertical(v_id)
            self.assertIsNotNone(result, f"{v_id} CSRD issues not registered")

    def test_all_have_20_issues(self):
        for v_id in ALL_VERTICAL_IDS:
            issues = get_csrd_issues_for_vertical(v_id)
            self.assertEqual(len(issues), 20,
                             f"{v_id} has {len(issues)} issues, expected 20")

    def test_quadrant_distribution_all_verticals(self):
        for v_id in ALL_VERTICAL_IDS:
            issues = get_csrd_issues_for_vertical(v_id)
            quads = {}
            for iid, issue in issues.items():
                q = issue["correct_quadrant"]
                quads[q] = quads.get(q, 0) + 1
            self.assertEqual(quads.get(1, 0), 6, f"{v_id}: Q1 should have 6")
            self.assertEqual(quads.get(2, 0), 4, f"{v_id}: Q2 should have 4")
            self.assertEqual(quads.get(3, 0), 4, f"{v_id}: Q3 should have 4")
            self.assertEqual(quads.get(4, 0), 6, f"{v_id}: Q4 should have 6")

    def test_all_have_required_fields(self):
        for v_id in ALL_VERTICAL_IDS:
            for iid, issue in get_csrd_issues_for_vertical(v_id).items():
                for field in CSRD_REQUIRED_FIELDS:
                    self.assertIn(field, issue,
                                  f"{v_id}/{iid} missing '{field}'")

    def test_q1_disclosure_required(self):
        for v_id in ALL_VERTICAL_IDS:
            for iid, issue in get_csrd_issues_for_vertical(v_id).items():
                if issue["correct_quadrant"] == 1:
                    self.assertTrue(issue["disclosure_required"],
                                    f"{v_id}/{iid} Q1 must require disclosure")

    def test_q4_no_disclosure(self):
        for v_id in ALL_VERTICAL_IDS:
            for iid, issue in get_csrd_issues_for_vertical(v_id).items():
                if issue["correct_quadrant"] == 4:
                    self.assertFalse(issue["disclosure_required"],
                                     f"{v_id}/{iid} Q4 must NOT require disclosure")

    def test_sensitive_issues_exist_per_vertical(self):
        for v_id in ALL_VERTICAL_IDS:
            sensitive = [i for i in get_csrd_issues_for_vertical(v_id).values()
                         if i.get("electronics_sensitive")]
            self.assertGreater(len(sensitive), 0,
                               f"{v_id}: needs at least 1 BU-sensitive issue")

    def test_unique_ids_within_vertical(self):
        for v_id in ALL_VERTICAL_IDS:
            issues = get_csrd_issues_for_vertical(v_id)
            ids = list(issues.keys())
            self.assertEqual(len(ids), len(set(ids)),
                             f"{v_id}: duplicate CSRD issue IDs")

    def test_unique_ids_across_verticals(self):
        all_ids = []
        for v_id in ALL_VERTICAL_IDS:
            all_ids.extend(get_csrd_issues_for_vertical(v_id).keys())
        self.assertEqual(len(all_ids), len(set(all_ids)),
                         "Duplicate CSRD issue IDs across verticals")


class TestBuildBuStatesAllVerticals(unittest.TestCase):
    """Test build_bu_states with every valid substitution combo."""

    def test_all_valid_substitutions_produce_4_states(self):
        for slot, verticals in SLOT_FIT_MAP.items():
            for v_id in verticals:
                subs = {slot: v_id}
                states = build_bu_states(subs)
                self.assertEqual(len(states), 4,
                                 f"Substitution {slot}->{v_id} should produce 4 states")
                ids = [s["bu_id"] for s in states]
                self.assertIn(v_id, ids)
                self.assertNotIn(slot, ids)

    def test_max_substitution_combo(self):
        """Test replacing all 4 slots simultaneously."""
        subs = {
            "pharma": "oil_gas",
            "electronics": "oil_gas",  # oil_gas fits electronics slot too
            "consumer_goods": "agriculture",
            "software": "technology",
        }
        states = build_bu_states(subs)
        self.assertEqual(len(states), 4)
        ids = [s["bu_id"] for s in states]
        self.assertEqual(ids, ["oil_gas", "oil_gas", "agriculture", "technology"])

    def test_all_states_have_engine_fields(self):
        """Verify build_bu_states produces fields the engine needs."""
        engine_fields = {"bu_id", "revenue_base", "opex_base", "carbon_intensity",
                         "water_dependency", "natural_capital_debt",
                         "social_license_score", "governance_risk_score",
                         "reputation_score", "staff_burnout_index",
                         "vrio_advantage", "risk_factors"}
        for slot, verticals in SLOT_FIT_MAP.items():
            for v_id in verticals:
                states = build_bu_states({slot: v_id})
                for s in states:
                    for field in engine_fields:
                        self.assertIn(field, s,
                                      f"State for {s['bu_id']} missing engine field '{field}'")


if __name__ == "__main__":
    unittest.main(verbosity=2)
