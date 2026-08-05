"""
Audit harness — drives the REAL pipeline exactly as tests/test_financial_golden_trace.py
does (which itself replicates router.commit_turn):
    process_tick -> seed re-inject -> post_tick -> run_new_engines -> reporting resync
and captures, per round:
    - opening & closing balance sheet (full deep copies)
    - balance-sheet diagnostics (income statement, capex, depreciation, sweeps)
    - treasury before/after, consequence waterfall
Writes JSON for the reconciliation pass.
"""
from __future__ import annotations
import copy, json, os, random, sys
sys.path.insert(0, "/home/claude/work/muressons-sim/backend")
os.environ.setdefault("USE_MEMORY_DB", "true")

from engine import process_tick
from round_logic import post_tick, run_new_engines

SEED = 20260802
N_ROUNDS = 10

PED_OVERRIDES = {"black_swan_events_enabled": False, "decision_timer_enabled": False}

def make_initial_global():
    return {
        "round_number": 1,
        "corporate_treasury": 50_000_000,
        "group_reputation": 60.0,
        "synergy_multiplier": 0.35,
        "cost_of_capital": 0.05,
        "active_event_flags": {"stochastic_seed": f"audit-{SEED}"},
        "historical_ebitda": 0,
        "tco2e_emissions": 0,
        "green_transition_fund": 0,
        "tipping_point_active": False,
        "workforce_readiness": 50.0,
        "momentum_history": [],
        "pending_capex_projects": [],
    }

def make_initial_bus():
    configs = {
        "pharma":         {"revenue_base": 20_000_000, "opex_base": 12_000_000, "carbon_intensity": 35},
        "electronics":    {"revenue_base": 18_000_000, "opex_base": 11_000_000, "carbon_intensity": 55},
        "consumer_goods": {"revenue_base": 15_000_000, "opex_base":  9_000_000, "carbon_intensity": 40},
        "software":       {"revenue_base": 22_000_000, "opex_base":  8_000_000, "carbon_intensity": 15},
    }
    return [
        {"bu_id": b, "revenue_base": c["revenue_base"], "opex_base": c["opex_base"],
         "reputation_score": 60.0, "social_license_score": 55.0,
         "governance_risk_score": 20.0, "natural_capital_debt": 50.0,
         "carbon_intensity": c["carbon_intensity"], "water_dependency": 30.0,
         "staff_burnout_index": 15.0, "risk_factors": {"top_investment_streak": 0},
         "consecutive_zero_rounds": 0}
        for b, c in configs.items()
    ]

CHOICE = {1:"option_b",2:"option_a",3:"option_c",4:"option_a",5:"option_b",
          6:"option_c",7:"option_a",8:"option_b",9:"option_c",10:"option_a"}
INVEST = {"pharma":0.9,"electronics":0.7,"consumer_goods":0.5,"software":0.3}
CAPEX  = {"pharma":500_000,"electronics":0,"consumer_goods":250_000,"software":100_000}

def decisions_for(rnd, bus):
    return [{"bu_id": bu["bu_id"], "investment_ratio": INVEST.get(bu["bu_id"],0.3),
             "capex_allocated": CAPEX.get(bu["bu_id"],1_000_000),
             "choice_selected": CHOICE.get(rnd,"option_b")} for bu in bus]

def resync(gs, bus):
    gs["historical_ebitda"] = round(sum((b.get("revenue_base") or 0)-(b.get("opex_base") or 0) for b in bus),2)
    gs["tco2e_emissions"]   = round(sum((b.get("carbon_intensity") or 0)*(b.get("revenue_base") or 0)/1e6 for b in bus),1)

def bs_copy(gs):
    bs = gs.get("balance_sheet")
    if bs is None: return None
    c = copy.deepcopy(bs)
    c.pop("balance_sheet_history", None)
    return c

def run(dividends_fn=None, decisions_fn=None, n_rounds=N_ROUNDS, tag="base"):
    random.seed(SEED)
    gs, bus = make_initial_global(), make_initial_bus()
    prev_flags = dict(gs["active_event_flags"])
    out = []
    for rnd in range(1, n_rounds+1):
        gs["round_number"] = rnd
        gs["pedagogical_overrides"] = dict(PED_OVERRIDES)
        decs = (decisions_fn or decisions_for)(rnd, bus)
        div  = (dividends_fn(rnd) if dividends_fn else (500_000 if rnd > 1 else 0))
        rec = {"round": rnd, "dividends_requested": div,
               "treasury_open": gs.get("corporate_treasury"),
               "bs_open": bs_copy(gs)}
        res = process_tick(current_global=copy.deepcopy(gs), current_bus=copy.deepcopy(bus),
                           decisions=decs, dividends_paid=div, crisis_severity=20.0,
                           imitation_decay_rate=0.10, decision_paradigm="legacy_abc")
        ng, nb, ev = res["global_state"], res["bu_states"], res["events"]
        ng.setdefault("active_event_flags", {})["stochastic_seed"] = f"audit-{SEED}"
        ng["pedagogical_overrides"] = dict(PED_OVERRIDES)
        rec["treasury_after_tick"] = ng.get("corporate_treasury")
        rec["waterfall"] = copy.deepcopy(ev.get("consequence_waterfall"))
        post_tick(round_number=rnd, global_state=ng, bu_states=nb, decisions=decs,
                  events=ev, previous_flags=prev_flags, decision_paradigm="legacy_abc")
        rec["treasury_after_post_tick"] = ng.get("corporate_treasury")
        # Replicate router.py:2543-2544 (production wiring for the BS engine)
        ev["decisions_raw"] = decs
        ev["dividends_paid"] = div
        extra = run_new_engines(round_number=rnd, global_state=ng, bu_states=nb, events=ev)
        resync(ng, nb)
        rec["treasury_close"] = ng.get("corporate_treasury")
        rec["bs_close"] = bs_copy(ng)
        rec["bs_diag"] = copy.deepcopy(extra.get("balance_sheet"))
        rec["dividends_paid_effective"] = ev.get("dividends_paid", div)
        rec["events_fin"] = {k: ev.get(k) for k in (
            "loan_principal","loan_interest_payment","loan_interest_rate",
            "capex_capped","capex_overrun_amount","dividends_clamped",
            "negative_treasury_interest_applied","bailout_applied","green_fund_used")}
        rec["bus_close"] = [{k: b.get(k) for k in ("bu_id","revenue_base","opex_base","governance_risk_score")} for b in nb]
        hist = (ng.get("balance_sheet") or {}).get("balance_sheet_history", [])
        rec["bs_hist_last"] = copy.deepcopy(hist[-1]) if hist else None
        out.append(rec)
        prev_flags = dict(ng.get("active_event_flags") or {})
        gs, bus = ng, nb
    return {"tag": tag, "rounds": out}

if __name__ == "__main__":
    trace = run()
    with open("/home/claude/work/audit/trace_base.json","w") as f:
        json.dump(trace, f, indent=1, default=str)
    print("rounds captured:", len(trace["rounds"]))
    r1 = trace["rounds"][0]
    print("r1 treasury open/close:", r1["treasury_open"], r1["treasury_close"])
    print("r1 bs_close totals:", r1["bs_close"]["total_assets"], r1["bs_close"]["total_liabilities"], r1["bs_close"]["net_assets"])
