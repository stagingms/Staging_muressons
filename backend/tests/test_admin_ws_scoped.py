"""F08 (AUDIT_Engines_Flow_Classroom50_20260909, P2) — the admin WebSocket
never answers "refresh" with data.

A facilitator authenticated by cookie who opened /api/admin/ws/admin WITHOUT
the ?facilitator_id= query the UI normally sends fell into a branch that
answered "refresh" with db.fetch_all_sessions() — every cohort on the
instance, with its session metadata merged in (rosters, password fields),
under none of the REST ownership guards. The socket now answers only with
the refresh trigger; the frontend fetches its own, scoped, leaderboard over
REST as it always did.
"""
from __future__ import annotations

import os
import pathlib
import tempfile

import pytest


@pytest.fixture(scope="module")
def client():
    d = tempfile.mkdtemp(prefix="ws_scope_")
    os.environ["MURESSONS_DATA_DIR"] = d
    pathlib.Path(d, "memory_snapshot.json").write_text("{}", encoding="utf-8")
    pathlib.Path(d, "facilitators.json").write_text("[]", encoding="utf-8")
    from fastapi.testclient import TestClient
    from main import app
    with TestClient(app) as c:
        r = c.post("/api/admin/facilitators/login",
                   json={"facilitator_id": "god_mode", "password": "sim2026@iim"})
        assert r.status_code == 200, r.text
        yield c


def test_cookie_only_admin_socket_gets_a_trigger_not_the_session_list(client):
    # a cohort exists, so a leaky answer would have something to leak
    r = client.post("/api/simulations/start", json={"cohort_name": "WS-Scope", "facilitator_id": "god_mode"})
    assert r.status_code in (200, 201), r.text
    # the login above set the mur_session cookie on the client; open the
    # socket with NO query parameter — the branch the audit exercised
    with client.websocket_connect("/api/admin/ws/admin") as ws:
        ws.send_text("refresh")
        msg = ws.receive_json()
    assert msg == {"type": "sessions_refresh_trigger"}
    assert "sessions" not in msg


def test_admin_socket_with_the_ui_query_behaves_the_same(client):
    with client.websocket_connect("/api/admin/ws/admin?facilitator_id=god_mode") as ws:
        ws.send_text("refresh")
        msg = ws.receive_json()
    assert msg == {"type": "sessions_refresh_trigger"}


def test_no_all_sessions_reply_remains_in_the_socket_handler():
    src = (pathlib.Path(__file__).resolve().parents[1] / "admin_router.py").read_text(encoding="utf-8")
    start = src.index('@admin_router.websocket("/ws/admin")')
    end = src.index('@admin_router.websocket("/ws/session/{session_id}")')
    code = "\n".join(l for l in src[start:end].splitlines() if not l.strip().startswith("#"))
    assert "await db.fetch_all_sessions()" not in code
    assert '"sessions_refresh"' not in code
