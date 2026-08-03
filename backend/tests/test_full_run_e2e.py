"""A complete simulation, played over HTTP, with assertions that can fail.

WHAT THIS REPLACES
    `backend/test_e2e_full_flow.py` (596 lines) plays a full game and is the
    only end-to-end coverage this product has. pytest collects **zero** tests
    from it — it is an `if __name__ == "__main__"` script. It contains zero
    `assert` statements; checking is done by an `assert_ok(resp, label)` helper
    that only compares the status code against `(200, 201)` and appends to a
    list. Eighteen of its checks are wrapped in `if r.status_code == 200:`, so a
    500 does not fail the check — it SKIPS it. Its game-over stage logs terminal
    valuation, EBITDA, treasury, CO2, synergy and archetype, and asserts none of
    them.

    So the deepest collected pytest coverage of the commit path was five rounds
    (`test_brsr_paradigm.py`), and nothing at all played a full game over HTTP.

WHAT THIS DOES DIFFERENTLY
    1. It is collected. Ordinary pytest functions, no __main__ block.
    2. No `time.sleep(5.2)`. The 5-second per-session commit cooldown is cleared
       by popping `_commit_timestamps`, the way test_concurrent_commit_race.py
       already does. A 10-round run costs milliseconds instead of a minute.
    3. Every response is asserted, not conditionally inspected. A 500 fails.
    4. It asserts VALUES at game over, not just that the request succeeded.

WHAT IT IS FOR
    Not correctness of the model — the golden traces do that. This is the
    integration seam: routing, guards, gates, serialisation, persistence and the
    round state machine, exercised the way a cohort exercises them. It is the
    test that fails when the commit path breaks for a reason that has nothing to
    do with the engine, which is the failure a facilitator actually meets.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import pytest

_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))
os.environ.setdefault("USE_MEMORY_DB", "true")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("JWT_SECRET", "testsecret0123456789abcdefabcdef")

import httpx  # noqa: E402
from httpx import ASGITransport  # noqa: E402

from main import app  # noqa: E402
from router import _commit_timestamps  # noqa: E402

_ROUNDS = 10


def _run(coro):
    """Run an async body on a private event loop, disposing of any asyncpg pool
    that body created BEFORE the loop is closed.

    Why this is not simply `asyncio.run(...)`: `database.get_pool()` caches the
    pool in a MODULE GLOBAL, and an asyncpg pool is bound to the event loop it
    was created on. Close that loop and open a fresh one for the next test and
    the global still points at connections whose loop is dead — asyncpg then
    reports "Event loop is closed", or "cannot perform operation: another
    operation is in progress" when its half-finished state is re-entered.

    In memory mode there is no pool, so nothing notices. That is exactly why
    this defect survived until the suite first met real Postgres in CI: the
    harness encoded an assumption ("event loops are disposable") that only
    holds for the backend production does not use. test_postgres_parity.py hits
    the same hazard and works around it the same way — see its `saved_pool`
    block and the comment about the app's pool being bound to the client's loop.
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        try:
            import database as _active_db     # memory module or the real one
            if getattr(_active_db, "_pool", None) is not None:
                loop.run_until_complete(_active_db.close_pool())
        except Exception:                     # noqa: BLE001 — teardown only
            pass
        loop.close()


def _active_store():
    """The storage module the app is ACTUALLY using on this run.

    main.py rebinds `sys.modules["database"]` to `database_memory` when
    USE_MEMORY_DB is on, so `import database` yields whichever backend is live.
    Importing `database_memory` DIRECTLY reads the memory dicts even when the
    app is writing to PostgreSQL — which is precisely how these assertions came
    to report "a completed 10-round game produced an empty decision log" in the
    first Postgres CI run, while Postgres itself held all ten rounds:

        round_number | count
        -------------+-------
                   1 |    40
                  ...
                  10 |    36

    The product was right; the test was reading the wrong drawer.
    """
    import database
    return database


async def _play(ac, rounds=_ROUNDS):
    """Start a solo session and commit every round. Returns (sid, per-round responses)."""
    r = await ac.post("/api/simulations/solo-start",
                      json={"player_name": "E2E", "decision_paradigm": "legacy_abc"})
    assert r.status_code in (200, 201), f"solo-start failed: {r.status_code} {r.text[:300]}"
    sid = r.json()["session_id"]

    dash = await ac.get(f"/api/simulations/{sid}/dashboard")
    assert dash.status_code == 200, f"dashboard failed: {dash.status_code} {dash.text[:300]}"
    bus = dash.json()["business_units"]
    assert bus, "a new session has no business units"

    responses = []
    for rnd in range(1, rounds + 1):
        # Clear the 5s per-session cooldown rather than sleeping through it.
        _commit_timestamps.pop(sid, None)
        payload = {
            "decisions": [
                {"bu_id": b["bu_id"], "investment_ratio": 0.4,
                 "capex_allocated": 500_000, "choice_selected": "option_a"}
                for b in bus
            ],
            "force_override_cfo": True,
            "expected_round": rnd,
        }
        res = await ac.post(f"/api/simulations/{sid}/commit-turn", json=payload)
        assert res.status_code == 201, (
            f"round {rnd} commit failed: {res.status_code} {res.text[:400]}"
        )
        body = res.json()
        responses.append(body)
        bus = body.get("business_units") or bus

    return sid, responses


def _client():
    return httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


# ── 1. The run completes ───────────────────────────────────────────────────

def test_a_full_ten_round_game_completes_over_http():
    """Every round returns 201. No conditional inspection, no skipped checks."""
    async def go():
        async with _client() as ac:
            return await _play(ac)
    sid, responses = _run(go())
    assert len(responses) == _ROUNDS
    assert sid


def test_the_round_number_advances_exactly_once_per_commit():
    """Off-by-one or double-advance in the state machine shows up here and
    almost nowhere else — the engine tests never touch round bookkeeping."""
    async def go():
        async with _client() as ac:
            return await _play(ac)
    _sid, responses = _run(go())
    seen = [r["new_round_number"] for r in responses]
    assert seen == list(range(2, _ROUNDS + 1)) + [_ROUNDS], (
        f"round progression is wrong: {seen}. Expected 2..10 then 10 (R10 "
        f"persists in place rather than creating an 11th round)."
    )


# ── 2. The graded numbers exist and are numbers ────────────────────────────

def test_game_over_produces_real_terminal_values():
    """test_e2e_full_flow.py LOGGED these and asserted none of them."""
    async def go():
        async with _client() as ac:
            sid, responses = await _play(ac)
            final = await ac.get(f"/api/simulations/{sid}/dashboard")
            return sid, responses, final
    _sid, responses, final = _run(go())

    assert final.status_code == 200
    gs = final.json()["global_state"]

    for key in ("corporate_treasury", "historical_ebitda", "tco2e_emissions",
                "synergy_multiplier"):
        assert key in gs, f"{key} missing from the final state"
        assert isinstance(gs[key], (int, float)), f"{key} is not numeric: {gs[key]!r}"
        assert gs[key] == gs[key], f"{key} is NaN"          # NaN != NaN

    assert final.json()["current_round"] == _ROUNDS


def test_the_finale_marks_the_run_complete():
    """R10-1 (Phase 0): the normal finale sets game_over, so the run cannot be
    re-committed. Before that fix, completion was only ever INFERRED as
    `rn >= 10` in three separate places and R10 was infinitely re-committable."""
    async def go():
        async with _client() as ac:
            sid, _ = await _play(ac)
            return sid, await ac.get(f"/api/simulations/{sid}/dashboard")
    _sid, final = _run(go())
    flags = final.json()["global_state"].get("active_event_flags") or {}
    assert final.json()["global_state"].get("game_over") or flags.get("game_over"), (
        "the finale did not set game_over — R10 is re-committable again"
    )


def test_a_completed_run_refuses_another_commit():
    """The other half of R10-1, end to end: the guard has to hold over HTTP,
    not just in a unit test."""
    async def go():
        async with _client() as ac:
            sid, _ = await _play(ac)
            _commit_timestamps.pop(sid, None)
            dash = await ac.get(f"/api/simulations/{sid}/dashboard")
            bus = dash.json()["business_units"]
            return await ac.post(f"/api/simulations/{sid}/commit-turn", json={
                "decisions": [{"bu_id": b["bu_id"], "investment_ratio": 0.4,
                               "capex_allocated": 500_000, "choice_selected": "option_a"}
                              for b in bus],
                "force_override_cfo": True,
                "expected_round": _ROUNDS,
            })
    res = _run(go())
    assert res.status_code == 409, (
        f"a completed run accepted another commit ({res.status_code}) — the "
        "terminal valuation can be compounded by re-posting"
    )


# ── 3. The audit trail exists for the graded round ─────────────────────────

def test_every_round_including_the_finale_is_in_the_decision_log():
    """R10-2 (Phase 0): the R10 branch used to be `for dec in decisions_raw:
    pass`, so the graded finale's decisions were recorded nowhere at all.

    Note what this asserts: TEN distinct rounds carry decision rows. It does not
    assert WHICH round each set is filed under — see the xfail below.
    """
    db = _active_store()

    async def go():
        async with _client() as ac:
            sid, _ = await _play(ac)
            return sid
    sid = _run(go())

    log = _run(db.get_decision_log(sid))
    assert log, "a completed 10-round game produced an empty decision log"
    rounds_logged = sorted({entry["round_number"] for entry in log})
    assert rounds_logged == list(range(1, _ROUNDS + 1)), (
        f"a {_ROUNDS}-round game filed decisions under rounds {rounds_logged}. "
        "Every round's decisions must be recorded, under the round they were "
        "made in — a grade you cannot reconstruct is a grade you cannot defend."
    )


def test_decisions_are_attributed_to_the_round_they_were_made_in():
    """The contract, now enforced (AUDIT-1, fixed 2026-08-02).

    insert_next_round used to file a commit's decisions under the round it
    CREATED, so round 1 had no rows and every set was one round late — any
    debrief, grade reconstruction or replay read the wrong round. Both storage
    backends now file at `round_number - 1`; R10 files explicitly at
    `current_round` because its branch never reaches insert_next_round.

    Historical note: runs committed before the fix carry the old offset. They
    were not backfilled — decision_audit_log is append-only behind an
    immutability trigger, and no score had been graded from them.
    """
    db = _active_store()

    async def go():
        async with _client() as ac:
            sid, _ = await _play(ac)
            return sid
    sid = _run(go())

    rounds_logged = sorted({e["round_number"] for e in _run(db.get_decision_log(sid))})
    assert rounds_logged == list(range(1, _ROUNDS + 1)), (
        f"decisions are filed under rounds {rounds_logged}, expected "
        f"{list(range(1, _ROUNDS + 1))}"
    )


# ── 4. The history a debrief is built from ─────────────────────────────────

def test_the_dashboard_carries_the_whole_run_history():
    """The debrief, the trend charts and any future replay all read this."""
    async def go():
        async with _client() as ac:
            sid, _ = await _play(ac)
            return await ac.get(f"/api/simulations/{sid}/dashboard")
    final = _run(go())
    history = final.json().get("history") or []
    assert len(history) >= _ROUNDS - 1, (
        f"history has {len(history)} entries after a {_ROUNDS}-round game"
    )
    numbers = [h["global_state"]["corporate_treasury"] for h in history]
    assert len(set(numbers)) > 1, "treasury is identical in every history entry"


# ── 5. A stale client cannot double-advance ────────────────────────────────

def test_a_stale_expected_round_is_refused():
    """CMT-1 (Phase 0). The client retries a 429'd commit with the SAME payload;
    if the round has moved on, that retry used to commit the NEXT round with the
    previous round's decisions. uq_session_round does not catch it — the round
    numbers differ."""
    async def go():
        async with _client() as ac:
            r = await ac.post("/api/simulations/solo-start",
                              json={"player_name": "STALE", "decision_paradigm": "legacy_abc"})
            # Assert BEFORE parsing. Reading ["session_id"] off an error body
            # raises KeyError and buries the actual 500 detail, which is how the
            # first Postgres CI run reported a pool defect as a missing key.
            assert r.status_code in (200, 201), f"solo-start failed: {r.status_code} {r.text[:300]}"
            sid = r.json()["session_id"]
            dash = await ac.get(f"/api/simulations/{sid}/dashboard")
            bus = dash.json()["business_units"]
            decisions = [{"bu_id": b["bu_id"], "investment_ratio": 0.4,
                          "capex_allocated": 500_000, "choice_selected": "option_a"} for b in bus]

            _commit_timestamps.pop(sid, None)
            first = await ac.post(f"/api/simulations/{sid}/commit-turn",
                                  json={"decisions": decisions, "force_override_cfo": True,
                                        "expected_round": 1})
            _commit_timestamps.pop(sid, None)
            replay = await ac.post(f"/api/simulations/{sid}/commit-turn",
                                   json={"decisions": decisions, "force_override_cfo": True,
                                         "expected_round": 1})
            return sid, first, replay
    sid, first, replay = _run(go())
    assert first.status_code == 201
    assert replay.status_code == 409, (
        f"the retry advanced a second round ({replay.status_code}) — a lost "
        "response now costs the team a round"
    )
    detail = replay.json().get("detail")
    assert isinstance(detail, dict) and detail.get("code") == "stale_round", (
        f"expected a structured stale_round conflict, got {detail!r}. The client "
        "keys its silent re-sync on that code; without it the player sees an error."
    )
