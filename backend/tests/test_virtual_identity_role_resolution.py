"""Regression tests for two bug PATTERNS found on 2026-07-19.

Pattern A — virtual-identity role demotion.
    Several endpoints derived the caller's role from the facilitator REGISTRY:
        caller_role = get_role(caller_fac) if caller_fac else "facilitator"
    god_mode and project_admin are VIRTUAL identities with no registry row, so
    they silently resolved to "facilitator". In broadcast_message that flipped
    is_super to False and the ownership filter (`caller_fac and owns_session`,
    caller_fac being None) then selected NOTHING: God Mode's Universal
    Broadcast returned 200 "sent" and delivered to zero cohorts.
    Fix: resolve via get_fac_role(request) + is_admin_role (CLAUDE.md role
    convention 1 — decide on the LEVEL, never on a role string).

Pattern B — silently dropped keys.
    patch_cohort_settings filtered a lead facilitator's body to a role
    allow-list BEFORE computing the rejected-key list, so a disallowed key
    vanished with a 200 and an empty rejection list — a settings toggle that
    lies. Fix: report them as `rejected_for_role`.
"""
import pytest
from fastapi.testclient import TestClient

from main import app

MASTER = {"password": "sim2026@iim"}


def _god():
    c = TestClient(app)
    assert c.post("/api/admin/facilitators/login", json={"facilitator_id": "god_mode", **MASTER}).status_code == 200
    return c


def _fac(god, name, role="facilitator"):
    r = god.post("/api/admin/facilitators", json={"name": name, "email": f"{name.lower()}@x.y", "role": role})
    assert r.status_code == 200, r.text
    fid = r.json()["facilitator_id"]
    c = TestClient(app)
    assert c.post("/api/admin/facilitators/login", json={"facilitator_id": fid, **MASTER}).status_code == 200
    return fid, c


def _cohorts(client, fid, n, prefix):
    return [
        client.post("/api/simulations/start", json={
            "cohort_name": f"{prefix}{i}", "facilitator_id": fid, "decision_paradigm": "legacy_abc",
        }).json()["session_id"]
        for i in range(n)
    ]


# ── Pattern A ───────────────────────────────────────────────────────────────

def test_god_mode_broadcast_reaches_every_cohort():
    """The headline symptom: 200 'sent' to nobody."""
    god = _god()
    fid, owner = _fac(god, "BcastOwner")
    sids = _cohorts(owner, fid, 3, "BC")
    d = god.post("/api/admin/broadcast", json={"title": "All hands", "body": "Round 3 in 2 minutes."}).json()
    assert set(sids).issubset(set(d["delivered_to"])), d["delivered_to"]


def test_broadcast_ownership_scoping_still_holds():
    """The fix must not turn every facilitator into a broadcaster-to-all."""
    god = _god()
    fid_a, cli_a = _fac(god, "BcastA")
    fid_b, cli_b = _fac(god, "BcastB")
    sids_a = _cohorts(cli_a, fid_a, 2, "BA")
    sids_b = _cohorts(cli_b, fid_b, 2, "BB")

    d_a = cli_a.post("/api/admin/broadcast", json={"title": "Mine", "body": "x"}).json()
    assert set(d_a["delivered_to"]) == set(sids_a)
    assert not set(d_a["delivered_to"]) & set(sids_b)


def test_broadcast_explicit_targets_are_still_filtered_for_non_admins():
    god = _god()
    fid_a, cli_a = _fac(god, "BcastTgtA")
    fid_b, cli_b = _fac(god, "BcastTgtB")
    sids_a = _cohorts(cli_a, fid_a, 1, "TA")
    sids_b = _cohorts(cli_b, fid_b, 1, "TB")
    # A aims at B's cohort explicitly → filtered out
    d = cli_a.post("/api/admin/broadcast", json={
        "title": "Cross", "body": "x", "target_sessions": sids_a + sids_b,
    }).json()
    assert set(d["delivered_to"]) == set(sids_a)


def test_cohort_settings_god_mode_is_not_demoted_to_facilitator():
    """god_mode must write ANY overridable key (it used to work only by the
    accident of the lead-only branch not firing)."""
    god = _god()
    fid, cli = _fac(god, "CsGod", role="lead_facilitator")
    sid = _cohorts(cli, fid, 1, "CG")[0]
    r = god.patch(f"/api/admin/sessions/{sid}/cohort-settings", json={"ceo_interview_enabled": True})
    assert r.status_code == 200
    assert r.json()["applied"].get("ceo_interview_enabled") is True
    assert r.json()["rejected_for_role"] == []


# ── Pattern B ───────────────────────────────────────────────────────────────

def test_lead_blocked_keys_are_reported_not_swallowed():
    god = _god()
    fid, cli = _fac(god, "LeadReport", role="lead_facilitator")
    sid = _cohorts(cli, fid, 1, "LR")[0]
    before = cli.get(f"/api/admin/global-settings?session_id={sid}").json()["ceo_interview_enabled"]
    r = cli.patch(f"/api/admin/sessions/{sid}/cohort-settings",
                  json={"ceo_interview_enabled": True, "system_frozen": True})
    j = r.json()
    # allowed key applied…
    assert "system_frozen" in j["applied"]
    # …disallowed key surfaced rather than vanishing
    assert j["rejected_for_role"] == ["ceo_interview_enabled"]
    after = cli.get(f"/api/admin/global-settings?session_id={sid}").json()["ceo_interview_enabled"]
    assert before == after
