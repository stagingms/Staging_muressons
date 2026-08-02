"""
Muressons Global Corporation — Supply Chain Track: Round Configurations

7 rounds of crisis scenarios covering the full supply chain management lifecycle.
Each round follows the same ABC option structure as the main simulation,
with graduated cost/impact trade-offs and inter-round flag dependencies.

Pedagogical Framework:
  - Builds from visibility (R1) through ethics (R2), emissions (R3),
    circularity (R4), digitalisation (R5), geopolitics (R6) to resilience (R7)
  - Each round's options range from aggressive/costly to cheap/risky
  - Flag dependencies create consequence chains across rounds
  - Custom metrics: supply_visibility, supplier_risk_score, scope3_reduction,
    circular_procurement_index, digital_maturity, geopolitical_resilience

Scoring Dimensions (separate leaderboard):
  - Supply Visibility (0–100): How deep the organisation can see into its supply tiers
  - Supplier Risk Score (100→0): Lower is better — aggregate risk across all tiers
  - Scope 3 Reduction %: Cumulative supply chain carbon reduction
"""

from __future__ import annotations
from typing import Any


SUPPLY_CHAIN_ROUND_CONFIGS: dict[int, dict[str, Any]] = {

    # ═══════════════════════════════════════════════════════════════
    #  SC-R1: SUPPLIER MAPPING & TIER ANALYSIS
    #  Theme: Visibility & Transparency
    #  Key tension: Depth vs cost of supply chain visibility
    # ═══════════════════════════════════════════════════════════════
    1: {
        "title": "Supplier Mapping & Tier Analysis",
        "theme": "Visibility & Transparency",
        "crisis": {
            "id": "sc_r1_mapping",
            "title": "The Hidden Tiers",
            "description": (
                "A leaked audit report reveals that 60% of your Tier-2 and Tier-3 "
                "suppliers have never been assessed for ESG compliance. An investigative "
                "journalist is asking questions, and the EU Corporate Sustainability "
                "Due Diligence Directive (CSDDD) enforcement begins next period. "
                "Your current supply chain visibility extends only to direct (Tier-1) "
                "suppliers — leaving massive blind spots in conflict minerals, forced "
                "labour risk, and environmental impact."
            ),
            "icon": "🔗",
            "facilitator_note": (
                "This round establishes the baseline for supply chain visibility. "
                "Option A gives the deepest foundation but costs heavily upfront. "
                "Option C's self-assessment approach creates a 'greenwash risk' flag "
                "that compounds in SC-R5 (digital traceability)."
            ),
            "tyler_reference": {
                "quote": (
                    "\"Do you know where everything you buy comes from? "
                    "What appears straightforward at the surface often involves "
                    "a vast, opaque network of suppliers and materials.\""
                ),
                "speaker": "Olivia Tyler",
                "talk_title": "The Complex Path to Sustainability",
                "discussion_prompt": (
                    "If a consumer buys a smartphone from Muressons, how many "
                    "supplier tiers deep does the chain go? (Answer: typically "
                    "7\u201310 tiers.) How many can they name? Tyler uses a simple "
                    "cake to show that even basic products have invisible supply "
                    "chains. What does that mean for your mapping decision?"
                ),
                "source_url": "https://www.ted.com/talks/olivia_tyler_the_complex_path_to_sustainability",
            },
        },
        "options": {
            "option_a": {
                "label": "A",
                "title": "Full Multi-Tier Mapping (Tier 1–4)",
                "description": (
                    "Commission a comprehensive supply chain mapping exercise using "
                    "third-party ESG auditors. Maps all suppliers down to Tier-4 raw "
                    "material sources. Includes on-site factory audits, satellite "
                    "monitoring for deforestation, and worker voice surveys."
                ),
                "flags_set": ["full_tier_mapping", "sc_deep_visibility"],
                "impacts": {
                    "treasury": -5_000_000,
                    "supply_visibility": +40,
                    "supplier_risk_score": -15,
                    "governance_risk_delta": -8,
                    "reputation": +5,
                },
            },
            "option_b": {
                "label": "B",
                "title": "Tier-1 & Critical Tier-2 Audit",
                "description": (
                    "Focus auditing resources on all Tier-1 suppliers and the "
                    "highest-risk Tier-2 suppliers (minerals, textiles, agriculture). "
                    "Uses a risk-based approach — cheaper but leaves gaps in "
                    "lower-risk categories."
                ),
                "flags_set": ["partial_tier_mapping"],
                "impacts": {
                    "treasury": -2_000_000,
                    "supply_visibility": +20,
                    "supplier_risk_score": -8,
                    "governance_risk_delta": -3,
                    "reputation": +2,
                },
            },
            "option_c": {
                "label": "C",
                "title": "Self-Assessment Questionnaires",
                "description": (
                    "Distribute ESG self-assessment questionnaires to Tier-1 "
                    "suppliers and rely on their responses. No on-site audits. "
                    "Cheapest option but creates significant greenwash risk — "
                    "self-reported data has a 40% inaccuracy rate in practice."
                ),
                "flags_set": ["self_assessment_only", "sc_greenwash_risk"],
                "impacts": {
                    "treasury": -300_000,
                    "supply_visibility": +5,
                    "supplier_risk_score": +5,
                    "reputation": -2,
                },
            },
        },
    },

    # ═══════════════════════════════════════════════════════════════
    #  SC-R2: ETHICAL SOURCING & MODERN SLAVERY
    #  Theme: Human Rights Due Diligence
    #  Key tension: Ethical imperative vs commercial disruption
    #  Cross-track: Findings seed ETH-R5 (Ethics track) scenarios
    # ═══════════════════════════════════════════════════════════════
    2: {
        "title": "Ethical Sourcing & Modern Slavery",
        "theme": "Human Rights Due Diligence",
        "crisis": {
            "id": "sc_r2_ethics",
            "title": "The Cobalt Question",
            "description": (
                "An NGO investigation published in the Financial Times links your "
                "electronics BU's battery supplier to artisanal cobalt mines in the "
                "DRC where child labour has been documented. The Modern Slavery Act "
                "requires your annual statement to address this. Three major "
                "institutional investors have sent formal letters requesting your "
                "remediation plan within 30 days."
            ),
            "icon": "⛏️",
            "facilitator_note": (
                "This round introduces the tension between ethical imperative and "
                "commercial continuity. Option A is the 'right thing' but creates "
                "massive short-term supply disruption. Option C's quiet monitoring "
                "creates a 'modern_slavery_unresolved' flag that doubles the "
                "reputational hit in SC-R6 if geopolitical tensions surface."
            ),
            "tyler_reference": {
                "quote": (
                    "\"The daunting challenges companies face when enforcing "
                    "sustainability across their supply chains arise from the "
                    "depth and opacity of lower-tier supplier relationships.\""
                ),
                "speaker": "Olivia Tyler",
                "talk_title": "The Complex Path to Sustainability",
                "discussion_prompt": (
                    "If Muressons discovers child labour at a Tier-4 cobalt mine, "
                    "are they morally responsible? Legally under the CSDDD? Tyler "
                    "argues the \u2018burden of responsibility\u2019 extends to every tier "
                    "you benefit from \u2014 even the ones you can\u2019t see. Does your "
                    "SC-R1 mapping decision change this analysis?"
                ),
                "source_url": "https://www.ted.com/talks/olivia_tyler_the_complex_path_to_sustainability",
            },
        },
        "special_rules": {
            "blindspot_interaction": True,
            "sc_r1_deep_visibility_bonus": {
                "description": "Full Tier Mapping in SC-R1 reduces cost of Option A by $1M (early intelligence)",
                "discount_amount": 1_000_000,
                "applies_to": "option_a",
            },
        },
        "options": {
            "option_a": {
                "label": "A",
                "title": "Immediate Supply Chain Restructuring",
                "description": (
                    "Terminate contracts with implicated suppliers immediately. "
                    "Source certified conflict-free cobalt through the Responsible "
                    "Minerals Initiative (RMI). Engage directly with artisanal "
                    "mining cooperatives to fund formalisation programs."
                ),
                "flags_set": ["ethical_sourcing_restructured", "sc_cobalt_clean"],
                "impacts": {
                    "treasury": -8_000_000,
                    "supply_visibility": +10,
                    "supplier_risk_score": -20,
                    "social_license_delta": +10,
                    "reputation": +8,
                    "carbon_intensity_delta": +2,  # Short-term logistics rerouting
                },
            },
            "option_b": {
                "label": "B",
                "title": "Managed Transition with Remediation Fund",
                "description": (
                    "Maintain existing suppliers but establish a $3M remediation "
                    "fund to improve working conditions. Deploy third-party monitors "
                    "to the mines. Set a 2-year deadline for full compliance or "
                    "contract termination."
                ),
                "flags_set": ["ethical_sourcing_transitional", "remediation_fund_active"],
                "impacts": {
                    "treasury": -3_000_000,
                    "supply_visibility": +5,
                    "supplier_risk_score": -10,
                    "social_license_delta": +4,
                    "reputation": +3,
                },
            },
            "option_c": {
                "label": "C",
                "title": "Enhanced Monitoring Only",
                "description": (
                    "Issue a public statement committing to 'enhanced due diligence' "
                    "while quietly increasing monitoring frequency. No supplier "
                    "changes. Cheapest option but carries significant reputational "
                    "risk if the NGO escalates."
                ),
                "flags_set": ["modern_slavery_unresolved", "sc_monitoring_only"],
                "impacts": {
                    "treasury": -500_000,
                    "supply_visibility": +2,
                    "supplier_risk_score": +8,
                    "social_license_delta": -5,
                    "reputation": -5,
                    "governance_risk_delta": +5,
                },
            },
        },
    },

    # ═══════════════════════════════════════════════════════════════
    #  SC-R3: SCOPE 3 DECARBONISATION DEEP DIVE
    #  Theme: Supply Chain Emissions
    #  Key tension: Speed vs cost of supplier decarbonisation
    # ═══════════════════════════════════════════════════════════════
    3: {
        "title": "Scope 3 Decarbonisation Deep Dive",
        "theme": "Supply Chain Emissions",
        "crisis": {
            "id": "sc_r3_scope3",
            "title": "The Carbon Cliff",
            "description": (
                "Your newly published Scope 3 emissions inventory reveals that "
                "upstream supply chain emissions are 4.2× your direct (Scope 1+2) "
                "footprint. The Science Based Targets initiative (SBTi) has flagged "
                "your near-term target as insufficient — you must demonstrate a "
                "credible 42% reduction pathway by 2030 or face removal from the "
                "SBTi validated list. Three green bond covenants reference your "
                "SBTi status."
            ),
            "icon": "🏭",
            "facilitator_note": (
                "This round connects directly to main-sim R3 (Scope 3) themes. "
                "The 'scope3_reduction' metric is the primary scoring dimension. "
                "Option A's supplier capacity building creates the most durable "
                "decarbonisation but takes 2 rounds to fully materialise."
            ),
            "tyler_reference": {
                "quote": (
                    "\"Achieving genuine sustainability requires moving beyond "
                    "surface-level corporate initiatives into the structural "
                    "transformation of how goods are produced.\""
                ),
                "speaker": "Olivia Tyler",
                "talk_title": "The Complex Path to Sustainability",
                "discussion_prompt": (
                    "Tyler would argue that carbon offsets (Option C) are a "
                    "\u2018surface-level initiative\u2019. Supplier capacity building "
                    "(Option A) is structural transformation. But it costs 4\u00d7 "
                    "more. When is the cheap option genuinely irresponsible "
                    "versus pragmatically sensible?"
                ),
                "source_url": "https://www.ted.com/talks/olivia_tyler_the_complex_path_to_sustainability",
            },
        },
        "options": {
            "option_a": {
                "label": "A",
                "title": "Supplier Capacity Building Program",
                "description": (
                    "Fund a $6M program to deploy clean energy and efficiency "
                    "technology directly into your Tier-1 and Tier-2 supplier "
                    "facilities. Includes on-site energy audits, solar PV installation "
                    "funding, and process electrification support."
                ),
                "flags_set": ["supplier_capacity_building", "scope3_deep_cut"],
                "impacts": {
                    "treasury": -6_000_000,
                    "scope3_reduction": +30,
                    "carbon_intensity_delta": -12,
                    "supplier_risk_score": -5,
                    "reputation": +6,
                    "natural_capital_debt_delta": -8,
                },
            },
            "option_b": {
                "label": "B",
                "title": "Supplier Switching to Low-Carbon Sources",
                "description": (
                    "Replace the highest-emitting 20% of suppliers with pre-vetted "
                    "low-carbon alternatives. Fast carbon reduction but creates "
                    "short-term supply disruption risk and strands existing "
                    "supplier relationships."
                ),
                "flags_set": ["supplier_switching", "supply_disruption_risk"],
                "impacts": {
                    "treasury": -3_500_000,
                    "scope3_reduction": +20,
                    "carbon_intensity_delta": -8,
                    "supplier_risk_score": +5,  # Disruption risk
                    "governance_risk_delta": +5,
                    "reputation": +3,
                },
            },
            "option_c": {
                "label": "C",
                "title": "Carbon Offset & Insetting Program",
                "description": (
                    "Purchase verified carbon offsets to cover Scope 3 emissions "
                    "while running a small insetting program (reforestation in "
                    "supplier regions). Cheapest option but does not address "
                    "root-cause emissions — creates SBTi compliance risk."
                ),
                "flags_set": ["scope3_offset_only", "sbti_risk"],
                "impacts": {
                    "treasury": -1_500_000,
                    "scope3_reduction": +8,
                    "carbon_intensity_delta": -3,
                    "natural_capital_debt_delta": +5,
                    "reputation": -3,
                },
            },
        },
    },

    # ═══════════════════════════════════════════════════════════════
    #  SC-R4: CIRCULAR PROCUREMENT
    #  Theme: Closed-Loop Material Sourcing
    #  Key tension: Circular ambition vs linear economics
    # ═══════════════════════════════════════════════════════════════
    4: {
        "title": "Circular Procurement",
        "theme": "Closed-Loop Material Sourcing",
        "crisis": {
            "id": "sc_r4_circular",
            "title": "The Waste Mandate",
            "description": (
                "New EU Packaging and Packaging Waste Regulation (PPWR) mandates "
                "minimum recycled content thresholds: 35% for plastics, 70% for "
                "metals, and 85% for paper/board by 2030. Your current procurement "
                "is 95% virgin materials. Non-compliance fines are projected at "
                "$12M annually. Your procurement team says the recycled materials "
                "market is immature and supply is unreliable."
            ),
            "icon": "♻️",
            "facilitator_note": (
                "This round tests whether teams understand the Total Cost of "
                "Ownership in circular vs linear procurement. Option A has high "
                "upfront cost but eliminates the fine risk entirely. Option C's "
                "compliance-minimum approach creates ongoing OPEX drag."
            ),
            "tyler_reference": {
                "quote": (
                    "\"The complex path to sustainability is not a straight line "
                    "\u2014 it requires rethinking how raw materials flow through "
                    "the entire value chain, from extraction to end-of-life.\""
                ),
                "speaker": "Olivia Tyler",
                "talk_title": "The Complex Path to Sustainability",
                "discussion_prompt": (
                    "Tyler\u2019s framework extends to how we think about waste. "
                    "Circular procurement means the supply chain doesn\u2019t end "
                    "at the consumer \u2014 it loops back. Ask: does your current "
                    "procurement model assume materials are \u2018consumed\u2019 or "
                    "\u2018borrowed\u2019? What changes if you adopt Tyler\u2019s lens?"
                ),
                "source_url": "https://www.ted.com/talks/olivia_tyler_the_complex_path_to_sustainability",
            },
        },
        "options": {
            "option_a": {
                "label": "A",
                "title": "Full Circular Procurement Transformation",
                "description": (
                    "Redesign procurement strategy around circular principles. "
                    "Invest in take-back schemes, establish recycled material "
                    "supply agreements, and build internal reprocessing capability. "
                    "Achieves 60% recycled content within 2 years."
                ),
                "flags_set": ["circular_procurement_leader", "take_back_active"],
                "impacts": {
                    "treasury": -7_000_000,
                    "circular_procurement_index": +45,
                    "natural_capital_debt_delta": -12,
                    "supplier_risk_score": -8,
                    "reputation": +8,
                },
            },
            "option_b": {
                "label": "B",
                "title": "Targeted Recycled Content Sourcing",
                "description": (
                    "Focus on the three highest-volume material categories "
                    "(plastics, metals, packaging) and secure recycled content "
                    "supply contracts. Achieves 40% recycled content — above "
                    "the minimum but below best practice."
                ),
                "flags_set": ["circular_procurement_partial"],
                "impacts": {
                    "treasury": -3_000_000,
                    "circular_procurement_index": +25,
                    "natural_capital_debt_delta": -5,
                    "reputation": +3,
                },
            },
            "option_c": {
                "label": "C",
                "title": "Regulatory Minimum Compliance",
                "description": (
                    "Meet the bare minimum recycled content thresholds through "
                    "spot-market purchasing. Volatile pricing and unreliable supply "
                    "mean ongoing OPEX premium. No structural change to procurement."
                ),
                "flags_set": ["circular_minimum_compliance"],
                "impacts": {
                    "treasury": -1_000_000,
                    "circular_procurement_index": +10,
                    "natural_capital_debt_delta": +3,
                    "reputation": -2,
                    "governance_risk_delta": +3,
                },
            },
        },
    },

    # ═══════════════════════════════════════════════════════════════
    #  SC-R5: DIGITAL SUPPLY CHAIN & TRACEABILITY
    #  Theme: Technology-Enabled Transparency
    #  Key tension: Digital investment vs data privacy/complexity
    #  Cross-track: ETH-R2 AI framework enriches this round
    # ═══════════════════════════════════════════════════════════════
    5: {
        "title": "Digital Supply Chain & Traceability",
        "theme": "Technology-Enabled Transparency",
        "crisis": {
            "id": "sc_r5_digital",
            "title": "The Traceability Ultimatum",
            "description": (
                "The EU Digital Product Passport (DPP) regulation requires full "
                "material traceability by 2027. Major retail customers (IKEA, "
                "Unilever, Apple) now mandate real-time supply chain visibility "
                "as a procurement condition. Your current systems rely on Excel "
                "spreadsheets and email-based supplier communications. The technology "
                "gap is existential — without digital traceability, you risk losing "
                "40% of your B2B revenue within 18 months."
            ),
            "icon": "📡",
            "facilitator_note": (
                "If SC-R1 chose Option C (self-assessment), the 'sc_greenwash_risk' "
                "flag is active — Option A's blockchain solution will surface false "
                "data from self-reported suppliers, costing an additional $2M to "
                "remediate. This is the consequence chain in action."
            ),
            "tyler_reference": {
                "quote": (
                    "\"Blockchain can track goods from extraction to consumption, "
                    "creating trustworthy products for consumers \u2014 but technology "
                    "alone is not enough without collaboration and honest data.\""
                ),
                "speaker": "Olivia Tyler",
                "talk_title": "The Complex Path to Sustainability",
                "discussion_prompt": (
                    "Tyler advocates for blockchain traceability but warns that "
                    "tech doesn\u2019t create trust \u2014 honest inputs do. What happens "
                    "when your blockchain surfaces bad data? (Connect to SC-R1: "
                    "self-reported data has a 40% inaccuracy rate.) Is your "
                    "digital investment building transparency or just recording "
                    "existing lies more efficiently?"
                ),
                "source_url": "https://www.ted.com/talks/olivia_tyler_the_complex_path_to_sustainability",
            },
        },
        "special_rules": {
            "greenwash_interaction": True,
            "sc_greenwash_penalty": {
                "description": "Self-assessment data from SC-R1 contaminates blockchain → +$2M cost for Option A",
                "penalty_amount": 2_000_000,
                "applies_to": "option_a",
                "flag_required": "sc_greenwash_risk",
            },
        },
        "options": {
            "option_a": {
                "label": "A",
                "title": "Blockchain-Enabled Digital Twin",
                "description": (
                    "Deploy a full blockchain-based supply chain digital twin with "
                    "IoT sensor integration at all Tier-1 and critical Tier-2 "
                    "facilities. Real-time monitoring of carbon, water, labour, and "
                    "material provenance. Includes supplier onboarding and training."
                ),
                "flags_set": ["blockchain_traceability_sc", "digital_twin_supply"],
                "impacts": {
                    "treasury": -8_000_000,
                    "digital_maturity": +40,
                    "supply_visibility": +15,
                    "supplier_risk_score": -12,
                    "governance_risk_delta": -8,
                    "reputation": +6,
                },
            },
            "option_b": {
                "label": "B",
                "title": "Cloud ERP Integration Platform",
                "description": (
                    "Implement a cloud-based ERP integration platform that connects "
                    "to Tier-1 supplier systems via API. Provides batch-level "
                    "traceability for key material categories. Faster deployment "
                    "than blockchain but less tamper-proof."
                ),
                "flags_set": ["erp_integration_sc"],
                "impacts": {
                    "treasury": -3_500_000,
                    "digital_maturity": +25,
                    "supply_visibility": +8,
                    "supplier_risk_score": -5,
                    "reputation": +3,
                },
            },
            "option_c": {
                "label": "C",
                "title": "Manual Compliance Documentation",
                "description": (
                    "Hire a compliance team to manually collect and verify "
                    "documentation from suppliers. Generates paper compliance "
                    "but no real-time visibility. High labour cost, error-prone, "
                    "and does not satisfy the DPP regulation."
                ),
                "flags_set": ["manual_compliance_sc", "dpp_non_compliant"],
                "impacts": {
                    "treasury": -1_500_000,
                    "digital_maturity": +5,
                    "supply_visibility": +2,
                    "governance_risk_delta": +8,
                    "reputation": -3,
                },
            },
        },
    },

    # ═══════════════════════════════════════════════════════════════
    #  SC-R6: GEOPOLITICAL RISK & NEARSHORING
    #  Theme: Geographic Diversification Under Pressure
    #  Key tension: Cost efficiency of global sourcing vs resilience
    #  Flag dependency: 'modern_slavery_unresolved' from SC-R2 doubles rep hit
    # ═══════════════════════════════════════════════════════════════
    6: {
        "title": "Geopolitical Risk & Nearshoring",
        "theme": "Geographic Diversification Under Pressure",
        "crisis": {
            "id": "sc_r6_geopolitical",
            "title": "The Trade War Escalation",
            "description": (
                "A major geopolitical escalation has triggered new trade sanctions "
                "and export controls on critical materials. 35% of your supply base "
                "is concentrated in affected regions. Shipping lanes are disrupted, "
                "insurance premiums have tripled, and lead times have doubled. "
                "Your CEO is demanding a 'China+1' strategy within 90 days."
            ),
            "icon": "🌍",
            "facilitator_note": (
                "If SC-R2 chose Option C (monitoring only), the 'modern_slavery_unresolved' "
                "flag means the geopolitical disruption also surfaces the unresolved "
                "labour rights issues — doubling the reputation damage for Option C. "
                "This demonstrates how deferred ethical decisions compound under "
                "geopolitical stress."
            ),
            "tyler_reference": {
                "quote": (
                    "\"Achieving genuine sustainability requires active collaboration "
                    "among diverse stakeholders, including businesses, regulators, "
                    "and consumers. No single company can do it alone.\""
                ),
                "speaker": "Olivia Tyler",
                "talk_title": "The Complex Path to Sustainability",
                "discussion_prompt": (
                    "Tyler says collaboration is non-negotiable. Is Option A "
                    "(nearshoring) an individual solution or a collaborative one? "
                    "What industry coalitions could Muressons join? If you invested "
                    "in supplier capacity building (SC-R3) AND circular procurement "
                    "(SC-R4), your suppliers are now your partners \u2014 Tyler would "
                    "call this \u2018structural collaboration\u2019."
                ),
                "source_url": "https://www.ted.com/talks/olivia_tyler_the_complex_path_to_sustainability",
            },
        },
        "special_rules": {
            "slavery_compounding": True,
            "modern_slavery_reputation_multiplier": {
                "description": "Unresolved modern slavery doubles Option C reputation penalty",
                "multiplier": 2.0,
                "applies_to": "option_c",
                "flag_required": "modern_slavery_unresolved",
            },
        },
        "options": {
            "option_a": {
                "label": "A",
                "title": "Aggressive Nearshoring Program",
                "description": (
                    "Relocate 50% of supply base to nearshore locations (Mexico, "
                    "Turkey, Poland, Vietnam) within 18 months. Build redundant "
                    "supply lines for all critical materials. Massive upfront cost "
                    "but eliminates concentration risk."
                ),
                "flags_set": ["nearshored_supply", "geographic_diversified"],
                "impacts": {
                    "treasury": -10_000_000,
                    "geopolitical_resilience": +40,
                    "supplier_risk_score": -18,
                    "carbon_intensity_delta": -5,  # Shorter transport routes
                    "reputation": +5,
                },
            },
            "option_b": {
                "label": "B",
                "title": "Dual-Sourcing for Critical Materials",
                "description": (
                    "Identify and qualify alternative suppliers for the top 10 "
                    "critical materials. Maintain existing suppliers but establish "
                    "contractual options to switch within 60 days. Moderate cost, "
                    "moderate protection."
                ),
                "flags_set": ["dual_sourcing_active"],
                "impacts": {
                    "treasury": -4_000_000,
                    "geopolitical_resilience": +20,
                    "supplier_risk_score": -8,
                    "reputation": +2,
                },
            },
            "option_c": {
                "label": "C",
                "title": "Hold & Monitor Strategy",
                "description": (
                    "Maintain existing supply base and monitor the situation. "
                    "Build inventory buffers (90-day stockpile) for critical "
                    "materials. Cheapest option but leaves concentration risk "
                    "fully exposed and ties up working capital."
                ),
                "flags_set": ["supply_concentration_risk", "inventory_buffer_only"],
                "impacts": {
                    "treasury": -2_000_000,
                    "geopolitical_resilience": +5,
                    "supplier_risk_score": +5,
                    "reputation": -5,
                    "governance_risk_delta": +5,
                },
            },
        },
    },

    # ═══════════════════════════════════════════════════════════════
    #  SC-R7: SUPPLY CHAIN RESILIENCE STRESS TEST
    #  Theme: Final Resilience Assessment
    #  Key tension: All prior decisions converge into a stress scenario
    #  Stochastic element: disruption severity based on accumulated flags
    # ═══════════════════════════════════════════════════════════════
    7: {
        "title": "Supply Chain Resilience Stress Test",
        "theme": "Final Resilience Assessment",
        "crisis": {
            "id": "sc_r7_stress_test",
            "title": "The Perfect Storm",
            "description": (
                "A Category 5 typhoon devastates a key manufacturing hub "
                "simultaneously with a cyberattack on your logistics partner's "
                "systems. Your supply chain faces a triple disruption: physical "
                "infrastructure damage, digital systems offline, and supplier "
                "financial distress cascading through your network. The board "
                "demands to know: is our supply chain resilient?"
            ),
            "icon": "🌪️",
            "facilitator_note": (
                "This is the culminating round. Disruption severity is calculated "
                "from accumulated flags: deep visibility reduces it, greenwash risk "
                "and concentration risk increase it. The stochastic element means "
                "even well-prepared teams can face significant damage — but their "
                "recovery options are much better. Debrief should focus on how "
                "cumulative investment created (or failed to create) resilience."
            ),
            "tyler_reference": {
                "quote": (
                    "\"Individuals \u2014 regardless of their role in society \u2014 have the "
                    "power to influence the market through their choices. Be conscious "
                    "of where your products come from.\""
                ),
                "speaker": "Olivia Tyler",
                "talk_title": "The Complex Path to Sustainability",
                "discussion_prompt": (
                    "Tyler\u2019s final message is about consumer empowerment. If "
                    "consumers could see your Supply Chain scorecard right now, "
                    "would they buy your products? Your Consumer Trust Index "
                    "reflects this. What grade would Tyler give your supply chain?"
                ),
                "source_url": "https://www.ted.com/talks/olivia_tyler_the_complex_path_to_sustainability",
            },
        },
        "special_rules": {
            "stochastic_disruption": True,
            "base_disruption_severity": 60,
            "disruption_modifiers": {
                "full_tier_mapping": -10,
                "sc_deep_visibility": -5,
                "blockchain_traceability_sc": -10,
                "nearshored_supply": -15,
                "dual_sourcing_active": -8,
                "supplier_capacity_building": -5,
                "circular_procurement_leader": -5,
                "sc_greenwash_risk": +10,
                "supply_concentration_risk": +15,
                "dpp_non_compliant": +8,
                "modern_slavery_unresolved": +5,
                "self_assessment_only": +5,
            },
            "stochastic_threshold": 0.65,
            "max_disruption_damage": 20_000_000,
        },
        "options": {
            "option_a": {
                "label": "A",
                "title": "Full Crisis Response & Recovery Investment",
                "description": (
                    "Deploy emergency procurement teams, activate backup suppliers, "
                    "fund supplier recovery loans, and invest in permanent resilience "
                    "infrastructure. Maximum cost, maximum protection, maximum "
                    "long-term value."
                ),
                "flags_set": ["crisis_response_full", "sc_resilient"],
                "impacts": {
                    "treasury": -12_000_000,
                    "geopolitical_resilience": +20,
                    "supplier_risk_score": -15,
                    "supply_visibility": +10,
                    "reputation": +10,
                    "social_license_delta": +8,
                },
            },
            "option_b": {
                "label": "B",
                "title": "Targeted Recovery for Critical Lines",
                "description": (
                    "Focus recovery efforts on the most revenue-critical supply "
                    "lines. Accept disruption in non-critical categories. Deploy "
                    "insurance claims for physical damage."
                ),
                "flags_set": ["crisis_response_targeted"],
                "impacts": {
                    "treasury": -5_000_000,
                    "geopolitical_resilience": +10,
                    "supplier_risk_score": -5,
                    "reputation": +3,
                },
            },
            "option_c": {
                "label": "C",
                "title": "Insurance Claim & Wait",
                "description": (
                    "File insurance claims, activate force majeure clauses, and "
                    "wait for suppliers to self-recover. Minimal investment but "
                    "extended supply disruption lasting 6–12 months. Revenue "
                    "impact is severe."
                ),
                "flags_set": ["crisis_passive_response", "supply_chain_fragile"],
                "impacts": {
                    "treasury": -1_000_000,
                    "supplier_risk_score": +10,
                    "reputation": -8,
                    "social_license_delta": -5,
                    "governance_risk_delta": +10,
                },
            },
        },
    },
}
