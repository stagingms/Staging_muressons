import sys
import asyncio
import router
import database_memory as dm

sys.stdout.reconfigure(encoding='utf-8')
router.db = dm

from router import commit_turn, SoloStartRequest, solo_start_simulation, CommitTurnRequest
from models import BUDecision

async def verify():
    print('Starting End-to-End Test for Real-World Scenarios...')
    
    # 1. Start a solo session in multi_toggles mode
    req = SoloStartRequest(player_name='Test_Real_World', decision_paradigm='multi_toggles')
    resp = await solo_start_simulation(req)
    session_id = resp.session_id
    
    state1 = await dm.fetch_latest_state(session_id)
    bus = state1['bu_states']
    
    # ── Test Scenario 1: Supplier Defection & Austerity ──
    decisions1 = []
    for bu in bus:
        decisions1.append(BUDecision(
            bu_id=bu['bu_id'],
            investment_ratio=0.10, # < 15% to trigger supplier defection
            capex_allocated=50000000, # Large CAPEX to trigger newly patched Austerity (loan > 50% treasury)
            pillar_decisions={'supply_chain': 'audit_suppliers'}
        ))
    
    commit_req1 = CommitTurnRequest(decisions=decisions1, crisis_severity=0.0)
    print('\nCommitting Round 1 (Testing Supplier Defection & Austerity Trigger)...')
    await commit_turn(session_id, commit_req1)
    
    state2 = await dm.fetch_latest_state(session_id)
    flags = state2['global_state'].get('active_event_flags', {})
    
    print('--- ROUND 1 RESULTS ---')
    print('Supplier Defection Active:', flags.get('supplier_defection', {}).get('active'))
    print('CFO Austerity Active (for next round):', flags.get('cfo_austerity_active'))
    
    print('\nWaiting 6 seconds to bypass rate limiting...')
    await asyncio.sleep(6)
    
    # ── Test Scenario 2: Regulatory Ratchet ──
    bus_state2 = state2['bu_states']
    for bu in bus_state2:
        bu['governance_risk_score'] = 50.0
    state2['bu_states'] = bus_state2
    await dm.update_latest_global_state(session_id, state2['global_state'], bus_state2)
    
    decisions2 = []
    for bu in bus_state2:
        decisions2.append(BUDecision(
            bu_id=bu['bu_id'],
            investment_ratio=0.50, # Austerity should clamp this
            capex_allocated=10000000, # Austerity should clamp this
            pillar_decisions={'supply_chain': 'audit_suppliers'}
        ))
    commit_req2 = CommitTurnRequest(decisions=decisions2, crisis_severity=0.0)
    print('\nCommitting Round 2 (Testing Regulatory Ratchet & Austerity Clamp)...')
    await commit_turn(session_id, commit_req2)
    
    state3 = await dm.fetch_latest_state(session_id)
    flags3 = state3['global_state'].get('active_event_flags', {})
    
    print('--- ROUND 2 RESULTS ---')
    print('Avg Inv Ratio Used (should be 0.0 due to Austerity):', flags3.get('greenwashing_avg_investment_ratio'))
    print('Regulatory Ratchet Active:', flags3.get('regulatory_ratchet', {}).get('active'))
    
    print('\nWaiting 6 seconds to bypass rate limiting...')
    await asyncio.sleep(6)
    
    # ── Test Scenario 3: Green Premium Squeeze ──
    bus_state3 = state3['bu_states']
    decisions3 = []
    for bu in bus_state3:
        decisions3.append(BUDecision(
            bu_id=bu['bu_id'],
            investment_ratio=0.50,
            capex_allocated=1,
            pillar_decisions={'product_innovation': 'redesign_product'}
        ))
        
    for bu in bus_state3:
        bu['social_license_score'] = 10
        
    state3['bu_states'] = bus_state3
    await dm.update_latest_global_state(session_id, state3['global_state'], bus_state3)

    commit_req3 = CommitTurnRequest(decisions=decisions3, crisis_severity=0.0)
    print('\nCommitting Round 3 (Testing Green Premium Squeeze)...')
    await commit_turn(session_id, commit_req3)

    state4 = await dm.fetch_latest_state(session_id)
    flags4 = state4['global_state'].get('active_event_flags', {})
    print('--- ROUND 3 RESULTS ---')
    print('Green Premium Squeeze Active:', flags4.get('green_premium_squeeze', {}).get('active'))
    
    print('\nWaiting 6 seconds to bypass rate limiting...')
    await asyncio.sleep(6)
    
    # ── Test Scenario 4: ALL TRAPS SIMULTANEOUSLY ──
    # To trigger Austerity we need low treasury + large loan.
    # To trigger Supplier Defection we need strict mandate + low investment ratio.
    # To trigger Green Premium Squeeze we need high investment ratio.
    # WAIT! Supplier Defection requires <15% investment, but Green Premium requires >25%.
    # We can trigger them on DIFFERENT BUs!
    
    bus_state4 = state4['bu_states']
    for bu in bus_state4:
        bu['governance_risk_score'] = 90.0 # High risk for Ratchet
        bu['social_license_score'] = 10.0  # Low social license for Green Premium Squeeze
        
    state4['bu_states'] = bus_state4
    await dm.update_latest_global_state(session_id, state4['global_state'], bus_state4)

    decisions4 = []
    # BU 1: Triggers Supplier Defection (low invest, strict mandate)
    decisions4.append(BUDecision(
        bu_id=bus_state4[0]['bu_id'],
        investment_ratio=0.10,
        capex_allocated=50000000, # High Capex to trigger Austerity next round
        pillar_decisions={'supply_chain': 'audit_suppliers'}
    ))
    # BU 2: Triggers Green Premium Squeeze (high invest, low social license)
    decisions4.append(BUDecision(
        bu_id=bus_state4[1]['bu_id'],
        investment_ratio=0.30,
        capex_allocated=50000000, # High Capex
        pillar_decisions={'product_innovation': 'redesign_product'}
    ))
    # Fill remaining BUs normally
    for bu in bus_state4[2:]:
        decisions4.append(BUDecision(
            bu_id=bu['bu_id'],
            investment_ratio=0.20,
            capex_allocated=1,
            pillar_decisions={'operations': 'energy_efficiency'}
        ))

    commit_req4 = CommitTurnRequest(decisions=decisions4, crisis_severity=0.0)
    print('\nCommitting Round 4 (Testing ALL TRAPS SIMULTANEOUSLY)...')
    await commit_turn(session_id, commit_req4)

    state5 = await dm.fetch_latest_state(session_id)
    flags5 = state5['global_state'].get('active_event_flags', {})
    
    print('--- ROUND 4 RESULTS (MEGA TRAP) ---')
    print('Supplier Defection Active:', flags5.get('supplier_defection', {}).get('active'))
    print('Green Premium Squeeze Active:', flags5.get('green_premium_squeeze', {}).get('active'))
    print('Regulatory Ratchet Active:', flags5.get('regulatory_ratchet', {}).get('active'))
    print('CFO Austerity Active (for next round):', flags5.get('cfo_austerity_active'))
    
    print('\nEnd-to-End Test Completed Successfully.')

if __name__ == '__main__':
    asyncio.run(verify())
