"""
Muressons — BRSR NGRBC Round Configs (5 rounds)
"""

BRSR_ROUND_CONFIGS: dict = {
    1: {
        "title": "Governance & Transparency (P1 & P7)",
        "crisis_title": "📋 SEBI BRSR Mandate Triggers",
        "crisis_narrative": (
            "SEBI notifies the top 1,000 listed companies. Muressons must establish "
            "a BRSR Steering Committee. The MCA's NGRBC guidelines require a signed "
            "Board declaration. Political contributions from the Consumer Goods BU's "
            "lobbying in Delhi surface in an RTI query."
        ),
        "options": {
            "option_a": {
                "title": "Radical Transparency (Leadership Indicator)",
                "description": (
                    "Establish a Board-level ESG Committee, publish a public lobbying register, "
                    "roll out ethics training across the value chain, and appoint an independent "
                    "ethics officer. Exceeds Essential requirements."
                ),
                "impacts": {"treasury": -4_000_000, "reputation": 10, "governance_risk_delta": -8},
                "flags_set": ["brsr_pioneer", "brsr_indicator_leadership"],
            },
            "option_b": {
                "title": "Standard Compliance (Essential Indicators)",
                "description": (
                    "Adopt a standard code of conduct, whistle-blower policy, and "
                    "conflict of interest disclosures. Meets all Essential Indicators "
                    "for Principle 1 and Principle 7."
                ),
                "impacts": {"treasury": -2_000_000, "reputation": 5, "governance_risk_delta": -3},
                "flags_set": ["brsr_indicator_essential"],
            },
            "option_c": {
                "title": "Reactive Disclosure (Below Compliance)",
                "description": (
                    "Fulfill only mandatory basic disclosures. Delay establishing a "
                    "Board-level committee and rely on the existing compliance team. "
                    "Risks a SEBI show-cause notice."
                ),
                "impacts": {"treasury": -500_000, "reputation": -5, "governance_risk_delta": 10},
                "flags_set": ["governance_fragility"],
            },
        },
    },
    2: {
        "title": "Workforce & Human Rights (P3 & P5)",
        "crisis_title": "👥 Living Wage Demands & OHS Gaps",
        "crisis_narrative": (
            "Electronics BU unions in Chennai demand living wage disclosures, a key "
            "Leadership Indicator under Principle 3. Meanwhile, Pharma BU contract "
            "workers face Occupational Health & Safety (OHS) gaps at API plants. "
            "POSH committee reports also highlight inconsistencies."
        ),
        "options": {
            "option_a": {
                "title": "Living Wage Standard (Leadership Indicator)",
                "description": (
                    "Conduct a living wage gap analysis, implement comprehensive DEI "
                    "dashboards, upgrade OHS to ISO 45001 across all BUs, and perform "
                    "human rights due diligence for Tier-1 suppliers."
                ),
                "impacts": {"treasury": -8_000_000, "social_license_delta": 15, "burnout_delta": -12, "governance_risk_delta": -5},
                "flags_set": ["brsr_living_wage", "brsr_indicator_leadership"],
            },
            "option_b": {
                "title": "Safety & POSH Focus (Essential+)",
                "description": (
                    "Mandatory safety upgrades at API plants, disclose gender pay gap data, "
                    "and remediate POSH compliance issues. Meets Essential indicators and "
                    "partially addresses Leadership expectations."
                ),
                "impacts": {"treasury": -4_000_000, "social_license_delta": 5, "burnout_delta": -5},
                "flags_set": ["brsr_indicator_essential"],
            },
            "option_c": {
                "title": "Statutory Minimums Only",
                "description": (
                    "Adhere strictly to legal minimum wage compliance and basic safety records. "
                    "Fails Leadership Indicators and increases the risk of labor unrest."
                ),
                "impacts": {"treasury": 0, "social_license_delta": -10, "burnout_delta": 5},
                "flags_set": ["brsr_statutory_minimums"],
            },
        },
    },
    3: {
        "title": "Environment & Circularity (P6 & P2)",
        "crisis_title": "🌊 API Discharge & EPR Scrutiny",
        "crisis_narrative": (
            "The CPCB flags the Pharma BU's water discharge in Hyderabad for API residues. "
            "Leadership Indicators require Extended Producer Responsibility (EPR) disclosures "
            "for Electronics (e-waste) and Consumer Goods (plastics). BRSR demands Scope 1+2 GHG intensity."
        ),
        "options": {
            "option_a": {
                "title": "Circular Symbiosis & ZLD (Leadership)",
                "description": (
                    "Deploy Zero Liquid Discharge (ZLD) for Pharma, full EPR compliance for all BUs, "
                    "a Waste-to-Energy partnership, Scope 3 mapping, and biodiversity impact assessment."
                ),
                "impacts": {"treasury": -10_000_000, "natural_capital_debt_delta": -15, "carbon_intensity_delta": -5},
                "flags_set": ["brsr_circular_symbiosis", "sdg_12_leadership", "brsr_indicator_leadership"],
            },
            "option_b": {
                "title": "Efficiency Upgrades & EPR (Essential+)",
                "description": (
                    "Implement high-efficiency water recycling, comprehensive Scope 1+2 reporting, "
                    "EPR registration, and standard waste segregation. Partially addresses Leadership metrics."
                ),
                "impacts": {"treasury": -6_000_000, "natural_capital_debt_delta": -8},
                "flags_set": ["brsr_indicator_essential"],
            },
            "option_c": {
                "title": "Regulatory Minimums",
                "description": (
                    "Pay standard environmental levies and submit minimal waste reporting. Fails "
                    "Leadership requirements and risks further CPCB penalties."
                ),
                "impacts": {"treasury": -2_000_000, "natural_capital_debt_delta": 5, "carbon_intensity_delta": 2},
                "flags_set": ["brsr_regulatory_minimum"],
            },
        },
    },
    4: {
        "title": "Value Chain & BRSR Core",
        "crisis_title": "🔍 BRSR Core Reasonable Assurance",
        "crisis_narrative": (
            "SEBI introduces 'BRSR Core' for value chain disclosures. Muressons falls in the top 250 "
            "glide path, making reasonable assurance mandatory for 9 key attributes. Concurrently, "
            "Tier-2 electronics suppliers face scrutiny for child labor, and CG faces a product recall."
        ),
        "options": {
            "option_a": {
                "title": "Multi-Tier Assurance (Leadership)",
                "description": (
                    "Implement blockchain-based supply chain traceability, reasonable assurance engagement "
                    "with Big 4, MSME supplier development programs, and advanced consumer grievance analytics."
                ),
                "impacts": {"treasury": -6_000_000, "reputation": 12, "governance_risk_delta": -10},
                "flags_set": ["brsr_core_assured", "brsr_indicator_leadership"],
            },
            "option_b": {
                "title": "Tier-1 Screening (Essential)",
                "description": (
                    "Conduct Tier-1 supplier audits, limited assurance engagement, and document CSR spend. "
                    "Meets Essential requirements for value chain reporting."
                ),
                "impacts": {"treasury": -2_000_000, "reputation": 4, "governance_risk_delta": -3},
                "flags_set": ["brsr_indicator_essential"],
            },
            "option_c": {
                "title": "Self-Assessment Only",
                "description": (
                    "Rely entirely on supplier questionnaires and internal verification. Sets Greenwash Risk "
                    "flag and creates significant SEBI compliance vulnerability."
                ),
                "impacts": {"treasury": -500_000, "reputation": -8, "governance_risk_delta": 8},
                "flags_set": ["brsr_greenwash_risk"],
            },
        },
    },
    5: {
        "title": "Integrated Disclosure & ESG Alpha",
        "crisis_title": "💎 The Final Report & ESG Alpha",
        "crisis_narrative": (
            "FY-end approaches. The Board demands the final BRSR filing. The Investor Relations team "
            "must present the ESG narrative. CRISIL ESG and Sustainalytics are benchmarking Muressons "
            "against peers. The choice: How deeply do you integrate sustainability into corporate identity?"
        ),
        "options": {
            "option_a": {
                "title": "Integrated Report (Leadership)",
                "description": (
                    "Publish a Six Capitals integrated report (IIRC), ESG-Financial connectivity dashboard, "
                    "third-party materiality validation, and GRI/TCFD cross-references. Prevents Exit Multiple haircut."
                ),
                "impacts": {"treasury": -4_000_000, "reputation": 15},
                "flags_set": ["brsr_integrated_report", "brsr_indicator_leadership"],
            },
            "option_b": {
                "title": "Strategic BRSR (Essential+)",
                "description": (
                    "Provide a structured BRSR aligned with performance KPIs, sector benchmarking, and "
                    "a basic materiality matrix."
                ),
                "impacts": {"treasury": -2_000_000, "reputation": 6},
                "flags_set": ["brsr_indicator_essential"],
            },
            "option_c": {
                "title": "Compliance File",
                "description": (
                    "Submit a basic statutory BRSR filing with minimal narrative context. Blocks Truth Premium bonus."
                ),
                "impacts": {"treasury": -500_000, "reputation": -3},
                "flags_set": ["brsr_compliance_only"],
            },
        },
    },
}
