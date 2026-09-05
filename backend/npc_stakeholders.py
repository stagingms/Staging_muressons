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

Memory model / reconciliation decision (SPEC F1 §1.4, §7):
  Two "how does X feel about us" surfaces exist in the codebase — this module's
  named NPCs and `stakeholder_sentiment.py`'s portfolio `attitude_score` list.
  AUTHORITY: the per-NPC `trust` stock defined here (integrated from the existing
  `satisfaction` signal) is authoritative for escalation, cascades, strikes and
  (later) promises; `attitude_score` stays authoritative for the portfolio
  heat-map / salience-weighted overview. The two are *bridged*: when memory is on,
  a named NPC's `satisfaction` is blended toward its matching sentiment cohort's
  `attitude_score` (see `_matched_attitude` / `NPC_SENTIMENT_BRIDGE_WEIGHT`) so the
  two surfaces cannot drift (§1.4). Everything trust- and bridge-related is gated
  on the `stakeholder_memory_enabled` toggle, which defaults OFF; with it off this
  module behaves exactly as before.
"""

from __future__ import annotations
from typing import Any
import random
import math
import hashlib


# Flags that constitute a trust betrayal in a given round. Broken *promises*
# (F5) will be added here once the promise ledger ships; for now a betrayal is a
# deliberate opacity/greenwashing choice made this round. Kept small and explicit.
_BETRAYAL_FLAGS: frozenset[str] = frozenset({
    "deny_and_deflect",
    "greenwash_risk",
    "greenwash_detected",
    "materiality_ignored",
})


def detect_betrayal(events: dict | None) -> bool:
    """True if any trust-breaking flag was set this round (SPEC F1 §1.2)."""
    if not events:
        return False
    active = {k for k, v in events.items() if v is True}
    active |= {str(x) for x in (events.get("flags_set") or [])}
    return bool(active & _BETRAYAL_FLAGS)


def update_trust(
    npc_state: dict,
    satisfaction: float,
    betrayal_event: bool,
    round_number: int,
    *,
    gain_rate: float,
    loss_rate: float,
    scar_immediate: float,
    scar_duration: int,
    scar_ceiling: float,
) -> float:
    """
    Integrate the per-round `satisfaction` pressure into a persistent `trust`
    stock (0–100) with asymmetric dynamics (SPEC F1 §1.2):

        gap   = satisfaction - trust_prev
        rate  = gain_rate if gap >= 0 else loss_rate   # rises slow, falls fast
        trust = trust_prev + rate * gap

    A betrayal this round subtracts `scar_immediate` and caps recovery at
    `scar_ceiling` for `scar_duration` rounds. Mutates and returns
    `npc_state["trust"]`. Deterministic (no RNG).

    Requires the carry-forward fix (SPEC §1.7) so the stock persists across
    rounds; without it this would re-seed every tick and never integrate.
    """
    # First observation: seed the stock at current mood, not a flat 50, so it
    # doesn't start misleading (§1.5). State persists (§1.7) so this runs once.
    if not npc_state.get("trust_initialised"):
        npc_state["trust"] = round(float(satisfaction), 2)
        npc_state["trust_initialised"] = True
        npc_state.setdefault("scar_until", 0)
        return npc_state["trust"]

    trust_prev = float(npc_state.get("trust", satisfaction))
    gap = satisfaction - trust_prev
    rate = gain_rate if gap >= 0 else loss_rate
    trust_raw = trust_prev + rate * gap

    scar_until = int(npc_state.get("scar_until", 0))
    if betrayal_event:
        trust_raw -= scar_immediate
        scar_until = round_number + scar_duration
        npc_state["scar_until"] = scar_until

    ceiling = scar_ceiling if round_number <= scar_until else 100.0
    npc_state["trust"] = round(max(0.0, min(ceiling, trust_raw)), 2)
    return npc_state["trust"]


def _trust_constants() -> dict:
    """Lazily pull trust tunables from config (config-Excel backed)."""
    from config import (
        TRUST_GAIN_RATE, TRUST_LOSS_RATE,
        TRUST_SCAR_IMMEDIATE, TRUST_SCAR_DURATION, TRUST_SCAR_CEILING,
    )
    return {
        "gain_rate": TRUST_GAIN_RATE,
        "loss_rate": TRUST_LOSS_RATE,
        "scar_immediate": TRUST_SCAR_IMMEDIATE,
        "scar_duration": TRUST_SCAR_DURATION,
        "scar_ceiling": TRUST_SCAR_CEILING,
    }


# ── SPEC F1 §1.4: named-NPC ↔ portfolio-sentiment bridge ──────────
# Maps each named NPC to the id-substrings of the `stakeholder_sentiment` cohort
# that represents the same constituency, so the named NPC's `satisfaction` can be
# blended toward that cohort's `attitude_score` and the two surfaces stay aligned.
_NPC_SENTIMENT_MATCH: dict[str, tuple[str, ...]] = {
    "activist_investor": ("investor", "analyst", "shareholder"),
    "regulator":         ("regulator", "government"),
    "community_leader":  ("community", "farmer", "worker", "population", "ngo"),
    "journalist":        ("journalist", "media", "press"),
}


def _matched_attitude(npc_id: str, gs: dict) -> float | None:
    """
    Mean `attitude_score` of the portfolio sentiment stakeholders matching this
    named NPC (SPEC F1 §1.4). Returns None when no sentiment list is present or
    nothing matches, so the caller leaves satisfaction untouched (bridge no-op).
    """
    patterns = _NPC_SENTIMENT_MATCH.get(npc_id)
    if not patterns:
        return None
    scores = []
    _slist = (gs.get("sentiment_stakeholders")
              or (gs.get("active_event_flags") or {}).get("sentiment_stakeholders")
              or [])
    for s in _slist:
        sid = str(s.get("id", "")).lower()
        if any(p in sid for p in patterns):
            v = s.get("attitude_score")
            if isinstance(v, (int, float)):
                scores.append(float(v))
    return (sum(scores) / len(scores)) if scores else None


def _bridge_weight_baseline() -> float:
    """Low always-on bridge weight used when F1 memory is off (EVAL rec 5)."""
    from config import NPC_SENTIMENT_BRIDGE_BASELINE
    return NPC_SENTIMENT_BRIDGE_BASELINE


def _bridge_weight() -> float:
    """Lazily pull the sentiment-bridge weight from config (config-Excel backed)."""
    from config import NPC_SENTIMENT_BRIDGE_WEIGHT
    return NPC_SENTIMENT_BRIDGE_WEIGHT


# ── SPEC F4: seeded threshold uncertainty + patience ─────────────
# F-16 (audit 2026-09-04): the tier index from which the patience clock arms.
# 2 = the first hostile-ish tier ("Public Campaign" / "Formal Investigation");
# it was 1 ("Concerned"), which forced every team hostile on a timer.
PATIENCE_ARMS_FROM_TIER: int = 2
def _seeded_unit(seed: Any, *tags: Any) -> float:
    """Deterministic [0,1) from a cohort seed + tags via SHA-256 (GAME-4 style)."""
    key = "|".join(str(t) for t in (seed, *tags))
    return int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:8], 16) / 0xFFFFFFFF


def _draw_threshold_offsets(npc_id: str, seed: Any, jitter: float, n: int = 4) -> list[float]:
    """
    Per-NPC escalation-threshold offsets in [−jitter, +jitter], drawn ONCE from
    the cohort seed (SPEC F4 §4.2). Same seed → identical offsets for every team
    (fair); no team is told them (tense). Never mutates the shared NPC_PROFILES.
    """
    return [round((_seeded_unit(seed, "thr", npc_id, i) * 2.0 - 1.0) * jitter, 2) for i in range(n)]


def _seeded_fine(seed: Any, npc_id: str, round_number: int, lo: float, hi: float) -> float:
    """Deterministic per-cohort fine amount — replaces the bare-random draws
    in the stakeholder path so all teams face the same number (GAME-4, §4.3)."""
    return round(lo + _seeded_unit(seed, "fine", npc_id, round_number) * (hi - lo), 2)


def _uncertainty_consts() -> dict:
    from config import THRESHOLD_JITTER, PATIENCE_LIMIT
    return {"jitter": THRESHOLD_JITTER, "patience_limit": PATIENCE_LIMIT}


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
        "title": "Head Deccan Plateau Council",
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
    bridge_weight: float = 0.0,
) -> tuple[float, dict]:
    """
    Calculate NPC satisfaction based on game state.

    When `bridge_weight > 0` (set only when memory is enabled), the metric-based
    result is blended toward the matching portfolio sentiment cohort's
    `attitude_score` so the named-NPC and portfolio surfaces stay aligned
    (SPEC F1 §1.4). `bridge_weight == 0` (the default) reproduces legacy behaviour
    exactly, so every other call site and the memory-off path are unchanged.
    """
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

    # SPEC F1 §1.4 bridge: pull satisfaction toward the matching portfolio
    # sentiment cohort so the two "how they feel about us" surfaces agree by
    # construction. No-op when bridge_weight == 0 or no sentiment list is present.
    bridge_applied = None
    if bridge_weight > 0.0:
        matched = _matched_attitude(npc_id, gs)
        if matched is not None:
            final = max(0.0, min(100.0, round(
                (1.0 - bridge_weight) * final + bridge_weight * matched, 2
            )))
            bridge_applied = round(matched, 2)

    return final, {"satisfaction": final, "drivers": details, "sentiment_bridge": bridge_applied}


def determine_npc_action(
    npc_id: str,
    npc_state: dict,
    satisfaction: float,
    gs: dict,
    round_number: int,
    gate_value: float | None = None,
    threshold_offsets: list[float] | None = None,
    patience_limit: int | None = None,
    seed: Any = None,
) -> dict:
    """
    Determine what action the NPC takes this round.

    Escalation tiers are selected on `gate_value` when provided (the `trust`
    stock, once F1/memory is enabled) and otherwise on raw `satisfaction`
    (legacy behaviour). `satisfaction` is always retained in state and output for
    the facilitator/debrief view (SPEC F1 §1.3).

    SPEC F4 (only when the caller passes them):
      • `threshold_offsets` jitter each tier's threshold (seeded per cohort), so
        the exact tipping points are uncertain.
      • `patience_limit` runs a patience clock: an NPC held at a HOSTILE-ish tier
        (index ≥ 2 — F-16, audit 2026-09-04; was ≥ 1, the merely "concerned"
        tier, which three of four NPCs sit at even for an excellent team, so
        every team was forced hostile on a timer) for that many rounds
        escalates one tier regardless of the metric.
    With both None (the default) tier selection is byte-for-byte the legacy path.
    """
    profile = npc_state["profile"]
    escalation_levels = profile.get("escalation_levels", [])

    # Value the escalation tiers gate on: trust when supplied, else satisfaction.
    tier_metric = gate_value if gate_value is not None else satisfaction

    # Find current escalation level (thresholds optionally jittered — F4).
    action = "neutral"
    label = "No Action"
    tier_idx = None
    for i, level in enumerate(escalation_levels):
        thr = level["threshold"]
        if threshold_offsets and i < len(threshold_offsets):
            thr = max(0.0, min(100.0, thr + threshold_offsets[i]))
        if tier_metric >= thr:
            action, label, tier_idx = level["action"], level["label"], i
            break

    # ── Staged escalation (EVAL rec 3, 2026-09-01) ─────────────────────────
    # A relationship may WORSEN by at most one tier per round: real
    # stakeholders write the concerned letter before the proxy fight, and a
    # standing start (no prior tier) counts as cooperative — so Round 1 can
    # reach at most one step past tier 0, however bad the KPIs. De-escalation
    # is never rate-limited (with F1 on, the trust stock already makes the
    # way back slow). The F4 patience clock below still forces its own +1.
    if tier_idx is not None and escalation_levels:
        _prev_tier = npc_state.get("last_tier")
        _cap = (0 if _prev_tier is None else _prev_tier) + 1
        if tier_idx > _cap:
            tier_idx = _cap
            staged = escalation_levels[tier_idx]
            action, label = staged["action"], staged["label"]

    # Patience clock (F4): sitting at a hostile-ish tier too long forces
    # escalation. F-16 (audit 2026-09-04): the clock armed from tier 1, the
    # "concerned" tier, which needs satisfaction/trust ≥ 70 to leave and which
    # three of four NPCs occupy even at reputation 85 / SLO 85 / CI 20 — so an
    # even-investment team with F4 on (the production default) took ≈3.5
    # forced hostile actions, −16.8 reputation and near the jittered boundary
    # a regulator fine, none of it attributable to a decision. It now arms
    # from the first hostile-ish tier (index 2): a team that IS at "Public
    # Campaign" and does nothing for PATIENCE_LIMIT rounds is escalated; a
    # team at "Concerned" is not. PATIENCE_LIMIT stays 3 (calibration call:
    # the tier change, not the limit, was the defect).
    if patience_limit is not None and tier_idx is not None and escalation_levels:
        if tier_idx == npc_state.get("last_tier"):
            npc_state["rounds_at_tier"] = npc_state.get("rounds_at_tier", 0) + 1
        else:
            npc_state["rounds_at_tier"] = 1
        if (tier_idx >= PATIENCE_ARMS_FROM_TIER and npc_state["rounds_at_tier"] >= patience_limit
                and tier_idx < len(escalation_levels) - 1):
            tier_idx += 1
            forced = escalation_levels[tier_idx]
            action, label = forced["action"], forced["label"]
            npc_state["rounds_at_tier"] = 1        # reset so it doesn't force every round
        if tier_idx == 0:
            npc_state["rounds_at_tier"] = 0        # cooperation resets patience generously

    # Staged escalation + the patience clock both key off last round's tier.
    npc_state["last_tier"] = tier_idx

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
        # Seeded per cohort when a stochastic seed is present (GAME-4, §4.3);
        # falls back to the legacy random draw only for un-seeded ad-hoc sessions.
        _seed = gs.get("active_event_flags", {}).get("stochastic_seed")
        fine = (_seeded_fine(_seed, npc_id, round_number, 5, 25)
                if _seed not in (None, "") else round(random.uniform(5, 25), 1))
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
        "trust": round(float(npc_state.get("trust", satisfaction)), 1),
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
    memory_enabled: bool = False,
    uncertainty_enabled: bool = False,
) -> tuple[dict, dict]:
    """
    Process all NPC stakeholders for this round.
    Returns (updated_state, diagnostics).

    When `memory_enabled` (the `stakeholder_memory_enabled` toggle, default off),
    each NPC's persistent `trust` stock is integrated from its satisfaction and
    used to gate escalation; otherwise behaviour is unchanged (SPEC F1).
    When `uncertainty_enabled` (SPEC F4, default off), escalation thresholds are
    jittered per cohort and a patience clock can force escalation. Both toggles
    default off so every other call site stays legacy.
    """
    diagnostics: dict[str, Any] = {"npc_actions": []}

    # Betrayal is a round-level event (a deliberate opacity/greenwash choice) —
    # evaluate once and apply to every relationship's trust.
    betrayal = detect_betrayal(events) if memory_enabled else False
    trust_consts = _trust_constants() if memory_enabled else None
    # Bridge only pulls satisfaction toward portfolio sentiment when memory is on;
    # 0.0 otherwise keeps the legacy metric-only path (SPEC F1 §1.4).
    # EVAL rec 5 (2026-09-01): the bridge never fully sleeps — with F1 off it
    # runs at a low baseline weight so the heat-map and the named NPCs cannot
    # drift into telling the classroom two different moods for one regulator.
    bridge_weight = _bridge_weight() if memory_enabled else _bridge_weight_baseline()
    # F4 uncertainty: seeded threshold jitter + patience clock (default off).
    _uncert = _uncertainty_consts() if uncertainty_enabled else None
    _seed = gs.get("active_event_flags", {}).get("stochastic_seed")

    for npc_id, npc_state in npc_master_state["npcs"].items():
        satisfaction, sat_diag = calc_npc_satisfaction(
            npc_id, npc_state, gs, bus, bridge_weight=bridge_weight
        )

        gate_value = None
        if memory_enabled:
            gate_value = update_trust(
                npc_state, satisfaction, betrayal, round_number, **trust_consts
            )

        _offsets = _patience = None
        if uncertainty_enabled:
            if "threshold_offsets" not in npc_state:
                npc_state["threshold_offsets"] = _draw_threshold_offsets(
                    npc_id, _seed, _uncert["jitter"]
                )
            _offsets = npc_state["threshold_offsets"]
            _patience = _uncert["patience_limit"]

        action_result = determine_npc_action(
            npc_id, npc_state, satisfaction, gs, round_number,
            gate_value=gate_value, threshold_offsets=_offsets,
            patience_limit=_patience, seed=_seed,
        )

        diagnostics["npc_actions"].append(action_result)

        # Apply consequences of hostile NPC actions
        if action_result["action"] in ("hostile", "adversarial", "enforcement", "legal"):
            # Reputation hit from hostile stakeholders
            rep_hit = -5 if action_result["action"] in ("hostile", "adversarial") else -3
            gs["group_reputation"] = max(
                0, round(gs.get("group_reputation", 50) + rep_hit, 2)
            )
            diagnostics[f"npc_{npc_id}_rep_impact"] = rep_hit

            # Financial penalty from regulator (seeded per cohort — GAME-4, §4.3).
            if npc_id == "regulator" and action_result["action"] == "enforcement":
                fine = (_seeded_fine(_seed, npc_id, round_number, 5_000_000, 25_000_000)
                        if _seed not in (None, "") else round(random.uniform(5_000_000, 25_000_000), 2))
                gs["corporate_treasury"] = round(gs.get("corporate_treasury", 0.0) - fine, 2)
                diagnostics["regulatory_fine"] = fine

        npc_state["interactions"].append({
            "round": round_number,
            "satisfaction": satisfaction,
            "action": action_result["action"],
        })

    npc_master_state["total_interactions"] += len(diagnostics["npc_actions"])

    return npc_master_state, diagnostics


# ═══════════════════════════════════════════════════════════════
#  EVAL rec 6 (2026-09-01) — Stakeholder-Management side track feeds
#  the stakeholder system it teaches
# ═══════════════════════════════════════════════════════════════
# The sm_ outcome flags were declared-but-read-by-nothing (flag taxonomy,
# DEEP-5). Each completion outcome now grants a ONE-SHOT credit (or debit —
# the hostile paths cost you) to the named NPCs' trust stock and/or the
# autonomous agents' tolerance. Guarded by `sm_stakeholder_credits_applied`
# so replays and later rounds never double-apply. Magnitudes sit at 1-2
# rounds of trust/tolerance movement: meaningful, never game-deciding.
#
# npc: list of named-NPC ids credited on `trust` (skipped until the F1 stock
#      is initialised); agents: autonomous-agent ids credited on `tolerance`.
SM_TRACK_CREDITS: dict[str, dict] = {
    "sm_esg_gold_standard":     {"trust": +8, "npc": ["activist_investor", "regulator", "community_leader", "journalist"],
                                 "tolerance": +6, "agents": ["the_institutional_investor", "the_regulator"]},
    "sm_transparency_champion": {"trust": +6, "npc": ["journalist", "regulator"],
                                 "tolerance": +5, "agents": ["the_journalist"]},
    "sm_community_partnership": {"trust": +6, "npc": ["community_leader"],
                                 "tolerance": +6, "agents": ["the_community_activist"]},
    "sm_investor_focus":        {"trust": +5, "npc": ["activist_investor"],
                                 "tolerance": +5, "agents": ["the_institutional_investor"]},
    "sm_issb_aligned":          {"trust": +5, "npc": ["regulator", "activist_investor"],
                                 "tolerance": +4, "agents": ["the_regulator"]},
    "sm_voluntary_commitments": {"trust": +4, "npc": ["regulator", "community_leader"],
                                 "tolerance": +3, "agents": ["the_regulator", "the_community_activist"]},
    "sm_structured_response":   {"trust": +3, "npc": ["journalist", "regulator"],
                                 "tolerance": +3, "agents": ["the_journalist"]},
    "sm_gap_closure":           {"trust": +3, "npc": ["regulator"],
                                 "tolerance": +3, "agents": ["the_regulator"]},
    "sm_rating_challenge":      {"trust": -3, "npc": ["activist_investor"],
                                 "tolerance": -3, "agents": ["the_institutional_investor"]},
    "sm_defensive_crisis":      {"trust": -4, "npc": ["journalist", "community_leader"],
                                 "tolerance": -4, "agents": ["the_journalist"]},
    "sm_media_hostile":         {"trust": -6, "npc": ["journalist"],
                                 "tolerance": -5, "agents": ["the_journalist"]},
    "sm_legal_escalation":      {"trust": -5, "npc": ["regulator", "community_leader"],
                                 "tolerance": -4, "agents": ["the_regulator", "the_community_activist"]},
}


def apply_sm_track_credits(npc_master_state: dict, agent_master_state: dict,
                           flags: dict) -> dict:
    """One-shot application of SM_TRACK_CREDITS for every sm_ outcome flag
    present in `flags`. Stamps `sm_stakeholder_credits_applied` (a list of
    the flags credited) into `flags` as the double-apply guard. Mutates the
    engine sub-states in place; returns a diagnostics dict."""
    already = set(flags.get("sm_stakeholder_credits_applied") or [])
    applied: list[dict] = []
    for flag, spec in SM_TRACK_CREDITS.items():
        if not flags.get(flag) or flag in already:
            continue
        for npc_id in spec.get("npc", []):
            st = (npc_master_state.get("npcs") or {}).get(npc_id)
            if st is not None and st.get("trust_initialised"):
                st["trust"] = round(max(0.0, min(100.0, float(st.get("trust", 50.0)) + spec["trust"])), 2)
        for agent_id in spec.get("agents", []):
            ag = (agent_master_state.get("agents") or {}).get(agent_id)
            if ag is not None and ag.get("triggered_round") is None:
                ag["tolerance"] = round(max(0.0, min(100.0, float(ag.get("tolerance", 50.0)) + spec["tolerance"])), 1)
        already.add(flag)
        applied.append({"flag": flag, "trust": spec["trust"], "tolerance": spec["tolerance"]})
    if applied:
        flags["sm_stakeholder_credits_applied"] = sorted(already)
    return {"applied": applied}


# ═══════════════════════════════════════════════════════════════
#  F2 — CONTINUOUS STAKEHOLDER → SLO FEEDBACK (SPEC §2)
# ═══════════════════════════════════════════════════════════════

# Per-round SLO pressure by escalation TIER INDEX (0 = most cooperative tier,
# 3 = most hostile). Indexed by position in each NPC's `escalation_levels` so it
# is robust to NPC-specific action names (activist "hostile" vs journalist
# "hostile" sit at different severities). A cooperative stakeholder actively
# rebuilds license (+); a hostile one erodes it (−). Weaker than a cascade delta.
PRESSURE_BY_TIER: tuple[float, ...] = (1.0, 0.0, -2.0, -3.5)


def _tier_index(npc_state: dict) -> int | None:
    """Position of the NPC's current escalation tier within its ordered levels."""
    action = npc_state.get("escalation_level")
    for i, level in enumerate(npc_state.get("profile", {}).get("escalation_levels", [])):
        if level.get("action") == action:
            return i
    return None


def _attached_bus(npc_id: str, bus_states: list[dict]) -> list[dict]:
    """
    BUs a stakeholder's pressure lands on. The community leader hits water/agri
    BUs (its constituency); regulator/investor/journalist act on the whole group.
    Falls back to all BUs so a stakeholder is never a no-op by accident.
    """
    if npc_id == "community_leader":
        water = [b for b in bus_states if b.get("water_dependency", 0) >= 40]
        return water or bus_states
    return bus_states


def apply_stakeholder_slo_feedback(
    npc_master_state: dict,
    bus_states: list[dict],
    round_number: int,
    cascaded_npc_ids: set[str] | None = None,
    coupling: float = 1.0,
) -> dict:
    """
    Continuous per-round SLO pressure from each stakeholder's escalation tier
    (SPEC F2 §2.2). This provides the *slope* of the reinforcing loop; cascades
    provide the *cliffs*.

    Correctness guards (SPEC §2.3):
      • Double-count: an NPC that triggers a cascade this round is SKIPPED here —
        its `social_license_delta` supersedes the continuous term, so no
        escalation is charged twice. Caller passes `cascaded_npc_ids`.
      • Bounds only: clamps to [0, 100]; does NOT apply the ≤50 social-tipping cap,
        which runs later in post_tick and must not be duplicated.
      • Idempotency: keyed on `round_number` via a marker in npc_master_state so a
        retried/re-entrant commit cannot apply the feedback twice.

    Returns {bu_id: {npc_id: delta}} for UI/debrief; mutates bus SLO in place.
    """
    if npc_master_state.get("slo_feedback_applied_round") == round_number:
        return {}
    cascaded = cascaded_npc_ids or set()

    deltas: dict[str, dict[str, float]] = {}
    for npc_id, npc_state in npc_master_state.get("npcs", {}).items():
        if npc_id in cascaded:
            continue  # cascade supersedes continuous feedback this round
        tier_idx = _tier_index(npc_state)
        if tier_idx is None:
            continue
        pressure = PRESSURE_BY_TIER[tier_idx] * coupling
        if pressure == 0.0:
            continue
        for bu in _attached_bus(npc_id, bus_states):
            prev = bu.get("social_license_score", 50)
            new = max(0.0, min(100.0, round(prev + pressure, 2)))
            applied = round(new - prev, 2)
            if applied:
                bu["social_license_score"] = new
                deltas.setdefault(bu["bu_id"], {})[npc_id] = applied

    npc_master_state["slo_feedback_applied_round"] = round_number
    return deltas


# ═══════════════════════════════════════════════════════════════
#  F6 — INTENT-FORWARD INTEL (SPEC §6): demand · leverage · trend
# ═══════════════════════════════════════════════════════════════

# Plain-language demand phrasing, keyed by the driver metric. THIS is the single
# source of truth (§6.4): the backend emits the sentence so the front-end never
# re-implements it and the two cannot drift. Every satisfaction-driver metric in
# NPC_PROFILES must appear here — the drift tripwire test enforces that.
_DEMAND_PHRASE: dict[str, str] = {
    "social_license_score":        "wants stronger community license and local trust",
    "carbon_intensity":            "wants faster decarbonisation",
    "governance_risk":             "wants tighter governance and disclosure",
    "group_reputation":            "wants the reputation risk addressed",
    "water_stress_index":          "wants water stewardship in the basin",
    "tnfd_disclosure_level":       "wants nature-related (TNFD) disclosure",
    "esg_linked_compensation_pct": "wants ESG-linked executive pay",
    "just_transition_fund":        "wants a funded just-transition commitment",
    "transparency":                "wants greater transparency",
}


def _leverage_label(salience: dict) -> dict:
    """Turn a Mitchell salience profile into words (no raw numbers on the card)."""
    p = float(salience.get("power", 0.5))
    u = float(salience.get("urgency", 0.5))
    l = float(salience.get("legitimacy", 0.5))

    def word(v: float) -> str:
        return "high" if v >= 0.66 else ("moderate" if v >= 0.4 else "low")

    attrs = {"power": p, "urgency": u, "legitimacy": l}
    hi = max(attrs, key=attrs.get)
    lo = min(attrs, key=attrs.get)
    if attrs[hi] - attrs[lo] < 0.15:
        label = f"{word(p)} power, urgency and legitimacy"
    else:
        label = f"{word(attrs[hi])} {hi}, {word(attrs[lo])} {lo}"
    return {"power": word(p), "urgency": word(u), "legitimacy": word(l), "label": label}


def build_stakeholder_intel(npc_master_state: dict, gs: dict, bus: list[dict]) -> list[dict]:
    """
    SPEC F6. For each named NPC emit a *readable* intel card — what they want
    (top unmet driver), how much leverage they hold (salience in words), and which
    way the relationship is trending — so players read the person, not a number.
    The raw satisfaction/trust scores are tucked into a `facilitator` sub-dict for
    the debrief view only. Pure/read-only: never mutates state.
    """
    cards: list[dict] = []
    for npc_id, st in npc_master_state.get("npcs", {}).items():
        profile = st.get("profile", {})
        _, diag = calc_npc_satisfaction(npc_id, st, gs, bus)
        drivers = diag.get("drivers", [])

        worst = min(drivers, key=lambda d: d["contribution"]) if drivers else None
        if worst and worst["contribution"] < 0:
            demand = _DEMAND_PHRASE.get(
                worst["metric"], f"wants improvement on {worst['metric'].replace('_', ' ')}"
            )
        else:
            demand = "broadly satisfied for now"

        inter = st.get("interactions", [])
        if len(inter) >= 2:
            delta = inter[-1].get("satisfaction", 50) - inter[-2].get("satisfaction", 50)
            trend = "improving" if delta > 1 else ("declining" if delta < -1 else "steady")
            arrow = "up" if delta > 1 else ("down" if delta < -1 else "flat")
        else:
            trend, arrow = "new", "flat"

        _trust = st.get("trust")
        cards.append({
            "npc_id": npc_id,
            "name": profile.get("name", npc_id),
            "title": profile.get("title", ""),
            "icon": profile.get("icon", ""),
            "escalation_level": st.get("escalation_level", "neutral"),
            "demand": demand,
            "leverage": _leverage_label(profile.get("salience", {})),
            "trend": trend,
            "trend_direction": arrow,
            # numeric scores are intentionally NOT on the player card (§6.2)
            "facilitator": {
                "satisfaction": round(float(diag.get("satisfaction", 50)), 1),
                "trust": round(float(_trust), 1) if isinstance(_trust, (int, float)) else None,
            },
        })
    return cards


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
