"""
Muressons — Stakeholder Management Track Implementation (4 rounds)

Scoring Dimensions:
  - Stakeholder Mapping Quality (0–100)
  - Investor Confidence (0–100)
  - Community Trust (0–100)
  - Crisis Resilience (0–100)
"""

from __future__ import annotations
from typing import Any
from side_tracks.base_track import BaseSideTrack
from side_tracks.stakeholder_management.configs import STAKEHOLDER_ROUND_CONFIGS
from side_tracks.bridge_schemas import DataBridgeInput, DataBridgeOutput


class StakeholderManagementTrack(BaseSideTrack):
    """4-round Stakeholder Management side simulation."""

    @property
    def track_id(self) -> str: return "stakeholder_management"
    @property
    def display_name(self) -> str: return "Stakeholder Management Deep Dive"
    @property
    def description(self) -> str:
        return "A 4-round deep dive into stakeholder engagement: salience mapping, ESG disclosure, community relations, and crisis communication."
    @property
    def icon(self) -> str: return "🤝"
    @property
    def num_rounds(self) -> int: return 4
    @property
    def available_window(self) -> tuple[int, int]: return (1, 6)

    @property
    def scoring_dimensions(self) -> list[dict[str, str]]:
        return [
            {"id": "stakeholder_mapping", "label": "Stakeholder Mapping", "unit": "/100"},
            {"id": "investor_confidence", "label": "Investor Confidence", "unit": "/100"},
            {"id": "community_trust", "label": "Community Trust", "unit": "/100"},
            {"id": "crisis_resilience", "label": "Crisis Resilience", "unit": "/100"},
        ]

    @property
    def cross_track_prerequisites(self) -> list[str]: return []

    def get_round_configs(self) -> dict[int, dict[str, Any]]:
        return STAKEHOLDER_ROUND_CONFIGS

    def seed_from_main_state(
        self,
        main_global: dict,
        main_bus: list[dict],
        completed_tracks: dict[str, dict] = None,
    ) -> DataBridgeInput:
        completed_tracks = completed_tracks or {}
        n = max(len(main_bus), 1)
        avg_sl = sum(bu.get("social_license_score", 50) for bu in main_bus) / n
        flags = main_global.get("active_event_flags", {})
        kpis = self._build_bridge_kpis(main_bus, main_global)
        return DataBridgeInput(
            treasury=main_global.get("corporate_treasury", 50_000_000),
            reputation=main_global.get("group_reputation", 50.0),
            active_flags=dict(flags),
            kpis=kpis,
            extra_state={
                # Track-specific initial scoring metrics
                "stakeholder_mapping":   15 + (10 if flags.get("stakeholder_map_completed") else 0),
                "investor_confidence":   20,
                "community_trust":       round(avg_sl * 0.4, 1),
                "crisis_resilience":     10,
                # Context for post_tick hooks
                "inherited_social_license":      round(avg_sl, 2),
                "main_stakeholder_accuracy":     flags.get("stakeholder_map_accuracy", 50),
            },
        )

    def write_back_to_main(
        self,
        track_state: dict,
        main_global: dict,
    ) -> DataBridgeOutput:
        score = self.calculate_score(track_state)
        flags: dict = {
            "stakeholder_track_completed": True,
            "stakeholder_final_score":     score["total_score"],
            "stakeholder_grade":           score["grade"],
            "stakeholder_archetype":       score["archetype"]["title"],
        }
        if score["total_score"] >= 80:   flags["sm_track_mr_bonus"] = 0.08
        elif score["total_score"] >= 60: flags["sm_track_mr_bonus"] = 0.04
        elif score["total_score"] < 40:  flags["sm_track_mr_penalty"] = -0.04
        if track_state.get("community_trust", 0) >= 70:
            flags["sm_strong_social_license"] = True
        if track_state.get("crisis_resilience", 0) >= 60:
            flags["sm_crisis_ready"] = True
        return DataBridgeOutput(flags_to_set=flags)

    def calculate_score(self, track_state: dict) -> dict[str, Any]:
        sm = min(100, max(0, track_state.get("stakeholder_mapping", 0)))
        ic = min(100, max(0, track_state.get("investor_confidence", 0)))
        ct = min(100, max(0, track_state.get("community_trust", 0)))
        cr = min(100, max(0, track_state.get("crisis_resilience", 0)))

        total = round(sm * 0.25 + ic * 0.25 + ct * 0.25 + cr * 0.25, 1)

        if total >= 85: grade = "A+"
        elif total >= 75: grade = "A"
        elif total >= 65: grade = "B"
        elif total >= 50: grade = "C"
        elif total >= 35: grade = "D"
        else: grade = "F"

        if total >= 80:
            archetype = {"title": "Stakeholder Champion", "description": "Deep engagement across all groups creates durable trust and crisis immunity.", "icon": "🏆", "gradient": "linear-gradient(135deg, #10b981, #059669)"}
        elif total >= 60:
            archetype = {"title": "Engaged Operator", "description": "Good stakeholder relationships with room for deeper community integration.", "icon": "🤝", "gradient": "linear-gradient(135deg, #3b82f6, #2563eb)"}
        elif total >= 40:
            archetype = {"title": "Transactional Manager", "description": "Stakeholder engagement is procedural — lacking authentic commitment.", "icon": "📋", "gradient": "linear-gradient(135deg, #f59e0b, #d97706)"}
        else:
            archetype = {"title": "Isolated Enterprise", "description": "Stakeholder relationships are adversarial — creating material governance risk.", "icon": "🏚️", "gradient": "linear-gradient(135deg, #ef4444, #b91c1c)"}

        return {"total_score": total, "dimensions": {"stakeholder_mapping": sm, "investor_confidence": ic, "community_trust": ct, "crisis_resilience": cr}, "grade": grade, "archetype": archetype}

    def pre_tick(self, round_number: int, track_state: dict, bus: list[dict], decisions: list[dict], crisis_severity: float) -> dict[str, Any]:
        result = {"crisis_severity": crisis_severity, "pre_events": {}}
        accumulated = set(track_state.get("accumulated_flags", []))

        if round_number == 4:
            if "sm_engagement_policy" in accumulated:
                result["crisis_severity"] = max(10, crisis_severity - 12)
                result["pre_events"]["crisis_playbook_active"] = True
            if "sm_reactive_approach" in accumulated:
                result["crisis_severity"] = min(100, crisis_severity + 10)
                result["pre_events"]["no_crisis_playbook"] = True
        return result

    def post_tick(self, round_number: int, global_state: dict, bu_states: list[dict], decisions: list[dict], events: dict, extra_events: dict, previous_flags: dict) -> dict[str, Any]:
        extra = self._apply_default_option_impacts(round_number, global_state, bu_states, decisions, events, extra_events)
        accumulated = set(previous_flags.get("accumulated_flags", []))
        choice = self._get_primary_choice(decisions)

        if round_number == 4 and "sm_community_overridden" in accumulated and choice == "option_c":
            global_state["group_reputation"] = max(0, round(global_state.get("group_reputation", 50) - 6, 2))
            extra["sm_community_backlash_compounding"] = -6

        # ── ITEM 25: Mitchell/Agle/Wood Dynamic Salience ─────
        salience = self._compute_dynamic_salience(
            round_number, accumulated, choice, global_state
        )
        extra["stakeholder_salience"] = salience

        return extra

    # ── Mitchell/Agle/Wood Stakeholder Salience Framework ────
    # Stakeholders are classified by 3 attributes: Power, Legitimacy, Urgency
    # Each attribute: 0-100. Classification:
    #   Dormant    = P only (no L, no U)
    #   Discretionary = L only
    #   Demanding  = U only
    #   Dominant   = P + L
    #   Dangerous  = P + U
    #   Dependent  = L + U
    #   Definitive = P + L + U (highest salience — demands immediate attention)

    _STAKEHOLDER_BASE_SALIENCE = {
        "institutional_investors": {"power": 85, "legitimacy": 80, "urgency": 40},
        "activist_shareholders": {"power": 35, "legitimacy": 60, "urgency": 90},
        "local_communities": {"power": 20, "legitimacy": 90, "urgency": 50},
        "employees_unions": {"power": 45, "legitimacy": 85, "urgency": 35},
        "regulators": {"power": 90, "legitimacy": 95, "urgency": 30},
        "media_ngos": {"power": 50, "legitimacy": 70, "urgency": 70},
        "customers": {"power": 60, "legitimacy": 75, "urgency": 25},
        "suppliers": {"power": 30, "legitimacy": 65, "urgency": 20},
    }

    def _compute_dynamic_salience(
        self,
        round_number: int,
        accumulated_flags: set,
        choice: str,
        global_state: dict,
    ) -> dict:
        """Compute dynamic salience scores and classifications for all stakeholders."""
        import copy
        salience_map = copy.deepcopy(self._STAKEHOLDER_BASE_SALIENCE)

        # Dynamic migrations based on accumulated flags and choices
        if "sm_dynamic_salience" in accumulated_flags:
            # Formal mapping improves visibility → all urgency scores +10
            for s in salience_map.values():
                s["urgency"] = min(100, s["urgency"] + 10)

        if "sm_community_overridden" in accumulated_flags:
            # Community overridden → local communities become definitive
            salience_map["local_communities"]["power"] += 40
            salience_map["local_communities"]["urgency"] += 30
            salience_map["media_ngos"]["urgency"] += 20

        if "sm_reactive_approach" in accumulated_flags:
            # Reactive → regulators and activists gain urgency
            salience_map["regulators"]["urgency"] += 25
            salience_map["activist_shareholders"]["power"] += 15

        if "sm_crisis_leader" in accumulated_flags:
            # Crisis leadership → reduces urgency across board
            for s in salience_map.values():
                s["urgency"] = max(0, s["urgency"] - 15)

        if "sm_cba_signed" in accumulated_flags:
            # Community Benefit Agreement → communities become discretionary
            salience_map["local_communities"]["urgency"] = max(0, salience_map["local_communities"]["urgency"] - 30)
            salience_map["local_communities"]["legitimacy"] = min(100, salience_map["local_communities"]["legitimacy"] + 10)

        # Round-specific escalations
        if round_number >= 3:
            salience_map["activist_shareholders"]["power"] += 10 * (round_number - 2)
        if round_number == 4:
            # Crisis round: urgency spikes for everyone
            for s in salience_map.values():
                s["urgency"] = min(100, s["urgency"] + 15)

        # Reputation-based modulation
        rep = global_state.get("group_reputation", 50)
        if rep < 30:
            salience_map["regulators"]["urgency"] += 20
            salience_map["media_ngos"]["urgency"] += 25

        # Classify each stakeholder
        result = {}
        threshold = 50  # Attribute is "active" above this threshold
        for name, scores in salience_map.items():
            p = min(100, max(0, scores["power"]))
            l = min(100, max(0, scores["legitimacy"]))
            u = min(100, max(0, scores["urgency"]))

            has_p = p >= threshold
            has_l = l >= threshold
            has_u = u >= threshold

            if has_p and has_l and has_u:
                classification = "Definitive"
                priority = "🔴 Critical"
            elif has_p and has_l:
                classification = "Dominant"
                priority = "🟠 High"
            elif has_p and has_u:
                classification = "Dangerous"
                priority = "🟠 High"
            elif has_l and has_u:
                classification = "Dependent"
                priority = "🟡 Medium"
            elif has_p:
                classification = "Dormant"
                priority = "🟢 Low"
            elif has_l:
                classification = "Discretionary"
                priority = "🟢 Low"
            elif has_u:
                classification = "Demanding"
                priority = "🟡 Medium"
            else:
                classification = "Non-stakeholder"
                priority = "⚪ None"

            result[name] = {
                "power": p,
                "legitimacy": l,
                "urgency": u,
                "classification": classification,
                "priority": priority,
            }

        return {
            "stakeholders": result,
            "framework": "Mitchell, Agle & Wood (1997)",
            "note": "Stakeholder salience evolves based on your decisions and round events.",
        }
