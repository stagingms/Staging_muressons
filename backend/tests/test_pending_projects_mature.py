"""Audit F-05 (FLAG-1): R8-C "Desalination Mega-Project" must pay inside the game.

round_configs R8 option_c promised "$5M/round revenue from Round 10 onward for
3 rounds"; the handler queued ONE pending project with rounds_remaining =
payback_rounds = 3. engine._process_pending_projects matures a project when the
counter reaches 0 and the game ends at round 10, so the counter went 3 -> 2
(R9) -> 1 (R10) and $0 was ever credited (audit probe flag/probe_deferred.py).
payback_rounds is now 2 — it matures at the R10 tick like the NCD drop queued
beside it — and the copy says a single $5M payment.
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

import router as _router  # noqa: E402
from main import app  # noqa: E402
from round_configs import get_round_config  # noqa: E402


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _display_key(sid, canonical, rnd):
    import database_memory as dm
    from option_shuffle import get_shuffle_mapping
    seed = (dm._sessions.get(sid) or {}).get("shuffle_seed")
    if not seed:
        return canonical
    return get_shuffle_mapping(seed, rnd)["canonical_to_display"].get(canonical, canonical)


def test_the_option_copy_and_the_config_agree():
    opt = get_round_config(8)["options"]["option_c"]
    assert opt["impacts"]["generates_revenue"] == 5_000_000
    assert opt["impacts"]["payback_rounds"] == 2      # 8 + 2 = matures at the R10 tick
    assert "single $5M" in opt["description"]
    assert "for 3 rounds" not in opt["description"]


def test_desalination_revenue_is_credited_at_the_round_ten_tick():
    async def go():
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            r = await ac.post("/api/simulations/solo-start",
                              json={"player_name": "Desal", "decision_paradigm": "legacy_abc"})
            assert r.status_code in (200, 201), r.text[:300]
            sid = r.json()["session_id"]
            bus = (await ac.get(f"/api/simulations/{sid}/dashboard")).json()["business_units"]
            out = {}
            for rnd in range(1, 11):
                canonical = "option_c" if rnd == 8 else "option_b"
                _router._commit_timestamps.pop(sid, None)
                r = await ac.post(f"/api/simulations/{sid}/commit-turn", json={
                    "decisions": [{"bu_id": b["bu_id"], "investment_ratio": 0.3, "capex_allocated": 1_000_000,
                                   "choice_selected": _display_key(sid, canonical, rnd)} for b in bus],
                    "force_override_cfo": True, "expected_round": rnd})
                assert r.status_code == 201, f"R{rnd}: {r.status_code} {r.text[:300]}"
                body = r.json()
                bus = body.get("business_units") or bus
                out[rnd] = body
            return out
    bodies = _run(go())
    # Queued at R8 with two rounds to run …
    pending_after_r8 = bodies[8]["global_state"].get("pending_capex_projects") or []
    desal = [p for p in pending_after_r8 if "Desalination" in str(p.get("description", ""))]
    assert desal and desal[0]["rounds_remaining"] == 2, pending_after_r8
    # … and matured at the R10 tick: the $5M is in that round's credited total
    # (the DSO working-capital deferral matures every round; it is < $5M).
    ev10 = bodies[10]["events"] or {}
    assert float(ev10.get("revenue_generation_completed") or 0) >= 5_000_000, ev10.get("revenue_generation_completed")
    assert not [p for p in (bodies[10]["global_state"].get("pending_capex_projects") or [])
                if "Desalination" in str(p.get("description", ""))], "desalination still pending after R10"
