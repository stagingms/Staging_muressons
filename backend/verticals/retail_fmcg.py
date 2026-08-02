"""
Muressons — Retail/FMCG Vertical: Stakeholders + CSRD Issues
Replaces: Consumer Goods slot (supply chain, packaging, consumer-facing)
"""
from __future__ import annotations
from typing import Any

RETAIL_FMCG_STAKEHOLDERS: list[dict[str, Any]] = [
    # Q1 — Manage Closely
    {"id": "consumer_watchdog", "name": "EU Consumer Protection Authority", "icon": "🏛️",
     "description": "Issued a formal inquiry into misleading 'eco-friendly' product claims under the EU Green Claims Directive. Mandatory product audit for 120 SKUs due in Q3. Fined a peer company €18M for greenwashing last year.",
     "correct_quadrant": "manage_closely", "urgency": "high", "legitimacy": "high",
     "urgency_rationale": "Formal inquiry with Q3 audit deadline. Product recall risk.",
     "intel_dossier": ["📰 EU Commission: 'Consumer authority opens greenwashing investigation into Muressons Retail'", "📰 FT: 'Peer FMCG company fined €18M for misleading eco-labels'", "📰 Reuters: 'Muressons Retail added to priority enforcement list for Green Claims Directive'"],
     "engagement_tactics": [
         {"id": "voluntary_audit", "label": "Commission independent product lifecycle assessment ahead of deadline", "correct": True, "rationale": "Demonstrates good faith and builds evidence base."},
         {"id": "lobby_exemption", "label": "Lobby for SME-style exemption from full product audit requirements", "correct": False, "rationale": "Regulatory capture attempt. Muressons is not an SME."},
         {"id": "relabel_quick", "label": "Rush relabeling of products to remove eco-claims before audit", "correct": False, "rationale": "Destroying evidence. May constitute obstruction."},
     ]},
    {"id": "ethical_consumer_ngo", "name": "Ethical Consumer Alliance", "icon": "🦅",
     "description": "Published a viral exposé linking Muressons' chocolate supply chain to child labour in Côte d'Ivoire. 500K signatures on petition. Threatened coordinated boycott across 12 European markets.",
     "correct_quadrant": "manage_closely", "urgency": "high", "legitimacy": "high",
     "urgency_rationale": "Viral exposure with 500K petition. Boycott in 12 markets imminent.",
     "intel_dossier": ["📰 Guardian: 'Ethical Consumer Alliance links Muressons to child labour in cocoa supply chain'", "📰 Change.org: 'Petition hits 500K — #BoycottMuressons trending in 12 countries'", "📰 Reuters: 'Major retailers considering de-listing Muressons products over ESG concerns'"],
     "engagement_tactics": [
         {"id": "supply_chain_audit", "label": "Commission independent supply chain audit and publish full findings", "correct": True, "rationale": "Transparency demonstrates accountability and willingness to remediate."},
         {"id": "pr_campaign", "label": "Launch counter-PR campaign highlighting existing CSR programmes", "correct": False, "rationale": "Defensive PR without addressing root cause — will be dismantled by NGO."},
         {"id": "threaten_legal", "label": "Send cease-and-desist to the NGO over defamatory claims", "correct": False, "rationale": "SLAPP suit — creates Streisand effect and mobilises wider boycott."},
     ]},
    # Q2 — Keep Informed
    {"id": "garment_workers", "name": "Tier-2 Garment Factory Workers", "icon": "👕",
     "description": "ILO investigation found wage theft and unsafe conditions at 3 Bangladeshi garment suppliers producing Muressons' private-label clothing. Workers are organising through local unions.",
     "correct_quadrant": "keep_informed", "urgency": "medium", "legitimacy": "high",
     "urgency_rationale": "ILO investigation creates exposure. High moral legitimacy.",
     "intel_dossier": ["📰 BBC: 'ILO finds wage theft at factories supplying Muressons private-label clothing'", "📰 Clean Clothes Campaign: 'Garment workers at Muressons suppliers earn 40% below living wage'", "📰 Reuters: 'Bangladesh factory unions mobilise at Muressons supplier sites'"]},
    {"id": "store_associates", "name": "Retail Store Associates", "icon": "👷",
     "description": "Store staff submitted formal grievance about zero-hours contracts and algorithmic scheduling. Internal pulse survey shows 60% 'dissatisfied'. Turnover rate at 45% annually.",
     "correct_quadrant": "keep_informed", "urgency": "medium", "legitimacy": "high",
     "urgency_rationale": "Rising turnover and collective grievance. Latent strike risk.",
     "intel_dossier": ["📰 Internal HR: 'Annual turnover hits 45% — retention crisis in store operations'", "📰 Retail Workers Union: 'Formal grievance filed re: algorithmic scheduling and zero-hours'", "📰 Guardian: 'Muressons store staff report 'dehumanising' AI-driven shift allocation'"]},
    {"id": "smallholder_farmers", "name": "Smallholder Farmer Suppliers", "icon": "🌱",
     "description": "3,200 smallholder farmers in the cocoa and palm oil supply chain report being squeezed by procurement price floors. Fair Trade certification under review. Poverty rates among suppliers at 68%.",
     "correct_quadrant": "keep_informed", "urgency": "medium", "legitimacy": "high",
     "urgency_rationale": "Fair Trade certification review. High moral legitimacy.",
     "intel_dossier": ["📰 Fairtrade Foundation: 'Muressons Fair Trade certification under review — pricing concerns'", "📰 Oxfam: '68% of Muressons cocoa suppliers live below poverty line'", "📰 Reuters: 'Smallholder cocoa farmers threaten to switch to competitor buyers'"]},
    # Q3 — Keep Satisfied
    {"id": "major_retailers", "name": "Retail Distribution Partners", "icon": "🏪",
     "description": "Top 5 retail chains (representing 55% of sales) sent routine contract renewal letters. No flags. Their procurement teams published a sector ESG note but did not mention Muressons.",
     "correct_quadrant": "keep_satisfied", "urgency": "low", "legitimacy": "high",
     "urgency_rationale": "No delisting imminent. Routine engagement sufficient.",
     "intel_dossier": ["📰 Retail Week: 'Major retailers tighten ESG clauses in supplier contracts'", "📰 Internal Sales: 'Annual contract review — all SLAs met'", "📰 IGD: 'FMCG supplier ESG ratings — Muressons rated 'neutral''"]},
    {"id": "pension_fund", "name": "Pension Fund Investors", "icon": "🏦",
     "description": "Hold €1.5B in long-term equity. Sent routine annual review. Their responsible investment desk published a consumer sector note but did not flag Muressons.",
     "correct_quadrant": "keep_satisfied", "urgency": "low", "legitimacy": "high",
     "urgency_rationale": "No covenant breach imminent. Routine engagement.",
     "intel_dossier": ["📰 FT Pensions: 'Pension funds tighten ESG screening for consumer stocks'", "📰 Internal IR: 'Annual pension fund review — all covenants met'", "📰 PRI: 'Consumer sector rated 'developing' on supply chain transparency'"]},
    # Q4 — Monitor
    {"id": "office_cleaner_fmcg", "name": "HQ Office Cleaning Service", "icon": "🧹",
     "description": "Renewed annual contract without negotiation. 12 cleaning staff across 2 offices. Never attended a supplier session.",
     "correct_quadrant": "monitor", "urgency": "low", "legitimacy": "low",
     "urgency_rationale": "No claims, no engagement, no influence.",
     "intel_dossier": ["📰 Procurement Log: 'Cleaning contract auto-renewed — £180K annual'", "📰 No external coverage", "📰 Supplier Survey: 'Cleaning contractor did not respond to ESG questionnaire'"]},
    {"id": "fmcg_general_public", "name": "General Public (Consumers)", "icon": "👥",
     "description": "Brand awareness at 35% but ESG awareness at <3%. Consumers purchase on price and convenience. No trending ESG social media mentions this period.",
     "correct_quadrant": "monitor", "urgency": "low", "legitimacy": "low",
     "urgency_rationale": "Consumer purchasing behaviour driven by price, not ESG.",
     "intel_dossier": ["📰 Brand Tracker: '35% brand awareness, <3% ESG awareness'", "📰 Social Listening: '8 ESG-related mentions this month'", "📰 Consumer Survey: 'Price and convenience rank 1st and 2nd; sustainability ranks 7th'"]},
    # AMBIGUOUS
    {"id": "food_safety_blogger", "name": "Food Safety Investigative Blogger", "icon": "📰",
     "description": "A popular food safety blogger with 180K followers has been testing Muressons products for microplastics. Published 2 viral posts about competitor recalls. Track record of stories triggering recalls.",
     "correct_quadrant": "monitor",
     "alternate_quadrant": "keep_informed",
     "alternate_rationale": "Reasonable case for 'Keep Informed': track record of triggering product recalls. Mitchell et al. (1997): latent power activated by urgency.",
     "urgency": "medium", "legitimacy": "medium",
     "urgency_rationale": "No immediate findings, but active testing creates latent exposure.",
     "intel_dossier": ["📰 Social Media: 'Food blogger announces Muressons microplastic testing series — 180K followers'", "📰 Media Monitor: 'Blogger's previous exposé triggered national product recall at competitor'", "📰 PR Brief: 'Proactive engagement recommended before results published'"]},
]

RETAIL_FMCG_SALIENCE_MIGRATIONS: list[dict[str, Any]] = [
    {"round": 4, "stakeholder": "fmcg_general_public", "from_quadrant": "monitor", "to_quadrant": "manage_closely", "condition_flags": [],
     "narrative": "The child labour exposé went viral on TikTok. Consumer ESG awareness surged from 3% to 45%. #BoycottMuressons is trending.",
     "theory_note": "Mitchell et al. (1997): Dormant stakeholders acquire URGENCY through crisis events."},
    {"round": 4, "stakeholder": "food_safety_blogger", "from_quadrant": "monitor", "to_quadrant": "manage_closely", "condition_flags": [],
     "narrative": "The food safety blogger found microplastic contamination in Muressons packaging and published results. The story triggered regulatory inquiry.",
     "theory_note": "Ackermann & Eden (2011): Media stakeholders have 'latent power' activated by crisis."},
    {"round": 4, "stakeholder": "office_cleaner_fmcg", "from_quadrant": "monitor", "to_quadrant": "keep_informed", "condition_flags": [],
     "narrative": "Cleaning staff report increased workload from protest clean-ups and media visits to HQ.",
     "theory_note": "Freeman (2010): Even peripheral stakeholders are affected by systemic crises."},
    {"round": 6, "stakeholder": "smallholder_farmers", "from_quadrant": "keep_informed", "to_quadrant": "manage_closely", "condition_flags": [],
     "narrative": "An international fair trade NGO adopted the farmers' case. Coordinated supply switch threatens 30% of cocoa supply.",
     "theory_note": "Mitchell et al. (1997): Communities acquired POWER through NGO alliance."},
    {"round": 6, "stakeholder": "pension_fund", "from_quadrant": "keep_satisfied", "to_quadrant": "manage_closely", "condition_flags": ["supply_chain_blindspot"],
     "narrative": "Pension fund ESG desk flagged Muressons for review after the R4 scandal. Divestment review initiated.",
     "theory_note": "Mendelow (1991): 'Keep Satisfied' shifts to 'Manage Closely' when interest activates."},
    {"round": 9, "stakeholder": "store_associates", "from_quadrant": "keep_informed", "to_quadrant": "manage_closely", "condition_flags": [],
     "narrative": "Store associates voted to authorise coordinated action across 200 locations. Union density at 65%.",
     "theory_note": "Mitchell et al. (1997): Workers acquired POWER through collective action."},
    {"round": 9, "stakeholder": "garment_workers", "from_quadrant": "keep_informed", "to_quadrant": "manage_closely", "condition_flags": [],
     "narrative": "ILO enforcement escalated. EU CSDDD gives garment workers in value chain legal standing against Muressons.",
     "theory_note": "EU CSDDD gave these stakeholders regulatory-backed POWER."},
]

# ═══════════════════════════════════════════════════════════════
#  RETAIL/FMCG CSRD ISSUES (20 total)
# ═══════════════════════════════════════════════════════════════

RETAIL_FMCG_CSRD_ISSUES: dict = {
    # Q1 (6)
    "packaging_waste": {"id": "packaging_waste", "title": "Plastic Packaging & Circular Economy Compliance", "hover_description": "42,000 tonnes/yr of plastic packaging. EU PPWR mandates 65% recycled content by 2025. Current rate: 18%. Non-compliance penalties up to 4% of revenue. ESRS E5 mandatory.", "blindspot_description": "Packaging data — recycled content audit incomplete.", "correct_quadrant": 1, "severity": "high", "likelihood": "high", "time_horizon": "short", "disclosure_required": True, "electronics_sensitive": False, "esrs_reference": "ESRS E5 (Resource Use & Circular Economy) / EU PPWR", "stakeholder_voice": None},
    "child_labour_supply": {"id": "child_labour_supply", "title": "Child Labour in Agricultural Supply Chain", "hover_description": "Tier-2 cocoa and palm oil suppliers linked to child labour in West Africa. EU CSDDD creates civil liability for Muressons as buyer. Severity: HIGH.", "blindspot_description": "Supply chain labour audit — tier-2 data incomplete.", "correct_quadrant": 1, "severity": "high", "likelihood": "medium", "time_horizon": "short", "disclosure_required": True, "electronics_sensitive": True, "esrs_reference": "ESRS S2 (Workers in Value Chain) / EU CSDDD", "stakeholder_voice": "suppliers"},
    "food_safety_contam": {"id": "food_safety_contam", "title": "Microplastic Food Contact Contamination", "hover_description": "Independent lab testing detected microplastics in 8 product lines from packaging migration. EU Food Contact Materials regulation under review. Product recall risk. ESRS S4 mandatory.", "blindspot_description": "Food safety data — packaging migration testing incomplete.", "correct_quadrant": 1, "severity": "high", "likelihood": "medium", "time_horizon": "short", "disclosure_required": True, "electronics_sensitive": True, "esrs_reference": "ESRS S4 (Consumers & End-Users) / EU FCM Regulation", "stakeholder_voice": "consumers"},
    "scope3_logistics": {"id": "scope3_logistics", "title": "Scope 3 Distribution & Logistics Emissions", "hover_description": "Last-mile delivery and cold chain logistics generate 65% of total CO₂. SBTi pathway requires 4.2%/yr reduction. ESRS E1 mandatory.", "blindspot_description": "Logistics emissions — third-party carrier data incomplete.", "correct_quadrant": 1, "severity": "high", "likelihood": "high", "time_horizon": "long", "disclosure_required": True, "electronics_sensitive": False, "esrs_reference": "ESRS E1 (Climate Change) / GHG Protocol Scope 3", "stakeholder_voice": None},
    "deforestation_palm": {"id": "deforestation_palm", "title": "Palm Oil Deforestation & EUDR Compliance", "hover_description": "EU Deforestation Regulation requires full traceability to plantation level by 2025. Current traceability: 45%. Non-compliance blocks EU market access. ESRS E4 mandatory.", "blindspot_description": "Deforestation data — plantation-level traceability gaps.", "correct_quadrant": 1, "severity": "high", "likelihood": "high", "time_horizon": "short", "disclosure_required": True, "electronics_sensitive": False, "esrs_reference": "ESRS E4 (Biodiversity) / EU Deforestation Regulation", "stakeholder_voice": None},
    "water_intensive_prod": {"id": "water_intensive_prod", "title": "Water-Intensive Production in Stressed Regions", "hover_description": "3 factories in water-stressed basins consume 8M litres/yr. Local communities depend on same aquifer. CDP Water Security grade: D. ESRS E3 mandatory.", "blindspot_description": "Water consumption — basin-level impact assessment pending.", "correct_quadrant": 1, "severity": "medium", "likelihood": "high", "time_horizon": "short", "disclosure_required": True, "electronics_sensitive": False, "esrs_reference": "ESRS E3 (Water & Marine Resources)", "stakeholder_voice": "local_communities"},
    # Q2 (4)
    "store_worker_wellbeing": {"id": "store_worker_wellbeing", "title": "Retail Worker Mental Health & Zero-Hours", "hover_description": "Store associates on zero-hours contracts report 2× anxiety rates. Financially immaterial. ESRS S1 requires disclosure. Disclosure cost: $140K.", "blindspot_description": "Employee wellbeing — pulse survey not conducted.", "correct_quadrant": 2, "severity": "medium", "likelihood": "high", "time_horizon": "medium", "disclosure_required": True, "electronics_sensitive": False, "esrs_reference": "ESRS S1 §65 (Workforce Wellbeing)", "disclosure_investment_usd": 140_000, "stakeholder_voice": "employees"},
    "nutrition_transparency": {"id": "nutrition_transparency", "title": "Product Nutritional Transparency", "hover_description": "45% of product portfolio classified as HFSS (High Fat Sugar Salt). Financially immaterial. ESRS S4 requires disclosure. Cost: $95K.", "blindspot_description": "Nutritional data — product portfolio assessment needed.", "correct_quadrant": 2, "severity": "medium", "likelihood": "medium", "time_horizon": "medium", "disclosure_required": True, "electronics_sensitive": False, "esrs_reference": "ESRS S4 (Consumers & End-Users)", "disclosure_investment_usd": 95_000, "stakeholder_voice": "consumers"},
    "fair_trade_sourcing": {"id": "fair_trade_sourcing", "title": "Fair Trade Sourcing Impact Reporting", "hover_description": "Fair Trade certified lines generate positive social impact. Financially immaterial. ESRS S2 disclosure. Cost: $70K.", "blindspot_description": "Fair Trade impact — measurement framework missing.", "correct_quadrant": 2, "severity": "medium", "likelihood": "medium", "time_horizon": "medium", "disclosure_required": True, "electronics_sensitive": False, "esrs_reference": "ESRS S2 / Fair Trade Standard", "disclosure_investment_usd": 70_000, "stakeholder_voice": "suppliers"},
    "animal_welfare": {"id": "animal_welfare", "title": "Animal Welfare in Dairy & Meat Supply Chain", "hover_description": "EU proposal for mandatory animal welfare labelling. Current compliance unknown. ESRS E4 disclosure. Cost: $110K.", "blindspot_description": "Animal welfare data — supplier audit incomplete.", "correct_quadrant": 2, "severity": "medium", "likelihood": "medium", "time_horizon": "medium", "disclosure_required": True, "electronics_sensitive": False, "esrs_reference": "ESRS E4 (Biodiversity) / EU Animal Welfare Regulation", "disclosure_investment_usd": 110_000, "stakeholder_voice": None},
    # Q3 (4)
    "commodity_input_prices": {"id": "commodity_input_prices", "title": "Agricultural Commodity Price Volatility", "hover_description": "Cocoa and wheat prices swung ±25% in 12 months. High financial risk. No environmental/social harm. Not ESRS impact-material.", "blindspot_description": "Commodity exposure — procurement analysis needed.", "correct_quadrant": 3, "severity": "low", "likelihood": "high", "time_horizon": "short", "disclosure_required": False, "electronics_sensitive": False, "esrs_reference": "ESRS 2 §SBM-3", "stakeholder_voice": None},
    "private_label_competition": {"id": "private_label_competition", "title": "Private Label Margin Erosion", "hover_description": "Retailer own-brands captured 8% of market share. Competitive dynamics only. Not ESRS impact-material.", "blindspot_description": "Market share — competitive analysis.", "correct_quadrant": 3, "severity": "low", "likelihood": "medium", "time_horizon": "medium", "disclosure_required": False, "electronics_sensitive": False, "esrs_reference": "ESRS 2 §SBM-3", "stakeholder_voice": None},
    "fx_fmcg": {"id": "fx_fmcg", "title": "GBP/EUR Exchange Rate Exposure", "hover_description": "35% foreign revenue creates ±5% revenue swing. Pure financial risk.", "blindspot_description": "FX exposure — treasury review.", "correct_quadrant": 3, "severity": "low", "likelihood": "medium", "time_horizon": "short", "disclosure_required": False, "electronics_sensitive": False, "esrs_reference": "ESRS 2 §SBM-3", "stakeholder_voice": None},
    "shelf_space_fees": {"id": "shelf_space_fees", "title": "Retail Shelf Space Fee Escalation", "hover_description": "Major retailers increasing slotting fees by 12%. Financial pressure only. No ESG impact.", "blindspot_description": "Retail terms — commercial review.", "correct_quadrant": 3, "severity": "low", "likelihood": "high", "time_horizon": "short", "disclosure_required": False, "electronics_sensitive": False, "esrs_reference": None, "stakeholder_voice": None},
    # Q4 (6)
    "office_recycling_fmcg": {"id": "office_recycling_fmcg", "title": "HQ Office Paper Recycling", "hover_description": "Recycles 3 tonnes/yr. Negligible at group scale.", "blindspot_description": "Office waste — minor.", "correct_quadrant": 4, "severity": "low", "likelihood": "high", "time_horizon": "short", "disclosure_required": False, "electronics_sensitive": False, "esrs_reference": None, "stakeholder_voice": None},
    "plastic_bags_fmcg": {"id": "plastic_bags_fmcg", "title": "Reusable Bag Campaign at POS", "hover_description": "Classic greenwashing distractor vs. 42,000 tonnes packaging waste.", "blindspot_description": "POS waste — minor metric.", "correct_quadrant": 4, "severity": "low", "likelihood": "high", "time_horizon": "short", "disclosure_required": False, "electronics_sensitive": False, "esrs_reference": None, "stakeholder_voice": None},
    "exec_travel_fmcg": {"id": "exec_travel_fmcg", "title": "Executive Travel Carbon Offsets", "hover_description": "C-suite flights ~50 tCO₂/yr. <0.01% of total emissions. Symbolic.", "blindspot_description": "Exec travel — HR.", "correct_quadrant": 4, "severity": "low", "likelihood": "high", "time_horizon": "short", "disclosure_required": False, "electronics_sensitive": False, "esrs_reference": None, "stakeholder_voice": None},
    "charity_pr_fmcg": {"id": "charity_pr_fmcg", "title": "Annual Food Bank Donation PR", "hover_description": "Donates unsold stock. Good practice but zero ESG improvement at group level.", "blindspot_description": "CSR spend — marketing.", "correct_quadrant": 4, "severity": "low", "likelihood": "high", "time_horizon": "short", "disclosure_required": False, "electronics_sensitive": False, "esrs_reference": None, "stakeholder_voice": None},
    "ev_fleet_fmcg": {"id": "ev_fleet_fmcg", "title": "EV Company Cars for Sales Team", "hover_description": "Saves ~30 tCO₂/yr. Measurable but immaterial vs. logistics emissions.", "blindspot_description": "Fleet data — procurement.", "correct_quadrant": 4, "severity": "low", "likelihood": "high", "time_horizon": "short", "disclosure_required": False, "electronics_sensitive": False, "esrs_reference": None, "stakeholder_voice": None},
    "fruit_baskets": {"id": "fruit_baskets", "title": "Free Fruit Baskets for HQ Staff", "hover_description": "Good HR practice. Financially negligible.", "blindspot_description": "Staff amenities.", "correct_quadrant": 4, "severity": "low", "likelihood": "high", "time_horizon": "short", "disclosure_required": False, "electronics_sensitive": False, "esrs_reference": None, "stakeholder_voice": None},
}
