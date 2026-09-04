"""The CapEx term loan reaches the balance sheet and the P&L the participant
sees — audit 2026-09-04 F-12 / WP-11.

F-05 (launch audit) made CapEx above the 20% allowance a term loan carried in
active_event_flags.capex_loan_balance, charged interest and repaid by R10. The
engine emits capex_loan_balance / loan_interest_payment every tick and
balance_sheet.py READS both from its `events` argument — but round_logic built
that argument as a seven-key dict that never carried them. The ledger showed
PPE financed by nothing, no "CapEx Term Loan" row existed on either statement,
and the P&L priced no interest on the loan. tests/test_launch_audit
::test_balance_sheet_shows_the_term_loan passed the engine dict straight to
the function and so never saw the wiring.

This file goes through the ROUTER: a solo game, a commit whose CapEx exceeds
the allowance, then GET /balance-sheet.
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


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _commit(ac, sid, bus, rnd, capex_per_bu):
    _router._commit_timestamps.pop(sid, None)
    r = await ac.post(f"/api/simulations/{sid}/commit-turn", json={
        "decisions": [{"bu_id": b["bu_id"], "investment_ratio": 0.2, "capex_allocated": capex_per_bu,
                       "choice_selected": "option_b"} for b in bus],
        "force_override_cfo": True, "expected_round": rnd})
    assert r.status_code == 201, f"R{rnd}: {r.status_code} {r.text[:300]}"
    return r.json()


async def _game_with_loan():
    # module-scoped: runs before conftest's per-test solo enable
    import admin_shared
    admin_shared._god_mode_settings["solo_mode_enabled"] = True
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
        r = await ac.post("/api/simulations/solo-start",
                          json={"player_name": "Loan", "decision_paradigm": "legacy_abc"})
        assert r.status_code in (200, 201), r.text[:300]
        sid = r.json()["session_id"]
        dash = (await ac.get(f"/api/simulations/{sid}/dashboard")).json()
        bus = dash["business_units"]
        treasury = dash["global_state"]["corporate_treasury"]
        # well above the 20%-of-treasury allowance → a term loan is drawn
        per_bu = round(treasury * 0.5 / len(bus))
        r1 = await _commit(ac, sid, bus, 1, per_bu)
        bs1 = (await ac.get(f"/api/simulations/{sid}/balance-sheet")).json()["balance_sheet"]
        # a light second round: the loan is still outstanding and interest is charged
        r2 = await _commit(ac, sid, r1.get("business_units") or bus, 2, 1)
        bs2 = (await ac.get(f"/api/simulations/{sid}/balance-sheet")).json()["balance_sheet"]
        return r1, bs1, r2, bs2


@pytest.fixture(scope="module")
def game():
    return _run(_game_with_loan())


def test_the_loan_the_engine_drew_is_on_the_balance_sheet(game):
    r1, bs1, _, _ = game
    ev = r1["events"]
    assert ev.get("capex_loan_drawn", 0) > 0, "precondition: CapEx above the allowance draws a loan"
    assert ev["capex_loan_balance"] > 0
    assert bs1["non_current_liabilities"].get("capex_term_loan", 0) == pytest.approx(ev["capex_loan_balance"], abs=0.01), \
        "the term loan the engine carries is not on the statement"
    # and it is inside the totals the covenant test reads
    assert bs1["total_liabilities"] >= bs1["non_current_liabilities"]["capex_term_loan"]


def test_the_statement_prices_the_loan_interest_the_engine_charged(game):
    _, _, r2, bs2 = game
    ev = r2["events"]
    assert ev.get("loan_interest_payment", 0) > 0, "precondition: interest on the opening balance in R2"
    inc = ev["balance_sheet"]["income_statement"]
    # interest_expense = other debt at WACC/2 + decommissioning accretion + the loan interest
    other = bs2["non_current_liabilities"]["revolving_credit_facility"] + bs2["non_current_liabilities"]["green_bonds_outstanding"] \
        + bs2["current_liabilities"]["short_term_debt"]
    assert inc["interest_expense"] >= ev["loan_interest_payment"], "the P&L does not carry the loan's interest"
    assert inc["interest_expense"] - ev["loan_interest_payment"] < other * 0.5 + 1, "interest is over-counted"
    # the ledger's loan balance follows the engine's closing stock after repayment
    assert bs2["non_current_liabilities"]["capex_term_loan"] == pytest.approx(ev["capex_loan_balance"], abs=0.01)
    assert ev["capex_loan_balance"] < r2["events"].get("capex_loan_opening", ev["capex_loan_balance"] + 1)


def test_bs_events_forwards_the_loan_keys():
    """Source pin: the dict round_logic hands the ledger carries both keys."""
    import inspect
    import round_logic
    src = inspect.getsource(round_logic.run_new_engines)
    i = src.index("bs_events = {")
    block = src[i:i + 2500]
    assert '"capex_loan_balance"' in block and '"loan_interest_payment"' in block


def test_a_state_without_an_engine_event_falls_back_to_the_persisted_flag():
    from round_logic import _capex_loan_for_statement
    assert _capex_loan_for_statement({"capex_loan_balance": 0.0}, {"active_event_flags": {"capex_loan_balance": 5e6}}) == 0.0
    assert _capex_loan_for_statement({}, {"active_event_flags": {"capex_loan_balance": 5e6}}) == 5e6
    assert _capex_loan_for_statement({}, {}) == 0.0


def test_the_financial_golden_trace_carries_no_loan():
    """The golden trace invests inside the allowance, so this fix must not
    move it — assert the premise rather than trust it."""
    import json
    golden = _BACKEND_DIR / "tests" / "golden"
    files = list(golden.glob("*financial*")) + list(golden.glob("*trace*"))
    assert files, f"no golden trace under {golden}"
    for f in files:
        if f.suffix != ".json":
            continue
        txt = f.read_text(encoding="utf-8")
        data = json.loads(txt)
        s = json.dumps(data)
        assert '"capex_loan_drawn": 0' in s or "capex_loan_drawn" not in s or '"capex_loan_balance": 0' in s, f.name
