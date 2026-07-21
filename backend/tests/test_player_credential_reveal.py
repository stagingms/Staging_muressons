"""Player credential reveal — generated passwords visible until player owns one.

The facilitator's Player Registry rebuilds its credential rows from the
leaderboard roster on every refresh. Pins:

  1. generate-player returns the plaintext once AND the leaderboard's
     registered_players projection carries it as `temp_password` while the
     credential is still the live one (must_change_password) — no more
     "— (reset to reveal)" for a freshly generated id.
  2. The bcrypt hash is never serialized in the roster projection (H-2).
  3. Once the player sets a personal password, the temp credential disappears
     from the roster read entirely.
  4. Admin reset re-arms the reveal with the NEW temp password.
"""

import os

os.environ["USE_MEMORY_DB"] = "true"

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

_GOD = {"facilitator_id": "god_mode", "password": "sim2026@iim"}


def _god_cookies():
    r = client.post("/api/admin/facilitators/login", json=_GOD)
    assert r.status_code == 200, r.text
    return r.cookies


def _make_cohort(gm):
    r = client.post(
        "/api/simulations/solo-start",
        json={"player_name": "CRED COHORT", "decision_paradigm": "legacy_abc"},
    )
    assert r.status_code in (200, 201), r.text
    sid = r.json()["session_id"]
    # solo sessions are top-level; generate-player treats them as a cohort root
    import database_memory as dbm
    dbm._sessions[sid]["is_solo"] = False
    return sid


def _roster_entry(gm, sid, player_id):
    lb = client.get("/api/admin/leaderboard", cookies=gm).json()["leaderboard"]
    entry = next((e for e in lb if e["session_id"] == sid), None)
    assert entry is not None, "cohort missing from leaderboard"
    return next((rp for rp in entry.get("registered_players", [])
                 if rp["player_id"] == player_id), None)


def test_generated_password_is_revealed_on_roster_reads():
    gm = _god_cookies()
    sid = _make_cohort(gm)
    r = client.post(f"/api/admin/{sid}/generate-player", cookies=gm)
    assert r.status_code == 200, r.text
    pid, pw = r.json()["player_id"], r.json()["password"]
    assert pw, "generate must return the plaintext once"

    rp = _roster_entry(gm, sid, pid)
    assert rp is not None, "generated player missing from leaderboard roster"
    assert rp["temp_password"] == pw          # revealed directly — no reset needed
    assert rp["must_change_password"] is True
    assert "password" not in rp               # bcrypt hash never serialized
    assert "plaintext_password" not in rp     # only the sanctioned field


def test_temp_password_disappears_once_player_owns_it():
    gm = _god_cookies()
    sid = _make_cohort(gm)
    r = client.post(f"/api/admin/{sid}/generate-player", cookies=gm)
    pid, pw = r.json()["player_id"], r.json()["password"]

    # Player sets a personal password.
    r2 = client.post(
        "/api/simulations/change-password",
        json={"player_id": pid, "old_password": pw, "new_password": "MyOwnSecret99"},
    )
    assert r2.status_code == 200, r2.text

    rp = _roster_entry(gm, sid, pid)
    assert rp is not None
    assert rp["must_change_password"] is False
    assert rp["temp_password"] == ""          # player owns their password now


def test_admin_reset_rearms_the_reveal():
    gm = _god_cookies()
    sid = _make_cohort(gm)
    r = client.post(f"/api/admin/{sid}/generate-player", cookies=gm)
    pid, pw = r.json()["player_id"], r.json()["password"]
    client.post(
        "/api/simulations/change-password",
        json={"player_id": pid, "old_password": pw, "new_password": "MyOwnSecret99"},
    )

    r3 = client.post(f"/api/admin/players/{pid}/reset-password", cookies=gm)
    assert r3.status_code == 200, r3.text
    new_pw = r3.json()["new_password"]

    rp = _roster_entry(gm, sid, pid)
    assert rp["temp_password"] == new_pw
    assert rp["must_change_password"] is True
