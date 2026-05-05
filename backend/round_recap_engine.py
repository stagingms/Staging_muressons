"""
Muressons Global Corporation — Round Recap Engine
"What Just Happened?" causal chain narrator.
Generates a 3-item narrative recap of the most impactful engine interactions.

Visibility: Facilitator-toggleable (round_recap_enabled).
"""

from __future__ import annotations
from typing import Any


# ═══════════════════════════════════════════════════════════════
#  THREE-WORD ANCHORS (Facilitator Teleprompter Enhancement)
# ═══════════════════════════════════════════════════════════════

THREE_WORD_ANCHORS: dict[int, dict[str, str]] = {
    1: {
        "option_a": "Surface. Blindspot. Ticking.",
        "option_b": "Deep. Revealed. Protected.",
        "option_c": "Partial. Deferred. Gamble.",
        "_default": "Foundations. Baseline. Uncertainty.",
    },
    2: {
        "option_a": "Aligned. Compliant. Invested.",
        "option_b": "Exceptions. Pragmatic. Risk.",
        "option_c": "Ignored. Clawback. Exposed.",
        "_default": "Materiality. Governance. Stakes.",
    },
    3: {
        "option_a": "Disrupted. Transformed. Costly.",
        "option_b": "Bonded. Transitioning. Watched.",
        "option_c": "Offset. Greenwash. Questioned.",
        "_default": "Carbon. Supply-chain. Pressure.",
    },
    4: {
        "option_a": "Transparent. Expensive. Trusted.",
        "option_b": "Contained. Managed. Festering.",
        "option_c": "Denied. Doubled. Cascading.",
        "_default": "Crisis. Contagion. Reputation.",
    },
    5: {
        "option_a": "Engineered. Concrete. Waiting.",
        "option_b": "Natural. Growing. Uncertain.",
        "option_c": "Insured. Exposed. Praying.",
        "_default": "Climate. Physical. Urgent.",
    },
    6: {
        "option_a": "Monetised. Profitable. Ticking.",
        "option_b": "Ethical. Costly. Principled.",
        "option_c": "Patched. Quiet. Fragile.",
        "_default": "Bias. Algorithm. Leadership.",
    },
    7: {
        "option_a": "Circular. Redesigned. Future-proof.",
        "option_b": "Extended. Compliant. Minimum.",
        "option_c": "Energy. Synergy. Bridge.",
        "_default": "Waste. Regulation. Transformation.",
    },
    8: {
        "option_a": "Equal. Expensive. Trusted.",
        "option_b": "Prioritised. Divided. Contested.",
        "option_c": "Desalination. Massive. Delayed.",
        "_default": "Water. Scarcity. Choice.",
    },
    9: {
        "option_a": "Closed. Efficient. Protested.",
        "option_b": "Managed. Dignified. Costly.",
        "option_c": "Community. Invested. Praised.",
        "_default": "Transition. Human. Moral.",
    },
    10: {
        "option_a": "Defended. Integrated. Survived.",
        "option_b": "Amputated. Lean. Painful.",
        "option_c": "Sold. Extracted. Finished.",
        "_default": "Terminal. Legacy. Reckoning.",
    },
}


# ═══════════════════════════════════════════════════════════════
#  CAUSAL CHAIN TEMPLATES
#  Maps engine events to narrative sentences
# ═══════════════════════════════════════════════════════════════

CAUSAL_TEMPLATES = {
    "contagion": {
        "positive": "Your reputation management contained the crisis — contagion spread was limited to {value:.0f}%.",
        "negative": "The crisis spread through your divisions like wildfire — contagion hit {value:.0f}%, dragging group reputation to {rep:.0f}.",
    },
    "synergy": {
        "positive": "Cross-BU synergy kicked in — your integrated strategy reduced OPEX by {value:.0f}% across all divisions.",
        "negative": "Synergy is failing — your divisions are operating in silos, with a multiplier of just {value:.2f}×.",
    },
    "ncd_interest": {
        "positive": "Natural capital debt is under control — interest at {value:.1f}% is manageable.",
        "negative": "Natural capital debt is compounding — interest has reached {value:.1f}%, costing ${cost:,.0f} this round.",
    },
    "burnout": {
        "positive": "Workforce wellbeing is strong — burnout at {value:.0f}% means full operational capacity.",
        "negative": "Burnout is reaching critical levels at {value:.0f}% — OPEX penalties are mounting and strike risk is rising.",
    },
    "brain_drain": {
        "positive": "Talent retention is healthy — your reputation attracts skilled workers.",
        "negative": "Brain drain is accelerating — low reputation ({rep:.0f}) is driving away your best people, costing {value:.0f}% OPEX penalty.",
    },
    "strike": {
        "positive": "Labour relations are stable — no industrial action risk.",
        "negative": "⚠️ STRIKE TRIGGERED — all revenue zeroed this round. Burnout ({burnout:.0f}%) exceeded the threshold.",
    },
    "treasury": {
        "positive": "Treasury is healthy at ${value:,.0f} — you have strategic flexibility.",
        "negative": "⚠️ Treasury is critical at ${value:,.0f} — distress mode may activate.",
    },
    "cascade": {
        "positive": "Your earlier decisions are paying dividends — {flag} provided protection this round.",
        "negative": "⚡ CASCADE: Your {flag} from Round {source_round} has come back to haunt you — {effect}.",
    },
    "stochastic": {
        "neutral": "🎲 Market fluctuation: {description} (This was random — not caused by your decisions.)",
    },
}


def generate_round_recap(
    round_number: int,
    choice_selected: str,
    engine_events: list[dict],
    bus: list[dict],
    gs: dict,
    active_flags: set,
) -> dict:
    """
    Generate a narrative round recap with:
    - three_word_anchor: 3-word facilitator summary
    - causal_chains: Top 3 most impactful events as narrative sentences
    - summary_sentence: One-line overall assessment
    """
    # Three-word anchor
    round_anchors = THREE_WORD_ANCHORS.get(round_number, {})
    anchor = round_anchors.get(choice_selected, round_anchors.get("_default", "Decision. Consequence. Learning."))

    # Score events by impact magnitude
    scored_events = []
    for e in engine_events:
        impact = abs(e.get("treasury_delta", 0)) / 1_000_000 + abs(e.get("reputation_delta", 0))
        scored_events.append((impact, e))
    scored_events.sort(key=lambda x: x[0], reverse=True)

    # Generate narrative for top 3
    causal_chains = []
    for _, event in scored_events[:3]:
        engine_id = event.get("engine_id", "unknown")
        templates = CAUSAL_TEMPLATES.get(engine_id, {})

        treasury_delta = event.get("treasury_delta", 0)
        rep_delta = event.get("reputation_delta", 0)

        if event.get("source_type") == "stochastic":
            template = templates.get("neutral", CAUSAL_TEMPLATES["stochastic"]["neutral"])
            narrative = template.format(
                description=event.get("description", "Unknown market event"),
            )
        elif treasury_delta >= 0 and rep_delta >= 0:
            template = templates.get("positive", "Positive outcome from {engine_id}.")
            narrative = _safe_format(template, event, bus, gs)
        else:
            template = templates.get("negative", "Negative outcome from {engine_id}.")
            narrative = _safe_format(template, event, bus, gs)

        causal_chains.append({
            "engine_id": engine_id,
            "narrative": narrative,
            "impact_magnitude": round(scored_events[0][0] if scored_events else 0, 2),
            "source_type": event.get("source_type", "strategic"),
            "source_icon": event.get("source_icon", "🎯"),
        })

    # Overall summary
    treasury = gs.get("corporate_treasury", 0)
    rep = gs.get("group_reputation", 50)
    if treasury < 0:
        summary = f"Round {round_number} was brutal. You're in financial distress with ${treasury/1e6:.1f}M treasury."
    elif rep < 30:
        summary = f"Round {round_number} damaged your reputation severely ({rep:.0f}/100). Recovery will be difficult."
    elif rep > 70 and treasury > 10_000_000:
        summary = f"Round {round_number} went well. Strong reputation ({rep:.0f}) and healthy treasury (${treasury/1e6:.1f}M)."
    else:
        summary = f"Round {round_number} had mixed results. Treasury: ${treasury/1e6:.1f}M, Reputation: {rep:.0f}/100."

    return {
        "round": round_number,
        "three_word_anchor": anchor,
        "causal_chains": causal_chains,
        "summary_sentence": summary,
        "choice_selected": choice_selected,
    }


def _safe_format(template: str, event: dict, bus: list[dict], gs: dict) -> str:
    """Format a template string safely, substituting available values."""
    avg_burnout = sum(b.get("staff_burnout_index", 0) for b in bus) / max(len(bus), 1) if bus else 0
    avg_rep = sum(b.get("reputation_score", 50) for b in bus) / max(len(bus), 1) if bus else 50

    try:
        return template.format(
            value=abs(event.get("value", event.get("treasury_delta", 0))),
            rep=avg_rep,
            cost=abs(event.get("treasury_delta", 0)),
            burnout=avg_burnout,
            flag=event.get("flag_triggered", "unknown"),
            source_round=event.get("source_round", "?"),
            effect=event.get("description", "unknown effect"),
            engine_id=event.get("engine_id", "unknown"),
            description=event.get("description", ""),
        )
    except (KeyError, ValueError):
        return event.get("description", f"Engine event: {event.get('engine_id', 'unknown')}")


def get_three_word_anchor(round_number: int, choice: str) -> str:
    """Return the three-word anchor for a round/choice."""
    anchors = THREE_WORD_ANCHORS.get(round_number, {})
    return anchors.get(choice, anchors.get("_default", "Decision. Consequence. Learning."))
