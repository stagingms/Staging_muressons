"""Phase 1 reconciliation pass over trace_base.json. All numbers computed, none asserted from memory."""
import json, sys
sys.path.insert(0, "/home/claude/work/muressons-sim/backend")
import os; os.environ.setdefault("USE_MEMORY_DB","true")

T = json.load(open("/home/claude/work/audit/trace_base.json"))
rounds = T["rounds"]

def eq_residual(bs):
    equity = bs["share_capital"] + bs["other_reserves"] + bs["retained_earnings"]
    return round(bs["total_assets"] - bs["total_liabilities"] - equity, 2)

def recomputed_totals(bs):
    ta = sum(bs["tangible_assets"].values()) + sum(bs["intangible_assets"].values()) + sum(bs["current_assets"].values())
    tl = sum(bs["non_current_liabilities"].values()) + sum(bs["current_liabilities"].values())
    return round(ta,2), round(tl,2)

print("="*110)
print("TEST 1 — Fundamental identity A = L + E, and stored totals vs recomputed sums (per round)")
print(f"{'rnd':>3} {'A':>16} {'L':>16} {'E':>16} {'A-L-E':>10} {'A(recomp)-A(stored)':>20} {'L(recomp)-L(stored)':>20}")
for r in rounds:
    bs = r["bs_close"]
    ta_r, tl_r = recomputed_totals(bs)
    print(f"{r['round']:>3} {bs['total_assets']:>16,.2f} {bs['total_liabilities']:>16,.2f} "
          f"{bs['share_capital']+bs['other_reserves']+bs['retained_earnings']:>16,.2f} "
          f"{eq_residual(bs):>10,.2f} {round(ta_r-bs['total_assets'],2):>20,.2f} {round(tl_r-bs['total_liabilities'],2):>20,.2f}")

print()
print("="*110)
print("TEST 2 — Retained earnings roll-forward: RE_open + NI - dividends = RE_close?")
print(f"{'rnd':>3} {'RE_open':>16} {'NI':>14} {'div':>10} {'expected RE':>16} {'RE_close':>16} {'RESIDUAL':>16}")
# reconstruct round-1 opening BS
from balance_sheet import create_initial_balance_sheet
for i, r in enumerate(rounds):
    bs_open = r["bs_open"]
    if bs_open is None:
        continue  # r1 opening handled separately below
    ni  = r["bs_diag"]["income_statement"]["net_income"]
    div = r["bs_diag"]["income_statement"]["dividends_as_equity_distribution"]
    re_open, re_close = bs_open["retained_earnings"], r["bs_close"]["retained_earnings"]
    exp = round(re_open + ni - div, 2)
    print(f"{r['round']:>3} {re_open:>16,.2f} {ni:>14,.2f} {div:>10,.2f} {exp:>16,.2f} {re_close:>16,.2f} {round(re_close-exp,2):>16,.2f}")

print()
print("="*110)
print("TEST 3 — Cash: BS cash vs treasury; waterfall coverage")
print(f"{'rnd':>3} {'treas_open':>15} {'treas_close':>15} {'bs_cash':>15} {'cash==max(0,T)':>15} {'wf_final':>15} {'post-wf drift':>14}")
for r in rounds:
    bs = r["bs_close"]; cash = bs["current_assets"]["cash_and_equivalents"]
    wf = r["waterfall"] or {}
    wf_final = wf.get("final_treasury")
    ok = abs(cash - max(0.0, r["treasury_close"])) < 0.01
    drift = round(r["treasury_close"] - wf_final, 2) if wf_final is not None else None
    print(f"{r['round']:>3} {r['treasury_open']:>15,.2f} {r['treasury_close']:>15,.2f} {cash:>15,.2f} {str(ok):>15} "
          f"{wf_final:>15,.2f} {drift:>14,.2f}")

print()
print("="*110)
print("TEST 4 — PP&E roll-forward: PPE_open + capex_capitalised - dep_ppe = PPE_close  (dep_ppe = 5% of PPE_open)")
print(f"{'rnd':>3} {'PPE_open':>16} {'capex_cap':>12} {'dep_ppe':>12} {'expected':>16} {'PPE_close':>16} {'RESID':>10}")
for r in rounds:
    if r["bs_open"] is None: continue
    ppe_o = r["bs_open"]["tangible_assets"]["property_plant_equipment"]
    ppe_c = r["bs_close"]["tangible_assets"]["property_plant_equipment"]
    cap   = r["bs_diag"]["capex_capitalised"]
    dep_ppe = round(ppe_o*0.05,2)
    exp = round(ppe_o + cap - dep_ppe, 2)
    print(f"{r['round']:>3} {ppe_o:>16,.2f} {cap:>12,.2f} {dep_ppe:>12,.2f} {exp:>16,.2f} {ppe_c:>16,.2f} {round(ppe_c-exp,2):>10,.2f}")

print()
print("="*110)
print("TEST 5 — Debt roll: revolver static?  green bonds?  short-term debt = swept deficit?")
for r in rounds:
    bs = r["bs_close"]
    ncl = bs["non_current_liabilities"]; cl = bs["current_liabilities"]
    swept = (r["bs_diag"] or {}).get("negative_cash_swept_to_short_term_debt", 0)
    print(f" r{r['round']}: revolver={ncl['revolving_credit_facility']:,.0f} green_bonds={ncl['green_bonds_outstanding']:,.0f} "
          f"STD={cl['short_term_debt']:,.2f} swept_diag={swept} lease_liab={ncl['lease_liabilities']:,.2f}")

print()
print("="*110)
print("TEST 6 — Working capital lines: recompute from closing BU table (formula-driven, not roll-forward)")
for r in rounds:
    bs = r["bs_close"]
    rev = sum(b["revenue_base"] for b in r["bus_close"]); opx = sum(b["opex_base"] for b in r["bus_close"])
    gov = sum(b["governance_risk_score"] for b in r["bus_close"])/len(r["bus_close"])
    inv_exp = round(opx/365*60,2)
    dso = min(0.25, 0.12+0.001*gov); ar_exp = round(rev*dso,2)
    dpo = min(0.18, 0.10+0.0005*gov); ap_exp = round(opx*dpo,2)
    inv = bs["tangible_assets"]["inventory"]; ar = bs["current_assets"]["trade_receivables"]; ap = bs["current_liabilities"]["trade_payables"]
    print(f" r{r['round']}: inv resid={round(inv-inv_exp,2):>12,.2f}  AR resid={round(ar-ar_exp,2):>12,.2f}  AP resid={round(ap-ap_exp,2):>12,.2f}")

print()
print("="*110)
print("TEST 7 — Income statement internal arithmetic + interest & tax recompute")
for r in rounds:
    d = r["bs_diag"]["income_statement"]; bs = r["bs_close"]
    taxable_exp = round(d["gross_profit"] - d["interest_expense"] - d["depreciation"] - d["capex_expensed"],2)
    ni_exp = round(d["taxable_income"] - d["tax_charge"],2)
    tax_exp = round(max(0, d["taxable_income"]*0.25),2)
    total_debt = (bs["non_current_liabilities"]["revolving_credit_facility"]
                  + bs["non_current_liabilities"]["green_bonds_outstanding"]
                  + bs["current_liabilities"]["short_term_debt"])
    int_exp = round(round(total_debt*d["interest_rate_used"]/2,2) + r["bs_diag"].get("decommissioning_accretion",0),2)
    tax_prov = bs["current_liabilities"]["tax_provisions"]
    tax_prov_exp = round(max(0, d["gross_profit"]*0.25*0.20),2)
    print(f" r{r['round']}: taxable resid={round(d['taxable_income']-taxable_exp,2)}  NI resid={round(d['net_income']-ni_exp,2)}  "
          f"tax resid={round(d['tax_charge']-tax_exp,2)}  interest resid={round(d['interest_expense']-int_exp,2)}  "
          f"BS tax_prov={tax_prov:,.2f} (formula {tax_prov_exp:,.2f}) vs P&L tax {d['tax_charge']:,.2f}")

print()
print("="*110)
print("TEST 8 — Cross-statement: BS P&L revenue vs waterfall CSF implied revenue; NI(hist) vs NI(diag)")
for r in rounds:
    d = r["bs_diag"]["income_statement"]
    wf = r["waterfall"] or {}
    csf_entry = next((e for e in wf.get("entries",[]) if "CSF" in e["label"]), None)
    csf = csf_entry["amount"] if csf_entry else None
    ni_hist = (r["bs_hist_last"] or {}).get("net_income")
    div_eff = r["dividends_paid_effective"]
    # CSF = gross_profit(at CSF time) - dividends  -> implied engine-side gross profit
    implied_gp = round(csf + div_eff,2) if csf is not None else None
    print(f" r{r['round']}: BS P&L gross_profit={d['gross_profit']:>14,.2f}  engine CSF-implied GP={implied_gp:>14,.2f}  "
          f"diff={round(d['gross_profit']-implied_gp,2) if implied_gp is not None else 'NA':>12}  NI(hist)==NI(diag): {ni_hist==d['net_income']}")

print()
print("="*110)
print("TEST 9 — Equity components: share capital / other reserves static?")
for r in rounds:
    bs = r["bs_close"]
    print(f" r{r['round']}: share_capital={bs['share_capital']:,.0f} other_reserves={bs['other_reserves']:,.0f}")

print()
print("TEST 10 — Round-1 opening BS (create_initial_balance_sheet on the SEED bus): does it balance?")
bus0 = [
    {"bu_id":"pharma","revenue_base":20_000_000,"opex_base":12_000_000},
    {"bu_id":"electronics","revenue_base":18_000_000,"opex_base":11_000_000},
    {"bu_id":"consumer_goods","revenue_base":15_000_000,"opex_base":9_000_000},
    {"bu_id":"software","revenue_base":22_000_000,"opex_base":8_000_000},
]
bs0 = create_initial_balance_sheet(bus0)
ta = sum(bs0["tangible_assets"].values())+sum(bs0["intangible_assets"].values())+sum(bs0["current_assets"].values())
tl = sum(bs0["non_current_liabilities"].values())+sum(bs0["current_liabilities"].values())
eq = bs0["share_capital"]+bs0["other_reserves"]+bs0["retained_earnings"]
print(f" opening: A={ta:,.2f} L={tl:,.2f} E={eq:,.2f}  A-L-E={round(ta-tl-eq,2)}  RE_seed={bs0['retained_earnings']:,.2f} PPE_seed={bs0['tangible_assets']['property_plant_equipment']:,.2f}")
