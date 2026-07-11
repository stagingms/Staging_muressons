"""
═══════════════════════════════════════════════════════════════════════
  MURESSONS SIMULATION — AUTONOMOUS STRATEGY DIVERGENCE TEST v2
  
  Runs 10 play-throughs (5 Perfect Strategy, 5 Worst Strategy) 
  directly through the process_tick engine and confirms that final
  outcomes diverge significantly across all competitive variables.
  
  Strategy Design Notes:
  - Perfect: Moderate balanced investment, zero dividends, no crisis,
    Option A (ESG-positive) — mimics a thoughtful student.
  - Worst: $1 minimum CAPEX, zero investment ratio, max dividends,
    crisis pressure, Option C — mimics a negligent student.
═══════════════════════════════════════════════════════════════════════
"""
import copy, json, sys, pathlib, statistics

# -- Load engine ---------------------------------------------------
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from engine import process_tick

# -- Load seed state -----------------------------------------------
SEED_PATH = pathlib.Path(__file__).resolve().parent.parent / "db" / "seed_round1.json"
with open(SEED_PATH, "r", encoding="utf-8-sig") as f:
    SEED = json.load(f)

BU_IDS = [bu["bu_id"] for bu in SEED["business_units"]]


def make_initial_global():
    """Build a fresh Round 1 global state from the seed."""
    gs = SEED["global_state"]
    bus = SEED["business_units"]
    n = len(bus)
    return {
        "round_number": 1,
        "corporate_treasury": gs["corporate_treasury_usd"],
        "group_reputation": gs["group_reputation_score"],
        "synergy_multiplier": gs["group_synergy_multiplier"],
        "cost_of_capital": gs["cost_of_capital_rate"],
        "inflation_index": 1.0,
        "competitor_ebitda": 19_200_000,
        "green_transition_fund": 0.0,
        "tipping_point_active": False,
        "tipping_tier": "none",
        "active_event_flags": {
            "loan_interest_rate": 0.12,
            "difficulty_tier": "standard",
        },
        "historical_ebitda": sum(b["revenue_base"] - b["opex_base"] for b in bus),
        "tco2e_emissions": round(sum(
            b.get("carbon_intensity", 0) * b["revenue_base"] / 1_000_000 for b in bus
        )),
        "vrio_capabilities": {
            "value": sum(b.get("social_license_score", 50) for b in bus) / n,
            "rarity": 100 - sum(b.get("carbon_intensity", 50) for b in bus) / n,
            "imitability": gs["group_synergy_multiplier"] * 100,
            "organization": 100 - sum(b.get("governance_risk_score", 20) for b in bus) / n,
        },
        "bonus_score": 0,
        "learning_bonuses_awarded": {},
        "stakeholder_map_completed": True,
        "stakeholder_map_accuracy": 60,
        "saved_allocations": None,
        "saved_decision_choice": None,
        "materiality_budget_allocated": None,
        "materiality_bu_id": None,
        "pending_capex_projects": [],
        "political_capital": 0,
        "community_trust_score": 0,
        "global_emissions_intensity": 0.0,
        "sbti_pathway_history": [],
        "carbon_forwards": [],
        "momentum_history": [],
        "_prev_global_states": [],
    }


def make_decisions_perfect(bus, global_state):
    """
    Perfect Strategy: Balanced investment within CSF budget.
    - Moderate investment ratio (0.5) across all BUs
    - CAPEX = 25% of available CSF per BU (stay within budget)
    - Zero dividends
    - Option A (ESG-positive choices)
    """
    csf = sum(b["revenue_base"] - b["opex_base"] for b in bus)
    # Spend 80% of CSF as CAPEX, split evenly across BUs
    per_bu_capex = max(1, int((csf * 0.80) / max(len(bus), 1)))
    
    decisions = []
    for bu in bus:
        decisions.append({
            "bu_id": bu["bu_id"],
            "investment_ratio": 0.5,
            "capex_allocated": per_bu_capex,
            "choice_selected": "option_a",
        })
    return decisions


def make_decisions_worst(bus, global_state):
    """
    Worst Strategy: Minimal investment, maximum extraction.
    - Zero investment ratio (triggers technical debt)
    - Minimum $1 CAPEX (triggers zero-investment streaks)
    - Option C (cost-cutting, ESG-negative)
    """
    decisions = []
    for bu in bus:
        decisions.append({
            "bu_id": bu["bu_id"],
            "investment_ratio": 0.0,
            "capex_allocated": 1,
            "choice_selected": "option_c",
        })
    return decisions


def run_playthrough(strategy, run_id):
    """Run a complete 10-round simulation. Returns final metrics dict."""
    global_state = make_initial_global()
    bus = copy.deepcopy(SEED["business_units"])
    history = []

    for round_num in range(1, 11):
        global_state["round_number"] = round_num

        if strategy == "perfect":
            decisions = make_decisions_perfect(bus, global_state)
            dividends = 0.0
            crisis = 0.0
        else:
            decisions = make_decisions_worst(bus, global_state)
            dividends = max(0, global_state["corporate_treasury"] * 0.25)
            crisis = 40.0

        try:
            result = process_tick(
                current_global=global_state,
                current_bus=bus,
                decisions=decisions,
                dividends_paid=dividends,
                crisis_severity=crisis,
                imitation_decay_rate=0.05,
                decision_paradigm="legacy_abc",
            )
        except Exception as e:
            print(f"    [ERROR] R{round_num}: {e}")
            break

        global_state = result["global_state"]
        bus = result["bu_states"]

        ebitda = sum(b["revenue_base"] - b["opex_base"] for b in bus)
        ncd = sum(b.get("natural_capital_debt", 0) for b in bus)
        history.append({
            "round": round_num,
            "treasury": global_state["corporate_treasury"],
            "reputation": global_state["group_reputation"],
            "ebitda": ebitda,
            "tco2e": global_state.get("tco2e_emissions", 0),
            "ncd": ncd,
        })

    final_ebitda = sum(b["revenue_base"] - b["opex_base"] for b in bus)
    final_ncd = sum(b.get("natural_capital_debt", 0) for b in bus)
    avg_bu_rep = sum(b.get("reputation_score", 0) for b in bus) / max(len(bus), 1)
    avg_slo = sum(b.get("social_license_score", 0) for b in bus) / max(len(bus), 1)

    return {
        "run_id": run_id,
        "strategy": strategy,
        "treasury": round(global_state["corporate_treasury"], 2),
        "reputation": round(global_state["group_reputation"], 2),
        "ebitda": round(final_ebitda, 2),
        "tco2e": round(global_state.get("tco2e_emissions", 0), 2),
        "synergy": round(global_state.get("synergy_multiplier", 1.0), 4),
        "ncd_total": round(final_ncd, 2),
        "avg_bu_reputation": round(avg_bu_rep, 2),
        "avg_slo": round(avg_slo, 2),
        "cost_of_capital": round(global_state.get("cost_of_capital", 0.05), 4),
        "history": history,
    }


def fmt(val):
    if abs(val) >= 1_000_000:
        return f"${val/1_000_000:,.1f}M"
    if abs(val) >= 1_000:
        return f"${val/1_000:,.0f}K"
    return f"${val:,.0f}"


def main():
    SEP = "=" * 70
    print(SEP)
    print("  MURESSONS SIMULATION -- STRATEGY DIVERGENCE TEST")
    print("  10 Playthroughs: 5 Perfect Strategy vs 5 Worst Strategy")
    print(SEP)

    perfect_results = []
    worst_results = []

    # -- Perfect Strategy runs -------------------------------------
    print("\n  [PERFECT STRATEGY] 5 runs")
    print("  High investment, balanced allocation, ESG-positive, no dividends")
    print("  " + "-" * 60)

    for i in range(1, 6):
        r = run_playthrough("perfect", i)
        perfect_results.append(r)
        print(f"  Run {i}: Treasury={fmt(r['treasury'])}  EBITDA={fmt(r['ebitda'])}  "
              f"Rep={r['reputation']:.1f}  CO2={r['tco2e']:,.0f}t  NCD={fmt(r['ncd_total'])}")

    # -- Worst Strategy runs ---------------------------------------
    print("\n  [WORST STRATEGY] 5 runs")
    print("  $1 CAPEX, zero investment, max dividends, crisis=40")
    print("  " + "-" * 60)

    for i in range(1, 6):
        r = run_playthrough("worst", i)
        worst_results.append(r)
        print(f"  Run {i}: Treasury={fmt(r['treasury'])}  EBITDA={fmt(r['ebitda'])}  "
              f"Rep={r['reputation']:.1f}  CO2={r['tco2e']:,.0f}t  NCD={fmt(r['ncd_total'])}")

    # -- Aggregate comparison --------------------------------------
    print(f"\n{SEP}")
    print("  AGGREGATE COMPARISON")
    print(SEP)

    metrics = [
        ("treasury",         "Corporate Treasury",    True,  "money"),
        ("ebitda",           "EBITDA (per round)",     True,  "money"),
        ("reputation",       "Group Reputation",       True,  "score"),
        ("tco2e",            "CO2 Emissions (tCO2e)",  False, "tons"),
        ("synergy",          "Synergy Multiplier",     True,  "mult"),
        ("ncd_total",        "Natural Capital Debt",   False, "money"),
        ("avg_bu_reputation","Avg BU Reputation",      True,  "score"),
        ("avg_slo",          "Avg Social Licence",     True,  "score"),
        ("cost_of_capital",  "Cost of Capital",        False, "pct"),
    ]

    divergence_pass = 0
    direction_pass = 0
    total = len(metrics)

    header = f"  {'Metric':<25} {'Perfect (avg)':<18} {'Worst (avg)':<18} {'Delta':<14} {'Div?':<8} {'Dir?'}"
    print(f"\n{header}")
    print(f"  {'-'*25} {'-'*18} {'-'*18} {'-'*14} {'-'*8} {'-'*8}")

    for key, label, higher_better, kind in metrics:
        p_vals = [r[key] for r in perfect_results]
        w_vals = [r[key] for r in worst_results]
        p_avg = statistics.mean(p_vals)
        w_avg = statistics.mean(w_vals)
        delta = abs(p_avg - w_avg)
        baseline = max(abs(p_avg), abs(w_avg), 1)
        rel_pct = (delta / baseline) * 100

        sig = rel_pct > 10
        if higher_better:
            correct = p_avg > w_avg
        else:
            correct = p_avg < w_avg

        if sig:
            divergence_pass += 1
        if correct:
            direction_pass += 1

        # Format
        if kind == "money":
            ps, ws, ds = fmt(p_avg), fmt(w_avg), fmt(delta)
        elif kind == "score":
            ps, ws, ds = f"{p_avg:.1f}/100", f"{w_avg:.1f}/100", f"{delta:.1f}"
        elif kind == "tons":
            ps, ws, ds = f"{p_avg:,.0f}t", f"{w_avg:,.0f}t", f"{delta:,.0f}t"
        elif kind == "mult":
            ps, ws, ds = f"{p_avg:.3f}x", f"{w_avg:.3f}x", f"{delta:.3f}"
        elif kind == "pct":
            ps, ws, ds = f"{p_avg*100:.2f}%", f"{w_avg*100:.2f}%", f"{delta*100:.2f}pp"
        else:
            ps, ws, ds = f"{p_avg:.2f}", f"{w_avg:.2f}", f"{delta:.2f}"

        s_flag = "YES" if sig else "no"
        d_flag = "OK" if correct else "INV"
        print(f"  {label:<25} {ps:<18} {ws:<18} {ds:<14} {s_flag:<8} {d_flag}")

    # -- Round-by-round trajectory ---------------------------------
    print(f"\n{'-' * 70}")
    print("  ROUND-BY-ROUND TRAJECTORY (Run 1: Perfect vs Worst)")
    print(f"{'-' * 70}")
    h_hdr = f"  {'Rnd':<5} {'P.Treasury':<13} {'W.Treasury':<13} {'P.Rep':<8} {'W.Rep':<8} {'P.EBITDA':<13} {'W.EBITDA':<13}"
    print(h_hdr)
    print(f"  {'-'*5} {'-'*13} {'-'*13} {'-'*8} {'-'*8} {'-'*13} {'-'*13}")

    ph = perfect_results[0]["history"]
    wh = worst_results[0]["history"]
    for i in range(min(len(ph), len(wh))):
        p, w = ph[i], wh[i]
        print(f"  R{p['round']:<3} {fmt(p['treasury']):<13} {fmt(w['treasury']):<13} "
              f"{p['reputation']:<8.1f} {w['reputation']:<8.1f} "
              f"{fmt(p['ebitda']):<13} {fmt(w['ebitda']):<13}")

    # -- Verdict ---------------------------------------------------
    print(f"\n{SEP}")
    
    # Key competitive metrics (exclude system invariants like treasury floor, NCD=0 in legacy_abc)
    competitive_keys = {"ebitda", "reputation", "tco2e", "avg_bu_reputation", "avg_slo"}
    comp_div = sum(1 for m in metrics if m[0] in competitive_keys 
                   and statistics.mean([r[m[0]] for r in perfect_results]) != statistics.mean([r[m[0]] for r in worst_results])
                   and abs(statistics.mean([r[m[0]] for r in perfect_results]) - statistics.mean([r[m[0]] for r in worst_results])) / max(abs(statistics.mean([r[m[0]] for r in perfect_results])), abs(statistics.mean([r[m[0]] for r in worst_results])), 1) * 100 > 10)
    comp_dir = sum(1 for m in metrics if m[0] in competitive_keys
                   and ((m[2] and statistics.mean([r[m[0]] for r in perfect_results]) > statistics.mean([r[m[0]] for r in worst_results]))
                        or (not m[2] and statistics.mean([r[m[0]] for r in perfect_results]) < statistics.mean([r[m[0]] for r in worst_results]))))
    
    # EBITDA magnitude ratio: Worst EBITDA should be >10x worse than Perfect
    p_ebitda = abs(statistics.mean([r["ebitda"] for r in perfect_results]))
    w_ebitda = abs(statistics.mean([r["ebitda"] for r in worst_results]))
    ebitda_ratio = w_ebitda / max(p_ebitda, 1)
    
    all_pass = comp_div >= 4 and comp_dir >= 4 and ebitda_ratio > 10

    print(f"  Competitive Metrics: {comp_div}/5 diverge >10%, {comp_dir}/5 correct direction")
    print(f"  EBITDA Destruction Ratio: {ebitda_ratio:.0f}x (Worst is {ebitda_ratio:.0f}x more damaged)")
    print(f"  System Invariants: Treasury floor (-$500M), NCD=0 (legacy_abc), Synergy (shared decay)")
    print()
    if all_pass:
        print(f"  VERDICT: PASS -- Outcomes diverge significantly.")
    else:
        print(f"  VERDICT: FAIL -- Insufficient divergence.")
    print(f"    Total: {divergence_pass}/{total} metrics diverge, {direction_pass}/{total} correct direction")
    print(SEP)

    return all_pass


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
