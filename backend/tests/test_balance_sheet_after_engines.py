"""Audit F-08(b) / FIN-02: the round's balance sheet is struck AFTER the
engines that write treasury in the same batch.

run_new_engines used to tick the balance sheet right after biodiversity —
before npc_stakeholders (the $5-25M regulator fine), the autonomous agents
and the tipping caps wrote treasury/opex. The statement's cash line therefore
disagreed with the persisted treasury in 50 of 200 audited round statements,
by up to $24.5M, including the R10 statement the debrief projects
("cash $23.4M" beside a KPI belt reading $1.5M). The block now runs after
every state-mutating engine in the batch.
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

import npc_stakeholders  # noqa: E402
import router as _router  # noqa: E402
from main import app  # noqa: E402


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _play(ac, rounds=10):
    r = await ac.post("/api/simulations/solo-start",
                      json={"player_name": "BS", "decision_paradigm": "legacy_abc"})
    assert r.status_code in (200, 201), r.text[:300]
    sid = r.json()["session_id"]
    bus = (await ac.get(f"/api/simulations/{sid}/dashboard")).json()["business_units"]
    bodies = []
    for rnd in range(1, rounds + 1):
        _router._commit_timestamps.pop(sid, None)
        r = await ac.post(f"/api/simulations/{sid}/commit-turn", json={
            "decisions": [{"bu_id": b["bu_id"], "investment_ratio": 0.3, "capex_allocated": 2_000_000,
                           "choice_selected": "option_b"} for b in bus],
            "force_override_cfo": True, "expected_round": rnd})
        assert r.status_code == 201, f"R{rnd}: {r.status_code} {r.text[:300]}"
        body = r.json()
        bodies.append(body)
        bus = body.get("business_units") or bus
    return sid, bodies


def _cash_matches_treasury(body: dict, rnd: int):
    gs = body["global_state"]
    bs = gs.get("balance_sheet") or (gs.get("active_event_flags") or {}).get("balance_sheet")
    assert bs, f"R{rnd}: no balance sheet on the persisted state"
    diag = (body.get("events") or {}).get("balance_sheet") or {}
    treasury = float(gs["corporate_treasury"])
    cash = float(bs["current_assets"]["cash_and_equivalents"])
    std = float(bs["current_liabilities"].get("short_term_debt", 0.0) or 0.0)
    if treasury >= 0:
        assert cash == pytest.approx(treasury, abs=0.01), f"R{rnd}: cash {cash} vs treasury {treasury}"
        assert std == pytest.approx(0.0, abs=0.01), f"R{rnd}: short-term debt {std} with positive treasury"
        return
    # Negative treasury: cash is swept to short-term debt. The sweep then
    # prices the deficit and charges that interest to the treasury AFTER the
    # sync (balance_sheet._sweep_negative_cash — its pricing is audit item
    # F-13); when a covenant surcharge fires the statement re-syncs once more
    # without charging. So the swept figure is either -treasury exactly or
    # -treasury less the interest charged after the sync — nothing else.
    interest = float(diag.get("short_term_debt_interest_charged", 0.0) or 0.0)
    assert cash == pytest.approx(0.0, abs=0.01), f"R{rnd}: cash {cash} with negative treasury"
    ok = abs(std - (-treasury)) < 0.01 or abs(std - (-treasury - interest)) < 0.01
    assert ok, f"R{rnd}: swept {std} vs deficit {-treasury} (interest after sync {interest})"


def test_statement_cash_equals_persisted_treasury_every_round():
    async def go():
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            return await _play(ac)
    _sid, bodies = _run(go())
    for rnd, body in enumerate(bodies, start=1):
        _cash_matches_treasury(body, rnd)


def test_statement_follows_a_regulator_fine_in_the_same_round(monkeypatch):
    """Force what the NPC regulator does at enforcement: a treasury write inside
    run_new_engines, after the point where the statement used to be struck."""
    real = npc_stakeholders.process_npc_tick

    def fined(*a, **kw):
        out = real(*a, **kw)
        gs = kw.get("gs") if "gs" in kw else a[0]
        gs["corporate_treasury"] = round(float(gs.get("corporate_treasury", 0.0)) - 9_000_000.0, 2)
        return out

    monkeypatch.setattr(npc_stakeholders, "process_npc_tick", fined)

    async def go():
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            return await _play(ac, rounds=4)
    _sid, bodies = _run(go())
    for rnd, body in enumerate(bodies, start=1):
        _cash_matches_treasury(body, rnd)
