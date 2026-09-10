"""N2 (EVAL_AuditResponse 2026-09-10, action 9) — every read-modify-write of a
session's latest state is bound to the round that was read.

F01 was one instance of a pattern: 45 call sites read the latest state,
mutate it and hand it to update_latest_global_state, which resolved "latest"
AGAIN at write time. Any of them overlapping a commit — a stakeholder map, a
materiality matrix, a side track, a facilitator shockwave looping over fifty
teams — replaced the new round's economics with the old round's.

Contract now: update_latest_global_state(..., expected_round=<the round
read>) raises StaleStateError (409 stale_state) and writes nothing when the
session has moved on; every call site in router.py / admin_router.py passes
it (ratchet below); the facilitator's cohort-wide shockwave re-applies its
mutation to a team's fresh round instead of failing or corrupting.
"""
from __future__ import annotations

import asyncio
import os
import re
import sys
import time
from pathlib import Path

import pytest

_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))
os.environ.setdefault("USE_MEMORY_DB", "true")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("JWT_SECRET", "testsecret0123456789abcdefabcdef")

import httpx  # noqa: E402
from httpx import ASGITransport  # noqa: E402

import admin_router as _ar  # noqa: E402
import router as _router  # noqa: E402
from main import app  # noqa: E402
from store_errors import StaleStateError  # noqa: E402
from tests.test_draft_round_bound import (  # noqa: E402
    _ECONOMIC_BU, _ECONOMIC_GLOBAL, _cohort, _commit, _dash, _login, _player, _run,
)


# ── the store contract ───────────────────────────────────────────────────────

def test_memory_store_refuses_a_write_bound_to_the_wrong_round():
    import database_memory as dm
    sid = f"n2-{int(time.time() * 1000)}"
    dm._global_states[sid] = [{"round_number": 1, "corporate_treasury": 1.0, "group_reputation": 50.0,
                               "synergy_multiplier": 1.0, "cost_of_capital": 0.05, "active_event_flags": {}},
                              {"round_number": 2, "corporate_treasury": 2.0, "group_reputation": 50.0,
                               "synergy_multiplier": 1.0, "cost_of_capital": 0.05, "active_event_flags": {}}]
    dm._bu_states[sid] = {1: [], 2: []}
    stale = {"corporate_treasury": 999.0, "group_reputation": 50.0, "synergy_multiplier": 1.0,
             "cost_of_capital": 0.05, "active_event_flags": {}}
    with pytest.raises(StaleStateError) as ei:
        _run(dm.update_latest_global_state(sid, stale, [], expected_round=1))
    assert ei.value.expected_round == 1 and ei.value.actual_round == 2
    assert dm._global_states[sid][-1]["corporate_treasury"] == 2.0     # nothing written
    _run(dm.update_latest_global_state(sid, stale, [], expected_round=2))
    assert dm._global_states[sid][-1]["corporate_treasury"] == 999.0
    dm._global_states.pop(sid, None); dm._bu_states.pop(sid, None)


def test_every_write_site_names_the_round_it_read():
    """Ratchet: no call to update_latest_global_state without expected_round
    in the two routers (definitions and comments excluded)."""
    for fn in ("router.py", "admin_router.py"):
        src = (_BACKEND_DIR / fn).read_text(encoding="utf-8")
        offenders = []
        for m in re.finditer(r"await db\.update_latest_global_state\(", src):
            # the call's argument list: up to the matching close paren
            depth, i = 1, m.end()
            while depth and i < len(src):
                depth += {"(": 1, ")": -1}.get(src[i], 0)
                i += 1
            call = src[m.start():i]
            if "expected_round=" not in call:
                offenders.append(src[:m.start()].count("\n") + 1)
        assert not offenders, f"{fn}: update_latest_global_state without expected_round at lines {offenders}"


# ── a player-side write losing the race with a commit ───────────────────────

def test_a_learning_bonus_that_loses_the_race_with_a_commit_is_refused(monkeypatch):
    """The audit's E01 schedule on a different endpoint: the learning-bonus
    handler reads R1, a commit inserts R2, the handler writes. Before: R2's
    economics replaced by R1's, 200. Now: 409 stale_state, R2 untouched."""
    async def go():
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
            await _login(ac, monkeypatch)
            cid = await _cohort(ac)
            sid, _, h = await _player(ac, cid, "TeamN")
            gate = asyncio.Event(); read_done = asyncio.Event()
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
            write = asyncio.create_task(ac.post(f"/api/simulations/{sid}/learning-bonus", headers=h,
                                                json={"activity_type": "podcast_complete", "notebook_id": "nb-race"}))
            await asyncio.wait_for(read_done.wait(), 10)
            commit = await _commit(ac, sid, h)
            assert commit.status_code == 201, commit.text[:300]
            committed = commit.json()
            gate.set()
            res = await asyncio.wait_for(write, 10)
            monkeypatch.undo()
            d = await _dash(ac, sid, h)
            return res, committed, d
    res, committed, d = _run(go())
    assert res.status_code == 409, res.text[:300]
    assert res.json()["detail"]["code"] == "stale_state"
    assert d["current_round"] == 2
    for k in _ECONOMIC_GLOBAL:
        assert d["global_state"][k] == pytest.approx(committed["global_state"][k]), k
    by_id = {b["bu_id"]: b for b in committed["business_units"]}
    for b in d["business_units"]:
        for k in _ECONOMIC_BU:
            assert b.get(k) == pytest.approx(by_id[b["bu_id"]].get(k)), (b["bu_id"], k)


# ── a facilitator cohort-wide write racing one team's commit ────────────────

def test_shockwave_lands_on_a_teams_fresh_round_when_it_commits_mid_loop(monkeypatch):
    async def go():
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
            await _login(ac, monkeypatch)
            cid = await _cohort(ac)
            sidA, _, hA = await _player(ac, cid, "TeamSA")
            sidB, _, hB = await _player(ac, cid, "TeamSB")
            gate = asyncio.Event(); read_done = asyncio.Event()
            real_fetch = _ar.db.fetch_latest_state
            armed = {"on": True}

            async def slow_fetch(session_id):
                state = await real_fetch(session_id)
                if armed["on"] and session_id == sidB:
                    armed["on"] = False
                    read_done.set()
                    await gate.wait()          # team B commits while the loop holds B's R1
                return state
            monkeypatch.setattr(_ar.db, "fetch_latest_state", slow_fetch)
            _ar._god_mode_settings["shockwave_enabled"] = True
            shock = asyncio.create_task(ac.post(f"/api/admin/{cid}/shockwave", json={"event_id": "cyber_attack", "countdown": 0}))
            await asyncio.wait_for(read_done.wait(), 10)
            commit = await _commit(ac, sidB, hB)
            assert commit.status_code == 201, commit.text[:300]
            committed_b = commit.json()["global_state"]
            gate.set()
            res = await asyncio.wait_for(shock, 10)
            monkeypatch.undo()
            dA = await _dash(ac, sidA, hA)
            dB = await _dash(ac, sidB, hB)
            return res, committed_b, dA, dB
    res, committed_b, dA, dB = _run(go())
    assert res.status_code == 200, res.text[:300]
    body = res.json()
    assert body["teams_hit"] == 2 and body["skipped_stale"] == []
    # A: shockwave on round 1 as usual
    assert dA["current_round"] == 1
    assert dA["global_state"]["corporate_treasury"] == pytest.approx(50_000_000.0 - 4_000_000.0)
    # B: the commit produced R2; the shockwave was re-applied to R2, not to a stale R1 copy
    assert dB["current_round"] == 2
    assert dB["global_state"]["corporate_treasury"] == pytest.approx(committed_b["corporate_treasury"] - 4_000_000.0)
    assert dB["global_state"]["group_reputation"] == pytest.approx(max(0, committed_b["group_reputation"] - 7))
    swans = (dB["global_state"].get("active_event_flags") or {}).get("custom_black_swans") or []
    assert any(s.get("event_id") == "cyber_attack" for s in swans)
