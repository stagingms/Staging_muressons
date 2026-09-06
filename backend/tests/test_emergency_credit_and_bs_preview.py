"""FIN-04 and FIN-05 (audit 2026-09-04, Wave 3).

FIN-04  GET /balance-sheet before the first commit ran a balance-sheet tick and
        PERSISTED it, so round 1 was depreciated twice and appeared twice in
        history — on every team, because every cockpit issues that GET on mount.
FIN-05  "Emergency credit" charged $140K/round of interest on a $1M line that
        was never credited, from a $25M server threshold the cockpit announced
        as $5M. It is now a real facility: drawn once into cash at the $5M
        trigger, interest on the outstanding balance, repaid when the treasury
        recovers or at round 10, on the balance sheet as a current liability,
        a ledger term in the conservation law and a waterfall entry.
"""
import copy
import os
import sys
from pathlib import Path

import pytest

_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))
os.environ.setdefault("USE_MEMORY_DB", "true")

from bu_profiles import build_bu_states  # noqa: E402
from engine import process_tick  # noqa: E402
from config import (FINANCIAL_EMERGENCY_CREDIT_AMOUNT, FINANCIAL_EMERGENCY_RATE_SPREAD,  # noqa: E402
                    FINANCIAL_DEFAULT_LOAN_RATE, CSF_POOL_TREASURY_FRACTION)


def _gs(treasury, round_number=3, **flags):
    return {
        "round_number": round_number, "corporate_treasury": float(treasury), "group_reputation": 60.0,
        "synergy_multiplier": 0.35, "cost_of_capital": 0.05,
        "active_event_flags": {"stochastic_seed": "fin05", **flags},
        "historical_ebitda": 0, "tco2e_emissions": 0, "green_transition_fund": 0,
        "tipping_point_active": False, "workforce_readiness": 50.0, "momentum_history": [],
        "pending_capex_projects": [], "inflation_index": 0.025,
        "pedagogical_overrides": {"black_swan_events_enabled": False, "decision_timer_enabled": False},
    }


def _tick(gs, bus, emergency, capex=1.0):
    decisions = [{"bu_id": b["bu_id"], "investment_ratio": 0.0, "capex_allocated": capex,
                  "choice_selected": "option_b"} for b in bus]
    return process_tick(current_global=copy.deepcopy(gs), current_bus=copy.deepcopy(bus), decisions=decisions,
                        dividends_paid=0, crisis_severity=40.0, imitation_decay_rate=0.05,
                        decision_paradigm="legacy_abc", emergency_credit_used=emergency)


def _entries(out):
    return {e["label"]: e["amount"] for e in out["events"]["consequence_waterfall"]["entries"]}


def test_the_line_is_drawn_into_cash_once_and_carried_as_a_stock():
    bus = build_bu_states()
    off = _tick(_gs(3_000_000), bus, emergency=False)
    on = _tick(_gs(3_000_000), bus, emergency=True)
    ev = on["events"]
    assert ev["emergency_credit_drawn"] == FINANCIAL_EMERGENCY_CREDIT_AMOUNT
    assert ev["emergency_credit_balance"] == FINANCIAL_EMERGENCY_CREDIT_AMOUNT
    assert ev["emergency_credit_interest"] == 0.0             # nothing was outstanding at the start of the round
    # the cash arrived — the only difference between the two ticks is the draw
    assert on["global_state"]["corporate_treasury"] - off["global_state"]["corporate_treasury"] == pytest.approx(FINANCIAL_EMERGENCY_CREDIT_AMOUNT, abs=0.01)
    assert _entries(on)["Emergency credit drawn"] == FINANCIAL_EMERGENCY_CREDIT_AMOUNT
    assert "Emergency Credit Interest" not in _entries(on)
    # a second round with the line outstanding: interest on the balance, no second draw
    gs2 = _gs(3_500_000, round_number=4, emergency_credit_balance=FINANCIAL_EMERGENCY_CREDIT_AMOUNT)
    nxt = _tick(gs2, bus, emergency=True)
    rate = FINANCIAL_DEFAULT_LOAN_RATE + FINANCIAL_EMERGENCY_RATE_SPREAD
    assert nxt["events"]["emergency_credit_interest"] == pytest.approx(FINANCIAL_EMERGENCY_CREDIT_AMOUNT * rate, abs=0.01)
    assert nxt["events"].get("emergency_credit_drawn", 0.0) == 0.0
    assert nxt["events"]["emergency_credit_balance"] in (FINANCIAL_EMERGENCY_CREDIT_AMOUNT, 0.0)
    assert _entries(nxt)["Emergency Credit Interest"] == pytest.approx(-FINANCIAL_EMERGENCY_CREDIT_AMOUNT * rate, abs=0.01)


def test_the_line_is_repaid_when_the_treasury_can_clear_the_trigger_or_at_round_ten():
    bus = build_bu_states()
    trigger = FINANCIAL_EMERGENCY_CREDIT_AMOUNT / CSF_POOL_TREASURY_FRACTION
    # a recovered treasury: repaid in full this round
    rich = _tick(_gs(40_000_000, round_number=5, emergency_credit_balance=FINANCIAL_EMERGENCY_CREDIT_AMOUNT), bus, emergency=False)
    assert rich["events"]["emergency_credit_repaid"] == FINANCIAL_EMERGENCY_CREDIT_AMOUNT
    assert rich["events"]["emergency_credit_balance"] == 0.0
    assert _entries(rich)["Emergency credit repaid"] == -FINANCIAL_EMERGENCY_CREDIT_AMOUNT
    assert rich["global_state"]["corporate_treasury"] >= trigger
    # still poor (zero-margin BUs, so gross profit does not lift the treasury): carried, not repaid
    flat = copy.deepcopy(bus)
    for b in flat:
        b["opex_base"] = b["revenue_base"]
    poor = _tick(_gs(2_000_000, round_number=5, emergency_credit_balance=FINANCIAL_EMERGENCY_CREDIT_AMOUNT), flat, emergency=True)
    assert poor["events"].get("emergency_credit_repaid", 0.0) == 0.0
    assert poor["events"]["emergency_credit_balance"] == FINANCIAL_EMERGENCY_CREDIT_AMOUNT
    # round 10: nothing outlives the game
    last = _tick(_gs(2_000_000, round_number=10, emergency_credit_balance=FINANCIAL_EMERGENCY_CREDIT_AMOUNT), flat, emergency=True)
    assert last["events"]["emergency_credit_repaid"] == FINANCIAL_EMERGENCY_CREDIT_AMOUNT
    assert last["events"]["emergency_credit_balance"] == 0.0


def test_no_interest_without_a_balance_and_the_waterfall_closes():
    bus = build_bu_states()
    out = _tick(_gs(20_000_000), bus, emergency=False)
    assert "emergency_credit_interest" not in out["events"]
    assert "Emergency Credit Interest" not in _entries(out)
    for o in (out, _tick(_gs(3_000_000), bus, emergency=True)):
        wf = o["events"]["consequence_waterfall"]
        assert wf["unattributed"] == 0.0
        assert wf["initial_treasury"] + sum(e["amount"] for e in wf["entries"]) == pytest.approx(wf["final_treasury"], abs=0.05)


def test_the_conservation_law_carries_the_draw_and_the_repayment():
    import inspect
    import test_treasury_waterfall as T
    src = inspect.getsource(T._residual)
    assert "+ ledger.emergency_credit_drawn" in src and "- ledger.emergency_credit_repaid" in src


# ── the router: trigger and the balance sheet ─────────────────────────────────

@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from main import app
    import admin_shared
    admin_shared._god_mode_settings["solo_mode_enabled"] = True
    with TestClient(app) as c:
        yield c


def test_the_server_trigger_is_the_one_the_cockpit_announces():
    import inspect, router
    src = inspect.getsource(router._commit_turn_impl)
    line = src.split("_server_emergency = ")[1].split("\n")[0]
    assert "_cfg.FINANCIAL_EMERGENCY_CREDIT_AMOUNT" in line
    assert "CSF_POOL_FLOOR" not in line


def test_a_drawn_line_is_a_current_liability_on_the_statement(client):
    """Play with a treasury forced under the trigger: the line is drawn, sits in
    current_liabilities.emergency_credit_line, and feeds the equity bridge."""
    from router import _commit_timestamps
    import database as db
    import anyio
    r = client.post("/api/simulations/solo-start", json={"player_name": "EC", "decision_paradigm": "legacy_abc"})
    sid = r.json()["session_id"]

    async def impoverish():
        latest = await db.fetch_latest_state(sid)
        gs = latest["global_state"]; gs["corporate_treasury"] = 2_000_000.0
        await db.update_latest_global_state(sid, gs, latest["bu_states"])
    anyio.run(impoverish)
    bus = client.get(f"/api/simulations/{sid}/dashboard").json()["business_units"]
    _commit_timestamps.pop(sid, None)
    res = client.post(f"/api/simulations/{sid}/commit-turn", json={
        "decisions": [{"bu_id": b["bu_id"], "investment_ratio": 0.0, "capex_allocated": 1.0, "choice_selected": "option_b"} for b in bus],
        "force_override_cfo": True, "expected_round": 1})
    assert res.status_code == 201, res.text[:300]
    ev = res.json()["events"]
    assert ev["emergency_credit_used"] is True and ev["emergency_credit_drawn"] == FINANCIAL_EMERGENCY_CREDIT_AMOUNT
    bs = res.json()["global_state"]["balance_sheet"]
    assert bs["current_liabilities"]["emergency_credit_line"] == FINANCIAL_EMERGENCY_CREDIT_AMOUNT
    flags = res.json()["global_state"]["active_event_flags"]
    assert flags["emergency_credit_balance"] == FINANCIAL_EMERGENCY_CREDIT_AMOUNT


# ── FIN-04 ────────────────────────────────────────────────────────────────────

def test_a_pre_commit_balance_sheet_get_is_a_preview_and_persists_nothing(client):
    from router import _commit_timestamps
    import database as db
    import anyio
    r = client.post("/api/simulations/solo-start", json={"player_name": "BS", "decision_paradigm": "legacy_abc"})
    sid = r.json()["session_id"]
    g = client.get(f"/api/simulations/{sid}/balance-sheet")
    assert g.status_code == 200
    body = g.json()
    assert body["preview"] is True and body["balance_sheet"].get("total_assets")
    # nothing was written
    async def persisted():
        latest = await db.fetch_latest_state(sid)
        return latest["global_state"].get("balance_sheet")
    assert not (anyio.run(persisted) or {}).get("total_assets")
    # the R1 commit then produces ONE round-1 statement
    bus = client.get(f"/api/simulations/{sid}/dashboard").json()["business_units"]
    _commit_timestamps.pop(sid, None)
    res = client.post(f"/api/simulations/{sid}/commit-turn", json={
        "decisions": [{"bu_id": b["bu_id"], "investment_ratio": 0.1, "capex_allocated": 500_000, "choice_selected": "option_a"} for b in bus],
        "force_override_cfo": True, "expected_round": 1})
    assert res.status_code == 201
    hist = res.json()["global_state"]["balance_sheet"]["balance_sheet_history"]
    assert [h["round"] for h in hist] == [1]
    # and the GET after a commit serves the persisted statement, not a preview
    g2 = client.get(f"/api/simulations/{sid}/balance-sheet").json()
    assert g2["preview"] is False and [h["round"] for h in g2["balance_sheet"]["balance_sheet_history"]] == [1]
