"""
Muressons — Sustainability Reporting Track Implementation (5 rounds)

Scoring Dimensions:
  - Regulatory Readiness (0–100)
  - Climate Disclosure Quality (0–100)
  - Social & Governance Metrics (0–100)
  - Assurance Credibility (0–100)
  - Integrated Value Creation (0–100)
"""

from __future__ import annotations
from typing import Any
from side_tracks.base_track import BaseSideTrack
from side_tracks.sustainability_reporting.configs import REPORTING_ROUND_CONFIGS
from side_tracks.bridge_schemas import DataBridgeInput, DataBridgeOutput


class SustainabilityReportingTrack(BaseSideTrack):
    """5-round Sustainability Reporting side simulation."""

    @property
    def track_id(self) -> str: return "sustainability_reporting"
    @property
    def display_name(self) -> str: return "Sustainability Reporting Deep Dive"
    @property
    def description(self) -> str:
        return "A 5-round deep dive into ESG/sustainability reporting covering CSRD readiness, climate disclosure, social metrics, assurance, and integrated value creation."
    @property
    def icon(self) -> str: return "📊"
    @property
    def num_rounds(self) -> int: return 5
    @property
    def available_window(self) -> tuple[int, int]: return (2, 8)

    @property
    def scoring_dimensions(self) -> list[dict[str, str]]:
        return [
            {"id": "regulatory_readiness", "label": "Regulatory Readiness", "unit": "/100"},
            {"id": "climate_disclosure", "label": "Climate Disclosure", "unit": "/100"},
            {"id": "social_governance", "label": "Social & Governance", "unit": "/100"},
            {"id": "assurance_credibility", "label": "Assurance Credibility", "unit": "/100"},
            {"id": "integrated_value", "label": "Integrated Value", "unit": "/100"},
        ]

    @property
    def cross_track_prerequisites(self) -> list[str]:
        return ["ethics_sustainability"]

    def get_round_configs(self) -> dict[int, dict[str, Any]]:
        return REPORTING_ROUND_CONFIGS

    def seed_from_main_state(
        self,
        main_global: dict,
        main_bus: list[dict],
        completed_tracks: dict[str, dict],
    ) -> DataBridgeInput:
        flags = main_global.get("active_event_flags", {})
        # Cross-track enrichment
        ethics_done = "ethics_sustainability" in completed_tracks
        ethics_gov  = completed_tracks.get("ethics_sustainability", {}).get("ethical_governance", 0)
        kpis = self._build_bridge_kpis(main_bus, main_global)
        return DataBridgeInput(
            treasury=main_global.get("corporate_treasury", 50_000_000),
            reputation=main_global.get("group_reputation", 50.0),
            active_flags=dict(flags),
            kpis=kpis,
            extra_state={
                # Track-specific initial scoring metrics
                "regulatory_readiness":  10 + (15 if flags.get("csrd_assessment_completed") else 0),
                "climate_disclosure":    15,
                "social_governance":     10 + (10 if ethics_done else 0),
                "assurance_credibility": 5,
                "integrated_value":      5,
                # Context for post_tick hooks
                "inherited_governance_risk": round(kpis.avg_governance_risk, 2),
                "ethics_track_completed":    ethics_done,
                "ethics_governance_score":   ethics_gov,
            },
        )

    def write_back_to_main(
        self,
        track_state: dict,
        main_global: dict,
    ) -> DataBridgeOutput:
        score = self.calculate_score(track_state)
        flags: dict = {
            "reporting_track_completed": True,
            "reporting_final_score":     score["total_score"],
            "reporting_grade":           score["grade"],
            "reporting_archetype":       score["archetype"]["title"],
        }
        if score["total_score"] >= 80:   flags["sr_track_mr_bonus"] = 0.10
        elif score["total_score"] >= 60: flags["sr_track_mr_bonus"] = 0.05
        elif score["total_score"] < 40:  flags["sr_track_mr_penalty"] = -0.05
        if track_state.get("assurance_credibility", 0) >= 70:
            flags["sr_high_assurance"] = True
        if track_state.get("integrated_value", 0) >= 60:
            flags["sr_value_creator"] = True
        return DataBridgeOutput(flags_to_set=flags)

    def calculate_score(self, track_state: dict) -> dict[str, Any]:
        rr = min(100, max(0, track_state.get("regulatory_readiness", 0)))
        cd = min(100, max(0, track_state.get("climate_disclosure", 0)))
        sg = min(100, max(0, track_state.get("social_governance", 0)))
        ac = min(100, max(0, track_state.get("assurance_credibility", 0)))
        iv = min(100, max(0, track_state.get("integrated_value", 0)))

        total = round(rr * 0.20 + cd * 0.25 + sg * 0.20 + ac * 0.20 + iv * 0.15, 1)

        if total >= 85: grade = "A+"
        elif total >= 75: grade = "A"
        elif total >= 65: grade = "B"
        elif total >= 50: grade = "C"
        elif total >= 35: grade = "D"
        else: grade = "F"

        if total >= 80:
            archetype = {"title": "Disclosure Pioneer", "description": "Best-in-class reporting with assured data, integrated value narratives, and full regulatory compliance.", "icon": "🌟", "gradient": "linear-gradient(135deg, #10b981, #059669)"}
        elif total >= 60:
            archetype = {"title": "Compliant Reporter", "description": "Meets regulatory requirements with credible data but lacks integration of sustainability into financial narrative.", "icon": "📋", "gradient": "linear-gradient(135deg, #3b82f6, #2563eb)"}
        elif total >= 40:
            archetype = {"title": "Selective Discloser", "description": "Cherry-picks favourable metrics while leaving material gaps — vulnerable to investor scrutiny.", "icon": "⚠️", "gradient": "linear-gradient(135deg, #f59e0b, #d97706)"}
        else:
            archetype = {"title": "Opaque Enterprise", "description": "Minimal disclosure creates investor uncertainty and regulatory exposure — ESG rating downgrades likely.", "icon": "🔒", "gradient": "linear-gradient(135deg, #ef4444, #b91c1c)"}

        return {"total_score": total, "dimensions": {"regulatory_readiness": rr, "climate_disclosure": cd, "social_governance": sg, "assurance_credibility": ac, "integrated_value": iv}, "grade": grade, "archetype": archetype}

    def pre_tick(self, round_number: int, track_state: dict, bus: list[dict], decisions: list[dict], crisis_severity: float) -> dict[str, Any]:
        result = {"crisis_severity": crisis_severity, "pre_events": {}}
        accumulated = set(track_state.get("accumulated_flags", []))

        if round_number == 5:
            if "sr_data_infrastructure" in accumulated:
                result["pre_events"]["data_infrastructure_bonus"] = True
                result["crisis_severity"] = max(10, crisis_severity - 10)
            if "sr_credibility_gap" in accumulated:
                result["pre_events"]["credibility_undermined"] = True
                result["crisis_severity"] = min(100, crisis_severity + 15)
        return result

    def post_tick(self, round_number: int, global_state: dict, bu_states: list[dict], decisions: list[dict], events: dict, extra_events: dict, previous_flags: dict) -> dict[str, Any]:
        extra = self._apply_default_option_impacts(round_number, global_state, bu_states, decisions, events, extra_events)
        accumulated = set(previous_flags.get("accumulated_flags", []))
        choice = self._get_primary_choice(decisions)

        if round_number == 4 and "sr_minimum_compliance" in accumulated and choice == "option_c":
            # Compounding: minimum R1 + no assurance R4 = credibility collapse
            global_state["group_reputation"] = max(0, round(global_state.get("group_reputation", 50) - 6, 2))
            extra["sr_credibility_collapse"] = -6

        if round_number == 5 and "sr_no_external_assurance" in accumulated:
            # Integrated report without assurance is hollow
            global_state["group_reputation"] = max(0, round(global_state.get("group_reputation", 50) - 4, 2))
            extra["sr_unassured_integration_penalty"] = -4
        return extra
