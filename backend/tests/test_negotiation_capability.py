"""Per-facilitator capability gate for Stakeholder Negotiation Rooms.

Contract (updated 2026-09-01, EVAL_Stakeholder_SLO rec 2): the capability is
DEFAULT-GRANTED — rooms are part of the standard experience — and explicitly
REVOCABLE: a super admin can store False on the registry record, after which
the lead may not enable the cohort flag and — critically — rooms stop on
already-enabled LIVE cohorts, not merely future ones.
"""
import pytest
from fastapi.testclient import TestClient

from main import app
import database_memory as dm
from autonomous_agents import create_initial_agent_state

MASTER = {"password": "sim2026@iim"}


def _god():
    c = TestClient(app)
    assert c.post("/api/admin/facilitators/login", json={"facilitator_id": "god_mode", **MASTER}).status_code == 200
    return c


def _make_lead(god, name, granted):
    body = {"name": name, "email": f"{name.lower()}@x.y", "role": "lead_facilitator"}
    if granted:
        body["negotiation_rooms_enabled"] = True
    r = god.post("/api/admin/facilitators", json=body)
    assert r.status_code == 200, r.text
    return r.json()


def _session_for(fid, name):
    c = TestClient(app)
    assert c.post("/api/admin/facilitators/login", json={"facilitator_id": fid, **MASTER}).status_code == 200
    sid = c.post("/api/simulations/start", json={
        "cohort_name": name, "facilitator_id": fid, "decision_paradigm": "legacy_abc",
    }).json()["session_id"]
    return c, sid


def _make_hostile(sid):
    row = dm._global_states[sid][-1]
    aa = row.get("autonomous_agents") or create_initial_agent_state()
    aa["agents"]["the_regulator"]["escalation_stage"] = "hostile"
    aa["agents"]["the_regulator"]["tolerance"] = 14.0
    row["autonomous_agents"] = aa


def test_capability_defaults_granted_and_is_revocable():
    god = _god()
    # absent on create → granted (the platform default since 2026-09-01)
    assert _make_lead(god, "CapOffA", granted=False)["negotiation_rooms_enabled"] is True
    assert _make_lead(god, "CapOnA", granted=True)["negotiation_rooms_enabled"] is True
    # explicit revoke sticks
    fid = _make_lead(god, "CapRevokable", granted=False)["facilitator_id"]
    assert god.put(f"/api/admin/facilitators/{fid}", json={"negotiation_rooms_enabled": False}).status_code == 200
    from admin_shared import facilitator_negotiation_granted
    rec = next(f for f in dm.__dict__.get("_facilitator_registry", []) if f["facilitator_id"] == fid) \
        if hasattr(dm, "_facilitator_registry") else None
    if rec is None:
        from admin_shared import _facilitator_registry
        rec = next(f for f in _facilitator_registry if f["facilitator_id"] == fid)
    assert facilitator_negotiation_granted(rec) is False


def test_login_response_carries_the_capability():
    god = _god()
    fid = _make_lead(god, "CapLogin", granted=True)["facilitator_id"]
    c = TestClient(app)
    r = c.post("/api/admin/facilitators/login", json={"facilitator_id": fid, **MASTER})
    assert r.json()["negotiation_rooms_enabled"] is True


def test_revoked_lead_is_refused_with_an_explanation():
    god = _god()
    fid = _make_lead(god, "CapDeny", granted=False)["facilitator_id"]
    assert god.put(f"/api/admin/facilitators/{fid}", json={"negotiation_rooms_enabled": False}).status_code == 200
    c, sid = _session_for(fid, "DenyCohort")
    r = c.patch(f"/api/admin/sessions/{sid}/cohort-settings", json={"negotiation_rooms_enabled": True})
    assert r.status_code == 403
    assert "not enabled for your facilitator profile" in r.json()["detail"]
    # …and no cohort override was written (effective still shows the platform
    # default, which is True since 2026-09-01 — assert the store directly)
    from admin_shared import cohort_settings
    assert "negotiation_rooms_enabled" not in (cohort_settings.get(sid) or {})


def test_granted_lead_can_enable_own_cohort():
    god = _god()
    fid = _make_lead(god, "CapAllow", granted=True)["facilitator_id"]
    c, sid = _session_for(fid, "AllowCohort")
    assert c.patch(f"/api/admin/sessions/{sid}/cohort-settings", json={"negotiation_rooms_enabled": True}).status_code == 200
    assert c.get(f"/api/admin/global-settings?session_id={sid}").json()["negotiation_rooms_enabled"] is True


def test_god_mode_bypasses_the_capability():
    """god_mode is a VIRTUAL identity absent from the registry — the gate must
    resolve its role from the signed token (is_admin_role), not the record."""
    god = _god()
    fid = _make_lead(god, "CapAdminBypass", granted=False)["facilitator_id"]
    _, sid = _session_for(fid, "BypassCohort")
    assert god.patch(f"/api/admin/sessions/{sid}/cohort-settings", json={"negotiation_rooms_enabled": True}).status_code == 200


def test_player_calls_blocked_when_owner_capability_revoked():
    god = _god()
    fid = _make_lead(god, "CapPlayerBlock", granted=False)["facilitator_id"]
    assert god.put(f"/api/admin/facilitators/{fid}", json={"negotiation_rooms_enabled": False}).status_code == 200
    _, sid = _session_for(fid, "PlayerBlockCohort")
    # cohort flag is on (platform default), but the owner's grant is revoked
    _make_hostile(sid)
    r = TestClient(app).post(f"/api/simulations/{sid}/negotiation/open", json={"agent_id": "the_regulator"})
    assert r.status_code == 403


def test_revoking_capability_stops_a_live_cohort():
    god = _god()
    fac = _make_lead(god, "CapRevoke", granted=True)
    fid = fac["facilitator_id"]
    c, sid = _session_for(fid, "RevokeCohort")
    assert c.patch(f"/api/admin/sessions/{sid}/cohort-settings", json={"negotiation_rooms_enabled": True}).status_code == 200
    _make_hostile(sid)
    player = TestClient(app)
    assert player.post(f"/api/simulations/{sid}/negotiation/open", json={"agent_id": "the_regulator"}).status_code == 200
    # super admin revokes mid-game → the open room stops taking calls at once
    assert god.put(f"/api/admin/facilitators/{fid}", json={"negotiation_rooms_enabled": False}).status_code == 200
    assert player.post(f"/api/simulations/{sid}/negotiation/say", json={"text": "hello"}).status_code == 403
