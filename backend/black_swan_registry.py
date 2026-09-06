"""
Muressons Global Corporation — Black Swan Event Registry (PHASE-1)
Stochastic, low-probability, high-impact events that override normal
simulation dynamics. These are the "unknown unknowns" that test
executive resilience and buffer adequacy.

Theory base:
  - Taleb (2007): The Black Swan — impact of highly improbable events
  - Mandelbrot (1963): Fat-tailed distributions in financial markets
  - Weick & Sutcliffe (2007): Managing the Unexpected (HRO theory)

Architecture:
  Pure-function module. Events are evaluated each round via
  `evaluate_black_swans()` which is called from `process_tick()`.
  Facilitators can also inject specific events via admin API.

Difficulty Scaling:
  The difficulty_multiplier now applies ONLY to event IMPACTS (financial /
  reputational damage deltas), NOT to the probability of an event occurring.
  Probability is determined purely by base_prob + conditional modifiers + the
  hard 12% ceiling.  This ensures the game remains playable at all tiers.
"""

from __future__ import annotations
from typing import Any
import random
import math
from rng_util import event_rng  # GAME-4: deterministic per-cohort RNG
from config import BLACK_SWAN_MAX_EVENT_PROBABILITY


# ═══════════════════════════════════════════════════════════════
#  DIFFICULTY TIER CONFIGURATION
# ═══════════════════════════════════════════════════════════════

# FIN-08 (audit 2026-09-04, WP-23): sessions carry foundation / advanced /
# expert (the wizard, the presets, database default "advanced"), but this
# table was keyed easy / standard / expert, so every "Classroom (Easy)"
# cohort silently got the standard tier through the .get() fallback. Keyed
# by the session vocabulary now; the old names are accepted as aliases.
# The four keys no code read (treasury_floor, bailout_amount,
# natural_decay_rate, and the never-consulted npc_max_fine) are gone or
# wired: npc_max_fine caps the regulator's enforcement fine (FIN-09).
DIFFICULTY_TIERS = {
    "foundation": {
        "probability_multiplier": 0.5,
        "impact_multiplier": 0.7,
        "npc_max_fine": 6_000_000,
        "covenant_trigger_ratio": 4.5,
        "label": "Introductory",
    },
    "advanced": {
        "probability_multiplier": 1.0,
        "impact_multiplier": 1.0,
        "npc_max_fine": 12_000_000,
        "covenant_trigger_ratio": 3.5,
        "label": "Professional",
    },
    "expert": {
        "probability_multiplier": 1.5,
        "impact_multiplier": 1.3,
        "npc_max_fine": 25_000_000,
        "covenant_trigger_ratio": 2.5,
        "label": "Executive",
    },
}
_TIER_ALIASES = {"easy": "foundation", "standard": "advanced", "intermediate": "advanced",
                 "hard": "expert", "": "advanced", None: "advanced"}


def normalise_tier(tier: str | None) -> str:
    """The session vocabulary (foundation / advanced / expert) for any spelling."""
    key = (tier or "").strip().lower()
    if key in DIFFICULTY_TIERS:
        return key
    return _TIER_ALIASES.get(key, "advanced")


def get_difficulty_config(tier: str = "advanced") -> dict:
    """Return the difficulty configuration for a given tier (aliases accepted)."""
    return DIFFICULTY_TIERS[normalise_tier(tier)]


# ═══════════════════════════════════════════════════════════════
#  BLACK SWAN EVENT DEFINITIONS
# ═══════════════════════════════════════════════════════════════

BLACK_SWAN_EVENTS = {
    "sovereign_debt_crisis": {
        "id": "sovereign_debt_crisis",
        "title": "Sovereign Debt Crisis",
        "icon": "🏦",
        "description": (
            "A sovereign debt crisis in a key export market triggers capital "
            "flight, currency crash, and demand collapse across emerging markets."
        ),
        "trigger_conditions": {
            "round_range": [4, 8],
            "base_probability": 0.0267,  # was 0.08 ÷ 3
            "conditional_modifiers": [],   # Always possible
        },
        "impacts": {
            "treasury_pct_hit": -0.12,       # 12% of treasury
            "interest_rate_spike": 0.03,     # +300bps
            "revenue_pct_reduction": -0.10,  # 10% revenue loss
            "reputation_delta": -5,
        },
        "duration_rounds": 2,
        "cascading_npcs": [],
        "pedagogical_note": (
            "Tests treasury buffer adequacy and geographic diversification. "
            "Students who hoarded cash survive; those who over-invested are vulnerable."
        ),
        "narrative_trigger": (
            "🏦 **SOVEREIGN DEBT CRISIS**: A key export market has defaulted on "
            "government bonds. Currency has crashed 15%, trade finance is frozen, "
            "and demand has collapsed. Your treasury absorbs a {impact_amount} hit."
        ),
        "applicable_regions": None,  # None = all regions
    },

    "whistleblower_scandal": {
        "id": "whistleblower_scandal",
        "title": "Internal Whistleblower Scandal",
        "icon": "🔔",
        "description": (
            "A senior executive whistleblower reveals systematic greenwashing "
            "of ESG metrics to inflate sustainability ratings."
        ),
        "trigger_conditions": {
            "round_range": [3, 9],
            "base_probability": 0.0200,  # was 0.06 ÷ 3
            "conditional_modifiers": [
                {"metric": "governance_risk_avg", "above": 50, "probability_add": 0.12},
                {"flag": "greenwashing_detected", "probability_add": 0.15},
            ],
        },
        "impacts": {
            "reputation_delta": -20,
            "treasury_pct_hit": -0.08,       # Regulatory fine
            "social_license_delta": -15,
            "governance_risk_delta": +15,
        },
        "duration_rounds": 1,
        "cascading_npcs": ["journalist_hostile", "regulator_investigation"],
        "pedagogical_note": (
            "Governance failures compound. Students learn that greenwashing "
            "creates latent liability that can detonate at any time."
        ),
        "narrative_trigger": (
            "🔔 **WHISTLEBLOWER SCANDAL**: A former VP of Sustainability has gone "
            "public with evidence of systematic ESG metric manipulation. "
            "Regulators are launching an investigation. Share price drops {impact_pct}%."
        ),
        "applicable_regions": None,
    },

    "pandemic_wave": {
        "id": "pandemic_wave",
        "title": "Pandemic Disruption Wave",
        "icon": "🦠",
        "description": (
            "A novel pathogen disrupts global supply chains and workforce "
            "availability. Physical operations severely impacted."
        ),
        "trigger_conditions": {
            "round_range": [5, 9],
            "base_probability": 0.0200,  # was 0.06 ÷ 3
            "conditional_modifiers": [],
        },
        "impacts": {
            "workforce_availability_pct": 0.70,  # 30% workforce reduction
            "opex_pct_increase": 0.15,            # 15% OPEX surge
            "revenue_pct_reduction": -0.08,
            "burnout_delta": +20,
        },
        "duration_rounds": 2,
        "bu_differential": True,    # Physical BUs hit harder
        "cascading_npcs": ["community_leader_concerned"],
        "pedagogical_note": (
            "Tests operational resilience and workforce investment history. "
            "Companies with high burnout pre-pandemic experience cascading failures."
        ),
        "narrative_trigger": (
            "🦠 **PANDEMIC DISRUPTION**: A novel respiratory pathogen forces "
            "facility shutdowns. {workforce_pct}% of your workforce is unavailable. "
            "OPEX surges {opex_pct}% from health & safety measures."
        ),
        "applicable_regions": None,
    },

    "ai_disruption_wave": {
        "id": "ai_disruption_wave",
        "title": "AI Disruption Wave",
        "icon": "🤖",
        "description": (
            "Generative AI breakthroughs displace operational roles while "
            "creating windfall for software-enabled business units."
        ),
        "trigger_conditions": {
            "round_range": [6, 10],
            "base_probability": 0.0333,  # was 0.10 ÷ 3
            "conditional_modifiers": [
                {"flag": "ethical_ai_overhaul", "probability_add": -0.05},
                {"flag": "ai_monetised", "probability_add": +0.08},
            ],
        },
        "impacts": {
            "software_revenue_boost_pct": 0.20,
            "operations_workforce_displacement_pct": 0.15,
            "burnout_delta": +10,
            "governance_risk_delta": +8,
        },
        "duration_rounds": 1,
        "bu_differential": True,
        "cascading_npcs": ["gen_z_employee_concerned"],
        "pedagogical_note": (
            "Tests whether students invested in ethical AI infrastructure. "
            "Those who did ethical overhaul are better positioned."
        ),
        "narrative_trigger": (
            "🤖 **AI DISRUPTION WAVE**: A breakthrough AI model automates 15% "
            "of operational roles. Software BU revenue surges 20%, but industrial "
            "BUs face workforce displacement and ethics scrutiny."
        ),
        "applicable_regions": None,
    },

    "climate_litigation": {
        "id": "climate_litigation",
        "title": "Climate Litigation Ruling",
        "icon": "⚖️",
        "description": (
            "A landmark court ruling holds your company liable for climate "
            "damages under the 'polluter pays' principle."
        ),
        "trigger_conditions": {
            "round_range": [7, 10],
            "base_probability": 0.0167,  # was 0.05 ÷ 3
            "conditional_modifiers": [
                {"metric": "carbon_intensity_avg", "above": 60, "probability_add": 0.12},
                {"metric": "carbon_intensity_avg", "above": 80, "probability_add": 0.15},
            ],
        },
        "impacts": {
            "treasury_flat_hit": -8_000_000,
            "stranded_asset_writedown_pct": 0.10,
            "reputation_delta": -10,
            "governance_risk_delta": +5,
        },
        "duration_rounds": 1,
        "cascading_npcs": ["activist_investor_hostile", "regulator_monitoring"],
        "pedagogical_note": (
            "Sabin Center tracks 2,500+ climate cases filed globally. "
            "High carbon intensity companies face increasing legal exposure."
        ),
        "narrative_trigger": (
            "⚖️ **CLIMATE LITIGATION**: A court rules Muressons liable for "
            "climate damages under the 'duty of care' doctrine. Legal costs: "
            "${legal_cost:,.0f}. {writedown_pct}% of carbon-intensive assets written down."
        ),
        "applicable_regions": None,
    },

    "supply_chain_embargo": {
        "id": "supply_chain_embargo",
        "title": "Critical Mineral Embargo",
        "icon": "🚫",
        "description": (
            "A geopolitical crisis triggers export restrictions on critical "
            "minerals essential to Electronics and Pharma manufacturing."
        ),
        "trigger_conditions": {
            "round_range": [4, 9],
            "base_probability": 0.0233,  # was 0.07 ÷ 3
            "conditional_modifiers": [
                {"metric": "supply_chain_transparency", "below": 40, "probability_add": 0.10},
            ],
        },
        "impacts": {
            "affected_bus": ["electronics", "pharma"],
            "revenue_pct_reduction_targeted": -0.15,
            "opex_pct_increase_targeted": 0.10,
            "supply_chain_transparency_delta": -10,
        },
        "duration_rounds": 2,
        "cascading_npcs": [],
        "pedagogical_note": (
            "Tests supply chain diversification and transparency investment. "
            "Students who invested in supply chain mapping recover faster."
        ),
        "narrative_trigger": (
            "🚫 **CRITICAL MINERAL EMBARGO**: A major supplier nation has "
            "imposed export restrictions on rare earth elements. Electronics "
            "and Pharma BUs face 15% revenue loss and 10% OPEX increase."
        ),
        "applicable_regions": None,
    },

    "cyber_attack": {
        "id": "cyber_attack",
        "title": "Ransomware Attack",
        "icon": "💀",
        "description": (
            "A sophisticated ransomware group has encrypted critical systems "
            "across all business units."
        ),
        "trigger_conditions": {
            "round_range": [3, 10],
            "base_probability": 0.0233,  # was 0.07 ÷ 3
            "conditional_modifiers": [
                {"metric": "governance_risk_avg", "above": 45, "probability_add": 0.08},
            ],
        },
        "impacts": {
            "treasury_flat_hit": -5_000_000,
            "revenue_pct_reduction": -0.05,
            "reputation_delta": -8,
            "governance_risk_delta": +12,
        },
        "duration_rounds": 1,
        "cascading_npcs": ["regulator_investigation", "journalist_hostile"],
        "pedagogical_note": (
            "Cyber risk correlates with governance quality. Companies with "
            "low governance risk scores have better incident response."
        ),
        "narrative_trigger": (
            "💀 **RANSOMWARE ATTACK**: Critical systems encrypted across all BUs. "
            "Ransom demand: $5M. Operations disrupted for {duration} round(s). "
            "Regulators demand explanation of cyber governance failures."
        ),
        "applicable_regions": None,
    },

    "social_media_boycott": {
        "id": "social_media_boycott",
        "title": "Viral Consumer Boycott",
        "icon": "📱",
        "description": (
            "A viral social media campaign calls for consumer boycott of "
            "Muressons products over labour practices."
        ),
        "trigger_conditions": {
            "round_range": [4, 9],
            "base_probability": 0.0167,  # was 0.05 ÷ 3
            "conditional_modifiers": [
                {"metric": "social_license_avg", "below": 40, "probability_add": 0.15},
                {"metric": "group_reputation", "below": 35, "probability_add": 0.12},
            ],
        },
        "impacts": {
            "affected_bus": ["consumer_goods"],
            "revenue_pct_reduction_targeted": -0.20,
            "reputation_delta": -12,
            "social_license_delta": -10,
        },
        "duration_rounds": 1,
        "cascading_npcs": ["journalist_hostile", "community_leader_concerned"],
        "pedagogical_note": (
            "Demonstrates the asymmetry of social media — years of brand "
            "building destroyed in days. SLO is the best defence."
        ),
        "narrative_trigger": (
            "📱 **VIRAL BOYCOTT**: #BoycottMuressons is trending globally after "
            "an undercover video from a Consumer Goods supplier goes viral. "
            "Consumer Goods revenue drops 20%. Brand value under siege."
        ),
        "applicable_regions": None,
    },

    # ── Region-specific events ───────────────────────────────────

    "asean_trade_dispute": {
        "id": "asean_trade_dispute",
        "title": "ASEAN Trade Corridor Dispute",
        "icon": "🚢",
        "description": (
            "A territorial dispute in the South China Sea disrupts "
            "shipping lanes used by ASEAN-based supply chains."
        ),
        "trigger_conditions": {
            "round_range": [3, 8],
            "base_probability": 0.0333,  # was 0.10 ÷ 3
            "conditional_modifiers": [],
        },
        "impacts": {
            "treasury_pct_hit": -0.08,
            "opex_pct_increase": 0.12,
            "revenue_pct_reduction": -0.06,
            "reputation_delta": -4,
        },
        "duration_rounds": 2,
        "cascading_npcs": [],
        "pedagogical_note": (
            "Tests geographic diversification. ASEAN players must invest "
            "in alternative shipping routes and local buffer stocks."
        ),
        "narrative_trigger": (
            "🚢 **ASEAN TRADE DISPUTE**: Escalating tensions in the South China Sea "
            "have forced container ships onto longer, more expensive routes. "
            "OPEX surges {opex_pct}%. Treasury hit: {impact_amount}."
        ),
        "applicable_regions": ["asean"],
    },

    "south_asia_monsoon_crisis": {
        "id": "south_asia_monsoon_crisis",
        "title": "South Asia Extreme Monsoon",
        "icon": "🌧️",
        "description": (
            "An extreme monsoon season devastates agricultural supply chains "
            "and forces factory closures across South Asia."
        ),
        "trigger_conditions": {
            "round_range": [2, 7],
            "base_probability": 0.0300,  # was 0.09 ÷ 3
            "conditional_modifiers": [
                {"metric": "governance_risk_avg", "above": 40, "probability_add": 0.06},
            ],
        },
        "impacts": {
            "opex_pct_increase": 0.10,
            "revenue_pct_reduction": -0.08,
            "social_license_delta": -6,
            "burnout_delta": +12,
        },
        "duration_rounds": 2,
        "bu_differential": True,
        "cascading_npcs": ["community_leader_concerned"],
        "pedagogical_note": (
            "South Asian businesses face systemic climate-physical risk. "
            "Students learn that climate adaptation spending is an insurance premium."
        ),
        "narrative_trigger": (
            "🌧️ **EXTREME MONSOON**: Record rainfall has flooded industrial zones "
            "across South Asia. Factory closures, supply disruption, and community "
            "health impacts push OPEX up {opex_pct}% for {duration} round(s)."
        ),
        "applicable_regions": ["south_asia"],
    },

    "europe_carbon_border_tax": {
        "id": "europe_carbon_border_tax",
        "title": "EU Carbon Border Adjustment Mechanism",
        "icon": "🌿",
        "description": (
            "The EU's Carbon Border Adjustment Mechanism (CBAM) "
            "imposes tariffs on carbon-intensive imports, raising costs "
            "for Europe-facing business units."
        ),
        "trigger_conditions": {
            "round_range": [4, 9],
            "base_probability": 0.0367,  # was 0.11 ÷ 3
            "conditional_modifiers": [
                {"metric": "carbon_intensity_avg", "above": 50, "probability_add": 0.10},
            ],
        },
        "impacts": {
            "treasury_flat_hit": -4_000_000,
            "opex_pct_increase": 0.08,
            "reputation_delta": -6,
            "governance_risk_delta": +5,
        },
        "duration_rounds": 1,
        "cascading_npcs": ["eu_regulators", "activist_investor_hostile"],
        "pedagogical_note": (
            "CBAM is now live in transition. High-carbon European businesses "
            "face both compliance costs and reputational risk from institutional "
            "investors subject to EU Taxonomy alignment obligations."
        ),
        "narrative_trigger": (
            "🌿 **EU CBAM TARIFF**: The Carbon Border Adjustment Mechanism now "
            "applies to your European operations. Carbon surcharge: {impact_amount}. "
            "OPEX increases {opex_pct}% to meet compliance standards."
        ),
        "applicable_regions": ["europe"],
    },

    "north_america_sec_climate_rule": {
        "id": "north_america_sec_climate_rule",
        "title": "SEC Climate Disclosure Enforcement",
        "icon": "📋",
        "description": (
            "The SEC enforces its mandatory climate risk disclosure rules, "
            "triggering audit requirements and potential restatements for "
            "North American-listed entities."
        ),
        "trigger_conditions": {
            "round_range": [5, 9],
            "base_probability": 0.0267,  # was 0.08 ÷ 3
            "conditional_modifiers": [
                {"metric": "governance_risk_avg", "above": 45, "probability_add": 0.10},
                {"flag": "greenwashing_detected", "probability_add": 0.12},
            ],
        },
        "impacts": {
            "treasury_flat_hit": -6_000_000,
            "reputation_delta": -10,
            "governance_risk_delta": +10,
            "social_license_delta": -5,
        },
        "duration_rounds": 1,
        "cascading_npcs": ["regulator_investigation", "activist_investor_hostile"],
        "pedagogical_note": (
            "SEC climate disclosure applies to all US-listed entities. "
            "Students who invested in governance infrastructure are better "
            "positioned to respond quickly without costly restatements."
        ),
        "narrative_trigger": (
            "📋 **SEC CLIMATE ENFORCEMENT**: The Securities and Exchange Commission "
            "has issued a deficiency notice citing incomplete Scope 3 disclosures. "
            "Remediation costs: {impact_amount}. Governance risk spikes."
        ),
        "applicable_regions": ["north_america"],
    },

    "africa_resource_nationalisation": {
        "id": "africa_resource_nationalisation",
        "title": "African Resource Nationalisation Wave",
        "icon": "⛏️",
        "description": (
            "A coalition of African nations enacts new resource "
            "nationalisation laws, threatening assets and licences "
            "held by foreign multinationals."
        ),
        "trigger_conditions": {
            "round_range": [3, 9],
            "base_probability": 0.0233,  # was 0.07 ÷ 3
            "conditional_modifiers": [
                {"metric": "social_license_avg", "below": 45, "probability_add": 0.10},
            ],
        },
        "impacts": {
            "treasury_pct_hit": -0.10,
            "revenue_pct_reduction": -0.07,
            "reputation_delta": -8,
            "social_license_delta": -10,
        },
        "duration_rounds": 2,
        "cascading_npcs": ["community_leader_concerned", "regulator_monitoring"],
        "pedagogical_note": (
            "Social licence to operate is the primary defence against "
            "nationalisation risk. Students learn that community investment "
            "and local equity participation are value-preserving, not altruistic."
        ),
        "narrative_trigger": (
            "⛏️ **RESOURCE NATIONALISATION**: Three African partner governments "
            "have enacted mining and resource sector nationalisation bills. "
            "Treasury hit: {impact_amount}. Operating licences under review."
        ),
        "applicable_regions": ["africa"],
    },
}


# ═══════════════════════════════════════════════════════════════
#  BLACK SWAN EVALUATION ENGINE
# ═══════════════════════════════════════════════════════════════

# Hard ceiling on effective probability for any single Black Swan event per round.
# Prevents conditional modifier stacking from making events near-certain even
# for teams in severe distress — preserves game playability.
_MAX_EVENT_PROBABILITY: float = BLACK_SWAN_MAX_EVENT_PROBABILITY


def evaluate_black_swans(
    gs: dict,
    bus: list[dict],
    round_number: int,
    difficulty_tier: str = "advanced",
    active_black_swans: list[dict] | None = None,
    forced_event_id: str | None = None,
    region_id: str | None = None,
) -> dict:
    """
    Evaluate all Black Swan events for this round.
    Returns dict with triggered events and their impacts.

    Parameters:
        gs: Current global state
        bus: Current business unit states
        round_number: Current round number
        difficulty_tier: Difficulty tier — applies ONLY to impact magnitude,
            NOT to probability. This ensures every difficulty tier has the
            same base risk of events occurring; harder tiers hurt more when
            they do occur.
        active_black_swans: Currently active multi-round events
        forced_event_id: If set, forces this specific event (facilitator injection)
        region_id: If set, filters events to those applicable to this region

    Cool-down contract:
        If any Black Swan fired in round N, the key
        ``gs["active_event_flags"]["last_black_swan_round"]`` is set to N.
        In round N+1, all stochastic rolls are skipped (forced events still fire).
        This guarantees at least one grace round between consecutive Black Swans.
    """
    difficulty = get_difficulty_config(difficulty_tier)
    # ── Difficulty isolation: impact only, NOT probability ──────────────────
    # prob_mult is intentionally NOT read here — see docstring above.
    impact_mult = difficulty["impact_multiplier"]
    flags = gs.get("active_event_flags", {})
    n = max(len(bus), 1)

    # ── Global 1-round cool-down check ─────────────────────────────────────
    # If a Black Swan fired last round, skip all stochastic rolls this round.
    last_bs_round = flags.get("last_black_swan_round", -999)
    in_cooldown = (last_bs_round == round_number - 1)

    # Compute aggregate metrics for conditional modifiers
    metrics = {
        "governance_risk_avg": sum(bu.get("governance_risk_score", 20) for bu in bus) / n,
        "carbon_intensity_avg": sum(bu.get("carbon_intensity", 50) for bu in bus) / n,
        "social_license_avg": sum(bu.get("social_license_score", 50) for bu in bus) / n,
        "group_reputation": gs.get("group_reputation", 50),
        # IMP-11 (WP-23): the engine writes `supply_chain_transparency`; this
        # read a key nobody wrote (…_avg), so the +10 pp embargo modifier
        # applied forever regardless of the audits the team had done.
        "supply_chain_transparency": gs.get("active_event_flags", {}).get(
            "supply_chain_transparency",
            gs.get("active_event_flags", {}).get("supply_chain_transparency_avg", 30),
        ),
    }
    # FLAG-8 (WP-23): option flags live in rN_flags / rN_pillar_flags LISTS;
    # a top-level key test never saw them, so ethical_ai_overhaul's −5 pp on
    # the AI-disruption wave never applied. Flatten once, the way round_logic does.
    try:
        from flag_utils import collect_all_flags as _collect_all_flags
        _held_flags = set(_collect_all_flags(flags))
    except Exception:
        _held_flags = set()

    triggered_events = []
    event_narratives = []
    total_treasury_impact = 0
    total_reputation_impact = 0

    # Track already-active event types to prevent duplicates
    active_types = set()
    if active_black_swans:
        for active in active_black_swans:
            active_types.add(active.get("event_id"))

    for event_id, event in BLACK_SWAN_EVENTS.items():
        # Skip already-active events
        if event_id in active_types:
            continue

        # Region filter: skip events that don't apply to this region
        applicable_regions = event.get("applicable_regions")
        if applicable_regions is not None and region_id:
            if region_id not in applicable_regions:
                continue
        elif applicable_regions is not None and not region_id:
            # Region-specific event but no region set on session — skip it
            continue

        tc = event["trigger_conditions"]

        # Check round range
        r_range = tc.get("round_range", [1, 10])
        if round_number < r_range[0] or round_number > r_range[1]:
            continue

        is_forced = forced_event_id == event_id

        # ── Cool-down gate: suppress stochastic rolls for one grace round ──
        # Forced facilitator injections bypass the cool-down intentionally.
        if in_cooldown and not is_forced:
            continue

        # ── Probability calculation (difficulty-independent) ───────────────
        base_prob = tc.get("base_probability", 0.05)
        effective_prob = base_prob  # difficulty multiplier NOT applied here

        # Apply conditional modifiers
        for mod in tc.get("conditional_modifiers", []):
            if "metric" in mod:
                metric_val = metrics.get(mod["metric"], 0)
                if "above" in mod and metric_val > mod["above"]:
                    effective_prob += mod["probability_add"]
                elif "below" in mod and metric_val < mod["below"]:
                    effective_prob += mod["probability_add"]
            elif "flag" in mod:
                flag_set = flags.get("flags_set", [])
                flag_list = flag_set if isinstance(flag_set, list) else []
                # Wave 3 (WAVE2 residual): TRUTH, not key membership — since FIN-13
                # the engine writes some flags every tick with a False value, and
                # `mod["flag"] in flags` would have counted them as set.
                if bool(flags.get(mod["flag"])) or mod["flag"] in flag_list or mod["flag"] in _held_flags:
                    effective_prob += mod["probability_add"]

        # ── Hard probability ceiling: max 12% regardless of penalty stacking ─
        effective_prob = max(0.0, min(_MAX_EVENT_PROBABILITY, effective_prob))

        # Roll the dice (or force). GAME-4: per-event seeded stream so all teams
        # in a cohort face the same black-swan luck (independent per event_id, so
        # differing per-team probabilities never desync each other's rolls).
        roll = round(event_rng(flags, round_number, f"blackswan:{event_id}").random(), 4)

        if roll < effective_prob or is_forced:
            # Event triggered!
            impacts = event["impacts"]
            treasury = gs.get("corporate_treasury", 0)

            # ── Impact calculation — difficulty multiplier applied here only ──
            treasury_hit = 0
            if "treasury_pct_hit" in impacts:
                treasury_hit += round(treasury * abs(impacts["treasury_pct_hit"]) * impact_mult, 2)
            if "treasury_flat_hit" in impacts:
                treasury_hit += round(abs(impacts["treasury_flat_hit"]) * impact_mult, 2)

            rep_hit = round(impacts.get("reputation_delta", 0) * impact_mult, 1)
            slo_hit = round(impacts.get("social_license_delta", 0) * impact_mult, 1)
            gov_hit = round(impacts.get("governance_risk_delta", 0) * impact_mult, 1)

            # IMP-05 (WP-23): the revenue / OPEX percentages are FLOWS for the
            # event's duration (the engine records them as transients and
            # re-applies them while the event continues), and the headline
            # the player sees is the all-in cost — treasury hit plus the
            # flow erosion over the duration — not the cash hit alone, which
            # understated the real cost 4–5×.
            _dur = int(event.get("duration_rounds", 1) or 1)
            _aff = impacts.get("affected_bus", [])
            _flow_round = 0.0
            for _b in bus:
                _tgt = not _aff or _b["bu_id"] in _aff
                if _tgt:
                    _flow_round += abs(float(_b.get("revenue_base", 0) or 0) * float(impacts.get("revenue_pct_reduction", 0) or 0))
                    _flow_round += abs(float(_b.get("opex_base", 0) or 0) * float(impacts.get("opex_pct_increase", 0) or 0))
                if _b["bu_id"] in _aff:
                    _flow_round += abs(float(_b.get("revenue_base", 0) or 0) * float(impacts.get("revenue_pct_reduction_targeted", 0) or 0))
                    _flow_round += abs(float(_b.get("opex_base", 0) or 0) * float(impacts.get("opex_pct_increase_targeted", 0) or 0))
            _flow_round = round(_flow_round, 2)
            _flow_total = round(_flow_round * _dur, 2)
            _headline = round(treasury_hit + _flow_total, 2)

            triggered_event = {
                "event_id": event_id,
                "title": event["title"],
                "icon": event["icon"],
                "round_triggered": round_number,
                "duration_rounds": event.get("duration_rounds", 1),
                "rounds_remaining": event.get("duration_rounds", 1),
                "probability": round(effective_prob, 4),
                "roll": roll,
                "forced": is_forced,
                "difficulty_multiplier": impact_mult,
                "impacts_applied": {
                    "treasury_hit": treasury_hit,
                    "reputation_delta": rep_hit,
                    "social_license_delta": slo_hit,
                    "governance_risk_delta": gov_hit,
                    "interest_rate_spike": round(
                        impacts.get("interest_rate_spike", 0) * impact_mult, 4
                    ),
                    "revenue_pct_reduction": impacts.get("revenue_pct_reduction", 0),
                    "opex_pct_increase": impacts.get("opex_pct_increase", 0),
                    "revenue_pct_reduction_targeted": impacts.get("revenue_pct_reduction_targeted", 0),
                    "opex_pct_increase_targeted": impacts.get("opex_pct_increase_targeted", 0),
                    "burnout_delta": round(impacts.get("burnout_delta", 0) * impact_mult, 1),
                    "affected_bus": impacts.get("affected_bus", []),
                    # IMP-05: the flow erosion this event costs per round, and
                    # the all-in headline (cash hit + flow × duration).
                    "flow_cost_per_round": _flow_round,
                    "flow_cost_total": _flow_total,
                    "headline_cost": _headline,
                },
                "cascading_npcs": event.get("cascading_npcs", []),
                "pedagogical_note": event.get("pedagogical_note", ""),
                "narrative": event.get("narrative_trigger", "").format(
                    impact_amount=f"${_headline:,.0f}",
                    impact_pct=round(abs(impacts.get("treasury_pct_hit", 0)) * 100, 1),
                    legal_cost=abs(impacts.get("treasury_flat_hit", 0)),
                    writedown_pct=round(impacts.get("stranded_asset_writedown_pct", 0) * 100, 1),
                    workforce_pct=round(
                        (1 - impacts.get("workforce_availability_pct", 1)) * 100, 0
                    ),
                    opex_pct=round(impacts.get("opex_pct_increase", 0) * 100, 1),
                    duration=event.get("duration_rounds", 1),
                ),
            }

            triggered_events.append(triggered_event)
            event_narratives.append(triggered_event["narrative"])
            total_treasury_impact += treasury_hit
            total_reputation_impact += rep_hit

    # ── Cool-down write-back ───────────────────────────────────────────────
    # Persist the round number if any new event fired, so next round knows
    # to enforce the grace period.
    if triggered_events:
        gs.setdefault("active_event_flags", {})
        gs["active_event_flags"]["last_black_swan_round"] = round_number

    # Process continuing multi-round events
    continuing_events = []
    if active_black_swans:
        for active in active_black_swans:
            remaining = active.get("rounds_remaining", 0) - 1
            if remaining > 0:
                active_copy = {**active, "rounds_remaining": remaining}
                continuing_events.append(active_copy)

    return {
        "black_swan_evaluated": True,
        "events_checked": len(BLACK_SWAN_EVENTS),
        "events_triggered": triggered_events,
        "events_continuing": continuing_events,
        "total_new_events": len(triggered_events),
        "total_treasury_impact": round(total_treasury_impact, 2),
        "total_reputation_impact": round(total_reputation_impact, 1),
        "narratives": event_narratives,
        "difficulty_tier": difficulty_tier,
        "difficulty_label": difficulty.get("label", "Standard"),
        "in_cooldown": in_cooldown,
    }


def apply_black_swan_impacts(
    gs: dict,
    bus: list[dict],
    triggered_events: list[dict],
) -> dict:
    """
    Apply Black Swan event impacts to global and BU states (in-place mutation).
    Returns diagnostics dict.
    """
    diagnostics = {"events_applied": [], "total_treasury_drain": 0}
    n = max(len(bus), 1)

    for event in triggered_events:
        impacts = event.get("impacts_applied", {})

        # Treasury hit
        treasury_hit = impacts.get("treasury_hit", 0)
        if treasury_hit > 0:
            gs["corporate_treasury"] = round(gs["corporate_treasury"] - treasury_hit, 2)
            diagnostics["total_treasury_drain"] += treasury_hit

        # Reputation
        rep_delta = impacts.get("reputation_delta", 0)
        if rep_delta != 0:
            gs["group_reputation"] = max(0, min(100,
                round(gs["group_reputation"] + rep_delta, 2)))

        # Cost of capital spike
        rate_spike = impacts.get("interest_rate_spike", 0)
        if rate_spike > 0:
            gs["cost_of_capital"] = round(
                gs.get("cost_of_capital", 0.05) + rate_spike, 4
            )

        # BU-level impacts
        slo_delta = impacts.get("social_license_delta", 0)
        gov_delta = impacts.get("governance_risk_delta", 0)
        burnout_delta = impacts.get("burnout_delta", 0)
        revenue_pct = impacts.get("revenue_pct_reduction", 0)
        opex_pct = impacts.get("opex_pct_increase", 0)
        affected_bus_list = impacts.get("affected_bus", [])

        for bu in bus:
            is_targeted = not affected_bus_list or bu["bu_id"] in affected_bus_list

            if is_targeted:
                if slo_delta != 0:
                    bu["social_license_score"] = max(0, min(100,
                        round(bu["social_license_score"] + slo_delta, 2)))
                if gov_delta != 0:
                    bu["governance_risk_score"] = max(0, min(100,
                        round(bu["governance_risk_score"] + gov_delta, 2)))
                if burnout_delta != 0:
                    bu["staff_burnout_index"] = max(0, min(100,
                        round(bu.get("staff_burnout_index", 0) + burnout_delta, 2)))
                if revenue_pct != 0:
                    bu["revenue_base"] = round(
                        bu["revenue_base"] * (1 + revenue_pct), 2
                    )
                if opex_pct != 0:
                    bu["opex_base"] = round(
                        bu["opex_base"] * (1 + opex_pct), 2
                    )

        # Targeted BU impacts
        rev_targeted = impacts.get("revenue_pct_reduction_targeted", 0)
        opex_targeted = impacts.get("opex_pct_increase_targeted", 0)
        if rev_targeted != 0 or opex_targeted != 0:
            for bu in bus:
                if bu["bu_id"] in affected_bus_list:
                    if rev_targeted != 0:
                        bu["revenue_base"] = round(
                            bu["revenue_base"] * (1 + rev_targeted), 2
                        )
                    if opex_targeted != 0:
                        bu["opex_base"] = round(
                            bu["opex_base"] * (1 + opex_targeted), 2
                        )

        diagnostics["events_applied"].append({
            "event_id": event["event_id"],
            "treasury_hit": treasury_hit,
            "reputation_delta": rep_delta,
        })

    return diagnostics


def apply_black_swan_flows(bus: list[dict], events: list[dict]) -> list[tuple[str, str, float]]:
    """IMP-05 (WP-23): apply the revenue / OPEX percentage effects of the
    given events to the BU bases IN PLACE and return the deltas applied as
    (bu_id, field, delta) so the engine can record them as transients — a
    flow for this round, reversed from the persisted base at tick end. Used
    for the rounds an event CONTINUES (the trigger round is applied by
    apply_black_swan_impacts, whose deltas the engine records the same way)."""
    applied: list[tuple[str, str, float]] = []
    for event in events:
        impacts = event.get("impacts_applied", {}) or {}
        revenue_pct = impacts.get("revenue_pct_reduction", 0) or 0
        opex_pct = impacts.get("opex_pct_increase", 0) or 0
        rev_t = impacts.get("revenue_pct_reduction_targeted", 0) or 0
        opex_t = impacts.get("opex_pct_increase_targeted", 0) or 0
        affected = impacts.get("affected_bus", []) or []
        for bu in bus:
            is_targeted = not affected or bu["bu_id"] in affected
            if is_targeted and revenue_pct:
                before = bu["revenue_base"]
                bu["revenue_base"] = round(before * (1 + revenue_pct), 2)
                applied.append((bu["bu_id"], "revenue_base", round(bu["revenue_base"] - before, 2)))
            if is_targeted and opex_pct:
                before = bu["opex_base"]
                bu["opex_base"] = round(before * (1 + opex_pct), 2)
                applied.append((bu["bu_id"], "opex_base", round(bu["opex_base"] - before, 2)))
            if bu["bu_id"] in affected:
                if rev_t:
                    before = bu["revenue_base"]
                    bu["revenue_base"] = round(before * (1 + rev_t), 2)
                    applied.append((bu["bu_id"], "revenue_base", round(bu["revenue_base"] - before, 2)))
                if opex_t:
                    before = bu["opex_base"]
                    bu["opex_base"] = round(before * (1 + opex_t), 2)
                    applied.append((bu["bu_id"], "opex_base", round(bu["opex_base"] - before, 2)))
    return applied


def get_available_black_swans(round_number: int) -> list[dict]:
    """Return list of Black Swan events available for facilitator injection this round."""
    available = []
    for event_id, event in BLACK_SWAN_EVENTS.items():
        r_range = event["trigger_conditions"].get("round_range", [1, 10])
        if r_range[0] <= round_number <= r_range[1]:
            available.append({
                "event_id": event_id,
                "title": event["title"],
                "icon": event["icon"],
                "description": event["description"],
                "base_probability": event["trigger_conditions"]["base_probability"],
                "duration_rounds": event.get("duration_rounds", 1),
                "pedagogical_note": event.get("pedagogical_note", ""),
            })
    return available
