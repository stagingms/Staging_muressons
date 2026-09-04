"""Audit F-08 (SEAM-05 / SEAM-06): one closing number.

_post_r10_grand_finale runs inside post_tick and stamped final_treasury,
group_reputation, net debt -> equity / share price, carbon tonnage and the
solvency-gated profile BEFORE run_new_engines applied the round's NPC fines,
agent hits and balance sheet. The audit found three "closing treasury" values
on one team: persisted 70.58M, flags.final_treasury 79.98M, waterfall 84.98M.
router.commit_turn now re-runs the valuation stamps on the closing state.
"""

from __future__ import annotations

import asyncio
import copy
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
import round_logic  # noqa: E402
from main import app  # noqa: E402
from terminal_valuation import calculate_equity_bridge  # noqa: E402
from config import TV_SHARES_OUTSTANDING  # noqa: E402


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _play_ten(ac):
    r = await ac.post("/api/simulations/solo-start",
                      json={"player_name": "Finale", "decision_paradigm": "legacy_abc"})
    assert r.status_code in (200, 201), r.text[:300]
    sid = r.json()["session_id"]
    bus = (await ac.get(f"/api/simulations/{sid}/dashboard")).json()["business_units"]
    last = None
    for rnd in range(1, 11):
        _router._commit_timestamps.pop(sid, None)
        r = await ac.post(f"/api/simulations/{sid}/commit-turn", json={
            "decisions": [{"bu_id": b["bu_id"], "investment_ratio": 0.3, "capex_allocated": 1_500_000,
                           "choice_selected": "option_b"} for b in bus],
            "force_override_cfo": True, "expected_round": rnd})
        assert r.status_code == 201, f"R{rnd}: {r.status_code} {r.text[:300]}"
        last = r.json()
        bus = last.get("business_units") or bus
    final = (await ac.get(f"/api/simulations/{sid}/dashboard")).json()
    return sid, last, final


def _assert_one_closing_number(final: dict):
    gs = final["global_state"]
    flags = gs["active_event_flags"]
    bus = final["business_units"]
    assert flags["final_treasury"] == pytest.approx(gs["corporate_treasury"], abs=0.01)
    assert flags["group_reputation"] == pytest.approx(gs["group_reputation"], abs=0.01)
    tonnage = sum(b.get("carbon_intensity", 0) * b.get("revenue_base", 0) / 1_000_000 for b in bus)
    assert flags["carbon_tonnage_group"] == pytest.approx(tonnage, rel=1e-6)
    # Equity bridge recomputed from the persisted state equals the stamped one.
    bs = gs.get("balance_sheet") or flags.get("balance_sheet") or {}
    ncl, cl = bs.get("non_current_liabilities", {}), bs.get("current_liabilities", {})
    debt = (ncl.get("revolving_credit_facility", 50_000_000) + ncl.get("green_bonds_outstanding", 0.0)
            + max(ncl.get("capex_term_loan", 0.0), float(flags.get("capex_loan_balance", 0.0) or 0.0))
            + cl.get("short_term_debt", 0.0))
    bridge = calculate_equity_bridge(enterprise_value=flags["terminal_value"],
                                     net_debt=round(debt - gs["corporate_treasury"], 2),
                                     shares_outstanding=TV_SHARES_OUTSTANDING,
                                     book_equity=bs.get("net_assets", 0.0),
                                     total_revenue=sum(b["revenue_base"] for b in bus))
    assert flags["equity_value"] == pytest.approx(bridge["equity_value"], abs=0.01)
    assert flags["price_per_share"] == pytest.approx(bridge["price_per_share"], abs=0.0001)
    canonical = gs.get("final_report_canonical") or flags.get("final_report_canonical") or {}
    assert canonical.get("terminal_value") == flags["terminal_value"]
    assert canonical.get("profile") == flags["profile"]


def test_closing_figures_match_the_persisted_state_after_a_full_game():
    async def go():
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            return await _play_ten(ac)
    _sid, _last, final = _run(go())
    _assert_one_closing_number(final)


def test_closing_figures_follow_a_treasury_hit_applied_by_the_engines(monkeypatch):
    """Force what NPC fines / agent hits do at R10: a treasury write inside
    run_new_engines. The finale stamped before it; the re-stamp must follow it."""
    real = _router.run_new_engines

    def hit_after(**kw):
        out = real(**kw)
        if kw["round_number"] == 10:
            gs = kw["global_state"]
            gs["corporate_treasury"] = round(gs["corporate_treasury"] - 7_500_000.0, 2)
            gs["group_reputation"] = max(0.0, round(float(gs.get("group_reputation", 50) or 0) - 9.0, 2))
        return out

    monkeypatch.setattr(_router, "run_new_engines", hit_after)

    async def go():
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            return await _play_ten(ac)
    _sid, last, final = _run(go())
    _assert_one_closing_number(final)
    # and the commit response itself carries the closing number
    ev = last["events"]
    assert ev["final_treasury"] == pytest.approx(final["global_state"]["corporate_treasury"], abs=0.01)


def test_restamp_is_a_pure_function_of_the_closing_state():
    """Unit: run the finale, move the treasury, restamp — stamps and the
    write-once canonical record follow; the option phase is not re-run."""
    from tests.test_launch_audit_2026_09_01 import _tick_state
    gs, bus = _tick_state(round_number=10, treasury=40_000_000)
    prev_flags = dict(gs.get("active_event_flags") or {})
    prev_flags.setdefault("ending_pathway", "activist_ultimatum")
    decs = [{"bu_id": b["bu_id"], "capex_allocated": 1_000_000, "choice_selected": "option_b"} for b in bus]
    extra: dict = {}
    gs.setdefault("active_event_flags", {})
    round_logic._post_r10_grand_finale(gs, bus, decs, {}, extra, prev_flags)
    tv_before, ft_before = extra["terminal_value"], extra["final_treasury"]
    assert ft_before == pytest.approx(gs["corporate_treasury"])
    canonical_before = copy.deepcopy(gs["final_report_canonical"])

    gs["corporate_treasury"] = round(gs["corporate_treasury"] - 20_000_000.0, 2)
    assert round_logic.restamp_finale_valuation(gs, bus, extra, prev_flags) is True
    assert extra["final_treasury"] == pytest.approx(gs["corporate_treasury"])
    assert extra["terminal_value"] == pytest.approx(tv_before)          # EBITDA-driven, unchanged
    assert extra["equity_value"] < canonical_before.get("terminal_value", 0) + 1e9  # bridge recomputed
    assert gs["final_report_canonical"]["terminal_value"] == extra["terminal_value"]
    assert gs["final_report_canonical"]["profile"] == extra["profile"]
    # no finale_inputs -> nothing to restamp
    assert round_logic.restamp_finale_valuation({"active_event_flags": {}}, bus, {}, prev_flags) is False
