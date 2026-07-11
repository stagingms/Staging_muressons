"""
Muressons Simulation — Industry Master Materiality Spreadsheet Generator
==========================================================================
Generates a fully pre-populated .xlsx workbook covering all 9 industry
verticals in the BU registry. Each industry gets its own sheet tab with
10 CSRD-mapped materiality issues.

Usage (CLI):
    python generate_industry_master.py
    -> Outputs: db/industry_master_materiality.xlsx

    python generate_industry_master.py --json-dir db/industry_configs/
    -> Also writes individual JSON files per industry

    python generate_industry_master.py --list
    -> List all industries and issue counts

Each industry sheet can be saved as its own .xlsx and uploaded via:
    POST /api/admin/materiality-config/upload?scope={bu_id}

The workbook includes:
    ReadMe             - instructions and upload workflow
    {Icon} {Label}     - Issues sheet per industry
    {Icon} {Label} x   - Interdependencies sheet per industry
    PanelBiasConfig    - Panel group bias configuration reference table
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


# =============================================================================
#  INDUSTRY MASTER DATA
#  Each issue:  id, title, hover_description, category,
#               financial_impact (high/medium/low), societal_impact,
#               mitigation_cost_usd,
#               stakeholders_group, nature_of_impact,
#               interdependency_1, interdependency_2,
#               affected_bu_1, affected_bu_2
# =============================================================================

INDUSTRIES: list[dict] = [

    # =========================================================================
    {
        "bu_id":           "pharma",
        "label":           "Pharma",
        "icon":            "PH",
        "esrs_sector":     "Healthcare / Life Sciences",
        "consultant_fee_usd": 1_500_000,
        "issues": [
            {
                "id": "drug_pricing_access",
                "title": "Drug Pricing & Access",
                "hover_description": "High drug prices restrict patient access. ESRS S2/S3 community impact. Reputational risk if access gap is publicised (S&P ESG score -8%).",
                "category": "social",
                "financial_impact": "high",
                "societal_impact": "high",
                "mitigation_cost_usd": 3_000_000,
                "stakeholders_group": "NGOs; Patient Advocacy Groups",
                "nature_of_impact": "Actual negative - access inequity",
                "interdependency_1": "clinical_trials_ethics",
                "interdependency_2": "",
                "affected_bu_1": "pharma",
                "affected_bu_2": "",
            },
            {
                "id": "clinical_trials_ethics",
                "title": "Clinical Trials Ethics",
                "hover_description": "ESRS S2: risks of exploitative trials in low-income countries. Regulatory sanction risk under ICH E6 (R3) and EMA guidelines.",
                "category": "governance",
                "financial_impact": "high",
                "societal_impact": "high",
                "mitigation_cost_usd": 2_500_000,
                "stakeholders_group": "Regulators; Bioethics Committees",
                "nature_of_impact": "Potential negative - exploitative research",
                "interdependency_1": "drug_pricing_access",
                "interdependency_2": "r_and_d_ip_concentration",
                "affected_bu_1": "pharma",
                "affected_bu_2": "",
            },
            {
                "id": "pharmaceutical_waste",
                "title": "Pharmaceutical Waste in Waterways",
                "hover_description": "Active pharmaceutical ingredients (APIs) in effluents. ESRS E3 (water) - biodiversity impact. EU Pharmaceutical Strategy calls for enhanced wastewater treatment.",
                "category": "ecological",
                "financial_impact": "medium",
                "societal_impact": "high",
                "mitigation_cost_usd": 4_000_000,
                "stakeholders_group": "Environmental NGOs; Regulators",
                "nature_of_impact": "Actual negative - ecosystem contamination",
                "interdependency_1": "manufacturing_emissions",
                "interdependency_2": "",
                "affected_bu_1": "pharma",
                "affected_bu_2": "consumer_goods",
            },
            {
                "id": "manufacturing_emissions",
                "title": "Manufacturing GHG Emissions",
                "hover_description": "Pharma manufacturing is energy-intensive. Scope 1 & 2 emissions subject to EU ETS. Carbon cost exposure: EUR60-110/tCO2 by 2030.",
                "category": "ecological",
                "financial_impact": "high",
                "societal_impact": "medium",
                "mitigation_cost_usd": 5_500_000,
                "stakeholders_group": "Investors; Regulators",
                "nature_of_impact": "Actual negative - climate change contribution",
                "interdependency_1": "pharmaceutical_waste",
                "interdependency_2": "",
                "affected_bu_1": "pharma",
                "affected_bu_2": "oil_gas",
            },
            {
                "id": "r_and_d_ip_concentration",
                "title": "R&D IP Concentration & Antibiotic Resistance",
                "hover_description": "Underfunding of antibiotic R&D due to low ROI. ESRS G1 systemic risk. AMR causes 1.27M deaths/year; WHO declares global emergency.",
                "category": "governance",
                "financial_impact": "low",
                "societal_impact": "high",
                "mitigation_cost_usd": 2_000_000,
                "stakeholders_group": "WHO; Governments; Investors",
                "nature_of_impact": "Potential negative - systemic health risk",
                "interdependency_1": "drug_pricing_access",
                "interdependency_2": "",
                "affected_bu_1": "pharma",
                "affected_bu_2": "",
            },
            {
                "id": "supply_chain_labor",
                "title": "Supply Chain Labour Conditions (API Suppliers)",
                "hover_description": "API manufacturing concentrated in India & China. ESRS S2: forced labour and unsafe conditions risk in Tier-2/3 suppliers.",
                "category": "social",
                "financial_impact": "medium",
                "societal_impact": "high",
                "mitigation_cost_usd": 1_800_000,
                "stakeholders_group": "Own Workforce; NGOs",
                "nature_of_impact": "Potential negative - labour rights violations",
                "interdependency_1": "",
                "interdependency_2": "",
                "affected_bu_1": "pharma",
                "affected_bu_2": "consumer_goods",
            },
            {
                "id": "counterfeit_medicines",
                "title": "Counterfeit Medicines & Supply Chain Integrity",
                "hover_description": "10% of medicines in low-income markets are counterfeit (WHO). Patient safety risk and brand liability. ESRS G1 traceability gap.",
                "category": "governance",
                "financial_impact": "high",
                "societal_impact": "high",
                "mitigation_cost_usd": 3_200_000,
                "stakeholders_group": "Regulators; Patients",
                "nature_of_impact": "Actual negative - patient harm",
                "interdependency_1": "supply_chain_labor",
                "interdependency_2": "",
                "affected_bu_1": "pharma",
                "affected_bu_2": "",
            },
            {
                "id": "biodiversity_sourcing",
                "title": "Biodiversity Impact - Natural Compound Sourcing",
                "hover_description": "Extracting compounds from threatened species and habitats. ESRS E4 (biodiversity). CBD Nagoya Protocol compliance risk.",
                "category": "ecological",
                "financial_impact": "low",
                "societal_impact": "high",
                "mitigation_cost_usd": 1_200_000,
                "stakeholders_group": "Environmental NGOs; Communities",
                "nature_of_impact": "Actual negative - biodiversity loss",
                "interdependency_1": "pharmaceutical_waste",
                "interdependency_2": "",
                "affected_bu_1": "pharma",
                "affected_bu_2": "agriculture",
            },
            {
                "id": "pandemic_preparedness",
                "title": "Pandemic Preparedness & Vaccine Equity",
                "hover_description": "ESRS S3: Failure to provide affordable vaccines in LMIC during outbreaks. WHO Essential Medicines List pressure. IP waiver debate (TRIPS).",
                "category": "social",
                "financial_impact": "medium",
                "societal_impact": "high",
                "mitigation_cost_usd": 4_500_000,
                "stakeholders_group": "Governments; NGOs; Communities",
                "nature_of_impact": "Potential negative - health inequity",
                "interdependency_1": "drug_pricing_access",
                "interdependency_2": "r_and_d_ip_concentration",
                "affected_bu_1": "pharma",
                "affected_bu_2": "",
            },
            {
                "id": "product_safety_recalls",
                "title": "Product Safety Recalls",
                "hover_description": "Post-market safety failures trigger FDA/EMA recalls. ESRS G1: liability and governance risk. Avg. recall cost: $100M-$600M per event.",
                "category": "governance",
                "financial_impact": "high",
                "societal_impact": "high",
                "mitigation_cost_usd": 6_000_000,
                "stakeholders_group": "Regulators; Patients; Investors",
                "nature_of_impact": "Actual negative - consumer harm",
                "interdependency_1": "counterfeit_medicines",
                "interdependency_2": "",
                "affected_bu_1": "pharma",
                "affected_bu_2": "",
            },
        ],
        "interdependencies": [
            {"source_issue_id": "drug_pricing_access",   "target_issue_id": "clinical_trials_ethics", "severity": 3, "description": "Access gaps incentivise cheaper trial populations"},
            {"source_issue_id": "pharmaceutical_waste",  "target_issue_id": "manufacturing_emissions", "severity": 4, "description": "Same production process drives both water and air impact"},
            {"source_issue_id": "supply_chain_labor",    "target_issue_id": "counterfeit_medicines",   "severity": 3, "description": "Weak Tier-2 oversight enables counterfeit entry"},
        ],
    },

    # =========================================================================
    {
        "bu_id":           "electronics",
        "label":           "Electronics",
        "icon":            "EL",
        "esrs_sector":     "Technology Hardware / Semiconductors",
        "consultant_fee_usd": 1_500_000,
        "issues": [
            {
                "id": "e_waste_recycling",
                "title": "E-Waste & WEEE Compliance",
                "hover_description": "53.6Mt of e-waste generated globally (2019). ESRS E5 (circular economy). EU WEEE Directive requires 65% collection rate.",
                "category": "ecological",
                "financial_impact": "high",
                "societal_impact": "high",
                "mitigation_cost_usd": 4_000_000,
                "stakeholders_group": "Regulators; Environmental NGOs",
                "nature_of_impact": "Actual negative - toxic landfill",
                "interdependency_1": "conflict_minerals",
                "interdependency_2": "product_lifespan",
                "affected_bu_1": "electronics",
                "affected_bu_2": "consumer_goods",
            },
            {
                "id": "conflict_minerals",
                "title": "Conflict Minerals (3TG) in Supply Chain",
                "hover_description": "Tin, tantalum, tungsten, gold from DRC conflict zones. ESRS S2: human rights due diligence. EU Conflict Minerals Regulation (2021) compliance.",
                "category": "social",
                "financial_impact": "high",
                "societal_impact": "high",
                "mitigation_cost_usd": 2_800_000,
                "stakeholders_group": "NGOs; Governments; Investors",
                "nature_of_impact": "Actual negative - conflict financing",
                "interdependency_1": "e_waste_recycling",
                "interdependency_2": "",
                "affected_bu_1": "electronics",
                "affected_bu_2": "",
            },
            {
                "id": "semiconductor_supply_risk",
                "title": "Semiconductor Supply Chain Concentration",
                "hover_description": "85% of advanced chips from TSMC (Taiwan). ESRS G1 systemic risk. US-China decoupling creates capital expenditure decisions in the billions.",
                "category": "economic",
                "financial_impact": "high",
                "societal_impact": "low",
                "mitigation_cost_usd": 8_000_000,
                "stakeholders_group": "Investors; Governments",
                "nature_of_impact": "Potential negative - supply disruption",
                "interdependency_1": "",
                "interdependency_2": "",
                "affected_bu_1": "electronics",
                "affected_bu_2": "software",
            },
            {
                "id": "product_lifespan",
                "title": "Planned Obsolescence & Right to Repair",
                "hover_description": "EU Right to Repair Directive (2024) mandates 5-10yr spare parts. ESRS E5: circular economy failure. Consumer trust and brand risk.",
                "category": "governance",
                "financial_impact": "medium",
                "societal_impact": "high",
                "mitigation_cost_usd": 3_000_000,
                "stakeholders_group": "Consumers; Regulators",
                "nature_of_impact": "Actual negative - resource waste",
                "interdependency_1": "e_waste_recycling",
                "interdependency_2": "",
                "affected_bu_1": "electronics",
                "affected_bu_2": "consumer_goods",
            },
            {
                "id": "factory_labor_osh",
                "title": "Factory Worker Safety (OSH)",
                "hover_description": "ESRS S1: Occupational health risks in electronics manufacturing (chemical exposure, repetitive strain). ILO Convention 155 compliance.",
                "category": "social",
                "financial_impact": "medium",
                "societal_impact": "high",
                "mitigation_cost_usd": 2_200_000,
                "stakeholders_group": "Own Workforce; Trade Unions",
                "nature_of_impact": "Actual negative - worker harm",
                "interdependency_1": "conflict_minerals",
                "interdependency_2": "",
                "affected_bu_1": "electronics",
                "affected_bu_2": "",
            },
            {
                "id": "data_center_energy",
                "title": "Data Centre & Device Energy Consumption",
                "hover_description": "Electronics supply 2% of global GHG (equal to aviation). ESRS E1: Scope 3 use-phase emissions. RE100 and EU Green Deal pressure.",
                "category": "ecological",
                "financial_impact": "high",
                "societal_impact": "medium",
                "mitigation_cost_usd": 5_000_000,
                "stakeholders_group": "Investors; Regulators",
                "nature_of_impact": "Actual negative - climate contribution",
                "interdependency_1": "",
                "interdependency_2": "",
                "affected_bu_1": "electronics",
                "affected_bu_2": "software",
            },
            {
                "id": "rare_earth_dependency",
                "title": "Rare Earth Element Dependency",
                "hover_description": "China controls 85% of REE production. ESRS E5 resource security. EU Critical Raw Materials Act identifies 34 critical raw materials.",
                "category": "ecological",
                "financial_impact": "high",
                "societal_impact": "medium",
                "mitigation_cost_usd": 3_500_000,
                "stakeholders_group": "Investors; Governments",
                "nature_of_impact": "Potential negative - resource depletion",
                "interdependency_1": "conflict_minerals",
                "interdependency_2": "e_waste_recycling",
                "affected_bu_1": "electronics",
                "affected_bu_2": "agriculture",
            },
            {
                "id": "ai_bias_electronics",
                "title": "AI Bias in Consumer Devices",
                "hover_description": "Facial recognition and AI features in consumer electronics discriminate by race/gender. ESRS S2: human rights. EU AI Act Art. 10 high-risk classification.",
                "category": "social",
                "financial_impact": "medium",
                "societal_impact": "high",
                "mitigation_cost_usd": 1_800_000,
                "stakeholders_group": "NGOs; Regulators; Communities",
                "nature_of_impact": "Actual negative - discrimination",
                "interdependency_1": "",
                "interdependency_2": "",
                "affected_bu_1": "electronics",
                "affected_bu_2": "software",
            },
            {
                "id": "packaging_plastics",
                "title": "Plastic Packaging Reduction",
                "hover_description": "Single-use plastics in electronics packaging. ESRS E5: EU SUP Directive and EPR obligations. 70% of consumers prefer eco-packaging (GfK 2023).",
                "category": "ecological",
                "financial_impact": "medium",
                "societal_impact": "medium",
                "mitigation_cost_usd": 1_200_000,
                "stakeholders_group": "Consumers; Regulators",
                "nature_of_impact": "Actual negative - plastic pollution",
                "interdependency_1": "e_waste_recycling",
                "interdependency_2": "",
                "affected_bu_1": "electronics",
                "affected_bu_2": "retail_fmcg",
            },
            {
                "id": "cybersecurity_product",
                "title": "Product Cybersecurity Vulnerabilities",
                "hover_description": "IoT devices with weak security. EU Cyber Resilience Act (2024) requires security-by-design. Avg. breach cost: $4.5M. ESRS G1 governance gap.",
                "category": "governance",
                "financial_impact": "high",
                "societal_impact": "high",
                "mitigation_cost_usd": 4_500_000,
                "stakeholders_group": "Consumers; Regulators; Investors",
                "nature_of_impact": "Potential negative - data breach",
                "interdependency_1": "ai_bias_electronics",
                "interdependency_2": "",
                "affected_bu_1": "electronics",
                "affected_bu_2": "software",
            },
        ],
        "interdependencies": [
            {"source_issue_id": "e_waste_recycling",  "target_issue_id": "rare_earth_dependency",    "severity": 5, "description": "Recycling REEs from e-waste reduces virgin mining dependency"},
            {"source_issue_id": "conflict_minerals",  "target_issue_id": "factory_labor_osh",         "severity": 3, "description": "Weak supply chain governance exposes all labour tiers"},
            {"source_issue_id": "data_center_energy", "target_issue_id": "semiconductor_supply_risk", "severity": 2, "description": "Energy demand drives chip innovation and supply pressure"},
        ],
    },

    # =========================================================================
    {
        "bu_id":           "consumer_goods",
        "label":           "Consumer Goods",
        "icon":            "CG",
        "esrs_sector":     "Consumer Staples / FMCG",
        "consultant_fee_usd": 1_500_000,
        "issues": [
            {"id": "plastic_packaging_cg", "title": "Single-Use Plastic Packaging", "hover_description": "ESRS E5: 8Mt of plastics enter oceans annually. EU SUP Directive bans 10 categories. EPR fees up to 5% of packaging revenue.", "category": "ecological", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 3_500_000, "stakeholders_group": "Consumers; NGOs; Regulators", "nature_of_impact": "Actual negative - ocean pollution", "interdependency_1": "consumer_recycling_rates", "interdependency_2": "", "affected_bu_1": "consumer_goods", "affected_bu_2": "retail_fmcg"},
            {"id": "consumer_recycling_rates", "title": "Consumer Recycling Infrastructure Gap", "hover_description": "Only 14% of plastic packaging recycled globally. ESRS E5 circular economy obligation. Gap between producer responsibility and consumer behaviour.", "category": "ecological", "financial_impact": "medium", "societal_impact": "medium", "mitigation_cost_usd": 2_000_000, "stakeholders_group": "NGOs; Local Governments", "nature_of_impact": "Potential negative - waste accumulation", "interdependency_1": "plastic_packaging_cg", "interdependency_2": "", "affected_bu_1": "consumer_goods", "affected_bu_2": ""},
            {"id": "palm_oil_deforestation", "title": "Palm Oil & Deforestation in Supply Chain", "hover_description": "ESRS E4: 300 football fields of rainforest cleared daily for palm oil. EU Deforestation Regulation (2023) due diligence. 80% of consumer goods contain palm oil.", "category": "ecological", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 4_200_000, "stakeholders_group": "Environmental NGOs; Investors", "nature_of_impact": "Actual negative - deforestation/biodiversity", "interdependency_1": "", "interdependency_2": "", "affected_bu_1": "consumer_goods", "affected_bu_2": "agriculture"},
            {"id": "greenwashing_risk", "title": "Greenwashing & Green Claims", "hover_description": "EU Green Claims Directive (2024): substantiation of eco-labels required. 53% of green claims were found vague or false (EU Commission). ESRS G1.", "category": "governance", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 1_500_000, "stakeholders_group": "Regulators; Consumers; Investors", "nature_of_impact": "Potential negative - consumer deception", "interdependency_1": "plastic_packaging_cg", "interdependency_2": "palm_oil_deforestation", "affected_bu_1": "consumer_goods", "affected_bu_2": "retail_fmcg"},
            {"id": "obesity_nutrition", "title": "Obesity & Ultra-Processed Food Impact", "hover_description": "ESRS S2/S3: ultra-processed food linked to obesity pandemic (38% of adults globally overweight). WHO SHAKE initiative and front-of-pack labelling regulation.", "category": "social", "financial_impact": "medium", "societal_impact": "high", "mitigation_cost_usd": 3_000_000, "stakeholders_group": "Consumers; NGOs; Governments", "nature_of_impact": "Actual negative - public health harm", "interdependency_1": "", "interdependency_2": "", "affected_bu_1": "consumer_goods", "affected_bu_2": "retail_fmcg"},
            {"id": "living_wage_cg", "title": "Living Wage in Agricultural Supply Chains", "hover_description": "ESRS S2: 70% of global food workers earn below living wage. Tesco, Unilever Living Wage commitments. Supply chain traceability under EU CSDDD.", "category": "social", "financial_impact": "medium", "societal_impact": "high", "mitigation_cost_usd": 2_800_000, "stakeholders_group": "NGOs; Trade Unions; Investors", "nature_of_impact": "Actual negative - income inequity", "interdependency_1": "palm_oil_deforestation", "interdependency_2": "", "affected_bu_1": "consumer_goods", "affected_bu_2": "agriculture"},
            {"id": "water_use_food", "title": "Water Consumption in Food Production", "hover_description": "Agriculture consumes 70% of global freshwater. ESRS E3: water risk in water-stressed regions. CDP Water Security risk assessment mandated.", "category": "ecological", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 3_800_000, "stakeholders_group": "NGOs; Local Communities; Investors", "nature_of_impact": "Actual negative - water depletion", "interdependency_1": "palm_oil_deforestation", "interdependency_2": "", "affected_bu_1": "consumer_goods", "affected_bu_2": "agriculture"},
            {"id": "food_waste", "title": "Food Waste Across Value Chain", "hover_description": "1/3 of all food produced is wasted (FAO). ESRS E5: circular economy target. EU Farm-to-Fork Strategy 50% waste reduction by 2030.", "category": "ecological", "financial_impact": "medium", "societal_impact": "medium", "mitigation_cost_usd": 2_500_000, "stakeholders_group": "Consumers; Retailers; NGOs", "nature_of_impact": "Actual negative - resource waste + emissions", "interdependency_1": "", "interdependency_2": "", "affected_bu_1": "consumer_goods", "affected_bu_2": "retail_fmcg"},
            {"id": "product_safety_cg", "title": "Product Safety & Chemical Compliance", "hover_description": "REACH, SVHC restrictions on hazardous substances in consumer products. ESRS G1. Recall costs average $10M per incident. PFAS ban in 2025.", "category": "governance", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 4_000_000, "stakeholders_group": "Regulators; Consumers", "nature_of_impact": "Actual negative - consumer harm", "interdependency_1": "", "interdependency_2": "", "affected_bu_1": "consumer_goods", "affected_bu_2": "pharma"},
            {"id": "scope3_upstream", "title": "Scope 3 Upstream Emissions", "hover_description": "80-90% of FMCG GHG in value chain (Scope 3 Cat 1). ESRS E1: SBTi 1.5C alignment requires supply chain decarbonisation. CDP Supply Chain programme.", "category": "ecological", "financial_impact": "high", "societal_impact": "medium", "mitigation_cost_usd": 5_000_000, "stakeholders_group": "Investors; Regulators; Suppliers", "nature_of_impact": "Actual negative - climate change", "interdependency_1": "palm_oil_deforestation", "interdependency_2": "water_use_food", "affected_bu_1": "consumer_goods", "affected_bu_2": "agriculture"},
        ],
        "interdependencies": [
            {"source_issue_id": "palm_oil_deforestation", "target_issue_id": "scope3_upstream",    "severity": 5, "description": "Land-use change is biggest Scope 3 driver in food"},
            {"source_issue_id": "greenwashing_risk",      "target_issue_id": "plastic_packaging_cg","severity": 3, "description": "Green claims on packaging trigger most scrutiny"},
            {"source_issue_id": "food_waste",             "target_issue_id": "water_use_food",      "severity": 4, "description": "Wasted food equals wasted water embedded in production"},
        ],
    },

    # =========================================================================
    {
        "bu_id":           "software",
        "label":           "Software",
        "icon":            "SW",
        "esrs_sector":     "Information Technology / SaaS",
        "consultant_fee_usd": 1_500_000,
        "issues": [
            {"id": "data_privacy_gdpr", "title": "Data Privacy & GDPR Compliance", "hover_description": "ESRS S2: GDPR Art. 83 - fines up to EUR20M or 4% global turnover. 2023 EU fines: EUR1.4B total. Consumer trust: NPS drops 18pts after breach.", "category": "social", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 2_500_000, "stakeholders_group": "Consumers; Regulators; Investors", "nature_of_impact": "Actual negative - privacy violation", "interdependency_1": "cybersecurity_sw", "interdependency_2": "ai_fairness", "affected_bu_1": "software", "affected_bu_2": "electronics"},
            {"id": "cybersecurity_sw", "title": "Cybersecurity & Ransomware Risk", "hover_description": "ESRS G1: Average ransomware payment $1.5M (2023). NIS2 Directive mandates 24h incident reporting. Critical infrastructure exposure.", "category": "governance", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 4_000_000, "stakeholders_group": "Regulators; Investors; Customers", "nature_of_impact": "Potential negative - operational disruption", "interdependency_1": "data_privacy_gdpr", "interdependency_2": "", "affected_bu_1": "software", "affected_bu_2": "banking_financial_services"},
            {"id": "ai_fairness", "title": "AI Fairness & Algorithmic Bias", "hover_description": "ESRS S2: EU AI Act High-Risk classification (hiring, credit, healthcare AI). Algorithmic bias litigation risk. Model cards and impact assessments mandatory.", "category": "social", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 3_000_000, "stakeholders_group": "NGOs; Regulators; Communities", "nature_of_impact": "Actual negative - discrimination", "interdependency_1": "data_privacy_gdpr", "interdependency_2": "", "affected_bu_1": "software", "affected_bu_2": "banking_financial_services"},
            {"id": "digital_divide", "title": "Digital Divide & Access Inequity", "hover_description": "ESRS S3: 2.7B people lack internet access. SaaS pricing and accessibility barriers. EU Web Accessibility Directive. UN SDG 10 - reduce inequality.", "category": "social", "financial_impact": "low", "societal_impact": "high", "mitigation_cost_usd": 1_500_000, "stakeholders_group": "NGOs; Communities; Governments", "nature_of_impact": "Potential negative - exclusion", "interdependency_1": "", "interdependency_2": "", "affected_bu_1": "software", "affected_bu_2": ""},
            {"id": "energy_data_centers_sw", "title": "Data Centre Energy & Carbon Footprint", "hover_description": "Data centres consume 2% of global electricity. ESRS E1: Scope 2 + Scope 3 Cat 11 (use of sold products). Hyperscaler PPA commitments under pressure.", "category": "ecological", "financial_impact": "high", "societal_impact": "medium", "mitigation_cost_usd": 5_000_000, "stakeholders_group": "Investors; Regulators", "nature_of_impact": "Actual negative - climate contribution", "interdependency_1": "", "interdependency_2": "", "affected_bu_1": "software", "affected_bu_2": "electronics"},
            {"id": "worker_surveillance", "title": "Remote Worker Surveillance & Autonomy", "hover_description": "ESRS S1: 78% of companies use employee monitoring software (ExpressVPN 2023). Erosion of trust and autonomy. EU AI Act workplace monitoring provisions.", "category": "social", "financial_impact": "medium", "societal_impact": "high", "mitigation_cost_usd": 1_200_000, "stakeholders_group": "Own Workforce; Trade Unions", "nature_of_impact": "Actual negative - dignity/autonomy violation", "interdependency_1": "data_privacy_gdpr", "interdependency_2": "", "affected_bu_1": "software", "affected_bu_2": ""},
            {"id": "platform_monopoly", "title": "Platform Monopoly & Market Concentration", "hover_description": "ESRS G1: EU Digital Markets Act designates GAFA as gatekeepers. Antitrust fines: EUR4.3B (Google, 2022). Market foreclosure harms SME competitors.", "category": "governance", "financial_impact": "high", "societal_impact": "medium", "mitigation_cost_usd": 2_000_000, "stakeholders_group": "Regulators; Competitors; SMEs", "nature_of_impact": "Actual negative - market exclusion", "interdependency_1": "digital_divide", "interdependency_2": "", "affected_bu_1": "software", "affected_bu_2": ""},
            {"id": "open_source_dependency", "title": "Open Source Dependency Risk", "hover_description": "96% of codebases contain open source (Synopsys 2023). Log4Shell-style vulnerabilities propagate instantly. EU Cyber Resilience Act OSS provisions.", "category": "governance", "financial_impact": "high", "societal_impact": "low", "mitigation_cost_usd": 1_800_000, "stakeholders_group": "Investors; Developers; Regulators", "nature_of_impact": "Potential negative - systemic vulnerability", "interdependency_1": "cybersecurity_sw", "interdependency_2": "", "affected_bu_1": "software", "affected_bu_2": "electronics"},
            {"id": "digital_addiction", "title": "Digital Addiction & Mental Health Impact", "hover_description": "ESRS S3: social media linked to depression in adolescents. UK Online Safety Act. Platform design features (dark patterns, infinite scroll) as intentional harm.", "category": "social", "financial_impact": "medium", "societal_impact": "high", "mitigation_cost_usd": 2_200_000, "stakeholders_group": "Consumers; NGOs; Governments", "nature_of_impact": "Actual negative - mental health harm", "interdependency_1": "digital_divide", "interdependency_2": "", "affected_bu_1": "software", "affected_bu_2": ""},
            {"id": "ai_hallucinations", "title": "AI Hallucinations & Misinformation Risk", "hover_description": "ESRS G1/S3: LLM hallucination in healthcare/legal contexts creates liability. EU AI Act transparency requirements. Trust erosion if not addressed.", "category": "governance", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 3_500_000, "stakeholders_group": "Customers; Regulators; Media", "nature_of_impact": "Potential negative - decision harm", "interdependency_1": "ai_fairness", "interdependency_2": "cybersecurity_sw", "affected_bu_1": "software", "affected_bu_2": "banking_financial_services"},
        ],
        "interdependencies": [
            {"source_issue_id": "ai_fairness",       "target_issue_id": "data_privacy_gdpr",     "severity": 4, "description": "Bias often emerges from unlawful data use"},
            {"source_issue_id": "cybersecurity_sw",  "target_issue_id": "open_source_dependency", "severity": 5, "description": "OSS vulnerabilities are primary cybersecurity attack vector"},
            {"source_issue_id": "digital_addiction", "target_issue_id": "ai_fairness",            "severity": 3, "description": "Engagement algorithms that maximise time amplify bias"},
        ],
    },

    # =========================================================================
    {
        "bu_id":           "oil_gas",
        "label":           "Oil & Gas",
        "icon":            "OG",
        "esrs_sector":     "Energy / Extractives",
        "consultant_fee_usd": 1_500_000,
        "issues": [
            {"id": "stranded_assets", "title": "Stranded Asset Risk - Fossil Fuel Reserves", "hover_description": "ESRS E1/G1: IEA Net Zero scenario - no new O&G fields approved after 2021. Carbon bubble: $1-4T in stranded assets. TCFD transition risk.", "category": "economic", "financial_impact": "high", "societal_impact": "low", "mitigation_cost_usd": 10_000_000, "stakeholders_group": "Investors; Governments", "nature_of_impact": "Potential negative - systemic financial risk", "interdependency_1": "scope1_methane", "interdependency_2": "just_transition", "affected_bu_1": "oil_gas", "affected_bu_2": "banking_financial_services"},
            {"id": "scope1_methane", "title": "Methane & Scope 1 Emissions", "hover_description": "Methane 80x more potent than CO2 over 20 years. ESRS E1: EU Methane Regulation (2024) requires monitoring and repair. Flaring reduction commitments.", "category": "ecological", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 7_000_000, "stakeholders_group": "Regulators; Environmental NGOs; Investors", "nature_of_impact": "Actual negative - climate acceleration", "interdependency_1": "stranded_assets", "interdependency_2": "", "affected_bu_1": "oil_gas", "affected_bu_2": ""},
            {"id": "biodiversity_og", "title": "Biodiversity Loss from Extraction Sites", "hover_description": "ESRS E4: Oil spills destroy marine and terrestrial ecosystems. Deepwater Horizon cost: $65B. EU Nature Restoration Law - no-net-loss obligation.", "category": "ecological", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 8_000_000, "stakeholders_group": "NGOs; Communities; Governments", "nature_of_impact": "Actual negative - biodiversity destruction", "interdependency_1": "scope1_methane", "interdependency_2": "", "affected_bu_1": "oil_gas", "affected_bu_2": ""},
            {"id": "just_transition", "title": "Just Transition for Workers & Communities", "hover_description": "ESRS S1/S3: 12M direct fossil fuel jobs at risk by 2030 (IEA). EU Just Transition Mechanism. Community dependency on extraction revenue in LMIC.", "category": "social", "financial_impact": "medium", "societal_impact": "high", "mitigation_cost_usd": 5_000_000, "stakeholders_group": "Own Workforce; Communities; Governments", "nature_of_impact": "Potential negative - socioeconomic disruption", "interdependency_1": "stranded_assets", "interdependency_2": "", "affected_bu_1": "oil_gas", "affected_bu_2": "agriculture"},
            {"id": "water_contamination", "title": "Water Contamination from Extraction", "hover_description": "ESRS E3: Hydraulic fracturing contaminates groundwater. Produced water disposal risk. Communities near extraction sites face health impacts.", "category": "ecological", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 6_000_000, "stakeholders_group": "Communities; Regulators; NGOs", "nature_of_impact": "Actual negative - water/health impact", "interdependency_1": "biodiversity_og", "interdependency_2": "", "affected_bu_1": "oil_gas", "affected_bu_2": ""},
            {"id": "energy_security_price", "title": "Energy Security & Price Volatility", "hover_description": "ESRS G1: Geopolitical disruptions cause extreme energy price swings (2022 gas crisis). Energy security as dual-use argument for fossil fuel continuation.", "category": "economic", "financial_impact": "high", "societal_impact": "medium", "mitigation_cost_usd": 4_000_000, "stakeholders_group": "Governments; Investors; Consumers", "nature_of_impact": "Actual negative - social price burden", "interdependency_1": "stranded_assets", "interdependency_2": "", "affected_bu_1": "oil_gas", "affected_bu_2": "banking_financial_services"},
            {"id": "indigenous_rights", "title": "Indigenous Peoples Rights & FPIC", "hover_description": "ESRS S3: Free, Prior and Informed Consent (FPIC) under UNDRIP. Pipeline projects on ancestral lands trigger legal injunctions. CSDDD Art. 6 obligations.", "category": "social", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 3_500_000, "stakeholders_group": "Indigenous Communities; NGOs; Regulators", "nature_of_impact": "Actual negative - rights violation", "interdependency_1": "biodiversity_og", "interdependency_2": "just_transition", "affected_bu_1": "oil_gas", "affected_bu_2": "agriculture"},
            {"id": "refinery_air_quality", "title": "Refinery Air Quality & Local Pollution", "hover_description": "ESRS E2: NOx, SOx, PM2.5 from refineries causes respiratory illness in nearby communities. EU Industrial Emissions Directive (IED) revision 2024.", "category": "ecological", "financial_impact": "medium", "societal_impact": "high", "mitigation_cost_usd": 4_500_000, "stakeholders_group": "Communities; Regulators; Own Workforce", "nature_of_impact": "Actual negative - health harm", "interdependency_1": "scope1_methane", "interdependency_2": "", "affected_bu_1": "oil_gas", "affected_bu_2": ""},
            {"id": "greenwashing_og", "title": "Greenwashing - Net Zero Pledges", "hover_description": "ESRS G1: Major O&G companies net zero pledges rated insufficient by Climate Action 100+. EU Green Claims Directive and potential litigation (ClientEarth vs. Shell).", "category": "governance", "financial_impact": "high", "societal_impact": "medium", "mitigation_cost_usd": 2_000_000, "stakeholders_group": "Investors; Regulators; NGOs", "nature_of_impact": "Actual negative - investor/consumer deception", "interdependency_1": "stranded_assets", "interdependency_2": "scope1_methane", "affected_bu_1": "oil_gas", "affected_bu_2": ""},
            {"id": "corruption_og", "title": "Corruption & Bribery in Resource Extraction", "hover_description": "ESRS G1: O&G sector highest bribery risk (Transparency International). FCPA, UK Bribery Act penalties. Resource curse - weak governance in extraction nations.", "category": "governance", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 3_000_000, "stakeholders_group": "Governments; Investors; NGOs", "nature_of_impact": "Actual negative - governance failure", "interdependency_1": "indigenous_rights", "interdependency_2": "", "affected_bu_1": "oil_gas", "affected_bu_2": "banking_financial_services"},
        ],
        "interdependencies": [
            {"source_issue_id": "stranded_assets",   "target_issue_id": "just_transition",     "severity": 5, "description": "Asset retirement timeline determines workforce transition urgency"},
            {"source_issue_id": "scope1_methane",    "target_issue_id": "refinery_air_quality", "severity": 4, "description": "Combustion drives both climate and local air quality"},
            {"source_issue_id": "indigenous_rights", "target_issue_id": "biodiversity_og",      "severity": 4, "description": "Indigenous land rights protect high-biodiversity ecosystems"},
        ],
    },

    # =========================================================================
    {
        "bu_id":           "banking_financial_services",
        "label":           "Banking & Financial Services",
        "icon":            "BFS",
        "esrs_sector":     "Financial Services / Asset Management",
        "consultant_fee_usd": 1_500_000,
        "issues": [
            {"id": "climate_financed_emissions", "title": "Financed Emissions (Scope 3 Cat 15)", "hover_description": "ESRS E1: Banks financed emissions 700x larger than own ops. PCAF Standard for financed emission measurement. Science-Based Targets for FIs (SBTi-FI).", "category": "ecological", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 5_000_000, "stakeholders_group": "Investors; Regulators; NGOs", "nature_of_impact": "Actual negative - climate acceleration", "interdependency_1": "stranded_asset_loans", "interdependency_2": "", "affected_bu_1": "banking_financial_services", "affected_bu_2": "oil_gas"},
            {"id": "stranded_asset_loans", "title": "Stranded Asset Exposure in Loan Books", "hover_description": "ESRS E1: ECB economy wide climate stress test - 30% NPL increase under 3C scenario. NGFS transition risk scenarios. Fossil fuel loan cliff edge.", "category": "economic", "financial_impact": "high", "societal_impact": "low", "mitigation_cost_usd": 8_000_000, "stakeholders_group": "Investors; Regulators; Shareholders", "nature_of_impact": "Potential negative - financial systemic risk", "interdependency_1": "climate_financed_emissions", "interdependency_2": "", "affected_bu_1": "banking_financial_services", "affected_bu_2": "oil_gas"},
            {"id": "financial_inclusion", "title": "Financial Inclusion & Unbanked Population", "hover_description": "ESRS S3: 1.7B adults unbanked globally. EU Payment Services Directive 3. Digital banking can extend access but risks widening digital divide.", "category": "social", "financial_impact": "low", "societal_impact": "high", "mitigation_cost_usd": 2_500_000, "stakeholders_group": "NGOs; Communities; Governments", "nature_of_impact": "Potential negative - economic exclusion", "interdependency_1": "", "interdependency_2": "", "affected_bu_1": "banking_financial_services", "affected_bu_2": ""},
            {"id": "aml_governance", "title": "Anti-Money Laundering & Financial Crime", "hover_description": "ESRS G1: EUR800B+ in laundered money annually (UNODC). EU 6th AML Directive. Fines: Danske Bank EUR1.8B, Santander EUR108M. Reputational collapse risk.", "category": "governance", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 6_000_000, "stakeholders_group": "Regulators; Governments; Investors", "nature_of_impact": "Actual negative - enabling criminal harm", "interdependency_1": "", "interdependency_2": "", "affected_bu_1": "banking_financial_services", "affected_bu_2": ""},
            {"id": "predatory_lending", "title": "Predatory Lending & Consumer Debt", "hover_description": "ESRS S2/S3: Payday loans, revolving credit trap vulnerable households. EU Consumer Credit Directive revision. Interest rate caps and affordability testing.", "category": "social", "financial_impact": "medium", "societal_impact": "high", "mitigation_cost_usd": 2_000_000, "stakeholders_group": "Consumers; NGOs; Regulators", "nature_of_impact": "Actual negative - financial harm", "interdependency_1": "financial_inclusion", "interdependency_2": "", "affected_bu_1": "banking_financial_services", "affected_bu_2": ""},
            {"id": "cybersecurity_banking", "title": "Cybersecurity & Systemic Financial Risk", "hover_description": "ESRS G1: Bank cyberattacks increasing 238% (VMware 2023). DORA regulation (2025) mandatory for EU financial entities. Average breach: $5.9M.", "category": "governance", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 5_500_000, "stakeholders_group": "Regulators; Customers; Investors", "nature_of_impact": "Potential negative - systemic disruption", "interdependency_1": "", "interdependency_2": "", "affected_bu_1": "banking_financial_services", "affected_bu_2": "software"},
            {"id": "esg_investment_integrity", "title": "ESG Fund Integrity & Label Greenwashing", "hover_description": "ESRS G1: SFDR Art. 9 downgrades (EUR195B reclassified in 2023). EU ESG Rating Regulation (2024). Greenwashing litigation risk for fund managers.", "category": "governance", "financial_impact": "high", "societal_impact": "medium", "mitigation_cost_usd": 2_200_000, "stakeholders_group": "Investors; Regulators; End-investors", "nature_of_impact": "Actual negative - investor deception", "interdependency_1": "stranded_asset_loans", "interdependency_2": "climate_financed_emissions", "affected_bu_1": "banking_financial_services", "affected_bu_2": ""},
            {"id": "exec_pay_inequality", "title": "Executive Pay & Internal Pay Ratio", "hover_description": "ESRS S1: CEO-to-median worker pay ratio: 350:1 (US), 120:1 (EU). EU Pay Transparency Directive (2026). Shareholder activism on remuneration.", "category": "social", "financial_impact": "medium", "societal_impact": "high", "mitigation_cost_usd": 1_500_000, "stakeholders_group": "Own Workforce; Shareholders; NGOs", "nature_of_impact": "Potential negative - income inequality", "interdependency_1": "", "interdependency_2": "", "affected_bu_1": "banking_financial_services", "affected_bu_2": ""},
            {"id": "pension_deficit", "title": "Pension Fund Climate Misalignment", "hover_description": "ESRS E1: Pension funds investments misaligned with Paris Agreement. IORP II Directive: ESG integration mandatory. Beneficiary exposure to transition risk.", "category": "economic", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 4_000_000, "stakeholders_group": "Beneficiaries; Regulators; NGOs", "nature_of_impact": "Potential negative - retirement insecurity", "interdependency_1": "stranded_asset_loans", "interdependency_2": "esg_investment_integrity", "affected_bu_1": "banking_financial_services", "affected_bu_2": ""},
            {"id": "nature_related_risk", "title": "Nature-Related Financial Risk (TNFD)", "hover_description": "ESRS E4: TNFD framework released 2023. 55% of global GDP depends on nature. Biodiversity loss creates loan default risk (pollinator collapse -> agriculture).", "category": "ecological", "financial_impact": "high", "societal_impact": "medium", "mitigation_cost_usd": 3_000_000, "stakeholders_group": "Investors; Regulators; NGOs", "nature_of_impact": "Potential negative - biodiversity-driven financial risk", "interdependency_1": "climate_financed_emissions", "interdependency_2": "", "affected_bu_1": "banking_financial_services", "affected_bu_2": "agriculture"},
        ],
        "interdependencies": [
            {"source_issue_id": "climate_financed_emissions", "target_issue_id": "stranded_asset_loans",  "severity": 5, "description": "Financed emissions create the very assets that will be stranded"},
            {"source_issue_id": "aml_governance",             "target_issue_id": "cybersecurity_banking",  "severity": 3, "description": "Weak AML systems are exploited via cyber breaches"},
            {"source_issue_id": "esg_investment_integrity",   "target_issue_id": "nature_related_risk",    "severity": 4, "description": "Biodiversity risk is the next major ESG disclosure category"},
        ],
    },

    # =========================================================================
    {
        "bu_id":           "retail_fmcg",
        "label":           "Retail / FMCG",
        "icon":            "RT",
        "esrs_sector":     "Retail / Consumer Distribution",
        "consultant_fee_usd": 1_500_000,
        "issues": [
            {"id": "fast_fashion_waste", "title": "Fast Fashion & Textile Waste", "hover_description": "ESRS E5: 92M tons of textile waste/year. EU Textile Strategy (2030): mandatory recycled content and design-for-durability. EPR for textiles from 2025.", "category": "ecological", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 4_000_000, "stakeholders_group": "Consumers; NGOs; Regulators", "nature_of_impact": "Actual negative - resource waste", "interdependency_1": "garment_worker_wages", "interdependency_2": "", "affected_bu_1": "retail_fmcg", "affected_bu_2": "consumer_goods"},
            {"id": "garment_worker_wages", "title": "Garment Worker Living Wages", "hover_description": "ESRS S2: 80M garment workers; 98% earn below living wage. EU CSDDD due diligence on Tier-1-3 suppliers. Rana Plaza legacy - structural audit gaps.", "category": "social", "financial_impact": "medium", "societal_impact": "high", "mitigation_cost_usd": 3_200_000, "stakeholders_group": "NGOs; Trade Unions; Investors", "nature_of_impact": "Actual negative - labour exploitation", "interdependency_1": "fast_fashion_waste", "interdependency_2": "", "affected_bu_1": "retail_fmcg", "affected_bu_2": "consumer_goods"},
            {"id": "food_miles_logistics", "title": "Food Miles & Logistics Emissions", "hover_description": "ESRS E1: Last-mile delivery and cold chain represent 40% of FMCG Scope 3. EU Clean Vehicles Directive. Net-zero delivery commitments vs. reality.", "category": "ecological", "financial_impact": "medium", "societal_impact": "medium", "mitigation_cost_usd": 3_500_000, "stakeholders_group": "Investors; Regulators; Consumers", "nature_of_impact": "Actual negative - logistics climate impact", "interdependency_1": "", "interdependency_2": "", "affected_bu_1": "retail_fmcg", "affected_bu_2": "consumer_goods"},
            {"id": "retail_labour_precarity", "title": "Retail Worker Zero-Hours & Precarity", "hover_description": "ESRS S1: 70% of retail workers on variable hours (Eurofound 2023). EU Transparent & Predictable Working Conditions Directive - minimum notice periods.", "category": "social", "financial_impact": "medium", "societal_impact": "high", "mitigation_cost_usd": 2_000_000, "stakeholders_group": "Own Workforce; Trade Unions", "nature_of_impact": "Actual negative - income insecurity", "interdependency_1": "", "interdependency_2": "", "affected_bu_1": "retail_fmcg", "affected_bu_2": ""},
            {"id": "dark_pattern_ecommerce", "title": "Dark Patterns in E-Commerce", "hover_description": "ESRS G1: EU Digital Services Act bans manipulative design. 97% of top websites use at least one dark pattern (2022 study). Consumer deception at scale.", "category": "governance", "financial_impact": "medium", "societal_impact": "high", "mitigation_cost_usd": 1_500_000, "stakeholders_group": "Consumers; Regulators", "nature_of_impact": "Actual negative - consumer manipulation", "interdependency_1": "", "interdependency_2": "", "affected_bu_1": "retail_fmcg", "affected_bu_2": "software"},
            {"id": "product_traceability", "title": "Product Traceability & Origin Labelling", "hover_description": "ESRS E4/S2: EU Deforestation Regulation and CSDDD require farm-level traceability for 7 commodities. Digital Product Passport by 2026 for textiles.", "category": "governance", "financial_impact": "high", "societal_impact": "medium", "mitigation_cost_usd": 3_000_000, "stakeholders_group": "Regulators; Consumers; Suppliers", "nature_of_impact": "Potential negative - deception/non-compliance", "interdependency_1": "garment_worker_wages", "interdependency_2": "fast_fashion_waste", "affected_bu_1": "retail_fmcg", "affected_bu_2": "consumer_goods"},
            {"id": "overconsumption_promo", "title": "Promotional Overconsumption", "hover_description": "ESRS E5: Flash sales and single-day shopping events (Black Friday) drive 40% of annual textile waste. French anti-promotional law on fast fashion as policy signal.", "category": "governance", "financial_impact": "medium", "societal_impact": "medium", "mitigation_cost_usd": 1_200_000, "stakeholders_group": "Consumers; NGOs; Regulators", "nature_of_impact": "Actual negative - resource overconsumption", "interdependency_1": "fast_fashion_waste", "interdependency_2": "", "affected_bu_1": "retail_fmcg", "affected_bu_2": ""},
            {"id": "smallholder_supplier_risk", "title": "Smallholder Supplier Income Vulnerability", "hover_description": "ESRS S2: FMCG sourcing from 500M smallholder farmers. Climate shocks and price volatility threaten incomes. Buyer power squeeze - 5 buyers control 40% of global grocery.", "category": "social", "financial_impact": "medium", "societal_impact": "high", "mitigation_cost_usd": 2_800_000, "stakeholders_group": "Suppliers; NGOs; Governments", "nature_of_impact": "Actual negative - supplier income harm", "interdependency_1": "product_traceability", "interdependency_2": "", "affected_bu_1": "retail_fmcg", "affected_bu_2": "agriculture"},
            {"id": "store_energy_efficiency", "title": "Retail Store Energy Efficiency", "hover_description": "ESRS E1: Large retail chains operate 100,000s of stores globally. Refrigeration, HVAC, and lighting = 65% of store energy. EU Energy Efficiency Directive Article 8 mandatory audits.", "category": "ecological", "financial_impact": "medium", "societal_impact": "low", "mitigation_cost_usd": 2_500_000, "stakeholders_group": "Investors; Regulators", "nature_of_impact": "Actual negative - GHG emissions", "interdependency_1": "food_miles_logistics", "interdependency_2": "", "affected_bu_1": "retail_fmcg", "affected_bu_2": ""},
            {"id": "packaging_take_back", "title": "Packaging Take-Back & Deposit Return", "hover_description": "ESRS E5: EU Packaging Regulation (PPWR) 2024 - refillable targets. Deposit Return Schemes mandated in 22+ EU member states. Retailers as collection point.", "category": "ecological", "financial_impact": "medium", "societal_impact": "medium", "mitigation_cost_usd": 3_000_000, "stakeholders_group": "Consumers; Regulators; NGOs", "nature_of_impact": "Potential negative - packaging waste", "interdependency_1": "fast_fashion_waste", "interdependency_2": "", "affected_bu_1": "retail_fmcg", "affected_bu_2": "consumer_goods"},
        ],
        "interdependencies": [
            {"source_issue_id": "fast_fashion_waste",    "target_issue_id": "garment_worker_wages",     "severity": 5, "description": "High volume, low price model requires cheap labour"},
            {"source_issue_id": "product_traceability",  "target_issue_id": "smallholder_supplier_risk", "severity": 4, "description": "Traceability systems expose smallholder vulnerability"},
            {"source_issue_id": "dark_pattern_ecommerce","target_issue_id": "overconsumption_promo",     "severity": 4, "description": "UX design amplifies promotional overconsumption"},
        ],
    },

    # =========================================================================
    {
        "bu_id":           "agriculture",
        "label":           "Agriculture",
        "icon":            "AG",
        "esrs_sector":     "Food & Agriculture / Agribusiness",
        "consultant_fee_usd": 1_500_000,
        "issues": [
            {"id": "land_degradation", "title": "Soil Degradation & Land Use Change", "hover_description": "ESRS E4: 33% of global soils degraded (FAO). EU Nature Restoration Law mandates 20% habitat restoration by 2030. Carbon sequestration loss.", "category": "ecological", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 5_000_000, "stakeholders_group": "NGOs; Governments; Communities", "nature_of_impact": "Actual negative - soil/ecosystem degradation", "interdependency_1": "agrochemical_pollution", "interdependency_2": "water_use_ag", "affected_bu_1": "agriculture", "affected_bu_2": "consumer_goods"},
            {"id": "agrochemical_pollution", "title": "Pesticide & Fertiliser Pollution", "hover_description": "ESRS E3/E4: Nitrate pollution in 40% of EU waterways. EU Farm-to-Fork: 50% pesticide reduction by 2030. Biodiversity collapse (pollinator crisis).", "category": "ecological", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 4_000_000, "stakeholders_group": "NGOs; Communities; Regulators", "nature_of_impact": "Actual negative - water and biodiversity harm", "interdependency_1": "land_degradation", "interdependency_2": "", "affected_bu_1": "agriculture", "affected_bu_2": "consumer_goods"},
            {"id": "water_use_ag", "title": "Irrigation Water Stress", "hover_description": "ESRS E3: Agriculture uses 70% of global freshwater. 40% of food production in water-stressed areas. CSRD mandates water-use disclosure under ESRS E3.", "category": "ecological", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 5_500_000, "stakeholders_group": "NGOs; Communities; Investors", "nature_of_impact": "Actual negative - water depletion", "interdependency_1": "land_degradation", "interdependency_2": "", "affected_bu_1": "agriculture", "affected_bu_2": "consumer_goods"},
            {"id": "animal_welfare", "title": "Animal Welfare in Intensive Farming", "hover_description": "ESRS S2/S3: EU revising Animal Welfare Legislation (2023). 80% of EU consumers support stricter rules. Battery cage ban implemented; gestation crate ban pending.", "category": "social", "financial_impact": "medium", "societal_impact": "high", "mitigation_cost_usd": 3_000_000, "stakeholders_group": "NGOs; Consumers; Regulators", "nature_of_impact": "Actual negative - sentient being harm", "interdependency_1": "", "interdependency_2": "", "affected_bu_1": "agriculture", "affected_bu_2": "consumer_goods"},
            {"id": "migrant_worker_ag", "title": "Migrant Agricultural Worker Rights", "hover_description": "ESRS S1/S2: Seasonal migrant workers face wage theft, unsafe housing, no contracts. EU CSDDD supply chain due diligence covers agricultural Tier-1 contractors.", "category": "social", "financial_impact": "medium", "societal_impact": "high", "mitigation_cost_usd": 2_000_000, "stakeholders_group": "NGOs; Trade Unions; Governments", "nature_of_impact": "Actual negative - labour rights violation", "interdependency_1": "", "interdependency_2": "", "affected_bu_1": "agriculture", "affected_bu_2": "retail_fmcg"},
            {"id": "food_security_climate", "title": "Food Security & Climate Disruption", "hover_description": "ESRS E1: Crop yield losses of 25% projected under 2C (IPCC). 828M people face hunger. EU Food Security Strategy - strategic protein and grain reserves.", "category": "ecological", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 6_000_000, "stakeholders_group": "Governments; NGOs; Communities", "nature_of_impact": "Actual negative - food system disruption", "interdependency_1": "water_use_ag", "interdependency_2": "land_degradation", "affected_bu_1": "agriculture", "affected_bu_2": ""},
            {"id": "antibiotic_ag", "title": "Antibiotic Use in Livestock", "hover_description": "ESRS S3: 70% of global antibiotics used in livestock. EU banned growth promoter antibiotics; preventive use still widespread. AMR public health risk.", "category": "social", "financial_impact": "medium", "societal_impact": "high", "mitigation_cost_usd": 2_500_000, "stakeholders_group": "Regulators; NGOs; Communities", "nature_of_impact": "Actual negative - AMR systemic risk", "interdependency_1": "animal_welfare", "interdependency_2": "", "affected_bu_1": "agriculture", "affected_bu_2": "pharma"},
            {"id": "agri_biodiversity", "title": "Agricultural Biodiversity Loss", "hover_description": "ESRS E4: 75% of crop varieties lost in last 100 years. Monoculture dominance creates systemic vulnerability. EU Biodiversity Strategy 2030: 30% protected land.", "category": "ecological", "financial_impact": "medium", "societal_impact": "high", "mitigation_cost_usd": 3_000_000, "stakeholders_group": "Scientists; NGOs; Communities", "nature_of_impact": "Actual negative - genetic erosion", "interdependency_1": "agrochemical_pollution", "interdependency_2": "food_security_climate", "affected_bu_1": "agriculture", "affected_bu_2": ""},
            {"id": "smallholder_income", "title": "Smallholder Farm Income Viability", "hover_description": "ESRS S2: 500M smallholder farms produce 70% of food in developing countries. EU supply chain squeeze - supermarket buyer power. Minimum price mechanisms (cocoa, coffee).", "category": "social", "financial_impact": "low", "societal_impact": "high", "mitigation_cost_usd": 2_000_000, "stakeholders_group": "NGOs; Trade Bodies; Governments", "nature_of_impact": "Actual negative - poverty perpetuation", "interdependency_1": "food_security_climate", "interdependency_2": "", "affected_bu_1": "agriculture", "affected_bu_2": "retail_fmcg"},
            {"id": "ghg_livestock", "title": "Livestock GHG Emissions (Methane)", "hover_description": "ESRS E1: Livestock = 14.5% of global GHG. Enteric fermentation and manure management dominate. EU Farm-to-Fork - no binding livestock targets (political controversy).", "category": "ecological", "financial_impact": "medium", "societal_impact": "high", "mitigation_cost_usd": 4_500_000, "stakeholders_group": "NGOs; Investors; Regulators", "nature_of_impact": "Actual negative - climate contribution", "interdependency_1": "food_security_climate", "interdependency_2": "antibiotic_ag", "affected_bu_1": "agriculture", "affected_bu_2": "consumer_goods"},
        ],
        "interdependencies": [
            {"source_issue_id": "land_degradation",      "target_issue_id": "food_security_climate",  "severity": 5, "description": "Degraded soils reduce yield, accelerating food insecurity"},
            {"source_issue_id": "agrochemical_pollution","target_issue_id": "agri_biodiversity",       "severity": 5, "description": "Pesticides are primary driver of pollinator collapse"},
            {"source_issue_id": "ghg_livestock",         "target_issue_id": "antibiotic_ag",           "severity": 3, "description": "Intensive systems driving both GHG and AMR"},
        ],
    },

    # =========================================================================
    {
        "bu_id":           "technology",
        "label":           "Technology",
        "icon":            "TK",
        "esrs_sector":     "Technology / Deep Tech / AI",
        "consultant_fee_usd": 1_500_000,
        "issues": [
            {"id": "ai_governance", "title": "AI Governance & Accountability", "hover_description": "ESRS G1: EU AI Act (2024) - high-risk AI requires conformity assessment. No binding global framework. OECD AI Principles voluntary. Liability gap in autonomous systems.", "category": "governance", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 3_500_000, "stakeholders_group": "Regulators; Customers; NGOs", "nature_of_impact": "Potential negative - accountability vacuum", "interdependency_1": "ai_environment_cost", "interdependency_2": "surveillance_tech", "affected_bu_1": "technology", "affected_bu_2": "software"},
            {"id": "ai_environment_cost", "title": "AI Training Environmental Cost", "hover_description": "ESRS E1: Training GPT-4 = 550 tonnes CO2 (est). AI data centre water use: 1.8L per query. Microsoft, Google water disclosures under pressure. IEA energy demand projection surge.", "category": "ecological", "financial_impact": "high", "societal_impact": "medium", "mitigation_cost_usd": 5_000_000, "stakeholders_group": "Investors; Regulators; Communities", "nature_of_impact": "Actual negative - energy/water intensity", "interdependency_1": "", "interdependency_2": "", "affected_bu_1": "technology", "affected_bu_2": "software"},
            {"id": "surveillance_tech", "title": "Surveillance Technology & Civil Liberties", "hover_description": "ESRS S2: Facial recognition sold to authoritarian governments. EU AI Act bans real-time biometric surveillance in public spaces. Export control debate.", "category": "social", "financial_impact": "medium", "societal_impact": "high", "mitigation_cost_usd": 2_500_000, "stakeholders_group": "NGOs; Governments; Communities", "nature_of_impact": "Actual negative - civil liberties violation", "interdependency_1": "ai_governance", "interdependency_2": "", "affected_bu_1": "technology", "affected_bu_2": "software"},
            {"id": "quantum_security", "title": "Quantum Computing & Encryption Risk", "hover_description": "ESRS G1: Quantum computers will break RSA-2048 within 10-15 years. NIST Post-Quantum Cryptography standards (2024). Harvest now, decrypt later attacks already underway.", "category": "governance", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 4_000_000, "stakeholders_group": "Governments; Investors; Customers", "nature_of_impact": "Potential negative - systemic security collapse", "interdependency_1": "", "interdependency_2": "", "affected_bu_1": "technology", "affected_bu_2": "banking_financial_services"},
            {"id": "tech_talent_diversity", "title": "Tech Talent Diversity & Inclusion", "hover_description": "ESRS S1: Women hold 26% of tech roles. Diversity deficit in AI teams amplifies bias in outputs. EU Pay Transparency Directive and gender pay gap disclosure.", "category": "social", "financial_impact": "medium", "societal_impact": "high", "mitigation_cost_usd": 2_000_000, "stakeholders_group": "Own Workforce; NGOs; Investors", "nature_of_impact": "Actual negative - exclusion", "interdependency_1": "ai_governance", "interdependency_2": "", "affected_bu_1": "technology", "affected_bu_2": ""},
            {"id": "open_source_ai", "title": "Open Source AI & Dual-Use Risk", "hover_description": "ESRS G1: Open source LLMs (LLaMA, Mistral) remove safety guardrails. EU AI Act Art. 53 exemptions for OSS - but high-risk use cases still regulated.", "category": "governance", "financial_impact": "medium", "societal_impact": "high", "mitigation_cost_usd": 1_800_000, "stakeholders_group": "Regulators; NGOs; Researchers", "nature_of_impact": "Potential negative - misuse/harm enablement", "interdependency_1": "ai_governance", "interdependency_2": "", "affected_bu_1": "technology", "affected_bu_2": "software"},
            {"id": "space_debris", "title": "Satellite Proliferation & Space Debris", "hover_description": "ESRS E2/G1: 8,000+ satellites in LEO; 27,000+ debris objects tracked. No binding international governance. Kessler syndrome risk threatens global communications.", "category": "ecological", "financial_impact": "low", "societal_impact": "high", "mitigation_cost_usd": 1_500_000, "stakeholders_group": "Governments; Scientists; Investors", "nature_of_impact": "Potential negative - orbital commons degradation", "interdependency_1": "", "interdependency_2": "", "affected_bu_1": "technology", "affected_bu_2": ""},
            {"id": "gig_worker_rights", "title": "Gig Worker Rights in Platform Economy", "hover_description": "ESRS S1: EU Platform Work Directive (2024) - algorithmic management rights, reclassification. 40M gig workers in EU. App-based workers lack social protection.", "category": "social", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 3_000_000, "stakeholders_group": "Own Workforce; Trade Unions; Governments", "nature_of_impact": "Actual negative - labour precarity", "interdependency_1": "tech_talent_diversity", "interdependency_2": "", "affected_bu_1": "technology", "affected_bu_2": "retail_fmcg"},
            {"id": "critical_infra_dependency", "title": "Critical Infrastructure Technology Dependency", "hover_description": "ESRS G1: Power grids, hospitals, water systems dependent on proprietary tech vendors. Single-vendor risk. EU DORA and NIS2 require resilience testing of IT/OT systems.", "category": "governance", "financial_impact": "high", "societal_impact": "high", "mitigation_cost_usd": 5_000_000, "stakeholders_group": "Governments; Regulators; Communities", "nature_of_impact": "Potential negative - systemic infrastructure risk", "interdependency_1": "quantum_security", "interdependency_2": "", "affected_bu_1": "technology", "affected_bu_2": "software"},
            {"id": "misinformation_ai", "title": "AI-Generated Misinformation & Deepfakes", "hover_description": "ESRS G1/S3: Synthetic media undermines democratic institutions. EU DSA misinformation obligations for Very Large Platforms. Deepfake fraud losses: $25M (Hong Kong, 2024).", "category": "governance", "financial_impact": "medium", "societal_impact": "high", "mitigation_cost_usd": 2_800_000, "stakeholders_group": "Governments; NGOs; Media", "nature_of_impact": "Actual negative - democratic harm", "interdependency_1": "ai_governance", "interdependency_2": "surveillance_tech", "affected_bu_1": "technology", "affected_bu_2": "software"},
        ],
        "interdependencies": [
            {"source_issue_id": "ai_governance",       "target_issue_id": "misinformation_ai",        "severity": 5, "description": "Weak governance enables deepfake and misinformation at scale"},
            {"source_issue_id": "ai_environment_cost", "target_issue_id": "critical_infra_dependency", "severity": 3, "description": "AI energy demand strains critical power infrastructure"},
            {"source_issue_id": "quantum_security",    "target_issue_id": "critical_infra_dependency", "severity": 4, "description": "Quantum attacks on infrastructure encryption"},
        ],
    },
]


# =============================================================================
#  PANEL BIAS CONFIGURATION REFERENCE TABLE
# =============================================================================

PANEL_BIAS_TABLE = [
    {"industry": "All (default)",     "group": "Investors",              "bias_rule": "q3_push",            "description": "Social Q2 issues pushed to Q3 - investors focus on financial risk",             "esrs_ref": "ESRS S1.47(a)", "fee_usd": 750_000, "color": "#6366f1"},
    {"industry": "All (default)",     "group": "Own Workforce",          "bias_rule": "s1_boost",           "description": "Social/workforce issues in Q2/Q4 bumped to Q1 by workers",                      "esrs_ref": "ESRS S1.47(b)", "fee_usd": 750_000, "color": "#3b82f6"},
    {"industry": "All (default)",     "group": "NGOs / Communities",     "bias_rule": "q2_push",            "description": "Pure-financial Q3 issues elevated to Q2 (community impact surfaced)",            "esrs_ref": "ESRS S1.47(c)", "fee_usd": 750_000, "color": "#10b981"},
    {"industry": "All (default)",     "group": "Subject Matter Experts", "bias_rule": "accurate",           "description": "Always returns correct quadrant - calibrated ESRS mapping",                     "esrs_ref": "ESRS S1.47(d)", "fee_usd": 750_000, "color": "#f59e0b"},
    {"industry": "Oil & Gas",         "group": "NGOs / Communities",     "bias_rule": "q2_push (amplified)","description": "Indigenous rights and biodiversity issues amplified - NGO priority",              "esrs_ref": "ESRS S1.47(c)", "fee_usd": 750_000, "color": "#10b981"},
    {"industry": "Banking",           "group": "Investors",              "bias_rule": "accurate (domain)",  "description": "Financial sector investors more accurate on financed emissions risk",              "esrs_ref": "ESRS S1.47(a)", "fee_usd": 750_000, "color": "#6366f1"},
]


# =============================================================================
#  COLUMN DEFINITIONS
# =============================================================================

ISSUE_COLS = [
    ("id",                  "ID",                    22),
    ("title",               "Title",                 34),
    ("hover_description",   "Hover Description",     60),
    ("category",            "Category",              16),
    ("financial_impact",    "Financial Impact",      16),
    ("societal_impact",     "Societal Impact",       16),
    ("mitigation_cost_usd", "Mitigation Cost (USD)", 22),
    ("stakeholders_group",  "Stakeholders Group",    28),
    ("nature_of_impact",    "Nature of Impact",      35),
    ("interdependency_1",   "Interdependency 1",     22),
    ("interdependency_2",   "Interdependency 2",     22),
    ("affected_bu_1",       "Affected BU 1",         18),
    ("affected_bu_2",       "Affected BU 2",         18),
]

LINK_COLS = [
    ("source_issue_id", "Source Issue ID", 26),
    ("target_issue_id", "Target Issue ID", 26),
    ("severity",        "Severity (1-5)",  16),
    ("description",     "Description",     60),
]

BIAS_COLS = [
    ("industry",    "Industry",             22),
    ("group",       "Stakeholder Group",    26),
    ("bias_rule",   "Bias Rule",            22),
    ("description", "Description",         55),
    ("esrs_ref",    "ESRS Reference",       20),
    ("fee_usd",     "Fee (USD)",            18),
    ("color",       "UI Color Hex",         16),
]


# =============================================================================
#  HELPER FUNCTIONS
# =============================================================================

def _tab_color(idx: int) -> str:
    palette = ["1B4F72","145A32","7D3C98","922B21","B7950B","1A5276","0E6655","6E2FBE","A04000","1F618D"]
    return palette[idx % len(palette)]


_INVALID_SHEET_CHARS = str.maketrans({"/": "-", "\\": "-", "?": "", "*": "", "[": "(", "]": ")", ":": "-", "&": "n"})

def _safe_sheet_name(name: str, max_len: int = 31) -> str:
    """Return a valid Excel sheet name (<=31 chars, no forbidden chars)."""
    safe = name.translate(_INVALID_SHEET_CHARS).strip()
    return safe[:max_len]


def _style_header(ws, row: int, cols: list, fill_hex: str) -> None:
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    fill   = PatternFill(start_color=fill_hex, end_color=fill_hex, fill_type="solid")
    font   = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    border = Border(bottom=Side(style="thin", color="D5D8DC"))
    align  = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for col_idx, (_, header, width) in enumerate(cols, 1):
        cell = ws.cell(row=row, column=col_idx, value=header)
        cell.font = font; cell.fill = fill; cell.border = border; cell.alignment = align
        ws.column_dimensions[get_column_letter(col_idx)].width = width


def _style_data(ws, row: int, cols: list, data: dict, even: bool) -> None:
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    even_fill = PatternFill(start_color="F0F4FF", end_color="F0F4FF", fill_type="solid")
    odd_fill  = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
    data_font = Font(name="Calibri", size=10)
    bold_font = Font(name="Calibri", size=10, bold=True)
    border    = Border(bottom=Side(style="thin", color="E8ECF0"))
    for col_idx, (key, _, _) in enumerate(cols, 1):
        value = data.get(key, "")
        cell  = ws.cell(row=row, column=col_idx, value=value)
        cell.font   = bold_font if col_idx <= 2 else data_font
        cell.fill   = even_fill if even else odd_fill
        cell.border = border
        cell.alignment = Alignment(vertical="center", wrap_text=(col_idx > 6))


# =============================================================================
#  MAIN GENERATOR
# =============================================================================

def generate_industry_master_excel(output_path) -> None:
    """Generate the multi-industry master materiality workbook."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook()

    # ── ReadMe sheet ─────────────────────────────────────────────────────────
    ws_readme = wb.active
    ws_readme.title = "ReadMe"
    ws_readme.sheet_properties.tabColor = "2C3E50"
    ws_readme.column_dimensions["A"].width = 20
    ws_readme.column_dimensions["B"].width = 88

    readme_rows = [
        ("MURESSONS — INDUSTRY MASTER MATERIALITY SPREADSHEET", ""),
        ("", ""),
        ("PURPOSE",      "Pre-populated CSRD double materiality issues for 9 industry verticals."),
        ("INDUSTRIES",   "pharma | electronics | consumer_goods | software | oil_gas | banking_financial_services | retail_fmcg | agriculture | technology"),
        ("", ""),
        ("UPLOAD",       "Step 1: Select the industry sheet (e.g. 'PH Pharma')"),
        ("",             "Step 2: Review / edit issues as needed"),
        ("",             "Step 3: Save as separate .xlsx file"),
        ("",             "Step 4: POST /api/admin/materiality-config/upload?scope={bu_id}"),
        ("",             "        curl -X POST 'https://<host>/api/admin/materiality-config/upload?scope=pharma' \\"),
        ("",             "             -H 'X-Admin-Key: <key>' -F 'file=@pharma.xlsx'"),
        ("", ""),
        ("QUADRANT",     "Financial HIGH + Societal HIGH  -> Q1 (Material: CFO approval needed)"),
        ("",             "Financial LOW  + Societal HIGH  -> Q2 (Impact material: disclosure only)"),
        ("",             "Financial HIGH + Societal LOW   -> Q3 (Financial risk: risk management)"),
        ("",             "Financial LOW  + Societal LOW   -> Q4 (Watch list: low priority)"),
        ("", ""),
        ("PANEL FEES",   "Flat $750K per stakeholder group. See PanelBiasConfig sheet."),
        ("ESRS MAP",     "E1=Climate  E2=Pollution  E3=Water  E4=Biodiversity  E5=Circular"),
        ("",             "S1=Own Workforce  S2=Value Chain  S3=Communities  S4=Consumers  G1=Conduct"),
    ]

    h_fill = PatternFill(start_color="2C3E50", end_color="2C3E50", fill_type="solid")
    h_font = Font(name="Calibri", size=13, bold=True, color="FFFFFF")
    l_font = Font(name="Calibri", size=10, bold=True, color="2C3E50")
    b_font = Font(name="Calibri", size=10, color="374151")

    for r, (label, body) in enumerate(readme_rows, 1):
        if r == 1:
            c = ws_readme.cell(row=r, column=1, value=label)
            c.font = h_font; c.fill = h_fill
            c.alignment = Alignment(horizontal="left", vertical="center")
            ws_readme.merge_cells(start_row=r, start_column=1, end_row=r, end_column=2)
            ws_readme.row_dimensions[r].height = 22
        else:
            ca = ws_readme.cell(row=r, column=1, value=label)
            ca.font = l_font; ca.alignment = Alignment(vertical="top")
            cb = ws_readme.cell(row=r, column=2, value=body)
            cb.font = b_font; cb.alignment = Alignment(vertical="top", wrap_text=True)
            ws_readme.row_dimensions[r].height = 16 if body or label else 6

    ws_readme.freeze_panes = "A3"

    # ── Industry sheets ───────────────────────────────────────────────────────
    for idx, industry in enumerate(INDUSTRIES):
        bu_id = industry["bu_id"]
        label = industry["label"]
        icon  = industry["icon"]
        clr   = _tab_color(idx)

        # Issues sheet
        ws = wb.create_sheet(_safe_sheet_name(f"{icon} {label}"))
        ws.sheet_properties.tabColor = clr

        fee = industry.get("consultant_fee_usd", 1_500_000)
        meta = (f"BU ID: {bu_id}  |  Sector: {industry.get('esrs_sector','')}  "
                f"|  Consultant Fee: ${fee:,}  |  Issues: {len(industry['issues'])}")
        mc = ws.cell(row=1, column=1, value=meta)
        mc.font = Font(name="Calibri", size=10, italic=True, color="1B4F72")
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(ISSUE_COLS))
        ws.row_dimensions[1].height = 20

        _style_header(ws, 2, ISSUE_COLS, clr)
        ws.freeze_panes = "A3"
        ws.row_dimensions[2].height = 22

        for ri, issue in enumerate(industry["issues"], start=3):
            ws.row_dimensions[ri].height = 32
            _style_data(ws, ri, ISSUE_COLS, issue, even=(ri % 2 == 0))

        # Interdependencies sheet
        ws_lk = wb.create_sheet(_safe_sheet_name(f"{icon} {label} Links"))
        ws_lk.sheet_properties.tabColor = clr
        _style_header(ws_lk, 1, LINK_COLS, clr)
        ws_lk.freeze_panes = "A2"
        ws_lk.row_dimensions[1].height = 22

        for ri, link in enumerate(industry.get("interdependencies", []), start=2):
            ws_lk.row_dimensions[ri].height = 24
            _style_data(ws_lk, ri, LINK_COLS, link, even=(ri % 2 == 0))

    # ── PanelBiasConfig sheet ─────────────────────────────────────────────────
    ws_bias = wb.create_sheet("PanelBiasConfig")
    ws_bias.sheet_properties.tabColor = "6C3483"
    _style_header(ws_bias, 1, BIAS_COLS, "6C3483")
    ws_bias.freeze_panes = "A2"
    for ri, row in enumerate(PANEL_BIAS_TABLE, start=2):
        _style_data(ws_bias, ri, BIAS_COLS, row, even=(ri % 2 == 0))

    wb.save(str(output_path))
    total = sum(len(i["issues"]) for i in INDUSTRIES)
    print(f"[OK] {len(INDUSTRIES)} industries | {total} total issues -> {output_path}")


# =============================================================================
#  JSON EXPORT
# =============================================================================

def export_all_industries_to_json(output_dir) -> None:
    """Write each industry as a standalone materiality_config JSON."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for industry in INDUSTRIES:
        bu_id = industry["bu_id"]
        cfg = {
            "consultant_fee_usd": industry.get("consultant_fee_usd", 1_500_000),
            "issues": industry["issues"],
            "interdependencies": industry.get("interdependencies", []),
        }
        out = output_dir / f"materiality_{bu_id}.json"
        with open(out, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"  [OK] {len(cfg['issues'])} issues -> {out}")


# =============================================================================
#  PER-INDUSTRY UPLOADABLE XLSX  (standard Issues + Interdependencies sheets)
#  Compatible with backend: POST /api/admin/materiality-config/upload?scope={bu_id}
# =============================================================================

# Columns expected by import_materiality_from_excel (must match _ISSUE_COLUMNS there)
_UPLOAD_ISSUE_COLS = [
    ("id",                  "ID",                    22),
    ("title",               "Title",                 34),
    ("hover_description",   "Hover Description",     60),
    ("category",            "Category",              16),
    ("financial_impact",    "Financial Impact",      16),
    ("societal_impact",     "Societal Impact",       16),
    ("mitigation_cost_usd", "Mitigation Cost USD",   22),
    ("stakeholders_group",  "Stakeholders Group",    28),
    ("nature_of_impact",    "Nature of Impact",      35),
    ("interdependency_1",   "Interdependency 1",     22),
    ("interdependency_2",   "Interdependency 2",     22),
    ("affected_bu_1",       "Affected BU 1",         18),
    ("affected_bu_2",       "Affected BU 2",         18),
]

_UPLOAD_LINK_COLS = [
    ("source_issue_id", "Source Issue ID", 26),
    ("target_issue_id", "Target Issue ID", 26),
    ("severity",        "Severity (1-5)",  16),
    ("description",     "Description",     60),
]


def export_individual_xlsx(industry: dict, output_path) -> None:
    """
    Write a single upload-ready .xlsx for one industry.
    Sheet names are 'Issues' and 'Interdependencies' — exactly what
    import_materiality_from_excel expects.

    Upload with:
        POST /api/admin/materiality-config/upload?scope={bu_id}
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook()

    TAB_CLR = "1B4F72"
    fee = industry.get("consultant_fee_usd", 1_500_000)
    label = industry["label"]
    bu_id = industry["bu_id"]

    # ── Sheet 1: Issues (REQUIRED name) ──────────────────────────────────────
    ws = wb.active
    ws.title = "Issues"
    ws.sheet_properties.tabColor = TAB_CLR

    # Row 1: metadata (parsed by import_materiality_from_excel for fee)
    meta = f"Consultant Fee (USD): {fee:,}  |  Industry: {label}  |  BU ID: {bu_id}"
    mc = ws.cell(row=1, column=1, value=meta)
    mc.font = Font(name="Calibri", size=10, italic=True, color="1B4F72")
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(_UPLOAD_ISSUE_COLS))
    ws.row_dimensions[1].height = 20

    # Row 2: headers
    _style_header(ws, 2, _UPLOAD_ISSUE_COLS, TAB_CLR)
    ws.freeze_panes = "A3"
    ws.row_dimensions[2].height = 22

    # Data rows
    for ri, issue in enumerate(industry["issues"], start=3):
        ws.row_dimensions[ri].height = 32
        _style_data(ws, ri, _UPLOAD_ISSUE_COLS, issue, even=(ri % 2 == 0))

    # ── Sheet 2: Interdependencies ────────────────────────────────────────────
    ws_lk = wb.create_sheet("Interdependencies")
    ws_lk.sheet_properties.tabColor = "6C3483"
    _style_header(ws_lk, 1, _UPLOAD_LINK_COLS, "6C3483")
    ws_lk.freeze_panes = "A2"
    ws_lk.row_dimensions[1].height = 22

    for ri, link in enumerate(industry.get("interdependencies", []), start=2):
        ws_lk.row_dimensions[ri].height = 24
        _style_data(ws_lk, ri, _UPLOAD_LINK_COLS, link, even=(ri % 2 == 0))

    wb.save(str(output_path))


def export_all_individual_xlsx(output_dir) -> None:
    """Write one upload-ready .xlsx per industry into output_dir."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for industry in INDUSTRIES:
        bu_id = industry["bu_id"]
        out = output_dir / f"upload_{bu_id}.xlsx"
        export_individual_xlsx(industry, out)
        print(f"  [OK] {len(industry['issues'])} issues -> {out}")

# =============================================================================
#  CLI
# =============================================================================

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Muressons Industry Master Materiality Spreadsheet")
    p.add_argument("--output",   "-o", default="db/industry_master_materiality.xlsx",
                   help="Master multi-industry .xlsx (default: db/industry_master_materiality.xlsx)")
    p.add_argument("--json-dir", "-j", default=None, help="Also export individual JSON per industry")
    p.add_argument("--xlsx-dir", "-x", default=None,
                   help="Export individual upload-ready .xlsx per industry (Issues + Interdependencies sheets)")
    p.add_argument("--list",     action="store_true", help="List industries and exit")
    args = p.parse_args()

    if args.list:
        print(f"\n{'BU ID':<35} {'Label':<28} {'Issues':>7} {'Links':>7}")
        print("-" * 80)
        total = 0
        for ind in INDUSTRIES:
            n = len(ind["issues"]); total += n
            print(f"{ind['bu_id']:<35} {ind['label']:<28} {n:>7} {len(ind.get('interdependencies',[])):>7}")
        print("-" * 80)
        print(f"{'TOTAL':<35} {'':<28} {total:>7}")
    else:
        generate_industry_master_excel(args.output)

        if args.json_dir:
            print(f"\nExporting JSON configs to {args.json_dir}/")
            export_all_industries_to_json(args.json_dir)

        if args.xlsx_dir:
            print(f"\nExporting individual upload-ready xlsx to {args.xlsx_dir}/")
            export_all_individual_xlsx(args.xlsx_dir)
