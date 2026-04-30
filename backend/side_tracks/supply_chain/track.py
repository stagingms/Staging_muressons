"""
Muressons Global Command — Supply Chain Track Implementation

Concrete implementation of BaseSideTrack for the 7-round
Supply Chain Deep Dive side simulation.

Scoring Dimensions (separate leaderboard):
  - Supply Visibility (0–100)
  - Supplier Risk Score (100→0, lower is better)
  - Scope 3 Reduction (0–100%)
  - Circular Procurement Index (0–100)
  - Digital Maturity (0–100)
  - Geopolitical Resilience (0–100)
"""

from __future__ import annotations
import random
from typing import Any

from side_tracks.base_track import BaseSideTrack
from side_tracks.supply_chain.configs import SUPPLY_CHAIN_ROUND_CONFIGS


class SupplyChainTrack(BaseSideTrack):
    """7-round Supply Chain Deep Dive side simulation."""

    # ── Identity ────────────────────────────────────────────────

    @property
    def track_id(self) -> str:
        return "supply_chain"

    @property
    def display_name(self) -> str:
        return "Supply Chain Deep Dive"

    @property
    def description(self) -> str:
        return (
            "A 7-round deep dive into supply chain management covering "
            "supplier mapping, ethical sourcing, Scope 3 decarbonisation, "
            "circular procurement, digital traceability, geopolitical risk, "
            "and resilience stress testing."
        )

    @property
    def icon(self) -> str:
        return "🔗"

    # ── Structure ───────────────────────────────────────────────

    @property
    def num_rounds(self) -> int:
        return 7

    @property
    def available_window(self) -> tuple[int, int]:
        return (3, 8)  # Can be started after main R3, must complete before R8

    @property
    def scoring_dimensions(self) -> list[dict[str, str]]:
        return [
            {"id": "supply_visibility", "label": "Supply Visibility", "unit": "/100"},
            {"id": "supplier_risk_score", "label": "Supplier Risk Score", "unit": "/100 (lower=better)"},
            {"id": "scope3_reduction", "label": "Scope 3 Reduction", "unit": "%"},
            {"id": "circular_procurement_index", "label": "Circular Procurement", "unit": "/100"},
            {"id": "digital_maturity", "label": "Digital Maturity", "unit": "/100"},
            {"id": "geopolitical_resilience", "label": "Geopolitical Resilience", "unit": "/100"},
            {"id": "consumer_trust_index", "label": "Consumer Trust Index", "unit": "/100"},
        ]

    @property
    def cross_track_prerequisites(self) -> list[str]:
        return []  # Supply Chain has no prerequisites; it enriches Ethics track

    # ── Round Configuration ─────────────────────────────────────

    def get_round_configs(self) -> dict[int, dict[str, Any]]:
        return SUPPLY_CHAIN_ROUND_CONFIGS

    # ── Data Bridges ────────────────────────────────────────────

    def seed_from_main_state(
        self,
        main_global: dict,
        main_bus: list[dict],
        completed_tracks: dict[str, dict],
    ) -> dict:
        """
        DATA BRIDGE (READ): Inherit relevant state from the main simulation
        to contextualise the supply chain track.

        Reads:
          - NCD across BUs → sets inherited baseline
          - Carbon intensity → baseline for Scope 3 work
          - Governance risk → influences supplier risk score
          - Group reputation → inherited for social licence context
          - Main sim flags → check for existing supply chain actions
        """
        n = len(main_bus) or 1

        # Calculate inherited baselines from main sim state
        avg_gov_risk = sum(
            bu.get("governance_risk_score", 20) for bu in main_bus
        ) / n
        total_ncd = sum(
            bu.get("natural_capital_debt", 0) for bu in main_bus
        )
        avg_ci = sum(
            bu.get("carbon_intensity", 0) for bu in main_bus
        ) / n
        inherited_reputation = main_global.get("group_reputation", 50)

        # Check if main sim already did supply chain work
        main_flags = main_global.get("active_event_flags", {})
        has_deep_audit = "deep_audit_completed" in main_flags
        has_blockchain = "blockchain_traceability" in main_flags

        # Seed the track's initial state
        return {
            # ── Track-Specific Metrics (start low, build through rounds) ──
            "supply_visibility": 20 + (10 if has_deep_audit else 0),
            "supplier_risk_score": min(100, max(0, round(avg_gov_risk * 1.5, 1))),
            "scope3_reduction": 0,
            "circular_procurement_index": 5,  # Almost zero baseline
            "digital_maturity": 10 + (15 if has_blockchain else 0),
            "geopolitical_resilience": 15,

            # ── Inherited Context from Main Sim ──
            "inherited_ncd": total_ncd,
            "inherited_carbon_intensity": round(avg_ci, 2),
            "inherited_reputation": inherited_reputation,
            "inherited_treasury": main_global.get("corporate_treasury", 50_000_000),

            # ── Flag Context ──
            "main_sim_deep_audit": has_deep_audit,
            "main_sim_blockchain": has_blockchain,
            "main_sim_flags": list(main_flags.keys()),

            # ── Cross-Track Context ──
            "ethics_track_completed": "ethics_sustainability" in completed_tracks,
        }

    def write_back_to_main(
        self,
        track_state: dict,
        main_global: dict,
    ) -> dict:
        """
        DATA BRIDGE (WRITE): On track completion, write flags into
        the main simulation's active_event_flags.

        These flags:
          1. Appear on the separate Supply Chain leaderboard
          2. Provide narrative continuity to the main sim
          3. Can modulate terminal valuation (secondary to leaderboard score)
        """
        flags: dict[str, Any] = {}
        score = self.calculate_score(track_state)

        flags["supply_chain_track_completed"] = True
        flags["supply_chain_final_score"] = score["total_score"]
        flags["supply_chain_grade"] = score["grade"]
        flags["supply_chain_archetype"] = score["archetype"]["title"]

        # Dimension-specific flags for main sim consumption
        visibility = track_state.get("supply_visibility", 0)
        risk = track_state.get("supplier_risk_score", 50)
        scope3 = track_state.get("scope3_reduction", 0)

        if visibility >= 80:
            flags["supply_chain_resilient"] = True
        elif visibility >= 50:
            flags["supply_chain_adequate"] = True
        else:
            flags["supply_chain_fragile"] = True

        # M_R influence (secondary to separate leaderboard)
        if score["total_score"] >= 80:
            flags["sc_track_mr_bonus"] = 0.10
        elif score["total_score"] >= 60:
            flags["sc_track_mr_bonus"] = 0.05
        elif score["total_score"] < 40:
            flags["sc_track_mr_penalty"] = -0.05

        # Propagate individual flags for cross-track dependencies
        # (Ethics track checks these in its seed_from_main_state)
        flags["sc_cobalt_findings"] = "sc_cobalt_clean" in (
            track_state.get("accumulated_flags", [])
        )
        flags["sc_digital_maturity"] = track_state.get("digital_maturity", 0)

        return flags

    # ── Scoring ─────────────────────────────────────────────────

    def calculate_score(self, track_state: dict) -> dict[str, Any]:
        """
        Calculate the Supply Chain leaderboard score.

        Composite score = weighted average of 7 dimensions:
          - Supply Visibility: 20%
          - Supplier Risk (inverted): 17%
          - Scope 3 Reduction: 17%
          - Circular Procurement: 13%
          - Digital Maturity: 10%
          - Geopolitical Resilience: 10%
          - Consumer Trust Index: 13%  (Tyler-inspired)
        """
        vis = min(100, max(0, track_state.get("supply_visibility", 0)))
        risk_raw = min(100, max(0, track_state.get("supplier_risk_score", 50)))
        risk_inverted = 100 - risk_raw  # Lower risk = higher score
        scope3 = min(100, max(0, track_state.get("scope3_reduction", 0)))
        circular = min(100, max(0, track_state.get("circular_procurement_index", 0)))
        digital = min(100, max(0, track_state.get("digital_maturity", 0)))
        geo = min(100, max(0, track_state.get("geopolitical_resilience", 0)))

        # Consumer Trust Index (Tyler-inspired)
        # Represents how transparent and traceable the chain is from a consumer lens
        # Calculated from: digital maturity × 0.3 + supply visibility × 0.3
        #   + cumulative reputation delta across SC rounds × 0.4
        rep_delta = track_state.get("cumulative_reputation_delta", 0)
        # Normalise rep_delta: range roughly -30 to +30 → 0–100
        rep_component = min(100, max(0, 50 + rep_delta * 1.67))
        consumer_trust = round(
            digital * 0.3 + vis * 0.3 + rep_component * 0.4, 1
        )
        consumer_trust = min(100, max(0, consumer_trust))

        total = round(
            vis * 0.20 +
            risk_inverted * 0.17 +
            scope3 * 0.17 +
            circular * 0.13 +
            digital * 0.10 +
            geo * 0.10 +
            consumer_trust * 0.13
        , 1)

        # Grade
        if total >= 85:
            grade = "A+"
        elif total >= 75:
            grade = "A"
        elif total >= 65:
            grade = "B"
        elif total >= 50:
            grade = "C"
        elif total >= 35:
            grade = "D"
        else:
            grade = "F"

        # Archetype
        if total >= 80:
            archetype = {
                "title": "Resilient Network Architect",
                "description": (
                    "Your supply chain is a strategic asset. Deep visibility, "
                    "ethical sourcing, and geographic diversification have created "
                    "a resilient network that competitors cannot easily replicate."
                ),
                "icon": "🏗️",
                "gradient": "linear-gradient(135deg, #10b981, #059669)",
            }
        elif total >= 60:
            archetype = {
                "title": "Responsible Operator",
                "description": (
                    "A well-managed supply chain with good foundations. Some gaps "
                    "in digital maturity or geographic diversification leave you "
                    "exposed to emerging risks."
                ),
                "icon": "🛡️",
                "gradient": "linear-gradient(135deg, #3b82f6, #2563eb)",
            }
        elif total >= 40:
            archetype = {
                "title": "Reactive Manager",
                "description": (
                    "Your supply chain is functional but fragile. Limited visibility "
                    "and deferred investments mean you're always one disruption away "
                    "from crisis."
                ),
                "icon": "⚠️",
                "gradient": "linear-gradient(135deg, #f59e0b, #d97706)",
            }
        else:
            archetype = {
                "title": "Exposed & Vulnerable",
                "description": (
                    "Your supply chain is a liability. Blind spots, unresolved "
                    "ethical issues, and geographic concentration create compounding "
                    "risks that threaten the entire enterprise."
                ),
                "icon": "🔥",
                "gradient": "linear-gradient(135deg, #ef4444, #b91c1c)",
            }

        return {
            "total_score": total,
            "dimensions": {
                "supply_visibility": vis,
                "supplier_risk_score": risk_raw,
                "scope3_reduction": scope3,
                "circular_procurement_index": circular,
                "digital_maturity": digital,
                "geopolitical_resilience": geo,
                "consumer_trust_index": consumer_trust,
            },
            "grade": grade,
            "archetype": archetype,
            "tyler_insight": {
                "consumer_trust_index": consumer_trust,
                "source": "Olivia Tyler — The Complex Path to Sustainability (TED)",
                "source_url": "https://www.ted.com/talks/olivia_tyler_the_complex_path_to_sustainability",
                "interpretation": (
                    f"Consumer Trust Index: {consumer_trust:.0f}/100 — "
                    f"{'Consumers would confidently buy your products knowing the supply chain is transparent and ethical.' if consumer_trust >= 70 else 'Significant gaps in traceability and transparency would erode consumer confidence if exposed.' if consumer_trust >= 40 else 'Tyler would say your supply chain is a consumer trust liability — opacity breeds distrust.'}"
                ),
            },
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
        Pre-tick hook. Handles:
          - SC-R2: Deep visibility discount on Option A
          - SC-R5: Greenwash penalty on Option A
          - SC-R6: Modern slavery compounding on Option C
          - SC-R7: Stochastic disruption severity calculation
        """
        result: dict[str, Any] = {
            "crisis_severity": crisis_severity,
            "pre_events": {},
        }
        accumulated_flags = set(track_state.get("accumulated_flags", []))
        choice = self._get_primary_choice(decisions)

        if round_number == 2:
            # SC-R2: Deep visibility from SC-R1 reduces Option A cost
            if choice == "option_a" and "sc_deep_visibility" in accumulated_flags:
                result["pre_events"]["sc_r1_visibility_discount"] = True
                result["pre_events"]["sc_r1_visibility_discount_amount"] = 1_000_000
                result["pre_events"]["sc_r1_visibility_discount_message"] = (
                    "📊 Your Tier-4 mapping from SC-R1 provided early intelligence "
                    "on cobalt supply chains — saving $1M in due diligence costs."
                )

        elif round_number == 5:
            # SC-R5: Greenwash data from SC-R1 contaminates blockchain
            if choice == "option_a" and "sc_greenwash_risk" in accumulated_flags:
                result["pre_events"]["sc_greenwash_contamination"] = True
                result["pre_events"]["sc_greenwash_penalty_amount"] = 2_000_000
                result["pre_events"]["sc_greenwash_penalty_message"] = (
                    "⚠️ Your blockchain deployment surfaced systematic inaccuracies "
                    "in self-reported supplier data from SC-R1. Remediation cost: $2M."
                )

        elif round_number == 7:
            # SC-R7: Calculate stochastic disruption severity
            cfg = self.get_round_config(7)
            special = cfg.get("special_rules", {}) if cfg else {}
            base = special.get("base_disruption_severity", 60)
            modifiers = special.get("disruption_modifiers", {})

            # Apply flag-based modifiers
            for flag, delta in modifiers.items():
                if flag in accumulated_flags:
                    base += delta
                    result["pre_events"][f"severity_mod_{flag}"] = delta

            # Clamp severity
            base = max(10, min(100, base))

            # Stochastic roll
            threshold = special.get("stochastic_threshold", 0.65)
            roll = random.random()
            if roll > threshold:
                # Bad luck — severity increases
                base = min(100, round(base * 1.3))
                result["pre_events"]["stochastic_bad_luck"] = True
                result["pre_events"]["stochastic_roll"] = round(roll, 3)
            else:
                result["pre_events"]["stochastic_roll"] = round(roll, 3)

            result["crisis_severity"] = base
            result["pre_events"]["final_disruption_severity"] = base
            result["pre_events"]["disruption_severity_message"] = (
                f"🌪️ Disruption Severity: {base}/100 — "
                f"{'Your investments paid off.' if base < 40 else 'Significant exposure remains.'}"
            )

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
        Post-tick hook. Applies option impacts and handles:
          - SC-R2: Deep visibility cost discount
          - SC-R5: Greenwash penalty application
          - SC-R7: Disruption damage calculation
        """
        # Apply default option impacts first
        extra = self._apply_default_option_impacts(
            round_number, global_state, bu_states, decisions, events, extra_events
        )

        choice = self._get_primary_choice(decisions)

        # ── Tyler: Track cumulative reputation delta for Consumer Trust Index ──
        cfg = self.get_round_config(round_number)
        if cfg:
            option_cfg = cfg.get("options", {}).get(choice, {})
            rep_impact = option_cfg.get("impacts", {}).get("reputation", 0)
            global_state["cumulative_reputation_delta"] = round(
                global_state.get("cumulative_reputation_delta", 0) + rep_impact, 2
            )

        # ── Tyler: Apply Transparency Cascade multiplier (R6, R7) ──
        if round_number >= 6 and global_state.get("transparency_cascade_active"):
            # Amplify supplier_risk_score reductions by 1.3×
            if cfg:
                option_cfg = cfg.get("options", {}).get(choice, {})
                risk_delta = option_cfg.get("impacts", {}).get("supplier_risk_score", 0)
                if risk_delta < 0:  # Only amplify reductions, not increases
                    bonus_risk = round(risk_delta * 0.3, 1)  # Extra 30%
                    global_state["supplier_risk_score"] = round(
                        global_state.get("supplier_risk_score", 50) + bonus_risk, 2
                    )
                    extra["transparency_cascade_risk_bonus"] = bonus_risk
                    extra["transparency_cascade_applied"] = True

        if round_number == 2:
            # Apply SC-R1 visibility discount
            if events.get("sc_r1_visibility_discount") and choice == "option_a":
                discount = events.get("sc_r1_visibility_discount_amount", 1_000_000)
                global_state["corporate_treasury"] = round(
                    global_state["corporate_treasury"] + discount, 2
                )
                extra["sc_r2_discount_applied"] = discount

        elif round_number == 5:
            # Apply greenwash penalty
            if events.get("sc_greenwash_contamination") and choice == "option_a":
                penalty = events.get("sc_greenwash_penalty_amount", 2_000_000)
                global_state["corporate_treasury"] = round(
                    global_state["corporate_treasury"] - penalty, 2
                )
                extra["sc_r5_greenwash_penalty_applied"] = penalty

            # ── Tyler Mechanic: Transparency Cascade ──
            # If supply_visibility ≥ 60 by SC-R5, activate a 1.3× multiplier
            # for all future supplier_risk_score reductions
            track_state = global_state  # Side-track state is stored in global_state
            vis = track_state.get("supply_visibility", 0)
            if vis >= 60:
                extra["transparency_cascade_active"] = True
                extra["transparency_cascade_message"] = (
                    "📊 Tyler Transparency Cascade: Your deep visibility (≥60) "
                    "has created compounding transparency benefits — all future "
                    "supplier risk reductions are amplified by 1.3×."
                )

        elif round_number == 6:
            # Modern slavery compounding: if unresolved + chose Option C
            accumulated_flags = set(previous_flags.get("accumulated_flags", []))
            if choice == "option_c" and "modern_slavery_unresolved" in accumulated_flags:
                # Double the reputation penalty
                additional_rep_penalty = -5  # Extra on top of the -5 in config
                global_state["group_reputation"] = max(
                    0.0, round(global_state.get("group_reputation", 50.0) + additional_rep_penalty, 2)
                )
                extra["sc_r6_modern_slavery_compounding"] = True
                extra["sc_r6_compounding_rep_penalty"] = additional_rep_penalty
                extra["sc_r6_compounding_message"] = (
                    "⚠️ The geopolitical disruption surfaced your unresolved modern "
                    "slavery findings from SC-R2. Media coverage doubled the "
                    "reputational damage."
                )

            # ── Tyler Mechanic: Collaboration Multiplier ──
            # If team invested in BOTH supplier capacity building (SC-R3 Option A)
            # AND circular procurement leader (SC-R4 Option A), their
            # geopolitical_resilience bonus from this round is doubled.
            if ("supplier_capacity_building" in accumulated_flags
                    and "circular_procurement_leader" in accumulated_flags):
                # Double the geo resilience impact for this round
                cfg_r6 = self.get_round_config(6)
                if cfg_r6:
                    option_cfg = cfg_r6.get("options", {}).get(choice, {})
                    base_geo = option_cfg.get("impacts", {}).get("geopolitical_resilience", 0)
                    if base_geo > 0:
                        bonus_geo = base_geo  # Add another 1× (total = 2×)
                        global_state["geopolitical_resilience"] = round(
                            global_state.get("geopolitical_resilience", 0) + bonus_geo, 2
                        )
                        extra["tyler_collaboration_multiplier"] = True
                        extra["tyler_collaboration_geo_bonus"] = bonus_geo
                        extra["tyler_collaboration_message"] = (
                            "🤝 Tyler Collaboration Multiplier: Your deep supplier "
                            "partnerships (capacity building + circular procurement) "
                            "created mutual dependency — suppliers prioritised your "
                            f"orders during the disruption. Resilience +{bonus_geo}."
                        )

        elif round_number == 7:
            # Calculate disruption damage based on severity and choice
            severity = events.get("final_disruption_severity", 60)
            cfg = self.get_round_config(7)
            special = cfg.get("special_rules", {}) if cfg else {}
            max_damage = special.get("max_disruption_damage", 20_000_000)

            # Resilience factor from choice
            resilience_factors = {
                "option_a": 0.80,  # 80% damage reduction
                "option_b": 0.50,  # 50% damage reduction
                "option_c": 0.10,  # 10% damage reduction (insurance only)
            }
            resilience = resilience_factors.get(choice, 0.10)

            # Calculate damage
            base_damage = round(max_damage * (severity / 100), 2)
            actual_damage = round(base_damage * (1 - resilience), 2)

            global_state["corporate_treasury"] = round(
                global_state["corporate_treasury"] - actual_damage, 2
            )

            extra["sc_r7_disruption_base_damage"] = base_damage
            extra["sc_r7_disruption_resilience_factor"] = resilience
            extra["sc_r7_disruption_actual_damage"] = actual_damage
            extra["sc_r7_disruption_avoided"] = round(base_damage - actual_damage, 2)
            extra["sc_r7_damage_message"] = (
                f"🌪️ Disruption Damage: ${actual_damage:,.0f} "
                f"(${round(base_damage - actual_damage, 2):,.0f} avoided "
                f"through resilience investments)."
            )

        return extra
