"""
CEO Interview — Post-Game Competency Assessment Engine
=====================================================

After Round 10, players are optionally interviewed by the "CEO of Muressons"
(AI voice via ElevenLabs) on their strategic decisions. Responses are scored
against a 6-dimension competency framework and blended with simulation-derived
performance metrics to produce a spider (radar) diagram and narrative feedback.

Feature is gated by: god-mode `ceo_interview_enabled: True`
"""

from __future__ import annotations
from typing import Any

# ═══════════════════════════════════════════════════════════════
#  ASSESSMENT DIMENSIONS
# ═══════════════════════════════════════════════════════════════

DIMENSIONS = [
    {
        "id": "strategic_thinking",
        "label": "Strategic Thinking",
        "description": "Long-term vs short-term trade-off awareness",
        "max_score": 10,
    },
    {
        "id": "stakeholder_empathy",
        "label": "Stakeholder Empathy",
        "description": "Ability to articulate competing stakeholder interests",
        "max_score": 10,
    },
    {
        "id": "financial_acumen",
        "label": "Financial Acumen",
        "description": "Understanding of treasury, EBITDA, M_R mechanics",
        "max_score": 10,
    },
    {
        "id": "ethical_reasoning",
        "label": "Ethical Reasoning",
        "description": "Moral framework sophistication",
        "max_score": 10,
    },
    {
        "id": "systems_thinking",
        "label": "Systems Thinking",
        "description": "Understanding of cross-round flag dependencies",
        "max_score": 10,
    },
    {
        "id": "adaptive_leadership",
        "label": "Adaptive Leadership",
        "description": "Willingness to change strategy based on new information",
        "max_score": 10,
    },
]

# ═══════════════════════════════════════════════════════════════
#  INTERVIEW QUESTIONS
# ═══════════════════════════════════════════════════════════════

# Base questions (always asked) — 4 core questions
BASE_QUESTIONS = [
    {
        "id": "q_strategic_rationale",
        "text": "Walk me through your most impactful strategic decision. What was your reasoning, and what trade-offs did you consider?",
        "dimensions": ["strategic_thinking", "financial_acumen"],
        "follow_up": "How did that decision affect your stakeholders differently?",
        "ceo_intro": "I've reviewed your 10-round track record. Let's start with the big picture.",
    },
    {
        "id": "q_tradeoff_awareness",
        "text": "There were moments where you had to sacrifice one stakeholder group's interests for another. Can you describe a specific example and explain how you weighed those competing interests?",
        "dimensions": ["stakeholder_empathy", "ethical_reasoning"],
        "follow_up": "Would you make the same choice again knowing the outcome?",
        "ceo_intro": "Being a CEO means making impossible choices. Tell me about yours.",
    },
    {
        "id": "q_systems_understanding",
        "text": "Looking across all 10 rounds, can you identify a decision in an earlier round that had unexpected consequences in a later round? What did that teach you?",
        "dimensions": ["systems_thinking", "adaptive_leadership"],
        "follow_up": "How would you build early-warning systems for these cascading effects?",
        "ceo_intro": "Strategy isn't linear — decisions compound. Let's explore that.",
    },
    {
        "id": "q_hindsight_reflection",
        "text": "If you could go back and change one decision, which would it be and why? What would you do differently?",
        "dimensions": ["adaptive_leadership", "strategic_thinking"],
        "follow_up": "What structural change to your decision-making process would have helped?",
        "ceo_intro": "Hindsight is 20/20, but wisdom comes from examining it honestly.",
    },
]

# Pathway-specific questions (Q5)
PATHWAY_QUESTIONS = {
    "activist_ultimatum": {
        "id": "q_pathway_activist",
        "text": "An activist investor forced your hand in Round 10. How would you restructure your board governance to prevent being blindsided by activist campaigns in the future?",
        "dimensions": ["stakeholder_empathy", "strategic_thinking"],
        "ceo_intro": "Activist pressure is the new normal. How prepared are you?",
    },
    "climate_black_swan": {
        "id": "q_pathway_climate",
        "text": "A catastrophic climate event reshaped the market in Round 10. Given that carbon-intensive assets are increasingly becoming stranded, how would you redesign Muressons' portfolio for climate resilience over the next decade?",
        "dimensions": ["systems_thinking", "strategic_thinking"],
        "ceo_intro": "The climate crisis just became personal for Muressons. What's your long game?",
    },
    "stakeholder_revolt": {
        "id": "q_pathway_stakeholder",
        "text": "Your workforce and communities revolted against corporate decisions they felt were unjust. How do you rebuild trust with employees and local communities after such a breakdown?",
        "dimensions": ["stakeholder_empathy", "ethical_reasoning"],
        "ceo_intro": "Social license isn't optional — it's existential. How do you earn it back?",
    },
    "hostile_takeover": {
        "id": "q_pathway_hostile",
        "text": "A hostile bidder saw weakness in your balance sheet. What corporate governance reforms would you implement to make Muressons resilient against future takeover attempts without destroying shareholder value?",
        "dimensions": ["financial_acumen", "strategic_thinking"],
        "ceo_intro": "Corporate raiders smell blood in the water. How do you fortify?",
    },
    "regulatory_shutdown": {
        "id": "q_pathway_regulatory",
        "text": "Regulators threatened to revoke your operating license. How would you build a proactive regulatory engagement strategy that goes beyond compliance?",
        "dimensions": ["ethical_reasoning", "systems_thinking"],
        "ceo_intro": "Regulation is not an obstacle — it's a signal. What is it telling you?",
    },
}


def get_interview_questions(
    ending_pathway: str = "activist_ultimatum",
    question_count: int = 5,
    include_pathway_question: bool = True,
) -> list[dict]:
    """Generate the interview question set for a session.
    
    Returns a list of question dicts with:
      - id, text, dimensions, ceo_intro, follow_up (optional)
    """
    questions = list(BASE_QUESTIONS[:min(question_count - 1, 4)])

    if include_pathway_question:
        pw_q = PATHWAY_QUESTIONS.get(ending_pathway, PATHWAY_QUESTIONS["activist_ultimatum"])
        questions.append(pw_q)

    return questions[:question_count]


# ═══════════════════════════════════════════════════════════════
#  DATA-DRIVEN SCORING (from simulation metrics)
# ═══════════════════════════════════════════════════════════════

def calc_data_scores(
    extra: dict,
    global_state: dict,
    bus: list[dict],
    all_flags: dict,
) -> dict[str, float]:
    """Calculate simulation-performance-derived dimension scores (0–10 each).
    
    These scores are blended with LLM response scores (50/50) to produce
    the final spider diagram values.
    """
    scores = {}

    # ── Strategic Thinking (from M_R and terminal value) ──
    mr = extra.get("regenerative_multiple", 1.0)
    # Map M_R range [0.5, 2.0] to [1, 10]
    scores["strategic_thinking"] = round(min(10, max(1, (mr - 0.5) / 0.15)), 1)

    # ── Stakeholder Empathy (from avg SLO and burnout) ──
    if bus:
        avg_slo = sum(b.get("social_license_score", 50) for b in bus) / len(bus)
        avg_burnout = sum(b.get("staff_burnout_index", 0) for b in bus) / len(bus)
        slo_score = min(10, max(1, avg_slo / 10))
        burnout_bonus = 2.0 if avg_burnout < 30 else (1.0 if avg_burnout < 60 else 0)
        scores["stakeholder_empathy"] = round(min(10, slo_score + burnout_bonus), 1)
    else:
        scores["stakeholder_empathy"] = 5.0

    # ── Financial Acumen (from treasury management and EBITDA growth) ──
    treasury = global_state.get("corporate_treasury", 0)
    historical_ebitda = global_state.get("historical_ebitda", 0)
    # Positive treasury and growing EBITDA = strong financial management
    t_score = min(5, max(0, treasury / 5_000_000))  # $25M → 5
    e_score = min(5, max(0, historical_ebitda / 10_000_000))  # $50M → 5
    scores["financial_acumen"] = round(min(10, t_score + e_score), 1)

    # ── Ethical Reasoning (from ethical AI + just transition flags) ──
    ethical_score = 4.0  # Baseline
    if all_flags.get("ethical_ai_overhaul"):
        ethical_score += 2.5
    if all_flags.get("community_fund"):
        ethical_score += 2.0
    elif all_flags.get("managed_transition"):
        ethical_score += 1.0
    if all_flags.get("deep_audit"):
        ethical_score += 1.0
    scores["ethical_reasoning"] = round(min(10, ethical_score), 1)

    # ── Systems Thinking (from synergy and VRIO coherence) ──
    synergy = global_state.get("synergy_multiplier", 1.0)
    vrio = global_state.get("vrio_capabilities", {})
    vrio_avg = sum(vrio.values()) / max(len(vrio), 1)
    syn_score = min(5, max(0, (synergy - 0.7) * 10))
    vrio_score = min(5, vrio_avg / 20)
    scores["systems_thinking"] = round(min(10, syn_score + vrio_score), 1)

    # ── Adaptive Leadership (from HR investment consistency + workforce readiness) ──
    workforce_readiness = global_state.get("workforce_readiness", 50.0)
    hr_rounds = sum(
        1 for k, v in all_flags.items()
        if isinstance(k, str) and k.startswith("hr_invested_r") and v is True
    )
    wr_score = min(5, workforce_readiness / 15)
    hr_score = min(5, hr_rounds * 1.0)
    scores["adaptive_leadership"] = round(min(10, wr_score + hr_score), 1)

    return scores


def generate_score_rationale(
    data_scores: dict[str, float],
    extra: dict,
    global_state: dict,
    bus: list[dict],
    all_flags: dict,
) -> dict[str, str]:
    """Generate human-readable rationale for each data-derived dimension score.
    
    Returns {dimension_id: rationale_string} explaining *why* the score was given,
    referencing the actual simulation metrics that drove it.
    """
    rationale = {}

    # ── Strategic Thinking ──
    mr = extra.get("regenerative_multiple", 1.0)
    score = data_scores.get("strategic_thinking", 5.0)
    if score >= 8:
        rationale["strategic_thinking"] = (
            f"Your Regenerative Multiple of {mr:.2f}× demonstrates exceptional long-term strategic "
            f"vision. You consistently prioritised decisions that balanced financial returns with "
            f"sustainability outcomes, producing a terminal value that exceeded expectations."
        )
    elif score >= 5:
        rationale["strategic_thinking"] = (
            f"Your Regenerative Multiple of {mr:.2f}× shows competent strategic thinking. While you "
            f"maintained viability, there were rounds where short-term financial pressures may have "
            f"overridden longer-term sustainability investments."
        )
    else:
        rationale["strategic_thinking"] = (
            f"Your Regenerative Multiple of {mr:.2f}× suggests that strategic trade-offs were not "
            f"consistently well-managed. Key decisions in earlier rounds likely compounded into "
            f"reduced terminal value. This is the most important learning from the simulation."
        )

    # ── Stakeholder Empathy ──
    if bus:
        avg_slo = sum(b.get("social_license_score", 50) for b in bus) / len(bus)
        avg_burnout = sum(b.get("staff_burnout_index", 0) for b in bus) / len(bus)
    else:
        avg_slo, avg_burnout = 50, 50
    score = data_scores.get("stakeholder_empathy", 5.0)
    burnout_text = f"workforce burnout at {avg_burnout:.0f}%"
    if score >= 7:
        rationale["stakeholder_empathy"] = (
            f"Average Social License of {avg_slo:.0f}/100 and {burnout_text} reflect genuine attention "
            f"to stakeholder welfare. You maintained community consent and workforce wellbeing — critical "
            f"for avoiding the Instability Discount on the Regenerative Multiple."
        )
    elif score >= 4:
        rationale["stakeholder_empathy"] = (
            f"Average Social License of {avg_slo:.0f}/100 and {burnout_text} suggest uneven stakeholder "
            f"management. Some communities and employees were deprioritised during cost-cutting rounds, "
            f"which contributed to reputational pressure."
        )
    else:
        rationale["stakeholder_empathy"] = (
            f"Average Social License of {avg_slo:.0f}/100 and {burnout_text} indicate that stakeholder "
            f"interests were systematically underweighted. This triggered the -0.4 Instability Discount "
            f"and reduced your final valuation significantly."
        )

    # ── Financial Acumen ──
    treasury = global_state.get("corporate_treasury", 0)
    ebitda = global_state.get("historical_ebitda", 0)
    score = data_scores.get("financial_acumen", 5.0)
    if score >= 7:
        rationale["financial_acumen"] = (
            f"Treasury of ${treasury / 1_000_000:.1f}M and EBITDA of ${ebitda / 1_000_000:.1f}M "
            f"demonstrate strong financial stewardship. You managed capital allocation effectively, "
            f"avoided excessive borrowing, and maintained profitability under pressure."
        )
    elif score >= 4:
        rationale["financial_acumen"] = (
            f"Treasury of ${treasury / 1_000_000:.1f}M and EBITDA of ${ebitda / 1_000_000:.1f}M "
            f"show adequate financial management, though there may have been rounds where over-investment "
            f"or under-allocation created cash flow strain."
        )
    else:
        rationale["financial_acumen"] = (
            f"Treasury of ${treasury / 1_000_000:.1f}M and EBITDA of ${ebitda / 1_000_000:.1f}M "
            f"suggest significant financial mismanagement. Over-borrowing, poor CAPEX allocation, "
            f"or failure to control OPEX likely eroded the balance sheet."
        )

    # ── Ethical Reasoning ──
    ethical_flags = []
    if all_flags.get("ethical_ai_overhaul"):
        ethical_flags.append("Ethical AI Overhaul")
    if all_flags.get("community_fund"):
        ethical_flags.append("Community Fund")
    elif all_flags.get("managed_transition"):
        ethical_flags.append("Managed Transition")
    if all_flags.get("deep_audit"):
        ethical_flags.append("Deep Audit")
    score = data_scores.get("ethical_reasoning", 5.0)
    flags_text = ", ".join(ethical_flags) if ethical_flags else "none triggered"
    if score >= 7:
        rationale["ethical_reasoning"] = (
            f"Ethical decisions tracked: {flags_text}. Your choices demonstrate a consistent moral "
            f"framework — you invested in transparency, community welfare, and responsible AI governance "
            f"even when cheaper alternatives were available."
        )
    elif score >= 4:
        rationale["ethical_reasoning"] = (
            f"Ethical decisions tracked: {flags_text}. You showed some ethical awareness but missed "
            f"opportunities to invest in community or governance structures that would have strengthened "
            f"your ethical profile."
        )
    else:
        rationale["ethical_reasoning"] = (
            f"Ethical decisions tracked: {flags_text}. Key ethical safeguards were bypassed, likely "
            f"to preserve short-term financial performance. In real organisations, this pattern "
            f"creates material governance and reputational risk."
        )

    # ── Systems Thinking ──
    synergy = global_state.get("synergy_multiplier", 1.0)
    vrio = global_state.get("vrio_capabilities", {})
    vrio_avg = sum(vrio.values()) / max(len(vrio), 1) if vrio else 0
    score = data_scores.get("systems_thinking", 5.0)
    if score >= 7:
        rationale["systems_thinking"] = (
            f"Synergy multiplier of {synergy:.2f}× and VRIO capability average of {vrio_avg:.0f} "
            f"show strong cross-BU integration. You understood that decisions in one business unit "
            f"create ripple effects across the entire portfolio — a hallmark of systems thinking."
        )
    elif score >= 4:
        rationale["systems_thinking"] = (
            f"Synergy multiplier of {synergy:.2f}× and VRIO capability average of {vrio_avg:.0f} "
            f"suggest partial systems awareness. Some cross-BU dependencies were managed well, "
            f"but the portfolio didn't achieve the full integration needed for industrial symbiosis."
        )
    else:
        rationale["systems_thinking"] = (
            f"Synergy multiplier of {synergy:.2f}× and VRIO capability average of {vrio_avg:.0f} "
            f"indicate siloed decision-making. Business units were treated independently rather than "
            f"as an interconnected system, missing opportunities for circularity and shared value."
        )

    # ── Adaptive Leadership ──
    workforce_readiness = global_state.get("workforce_readiness", 50.0)
    hr_rounds = sum(
        1 for k, v in all_flags.items()
        if isinstance(k, str) and k.startswith("hr_invested_r") and v is True
    )
    score = data_scores.get("adaptive_leadership", 5.0)
    if score >= 7:
        rationale["adaptive_leadership"] = (
            f"Workforce readiness at {workforce_readiness:.0f}% and HR investment in {hr_rounds} rounds "
            f"demonstrate consistent people-first leadership. You adapted your strategy as conditions "
            f"changed and invested in building organisational capability for the long term."
        )
    elif score >= 4:
        rationale["adaptive_leadership"] = (
            f"Workforce readiness at {workforce_readiness:.0f}% and HR investment in {hr_rounds} rounds "
            f"show some adaptive capacity, but there were periods where strategy remained static "
            f"despite changing market conditions."
        )
    else:
        rationale["adaptive_leadership"] = (
            f"Workforce readiness at {workforce_readiness:.0f}% and HR investment in {hr_rounds} rounds "
            f"suggest difficulty adapting to new information. A more agile approach — adjusting strategy "
            f"when feedback signals changed — would have produced better outcomes."
        )

    return rationale


# ═══════════════════════════════════════════════════════════════
#  RESPONSE ANALYSIS PROMPT TEMPLATE
# ═══════════════════════════════════════════════════════════════

ASSESSMENT_SYSTEM_PROMPT = """You are an expert assessor evaluating a business simulation participant's
interview responses. Score each response on the specified dimensions using a 1-10 scale.

SCORING RUBRIC:
- 1-3: Superficial, generic, or incorrect understanding
- 4-5: Basic awareness but lacks depth or nuance
- 6-7: Good understanding with specific examples and reasoning
- 8-9: Excellent analysis showing sophisticated strategic thinking
- 10: Exceptional insight that demonstrates mastery-level understanding

You must return a JSON object with:
1. "dimension_scores": { dimension_id: score (1-10) } for each relevant dimension
2. "feedback_paragraphs": array of 2-3 paragraphs of constructive narrative feedback
3. "key_strengths": array of 2-3 short strength statements
4. "growth_areas": array of 2-3 short improvement areas

Be rigorous but fair. A score of 7+ should require genuinely insightful responses."""


def build_assessment_prompt(
    questions: list[dict],
    responses: list[str],
    data_scores: dict[str, float],
    extra: dict,
) -> str:
    """Build the LLM prompt for scoring interview responses.
    
    Returns a user-message string to send to GPT-4o / Claude for assessment.
    """
    q_and_a = []
    for i, (q, r) in enumerate(zip(questions, responses), 1):
        dims = ", ".join(q.get("dimensions", []))
        q_and_a.append(
            f"Q{i} [{dims}]: {q['text']}\n"
            f"RESPONSE: {r}\n"
        )

    context = (
        f"Simulation Performance Context:\n"
        f"- Regenerative Multiple (M_R): {extra.get('regenerative_multiple', 1.0):.2f}\n"
        f"- Terminal Value: ${extra.get('terminal_value', 0):,.0f}\n"
        f"- Profile: {extra.get('profile_title', 'Unknown')}\n"
        f"- Data-derived dimension scores: {data_scores}\n"
    )

    return (
        f"{context}\n"
        f"INTERVIEW TRANSCRIPT:\n"
        f"{''.join(q_and_a)}\n"
        f"Assess the responses above. Return valid JSON only."
    )


# ═══════════════════════════════════════════════════════════════
#  SCORE BLENDING (data + LLM response analysis)
# ═══════════════════════════════════════════════════════════════

def blend_scores(
    data_scores: dict[str, float],
    response_scores: dict[str, float],
    data_weight: float = 0.5,
) -> dict[str, float]:
    """Blend data-derived scores with LLM response scores.
    
    Default 50/50 split. Returns final spider diagram values.
    """
    final = {}
    for dim in DIMENSIONS:
        did = dim["id"]
        d_score = data_scores.get(did, 5.0)
        r_score = response_scores.get(did, 5.0)
        final[did] = round(d_score * data_weight + r_score * (1 - data_weight), 1)
    return final


# ═══════════════════════════════════════════════════════════════
#  CEO PERSONA
# ═══════════════════════════════════════════════════════════════

CEO_PERSONAS = {
    "female": {
        "name": "Victoria Muressons",
        "title": "CEO & Chair, Muressons Global Corporation",
        "avatar": "👩‍💼",
        "voice_description": "Professional, warm, direct. British accent. Speaks with authority but genuine curiosity.",
        "elevenlabs_voice_id": "21m00Tcm4TlvDq8ikWAM",  # Rachel
        "intro_text": (
            "Good afternoon. I'm Victoria Muressons, CEO of this organisation. "
            "I've reviewed your performance across all 10 rounds of the simulation, "
            "and I'd like to understand the thinking behind your decisions. "
            "This isn't a test — it's a conversation about leadership. Let's begin."
        ),
        "outro_text": (
            "Thank you for your candid responses. Leading through complexity "
            "requires exactly this kind of reflective practice. I've prepared "
            "your competency assessment — let's review it together."
        ),
    },
    "male": {
        "name": "Alexander Muressons",
        "title": "CEO & Chair, Muressons Global Corporation",
        "avatar": "👨‍💼",
        "voice_description": "Authoritative, measured, analytical. Mid-Atlantic accent. Probing but respectful.",
        "elevenlabs_voice_id": "pNInz6obpgDQGcFmaJgB",  # Adam
        "intro_text": (
            "Good afternoon. I'm Alexander Muressons, CEO of this organisation. "
            "I've been following your decisions across all 10 rounds closely, "
            "and I'd like to understand the strategic reasoning behind them. "
            "Think of this as a board-level debrief. Let's begin."
        ),
        "outro_text": (
            "Thank you for your thoughtful responses. The mark of a strong leader "
            "is the ability to reflect honestly on their decisions. I've prepared "
            "your competency assessment — let's review it together."
        ),
    },
}

# Default alias — resolved at runtime via get_ceo_persona()
CEO_PERSONA = CEO_PERSONAS["female"]


def get_ceo_persona(voice_gender: str = "female") -> dict:
    """Return the CEO persona dict for the given gender."""
    return CEO_PERSONAS.get(voice_gender, CEO_PERSONAS["female"])


# ═══════════════════════════════════════════════════════════════
#  NARRATIVE FEEDBACK GENERATOR (fallback when no LLM available)
# ═══════════════════════════════════════════════════════════════

def generate_fallback_feedback(
    final_scores: dict[str, float],
    extra: dict,
) -> dict:
    """Generate narrative feedback without LLM — uses rule-based templates.
    
    Returns {feedback_paragraphs, key_strengths, growth_areas}
    """
    mr = extra.get("regenerative_multiple", 1.0)
    profile = extra.get("profile_title", "Strategic Leader")
    tv = extra.get("terminal_value", 0)

    # Find top 2 and bottom 2 dimensions
    sorted_dims = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)
    top_dims = sorted_dims[:2]
    bottom_dims = sorted_dims[-2:]

    dim_labels = {d["id"]: d["label"] for d in DIMENSIONS}

    strengths = []
    for did, score in top_dims:
        label = dim_labels.get(did, did)
        if score >= 8:
            strengths.append(f"Exceptional {label} — consistently demonstrated across decisions.")
        elif score >= 6:
            strengths.append(f"Strong {label} — good instincts with room for deeper application.")
        else:
            strengths.append(f"Developing {label} — shows awareness but needs more practice.")

    growth_areas = []
    for did, score in bottom_dims:
        label = dim_labels.get(did, did)
        if score < 4:
            growth_areas.append(f"Critical gap in {label} — prioritise development in this area.")
        elif score < 6:
            growth_areas.append(f"Moderate gap in {label} — seek opportunities to build this competency.")
        else:
            growth_areas.append(f"Minor gap in {label} — refinement would elevate overall performance.")

    # Narrative paragraphs
    paragraphs = []

    # Overall assessment
    if mr >= 1.5:
        paragraphs.append(
            f"Your performance as {profile} demonstrates a sophisticated understanding of "
            f"sustainability-integrated strategy. With a Regenerative Multiple of {mr:.2f}× and "
            f"terminal valuation of ${tv / 1_000_000:.1f}M, you've shown that financial performance "
            f"and stakeholder value are not mutually exclusive."
        )
    elif mr >= 1.0:
        paragraphs.append(
            f"As {profile}, you've navigated the simulation with solid foundational skills. "
            f"Your M_R of {mr:.2f}× reflects competent management, though there's meaningful "
            f"upside from deeper stakeholder engagement and systems thinking."
        )
    else:
        paragraphs.append(
            f"Your journey as {profile} reveals important learning opportunities. "
            f"An M_R of {mr:.2f}× suggests that key sustainability dimensions were underweighted "
            f"in your decision framework. This isn't failure — it's precisely what simulations "
            f"are designed to surface."
        )

    # Dimension-specific
    top_label = dim_labels.get(top_dims[0][0], "leadership")
    bottom_label = dim_labels.get(bottom_dims[0][0], "skills")
    paragraphs.append(
        f"Your strongest competency is {top_label}, which appeared consistently in how "
        f"you framed problems and articulated solutions. To unlock the next level of "
        f"leadership effectiveness, focus on developing your {bottom_label} — this is "
        f"the dimension that would most amplify your other strengths."
    )

    # Forward-looking
    paragraphs.append(
        "In real organisations, the leaders who create lasting value are those who can "
        "hold multiple stakeholder perspectives simultaneously, think in systems rather "
        "than silos, and adapt their approach when new information challenges their assumptions. "
        "Continue practising these competencies in every strategic decision you make."
    )

    return {
        "feedback_paragraphs": paragraphs,
        "key_strengths": strengths,
        "growth_areas": growth_areas,
    }


# ═══════════════════════════════════════════════════════════════
#  IMPROVEMENT 1: LLM-BASED RESPONSE SCORING
# ═══════════════════════════════════════════════════════════════

async def score_responses_with_llm(
    questions: list[dict],
    responses: list[str],
    data_scores: dict[str, float],
    extra: dict,
) -> dict | None:
    """Call LLM API to score interview responses. Returns parsed result or None."""
    import json as _json
    try:
        from config import LLM_API_KEY, LLM_PROVIDER, LLM_MODEL
    except ImportError:
        return None

    if not LLM_API_KEY:
        return None

    prompt = build_assessment_prompt(questions, responses, data_scores, extra)

    try:
        import httpx
        if LLM_PROVIDER == "anthropic":
            async with httpx.AsyncClient(timeout=30) as client:
                res = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": LLM_API_KEY,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": LLM_MODEL or "claude-sonnet-4-20250514",
                        "max_tokens": 2000,
                        "system": ASSESSMENT_SYSTEM_PROMPT,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                body = res.json()
                text = body.get("content", [{}])[0].get("text", "")
        else:  # openai
            async with httpx.AsyncClient(timeout=30) as client:
                res = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {LLM_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": LLM_MODEL or "gpt-4o-mini",
                        "messages": [
                            {"role": "system", "content": ASSESSMENT_SYSTEM_PROMPT},
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.3,
                        "response_format": {"type": "json_object"},
                    },
                )
                body = res.json()
                text = body["choices"][0]["message"]["content"]

        # Parse JSON from response
        # Strip markdown fences if present
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        result = _json.loads(text)
        return result
    except Exception as e:
        print(f"[ceo-interview] LLM scoring error: {e}")
        return None


# ═══════════════════════════════════════════════════════════════
#  IMPROVEMENT 2: TRAJECTORY-AWARE SCORING
# ═══════════════════════════════════════════════════════════════

def calc_trajectory_modifiers(
    round_history: list[dict],
    decision_log: list[dict],
) -> dict[str, dict]:
    """Analyze round-over-round trajectories for consistency bonuses/penalties.

    Returns {dimension_id: {modifier: float, narrative: str}}
    where modifier is a multiplier (0.8 to 1.2) applied to the data score.
    """
    if not round_history or len(round_history) < 3:
        return {}

    modifiers = {}

    # Extract time series
    mr_series = []
    slo_series = []
    treasury_series = []
    synergy_series = []

    for rh in round_history:
        gs = rh.get("global_state", {})
        flags = gs.get("active_event_flags", {})
        mr_series.append(flags.get("regenerative_multiple", gs.get("synergy_multiplier", 1.0)))
        treasury_series.append(gs.get("corporate_treasury", 0))
        synergy_series.append(gs.get("synergy_multiplier", 1.0))

        bus = rh.get("business_units", [])
        if bus:
            slo_series.append(sum(b.get("social_license_score", 50) for b in bus) / len(bus))
        else:
            slo_series.append(50)

    def _trend_score(series):
        """Calculate improvement trend. Returns -1 to +1."""
        if len(series) < 2:
            return 0
        improvements = sum(1 for i in range(1, len(series)) if series[i] > series[i - 1])
        return (improvements / (len(series) - 1)) * 2 - 1

    def _variance_penalty(series):
        """High variance = inconsistency = penalty."""
        if len(series) < 2:
            return 0
        mean = sum(series) / len(series)
        if mean == 0:
            return 0
        variance = sum((x - mean) ** 2 for x in series) / len(series)
        cv = (variance ** 0.5) / abs(mean)  # coefficient of variation
        return min(0.15, cv * 0.3)  # cap at 15% penalty

    # Strategic Thinking — reward consistent M_R improvement
    trend = _trend_score(synergy_series)
    mod = 1.0 + (trend * 0.1)  # ±10%
    if trend > 0.3:
        narr = f"Your strategic metrics improved consistently across {len(round_history)} rounds (+{trend*10:.0f}% trajectory bonus)."
    elif trend < -0.3:
        narr = f"Your strategic metrics declined over the simulation (-{abs(trend)*10:.0f}% trajectory penalty)."
    else:
        narr = "Your strategic trajectory was relatively flat — neither consistently improving nor declining."
    modifiers["strategic_thinking"] = {"modifier": round(mod, 2), "narrative": narr}

    # Stakeholder Empathy — penalise high SLO variance (boom-bust)
    penalty = _variance_penalty(slo_series)
    mod = 1.0 - penalty
    if penalty > 0.08:
        narr = f"Your Social License score showed high volatility across rounds (σ penalty: -{penalty*100:.0f}%). Consistent stakeholder management would have scored higher."
    elif penalty > 0.03:
        narr = "Your SLO showed moderate fluctuation — some rounds saw significant drops followed by recovery."
    else:
        narr = "Your Social License was maintained consistently — a sign of genuine stakeholder management discipline."
    modifiers["stakeholder_empathy"] = {"modifier": round(mod, 2), "narrative": narr}

    # Financial Acumen — reward consistent treasury growth, penalise boom-bust
    t_trend = _trend_score(treasury_series)
    t_penalty = _variance_penalty(treasury_series)
    mod = 1.0 + (t_trend * 0.08) - t_penalty
    emergency_rounds = sum(1 for r in round_history
                          if r.get("global_state", {}).get("active_event_flags", {}).get("emergency_credit_used"))
    if emergency_rounds > 0:
        mod -= 0.05 * emergency_rounds
        narr = f"Emergency credit was used in {emergency_rounds} round(s), indicating cash flow stress. Treasury trend: {'growing' if t_trend > 0 else 'declining'}."
    elif t_trend > 0.2:
        narr = "Treasury grew consistently across rounds — strong cash management."
    else:
        narr = "Treasury showed instability — consider more conservative capital allocation in volatile rounds."
    modifiers["financial_acumen"] = {"modifier": round(max(0.8, mod), 2), "narrative": narr}

    # Systems Thinking — reward compounding synergy
    syn_trend = _trend_score(synergy_series)
    mod = 1.0 + (syn_trend * 0.1)
    if syn_trend > 0.3:
        narr = f"Synergy multiplier compounded consistently (+{syn_trend*10:.0f}% bonus) — evidence of systems-level thinking."
    else:
        narr = "Synergy gains were inconsistent, suggesting siloed rather than systemic investment decisions."
    modifiers["systems_thinking"] = {"modifier": round(mod, 2), "narrative": narr}

    # Adaptive Leadership — detect strategy pivots after crises
    pivots = 0
    for entry in decision_log:
        if entry.get("choice_selected", "") != entry.get("previous_choice", ""):
            pivots += 1
    mod = 1.0 + min(0.15, pivots * 0.03)
    if pivots >= 3:
        narr = f"You adapted your strategy {pivots} times across the simulation — strong adaptive capacity."
    elif pivots >= 1:
        narr = f"You made {pivots} strategic pivot(s). More willingness to adapt mid-game would strengthen this score."
    else:
        narr = "No significant strategy changes were detected across rounds — consider whether more flexibility was warranted."
    modifiers["adaptive_leadership"] = {"modifier": round(mod, 2), "narrative": narr}

    # Ethical Reasoning — reward early vs late ethical investment
    ethical_flags_by_round = {}
    for rh in round_history:
        rn = rh.get("round_number", 0)
        flags = rh.get("global_state", {}).get("active_event_flags", {})
        for key in ["ethical_ai_overhaul", "community_fund", "managed_transition", "deep_audit"]:
            if flags.get(key) and key not in ethical_flags_by_round:
                ethical_flags_by_round[key] = rn

    if ethical_flags_by_round:
        avg_round = sum(ethical_flags_by_round.values()) / len(ethical_flags_by_round)
        # Early = bonus (rounds 1-4), late = penalty (rounds 8-10)
        mod = 1.0 + max(-0.1, min(0.15, (5 - avg_round) * 0.03))
        if avg_round <= 4:
            narr = f"Ethical investments were made proactively (avg round {avg_round:.0f}) — this indicates genuine values-driven leadership, not reactive compliance."
        else:
            narr = f"Ethical decisions came late (avg round {avg_round:.0f}). Earlier investment signals conviction; late investment may appear reactive."
    else:
        mod = 0.9
        narr = "No ethical investment flags were triggered — a significant gap in your leadership profile."
    modifiers["ethical_reasoning"] = {"modifier": round(mod, 2), "narrative": narr}

    return modifiers


# ═══════════════════════════════════════════════════════════════
#  IMPROVEMENT 3: BEHAVIOURAL EVIDENCE CITATIONS
# ═══════════════════════════════════════════════════════════════

def generate_evidence_citations(
    decision_log: list[dict],
    round_history: list[dict],
    data_scores: dict[str, float],
) -> dict[str, list[str]]:
    """Mine decision log for specific round/choice citations per dimension.

    Returns {dimension_id: [citation_1, citation_2]}
    """
    citations = {d["id"]: [] for d in DIMENSIONS}
    if not decision_log:
        return citations

    # Build round → choice mapping
    choices_by_round = {}
    for entry in decision_log:
        rn = entry.get("round_number", 0)
        choices_by_round.setdefault(rn, []).append(entry)

    # Build round → SLO delta mapping
    slo_deltas = {}
    for i in range(1, len(round_history)):
        prev_bus = round_history[i - 1].get("business_units", [])
        curr_bus = round_history[i].get("business_units", [])
        if prev_bus and curr_bus:
            prev_avg = sum(b.get("social_license_score", 50) for b in prev_bus) / len(prev_bus)
            curr_avg = sum(b.get("social_license_score", 50) for b in curr_bus) / len(curr_bus)
            slo_deltas[round_history[i].get("round_number", i + 1)] = round(curr_avg - prev_avg, 1)

    # Treasury deltas
    treasury_deltas = {}
    for i in range(1, len(round_history)):
        prev_t = round_history[i - 1].get("global_state", {}).get("corporate_treasury", 0)
        curr_t = round_history[i].get("global_state", {}).get("corporate_treasury", 0)
        treasury_deltas[round_history[i].get("round_number", i + 1)] = round(curr_t - prev_t)

    # Find most impactful rounds per dimension
    # Stakeholder Empathy — worst SLO drop
    if slo_deltas:
        worst_slo_round = min(slo_deltas, key=slo_deltas.get)
        delta = slo_deltas[worst_slo_round]
        if delta < -5:
            choices = choices_by_round.get(worst_slo_round, [])
            choice_text = choices[0].get("choice_selected", "unknown") if choices else "unknown"
            citations["stakeholder_empathy"].append(
                f"Round {worst_slo_round}: Your choice ('{choice_text}') caused a {abs(delta):.0f}-point SLO drop — the largest single-round decline in your simulation."
            )

    # Financial Acumen — worst treasury drop
    if treasury_deltas:
        worst_t_round = min(treasury_deltas, key=treasury_deltas.get)
        delta = treasury_deltas[worst_t_round]
        if delta < -1_000_000:
            choices = choices_by_round.get(worst_t_round, [])
            choice_text = choices[0].get("choice_selected", "unknown") if choices else "unknown"
            citations["financial_acumen"].append(
                f"Round {worst_t_round}: Treasury dropped by ${abs(delta)/1_000_000:.1f}M after choosing '{choice_text}'. This was your most expensive single-round decision."
            )

    # Strategic Thinking — cite the choice with highest CAPEX
    all_choices = sorted(decision_log, key=lambda x: abs(x.get("capex_allocated", 0)), reverse=True)
    if all_choices and all_choices[0].get("capex_allocated", 0) > 0:
        top = all_choices[0]
        citations["strategic_thinking"].append(
            f"Round {top.get('round_number', '?')}: You allocated ${top['capex_allocated']/1_000_000:.1f}M CAPEX via '{top.get('choice_selected', '?')}' — your largest single investment. This decision shaped your terminal value trajectory."
        )

    # Ethical Reasoning — cite specific ethical flag rounds
    for rh in round_history:
        rn = rh.get("round_number", 0)
        flags = rh.get("global_state", {}).get("active_event_flags", {})
        if flags.get("ethical_ai_overhaul"):
            citations["ethical_reasoning"].append(f"Round {rn}: You invested in the Ethical AI Overhaul — demonstrating commitment to responsible technology governance.")
            break
    for rh in round_history:
        rn = rh.get("round_number", 0)
        flags = rh.get("global_state", {}).get("active_event_flags", {})
        if flags.get("community_fund"):
            citations["ethical_reasoning"].append(f"Round {rn}: You established the Community Fund — prioritising just transition over cost minimisation.")
            break

    return citations


# ═══════════════════════════════════════════════════════════════
#  IMPROVEMENT 4: PEER BENCHMARKING
# ═══════════════════════════════════════════════════════════════

_peer_scores_store: dict[str, list[dict]] = {}  # cohort_id -> [{dim_id: score}]


def store_peer_scores(cohort_id: str, final_scores: dict[str, float]) -> None:
    """Store a completed assessment's scores for peer comparison."""
    _peer_scores_store.setdefault(cohort_id, []).append(final_scores)


def calc_peer_benchmarks(cohort_id: str, final_scores: dict[str, float]) -> dict[str, dict]:
    """Calculate percentile rank relative to cohort peers.

    Returns {dimension_id: {percentile: int, cohort_avg: float, cohort_size: int}}
    """
    peers = _peer_scores_store.get(cohort_id, [])
    if len(peers) < 2:
        return {}

    benchmarks = {}
    for dim in DIMENSIONS:
        did = dim["id"]
        my_score = final_scores.get(did, 0)
        peer_values = [p.get(did, 0) for p in peers]
        below = sum(1 for v in peer_values if v < my_score)
        percentile = round((below / len(peer_values)) * 100)
        avg = sum(peer_values) / len(peer_values)
        benchmarks[did] = {
            "percentile": percentile,
            "cohort_avg": round(avg, 1),
            "cohort_size": len(peer_values),
        }
    return benchmarks


# ═══════════════════════════════════════════════════════════════
#  IMPROVEMENT 6: ADAPTIVE INTERVIEW QUESTIONS
# ═══════════════════════════════════════════════════════════════

PROBE_TEMPLATES = {
    "strategic_thinking": {
        "text": "Your overall strategic trajectory suggests some missed opportunities. Looking at Rounds 4-7 specifically, what was driving your investment priorities? Were you optimising for short-term stability or long-term value creation?",
        "dimensions": ["strategic_thinking"],
        "ceo_intro": "I want to drill into your strategic framework more deeply.",
    },
    "stakeholder_empathy": {
        "text": "Your Social License scores fluctuated significantly. Can you walk me through a specific moment where you had to choose between stakeholder welfare and financial performance? What tipped the balance?",
        "dimensions": ["stakeholder_empathy"],
        "ceo_intro": "Stakeholder management is where many leaders struggle. Let's examine yours.",
    },
    "financial_acumen": {
        "text": "Your balance sheet tells an interesting story. There were rounds where treasury moved sharply. Walk me through your capital allocation logic — how did you decide what to invest in and what to defer?",
        "dimensions": ["financial_acumen"],
        "ceo_intro": "The numbers don't lie. Let's talk about your financial strategy.",
    },
    "ethical_reasoning": {
        "text": "Ethical leadership often requires investing in initiatives that don't have immediate financial returns. How did you weigh ethical considerations against commercial pressures? Give me a specific example.",
        "dimensions": ["ethical_reasoning"],
        "ceo_intro": "Ethics isn't just about compliance — it's about conviction. Tell me about yours.",
    },
    "systems_thinking": {
        "text": "Cross-business-unit synergies are the hidden multiplier in this simulation. How did you think about the connections between your divisions? Were you managing each BU independently or as an integrated portfolio?",
        "dimensions": ["systems_thinking"],
        "ceo_intro": "I'm interested in whether you saw the forest or just the trees.",
    },
    "adaptive_leadership": {
        "text": "The simulation threw several curveballs — market shocks, regulatory changes, stakeholder crises. How quickly did you adapt your strategy when conditions changed? Can you describe a specific pivot?",
        "dimensions": ["adaptive_leadership"],
        "ceo_intro": "Adaptability separates good managers from great leaders.",
    },
}


def generate_adaptive_questions(
    data_scores: dict[str, float],
    ending_pathway: str = "activist_ultimatum",
    question_count: int = 5,
) -> list[dict]:
    """Generate interview questions that probe the player's weakest dimensions.

    Returns a mix of base questions + targeted probes for weak areas.
    """
    # Start with 3 core questions
    questions = list(BASE_QUESTIONS[:3])

    # Find weakest 2 dimensions
    sorted_dims = sorted(data_scores.items(), key=lambda x: x[1])
    weakest = [d[0] for d in sorted_dims[:2]]

    # Add targeted probes for weak areas
    for dim_id in weakest:
        if dim_id in PROBE_TEMPLATES and len(questions) < question_count:
            probe = dict(PROBE_TEMPLATES[dim_id])
            probe["id"] = f"q_probe_{dim_id}"
            probe["is_adaptive"] = True
            probe["target_dimension"] = dim_id
            questions.append(probe)

    # Fill remaining with pathway question
    if len(questions) < question_count:
        pw_q = PATHWAY_QUESTIONS.get(ending_pathway, PATHWAY_QUESTIONS["activist_ultimatum"])
        questions.append(pw_q)

    return questions[:question_count]


# ═══════════════════════════════════════════════════════════════
#  IMPROVEMENT 5: SELF-ASSESSMENT CALIBRATION
# ═══════════════════════════════════════════════════════════════

def calc_calibration_gaps(
    self_assessment: dict[str, float],
    final_scores: dict[str, float],
) -> dict[str, dict]:
    """Calculate the gap between self-rated and actual scores.

    Returns {dimension_id: {self: float, actual: float, gap: float, label: str}}
    """
    if not self_assessment:
        return {}

    gaps = {}
    for dim in DIMENSIONS:
        did = dim["id"]
        self_score = self_assessment.get(did, 5.0)
        actual = final_scores.get(did, 5.0)
        gap = round(self_score - actual, 1)

        if abs(gap) <= 1.0:
            label = "Well Calibrated"
        elif gap > 2.5:
            label = "Significantly Overconfident"
        elif gap > 1.0:
            label = "Moderately Overconfident"
        elif gap < -2.5:
            label = "Significantly Underconfident"
        else:
            label = "Moderately Underconfident"

        gaps[did] = {
            "self": self_score,
            "actual": actual,
            "gap": gap,
            "label": label,
        }
    return gaps
