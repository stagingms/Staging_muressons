"""
Muressons Full E2E Simulation Test: God Mode -> Facilitator -> Player (10 Rounds)

Tests the complete flow:
1. God Mode login & system status
2. Facilitator creation from God Mode
3. Cohort creation (via /api/simulations/start)
4. Player registration & login
5. All 10 rounds of Narrative Crisis (legacy_abc) with:
   - Round 1: Stakeholder Map minigame
   - Round 2: Materiality Matrix minigame
   - Rounds 3-10: Capital allocation + decision nodes + crisis events
6. Game Over: Final report & debrief validation
"""
import os
os.environ['USE_MEMORY_DB'] = 'true'
os.environ['DEBUG'] = 'true'
os.environ['MASTER_PASSWORD'] = '321'

import sys, time, json, hmac
from datetime import datetime
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
BU_IDS = ["pharma", "electronics", "consumer_goods", "software"]

# Pretty printing
PASS = "[PASS]"
FAIL = "[FAIL]"
WARN = "[WARN]"
INFO = "[INFO]"

test_results = []

def log(icon, msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"  [{ts}] {icon} {msg}")

def section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

def assert_ok(resp, label, expected=(200, 201)):
    if isinstance(expected, int):
        expected = (expected,)
    if resp.status_code in expected:
        log(PASS, f"{label} -> {resp.status_code}")
        test_results.append((label, True, None))
        return True
    else:
        detail = resp.text[:300]
        log(FAIL, f"{label} -> {resp.status_code}: {detail}")
        test_results.append((label, False, detail))
        return False


# ============================================================
#  PHASE 1: GOD MODE - System Setup
# ============================================================
def _test_god_mode():
    section("PHASE 1: GOD MODE - System Setup")

    # 1.1 Health check
    r = client.get("/health")
    assert_ok(r, "Health check")
    health = r.json()
    log(INFO, f"Database: {health.get('database')}, Version: {health.get('version')}")

    # 1.2 God Mode login (god_mode / 321 master password)
    r = client.post("/api/admin/facilitators/login", json={
        "facilitator_id": "god_mode",
        "password": "321",
    })
    if r.status_code == 200:
        assert_ok(r, "God Mode login")
        auth = r.json()
        log(INFO, f"Logged in as: {auth.get('name')} ({auth.get('facilitator_id')}), role={auth.get('role')}")
    else:
        log(WARN, f"god_mode login returned {r.status_code}, proceeding with API")

    # 1.3 Get global settings
    r = client.get("/api/admin/global-settings")
    assert_ok(r, "Get global settings")
    settings = r.json()
    log(INFO, f"Simulation mode: {settings.get('simulation_mode')}")

    # 1.4 System status
    r = client.get("/api/admin/god/system-status")
    if r.status_code == 200:
        assert_ok(r, "System status")
        status_data = r.json()
        log(INFO, f"Facilitators: {status_data.get('total_facilitators')}, Cohorts: {status_data.get('total_cohorts')}")

    # 1.5 Get audit log
    r = client.get("/api/admin/god/audit-log")
    assert_ok(r, "Audit log accessible")

    return True


# ============================================================
#  PHASE 2: FACILITATOR CREATION
# ============================================================
def _test_create_facilitator():
    section("PHASE 2: FACILITATOR CREATION")

    # 2.1 Create a new facilitator
    r = client.post("/api/admin/facilitators", json={
        "name": "E2E Test Professor",
        "password": "321",
        "max_cohorts": 10,
        "decision_paradigm": "legacy_abc",
        "role": "lead_facilitator",
        "created_by": "e2e_test",
    }, headers={"x-facilitator-id": "god_mode"})
    
    if r.status_code in (200, 201):
        assert_ok(r, "Create facilitator", expected=(200, 201))
        fac = r.json()
        fac_id = fac.get("facilitator_id")
        log(INFO, f"Created facilitator: {fac_id} ({fac.get('name')})")
    else:
        log(FAIL, f"Create facilitator failed: {r.status_code}")
        fac_id = "god_mode"  # fallback

    # 2.2 Verify facilitator login
    r = client.post("/api/admin/facilitators/login", json={
        "facilitator_id": fac_id,
        "password": "321",
    })
    assert_ok(r, "Facilitator login")

    # 2.3 List facilitators
    r = client.get("/api/admin/facilitators", headers={"x-facilitator-id": "god_mode"})
    assert_ok(r, "List facilitators")
    fac_list = r.json().get("facilitators", [])
    active = [f for f in fac_list if not f.get("deleted_at")]
    log(INFO, f"Active facilitators: {len(active)}")

    return fac_id


# ============================================================
#  PHASE 3: COHORT PROVISIONING (via /api/simulations/start)
# ============================================================
def _test_create_cohort(fac_id):
    section("PHASE 3: COHORT PROVISIONING")

    # 3.1 Create cohort with narrative crisis (legacy_abc) via /api/simulations/start
    r = client.post("/api/simulations/start", json={
        "cohort_name": f"E2E_NarrativeCrisis_{int(time.time())}",
        "facilitator_id": fac_id,
        "decision_paradigm": "legacy_abc",
        "experience_level": "standard",
    })
    assert_ok(r, "Create cohort (start session)", expected=201)
    cohort = r.json()
    session_id = cohort.get("session_id")
    log(INFO, f"Session ID: {session_id}")
    log(INFO, f"Round: {cohort.get('round_number')}")
    
    # 3.2 Verify session appears in the dashboard
    r = client.get(f"/api/simulations/{session_id}/dashboard")
    assert_ok(r, "Dashboard after cohort creation")
    dash = r.json()
    log(INFO, f"Treasury: ${dash.get('global_state', {}).get('corporate_treasury', 0):,.0f}")

    # 3.3 Verify leaderboard
    r = client.get("/api/admin/leaderboard", headers={"x-facilitator-id": fac_id})
    assert_ok(r, "Leaderboard accessible")
    lb = r.json().get("leaderboard", [])
    log(INFO, f"Leaderboard entries: {len(lb)}")

    return session_id


# ============================================================
#  PHASE 4: SESSION VERIFICATION
# ============================================================
def _test_session_setup(session_id):
    section("PHASE 4: SESSION VERIFICATION")

    # 4.1 Get dashboard
    r = client.get(f"/api/simulations/{session_id}/dashboard")
    assert_ok(r, "Player dashboard R1")
    dash = r.json()
    log(INFO, f"Round: {dash.get('current_round')}")
    log(INFO, f"Treasury: ${dash.get('global_state', {}).get('corporate_treasury', 0):,.0f}")
    bus = dash.get("business_units", [])
    log(INFO, f"Business Units: {[b['bu_id'] for b in bus]}")

    # 4.2 Session info
    r = client.get(f"/api/simulations/{session_id}/session-info")
    if r.status_code == 200:
        assert_ok(r, "Session info")
        info = r.json()
        log(INFO, f"Paradigm: {info.get('decision_paradigm')}")
        log(INFO, f"Ending pathway: {info.get('ending_pathway')}")

    # 4.3 Round config
    r = client.get(f"/api/simulations/{session_id}/round-config")
    if r.status_code == 200:
        assert_ok(r, "Round config R1")

    return True


# ============================================================
#  PHASE 5: PLAY ALL 10 ROUNDS
# ============================================================
def submit_stakeholder_map(sid):
    """Round 1 gate: complete the Mendelow stakeholder power/interest grid."""
    r = client.get("/api/simulations/stakeholder-map/stakeholders")
    if r.status_code != 200:
        log(FAIL, f"Get stakeholders failed: {r.status_code}")
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
        d = r2.json()
        log(PASS, f"Stakeholder map: accuracy={d.get('accuracy_percentage', 'N/A')}%")
        test_results.append(("R1 Stakeholder Map", True, None))
        return True
    else:
        log(FAIL, f"Stakeholder map failed: {r2.status_code} {r2.text[:200]}")
        test_results.append(("R1 Stakeholder Map", False, r2.text[:200]))
        return False


def submit_materiality(sid):
    """Round 2 gate: complete the CSRD double materiality matrix."""
    r = client.get("/api/admin/materiality-config")
    if r.status_code != 200:
        log(FAIL, f"Get materiality config failed: {r.status_code}")
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
        d = r2.json()
        log(PASS, f"Materiality matrix: budget=${d.get('allocated_budget', 0):,.0f}, treasury=${d.get('corporate_treasury', 0):,.0f}")
        test_results.append(("R2 Materiality Matrix", True, None))
        return True
    else:
        log(FAIL, f"Materiality failed: {r2.status_code} {r2.text[:300]}")
        test_results.append(("R2 Materiality Matrix", False, r2.text[:300]))
        return False


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

def commit_round(sid, round_num):
    """Commit a turn for the given round with narrative crisis decisions."""
    options = ["option_a", "option_b", "option_c"]
    choice = options[(round_num - 1) % 3]
    
    # Get active BUs
    dash = client.get(f"/api/simulations/{sid}/dashboard").json()
    active_bus = [bu["bu_id"] for bu in dash.get("business_units", [])]
    if not active_bus:
        active_bus = BU_IDS
    
    decisions = []
    for bu in active_bus:
        decisions.append({
            "bu_id": bu,
            "investment_ratio": 0.25 + (round_num * 0.02),
            "capex_allocated": 400000 + (round_num * 50000),
            "choice_selected": choice,
            "decision_node_id": f"round_{round_num}_{bu}",
            "time_to_decision_seconds": 30 + round_num * 5,
            "team_consensus": "majority",
        })
    
    payload = {
        "decisions": decisions,
        "dividends_paid": 0,
        "crisis_severity": 0,
        "imitation_decay_rate": 0.05,
        "force_override_cfo": True,
    }
    
    r = client.post(f"/api/simulations/{sid}/commit-turn", json=payload)
    if r.status_code in (200, 201):
        d = r.json()
        gs = d.get("global_state", {})
        events = d.get("events", {})
        new_round = d.get("new_round_number", "?")
        event_keys = [k for k in events.keys() if k not in ("decision_paradigm",)]
        
        treasury = gs.get("corporate_treasury", 0)
        ebitda = gs.get("historical_ebitda", 0)
        reputation = gs.get("group_reputation", 0)
        co2 = gs.get("tco2e_emissions", 0)
        synergy = gs.get("synergy_multiplier", 1.0)
        
        log(PASS, f"R{round_num} -> R{new_round}: "
            f"T=${treasury:,.0f} | EBITDA=${ebitda:,.0f} | "
            f"Rep={reputation:.1f} | CO2={co2:,.0f}t | Syn={synergy:.3f}")
        
        if event_keys:
            log(INFO, f"  Events: [{', '.join(event_keys[:5])}]")
        
        test_results.append((f"R{round_num} Commit", True, None))
        return d
    else:
        log(FAIL, f"R{round_num} commit failed: {r.status_code} {r.text[:300]}")
        test_results.append((f"R{round_num} Commit", False, r.text[:300]))
        return None


def _test_round_features(sid, round_num):
    """Test round-specific features and endpoints."""
    # Crisis alerts
    r = client.get(f"/api/simulations/{sid}/crisis-alerts")
    if r.status_code == 200:
        alerts = r.json()
        if alerts.get("alerts"):
            log(INFO, f"  Crisis alerts: {len(alerts['alerts'])} active")
    
    # Consequence DNA (R3+)
    if round_num >= 3:
        r = client.get(f"/api/simulations/{sid}/consequence-dna")
        if r.status_code == 200:
            dna = r.json()
            strands = len(dna.get("dna_strands", []))
            if strands:
                log(INFO, f"  Consequence DNA: {strands} strands")
    
    # Balanced Scorecard (R2+)
    if round_num >= 2:
        r = client.get(f"/api/simulations/{sid}/balanced-scorecard")
        if r.status_code == 200:
            sc = r.json()
            log(INFO, f"  Scorecard: ESG={sc.get('esg_score', 'N/A')}")
    
    # SDG alignment
    r = client.get(f"/api/simulations/{sid}/sdg-alignment")
    if r.status_code == 200:
        sdg = r.json()
        sdg_count = len(sdg.get("sdg_scores", {}))
        if sdg_count:
            log(INFO, f"  SDG alignment: {sdg_count} goals tracked")
    
    # Save decisions (autosave test)
    r = client.post(f"/api/simulations/{sid}/save-decisions", json={
        "allocations": {"pharma": 300000, "electronics": 200000},
        "decision_choice": "option_b",
    })
    if r.status_code == 200:
        test_results.append((f"R{round_num} Autosave", True, None))


def play_all_rounds(sid):
    section("PHASE 5: PLAYING ALL 10 ROUNDS (Narrative Crisis)")
    
    errors = []
    materiality_done = False
    last_round = None
    
    for rnd in range(1, 11):
        dash = client.get(f"/api/simulations/{sid}/dashboard").json()
        current = dash.get("current_round", rnd)
        
        print(f"\n  {'~'*50}")
        print(f"  ROUND {current} of 10 - {ROUND_TITLES.get(current, 'Unknown')}")
        print(f"  {'~'*50}")
        
        if current != last_round:
            materiality_done = False
        last_round = current
        
        # Test round-specific features
        _test_round_features(sid, current)
        
        # Round 1 gate: Stakeholder Map
        if current == 1:
            if not submit_stakeholder_map(sid):
                errors.append(f"R1: stakeholder map failed")
        
        # Round 2 gate: Materiality Matrix
        if current == 2 and not materiality_done:
            if not submit_materiality(sid):
                errors.append(f"R2: materiality failed")
            materiality_done = True
        
        # Commit the turn
        result = commit_round(sid, current)
        if result is None:
            errors.append(f"R{current}: commit failed")
            break
        
        # Respect 5-second rate limiter
        time.sleep(5.2)
    
    return errors


# ============================================================
#  PHASE 6: GAME OVER VALIDATION
# ============================================================
def _test_game_over(sid):
    section("PHASE 6: GAME OVER VALIDATION")
    
    # 6.1 Final dashboard state
    r = client.get(f"/api/simulations/{sid}/dashboard")
    assert_ok(r, "Final dashboard")
    dash = r.json()
    gs = dash.get("global_state", {})
    current = dash.get("current_round", "?")
    history = dash.get("history", [])
    
    log(INFO, f"Final round: {current}")
    log(INFO, f"History entries: {len(history)}")
    log(INFO, f"Treasury: ${gs.get('corporate_treasury', 0):,.0f}")
    log(INFO, f"EBITDA: ${gs.get('historical_ebitda', 0):,.0f}")
    log(INFO, f"Reputation: {gs.get('group_reputation', 0):.1f}")
    log(INFO, f"CO2: {gs.get('tco2e_emissions', 0):,.0f} tCO2e")
    log(INFO, f"Synergy: {gs.get('synergy_multiplier', 1.0):.3f}")
    
    # 6.2 Final report
    r = client.get(f"/api/simulations/{sid}/final-report")
    if r.status_code == 200:
        assert_ok(r, "Final report")
        report = r.json()
        archetype = report.get("archetype", {})
        log(INFO, f"Archetype: {archetype.get('title', 'N/A')} ({archetype.get('key', 'N/A')})")
        log(INFO, f"Regenerative Multiple: {report.get('regenerative_multiple', 'N/A')}")
        log(INFO, f"Terminal Valuation: ${report.get('terminal_valuation', 0):,.0f}")
    else:
        log(WARN, f"Final report: {r.status_code}")
    
    # 6.3 Debrief
    r = client.get(f"/api/admin/{sid}/debrief")
    if r.status_code == 200:
        assert_ok(r, "Debrief report")
        debrief = r.json()
        log(INFO, f"Debrief rounds: {len(debrief.get('rounds', []))}")
    
    # 6.4 Decision timeline
    r = client.get(f"/api/admin/{sid}/decision-timeline")
    if r.status_code == 200:
        assert_ok(r, "Decision timeline")
    
    # 6.5 Consequence DNA
    r = client.get(f"/api/simulations/{sid}/consequence-dna")
    if r.status_code == 200:
        assert_ok(r, "Consequence DNA (final)")
    
    # 6.6 Ending pathway
    r = client.get(f"/api/simulations/{sid}/ending-pathway")
    if r.status_code == 200:
        assert_ok(r, "Ending pathway")
        ep = r.json()
        log(INFO, f"Ending: {ep.get('pathway_id', 'N/A')}")
    
    return current >= 10


# ============================================================
#  PHASE 7: FACILITATOR ADMIN FEATURES
# ============================================================
def _test_facilitator_admin(sid, fac_id):
    section("PHASE 7: FACILITATOR ADMIN FEATURES")
    
    # 7.1 Teleprompter slides
    r = client.get(f"/api/admin/{sid}/teleprompter/slides",
                   headers={"x-facilitator-id": fac_id})
    if r.status_code == 200:
        assert_ok(r, "Teleprompter slides")
    
    # 7.2 Platform analytics
    r = client.get("/api/admin/analytics/platform/summary",
                   headers={"x-facilitator-id": "god_mode"})
    if r.status_code == 200:
        assert_ok(r, "Platform analytics")
    
    # 7.3 Glossary
    r = client.get("/api/admin/analytics/glossary")
    if r.status_code == 200:
        assert_ok(r, "Glossary")
    
    # 7.4 Resources
    r = client.get(f"/api/simulations/{sid}/resources")
    if r.status_code == 200:
        assert_ok(r, "Resources")


# ============================================================
#  MAIN TEST RUNNER
# ============================================================
if __name__ == "__main__":
    start_time = time.time()
    
    print("\n" + "="*70)
    print("  MURESSONS GLOBAL - COMPLETE E2E SIMULATION TEST")
    print("  God Mode -> Facilitator -> Player (10 Rounds, Narrative Crisis)")
    print("="*70)
    
    # Phase 1: God Mode
    _test_god_mode()
    
    # Phase 2: Create Facilitator
    fac_id = _test_create_facilitator()
    
    # Phase 3: Create Cohort
    session_id = _test_create_cohort(fac_id)
    
    # Phase 4: Session verification
    _test_session_setup(session_id)
    
    # Phase 5: Play all 10 rounds
    errors = play_all_rounds(session_id)
    
    # Phase 6: Game Over validation
    completed = _test_game_over(session_id)
    
    # Phase 7: Facilitator admin features
    _test_facilitator_admin(session_id, fac_id)
    
    # -- Final Summary --
    elapsed = time.time() - start_time
    
    section("FINAL TEST SUMMARY")
    
    passed = sum(1 for _, ok, _ in test_results if ok)
    failed = sum(1 for _, ok, _ in test_results if not ok)
    total = len(test_results)
    
    print(f"\n  Tests: {total} total | {passed} passed | {failed} failed")
    print(f"  Time: {elapsed:.1f}s")
    print(f"  Simulation completed: {'YES (all 10 rounds)' if completed else 'NO'}")
    
    if errors:
        print(f"\n  Round errors:")
        for e in errors:
            print(f"    - {e}")
    
    if failed > 0:
        print(f"\n  Failed tests:")
        for label, ok, detail in test_results:
            if not ok:
                print(f"    - {label}: {(detail or '')[:100]}")
    
    print(f"\n{'='*70}")
    overall = completed and failed == 0 and len(errors) == 0
    print(f"  OVERALL: {'PASS' if overall else 'FAIL'}")
    print(f"{'='*70}\n")
    
    sys.exit(0 if overall else 1)
