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


# ═══════════════════════════════════════════════════════════════
#  AGENT PROFILE DEFINITIONS
# ═══════════════════════════════════════════════════════════════

AGENT_PROFILES = {
    "the_regulator": {
        "name": "Commissioner Eleanor Carson",
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
        "name": "Marcus Chen-Hoffmann",
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
            "watching": "'We've placed Muressons on our ESG watchlist,' Chen-Hoffmann informs the board. 'We expect a credible improvement plan within 90 days.'",
            "agitated": "Nordic Pension Alliance downgrades Muressons to 'underweight'. Chen-Hoffmann's public letter: 'We are deeply concerned about trajectory.'",
            "hostile": "BREAKING: Nordic Pension Alliance begins systematic position reduction. 'We can no longer justify this allocation to our beneficiaries.'",
            "triggered": None,
        },
        "triggered_event": {
            "title": "📉 INSTITUTIONAL DIVESTMENT FIRE SALE",
            "narrative": (
                "🦅 Marcus Chen-Hoffmann triggers full divestment protocol. "
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
        "title": "Head Panchayat, Deccan Plateau District Council",
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
        "name": "Jay Buffet",
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
            "dormant": "Jay Buffet publishes a balanced feature: 'Muressons: A Corporate Turnaround Story.'",
            "watching": "Buffet begins a series: 'Inside Muressons — Part 1: The Promises.' Sources say he's requesting internal documents.",
            "agitated": "INVESTIGATION: 'The Green Facade?' by Jay Buffet trends on social media. 12,000 engagements in 24 hours.",
            "hostile": "Buffet's 3-part exposé 'Muressons Unmasked' is syndicated across 5 national outlets. Reach: 4.5M impressions.",
            "triggered": None,
        },
        "triggered_event": {
            "title": "📰 VIRAL EXPOSÉ — CORPORATE CREDIBILITY DESTROYED",
            "narrative": (
                "📰 Jay Buffet's Pulitzer-nominated investigation 'Muressons: "
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
) -> tuple[dict, dict]:
    """
    Process all autonomous stakeholder agents for this round.
    Returns (updated_state, diagnostics).
    """
    metrics = _compute_agent_metrics(gs, bus)
    diagnostics: dict[str, Any] = {"agent_actions": [], "cascades_fired": []}
    triggered_agents = []

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
            decay = profile["patience_decay_rate"] * (1 + severity)
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

        # Determine stage
        new_stage = _get_stage(
            agent_state["tolerance"],
            profile["escalation_thresholds"]
        )
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

    agent_master_state["events_this_round"] = diagnostics["agent_actions"]
    return agent_master_state, diagnostics


def get_agent_summary(agent_master_state: dict) -> list[dict]:
    """Return a frontend-friendly summary of all agent states."""
    summary = []
    for agent_id, agent_state in agent_master_state.get("agents", {}).items():
        profile = AGENT_PROFILES.get(agent_id, {})
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
        })
    return summary
