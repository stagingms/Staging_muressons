"""
Muressons Global Corporation — AI-Driven NPC Stakeholders (SI-2)
LLM-powered non-player characters that react dynamically to player
decisions: activist investor, regulator, community leader, journalist.

Theory base:
  - Mitchell et al. (1997): Stakeholder Salience (power, legitimacy, urgency)
  - Fassin (2009): Stakeholder management vs stakeholding
  - Phillips (2003): Stakeholder legitimacy

Architecture:
  Hybrid module. Contains deterministic personality/behaviour models
  AND prompt templates for LLM-enhanced dialogue generation.
  Falls back to deterministic responses if LLM is unavailable.
"""

from __future__ import annotations
from typing import Any
import random
import math


# ═══════════════════════════════════════════════════════════════
#  NPC DEFINITIONS
# ═══════════════════════════════════════════════════════════════

NPC_PROFILES = {
    "activist_investor": {
        "name": "Elise Thornton",
        "title": "Managing Director, FutureFirst Activist Fund",
        "icon": "🦅",
        "personality": "assertive",
        "salience": {"power": 0.85, "legitimacy": 0.70, "urgency": 0.90},
        "priorities": ["climate_disclosure", "board_diversity", "stranded_assets"],
        "triggers": {
            "reputation_below_40": "escalate",
            "carbon_intensity_above_60": "public_letter",
            "no_esg_committee": "proxy_fight",
        },
        "satisfaction_drivers": [
            ("group_reputation", 0.3, 50),    # Weight, baseline
            ("carbon_intensity", -0.3, 50),    # Negative: high CI = low satisfaction
            ("esg_linked_compensation_pct", 0.2, 20),
            ("governance_risk", -0.2, 30),
        ],
        "escalation_levels": [
            {"threshold": 70, "action": "supportive", "label": "Supportive Engagement"},
            {"threshold": 50, "action": "concerned", "label": "Concerned Letter to Board"},
            {"threshold": 30, "action": "hostile", "label": "Public Campaign"},
            {"threshold": 0, "action": "adversarial", "label": "Proxy Fight / AGM Challenge"},
        ],
        "dialogue_templates": {
            "supportive": (
                "Ms Thornton nods approvingly. 'Your progress on {topic} is noted. "
                "FutureFirst will support management's slate at the AGM. "
                "Continue this trajectory.'"
            ),
            "concerned": (
                "'We've been patient,' Thornton says, placing a thick dossier on the table. "
                "'But your {weakness} is becoming a liability. We expect a credible "
                "remediation plan within 90 days, or we go public.'"
            ),
            "hostile": (
                "FutureFirst issues a public letter: 'Dear Fellow Shareholders, "
                "Muressons management has failed to address {weakness}. We are "
                "filing a resolution demanding {demand}. We urge all shareholders "
                "to vote FOR this resolution.'"
            ),
            "adversarial": (
                "BREAKING: FutureFirst Activist Fund announces proxy contest at Muressons AGM. "
                "'Management has had every opportunity to address {weakness},' "
                "says Thornton. 'We are nominating three independent directors "
                "with genuine ESG expertise. The current board must be held accountable.'"
            ),
        },
    },
    "regulator": {
        "name": "Commissioner Sofia Petrova",
        "title": "EU DG FISMA — Corporate Sustainability Division",
        "icon": "🏛️",
        "personality": "methodical",
        "salience": {"power": 0.95, "legitimacy": 0.95, "urgency": 0.60},
        "priorities": ["csrd_compliance", "taxonomy_alignment", "audit_quality"],
        "triggers": {
            "governance_risk_above_60": "formal_investigation",
            "greenwashing_detected": "enforcement_action",
            "non_disclosure": "compliance_notice",
        },
        "satisfaction_drivers": [
            ("governance_risk", -0.4, 30),
            ("group_reputation", 0.2, 50),
            ("tnfd_disclosure_level", 0.2, 0),
        ],
        "escalation_levels": [
            {"threshold": 70, "action": "satisfied", "label": "Compliant — No Action"},
            {"threshold": 50, "action": "monitoring", "label": "Enhanced Monitoring"},
            {"threshold": 30, "action": "investigation", "label": "Formal Investigation"},
            {"threshold": 0, "action": "enforcement", "label": "Enforcement Action / Fine"},
        ],
        "dialogue_templates": {
            "satisfied": (
                "Commissioner Petrova's office issues a routine acknowledgement: "
                "'Muressons' CSRD disclosures meet current requirements. "
                "No further action required at this time.'"
            ),
            "monitoring": (
                "'We have placed Muressons on our enhanced monitoring list,' "
                "Commissioner Petrova states formally. 'Your {weakness} "
                "requires attention. We expect full remediation by Q3.'"
            ),
            "investigation": (
                "OFFICIAL: EU DG FISMA opens formal investigation into Muressons' "
                "{weakness}. 'We have reasonable grounds to believe that current "
                "disclosures are materially incomplete,' says Commissioner Petrova. "
                "'A full Article 8 review will commence immediately.'"
            ),
            "enforcement": (
                "ENFORCEMENT ACTION: Commissioner Petrova announces a €{fine}M fine "
                "against Muressons for {weakness}. 'Persistent non-compliance is not "
                "acceptable. This fine reflects the severity of the deficiency "
                "and should serve as a deterrent to the sector.'"
            ),
        },
    },
    "community_leader": {
        "name": "Rajesh Patil",
        "title": "Head Panchayat, Deccan Plateau District Council",
        "icon": "🏘️",
        "personality": "passionate",
        "salience": {"power": 0.30, "legitimacy": 0.90, "urgency": 0.75},
        "priorities": ["water_rights", "employment", "environmental_justice"],
        "triggers": {
            "slo_below_40": "protest",
            "water_stress_above_60": "legal_action",
            "facility_closure": "community_campaign",
        },
        "satisfaction_drivers": [
            ("social_license_score", 0.4, 50),
            ("water_stress_index", -0.3, 40),
            ("just_transition_fund", 0.2, 0),
        ],
        "escalation_levels": [
            {"threshold": 70, "action": "cooperative", "label": "Community Partnership"},
            {"threshold": 50, "action": "watchful", "label": "Community Monitoring"},
            {"threshold": 30, "action": "protest", "label": "Community Protest"},
            {"threshold": 0, "action": "legal", "label": "Legal Action / Injunction"},
        ],
        "dialogue_templates": {
            "cooperative": (
                "Rajesh Patil invites Muressons to the annual harvest festival. "
                "'Your company has been a good neighbour. The water recycling "
                "plant has made a real difference. Let us continue to grow together.'"
            ),
            "watchful": (
                "'We are watching carefully,' says Patil at the panchayat meeting. "
                "'The promises about {topic} have not yet materialised. "
                "Our patience is not infinite.'"
            ),
            "protest": (
                "200 villagers block the road to the Pune facility. Patil addresses "
                "the crowd: 'Our water, our land, our lives! Muressons takes "
                "everything and gives nothing. We will not move until they listen!'"
            ),
            "legal": (
                "BREAKING: Deccan communities file injunction against Muressons. "
                "'We have exhausted every avenue of dialogue,' says Patil. "
                "'The courts will decide whether corporations can destroy "
                "our water sources with impunity.'"
            ),
        },
    },
    "journalist": {
        "name": "Jaya Mehta",
        "title": "Senior Investigative Reporter, Deccan Herald Business",
        "icon": "📰",
        "personality": "curious",
        "salience": {"power": 0.50, "legitimacy": 0.60, "urgency": 0.40},
        "priorities": ["transparency", "greenwashing", "worker_conditions"],
        "triggers": {
            "reputation_drop_gt_10": "investigation",
            "greenwashing_detected": "expose",
            "strike_triggered": "coverage",
        },
        "satisfaction_drivers": [
            ("transparency", 0.3, 50),
            ("group_reputation", 0.2, 50),
            ("governance_risk", -0.3, 30),
        ],
        "escalation_levels": [
            {"threshold": 70, "action": "favorable", "label": "Positive Feature Story"},
            {"threshold": 50, "action": "neutral", "label": "Balanced Coverage"},
            {"threshold": 30, "action": "critical", "label": "Critical Investigation"},
            {"threshold": 0, "action": "hostile", "label": "Exposé / Viral Story"},
        ],
        "dialogue_templates": {
            "favorable": (
                "Jaya Mehta publishes: 'Muressons: A Corporate Turnaround Story. "
                "How one conglomerate is proving that sustainability and profit "
                "can coexist.' [Syndicated to Economic Times, reach: 2.1M]"
            ),
            "neutral": (
                "Mehta's latest column mentions Muressons in passing: "
                "'The company's efforts on {topic} are noted, though questions "
                "remain about {weakness}. We continue to monitor.'"
            ),
            "critical": (
                "INVESTIGATION: 'The Green Facade? Inside Muressons' struggle "
                "with {weakness},' by Jaya Mehta. [12,000 social media engagements "
                "in 24 hours. National syndication pending.]"
            ),
            "hostile": (
                "VIRAL: Mehta's 3-part exposé 'Muressons Unmasked' trends #1 on X/Twitter. "
                "'Documents reveal systematic {weakness}. Workers describe a culture of "
                "{negative_culture}. Investors are demanding answers.' "
                "[Reached 4.5M impressions in 48 hours]"
            ),
        },
    },
}


# ═══════════════════════════════════════════════════════════════
#  NPC STATE MANAGEMENT
# ═══════════════════════════════════════════════════════════════

def create_initial_npc_state() -> dict[str, Any]:
    """Create initial NPC stakeholder states."""
    npcs = {}
    for npc_id, profile in NPC_PROFILES.items():
        npcs[npc_id] = {
            "profile": profile,
            "satisfaction": 50.0,
            "escalation_level": "neutral",
            "interactions": [],
            "trust": 50.0,
            "last_action": None,
            "rounds_since_interaction": 0,
        }

    return {
        "npcs": npcs,
        "npc_events_this_round": [],
        "total_interactions": 0,
    }


def calc_npc_satisfaction(
    npc_id: str,
    npc_state: dict,
    gs: dict,
    bus: list[dict],
) -> tuple[float, dict]:
    """Calculate NPC satisfaction based on game state."""
    profile = npc_state["profile"]
    drivers = profile.get("satisfaction_drivers", [])

    satisfaction = 0.0
    details = []

    for metric, weight, baseline in drivers:
        if metric == "social_license_score":
            value = sum(bu.get("social_license_score", 50) for bu in bus) / max(len(bus), 1)
        elif metric == "carbon_intensity":
            value = sum(bu.get("carbon_intensity", 50) for bu in bus) / max(len(bus), 1)
        elif metric == "governance_risk":
            value = sum(bu.get("governance_risk_score", 20) for bu in bus) / max(len(bus), 1)
        elif metric == "water_stress_index":
            bio = gs.get("biodiversity_state", {})
            value = bio.get("water_stress_index", 0.4) * 100
        elif metric == "tnfd_disclosure_level":
            levels = {"none": 0, "partial": 25, "aligned": 50, "leadership": 75}
            bio = gs.get("biodiversity_state", {})
            value = levels.get(bio.get("tnfd_disclosure_level", "none"), 0)
        else:
            value = gs.get(metric, baseline)

        contribution = weight * (value - baseline)
        satisfaction += contribution
        details.append({
            "metric": metric,
            "value": round(value, 2),
            "weight": weight,
            "baseline": baseline,
            "contribution": round(contribution, 2),
        })

    # Base satisfaction + calculated delta
    final = max(0, min(100, round(50 + satisfaction, 2)))

    return final, {"satisfaction": final, "drivers": details}


def determine_npc_action(
    npc_id: str,
    npc_state: dict,
    satisfaction: float,
    gs: dict,
    round_number: int,
) -> dict:
    """Determine what action the NPC takes this round."""
    profile = npc_state["profile"]
    escalation_levels = profile.get("escalation_levels", [])

    # Find current escalation level
    action = "neutral"
    label = "No Action"
    for level in escalation_levels:
        if satisfaction >= level["threshold"]:
            action = level["action"]
            label = level["label"]
            break

    # Generate dialogue
    templates = profile.get("dialogue_templates", {})
    template = templates.get(action, "No specific message this round.")

    # Fill template variables
    message = template
    if "{topic}" in message:
        topics = profile.get("priorities", ["sustainability"])
        message = message.replace("{topic}", topics[0] if topics else "ESG")
    if "{weakness}" in message:
        weaknesses = []
        if gs.get("group_reputation", 50) < 40:
            weaknesses.append("reputational decline")
        avg_ci = sum(bu.get("carbon_intensity", 50) for bu in gs.get("bu_states_cache", [{}])) / 1
        if avg_ci > 60:
            weaknesses.append("high carbon intensity")
        weakness = weaknesses[0] if weaknesses else "governance gaps"
        message = message.replace("{weakness}", weakness)
    if "{demand}" in message:
        message = message.replace("{demand}", "enhanced climate risk disclosure")
    if "{fine}" in message:
        fine = round(random.uniform(5, 25), 1)
        message = message.replace("{fine}", str(fine))
    if "{negative_culture}" in message:
        message = message.replace("{negative_culture}", "short-termism and opacity")

    npc_state["satisfaction"] = satisfaction
    npc_state["escalation_level"] = action
    npc_state["last_action"] = {
        "round": round_number,
        "action": action,
        "label": label,
        "message": message,
    }
    npc_state["rounds_since_interaction"] = 0

    return {
        "npc_id": npc_id,
        "name": profile["name"],
        "title": profile["title"],
        "icon": profile["icon"],
        "satisfaction": round(satisfaction, 1),
        "action": action,
        "label": label,
        "message": message,
    }


def process_npc_tick(
    npc_master_state: dict,
    gs: dict,
    bus: list[dict],
    events: dict,
    round_number: int,
) -> tuple[dict, dict]:
    """
    Process all NPC stakeholders for this round.
    Returns (updated_state, diagnostics).
    """
    diagnostics: dict[str, Any] = {"npc_actions": []}

    for npc_id, npc_state in npc_master_state["npcs"].items():
        satisfaction, sat_diag = calc_npc_satisfaction(npc_id, npc_state, gs, bus)
        action_result = determine_npc_action(npc_id, npc_state, satisfaction, gs, round_number)

        diagnostics["npc_actions"].append(action_result)

        # Apply consequences of hostile NPC actions
        if action_result["action"] in ("hostile", "adversarial", "enforcement", "legal"):
            # Reputation hit from hostile stakeholders
            rep_hit = -5 if action_result["action"] in ("hostile", "adversarial") else -3
            gs["group_reputation"] = max(
                0, round(gs.get("group_reputation", 50) + rep_hit, 2)
            )
            diagnostics[f"npc_{npc_id}_rep_impact"] = rep_hit

            # Financial penalty from regulator
            if npc_id == "regulator" and action_result["action"] == "enforcement":
                fine = round(random.uniform(5_000_000, 25_000_000), 2)
                gs["corporate_treasury"] = round(gs["corporate_treasury"] - fine, 2)
                diagnostics["regulatory_fine"] = fine

        npc_state["interactions"].append({
            "round": round_number,
            "satisfaction": satisfaction,
            "action": action_result["action"],
        })

    npc_master_state["total_interactions"] += len(diagnostics["npc_actions"])

    return npc_master_state, diagnostics


# ═══════════════════════════════════════════════════════════════
#  LLM PROMPT TEMPLATES (for enhanced dialogue)
# ═══════════════════════════════════════════════════════════════

def get_npc_llm_prompt(
    npc_id: str,
    npc_state: dict,
    gs: dict,
    round_number: int,
) -> str:
    """
    Generate a prompt for LLM-enhanced NPC dialogue.
    Falls back to deterministic templates if LLM is unavailable.
    """
    profile = npc_state["profile"]
    satisfaction = npc_state.get("satisfaction", 50)

    return f"""You are {profile['name']}, {profile['title']}.

Personality: {profile['personality']}
Current satisfaction with Muressons: {satisfaction}/100
Escalation level: {npc_state.get('escalation_level', 'neutral')}
Your priorities: {', '.join(profile['priorities'])}

Company context:
- Group reputation: {gs.get('group_reputation', 50)}/100
- Corporate treasury: ${gs.get('corporate_treasury', 0):,.0f}
- Round: {round_number}/10

Generate a brief (2-3 sentence) in-character response that reflects your current
satisfaction level and priorities. If satisfaction is low, be confrontational.
If high, be supportive but maintain professional distance.

Respond in character, first person. Do not break character."""
