"""
Muressons — BRSR NGRBC Round Configs (5 rounds)
"""
from __future__ import annotations
from typing import Any
import copy


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
                "regulatory_tooltip": "Mitigates P1 Principle friction; satisfies Clause 4(b) of the updated NGRBC mandate regarding independent oversight. Exceeds SEBI Circular SEBI/HO/CFD/CMD-2/P/CIR/2023/18 disclosure requirements for board-level ESG governance structures.",
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
                "regulatory_tooltip": "Meets P1 Essential Indicator baseline for anti-corruption and conflict of interest disclosures. Compliance with Rule 8(5)(xi)(a) of the Companies (Accounts) Rules, 2014 but may not satisfy institutional investor ESG screening criteria.",
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
                "regulatory_tooltip": "Heightens vulnerability to SEBI Show-Cause interventions under Regulation 4(2)(f) of the LODR Regulations, 2015. Compounds Section 135 CSR shortfall penalties and NGRBC P1 non-compliance citations.",
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
                "regulatory_tooltip": "Aligns with P3 Leadership Indicators; rectifies statutory EPFO and ESIC non-compliance risks among third-party contractual dependencies. Satisfies POSH Act, 2013 reporting mandates and ISO 45001:2018 OHS certification requirements.",
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
                "regulatory_tooltip": "Meets P3 Essential Indicator on employee well-being metrics; addresses basic OHS compliance under Factories Act, 1948 but defers living wage gap analysis required by P3 Leadership tier.",
            },
            "option_c": {
                "title": "Statutory Minimums Only",
                "description": (
                    "Adhere strictly to legal minimum wage compliance and basic safety records. "
                    "Fails Leadership Indicators and increases the risk of labor unrest."
                ),
                "impacts": {"treasury": 0, "social_license_delta": -10, "burnout_delta": 5},
                "flags_set": ["brsr_statutory_minimums"],
                "regulatory_tooltip": "Heightens vulnerability to P3/P5 non-compliance citations; compounds exposure to Section 25FF Industrial Disputes Act consequences and ESI Act penalty proceedings. Risk of labour commissioner suo-motu investigation.",
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
                "regulatory_tooltip": "Satisfies P6 Leadership Indicator; exceeds BRSR Core Attribute 5 (Energy intensity per rupee of turnover) requirements. Aligns with CPCB Zero Liquid Discharge mandates under National Green Tribunal Order dated 13.01.2015 for pharmaceutical effluents.",
            },
            "option_b": {
                "title": "Efficiency Upgrades & EPR (Essential+)",
                "description": (
                    "Implement high-efficiency water recycling, comprehensive Scope 1+2 reporting, "
                    "EPR registration, and standard waste segregation. Partially addresses Leadership metrics."
                ),
                "impacts": {"treasury": -6_000_000, "natural_capital_debt_delta": -8},
                "flags_set": ["brsr_indicator_essential"],
                "regulatory_tooltip": "Meets P6 Essential Indicator baseline; partial compliance with EPR registration under Plastic Waste Management Rules, 2016 and E-Waste (Management) Rules, 2022. May trigger SEBI clarification query on Scope 3 methodology.",
            },
            "option_c": {
                "title": "Regulatory Minimums",
                "description": (
                    "Pay standard environmental levies and submit minimal waste reporting. Fails "
                    "Leadership requirements and risks further CPCB penalties."
                ),
                "impacts": {"treasury": -2_000_000, "natural_capital_debt_delta": 5, "carbon_intensity_delta": 2},
                "flags_set": ["brsr_regulatory_minimum"],
                "regulatory_tooltip": "Heightens vulnerability to SPCB closure orders under Section 33(A) of the Water Act, 1974. Compounds CPCB consent-to-operate revocation risk and MoEFCC National Clean Air Programme non-compliance penalties.",
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
                "regulatory_tooltip": "Ensures BRSR Core readiness; initiates preliminary Top-250 glide path reasonable assurance mapping under SEBI Circular SEBI/HO/CFD/CMD-2/P/CIR/2023/18. Blockchain traceability exceeds P4 Leadership Indicator requirements.",
            },
            "option_b": {
                "title": "Tier-1 Screening (Essential)",
                "description": (
                    "Conduct Tier-1 supplier audits, limited assurance engagement, and document CSR spend. "
                    "Meets Essential requirements for value chain reporting."
                ),
                "impacts": {"treasury": -2_000_000, "reputation": 4, "governance_risk_delta": -3},
                "flags_set": ["brsr_indicator_essential"],
                "regulatory_tooltip": "Meets P4 Essential Indicator on supply chain disclosure; partial compliance with BRSR Core but defers reasonable assurance engagement to subsequent filing period under Regulation 34(2)(f).",
            },
            "option_c": {
                "title": "Self-Assessment Only",
                "description": (
                    "Rely entirely on supplier questionnaires and internal verification. Sets Greenwash Risk "
                    "flag and creates significant SEBI compliance vulnerability."
                ),
                "impacts": {"treasury": -500_000, "reputation": -8, "governance_risk_delta": 8},
                "flags_set": ["brsr_greenwash_risk"],
                "regulatory_tooltip": "Heightens greenwash exposure; creates material discrepancy between self-assessed and third-party validated BRSR Core attributes. SEBI adjudication proceedings under Regulation 4(2)(f) of LODR likely.",
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
                "regulatory_tooltip": "Satisfies P9 Leadership Indicator on integrated reporting; aligns with IIRC <IR> Framework mandatory connectivity requirements. Prevents exit multiple haircut under SEBI ESG indices eligibility criteria.",
            },
            "option_b": {
                "title": "Strategic BRSR (Essential+)",
                "description": (
                    "Provide a structured BRSR aligned with performance KPIs, sector benchmarking, and "
                    "a basic materiality matrix."
                ),
                "impacts": {"treasury": -2_000_000, "reputation": 6},
                "flags_set": ["brsr_indicator_essential"],
                "regulatory_tooltip": "Meets P9 Essential Indicator on sustainability reporting structure. Basic materiality matrix satisfies Rule 8(5)(xii) but defers TCFD/GRI cross-referencing to subsequent disclosure period.",
            },
            "option_c": {
                "title": "Compliance File",
                "description": (
                    "Submit a basic statutory BRSR filing with minimal narrative context. Blocks Truth Premium bonus."
                ),
                "impacts": {"treasury": -500_000, "reputation": -3},
                "flags_set": ["brsr_compliance_only"],
                "regulatory_tooltip": "Blocks Truth Premium bonus. Bare minimum statutory filing under Rule 34(2)(f) without narrative context. Compounds BRSR performance score depreciation and institutional ESG fund exclusion risk.",
            },
        },
    },
    6: {
        "title": "Human Rights Realities (P5)",
        "crisis_title": "👥 Human Rights & Child Labor Exposure",
        "crisis_narrative": (
            "A localized media investigation exposes human rights violations and child labor "
            "within unorganized, unregistered Tier-2 component manufacturers supplying your "
            "Electronics manufacturing hub."
        ),
        "options": {
            "option_a": {
                "title": "Deep Ecosystem Formalization",
                "description": (
                    "Implement deep human rights due diligence with Tier-2 digital traceability, "
                    "strict contractual enforcement, independent unannounced audits, NGO partnerships, "
                    "and vendor ESG capacity overhaul programs."
                ),
                "impacts": {"treasury": -6_000_000, "reputation": 12, "governance_risk_delta": -6},
                "flags_set": ["deep_hrdd_active", "brsr_indicator_leadership"],
                "regulatory_tooltip": "Satisfies P5 Leadership Indicator on Human Rights Due Diligence (HRDD); exceeds UNGP Reporting Framework requirements. Aligns with Section 135 Schedule VII Item (x) and NGRBC Principle 5 on stakeholder engagement.",
            },
            "option_b": {
                "title": "Tier-1 Vendor Containment",
                "description": (
                    "Focus containment on Tier-1 vendors with cloud portal expansion, "
                    "self-declaration documentation, and scheduled annual sample audits."
                ),
                "impacts": {"treasury": -2_500_000, "reputation": 4, "governance_risk_delta": -2},
                "flags_set": ["brsr_indicator_essential"],
                "regulatory_tooltip": "Meets P5 Essential Indicator baseline on Tier-1 vendor due diligence. Cloud-based self-declaration may not satisfy 'Reasonable Assurance' standard under BRSR Core for human rights attributes.",
            },
            "option_c": {
                "title": "Superficial Desk Audits",
                "description": (
                    "Conduct superficial desk audits relying exclusively on vendor assurances. "
                    "No system architecture changes or institutional outlays."
                ),
                "impacts": {"treasury": -400_000, "reputation": -10, "governance_risk_delta": 8},
                "flags_set": ["tier2_human_rights_risk"],
                "regulatory_tooltip": "Heightens exposure to SEBI adverse media screening algorithms; compounds P5 non-compliance risk. May trigger NHRC suo-motu cognizance under Section 12(1) of the Protection of Human Rights Act, 1993.",
            },
        },
    },
    7: {
        "title": "Policy Advocacy & Ethical Frameworks (P7)",
        "crisis_title": "📢 Carbon Tax Lobbying Pressure",
        "crisis_narrative": (
            "A major national trade association aggressively lobbies the Ministry to dilute "
            "industrial carbon taxes. As an industry vanguard, Muressons is pressured to sign "
            "the joint lobby memo or state a clear independent stance."
        ),
        "options": {
            "option_a": {
                "title": "Public Progressive Dissent",
                "description": (
                    "Publish pro-climate independent position papers, withdraw from carbon-regressive "
                    "trade associations, establish transparent advocacy protocols, endow sustainability chairs, "
                    "and deploy corporate integrity officers."
                ),
                "impacts": {"treasury": -3_000_000, "reputation": 16, "governance_risk_delta": -3},
                "flags_set": ["policy_leadership", "brsr_indicator_leadership"],
                "regulatory_tooltip": "Satisfies P7 Leadership Indicator on responsible policy advocacy. Independent pro-climate position exceeds NGRBC Principle 7 requirements on transparent lobbying disclosures and trade association governance.",
            },
            "option_b": {
                "title": "Silent Abstention from Voting",
                "description": (
                    "Submit internal dissent letters, draft restrained policy papers, "
                    "and incorporate standard governance disclosures without public stance."
                ),
                "impacts": {"treasury": -1_000_000, "reputation": 2, "governance_risk_delta": 0},
                "flags_set": ["brsr_indicator_essential"],
                "regulatory_tooltip": "Meets P7 Essential Indicator on policy advocacy disclosure. Silent abstention satisfies minimum governance standards but defers public accountability on climate lobbying positions.",
            },
            "option_c": {
                "title": "Align with Lobbying Cartel",
                "description": (
                    "Sign common cartel strategic statements, suppress group lobbying metrics, "
                    "and execute full silent policy compliance."
                ),
                "impacts": {"treasury": -200_000, "reputation": -8, "governance_risk_delta": 6},
                "flags_set": ["greenwash_advocacy"],
                "regulatory_tooltip": "Heightens P7 greenwash advocacy risk; suppresses lobbying metrics in contravention of NGRBC Principle 7. Compounds vulnerability to RTI Act, 2005 disclosures and media investigative scrutiny.",
            },
        },
    },
    8: {
        "title": "Inclusive Micro-Growth & Vendor Protection (P8)",
        "crisis_title": "💳 MSME Payment Crisis",
        "crisis_narrative": (
            "SEBI tightens monitoring on payments to Micro, Small, and Medium Enterprises (MSMEs). "
            "Muressons' working capital optimizations have inadvertently locked localized vendors "
            "into extended 90-day credit cycles, threatening vendor business continuity."
        ),
        "options": {
            "option_a": {
                "title": "TReDS Integration & Instant Settle",
                "description": (
                    "Immediate TReDS platform integration, formal MSME operational development programs, "
                    "disadvantaged & women-led vendor sourcing quotas, small vendor credit guarantees, "
                    "and systematized procurement ethics training."
                ),
                "impacts": {"treasury": -5_500_000, "reputation": 11, "governance_risk_delta": -5},
                "flags_set": ["msme_champion", "brsr_indicator_leadership"],
                "regulatory_tooltip": "Satisfies P8 Leadership Indicator on inclusive growth; aligns with TReDS platform mandatory registration under MSMED Act, 2006 Section 15. Exceeds SEBI BRSR Core Attribute on MSME payment cycle disclosures.",
            },
            "option_b": {
                "title": "Selective Liquidity Windows",
                "description": (
                    "Manual accelerated payment tracks, periodic vendor technical seminars, "
                    "aggregated supply auditing, and basic advance payment operations."
                ),
                "impacts": {"treasury": -2_500_000, "reputation": 4, "governance_risk_delta": -1},
                "flags_set": ["brsr_indicator_essential"],
                "regulatory_tooltip": "Meets P8 Essential Indicator on MSME engagement metrics. Selective liquidity windows address basic compliance with Section 43B(h) of the Income Tax Act for MSME payment timelines.",
            },
            "option_c": {
                "title": "Maintain Cash Hoarding Strategy",
                "description": (
                    "Maintain institutional 90-day credit rules, execute basic commercial "
                    "transactions only, and disregard supplier demographic metrics."
                ),
                "impacts": {"treasury": 0, "reputation": -12, "governance_risk_delta": 8},
                "flags_set": ["working_capital_hoarder"],
                "regulatory_tooltip": "Heightens P8 non-compliance risk; compounds exposure to MSMED Act penal interest provisions and SEBI adverse commentary in annual governance review. Risk of supplier payment litigation under Section 16.",
            },
        },
    },
    9: {
        "title": "Value Chain Assurance (P4 & P9)",
        "crisis_title": "🔍 BRSR Core Statutory Mandate",
        "crisis_narrative": (
            "The SEBI 'BRSR Core' glide path takes full statutory effect for top market-cap entities. "
            "Reasonable assurance by a third-party auditor across 9 attributes in the value chain is "
            "mandatory. Skipping true vendor formalization in previous cycles will trigger an extreme "
            "correction expense."
        ),
        "options": {
            "option_a": {
                "title": "Full-Spectrum Reasonable Assurance",
                "description": (
                    "Big 4 reasonable value chain assurance, real-time automated telemetry engines, "
                    "Tier-2 supplier onboarding networks, enterprise consumer grievance analytics, "
                    "and advanced multi-tier ESG specialist certification."
                ),
                "impacts": {"treasury": -6_500_000, "reputation": 14, "governance_risk_delta": -8},
                "flags_set": ["brsr_core_assured", "csrd_aligned", "brsr_indicator_leadership"],
                "regulatory_tooltip": "Ensures BRSR Core statutory compliance; initiates full reasonable assurance under SA 3000 (Revised) for value chain attributes. Big 4 engagement exceeds SEBI top-250 mandatory requirements.",
            },
            "option_b": {
                "title": "Tier-1 Verification & Limited Scope",
                "description": (
                    "Mid-tier limited scope assurance audits, intermittent digital verification portals, "
                    "semi-annual value chain spot auditing, and generic supplier ESG dossiers."
                ),
                "impacts": {"treasury": -3_000_000, "reputation": 5, "governance_risk_delta": -2},
                "flags_set": ["brsr_indicator_essential"],
                "regulatory_tooltip": "Meets P4/P9 Essential Indicator on value chain disclosure. Limited scope assurance satisfies minimum BRSR Core filing but may trigger SEBI limited assurance gap observations.",
            },
            "option_c": {
                "title": "Self-Assessed Compliance Only",
                "description": (
                    "Rely on in-house self-assessed filing matrix. No core infrastructure enhancements, "
                    "no active engagement strategies, and no analytics infrastructure."
                ),
                "impacts": {"treasury": -600_000, "reputation": -15, "governance_risk_delta": 10},
                "flags_set": ["brsr_greenwash_risk"],
                "regulatory_tooltip": "Heightens greenwash exposure catastrophically; in-house self-assessment creates terminal discrepancy with BRSR Core mandatory assurance standards. SEBI delisting from ESG indices highly probable.",
            },
        },
    },
    10: {
        "title": "Global Integration & Double Materiality (Integrated)",
        "crisis_title": "💎 Filing Deadline & CSRD Alignment",
        "crisis_narrative": (
            "Filing deadline. Institutional investors demand alignment between the BRSR submission "
            "and global CSRD standards for European distribution. To capture the terminal premium, "
            "you must execute a verified Double Materiality analysis validating both financial and "
            "real-world impact footprints."
        ),
        "options": {
            "option_a": {
                "title": "Integrated Report & Double Materiality",
                "description": (
                    "Publish a holistically audited Six Capitals integrated report, conduct third-party "
                    "double materiality verification, execute global GRI/TCFD/ESRS multi-framework mapping, "
                    "launch real-time ESG financial connectivity, and deploy institutional analyst communications."
                ),
                "impacts": {"treasury": -4_500_000, "reputation": 20, "governance_risk_delta": -10},
                "flags_set": ["brsr_integrated_report", "csrd_aligned", "brsr_net_positive_dividend", "brsr_indicator_leadership"],
                "regulatory_tooltip": "Satisfies BRSR-CSRD convergence requirements; double materiality analysis aligns with ESRS 1 and EFRAG technical standards. Captures terminal ESG Alpha Dividend under SEBI integrated reporting incentive framework.",
            },
            "option_b": {
                "title": "Standard Strategic BRSR",
                "description": (
                    "Generate advanced cross-pillar KPI indexes, formulate internal matrix materiality "
                    "registries, and compile consolidated executive summary briefing materials."
                ),
                "impacts": {"treasury": -2_000_000, "reputation": 8, "governance_risk_delta": -3},
                "flags_set": ["brsr_indicator_essential"],
                "regulatory_tooltip": "Meets Essential Indicator on structured BRSR filing. Internal materiality registry addresses Rule 8(5)(xii) minimum requirements but does not satisfy European institutional investor CSRD screening mandates.",
            },
            "option_c": {
                "title": "Bare Minimum Regulatory File",
                "description": (
                    "File basic bare minimum regulatory disclosures. By-pass specialized double materiality "
                    "assessments. No international standard integrations or external outreach."
                ),
                "impacts": {"treasury": -500_000, "reputation": -5, "governance_risk_delta": 5},
                "flags_set": ["brsr_compliance_only"],
                "regulatory_tooltip": "Blocks ESG Alpha Dividend permanently. Bare minimum filing forfeits CSRD alignment and triggers SEBI ESG fund exclusion. Terminal valuation suffers maximum M_R haircut under greenwash penalty matrix.",
            },
        },
    },
}


# ═════════════════════════════════════════════════════════════════
#  BRSR STRATEGIC PILLARS (areas schema — mirrors PILLAR_OPTIONS)
#  10 rounds × 5 areas × 3 options each
# ═════════════════════════════════════════════════════════════════



BRSR_PILLAR_OPTIONS: dict[int, dict[str, Any]] = {

    # ── Round 1: Governance & Transparency (P1 & P7) ───────────
    1: {
        "title": "Governance & Transparency (P1 & P7)",
        "description": (
            "SEBI mandates BRSR reporting. Establish governance structures, "
            "ethics frameworks, and transparency mechanisms across Muressons."
        ),
        "areas": {
            "energy": {
                "label": "Board ESG Governance",
                "icon": "⚡",
                "options": {
                    "board_esg_committee": {
                        "title": "Board ESG Committee",
                        "description": (
                            "Establish a Board-level ESG Committee with independent directors, "
                            "quarterly KPI reviews, and a dedicated sustainability budget."
                        ),
                        "cost": -2_500_000,
                        "impacts": {"governance_risk_delta": -6, "reputation": 4},
                        "flags_set": ["brsr_pioneer", "brsr_indicator_leadership"],
                        "regulatory_tooltip": (
                            "Satisfies P6 Leadership Indicator; aligns with BRSR Core Attribute 5 "
                            "(Energy intensity per rupee of turnover) and MoEFCC National Clean Air "
                            "Programme reporting mandates."
                        ),
                    },
                    "ethics_compliance_audit": {
                        "title": "Ethics Compliance Audit",
                        "description": (
                            "Engage an external firm to audit current ethics and compliance "
                            "posture across all BUs. Produces a gap report for NGRBC alignment."
                        ),
                        "cost": -1_000_000,
                        "impacts": {"governance_risk_delta": -2, "reputation": 2},
                        "flags_set": ["brsr_indicator_essential", "brsr_ethics_officer"],
                        "regulatory_tooltip": (
                            "Meets P6 Essential Indicator baseline; partial compliance with BRSR Core "
                            "Attribute 5 but may trigger SEBI clarification query on energy intensity "
                            "methodology."
                        ),
                    },
                    "status_quo": {
                        "title": "Status Quo",
                        "description": "Rely on existing management committee. No new governance investment.",
                        "cost": 0,
                        "impacts": {"governance_risk_delta": 3},
                        "flags_set": ["governance_fragility"],
                        "regulatory_tooltip": (
                            "Heightens vulnerability to SEBI Show-Cause interventions; compounds P6 "
                            "non-compliance risks under Rule 34(2)(f) of the Companies Act, 2013."
                        ),
                    },
                },
            },
            "operations": {
                "label": "Transparency & Lobbying",
                "icon": "🏭",
                "options": {
                    "public_lobbying_register": {
                        "title": "Public Lobbying Register",
                        "description": (
                            "Publish a transparent register of all political contributions, "
                            "trade-body memberships, and policy advocacy positions."
                        ),
                        "cost": -1_500_000,
                        "impacts": {"reputation": 5, "governance_risk_delta": -4},
                        "flags_set": ["brsr_pioneer", "brsr_indicator_leadership"],
                        "regulatory_tooltip": (
                            "Fulfills Extended Producer Responsibility (EPR) statutory filing requirements "
                            "under CPCB hazardous waste amendments; satisfies P2 Leadership Indicator on "
                            "product lifecycle stewardship."
                        ),
                    },
                    "ethics_officer": {
                        "title": "Ethics Officer Appointment",
                        "description": (
                            "Appoint a Chief Ethics Officer with reporting line to the Board. "
                            "Covers conflict-of-interest disclosures and policy compliance."
                        ),
                        "cost": -800_000,
                        "impacts": {"reputation": 2, "governance_risk_delta": -2},
                        "flags_set": ["brsr_indicator_essential", "brsr_ethics_officer"],
                        "regulatory_tooltip": (
                            "Meets P2 Essential Indicator on responsible sourcing; partial compliance with "
                            "EPR registration requirements under Plastic Waste Management Rules, 2016."
                        ),
                    },
                    "no_change": {
                        "title": "No Change",
                        "description": "Maintain existing compliance structure without additional transparency.",
                        "cost": 0,
                        "impacts": {"reputation": -2},
                        "flags_set": ["governance_fragility"],
                        "regulatory_tooltip": (
                            "Heightens vulnerability to SPCB closure orders; compounds Section 135 CSR "
                            "shortfall penalties and CPCB consent-to-operate revocation risk."
                        ),
                    },
                },
            },
            "supply_chain": {
                "label": "Value Chain Ethics",
                "icon": "🔗",
                "options": {
                    "value_chain_ethics_training": {
                        "title": "Value Chain Ethics Training",
                        "description": (
                            "Deploy ethics and anti-bribery training across Tier-1 and Tier-2 "
                            "suppliers, including NGRBC Principle 1 alignment workshops."
                        ),
                        "cost": -2_000_000,
                        "impacts": {"governance_risk_delta": -3, "reputation": 3},
                        "flags_set": ["brsr_pioneer", "brsr_indicator_leadership"],
                        "regulatory_tooltip": (
                            "Ensures BRSR Core readiness; initiates preliminary Top-250 glide path "
                            "reasonable assurance mapping under SEBI Circular "
                            "SEBI/HO/CFD/CMD-2/P/CIR/2023/18."
                        ),
                    },
                    "tier1_screening": {
                        "title": "Tier-1 Screening",
                        "description": (
                            "Basic ethics questionnaire and screening for Tier-1 suppliers only. "
                            "Meets Essential Indicator requirements."
                        ),
                        "cost": -500_000,
                        "impacts": {"governance_risk_delta": -1, "reputation": 1},
                        "flags_set": ["brsr_indicator_essential", "brsr_ethics_officer"],
                        "regulatory_tooltip": (
                            "Meets P4 Essential Indicator on supply chain disclosure; partial compliance "
                            "with BRSR Core but defers reasonable assurance engagement to subsequent "
                            "filing period."
                        ),
                    },
                    "defer": {
                        "title": "Defer",
                        "description": "Postpone supply chain ethics assessment to next fiscal year.",
                        "cost": 0,
                        "impacts": {"governance_risk_delta": 2},
                        "flags_set": ["governance_fragility"],
                        "regulatory_tooltip": (
                            "Heightens greenwash exposure; creates material discrepancy between "
                            "self-assessed and third-party validated BRSR Core attributes for value "
                            "chain KPIs."
                        ),
                    },
                },
            },
            "offsetting": {
                "label": "Ethics Oversight Investment",
                "icon": "🌱",
                "options": {
                    "independent_ethics_board": {
                        "title": "Independent Ethics Board",
                        "description": (
                            "Fund an independent ethics advisory board with external experts, "
                            "civil society representatives, and an annual public ethics report."
                        ),
                        "cost": -2_000_000,
                        "impacts": {"governance_risk_delta": -5, "reputation": 4},
                        "flags_set": ["brsr_pioneer", "brsr_indicator_leadership"],
                        "regulatory_tooltip": (
                            "Mitigates P1 Principle friction; satisfies Clause 4(b) of the updated "
                            "NGRBC mandate regarding independent oversight of lobbying and political "
                            "contribution disclosures."
                        ),
                    },
                    "csr_fund": {
                        "title": "CSR Fund",
                        "description": (
                            "Allocate CSR budget towards governance capacity building. "
                            "Partial coverage of NGRBC Principle 7 expectations."
                        ),
                        "cost": -700_000,
                        "impacts": {"reputation": 2, "governance_risk_delta": -1},
                        "flags_set": ["brsr_indicator_essential", "brsr_ethics_officer"],
                        "regulatory_tooltip": (
                            "Meets P1 Essential Indicator on anti-corruption policies; partial compliance "
                            "with NGRBC governance standards but may not satisfy institutional investor "
                            "ESG screening criteria."
                        ),
                    },
                    "no_investment": {
                        "title": "No Investment",
                        "description": "No additional ethics or governance investment this round.",
                        "cost": 0,
                        "impacts": {},
                        "flags_set": ["governance_fragility"],
                        "regulatory_tooltip": (
                            "Heightens governance fragility; compounds vulnerability to SEBI adjudication "
                            "proceedings under Regulation 4(2)(f) of the LODR Regulations, 2015."
                        ),
                    },
                },
            },
            "human_resources": {
                "label": "Whistleblower & Conduct",
                "icon": "👥",
                "options": {
                    "whistleblower_hotline": {
                        "title": "Whistleblower Hotline",
                        "description": (
                            "Launch a 24/7 anonymous whistleblower hotline with third-party "
                            "case management and Board-level escalation protocols."
                        ),
                        "cost": -1_500_000,
                        "impacts": {"social_license_delta": 4, "governance_risk_delta": -3},
                        "flags_set": ["brsr_pioneer", "brsr_indicator_leadership"],
                        "regulatory_tooltip": (
                            "Aligns with P3 Leadership Indicators; rectifies statutory EPFO and ESIC "
                            "non-compliance risks among third-party contractual dependencies. Satisfies "
                            "POSH Act, 2013 reporting mandates."
                        ),
                    },
                    "basic_code_of_conduct": {
                        "title": "Basic Code of Conduct",
                        "description": (
                            "Roll out a standard code of conduct document to all employees. "
                            "Meets Essential Indicator expectations for Principle 1."
                        ),
                        "cost": -500_000,
                        "impacts": {"social_license_delta": 1, "governance_risk_delta": -1},
                        "flags_set": ["brsr_indicator_essential", "brsr_ethics_officer"],
                        "regulatory_tooltip": (
                            "Meets P3 Essential Indicator on employee well-being metrics; addresses basic "
                            "OHS compliance under Factories Act but defers living wage gap analysis."
                        ),
                    },
                    "no_hr_action": {
                        "title": "No HR Action",
                        "description": "No whistleblower or conduct investments.",
                        "cost": 0,
                        "impacts": {"social_license_delta": -2},
                        "flags_set": ["governance_fragility"],
                        "regulatory_tooltip": (
                            "Heightens vulnerability to P3/P5 non-compliance citations; compounds exposure "
                            "to Section 25FF Industrial Disputes Act consequences and ESI Act penalty "
                            "proceedings."
                        ),
                    },
                },
            },
        },
    },

    # ── Round 2: Workforce & Human Rights (P3 & P5) ────────────
    2: {
        "title": "Workforce & Human Rights (P3 & P5)",
        "description": (
            "Unions demand living wage disclosures. OHS gaps and POSH "
            "inconsistencies require decisive workforce action."
        ),
        "areas": {
            "energy": {
                "label": "Occupational Health & Safety",
                "icon": "⚡",
                "options": {
                    "iso45001_upgrade": {
                        "title": "ISO 45001 OHS Upgrade",
                        "description": (
                            "Full ISO 45001 certification across all BUs — Pharma API plants, "
                            "Electronics assembly, and Consumer Goods factories."
                        ),
                        "cost": -3_000_000,
                        "impacts": {"social_license_delta": 6, "burnout_delta": -8, "governance_risk_delta": -3},
                        "flags_set": ["brsr_living_wage", "brsr_indicator_leadership"],
                        "regulatory_tooltip": (
                            "Satisfies P6 Leadership Indicator; aligns with BRSR Core Attribute 5 "
                            "(Energy intensity per rupee of turnover) and MoEFCC National Clean Air "
                            "Programme reporting mandates."
                        ),
                    },
                    "basic_safety": {
                        "title": "Basic Safety Compliance",
                        "description": (
                            "Upgrade fire-safety and hazard signage to meet Factories Act standards. "
                            "Essential Indicator compliance for Principle 3."
                        ),
                        "cost": -1_000_000,
                        "impacts": {"social_license_delta": 2, "burnout_delta": -3},
                        "flags_set": ["brsr_indicator_essential"],
                        "regulatory_tooltip": (
                            "Meets P6 Essential Indicator baseline; partial compliance with BRSR Core "
                            "Attribute 5 but may trigger SEBI clarification query on energy intensity "
                            "methodology."
                        ),
                    },
                    "no_change": {
                        "title": "No Change",
                        "description": "Maintain current safety standards. Risk OHS violation notices.",
                        "cost": 0,
                        "impacts": {"burnout_delta": 3, "governance_risk_delta": 2},
                        "flags_set": ["brsr_statutory_minimums"],
                        "regulatory_tooltip": (
                            "Heightens vulnerability to SEBI Show-Cause interventions; compounds P6 "
                            "non-compliance risks under Rule 34(2)(f) of the Companies Act, 2013."
                        ),
                    },
                },
            },
            "operations": {
                "label": "POSH & Grievance Redressal",
                "icon": "🏭",
                "options": {
                    "posh_remediation": {
                        "title": "POSH Remediation Program",
                        "description": (
                            "Comprehensive POSH committee overhaul with external legal counsel, "
                            "mandatory training, and quarterly compliance audits."
                        ),
                        "cost": -2_000_000,
                        "impacts": {"social_license_delta": 5, "governance_risk_delta": -4},
                        "flags_set": ["brsr_living_wage", "brsr_indicator_leadership"],
                        "regulatory_tooltip": (
                            "Fulfills Extended Producer Responsibility (EPR) statutory filing requirements "
                            "under CPCB hazardous waste amendments; satisfies P2 Leadership Indicator on "
                            "product lifecycle stewardship."
                        ),
                    },
                    "grievance_mechanism": {
                        "title": "Grievance Mechanism",
                        "description": (
                            "Establish formal employee grievance channels with documented "
                            "resolution timelines. Meets Essential requirements."
                        ),
                        "cost": -800_000,
                        "impacts": {"social_license_delta": 2, "governance_risk_delta": -1},
                        "flags_set": ["brsr_indicator_essential"],
                        "regulatory_tooltip": (
                            "Meets P2 Essential Indicator on responsible sourcing; partial compliance with "
                            "EPR registration requirements under Plastic Waste Management Rules, 2016."
                        ),
                    },
                    "no_change": {
                        "title": "No Change",
                        "description": "Rely on existing informal complaint mechanisms.",
                        "cost": 0,
                        "impacts": {"social_license_delta": -3, "governance_risk_delta": 3},
                        "flags_set": ["brsr_statutory_minimums"],
                        "regulatory_tooltip": (
                            "Heightens vulnerability to SPCB closure orders; compounds Section 135 CSR "
                            "shortfall penalties and CPCB consent-to-operate revocation risk."
                        ),
                    },
                },
            },
            "supply_chain": {
                "label": "Human Rights Due Diligence",
                "icon": "🔗",
                "options": {
                    "tier1_hrdd": {
                        "title": "Tier-1 Human Rights Due Diligence",
                        "description": (
                            "Full HRDD assessment of Tier-1 suppliers covering child labor, "
                            "forced labor, and working conditions. Aligned with UNGPs."
                        ),
                        "cost": -2_500_000,
                        "impacts": {"social_license_delta": 5, "reputation": 3},
                        "flags_set": ["brsr_living_wage", "brsr_indicator_leadership"],
                        "regulatory_tooltip": (
                            "Ensures BRSR Core readiness; initiates preliminary Top-250 glide path "
                            "reasonable assurance mapping under SEBI Circular "
                            "SEBI/HO/CFD/CMD-2/P/CIR/2023/18."
                        ),
                    },
                    "supplier_questionnaire": {
                        "title": "Supplier Questionnaire",
                        "description": (
                            "Self-assessment questionnaire sent to top 50 suppliers. "
                            "Partial coverage for Essential Indicators."
                        ),
                        "cost": -500_000,
                        "impacts": {"reputation": 1},
                        "flags_set": ["brsr_indicator_essential"],
                        "regulatory_tooltip": (
                            "Meets P4 Essential Indicator on supply chain disclosure; partial compliance "
                            "with BRSR Core but defers reasonable assurance engagement to subsequent "
                            "filing period."
                        ),
                    },
                    "defer": {
                        "title": "Defer",
                        "description": "Postpone supply chain human rights assessment.",
                        "cost": 0,
                        "impacts": {"reputation": -2},
                        "flags_set": ["brsr_statutory_minimums"],
                        "regulatory_tooltip": (
                            "Heightens greenwash exposure; creates material discrepancy between "
                            "self-assessed and third-party validated BRSR Core attributes for value "
                            "chain KPIs."
                        ),
                    },
                },
            },
            "offsetting": {
                "label": "Wage & Welfare Fund",
                "icon": "🌱",
                "options": {
                    "living_wage_fund": {
                        "title": "Living Wage Gap Analysis Fund",
                        "description": (
                            "Commission an independent living wage gap analysis and establish a "
                            "₹2 Crore fund to close identified wage gaps across all BUs."
                        ),
                        "cost": -2_000_000,
                        "impacts": {"social_license_delta": 8, "burnout_delta": -5},
                        "flags_set": ["brsr_living_wage", "brsr_indicator_leadership"],
                        "regulatory_tooltip": (
                            "Mitigates P1 Principle friction; satisfies Clause 4(b) of the updated "
                            "NGRBC mandate regarding independent oversight of lobbying and political "
                            "contribution disclosures."
                        ),
                    },
                    "statutory_compliance_fund": {
                        "title": "Statutory Compliance Fund",
                        "description": (
                            "Budget allocation to ensure PF, ESIC, and gratuity compliance "
                            "across contract workers. Essential Indicator coverage."
                        ),
                        "cost": -600_000,
                        "impacts": {"social_license_delta": 2},
                        "flags_set": ["brsr_indicator_essential"],
                        "regulatory_tooltip": (
                            "Meets P1 Essential Indicator on anti-corruption policies; partial compliance "
                            "with NGRBC governance standards but may not satisfy institutional investor "
                            "ESG screening criteria."
                        ),
                    },
                    "no_investment": {
                        "title": "No Investment",
                        "description": "No additional wage or welfare investment this round.",
                        "cost": 0,
                        "impacts": {"social_license_delta": -4},
                        "flags_set": ["brsr_statutory_minimums"],
                        "regulatory_tooltip": (
                            "Heightens governance fragility; compounds vulnerability to SEBI adjudication "
                            "proceedings under Regulation 4(2)(f) of the LODR Regulations, 2015."
                        ),
                    },
                },
            },
            "human_resources": {
                "label": "DEI & Pay Equity",
                "icon": "👥",
                "options": {
                    "dei_dashboard": {
                        "title": "DEI Dashboard & Training",
                        "description": (
                            "Launch a real-time DEI dashboard tracking gender, disability, and "
                            "caste representation. Mandatory unconscious bias training for managers."
                        ),
                        "cost": -1_500_000,
                        "impacts": {"social_license_delta": 5, "reputation": 3},
                        "flags_set": ["brsr_living_wage", "brsr_indicator_leadership"],
                        "regulatory_tooltip": (
                            "Aligns with P3 Leadership Indicators; rectifies statutory EPFO and ESIC "
                            "non-compliance risks among third-party contractual dependencies. Satisfies "
                            "POSH Act, 2013 reporting mandates."
                        ),
                    },
                    "gender_pay_audit": {
                        "title": "Gender Pay Gap Audit",
                        "description": (
                            "Conduct an annual gender pay gap audit and publish results. "
                            "Addresses Essential Indicators for Principle 5."
                        ),
                        "cost": -700_000,
                        "impacts": {"social_license_delta": 2, "reputation": 1},
                        "flags_set": ["brsr_indicator_essential"],
                        "regulatory_tooltip": (
                            "Meets P3 Essential Indicator on employee well-being metrics; addresses basic "
                            "OHS compliance under Factories Act but defers living wage gap analysis."
                        ),
                    },
                    "no_hr_action": {
                        "title": "No HR Action",
                        "description": "No DEI or pay equity investments.",
                        "cost": 0,
                        "impacts": {"social_license_delta": -3},
                        "flags_set": ["brsr_statutory_minimums"],
                        "regulatory_tooltip": (
                            "Heightens vulnerability to P3/P5 non-compliance citations; compounds exposure "
                            "to Section 25FF Industrial Disputes Act consequences and ESI Act penalty "
                            "proceedings."
                        ),
                    },
                },
            },
        },
    },

    # ── Round 3: Environment & Circularity (P6 & P2) ───────────
    3: {
        "title": "Environment & Circularity (P6 & P2)",
        "description": (
            "CPCB flags Pharma discharge. EPR scrutiny for Electronics and Consumer Goods. "
            "Leadership Indicators demand Scope 3 mapping and circular economy initiatives."
        ),
        "areas": {
            "energy": {
                "label": "Water & Discharge",
                "icon": "⚡",
                "options": {
                    "zld_pharma": {
                        "title": "ZLD for Pharma API Plants",
                        "description": (
                            "Deploy Zero Liquid Discharge (ZLD) systems at Hyderabad and Vizag "
                            "Pharma API plants. Eliminates effluent discharge entirely."
                        ),
                        "cost": -3_000_000,
                        "impacts": {"natural_capital_debt_delta": -8, "reputation": 4},
                        "flags_set": ["brsr_circular_symbiosis", "sdg_12_leadership", "brsr_indicator_leadership"],
                        "regulatory_tooltip": (
                            "Satisfies P6 Leadership Indicator; aligns with BRSR Core Attribute 5 "
                            "(Energy intensity per rupee of turnover) and MoEFCC National Clean Air "
                            "Programme reporting mandates."
                        ),
                    },
                    "water_recycling": {
                        "title": "Water Recycling Upgrade",
                        "description": (
                            "Install high-efficiency water recycling to reduce freshwater "
                            "intake by 40%. Meets Essential water disclosure requirements."
                        ),
                        "cost": -1_200_000,
                        "impacts": {"natural_capital_debt_delta": -3, "reputation": 2},
                        "flags_set": ["brsr_indicator_essential"],
                        "regulatory_tooltip": (
                            "Meets P6 Essential Indicator baseline; partial compliance with BRSR Core "
                            "Attribute 5 but may trigger SEBI clarification query on energy intensity "
                            "methodology."
                        ),
                    },
                    "no_change": {
                        "title": "No Change",
                        "description": "Maintain current discharge levels. Risk CPCB penalties.",
                        "cost": 0,
                        "impacts": {"natural_capital_debt_delta": 3, "governance_risk_delta": 3},
                        "flags_set": ["brsr_regulatory_minimum"],
                        "regulatory_tooltip": (
                            "Heightens vulnerability to SEBI Show-Cause interventions; compounds P6 "
                            "non-compliance risks under Rule 34(2)(f) of the Companies Act, 2013."
                        ),
                    },
                },
            },
            "operations": {
                "label": "EPR & Waste Management",
                "icon": "🏭",
                "options": {
                    "epr_full": {
                        "title": "EPR Full Compliance (All BUs)",
                        "description": (
                            "Full Extended Producer Responsibility compliance for Electronics "
                            "(e-waste), Consumer Goods (plastics), and Pharma (hazardous waste)."
                        ),
                        "cost": -2_500_000,
                        "impacts": {"natural_capital_debt_delta": -6, "reputation": 3},
                        "flags_set": ["brsr_circular_symbiosis", "sdg_12_leadership", "brsr_indicator_leadership"],
                        "regulatory_tooltip": (
                            "Fulfills Extended Producer Responsibility (EPR) statutory filing requirements "
                            "under CPCB hazardous waste amendments; satisfies P2 Leadership Indicator on "
                            "product lifecycle stewardship."
                        ),
                    },
                    "basic_waste_segregation": {
                        "title": "Basic Waste Segregation",
                        "description": (
                            "Implement source-segregation and basic recycling across factories. "
                            "Meets Essential waste reporting requirements."
                        ),
                        "cost": -800_000,
                        "impacts": {"natural_capital_debt_delta": -2},
                        "flags_set": ["brsr_indicator_essential"],
                        "regulatory_tooltip": (
                            "Meets P2 Essential Indicator on responsible sourcing; partial compliance with "
                            "EPR registration requirements under Plastic Waste Management Rules, 2016."
                        ),
                    },
                    "no_change": {
                        "title": "No Change",
                        "description": "Continue current waste handling. Risk EPR non-compliance notices.",
                        "cost": 0,
                        "impacts": {"natural_capital_debt_delta": 2, "governance_risk_delta": 2},
                        "flags_set": ["brsr_regulatory_minimum"],
                        "regulatory_tooltip": (
                            "Heightens vulnerability to SPCB closure orders; compounds Section 135 CSR "
                            "shortfall penalties and CPCB consent-to-operate revocation risk."
                        ),
                    },
                },
            },
            "supply_chain": {
                "label": "Circular Economy Partnerships",
                "icon": "🔗",
                "options": {
                    "waste_to_energy_partner": {
                        "title": "Waste-to-Energy Partnership",
                        "description": (
                            "Partner with cement kilns and WtE plants for co-processing of "
                            "industrial waste. Creates circular revenue stream."
                        ),
                        "cost": -1_800_000,
                        "impacts": {"natural_capital_debt_delta": -5, "reputation": 3},
                        "flags_set": ["brsr_circular_symbiosis", "sdg_12_leadership", "brsr_indicator_leadership"],
                        "regulatory_tooltip": (
                            "Ensures BRSR Core readiness; initiates preliminary Top-250 glide path "
                            "reasonable assurance mapping under SEBI Circular "
                            "SEBI/HO/CFD/CMD-2/P/CIR/2023/18."
                        ),
                    },
                    "epr_registration": {
                        "title": "EPR Registration",
                        "description": (
                            "Register with CPCB for EPR obligations and engage PROs "
                            "(Producer Responsibility Organisations) for compliance."
                        ),
                        "cost": -600_000,
                        "impacts": {"natural_capital_debt_delta": -1, "reputation": 1},
                        "flags_set": ["brsr_indicator_essential"],
                        "regulatory_tooltip": (
                            "Meets P4 Essential Indicator on supply chain disclosure; partial compliance "
                            "with BRSR Core but defers reasonable assurance engagement to subsequent "
                            "filing period."
                        ),
                    },
                    "defer": {
                        "title": "Defer",
                        "description": "Postpone circular economy partnerships. Maintain linear model.",
                        "cost": 0,
                        "impacts": {"natural_capital_debt_delta": 2},
                        "flags_set": ["brsr_regulatory_minimum"],
                        "regulatory_tooltip": (
                            "Heightens greenwash exposure; creates material discrepancy between "
                            "self-assessed and third-party validated BRSR Core attributes for value "
                            "chain KPIs."
                        ),
                    },
                },
            },
            "offsetting": {
                "label": "Climate Disclosure",
                "icon": "🌱",
                "options": {
                    "sbti_scope3": {
                        "title": "SBTi Scope 3 Pathway",
                        "description": (
                            "Commit to Science Based Targets initiative with full Scope 3 "
                            "value chain emissions mapping and reduction pathway."
                        ),
                        "cost": -2_500_000,
                        "impacts": {"carbon_intensity_delta": -5, "reputation": 5},
                        "flags_set": ["brsr_circular_symbiosis", "sdg_12_leadership", "brsr_indicator_leadership"],
                        "regulatory_tooltip": (
                            "Mitigates P1 Principle friction; satisfies Clause 4(b) of the updated "
                            "NGRBC mandate regarding independent oversight of lobbying and political "
                            "contribution disclosures."
                        ),
                    },
                    "scope12_reporting": {
                        "title": "Scope 1+2 Reporting",
                        "description": (
                            "Comprehensive Scope 1 and Scope 2 GHG intensity reporting. "
                            "Meets Essential environmental disclosure requirements."
                        ),
                        "cost": -800_000,
                        "impacts": {"carbon_intensity_delta": -2, "reputation": 1},
                        "flags_set": ["brsr_indicator_essential"],
                        "regulatory_tooltip": (
                            "Meets P1 Essential Indicator on anti-corruption policies; partial compliance "
                            "with NGRBC governance standards but may not satisfy institutional investor "
                            "ESG screening criteria."
                        ),
                    },
                    "no_investment": {
                        "title": "No Investment",
                        "description": "Minimal climate disclosure. Risk of greenwash accusations.",
                        "cost": 0,
                        "impacts": {"reputation": -2, "carbon_intensity_delta": 1},
                        "flags_set": ["brsr_regulatory_minimum"],
                        "regulatory_tooltip": (
                            "Heightens governance fragility; compounds vulnerability to SEBI adjudication "
                            "proceedings under Regulation 4(2)(f) of the LODR Regulations, 2015."
                        ),
                    },
                },
            },
            "human_resources": {
                "label": "Green Skills",
                "icon": "👥",
                "options": {
                    "green_skills_academy": {
                        "title": "Green Skills Academy",
                        "description": (
                            "Establish a Green Skills Academy offering certifications in circular "
                            "economy, renewable energy, and environmental management for 500+ employees."
                        ),
                        "cost": -1_500_000,
                        "impacts": {"social_license_delta": 4, "reputation": 3},
                        "flags_set": ["brsr_circular_symbiosis", "brsr_indicator_leadership"],
                        "regulatory_tooltip": (
                            "Aligns with P3 Leadership Indicators; rectifies statutory EPFO and ESIC "
                            "non-compliance risks among third-party contractual dependencies. Satisfies "
                            "POSH Act, 2013 reporting mandates."
                        ),
                    },
                    "basic_ehs_training": {
                        "title": "Basic EHS Training",
                        "description": (
                            "Standard Environment, Health & Safety training modules. "
                            "Meets Essential workforce disclosure requirements."
                        ),
                        "cost": -400_000,
                        "impacts": {"social_license_delta": 1},
                        "flags_set": ["brsr_indicator_essential"],
                        "regulatory_tooltip": (
                            "Meets P3 Essential Indicator on employee well-being metrics; addresses basic "
                            "OHS compliance under Factories Act but defers living wage gap analysis."
                        ),
                    },
                    "no_hr_action": {
                        "title": "No HR Action",
                        "description": "No environmental skilling investment.",
                        "cost": 0,
                        "impacts": {"social_license_delta": -2},
                        "flags_set": ["brsr_regulatory_minimum"],
                        "regulatory_tooltip": (
                            "Heightens vulnerability to P3/P5 non-compliance citations; compounds exposure "
                            "to Section 25FF Industrial Disputes Act consequences and ESI Act penalty "
                            "proceedings."
                        ),
                    },
                },
            },
        },
    },

    # ── Round 4: Value Chain & BRSR Core ────────────────────────
    4: {
        "title": "Value Chain & BRSR Core",
        "description": (
            "SEBI introduces BRSR Core. Top 250 companies face mandatory reasonable "
            "assurance for 9 key attributes. Value chain scrutiny intensifies."
        ),
        "areas": {
            "energy": {
                "label": "Supply Chain Traceability",
                "icon": "⚡",
                "options": {
                    "blockchain_traceability": {
                        "title": "Blockchain Supply Traceability",
                        "description": (
                            "Deploy blockchain-based supply chain traceability across Pharma "
                            "(API sourcing) and Electronics (conflict minerals). Full provenance."
                        ),
                        "cost": -3_000_000,
                        "impacts": {"governance_risk_delta": -6, "reputation": 5},
                        "flags_set": ["brsr_core_assured", "brsr_indicator_leadership"],
                        "regulatory_tooltip": (
                            "Satisfies P6 Leadership Indicator; aligns with BRSR Core Attribute 5 "
                            "(Energy intensity per rupee of turnover) and MoEFCC National Clean Air "
                            "Programme reporting mandates."
                        ),
                    },
                    "tier1_digital_portal": {
                        "title": "Tier-1 Digital Portal",
                        "description": (
                            "Launch a supplier self-service portal for Tier-1 data collection. "
                            "Covers Essential traceability requirements."
                        ),
                        "cost": -1_000_000,
                        "impacts": {"governance_risk_delta": -2, "reputation": 2},
                        "flags_set": ["brsr_indicator_essential"],
                        "regulatory_tooltip": (
                            "Meets P6 Essential Indicator baseline; partial compliance with BRSR Core "
                            "Attribute 5 but may trigger SEBI clarification query on energy intensity "
                            "methodology."
                        ),
                    },
                    "no_change": {
                        "title": "No Change",
                        "description": "Rely on manual supplier data. Risk BRSR Core non-compliance.",
                        "cost": 0,
                        "impacts": {"governance_risk_delta": 4, "reputation": -3},
                        "flags_set": ["brsr_greenwash_risk"],
                        "regulatory_tooltip": (
                            "Heightens vulnerability to SEBI Show-Cause interventions; compounds P6 "
                            "non-compliance risks under Rule 34(2)(f) of the Companies Act, 2013."
                        ),
                    },
                },
            },
            "operations": {
                "label": "Assurance & Verification",
                "icon": "🏭",
                "options": {
                    "big4_reasonable_assurance": {
                        "title": "Big 4 Reasonable Assurance",
                        "description": (
                            "Engage a Big 4 firm for reasonable assurance engagement covering "
                            "all 9 BRSR Core attributes. Gold-standard verification."
                        ),
                        "cost": -2_500_000,
                        "impacts": {"governance_risk_delta": -8, "reputation": 6},
                        "flags_set": ["brsr_core_assured", "brsr_indicator_leadership"],
                        "regulatory_tooltip": (
                            "Fulfills Extended Producer Responsibility (EPR) statutory filing requirements "
                            "under CPCB hazardous waste amendments; satisfies P2 Leadership Indicator on "
                            "product lifecycle stewardship."
                        ),
                    },
                    "limited_assurance": {
                        "title": "Limited Assurance",
                        "description": (
                            "Limited assurance engagement from a mid-tier audit firm. "
                            "Meets minimum SEBI requirements for BRSR Core."
                        ),
                        "cost": -1_200_000,
                        "impacts": {"governance_risk_delta": -3, "reputation": 2},
                        "flags_set": ["brsr_indicator_essential"],
                        "regulatory_tooltip": (
                            "Meets P2 Essential Indicator on responsible sourcing; partial compliance with "
                            "EPR registration requirements under Plastic Waste Management Rules, 2016."
                        ),
                    },
                    "self_assessment": {
                        "title": "Self-Assessment",
                        "description": (
                            "Internal self-assessment with no external verification. "
                            "High risk of SEBI scrutiny and greenwash allegations."
                        ),
                        "cost": -300_000,
                        "impacts": {"governance_risk_delta": 5, "reputation": -4},
                        "flags_set": ["brsr_greenwash_risk"],
                        "regulatory_tooltip": (
                            "Heightens vulnerability to SPCB closure orders; compounds Section 135 CSR "
                            "shortfall penalties and CPCB consent-to-operate revocation risk."
                        ),
                    },
                },
            },
            "supply_chain": {
                "label": "Supplier Development",
                "icon": "🔗",
                "options": {
                    "msme_supplier_dev": {
                        "title": "MSME Supplier Development",
                        "description": (
                            "Launch a structured MSME supplier development program covering ESG "
                            "capacity building, digital readiness, and financial inclusion."
                        ),
                        "cost": -2_000_000,
                        "impacts": {"social_license_delta": 5, "reputation": 4},
                        "flags_set": ["brsr_core_assured", "brsr_indicator_leadership"],
                        "regulatory_tooltip": (
                            "Ensures BRSR Core readiness; initiates preliminary Top-250 glide path "
                            "reasonable assurance mapping under SEBI Circular "
                            "SEBI/HO/CFD/CMD-2/P/CIR/2023/18."
                        ),
                    },
                    "annual_supplier_audit": {
                        "title": "Annual Supplier Audit",
                        "description": (
                            "Conduct annual ESG audits of top 30 suppliers. "
                            "Essential compliance for value chain disclosures."
                        ),
                        "cost": -800_000,
                        "impacts": {"reputation": 2},
                        "flags_set": ["brsr_indicator_essential"],
                        "regulatory_tooltip": (
                            "Meets P4 Essential Indicator on supply chain disclosure; partial compliance "
                            "with BRSR Core but defers reasonable assurance engagement to subsequent "
                            "filing period."
                        ),
                    },
                    "defer": {
                        "title": "Defer",
                        "description": "No supplier development investment. Risk Tier-2 supply chain incidents.",
                        "cost": 0,
                        "impacts": {"reputation": -2, "governance_risk_delta": 3},
                        "flags_set": ["brsr_greenwash_risk"],
                        "regulatory_tooltip": (
                            "Heightens greenwash exposure; creates material discrepancy between "
                            "self-assessed and third-party validated BRSR Core attributes for value "
                            "chain KPIs."
                        ),
                    },
                },
            },
            "offsetting": {
                "label": "Consumer & Stakeholder Engagement",
                "icon": "🌱",
                "options": {
                    "consumer_grievance_analytics": {
                        "title": "Consumer Grievance Analytics",
                        "description": (
                            "Deploy AI-powered consumer grievance analytics with real-time "
                            "dashboards, NPS tracking, and product safety incident reporting."
                        ),
                        "cost": -1_800_000,
                        "impacts": {"reputation": 5, "social_license_delta": 3},
                        "flags_set": ["brsr_core_assured", "brsr_indicator_leadership"],
                        "regulatory_tooltip": (
                            "Mitigates P1 Principle friction; satisfies Clause 4(b) of the updated "
                            "NGRBC mandate regarding independent oversight of lobbying and political "
                            "contribution disclosures."
                        ),
                    },
                    "csr_documentation": {
                        "title": "CSR Spend Documentation",
                        "description": (
                            "Comprehensive documentation of Section 135 CSR spend with "
                            "impact metrics. Meets Essential disclosure expectations."
                        ),
                        "cost": -500_000,
                        "impacts": {"reputation": 1},
                        "flags_set": ["brsr_indicator_essential"],
                        "regulatory_tooltip": (
                            "Meets P1 Essential Indicator on anti-corruption policies; partial compliance "
                            "with NGRBC governance standards but may not satisfy institutional investor "
                            "ESG screening criteria."
                        ),
                    },
                    "no_investment": {
                        "title": "No Investment",
                        "description": "Minimal stakeholder engagement documentation.",
                        "cost": 0,
                        "impacts": {"reputation": -2},
                        "flags_set": ["brsr_greenwash_risk"],
                        "regulatory_tooltip": (
                            "Heightens governance fragility; compounds vulnerability to SEBI adjudication "
                            "proceedings under Regulation 4(2)(f) of the LODR Regulations, 2015."
                        ),
                    },
                },
            },
            "human_resources": {
                "label": "Supplier ESG Capacity",
                "icon": "👥",
                "options": {
                    "supplier_esg_training": {
                        "title": "Supplier ESG Training Program",
                        "description": (
                            "Design and deliver a structured ESG training program for 200+ "
                            "supplier factory managers covering BRSR Core requirements."
                        ),
                        "cost": -1_500_000,
                        "impacts": {"social_license_delta": 3, "reputation": 3},
                        "flags_set": ["brsr_core_assured", "brsr_indicator_leadership"],
                        "regulatory_tooltip": (
                            "Aligns with P3 Leadership Indicators; rectifies statutory EPFO and ESIC "
                            "non-compliance risks among third-party contractual dependencies. Satisfies "
                            "POSH Act, 2013 reporting mandates."
                        ),
                    },
                    "basic_awareness": {
                        "title": "Basic Awareness Session",
                        "description": (
                            "One-time awareness sessions on BRSR expectations for key suppliers. "
                            "Covers Essential requirements."
                        ),
                        "cost": -400_000,
                        "impacts": {"reputation": 1},
                        "flags_set": ["brsr_indicator_essential"],
                        "regulatory_tooltip": (
                            "Meets P3 Essential Indicator on employee well-being metrics; addresses basic "
                            "OHS compliance under Factories Act but defers living wage gap analysis."
                        ),
                    },
                    "no_hr_action": {
                        "title": "No HR Action",
                        "description": "No supplier capacity building investment.",
                        "cost": 0,
                        "impacts": {},
                        "flags_set": ["brsr_greenwash_risk"],
                        "regulatory_tooltip": (
                            "Heightens vulnerability to P3/P5 non-compliance citations; compounds exposure "
                            "to Section 25FF Industrial Disputes Act consequences and ESI Act penalty "
                            "proceedings."
                        ),
                    },
                },
            },
        },
    },

    # ── Round 5: Integrated Disclosure & ESG Alpha ──────────────
    5: {
        "title": "Integrated Disclosure & ESG Alpha",
        "description": (
            "FY-end filing deadline. The Board demands the final BRSR submission. "
            "Investor Relations must present the ESG narrative to CRISIL and Sustainalytics."
        ),
        "areas": {
            "energy": {
                "label": "Integrated Reporting",
                "icon": "⚡",
                "options": {
                    "six_capitals_report": {
                        "title": "Six Capitals Integrated Report",
                        "description": (
                            "Publish a full IIRC Six Capitals integrated report linking financial, "
                            "manufactured, intellectual, human, social, and natural capital performance."
                        ),
                        "cost": -2_500_000,
                        "impacts": {"reputation": 8},
                        "flags_set": ["brsr_integrated_report", "brsr_indicator_leadership"],
                        "regulatory_tooltip": (
                            "Satisfies P6 Leadership Indicator; aligns with BRSR Core Attribute 5 "
                            "(Energy intensity per rupee of turnover) and MoEFCC National Clean Air "
                            "Programme reporting mandates."
                        ),
                    },
                    "strategic_kpis": {
                        "title": "Strategic BRSR KPIs",
                        "description": (
                            "Structured BRSR filing with strategic KPIs linked to business "
                            "performance. Exceeds Essential, partially addresses Leadership."
                        ),
                        "cost": -1_000_000,
                        "impacts": {"reputation": 3},
                        "flags_set": ["brsr_indicator_essential"],
                        "regulatory_tooltip": (
                            "Meets P6 Essential Indicator baseline; partial compliance with BRSR Core "
                            "Attribute 5 but may trigger SEBI clarification query on energy intensity "
                            "methodology."
                        ),
                    },
                    "minimal_filing": {
                        "title": "Minimal Filing",
                        "description": "Bare-minimum statutory BRSR filing with no strategic narrative.",
                        "cost": -200_000,
                        "impacts": {"reputation": -2},
                        "flags_set": ["brsr_compliance_only"],
                        "regulatory_tooltip": (
                            "Heightens vulnerability to SEBI Show-Cause interventions; compounds P6 "
                            "non-compliance risks under Rule 34(2)(f) of the Companies Act, 2013."
                        ),
                    },
                },
            },
            "operations": {
                "label": "ESG-Financial Connectivity",
                "icon": "🏭",
                "options": {
                    "esg_financial_dashboard": {
                        "title": "ESG-Financial Connectivity Dashboard",
                        "description": (
                            "Build an interactive dashboard linking ESG metrics to financial "
                            "outcomes — carbon cost per unit revenue, social ROI, etc."
                        ),
                        "cost": -2_000_000,
                        "impacts": {"reputation": 6, "governance_risk_delta": -3},
                        "flags_set": ["brsr_integrated_report", "brsr_indicator_leadership"],
                        "regulatory_tooltip": (
                            "Fulfills Extended Producer Responsibility (EPR) statutory filing requirements "
                            "under CPCB hazardous waste amendments; satisfies P2 Leadership Indicator on "
                            "product lifecycle stewardship."
                        ),
                    },
                    "sector_benchmarking": {
                        "title": "Sector Benchmarking",
                        "description": (
                            "Commission a sector benchmarking report comparing Muressons "
                            "BRSR performance against peer conglomerates."
                        ),
                        "cost": -800_000,
                        "impacts": {"reputation": 2},
                        "flags_set": ["brsr_indicator_essential"],
                        "regulatory_tooltip": (
                            "Meets P2 Essential Indicator on responsible sourcing; partial compliance with "
                            "EPR registration requirements under Plastic Waste Management Rules, 2016."
                        ),
                    },
                    "no_change": {
                        "title": "No Change",
                        "description": "No ESG-financial integration. File standalone reports.",
                        "cost": 0,
                        "impacts": {"reputation": -1},
                        "flags_set": ["brsr_compliance_only"],
                        "regulatory_tooltip": (
                            "Heightens vulnerability to SPCB closure orders; compounds Section 135 CSR "
                            "shortfall penalties and CPCB consent-to-operate revocation risk."
                        ),
                    },
                },
            },
            "supply_chain": {
                "label": "Disclosure Cross-References",
                "icon": "🔗",
                "options": {
                    "gri_tcfd_mapping": {
                        "title": "GRI/TCFD Cross-Reference Mapping",
                        "description": (
                            "Full cross-reference mapping between BRSR, GRI Standards, and "
                            "TCFD recommendations. Investor-grade disclosure alignment."
                        ),
                        "cost": -1_500_000,
                        "impacts": {"reputation": 5, "governance_risk_delta": -2},
                        "flags_set": ["brsr_integrated_report", "brsr_indicator_leadership"],
                        "regulatory_tooltip": (
                            "Ensures BRSR Core readiness; initiates preliminary Top-250 glide path "
                            "reasonable assurance mapping under SEBI Circular "
                            "SEBI/HO/CFD/CMD-2/P/CIR/2023/18."
                        ),
                    },
                    "basic_gri_index": {
                        "title": "Basic GRI Index",
                        "description": (
                            "Publish a basic GRI Content Index alongside BRSR filing. "
                            "Partial cross-reference for ESG-aware investors."
                        ),
                        "cost": -500_000,
                        "impacts": {"reputation": 1},
                        "flags_set": ["brsr_indicator_essential"],
                        "regulatory_tooltip": (
                            "Meets P4 Essential Indicator on supply chain disclosure; partial compliance "
                            "with BRSR Core but defers reasonable assurance engagement to subsequent "
                            "filing period."
                        ),
                    },
                    "defer": {
                        "title": "Defer",
                        "description": "No disclosure cross-referencing. BRSR filed in isolation.",
                        "cost": 0,
                        "impacts": {"reputation": -1},
                        "flags_set": ["brsr_compliance_only"],
                        "regulatory_tooltip": (
                            "Heightens greenwash exposure; creates material discrepancy between "
                            "self-assessed and third-party validated BRSR Core attributes for value "
                            "chain KPIs."
                        ),
                    },
                },
            },
            "offsetting": {
                "label": "Materiality Validation",
                "icon": "🌱",
                "options": {
                    "third_party_materiality": {
                        "title": "Third-Party Materiality Validation",
                        "description": (
                            "Engage an independent advisory firm for double-materiality assessment "
                            "with stakeholder consultation covering 500+ stakeholders."
                        ),
                        "cost": -2_000_000,
                        "impacts": {"reputation": 5, "governance_risk_delta": -3},
                        "flags_set": ["brsr_integrated_report", "brsr_indicator_leadership"],
                        "regulatory_tooltip": (
                            "Mitigates P1 Principle friction; satisfies Clause 4(b) of the updated "
                            "NGRBC mandate regarding independent oversight of lobbying and political "
                            "contribution disclosures."
                        ),
                    },
                    "internal_materiality": {
                        "title": "Internal Materiality Matrix",
                        "description": (
                            "Conduct an internal materiality assessment with management input. "
                            "Meets Essential materiality disclosure requirements."
                        ),
                        "cost": -600_000,
                        "impacts": {"reputation": 1},
                        "flags_set": ["brsr_indicator_essential"],
                        "regulatory_tooltip": (
                            "Meets P1 Essential Indicator on anti-corruption policies; partial compliance "
                            "with NGRBC governance standards but may not satisfy institutional investor "
                            "ESG screening criteria."
                        ),
                    },
                    "no_investment": {
                        "title": "No Investment",
                        "description": "No materiality assessment. File BRSR without materiality context.",
                        "cost": 0,
                        "impacts": {"reputation": -2},
                        "flags_set": ["brsr_compliance_only"],
                        "regulatory_tooltip": (
                            "Heightens governance fragility; compounds vulnerability to SEBI adjudication "
                            "proceedings under Regulation 4(2)(f) of the LODR Regulations, 2015."
                        ),
                    },
                },
            },
            "human_resources": {
                "label": "Investor Communication",
                "icon": "👥",
                "options": {
                    "analyst_ir_pack": {
                        "title": "Analyst & IR ESG Pack",
                        "description": (
                            "Produce a comprehensive ESG data pack for sell-side analysts and "
                            "investor relations — includes ESG scores, trend data, and peer comparison."
                        ),
                        "cost": -1_200_000,
                        "impacts": {"reputation": 4},
                        "flags_set": ["brsr_integrated_report", "brsr_indicator_leadership"],
                        "regulatory_tooltip": (
                            "Aligns with P3 Leadership Indicators; rectifies statutory EPFO and ESIC "
                            "non-compliance risks among third-party contractual dependencies. Satisfies "
                            "POSH Act, 2013 reporting mandates."
                        ),
                    },
                    "board_summary": {
                        "title": "Board Summary",
                        "description": (
                            "Prepare a board-level ESG summary for investor meetings. "
                            "Essential-level investor communication."
                        ),
                        "cost": -400_000,
                        "impacts": {"reputation": 1},
                        "flags_set": ["brsr_indicator_essential"],
                        "regulatory_tooltip": (
                            "Meets P3 Essential Indicator on employee well-being metrics; addresses basic "
                            "OHS compliance under Factories Act but defers living wage gap analysis."
                        ),
                    },
                    "no_hr_action": {
                        "title": "No HR Action",
                        "description": "No dedicated investor ESG communication.",
                        "cost": 0,
                        "impacts": {"reputation": -1},
                        "flags_set": ["brsr_compliance_only"],
                        "regulatory_tooltip": (
                            "Heightens vulnerability to P3/P5 non-compliance citations; compounds exposure "
                            "to Section 25FF Industrial Disputes Act consequences and ESI Act penalty "
                            "proceedings."
                        ),
                    },
                },
            },
        },
    },

    # ── Round 6: Human Rights Realities (P5) ─────────────────────
    6: {
        "title": "Human Rights Realities (P5)",
        "description": (
            "A media investigation exposes human rights violations in Tier-2 suppliers. "
            "Deploy deep due diligence or risk reputational and regulatory fallout."
        ),
        "areas": {
            "energy": {
                "label": "HRDD Tier-2 Traceability",
                "icon": "⚡",
                "options": {
                    "digital_traceability": {
                        "title": "Digital Traceability Platform",
                        "description": (
                            "Deploy blockchain-backed digital traceability across Tier-2 component "
                            "manufacturers with real-time labor condition monitoring."
                        ),
                        "cost": -2_000_000,
                        "impacts": {"governance_risk_delta": -3, "reputation": 5},
                        "flags_set": ["deep_hrdd_active", "brsr_indicator_leadership"],
                        "regulatory_tooltip": (
                            "Satisfies P6 Leadership Indicator; aligns with BRSR Core Attribute 5 "
                            "(Energy intensity per rupee of turnover) and MoEFCC National Clean Air "
                            "Programme reporting mandates."
                        ),
                    },
                    "vendor_portal_expansion": {
                        "title": "Vendor Portal Expansion",
                        "description": (
                            "Expand existing vendor compliance portal with self-declaration modules "
                            "and annual sample audit scheduling."
                        ),
                        "cost": -800_000,
                        "impacts": {"governance_risk_delta": -1, "reputation": 2},
                        "flags_set": ["brsr_indicator_essential"],
                        "regulatory_tooltip": (
                            "Meets P6 Essential Indicator baseline; partial compliance with BRSR Core "
                            "Attribute 5 but may trigger SEBI clarification query on energy intensity "
                            "methodology."
                        ),
                    },
                    "desk_audits_only": {
                        "title": "Desk Audits Only",
                        "description": "Rely on vendor self-attestation letters. No system changes.",
                        "cost": 0,
                        "impacts": {"governance_risk_delta": 3, "reputation": -3},
                        "flags_set": ["tier2_human_rights_risk"],
                        "regulatory_tooltip": (
                            "Heightens vulnerability to SEBI Show-Cause interventions; compounds P6 "
                            "non-compliance risks under Rule 34(2)(f) of the Companies Act, 2013."
                        ),
                    },
                },
            },
            "operations": {
                "label": "Child Labor Remediation",
                "icon": "🏭",
                "options": {
                    "ngo_partnership_remediation": {
                        "title": "NGO Partnership Remediation",
                        "description": (
                            "Partner with child rights NGOs for systematic remediation, rehabilitation "
                            "programs, and community education investments."
                        ),
                        "cost": -1_500_000,
                        "impacts": {"reputation": 4, "governance_risk_delta": -2},
                        "flags_set": ["deep_hrdd_active", "brsr_indicator_leadership"],
                        "regulatory_tooltip": (
                            "Fulfills Extended Producer Responsibility (EPR) statutory filing requirements "
                            "under CPCB hazardous waste amendments; satisfies P2 Leadership Indicator on "
                            "product lifecycle stewardship."
                        ),
                    },
                    "internal_compliance_team": {
                        "title": "Internal Compliance Team",
                        "description": "Assign internal compliance officers for periodic unannounced spot checks.",
                        "cost": -600_000,
                        "impacts": {"reputation": 1, "governance_risk_delta": -1},
                        "flags_set": ["brsr_indicator_essential"],
                        "regulatory_tooltip": (
                            "Meets P2 Essential Indicator on responsible sourcing; partial compliance with "
                            "EPR registration requirements under Plastic Waste Management Rules, 2016."
                        ),
                    },
                    "no_remediation": {
                        "title": "No Remediation",
                        "description": "Issue public statement only. No operational remediation programs.",
                        "cost": 0,
                        "impacts": {"reputation": -4, "governance_risk_delta": 2},
                        "flags_set": ["tier2_human_rights_risk"],
                        "regulatory_tooltip": (
                            "Heightens vulnerability to SPCB closure orders; compounds Section 135 CSR "
                            "shortfall penalties and CPCB consent-to-operate revocation risk."
                        ),
                    },
                },
            },
            "supply_chain": {
                "label": "Contractual Enforcement",
                "icon": "🔗",
                "options": {
                    "strict_contractual_clauses": {
                        "title": "Strict Contractual Clauses",
                        "description": (
                            "Insert human rights clauses with automatic termination triggers "
                            "into all Tier-1 and Tier-2 supplier contracts."
                        ),
                        "cost": -1_200_000,
                        "impacts": {"governance_risk_delta": -2, "reputation": 3},
                        "flags_set": ["deep_hrdd_active", "brsr_indicator_leadership"],
                        "regulatory_tooltip": (
                            "Ensures BRSR Core readiness; initiates preliminary Top-250 glide path "
                            "reasonable assurance mapping under SEBI Circular "
                            "SEBI/HO/CFD/CMD-2/P/CIR/2023/18."
                        ),
                    },
                    "tier1_contractual_review": {
                        "title": "Tier-1 Contractual Review",
                        "description": "Add basic human rights acknowledgment clauses to Tier-1 contracts only.",
                        "cost": -400_000,
                        "impacts": {"governance_risk_delta": -1, "reputation": 1},
                        "flags_set": ["brsr_indicator_essential"],
                        "regulatory_tooltip": (
                            "Meets P4 Essential Indicator on supply chain disclosure; partial compliance "
                            "with BRSR Core but defers reasonable assurance engagement to subsequent "
                            "filing period."
                        ),
                    },
                    "no_contract_changes": {
                        "title": "No Contract Changes",
                        "description": "Maintain existing commercial terms without human rights provisions.",
                        "cost": 0,
                        "impacts": {"reputation": -2},
                        "flags_set": ["tier2_human_rights_risk"],
                        "regulatory_tooltip": (
                            "Heightens greenwash exposure; creates material discrepancy between "
                            "self-assessed and third-party validated BRSR Core attributes for value "
                            "chain KPIs."
                        ),
                    },
                },
            },
            "offsetting": {
                "label": "Independent Auditing",
                "icon": "🌿",
                "options": {
                    "independent_unannounced_audits": {
                        "title": "Independent Unannounced Audits",
                        "description": (
                            "Commission independent third-party auditors for unannounced factory "
                            "inspections across all manufacturing tiers."
                        ),
                        "cost": -1_000_000,
                        "impacts": {"governance_risk_delta": -2, "reputation": 3},
                        "flags_set": ["deep_hrdd_active", "brsr_indicator_leadership"],
                        "regulatory_tooltip": (
                            "Mitigates P1 Principle friction; satisfies Clause 4(b) of the updated "
                            "NGRBC mandate regarding independent oversight of lobbying and political "
                            "contribution disclosures."
                        ),
                    },
                    "scheduled_annual_audits": {
                        "title": "Scheduled Annual Audits",
                        "description": "Conduct scheduled annual compliance audits with advance notification.",
                        "cost": -400_000,
                        "impacts": {"governance_risk_delta": -1, "reputation": 1},
                        "flags_set": ["brsr_indicator_essential"],
                        "regulatory_tooltip": (
                            "Meets P1 Essential Indicator on anti-corruption policies; partial compliance "
                            "with NGRBC governance standards but may not satisfy institutional investor "
                            "ESG screening criteria."
                        ),
                    },
                    "no_auditing": {
                        "title": "No Auditing",
                        "description": "No external auditing program. Rely on vendor self-reports.",
                        "cost": 0,
                        "impacts": {"reputation": -2},
                        "flags_set": ["tier2_human_rights_risk"],
                        "regulatory_tooltip": (
                            "Heightens governance fragility; compounds vulnerability to SEBI adjudication "
                            "proceedings under Regulation 4(2)(f) of the LODR Regulations, 2015."
                        ),
                    },
                },
            },
            "human_resources": {
                "label": "Vendor ESG Capacity Building",
                "icon": "👥",
                "options": {
                    "vendor_esg_overhaul": {
                        "title": "Vendor ESG Capacity Overhaul",
                        "description": (
                            "Launch comprehensive vendor ESG capability programs including training, "
                            "certification, and financial support for compliance upgrades."
                        ),
                        "cost": -1_500_000,
                        "impacts": {"reputation": 3, "governance_risk_delta": -1},
                        "flags_set": ["deep_hrdd_active", "brsr_indicator_leadership"],
                        "regulatory_tooltip": (
                            "Aligns with P3 Leadership Indicators; rectifies statutory EPFO and ESIC "
                            "non-compliance risks among third-party contractual dependencies. Satisfies "
                            "POSH Act, 2013 reporting mandates."
                        ),
                    },
                    "basic_vendor_training": {
                        "title": "Basic Vendor Training",
                        "description": "Provide basic online ESG awareness training modules to Tier-1 vendors.",
                        "cost": -300_000,
                        "impacts": {"reputation": 1},
                        "flags_set": ["brsr_indicator_essential"],
                        "regulatory_tooltip": (
                            "Meets P3 Essential Indicator on employee well-being metrics; addresses basic "
                            "OHS compliance under Factories Act but defers living wage gap analysis."
                        ),
                    },
                    "no_vendor_capacity": {
                        "title": "No Vendor Capacity Building",
                        "description": "No investment in vendor ESG capacity. Vendors manage independently.",
                        "cost": 0,
                        "impacts": {"reputation": -1},
                        "flags_set": ["tier2_human_rights_risk"],
                        "regulatory_tooltip": (
                            "Heightens vulnerability to P3/P5 non-compliance citations; compounds exposure "
                            "to Section 25FF Industrial Disputes Act consequences and ESI Act penalty "
                            "proceedings."
                        ),
                    },
                },
            },
        },
    },

    # ── Round 7: Policy Advocacy & Ethical Frameworks (P7) ────────
    7: {
        "title": "Policy Advocacy & Ethical Frameworks (P7)",
        "description": (
            "A trade association lobbies to dilute carbon taxes. Take a public progressive "
            "stance or align with the industry cartel."
        ),
        "areas": {
            "energy": {
                "label": "Corporate Policy Stance",
                "icon": "⚡",
                "options": {
                    "independent_position_papers": {
                        "title": "Independent Position Papers",
                        "description": (
                            "Publish pro-climate independent position papers and withdraw from "
                            "carbon-regressive trade associations."
                        ),
                        "cost": -1_200_000,
                        "impacts": {"reputation": 6, "governance_risk_delta": -2},
                        "flags_set": ["policy_leadership", "brsr_indicator_leadership"],
                        "regulatory_tooltip": (
                            "Satisfies P6 Leadership Indicator; aligns with BRSR Core Attribute 5 "
                            "(Energy intensity per rupee of turnover) and MoEFCC National Clean Air "
                            "Programme reporting mandates."
                        ),
                    },
                    "internal_dissent_letters": {
                        "title": "Internal Dissent Letters",
                        "description": "Submit internal dissent letters without public positioning.",
                        "cost": -400_000,
                        "impacts": {"reputation": 1, "governance_risk_delta": -1},
                        "flags_set": ["brsr_indicator_essential"],
                        "regulatory_tooltip": (
                            "Meets P6 Essential Indicator baseline; partial compliance with BRSR Core "
                            "Attribute 5 but may trigger SEBI clarification query on energy intensity "
                            "methodology."
                        ),
                    },
                    "sign_cartel_memo": {
                        "title": "Sign Cartel Memo",
                        "description": "Sign the joint industry lobby memorandum supporting carbon tax dilution.",
                        "cost": 0,
                        "impacts": {"reputation": -3, "governance_risk_delta": 2},
                        "flags_set": ["greenwash_advocacy"],
                        "regulatory_tooltip": (
                            "Heightens vulnerability to SEBI Show-Cause interventions; compounds P6 "
                            "non-compliance risks under Rule 34(2)(f) of the Companies Act, 2013."
                        ),
                    },
                },
            },
            "operations": {
                "label": "Advocacy Protocol Transparency",
                "icon": "🏭",
                "options": {
                    "transparent_advocacy_protocols": {
                        "title": "Transparent Advocacy Protocols",
                        "description": (
                            "Establish publicly accessible advocacy protocols with annual "
                            "disclosure of all lobbying expenditures and positions."
                        ),
                        "cost": -800_000,
                        "impacts": {"reputation": 4, "governance_risk_delta": -1},
                        "flags_set": ["policy_leadership", "brsr_indicator_leadership"],
                        "regulatory_tooltip": (
                            "Fulfills Extended Producer Responsibility (EPR) statutory filing requirements "
                            "under CPCB hazardous waste amendments; satisfies P2 Leadership Indicator on "
                            "product lifecycle stewardship."
                        ),
                    },
                    "restrained_policy_papers": {
                        "title": "Restrained Policy Papers",
                        "description": "Draft measured policy papers for internal governance records only.",
                        "cost": -300_000,
                        "impacts": {"reputation": 1},
                        "flags_set": ["brsr_indicator_essential"],
                        "regulatory_tooltip": (
                            "Meets P2 Essential Indicator on responsible sourcing; partial compliance with "
                            "EPR registration requirements under Plastic Waste Management Rules, 2016."
                        ),
                    },
                    "suppress_lobbying_metrics": {
                        "title": "Suppress Lobbying Metrics",
                        "description": "Suppress group lobbying expenditure data from public disclosures.",
                        "cost": 0,
                        "impacts": {"reputation": -2, "governance_risk_delta": 2},
                        "flags_set": ["greenwash_advocacy"],
                        "regulatory_tooltip": (
                            "Heightens vulnerability to SPCB closure orders; compounds Section 135 CSR "
                            "shortfall penalties and CPCB consent-to-operate revocation risk."
                        ),
                    },
                },
            },
            "supply_chain": {
                "label": "Trade Association Ethics",
                "icon": "🔗",
                "options": {
                    "withdraw_regressive_associations": {
                        "title": "Withdraw from Regressive Associations",
                        "description": (
                            "Formally withdraw from trade associations with anti-climate policy "
                            "positions and publish rationale."
                        ),
                        "cost": -500_000,
                        "impacts": {"reputation": 3, "governance_risk_delta": -1},
                        "flags_set": ["policy_leadership", "brsr_indicator_leadership"],
                        "regulatory_tooltip": (
                            "Ensures BRSR Core readiness; initiates preliminary Top-250 glide path "
                            "reasonable assurance mapping under SEBI Circular "
                            "SEBI/HO/CFD/CMD-2/P/CIR/2023/18."
                        ),
                    },
                    "standard_governance_disclosures": {
                        "title": "Standard Governance Disclosures",
                        "description": "Include standard governance disclosures about trade body memberships.",
                        "cost": -200_000,
                        "impacts": {"reputation": 1},
                        "flags_set": ["brsr_indicator_essential"],
                        "regulatory_tooltip": (
                            "Meets P4 Essential Indicator on supply chain disclosure; partial compliance "
                            "with BRSR Core but defers reasonable assurance engagement to subsequent "
                            "filing period."
                        ),
                    },
                    "silent_policy_compliance": {
                        "title": "Silent Policy Compliance",
                        "description": "Maintain all existing trade body affiliations without review.",
                        "cost": 0,
                        "impacts": {"reputation": -1, "governance_risk_delta": 1},
                        "flags_set": ["greenwash_advocacy"],
                        "regulatory_tooltip": (
                            "Heightens greenwash exposure; creates material discrepancy between "
                            "self-assessed and third-party validated BRSR Core attributes for value "
                            "chain KPIs."
                        ),
                    },
                },
            },
            "offsetting": {
                "label": "Sustainability Endowments",
                "icon": "🌿",
                "options": {
                    "endow_sustainability_chairs": {
                        "title": "Endow Sustainability Chairs",
                        "description": (
                            "Endow academic sustainability chairs and research programs "
                            "at leading Indian universities."
                        ),
                        "cost": -800_000,
                        "impacts": {"reputation": 3, "governance_risk_delta": -1},
                        "flags_set": ["policy_leadership", "brsr_indicator_leadership"],
                        "regulatory_tooltip": (
                            "Mitigates P1 Principle friction; satisfies Clause 4(b) of the updated "
                            "NGRBC mandate regarding independent oversight of lobbying and political "
                            "contribution disclosures."
                        ),
                    },
                    "sponsor_industry_forums": {
                        "title": "Sponsor Industry Forums",
                        "description": "Sponsor periodic ESG industry forums and webinars.",
                        "cost": -200_000,
                        "impacts": {"reputation": 1},
                        "flags_set": ["brsr_indicator_essential"],
                        "regulatory_tooltip": (
                            "Meets P1 Essential Indicator on anti-corruption policies; partial compliance "
                            "with NGRBC governance standards but may not satisfy institutional investor "
                            "ESG screening criteria."
                        ),
                    },
                    "no_endowments": {
                        "title": "No Endowments",
                        "description": "No academic or research engagement on sustainability topics.",
                        "cost": 0,
                        "impacts": {"reputation": -1},
                        "flags_set": ["greenwash_advocacy"],
                        "regulatory_tooltip": (
                            "Heightens governance fragility; compounds vulnerability to SEBI adjudication "
                            "proceedings under Regulation 4(2)(f) of the LODR Regulations, 2015."
                        ),
                    },
                },
            },
            "human_resources": {
                "label": "Corporate Integrity Officers",
                "icon": "👥",
                "options": {
                    "deploy_integrity_officers": {
                        "title": "Deploy Corporate Integrity Officers",
                        "description": (
                            "Deploy dedicated corporate integrity officers across all BUs with "
                            "direct Board reporting lines."
                        ),
                        "cost": -1_000_000,
                        "impacts": {"reputation": 2, "governance_risk_delta": -2},
                        "flags_set": ["policy_leadership", "brsr_indicator_leadership"],
                        "regulatory_tooltip": (
                            "Aligns with P3 Leadership Indicators; rectifies statutory EPFO and ESIC "
                            "non-compliance risks among third-party contractual dependencies. Satisfies "
                            "POSH Act, 2013 reporting mandates."
                        ),
                    },
                    "ethics_training_rollout": {
                        "title": "Ethics Training Rollout",
                        "description": "Roll out annual ethics and integrity training across management.",
                        "cost": -300_000,
                        "impacts": {"reputation": 1, "governance_risk_delta": -1},
                        "flags_set": ["brsr_indicator_essential"],
                        "regulatory_tooltip": (
                            "Meets P3 Essential Indicator on employee well-being metrics; addresses basic "
                            "OHS compliance under Factories Act but defers living wage gap analysis."
                        ),
                    },
                    "no_integrity_officers": {
                        "title": "No Integrity Officers",
                        "description": "No dedicated integrity function. Existing compliance team handles issues.",
                        "cost": 0,
                        "impacts": {"reputation": -1},
                        "flags_set": ["greenwash_advocacy"],
                        "regulatory_tooltip": (
                            "Heightens vulnerability to P3/P5 non-compliance citations; compounds exposure "
                            "to Section 25FF Industrial Disputes Act consequences and ESI Act penalty "
                            "proceedings."
                        ),
                    },
                },
            },
        },
    },

    # ── Round 8: Inclusive Micro-Growth & Vendor Protection (P8) ──
    8: {
        "title": "Inclusive Micro-Growth & Vendor Protection (P8)",
        "description": (
            "SEBI tightens MSME payment monitoring. Formalize vendor relationships "
            "or risk regulatory penalties and vendor business continuity failures."
        ),
        "areas": {
            "energy": {
                "label": "TReDS Platform Integration",
                "icon": "⚡",
                "options": {
                    "full_treds_integration": {
                        "title": "Full TReDS Integration",
                        "description": (
                            "Immediate integration with Trade Receivables Discounting System (TReDS) "
                            "for automated MSME invoice discounting and instant settlements."
                        ),
                        "cost": -2_000_000,
                        "impacts": {"governance_risk_delta": -3, "reputation": 4},
                        "flags_set": ["msme_champion", "brsr_indicator_leadership"],
                        "regulatory_tooltip": (
                            "Satisfies P6 Leadership Indicator; aligns with BRSR Core Attribute 5 "
                            "(Energy intensity per rupee of turnover) and MoEFCC National Clean Air "
                            "Programme reporting mandates."
                        ),
                    },
                    "manual_accelerated_payments": {
                        "title": "Manual Accelerated Payments",
                        "description": "Set up manual accelerated payment tracks for critical MSME vendors.",
                        "cost": -800_000,
                        "impacts": {"governance_risk_delta": -1, "reputation": 2},
                        "flags_set": ["brsr_indicator_essential"],
                        "regulatory_tooltip": (
                            "Meets P6 Essential Indicator baseline; partial compliance with BRSR Core "
                            "Attribute 5 but may trigger SEBI clarification query on energy intensity "
                            "methodology."
                        ),
                    },
                    "maintain_90day_credit": {
                        "title": "Maintain 90-Day Credit",
                        "description": "Maintain existing 90-day credit cycle. No payment acceleration.",
                        "cost": 0,
                        "impacts": {"reputation": -4, "governance_risk_delta": 3},
                        "flags_set": ["working_capital_hoarder"],
                        "regulatory_tooltip": (
                            "Heightens vulnerability to SEBI Show-Cause interventions; compounds P6 "
                            "non-compliance risks under Rule 34(2)(f) of the Companies Act, 2013."
                        ),
                    },
                },
            },
            "operations": {
                "label": "MSME Development Programs",
                "icon": "🏭",
                "options": {
                    "formal_msme_development": {
                        "title": "Formal MSME Development",
                        "description": (
                            "Launch formal MSME operational development programs with technical "
                            "assistance, quality systems training, and business planning support."
                        ),
                        "cost": -1_200_000,
                        "impacts": {"reputation": 3, "governance_risk_delta": -1},
                        "flags_set": ["msme_champion", "brsr_indicator_leadership"],
                        "regulatory_tooltip": (
                            "Fulfills Extended Producer Responsibility (EPR) statutory filing requirements "
                            "under CPCB hazardous waste amendments; satisfies P2 Leadership Indicator on "
                            "product lifecycle stewardship."
                        ),
                    },
                    "periodic_vendor_seminars": {
                        "title": "Periodic Vendor Seminars",
                        "description": "Organize periodic vendor technical seminars and knowledge sharing.",
                        "cost": -400_000,
                        "impacts": {"reputation": 1},
                        "flags_set": ["brsr_indicator_essential"],
                        "regulatory_tooltip": (
                            "Meets P2 Essential Indicator on responsible sourcing; partial compliance with "
                            "EPR registration requirements under Plastic Waste Management Rules, 2016."
                        ),
                    },
                    "no_vendor_development": {
                        "title": "No Vendor Development",
                        "description": "No investment in MSME vendor development or capacity building.",
                        "cost": 0,
                        "impacts": {"reputation": -3, "governance_risk_delta": 2},
                        "flags_set": ["working_capital_hoarder"],
                        "regulatory_tooltip": (
                            "Heightens vulnerability to SPCB closure orders; compounds Section 135 CSR "
                            "shortfall penalties and CPCB consent-to-operate revocation risk."
                        ),
                    },
                },
            },
            "supply_chain": {
                "label": "Inclusive Sourcing Quotas",
                "icon": "🔗",
                "options": {
                    "disadvantaged_sourcing_quotas": {
                        "title": "Disadvantaged & Women-Led Sourcing",
                        "description": (
                            "Implement vendor sourcing quotas for disadvantaged communities "
                            "and women-led enterprises with preferential payment terms."
                        ),
                        "cost": -1_000_000,
                        "impacts": {"reputation": 3, "governance_risk_delta": -1},
                        "flags_set": ["msme_champion", "brsr_indicator_leadership"],
                        "regulatory_tooltip": (
                            "Ensures BRSR Core readiness; initiates preliminary Top-250 glide path "
                            "reasonable assurance mapping under SEBI Circular "
                            "SEBI/HO/CFD/CMD-2/P/CIR/2023/18."
                        ),
                    },
                    "aggregated_supply_auditing": {
                        "title": "Aggregated Supply Auditing",
                        "description": "Conduct aggregated supply chain demographic auditing annually.",
                        "cost": -300_000,
                        "impacts": {"reputation": 1},
                        "flags_set": ["brsr_indicator_essential"],
                        "regulatory_tooltip": (
                            "Meets P4 Essential Indicator on supply chain disclosure; partial compliance "
                            "with BRSR Core but defers reasonable assurance engagement to subsequent "
                            "filing period."
                        ),
                    },
                    "no_inclusive_sourcing": {
                        "title": "No Inclusive Sourcing",
                        "description": "No demographic-based sourcing targets. Pure commercial procurement.",
                        "cost": 0,
                        "impacts": {"reputation": -2, "governance_risk_delta": 1},
                        "flags_set": ["working_capital_hoarder"],
                        "regulatory_tooltip": (
                            "Heightens greenwash exposure; creates material discrepancy between "
                            "self-assessed and third-party validated BRSR Core attributes for value "
                            "chain KPIs."
                        ),
                    },
                },
            },
            "offsetting": {
                "label": "Small Vendor Credit Guarantees",
                "icon": "🌿",
                "options": {
                    "credit_guarantee_scheme": {
                        "title": "Credit Guarantee Scheme",
                        "description": (
                            "Establish a credit guarantee fund for small vendors, enabling access "
                            "to institutional finance at preferential rates."
                        ),
                        "cost": -1_200_000,
                        "impacts": {"reputation": 2, "governance_risk_delta": -1},
                        "flags_set": ["msme_champion", "brsr_indicator_leadership"],
                        "regulatory_tooltip": (
                            "Mitigates P1 Principle friction; satisfies Clause 4(b) of the updated "
                            "NGRBC mandate regarding independent oversight of lobbying and political "
                            "contribution disclosures."
                        ),
                    },
                    "basic_advance_payments": {
                        "title": "Basic Advance Payments",
                        "description": "Offer basic advance payment options for vendors with critical supply needs.",
                        "cost": -400_000,
                        "impacts": {"reputation": 1},
                        "flags_set": ["brsr_indicator_essential"],
                        "regulatory_tooltip": (
                            "Meets P1 Essential Indicator on anti-corruption policies; partial compliance "
                            "with NGRBC governance standards but may not satisfy institutional investor "
                            "ESG screening criteria."
                        ),
                    },
                    "no_credit_support": {
                        "title": "No Credit Support",
                        "description": "No vendor credit support. Standard commercial payment terms only.",
                        "cost": 0,
                        "impacts": {"reputation": -2, "governance_risk_delta": 1},
                        "flags_set": ["working_capital_hoarder"],
                        "regulatory_tooltip": (
                            "Heightens governance fragility; compounds vulnerability to SEBI adjudication "
                            "proceedings under Regulation 4(2)(f) of the LODR Regulations, 2015."
                        ),
                    },
                },
            },
            "human_resources": {
                "label": "Procurement Ethics Training",
                "icon": "👥",
                "options": {
                    "systematized_procurement_ethics": {
                        "title": "Systematized Procurement Ethics",
                        "description": (
                            "Deploy systematized procurement ethics training covering MSME fair dealing, "
                            "anti-corruption, and inclusive sourcing across all procurement teams."
                        ),
                        "cost": -800_000,
                        "impacts": {"reputation": 2, "governance_risk_delta": -1},
                        "flags_set": ["msme_champion", "brsr_indicator_leadership"],
                        "regulatory_tooltip": (
                            "Aligns with P3 Leadership Indicators; rectifies statutory EPFO and ESIC "
                            "non-compliance risks among third-party contractual dependencies. Satisfies "
                            "POSH Act, 2013 reporting mandates."
                        ),
                    },
                    "basic_procurement_guidelines": {
                        "title": "Basic Procurement Guidelines",
                        "description": "Distribute basic procurement guideline documents to sourcing teams.",
                        "cost": -200_000,
                        "impacts": {"reputation": 1},
                        "flags_set": ["brsr_indicator_essential"],
                        "regulatory_tooltip": (
                            "Meets P3 Essential Indicator on employee well-being metrics; addresses basic "
                            "OHS compliance under Factories Act but defers living wage gap analysis."
                        ),
                    },
                    "no_procurement_training": {
                        "title": "No Procurement Training",
                        "description": "No specific procurement ethics training. Commercial norms apply.",
                        "cost": 0,
                        "impacts": {"reputation": -1},
                        "flags_set": ["working_capital_hoarder"],
                        "regulatory_tooltip": (
                            "Heightens vulnerability to P3/P5 non-compliance citations; compounds exposure "
                            "to Section 25FF Industrial Disputes Act consequences and ESI Act penalty "
                            "proceedings."
                        ),
                    },
                },
            },
        },
    },

    # ── Round 9: Value Chain Assurance (P4 & P9) ──────────────────
    9: {
        "title": "Value Chain Assurance (P4 & P9)",
        "description": (
            "BRSR Core statutory mandate takes effect. Achieve reasonable assurance across "
            "9 value chain attributes or face extreme correction expenses."
        ),
        "areas": {
            "energy": {
                "label": "Third-Party Assurance",
                "icon": "⚡",
                "options": {
                    "big4_reasonable_assurance": {
                        "title": "Big 4 Reasonable Assurance",
                        "description": (
                            "Engage Big 4 audit firm for full reasonable assurance across all "
                            "9 BRSR Core value chain attributes with real-time telemetry."
                        ),
                        "cost": -2_500_000,
                        "impacts": {"governance_risk_delta": -4, "reputation": 5},
                        "flags_set": ["brsr_core_assured", "csrd_aligned", "brsr_indicator_leadership"],
                    },
                    "midtier_limited_assurance": {
                        "title": "Mid-Tier Limited Assurance",
                        "description": "Engage mid-tier auditor for limited scope assurance on priority attributes.",
                        "cost": -1_000_000,
                        "impacts": {"governance_risk_delta": -1, "reputation": 2},
                        "flags_set": ["brsr_indicator_essential"],
                    },
                    "self_assessed_filing": {
                        "title": "Self-Assessed Filing",
                        "description": "Rely on in-house self-assessed compliance filing matrix.",
                        "cost": -200_000,
                        "impacts": {"governance_risk_delta": 4, "reputation": -5},
                        "flags_set": ["brsr_greenwash_risk"],
                    },
                },
            },
            "operations": {
                "label": "Automated Telemetry Engines",
                "icon": "🏭",
                "options": {
                    "realtime_telemetry": {
                        "title": "Real-Time Automated Telemetry",
                        "description": (
                            "Deploy automated IoT-based telemetry engines across manufacturing "
                            "for continuous ESG metric collection and anomaly detection."
                        ),
                        "cost": -1_500_000,
                        "impacts": {"reputation": 3, "governance_risk_delta": -2},
                        "flags_set": ["brsr_core_assured", "csrd_aligned", "brsr_indicator_leadership"],
                    },
                    "digital_verification_portals": {
                        "title": "Digital Verification Portals",
                        "description": "Set up intermittent digital verification portals for periodic data collection.",
                        "cost": -600_000,
                        "impacts": {"reputation": 1, "governance_risk_delta": -1},
                        "flags_set": ["brsr_indicator_essential"],
                    },
                    "no_telemetry": {
                        "title": "No Telemetry",
                        "description": "No automated data collection. Manual quarterly reporting only.",
                        "cost": 0,
                        "impacts": {"reputation": -3, "governance_risk_delta": 2},
                        "flags_set": ["brsr_greenwash_risk"],
                    },
                },
            },
            "supply_chain": {
                "label": "Tier-2 Supplier Onboarding",
                "icon": "🔗",
                "options": {
                    "tier2_onboarding_networks": {
                        "title": "Tier-2 Onboarding Networks",
                        "description": (
                            "Build formal Tier-2 supplier onboarding networks with ESG screening, "
                            "capacity building, and continuous monitoring requirements."
                        ),
                        "cost": -1_200_000,
                        "impacts": {"governance_risk_delta": -2, "reputation": 3},
                        "flags_set": ["brsr_core_assured", "csrd_aligned", "brsr_indicator_leadership"],
                    },
                    "semiannual_spot_auditing": {
                        "title": "Semi-Annual Spot Auditing",
                        "description": "Conduct semi-annual value chain spot audits on a sample basis.",
                        "cost": -500_000,
                        "impacts": {"governance_risk_delta": -1, "reputation": 1},
                        "flags_set": ["brsr_indicator_essential"],
                    },
                    "no_tier2_engagement": {
                        "title": "No Tier-2 Engagement",
                        "description": "No active Tier-2 supplier engagement or monitoring programs.",
                        "cost": 0,
                        "impacts": {"reputation": -3, "governance_risk_delta": 2},
                        "flags_set": ["brsr_greenwash_risk"],
                    },
                },
            },
            "offsetting": {
                "label": "Consumer Grievance Analytics",
                "icon": "🌿",
                "options": {
                    "enterprise_grievance_analytics": {
                        "title": "Enterprise Grievance Analytics",
                        "description": (
                            "Deploy enterprise-grade consumer grievance analytics with AI-powered "
                            "pattern recognition and automated escalation workflows."
                        ),
                        "cost": -1_000_000,
                        "impacts": {"reputation": 3, "governance_risk_delta": -1},
                        "flags_set": ["brsr_core_assured", "csrd_aligned", "brsr_indicator_leadership"],
                    },
                    "generic_supplier_dossiers": {
                        "title": "Generic Supplier ESG Dossiers",
                        "description": "Compile generic supplier ESG dossiers for regulatory filing purposes.",
                        "cost": -300_000,
                        "impacts": {"reputation": 1},
                        "flags_set": ["brsr_indicator_essential"],
                    },
                    "no_grievance_system": {
                        "title": "No Grievance System",
                        "description": "No dedicated consumer grievance analytics. Ad-hoc complaint handling.",
                        "cost": 0,
                        "impacts": {"reputation": -3, "governance_risk_delta": 2},
                        "flags_set": ["brsr_greenwash_risk"],
                    },
                },
            },
            "human_resources": {
                "label": "ESG Specialist Certification",
                "icon": "👥",
                "options": {
                    "multitier_esg_certification": {
                        "title": "Multi-Tier ESG Certification",
                        "description": (
                            "Launch advanced multi-tier ESG specialist certification program "
                            "with external accreditation for value chain assurance teams."
                        ),
                        "cost": -800_000,
                        "impacts": {"reputation": 2, "governance_risk_delta": -1},
                        "flags_set": ["brsr_core_assured", "csrd_aligned", "brsr_indicator_leadership"],
                    },
                    "basic_esg_training": {
                        "title": "Basic ESG Training",
                        "description": "Provide basic ESG awareness training to procurement and operations staff.",
                        "cost": -200_000,
                        "impacts": {"reputation": 1},
                        "flags_set": ["brsr_indicator_essential"],
                    },
                    "no_esg_training": {
                        "title": "No ESG Training",
                        "description": "No dedicated ESG training programs. Existing skills deemed sufficient.",
                        "cost": 0,
                        "impacts": {"reputation": -1},
                        "flags_set": ["brsr_greenwash_risk"],
                    },
                },
            },
        },
    },

    # ── Round 10: Global Integration & Double Materiality ─────────
    10: {
        "title": "Global Integration & Double Materiality (Integrated)",
        "description": (
            "Filing deadline. Institutional investors demand BRSR-CSRD alignment "
            "and Double Materiality verification for the terminal ESG premium."
        ),
        "areas": {
            "energy": {
                "label": "Double Materiality Verification",
                "icon": "⚡",
                "options": {
                    "third_party_double_materiality": {
                        "title": "Third-Party Double Materiality",
                        "description": (
                            "Commission third-party double materiality verification assessing both "
                            "financial and real-world impact footprints per CSRD/ESRS standards."
                        ),
                        "cost": -1_500_000,
                        "impacts": {"governance_risk_delta": -4, "reputation": 7},
                        "flags_set": ["brsr_integrated_report", "csrd_aligned", "brsr_indicator_leadership"],
                    },
                    "internal_materiality_registry": {
                        "title": "Internal Materiality Registry",
                        "description": "Formulate internal matrix materiality registries for key stakeholder groups.",
                        "cost": -600_000,
                        "impacts": {"governance_risk_delta": -1, "reputation": 3},
                        "flags_set": ["brsr_indicator_essential"],
                    },
                    "skip_materiality": {
                        "title": "Skip Materiality Assessment",
                        "description": "By-pass specialized double materiality assessments. Minimum filing only.",
                        "cost": 0,
                        "impacts": {"governance_risk_delta": 2, "reputation": -2},
                        "flags_set": ["brsr_compliance_only"],
                    },
                },
            },
            "operations": {
                "label": "Six Capitals Integrated Report",
                "icon": "🏭",
                "options": {
                    "six_capitals_report": {
                        "title": "Six Capitals Integrated Report",
                        "description": (
                            "Publish a holistically audited Six Capitals integrated report covering "
                            "financial, manufactured, intellectual, human, social, and natural capital."
                        ),
                        "cost": -1_200_000,
                        "impacts": {"reputation": 5, "governance_risk_delta": -2},
                        "flags_set": ["brsr_integrated_report", "brsr_indicator_leadership"],
                    },
                    "executive_summary_briefing": {
                        "title": "Executive Summary Briefing",
                        "description": "Compile consolidated executive summary briefing materials for Board.",
                        "cost": -400_000,
                        "impacts": {"reputation": 2, "governance_risk_delta": -1},
                        "flags_set": ["brsr_indicator_essential"],
                    },
                    "bare_minimum_filing": {
                        "title": "Bare Minimum Filing",
                        "description": "File basic regulatory disclosures. No integrated reporting.",
                        "cost": -100_000,
                        "impacts": {"reputation": -2},
                        "flags_set": ["brsr_compliance_only"],
                    },
                },
            },
            "supply_chain": {
                "label": "Multi-Framework Mapping",
                "icon": "🔗",
                "options": {
                    "gri_tcfd_esrs_mapping": {
                        "title": "GRI/TCFD/ESRS Multi-Framework Mapping",
                        "description": (
                            "Execute global multi-framework mapping covering GRI, TCFD, and ESRS "
                            "standards with automated cross-referencing."
                        ),
                        "cost": -1_000_000,
                        "impacts": {"governance_risk_delta": -2, "reputation": 4},
                        "flags_set": ["brsr_integrated_report", "csrd_aligned", "brsr_indicator_leadership"],
                    },
                    "cross_pillar_kpi_indexes": {
                        "title": "Cross-Pillar KPI Indexes",
                        "description": "Generate advanced cross-pillar KPI indexes for internal tracking.",
                        "cost": -400_000,
                        "impacts": {"governance_risk_delta": -1, "reputation": 2},
                        "flags_set": ["brsr_indicator_essential"],
                    },
                    "no_framework_integration": {
                        "title": "No Framework Integration",
                        "description": "No international standard integrations. BRSR-only filing.",
                        "cost": 0,
                        "impacts": {"reputation": -1},
                        "flags_set": ["brsr_compliance_only"],
                    },
                },
            },
            "offsetting": {
                "label": "ESG Financial Connectivity",
                "icon": "🌿",
                "options": {
                    "realtime_esg_connectivity": {
                        "title": "Real-Time ESG Financial Connectivity",
                        "description": (
                            "Launch real-time ESG-financial connectivity dashboards integrating "
                            "sustainability metrics with financial performance indicators."
                        ),
                        "cost": -800_000,
                        "impacts": {"reputation": 3, "governance_risk_delta": -1},
                        "flags_set": ["brsr_integrated_report", "brsr_net_positive_dividend", "brsr_indicator_leadership"],
                    },
                    "periodic_esg_reports": {
                        "title": "Periodic ESG Reports",
                        "description": "Generate periodic ESG performance reports for investor communications.",
                        "cost": -300_000,
                        "impacts": {"reputation": 1},
                        "flags_set": ["brsr_indicator_essential"],
                    },
                    "no_esg_reporting": {
                        "title": "No ESG-Finance Reporting",
                        "description": "No dedicated ESG-financial connectivity. Standard annual report only.",
                        "cost": 0,
                        "impacts": {"reputation": -1},
                        "flags_set": ["brsr_compliance_only"],
                    },
                },
            },
            "human_resources": {
                "label": "Institutional Analyst Comms",
                "icon": "👥",
                "options": {
                    "institutional_analyst_comms": {
                        "title": "Institutional Analyst Communications",
                        "description": (
                            "Deploy institutional analyst communications program with ESG roadshows, "
                            "investor briefings, and sustainability-linked bond frameworks."
                        ),
                        "cost": -1_000_000,
                        "impacts": {"reputation": 3, "governance_risk_delta": -1},
                        "flags_set": ["brsr_integrated_report", "brsr_indicator_leadership"],
                    },
                    "basic_investor_updates": {
                        "title": "Basic Investor Updates",
                        "description": "Include basic ESG section in quarterly investor update presentations.",
                        "cost": -200_000,
                        "impacts": {"reputation": 1},
                        "flags_set": ["brsr_indicator_essential"],
                    },
                    "no_investor_outreach": {
                        "title": "No ESG Investor Outreach",
                        "description": "No dedicated ESG investor outreach or sustainability communications.",
                        "cost": 0,
                        "impacts": {"reputation": -1},
                        "flags_set": ["brsr_compliance_only"],
                    },
                },
            },
        },
    },
}


# ═════════════════════════════════════════════════════════════════
#  BRSR PILLAR HELPER FUNCTIONS
# ═════════════════════════════════════════════════════════════════

def get_brsr_pillar_config(round_number: int) -> dict | None:
    """Return just the ``areas`` dict for the given BRSR pillar round."""
    cfg = BRSR_PILLAR_OPTIONS.get(round_number)
    if not cfg:
        return None
    return copy.deepcopy(cfg.get("areas", {}))


def aggregate_brsr_pillar_decisions(
    round_number: int,
    pillar_choices: dict[str, str],
) -> dict[str, Any]:
    """
    Aggregate pillar selections into combined impacts.

    Mirrors :func:`aggregate_pillar_decisions` in ``pillar_configs.py``.

    Returns::

        {
            "total_cost": float,
            "impacts": {key: delta},
            "flags_set": [str],
            "per_area": {area: {action_key, title, cost, impacts}},
            "exclusivity_warnings": [],
        }
    """
    cfg = BRSR_PILLAR_OPTIONS.get(round_number)
    if not cfg:
        return {
            "total_cost": 0,
            "impacts": {},
            "flags_set": [],
            "per_area": {},
            "exclusivity_warnings": [],
        }

    areas = cfg.get("areas", {})
    total_cost: float = 0
    combined_impacts: dict[str, float] = {}
    all_flags: list[str] = []
    per_area: dict[str, dict] = {}

    for area_key, action_key in pillar_choices.items():
        area_cfg = areas.get(area_key)
        if not area_cfg:
            continue

        action = area_cfg.get("options", {}).get(action_key)
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
        "exclusivity_warnings": [],
    }


def translate_brsr_pillars_to_legacy_choice(
    round_number: int,
    pillar_choices: dict[str, str],
) -> str:
    """
    Map BRSR pillar selections to the closest legacy ``option_a/b/c``
    for backward compatibility with ``track.py`` round logic.

    Uses flag-based priority with cost-based fallback.
    """
    agg = aggregate_brsr_pillar_decisions(round_number, pillar_choices)
    flags_this_round = set(agg["flags_set"])
    total_cost = agg["total_cost"]

    # ── Round-specific flag → legacy mapping (checked a → b → c) ──
    FLAG_OVERRIDES: dict[int, dict[str, set[str]]] = {
        1: {
            "option_a": {"brsr_pioneer"},
            "option_b": {"brsr_ethics_officer"},
            "option_c": {"governance_fragility"},
        },
        2: {
            "option_a": {"brsr_living_wage"},
            "option_b": {"brsr_indicator_essential"},
            "option_c": {"brsr_statutory_minimums"},
        },
        3: {
            "option_a": {"brsr_circular_symbiosis"},
            "option_b": {"brsr_indicator_essential"},
            "option_c": {"brsr_regulatory_minimum"},
        },
        4: {
            "option_a": {"brsr_core_assured"},
            "option_b": {"brsr_indicator_essential"},
            "option_c": {"brsr_greenwash_risk"},
        },
        5: {
            "option_a": {"brsr_integrated_report"},
            "option_b": {"brsr_indicator_essential"},
            "option_c": {"brsr_compliance_only"},
        },
        6: {
            "option_a": {"deep_hrdd_active"},
            "option_b": {"brsr_indicator_essential"},
            "option_c": {"tier2_human_rights_risk"},
        },
        7: {
            "option_a": {"policy_leadership"},
            "option_b": {"brsr_indicator_essential"},
            "option_c": {"greenwash_advocacy"},
        },
        8: {
            "option_a": {"msme_champion"},
            "option_b": {"brsr_indicator_essential"},
            "option_c": {"working_capital_hoarder"},
        },
        9: {
            "option_a": {"brsr_core_assured", "csrd_aligned"},
            "option_b": {"brsr_indicator_essential"},
            "option_c": {"brsr_greenwash_risk"},
        },
        10: {
            "option_a": {"brsr_integrated_report"},
            "option_b": {"brsr_indicator_essential"},
            "option_c": {"brsr_compliance_only"},
        },
    }

    round_overrides = FLAG_OVERRIDES.get(round_number, {})
    for proxy_choice in ("option_a", "option_b", "option_c"):
        trigger_flags = round_overrides.get(proxy_choice, set())
        if trigger_flags & flags_this_round:
            return proxy_choice

    # ── Fallback: cost-based heuristic ──
    if total_cost <= -8_000_000:
        return "option_a"
    elif total_cost <= -3_000_000:
        return "option_b"
    else:
        return "option_c"


# ═════════════════════════════════════════════════════════════════
#  LEGACY ROUND HELPERS (DO NOT MODIFY)
# ═════════════════════════════════════════════════════════════════

def get_brsr_round_config(round_number: int) -> dict | None:
    import copy
    if round_number not in BRSR_ROUND_CONFIGS:
        return None
    raw = copy.deepcopy(BRSR_ROUND_CONFIGS[round_number])
    for key, opt in raw.setdefault("options", {}).items():
        if "label" not in opt:
            opt["label"] = key[-1].upper()
    if "crisis" not in raw:
        raw["crisis"] = {
            "id": f"brsr_r{round_number}",
            "title": raw.get("crisis_title", "BRSR Challenge"),
            "description": raw.get("crisis_narrative", ""),
            "icon": "🇮🇳",
        }
    return raw

def get_brsr_round_options(round_number: int) -> dict:
    cfg = get_brsr_round_config(round_number)
    return cfg.get("options", {}) if cfg else {}
