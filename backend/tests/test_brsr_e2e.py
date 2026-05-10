import unittest
import copy
from side_tracks import get_track

class TestBRSRTrack(unittest.TestCase):
    def setUp(self):
        self.track = get_track("brsr_ngrbc")
        self.main_gs = {"corporate_treasury": 50_000_000, "group_reputation": 60, "active_event_flags": {}}
        self.main_bus = [{"governance_risk_score": 25, "social_license_score": 50}]

    def test_identity(self):
        self.assertEqual(self.track.track_id, "brsr_ngrbc")
        self.assertEqual(self.track.num_rounds, 5)

    def test_scoring_pioneer(self):
        state = {
            "governance_ethics": 90,
            "human_capital": 90,
            "environmental": 90,
            "value_chain": 90,
            "reporting_quality": 90
        }
        score = self.track.calculate_score(state)
        self.assertEqual(score["grade"], "A+")
        self.assertEqual(score["archetype"]["title"], "BRSR Pioneer")

        flags = self.track.write_back_to_main(state, self.main_gs)
        self.assertEqual(flags["brsr_net_positive_dividend"], 0.05)

    def test_greenwash_crisis_injection(self):
        gs = copy.deepcopy(self.main_gs)
        bus = copy.deepcopy(self.main_bus)
        prev = {"accumulated_flags": ["brsr_greenwash_risk"]}
        
        # Round 4 post_tick should inject greenwash crisis
        extra = self.track.post_tick(4, gs, bus, [{"choice_selected": "option_c"}], {}, {}, prev)
        self.assertIn("brsr_greenwash_crisis", extra)
        self.assertEqual(gs["group_reputation"], 40)  # 60 - 12 (crisis) - 8 (option C cost)
        
    def test_governance_crisis_injection(self):
        gs = copy.deepcopy(self.main_gs)
        bus = copy.deepcopy(self.main_bus)
        prev = {"accumulated_flags": ["governance_fragility"]}
        
        # Round 5 post_tick should inject governance crisis
        extra = self.track.post_tick(5, gs, bus, [{"choice_selected": "option_c"}], {}, {}, prev)
        self.assertIn("brsr_governance_crisis", extra)
        self.assertEqual(gs["corporate_treasury"], 47_000_000) # 50m - 2.5m (crisis) - 500k (option C cost)

if __name__ == "__main__":
    unittest.main()
