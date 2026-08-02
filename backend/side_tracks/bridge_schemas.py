"""
Muressons Global Corporation — Data Bridge Schemas (Layer 3)

Strict Pydantic contracts for state passing between the main simulation
loop and all side track implementations.

Architecture
------------
Main Sim  ──[DataBridgeInput]──►  Side Track  ──[DataBridgeOutput]──►  Main Sim

Rules
-----
- DataBridgeInput  : validated on construction from raw main-sim dicts.
- DataBridgeOutput : every flag key is validated against _ALLOWED_FLAG_PREFIXES.
                     Unrecognised prefixes raise ValueError — no silent failures.
- BridgeKPIDeltas  : Only additive deltas. Side tracks NEVER overwrite KPIs directly;
                     the main engine applies deltas after write-back.
"""

from __future__ import annotations
import copy
import warnings
from typing import Any
from pydantic import BaseModel, Field, field_validator, model_validator


# ── Flag Registry ────────────────────────────────────────────────────────────
# All flag keys emitted by DataBridgeOutput.flags_to_set MUST start with one
# of these prefixes. Mismatches raise ValueError at model-construction time.

_ALLOWED_FLAG_PREFIXES: tuple[str, ...] = (
    "supply_",      # Supply Chain track
    "sc_",          # Supply Chain track (short alias)
    "ethics_",      # Ethics & Sustainability track
    "es_",          # Ethics & Sustainability track (short alias)
    "stakeholder_", # Stakeholder Management track
    "sm_",          # Stakeholder Management track (short alias)
    "reporting_",   # Sustainability Reporting track
    "sr_",          # Sustainability Reporting track (short alias)
    "sdg_",         # Corporate SDG track
    "brsr_",        # BRSR / NGRBC track
    "side_track_",  # Generic side-track system flag (e.g. side_track_completed)
)

# Maximum absolute treasury delta a side track may inject per write-back.
# Prevents a rogue track from zeroing the main treasury.
_MAX_TREASURY_DELTA_ABS: float = 20_000_000.0   # ±$20M


# ── Side Track Decision Schema ───────────────────────────────────────────────
# Typed replacement for the raw `list[dict]` in SideTrackCommitRequest.

class SideTrackDecision(BaseModel):
    """
    Typed schema for a single side-track decision payload.

    Replaces the untyped `list[dict]` in SideTrackCommitRequest.decisions
    (VUL-L3-004). The model validates that choice_selected is present and
    non-empty, while allowing optional metadata fields for audit trails.
    """
    bu_id:            str   = Field(description="Business unit ID this decision applies to.")
    choice_selected:  str   = Field(
        default="",
        description="The canonical option key: 'option_a', 'option_b', or 'option_c'. Empty = no choice.",
    )
    capex_allocated:  float = Field(
        default=0.0, ge=0.0,
        description="Capital expenditure allocated to this BU ($).",
    )
    player_id:        str   = Field(default="", description="Player ID for audit trail.")
    decision_node_id: str   = Field(default="", description="Crisis / decision node ID.")
    pillar_decisions: dict[str, Any] | None = Field(
        default=None,
        description="Pillar-mode decisions (if applicable). None for legacy_abc paradigm.",
    )



# ── KPI Snapshot (main → side track) ─────────────────────────────────────────

class BridgeKPIs(BaseModel):
    """
    Structured KPI snapshot passed INTO a side track at seed time.
    All fields are read-only reference data from the last completed main-sim round.
    """
    avg_carbon_intensity:  float = Field(ge=0.0,    description="Average CI across BUs (tCO₂e / $1M revenue)")
    avg_governance_risk:   float = Field(ge=0.0, le=100.0, description="Average governance risk score across BUs")
    avg_social_license:    float = Field(ge=0.0, le=100.0, description="Average social licence score across BUs")
    total_ncd:             float = Field(ge=0.0,    description="Sum of Natural Capital Debt across all BUs")
    group_synergy:         float = Field(ge=0.0,    description="Current VRIO synergy multiplier")
    tco2e_emissions:       float = Field(ge=0.0,    description="Last-round total group tCO₂e")

    model_config = {"frozen": True}  # Immutable — side tracks must not mutate this


# ── Input Schema: Main → Side Track ─────────────────────────────────────────

class DataBridgeInput(BaseModel):
    """
    DATA BRIDGE (READ): Structured payload seeding a side track's initial state.

    Replaces the raw `dict` return type of BaseSideTrack.seed_from_main_state().
    Constructed from main simulation state at the moment a side track is unlocked.

    Fields
    ------
    treasury     : Main sim corporate treasury ($).
    reputation   : Main sim group reputation score [0, 100].
    active_flags : Snapshot of main sim active_event_flags (read-only reference).
    kpis         : Structured KPI snapshot from main sim.
    extra_state  : Track-specific initial metric values (e.g. supply_visibility,
                   ethical_governance) that are merged into track_data["state"]
                   verbatim by to_seed_dict(). This preserves the full legacy
                   seed dict contract while keeping the typed boundary intact.
    """
    treasury:     float = Field(description="Main sim corporate treasury at seed time ($)")
    reputation:   float = Field(ge=0.0, le=100.0, description="Main sim group reputation score")
    active_flags: dict[str, Any] = Field(
        default_factory=dict,
        description="Snapshot of main sim active_event_flags (read-only reference).",
    )
    kpis: BridgeKPIs = Field(description="Structured KPI snapshot from main sim.")
    extra_state: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Track-specific initial metric values to be stored verbatim in "
            "track_data['state']. Use this for metrics like supply_visibility, "
            "ethical_governance, sdg_impact_score, etc. that the track's "
            "calculate_score() and post_tick() hooks read from the state dict."
        ),
    )

    # ── Convenience accessors ────────────────────────────────────────────────

    def flag(self, key: str, default: Any = None) -> Any:
        """Safe flag lookup — never raises KeyError."""
        return self.active_flags.get(key, default)

    def to_seed_dict(self) -> dict[str, Any]:
        """
        Returns a plain dict suitable for storage in track_data["state"].

        Output merges (in order of increasing priority):
          1. Standard inherited keys (inherited_treasury, inherited_reputation, inherited_kpis)
          2. extra_state — all track-specific initial metric values

        V11 fix: extra_state is deep-copied before merging so mutable values
        (e.g. sdg_score_history=[], accumulated_flags=[]) are independent
        references. This prevents the track state from mutating the original
        DataBridgeInput object and causing cross-round contamination.
        """
        base: dict[str, Any] = {
            "inherited_treasury":   self.treasury,
            "inherited_reputation": self.reputation,
            "inherited_kpis":       self.kpis.model_dump(),
        }
        base.update(copy.deepcopy(self.extra_state))
        return base

    model_config = {"frozen": True}


# ── KPI Deltas (side track → main) ───────────────────────────────────────────

class BridgeKPIDeltas(BaseModel):
    """
    Additive KPI deltas emitted by a side track on write-back.

    Side tracks NEVER overwrite main-sim KPIs directly. The main engine
    applies these deltas to the current state after write-back validation.
    All defaults are zero (no-op).
    """
    treasury_delta:           float = Field(default=0.0, description="Treasury change ($). Negative = cost.")
    reputation_delta:         float = Field(default=0.0, ge=-100.0, le=100.0, description="Reputation points change.")
    carbon_intensity_delta:   float = Field(default=0.0, description="CI delta applied uniformly to all BUs.")
    ncd_delta:                float = Field(default=0.0, description="NCD delta applied uniformly to all BUs.")
    governance_risk_delta:    float = Field(default=0.0, ge=-100.0, le=100.0, description="Governance risk delta.")
    social_license_delta:     float = Field(default=0.0, ge=-100.0, le=100.0, description="Social licence delta.")

    @field_validator("treasury_delta")
    @classmethod
    def treasury_delta_bounded(cls, v: float) -> float:
        if abs(v) > _MAX_TREASURY_DELTA_ABS:
            raise ValueError(
                f"treasury_delta magnitude ${abs(v):,.0f} exceeds the maximum allowed "
                f"per-write-back delta of ${_MAX_TREASURY_DELTA_ABS:,.0f}. "
                "Use multiple rounds or escalation events instead."
            )
        return v


# ── KPI Overrides (side track → main, absolute assignment) ───────────────────

class KPIOverrides(BaseModel):
    """
    Absolute KPI assignments emitted by a side track on write-back.

    Unlike BridgeKPIDeltas (additive), overrides perform a direct SET on the
    main-sim state. They are applied AFTER deltas, so a field present in both
    will reflect the override value in the final state.

    All fields default to None (= no override for that field). Only non-None
    fields are written. This prevents a side track from accidentally zeroing
    out a KPI it didn't intend to touch.

    Contract:
        apply_side_track_results() applies:
          1. kpi_deltas  (addition/subtraction)  FIRST
          2. kpi_overrides (absolute assignment)  SECOND
    """
    corporate_treasury:   float | None = Field(default=None, description="Absolute treasury override ($). None = no override.")
    group_reputation:     float | None = Field(default=None, ge=0.0, le=100.0, description="Absolute reputation override [0,100]. None = no override.")
    avg_carbon_intensity: float | None = Field(default=None, ge=0.0, description="Absolute CI override. None = no override.")
    total_ncd:            float | None = Field(default=None, ge=0.0, description="Absolute NCD override. None = no override.")
    synergy_multiplier:   float | None = Field(default=None, ge=0.0, description="Absolute synergy multiplier override. None = no override.")
    group_social_license: float | None = Field(default=None, ge=0.0, le=100.0, description="Absolute social licence override. None = no override.")

    model_config = {"frozen": True}


# Canonical alias — use KPIDeltas in new code; BridgeKPIDeltas for legacy refs.
KPIDeltas = BridgeKPIDeltas


# ── Output Schema: Side Track → Main ─────────────────────────────────────────

class DataBridgeOutput(BaseModel):
    """
    DATA BRIDGE (WRITE): Structured payload returned by a side track on completion.

    Replaces the raw `dict` return type of BaseSideTrack.write_back_to_main().
    All flag keys are validated against the master flag registry at construction time.
    Unregistered flag prefixes raise ValueError — no silent failures.

    Usage in router.py:
        output: DataBridgeOutput = track.write_back_to_main(track_state, main_global)
        main_flags.update(output.flags_to_set)
        for key in output.flags_to_remove:
            main_flags.pop(key, None)
        # output.kpi_deltas is applied by the engine separately
    """
    flags_to_set:    dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Flags to merge into main_global['active_event_flags']. "
            "All keys MUST match a registered prefix in _ALLOWED_FLAG_PREFIXES."
        ),
    )
    flags_to_remove: list[str] = Field(
        default_factory=list,
        description="Flag keys to delete from active_event_flags on write-back.",
    )
    kpi_deltas: BridgeKPIDeltas = Field(
        default_factory=BridgeKPIDeltas,
        description="Additive KPI deltas applied by apply_side_track_results() FIRST.",
    )
    kpi_overrides: KPIOverrides = Field(
        default_factory=KPIOverrides,
        description=(
            "Absolute KPI assignments applied by apply_side_track_results() SECOND, "
            "after deltas. Only non-None fields are written. These allow a side track "
            "to lock in a precise value (e.g. group_reputation=50.0) regardless of "
            "what deltas computed."
        ),
    )

    # ── Validators ──────────────────────────────────────────────────────────

    @field_validator("flags_to_set")
    @classmethod
    def validate_flag_names(cls, v: dict[str, Any]) -> dict[str, Any]:
        """
        Enforces the master flag registry.
        Every key in flags_to_set must begin with a registered prefix.
        Raises ValueError immediately on the first violation — no silent drops.
        """
        invalid: list[str] = [
            key for key in v
            if not any(key.startswith(p) for p in _ALLOWED_FLAG_PREFIXES)
        ]
        if invalid:
            raise ValueError(
                f"DataBridgeOutput.flags_to_set contains unregistered flag key(s): {invalid}. "
                f"Allowed prefixes: {_ALLOWED_FLAG_PREFIXES}. "
                "Register the prefix in _ALLOWED_FLAG_PREFIXES or rename the flag."
            )
        return v

    @field_validator("flags_to_remove")
    @classmethod
    def validate_removal_names(cls, v: list[str]) -> list[str]:
        """Removal keys must also match the registry — prevents wildcard nuking."""
        invalid = [k for k in v if not any(k.startswith(p) for p in _ALLOWED_FLAG_PREFIXES)]
        if invalid:
            raise ValueError(
                f"flags_to_remove contains unregistered key(s): {invalid}. "
                "Side tracks may only remove flags they own (matching their prefix)."
            )
        return v

    @model_validator(mode="after")
    def no_overlap(self) -> DataBridgeOutput:
        """A flag cannot appear in both flags_to_set and flags_to_remove."""
        overlap = set(self.flags_to_set.keys()) & set(self.flags_to_remove)
        if overlap:
            raise ValueError(
                f"Flag(s) {overlap} appear in both flags_to_set and flags_to_remove. "
                "A write-back cannot simultaneously set and remove the same flag."
            )
        return self

    # ── Convenience factory ──────────────────────────────────────────────────

    @classmethod
    def from_legacy_dict(
        cls,
        flags: dict[str, Any],
        *,
        kpi_deltas: BridgeKPIDeltas | None = None,
        flags_to_remove: list[str] | None = None,
        filter_unregistered: bool = False,
    ) -> DataBridgeOutput:
        """
        **DEPRECATED** — Prefer constructing DataBridgeOutput directly:
            DataBridgeOutput(flags_to_set=flags, kpi_deltas=..., kpi_overrides=...)

        Compatibility shim: wraps a legacy raw-dict write_back return into
        a validated DataBridgeOutput. This still performs full registry
        validation — it is NOT a bypass.

        Parameters
        ----------
        flags              : The raw flag dict to wrap.
        kpi_deltas         : Optional KPI deltas to attach.
        flags_to_remove    : Optional list of flags to remove from main sim.
        filter_unregistered: If True, silently drops flags whose keys do not
                             match any registered prefix rather than raising
                             ValueError. Use this when the source dict contains
                             a mix of internal track flags and main-sim flags
                             (e.g. SDG flags_earned which mixes scoring
                             bookmarks with main-sim write-backs). Dropped
                             keys are not raised as errors — they remain
                             internal to the track's own state.
        """
        warnings.warn(
            "DataBridgeOutput.from_legacy_dict() is deprecated. "
            "Construct DataBridgeOutput directly with flags_to_set=, "
            "kpi_deltas=, and kpi_overrides= arguments.",
            DeprecationWarning,
            stacklevel=2,
        )
        if filter_unregistered:
            flags = {
                k: v for k, v in flags.items()
                if any(k.startswith(p) for p in _ALLOWED_FLAG_PREFIXES)
            }
        return cls(
            flags_to_set=flags,
            flags_to_remove=flags_to_remove or [],
            kpi_deltas=kpi_deltas or BridgeKPIDeltas(),
        )
