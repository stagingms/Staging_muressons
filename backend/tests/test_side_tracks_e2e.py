"""
Muressons Global Corporation — Side Track E2E Tests

Comprehensive test suite covering:
  1. All 5 tracks: registry, configs, scoring, data bridges
  2. Cross-track dependency chain (SC → Ethics → Reporting)
  3. Multiplayer state isolation
  4. Aggregate leaderboard composite scoring
"""

import unittest
import copy
from side_tracks import get_track, get_track_catalog, get_all_tracks


# ═════════════════════════════════════════════════════════════════
#  REGISTRY TESTS — All 4 tracks
# ═════════════════════════════════════════════════════════════════

class TestTrackRegistry(unittest.TestCase):
    """Verify all 5 tracks register correctly."""

    def test_five_tracks_registered(self):
        tracks = get_all_tracks()
        self.assertEqual(len(tracks), 6)
        expected = {"supply_chain", "ethics_sustainability", "stakeholder_management", "sustainability_reporting", "corporate_sdg", "brsr_ngrbc"}
        self.assertEqual(set(tracks.keys()), expected)

    def test_catalog_completeness(self):
        catalog = get_track_catalog()
        self.assertEqual(len(catalog), 6)
        for entry in catalog:
            self.assertIn("track_id", entry)
            self.assertIn("display_name", entry)
            self.assertIn("icon", entry)
            self.assertIn("num_rounds", entry)
            self.assertIn("available_window", entry)
            self.assertIn("scoring_dimensions", entry)

    def test_no_duplicate_track_ids(self):
        catalog = get_track_catalog()
        ids = [t["track_id"] for t in catalog]
        self.assertEqual(len(ids), len(set(ids)))

    def test_total_rounds(self):
        """6 tracks: 7 + 5 + 4 + 5 + 5 + 5 = 31 total rounds."""
        catalog = get_track_catalog()
        total = sum(t["num_rounds"] for t in catalog)
        self.assertEqual(total, 31)


# ═════════════════════════════════════════════════════════════════
#  ETHICS & SUSTAINABILITY TRACK TESTS
# ═════════════════════════════════════════════════════════════════

class TestEthicsTrackConfigs(unittest.TestCase):
    """Test Ethics & Sustainability track configuration integrity."""

    def setUp(self):
        self.track = get_track("ethics_sustainability")

    def test_identity(self):
        self.assertEqual(self.track.track_id, "ethics_sustainability")
        self.assertEqual(self.track.num_rounds, 5)
        self.assertEqual(self.track.icon, "⚖️")
        self.assertEqual(self.track.available_window, (2, 7))

    def test_all_five_rounds_exist(self):
        configs = self.track.get_round_configs()
        self.assertEqual(len(configs), 5)
        for i in range(1, 6):
            self.assertIn(i, configs)

    def test_each_round_has_three_options(self):
        for rn in range(1, 6):
            opts = self.track.get_round_options(rn)
            self.assertEqual(len(opts), 3, f"ES-R{rn} should have 3 options")

    def test_all_options_have_impacts(self):
        for rn in range(1, 6):
            opts = self.track.get_round_options(rn)
            for key, opt in opts.items():
                self.assertIn("impacts", opt, f"ES-R{rn} {key} missing impacts")
                self.assertIn("flags_set", opt, f"ES-R{rn} {key} missing flags_set")

    def test_cross_track_prerequisite(self):
        self.assertIn("supply_chain", self.track.cross_track_prerequisites)


class TestEthicsTrackScoring(unittest.TestCase):

    def setUp(self):
        self.track = get_track("ethics_sustainability")

    def test_perfect_score(self):
        state = {
            "ethical_governance": 100, "human_rights_dd": 100,
            "green_claims_integrity": 100, "biodiversity_stewardship": 100,
            "just_transition": 100,
        }
        score = self.track.calculate_score(state)
        self.assertEqual(score["total_score"], 100.0)
        self.assertEqual(score["grade"], "A+")
        self.assertEqual(score["archetype"]["title"], "Ethical Vanguard")

    def test_zero_score(self):
        state = {}
        score = self.track.calculate_score(state)
        self.assertEqual(score["total_score"], 0.0)
        self.assertEqual(score["grade"], "F")

    def test_five_dimensions(self):
        score = self.track.calculate_score({"ethical_governance": 50})
        self.assertEqual(len(score["dimensions"]), 5)


class TestEthicsDataBridge(unittest.TestCase):

    def setUp(self):
        self.track = get_track("ethics_sustainability")
        self.main_gs = {"corporate_treasury": 50_000_000, "group_reputation": 60, "active_event_flags": {}}
        self.main_bus = [{"governance_risk_score": 25, "social_license_score": 50}]

    def test_seed_without_sc(self):
        seed = self.track.seed_from_main_state(self.main_gs, self.main_bus, {})
        self.assertFalse(seed["sc_track_completed"])
        self.assertEqual(seed["human_rights_dd"], 10)  # No SC cobalt boost

    def test_seed_with_sc_cobalt(self):
        completed = {"supply_chain": {"sc_cobalt_findings": True}}
        seed = self.track.seed_from_main_state(self.main_gs, self.main_bus, completed)
        self.assertTrue(seed["sc_track_completed"])
        self.assertEqual(seed["human_rights_dd"], 30)  # +20 SC cobalt boost

    def test_write_back_high_score(self):
        state = {"ethical_governance": 90, "human_rights_dd": 80, "green_claims_integrity": 85, "biodiversity_stewardship": 75, "just_transition": 80}
        flags = self.track.write_back_to_main(state, self.main_gs)
        self.assertTrue(flags["ethics_track_completed"])
        self.assertEqual(flags["es_track_mr_bonus"], 0.10)
        self.assertTrue(flags.get("es_governance_excellence"))


class TestEthicsEngineHooks(unittest.TestCase):

    def setUp(self):
        self.track = get_track("ethics_sustainability")

    def test_r5_human_rights_leader_reduces_severity(self):
        state = {"accumulated_flags": ["es_human_rights_leader"]}
        result = self.track.pre_tick(5, state, [], [{"choice_selected": "option_a"}], 50)
        self.assertTrue(result["pre_events"].get("union_trust_bonus"))
        self.assertLess(result["crisis_severity"], 50)

    def test_r5_ai_denial_increases_severity(self):
        state = {"accumulated_flags": ["es_ai_denial"]}
        result = self.track.pre_tick(5, state, [], [{"choice_selected": "option_a"}], 50)
        self.assertTrue(result["pre_events"].get("employee_distrust"))
        self.assertGreater(result["crisis_severity"], 50)

    def test_r3_ai_denial_compounds_greenwash(self):
        gs = {"group_reputation": 60, "corporate_treasury": 50_000_000}
        bus = [{"governance_risk_score": 20, "social_license_score": 50}]
        decisions = [{"choice_selected": "option_c"}]
        prev = {"accumulated_flags": ["es_ai_denial"]}
        extra = self.track.post_tick(3, gs, bus, decisions, {}, {}, prev)
        self.assertEqual(extra.get("es_compounding_credibility_penalty"), -5)


# ═════════════════════════════════════════════════════════════════
#  STAKEHOLDER MANAGEMENT TRACK TESTS
# ═════════════════════════════════════════════════════════════════

class TestStakeholderTrackConfigs(unittest.TestCase):

    def setUp(self):
        self.track = get_track("stakeholder_management")

    def test_identity(self):
        self.assertEqual(self.track.num_rounds, 4)
        self.assertEqual(self.track.icon, "🤝")
        self.assertEqual(self.track.available_window, (1, 6))

    def test_all_four_rounds_exist(self):
        configs = self.track.get_round_configs()
        self.assertEqual(len(configs), 4)

    def test_scoring_dimensions(self):
        dims = self.track.scoring_dimensions
        self.assertEqual(len(dims), 4)
        ids = {d["id"] for d in dims}
        self.assertEqual(ids, {"stakeholder_mapping", "investor_confidence", "community_trust", "crisis_resilience"})


class TestStakeholderScoring(unittest.TestCase):

    def setUp(self):
        self.track = get_track("stakeholder_management")

    def test_equal_weights(self):
        """All 4 dimensions weighted equally at 25%."""
        state = {"stakeholder_mapping": 100, "investor_confidence": 0, "community_trust": 0, "crisis_resilience": 0}
        score = self.track.calculate_score(state)
        self.assertEqual(score["total_score"], 25.0)

    def test_perfect_score(self):
        state = {"stakeholder_mapping": 100, "investor_confidence": 100, "community_trust": 100, "crisis_resilience": 100}
        score = self.track.calculate_score(state)
        self.assertEqual(score["total_score"], 100.0)
        self.assertEqual(score["grade"], "A+")
        self.assertEqual(score["archetype"]["title"], "Stakeholder Champion")


class TestStakeholderEngineHooks(unittest.TestCase):

    def setUp(self):
        self.track = get_track("stakeholder_management")

    def test_r4_engagement_policy_reduces_crisis(self):
        state = {"accumulated_flags": ["sm_engagement_policy"]}
        result = self.track.pre_tick(4, state, [], [{"choice_selected": "option_a"}], 50)
        self.assertTrue(result["pre_events"].get("crisis_playbook_active"))
        self.assertLess(result["crisis_severity"], 50)

    def test_r4_reactive_increases_crisis(self):
        state = {"accumulated_flags": ["sm_reactive_approach"]}
        result = self.track.pre_tick(4, state, [], [{"choice_selected": "option_a"}], 50)
        self.assertTrue(result["pre_events"].get("no_crisis_playbook"))
        self.assertGreater(result["crisis_severity"], 50)


# ═════════════════════════════════════════════════════════════════
#  SUSTAINABILITY REPORTING TRACK TESTS
# ═════════════════════════════════════════════════════════════════

class TestReportingTrackConfigs(unittest.TestCase):

    def setUp(self):
        self.track = get_track("sustainability_reporting")

    def test_identity(self):
        self.assertEqual(self.track.num_rounds, 5)
        self.assertEqual(self.track.icon, "📊")
        self.assertEqual(self.track.available_window, (2, 8))

    def test_cross_track_prerequisite(self):
        self.assertIn("ethics_sustainability", self.track.cross_track_prerequisites)

    def test_all_five_rounds_exist(self):
        configs = self.track.get_round_configs()
        self.assertEqual(len(configs), 5)


class TestReportingScoring(unittest.TestCase):

    def setUp(self):
        self.track = get_track("sustainability_reporting")

    def test_perfect_score(self):
        state = {"regulatory_readiness": 100, "climate_disclosure": 100, "social_governance": 100, "assurance_credibility": 100, "integrated_value": 100}
        score = self.track.calculate_score(state)
        self.assertEqual(score["total_score"], 100.0)
        self.assertEqual(score["grade"], "A+")
        self.assertEqual(score["archetype"]["title"], "Disclosure Pioneer")

    def test_zero_score(self):
        score = self.track.calculate_score({})
        self.assertEqual(score["total_score"], 0.0)
        self.assertEqual(score["grade"], "F")
        self.assertEqual(score["archetype"]["title"], "Opaque Enterprise")


class TestReportingDataBridge(unittest.TestCase):

    def setUp(self):
        self.track = get_track("sustainability_reporting")
        self.main_gs = {"corporate_treasury": 50_000_000, "group_reputation": 60, "active_event_flags": {}}
        self.main_bus = [{"governance_risk_score": 25}]

    def test_seed_without_ethics(self):
        seed = self.track.seed_from_main_state(self.main_gs, self.main_bus, {})
        self.assertFalse(seed["ethics_track_completed"])
        self.assertEqual(seed["social_governance"], 10)

    def test_seed_with_ethics(self):
        completed = {"ethics_sustainability": {"ethical_governance": 80}}
        seed = self.track.seed_from_main_state(self.main_gs, self.main_bus, completed)
        self.assertTrue(seed["ethics_track_completed"])
        self.assertEqual(seed["social_governance"], 20)  # +10 ethics boost


class TestReportingEngineHooks(unittest.TestCase):

    def setUp(self):
        self.track = get_track("sustainability_reporting")

    def test_r5_data_infrastructure_bonus(self):
        state = {"accumulated_flags": ["sr_data_infrastructure"]}
        result = self.track.pre_tick(5, state, [], [{"choice_selected": "option_a"}], 50)
        self.assertTrue(result["pre_events"].get("data_infrastructure_bonus"))
        self.assertLess(result["crisis_severity"], 50)

    def test_r5_credibility_gap_penalty(self):
        state = {"accumulated_flags": ["sr_credibility_gap"]}
        result = self.track.pre_tick(5, state, [], [{"choice_selected": "option_a"}], 50)
        self.assertTrue(result["pre_events"].get("credibility_undermined"))
        self.assertGreater(result["crisis_severity"], 50)

    def test_r4_credibility_collapse(self):
        gs = {"group_reputation": 60, "corporate_treasury": 50_000_000}
        bus = [{"governance_risk_score": 20}]
        prev = {"accumulated_flags": ["sr_minimum_compliance"]}
        extra = self.track.post_tick(4, gs, bus, [{"choice_selected": "option_c"}], {}, {}, prev)
        self.assertEqual(extra.get("sr_credibility_collapse"), -6)
        # Base option_c reputation impact (-8) + compounding (-6) = -14
        self.assertLess(gs["group_reputation"], 60)


# ═════════════════════════════════════════════════════════════════
#  CROSS-TRACK DEPENDENCY CHAIN TESTS
# ═════════════════════════════════════════════════════════════════

class TestCrossTrackDependencies(unittest.TestCase):
    """Test the SC → Ethics → Reporting enrichment chain."""

    def setUp(self):
        self.main_gs = {"corporate_treasury": 50_000_000, "group_reputation": 60, "active_event_flags": {}}
        self.main_bus = [{"governance_risk_score": 25, "natural_capital_debt": 15, "carbon_intensity": 45, "social_license_score": 50}]

    def test_sc_to_ethics_pipeline(self):
        """SC completion enriches Ethics seeding."""
        sc_track = get_track("supply_chain")
        sc_state = sc_track.seed_from_main_state(self.main_gs, self.main_bus, {})
        sc_state["accumulated_flags"] = ["sc_cobalt_clean"]
        sc_flags = sc_track.write_back_to_main(sc_state, self.main_gs)

        # Update main global with SC flags
        self.main_gs["active_event_flags"].update(sc_flags)

        # Now seed Ethics with SC completed
        es_track = get_track("ethics_sustainability")
        completed = {"supply_chain": sc_state}
        es_state = es_track.seed_from_main_state(self.main_gs, self.main_bus, completed)
        self.assertTrue(es_state["sc_track_completed"])

    def test_ethics_to_reporting_pipeline(self):
        """Ethics completion enriches Reporting seeding."""
        es_track = get_track("ethics_sustainability")
        es_state = es_track.seed_from_main_state(self.main_gs, self.main_bus, {})
        es_state["ethical_governance"] = 80
        es_flags = es_track.write_back_to_main(es_state, self.main_gs)
        self.main_gs["active_event_flags"].update(es_flags)

        sr_track = get_track("sustainability_reporting")
        completed = {"ethics_sustainability": es_state}
        sr_state = sr_track.seed_from_main_state(self.main_gs, self.main_bus, completed)
        self.assertTrue(sr_state["ethics_track_completed"])
        self.assertEqual(sr_state["ethics_governance_score"], 80)
        self.assertEqual(sr_state["social_governance"], 20)  # 10 base + 10 ethics

    def test_full_chain_sc_ethics_reporting(self):
        """Full 3-track dependency chain: SC → Ethics → Reporting."""
        # SC
        sc = get_track("supply_chain")
        sc_state = sc.seed_from_main_state(self.main_gs, self.main_bus, {})
        sc_flags = sc.write_back_to_main(sc_state, self.main_gs)
        self.main_gs["active_event_flags"].update(sc_flags)

        # Ethics (seeded by SC)
        es = get_track("ethics_sustainability")
        es_state = es.seed_from_main_state(self.main_gs, self.main_bus, {"supply_chain": sc_state})
        es_state["ethical_governance"] = 75
        es_flags = es.write_back_to_main(es_state, self.main_gs)
        self.main_gs["active_event_flags"].update(es_flags)

        # Reporting (seeded by Ethics)
        sr = get_track("sustainability_reporting")
        sr_state = sr.seed_from_main_state(self.main_gs, self.main_bus, {"supply_chain": sc_state, "ethics_sustainability": es_state})
        self.assertTrue(sr_state["ethics_track_completed"])
        self.assertEqual(sr_state["ethics_governance_score"], 75)

    def test_standalone_track_no_dependencies(self):
        """Stakeholder Management works without any completed tracks."""
        sm = get_track("stakeholder_management")
        self.assertEqual(sm.cross_track_prerequisites, [])
        state = sm.seed_from_main_state(self.main_gs, self.main_bus, {})
        score = sm.calculate_score(state)
        self.assertGreaterEqual(score["total_score"], 0)


# ═════════════════════════════════════════════════════════════════
#  MULTIPLAYER STATE ISOLATION TESTS
# ═════════════════════════════════════════════════════════════════

class TestMultiplayerStateIsolation(unittest.TestCase):
    """
    Verify that side track state is isolated per-player.
    Two players seeded from the same main state should have
    independent track states that don't cross-contaminate.
    """

    def setUp(self):
        self.main_gs = {"corporate_treasury": 50_000_000, "group_reputation": 60, "active_event_flags": {}}
        self.main_bus = [{"governance_risk_score": 25, "natural_capital_debt": 15, "carbon_intensity": 45, "social_license_score": 50}]

    def test_independent_seeding(self):
        """Two players seed independently from the same main state."""
        track = get_track("supply_chain")
        state_p1 = track.seed_from_main_state(self.main_gs, self.main_bus, {})
        state_p2 = track.seed_from_main_state(self.main_gs, self.main_bus, {})

        # Both should start identically
        self.assertEqual(state_p1["supply_visibility"], state_p2["supply_visibility"])

        # Mutating P1 should NOT affect P2
        state_p1["supply_visibility"] = 99
        self.assertNotEqual(state_p1["supply_visibility"], state_p2["supply_visibility"])

    def test_independent_scoring(self):
        """Different player states should produce different scores."""
        track = get_track("ethics_sustainability")
        state_p1 = {"ethical_governance": 90, "human_rights_dd": 85, "green_claims_integrity": 80, "biodiversity_stewardship": 75, "just_transition": 80}
        state_p2 = {"ethical_governance": 20, "human_rights_dd": 15, "green_claims_integrity": 10, "biodiversity_stewardship": 5, "just_transition": 10}

        score_p1 = track.calculate_score(state_p1)
        score_p2 = track.calculate_score(state_p2)

        self.assertGreater(score_p1["total_score"], score_p2["total_score"])
        self.assertNotEqual(score_p1["grade"], score_p2["grade"])

    def test_independent_write_back(self):
        """Different final states produce different M_R flags."""
        track = get_track("supply_chain")
        state_good = {"supply_visibility": 90, "supplier_risk_score": 10, "scope3_reduction": 80, "circular_procurement_index": 75, "digital_maturity": 70, "geopolitical_resilience": 65, "cumulative_reputation_delta": 20}
        state_bad = {"supply_visibility": 10, "supplier_risk_score": 80, "scope3_reduction": 5, "circular_procurement_index": 5, "digital_maturity": 5, "geopolitical_resilience": 5}

        flags_good = track.write_back_to_main(state_good, self.main_gs)
        flags_bad = track.write_back_to_main(state_bad, self.main_gs)

        self.assertTrue(flags_good.get("supply_chain_resilient"))
        self.assertTrue(flags_bad.get("supply_chain_fragile"))
        self.assertEqual(flags_good.get("sc_track_mr_bonus"), 0.10)
        self.assertEqual(flags_bad.get("sc_track_mr_penalty"), -0.05)

    def test_post_tick_isolation(self):
        """Post-tick mutations to one player's global state don't affect another's."""
        track = get_track("stakeholder_management")
        gs_p1 = copy.deepcopy(self.main_gs)
        gs_p2 = copy.deepcopy(self.main_gs)
        bus_p1 = copy.deepcopy(self.main_bus)
        bus_p2 = copy.deepcopy(self.main_bus)

        # P1 picks expensive option, P2 picks cheap option
        extra_p1 = track.post_tick(1, gs_p1, bus_p1, [{"choice_selected": "option_a"}], {}, {}, {})
        extra_p2 = track.post_tick(1, gs_p2, bus_p2, [{"choice_selected": "option_c"}], {}, {}, {})

        # P1 should have lower treasury, P2 unchanged
        self.assertLess(gs_p1["corporate_treasury"], gs_p2["corporate_treasury"])
        # P1 should have higher reputation
        self.assertGreater(gs_p1["group_reputation"], gs_p2["group_reputation"])


# ═════════════════════════════════════════════════════════════════
#  M_R FLAG ACCUMULATION TESTS
# ═════════════════════════════════════════════════════════════════

class TestMRFlagAccumulation(unittest.TestCase):
    """Test that M_R bonuses/penalties from multiple tracks stack correctly."""

    def test_multiple_track_bonuses(self):
        """Completing all 4 tracks with A+ should yield stacked M_R bonuses."""
        main_gs = {"corporate_treasury": 50_000_000, "group_reputation": 60, "active_event_flags": {}}
        main_bus = [{"governance_risk_score": 25, "natural_capital_debt": 15, "carbon_intensity": 45, "social_license_score": 50}]

        total_mr = 0
        for tid in ["supply_chain", "ethics_sustainability", "stakeholder_management", "sustainability_reporting"]:
            track = get_track(tid)
            # Create a high-scoring state
            dims = track.scoring_dimensions
            state = {d["id"]: 90 for d in dims}
            # SC special: supplier_risk_score is inverted (lower = better)
            if "supplier_risk_score" in state:
                state["supplier_risk_score"] = 10

            flags = track.write_back_to_main(state, main_gs)
            mr_bonus = flags.get(f"{tid[:2]}_track_mr_bonus", flags.get("sm_track_mr_bonus", flags.get("sr_track_mr_bonus", 0)))

            # All high-scoring tracks should yield positive M_R
            total_mr += mr_bonus
            main_gs["active_event_flags"].update(flags)

        # Should have meaningful cumulative M_R bonus
        self.assertGreater(total_mr, 0.15)


if __name__ == "__main__":
    unittest.main()
