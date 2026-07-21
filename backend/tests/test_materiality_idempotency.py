"""Double-Materiality submit is idempotent — no 500, no loop, no double-deduction.

The recurring "double materiality loops twice" bug: a duplicate submit (spurious
matrix remount, network retry, or the CFO "Force Override" re-submit) hit the
BUG-8 idempotency guard, which returned a dict missing the response_model's
required fields → FastAPI ResponseValidationError → generic 500. The frontend
showed that 500 through the CFO override modal, whose override re-submitted →
another 500: a deterministic loop. And the marker lived in a top-level state key
the memory backend drops, so the guard didn't even fire there (double-deduction).

Pins:
  1. First submit succeeds (200) and deducts the allocated budget once.
  2. An IDENTICAL re-submit returns 200 with a schema-valid body (allocated_budget
     + corporate_treasury present) — never a 500.
  3. The re-submit does NOT deduct again (treasury unchanged) and replays the
     same allocated_budget + debrief.
  4. A force-override re-submit after success is also a clean idempotent replay.
"""

import os

os.environ["USE_MEMORY_DB"] = "true"

from fastapi.testclient import TestClient

import database_memory as dbm
from main import app

client = TestClient(app)


def _solo():
    r = client.post(
        "/api/simulations/solo-start",
        json={"player_name": "MAT", "decision_paradigm": "legacy_abc"},
    )
    assert r.status_code in (200, 201), r.text
    return r.json()["session_id"]


def _submit(sid, force=False):
    # A minimal valid placement: two doubly-material issues into Q1.
    payload = {
        "matrix_submission": {
            "quadrant_1_top_right": ["data_privacy_impact", "api_leakage_impact"],
            "quadrant_2_top_left": [],
            "quadrant_3_bottom_right": [],
            "quadrant_4_bottom_left": [],
        },
        "force_override_cfo": force,
    }
    return client.post(f"/api/simulations/{sid}/materiality", json=payload)


def _treasury(sid):
    return dbm._global_states[sid][-1]["corporate_treasury"]


def test_duplicate_submit_replays_cleanly_no_500():
    sid = _solo()
    before = _treasury(sid)

    r1 = _submit(sid)
    assert r1.status_code == 200, r1.text
    body1 = r1.json()
    assert "allocated_budget" in body1 and "corporate_treasury" in body1
    after_first = _treasury(sid)
    assert after_first == before - body1["allocated_budget"]   # deducted once

    # Identical re-submit — the exact loop trigger. Must be 200, never 500.
    r2 = _submit(sid)
    assert r2.status_code == 200, r2.text
    body2 = r2.json()
    assert body2["allocated_budget"] == body1["allocated_budget"]  # replayed
    assert body2["corporate_treasury"] is not None
    assert _treasury(sid) == after_first                        # NOT deducted again


def test_force_override_resubmit_is_idempotent():
    sid = _solo()
    r1 = _submit(sid)
    assert r1.status_code == 200, r1.text
    t_after = _treasury(sid)
    alloc = r1.json()["allocated_budget"]

    # Force-override re-submit (what the CFO memo modal fires) — clean replay.
    r2 = _submit(sid, force=True)
    assert r2.status_code == 200, r2.text
    assert r2.json()["allocated_budget"] == alloc
    assert _treasury(sid) == t_after


def test_response_always_conforms_to_schema():
    # The response_model requires allocated_budget:int and corporate_treasury:float
    # on EVERY path — the guard included. A malformed guard body is what 500'd.
    sid = _solo()
    _submit(sid)
    r = _submit(sid)  # guard path
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body["allocated_budget"], int)
    assert isinstance(body["corporate_treasury"], (int, float))
    assert body["success"] is True
