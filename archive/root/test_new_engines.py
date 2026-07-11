import sys
sys.path.insert(0, 'backend')

from black_swan_registry import evaluate_black_swans, DIFFICULTY_TIERS, BLACK_SWAN_EVENTS
print('Black Swan Registry: OK')
print(f'  Events: {len(BLACK_SWAN_EVENTS)}')
print(f'  Tiers: {list(DIFFICULTY_TIERS.keys())}')

from systemic_risk_engine import (
    calc_esg_adjusted_wacc, calc_supply_chain_transparency,
    calc_employer_brand, evaluate_tipping_points,
    evaluate_materiality_shocks, evaluate_npc_cascades,
    get_foreshadowing_for_round
)
print('Systemic Risk Engine: OK')

w, d = calc_esg_adjusted_wacc(0.05, 60, 40, 45, 0.3, 30)
print(f'  WACC: {w} (delta: {d["wacc_delta_bps"]}bps)')

sct, sd = calc_supply_chain_transparency(30, {'deep_audit_completed': True}, 1)
print(f'  Supply Chain Transparency: {sct}')

eb, ed = calc_employer_brand(50, 30, 60)
print(f'  Employer Brand: {eb} (risk: {ed["talent_risk_level"]})')

tp = evaluate_tipping_points(
    {'biodiversity_state': {'ecosystem_health_index': 20}},
    [{'carbon_intensity': 80, 'social_license_score': 30,
      'governance_risk_score': 40, 'staff_burnout_index': 50}]
)
print(f'  Tipping: climate={tp["dimensions"]["climate"]["tier"]}, social={tp["dimensions"]["social"]["tier"]}')

signals = get_foreshadowing_for_round(3, {'deep_audit_completed': True})
print(f'  Foreshadowing R3: {len(signals)} signal(s)')

cascades = evaluate_npc_cascades({'activist_investor': 20, 'regulator': 15}, 5)
print(f'  NPC Cascades: {len(cascades)} triggered')

print('\nAll engines validated successfully!')
