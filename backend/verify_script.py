import sys
import asyncio
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from fastapi.testclient import TestClient

# Must import from current dir
sys.path.append(".")
from main import app

client = TestClient(app)

def run_tests():
    print("Starting verification tests...")
    
    import time
    
    # 0. Create a fresh facilitator to bypass cohort limits
    fac_res = client.post("/api/admin/facilitators/batch", json={"names": [f"TestFac {int(time.time())}"]})
    test_fac_id = fac_res.json()["created"][0]["facilitator_id"]
    
    # 1. Start a session
    test_cohort_name = f"Test Cohort {int(time.time())}"
    res = client.post("/api/simulations/start", json={"cohort_name": test_cohort_name, "facilitator_id": test_fac_id})
    if "session_id" not in res.json():
        print("Start session error:", res.json())
        sys.exit(1)
    sid = res.json()["session_id"]
    print("Started session:", sid)
    
    # 2. Generate a valid player_id for the cohort
    res = client.post(f"/api/admin/{sid}/generate-player")
    valid_pid = res.json().get("player_id")
    generated_pass = res.json().get("password")
    print("Generated player:", valid_pid)
    
    res = client.post(f"/api/simulations/public/sessions/{sid}/join", json={"player_id": valid_pid, "password": generated_pass})
    if res.status_code != 200:
        print("Join error:", res.json())
        sys.exit(1)
        
    player_sid = res.json()["session_id"]
    
    # 3. Set username for player
    res = client.post("/api/simulations/set-username", json={"user_id": valid_pid, "role": "player", "username": "StarLord"})
    assert res.json()["username"] == "StarLord", "Set username failed"
    
    # 4. Login as player
    res = client.post("/api/simulations/player-login", json={"player_id": valid_pid, "password": generated_pass})
    assert res.json()["username"] == "StarLord", "Player login did not return username"
    
    # 5. Check peer leaderboard username
    res = client.get(f"/api/simulations/{player_sid}/peer-leaderboard")
    leaderboard = res.json().get("leaderboard", [])
    print(f"Peer leaderboard for {player_sid}: {leaderboard}")
    
    # 6. Admin login (new fac)
    res = client.post("/api/admin/facilitators/login", json={"facilitator_id": "newfac", "password": "321"})
    fac_username = res.json().get("username", "")
    assert fac_username in ("", "AdminMaster"), "New facilitator should have empty username or be persisted"
    
    # 7. Set facilitator username
    res = client.post("/api/simulations/set-username", json={"user_id": "newfac", "role": "facilitator", "username": "AdminMaster"})
    assert res.json()["username"] == "AdminMaster", "Set facilitator username failed"
    
    # 8. Admin login again
    res = client.post("/api/admin/facilitators/login", json={"facilitator_id": "newfac", "password": "321"})
    assert res.json()["username"] == "AdminMaster", "Admin login did not return username"
    
    # 9. Verify soft delete session
    res = client.delete(f"/api/admin/{sid}/reset")
    assert res.json()["status"] == "deleted", "Soft delete failed"
    
    # 10. Verify active public sessions does not show soft deleted
    res = client.get("/api/simulations/public/sessions")
    sids = [s["session_id"] for s in res.json().get("sessions", [])]
    assert sid not in sids, "Soft deleted session still in public sessions"
    
    # 11. Verify hard delete session
    res = client.post("/api/simulations/start", json={"cohort_name": "Hard Delete Cohort", "facilitator_id": "admin-harddelete"})
    sid2 = res.json()["session_id"]
    res = client.delete(f"/api/admin/{sid2}/reset?hard=true")
    assert res.json()["status"] == "deleted", "Hard delete failed"
    
    print("✅ ALL TESTS PASSED!")

if __name__ == "__main__":
    run_tests()
