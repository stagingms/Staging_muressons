"""
Muressons — Banking & Financial Services Vertical: Stakeholders + CSRD Issues
Replaces: Software slot (asset-light, governance-heavy)
"""
from __future__ import annotations
from typing import Any

# ═══════════════════════════════════════════════════════════════
#  BANKING & FINANCIAL SERVICES STAKEHOLDERS (10 total)
# ═══════════════════════════════════════════════════════════════

BANKING_FS_STAKEHOLDERS: list[dict[str, Any]] = [
    # Q1 — Manage Closely
    {"id": "central_bank_supervisor", "name": "Central Bank Prudential Supervisor", "icon": "🏛️",
     "description": "Issued a formal inquiry into Muressons' financed emissions disclosure after reviewing the TCFD report. Mandatory stress test under ECB climate scenario analysis due in Q3. Fined a peer bank €30M for inadequate ESG risk modelling last year.",
     "correct_quadrant": "manage_closely", "urgency": "high", "legitimacy": "high",
     "urgency_rationale": "Formal inquiry with Q3 stress test deadline. Regulatory licence at risk.",
     "intel_dossier": ["📰 ECB: 'Prudential supervisor flags Muressons for inadequate climate stress testing'", "📰 FT: 'Peer bank fined €30M for ESG risk model deficiencies'", "📰 Reuters: 'Muressons added to priority supervision list for 2025 climate review'"],
     "engagement_tactics": [
         {"id": "voluntary_stress", "label": "Submit voluntary climate stress test results ahead of ECB deadline", "correct": True, "rationale": "Demonstrates proactive risk management, may reduce supervisory intensity."},
         {"id": "lobby_delay_ecb", "label": "Lobby ECB through trade association to delay enforcement timeline", "correct": False, "rationale": "Regulatory capture attempt — reputational disaster in post-GFC banking."},
         {"id": "min_compliance", "label": "Wait for formal requirements and respond with minimum data", "correct": False, "rationale": "Reactive posture invites maximum supervisory scrutiny."},
     ]},
    {"id": "esg_activist_investor", "name": "Responsible Investment Activist", "icon": "🦅",
     "description": "Filed 3 shareholder resolutions demanding fossil fuel lending phase-out by 2030. Building a 5% blocking stake. Published a 120-page report titled 'Muressons: Banking on Extinction' with detailed portfolio carbon analysis.",
     "correct_quadrant": "manage_closely", "urgency": "high", "legitimacy": "high",
     "urgency_rationale": "Active proxy fight with AGM in 90 days. Research report generating media coverage.",
     "intel_dossier": ["📰 Bloomberg: 'Activist fund publishes 'Banking on Extinction' — targets Muressons fossil portfolio'", "📰 FT: 'ESG activist acquires 4.2% stake, signals AGM proxy fight'", "📰 Reuters: 'Muressons' financed emissions 3× peer average — activist report'"],
     "engagement_tactics": [
         {"id": "transition_plan", "label": "Publish credible fossil fuel lending transition plan with 2030 targets", "correct": True, "rationale": "Addresses core demand with measurable commitments."},
         {"id": "buyback_dilute", "label": "Launch share buyback to dilute activist's stake", "correct": False, "rationale": "Defensive financial engineering signals fear, not engagement."},
         {"id": "reject_publicly", "label": "Publish open letter rejecting the report's methodology", "correct": False, "rationale": "Confrontational stance mobilises other ESG investors against management."},
     ]},
    # Q2 — Keep Informed
    {"id": "consumer_debtors", "name": "Distressed Consumer Borrowers", "icon": "👨‍👩‍👧‍👦",
     "description": "Cost-of-living crisis has pushed mortgage arrears to 8-year high. 12,000 customers in financial hardship programmes. Consumer advocacy groups demanding interest rate forbearance. Low market power but high moral legitimacy.",
     "correct_quadrant": "keep_informed", "urgency": "medium", "legitimacy": "high",
     "urgency_rationale": "Rising arrears and advocacy group pressure. High moral legitimacy.",
     "intel_dossier": ["📰 BBC: 'Mortgage arrears surge to 8-year high as cost-of-living bites'", "📰 Consumer Rights: 'Advocacy group demands 12-month interest rate cap for distressed borrowers'", "📰 FCA: 'Consumer Duty rules require enhanced forbearance procedures'"]},
    {"id": "branch_staff", "name": "Retail Branch Staff", "icon": "👷",
     "description": "Announced closure of 45 branches, affecting 1,200 employees. Union has submitted formal grievance. Internal survey shows 72% fear further job losses from AI automation. Financial inclusion groups protesting closures in rural areas.",
     "correct_quadrant": "keep_informed", "urgency": "medium", "legitimacy": "high",
     "urgency_rationale": "Active restructuring with union grievance. Latent strike risk.",
     "intel_dossier": ["📰 Internal Memo: 'Branch closure programme — 45 locations, 1,200 FTE affected'", "📰 Financial Times: 'Banking union threatens coordinated action over branch closures'", "📰 HR Brief: 'Formal grievance filed re: consultation period for branch closures'"]},
    {"id": "whistleblower_network", "name": "Internal Compliance Whistleblowers", "icon": "🔔",
     "description": "Anonymous tip to the financial ombudsman alleges systematic under-reporting of financed emissions in the loan book. Internal audit found discrepancies in 3 portfolios. Whistleblower protection laws apply.",
     "correct_quadrant": "keep_informed", "urgency": "high", "legitimacy": "high",
     "urgency_rationale": "Whistleblower complaint creates regulatory referral risk. Protected status limits management options.",
     "intel_dossier": ["📰 Internal Audit: 'Discrepancies found in financed emissions reporting across 3 portfolios'", "📰 Financial Ombudsman: 'Anonymous tip received — preliminary review initiated'", "📰 Compliance Brief: 'Whistleblower protection regime — management cannot take adverse action'"]},
    # Q3 — Keep Satisfied
    {"id": "institutional_depositors", "name": "Institutional Depositors", "icon": "🏢",
     "description": "Hold €8B in term deposits with covenant triggers at Tier 1 capital ratios. Sent routine annual review letter. Their ESG desk published a banking sector note but did not mention Muressons specifically.",
     "correct_quadrant": "keep_satisfied", "urgency": "low", "legitimacy": "high",
     "urgency_rationale": "No covenant breach imminent. Routine relationship management.",
     "intel_dossier": ["📰 Internal Treasury: 'Institutional deposit renewals — all Tier 1 covenants met'", "📰 Moody's: 'Banking sector ESG assessment — Muressons rated 'neutral''", "📰 Risk Monitor: 'No deposit flight signals detected in current quarter'"]},
    {"id": "payments_regulator", "name": "Payments Systems Regulator", "icon": "⚖️",
     "description": "Completed routine annual compliance review — no adverse findings. Published guidance on digital payments accessibility that may require minor system updates within 18 months.",
     "correct_quadrant": "keep_satisfied", "urgency": "low", "legitimacy": "high",
     "urgency_rationale": "No active enforcement. Accessibility guidance has 18-month implementation window.",
     "intel_dossier": ["📰 PSR: 'Annual compliance review — Muressons rated 'fully compliant''", "📰 Regulatory Gazette: 'Digital payments accessibility guidance published — 18-month transition'", "📰 Internal Compliance: 'System updates budgeted at €2.1M for accessibility compliance'"]},
    # Q4 — Monitor
    {"id": "atm_maintenance", "name": "ATM Maintenance Contractor", "icon": "🔧",
     "description": "Renewed annual contract without negotiation. Maintains 2,400 ATMs nationally. Has never attended a supplier engagement session.",
     "correct_quadrant": "monitor", "urgency": "low", "legitimacy": "low",
     "urgency_rationale": "No claims, no engagement, no influence pathway.",
     "intel_dossier": ["📰 Procurement Log: 'ATM maintenance contract auto-renewed — €3.2M annual'", "📰 No external media coverage", "📰 Supplier Survey: 'ATM contractor did not respond to ESG questionnaire'"]},
    {"id": "banking_general_public", "name": "General Public", "icon": "👥",
     "description": "Consumer banking awareness is 22% but Muressons' corporate/investment banking arm (the ESG-sensitive unit) has <5% public awareness. No trending social media mentions.",
     "correct_quadrant": "monitor", "urgency": "low", "legitimacy": "low",
     "urgency_rationale": "Low awareness of corporate banking activities. Retail banking brand is separate.",
     "intel_dossier": ["📰 Brand Tracker: '22% retail awareness but <5% for corporate/investment banking'", "📰 Social Listening: '12 mentions this month re: corporate banking ESG'", "📰 No consumer-facing incidents on record"]},
    # AMBIGUOUS
    {"id": "banking_journalist", "name": "Financial Investigations Journalist", "icon": "📰",
     "description": "A respected journalist at a financial daily has been FOIA-requesting Muressons' fossil fuel loan book details. Published 3 exposés on competitor greenwashing in banking. Has 200K followers and a Pulitzer nomination.",
     "correct_quadrant": "monitor",
     "alternate_quadrant": "keep_informed",
     "alternate_rationale": "Reasonable case for 'Keep Informed': Pulitzer-calibre investigative journalist with FOIA powers. A negative exposé could trigger regulatory referral. Mitchell et al. (1997): latent power activated by urgency.",
     "urgency": "medium", "legitimacy": "medium",
     "urgency_rationale": "No immediate deadline, but FOIA requests signal active investigation.",
     "intel_dossier": ["📰 Press Office: 'FOIA request from J. Whitfield, Financial Times — 5th this quarter'", "📰 Media Monitor: 'Whitfield's banking greenwashing series syndicated to NYT (reach: 10M)'", "📰 X/Twitter: 'Reporter's thread on financed emissions got 30K engagements'"]},
]

BANKING_FS_SALIENCE_MIGRATIONS: list[dict[str, Any]] = [
    {"round": 4, "stakeholder": "banking_general_public", "from_quadrant": "monitor", "to_quadrant": "manage_closely", "condition_flags": [],
     "narrative": "The financed emissions scandal went viral. Public awareness surged after a major newspaper published Muressons' fossil fuel loan book. #DivestMuressons is trending.",
     "theory_note": "Mitchell et al. (1997): Dormant stakeholders acquire URGENCY through crisis events."},
    {"round": 4, "stakeholder": "banking_journalist", "from_quadrant": "monitor", "to_quadrant": "manage_closely", "condition_flags": [],
     "narrative": "The financial journalist's exposé was syndicated globally. Parliamentary inquiry announced into banking sector greenwashing.",
     "theory_note": "Ackermann & Eden (2011): Media stakeholders have 'latent power' activated by crisis."},
    {"round": 4, "stakeholder": "atm_maintenance", "from_quadrant": "monitor", "to_quadrant": "keep_informed", "condition_flags": [],
     "narrative": "ATM maintenance contractor reports vandalism incidents at branches linked to the greenwashing scandal.",
     "theory_note": "Freeman (2010): Even peripheral stakeholders are affected by systemic crises."},
    {"round": 6, "stakeholder": "whistleblower_network", "from_quadrant": "keep_informed", "to_quadrant": "manage_closely", "condition_flags": [],
     "narrative": "The whistleblower's complaint escalated to a formal regulatory investigation. Internal audit findings leaked to media.",
     "theory_note": "Mitchell et al. (1997): Whistleblowers acquired POWER through regulatory backing."},
    {"round": 6, "stakeholder": "institutional_depositors", "from_quadrant": "keep_satisfied", "to_quadrant": "manage_closely", "condition_flags": ["governance_blindspot"],
     "narrative": "Institutional depositors triggered ESG covenant review clause after the R4 scandal. €2B in deposits up for renegotiation.",
     "theory_note": "Mendelow (1991): 'Keep Satisfied' shifts to 'Manage Closely' when interest activates."},
    {"round": 9, "stakeholder": "branch_staff", "from_quadrant": "keep_informed", "to_quadrant": "manage_closely", "condition_flags": [],
     "narrative": "Branch staff voted to authorise industrial action. Union membership at 78%. AI automation fears compounded by restructuring.",
     "theory_note": "Mitchell et al. (1997): Workers acquired POWER through collective action."},
    {"round": 9, "stakeholder": "consumer_debtors", "from_quadrant": "keep_informed", "to_quadrant": "manage_closely", "condition_flags": [],
     "narrative": "Consumer advocacy groups filed a super-complaint with the regulator. FCA Consumer Duty enforcement gives borrowers enhanced legal standing.",
     "theory_note": "FCA Consumer Duty gave these stakeholders regulatory-backed POWER."},
]

# ═══════════════════════════════════════════════════════════════
#  BANKING & FINANCIAL SERVICES CSRD ISSUES (20 total)
# ═══════════════════════════════════════════════════════════════

BANKING_FS_CSRD_ISSUES: dict = {
    # Q1 (6)
    "financed_emissions": {"id": "financed_emissions", "title": "Financed Emissions — Loan Portfolio", "hover_description": "Portfolio carbon intensity 3× peer average. €12B in fossil fuel exposure. PCAF methodology shows 2.8M tCO₂e financed. ESRS E1 mandatory + ECB climate stress test.", "blindspot_description": "Financed emissions — PCAF data collection incomplete.", "correct_quadrant": 1, "severity": "high", "likelihood": "high", "time_horizon": "short", "disclosure_required": True, "electronics_sensitive": False, "esrs_reference": "ESRS E1 / PCAF Standard / ECB Climate Stress Test", "stakeholder_voice": None},
    "aml_sanctions": {"id": "aml_sanctions", "title": "Anti-Money Laundering & Sanctions Compliance", "hover_description": "Internal audit found 340 accounts with incomplete KYC. 3 correspondent banking relationships under sanctions review. EU 6AMLD creates personal criminal liability for board. Severity: CRITICAL.", "blindspot_description": "AML data — KYC remediation backlog.", "correct_quadrant": 1, "severity": "high", "likelihood": "high", "time_horizon": "short", "disclosure_required": True, "electronics_sensitive": True, "esrs_reference": "ESRS G1 (Business Conduct) / EU 6AMLD", "stakeholder_voice": None},
    "systemic_risk": {"id": "systemic_risk", "title": "Systemic Risk & Interconnectedness", "hover_description": "Interbank exposure concentration exceeds Basel III guidelines. Stress test reveals Tier 1 ratio drops below 8% under adverse scenario. ECB SREP mandatory.", "blindspot_description": "Interconnectedness data — stress test model validation needed.", "correct_quadrant": 1, "severity": "high", "likelihood": "medium", "time_horizon": "short", "disclosure_required": True, "electronics_sensitive": False, "esrs_reference": "ESRS G1 / Basel III Pillar 3 / ECB SREP", "stakeholder_voice": None},
    "predatory_lending": {"id": "predatory_lending", "title": "Predatory Lending Practices", "hover_description": "Consumer credit products with effective APR >40% marketed to vulnerable borrowers. FCA Consumer Duty requires assessment of consumer outcomes. Est. £15M redress liability.", "blindspot_description": "Consumer outcomes data — product review incomplete.", "correct_quadrant": 1, "severity": "high", "likelihood": "medium", "time_horizon": "short", "disclosure_required": True, "electronics_sensitive": False, "esrs_reference": "ESRS S4 (Consumers & End-Users) / FCA Consumer Duty", "stakeholder_voice": "consumers"},
    "cyber_breach_risk": {"id": "cyber_breach_risk", "title": "Cybersecurity & Customer Data Breach Risk", "hover_description": "2 near-miss incidents in 12 months. 14M customer records at risk. DORA (Digital Operational Resilience Act) mandatory from 2025. Severity: HIGH.", "blindspot_description": "Cyber resilience — penetration test findings not remediated.", "correct_quadrant": 1, "severity": "high", "likelihood": "medium", "time_horizon": "short", "disclosure_required": True, "electronics_sensitive": True, "esrs_reference": "ESRS G1 / EU DORA", "stakeholder_voice": None},
    "living_wage_outsourced": {"id": "living_wage_outsourced", "title": "Outsourced Operations Living Wage", "hover_description": "Call centre and IT operations outsourced to 4 countries. Living wage gap affects ~8,000 workers. ESRS S2 mandatory.", "blindspot_description": "Supply chain wage data — outsourced audit incomplete.", "correct_quadrant": 1, "severity": "medium", "likelihood": "high", "time_horizon": "short", "disclosure_required": True, "electronics_sensitive": True, "esrs_reference": "ESRS S2 (Workers in Value Chain)", "stakeholder_voice": "suppliers"},
    # Q2 (4)
    "financial_inclusion": {"id": "financial_inclusion", "title": "Financial Inclusion & Unbanked Access", "hover_description": "Branch closures leave 180 communities without banking access. Financially immaterial but ESRS S4 requires disclosure. Disclosure cost: $120K.", "blindspot_description": "Financial inclusion data — community impact assessment needed.", "correct_quadrant": 2, "severity": "medium", "likelihood": "high", "time_horizon": "medium", "disclosure_required": True, "electronics_sensitive": False, "esrs_reference": "ESRS S4 (Consumers & End-Users)", "disclosure_investment_usd": 120_000, "stakeholder_voice": "consumers"},
    "employee_mental_health": {"id": "employee_mental_health", "title": "Employee Mental Health in High-Pressure Roles", "hover_description": "Trading floor and investment banking staff report burnout at 3× industry average. Financially immaterial but ESRS S1 requires disclosure. Disclosure cost: $100K.", "blindspot_description": "Employee wellbeing — occupational health study needed.", "correct_quadrant": 2, "severity": "medium", "likelihood": "high", "time_horizon": "medium", "disclosure_required": True, "electronics_sensitive": False, "esrs_reference": "ESRS S1 §65 (Workforce Wellbeing)", "disclosure_investment_usd": 100_000, "stakeholder_voice": "employees"},
    "green_bond_impact": {"id": "green_bond_impact", "title": "Green Bond Framework Impact Reporting", "hover_description": "€3B green bond programme. Real environmental impact but financially immaterial. EU Green Bond Standard requires impact verification. Cost: $80K.", "blindspot_description": "Green bond impact — verification framework not established.", "correct_quadrant": 2, "severity": "medium", "likelihood": "medium", "time_horizon": "medium", "disclosure_required": True, "electronics_sensitive": False, "esrs_reference": "EU Green Bond Standard / ESRS E1", "disclosure_investment_usd": 80_000, "stakeholder_voice": None},
    "whistleblower_channel": {"id": "whistleblower_channel", "title": "Whistleblower Channel Effectiveness", "hover_description": "EU Whistleblower Directive requires robust internal reporting. Current channel utilisation low. ESRS G1 disclosure. Cost: $60K.", "blindspot_description": "Whistleblower data — channel assessment incomplete.", "correct_quadrant": 2, "severity": "medium", "likelihood": "medium", "time_horizon": "medium", "disclosure_required": True, "electronics_sensitive": False, "esrs_reference": "ESRS G1 / EU Whistleblower Directive", "disclosure_investment_usd": 60_000, "stakeholder_voice": None},
    # Q3 (4)
    "interest_rate_nim": {"id": "interest_rate_nim", "title": "Net Interest Margin Compression", "hover_description": "Central bank rate cuts compressing NIM by 15bps. High financial risk. No environmental/social harm. Not ESRS impact-material.", "blindspot_description": "NIM data — ALM model update needed.", "correct_quadrant": 3, "severity": "low", "likelihood": "high", "time_horizon": "short", "disclosure_required": False, "electronics_sensitive": False, "esrs_reference": "ESRS 2 §SBM-3 (Material Risks)", "stakeholder_voice": None},
    "fintech_competition": {"id": "fintech_competition", "title": "Fintech Market Share Erosion", "hover_description": "Digital-only banks captured 12% of retail deposit growth. Competitive dynamics only. Not ESRS impact-material.", "blindspot_description": "Market share — competitive analysis needed.", "correct_quadrant": 3, "severity": "low", "likelihood": "medium", "time_horizon": "medium", "disclosure_required": False, "electronics_sensitive": False, "esrs_reference": "ESRS 2 §SBM-3 (Competitive Risk)", "stakeholder_voice": None},
    "fx_trading_exposure": {"id": "fx_trading_exposure", "title": "Proprietary FX Trading Exposure", "hover_description": "Trading desk VaR at 95th percentile. Pure financial risk. Not ESRS impact-material.", "blindspot_description": "Trading exposure — risk model review needed.", "correct_quadrant": 3, "severity": "low", "likelihood": "medium", "time_horizon": "short", "disclosure_required": False, "electronics_sensitive": False, "esrs_reference": "ESRS 2 §SBM-3 (Financial Risk)", "stakeholder_voice": None},
    "regulatory_capital": {"id": "regulatory_capital", "title": "Basel IV Capital Requirements Phase-In", "hover_description": "2025 output floor increases RWA by est. €2B. Financial planning issue. Not ESRS impact-material.", "blindspot_description": "Capital requirements — RWA model recalibration needed.", "correct_quadrant": 3, "severity": "low", "likelihood": "high", "time_horizon": "short", "disclosure_required": False, "electronics_sensitive": False, "esrs_reference": "Basel IV / CRR3", "stakeholder_voice": None},
    # Q4 (6)
    "office_recycling_bfs": {"id": "office_recycling_bfs", "title": "HQ Paper Recycling", "hover_description": "HQ recycles 4 tonnes/yr. Negligible at group scale.", "blindspot_description": "Office waste — minor metric.", "correct_quadrant": 4, "severity": "low", "likelihood": "high", "time_horizon": "short", "disclosure_required": False, "electronics_sensitive": False, "esrs_reference": None, "stakeholder_voice": None},
    "charity_marathon": {"id": "charity_marathon", "title": "Staff Charity Marathon", "hover_description": "Annual charity run raises £50K. Good PR. Zero ESG impact at group level.", "blindspot_description": "CSR spend — HR records.", "correct_quadrant": 4, "severity": "low", "likelihood": "high", "time_horizon": "short", "disclosure_required": False, "electronics_sensitive": False, "esrs_reference": None, "stakeholder_voice": None},
    "exec_travel_bfs": {"id": "exec_travel_bfs", "title": "Executive Travel Carbon Offsets", "hover_description": "C-suite flights generate ~80 tCO₂/yr. Symbolic vs. 2.8M tCO₂ financed emissions.", "blindspot_description": "Executive travel — HR records.", "correct_quadrant": 4, "severity": "low", "likelihood": "high", "time_horizon": "short", "disclosure_required": False, "electronics_sensitive": False, "esrs_reference": None, "stakeholder_voice": None},
    "esg_award": {"id": "esg_award", "title": "Industry ESG Award Application", "hover_description": "Submitted for 'Best ESG Bank' award. PR exercise with no material impact.", "blindspot_description": "Award submission — marketing records.", "correct_quadrant": 4, "severity": "low", "likelihood": "high", "time_horizon": "short", "disclosure_required": False, "electronics_sensitive": False, "esrs_reference": None, "stakeholder_voice": None},
    "standing_desks_bfs": {"id": "standing_desks_bfs", "title": "Standing Desks for Trading Floor", "hover_description": "Good HR practice. Financially negligible. Not CSRD-material.", "blindspot_description": "Workplace ergonomics — HR records.", "correct_quadrant": 4, "severity": "low", "likelihood": "high", "time_horizon": "short", "disclosure_required": False, "electronics_sensitive": False, "esrs_reference": None, "stakeholder_voice": None},
    "led_branches": {"id": "led_branches", "title": "LED Retrofit in Branch Network", "hover_description": "Saves ~20 tCO₂/yr. Measurable but immaterial vs. financed emissions.", "blindspot_description": "Energy data — facilities records.", "correct_quadrant": 4, "severity": "low", "likelihood": "high", "time_horizon": "short", "disclosure_required": False, "electronics_sensitive": False, "esrs_reference": None, "stakeholder_voice": None},
}
