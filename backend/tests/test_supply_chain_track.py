"""
Muressons Global Corporation — Supply Chain Side Track Tests

Tests the Supply Chain side track's:
  - Registry discovery
  - Round configuration integrity (7 rounds, all options)
  - Data bridge (read): seeding from main state
  - Data bridge (write): write-back flags
  - Scoring system (grades, archetypes, dimensions)
  - Engine hooks (inter-round flag dependencies)
  - Stochastic stress test (SC-R7)
"""

import unittest
import copy
from side_tracks import get_track, get_track_catalog, get_all_tracks
from side_tracks.supply_chain.track import SupplyChainTrack


class TestSupplyChainRegistry(unittest.TestCase):
    """Test that the Supply Chain track registers correctly."""

    def test_track_in_registry(self):
        tracks = get_all_tracks()
        self.assertIn("supply_chain", tracks)

    def test_catalog_entry(self):
        catalog = get_track_catalog()
        sc = [t for t in catalog if t["track_id"] == "supply_chain"]
        self.assertEqual(len(sc), 1)
        self.assertEqual(sc[0]["num_rounds"], 7)
        self.assertEqual(sc[0]["available_window"], [3, 8])
        self.assertEqual(len(sc[0]["scoring_dimensions"]), 7)

    def test_get_track_by_id(self):
        track = get_track("supply_chain")
        self.assertIsNotNone(track)
        self.assertIsInstance(track, SupplyChainTrack)

    def test_unknown_track_returns_none(self):
        self.assertIsNone(get_track("nonexistent_track"))


class TestSupplyChainRoundConfigs(unittest.TestCase):
    """Test that all 7 rounds have valid configuration."""

    def setUp(self):
        self.track = get_track("supply_chain")

    def test_all_seven_rounds_exist(self):
        configs = self.track.get_round_configs()
        self.assertEqual(len(configs), 7)
        for i in range(1, 8):
            self.assertIn(i, configs)

    def test_each_round_has_required_fields(self):
        for rn in range(1, 8):
            cfg = self.track.get_round_config(rn)
            self.assertIsNotNone(cfg, f"SC-R{rn} config is None")
            self.assertIn("title", cfg)
            self.assertIn("crisis", cfg)
            self.assertIn("options", cfg)
            self.assertIn("title", cfg["crisis"])
            self.assertIn("description", cfg["crisis"])

    def test_each_round_has_three_options(self):
        for rn in range(1, 8):
            opts = self.track.get_round_options(rn)
            self.assertEqual(len(opts), 3, f"SC-R{rn} should have 3 options")
            self.assertIn("option_a", opts)
            self.assertIn("option_b", opts)
            self.assertIn("option_c", opts)

    def test_all_options_have_impacts(self):
        for rn in range(1, 8):
            opts = self.track.get_round_options(rn)
            for opt_key, opt in opts.items():
                self.assertIn("impacts", opt, f"SC-R{rn} {opt_key} missing impacts")
                self.assertIn("flags_set", opt, f"SC-R{rn} {opt_key} missing flags_set")
                self.assertIn("title", opt, f"SC-R{rn} {opt_key} missing title")
                self.assertIn("description", opt, f"SC-R{rn} {opt_key} missing description")

    def test_option_a_always_most_expensive(self):
        """Option A should always be the highest-cost (most aggressive) choice."""
        for rn in range(1, 8):
            opts = self.track.get_round_options(rn)
            cost_a = opts["option_a"]["impacts"].get("treasury", 0)
            cost_c = opts["option_c"]["impacts"].get("treasury", 0)
            self.assertLessEqual(cost_a, cost_c,
                f"SC-R{rn}: Option A (${cost_a:,}) should be <= Option C (${cost_c:,})")

    def test_round_configs_are_deep_copies(self):
        """Ensure get_round_config returns deep copies, not references."""
        cfg1 = self.track.get_round_config(1)
        cfg2 = self.track.get_round_config(1)
        cfg1["title"] = "MUTATED"
        self.assertNotEqual(cfg2["title"], "MUTATED")


class TestSupplyChainDataBridgeRead(unittest.TestCase):
    """Test the DATA BRIDGE (READ): seeding from main state."""

    def setUp(self):
        self.track = get_track("supply_chain")
        self.main_global = {
            "corporate_treasury": 50_000_000,
            "group_reputation": 65.0,
            "active_event_flags": {},
        }
        self.main_bus = [
            {"bu_id": "electronics", "governance_risk_score": 25.0,
             "natural_capital_debt": 15.0, "carbon_intensity": 45.0},
            {"bu_id": "pharma", "governance_risk_score": 18.0,
             "natural_capital_debt": 10.0, "carbon_intensity": 30.0},
        ]

    def test_seed_returns_all_track_metrics(self):
        seed = self.track.seed_from_main_state(self.main_global, self.main_bus, {})
        required_keys = [
            "supply_visibility", "supplier_risk_score", "scope3_reduction",
            "circular_procurement_index", "digital_maturity", "geopolitical_resilience",
        ]
        for key in required_keys:
            self.assertIn(key, seed.extra_state, f"Seed missing track metric: {key}")

    def test_seed_supply_visibility_baseline(self):
        """Without main sim deep audit, visibility starts at 20."""
        seed = self.track.seed_from_main_state(self.main_global, self.main_bus, {})
        self.assertEqual(seed.extra_state["supply_visibility"], 20)

    def test_seed_deep_audit_bonus(self):
        """With main sim deep audit, visibility starts at 30 (+10 bonus)."""
        self.main_global["active_event_flags"]["deep_audit_completed"] = True
        seed = self.track.seed_from_main_state(self.main_global, self.main_bus, {})
        self.assertEqual(seed.extra_state["supply_visibility"], 30)

    def test_seed_blockchain_bonus(self):
        """Main sim blockchain adds +15 to digital maturity."""
        self.main_global["active_event_flags"]["blockchain_traceability"] = True
        seed = self.track.seed_from_main_state(self.main_global, self.main_bus, {})
        self.assertEqual(seed.extra_state["digital_maturity"], 25)  # 10 base + 15

    def test_seed_inherits_ncd(self):
        seed = self.track.seed_from_main_state(self.main_global, self.main_bus, {})
        self.assertEqual(seed.extra_state["inherited_ncd"], 25.0)  # 15 + 10

    def test_seed_inherits_carbon_intensity(self):
        seed = self.track.seed_from_main_state(self.main_global, self.main_bus, {})
        self.assertEqual(seed.extra_state["inherited_carbon_intensity"], 37.5)  # (45+30)/2


class TestSupplyChainDataBridgeWrite(unittest.TestCase):
    """Test the DATA BRIDGE (WRITE): write-back to main sim."""

    def setUp(self):
        self.track = get_track("supply_chain")
        self.main_global = {
            "corporate_treasury": 50_000_000,
            "group_reputation": 65.0,
            "active_event_flags": {},
        }

    def test_completed_flag_always_set(self):
        state = {"supply_visibility": 50}
        flags = self.track.write_back_to_main(state, self.main_global)
        self.assertTrue(flags.flags_to_set["supply_chain_track_completed"])

    def test_high_score_resilient_flag(self):
        state = {
            "supply_visibility": 95, "supplier_risk_score": 10,
            "scope3_reduction": 80, "circular_procurement_index": 75,
            "digital_maturity": 70, "geopolitical_resilience": 65,
        }
        flags = self.track.write_back_to_main(state, self.main_global)
        self.assertTrue(flags.flags_to_set.get("supply_chain_resilient"))
        self.assertIn(flags.flags_to_set.get("sc_track_mr_bonus"), [0.05, 0.10])  # Depends on consumer_trust

    def test_medium_score_adequate_flag(self):
        state = {
            "supply_visibility": 55, "supplier_risk_score": 40,
            "scope3_reduction": 30, "circular_procurement_index": 25,
            "digital_maturity": 20, "geopolitical_resilience": 20,
        }
        flags = self.track.write_back_to_main(state, self.main_global)
        self.assertTrue(flags.flags_to_set.get("supply_chain_adequate"))

    def test_low_score_fragile_flag(self):
        state = {
            "supply_visibility": 20, "supplier_risk_score": 70,
            "scope3_reduction": 5, "circular_procurement_index": 5,
            "digital_maturity": 5, "geopolitical_resilience": 5,
        }
        flags = self.track.write_back_to_main(state, self.main_global)
        self.assertTrue(flags.flags_to_set.get("supply_chain_fragile"))
        self.assertEqual(flags.flags_to_set.get("sc_track_mr_penalty"), -0.05)

    def test_grade_included(self):
        state = {"supply_visibility": 75, "supplier_risk_score": 25}
        flags = self.track.write_back_to_main(state, self.main_global)
        self.assertIn("supply_chain_grade", flags.flags_to_set)
        self.assertIn(flags.flags_to_set["supply_chain_grade"], ["A+", "A", "B", "C", "D", "F"])


class TestSupplyChainScoring(unittest.TestCase):
    """Test the separate leaderboard scoring system."""

    def setUp(self):
        self.track = get_track("supply_chain")

    def test_perfect_score(self):
        state = {
            "supply_visibility": 100, "supplier_risk_score": 0,
            "scope3_reduction": 100, "circular_procurement_index": 100,
            "digital_maturity": 100, "geopolitical_resilience": 100,
            "cumulative_reputation_delta": 30,  # Max positive rep
        }
        score = self.track.calculate_score(state)
        self.assertEqual(score["total_score"], 100.0)
        self.assertEqual(score["grade"], "A+")
        self.assertEqual(score["archetype"]["title"], "Resilient Network Architect")

    def test_zero_score(self):
        state = {
            "supply_visibility": 0, "supplier_risk_score": 100,
            "scope3_reduction": 0, "circular_procurement_index": 0,
            "digital_maturity": 0, "geopolitical_resilience": 0,
            "cumulative_reputation_delta": -30,  # Max negative rep
        }
        score = self.track.calculate_score(state)
        self.assertEqual(score["total_score"], 0.0)
        self.assertEqual(score["grade"], "F")
        self.assertEqual(score["archetype"]["title"], "Exposed & Vulnerable")

    def test_mid_range_score(self):
        state = {
            "supply_visibility": 50, "supplier_risk_score": 50,
            "scope3_reduction": 50, "circular_procurement_index": 50,
            "digital_maturity": 50, "geopolitical_resilience": 50,
        }
        score = self.track.calculate_score(state)
        self.assertEqual(score["total_score"], 50.0)
        self.assertEqual(score["grade"], "C")

    def test_scoring_weights_correct(self):
        """Verify the weighted average formula is correct."""
        state = {
            "supply_visibility": 100, "supplier_risk_score": 0,
            "scope3_reduction": 0, "circular_procurement_index": 0,
            "digital_maturity": 0, "geopolitical_resilience": 0,
        }
        score = self.track.calculate_score(state)
        # 100 * 0.20 (visibility) + 100 * 0.17 (risk inverted) + consumer_trust component
        # Consumer trust = 0*0.3 + 100*0.3 + 50*0.4 = 50  →  50 * 0.13 = 6.5
        # Total ≈ 20 + 17 + 6.5 = 43.5
        self.assertAlmostEqual(score["total_score"], 43.5, delta=1.0)

    def test_all_dimensions_present(self):
        state = {"supply_visibility": 50}
        score = self.track.calculate_score(state)
        self.assertIn("dimensions", score)
        self.assertEqual(len(score["dimensions"]), 7)

    def test_archetype_always_present(self):
        state = {"supply_visibility": 50}
        score = self.track.calculate_score(state)
        self.assertIn("archetype", score)
        self.assertIn("title", score["archetype"])
        self.assertIn("gradient", score["archetype"])


class TestSupplyChainPreTick(unittest.TestCase):
    """Test pre-tick engine hooks."""

    def setUp(self):
        self.track = get_track("supply_chain")

    def test_r2_deep_visibility_discount(self):
        """SC-R1's full tier mapping should discount SC-R2 Option A."""
        state = {"accumulated_flags": ["full_tier_mapping", "sc_deep_visibility"]}
        decisions = [{"choice_selected": "option_a"}]
        result = self.track.pre_tick(2, state, [], decisions, 0)
        self.assertTrue(result["pre_events"].get("sc_r1_visibility_discount"))
        self.assertEqual(result["pre_events"]["sc_r1_visibility_discount_amount"], 1_000_000)

    def test_r2_no_discount_without_flag(self):
        """Without deep visibility, no discount."""
        state = {"accumulated_flags": []}
        decisions = [{"choice_selected": "option_a"}]
        result = self.track.pre_tick(2, state, [], decisions, 0)
        self.assertNotIn("sc_r1_visibility_discount", result["pre_events"])

    def test_r5_greenwash_contamination(self):
        """SC-R1's self-assessment should penalise SC-R5 Option A."""
        state = {"accumulated_flags": ["self_assessment_only", "sc_greenwash_risk"]}
        decisions = [{"choice_selected": "option_a"}]
        result = self.track.pre_tick(5, state, [], decisions, 0)
        self.assertTrue(result["pre_events"].get("sc_greenwash_contamination"))
        self.assertEqual(result["pre_events"]["sc_greenwash_penalty_amount"], 2_000_000)

    def test_r7_stochastic_severity(self):
        """SC-R7 should calculate disruption severity from accumulated flags."""
        state = {
            "accumulated_flags": [
                "full_tier_mapping", "sc_deep_visibility",
                "blockchain_traceability_sc", "nearshored_supply"
            ]
        }
        decisions = [{"choice_selected": "option_a"}]
        result = self.track.pre_tick(7, state, [], decisions, 60)

        # With these flags: 60 - 10 - 5 - 10 - 15 = 20 (before stochastic)
        severity = result["crisis_severity"]
        self.assertLessEqual(severity, 60)  # Should be significantly reduced
        self.assertIn("final_disruption_severity", result["pre_events"])

    def test_r7_bad_flags_increase_severity(self):
        """Bad accumulated flags should increase disruption severity."""
        state = {
            "accumulated_flags": [
                "sc_greenwash_risk", "supply_concentration_risk",
                "dpp_non_compliant", "modern_slavery_unresolved"
            ]
        }
        decisions = [{"choice_selected": "option_c"}]
        result = self.track.pre_tick(7, state, [], decisions, 60)

        # 60 + 10 + 15 + 8 + 5 = 98 (before stochastic)
        self.assertGreaterEqual(result["pre_events"]["final_disruption_severity"], 60)


class TestSupplyChainPostTick(unittest.TestCase):
    """Test post-tick engine hooks."""

    def setUp(self):
        self.track = get_track("supply_chain")
        self.gs = {"corporate_treasury": 50_000_000, "group_reputation": 65.0}
        self.bus = [
            {"bu_id": "electronics", "governance_risk_score": 25.0,
             "natural_capital_debt": 15.0, "carbon_intensity": 45.0,
             "social_license_score": 50.0},
        ]

    def test_r1_option_a_applies_treasury(self):
        """SC-R1 Option A should deduct $5M from treasury."""
        gs = copy.deepcopy(self.gs)
        bus = copy.deepcopy(self.bus)
        decisions = [{"choice_selected": "option_a"}]
        extra = self.track.post_tick(1, gs, bus, decisions, {}, {}, {})
        self.assertEqual(gs["corporate_treasury"], 50_000_000 - 5_000_000)

    def test_r2_discount_applied(self):
        """SC-R2 post-tick applies the visibility discount."""
        gs = copy.deepcopy(self.gs)
        bus = copy.deepcopy(self.bus)
        decisions = [{"choice_selected": "option_a"}]
        events = {"sc_r1_visibility_discount": True, "sc_r1_visibility_discount_amount": 1_000_000}
        extra = self.track.post_tick(2, gs, bus, decisions, events, {}, {})
        # Treasury: 50M - 8M (option_a cost) + 1M (discount) = 43M
        self.assertEqual(gs["corporate_treasury"], 43_000_000)

    def test_r5_greenwash_penalty_applied(self):
        """SC-R5 post-tick applies greenwash penalty."""
        gs = copy.deepcopy(self.gs)
        bus = copy.deepcopy(self.bus)
        decisions = [{"choice_selected": "option_a"}]
        events = {"sc_greenwash_contamination": True, "sc_greenwash_penalty_amount": 2_000_000}
        extra = self.track.post_tick(5, gs, bus, decisions, events, {}, {})
        # Treasury: 50M - 8M (option_a cost) - 2M (penalty) = 40M
        self.assertEqual(gs["corporate_treasury"], 40_000_000)

    def test_r6_modern_slavery_compounding(self):
        """SC-R6 Option C with unresolved modern slavery doubles rep penalty."""
        gs = copy.deepcopy(self.gs)
        bus = copy.deepcopy(self.bus)
        decisions = [{"choice_selected": "option_c"}]
        prev_flags = {"accumulated_flags": ["modern_slavery_unresolved"]}
        extra = self.track.post_tick(6, gs, bus, decisions, {}, {}, prev_flags)
        self.assertTrue(extra.get("sc_r6_modern_slavery_compounding"))
        # Base option_c rep: -5, compounding: -5 more = -10 total
        self.assertEqual(gs["group_reputation"], 55.0)  # 65 - 10

    def test_r7_disruption_damage(self):
        """SC-R7 applies disruption damage based on severity and choice."""
        gs = copy.deepcopy(self.gs)
        bus = copy.deepcopy(self.bus)
        decisions = [{"choice_selected": "option_a"}]
        events = {"final_disruption_severity": 50}
        extra = self.track.post_tick(7, gs, bus, decisions, events, {}, {})

        self.assertIn("sc_r7_disruption_actual_damage", extra)
        self.assertIn("sc_r7_disruption_avoided", extra)
        # Option A resilience = 0.80 → 80% damage reduction
        self.assertEqual(extra["sc_r7_disruption_resilience_factor"], 0.80)
        damage = extra["sc_r7_disruption_actual_damage"]
        avoided = extra["sc_r7_disruption_avoided"]
        self.assertGreater(avoided, damage)  # More was avoided than suffered


if __name__ == "__main__":
    unittest.main()
