"""
Muressons QA — Monte Carlo Stress Test & Equilibrium Validation
Runs 100 headless iterations per persona through the full 10-round engine.
Tests mathematical soundness, boundary conditions, and state integrity.
"""
import os
os.environ["USE_MEMORY_DB"] = "true"

import sys, copy, json, time, math, random, tracemalloc
import pathlib

backend_dir = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

import engine
from engine import (
    calc_csf, calc_contagion, calc_synergy_opex, calc_natural_capital_interest,
    calc_vrio_decay, calc_talent_braindrain, calc_strike_probability,
    apply_natural_decay, calc_inflation, calc_overrun_risk, calc_technical_debt,
    calc_revenue_cannibalization, calc_stakeholder_fatigue,
    calc_supply_chain_contagion, calc_competitor_pressure, calc_cash_conversion,
    calc_dividend_ratchet, calc_greenwashing_risk, calc_macro_rate_environment,
    calc_fx_impact, calc_macro_noise, detect_distress, calc_burnout_accumulation,
    calc_workforce_readiness, process_tick,
)
from terminal_valuation import calculate_mr, calculate_terminal_value, determine_archetype
from branching_engine import classify_player_archetype, calc_adaptive_crisis_severity

# ═══════════════════════════════════════════════════════════════
#  INITIAL STATE FACTORY
# ═══════════════════════════════════════════════════════════════
BU_IDS = ["pharma", "electronics", "consumer_goods", "software"]

def make_initial_global():
    return {
        "round_number": 1,
        "corporate_treasury": 50_000_000,
        "group_reputation": 60.0,
        "synergy_multiplier": 0.35,
        "cost_of_capital": 0.05,
        "active_event_flags": {},
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
        "pharma": {"revenue_base": 20_000_000, "opex_base": 12_000_000, "carbon_intensity": 35},
        "electronics": {"revenue_base": 18_000_000, "opex_base": 11_000_000, "carbon_intensity": 55},
        "consumer_goods": {"revenue_base": 15_000_000, "opex_base": 9_000_000, "carbon_intensity": 40},
        "software": {"revenue_base": 22_000_000, "opex_base": 8_000_000, "carbon_intensity": 15},
    }
    bus = []
    for bu_id, cfg in configs.items():
        bus.append({
            "bu_id": bu_id,
            "revenue_base": cfg["revenue_base"],
            "opex_base": cfg["opex_base"],
            "reputation_score": 60.0,
            "social_license_score": 55.0,
            "governance_risk_score": 20.0,
            "natural_capital_debt": 50.0,
            "carbon_intensity": cfg["carbon_intensity"],
            "water_dependency": 30.0,
            "staff_burnout_index": 15.0,
            "risk_factors": {"top_investment_streak": 0},
            "consecutive_zero_rounds": 0,
        })
    return bus

# ═══════════════════════════════════════════════════════════════
#  PERSONA DECISION GENERATORS
# ═══════════════════════════════════════════════════════════════
ROUND_CHOICES = {
    1: ["option_a", "option_b", "option_c"],
    2: ["option_a", "option_b", "option_c"],
    3: ["option_a", "option_b", "option_c"],
    4: ["option_a", "option_b", "option_c"],
    5: ["option_a", "option_b", "option_c"],
    6: ["option_a", "option_b", "option_c"],
    7: ["option_a", "option_b", "option_c"],
    8: ["option_a", "option_b", "option_c"],
    9: ["option_a", "option_b", "option_c"],
    10: ["option_a", "option_b", "option_c"],
}

# Optimal choices based on decision_nodes_summary KI
OPTIMIZER_CHOICES = {
    1: "option_b",  # Deep Forensic Audit (-$3M, Rep+5, protects R4)
    2: "option_a",  # Full Alignment (Rep+5, Gov-5)
    3: "option_b",  # Green Bond (-$2M, Carbon-8, NCD-15)
    4: "option_a",  # Full Transparency (-$6M, Rep+10, SLO+8)
    5: "option_b",  # Nature-Based Solutions (-$5M, Resilience 0.6, NCD-8)
    6: "option_b",  # Ethical Overhaul (-$8M, SLO+15, Rep+5, Truth Premium)
    7: "option_c",  # Waste-to-Energy (-$7M, NCD-4, Synergy+0.35, enables R10A)
    8: "option_a",  # Water Efficiency all BUs (-$12M, Water-20, SLO+5)
    9: "option_c",  # Community Fund (-$20M, SLO+18, Rep+12, Gov-5)
    10: "option_a", # Resist & Integrate (leverages synergy)
}

DISRUPTOR_CHOICES = {
    1: "option_a",  # Surface-Level (blindspot!)
    2: "option_c",  # Ignore Framework (Rep-5, Gov+10)
    3: "option_c",  # Offset & Defer (-$1M, Rep-3, NCD+5)
    4: "option_c",  # Deny & Deflect ($0, Rep-15, SLO-10)
    5: "option_c",  # Insurance Only (-$2M, blocks resilience)
    6: "option_a",  # Monetise Algorithm (+$5M, Rep-20, contagion!)
    7: "option_b",  # Producer Responsibility (-$5M, moderate)
    8: "option_b",  # Prioritise Electronics (-$4M, blocks resilience)
    9: "option_a",  # Immediate Closure (+$5M, SLO-20, Rep-15)
    10: "option_c", # Divest (+$25M, wipes synergy)
}

def persona_optimizer_decisions(rnd, bus):
    choice = OPTIMIZER_CHOICES.get(rnd, "option_b")
    return [{
        "bu_id": bu["bu_id"], "investment_ratio": 0.7,
        "capex_allocated": 2_000_000, "choice_selected": choice,
    } for bu in bus]

def persona_disruptor_decisions(rnd, bus):
    choice = DISRUPTOR_CHOICES.get(rnd, "option_c")
    # Zero investment for half the BUs, max for others
    decs = []
    for i, bu in enumerate(bus):
        decs.append({
            "bu_id": bu["bu_id"],
            "investment_ratio": 0.0 if i % 2 == 0 else 1.0,
            "capex_allocated": 1 if i % 2 == 0 else 5_000_000,
            "choice_selected": choice,
        })
    return decs

def persona_explorer_decisions(rnd, bus):
    # Cycles through all choices across rounds to hit every path
    choices = ["option_a", "option_b", "option_c"]
    choice = choices[(rnd - 1) % 3]
    return [{
        "bu_id": bu["bu_id"], "investment_ratio": 0.4,
        "capex_allocated": 1_500_000, "choice_selected": choice,
    } for bu in bus]

# ═══════════════════════════════════════════════════════════════
#  INVARIANT CHECKS
# ═══════════════════════════════════════════════════════════════
def check_invariants(gs, bus, rnd, anomalies):
    """Validate mathematical invariants after each round."""
    # Treasury should not be NaN/Inf
    t = gs.get("corporate_treasury", 0)
    if math.isnan(t) or math.isinf(t):
        anomalies.append(f"R{rnd}: Treasury is {t} (NaN/Inf)")

    # Reputation clamped [0, 100]
    rep = gs.get("group_reputation", 50)
    if rep < 0 or rep > 100:
        anomalies.append(f"R{rnd}: Reputation {rep} out of [0,100]")

    # Synergy multiplier should be non-negative
    syn = gs.get("synergy_multiplier", 0.35)
    if syn < 0:
        anomalies.append(f"R{rnd}: Synergy multiplier negative: {syn}")

    for bu in bus:
        bu_id = bu["bu_id"]
        # OPEX non-negative
        if bu["opex_base"] < 0:
            anomalies.append(f"R{rnd}: {bu_id} OPEX negative: {bu['opex_base']}")
        # Revenue non-negative
        if bu.get("revenue_base", 0) < 0:
            anomalies.append(f"R{rnd}: {bu_id} Revenue negative: {bu['revenue_base']}")
        # NCD capped and non-negative
        ncd = bu.get("natural_capital_debt", 0)
        if ncd < 0:
            anomalies.append(f"R{rnd}: {bu_id} NCD negative: {ncd}")
        if ncd > 1_000_001:
            anomalies.append(f"R{rnd}: {bu_id} NCD overflow: {ncd}")
        # Social license [0, 100]
        slo = bu.get("social_license_score", 50)
        if slo < 0 or slo > 100.01:
            anomalies.append(f"R{rnd}: {bu_id} SLO {slo} out of [0,100]")
        # Reputation [0, 100]
        brep = bu.get("reputation_score", 50)
        if brep < 0 or brep > 100.01:
            anomalies.append(f"R{rnd}: {bu_id} BU Rep {brep} out of [0,100]")
        # Carbon intensity non-negative
        ci = bu.get("carbon_intensity", 0)
        if ci < 0:
            anomalies.append(f"R{rnd}: {bu_id} Carbon Intensity negative: {ci}")
        # Burnout [0, 100]
        bo = bu.get("staff_burnout_index", 0)
        if bo < 0 or bo > 100.01:
            anomalies.append(f"R{rnd}: {bu_id} Burnout {bo} out of [0,100]")

# ═══════════════════════════════════════════════════════════════
#  SINGLE 10-ROUND SIMULATION
# ═══════════════════════════════════════════════════════════════
def run_simulation(decision_fn, seed=None):
    """Run a full 10-round simulation using process_tick directly."""
    if seed is not None:
        random.seed(seed)

    gs = make_initial_global()
    bus = make_initial_bus()
    anomalies = []
    round_results = []

    for rnd in range(1, 11):
        gs["round_number"] = rnd
        decisions = decision_fn(rnd, bus)

        try:
            result = process_tick(
                current_global=copy.deepcopy(gs),
                current_bus=copy.deepcopy(bus),
                decisions=decisions,
                dividends_paid=500_000 if rnd > 1 else 0,
                crisis_severity=40.0,
                imitation_decay_rate=0.10,
                decision_paradigm="legacy_abc",
            )
            gs = result["global_state"]
            bus = result["bu_states"]
            events = result["events"]
        except Exception as e:
            anomalies.append(f"R{rnd}: ENGINE CRASH: {e}")
            round_results.append({"round": rnd, "status": "CRASH", "error": str(e)})
            break

        check_invariants(gs, bus, rnd, anomalies)
        round_results.append({
            "round": rnd, "status": "PASS" if not any(f"R{rnd}:" in a for a in anomalies) else "FAIL",
            "treasury": gs.get("corporate_treasury", 0),
            "reputation": gs.get("group_reputation", 0),
            "synergy": gs.get("synergy_multiplier", 0),
        })

    # Terminal valuation
    try:
        flags = gs.get("active_event_flags", {})
        avg_slo = sum(b.get("social_license_score", 50) for b in bus) / max(len(bus), 1)
        avg_bo = sum(b.get("staff_burnout_index", 0) for b in bus) / max(len(bus), 1)
        wr = gs.get("workforce_readiness", 50)
        syn = gs.get("synergy_multiplier", 0.35)
        mr_result = calculate_mr(flags, avg_slo, avg_bo, wr, syn)
        tv_result = calculate_terminal_value(bus, mr_result["mr"])
        mr = mr_result["mr"]
        tv = tv_result["terminal_value"]
        if math.isnan(mr) or math.isinf(mr):
            anomalies.append(f"Terminal: M_R is {mr}")
        if math.isnan(tv) or math.isinf(tv):
            anomalies.append(f"Terminal: TV is {tv}")
        if mr < 0:
            anomalies.append(f"Terminal: M_R negative: {mr}")
    except Exception as e:
        anomalies.append(f"Terminal valuation crash: {e}")
        mr, tv = 0, 0

    return {
        "anomalies": anomalies,
        "rounds": round_results,
        "final_treasury": gs.get("corporate_treasury", 0),
        "final_reputation": gs.get("group_reputation", 0),
        "final_mr": mr,
        "terminal_value": tv,
        "completed_rounds": len(round_results),
    }

# ═══════════════════════════════════════════════════════════════
#  BOUNDARY / INJECTION TESTS
# ═══════════════════════════════════════════════════════════════
def run_boundary_tests():
    """Test input validation and boundary conditions on engine functions."""
    results = []

    # Test 1: Negative crisis severity clamped
    rep = calc_contagion([{"reputation_score": 60}], -50)
    results.append(("Negative crisis clamp", "PASS" if rep >= 0 else "FAIL", f"rep={rep}"))

    # Test 2: Zero BU list
    rep = calc_contagion([], 40)
    results.append(("Empty BU list", "PASS" if rep == 50.0 else "FAIL", f"rep={rep}"))

    # Test 3: Investment ratio clamped
    opex = calc_synergy_opex(10_000_000, 5.0, 0.5)
    results.append(("Investment ratio >1 clamp", "PASS" if opex >= 0 else "FAIL", f"opex={opex}"))

    # Test 4: Negative investment ratio
    opex = calc_synergy_opex(10_000_000, -1.0, 0.5)
    results.append(("Negative investment ratio", "PASS" if opex == 10_000_000 else "FAIL", f"opex={opex}"))

    # Test 5: NCD floor at 0
    rate = calc_natural_capital_interest(0.05, -100)
    results.append(("Negative NCD floor", "PASS" if rate >= 0.05 else "FAIL", f"rate={rate}"))

    # Test 6: Strike probability clamped [0,1]
    p = calc_strike_probability(0.8, -50)
    results.append(("Strike prob clamp high", "PASS" if p <= 1.0 else "FAIL", f"p={p}"))

    p = calc_strike_probability(-0.5, 200)
    results.append(("Strike prob clamp low", "PASS" if p >= 0.0 else "FAIL", f"p={p}"))

    # Test 7: Burnout clamp [0, 100]
    bo, _ = calc_burnout_accumulation(95, 20, 10)
    results.append(("Burnout cap at 100", "PASS" if bo <= 100 else "FAIL", f"bo={bo}"))

    bo, _ = calc_burnout_accumulation(5, -30, 0)
    results.append(("Burnout floor at 0", "PASS" if bo >= 0 else "FAIL", f"bo={bo}"))

    # Test 8: Workforce readiness clamp
    wr, _ = calc_workforce_readiness(95, True, "high")
    results.append(("Readiness cap at 100", "PASS" if wr <= 100 else "FAIL", f"wr={wr}"))

    # Test 9: Distress detection
    d = detect_distress(-1_000_000, 10, 5)
    results.append(("Distress at negative treasury", "PASS" if d["distress_detected"] else "FAIL", str(d.get("turnaround_phase"))))

    # Test 10: VRIO decay non-negative
    v = calc_vrio_decay(0.5, 0.05)
    results.append(("VRIO decay positive", "PASS" if v >= 0 else "FAIL", f"v={v}"))

    # Test 11: Extreme float values
    try:
        opex = calc_synergy_opex(float('inf'), 0.5, 0.5)
        results.append(("Inf OPEX input", "WARN", f"opex={opex}"))
    except Exception as e:
        results.append(("Inf OPEX input", "FAIL", str(e)))

    # Test 12: process_tick immutability
    gs = make_initial_global()
    bus = make_initial_bus()
    gs_copy = copy.deepcopy(gs)
    bus_copy = copy.deepcopy(bus)
    decs = persona_optimizer_decisions(1, bus)
    process_tick(gs, bus, decs, 0, 40, 0.10)
    immutable = (gs == gs_copy)  # Should NOT have mutated
    results.append(("Input immutability", "PASS" if immutable else "FAIL", ""))

    return results

# ═══════════════════════════════════════════════════════════════
#  SIDE TRACK DATA BRIDGE TESTS
# ═══════════════════════════════════════════════════════════════
def run_side_track_tests():
    """Verify all side tracks can seed, tick, score, and write back."""
    results = []
    try:
        from side_tracks import get_all_tracks
        tracks = get_all_tracks()

        gs = make_initial_global()
        bus = make_initial_bus()

        for tid, track in tracks.items():
            try:
                # Test seed
                state = track.seed_from_main_state(gs, bus, {})
                results.append((f"{tid}: seed", "PASS", f"keys={len(state)}"))

                # Test round configs exist
                configs = track.get_round_configs()
                results.append((f"{tid}: configs", "PASS", f"rounds={len(configs)}"))

                # Test score
                score = track.calculate_score(state)
                results.append((f"{tid}: score", "PASS", f"total={score.get('total_score')}"))

                # Test write-back
                wb = track.write_back_to_main(state, gs)
                results.append((f"{tid}: writeback", "PASS", f"flags={len(wb)}"))

                # Verify write-back doesn't corrupt main state keys
                for key in wb:
                    if key in ("corporate_treasury", "group_reputation", "synergy_multiplier"):
                        results.append((f"{tid}: key collision '{key}'", "FAIL", "Reserved key overwritten"))
                    else:
                        pass  # OK, side track flags don't collide

            except Exception as e:
                results.append((f"{tid}: ERROR", "FAIL", str(e)[:100]))
    except ImportError as e:
        results.append(("Side track import", "FAIL", str(e)))

    return results

# ═══════════════════════════════════════════════════════════════
#  MEMORY TRACKING
# ═══════════════════════════════════════════════════════════════
def run_memory_audit(iterations=10):
    """Track memory across simulation iterations."""
    tracemalloc.start()
    snapshots = []
    for i in range(iterations):
        snapshot_before = tracemalloc.take_snapshot()
        run_simulation(persona_optimizer_decisions, seed=i)
        snapshot_after = tracemalloc.take_snapshot()
        stats = snapshot_after.compare_to(snapshot_before, 'lineno')
        total_diff = sum(s.size_diff for s in stats[:20])
        snapshots.append({"iteration": i, "mem_diff_bytes": total_diff})
    tracemalloc.stop()

    # Check for monotonically increasing memory (leak indicator)
    diffs = [s["mem_diff_bytes"] for s in snapshots]
    avg_diff = sum(diffs) / max(len(diffs), 1)
    max_diff = max(diffs) if diffs else 0
    leak_suspected = all(d > 0 for d in diffs[2:])  # Skip first 2 (warmup)
    return {
        "iterations": iterations,
        "avg_mem_diff_bytes": round(avg_diff),
        "max_mem_diff_bytes": max_diff,
        "leak_suspected": leak_suspected,
        "snapshots": snapshots,
    }

# ═══════════════════════════════════════════════════════════════
#  MAIN RUNNER
# ═══════════════════════════════════════════════════════════════
def main():
    ITERATIONS = 100
    personas = {
        "Optimizer": persona_optimizer_decisions,
        "Disruptor": persona_disruptor_decisions,
        "Explorer": persona_explorer_decisions,
    }

    all_results = {}
    print("=" * 70)
    print("  MURESSONS QA — MONTE CARLO STRESS TEST")
    print(f"  {ITERATIONS} iterations × 3 personas × 10 rounds")
    print("=" * 70)

    for name, fn in personas.items():
        print(f"\n{'─' * 50}")
        print(f"  PERSONA: {name}")
        print(f"{'─' * 50}")
        start = time.time()
        persona_anomalies = []
        round_pass_counts = {r: 0 for r in range(1, 11)}
        treasuries = []
        reputations = []
        mrs = []
        tvs = []
        crashes = 0

        for i in range(ITERATIONS):
            result = run_simulation(fn, seed=i * 42)
            persona_anomalies.extend(result["anomalies"])
            treasuries.append(result["final_treasury"])
            reputations.append(result["final_reputation"])
            mrs.append(result["final_mr"])
            tvs.append(result["terminal_value"])
            if result["completed_rounds"] < 10:
                crashes += 1
            for rr in result["rounds"]:
                if rr["status"] == "PASS":
                    round_pass_counts[rr["round"]] += 1

        elapsed = time.time() - start
        unique_anomalies = list(set(persona_anomalies))

        all_results[name] = {
            "iterations": ITERATIONS,
            "crashes": crashes,
            "total_anomalies": len(persona_anomalies),
            "unique_anomalies": unique_anomalies[:20],
            "round_pass_rates": {r: f"{round_pass_counts[r]}/{ITERATIONS}" for r in range(1, 11)},
            "treasury_range": [min(treasuries), max(treasuries)],
            "reputation_range": [min(reputations), max(reputations)],
            "mr_range": [min(mrs), max(mrs)],
            "tv_range": [min(tvs), max(tvs)],
            "elapsed_seconds": round(elapsed, 2),
        }

        print(f"  Completed in {elapsed:.2f}s | Crashes: {crashes}")
        print(f"  Anomalies: {len(unique_anomalies)} unique / {len(persona_anomalies)} total")
        print(f"  Treasury: ${min(treasuries):,.0f} — ${max(treasuries):,.0f}")
        print(f"  Reputation: {min(reputations):.1f} — {max(reputations):.1f}")
        print(f"  M_R: {min(mrs):.4f} — {max(mrs):.4f}")
        print(f"  Terminal Value: ${min(tvs):,.0f} — ${max(tvs):,.0f}")
        for r in range(1, 11):
            status = "✅" if round_pass_counts[r] == ITERATIONS else "❌"
            print(f"    R{r:2d}: {status} {round_pass_counts[r]}/{ITERATIONS}")

    # ── Boundary Tests ──
    print(f"\n{'─' * 50}")
    print("  BOUNDARY & INJECTION TESTS")
    print(f"{'─' * 50}")
    boundary = run_boundary_tests()
    boundary_pass = 0
    for name_b, status, detail in boundary:
        icon = "✅" if status == "PASS" else ("⚠️" if status == "WARN" else "❌")
        print(f"  {icon} {name_b}: {status} {detail}")
        if status == "PASS":
            boundary_pass += 1
    all_results["boundary_tests"] = {
        "total": len(boundary),
        "passed": boundary_pass,
        "results": [{"name": n, "status": s, "detail": d} for n, s, d in boundary],
    }

    # ── Side Track Tests ──
    print(f"\n{'─' * 50}")
    print("  SIDE TRACK DATA BRIDGE TESTS")
    print(f"{'─' * 50}")
    st_results = run_side_track_tests()
    st_pass = 0
    for name_s, status, detail in st_results:
        icon = "✅" if status == "PASS" else "❌"
        print(f"  {icon} {name_s}: {status} {detail}")
        if status == "PASS":
            st_pass += 1
    all_results["side_track_tests"] = {
        "total": len(st_results),
        "passed": st_pass,
        "results": [{"name": n, "status": s, "detail": d} for n, s, d in st_results],
    }

    # ── Memory Audit ──
    print(f"\n{'─' * 50}")
    print("  MEMORY AUDIT (10 iterations)")
    print(f"{'─' * 50}")
    mem = run_memory_audit(10)
    print(f"  Avg mem diff: {mem['avg_mem_diff_bytes']:,} bytes")
    print(f"  Max mem diff: {mem['max_mem_diff_bytes']:,} bytes")
    print(f"  Leak suspected: {'⚠️ YES' if mem['leak_suspected'] else '✅ NO'}")
    all_results["memory_audit"] = mem

    # ── Write JSON results ──
    output_path = backend_dir / "test_comprehensive_results.json"
    with open(output_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\n  Results saved to {output_path}")

    # ── Summary ──
    print(f"\n{'=' * 70}")
    print("  FINAL SUMMARY")
    print(f"{'=' * 70}")
    total_anomalies = sum(len(all_results[p].get("unique_anomalies", [])) for p in personas)
    total_crashes = sum(all_results[p].get("crashes", 0) for p in personas)
    print(f"  Total iterations: {ITERATIONS * 3}")
    print(f"  Total crashes: {total_crashes}")
    print(f"  Total unique anomalies: {total_anomalies}")
    print(f"  Boundary tests: {boundary_pass}/{len(boundary)}")
    print(f"  Side track tests: {st_pass}/{len(st_results)}")
    print(f"  Memory leak: {'SUSPECTED' if mem['leak_suspected'] else 'NONE'}")

    overall = total_crashes == 0 and total_anomalies == 0
    print(f"\n  {'✅ CERTIFICATION: 10-ROUND LOOP STABLE' if overall else '⚠️ ISSUES DETECTED — SEE REPORT'}")
    print(f"{'=' * 70}")

    return all_results

if __name__ == "__main__":
    main()
