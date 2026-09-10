"""F-01 (audit 2026-09-04) — the first-login password gate, as the cockpit now
uses it.

The server side was already right (F-22): a driver on the issued password may
READ but every write answers 403 {code: password_change_required, message}.
What the cockpit relies on, and what this pins:
  • the 403 carries a human sentence in detail.message (the map, the matrix
    and save-decisions now display it instead of "incomplete data");
  • POST /change-password with the issued password clears the gate WITHOUT
    a re-login — the token minted at player-login keeps working, which is
    what lets the forced modal simply dismiss itself on success;
  • after that, the R1 map, save-decisions and commit all succeed.
"""
import pytest


@pytest.fixture
def client(monkeypatch):
    import master_credentials
    monkeypatch.setattr(master_credentials, "MASTER_PASSWORD", "test-master-pw", raising=False)
    monkeypatch.setattr(master_credentials, "_load_override_hash", lambda: None, raising=False)
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app, raise_server_exceptions=False)


def _clear():
    import rate_limit
    import router as rmod
    rate_limit._rate_buckets.clear()
    rate_limit._persistent_bans.clear()
    getattr(rmod, "_commit_timestamps", {}).clear()


def test_issued_password_blocks_every_write_with_a_message_then_one_change_unblocks_them(client):
    from fastapi.testclient import TestClient
    from main import app
    _clear()
    assert client.post("/api/admin/facilitators/login",
                       json={"facilitator_id": "god_mode", "password": "test-master-pw"}).status_code == 200
    r = client.post("/api/simulations/start", json={"cohort_name": "FirstLoginGate", "facilitator_id": "god_mode"})
    cohort = str(r.json()["session_id"])
    g = client.post(f"/api/admin/{cohort}/generate-player").json()
    pid, issued = g["player_id"], g["password"]

    # what the join screen does: join, then sign in
    player = TestClient(app, raise_server_exceptions=False)
    assert player.post(f"/api/simulations/public/sessions/{cohort}/join",
                       json={"player_id": pid, "password": issued}).status_code == 200
    _clear()
    login = player.post("/api/simulations/player-login", json={"player_id": pid, "password": issued})
    assert login.status_code == 200, login.text
    assert login.json()["must_change_password"] is True, "the cockpit's flag comes from here"
    sid, tok = login.json()["session_id"], login.json()["player_token"]
    H = {"X-Player-Id": pid, "Authorization": f"Bearer {tok}"}

    # reads work (the board must render behind the modal)
    dash = player.get(f"/api/simulations/{sid}/dashboard", headers=H)
    assert dash.status_code == 200

    # every write is refused with the code AND a sentence
    r = player.post(f"/api/simulations/{sid}/stakeholder-map", headers=H, json={"mapping": {}})
    assert r.status_code == 403
    d = r.json()["detail"]
    assert d["code"] == "password_change_required" and "password" in d["message"].lower()
    r = player.post(f"/api/simulations/{sid}/save-decisions", headers=H,
                    json={"allocations": {"pharma": 0.2}, "decision_choice": "option_a"})
    assert r.status_code == 403 and r.json()["detail"]["code"] == "password_change_required"
    _clear()
    bus = [b["bu_id"] for b in dash.json()["business_units"]]
    commit = {"decisions": [{"bu_id": b, "capex_allocated": 1_000_000, "choice_selected": "option_a",
                             "investment_ratio": 0.1} for b in bus],
              "dividends_paid": 0, "expected_round": 1, "force_override_cfo": True}
    r = player.post(f"/api/simulations/{sid}/commit-turn", headers=H, json=commit)
    assert r.status_code == 403 and r.json()["detail"]["code"] == "password_change_required"

    # the modal's request: issued → personal
    r = player.post("/api/simulations/change-password",
                    json={"player_id": pid, "old_password": issued, "new_password": "Personal#2026"})
    assert r.status_code == 200, r.text

    # the SAME token now writes — no re-login, no new session
    r = player.post(f"/api/simulations/{sid}/save-decisions", headers=H,
                    json={"allocations": {"pharma": 0.2}, "decision_choice": "option_a",
                          "expected_round": 1})   # F01: drafts name their round
    assert r.status_code == 200, r.text[:200]
    r = player.post(f"/api/simulations/{sid}/stakeholder-map", headers=H, json={"mapping": {}})
    assert r.status_code == 200, r.text[:200]
    _clear()
    r = player.post(f"/api/simulations/{sid}/commit-turn", headers=H, json=commit)
    assert r.status_code == 201, r.text[:200]
    # and a fresh login no longer raises the flag
    _clear()
    again = player.post("/api/simulations/player-login", json={"player_id": pid, "password": "Personal#2026"})
    assert again.status_code == 200 and again.json()["must_change_password"] is False
    assert again.json()["session_id"] == sid
