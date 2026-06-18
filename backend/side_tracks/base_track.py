"""
Muressons Global Corporation — Abstract Base Side Track

All side simulation tracks inherit from this class.
Enforces the contract for round configs, data bridges,
and engine hook integration.

Layer 3: Data Bridge and Type Safety — BaseSideTrack now enforces
strict Pydantic types (DataBridgeInput / DataBridgeOutput) on both
bridge method signatures. Any subclass that returns a plain dict
from write_back_to_main() without using DataBridgeOutput.from_legacy_dict()
will raise a Pydantic ValidationError at runtime.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any
import copy

from side_tracks.bridge_schemas import (
    DataBridgeInput,
    DataBridgeOutput,
    BridgeKPIs,
    BridgeKPIDeltas,
    BridgeKPIDeltas as KPIDeltas,   # canonical alias for new code
    KPIOverrides,
)


class BaseSideTrack(ABC):
    """
    Abstract base class for side simulation tracks.

    Architecture:
        - Each track is a self-contained mini-simulation (4–7 rounds).
        - Tracks run SEQUENTIALLY: the main sim pauses while a side track is active.
        - Tracks use the FULL process_tick() engine with all 8 formulas.
        - Data bridges allow bidirectional state flow with the main simulation.

    Data Bridge Contract (Layer 3):
        seed_from_main_state() → DataBridgeInput
            Reads main sim state; returns a strictly-typed seeding payload.
            The router stores DataBridgeInput.to_seed_dict() in track_data["state"].

        write_back_to_main() → DataBridgeOutput
            Returns validated flags and KPI deltas.
            The router merges only DataBridgeOutput.flags_to_set — no blind .update().
            Unregistered flag prefixes raise ValueError at construction time.

    Control hierarchy:
        God Mode → enables/disables tracks globally & per-facilitator
        Facilitator → assigns enabled tracks to cohorts
        Player → plays through assigned tracks sequentially
    """

    # ── Identity ────────────────────────────────────────────────

    @property
    @abstractmethod
    def track_id(self) -> str:
        """Unique identifier: 'supply_chain', 'ethics_sustainability', etc."""

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name for the facilitator/player UI."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Short description of the track's pedagogical focus."""

    @property
    @abstractmethod
    def icon(self) -> str:
        """Emoji icon for UI display."""

    # ── Structure ───────────────────────────────────────────────

    @property
    @abstractmethod
    def num_rounds(self) -> int:
        """Total number of rounds in this side track."""

    @property
    @abstractmethod
    def available_window(self) -> tuple[int, int]:
        """
        Main-sim round range when this track can be started.
        (min_round, max_round) — e.g. (3, 7) means "after R3, before R7".
        """

    @property
    def scoring_dimensions(self) -> list[dict[str, str]]:
        """
        List of scoring metrics for the side track leaderboard.
        Each dict: {"id": "supply_visibility", "label": "Supply Visibility", "unit": "/100"}
        Default: empty (override in subclasses).
        """
        return []

    @property
    def cross_track_prerequisites(self) -> list[str]:
        """
        Track IDs that enrich this track if completed first.
        Default: none.
        """
        return []

    # ── Round Configuration ─────────────────────────────────────

    @abstractmethod
    def get_round_configs(self) -> dict[int, dict[str, Any]]:
        """
        Return the full round configuration dictionary.
        Keys are round numbers (1-indexed), values are config dicts
        matching the same schema as round_configs.py / healthcare_configs.py.
        """

    def get_round_config(self, round_number: int) -> dict[str, Any] | None:
        """Return config for a specific round, or None if invalid."""
        cfg = self.get_round_configs().get(round_number)
        return copy.deepcopy(cfg) if cfg else None

    def get_round_options(self, round_number: int) -> dict[str, Any]:
        """Return just the options dict for a specific round."""
        cfg = self.get_round_configs().get(round_number, {})
        return copy.deepcopy(cfg.get("options", {}))

    # ── Data Bridges (Layer 3: Strictly Typed) ──────────────────

    @abstractmethod
    def seed_from_main_state(
        self,
        main_global: dict,
        main_bus: list[dict],
        completed_tracks: dict[str, dict],
    ) -> DataBridgeInput:
        """
        DATA BRIDGE (READ): Build the typed seed payload for this side track
        by reading relevant fields from the main simulation.

        Implementations MUST return a DataBridgeInput — not a plain dict.
        Use DataBridgeInput.to_seed_dict() in the router to extract the
        storage dict that goes into track_data["state"].

        Args:
            main_global       : Main simulation's current global state dict.
            main_bus          : Main simulation's current BU states list.
            completed_tracks  : {track_id → final track state dict} for any
                                previously completed side tracks (enables
                                cross-track dependency enrichment).

        Returns:
            DataBridgeInput — strictly validated seed payload.
            The router stores DataBridgeInput.to_seed_dict() in session state.
        """

    @abstractmethod
    def write_back_to_main(
        self,
        track_state: dict,
        main_global: dict,
    ) -> DataBridgeOutput:
        """
        DATA BRIDGE (WRITE): When the side track completes, return a
        strictly-typed, registry-validated payload to merge into the
        main simulation.

        All flag keys in DataBridgeOutput.flags_to_set MUST match a registered
        prefix in _ALLOWED_FLAG_PREFIXES (bridge_schemas.py). Unregistered
        keys raise ValueError at DataBridgeOutput construction — NO silent
        state leakage.

        KPI changes MUST be expressed as deltas in DataBridgeOutput.kpi_deltas.
        Side tracks do NOT directly overwrite main-sim KPIs.

        For backwards-compatible migration, use:
            DataBridgeOutput.from_legacy_dict(your_flags_dict)
        This still runs registry validation.

        Args:
            track_state : The final side-track global state dict.
            main_global : Main simulation's current global state (read-only
                          reference for context; do NOT mutate).

        Returns:
            DataBridgeOutput — validated write-back payload.
        """

    @abstractmethod
    def calculate_score(self, track_state: dict) -> dict[str, Any]:
        """
        Calculate the side track's leaderboard score from its final state.

        Returns:
            {
                "total_score": float,  # 0–100 composite
                "dimensions": {        # Individual scoring dimensions
                    "supply_visibility": 85,
                    "supplier_risk": 22,
                    ...
                },
                "grade": "A",          # Letter grade
                "archetype": {         # Narrative archetype
                    "title": "Resilient Network",
                    "description": "...",
                    "icon": "🛡️",
                },
            }
        """

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
        Pre-tick hook for the side track. Runs BEFORE process_tick().
        Can modify crisis_severity, validate inputs, set flags.

        Default implementation: pass through with no modifications.
        Override in subclasses for track-specific logic.

        Returns:
            Same schema as round_logic.pre_tick():
            {"crisis_severity": float, "pre_events": {}, "validation_error": str|None}
        """
        return {
            "crisis_severity": crisis_severity,
            "pre_events": {},
        }

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
        Post-tick hook for the side track. Runs AFTER process_tick().
        Mutates global_state / bu_states in place.
        Returns extra events to merge.

        Default implementation: apply option impacts from config.
        Override in subclasses for track-specific logic.
        """
        return self._apply_default_option_impacts(
            round_number, global_state, bu_states, decisions, events, extra_events
        )

    # ── Helpers ─────────────────────────────────────────────────

    @staticmethod
    def _build_bridge_kpis(main_bus: list[dict], main_global: dict) -> BridgeKPIs:
        """
        Convenience factory: construct a BridgeKPIs snapshot from raw main-sim
        state. Call this inside seed_from_main_state() implementations.
        """
        n = max(len(main_bus), 1)
        return BridgeKPIs(
            avg_carbon_intensity=round(
                sum(bu.get("carbon_intensity", 0) for bu in main_bus) / n, 2
            ),
            avg_governance_risk=round(
                sum(bu.get("governance_risk_score", 20) for bu in main_bus) / n, 2
            ),
            avg_social_license=round(
                sum(bu.get("social_license_score", 50) for bu in main_bus) / n, 2
            ),
            total_ncd=round(
                sum(bu.get("natural_capital_debt", 0) for bu in main_bus), 2
            ),
            group_synergy=float(main_global.get("synergy_multiplier", 1.0)),
            tco2e_emissions=float(main_global.get("tco2e_emissions", 0.0)),
        )

    def _apply_default_option_impacts(
        self,
        round_number: int,
        gs: dict,
        bus: list[dict],
        decisions: list[dict],
        events: dict,
        extra: dict,
    ) -> dict[str, Any]:
        """
        Generic impact applicator for side track options.
        Reads the chosen option from configs and applies treasury,
        reputation, NCD, carbon intensity, and custom metric impacts.
        """
        choice = self._get_primary_choice(decisions)
        opts = self.get_round_options(round_number)
        opt = opts.get(choice, {})
        impacts = opt.get("impacts", {})

        # Treasury
        treasury_cost = impacts.get("treasury", 0)
        if treasury_cost != 0:
            gs["corporate_treasury"] = round(
                gs.get("corporate_treasury", 0) + treasury_cost, 2
            )
            extra[f"st_{self.track_id}_treasury_r{round_number}"] = treasury_cost

        # Reputation
        rep = impacts.get("reputation", 0)
        if rep:
            gs["group_reputation"] = max(
                0.0, min(100.0, round(gs.get("group_reputation", 50.0) + rep, 2))
            )
            extra[f"st_{self.track_id}_rep_r{round_number}"] = rep

        # NCD
        ncd = impacts.get("natural_capital_debt_delta", 0)
        if ncd:
            for bu in bus:
                bu["natural_capital_debt"] = max(
                    0, round(bu.get("natural_capital_debt", 0) + ncd, 2)
                )
            extra[f"st_{self.track_id}_ncd_r{round_number}"] = ncd

        # I2 — Carbon intensity with scope-aware routing
        ci = impacts.get("carbon_intensity_delta", 0)
        ci_routing = opt.get("ci_routing", "uniform")
        if ci:
            try:
                from engine import apply_ci_delta_to_bus
                applied = apply_ci_delta_to_bus(bus, ci, routing=ci_routing)
            except Exception as exc:  # V9: catch ImportError AND any engine-level error
                # Fallback: uniform application; surface failure in events for debugging
                for bu in bus:
                    bu["carbon_intensity"] = max(0, round(bu.get("carbon_intensity", 0) + ci, 2))
                applied = {}
                extra[f"st_{self.track_id}_ci_fallback_r{round_number}"] = str(exc)[:120]
            extra[f"st_{self.track_id}_ci_r{round_number}"] = ci
            if ci_routing == "scope3_weighted":
                extra[f"st_{self.track_id}_ci_by_bu_r{round_number}"] = applied

        # Governance risk
        gov = impacts.get("governance_risk_delta", 0)
        if gov:
            for bu in bus:
                bu["governance_risk_score"] = max(
                    0.0, min(100.0, round(bu.get("governance_risk_score", 20.0) + gov, 2))
                )
            extra[f"st_{self.track_id}_gov_r{round_number}"] = gov

        # Social licence
        sl = impacts.get("social_license_delta", 0)
        if sl:
            for bu in bus:
                bu["social_license_score"] = max(
                    0.0, min(100.0, round(bu.get("social_license_score", 50.0) + sl, 2))
                )
            extra[f"st_{self.track_id}_sl_r{round_number}"] = sl

        # Track-specific custom metrics → stored in track state
        # ST-002: Validate custom keys don't collide with reserved main-sim prefixes
        _RESERVED_PREFIXES = (
            "terminal_", "mr_", "strike_", "climate_", "pathway_",
            "insolvency_", "greenwashing_", "dividend_", "capex_",
        )
        for key, val in impacts.items():
            if key not in (
                "treasury", "reputation", "natural_capital_debt_delta",
                "carbon_intensity_delta", "governance_risk_delta",
                "social_license_delta",
            ):
                prefixed_key = f"st_{self.track_id}_custom_{key}"
                # Guard: warn if a custom key accidentally shadows a main-sim key
                if any(key.startswith(p) for p in _RESERVED_PREFIXES):
                    extra[f"st_{self.track_id}_collision_warning_{key}"] = True
                extra[prefixed_key] = val

        extra[f"st_{self.track_id}_choice_r{round_number}"] = choice
        return extra

    @staticmethod
    def _get_primary_choice(decisions: list[dict]) -> str:
        """Extract the primary option choice from decisions.

        VUL-002 FIX: Returns a (choice, defaulted) tuple is not viable here
        without breaking all callers. Instead: emit a sentinel constant that
        router.py and post_tick hooks can detect via the module attribute
        LAST_CHOICE_DEFAULTED (set per-call — NOT thread-safe for concurrent
        sessions; router must use result not this side-channel).

        Correct fix: the router now emits a 'choice_defaulted' warning event
        so facilitators can see that no decision was submitted.
        """
        for dec in decisions:
            if dec.get("choice_selected"):
                return dec["choice_selected"]
        return "option_b"  # FIX-004: Harmonized default. Router emits warning event.
