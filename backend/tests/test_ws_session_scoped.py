"""F08 residual (AUDIT_Engines_Flow_Classroom50_20260909 F08; EVAL action 8,
"later" part) — the two facilitator-facing WebSockets are scoped like the
REST endpoints.

Before: any signed facilitator token opened /ws/session/{id} for ANY team
(the push channel that carries God-Mode messages, broadcasts, shockwave
countdowns), and every admin socket received every admin push about every
cohort — pacing changes, overrides, black swans, player registrations.

Now: /ws/session/{id} admits a facilitator only if they own, co-facilitate
or administer the session's cohort (4003 otherwise); an admin socket
carries its facilitator, and a push that names a session is delivered only
to the sockets whose facilitator may observe it. A push that names no
session (platform settings) still reaches every admin socket.
"""
from __future__ import annotations

import os
import pathlib
import tempfile

import pytest
from starlette.websockets import WebSocketDisconnect


@pytest.fixture(scope="module")
def client():
    d = tempfile.mkdtemp(prefix="ws_session_scope_")
    os.environ["MURESSONS_DATA_DIR"] = d
    pathlib.Path(d, "memory_snapshot.json").write_text("{}", encoding="utf-8")
    pathlib.Path(d, "facilitators.json").write_text("[]", encoding="utf-8")
    from fastapi.testclient import TestClient
    from main import app
    with TestClient(app) as c:
        yield c


def _god(c):
    c.cookies.clear()
    r = c.post("/api/admin/facilitators/login",
               json={"facilitator_id": "god_mode", "password": os.environ.get("MASTER_PASSWORD", "sim2026@iim")})
    assert r.status_code == 200, r.text
    ck = r.cookies
    c.cookies.clear()
    return ck


def _facilitator(c, god_ck, name):
    from conftest import rotate_facilitator_password
    r = c.post("/api/admin/facilitators", json={"name": name, "role": "facilitator"}, cookies=god_ck)
    assert r.status_code in (200, 201), r.text
    fid, otp = r.json()["facilitator_id"], r.json()["one_time_password"]
    pw = rotate_facilitator_password(c, fid, otp)
    c.cookies.clear()
    ck = c.post("/api/admin/facilitators/login", json={"facilitator_id": fid, "password": pw}).cookies
    c.cookies.clear()
    return fid, ck


def _two_cohorts(c):
    """Owner A with a team and co-facilitator C on cohort A; owner B with cohort B.
    Built per test: conftest clears the session store before every test."""
    god_ck = _god(c)
    fa, ck_a = _facilitator(c, god_ck, "WS Owner A")
    fb, ck_b = _facilitator(c, god_ck, "WS Other B")
    fc, ck_c = _facilitator(c, god_ck, "WS CoFac C")
    r = c.post("/api/simulations/start", json={"cohort_name": "WS-A", "facilitator_id": fa}, cookies=ck_a)
    assert r.status_code in (200, 201), r.text
    cohort_a = r.json()["session_id"]
    r = c.post("/api/simulations/start", json={"cohort_name": "WS-B", "facilitator_id": fb}, cookies=ck_b)
    assert r.status_code in (200, 201), r.text
    cohort_b = r.json()["session_id"]
    g = c.post(f"/api/admin/{cohort_a}/generate-player", json={"player_name": "TeamA"}, cookies=ck_a)
    assert g.status_code in (200, 201), g.text
    pid, pw = g.json()["player_id"], g.json()["password"]
    c.cookies.clear()
    j = c.post(f"/api/simulations/public/sessions/{cohort_a}/join",
               json={"player_id": pid, "password": pw, "player_name": "TeamA"})
    assert j.status_code == 200, j.text
    team_a = j.json()["session_id"]
    r = c.post(f"/api/admin/sessions/{cohort_a}/co-facilitators", json={"facilitator_id": fc}, cookies=ck_a)
    assert r.status_code == 200, r.text
    c.cookies.clear()
    return {"god": god_ck, "a": (fa, ck_a), "b": (fb, ck_b), "cofac": (fc, ck_c),
            "cohort_a": cohort_a, "cohort_b": cohort_b, "team_a": team_a}


def _close_code(c, path, cookies):
    c.cookies.clear()
    try:
        with c.websocket_connect(path, cookies=cookies) as ws:
            ws.close()
        return None                     # accepted
    except WebSocketDisconnect as exc:
        return exc.code
    finally:
        c.cookies.clear()


# ── /ws/session/{id} ─────────────────────────────────────────────────────────

def test_a_facilitator_from_another_cohort_is_refused_the_teams_push_channel(client):
    env = _two_cohorts(client)
    assert _close_code(client, f"/api/admin/ws/session/{env['team_a']}", env["b"][1]) == 4003
    assert _close_code(client, f"/api/admin/ws/session/{env['cohort_a']}", env["b"][1]) == 4003


def test_the_owner_the_cofacilitator_and_the_admin_are_admitted(client):
    env = _two_cohorts(client)
    assert _close_code(client, f"/api/admin/ws/session/{env['team_a']}", env["a"][1]) is None
    assert _close_code(client, f"/api/admin/ws/session/{env['team_a']}", env["cofac"][1]) is None   # via the parent cohort
    assert _close_code(client, f"/api/admin/ws/session/{env['cohort_a']}", env["cofac"][1]) is None
    assert _close_code(client, f"/api/admin/ws/session/{env['team_a']}", env["god"]) is None


def test_no_credential_is_still_4001(client):
    env = _two_cohorts(client)
    assert _close_code(client, f"/api/admin/ws/session/{env['team_a']}", None) == 4001


# ── /ws/admin pushes ─────────────────────────────────────────────────────────

def test_a_push_about_a_cohort_reaches_only_facilitators_who_may_observe_it(client):
    c = client
    env = _two_cohorts(c)
    fa, ck_a = env["a"]; fb, ck_b = env["b"]
    c.cookies.clear()
    with c.websocket_connect("/api/admin/ws/admin", cookies=ck_a) as ws_a, \
         c.websocket_connect("/api/admin/ws/admin", cookies=ck_b) as ws_b, \
         c.websocket_connect("/api/admin/ws/admin", cookies=env["god"]) as ws_god:
        # A toggles cohort A public → a push naming cohort A
        r = c.put(f"/api/admin/{env['cohort_a']}/public-status", json={"is_public": True}, cookies=ck_a)
        assert r.status_code == 200, r.text
        # god changes a platform setting → a push naming no session
        r = c.patch("/api/admin/global-settings", json={"freeze_message": "ws-scope-probe", "reason": "ws scope probe"}, cookies=env["god"])
        assert r.status_code == 200, r.text

        first_a = ws_a.receive_json()
        second_a = ws_a.receive_json()
        first_b = ws_b.receive_json()          # B's FIRST message is the unscoped one: it never saw cohort A's
        first_god = ws_god.receive_json()
        second_god = ws_god.receive_json()
    c.cookies.clear()
    assert first_a["type"] == "session_public_toggled" and first_a["session_id"] == env["cohort_a"]
    assert second_a["type"] == "settings_changed"
    assert first_b["type"] == "settings_changed", first_b
    assert first_god["type"] == "session_public_toggled" and second_god["type"] == "settings_changed"


def test_the_manager_scopes_by_the_session_a_message_names():
    """Unit level: the manager asks its scope predicate per socket, and a
    socket with no identity never receives a session-bound push."""
    import asyncio
    from admin_ws import ConnectionManager

    class _WS:
        def __init__(self): self.sent = []
        async def accept(self): pass
        async def send_text(self, t): self.sent.append(t)

    m = ConnectionManager()
    seen = []
    async def scope(fac, sid):
        seen.append((fac, sid))
        return fac == "FAC-A"
    m.admin_scope = scope
    a, b, anon = _WS(), _WS(), _WS()
    asyncio.run(m.connect_admin(a, facilitator_id="FAC-A"))
    asyncio.run(m.connect_admin(b, facilitator_id="FAC-B"))
    asyncio.run(m.connect_admin(anon))
    asyncio.run(m._deliver_admin_local({"type": "pacing_update", "session_id": "S1"}))
    asyncio.run(m._deliver_admin_local({"type": "player_registered", "player": {"session_id": "S1"}}))
    asyncio.run(m._deliver_admin_local({"type": "engine_failure", "cohort_id": "S1"}))
    asyncio.run(m._deliver_admin_local({"type": "settings_changed"}))
    assert len(a.sent) == 4 and len(b.sent) == 1 and len(anon.sent) == 1
    assert ("FAC-B", "S1") in seen and ("FAC-A", "S1") in seen
    m.disconnect_admin(a)
    assert a not in m.admin_identity
