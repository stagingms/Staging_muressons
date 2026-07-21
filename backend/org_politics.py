"""
Muressons Global Corporation — Organisational Politics Layer (SI-5)
Models internal stakeholder dynamics between C-suite executives,
each with competing agendas, coalition preferences, and influence.

Theory base:
  - Pfeffer (1992): Managing with Power
  - Mintzberg (1983): Power In and Around Organizations
  - Cyert & March (1963): Behavioral Theory of the Firm
  - Tushman & O'Reilly (1996): Ambidextrous organizations

Architecture:
  Pure-function module. Tracks internal stakeholder state as
  global_state["org_politics"]. Each C-suite member has an
  alignment score, satisfaction, and influence budget.

Game Mechanic:
  Players must build coalitions to pass strategic initiatives.
  Each decision requires support from at least 3 of 5 C-suite members.
  Unsupported decisions incur implementation penalties.
"""

from __future__ import annotations
from typing import Any
import random


# ═══════════════════════════════════════════════════════════════
#  C-SUITE CHARACTERS
# ═══════════════════════════════════════════════════════════════

CSUITE_MEMBERS = [
    {
        "id": "cfo",
        "name": "Priya Krishnamurthy",
        "title": "Chief Financial Officer",
        "icon": "💰",
        "priorities": ["cost_reduction", "treasury_growth", "debt_management"],
        "resistance_topics": ["high_cost_esg", "unproven_technology", "community_spending"],
        "support_topics": ["revenue_growth", "risk_reduction", "green_bonds"],
        "base_satisfaction": 60.0,
        "influence_weight": 1.2,  # CFO has slightly more influence on financial decisions
        "personality": "analytical",
        "quote_supportive": "The numbers support this initiative. Proceed.",
        "quote_resistant": "I need to see the ROI before I can endorse this spend.",
    },
    {
        "id": "coo",
        "name": "Hans Weber",
        "title": "Chief Operating Officer",
        "icon": "⚙️",
        "priorities": ["operational_efficiency", "supply_chain", "production"],
        "resistance_topics": ["operational_disruption", "radical_restructuring"],
        "support_topics": ["efficiency_gains", "process_improvement", "automation"],
        "base_satisfaction": 55.0,
        "influence_weight": 1.0,
        "personality": "pragmatic",
        "quote_supportive": "We can make this work operationally. Let's plan the rollout.",
        "quote_resistant": "This will disrupt production lines for at least two periods.",
    },
    {
        "id": "chro",
        "name": "Anna Kowalski",
        "title": "Chief Human Resources Officer",
        "icon": "👥",
        "priorities": ["workforce_welfare", "talent_retention", "just_transition"],
        "resistance_topics": ["layoffs", "automation_without_retraining", "burnout_risk"],
        "support_topics": ["training", "dei", "worker_safety", "retention"],
        "base_satisfaction": 50.0,
        "influence_weight": 0.9,
        "personality": "empathetic",
        "quote_supportive": "Our people will rally behind this. It's the right thing to do.",
        "quote_resistant": "We're asking too much of our workforce without adequate support.",
    },
    {
        "id": "cso",
        "name": "Dr. Amara Osei",
        "title": "Chief Sustainability Officer",
        "icon": "🌍",
        "priorities": ["emissions_reduction", "biodiversity", "stakeholder_trust"],
        "resistance_topics": ["greenwashing", "carbon_offsets_only", "compliance_minimum"],
        "support_topics": ["science_based_targets", "nature_positive", "transparency"],
        "base_satisfaction": 45.0,  # Often frustrated with pace of change
        "influence_weight": 0.8,  # CSO often has less institutional power
        "personality": "principled",
        "quote_supportive": "This aligns with our science-based pathway. Strong signal to stakeholders.",
        "quote_resistant": "This is greenwashing. We need structural change, not cosmetic measures.",
    },
    {
        "id": "cto",
        "name": "Kenji Tanaka",
        "title": "Chief Technology Officer",
        "icon": "🔬",
        "priorities": ["innovation", "digital_transformation", "ai_governance"],
        "resistance_topics": ["legacy_systems", "anti_innovation"],
        "support_topics": ["technology_investment", "ai_deployment", "data_analytics"],
        "base_satisfaction": 55.0,
        "influence_weight": 0.9,
        "personality": "visionary",
        "quote_supportive": "The technology is ready. This is a leap forward for the company.",
        "quote_resistant": "We're not investing enough in the digital infrastructure to support this.",
    },
]


def create_initial_org_politics_state() -> dict[str, Any]:
    """Create the starting organisational politics state."""
    members = []
    for m in CSUITE_MEMBERS:
        members.append({
            **m,
            "satisfaction": m["base_satisfaction"],
            "trust_in_player": 50.0,  # 0-100, how much they trust the CEO (player)
            "coalition_willingness": 0.5,  # 0-1, probability of joining a coalition
            "last_supported": None,
            "last_opposed": None,
            "opposition_streak": 0,
        })

    return {
        "csuite_members": members,
        "coalition_threshold": 3,  # Need 3/5 supporters to pass cleanly
        "political_capital": 100,  # Player's political capital budget
        "political_capital_regen": 15,  # Per round regeneration
        "decisions_forced": 0,  # Count of decisions pushed through without coalition
        "total_coalitions_built": 0,
        "org_politics_history": [],
    }


# ═══════════════════════════════════════════════════════════════
#  COALITION MECHANICS
# ═══════════════════════════════════════════════════════════════

def evaluate_csuite_support(
    org_state: dict,
    decision_tags: list[str],
    cost: float,
    gs: dict,
) -> dict:
    """
    Evaluate which C-suite members support or oppose a decision.
    Returns support map with reasoning.
    """
    members = org_state["csuite_members"]
    support_map = []
    total_support = 0
    total_opposed = 0

    for member in members:
        # Base support probability from satisfaction and trust
        base_prob = (member["satisfaction"] / 100.0) * 0.3 + (member["trust_in_player"] / 100.0) * 0.3

        # Topic alignment
        support_tags = set(member.get("support_topics", []))
        resist_tags = set(member.get("resistance_topics", []))
        decision_set = set(decision_tags)

        support_overlap = len(decision_set & support_tags)
        resist_overlap = len(decision_set & resist_tags)

        topic_modifier = (support_overlap - resist_overlap) * 0.15

        # Cost sensitivity (CFO cares more about cost)
        cost_modifier = 0.0
        if cost > 5_000_000 and "cost_reduction" in member["priorities"]:
            cost_modifier = -0.15
        elif cost < 1_000_000:
            cost_modifier = 0.05

        # Reputation context
        rep = gs.get("group_reputation", 50)
        rep_modifier = (rep - 50) / 200.0

        final_prob = max(0.1, min(0.95, base_prob + topic_modifier + cost_modifier + rep_modifier + 0.2))

        supports = random.random() < final_prob

        if supports:
            total_support += 1
        else:
            total_opposed += 1

        support_map.append({
            "member_id": member["id"],
            "name": member["name"],
            "title": member["title"],
            "icon": member["icon"],
            "supports": supports,
            "probability": round(final_prob, 3),
            "reasoning": (
                member["quote_supportive"] if supports
                else member["quote_resistant"]
            ),
            "key_concern": (
                member["priorities"][0] if member["priorities"]
                else "general"
            ),
        })

    has_coalition = total_support >= org_state.get("coalition_threshold", 3)

    return {
        "support_map": support_map,
        "total_support": total_support,
        "total_opposed": total_opposed,
        "has_coalition": has_coalition,
        "message": (
            f"✅ Coalition secured ({total_support}/5 support). Initiative proceeds with full backing."
            if has_coalition
            else f"⚠️ Insufficient support ({total_support}/5). Initiative will face implementation resistance."
        ),
    }


def apply_coalition_outcome(
    org_state: dict,
    coalition_result: dict,
    player_forced: bool = False,
) -> dict:
    """
    Apply consequences of coalition outcome.
    If player forces a decision without coalition support:
    - Political capital spent
    - Trust erosion with opposed members
    - Implementation penalty (reduced effectiveness)
    """
    extra = {}

    if coalition_result["has_coalition"]:
        org_state["total_coalitions_built"] += 1
        # Boost trust with supporters
        for entry in coalition_result["support_map"]:
            member = next(
                (m for m in org_state["csuite_members"] if m["id"] == entry["member_id"]),
                None,
            )
            if member and entry["supports"]:
                member["trust_in_player"] = min(100, member["trust_in_player"] + 3)
                member["satisfaction"] = min(100, member["satisfaction"] + 2)
        extra["coalition_trust_boost"] = True

    elif player_forced:
        org_state["decisions_forced"] += 1
        political_cost = 25
        org_state["political_capital"] = max(0, org_state["political_capital"] - political_cost)

        # Trust erosion with ALL opposed members
        for entry in coalition_result["support_map"]:
            if not entry["supports"]:
                member = next(
                    (m for m in org_state["csuite_members"] if m["id"] == entry["member_id"]),
                    None,
                )
                if member:
                    member["trust_in_player"] = max(0, member["trust_in_player"] - 10)
                    member["satisfaction"] = max(0, member["satisfaction"] - 8)
                    member["opposition_streak"] += 1

        extra["decision_forced"] = True
        extra["political_capital_spent"] = political_cost
        extra["implementation_penalty"] = 0.75  # 25% effectiveness reduction
        extra["force_message"] = (
            f"🏛️ Decision forced through executive authority. "
            f"Political capital: -{political_cost} (remaining: {org_state['political_capital']}). "
            f"Implementation effectiveness reduced to 75% due to internal resistance."
        )

    # Regenerate political capital
    org_state["political_capital"] = min(
        100,
        org_state["political_capital"] + org_state.get("political_capital_regen", 15),
    )

    return extra


def process_org_politics_tick(
    org_state: dict,
    gs: dict,
    bus: list[dict],
    events: dict,
    round_number: int,
) -> tuple[dict, dict]:
    """
    Process org politics updates for this round.
    Returns (updated_state, diagnostics).
    """
    diagnostics: dict[str, Any] = {}

    # Natural satisfaction drift based on company performance
    treasury = gs.get("corporate_treasury", 0)
    rep = gs.get("group_reputation", 50)
    avg_burnout = sum(bu.get("staff_burnout_index", 0) for bu in bus) / max(len(bus), 1)

    for member in org_state["csuite_members"]:
        # CFO: satisfaction tracks treasury
        if member["id"] == "cfo":
            treasury_health = min(1.0, treasury / 50_000_000)
            member["satisfaction"] = round(
                member["satisfaction"] * 0.9 + treasury_health * 10, 1
            )
        # CHRO: satisfaction tracks burnout (inverse)
        elif member["id"] == "chro":
            burnout_health = max(0, (100 - avg_burnout) / 100)
            member["satisfaction"] = round(
                member["satisfaction"] * 0.9 + burnout_health * 10, 1
            )
        # CSO: satisfaction tracks reputation + SLO
        elif member["id"] == "cso":
            avg_slo = sum(bu.get("social_license_score", 50) for bu in bus) / max(len(bus), 1)
            esg_health = (rep + avg_slo) / 200
            member["satisfaction"] = round(
                member["satisfaction"] * 0.9 + esg_health * 10, 1
            )

        # Clamp
        member["satisfaction"] = max(0, min(100, member["satisfaction"]))

    # Track average satisfaction
    avg_satisfaction = round(
        sum(m["satisfaction"] for m in org_state["csuite_members"])
        / len(org_state["csuite_members"]),
        1,
    )

    # Resignation risk: if satisfaction < 20 for 2+ rounds
    resignation_risk = [
        m["name"] for m in org_state["csuite_members"]
        if m["satisfaction"] < 20 and m["opposition_streak"] >= 2
    ]

    diagnostics["avg_satisfaction"] = avg_satisfaction
    diagnostics["resignation_risk"] = resignation_risk
    diagnostics["political_capital"] = org_state["political_capital"]
    diagnostics["decisions_forced"] = org_state["decisions_forced"]

    if resignation_risk:
        diagnostics["resignation_warning"] = (
            f"🚨 RESIGNATION RISK: {', '.join(resignation_risk)} may resign. "
            f"Continued overriding of their concerns is unsustainable."
        )

    org_state["org_politics_history"].append({
        "round": round_number,
        "avg_satisfaction": avg_satisfaction,
        "political_capital": org_state["political_capital"],
        "forced_decisions": org_state["decisions_forced"],
    })

    return org_state, diagnostics
