"""
Muressons — Oil & Gas Vertical: Stakeholders + CSRD Issues
Replaces: Pharma or Electronics slot (heavy industry, physical assets)
"""
from __future__ import annotations
from typing import Any

# ═══════════════════════════════════════════════════════════════
#  OIL & GAS STAKEHOLDERS (10 total)
# ═══════════════════════════════════════════════════════════════

OIL_GAS_STAKEHOLDERS: list[dict[str, Any]] = [
    # Q1 — Manage Closely
    {"id": "climate_litigators", "name": "Climate Litigation Coalition", "icon": "⚖️",
     "description": "Filed a landmark climate damages lawsuit seeking €2.1B for Scope 1+2 emissions. Backed by 6 European states and supported by IPCC expert witnesses. Court hearing scheduled in 90 days.",
     "correct_quadrant": "manage_closely", "urgency": "high", "legitimacy": "high",
     "urgency_rationale": "Active litigation with court date in 90 days. Existential financial risk.",
     "intel_dossier": ["📰 FT: 'Climate litigation coalition files €2.1B damages claim against Muressons O&G'", "📰 Reuters: 'IPCC scientists agree to testify as expert witnesses in landmark case'", "📰 Guardian: '6 EU states join climate damages suit — largest coordinated action yet'"],
     "engagement_tactics": [
         {"id": "settle_fund", "label": "Establish a €500M climate transition fund and offer structured settlement", "correct": True, "rationale": "Demonstrates good faith while reducing litigation exposure."},
         {"id": "fight_court", "label": "Hire elite defence team to fight the case aggressively", "correct": False, "rationale": "Prolongs reputational damage and risks precedent-setting loss."},
         {"id": "lobby_immunity", "label": "Lobby for legislative immunity for fossil fuel companies", "correct": False, "rationale": "Public backlash and political toxicity far outweigh any protection gained."},
     ]},
    {"id": "pipeline_regulator", "name": "National Pipeline Safety Authority", "icon": "🏛️",
     "description": "Issued 3 compliance notices for pipeline integrity failures in the North Sea corridor. Mandatory inspection deadline in Q3. Fined a peer company €45M for a pipeline rupture last year.",
     "correct_quadrant": "manage_closely", "urgency": "high", "legitimacy": "high",
     "urgency_rationale": "3 compliance notices with Q3 inspection deadline. Operational shutdown risk.",
     "intel_dossier": ["📰 Energy Voice: 'Pipeline safety authority issues triple compliance notice to Muressons'", "📰 Reuters: 'Peer company fined €45M after North Sea pipeline rupture'", "📰 Upstream: 'Muressons added to priority inspection list for 2025 integrity cycle'"],
     "engagement_tactics": [
         {"id": "proactive_integrity", "label": "Commission independent pipeline integrity assessment ahead of deadline", "correct": True, "rationale": "Demonstrates proactive safety culture, may reduce penalty exposure."},
         {"id": "delay_maintenance", "label": "Request 6-month extension citing supply chain delays", "correct": False, "rationale": "Delays increase rupture probability and regulatory suspicion."},
         {"id": "min_response", "label": "Address only the specific cited deficiencies", "correct": False, "rationale": "Minimum compliance invites deeper scrutiny and repeat notices."},
     ]},
    # Q2 — Keep Informed
    {"id": "indigenous_communities", "name": "First Nations Land Council", "icon": "🏕️",
     "description": "Filed a Right to Consultation petition with the federal tribunal over pipeline expansion through ancestral lands. Organised a 500-person peaceful blockade last month. International media covering the standoff.",
     "correct_quadrant": "keep_informed", "urgency": "high", "legitimacy": "high",
     "urgency_rationale": "Active legal petition and escalating protests. High urgency but limited market power.",
     "intel_dossier": ["📰 CBC: 'First Nations blockade enters 3rd week at Muressons pipeline site'", "📰 Al Jazeera: 'Indigenous rights groups call for international boycott of Muressons crude'", "📰 Federal Tribunal: 'Right to Consultation petition accepted — hearing in 60 days'"]},
    {"id": "refinery_workers", "name": "Refinery Floor Workers", "icon": "👷",
     "description": "Shop stewards submitted formal grievance about mandatory overtime during turnaround season. Internal pulse survey shows 65% 'dissatisfied'. Union membership has risen 20% this year.",
     "correct_quadrant": "keep_informed", "urgency": "medium", "legitimacy": "high",
     "urgency_rationale": "Rising union membership signals latent collective action capability.",
     "intel_dossier": ["📰 Internal Memo: 'Q3 pulse survey — 65% dissatisfaction, highest in 6 years'", "📰 Energy Workers Union: 'Membership surges 20% across refining sector'", "📰 HR Brief: 'Formal grievance filed re: mandatory turnaround overtime'"]},
    {"id": "downstream_communities", "name": "Refinery-Adjacent Communities", "icon": "🏘️",
     "description": "Residents within 5km of the Texas refinery report elevated asthma rates. A leaked internal memo shows the company was aware of benzene exceedances for 18 months. Community lawyers are mobilising.",
     "correct_quadrant": "keep_informed", "urgency": "medium", "legitimacy": "high",
     "urgency_rationale": "Leaked memo creates latent litigation exposure. High moral legitimacy.",
     "intel_dossier": ["📰 Houston Chronicle: 'Asthma rates 3× national average near Muressons refinery'", "📰 ProPublica: 'Leaked memo shows Muressons knew about benzene exceedances for 18 months'", "📰 EPA: 'Community air quality petition accepted for review'"]},
    # Q3 — Keep Satisfied
    {"id": "commodity_traders", "name": "Commodity Trading Counterparties", "icon": "📊",
     "description": "Hold $3.2B in forward crude contracts with covenant triggers at 2.5× net debt/EBITDA. Sent routine annual review letter — no flags. Their ESG desk published a sector note but did not mention Muressons.",
     "correct_quadrant": "keep_satisfied", "urgency": "low", "legitimacy": "high",
     "urgency_rationale": "No covenant breach imminent. Routine engagement sufficient.",
     "intel_dossier": ["📰 Platts: 'Commodity traders tighten ESG covenants for new forward contracts'", "📰 Internal Treasury: 'Annual counterparty review — all covenants met'", "📰 S&P Global: 'O&G sector rated 'neutral' on transition risk — no Muressons flag'"]},
    {"id": "host_government", "name": "Host Government Mining Ministry", "icon": "🏛️",
     "description": "Controls exploration licensing and production-sharing agreements. Standard fiscal review completed last quarter with no adverse findings. New carbon border regulations are 24 months away.",
     "correct_quadrant": "keep_satisfied", "urgency": "low", "legitimacy": "high",
     "urgency_rationale": "No active investigation. CBAM is 24+ months from enforcement.",
     "intel_dossier": ["📰 Ministry Gazette: 'Muressons production-sharing agreement renewed — standard terms'", "📰 Reuters: 'Host government drafts carbon export levy — earliest implementation 2027'", "📰 Fiscal Review: 'Muressons rated Green (fully compliant) on royalty payments'"]},
    # Q4 — Monitor
    {"id": "catering_contractor", "name": "Platform Catering Contractor", "icon": "🍽️",
     "description": "Renewed their annual offshore catering contract without negotiation. Serve 400 meals/day across 3 platforms. Have never attended a supplier engagement session.",
     "correct_quadrant": "monitor", "urgency": "low", "legitimacy": "low",
     "urgency_rationale": "No claims, no engagement, no influence pathway.",
     "intel_dossier": ["📰 Procurement Log: 'Offshore catering contract auto-renewed — $2.4M annual'", "📰 No external media coverage", "📰 Supplier Survey: 'Catering contractor did not respond to ESG questionnaire'"]},
    {"id": "og_general_public", "name": "General Public", "icon": "👥",
     "description": "Consumer sentiment survey shows 8% unaided brand awareness for Muressons O&G. No trending social media mentions. A B2B upstream/midstream operator — products rarely reach end consumers directly.",
     "correct_quadrant": "monitor", "urgency": "low", "legitimacy": "low",
     "urgency_rationale": "Low brand awareness. B2B model limits public salience.",
     "intel_dossier": ["📰 Brand Tracker: '8% unaided awareness — unchanged'", "📰 Social Listening: '25 mentions on Twitter/X this month'", "📰 No consumer-facing incidents on record"]},
    # AMBIGUOUS
    {"id": "energy_journalist", "name": "Investigative Energy Journalist", "icon": "📰",
     "description": "A well-connected reporter at an energy trade publication has been requesting interviews about methane emissions. Published 4 articles about competitor greenwashing. Has 95K followers and a track record of triggering regulatory inquiries.",
     "correct_quadrant": "monitor",
     "alternate_quadrant": "keep_informed",
     "alternate_rationale": "Reasonable case for 'Keep Informed': track record of triggering regulatory inquiries means a negative story could rapidly escalate. Mitchell et al. (1997): latent power activated by urgency.",
     "urgency": "medium", "legitimacy": "medium",
     "urgency_rationale": "No immediate deadline, but investigative interest creates latent exposure.",
     "intel_dossier": ["📰 Press Office: 'Interview request from M. Torres, Upstream — 3rd this quarter'", "📰 Media Monitor: 'Torres methane investigation syndicated to Bloomberg (reach: 5M)'", "📰 X/Twitter: 'Reporter's thread on fossil fuel greenwashing got 18K engagements'"]},
]

OIL_GAS_SALIENCE_MIGRATIONS: list[dict[str, Any]] = [
    {"round": 4, "stakeholder": "og_general_public", "from_quadrant": "monitor", "to_quadrant": "manage_closely", "condition_flags": [],
     "narrative": "A catastrophic pipeline spill went viral on social media. Public awareness surged from 8% to 65% in 48 hours. #BoycottMuressons is trending.",
     "theory_note": "Mitchell et al. (1997): Dormant stakeholders acquire URGENCY through crisis events."},
    {"round": 4, "stakeholder": "energy_journalist", "from_quadrant": "monitor", "to_quadrant": "manage_closely", "condition_flags": [],
     "narrative": "The energy journalist broke the spill story internationally. Their investigation triggered an EPA emergency review.",
     "theory_note": "Ackermann & Eden (2011): Media stakeholders have 'latent power' activated by crisis."},
    {"round": 4, "stakeholder": "catering_contractor", "from_quadrant": "monitor", "to_quadrant": "keep_informed", "condition_flags": [],
     "narrative": "Platform catering contractor reports staff refusing offshore rotations due to safety fears following the spill.",
     "theory_note": "Freeman (2010): Even peripheral stakeholders are affected by systemic crises."},
    {"round": 6, "stakeholder": "indigenous_communities", "from_quadrant": "keep_informed", "to_quadrant": "manage_closely", "condition_flags": [],
     "narrative": "An international NGO adopted the First Nations land rights case. The community now has legal representation and credible threat of operational injunction.",
     "theory_note": "Mitchell et al. (1997): Communities acquired POWER through NGO alliance."},
    {"round": 6, "stakeholder": "commodity_traders", "from_quadrant": "keep_satisfied", "to_quadrant": "manage_closely", "condition_flags": ["refinery_blindspot"],
     "narrative": "Commodity traders' ESG desk flagged Muressons for review after the R4 spill. Contract renegotiation is on the table.",
     "theory_note": "Mendelow (1991): 'Keep Satisfied' shifts to 'Manage Closely' when interest activates."},
    {"round": 9, "stakeholder": "refinery_workers", "from_quadrant": "keep_informed", "to_quadrant": "manage_closely", "condition_flags": [],
     "narrative": "Refinery workers voted to authorise a strike over just transition concerns. Union membership at 82%.",
     "theory_note": "Mitchell et al. (1997): Workers acquired POWER through unionisation."},
    {"round": 9, "stakeholder": "downstream_communities", "from_quadrant": "keep_informed", "to_quadrant": "manage_closely", "condition_flags": [],
     "narrative": "Community lawyers filed a class action for health damages. EU CSDDD gives affected communities direct legal standing.",
     "theory_note": "EU CSDDD gave these stakeholders regulatory-backed POWER."},
]

# ═══════════════════════════════════════════════════════════════
#  OIL & GAS CSRD ISSUES (20 total)
# ═══════════════════════════════════════════════════════════════

OIL_GAS_CSRD_ISSUES: dict = {
    # Q1 (6)
    "methane_leakage": {"id": "methane_leakage", "title": "Fugitive Methane Emissions", "hover_description": "Satellite monitoring reveals 12,000 tonnes/yr of unaccounted methane from wellheads and pipelines. 80× CO₂ warming potential over 20 years. EU Methane Regulation mandates LDAR by 2025. Severity: HIGH. ESRS E1 mandatory.", "blindspot_description": "Methane emissions — satellite data not integrated into reporting.", "correct_quadrant": 1, "severity": "high", "likelihood": "high", "time_horizon": "short", "disclosure_required": True, "electronics_sensitive": False, "esrs_reference": "ESRS E1 (Climate Change) / EU Methane Regulation", "stakeholder_voice": None},
    "stranded_reserves": {"id": "stranded_reserves", "title": "Stranded Asset Risk — Proven Reserves", "hover_description": "IEA Net Zero pathway implies 40% of proven reserves become unburnable by 2035. €8.2B book value at risk of impairment. Severity: HIGH. ESRS E1 + IFRS S2 mandatory.", "blindspot_description": "Reserve valuation — climate scenario analysis not completed.", "correct_quadrant": 1, "severity": "high", "likelihood": "high", "time_horizon": "medium", "disclosure_required": True, "electronics_sensitive": False, "esrs_reference": "ESRS E1 / IFRS S2 (Climate-Related Disclosures)", "stakeholder_voice": None},
    "pipeline_spill_risk": {"id": "pipeline_spill_risk", "title": "Pipeline Integrity & Spill Risk", "hover_description": "3 compliance notices for corrosion in North Sea pipeline. Historical spill rate 2× industry average. EU Environmental Liability Directive exposure. Severity: HIGH. ESRS E2 mandatory.", "blindspot_description": "Pipeline integrity data — corrosion audit incomplete.", "correct_quadrant": 1, "severity": "high", "likelihood": "medium", "time_horizon": "short", "disclosure_required": True, "electronics_sensitive": True, "esrs_reference": "ESRS E2 (Pollution) / EU ELD", "stakeholder_voice": "local_communities"},
    "indigenous_land_rights": {"id": "indigenous_land_rights", "title": "Indigenous Land Rights & FPIC", "hover_description": "Pipeline expansion crosses ancestral territories without Free, Prior and Informed Consent (FPIC). UN Declaration on Indigenous Rights. Severity: HIGH. ESRS S3 mandatory.", "blindspot_description": "FPIC documentation — consultation records incomplete.", "correct_quadrant": 1, "severity": "high", "likelihood": "medium", "time_horizon": "short", "disclosure_required": True, "electronics_sensitive": False, "esrs_reference": "ESRS S3 (Affected Communities) / UNDRIP", "stakeholder_voice": "suppliers"},
    "scope3_downstream": {"id": "scope3_downstream", "title": "Scope 3 Downstream Combustion Emissions", "hover_description": "Customer combustion of sold products generates 15× more CO₂ than operations. At $250/tCO₂ terminal tax, trajectory costs $45M at R10. ESRS E1 mandatory.", "blindspot_description": "Downstream emission profile — customer data unavailable.", "correct_quadrant": 1, "severity": "high", "likelihood": "high", "time_horizon": "long", "disclosure_required": True, "electronics_sensitive": False, "esrs_reference": "ESRS E1 (Climate Change) / GHG Protocol Scope 3", "stakeholder_voice": None},
    "produced_water": {"id": "produced_water", "title": "Produced Water Contamination", "hover_description": "Drilling operations generate 8M barrels/yr of produced water containing BTEX compounds. Aquifer contamination risk in water-stressed regions. Severity: HIGH. ESRS E3 mandatory.", "blindspot_description": "Water contamination data — disposal site audit pending.", "correct_quadrant": 1, "severity": "medium", "likelihood": "high", "time_horizon": "short", "disclosure_required": True, "electronics_sensitive": True, "esrs_reference": "ESRS E3 (Water & Marine Resources)", "stakeholder_voice": "local_communities"},
    # Q2 (4)
    "worker_health_monitoring": {"id": "worker_health_monitoring", "title": "Offshore Worker Health Monitoring", "hover_description": "Long-rotation offshore workers show elevated cardiovascular risk. Financially immaterial but ESRS S1 requires disclosure. Disclosure cost: $180K.", "blindspot_description": "Occupational health data — long-term study not conducted.", "correct_quadrant": 2, "severity": "medium", "likelihood": "high", "time_horizon": "medium", "disclosure_required": True, "electronics_sensitive": False, "esrs_reference": "ESRS S1 §65 (Workforce Health)", "disclosure_investment_usd": 180_000, "stakeholder_voice": "employees"},
    "community_development": {"id": "community_development", "title": "Host Community Development Fund", "hover_description": "Production-sharing agreements mandate community investment. Real impact but financially immaterial. ESRS S3 requires disclosure. Disclosure cost: $90K.", "blindspot_description": "Community investment data — insufficient documentation.", "correct_quadrant": 2, "severity": "medium", "likelihood": "high", "time_horizon": "medium", "disclosure_required": True, "electronics_sensitive": False, "esrs_reference": "ESRS S3 (Affected Communities)", "disclosure_investment_usd": 90_000, "stakeholder_voice": "local_communities"},
    "flaring_reduction": {"id": "flaring_reduction", "title": "Routine Gas Flaring Reduction Programme", "hover_description": "Voluntary Zero Routine Flaring commitment. Positive environmental impact but financially immaterial. ESRS E1 disclosure. Disclosure cost: $75K.", "blindspot_description": "Flaring data — measurement framework not established.", "correct_quadrant": 2, "severity": "medium", "likelihood": "medium", "time_horizon": "medium", "disclosure_required": True, "electronics_sensitive": False, "esrs_reference": "ESRS E1 (Climate Change)", "disclosure_investment_usd": 75_000, "stakeholder_voice": None},
    "supply_chain_wages": {"id": "supply_chain_wages", "title": "Contractor Living Wage Standardization", "hover_description": "Gap between minimum and living wage at tier-2 service contractors affects ~5,000 workers. ESRS S2 mandatory. Disclosure cost: $200K.", "blindspot_description": "Contractor wage data — supply chain audit incomplete.", "correct_quadrant": 2, "severity": "high", "likelihood": "high", "time_horizon": "short", "disclosure_required": True, "electronics_sensitive": True, "esrs_reference": "ESRS S2 (Workers in Value Chain)", "disclosure_investment_usd": 200_000, "stakeholder_voice": "suppliers"},
    # Q3 (4)
    "crude_price_volatility": {"id": "crude_price_volatility", "title": "Brent Crude Price Volatility", "hover_description": "Spot prices swung ±30% in 12 months. High financial risk. No environmental/social harm from price fluctuation. Not ESRS impact-material.", "blindspot_description": "Commodity exposure — trading desk data missing.", "correct_quadrant": 3, "severity": "low", "likelihood": "high", "time_horizon": "short", "disclosure_required": False, "electronics_sensitive": False, "esrs_reference": "ESRS 2 §SBM-3 (Material Risks)", "stakeholder_voice": None},
    "refinery_margin": {"id": "refinery_margin", "title": "Refinery Crack Spread Compression", "hover_description": "EV adoption reducing gasoline demand. Crack spreads compressed 15% YoY. Financial risk only. Not ESRS impact-material.", "blindspot_description": "Demand forecast data — market analysis needed.", "correct_quadrant": 3, "severity": "low", "likelihood": "medium", "time_horizon": "medium", "disclosure_required": False, "electronics_sensitive": False, "esrs_reference": "ESRS 2 §SBM-3 (Competitive Risk)", "stakeholder_voice": None},
    "fx_petrodollar": {"id": "fx_petrodollar", "title": "Petrodollar FX Exposure", "hover_description": "USD-denominated revenues vs. EUR/GBP cost base creates ±10% margin swing. Pure financial risk. Not ESRS impact-material.", "blindspot_description": "FX exposure — treasury data review needed.", "correct_quadrant": 3, "severity": "low", "likelihood": "medium", "time_horizon": "short", "disclosure_required": False, "electronics_sensitive": False, "esrs_reference": "ESRS 2 §SBM-3 (Financial Risk)", "stakeholder_voice": None},
    "windfall_tax": {"id": "windfall_tax", "title": "Energy Windfall Profit Tax", "hover_description": "EU Energy Crisis windfall levy affects supernormal profits. Est. €6M additional tax liability. Governance disclosure under ESRS G1.", "blindspot_description": "Tax structure exposure — group finance review required.", "correct_quadrant": 3, "severity": "low", "likelihood": "high", "time_horizon": "short", "disclosure_required": False, "electronics_sensitive": False, "esrs_reference": "ESRS G1 §37 (Tax Transparency)", "stakeholder_voice": None},
    # Q4 (6)
    "office_recycling_og": {"id": "office_recycling_og", "title": "HQ Paper Recycling", "hover_description": "HQ recycles 5 tonnes/yr. Negligible vs. operational emissions. Not CSRD-material.", "blindspot_description": "Office waste — minor metric.", "correct_quadrant": 4, "severity": "low", "likelihood": "high", "time_horizon": "short", "disclosure_required": False, "electronics_sensitive": False, "esrs_reference": None, "stakeholder_voice": None},
    "plastic_cups_og": {"id": "plastic_cups_og", "title": "Eliminating Single-Use Cups on Platforms", "hover_description": "~15,000 cups eliminated/yr. Classic greenwashing distractor vs. 45,000 tonnes CO₂.", "blindspot_description": "Platform waste — minor metric.", "correct_quadrant": 4, "severity": "low", "likelihood": "high", "time_horizon": "short", "disclosure_required": False, "electronics_sensitive": False, "esrs_reference": None, "stakeholder_voice": None},
    "exec_jet_offsets": {"id": "exec_jet_offsets", "title": "Executive Private Jet Carbon Offsets", "hover_description": "C-suite flights generate ~200 tCO₂/yr — <0.001% of total emissions. Symbolic. Governance red flag.", "blindspot_description": "Executive travel — HR records.", "correct_quadrant": 4, "severity": "low", "likelihood": "high", "time_horizon": "short", "disclosure_required": False, "electronics_sensitive": False, "esrs_reference": None, "stakeholder_voice": None},
    "energy_day_pr": {"id": "energy_day_pr", "title": "Annual Energy Transition Day PR Campaign", "hover_description": "PR campaign while operating fossil fuel assets. Greenwashing risk under EU Green Claims Directive.", "blindspot_description": "PR spend — marketing records.", "correct_quadrant": 4, "severity": "low", "likelihood": "high", "time_horizon": "short", "disclosure_required": False, "electronics_sensitive": False, "esrs_reference": "EU Green Claims Directive", "stakeholder_voice": None},
    "ergonomic_rigs": {"id": "ergonomic_rigs", "title": "Ergonomic Equipment for Rig Workers", "hover_description": "Good HSE practice. Financially negligible. Not CSRD-material at group level.", "blindspot_description": "Workplace ergonomics — HSE records.", "correct_quadrant": 4, "severity": "low", "likelihood": "high", "time_horizon": "short", "disclosure_required": False, "electronics_sensitive": False, "esrs_reference": None, "stakeholder_voice": None},
    "led_platforms": {"id": "led_platforms", "title": "LED Lighting Retrofit on Offshore Platforms", "hover_description": "Saves ~12 tCO₂/yr. Immaterial vs. operational emissions. Not ESRS-material.", "blindspot_description": "Energy data — facilities records.", "correct_quadrant": 4, "severity": "low", "likelihood": "high", "time_horizon": "short", "disclosure_required": False, "electronics_sensitive": False, "esrs_reference": None, "stakeholder_voice": None},
}
