"""The free-mode "Waiting for Other Teams" barrier is enforced server-side —
audit 2026-09-04 F-18(ii) · WP-18.

In free mode (the default) the cohort advances together: after committing
round N a team waits until every team has committed N, the auto-advance
timeout lapses, or the facilitator forces. That barrier was React state
only — a reload skipped it and the server accepted round N+1 from a team
while a sibling was still on round N (~/audit_scratch/flow/probe_flow.py
A3 → 201). The commit path now consults the same status the dashboard
computes and refuses a team that is ahead with the barrier's own copy.
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

import router as _router  # noqa: E402
from admin_shared import _get_pacing  # noqa: E402
from main import app  # noqa: E402


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
    return r.json()["session_id"], {"Authorization": f"Bearer {r.json()['player_token']}", "X-Player-Id": pid}


async def _dash(ac, sid, hdr):
    r = await ac.get(f"/api/simulations/{sid}/dashboard", headers=hdr)
    assert r.status_code == 200, r.text[:200]
    return r.json()


async def _commit(ac, sid, hdr):
    _router._commit_timestamps.pop(sid, None)
    d = await _dash(ac, sid, hdr)
    body = {"decisions": [{"bu_id": b["bu_id"], "investment_ratio": 0.3, "capex_allocated": 500_000,
                           "choice_selected": "option_a"} for b in d["business_units"]],
            "dividends_paid": 0.0, "force_override_cfo": True, "expected_round": d["current_round"]}
    return await ac.post(f"/api/simulations/{sid}/commit-turn", json=body, headers=hdr)


async def _cohort(ac, tag):
    r = await ac.post("/api/simulations/start", json={"cohort_name": f"FA-{tag}-{int(time.time()*1000)}", "decision_paradigm": "legacy_abc"})
    assert r.status_code == 201, r.text[:200]
    return r.json()["session_id"]


def test_a_team_ahead_waits_until_every_team_has_committed(monkeypatch):
    async def go():
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
            await _login(ac, monkeypatch)
            cid = await _cohort(ac, "wait")
            sidA, hA = await _player(ac, cid, "TeamA")
            sidB, hB = await _player(ac, cid, "TeamB")
            assert _get_pacing(cid)["mode"] == "free"
            assert (await _commit(ac, sidA, hA)).status_code == 201       # A commits R1
            ahead = await _commit(ac, sidA, hA)                            # A tries R2 (reload skipped the client barrier)
            dA = await _dash(ac, sidA, hA)
            assert (await _commit(ac, sidB, hB)).status_code == 201       # B commits R1 → in sync
            released = await _commit(ac, sidA, hA)                         # A's R2 now goes through
            return ahead, dA, released
    ahead, dA, released = _run(go())
    assert ahead.status_code == 403, f"a team ran ahead of the cohort: {ahead.status_code} {ahead.text[:200]}"
    detail = ahead.json()["detail"]
    assert detail["code"] == "waiting_for_teams"
    assert "other teams" in detail["message"].lower() and detail["teams"] == 2
    assert dA["current_round"] == 2 and dA["global_state"].get("cohort_advance_unblocked") is False
    assert released.status_code == 201


def test_a_team_behind_is_never_blocked_and_force_advance_releases(monkeypatch):
    async def go():
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
            await _login(ac, monkeypatch)
            cid = await _cohort(ac, "force")
            sidA, hA = await _player(ac, cid, "TeamA")
            sidB, hB = await _player(ac, cid, "TeamB")
            assert (await _commit(ac, sidA, hA)).status_code == 201
            assert (await _commit(ac, sidA, hA)).status_code == 403
            # B (behind) commits R1 freely, then R2 while A waits? no: after B's R1 both are at 2 → both may commit R2
            assert (await _commit(ac, sidB, hB)).status_code == 201
            assert (await _commit(ac, sidB, hB)).status_code == 201       # B at 3, A at 2 → B is ahead now
            assert (await _commit(ac, sidB, hB)).status_code == 403       # B cannot run to R4
            # the facilitator forces: A (behind) is auto-committed from defaults, barrier released
            r = await ac.post(f"/api/admin/sessions/{cid}/force-advance")
            assert r.status_code == 200, r.text[:200]
            await _dash(ac, sidA, hA)        # the dashboard poll applies the force (auto-commits A from defaults)
            dA = await _dash(ac, sidA, hA)   # …and the next poll shows the advanced state
            dB = await _dash(ac, sidB, hB)
            rB = await _commit(ac, sidB, hB)
            return dA, dB, rB
    dA, dB, rB = _run(go())
    assert dA["current_round"] == 3, dA["current_round"]
    assert (dA["global_state"].get("active_event_flags") or {}).get("auto_committed") is True
    assert rB.status_code == 201


def test_manual_pacing_is_untouched_and_solo_is_never_barred(monkeypatch):
    async def go():
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
            await _login(ac, monkeypatch)
            cid = await _cohort(ac, "manual")
            sidA, hA = await _player(ac, cid, "TeamA")
            _sidB, _hB = await _player(ac, cid, "TeamB")
            assert (await ac.post(f"/api/admin/sessions/{cid}/pacing", json={"mode": "manual"})).status_code == 200
            assert (await _commit(ac, sidA, hA)).status_code == 201
            locked = await _commit(ac, sidA, hA)
            assert (await ac.post(f"/api/admin/sessions/{cid}/pacing/unlock", json={"target_round": 2})).status_code == 200
            opened = await _commit(ac, sidA, hA)   # B still on R1, but manual pacing has no barrier
            import admin_shared
            admin_shared._god_mode_settings["solo_mode_enabled"] = True
            r = await ac.post("/api/simulations/solo-start", json={"player_name": "Solo", "decision_paradigm": "legacy_abc"})
            sid = r.json()["session_id"]
            solo = [(await _commit(ac, sid, {})).status_code for _ in range(3)]
            return locked, opened, solo
    locked, opened, solo = _run(go())
    assert locked.status_code == 403 and "locked" in str(locked.json()["detail"]).lower()
    assert opened.status_code == 201
    assert solo == [201, 201, 201]
