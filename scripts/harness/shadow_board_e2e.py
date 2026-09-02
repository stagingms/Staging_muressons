"""
E2E Test: Shadow Board Audit — Archetype Badge + Facilitator Dashboard Integration

Tests:
1. Create a cohort session
2. Advance to Round 5 via commit-turn
3. Trigger the Shadow Board Audit (GET endpoint)
4. Submit a rejection (POST endpoint)
5. Verify archetype is stored in active_event_flags
6. Verify leaderboard returns shadow_board_archetype + shadow_board_rejection

Moved from backend/test_shadow_board_e2e.py (F-38, 2026-09-02). Runs against a
LIVE server: MURESSONS_API=http://127.0.0.1:8000 python scripts/harness/shadow_board_e2e.py
(the original never imported `requests` nor defined SIM, so it could not run).
"""
import os
import requests

SIM = os.environ.get("MURESSONS_API", "http://127.0.0.1:8000").rstrip("/") + "/api/simulations"

def main():
    import uuid
    import time
    print("=" * 60)
    print("STEP 1: Creating cohort session...")
    r = requests.post(f"{SIM}/start", json={
        "cohort_name": f"ShadowBoard_E2E_Test_{uuid.uuid4()}",
        "facilitator_id": "test-facilitator",
        "decision_paradigm": "legacy_abc",
    })
    if r.status_code not in (200, 201):
        print(f"  FAIL: {r.status_code} -- {r.text[:300]}")
        sys.exit(1)

    data = r.json()
    session_id = data["session_id"]
    print(f"  OK: session_id = {session_id}")

    print("\nSTEP 2: Advancing to Round 5...")
    for round_num in range(1, 5):
        print(f"  Committing Round {round_num}...")
        if round_num > 1:
            time.sleep(6)  # Avoid rate limits
        r = requests.post(f"{SIM}/{session_id}/commit-turn", json={
            "decisions": [
                {"bu_id": "pharma", "decision_node_id": f"r{round_num}_pharma", "choice_selected": "option_a", "capex_allocated": 1, "pillar_decisions": {}},
                {"bu_id": "electronics", "decision_node_id": f"r{round_num}_electronics", "choice_selected": "option_a", "capex_allocated": 1, "pillar_decisions": {}},
                {"bu_id": "consumer_goods", "decision_node_id": f"r{round_num}_cg", "choice_selected": "option_a", "capex_allocated": 1, "pillar_decisions": {}},
                {"bu_id": "software", "decision_node_id": f"r{round_num}_sw", "choice_selected": "option_a", "capex_allocated": 1, "pillar_decisions": {}},
            ],
            "strategic_choice": "option_a",
            "force_override_cfo": True,
        })
        if r.status_code not in (200, 201):
            print(f"    FAIL: {r.status_code} -- {r.text[:200]}")
            sys.exit(1)
        result = r.json()
        new_round = result.get("new_round_number", result.get("round_number", "?"))
        print(f"    OK: Advanced to Round {new_round}")

    # ── Step 3: Verify at Round 5 ───────────────────────────────────
    print("\nSTEP 3: Verifying current state is Round 5...")
    r = requests.get(f"{SIM}/{session_id}/dashboard")
    state = r.json()
    current_round = state.get("current_round")
    print(f"  Current round: {current_round}")
    assert current_round == 5, f"Expected round 5, got {current_round}"

    # ── Step 4: Trigger Shadow Board Audit ──────────────────────────
    print("\nSTEP 4: Triggering Shadow Board Audit (GET)...")
    r = requests.get(f"{SIM}/{session_id}/shadow-board-audit")
    if r.status_code != 200:
        print(f"  FAIL: {r.status_code} -- {r.text[:200]}")
        sys.exit(1)
    audit = r.json()
    print(f"  audit_required: {audit.get('audit_required')}")
    personas = audit.get("personas", [])
    print(f"  personas: {[p['name'] for p in personas]}")
    assert audit["audit_required"] == True, "Expected audit_required=True"
    assert len(personas) == 3, f"Expected 3 personas, got {len(personas)}"
    print("  OK: 3 personas returned, audit required")

    # ── Step 5: Reject the Shareholder (should get Sustainability-First) ──
    print("\nSTEP 5: Rejecting Shareholder persona...")
    r = requests.post(f"{SIM}/{session_id}/shadow-board-audit/reject", json={
        "rejection_target": "shareholder",
    })
    if r.status_code != 200:
        print(f"  FAIL: {r.status_code} -- {r.text[:200]}")
        sys.exit(1)
    result = r.json()
    archetype = result.get("strategic_archetype", {}).get("archetype")
    flag = result.get("hidden_flag", {}).get("name")
    print(f"  archetype: {archetype}")
    print(f"  hidden_flag: {flag}")
    assert archetype == "Sustainability-First", f"Expected 'Sustainability-First', got '{archetype}'"
    assert flag == "shareholder_alienated", f"Expected 'shareholder_alienated', got '{flag}'"
    print("  OK: Archetype = Sustainability-First, Flag = shareholder_alienated")

    # ── Step 6: Verify flags persisted in game state ────────────────
    print("\nSTEP 6: Verifying flags in game state...")
    r = requests.get(f"{SIM}/{session_id}/dashboard")
    state = r.json()
    flags = state.get("global_state", {}).get("active_event_flags", {})
    print(f"  shadow_board_completed: {flags.get('shadow_board_completed')}")
    print(f"  shadow_board_archetype: {flags.get('shadow_board_archetype')}")
    print(f"  shadow_board_rejection: {flags.get('shadow_board_rejection')}")
    print(f"  shareholder_alienated: {flags.get('shareholder_alienated')}")
    assert flags.get("shadow_board_completed") == True
    assert flags.get("shadow_board_archetype") == "Sustainability-First"
    assert flags.get("shadow_board_rejection") == "shareholder"
    assert flags.get("shareholder_alienated") == True
    print("  OK: All shadow board flags correctly persisted")

    # ── Step 7: Check facilitator leaderboard returns archetype ─────
    print("\nSTEP 7: Checking facilitator leaderboard...")
    r = requests.get(f"{ADMIN}/leaderboard")
    if r.status_code != 200:
        print(f"  FAIL: {r.status_code} -- {r.text[:200]}")
        sys.exit(1)
    leaderboard = r.json().get("leaderboard", [])
    our_entry = next((e for e in leaderboard if e["session_id"] == session_id), None)
    if not our_entry:
        print("  FAIL: Session not found in leaderboard")
        sys.exit(1)
    print(f"  shadow_board_archetype: {our_entry.get('shadow_board_archetype')}")
    print(f"  shadow_board_rejection: {our_entry.get('shadow_board_rejection')}")
    assert our_entry["shadow_board_archetype"] == "Sustainability-First"
    assert our_entry["shadow_board_rejection"] == "shareholder"
    print("  OK: Leaderboard returns archetype + rejection correctly")

    # ── Step 8: Verify audit is no longer required after completion ─
    print("\nSTEP 8: Verify audit no longer required...")
    r = requests.get(f"{SIM}/{session_id}/shadow-board-audit")
    audit2 = r.json()
    assert audit2["audit_required"] == False, "Expected audit_required=False after completion"
    print(f"  audit_required: {audit2['audit_required']}")
    print("  OK: Audit no longer required (idempotent)")

    # ── Cleanup ─────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("ALL 8 TESTS PASSED -- Shadow Board E2E validated")
    print("=" * 60)

    # Clean up test session
    requests.delete(f"{ADMIN}/sessions/{session_id}?hard=true")

if __name__ == "__main__":
    main()
