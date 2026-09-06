"""
Muressons Global Corporation — Board Governance Minigame (SE-1)
Simulates corporate board dynamics: composition, voting, executive
compensation, ESG committee mandate, and shareholder resolutions.

Theory base:
  - Cadbury Report (1992): Board independence
  - UK Corporate Governance Code (2018): Board effectiveness
  - ICGN Global Governance Principles (2021)
  - Jensen & Meckling (1976): Agency theory
  - Bebchuk (2005): Pay without performance

Architecture:
  Pure-function module. Board state is maintained as a dict within
  global_state["board_governance"]. Updated via minigame interactions
  at configurable round triggers (default: R3, R6).
"""

from __future__ import annotations
from typing import Any
import math


# ═══════════════════════════════════════════════════════════════
#  INITIAL BOARD STATE
# ═══════════════════════════════════════════════════════════════

INITIAL_DIRECTORS = [
    {
        "id": "chair",
        "name": "Helena Van der Berg",
        "role": "Chair (Non-Executive)",
        "icon": "👩‍💼",
        "independence": True,
        "tenure_years": 8,
        "expertise": ["governance", "strategy"],
        "esg_alignment": 0.4,  # 0-1: how ESG-aligned their voting is
        "voting_bloc": "traditional",
        "bio": "Former McKinsey partner. Prioritises shareholder returns and cost discipline.",
    },
    {
        "id": "ceo",
        "name": "Marcus Chen",
        "role": "CEO (Executive)",
        "icon": "👨‍💼",
        "independence": False,
        "tenure_years": 5,
        "expertise": ["operations", "strategy", "finance"],
        "esg_alignment": 0.5,
        "voting_bloc": "management",
        "bio": "Operations-focused CEO. Open to ESG if it demonstrably improves margins.",
    },
    {
        "id": "cfo",
        "name": "Priya Krishnamurthy",
        "role": "CFO (Executive)",
        "icon": "👩‍💼",
        "independence": False,
        "tenure_years": 3,
        "expertise": ["finance", "risk"],
        "esg_alignment": 0.3,
        "voting_bloc": "management",
        "bio": "Risk-averse CFO. Views ESG primarily through cost-of-capital lens.",
    },
    {
        "id": "ned_sustainability",
        "name": "Dr. Amara Osei",
        "role": "NED (Sustainability)",
        "icon": "👩‍🔬",
        "independence": True,
        "tenure_years": 2,
        "expertise": ["sustainability", "climate", "governance"],
        "esg_alignment": 0.9,
        "voting_bloc": "progressive",
        "bio": "Former UNFCCC negotiator. Champion of science-based targets.",
    },
    {
        "id": "ned_finance",
        "name": "Sir James Hartley",
        "role": "NED (Finance)",
        "icon": "🧑‍💼",
        "independence": True,
        "tenure_years": 11,
        "expertise": ["finance", "M&A"],
        "esg_alignment": 0.2,
        "voting_bloc": "traditional",
        "bio": "Ex-Goldman Sachs. Sceptical of ESG, prefers shareholder value maximisation.",
    },
    {
        "id": "ned_legal",
        "name": "Maria Santos",
        "role": "NED (Legal/Compliance)",
        "icon": "👩‍⚖️",
        "independence": True,
        "tenure_years": 4,
        "expertise": ["legal", "compliance", "governance"],
        "esg_alignment": 0.6,
        "voting_bloc": "swing",
        "bio": "Corporate governance expert. Follows regulatory trends closely.",
    },
    {
        "id": "ned_tech",
        "name": "Kenji Tanaka",
        "role": "NED (Technology)",
        "icon": "👨‍💻",
        "independence": True,
        "tenure_years": 1,
        "expertise": ["technology", "innovation", "ai"],
        "esg_alignment": 0.5,
        "voting_bloc": "swing",
        "bio": "AI ethics researcher. Interested in responsible technology deployment.",
    },
    {
        "id": "worker_rep",
        "name": "Anna Kowalski",
        "role": "Employee Representative",
        "icon": "👷‍♀️",
        "independence": True,
        "tenure_years": 2,
        "expertise": ["operations", "labour"],
        "esg_alignment": 0.7,
        "voting_bloc": "progressive",
        "bio": "Former shop steward. Advocates for just transition and worker welfare.",
    },
]


def create_initial_board_state() -> dict[str, Any]:
    """Create the starting board governance state."""
    return {
        "directors": [d.copy() for d in INITIAL_DIRECTORS],
        "board_size": len(INITIAL_DIRECTORS),
        "independence_ratio": sum(1 for d in INITIAL_DIRECTORS if d["independence"]) / len(INITIAL_DIRECTORS),
        "avg_esg_alignment": sum(d["esg_alignment"] for d in INITIAL_DIRECTORS) / len(INITIAL_DIRECTORS),
        "esg_committee_established": False,
        "esg_committee_mandate": "advisory",  # advisory, oversight, binding
        "esg_linked_compensation_pct": 0,  # % of exec pay tied to ESG
        "say_on_pay_approval": 100.0,  # Last AGM approval %
        "shareholder_resolutions_pending": [],
        "board_effectiveness_score": 65.0,  # 0-100
        "governance_history": [],
        "activist_nominees_seated": 0,
        "diversity_score": 0.625,  # Gender + expertise diversity
    }


# ═══════════════════════════════════════════════════════════════
#  SHAREHOLDER RESOLUTIONS
# ═══════════════════════════════════════════════════════════════

SHAREHOLDER_RESOLUTIONS = [
    {
        "id": "climate_disclosure",
        "title": "Enhanced Climate Risk Disclosure (TCFD-aligned)",
        "proposer": "FutureFirst Activist Fund",
        "round_available": 3,
        "description": (
            "Requires the company to publish annual TCFD-aligned climate risk "
            "assessment including Scope 3 emissions and 1.5°C scenario analysis."
        ),
        "esg_impact": {"reputation": 5, "governance_risk_delta": -5},
        "cost": 500_000,
        "opposition_argument": "Commercially sensitive data exposure. Competitive disadvantage.",
        "support_threshold": 0.50,
    },
    {
        "id": "exec_esg_pay",
        "title": "Link 30% of Executive Compensation to ESG Targets",
        "proposer": "CalPERS Pension Fund",
        "round_available": 3,
        "description": (
            "Amend executive compensation policy to tie 30% of annual bonus "
            "to measurable ESG KPIs: emissions reduction, social licence, and "
            "governance effectiveness."
        ),
        "esg_impact": {"esg_linked_compensation_pct": 30},
        "cost": 0,
        "opposition_argument": "Distorts incentives. ESG metrics are subjective and gameable.",
        "support_threshold": 0.50,
    },
    {
        "id": "nature_positive",
        "title": "Adopt Nature-Positive Commitment by 2030",
        "proposer": "Green Century Capital Management",
        "round_available": 6,
        "description": (
            "Commit to TNFD-aligned disclosure, set Science Based Targets for "
            "Nature (SBTN), and achieve net positive biodiversity impact by 2030."
        ),
        "esg_impact": {"reputation": 3, "tnfd_level": "aligned"},
        "cost": 1_000_000,
        "opposition_argument": "Immature framework. No reliable biodiversity metrics yet.",
        "support_threshold": 0.50,
    },
    {
        "id": "human_rights_dd",
        "title": "Mandatory Human Rights Due Diligence (EU CS3D Proactive)",
        "proposer": "Amnesty International (shareholder coalition)",
        "round_available": 6,
        "description": (
            "Implement full EU CS3D-compliant human rights due diligence across "
            "all supply chain tiers before regulatory deadline."
        ),
        "esg_impact": {"social_license_delta": 5, "governance_risk_delta": -3},
        "cost": 2_000_000,
        "opposition_argument": "CS3D not yet enforced. Pre-compliance is premature spending.",
        "support_threshold": 0.50,
    },
]


def simulate_board_vote(
    board_state: dict,
    resolution: dict,
    player_recommendation: str,  # "support" or "oppose"
    gs: dict,
) -> dict:
    """
    Simulate a board vote on a shareholder resolution.
    Each director votes based on their ESG alignment + player influence.
    Player recommendation carries weight proportional to board effectiveness.
    """
    directors = board_state["directors"]
    votes_for = 0
    votes_against = 0
    vote_details = []

    # Player's influence weight (CEO recommendation power)
    player_influence = 0.3 if player_recommendation == "support" else -0.3

    # Reputation context: high rep makes progressive resolutions easier to pass
    rep_modifier = (gs.get("group_reputation", 50) - 50) / 200.0

    # RNG-8 (audit 2026-09-04, Wave 3): the per-director roll came from the
    # process-global Random — unseeded, and shared with every other module's
    # fallback draws. It is the cohort's event stream now (seeded when the
    # session carries a stochastic_seed; system-seeded otherwise), keyed by
    # round and resolution so a repeat vote on the same resolution is the same.
    from rng_util import event_rng
    _rng = event_rng(gs.get("active_event_flags") or {}, int(gs.get("round_number", 0) or 0),
                     f"board_vote:{resolution.get('id', '')}")

    for director in directors:
        # Base probability of supporting = ESG alignment
        base_prob = director["esg_alignment"]

        # Modify by player recommendation
        prob = base_prob + player_influence + rep_modifier

        # Bloc dynamics
        if director["voting_bloc"] == "progressive":
            prob += 0.1
        elif director["voting_bloc"] == "traditional":
            prob -= 0.1

        prob = max(0.05, min(0.95, prob))

        # Stochastic vote (RNG-8: seeded stream)
        roll = _rng.random()
        voted_for = roll < prob

        if voted_for:
            votes_for += 1
        else:
            votes_against += 1

        vote_details.append({
            "director_id": director["id"],
            "director_name": director["name"],
            "voted_for": voted_for,
            "probability": round(prob, 3),
        })

    total_votes = votes_for + votes_against
    support_pct = votes_for / total_votes if total_votes > 0 else 0
    passed = support_pct >= resolution.get("support_threshold", 0.50)

    return {
        "resolution_id": resolution["id"],
        "resolution_title": resolution["title"],
        "votes_for": votes_for,
        "votes_against": votes_against,
        "support_percentage": round(support_pct * 100, 1),
        "passed": passed,
        "player_recommendation": player_recommendation,
        "vote_details": vote_details,
        "impact": resolution["esg_impact"] if passed else {},
        "cost": resolution["cost"] if passed else 0,
        "message": (
            f"✅ Resolution PASSED ({support_pct:.0%} support): {resolution['title']}"
            if passed
            else f"❌ Resolution DEFEATED ({support_pct:.0%} support): {resolution['title']}"
        ),
    }


# ═══════════════════════════════════════════════════════════════
#  EXECUTIVE COMPENSATION ENGINE
# ═══════════════════════════════════════════════════════════════

def calc_say_on_pay(
    board_state: dict,
    gs: dict,
    bus: list[dict],
) -> dict:
    """
    Simulate annual Say-on-Pay advisory vote.
    Approval depends on ESG performance, reputation, and pay ratio.

    Bebchuk (2005): Pay-for-performance sensitivity.
    """
    esg_pct = board_state.get("esg_linked_compensation_pct", 0)
    rep = gs.get("group_reputation", 50)
    avg_slo = sum(bu.get("social_license_score", 50) for bu in bus) / max(len(bus), 1)

    # Higher ESG-linked pay + good reputation = higher approval
    base_approval = 60.0
    esg_bonus = esg_pct * 0.3  # Up to +9 at 30%
    rep_bonus = (rep - 50) * 0.2  # +/- 10
    slo_bonus = (avg_slo - 50) * 0.1  # +/- 5

    approval = base_approval + esg_bonus + rep_bonus + slo_bonus
    approval = max(20.0, min(99.0, round(approval, 1)))

    status = (
        "approved" if approval >= 80
        else "qualified_approval" if approval >= 50
        else "rejected"
    )

    return {
        "approval_percentage": approval,
        "status": status,
        "esg_linked_pct": esg_pct,
        "message": {
            "approved": f"✅ Say-on-Pay APPROVED ({approval:.0f}%). Strong governance signal.",
            "qualified_approval": f"⚠️ Say-on-Pay narrowly approved ({approval:.0f}%). Investors signalling discontent.",
            "rejected": f"🚨 Say-on-Pay REJECTED ({approval:.0f}%). Board must revise compensation policy.",
        }[status],
    }


# ═══════════════════════════════════════════════════════════════
#  BOARD EFFECTIVENESS
# ═══════════════════════════════════════════════════════════════

def calc_board_effectiveness(board_state: dict) -> tuple[float, dict]:
    """
    Board effectiveness composite score (0-100).
    Based on UK Corporate Governance Code evaluation criteria.
    """
    directors = board_state["directors"]
    n = len(directors)

    # 1. Independence ratio (target: ≥ 50%)
    independent = sum(1 for d in directors if d["independence"])
    ind_ratio = independent / n if n > 0 else 0
    ind_score = min(25.0, ind_ratio * 50.0)  # Max 25 points

    # 2. Tenure balance (mix of fresh and experienced)
    avg_tenure = sum(d["tenure_years"] for d in directors) / n if n > 0 else 0
    tenure_score = 25.0 - abs(avg_tenure - 5) * 3  # Optimal at ~5 years
    tenure_score = max(0, min(25.0, tenure_score))

    # 3. Expertise diversity
    all_expertise = set()
    for d in directors:
        all_expertise.update(d.get("expertise", []))
    needed = {"sustainability", "finance", "governance", "technology", "operations", "legal"}
    coverage = len(all_expertise & needed) / len(needed)
    expertise_score = coverage * 25.0

    # 4. ESG committee effectiveness
    committee_scores = {
        "binding": 25.0,
        "oversight": 18.0,
        "advisory": 10.0,
        "none": 0.0,
    }
    if not board_state.get("esg_committee_established"):
        committee_score = 0.0
    else:
        mandate = board_state.get("esg_committee_mandate", "advisory")
        committee_score = committee_scores.get(mandate, 0.0)

    total = round(ind_score + tenure_score + expertise_score + committee_score, 1)

    return total, {
        "independence_score": round(ind_score, 1),
        "tenure_score": round(tenure_score, 1),
        "expertise_score": round(expertise_score, 1),
        "committee_score": round(committee_score, 1),
        "total": total,
        "independence_ratio": round(ind_ratio, 3),
        "avg_tenure": round(avg_tenure, 1),
        "expertise_coverage": round(coverage, 3),
    }


def get_resolutions_for_round(round_number: int) -> list[dict]:
    """Return shareholder resolutions available for voting this round."""
    return [r for r in SHAREHOLDER_RESOLUTIONS if r["round_available"] == round_number]


def process_board_tick(
    board_state: dict,
    gs: dict,
    bus: list[dict],
    round_number: int,
) -> tuple[dict, dict]:
    """
    Process board governance for this round.
    Returns (updated_board_state, diagnostics).
    """
    diagnostics: dict[str, Any] = {}

    # Update effectiveness
    effectiveness, eff_diag = calc_board_effectiveness(board_state)
    board_state["board_effectiveness_score"] = effectiveness
    diagnostics["effectiveness"] = eff_diag

    # Update ESG alignment average
    directors = board_state["directors"]
    if directors:
        board_state["avg_esg_alignment"] = round(
            sum(d["esg_alignment"] for d in directors) / len(directors), 3
        )
        board_state["independence_ratio"] = round(
            sum(1 for d in directors if d["independence"]) / len(directors), 3
        )

    # M_R bonus from strong governance
    mr_bonus = 0.0
    if effectiveness >= 80:
        mr_bonus = 0.05
    elif effectiveness >= 60:
        mr_bonus = 0.02
    diagnostics["governance_mr_bonus"] = mr_bonus

    # History
    board_state["governance_history"].append({
        "round": round_number,
        "effectiveness": effectiveness,
        "esg_alignment": board_state["avg_esg_alignment"],
        "independence": board_state["independence_ratio"],
    })

    return board_state, diagnostics
