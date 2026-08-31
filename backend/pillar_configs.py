"""Muressons Global Corporation — Strategic Pillars Configuration
Defines the 5-area decision options per round for the "multi_toggles" paradigm.
Each round has options for: Energy, Operations, Supply Chain, Offsetting,
and Human Resources.
"""

from __future__ import annotations
from typing import Any
import copy
import json
import os
from pathlib import Path

from runtime_paths import config_file as _config_file
OVERRIDES_FILE = _config_file("decision_overrides.json")  # 3.1: durable location


# ═════════════════════════════════════════════════════════════════
#  PILLAR OPTIONS PER ROUND
#  Each round maps 5 areas → 3 actions each.
#  Actions have: cost (treasury delta), impacts (capital deltas),
#  flags_set (for round_logic compatibility).
# ═════════════════════════════════════════════════════════════════

PILLAR_OPTIONS = {

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
            "human_resources": {
                "label": "Talent & Culture",
                "icon": "👥",
                "options": {
                    "dei_training": {
                        "title": "DEI & Inclusion Program",
                        "description": "Launch a comprehensive Diversity, Equity & Inclusion training program across all BUs, including executive sponsorship and ERGs.",
                        "cost": -2_000_000,
                        "impacts": {"social_license_delta": +4, "reputation": +3, "burnout_delta": -8},
                        "flags_set": ["dei_program"],
                    },
                    "leadership_dev": {
                        "title": "Leadership Development",
                        "description": "Invest in a leadership pipeline with mentoring, succession planning and executive coaching.",
                        "cost": -1_500_000,
                        "impacts": {"reputation": +2, "governance_risk_delta": -2},
                        "flags_set": ["leadership_pipeline"],
                    },
                    "no_hr_action": {
                        "title": "No HR Investment",
                        "description": "Defer all workforce development spending this round.",
                        "cost": 0,
                        "impacts": {"social_license_delta": -1},
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
                        # F-2: pillar-specific marker. The round tier flag
                        # (materiality_aligned) is owned by _post_r2_materiality.
                        "flags_set": ["materiality_board_established"],
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
                        # F-2: pillar-specific marker (tier flag owned by _post_r2_materiality).
                        "flags_set": ["materiality_framework_ignored"],
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
                        "impacts": {"social_license_delta": +5, "reputation": +4, "burnout_delta": -10},
                        "flags_set": ["blockchain_traceability"],
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
            "human_resources": {
                "label": "Workforce Analytics",
                "icon": "👥",
                "options": {
                    "people_analytics": {
                        "title": "People Analytics Platform",
                        "description": "Deploy AI-driven workforce analytics for attrition prediction, engagement tracking and skills gap analysis.",
                        "cost": -2_500_000,
                        "impacts": {"governance_risk_delta": -4, "reputation": +3},
                        "flags_set": ["people_analytics"],
                    },
                    "engagement_survey": {
                        "title": "Annual Engagement Survey",
                        "description": "Conduct a company-wide engagement survey with action plans for each BU.",
                        "cost": -500_000,
                        "impacts": {"social_license_delta": +2, "reputation": +1},
                        "flags_set": ["engagement_survey"],
                    },
                    "no_hr_action": {
                        "title": "No Workforce Analytics",
                        "description": "No investment in workforce data or analytics.",
                        "cost": 0,
                        "impacts": {},
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
                        "flags_set": ["supply_chain_disruption_risk", "early_decarboniser"],
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
                        "description": "Issue a net-zero pledge without binding commitments. Low cost but activates the Greenwashing Engine if average investment ratio drops below 15%.",
                        "cost": -200_000,
                        "impacts": {"reputation": -3, "governance_risk_delta": +5},
                        "flags_set": ["greenwash_risk"],
                        "warning_badge": "\u26a0\ufe0f GREENWASH RISK: If avg investment ratio < 15%, the Greenwashing Engine deducts \u22128 Social Licence from ALL BUs.",
                    },
                },
            },
            "human_resources": {
                "label": "Green Skills Pipeline",
                "icon": "👥",
                "options": {
                    "green_academy": {
                        "title": "Internal Green Skills Academy",
                        "description": "Build an in-house training academy for Scope 3 carbon accounting, lifecycle assessment and circular design skills.",
                        "cost": -3_000_000,
                        "impacts": {"social_license_delta": +5, "reputation": +4},
                        "flags_set": ["green_skills_academy"],
                    },
                    "safety_compliance": {
                        "title": "Basic OHS Compliance",
                        "description": "Meet minimum occupational health and safety standards. Low cost but no strategic uplift.",
                        "cost": -500_000,
                        "impacts": {"reputation": +1},
                        "flags_set": ["ohs_basic"],
                    },
                    "no_hr_action": {
                        "title": "No Workforce Change",
                        "description": "No workforce development investment. Risk of skills gap widening.",
                        "cost": 0,
                        "impacts": {"social_license_delta": -2},
                        "flags_set": [],
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
            "human_resources": {
                "label": "Crisis Workforce Support",
                "icon": "👥",
                "options": {
                    "crisis_counselling": {
                        "title": "Employee Crisis Support",
                        "description": "Provide mental health support, crisis counselling and transparent internal comms to maintain employee trust during the scandal.",
                        "cost": -1_500_000,
                        "impacts": {"social_license_delta": +4, "reputation": +3},
                        "flags_set": ["crisis_employee_support"],
                    },
                    "overtime_push": {
                        "title": "Overtime & Crisis Push",
                        "description": "Mandate overtime to accelerate crisis response. Short-term gain at the cost of burnout and attrition risk.",
                        "cost": +500_000,
                        "impacts": {"social_license_delta": -4, "reputation": -2, "burnout_delta": +12},
                        "flags_set": ["burnout_risk"],
                    },
                    "no_hr_action": {
                        "title": "No Employee Support",
                        "description": "No additional workforce support. Employee morale is left to fend for itself.",
                        "cost": 0,
                        "impacts": {"social_license_delta": -2, "reputation": -1},
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
                        "impacts": {"natural_capital_debt_delta": +10, "resilience_factor": 0.85},
                        "flags_set": ["hard_engineering"],
                    },
                    "nature_based": {
                        "title": "Nature-Based Solutions",
                        "description": "Mangrove restoration and natural buffers.",
                        "cost": -5_000_000,
                        "impacts": {"natural_capital_debt_delta": -8, "reputation": +4, "resilience_factor": 0.60},
                        "flags_set": ["nature_based_resilience"],
                    },
                    "insurance_only": {
                        "title": "Insurance Only",
                        "description": "Buy comprehensive insurance. No physical defence.",
                        "cost": -2_000_000,
                        "impacts": {"resilience_factor": 0.0},
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
                        "impacts": {"social_license_delta": +6, "reputation": +4, "burnout_delta": -10},
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
            "human_resources": {
                "label": "Worker Safety & Resilience",
                "icon": "👥",
                "options": {
                    "emergency_team": {
                        "title": "Emergency Response Training",
                        "description": "Train dedicated emergency response teams at each facility. Includes evacuation drills, first-aid certification and business continuity roles.",
                        "cost": -2_000_000,
                        "impacts": {"social_license_delta": +5, "reputation": +3, "governance_risk_delta": -3},
                        "flags_set": ["emergency_trained"],
                    },
                    "basic_ppe": {
                        "title": "Basic Safety Gear Upgrade",
                        "description": "Issue standard PPE and establish minimum safety protocols.",
                        "cost": -500_000,
                        "impacts": {"social_license_delta": +1, "reputation": +1},
                        "flags_set": ["basic_ppe"],
                    },
                    "no_hr_action": {
                        "title": "No Workforce Safety Investment",
                        "description": "No additional worker safety spending. Accept existing risk levels.",
                        "cost": 0,
                        "impacts": {"social_license_delta": -3},
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
            "human_resources": {
                "label": "AI Ethics & Workforce",
                "icon": "👥",
                "options": {
                    "responsible_ai_training": {
                        "title": "Responsible AI Training",
                        "description": "Train all employees on responsible AI use, bias detection and ethical data handling. Includes whistleblower protections.",
                        "cost": -2_500_000,
                        "impacts": {"social_license_delta": +5, "reputation": +4, "governance_risk_delta": -4, "burnout_delta": -10},
                        "flags_set": ["responsible_ai_trained"],
                    },
                    "ai_upskilling": {
                        "title": "AI Upskilling Program",
                        "description": "Offer voluntary AI skills courses for interested employees.",
                        "cost": -800_000,
                        "impacts": {"reputation": +2},
                        "flags_set": ["ai_upskilling"],
                    },
                    "no_hr_action": {
                        "title": "No AI Workforce Training",
                        "description": "No employee AI training. Risk of misuse and compliance gaps.",
                        "cost": 0,
                        "impacts": {"governance_risk_delta": +3, "social_license_delta": -2},
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
            "human_resources": {
                "label": "Circular Workforce",
                "icon": "👥",
                "options": {
                    "circular_reskilling": {
                        "title": "Circular Economy Reskilling",
                        "description": "Retrain manufacturing workforce in disassembly, refurbishment and reverse logistics skills. Directly supports circular transition.",
                        "cost": -3_500_000,
                        "impacts": {"social_license_delta": +6, "reputation": +4},
                        "flags_set": ["circular_reskilled"],
                    },
                    "cross_training": {
                        "title": "Cross-Functional Training",
                        "description": "Implement cross-BU rotation to build generalist skills.",
                        "cost": -1_000_000,
                        "impacts": {"reputation": +2, "governance_risk_delta": -2},
                        "flags_set": ["cross_trained"],
                    },
                    "no_hr_action": {
                        "title": "No Skills Investment",
                        "description": "No additional circular economy workforce investment.",
                        "cost": 0,
                        "impacts": {"social_license_delta": -2},
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
            "human_resources": {
                "label": "Water Crisis Workforce",
                "icon": "👥",
                "options": {
                    "water_steward_training": {
                        "title": "Water Steward Certification",
                        "description": "Certify facility managers as AWS Water Stewards. Embeds water conservation into daily operations and reporting.",
                        "cost": -2_000_000,
                        "impacts": {"social_license_delta": +4, "reputation": +3, "water_dependency_delta": -3},
                        "flags_set": ["water_stewards_trained"],
                    },
                    "shift_rotation": {
                        "title": "Shift Rotation Optimization",
                        "description": "Restructure shift patterns to reduce peak water demand during shortage periods.",
                        "cost": -700_000,
                        "impacts": {"water_dependency_delta": -2, "reputation": +1},
                        "flags_set": ["shift_optimized"],
                    },
                    "no_hr_action": {
                        "title": "No Workforce Action",
                        "description": "No water-related workforce changes.",
                        "cost": 0,
                        "impacts": {},
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
            "human_resources": {
                "label": "Just Transition Workforce",
                "icon": "👥",
                "options": {
                    "full_severance_redeploy": {
                        "title": "Full Severance & Redeployment",
                        "description": "Offer 12-month enhanced severance packages plus funded redeployment into green economy roles. Partnered with local government employment services.",
                        "cost": -6_000_000,
                        "impacts": {"social_license_delta": +10, "reputation": +7, "burnout_delta": -12},
                        "flags_set": ["full_severance_redeployment"],
                    },
                    "statutory_minimum": {
                        "title": "Statutory Minimum Only",
                        "description": "Meet legal requirements for notice periods and minimum severance. No additional support.",
                        "cost": -1_000_000,
                        "impacts": {"social_license_delta": -3, "reputation": -2},
                        "flags_set": ["statutory_minimum_hr"],
                    },
                    "no_hr_action": {
                        "title": "No HR Consideration",
                        "description": "No dedicated HR strategy for factory closures. Workers learn from media.",
                        "cost": 0,
                        "impacts": {"social_license_delta": -8, "reputation": -6, "burnout_delta": +15},
                        "flags_set": ["hr_absent_transition"],
                    },
                },
            },
        },
    },

    10: {
        "title": "Year 5 Corporate Destiny",
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
                        "description": "Commit to 80% carbon reduction by Year 5.",
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
            "human_resources": {
                "label": "Workforce Legacy",
                "icon": "👥",
                "options": {
                    "employee_ownership": {
                        "title": "Employee Ownership Scheme",
                        "description": "Transition 10% of equity to an Employee Share Ownership Plan (ESOP). Aligns workforce incentives with long-term sustainability.",
                        "cost": -5_000_000,
                        "impacts": {"social_license_delta": +8, "reputation": +6, "governance_risk_delta": -5},
                        "flags_set": ["employee_ownership"],
                    },
                    "retention_bonuses": {
                        "title": "Retention Bonus Package",
                        "description": "Issue retention bonuses to key talent during restructuring uncertainty.",
                        "cost": -2_000_000,
                        "impacts": {"reputation": +2},
                        "flags_set": ["retention_bonuses"],
                    },
                    "no_hr_action": {
                        "title": "No Workforce Consideration",
                        "description": "No dedicated workforce strategy during corporate restructuring.",
                        "cost": 0,
                        "impacts": {"social_license_delta": -4, "reputation": -3},
                        "flags_set": [],
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
            "exclusivity_warnings": [str],  # any mutual exclusivity violations
        }
    """
    # ── Mutual exclusivity config: groups of flags that cannot coexist ──
    # Within each group, flags are listed in priority order (first match wins).
    MUTUAL_EXCLUSIVITY: dict[int, list[list[set]]] = {
        7: [
            # Synergy unlock and circular redesign are separate strategic paths
            [{"synergy_unlock", "waste_to_energy"}, {"circular_redesign"}],
        ],
        9: [
            # Community fund, managed transition, and immediate closure are
            # three distinct approaches to factory closure
            [{"community_fund"}, {"managed_transition"}, {"immediate_closure"}],
        ],
    }

    cfg = PILLAR_OPTIONS.get(round_number)
    if not cfg:
        return {"total_cost": 0, "impacts": {}, "flags_set": [], "per_area": {}, "exclusivity_warnings": []}

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

    # ── Enforce mutual exclusivity ──
    exclusivity_warnings: list[str] = []
    exclusivity_groups = MUTUAL_EXCLUSIVITY.get(round_number, [])
    flag_set = set(all_flags)

    for group in exclusivity_groups:
        matched_indices = [i for i, flag_group in enumerate(group) if flag_group & flag_set]
        if len(matched_indices) > 1:
            # Conflict: keep the first match (highest priority), remove later matches
            kept = group[matched_indices[0]]
            for idx in matched_indices[1:]:
                conflicting_flags = group[idx] & flag_set
                for f in conflicting_flags:
                    all_flags.remove(f)
                    # Also remove the impacts from the conflicting area
                    for area_key, area_data in per_area.items():
                        action_key = area_data["action_key"]
                        area_cfg = areas.get(area_key, {})
                        action = area_cfg.get("options", {}).get(action_key, {})
                        action_flags = set(action.get("flags_set", []))
                        if f in action_flags:
                            # Reverse this area's impacts (keep cost — you still paid for it)
                            for k, v in area_data.get("impacts", {}).items():
                                combined_impacts[k] = combined_impacts.get(k, 0) - v
                            exclusivity_warnings.append(
                                f"⚠️ Mutual exclusivity: '{area_data['title']}' conflicts with "
                                f"'{group[matched_indices[0]]}' — impacts reversed (cost still applies)."
                            )
                            break

    return {
        "total_cost": total_cost,
        "impacts": combined_impacts,
        "flags_set": all_flags,
        "per_area": per_area,
        "exclusivity_warnings": exclusivity_warnings,
    }


def translate_pillars_to_legacy_choice(
    round_number: int,
    pillar_choices: dict[str, str],
) -> str:
    """
    Map a set of pillar selections to the closest legacy A/B/C choice
    for backward compatibility with round_logic._get_primary_choice().

    Fix #5: Strategy upgraded from pure cost heuristic to flag-aware priority.
    Round-specific FLAG_OVERRIDES encode the STRATEGIC INTENT of critical pillar
    flags (e.g. deny_and_deflect, insurance_only, ethical_ai_overhaul) so the
    correct post-tick code path fires regardless of total spend.
    Cost-based heuristic is retained as fallback for ambiguous combinations.
    """
    agg = aggregate_pillar_decisions(round_number, pillar_choices)
    flags_this_round = set(agg["flags_set"])
    total_cost = agg["total_cost"]

    # ── Round-specific flag-based overrides (strategic intent > cost proxy) ──
    # Maps legacy proxy choice -> set of pillar flags that unambiguously
    # indicate that choice. Checked in a, b, c priority order.
    FLAG_OVERRIDES: dict[int, dict[str, set]] = {
        1: {
            "option_b": {"deep_audit_completed"},
            "option_c": {"electronics_blindspot"},
        },
        2: {
            # Reverse map ONLY (proxy-choice inference) — never a write path.
            # Legacy flag names retained so replays of old saves still resolve.
            "option_a": {"materiality_board_established", "materiality_aligned"},
            "option_c": {"materiality_framework_ignored", "materiality_ignored"},
        },
        3: {
            "option_a": {"supply_chain_disruption_risk"},
            "option_b": {"green_bond_active"},
            "option_c": {"carbon_deferred"},
        },
        4: {
            "option_a": {"remediation_active", "supplier_remediation", "stakeholder_compensated"},
            "option_c": {"deny_and_deflect"},
        },
        5: {
            "option_a": {"hard_engineering"},
            "option_b": {"nature_based_resilience"},
            "option_c": {"insurance_only"},
        },
        6: {
            "option_a": {"ai_monetised"},
            "option_b": {"ethical_ai_overhaul"},
            "option_c": {"quiet_patch"},
        },
        7: {
            "option_c": {"synergy_unlock", "waste_to_energy"},
            "option_a": {"circular_redesign"},
        },
        8: {
            "option_c": {"desalination_built"},
            "option_b": {"electronics_water_priority"},
            "option_a": {"water_efficiency_all"},
        },
        9: {
            "option_c": {"community_fund"},
            "option_b": {"managed_transition"},
            "option_a": {"immediate_closure"},
        },
        10: {
            "option_a": {"resist_integrate"},
            "option_c": {"divest"},
        },
    }

    round_overrides = FLAG_OVERRIDES.get(round_number, {})
    # Priority order: option_a first (most aggressive), then b, then c
    for proxy_choice in ("option_a", "option_b", "option_c"):
        trigger_flags = round_overrides.get(proxy_choice, set())
        if trigger_flags & flags_this_round:  # any overlap -> match
            return proxy_choice

    # ── Fallback: cost-based heuristic for rounds with no flag match ──
    # More negative cost = more aggressive strategic spend = bolder choice
    if total_cost <= -8_000_000:
        return "option_a"
    elif total_cost <= -3_000_000:
        return "option_b"
    else:
        return "option_c"


# ═════════════════════════════════════════════════════════════════
#  VERTICAL-SPECIFIC PILLAR OVERRIDE LOADER
#  Loads backend/db/pillar_overrides_{bu_id}.json and merges with
#  the standard PILLAR_OPTIONS for a given round.
# ═════════════════════════════════════════════════════════════════

_OVERRIDES_DB_DIR = Path(__file__).parent / "db"


def _load_pillar_overrides(bu_id: str) -> dict:
    """
    Load pillar overrides JSON for a given vertical.
    Returns empty dict if file not found or invalid.
    Schema: { "override_areas": {...}, "custom_areas": [...] }
    """
    if not bu_id:
        return {}
    bu_id_norm = bu_id.lower().replace(" ", "_").replace("-", "_")
    path = _OVERRIDES_DB_DIR / f"pillar_overrides_{bu_id_norm}.json"
    if not path.exists():
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[pillar_configs] Error loading overrides for {bu_id}: {e}")
        return {}


def _save_pillar_overrides(bu_id: str, data: dict) -> None:
    """Persist pillar overrides JSON for a given vertical."""
    bu_id_norm = bu_id.lower().replace(" ", "_").replace("-", "_")
    _OVERRIDES_DB_DIR.mkdir(parents=True, exist_ok=True)
    path = _OVERRIDES_DB_DIR / f"pillar_overrides_{bu_id_norm}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_pillar_config_for_vertical(round_number: int, bu_id: str = "") -> dict:
    """
    Return the pillar areas config for a given round and business vertical.

    Resolution order:
    1. Start with the generic PILLAR_OPTIONS[round_number]
    2. Apply override_areas (replaces matching standard areas 1-for-1)
    3. Append custom_areas (sorted by their order field)

    If no bu_id or no overrides file exists, returns the generic config.
    """
    base_config = copy.deepcopy(PILLAR_OPTIONS.get(round_number, {}))
    if not base_config:
        return base_config

    if not bu_id:
        return base_config

    overrides = _load_pillar_overrides(bu_id)
    if not overrides:
        return base_config

    areas = base_config.get("areas", {})

    # Apply override_areas: replace matching standard area key
    for area_key, area_override in overrides.get("override_areas", {}).items():
        areas[area_key] = area_override  # Replaces the standard area at that key

    # Append custom_areas: sorted by order, injected after standard areas
    custom_areas = overrides.get("custom_areas", [])
    if custom_areas:
        sorted_custom = sorted(custom_areas, key=lambda x: x.get("order", 99))
        for ca in sorted_custom:
            area_key = ca.get("area_key", f"custom_{len(areas)}")
            areas[area_key] = {
                "label": ca.get("label", "Custom Area"),
                "icon": ca.get("icon", "⭐"),
                "description_override": ca.get("description", ""),
                "options": ca.get("options", {}),
                "is_custom": True,
                "order": ca.get("order", 99),
            }

    base_config["areas"] = areas
    base_config["vertical"] = bu_id
    return base_config


def get_pillar_summary(bu_id: str = "") -> dict:
    """
    Return a summary of all standard + override + custom pillar areas for a vertical.
    Used by the PillarConfigurator admin panel.
    """
    overrides = _load_pillar_overrides(bu_id)
    # Standard areas (from Round 1 as reference)
    r1 = PILLAR_OPTIONS.get(1, {})
    standard_areas = [
        {"area_key": k, "label": v.get("label", k), "icon": v.get("icon", "⭐"), "is_standard": True}
        for k, v in r1.get("areas", {}).items()
    ]
    override_areas = [
        {
            "area_key": k,
            "label": v.get("label", k),
            "icon": v.get("icon", "⭐"),
            "is_override": True,
            "replaces": k,
            "options": v.get("options", {}),
        }
        for k, v in overrides.get("override_areas", {}).items()
    ]
    custom_areas = overrides.get("custom_areas", [])
    return {
        "bu_id": bu_id,
        "standard_areas": standard_areas,
        "override_areas": override_areas,
        "custom_areas": custom_areas,
        "total_areas": len(standard_areas) + len(custom_areas),
    }
