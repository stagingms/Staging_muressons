"""
Muressons Global Corporation — Ethics & Sustainability Round Configs

5 rounds of crisis-driven ethical decision-making:
  ES-R1: Ethical AI Governance
  ES-R2: Modern Slavery Due Diligence
  ES-R3: Greenwashing Substantiation
  ES-R4: Biodiversity & Natural Capital
  ES-R5: Just Transition & Community Impact
"""

ETHICS_ROUND_CONFIGS: dict = {
    1: {
        "title": "Ethical AI Governance",
        "crisis_title": "🤖 Algorithmic Bias Discovery",
        "crisis_narrative": (
            "An internal audit reveals your recruitment AI has a 34% gender bias "
            "in shortlisting. The EU AI Act classifies employment AI as 'high-risk', "
            "requiring conformity assessments. A whistleblower leak is imminent — "
            "you have 72 hours to respond before the story breaks."
        ),
        "options": {
            "option_a": {
                "title": "Full Transparency & Remediation",
                "description": (
                    "Immediately halt the AI system, publish a transparency report, "
                    "commission an independent algorithmic audit, and establish a "
                    "permanent AI Ethics Board with external stakeholders."
                ),
                "impacts": {
                    "treasury": -4_000_000,
                    "reputation": 8,
                    "governance_risk_delta": -8,
                },
                "flags_set": ["es_ai_ethics_board", "es_transparency_leader"],
            },
            "option_b": {
                "title": "Quiet Fix & Compliance",
                "description": (
                    "Retrain the model with de-biased data, implement monitoring "
                    "dashboards, and file a proactive notification with the EU AI "
                    "Office. Avoid public disclosure unless legally required."
                ),
                "impacts": {
                    "treasury": -2_000_000,
                    "reputation": 2,
                    "governance_risk_delta": -3,
                },
                "flags_set": ["es_ai_quiet_fix"],
            },
            "option_c": {
                "title": "Minimise & Defend",
                "description": (
                    "Challenge the audit methodology, argue 'statistical noise', "
                    "and continue operations while legal reviews the whistleblower "
                    "threat. Prepare counter-narratives for media engagement."
                ),
                "impacts": {
                    "treasury": 0,
                    "reputation": -6,
                    "governance_risk_delta": 5,
                },
                "flags_set": ["es_ai_denial", "es_whistleblower_risk"],
            },
        },
    },
    2: {
        "title": "Modern Slavery Due Diligence",
        "crisis_title": "⛓️ Forced Labour in Tier-3 Suppliers",
        "crisis_narrative": (
            "An investigative journalist has documented forced labour conditions "
            "at a Tier-3 cobalt supplier in the DRC. Your electronics division "
            "sources 40% of its cobalt through this supply chain. The UK Modern "
            "Slavery Act and EU CSDDD both require proactive due diligence. "
            "The story will be published in the Financial Times in 5 days."
        ),
        "options": {
            "option_a": {
                "title": "Comprehensive Due Diligence Programme",
                "description": (
                    "Launch a full supply chain human rights impact assessment, "
                    "join the Responsible Minerals Initiative, establish grievance "
                    "mechanisms for workers, and commit to 100% certified cobalt "
                    "within 24 months."
                ),
                "impacts": {
                    "treasury": -5_000_000,
                    "reputation": 10,
                    "social_license_delta": 8,
                    "governance_risk_delta": -6,
                },
                "flags_set": ["es_human_rights_leader", "es_cobalt_certified"],
            },
            "option_b": {
                "title": "Targeted Remediation",
                "description": (
                    "Terminate the specific Tier-3 supplier, conduct spot audits "
                    "on remaining cobalt sources, and publish a revised Modern "
                    "Slavery Statement with strengthened commitments."
                ),
                "impacts": {
                    "treasury": -2_500_000,
                    "reputation": 3,
                    "social_license_delta": 3,
                    "governance_risk_delta": -2,
                },
                "flags_set": ["es_supplier_terminated"],
            },
            "option_c": {
                "title": "Legal Firewall",
                "description": (
                    "Argue the Tier-3 supplier is outside your 'sphere of influence', "
                    "rely on existing contractual provisions, and prepare legal "
                    "responses to any allegations. Maintain current supply relationships."
                ),
                "impacts": {
                    "treasury": 0,
                    "reputation": -8,
                    "social_license_delta": -6,
                    "governance_risk_delta": 4,
                },
                "flags_set": ["es_modern_slavery_unresolved", "es_legal_firewall"],
            },
        },
    },
    3: {
        "title": "Greenwashing Substantiation",
        "crisis_title": "🎭 Regulatory Greenwash Inquiry",
        "crisis_narrative": (
            "The Advertising Standards Authority (ASA) and the EU Green Claims "
            "Directive are investigating your 'carbon neutral' marketing claims. "
            "Your offset portfolio includes HFC-23 destruction credits that "
            "regulators consider 'non-additional'. Competitors are watching — "
            "a finding against you would set sector precedent."
        ),
        "options": {
            "option_a": {
                "title": "Science-Based Claims Overhaul",
                "description": (
                    "Withdraw all unsubstantiated claims, replace offsets with "
                    "insetting and removal credits, commission third-party "
                    "verification (SBTi-aligned), and publish a Transition Plan "
                    "with interim targets."
                ),
                "impacts": {
                    "treasury": -6_000_000,
                    "reputation": 12,
                    "carbon_intensity_delta": -5,
                },
                "flags_set": ["es_sbti_aligned", "es_green_claims_verified"],
            },
            "option_b": {
                "title": "Selective Correction",
                "description": (
                    "Replace the HFC-23 credits with nature-based solutions, "
                    "update marketing language from 'carbon neutral' to 'climate "
                    "positive journey', and engage proactively with the ASA."
                ),
                "impacts": {
                    "treasury": -3_000_000,
                    "reputation": 5,
                    "carbon_intensity_delta": -2,
                },
                "flags_set": ["es_partial_correction"],
            },
            "option_c": {
                "title": "Defend & Lobby",
                "description": (
                    "Challenge the ASA methodology, lobby for industry-wide "
                    "offset standards, and maintain current claims while the "
                    "regulatory process unfolds."
                ),
                "impacts": {
                    "treasury": -500_000,
                    "reputation": -10,
                    "governance_risk_delta": 6,
                },
                "flags_set": ["es_greenwash_defended", "es_lobby_active"],
            },
        },
    },
    4: {
        "title": "Biodiversity & Natural Capital",
        "crisis_title": "🦋 TNFD Disclosure & Ecosystem Collapse",
        "crisis_narrative": (
            "The Taskforce on Nature-related Financial Disclosures (TNFD) has "
            "flagged your consumer goods division's palm oil supply chain as "
            "'high nature impact'. Satellite imagery shows 3,200 hectares of "
            "primary forest cleared by your suppliers since 2020. The Science "
            "Based Targets for Nature (SBTN) framework demands a 'No Net Loss' "
            "commitment by 2030."
        ),
        "options": {
            "option_a": {
                "title": "Nature-Positive Transformation",
                "description": (
                    "Commit to SBTN No-Net-Loss, establish a $3M biodiversity "
                    "restoration fund, shift to 100% RSPO-certified palm oil, "
                    "and publish a TNFD-aligned disclosure with dependency "
                    "and impact metrics."
                ),
                "impacts": {
                    "treasury": -7_000_000,
                    "reputation": 10,
                    "natural_capital_debt_delta": -15,
                    "social_license_delta": 5,
                },
                "flags_set": ["es_nature_positive", "es_tnfd_disclosed"],
            },
            "option_b": {
                "title": "Targeted Conservation",
                "description": (
                    "Fund reforestation of 1,000 hectares, transition 60% of "
                    "palm oil to certified sources, and begin TNFD pilot "
                    "disclosures for the consumer goods division."
                ),
                "impacts": {
                    "treasury": -3_500_000,
                    "reputation": 4,
                    "natural_capital_debt_delta": -6,
                },
                "flags_set": ["es_partial_conservation"],
            },
            "option_c": {
                "title": "Market-Based Deferral",
                "description": (
                    "Purchase biodiversity credits, argue that palm oil "
                    "alternatives are technically infeasible at scale, and "
                    "defer TNFD disclosure until mandatory reporting begins."
                ),
                "impacts": {
                    "treasury": -1_000_000,
                    "reputation": -5,
                    "natural_capital_debt_delta": 5,
                    "governance_risk_delta": 3,
                },
                "flags_set": ["es_biodiversity_deferred"],
            },
        },
    },
    5: {
        "title": "Just Transition & Community Impact",
        "crisis_title": "✊ Workforce Transition Ultimatum",
        "crisis_narrative": (
            "Your decarbonisation commitments require closing two high-emission "
            "manufacturing plants in economically disadvantaged regions, affecting "
            "4,200 workers and 15,000 indirect dependents. The International "
            "Labour Organization and local government demand a 'Just Transition' "
            "plan. Unions threaten sector-wide industrial action if workers "
            "are 'sacrificed for shareholder ESG scores'."
        ),
        "special_rules": {
            "prior_ethics_bonus": {
                "condition": "es_human_rights_leader",
                "effect": "Union trust increased — reduces strike probability by 30%",
                "strike_reduction": 0.30,
            },
            "ai_denial_penalty": {
                "condition": "es_ai_denial",
                "effect": "Employees distrust management — increases strike probability by 20%",
                "strike_increase": 0.20,
            },
        },
        "options": {
            "option_a": {
                "title": "Comprehensive Just Transition Fund",
                "description": (
                    "Establish a $10M Just Transition Fund providing 3-year "
                    "retraining programmes, relocation support, early retirement "
                    "packages, and community economic development grants. "
                    "Partner with local government and unions on governance."
                ),
                "impacts": {
                    "treasury": -10_000_000,
                    "reputation": 15,
                    "social_license_delta": 12,
                },
                "flags_set": ["es_just_transition_leader", "es_community_invested"],
            },
            "option_b": {
                "title": "Phased Transition with Retraining",
                "description": (
                    "Close plants over 36 months rather than 12, provide "
                    "retraining vouchers and outplacement support, and "
                    "contribute $2M to a regional development fund."
                ),
                "impacts": {
                    "treasury": -5_000_000,
                    "reputation": 6,
                    "social_license_delta": 5,
                },
                "flags_set": ["es_phased_transition"],
            },
            "option_c": {
                "title": "Rapid Closure with Statutory Minimum",
                "description": (
                    "Close both plants within 6 months, provide only legally "
                    "required severance, and redirect savings to green "
                    "technology investments. Maximise shareholder value from "
                    "the transition."
                ),
                "impacts": {
                    "treasury": -1_000_000,
                    "reputation": -12,
                    "social_license_delta": -10,
                    "governance_risk_delta": 8,
                },
                "flags_set": ["es_workers_abandoned", "es_union_strike_risk"],
            },
        },
    },
}
