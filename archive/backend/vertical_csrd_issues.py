"""
Muressons — Vertical-Specific CSRD Issue Banks
20 CSRD materiality issues per vertical, same quadrant distribution as default:
  Q1 (High Fin/High Impact): 6 issues
  Q2 (Low Fin/High Impact):  4 issues  
  Q3 (High Fin/Low Impact):  4 issues
  Q4 (Low Fin/Low Impact):   6 issues
"""
from __future__ import annotations

# ═══════════════════════════════════════════════════════════════
#  TECHNOLOGY VERTICAL — 20 CSRD Issues
# ═══════════════════════════════════════════════════════════════

TECHNOLOGY_CSRD_ISSUES: dict = {
    # ── Q1: Doubly Material ──────────────────────────────────
    "data_centre_energy": {
        "id": "data_centre_energy", "title": "Data Centre Energy Consumption",
        "hover_description": (
            "Your AI training clusters consume 180GWh/yr — equivalent to a small city. "
            "EU Energy Efficiency Directive (EED) mandates PUE reporting by 2025. "
            "Severity: HIGH. Time horizon: SHORT. ESRS E1 mandatory."
        ),
        "blindspot_description": "Energy consumption data — data centre audit not completed.",
        "correct_quadrant": 1, "severity": "high", "likelihood": "high", "time_horizon": "short",
        "disclosure_required": True, "electronics_sensitive": False,
        "esrs_reference": "ESRS E1 (Climate Change) / EU EED",
        "stakeholder_voice": None,
    },
    "ai_training_bias": {
        "id": "ai_training_bias", "title": "AI Model Training Data Bias",
        "hover_description": (
            "Foundation models trained on web-scraped data contain documented biases "
            "against minority groups. EU AI Act (High-Risk Systems) triggers fines "
            "up to €35M or 7% global revenue. Severity: HIGH. ESRS S1 / AI Act mandatory."
        ),
        "blindspot_description": "AI bias assessment — model audit data insufficient.",
        "correct_quadrant": 1, "severity": "high", "likelihood": "medium", "time_horizon": "short",
        "disclosure_required": True, "electronics_sensitive": False,
        "esrs_reference": "ESRS S1 (Own Workforce) / EU AI Act Art. 9",
        "stakeholder_voice": "employees",
    },
    "scope3_cloud": {
        "id": "scope3_cloud", "title": "Scope 3 Cloud Supply Chain Emissions",
        "hover_description": (
            "Upstream hardware manufacturing and downstream customer compute generate "
            "5× more CO₂ than direct operations. SBTi pathway requires 4.2%/yr reduction. "
            "ESRS E1 mandatory."
        ),
        "blindspot_description": "Upstream emission profile — hardware vendor data unavailable.",
        "correct_quadrant": 1, "severity": "high", "likelihood": "high", "time_horizon": "long",
        "disclosure_required": True, "electronics_sensitive": False,
        "esrs_reference": "ESRS E1 (Climate Change) / GHG Protocol Scope 3",
        "stakeholder_voice": None,
    },
    "content_moderation_labour": {
        "id": "content_moderation_labour", "title": "Content Moderation Worker Exploitation",
        "hover_description": (
            "Outsourced content moderators in the Philippines work 14-hour shifts "
            "reviewing traumatic content without adequate mental health support. "
            "EU CSDDD creates civil liability. Severity: HIGH. ESRS S2 mandatory."
        ),
        "blindspot_description": "Supply chain labour conditions — outsourced audit not completed.",
        "correct_quadrant": 1, "severity": "high", "likelihood": "medium", "time_horizon": "short",
        "disclosure_required": True, "electronics_sensitive": True,
        "esrs_reference": "ESRS S2 (Workers in Value Chain) / EU CSDDD",
        "stakeholder_voice": "suppliers",
    },
    "e_waste_hardware": {
        "id": "e_waste_hardware", "title": "Server & Hardware E-Waste",
        "hover_description": (
            "Data centre refresh cycles generate 2,400 tonnes/yr of decommissioned servers. "
            "Lead, lithium, and rare earth metals leaching risk. EU WEEE Phase III "
            "enforcement begins 2026. Severity: HIGH. ESRS E2 mandatory."
        ),
        "blindspot_description": "Hardware lifecycle data — decommission audit incomplete.",
        "correct_quadrant": 1, "severity": "high", "likelihood": "high", "time_horizon": "short",
        "disclosure_required": True, "electronics_sensitive": True,
        "esrs_reference": "ESRS E2 (Pollution) / WEEE Directive Phase III",
        "stakeholder_voice": None,
    },
    "water_cooling": {
        "id": "water_cooling", "title": "Data Centre Water Cooling Consumption",
        "hover_description": (
            "Evaporative cooling systems consume 12M litres/yr from a stressed aquifer. "
            "Local communities depend on the same source. Severity: HIGH. "
            "ESRS E3 disclosure mandatory."
        ),
        "blindspot_description": "Water consumption data — cooling infrastructure audit pending.",
        "correct_quadrant": 1, "severity": "medium", "likelihood": "high", "time_horizon": "short",
        "disclosure_required": True, "electronics_sensitive": False,
        "esrs_reference": "ESRS E3 (Water & Marine Resources)",
        "stakeholder_voice": "local_communities",
    },

    # ── Q2: Disclosure-Only ──────────────────────────────────
    "developer_wellbeing": {
        "id": "developer_wellbeing", "title": "Developer Mental Health & Wellbeing",
        "hover_description": (
            "Burnout rates at 2× industry average. Financially immaterial (<0.1% revenue) "
            "but ESRS S1 §65 requires disclosure. Disclosure cost: $150K."
        ),
        "blindspot_description": "Employee wellbeing data — pulse survey not conducted.",
        "correct_quadrant": 2, "severity": "medium", "likelihood": "high", "time_horizon": "medium",
        "disclosure_required": True, "electronics_sensitive": False,
        "esrs_reference": "ESRS S1 §65 (Workforce Wellbeing)",
        "disclosure_investment_usd": 150_000, "stakeholder_voice": "employees",
    },
    "digital_inclusion": {
        "id": "digital_inclusion", "title": "Digital Inclusion & Accessibility",
        "hover_description": (
            "Platform accessibility compliance below WCAG 2.1 AA standard. "
            "Impacts 15% of users with disabilities. ESRS S4 mandatory disclosure. "
            "Disclosure cost: $100K."
        ),
        "blindspot_description": "Accessibility audit — user impact data insufficient.",
        "correct_quadrant": 2, "severity": "medium", "likelihood": "medium", "time_horizon": "medium",
        "disclosure_required": True, "electronics_sensitive": False,
        "esrs_reference": "ESRS S4 (Consumers & End-Users)",
        "disclosure_investment_usd": 100_000, "stakeholder_voice": None,
    },
    "open_source_contributions": {
        "id": "open_source_contributions", "title": "Open-Source Community Contributions",
        "hover_description": (
            "Releasing AI tools to NGOs creates genuine positive impact. "
            "Financially immaterial but generates social license. ESRS G1 §37 "
            "requires disclosure. Disclosure cost: $60K."
        ),
        "blindspot_description": "Open-source impact metrics — measurement framework missing.",
        "correct_quadrant": 2, "severity": "medium", "likelihood": "medium", "time_horizon": "medium",
        "disclosure_required": True, "electronics_sensitive": False,
        "esrs_reference": "ESRS G1 (Business Conduct) §37",
        "disclosure_investment_usd": 60_000, "stakeholder_voice": None,
    },
    "gig_worker_wages": {
        "id": "gig_worker_wages", "title": "Platform Worker Living Wage Gap",
        "hover_description": (
            "Gap between minimum wage and living wage at outsourced moderation sites "
            "affects ~3,000 workers. ESRS S2 mandatory disclosure. "
            "Disclosure cost: $200K."
        ),
        "blindspot_description": "Wage data — outsourced workforce audit incomplete.",
        "correct_quadrant": 2, "severity": "high", "likelihood": "high", "time_horizon": "short",
        "disclosure_required": True, "electronics_sensitive": True,
        "esrs_reference": "ESRS S2 (Workers in Value Chain) — wage adequacy",
        "disclosure_investment_usd": 200_000, "stakeholder_voice": "suppliers",
    },

    # ── Q3: High Fin / Low Impact ────────────────────────────
    "gpu_prices": {
        "id": "gpu_prices", "title": "GPU & Compute Price Volatility",
        "hover_description": (
            "Spot prices for H100 GPUs have swung ±40% in 12 months. High financial risk. "
            "Not a CSRD impact issue — no environmental or social harm from price fluctuation."
        ),
        "blindspot_description": "GPU supply exposure — procurement audit data missing.",
        "correct_quadrant": 3, "severity": "low", "likelihood": "high", "time_horizon": "short",
        "disclosure_required": False, "electronics_sensitive": True,
        "esrs_reference": "ESRS 2 §SBM-3 (Material Risks)", "stakeholder_voice": None,
    },
    "cloud_competitor": {
        "id": "cloud_competitor", "title": "Hyperscaler Market Share Erosion",
        "hover_description": (
            "Three AI-native competitors have taken 15% market share in 18 months. "
            "Purely competitive dynamics. Not an ESRS impact materiality issue."
        ),
        "blindspot_description": "Market share data — competitive intelligence not in audit.",
        "correct_quadrant": 3, "severity": "low", "likelihood": "medium", "time_horizon": "medium",
        "disclosure_required": False, "electronics_sensitive": False,
        "esrs_reference": "ESRS 2 §SBM-3 (Competitive Risk)", "stakeholder_voice": None,
    },
    "currency_tech": {
        "id": "currency_tech", "title": "USD/EUR Exchange Rate Exposure",
        "hover_description": (
            "80% foreign revenue creates ±8% revenue swing on FX movements. "
            "Pure financial risk. Not ESRS impact-material."
        ),
        "blindspot_description": "FX exposure — treasury data review needed.",
        "correct_quadrant": 3, "severity": "low", "likelihood": "medium", "time_horizon": "short",
        "disclosure_required": False, "electronics_sensitive": False,
        "esrs_reference": "ESRS 2 §SBM-3 (Financial Risk)", "stakeholder_voice": None,
    },
    "digital_tax": {
        "id": "digital_tax", "title": "Digital Services Tax Exposure",
        "hover_description": (
            "EU Digital Markets Act and Pillar Two (15% minimum) affect Muressons' "
            "Irish holding structure. Est. €5M additional tax liability. "
            "No environmental/social harm."
        ),
        "blindspot_description": "Tax structure exposure — group finance review required.",
        "correct_quadrant": 3, "severity": "low", "likelihood": "high", "time_horizon": "short",
        "disclosure_required": False, "electronics_sensitive": False,
        "esrs_reference": "ESRS G1 §37 (Tax Transparency)", "stakeholder_voice": None,
    },

    # ── Q4: Low Fin / Low Impact ─────────────────────────────
    "campus_recycling": {
        "id": "campus_recycling", "title": "Office Paper Recycling at HQ",
        "hover_description": "HQ recycles 3 tonnes of paper/yr. Negligible at group scale.",
        "blindspot_description": "Office waste data — minor operational metric.",
        "correct_quadrant": 4, "severity": "low", "likelihood": "high", "time_horizon": "short",
        "disclosure_required": False, "electronics_sensitive": False,
        "esrs_reference": None, "stakeholder_voice": None,
    },
    "plastic_bottles": {
        "id": "plastic_bottles", "title": "Replacing Plastic Bottles in Campus",
        "hover_description": "Estimated 8,000 single-use bottles eliminated/yr. Classic greenwashing distractor.",
        "blindspot_description": "Campus waste — minor operational metric.",
        "correct_quadrant": 4, "severity": "low", "likelihood": "high", "time_horizon": "short",
        "disclosure_required": False, "electronics_sensitive": False,
        "esrs_reference": None, "stakeholder_voice": None,
    },
    "exec_travel_tech": {
        "id": "exec_travel_tech", "title": "Executive Travel Carbon Offsets",
        "hover_description": "C-suite flights generate ~60 tCO₂/yr — <0.01% of total emissions. Symbolic.",
        "blindspot_description": "Executive travel data — HR records required.",
        "correct_quadrant": 4, "severity": "low", "likelihood": "high", "time_horizon": "short",
        "disclosure_required": False, "electronics_sensitive": False,
        "esrs_reference": None, "stakeholder_voice": None,
    },
    "hackathon_campaign": {
        "id": "hackathon_campaign", "title": "Annual AI-for-Good Hackathon PR",
        "hover_description": "PR campaign generates goodwill but zero measurable ESG improvement. Greenwashing risk.",
        "blindspot_description": "PR spend data — marketing records needed.",
        "correct_quadrant": 4, "severity": "low", "likelihood": "high", "time_horizon": "short",
        "disclosure_required": False, "electronics_sensitive": False,
        "esrs_reference": "EU Green Claims Directive (greenwashing risk)", "stakeholder_voice": None,
    },
    "standing_desks": {
        "id": "standing_desks", "title": "Standing Desks for Engineers",
        "hover_description": "Good HR practice. Financially negligible. Not CSRD-material at group level.",
        "blindspot_description": "Workplace ergonomics — HR records needed.",
        "correct_quadrant": 4, "severity": "low", "likelihood": "high", "time_horizon": "short",
        "disclosure_required": False, "electronics_sensitive": False,
        "esrs_reference": None, "stakeholder_voice": None,
    },
    "led_campus": {
        "id": "led_campus", "title": "LED Retrofit in Admin Buildings",
        "hover_description": "Saves ~6 tCO₂/yr. Measurable but immaterial vs. data centre energy footprint.",
        "blindspot_description": "Energy consumption — facilities data needed.",
        "correct_quadrant": 4, "severity": "low", "likelihood": "high", "time_horizon": "short",
        "disclosure_required": False, "electronics_sensitive": False,
        "esrs_reference": None, "stakeholder_voice": None,
    },
}


# ═══════════════════════════════════════════════════════════════
#  REGISTRY
# ═══════════════════════════════════════════════════════════════

from verticals import (
    OIL_GAS_CSRD_ISSUES,
    BANKING_FS_CSRD_ISSUES,
    RETAIL_FMCG_CSRD_ISSUES,
    AGRICULTURE_CSRD_ISSUES,
)

VERTICAL_CSRD_ISSUES = {
    "technology": TECHNOLOGY_CSRD_ISSUES,
    "oil_gas": OIL_GAS_CSRD_ISSUES,
    "banking_financial_services": BANKING_FS_CSRD_ISSUES,
    "retail_fmcg": RETAIL_FMCG_CSRD_ISSUES,
    "agriculture": AGRICULTURE_CSRD_ISSUES,
}


def get_csrd_issues_for_vertical(vertical_id: str) -> dict | None:
    """Return the CSRD issue bank for a vertical, or None if not yet authored."""
    return VERTICAL_CSRD_ISSUES.get(vertical_id)
