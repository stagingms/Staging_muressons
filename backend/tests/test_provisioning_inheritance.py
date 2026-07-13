"""
Workstream D tests — provisioning inheritance (C1 / C4 / I4) and precedence.

The global default (Sim Switchboard) seeds NEW cohorts for values the provisioning
request omits, while explicit provisioning choices always win, and EXISTING cohorts
are never mutated silently. Precedence: cohort_override > cohort_record > global.
"""
import pytest

from admin_shared import (
    _god_mode_settings,
    cohort_settings,
    get_effective_settings,
    inherited_provisioning_defaults,
)


@pytest.fixture
def restore_globals():
    """Snapshot/restore the mutable global settings so tests don't leak state."""
    snap = dict(_god_mode_settings)
    yield
    _god_mode_settings.clear()
    _god_mode_settings.update(snap)


# ── Explicit values always win ───────────────────────────────────────
def test_explicit_paradigm_is_never_overridden(restore_globals):
    _god_mode_settings["climate_paradigm"] = "advanced_climate"
    dp, sm, iv = inherited_provisioning_defaults(
        decision_paradigm="legacy_abc", simulation_mode="conglomerate", industry_vertical=None
    )
    assert dp == "legacy_abc"          # caller's explicit choice preserved
    assert sm == "conglomerate"


def test_explicit_scope_blocks_bu_inheritance(restore_globals):
    _god_mode_settings["assigned_bu"] = "pharma"
    dp, sm, iv = inherited_provisioning_defaults(
        decision_paradigm="legacy_abc", simulation_mode="conglomerate", industry_vertical=None
    )
    assert sm == "conglomerate"        # explicit scope wins over global single-BU


# ── Inheritance when omitted ─────────────────────────────────────────
def test_inherits_advanced_climate_when_omitted(restore_globals):
    _god_mode_settings["climate_paradigm"] = "advanced_climate"
    dp, sm, iv = inherited_provisioning_defaults(
        decision_paradigm=None, simulation_mode="conglomerate", industry_vertical=None
    )
    assert dp == "advanced_climate"


def test_standard_global_does_not_force_a_paradigm(restore_globals):
    _god_mode_settings["climate_paradigm"] = "standard"
    dp, sm, iv = inherited_provisioning_defaults(
        decision_paradigm=None, simulation_mode="conglomerate", industry_vertical=None
    )
    # 'standard' maps to no specific decision_paradigm — caller keeps its fallback.
    assert dp is None


def test_inherits_single_bu_scope_from_global_assigned_bu(restore_globals):
    _god_mode_settings["assigned_bu"] = "pharma"
    dp, sm, iv = inherited_provisioning_defaults(
        decision_paradigm="legacy_abc", simulation_mode=None, industry_vertical=None
    )
    assert sm == "single_bu"
    assert iv == "pharma"


def test_no_scope_inheritance_when_global_bu_empty(restore_globals):
    _god_mode_settings["assigned_bu"] = ""
    dp, sm, iv = inherited_provisioning_defaults(
        decision_paradigm="legacy_abc", simulation_mode=None, industry_vertical=None
    )
    assert sm is None                  # nothing to inherit -> caller falls back


# ── Precedence: override > cohort_record(≈global here) > global ───────
def test_cohort_override_wins_over_global(restore_globals):
    sid = "test-d-precedence"
    _god_mode_settings["global_carbon_fee"] = 40
    cohort_settings[sid] = {"global_carbon_fee": 88}
    try:
        assert get_effective_settings(sid)["global_carbon_fee"] == 88
        # A different cohort with no override still sees the global default.
        assert get_effective_settings("other")["global_carbon_fee"] == 40
    finally:
        cohort_settings.pop(sid, None)
