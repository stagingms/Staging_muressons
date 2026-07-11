"""Verify that the covenant surcharge fix eliminates the $14M discrepancy."""
from balance_sheet import create_initial_balance_sheet, process_balance_sheet_tick

# Create a 4-BU config
bus = [
    {"revenue_base": 10_000_000, "opex_base": 8_000_000,
     "governance_risk_score": 20, "social_license_score": 10,
     "carbon_intensity": 80, "natural_capital_debt": 5}
    for _ in range(4)
]
bs = create_initial_balance_sheet(bus)

# Set up a scenario that triggers covenant breach (very negative cash)
gs = {
    "corporate_treasury": -521_100_000,
    "group_reputation": 15,
    "cost_of_capital": 0.12,
    "survival_mode": False,
    "active_event_flags": {},
}
events = {"total_capex_allocated": 0, "dividends_paid": 0}

bs, diag = process_balance_sheet_tick(bs, gs, bus, events, round_number=2)

# Check consistency
ta_backend = bs["total_assets"]
ta_dicts = round(
    sum(bs["tangible_assets"].values())
    + sum(bs["intangible_assets"].values())
    + sum(bs["current_assets"].values()), 2
)

print(f"Backend total_assets:  {ta_backend:>18,.2f}")
print(f"Dict re-sum:           {ta_dicts:>18,.2f}")
print(f"Discrepancy:           {abs(ta_backend - ta_dicts):>18,.2f}")
print(f"Covenant status:       {bs['covenant_status']}")
print(f"Surcharge applied:     {diag.get('covenant_surcharge_applied', 0):,.2f}")
print()

# Verify A = L + E
net_assets = bs["total_assets"] - bs["total_liabilities"]
total_equity = bs["share_capital"] + bs["retained_earnings"] + bs["other_reserves"]
print(f"Net Assets (A - L):    {net_assets:>18,.2f}")
print(f"Total Equity (S+R+O):  {total_equity:>18,.2f}")
ale_holds = abs(net_assets - total_equity) < 0.01
print(f"A = L + E holds:       {ale_holds}")
print()

if abs(ta_backend - ta_dicts) < 0.01 and ale_holds:
    print("=== ALL CHECKS PASSED ===")
else:
    print("!!! FIX FAILED — discrepancy still exists !!!")
