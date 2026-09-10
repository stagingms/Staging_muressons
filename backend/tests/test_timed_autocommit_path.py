"""Timed-pacing auto-commit goes through the real commit path — audit
2026-09-04 OPS-1 · WP-17.

admin_router._scheduled_unlock_task (timed mode with an interval) used its
own engine chain, _auto_commit_player: no commit lock, defaults instead of
the team's saved draft, and `active_event_flags = events` — which REPLACED
the persisted flags. An auto-committed team lost 26 flag keys
(stochastic_seed, decision_paradigm, ending_pathway, loan_interest_rate,
every new-engine state …), so its later stochastic events diverged from the
cohort and every engine panel went blank; at R10 it got a round-11 row with
no game_over. It now calls router._auto_commit_laggards — the Force-Advance
path: _run_commit_locked, draft-aware, flags merged, R10-aware, disclosure
stamped. ~/audit_scratch/ops/probe_timed_autocommit.py as a test.
"""
from __future__ import annotations

import asyncio
import os
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
from admin_shared import _get_pacing, is_round_unlocked  # noqa: E402
from main import app  # noqa: E402

_VOLATILE = {"cohort_team_count", "team_commits_this_round", "decisions_raw", "auto_committed",
             "auto_committed_source", "auto_committed_reason"}


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _login(ac, mp):
    import master_credentials
    mp.setattr(master_credentials, "MASTER_PASSWORD", "test-master-pw", raising=False)
    mp.setattr(master_credentials, "_load_override_hash", lambda: None, raising=False)
    r = await ac.post("/api/admin/facilitators/login", json={"facilitator_id": "god_mode", "password": "test-master-pw"})
    assert r.status_code == 200, r.text[:200]


async def _player(ac, cid, name):
    import rate_limit
    rate_limit._rate_buckets.clear()
    r = await ac.post(f"/api/admin/{cid}/generate-player")
    pid, pw = r.json()["player_id"], r.json()["password"]
    r = await ac.post(f"/api/simulations/public/sessions/{cid}/join", json={"player_id": pid, "password": pw, "player_name": name})
    assert r.status_code == 200, r.text[:200]
    r = await ac.post("/api/simulations/change-password", json={"player_id": pid, "old_password": pw, "new_password": name + "#2026pw"})
    assert r.status_code == 200, r.text[:200]
    rate_limit._rate_buckets.clear()
    r = await ac.post("/api/simulations/player-login", json={"player_id": pid, "password": name + "#2026pw"})
    assert r.status_code == 200, r.text[:200]
    return r.json()["session_id"], pid, {"Authorization": f"Bearer {r.json()['player_token']}", "X-Player-Id": pid}


async def _dash(ac, sid, hdr):
    r = await ac.get(f"/api/simulations/{sid}/dashboard", headers=hdr)
    assert r.status_code == 200, r.text[:200]
    return r.json()


async def _commit(ac, sid, hdr, choice="option_a"):
    _router._commit_timestamps.pop(sid, None)
    d = await _dash(ac, sid, hdr)
    body = {"decisions": [{"bu_id": b["bu_id"], "investment_ratio": 0.3, "capex_allocated": 500_000,
                           "choice_selected": choice} for b in d["business_units"]],
            "dividends_paid": 0.0, "force_override_cfo": True, "expected_round": d["current_round"]}
    return await ac.post(f"/api/simulations/{sid}/commit-turn", json=body, headers=hdr)


async def _fire_timer(cid):
    p = _get_pacing(cid)
    if p.get("_timer_task"):
        try:
            p["_timer_task"].cancel()
        except Exception:
            pass
    await _ar._scheduled_unlock_task(cid, 0)


def test_auto_commit_player_is_gone():
    assert not hasattr(_ar, "_auto_commit_player")
    import inspect
    src = inspect.getsource(_ar._scheduled_unlock_task)
    assert "_auto_commit_laggards(session_id, current_unlocked + 1)" in src


def test_timed_auto_commit_keeps_the_flags_and_uses_the_draft(monkeypatch):
    async def go():
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
            await _login(ac, monkeypatch)
            r = await ac.post("/api/simulations/start", json={"cohort_name": f"OPS1-{int(time.time()*1000)}", "decision_paradigm": "legacy_abc",
                                                            "ending_pathway": "hostile_takeover"})
            cid = r.json()["session_id"]
            sidA, _, hA = await _player(ac, cid, "TeamA")
            sidB, _, hB = await _player(ac, cid, "TeamB")
            # B saves a draft: option C, $2M per BU
            dB = await _dash(ac, sidB, hB)
            r = await ac.post(f"/api/simulations/{sidB}/save-decisions", headers=hB,
                              json={"allocations": {b["bu_id"]: 2_000_000 for b in dB["business_units"]}, "decision_choice": "option_c",
                                    "expected_round": dB["current_round"]})   # F01: drafts name their round
            assert r.status_code == 200, r.text[:200]
            # timed pacing with an interval (the API path the UI does not use)
            r = await ac.post(f"/api/admin/sessions/{cid}/pacing", json={"mode": "timed", "interval_seconds": 180})
            assert r.status_code == 200, r.text[:200]
            assert is_round_unlocked(cid, 2) is False
            assert (await _commit(ac, sidA, hA)).status_code == 201
            await _fire_timer(cid)
            assert _get_pacing(cid)["unlocked_round"] == 2
            dA = await _dash(ac, sidA, hA)
            dB = await _dash(ac, sidB, hB)
            return dA, dB
    dA, dB = _run(go())
    assert dA["current_round"] == 2 and dB["current_round"] == 2
    fA = dA["global_state"]["active_event_flags"]
    fB = dB["global_state"]["active_event_flags"]
    # A and B made different decisions (A: option A by hand; B: option C from
    # its draft), so decision-driven event keys legitimately differ. The wipe
    # took 26 PERSISTENT keys; none of those may be missing, and the flag set
    # must be the same size as a hand-committed team's, give or take events.
    # The wipe took the PERSISTENT keys (the audit's list) — those must all be
    # there; event-driven keys legitimately differ between A's and B's decisions.
    persistent = ("stochastic_seed", "decision_paradigm", "ending_pathway", "loan_interest_rate", "difficulty_tier")
    missing = [k for k in persistent if k in fA and k not in fB]
    assert not missing, f"auto-committed team lost persistent flags: {missing}"
    # every engine sub-state A carries, B carries too (on the state or folded into the flags)
    def _has(d, f, k):
        return k in d["global_state"] or k in f
    engine_states = [k for k in ("npc_stakeholders", "org_politics", "supply_chain", "board_governance",
                                 "balance_sheet", "autonomous_agents", "biodiversity") if _has(dA, fA, k)]
    assert engine_states, "precondition: a hand-committed team carries engine sub-states"
    lost = [k for k in engine_states if not _has(dB, fB, k)]
    assert not lost, f"auto-committed team lost engine state: {lost}"
    assert len(fB) >= 0.9 * len(fA), (len(fA), len(fB))
    for k in ("stochastic_seed", "ending_pathway", "loan_interest_rate"):
        assert fB.get(k) == fA.get(k), (k, fB.get(k), fA.get(k))
    assert fB["ending_pathway"] == "hostile_takeover"
    assert fB.get("auto_committed") is True and fB.get("auto_committed_source") == "draft"
    # the draft was honoured: $2M per BU from the saved allocations, not the
    # old hard-coded $1/BU (the option letter is shuffled per session, so the
    # capex is the unambiguous witness)
    decs = dB["global_state"].get("decisions_raw") or fB.get("decisions_raw") or []
    assert decs, "no decisions recorded for the auto-committed round"
    assert all(float(d.get("capex_allocated", 0)) == pytest.approx(2_000_000, abs=1) for d in decs), decs


def test_r10_timed_auto_commit_ends_the_game_properly(monkeypatch):
    async def go():
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
            await _login(ac, monkeypatch)
            r = await ac.post("/api/simulations/start", json={"cohort_name": f"OPS1R10-{int(time.time()*1000)}", "decision_paradigm": "legacy_abc"})
            cid = r.json()["session_id"]
            sidC, _, hC = await _player(ac, cid, "TeamC")
            for i in range(9):
                rc = await _commit(ac, sidC, hC)
                assert rc.status_code == 201, f"R{i+1}: {rc.status_code} {rc.text[:200]}"
            d = await _dash(ac, sidC, hC)
            assert d["current_round"] == 10
            r = await ac.post(f"/api/admin/sessions/{cid}/pacing", json={"mode": "timed", "interval_seconds": 180})
            assert r.status_code == 200
            await _fire_timer(cid)
            d = await _dash(ac, sidC, hC)
            late = await _commit(ac, sidC, hC)
            rep = await ac.get(f"/api/simulations/{sidC}/final-report", headers=hC)
            return d, late.status_code, rep.status_code, rep.json() if rep.status_code == 200 else rep.text[:200]
    d, late_status, rep_status, rep = _run(go())
    gs = d["global_state"]
    flags = gs.get("active_event_flags") or {}
    assert d["current_round"] == 10, "an R11 row was written"
    # the R10 path persists in place; the memory store folds game_over into the flags
    assert gs.get("game_over") is True or flags.get("game_over") is True
    assert flags.get("terminal_value") is not None and flags.get("profile")
    assert len(d.get("history") or []) <= 11
    assert late_status in (400, 409, 403)
    assert rep_status == 200 and rep.get("regenerative_multiple") is not None
