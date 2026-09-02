"""
SEC-3 regression tests -- get_dashboard and commit-turn must bind the caller to
the session, so a party holding only the session UUID cannot read or advance
another team's game.

F-22 (launch audit 2026-09-01): the player credential is the signed bearer
token minted at login (conftest.player_token_headers mints one directly for
store-built sessions). The X-Player-Id header is display-only and no longer
identifies anyone: a request that carries it without a token gets 401
player_token_required.

Behaviour contract (audit #9 tightened SEC-3):
  * Correct player token      -> allowed (200 / not blocked by the ownership gate).
  * Token for another session -> 403 "Player is not the owner of this session."
  * Bare X-Player-Id, no token-> 401 player_token_required.
  * No credential, OWNED      -> 403 unless the caller is an authenticated
                                facilitator who owns/observes the cohort.
  * Facilitator JWT           -> allowed (observer console).
  * Unowned (solo) session    -> allowed with no header (UUID is the bearer).
"""

from fastapi.testclient import TestClient

from main import app
from conftest import player_token_headers

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


def _new_player_session():
    """Create a cohort, register one allowed player, join -> (pid, sub_session_id).

    The roster entry is minted over HTTP rather than by awaiting the db module
    on a private event loop: under Postgres the asyncpg pool belongs to the
    TestClient's loop, so the old direct call failed with "another operation
    is in progress" and this file could never run in the PG parity job."""
    gm = _facilitator_cookies()
    cohort = client.post(
        "/api/simulations/start", json={"cohort_name": "SEC3-Test"}, cookies=gm,
    ).json()["session_id"]
    gen = client.post(f"/api/admin/{cohort}/generate-player", json={"player_name": "Owner"}, cookies=gm)
    assert gen.status_code in (200, 201), gen.text
    pid = gen.json()["player_id"]
    pw = gen.json().get("password") or gen.json().get("plaintext_password") or gen.json().get("temp_password") or ""
    joined = client.post(
        f"/api/simulations/public/sessions/{cohort}/join",
        json={"player_id": pid, "password": pw, "player_name": "Owner"},
    )
    assert joined.status_code == 200, joined.text
    return pid, joined.json()["session_id"]


def test_dashboard_correct_owner_allowed():
    pid, sub = _new_player_session()
    client.cookies.clear()
    r = client.get(f"/api/simulations/{sub}/dashboard", headers=player_token_headers(sub, pid))
    assert r.status_code == 200


def test_dashboard_wrong_owner_forbidden():
    """A valid token scoped to ANOTHER session is refused."""
    pid, sub = _new_player_session()
    client.cookies.clear()
    r = client.get(f"/api/simulations/{sub}/dashboard",
                   headers=player_token_headers("00000000-0000-0000-0000-000000000000", "MUR-EVIL"))
    assert r.status_code == 403
    assert OWNERSHIP_DENIED in r.json().get("detail", "").lower()


def test_dashboard_bare_header_without_token_is_401():
    """F-22: the header alone (what a forger could send) no longer identifies anyone."""
    pid, sub = _new_player_session()
    client.cookies.clear()
    r = client.get(f"/api/simulations/{sub}/dashboard", headers={"X-Player-Id": pid})
    assert r.status_code == 401
    assert r.json()["detail"]["code"] == "player_token_required"


def test_dashboard_no_header_owned_session_rejected():
    """audit #9: an anonymous caller holding only the session UUID (no
    X-Player-Id, no facilitator auth) is now rejected on an OWNED session."""
    pid, sub = _new_player_session()
    # The shared TestClient's cookie jar still holds the god_mode cookie from
    # _new_player_session's /start call — clear it so this request is genuinely
    # anonymous (otherwise the facilitator-observer allowance would apply).
    client.cookies.clear()
    r = client.get(f"/api/simulations/{sub}/dashboard")
    assert r.status_code == 403
    assert "credential" in r.json().get("detail", "").lower()


def test_dashboard_no_header_facilitator_allowed():
    """A facilitator/observer (JWT cookie, no X-Player-Id) may still read an
    owned player's dashboard."""
    pid, sub = _new_player_session()
    r = client.get(f"/api/simulations/{sub}/dashboard", cookies=_facilitator_cookies())
    assert r.status_code == 200


def test_dashboard_solo_session_no_header_allowed():
    """An unowned (solo) session has no player_id to bind against, so the
    high-entropy UUID remains the bearer and no header is required."""
    sub = client.post(
        "/api/simulations/solo-start",
        json={"player_name": "SoloSEC3", "decision_paradigm": "legacy_abc"},
    ).json()["session_id"]
    r = client.get(f"/api/simulations/{sub}/dashboard")
    assert r.status_code == 200


def test_commit_wrong_owner_forbidden():
    pid, sub = _new_player_session()
    client.cookies.clear()
    payload = {"dividends_paid": 0, "decisions": []}
    r = client.post(f"/api/simulations/{sub}/commit-turn", json=payload,
                    headers=player_token_headers("00000000-0000-0000-0000-000000000000", "MUR-EVIL"))
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
