"""
CON-1 / CON-2 regression tests for commit-turn serialization.

CON-2 (in-process): a concurrent commit for the same session gets a deterministic
409 while another is in flight (the per-session asyncio lock is held).

CON-1 (cross-process): the commit critical section is additionally wrapped in a
Postgres try-advisory-lock (SEC-5). On contention the helper returns None and the
request must 409; the advisory lock/connection must always be released, including
on validation-error exit paths (no leak). In memory mode the helper is a no-op
sentinel, so classroom/offline runs are unaffected.
"""

import asyncio
import os

os.environ["USE_MEMORY_DB"] = "true"

from fastapi.testclient import TestClient

import router
from main import app
from router import _commit_timestamps, _get_commit_lock

client = TestClient(app)


def _solo():
    sid = client.post(
        "/api/simulations/solo-start",
        json={"player_name": "CON", "decision_paradigm": "legacy_abc"},
    ).json()["session_id"]
    bus = client.get(f"/api/simulations/{sid}/dashboard").json()["business_units"]
    return sid, bus


def _valid_payload(bus, rnd=1):
    return {
        "decisions": [
            {"bu_id": b["bu_id"], "investment_ratio": 0.1,
             "capex_allocated": 100000, "choice_selected": "option_a"}
            for b in bus
        ],
        "dividends_paid": 0, "crisis_severity": 0, "imitation_decay_rate": 0.05,
        "force_override_cfo": True, "expected_round": rnd,
    }


def test_normal_commit_succeeds_through_lock_stack():
    """Regression: the advisory-lock wrapper must not break the happy path."""
    sid, bus = _solo()
    _commit_timestamps[sid] = 0.0
    r = client.post(f"/api/simulations/{sid}/commit-turn", json=_valid_payload(bus))
    assert r.status_code == 201, r.text


def test_in_process_lock_fast_fails_409():
    """CON-2: while the per-session asyncio lock is held, a commit gets a
    deterministic 409 (in-process message, not the cross-process one)."""
    sid, bus = _solo()
    lock = _get_commit_lock(sid)
    loop = asyncio.new_event_loop()
    loop.run_until_complete(lock.acquire())
    try:
        _commit_timestamps[sid] = 0.0
        r = client.post(f"/api/simulations/{sid}/commit-turn", json=_valid_payload(bus))
        assert r.status_code == 409
        detail = r.json().get("detail", "").lower()
        assert "in progress" in detail
        assert "cross-process" not in detail
    finally:
        lock.release()   # asyncio.Lock.release() is synchronous
        loop.close()


def test_advisory_contention_returns_409(monkeypatch):
    """CON-1: when the cross-process advisory lock is already held elsewhere
    (helper returns None), the commit must 409 with the cross-process message."""
    sid, bus = _solo()

    async def _held(_sid):
        return None

    monkeypatch.setattr(router.db, "acquire_advisory_lock", _held)
    _commit_timestamps[sid] = 0.0
    r = client.post(f"/api/simulations/{sid}/commit-turn", json=_valid_payload(bus))
    assert r.status_code == 409
    assert "cross-process" in r.json().get("detail", "").lower()


def test_advisory_lock_released_even_on_validation_error(monkeypatch):
    """CON-1 leak guard: the advisory lock is released on EVERY exit path,
    including when the impl raises a 400 after the lock was acquired."""
    sid, _ = _solo()
    calls = {"acquire": 0, "release": 0}
    _sentinel = object()

    async def _acq(_sid):
        calls["acquire"] += 1
        return _sentinel

    async def _rel(conn, _sid):
        calls["release"] += 1
        assert conn is _sentinel

    monkeypatch.setattr(router.db, "acquire_advisory_lock", _acq)
    monkeypatch.setattr(router.db, "release_advisory_lock", _rel)

    _commit_timestamps[sid] = 0.0
    # Empty decisions -> impl raises 400 AFTER the advisory lock is acquired.
    r = client.post(f"/api/simulations/{sid}/commit-turn",
                    json={"dividends_paid": 0, "decisions": []})
    assert r.status_code == 400
    assert calls["acquire"] == 1
    assert calls["release"] == 1
