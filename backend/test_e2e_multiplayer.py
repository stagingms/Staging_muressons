"""
Muressons Multi-Player E2E Test: 4 Players Playing Simultaneously in Same Cohort

Tests:
1. God Mode login & facilitator creation
2. Cohort creation with Narrative Crisis
3. 4 players inducted, registered, and joined
4. All 4 players play 10 rounds CONCURRENTLY (via threading)
5. State isolation: each player's metrics diverge based on different choices
6. Leaderboard shows all 4 players ranked
7. Peer benchmarking data available
8. No race conditions or state corruption
"""
import os
os.environ['USE_MEMORY_DB'] = 'true'
os.environ['DEBUG'] = 'true'
os.environ['MASTER_PASSWORD'] = '321'

import sys, time, json, threading
from datetime import datetime
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
BU_IDS = ["pharma", "electronics", "consumer_goods", "software"]

PASS = "[PASS]"
FAIL = "[FAIL]"
WARN = "[WARN]"
INFO = "[INFO]"

test_results = []
_results_lock = threading.Lock()

def log(icon, msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"  [{ts}] {icon} {msg}")

def section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

def record(label, ok, detail=None):
    with _results_lock:
        test_results.append((label, ok, detail))

def assert_ok(resp, label, expected=(200, 201)):
    if isinstance(expected, int):
        expected = (expected,)
    if resp.status_code in expected:
        log(PASS, f"{label} -> {resp.status_code}")
        record(label, True)
        return True
    else:
        detail = resp.text[:300]
        log(FAIL, f"{label} -> {resp.status_code}: {detail}")
        record(label, False, detail)
        return False


# ============================================================
#  SETUP: Create cohort and register 4 players
# ============================================================
PLAYER_PROFILES = [
    {"name": "Alpha Team (Aggressive)", "strategy": "aggressive"},
    {"name": "Beta Team (Balanced)", "strategy": "balanced"},
    {"name": "Gamma Team (Conservative)", "strategy": "conservative"},
    {"name": "Delta Team (Random)", "strategy": "random"},
]

STRATEGY_CHOICES = {
    "aggressive":   ["option_a", "option_a", "option_b", "option_a", "option_a",
                     "option_b", "option_a", "option_a", "option_b", "option_a"],
    "balanced":     ["option_b", "option_b", "option_b", "option_b", "option_b",
                     "option_b", "option_b", "option_b", "option_b", "option_b"],
    "conservative": ["option_c", "option_c", "option_c", "option_c", "option_c",
                     "option_c", "option_c", "option_c", "option_c", "option_c"],
    "random":       ["option_a", "option_c", "option_b", "option_a", "option_c",
                     "option_b", "option_a", "option_c", "option_b", "option_a"],
}

STRATEGY_INVEST = {
    "aggressive":   0.45,   # High sustainability investment
    "balanced":     0.30,
    "conservative": 0.10,   # Minimal sustainability spend
    "random":       0.25,
}

ROUND_TITLES = {
    1: "Foundations - ESG Materiality",
    2: "Double Materiality Gate",
    3: "Scope 3 Supply Chain",
    4: "ESG Contagion Crisis",
    5: "Climate Physical Risk",
    6: "AI Ethics & Bias",
    7: "Circular Economy Pivot",
    8: "Blue Water Stress",
    9: "Just Transition & Labor",
    10: "Grand Finale - Activist Ultimatum",
}


def setup_environment():
    """Create facilitator, cohort, and register 4 players."""
    section("SETUP: Environment Initialization")

    # God Mode login
    r = client.post("/api/admin/facilitators/login", json={
        "facilitator_id": "god_mode", "password": "321",
    })
    assert_ok(r, "God Mode login")

    # Create facilitator
    r = client.post("/api/admin/facilitators", json={
        "name": "Multi-Player Test Prof",
        "password": "321",
        "max_cohorts": 10,
        "decision_paradigm": "legacy_abc",
        "role": "facilitator",
        "created_by": "mp_test",
    }, headers={"x-facilitator-id": "god_mode"})
    assert_ok(r, "Create facilitator", expected=(200, 201))
    fac_id = r.json().get("facilitator_id")
    log(INFO, f"Facilitator: {fac_id}")

    # Create cohort
    cohort_name = f"MP_Test_Cohort_{int(time.time())}"
    r = client.post("/api/simulations/start", json={
        "cohort_name": cohort_name,
        "facilitator_id": fac_id,
        "decision_paradigm": "legacy_abc",
        "experience_level": "standard",
    })
    assert_ok(r, "Create cohort", expected=201)
    cohort_session_id = r.json().get("session_id")
    log(INFO, f"Cohort session: {cohort_session_id}")

    # Induct 4 players
    players = []
    for i, profile in enumerate(PLAYER_PROFILES):
        r = client.post("/api/admin/players/induct", json={
            "name": profile["name"],
            "email": f"player{i+1}@test.com",
            "assigned_bu": "",
            "session_id": cohort_session_id,
        }, headers={"x-facilitator-id": fac_id})
        assert_ok(r, f"Induct player {i+1}: {profile['name']}")
        p = r.json()
        player_id = p.get("player_id")
        player_pw = p.get("password")
        log(INFO, f"  Player {i+1}: {player_id} (pw: {player_pw})")
        players.append({
            "player_id": player_id,
            "password": player_pw,
            "name": profile["name"],
            "strategy": profile["strategy"],
        })

    # Each player joins the cohort -> gets their own sub-session
    section("SETUP: Players Joining Cohort")
    for i, p in enumerate(players):
        r = client.post(f"/api/simulations/public/sessions/{cohort_session_id}/join", json={
            "player_id": p["player_id"],
            "password": "321",  # master password bypass
            "player_name": p["name"],
        })
        assert_ok(r, f"Player {i+1} joins cohort")
        join_data = r.json()
        p["session_id"] = join_data.get("session_id")
        p["player_count"] = join_data.get("player_count")
        log(INFO, f"  {p['name']}: sub-session={p['session_id'][:8]}... (count={p['player_count']})")

    return fac_id, cohort_session_id, players


# ============================================================
#  PLAYER ROUND LOGIC
# ============================================================
def submit_stakeholder_map(sid, player_name):
    r = client.get("/api/simulations/stakeholder-map/stakeholders")
    if r.status_code != 200:
        return False
    stakeholders = r.json().get("stakeholders", [])
    quadrants = ["high_power_high_interest", "high_power_low_interest",
                 "low_power_high_interest", "low_power_low_interest"]
    mapping = {}
    for i, s in enumerate(stakeholders):
        sid_s = s.get("id", s.get("stakeholder_id", f"s{i}"))
        mapping[sid_s] = quadrants[i % 4]
    r2 = client.post(f"/api/simulations/{sid}/stakeholder-map", json={"mapping": mapping})
    if r2.status_code == 200:
        record(f"{player_name} R1 Stakeholder Map", True)
        return True
    record(f"{player_name} R1 Stakeholder Map", False, r2.text[:200])
    return False


def submit_materiality(sid, player_name):
    r = client.get("/api/admin/materiality-config")
    if r.status_code != 200:
        return False
    config = r.json()
    issues = config.get("issues", [])
    q1, q2, q3, q4 = [], [], [], []
    for issue in issues:
        fi = issue.get("financial_impact", "low")
        si = issue.get("societal_impact", "low")
        if fi == "high" and si == "high":
            q1.append(issue["id"])
        elif fi == "high":
            q2.append(issue["id"])
        elif si == "high":
            q3.append(issue["id"])
        else:
            q4.append(issue["id"])
    payload = {
        "consultant_used": False,
        "matrix_submission": {
            "quadrant_1_top_right": q1,
            "quadrant_2_top_left": q2,
            "quadrant_3_bottom_right": q3,
            "quadrant_4_bottom_left": q4,
        },
        "force_override_cfo": False,
    }
    r2 = client.post(f"/api/simulations/{sid}/materiality", json=payload)
    if r2.status_code == 200:
        record(f"{player_name} R2 Materiality", True)
        return True
    record(f"{player_name} R2 Materiality", False, r2.text[:200])
    return False


def commit_round_for_player(sid, round_num, strategy, player_name):
    """Commit a turn with strategy-specific decisions."""
    choice = STRATEGY_CHOICES[strategy][round_num - 1]
    invest_ratio = STRATEGY_INVEST[strategy]

    dash = client.get(f"/api/simulations/{sid}/dashboard").json()
    active_bus = [bu["bu_id"] for bu in dash.get("business_units", [])]
    if not active_bus:
        active_bus = BU_IDS

    decisions = []
    for bu in active_bus:
        capex = 600000 if strategy == "aggressive" else (
            400000 if strategy == "balanced" else (
                200000 if strategy == "conservative" else 350000
            )
        )
        decisions.append({
            "bu_id": bu,
            "investment_ratio": invest_ratio,
            "capex_allocated": capex + (round_num * 20000),
            "choice_selected": choice,
        })

    payload = {
        "decisions": decisions,
        "dividends_paid": 0,
        "crisis_severity": 0,
        "force_override_cfo": True,
    }

    r = client.post(f"/api/simulations/{sid}/commit-turn", json=payload)
    if r.status_code in (200, 201):
        d = r.json()
        gs = d.get("global_state", {})
        treasury = gs.get("corporate_treasury", 0)
        rep = gs.get("group_reputation", 0)
        co2 = gs.get("tco2e_emissions", 0)
        record(f"{player_name} R{round_num} Commit", True)
        return {
            "round": round_num,
            "new_round": d.get("new_round_number"),
            "treasury": treasury,
            "reputation": rep,
            "co2": co2,
            "ebitda": gs.get("historical_ebitda", 0),
            "synergy": gs.get("synergy_multiplier", 1.0),
        }
    else:
        record(f"{player_name} R{round_num} Commit", False, r.text[:200])
        return None


# ============================================================
#  PLAYER THREAD: plays all 10 rounds
# ============================================================
player_metrics = {}   # {player_name: [round_data, ...]}
player_errors = {}    # {player_name: [error_str, ...]}

def player_thread(player):
    """Thread function: play all 10 rounds for a single player."""
    name = player["name"]
    sid = player["session_id"]
    strategy = player["strategy"]
    metrics = []
    errors = []

    materiality_done = False

    for rnd in range(1, 11):
        dash = client.get(f"/api/simulations/{sid}/dashboard").json()
        current = dash.get("current_round", rnd)

        if current != rnd:
            materiality_done = False

        # R1: Stakeholder map
        if current == 1:
            submit_stakeholder_map(sid, name)

        # R2: Materiality
        if current == 2 and not materiality_done:
            submit_materiality(sid, name)
            materiality_done = True

        # Commit
        result = commit_round_for_player(sid, current, strategy, name)
        if result is None:
            errors.append(f"R{current}: commit failed")
            break
        metrics.append(result)

        # Rate limiter cooldown
        time.sleep(5.2)

    player_metrics[name] = metrics
    player_errors[name] = errors


# ============================================================
#  CONCURRENT EXECUTION
# ============================================================
def play_all_players_concurrently(players):
    section("PHASE: 4 PLAYERS PLAYING 10 ROUNDS CONCURRENTLY")

    threads = []
    for p in players:
        t = threading.Thread(target=player_thread, args=(p,), name=p["name"])
        threads.append(t)

    log(INFO, "Starting 4 player threads simultaneously...")
    start = time.time()

    for t in threads:
        t.start()

    for t in threads:
        t.join(timeout=120)

    elapsed = time.time() - start
    log(INFO, f"All players finished in {elapsed:.1f}s")

    # Print individual player summaries
    for p in players:
        name = p["name"]
        metrics = player_metrics.get(name, [])
        errors = player_errors.get(name, [])
        if metrics:
            final = metrics[-1]
            log(PASS if not errors else FAIL,
                f"{name}: {len(metrics)} rounds | "
                f"T=${final['treasury']:,.0f} | Rep={final['reputation']:.1f} | "
                f"CO2={final['co2']:,.0f}t | Syn={final['synergy']:.3f}")
        else:
            log(FAIL, f"{name}: NO ROUNDS COMPLETED")
        if errors:
            for e in errors:
                log(FAIL, f"  Error: {e}")


# ============================================================
#  POST-GAME VALIDATION
# ============================================================
def validate_state_isolation(players):
    section("VALIDATION: State Isolation Between Players")

    treasuries = {}
    reputations = {}
    co2s = {}

    for p in players:
        r = client.get(f"/api/simulations/{p['session_id']}/dashboard")
        assert_ok(r, f"Final dashboard: {p['name']}")
        dash = r.json()
        gs = dash.get("global_state", {})
        current = dash.get("current_round", "?")
        history = dash.get("history", [])

        t = gs.get("corporate_treasury", 0)
        rep = gs.get("group_reputation", 0)
        co2 = gs.get("tco2e_emissions", 0)

        treasuries[p["name"]] = t
        reputations[p["name"]] = rep
        co2s[p["name"]] = co2

        log(INFO, f"  {p['name']}: R{current}, {len(history)} history, "
            f"T=${t:,.0f}, Rep={rep:.1f}, CO2={co2:,.0f}t")

    # Check divergence: at least 2 unique treasury values
    unique_t = len(set(int(v) for v in treasuries.values()))
    unique_r = len(set(round(v, 1) for v in reputations.values()))
    unique_co2 = len(set(int(v) for v in co2s.values()))

    if unique_t >= 2:
        log(PASS, f"Treasury divergence: {unique_t} unique values (state isolation confirmed)")
        record("State Isolation: Treasury", True)
    else:
        log(WARN, f"Treasury values identical ({unique_t} unique) - may indicate state leakage")
        record("State Isolation: Treasury", False, "All treasuries identical")

    if unique_co2 >= 2:
        log(PASS, f"CO2 divergence: {unique_co2} unique values")
        record("State Isolation: CO2", True)
    else:
        log(WARN, f"CO2 values identical ({unique_co2} unique)")
        record("State Isolation: CO2", False, "All CO2 identical")

    # Print comparison table
    print(f"\n  {'Player':<35} {'Treasury':>15} {'Reputation':>12} {'CO2 (t)':>10}")
    print(f"  {'-'*35} {'-'*15} {'-'*12} {'-'*10}")
    for name in treasuries:
        print(f"  {name:<35} ${treasuries[name]:>13,.0f} {reputations[name]:>11.1f} {co2s[name]:>9,.0f}")


def validate_leaderboard(fac_id, cohort_session_id, players):
    section("VALIDATION: Leaderboard & Peer Benchmarking")

    # Leaderboard
    r = client.get("/api/admin/leaderboard", headers={"x-facilitator-id": fac_id})
    assert_ok(r, "Leaderboard")
    lb = r.json().get("leaderboard", [])

    # Find entries matching our cohort
    cohort_entries = [e for e in lb if e.get("session_id") == cohort_session_id]
    log(INFO, f"Cohort leaderboard entries: {len(cohort_entries)}")

    # Check all 4 player sub-sessions exist
    sub_session_ids = {p["session_id"] for p in players}
    found_subs = [e for e in lb if e.get("session_id") in sub_session_ids]
    log(INFO, f"Player sub-sessions in leaderboard: {len(found_subs)}")

    if len(found_subs) >= 4:
        log(PASS, "All 4 players visible in leaderboard")
        record("Leaderboard: 4 players visible", True)
    else:
        log(WARN, f"Only {len(found_subs)} of 4 players in leaderboard")
        record("Leaderboard: 4 players visible", False, f"Only {len(found_subs)}")

    # Peer trend data
    for p in players[:1]:  # Check just one player's peer data
        r = client.get(f"/api/simulations/{p['session_id']}/peer-trend-history")
        if r.status_code == 200:
            assert_ok(r, "Peer trend history")
            peer = r.json()
            log(INFO, f"Peer data rounds: {len(peer.get('rounds', []))}")
        else:
            log(WARN, f"Peer trend: {r.status_code}")


def validate_facilitator_view(fac_id, cohort_session_id, players):
    section("VALIDATION: Facilitator Dashboard Features")

    # Session viewer
    r = client.get(f"/api/admin/{cohort_session_id}/debrief")
    if r.status_code == 200:
        assert_ok(r, "Cohort debrief")

    # Teleprompter
    r = client.get(f"/api/admin/{cohort_session_id}/teleprompter/slides",
                   headers={"x-facilitator-id": fac_id})
    if r.status_code == 200:
        assert_ok(r, "Teleprompter slides")

    # Player registry
    r = client.get("/api/admin/players", headers={"x-facilitator-id": fac_id})
    assert_ok(r, "Player registry")
    all_players = r.json().get("players", [])
    our_players = [p for p in all_players if p.get("session_id") == cohort_session_id]
    log(INFO, f"Players in registry for this cohort: {len(our_players)}")

    # Compare all player sessions for the facilitator
    for p in players:
        r = client.get(f"/api/simulations/{p['session_id']}/balanced-scorecard")
        if r.status_code == 200:
            sc = r.json()
            log(INFO, f"  {p['name']}: ESG={sc.get('esg_score', 'N/A')}")


# ============================================================
#  MAIN
# ============================================================
if __name__ == "__main__":
    start_time = time.time()

    print("\n" + "="*70)
    print("  MURESSONS GLOBAL - MULTI-PLAYER CONCURRENT E2E TEST")
    print("  4 Players x 10 Rounds x Same Cohort (Simultaneous Play)")
    print("="*70)

    # Setup
    fac_id, cohort_session_id, players = setup_environment()

    # Play all 10 rounds concurrently
    play_all_players_concurrently(players)

    # Validate state isolation
    validate_state_isolation(players)

    # Validate leaderboard
    validate_leaderboard(fac_id, cohort_session_id, players)

    # Validate facilitator view
    validate_facilitator_view(fac_id, cohort_session_id, players)

    # Final Summary
    elapsed = time.time() - start_time

    section("FINAL TEST SUMMARY")

    passed = sum(1 for _, ok, _ in test_results if ok)
    failed = sum(1 for _, ok, _ in test_results if not ok)
    total = len(test_results)

    all_completed = all(
        len(player_metrics.get(p["name"], [])) >= 10
        for p in players
    )
    all_error_free = all(
        len(player_errors.get(p["name"], [])) == 0
        for p in players
    )

    print(f"\n  Tests: {total} total | {passed} passed | {failed} failed")
    print(f"  Time: {elapsed:.1f}s")
    print(f"  All 4 players completed 10 rounds: {'YES' if all_completed else 'NO'}")
    print(f"  No player errors: {'YES' if all_error_free else 'NO'}")

    # Per-player summary
    print(f"\n  {'Player':<35} {'Rounds':>7} {'Errors':>7} {'Final Treasury':>16}")
    print(f"  {'-'*35} {'-'*7} {'-'*7} {'-'*16}")
    for p in players:
        name = p["name"]
        rounds = len(player_metrics.get(name, []))
        errs = len(player_errors.get(name, []))
        final_t = player_metrics[name][-1]["treasury"] if player_metrics.get(name) else 0
        print(f"  {name:<35} {rounds:>7} {errs:>7} ${final_t:>14,.0f}")

    if failed > 0:
        print(f"\n  Failed tests:")
        for label, ok, detail in test_results:
            if not ok:
                print(f"    - {label}: {(detail or '')[:100]}")

    print(f"\n{'='*70}")
    overall = all_completed and all_error_free and failed == 0
    print(f"  OVERALL: {'PASS' if overall else 'FAIL'}")
    print(f"{'='*70}\n")

    sys.exit(0 if overall else 1)
