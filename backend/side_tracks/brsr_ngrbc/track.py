"""
Muressons — BRSR NGRBC Track Implementation (5 rounds)
"""

from __future__ import annotations
from typing import Any
from side_tracks.base_track import BaseSideTrack
from side_tracks.brsr_ngrbc.configs import BRSR_ROUND_CONFIGS


class BRSRNGRBCTrack(BaseSideTrack):
    """5-round BRSR NGRBC side simulation."""

    @property
    def track_id(self) -> str: return "brsr_ngrbc"
    @property
    def display_name(self) -> str: return "BRSR: NGRBC Deep Dive"
    @property
    def description(self) -> str:
        return "A 5-round deep dive into the SEBI BRSR framework, covering all nine NGRBC principles, Essential vs Leadership indicators, and BRSR Core assurance."
    @property
    def icon(self) -> str: return "🇮🇳"
    @property
    def num_rounds(self) -> int: return 5
    @property
    def available_window(self) -> tuple[int, int]: return (2, 8)

    @property
    def scoring_dimensions(self) -> list[dict[str, str]]:
        return [
            {"id": "governance_ethics", "label": "Governance & Ethics (P1/P7)", "unit": "/100"},
            {"id": "human_capital", "label": "Human Capital (P3/P5)", "unit": "/100"},
            {"id": "environmental", "label": "Environmental Stewardship (P6/P2)", "unit": "/100"},
            {"id": "value_chain", "label": "Value Chain & Stakeholder (P4/P8/P9)", "unit": "/100"},
            {"id": "reporting_quality", "label": "Integrated Disclosure", "unit": "/100"},
        ]

    @property
    def cross_track_prerequisites(self) -> list[str]:
        return ["sustainability_reporting", "ethics_sustainability"]

    def get_round_configs(self) -> dict[int, dict[str, Any]]:
        return BRSR_ROUND_CONFIGS

    def seed_from_main_state(self, main_global, main_bus, completed_tracks):
        flags = main_global.get("active_event_flags", {})
        n = len(main_bus) or 1
        avg_gov = sum(bu.get("governance_risk_score", 20) for bu in main_bus) / n

        reporting_done = "sustainability_reporting" in completed_tracks
        reporting_data = completed_tracks.get("sustainability_reporting", {})
        ethics_done = "ethics_sustainability" in completed_tracks

        return {
            "governance_ethics": 10 + (10 if ethics_done else 0),
            "human_capital": 10,
            "environmental": 10,
            "value_chain": 5,
            "reporting_quality": 5 + (15 if reporting_data.get("regulatory_readiness", 0) > 60 else 0),
            "inherited_reputation": main_global.get("group_reputation", 50),
            "inherited_treasury": main_global.get("corporate_treasury", 50_000_000),
            "inherited_governance_risk": round(avg_gov, 2),
            "accumulated_flags": [],
        }

    def write_back_to_main(self, track_state, main_global):
        flags = {}
        score = self.calculate_score(track_state)
        flags["brsr_track_completed"] = True
        flags["brsr_performance_score"] = score["total_score"]
        flags["brsr_grade"] = score["grade"]
        flags["brsr_archetype"] = score["archetype"]["title"]

        if score["total_score"] >= 80:
            flags["brsr_net_positive_dividend"] = 0.05
            
        accumulated = set(track_state.get("accumulated_flags", []))
        if "governance_fragility" in accumulated:
            flags["brsr_truth_premium_cost_doubled"] = True
            
        # Optional: Pass specific indicator flags back for visualizer
        for f in ["brsr_pioneer", "brsr_core_assured", "brsr_living_wage", "sdg_12_leadership", "brsr_greenwash_risk"]:
            if f in accumulated:
                flags[f] = True

        return flags

    def calculate_score(self, track_state):
        ge = min(100, max(0, track_state.get("governance_ethics", 0)))
        hc = min(100, max(0, track_state.get("human_capital", 0)))
        en = min(100, max(0, track_state.get("environmental", 0)))
        vc = min(100, max(0, track_state.get("value_chain", 0)))
        rq = min(100, max(0, track_state.get("reporting_quality", 0)))

        total = round(ge * 0.20 + hc * 0.20 + en * 0.25 + vc * 0.20 + rq * 0.15, 1)

        if total >= 85: grade = "A+"
        elif total >= 75: grade = "A"
        elif total >= 65: grade = "B"
        elif total >= 50: grade = "C"
        elif total >= 35: grade = "D"
        else: grade = "F"

        if total >= 80:
            archetype = {"title": "BRSR Pioneer", "description": "Exemplary implementation of NGRBC Leadership Indicators and rigorous BRSR Core value chain assurance.", "icon": "🏆", "gradient": "linear-gradient(135deg, #10b981, #059669)"}
        elif total >= 60:
            archetype = {"title": "Responsible Steward", "description": "Meets Essential Indicators reliably and adopts strategic Leadership practices in material areas.", "icon": "🌿", "gradient": "linear-gradient(135deg, #3b82f6, #2563eb)"}
        elif total >= 40:
            archetype = {"title": "Compliance Pragmatist", "description": "Fulfills mandatory SEBI BRSR requirements but exposes value chain to unchecked ESG risks.", "icon": "📋", "gradient": "linear-gradient(135deg, #f59e0b, #d97706)"}
        else:
            archetype = {"title": "Regulatory Laggard", "description": "Fails basic Essential indicators. High risk of regulatory action and ESG rating downgrades.", "icon": "⚠️", "gradient": "linear-gradient(135deg, #ef4444, #b91c1c)"}

        return {"total_score": total, "dimensions": {"governance_ethics": ge, "human_capital": hc, "environmental": en, "value_chain": vc, "reporting_quality": rq}, "grade": grade, "archetype": archetype}

    def pre_tick(self, round_number, track_state, bus, decisions, crisis_severity):
        result = {"crisis_severity": crisis_severity, "pre_events": {}}
        accumulated = set(track_state.get("accumulated_flags", []))

        if round_number == 5:
            if "governance_fragility" in accumulated:
                result["pre_events"]["fragility_penalty"] = True
                result["crisis_severity"] = min(100, crisis_severity + 15)
            if "brsr_core_assured" in accumulated:
                result["pre_events"]["assurance_bonus"] = True
                result["crisis_severity"] = max(10, crisis_severity - 10)
        return result

    def post_tick(self, round_number, global_state, bu_states, decisions, events, extra_events, previous_flags):
        extra = self._apply_default_option_impacts(round_number, global_state, bu_states, decisions, events, extra_events)
        
        choice = self._get_primary_choice(decisions)
        opts = self.get_round_options(round_number)
        opt = opts.get(choice, {})
        flags_set = opt.get("flags_set", [])
        
        # Track metric state updates based on choices
        accumulated = list(previous_flags.get("accumulated_flags", []))
        for f in flags_set:
            if f not in accumulated:
                accumulated.append(f)
        
        extra[f"st_{self.track_id}_accumulated_flags"] = accumulated
        
        # Update specific BRSR track state dimensions
        if round_number == 1:
            if choice == "option_a": extra[f"st_{self.track_id}_custom_governance_ethics"] = 80
            elif choice == "option_b": extra[f"st_{self.track_id}_custom_governance_ethics"] = 50
            else: extra[f"st_{self.track_id}_custom_governance_ethics"] = 0
            
        elif round_number == 2:
            if choice == "option_a": extra[f"st_{self.track_id}_custom_human_capital"] = 80
            elif choice == "option_b": extra[f"st_{self.track_id}_custom_human_capital"] = 50
            else: extra[f"st_{self.track_id}_custom_human_capital"] = 0
            
        elif round_number == 3:
            if choice == "option_a": extra[f"st_{self.track_id}_custom_environmental"] = 80
            elif choice == "option_b": extra[f"st_{self.track_id}_custom_environmental"] = 50
            else: extra[f"st_{self.track_id}_custom_environmental"] = 0
            
        elif round_number == 4:
            if choice == "option_a": extra[f"st_{self.track_id}_custom_value_chain"] = 80
            elif choice == "option_b": extra[f"st_{self.track_id}_custom_value_chain"] = 50
            else: extra[f"st_{self.track_id}_custom_value_chain"] = 0
            
        elif round_number == 5:
            if choice == "option_a": extra[f"st_{self.track_id}_custom_reporting_quality"] = 80
            elif choice == "option_b": extra[f"st_{self.track_id}_custom_reporting_quality"] = 50
            else: extra[f"st_{self.track_id}_custom_reporting_quality"] = 0

        # Special side effects directly modifying global state
        if round_number == 2 and choice == "option_a":
            # Reduce burnout across BUs
            for bu in bu_states:
                bu["staff_burnout_index"] = max(0, bu.get("staff_burnout_index", 0) - 12)
                
        if round_number == 3 and choice == "option_a":
            # Synergy bonus
            global_state["synergy_multiplier"] = min(2.0, global_state.get("synergy_multiplier", 1.0) + 0.30)
            extra["brsr_synergy_boost"] = True

        # Dynamic BRSR Crisis Events injected into the engine loop
        if round_number == 4 and "brsr_greenwash_risk" in accumulated:
            extra["brsr_greenwash_crisis"] = "SEBI issues a show-cause notice regarding unverifiable Scope 3 claims. Value chain restructuring required."
            global_state["group_reputation"] = max(10, global_state.get("group_reputation", 50) - 12)

        if round_number == 5 and "governance_fragility" in accumulated:
            extra["brsr_governance_crisis"] = "A major whistleblower leak regarding unreported political contributions triggers SEBI scrutiny. Confidence plummets."
            global_state["corporate_treasury"] = max(0, global_state.get("corporate_treasury", 0) - 2_500_000)

        return extra
