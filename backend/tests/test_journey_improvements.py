"""
Tests for journey_improvements.py — R1 split, R6 revelation,
R7/R8 mechanic variants, and persona pain point helpers.
"""

import unittest
from journey_improvements import (
    get_r1_split_config,
    should_split_r1,
    get_r6_revelation,
    get_r7_variant,
    get_r8_variant,
    get_flag_dependency_warnings,
    get_impact_magnitude,
    classify_impact_magnitude,
    R1_SPLIT_CONFIG,
    R6_REVELATION_MECHANIC,
    R7_BUDGET_ALLOCATION_VARIANT,
    R8_STAKEHOLDER_TRIBUNAL_VARIANT,
    FLAG_DEPENDENCY_WARNINGS,
    IMPACT_MAGNITUDE_LABELS,
)


class TestR1PhaseSplit(unittest.TestCase):
    """R1a/R1b split mechanics."""

    def test_r1a_config_exists(self):
        cfg = get_r1_split_config("r1a")
        self.assertIsNotNone(cfg)
        self.assertTrue(cfg["is_orientation"])
        self.assertTrue(cfg["skip_decision"])

    def test_r1b_config_exists(self):
        cfg = get_r1_split_config("r1b")
        self.assertIsNotNone(cfg)
        self.assertTrue(cfg["is_first_decision"])
        self.assertEqual(cfg["inherit_options_from"], 1)

    def test_r1a_has_orientation_tasks(self):
        cfg = get_r1_split_config("r1a")
        tasks = cfg["orientation_tasks"]
        self.assertEqual(len(tasks), 3)
        task_ids = [t["id"] for t in tasks]
        self.assertIn("read_briefing", task_ids)
        self.assertIn("stakeholder_map", task_ids)
        self.assertIn("meet_personas", task_ids)

    def test_unknown_phase_returns_none(self):
        self.assertIsNone(get_r1_split_config("r1c"))
        self.assertIsNone(get_r1_split_config(""))

    def test_split_active_for_foundation(self):
        self.assertTrue(should_split_r1("foundation"))

    def test_split_active_for_advanced(self):
        self.assertTrue(should_split_r1("advanced"))

    def test_split_inactive_for_expert(self):
        self.assertFalse(should_split_r1("expert"))

    def test_split_inactive_for_unknown_tier(self):
        self.assertFalse(should_split_r1("unknown"))

    def test_both_phases_have_pedagogical_purpose(self):
        for phase in ("r1a", "r1b"):
            cfg = get_r1_split_config(phase)
            self.assertIn("pedagogical_purpose", cfg)
            self.assertTrue(len(cfg["pedagogical_purpose"]) > 20)

    def test_both_phases_have_crisis(self):
        for phase in ("r1a", "r1b"):
            cfg = get_r1_split_config(phase)
            self.assertIn("crisis", cfg)
            self.assertIn("id", cfg["crisis"])
            self.assertIn("title", cfg["crisis"])
            self.assertIn("description", cfg["crisis"])


class TestR6Revelation(unittest.TestCase):
    """R6 whistleblower revelation mechanic."""

    def test_revelation_config_exists(self):
        rev = get_r6_revelation()
        self.assertTrue(rev["enabled"])
        self.assertEqual(rev["revelation_trigger"], "post_decision")

    def test_revelation_has_three_micro_decisions(self):
        rev = get_r6_revelation()
        self.assertEqual(len(rev["micro_decisions"]), 3)

    def test_micro_decision_keys(self):
        rev = get_r6_revelation()
        keys = set(rev["micro_decisions"].keys())
        self.assertEqual(keys, {"accept_accountability", "legal_containment", "internal_investigation"})

    def test_each_micro_decision_has_required_fields(self):
        rev = get_r6_revelation()
        for key, dec in rev["micro_decisions"].items():
            self.assertIn("label", dec, f"{key} missing label")
            self.assertIn("description", dec, f"{key} missing description")
            self.assertIn("icon", dec, f"{key} missing icon")
            self.assertIn("impacts", dec, f"{key} missing impacts")
            self.assertIn("flags_set", dec, f"{key} missing flags_set")

    def test_legal_containment_has_stochastic(self):
        rev = get_r6_revelation()
        legal = rev["micro_decisions"]["legal_containment"]
        self.assertIn("stochastic", legal)
        self.assertEqual(legal["stochastic"]["backfire_probability"], 0.40)

    def test_accept_accountability_boosts_social_license(self):
        rev = get_r6_revelation()
        acc = rev["micro_decisions"]["accept_accountability"]
        self.assertGreater(acc["impacts"]["social_license_delta"], 0)

    def test_revelation_has_pedagogical_purpose(self):
        rev = get_r6_revelation()
        self.assertIn("pedagogical_purpose", rev)
        self.assertIn("Kolb", rev["pedagogical_purpose"])


class TestR7BudgetAllocation(unittest.TestCase):
    """R7 circular economy budget allocation variant."""

    def test_variant_config_exists(self):
        v = get_r7_variant()
        self.assertTrue(v["enabled"])
        self.assertEqual(v["mechanic"], "budget_allocation")

    def test_total_budget_is_15m(self):
        v = get_r7_variant()
        self.assertEqual(v["total_budget"], 15_000_000)

    def test_has_three_initiatives(self):
        v = get_r7_variant()
        self.assertEqual(len(v["initiatives"]), 3)

    def test_initiative_keys(self):
        v = get_r7_variant()
        keys = set(v["initiatives"].keys())
        self.assertEqual(keys, {"product_redesign", "take_back_program", "waste_to_energy"})

    def test_each_initiative_has_required_fields(self):
        v = get_r7_variant()
        for key, init in v["initiatives"].items():
            self.assertIn("label", init, f"{key} missing label")
            self.assertIn("icon", init, f"{key} missing icon")
            self.assertIn("description", init, f"{key} missing description")
            self.assertIn("per_million_impact", init, f"{key} missing per_million_impact")
            self.assertIn("synergy_threshold", init, f"{key} missing synergy_threshold")
            self.assertIn("synergy_bonus", init, f"{key} missing synergy_bonus")

    def test_synergy_thresholds_are_within_budget(self):
        v = get_r7_variant()
        for key, init in v["initiatives"].items():
            self.assertLessEqual(init["synergy_threshold"], v["total_budget"],
                                 f"{key} synergy threshold exceeds total budget")

    def test_has_pedagogical_purpose(self):
        v = get_r7_variant()
        self.assertIn("Thiagarajan", v["pedagogical_purpose"])


class TestR8StakeholderTribunal(unittest.TestCase):
    """R8 stakeholder tribunal variant."""

    def test_variant_config_exists(self):
        v = get_r8_variant()
        self.assertTrue(v["enabled"])
        self.assertEqual(v["mechanic"], "stakeholder_tribunal")

    def test_has_three_challenges(self):
        v = get_r8_variant()
        self.assertEqual(len(v["challenges"]), 3)

    def test_response_time_is_90_seconds(self):
        v = get_r8_variant()
        self.assertEqual(v["response_time_seconds"], 90)

    def test_each_challenge_has_three_responses(self):
        v = get_r8_variant()
        for ch in v["challenges"]:
            self.assertEqual(len(ch["responses"]), 3,
                             f"Challenge '{ch['stakeholder']}' should have 3 responses")

    def test_response_keys_are_consistent(self):
        v = get_r8_variant()
        for ch in v["challenges"]:
            keys = set(ch["responses"].keys())
            self.assertEqual(keys, {"comply", "negotiate", "deflect"},
                             f"Challenge '{ch['stakeholder']}' has wrong response keys: {keys}")

    def test_each_response_has_impacts(self):
        v = get_r8_variant()
        for ch in v["challenges"]:
            for rkey, resp in ch["responses"].items():
                self.assertIn("impacts", resp,
                              f"{ch['stakeholder']}/{rkey} missing impacts")
                self.assertIn("label", resp,
                              f"{ch['stakeholder']}/{rkey} missing label")

    def test_has_pedagogical_purpose(self):
        v = get_r8_variant()
        self.assertIn("Freeman", v["pedagogical_purpose"])


class TestFlagDependencyWarnings(unittest.TestCase):
    """Flag dependency warning system."""

    def test_warning_rounds_covered(self):
        expected_rounds = {4, 7, 8, 10}
        actual_rounds = set(FLAG_DEPENDENCY_WARNINGS.keys())
        self.assertEqual(actual_rounds, expected_rounds)

    def test_r4_electronics_blindspot_warning(self):
        warnings = get_flag_dependency_warnings(4, {"electronics_blindspot": True})
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]["severity"], "critical")
        self.assertEqual(warnings[0]["from_round"], 1)

    def test_r7_positive_warnings(self):
        warnings = get_flag_dependency_warnings(7, {"hard_engineering": True})
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]["severity"], "positive")

    def test_no_warnings_for_missing_flags(self):
        warnings = get_flag_dependency_warnings(4, {"some_other_flag": True})
        self.assertEqual(len(warnings), 0)

    def test_no_warnings_for_uncovered_rounds(self):
        warnings = get_flag_dependency_warnings(3, {"electronics_blindspot": True})
        self.assertEqual(len(warnings), 0)

    def test_multiple_warnings_same_round(self):
        warnings = get_flag_dependency_warnings(7, {
            "hard_engineering": True,
            "nature_based_resilience": True,
        })
        self.assertEqual(len(warnings), 2)

    def test_each_warning_has_required_fields(self):
        for round_num, deps in FLAG_DEPENDENCY_WARNINGS.items():
            for flag, warning in deps.items():
                self.assertIn("from_round", warning, f"R{round_num}/{flag} missing from_round")
                self.assertIn("from_option", warning, f"R{round_num}/{flag} missing from_option")
                self.assertIn("warning", warning, f"R{round_num}/{flag} missing warning text")
                self.assertIn("severity", warning, f"R{round_num}/{flag} missing severity")
                self.assertIn(warning["severity"], ("critical", "warning", "positive"),
                              f"R{round_num}/{flag} invalid severity: {warning['severity']}")


class TestImpactMagnitude(unittest.TestCase):
    """Impact magnitude classification and labels."""

    def test_negligible_classification(self):
        self.assertEqual(classify_impact_magnitude(0, 0, 0), "negligible")

    def test_moderate_classification(self):
        self.assertEqual(classify_impact_magnitude(5_000_000, 5, 2), "moderate")

    def test_significant_classification(self):
        self.assertEqual(classify_impact_magnitude(10_000_000, 10, 5), "significant")

    def test_transformative_classification(self):
        self.assertEqual(classify_impact_magnitude(30_000_000, 15, 10), "transformative")

    def test_all_labels_have_required_fields(self):
        for key, label in IMPACT_MAGNITUDE_LABELS.items():
            self.assertIn("label", label)
            self.assertIn("icon", label)
            self.assertIn("color", label)

    def test_get_impact_magnitude_returns_label(self):
        result = get_impact_magnitude({"treasury": -10_000_000, "reputation": 8, "carbon_intensity_delta": -5})
        self.assertIn("label", result)
        self.assertIn("icon", result)
        self.assertIn("color", result)

    def test_magnitude_with_reputation_delta_key(self):
        result = get_impact_magnitude({"reputation_delta": -15})
        # -15 rep → score = 15/10 = 1.5 → moderate
        self.assertEqual(result["label"], "Moderate Impact")


if __name__ == "__main__":
    unittest.main()
