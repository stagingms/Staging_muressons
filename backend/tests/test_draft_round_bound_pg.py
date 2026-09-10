"""F01 (audit 2026-09-09) on REAL PostgreSQL — the store the class runs on.

The memory-store tests in test_draft_round_bound.py prove the handler; this
module proves the write itself against Postgres: the round-bound single
statement, the append-only trigger refusing a write to a round that is no
longer current, and the barrier schedule from the audit (save reads R1,
commit inserts R2, save writes) leaving R2 exactly as the commit produced it.

Gated like tests/test_postgres_parity.py: PG_PARITY=1 with USE_MEMORY_DB=false
and a reachable DATABASE_URL (CI's backend-postgres job). Skipped otherwise.
"""
from __future__ import annotations

import asyncio
import os
import socket
from urllib.parse import urlparse

import pytest

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/muressons")


def _pg_reachable() -> bool:
    if "host=/" in DATABASE_URL:
        return True
    try:
        p = urlparse(DATABASE_URL)
        with socket.create_connection((p.hostname or "localhost", p.port or 5432), timeout=2):
            return True
    except OSError:
        return False


_OPTED_IN = os.environ.get("PG_PARITY", "").strip() in ("1", "true", "yes") or bool(os.environ.get("CI"))
pytestmark = pytest.mark.skipif(
    not (_OPTED_IN and _pg_reachable()),
    reason="Postgres draft-race suite: set PG_PARITY=1, USE_MEMORY_DB=false and a reachable DATABASE_URL.",
)

import httpx  # noqa: E402
from httpx import ASGITransport  # noqa: E402

import main  # noqa: E402
import router as _router  # noqa: E402
from tests.test_draft_round_bound import (  # noqa: E402
    _ECONOMIC_BU, _ECONOMIC_GLOBAL, _cohort, _commit, _dash, _login, _player,
)


def _run_pg(coro):
    """A fresh loop per test; the asyncpg pool binds to the loop that creates
    it, so drop the module pool first and let get_pool() rebuild it here."""
    import database
    database._pool = None
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        try:
            pool = database._pool
            if pool is not None:
                loop.run_until_complete(pool.close())
        except Exception:
            pass
        database._pool = None
        loop.close()


@pytest.fixture(autouse=True)
def _real_store():
    assert main.db.__name__ == "database", (
        "App selected the MEMORY store — this suite must run with USE_MEMORY_DB=false "
        f"against {DATABASE_URL}")


def test_update_draft_fields_is_round_bound_and_touches_nothing_else(monkeypatch):
    async def go():
        import database as db
        async with httpx.AsyncClient(transport=ASGITransport(app=main.app), base_url="http://t") as ac:
            await _login(ac, monkeypatch)
            cid = await _cohort(ac)
            sid, _, h = await _player(ac, cid, "PGa")
            before = await db.fetch_latest_state(sid)
            ok = await db.update_draft_fields(sid, 1, {"saved_allocations": {"pharma": 7}, "saved_round": 1})
            wrong = await db.update_draft_fields(sid, 2, {"saved_allocations": {"pharma": 8}, "saved_round": 2})
            after = await db.fetch_latest_state(sid)
            return before, ok, wrong, after
    before, ok, wrong, after = _run_pg(go())
    assert ok is True and wrong is False
    assert after["global_state"]["saved_allocations"] == {"pharma": 7}
    assert after["global_state"]["saved_round"] == 1
    for k in _ECONOMIC_GLOBAL:
        assert after["global_state"][k] == before["global_state"][k], k
    for b_before, b_after in zip(before["bu_states"], after["bu_states"]):
        for k in _ECONOMIC_BU:
            assert b_after.get(k) == b_before.get(k), (b_after["bu_id"], k)


def test_a_draft_for_a_closed_round_is_refused_by_the_trigger(monkeypatch):
    """After a commit, R1 is historical; the append-only trigger must refuse
    the UPDATE and update_draft_fields must report that as 'not saved'."""
    async def go():
        import database as db
        async with httpx.AsyncClient(transport=ASGITransport(app=main.app), base_url="http://t") as ac:
            await _login(ac, monkeypatch)
            cid = await _cohort(ac)
            sid, _, h = await _player(ac, cid, "PGb")
            assert (await _commit(ac, sid, h)).status_code == 201
            refused = await db.update_draft_fields(sid, 1, {"saved_allocations": {"pharma": 9}, "saved_round": 1})
            d = await _dash(ac, sid, h)
            return refused, d
    refused, d = _run_pg(go())
    assert refused is False
    assert d["current_round"] == 2
    assert not d["global_state"].get("saved_allocations")


def test_autosave_that_loses_the_race_with_a_commit_changes_nothing_on_postgres(monkeypatch):
    """The audit's E01 schedule on the production store."""
    async def go():
        async with httpx.AsyncClient(transport=ASGITransport(app=main.app), base_url="http://t") as ac:
            await _login(ac, monkeypatch)
            cid = await _cohort(ac)
            sid, _, h = await _player(ac, cid, "PGc")
            gate = asyncio.Event()
            read_done = asyncio.Event()
            real_fetch = _router.db.fetch_latest_state
            armed = {"on": True}

            async def slow_fetch(session_id):
                state = await real_fetch(session_id)
                if armed["on"] and session_id == sid:
                    armed["on"] = False
                    read_done.set()
                    await gate.wait()
                return state
            monkeypatch.setattr(_router.db, "fetch_latest_state", slow_fetch)
            save = asyncio.create_task(ac.post(
                f"/api/simulations/{sid}/save-decisions", headers=h,
                json={"allocations": {"pharma": 4_000_000}, "decision_choice": "option_c", "expected_round": 1}))
            await asyncio.wait_for(read_done.wait(), 10)
            commit = await _commit(ac, sid, h)
            assert commit.status_code == 201, commit.text[:300]
            committed = commit.json()
            gate.set()
            save_res = await asyncio.wait_for(save, 10)
            monkeypatch.undo()
            d = await _dash(ac, sid, h)
            return save_res, committed, d
    save_res, committed, d = _run_pg(go())
    assert save_res.status_code == 409 and save_res.json()["detail"]["code"] == "stale_draft"
    assert d["current_round"] == 2
    for k in _ECONOMIC_GLOBAL:
        assert d["global_state"][k] == pytest.approx(committed["global_state"][k]), k
    by_id = {b["bu_id"]: b for b in committed["business_units"]}
    for b in d["business_units"]:
        for k in _ECONOMIC_BU:
            assert b.get(k) == pytest.approx(by_id[b["bu_id"]].get(k)), (b["bu_id"], k)
    assert not d["global_state"].get("saved_allocations")


def test_pillar_draft_round_trips_through_postgres(monkeypatch):
    async def go():
        async with httpx.AsyncClient(transport=ASGITransport(app=main.app), base_url="http://t") as ac:
            await _login(ac, monkeypatch)
            cid = await _cohort(ac, "multi_toggles")
            sid, _, h = await _player(ac, cid, "PGd")
            pillars = {"energy": "solar_capex", "operations": "digital_twin"}
            r = await ac.post(f"/api/simulations/{sid}/save-decisions", headers=h,
                              json={"allocations": {"pharma": 1}, "decision_choice": None,
                                    "pillar_decisions": pillars, "expected_round": 1})
            d = await _dash(ac, sid, h)
            return r, d, pillars
    r, d, pillars = _run_pg(go())
    assert r.status_code == 200, r.text[:200]
    assert d["global_state"]["saved_pillar_decisions"] == pillars
    assert d["global_state"]["saved_round"] == 1


def test_update_latest_global_state_is_round_bound_on_postgres(monkeypatch):
    """N2: the general write helper refuses a write bound to a round the
    session has left — both by the round it finds (StaleStateError before
    any UPDATE) and, for the SELECT→UPDATE gap, via the append-only trigger."""
    from store_errors import StaleStateError

    async def go():
        import database as db
        async with httpx.AsyncClient(transport=ASGITransport(app=main.app), base_url="http://t") as ac:
            await _login(ac, monkeypatch)
            cid = await _cohort(ac)
            sid, _, h = await _player(ac, cid, "PGn2")
            r1 = await db.fetch_latest_state(sid)
            assert (await _commit(ac, sid, h)).status_code == 201
            stale_gs = dict(r1["global_state"]); stale_gs["corporate_treasury"] = 1.0
            refused = None
            try:
                await db.update_latest_global_state(sid, stale_gs, r1["bu_states"], expected_round=1)
            except StaleStateError as exc:
                refused = exc
            after = await db.fetch_latest_state(sid)
            return refused, after
    refused, after = _run_pg(go())
    assert refused is not None and refused.expected_round == 1 and refused.actual_round == 2
    assert after["round_number"] == 2 and after["global_state"]["corporate_treasury"] != 1.0


def test_a_committed_rounds_draft_does_not_reach_the_next_row_or_a_force_advance_on_postgres(monkeypatch):
    """Found by the burst drill (2026-09-10) ON THIS STORE: the draft keys live
    in active_event_flags here, the commit's flag merge forwarded them, and
    a Force Advance re-committed last round's pillar draft as this round's
    decisions. The memory store hid it (its dashboard reads the row's top
    level, which the commit did clear)."""
    from pillar_configs import get_pillar_config
    cfg = get_pillar_config(1)
    pillars_r1 = {area: list(spec["options"])[0] for area, spec in cfg["areas"].items()}

    async def go():
        import database as db
        async with httpx.AsyncClient(transport=ASGITransport(app=main.app), base_url="http://t") as ac:
            await _login(ac, monkeypatch)
            cid = await _cohort(ac, "multi_toggles")
            sid, _, h = await _player(ac, cid, "PGdraft")
            r = await ac.post(f"/api/simulations/{sid}/save-decisions", headers=h,
                              json={"allocations": {"pharma": 4_000_000.0}, "decision_choice": None,
                                    "pillar_decisions": pillars_r1, "expected_round": 1})
            assert r.status_code == 200, r.text[:200]
            assert (await _commit(ac, sid, h, choice="", pillars=pillars_r1)).status_code == 201
            row2 = await db.fetch_latest_state(sid)
            d2 = await _dash(ac, sid, h)
            pulse = await ac.get(f"/api/admin/cohort-pulse/{cid}")
            advanced = await _router._auto_commit_laggards(cid, 3)
            d3 = await _dash(ac, sid, h)
            return row2, d2, pulse, advanced, d3
    row2, d2, pulse, advanced, d3 = _run_pg(go())
    flags2 = row2["global_state"].get("active_event_flags") or {}
    for k in ("saved_allocations", "saved_decision_choice", "saved_round", "saved_pillar_decisions"):
        assert k not in flags2, k
        assert not d2["global_state"].get(k), k
    team = next(t for t in pulse.json()["teams"] if t.get("session_id") == d2["session_id"])
    assert team["has_saved_draft"] is False
    assert advanced == 1 and d3["current_round"] == 3
    f3 = d3["global_state"]["active_event_flags"]
    assert f3.get("auto_committed_source") == "legacy_fallback", f3.get("auto_committed_source")
    assert not f3.get("r2_pillar_flags"), "R1's pillar selections were replayed as R2's decisions"
