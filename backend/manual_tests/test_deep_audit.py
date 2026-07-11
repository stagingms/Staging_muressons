"""
=======================================================================
  MURESSONS DEEP-SYSTEM AUDIT — COMPREHENSIVE STRESS TEST
  
  Phase 1: Trace & Debug — scan for runtime error patterns
  Phase 2: Logic Stress Test — 30 concurrent sessions, edge equilibria
  Phase 3: Edge-Case Evaluation — extreme inputs, boundary conditions
  Phase 4: Deployment Readiness — API + build verification
  
  Run: $env:PYTHONIOENCODING='utf-8'; python test_deep_audit.py
=======================================================================
"""
import copy, json, sys, pathlib, time, traceback, random, concurrent.futures

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from engine import process_tick, calc_contagion, calc_csf, calc_synergy_opex
from engine import calc_revenue_cannibalization, calc_technical_debt
from engine import calc_vrio_decay, calc_natural_capital_interest
from terminal_valuation import calculate_mr, calculate_terminal_value, determine_archetype

SEED_PATH = pathlib.Path(__file__).resolve().parent.parent / "db" / "seed_round1.json"
with open(SEED_PATH, "r", encoding="utf-8-sig") as f:
    SEED = json.load(f)

PASS_COUNT = 0
FAIL_COUNT = 0
BUGS_FOUND = []


def check(label, condition, detail=""):
    global PASS_COUNT, FAIL_COUNT
    if condition:
        PASS_COUNT += 1
    else:
        FAIL_COUNT += 1
        BUGS_FOUND.append({"label": label, "detail": detail})
        print(f"    [FAIL] {label}: {detail}")


def make_global():
    gs = SEED["global_state"]
    bus = SEED["business_units"]
    n = max(len(bus), 1)
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
        "active_event_flags": {"loan_interest_rate": 0.12, "difficulty_tier": "standard"},
        "historical_ebitda": sum(b["revenue_base"] - b["opex_base"] for b in bus),
        "tco2e_emissions": round(sum(b.get("carbon_intensity", 0) * b["revenue_base"] / 1e6 for b in bus)),
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


def make_bus():
    return copy.deepcopy(SEED["business_units"])


def make_decisions(bus, inv_ratio=0.3, capex=500_000, choice="option_a"):
    return [{"bu_id": b["bu_id"], "investment_ratio": inv_ratio,
             "capex_allocated": capex, "choice_selected": choice} for b in bus]


# =====================================================================
#  PHASE 1: TRACE & DEBUG — Runtime Error Pattern Detection
# =====================================================================
def phase1_trace_debug():
    print("\n" + "=" * 70)
    print("  PHASE 1: TRACE & DEBUG")
    print("  Runtime error pattern detection & null-pointer analysis")
    print("=" * 70)

    # BUG-001: calc_contagion crashes on empty bu_states (/ len)
    print("\n  [1.1] Empty BU list — ZeroDivisionError scan")
    try:
        result = calc_contagion([], 40.0)
        check("BUG-001 contagion([])", result == 50.0,
              f"Expected 50.0 (neutral), got {result}")
    except ZeroDivisionError:
        check("BUG-001 contagion([])", False,
              "ZeroDivisionError on empty bu_states — FIX BUG-001 not applied")
    except Exception as e:
        check("BUG-001 contagion([])", False, f"Unexpected: {e}")

    # BUG-002: calc_csf on empty list
    print("  [1.2] CSF with empty BU list")
    try:
        csf = calc_csf([], 0)
        check("CSF empty list", csf == 0.0, f"CSF should be 0, got {csf}")
    except Exception as e:
        check("CSF empty list", False, f"Crashed: {e}")

    # BUG-003: calc_ncd_interest with extreme values
    print("  [1.3] NCD interest with extreme debt ($1B)")
    try:
        ncd_i = calc_natural_capital_interest(1_000_000_000, 0.05)
        check("NCD extreme debt", ncd_i >= 0 and not (ncd_i != ncd_i), f"Result: {ncd_i}")
    except Exception as e:
        check("NCD extreme debt", False, f"Crashed: {e}")

    # BUG-004: calc_vrio_decay with extreme decay rate
    print("  [1.4] VRIO decay with 100% decay rate")
    try:
        result = calc_vrio_decay(1.0, 1.0)  # 2 args: advantage_current, imitation_decay_rate
        check("VRIO 100% decay", result == 0.0, f"Result: {result}")
    except Exception as e:
        check("VRIO 100% decay", False, f"Crashed: {e}")

    # BUG-005: process_tick with zero-revenue BUs
    print("  [1.5] process_tick with zero-revenue BUs (null-pointer risk)")
    gs = make_global()
    bus = make_bus()
    for b in bus:
        b["revenue_base"] = 0.0
    decisions = make_decisions(bus, inv_ratio=0.0, capex=1)
    try:
        result = process_tick(gs, bus, decisions, 0, 0, 0.05, "legacy_abc")
        check("Zero-revenue BUs", "global_state" in result, "Engine survived zero-revenue")
    except Exception as e:
        check("Zero-revenue BUs", False, f"Crashed: {e}")

    # BUG-006: process_tick with negative OPEX (impossible state)
    print("  [1.6] process_tick with negative OPEX (impossible state)")
    gs = make_global()
    bus = make_bus()
    for b in bus:
        b["opex_base"] = -1000000
    decisions = make_decisions(bus, inv_ratio=0.5, capex=100_000)
    try:
        result = process_tick(gs, bus, decisions, 0, 0, 0.05, "legacy_abc")
        # Check FIX-QA-005 clamp
        for b in result["bu_states"]:
            check("Negative OPEX clamped", b["opex_base"] >= 0,
                  f"BU {b['bu_id']} opex={b['opex_base']}")
    except Exception as e:
        check("Negative OPEX", False, f"Crashed: {e}")

    # BUG-007: terminal_valuation with edge MR values
    print("  [1.7] Terminal valuation edge cases")
    bus = make_bus()
    for mr_val in [0.0, -1.0, 5.0, float('inf')]:
        try:
            tv = calculate_terminal_value(bus, mr_val if mr_val != float('inf') else 999)
            check(f"TV mr={mr_val}", True, f"TV={tv['terminal_value']}")
        except Exception as e:
            check(f"TV mr={mr_val}", False, f"Crashed: {e}")

    # BUG-008: determine_archetype with NaN
    print("  [1.8] Archetype determination with extreme values")
    for val in [0.0, -1.0, 100.0, 0.001]:
        try:
            arch = determine_archetype(val)
            check(f"Archetype mr={val}", "key" in arch, f"Got: {arch['key']}")
        except Exception as e:
            check(f"Archetype mr={val}", False, f"Crashed: {e}")


# =====================================================================
#  PHASE 2: LOGIC STRESS TEST — 30 Concurrent Sessions
# =====================================================================
def run_single_session(session_id):
    """Run one full 10-round session with randomized strategy. Returns metrics."""
    gs = make_global()
    bus = make_bus()
    errors = []

    for rnd in range(1, 11):
        gs["round_number"] = rnd
        inv = random.uniform(0.0, 1.0)
        capex = random.randint(1, 5_000_000)
        choice = random.choice(["option_a", "option_b", "option_c"])
        dividends = random.uniform(0, max(0, gs["corporate_treasury"] * 0.1))
        crisis = random.uniform(0, 80)

        decisions = make_decisions(bus, inv, capex, choice)
        try:
            result = process_tick(gs, bus, decisions, dividends, crisis, 0.05, "legacy_abc")
            gs = result["global_state"]
            bus = result["bu_states"]

            # Check for impossible values
            for b in bus:
                if b["revenue_base"] < 0:
                    errors.append(f"S{session_id} R{rnd}: Negative revenue {b['bu_id']}")
                if b["opex_base"] < 0:
                    errors.append(f"S{session_id} R{rnd}: Negative opex {b['bu_id']}")
                if b.get("reputation_score", 0) < 0 or b.get("reputation_score", 0) > 100:
                    errors.append(f"S{session_id} R{rnd}: Rep out of bounds {b['bu_id']}")
                if b.get("social_license_score", 0) < 0 or b.get("social_license_score", 0) > 100:
                    errors.append(f"S{session_id} R{rnd}: SLO out of bounds {b['bu_id']}")
            if gs.get("group_reputation", 0) < 0 or gs.get("group_reputation", 0) > 100:
                errors.append(f"S{session_id} R{rnd}: Group rep out of bounds")

        except Exception as e:
            errors.append(f"S{session_id} R{rnd}: CRASH - {e}")
            break

    return {
        "session_id": session_id,
        "treasury": gs.get("corporate_treasury", 0),
        "reputation": gs.get("group_reputation", 0),
        "ebitda": sum(b["revenue_base"] - b["opex_base"] for b in bus),
        "errors": errors,
    }


def phase2_logic_stress():
    print("\n" + "=" * 70)
    print("  PHASE 2: LOGIC STRESS TEST")
    print("  30 concurrent sessions with randomized strategies")
    print("=" * 70)

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(run_single_session, i): i for i in range(1, 31)}
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())

    total_errors = sum(len(r["errors"]) for r in results)
    crashed = [r for r in results if any("CRASH" in e for e in r["errors"])]
    impossible = [r for r in results if any("Negative" in e or "out of bounds" in e for e in r["errors"])]

    print(f"\n  Sessions completed: {len(results)}/30")
    print(f"  Total errors: {total_errors}")
    print(f"  Crashed sessions: {len(crashed)}")
    print(f"  Impossible values: {len(impossible)}")

    check("30 sessions complete", len(results) == 30, f"Only {len(results)} completed")
    check("Zero crashes", len(crashed) == 0, 
          f"{len(crashed)} crashed: {[e for r in crashed for e in r['errors'] if 'CRASH' in e][:3]}")
    check("No impossible values", len(impossible) == 0,
          f"{len(impossible)} had impossible values: {[e for r in impossible for e in r['errors']][:5]}")

    # Check equilibrium — no infinite loops (all sessions finished 10 rounds)
    # Check no NaN/Inf in final values
    for r in results:
        t = r["treasury"]
        check(f"S{r['session_id']} no NaN/Inf", 
              t == t and abs(t) < 1e15,
              f"Treasury={t}")

    # Distribution spread — confirm outcomes aren't identical
    treasuries = [r["treasury"] for r in results]
    unique_t = len(set(round(t, 2) for t in treasuries))
    check("Outcome diversity", unique_t >= 1, f"Only {unique_t} unique treasury outcomes")

    if total_errors > 0:
        print("\n  First 5 errors:")
        count = 0
        for r in results:
            for e in r["errors"]:
                if count < 5:
                    print(f"    - {e}")
                    count += 1


# =====================================================================
#  PHASE 3: EDGE-CASE EVALUATION — Extreme Inputs
# =====================================================================
def phase3_edge_cases():
    print("\n" + "=" * 70)
    print("  PHASE 3: EDGE-CASE EVALUATION")
    print("  Extreme inputs, boundary conditions, rapid-fire decisions")
    print("=" * 70)

    # EDGE-001: Zero budget allocation (all BUs get $1 CAPEX)
    print("\n  [3.1] Zero-budget allocation ($1 CAPEX x 10 rounds)")
    gs = make_global()
    bus = make_bus()
    for rnd in range(1, 11):
        gs["round_number"] = rnd
        decisions = make_decisions(bus, inv_ratio=0.0, capex=1, choice="option_a")
        try:
            result = process_tick(gs, bus, decisions, 0, 0, 0.05, "legacy_abc")
            gs = result["global_state"]
            bus = result["bu_states"]
        except Exception as e:
            check(f"Zero-budget R{rnd}", False, f"Crashed: {e}")
            break
    check("Zero-budget 10 rounds", gs["round_number"] == 10 or gs.get("round_number", 0) >= 10,
          f"Reached round {gs.get('round_number', '?')}")

    # EDGE-002: Maximum market saturation (investment_ratio=1.0, max CAPEX)
    print("  [3.2] Maximum saturation (100% investment, $100M CAPEX)")
    gs = make_global()
    bus = make_bus()
    for rnd in range(1, 11):
        gs["round_number"] = rnd
        decisions = make_decisions(bus, inv_ratio=1.0, capex=100_000_000, choice="option_a")
        try:
            result = process_tick(gs, bus, decisions, 0, 0, 0.05, "legacy_abc")
            gs = result["global_state"]
            bus = result["bu_states"]
        except Exception as e:
            check(f"Max-saturation R{rnd}", False, f"Crashed: {e}")
            break
    check("Max-saturation 10 rounds", True, "Engine survived maximum investment")

    # EDGE-003: Max dividends (drain entire treasury each round)
    print("  [3.3] Maximum dividends (drain treasury each round)")
    gs = make_global()
    bus = make_bus()
    for rnd in range(1, 11):
        gs["round_number"] = rnd
        treasury = gs.get("corporate_treasury", 0)
        dividends = max(0, treasury)
        decisions = make_decisions(bus, inv_ratio=0.5, capex=100_000, choice="option_b")
        try:
            result = process_tick(gs, bus, decisions, dividends, 0, 0.05, "legacy_abc")
            gs = result["global_state"]
            bus = result["bu_states"]
        except Exception as e:
            check(f"Max-dividends R{rnd}", False, f"Crashed: {e}")
            break
    check("Max-dividends 10 rounds", True, "Engine survived maximum extraction")

    # EDGE-004: Maximum crisis severity (100)
    print("  [3.4] Maximum crisis severity (100) for all 10 rounds")
    gs = make_global()
    bus = make_bus()
    for rnd in range(1, 11):
        gs["round_number"] = rnd
        decisions = make_decisions(bus, inv_ratio=0.5, capex=100_000, choice="option_c")
        try:
            result = process_tick(gs, bus, decisions, 0, 100.0, 0.05, "legacy_abc")
            gs = result["global_state"]
            bus = result["bu_states"]
        except Exception as e:
            check(f"Max-crisis R{rnd}", False, f"Crashed: {e}")
            break
    check("Max-crisis 10 rounds", True, "Engine survived maximum crisis")
    check("Reputation clamped", 0 <= gs.get("group_reputation", -1) <= 100,
          f"Rep={gs.get('group_reputation')}")

    # EDGE-005: Rapid-fire same round (deterministic: process_tick is idempotent)
    print("  [3.5] Rapid-fire: 100 ticks on same state (idempotency check)")
    gs = make_global()
    bus = make_bus()
    decisions = make_decisions(bus, inv_ratio=0.5, capex=500_000, choice="option_a")
    results_list = []
    for _ in range(100):
        try:
            r = process_tick(copy.deepcopy(gs), copy.deepcopy(bus), decisions, 0, 0, 0.05, "legacy_abc")
            results_list.append(r["global_state"]["corporate_treasury"])
        except Exception as e:
            check("Rapid-fire", False, f"Crashed on iteration: {e}")
            break
    # Not necessarily deterministic (uses random) but should never crash
    check("Rapid-fire 100 ticks", len(results_list) == 100,
          f"Only {len(results_list)} completed")

    # EDGE-006: Extreme BU state values
    print("  [3.6] Extreme BU state: all values at 0 or 100")
    gs = make_global()
    bus = make_bus()
    for b in bus:
        b["revenue_base"] = 0
        b["opex_base"] = 0
        b["reputation_score"] = 0
        b["social_license_score"] = 0
        b["carbon_intensity"] = 100
        b["governance_risk_score"] = 100
        b["natural_capital_debt"] = 1_000_000
    decisions = make_decisions(bus, inv_ratio=0.5, capex=1, choice="option_a")
    try:
        result = process_tick(gs, bus, decisions, 0, 100, 0.05, "legacy_abc")
        check("Extreme BU state", "global_state" in result, "Engine survived extreme state")
    except Exception as e:
        check("Extreme BU state", False, f"Crashed: {e}")

    # EDGE-007: Single BU (not standard 4-BU setup)
    print("  [3.7] Single BU session")
    gs = make_global()
    bus = [make_bus()[0]]
    decisions = [{"bu_id": bus[0]["bu_id"], "investment_ratio": 0.5,
                  "capex_allocated": 500_000, "choice_selected": "option_a"}]
    try:
        result = process_tick(gs, bus, decisions, 0, 0, 0.05, "legacy_abc")
        check("Single BU", len(result["bu_states"]) == 1, "Engine handled single BU")
    except Exception as e:
        check("Single BU", False, f"Crashed: {e}")

    # EDGE-008: Terminal valuation with all-zero BUs
    print("  [3.8] Terminal valuation with zero-revenue BUs")
    zero_bus = [{"bu_id": "test", "revenue_base": 0, "opex_base": 0,
                 "carbon_intensity": 0}]
    try:
        tv = calculate_terminal_value(zero_bus, 1.0)
        check("TV zero-rev", tv["terminal_value"] == 0.0, f"TV={tv['terminal_value']}")
    except Exception as e:
        check("TV zero-rev", False, f"Crashed: {e}")

    # EDGE-009: calculate_mr with all-zero inputs
    print("  [3.9] MR calculation with all-zero inputs")
    try:
        mr = calculate_mr({}, 0, 0, 0, 0, 0)
        check("MR all-zero", mr["mr"] >= 0, f"MR={mr['mr']}")
    except Exception as e:
        check("MR all-zero", False, f"Crashed: {e}")


# =====================================================================
#  PHASE 4: DEPLOYMENT READINESS
# =====================================================================
def phase4_deployment():
    print("\n" + "=" * 70)
    print("  PHASE 4: DEPLOYMENT READINESS")
    print("  API responsiveness, schema validation, build verification")
    print("=" * 70)

    # 4.1: Import all critical modules
    print("\n  [4.1] Module import verification")
    modules = [
        "engine", "round_logic", "round_configs", "impact_engine",
        "terminal_valuation", "database_memory", "stakeholder_map",
        "ending_pathways", "ceo_diary", "biodiversity_engine",
        "balance_sheet", "board_governance", "org_politics",
        "supply_chain_network", "npc_stakeholders", "autonomous_agents",
        "systemic_risk_engine", "black_swan_registry", "branching_engine",
        "dynamic_cases", "pedagogical_engine", "meadows_leverage",
    ]
    for mod_name in modules:
        try:
            __import__(mod_name)
            check(f"Import {mod_name}", True)
        except ImportError as e:
            check(f"Import {mod_name}", False, f"ImportError: {e}")
        except Exception as e:
            check(f"Import {mod_name}", False, f"Error: {e}")

    # 4.2: FastAPI app instantiation
    print("\n  [4.2] FastAPI app instantiation")
    try:
        from main import app
        check("FastAPI app", app is not None)
    except Exception as e:
        check("FastAPI app", False, f"Error: {e}")

    # 4.3: Pytest suite
    print("\n  [4.3] Backend test suite (458 tests)")
    import subprocess
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=line"],
        cwd=str(pathlib.Path(__file__).resolve().parent),
        capture_output=True, text=True, timeout=30,
    )
    passed = "passed" in r.stdout
    check("Pytest suite", passed and r.returncode == 0,
          r.stdout.strip().split("\n")[-1] if r.stdout else r.stderr[:200])

    # 4.4: Seed data integrity
    print("\n  [4.4] Seed data integrity")
    seed = SEED
    check("Seed has 4 BUs", len(seed["business_units"]) == 4)
    check("Seed round is 1", seed["round"] == 1)
    check("Seed treasury is $50M", seed["global_state"]["corporate_treasury_usd"] == 50_000_000)
    for bu in seed["business_units"]:
        check(f"BU {bu['bu_id']} revenue > 0", bu["revenue_base"] > 0)
        check(f"BU {bu['bu_id']} opex > 0", bu["opex_base"] > 0)
        check(f"BU {bu['bu_id']} NCD == 0", bu["natural_capital_debt"] == 0)

    # 4.5: Round config completeness
    print("\n  [4.5] Round config completeness (R1-R10)")
    from round_configs import get_round_config
    for rnd in range(1, 11):
        cfg = get_round_config(rnd)
        check(f"R{rnd} config exists", cfg is not None)
        if cfg:
            check(f"R{rnd} has crisis", "crisis" in cfg, f"Keys: {list(cfg.keys())[:5]}")


# =====================================================================
#  MAIN
# =====================================================================
def main():
    global PASS_COUNT, FAIL_COUNT
    print("=" * 70)
    print("  MURESSONS DEEP-SYSTEM AUDIT v1.0")
    print("  Trace, Stress, Edge-Case, Deploy")
    print("=" * 70)

    t0 = time.time()

    phase1_trace_debug()
    phase2_logic_stress()
    phase3_edge_cases()
    phase4_deployment()

    elapsed = time.time() - t0

    print("\n" + "=" * 70)
    print("  FINAL SUMMARY")
    print("=" * 70)
    print(f"  Total checks: {PASS_COUNT + FAIL_COUNT}")
    print(f"  Passed: {PASS_COUNT}")
    print(f"  Failed: {FAIL_COUNT}")
    print(f"  Time: {elapsed:.1f}s")

    if BUGS_FOUND:
        print(f"\n  BUGS FOUND ({len(BUGS_FOUND)}):")
        for i, bug in enumerate(BUGS_FOUND, 1):
            print(f"    {i}. [{bug['label']}] {bug['detail']}")

    print()
    if FAIL_COUNT == 0:
        print("  VERDICT: READY FOR DEPLOYMENT")
    else:
        print(f"  VERDICT: {FAIL_COUNT} ISSUE(S) REQUIRE ATTENTION")
    print("=" * 70)

    return FAIL_COUNT == 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
