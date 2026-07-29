"""Extended Horizon Mode (rounds 11-20) must actually activate — and be guarded.

BUG-2026-07-29, found by route audit. POST /api/simulations/{id}/extend had two
independent defects, either of which alone made it useless:

  1. NO AUTHORIZATION. The handler signature took no `request`, so no guard
     could run: not the facilitator cookie, not player ownership. Any
     anonymous caller holding a session id could flip `game_over` off and
     mutate round state on someone else's run.

  2. IT CALLED A FUNCTION THAT DOES NOT EXIST. `db.advance_round(...)` is
     absent from BOTH database.py and database_memory.py, so every call raised
     AttributeError -> HTTP 500. Extended Horizon could never be activated by
     anyone, on either backend, ever.

Defect 2 masked defect 1: the endpoint 500'd before anyone noticed it was also
unguarded. The real mechanism is `insert_next_round`, the parity call
commit_turn already uses.

These tests pin BOTH: the guard, and that activation genuinely reaches round 11.
"""
import os
import pathlib
import tempfile

import pytest


@pytest.fixture(scope="module")
def client():
    d = tempfile.mkdtemp(prefix="exthorizon_")
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


@pytest.fixture
def owned_session(client):
    """A cohort with one joined player. Returns (player_session_id, player_id)."""
    from rate_limit import _rate_buckets, _persistent_bans
    sid = str(client.post("/api/simulations/start",
                          json={"cohort_name": "Ext-" + os.urandom(4).hex(),
                                "facilitator_id": "god_mode"}
                          ).json()["session_id"])
    _rate_buckets.clear()
    _persistent_bans.clear()
    g = client.post(f"/api/admin/{sid}/generate-player").json()
    j = client.post(f"/api/simulations/public/sessions/{sid}/join",
                    json={"player_id": g["player_id"], "password": g["password"]})
    return str(j.json()["session_id"]), g["player_id"]


def _anon(client):
    """A client with no facilitator cookie."""
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app, raise_server_exceptions=False)


def test_advance_round_is_not_a_real_parity_api(client):
    """The root cause, pinned. If someone reintroduces db.advance_round they
    must add it to BOTH backends — this asserts the current truth so the next
    reader is not misled into calling it."""
    import database as db
    import database_memory as dm
    assert not hasattr(dm, "advance_round"), \
        "database_memory grew advance_round — update the extend endpoint and this test"
    assert not hasattr(db, "advance_round") or hasattr(dm, "advance_round"), \
        "advance_round exists in only ONE backend — that is the parity gap this file exists for"


def test_anonymous_caller_cannot_extend(client, owned_session):
    psid, _ = owned_session
    r = _anon(client).post(f"/api/simulations/{psid}/extend", json={})
    assert r.status_code == 403, (
        f"anonymous caller got {r.status_code}; an unauthenticated request must "
        "not be able to clear game_over on someone else's run"
    )


def test_wrong_player_cannot_extend(client, owned_session):
    psid, _ = owned_session
    r = _anon(client).post(f"/api/simulations/{psid}/extend", json={},
                           headers={"X-Player-Id": "MUR-EVIL"})
    assert r.status_code == 403


def test_owner_can_activate_and_reaches_round_11(client, owned_session):
    psid, pid = owned_session
    hdr = {"X-Player-Id": pid}
    r = _anon(client).post(f"/api/simulations/{psid}/extend", json={}, headers=hdr)
    assert r.status_code == 200, f"owner could not activate Extended Horizon: {r.text}"
    body = r.json()
    assert body["extended_horizon_mode"] is True
    assert body["new_round"] == 11
    assert body.get("round_title"), "round 11 config did not resolve"

    dash = client.get(f"/api/simulations/{psid}/dashboard", headers=hdr).json()
    current = dash.get("current_round") or dash.get("round_number")
    assert current == 11, f"dashboard still on round {current} — the round never persisted"


def test_reactivation_is_idempotent(client, owned_session):
    """A double-click must not raise, rewind the run, or violate
    uq_session_round by inserting round 11 twice."""
    psid, pid = owned_session
    hdr = {"X-Player-Id": pid}
    a = _anon(client)
    first = a.post(f"/api/simulations/{psid}/extend", json={}, headers=hdr)
    assert first.status_code == 200, first.text
    second = a.post(f"/api/simulations/{psid}/extend", json={}, headers=hdr)
    assert second.status_code == 200, f"re-activation failed: {second.text}"
    assert second.json()["new_round"] == 11, "re-activation must not rewind or skip"
