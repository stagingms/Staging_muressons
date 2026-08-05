"""Decompose the RE roll-forward residual per round: which balance-sheet movements bypass the P&L.
ΔRE = Δnet_assets (fixed equity static). Residual = ΔRE - (NI - div).
Itemise every line-item delta and tag whether it is in the P&L (NI) or in dividends."""
import json
T = json.load(open("/home/claude/work/audit/trace_base.json"))
rounds = T["rounds"]

def flat(bs):
    d = {}
    for grp in ("tangible_assets","intangible_assets","current_assets","non_current_liabilities","current_liabilities"):
        for k,v in bs[grp].items():
            d[(grp,k)] = v
    return d

for r in rounds:
    if r["bs_open"] is None: continue
    o, c = flat(r["bs_open"]), flat(r["bs_close"])
    ni  = r["bs_diag"]["income_statement"]["net_income"]
    div = r["bs_diag"]["income_statement"]["dividends_as_equity_distribution"]
    d_re = round(r["bs_close"]["retained_earnings"] - r["bs_open"]["retained_earnings"],2)
    resid = round(d_re - (ni - div),2)
    print(f"\n── Round {r['round']}: ΔRE={d_re:,.2f}  NI-div={ni-div:,.2f}  RESIDUAL={resid:,.2f}")
    keys = set(o)|set(c)
    total_delta_check = 0.0
    for k in sorted(keys):
        dv = round(c.get(k,0)-o.get(k,0),2)
        if abs(dv) < 0.005: continue
        sign = 1 if k[0] in ("tangible_assets","intangible_assets","current_assets") else -1
        total_delta_check += sign*dv
        print(f"   {'+' if sign>0 else '-'} {k[0][:4]}.{k[1]:<32} Δ={dv:>16,.2f}")
    print(f"   Σ(ΔA - ΔL) = {round(total_delta_check,2):,.2f}  (should equal ΔRE: {d_re:,.2f})")
