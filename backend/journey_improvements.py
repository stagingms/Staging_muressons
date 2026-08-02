from __future__ import annotations
"""
Muressons Global Corporation — Journey Improvements (Phase 6)
Pedagogical Review Implementation: R1 split, R6 climax redesign,
R7-R8 mechanic variation, persona pain point removals.

All functions are pure helpers returning config overlays. They do NOT
modify the frozen ROUND_CONFIGS directly — callers apply the patches
conditionally (e.g. when Foundation tier is active or self-learning mode).

References:
  - Sweller (1988): Cognitive Load Theory → R1a/R1b split
  - Kolb (1984): Experiential Learning Cycle → R6 mechanic change
  - Thiagarajan (2006): Debriefing frames → R7-R8 variation
"""

from typing import Any


# ═════════════════════════════════════════════════════════════════
#  1. R1 PHASE SPLIT (R1a → R1b)
#
#  Problem: R1 currently overloads new players with ESG audit +
#  Stakeholder Map + Materiality concepts in a single turn.
#  Sweller (1988): Intrinsic cognitive load ≫ germane load.
#
#  Solution: Split R1 into two half-rounds:
#    R1a: "Orientation" — Narrative only, no investment decision.
#         Players read the ESG briefing, meet the board personas,
#         and complete the Stakeholder Map. No commit required.
#    R1b: "First Decision" — The actual A/B/C audit choice.
#         Now players have context and mental models before deciding.
#
#  For Expert tier: R1a and R1b collapse back into normal R1.
# ═════════════════════════════════════════════════════════════════

R1_SPLIT_CONFIG = {
    "r1a": {
        "title": "Orientation — Meet the Board",
        "theme": "Company Onboarding & Stakeholder Mapping",
        "is_orientation": True,
        "skip_decision": True,  # No A/B/C choice — just exploration
        "crisis": {
            "id": "r1a_orientation",
            "title": "Welcome to Muressons Global Corporation",
            "description": (
                "You have been appointed to the Board of Muressons Group, "
                "a multinational conglomerate with four business units: "
                "Pharma, Electronics, Consumer Goods, and Software. "
                "Before making any strategic decisions, familiarise yourself "
                "with each unit's financials and ESG posture. Complete the "
                "Stakeholder Map to unlock Round 1b."
            ),
            "icon": "🏢",
        },
        "orientation_tasks": [
            {
                "id": "read_briefing",
                "label": "Read the Executive Briefing",
                "icon": "📋",
                "instruction": "Review the company profile, BU financials, and ESG baseline in the briefing panel.",
            },
            {
                "id": "stakeholder_map",
                "label": "Complete the Stakeholder Map",
                "icon": "⚖️",
                "instruction": "Drag stakeholders into the correct Mendelow quadrant. This is graded — accuracy affects R4 crisis severity.",
            },
            {
                "id": "meet_personas",
                "label": "Read Board Member Profiles",
                "icon": "👥",
                "instruction": (
                    "The AI Board Members (CFO Sarah Chen, CSO Dr. Kwame Asante, "
                    "GC Marcus Wong, CRO Elena Vasquez) each have different priorities. "
                    "Their advice in your mailbox reflects these biases."
                ),
            },
        ],
        "pedagogical_purpose": (
            "Reduces cognitive overload (Sweller 1988) by separating "
            "context-building from decision-making. Players establish "
            "germane schemas before facing their first strategic choice."
        ),
    },
    "r1b": {
        "title": "First Decision — ESG Audit",
        "theme": "ESG Baseline Assessment",
        "is_first_decision": True,
        "crisis": {
            "id": "r1b_first_decision",
            "title": "ESG Audit Decision",
            "description": (
                "Now that you understand the company's position, the board "
                "has mandated an initial ESG assessment across all business "
                "units. Choose the depth and scope of the audit. "
                "Your Stakeholder Map accuracy from R1a will influence "
                "future crisis severity."
            ),
            "icon": "📋",
        },
        # Options identical to normal R1 — inherits from ROUND_CONFIGS[1]
        "inherit_options_from": 1,
        "pedagogical_purpose": (
            "First genuine decision point. Players have built mental models "
            "during orientation and can now make an informed choice."
        ),
    },
}


def get_r1_split_config(phase: str) -> dict[str, Any] | None:
    """Return R1a or R1b config for Foundation/Advanced tiers."""
    return R1_SPLIT_CONFIG.get(phase)


def should_split_r1(difficulty_tier: str) -> bool:
    """Expert tier collapses R1a+R1b into single R1."""
    return difficulty_tier in ("foundation", "advanced")


# ═════════════════════════════════════════════════════════════════
#  2. R6 SECOND CLIMAX REDESIGN
#
#  Problem: R6 (AI Bias) feels like a dip in narrative tension
#  between the R5 climate event (physical danger) and R7-R9
#  circularity arc. The "second act" needs a climax.
#
#  Solution: Add a "revelation mechanic" — after players choose
#  their R6 option, a second-stage consequence is revealed that
#  forces a follow-up micro-decision. This creates the dramatic
#  twist that sustains engagement through the mid-game.
# ═════════════════════════════════════════════════════════════════

R6_REVELATION_MECHANIC = {
    "enabled": True,
    "revelation_trigger": "post_decision",
    "title": "🚨 Breaking: Whistleblower Leak",
    "narrative": (
        "BREAKING NEWS: A former employee has leaked internal documents "
        "showing the AI bias was KNOWN internally for 18 months before "
        "the public scandal broke. The board chair is demanding an "
        "emergency response."
    ),
    "micro_decisions": {
        "accept_accountability": {
            "label": "Accept Full Accountability",
            "description": (
                "The CEO goes public with a mea culpa. Accept the reputational "
                "hit now to prevent prolonged damage."
            ),
            "icon": "🎤",
            "impacts": {
                "reputation_delta": -8,  # Short-term hit
                "social_license_delta": +12,  # Long-term trust gain
                "governance_risk_delta": -8,
            },
            "flags_set": ["whistleblower_accountability"],
        },
        "legal_containment": {
            "label": "Legal Containment",
            "description": (
                "Instruct legal to pursue injunctions against the whistleblower. "
                "May contain the story — or may backfire spectacularly."
            ),
            "icon": "⚖️",
            "impacts": {
                "treasury": -3_000_000,
                "reputation_delta": -3,  # Mild initial hit
                "governance_risk_delta": +15,  # Massive governance exposure
            },
            "stochastic": {
                "backfire_probability": 0.40,
                "backfire_narrative": (
                    "The injunction attempt has BACKFIRED. #StreisandEffect is "
                    "trending. Reputation drops an additional 15 points."
                ),
                "backfire_impacts": {"reputation_delta": -15},
            },
            "flags_set": ["whistleblower_suppressed"],
        },
        "internal_investigation": {
            "label": "Launch Independent Investigation",
            "description": (
                "Commission an external ethics review panel. Transparent, "
                "thorough, but expensive and slow."
            ),
            "icon": "🔍",
            "impacts": {
                "treasury": -5_000_000,
                "reputation_delta": +3,
                "social_license_delta": +8,
                "governance_risk_delta": -12,
            },
            "flags_set": ["independent_investigation"],
        },
    },
    "pedagogical_purpose": (
        "Creates Kolb (1984) 'Reflective Observation' moment — players "
        "must re-evaluate their initial R6 choice in light of new "
        "information, simulating real-world iterative decision-making."
    ),
}


def get_r6_revelation() -> dict[str, Any]:
    """Return the R6 revelation mechanic config."""
    return R6_REVELATION_MECHANIC


# ═════════════════════════════════════════════════════════════════
#  3. R7-R8 MECHANIC VARIATION
#
#  Problem: R7 (Circularity) and R8 (Water Stress) both use the
#  same A/B/C decision mechanic. By this point learners have
#  habituated to the interface (Thiagarajan 2006: "game fatigue").
#
#  Solution: Introduce mechanic variations that break the pattern:
#    R7: "Supplier Negotiation" — players must allocate a fixed
#        budget across 3 circular economy initiatives using sliders
#        (not mutually exclusive choices). Teaches trade-off thinking.
#    R8: "Stakeholder Tribunal" — a timed debate format where players
#        must respond to stakeholder challenges in sequence. Teaches
#        stakeholder management under pressure.
# ═════════════════════════════════════════════════════════════════

R7_BUDGET_ALLOCATION_VARIANT = {
    "enabled": True,
    "mechanic": "budget_allocation",
    "title": "Circular Economy Budget Allocation",
    "instruction": (
        "You have a $15M circular economy budget. Distribute it across "
        "three initiatives. Each dollar generates different returns depending "
        "on allocation balance. There is no single 'right answer' — the "
        "optimal split depends on your current BU health."
    ),
    "total_budget": 15_000_000,
    "initiatives": {
        "product_redesign": {
            "label": "Product Redesign",
            "icon": "🔄",
            "description": "Redesign products for disassembly and material recovery.",
            "per_million_impact": {
                "natural_capital_debt_delta": -1.2,
                "carbon_intensity_delta": -0.8,
                "revenue_delta": +100_000,
            },
            "synergy_threshold": 8_000_000,  # Bonus if >$8M allocated
            "synergy_bonus": {"reputation": +5, "flags_set": ["circular_redesign"]},
        },
        "take_back_program": {
            "label": "Take-Back Program",
            "icon": "📦",
            "description": "Fund consumer take-back and recycling infrastructure.",
            "per_million_impact": {
                "natural_capital_debt_delta": -0.6,
                "social_license_delta": +1.5,
                "revenue_delta": +60_000,
            },
            "synergy_threshold": 5_000_000,
            "synergy_bonus": {"social_license_delta": +8, "flags_set": ["epr_program"]},
        },
        "waste_to_energy": {
            "label": "Waste-to-Energy",
            "icon": "⚡",
            "description": "Convert manufacturing waste into energy, reducing OPEX.",
            "per_million_impact": {
                "carbon_intensity_delta": -0.6,
                "synergy_multiplier_boost": 0.02,
                "revenue_delta": +40_000,
            },
            "synergy_threshold": 7_000_000,
            "synergy_bonus": {
                "synergy_multiplier_boost": 0.15,
                "flags_set": ["waste_to_energy", "synergy_unlock"],
            },
        },
    },
    "pedagogical_purpose": (
        "Breaks A/B/C habituation. Teaches continuous trade-off thinking "
        "(Thiagarajan 2006 mechanic variation). Players must understand "
        "diminishing returns and portfolio allocation — key sustainability "
        "leadership competencies."
    ),
}


R8_STAKEHOLDER_TRIBUNAL_VARIANT = {
    "enabled": True,
    "mechanic": "stakeholder_tribunal",
    "title": "Stakeholder Water Tribunal",
    "instruction": (
        "Three stakeholder groups are demanding water allocation priority. "
        "You must respond to each challenge. Your responses determine the "
        "combined outcome — there are no 'safe' answers when resources "
        "are genuinely scarce."
    ),
    "time_pressure": True,
    "response_time_seconds": 90,  # Per challenge
    "challenges": [
        {
            "stakeholder": "Local Community Representatives",
            "icon": "🏘️",
            "challenge": (
                "Our children are drinking contaminated water while your "
                "Electronics factory runs 24/7. We demand a 40% water "
                "allocation to residential use."
            ),
            "responses": {
                "comply": {
                    "label": "Accept 40% Residential Allocation",
                    "impacts": {"social_license_delta": +12, "revenue_delta": -800_000},
                },
                "negotiate": {
                    "label": "Counter: 25% + Water Treatment Plant",
                    "impacts": {"treasury": -3_000_000, "social_license_delta": +6, "reputation": +3},
                },
                "deflect": {
                    "label": "Refer to Government Water Authority",
                    "impacts": {"social_license_delta": -8, "governance_risk_delta": +5},
                },
            },
        },
        {
            "stakeholder": "Environmental NGO Coalition",
            "icon": "🌿",
            "challenge": (
                "Your desalination plans will destroy the marine ecosystem. "
                "We have photographic evidence of coral bleaching from your "
                "intake pipes. Cease all desalination operations."
            ),
            "responses": {
                "comply": {
                    "label": "Halt Desalination, Accept Water Shortfall",
                    "impacts": {"natural_capital_debt_delta": -15, "water_dependency_delta": +20},
                },
                "negotiate": {
                    "label": "Commission Independent Environmental Impact Study",
                    "impacts": {"treasury": -2_000_000, "natural_capital_debt_delta": -5, "reputation": +4},
                },
                "deflect": {
                    "label": "Challenge the Evidence Quality",
                    "impacts": {"reputation": -6, "governance_risk_delta": +8},
                },
            },
        },
        {
            "stakeholder": "Employee Union",
            "icon": "✊",
            "challenge": (
                "Workers in the Pharma cleanroom facility report dehydration "
                "and unsafe working conditions due to water rationing. "
                "We will strike unless water access is restored within 48 hours."
            ),
            "responses": {
                "comply": {
                    "label": "Restore Full Water Access to Pharma",
                    "impacts": {"social_license_delta": +8, "treasury": -1_500_000},
                },
                "negotiate": {
                    "label": "Emergency Water Trucking + Safety Bonus",
                    "impacts": {"treasury": -4_000_000, "social_license_delta": +5, "reputation": +2},
                },
                "deflect": {
                    "label": "Invoke Force Majeure Clause",
                    "impacts": {"social_license_delta": -15, "strike_risk": True},
                },
            },
        },
    ],
    "pedagogical_purpose": (
        "Mechanic variation: sequential stakeholder challenges under "
        "time pressure. Tests empathy, negotiation, and systems thinking. "
        "No single 'right answer' — teaches that sustainability leadership "
        "requires managing legitimate competing claims (Freeman 1984)."
    ),
}


def get_r7_variant() -> dict[str, Any]:
    """Return R7 budget allocation mechanic variant."""
    return R7_BUDGET_ALLOCATION_VARIANT


def get_r8_variant() -> dict[str, Any]:
    """Return R8 stakeholder tribunal mechanic variant."""
    return R8_STAKEHOLDER_TRIBUNAL_VARIANT


# ═════════════════════════════════════════════════════════════════
#  4. PERSONA PAIN POINT REMOVALS
#
#  Common player complaints from facilitator debriefs:
#    - "I didn't understand what option C actually does" → fixed
#      by adding explicit consequence previews
#    - "The numbers surprised me — I couldn't predict the outcome"
#      → fixed by adding impact magnitude indicators
#    - "R4 felt unfair because of something I did in R1" → fixed
#      by adding flag dependency warnings
# ═════════════════════════════════════════════════════════════════

IMPACT_MAGNITUDE_LABELS = {
    "negligible": {"label": "Minimal Impact", "icon": "·", "color": "#64748b"},
    "moderate": {"label": "Moderate Impact", "icon": "●", "color": "#f59e0b"},
    "significant": {"label": "Major Impact", "icon": "●●", "color": "#ef4444"},
    "transformative": {"label": "Transformative", "icon": "●●●", "color": "#8b5cf6"},
}


def classify_impact_magnitude(treasury_delta: int = 0, reputation_delta: int = 0,
                               carbon_delta: int = 0) -> str:
    """Classify an option's combined impact magnitude for UI display."""
    score = (
        abs(treasury_delta) / 5_000_000 +
        abs(reputation_delta) / 10 +
        abs(carbon_delta) / 5
    )
    if score < 1:
        return "negligible"
    elif score < 3:
        return "moderate"
    elif score < 6:
        return "significant"
    else:
        return "transformative"


FLAG_DEPENDENCY_WARNINGS = {
    # Round 4 depends on R1
    4: {
        "electronics_blindspot": {
            "from_round": 1,
            "from_option": "option_a",
            "warning": (
                "⚠️ Your R1 Surface-Level Scan left an Electronics blind spot. "
                "This round's crisis severity is DOUBLED because the labour-rights "
                "issues were not detected early."
            ),
            "severity": "critical",
        },
    },
    # Round 7 depends on R5
    7: {
        "hard_engineering": {
            "from_round": 5,
            "from_option": "option_a",
            "warning": (
                "✅ Your R5 Hard Engineering Defence completes this round. "
                "Infrastructure resilience factor now active (0.85)."
            ),
            "severity": "positive",
        },
        "nature_based_resilience": {
            "from_round": 5,
            "from_option": "option_b",
            "warning": (
                "✅ Your R5 Nature-Based Solutions mature this round. "
                "Ecosystem buffers now providing resilience factor (0.60) "
                "and ongoing NCD reduction."
            ),
            "severity": "positive",
        },
    },
    # Round 8 depends on R2
    8: {
        "materiality_ignored": {
            "from_round": 2,
            "from_option": "option_c",
            "warning": (
                "⚠️ Your R2 decision to ignore the Materiality Framework "
                "means you have no ESG data infrastructure. Water dependency "
                "measurements are unreliable — actual impact may be 25% worse "
                "than projected."
            ),
            "severity": "warning",
        },
    },
    # Round 10 depends on R7 synergy
    10: {
        "synergy_unlock": {
            "from_round": 7,
            "from_option": "option_c",
            "warning": (
                "✅ Your R7 Waste-to-Energy synergy unlock qualifies you "
                "for Option A (Resist & Integrate) if Synergy Score > 80."
            ),
            "severity": "positive",
        },
    },
}


def get_flag_dependency_warnings(round_number: int, active_flags: dict) -> list[dict]:
    """Return list of dependency warnings relevant to this round."""
    warnings = []
    round_deps = FLAG_DEPENDENCY_WARNINGS.get(round_number, {})
    for flag_key, warning_config in round_deps.items():
        if flag_key in active_flags:
            warnings.append(warning_config)
    return warnings


def get_impact_magnitude(option_impacts: dict) -> dict[str, Any]:
    """Return magnitude classification for an option's impact dict."""
    magnitude = classify_impact_magnitude(
        treasury_delta=option_impacts.get("treasury", 0),
        reputation_delta=option_impacts.get("reputation", option_impacts.get("reputation_delta", 0)),
        carbon_delta=option_impacts.get("carbon_intensity_delta", 0),
    )
    return IMPACT_MAGNITUDE_LABELS[magnitude]
