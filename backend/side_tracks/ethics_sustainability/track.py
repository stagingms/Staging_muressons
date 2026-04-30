"""
Muressons Global Command — Ethics & Sustainability Track Implementation

5-round deep dive: AI governance, modern slavery, greenwashing,
biodiversity, and just transition.

Scoring Dimensions (separate leaderboard):
  - Ethical Governance Score (0–100)
  - Human Rights Due Diligence (0–100)
  - Green Claims Integrity (0–100)
  - Biodiversity Stewardship (0–100)
  - Just Transition Commitment (0–100)
"""

from __future__ import annotations
from typing import Any

from side_tracks.base_track import BaseSideTrack
from side_tracks.ethics_sustainability.configs import ETHICS_ROUND_CONFIGS


class EthicsSustainabilityTrack(BaseSideTrack):
    """5-round Ethics & Sustainability side simulation."""

    @property
    def track_id(self) -> str:
        return "ethics_sustainability"

    @property
    def display_name(self) -> str:
        return "Ethics & Sustainability Deep Dive"

    @property
    def description(self) -> str:
        return (
            "A 5-round exploration of corporate ethics covering AI governance, "
            "human rights due diligence, greenwashing risk, biodiversity, and "
            "just transition — with real regulatory frameworks (EU AI Act, "
            "CSDDD, TNFD, SBTN)."
        )

    @property
    def icon(self) -> str:
        return "⚖️"

    @property
    def num_rounds(self) -> int:
        return 5

    @property
    def available_window(self) -> tuple[int, int]:
        return (2, 7)

    @property
    def scoring_dimensions(self) -> list[dict[str, str]]:
        return [
            {"id": "ethical_governance", "label": "Ethical Governance", "unit": "/100"},
            {"id": "human_rights_dd", "label": "Human Rights DD", "unit": "/100"},
            {"id": "green_claims_integrity", "label": "Green Claims Integrity", "unit": "/100"},
            {"id": "biodiversity_stewardship", "label": "Biodiversity Stewardship", "unit": "/100"},
            {"id": "just_transition", "label": "Just Transition", "unit": "/100"},
        ]

    @property
    def cross_track_prerequisites(self) -> list[str]:
        return ["supply_chain"]  # SC track enriches modern slavery context

    def get_round_configs(self) -> dict[int, dict[str, Any]]:
        return ETHICS_ROUND_CONFIGS

    # ── Data Bridges ────────────────────────────────────────────

    def seed_from_main_state(self, main_global, main_bus, completed_tracks):
        n = len(main_bus) or 1
        avg_gov = sum(bu.get("governance_risk_score", 20) for bu in main_bus) / n
        avg_sl = sum(bu.get("social_license_score", 50) for bu in main_bus) / n
        flags = main_global.get("active_event_flags", {})

        # Cross-track: SC findings enrich starting state
        sc_state = completed_tracks.get("supply_chain", {})
        has_sc_cobalt = sc_state.get("sc_cobalt_findings", False) or flags.get("sc_cobalt_findings")

        return {
            "ethical_governance": 15 + (10 if flags.get("deep_audit_completed") else 0),
            "human_rights_dd": 10 + (20 if has_sc_cobalt else 0),
            "green_claims_integrity": 20,
            "biodiversity_stewardship": 5,
            "just_transition": 10,
            "inherited_reputation": main_global.get("group_reputation", 50),
            "inherited_treasury": main_global.get("corporate_treasury", 50_000_000),
            "inherited_governance_risk": round(avg_gov, 2),
            "inherited_social_license": round(avg_sl, 2),
            "sc_track_completed": "supply_chain" in completed_tracks,
            "sc_cobalt_findings": has_sc_cobalt,
        }

    def write_back_to_main(self, track_state, main_global):
        flags = {}
        score = self.calculate_score(track_state)

        flags["ethics_track_completed"] = True
        flags["ethics_final_score"] = score["total_score"]
        flags["ethics_grade"] = score["grade"]
        flags["ethics_archetype"] = score["archetype"]["title"]

        if score["total_score"] >= 80:
            flags["es_track_mr_bonus"] = 0.10
        elif score["total_score"] >= 60:
            flags["es_track_mr_bonus"] = 0.05
        elif score["total_score"] < 40:
            flags["es_track_mr_penalty"] = -0.05

        # Propagate key flags for cross-track dependencies
        if track_state.get("ethical_governance", 0) >= 70:
            flags["es_governance_excellence"] = True
        if track_state.get("just_transition", 0) >= 60:
            flags["es_just_transition_credible"] = True

        return flags

    # ── Scoring ─────────────────────────────────────────────────

    def calculate_score(self, track_state):
        eg = min(100, max(0, track_state.get("ethical_governance", 0)))
        hr = min(100, max(0, track_state.get("human_rights_dd", 0)))
        gc = min(100, max(0, track_state.get("green_claims_integrity", 0)))
        bd = min(100, max(0, track_state.get("biodiversity_stewardship", 0)))
        jt = min(100, max(0, track_state.get("just_transition", 0)))

        total = round(eg * 0.25 + hr * 0.25 + gc * 0.20 + bd * 0.15 + jt * 0.15, 1)

        if total >= 85: grade = "A+"
        elif total >= 75: grade = "A"
        elif total >= 65: grade = "B"
        elif total >= 50: grade = "C"
        elif total >= 35: grade = "D"
        else: grade = "F"

        if total >= 80:
            archetype = {"title": "Ethical Vanguard", "description": "Your organisation leads on ethics, substantiating claims, protecting rights, and transitioning justly.", "icon": "🏛️", "gradient": "linear-gradient(135deg, #10b981, #059669)"}
        elif total >= 60:
            archetype = {"title": "Responsible Steward", "description": "Good foundations but some gaps — regulatory exposure remains in specific areas.", "icon": "🛡️", "gradient": "linear-gradient(135deg, #3b82f6, #2563eb)"}
        elif total >= 40:
            archetype = {"title": "Compliance Minimalist", "description": "Meeting minimum requirements but lacking substantive commitment — vulnerable to activist campaigns.", "icon": "⚠️", "gradient": "linear-gradient(135deg, #f59e0b, #d97706)"}
        else:
            archetype = {"title": "Ethics Liability", "description": "Significant ethical deficits creating material legal, reputational, and regulatory risk.", "icon": "🔥", "gradient": "linear-gradient(135deg, #ef4444, #b91c1c)"}

        return {
            "total_score": total,
            "dimensions": {"ethical_governance": eg, "human_rights_dd": hr, "green_claims_integrity": gc, "biodiversity_stewardship": bd, "just_transition": jt},
            "grade": grade,
            "archetype": archetype,
        }

    # ── Engine Hooks ────────────────────────────────────────────

    def pre_tick(self, round_number, track_state, bus, decisions, crisis_severity):
        result = {"crisis_severity": crisis_severity, "pre_events": {}}
        accumulated = set(track_state.get("accumulated_flags", []))
        choice = self._get_primary_choice(decisions)

        if round_number == 5:
            # Just Transition: prior HR leader reduces strike risk
            if "es_human_rights_leader" in accumulated:
                result["pre_events"]["union_trust_bonus"] = True
                result["crisis_severity"] = max(10, crisis_severity - 15)
            # AI denial increases strike risk
            if "es_ai_denial" in accumulated:
                result["pre_events"]["employee_distrust"] = True
                result["crisis_severity"] = min(100, crisis_severity + 10)

        return result

    def post_tick(self, round_number, global_state, bu_states, decisions, events, extra_events, previous_flags):
        extra = self._apply_default_option_impacts(round_number, global_state, bu_states, decisions, events, extra_events)
        accumulated = set(previous_flags.get("accumulated_flags", []))
        choice = self._get_primary_choice(decisions)

        if round_number == 3:
            # If AI denial was chosen in R1, greenwash scrutiny is doubled
            if "es_ai_denial" in accumulated and choice == "option_c":
                global_state["group_reputation"] = max(0, round(global_state.get("group_reputation", 50) - 5, 2))
                extra["es_compounding_credibility_penalty"] = -5

        if round_number == 5:
            # Modern slavery unresolved compounds just transition damage
            if "es_modern_slavery_unresolved" in accumulated and choice == "option_c":
                global_state["group_reputation"] = max(0, round(global_state.get("group_reputation", 50) - 8, 2))
                extra["es_workers_betrayed_compounding"] = -8

        return extra
