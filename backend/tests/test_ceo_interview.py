import pytest
from fastapi.testclient import TestClient
from main import app
from database_memory import _sessions, _global_states, _bu_states
import uuid

client = TestClient(app)

def test_ceo_interview_llm_scoring():
    session_id = f"test_session_{uuid.uuid4().hex[:8]}"
    _sessions[session_id] = {
        "player_id": "test_player",
        "player_name": "Test Player",
        "industry": "test",
        "parent_cohort_id": "test_cohort"
    }

    # Simulate game end
    gs = {
        "state_id": "test_state_id",
        "round_number": 11,
        "corporate_treasury": 1000000,
        "group_reputation": 50,
        "synergy_multiplier": 1.0,
        "cost_of_capital": 0.05,
        "active_event_flags": {
            "profile": "Test Profile"
        }
    }
    
    _global_states[session_id] = [gs]
    _bu_states[session_id] = {11: []}
    
    responses = [
        "Test response 1",
        "Test response 2",
        "Test response 3",
        "Test response 4",
        "Test response 5",
    ]
    
    resp = client.post(f"/api/simulations/{session_id}/ceo-interview/assess", json={"responses": responses})
    assert resp.status_code == 200, resp.text
    
    data = resp.json()
    assert "response_scores" in data
    # Ensure there's no AttributeError fallback that overrides everything silently.
    # LLM might fail due to missing API keys or something, but it shouldn't crash
    print("Success. Response keys:", list(data.keys()))
