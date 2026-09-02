"""
Muressons Simulation — Stakeholder Sentiment Tracker

Tracks how each stakeholder group's attitude and salience shifts across rounds
based on player decisions (pillar choices) and black swan events.

Approach: Deterministic rule engine with template-based narratives.
LLM upgrade path: Replace _generate_narrative() with async LLM call when ready.

Theory base:
  - Mitchell, Agle & Wood (1997): Salience model (power, urgency, legitimacy)
  - Freeman (1984): Stakeholder management theory
  - Clarkson (1995): Primary/secondary stakeholder distinction
"""

from __future__ import annotations
from typing import Any
import copy


# ═════════════════════════════════════════════════════════════════
#  PILLAR FLAG → STAKEHOLDER SENTIMENT DELTA MAP
#  Maps flags_set from pillar decisions to per-stakeholder-type attitude deltas.
#  Stakeholder types are matched by substring of stakeholder id.
# ═════════════════════════════════════════════════════════════════

FLAG_SENTIMENT_RULES: list[dict] = [
    # Environmental actions
    {
        "flags": ["renewable_ppa_signed", "solar_investment", "fleet_electrified", "sbti_committed"],
        "stakeholder_matches": ["regulator", "investor", "ngo", "advocacy", "community"],
        "attitude_delta": +5,
        "narrative_template": "Your commitment to renewable energy has been noted positively.",
    },
    {
        "flags": ["fossil_status_quo", "carbon_deferred", "energy_cut"],
        "stakeholder_matches": ["regulator", "ngo", "advocacy", "community"],
        "attitude_delta": -6,
        "narrative_template": "Continued fossil fuel dependence is drawing criticism from environmental stakeholders.",
    },
    # Supply chain
    {
        "flags": ["deep_audit_completed", "blockchain_traceability", "supplier_remediation"],
        "stakeholder_matches": ["regulator", "ngo", "community", "buyer", "consumer"],
        "attitude_delta": +7,
        "narrative_template": "Supply chain transparency measures have improved stakeholder confidence.",
    },
    {
        "flags": ["electronics_blindspot", "supply_ignored"],
        "stakeholder_matches": ["ngo", "community", "regulator"],
        "attitude_delta": -8,
        "narrative_template": "Gaps in supply chain oversight are raising concerns.",
    },
    # Governance
    {
        "flags": ["materiality_aligned", "ethical_ai_overhaul", "privacy_by_design", "ai_ethics_board"],
        "stakeholder_matches": ["regulator", "investor", "analyst"],
        "attitude_delta": +6,
        "narrative_template": "Strong governance actions have improved your standing with oversight stakeholders.",
    },
    {
        "flags": ["materiality_ignored", "greenwash_risk", "quiet_patch", "ai_monetised"],
        "stakeholder_matches": ["regulator", "ngo", "investor", "media", "journalist"],
        "attitude_delta": -10,
        "narrative_template": "Governance shortfalls are eroding trust with key oversight stakeholders.",
    },
    # Social / HR
    {
        "flags": ["dei_program", "crisis_employee_support", "green_skills_academy", "emergency_trained"],
        "stakeholder_matches": ["employee", "community", "union", "farmer", "worker"],
        "attitude_delta": +6,
        "narrative_template": "People-focused investments are strengthening your social licence.",
    },
    {
        "flags": ["burnout_risk", "deny_and_deflect"],
        "stakeholder_matches": ["employee", "community", "media", "journalist"],
        "attitude_delta": -8,
        "narrative_template": "Workforce and community concerns are escalating due to recent decisions.",
    },
    # Financial inclusion / access
    {
        "flags": ["mobile_banking_rural", "microlending", "tiered_pricing", "generic_licensing"],
        "stakeholder_matches": ["community", "population", "ngo", "regulator"],
        "attitude_delta": +8,
        "narrative_template": "Access and inclusion initiatives are building goodwill with underserved communities.",
    },
    # Water / environment — Agriculture specific
    {
        "flags": ["drip_irrigation", "rainwater_harvesting"],
        "stakeholder_matches": ["farmer", "community", "regulator", "groundwater", "water"],
        "attitude_delta": +7,
        "narrative_template": "Water stewardship investments are being welcomed by farming and regulatory stakeholders.",
    },
    {
        "flags": ["no_water_action"],
        "stakeholder_matches": ["farmer", "community", "regulator", "groundwater", "water"],
        "attitude_delta": -7,
        "narrative_template": "Lack of water management action is causing growing concern among water-dependent stakeholders.",
    },
    # Decommissioning — Oil & Gas specific
    {
        "flags": ["decommissioning_trust", "decommission_plan"],
        "stakeholder_matches": ["regulator", "community", "investor", "decommission"],
        "attitude_delta": +6,
        "narrative_template": "Proactive decommissioning provisions are reassuring environmental regulators.",
    },
    {
        "flags": ["decommission_deferred"],
        "stakeholder_matches": ["regulator", "community", "investor", "ngo"],
        "attitude_delta": -9,
        "narrative_template": "Deferred decommissioning liabilities are a growing concern for regulators and investors.",
    },
]


# Black swan event → stakeholder sentiment shocks
BLACK_SWAN_SENTIMENT_SHOCKS: dict[str, list[dict]] = {
    "whistleblower_scandal": [
        {"stakeholder_matches": ["regulator", "investor", "analyst"], "attitude_delta": -15, "narrative": "Whistleblower revelations have severely damaged trust with oversight stakeholders."},
        {"stakeholder_matches": ["community", "employee", "worker"], "attitude_delta": -10, "narrative": "Internal scandals are undermining employee and community confidence."},
    ],
    "social_media_boycott": [
        {"stakeholder_matches": ["consumer", "community", "farmer", "population"], "attitude_delta": -18, "narrative": "The viral boycott has turned consumer sentiment sharply hostile."},
        {"stakeholder_matches": ["investor", "buyer"], "attitude_delta": -8, "narrative": "Brand damage from the boycott is affecting investor and buyer relations."},
    ],
    "cbam_shock": [
        {"stakeholder_matches": ["regulator", "buyer"], "attitude_delta": -10, "narrative": "CBAM non-readiness has damaged your regulatory standing in the EU market."},
    ],
    "south_asia_water_crisis": [
        {"stakeholder_matches": ["farmer", "community", "groundwater", "water"], "attitude_delta": -12, "narrative": "Water crisis has triggered intense anger from farming and local communities."},
    ],
    "africa_political_instability": [
        {"stakeholder_matches": ["community", "government", "national"], "attitude_delta": -8, "narrative": "Political instability has strained relationships with government stakeholders."},
    ],
    "asean_deforestation_ruling": [
        {"stakeholder_matches": ["regulator", "ngo", "advocacy"], "attitude_delta": -11, "narrative": "Deforestation ruling has intensified regulatory and NGO scrutiny."},
    ],
}


# ═════════════════════════════════════════════════════════════════
#  SENTIMENT ENGINE
# ═════════════════════════════════════════════════════════════════

def _matches_stakeholder(stakeholder_id: str, match_patterns: list[str]) -> bool:
    """Check if a stakeholder ID contains any of the match pattern substrings."""
    sid_lower = stakeholder_id.lower()
    return any(pattern.lower() in sid_lower for pattern in match_patterns)


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def apply_decision_sentiment(
    stakeholders: list[dict],
    flags_set: list[str],
    round_number: int = 1,
) -> list[dict]:
    """
    Apply sentiment deltas to stakeholder list based on flags set by a pillar decision.

    Parameters:
        stakeholders:  List of stakeholder dicts (each with 'id', 'attitude_score', etc.)
        flags_set:     List of flag strings from the pillar decision's flags_set field
        round_number:  Current game round (used for narrative context)

    Returns:
        Updated stakeholder list with modified attitude_score and appended narratives.
    """
    updated = copy.deepcopy(stakeholders)
    flags_lower = {f.lower() for f in flags_set}

    for rule in FLAG_SENTIMENT_RULES:
        rule_flags = {f.lower() for f in rule["flags"]}
        if not rule_flags.intersection(flags_lower):
            continue

        for sh in updated:
            if _matches_stakeholder(sh["id"], rule["stakeholder_matches"]):
                sh["attitude_score"] = _clamp(
                    sh.get("attitude_score", 50) + rule["attitude_delta"]
                )
                sh.setdefault("round_narratives", []).append({
                    "round": round_number,
                    "text": rule["narrative_template"],
                    "delta": rule["attitude_delta"],
                })

    return updated


def apply_black_swan_sentiment(
    stakeholders: list[dict],
    event_id: str,
    round_number: int = 1,
) -> list[dict]:
    """
    Apply black swan event sentiment shocks to the stakeholder list.

    Parameters:
        stakeholders: List of stakeholder dicts
        event_id:     The black swan event identifier (e.g. 'whistleblower_scandal')
        round_number: Current game round

    Returns:
        Updated stakeholder list.
    """
    updated = copy.deepcopy(stakeholders)
    shocks = BLACK_SWAN_SENTIMENT_SHOCKS.get(event_id, [])

    for shock in shocks:
        for sh in updated:
            if _matches_stakeholder(sh["id"], shock["stakeholder_matches"]):
                sh["attitude_score"] = _clamp(
                    sh.get("attitude_score", 50) + shock["attitude_delta"]
                )
                sh.setdefault("round_narratives", []).append({
                    "round": round_number,
                    "text": shock["narrative"],
                    "delta": shock["attitude_delta"],
                    "event": event_id,
                })

    return updated


def initialise_stakeholder_attitudes(stakeholders: list[dict]) -> list[dict]:
    """
    Seed initial attitude scores based on stakeholder quadrant and salience.

    Manage Closely → 55 (engaged, cautious)
    Keep Satisfied → 60 (satisfied but watching)
    Keep Informed  → 45 (neutral, under-engaged)
    Monitor        → 50 (baseline)
    """
    QUADRANT_DEFAULTS = {
        "manage_closely": 55,
        "keep_satisfied": 60,
        "keep_informed": 45,
        "monitor": 50,
    }

    initialised = copy.deepcopy(stakeholders)
    for sh in initialised:
        if "attitude_score" not in sh:
            sh["attitude_score"] = QUADRANT_DEFAULTS.get(sh.get("quadrant", "monitor"), 50)
        sh.setdefault("round_narratives", [])
    return initialised


def get_sentiment_summary(stakeholders: list[dict]) -> dict:
    """
    Return a summary of current stakeholder sentiment across the portfolio.

    Returns:
        Dict with overall sentiment, breakdown by quadrant, and at-risk stakeholders.
    """
    if not stakeholders:
        return {"overall": 50, "by_quadrant": {}, "at_risk": [], "champions": []}

    scores = [sh.get("attitude_score", 50) for sh in stakeholders]
    overall = round(sum(scores) / len(scores), 1)

    by_quadrant: dict[str, list[float]] = {}
    for sh in stakeholders:
        q = sh.get("quadrant", "unknown")
        by_quadrant.setdefault(q, []).append(sh.get("attitude_score", 50))

    quadrant_avg = {
        q: round(sum(vals) / len(vals), 1)
        for q, vals in by_quadrant.items()
    }

    at_risk = [
        {"id": sh["id"], "name": sh.get("name", sh["id"]), "score": sh.get("attitude_score", 50)}
        for sh in stakeholders
        if sh.get("attitude_score", 50) < 35
    ]

    champions = [
        {"id": sh["id"], "name": sh.get("name", sh["id"]), "score": sh.get("attitude_score", 50)}
        for sh in stakeholders
        if sh.get("attitude_score", 50) >= 75
    ]

    return {
        "overall": overall,
        "by_quadrant": quadrant_avg,
        "at_risk": sorted(at_risk, key=lambda x: x["score"]),
        "champions": sorted(champions, key=lambda x: -x["score"]),
        "total_stakeholders": len(stakeholders),
    }


def get_salience_weighted_score(stakeholders: list[dict]) -> float:
    """
    Compute a salience-weighted sentiment score.

    Power + Urgency + Legitimacy each add weight to the stakeholder's attitude.
    High-salience (manage_closely) stakeholders have 3x the weight of monitor stakeholders.
    """
    POWER_WEIGHT = {"high": 3, "medium": 2, "low": 1}
    SALIENCE_WEIGHT = {"manage_closely": 3, "keep_satisfied": 2, "keep_informed": 1, "monitor": 0.5}

    total_weight = 0.0
    weighted_sum = 0.0

    for sh in stakeholders:
        pw = POWER_WEIGHT.get(sh.get("power", "medium"), 2)
        sw = SALIENCE_WEIGHT.get(sh.get("quadrant", "monitor"), 1)
        weight = pw * sw
        weighted_sum += sh.get("attitude_score", 50) * weight
        total_weight += weight

    if total_weight == 0:
        return 50.0

    return round(weighted_sum / total_weight, 1)


# ── Engine entry points (F-41, found 2026-09-02 while making F-36 failures visible) ──
# engine.py's per-tick "Stakeholder Sentiment Update" block imported
# `update_stakeholder_sentiment` and `initialise_sentiment` from this module —
# names that were never defined here. The ImportError was swallowed by a bare
# `except Exception: pass`, so the block has never executed in production:
# no stakeholder attitude ever moved, `sentiment_stakeholders` was never
# written, and the F1 NPC sentiment bridge (npc_stakeholders._sentiment_bridge)
# always saw an empty list and did nothing. Two earlier fixes (2026-07-31,
# EVAL rec 5) edited this dead block believing it ran. These wrappers compose
# the functions that do exist, and fill the per-round fields the engine reads
# (attitude_delta_this_round, salience_label, sentiment_narrative).

_SALIENCE_LABELS = {"manage_closely": "Definitive", "keep_satisfied": "Dominant",
                    "keep_informed": "Dependent", "monitor": "Latent"}


def initialise_sentiment(stakeholders: list[dict]) -> list[dict]:
    """Seed attitude scores for a freshly resolved stakeholder list."""
    return initialise_stakeholder_attitudes(stakeholders)


def update_stakeholder_sentiment(
    stakeholders: list[dict],
    flags_set_this_round: list[str],
    round_number: int = 1,
    black_swans_triggered: list[dict] | None = None,
) -> list[dict]:
    """One round of sentiment movement: decision flags, then black swans.
    Returns a new list; each stakeholder carries the round's delta, its
    salience label and the most recent narrative line."""
    before = {sh.get("id"): float(sh.get("attitude_score", 50) or 50) for sh in stakeholders}
    updated = apply_decision_sentiment(stakeholders, list(flags_set_this_round or []), round_number)
    for swan in (black_swans_triggered or []):
        eid = (swan or {}).get("event_id") or (swan or {}).get("id") or ""
        if eid:
            updated = apply_black_swan_sentiment(updated, eid, round_number)
    for sh in updated:
        sid = sh.get("id")
        after = float(sh.get("attitude_score", 50) or 50)
        sh["attitude_delta_this_round"] = round(after - before.get(sid, after), 2)
        sh["salience_label"] = _SALIENCE_LABELS.get(sh.get("quadrant", "monitor"), "Latent")
        narratives = sh.get("round_narratives") or []
        this_round = [n for n in narratives if n.get("round") == round_number]
        sh["sentiment_narrative"] = (this_round[-1]["text"] if this_round else "")
    return updated
