"""
Workstream B tests — unified role-scoped effective-settings read (I3).

Deny-by-default projection: each role sees only its allow-listed keys, every key
carries provenance (global vs cohort_override), and admins see everything.
"""
import pytest

from admin_shared import (
    _god_mode_settings,
    cohort_settings,
    visible_keys_for_role,
    project_effective,
    bu_scope_source,
)


# ── allow-list semantics ─────────────────────────────────────────────
def test_admins_see_all_keys():
    assert visible_keys_for_role("super_admin") is None
    assert visible_keys_for_role("god_mode") is None


def test_lead_sees_climate_and_scaffolding_not_everything():
    keys = visible_keys_for_role("lead_facilitator")
    assert "global_carbon_fee" in keys
    assert "climate_paradigm" in keys
    # A super-admin-only tunable must NOT be visible to a lead.
    assert "overrun_probability" not in keys


def test_facilitator_sees_only_scaffolding_subset():
    keys = visible_keys_for_role("facilitator")
    assert "board_room_moments_enabled" in keys
    assert "global_carbon_fee" not in keys
    assert "assigned_bu" not in keys


def test_project_admin_sees_provisioning_keys():
    keys = visible_keys_for_role("project_admin")
    assert "assigned_bu" in keys
    assert "climate_paradigm" in keys
    assert "global_carbon_fee" not in keys


def test_unknown_role_sees_nothing():
    assert visible_keys_for_role("anonymous") == frozenset()
    assert visible_keys_for_role("player") == frozenset()


# ── projection + provenance ──────────────────────────────────────────
def test_admin_projection_includes_provenance():
    proj = project_effective(None, "super_admin")
    assert proj["role"] == "super_admin"
    fee = proj["settings"]["global_carbon_fee"]
    assert fee["source"] == "global"
    assert fee["overridden"] is False
    assert fee["value"] == _god_mode_settings["global_carbon_fee"]


def test_override_is_flagged_in_provenance():
    sid = "test-b-proj-override"
    cohort_settings[sid] = {"global_carbon_fee": 77}
    try:
        proj = project_effective(sid, "super_admin")
        fee = proj["settings"]["global_carbon_fee"]
        assert fee["value"] == 77
        assert fee["source"] == "cohort_override"
        assert fee["overridden"] is True
        assert proj["overrides_active"] is True
    finally:
        cohort_settings.pop(sid, None)


def test_non_admin_projection_is_deny_by_default():
    # A facilitator projection must never leak a super-admin-only tunable.
    proj = project_effective(None, "facilitator")
    assert "overrun_probability" not in proj["settings"]
    assert "global_carbon_fee" not in proj["settings"]
    # A scaffolding key that IS present in the global defaults is projected.
    assert "foreshadowing_signals_enabled" in proj["settings"]


def test_lead_gets_cohort_settings_view_tab_but_facilitator_does_not():
    # I2 (Workstream C): the read-only effective-settings tab is a lead+ surface.
    from admin_shared import get_allowed_tabs
    lead_tabs = get_allowed_tabs({"facilitator_id": "F1", "role": "lead_facilitator"})
    base_tabs = get_allowed_tabs({"facilitator_id": "F2", "role": "facilitator"})
    assert "cohort_settings_view" in lead_tabs
    assert "cohort_settings_view" not in base_tabs


def test_bu_scope_source_reports_global_when_set():
    snap = _god_mode_settings.get("assigned_bu")
    try:
        _god_mode_settings["assigned_bu"] = "pharma"
        assert bu_scope_source(None) == "switchboard_global"
        _god_mode_settings["assigned_bu"] = ""
        assert bu_scope_source(None) == "none"
    finally:
        _god_mode_settings["assigned_bu"] = snap
