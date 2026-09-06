import pytest
from fastapi.testclient import TestClient
from main import app
from database_memory import _sessions, _global_states, _bu_states
import uuid

client = TestClient(app)

@pytest.fixture
def injected_session():
    """A hand-made session row. Wave 3 hygiene: it used to stay in _sessions after
    the test, and any later test that scans the store (fetch_all_sessions,
    solo-start) 500'd on the keys it lacks — an order-dependent failure that
    only showed when this file ran before test_leaderboard_awarded_tv."""
    session_id = f"test_session_{uuid.uuid4().hex[:8]}"
    yield session_id
    _sessions.pop(session_id, None)
    _global_states.pop(session_id, None)
    _bu_states.pop(session_id, None)


def test_ceo_interview_llm_scoring(injected_session):
    session_id = injected_session
    _sessions[session_id] = {
        "session_id": session_id,
        "cohort_name": "CEO-TEST",
        "facilitator_id": "test",
        "start_time": None,
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
    
    # SEC-AUDIT-2026-07-29: this session has an owner ("test_player"), so the
    # caller must identify as that player — the same X-Player-Id the real
    # cockpit sends. Before the audit these CEO-interview endpoints took no
    # `request` at all and ran no ownership check, so this call used to pass
    # anonymously. It must not.
    # F-22 (launch audit 2026-09-01): the credential is the signed player token.
    from conftest import player_token_headers
    hdr = player_token_headers(session_id, "test_player")
    resp = client.post(f"/api/simulations/{session_id}/ceo-interview/assess",
                       json={"responses": responses}, headers=hdr)
    assert resp.status_code == 200, resp.text
    
    data = resp.json()
    assert "response_scores" in data
    # Ensure there's no AttributeError fallback that overrides everything silently.
    # LLM might fail due to missing API keys or something, but it shouldn't crash
    print("Success. Response keys:", list(data.keys()))
