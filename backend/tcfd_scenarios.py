"""
Muressons Global Corporation — TCFD Scenario Analysis Tool (SI-4)
Allows players to run climate scenario analysis on their portfolio
across 1.5°C, 2°C, and 4°C pathways.

Theory base:
  - TCFD (2017): Recommendations of the Task Force on Climate-related
    Financial Disclosures
  - NGFS (2022): Network for Greening the Financial System scenarios
  - IEA (2023): World Energy Outlook scenario framework
  - Carbon Tracker Initiative: Stranded asset methodology

Architecture:
  Pure-function module. Takes current BU states and simulates
  forward projections under different climate scenarios.
  No mutation of game state — purely analytical.
"""

from __future__ import annotations
from typing import Any
import math


# ═══════════════════════════════════════════════════════════════
#  SCENARIO DEFINITIONS (NGFS-aligned)
# ═══════════════════════════════════════════════════════════════

CLIMATE_SCENARIOS = {
    "orderly_1_5": {
        "name": "Net Zero 2050 (1.5°C Orderly)",
        "description": (
            "Ambitious, early action scenario. Carbon price rises steadily to "
            "$250/tCO2 by 2050. Strong regulatory push. High transition risk, "
            "low physical risk. Green technology boom."
        ),
        "ngfs_category": "Orderly",
        "carbon_price_trajectory": [50, 80, 120, 170, 250],  # $/tCO2 per decade
        "physical_risk_multiplier": 1.0,  # Baseline
        "transition_risk_multiplier": 2.5,  # High transition costs
        "stranded_asset_pct": 0.35,  # 35% of fossil-linked assets stranded
        "green_premium": -0.02,  # Green tech becomes 2% cheaper
        "regulatory_stringency": "very_high",
        "demand_shift": {
            "pharma": 1.05,     # Slight increase (climate health impacts)
            "electronics": 0.90,  # Circular economy reduces new production
            "consumer_goods": 0.85,  # Sustainable consumption reduces volume
            "software": 1.15,     # Digital solutions boom
            "hospitals": 1.10,    # Climate health burden
            "clinics": 1.08,
            "specialised_care": 1.05,
            "telehealth": 1.25,   # Digital health surge
        },
    },
    "disorderly_2": {
        "name": "Delayed Transition (2°C Disorderly)",
        "description": (
            "Late, sudden policy action after 2030. Carbon price jumps abruptly. "
            "Both transition AND physical risks are elevated. Market volatility. "
            "Stranded assets and climate damages co-occur."
        ),
        "ngfs_category": "Disorderly",
        "carbon_price_trajectory": [30, 40, 150, 300, 350],
        "physical_risk_multiplier": 1.5,
        "transition_risk_multiplier": 3.0,
        "stranded_asset_pct": 0.45,
        "green_premium": 0.0,
        "regulatory_stringency": "shock",
        "demand_shift": {
            "pharma": 1.10,
            "electronics": 0.80,
            "consumer_goods": 0.75,
            "software": 1.10,
            "hospitals": 1.15,
            "clinics": 1.10,
            "specialised_care": 1.08,
            "telehealth": 1.20,
        },
    },
    "hothouse_4": {
        "name": "Current Policies (4°C Hothouse)",
        "description": (
            "No additional policy action. Severe physical climate impacts: "
            "extreme weather, sea level rise, crop failure, mass migration. "
            "Low transition risk but catastrophic physical risk. Nature collapse."
        ),
        "ngfs_category": "Hot house world",
        "carbon_price_trajectory": [20, 25, 30, 35, 40],
        "physical_risk_multiplier": 4.0,  # Catastrophic
        "transition_risk_multiplier": 0.5,  # Low transition costs
        "stranded_asset_pct": 0.10,  # Few stranded (no transition)
        "green_premium": 0.05,  # No green incentives
        "regulatory_stringency": "minimal",
        "demand_shift": {
            "pharma": 1.30,     # Disease burden explodes
            "electronics": 0.70,  # Supply chain collapse
            "consumer_goods": 0.60,  # Agricultural collapse
            "software": 0.95,
            "hospitals": 1.40,    # Climate health emergency
            "clinics": 1.25,
            "specialised_care": 1.30,
            "telehealth": 1.15,
        },
    },
}


# ═══════════════════════════════════════════════════════════════
#  SCENARIO ANALYSIS ENGINE
# ═══════════════════════════════════════════════════════════════

def run_scenario_analysis(
    scenario_id: str,
    bus: list[dict],
    gs: dict,
    bio_state: dict | None = None,
    time_horizon_years: int = 10,
) -> dict[str, Any]:
    """
    Run a TCFD-aligned scenario analysis on the current portfolio.
    Returns projected financial impacts, risk exposure, and strategic implications.
    """
    scenario = CLIMATE_SCENARIOS.get(scenario_id)
    if not scenario:
        return {"error": f"Unknown scenario: {scenario_id}"}

    results: dict[str, Any] = {
        "scenario": scenario["name"],
        "ngfs_category": scenario["ngfs_category"],
        "description": scenario["description"],
        "time_horizon_years": time_horizon_years,
    }

    # ── 1. Revenue Impact by BU ──
    bu_projections = []
    total_current_revenue = 0
    total_projected_revenue = 0

    for bu in bus:
        bu_id = bu.get("bu_id", "unknown")
        current_rev = bu.get("revenue_base", 10_000_000)
        total_current_revenue += current_rev

        demand_mult = scenario["demand_shift"].get(bu_id, 1.0)
        # Project revenue with compounding demand shift. IMP-13 (audit
        # 2026-09-04, WP-22): the shift is a 10-YEAR multiplier — annualised
        # over 5 it was applied squared at the 10-year horizon.
        annual_shift = demand_mult ** (1 / 10)
        projected_rev = round(current_rev * (annual_shift ** time_horizon_years), 2)
        total_projected_revenue += projected_rev

        bu_projections.append({
            "bu_id": bu_id,
            "current_revenue": current_rev,
            "projected_revenue": projected_rev,
            "demand_multiplier": demand_mult,
            "revenue_change_pct": round((projected_rev / max(current_rev, 1) - 1) * 100, 1),   # IMP-13: revenue 0 guard
        })

    results["bu_projections"] = bu_projections
    results["total_revenue_change_pct"] = round(
        (total_projected_revenue / max(total_current_revenue, 1) - 1) * 100, 1
    )

    # ── 2. Carbon Cost Exposure ──
    avg_ci = sum(bu.get("carbon_intensity", 50) for bu in bus) / max(len(bus), 1)
    # IMP-02 (audit 2026-09-04, WP-22): CI is tCO2e per $1M of revenue, so
    # `avg_ci × n × 1000` assumed $1B of revenue per BU — ~69× the engine's
    # own tonnage — and the "annual carbon cost" read 85–120% of revenue. The
    # emissions are the engine's arbiter (engine.py local_tco2e: Σ CI ×
    # revenue / 1e6), and the price array is per DECADE, indexed by decade.
    total_emissions_proxy = sum(
        float(bu.get("carbon_intensity", 50) or 0) * float(bu.get("revenue_base", 0) or 0) / 1_000_000
        for bu in bus
    )
    carbon_price = scenario["carbon_price_trajectory"][min(max(int(time_horizon_years) - 1, 0) // 10, 4)]
    carbon_cost = round(total_emissions_proxy * carbon_price, 2)

    results["carbon_exposure"] = {
        "avg_carbon_intensity": round(avg_ci, 1),
        "estimated_emissions_tco2e": round(total_emissions_proxy, 0),
        "carbon_price_at_horizon": carbon_price,
        "annual_carbon_cost": carbon_cost,
        "carbon_cost_as_pct_revenue": round(
            carbon_cost / max(total_current_revenue, 1) * 100, 2
        ),
    }

    # ── 3. Physical Risk Assessment ──
    phys_mult = scenario["physical_risk_multiplier"]
    treasury = gs.get("corporate_treasury", 0)
    resilience = gs.get("active_event_flags", {}).get("active_resilience_factor", 0)

    # Annual expected physical loss (IMP-13: a negative treasury is not a negative loss)
    base_physical_loss = max(float(treasury or 0), 0.0) * 0.02  # 2% baseline
    scenario_physical_loss = round(base_physical_loss * phys_mult * (1 - resilience), 2)

    results["physical_risk"] = {
        "multiplier": phys_mult,
        "resilience_factor": resilience,
        "annual_expected_loss": scenario_physical_loss,
        "cumulative_loss_at_horizon": round(scenario_physical_loss * time_horizon_years, 2),
        "risk_level": (
            "catastrophic" if phys_mult >= 3.0
            else "severe" if phys_mult >= 2.0
            else "moderate" if phys_mult >= 1.5
            else "manageable"
        ),
    }

    # ── 4. Stranded Asset Exposure ──
    total_ppe = sum(bu.get("revenue_base", 0) * 2.5 for bu in bus)  # Proxy PPE
    stranded = round(total_ppe * scenario["stranded_asset_pct"], 2)

    results["stranded_assets"] = {
        "estimated_ppe": round(total_ppe, 2),
        "stranded_pct": scenario["stranded_asset_pct"],
        "stranded_value": stranded,
        "write_down_impact": round(stranded * 0.8, 2),  # 80% written off
    }

    # ── 5. Transition Opportunity ──
    trans_mult = scenario["transition_risk_multiplier"]
    green_premium = scenario["green_premium"]

    # Opportunity score: how well positioned is the company?
    rep = gs.get("group_reputation", 50)
    avg_slo = sum(bu.get("social_license_score", 50) for bu in bus) / max(len(bus), 1)
    # IMP-13: workforce readiness lives on the flags (engine writes it there)
    readiness = gs.get("active_event_flags", {}).get("workforce_readiness", gs.get("workforce_readiness", 50))

    opportunity_score = round(
        (rep / 100 * 0.3 + avg_slo / 100 * 0.3 + readiness / 100 * 0.2 + (100 - avg_ci) / 100 * 0.2) * 100,
        1,
    )

    results["transition_opportunity"] = {
        "opportunity_score": opportunity_score,
        "transition_risk_multiplier": trans_mult,
        "green_cost_premium": round(green_premium * 100, 1),
        "readiness_assessment": (
            "well_positioned" if opportunity_score >= 70
            else "moderate_exposure" if opportunity_score >= 45
            else "high_vulnerability"
        ),
        "strategic_implications": _get_strategic_implications(
            scenario_id, opportunity_score, avg_ci
        ),
    }

    # ── 6. Nature Risk (TNFD overlay) ──
    if bio_state:
        ehi = bio_state.get("ecosystem_health_index", 65)
        nature_dep = bio_state.get("biodiversity_dependency_score", 0.35)

        nature_risk = round(
            (100 - ehi) / 100 * nature_dep * phys_mult * 100, 1
        )
        results["nature_risk"] = {
            "ecosystem_health": ehi,
            "biodiversity_dependency": nature_dep,
            "nature_risk_score": nature_risk,
            "tnfd_recommendation": (
                "Urgent: Implement TNFD LEAP approach immediately"
                if nature_risk > 50
                else "Important: Begin TNFD-aligned disclosure"
                if nature_risk > 25
                else "Monitor: Current nature exposure is manageable"
            ),
        }

    # ── 7. Overall Risk Rating ──
    total_risk = round(
        (results["carbon_exposure"]["carbon_cost_as_pct_revenue"] * 0.3
         + results["physical_risk"]["multiplier"] * 10
         + results["stranded_assets"]["stranded_pct"] * 100 * 0.2
         + (100 - opportunity_score) * 0.1),
        1,
    )
    results["overall_risk_rating"] = {
        "score": total_risk,
        "category": (
            "critical" if total_risk > 60
            else "high" if total_risk > 40
            else "moderate" if total_risk > 20
            else "low"
        ),
    }

    return results


def _get_strategic_implications(
    scenario_id: str,
    opportunity_score: float,
    avg_ci: float,
) -> list[str]:
    """Generate scenario-specific strategic recommendations."""
    implications = []

    if scenario_id == "orderly_1_5":
        if avg_ci > 60:
            implications.append(
                "🔴 High carbon intensity is unsustainable under 1.5°C. "
                "Accelerate operational decarbonisation immediately."
            )
        if opportunity_score < 50:
            implications.append(
                "⚠️ Low transition readiness. Risk of being outcompeted by "
                "sustainability leaders in the orderly transition."
            )
        implications.append(
            "📈 Green technology investments will yield premium returns. "
            "Consider front-loading decarbonisation CapEx."
        )

    elif scenario_id == "disorderly_2":
        implications.append(
            "⚡ VOLATILITY WARNING: Disorderly transition means both physical "
            "AND transition risks are elevated. Build financial buffers."
        )
        if avg_ci > 40:
            implications.append(
                "🔴 Carbon price shock risk: sudden jump from $40 to $150/tCO2 "
                "would cause severe margin compression."
            )

    elif scenario_id == "hothouse_4":
        implications.append(
            "🌡️ CATASTROPHIC PHYSICAL RISK: Supply chain disruptions, "
            "extreme weather losses, and agricultural collapse are probable."
        )
        implications.append(
            "🏥 Healthcare demand surge creates revenue opportunity but "
            "operational challenges from climate-driven disease burden."
        )
        if opportunity_score > 60:
            implications.append(
                "💡 Despite low transition pressure, your ESG positioning "
                "could provide resilience advantages in a degrading world."
            )

    return implications


def get_scenario_comparison(
    bus: list[dict],
    gs: dict,
    bio_state: dict | None = None,
) -> dict:
    """Run all three scenarios and return a comparison matrix."""
    comparison = {}
    for scenario_id in CLIMATE_SCENARIOS:
        comparison[scenario_id] = run_scenario_analysis(
            scenario_id, bus, gs, bio_state
        )

    # Summary comparison
    summary = {
        "scenarios_analysed": list(CLIMATE_SCENARIOS.keys()),
        "revenue_impact": {
            sid: r["total_revenue_change_pct"]
            for sid, r in comparison.items()
        },
        "carbon_cost": {
            sid: r["carbon_exposure"]["annual_carbon_cost"]
            for sid, r in comparison.items()
        },
        "physical_loss": {
            sid: r["physical_risk"]["annual_expected_loss"]
            for sid, r in comparison.items()
        },
        "overall_risk": {
            sid: r["overall_risk_rating"]["score"]
            for sid, r in comparison.items()
        },
        "strategic_insight": (
            "Your portfolio shows different risk profiles across scenarios. "
            "A robust strategy should perform acceptably across ALL scenarios, "
            "not just optimise for one. This is the TCFD principle of "
            "'strategic resilience under uncertainty'."
        ),
    }

    return {"scenarios": comparison, "summary": summary}
