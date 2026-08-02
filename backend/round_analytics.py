"""
Muressons Global Corporation — Round Analytics Engine
Pure-function module: no I/O, no database access.

Tracks the Collaboration Gap — the divergence between financial
accumulation and ESG stewardship across rounds.

Design contract (mirrors engine.py):
  - Operates exclusively on plain dicts passed in as arguments.
  - Returns plain dicts — never mutates inputs.
  - Never raises — returns a safe sentinel on any data error.
  - No imports from engine, round_logic, or router (no circular risk).

Intended use: called from run_new_engines() in round_logic.py,
result merged into extra_events and surfaced to the facilitator
debrief dashboard. Not a game mechanic — does not affect any
simulation outcome.

Field mapping (original concept → real engine fields):
  resource_inventory            → corporate_treasury + total_revenue
  sustainability_report_contribution → social_license_score,
                                       group_reputation,
                                       natural_capital_debt
"""

from __future__ import annotations


def calc_collaboration_gap(
    round_number: int,
    global_state: dict,
    bu_states: list[dict],
) -> dict:
    """
    Measure the 'Collaboration Gap' for this round.

    The gap quantifies how far financial accumulation has outrun
    (or underrun) ESG stewardship. It is a facilitator debrief
    metric, not a game-mechanic input.

    Parameters
    ----------
    round_number : int
        Current simulation round (1–10).
    global_state : dict
        Post-tick global state. Reads: corporate_treasury,
        group_reputation.
    bu_states : list[dict]
        Post-tick BU snapshots. Reads: revenue_base,
        social_license_score, natural_capital_debt.

    Returns
    -------
    dict with keys:
        collaboration_gap   float  — signed gap score
        financial_index     float  — 0-100 financial accumulation proxy
        esg_index           float  — 0-100 ESG stewardship composite
        gap_label           str    — human-readable category
        gap_icon            str    — colour-coded emoji
        trend               str    — "improving" | "worsening" | "stable"
        round               int
        components          dict   — sub-scores for dashboard breakdown

    Gap semantics
    -------------
    +30 and above  → Extractive   (wealth far outpacing ESG)
    +10 to +30     → Accumulation Bias
    -10 to +10     → Balanced
    Below -10      → Regenerative (ESG investment outpacing extraction)
    """
    try:
        n = max(len(bu_states), 1)

        # ── Financial accumulation index ──────────────────────────
        # Corporate treasury expressed as a percentage of one round's
        # total revenue run-rate.  Clamped to [-100, 100] so it sits
        # on the same scale as the ESG index.
        total_revenue = sum(bu.get("revenue_base", 0) for bu in bu_states)
        treasury      = global_state.get("corporate_treasury", 0.0)
        fin_index = round(
            min(100.0, max(-100.0, (treasury / max(total_revenue, 1)) * 100)),
            2,
        )

        # ── ESG stewardship index (0–100 composite) ───────────────
        # Weights chosen to reflect the simulation's own terminal-value
        # M_R formula: social license and reputation drive the
        # instability_discount; NCD drives natural_capital_interest.
        #
        #   social_license_score : 40 % — community trust
        #   group_reputation     : 40 % — market credibility
        #   natural_capital_debt : 20 % — inverted (lower is better)
        #       ncd_score = 100 when NCD = 0
        #       ncd_score = 0   when NCD = 1,000,000 (engine hard cap)
        avg_slo  = sum(bu.get("social_license_score", 50) for bu in bu_states) / n
        avg_ncd  = sum(bu.get("natural_capital_debt", 0)  for bu in bu_states) / n
        group_rep = global_state.get("group_reputation", 50.0)

        ncd_score = round(max(0.0, 100.0 - (avg_ncd / 10_000)), 2)
        esg_index = round(
            (avg_slo   * 0.40)
            + (group_rep * 0.40)
            + (ncd_score * 0.20),
            2,
        )

        # ── Gap ───────────────────────────────────────────────────
        # Positive → extractive (financial ahead of ESG)
        # Negative → regenerative (ESG ahead of financial)
        gap = round(fin_index - esg_index, 2)

        # ── Label ─────────────────────────────────────────────────
        if gap > 30:
            label = "Extractive"
            icon  = "🔴"
        elif gap > 10:
            label = "Accumulation Bias"
            icon  = "🟡"
        elif gap >= -10:
            label = "Balanced"
            icon  = "🟢"
        else:
            label = "Regenerative"
            icon  = "🌱"

        return {
            "round":             round_number,
            "collaboration_gap": gap,
            "financial_index":   fin_index,
            "esg_index":         esg_index,
            "gap_label":         label,
            "gap_icon":          icon,
            "components": {
                "avg_social_license": round(avg_slo, 1),
                "group_reputation":   round(group_rep, 1),
                "ncd_score":          ncd_score,
                "treasury_index":     fin_index,
                "total_revenue":      round(total_revenue, 0),
                "corporate_treasury": round(treasury, 0),
            },
        }

    except Exception as exc:  # pragma: no cover — safety net only
        return {
            "round":             round_number,
            "collaboration_gap": None,
            "error":             f"analytics_unavailable: {exc}",
        }


def summarise_gap_history(gap_history: list[dict]) -> dict:
    """
    Reduce a list of per-round gap dicts (as stored in global_state or
    returned from the router's session history) into a debrief summary.

    Parameters
    ----------
    gap_history : list[dict]
        Ordered list of calc_collaboration_gap() return values, one
        per round that the engine ran.

    Returns
    -------
    dict with keys:
        trend_direction  str   — "improving" | "worsening" | "stable"
        peak_gap         float — worst (most extractive) round gap
        peak_gap_round   int
        final_gap        float — gap in the last round played
        avg_gap          float — mean gap across all rounds
        rounds_extractive int  — rounds where gap > 30
        rounds_balanced   int  — rounds where -10 <= gap <= 30
        rounds_regenerative int — rounds where gap < -10
        debrief_message  str  — one-line facilitator prompt
    """
    valid = [
        r for r in gap_history
        if isinstance(r.get("collaboration_gap"), (int, float))
    ]
    if not valid:
        return {"trend_direction": "unknown", "error": "no_valid_rounds"}

    gaps = [r["collaboration_gap"] for r in valid]
    rounds = [r["round"] for r in valid]

    avg_gap   = round(sum(gaps) / len(gaps), 2)
    final_gap = gaps[-1]
    peak_gap  = max(gaps)
    peak_round = rounds[gaps.index(peak_gap)]

    # Trend: compare first half vs second half average
    mid = max(len(gaps) // 2, 1)
    first_half_avg  = sum(gaps[:mid]) / mid
    second_half_avg = sum(gaps[mid:]) / max(len(gaps) - mid, 1)
    delta = second_half_avg - first_half_avg

    if delta < -5:
        trend = "improving"
    elif delta > 5:
        trend = "worsening"
    else:
        trend = "stable"

    rounds_extractive   = sum(1 for g in gaps if g > 30)
    rounds_balanced     = sum(1 for g in gaps if -10 <= g <= 30)
    rounds_regenerative = sum(1 for g in gaps if g < -10)

    # Facilitator debrief prompt
    if trend == "worsening" and final_gap > 20:
        message = (
            "Financial extraction accelerated while ESG stewardship declined. "
            "Ask the team: at what point did the gap start widening — and why?"
        )
    elif trend == "improving":
        message = (
            "ESG stewardship improved relative to financial accumulation over time. "
            "Ask the team: what decisions drove that convergence?"
        )
    elif rounds_extractive >= 3:
        message = (
            f"The portfolio ran extractive for {rounds_extractive} rounds. "
            "Ask the team: where was the tipping point where ESG was deprioritised?"
        )
    else:
        message = (
            "The portfolio maintained a broadly balanced trajectory. "
            "Ask the team: was this intentional, or a by-product of other pressures?"
        )

    return {
        "trend_direction":    trend,
        "peak_gap":           peak_gap,
        "peak_gap_round":     peak_round,
        "final_gap":          final_gap,
        "avg_gap":            avg_gap,
        "rounds_extractive":  rounds_extractive,
        "rounds_balanced":    rounds_balanced,
        "rounds_regenerative": rounds_regenerative,
        "debrief_message":    message,
    }
