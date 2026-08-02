"""
C6/C2 settings-resolution tests (Sim Switchboard remediation).

Covers the two Phase-1 foundation fixes:
  C6 — the climate branch has its own canonical key (`climate_paradigm`) and the
       overloaded `simulation_mode` is never read as a climate value in the
       cohort/session layer.
  C2 — effective settings (global defaults + per-cohort overrides) are seeded
       into a session's active_event_flags, so the engine actually sees them.

These mirror the repo's tripwire style: a wiring invariant plus focused
behaviour checks, all runnable without a live DB or HTTP auth.
"""
import pytest

from admin_shared import (
    _god_mode_settings,
    cohort_settings,
    COHORT_OVERRIDABLE_KEYS,
    get_effective_settings,
    resolve_climate_paradigm,
    seed_effective_flags,
)


# ── C6: wiring tripwire ──────────────────────────────────────────────
def test_climate_paradigm_is_wired_into_both_stores():
    """The canonical key must exist in the global defaults AND be per-cohort
    overridable — otherwise a reader/override path silently loses it."""
    assert _god_mode_settings.get("climate_paradigm") == "standard"
    assert "climate_paradigm" in COHORT_OVERRIDABLE_KEYS


# ── C6: resolver semantics ───────────────────────────────────────────
def test_resolver_prefers_canonical_key():
    assert resolve_climate_paradigm({"climate_paradigm": "advanced_climate"}) == "advanced_climate"


def test_resolver_falls_back_to_legacy_climate_value():
    # Legacy Switchboard payloads only carried simulation_mode.
    assert resolve_climate_paradigm({"simulation_mode": "advanced_climate"}) == "advanced_climate"


def test_resolver_never_reads_scope_as_climate():
    # simulation_mode='single_bu' is a SCOPE value; it must not be interpreted
    # as a climate branch. This is the core C6 collision guard.
    assert resolve_climate_paradigm({"simulation_mode": "single_bu"}) == "standard"


def test_resolver_defaults_to_standard():
    assert resolve_climate_paradigm({}) == "standard"


def test_effective_settings_normalizes_legacy_override():
    sid = "test-c6-normalize"
    cohort_settings[sid] = {"simulation_mode": "advanced_climate"}  # legacy shape
    try:
        eff = get_effective_settings(sid)
        assert eff["climate_paradigm"] == "advanced_climate"
    finally:
        cohort_settings.pop(sid, None)


# ── C2: seeding behaviour ────────────────────────────────────────────
def test_seed_writes_default_fee_when_no_override():
    flags = {}
    seed_effective_flags(None, flags)
    assert flags["global_carbon_fee"] == _god_mode_settings["global_carbon_fee"]
    assert flags["market_hostility_index"] == _god_mode_settings["market_hostility_index"]
    assert flags["scope_3_threshold"] == _god_mode_settings["scope_3_threshold"]


def test_per_cohort_override_reaches_flags_and_is_isolated():
    """A per-cohort carbon-fee override must land in that session's flags (which
    is what the engine reads) and must NOT bleed into other sessions."""
    sid = "test-c2-override"
    baseline = _god_mode_settings["global_carbon_fee"]
    cohort_settings[sid] = {"global_carbon_fee": baseline + 55}
    try:
        overridden = {}
        seed_effective_flags(sid, overridden)
        assert overridden["global_carbon_fee"] == baseline + 55

        neighbour = {}
        seed_effective_flags("some-other-session", neighbour)
        assert neighbour["global_carbon_fee"] == baseline
    finally:
        cohort_settings.pop(sid, None)


def test_seed_does_not_clobber_round_computed_keys():
    """Seeding sets base inputs only; unrelated round-computed keys survive."""
    flags = {"peak_internal_carbon_fee": 123.0, "carbon_fee_per_ton": 40.0}
    seed_effective_flags(None, flags)
    assert flags["peak_internal_carbon_fee"] == 123.0
    assert flags["carbon_fee_per_ton"] == 40.0


def test_seed_is_safe_on_none_flags():
    assert seed_effective_flags(None, None) is None
