"""
Multiplayer commit-indicator (MP-01) regression tests.

The cockpit renders an "X/Y teams committed" badge from
globalState.team_commits_this_round / cohort_team_count. These must survive the
full round-trip -- commit (MP-01 compute) -> persist -> fetch -> GlobalStateOut
response model -- for cohort sub-sessions, and stay absent for solo sessions so
the badge (gated on cohort_team_count > 0) stays hidden.
"""

import asyncio
import os

os.environ["USE_MEMORY_DB"] = "true"

from fastapi.testclient import TestClient

from main import app
import database as db
from router import _commit_timestamps

client = TestClient(app)

# C2: /start now requires facilitator auth. god_mode is registry-independent and
# has unlimited quota, so it never mutates the on-disk facilitator registry.
_GOD_MODE_CREDS = {"facilitator_id": "god_mode", "password": "sim2026@iim"}


def _facilitator_cookies():
    resp = client.post("/api/admin/facilitators/login", json=_GOD_MODE_CREDS)
    assert resp.status_code == 200, f"god_mode login failed: {resp.text}"
    return resp.cookies


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _commit(pid, sub, rnd):
    bus = client.get(f"/api/simulations/{sub}/dashboard",
                     headers={"X-Player-Id": pid}).json()["business_units"]
    _commit_timestamps[sub] = 0.0
    return client.post(
        f"/api/simulations/{sub}/commit-turn",
        json={"decisions": [{"bu_id": b["bu_id"], "investment_ratio": 0.15,
                             "capex_allocated": 400000, "choice_selected": "option_b"} for b in bus],
              "dividends_paid": 0, "crisis_severity": 0, "imitation_decay_rate": 0.05,
              "force_override_cfo": True, "expected_round": rnd},
        headers={"X-Player-Id": pid},
    )


def _badge(pid, sub):
    gs = client.get(f"/api/simulations/{sub}/dashboard",
                    headers={"X-Player-Id": pid}).json()["global_state"]
    return gs.get("team_commits_this_round"), gs.get("cohort_team_count")


def test_indicator_populated_and_increments_for_cohort():
    cid = client.post("/api/simulations/start",
                      json={"cohort_name": "MP-Ind", "decision_paradigm": "legacy_abc"},
                      cookies=_facilitator_cookies()).json()["session_id"]
    players = []
    for i in range(3):
        pid = _run(db.generate_player_id(cid))
        sub = client.post(f"/api/simulations/public/sessions/{cid}/join",
                          json={"player_id": pid, "password": "", "player_name": f"T{i}"}).json()["session_id"]
        players.append((pid, sub))

    # As each team commits round 1, its badge reflects the tally at commit time.
    assert _commit(*players[0], 1).status_code == 201
    assert _badge(*players[0]) == (1, 3)
    assert _commit(*players[1], 1).status_code == 201
    assert _badge(*players[1]) == (2, 3)
    assert _commit(*players[2], 1).status_code == 201
    assert _badge(*players[2]) == (3, 3)


def test_indicator_hidden_for_solo():
    sid = client.post("/api/simulations/solo-start",
                      json={"player_name": "Solo", "decision_paradigm": "legacy_abc"}).json()["session_id"]
    bus = client.get(f"/api/simulations/{sid}/dashboard").json()["business_units"]
    _commit_timestamps[sid] = 0.0
    client.post(f"/api/simulations/{sid}/commit-turn",
                json={"decisions": [{"bu_id": b["bu_id"], "investment_ratio": 0.1,
                                     "capex_allocated": 100000, "choice_selected": "option_a"} for b in bus],
                      "dividends_paid": 0, "crisis_severity": 0, "imitation_decay_rate": 0.05,
                      "force_override_cfo": True, "expected_round": 1})
    gs = client.get(f"/api/simulations/{sid}/dashboard").json()["global_state"]
    # Solo: never set -> None -> frontend gate (cohort_team_count > 0) hides the badge.
    assert gs.get("cohort_team_count") in (None, 0)


def test_indicator_live_refresh_across_teams():
    """The badge updates on a team's dashboard as OTHER teams commit, without
    that team re-committing, and resets when the cohort advances a round."""
    cid = client.post("/api/simulations/start",
                      json={"cohort_name": "MP-Live", "decision_paradigm": "legacy_abc"},
                      cookies=_facilitator_cookies()).json()["session_id"]
    players = []
    for i in range(3):
        pid = _run(db.generate_player_id(cid))
        sub = client.post(f"/api/simulations/public/sessions/{cid}/join",
                          json={"player_id": pid, "password": "", "player_name": f"T{i}"}).json()["session_id"]
        players.append((pid, sub))

    _commit(*players[0], 1)
    assert _badge(*players[0]) == (1, 3)          # T0's own view

    # T1 commits -> T0's view must update LIVE (no re-commit by T0).
    _commit(*players[1], 1)
    assert _badge(*players[0]) == (2, 3)          # live cross-team refresh
    assert _badge(*players[2]) == (2, 3)          # even a team that hasn't committed sees the shared tally

    _commit(*players[2], 1)
    assert _badge(*players[0]) == (3, 3)
    assert _badge(*players[1]) == (3, 3)

    # First team advances to round 2 -> the badge resets for the new round.
    _commit(*players[0], 2)
    assert _badge(*players[1]) == (1, 3)
