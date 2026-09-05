"""One price for a negative treasury; the floor holds where treasury is
written — audit 2026-09-04 F-13 / FIN-10 · WP-12.

F-13  A negative treasury was charged interest twice per round by independent
      code paths: engine.py's debt service (cost of capital on the deficit,
      on the waterfall as "Debt Service Interest") and balance_sheet.py's
      _sweep_negative_cash (half-year revolver interest on the same deficit,
      invisible — no surface read short_term_debt_interest_charged), plus the
      covenant surcharge when breached: ≈22–33% of the deficit per round.
      Once negative, recovery was arithmetically impossible.
FIN-10 FINANCIAL_TREASURY_FLOOR was enforced only inside process_tick; NPC
      fines, agent hits, impact and biodiversity charges wrote treasury
      afterwards, so a healthcare cohort closed at −$538M against a −$460M
      floor. The talent brain-drain multiplier (×2.975 per round at
      reputation 0 + burnout 100) was the amplifier.

Calibration calls, stated: the deficit is priced ONCE, at the engine's rate
(corporate cost of capital per round — the rate itself is a Wave-2 topic);
the brain-drain premium is capped at +30% of OPEX per round.
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
from config import FINANCIAL_TREASURY_FLOOR, BRAINDRAIN_PENALTY_CAP  # noqa: E402
from main import app  # noqa: E402


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _play(ac, rounds, capex=1_500_000, ratio=0.3):
    import admin_shared
    admin_shared._god_mode_settings["solo_mode_enabled"] = True
    r = await ac.post("/api/simulations/solo-start",
                      json={"player_name": "Floor", "decision_paradigm": "legacy_abc"})
    assert r.status_code in (200, 201), r.text[:300]
    sid = r.json()["session_id"]
    bus = (await ac.get(f"/api/simulations/{sid}/dashboard")).json()["business_units"]
    bodies = []
    for rnd in range(1, rounds + 1):
        _router._commit_timestamps.pop(sid, None)
        r = await ac.post(f"/api/simulations/{sid}/commit-turn", json={
            "decisions": [{"bu_id": b["bu_id"], "investment_ratio": ratio, "capex_allocated": capex,
                           "choice_selected": "option_b"} for b in bus],
            "force_override_cfo": True, "expected_round": rnd})
        assert r.status_code == 201, f"R{rnd}: {r.status_code} {r.text[:300]}"
        body = r.json()
        bodies.append(body)
        bus = body.get("business_units") or bus
    return sid, bodies


# ── F-13: one price ────────────────────────────────────────────────────────

def test_the_sweep_reclassifies_but_no_longer_prices_the_deficit():
    from balance_sheet import _sweep_negative_cash, create_initial_balance_sheet
    bs = create_initial_balance_sheet([{"bu_id": "pharma", "revenue_base": 2e7, "opex_base": 1.2e7}])
    bs["current_assets"]["cash_and_equivalents"] = -19_260_000.0
    gs = {"corporate_treasury": -19_260_000.0, "active_event_flags": {"loan_interest_rate": 0.12}}
    diag = {}
    _sweep_negative_cash(bs, gs, diag, charge_interest=False)
    assert bs["current_liabilities"]["short_term_debt"] == 19_260_000.0
    assert bs["current_assets"]["cash_and_equivalents"] == 0.0
    assert gs["corporate_treasury"] == -19_260_000.0, "the sweep charged the treasury"
    assert "short_term_debt_interest_charged" not in diag


def test_process_balance_sheet_tick_charges_nothing_on_a_deficit():
    """The production call site: process_balance_sheet_tick on a negative
    treasury leaves the treasury exactly where the engine put it (only a
    covenant surcharge — its own, disclosed mechanic — may move it)."""
    from balance_sheet import create_initial_balance_sheet, process_balance_sheet_tick
    bus = [{"bu_id": "pharma", "revenue_base": 2e7, "opex_base": 1.2e7, "governance_risk_score": 20,
            "social_license_score": 55, "natural_capital_debt": 50, "carbon_intensity": 35}]
    gs = {"corporate_treasury": -19_260_000.0, "group_reputation": 40, "cost_of_capital": 0.05,
          "active_event_flags": {"loan_interest_rate": 0.12}, "round_number": 6}
    bs = create_initial_balance_sheet(bus)
    _, diag = process_balance_sheet_tick(bs, gs, bus, {"csf_this_round": 0, "total_capex_allocated": 0,
                                                       "dividends_paid": 0, "remediation_events": [],
                                                       "tipping_tier": "none"}, 6)
    assert "short_term_debt_interest_charged" not in diag
    surcharge = float((diag.get("covenants") or {}).get("treasury_surcharge", 0.0) or 0.0)
    assert gs["corporate_treasury"] == pytest.approx(-19_260_000.0 - surcharge, abs=0.01)


def test_a_negative_round_carries_exactly_one_interest_line_through_the_router(monkeypatch):
    """Drive a team negative with a regulator-shaped hit inside run_new_engines,
    then read the next round: the engine's debt service prices the deficit
    once and the statement diag shows no revolver charge."""
    real = npc_stakeholders.process_npc_tick
    hits = {"n": 0}

    def hit(*a, **kw):
        out = real(*a, **kw)
        gs = kw.get("gs") if "gs" in kw else a[1]  # process_npc_tick(npc_state, gs, bus, …)
        if hits["n"] == 0:
            gs["corporate_treasury"] = round(float(gs.get("corporate_treasury", 0.0)) - 90_000_000.0, 2)
        hits["n"] += 1
        return out

    monkeypatch.setattr(npc_stakeholders, "process_npc_tick", hit)

    async def go():
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
            return await _play(ac, 2)
    _sid, bodies = _run(go())
    r1, r2 = bodies[0], bodies[1]
    assert r1["global_state"]["corporate_treasury"] < 0, "precondition: the hit made the treasury negative"
    ev2 = r2["events"]
    assert ev2.get("negative_treasury_interest_applied", 0) > 0, "the engine's debt service did not price the deficit"
    wf = ev2.get("consequence_waterfall") or {}
    steps = wf.get("steps") or wf.get("lines") or wf.get("items") or []
    lines = [s for s in steps if "Debt Service" in str(s)]
    assert len(lines) <= 1, f"more than one debt-service line on the waterfall: {lines}"
    bs_diag = ev2.get("balance_sheet") or {}
    assert "short_term_debt_interest_charged" not in bs_diag, "the revolver priced the deficit a second time"


# ── FIN-10: the floor after the engines ────────────────────────────────────

def test_a_post_tick_charge_cannot_breach_the_floor(monkeypatch):
    real = npc_stakeholders.process_npc_tick

    def catastrophic(*a, **kw):
        out = real(*a, **kw)
        gs = kw.get("gs") if "gs" in kw else a[1]  # process_npc_tick(npc_state, gs, bus, …)
        gs["corporate_treasury"] = round(float(gs.get("corporate_treasury", 0.0)) - 2_000_000_000.0, 2)
        return out

    monkeypatch.setattr(npc_stakeholders, "process_npc_tick", catastrophic)

    async def go():
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
            return await _play(ac, 1)
    _sid, bodies = _run(go())
    body = bodies[0]
    gs = body["global_state"]
    ev = body["events"]
    floor = float(ev.get("treasury_floor_effective", FINANCIAL_TREASURY_FLOOR))
    assert floor >= FINANCIAL_TREASURY_FLOOR
    assert gs["corporate_treasury"] == pytest.approx(floor, abs=0.01), \
        f"persisted treasury {gs['corporate_treasury']} breached the floor {floor}"
    assert ev.get("treasury_floor_clamp_post_tick", 0) > 1_000_000_000
    assert ev["treasury_floor_clamp_applied"] >= ev["treasury_floor_clamp_post_tick"]
    assert "floor" in ev.get("treasury_floor_clamp_because", "").lower()
    # the statement was struck AFTER the clamp: it articulates to the floored treasury
    bs = gs.get("balance_sheet") or (gs.get("active_event_flags") or {}).get("balance_sheet")
    assert bs["current_liabilities"]["short_term_debt"] == pytest.approx(-floor, abs=0.01)
    assert bs["current_assets"]["cash_and_equivalents"] == 0.0


def test_the_engine_publishes_the_floor_it_used():
    """The post-tick clamp must enforce the same number process_tick did."""
    from tests.test_launch_audit_2026_09_01 import _tick_state, _tick
    gs, bus = _tick_state()
    res = _tick(gs, bus, capex=1_000_000, ratio=0.3)
    ev = res["events"]
    assert "treasury_floor_effective" in ev
    assert ev["treasury_floor_effective"] == pytest.approx(
        FINANCIAL_TREASURY_FLOOR + float(ev.get("_pre_austerity_avg_invest", 0)) * 200_000_000, abs=1.0)


# ── FIN-10: the amplifier is capped ────────────────────────────────────────

def test_brain_drain_premium_is_capped():
    from engine import calc_talent_braindrain
    assert BRAINDRAIN_PENALTY_CAP == pytest.approx(1.30)
    opex, pen = calc_talent_braindrain(10_000_000.0, group_reputation=0.0, burnout_index=100.0)
    assert pen == pytest.approx(1.30) and opex == pytest.approx(13_000_000.0)
    opex, pen = calc_talent_braindrain(10_000_000.0, group_reputation=55.0, burnout_index=0.0)
    assert pen == pytest.approx(1.15) and opex == pytest.approx(11_500_000.0)
    _, pen = calc_talent_braindrain(10_000_000.0, group_reputation=80.0, burnout_index=0.0)
    assert pen == pytest.approx(1.0)


def test_floor_clamp_runs_before_the_statement_is_struck():
    """Source pin: the FIN-10 clamp precedes the SE-6 balance sheet block in
    run_new_engines, so statement cash still equals the persisted treasury."""
    import inspect
    import round_logic
    src = inspect.getsource(round_logic.run_new_engines)
    assert src.index("treasury_floor_clamp_post_tick") < src.index("SE-6: Balance Sheet Engine")
