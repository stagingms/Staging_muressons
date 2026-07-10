"""Patch script: add ESRS fields to remaining BU issues in materiality_db.py"""
import re

with open('materiality_db.py', 'r', encoding='utf-8') as f:
    src = f.read()

# ── Fix "economic" category → "governance" for all remaining issues ──────────
# Each tuple: (old_suffix, new_suffix)  — appended after mitigation_cost
patches = [
    # software: open_source_risk
    ('"category": "economic", "financial_impact": "high", "societal_impact": "medium", "mitigation_cost_usd": 800000}',
     '"category": "governance", "financial_impact": "high", "societal_impact": "medium", "mitigation_cost_usd": 800000, "esrs_topic": "G1", "value_chain_scope": "own_ops", "time_horizon": "short", "severity_score": 3, "likelihood_score": 3, "is_ambiguous": False}'),
    # oil_gas: stranded_asset_risk
    ('"category": "economic", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 5000000}',
     '"category": "governance", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 5000000, "esrs_topic": "G1", "value_chain_scope": "own_ops", "time_horizon": "long", "severity_score": 5, "likelihood_score": 4, "is_ambiguous": True}'),
    # oil_gas: lng_price_volatility
    ('"category": "economic", "financial_impact": "high", "societal_impact": "low", "mitigation_cost_usd": 1500000}',
     '"category": "governance", "financial_impact": "high", "societal_impact": "low", "mitigation_cost_usd": 1500000, "esrs_topic": "G1", "value_chain_scope": "own_ops", "time_horizon": "short", "severity_score": 3, "likelihood_score": 3, "is_ambiguous": False}'),
    # financial_services: climate_credit_risk
    ('"category": "economic", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 4000000}',
     '"category": "governance", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 4000000, "esrs_topic": "G1", "value_chain_scope": "own_ops", "time_horizon": "medium", "severity_score": 4, "likelihood_score": 4, "is_ambiguous": True}'),
    # financial_services: sfdr_greenwashing_risk
    ('"category": "economic", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 3500000}',
     '"category": "governance", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 3500000, "esrs_topic": "G1", "value_chain_scope": "own_ops", "time_horizon": "short", "severity_score": 5, "likelihood_score": 4, "is_ambiguous": False}'),
    # financial_services: cybersecurity_resilience
    ('"category": "economic", "financial_impact": "high", "societal_impact": "low", "mitigation_cost_usd": 8000000}',
     '"category": "governance", "financial_impact": "high", "societal_impact": "low", "mitigation_cost_usd": 8000000, "esrs_topic": "G1", "value_chain_scope": "own_ops", "time_horizon": "short", "severity_score": 4, "likelihood_score": 4, "is_ambiguous": False}'),
    # retail_fmcg: consumer_spending_risk
    ('"category": "economic", "financial_impact": "high", "societal_impact": "low", "mitigation_cost_usd": 1000000}',
     '"category": "governance", "financial_impact": "high", "societal_impact": "low", "mitigation_cost_usd": 1000000, "esrs_topic": "G1", "value_chain_scope": "own_ops", "time_horizon": "short", "severity_score": 3, "likelihood_score": 3, "is_ambiguous": False}'),
]

for old, new in patches:
    if old in src:
        src = src.replace(old, new, 1)
        print(f"OK: {old[:60]}")
    else:
        print(f"MISS: {old[:60]}")

# ── Add interdependencies to software BU ─────────────────────────────────────
src = src.replace(
    '"interdependencies": []\n    },\n    "oil_gas"',
    '"interdependencies": [\n            {"source": "ai_bias", "target": "data_privacy", "severity": "high",'
    ' "description": "EU AI Act high-risk classification amplifies GDPR obligations"},\n'
    '            {"source": "cloud_energy", "target": "ai_bias", "severity": "medium",'
    ' "description": "AI compute energy creates both E1 and S4 exposure"}\n        ]\n    },\n    "oil_gas"',
    1
)

# ── Add interdependencies to financial_services BU ───────────────────────────
src = src.replace(
    '"interdependencies": []\n    },\n    "retail_fmcg"',
    '"interdependencies": [\n            {"source": "climate_credit_risk", "target": "financed_emissions", "severity": "high",'
    ' "description": "Loan book stranded asset exposure amplifies Scope 3 Cat.15 financed emissions"},\n'
    '            {"source": "ai_credit_discrimination", "target": "sfdr_greenwashing_risk", "severity": "medium",'
    ' "description": "AI governance failures undermine ESG fund credibility"}\n        ]\n    },\n    "retail_fmcg"',
    1
)

# ── Add interdependencies to retail_fmcg BU ──────────────────────────────────
src = src.replace(
    '"interdependencies": []\n    },\n    "agriculture"',
    '"interdependencies": [\n            {"source": "eudr_deforestation", "target": "child_labour_cocoa", "severity": "high",'
    ' "description": "Same W.Africa/SE Asia sourcing regions concentrate E4 deforestation and S2 child labour risk"},\n'
    '            {"source": "epr_plastic", "target": "product_safety_reach", "severity": "medium",'
    ' "description": "Packaging changes expose product formulation REACH compliance gaps"}\n        ]\n    },\n    "agriculture"',
    1
)

# ── Verify no "economic" category remains ────────────────────────────────────
remaining = [(i+1, l.strip()) for i, l in enumerate(src.splitlines()) if '"category": "economic"' in l]
if remaining:
    print(f"\nWARNING: {len(remaining)} 'economic' category entries remain:")
    for ln, txt in remaining:
        print(f"  Line {ln}: {txt[:80]}")
else:
    print("\nAll 'economic' categories resolved.")

with open('materiality_db.py', 'w', encoding='utf-8') as f:
    f.write(src)
print("DONE — materiality_db.py patched.")
