"""
SEC-3 regression tests -- get_dashboard and commit-turn must bind the caller to
the session (via the X-Player-Id header, consistent with save_decisions and the
other player routes), so a party holding only the session UUID cannot read or
advance another team's game.

Behaviour contract (matches MED-003-008):
  * Correct X-Player-Id  -> allowed (200 / not blocked by the ownership gate).
  * Wrong X-Player-Id     -> 403 "Player is not the owner of this session."
  * No X-Player-Id        -> allowed (backward-compatible UUID-as-bearer; also how
                            facilitator/observer clients hit these routes).
"""

import asyncio

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

OWNERSHIP_DENIED = "not the owner"

# C2: cohort creation now requires facilitator auth. Log in as the virtual
# god_mode account (registry-independent, unlimited quota, so it never mutates
# the on-disk facilitator registry) and reuse its session cookie for /start.
_GOD_MODE_CREDS = {"facilitator_id": "god_mode", "password": "sim2026@iim"}


def _facilitator_cookies():
    resp = client.post("/api/admin/facilitators/login", json=_GOD_MODE_CREDS)
    assert resp.status_code == 200, f"god_mode login failed: {resp.text}"
    return resp.cookies


def _run(coro):
    """Run a coroutine on a dedicated loop (the global loop may be closed by
    other async tests in the suite)."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _new_player_session():
    """Create a cohort, register one allowed player, join -> (pid, sub_session_id)."""
    import database as db

    cohort = client.post(
        "/api/simulations/start", json={"cohort_name": "SEC3-Test"},
        cookies=_facilitator_cookies(),
    ).json()["session_id"]
    pid = _run(db.generate_player_id(cohort))
    sub = client.post(
        f"/api/simulations/public/sessions/{cohort}/join",
        json={"player_id": pid, "password": "", "player_name": "Owner"},
    ).json()["session_id"]
    return pid, sub


def test_dashboard_correct_owner_allowed():
    pid, sub = _new_player_session()
    r = client.get(f"/api/simulations/{sub}/dashboard", headers={"X-Player-Id": pid})
    assert r.status_code == 200


def test_dashboard_wrong_owner_forbidden():
    pid, sub = _new_player_session()
    r = client.get(f"/api/simulations/{sub}/dashboard", headers={"X-Player-Id": "MUR-EVIL"})
    assert r.status_code == 403
    assert OWNERSHIP_DENIED in r.json().get("detail", "").lower()


def test_dashboard_no_header_backward_compatible():
    pid, sub = _new_player_session()
    r = client.get(f"/api/simulations/{sub}/dashboard")
    assert r.status_code == 200


def test_commit_wrong_owner_forbidden():
    pid, sub = _new_player_session()
    payload = {"dividends_paid": 0, "decisions": []}
    r = client.post(f"/api/simulations/{sub}/commit-turn", json=payload,
                    headers={"X-Player-Id": "MUR-EVIL"})
    assert r.status_code == 403
    assert OWNERSHIP_DENIED in r.json().get("detail", "").lower()


def test_commit_correct_owner_clears_ownership_gate():
    # The real owner must NOT be rejected by the SEC-3 ownership gate. It may hit
    # later validation / rate-limit / round-lock (any status), but never the
    # "not the owner" 403.
    pid, sub = _new_player_session()
    payload = {"dividends_paid": 0, "decisions": []}
    r = client.post(f"/api/simulations/{sub}/commit-turn", json=payload,
                    headers={"X-Player-Id": pid})
    if r.status_code == 403:
        assert OWNERSHIP_DENIED not in r.json().get("detail", "").lower()
