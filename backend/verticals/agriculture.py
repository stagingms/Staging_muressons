"""
Muressons — Agriculture Vertical: Stakeholders + CSRD Issues
Replaces: Consumer Goods slot (natural resources, supply chain)
"""
from __future__ import annotations
from typing import Any

AGRICULTURE_STAKEHOLDERS: list[dict[str, Any]] = [
    # Q1 — Manage Closely
    {"id": "water_authority", "name": "River Basin Water Authority", "icon": "🏛️",
     "description": "Issued a formal extraction licence review after satellite data showed aquifer depletion at 3 Muressons irrigation sites. Mandatory environmental impact assessment due in Q3. Revoked a peer company's licence last year.",
     "correct_quadrant": "manage_closely", "urgency": "high", "legitimacy": "high",
     "urgency_rationale": "Active licence review with Q3 EIA deadline. Operational shutdown risk.",
     "intel_dossier": ["📰 Water Authority: 'Satellite data shows aquifer depletion at Muressons sites — licence review initiated'", "📰 Reuters: 'Peer agribusiness loses extraction licence after aquifer collapse'", "📰 Guardian: 'Water crisis in river basin — Muressons operations named as largest extractor'"],
     "engagement_tactics": [
         {"id": "water_stewardship", "label": "Commission independent water stewardship plan and submit voluntary EIA early", "correct": True, "rationale": "Demonstrates proactive resource management."},
         {"id": "legal_challenge", "label": "Challenge the licence review through administrative court", "correct": False, "rationale": "Adversarial posture against regulator while aquifer data is public."},
         {"id": "reduce_disclosure", "label": "Reduce publicly reported extraction volumes through accounting adjustments", "correct": False, "rationale": "Satellite data makes this transparently deceptive."},
     ]},
    {"id": "biodiversity_coalition", "name": "Biodiversity & Land Rights Coalition", "icon": "🦅",
     "description": "Filed a legal challenge under the EU Nature Restoration Law over Muressons' conversion of 4,000 hectares of wetland to cropland. Coalition includes WWF, local indigenous groups, and 3 EU member state environmental agencies.",
     "correct_quadrant": "manage_closely", "urgency": "high", "legitimacy": "high",
     "urgency_rationale": "Active legal challenge. State environmental agencies backing the coalition.",
     "intel_dossier": ["📰 WWF: 'Coalition files EU Nature Restoration Law challenge against Muressons Agriculture'", "📰 Euractiv: 'Three EU states join legal challenge over wetland conversion'", "📰 Nature: 'Biodiversity loss at Muressons sites — 40% species decline documented'"],
     "engagement_tactics": [
         {"id": "restore_wetland", "label": "Commit to 1,500-hectare wetland restoration programme with monitoring", "correct": True, "rationale": "Addresses root cause and demonstrates ecological commitment."},
         {"id": "offset_purchase", "label": "Purchase biodiversity offsets from a broker instead of on-site restoration", "correct": False, "rationale": "Offsets are contested under NRL — may not satisfy legal requirements."},
         {"id": "split_coalition", "label": "Negotiate separately with indigenous groups to divide the coalition", "correct": False, "rationale": "Divide-and-conquer strategy will be exposed and backfire."},
     ]},
    # Q2 — Keep Informed
    {"id": "seasonal_farmworkers", "name": "Seasonal Migrant Farmworkers", "icon": "👷",
     "description": "Seasonal workers from 6 countries report substandard housing, wage deductions for transport, and limited access to healthcare. Labour inspectorate has flagged 2 Muressons farms. Workers are organising through an NGO-supported union.",
     "correct_quadrant": "keep_informed", "urgency": "medium", "legitimacy": "high",
     "urgency_rationale": "Labour inspectorate flag and NGO support create latent exposure. High moral legitimacy.",
     "intel_dossier": ["📰 Guardian: 'Migrant farmworkers at Muressons farms report substandard living conditions'", "📰 Labour Inspectorate: '2 Muressons farms flagged for housing and wage violations'", "📰 Landworkers' Alliance: 'NGO-supported union forming at 4 Muressons operations'"]},
    {"id": "downstream_food_co", "name": "Downstream Food Processors", "icon": "🏭",
     "description": "Major food companies sourcing from Muressons are implementing EU CSDDD due diligence on their agricultural supply chains. 3 have sent formal questionnaires requesting pesticide use data and worker welfare documentation.",
     "correct_quadrant": "keep_informed", "urgency": "medium", "legitimacy": "high",
     "urgency_rationale": "CSDDD cascade creates B2B compliance pressure.",
     "intel_dossier": ["📰 Just-Food: 'Food processors cascade EU CSDDD requirements to agricultural suppliers'", "📰 Procurement: '3 major buyers send formal due diligence questionnaires to Muressons'", "📰 Reuters: 'Agricultural suppliers face new compliance burden from downstream CSDDD'"]},
    {"id": "rural_communities", "name": "Rural Farming Communities", "icon": "🏘️",
     "description": "Communities adjacent to industrial farms report pesticide drift affecting school playgrounds and residential areas. Local government submitted a formal complaint to the environmental agency. Community health study shows elevated respiratory issues.",
     "correct_quadrant": "keep_informed", "urgency": "medium", "legitimacy": "high",
     "urgency_rationale": "Formal government complaint. Health data creates latent litigation exposure.",
     "intel_dossier": ["📰 Local Gazette: 'Parents protest pesticide drift near primary school adjacent to Muressons farm'", "📰 Environmental Agency: 'Formal complaint received re: aerial pesticide application near residential areas'", "📰 Public Health: 'Community health study shows 2× respiratory issues near industrial farming operations'"]},
    # Q3 — Keep Satisfied
    {"id": "agri_commodity_buyers", "name": "Commodity Trading Houses", "icon": "📊",
     "description": "Hold $2.1B in forward crop contracts with quality covenant triggers. Sent routine review letter. Their sustainability desk published a sector note but did not mention Muressons specifically.",
     "correct_quadrant": "keep_satisfied", "urgency": "low", "legitimacy": "high",
     "urgency_rationale": "No covenant breach imminent. Routine engagement.",
     "intel_dossier": ["📰 Internal Sales: 'Annual commodity buyer review — all quality covenants met'", "📰 S&P Platts: 'Agri-commodity ESG ratings — Muressons rated 'neutral''", "📰 Sustainability Desk: 'Sector note on deforestation risk — no Muressons mention'"]},
    {"id": "development_bank", "name": "Development Finance Lender", "icon": "🏦",
     "description": "Provided €200M concessional loan for sustainable agriculture transition. Annual review completed — satisfactory. New tranche conditions may tighten ESG covenants in 18 months.",
     "correct_quadrant": "keep_satisfied", "urgency": "low", "legitimacy": "high",
     "urgency_rationale": "No covenant breach. New tranche 18+ months away.",
     "intel_dossier": ["📰 DFI Annual Review: 'Muressons loan — satisfactory progress on transition milestones'", "📰 Development Finance: 'Next tranche conditions may include biodiversity net gain requirements'", "📰 Internal Treasury: 'DFI relationship healthy — no remediation actions required'"]},
    # Q4 — Monitor
    {"id": "farm_equipment_vendor", "name": "Farm Equipment Maintenance Vendor", "icon": "🚜",
     "description": "Renewed annual tractor and harvester maintenance contract without negotiation. Serves 8 Muressons farms. Never attended a supplier session.",
     "correct_quadrant": "monitor", "urgency": "low", "legitimacy": "low",
     "urgency_rationale": "No claims, no engagement, no influence.",
     "intel_dossier": ["📰 Procurement: 'Equipment maintenance contract auto-renewed — €1.6M annual'", "📰 No external coverage", "📰 Supplier Survey: 'Equipment vendor did not respond to ESG questionnaire'"]},
    {"id": "agri_general_public", "name": "General Public", "icon": "👥",
     "description": "Consumer awareness of Muressons Agriculture at 4%. Products sold as ingredients to food processors, not directly to consumers. No trending social media mentions.",
     "correct_quadrant": "monitor", "urgency": "low", "legitimacy": "low",
     "urgency_rationale": "B2B ingredient supplier — negligible direct public awareness.",
     "intel_dossier": ["📰 Brand Tracker: '4% unaided awareness — unchanged'", "📰 Social Listening: '6 mentions this month'", "📰 No consumer-facing product incidents on record"]},
    # AMBIGUOUS
    {"id": "agri_journalist", "name": "Agricultural Investigative Journalist", "icon": "📰",
     "description": "Award-winning journalist at a farming trade publication has been researching pesticide use patterns. Published 3 articles about competitor agrochemical scandals. Has 85K followers and a track record of EU Parliament questions.",
     "correct_quadrant": "monitor",
     "alternate_quadrant": "keep_informed",
     "alternate_rationale": "Reasonable case for 'Keep Informed': track record of triggering EU Parliament questions. Mitchell et al. (1997): latent power activated by urgency.",
     "urgency": "medium", "legitimacy": "medium",
     "urgency_rationale": "No immediate deadline, but active research creates latent exposure.",
     "intel_dossier": ["📰 Press Office: 'Interview request from A. Chen, Farmers Weekly — 3rd this quarter'", "📰 Media Monitor: 'Chen's pesticide investigation syndicated to Bloomberg (reach: 4M)'", "📰 X/Twitter: 'Reporter's thread on agrochemical pollution got 12K engagements'"]},
]

AGRICULTURE_SALIENCE_MIGRATIONS: list[dict[str, Any]] = [
    {"round": 4, "stakeholder": "agri_general_public", "from_quadrant": "monitor", "to_quadrant": "manage_closely", "condition_flags": [],
     "narrative": "A pesticide contamination incident went viral. Public awareness surged from 4% to 52% in 48 hours. #ToxicFarming is trending.",
     "theory_note": "Mitchell et al. (1997): Dormant stakeholders acquire URGENCY through crisis events."},
    {"round": 4, "stakeholder": "agri_journalist", "from_quadrant": "monitor", "to_quadrant": "manage_closely", "condition_flags": [],
     "narrative": "The agricultural journalist broke the contamination story internationally. EU Parliament questions tabled.",
     "theory_note": "Ackermann & Eden (2011): Media stakeholders have 'latent power' activated by crisis."},
    {"round": 4, "stakeholder": "farm_equipment_vendor", "from_quadrant": "monitor", "to_quadrant": "keep_informed", "condition_flags": [],
     "narrative": "Farm equipment vendor reports difficulty recruiting technicians willing to work at Muressons sites due to contamination fears.",
     "theory_note": "Freeman (2010): Even peripheral stakeholders are affected by systemic crises."},
    {"round": 6, "stakeholder": "rural_communities", "from_quadrant": "keep_informed", "to_quadrant": "manage_closely", "condition_flags": [],
     "narrative": "An international environmental law firm adopted the community's case pro bono. Class action for health damages filed.",
     "theory_note": "Mitchell et al. (1997): Communities acquired POWER through legal representation."},
    {"round": 6, "stakeholder": "development_bank", "from_quadrant": "keep_satisfied", "to_quadrant": "manage_closely", "condition_flags": ["land_use_blindspot"],
     "narrative": "Development finance lender triggered ESG covenant review after the R4 scandal. Loan restructuring on the table.",
     "theory_note": "Mendelow (1991): 'Keep Satisfied' shifts to 'Manage Closely' when interest activates."},
    {"round": 9, "stakeholder": "seasonal_farmworkers", "from_quadrant": "keep_informed", "to_quadrant": "manage_closely", "condition_flags": [],
     "narrative": "Seasonal workers voted to refuse harvest contracts. NGO-backed union has legal representation and media platform.",
     "theory_note": "Mitchell et al. (1997): Workers acquired POWER through unionisation."},
    {"round": 9, "stakeholder": "downstream_food_co", "from_quadrant": "keep_informed", "to_quadrant": "manage_closely", "condition_flags": [],
     "narrative": "Major food processors issued formal compliance ultimatum. Will switch suppliers if CSDDD documentation not provided within 60 days.",
     "theory_note": "CSDDD cascade created regulatory-backed POWER for downstream buyers."},
]

# ═══════════════════════════════════════════════════════════════
#  AGRICULTURE CSRD ISSUES (20 total)
# ═══════════════════════════════════════════════════════════════

AGRICULTURE_CSRD_ISSUES: dict = {
    # Q1 (6)
    "pesticide_contamination": {"id": "pesticide_contamination", "title": "Pesticide Runoff & Groundwater Contamination", "hover_description": "Neonicotinoid and glyphosate runoff detected in 3 downstream water bodies. EU Pesticides Regulation tightening enforcement. Community health study shows elevated risks. ESRS E2 mandatory.", "blindspot_description": "Pesticide data — runoff monitoring incomplete.", "correct_quadrant": 1, "severity": "high", "likelihood": "high", "time_horizon": "short", "disclosure_required": True, "electronics_sensitive": False, "esrs_reference": "ESRS E2 (Pollution) / EU Pesticides Regulation", "stakeholder_voice": "local_communities"},
    "land_use_change": {"id": "land_use_change", "title": "Land Use Change & Biodiversity Loss", "hover_description": "4,000 hectares of wetland converted to cropland. EU Nature Restoration Law mandates 20% restoration by 2030. 40% species decline documented. ESRS E4 mandatory.", "blindspot_description": "Biodiversity data — species impact assessment incomplete.", "correct_quadrant": 1, "severity": "high", "likelihood": "high", "time_horizon": "medium", "disclosure_required": True, "electronics_sensitive": False, "esrs_reference": "ESRS E4 (Biodiversity) / EU NRL", "stakeholder_voice": None},
    "water_extraction": {"id": "water_extraction", "title": "Irrigation Water Over-Extraction", "hover_description": "Satellite data shows aquifer depletion at 3 sites. Extraction licence under formal review. 90% water dependency. ESRS E3 mandatory.", "blindspot_description": "Water extraction data — licence compliance audit pending.", "correct_quadrant": 1, "severity": "high", "likelihood": "high", "time_horizon": "short", "disclosure_required": True, "electronics_sensitive": True, "esrs_reference": "ESRS E3 (Water & Marine Resources)", "stakeholder_voice": "local_communities"},
    "migrant_worker_rights": {"id": "migrant_worker_rights", "title": "Seasonal Migrant Worker Exploitation", "hover_description": "Labour inspectorate flagged 2 farms for housing violations and wage deductions. EU CSDDD creates civil liability. ESRS S2 mandatory.", "blindspot_description": "Worker conditions — labour audit incomplete.", "correct_quadrant": 1, "severity": "high", "likelihood": "medium", "time_horizon": "short", "disclosure_required": True, "electronics_sensitive": True, "esrs_reference": "ESRS S2 (Workers in Value Chain) / EU CSDDD", "stakeholder_voice": "suppliers"},
    "soil_degradation": {"id": "soil_degradation", "title": "Soil Carbon Depletion & Degradation", "hover_description": "Intensive monoculture depleted soil organic carbon by 35% over 15 years. EU Soil Health Law proposal mandates soil health monitoring from 2027. ESRS E4 mandatory.", "blindspot_description": "Soil health data — carbon sequestration monitoring not established.", "correct_quadrant": 1, "severity": "high", "likelihood": "high", "time_horizon": "medium", "disclosure_required": True, "electronics_sensitive": False, "esrs_reference": "ESRS E4 (Biodiversity) / EU Soil Health Law", "stakeholder_voice": None},
    "scope1_n2o": {"id": "scope1_n2o", "title": "Nitrous Oxide (N₂O) Emissions from Fertiliser", "hover_description": "N₂O from nitrogen fertiliser application has 265× CO₂ GWP. Represents 60% of total Scope 1 emissions. SBTi FLAG pathway mandatory. ESRS E1.", "blindspot_description": "N₂O emission data — fertiliser application monitoring gaps.", "correct_quadrant": 1, "severity": "high", "likelihood": "high", "time_horizon": "short", "disclosure_required": True, "electronics_sensitive": False, "esrs_reference": "ESRS E1 (Climate Change) / SBTi FLAG", "stakeholder_voice": None},
    # Q2 (4)
    "smallholder_livelihoods": {"id": "smallholder_livelihoods", "title": "Smallholder Farmer Livelihood Support", "hover_description": "Partnership programmes support 3,200 smallholder suppliers. Positive social impact but financially immaterial. ESRS S3 requires disclosure. Cost: $130K.", "blindspot_description": "Smallholder impact — measurement framework needed.", "correct_quadrant": 2, "severity": "medium", "likelihood": "high", "time_horizon": "medium", "disclosure_required": True, "electronics_sensitive": False, "esrs_reference": "ESRS S3 (Affected Communities)", "disclosure_investment_usd": 130_000, "stakeholder_voice": "suppliers"},
    "pollinator_protection": {"id": "pollinator_protection", "title": "Pollinator Protection & Habitat Corridors", "hover_description": "Pollinator decline threatens crop yields. Habitat corridor programme positive but financially immaterial. ESRS E4 disclosure. Cost: $85K.", "blindspot_description": "Pollinator data — biodiversity monitoring insufficient.", "correct_quadrant": 2, "severity": "medium", "likelihood": "medium", "time_horizon": "medium", "disclosure_required": True, "electronics_sensitive": False, "esrs_reference": "ESRS E4 (Biodiversity)", "disclosure_investment_usd": 85_000, "stakeholder_voice": None},
    "worker_health_pesticide": {"id": "worker_health_pesticide", "title": "Farmworker Pesticide Exposure Health Monitoring", "hover_description": "Long-term health risks from pesticide exposure. Financially immaterial. ESRS S1 requires disclosure. Cost: $150K.", "blindspot_description": "Occupational health — long-term study not conducted.", "correct_quadrant": 2, "severity": "medium", "likelihood": "high", "time_horizon": "medium", "disclosure_required": True, "electronics_sensitive": False, "esrs_reference": "ESRS S1 §65 (Workforce Health)", "disclosure_investment_usd": 150_000, "stakeholder_voice": "employees"},
    "regenerative_transition": {"id": "regenerative_transition", "title": "Regenerative Agriculture Transition Reporting", "hover_description": "Pilot regenerative programme on 200 hectares. Positive environmental impact but financially immaterial. ESRS E1 disclosure. Cost: $75K.", "blindspot_description": "Regenerative data — programme measurement not established.", "correct_quadrant": 2, "severity": "medium", "likelihood": "medium", "time_horizon": "long", "disclosure_required": True, "electronics_sensitive": False, "esrs_reference": "ESRS E1 / ESRS E4", "disclosure_investment_usd": 75_000, "stakeholder_voice": None},
    # Q3 (4)
    "crop_price_volatility": {"id": "crop_price_volatility", "title": "Crop Price Volatility (Wheat, Soy, Corn)", "hover_description": "Global crop prices swung ±20% in 12 months. High financial risk. No environmental/social harm. Not ESRS impact-material.", "blindspot_description": "Commodity exposure — analysis needed.", "correct_quadrant": 3, "severity": "low", "likelihood": "high", "time_horizon": "short", "disclosure_required": False, "electronics_sensitive": False, "esrs_reference": "ESRS 2 §SBM-3", "stakeholder_voice": None},
    "climate_yield_risk": {"id": "climate_yield_risk", "title": "Climate-Driven Crop Yield Variability", "hover_description": "Drought risk increasing yield variability by ±15%. Financial risk from physical climate change. Not ESRS impact-material.", "blindspot_description": "Yield data — climate model needed.", "correct_quadrant": 3, "severity": "low", "likelihood": "medium", "time_horizon": "medium", "disclosure_required": False, "electronics_sensitive": False, "esrs_reference": "ESRS 2 §SBM-3", "stakeholder_voice": None},
    "fx_agri": {"id": "fx_agri", "title": "Agricultural Commodity FX Exposure", "hover_description": "45% export revenue creates ±6% swing on FX. Pure financial risk.", "blindspot_description": "FX exposure — treasury review.", "correct_quadrant": 3, "severity": "low", "likelihood": "medium", "time_horizon": "short", "disclosure_required": False, "electronics_sensitive": False, "esrs_reference": "ESRS 2 §SBM-3", "stakeholder_voice": None},
    "input_cost_fertiliser": {"id": "input_cost_fertiliser", "title": "Fertiliser & Energy Input Cost Inflation", "hover_description": "Natural gas-linked fertiliser costs up 40%. Financial pressure only. No ESG impact.", "blindspot_description": "Input costs — procurement analysis.", "correct_quadrant": 3, "severity": "low", "likelihood": "high", "time_horizon": "short", "disclosure_required": False, "electronics_sensitive": False, "esrs_reference": None, "stakeholder_voice": None},
    # Q4 (6)
    "office_recycling_agri": {"id": "office_recycling_agri", "title": "HQ Office Paper Recycling", "hover_description": "Recycles 2 tonnes/yr. Negligible.", "blindspot_description": "Office waste.", "correct_quadrant": 4, "severity": "low", "likelihood": "high", "time_horizon": "short", "disclosure_required": False, "electronics_sensitive": False, "esrs_reference": None, "stakeholder_voice": None},
    "beehive_pr": {"id": "beehive_pr", "title": "Corporate Beehive PR Programme", "hover_description": "6 beehives at HQ while industrial operations threaten pollinator habitat. Classic greenwashing distractor.", "blindspot_description": "PR spend.", "correct_quadrant": 4, "severity": "low", "likelihood": "high", "time_horizon": "short", "disclosure_required": False, "electronics_sensitive": False, "esrs_reference": None, "stakeholder_voice": None},
    "exec_travel_agri": {"id": "exec_travel_agri", "title": "Executive Travel Carbon Offsets", "hover_description": "C-suite flights ~40 tCO₂/yr. <0.01% of total emissions.", "blindspot_description": "Exec travel.", "correct_quadrant": 4, "severity": "low", "likelihood": "high", "time_horizon": "short", "disclosure_required": False, "electronics_sensitive": False, "esrs_reference": None, "stakeholder_voice": None},
    "tree_planting_pr": {"id": "tree_planting_pr", "title": "Annual Tree Planting Day PR Campaign", "hover_description": "500 trees planted/yr vs. 4,000 hectares of wetland converted. Symbolic.", "blindspot_description": "CSR spend.", "correct_quadrant": 4, "severity": "low", "likelihood": "high", "time_horizon": "short", "disclosure_required": False, "electronics_sensitive": False, "esrs_reference": None, "stakeholder_voice": None},
    "ergonomic_tractors": {"id": "ergonomic_tractors", "title": "Ergonomic Tractor Seats for Operators", "hover_description": "Good HSE practice. Financially negligible.", "blindspot_description": "HSE records.", "correct_quadrant": 4, "severity": "low", "likelihood": "high", "time_horizon": "short", "disclosure_required": False, "electronics_sensitive": False, "esrs_reference": None, "stakeholder_voice": None},
    "solar_barn": {"id": "solar_barn", "title": "Solar Panels on Equipment Barn Roof", "hover_description": "Saves ~8 tCO₂/yr. Immaterial vs. N₂O emissions.", "blindspot_description": "Energy data.", "correct_quadrant": 4, "severity": "low", "likelihood": "high", "time_horizon": "short", "disclosure_required": False, "electronics_sensitive": False, "esrs_reference": None, "stakeholder_voice": None},
}
