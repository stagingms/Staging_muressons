"""
Muressons Global Corporation - Admin Teleprompter Sub-Router (ARCH-002)
Extracted from admin_router.py to reduce monolith size.

Contains:
  - Base teleprompter scripts (10 rounds)
  - Healthcare teleprompter overlays
  - Advanced Climate teleprompter overlays
  - 3 API endpoints: /teleprompter, /teleprompter/{round}, /teleprompter/{round}/{paradigm}
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

teleprompter_router = APIRouter(prefix="/api/admin", tags=["Admin - Teleprompter"])


def _get_fac_role(request: Request) -> str:
    """Delegate to the canonical resolver (lazy import — admin_router imports
    this module's router at load time, so a top-level import would be circular)."""
    from admin_router import get_fac_role as _canonical
    return _canonical(request)


def require_facilitator(role: str = Depends(_get_fac_role)):
    if role == "anonymous":
        raise HTTPException(status_code=401, detail="Facilitator authentication required")


_TELEPROMPTER_SCRIPTS = {
    1: {
        "title": "Round 1: ESG Baseline Assessment — Stakeholder Mapping & The Diagnostic Decision",
        "crisis_theme": "📋 Foundation: Map your stakeholders before committing resources. How much do you invest in understanding your risks?",
        "talking_points": [
            "Welcome teams to their first strategic decision cycle",
            "STAKEHOLDER MAP (Pre-Decision Gate): Teams must complete Mendelow's Power-Interest Matrix BEFORE making their A/B/C decision — this is deliberate. Classification must precede strategy.",
            "Ask teams to READ the intelligence dossiers before dragging — descriptions are behavioural evidence, not labels. They must INFER power and interest from what stakeholders DO.",
            "AMBIGUOUS STAKEHOLDER: The Regional Business Journalist accepts two quadrants (Monitor or Keep Informed). Use this to discuss: real-world stakeholder classification is not always binary.",
            "ENGAGEMENT TACTICS: After classification, the debrief shows correct engagement tactics for 'Manage Closely' stakeholders. Discuss WHY offering board seats to an activist fund works better than defensive buybacks.",
            "Explain the Fog of War: metrics are noisy in early rounds — teams must decide with imperfect information",
            "CRITICAL: The $3M audit (Option B) seems expensive NOW but has 5× NPV return at Round 4",
            "Option A ($0 Surface Scan) creates the 'electronics_blindspot' flag — this DOUBLES R4 crisis severity",
            "Highlight: the inflation engine means doing nothing still costs money",
            "SCORING: 100%=3000pts, 90%=2000pts, 80%=1000pts. Below 80% = -3 reputation. Below 60% = $500K treasury penalty.",
        ],
        "key_teaching_moment": "💡 Stakeholder classification is step 1 — strategy selection is step 2. A Mendelow's Matrix is useless without engagement tactics. The value of information is non-linear: a $3M diagnostic investment avoids $15M+ in downstream damage.",
        "hr_tracking": "🧑‍💼 HR ROI tracking begins this round. Each HR pillar choice affects burnout and workforce readiness — these compound across all 10 rounds.",
        "engines_likely": ["fog_of_war_active", "inflation_index_applied"],
        "discussion_prompts": [
            "Why is the Tax Authority 'Keep Satisfied' and not 'Monitor'? (Answer: They hold high POWER via enforcement but low INTEREST unless triggered.)",
            "The Regional Business Journalist can be Monitor OR Keep Informed — what real-world event could shift them to 'Manage Closely'? (Answer: A data breach, ESG scandal, or viral story.)",
            "Mitchell, Agle & Wood (1997) added URGENCY as a 3rd dimension beyond Power and Interest. Which stakeholder has the highest urgency? (Answer: FutureFirst Activist Fund — AGM deadline in 90 days.)",
            "You classified stakeholders and THEN chose your ESG audit option. Did your mapping influence your A/B/C decision? Should it have?",
            "If you placed EU Regulators in 'Manage Closely' but chose Option A (Surface Scan), is your strategy internally consistent?",
            "For pillar teams: did you invest in the HR pillar? Why or why not?",
        ],
        "stakeholder_debrief": {
            "mendelow_theory": "Mendelow (1991) proposed that stakeholder management strategy should follow directly from classification: 'Manage Closely' → active partnership, 'Keep Satisfied' → routine compliance, 'Keep Informed' → transparent communication, 'Monitor' → passive observation.",
            "mitchell_extension": "Mitchell, Agle & Wood (1997) extended this with Urgency and Legitimacy. The simulation shows urgency badges post-submission — use these to discuss WHY some 'Keep Informed' stakeholders (e.g., Tier-3 Mine Workers with ILO scrutiny) have higher moral legitimacy than some 'Keep Satisfied' ones.",
            "bloom_progression": "This exercise operates at Bloom's Level 4 (Analyze) — students must infer power/interest from behavioural evidence, not given labels. The engagement tactics quiz pushes to Level 5 (Evaluate) — selecting the right response requires judgment.",
            "salience_preview": "Preview for R4: tell teams that stakeholder salience is NOT static. The 'General Public' they classified as 'Monitor' today may become 'Manage Closely' after a viral crisis. Ackermann & Eden (2011) call this salience migration.",
        },
        "pillar_guidance": "In pillar mode, remind teams that the HR pillar is available EVERY round. Consistent HR investment builds workforce readiness (which affects R7 synergy) and reduces burnout (which affects R9 strike probability and R10 M_R).",
        "student_ux_coaching": {
            "ux_gap": "Stakeholder Map opens as a separate full-screen modal, disconnected from the briefing narrative.",
            "facilitator_prompt": "Before students open the Stakeholder Map, walk them through the briefing connection: the dossier descriptions ARE the evidence for classification. Remind them to READ each description before dragging.",
            "what_to_watch": "Students who rush through the map without reading descriptions will score <80% and face a reputation penalty.",
            "ui_tip": "The Consequence DNA panel will surface in R4 for students who classified stakeholders poorly — point this out during the R4 debrief.",
        },
        "journey_improvement": {
            "r1_split": {
                "applies_to_tiers": ["foundation", "advanced"],
                "facilitator_guidance": [
                    "R1a ORIENTATION: In Foundation/Advanced tiers, R1 splits into two phases. R1a is exploration-only — NO decision required.",
                    "Guide teams through the Orientation checklist: (1) Read the Executive Briefing, (2) Complete the Stakeholder Map, (3) Read Board Member Profiles.",
                    "The stakeholder map task is GRADED and shared with the standard R1 gate — accuracy still affects R4 crisis severity.",
                    "R1b FIRST DECISION: Only after completing all orientation tasks does the A/B/C audit choice appear.",
                    "Sweller (1988): This split reduces intrinsic cognitive load. Players build germane schemas before facing their first strategic choice.",
                    "EXPERT TIER: The split is collapsed — Expert players get standard R1 with all tasks and decisions in one phase.",
                ],
            },
        },
    },
    2: {
        "title": "Round 2: Double Materiality — The CSRD Acid Test",
        "crisis_theme": "📊 Materiality: Can you separate real ESG impact from performative noise?",
        # ── Opening Question (5 min) ─────────────────────────────────────────
        "opening_question": (
            "Before revealing any metrics, ask teams: 'Write down the 3 ESG issues you "
            "think are most financially material to this company. Now write the 3 that "
            "have the most severe societal or environmental impact. How much overlap is there?' "
            "This surfaces the double materiality intuition before the exercise begins — "
            "teams that got it right early are usually the ones who invested in R1 audit data."
        ),
        # ── Core Teaching Points (10 min) ────────────────────────────────────
        "talking_points": [
            "OPEN with the opening_question above — do this BEFORE showing the matrix",
            "Explain the CFO Materiality Gate: investments must target Q1 (doubly material) nodes or face a −10 reputation override penalty",
            "★ KEY TENSION: Option A (Full Alignment) costs $2.5M in compliance infrastructure. Option C (Ignore) earns +$400K/BU but triggers a 40% budget clawback AND sets materiality_ignored flag — costing ~$5M+ over 8 rounds",
            "The 40% clawback is the simulation's version of ESG ratings agencies downgrading your disclosure quality score",
            "Option C also blocks the Green Bond discount in R3 — investors apply a $1M risk premium on your bond pricing",
            "Governance risk → Cash Conversion drag: at gov_risk=30, you lose ~6% revenue efficiency across all remaining rounds",
            "★ R2→R10 PAYOFF: the premium is TIERED — ≥80% matrix accuracy AND Option A → materiality_aligned (+0.10 M_R, ~$36M at the mean EBITDA); ≥80% AND Option B → materiality_partial (+0.05); Option C or <80% → materiality_ignored (nothing). Doing the analysis well does not excuse approving it badly",
        ],
        "key_teaching_moment": (
            "💡 DOUBLE MATERIALITY ≠ DOUBLE THE WORK. It's a lens change. Q1 issues are doubly material: "
            "they hit your P&L AND harm people/planet. Q2 issues (High Impact/Low Financial) don't need "
            "capex — they need disclosure investment (data, assurance, stakeholder engagement). "
            "Companies that fund Q4 issues (plastic straws, CSR galas) instead of Q1 are making a "
            "governance error — not just a strategy error."
        ),
        "hr_tracking": "🧑‍💼 Check: are teams investing in HR this round? Burnout begins accumulating if neglected. The OPEX penalty is quadratic — small now, devastating later.",
        "engines_likely": ["cash_conversion_drag", "implementation_lag", "supply_chain_contagion"],
        # ── ESRS Debrief Script — Regulatory Fidelity Note ───────────────────
        "regulatory_fidelity_note": (
            "★ FACILITATOR TRANSPARENCY NOTE: This simulation uses a simplified 2×2 binary matrix. "
            "Real CSRD/ESRS 1 assessment uses continuous severity/likelihood/time-horizon weighting "
            "(ESRS 1 §1.51-1.61). The binary grid is pedagogically justified — it forces a clear "
            "allocation choice. But in real practice, issues sit on a spectrum. Always surface this "
            "simplification in the debrief so participants don't leave with an oversimplified mental model."
        ),
        # ── Industry Vertical Notes ───────────────────────────────────────────
        "industry_vertical_notes": {
            "agriculture": (
                "🌾 AGRICULTURE INSIGHT: Agriculture is the ONLY vertical where TNFD (Taskforce on "
                "Nature-related Financial Disclosures) is as material as TCFD. The tnfd_nature_disclosure "
                "issue is Q1 — nature loss = production collapse. Ask: 'What is the difference between "
                "climate risk (TCFD) and nature risk (TNFD)? Why does agriculture sit at the intersection?'"
            ),
            "banking_financial_services": (
                "🏦 FINANCIAL SERVICES INSIGHT: The sfdr_greenwashing_risk issue is Q1. "
                "EU SFDR (Sustainable Finance Disclosure Regulation) Article 8/9 fund mislabelling "
                "is both high financial (fund outflows, fines up to 10% AUM) AND high societal "
                "(investor deception undermines the entire ESG investment thesis). Ask: "
                "'Who is harmed when an ESG fund isn't actually ESG?'"
            ),
            "technology": (
                "🧠 TECHNOLOGY INSIGHT: eu_ai_act_compliance is Q1 from 2025. The EU AI Act creates "
                "mandatory conformity assessments for high-risk AI systems (recruitment, credit, biometrics). "
                "Fines up to 3% global revenue. This is unique to Tech — no equivalent in other verticals. "
                "Ask: 'At what point does algorithmic efficiency become algorithmic discrimination?'"
            ),
            "oil_gas": (
                "⛽ OIL & GAS INSIGHT: stranded_asset_risk is the simulation's ONLY deliberately ambiguous Q1 issue. "
                "For a company in denial, it looks like Q3 (financial risk only). For one that has read "
                "the IEA NZE 2050 report, it's Q1 (existential). Ask: "
                "'What does your company's materiality assessment reveal about your strategic worldview?'"
            ),
        },
        # ── Closing: The Long Game ────────────────────────────────────────────
        "closing_script": (
            "Before moving on, ask: 'What would your company's real sustainability report look like if "
            "it was built from this matrix?' Pause on Q4 issues: plastic straws, CSR galas, exec offsets. "
            "'These are what make it into most corporate sustainability reports. Why? Because they're "
            "safe, cheap, and photographable.' The real test of CSRD is whether material issues — the "
            "ones that are hard, expensive, and inconvenient — end up in Q1. "
            "The simulation's terminal valuation is designed to answer that question with a number."
        ),
        "connection_to_theory": {
            "box_title": "📖 Connection to Theory — Double Materiality",
            "insights": [
                {
                    "theory": "Double Materiality (CSRD/ESRS)",
                    "insight": "The 2×2 matrix operationalises the CSRD's dual lens: financial materiality (outside-in risk) and impact materiality (inside-out harm). Q1 issues are doubly material — they require both disclosure AND strategic investment.",
                    "reference": "European Commission (2023). European Sustainability Reporting Standards (ESRS 1), §1.51-1.61.",
                },
                {
                    "theory": "Legitimacy Theory",
                    "insight": "Option C (Ignore Materiality) is a legitimacy gap — the company claims sustainability credentials while ignoring material issues. The 40% budget clawback is the market's legitimacy correction.",
                    "reference": "Suchman, M.C. (1995). Managing Legitimacy: Strategic and Institutional Approaches. Academy of Management Review, 20(3), 571-610.",
                },
                {
                    "theory": "Signalling Theory",
                    "insight": "Option A's $2.5M compliance investment is a CREDIBLE SIGNAL — costly enough to be unfakeable. Option C's cost savings send an equally strong signal: 'we don't take this seriously.'",
                    "reference": "Spence, M. (1973). Job Market Signaling. Quarterly Journal of Economics, 87(3), 355-374.",
                },
            ],
        },
        "discussion_prompts": [
            "Which option did you choose and why? What would the CFO say?",
            "Look at your Q4 placements: are any of these in your company's real sustainability report?",
            "What's the difference between a materiality assessment and a PR exercise?",
            "If you chose Option C: what signal does that send to your institutional investors?",
            "★ ADVANCED: Under ESRS 1, impact materiality is assessed regardless of financial impact. What does that mean for your Q2 issues?",
        ],
        "student_ux_coaching": {
            "ux_gap": "CSRD matrix opens in isolation with no visual connection to R1 audit results.",
            "facilitator_prompt": "Explicitly link the materiality matrix to R1: 'Your R1 audit decision determines HOW MUCH data you have for this matrix.' Deep Audit teams can classify with confidence; Surface Scan teams are guessing.",
            "what_to_watch": "Students may feel the matrix is a standalone exercise. Draw the R1→R2 arrow on the whiteboard.",
            "ui_tip": "The Consequence DNA panel (visible from R4) will trace materiality_aligned / materiality_partial / greenwash_risk flags back to this round.",
        },
    },

    3: {
        "title": "Round 3: Scope 3 Emissions — Supply Chain Decarbonisation",
        "crisis_theme": "🏭 Scope 3: Your supply chain carbon footprint is 4× your direct emissions. How fast do you transition?",
        "talking_points": [
            "Fog of War clears after this round — true metrics become visible",
            "Option A (Rapid Switch) earns the 'early_decarboniser' flag → +0.10 synergy bonus at R7",
            "Option B (Green Bond) is the financially elegant choice — reduces NCD by 15 with minimal disruption",
            "Option C (Offset & Defer) adds +5 NCD — this compounds at 6%+ interest for 7 remaining rounds",
            "Carbon intensity reduction NOW saves money at R10 terminal valuation ($250/ton carbon tax)",
        ],
        "key_teaching_moment": "💡 First-mover advantage in decarbonisation: Option A costs $4M now but earns a synergy bonus worth ~$50M+ at terminal valuation. Option C saves $3M now but compounds ~$850K in hidden NCD interest.",
        "hr_tracking": "🧑‍💼 Workforce readiness check: if readiness drops below 40, future pillar effectiveness is reduced by 20%. This affects how much value teams extract from their strategic choices.",
        "engines_likely": ["fog_of_war_active", "competitor_warning", "revenue_cannibalized"],
        "connection_to_theory": {
            "box_title": "📖 Connection to Theory — Decarbonisation Strategy",
            "insights": [
                {
                    "theory": "Real Options Theory",
                    "insight": "Option C (Offset & Defer) treats decarbonisation as a real option — delay commitment until uncertainty resolves. But the NCD compounding mechanism shows that deferral has a COST — the 'option premium' is the $850K in hidden interest.",
                    "reference": "Dixit, A.K. & Pindyck, R.S. (1994). Investment Under Uncertainty. Princeton University Press.",
                },
                {
                    "theory": "First-Mover Advantage",
                    "insight": "Option A's 'early_decarboniser' flag is Lieberman & Montgomery's first-mover advantage: the R7 synergy bonus rewards teams who committed to decarbonisation before competitors.",
                    "reference": "Lieberman, M.B. & Montgomery, D.B. (1988). First-Mover Advantages. Strategic Management Journal, 9(S1), 41-58.",
                },
                {
                    "theory": "Stranded Assets",
                    "insight": "NCD compounding is the simulation's proxy for stranded asset risk. Carbon-intensive assets lose value exponentially as regulation tightens — the $250/ton R10 carbon tax makes this visceral.",
                    "reference": "Carbon Tracker Initiative (2013). Unburnable Carbon: Are the World's Financial Markets Carrying a Carbon Bubble?",
                },
            ],
        },
        "discussion_prompts": [
            "Now that Fog of War is lifting, would you have changed your Round 1 decisions?",
            "How does the NPC competitor change your decarbonisation strategy?",
            "For Option A teams: was the disruption risk worth the early-mover advantage?",
        ],
        "student_ux_coaching": {
            "ux_gap": "Rounds 3-4 show the same UI as R1 — no visual escalation despite rising narrative stakes.",
            "facilitator_prompt": "Verbally escalate the stakes: 'The Fog of War is clearing — from next round, you will see the REAL consequences of your choices.' This primes students for the R4 reckoning.",
            "what_to_watch": "The Board Mood indicator will start shifting colour from R3 based on reputation trajectory. Point this out.",
            "ui_tip": "Round-tier CSS will auto-transition from Foundation (clean) to Crisis (urgent) at R4. The UI will feel visually different.",
        },
        "autonomous_agents_debrief": {
            "likely_stage": "dormant → watching",
            "facilitator_note": "By R3, agents with low patience (Greta Berg / Gen Z, Beth Colbert / Journalist) may have entered WATCHING if metrics are poor. Check the Autonomous Stakeholders panel.",
            "debrief_if_watching": [
                "An autonomous stakeholder has started monitoring your performance. Which agent is it, and what metric triggered their attention?",
                "The Gen Z Employee (Greta Berg) has the fastest decay rate — she notices problems before others. What does this tell us about generational expectations in ESG?",
            ],
        },
    },
    4: {
        "title": "Round 4: Contagion — The R1 Reckoning ★ KEY DEBRIEF ROUND ★",
        "crisis_theme": "🔥 Electronics Supply Chain Scandal — severity depends on your Round 1 audit decision!",
        "talking_points": [
            "★ THIS IS THE SIMULATION'S MOST IMPORTANT TEACHING MOMENT ★",
            "Reveal the R1→R4 cascade: Surface Scan teams face DOUBLE crisis severity (80 vs 40)",
            "At severity 80: reputation drops by 32 points. Combined with R4-C (Deny), reputation can hit single digits",
            "Low reputation triggers Brain-Drain on Software: OPEX can increase 50-85%",
            "Stakeholder Fatigue means future crises become even harder to recover from",
            "Ask teams who chose Option B in R1: 'Was the $3M audit worth it now?'",
        ],
        "key_teaching_moment": "💡 THE R1→R4 CASCADE: A $3M audit in R1 avoids ~$16M in reputation damage, Brain-Drain OPEX penalties, and Stakeholder Fatigue compounding. The NPV of the R1 diagnostic exceeds 5× its cost. This teaches: incomplete due diligence has asymmetric, non-linear downstream costs.",
        "debrief_the_cascade": {
            "surface_scan_teams": "Your crisis severity is 80 (2×). You now face −32 reputation. If you also chose Deny & Deflect, your reputation may be in single digits — triggering catastrophic Brain-Drain on Software BU.",
            "deep_audit_teams": "Your crisis severity is 40 (base). You face −16 reputation — manageable. Your $3M investment has now saved you ~$16M+ in avoided damage.",
            "deferred_audit_teams": "Your crisis severity is 60 (1.5×). You face −24 reputation — significant but survivable. A middle-ground outcome.",
            "key_question": "Would you invest $3M to avoid $16M in damage? Every corporate ESG audit decision carries this exact calculus.",
        },
        "hr_tracking": "🧑‍💼 Crisis burnout check: teams in crisis who chose 'Overtime & Crisis Push' in the HR pillar gained +12 burnout. This will compound into OPEX penalties and increase R9 strike probability.",
        "engines_likely": ["technology_lockin_penalty", "greenwashing_scandal", "regulatory_ratchet_active"],
        "discussion_prompts": [
            "★ R1→R4 CASCADE: What was the actual cost of skipping the audit in Round 1?",
            "How does path dependency change your view of upfront ESG investment?",
            "Is your strategy sustainable for 6 more rounds, or are you in damage control mode?",
            "How do you balance short-term EBITDA vs long-term resilience?",
        ],
        "student_ux_coaching": {
            "ux_gap": "Contagion crisis shows same UI as R1 — no escalation feel. Students miss the rising stakes.",
            "facilitator_prompt": "Direct students' attention to the Consequence DNA panel now visible in the center column — it shows the R1→R4 causal chain visually. Ask: 'Can you see WHY your crisis is this severe?'",
            "what_to_watch": "The Board Mood ambient indicator should be shifting to stressed (red-amber) for teams with low reputation. Use this: 'Notice how the cockpit feels different? That's your board's mood.'",
            "ui_tip": "Market Feed items now have consequence traceability — hover over crisis events to see which past decision caused them.",
        },
        "connection_to_theory": {
            "argyris_double_loop": (
                "🎓 ARGYRIS (1977) DOUBLE-LOOP LEARNING: R4 is the simulation's double-loop "
                "moment. Single-loop: 'our crisis severity is 80, how do we fix it?' "
                "Double-loop: 'WHY did we choose the surface scan in R1? What assumption "
                "about ESG auditing led to this?' Push teams past symptom-fixing to "
                "questioning their underlying mental models about risk."
            ),
            "kahneman_system1": (
                "🧠 KAHNEMAN (2011) SYSTEM 1 vs 2: R1's surface scan was a System 1 choice "
                "— fast, cheap, feels right. The $3M audit required System 2 deliberation. "
                "R4 reveals that System 1 shortcuts in ESG governance have asymmetric costs. "
                "Ask: 'Which of your other decisions this game have been System 1?'"
            ),
        },
        "reflection_sensitisation": (
            "🪞 MOON (2004): If a Board Room Moment triggers this round (likely for "
            "teams with >20% treasury drop), use it to FORCE the double-loop. The reflection "
            "prompt asks for ROOT CAUSE, not symptom. Teams will instinctively answer 'we "
            "need more money' — redirect to 'what decision created this situation?' "
            "The habit of causal attribution is the most transferable skill from this simulation."
        ),
        "stakeholder_migration": {
            "migrations_this_round": [
                "General Public: Monitor → Manage Closely (viral crisis amplified their power)",
                "Regional Business Journalist: Monitor → Manage Closely (broke the story nationally)",
                "Cafeteria Vendors: Monitor → Keep Informed (commercial interest increased)",
            ],
            "discussion_prompt": "In Round 1, teams classified the General Public as 'Monitor' — low power, low interest. After this crisis, they are 'Manage Closely'. Ask: what changed? (Answer: The crisis gave them URGENCY. Social media gave them POWER. Mitchell et al. call this salience activation.)",
            "theory": "Ackermann & Eden (2011): Salience is dynamic, not static. A stakeholder's power/interest classification is only valid until the next crisis event. Every Mendelow's Matrix is a snapshot, not a map.",
        },
        "autonomous_agents_debrief": {
            "likely_stage": "watching → agitated",
            "facilitator_note": "R4 crisis damage often pushes 2-3 agents from WATCHING to AGITATED. Teams who chose Surface Scan in R1 may see the Journalist and Community Activist escalate simultaneously.",
            "debrief_if_agitated": [
                "Multiple stakeholders are now publicly critical. How does this compound the R4 contagion crisis?",
                "Beth Colbert (Journalist) has the most cascade targets — if he triggers, he pulls 3 other agents toward action. What real-world dynamic does this model? (Answer: media amplification of corporate crises)",
                "Compare the Regulator's 'methodical' escalation with the Gen Z Employee's 'passionate' escalation. Which is more dangerous to your terminal value, and why?",
            ],
        },
    },
    5: {
        "title": "Round 5: Climate — Physical Climate Risk & Infrastructure Lead Times",
        "crisis_theme": "🌪️ Category 4 cyclone approaching. 75% chance of $12M damage. How do you prepare?",
        "talking_points": [
            "CRITICAL WARNING: Infrastructure does NOT protect this round — 2-round construction delay",
            "All three options are investments in FUTURE resilience, not current protection",
            "Option A (Hard Engineering) has hidden costs: +10 NCD + carbon intensity increase",
            "Option B (Nature-Based) is financially superior on total cost of ownership — reduces NCD AND carbon",
            "Option C (Insurance Only) is cheapest but BLOCKS the Resilience M_R bonus at R10 (−0.20)",
            "The stochastic roll adds genuine uncertainty — 75% chance of full $12M damage regardless of choice",
        ],
        "key_teaching_moment": "💡 Nature-Based Solutions (Option B) have lower TCO than Hard Engineering (Option A): B saves ~$1.4M over 5 rounds through NCD interest reduction and carbon tax avoidance, while A adds ~$850K in hidden costs. This mirrors real-world climate adaptation economics.",
        "hr_tracking": "🧑‍💼 Halfway mark: cumulative HR investment is now visible. Teams who neglected HR should see rising burnout and OPEX penalties. Ask: 'What is your burnout index? What is your workforce readiness score?'",
        "engines_likely": ["stakeholder_fatigue_applied", "dividend_ratchet_triggered", "tipping_point_reached"],
        "connection_to_theory": {
            "prospect_theory": (
                "🎓 KAHNEMAN & TVERSKY (1979) PROSPECT THEORY: R5 is where time-to-impact "
                "warnings become critical. 'NCD will trigger credit downgrade in 3 rounds' "
                "is LOSS FRAMING — more motivating than 'your NCD is 380K.' Read the "
                "time-to-impact warnings BEFORE showing absolute numbers. This primes "
                "teams to feel the urgency of compounding risks."
            ),
            "taleb_antifragility": (
                "📚 TALEB (2012) ANTIFRAGILITY: Nature-Based Solutions (Option B) make "
                "the system antifragile — they GAIN from volatility through reduced NCD. "
                "Hard Engineering (Option A) is merely robust — it resists stress but "
                "doesn't benefit from it. Insurance (Option C) is fragile — it transfers "
                "risk but creates moral hazard."
            ),
            "agency_theory": (
                "📚 JENSEN & MECKLING (1976) AGENCY THEORY: The Shareholder persona "
                "argues managers must maximise shareholder value and cash retention. "
                "This is the primary fiduciary duty under traditional agency theory."
            ),
            "natural_capital": (
                "🌿 COSTANZA ET AL. (1997) NATURAL CAPITAL: The Activist persona "
                "argues for the value of ecosystem services. Nature-based solutions outperform "
                "grey infrastructure over 30-year horizons."
            ),
            "ifc_standards": (
                "⚖️ IFC PERFORMANCE STANDARD 1 (2012): The Auditor persona "
                "argues fiduciary duty extends to physical climate risk preparedness and "
                "assessment/management of environmental and social risks."
            ),
        },
        "reflection_sensitisation": (
            "🪞 MIDPOINT BOARD ROOM MOMENT: Round 5 always triggers a reflection prompt. "
            "Moon (2004) shows that MID-EXPERIENCE reflection is more effective than "
            "post-experience because learners can still ACT on their insights. "
            "The prompt asks: 'If you could undo one decision from Rounds 1-5, which "
            "would it be?' This is Schön's (1983) REFLECTION-IN-ACTION — the goal is "
            "not correctness but the PRACTICE of strategic self-assessment."
        ),
        "discussion_prompts": [
            "Did the 2-round delay change your decision? Would you have chosen differently if protection was immediate?",
            "How do you value future resilience vs. current cash preservation?",
            "For Option C teams: how do you feel about blocking your Resilience M_R bonus?",
        ],
        "student_ux_coaching": {
            "ux_gap": "The stochastic dice roll (75% probability) happens invisibly in the backend. Students miss the core risk vs. resilience lesson.",
            "facilitator_prompt": "Before students commit, say: 'There is a 75% chance that a Category 4 cyclone will hit your operations THIS ROUND, regardless of your choice. Your decision is about FUTURE resilience, not current protection.' Make the randomness explicit.",
            "what_to_watch": "Students may feel cheated when damage occurs despite their investment. Explain: 'Your infrastructure takes 2 rounds to build. This is realistic — you cannot retrofit a factory in a single period.'",
            "ui_tip": "After commit, the results overlay will show the Prediction vs. Reality comparison. Ask students: 'Did you predict the cyclone damage?'",
        },
        "autonomous_agents_debrief": {
            "likely_stage": "agitated → hostile",
            "facilitator_note": "R5 is when the first agents may reach HOSTILE. The Community Activist (Megha Patrike) often leads — she has the lowest initial tolerance (65) and monitors water stress, which spikes during climate rounds.",
            "debrief_if_hostile": [
                "A stakeholder is now actively preparing action against your company. Could you have prevented this? At which round was the 'point of no return'?",
                "How does the asymmetric decay/recovery rate reflect real-world dynamics? (Gen Z: decay 10, recovery 5 vs Investor: decay 6, recovery 2)",
                "The Community Activist monitors water stress and social license — both of which are affected by your R5 climate decision. How does physical climate risk create social risk?",
            ],
        },
    },
    6: {
        "title": "Round 6: AI Bias — Algorithmic Ethics & the Truth Premium",
        "crisis_theme": "🤖 Your Software BU's AI recruitment tool discriminates against minorities. Monetise, reform, or conceal?",
        "talking_points": [
            "Option A (Monetise) is the moral hazard trap: +$10M revenue but −20 reputation triggers catastrophic Brain-Drain",
            "Option B (Ethical AI Overhaul) costs $8M but earns the 'Truth Premium' at R10: +0.15 M_R ≈ $54M terminal value uplift",
            "Option C (Quiet Patch) adds +10 governance risk — the same invisible tax as R2-C",
            "ROI of ethical investment: $8M cost → $54M terminal uplift = 675% return",
            "The contagion spike from Option A re-triggers the crisis engine — compounding R4 damage",
        ],
        "key_teaching_moment": "💡 Ethical infrastructure has measurable financial value. The $8M Ethical AI Overhaul generates a 675% ROI through the Truth Premium at terminal valuation. This is the strongest evidence in the simulation that ESG is not a cost — it's an investment.",
        "hr_tracking": "🧑‍💼 Inflation is now 6 rounds deep. OPEX has grown significantly. Teams with high burnout are seeing quadratic penalties. Ask teams: 'How much of your OPEX increase is from burnout vs. inflation?'",
        "engines_likely": ["supply_chain_contagion", "talent_neglect_surcharge", "technical_debt_penalty"],
        "connection_to_theory": {
            "box_title": "📖 Connection to Theory — AI Ethics & Moral Hazard",
            "insights": [
                {
                    "theory": "Moral Hazard",
                    "insight": "Option A (Monetise) is a textbook moral hazard: the team profits from a known defect because the harmed party (job applicants) bears the cost. The -20 reputation penalty is the market's delayed correction.",
                    "reference": "Arrow, K.J. (1963). Uncertainty and the Welfare Economics of Medical Care. American Economic Review, 53(5), 941-973.",
                },
                {
                    "theory": "Institutional Theory — Coercive Isomorphism",
                    "insight": "The EU AI Act (2024) creates coercive isomorphism — all firms in scope must adopt the same ethical AI governance structures. Option B's $8M cost is the PRICE of institutional legitimacy.",
                    "reference": "DiMaggio, P.J. & Powell, W.W. (1983). The Iron Cage Revisited. American Sociological Review, 48(2), 147-160.",
                },
                {
                    "theory": "Virtue Ethics",
                    "insight": "Option B asks: 'What kind of company do we want to BE?' not 'What is the profit-maximising choice?' The Truth Premium rewards virtue — Aristotle's argument that character generates its own returns.",
                    "reference": "Solomon, R.C. (1992). Ethics and Excellence: Cooperation and Integrity in Business. Oxford University Press.",
                },
            ],
        },
        "discussion_prompts": [
            "Would you monetise an ethically compromised AI tool for $10M? What's your real-world threshold?",
            "How do you value the 'Truth Premium' — is 675% ROI sufficient to justify the $8M cost?",
            "Which complexity engine has hurt you the most, and could you have prevented it?",
        ],
        "student_ux_coaching": {
            "ux_gap": "AI bias response looks like any other A/B/C choice — the moral gravity of the decision is under-communicated in the UI.",
            "facilitator_prompt": "Pause the timer. Read the briefing aloud. Say: 'This is not a financial decision — it's an ethical one. The person affected by your AI tool is a real job applicant. The $10M is revenue from discrimination.' Let that sit before allowing decisions.",
            "what_to_watch": "Students who choose Option A (Monetise) often regret it after seeing the -20 reputation drop. The Consequence DNA panel will trace this forward to R10.",
            "ui_tip": "The R6 Revelation (post-decision whistleblower twist) adds a second decision layer. Watch for surprise — this breaks the A/B/C habituation pattern.",
        },
        "stakeholder_migration": {
            "migrations_this_round": [
                "Local Communities: Keep Informed \u2192 Manage Closely (NGO coalition gave them legal power)",
                "Syndicate Banks: Keep Satisfied \u2192 Manage Closely (ONLY if electronics_blindspot active \u2014 R4 scandal activated their ESG desk)",
            ],
            "discussion_prompt": "The Deccan communities had HIGH legitimacy but LOW power in R1. What changed? (Answer: NGO coalition gave them institutional power \u2014 legal representation + media amplification. Mitchell et al. call this 'power acquisition through coalition'.)",
        },
        "journey_improvement": {
            "r6_revelation": {
                "facilitator_guidance": [
                    "POST-DECISION TWIST: After teams commit their A/B/C choice, a Whistleblower Leak revelation is triggered.",
                    "This is a MICRO-DECISION \u2014 3 response options appear: Accept Accountability, Legal Containment, Independent Investigation.",
                    "Legal Containment has a 40% BACKFIRE probability (Streisand Effect) \u2014 the stochastic outcome adds drama.",
                    "Kolb (1984): This forces Reflective Observation \u2014 teams must re-evaluate their initial choice in light of new information.",
                    "DEBRIEF QUESTION: 'Did the revelation change your opinion of your original choice? Would you choose differently now?'",
                    "Connect to R4: Teams who chose 'Deny & Deflect' in R4 may recognise a pattern \u2014 denial creates compounding governance risk.",
                ],
            },
        },
        "autonomous_agents_debrief": {
            "likely_stage": "hostile \u2192 FIRST TRIGGER possible",
            "facilitator_note": "\u26a0\ufe0f R4 is the earliest round a trigger can fire under maximal breach (audit 2026-09-04 probe); R6 under sustained poor management. The Gen Z Employee (Greta Berg, tolerance decay=10) or Journalist (Beth Colbert, decay=9) are most likely. Check the panel for HOSTILE agents.",
            "debrief_if_triggered": [
                "\u2605 A stakeholder has TRIGGERED. Read the crisis event aloud. Which agent was it? What was the cascading effect on other agents?",
                "The triggered agent's cascade chain has damaged other agents' tolerance. Can you identify the domino effect in your dashboard?",
                "Could you have prevented this trigger? Which specific metric(s) would you have needed to improve, and by how much?",
                "If Greta Berg (Gen Z) triggered a strike: 78% of your workforce participated. What does this tell you about the relationship between employee engagement and operational continuity?",
            ],
            "debrief_cascade_chain": [
                "The cascade chain creates a domino effect \u2014 one negligent trigger pulls others toward action. How does this mirror real-world corporate crises? (Example: Rana Plaza collapse triggered regulatory, investor, and media responses simultaneously)",
                "If you could reset ONE agent's tolerance to maximum, which would you choose and why?",
            ],
        },
    },
    7: {
        "title": "Round 7: Circularity — Synergy Unlock & Workforce Readiness Test",
        "crisis_theme": "♻️ EU circular economy regulations mandate 60% waste diversion. Comply, innovate, or synergise?",
        "talking_points": [
            "Option C (Waste-to-Energy) unlocks +0.15 M_R (STRAT-010: reduced from +0.30 because the OPEX benefit already compounds through EBITDA) plus the +0.30 synergy multiplier boost",
            "Workforce Readiness interdependency: if readiness < 40, synergy boost is reduced by 30%",
            "If readiness ≥ 60, synergy boost is AMPLIFIED by 10%",
            "Teams who earned 'early_decarboniser' in R3 get an additional +0.10 synergy",
            "Three rounds left — terminal value calculations are now critical",
        ],
        "key_teaching_moment": "💡 Operational transformation requires workforce capability. The R7 synergy boost is modified by workforce readiness — teams who neglected HR investment lose up to 30% of their synergy potential. This teaches: you can't execute circular economy strategies without skilled people.",
        "hr_tracking": "🧑‍💼 CRITICAL: Workforce readiness is NOW being tested. Display readiness scores. Teams with readiness < 40 are about to lose 30% of their synergy boost — a direct consequence of HR underinvestment.",
        "journey_improvement": {
            "r7_budget_allocation": {
                "facilitator_guidance": [
                    "MECHANIC VARIANT: After committing R7, teams see a Budget Allocation panel instead of standard results.",
                    "$15M CIRCULAR ECONOMY BUDGET: Three slider-based initiatives (Product Redesign, Take-Back Program, Waste-to-Energy).",
                    "This breaks the A/B/C habituation pattern — Thiagarajan (2006) recommends mechanic variation every 5-7 rounds.",
                    "SYNERGY THRESHOLDS: If a team allocates >$8M to Product Redesign, they earn the 'circular_redesign' bonus flag.",
                    "There is NO single right answer — optimal allocation depends on each team's current BU health and strategy.",
                    "DEBRIEF QUESTION: 'How did you decide the split? Did you optimise for one initiative or spread evenly? What trade-offs did you make?'",
                    "Connect to portfolio theory: diversification vs. concentration. Balanced allocation reduces risk but misses synergy bonuses.",
                ],
            },
        },
        "engines_likely": ["competitor_warning", "regulatory_ratchet_active"],
        "connection_to_theory": {
            "rbv_dynamic_capabilities": (
                "🎓 BARNEY (1991) RBV + TEECE (2007) DYNAMIC CAPABILITIES: The workforce "
                "readiness gate is a direct manifestation of RBV theory. Resources "
                "(capital) are necessary but not sufficient — you need capabilities "
                "(workforce readiness) to convert them into competitive advantage. "
                "Teams who invested in capital but not people have resources without capabilities. "
                "Ask: 'Is your workforce a VRIO resource? Is it Valuable, Rare, Inimitable, and Organised?'"
            ),
            "senge_learning_org": (
                "📚 SENGE (1990) THE LEARNING ORGANISATION: The synergy multiplier is "
                "systems thinking in action — it rewards teams who see connections between "
                "BUs rather than optimizing each BU in isolation. Waste-to-energy (Option C) "
                "is a CROSS-BU innovation — it requires the organisation to learn as a system, "
                "not as silos."
            ),
        },
        "discussion_prompts": [
            "What metrics matter most for your final score?",
            "If you could undo one decision from the entire game, which would it be?",
            "How did your HR investment (or lack thereof) affect your synergy outcome?",
        ],
        "student_ux_coaching": {
            "ux_gap": "Synergy multiplier (+0.30) is buried in the Advanced Metrics drawer. Students don't realize R7 gates R10 options.",
            "facilitator_prompt": "Tell students explicitly: 'Open the Advanced Metrics drawer in the left panel. Your Synergy Multiplier is the MOST IMPORTANT number for your terminal valuation.' Write the threshold on the board: Synergy > 80 = unlocks Option A in R10.",
            "what_to_watch": "Students with workforce readiness < 40 will lose 30% of their synergy boost. Call this out: 'If you neglected HR, you're about to pay for it.'",
            "ui_tip": "From R7+, the round-tier shifts to Integration — the UI automatically surfaces more historical data and cross-round analytics.",
        },
        "pillar_guidance": "For pillar teams: Mutual exclusivity is enforced in R7. Teams cannot combine synergy_unlock AND circular_redesign — they must choose one strategic path. If both are selected, synergy_unlock takes priority and circular_redesign impacts are reversed.",
        "autonomous_agents_debrief": {
            "likely_stage": "TRIGGER + CASCADE CHAIN",
            "facilitator_note": "By R7, poorly-managed teams may have 1-2 triggered agents with active cascade chains. The Journalist's cascade (→ Regulator, Investor, Community) is the most devastating. Well-managed teams should still have agents in dormant/watching.",
            "debrief_multi_trigger": [
                "How many of your autonomous stakeholders are in hostile or triggered state? What pattern do you see in the metrics that caused this?",
                "The Institutional Investor (Jay Buffet) is the most patient agent but the hardest to recover. If he's in HOSTILE, what does that signal about your long-term financial credibility?",
                "Compare your team's agent states with another team. What strategic choices explain the difference?",
            ],
        },
        "sandbox_cascade_multiplier": {
            "box_title": "💥 CASCADE MULTIPLIER — Regulatory Leak to Press (Sandbox)",
            "when_to_surface": "Surface this IF the Regulatory Sandbox is enabled AND Carson's crosswire has fired this round.",
            "narrative_setup": (
                "Commissioner Carson's regulatory probe has leaked to the press. "
                "Beth Colbert's tolerance has been reduced by 10 points — he is now closer "
                "to publishing a full exposé. This is the Cascade Multiplier: a reinforcing "
                "feedback loop where regulation → media attention → further corporate damage."
            ),
            "theory": (
                "Herman & Chomsky (1988) Manufacturing Consent: Media and regulatory agendas "
                "co-amplify through institutional feedback. A regulatory probe generates "
                "headline material; headlines create political pressure for stronger enforcement. "
                "The loop is self-reinforcing until the company either reforms or collapses."
            ),
            "debrief_prompts": [
                "The Regulator's probe has leaked to the Journalist. In real-world terms, name a company where a regulatory investigation was amplified by media coverage. (Examples: Enron/Arthur Andersen, Volkswagen Dieselgate, Wirecard)",
                "Beth Colbert's tolerance just dropped by 10. If he triggers, his cascade hits 3 OTHER agents. Can you map the full domino chain on the whiteboard?",
                "★ CRITICAL: If both the Regulator AND the Journalist trigger in the same session, you are on the path to Total Corporate Collapse. What would a real board do at this point?",
            ],
            "facilitator_action": (
                "Draw the cascade chain on the board: "
                "🏛️ Carson (Regulator) → 📰 Colbert (Journalist) → [📉 Investor, ✊ Activist, 👩‍💻 Gen Z]. "
                "Ask: 'How many dominoes are left standing?'"
            ),
        },
    },
    8: {
        "title": "Round 8: Blue Stress — Water Scarcity & Equitable Resource Allocation",
        "crisis_theme": "🌊 Multi-year drought threatens Pharma and Electronics. Equitable sharing, utilitarian priority, or mega-project?",
        "talking_points": [
            "Option B (Prioritise Electronics) is the utilitarian trap: saves $8M but −25 SLO on Pharma/CG",
            "Option B also BLOCKS the Resilience M_R bonus — same penalty as R5 Insurance Only",
            "Option C (Desalination) costs $30M with 2-round delay — can push treasury deeply negative",
            "Desalination completes at the R10 tick: −30 NCD plus a single $5M revenue credit — the plant's later payback falls outside the game, so inside it the option is $25M net and needs a financial cushion",
            "Blockchain traceability (from R2 pillar) provides scandal shielding this round",
        ],
        "key_teaching_moment": "💡 Equitable resource allocation (Option A) costs more upfront but preserves social license and M_R eligibility. Utilitarian prioritisation (Option B) saves money but creates a -25 SLO crater that triggers Regulatory Friction and blocks terminal bonuses worth ~$72M.",
        "hr_tracking": "🧑‍💼 Two rounds left for HR to make a difference. Burnout below 20 at R10 earns +0.05 M_R (Wellbeing Champion). Workforce readiness ≥ 75 earns +0.10 M_R (Workforce Excellence). Ask: 'Are you on track for either bonus?'",
        "engines_likely": ["greenwashing_scandal", "dividend_ratchet_triggered"],
        "connection_to_theory": {
            "box_title": "📖 Connection to Theory — Resource Allocation & Environmental Justice",
            "insights": [
                {
                    "theory": "Tragedy of the Commons",
                    "insight": "Option B (Prioritise Electronics) is Hardin's tragedy: one BU captures the shared resource (water) at the expense of others. The -25 SLO penalty represents the commons collapse.",
                    "reference": "Hardin, G. (1968). The Tragedy of the Commons. Science, 162(3859), 1243-1248.",
                },
                {
                    "theory": "Environmental Justice",
                    "insight": "Equitable allocation (Option A) reflects Schlosberg's environmental justice framework: fair distribution of environmental burdens AND meaningful participation in decision-making.",
                    "reference": "Schlosberg, D. (2007). Defining Environmental Justice: Theories, Movements, and Nature. Oxford University Press.",
                },
                {
                    "theory": "Natural Capital Accounting",
                    "insight": "Option C's $30M desalination with -30 NCD reduction demonstrates that natural capital debt has a PRICE — and that manufactured capital can substitute for natural capital, but at significant cost.",
                    "reference": "Costanza, R. et al. (1997). The Value of the World's Ecosystem Services and Natural Capital. Nature, 387, 253-260.",
                },
            ],
        },
        "discussion_prompts": [
            "Is it ethical to prioritise the highest-margin BU during a water crisis?",
            "How are you positioning for the terminal valuation debrief?",
            "What have you learned about the relationship between ESG and financial performance?",
        ],
        "student_ux_coaching": {
            "ux_gap": "Water dependency scores are shown but not linked to BU vulnerability. Students can't see the equity dimension.",
            "facilitator_prompt": "Say: 'Option B saves the most revenue BUT blocks your Resilience M_R bonus (-0.20 at R10). Is $8M in saved revenue worth ~$72M in terminal value?' Write this trade-off on the board.",
            "what_to_watch": "Students may not connect SLO (Social License) scores to the water decision. Point at the KPI cards: 'Which BUs have the lowest social license? What happens when you take THEIR water?'",
            "ui_tip": "The R8 Stakeholder Tribunal mechanic (post-decision) makes this visceral — stakeholders will challenge students face-to-face.",
        },
        "journey_improvement": {
            "r8_stakeholder_tribunal": {
                "facilitator_guidance": [
                    "MECHANIC VARIANT: After committing R8, teams face a Stakeholder Tribunal — 3 sequential challenges.",
                    "Three stakeholder groups (Community, Environmental NGO, Employee Union) each demand water allocation priority.",
                    "Each challenge has 3 response types: Comply, Negotiate, or Deflect. There is NO 'right' answer.",
                    "TIME PRESSURE: 90 seconds per challenge. This tests decision-making under realistic stakeholder pressure.",
                    "Freeman (1984): This mechanic teaches that sustainability leadership means managing LEGITIMATE COMPETING CLAIMS.",
                    "DEBRIEF: Compare team response patterns. Did they consistently comply? Negotiate? Deflect? What does this reveal about their stakeholder philosophy?",
                    "Connect to R1 Stakeholder Map: 'In R1, you classified stakeholders by power/interest. Now they're AT YOUR DOOR. Does your classification strategy hold up?'",
                ],
            },
        },
        "autonomous_agents_debrief": {
            "likely_stage": "MULTIPLE TRIGGERS + SYSTEMIC CASCADE",
            "facilitator_note": "R8 water crisis often triggers the Community Activist (Megha Patrike) via water stress and social license collapse. If Option B (Prioritise Electronics) is chosen, expect −25 SLO to push Patrike into HOSTILE/TRIGGERED.",
            "debrief_water_cascade": [
                "The Community Activist (Megha Patrike) monitors water stress directly. How did your R8 water allocation decision affect her tolerance?",
                "If Patrike triggered a Community Blockade: 'Muressons has destroyed our water table.' How does this connect to your R5 climate infrastructure choice?",
                "The cascade from Community Activist hits the Journalist AND the Gen Z Employee. Why does community anger amplify through these specific channels?",
            ],
            "cascade_multiplier_warning": (
                "⚠️ CASCADE MULTIPLIER CHECK: If the Regulatory Sandbox fired Carson's crosswire in R7, "
                "Beth Colbert entered R8 with reduced tolerance. Combined with the R8 water crisis "
                "and the journalist's natural decay, Colbert may now be at HOSTILE or TRIGGERED. "
                "If Colbert triggers, his cascade chain hits 3 agents simultaneously: the Regulator "
                "(reinforcing loop), the Investor (capital flight), and the Community Activist "
                "(social license collapse). This is the Total Corporate Collapse scenario — "
                "all 5 agents trigger within 1-2 rounds. Ask: 'Is your company still recoverable, "
                "or has the feedback loop passed the point of no return?'"
            ),
        },
    },
    9: {
        "title": "Round 9: Just Transition — The Social Cost of Decarbonisation",
        "crisis_theme": "✊ 2,000 jobs at risk from factory closures. Close immediately, manage transition, or invest in community?",
        "talking_points": [
            "Option A (Immediate Closure) has a STRIKE MECHANIC: 50-66% chance of losing ALL revenue for one round",
            "Strike probability increases with burnout: at burnout=70, P(strike)=58%",
            "Option C (Community Fund) earns +0.18 M_R (Community Champion) — highest just-transition bonus",
            "Option B (Managed Transition) earns +0.12 M_R — still meaningful, narrowed gap from previous 0.10",
            "This is the final substantive round — next round is the Grand Finale",
        ],
        "key_teaching_moment": "💡 The strike mechanic connects 9 rounds of HR and social license decisions into one dramatic moment. Teams who neglected workforce wellbeing face a 50-66% chance of catastrophic revenue loss. This teaches: social license is not optional — it's insurance against systemic risk.",
        "hr_tracking": "🧑‍💼 FINAL HR CHECKPOINT: Burnout directly affects strike probability. Display burnout scores publicly. Teams with burnout > 50 and SLO < 50 face a 52-66% strike chance. This is the ultimate consequence of HR neglect.",
        "engines_likely": ["inflation_index_applied", "competitor_warning"],
        "connection_to_theory": {
            "rawlsian_justice": (
                "🎓 RAWLS (1971) VEIL OF IGNORANCE: Option C (Community Fund) is the "
                "Rawlsian choice — it asks 'what would we choose if we didn't know "
                "whether we were the CEO or the factory worker being laid off?' "
                "Option A (Immediate Closure) is purely utilitarian. Use this to "
                "surface: 'Which ethical framework is your team ACTUALLY using?'"
            ),
            "freeman_stakeholder_theory": (
                "📚 FREEMAN (1984) STAKEHOLDER THEORY: The strike mechanic is Freeman's "
                "thesis made visceral. Shareholders can be satisfied through dividends, "
                "but if employees (stakeholders with HIGH urgency and legitimacy) are "
                "neglected, they have the power to DESTROY shareholder value overnight. "
                "The strike is not a punishment — it's a demonstration of stakeholder interdependence."
            ),
            "sen_capabilities": (
                "📚 SEN (1999) CAPABILITY APPROACH: The $20M Community Fund doesn't just "
                "transfer money — it builds capabilities (retraining, reskilling). "
                "The M_R bonus rewards capability building, not charity. Ask: "
                "'What's the difference between compensating a laid-off worker and "
                "giving them a new career?'"
            ),
        },
        "reflection_sensitisation": (
            "🪞 MOON (2004): If teams chose Option A, a Board Room Moment is highly likely "
            "(contagion risk will spike). The reflection prompt will ask about ROOT CAUSE. "
            "Resist the urge to lecture — Moon's framework shows that facilitator-imposed "
            "interpretations are LESS effective than learner-generated ones. Let teams "
            "connect the dots: 'My strike probability is 58% BECAUSE I chose Overtime Push "
            "in R4 BECAUSE I was in crisis BECAUSE I chose Surface Scan in R1.' "
            "This causal chain is the entire pedagogical payoff of the simulation."
        ),
        "discussion_prompts": [
            "What surprised you most about the strike risk calculation?",
            "How does your burnout score reflect your HR investment strategy?",
            "Is the $20M Community Fund worth +0.18 M_R? What's the real-world equivalent?",
        ],
        "autonomous_agents_debrief": {
            "likely_stage": "SYSTEMIC COLLAPSE for negligent teams",
            "facilitator_note": "R9 is where cascade chains complete. Teams with 3+ triggered agents are experiencing the simulation's full 'stakeholder systemic failure' mode. The Regulator's fine (4% revenue) and Investor's divestment (−8% treasury, +200bps cost of capital) are compounding.",
            "debrief_systemic_failure": [
                "★ CAPSTONE AGENT QUESTION: Trace the cascade chain from your FIRST triggered agent to your LAST. What was the domino sequence?",
                "The Institutional Investor (Jay Buffet) has the slowest recovery rate (2/round). If he triggered, can you mathematically recover before R10? What does this teach about institutional trust?",
                "Compare: the Gen Z Employee's fast decay/fast recovery with the Investor's slow decay/slow recovery. What different engagement strategies would you use for each in a real company?",
                "If ALL 5 agents have triggered: your company has experienced total stakeholder system failure. In real-world terms, name a company that experienced something similar. (Examples: Wirecard, Theranos, Lehman Brothers)",
            ],
        },
        "student_ux_coaching": {
            "ux_gap": "Strike probability is delivered as a mailbox message, not a visual threat meter. The just transition stakes feel abstract.",
            "facilitator_prompt": "Read the strike probability ALOUD: 'Your team has a X% chance of losing ALL revenue next round.' Let the room react. Then say: 'This probability is a FUNCTION of your burnout index. Open your Advanced Metrics. What is your burnout?'",
            "what_to_watch": "Students with burnout > 50 face strike probabilities above 52%. Their faces when they see this are a teaching moment in themselves.",
            "ui_tip": "The Consequence DNA panel now shows the full R1→R4→R9 chain. Ask: 'Can you trace your strike risk back to a Round 1 decision?'",
        },
        "pillar_guidance": "For pillar teams: Mutual exclusivity is enforced in R9. Teams cannot combine community_fund AND managed_transition — they must choose one closure approach. community_fund takes priority.",
    },
    10: {
        "title": "Round 10: Grand Finale — Activist Ultimatum & Terminal Valuation",
        "crisis_theme": "🏛️ Activist investors demand restructuring. Resist, spin-off, or divest?",
        "talking_points": [
            "SHOW THE M_R BREAKDOWN: walk teams through each bonus/penalty earned across 10 rounds",
            "Option A (Resist & Integrate) is GATED: requires Synergy Score > 80",
            "Option C (Divest) gives +$25M cash but WIPES synergy to 1.0 — destroying all R7 value",
            "Terminal Value formula: V_T = (Terminal EBITDA + Green Fund) × Exit Multiple (WACC-coupled, 6-18×, 12× at baseline) × M_R",
            "Max M_R achievable: 1.93 legacy / 2.02 pillar (pinned by test_mr_ceilings_unchanged; global clamp 2.05)",
        ],
        "key_teaching_moment": "💡 USE THE SPREAD: Regenerative Titan (~$700M) vs Stranded Relic (~$27M) = 25× difference. This 25× gap is driven ENTIRELY by ESG decisions across 10 rounds. No single decision caused it — it's the compound effect of consistent strategic alignment.",
        "mr_breakdown_guide": {
            "base": {"value": 1.0, "source": "Starting multiple"},
            "synergy_bonus": {"value": 0.15, "source": "R7: Chose waste-to-energy / synergy unlock (STRAT-010: reduced from 0.30)"},
            "resilience_bonus": {"value": 0.20, "source": "R5/R8: Avoided insurance-only and electronics prioritisation"},
            "truth_premium": {"value": 0.15, "source": "R6: Chose ethical AI overhaul"},
            "community_champion_bonus": {"value": 0.18, "source": "R9: Invested $20M in community fund"},
            "just_transition_bonus": {"value": 0.12, "source": "R9: Chose managed transition (if no community fund)"},
            "workforce_bonus": {"value": 0.10, "source": "Cumulative HR: Workforce readiness ≥ 75 at R10"},
            "wellbeing_bonus": {"value": 0.05, "source": "Cumulative HR: Average burnout < 20 at R10"},
            "instability_discount": {"value": -0.40, "source": "Penalty: Average social license < 75"},
        },
        "capstone_discussion": {
            "titan_vs_relic": "Display the highest and lowest terminal values in the cohort. Ask: 'What decisions separated the Regenerative Titan from the Stranded Relic?' Walk through the M_R breakdown for both.",
            "key_decision_audit": "Ask each team: 'Which single round had the biggest impact on your terminal value?' Most will point to R1 (audit), R4 (crisis), R7 (synergy), or R9 (transition).",
            "real_world_parallel": "The simulation compressed 5 years of corporate ESG strategy into 10 decisions. In reality, these decisions play out over decades — but the compounding dynamics are identical.",
        },
        "connection_to_theory": {
            "kolb_experiential_cycle": (
                "🎓 KOLB (1984) EXPERIENTIAL LEARNING CYCLE: R10 is the REFLECTIVE OBSERVATION "
                "and ABSTRACT CONCEPTUALISATION phases. The 10 rounds provided Concrete "
                "Experience and Active Experimentation. Now extract theory: "
                "'What mental model did you enter with? How has it changed?' "
                "The M_R breakdown IS the abstract conceptualisation — it converts experience "
                "into quantifiable cause-and-effect relationships."
            ),
            "porter_shared_value": (
                "📚 PORTER & KRAMER (2011) CREATING SHARED VALUE: The terminal value gap "
                "between Regenerative Titan and Stranded Relic is empirical proof of CSV. "
                "Teams that created shared value (ESG + financial returns) achieved 25× "
                "higher valuations than those who treated ESG as a cost centre. "
                "This is not ideology — it's compound mathematics."
            ),
            "meadows_systems_thinking": (
                "📚 MEADOWS (2008) THINKING IN SYSTEMS: The consequence waterfall reveals "
                "feedback loops that were invisible during gameplay. NCD compounding, "
                "stakeholder fatigue, brain drain cascades — these are all reinforcing "
                "feedback loops. Ask: 'Where were the BALANCING loops?' "
                "(Answer: the Turnaround Arc, Option T restructuring, Board Room Moments.)"
            ),
        },
        "reflection_sensitisation": (
            "🪞 CAPSTONE REFLECTION: Collect ALL Board Room Moment responses from Rounds 1-9. "
            "Read them back to each team chronologically. Moon (2004): 'The most powerful "
            "learning occurs when learners see their OWN thinking evolve over time.' "
            "Teams will see themselves shift from 'we need more money' (symptom-thinking) "
            "to 'we need to reduce NCD compounding' (systems-thinking). "
            "This metacognitive arc is the simulation's deepest pedagogical achievement. "
            "If you only do ONE debrief activity, do THIS."
        ),
        "momentum_debrief": (
            "📈 ATTRIBUTION THEORY (WEINER, 1985): Display each team's Momentum Score "
            "trajectory. Teams that recovered from low positions deserve public recognition. "
            "The Comeback Kid bonus (+0.05 M_R) rewards EFFORT, not just outcomes. "
            "This reframes the narrative: the team that fell to -$10M and recovered to "
            "+$20M has a more impressive story than the team that cruised at $50M."
        ),
        "hr_tracking": "🧑‍💼 FINAL HR ROI REPORT: Display the cumulative HR ROI for each team. Teams who invested consistently in HR should see: (1) lower OPEX from avoided burnout penalties, (2) higher synergy from workforce readiness, (3) lower strike risk from R9, (4) up to +0.15 M_R from workforce + wellbeing bonuses.",
        "engines_likely": [],
        "discussion_prompts": [
            "★ CAPSTONE: What was the terminal value spread in your cohort? What drove the gap?",
            "Which M_R bonus did you earn? Which did you miss, and which round caused it?",
            "What was your biggest strategic mistake, and when did you realize it?",
            "How would you advise the next cohort playing this simulation?",
            "What real-world corporate decision does this simulation remind you of?",
        ],
        "student_ux_coaching": {
            "ux_gap": "Terminal valuation formula is not visible during decision-making. Students can't calculate the impact of their choice.",
            "facilitator_prompt": "Direct students to the Terminal Valuation Calculator now visible in their center column (Finale tier). Walk through the formula: TV = EBITDA × M_R × EV Multiple. Ask: 'Which component can you STILL affect with your R10 choice?'",
            "what_to_watch": "The Consequence DNA panel now shows the complete 10-round causal chain. This IS the debrief. Project one team's DNA chain on the screen.",
            "ui_tip": "The Prediction vs. Reality comparison will appear after commit, showing metacognitive accuracy across all rounds. Use this as a discussion trigger: 'Were you getting BETTER at predicting outcomes as the game progressed?'",
        },
        "autonomous_agents_debrief": {
            "likely_stage": "FINAL STATE — full agent audit",
            "facilitator_note": "Display each team's final agent state. The agent panel IS a stakeholder management report card. Teams with all agents in dormant/watching achieved stakeholder excellence. Teams with 3+ triggers experienced systemic stakeholder failure.",
            "debrief_final_audit": [
                "★ AGENT REPORT CARD: How many agents are in each stage? (dormant/watching/agitated/hostile/triggered). What grade would you give your stakeholder management?",
                "Which agent triggered FIRST in your simulation? What metrics caused it? Could you have prevented the cascade chain?",
                "The Journalist (Beth Colbert) has the most cascade targets (3). How does media amplification accelerate corporate crises in practice?",
                "Compare the Gen Z Employee's fast decay/fast recovery with the Institutional Investor's slow decay/slow recovery. What does this tell you about different stakeholder engagement strategies in your future career?",
                "If you could replay the simulation with ONLY the goal of keeping all agents in dormant, which 3 decisions would you change?",
                "★ TRANSFER: Name one real-world stakeholder in your industry who behaves like each of the 5 agents. How would you manage them differently after this experience?",
            ],
        },
    },
}

# ── BRSR NGRBC Teleprompter Overlays ─────────────────────────────
# Injected into the standard teleprompter when the BRSR NGRBC track is enabled.
# Keyed by main simulation round number where the BRSR content is most relevant.
_BRSR_TELEPROMPTER_OVERLAYS = {
    1: {
        "brsr_round": "BRSR R1 — Governance & Ethics (NGRBC Principles 1 & 7)",
        "banner": "🇮🇳 BRSR TRACK ACTIVE: SEBI's NGRBC-aligned deep-dive begins this round.",
        "facilitator_guidance": [
            "The BRSR track opens with Governance & Ethics — SEBI's Essential Indicators for board-level responsible conduct.",
            "Option A (Radical Transparency) sets the 'brsr_pioneer' flag — this is the Leadership Indicator path and unlocks the +0.05 ESG Alpha Dividend at terminal valuation.",
            "Option C (Reactive Disclosure) sets 'governance_fragility' — this will trigger a Whistleblower Governance Leak crisis in BRSR Round 5, draining $2.5M from corporate treasury.",
            "KEY TEACHING MOMENT: Ask teams — 'What is the difference between Essential and Leadership indicators under SEBI BRSR? Why does SEBI distinguish them?'",
        ],
        "debrief_prompts": [
            "Under NGRBC Principle 1, what does 'responsible business conduct' mean beyond legal compliance?",
            "SEBI mandates BRSR for the top 1,000 listed companies. Why 1,000? What market signal does this threshold create?",
            "If you chose Reactive Disclosure: you fulfilled Essential Indicators but skipped Leadership. Is that acceptable to institutional investors?",
        ],
    },
    3: {
        "brsr_round": "BRSR R2 — Workforce Well-being (NGRBC Principles 3 & 5)",
        "banner": "🇮🇳 BRSR TRACK: Workforce well-being and living wage decisions.",
        "facilitator_guidance": [
            "This round tests whether teams adopt a living wage across tier-1 suppliers — a Leadership Indicator under NGRBC Principle 3.",
            "The living wage decision connects directly to the main simulation's HR tracking — teams who neglect HR here AND in the core loop compound their workforce fragility.",
            "Essential vs. Leadership: minimum wage compliance is Essential; living wage adoption is Leadership. The distinction mirrors SEBI's actual BRSR framework.",
        ],
        "debrief_prompts": [
            "What is the difference between 'minimum wage' and 'living wage'? Why does BRSR distinguish them?",
            "How does your BRSR workforce decision align with your core simulation HR investment strategy?",
        ],
    },
    5: {
        "brsr_round": "BRSR R3 — Environmental Footprint (NGRBC Principles 2 & 6)",
        "banner": "🇮🇳 BRSR TRACK: Environmental stewardship and circular procurement.",
        "facilitator_guidance": [
            "NGRBC Principle 6 (Environment) is the most data-intensive BRSR section — circular procurement requires Scope 3 tracking infrastructure.",
            "Teams who chose deep audit data in the core simulation (R1 Option B) will find this round easier — the data infrastructure carries over.",
            "The 'brsr_circular_symbiosis' flag unlocks additional environmental scoring at terminal valuation.",
        ],
        "debrief_prompts": [
            "How does your Scope 3 emissions strategy from the main simulation affect your BRSR environmental score?",
            "NGRBC Principle 2 requires 'sustainability in products and services.' How do you measure that?",
        ],
    },
    7: {
        "brsr_round": "BRSR R4 — Value Chain Assurance (NGRBC Principles 4, 8 & 9)",
        "banner": "⚠️ BRSR CRISIS WINDOW: Greenwash risk assessment. SEBI show-cause notice may trigger.",
        "facilitator_guidance": [
            "★ CRITICAL: If teams accumulated the 'brsr_greenwash_risk' flag in earlier rounds, the engine will autonomously inject a 'SEBI Show-Cause Notice' crisis this round.",
            "The show-cause notice reduces Group Reputation by -12 — a severe penalty representing SEBI regulatory enforcement.",
            "This teaches that greenwashing in BRSR disclosures has real regulatory consequences — SEBI actively monitors Leadership vs. Essential indicator mismatch.",
            "For teams WITHOUT greenwash risk: this round rewards consistent integrity. Their value chain assurance is credible.",
        ],
        "debrief_prompts": [
            "A SEBI show-cause notice is a formal regulatory escalation. What are the real-world consequences for listed companies?",
            "How does value chain greenwashing differ from product greenwashing? Which is harder to detect?",
            "NGRBC Principle 8 (Inclusive Growth) requires addressing community impacts. How does your supply chain affect local communities?",
        ],
    },
    9: {
        "brsr_round": "BRSR R5 — Integrated Reporting & BRSR Core (Final Assessment)",
        "banner": "🇮🇳 BRSR TRACK FINALE: Integrated reporting and terminal BRSR assessment.",
        "facilitator_guidance": [
            "★ GOVERNANCE CRISIS: If 'governance_fragility' flag is active from BRSR R1, the engine injects a 'Whistleblower Governance Leak' crisis, draining $2.5M from treasury.",
            "This is the 'long-tail' consequence — a governance shortcut taken 8 rounds ago now materialises as a crisis. Use this as the primary debrief teaching moment.",
            "Teams achieving 'BRSR Pioneer' status earn the brsr_net_positive_dividend (+0.05 M_R) — permanently boosting their Regenerative Multiple.",
            "Ask teams to compare their BRSR Dashboard status with their core simulation performance. Are they consistent, or is there a disconnect?",
        ],
        "debrief_prompts": [
            "★ CAPSTONE: Trace the governance_fragility flag from BRSR R1 to this crisis. What was the compounding cost of the shortcut?",
            "What does 'reasonable assurance' mean in BRSR reporting? How is it different from 'limited assurance'?",
            "If you achieved BRSR Pioneer: what strategic decisions enabled it? Would a real company make the same choices?",
            "How does the BRSR framework's Essential/Leadership structure compare to GRI or TCFD reporting?",
        ],
    },
    2: {
        "brsr_round": "BRSR R6 — Human Rights Realities (NGRBC Principle 5)",
        "banner": "🇮🇳 BRSR TRACK: Human rights due diligence and Tier-2 supply chain exposure.",
        "facilitator_guidance": [
            "NGRBC Principle 5 requires companies to respect and promote human rights — not just within direct operations but across the value chain.",
            "Option A (Deep HRDD with Digital Traceability) deploys blockchain-enabled Tier-2 supplier monitoring. Sets the 'deep_hrdd_active' flag — providing assurance bonus in later rounds.",
            "Option C (Tier-1 Only Compliance) creates the 'tier2_human_rights_risk' flag — Tier-2 blind spots will surface in later rounds when international buyers audit the supply chain.",
            "KEY TEACHING MOMENT: Ask teams — 'Where does your corporate responsibility end? At Tier-1 suppliers? Tier-2? The raw material source?'",
        ],
        "debrief_prompts": [
            "India's informal sector constitutes over 80% of employment. How does formalisation affect BRSR human rights compliance?",
            "What is the difference between 'knowing about' human rights risks and 'acting on' them under NGRBC P5?",
            "If international buyers suspend contracts due to Tier-2 issues, whose fault is it — yours or the supplier's?",
        ],
    },
    4: {
        "brsr_round": "BRSR R7 — Policy Advocacy & Lobbying Transparency (NGRBC Principle 7)",
        "banner": "🇮🇳 BRSR TRACK: Corporate policy advocacy and responsible lobbying.",
        "facilitator_guidance": [
            "NGRBC Principle 7 addresses policy advocacy — this is one of the most politically sensitive BRSR areas.",
            "Option A (Progressive Public Stance) publicly advocates for stronger ESG regulation. Sets 'policy_leadership' — acts as a terminal valuation shield against governance fragility.",
            "Option C (Industry Cartel Lobbying Memo) secretly signs a joint memo against carbon pricing. Sets 'greenwash_advocacy' — a reputational time bomb if leaked.",
            "★ CRITICAL: Connect this to real-world debates about corporate lobbying disclosure (e.g., InfluenceMap data on oil & gas companies publicly supporting Paris Agreement while funding anti-climate lobbying).",
        ],
        "debrief_prompts": [
            "Is it legitimate for companies to lobby against regulations they believe are economically harmful?",
            "How does India's Companies Act Section 135 CSR mandate interact with corporate policy advocacy?",
            "If your greenwash_advocacy flag gets leaked in later rounds, how would you explain it to institutional investors?",
        ],
    },
    6: {
        "brsr_round": "BRSR R8 — MSME & Vendor Protection (NGRBC Principle 8)",
        "banner": "🇮🇳 BRSR TRACK: MSME payment practices and inclusive supply chain development.",
        "facilitator_guidance": [
            "NGRBC Principle 8 (Inclusive Growth) focuses on equitable relationships with MSMEs — India's backbone employers.",
            "Option A (TReDS Integration + Inclusive Sourcing) onboards MSME vendors onto the Trade Receivables Discounting System. Sets 'msme_champion' — a crisis severity shield in later rounds.",
            "Option C (Working Capital Hoarding) delays MSME payments beyond 45 days for treasury benefit. Sets 'working_capital_hoarder' — triggers a SEBI penalty ($1.5M) in Round 8.",
            "KEY TEACHING MOMENT: Explain Section 43B(h) of the Income Tax Act — payments to MSMEs beyond 45 days are now non-deductible. This makes working capital hoarding economically irrational.",
        ],
        "debrief_prompts": [
            "What is TReDS and why did SEBI mandate its adoption for top listed companies?",
            "How does the 45-day payment rule (Section 43B(h)) change the corporate incentive structure for MSME dealings?",
            "Is inclusive sourcing (reserving 10% procurement for MSME vendors) fair or distortionary?",
        ],
    },
    8: {
        "brsr_round": "BRSR R9 — BRSR Core Statutory Mandate & Assurance (NGRBC P4/P9)",
        "banner": "⚠️ BRSR CRISIS WINDOW: BRSR Core statutory mandate enforcement. Unverified claims face correction expense.",
        "facilitator_guidance": [
            "★ CRITICAL: If 'brsr_greenwash_risk' persists from earlier rounds AND 'brsr_core_assured' is absent, the engine imposes a $4M correction expense this round.",
            "This represents the real-world BRSR Core glide path — SEBI is progressively mandating reasonable assurance for value chain metrics. Companies without Big 4 verification face statutory penalties.",
            "Teams that secured BRSR Core assurance in Round 4 are protected. Ask: 'Was the assurance investment worth it now?'",
            "Option A (Full CSRD-BRSR dual alignment) earns the 'csrd_aligned' flag — recognised by European institutional investors.",
        ],
        "debrief_prompts": [
            "What is the real BRSR Core glide path timeline set by SEBI? (Hint: top 150 → top 500 → top 1000)",
            "How does BRSR reasonable assurance differ from financial audit assurance?",
            "If you faced the $4M correction expense: what would you do differently in a real BRSR filing?",
        ],
    },
    10: {
        "brsr_round": "BRSR R10 — Integrated Double Materiality & CSRD Alignment (Terminal)",
        "banner": "🇮🇳 BRSR TRACK FINALE: Double materiality assessment and terminal BRSR filing.",
        "facilitator_guidance": [
            "This is the terminal BRSR round. Teams must reconcile Indian BRSR with global CSRD double materiality requirements.",
            "Option A (Full Double Materiality Integrated Report) achieves maximum BRSR filing premium. Requires both financial and impact materiality assessment.",
            "Teams with accumulated governance fragility AND no policy leadership face a terminal governance reckoning: ESG rating downgrade (-6 Reputation).",
            "★ CAPSTONE: Walk teams through their full 10-round BRSR journey. Which flags compounded? Which crises were avoidable? What would they change?",
            "Connect to the main simulation terminal valuation: BRSR Pioneer status contributes +0.05 to the Regenerative Multiple.",
        ],
        "debrief_prompts": [
            "★ TERMINAL: Compare your BRSR archetype with your main simulation archetype. Are they consistent?",
            "How would you reconcile BRSR (Indian) and CSRD (European) reporting in a multinational context?",
            "What is the business case for double materiality reporting? Is it a cost or an investment?",
            "If you could replay the 10 BRSR rounds with one strategic change, what would it be?",
        ],
    },
}

@teleprompter_router.get("/teleprompter/{round_number}", summary="Get facilitator teleprompter script")
async def get_teleprompter(round_number: int, _g: None = Depends(require_facilitator)):
    script = _TELEPROMPTER_SCRIPTS.get(round_number, {
        "title": f"Round {round_number}",
        "talking_points": ["Continue guiding teams through their decisions."],
        "engines_likely": [],
        "discussion_prompts": ["What patterns are emerging in your strategy?"],
    })
    # Inject Real World Parallel card
    try:
        from real_world_parallels import get_parallel
        parallel = get_parallel(round_number)
        if parallel:
            script["real_world_parallel"] = parallel
    except ImportError:
        pass
    # Inject Three-Word Anchor
    try:
        from round_recap_engine import get_three_word_anchor
        script["three_word_anchors"] = {
            "option_a": get_three_word_anchor(round_number, "option_a"),
            "option_b": get_three_word_anchor(round_number, "option_b"),
            "option_c": get_three_word_anchor(round_number, "option_c"),
        }
    except ImportError:
        pass
    # Inject Debrief Protocol for R10
    if round_number == 10:
        try:
            from pedagogical_engine import DEBRIEF_PROTOCOL
            script["debrief_protocol"] = DEBRIEF_PROTOCOL
        except ImportError:
            pass
    # Inject Board Room prompts
    try:
        from pedagogical_engine import BOARD_ROOM_PROMPTS
        script["board_room_prompts"] = BOARD_ROOM_PROMPTS
    except ImportError:
        pass
    # Inject BRSR NGRBC overlay if track is enabled
    try:
        from admin_shared import _god_mode_settings
        if _god_mode_settings.get("brsr_ngrbc_enabled", False):
            brsr_overlay = _BRSR_TELEPROMPTER_OVERLAYS.get(round_number)
            if brsr_overlay:
                script["brsr_ngrbc_overlay"] = brsr_overlay
    except ImportError:
        pass
    return {"round": round_number, "script": script}


@teleprompter_router.get("/teleprompter", summary="Get all teleprompter scripts")
async def get_all_teleprompter(_g: None = Depends(require_facilitator)):
    import copy
    scripts = copy.deepcopy(_TELEPROMPTER_SCRIPTS)
    # Inject BRSR NGRBC overlay into scripts when enabled
    try:
        from admin_shared import _god_mode_settings
        if _god_mode_settings.get("brsr_ngrbc_enabled", False):
            for rnd, overlay in _BRSR_TELEPROMPTER_OVERLAYS.items():
                if rnd in scripts:
                    scripts[rnd]["brsr_ngrbc_overlay"] = overlay
    except ImportError:
        pass
    return {"scripts": scripts}


# ═══════════════════════════════════════════════════════════════
#  AUTONOMOUS AGENT LIVE STATE (Session-Aware)
#  Facilitator reads live agent states for a specific session
#  to surface context-appropriate debrief questions.
# ═══════════════════════════════════════════════════════════════

_AGENT_DEBRIEF_BANK = {
    "dormant": [],
    "watching": [
        "An autonomous stakeholder has started monitoring your company. What metric crossed their red line?",
        "Which agent entered WATCHING first? What does their personality type tell you about their priorities?",
    ],
    "agitated": [
        "A stakeholder is now publicly critical. How does this affect your reputation trajectory?",
        "Compare the Regulator's 'methodical' escalation with the Gen Z Employee's 'passionate' escalation. Which is more dangerous?",
    ],
    "hostile": [
        "A stakeholder is preparing action. Could you have prevented this? At which round was the 'point of no return'?",
        "How does the asymmetric decay/recovery rate (fast to anger, slow to forgive) reflect real-world trust dynamics?",
    ],
    "triggered": [
        "\u2605 A stakeholder has TRIGGERED. Read the crisis event aloud. What was the cascading effect on other agents?",
        "Could you have prevented this trigger? Which metric(s) needed improvement, and by how much?",
        "The cascade chain creates a domino effect. How does this mirror real-world corporate crises?",
        "If you could reset ONE agent's tolerance to maximum, which would you choose and why?",
    ],
}


@teleprompter_router.get(
    "/teleprompter/agents/{session_id}",
    summary="Get live autonomous agent state + contextual debrief questions for a session",
)
async def get_agent_teleprompter(request: Request, session_id: str, _guard: None = Depends(require_facilitator)):
    """Reads live agent state from a session and returns contextual debrief questions."""
    # F-21 (launch audit 2026-09-01): cross-cohort access — this returned live
    # per-team agent state for ANY session id with no credential at all.
    from admin_router import _assert_session_visible
    await _assert_session_visible(request, session_id)
    try:
        # Railway audit §1.1: read via the parity db API (works under both
        # stores) instead of the memory store's private dict.
        import database as _db_api
        _row = await _db_api.fetch_latest_state(session_id)
        if not _row:
            return {"session_id": session_id, "agents": None, "message": "Session not found"}

        gs = dict(_row["global_state"])
        gs.setdefault("round_number", _row.get("round_number", 1))
        aa_state = gs.get("autonomous_agents") or {}
        agents_raw = aa_state.get("agents", {})

        if not agents_raw:
            return {"session_id": session_id, "agents": None, "message": "Autonomous agents not active"}

        from autonomous_agents import AGENT_PROFILES, get_agent_summary
        summary = get_agent_summary(aa_state)

        # Build facilitator-facing alert card per agent
        agent_alerts = []
        worst_stage = "dormant"
        stage_order = {"dormant": 0, "watching": 1, "agitated": 2, "hostile": 3, "triggered": 4}

        for agent in summary:
            stage = agent.get("stage", "dormant")
            if stage_order.get(stage, 0) > stage_order.get(worst_stage, 0):
                worst_stage = stage

            profile = AGENT_PROFILES.get(agent["agent_id"], {})
            alert = {
                "agent_id": agent["agent_id"],
                "name": agent["name"],
                "icon": agent["icon"],
                "stage": stage,
                "tolerance": agent["tolerance"],
                "max_tolerance": agent["max_tolerance"],
                "tolerance_pct": round(agent["tolerance"] / max(agent["max_tolerance"], 1) * 100, 1),
                "trend": agent["trend"],
                "patience_counter": agent["patience_counter"],
                "triggered_round": agent.get("triggered_round"),
                "dialogue": profile.get("stage_dialogue", {}).get(stage, ""),
            }
            agent_alerts.append(alert)

        # Select contextual debrief questions based on worst stage
        debrief_questions = _AGENT_DEBRIEF_BANK.get(worst_stage, [])

        # Add cascade log summary
        cascade_log = aa_state.get("cascade_log", [])
        total_triggers = aa_state.get("total_triggers", 0)

        return {
            "session_id": session_id,
            "round_number": gs.get("round_number", 1),
            "worst_stage": worst_stage,
            "total_triggers": total_triggers,
            "agents": agent_alerts,
            "contextual_debrief_questions": debrief_questions,
            "cascade_log": cascade_log[-10:],  # Last 10 cascades
            "facilitator_alert": (
                f"\u26a0\ufe0f {total_triggers} agent(s) triggered. Worst stage: {worst_stage.upper()}. "
                f"Use the debrief questions below."
                if total_triggers > 0 else
                f"Agent system active. Worst stage: {worst_stage.upper()}."
            ),
        }
    except Exception as exc:
        return {"session_id": session_id, "agents": None, "error": str(exc)}


# ═══════════════════════════════════════════════════════════════
#  PEDAGOGICAL SCAFFOLDING API ENDPOINTS
#  New endpoints for metacognitive features, formative assessment,
#  and learner journey support.
# ═══════════════════════════════════════════════════════════════

@teleprompter_router.get("/pedagogical/toggles", summary="Get default pedagogical feature toggles")
async def get_pedagogical_toggles():
    """Returns the default pedagogical toggles and difficulty tier options."""
    from pedagogical_engine import DEFAULT_PEDAGOGICAL_TOGGLES, ENGINE_TIERS
    return {
        "defaults": DEFAULT_PEDAGOGICAL_TOGGLES,
        "difficulty_tiers": {k: {"label": v["label"], "target": v["target"]} for k, v in ENGINE_TIERS.items()},
    }


@teleprompter_router.get("/pedagogical/real-world-parallels", summary="Get all real-world parallel cards")
async def get_all_parallels():
    """Returns real-world case briefs for all 10 rounds."""
    from real_world_parallels import get_all_parallels
    return {"parallels": get_all_parallels()}


@teleprompter_router.get("/pedagogical/real-world-parallels/{round_number}", summary="Get parallel card for a round")
async def get_parallel_for_round(round_number: int):
    from real_world_parallels import get_parallel
    parallel = get_parallel(round_number)
    if not parallel:
        return {"round": round_number, "parallel": None}
    return {"round": round_number, "parallel": parallel}


@teleprompter_router.get("/pedagogical/board-room-prompts", summary="Get Board Room Moment prompts (Moon 2004)")
async def get_board_room_prompts():
    from pedagogical_engine import BOARD_ROOM_PROMPTS
    return {"prompts": BOARD_ROOM_PROMPTS}


@teleprompter_router.get("/pedagogical/mental-model-factors", summary="Get mental model tracking factors")
async def get_mental_model_factors():
    from pedagogical_engine import MENTAL_MODEL_FACTORS, MENTAL_MODEL_ROUNDS
    return {"factors": MENTAL_MODEL_FACTORS, "collection_rounds": MENTAL_MODEL_ROUNDS}


@teleprompter_router.get("/pedagogical/strategy-memo-template", summary="Get strategy memo template")
async def get_strategy_memo_template():
    from pedagogical_engine import STRATEGY_MEMO_TEMPLATE
    return {"template": STRATEGY_MEMO_TEMPLATE}


@teleprompter_router.get("/pedagogical/debrief-protocol", summary="Get Thiagarajan 3-phase debrief protocol")
async def get_debrief_protocol(_g: None = Depends(require_facilitator)):
    from pedagogical_engine import DEBRIEF_PROTOCOL
    return {"protocol": DEBRIEF_PROTOCOL}


@teleprompter_router.get("/pedagogical/engine-disclosure/{round_number}", summary="Get visible engines for a round")
async def get_engine_disclosure(round_number: int, tier: str = "advanced"):
    from pedagogical_engine import get_visible_engines, ENGINE_TIERS
    visible = get_visible_engines(round_number, tier)
    return {
        "round": round_number,
        "tier": tier,
        "visible_engines": list(visible) if visible else "all",
        "is_full_disclosure": visible is None,
        "tier_info": ENGINE_TIERS.get(tier, {}),
    }


# ═══════════════════════════════════════════════════════════════
#  JOURNEY IMPROVEMENT API ENDPOINTS (Phase 6)
# ═══════════════════════════════════════════════════════════════

@teleprompter_router.get("/journey/r1-split/{phase}", summary="Get R1a or R1b split config")
async def get_r1_split(phase: str, tier: str = "advanced"):
    from journey_improvements import get_r1_split_config, should_split_r1
    if not should_split_r1(tier):
        return {"split_active": False, "message": "Expert tier uses standard R1"}
    cfg = get_r1_split_config(phase)
    if not cfg:
        return {"split_active": False, "error": f"Unknown phase: {phase}"}
    return {"split_active": True, "phase": phase, "config": cfg}


# F-10 (audit 2026-09-04): the R6 revelation is fetched by the PLAYER cockpit
# (R6RevelationPanel), so it cannot be gated — but its per-option `impacts`,
# `flags_set` and stochastic `backfire_impacts` are the payoff table. Players
# get the narrative, the options and the disclosed backfire probability (the
# panel shows it by design); the payoffs go only to a facilitator.
_R6_PLAYER_HIDDEN_KEYS = ("impacts", "flags_set")
_R6_PLAYER_HIDDEN_STOCHASTIC_KEYS = ("backfire_impacts",)


def _r6_player_projection(revelation: dict) -> dict:
    out = dict(revelation)
    decisions = {}
    for key, dec in (revelation.get("micro_decisions") or {}).items():
        d = {k: v for k, v in dec.items() if k not in _R6_PLAYER_HIDDEN_KEYS}
        if isinstance(d.get("stochastic"), dict):
            d["stochastic"] = {k: v for k, v in d["stochastic"].items()
                               if k not in _R6_PLAYER_HIDDEN_STOCHASTIC_KEYS}
        decisions[key] = d
    out["micro_decisions"] = decisions
    out["player_projection"] = True
    return out


@teleprompter_router.get("/journey/r6-revelation", summary="Get R6 revelation mechanic config")
async def get_r6_revelation(request: Request):
    from journey_improvements import get_r6_revelation
    revelation = get_r6_revelation()
    if _get_fac_role(request) == "anonymous":
        return {"revelation": _r6_player_projection(revelation)}
    return {"revelation": revelation}


@teleprompter_router.get("/journey/mechanic-variant/{round_number}", summary="Get mechanic variant for R7 or R8")
async def get_mechanic_variant(round_number: int):
    if round_number == 7:
        from journey_improvements import get_r7_variant
        return {"round": 7, "variant": get_r7_variant()}
    elif round_number == 8:
        from journey_improvements import get_r8_variant
        return {"round": 8, "variant": get_r8_variant()}
    return {"round": round_number, "variant": None, "message": "No mechanic variant for this round"}


@teleprompter_router.get("/journey/flag-warnings/{round_number}", summary="Get flag dependency warnings")
async def get_flag_warnings(round_number: int):
    from journey_improvements import get_flag_dependency_warnings, get_impact_magnitude, IMPACT_MAGNITUDE_LABELS
    # Return the warning schema — actual flag evaluation is done client-side
    from journey_improvements import FLAG_DEPENDENCY_WARNINGS
    round_deps = FLAG_DEPENDENCY_WARNINGS.get(round_number, {})
    return {
        "round": round_number,
        "dependency_flags": list(round_deps.keys()),
        "warnings": {k: v for k, v in round_deps.items()},
        "magnitude_labels": IMPACT_MAGNITUDE_LABELS,
    }

# ── Healthcare Teleprompter Overlays ─────────────────────────────
# Merged with base NC scripts at runtime — only paradigm-specific differences.
_HC_TELEPROMPTER_OVERLAYS = {
    1: {
        "title": "Round 1: Medical Waste Compliance Review",
        "crisis_theme": "🏥 Regulators flagged gaps in medical waste disposal. Expand beds, audit, or outsource?",
        "hc_specific": [
            "Option A (Fast-Track Beds) is the HC equivalent of 'Surface Scan' — creates compliance_gap flag",
            "Option B (Strict Audit) costs $5M (vs NC's $3M) — healthcare audits are more expensive due to clinical governance",
            "Option C (Outsource) introduces supply chain opacity — mirrors NC's outsourcing risk",
            "⚠️ HC R1-A creates waste_compliance_gap — check if this triggers R4 severity multiplier",
        ],
        "discussion_prompts": [
            "In healthcare, what is the cost of a compliance gap vs. a bed shortage?",
            "How do you balance patient access (more beds) vs. safety (waste protocols)?",
        ],
    },
    4: {
        "title": "Round 4: Digital Health Malpractice — AI Triage Failure",
        "crisis_theme": "⚠️ Telehealth AI deprioritized high-risk groups, causing severe clinical outcomes",
        "hc_specific": [
            "HC R4 uses clinical malpractice (not supply chain scandal) — emotionally higher stakes",
            "Option C (Human-in-the-Loop) adds burnout_spike — unique to HC, no NC equivalent",
            "Burnout spike from Option C compounds with utilization overload in later rounds",
            "★ DEBRIEF: compare R1 audit choice impact on R4 severity (same cascade as NC)",
        ],
    },
    5: {
        "title": "Round 5: Extreme Weather — Hospital Infrastructure",
        "crisis_theme": "🌪️ Category 4 cyclone approaching hospital network. Base damage: $18M (50% higher than corporate)",
        "hc_specific": [
            "⚠️ FLAG INVERSION: In HC, insurance_only is Option A (not Option C like NC)",
            "When debriefing mixed cohorts, emphasize the MECHANIC not the option letter",
            "HC base damage is $18M (vs NC $12M) — hospitals can't shut down during disasters",
            "Option C (Hardened Grid) gives 0.85 resilience — same as NC Option A",
        ],
    },
    7: {
        "title": "Round 7: The Sterile Waste Mountain — Circular Instrument Hubs",
        "crisis_theme": "♻️ Punitive tax on medical incinerators. Your hospitals are the largest polluters in 3 states.",
        "hc_specific": [
            "HC synergy boost is +0.15 (vs NC +0.30) — compensated by higher exit multiple (14× vs 12×)",
            "Option A (Lobby Against Tax) is the moral hazard equivalent of NC's monetise trap",
            "R3 'early_decarboniser' from Local Sterile Manufacturing now enables synergy bonus here",
        ],
    },
    9: {
        "title": "Round 9: The Nursing Strike — Workforce Automation",
        "crisis_theme": "✊ Nursing union threatens total strike over robotic pharmacy deployments",
        "hc_specific": [
            "HC R9 now has M_R-eligible flags: Option B = managed_transition (+0.12), Option C = community_fund (+0.18)",
            "Option A (Bust the Strike) triggers burnout_spike — no strike mechanic roll needed (guaranteed damage)",
            "Option C (Clinician Retraining) earns community_fund flag — identical M_R pathway as NC",
            "Burnout passive decay (−5/round in HC) means HC teams recover faster than NC teams",
        ],
    },
    10: {
        "title": "Round 10: Legacy & Terminal Valuation — Universal Care Mandate",
        "crisis_theme": "🏁 Board demands final market posture before going public with acquisition",
        "hc_specific": [
            "HC uses 14× exit multiple (vs NC 12×) and $180/ton carbon tax (vs NC $250)",
            "HC max M_R matches NC — community_fund and managed_transition flags fixed (ceilings pinned at 1.93 legacy / 2.02 pillar by test_mr_ceilings_unchanged)",
            "HC archetypes: Community Health Champion / Resilient Care System / Profit-First / Fragile Ward",
            "Option C (Universal Care Mandate) protects synergy — the healthcare equivalent of NC's Resist & Integrate",
        ],
    },
}


# Strategic Pillars (multi_toggles) Teleprompter Overlays
# Merged with base NC scripts at runtime - only paradigm-specific differences.
_SP_TELEPROMPTER_OVERLAYS = {
    1: {
        "title": "Round 1: ESG Baseline Assessment - Multi-Pillar Mode",
        "crisis_theme": "In Strategic Pillars mode, teams select actions across 4 ESG pillars each round, not a single A/B/C choice.",
        "sp_specific": [
            "KEY DIFFERENCE: Teams choose ONE action per pillar (Energy, Operations, Supply Chain, Offsetting) - no A/B/C menu",
            "The HR pillar is available EVERY round. Consistent HR investment builds workforce readiness (+8/round at high) and reduces burnout",
            "Burnout drift (+3/round without HR investment) is invisible initially but compounds into OPEX penalties above burnout index 20",
            "Pillar budget constraint: total pillar spend is deducted from CSF - teams cannot overspend across pillars",
            "Mutual exclusivity is NOT enforced until R7 - early rounds allow combinatorial freedom",
        ],
        "discussion_prompts": [
            "You now have 4 levers instead of 1 binary choice. Does more choice make better strategy, or more rope to hang yourself?",
            "Which pillar did you spend the most on, and does that reveal your team's strategic bias?",
        ],
    },
    2: {
        "title": "Round 2: Double Materiality - Pillar Allocation Under CSRD",
        "crisis_theme": "Materiality in pillar mode: each ESG pillar has different financial-vs-impact materiality profiles",
        "sp_specific": [
            "Pillar teams face the SAME Double Materiality Matrix but must allocate across 4 areas, not just commit to one path",
            "Ask teams: Which pillar aligns most with FINANCIAL materiality? Which aligns with IMPACT materiality?",
            "R2 materiality alignment directly modulates R3 Green Bond pricing - misalignment increases coupon rate",
            "Blockchain traceability (supply chain pillar) can shield against R8 scandal - mention this as a forward-looking incentive",
        ],
        "discussion_prompts": [
            "In pillar mode, is it better to spread materiality alignment evenly or concentrate on your weakest pillar?",
            "How does the CSF budget constraint force prioritisation between financial and impact materiality?",
        ],
    },
    4: {
        "title": "Round 4: Geopolitical Crisis - Multi-Pillar Response",
        "crisis_theme": "Crisis severity hits ALL pillars simultaneously. Your pillar allocation from R1-R3 determines your resilience.",
        "sp_specific": [
            "In pillar mode, crisis severity is modulated by AVERAGE pillar investment, not a single flag",
            "Teams that invested heavily in the Supply Chain pillar (R2-R3) will see lower COGS impact",
            "The HR pillar crisis response (Overtime and Crisis Push) adds +12 burnout - flag this for teams who chose it",
            "Compare crisis outcomes between teams with balanced vs. concentrated pillar strategies",
            "Crisis multiplier is VISIBLE in pillar mode - show teams the KPI dashboard crisis severity gauge",
        ],
    },
    7: {
        "title": "Round 7: Synergy Crossroads - Pillar Mutual Exclusivity",
        "crisis_theme": "Mutual exclusivity is NOW ENFORCED. Teams cannot combine synergy_unlock AND circular_redesign.",
        "sp_specific": [
            "CRITICAL MECHANIC: This is the first round where mutual exclusivity bites",
            "If teams select BOTH synergy_unlock and circular_redesign, synergy_unlock takes priority and circular_redesign impacts are reversed",
            "synergy_unlock boosts M_R by +0.30 - circular_redesign boosts OPEX efficiency but NOT M_R",
            "Ask teams to declare their choice BEFORE seeing the impact - this tests conviction vs. optimisation",
            "For pillar teams that invested consistently in HR: workforce readiness should be near 75+ by now, which enables the +0.10 workforce M_R bonus at R10",
        ],
        "discussion_prompts": [
            "You were forced to choose between synergy and circularity. In real corporate strategy, how do boards navigate similar trade-offs?",
            "Did your HR pillar investment make R7 easier or harder? Why?",
        ],
    },
    9: {
        "title": "Round 9: Just Transition - Pillar Consequences Compound",
        "crisis_theme": "Your 8 rounds of pillar decisions now determine strike probability and regulatory friction.",
        "sp_specific": [
            "In pillar mode, strike probability is a FUNCTION of cumulative HR investment - not just the R9 A/B/C choice",
            "Teams with high workforce readiness (>75) get the M_R workforce bonus (+0.10) AND lower strike probability",
            "Mutual exclusivity enforced again: community_fund and managed_transition are exclusive pathways",
            "community_fund (+0.18 M_R) > managed_transition (+0.12 M_R) - budget arbitrage has been eliminated",
            "Burnout accumulated from R4 crisis and underinvestment in HR now directly feeds strike rolls",
        ],
    },
    10: {
        "title": "Round 10: Terminal Valuation - Pillar Strategy Payoff",
        "crisis_theme": "Your cumulative pillar strategy determines M_R. Consistent pillar investors earn up to 2.02x (the pinned pillar ceiling) vs 0.65x for neglecters.",
        "sp_specific": [
            "Pillar teams have MORE M_R bonus pathways than A/B/C teams: workforce readiness (+0.10) and wellbeing (+0.05) are pillar-exclusive bonuses",
            "Max M_R pathway: synergy(+0.3) + resilience(+0.2) + truth(+0.15) + community_fund(+0.18) + workforce(+0.10) + wellbeing(+0.05) = 1.98",
            "Compare pillar vs. A/B/C team terminal values - pillar teams should show WIDER spreads due to more decision surface area",
            "Highlight: workforce readiness was invisible in early rounds but is now worth $70M+ in terminal value delta",
            "The pillar mode demonstrates that consistent multi-dimensional ESG investment beats single-dimensional optimization",
        ],
        "discussion_prompts": [
            "How did having 4 pillars instead of 1 choice change your strategic consistency?",
            "Which pillar delivered the most ROI? Which was the biggest regret?",
            "In real corporations, which ESG pillar gets systematically underinvested?",
        ],
    },
}

# ── Advanced Climate Teleprompter Overlays ───────────────────────
_AC_TELEPROMPTER_OVERLAYS = {
    1: {
        "title": "Round 1: ESG Audit — Climate Foundations",
        "crisis_theme": "📋 In Advanced Climate mode, every carbon intensity point matters from Round 1",
        "ac_specific": [
            "★ FACILITATOR NOTE: Carbon intensity feeds the TIPPING POINT check from R4+",
            "The tipping threshold is graduated: Warning (CI>45) → Stressed (CI>55) → Tipped (CI>65)",
            "Option A (+2 CI) seems free but compounds via escalating carbon fee ($40/ton rising 15%/round)",
            "Option B (-5 CI) creates early headroom — the cumulative carbon fee difference can exceed $2M over 10 rounds",
            "Frame this as: 'Your first decision sets the carbon trajectory for the entire simulation'",
        ],
    },
    2: {
        "title": "Round 2: Double Materiality — CSRD/TNFD Climate Alignment",
        "crisis_theme": "📊 Under CSRD/ESRS, double materiality explicitly includes climate-related financial materiality",
        "ac_specific": [
            "★ AC BONUS: Option A (Full Materiality Alignment) unlocks +25% NCD forgiveness multiplier",
            "This models CSRD/ESRS climate materiality alignment — real-world companies face similar incentives",
            "TNFD (Taskforce on Nature-related Financial Disclosures) parallel: nature-positive investment is rewarded",
            "Option C (Ignore Materiality) adds +3 CI and +10 governance risk — a double climate penalty",
            "★ EU TAXONOMY: BUs with CI < 25 count as taxonomy-aligned. >60% aligned = green finance discount (-0.5% CoC)",
            "Frame this as: 'Does your materiality assessment include climate-related financial risks?'",
        ],
    },
    3: {
        "title": "Round 3: Scope 3 — Carbon Intensity & Tipping Point Prelude",
        "crisis_theme": "🏭 Supply chain decarbonisation — Scope 3 is 65% of total emissions (GHG Protocol)",
        "ac_specific": [
            "★ SCOPE 1/2/3: Now DYNAMIC per BU — Pharma 35/25/40, Electronics 10/15/75, Software 5/60/35",
            "Each BU has industry-specific emission profiles per GHG Protocol sector guidance",
            "Option A (Rapid Switch) −15 CI is critical to staying below tipping thresholds",
            "★ CBAM: In Advanced Climate mode, avg CI > 40 triggers EU CBAM border adjustment surcharge",
            "★ SBTi: Teams are tracked against a 1.5°C Science-Based Target (CI must drop 4.2%/year)",
            "Option C (Offset & Defer) triggers CARBON FUTURES MARKET — spot prices ±30%, or lock in forward at +20% premium",
            "Green CapEx triggers logarithmic NCD Forgiveness (diminishing returns — 2×ln(1+CapEx_M$))",
            "The 'early_decarboniser' flag from Option A unlocks +0.10 synergy in R7 — hidden long-term reward",
        ],
    },
    4: {
        "title": "Round 4: Contagion — EU CSDDD Climate Liability",
        "crisis_theme": "🔥 ESG scandals increasingly trigger EU CSDDD (Corporate Sustainability Due Diligence Directive) liability",
        "ac_specific": [
            "★ AC-SPECIFIC: Option A (Remediation) reduces future regulatory risk in climate mode",
            "Under CSDDD, companies face civil liability for failing to prevent adverse impacts",
            "The remediation_active flag provides a governance risk buffer for later climate shocks",
            "Option C (Deny & Deflect) adds +4 CI — pushing closer to tipping thresholds",
            "★ FACILITATOR NOTE: The graduated tipping point can activate from Round 4 onwards",
            "If avg CI > 45 at this point, the WARNING tier activates (NCD costs +25%)",
        ],
    },

    5: {
        "title": "Round 5: Climate Tipping Point — The Critical Threshold",
        "crisis_theme": "🌡️ Graduated tipping point check: Warning (CI>45) → Stressed (CI>55) → Tipped (CI>65)",
        "ac_specific": [
            "★ TIPPING POINT: Graduated 3-tier system — thresholds lowered to 45/55/65",
            "Tier 1 (Warning): NCD costs ×1.25, cyclone probability +5%",
            "Tier 2 (Stressed): NCD costs ×1.75, cyclone probability +10%, $500K/round L&D levy",
            "Tier 3 (Tipped): NCD costs ×2.50, cyclone probability +15%, $2M/round L&D levy, IRREVERSIBLE",
            "★ CLIMATE VaR: Physical + Transition risk composite metric visible in events",
            "★ SBTi TRACKER: Teams see whether they're on/off track for 1.5°C Science-Based Target",
            "★ ADAPTATION vs MITIGATION: Each option is now labelled",
            "  Option A: ADAPTATION (physical infrastructure) — but +3 CI risks tipping!",
            "  Option B: ADAPTATION + MITIGATION (nature-positive) — reduces CI AND builds resilience",
            "  Option C: RISK TRANSFER — blocks M_R resilience bonus permanently",
            "Internal Carbon Pricing now ESCALATES: $40×1.15^(round-1) per tCO2e → Green Fund",
            "Stranded Asset Penalty: any BU with CI > 120 triggers +1.5% CoC + divestment pressure",
            "★ Loss & Damage: Post-tipping teams face mandatory UNFCCC fund contributions",
        ],
    },
    7: {
        "title": "Round 7: Circularity — CBAM Border Adjustment",
        "crisis_theme": "♻️ Circular economy + CBAM interaction in supply chain rounds",
        "ac_specific": [
            "★ CBAM: If avg CI > 40, EU CBAM surcharge applies ($100K per CI point above 40)",
            "This models the real EU Carbon Border Adjustment Mechanism (phased in 2023-2026)",
            "Option A (Full Circular Redesign): Ellen MacArthur Foundation estimates 15-30% of revenue",
            "The $10M cost is within the realistic range for a $54M-revenue group",
            "Option C (Waste-to-Energy): +0.30 synergy is the largest single M_R bonus available",
            "NCD forgiveness now follows logarithmic curve: first $1M forgives 1.39 NCD, next $1M only 0.71 more",
        ],
    },
    8: {
        "title": "Round 8: Water Scarcity — Climate-Water Nexus",
        "crisis_theme": "🌊 Water scarcity is increasingly linked to climate change (IPCC AR6 WG2 Chapter 4)",
        "ac_specific": [
            "★ NEW: Option C (Desalination) now has +5 CI penalty (energy-intensive: 3-4 kWh/m³)",
            "This creates a genuine climate trade-off: water security vs carbon intensity",
            "★ EU TAXONOMY: Desalination's +5 CI may push BUs above taxonomy threshold (CI 25)",
            "Stranded asset penalties compound with water crisis costs (double jeopardy)",
            "If any BU has CI > 120 AND faces water scarcity: compounding CoC + OPEX penalties",
            "★ ADAPTATION FRAMING: Options are labelled as Adaptation/Maladaptation",
            "Option B (Prioritise Electronics) is labelled MALADAPTATION — inequitable resource allocation",
        ],
    },
    9: {
        "title": "Round 9: Just Transition — ILO Guidelines & Climate Justice",
        "crisis_theme": "✊ Just Transition is a process, not a one-time investment (ILO 2015)",
        "ac_specific": [
            "★ M_R SCALING: Community/Transition bonus now scales with sustained HR investment",
            "Each round of workforce_readiness > 60 adds +10% to the JT M_R bonus (capped at +50%)",
            "This rewards social dialogue as a process — teams that invested in HR across rounds benefit more",
            "Option A (+3 CI) could push borderline teams past tipping point late in the game",
            "★ CLIMATE FRAMING: Options labelled as JUST TRANSITION (community-led) vs MALADAPTATION",
            "Community Fund ($20M): +0.18 M_R × JT scaling | Managed Transition ($12M): +0.12 M_R × JT scaling",
        ],
    },
    10: {
        "title": "Round 10: Terminal Valuation — Climate-Adjusted",
        "crisis_theme": "🏛️ Terminal value now includes Green Fund balance as accumulated climate capital",
        "ac_specific": [
            "★ GREEN FUND TERMINAL BONUS: Fund balance is added to Terminal EBITDA before exit multiple",
            "Formula: TV = (Terminal_EBITDA + Green_Fund_Balance) × Exit_Multiple × M_R",
            "Post-tipping teams face permanently elevated CoC, NCD hostility (2.5×), and L&D levies",
            "Carbon tax at terminal ($250/ton) is especially punishing for high-CI teams",
            "★ COMPARE: Teams that avoided tipping vs those that didn't — spread should be dramatic",
            "★ EU TAXONOMY: Final taxonomy alignment % affects CoC (>60% = -0.5% green discount)",
            "★ SBTi: Final SBTi pathway status shown — on track teams get credibility premium",
            "Escalated carbon fee at R10: ~$162/tCO2e (vs base $40) for internal pricing",
            "★ DEBRIEF QUESTIONS:",
            "  1. 'Which rounds did you feel climate pressure most?'",
            "  2. 'How did the escalating carbon fee change your investment calculus?'",
            "  3. 'Did the tipping point warning at CI>50 change your strategy?'",
            "  4. 'If you could replay one round with climate knowledge, which would it be?'",
        ],
    },
}

@teleprompter_router.get("/teleprompter/{round_number}/{paradigm}", summary="Get paradigm-specific teleprompter script")
async def get_paradigm_teleprompter(round_number: int, paradigm: str = "legacy_abc", _g: None = Depends(require_facilitator)):
    """Get teleprompter script merged with paradigm-specific overlay."""
    base = _TELEPROMPTER_SCRIPTS.get(round_number, {
        "title": f"Round {round_number}",
        "talking_points": [],
        "engines_likely": [],
        "discussion_prompts": [],
    })
    result = {"round": round_number, "paradigm": paradigm, "script": dict(base)}

    if paradigm == "healthcare":
        overlay = _HC_TELEPROMPTER_OVERLAYS.get(round_number, {})
        result["script"]["paradigm_overlay"] = overlay
    elif paradigm == "advanced_climate":
        overlay = _AC_TELEPROMPTER_OVERLAYS.get(round_number, {})
        result["script"]["paradigm_overlay"] = overlay
    elif paradigm == "multi_toggles":
        overlay = _SP_TELEPROMPTER_OVERLAYS.get(round_number, {})
        result["script"]["paradigm_overlay"] = overlay

    return result


# ═════════════════════════════════════════════════════════════════
#  GAME FEEL — FACILITATOR GUIDANCE
#  Cross-cutting pedagogical notes for interpreting new engine outputs.
#  Injected into teleprompter responses when relevant.
# ═════════════════════════════════════════════════════════════════

GAME_FEEL_GUIDANCE = {
    "time_to_impact": {
        "title": "📊 Time-to-Impact Indicators — Facilitator Guide",
        "theory": (
            "Prospect theory (Kahneman & Tversky, 1979) shows that people respond "
            "more strongly to LOSS FRAMING than gain framing. 'You'll lose your "
            "A+ rating in 2 rounds' is more motivating than 'Your NCD is currently "
            "380K.' Use Time-to-Impact countdowns to convert static metrics into "
            "loss countdowns — the single most powerful engagement lever in simulation."
        ),
        "how_to_use": [
            "When revealing round results, READ the time-to-impact warnings FIRST, "
            "before showing absolute numbers. This primes teams to feel urgency.",
            "Frame each warning as a CHOICE, not a fate: 'At current trajectory, "
            "NCD triggers a credit downgrade in 2 rounds — unless you act now.'",
            "For strong teams: use the ABSENCE of warnings as positive reinforcement. "
            "'Notice that you have zero time-to-impact warnings. That's strategic cushion.'",
            "For struggling teams: pick ONE warning and make it the round's priority. "
            "Don't overwhelm — focus creates agency.",
        ],
        "indicators": {
            "ncd_downgrade": "NCD exceeding 500K/BU triggers a credit downgrade — higher cost of capital for all future rounds.",
            "braindrain": "Reputation below 25 activates brain drain — OPEX increases 12-85% on affected BUs.",
            "strike_risk": "Strike probability above 20% means random BU shutdown risk next round.",
            "death_spiral": "Treasury hitting $0 with reputation below 30 triggers Survival Mode — the 3-act turnaround arc begins.",
        },
    },
    "severity_tiers": {
        "title": "🎨 Severity Tier System — Visual Interpretation Guide",
        "theory": (
            "Weber's Law in psychophysics: humans perceive changes proportionally, "
            "not absolutely. A $500K penalty matters enormously at $5M treasury but "
            "is noise at $100M. The severity tier system normalizes consequence "
            "significance to the team's current position. Without this, players "
            "habituate to penalty messages and stop reading them — the 'alarm fatigue' "
            "problem (Cvach, 2012)."
        ),
        "tiers": {
            "🟢 Routine": "Impact <1% of treasury. Collapsed by default. Don't discuss unless asked.",
            "🟡 Noteworthy": "Impact 1-5% of treasury. Worth mentioning in passing. One-round concern.",
            "🟠 Material": "Impact 5-15% of treasury. Strategic-level conversation needed. Multi-round effect.",
            "🔴 Critical": "Impact >15% of treasury. Full debrief required. Existential if unaddressed for 2+ rounds.",
        },
        "facilitator_action": (
            "After each round, scan the consequence waterfall for 🟠 Material and "
            "🔴 Critical entries. These are your teaching moments. Everything else "
            "can be summarized as 'normal market friction.' This prevents cognitive "
            "overload — teams focus on what matters."
        ),
    },
    "consequence_waterfall": {
        "title": "📊 Consequence Waterfall — How to Debrief",
        "how_to_use": [
            "The waterfall shows how treasury moved inside the engine tick — gross profit, "
            "inflation, the NCD penalty, the flow surcharges. It is frozen before the round "
            "handlers and the stakeholder engines (option costs, NPC fines, balance-sheet items) "
            "post, so read it beside the round's events, not as the whole story (FIN-06).",
            "Read it top-to-bottom with the team: 'You started at $50M. Gross profit added $13M. "
            "Then inflation took $860K. Then NCD interest took $180K — and notice, that was "
            "only $90K last round. It's compounding.'",
            "The 'because' field on each entry explains WHY. Read this out loud.",
            "The 'counterfactual' field shows what COULD have been different. "
            "Use this for the strongest teaching moments.",
        ],
    },
    "board_room_moments": {
        "title": "🪞 Board Room Reflection Moments — Facilitator Protocol",
        "theory": (
            "Moon (2004) identifies the critical gap in simulation learning: participants "
            "DO things but don't PROCESS them. Board Room Moments are forced metacognitive "
            "interventions. They don't teach content — they teach the HABIT of reflection."
        ),
        "protocol": [
            "When a Board Room Moment triggers, PAUSE the simulation for the team.",
            "Read the prompt aloud. Give teams 3-5 minutes to discuss.",
            "They must write ONE sentence (the answer). Collect these for the final debrief.",
            "Do NOT judge the answers. The act of reflection is the goal, not the content.",
            "After Round 10, read back their reflections chronologically. "
            "Teams will see their strategic thinking evolve.",
        ],
    },
    "turnaround_narrative": {
        "title": "🔧 Turnaround Arc — Facilitator Narrative Guide",
        "phases": {
            "crisis": (
                "TONE: Grave but not hopeless. 'The board has brought in outside help. "
                "This is serious — but every turnaround story starts with a crisis. "
                "Your job is to stop the bleeding.' "
                "REMIND: CapEx is frozen. They can only choose Option T or wait."
            ),
            "stabilisation": (
                "TONE: Cautiously optimistic. 'The creditors are watching. You've "
                "bought yourself time — now use it wisely. 50% CapEx cap means every "
                "dollar must count.' "
                "REMIND: No dividends. M_R capped at 0.80."
            ),
            "recovery": (
                "TONE: Encouraging. 'The market is starting to notice your comeback. "
                "Credit rating upgraded. Full CapEx restored. One more phase to go.' "
                "REMIND: M_R cap is 1.20 — better than Fragile Giant territory."
            ),
            "exit": (
                "TONE: Celebratory. 'Against all odds, you rebuilt this company. "
                "That +0.10 Turnaround Premium? That's the market saying: we believe "
                "in you MORE because you survived the impossible.' "
                "HIGHLIGHT: This is the most impressive outcome in the simulation."
            ),
        },
    },
    "momentum_score": {
        "title": "📈 Momentum Score — Interpreting Rate of Change",
        "theory": (
            "Attribution theory (Weiner, 1985): learners who attribute outcomes to "
            "EFFORT (unstable, controllable) are more motivated than those who attribute "
            "outcomes to ABILITY (stable, uncontrollable). The Momentum Score explicitly "
            "measures effort — 'are you improving?' not 'are you good?'"
        ),
        "interpretation": {
            "accelerating (70+)": "Team is improving rapidly. Highlight this publicly to reinforce effort.",
            "stable (50-70)": "Steady state. Neither gaining nor losing ground. Challenge them: 'Is stability enough?'",
            "decelerating (30-50)": "Warning zone. Previous gains are eroding. Ask: 'What changed?'",
            "declining (<30)": "Active deterioration. Multiple systems failing. Focus on triage, not ambition.",
        },
        "comeback_kid": (
            "If a team maintains Momentum >70 for 2 consecutive rounds, they earn the "
            "'Comeback Kid' bonus (+0.05 M_R). Announce this publicly — it rewards persistence "
            "and makes struggling teams aspirational rather than pitiful."
        ),
    },
}
