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
        "decision_paradigm": "brsr_ngrbc",
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
    assert info_data["currency_symbol"] == "₹"
    assert info_data["decision_paradigm"] == "brsr_ngrbc"
    assert data["round_number"] == 1
    
    # 3. E2E step-through of all 5 rounds, submitting option_a (Radical Transparency/Pioneer choice)
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
            # Round 5 should cap at Round 5
            assert commit_data["new_round_number"] == 5
            
    # Let's fetch final dashboard state to verify final values
    final_dash_resp = client.get(f"/api/simulations/{session_id}/dashboard")
    assert final_dash_resp.status_code == 200
    final_dash_data = final_dash_resp.json()
    final_gs = final_dash_data["global_state"]
    active_flags = final_gs.get("active_event_flags", {})
    
    # 4. Verify consequence flags are written back to active_event_flags
    assert active_flags.get("brsr_track_completed") is True
    assert active_flags.get("brsr_pioneer") is True
    assert active_flags.get("brsr_net_positive_dividend") == 0.05
    
    # 5. Verify final terminal valuation outputs
    assert "terminal_value" in active_flags
    assert "regenerative_multiple" in active_flags
    assert "profile" in active_flags
    assert "profile_title" in active_flags
    
    # Confirm they are positive or match expectation
    assert active_flags["terminal_value"] > 0
    # 1.0 (base) + 0.05 (BRSR net positive dividend) + 0.35 (BRSR steward bonus, score=80 >= 70)
    # + 0.05 (wellbeing bonus, burnout < 20) - 0.4 (instability discount for avg_sl < 75) = 1.05
    assert active_flags["regenerative_multiple"] == 1.05
    assert active_flags["profile"] in ("regenerative_titan", "derisked_safe_haven", "fragile_giant", "stranded_relic")
    
    # 6. Confirm simulation terminates at Round 5 (returns 409 conflict if trying to commit round 6)
    # We prepare decisions again
    dec_err = [
        {
            "bu_id": bu["bu_id"],
            "investment_ratio": 0.2,
            "capex_allocated": 100000.0,
            "choice_selected": "option_a"
        }
        for bu in bus
    ]
    commit_payload_err = {
        "decisions": dec_err,
        "dividends_paid": 0.0,
        "crisis_severity": 0.0,
        "imitation_decay_rate": 0.05,
        "force_override_cfo": True,
        "expected_round": 5
    }
    
    _commit_timestamps[session_id] = 0.0
    err_resp = client.post(f"/api/simulations/{session_id}/commit-turn", json=commit_payload_err)
    assert err_resp.status_code == 409
    assert "already completed all 5 rounds" in err_resp.json()["detail"]
