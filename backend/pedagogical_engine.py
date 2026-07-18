from __future__ import annotations
"""
Muressons Global Corporation — Pedagogical Engine
Pure-function module for metacognitive scaffolding, engine disclosure,
formative assessment, and learner journey support.

Features:
  - Progressive Engine Disclosure (Fog of Complexity)
  - Stochastic Feedback Labelling
  - Prediction Gates (Pre-Mortems)
  - Board Room Moments (Moon 2004 3-stage)
  - Mental Model Tracker (R1/R5/R10)
  - Confidence Calibration
  - Mid-Game Formative Checkpoint (R5)
  - Peer Comparison Nudges
  - Strategy Memo storage
  - Debrief Protocol (Thiagarajan 1993)
  - Difficulty Presets
  - Custom Crisis Designer
"""

from typing import Any
import math

# ═══════════════════════════════════════════════════════════════
#  1. PROGRESSIVE ENGINE DISCLOSURE (Fog of Complexity)
#     Sweller (1988): Reduce cognitive load in early rounds
# ═══════════════════════════════════════════════════════════════

ENGINE_TIERS = {
    "foundation": {
        "label": "Foundation",
        "target": "Undergraduates, non-business",
        "engines": [
            "csf", "contagion", "synergy", "ncd_interest", "decay",
            "inflation", "fog_of_war", "burnout",
        ],
        "metrics": [
            "corporate_treasury", "group_reputation", "synergy_multiplier",
            "avg_carbon_intensity", "avg_burnout", "workforce_readiness",
        ],
    },
    "advanced": {
        "label": "Advanced",
        "target": "MBA, sustainability professionals",
        "engines": None,  # All engines
        "metrics": None,  # All metrics
    },
    "expert": {
        "label": "Expert",
        "target": "Doctoral, consultants",
        "engines": None,  # All + stochastic noise visible
        "metrics": None,  # All + audit trail
        "show_stochastic_noise": True,
        "show_audit_trail": True,
    },
}

# Round-based progressive disclosure for "advanced" tier
ROUND_ENGINE_DISCLOSURE = {
    1: {"csf", "contagion", "synergy", "ncd_interest", "decay"},
    2: {"csf", "contagion", "synergy", "ncd_interest", "decay",
        "cash_conversion", "implementation_lag"},
    3: {"csf", "contagion", "synergy", "ncd_interest", "decay",
        "cash_conversion", "implementation_lag", "supply_chain_contagion"},
    4: {"csf", "contagion", "synergy", "ncd_interest", "decay",
        "cash_conversion", "implementation_lag", "supply_chain_contagion",
        "brain_drain", "strike", "inflation", "stakeholder_fatigue"},
    5: {"csf", "contagion", "synergy", "ncd_interest", "decay",
        "cash_conversion", "implementation_lag", "supply_chain_contagion",
        "brain_drain", "strike", "inflation", "stakeholder_fatigue",
        "overrun_risk", "technical_debt"},
    6: {"csf", "contagion", "synergy", "ncd_interest", "decay",
        "cash_conversion", "implementation_lag", "supply_chain_contagion",
        "brain_drain", "strike", "inflation", "stakeholder_fatigue",
        "overrun_risk", "technical_debt", "technology_lockin",
        "revenue_cannibalization"},
    7: {"csf", "contagion", "synergy", "ncd_interest", "decay",
        "cash_conversion", "implementation_lag", "supply_chain_contagion",
        "brain_drain", "strike", "inflation", "stakeholder_fatigue",
        "overrun_risk", "technical_debt", "technology_lockin",
        "revenue_cannibalization", "competitor_pressure", "fx_risk",
        "greenwashing_risk"},
}
# R8-R10: all engines visible
for r in (8, 9, 10):
    ROUND_ENGINE_DISCLOSURE[r] = None  # None = show all


def get_visible_engines(round_number: int, difficulty_tier: str = "advanced") -> set | None:
    """Return the set of engine IDs visible at this round/tier. None = all."""
    tier = ENGINE_TIERS.get(difficulty_tier, ENGINE_TIERS["advanced"])
    if tier.get("engines") is not None:
        return set(tier["engines"])
    return ROUND_ENGINE_DISCLOSURE.get(round_number)


def filter_engine_events(
    events: list[dict], round_number: int, difficulty_tier: str = "advanced",
) -> list[dict]:
    """Filter engine event list to only show visible engines."""
    visible = get_visible_engines(round_number, difficulty_tier)
    if visible is None:
        return events
    return [e for e in events if e.get("engine_id", "") in visible]


# ═══════════════════════════════════════════════════════════════
#  2. STOCHASTIC FEEDBACK LABELLING
#     Separate luck from strategy for causal attribution
# ═══════════════════════════════════════════════════════════════

STOCHASTIC_ENGINES = {
    "macro_noise", "fx_risk", "micro_strike_roll", "inflation_jitter",
    "carbon_price_noise",
}

CASCADE_FLAGS = {
    "electronics_blindspot", "greenwash_risk", "ai_monetised",
    "insurance_only", "electronics_water_priority", "civil_water_priority",
}


def label_outcome(event: dict, active_flags: set) -> dict:
    """
    Add a 'source_type' label to an engine event:
      - 'strategic': outcome from player decision
      - 'stochastic': outcome from random/noise engine
      - 'cascade': outcome from cross-round flag dependency
    """
    engine_id = event.get("engine_id", "")
    flag_triggered = event.get("flag_triggered", "")

    if engine_id in STOCHASTIC_ENGINES:
        event["source_type"] = "stochastic"
        event["source_icon"] = "🎲"
        event["source_label"] = "Market Fluctuation"
    elif flag_triggered and flag_triggered in CASCADE_FLAGS:
        event["source_type"] = "cascade"
        event["source_icon"] = "⚡"
        event["source_label"] = "Flag Cascade"
    else:
        event["source_type"] = "strategic"
        event["source_icon"] = "🎯"
        event["source_label"] = "Strategic Outcome"
    return event


def label_all_outcomes(events: list[dict], active_flags: set) -> list[dict]:
    """Label all engine events with source_type."""
    return [label_outcome(e, active_flags) for e in events]


# ═══════════════════════════════════════════════════════════════
#  3. ENGINE IMPACT SUMMARISER (Traffic-Light)
# ═══════════════════════════════════════════════════════════════

def summarise_engine_impacts(events: list[dict], top_n: int = 3) -> list[dict]:
    """
    Distill engine events into a traffic-light summary.
    Returns top N events sorted by absolute impact magnitude.
    """
    scored = []
    for e in events:
        impact = abs(e.get("treasury_delta", 0)) + abs(e.get("reputation_delta", 0)) * 1000
        if impact > 0:
            severity = "red" if e.get("treasury_delta", 0) < -500000 or e.get("reputation_delta", 0) < -5 else \
                       "green" if e.get("treasury_delta", 0) > 0 and e.get("reputation_delta", 0) >= 0 else "yellow"
            scored.append({
                "engine_id": e.get("engine_id", "unknown"),
                "description": e.get("description", ""),
                "severity": severity,
                "icon": "🔴" if severity == "red" else "🟢" if severity == "green" else "🟡",
                "impact_score": impact,
                "source_type": e.get("source_type", "strategic"),
            })
    scored.sort(key=lambda x: x["impact_score"], reverse=True)
    return scored[:top_n]


# ═══════════════════════════════════════════════════════════════
#  4. PREDICTION GATES (Pre-Mortems)
#     Klein (2007): Prospective hindsight
#     Facilitator-toggleable
# ═══════════════════════════════════════════════════════════════

def create_prediction_entry(
    round_number: int, player_id: str, prediction_text: str, choice_selected: str,
) -> dict:
    """Create a prediction record for storage."""
    return {
        "round": round_number,
        "player_id": player_id,
        "prediction": prediction_text,
        "choice_selected": choice_selected,
        "outcome_summary": None,  # Filled after round resolves
        "calibration": None,      # Filled after round resolves
    }


def evaluate_prediction(prediction: dict, outcome_summary: str, outcome_quality: float) -> dict:
    """
    LEGACY (sentiment-heuristic) evaluation — superseded by score_prediction()
    below, which scores STRUCTURED predictions deterministically. Kept only for
    backward compatibility with any old callers; do not use for new code.
    """
    prediction["outcome_summary"] = outcome_summary
    # Simple heuristic: if outcome_quality > 0.6, prediction was "aligned"
    prediction["calibration"] = "aligned" if outcome_quality > 0.6 else "misaligned"
    prediction["calibration_icon"] = "✅" if outcome_quality > 0.6 else "❌"
    return prediction


# ── Calibration scoring (PLAN_Calibration_Analytics.md, Phase 2) ─────────────
# Deterministic band scoring of the structured Predict-Before-Commit inputs.
# Pure functions: no I/O, no engine-state mutation. The commit path calls
# score_prediction() AFTER the tick with the realised deltas and writes the
# result only into the predictions log — never into engine ledgers.

TREASURY_BANDS = ("down_big", "down", "flat", "up", "up_big")
REPUTATION_DIRS = ("down", "flat", "up")

# Band edges (treasury, $): flat = |Δ| ≤ $1M; big = |Δ| > $5M.
_TRE_FLAT = 1_000_000
_TRE_BIG = 5_000_000
# Reputation: flat = |Δ| < 2 points.
_REP_FLAT = 2.0


def treasury_band_of(delta: float) -> str:
    """Map a realised treasury delta ($) onto the prediction bands."""
    d = float(delta or 0)
    if d < -_TRE_BIG:
        return "down_big"
    if d < -_TRE_FLAT:
        return "down"
    if d <= _TRE_FLAT:
        return "flat"
    if d <= _TRE_BIG:
        return "up"
    return "up_big"


def reputation_dir_of(delta: float) -> str:
    """Map a realised reputation delta (points) onto the direction bands."""
    d = float(delta or 0)
    if abs(d) < _REP_FLAT:
        return "flat"
    return "up" if d > 0 else "down"


def score_prediction(pred: dict, treasury_delta: float, reputation_delta: float) -> dict:
    """Score one structured prediction against realised deltas.

    Rules (documented in PLAN_Calibration_Analytics.md):
      • A KPI counts only if the player actually predicted it (blank = skipped).
      • A hit is an EXACT band match (bands are coarse by design).
      • brier = mean over predicted KPIs of (confidence − hit)², hit ∈ {0,1}.
        Only computed when a confidence was reported; otherwise None.
        Brier is a proper scoring rule: honest confidence is the optimal play.
    Returns a score dict; never raises on malformed input (defensive defaults).
    """
    hits = 0
    of = 0
    tre_hit = None
    rep_hit = None

    tb = pred.get("treasury_band")
    if tb in TREASURY_BANDS:
        of += 1
        tre_hit = tb == treasury_band_of(treasury_delta)
        hits += 1 if tre_hit else 0

    rd = pred.get("reputation_dir")
    if rd in REPUTATION_DIRS:
        of += 1
        rep_hit = rd == reputation_dir_of(reputation_delta)
        hits += 1 if rep_hit else 0

    brier = None
    conf = pred.get("confidence")
    if of > 0 and isinstance(conf, (int, float)):
        c = min(1.0, max(0.0, float(conf)))
        parts = []
        if tre_hit is not None:
            parts.append((c - (1.0 if tre_hit else 0.0)) ** 2)
        if rep_hit is not None:
            parts.append((c - (1.0 if rep_hit else 0.0)) ** 2)
        brier = round(sum(parts) / len(parts), 4)

    return {
        "treasury_hit": tre_hit,
        "reputation_hit": rep_hit,
        "hits": hits,
        "of": of,
        "brier": brier,
        "actual_treasury_band": treasury_band_of(treasury_delta),
        "actual_reputation_dir": reputation_dir_of(reputation_delta),
        "treasury_delta": round(float(treasury_delta or 0), 2),
        "reputation_delta": round(float(reputation_delta or 0), 2),
    }


# ═══════════════════════════════════════════════════════════════
#  5. BOARD ROOM MOMENTS (Moon 2004 Three-Stage Protocol)
# ═══════════════════════════════════════════════════════════════

BOARD_ROOM_PROMPTS = {
    "noticing": {
        "label": "Noticing",
        "duration_sec": 30,
        "prompt": "What surprised you about the outcome of this round?",
        "level": "descriptive",
    },
    "making_sense": {
        "label": "Making Sense",
        "duration_sec": 60,
        "prompt": "Why do you think this happened? What causal chain produced this result?",
        "level": "analytical",
    },
    "working_with_meaning": {
        "label": "Working with Meaning",
        "duration_sec": 60,
        "prompt": "What does this tell you about your assumptions? What will you change?",
        "level": "evaluative",
    },
}


def create_board_room_entry(
    round_number: int, player_id: str,
    noticing: str, making_sense: str, working_with_meaning: str,
) -> dict:
    """Store a complete Board Room Moment reflection."""
    return {
        "round": round_number,
        "player_id": player_id,
        "noticing": noticing,
        "making_sense": making_sense,
        "working_with_meaning": working_with_meaning,
    }


def get_reflection_progression(all_entries: list[dict]) -> list[dict]:
    """Return chronological progression for R10 debrief display."""
    return sorted(all_entries, key=lambda x: x["round"])


# ═══════════════════════════════════════════════════════════════
#  6. MENTAL MODEL TRACKER (R1, R5, R10)
#     Tracks cognitive development via factor ranking
# ═══════════════════════════════════════════════════════════════

MENTAL_MODEL_FACTORS = [
    {"id": "revenue_growth", "label": "Revenue Growth", "color": "#6366f1"},
    {"id": "cost_reduction", "label": "Cost Reduction", "color": "#f59e0b"},
    {"id": "reputation", "label": "Reputation", "color": "#10b981"},
    {"id": "natural_capital", "label": "Natural Capital Preservation", "color": "#059669"},
    {"id": "workforce_wellbeing", "label": "Workforce Wellbeing", "color": "#8b5cf6"},
    {"id": "governance_quality", "label": "Governance Quality", "color": "#0ea5e9"},
]

MENTAL_MODEL_ROUNDS = [1, 5, 10]


def create_mental_model_entry(
    round_number: int, player_id: str, ranking: list[str],
) -> dict:
    """Store a mental model ranking (ordered list of factor IDs)."""
    return {
        "round": round_number,
        "player_id": player_id,
        "ranking": ranking,  # e.g. ["revenue_growth", "cost_reduction", ...]
    }


def compute_mental_model_shift(entries: list[dict]) -> dict:
    """
    Compute the shift between R1 and R10 rankings.
    Returns Sankey-style data for visualisation.
    """
    by_round = {e["round"]: e["ranking"] for e in entries}
    if 1 not in by_round or 10 not in by_round:
        return {"shifts": [], "incomplete": True}

    r1 = by_round[1]
    r10 = by_round[10]
    shifts = []
    for factor_id in r1:
        r1_pos = r1.index(factor_id)
        r10_pos = r10.index(factor_id) if factor_id in r10 else -1
        shifts.append({
            "factor": factor_id,
            "r1_rank": r1_pos + 1,
            "r10_rank": r10_pos + 1 if r10_pos >= 0 else None,
            "delta": (r1_pos - r10_pos) if r10_pos >= 0 else None,
        })
    return {"shifts": shifts, "incomplete": False}


# ═══════════════════════════════════════════════════════════════
#  7. CONFIDENCE CALIBRATION ("Would You Bet?")
#     Dunning-Kruger awareness. Facilitator-toggleable.
# ═══════════════════════════════════════════════════════════════

def create_confidence_entry(
    round_number: int, player_id: str, confidence: int, choice: str,
) -> dict:
    """Store confidence rating (1-5) for a decision."""
    return {
        "round": round_number,
        "player_id": player_id,
        "confidence": max(1, min(5, confidence)),
        "choice": choice,
        "outcome_quality": None,  # Filled post-round
    }


def compute_calibration_curve(entries: list[dict]) -> dict:
    """
    Compute confidence vs outcome quality across rounds.
    Returns data for a calibration chart.
    """
    filled = [e for e in entries if e.get("outcome_quality") is not None]
    if not filled:
        return {"data_points": [], "calibration_score": None}

    points = []
    total_error = 0
    for e in filled:
        expected = e["confidence"] / 5.0
        actual = e["outcome_quality"]
        error = abs(expected - actual)
        total_error += error
        points.append({
            "round": e["round"],
            "confidence": e["confidence"],
            "outcome_quality": round(actual, 2),
            "overconfident": expected > actual + 0.15,
            "underconfident": expected < actual - 0.15,
        })

    avg_error = total_error / len(filled) if filled else 0
    # 0 = perfect calibration, 1 = terrible
    calibration_score = round(1.0 - avg_error, 2)

    return {
        "data_points": points,
        "calibration_score": calibration_score,
        "interpretation": (
            "Well calibrated" if calibration_score > 0.75 else
            "Tends to overconfidence" if sum(1 for p in points if p["overconfident"]) > len(points) / 2 else
            "Tends to underconfidence" if sum(1 for p in points if p["underconfident"]) > len(points) / 2 else
            "Mixed calibration"
        ),
    }


# ═══════════════════════════════════════════════════════════════
#  8. MID-GAME FORMATIVE CHECKPOINT (R5)
#     Closes the formative assessment gap
# ═══════════════════════════════════════════════════════════════

def generate_r5_checkpoint(
    bus: list[dict], gs: dict, all_flags: dict, extra: dict,
) -> dict:
    """Generate a mid-game diagnostic after R5."""
    from terminal_valuation import calculate_mr, calculate_terminal_value

    # Project M_R based on current flags
    avg_slo = sum(b.get("social_license_score", 50) for b in bus) / max(len(bus), 1)
    avg_burnout = sum(b.get("staff_burnout_index", 0) for b in bus) / max(len(bus), 1)
    wr = gs.get("workforce_readiness", 50.0)
    syn = gs.get("synergy_multiplier", 1.0)
    hr_rounds = sum(1 for k, v in all_flags.items() if str(k).startswith("hr_invested_r") and v)

    mr_result = calculate_mr(all_flags, avg_slo, avg_burnout, wr, syn, hr_rounds)
    tv_result = calculate_terminal_value(bus, mr_result["mr"])

    # Identify bonuses earned vs locked out
    earned = mr_result.get("bonuses_earned", [])
    locked_out = []
    if all_flags.get("electronics_blindspot"):
        locked_out.append("R1 Blindspot will double R4 crisis severity")
    if not all_flags.get("materiality_aligned"):
        locked_out.append("Materiality Governance bonus (+0.10 M_R) — locked out")
    if all_flags.get("insurance_only"):
        locked_out.append("Resilience Champion bonus (+0.20 M_R) — locked out")

    # Biggest risk factor
    risks = []
    if avg_burnout > 40:
        risks.append(f"Burnout at {avg_burnout:.0f}% — approaching strike threshold")
    if avg_slo < 60:
        risks.append(f"Social License at {avg_slo:.0f} — instability discount risk at R10")
    treasury = gs.get("corporate_treasury", 0)
    if treasury < 5_000_000:
        risks.append(f"Treasury at ${treasury/1e6:.1f}M — distress risk")

    # Actionable recommendation
    recommendations = []
    if avg_burnout > 30 and hr_rounds < 3:
        recommendations.append("Consider investing in HR pillar to prevent burnout cliff")
    if not all_flags.get("early_decarboniser") and sum(b.get("carbon_intensity", 0) for b in bus) / max(len(bus), 1) > 35:
        recommendations.append("Carbon intensity is high — R7 circular economy will be critical")
    if syn < 0.9:
        recommendations.append("Synergy multiplier is low — cross-BU integration needed before R10")

    return {
        "projected_mr": round(mr_result["mr"], 2),
        "projected_tv_range": {
            "low": round(tv_result["terminal_value"] * 0.8, 0),
            "mid": round(tv_result["terminal_value"], 0),
            "high": round(tv_result["terminal_value"] * 1.2, 0),
        },
        "bonuses_earned": earned,
        "bonuses_locked_out": locked_out,
        "top_risk": risks[0] if risks else "No critical risks identified",
        "all_risks": risks,
        "recommendation": recommendations[0] if recommendations else "Stay the course — your trajectory is solid",
        "all_recommendations": recommendations,
        "current_archetype_projection": (
            "Regenerative Titan" if mr_result["mr"] >= 1.8 else
            "De-risked Safe-Haven" if mr_result["mr"] >= 1.2 else
            "Fragile Giant" if mr_result["mr"] >= 0.8 else
            "Stranded Relic"
        ),
    }


# ═══════════════════════════════════════════════════════════════
#  9. PEER COMPARISON NUDGES
#     Festinger (1954): Social comparison as formative motivator
# ═══════════════════════════════════════════════════════════════

def compute_peer_nudges(
    player_metrics: dict, all_player_metrics: list[dict],
) -> dict:
    """
    Compute blinded percentile rank for 3 key metrics.
    Returns {metric: {value, percentile, label}}.
    """
    if not all_player_metrics:
        return {}

    results = {}
    for metric_key, label in [
        ("corporate_treasury", "Treasury"),
        ("group_reputation", "Reputation"),
        ("avg_ncd", "Natural Capital Debt"),
    ]:
        player_val = player_metrics.get(metric_key, 0)
        all_vals = sorted([p.get(metric_key, 0) for p in all_player_metrics])
        n = len(all_vals)
        if n == 0:
            continue
        # For NCD, lower is better — invert percentile
        invert = metric_key == "avg_ncd"
        rank = sum(1 for v in all_vals if v <= player_val)
        pct = round((rank / n) * 100)
        if invert:
            pct = 100 - pct

        results[metric_key] = {
            "label": label,
            "value": round(player_val, 2),
            "percentile": pct,
            "descriptor": (
                f"Top {100 - pct}%" if pct >= 70 else
                f"Bottom {pct}%" if pct <= 30 else
                "Median"
            ),
        }
    return results


# ═══════════════════════════════════════════════════════════════
#  10. STRATEGY MEMO (Post R5 — Bloom's Create)
#      Facilitator-toggleable
# ═══════════════════════════════════════════════════════════════

STRATEGY_MEMO_TEMPLATE = {
    "sections": [
        {"id": "position_assessment", "label": "Current Position Assessment",
         "prompt": "Assess Muressons' current strategic position. What are your greatest strengths and vulnerabilities?"},
        {"id": "top_risks", "label": "Top 3 Risks & Mitigations",
         "prompt": "Identify the 3 biggest risks facing the company in R6-R10. For each, propose a specific mitigation."},
        {"id": "resource_rationale", "label": "Resource Allocation Rationale",
         "prompt": "How will you allocate your remaining capital across R6-R10? Justify your priorities."},
    ],
}


def create_strategy_memo(
    player_id: str, sections: dict[str, str],
) -> dict:
    """Store a strategy memo submission."""
    return {
        "player_id": player_id,
        "submitted_after_round": 5,
        "sections": sections,
    }


# ═══════════════════════════════════════════════════════════════
#  11. THREE-PHASE DEBRIEF PROTOCOL (Thiagarajan 1993)
#      Facilitator-toggleable
# ═══════════════════════════════════════════════════════════════

DEBRIEF_PROTOCOL = {
    "phase_1": {
        "title": "How Do You Feel?",
        "duration_min": 2,
        "icon": "💭",
        "instruction": "Let teams express their emotional response. Frustration, pride, surprise — all valid. This prevents cognitive interference from unprocessed emotions.",
        "facilitator_prompt": "Before we analyse anything, I want each team to share one word that describes how they feel right now.",
    },
    "phase_2": {
        "title": "What Happened?",
        "duration_min": 5,
        "icon": "📊",
        "instruction": "Factual reconstruction. Display the decision timeline with M_R breakdown. Each team narrates their journey.",
        "facilitator_prompt": "Walk us through your journey. What were your key turning points? When did you realise your strategy was working — or wasn't?",
    },
    "phase_3": {
        "title": "So What? / Now What?",
        "duration_min": 10,
        "icon": "🎯",
        "instruction": "Learning extraction. Teams articulate transferable principles. Use Real World Parallel cards.",
        "facilitator_prompt": "If you were advising a real CEO facing these same challenges, what three principles would you recommend? What would you do differently in a real organisation?",
    },
}


# ═══════════════════════════════════════════════════════════════
#  12. CUSTOM CRISIS DESIGNER (Expert tier — Bloom's Create)
# ═══════════════════════════════════════════════════════════════

def validate_custom_crisis(crisis: dict) -> dict:
    """Validate a player-designed crisis for R11."""
    errors = []
    if not crisis.get("title"):
        errors.append("Crisis must have a title")
    if not crisis.get("type") or crisis["type"] not in ("environmental", "social", "governance"):
        errors.append("Type must be: environmental, social, or governance")
    severity = crisis.get("severity", 0)
    if severity < 1 or severity > 100:
        errors.append("Severity must be 1-100")
    if not crisis.get("flag_exploits"):
        errors.append("Must specify at least one flag dependency to exploit")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "crisis": crisis if not errors else None,
    }


# ═══════════════════════════════════════════════════════════════
#  13. GOD-MODE PEDAGOGICAL TOGGLES
#      Session-level feature flags for facilitator control
# ═══════════════════════════════════════════════════════════════

DEFAULT_PEDAGOGICAL_TOGGLES = {
    "difficulty_tier": "advanced",         # foundation | advanced | expert
    "prediction_gates_enabled": False,     # Facilitator toggle
    "board_room_moments_enabled": True,    # Always on by default
    "mental_model_tracker_enabled": True,  # Always on
    "confidence_calibration_enabled": False, # Facilitator toggle
    "mid_game_checkpoint_enabled": True,   # Always on
    "peer_comparison_enabled": True,       # Always on in multiplayer
    "strategy_memo_enabled": False,        # Facilitator toggle
    "what_if_builder_enabled": False,      # God-mode + facilitator toggle
    "custom_crisis_enabled": False,        # Expert tier only
    "round_recap_enabled": False,          # Facilitator toggle
    "real_world_cards_enabled": False,     # Facilitator toggle for player visibility
    "real_world_cards_teleprompter": True,  # Always in teleprompter
    "debrief_protocol_enabled": False,     # Facilitator toggle
    "self_learning_mode": False,           # God-mode: facilitator-absent
    "flag_diagram_enabled": True,          # Living flag dependency diagram
    "stochastic_labels_enabled": True,     # Always on
    "engine_summariser_enabled": True,     # Always on
    # ── QW-1: Decision Timer (cognitive pressure) ──
    "decision_timer_enabled": False,       # Facilitator toggle
    "decision_timer_seconds": 300,         # 5 minutes default (configurable 180-600)
    "decision_timer_warning_pct": 0.20,    # Show warning at 20% remaining
    "decision_timer_auto_submit": False,   # Auto-submit on expiry (vs. penalty)
    "decision_timer_penalty_reputation": -2, # Rep penalty if timer expires
    # ── QW-5: Peer Learning Prompts ──
    "peer_learning_prompts_enabled": True,  # Show between R5-R6
    "peer_learning_prompts_rounds": [5, 6],  # Rounds where prompts appear
    # ── SE-1: Board Governance Minigame ──
    "board_governance_enabled": True,       # Board voting minigame
    "board_governance_rounds": [3, 6],      # Rounds where board votes occur
    # ── SE-2: Supply Chain Network ──
    "supply_chain_network_enabled": True,   # 3-tier supply chain model
    # ── SE-4: Biodiversity Engine ──
    "biodiversity_engine_enabled": True,    # Ecosystem health tracking
    # ── SE-5: Cross-Player Market Dynamics ──
    "market_dynamics_enabled": False,       # Only in multiplayer sessions
    # ── SE-6: Balance Sheet View ──
    "balance_sheet_enabled": True,          # Balance sheet dashboard
    # ── SE-7: Regulatory Sandbox ──
    "regulatory_sandbox_enabled": False,    # Expert tier only
    # ── SE-8: Dynamic Case Injection ──
    "dynamic_cases_enabled": True,          # Context-aware case briefs
    # ── SI-1: Non-Linear Branching ──
    "branching_enabled": True,              # Archetype-based branching at R5
    # ── SI-2: AI-Driven NPC Stakeholders ──
    "npc_stakeholders_enabled": True,       # Dynamic NPC reactions
    # ── SI-4: TCFD Scenario Analysis ──
    "tcfd_scenarios_enabled": True,         # Scenario analysis tool
    # ── SI-5: Organisational Politics ──
    "org_politics_enabled": True,           # C-suite coalition mechanics
    # ── Meadows Leverage Points ──
    "meadows_leverage_enabled": True,       # Leverage point debrief overlay
    # ── Senge System Archetypes ──
    "system_archetypes_enabled": True,      # Archetype detection in debrief
    # ── Round Analytics: Collaboration Gap Tracker ──
    # Facilitator debrief tool — measures the spread between financial
    # accumulation and ESG stewardship each round.
    # Not a game mechanic: result goes to extra_events only, never
    # feeds back into engine state or terminal value calculation.
    "collaboration_gap_enabled": True,      # On by default; toggle off for speed
    # ── Stakeholder / SLO Realism Upgrade (SPEC v1) ──
    # Phase 0 "land dark" toggles for the stakeholder ↔ SLO realism work.
    # All default OFF: no gameplay code references them yet, so enabling
    # them here is a no-op until the corresponding phase ships its engine.
    # Per-cohort enablement flows through `pedagogical_overrides`
    # (get_pedagogical_toggles merges any key already present in defaults).
    "stakeholder_memory_enabled": False,       # F1 / Phase 1 — trust as a stock
    "stakeholder_slo_feedback_enabled": False, # F2 / Phase 2 — continuous action→SLO
    "stakeholder_engagement_enabled": False,   # F5 / Phase 3 — promises / dialogic verb
    "stakeholder_coalitions_enabled": False,   # F3 / Phase 4 — salience contagion
    "stakeholder_uncertainty_enabled": False,  # F4 / Phase 5 — seeded thresholds + patience
    "stakeholder_intel_ui_enabled": False,     # F6 / Phase 6 — intent-forward UI
}


def get_pedagogical_toggles(session_overrides: dict | None = None) -> dict:
    """Merge session overrides with defaults."""
    toggles = dict(DEFAULT_PEDAGOGICAL_TOGGLES)
    if session_overrides:
        for k, v in session_overrides.items():
            if k in toggles:
                toggles[k] = v
    return toggles


# ═══════════════════════════════════════════════════════════════
#  14. DECISION TIMER (QW-1)
#      Configurable time pressure to prevent "solved game" optimisation
#      and introduce realistic cognitive load.
#      Kahneman (2011): Forces System 1 engagement under time pressure.
# ═══════════════════════════════════════════════════════════════

def get_timer_config(toggles: dict) -> dict:
    """
    Return timer configuration for the frontend.
    Frontend should display countdown and handle expiry.
    """
    if not toggles.get("decision_timer_enabled"):
        return {"enabled": False}

    return {
        "enabled": True,
        "duration_seconds": toggles.get("decision_timer_seconds", 300),
        "warning_threshold_pct": toggles.get("decision_timer_warning_pct", 0.20),
        "auto_submit": toggles.get("decision_timer_auto_submit", False),
        "expiry_penalty": {
            "reputation_delta": toggles.get("decision_timer_penalty_reputation", -2),
            "message": (
                "⏰ TIME EXPIRED: Decision submitted with default allocations. "
                "Real executives face constant time pressure — indecision has costs."
            ),
        },
    }


# ═══════════════════════════════════════════════════════════════
#  15. PEER LEARNING PROMPTS (QW-5)
#      Structured peer reflection prompts injected between rounds.
#      Vygotsky (1978): Zone of Proximal Development through peer interaction.
# ═══════════════════════════════════════════════════════════════

PEER_LEARNING_PROMPTS = {
    5: {
        "title": "Mid-Game Peer Reflection",
        "instructions": (
            "Before proceeding to Round 6, share your strategic approach with "
            "a peer (or reflect solo if in self-learning mode)."
        ),
        "prompts": [
            {
                "id": "strategy_compare",
                "question": (
                    "What was your biggest strategic trade-off so far? "
                    "What did you sacrifice, and what did you gain?"
                ),
                "theory_note": "March (1991): Exploration vs Exploitation — which are you prioritising?",
            },
            {
                "id": "surprise_factor",
                "question": (
                    "What surprised you most about the simulation so far? "
                    "What outcome didn't match your expectations?"
                ),
                "theory_note": "Argyris (1977): Surprises signal gaps between your mental model and reality.",
            },
            {
                "id": "advice_giving",
                "question": (
                    "If you could advise your peer on ONE thing to change in their "
                    "strategy for R6-R10, what would it be? Why?"
                ),
                "theory_note": "Vygotsky (1978): Teaching others deepens your own understanding.",
            },
        ],
    },
    6: {
        "title": "Strategic Pivot Reflection",
        "instructions": (
            "Round 6 introduces new system dynamics. Reflect on whether "
            "your current approach needs to adapt."
        ),
        "prompts": [
            {
                "id": "mental_model_check",
                "question": (
                    "Has your understanding of 'what drives success' in this "
                    "simulation changed since Round 1? What shifted?"
                ),
                "theory_note": "Argyris (1977): Double-loop learning = questioning your assumptions.",
            },
            {
                "id": "system_pattern",
                "question": (
                    "Can you identify any reinforcing or balancing loops in the "
                    "simulation? Where are you stuck in a loop?"
                ),
                "theory_note": "Senge (1990): System archetypes reveal hidden patterns.",
            },
        ],
    },
}


def get_peer_prompts_for_round(round_number: int, toggles: dict) -> dict | None:
    """Return peer learning prompts if enabled for this round."""
    if not toggles.get("peer_learning_prompts_enabled"):
        return None
    prompt_rounds = toggles.get("peer_learning_prompts_rounds", [5, 6])
    if round_number not in prompt_rounds:
        return None
    return PEER_LEARNING_PROMPTS.get(round_number)
