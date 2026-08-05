"""Phase 3 edge-case runs. Each scenario drives the same production-faithful pipeline."""
import copy, json, random, sys, os
sys.path.insert(0, "/home/claude/work/muressons-sim/backend")
os.environ.setdefault("USE_MEMORY_DB","true")
sys.path.insert(0, "/home/claude/work/audit")
import run_trace as H
from engine import process_tick
from round_logic import post_tick, run_new_engines

def one_round(gs, bus, decisions, dividends, rnd=1, paradigm="legacy_abc"):
    gs = copy.deepcopy(gs); bus = copy.deepcopy(bus)
    gs["round_number"] = rnd
    gs["pedagogical_overrides"] = dict(H.PED_OVERRIDES)
    res = process_tick(current_global=copy.deepcopy(gs), current_bus=copy.deepcopy(bus),
                       decisions=decisions, dividends_paid=dividends, crisis_severity=20.0,
                       imitation_decay_rate=0.10, decision_paradigm=paradigm)
    ng, nb, ev = res["global_state"], res["bu_states"], res["events"]
    ng.setdefault("active_event_flags", {})["stochastic_seed"] = "edge"
    ng["pedagogical_overrides"] = dict(H.PED_OVERRIDES)
    post_tick(round_number=rnd, global_state=ng, bu_states=nb, decisions=decisions,
              events=ev, previous_flags=dict(gs.get("active_event_flags", {})), decision_paradigm=paradigm)
    ev["decisions_raw"] = decisions
    ev["dividends_paid"] = dividends
    run_new_engines(round_number=rnd, global_state=ng, bu_states=nb, events=ev)
    return ng, nb, ev

random.seed(42)

print("═"*100)
print("EDGE 1 — Dividends requested ($30M) far above treasury ($2M)")
gs = H.make_initial_global(); gs["corporate_treasury"] = 2_000_000
bus = H.make_initial_bus()
ng, nb, ev = one_round(gs, bus, H.decisions_for(1, bus), dividends=30_000_000)
bsd = None
for k in ("balance_sheet",):
    pass
bs = ng.get("balance_sheet", {})
inc = None
# find BS diag income statement from events? run_new_engines returns extra; simpler: read bs history
hist = bs.get("balance_sheet_history", [])
print(" engine: dividends_clamped:", ev.get("dividends_clamped"), " effective paid:", ev.get("last_dividends_paid"))
print(" BS history last: dividends recorded =", hist[-1]["dividends"] if hist else None,
      " net_income =", hist[-1]["net_income"] if hist else None)
print(" treasury close:", ng["corporate_treasury"])

print()
print("═"*100)
print("EDGE 2 — Zero revenue for a round (all revenue_base = 0)")
gs = H.make_initial_global()
bus = H.make_initial_bus()
for b in bus: b["revenue_base"] = 0
ng, nb, ev = one_round(gs, bus, H.decisions_for(1, bus), dividends=0)
bs = ng.get("balance_sheet", {}); hist = bs.get("balance_sheet_history", [])
if hist:
    h = hist[-1]
    print(" NI:", h["net_income"], " A:", h["total_assets"], " L:", h["total_liabilities"], " RE:", h["retained_earnings"])
    print(" AR:", h["current_assets"]["trade_receivables"], " inventory:", h["tangible_assets"]["inventory"],
          " cash:", h["current_assets"]["cash_and_equivalents"])
print(" treasury close:", ng["corporate_treasury"])

print()
print("═"*100)
print("EDGE 3 — Team submits nothing (decisions = [])")
gs = H.make_initial_global(); bus = H.make_initial_bus()
try:
    ng, nb, ev = one_round(gs, bus, [], dividends=0)
    bs = ng.get("balance_sheet", {}); hist = bs.get("balance_sheet_history", [])
    h = hist[-1] if hist else {}
    print(" OK — treasury:", ng["corporate_treasury"], " A:", h.get("total_assets"), " NI:", h.get("net_income"),
          " balanced resid:", round(h.get("total_assets",0)-h.get("total_liabilities",0)
            -(h.get("share_capital",0)+h.get("other_reserves",0)+h.get("retained_earnings",0)),2))
except Exception as e:
    print(" RAISED:", type(e).__name__, e)

print()
print("═"*100)
print("EDGE 4 — 20-round horizon, zero capex: does PP&E ever fully depreciate / go negative?")
def no_capex(rnd, bus):
    return [{"bu_id": b["bu_id"], "investment_ratio": 0.3, "capex_allocated": 0,
             "choice_selected": "option_b"} for b in bus]
tr = H.run(dividends_fn=lambda r: 0, decisions_fn=no_capex, n_rounds=20, tag="nocapex")
last = tr["rounds"][-1]["bs_close"]
ppes = [r["bs_close"]["tangible_assets"]["property_plant_equipment"] for r in tr["rounds"]]
print(" PP&E r1..r20:", [round(p/1e6,2) for p in ppes])
print(" min PP&E:", min(ppes), " negative?", any(p<0 for p in ppes))
rous = [r["bs_close"]["tangible_assets"]["right_of_use_assets"] for r in tr["rounds"]]
print(" ROU r20:", round(rous[-1],2), " lease liab r20:", round(tr["rounds"][-1]["bs_close"]["non_current_liabilities"]["lease_liabilities"],2))

print()
print("═"*100)
print("EDGE 5 — Round-number overflow / final round: r10 terminal valuation on deep-insolvent state")
from terminal_valuation import calculate_mr, calculate_terminal_value, determine_archetype
T = json.load(open("/home/claude/work/audit/trace_base.json"))
last_r = T["rounds"][-1]
bus_final = last_r["bus_close"]
# minimal reconstruction using engine state
flags = {}
mr = calculate_mr(flags=flags, avg_slo=40, avg_burnout=60, workforce_readiness=40, synergy_multiplier=0.5)
mr_v = mr["mr"] if isinstance(mr, dict) else mr
tv = calculate_terminal_value([{"revenue_base": b["revenue_base"], "opex_base": b["opex_base"], "carbon_intensity": 50} for b in bus_final], mr_v)
print(" M_R:", mr_v, " TV:", tv if not isinstance(tv, dict) else {k: tv[k] for k in list(tv)[:6]})

print()
print("═"*100)
print("EDGE 6 — Dividend paid while retained earnings already negative (r6 state): any guard?")
gs = H.make_initial_global(); gs["corporate_treasury"] = 10_000_000
bus = H.make_initial_bus()
# force negative RE by seeding a BS with negative RE via a prior loss-making tick
for b in bus: b["opex_base"] = b["revenue_base"] + 5_000_000   # heavy losses
ng, nb, ev = one_round(gs, bus, H.decisions_for(1, bus), dividends=0)
bs1 = ng.get("balance_sheet", {})
print(" RE after loss round:", bs1.get("retained_earnings"))
ng2, nb2, ev2 = one_round(ng, nb, H.decisions_for(2, nb), dividends=5_000_000, rnd=2)
bs2 = ng2.get("balance_sheet", {}); h2 = bs2.get("balance_sheet_history", [])[-1]
print(" dividends recorded r2:", h2["dividends"], " clamped?:", ev2.get("dividends_clamped"),
      " RE r2:", bs2.get("retained_earnings"), " treasury:", ng2["corporate_treasury"])
