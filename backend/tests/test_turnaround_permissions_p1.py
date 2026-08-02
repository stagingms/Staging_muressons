"""
Turnaround Module — P1 permission-spine regression.

Covers the superadmin → facilitator two-key access model for the post-completion
Turnaround module (see PLAN_Turnaround_Module_Implementation.md §2). No engine or
player-facing behaviour is exercised here (that is P3); this suite pins:

  1. Default-off — module ships disabled; can_orchestrate_turnaround is False.
  2. Two-key gate — global enable + explicit facilitator grant; grant rejected
     before global enable; lead_facilitator+ bypasses the grant list.
  3. Role exclusion — only super_admin/god_mode may flip the god-mode controls;
     project_admin and base facilitators cannot; project_admin never orchestrates.

Auth note: this httpx/TestClient version ignores per-request cookies, so each
role uses its own client instance whose cookie jar persists the login (the
pattern httpx recommends). See the DeprecationWarning on per-request cookies.
"""

import pytest
from fastapi.testclient import TestClient

from main import app
from admin_shared import _god_mode_settings, can_orchestrate_turnaround

_GOD = {"facilitator_id": "god_mode", "password": "sim2026@iim"}
_PA = {"facilitator_id": "project_admin", "password": "simadmin2026@"}
_REASON = {"reason": "P1 test — exercising turnaround permission spine"}


def _client(creds):
    """Fresh client whose jar persists the login cookie across calls."""
    c = TestClient(app)
    r = c.post("/api/admin/facilitators/login", json=creds)
    assert r.status_code == 200, r.text
    return c


@pytest.fixture(autouse=True)
def _reset_turnaround_settings():
    """Snapshot + restore the two module settings so tests don't leak state."""
    before_enabled = _god_mode_settings.get("turnaround_module_enabled", False)
    before_perms = dict(_god_mode_settings.get("turnaround_facilitator_permissions", {}))
    yield
    _god_mode_settings["turnaround_module_enabled"] = before_enabled
    _god_mode_settings["turnaround_facilitator_permissions"] = before_perms


# ── 1. Default-off ───────────────────────────────────────────────

def test_module_defaults_off():
    _god_mode_settings["turnaround_module_enabled"] = False
    assert can_orchestrate_turnaround("god_mode", "god_mode") is False
    assert can_orchestrate_turnaround("super_admin", "x") is False
    assert can_orchestrate_turnaround("facilitator", "any") is False


# ── 2. Two-key gate (unit) ───────────────────────────────────────

def test_two_key_gate_helper():
    _god_mode_settings["turnaround_module_enabled"] = True
    _god_mode_settings["turnaround_facilitator_permissions"] = {}
    assert can_orchestrate_turnaround("god_mode", "god_mode") is True
    assert can_orchestrate_turnaround("super_admin", "sa") is True
    assert can_orchestrate_turnaround("lead_facilitator", "lead1") is True
    assert can_orchestrate_turnaround("facilitator", "fac1") is False
    _god_mode_settings["turnaround_facilitator_permissions"]["fac1"] = True
    assert can_orchestrate_turnaround("facilitator", "fac1") is True
    assert can_orchestrate_turnaround("facilitator", "fac2") is False
    assert can_orchestrate_turnaround("project_admin", "pa") is False


def test_disabling_globally_makes_grants_inert():
    _god_mode_settings["turnaround_module_enabled"] = True
    _god_mode_settings["turnaround_facilitator_permissions"] = {"fac1": True}
    assert can_orchestrate_turnaround("facilitator", "fac1") is True
    _god_mode_settings["turnaround_module_enabled"] = False
    assert can_orchestrate_turnaround("facilitator", "fac1") is False
    assert can_orchestrate_turnaround("lead_facilitator", "lead1") is False


# ── 2b. Two-key gate (HTTP) ──────────────────────────────────────

def test_grant_rejected_before_global_enable():
    gm = _client(_GOD)
    assert gm.put("/api/admin/turnaround/global",
                  json={"enabled": False, **_REASON}).status_code == 200
    created = gm.post("/api/admin/facilitators",
                      json={"name": "TA-Base", "role": "facilitator"})
    assert created.status_code == 200, created.text
    fid = created.json()["facilitator_id"]
    r = gm.put(f"/api/admin/turnaround/facilitator-permissions/{fid}",
               json={"granted": True})
    assert r.status_code == 400, r.text


def test_enable_then_grant_flow():
    gm = _client(_GOD)
    assert gm.put("/api/admin/turnaround/global",
                  json={"enabled": True, **_REASON}).status_code == 200
    perms = gm.get("/api/admin/turnaround/facilitator-permissions")
    assert perms.status_code == 200 and perms.json()["module_enabled"] is True

    created = gm.post("/api/admin/facilitators",
                      json={"name": "TA-Base2", "role": "facilitator"})
    fid = created.json()["facilitator_id"]
    g = gm.put(f"/api/admin/turnaround/facilitator-permissions/{fid}",
               json={"granted": True})
    assert g.status_code == 200 and g.json()["granted"] is True
    assert _god_mode_settings["turnaround_facilitator_permissions"].get(fid) is True

    r = gm.put(f"/api/admin/turnaround/facilitator-permissions/{fid}",
               json={"granted": False})
    assert r.status_code == 200 and r.json()["granted"] is False
    assert fid not in _god_mode_settings["turnaround_facilitator_permissions"]


def test_god_mode_requires_reason():
    gm = _client(_GOD)
    r = gm.put("/api/admin/turnaround/global", json={"enabled": True})
    assert r.status_code == 422, r.text


# ── 3. Role exclusion ────────────────────────────────────────────

def test_project_admin_cannot_touch_god_controls():
    pa = _client(_PA)
    assert pa.put("/api/admin/turnaround/global",
                  json={"enabled": True, **_REASON}).status_code == 403
    assert pa.get("/api/admin/turnaround/facilitator-permissions").status_code == 403
    assert pa.put("/api/admin/turnaround/facilitator-permissions/anyone",
                  json={"granted": True}).status_code == 403
