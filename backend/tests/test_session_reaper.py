"""Audit #10 — idle-session reaper + in-process lock/timestamp GC."""

import asyncio
import os
from datetime import date, timedelta

os.environ["USE_MEMORY_DB"] = "true"

import admin_shared
import database_memory as dm
import router
import session_reaper as sr


def _new_session(cohort="Reaper"):
    res = asyncio.run(dm.create_session(cohort_name=cohort, facilitator_id=None))
    return str(res["session_id"])


def test_dead_session_ancillary_state_is_gced():
    live = _new_session("ReaperLive")
    dead = "DEAD-SESSION-XYZ"
    router._commit_timestamps[dead] = 0.0
    router._commit_timestamps[live] = 1.0
    router._get_commit_lock(dead)
    router._session_players[dead] = [{"player_session_id": "x"}]
    admin_shared._round_pacing[dead] = {"mode": "free"}

    sr.reap_once()

    # Dead session's per-process state is cleaned; the live session is untouched.
    assert dead not in router._commit_timestamps
    assert dead not in router._commit_locks
    assert dead not in router._session_players
    assert dead not in admin_shared._round_pacing
    assert live in router._commit_timestamps


def test_held_lock_is_not_gced():
    """An in-flight commit (held lock) for a non-live id must not be disturbed."""
    async def _run():
        dead = "HELD-SESSION"
        lock = router._get_commit_lock(dead)
        await lock.acquire()
        try:
            sr.reap_once()
            assert dead in router._commit_locks  # skipped because locked
        finally:
            lock.release()
        # Once released, a later pass may GC it.
        sr.reap_once()
        assert dead not in router._commit_locks
    asyncio.run(_run())


def test_expired_solo_session_is_reaped():
    sid = _new_session("SoloExpire")
    dm._sessions[sid]["is_solo"] = True
    dm._sessions[sid]["end_date"] = (date.today() - timedelta(days=1)).isoformat()

    summary = sr.reap_once()

    assert sid not in dm._sessions
    assert summary["sessions_reaped"] >= 1


def test_cohort_session_is_not_reaped():
    """Only solo sessions are reaped; cohort data is preserved for debrief."""
    sid = _new_session("CohortKeep")
    dm._sessions[sid].pop("is_solo", None)  # ensure not solo
    dm._sessions[sid]["end_date"] = (date.today() - timedelta(days=1)).isoformat()

    sr.reap_once()

    assert sid in dm._sessions


def test_active_solo_session_is_kept():
    sid = _new_session("SoloActive")
    dm._sessions[sid]["is_solo"] = True
    dm._sessions[sid]["end_date"] = (date.today() + timedelta(days=1)).isoformat()

    sr.reap_once()

    assert sid in dm._sessions
