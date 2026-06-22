"""
Muressons Global Corporation — Systemic Risk Engine (PHASE-1)
ESG-Adjusted WACC, Supply Chain Transparency, Employer Brand,
Materiality Shocks, Tipping Point Irreversibility, and NPC Cascading.

Theory: El Ghoul (2011), Sharfman & Fernando (2008), Rockström (2009)
Pure-function module. No I/O.
"""
from __future__ import annotations
from typing import Any
import math, random
from rng_util import event_rng  # GAME-4: deterministic per-cohort RNG


# ═══════════════════════════════════════════════════════════════
#  1. ESG-ADJUSTED WACC
# ═══════════════════════════════════════════════════════════════

def calc_esg_adjusted_wacc(
    base_wacc: float,
    carbon_intensity_avg: float,
    governance_risk_avg: float,
    social_license_avg: float,
    biodiversity_dependency: float = 0.0,
    supply_chain_transparency: float = 30.0,
) -> tuple[float, dict]:
    """
    ESG-Adjusted WACC = Base + Carbon_Premium + Gov_Premium - SLO_Discount + Nature_Premium
    Ranges: WACC 3%-15% (base 5%, ±10% ESG swing)
    """
    carbon_premium = max(0, (carbon_intensity_avg - 40) * 0.0008)
    gov_premium = max(0, (governance_risk_avg - 25) * 0.0006)
    slo_discount = max(0, (social_license_avg - 50) * 0.0003)
    nature_premium = max(0, biodiversity_dependency * (1 - supply_chain_transparency / 100) * 0.02)

    adjusted = base_wacc + carbon_premium + gov_premium - slo_discount + nature_premium
    adjusted = round(max(0.03, min(0.20, adjusted)), 4)  # FIX-C: raised cap from 15% to 20%

    return adjusted, {
        "base_wacc": base_wacc,
        "carbon_premium": round(carbon_premium, 4),
        "gov_premium": round(gov_premium, 4),
        "slo_discount": round(slo_discount, 4),
        "nature_premium": round(nature_premium, 4),
        "adjusted_wacc": adjusted,
        "wacc_delta_bps": round((adjusted - base_wacc) * 10000, 1),
        "annual_debt_service_impact": round((adjusted - base_wacc) * 50_000_000, 2),
    }


# ═══════════════════════════════════════════════════════════════
#  2. SUPPLY CHAIN TRANSPARENCY
# ═══════════════════════════════════════════════════════════════

def calc_supply_chain_transparency(
    current_score: float,
    flags: dict,
    round_number: int,
) -> tuple[float, dict]:
    """
    Supply Chain Transparency Score (0-100). Starts at 30.
    Improves via: deep audit (+20), blockchain (+15), materiality_aligned (+5)
    Degrades via: natural entropy (-3/round), scandal events (-25)
    """
    delta = -3.0  # Natural entropy

    flag_boosts = {
        "deep_audit_completed": 20.0,
        "blockchain_traceability": 15.0,
        "materiality_aligned": 5.0,
        "supply_chain_disruption_risk": -10.0,
        "deny_and_deflect": -15.0,
        "remediation_active": 8.0,
        "circular_redesign": 5.0,
        "epr_program": 3.0,
    }

    applied_boosts = {}
    for flag, boost in flag_boosts.items():
        if flag in flags or flag in (flags.get("flags_set", []) if isinstance(flags.get("flags_set"), list) else []):
            delta += boost
            applied_boosts[flag] = boost

    new_score = round(max(0, min(100, current_score + delta)), 2)
    return new_score, {
        "previous": current_score,
        "new": new_score,
        "delta": round(delta, 2),
        "entropy": -3.0,
        "boosts_applied": applied_boosts,
    }


# ═══════════════════════════════════════════════════════════════
#  3. EMPLOYER BRAND SCORE
# ═══════════════════════════════════════════════════════════════

def calc_employer_brand(
    group_reputation: float,
    avg_burnout: float,
    workforce_readiness: float,
) -> tuple[float, dict]:
    """
    Employer Brand = Rep × 0.4 + (100 - Burnout) × 0.3 + Readiness × 0.3
    Drives recruitment cost and talent retention across ALL BUs.
    """
    score = (
        group_reputation * 0.4
        + (100 - avg_burnout) * 0.3
        + workforce_readiness * 0.3
    )
    score = round(max(0, min(100, score)), 1)

    # Employer brand below 40 triggers recruitment cost premium
    recruitment_premium = 0.0
    if score < 40:
        recruitment_premium = round((40 - score) / 100 * 0.08, 4)

    return score, {
        "employer_brand_score": score,
        "components": {
            "reputation_contribution": round(group_reputation * 0.4, 1),
            "burnout_contribution": round((100 - avg_burnout) * 0.3, 1),
            "readiness_contribution": round(workforce_readiness * 0.3, 1),
        },
        "recruitment_cost_premium": recruitment_premium,
        "talent_risk_level": (
            "critical" if score < 25 else
            "high" if score < 40 else
            "moderate" if score < 60 else
            "healthy"
        ),
    }


# ═══════════════════════════════════════════════════════════════
#  4. SYSTEMIC TIPPING POINTS (IRREVERSIBILITY GATES)
# ═══════════════════════════════════════════════════════════════

TIPPING_THRESHOLDS = {
    "climate": {
        "warning":  {"carbon_intensity_avg": 65, "ehi_below": 45},
        "stressed": {"carbon_intensity_avg": 75, "ehi_below": 30},
        "tipped":   {"carbon_intensity_avg": 85, "ehi_below": 15},
    },
    "social": {
        "warning":  {"avg_slo": 35, "avg_burnout": 60},
        "stressed": {"avg_slo": 25, "avg_burnout": 75},
        "tipped":   {"avg_slo": 15, "avg_burnout": 90},
    },
    "financial": {
        "warning":  {"covenant_status": "amber"},
        "stressed": {"covenant_status": "red"},
        "tipped":   {"covenant_status": "breached"},
    },
}

# Once tipped, these permanent multipliers apply
IRREVERSIBILITY_PENALTIES = {
    "climate_tipped": {
        "ncd_interest_multiplier": 2.0,
        "carbon_tax_multiplier": 1.5,
        "reputation_ceiling": 60,
        "message": "🌡️ CLIMATE TIPPING POINT CROSSED: NCD costs permanently doubled.",
    },
    "social_tipped": {
        "strike_probability_floor": 0.30,
        "opex_surcharge_pct": 0.05,
        "social_license_ceiling": 50,
        "message": "✊ SOCIAL TIPPING POINT CROSSED: Permanent strike risk floor of 30%.",
    },
    "financial_tipped": {
        "borrowing_premium": 0.04,
        "capex_cap_multiplier": 0.50,
        "dividend_suspended": True,
        "message": "🏦 FINANCIAL TIPPING POINT CROSSED: Lender acceleration triggered.",
    },
}


def evaluate_tipping_points(
    gs: dict,
    bus: list[dict],
    current_tipped: dict | None = None,
) -> dict:
    """
    Evaluate all three tipping point dimensions.
    Once tipped, a dimension stays tipped permanently (irreversibility).
    """
    n = max(len(bus), 1)
    tipped = dict(current_tipped or {})
    transitions = []

    # Compute metrics
    avg_ci = sum(bu.get("carbon_intensity", 50) for bu in bus) / n
    avg_slo = sum(bu.get("social_license_score", 50) for bu in bus) / n
    avg_burnout = sum(bu.get("staff_burnout_index", 0) for bu in bus) / n
    ehi = gs.get("biodiversity_state", {}).get("ecosystem_health_index", 50)
    covenant = gs.get("active_event_flags", {}).get("covenant_status", "green")

    dimensions = {
        "climate": {"carbon_intensity_avg": avg_ci, "ehi": ehi},
        "social": {"avg_slo": avg_slo, "avg_burnout": avg_burnout},
        "financial": {"covenant_status": covenant},
    }

    for dim, metrics in dimensions.items():
        # Skip if already tipped (irreversible)
        if tipped.get(f"{dim}_tipped"):
            continue

        thresholds = TIPPING_THRESHOLDS[dim]
        tier = "none"

        for level in ["tipped", "stressed", "warning"]:
            level_thresholds = thresholds[level]
            met = True
            for key, val in level_thresholds.items():
                if key.endswith("_below"):
                    actual_key = key.replace("_below", "")
                    if metrics.get(actual_key, 100) > val:
                        met = False
                elif key == "covenant_status":
                    status_order = {"green": 0, "amber": 1, "red": 2, "breached": 3}
                    if status_order.get(metrics.get(key, "green"), 0) < status_order.get(val, 0):
                        met = False
                else:
                    if metrics.get(key, 0) < val:
                        met = False
            if met:
                tier = level
                break

        if tier == "tipped":
            tipped[f"{dim}_tipped"] = True
            penalty_key = f"{dim}_tipped"
            transitions.append({
                "dimension": dim,
                "new_tier": "tipped",
                "irreversible": True,
                "penalties": IRREVERSIBILITY_PENALTIES.get(penalty_key, {}),
                "message": IRREVERSIBILITY_PENALTIES.get(penalty_key, {}).get(
                    "message", f"⚠️ {dim.title()} tipping point crossed!"
                ),
            })

        tipped[f"{dim}_tier"] = tier

    return {
        "tipping_state": tipped,
        "transitions": transitions,
        "any_tipped": any(v for k, v in tipped.items() if k.endswith("_tipped") and v),
        "dimensions": {
            "climate": {"tier": tipped.get("climate_tier", "none"), "ci": round(avg_ci, 1), "ehi": round(ehi, 1)},
            "social": {"tier": tipped.get("social_tier", "none"), "slo": round(avg_slo, 1), "burnout": round(avg_burnout, 1)},
            "financial": {"tier": tipped.get("financial_tier", "none"), "covenant": covenant},
        },
    }


# ═══════════════════════════════════════════════════════════════
#  5. DOUBLE MATERIALITY SHOCKS
# ═══════════════════════════════════════════════════════════════

# ── Relative probability weights for the Double Materiality Shock pipeline ──
# These are *unitless multipliers* applied against NPC_SHOCK_BASE_PROB (config.py).
# effective_prob = min(NPC_SHOCK_MAX_PROB, weight × NPC_SHOCK_BASE_PROB)
#
# Weights preserve the original relative rank (stranded_asset is most likely,
# supply_chain is least likely) while decoupling absolute calibration from code.
# Original hardcoded probs: water=0.08, sc=0.06, bio=0.07, stranded=0.09
# Weights normalised to mean=1.0 against original mean of 0.075:
#   water:   0.08/0.075 ≈ 1.07 → 1.0 (neutral)
#   sc:      0.06/0.075 = 0.80 (lowest impact)
#   bio:     0.07/0.075 ≈ 0.93 → 0.9
#   stranded:0.09/0.075 = 1.20 (highest impact — IEA stranding is most severe)
# With NPC_SHOCK_BASE_PROB=0.05: effective range 4.0%–6.0%, capped at 8%.
MATERIALITY_SHOCKS = {
    "water_crisis": {
        "issue": "Water Stewardship",
        "financial_materiality_jump": 40,
        "impact_materiality_jump": 10,
        "narrative": (
            "🌊 **MATERIALITY SHOCK — Water Crisis**: Severe drought declared "
            "in 3 operational regions. Water stewardship leaps from low to "
            "critical financial materiality overnight."
        ),
        "forced_reallocation_pct": 0.10,
        "trigger_conditions": {
            "round_range": [4, 8],
            "probability_weight": 1.0,   # 1.0 × NPC_SHOCK_BASE_PROB = 5.0%
        },
    },
    "supply_chain_collapse": {
        "issue": "Supply Chain Human Rights",
        "financial_materiality_jump": 35,
        "impact_materiality_jump": 20,
        "narrative": (
            "⛓️ **MATERIALITY SHOCK — Supply Chain Collapse**: Tier-2 supplier "
            "factory collapse kills 47 workers. Human rights due diligence "
            "becomes existential financial risk."
        ),
        "forced_reallocation_pct": 0.08,
        "trigger_conditions": {
            "round_range": [3, 9],
            "probability_weight": 0.80,  # 0.80 × NPC_SHOCK_BASE_PROB = 4.0%
        },
    },
    "biodiversity_tipping": {
        "issue": "Biodiversity & Ecosystems",
        "financial_materiality_jump": 30,
        "impact_materiality_jump": 25,
        "narrative": (
            "🐝 **MATERIALITY SHOCK — Pollinator Collapse**: Pollinator "
            "populations crash in key agricultural regions. Pharma and Consumer "
            "Goods supply chains at immediate risk."
        ),
        "forced_reallocation_pct": 0.10,
        "trigger_conditions": {
            "round_range": [5, 9],
            "probability_weight": 0.90,  # 0.90 × NPC_SHOCK_BASE_PROB = 4.5%
        },
    },
    "stranded_asset_reclassification": {
        "issue": "Stranded Asset Exposure",
        "financial_materiality_jump": 45,
        "impact_materiality_jump": 15,
        "narrative": (
            "🏗️ **MATERIALITY SHOCK — Asset Stranding**: New IEA report reclassifies "
            "carbon-intensive industrial assets. 25% of PPE requires immediate "
            "impairment testing under IAS 36."
        ),
        "forced_reallocation_pct": 0.12,
        "trigger_conditions": {
            "round_range": [6, 10],
            "probability_weight": 1.20,  # 1.20 × NPC_SHOCK_BASE_PROB = 6.0%
        },
    },
}


# ── Hard ceiling on any single materiality shock per round ──────────────────
# Mirrors the pattern established in black_swan_registry._MAX_EVENT_PROBABILITY.
# Imported lazily here to avoid a circular import at module load time.
_NPC_SHOCK_CEILING_DEFAULT: float = 0.08   # fallback if config import fails


def evaluate_materiality_shocks(
    round_number: int,
    difficulty_tier: str = "standard",
    active_event_flags: dict | None = None,
) -> list[dict]:
    """
    Evaluate which Double Materiality Shocks trigger this round.

    Probability model (OI-2 refactor):
        effective_prob = min(NPC_SHOCK_MAX_PROB,
                             probability_weight × NPC_SHOCK_BASE_PROB)

    Key contracts:
    • NPC_SHOCK_BASE_PROB (config) is the single authoritative tuning dial.
    • Each event's probability_weight is a unitless relative multiplier (not
      an absolute probability); range 0.80–1.20 across the four events.
    • difficulty_multiplier is intentionally NOT applied to probability —
      difficulty makes shocks hurt more (impact), not happen more often.
    • NPC_SHOCK_MAX_PROB (8%) is a hard ceiling: no shock can exceed this
      rate regardless of accumulated conditional modifiers.
    • Per-event once-per-session gate: a shock that has already fired in this
      session is suppressed (stored in active_event_flags["fired_materiality
      _shocks"]). This prevents repetitive identical narratives and halves
      the expected per-run trigger count versus a pure per-round model.

    Args:
        round_number:        Current game round (1-10).
        difficulty_tier:     Session difficulty tier ("standard"/"expert"/"practice").
        active_event_flags:  Mutable global flags dict. Updated in-place with
                             fired_materiality_shocks list for cool-down tracking.
    """
    # ── Load config constants (lazy to avoid circular import at module top) ──
    try:
        from config import NPC_SHOCK_BASE_PROB, NPC_SHOCK_MAX_PROB
    except ImportError:
        NPC_SHOCK_BASE_PROB = 0.05
        NPC_SHOCK_MAX_PROB  = _NPC_SHOCK_CEILING_DEFAULT

    # ── Per-session cool-down: track which shocks have already fired ─────────
    # Stored as a list of shock_ids in active_event_flags for persistence.
    flags = active_event_flags if isinstance(active_event_flags, dict) else {}
    fired_this_session: list[str] = list(
        flags.get("fired_materiality_shocks", [])
    )

    triggered = []
    for shock_id, shock in MATERIALITY_SHOCKS.items():
        # ── Round-range gate ─────────────────────────────────────────────────
        tc      = shock["trigger_conditions"]
        r_range = tc.get("round_range", [1, 10])
        if round_number < r_range[0] or round_number > r_range[1]:
            continue

        # ── Once-per-session gate ────────────────────────────────────────────
        # Each materiality shock is a structural one-time event (IEA report,
        # factory collapse, drought declaration). Re-firing the same shock
        # in later rounds is narratively incoherent and statistically inflates
        # the trigger rate. Suppress after first occurrence.
        if shock_id in fired_this_session:
            continue

        # ── Probability calculation (config-routed, hard-capped) ─────────────
        # effective_prob = min(NPC_SHOCK_MAX_PROB, weight × NPC_SHOCK_BASE_PROB)
        # difficulty_multiplier intentionally excluded from probability path.
        weight        = tc.get("probability_weight", 1.0)
        raw_prob      = weight * NPC_SHOCK_BASE_PROB
        effective_prob = min(NPC_SHOCK_MAX_PROB, raw_prob)   # hard 8% ceiling

        # GAME-4: per-event seeded stream keyed on shock_id (deterministic per cohort).
        roll = event_rng(active_event_flags or {}, round_number, f"matshock:{shock_id}").random()
        if roll < effective_prob:
            triggered.append({
                "shock_id":                shock_id,
                "issue":                   shock["issue"],
                "narrative":               shock["narrative"],
                "financial_materiality_jump": shock["financial_materiality_jump"],
                "impact_materiality_jump":    shock["impact_materiality_jump"],
                "forced_reallocation_pct":    shock["forced_reallocation_pct"],
                "roll":                    round(roll, 4),
                "probability":             round(effective_prob, 4),
                "probability_weight":      weight,
                "npc_shock_base_prob":     NPC_SHOCK_BASE_PROB,
                "npc_shock_max_prob":      NPC_SHOCK_MAX_PROB,
                "ceiling_applied":         raw_prob > NPC_SHOCK_MAX_PROB,
            })
            fired_this_session.append(shock_id)

    # ── Write back fired shocks to flags for persistence ─────────────────────
    if isinstance(active_event_flags, dict):
        active_event_flags["fired_materiality_shocks"] = fired_this_session

    return triggered


# ═══════════════════════════════════════════════════════════════
#  6. NPC CASCADING REACTION LOGIC GATES
# ═══════════════════════════════════════════════════════════════

STAKEHOLDER_REACTION_GATES = {
    "activist_investor": {
        "divestment_campaign": {
            "conditions": [
                ("satisfaction", "<", 25),
            ],
            "persistence_rounds": 2,
            "action": "divestment_campaign",
            "effects": {
                "treasury_pct_hit": -0.05,
                "reputation_delta": -8,
                "cascading_triggers": ["journalist_hostile"],
            },
            "narrative": (
                "🦅 FutureFirst launches divestment campaign. Share price drops 5%. "
                "Financial media coverage amplifies reputational damage."
            ),
        },
        "proxy_fight": {
            "conditions": [
                ("satisfaction", "<", 15),
            ],
            "action": "proxy_fight",
            "effects": {
                "treasury_flat_hit": -2_000_000,
                "governance_risk_delta": -10,
                "board_composition_change": True,
                "cascading_triggers": ["regulator_monitoring"],
            },
            "narrative": (
                "🦅 FutureFirst files proxy contest. Three independent directors "
                "nominated. AGM costs: $2M. Governance actually improves."
            ),
        },
    },
    "regulator": {
        "enforcement_action": {
            "conditions": [
                ("satisfaction", "<", 20),
            ],
            "action": "enforcement_action",
            "effects": {
                "treasury_pct_hit": -0.04,
                "mandatory_disclosure": True,
                "cascading_triggers": ["journalist_hostile", "activist_investor_hostile"],
            },
            "narrative": (
                "🏛️ EU DG FISMA launches enforcement action. Fine: 4% of revenue. "
                "Mandatory enhanced disclosure requirements imposed."
            ),
        },
    },
    "community_leader": {
        "legal_injunction": {
            "conditions": [
                ("satisfaction", "<", 20),
            ],
            "action": "court_injunction",
            "effects": {
                "social_license_delta": -10,
                "reputation_delta": -5,
                "cascading_triggers": ["journalist_hostile"],
            },
            "narrative": (
                "👥 Community coalition files court injunction against facility operations. "
                "Social licence plummets. Media covers the story extensively."
            ),
        },
    },
    "gen_z_employee": {
        "mass_resignation": {
            "conditions": [
                ("satisfaction", "<", 20),
            ],
            "action": "mass_resignation",
            "effects": {
                "burnout_delta": +15,
                "opex_pct_increase": 0.08,
                "reputation_delta": -5,
                "cascading_triggers": ["journalist_concerned"],
            },
            "narrative": (
                "👩‍💻 Gen Z workforce initiates coordinated resignation. Agency costs "
                "surge 8%. #ToxicWorkplace trends on social media."
            ),
        },
    },
}


def evaluate_npc_cascades(
    npc_satisfaction: dict[str, float],
    round_number: int,
    active_cascades: list[dict] | None = None,
) -> list[dict]:
    """
    Evaluate NPC satisfaction against cascade thresholds.
    Returns list of triggered cascade events.
    """
    triggered = []
    active_ids = {c.get("action") for c in (active_cascades or [])}

    for npc_id, gates in STAKEHOLDER_REACTION_GATES.items():
        satisfaction = npc_satisfaction.get(npc_id, 50)

        for gate_id, gate in gates.items():
            if gate["action"] in active_ids:
                continue

            conditions_met = True
            for metric, op, threshold in gate["conditions"]:
                if metric == "satisfaction":
                    val = satisfaction
                else:
                    val = npc_satisfaction.get(metric, 50)

                if op == "<" and val >= threshold:
                    conditions_met = False
                elif op == ">" and val <= threshold:
                    conditions_met = False

            if conditions_met:
                triggered.append({
                    "npc_id": npc_id,
                    "action": gate["action"],
                    "gate_id": gate_id,
                    "satisfaction": round(satisfaction, 1),
                    "effects": gate["effects"],
                    "narrative": gate["narrative"],
                    "round_triggered": round_number,
                    "persistence_rounds": gate.get("persistence_rounds", 1),
                })

    return triggered


# ═══════════════════════════════════════════════════════════════
#  7. FORESHADOWING SIGNALS
# ═══════════════════════════════════════════════════════════════

FORESHADOWING_SIGNALS = {
    "materiality_accruing": {
        "source_flag": "materiality_aligned",
        "signal_round": 6,
        "message": "📊 Governance Premium Accruing: Your R2 materiality alignment is building toward a +0.10 M_R bonus at terminal valuation.",
        "category": "positive",
    },
    "audit_protection": {
        "source_flag": "deep_audit_completed",
        "signal_round": 3,
        "message": "🛡️ Audit Shield Active: Your deep audit from R1 has uncovered hidden supply chain risks. Crisis severity will be halved if contagion strikes.",
        "category": "positive",
    },
    "blindspot_warning": {
        "source_flag": "electronics_blindspot",
        "signal_round": 3,
        "message": "⚠️ Blind Spot Detected: Intelligence suggests unaudited risks in your Electronics supply chain. A scandal could be devastating.",
        "category": "warning",
    },
    "greenwash_exposure": {
        "source_flag": "greenwash_risk",
        "signal_round": 4,
        "message": "🟡 Greenwash Risk: ESG investment below 15% of revenue triggers scrutiny. Regulators and activists may act.",
        "category": "warning",
    },
    "synergy_building": {
        "source_flag": "early_decarboniser",
        "signal_round": 5,
        "message": "♻️ Decarbonisation Dividend: Your early supplier switch is generating cross-BU efficiency gains. Synergy bonus accruing for R7.",
        "category": "positive",
    },
    "insurance_trap": {
        "source_flag": "insurance_only",
        "signal_round": 7,
        "message": "⚠️ Resilience Gap: Insurance-only strategy has left you with ZERO physical climate protection. Resilience M_R bonus (-0.20) blocked at terminal valuation.",
        "category": "warning",
    },
}


def get_foreshadowing_for_round(
    round_number: int,
    flags: dict,
) -> list[dict]:
    """Return foreshadowing signals relevant to this round based on active flags."""
    signals = []
    all_flags = set(flags.keys()) if isinstance(flags, dict) else set()
    for sig_id, sig in FORESHADOWING_SIGNALS.items():
        if sig["signal_round"] == round_number:
            if sig["source_flag"] in all_flags:
                signals.append({
                    "signal_id": sig_id,
                    "message": sig["message"],
                    "category": sig["category"],
                    "source_flag": sig["source_flag"],
                })
    return signals
