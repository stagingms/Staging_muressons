"""
Muressons Global Corporation — Meadows Leverage Points Framework
Pedagogical overlay that maps every player decision to Donella Meadows'
(2008) 12 Leverage Points for systems intervention.

Theory base:
  Meadows, D. (2008). Thinking in Systems: A Primer. Chelsea Green.
  Places in increasing order of effectiveness (12 = weakest, 1 = strongest).

Architecture:
  Pure-function module. Analyses a complete game session and generates
  a leverage-points debrief mapping that can be used in:
    - Post-game reflection (Thiagarajan Phase 3)
    - Facilitator teleprompter commentary
    - Student self-assessment

This module also integrates:
  - Senge (1990) system archetypes detection
  - Argyris (1977) double-loop learning classification
  - Sterman (2000) system dynamics feedback identification
"""

from __future__ import annotations
from typing import Any


# ═══════════════════════════════════════════════════════════════
#  MEADOWS' 12 LEVERAGE POINTS (2008)
#  Numbered 12 (least effective) → 1 (most effective)
# ═══════════════════════════════════════════════════════════════

LEVERAGE_POINTS = {
    12: {
        "name": "Constants, parameters, numbers",
        "description": "Adjusting quantities: tax rates, subsidies, investment amounts",
        "simulation_examples": [
            "Adjusting investment slider amounts in InvestmentMatrix",
            "Changing CapEx allocation percentages",
            "Setting dividend levels",
        ],
        "effectiveness": "lowest",
        "student_trap": (
            "Students who only adjust 'how much' they invest without changing "
            "'what' or 'why' they invest are operating at the weakest leverage point."
        ),
    },
    11: {
        "name": "Buffer sizes (stabilizing stocks)",
        "description": "Size of stabilizing stocks relative to flows",
        "simulation_examples": [
            "Corporate Treasury as a buffer against shocks",
            "Green Transition Fund as an earmarked buffer",
            "Social Licence Score as a reputational buffer",
        ],
        "effectiveness": "low",
        "student_trap": (
            "Hoarding cash (large treasury buffer) feels safe but sacrifices "
            "investment returns. Too small a buffer means any crisis is fatal."
        ),
    },
    10: {
        "name": "Stock-and-flow structure",
        "description": "Physical structure of the system (BUs, supply chains)",
        "simulation_examples": [
            "4-BU conglomerate structure (pharma, electronics, consumer, software)",
            "Revenue base → OPEX base → CSF flow",
            "Natural Capital Debt stock with interest accumulation",
        ],
        "effectiveness": "low",
        "student_trap": (
            "The BU structure is fixed — students can't restructure the company. "
            "This mirrors real corporate constraints where restructuring is slow."
        ),
    },
    9: {
        "name": "Delays (relative to rate of system change)",
        "description": "Time lags between action and effect",
        "simulation_examples": [
            "Deferred CapEx projects (resilience takes 2 rounds to build)",
            "VRIO decay (competitive advantage erodes over time)",
            "Burnout accumulation (consequences of HR neglect appear late)",
            "Mangrove maturation (NbS take 3 rounds for full effectiveness)",
        ],
        "effectiveness": "medium",
        "student_trap": (
            "Students who expect instant results from sustainability investments "
            "will be disappointed. The simulation teaches that systemic change "
            "has inherent delays — and that's pedagogically intentional."
        ),
    },
    8: {
        "name": "Balancing feedback loops (strength)",
        "description": "Corrective mechanisms that stabilize the system",
        "simulation_examples": [
            "Burnout → OPEX penalty → Treasury pressure (self-correcting pain)",
            "Low SLO → Regulatory friction → Operating cost increase",
            "High NCD → Interest rate increase → Investment pressure",
            "Greenwashing → SLO penalty → forced authentic investment",
        ],
        "effectiveness": "medium",
        "student_trap": (
            "These loops punish bad behaviour automatically. Students who ignore "
            "them will find the system 'fights back' — which is realistic."
        ),
    },
    7: {
        "name": "Reinforcing feedback loops (gain)",
        "description": "Self-amplifying dynamics that drive growth or collapse",
        "simulation_examples": [
            "Contagion sigmoid: crisis severity → reputation loss → stakeholder revolt → more severity",
            "Social media velocity amplifier (R4+): digital acceleration of negative spirals",
            "Synergy multiplier: cross-BU investment → efficiency gains → more resources → more synergy",
            "Burnout → strike → revenue loss → cost cutting → more burnout",
        ],
        "effectiveness": "medium-high",
        "student_trap": (
            "Reinforcing loops are where simulations are won or lost. Students "
            "who accidentally trigger negative reinforcing loops (R4 contagion) "
            "find recovery extremely difficult. This mirrors real corporate crises."
        ),
    },
    6: {
        "name": "Information flows (access to information)",
        "description": "Who has what information, and when",
        "simulation_examples": [
            "Fog of Complexity (progressive engine disclosure)",
            "Intelligence dossiers in stakeholder mapping",
            "R5 formative checkpoint revealing hidden engines",
            "Foreshadowing events (R5-R8) as early warning signals",
            "God Mode transparency dashboard for facilitators",
        ],
        "effectiveness": "high",
        "student_trap": (
            "The Fog of Complexity deliberately withholds information. Students "
            "who demand full transparency miss the lesson: real executives always "
            "operate with incomplete information."
        ),
    },
    5: {
        "name": "Rules (incentives, punishments, constraints)",
        "description": "The formal and informal rules governing behaviour",
        "simulation_examples": [
            "CFO Materiality Gate (R2): blocks budget to non-material items",
            "Emergency Credit constraints (120% cap, interest premium)",
            "Dividend ratchet (cannot reduce dividends without penalty)",
            "Debt covenants (3.5× net debt/EBITDA trigger)",
            "CSRD compliance requirements",
        ],
        "effectiveness": "high",
        "student_trap": (
            "Rules are powerful because they constrain the decision space. Students "
            "who try to 'work around' rules (CFO override) pay reputation penalties."
        ),
    },
    4: {
        "name": "Self-organization (ability to evolve structure)",
        "description": "System's capacity to change its own structure",
        "simulation_examples": [
            "Stakeholder salience migration (quadrants shift based on events)",
            "Ending pathway selection (system morphs based on accumulated state)",
            "Turnaround arc (crisis → stabilization → recovery creates new structure)",
            "Board governance composition changes (SE-1)",
        ],
        "effectiveness": "high",
        "student_trap": (
            "Most students don't recognise that the simulation is self-organizing: "
            "the ending pathway chosen for them is determined by their accumulated "
            "decisions, not random chance."
        ),
    },
    3: {
        "name": "Goals (purpose of the system)",
        "description": "What the system is trying to achieve",
        "simulation_examples": [
            "Terminal Valuation formula (M_R): defines what 'winning' means",
            "Spider diagram competency assessment: measures HOW you played",
            "The shift from 'maximize treasury' to 'maximize M_R' as understanding deepens",
        ],
        "effectiveness": "very high",
        "student_trap": (
            "The simulation's deepest lesson: students who optimize for treasury "
            "alone score poorly because M_R rewards integrated ESG performance. "
            "The goal of the system IS the most powerful leverage point."
        ),
    },
    2: {
        "name": "Mindset (paradigm out of which the system arises)",
        "description": "The shared assumptions and mental models",
        "simulation_examples": [
            "Mental Model Tracker (R1/R5/R10): tracks paradigm shifts",
            "'Profit vs Purpose' → 'Profit through Purpose' transformation",
            "Double Materiality: financial AND impact perspectives",
            "CEO Interview: tests whether paradigm actually shifted",
        ],
        "effectiveness": "transformative",
        "student_trap": (
            "This is where the simulation truly succeeds or fails as pedagogy. "
            "If a student's mental model shifts from 'ESG is cost' to 'ESG is "
            "value creation', the simulation has achieved its educational purpose."
        ),
    },
    1: {
        "name": "Transcending paradigms",
        "description": "The ability to see that paradigms are constructed, not truth",
        "simulation_examples": [
            "Post-game debrief: 'This simulation itself has a paradigm — what did it assume?'",
            "Recognising that M_R formula ENCODES a value judgment about sustainability",
            "Understanding that the simulation's 'correct answers' reflect one theory of change",
            "Questioning whether the simulation's framing of ESG is itself sufficient",
        ],
        "effectiveness": "highest",
        "student_trap": (
            "The ultimate learning outcome: students who can critique the simulation "
            "itself — questioning its assumptions about capitalism, growth, and sustainability "
            "— have reached the highest level of systems thinking."
        ),
    },
}


# ═══════════════════════════════════════════════════════════════
#  SENGE (1990) SYSTEM ARCHETYPES
# ═══════════════════════════════════════════════════════════════

SYSTEM_ARCHETYPES = {
    "fixes_that_fail": {
        "name": "Fixes That Fail",
        "description": "Short-term fix creates long-term problem",
        "simulation_triggers": [
            {"flag": "electronics_blindspot", "narrative": (
                "Skipping the deep audit (quick cost saving) led to the R4 "
                "contagion crisis doubling — a classic 'fix that failed'."
            )},
            {"flag": "greenwashing_detected", "narrative": (
                "Greenwashing provided short-term reputation boost but triggered "
                "SLO penalties and regulatory scrutiny — the 'fix' created worse problems."
            )},
            {"flag": "immediate_closure", "narrative": (
                "Immediate facility closure saved transition costs but triggered "
                "strike risk and community backlash — solving one problem, creating two."
            )},
        ],
    },
    "shifting_the_burden": {
        "name": "Shifting the Burden",
        "description": "Symptomatic solution weakens fundamental solution",
        "simulation_triggers": [
            {"flag": "carbon_offsets_only", "narrative": (
                "Relying on carbon offsets instead of operational decarbonisation "
                "shifts the burden to offset markets. When offset integrity collapses, "
                "the fundamental emissions problem remains unsolved."
            )},
            {"flag": "outsource_opacity", "narrative": (
                "Outsourcing waste management shifted the operational burden but "
                "created supply chain opacity — the underlying environmental risk "
                "didn't disappear, it just became invisible."
            )},
        ],
    },
    "tragedy_of_the_commons": {
        "name": "Tragedy of the Commons",
        "description": "Individual rational action depletes shared resource",
        "simulation_triggers": [
            {"condition": "high_ncd", "threshold": 300, "narrative": (
                "High Natural Capital Debt represents the company extracting value "
                "from shared ecosystems (water, soil, atmosphere) without paying "
                "the true cost — a corporate tragedy of the commons."
            )},
            {"condition": "water_stress", "threshold": 0.7, "narrative": (
                "Water stress index above 70% means the company is over-extracting "
                "from shared watersheds. The Deccan community conflict (R6) is the "
                "direct consequence of this commons depletion."
            )},
        ],
    },
    "success_to_the_successful": {
        "name": "Success to the Successful",
        "description": "Winner gets resources, loser gets starved",
        "simulation_triggers": [
            {"condition": "bu_revenue_variance", "narrative": (
                "BUs that receive more investment generate more revenue, which "
                "funds more investment. Neglected BUs enter a decline spiral. "
                "This archetype explains why balanced portfolio investment matters."
            )},
        ],
    },
    "limits_to_growth": {
        "name": "Limits to Growth",
        "description": "Growth process hits a constraint that slows or reverses it",
        "simulation_triggers": [
            {"condition": "synergy_diminishing", "narrative": (
                "The synergy engine uses sqrt scaling — first investments yield "
                "outsized returns but further investment hits diminishing returns. "
                "This is the classic limits to growth archetype."
            )},
            {"condition": "burnout_critical", "threshold": 70, "narrative": (
                "Workforce burnout above 70 means productivity growth has hit "
                "a human capital limit. No amount of operational investment can "
                "compensate for an exhausted workforce."
            )},
        ],
    },
    "growth_and_underinvestment": {
        "name": "Growth and Underinvestment",
        "description": "Growth strains capacity; underinvestment causes decline",
        "simulation_triggers": [
            {"condition": "low_workforce_readiness", "threshold": 40, "narrative": (
                "Low workforce readiness (< 40) means strategic initiatives "
                "operate at 80% effectiveness. Growth demands capability "
                "investment that was never made."
            )},
        ],
    },
}


def detect_archetypes(
    gs: dict,
    bus: list[dict],
    flags: dict,
) -> list[dict]:
    """
    Analyse current game state and return all active system archetypes.
    Used in debrief and facilitator teleprompter.
    """
    active = []
    all_flags = set()
    if isinstance(flags, dict):
        all_flags.update(flags.keys())
        for v in flags.values():
            if isinstance(v, list):
                all_flags.update(str(x) for x in v if isinstance(x, str))

    for arch_id, arch in SYSTEM_ARCHETYPES.items():
        for trigger in arch["simulation_triggers"]:
            if "flag" in trigger:
                if trigger["flag"] in all_flags:
                    active.append({
                        "archetype": arch["name"],
                        "description": arch["description"],
                        "narrative": trigger["narrative"],
                        "trigger_type": "flag",
                        "trigger_value": trigger["flag"],
                    })
            elif "condition" in trigger:
                triggered = False
                if trigger["condition"] == "high_ncd":
                    avg_ncd = sum(bu.get("natural_capital_debt", 0) for bu in bus) / max(len(bus), 1)
                    triggered = avg_ncd > trigger.get("threshold", 300)
                elif trigger["condition"] == "water_stress":
                    bio = gs.get("biodiversity_state", {})
                    triggered = bio.get("water_stress_index", 0) > trigger.get("threshold", 0.7)
                elif trigger["condition"] == "burnout_critical":
                    avg_b = sum(bu.get("staff_burnout_index", 0) for bu in bus) / max(len(bus), 1)
                    triggered = avg_b > trigger.get("threshold", 70)
                elif trigger["condition"] == "low_workforce_readiness":
                    triggered = gs.get("workforce_readiness", 50) < trigger.get("threshold", 40)
                elif trigger["condition"] == "synergy_diminishing":
                    triggered = True  # Always active (structural archetype)
                elif trigger["condition"] == "bu_revenue_variance":
                    revs = [bu.get("revenue_base", 0) for bu in bus]
                    if revs:
                        mean_rev = sum(revs) / len(revs)
                        variance = sum((r - mean_rev) ** 2 for r in revs) / len(revs)
                        triggered = variance > (mean_rev * 0.3) ** 2
                if triggered:
                    active.append({
                        "archetype": arch["name"],
                        "description": arch["description"],
                        "narrative": trigger["narrative"],
                        "trigger_type": "condition",
                        "trigger_value": trigger["condition"],
                    })

    return active


# ═══════════════════════════════════════════════════════════════
#  ARGYRIS (1977) DOUBLE-LOOP LEARNING CLASSIFIER
# ═══════════════════════════════════════════════════════════════

def classify_learning_loop(
    mental_model_history: list[dict],
    decisions_history: list[dict],
) -> dict:
    """
    Determine whether the student's learning trajectory shows
    single-loop or double-loop learning.

    Single-loop: Adjusting actions within existing mental model
      (e.g., "I'll invest more in ESG next time")

    Double-loop: Questioning and changing the mental model itself
      (e.g., "I was wrong about the relationship between cost and value")

    Detected via Mental Model Tracker shifts between R1, R5, and R10.
    """
    if len(mental_model_history) < 2:
        return {
            "loop_type": "insufficient_data",
            "message": "Not enough mental model snapshots to classify learning.",
        }

    first = mental_model_history[0].get("factor_ranking", [])
    last = mental_model_history[-1].get("factor_ranking", [])

    if not first or not last:
        return {
            "loop_type": "insufficient_data",
            "message": "Mental model factor rankings not captured.",
        }

    # Calculate ranking displacement (how much the ranking changed)
    displacement = 0
    for i, factor in enumerate(first):
        if factor in last:
            new_pos = last.index(factor)
            displacement += abs(i - new_pos)

    # High displacement = double-loop (fundamental reordering of priorities)
    # Low displacement = single-loop (same priorities, different amounts)
    max_displacement = len(first) * (len(first) - 1) / 2

    if max_displacement > 0:
        displacement_ratio = displacement / max_displacement
    else:
        displacement_ratio = 0

    if displacement_ratio > 0.5:
        loop_type = "double_loop"
        message = (
            "🔄 DOUBLE-LOOP LEARNING DETECTED: Your mental model fundamentally "
            "shifted during the simulation. Your R10 priority ranking differs "
            f"significantly from R1 ({displacement_ratio:.0%} displacement). "
            "This indicates you questioned your underlying assumptions about "
            "what drives corporate value — the hallmark of deep learning."
        )
    elif displacement_ratio > 0.2:
        loop_type = "transitional"
        message = (
            "🔄 TRANSITIONAL LEARNING: Your mental model showed moderate "
            f"evolution ({displacement_ratio:.0%} displacement). Some assumptions "
            "were challenged, but the core framework remained similar. Consider: "
            "what assumption do you still hold that might need questioning?"
        )
    else:
        loop_type = "single_loop"
        message = (
            "🔄 SINGLE-LOOP LEARNING: Your mental model remained largely stable "
            f"({displacement_ratio:.0%} displacement). You adjusted your strategy "
            "within the same framework. Challenge question: was your R1 framework "
            "truly adequate, or did you resist changing it?"
        )

    return {
        "loop_type": loop_type,
        "displacement_ratio": round(displacement_ratio, 3),
        "r1_ranking": first,
        "r10_ranking": last,
        "message": message,
    }


# ═══════════════════════════════════════════════════════════════
#  FULL SESSION LEVERAGE POINT ANALYSIS
# ═══════════════════════════════════════════════════════════════

def analyse_session_leverage_points(
    decision_history: list[dict],
    gs: dict,
    bus: list[dict],
) -> dict:
    """
    Map all decisions from a completed session to Meadows' leverage points.
    Returns a summary showing which leverage points the student operated at.
    """
    point_counts = {i: 0 for i in range(1, 13)}
    point_examples = {i: [] for i in range(1, 13)}

    for decision in decision_history:
        round_num = decision.get("round_number", 0)
        choice = decision.get("primary_choice", "")
        allocations = decision.get("allocations", {})

        # Classify each decision
        if allocations:
            # Investment amount adjustments = LP12
            point_counts[12] += 1
            point_examples[12].append(f"R{round_num}: CapEx allocation adjustment")

        # Specific round classifications
        round_lp_map = {
            1: {  # R1: Foundation
                "option_a": (5, "Set rules: comprehensive audit changes system rules"),
                "option_b": (5, "Set rules: deep supply chain audit establishes governance"),
                "option_c": (12, "Adjusted parameters: phased approach adjusts timing only"),
            },
            2: {  # R2: Double Materiality
                "option_a": (3, "Changed goals: adopted double materiality redefines success"),
                "option_b": (5, "Set rules: partial compliance creates weaker constraints"),
                "option_c": (12, "Adjusted parameters: minimal compliance is parameter-level"),
            },
            3: {  # R3: Scope 3
                "option_a": (8, "Strengthened balancing loop: internal decarbonisation creates feedback"),
                "option_b": (5, "Changed rules: green bond creates new financial constraint"),
                "option_c": (12, "Adjusted parameters: offsets adjust numbers without systemic change"),
            },
            5: {  # R5: Climate Adaptation
                "option_a": (10, "Changed structure: hard engineering modifies physical stock"),
                "option_b": (4, "Self-organization: nature-based solutions allow ecosystem self-organization"),
                "option_c": (11, "Adjusted buffer: insurance is a financial buffer strategy"),
            },
            7: {  # R7: Circular Economy
                "option_a": (7, "Reinforcing loop: circular economy creates positive material flow"),
                "option_b": (10, "Changed structure: industrial symbiosis restructures material flows"),
                "option_c": (7, "Reinforcing loop: waste-to-energy creates positive energy feedback"),
            },
            9: {  # R9: Just Transition
                "option_a": (12, "Adjusted parameters: immediate closure is parameter-level cost optimization"),
                "option_b": (2, "Changed mindset: managed transition reframes workers as stakeholders"),
                "option_c": (2, "Changed mindset: community trust fund redefines corporate responsibility"),
            },
        }

        if round_num in round_lp_map and choice in round_lp_map[round_num]:
            lp, desc = round_lp_map[round_num][choice]
            point_counts[lp] += 1
            point_examples[lp].append(f"R{round_num}: {desc}")

    # Calculate effectiveness score
    # Weighted sum: higher leverage points count more
    weighted_score = sum(
        (13 - lp) * count for lp, count in point_counts.items()
    )
    max_possible = sum((13 - lp) for lp in range(1, 13)) * 2  # Assume max 2 per LP
    effectiveness = round(min(1.0, weighted_score / max(max_possible, 1)), 3)

    # Determine dominant leverage level
    active_points = {lp: c for lp, c in point_counts.items() if c > 0}
    if active_points:
        dominant = max(active_points, key=active_points.get)
    else:
        dominant = 12

    return {
        "leverage_point_distribution": point_counts,
        "leverage_point_examples": point_examples,
        "effectiveness_score": effectiveness,
        "dominant_leverage_point": dominant,
        "dominant_name": LEVERAGE_POINTS[dominant]["name"],
        "interpretation": (
            f"Your dominant leverage point was LP{dominant}: "
            f"'{LEVERAGE_POINTS[dominant]['name']}'. "
            f"System effectiveness score: {effectiveness:.0%}. "
            + (
                "You operated primarily at high-leverage points — your decisions "
                "addressed systemic structures, not just parameters. 🎯"
                if dominant <= 5
                else "You operated primarily at medium-leverage points — good "
                "awareness of feedback dynamics, but consider whether you "
                "questioned the system's goals or paradigm."
                if dominant <= 8
                else "You operated primarily at low-leverage points — adjusting "
                "parameters and buffers rather than changing structures or goals. "
                "Real transformation requires higher-leverage interventions."
            )
        ),
        "theory_reference": "Meadows, D. (2008). Thinking in Systems: A Primer.",
    }
