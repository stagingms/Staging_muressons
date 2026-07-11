import sys, math, copy
sys.path.insert(0, '.')
from balance_sheet import create_initial_balance_sheet, process_balance_sheet_tick

bus = [
    {'bu_id': 'pharma',         'revenue_base': 18_000_000, 'opex_base': 11_500_000, 'social_license_score': 55, 'governance_risk_score': 15, 'carbon_intensity': 45, 'natural_capital_debt': 0},
    {'bu_id': 'electronics',    'revenue_base': 16_500_000, 'opex_base': 10_800_000, 'social_license_score': 48, 'governance_risk_score': 20, 'carbon_intensity': 72, 'natural_capital_debt': 0},
    {'bu_id': 'consumer_goods', 'revenue_base': 10_500_000, 'opex_base':  7_800_000, 'social_license_score': 52, 'governance_risk_score': 10, 'carbon_intensity': 38, 'natural_capital_debt': 0},
    {'bu_id': 'software',       'revenue_base':  8_500_000, 'opex_base':  4_200_000, 'social_license_score': 60, 'governance_risk_score':  8, 'carbon_intensity': 28, 'natural_capital_debt': 0},
]

total_rev  = sum(b['revenue_base'] for b in bus)
total_opex = sum(b['opex_base']    for b in bus)
n_bus = 4

# Seed intermediate calculations
revolving_credit = 12_500_000 * n_bus
brand_base = 6_250_000 * n_bus
goodwill_seed = 2_500_000 * n_bus
env_prov = 1_250_000 * n_bus
decomm = 750_000 * n_bus
share_cap = 7_500_000 * n_bus
other_res = 1_250_000 * n_bus
ip_value = 15_000_000 + n_bus * 2_000_000
inventory = round((total_opex / 365) * 60, 2)
rou_assets = round(total_rev * 0.40, 2)
trade_rec = round(total_rev * 0.12, 2)
prepayments = 250_000 * n_bus
lease_liab = round(total_rev * 0.35, 2)
trade_pay = round(total_rev * 0.12, 2)

non_ppe = inventory + rou_assets + brand_base + ip_value + goodwill_seed + trade_rec + prepayments
total_liab_seed = revolving_credit + env_prov + decomm + lease_liab + trade_pay
fixed_eq = share_cap + other_res
ppe_seed = max(round(total_rev * 0.30, 2), round(total_liab_seed + fixed_eq - non_ppe, 2))
total_assets_seed = non_ppe + ppe_seed
re_seed = round(total_assets_seed - total_liab_seed - fixed_eq, 2)

print('ROUND 0 SEED INPUTS')
print(f'  Total Revenue:               {total_rev:>14,.0f}')
print(f'  Total OPEX:                  {total_opex:>14,.0f}')
print(f'  Gross Profit:                {total_rev - total_opex:>14,.0f}')
print()
print('ROUND 0 ASSET LINE DERIVATION')
print(f'  Inventory (60d x OPEX/365):  {inventory:>14,.0f}')
print(f'  ROU Assets (40pct x Rev):    {rou_assets:>14,.0f}')
print(f'  Brand Base ($6.25M x 4):     {brand_base:>14,.0f}')
print(f'  IP ($15M + $2M x 4):         {ip_value:>14,.0f}')
print(f'  Goodwill ($2.5M x 4):        {goodwill_seed:>14,.0f}')
print(f'  Trade Receivables (12pctRev):{trade_rec:>14,.0f}')
print(f'  Prepayments ($250K x 4):     {prepayments:>14,.0f}')
print(f'  Non-PPE Subtotal:            {non_ppe:>14,.0f}')
print()
print('ROUND 0 LIABILITY LINE DERIVATION')
print(f'  Revolving Credit ($12.5M x4):{revolving_credit:>14,.0f}')
print(f'  Env Provisions ($1.25M x 4): {env_prov:>14,.0f}')
print(f'  Decommissioning ($0.75M x 4):{decomm:>14,.0f}')
print(f'  Lease Liabilities (35pct Rev):{lease_liab:>14,.0f}')
print(f'  Trade Payables (12pct Rev):  {trade_pay:>14,.0f}')
print(f'  Total Liabilities:           {total_liab_seed:>14,.0f}')
print()
print('ROUND 0 PPE AND EQUITY CLOSING')
print(f'  Fixed Equity (SC + OR):      {fixed_eq:>14,.0f}')
print(f'  PPE = Liabs + FixedEq - NonPPE: {ppe_seed:>11,.0f}')
print(f'  Total Assets:                {total_assets_seed:>14,.0f}')
print(f'  Retained Earnings (residual):{re_seed:>14,.0f}')
balance_check = total_liab_seed + share_cap + re_seed + other_res
print(f'  A=L+E check: {total_assets_seed:,.0f} vs {balance_check:,.0f} diff={abs(total_assets_seed-balance_check):.2f}')
print()
print()

# Run Round 1
bs = create_initial_balance_sheet(bus)
gs = {'corporate_treasury': 47_000_000, 'group_reputation': 50, 'cost_of_capital': 0.05, 'active_event_flags': {}}
events_r1 = {'total_capex_allocated': 5_000_000, 'dividends_paid': 2_000_000, 'remediation_events': [], 'green_bond_issued': False, 'green_bond_amount': 0}

ppe_open = bs['tangible_assets']['property_plant_equipment']
rou_open = bs['tangible_assets']['right_of_use_assets']

print('ROUND 1 STEP CALCULATIONS')
print()
capex_cap = round(5_000_000 * 0.60, 2)
capex_exp = round(5_000_000 - capex_cap, 2)
depr      = round(ppe_open * 0.05, 2)
rou_dep   = round(rou_open * 0.025, 2)
total_dep = depr + rou_dep

print('STEP 1 - CAPEX Capitalisation')
print(f'  Total CAPEX invested:        {5_000_000:>14,.0f}')
print(f'  Capitalised rate:            60.00 pct')
print(f'  Amount Capitalised (to PPE): {capex_cap:>14,.0f}')
print(f'  Amount Expensed (to P&L):    {capex_exp:>14,.0f}')
print(f'  PPE before dep:              {ppe_open + capex_cap:>14,.0f}')
print()

print('STEP 2 - Depreciation')
print(f'  Opening PPE (pre-CAPEX):     {ppe_open:>14,.0f}')
print(f'  PPE Dep rate:                5.00 pct per round')
print(f'  PPE Depreciation:            {depr:>14,.0f}')
print(f'  PPE closing:                 {ppe_open + capex_cap - depr:>14,.0f}')
print(f'  Opening ROU:                 {rou_open:>14,.0f}')
print(f'  ROU Dep rate:                2.50 pct per round')
print(f'  ROU Depreciation:            {rou_dep:>14,.0f}')
print(f'  ROU closing:                 {rou_open - rou_dep:>14,.0f}')
print(f'  Total Depreciation:          {total_dep:>14,.0f}')
print()

avg_gov = (15+20+10+8)/4
dso = min(0.25, 0.12 + 0.001 * avg_gov)
dpo = min(0.18, 0.10 + 0.0005 * avg_gov)
inv_r1 = round((total_opex/365)*60, 2)
rec_r1  = round(total_rev * dso, 2)
pay_r1  = round(total_opex * dpo, 2)
tax_prov_r1 = round(max(0, (total_rev - total_opex) * 0.25 * 0.20), 2)

print('STEP 3 - Working Capital')
print(f'  Avg Gov Risk:                {avg_gov}')
print(f'  DSO factor = 0.12 + 0.001 x {avg_gov} = {dso:.4f}')
print(f'  DPO factor = 0.10 + 0.0005 x {avg_gov} = {dpo:.4f}')
print(f'  Inventory (60d OPEX/365):    {inv_r1:>14,.0f}')
print(f'  Trade Receivables:           {rec_r1:>14,.0f}')
print(f'  Trade Payables:              {pay_r1:>14,.0f}')
print(f'  Tax Provisions:              {tax_prov_r1:>14,.0f}')
print()

rep = 50
avg_slo_r1 = (55+48+52+60)/4
rep_factor = max(0.1, rep / 50.0)
slo_factor = max(0.1, math.sqrt(avg_slo_r1 / 50.0))
new_brand = round(max(1_000_000, brand_base * rep_factor * slo_factor), 2)
slo_cap_r1 = round(avg_slo_r1 * 200_000, 2)
rep_cap_r1 = round(rep * 300_000, 2)

print('STEP 4 - Intangible Revaluation')
print(f'  Group Rep:                   {rep}')
print(f'  Avg SLO:                     {avg_slo_r1}')
print(f'  Brand Base (fixed, stable):  {brand_base:>14,.0f}')
print(f'  Rep Factor = {rep}/50:            {rep_factor:.4f}')
print(f'  SLO Factor = sqrt({avg_slo_r1}/50): {slo_factor:.4f}')
print(f'  Brand = {brand_base:,.0f} x {rep_factor:.4f} x {slo_factor:.4f}')
print(f'  New Brand Value:             {new_brand:>14,.0f}')
print(f'  [Non-GAAP] SLO Capital:      {slo_cap_r1:>14,.0f}')
print(f'  [Non-GAAP] Rep Capital:      {rep_cap_r1:>14,.0f}')
print()

avg_ci = (45+72+38+28)/4
ci_risk = min(0.5, avg_ci / 200.0)
pathway_risk = 0.10
total_risk = ci_risk + pathway_risk
ppe_r1_closing = ppe_open + capex_cap - depr
stranded = round(ppe_r1_closing * total_risk, 2)

print('STEP 5 - Stranded Asset Exposure')
print(f'  Avg Carbon Intensity:        {avg_ci}')
print(f'  CI Risk = {avg_ci}/200:           {ci_risk:.4f}')
print(f'  Pathway Risk (activist):     {pathway_risk:.4f}')
print(f'  Total Risk:                  {total_risk:.4f} ({total_risk*100:.1f} pct)')
print(f'  PPE (after dep):             {ppe_r1_closing:>14,.0f}')
print(f'  Stranded Exposure:           {stranded:>14,.0f}')
print()

env_r1_prov = round(max(1_000_000, 0 * 5000), 2)
lease_r1 = round(lease_liab * 0.975, 2)
decomm_acc = round(decomm * 0.03 / 2, 2)
decomm_r1 = decomm + decomm_acc

print('STEP 6 - Liability Updates')
print(f'  NCD avg:                     0 (no ecological debt yet)')
print(f'  Env Provisions:              {env_r1_prov:>14,.0f}  (floor)')
print(f'  Lease Liabilities x 0.975:   {lease_r1:>14,.0f}')
print(f'  Decomm Accretion (1.5pct):   {decomm_acc:>14,.0f}')
print(f'  Decommissioning closing:     {decomm_r1:>14,.0f}')
print()

wacc = 0.05
interest_base = round(revolving_credit * wacc / 2, 2)
interest_total = round(interest_base + decomm_acc, 2)
gross_p = total_rev - total_opex
taxable = gross_p - interest_total - total_dep - capex_exp
tax = round(max(0, taxable * 0.25), 2)
net_inc = round(taxable - tax, 2)

print('STEP 7 - Income Statement')
print(f'  Revenue:                     {total_rev:>14,.0f}')
print(f'  OPEX:                        {total_opex:>14,.0f}')
print(f'  Gross Profit:                {gross_p:>14,.0f}')
print(f'  Less Depreciation:           ({total_dep:>12,.0f})')
print(f'  Less CAPEX Expensed (40pct): ({capex_exp:>12,.0f})')
print(f'  Less Interest (5pct/2 on debt):({interest_base:>11,.0f})')
print(f'  Less Decomm Accretion:       ({decomm_acc:>12,.0f})')
print(f'  Taxable Income:              {taxable:>14,.0f}')
print(f'  Tax at 25pct:                ({tax:>12,.0f})')
print(f'  Net Income:                  {net_inc:>14,.0f}')
print(f'  Dividends (equity dist):     ({2_000_000:>12,.0f})')
print()

# Get final balance sheet from engine
bs_r1, d = process_balance_sheet_tick(bs, gs, bus, events_r1, 1)

print('STEP 8 - Balance Sheet Totals (from engine)')
print()
total_tang  = sum(bs_r1['tangible_assets'].values())
total_intang= sum(bs_r1['intangible_assets'].values())
total_curr  = sum(bs_r1['current_assets'].values())
total_ncl   = sum(bs_r1['non_current_liabilities'].values())
total_cl    = sum(bs_r1['current_liabilities'].values())
tot_a = bs_r1['total_assets']
tot_l = bs_r1['total_liabilities']
net_a = bs_r1['net_assets']

print('ASSETS:')
print(f'  PPE:                         {bs_r1["tangible_assets"]["property_plant_equipment"]:>14,.0f}')
print(f'  Inventory:                   {bs_r1["tangible_assets"]["inventory"]:>14,.0f}')
print(f'  ROU Assets:                  {bs_r1["tangible_assets"]["right_of_use_assets"]:>14,.0f}')
print(f'  Tangible Subtotal:           {total_tang:>14,.0f}')
print(f'  Brand Value:                 {bs_r1["intangible_assets"]["brand_value"]:>14,.0f}')
print(f'  IP:                          {bs_r1["intangible_assets"]["intellectual_property"]:>14,.0f}')
print(f'  Goodwill:                    {bs_r1["intangible_assets"]["goodwill"]:>14,.0f}')
print(f'  Intangible Subtotal:         {total_intang:>14,.0f}')
print(f'  Cash:                        {bs_r1["current_assets"]["cash_and_equivalents"]:>14,.0f}')
print(f'  Trade Receivables:           {bs_r1["current_assets"]["trade_receivables"]:>14,.0f}')
print(f'  Prepayments:                 {bs_r1["current_assets"]["prepayments"]:>14,.0f}')
print(f'  Current Subtotal:            {total_curr:>14,.0f}')
print(f'  TOTAL ASSETS:                {tot_a:>14,.0f}')
print()
print('LIABILITIES:')
print(f'  Revolving Credit:            {bs_r1["non_current_liabilities"]["revolving_credit_facility"]:>14,.0f}')
print(f'  Green Bonds:                 {bs_r1["non_current_liabilities"]["green_bonds_outstanding"]:>14,.0f}')
print(f'  Env Provisions:              {bs_r1["non_current_liabilities"]["environmental_provisions"]:>14,.0f}')
print(f'  Decommissioning:             {bs_r1["non_current_liabilities"]["decommissioning_obligations"]:>14,.0f}')
print(f'  Lease Liabilities:           {bs_r1["non_current_liabilities"]["lease_liabilities"]:>14,.0f}')
print(f'  NCL Subtotal:                {total_ncl:>14,.0f}')
print(f'  Trade Payables:              {bs_r1["current_liabilities"]["trade_payables"]:>14,.0f}')
print(f'  Tax Provisions:              {bs_r1["current_liabilities"]["tax_provisions"]:>14,.0f}')
print(f'  Accrued Remediation:         {bs_r1["current_liabilities"]["accrued_remediation"]:>14,.0f}')
print(f'  Short-Term Debt:             {bs_r1["current_liabilities"]["short_term_debt"]:>14,.0f}')
print(f'  CL Subtotal:                 {total_cl:>14,.0f}')
print(f'  TOTAL LIABILITIES:           {tot_l:>14,.0f}')
print()
print('EQUITY:')
print(f'  Share Capital:               {bs_r1["share_capital"]:>14,.0f}')
print(f'  Retained Earnings:           {bs_r1["retained_earnings"]:>14,.0f}')
print(f'  Other Reserves:              {bs_r1["other_reserves"]:>14,.0f}')
print(f'  TOTAL EQUITY (= Net Assets): {net_a:>14,.0f}')
print()
print(f'  Balance Check: A={tot_a:,.0f} = L+E={tot_l+net_a:,.0f}  diff={abs(tot_a-(tot_l+net_a)):.2f}')
print()
print('STEP 9 - Covenants')
ebitda = d['covenants']['ebitda']
nd     = d['covenants']['net_debt']
ratio  = d['covenants']['ratio']
print(f'  True EBITDA (GP + Dep):      {ebitda:>14,.0f}')
print(f'  Net Debt (Debt - Cash):      {nd:>14,.0f}')
print(f'  ND/EBITDA Ratio:             {ratio:>14.2f}x')
print(f'  Covenant Trigger:            {d["covenants"]["trigger_ratio"]:>14.2f}x')
print(f'  Covenant Status:             {bs_r1["covenant_status"]}')
print(f'  D/E Ratio:                   {bs_r1["debt_to_equity"]:>14.2f}x')
print(f'  Stranded Asset Exposure:     {bs_r1["stranded_asset_exposure"]:>14,.0f}')
print()
print('NON-GAAP ESG CAPITALS (not in total assets):')
print(f'  Social Licence Capital:      {bs_r1["esg_capitals"]["social_licence_capital"]:>14,.0f}')
print(f'  Reputation Capital:          {bs_r1["esg_capitals"]["reputation_capital"]:>14,.0f}')
