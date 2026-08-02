"""
Muressons — Sustainability Reporting Round Configs (5 rounds)
"""

REPORTING_ROUND_CONFIGS: dict = {
    1: {
        "title": "CSRD/ESRS Readiness Assessment",
        "crisis_title": "📋 EU Regulatory Deadline Approaching",
        "crisis_narrative": (
            "The EU Corporate Sustainability Reporting Directive (CSRD) mandates "
            "your first disclosure under the European Sustainability Reporting "
            "Standards (ESRS) in 18 months. A gap analysis reveals you currently "
            "meet only 35% of the required data points. Your CFO estimates the "
            "remediation cost at $2-8M depending on approach."
        ),
        "options": {
            "option_a": {
                "title": "Full ESRS Implementation Programme",
                "description": (
                    "Engage Big 4 advisory, implement enterprise-wide data collection, "
                    "conduct double materiality assessment across all ESRS topics, "
                    "and establish a Sustainability Reporting Steering Committee."
                ),
                "impacts": {"treasury": -6_000_000, "reputation": 8, "governance_risk_delta": -8},
                "flags_set": ["sr_full_esrs", "sr_data_infrastructure"],
            },
            "option_b": {
                "title": "Phased Compliance Approach",
                "description": (
                    "Prioritise mandatory ESRS topics (E1-Climate, S1-Workers), "
                    "use industry templates, and build internal capacity "
                    "progressively. Address non-material topics in Year 2."
                ),
                "impacts": {"treasury": -3_000_000, "reputation": 4, "governance_risk_delta": -3},
                "flags_set": ["sr_phased_compliance"],
            },
            "option_c": {
                "title": "Minimum Viable Compliance",
                "description": (
                    "Focus only on the absolute minimum disclosures required. "
                    "Use boilerplate language, avoid quantitative targets, and "
                    "rely on existing data wherever possible."
                ),
                "impacts": {"treasury": -1_000_000, "reputation": -3, "governance_risk_delta": 4},
                "flags_set": ["sr_minimum_compliance"],
            },
        },
    },
    2: {
        "title": "Climate Disclosure (TCFD/ISSB)",
        "crisis_title": "🌡️ Investor Demand for Climate Scenarios",
        "crisis_narrative": (
            "BlackRock, Vanguard, and State Street have jointly written demanding "
            "TCFD-aligned climate scenario analysis with 1.5°C and 3°C pathways. "
            "IFRS S2 (Climate) requires disclosure of Scope 1, 2, and 3 emissions "
            "with transition plans. Your current Scope 3 data coverage is 42%."
        ),
        "options": {
            "option_a": {
                "title": "Comprehensive Climate Disclosure",
                "description": (
                    "Commission full scenario analysis (1.5°C, 2°C, 3°C pathways), "
                    "achieve 90%+ Scope 3 coverage using supplier engagement, "
                    "set SBTi-validated targets, and publish a Net-Zero Transition "
                    "Plan with interim milestones."
                ),
                "impacts": {"treasury": -5_000_000, "reputation": 12, "carbon_intensity_delta": -3, "governance_risk_delta": -6},
                "flags_set": ["sr_climate_leader", "sr_sbti_targets", "sr_scope3_complete"],
            },
            "option_b": {
                "title": "Targeted Climate Reporting",
                "description": (
                    "Conduct 2°C scenario analysis, improve Scope 3 to 70% "
                    "coverage using spend-based methods, and set aspirational "
                    "targets aligned with sector benchmarks."
                ),
                "impacts": {"treasury": -2_500_000, "reputation": 5, "governance_risk_delta": -3},
                "flags_set": ["sr_climate_adequate"],
            },
            "option_c": {
                "title": "Qualitative Narrative Only",
                "description": (
                    "Provide qualitative climate risk narrative without "
                    "quantitative scenario analysis. Report Scope 1 & 2 only. "
                    "State that Scope 3 methodology is 'under development'."
                ),
                "impacts": {"treasury": -500_000, "reputation": -6, "governance_risk_delta": 5},
                "flags_set": ["sr_climate_gap"],
            },
        },
    },
    3: {
        "title": "Social & Governance Metrics",
        "crisis_title": "👥 S-Pillar Scrutiny from Regulators",
        "crisis_narrative": (
            "The EU Sustainable Finance Disclosure Regulation (SFDR) requires "
            "Principal Adverse Impact (PAI) indicators on social topics. Your "
            "current disclosures lack: gender pay gap data, board diversity "
            "metrics, supply chain human rights due diligence, and employee "
            "wellbeing indicators. An activist investor has filed a shareholder "
            "proposal demanding a Human Capital Management report."
        ),
        "options": {
            "option_a": {
                "title": "Comprehensive Social & Governance Framework",
                "description": (
                    "Implement a full Human Capital Management system, publish "
                    "gender pay gap analysis with remediation targets, adopt "
                    "ISO 30414 (Human Capital Reporting), disclose board "
                    "skills matrix, and establish a Living Wage commitment."
                ),
                "impacts": {"treasury": -4_000_000, "reputation": 10, "social_license_delta": 8, "governance_risk_delta": -6},
                "flags_set": ["sr_social_leader", "sr_living_wage"],
            },
            "option_b": {
                "title": "SFDR PAI Compliance Package",
                "description": (
                    "Report all mandatory PAI indicators, publish diversity "
                    "data, and conduct a gender pay gap analysis. Meet regulatory "
                    "requirements without exceeding them."
                ),
                "impacts": {"treasury": -2_000_000, "reputation": 4, "governance_risk_delta": -3},
                "flags_set": ["sr_sfdr_compliant"],
            },
            "option_c": {
                "title": "Minimal Social Disclosure",
                "description": (
                    "Disclose only legally mandated social metrics. Argue "
                    "that detailed human capital data is 'commercially "
                    "sensitive'. Oppose the activist shareholder proposal."
                ),
                "impacts": {"treasury": -500_000, "reputation": -5, "social_license_delta": -4, "governance_risk_delta": 5},
                "flags_set": ["sr_social_gap", "sr_activist_opposition"],
            },
        },
    },
    4: {
        "title": "Assurance & Verification",
        "crisis_title": "🔍 Credibility Crisis: Data Integrity Questions",
        "crisis_narrative": (
            "An investigative report questions the accuracy of your Scope 2 "
            "market-based emissions accounting. The SEC's climate rule and "
            "CSRD both require third-party assurance. Your competitors are "
            "moving from limited to reasonable assurance. Without credible "
            "verification, all your previous disclosures are undermined."
        ),
        "options": {
            "option_a": {
                "title": "Reasonable Assurance (Full Scope)",
                "description": (
                    "Engage a Big 4 firm for reasonable (not limited) assurance "
                    "across all material sustainability metrics. Implement "
                    "COSO-aligned internal controls for ESG data. Establish "
                    "a dedicated ESG Data Quality function."
                ),
                "impacts": {"treasury": -5_000_000, "reputation": 12, "governance_risk_delta": -8},
                "flags_set": ["sr_reasonable_assurance", "sr_esg_controls"],
            },
            "option_b": {
                "title": "Limited Assurance with Roadmap",
                "description": (
                    "Obtain limited assurance on climate metrics, publish "
                    "a roadmap to reasonable assurance by Year 5, and "
                    "implement basic data quality checks."
                ),
                "impacts": {"treasury": -2_500_000, "reputation": 5, "governance_risk_delta": -3},
                "flags_set": ["sr_limited_assurance"],
            },
            "option_c": {
                "title": "Self-Verification",
                "description": (
                    "Rely on internal audit for data verification. "
                    "Argue that the assurance market is 'immature' and "
                    "standards are still evolving. Save costs."
                ),
                "impacts": {"treasury": -300_000, "reputation": -8, "governance_risk_delta": 6},
                "flags_set": ["sr_no_external_assurance", "sr_credibility_gap"],
            },
        },
    },
    5: {
        "title": "Integrated Reporting & Value Creation",
        "crisis_title": "💎 Board Demands: Prove ESG Creates Value",
        "crisis_narrative": (
            "The board challenges: 'We've spent $15M+ on ESG reporting. Where's "
            "the ROI?' Shareholders want to see how sustainability connects to "
            "financial performance. The International Integrated Reporting Council "
            "(IIRC) framework demands showing how six capitals (financial, "
            "manufactured, intellectual, human, social, natural) create value "
            "over time."
        ),
        "special_rules": {
            "data_infrastructure_bonus": {
                "condition": "sr_data_infrastructure",
                "effect": "R1 investment in data systems enables automated integrated dashboards",
            },
            "credibility_gap_penalty": {
                "condition": "sr_credibility_gap",
                "effect": "Lack of assurance undermines integrated report credibility",
            },
        },
        "options": {
            "option_a": {
                "title": "Full Six-Capitals Integrated Report",
                "description": (
                    "Publish a pioneering Integrated Report mapping all six "
                    "capitals with quantified value-creation narratives. "
                    "Implement an ESG-Financial Connectivity Dashboard for "
                    "the board. Commission academic research on ESG-ROI."
                ),
                "impacts": {"treasury": -4_000_000, "reputation": 15, "governance_risk_delta": -5},
                "flags_set": ["sr_integrated_leader", "sr_value_demonstrated"],
            },
            "option_b": {
                "title": "Enhanced Annual Report Integration",
                "description": (
                    "Embed key ESG metrics into the Annual Report's strategy "
                    "and MD&A sections. Show correlation between ESG investments "
                    "and financial performance. Include case studies."
                ),
                "impacts": {"treasury": -2_000_000, "reputation": 6, "governance_risk_delta": -2},
                "flags_set": ["sr_ar_integrated"],
            },
            "option_c": {
                "title": "Separate ESG Supplement",
                "description": (
                    "Publish ESG data as a standalone PDF supplement. "
                    "Keep financial and sustainability reporting separate. "
                    "Argue integration is 'premature' until standards converge."
                ),
                "impacts": {"treasury": -500_000, "reputation": -3, "governance_risk_delta": 3},
                "flags_set": ["sr_siloed_reporting"],
            },
        },
    },
}
