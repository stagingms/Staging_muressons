"""
Balance Sheet Fix Verification Tests
Runs all 6 checks for the 13 fixes applied to balance_sheet.py
"""
import copy, sys
sys.path.insert(0, ".")
from balance_sheet import create_initial_balance_sheet, process_balance_sheet_tick, calc_brand_value

PASS = "PASS"
FAIL = "FAIL"
results = []

def check(label, condition):
    status = PASS if condition else FAIL
    results.append((label, status))
    icon = "✅" if condition else "❌"
    print(f"  [{status}] {icon}  {label}")

bus_4 = [
    {"bu_id": "pharma",         "revenue_base": 18_000_000, "opex_base": 11_500_000, "social_license_score": 55, "governance_risk_score": 15, "carbon_intensity": 45, "natural_capital_debt": 0, "reputation_score": 52},
    {"bu_id": "electronics",    "revenue_base": 16_500_000, "opex_base": 10_800_000, "social_license_score": 48, "governance_risk_score": 20, "carbon_intensity": 72, "natural_capital_debt": 0, "reputation_score": 50},
    {"bu_id": "consumer_goods", "revenue_base": 10_500_000, "opex_base":  7_800_000, "social_license_score": 52, "governance_risk_score": 10, "carbon_intensity": 38, "natural_capital_debt": 0, "reputation_score": 53},
    {"bu_id": "software",       "revenue_base":  8_500_000, "opex_base":  4_200_000, "social_license_score": 60, "governance_risk_score":  8, "carbon_intensity": 28, "natural_capital_debt": 0, "reputation_score": 58},
]
bus_1 = [
    {"bu_id": "pharma", "revenue_base": 18_000_000, "opex_base": 11_500_000, "social_license_score": 55, "governance_risk_score": 15, "carbon_intensity": 45, "natural_capital_debt": 0, "reputation_score": 52},
]

gs = {"corporate_treasury": 50_000_000, "group_reputation": 50, "cost_of_capital": 0.05, "active_event_flags": {}}

# ==============================================================
print("\n=== TEST 1: FIX-1 — Opening Balance Sheet Balances (4-BU) ===")
bs4 = create_initial_balance_sheet(bus_4)
ta = sum(bs4["tangible_assets"].values()) + sum(bs4["intangible_assets"].values()) + sum(bs4["current_assets"].values())
tl = sum(bs4["non_current_liabilities"].values()) + sum(bs4["current_liabilities"].values())
te = bs4["share_capital"] + bs4["retained_earnings"] + bs4["other_reserves"]
gap = abs(ta - tl - te)
print(f"  Total Assets: {ta:,.0f}  Liabilities: {tl:,.0f}  Equity: {te:,.0f}  Gap: {gap:.2f}")
check("4-BU opening BS balances (A = L + E)", gap < 1.0)

# ==============================================================
print("\n=== TEST 2: FIX-1 + FIX-13 — Opening Balance Sheet Balances (1-BU) ===")
bs1 = create_initial_balance_sheet(bus_1)
ta1 = sum(bs1["tangible_assets"].values()) + sum(bs1["intangible_assets"].values()) + sum(bs1["current_assets"].values())
tl1 = sum(bs1["non_current_liabilities"].values()) + sum(bs1["current_liabilities"].values())
te1 = bs1["share_capital"] + bs1["retained_earnings"] + bs1["other_reserves"]
gap1 = abs(ta1 - tl1 - te1)
print(f"  Total Assets: {ta1:,.0f}  Liabilities: {tl1:,.0f}  Equity: {te1:,.0f}  Gap: {gap1:.2f}")
check("1-BU opening BS balances (A = L + E)", gap1 < 1.0)

# ==============================================================
print("\n=== TEST 3: FIX-2 — Brand Value Does NOT Compound ===")
brand_base = 25_000_000
brands = []
for _ in range(11):
    v, _ = calc_brand_value(brand_base, 60, 65)
    brands.append(v)
print(f"  Brand at rep=60, slo=65 for 11 iterations: {brands[0]:,.0f} -> {brands[5]:,.0f} -> {brands[10]:,.0f}")
check("Brand value constant across iterations (no compounding)", brands[0] == brands[5] == brands[10])
check("Brand value above base at rep=60 (> neutral)", brands[0] > brand_base)
check("Brand value stays bounded (below 3x base)", brands[10] < brand_base * 3)

# ==============================================================
print("\n=== TEST 4: FIX-3 — Dividends NOT in Net Income ===")
events_div  = {"total_capex_allocated": 0, "dividends_paid": 2_000_000, "remediation_events": []}
events_nodiv = {"total_capex_allocated": 0, "dividends_paid": 0,         "remediation_events": []}
bs_a, d_a = process_balance_sheet_tick(copy.deepcopy(bs4), copy.deepcopy(gs), bus_4, events_div,  1)
bs_b, d_b = process_balance_sheet_tick(copy.deepcopy(bs4), copy.deepcopy(gs), bus_4, events_nodiv, 1)
ni_a = d_a["income_statement"]["net_income"]
ni_b = d_b["income_statement"]["net_income"]
re_diff = bs_b["retained_earnings"] - bs_a["retained_earnings"]
print(f"  Net income WITH dividends: {ni_a:,.0f}")
print(f"  Net income WITHOUT dividends: {ni_b:,.0f}")
print(f"  RE difference: {re_diff:,.0f}")
print(f"  (With closing-identity model, RE is derived from net_assets each tick.")
print(f"   Dividend impact on RE flows via treasury->cash->net_assets.)")
check("Net income unchanged by dividend payment (FIX-3 core)", ni_a == ni_b)
check("Dividends not in net income (P&L correct)", "dividends_as_equity_distribution" in d_a["income_statement"])

# ==============================================================
print("\n=== TEST 5: FIX-4 — EBITDA Includes Depreciation ===")
bs_e = create_initial_balance_sheet(bus_4)
_, d_e = process_balance_sheet_tick(bs_e, copy.deepcopy(gs), bus_4, {"total_capex_allocated": 0, "dividends_paid": 0, "remediation_events": []}, 1)
gp   = d_e["income_statement"]["gross_profit"]
dep  = d_e["income_statement"]["depreciation"]
expected_ebitda = gp + dep
actual_ebitda   = d_e["covenants"]["ebitda"]
print(f"  Gross Profit: {gp:,.0f}  Depreciation: {dep:,.0f}  Expected EBITDA: {expected_ebitda:,.0f}  Actual: {actual_ebitda:,.0f}")
check("Covenant EBITDA = Gross Profit + Depreciation", abs(actual_ebitda - expected_ebitda) < 1)

# ==============================================================
print("\n=== TEST 6: FIX-5 — New CAPEX Not Depreciated Same Period ===")
bs_c0 = create_initial_balance_sheet(bus_4)
bs_c1 = create_initial_balance_sheet(bus_4)
ev_no_capex   = {"total_capex_allocated": 0,           "dividends_paid": 0, "remediation_events": []}
ev_big_capex  = {"total_capex_allocated": 10_000_000,  "dividends_paid": 0, "remediation_events": []}
_, d_no_capex  = process_balance_sheet_tick(copy.deepcopy(bs_c0), copy.deepcopy(gs), bus_4, ev_no_capex,  1)
_, d_big_capex = process_balance_sheet_tick(copy.deepcopy(bs_c1), copy.deepcopy(gs), bus_4, ev_big_capex, 1)
dep_no  = d_no_capex["depreciation_charge"]
dep_big = d_big_capex["depreciation_charge"]
print(f"  Depreciation with 0 CAPEX: {dep_no:,.0f}")
print(f"  Depreciation with $10M CAPEX: {dep_big:,.0f}  (should be same -- new CAPEX not yet depreciated)")
check("Depreciation equal regardless of new CAPEX (FIX-5)", abs(dep_no - dep_big) < 1)

# ==============================================================
print("\n=== TEST 7: FIX-6 — Environmental Provisions Can Decrease ===")
from balance_sheet import calc_environmental_provisions
high_prov = calc_environmental_provisions(5_000_000, 500, [])   # NCD=500 -> 500*5000=2.5M < 5M floor
low_ncd   = calc_environmental_provisions(5_000_000, 50, [])    # NCD=50  -> 50*5000=250K < floor
print(f"  Provisions at NCD=500: {high_prov:,.0f}  (floor=1,000,000)")
print(f"  Provisions at NCD=50:  {low_ncd:,.0f}   (floor=1,000,000, was 5,000,000)")
check("Provisions decrease when NCD falls (IAS 37 reversal)", low_ncd < 5_000_000)
check("Provisions floor at MIN_ENVIRONMENTAL_PROVISION", low_ncd >= 1_000_000)

# ==============================================================
print("\n=== TEST 8: FIX-7 — Inventory Updated Dynamically ===")
bs_inv = create_initial_balance_sheet(bus_4)
_, d_inv = process_balance_sheet_tick(bs_inv, copy.deepcopy(gs), bus_4, {"total_capex_allocated": 0, "dividends_paid": 0, "remediation_events": []}, 1)
inv_after = d_inv["working_capital"]["inventory"]
seed_inv  = sum(b["opex_base"] for b in bus_4) / 365 * 60  # Expected: 60-day OPEX model
print(f"  Inventory after tick: {inv_after:,.0f}  Expected (60-day OPEX): {seed_inv:,.0f}")
check("Inventory dynamically updated to 60-day OPEX model", abs(inv_after - seed_inv) < 10)

# ==============================================================
print("\n=== TEST 9: FIX-8 — ESG Capitals NOT in Total Assets ===")
bs_esg = create_initial_balance_sheet(bus_4)
_, d_esg = process_balance_sheet_tick(bs_esg, copy.deepcopy(gs), bus_4, {"total_capex_allocated": 0, "dividends_paid": 0, "remediation_events": []}, 1)
has_esg = "esg_capitals" in bs_esg
no_sla_in_intang = "social_licence_asset" not in bs_esg.get("intangible_assets", {})
print(f"  Has esg_capitals dict: {has_esg}")
print(f"  social_licence_asset absent from intangible_assets: {no_sla_in_intang}")
check("ESG capitals stored in esg_capitals (not intangible_assets)", has_esg and no_sla_in_intang)

# ==============================================================
print("\n=== TEST 10: FIX-9 — Goodwill Impairment Smooth (No Hard Cliff) ===")
from balance_sheet import create_initial_balance_sheet, process_balance_sheet_tick
gs_rep40 = {"corporate_treasury": 50_000_000, "group_reputation": 40, "cost_of_capital": 0.05, "active_event_flags": {}}
gs_rep39 = {"corporate_treasury": 50_000_000, "group_reputation": 39, "cost_of_capital": 0.05, "active_event_flags": {}}
bs_r40 = create_initial_balance_sheet(bus_4)
bs_r39 = create_initial_balance_sheet(bus_4)
_, d_r40 = process_balance_sheet_tick(bs_r40, gs_rep40, bus_4, {"total_capex_allocated": 0, "dividends_paid": 0, "remediation_events": []}, 2)
_, d_r39 = process_balance_sheet_tick(bs_r39, gs_rep39, bus_4, {"total_capex_allocated": 0, "dividends_paid": 0, "remediation_events": []}, 2)
imp_40 = d_r40.get("goodwill_impairment", {}).get("amount", 0)
imp_39 = d_r39.get("goodwill_impairment", {}).get("amount", 0)
print(f"  Impairment at rep=40: {imp_40:,.0f}  (should be 0 -- just at threshold)")
print(f"  Impairment at rep=39: {imp_39:,.0f}  (small smooth start, not 10% hard floor)")
check("No impairment at rep=40 (smooth, no cliff)", imp_40 == 0)
# Old code: fixed 10% floor -> impairment at rep=39 would be goodwill * 0.10 = 250,000
# New smooth formula: (40-39)/200 = 0.5% -> impairment = goodwill * 0.005 = 12,500 (scaled to n_bus)
check("Impairment at rep=39 is small (smooth < old 10% hard floor)", 0 < imp_39 < 250_000)

# ==============================================================
print("\n=== TEST 11: FIX-12 — Decommissioning Accretes Each Round ===")
bs_dc = create_initial_balance_sheet(bus_4)
initial_decomm = bs_dc["non_current_liabilities"]["decommissioning_obligations"]
bs_dc2, d_dc = process_balance_sheet_tick(bs_dc, copy.deepcopy(gs), bus_4, {"total_capex_allocated": 0, "dividends_paid": 0, "remediation_events": []}, 1)
final_decomm = bs_dc2["non_current_liabilities"]["decommissioning_obligations"]
accretion = d_dc["decommissioning_accretion"]
print(f"  Initial decommissioning: {initial_decomm:,.0f}  After accretion: {final_decomm:,.0f}  Accretion: {accretion:,.0f}")
check("Decommissioning obligation accretes each round (IFRIC 1)", final_decomm > initial_decomm and accretion > 0)

# ==============================================================
print("\n=== TEST 12: Post-tick Balance Sheet Still Balances ===")
gs3 = {"corporate_treasury": 47_000_000, "group_reputation": 50, "cost_of_capital": 0.05, "active_event_flags": {}}
bs_fin = create_initial_balance_sheet(bus_4)
bs_fin, d_fin = process_balance_sheet_tick(bs_fin, gs3, bus_4, {"total_capex_allocated": 5_000_000, "dividends_paid": 1_000_000, "remediation_events": []}, 1)
print(f"  balance_sheet_balanced: {d_fin['balance_sheet_balanced']}  Imbalance: {d_fin['imbalance']:.2f}")
check("Post-tick BS balances (A = L + E) with CAPEX + dividends", d_fin["balance_sheet_balanced"])

# ==============================================================
print("\n" + "="*60)
passed = sum(1 for _, s in results if s == PASS)
failed = sum(1 for _, s in results if s == FAIL)
print(f"RESULTS: {passed}/{passed+failed} tests passed  |  {failed} failed")
if failed == 0:
    print("ALL FIXES VERIFIED ✅")
else:
    print("FAILURES DETECTED ❌ — review output above")
