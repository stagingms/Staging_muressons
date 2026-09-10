"""F02 / F03 (AUDIT_Engines_Flow_Classroom50_20260909, P1) — covenant EBITDA
and the order of the balance-sheet close. Decision D1 (2026-09-10).

F02: `true_ebitda = gross_profit + total_depreciation` added back D&A that
gross profit (revenue − OPEX) had never deducted — EBITDA overstated by the
period's depreciation, leverage understated, a red covenant read amber.
Now: covenant EBITDA = revenue − OPEX − expensed CapEx (before D&A, interest
and tax), and it equals terminal_valuation's EBITDA at zero carbon tax and
zero expensed CapEx.

F03: the covenant surcharge (the round's last cash movement) was applied
AFTER the statement had been closed, and a partial recompute refreshed only
totals / net_assets / RE — the bridge, its residual, total_equity, D/E and
the liquidity ratio in the history row stayed pre-charge beside a
post-charge RE. Now the statement is closed once, after all cash movements.

This is the audit's proposed core_math_probe (Appendix C) as a permanent
test: real balance-sheet and terminal modules, synthetic state, no DB.
"""
from __future__ import annotations

import copy
import os
import sys
from pathlib import Path

import pytest

_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))
os.environ.setdefault("USE_MEMORY_DB", "true")

from balance_sheet import create_initial_balance_sheet, process_balance_sheet_tick  # noqa: E402
from terminal_valuation import calculate_terminal_value  # noqa: E402

_BU = {"bu_id": "audit", "revenue_base": 10_000_000.0, "opex_base": 8_000_000.0,
       "carbon_intensity": 0.0, "social_license_score": 70.0, "governance_risk_score": 20.0,
       "natural_capital_debt": 0.0, "staff_burnout_index": 20.0, "reputation_score": 70.0}


def _tick(treasury: float, rcf: float, capex: float = 0.0, dividends: float = 0.0, floor=None):
    bus = [dict(_BU)]
    bs = create_initial_balance_sheet(bus)
    bs["non_current_liabilities"]["revolving_credit_facility"] = rcf
    bs["covenant_trigger_ratio"] = 3.5
    gs = {"corporate_treasury": treasury, "group_reputation": 70.0, "cost_of_capital": 0.05,
          "active_event_flags": {}, "tipping_point_active": False}
    events = {"csf_this_round": 2_000_000.0, "total_capex_allocated": capex,
              "dividends_paid": dividends, "remediation_events": [], "tipping_tier": "none"}
    if floor is not None:
        events["treasury_floor_effective"] = floor
    closing, diag = process_balance_sheet_tick(bs, gs, copy.deepcopy(bus), events, 1)
    return closing, diag, gs, bus


# ── F02 ──────────────────────────────────────────────────────────────────────

def test_covenant_ebitda_does_not_add_back_depreciation_and_deducts_expensed_capex():
    closing, diag, _, _ = _tick(treasury=10_000_000.0, rcf=0.0, capex=4_000_000.0)
    inc = diag["income_statement"]
    assert diag["depreciation_charge"] > 0, "precondition: the period carries depreciation"
    assert inc["capex_expensed"] > 0, "precondition: part of the CapEx is expensed"
    ebitda = diag["covenants"]["ebitda"]
    assert ebitda == pytest.approx(inc["gross_profit"] - inc["capex_expensed"], abs=0.01)
    assert ebitda < inc["gross_profit"] + inc["depreciation"]          # the old figure
    assert closing["balance_sheet_history"][-1]["ebitda"] == ebitda


def test_covenant_ebitda_equals_terminal_ebitda_at_zero_carbon_tax_and_zero_expensed_capex():
    closing, diag, _, bus = _tick(treasury=10_000_000.0, rcf=0.0, capex=0.0)
    tv = calculate_terminal_value(bus, mr=1.0, carbon_tax_per_ton=0.0)
    assert diag["covenants"]["ebitda"] == pytest.approx(tv["terminal_ebitda"], abs=0.01)
    assert diag["covenants"]["ebitda"] == pytest.approx(2_000_000.0, abs=0.01)   # 10M − 8M


def test_leverage_reads_off_the_corrected_ebitda():
    # $7M net debt-ish position on $2M EBITDA: the ratio must use the corrected figure
    closing, diag, _, _ = _tick(treasury=1_000_000.0, rcf=8_000_000.0)
    cov = diag["covenants"]
    assert cov["ratio"] == pytest.approx(round(cov["net_debt"] / cov["ebitda"], 2), abs=0.01)


# ── F03 ──────────────────────────────────────────────────────────────────────

def test_a_positive_surcharge_leaves_no_stale_derived_figure_behind():
    closing, diag, gs, _ = _tick(treasury=10_000_000.0, rcf=100_000_000.0)
    surcharge = diag.get("covenant_surcharge_applied", 0.0)
    assert closing["covenant_status"] in ("red", "breached") and surcharge > 0, (
        closing["covenant_status"], diag["covenants"])

    # the surcharge is the last cash movement, and the statement was closed after it
    assert closing["current_assets"]["cash_and_equivalents"] == pytest.approx(max(0.0, gs["corporate_treasury"]), abs=0.01)
    assert closing["total_assets"] == pytest.approx(
        sum(closing["tangible_assets"].values()) + sum(closing["intangible_assets"].values())
        + sum(closing["current_assets"].values()), abs=0.01)
    assert closing["net_assets"] == pytest.approx(closing["total_assets"] - closing["total_liabilities"], abs=0.01)
    assert closing["retained_earnings"] == pytest.approx(
        closing["net_assets"] - closing["share_capital"] - closing["other_reserves"], abs=0.01)

    # the bridge is the post-charge bridge
    br = closing["re_bridge"]
    ni = diag["income_statement"]["net_income"]
    assert br["closing"] == pytest.approx(closing["retained_earnings"], abs=0.01)
    assert br["residual"] == pytest.approx(closing["retained_earnings"] - (br["opening"] + ni - br["dividends"]), abs=0.01)
    assert diag["re_bridge_residual"] == br["residual"]

    # the ratios are the post-charge ratios (99.0 is the sentinel for non-positive equity)
    expected_de = 99.0 if closing["net_assets"] <= 0 else round(closing["total_liabilities"] / closing["net_assets"], 2)
    assert closing["debt_to_equity"] == pytest.approx(expected_de, abs=0.01)
    assert closing["liquidity_ratio"] == pytest.approx(
        round(closing["current_assets"]["cash_and_equivalents"] / closing["total_assets"], 4), abs=1e-4)

    # the history row agrees with the closed statement in every derived field
    h = closing["balance_sheet_history"][-1]
    assert h["total_equity"] == pytest.approx(h["net_assets"], abs=0.01)
    assert h["retained_earnings"] == pytest.approx(closing["retained_earnings"], abs=0.01)
    assert h["re_bridge_residual"] == br["residual"]
    assert h["d_e_ratio"] == closing["debt_to_equity"]
    assert h["liquidity_ratio"] == closing["liquidity_ratio"]
    assert h["total_assets"] == closing["total_assets"]

    # the covenant assessment itself is the PRE-charge one (the lender's view of the period)
    cov = diag["covenants"]
    assert cov["net_debt"] == pytest.approx(
        closing["non_current_liabilities"]["revolving_credit_facility"]
        + closing["non_current_liabilities"]["green_bonds_outstanding"]
        + closing["non_current_liabilities"].get("capex_term_loan", 0.0)
        + closing["current_liabilities"]["short_term_debt"]
        - 10_000_000.0, abs=0.01)


def test_the_floor_relief_still_folds_into_the_disclosure():
    closing, diag, gs, _ = _tick(treasury=200_000.0, rcf=100_000_000.0, floor=0.0)
    assert diag.get("covenant_surcharge_forgiven_by_floor", 0.0) > 0
    assert gs["corporate_treasury"] == pytest.approx(0.0, abs=0.01)
    assert diag["covenant_surcharge_applied"] == pytest.approx(200_000.0, abs=0.01)


def test_zero_surcharge_path_is_unchanged_in_shape():
    closing, diag, _, _ = _tick(treasury=50_000_000.0, rcf=0.0)
    assert "covenant_surcharge_applied" not in diag
    assert closing["covenant_status"] in ("green", "amber")
    assert closing["re_bridge"]["closing"] == closing["retained_earnings"]
    assert closing["balance_sheet_history"][-1]["total_equity"] == pytest.approx(closing["net_assets"], abs=0.01)


def test_source_pin_the_surcharge_precedes_the_single_close():
    src = (_BACKEND_DIR / "balance_sheet.py").read_text(encoding="utf-8")
    i_cov = src.index("true_ebitda = round(gross_profit - capex_expensed, 2)")
    i_sur = src.index('surcharge = covenant_diag.get("treasury_surcharge", 0.0)')
    i_close = src.index("# ── Step 9: Calculate Totals and Close A = L + E")
    i_hist = src.index('bs["balance_sheet_history"].append({')
    assert i_cov < i_sur < i_close < i_hist
    assert "Recalculate totals after cash mutation" not in src
    assert 'true_ebitda = round(gross_profit + total_depreciation, 2)' not in src
