"""
Muressons Global Corporation — Supply Chain Network Model (SE-2)
Replaces toggle-based supply chain decisions with a 3-tier visual
network model with cascading failure mechanics.

Theory base:
  - Chopra & Sodhi (2004): Supply Chain Risk Management
  - Christopher & Peck (2004): Supply Chain Resilience
  - Simchi-Levi et al. (2015): Time-to-Survive metric
  - EU CS3D: Corporate Sustainability Due Diligence Directive

Architecture:
  Pure-function module. Maintains a directed graph of suppliers
  across 3 tiers with visibility, risk, and compliance metrics.
"""

from __future__ import annotations
from typing import Any
import random
import math


# ═══════════════════════════════════════════════════════════════
#  SUPPLY CHAIN NETWORK
# ═══════════════════════════════════════════════════════════════

def create_initial_supply_chain() -> dict[str, Any]:
    """Create the initial 3-tier supply chain network."""
    return {
        "tier_1_suppliers": [
            {
                "id": "t1_chemicals",
                "name": "ChemPure Industries",
                "category": "chemical_inputs",
                "location": "Germany",
                "risk_score": 20,       # 0-100
                "visibility": 0.95,     # 0-1 (how much we know)
                "compliance_status": "audited",
                "annual_spend": 15_000_000,
                "lead_time_days": 14,
                "alternatives": 2,
                "esg_rating": "A",
                "carbon_intensity": 35,
                "human_rights_risk": "low",
                "connected_to": ["t2_mining_eu", "t2_refining"],
            },
            {
                "id": "t1_electronics",
                "name": "TechSource Asia",
                "category": "electronic_components",
                "location": "Taiwan",
                "risk_score": 45,
                "visibility": 0.80,
                "compliance_status": "self_reported",
                "annual_spend": 22_000_000,
                "lead_time_days": 45,
                "alternatives": 1,
                "esg_rating": "B",
                "carbon_intensity": 55,
                "human_rights_risk": "medium",
                "connected_to": ["t2_semiconductors", "t2_rare_earth"],
            },
            {
                "id": "t1_packaging",
                "name": "GreenPack Solutions",
                "category": "packaging",
                "location": "Netherlands",
                "risk_score": 15,
                "visibility": 0.90,
                "compliance_status": "audited",
                "annual_spend": 8_000_000,
                "lead_time_days": 7,
                "alternatives": 4,
                "esg_rating": "A+",
                "carbon_intensity": 20,
                "human_rights_risk": "low",
                "connected_to": ["t2_forestry"],
            },
            {
                "id": "t1_logistics",
                "name": "GlobalFreight Corp",
                "category": "logistics",
                "location": "Singapore",
                "risk_score": 35,
                "visibility": 0.70,
                "compliance_status": "self_reported",
                "annual_spend": 12_000_000,
                "lead_time_days": 3,
                "alternatives": 3,
                "esg_rating": "B-",
                "carbon_intensity": 70,
                "human_rights_risk": "medium",
                "connected_to": ["t2_shipping", "t2_warehousing"],
            },
        ],
        "tier_2_suppliers": [
            {
                "id": "t2_mining_eu",
                "name": "Nordic Minerals AB",
                "category": "raw_materials",
                "location": "Sweden",
                "risk_score": 25,
                "visibility": 0.60,
                "compliance_status": "unknown",
                "carbon_intensity": 40,
                "human_rights_risk": "low",
                "connected_to": ["t3_cobalt_drc"],
            },
            {
                "id": "t2_semiconductors",
                "name": "Shenzhen Silicon Ltd",
                "category": "semiconductors",
                "location": "China",
                "risk_score": 55,
                "visibility": 0.40,
                "compliance_status": "unknown",
                "carbon_intensity": 65,
                "human_rights_risk": "medium",
                "connected_to": ["t3_cobalt_drc", "t3_lithium"],
            },
            {
                "id": "t2_rare_earth",
                "name": "Inner Mongolia RE Processing",
                "category": "rare_earth_elements",
                "location": "China",
                "risk_score": 70,
                "visibility": 0.25,
                "compliance_status": "no_data",
                "carbon_intensity": 80,
                "human_rights_risk": "high",
                "connected_to": ["t3_cobalt_drc"],
            },
            {
                "id": "t2_refining",
                "name": "Gulf Refining Co",
                "category": "chemical_refining",
                "location": "UAE",
                "risk_score": 40,
                "visibility": 0.50,
                "compliance_status": "self_reported",
                "carbon_intensity": 60,
                "human_rights_risk": "medium",
                "connected_to": [],
            },
            {
                "id": "t2_forestry",
                "name": "Amazon Basin Pulp Co",
                "category": "pulp_paper",
                "location": "Brazil",
                "risk_score": 65,
                "visibility": 0.30,
                "compliance_status": "no_data",
                "carbon_intensity": 45,
                "human_rights_risk": "high",
                "connected_to": ["t3_indigenous_land"],
            },
            {
                "id": "t2_shipping",
                "name": "Pacific Line Carriers",
                "category": "shipping",
                "location": "Marshall Islands",
                "risk_score": 50,
                "visibility": 0.35,
                "compliance_status": "unknown",
                "carbon_intensity": 75,
                "human_rights_risk": "medium",
                "connected_to": [],
            },
            {
                "id": "t2_warehousing",
                "name": "DHL Warehouse Ops",
                "category": "warehousing",
                "location": "Various",
                "risk_score": 20,
                "visibility": 0.70,
                "compliance_status": "audited",
                "carbon_intensity": 25,
                "human_rights_risk": "low",
                "connected_to": [],
            },
        ],
        "tier_3_suppliers": [
            {
                "id": "t3_cobalt_drc",
                "name": "Artisanal Cobalt Mines (DRC)",
                "category": "cobalt_mining",
                "location": "DRC",
                "risk_score": 95,
                "visibility": 0.10,
                "compliance_status": "no_data",
                "carbon_intensity": 30,
                "human_rights_risk": "critical",
                "child_labour_risk": True,
                "connected_to": [],
            },
            {
                "id": "t3_lithium",
                "name": "Atacama Lithium Extraction",
                "category": "lithium_mining",
                "location": "Chile",
                "risk_score": 60,
                "visibility": 0.15,
                "compliance_status": "no_data",
                "carbon_intensity": 35,
                "human_rights_risk": "high",
                "water_impact": "severe",
                "connected_to": [],
            },
            {
                "id": "t3_indigenous_land",
                "name": "Unregistered Land Clearance Operations",
                "category": "land_clearance",
                "location": "Brazil",
                "risk_score": 90,
                "visibility": 0.05,
                "compliance_status": "no_data",
                "carbon_intensity": 100,
                "human_rights_risk": "critical",
                "deforestation_linked": True,
                "connected_to": [],
            },
        ],
        # ── Network Metrics ──
        "overall_visibility": 0.0,    # Calculated
        "overall_risk": 0.0,          # Calculated
        "scope_3_estimate": 0.0,      # Calculated from network CI
        "due_diligence_level": 0,     # 0-4 tiers audited
        "time_to_survive_days": 30,   # Simchi-Levi metric
        "supply_chain_history": [],
        "disruption_events": [],
    }


# ═══════════════════════════════════════════════════════════════
#  VISIBILITY & AUDIT MECHANICS
# ═══════════════════════════════════════════════════════════════

def conduct_supply_chain_audit(
    sc_state: dict,
    audit_depth: int,  # 1, 2, or 3 (tiers)
    gs: dict,
) -> dict:
    """
    Conduct a supply chain audit to increase visibility.
    Deeper audits cost more but reveal hidden risks.

    CS3D: Due diligence must cover the full value chain.
    """
    cost_per_tier = {1: 500_000, 2: 1_500_000, 3: 3_000_000}
    cost = sum(cost_per_tier.get(t, 500_000) for t in range(1, audit_depth + 1))
    gs["corporate_treasury"] = round(gs["corporate_treasury"] - cost, 2)

    discoveries = []

    tier_map = {
        1: sc_state["tier_1_suppliers"],
        2: sc_state["tier_2_suppliers"],
        3: sc_state["tier_3_suppliers"],
    }

    for tier in range(1, audit_depth + 1):
        suppliers = tier_map.get(tier, [])
        for supplier in suppliers:
            old_vis = supplier["visibility"]
            # Audit increases visibility (with diminishing returns)
            new_vis = min(1.0, old_vis + (1.0 - old_vis) * 0.5)
            supplier["visibility"] = round(new_vis, 3)
            supplier["compliance_status"] = "audited" if new_vis > 0.7 else "partially_audited"

            # Discover hidden risks
            if old_vis < 0.30 and supplier.get("human_rights_risk") in ("high", "critical"):
                discoveries.append({
                    "supplier_id": supplier["id"],
                    "supplier_name": supplier["name"],
                    "risk_type": "human_rights",
                    "severity": supplier["human_rights_risk"],
                    "message": (
                        f"⚠️ AUDIT DISCOVERY at {supplier['name']} ({supplier['location']}): "
                        f"{supplier['human_rights_risk'].upper()} human rights risk identified. "
                        f"{'Child labour indicators detected.' if supplier.get('child_labour_risk') else ''}"
                        f"{'Deforestation linkage confirmed.' if supplier.get('deforestation_linked') else ''}"
                    ),
                })

    sc_state["due_diligence_level"] = max(sc_state.get("due_diligence_level", 0), audit_depth)

    return {
        "audit_depth": audit_depth,
        "cost": cost,
        "discoveries": discoveries,
        "discovery_count": len(discoveries),
        "message": (
            f"📋 Supply chain audit (Tier 1-{audit_depth}) completed. "
            f"Cost: ${cost:,.0f}. {len(discoveries)} risk(s) discovered."
            + (
                "\n\n🔴 CRITICAL FINDINGS REQUIRE IMMEDIATE ACTION"
                if any(d["severity"] == "critical" for d in discoveries)
                else ""
            )
        ),
    }


# ═══════════════════════════════════════════════════════════════
#  CASCADING FAILURE
# ═══════════════════════════════════════════════════════════════

def simulate_disruption(
    sc_state: dict,
    disruption_source: str,
    severity: float,  # 0-1
) -> dict:
    """
    Simulate a supply chain disruption that cascades through tiers.
    Christopher & Peck (2004): Disruptions propagate upstream.
    """
    affected = []
    all_suppliers = (
        sc_state["tier_1_suppliers"]
        + sc_state["tier_2_suppliers"]
        + sc_state["tier_3_suppliers"]
    )

    # Find directly affected supplier
    source = next((s for s in all_suppliers if s["id"] == disruption_source), None)
    if not source:
        return {"error": f"Supplier {disruption_source} not found"}

    affected.append({
        "supplier": source["id"],
        "name": source["name"],
        "impact": "direct",
        "severity": severity,
    })

    # Cascade: find suppliers connected to the disrupted one
    for supplier in all_suppliers:
        if disruption_source in supplier.get("connected_to", []):
            cascade_severity = severity * 0.6  # Attenuated
            alternatives = supplier.get("alternatives", 0)
            if alternatives > 2:
                cascade_severity *= 0.3  # Well-diversified
            elif alternatives > 0:
                cascade_severity *= 0.6  # Some alternatives
            # else: full cascade

            affected.append({
                "supplier": supplier["id"],
                "name": supplier["name"],
                "impact": "cascade",
                "severity": round(cascade_severity, 3),
                "alternatives_available": alternatives,
            })

    # Calculate total impact
    total_spend_affected = sum(
        next((s.get("annual_spend", 0) for s in all_suppliers if s["id"] == a["supplier"]), 0)
        for a in affected
    )

    # Time-to-survive calculation (Simchi-Levi)
    max_lead_time = max(
        (next((s.get("lead_time_days", 30) for s in all_suppliers if s["id"] == a["supplier"]), 30)
         for a in affected),
        default=30,
    )
    sc_state["time_to_survive_days"] = max_lead_time

    return {
        "disruption_source": disruption_source,
        "severity": severity,
        "affected_suppliers": affected,
        "total_affected_count": len(affected),
        "total_spend_at_risk": total_spend_affected,
        "time_to_survive_days": max_lead_time,
        "message": (
            f"🚨 SUPPLY CHAIN DISRUPTION at {source['name']} ({source['location']}). "
            f"Severity: {severity:.0%}. {len(affected)} suppliers affected through cascade. "
            f"${total_spend_affected:,.0f} annual spend at risk. "
            f"Time-to-survive: {max_lead_time} days."
        ),
    }


# ═══════════════════════════════════════════════════════════════
#  SCOPE 3 ESTIMATION (QW-3)
# ═══════════════════════════════════════════════════════════════

def estimate_scope3_emissions(sc_state: dict) -> dict:
    """
    Estimate Scope 3 emissions from the supply chain network.
    QW-3: Provides Scope 1/2/3 disaggregation.
    """
    scope_1 = 0  # Direct emissions (company operations)
    scope_2 = 0  # Purchased energy
    scope_3_upstream = 0  # Supply chain

    for tier_key in ["tier_1_suppliers", "tier_2_suppliers", "tier_3_suppliers"]:
        suppliers = sc_state.get(tier_key, [])
        for supplier in suppliers:
            ci = supplier.get("carbon_intensity", 50)
            visibility = supplier.get("visibility", 0.5)
            # Better visibility = better estimation
            estimated_emissions = ci * 100 * visibility
            scope_3_upstream += estimated_emissions

    sc_state["scope_3_estimate"] = round(scope_3_upstream, 2)

    return {
        "scope_1_direct": 0,  # Set from BU carbon_intensity
        "scope_2_energy": 0,  # Set from energy pillar choices
        "scope_3_upstream": round(scope_3_upstream, 2),
        "scope_3_confidence": round(
            sum(s.get("visibility", 0) for tier in [
                sc_state.get("tier_1_suppliers", []),
                sc_state.get("tier_2_suppliers", []),
                sc_state.get("tier_3_suppliers", []),
            ] for s in tier) /
            max(1, sum(len(sc_state.get(k, [])) for k in [
                "tier_1_suppliers", "tier_2_suppliers", "tier_3_suppliers"
            ])),
            3,
        ),
        "message": (
            f"📊 Scope 3 emissions estimate: {scope_3_upstream:,.0f} tCO2e "
            f"(upstream supply chain). Note: Scope 3 estimates improve with "
            f"deeper supply chain audits and visibility."
        ),
    }


def process_supply_chain_tick(
    sc_state: dict,
    gs: dict,
    bus: list[dict],
    events: dict,
    round_number: int,
) -> tuple[dict, dict]:
    """Process supply chain network for this round."""
    diagnostics: dict[str, Any] = {}

    # Calculate overall metrics
    all_suppliers = (
        sc_state.get("tier_1_suppliers", [])
        + sc_state.get("tier_2_suppliers", [])
        + sc_state.get("tier_3_suppliers", [])
    )
    if all_suppliers:
        sc_state["overall_visibility"] = round(
            sum(s["visibility"] for s in all_suppliers) / len(all_suppliers), 3
        )
        sc_state["overall_risk"] = round(
            sum(s["risk_score"] for s in all_suppliers) / len(all_suppliers), 1
        )

    # Scope 3 estimation
    scope3_diag = estimate_scope3_emissions(sc_state)
    diagnostics["scope3"] = scope3_diag

    # Stochastic disruption risk (increases with low visibility)
    if sc_state["overall_visibility"] < 0.40:
        disruption_prob = 0.15 + (0.40 - sc_state["overall_visibility"]) * 0.5
        if random.random() < disruption_prob:
            # Select a random high-risk supplier for disruption
            risky = [s for s in all_suppliers if s["risk_score"] > 60]
            if risky:
                target = random.choice(risky)
                disrupt_result = simulate_disruption(sc_state, target["id"], random.uniform(0.3, 0.8))
                diagnostics["disruption_event"] = disrupt_result
                sc_state["disruption_events"].append({
                    "round": round_number,
                    **disrupt_result,
                })

    sc_state["supply_chain_history"].append({
        "round": round_number,
        "visibility": sc_state["overall_visibility"],
        "risk": sc_state["overall_risk"],
        "scope3": sc_state["scope_3_estimate"],
    })

    return sc_state, diagnostics
