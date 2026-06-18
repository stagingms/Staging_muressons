import copy
from balance_sheet import create_initial_balance_sheet, process_balance_sheet_tick

bus_4 = [
    {"bu_id": "pharma",         "revenue_base": 18_000_000, "opex_base": 11_500_000, "social_license_score": 55, "governance_risk_score": 15, "carbon_intensity": 45, "natural_capital_debt": 0, "reputation_score": 52},
    {"bu_id": "electronics",    "revenue_base": 16_500_000, "opex_base": 10_800_000, "social_license_score": 48, "governance_risk_score": 20, "carbon_intensity": 72, "natural_capital_debt": 0, "reputation_score": 50},
    {"bu_id": "consumer_goods", "revenue_base": 10_500_000, "opex_base":  7_800_000, "social_license_score": 52, "governance_risk_score": 10, "carbon_intensity": 38, "natural_capital_debt": 0, "reputation_score": 53},
    {"bu_id": "software",       "revenue_base":  8_500_000, "opex_base":  4_200_000, "social_license_score": 60, "governance_risk_score":  8, "carbon_intensity": 28, "natural_capital_debt": 0, "reputation_score": 58},
]

gs3 = {"corporate_treasury": 47_000_000, "group_reputation": 50, "cost_of_capital": 0.05, "active_event_flags": {}}
bs_fin = create_initial_balance_sheet(bus_4)

# Before tick
ta0 = sum(bs_fin["tangible_assets"].values()) + sum(bs_fin["intangible_assets"].values()) + sum(bs_fin["current_assets"].values())
tl0 = sum(bs_fin["non_current_liabilities"].values()) + sum(bs_fin["current_liabilities"].values())
te0 = bs_fin["share_capital"] + bs_fin["retained_earnings"] + bs_fin["other_reserves"]
print(f"Before tick: Assets={ta0:,.0f}  Liabilities={tl0:,.0f}  Equity={te0:,.0f}  Gap={abs(ta0-tl0-te0):.2f}")

bs_fin, d_fin = process_balance_sheet_tick(bs_fin, gs3, bus_4, {"total_capex_allocated": 5_000_000, "dividends_paid": 1_000_000, "remediation_events": []}, 1)

ta = bs_fin["total_assets"]
tl = bs_fin["total_liabilities"]
na = bs_fin["net_assets"]
te = d_fin["equity_check"]
print(f"After tick:  Assets={ta:,.0f}  Liabilities={tl:,.0f}  Net Assets={na:,.0f}  Equity={te:,.0f}  Gap={abs(na-te):.2f}")
print()

# The root cause: the opening retained_earnings was SET to close A=L+E at time 0.
# But then net_income is ADDED on top. So RE grows, but Assets don't grow by the same amount.
# The fundamental issue: the opening BS does not represent a "pre-tick" clean state — 
# it's set so that A=L+E at seed, then the tick adds income to RE without a corresponding asset.
#
# Actually in double-entry: when you earn income, cash comes in (asset increases) OR
# a receivable increases. The cash increase IS represented via corporate_treasury → cash.
# But gross_profit in the income statement is already reflected in the BU revenue_base,
# which hasn't been converted to cash yet in the BS (only the treasury is).
# The BS and treasury are partially decoupled.
print("Income statement:")
for k, v in d_fin["income_statement"].items():
    print(f"  {k}: {v}")
print()
print("Net income added to RE:", d_fin["income_statement"]["net_income"])
print("Treasury input to BS (cash):", gs3["corporate_treasury"])
print()
print("Key insight: net_income added to RE but no corresponding new asset created")
print("This is the structural decoupling between cash-flow model and accrual BS")
