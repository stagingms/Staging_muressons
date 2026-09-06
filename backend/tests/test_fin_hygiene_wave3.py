"""FIN-07, FIN-11, FIN-12, FIN-13 (audit 2026-09-04, Wave 3).

FIN-07  Retained earnings is the plug that balances the statement, but the
        diagnostics said `balance_sheet_balanced: True` unconditionally and the
        UI printed Net Income beside an RE figure it does not explain. The
        identity is now CHECKED, and the RE roll-forward residual
        (RE_close − [RE_open + NI − dividends]) is reported on the statement,
        the history row and the diagnostics, with RE named as the closing
        residual.
FIN-11  Every session was created with loan_interest_rate=0.12 (a literal in the
        solo start, the /start model and three fallbacks), so an Excel edit of
        financial_parameters.default_loan_rate never reached a real session.
FIN-12  The router overwrote the engine's clamped `dividends_paid` with the
        REQUESTED amount, so the statement showed $5M distributed when $1M left
        the bank.
FIN-13  "CapEx capped at 50%, dividend suspension in effect" had no reader; a
        round-10 term-loan draw was interest-free and never repaid.
"""
import copy
import os
import sys
from pathlib import Path

import pytest

_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))
os.environ.setdefault("USE_MEMORY_DB", "true")

import config  # noqa: E402
from bu_profiles import build_bu_states  # noqa: E402
from engine import process_tick  # noqa: E402
from config import (FINANCIAL_DEFAULT_LOAN_RATE, FINANCIAL_FREE_CSF_PCT, CSF_POOL_FLOOR,  # noqa: E402
                    FINANCIAL_CAPEX_CAP_MULTIPLE)


def _gs(treasury, round_number=3, **flags):
    return {
        "round_number": round_number, "corporate_treasury": float(treasury), "group_reputation": 60.0,
        "synergy_multiplier": 0.35, "cost_of_capital": 0.05,
        "active_event_flags": {"stochastic_seed": "fin13", **flags},
        "historical_ebitda": 0, "tco2e_emissions": 0, "green_transition_fund": 0,
        "tipping_point_active": False, "workforce_readiness": 50.0, "momentum_history": [],
        "pending_capex_projects": [], "inflation_index": 0.025,
        "pedagogical_overrides": {"black_swan_events_enabled": False, "decision_timer_enabled": False},
    }


def _tick(gs, bus, capex=1.0, dividends=0.0):
    decisions = [{"bu_id": b["bu_id"], "investment_ratio": 0.0, "capex_allocated": capex,
                  "choice_selected": "option_b"} for b in bus]
    return process_tick(current_global=copy.deepcopy(gs), current_bus=copy.deepcopy(bus), decisions=decisions,
                        dividends_paid=dividends, crisis_severity=40.0, imitation_decay_rate=0.05,
                        decision_paradigm="legacy_abc", emergency_credit_used=False)


# ── FIN-07 ────────────────────────────────────────────────────────────────────

def _bs_tick(dividends=0.0):
    from balance_sheet import create_initial_balance_sheet, process_balance_sheet_tick
    bus = build_bu_states()
    gs = _gs(50_000_000, round_number=2)
    res = _tick(gs, bus, capex=2_000_000, dividends=dividends)
    gs2 = res["global_state"]
    gs2["active_event_flags"] = {**gs2.get("active_event_flags", {}), **res["events"]}
    bs = create_initial_balance_sheet(bus)
    re_open = bs["retained_earnings"]
    events = {"csf_this_round": res["events"].get("csf_delta", 0), "total_capex_allocated": 2_000_000 * len(bus),
              "dividends_paid": res["events"].get("dividends_paid", dividends), "remediation_events": [],
              "tipping_tier": "none"}
    bs, diag = process_balance_sheet_tick(bs, gs2, res["bu_states"], events, 2)
    return bs, diag, re_open, events["dividends_paid"]


def test_the_re_bridge_is_reported_and_names_the_plug():
    bs, diag, re_open, dividends = _bs_tick(dividends=500_000.0)
    br = bs["re_bridge"]
    ni = diag["income_statement"]["net_income"]
    assert br["opening"] == pytest.approx(re_open, abs=0.01)
    assert br["net_income"] == ni and br["dividends"] == dividends
    assert br["expected_closing"] == pytest.approx(re_open + ni - dividends, abs=0.01)
    assert br["closing"] == bs["retained_earnings"]
    assert br["residual"] == pytest.approx(bs["retained_earnings"] - (re_open + ni - dividends), abs=0.01)
    assert br["articulates"] == (abs(br["residual"]) < 0.01)
    assert "closing residual" in br["note"] and "does not roll forward" in br["note"]
    # the diagnostics carry the same residual, and the history row does too
    assert diag["re_bridge_residual"] == br["residual"]
    assert diag["re_articulates"] == br["articulates"]
    assert bs["balance_sheet_history"][-1]["re_bridge_residual"] == br["residual"]


def test_balanced_is_checked_not_asserted():
    import inspect
    import balance_sheet
    src = inspect.getsource(balance_sheet.process_balance_sheet_tick)
    assert 'diagnostics["balance_sheet_balanced"] = True' not in src
    assert 'diagnostics["imbalance"]              = 0.0' not in src
    bs, diag, _, _ = _bs_tick()
    fixed_equity = bs["total_assets"] - bs["total_liabilities"] - bs["retained_earnings"]
    gap = bs["total_assets"] - bs["total_liabilities"] - (fixed_equity + bs["retained_earnings"])
    assert diag["imbalance"] == pytest.approx(gap, abs=0.01)
    assert diag["balance_sheet_balanced"] is (abs(diag["imbalance"]) < 0.01)
    assert diag["balance_sheet_balanced"] is True   # it holds — because RE is derived; now that is checked


# ── FIN-11 ────────────────────────────────────────────────────────────────────

def test_the_start_model_default_is_the_config_rate(monkeypatch):
    from models import StartSessionRequest
    assert StartSessionRequest(cohort_name="c").loan_interest_rate == config.FINANCIAL_DEFAULT_LOAN_RATE
    monkeypatch.setattr(config, "FINANCIAL_DEFAULT_LOAN_RATE", 0.2)
    assert StartSessionRequest(cohort_name="c").loan_interest_rate == 0.2


def test_no_fallback_hard_codes_twelve_percent():
    import inspect
    import balance_sheet, database, database_memory, router
    assert "0.12" not in inspect.getsource(balance_sheet._sweep_negative_cash)
    assert "FINANCIAL_DEFAULT_LOAN_RATE" in inspect.getsource(balance_sheet._sweep_negative_cash)
    assert "loan_interest_rate=0.12" not in inspect.getsource(router.solo_start_simulation)
    assert "_cfg.FINANCIAL_DEFAULT_LOAN_RATE" in inspect.getsource(router.solo_start_simulation)
    for mod in (database, database_memory):
        src = inspect.getsource(mod.reset_session_to_round1)
        assert '"loan_interest_rate", 0.12)' not in src and "FINANCIAL_DEFAULT_LOAN_RATE" in src


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from main import app
    import admin_shared
    admin_shared._god_mode_settings["solo_mode_enabled"] = True
    with TestClient(app) as c:
        yield c


def test_a_solo_session_is_seeded_with_the_config_rate(client, monkeypatch):
    import database as db
    import anyio
    monkeypatch.setattr(config, "FINANCIAL_DEFAULT_LOAN_RATE", 0.17)
    r = client.post("/api/simulations/solo-start", json={"player_name": "LR", "decision_paradigm": "legacy_abc"})
    sid = r.json()["session_id"]
    latest = anyio.run(db.fetch_latest_state, sid)
    assert latest["global_state"]["active_event_flags"]["loan_interest_rate"] == 0.17


# ── FIN-12 ────────────────────────────────────────────────────────────────────

def test_the_statement_records_the_dividend_actually_paid(client):
    from router import _commit_timestamps
    import database as db
    import anyio
    r = client.post("/api/simulations/solo-start", json={"player_name": "DV", "decision_paradigm": "legacy_abc"})
    sid = r.json()["session_id"]

    async def impoverish():
        latest = await db.fetch_latest_state(sid)
        gs = latest["global_state"]; gs["corporate_treasury"] = 1_000_000.0
        await db.update_latest_global_state(sid, gs, latest["bu_states"])
    anyio.run(impoverish)
    bus = client.get(f"/api/simulations/{sid}/dashboard").json()["business_units"]
    _commit_timestamps.pop(sid, None)
    res = client.post(f"/api/simulations/{sid}/commit-turn", json={
        "decisions": [{"bu_id": b["bu_id"], "investment_ratio": 0.0, "capex_allocated": 1.0, "choice_selected": "option_b"} for b in bus],
        "dividends_paid": 5_000_000.0, "force_override_cfo": True, "expected_round": 1})
    assert res.status_code == 201, res.text[:300]
    ev = res.json()["events"]
    assert ev["dividends_clamped"] is True and ev["dividends_requested"] == 5_000_000.0
    assert ev["dividends_paid"] == 1_000_000.0                                      # the router kept the engine's figure
    assert ev["balance_sheet"]["income_statement"]["dividends_as_equity_distribution"] == 1_000_000.0
    hist = res.json()["global_state"]["balance_sheet"]["balance_sheet_history"]
    assert hist[-1]["dividends"] == 1_000_000.0
    assert ev["last_dividends_paid"] == 1_000_000.0
    # and an unclamped request still reaches the statement as requested
    _commit_timestamps.pop(sid, None)
    res2 = client.post(f"/api/simulations/{sid}/commit-turn", json={
        "decisions": [{"bu_id": b["bu_id"], "investment_ratio": 0.0, "capex_allocated": 1.0, "choice_selected": "option_b"} for b in bus],
        "dividends_paid": 250_000.0, "force_override_cfo": True, "expected_round": 2})
    assert res2.status_code == 201, res2.text[:300]
    assert res2.json()["events"]["dividends_paid"] == 250_000.0
    assert res2.json()["events"]["balance_sheet"]["income_statement"]["dividends_as_equity_distribution"] == 250_000.0


# ── FIN-13 ────────────────────────────────────────────────────────────────────

def _financed(ev):
    """What the round actually invested: the equity-funded part plus the loan draw."""
    return ev["capex_equity_funded"] + ev["capex_loan_drawn"]


def _requested(ev, per_bu, n):
    """The request as the cap sees it: the decisions plus a seeded execution overrun, if one fired."""
    return per_bu * n + float(ev.get("capex_overrun_amount", 0.0) or 0.0)


def test_the_insolvency_notice_caps_capex_and_suspends_the_dividend_next_round():
    bus = build_bu_states()
    treasury = 1_000_000.0
    base_cap = max(CSF_POOL_FLOOR, treasury * FINANCIAL_CAPEX_CAP_MULTIPLE)     # $5M floor
    per_bu = base_cap / len(bus) * 0.7                                           # under the plain cap (even with a 15% overrun), over half of it
    flags = dict(insolvency_active=True, capex_cap_multiplier=0.5, dividend_suspended=True)
    control = _tick(_gs(treasury), bus, capex=per_bu, dividends=200_000.0)
    assert not control["events"].get("capex_capped") and control["events"]["last_dividends_paid"] == 200_000.0
    out = _tick(_gs(treasury, **flags), bus, capex=per_bu, dividends=200_000.0)
    ev = out["events"]
    assert ev["capex_capped"] is True and ev["capex_cap_multiplier_applied"] == 0.5
    assert ev["capex_cap_limit"] == pytest.approx(base_cap * 0.5, abs=0.01)
    assert _financed(ev) == pytest.approx(base_cap * 0.5, abs=0.01)
    assert ev["dividends_suspended_applied"] == 200_000.0
    assert ev["dividends_paid"] == 0.0 and ev["dividends_clamped"] is True
    assert ev["last_dividends_paid"] == 0.0
    wf = ev["consequence_waterfall"]
    assert wf["unattributed"] == 0.0


def test_the_flags_clear_when_the_verdict_lifts():
    """The engine writes the verdict every tick, so the router's event→flag merge
    clears a stale notice instead of carrying it forever."""
    bus = build_bu_states()
    out = _tick(_gs(40_000_000, insolvency_active=True, capex_cap_multiplier=0.5, dividend_suspended=True), bus)
    ev = out["events"]
    assert ev["insolvency_active"] is False and ev["capex_cap_multiplier"] == 1.0 and ev["dividend_suspended"] is False
    merged = {**_gs(40_000_000, insolvency_active=True, capex_cap_multiplier=0.5, dividend_suspended=True)["active_event_flags"], **ev}
    assert merged["insolvency_active"] is False and merged["capex_cap_multiplier"] == 1.0


def test_the_turnaround_stabilisation_cap_applies_and_the_crisis_floor_is_kept():
    bus = build_bu_states()
    treasury = 1_000_000.0
    base_cap = max(CSF_POOL_FLOOR, treasury * FINANCIAL_CAPEX_CAP_MULTIPLE)
    per_bu = base_cap / len(bus) * 0.7
    stab = _tick(_gs(treasury, survival_mode=True, turnaround_phase="stabilisation",
                     distress_detection={"capex_cap_multiplier": 0.5, "turnaround_phase": "stabilisation"}),
                 bus, capex=per_bu, dividends=100_000.0)
    assert stab["events"]["capex_cap_multiplier_applied"] == 0.5
    assert _financed(stab["events"]) == pytest.approx(base_cap * 0.5, abs=0.01)
    assert stab["events"]["dividends_suspended_applied"] == 100_000.0
    # crisis: "CapEx frozen" stays narrative — the pool floor is the minimum, loan-funded investment path
    crisis = _tick(_gs(treasury, survival_mode=True, turnaround_phase="crisis",
                       distress_detection={"capex_cap_multiplier": 0.0, "turnaround_phase": "crisis"}),
                   bus, capex=per_bu, dividends=100_000.0)
    assert "capex_cap_multiplier_applied" not in crisis["events"]
    assert _financed(crisis["events"]) == pytest.approx(_requested(crisis["events"], per_bu, len(bus)), abs=0.01)
    assert crisis["events"]["dividends_suspended_applied"] == 100_000.0


def test_a_round_ten_draw_is_priced_and_repaid_in_the_round():
    bus = build_bu_states()
    treasury = 50_000_000.0
    per_bu = 4_000_000.0                                    # $16M > the 20% allowance ($10M)
    nine = _tick(_gs(treasury, round_number=9), bus, capex=per_bu)
    ten = _tick(_gs(treasury, round_number=10), bus, capex=per_bu)
    drawn = ten["events"]["capex_loan_drawn"]
    assert drawn > 0
    assert drawn == pytest.approx(_requested(ten["events"], per_bu, len(bus)) - treasury * FINANCIAL_FREE_CSF_PCT, abs=0.01)
    drawn9 = nine["events"]["capex_loan_drawn"]
    # round 9: the draw is carried; round 10: settled in the round, with a round's interest
    assert nine["events"]["capex_loan_balance"] == drawn9 > 0 and nine["events"]["capex_loan_repayment"] == 0.0
    assert nine["events"]["loan_interest_payment"] == 0.0 and "capex_loan_last_round_settled" not in nine["events"]
    assert ten["events"]["capex_loan_last_round_settled"] == drawn
    assert ten["events"]["capex_loan_repayment"] == drawn
    assert ten["events"]["loan_interest_payment"] == pytest.approx(drawn * FINANCIAL_DEFAULT_LOAN_RATE, abs=0.01)
    assert ten["events"]["capex_loan_balance"] == 0.0
    # the cash: the settled draw and its interest left the treasury this round, and the waterfall closes on it
    wf = ten["events"]["consequence_waterfall"]
    assert wf["unattributed"] == 0.0
    labels = {e["label"]: e["amount"] for e in wf["entries"]}
    assert labels["Loan Principal Repayment"] == -drawn
    assert labels["Loan Interest"] == pytest.approx(-drawn * FINANCIAL_DEFAULT_LOAN_RATE, abs=0.01)
