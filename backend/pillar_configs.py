"""
Muressons Global Command — Strategic Pillars Configuration
Defines the 4-area decision options per round for the "multi_toggles" paradigm.
Each round has options for: Energy, Operations, Supply Chain, Offsetting.
"""

from __future__ import annotations
from typing import Any
import copy
import json
import os
from pathlib import Path

OVERRIDES_FILE = Path(__file__).parent / "decision_overrides.json"


# ═════════════════════════════════════════════════════════════════
#  PILLAR OPTIONS PER ROUND
#  Each round maps 4 areas → 3 actions each.
#  Actions have: cost (treasury delta), impacts (capital deltas),
#  flags_set (for round_logic compatibility).
# ═════════════════════════════════════════════════════════════════

PILLAR_OPTIONS: dict[int, dict[str, Any]] = {

    # ── Round 1: Foundations ────────────────────────────────────
    1: {
        "title": "ESG Foundation Strategy",
        "description": "Set your initial ESG investment strategy across four key areas.",
        "areas": {
            "energy": {
                "label": "Energy Strategy",
                "icon": "⚡",
                "options": {
                    "renewable_ppa": {
                        "title": "Renewable PPA",
                        "description": "Sign a 10-year Power Purchase Agreement for renewable energy.",
                        "cost": -2_000_000,
                        "impacts": {"carbon_intensity_delta": -8, "reputation": +3},
                        "flags_set": ["renewable_ppa_signed"],
                    },
                    "fossil_status_quo": {
                        "title": "Fossil Fuel Status Quo",
                        "description": "Maintain existing energy contracts. No cost, no progress.",
                        "cost": 0,
                        "impacts": {"carbon_intensity_delta": +2, "reputation": -1},
                        "flags_set": ["fossil_status_quo"],
                    },
                    "solar_capex": {
                        "title": "Solar CapEx",
                        "description": "Build on-site solar arrays across manufacturing facilities.",
                        "cost": -4_000_000,
                        "impacts": {"carbon_intensity_delta": -12, "reputation": +5},
                        "flags_set": ["solar_investment"],
                    },
                },
            },
            "operations": {
                "label": "Operational Efficiency",
                "icon": "🏭",
                "options": {
                    "lean_process": {
                        "title": "Lean Process Optimization",
                        "description": "Implement lean manufacturing across all BUs.",
                        "cost": -1_500_000,
                        "impacts": {"reputation": +2},
                        "flags_set": ["lean_process"],
                    },
                    "digital_twin": {
                        "title": "Digital Twin Deployment",
                        "description": "Deploy digital twin technology for predictive maintenance.",
                        "cost": -3_000_000,
                        "impacts": {"reputation": +4, "governance_risk_delta": -3},
                        "flags_set": ["digital_twin"],
                    },
                    "no_change": {
                        "title": "No Operational Change",
                        "description": "Status quo operations. No investment required.",
                        "cost": 0,
                        "impacts": {},
                        "flags_set": [],
                    },
                },
            },
            "supply_chain": {
                "label": "Supply Chain",
                "icon": "🔗",
                "options": {
                    "audit_suppliers": {
                        "title": "Full Supplier Audit",
                        "description": "Commission deep ESG audits across all tier-1 suppliers.",
                        "cost": -2_500_000,
                        "impacts": {"reputation": +4, "social_license_delta": +3},
                        "flags_set": ["deep_audit_completed"],
                    },
                    "tier1_only": {
                        "title": "Tier-1 Screening Only",
                        "description": "Screen primary suppliers only. Blind spots remain.",
                        "cost": -500_000,
                        "impacts": {"reputation": +1},
                        "flags_set": ["electronics_blindspot"],
                    },
                    "defer": {
                        "title": "Defer Supply Chain Review",
                        "description": "Postpone supply chain assessments. Risk accumulates.",
                        "cost": 0,
                        "impacts": {"reputation": -2, "governance_risk_delta": +5},
                        "flags_set": ["electronics_blindspot"],
                    },
                },
            },
            "offsetting": {
                "label": "Carbon Offsetting",
                "icon": "🌱",
                "options": {
                    "nature_based": {
                        "title": "Nature-Based Offsets",
                        "description": "Invest in verified reforestation and wetland restoration.",
                        "cost": -2_000_000,
                        "impacts": {"natural_capital_debt_delta": -5, "reputation": +3},
                        "flags_set": ["nature_offsets"],
                    },
                    "carbon_credits": {
                        "title": "Carbon Credit Purchase",
                        "description": "Buy verified carbon credits on the open market.",
                        "cost": -1_000_000,
                        "impacts": {"natural_capital_debt_delta": -2, "reputation": +1},
                        "flags_set": ["carbon_credits"],
                    },
                    "no_offsetting": {
                        "title": "No Offsetting",
                        "description": "No offset investment this round.",
                        "cost": 0,
                        "impacts": {"natural_capital_debt_delta": +3},
                        "flags_set": [],
                    },
                },
            },
        },
    },

    # ── Round 2: Double Materiality ─────────────────────────────
    2: {
        "title": "Double Materiality Investment",
        "description": "Align capital allocation with double materiality principles.",
        "areas": {
            "energy": {
                "label": "Energy Transition",
                "icon": "⚡",
                "options": {
                    "green_tariff": {
                        "title": "Green Energy Tariff",
                        "description": "Switch all facilities to certified green energy tariffs.",
                        "cost": -1_500_000,
                        "impacts": {"carbon_intensity_delta": -6, "reputation": +2},
                        "flags_set": ["green_tariff"],
                    },
                    "efficiency_upgrades": {
                        "title": "Energy Efficiency Upgrades",
                        "description": "Retrofit buildings with smart HVAC and LED systems.",
                        "cost": -2_500_000,
                        "impacts": {"carbon_intensity_delta": -4, "reputation": +3},
                        "flags_set": ["efficiency_upgrades"],
                    },
                    "baseline": {
                        "title": "Maintain Baseline",
                        "description": "No energy changes this round.",
                        "cost": 0,
                        "impacts": {},
                        "flags_set": [],
                    },
                },
            },
            "operations": {
                "label": "Governance & Compliance",
                "icon": "🏛️",
                "options": {
                    "materiality_board": {
                        "title": "Materiality Advisory Board",
                        "description": "Establish a dedicated materiality oversight committee.",
                        "cost": -2_000_000,
                        "impacts": {"governance_risk_delta": -8, "reputation": +5},
                        "flags_set": ["materiality_aligned"],
                    },
                    "compliance_minimum": {
                        "title": "Minimum Compliance",
                        "description": "Meet regulatory minimums only.",
                        "cost": -500_000,
                        "impacts": {"governance_risk_delta": -2, "reputation": +1},
                        "flags_set": ["materiality_exceptions"],
                    },
                    "ignore_framework": {
                        "title": "Ignore Materiality",
                        "description": "Business as usual. No materiality integration.",
                        "cost": 0,
                        "impacts": {"governance_risk_delta": +10, "reputation": -5},
                        "flags_set": ["materiality_ignored"],
                    },
                },
            },
            "supply_chain": {
                "label": "Supply Chain Transparency",
                "icon": "🔗",
                "options": {
                    "blockchain_trace": {
                        "title": "Blockchain Traceability",
                        "description": "Implement supply chain blockchain for full transparency.",
                        "cost": -3_500_000,
                        "impacts": {"social_license_delta": +5, "reputation": +4},
                        "flags_set": ["blockchain_trace"],
                    },
                    "annual_report": {
                        "title": "Annual ESG Report",
                        "description": "Publish a comprehensive supply chain ESG report.",
                        "cost": -800_000,
                        "impacts": {"reputation": +2},
                        "flags_set": ["esg_report"],
                    },
                    "no_transparency": {
                        "title": "No Additional Transparency",
                        "description": "Maintain current disclosure levels.",
                        "cost": 0,
                        "impacts": {"reputation": -1},
                        "flags_set": [],
                    },
                },
            },
            "offsetting": {
                "label": "Impact Mitigation",
                "icon": "🌱",
                "options": {
                    "community_fund": {
                        "title": "Community Impact Fund",
                        "description": "Establish a community investment fund in operational regions.",
                        "cost": -3_000_000,
                        "impacts": {"social_license_delta": +8, "reputation": +4},
                        "flags_set": ["community_fund_r2"],
                    },
                    "employee_program": {
                        "title": "Employee Wellbeing Program",
                        "description": "Launch comprehensive employee health and development programs.",
                        "cost": -1_500_000,
                        "impacts": {"social_license_delta": +3, "reputation": +2},
                        "flags_set": ["employee_wellbeing"],
                    },
                    "no_mitigation": {
                        "title": "No Mitigation",
                        "description": "Defer impact mitigation investments.",
                        "cost": 0,
                        "impacts": {"social_license_delta": -2},
                        "flags_set": [],
                    },
                },
            },
        },
    },

    # ── Round 3: Scope 3 ───────────────────────────────────────
    3: {
        "title": "Scope 3 Decarbonisation",
        "description": "Address Scope 3 supply chain emissions across all areas.",
        "areas": {
            "energy": {
                "label": "Energy Decarbonisation",
                "icon": "⚡",
                "options": {
                    "electrification": {
                        "title": "Fleet Electrification",
                        "description": "Convert all logistics to electric vehicles.",
                        "cost": -5_000_000,
                        "impacts": {"carbon_intensity_delta": -15, "reputation": +4},
                        "flags_set": ["fleet_electrified"],
                    },
                    "hybrid_transition": {
                        "title": "Hybrid Transition",
                        "description": "Gradual shift to hybrid fleet over 3 rounds.",
                        "cost": -2_000_000,
                        "impacts": {"carbon_intensity_delta": -6, "reputation": +2},
                        "flags_set": ["hybrid_fleet"],
                    },
                    "status_quo": {
                        "title": "Keep Diesel Fleet",
                        "description": "Maintain existing fossil fuel logistics.",
                        "cost": 0,
                        "impacts": {"carbon_intensity_delta": +3, "reputation": -2},
                        "flags_set": ["carbon_deferred"],
                    },
                },
            },
            "operations": {
                "label": "Process Redesign",
                "icon": "🏭",
                "options": {
                    "closed_loop": {
                        "title": "Closed-Loop Manufacturing",
                        "description": "Redesign processes for zero-waste production.",
                        "cost": -4_000_000,
                        "impacts": {"natural_capital_debt_delta": -8, "reputation": +5},
                        "flags_set": ["closed_loop"],
                    },
                    "waste_reduction": {
                        "title": "Waste Reduction Program",
                        "description": "Implement 50% waste reduction targets.",
                        "cost": -1_500_000,
                        "impacts": {"natural_capital_debt_delta": -3, "reputation": +2},
                        "flags_set": ["waste_reduction"],
                    },
                    "no_change": {
                        "title": "No Process Change",
                        "description": "Maintain current manufacturing processes.",
                        "cost": 0,
                        "impacts": {"natural_capital_debt_delta": +5},
                        "flags_set": [],
                    },
                },
            },
            "supply_chain": {
                "label": "Supplier Decarbonisation",
                "icon": "🔗",
                "options": {
                    "rapid_switch": {
                        "title": "Rapid Supplier Switch",
                        "description": "Immediately switch to low-carbon suppliers.",
                        "cost": -4_000_000,
                        "impacts": {"carbon_intensity_delta": -12, "governance_risk_delta": +10},
                        "flags_set": ["supply_chain_disruption_risk"],
                    },
                    "green_bond": {
                        "title": "Green Bond Supplier Fund",
                        "description": "Issue green bonds to fund supplier transition.",
                        "cost": -2_000_000,
                        "impacts": {"natural_capital_debt_delta": -10, "carbon_intensity_delta": -6},
                        "flags_set": ["green_bond_active"],
                    },
                    "offset_defer": {
                        "title": "Offset & Defer",
                        "description": "Buy offsets and wait for regulatory clarity.",
                        "cost": -1_000_000,
                        "impacts": {"natural_capital_debt_delta": +5, "reputation": -3},
                        "flags_set": ["carbon_deferred"],
                    },
                },
            },
            "offsetting": {
                "label": "Carbon Neutrality",
                "icon": "🌱",
                "options": {
                    "science_based": {
                        "title": "Science-Based Targets",
                        "description": "Commit to SBTi-validated net-zero pathway.",
                        "cost": -3_000_000,
                        "impacts": {"carbon_intensity_delta": -8, "reputation": +6},
                        "flags_set": ["sbti_committed"],
                    },
                    "voluntary_offsets": {
                        "title": "Voluntary Offset Purchase",
                        "description": "Purchase voluntary carbon offsets from verified projects.",
                        "cost": -1_500_000,
                        "impacts": {"natural_capital_debt_delta": -4, "reputation": +2},
                        "flags_set": ["voluntary_offsets"],
                    },
                    "greenwash_risk": {
                        "title": "Marketing-Only Pledge",
                        "description": "Issue a net-zero pledge without binding commitments.",
                        "cost": -200_000,
                        "impacts": {"reputation": -3, "governance_risk_delta": +5},
                        "flags_set": ["greenwash_risk"],
                    },
                },
            },
        },
    },

    # ── Round 4: Contagion ──────────────────────────────────────
    4: {
        "title": "Reputation Crisis Response",
        "description": "A supply chain scandal has gone viral. Manage damage across all fronts.",
        "areas": {
            "energy": {
                "label": "Energy Crisis Response",
                "icon": "⚡",
                "options": {
                    "green_pivot": {
                        "title": "Green Energy Pivot",
                        "description": "Accelerate renewable transition to rebuild trust.",
                        "cost": -3_000_000,
                        "impacts": {"carbon_intensity_delta": -10, "reputation": +5},
                        "flags_set": ["green_pivot"],
                    },
                    "maintain": {
                        "title": "Maintain Course",
                        "description": "Keep existing energy plans unchanged.",
                        "cost": 0,
                        "impacts": {},
                        "flags_set": [],
                    },
                    "cost_cutting": {
                        "title": "Cut Energy Spending",
                        "description": "Reduce energy budgets to protect cash during crisis.",
                        "cost": +1_500_000,
                        "impacts": {"carbon_intensity_delta": +5, "reputation": -3},
                        "flags_set": ["energy_cut"],
                    },
                },
            },
            "operations": {
                "label": "Operational Response",
                "icon": "🏭",
                "options": {
                    "full_transparency": {
                        "title": "Full Factory Transparency",
                        "description": "Open factories to independent auditors and media.",
                        "cost": -2_000_000,
                        "impacts": {"reputation": +8, "social_license_delta": +5},
                        "flags_set": ["remediation_active"],
                    },
                    "pr_containment": {
                        "title": "PR Crisis Management",
                        "description": "Hire a crisis PR firm to control the narrative.",
                        "cost": -1_500_000,
                        "impacts": {"reputation": +2, "social_license_delta": -2},
                        "flags_set": ["pr_containment"],
                    },
                    "deny": {
                        "title": "Deny Allegations",
                        "description": "Issue a formal denial. Cheapest but highest risk.",
                        "cost": 0,
                        "impacts": {"reputation": -15, "social_license_delta": -10},
                        "flags_set": ["deny_and_deflect"],
                    },
                },
            },
            "supply_chain": {
                "label": "Supplier Remediation",
                "icon": "🔗",
                "options": {
                    "remediate_all": {
                        "title": "Full Supply Chain Remediation",
                        "description": "Audit and remediate all supplier labour practices.",
                        "cost": -5_000_000,
                        "impacts": {"social_license_delta": +10, "reputation": +6},
                        "flags_set": ["supplier_remediation"],
                    },
                    "targeted_fix": {
                        "title": "Targeted Fix",
                        "description": "Address only the exposed supplier violations.",
                        "cost": -1_500_000,
                        "impacts": {"social_license_delta": +3, "reputation": +2},
                        "flags_set": ["targeted_fix"],
                    },
                    "ignore": {
                        "title": "Ignore Supply Chain",
                        "description": "Focus on PR instead of root cause.",
                        "cost": 0,
                        "impacts": {"social_license_delta": -5, "governance_risk_delta": +8},
                        "flags_set": ["supply_ignored"],
                    },
                },
            },
            "offsetting": {
                "label": "Stakeholder Repair",
                "icon": "🌱",
                "options": {
                    "stakeholder_fund": {
                        "title": "Stakeholder Compensation Fund",
                        "description": "Establish a fund to compensate affected communities.",
                        "cost": -4_000_000,
                        "impacts": {"social_license_delta": +8, "reputation": +5},
                        "flags_set": ["stakeholder_compensated"],
                    },
                    "ngo_partnership": {
                        "title": "NGO Partnership",
                        "description": "Partner with NGOs for independent monitoring.",
                        "cost": -1_000_000,
                        "impacts": {"social_license_delta": +3, "reputation": +3},
                        "flags_set": ["ngo_partner"],
                    },
                    "no_action": {
                        "title": "No Stakeholder Action",
                        "description": "No additional stakeholder engagement.",
                        "cost": 0,
                        "impacts": {"reputation": -5},
                        "flags_set": [],
                    },
                },
            },
        },
    },

    # ── Round 5: Climate ────────────────────────────────────────
    5: {
        "title": "Climate Resilience",
        "description": "A severe weather event threatens operations. Build resilience.",
        "areas": {
            "energy": {
                "label": "Energy Resilience",
                "icon": "⚡",
                "options": {
                    "microgrids": {
                        "title": "Distributed Microgrids",
                        "description": "Install backup microgrids at all critical facilities.",
                        "cost": -4_000_000,
                        "impacts": {"reputation": +3},
                        "flags_set": ["microgrids"],
                    },
                    "generator_backup": {
                        "title": "Diesel Generator Backup",
                        "description": "Install conventional backup generators.",
                        "cost": -1_000_000,
                        "impacts": {"carbon_intensity_delta": +3},
                        "flags_set": ["diesel_backup"],
                    },
                    "no_backup": {
                        "title": "No Energy Backup",
                        "description": "Accept energy disruption risk.",
                        "cost": 0,
                        "impacts": {},
                        "flags_set": [],
                    },
                },
            },
            "operations": {
                "label": "Physical Defence",
                "icon": "🏭",
                "options": {
                    "hard_engineering": {
                        "title": "Hard Engineering Defence",
                        "description": "Build flood walls and reinforced infrastructure.",
                        "cost": -8_000_000,
                        "impacts": {"natural_capital_debt_delta": +10},
                        "flags_set": ["hard_engineering"],
                    },
                    "nature_based": {
                        "title": "Nature-Based Solutions",
                        "description": "Mangrove restoration and natural buffers.",
                        "cost": -5_000_000,
                        "impacts": {"natural_capital_debt_delta": -8, "reputation": +4},
                        "flags_set": ["nature_based_resilience"],
                    },
                    "insurance_only": {
                        "title": "Insurance Only",
                        "description": "Buy comprehensive insurance. No physical defence.",
                        "cost": -2_000_000,
                        "impacts": {},
                        "flags_set": ["insurance_only"],
                    },
                },
            },
            "supply_chain": {
                "label": "Supply Chain Resilience",
                "icon": "🔗",
                "options": {
                    "diversify": {
                        "title": "Geographic Diversification",
                        "description": "Diversify supply chain across multiple regions.",
                        "cost": -3_000_000,
                        "impacts": {"governance_risk_delta": -5, "reputation": +3},
                        "flags_set": ["supply_diversified"],
                    },
                    "nearshore": {
                        "title": "Nearshoring",
                        "description": "Move critical suppliers closer to operations.",
                        "cost": -2_000_000,
                        "impacts": {"carbon_intensity_delta": -3, "reputation": +2},
                        "flags_set": ["nearshored"],
                    },
                    "accept_risk": {
                        "title": "Accept Supply Risk",
                        "description": "Maintain existing supply chain configuration.",
                        "cost": 0,
                        "impacts": {"governance_risk_delta": +5},
                        "flags_set": [],
                    },
                },
            },
            "offsetting": {
                "label": "Adaptation Finance",
                "icon": "🌱",
                "options": {
                    "adaptation_fund": {
                        "title": "Climate Adaptation Fund",
                        "description": "Create a dedicated fund for community adaptation.",
                        "cost": -3_000_000,
                        "impacts": {"social_license_delta": +6, "reputation": +4},
                        "flags_set": ["adaptation_fund"],
                    },
                    "parametric_insurance": {
                        "title": "Parametric Insurance",
                        "description": "Purchase weather-indexed parametric insurance.",
                        "cost": -1_500_000,
                        "impacts": {"reputation": +1},
                        "flags_set": ["parametric_insurance"],
                    },
                    "no_adaptation": {
                        "title": "No Adaptation Spending",
                        "description": "No additional climate adaptation investment.",
                        "cost": 0,
                        "impacts": {"reputation": -2},
                        "flags_set": [],
                    },
                },
            },
        },
    },

    # ── Rounds 6-10: Follow same pattern ────────────────────────
    6: {
        "title": "AI Ethics & Technology",
        "description": "Navigate the AI bias scandal with strategic technology decisions.",
        "areas": {
            "energy": {
                "label": "Tech Infrastructure",
                "icon": "⚡",
                "options": {
                    "green_data_centers": {
                        "title": "Green Data Centers",
                        "description": "Migrate to 100% renewable-powered data centers.",
                        "cost": -4_000_000,
                        "impacts": {"carbon_intensity_delta": -10, "reputation": +4},
                        "flags_set": ["green_dc"],
                    },
                    "efficiency_optimize": {
                        "title": "Optimize Existing Infra",
                        "description": "Improve PUE of current data centers.",
                        "cost": -1_500_000,
                        "impacts": {"carbon_intensity_delta": -4, "reputation": +1},
                        "flags_set": ["dc_optimized"],
                    },
                    "no_change": {
                        "title": "No Infrastructure Change",
                        "description": "Maintain current technology infrastructure.",
                        "cost": 0,
                        "impacts": {},
                        "flags_set": [],
                    },
                },
            },
            "operations": {
                "label": "AI Governance",
                "icon": "🏭",
                "options": {
                    "ethical_overhaul": {
                        "title": "Ethical AI Overhaul",
                        "description": "Full AI ethics board, bias audits, model retraining.",
                        "cost": -8_000_000,
                        "impacts": {"social_license_delta": +15, "reputation": +5},
                        "flags_set": ["ethical_ai_overhaul"],
                    },
                    "quiet_patch": {
                        "title": "Quiet Patch",
                        "description": "Silently fix the algorithm. Risk of leak.",
                        "cost": -1_000_000,
                        "impacts": {"reputation": -5, "governance_risk_delta": +10},
                        "flags_set": ["quiet_patch"],
                    },
                    "monetise": {
                        "title": "Monetise the Algorithm",
                        "description": "Pivot AI tool into commercial product.",
                        "cost": 0,
                        "impacts": {"reputation": -20},
                        "flags_set": ["ai_monetised"],
                    },
                },
            },
            "supply_chain": {
                "label": "Digital Supply Chain",
                "icon": "🔗",
                "options": {
                    "ai_supply_optimize": {
                        "title": "AI Supply Optimization",
                        "description": "Deploy ethical AI for supply chain optimization.",
                        "cost": -3_000_000,
                        "impacts": {"reputation": +3, "governance_risk_delta": -3},
                        "flags_set": ["ai_supply"],
                    },
                    "manual_oversight": {
                        "title": "Manual Oversight",
                        "description": "Increase human oversight of supply decisions.",
                        "cost": -1_000_000,
                        "impacts": {"social_license_delta": +3},
                        "flags_set": ["manual_oversight"],
                    },
                    "automate_fully": {
                        "title": "Full Automation",
                        "description": "Aggressively automate without governance checks.",
                        "cost": -500_000,
                        "impacts": {"governance_risk_delta": +8, "reputation": -3},
                        "flags_set": ["reckless_automation"],
                    },
                },
            },
            "offsetting": {
                "label": "Social Investment",
                "icon": "🌱",
                "options": {
                    "digital_inclusion": {
                        "title": "Digital Inclusion Fund",
                        "description": "Fund digital literacy programs in underserved communities.",
                        "cost": -2_500_000,
                        "impacts": {"social_license_delta": +8, "reputation": +4},
                        "flags_set": ["digital_inclusion"],
                    },
                    "scholarship_program": {
                        "title": "Tech Scholarship Program",
                        "description": "Fund scholarships for underrepresented groups in tech.",
                        "cost": -1_000_000,
                        "impacts": {"social_license_delta": +4, "reputation": +2},
                        "flags_set": ["tech_scholarships"],
                    },
                    "no_social_invest": {
                        "title": "No Social Investment",
                        "description": "No additional social investment this round.",
                        "cost": 0,
                        "impacts": {"social_license_delta": -2},
                        "flags_set": [],
                    },
                },
            },
        },
    },

    7: {
        "title": "Circular Economy Transition",
        "description": "New regulations demand circular economy compliance. Invest strategically.",
        "areas": {
            "energy": {
                "label": "Circular Energy",
                "icon": "⚡",
                "options": {
                    "waste_to_energy": {
                        "title": "Waste-to-Energy Plant",
                        "description": "Convert manufacturing waste into energy.",
                        "cost": -6_000_000,
                        "impacts": {"carbon_intensity_delta": -8, "natural_capital_debt_delta": -4},
                        "flags_set": ["waste_to_energy", "synergy_unlock"],
                    },
                    "heat_recovery": {
                        "title": "Industrial Heat Recovery",
                        "description": "Capture and reuse waste heat from manufacturing.",
                        "cost": -2_500_000,
                        "impacts": {"carbon_intensity_delta": -4},
                        "flags_set": ["heat_recovery"],
                    },
                    "no_change": {
                        "title": "No Circular Energy",
                        "description": "Standard energy operations.",
                        "cost": 0,
                        "impacts": {},
                        "flags_set": [],
                    },
                },
            },
            "operations": {
                "label": "Product Redesign",
                "icon": "🏭",
                "options": {
                    "full_circular": {
                        "title": "Full Circular Redesign",
                        "description": "Redesign all products for disassembly and reuse.",
                        "cost": -10_000_000,
                        "impacts": {"natural_capital_debt_delta": -12, "reputation": +8},
                        "flags_set": ["circular_redesign"],
                    },
                    "epr": {
                        "title": "Extended Producer Responsibility",
                        "description": "Fund take-back programs and recycling partnerships.",
                        "cost": -5_000_000,
                        "impacts": {"natural_capital_debt_delta": -6, "reputation": +4},
                        "flags_set": ["epr_program"],
                    },
                    "minimum_compliance": {
                        "title": "Minimum EU Compliance",
                        "description": "Do the bare minimum to meet regulations.",
                        "cost": -1_000_000,
                        "impacts": {"reputation": -2, "governance_risk_delta": +5},
                        "flags_set": [],
                    },
                },
            },
            "supply_chain": {
                "label": "Circular Supply Chain",
                "icon": "🔗",
                "options": {
                    "reverse_logistics": {
                        "title": "Reverse Logistics Network",
                        "description": "Build a product return and refurbishment network.",
                        "cost": -4_000_000,
                        "impacts": {"natural_capital_debt_delta": -5, "reputation": +3},
                        "flags_set": ["reverse_logistics"],
                    },
                    "material_passport": {
                        "title": "Material Passports",
                        "description": "Implement digital material tracking across supply chain.",
                        "cost": -2_000_000,
                        "impacts": {"reputation": +2},
                        "flags_set": ["material_passport"],
                    },
                    "linear_model": {
                        "title": "Keep Linear Model",
                        "description": "Maintain the traditional take-make-dispose model.",
                        "cost": 0,
                        "impacts": {"natural_capital_debt_delta": +5, "reputation": -3},
                        "flags_set": [],
                    },
                },
            },
            "offsetting": {
                "label": "Nature Restoration",
                "icon": "🌱",
                "options": {
                    "biodiversity_fund": {
                        "title": "Biodiversity Restoration",
                        "description": "Fund ecosystem restoration in operational areas.",
                        "cost": -3_000_000,
                        "impacts": {"natural_capital_debt_delta": -8, "reputation": +5},
                        "flags_set": ["biodiversity_fund"],
                    },
                    "regenerative_ag": {
                        "title": "Regenerative Agriculture",
                        "description": "Transition supply chains to regenerative agriculture.",
                        "cost": -2_000_000,
                        "impacts": {"natural_capital_debt_delta": -4, "reputation": +3},
                        "flags_set": ["regen_agriculture"],
                    },
                    "no_nature": {
                        "title": "No Nature Investment",
                        "description": "No nature restoration spending this round.",
                        "cost": 0,
                        "impacts": {},
                        "flags_set": [],
                    },
                },
            },
        },
    },

    8: {
        "title": "Water Scarcity Response",
        "description": "Critical water shortage demands urgent strategic action.",
        "areas": {
            "energy": {
                "label": "Water-Energy Nexus",
                "icon": "⚡",
                "options": {
                    "dry_cooling": {
                        "title": "Dry Cooling Systems",
                        "description": "Convert manufacturing to water-free cooling.",
                        "cost": -5_000_000,
                        "impacts": {"water_dependency_delta": -15},
                        "flags_set": ["dry_cooling"],
                    },
                    "water_recycling": {
                        "title": "Water Recycling",
                        "description": "Install closed-loop water recycling systems.",
                        "cost": -3_000_000,
                        "impacts": {"water_dependency_delta": -8},
                        "flags_set": ["water_recycling"],
                    },
                    "no_water_action": {
                        "title": "No Water-Energy Action",
                        "description": "Maintain current water usage patterns.",
                        "cost": 0,
                        "impacts": {"water_dependency_delta": +5},
                        "flags_set": [],
                    },
                },
            },
            "operations": {
                "label": "Water Allocation",
                "icon": "🏭",
                "options": {
                    "equitable": {
                        "title": "Equitable Water Saving",
                        "description": "Equal water-saving upgrades across all BUs.",
                        "cost": -12_000_000,
                        "impacts": {"water_dependency_delta": -20, "social_license_delta": +5},
                        "flags_set": ["water_efficiency_all"],
                    },
                    "prioritize_electronics": {
                        "title": "Prioritise Electronics",
                        "description": "Divert water to highest-margin Electronics BU.",
                        "cost": -4_000_000,
                        "impacts": {},
                        "flags_set": ["electronics_water_priority"],
                    },
                    "desalination": {
                        "title": "Desalination Plant",
                        "description": "Build a desalination mega-project.",
                        "cost": -30_000_000,
                        "impacts": {"natural_capital_debt_delta": -30, "water_dependency_delta": -40},
                        "flags_set": ["desalination_built"],
                    },
                },
            },
            "supply_chain": {
                "label": "Supply Chain Water",
                "icon": "🔗",
                "options": {
                    "water_footprint_audit": {
                        "title": "Supply Chain Water Audit",
                        "description": "Map and reduce water footprint across suppliers.",
                        "cost": -2_000_000,
                        "impacts": {"water_dependency_delta": -5, "reputation": +2},
                        "flags_set": ["supply_water_audit"],
                    },
                    "water_efficient_suppliers": {
                        "title": "Switch to Water-Efficient Suppliers",
                        "description": "Replace water-intensive suppliers.",
                        "cost": -3_000_000,
                        "impacts": {"water_dependency_delta": -10, "governance_risk_delta": +3},
                        "flags_set": ["water_efficient_supply"],
                    },
                    "no_supply_change": {
                        "title": "No Supply Chain Change",
                        "description": "Maintain existing supplier base.",
                        "cost": 0,
                        "impacts": {},
                        "flags_set": [],
                    },
                },
            },
            "offsetting": {
                "label": "Water Stewardship",
                "icon": "🌱",
                "options": {
                    "watershed_restore": {
                        "title": "Watershed Restoration",
                        "description": "Invest in restoring the local watershed ecosystem.",
                        "cost": -4_000_000,
                        "impacts": {"natural_capital_debt_delta": -10, "social_license_delta": +5, "reputation": +4},
                        "flags_set": ["watershed_restored"],
                    },
                    "community_water": {
                        "title": "Community Water Access",
                        "description": "Fund clean water access for communities near operations.",
                        "cost": -2_000_000,
                        "impacts": {"social_license_delta": +8, "reputation": +3},
                        "flags_set": ["community_water"],
                    },
                    "no_stewardship": {
                        "title": "No Water Stewardship",
                        "description": "No additional water stewardship investment.",
                        "cost": 0,
                        "impacts": {"social_license_delta": -3},
                        "flags_set": [],
                    },
                },
            },
        },
    },

    9: {
        "title": "Just Transition Strategy",
        "description": "Factory closures risk 2,000 jobs. Navigate the workforce transition.",
        "areas": {
            "energy": {
                "label": "Green Jobs",
                "icon": "⚡",
                "options": {
                    "green_reskilling": {
                        "title": "Green Skills Academy",
                        "description": "Fund a training academy for green energy jobs.",
                        "cost": -5_000_000,
                        "impacts": {"social_license_delta": +10, "reputation": +5},
                        "flags_set": ["green_reskilling"],
                    },
                    "partial_retraining": {
                        "title": "Partial Retraining",
                        "description": "Offer retraining to 50% of affected workers.",
                        "cost": -2_000_000,
                        "impacts": {"social_license_delta": +4, "reputation": +2},
                        "flags_set": ["partial_retraining"],
                    },
                    "no_retraining": {
                        "title": "No Retraining",
                        "description": "Provide severance only, no retraining.",
                        "cost": -500_000,
                        "impacts": {"social_license_delta": -8, "reputation": -5},
                        "flags_set": [],
                    },
                },
            },
            "operations": {
                "label": "Factory Strategy",
                "icon": "🏭",
                "options": {
                    "managed_transition": {
                        "title": "2-Year Managed Transition",
                        "description": "Gradual phase-out with retraining and severance.",
                        "cost": -12_000_000,
                        "impacts": {"social_license_delta": +10, "reputation": +8},
                        "flags_set": ["managed_transition"],
                    },
                    "immediate_closure": {
                        "title": "Immediate Closure",
                        "description": "Close factories now for maximum cost savings.",
                        "cost": +5_000_000,
                        "impacts": {"social_license_delta": -20, "reputation": -15},
                        "flags_set": ["immediate_closure"],
                    },
                    "automation_pivot": {
                        "title": "Automation Pivot",
                        "description": "Convert closures into automated smart factories.",
                        "cost": -8_000_000,
                        "impacts": {"social_license_delta": -5, "reputation": +2},
                        "flags_set": ["automation_pivot"],
                    },
                },
            },
            "supply_chain": {
                "label": "Local Sourcing",
                "icon": "🔗",
                "options": {
                    "local_ecosystem": {
                        "title": "Local Supplier Ecosystem",
                        "description": "Build a network of local SME suppliers.",
                        "cost": -3_000_000,
                        "impacts": {"social_license_delta": +6, "reputation": +3},
                        "flags_set": ["local_ecosystem"],
                    },
                    "cooperative_model": {
                        "title": "Worker Cooperatives",
                        "description": "Convert some suppliers into worker-owned cooperatives.",
                        "cost": -2_000_000,
                        "impacts": {"social_license_delta": +8, "reputation": +4},
                        "flags_set": ["cooperatives"],
                    },
                    "offshore": {
                        "title": "Offshore Remaining",
                        "description": "Move remaining supply chain offshore for cost savings.",
                        "cost": +2_000_000,
                        "impacts": {"social_license_delta": -10, "reputation": -5},
                        "flags_set": ["offshored"],
                    },
                },
            },
            "offsetting": {
                "label": "Community Investment",
                "icon": "🌱",
                "options": {
                    "community_fund": {
                        "title": "$20M Community Fund",
                        "description": "Create a community economic development fund.",
                        "cost": -20_000_000,
                        "impacts": {"social_license_delta": +18, "reputation": +12, "governance_risk_delta": -5},
                        "flags_set": ["community_fund"],
                    },
                    "transition_bonds": {
                        "title": "Just Transition Bonds",
                        "description": "Issue bonds to finance regional economic diversification.",
                        "cost": -5_000_000,
                        "impacts": {"social_license_delta": +6, "reputation": +4},
                        "flags_set": ["transition_bonds"],
                    },
                    "no_community": {
                        "title": "No Community Investment",
                        "description": "No additional community support.",
                        "cost": 0,
                        "impacts": {"social_license_delta": -5, "reputation": -3},
                        "flags_set": [],
                    },
                },
            },
        },
    },

    10: {
        "title": "2050 Corporate Destiny",
        "description": "Activist investors demand restructuring. Choose your final trajectory.",
        "areas": {
            "energy": {
                "label": "Energy Legacy",
                "icon": "⚡",
                "options": {
                    "net_zero_certified": {
                        "title": "Net-Zero Certification",
                        "description": "Achieve verified net-zero energy operations.",
                        "cost": -8_000_000,
                        "impacts": {"carbon_intensity_delta": -20, "reputation": +8},
                        "flags_set": ["net_zero_energy"],
                    },
                    "low_carbon": {
                        "title": "Low-Carbon Pathway",
                        "description": "Commit to 80% carbon reduction by 2050.",
                        "cost": -3_000_000,
                        "impacts": {"carbon_intensity_delta": -10, "reputation": +3},
                        "flags_set": ["low_carbon_path"],
                    },
                    "fossil_dependent": {
                        "title": "Remain Fossil Dependent",
                        "description": "Maintain fossil fuel operations and accept carbon tax.",
                        "cost": 0,
                        "impacts": {"carbon_intensity_delta": +5, "reputation": -8},
                        "flags_set": ["fossil_dependent"],
                    },
                },
            },
            "operations": {
                "label": "Corporate Structure",
                "icon": "🏭",
                "options": {
                    "resist_integrate": {
                        "title": "Resist & Integrate",
                        "description": "Keep all BUs integrated, leverage synergy.",
                        "cost": -5_000_000,
                        "impacts": {},
                        "flags_set": ["resist_integrate"],
                    },
                    "spinoff": {
                        "title": "Strategic Spin-Off",
                        "description": "Spin off weakest BU as separate entity.",
                        "cost": 0,
                        "impacts": {},
                        "flags_set": ["spinoff"],
                    },
                    "divest": {
                        "title": "Full Divestiture",
                        "description": "Divest non-core assets for maximum cash.",
                        "cost": +25_000_000,
                        "impacts": {"reputation": -10},
                        "flags_set": ["divest"],
                    },
                },
            },
            "supply_chain": {
                "label": "Supply Chain Future",
                "icon": "🔗",
                "options": {
                    "regenerative_supply": {
                        "title": "Regenerative Supply Chain",
                        "description": "Transform to a fully regenerative supply model.",
                        "cost": -6_000_000,
                        "impacts": {"natural_capital_debt_delta": -15, "reputation": +6},
                        "flags_set": ["regenerative_supply"],
                    },
                    "resilient_network": {
                        "title": "Resilient Network",
                        "description": "Build a climate-resilient diversified supply network.",
                        "cost": -3_000_000,
                        "impacts": {"governance_risk_delta": -5, "reputation": +3},
                        "flags_set": ["resilient_network"],
                    },
                    "cost_optimize": {
                        "title": "Cost Optimized",
                        "description": "Pure cost optimization with accepted ESG risk.",
                        "cost": +2_000_000,
                        "impacts": {"governance_risk_delta": +8, "reputation": -4},
                        "flags_set": ["cost_optimized"],
                    },
                },
            },
            "offsetting": {
                "label": "Legacy Impact",
                "icon": "🌱",
                "options": {
                    "endowment": {
                        "title": "Perpetual Impact Endowment",
                        "description": "Establish a $15M perpetual fund for sustainability.",
                        "cost": -15_000_000,
                        "impacts": {"social_license_delta": +15, "natural_capital_debt_delta": -10, "reputation": +8},
                        "flags_set": ["endowment_created"],
                    },
                    "stakeholder_covenant": {
                        "title": "Stakeholder Covenant",
                        "description": "Sign a binding stakeholder governance covenant.",
                        "cost": -3_000_000,
                        "impacts": {"social_license_delta": +8, "governance_risk_delta": -8, "reputation": +5},
                        "flags_set": ["stakeholder_covenant"],
                    },
                    "shareholder_return": {
                        "title": "Shareholder Return Focus",
                        "description": "Maximize dividends and buybacks. Pure shareholder value.",
                        "cost": +10_000_000,
                        "impacts": {"social_license_delta": -10, "reputation": -5},
                        "flags_set": ["shareholder_only"],
                    },
                },
            },
        },
    },
}


# ═════════════════════════════════════════════════════════════════
#  AGGREGATION FUNCTIONS
# ═════════════════════════════════════════════════════════════════

import json
import os

def _deep_merge(dict1: dict, dict2: dict) -> dict:
    for k, v in dict2.items():
        if isinstance(v, dict) and k in dict1 and isinstance(dict1[k], dict):
            _deep_merge(dict1[k], v)
        else:
            dict1[k] = copy.deepcopy(v)
    return dict1

def _get_merged_pillar_options() -> dict[int, dict[str, Any]]:
    base_configs = copy.deepcopy(PILLAR_OPTIONS)
    if OVERRIDES_FILE.exists():
        try:
            with open(OVERRIDES_FILE, "r") as f:
                data = json.load(f)
            multi_toggles_overrides = data.get("multi_toggles", {})
            for round_num_str, cfg_override in multi_toggles_overrides.items():
                round_num = int(round_num_str)
                if round_num in base_configs:
                    _deep_merge(base_configs[round_num], cfg_override)
        except Exception as e:
            print(f"Error loading decision overrides: {e}")
    return base_configs


_detailed_cache = None

def _get_detailed_descriptions():
    global _detailed_cache
    if _detailed_cache is None:
        try:
            path = os.path.join(os.path.dirname(__file__), "detailed_descriptions.json")
            with open(path, "r", encoding="utf-8") as f:
                _detailed_cache = json.load(f)
        except Exception as e:
            print("Warning: Could not load detailed_descriptions.json:", e)
            _detailed_cache = {}
    return _detailed_cache


def get_pillar_config(round_number: int) -> dict | None:
    """Return a deep copy of the pillar config for a round."""
    cfg = PILLAR_OPTIONS.get(round_number)
    if not cfg:
        return None
        
    cfg_copy = copy.deepcopy(cfg)
    try:
        detailed = _get_detailed_descriptions().get("pillars", {}).get(str(round_number), {})
        for area_key, area_data in cfg_copy.get("areas", {}).items():
            area_details = detailed.get(area_key, {})
            for opt_key, opt_data in area_data.get("options", {}).items():
                if opt_key in area_details:
                    opt_data["detailed_description"] = area_details[opt_key]
    except Exception as e:
        print("Failed to inject pillar detailed descriptions:", e)
        
    return cfg_copy


def aggregate_pillar_decisions(
    round_number: int,
    pillar_choices: dict[str, str],
) -> dict[str, Any]:
    """
    Given {area: action_key} selections, aggregate into combined impacts.

    Returns:
        {
            "total_cost": float,
            "impacts": {key: delta},
            "flags_set": [str],
            "per_area": {area: {action_key, title, cost, impacts}},
        }
    """
    cfg = PILLAR_OPTIONS.get(round_number)
    if not cfg:
        return {"total_cost": 0, "impacts": {}, "flags_set": [], "per_area": {}}

    areas = cfg.get("areas", {})
    total_cost = 0
    combined_impacts: dict[str, float] = {}
    all_flags: list[str] = []
    per_area: dict[str, dict] = {}

    for area_key, action_key in pillar_choices.items():
        area_cfg = areas.get(area_key)
        if not area_cfg:
            continue

        action = area_cfg["options"].get(action_key)
        if not action:
            continue

        cost = action.get("cost", 0)
        total_cost += cost

        for k, v in action.get("impacts", {}).items():
            combined_impacts[k] = combined_impacts.get(k, 0) + v

        all_flags.extend(action.get("flags_set", []))

        per_area[area_key] = {
            "action_key": action_key,
            "title": action.get("title", action_key),
            "cost": cost,
            "impacts": action.get("impacts", {}),
        }

    return {
        "total_cost": total_cost,
        "impacts": combined_impacts,
        "flags_set": all_flags,
        "per_area": per_area,
    }


def translate_pillars_to_legacy_choice(
    round_number: int,
    pillar_choices: dict[str, str],
) -> str:
    """
    Map a set of pillar selections to the closest legacy A/B/C choice
    for backward compatibility with round_logic._get_primary_choice().

    Heuristic: total cost determines aggressiveness.
      - Aggressive spending → option_a (bold)
      - Moderate spending → option_b (balanced)
      - Low/no spending → option_c (conservative)
    """
    agg = aggregate_pillar_decisions(round_number, pillar_choices)
    total_cost = agg["total_cost"]

    # More negative cost = more aggressive
    if total_cost <= -8_000_000:
        return "option_a"
    elif total_cost <= -3_000_000:
        return "option_b"
    else:
        return "option_c"
