"""
Verification script for the Scholarly ESG Capitalisation toggle.
Tests standard vs scholarly mode, balance identity, and toggle reversal.
"""
import copy
from balance_sheet import create_initial_balance_sheet, process_balance_sheet_tick

bus = [{
    'bu_id': 'test',
    'revenue_base': 13_375_000,
    'opex_base':     8_600_000,
    'social_license_score': 55,
    'governance_risk_score': 15,
    'carbon_intensity': 40,
    'natural_capital_debt': 0,
}]
gs = {
    'corporate_treasury': 25_000_000,
    'group_reputation': 50,
    'cost_of_capital': 0.05,
    'active_event_flags': {},
    'tipping_tier': 'none',
}
ev = {
    'csf_this_round': 0, 'total_capex_allocated': 0, 'dividends_paid': 0,
    'remediation_events': [], 'tipping_tier': 'none', 'green_bond_issued': False,
    'green_bond_amount': 0,
}

# --- STANDARD MODE ---
bs_std = create_initial_balance_sheet(bus)
bs_std['current_assets']['cash_and_equivalents'] = 25_000_000
bs_std, d_std = process_balance_sheet_tick(
    bs_std, copy.deepcopy(gs), bus, copy.deepcopy(ev), 1, include_esg_on_bs=False
)

# --- SCHOLARLY MODE ---
bs_sch = create_initial_balance_sheet(bus)
bs_sch['current_assets']['cash_and_equivalents'] = 25_000_000
bs_sch, d_sch = process_balance_sheet_tick(
    bs_sch, copy.deepcopy(gs), bus, copy.deepcopy(ev), 1, include_esg_on_bs=True
)

# --- TOGGLE REVERSAL (scholarly state -> standard mode) ---
bs_rev, d_rev = process_balance_sheet_tick(
    copy.deepcopy(bs_sch), copy.deepcopy(gs), bus, copy.deepcopy(ev), 1, include_esg_on_bs=False
)

print("=== STANDARD (IAS 38 compliant) ===")
ta_std = bs_std['total_assets']
tl_std = bs_std['total_liabilities']
re_std = bs_std['retained_earnings']
sc_std = bs_std['share_capital']
or_std = bs_std['other_reserves']
chk_std = ta_std - tl_std - sc_std - re_std - or_std
print(f"  Total Assets:      {ta_std:>18,.2f}")
print(f"  Total Liabilities: {tl_std:>18,.2f}")
print(f"  Net Assets:        {bs_std['net_assets']:>18,.2f}")
print(f"  Retained Earnings: {re_std:>18,.2f}")
print(f"  Total Intangibles: {sum(v for v in bs_std['intangible_assets'].values() if v):>18,.2f}")
print(f"  Balance check A-L-E: {chk_std:>+.4f}  ({'PASS' if abs(chk_std) < 1 else 'FAIL'})")
print(f"  esg_bs_mode.active: {d_std['esg_bs_mode']['active']}")

print()
print("=== SCHOLARLY (ESG on BS) ===")
ta_sch = bs_sch['total_assets']
tl_sch = bs_sch['total_liabilities']
re_sch = bs_sch['retained_earnings']
sc_sch = bs_sch['share_capital']
or_sch = bs_sch['other_reserves']
chk_sch = ta_sch - tl_sch - sc_sch - re_sch - or_sch
slc_on = bs_sch['intangible_assets'].get('esg_social_licence_capital', 0)
rep_on = bs_sch['intangible_assets'].get('esg_reputation_capital', 0)
print(f"  Total Assets:      {ta_sch:>18,.2f}")
print(f"  Total Liabilities: {tl_sch:>18,.2f}")
print(f"  Net Assets:        {bs_sch['net_assets']:>18,.2f}")
print(f"  Retained Earnings: {re_sch:>18,.2f}")
print(f"  Total Intangibles: {sum(v for v in bs_sch['intangible_assets'].values() if v):>18,.2f}")
print(f"  SLC on BS:         {slc_on:>18,.2f}")
print(f"  Rep on BS:         {rep_on:>18,.2f}")
print(f"  Balance check A-L-E: {chk_sch:>+.4f}  ({'PASS' if abs(chk_sch) < 1 else 'FAIL'})")
print(f"  esg_bs_mode.active: {d_sch['esg_bs_mode']['active']}")
print(f"  esg_bs_mode.total_esg_on_bs: {d_sch['esg_bs_mode']['total_esg_on_bs']:,.2f}")

print()
delta_a  = ta_sch - ta_std
delta_re = re_sch - re_std
print("=== DELTA (Scholarly - Standard) ===")
print(f"  Delta Total Assets:      {delta_a:>+18,.2f}")
print(f"  Delta Retained Earnings: {delta_re:>+18,.2f}")
delta_ok = abs(delta_a - delta_re) < 1.0
print(f"  Delta_Assets == Delta_RE (A=L+E holds): {'PASS' if delta_ok else 'FAIL'}")

print()
print("=== TOGGLE REVERSAL TEST ===")
has_esg_key = 'esg_social_licence_capital' in bs_rev['intangible_assets']
ta_rev = bs_rev['total_assets']
print(f"  esg_ keys cleared on toggle-off: {'PASS' if not has_esg_key else 'FAIL'}")
rev_matches = abs(ta_rev - ta_std) < 1.0
print(f"  Total Assets after reversal: {ta_rev:>18,.2f}")
print(f"  Matches standard view:       {'PASS' if rev_matches else 'FAIL'} (expected {ta_std:,.2f})")

print()
all_pass = abs(chk_std) < 1 and abs(chk_sch) < 1 and delta_ok and not has_esg_key and rev_matches
print(f"{'ALL TESTS PASSED' if all_pass else 'SOME TESTS FAILED'}")
