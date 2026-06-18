"""
Muressons Simulation — Regional ESG Reporting Service

Generates framework-aligned ESG report summaries based on the session's
geographic region. Each region maps to its primary reporting framework:
  - South Asia:    BRSR (Business Responsibility & Sustainability Report)
  - Europe:        ESRS / CSRD (Corporate Sustainability Reporting Directive)
  - North America: SEC Climate Rules + TCFD
  - ASEAN:         ASEAN Taxonomy for Sustainable Finance
  - Africa:        GRI Standards + King IV Integrated Reporting
"""

from __future__ import annotations
from typing import Any


# ═════════════════════════════════════════════════════════════════
#  FRAMEWORK DEFINITIONS
# ═════════════════════════════════════════════════════════════════

REGION_FRAMEWORKS = {
    "south_asia": {
        "name": "BRSR (Business Responsibility & Sustainability Report)",
        "short": "BRSR",
        "authority": "SEBI (Securities and Exchange Board of India)",
        "icon": "🇮🇳",
        "principles": [
            "P1: Business should conduct with ethics, transparency and accountability",
            "P2: Business should provide sustainable goods and services",
            "P3: Business should respect and promote employee wellbeing",
            "P4: Business should respect stakeholder interests",
            "P5: Business should respect and promote human rights",
            "P6: Business should respect and make efforts to protect the environment",
            "P7: Business should engage with public and regulatory policy responsibly",
            "P8: Business should promote inclusive growth and equitable development",
            "P9: Business should engage with consumers responsibly",
        ],
        "key_metrics": [
            "GHG emissions (Scope 1, 2, 3 in tCO2e)",
            "Water consumption and recycling rates",
            "Waste generation and disposal",
            "Employee health, safety, and wellbeing",
            "CSR spend and beneficiary count",
            "Board diversity and governance practices",
        ],
        "thresholds": {
            "mandatory_disclosure": "Top 1000 listed companies by market cap",
            "brsr_core": "Assurance required for top 150 from FY 2023-24",
        },
    },

    "europe": {
        "name": "ESRS / CSRD (European Sustainability Reporting Standards)",
        "short": "CSRD / ESRS",
        "authority": "European Financial Reporting Advisory Group (EFRAG)",
        "icon": "🇪🇺",
        "standards": [
            "ESRS E1: Climate Change",
            "ESRS E2: Pollution",
            "ESRS E3: Water and Marine Resources",
            "ESRS E4: Biodiversity and Ecosystems",
            "ESRS E5: Resource Use and Circular Economy",
            "ESRS S1: Own Workforce",
            "ESRS S2: Workers in the Value Chain",
            "ESRS S3: Affected Communities",
            "ESRS S4: Consumers and End-users",
            "ESRS G1: Business Conduct",
        ],
        "key_metrics": [
            "Scope 1, 2, 3 GHG emissions and reduction targets",
            "CBAM-relevant carbon intensity data",
            "Taxonomy-eligible and aligned revenue share",
            "Gender pay gap and DEI metrics",
            "Supply chain due diligence (CSDDD compliance)",
            "Circular economy packaging metrics",
        ],
        "thresholds": {
            "phase_1": "Large PIEs > 500 employees from FY 2024",
            "phase_2": "All large companies from FY 2025",
            "phase_3": "Listed SMEs from FY 2026",
        },
    },

    "north_america": {
        "name": "SEC Climate Disclosure Rules + TCFD",
        "short": "SEC / TCFD",
        "authority": "U.S. Securities and Exchange Commission",
        "icon": "🇺🇸",
        "pillars": [
            "Governance: Board oversight of climate-related risks",
            "Strategy: Climate risk impacts on business model",
            "Risk Management: Identifying and managing climate risks",
            "Metrics & Targets: GHG targets and progress tracking",
        ],
        "key_metrics": [
            "Scope 1 and 2 GHG emissions (mandatory for large accelerated filers)",
            "Scope 3 if material or part of target-setting",
            "Physical and transition climate risk assessment",
            "Climate-related financial impacts on financial statements",
            "SBTi alignment and net-zero commitments",
        ],
        "thresholds": {
            "large_accelerated_filers": "Scope 1+2 from FY 2026; Scope 3 if material",
            "accelerated_filers": "Scope 1+2 from FY 2027",
        },
    },

    "asean": {
        "name": "ASEAN Taxonomy for Sustainable Finance",
        "short": "ASEAN Taxonomy",
        "authority": "ASEAN Taxonomy Board",
        "icon": "🌏",
        "traffic_light_system": [
            "GREEN: Economic activities substantially contributing to environmental objectives",
            "AMBER: Transition activities moving toward green threshold",
            "RED: Activities not meeting minimum sustainability safeguards",
        ],
        "key_criteria": [
            "Do No Significant Harm (DNSH) to 4 environmental objectives",
            "Climate change mitigation contribution",
            "Minimum Social Safeguards (ILO Core Labour Standards)",
            "Biodiversity safeguards",
        ],
        "key_metrics": [
            "Revenue % from taxonomy-eligible activities",
            "CapEx aligned with green taxonomy",
            "Carbon intensity per sector benchmark",
            "Deforestation-free supply chain certification",
        ],
        "thresholds": {
            "voluntary": "Phase 1 (voluntary adoption 2023-2025)",
            "mandatory": "Phase 2 (mandatory from 2025 in member states)",
        },
    },

    "africa": {
        "name": "GRI Standards + King IV Integrated Reporting",
        "short": "GRI / King IV",
        "authority": "Global Reporting Initiative + King Committee on Corporate Governance",
        "icon": "🌍",
        "gri_topics": [
            "GRI 201: Economic Performance",
            "GRI 302: Energy",
            "GRI 303: Water and Effluents",
            "GRI 305: Emissions",
            "GRI 401: Employment",
            "GRI 403: Occupational Health and Safety",
            "GRI 413: Local Communities",
        ],
        "king_iv_principles": [
            "Ethical and effective leadership",
            "Governance of strategy and performance",
            "Responsible corporate citizenship",
            "Stakeholder relationships",
            "Integrated thinking and integrated report",
        ],
        "key_metrics": [
            "Community development spend vs. revenue %",
            "Local employment and procurement ratios",
            "Environmental restoration and remediation",
            "Board independence and diversity",
            "FPIC compliance for extraction operations",
        ],
    },
}


# ═════════════════════════════════════════════════════════════════
#  REPORT GENERATOR
# ═════════════════════════════════════════════════════════════════

def generate_regional_report(session_meta: dict, final_state: dict) -> dict:
    """
    Generate a framework-aligned ESG report shell based on region_id.

    Parameters:
        session_meta: Session metadata dict (contains region_id, assigned_bu, etc.)
        final_state:  The final game state dict (global_state + bu_states)

    Returns:
        A structured report dict with framework details + populated metrics.
    """
    region_id = session_meta.get("region_id", "global")
    bu_id = session_meta.get("assigned_bu") or session_meta.get("industry_vertical", "")

    framework = REGION_FRAMEWORKS.get(region_id)
    if framework is None:
        # Fallback to GRI for unknown/global regions
        framework = REGION_FRAMEWORKS["africa"]
        region_id = "global"

    gs = final_state.get("global_state", {})
    bus = final_state.get("bu_states", [])

    # Compute aggregate metrics
    n = max(len(bus), 1)
    avg_carbon = round(sum(bu.get("carbon_intensity", 50) for bu in bus) / n, 1)
    avg_slo = round(sum(bu.get("social_license_score", 50) for bu in bus) / n, 1)
    avg_gov_risk = round(sum(bu.get("governance_risk_score", 30) for bu in bus) / n, 1)
    total_tco2e = round(sum(bu.get("total_tco2e", 0) for bu in bus), 0)

    reputation = gs.get("group_reputation", 50)
    treasury = gs.get("corporate_treasury", 0)
    active_flags = gs.get("active_event_flags", {})

    # Compliance traffic lights
    def traffic_light(value: float, good_below: float | None = None, good_above: float | None = None) -> str:
        if good_below is not None:
            if value <= good_below * 0.8: return "GREEN"
            if value <= good_below: return "AMBER"
            return "RED"
        if good_above is not None:
            if value >= good_above * 1.2: return "GREEN"
            if value >= good_above: return "AMBER"
            return "RED"
        return "AMBER"

    populated_metrics = {
        "carbon_intensity": {
            "value": avg_carbon,
            "unit": "tCO2e per unit revenue",
            "traffic_light": traffic_light(avg_carbon, good_below=50),
            "benchmark": 50,
        },
        "total_scope_1_2_tco2e": {
            "value": total_tco2e,
            "unit": "tCO2e",
            "traffic_light": traffic_light(total_tco2e, good_below=100000),
        },
        "social_license_score": {
            "value": avg_slo,
            "unit": "score /100",
            "traffic_light": traffic_light(avg_slo, good_above=60),
            "benchmark": 60,
        },
        "governance_risk_score": {
            "value": avg_gov_risk,
            "unit": "score /100 (lower is better)",
            "traffic_light": traffic_light(avg_gov_risk, good_below=35),
            "benchmark": 35,
        },
        "group_reputation": {
            "value": reputation,
            "unit": "score /100",
            "traffic_light": traffic_light(reputation, good_above=65),
        },
        "sbti_committed": {
            "value": active_flags.get("sbti_committed", False),
            "unit": "boolean",
            "traffic_light": "GREEN" if active_flags.get("sbti_committed") else "RED",
        },
        "greenwashing_detected": {
            "value": active_flags.get("greenwashing_detected", False),
            "unit": "boolean",
            "traffic_light": "RED" if active_flags.get("greenwashing_detected") else "GREEN",
        },
    }

    overall_score = round(
        (1 - avg_carbon / 100) * 30 +
        (avg_slo / 100) * 30 +
        (1 - avg_gov_risk / 100) * 20 +
        (reputation / 100) * 20,
        1
    )

    return {
        "session_id": session_meta.get("session_id", ""),
        "bu_id": bu_id,
        "region_id": region_id,
        "framework": framework,
        "populated_metrics": populated_metrics,
        "overall_esg_score": overall_score,
        "overall_traffic_light": (
            "GREEN" if overall_score >= 70
            else "AMBER" if overall_score >= 50
            else "RED"
        ),
        "report_title": f"{framework['short']} Sustainability Report",
        "generated_at": None,  # caller should inject datetime
    }


def get_framework_for_region(region_id: str) -> dict:
    """Return the framework definition for a given region."""
    return REGION_FRAMEWORKS.get(region_id, REGION_FRAMEWORKS["africa"])


def list_available_frameworks() -> list[dict]:
    """Return summary of all available reporting frameworks."""
    return [
        {
            "region_id": rid,
            "framework_name": fw["name"],
            "short": fw["short"],
            "icon": fw["icon"],
            "authority": fw["authority"],
        }
        for rid, fw in REGION_FRAMEWORKS.items()
    ]
