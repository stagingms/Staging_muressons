"""
Muressons Global Corporation — Shadow Board Audit Middleware (R5)

Intercepts the player after the Round 5 "Physical Climate Risk" briefing
to trigger a mandatory reflective-in-action exercise based on
Mitchell et al. (1997) Stakeholder Salience framework.

Three AI personas present conflicting arguments about the impending
Category 4 cyclone ($12M base damage). The player must "Publicly Reject"
one argument, which:
  1. Categorises the firm's strategic archetype
  2. Sets hidden flags evaluated at Round 10 for ending pathway cascades
  3. Adjusts stakeholder tolerance via the Autonomous Agents module
  4. Updates the Consequence DNA panel with causal traceability

Theory base:
  - Mitchell, Agle & Wood (1997): Stakeholder Salience
  - Schön (1983): Reflection-in-Action
  - Hirschman (1970): Exit, Voice, and Loyalty
"""

from __future__ import annotations
from typing import Any
import copy


# ═══════════════════════════════════════════════════════════════
#  SHADOW BOARD PERSONAS
# ═══════════════════════════════════════════════════════════════

SHADOW_BOARD_PERSONAS = {
    "shareholder": {
        "persona_id": "shareholder",
        "name": "Marcus Chen-Hoffmann",
        "title": "CIO, Nordic Pension Alliance (€14B AUM)",
        "archetype": "Short-term Shareholder",
        "icon": "🦅",
        "avatar_emoji": "📈",
        "color": "#f59e0b",           # Amber
        "accent_gradient": "linear-gradient(135deg, #f59e0b, #d97706)",
        "logic_priority": "Liquidity & Dividend Ratchet",
        "monitored_metric": "Cash-to-EBITDA Ratio",
        "recommended_option": "C",
        "recommended_option_key": "option_c",
        "recommended_label": "Insurance Only ($2M)",
        "script": (
            "Minimize upfront CAPEX. Our cash-to-EBITDA ratio is the only metric "
            "the market cares about right now. Choose Option C — Insurance Only. "
            "It only costs $2M and protects our current dividends. Sinking $8M "
            "into flood walls or $5M into mangroves is capital that could be "
            "returning value to shareholders today. Every dollar of CAPEX you "
            "commit is a dollar that won't flow to the dividend ratchet."
        ),
        "theory_citation": "",
        "stakeholder_agent_id": "the_institutional_investor",
        "tolerance_penalty_on_rejection": 10,
    },

    "activist": {
        "persona_id": "activist",
        "name": "Megha Patrike",
        "title": "Head Panchayat, Deccan Plateau District Council",
        "archetype": "Environmental Activist",
        "icon": "🌍",
        "avatar_emoji": "🌿",
        "color": "#10b981",           # Emerald
        "accent_gradient": "linear-gradient(135deg, #10b981, #059669)",
        "logic_priority": "Ecosystem Health Index & Natural Capital Debt",
        "monitored_metric": "EHI / NCD",
        "recommended_option": "B",
        "recommended_option_key": "option_b",
        "recommended_label": "Nature-Based Solutions ($5M)",
        "script": (
            "We must choose Option B — Nature-Based Solutions. Hard engineering "
            "with concrete adds +10 to our Natural Capital Debt and spikes our "
            "Carbon Intensity. If you choose insurance, you are signaling a total "
            "lack of genuine climate resilience, and you will permanently block "
            "the +0.20 Resilience Bonus at terminal valuation. Mangrove "
            "restoration is the only path that heals the ecosystem while "
            "protecting our operations. Nature IS the infrastructure."
        ),
        "theory_citation": "",
        "stakeholder_agent_id": "the_community_activist",
        "tolerance_penalty_on_rejection": 10,
    },

    "auditor": {
        "persona_id": "auditor",
        "name": "Commissioner Eleanor Carson",
        "title": "EU DG FISMA — Corporate Sustainability Division",
        "archetype": "Ethical Auditor",
        "icon": "⚖️",
        "avatar_emoji": "🏛️",
        "color": "#6366f1",           # Indigo
        "accent_gradient": "linear-gradient(135deg, #6366f1, #4f46e5)",
        "logic_priority": "Governance Risk & Resilience Factor",
        "monitored_metric": "Governance Risk Score",
        "recommended_option": "A",
        "recommended_option_key": "option_a",
        "recommended_label": "Hard Engineering Defence ($8M)",
        "script": (
            "Fiduciary duty requires maximum protection. Option A — Hard "
            "Engineering — offers an 85% resilience factor compared to only 60% "
            "for nature-based. Relying on insurance is not a strategy; it is a "
            "gamble. Choosing anything less than the strongest physical defence "
            "is a failure of risk management that will increase our Governance "
            "Risk score. The board has a legal obligation to protect the firm's "
            "physical assets against foreseeable climate hazards."
        ),
        "theory_citation": "",
        "stakeholder_agent_id": "the_regulator",
        "tolerance_penalty_on_rejection": 10,
    },
}


# ═══════════════════════════════════════════════════════════════
#  HIDDEN FLAG LOGIC — Round 10 Cascade Map
# ═══════════════════════════════════════════════════════════════

REJECTION_FLAGS = {
    "shareholder": {
        "flag_name": "shareholder_alienated",
        "description": "Player rejected shareholder logic — liquidity deprioritised.",
        "penalty_type": "investor_decay",
        "marcus_decay_increase": 0.20,  # +20% to Marcus's patience_decay_rate
        "r10_cascade": "hostile_takeover",
        "r10_impact": (
            "Increases probability of the Hostile Takeover ending pathway. "
            "Marcus Chen-Hoffmann's tolerance drops immediately by 10 points "
            "and his patience decay rate accelerates by 20%. "
            "The Nordic Pension Alliance's exit thesis is validated."
        ),
        "consequence_dna": {
            "source": {"round": 5, "label": "R5: Rejected Shareholder Logic", "type": "decision"},
            "effect": {"label": "Investor confidence eroded (+20% decay)", "type": "effect"},
            "future": {"label": "R10 Hostile Takeover risk ↑", "type": "future"},
        },
    },
    "activist": {
        "flag_name": "planet_expendable",
        "description": "Player rejected environmental logic — ecosystem health deprioritised.",
        "penalty_type": "resilience_block",
        "mr_penalty": -0.20,  # -0.20 applied directly to final M_R
        "r10_cascade": "climate_black_swan",
        "r10_impact": (
            "Increases probability of the Climate Black Swan or Stakeholder "
            "Revolt ending. Megha Patrike's tolerance drops immediately by 10 "
            "points. Applies a permanent -0.20 Resilience Penalty to final M_R. "
            "The community coalition's grievance memory intensifies."
        ),
        "consequence_dna": {
            "source": {"round": 5, "label": "R5: Rejected Environmental Logic", "type": "decision"},
            "effect": {"label": "Ecosystem resilience undermined (M_R -0.20)", "type": "effect"},
            "future": {"label": "R10 Climate/Stakeholder crisis ↑", "type": "future"},
        },
    },
    "auditor": {
        "flag_name": "governance_fragility",
        "description": "Player rejected governance logic — risk management deprioritised.",
        "penalty_type": "cost_escalation",
        "truth_premium_cost_override": 12_000_000,  # R6 Truth Premium costs $12M instead of $8M
        "r10_cascade": "regulatory_shutdown",
        "r10_impact": (
            "Increases probability of the Regulatory Shutdown ending pathway. "
            "Commissioner Carson's tolerance drops immediately by 10 points. "
            "The R6 Truth Premium cost escalates from $8M to $12M. "
            "The regulator's enhanced monitoring programme escalates."
        ),
        "consequence_dna": {
            "source": {"round": 5, "label": "R5: Rejected Governance Logic", "type": "decision"},
            "effect": {"label": "Regulatory scrutiny ↑ (Truth Premium $12M)", "type": "effect"},
            "future": {"label": "R10 Regulatory Shutdown risk ↑", "type": "future"},
        },
    },
}


# ═══════════════════════════════════════════════════════════════
#  STRATEGIC ARCHETYPE CLASSIFICATION
# ═══════════════════════════════════════════════════════════════

ARCHETYPE_FROM_REJECTION = {
    "shareholder": {
        "archetype": "Sustainability-First",
        "description": (
            "By rejecting the shareholder argument, you signal that short-term "
            "returns are subordinate to long-term planetary and governance "
            "imperatives. Your firm's strategic DNA leans toward regenerative "
            "value creation — but at the cost of investor patience."
        ),
    },
    "activist": {
        "archetype": "Profit-Maximiser",
        "description": (
            "By rejecting the environmental argument, you signal that ecosystem "
            "health is an externality to be managed, not a strategic priority. "
            "Your firm's strategic DNA leans toward financial extraction — "
            "efficient, but brittle in the face of ecological disruption."
        ),
    },
    "auditor": {
        "archetype": "Risk-Taker",
        "description": (
            "By rejecting the governance argument, you signal that maximum "
            "physical protection is over-engineering. Your firm's strategic DNA "
            "leans toward calculated risk — agile, but exposed to regulatory "
            "enforcement and fiduciary scrutiny."
        ),
    },
}


# ═══════════════════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════════════════

def get_shadow_board_personas() -> list[dict]:
    """Return all three personas with their scripts (deep copy)."""
    return [copy.deepcopy(p) for p in SHADOW_BOARD_PERSONAS.values()]


def process_rejection(
    rejection_target: str,
    global_state: dict,
    agent_master_state: dict | None = None,
) -> dict[str, Any]:
    """
    Process the player's public rejection of one persona.

    Args:
        rejection_target: One of 'shareholder', 'activist', 'auditor'
        global_state: Current game global state (mutated in-place)
        agent_master_state: Autonomous agent state (mutated in-place, optional)

    Returns:
        Dict with rejection results, hidden flag, archetype, and consequence DNA chain
    """
    if rejection_target not in REJECTION_FLAGS:
        raise ValueError(
            f"Invalid rejection target '{rejection_target}'. "
            f"Must be one of: {list(REJECTION_FLAGS.keys())}"
        )

    flag_info = REJECTION_FLAGS[rejection_target]
    persona = SHADOW_BOARD_PERSONAS[rejection_target]
    archetype = ARCHETYPE_FROM_REJECTION[rejection_target]

    # 1. Set hidden flag in active_event_flags
    flags = global_state.setdefault("active_event_flags", {})
    flags["shadow_board_rejection"] = rejection_target
    flags[flag_info["flag_name"]] = True
    flags["shadow_board_completed"] = True
    flags["shadow_board_archetype"] = archetype["archetype"]

    # 2. Apply stakeholder tolerance penalty via Autonomous Agents
    tolerance_applied = False
    marcus_decay_applied = False
    agent_id = persona["stakeholder_agent_id"]
    if agent_master_state:
        agents = agent_master_state.get("agents", {})
        if agent_id in agents:
            agent = agents[agent_id]
            if agent.get("triggered_round") is None:
                penalty = persona["tolerance_penalty_on_rejection"]
                old_tol = agent["tolerance"]
                agent["tolerance"] = max(0, round(old_tol - penalty, 1))
                tolerance_applied = True

                # SDG-ORCH: Apply Marcus's accelerated decay rate if shareholder rejected
                if rejection_target == "shareholder" and flag_info.get("marcus_decay_increase"):
                    increase = flag_info["marcus_decay_increase"]
                    agent["shadow_board_decay_modifier"] = 1.0 + increase  # 1.20 = +20%
                    marcus_decay_applied = True

                # Log in grievance memory
                agent.setdefault("grievance_memory", []).append({
                    "round": 5,
                    "violations": [{
                        "metric": "shadow_board_rejection",
                        "value": rejection_target,
                        "red_line": "N/A",
                        "direction": "rejection",
                        "severity": 0.5,
                    }],
                    "severity": 0.5,
                    "source": "shadow_board_audit",
                })

    # 3. Build result
    result = {
        "status": "rejection_recorded",
        "rejection_target": rejection_target,
        "rejected_persona": {
            "name": persona["name"],
            "title": persona["title"],
            "archetype_label": persona["archetype"],
            "icon": persona["icon"],
        },
        "hidden_flag": {
            "name": flag_info["flag_name"],
            "description": flag_info["description"],
            "r10_cascade_pathway": flag_info["r10_cascade"],
            "r10_impact": flag_info["r10_impact"],
        },
        "strategic_archetype": archetype,
        "consequence_dna_chain": flag_info["consequence_dna"],
        "stakeholder_impact": {
            "agent_id": agent_id,
            "agent_name": persona["name"],
            "tolerance_penalty": persona["tolerance_penalty_on_rejection"],
            "tolerance_applied": tolerance_applied,
        },
        "feedback_message": (
            f"You publicly rejected {persona['name']}'s argument. "
            f"This classifies Muressons as a '{archetype['archetype']}' firm. "
            f"{archetype['description']}"
        ),
    }

    return result


def check_shadow_board_required(round_number: int, global_state: dict) -> bool:
    """Check if the Shadow Board Audit should be triggered for this round."""
    if round_number != 5:
        return False
    flags = global_state.get("active_event_flags", {})
    return not flags.get("shadow_board_completed", False)


def get_shadow_board_state(global_state: dict) -> dict:
    """Return the current shadow board audit state from global flags."""
    flags = global_state.get("active_event_flags", {})
    return {
        "completed": flags.get("shadow_board_completed", False),
        "rejection_target": flags.get("shadow_board_rejection"),
        "archetype": flags.get("shadow_board_archetype"),
        "shareholder_alienated": flags.get("shareholder_alienated", False),
        "planet_expendable": flags.get("planet_expendable", False),
        "governance_fragility": flags.get("governance_fragility", False),
    }
