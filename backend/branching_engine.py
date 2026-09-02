"""
Muressons Global Corporation — Non-Linear Round Branching Engine (SI-1)
After R5, the simulation can diverge based on player archetype,
providing different crisis scenarios for different strategic profiles.

Theory base:
  - Mintzberg (1987): Strategy as Pattern — emergent strategy shapes path
  - March (1991): Exploration vs Exploitation
  - Snowden (2007): Cynefin Framework — complex vs complicated domains

Architecture:
  Pure-function module. Analyses cumulative player state at R5 to
  determine a "strategic archetype" that influences R6-R10 crisis
  selection and difficulty calibration.
"""

from __future__ import annotations
from typing import Any
import math


# ═══════════════════════════════════════════════════════════════
#  PLAYER ARCHETYPES (determined at R5 checkpoint)
# ═══════════════════════════════════════════════════════════════

ARCHETYPES = {
    "regenerative_leader": {
        "name": "Regenerative Leader",
        "icon": "🌱",
        "description": (
            "Consistent high investment in ESG across all dimensions. "
            "Reputation and social licence are strong. Treasury may be "
            "lower due to heavy investment, but long-term positioning is excellent."
        ),
        "criteria": {
            "reputation_min": 65,
            "avg_slo_min": 60,
            "avg_carbon_intensity_max": 45,
        },
        "branch_modifiers": {
            "crisis_severity_multiplier": 0.8,   # Easier crises (earned through investment)
            "opportunity_frequency": "high",      # More positive opportunities
            "stakeholder_support_bonus": 10,      # NPC stakeholders more supportive
            "unique_crisis": "scaling_challenge",  # R8: How to scale success?
        },
        "r6_r10_themes": [
            "R6: Responsible AI Scaling — your competitors are cutting corners",
            "R7: Circular Economy Leadership — standard-setting opportunity",
            "R8: Scaling Challenge — can you grow without compromising principles?",
            "R9: Just Transition — you have the trust capital to lead it well",
            "R10: Legacy Moment — will you codify your approach or cash out?",
        ],
    },
    "pragmatic_optimizer": {
        "name": "Pragmatic Optimizer",
        "icon": "⚖️",
        "description": (
            "Balanced approach: moderate ESG investment with strong financial "
            "performance. Neither leading nor lagging on sustainability. "
            "The 'sensible middle' — but is it enough?"
        ),
        "criteria": {
            "reputation_range": (40, 65),
            "treasury_min": 30_000_000,
        },
        "branch_modifiers": {
            "crisis_severity_multiplier": 1.0,    # Standard crises
            "opportunity_frequency": "medium",
            "stakeholder_support_bonus": 0,
            "unique_crisis": "disruption_test",
        },
        "r6_r10_themes": [
            "R6: AI Ethics Crossroads — pragmatism meets principle",
            "R7: Circular Economy — efficiency gains or transformation?",
            "R8: Industry Disruption — a competitor goes all-in on sustainability",
            "R9: Just Transition — hard choices with moderate trust capital",
            "R10: Strategic Fork — double down on ESG or optimise for exit?",
        ],
    },
    "fragile_extractor": {
        "name": "Fragile Extractor",
        "icon": "🔥",
        "description": (
            "Short-term financial optimisation at the expense of ESG. "
            "Treasury may be strong but reputation, social licence, and "
            "environmental metrics are deteriorating. A ticking time bomb."
        ),
        "criteria": {
            "reputation_max": 40,
            "avg_slo_max": 40,
        },
        "branch_modifiers": {
            "crisis_severity_multiplier": 1.5,    # Harder crises (earned through neglect)
            "opportunity_frequency": "low",
            "stakeholder_support_bonus": -10,
            "unique_crisis": "reckoning",
        },
        "r6_r10_themes": [
            "R6: AI Ethics Crisis — your shortcuts are being exposed",
            "R7: Regulatory Crackdown — circular economy mandated, not optional",
            "R8: The Reckoning — accumulated risks materialise simultaneously",
            "R9: Forced Transition — no trust capital for a managed approach",
            "R10: Survival Mode — can you avoid corporate collapse?",
        ],
    },
    "turnaround_candidate": {
        "name": "Turnaround Candidate",
        "icon": "🔄",
        "description": (
            "Started poorly but showing signs of course correction. "
            "Reputation improving, ESG metrics trending upward. "
            "The question is: is the turnaround fast enough?"
        ),
        "criteria": {
            "reputation_trend": "improving",  # Compared to R1
            "recent_esg_investment": True,
        },
        "branch_modifiers": {
            "crisis_severity_multiplier": 1.2,
            "opportunity_frequency": "medium",
            "stakeholder_support_bonus": 5,       # Market rewards turnaround stories
            "unique_crisis": "credibility_test",
        },
        "r6_r10_themes": [
            "R6: Proving the Pivot — stakeholders are watching closely",
            "R7: Circular Economy — a chance to demonstrate commitment",
            "R8: Credibility Test — is this real change or rebranding?",
            "R9: Just Transition — your past decisions haunt the present",
            "R10: The Verdict — has the turnaround earned trust?",
        ],
    },
}


# ═══════════════════════════════════════════════════════════════
#  ARCHETYPE CLASSIFICATION
# ═══════════════════════════════════════════════════════════════

def classify_player_archetype(
    gs: dict,
    bus: list[dict],
    decision_history: list[dict] | None = None,
) -> dict:
    """
    Classify the player into an archetype based on R1-R5 performance.
    Called at the R5 formative checkpoint.
    """
    rep = gs.get("group_reputation", 50)
    treasury = gs.get("corporate_treasury", 0)
    avg_slo = sum(bu.get("social_license_score", 50) for bu in bus) / max(len(bus), 1)
    avg_ci = sum(bu.get("carbon_intensity", 50) for bu in bus) / max(len(bus), 1)
    avg_burnout = sum(bu.get("staff_burnout_index", 0) for bu in bus) / max(len(bus), 1)

    # Check for Regenerative Leader
    regen = ARCHETYPES["regenerative_leader"]["criteria"]
    if (rep >= regen["reputation_min"]
        and avg_slo >= regen["avg_slo_min"]
        and avg_ci <= regen["avg_carbon_intensity_max"]):
        archetype_id = "regenerative_leader"

    # Check for Fragile Extractor
    elif rep <= ARCHETYPES["fragile_extractor"]["criteria"]["reputation_max"] \
         and avg_slo <= ARCHETYPES["fragile_extractor"]["criteria"]["avg_slo_max"]:
        archetype_id = "fragile_extractor"

    # Check for Turnaround Candidate (improving trend)
    elif decision_history and len(decision_history) >= 3:
        # Simple trend: is reputation higher now than at R2?
        early_rep = gs.get("reputation_history", [rep])[0] if gs.get("reputation_history") else rep
        if rep > early_rep + 5:
            archetype_id = "turnaround_candidate"
        else:
            archetype_id = "pragmatic_optimizer"
    else:
        archetype_id = "pragmatic_optimizer"

    archetype = ARCHETYPES[archetype_id]

    return {
        "archetype_id": archetype_id,
        "archetype_name": archetype["name"],
        "icon": archetype["icon"],
        "description": archetype["description"],
        "branch_modifiers": archetype["branch_modifiers"],
        "r6_r10_themes": archetype["r6_r10_themes"],
        "classification_data": {
            "reputation": round(rep, 2),
            "avg_slo": round(avg_slo, 2),
            "avg_carbon_intensity": round(avg_ci, 2),
            "treasury": treasury,
            "avg_burnout": round(avg_burnout, 2),
        },
        "message": (
            f"{archetype['icon']} Your strategic archetype: **{archetype['name']}**\n\n"
            f"{archetype['description']}\n\n"
            f"This classification will influence the challenges and opportunities "
            f"you face in Rounds 6-10."
        ),
    }


# ═══════════════════════════════════════════════════════════════
#  ADAPTIVE CRISIS SEVERITY (SE-3)
# ═══════════════════════════════════════════════════════════════

def calc_adaptive_crisis_severity(
    base_severity: float,
    archetype_id: str,
    gs: dict,
    bus: list[dict],
    round_number: int,
) -> tuple[float, dict]:
    """
    SE-3: Adaptive crisis severity based on player state.
    Prevents "cruise control" for strong players and provides
    proportional challenge for struggling players.

    If a player is doing well (high treasury, rep), crises intensify.
    If struggling, crises may ease slightly to keep the game educational.
    """
    archetype = ARCHETYPES.get(archetype_id, ARCHETYPES["pragmatic_optimizer"])
    branch_mult = archetype["branch_modifiers"]["crisis_severity_multiplier"]

    rep = gs.get("group_reputation", 50)
    treasury = gs.get("corporate_treasury", 0)
    avg_slo = sum(bu.get("social_license_score", 50) for bu in bus) / max(len(bus), 1)

    # Performance index: 0-100 composite
    perf_index = (
        rep * 0.3
        + min(100, treasury / 500_000) * 0.3  # Normalise treasury to 0-100
        + avg_slo * 0.2
        + gs.get("workforce_readiness", 50) * 0.2
    )

    # Adaptive scaling: strong players get harder crises
    if perf_index > 70:
        adaptive_mult = 1.0 + (perf_index - 70) / 100  # Up to 1.3x
    elif perf_index < 30:
        adaptive_mult = 0.8 + (perf_index / 100)  # Down to 0.8x
    else:
        adaptive_mult = 1.0

    # Round escalation: crises get harder in later rounds
    round_mult = 1.0 + (round_number - 5) * 0.05  # +5% per round after R5

    final_severity = round(base_severity * branch_mult * adaptive_mult * round_mult, 2)

    diagnostics = {
        "base_severity": base_severity,
        "archetype_multiplier": branch_mult,
        "adaptive_multiplier": round(adaptive_mult, 3),
        "round_multiplier": round(round_mult, 3),
        "final_severity": final_severity,
        "performance_index": round(perf_index, 1),
        "message": (
            f"Crisis severity calibrated to your performance "
            f"(Performance Index: {perf_index:.0f}/100). "
            + (
                "Your strong track record means stakeholders expect MORE from you."
                if adaptive_mult > 1.1
                else "Standard crisis calibration applies."
                if adaptive_mult > 0.95
                else "Crisis moderated to maintain educational value."
            )
        ),
    }

    return final_severity, diagnostics


# ═══════════════════════════════════════════════════════════════
#  EXTENDED HORIZON MODE (SI-3)
# ═══════════════════════════════════════════════════════════════

# Extended Horizon (rounds 11–20) content lived here until F-32 (launch audit
# 2026-09-01) retired the feature: it could never be played (commit cap, DB
# CHECK constraint, cockpit game-over logic). The recovery-round content in
# turnaround_engine.py is the surviving sibling.
