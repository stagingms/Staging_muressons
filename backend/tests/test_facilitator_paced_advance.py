"""Facilitator-paced advance — commit anytime, advance on timer/manual unlock.

The ask: in a multi-team cohort, a team must be able to COMMIT its round
whenever it is ready (values saved, results shown), while the round ADVANCES
only when the facilitator's timer fires or the facilitator advances it
manually — never gated on "everyone has committed".

Pins:
  1. The commit-turn pacing gate is scoped to the PARENT cohort's pacing (the
     facilitator sets pacing on the cohort; checking the child's own default
     policy silently disabled manual/timed pacing for cohort players).
  2. Under manual pacing: any team commits the unlocked round anytime; the
     NEXT round 403s until the facilitator unlocks it; after unlock it commits.
  3. Under manual/timed pacing the wait-for-all-teams barrier is OFF
     (_cohort_advance_status reports unblocked) and stragglers are NOT
     auto-committed — each team catches up at its own pace.
  4. Free-play cohorts keep the legacy wait-for-all behaviour untouched.
"""

import asyncio
import os

os.environ["USE_MEMORY_DB"] = "true"

from fastapi.testclient import TestClient

import database_memory as dbm
from admin_shared import _get_pacing, _round_pacing
from main import app
from router import _commit_timestamps, _session_players

client = TestClient(app)


def _solo_child_of(parent_id):
    """Create a real session via the API, then graft it under a cohort parent so
    the commit path resolves the parent's pacing (pace_session_id)."""
    sid = client.post(
        "/api/simulations/solo-start",
        json={"player_name": "PACE", "decision_paradigm": "legacy_abc"},
    ).json()["session_id"]
    bus = client.get(f"/api/simulations/{sid}/dashboard").json()["business_units"]
    dbm._sessions[parent_id] = {"parent_cohort_id": None, "player_name": "PACE COHORT",
                                "cohort_name": "PACE COHORT"}
    dbm._sessions[sid]["parent_cohort_id"] = parent_id
    return sid, bus


def _commit(sid, bus, rnd):
    _commit_timestamps[sid] = 0.0
    return client.post(
        f"/api/simulations/{sid}/commit-turn",
        json={
            "decisions": [{
                "bu_id": b["bu_id"], "investment_ratio": 0.5,
                "capex_allocated": 1_000_000, "choice_selected": "option_a",
            } for b in bus],
            "force_override_cfo": True,
            "expected_round": rnd,
        },
    )


def _cleanup(parent_id, sid):
    dbm._sessions.pop(parent_id, None)
    dbm._sessions.pop(sid, None)
    dbm._global_states.pop(sid, None)
    dbm._bu_states.pop(sid, None)
    _round_pacing.pop(parent_id, None)
    _round_pacing.pop(sid, None)
    _session_players.pop(parent_id, None)


def test_manual_pacing_gates_child_commits_via_parent():
    parent = "cohort-pace-manual"
    sid, bus = _solo_child_of(parent)
    pacing = _get_pacing(parent)
    pacing.update({"mode": "manual", "unlocked_round": 1, "set_by": "FAC-TEST"})
    try:
        # Round 1 is unlocked → the team commits whenever it is ready.
        r1 = _commit(sid, bus, 1)
        assert r1.status_code == 201, r1.text
        assert r1.json()["new_round_number"] == 2

        # Round 2 is NOT unlocked → commit is refused (decisions still savable).
        bus2 = r1.json()["business_units"]
        r2 = _commit(sid, bus2, 2)
        assert r2.status_code == 403, r2.text
        assert "locked" in r2.json()["detail"].lower()

        # Facilitator advances the round → the same commit now succeeds.
        pacing["unlocked_round"] = 2
        r3 = _commit(sid, bus2, 2)
        assert r3.status_code == 201, r3.text
        assert r3.json()["new_round_number"] == 3
    finally:
        _cleanup(parent, sid)


def test_timed_pacing_opens_round_when_timer_lapses():
    parent = "cohort-pace-timed"
    sid, bus = _solo_child_of(parent)
    pacing = _get_pacing(parent)
    pacing.update({"mode": "timed", "unlocked_round": 1, "set_by": "FAC-TEST",
                   "next_unlock_at": None})
    try:
        r1 = _commit(sid, bus, 1)
        assert r1.status_code == 201, r1.text
        bus2 = r1.json()["business_units"]

        # Timer not yet fired → round 2 locked.
        pacing["next_unlock_at"] = "2999-01-01T00:00:00+00:00"
        assert _commit(sid, bus2, 2).status_code == 403

        # Facilitator's specified time elapses → round 2 opens automatically
        # (wall-clock evaluation, robust to restarts).
        pacing["next_unlock_at"] = "2020-01-01T00:00:00+00:00"
        r2 = _commit(sid, bus2, 2)
        assert r2.status_code == 201, r2.text
    finally:
        _cleanup(parent, sid)


def test_wait_for_all_barrier_off_under_facilitator_pacing():
    """Manual/timed pacing: unblocked=True even when teams are OUT of sync, and
    no straggler is auto-committed."""
    from router import _cohort_advance_status
    parent = "cohort-pace-nosync"
    a, b = "pace-team-A", "pace-team-B"
    dbm._sessions[parent] = {"parent_cohort_id": None, "player_name": "P"}
    dbm._sessions[a] = {"parent_cohort_id": parent, "player_id": "pa"}
    dbm._sessions[b] = {"parent_cohort_id": parent, "player_id": "pb"}
    # Team A is a round ahead of team B.
    for sid, rn in ((a, 3), (b, 2)):
        dbm._global_states[sid] = [{"round_number": rn, "state_id": f"st-{sid}",
                                    "corporate_treasury": 1.0, "group_reputation": 50,
                                    "synergy_multiplier": 1.0, "cost_of_capital": 0.05}]
    _session_players[parent] = [
        {"player_id": "pa", "player_session_id": a},
        {"player_id": "pb", "player_session_id": b},
    ]
    _get_pacing(parent).update({"mode": "manual", "unlocked_round": 3, "set_by": "FAC-TEST"})
    try:
        adv = asyncio.run(_cohort_advance_status(dbm._sessions[a]))
        assert adv is not None
        assert adv["unblocked"] is True                 # barrier OFF
        # Straggler was NOT auto-committed — team B still at round 2.
        assert dbm._global_states[b][-1]["round_number"] == 2
    finally:
        for sid in (parent, a, b):
            dbm._sessions.pop(sid, None)
            dbm._global_states.pop(sid, None)
        _session_players.pop(parent, None)
        _round_pacing.pop(parent, None)


def test_free_play_keeps_legacy_wait_for_all():
    """Regression: an unconfigured (free) cohort still holds the barrier while
    teams are out of sync and no timeout/force is set."""
    from router import _cohort_advance_status
    parent = "cohort-pace-free"
    a, b = "free-team-A", "free-team-B"
    dbm._sessions[parent] = {"parent_cohort_id": None, "player_name": "P"}
    dbm._sessions[a] = {"parent_cohort_id": parent, "player_id": "pa"}
    dbm._sessions[b] = {"parent_cohort_id": parent, "player_id": "pb"}
    for sid, rn in ((a, 3), (b, 2)):
        dbm._global_states[sid] = [{"round_number": rn, "state_id": f"st-{sid}",
                                    "corporate_treasury": 1.0, "group_reputation": 50,
                                    "synergy_multiplier": 1.0, "cost_of_capital": 0.05}]
    _session_players[parent] = [
        {"player_id": "pa", "player_session_id": a},
        {"player_id": "pb", "player_session_id": b},
    ]
    _round_pacing.pop(parent, None)  # default free pacing, no timeout
    try:
        adv = asyncio.run(_cohort_advance_status(dbm._sessions[a]))
        assert adv is not None
        assert adv["unblocked"] is False               # legacy barrier intact
    finally:
        for sid in (parent, a, b):
            dbm._sessions.pop(sid, None)
            dbm._global_states.pop(sid, None)
        _session_players.pop(parent, None)
        _round_pacing.pop(parent, None)
