"""
Muressons Global Corporation — Corporate SDG Side Track Implementation

Five-round parallel track focused on UN SDG alignment.
Follows the BaseSideTrack contract for data bridges, scoring, and engine hooks.

SDG Impact Score feeds into the M_SDG terminal valuation multiplier:
  M_SDG = 1.0 + (SDG_Impact_Score / 100) × 0.25

Integration Mechanics (v2 — Deep Integration):
  - Flag propagation: custom_metrics deltas are applied to real BU states
  - BU-specific targeting: each round impacts the correct BU's metrics
  - SDG drag/boost: low SDG scores raise regulatory_ratchet; high scores reduce NCD rate
  - Greenwash wiring: greenwash_risk flag activates main-engine scandal detection
  - SDG state machine: sdg_track_state dict carries forward cumulative modifiers
"""

from __future__ import annotations
from typing import Any
import copy

from side_tracks.base_track import BaseSideTrack
from side_tracks.bridge_schemas import DataBridgeInput, DataBridgeOutput
from side_tracks.corporate_sdg.configs import (
    SDG_ROUND_CONFIGS,
    SDG_POINTS_MAP,
    get_sdg_round_config,
    get_sdg_round_options,
)


# ── BU Targeting Map ────────────────────────────────────────────
# Each SDG round targets specific BUs for its custom_metrics impacts.
# This ensures that e.g. Living Wage affects Electronics/Consumer burnout,
# not a uniform group-level average.

SDG_ROUND_TARGET_BUS: dict[int, list[str]] = {
    1: [],                                        # PAI Audit → group-wide (no BU-specific)
    2: ["electronics", "consumer_goods"],          # Living Wage → labor-intensive BUs
    3: ["electronics", "consumer_goods"],          # Circular Procurement → material BUs
    4: ["consumer_goods", "pharma"],              # Biodiversity → palm oil & API-dependent
    5: [],                                        # Integrated Reporting → group-wide
}

# ── Custom Metrics → BU State Key Mapping ───────────────────────
# Maps custom_metric keys from configs.py options to actual BU state keys.
CUSTOM_METRIC_TO_BU_KEY = {
    "burnout_delta":            "staff_burnout_index",
    "base_strike_risk":         "strike_probability",
    "workforce_readiness_delta":"workforce_readiness",
    "synergy_bonus":            "_synergy_bonus_pending",  # applied to global state
}


class CorporateSDGTrack(BaseSideTrack):
    """
    Corporate SDG Deep Track — 5 rounds of SDG alignment decisions.

    Scoring:
      SDG Impact Score = Σ(points per round choice)
      Range: -11 (all C) to 105 (all A)
      Feeds into M_SDG at terminal valuation.

    Deep Integration (v2):
      - custom_metrics deltas propagate into real BU states
      - BU-specific targeting routes impacts to the right BUs
      - SDG drag/boost modifies main sim flags per round
      - greenwash_risk activates the existing scandal detection engine
    """

    @property
    def track_id(self) -> str:
        return "corporate_sdg"

    @property
    def display_name(self) -> str:
        return "Corporate SDG Deep Track"

    @property
    def description(self) -> str:
        return (
            "Five-round SDG alignment track covering Principal Adverse Impact "
            "reporting, Living Wage commitments, Circular Procurement, "
            "Biodiversity Net-Gain, and Integrated Reporting. Decisions feed "
            "into the M_SDG terminal valuation multiplier and propagate "
            "real consequences into BU operational metrics."
        )

    @property
    def icon(self) -> str:
        return "🌐"

    @property
    def num_rounds(self) -> int:
        return 5

    @property
    def available_window(self) -> tuple[int, int]:
        # Independently triggerable from R1 through R8
        return (1, 8)

    @property
    def scoring_dimensions(self) -> list[dict[str, str]]:
        return [
            {"id": "sdg_impact_score", "label": "SDG Impact Score", "unit": "/105"},
            {"id": "sdg_integrity", "label": "SDG Integrity", "unit": "✓/✗"},
            {"id": "circular_leader", "label": "Circular Leader", "unit": "✓/✗"},
            {"id": "nature_positive", "label": "Nature Positive", "unit": "✓/✗"},
            {"id": "greenwash_risk_level", "label": "Greenwash Risk", "unit": "/100"},
        ]

    @property
    def cross_track_prerequisites(self) -> list[str]:
        return []  # No prerequisites

    # ── Round Configuration ─────────────────────────────────────

    def get_round_configs(self) -> dict[int, dict[str, Any]]:
        return copy.deepcopy(SDG_ROUND_CONFIGS)

    # ── Data Bridges ────────────────────────────────────────────

    def seed_from_main_state(
        self,
        main_global: dict,
        main_bus: list[dict],
        completed_tracks: dict[str, dict] = None,
    ) -> DataBridgeInput:
        """
        DATA BRIDGE (READ): Initialize SDG track state from main sim.
        Pulls NCD, reputation, governance risk, and existing flags.
        """
        completed_tracks = completed_tracks or {}
        flags = main_global.get("active_event_flags", {})
        kpis = self._build_bridge_kpis(main_bus, main_global)
        return DataBridgeInput(
            treasury=main_global.get("corporate_treasury", 50_000_000),
            reputation=main_global.get("group_reputation", 50.0),
            active_flags=dict(flags),
            kpis=kpis,
            extra_state={
                # Track-specific initial state (all required by post_tick / calculate_score)
                "sdg_impact_score":       0,
                "round_choices":          {},
                "round_points":           {},
                "flags_earned":           {},
                "initial_group_reputation": main_global.get("group_reputation", 50),
                "initial_ncd_avg":        round(
                    sum(bu.get("natural_capital_debt", 0) for bu in main_bus)
                    / max(len(main_bus), 1), 2
                ),
                "pai_blindspot_active":   bool(flags.get("pai_blindspot", False)),
                "total_treasury_spent":   0,
                "sdg_score_history":      [],
                "drag_applied_rounds":    [],
            },
        )

    def write_back_to_main(
        self,
        track_state: dict,
        main_global: dict,
    ) -> DataBridgeOutput:
        """
        DATA BRIDGE (WRITE): Merge SDG track results into main sim flags.
        The sdg_impact_score is the critical output — feeds into M_SDG.

        V2 fix: flags_earned contains a mix of internal SDG scoring bookmarks
        (e.g. 'circular_leader', 'nature_positive', 'greenwash_risk') and
        main-sim flags. We use filter_unregistered=True so that only
        registered-prefix flags are promoted — internal bookmarks stay
        inside the SDG track's own state and are NOT injected into main sim.
        This prevents arbitrary key injection while preserving M_SDG output.
        """
        flags: dict = {
            "sdg_impact_score":    track_state.get("sdg_impact_score", 0),
            "sdg_track_completed": True,
            "sdg_score_history":   track_state.get("sdg_score_history", []),
        }
        # Merge earned flags — filter_unregistered drops internal bookmarks
        # (e.g. 'greenwash_risk', 'circular_leader') that don't need to reach
        # the main sim because the SDG post_tick already writes them to
        # global_state["active_event_flags"] in real-time during play.
        for flag_key, flag_val in track_state.get("flags_earned", {}).items():
            flags[flag_key] = flag_val
        mr_bonus = track_state.get("mr_bonus_accumulated", 0)
        if mr_bonus > 0:
            flags["sdg_mr_bonus"] = mr_bonus
        return DataBridgeOutput.from_legacy_dict(flags, filter_unregistered=True)

    def calculate_score(self, track_state: dict) -> dict[str, Any]:
        """
        Calculate final SDG track leaderboard score.
        """
        score = track_state.get("sdg_impact_score", 0)
        flags = track_state.get("flags_earned", {})

        # Normalize to 0-100 scale (max raw is 105)
        normalized = round(max(0, min(100, (score / 105) * 100)), 1)

        # Grade assignment
        if normalized >= 90:
            grade, archetype = "A+", {"title": "SDG Champion", "icon": "🌟", "description": "Comprehensive SDG alignment across all dimensions"}
        elif normalized >= 75:
            grade, archetype = "A", {"title": "SDG Leader", "icon": "🏆", "description": "Strong SDG performance with minor gaps"}
        elif normalized >= 60:
            grade, archetype = "B", {"title": "SDG Performer", "icon": "📈", "description": "Meaningful SDG progress with room for improvement"}
        elif normalized >= 40:
            grade, archetype = "C", {"title": "SDG Starter", "icon": "📋", "description": "Basic SDG awareness but significant gaps remain"}
        else:
            grade, archetype = "D", {"title": "SDG Laggard", "icon": "⚠️", "description": "Critical SDG gaps creating material risk"}

        return {
            "total_score": normalized,
            "raw_sdg_points": score,
            "max_possible_points": 105,
            "dimensions": {
                "sdg_impact_score": score,
                "sdg_integrity": bool(flags.get("sdg_integrity_unlocked")),
                "circular_leader": bool(flags.get("circular_leader")),
                "nature_positive": bool(flags.get("nature_positive")),
                "greenwash_risk_level": 80 if flags.get("greenwash_risk") else 0,
            },
            "grade": grade,
            "archetype": archetype,
            "m_sdg_projection": round(1.0 + (score / 100.0) * 0.25, 4),
        }

    # ── Engine Hooks ────────────────────────────────────────────

    def pre_tick(
        self,
        round_number: int,
        track_state: dict,
        bus: list[dict],
        decisions: list[dict],
        crisis_severity: float,
    ) -> dict[str, Any]:
        """
        Pre-tick: Check for pai_blindspot multiplier on ST-R2.
        """
        result = {
            "crisis_severity": crisis_severity,
            "pre_events": {},
        }

        # ST-R2: If pai_blindspot is active, double the Living Wage Strike severity
        if round_number == 2 and track_state.get("pai_blindspot_active"):
            result["pre_events"]["pai_blindspot_triggered"] = True
            result["pre_events"]["strike_severity_doubled"] = True

        return result

    def post_tick(
        self,
        round_number: int,
        global_state: dict,
        bu_states: list[dict],
        decisions: list[dict],
        events: dict,
        extra_events: dict,
        previous_flags: dict,
    ) -> dict[str, Any]:
        """
        Post-tick: Apply SDG round impacts, accumulate SDG Impact Score,
        propagate custom_metrics to BU states, and apply round-by-round
        SDG drag/boost effects to the main simulation.
        """
        # Apply default option impacts (treasury, reputation, NCD, etc.)
        extra = self._apply_default_option_impacts(
            round_number, global_state, bu_states, decisions, events, extra_events
        )

        # Get the chosen option
        choice = self._get_primary_choice(decisions)
        cfg = get_sdg_round_config(round_number)
        if not cfg:
            return extra

        opt = cfg["options"].get(choice, {})

        # Accumulate SDG Impact Score
        points = opt.get("sdg_points", 0)

        # PAI blindspot doubles strike damage on ST-R2
        if round_number == 2 and events.get("pai_blindspot_triggered"):
            rep_hit = opt.get("impacts", {}).get("reputation", 0)
            if rep_hit < 0:
                current_rep = global_state.get("group_reputation", 50)
                if current_rep is not None:  # VUL-009: None guard
                    global_state["group_reputation"] = max(
                        0, round(current_rep + rep_hit, 2)
                    )
                extra["pai_blindspot_reputation_doubled"] = rep_hit

        # VUL-005/023 FIX: read persistent scoring state from previous_flags["track_state"]
        # NOT from global_state["_sdg_track_state"] which is ephemeral (rebuilt each tick).
        # The router passes full track_data["state"] as previous_flags["track_state"].
        track_state: dict = previous_flags.get("track_state", {})

        track_state.setdefault("round_choices", {})[round_number] = choice
        track_state.setdefault("round_points", {})[round_number] = points

        # Accumulate total score across ALL rounds (now correct because track_state persists)
        total_score = sum(track_state.get("round_points", {}).values())
        track_state["sdg_impact_score"] = total_score

        # ── FIX 1: Propagate custom_metrics to BU states ────────
        self._apply_custom_metrics_to_bus(
            round_number, opt, bu_states, global_state, extra
        )

        # Accumulate M_R bonus from custom_metrics
        mr_bonus = opt.get("custom_metrics", {}).get("mr_bonus", 0)
        if mr_bonus > 0:
            track_state["mr_bonus_accumulated"] = track_state.get("mr_bonus_accumulated", 0) + mr_bonus

        # Collect flags
        for flag_key, flag_val in opt.get("flags", {}).items():
            track_state.setdefault("flags_earned", {})[flag_key] = flag_val
            # Also set in main global flags for immediate effect
            global_state.setdefault("active_event_flags", {})[flag_key] = flag_val

        # ── FIX 5: Wire greenwash_risk into main scandal engine ─
        if opt.get("flags", {}).get("greenwash_risk"):
            global_state.setdefault("active_event_flags", {})["greenwash_detected"] = True
            global_state["active_event_flags"]["greenwash_scandal_source"] = "sdg_spot_market_compliance"
            extra["sdg_greenwash_scandal_activated"] = True
            extra["sdg_greenwash_narrative"] = (
                "📰 SDG GREENWASH ALERT: Spot-market circularity credit purchases detected. "
                "NGO analysis reveals no underlying operational change — SDG 12 claim is performative. "
                "Credibility penalty applied to brand valuation."
            )

        # ── FIX 2: Operational Hardball — elevate strike probability ─
        if opt.get("flags", {}).get("operational_hardball"):
            # Set the base_strike_risk directly in global flags for the main strike engine
            current_risk = global_state.get("active_event_flags", {}).get("base_strike_risk", 0.2)
            global_state["active_event_flags"]["base_strike_risk"] = max(
                current_risk,
                opt.get("custom_metrics", {}).get("base_strike_risk", 0.50)
            )
            global_state["active_event_flags"]["strike_probability"] = True
            extra["operational_hardball_strike_risk_elevated"] = True

        # ── FIX 2: Nature-positive → reduce NCD compound rate ───
        if track_state.get("flags_earned", {}).get("nature_positive"):
            # Reduce NCD interest rate by 1% per round after nature_positive is earned
            current_rate = global_state.get("ncd_interest_rate", 0.05)
            global_state["ncd_interest_rate"] = round(max(0.01, current_rate - 0.01), 4)
            extra["nature_positive_ncd_rate_reduced"] = True

        # ── FIX 2: Round-by-round SDG drag/boost ────────────────
        # VUL-006 FIX: idempotency guard now works correctly because track_state
        # is read from previous_flags["track_state"] (persistent) not global_state.
        self._apply_sdg_drag_boost(total_score, round_number, global_state, track_state, extra)

        # Track treasury spend
        treasury_cost = abs(opt.get("impacts", {}).get("treasury", 0))
        track_state["total_treasury_spent"] = track_state.get("total_treasury_spent", 0) + treasury_cost

        # ── FIX 4: Update SDG score history (sparkline data) ────
        m_sdg_current = round(1.0 + (total_score / 100.0) * 0.25, 4)
        track_state.setdefault("sdg_score_history", []).append({
            "sdg_track_round": round_number,
            "score": total_score,
            "m_sdg": m_sdg_current,
            "choice": choice,
            "points": points,
        })

        # VUL-005/023 FIX: Write updated track_state back via custom events
        # so the router's event-merge loop (lines 3982-3990) stores it in
        # track_data["state"] under each key. Emit each mutable key individually.
        extra[f"st_{self.track_id}_custom_round_points"]          = track_state["round_points"]
        extra[f"st_{self.track_id}_custom_round_choices"]         = track_state["round_choices"]
        extra[f"st_{self.track_id}_custom_sdg_impact_score"]      = track_state["sdg_impact_score"]
        extra[f"st_{self.track_id}_custom_sdg_score_history"]     = track_state.get("sdg_score_history", [])
        extra[f"st_{self.track_id}_custom_flags_earned"]          = track_state.get("flags_earned", {})
        extra[f"st_{self.track_id}_custom_total_treasury_spent"]  = track_state.get("total_treasury_spent", 0)
        extra[f"st_{self.track_id}_custom_mr_bonus_accumulated"]  = track_state.get("mr_bonus_accumulated", 0)
        extra[f"st_{self.track_id}_custom_drag_applied_rounds"]   = track_state.get("drag_applied_rounds", [])

        # Surface SDG progress in extra events
        extra["sdg_track_progress"] = {
            "round": round_number,
            "choice": choice,
            "points_awarded": points,
            "cumulative_score": total_score,
            "m_sdg_projection": m_sdg_current,
            "rounds_remaining": 5 - round_number,
            "flags_active": list(track_state.get("flags_earned", {}).keys()),
        }

        return extra

    # ── Private Helpers ──────────────────────────────────────────

    def _apply_custom_metrics_to_bus(
        self,
        round_number: int,
        opt: dict,
        bu_states: list[dict],
        global_state: dict,
        extra: dict,
    ) -> None:
        """
        FIX 1 + FIX 3: Propagate custom_metrics deltas from the chosen
        SDG option into the correct target BUs' live state.

        Targets are defined by SDG_ROUND_TARGET_BUS; if empty, applies group-wide.
        """
        custom = opt.get("custom_metrics", {})
        if not custom:
            return

        target_bus = SDG_ROUND_TARGET_BUS.get(round_number, [])

        for bu in bu_states:
            bu_id = bu.get("bu_id", "")
            # If targeting is specified, skip non-target BUs
            if target_bus and bu_id not in target_bus:
                continue

            applied = {}

            # burnout_delta → staff_burnout_index
            if "burnout_delta" in custom:
                delta = custom["burnout_delta"]
                old = bu.get("staff_burnout_index", 25)
                bu["staff_burnout_index"] = round(max(0, min(100, old + delta)), 2)
                applied["staff_burnout_index"] = bu["staff_burnout_index"]

            # workforce_readiness_delta → workforce_readiness
            if "workforce_readiness_delta" in custom:
                delta = custom["workforce_readiness_delta"]
                old = bu.get("workforce_readiness", 50)
                bu["workforce_readiness"] = round(max(0, min(100, old + delta)), 2)
                applied["workforce_readiness"] = bu["workforce_readiness"]

            if applied:
                extra[f"sdg_bu_metrics_applied_{bu_id}_r{round_number}"] = applied

        # synergy_bonus → applied to global synergy multiplier
        if "synergy_bonus" in custom:
            sb = custom["synergy_bonus"]
            # Accumulate synergy bonus in global state (capped at 1.35)
            current_synergy = global_state.get("synergy_multiplier", 1.0)
            global_state["synergy_multiplier"] = round(min(1.35, current_synergy + sb * 0.05), 4)
            extra["sdg_synergy_multiplier_boosted"] = global_state["synergy_multiplier"]

    def _apply_sdg_drag_boost(
        self,
        total_score: int,
        round_number: int,
        global_state: dict,
        track_state: dict,
        extra: dict,
    ) -> None:
        """
        FIX 2: Apply round-by-round SDG drag or boost effects to the main
        simulation based on cumulative SDG Impact Score.

        Rules:
          - score < 40 → regulatory_ratchet_active (ESG risk premium on next round OPEX)
          - score 40-70 → neutral (no drag, no boost)
          - score > 70 → sdg_reputational_tailwind (small reputation gain)
          - circular_leader flag → synergy_multiplier preservation
        """
        drag_applied = track_state.get("drag_applied_rounds", [])
        if round_number in drag_applied:
            return  # Already applied this round (idempotency guard)

        active_flags = global_state.setdefault("active_event_flags", {})
        flags_earned = track_state.get("flags_earned", {})

        if total_score < 40 and round_number >= 2:
            # Low SDG performance → activate regulatory ratchet
            active_flags["regulatory_ratchet_active"] = True
            active_flags["sdg_regulatory_ratchet_source"] = f"SDG score {total_score} below 40 threshold at SDG-R{round_number}"
            extra["sdg_regulatory_ratchet_triggered"] = True
            extra["sdg_drag_explanation"] = (
                f"SDG Impact Score ({total_score}/105) below materiality threshold. "
                "Regulatory risk premium applied — OPEX uplift next round."
            )
        elif total_score > 70:
            # Strong SDG performance → reputational tailwind
            current_rep = global_state.get("group_reputation", 50)
            tailwind = 2  # +2 reputation per SDG round when score > 70
            global_state["group_reputation"] = min(100, current_rep + tailwind)
            extra["sdg_reputational_tailwind"] = tailwind
            extra["sdg_boost_explanation"] = (
                f"Strong SDG momentum (score: {total_score}/105) generating "
                f"reputational tailwind: +{tailwind} group reputation."
            )

        # circular_leader: protect synergy from erosion in R7/R8 Circular Economy round
        if flags_earned.get("circular_leader") and round_number >= 3:
            # Lock in a minimum synergy floor
            current_synergy = global_state.get("synergy_multiplier", 1.0)
            synergy_floor = 1.10
            if current_synergy < synergy_floor:
                global_state["synergy_multiplier"] = synergy_floor
                active_flags["circular_synergy_floor_active"] = True
                extra["circular_leader_synergy_protected"] = True

        # sdg_integrity: halve governance_risk growth rate
        if flags_earned.get("sdg_integrity_unlocked"):
            current_gov_risk = global_state.get("governance_risk_score", 20)
            # Soft cap: slow governance risk accumulation for forensic-audit teams
            if current_gov_risk > 40:
                reduction = 3
                global_state["governance_risk_score"] = round(max(0, current_gov_risk - reduction), 2)
                extra["sdg_integrity_governance_risk_reduced"] = reduction

        drag_applied.append(round_number)
        track_state["drag_applied_rounds"] = drag_applied
