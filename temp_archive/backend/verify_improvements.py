"""Verify all improvement recommendations are implemented."""
import importlib

items = {
    "QW-1 Decision Timer": ("pedagogical_engine", "get_timer_config"),
    "QW-2 Option Shuffle": ("option_shuffle", None),
    "QW-3 Scope 1/2/3": ("supply_chain_network", "estimate_scope3_emissions"),
    "QW-4 Stochastic Noise": ("branching_engine", "calc_adaptive_crisis_severity"),
    "QW-5 Peer Prompts": ("pedagogical_engine", "get_peer_prompts_for_round"),
    "SE-1 Board Governance": ("board_governance", "process_board_tick"),
    "SE-2 Supply Chain Network": ("supply_chain_network", "process_supply_chain_tick"),
    "SE-3 Adaptive Crisis Severity": ("branching_engine", "calc_adaptive_crisis_severity"),
    "SE-4 Biodiversity Engine": ("biodiversity_engine", "process_biodiversity_tick"),
    "SE-5 Cross-Player Market": ("market_dynamics", "process_market_tick"),
    "SE-6 Balance Sheet": ("balance_sheet", "process_balance_sheet_tick"),
    "SE-7 Regulatory Sandbox": ("regulatory_sandbox", "apply_sandbox_effects"),
    "SE-8 Dynamic Cases": ("dynamic_cases", "select_contextual_cases"),
    "SI-1 Non-Linear Branching": ("branching_engine", "classify_player_archetype"),
    "SI-2 NPC Stakeholders": ("npc_stakeholders", "process_npc_tick"),
    "SI-3 Extended Horizon": ("branching_engine", "get_extended_round_config"),
    "SI-4 TCFD Scenarios": ("tcfd_scenarios", "run_scenario_analysis"),
    "SI-5 Org Politics": ("org_politics", "process_org_politics_tick"),
    "Meadows Leverage Points": ("meadows_leverage", "analyse_session_leverage_points"),
    "Senge System Archetypes": ("meadows_leverage", "detect_archetypes"),
    "Argyris Double-Loop": ("meadows_leverage", "classify_learning_loop"),
}

results = []
for name, (mod_name, func_name) in items.items():
    try:
        mod = importlib.import_module(mod_name)
        if func_name:
            fn = getattr(mod, func_name, None)
            if fn:
                results.append(("OK", name, f"{mod_name}.{func_name}"))
            else:
                results.append(("MISS", name, f"{mod_name}.{func_name} NOT FOUND"))
        else:
            results.append(("OK", name, f"{mod_name} (module exists)"))
    except Exception as e:
        results.append(("FAIL", name, str(e)))

print("=" * 70)
print("MURESSONS IMPROVEMENT VERIFICATION REPORT")
print("=" * 70)
for status, name, detail in results:
    icon = "YES" if status == "OK" else "NO "
    print(f"  [{icon}] {name:40s} {detail}")

ok = sum(1 for s, _, _ in results if s == "OK")
total = len(results)
print("=" * 70)
print(f"RESULT: {ok}/{total} items verified")
if ok < total:
    print("MISSING:")
    for s, n, d in results:
        if s != "OK":
            print(f"  - {n}: {d}")
print("=" * 70)

# Also check integration wiring
print("\nINTEGRATION WIRING:")
try:
    from round_logic import run_new_engines
    print("  [YES] run_new_engines() in round_logic.py")
except ImportError:
    print("  [NO ] run_new_engines() in round_logic.py")

try:
    from router import router
    route_paths = [r.path for r in router.routes if hasattr(r, "path")]
    new_endpoints = [
        "/tcfd-scenarios", "/board-vote", "/supply-chain-audit",
        "/coalition-check", "/leverage-analysis", "/contextual-cases",
        "/regulatory-sandbox/activate", "/regulatory-sandbox/instruments",
        "/biodiversity", "/balance-sheet", "/board-governance",
        "/supply-chain", "/npc-stakeholders",
    ]
    for ep in new_endpoints:
        # Check if path ends with the endpoint (since routes have {session_id} prefix)
        found = any(ep in p for p in route_paths)
        icon = "YES" if found else "NO "
        print(f"  [{icon}] API endpoint ...{ep}")
except Exception as e:
    print(f"  [FAIL] Router check: {e}")

# Check pedagogical toggles
print("\nPEDAGOGICAL TOGGLES:")
try:
    from pedagogical_engine import DEFAULT_PEDAGOGICAL_TOGGLES as t
    toggle_checks = [
        "decision_timer_enabled", "peer_learning_prompts_enabled",
        "board_governance_enabled", "supply_chain_network_enabled",
        "biodiversity_engine_enabled", "market_dynamics_enabled",
        "balance_sheet_enabled", "regulatory_sandbox_enabled",
        "dynamic_cases_enabled", "branching_enabled",
        "npc_stakeholders_enabled", "tcfd_scenarios_enabled",
        "org_politics_enabled", "meadows_leverage_enabled",
        "system_archetypes_enabled",
    ]
    for tk in toggle_checks:
        found = tk in t
        icon = "YES" if found else "NO "
        print(f"  [{icon}] {tk}")
except Exception as e:
    print(f"  [FAIL] Toggle check: {e}")
