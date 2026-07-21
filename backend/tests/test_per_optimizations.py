"""
PER-1 / PER-2 regression tests.

PER-1: GET /dashboard accepts an optional ?since_round=N to bound the history
payload; the default (no param) returns the full history unchanged.

PER-2: db.fetch_latest_round returns just the latest round number cheaply and is
used for the per-sibling commit-count fan-out (behaviour preserved).
"""

import asyncio
import os

os.environ["USE_MEMORY_DB"] = "true"

from fastapi.testclient import TestClient

from main import app
from router import _commit_timestamps

client = TestClient(app)


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _solo_with_history(rounds=3):
    sid = client.post(
        "/api/simulations/solo-start",
        json={"player_name": "PER", "decision_paradigm": "legacy_abc"},
    ).json()["session_id"]
    for r in range(1, rounds):
        bus = client.get(f"/api/simulations/{sid}/dashboard").json()["business_units"]
        payload = {
            "decisions": [
                {"bu_id": b["bu_id"], "investment_ratio": 0.1,
                 "capex_allocated": 100000, "choice_selected": "option_a"}
                for b in bus
            ],
            "dividends_paid": 0, "crisis_severity": 0, "imitation_decay_rate": 0.05,
            "force_override_cfo": True, "expected_round": r,
        }
        _commit_timestamps[sid] = 0.0
        assert client.post(f"/api/simulations/{sid}/commit-turn", json=payload).status_code == 201
    return sid


def test_dashboard_full_history_by_default():
    sid = _solo_with_history(rounds=3)
    data = client.get(f"/api/simulations/{sid}/dashboard").json()
    rounds = [h["round_number"] for h in data["history"]]
    assert len(rounds) >= 2  # rounds 1 and 2 are now historical


def test_dashboard_since_round_trims_history():
    sid = _solo_with_history(rounds=3)
    full = client.get(f"/api/simulations/{sid}/dashboard").json()["history"]
    full_rounds = sorted(h["round_number"] for h in full)
    cutoff = full_rounds[-1]  # keep only the most recent historical round

    trimmed = client.get(
        f"/api/simulations/{sid}/dashboard", params={"since_round": cutoff}
    ).json()["history"]
    trimmed_rounds = [h["round_number"] for h in trimmed]

    assert trimmed_rounds, "expected at least one round at/after the cutoff"
    assert all(r >= cutoff for r in trimmed_rounds)
    assert len(trimmed) < len(full)  # actually smaller than the full payload


def test_fetch_latest_round_helper():
    import database as db
    sid = _solo_with_history(rounds=3)  # committed up to round 3
    assert _run(db.fetch_latest_round(sid)) == 3
    assert _run(db.fetch_latest_round("does-not-exist")) is None
