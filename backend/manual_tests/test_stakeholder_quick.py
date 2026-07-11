"""Quick validation of stakeholder_map.py changes."""
from stakeholder_map import evaluate_stakeholder_map, get_stakeholder_list, STAKEHOLDERS, ALTERNATE_MAP

print(f"Stakeholders: {len(STAKEHOLDERS)}")
print(f"Alternate quadrants: {ALTERNATE_MAP}")

# Perfect score
r = evaluate_stakeholder_map({
    'activist_fund': 'manage_closely', 'eu_regulators': 'manage_closely',
    'local_communities': 'keep_informed', 'tier3_miners': 'keep_informed',
    'factory_employees': 'keep_informed', 'syndicate_banks': 'keep_satisfied',
    'national_gov': 'keep_satisfied', 'cafeteria_vendors': 'monitor',
    'gen_public': 'monitor', 'local_media': 'monitor',
})
print(f"\nPerfect: {r['accuracy_percentage']}%, Tier: {r['scoring_tier']}, Pts: {r['points_awarded']}")
assert r['accuracy_percentage'] == 100.0
assert r['points_awarded'] == 3000
assert r['treasury_penalty'] == 0
assert r['reputation_penalty'] == 0

# C17: Alternate quadrant accepted
r2 = evaluate_stakeholder_map({
    'activist_fund': 'manage_closely', 'eu_regulators': 'manage_closely',
    'local_communities': 'keep_informed', 'tier3_miners': 'keep_informed',
    'factory_employees': 'keep_informed', 'syndicate_banks': 'keep_satisfied',
    'national_gov': 'keep_satisfied', 'cafeteria_vendors': 'monitor',
    'gen_public': 'monitor', 'local_media': 'keep_informed',  # alternate
})
print(f"Alt accepted: {r2['accuracy_percentage']}%, Tier: {r2['scoring_tier']}")
assert r2['accuracy_percentage'] == 100.0, f"Expected 100%, got {r2['accuracy_percentage']}"

# All wrong — treasury + rep penalty
r3 = evaluate_stakeholder_map({
    'activist_fund': 'monitor', 'eu_regulators': 'monitor',
    'local_communities': 'monitor', 'tier3_miners': 'monitor',
    'factory_employees': 'monitor', 'syndicate_banks': 'monitor',
    'national_gov': 'monitor', 'cafeteria_vendors': 'manage_closely',
    'gen_public': 'manage_closely', 'local_media': 'manage_closely',
})
print(f"All wrong: {r3['accuracy_percentage']}%, Treasury penalty: {r3['treasury_penalty']}, Rep penalty: {r3['reputation_penalty']}")
assert r3['treasury_penalty'] == -500_000
assert r3['reputation_penalty'] == -3

# C13: Urgency debrief
print(f"\nUrgency debrief: {len(r['urgency_debrief'])} items")
assert len(r['urgency_debrief']) == 10
high_urgency = [u for u in r['urgency_debrief'] if u['urgency'] == 'high']
print(f"High urgency stakeholders: {[u['name'] for u in high_urgency]}")

# C8: Engagement tactics
print(f"Engagement tactics: {len(r['engagement_tactics'])} stakeholders")
assert len(r['engagement_tactics']) == 2  # activist_fund + eu_regulators

# C15: Intel dossier
sl = get_stakeholder_list()
print(f"\nBank items: {len(sl)}, has dossier: {bool(sl[0].get('intel_dossier'))}")
assert len(sl) == 10
assert 'correct_quadrant' not in sl[0]  # Security: no answer leakage
assert len(sl[0]['intel_dossier']) >= 2

print("\n[OK] ALL STAKEHOLDER MAP VALIDATIONS PASSED")
