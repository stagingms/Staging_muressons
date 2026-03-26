import sys
import asyncio
from fastapi.testclient import TestClient

# Must import from current dir
sys.path.append(".")
from main import app

client = TestClient(app)

def run_tests():
    print("Starting verification tests...")
    
    # 1. Start a session
    res = client.post("/api/simulations/start", json={"cohort_name": "Test Cohort", "facilitator_id": "admin"})
    sid = res.json()["session_id"]
    print("Started session:", sid)
    
    res = client.post(f"/api/simulations/public/sessions/{sid}/join", json={"player_id": "test_player", "password": "pass"})
    if res.status_code != 200:
        print("Join error:", res.json())
    pid = res.json()["player_id"]
    player_sid = res.json()["session_id"]
    
    # 3. Set username for player
    res = client.post("/api/simulations/set-username", json={"user_id": "test_player", "role": "player", "username": "StarLord"})
    assert res.json()["username"] == "StarLord", "Set username failed"
    
    # 4. Login as player
    res = client.post("/api/simulations/player-login", json={"player_id": "test_player", "password": "pass"})
    assert res.json()["username"] == "StarLord", "Player login did not return username"
    
    # 5. Check peer leaderboard username
    res = client.get(f"/api/simulations/{player_sid}/peer-leaderboard")
    leaderboard = res.json().get("leaderboard", [])
    print(f"Peer leaderboard for {player_sid}: {leaderboard}")
    
    # 6. Admin login (new fac)
    res = client.post("/api/admin/facilitators/login", json={"facilitator_id": "newfac", "password": "321"})
    fac_username = res.json().get("username", "")
    assert fac_username == "", "New facilitator should have empty username"
    
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
    res = client.post("/api/simulations/start", json={"cohort_name": "Hard Delete Cohort", "facilitator_id": "admin"})
    sid2 = res.json()["session_id"]
    res = client.delete(f"/api/admin/{sid2}/reset?hard=true")
    assert res.json()["status"] == "deleted", "Hard delete failed"
    
    print("✅ ALL TESTS PASSED!")

if __name__ == "__main__":
    run_tests()
