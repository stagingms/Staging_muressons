"""
Muressons Global Corporation — Autonomous Stakeholder Agents (SI-2+)
AI-driven agents with tolerance levels, patience counters, memory,
and cascading event triggers that replace static slider satisfaction.

Theory base:
  - Mitchell et al. (1997): Stakeholder Salience (power, legitimacy, urgency)
  - Hirschman (1970): Exit, Voice, and Loyalty
  - Kahneman & Tversky (1979): Loss aversion in stakeholder reactions

Architecture:
  Pure-function module. Each agent tracks:
    1. tolerance_zone: current patience (0-100, starts high)
    2. grievance_memory: list of past-round metric violations
    3. escalation_stage: dormant → watching → agitated → hostile → triggered
    4. cascade_chain: when triggered, which other agents are pulled toward action

  Agents evaluate TRENDS (not just snapshots) — two consecutive bad rounds
  are more dangerous than one terrible round followed by recovery.
"""

from __future__ import annotations
from typing import Any
import math
import random
from flag_utils import collect_all_flags
from rules import rule_on


# ═══════════════════════════════════════════════════════════════
#  AGENT PROFILE DEFINITIONS
# ═══════════════════════════════════════════════════════════════

AGENT_PROFILES = {
    "the_regulator": {
        "name": "Commissioner Carson",
        "title": "EU DG FISMA — Corporate Sustainability Division",
        "icon": "🏛️",
        "avatar_emoji": "👩‍⚖️",
        "personality": "methodical",
        "color": "#6366f1",  # Indigo
        "initial_tolerance": 75,
        "patience_decay_rate": 8,      # loses 8 tolerance per violation round
        "recovery_rate": 3,            # recovers 3 tolerance per clean round
        "escalation_thresholds": {
            "watching":  65,
            "agitated":  45,
            "hostile":   25,
            "triggered": 10,
        },
        "monitored_metrics": [
            {"key": "governance_risk_avg", "direction": "above", "red_line": 55, "weight": 0.4},
            {"key": "group_reputation", "direction": "below", "red_line": 35, "weight": 0.3},
            {"key": "carbon_intensity_avg", "direction": "above", "red_line": 70, "weight": 0.3},
        ],
        "cascade_targets": ["the_journalist", "the_institutional_investor"],
        "cascade_tolerance_hit": 12,
        "stage_dialogue": {
            "dormant": "Commissioner Carson's office confirms routine monitoring status. No concerns at this time.",
            "watching": "'We've placed Muressons on our enhanced monitoring programme,' states Carson. 'We expect proactive remediation.'",
            "agitated": "FORMAL: DG FISMA opens preliminary inquiry into Muressons governance practices. 'We have concerns,' says Carson.",
            "hostile": "URGENT: Commissioner Carson announces Article 8 investigation. 'Persistent deficiencies cannot be tolerated.'",
            "triggered": None,  # triggers cascade event
        },
        "triggered_event": {
            "title": "⚖️ REGULATORY SHUTDOWN ORDER",
            "narrative": (
                "🏛️ Commissioner Carson issues emergency cease-and-desist order. "
                "'Muressons has exhausted every opportunity for voluntary compliance. "
                "We are suspending operations at the Düsseldorf facility pending full review.' "
                "Fine: 4% of annual revenue. Mandatory disclosure regime imposed."
            ),
            "effects": {
                "treasury_pct_hit": -0.04,
                "reputation_delta": -12,
                "governance_risk_delta": -8,  # paradoxically improves via forced reform
                "opex_pct_increase": 0.06,
            },
        },
    },

    "the_gen_z_employee": {
        "name": "Greta Berg",
        "title": "Gen Z Employee Collective — Muressons Workers United",
        "icon": "👩‍💻",
        "avatar_emoji": "✊",
        "personality": "passionate",
        "color": "#ec4899",  # Pink
        "initial_tolerance": 70,
        "patience_decay_rate": 10,     # Gen Z has less patience
        "recovery_rate": 5,            # but recovers faster when treated well
        "escalation_thresholds": {
            "watching":  60,
            "agitated":  40,
            "hostile":   20,
            "triggered": 8,
        },
        "monitored_metrics": [
            {"key": "avg_burnout", "direction": "above", "red_line": 55, "weight": 0.35},
            {"key": "group_reputation", "direction": "below", "red_line": 40, "weight": 0.25},
            {"key": "governance_risk_avg", "direction": "above", "red_line": 50, "weight": 0.20},
            {"key": "workforce_readiness", "direction": "below", "red_line": 40, "weight": 0.20},
        ],
        "cascade_targets": ["the_journalist", "the_community_activist"],
        "cascade_tolerance_hit": 15,
        "stage_dialogue": {
            "dormant": "Employee engagement scores stable. Greta's internal blog post praises new sustainability initiatives.",
            "watching": "'We're watching management closely,' Greta posts on the internal forum. 'Actions, not mission statements.'",
            "agitated": "Greta's open letter to the CEO goes viral on LinkedIn: 'We didn't sign up to work for a company that burns out its people and the planet.'",
            "hostile": "#MuressonsWalkout trends on social media. Greta announces work-to-rule action across 3 facilities.",
            "triggered": None,
        },
        "triggered_event": {
            "title": "✊ COORDINATED STRIKE ACTION",
            "narrative": (
                "👩‍💻 Greta Berg announces full strike across all facilities. "
                "'We gave management every chance. They chose profits over people. "
                "We choose solidarity.' 78% of workforce participates. "
                "Operations halt for the period. Agency staff costs surge 15%."
            ),
            "effects": {
                "burnout_delta": 20,
                "opex_pct_increase": 0.15,
                "reputation_delta": -8,
                "social_license_delta": -12,
            },
        },
    },

    "the_institutional_investor": {
        "name": "Jay Buffet",
        "title": "CIO, Nordic Pension Alliance (€14B AUM)",
        "icon": "🦅",
        "avatar_emoji": "📉",
        "personality": "analytical",
        "color": "#f59e0b",  # Amber
        "initial_tolerance": 80,
        "patience_decay_rate": 6,      # Patient, but once decided, devastating
        "recovery_rate": 2,            # Very slow to forgive
        "escalation_thresholds": {
            "watching":  70,
            "agitated":  50,
            "hostile":   30,
            "triggered": 12,
        },
        "monitored_metrics": [
            {"key": "treasury_velocity", "direction": "below", "red_line": 0, "weight": 0.30},
            {"key": "group_reputation", "direction": "below", "red_line": 40, "weight": 0.25},
            {"key": "carbon_intensity_avg", "direction": "above", "red_line": 65, "weight": 0.25},
            {"key": "governance_risk_avg", "direction": "above", "red_line": 45, "weight": 0.20},
        ],
        "cascade_targets": ["the_regulator", "the_journalist"],
        "cascade_tolerance_hit": 10,
        "stage_dialogue": {
            "dormant": "Nordic Pension Alliance reaffirms Muressons position in core ESG portfolio. 'Management is delivering.'",
            "watching": "'We've placed Muressons on our ESG watchlist,' Buffet informs the board. 'We expect a credible improvement plan within 90 days.'",
            "agitated": "Nordic Pension Alliance downgrades Muressons to 'underweight'. Buffet's public letter: 'We are deeply concerned about trajectory.'",
            "hostile": "BREAKING: Nordic Pension Alliance begins systematic position reduction. 'We can no longer justify this allocation to our beneficiaries.'",
            "triggered": None,
        },
        "triggered_event": {
            "title": "📉 INSTITUTIONAL DIVESTMENT FIRE SALE",
            "narrative": (
                "🦅 Jay Buffet triggers full divestment protocol. "
                "'Nordic Pension Alliance is exiting Muressons entirely. "
                "We have a fiduciary duty that this management team has made impossible to fulfil.' "
                "€340M in shares dumped. Share price crashes 8%. "
                "Three other institutional investors follow within 48 hours."
            ),
            "effects": {
                "treasury_pct_hit": -0.08,
                "reputation_delta": -15,
                "cost_of_capital_delta": 0.02,
            },
        },
    },

    "the_community_activist": {
        "name": "Megha Patrike",
        "title": "Head Deccan Plateau Council",
        "icon": "🏘️",
        "avatar_emoji": "🌍",
        "personality": "persistent",
        "color": "#10b981",  # Emerald
        "initial_tolerance": 65,
        "patience_decay_rate": 7,
        "recovery_rate": 4,
        "escalation_thresholds": {
            "watching":  55,
            "agitated":  35,
            "hostile":   18,
            "triggered": 6,
        },
        "monitored_metrics": [
            {"key": "avg_slo", "direction": "below", "red_line": 45, "weight": 0.40},
            {"key": "water_stress", "direction": "above", "red_line": 0.5, "weight": 0.30},
            {"key": "avg_ncd", "direction": "above", "red_line": 200000, "weight": 0.30},
        ],
        "cascade_targets": ["the_journalist", "the_gen_z_employee"],
        "cascade_tolerance_hit": 10,
        "stage_dialogue": {
            "dormant": "Megha Patrike invites Muressons leadership to the annual harvest festival. 'We are grateful neighbours.'",
            "watching": "'We are watching,' Patrike says at the panchayat. 'The promises about water recycling have not materialised.'",
            "agitated": "200 villagers block the road to the Pune facility. Patrike: 'Our water, our land, our lives!'",
            "hostile": "International NGO adopts the community's case. Legal injunction filed against facility operations.",
            "triggered": None,
        },
        "triggered_event": {
            "title": "🌍 COMMUNITY BLOCKADE & COURT INJUNCTION",
            "narrative": (
                "🏘️ Megha Patrike and 500 community members blockade all facility access. "
                "High Court grants emergency injunction halting Pune operations. "
                "'Muressons has destroyed our water table, poisoned our soil, "
                "and broken every promise. The courts will decide.' "
                "Operations suspended. Social license collapses."
            ),
            "effects": {
                "social_license_delta": -20,
                "reputation_delta": -10,
                "opex_pct_increase": 0.10,
                "treasury_flat_hit": -3_000_000,
            },
        },
    },

    "the_journalist": {
        "name": "Beth Colbert",
        "title": "Senior Investigative Reporter, Deccan Herald Business",
        "icon": "📰",
        "avatar_emoji": "🔍",
        "personality": "tenacious",
        "color": "#8b5cf6",  # Violet
        "initial_tolerance": 72,
        "patience_decay_rate": 9,
        "recovery_rate": 4,
        "escalation_thresholds": {
            "watching":  62,
            "agitated":  42,
            "hostile":   22,
            "triggered": 8,
        },
        "monitored_metrics": [
            {"key": "group_reputation", "direction": "below", "red_line": 42, "weight": 0.35},
            {"key": "governance_risk_avg", "direction": "above", "red_line": 48, "weight": 0.35},
            {"key": "carbon_intensity_avg", "direction": "above", "red_line": 60, "weight": 0.30},
        ],
        "cascade_targets": ["the_regulator", "the_institutional_investor", "the_community_activist"],
        "cascade_tolerance_hit": 8,
        "stage_dialogue": {
            "dormant": "Beth Colbert publishes a balanced feature: 'Muressons: A Corporate Turnaround Story.'",
            "watching": "Colbert begins a series: 'Inside Muressons — Part 1: The Promises.' Sources say he's requesting internal documents.",
            "agitated": "INVESTIGATION: 'The Green Facade?' by Beth Colbert trends on social media. 12,000 engagements in 24 hours.",
            "hostile": "Colbert's 3-part exposé 'Muressons Unmasked' is syndicated across 5 national outlets. Reach: 4.5M impressions.",
            "triggered": None,
        },
        "triggered_event": {
            "title": "📰 VIRAL EXPOSÉ — CORPORATE CREDIBILITY DESTROYED",
            "narrative": (
                "📰 Beth Colbert's Pulitzer-nominated investigation 'Muressons: "
                "The Sustainability Mirage' airs as a documentary special. "
                "Leaked internal documents reveal systematic metric manipulation. "
                "Share price crashes. Consumer boycott organised. "
                "Board calls emergency session. '#MuressonsExposed' trends #1 globally."
            ),
            "effects": {
                "reputation_delta": -20,
                "treasury_pct_hit": -0.03,
                "social_license_delta": -10,
                "governance_risk_delta": 10,
            },
        },
    },
}


# ═══════════════════════════════════════════════════════════════
#  INTER-AGENT INTERFERENCE PAIRS
#  When BOTH agents in a pair are at 'agitated' or higher,
#  they multiply each other's tolerance decay rate.
#  Theory: Journalist coverage triggers regulatory probes,
#          regulatory probes generate more news stories.
# ═══════════════════════════════════════════════════════════════

_ESCALATED_STAGES = frozenset({"agitated", "hostile", "triggered"})

INTERFERENCE_PAIRS = [
    {
        "agents": ("the_journalist", "the_regulator"),
        "decay_multiplier": 1.4,           # 40% faster decay when both agitated+
        "min_stage": "agitated",            # activation threshold
        "narrative": (
            "📡 MEDIA-REGULATOR FEEDBACK LOOP: Beth Colbert's investigative reporting "
            "has prompted Commissioner Carson to accelerate her inquiry. Carson's "
            "subpoena requests are, in turn, generating fresh headline material for "
            "Colbert. Both agents' tolerance is decaying {pct}% faster."
        ),
        "theory": "Herman & Chomsky (1988) Manufacturing Consent — media and "
                  "regulatory agendas co-amplify through institutional feedback.",
    },
    {
        "agents": ("the_gen_z_employee", "the_community_activist"),
        "decay_multiplier": 1.25,           # 25% faster decay
        "min_stage": "agitated",
        "narrative": (
            "✊🏘️ SOLIDARITY AMPLIFICATION: Greta Berg's employee collective and "
            "Megha Patrike's community coalition are coordinating. Internal "
            "walkout threats are reinforcing external protests. Both agents' "
            "tolerance is decaying {pct}% faster."
        ),
        "theory": "Tarrow (1998) Power in Movement — contentious politics "
                  "accelerates when internal and external grievances converge.",
    },
    {
        "agents": ("the_institutional_investor", "the_regulator"),
        "decay_multiplier": 1.3,            # 30% faster decay
        "min_stage": "hostile",             # only at hostile+ (higher bar)
        "narrative": (
            "📉🏛️ REGULATORY-MARKET VORTEX: Jay Buffet's divestment "
            "signals are accelerating Commissioner Carson's enforcement timeline. "
            "Regulatory action is, in turn, validating the Investor's exit thesis. "
            "Both agents' tolerance is decaying {pct}% faster."
        ),
        "theory": "Admati & Hellwig (2013) The Bankers' New Clothes — "
                  "market discipline and regulatory discipline are complements.",
    },
]


def _compute_interference_multipliers(
    agents: dict[str, dict],
) -> dict[str, float]:
    """
    Pre-pass: for each agent, compute a combined decay multiplier
    from all active interference pairs it belongs to.
    Returns {agent_id: combined_multiplier} (1.0 = no interference).
    """
    multipliers: dict[str, float] = {}
    active_pairs: list[dict] = []

    for pair in INTERFERENCE_PAIRS:
        a_id, b_id = pair["agents"]
        a_state = agents.get(a_id, {})
        b_state = agents.get(b_id, {})

        # Skip if either is already triggered (permanently) or not yet at min_stage
        if a_state.get("triggered_round") is not None:
            continue
        if b_state.get("triggered_round") is not None:
            continue

        a_stage = a_state.get("escalation_stage", "dormant")
        b_stage = b_state.get("escalation_stage", "dormant")

        min_stage = pair.get("min_stage", "agitated")
        required = _ESCALATED_STAGES
        if min_stage == "hostile":
            required = frozenset({"hostile", "triggered"})

        if a_stage in required and b_stage in required:
            m = pair["decay_multiplier"]
            multipliers[a_id] = multipliers.get(a_id, 1.0) * m
            multipliers[b_id] = multipliers.get(b_id, 1.0) * m
            active_pairs.append(pair)

    return multipliers, active_pairs


# ═══════════════════════════════════════════════════════════════
#  STATE MANAGEMENT
# ═══════════════════════════════════════════════════════════════

def create_initial_agent_state() -> dict[str, Any]:
    """Create initial autonomous agent states for a new session."""
    agents = {}
    for agent_id, profile in AGENT_PROFILES.items():
        agents[agent_id] = {
            "tolerance": profile["initial_tolerance"],
            "escalation_stage": "dormant",
            "grievance_memory": [],      # list of {round, violations}
            "patience_counter": 0,       # consecutive violation rounds
            "recovery_counter": 0,       # consecutive clean rounds
            "cascade_received": False,   # hit by another agent's cascade
            "triggered_round": None,     # round the agent triggered (None = not yet)
            "trend": "stable",           # improving | stable | deteriorating
        }
    return {
        "agents": agents,
        "cascade_log": [],
        "total_triggers": 0,
        "events_this_round": [],
    }


# ═══════════════════════════════════════════════════════════════
#  METRIC COMPUTATION
# ═══════════════════════════════════════════════════════════════

def _compute_agent_metrics(gs: dict, bus: list[dict]) -> dict[str, float]:
    """Extract all metrics needed by agents from game state."""
    n = max(len(bus), 1)
    avg_gov = sum(bu.get("governance_risk_score", 20) for bu in bus) / n
    avg_ci = sum(bu.get("carbon_intensity", 50) for bu in bus) / n
    avg_slo = sum(bu.get("social_license_score", 50) for bu in bus) / n
    avg_burnout = sum(bu.get("staff_burnout_index", 0) for bu in bus) / n
    avg_ncd = sum(bu.get("natural_capital_debt", 0) for bu in bus) / n
    treasury = gs.get("corporate_treasury", 0)
    ebitda = sum(bu.get("revenue_base", 0) - bu.get("opex_base", 0) for bu in bus)
    bio = gs.get("biodiversity_state", {})
    water_stress = bio.get("water_stress_index", 0.4)
    readiness = gs.get("workforce_readiness", 50)

    return {
        "governance_risk_avg": avg_gov,
        "carbon_intensity_avg": avg_ci,
        "group_reputation": gs.get("group_reputation", 50),
        "avg_slo": avg_slo,
        "avg_burnout": avg_burnout,
        "avg_ncd": avg_ncd,
        "treasury_velocity": ebitda,
        "water_stress": water_stress,
        "workforce_readiness": readiness,
    }


def _check_violations(
    profile: dict, metrics: dict
) -> tuple[list[dict], float]:
    """Check which red lines an agent's monitored metrics cross."""
    violations = []
    violation_severity = 0.0

    for m in profile["monitored_metrics"]:
        val = metrics.get(m["key"], 0)
        red_line = m["red_line"]
        direction = m["direction"]
        weight = m["weight"]

        breached = False
        overshoot = 0.0
        if direction == "above" and val > red_line:
            breached = True
            overshoot = (val - red_line) / max(red_line, 1)
        elif direction == "below" and val < red_line:
            breached = True
            overshoot = (red_line - val) / max(red_line, 1)

        if breached:
            sev = min(1.0, overshoot) * weight
            violations.append({
                "metric": m["key"],
                "value": round(val, 2),
                "red_line": red_line,
                "direction": direction,
                "severity": round(sev, 3),
            })
            violation_severity += sev

    return violations, round(violation_severity, 3)


# ═══════════════════════════════════════════════════════════════
#  AGENT TICK — CORE EVALUATION LOOP
# ═══════════════════════════════════════════════════════════════

def _get_stage(tolerance: float, thresholds: dict) -> str:
    """Determine escalation stage from tolerance level."""
    if tolerance <= thresholds["triggered"]:
        return "triggered"
    elif tolerance <= thresholds["hostile"]:
        return "hostile"
    elif tolerance <= thresholds["agitated"]:
        return "agitated"
    elif tolerance <= thresholds["watching"]:
        return "watching"
    return "dormant"


def process_agent_tick(
    agent_master_state: dict,
    gs: dict,
    bus: list[dict],
    events: dict,
    round_number: int,
    memory_enabled: bool = False,
    slo_feedback_enabled: bool = False,
    engagement_enabled: bool = False,
    coalitions_enabled: bool = False,
    uncertainty_enabled: bool = False,
) -> tuple[dict, dict]:
    """
    Process all autonomous stakeholder agents for this round.
    Returns (updated_state, diagnostics).

    Optional flags (SPEC F1–F5) layer the stakeholder-realism waves onto all five
    agents: betrayal scars (F1), continuous per-stage SLO feedback (F2), the
    promise ledger (F5), coalition amplification (F3), and seeded threshold
    jitter + patience-forced escalation (F4). Each defaults False, so with the
    toggles off the base engine behaves exactly as before.
    """
    metrics = _compute_agent_metrics(gs, bus)
    _betrayal = detect_betrayal(events) if memory_enabled else False
    _scar_c = _scar_consts() if memory_enabled else None
    # F4 uncertainty: seeded per-cohort threshold jitter + patience clock.
    _seed = gs.get("active_event_flags", {}).get("stochastic_seed")
    _jitter = _patience = None
    if uncertainty_enabled:
        from config import THRESHOLD_JITTER, PATIENCE_LIMIT
        _jitter, _patience = THRESHOLD_JITTER, PATIENCE_LIMIT
    diagnostics: dict[str, Any] = {
        "agent_actions": [], "cascades_fired": [], "interference_active": [],
    }
    triggered_agents = []

    # Phase 0: Compute inter-agent interference multipliers
    interference_mults, active_pairs = _compute_interference_multipliers(
        agent_master_state["agents"]
    )
    for pair in active_pairs:
        a_id, b_id = pair["agents"]
        pct = round((pair["decay_multiplier"] - 1) * 100)
        diagnostics["interference_active"].append({
            "agents": [a_id, b_id],
            "multiplier": pair["decay_multiplier"],
            "narrative": pair["narrative"].format(pct=pct),
            "theory": pair["theory"],
        })

    # Phase 1: Evaluate each agent independently
    for agent_id, agent_state in agent_master_state["agents"].items():
        profile = AGENT_PROFILES[agent_id]

        # Skip if already triggered permanently
        if agent_state.get("triggered_round") is not None:
            diagnostics["agent_actions"].append({
                "agent_id": agent_id,
                "name": profile["name"],
                "title": profile["title"],
                "icon": profile["icon"],
                "avatar_emoji": profile["avatar_emoji"],
                "color": profile["color"],
                "tolerance": agent_state["tolerance"],
                "tolerance_delta": 0,
                "stage": "triggered",
                "previous_stage": "triggered",
                "stage_changed": False,
                "message": f"{profile['name']} already triggered in R{agent_state['triggered_round']}.",
                "violations": [],
                "violation_severity": 0,
                "patience_counter": agent_state.get("patience_counter", 0),
                "recovery_counter": 0,
                "trend": "n/a",
                "triggered_event": None,
            })
            continue

        violations, severity = _check_violations(profile, metrics)

        # Update tolerance based on violations
        old_tolerance = agent_state["tolerance"]
        if violations:
            # Severity-weighted decay: more violations = faster decay
            base_decay = profile["patience_decay_rate"] * (1 + severity)
            # Apply inter-agent interference multiplier (1.0 if none active)
            interference_mult = interference_mults.get(agent_id, 1.0)
            # SDG-ORCH: Apply shadow board decay modifier (e.g. +20% for shareholder rejection)
            sb_modifier = agent_state.get("shadow_board_decay_modifier", 1.0)
            decay = base_decay * interference_mult * sb_modifier
            agent_state["tolerance"] = max(0, round(old_tolerance - decay, 1))
            agent_state["patience_counter"] += 1
            agent_state["recovery_counter"] = 0
            agent_state["grievance_memory"].append({
                "round": round_number,
                "violations": violations,
                "severity": severity,
            })
            # Cap memory to last 5 rounds
            if len(agent_state["grievance_memory"]) > 5:
                agent_state["grievance_memory"] = agent_state["grievance_memory"][-5:]
        else:
            # Clean round: recover tolerance
            recovery = profile["recovery_rate"]
            # Bonus recovery if 2+ consecutive clean rounds
            if agent_state["recovery_counter"] >= 2:
                recovery *= 1.5
            agent_state["tolerance"] = min(
                profile["initial_tolerance"],
                round(old_tolerance + recovery, 1)
            )
            agent_state["recovery_counter"] += 1
            agent_state["patience_counter"] = max(0, agent_state["patience_counter"] - 1)

        # Apply cascade penalty from other agents
        if agent_state.get("cascade_received"):
            agent_state["tolerance"] = max(0, agent_state["tolerance"] - 5)
            agent_state["cascade_received"] = False

        # SPEC F1 — a betrayal cuts tolerance and caps recovery for a few rounds.
        if memory_enabled:
            apply_agent_betrayal_scar(agent_state, _betrayal, round_number, **_scar_c)

        # Determine trend
        if len(agent_state["grievance_memory"]) >= 2:
            recent_sev = agent_state["grievance_memory"][-1].get("severity", 0)
            prev_sev = agent_state["grievance_memory"][-2].get("severity", 0)
            if recent_sev > prev_sev:
                agent_state["trend"] = "deteriorating"
            elif recent_sev < prev_sev:
                agent_state["trend"] = "improving"
            else:
                agent_state["trend"] = "stable"
        elif not violations:
            agent_state["trend"] = "improving"
        else:
            agent_state["trend"] = "stable"

        # Determine stage (thresholds optionally jittered per cohort — F4)
        _thr = profile["escalation_thresholds"]
        if uncertainty_enabled:
            if "threshold_offsets" not in agent_state:
                agent_state["threshold_offsets"] = _draw_agent_offsets(agent_id, _seed, _jitter)
            _thr = _jittered_thresholds(_thr, agent_state["threshold_offsets"])
        new_stage = _get_stage(agent_state["tolerance"], _thr)
        # F4 patience clock: held at a wary stage too long → force escalation.
        if uncertainty_enabled and _patience and new_stage in ("watching", "agitated", "hostile"):
            if new_stage == agent_state.get("_last_stage"):
                agent_state["rounds_at_stage"] = agent_state.get("rounds_at_stage", 0) + 1
            else:
                agent_state["rounds_at_stage"] = 1
            if agent_state["rounds_at_stage"] >= _patience:
                agent_state["tolerance"] = max(0.0, round(
                    agent_state["tolerance"] - profile["patience_decay_rate"], 1))
                new_stage = _get_stage(agent_state["tolerance"], _thr)
                agent_state["rounds_at_stage"] = 1
        agent_state["_last_stage"] = new_stage
        old_stage = agent_state["escalation_stage"]
        agent_state["escalation_stage"] = new_stage

        # Get dialogue
        dialogue = profile["stage_dialogue"].get(new_stage, "")
        if new_stage == "triggered":
            agent_state["triggered_round"] = round_number
            triggered_agents.append(agent_id)
            dialogue = profile["triggered_event"]["narrative"]

        diagnostics["agent_actions"].append({
            "agent_id": agent_id,
            "name": profile["name"],
            "title": profile["title"],
            "icon": profile["icon"],
            "avatar_emoji": profile["avatar_emoji"],
            "color": profile["color"],
            "tolerance": round(agent_state["tolerance"], 1),
            "tolerance_delta": round(agent_state["tolerance"] - old_tolerance, 1),
            "stage": new_stage,
            "previous_stage": old_stage,
            "stage_changed": new_stage != old_stage,
            "message": dialogue,
            "violations": violations,
            "violation_severity": severity,
            "patience_counter": agent_state["patience_counter"],
            "recovery_counter": agent_state["recovery_counter"],
            "trend": agent_state["trend"],
            "triggered_event": (
                profile["triggered_event"] if new_stage == "triggered" else None
            ),
        })

    # Phase 2: Process cascading effects from triggered agents
    for triggered_id in triggered_agents:
        profile = AGENT_PROFILES[triggered_id]
        cascade_hit = profile.get("cascade_tolerance_hit", 10)

        for target_id in profile.get("cascade_targets", []):
            target_state = agent_master_state["agents"].get(target_id)
            if not target_state or target_state.get("triggered_round") is not None:
                continue
            target_state["cascade_received"] = True
            target_state["tolerance"] = max(
                0, round(target_state["tolerance"] - cascade_hit, 1)
            )

            cascade_event = {
                "source": triggered_id,
                "target": target_id,
                "tolerance_hit": cascade_hit,
                "round": round_number,
                "message": (
                    f"{AGENT_PROFILES[triggered_id]['name']}'s action cascades to "
                    f"{AGENT_PROFILES[target_id]['name']}: tolerance drops by {cascade_hit}."
                ),
            }
            diagnostics["cascades_fired"].append(cascade_event)
            agent_master_state["cascade_log"].append(cascade_event)

    # Phase 3: Apply triggered event effects to game state
    for triggered_id in triggered_agents:
        profile = AGENT_PROFILES[triggered_id]
        te = profile["triggered_event"]
        effects = te["effects"]

        # Treasury percentage hit
        if effects.get("treasury_pct_hit"):
            hit = round(
                gs.get("corporate_treasury", 0) * abs(effects["treasury_pct_hit"]), 2
            )
            gs["corporate_treasury"] = round(
                gs.get("corporate_treasury", 0) - hit, 2
            )
            diagnostics[f"agent_treasury_hit_{triggered_id}"] = hit

        # Treasury flat hit
        if effects.get("treasury_flat_hit"):
            gs["corporate_treasury"] = round(
                gs.get("corporate_treasury", 0) + effects["treasury_flat_hit"], 2
            )

        # Reputation
        if effects.get("reputation_delta"):
            gs["group_reputation"] = max(0, min(100, round(
                gs.get("group_reputation", 50) + effects["reputation_delta"], 2
            )))

        # Cost of capital
        if effects.get("cost_of_capital_delta"):
            gs["cost_of_capital"] = round(
                gs.get("cost_of_capital", 0.05) + effects["cost_of_capital_delta"], 4
            )

        # BU-level effects
        for bu in bus:
            if effects.get("social_license_delta"):
                bu["social_license_score"] = max(0, min(100, round(
                    bu.get("social_license_score", 50) + effects["social_license_delta"], 2
                )))
            if effects.get("burnout_delta"):
                bu["staff_burnout_index"] = max(0, min(100, round(
                    bu.get("staff_burnout_index", 0) + effects["burnout_delta"], 2
                )))
            if effects.get("opex_pct_increase"):
                bu["opex_base"] = round(
                    bu["opex_base"] * (1 + effects["opex_pct_increase"]), 2
                )
            if effects.get("governance_risk_delta"):
                bu["governance_risk_score"] = max(0, min(100, round(
                    bu.get("governance_risk_score", 20) + effects["governance_risk_delta"], 2
                )))

        agent_master_state["total_triggers"] += 1

        # Surface as custom black swan for the crisis feed
        events.setdefault("custom_black_swans", []).append({
            "title": te["title"],
            "narrative": te["narrative"],
            "icon": profile["icon"],
            "severity": "critical",
        })

    # ── SPEC F5 — promises: resolve any that mature this round, then apply the
    # player's engagement action toward one agent (if it targets an agent).
    # Negotiation-room deals (source="negotiation") ride the SAME ledger and
    # MUST be judged even when the F5 engagement toggle is off — a negotiated
    # promise that silently never comes due would be a free tolerance pump. ──
    _has_nego_promises = any(
        p.get("source") == "negotiation" and p.get("state") == "open"
        for p in agent_master_state.get("promises", [])
    )
    if engagement_enabled or _has_nego_promises:
        try:
            _res = resolve_agent_promises(agent_master_state, gs, bus, round_number)
            if _res:
                diagnostics["promise_resolutions"] = _res
            # Engagement ACTIONS stay strictly behind the F5 toggle — only the
            # ledger resolution above is shared with negotiation rooms.
            if engagement_enabled:
                _act = events.get("engagement_action")
                _tgt = (_act or {}).get("npc_id") or (_act or {}).get("agent_id")
                if _act and _tgt in agent_master_state.get("agents", {}):
                    diagnostics["engagement_action_result"] = apply_agent_engagement(
                        agent_master_state, gs, _act, round_number)
        except Exception as exc:
            print(f"[WARN] Agent engagement (F5) failed: {exc}")

    # ── SPEC F3 — coalitions: ≥2 hostile agents combine; the pressure amplifies
    # the continuous feedback below and embolden's the members (extra decay). ──
    _coalition_pressure = 0.0
    if coalitions_enabled:
        try:
            from config import CONTAGION_SAT_NUDGE
            _coalition_pressure, _members = evaluate_agent_coalition(agent_master_state)
            agent_master_state["coalition_pressure"] = _coalition_pressure
            if _coalition_pressure > 0:
                diagnostics["coalition"] = {"pressure": _coalition_pressure, "members": _members}
                for m in _members:
                    st = agent_master_state["agents"][m]
                    st["tolerance"] = max(0.0, round(st["tolerance"] - CONTAGION_SAT_NUDGE * _coalition_pressure, 1))
        except Exception as exc:
            print(f"[WARN] Agent coalition (F3) failed: {exc}")

    # ── SPEC F2 — continuous per-stage SLO feedback from the five agents,
    # amplified by any coalition (F3). ──
    if slo_feedback_enabled:
        try:
            from config import STAKEHOLDER_SLO_COUPLING, COALITION_F2_GAIN
            _coupling = STAKEHOLDER_SLO_COUPLING * (1.0 + _coalition_pressure * COALITION_F2_GAIN)
            _fb = apply_agent_slo_feedback(agent_master_state, bus, round_number, _coupling)
            if _fb:
                diagnostics["agent_slo_feedback"] = _fb
        except Exception as exc:
            print(f"[WARN] Agent SLO feedback (F2) failed: {exc}")

    agent_master_state["events_this_round"] = diagnostics["agent_actions"]
    return agent_master_state, diagnostics


def get_agent_summary(agent_master_state: dict) -> list[dict]:
    """Return a frontend-friendly summary of all agent states."""
    summary = []
    for agent_id, agent_state in agent_master_state.get("agents", {}).items():
        profile = AGENT_PROFILES.get(agent_id, {})
        d, l = _agent_demand_leverage(agent_id, agent_state)  # F6 intent (read-only, additive)
        summary.append({
            "agent_id": agent_id,
            "name": profile.get("name", agent_id),
            "title": profile.get("title", ""),
            "icon": profile.get("icon", "•"),
            "avatar_emoji": profile.get("avatar_emoji", ""),
            "color": profile.get("color", "#888"),
            "tolerance": agent_state.get("tolerance", 50),
            "max_tolerance": profile.get("initial_tolerance", 100),
            "stage": agent_state.get("escalation_stage", "dormant"),
            "trend": agent_state.get("trend", "stable"),
            "patience_counter": agent_state.get("patience_counter", 0),
            "triggered_round": agent_state.get("triggered_round"),
            "thresholds": profile.get("escalation_thresholds", {}),
            "demand": d,            # SPEC F6 — plain-language "what they want"
            "leverage": l,          # SPEC F6 — how much they can hurt you
        })
    return summary


# ═══════════════════════════════════════════════════════════════
#  STAKEHOLDER-REALISM WAVES ON THE LIVE 5-AGENT ENGINE (SPEC F1/F2/F5/F6)
#  Every function below is a no-op unless its toggle is passed in, so the
#  base engine behaviour is unchanged when the waves are off.
# ═══════════════════════════════════════════════════════════════

_BETRAYAL_FLAGS = frozenset({
    "deny_and_deflect", "greenwash_risk", "greenwash_detected", "materiality_ignored",
    "greenwashing_scandal", "greenwashing_detected",   # SOC-4 (audit 2026-09-04, WP-24)
})

# Per escalation stage, a small per-round SLO nudge to the BUs an agent watches
# (F2). Cooperative stages rebuild licence; hostile ones erode it. Weaker than a
# trigger event (which is the discrete cliff).
_STAGE_SLO_PRESSURE = {
    "dormant": 1.0, "watching": 0.0, "agitated": -2.0, "hostile": -3.5, "triggered": 0.0,
}

# What each agent primarily wants, keyed by the monitored metric (F6 single
# source of truth so the front-end never re-implements the phrasing).
_METRIC_DEMAND = {
    "governance_risk_avg": "wants tighter governance and disclosure",
    "group_reputation": "wants the reputation risk addressed",
    "carbon_intensity_avg": "wants faster decarbonisation",
    "avg_burnout": "wants workloads and wellbeing fixed",
    "workforce_readiness": "wants investment in people and skills",
    "treasury_velocity": "wants a credible path back to cash generation",
    "avg_slo": "wants the community licence restored",
    "water_stress": "wants water stewardship in the basin",
}

# Leverage label per agent — how hard they can hit you (design-authored).
_AGENT_LEVERAGE = {
    "the_regulator": "very high power and legitimacy — can fine and compel disclosure",
    "the_gen_z_employee": "high urgency — can strike and go viral",
    "the_institutional_investor": "very high power — can divest and move the share price",
    "the_community_activist": "high legitimacy, lower power — can protest and litigate",
    "the_journalist": "the amplifier — turns every other grievance into a headline",
}


def detect_betrayal(events: dict | None) -> bool:
    if not events:
        return False
    active = {k for k, v in events.items() if v is True}
    # Shape C, and the SECOND copy of it: this function is duplicated verbatim in
    # npc_stakeholders.py:50 and autonomous_agents.py:880, and so is
    # _BETRAYAL_FLAGS. `events["flags_set"]` has no writer anywhere in the tick —
    # the option layer writes r{N}_flags (round_logic.py:3770) — so the only
    # betrayal flags this has ever detected are the ones the engine happens to
    # write as top-level booleans. deny_and_deflect, the R4 option flag this list
    # was built around, is not one of them.
    # tests/test_flag_rule_switches.py asserts the two copies still agree.
    if rule_on(events, "npc_betrayal_reads_option_flags"):
        active |= set(collect_all_flags(events))
    else:
        active |= {str(x) for x in (events.get("flags_set") or [])}
    return bool(active & _BETRAYAL_FLAGS)


def _scar_consts() -> dict:
    from config import TRUST_SCAR_IMMEDIATE, TRUST_SCAR_DURATION, TRUST_SCAR_CEILING
    return {"scar_immediate": TRUST_SCAR_IMMEDIATE, "scar_duration": TRUST_SCAR_DURATION,
            "scar_ceiling": TRUST_SCAR_CEILING}


def _agent_bus(agent_id: str, bus: list[dict]) -> list[dict]:
    """BUs an agent's continuous SLO pressure lands on."""
    if agent_id == "the_community_activist":
        water = [b for b in bus if b.get("water_dependency", 0) >= 40]
        return water or bus
    return bus


def _agent_demand_leverage(agent_id: str, agent_state: dict) -> tuple[str, str]:
    """F6 — the agent's top current demand (worst recent violation) and leverage."""
    demand = "broadly satisfied for now"
    mem = agent_state.get("grievance_memory") or []
    if mem:
        vio = mem[-1].get("violations") or []
        if vio:
            worst = max(vio, key=lambda v: v.get("severity", 0))
            demand = _METRIC_DEMAND.get(worst.get("metric", ""),
                                        f"wants {worst.get('metric','the issue').replace('_',' ')} addressed")
    return demand, _AGENT_LEVERAGE.get(agent_id, "moderate influence")


def apply_agent_slo_feedback(agent_master_state: dict, bus: list[dict], round_number: int,
                             coupling: float = 1.0) -> dict:
    """F2 — continuous per-stage SLO pressure from each non-triggered agent.
    Idempotent within a round; clamps [0,100] (tipping cap runs later)."""
    if agent_master_state.get("slo_feedback_round") == round_number:
        return {}
    deltas: dict[str, dict[str, float]] = {}
    for agent_id, st in agent_master_state.get("agents", {}).items():
        if st.get("triggered_round") is not None:
            continue  # their trigger event already moved SLO
        pressure = _STAGE_SLO_PRESSURE.get(st.get("escalation_stage", "dormant"), 0.0) * coupling
        if pressure == 0.0:
            continue
        for b in _agent_bus(agent_id, bus):
            prev = b.get("social_license_score", 50)
            new = max(0.0, min(100.0, round(prev + pressure, 2)))
            if new != prev:
                b["social_license_score"] = new
                deltas.setdefault(b["bu_id"], {})[agent_id] = round(new - prev, 2)
    agent_master_state["slo_feedback_round"] = round_number
    return deltas


def apply_agent_betrayal_scar(agent_state: dict, betrayal: bool, round_number: int,
                              scar_immediate: float, scar_duration: int, scar_ceiling: float) -> None:
    """F1 — a betrayal cuts tolerance now and caps its recovery for a few rounds."""
    if betrayal:
        agent_state["tolerance"] = max(0.0, round(agent_state.get("tolerance", 50) - scar_immediate, 1))
        agent_state["scar_until"] = round_number + scar_duration
    if round_number <= int(agent_state.get("scar_until", 0)):
        agent_state["tolerance"] = min(agent_state["tolerance"], scar_ceiling)


def apply_agent_engagement(agent_master_state: dict, gs: dict, action: dict, round_number: int) -> dict:
    """F5 — a town hall / pledge / commitment toward one agent: cost + tolerance
    bump now, and (for pledge/commitment) a promise registered on the ledger."""
    from stakeholder_engagement import ENGAGEMENT_CATALOG, _engagement_consts
    a_type = (action or {}).get("type"); agent_id = (action or {}).get("npc_id") or (action or {}).get("agent_id")
    spec = ENGAGEMENT_CATALOG.get(a_type); agents = agent_master_state.get("agents", {})
    if spec is None or agent_id not in agents:
        return {"error": "invalid_engagement", "type": a_type, "agent_id": agent_id}
    c = _engagement_consts(); st = agents[agent_id]
    gs["corporate_treasury"] = round(gs.get("corporate_treasury", 0) - c["cost"][a_type], 2)
    st["tolerance"] = min(AGENT_PROFILES[agent_id]["initial_tolerance"],
                          round(st.get("tolerance", 50) + c["trust"][a_type], 1))
    res = {"type": a_type, "agent_id": agent_id, "cost": c["cost"][a_type], "tolerance_now": st["tolerance"]}
    if spec["creates_promise"]:
        promise = {"id": f"{agent_id}:{a_type}:R{round_number}", "agent_id": agent_id,
                   "metric": action.get("metric", "avg_slo"), "target": float(action.get("target", 60)),
                   "due_round": round_number + max(1, int(action.get("horizon", c["default_horizon"]))),
                   "state": "open"}
        agent_master_state.setdefault("promises", []).append(promise); res["promise"] = promise
    return res


def resolve_agent_promises(agent_master_state: dict, gs: dict, bus: list[dict], round_number: int) -> list[dict]:
    """F5 — judge due promises: kept pays tolerance/SLO/reputation, broken scars."""
    from stakeholder_engagement import _engagement_consts
    c = _engagement_consts(); ledger = agent_master_state.setdefault("promises", [])
    agents = agent_master_state.get("agents", {}); out = []
    metrics = _compute_agent_metrics(gs, bus)
    for p in ledger:
        if p.get("state") != "open" or int(p.get("due_round", 0)) > round_number:
            continue
        st = agents.get(p["agent_id"])
        if st is None:
            p["state"] = "void"; continue
        val = metrics.get(p["metric"], gs.get(p["metric"]))
        kept = isinstance(val, (int, float)) and val >= float(p["target"])
        cap = AGENT_PROFILES[p["agent_id"]]["initial_tolerance"]
        if kept:
            st["tolerance"] = min(cap, round(st.get("tolerance", 50) + c["kept_trust_bonus"], 1))
            for b in _agent_bus(p["agent_id"], bus):
                b["social_license_score"] = max(0.0, min(100.0, round(b.get("social_license_score", 50) + c["kept_slo_credit"], 2)))
            gs["group_reputation"] = max(0, min(100, round(gs.get("group_reputation", 50) + c["kept_rep_credit"], 2)))
            p["state"] = "kept"
        else:
            st["tolerance"] = max(0.0, round(st.get("tolerance", 50) - c["scar_immediate"], 1))
            st["scar_until"] = round_number + c["scar_duration"]
            gs["group_reputation"] = max(0, round(gs.get("group_reputation", 50) - c["broken_rep_ding"], 2))
            p["state"] = "broken"
        p["resolved_round"] = round_number
        out.append({"id": p["id"], "agent_id": p["agent_id"], "state": p["state"], "metric": p["metric"], "target": p["target"]})
    return out


# ── SPEC F3 — coalitions & F4 — seeded threshold jitter ──────────

# Per-agent clout: how hard they can hit you (design-authored, 0–1). Used to
# scale coalition pressure — a coalition of the regulator + investor bites harder
# than one of the vendors would.
_AGENT_CLOUT = {
    "the_regulator": 0.95,
    "the_institutional_investor": 0.90,
    "the_gen_z_employee": 0.70,
    "the_community_activist": 0.60,
    "the_journalist": 0.50,
}
_HOSTILE_STAGES = ("agitated", "hostile", "triggered")


def evaluate_agent_coalition(agent_master_state: dict) -> tuple[float, list[str]]:
    """F3 — two or more agents at a hostile stage form a coalition whose pressure
    grows with the number of members beyond the first and their mean clout."""
    members = [aid for aid, st in agent_master_state.get("agents", {}).items()
               if st.get("escalation_stage") in _HOSTILE_STAGES and st.get("triggered_round") is None]
    if len(members) < 2:
        return 0.0, members
    mean_clout = sum(_AGENT_CLOUT.get(m, 0.5) for m in members) / len(members)
    return round(min(1.0, mean_clout * (len(members) - 1)), 4), members


def _seeded_unit(seed, *tags) -> float:
    import hashlib
    key = "|".join(str(t) for t in (seed, *tags))
    return int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:8], 16) / 0xFFFFFFFF


def _draw_agent_offsets(agent_id: str, seed, jitter: float) -> dict:
    """F4 — per-agent escalation-threshold offsets in [−jitter, +jitter], drawn
    once from the cohort seed (identical for every team, unknown to all)."""
    return {stage: round((_seeded_unit(seed, "athr", agent_id, stage) * 2.0 - 1.0) * jitter, 1)
            for stage in ("watching", "agitated", "hostile", "triggered")}


def _jittered_thresholds(base: dict, offsets: dict) -> dict:
    if not offsets:
        return base
    return {k: max(0.0, min(100.0, v + offsets.get(k, 0.0))) for k, v in base.items()}
    return summary
