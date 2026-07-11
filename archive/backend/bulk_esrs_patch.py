"""
Bulk-add ESRS fields (esrs_topic, value_chain_scope, time_horizon, severity_score, likelihood_score, is_ambiguous)
to all remaining issues in materiality_db.py that are missing them.
"""

# Map: issue_id -> (esrs_topic, value_chain_scope, time_horizon, severity_score, likelihood_score, is_ambiguous)
ESRS_MAP = {
    # Software BU
    "ai_bias":                   ("S4", "own_ops",    "short",  5, 4, False),
    "data_privacy":              ("S4", "own_ops",    "short",  5, 4, False),
    "cloud_energy":              ("E1", "own_ops",    "medium", 4, 4, False),
    "digital_divide":            ("S4", "downstream", "medium", 4, 3, True),
    "talent_retention":          ("S1", "own_ops",    "medium", 3, 4, False),
    "sw_exec_travel":            ("E1", "own_ops",    "short",  1, 1, False),
    "sw_social_media":           ("G1", "own_ops",    "short",  1, 1, False),
    # Oil & Gas BU
    "methane_leakage":           ("E1", "own_ops",    "short",  5, 4, False),
    "just_transition_refinery":  ("S1", "own_ops",    "medium", 5, 4, False),
    "water_contamination":       ("E3", "own_ops",    "short",  5, 3, False),
    "indigenous_land":           ("S3", "upstream",   "short",  4, 3, True),
    "og_exec_offsets":           ("E1", "own_ops",    "short",  1, 1, False),
    "og_csr_scholarships":       ("S3", "own_ops",    "short",  1, 1, False),
    # Financial Services BU
    "financed_emissions":        ("E1", "upstream",   "medium", 5, 4, False),
    "ai_credit_discrimination":  ("S4", "own_ops",    "short",  5, 4, False),
    "financial_inclusion":       ("S3", "downstream", "long",   3, 3, False),
    "fs_charity_gala":           ("G1", "own_ops",    "short",  1, 1, False),
    "fs_ergonomic":              ("S1", "own_ops",    "short",  1, 1, False),
    # Retail FMCG BU
    "eudr_deforestation":        ("E4", "upstream",   "short",  5, 4, False),
    "epr_plastic":               ("E5", "downstream", "short",  4, 4, False),
    "child_labour_cocoa":        ("S2", "upstream",   "medium", 5, 3, False),
    "product_safety_reach":      ("S4", "own_ops",    "short",  5, 3, False),
    "living_wage_tier4":         ("S2", "upstream",   "medium", 4, 4, False),
    "retail_seasonal_csr":       ("S1", "own_ops",    "short",  1, 1, False),
    "retail_composting":         ("E5", "own_ops",    "short",  1, 1, False),
    # Agriculture BU
    "tnfd_nature_disclosure":    ("E4", "own_ops",    "long",   4, 3, False),
    "soil_degradation":          ("E4", "own_ops",    "medium", 4, 4, False),
    "water_depletion":           ("E3", "own_ops",    "short",  5, 4, False),
    "smallholder_livelihoods":   ("S2", "upstream",   "medium", 4, 3, True),
    "biodiversity_loss":         ("E4", "own_ops",    "long",   4, 3, True),
    "pesticide_competitor":      ("G1", "own_ops",    "short",  2, 2, False),
    "ag_led_offices":            ("E1", "own_ops",    "short",  1, 1, False),
    "ag_exec_offsets":           ("E1", "own_ops",    "short",  1, 1, False),
    # Technology BU
    "eu_ai_act_compliance":      ("S4", "own_ops",    "short",  5, 4, False),
    "data_privacy_surveillance": ("S4", "own_ops",    "short",  5, 4, False),
    "cloud_energy_scope2":       ("E1", "own_ops",    "medium", 4, 4, False),
    "cybersecurity_resilience_tech": ("G1", "own_ops", "short", 4, 4, False),
    "competitor_ai_platform":    ("G1", "own_ops",    "short",  2, 2, False),
    "tech_social_media":         ("G1", "own_ops",    "short",  1, 1, False),
    "tech_exec_travel":          ("E1", "own_ops",    "short",  1, 1, False),
}

with open('materiality_db.py', 'r', encoding='utf-8') as f:
    src = f.read()

import re

patched = 0
missed = []

for issue_id, (topic, scope, horizon, sev, like, ambig) in ESRS_MAP.items():
    # Match the issue line: "id": "ISSUE_ID", ... "mitigation_cost_usd": NNNN}
    # We need to find the closing } of this issue dict on the same line
    pattern = f'"id": "{issue_id}", '
    idx = src.find(pattern)
    if idx == -1:
        missed.append(issue_id)
        continue

    # Find the end of this dict entry (the closing })
    end_idx = src.find('}', idx)
    if end_idx == -1:
        missed.append(issue_id)
        continue

    # Check it doesn't already have esrs_topic
    slice_check = src[idx:end_idx]
    if '"esrs_topic"' in slice_check:
        print(f'SKIP (already has): {issue_id}')
        continue

    # Insert fields before the closing }
    ambig_str = "True" if ambig else "False"
    new_fields = (
        f', "esrs_topic": "{topic}"'
        f', "value_chain_scope": "{scope}"'
        f', "time_horizon": "{horizon}"'
        f', "severity_score": {sev}'
        f', "likelihood_score": {like}'
        f', "is_ambiguous": {ambig_str}'
    )
    src = src[:end_idx] + new_fields + src[end_idx:]
    patched += 1

print(f'Patched: {patched} | Missed: {len(missed)}')
if missed:
    print('Missed IDs:', missed)

# Validate syntax
import ast
try:
    ast.parse(src)
    print('Syntax OK')
except SyntaxError as e:
    print(f'SYNTAX ERROR: {e}')

with open('materiality_db.py', 'w', encoding='utf-8') as f:
    f.write(src)
print('DONE')
