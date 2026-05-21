import sys
import time
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
BU_IDS = ["pharma", "electronics", "consumer_goods", "software"]

def api(method, path, data=None, expect=None):
    if method == "GET":
        r = client.get(path)
    elif method == "POST":
        r = client.post(path, json=data)
    elif method == "PUT":
        r = client.put(path, json=data)
    elif method == "DELETE":
        r = client.delete(path)
    if expect and r.status_code != expect:
        print(f"    !! {method} {path} => {r.status_code}: {r.text[:300]}")
    return r

# ────────────────────────────────────────────────────
# Session Setup
# ────────────────────────────────────────────────────
def create_parent_cohort(paradigm, label):
    r = api("POST", "/api/simulations/start", {
        "cohort_name": label,
        "decision_paradigm": paradigm,
    }, expect=201)
    assert r.status_code == 201, f"Create parent cohort failed: {r.status_code} {r.text[:200]}"
    d = r.json()
    sid = d["session_id"]
    print(f"  Parent Cohort: {sid} ({paradigm})")
    return sid

def join_cohort(parent_sid, player_name):
    # Induct player first
    r1 = api("POST", "/api/admin/players/induct", {
        "name": player_name,
        "email": f"{player_name}@test.com",
        "session_id": parent_sid,
        "assigned_bu": "global"
    }, expect=200)
    assert r1.status_code == 200, f"Player {player_name} induct failed: {r1.status_code} {r1.text[:200]}"
    p_data = r1.json()
    player_id = p_data["player_id"]
    password = p_data["password"]
    
    # Then join
    r = api("POST", f"/api/simulations/public/sessions/{parent_sid}/join", {
        "player_id": player_id,
        "password": password,
        "player_name": player_name
    }, expect=200)
    assert r.status_code == 200, f"Player {player_id} join failed: {r.status_code} {r.text[:200]}"
    d = r.json()
    player_sid = d["session_id"]
    print(f"    Player {player_id} joined -> Session: {player_sid}")
    return player_sid

def get_dashboard(sid):
    r = api("GET", f"/api/simulations/{sid}/dashboard")
    assert r.status_code == 200, f"Dashboard failed: {r.status_code}"
    return r.json()

# ────────────────────────────────────────────────────
# Stakeholder Map (Round 1 gate)
# ────────────────────────────────────────────────────
def submit_stakeholder_map(sid):
    r = api("GET", "/api/simulations/stakeholder-map/stakeholders")
    if r.status_code != 200: return False
    stakeholders = r.json().get("stakeholders", [])
    
    quadrants = ["high_power_high_interest", "high_power_low_interest", 
                 "low_power_high_interest", "low_power_low_interest"]
    mapping = {}
    for i, s in enumerate(stakeholders):
        sid_s = s.get("id", s.get("stakeholder_id", f"s{i}"))
        mapping[sid_s] = quadrants[i % 4]
    
    r2 = api("POST", f"/api/simulations/{sid}/stakeholder-map", {"mapping": mapping})
    return r2.status_code == 200

# ────────────────────────────────────────────────────
# Materiality Matrix (Round 2 gate)
# ────────────────────────────────────────────────────
def submit_materiality(sid, bu_id=None):
    r = api("GET", f"/api/admin/materiality-config/bu/{bu_id}" if bu_id else "/api/admin/materiality-config")
    if r.status_code != 200: return False
    config = r.json()
    issues = config.get("issues", [])
    
    q1, q2, q3, q4 = [], [], [], []
    for issue in issues:
        fi = issue.get("financial_impact", "low")
        si = issue.get("societal_impact", "low")
        if fi == "high" and si == "high": q1.append(issue["id"])
        elif fi == "high": q2.append(issue["id"])
        elif si == "high": q3.append(issue["id"])
        else: q4.append(issue["id"])
    
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
    if bu_id: payload["bu_id"] = bu_id
    
    r2 = api("POST", f"/api/simulations/{sid}/materiality", payload)
    return r2.status_code == 200

# ────────────────────────────────────────────────────
# Commit Turn
# ────────────────────────────────────────────────────
def commit_turn(sid, round_num, paradigm, player_idx):
    # Vary decisions by player index so they don't all get the exact same results
    options = ["option_a", "option_b", "option_c"]
    choice = options[(round_num + player_idx) % 3]
    
    dash = get_dashboard(sid)
    active_bus = [bu["bu_id"] for bu in dash.get("business_units", [])]
    if not active_bus: active_bus = BU_IDS
    
    decisions = []
    for i, bu in enumerate(active_bus):
        d = {
            "bu_id": bu,
            "investment_ratio": 0.2 + (0.1 * player_idx), # Vary investment
            "capex_allocated": 300000 + (100000 * player_idx), # Vary capex
            "choice_selected": choice if paradigm in ("legacy_abc", "healthcare") else "",
        }
        if paradigm in ("multi_toggles", "advanced_climate"):
            pillar_opts = ["aggressive", "moderate", "conservative"]
            p_choice = pillar_opts[(round_num + player_idx + i) % 3]
            d["pillar_decisions"] = {
                "energy": p_choice,
                "operations": p_choice,
                "supply_chain": p_choice,
                "offsetting": p_choice,
            }
        decisions.append(d)
    
    payload = {
        "decisions": decisions,
        "dividends_paid": 50000 * player_idx,
        "crisis_severity": 0,
        "force_override_cfo": True,
    }
    
    r = api("POST", f"/api/simulations/{sid}/commit-turn", payload)
    if r.status_code in (200, 201):
        return r.json()
    return None

# ────────────────────────────────────────────────────
# Full Multiplayer Test Runner
# ────────────────────────────────────────────────────
def run_multiplayer_test(paradigm):
    label = f"mp_test_{paradigm}_{int(time.time())}"
    print(f"\n{'='*60}")
    print(f"  MULTIPLAYER TEST: {paradigm.upper()}")
    print(f"{'='*60}")
    
    parent_sid = create_parent_cohort(paradigm, label)
    
    # Create 3 players
    players_info = [
        {"name": "Alice"},
        {"name": "Bob"},
        {"name": "Charlie"},
    ]
    
    player_sids = []
    for p in players_info:
        sid = join_cohort(parent_sid, p["name"])
        player_sids.append((p, sid))
    
    errors = []
    materiality_done = {}  # per-session materiality gate

    for rnd in range(1, 11):
        # Admin needs to unlock round for the cohort
        api("POST", f"/api/admin/{parent_sid}/rounds/{rnd}/unlock", {"unlocked": True})

        print(f"\n  -- Round {rnd} --")

        for idx, (p, sid) in enumerate(player_sids):
            if rnd == 1:
                if not submit_stakeholder_map(sid): errors.append(f"R1: {p['name']} map failed")
            elif rnd == 2 and not materiality_done.get(sid):
                if paradigm == "multi_toggles":
                    r = api("GET", f"/api/admin/{sid}/r2-bu-selection")
                    if r.status_code == 200:
                        bu_id = r.json().get("selected_bu")
                        submit_materiality(sid, bu_id=bu_id)
                    else:
                        submit_materiality(sid)
                else:
                    submit_materiality(sid)
                materiality_done[sid] = True

            result = commit_turn(sid, rnd, paradigm, idx)
            if not result:
                errors.append(f"R{rnd}: {p['name']} commit failed")
                continue

            gs = result.get("global_state", {})
            print(f"    {p['name']} => Treasury: ${gs.get('corporate_treasury', 0):,.0f} | Rep: {gs.get('group_reputation', 0):.1f}")
            # Respect 5-second per-session rate limiter between players
            time.sleep(5.2)

    # Check peer leaderboard for P1
    print(f"\n  -- Leaderboard Check --")
    p1_sid = player_sids[0][1]
    lb_res = api("GET", f"/api/simulations/{p1_sid}/peer-leaderboard")
    if lb_res.status_code == 200:
        lb = lb_res.json().get("leaderboard", [])
        print(f"    Peer Leaderboard has {len(lb)} entries")
        if len(lb) != 3: errors.append(f"Leaderboard size is {len(lb)}, expected 3")
        for rank, entry in enumerate(lb):
            print(f"      #{rank+1} {entry.get('name')} - Treasury: ${entry.get('treasury', 0):,.0f}")
    else:
        errors.append(f"Peer leaderboard failed: {lb_res.status_code}")

    if errors:
        print(f"\n  ERRORS: {errors}")
        return False
    print(f"  RESULT: PASS")
    return True

if __name__ == "__main__":
    print("="*60)
    print("  MURESSONS SIMULATION — MULTIPLAYER E2E TEST")
    print("="*60)
    
    r1 = run_multiplayer_test("legacy_abc")
    r2 = run_multiplayer_test("multi_toggles")
    r3 = run_multiplayer_test("advanced_climate")
    r4 = run_multiplayer_test("healthcare")
    
    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")
    print(f"  {'PASS' if r1 else 'FAIL'} legacy_abc")
    print(f"  {'PASS' if r2 else 'FAIL'} multi_toggles")
    print(f"  {'PASS' if r3 else 'FAIL'} advanced_climate")
    print(f"  {'PASS' if r4 else 'FAIL'} healthcare")
    print(f"{'='*60}")
    
    sys.exit(0 if (r1 and r2 and r3 and r4) else 1)
