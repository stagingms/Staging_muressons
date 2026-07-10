"""Reversal identity check."""
import copy
from balance_sheet import create_initial_balance_sheet, process_balance_sheet_tick

bus = [{'bu_id': 'test', 'revenue_base': 13_375_000, 'opex_base': 8_600_000,
        'social_license_score': 55, 'governance_risk_score': 15,
        'carbon_intensity': 40, 'natural_capital_debt': 0}]
gs = {'corporate_treasury': 25_000_000, 'group_reputation': 50, 'cost_of_capital': 0.05,
      'active_event_flags': {}, 'tipping_tier': 'none'}
ev = {'csf_this_round': 0, 'total_capex_allocated': 0, 'dividends_paid': 0,
      'remediation_events': [], 'tipping_tier': 'none',
      'green_bond_issued': False, 'green_bond_amount': 0}

# Scholarly state
bs_sch = create_initial_balance_sheet(bus)
bs_sch['current_assets']['cash_and_equivalents'] = 25_000_000
bs_sch, _ = process_balance_sheet_tick(
    bs_sch, copy.deepcopy(gs), bus, copy.deepcopy(ev), 1, include_esg_on_bs=True)

# Toggle OFF on the scholarly state
bs_rev, d_rev = process_balance_sheet_tick(
    copy.deepcopy(bs_sch), copy.deepcopy(gs), bus, copy.deepcopy(ev), 1, include_esg_on_bs=False)

ta  = bs_rev['total_assets']
tl  = bs_rev['total_liabilities']
sc  = bs_rev['share_capital']
re  = bs_rev['retained_earnings']
or_ = bs_rev['other_reserves']
chk = ta - tl - sc - re - or_
esg_cleared = 'esg_social_licence_capital' not in bs_rev['intangible_assets']
mode_active  = d_rev['esg_bs_mode']['active']

print(f"After toggle-off: A-L-E = {chk:+.4f}  => {'PASS' if abs(chk) < 1 else 'FAIL'}")
print(f"esg_ keys cleared: {esg_cleared}")
print(f"esg_bs_mode.active: {mode_active}")
