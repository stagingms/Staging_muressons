"""Double-Materiality submit is idempotent — no 500, no loop, no double-deduction.

The recurring "double materiality loops twice" bug: a duplicate submit (spurious
matrix remount, network retry, or the CFO "Force Override" re-submit) hit the
BUG-8 idempotency guard, which returned a dict missing the response_model's
required fields → FastAPI ResponseValidationError → generic 500. The frontend
showed that 500 through the CFO override modal, whose override re-submitted →
another 500: a deterministic loop. And the marker lived in a top-level state key
the memory backend drops, so the guard didn't even fire there (double-deduction).

Pins:
  1. First submit succeeds (200); the released amount lands ONCE in the
     ring-fenced materiality fund (F-3 semantics: a restricted balance, not a
     treasury debit — treasury is untouched by the allocation itself).
  2. An IDENTICAL re-submit returns 200 with a schema-valid body (allocated_budget
     + corporate_treasury present) — never a 500.
  3. The re-submit changes NOTHING: treasury unchanged, fund not re-created or
     doubled, same allocated_budget + debrief replayed.
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


def _fund(sid):
    gs = dbm._global_states[sid][-1]
    if "materiality_restricted_fund" in gs:
        return gs["materiality_restricted_fund"]
    return (gs.get("active_event_flags") or {}).get("materiality_restricted_fund", 0)


def test_duplicate_submit_replays_cleanly_no_500():
    sid = _solo()
    before = _treasury(sid)

    r1 = _submit(sid)
    assert r1.status_code == 200, r1.text
    body1 = r1.json()
    assert "allocated_budget" in body1 and "corporate_treasury" in body1
    after_first = _treasury(sid)
    assert after_first == before                       # F-3: release is a fund, not a debit
    fund_first = _fund(sid)
    assert fund_first >= body1["allocated_budget"]     # released into the ring-fenced fund

    # Identical re-submit — the exact loop trigger. Must be 200, never 500.
    r2 = _submit(sid)
    assert r2.status_code == 200, r2.text
    body2 = r2.json()
    assert body2["allocated_budget"] == body1["allocated_budget"]  # replayed
    assert body2["corporate_treasury"] is not None
    assert _treasury(sid) == after_first               # treasury untouched by replay
    assert _fund(sid) == fund_first                    # fund NOT re-created or doubled


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


def test_cfo_rejection_then_override_completes_and_stays_complete():
    """The full override sequence the classroom reported as looping:
    a non-material issue in Q1 → 400 CFO memo → Force Override → success.
    Completion must then be VISIBLE (csrd_completed) and a further submit —
    override or not — must replay, never re-open the exercise.

    Verified live against real Postgres (pgserver) on 2026-07-31 before being
    pinned here; the client-side layers are pinned in
    frontend/__tests__/csrd-matrix-loop.test.js."""
    sid = _solo()
    bad_payload = {
        "matrix_submission": {
            # two genuinely doubly-material issues + one that is NOT
            "quadrant_1_top_right": ["data_privacy_impact", "api_leakage_impact",
                                     "energy_financial_risk"],
            "quadrant_2_top_left": [],
            "quadrant_3_bottom_right": [],
            "quadrant_4_bottom_left": [],
        },
        "force_override_cfo": False,
    }
    r = client.post(f"/api/simulations/{sid}/materiality", json=bad_payload)
    assert r.status_code == 400, f"CFO gate should reject: {r.status_code} {r.text[:120]}"
    assert "CFO Override" in r.json()["detail"]

    # The rejection must not have committed ANYTHING (no half-submission).
    gs = dbm._global_states[sid][-1]
    assert not (gs.get("active_event_flags") or {}).get("_materiality_idempotency")

    bad_payload["force_override_cfo"] = True
    r2 = client.post(f"/api/simulations/{sid}/materiality", json=bad_payload)
    assert r2.status_code == 200, r2.text
    assert r2.json()["allocated_budget"] >= 0

    gs = dbm._global_states[sid][-1]
    assert gs.get("csrd_completed") is True
    # The override marker's persisted location differs by design: Postgres
    # unpacks every dynamic key to the top level; the memory store keeps
    # non-allow-listed keys packed inside active_event_flags. Either location
    # satisfies the parity contract — LOSING it entirely would not.
    _flags = gs.get("active_event_flags") or {}
    assert gs.get("cfo_override_used_r2") is True or _flags.get("cfo_override_used_r2") is True, (
        "the governance-penalty marker was dropped on persist")

    # Any further submit — the loop trigger — replays the committed result.
    r3 = client.post(f"/api/simulations/{sid}/materiality", json=bad_payload)
    assert r3.status_code == 200
    assert r3.json()["allocated_budget"] == r2.json()["allocated_budget"]
