"""financial_invariants.py — articulation assertions for the Muressons engine.
Call check_all(...) at the end of process_balance_sheet_tick (dev: raise, prod: log).
TOL_ABS is cents-level for mechanical ties; TOL_ECON for economic bridges."""

TOL_ABS  = 0.01          # mechanical arithmetic must tie to the cent
TOL_ECON = 1.00          # accumulated float rounding across a bridge

class FinancialInvariantError(AssertionError):
    pass

def _sections(bs):
    a = (sum(bs["tangible_assets"].values()) + sum(bs["intangible_assets"].values())
         + sum(bs["current_assets"].values()))
    l = (sum(bs["non_current_liabilities"].values()) + sum(bs["current_liabilities"].values()))
    e = bs["share_capital"] + bs["other_reserves"] + bs["retained_earnings"]
    return a, l, e

def inv1_identity_independent(bs):
    """A = L + E recomputed from raw line items — NOT from the stored totals,
    and NOT trusting the RE derivation: uses the stored RE figure as data."""
    a, l, e = _sections(bs)
    if abs(a - l - e) > TOL_ABS:
        raise FinancialInvariantError(f"A-L-E residual {a-l-e:.2f}")
    if abs(a - bs["total_assets"]) > TOL_ABS or abs(l - bs["total_liabilities"]) > TOL_ABS:
        raise FinancialInvariantError("stored totals drifted from line-item sums")

def inv2_re_rollforward(bs_open, bs_close, net_income, dividends_paid_cash,
                        other_equity_movements=0.0):
    """RE_open + NI - dividends(CASH-effective) + itemised other movements = RE_close.
    other_equity_movements must be an itemised, disclosed number — not a residual.
    FAILS TODAY (plug): keep as xfail(strict=True) until remediation #1 Phase B."""
    expected = bs_open["retained_earnings"] + net_income - dividends_paid_cash + other_equity_movements
    resid = bs_close["retained_earnings"] - expected
    if abs(resid) > TOL_ECON:
        raise FinancialInvariantError(f"RE bridge residual {resid:,.2f}")

def inv3_cash_articulation(bs, corporate_treasury):
    """BS cash == max(0, treasury); swept deficit == -min(0, treasury)."""
    cash = bs["current_assets"]["cash_and_equivalents"]
    std  = bs["current_liabilities"]["short_term_debt"]
    if abs(cash - max(0.0, corporate_treasury)) > TOL_ABS:
        raise FinancialInvariantError(f"cash {cash:,.2f} != max(0, treasury {corporate_treasury:,.2f})")
    if abs(std - max(0.0, -corporate_treasury)) > TOL_ABS:
        raise FinancialInvariantError(f"short_term_debt {std:,.2f} != swept deficit")

def inv4_ppe_rollforward(ppe_open, capex_capitalised, depreciation_ppe, ppe_close):
    resid = ppe_close - (ppe_open + capex_capitalised - depreciation_ppe)
    if abs(resid) > TOL_ABS:
        raise FinancialInvariantError(f"PP&E roll residual {resid:.2f}")

def inv5_income_statement_arithmetic(inc):
    gp = inc["revenue"] - inc["opex"]
    taxable = gp - inc["interest_expense"] - inc["depreciation"] - inc["capex_expensed"]
    if abs(gp - inc["gross_profit"]) > TOL_ABS or abs(taxable - inc["taxable_income"]) > TOL_ABS:
        raise FinancialInvariantError("P&L internal arithmetic broken")
    if abs((inc["taxable_income"] - inc["tax_charge"]) - inc["net_income"]) > TOL_ABS:
        raise FinancialInvariantError("NI != taxable - tax")

def inv6_waterfall_closure(waterfall, treasury_open, treasury_close):
    """The cash statement must explain the whole round: initial + Σentries = close.
    FAILS TODAY by up to $55M/round: xfail until remediation #8."""
    explained = waterfall["initial_treasury"] + sum(e["amount"] for e in waterfall["entries"])
    resid = treasury_close - explained
    if abs(resid) > TOL_ECON:
        raise FinancialInvariantError(f"waterfall unexplained cash {resid:,.2f}")

def inv7_dividends_consistency(recorded_equity_distribution, cash_dividends_paid):
    """The equity distribution recorded on the statement equals the cash that left.
    FAILS TODAY in clamped rounds: xfail until remediation #3."""
    if abs(recorded_equity_distribution - cash_dividends_paid) > TOL_ABS:
        raise FinancialInvariantError(
            f"dividends: equity says {recorded_equity_distribution:,.2f}, "
            f"cash paid {cash_dividends_paid:,.2f}")

def check_all(bs_open, bs_close, gs, diagnostics, waterfall=None):
    inc = diagnostics["income_statement"]
    inv1_identity_independent(bs_close)
    inv3_cash_articulation(bs_close, gs.get("corporate_treasury", 0.0))
    if bs_open is not None:
        inv4_ppe_rollforward(
            bs_open["tangible_assets"]["property_plant_equipment"],
            diagnostics["capex_capitalised"],
            round(bs_open["tangible_assets"]["property_plant_equipment"] * 0.05, 2),
            bs_close["tangible_assets"]["property_plant_equipment"])
    inv5_income_statement_arithmetic(inc)
    # xfail-until-fixed set:
    # inv2_re_rollforward(...); inv6_waterfall_closure(...); inv7_dividends_consistency(...)
