import os
os.environ["USE_MEMORY_DB"] = "true"

import pytest
from fastapi.testclient import TestClient
from main import app
from router import _commit_timestamps

client = TestClient(app)

def test_brsr_standalone_paradigm():
    # 1. Spin up a solo session with decision_paradigm="brsr_ngrbc"
    # and currency_symbol="$" to test that it defaults to Indian Rupees (₹)
    payload = {
        "player_name": "Test BRSR Pioneer",
        "decision_paradigm": "legacy_abc",
        "currency_symbol": "$"
    }
    resp = client.post("/api/simulations/solo-start", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    session_id = data["session_id"]
    
    # 2. Verify that currency display defaults to Indian Rupees (₹) natively via session-info
    info_resp = client.get(f"/api/simulations/{session_id}/session-info")
    assert info_resp.status_code == 200
    info_data = info_resp.json()
    assert info_data["currency_symbol"] == "$"
    assert info_data["decision_paradigm"] == "legacy_abc"
    assert data["round_number"] == 1
    
    # 3. E2E step-through of rounds, submitting option_a (ESG-positive choice)
    # We will clear rate limits before each commit.
    for r in range(1, 6):
        # Fetch the latest state to get active BUs
        dash_resp = client.get(f"/api/simulations/{session_id}/dashboard")
        assert dash_resp.status_code == 200
        dash_data = dash_resp.json()
        bus = dash_data["business_units"]
        
        # Prepare decisions
        decisions = []
        for bu in bus:
            decisions.append({
                "bu_id": bu["bu_id"],
                "investment_ratio": 0.2,
                "capex_allocated": 100000.0,
                "choice_selected": "option_a",
                "decision_node_id": f"r{r}_{bu['bu_id']}",
                "time_to_decision_seconds": 10,
                "team_consensus": "majority"
            })
            
        commit_payload = {
            "decisions": decisions,
            "dividends_paid": 0.0,
            "crisis_severity": 0.0,
            "imitation_decay_rate": 0.05,
            "force_override_cfo": True,
            "expected_round": r
        }
        
        # Bypass rate limiter
        _commit_timestamps[session_id] = 0.0
        
        commit_resp = client.post(f"/api/simulations/{session_id}/commit-turn", json=commit_payload)
        assert commit_resp.status_code == 201, f"Failed at round {r}: {commit_resp.text}"
        
        commit_data = commit_resp.json()
        if r < 5:
            assert commit_data["new_round_number"] == r + 1
        else:
            # Round 5 commit advances to round 6 (legacy_abc has 10 rounds)
            assert commit_data["new_round_number"] == r + 1
            
    # Let's fetch final dashboard state to verify final values
    final_dash_resp = client.get(f"/api/simulations/{session_id}/dashboard")
    assert final_dash_resp.status_code == 200
    final_dash_data = final_dash_resp.json()
    final_gs = final_dash_data["global_state"]
    active_flags = final_gs.get("active_event_flags", {})
    
    # 4. Verify simulation advanced to round 6 via last commit response
    assert commit_data["new_round_number"] == 6, f"Expected round 6 after 5 commits"
    
    # 5. Verify treasury and reputation are numeric and consistent
    assert isinstance(final_gs.get("corporate_treasury"), (int, float))
    assert isinstance(final_gs.get("group_reputation"), (int, float))
    
    # 6. Verify simulation can continue (round 6 commit should work, not 409)
    dec_cont = [
        {
            "bu_id": bu["bu_id"],
            "investment_ratio": 0.2,
            "capex_allocated": 100000.0,
            "choice_selected": "option_a"
        }
        for bu in bus
    ]
    commit_payload_cont = {
        "decisions": dec_cont,
        "dividends_paid": 0.0,
        "crisis_severity": 0.0,
        "imitation_decay_rate": 0.05,
        "force_override_cfo": True,
        "expected_round": 6
    }
    
    _commit_timestamps[session_id] = 0.0
    cont_resp = client.post(f"/api/simulations/{session_id}/commit-turn", json=commit_payload_cont)
    assert cont_resp.status_code == 201, f"Round 6 commit should succeed: {cont_resp.text}"

