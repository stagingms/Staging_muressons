"""Part 2: §4 — Round-by-Round Guide with full briefing text."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from docx_styles import *

ROUNDS = {
    1: {
        "title": "ESG Baseline Assessment",
        "theme": "Stakeholder Mapping & Diagnostic Decision",
        "icon": "📋",
        "briefing": (
            "The board has mandated an initial ESG assessment across all business units. "
            "You must decide the depth and scope of the audit. Your decision here will echo "
            "throughout the simulation — hidden consequences will surface in later rounds."
        ),
        "pre_gate": "Mendelow's Stakeholder Matrix (drag-and-drop): Players must classify 8 stakeholders into Power × Interest quadrants before proceeding.",
        "options": [
            ["A", "Surface-Level Scan", "$0", "electronics_blindspot", "Fast compliance check. Electronics BU blind spots missed. +$500K revenue, -2 rep, +5 governance risk."],
            ["B", "Deep Forensic Audit", "-$3M", "deep_audit_completed", "Full forensic audit across all units. -$200K revenue, +5 rep, -5 governance risk, -5 CI."],
            ["C", "Phased Audit Rollout", "-$1.5M", "deferred_audit", "Audit Pharma and CG now; defer Electronics and Software. +2 rep, -2 CI. Partial blind spots remain."],
        ],
        "hidden": "electronics_blindspot flag DOUBLES R4 crisis severity from 40→80 via contagion sigmoid. This is the simulation's most consequential hidden mechanic.",
        "theory": "Mendelow (1991) Stakeholder Mapping; Real Options Theory — the audit is an option on future crisis mitigation (5× NPV); Signalling Theory — market interprets audit depth as governance quality signal.",
        "debrief": [
            "What information did you have when making this decision? What was unknown?",
            "How did you weigh cost vs. risk? What mental model drove your choice?",
            "If you chose the Surface Scan, what would you have paid to know the consequences?",
            "How does this mirror real-world ESG audit decisions?",
        ],
        "pitfall": "Students choose Surface Scan to 'save money'. They discover at R4 that the $3M audit would have prevented $15M+ in cascade damage.",
        "screenshot": "Stakeholder Map modal with stakeholder cards and quadrant grid",
    },
    2: {
        "title": "Double Materiality",
        "theme": "The CSRD Acid Test",
        "icon": "📊",
        "briefing": (
            "The CFO requires all investment proposals to demonstrate alignment with the "
            "High Financial Impact / High ESG Impact quadrant per the Double Materiality "
            "framework. Non-aligned spending triggers a 40% budget clawback."
        ),
        "pre_gate": "CSRD Materiality Matrix (2×2 drag-and-drop): Players classify 8 sustainability issues into Financial Impact × ESG Impact quadrants. Accuracy >90% earns a $2M treasury bonus.",
        "options": [
            ["A", "Full Materiality Alignment", "-$2.5M", "materiality_aligned", "Genuine CSRD compliance with assurance-ready report. +5 rep, -5 gov risk, +0.10 M_R at terminal. In Advanced Climate: NCD forgiveness +25%."],
            ["B", "Strategic Exceptions", "$0", "materiality_exceptions", "Limited off-quadrant spending with CFO approval. +2 rep, -2 gov risk. Partial compliance."],
            ["C", "CEO-Only Sign-Off", "$0 (+$400K)", "materiality_ignored", "CEO approves without board oversight. ESRS 1 §1.51 violation. 40% budget clawback, -5 rep, +10 gov risk. Blocks Green Bond eligibility."],
        ],
        "hidden": "Option C triggers a 40% clawback on all materiality capital released this round. Green Bond access blocked for remainder. materiality_aligned flag adds +0.10 M_R at terminal.",
        "theory": "EU CSRD/ESRS Standards; Double Materiality (financial + impact); Legitimacy Theory — ESRS compliance signals institutional legitimacy; Agency Theory — CEO-only sign-off bypasses board oversight (Jensen & Meckling 1976).",
        "debrief": [
            "How did you balance financial materiality vs. ESG impact materiality?",
            "What was the opportunity cost of full alignment?",
            "Did the CFO gate change how you allocated capital?",
            "How does CSRD compliance compare to voluntary ESG reporting?",
        ],
        "pitfall": "Students choose CEO-Only to 'save money' — the 40% clawback actually costs more than Full Alignment.",
        "screenshot": "CSRD Materiality Matrix with Q1–Q4 quadrants",
    },
    3: {
        "title": "Scope 3 Emissions",
        "theme": "Supply Chain Decarbonisation",
        "icon": "🏭",
        "briefing": (
            "Regulators have signalled mandatory Scope 3 disclosures. Your supply chain "
            "carbon footprint is 4× your direct emissions. The Fog of War clears after "
            "this round — all hidden engines become progressively visible."
        ),
        "pre_gate": None,
        "options": [
            ["A", "Rapid Supplier Switch", "-$4M", "early_decarboniser", "Immediately switch to low-carbon suppliers. -15 CI, -$800K revenue, +3 rep. Sets early_decarboniser flag (+0.15 M_R). Supply chain disruption risk."],
            ["B", "Green Bond Investment", "-$2M", "green_bond_active", "Issue green bond to fund supplier transition. -8 CI, -15 NCD, +$300K revenue, +4 rep. NCD reduction over 3 rounds."],
            ["C", "Offset & Defer", "-$1M", "carbon_deferred", "Buy carbon offsets and wait. +5 NCD (compounds at 6%!), -3 rep, -1 CI. Short-term savings, long-term ecological debt."],
        ],
        "hidden": "NCD compounds at 6%/round. The +5 NCD from Option C becomes +7.5 by R10, costing ~$1.9M in terminal value. early_decarboniser flag unlocks +0.15 M_R and amplifies R7 circular economy returns.",
        "theory": "GHG Protocol Scope 3; First-Mover Advantage (Lieberman & Montgomery 1988); Natural Capital accounting (Costanza 1997); Signalling Theory — Green Bond signals commitment to capital markets.",
        "debrief": [
            "How did you evaluate the trade-off between immediate cost and future NCD growth?",
            "What is the NPV of avoiding 6% compound NCD growth for 7 rounds?",
            "How does Scope 3 reporting change your view of 'company boundaries'?",
        ],
        "pitfall": "Students underestimate NCD compounding. +5 NCD in R3 seems small but compounds to $1.9M terminal value loss.",
        "screenshot": None,
    },
    4: {
        "title": "Contagion",
        "theme": "The R1 Reckoning",
        "icon": "🔥",
        "briefing": (
            "A labour-rights exposé in your Electronics supply chain has gone viral. "
            "The contagion engine will propagate reputational damage across all BUs. "
            "Crisis severity depends on your Round 1 audit decision."
        ),
        "pre_gate": None,
        "options": [
            ["A", "Full Transparency & Remediation", "-$6M", "remediation_active", "Public disclosure, factory audits, worker compensation. +10 rep, +8 social licence. Sets remediation_active (+0.10 M_R)."],
            ["B", "Damage Control PR", "-$2M", "pr_containment", "Crisis PR firm. +2 rep, -3 social licence. Narrative contained but root cause unfixed."],
            ["C", "Deny & Deflect", "$0", "deny_and_deflect", "Issue denial. -15 rep, -10 social licence, +8 gov risk, +5 NCD. Cheapest but highest contagion risk."],
        ],
        "hidden": "Severity = 40 (deep audit) / 60 (deferred) / 80 (blindspot). Contagion uses sigmoid: hit = max × 1/(1+e^(-s/scale)). Blindspot teams lose ~19 reputation vs. ~12 for audited teams. Board Room Moment triggers if rep < 40.",
        "theory": "Argyris (1977) Double-Loop Learning — players must question R1 assumptions; Kahneman (2011) System 1/2 — time pressure reveals heuristic biases; Taleb (2012) Antifragility — audited teams are antifragile, gaining from the crisis.",
        "debrief": [
            "★ KEY DEBRIEF: Ask teams to reveal their R1 choice. Compare R4 outcomes.",
            "What was the NPV of the R1 audit decision? (Answer: ~5× the $3M cost)",
            "When did you realize R1 had consequences? What assumption broke?",
            "How does this mirror real-world supply chain scandals?",
            "What would Argyris say about your mental model update?",
        ],
        "pitfall": "Teams that chose Surface Scan face 2× severity. The $0 'savings' at R1 cost $15M+ in R4 damage.",
        "screenshot": "Consequence DNA panel showing R1→R4 causal chain",
    },
    5: {
        "title": "Climate",
        "theme": "Physical Climate Risk & Shadow Board Audit",
        "icon": "🌪️",
        "briefing": (
            "A Category 4 cyclone is projected to hit your primary manufacturing corridor. "
            "Base damage: $12M. A stochastic roll (75% probability) determines actual impact. "
            "Before deciding, you must complete the mandatory Shadow Board Audit."
        ),
        "pre_gate": "Mandatory Shadow Board Audit: 3 independent personas (Shareholder, Community Leader, Environmental Scientist) evaluate your strategy. Rejecting their advice sets hidden flags that cascade to R10 ending pathways. See §5 for deep dive.",
        "options": [
            ["A", "Hard Engineering Defence", "-$8M", "hard_engineering", "Flood walls and reinforced infrastructure. Resilience 0.85 but NO PROTECTION THIS ROUND (2-round build). +10 NCD, +3 CI. Climate tipping point risk."],
            ["B", "Nature-Based Solutions", "-$5M", "nature_based_resilience", "Mangrove restoration and natural buffers. Resilience 0.60, 2-round maturation. -8 NCD, -6 CI, +6 rep. Unlocks Resilience Champion (+0.20 M_R)."],
            ["C", "Insurance Only", "-$2M", "insurance_only", "Comprehensive insurance. ZERO physical resilience. Full damage if cyclone strikes. ⚠️ BLOCKS Resilience Bonus (-0.20 M_R at terminal)."],
        ],
        "hidden": "75% cyclone probability triggers $12M×(1-resilience_factor) damage. Shadow Board rejection sets shareholder_alienated, community_distrust, or scientist_dismissed flags that determine R10 ending pathway. insurance_only permanently blocks +0.20 M_R.",
        "theory": "TCFD Physical Risk Assessment; Moon (2004) Board Room Moments; Mitchell et al. (1997) Stakeholder Salience; Schön (1983) Reflection-in-Action; Agency Theory (Shadow Board = independent oversight).",
        "debrief": [
            "How did the Shadow Board audit influence your decision?",
            "What trade-off exists between hard engineering and nature-based solutions?",
            "What does 'resilience' mean beyond infrastructure?",
            "Did the stochastic element (75% cyclone) change your risk calculus?",
        ],
        "pitfall": "Students choose Insurance Only to save money — permanently losing +0.20 M_R (worth ~$30M in terminal value).",
        "screenshot": "Shadow Board Audit modal with 3 persona cards",
    },
    6: {
        "title": "AI Bias",
        "theme": "Algorithmic Ethics & the Truth Premium",
        "icon": "🤖",
        "briefing": (
            "Your Software BU's AI recruitment tool has been found to systematically "
            "discriminate against minority applicants. The story has reached mainstream "
            "media. A whistleblower may escalate the story further."
        ),
        "pre_gate": None,
        "options": [
            ["A", "Monetise the Algorithm", "+$10M revenue", "ai_monetised", "Pivot AI tool into commercial product. +$10M revenue but -20 rep, -15 social licence, +8 gov risk. Contagion spike. High short-term return, devastating long-term."],
            ["B", "Ethical AI Overhaul", "-$8M", "ethical_ai_overhaul", "Shut down tool, hire ethics board, retrain models. +15 social licence, +5 rep, -5 gov risk. Sets Truth Premium (+0.15 M_R)."],
            ["C", "Quiet Patch", "-$1M", "quiet_patch", "Silently fix algorithm. -5 rep, +10 gov risk. 40% chance of whistleblower leak (Streisand Effect) → Legal Containment micro-decision."],
        ],
        "hidden": "R6 Revelation Mechanic: After decision, a whistleblower twist presents 3 micro-responses (Transparent Disclosure / Legal Containment / Quiet Settlement). Legal Containment has 40% backfire probability. Stakeholder migration: Local Communities move to 'Manage Closely' quadrant.",
        "theory": "Moral Hazard — monetising bias creates perverse incentives; Institutional Theory — AI ethics as institutional norm; Virtue Ethics — character-based evaluation of tech decisions; Prospect Theory — loss aversion in reputation damage.",
        "debrief": [
            "What is the 'Truth Premium' and why does it have terminal value?",
            "How did the 40% backfire probability affect your risk assessment?",
            "What real-world AI bias scandals does this mirror?",
            "Is there a moral difference between fixing quietly and fixing publicly?",
        ],
        "pitfall": "Teams monetise the algorithm for +$10M revenue but lose $40M+ in terminal value from reputation collapse and missing M_R bonuses.",
        "screenshot": None,
    },
    7: {
        "title": "Circularity",
        "theme": "Synergy Unlock & Workforce Readiness Test",
        "icon": "♻️",
        "briefing": (
            "New EU circular economy regulations mandate 60% waste diversion by next year. "
            "Non-compliance fines: $15M. This round uses the Budget Allocation mechanic — "
            "you must distribute $15M across 3 investment pillars."
        ),
        "pre_gate": None,
        "options": [
            ["A", "Full Circular Redesign", "-$10M", "circular_redesign", "Redesign products for full disassembly and reuse. -12 NCD, +8 rep, -8 CI, +$1M revenue. Workforce readiness gate applies."],
            ["B", "Extended Producer Responsibility", "-$5M", "epr_program", "Fund take-back programs and recycling partnerships. -6 NCD, +4 rep, -5 CI."],
            ["C", "Waste-to-Energy Partnership", "-$7M", "waste_to_energy + synergy_unlock", "Build waste-to-energy facility. Synergy multiplier +0.30, -4 NCD, -6 CI. Unlocks +0.30 M_R at terminal."],
        ],
        "hidden": "Workforce Readiness gate: WR<40 → 30% penalty on circular benefits; WR≥60 → 10% amplification. Teams that invested in HR across R1-R6 are rewarded here. Pillar mutual exclusivity applies — can't max all three.",
        "theory": "Resource-Based View (Barney 1991) — VRIO advantage from circular capabilities; Dynamic Capabilities (Teece 2007) — workforce readiness as adaptive capacity; Learning Organisation (Senge 1990) — system loop identification.",
        "debrief": [
            "How did the workforce readiness gate affect your circular economy returns?",
            "What is the relationship between human capital investment and technology adoption?",
            "Which option creates the most durable competitive advantage? (RBV analysis)",
        ],
        "pitfall": "Teams with low workforce readiness (<40) lose 30% of their circular investment returns — HR neglect compounds here.",
        "screenshot": "Advanced Metrics drawer showing Synergy Multiplier",
    },
    8: {
        "title": "Blue Stress",
        "theme": "Water Scarcity & Equitable Resource Allocation",
        "icon": "🌊",
        "briefing": (
            "A multi-year drought has depleted the watershed serving Pharma and Electronics. "
            "Government water rationing is imminent. You must choose how to allocate "
            "diminishing water resources across your business units."
        ),
        "pre_gate": "Stakeholder Tribunal: 3 stakeholder challenges (Community Leader, Regulator, Journalist), 90 seconds each. Players must defend their water allocation strategy under time pressure.",
        "options": [
            ["A", "Water Efficiency for All BUs", "-$12M", "water_efficiency_all", "Equitable water-saving upgrades across all units. -20 water dependency, +5 social licence, +5 rep, -3 CI."],
            ["B", "Prioritise Electronics", "-$4M", "electronics_water_priority", "Divert water to Electronics (highest margin). Pharma and CG take -25 social licence each. -8 rep. Maladaptation framing."],
            ["C", "Desalination Mega-Project", "-$30M", "desalination_built", "Build desalination plant. -30 NCD, -40 water dep, but +5 CI (energy-intensive). $5M/round revenue from R10 for 3 rounds. 2-round construction delay."],
        ],
        "hidden": "Cascade Multiplier: Regulatory Sandbox × Journalist tolerance. If journalist agent is already hostile, Prioritise Electronics triggers viral exposé. Community Leader agent enters 'protest' state at SLO < 30.",
        "theory": "Tragedy of the Commons (Hardin 1968); Environmental Justice (Schlosberg 2007); Natural Capital (Costanza 1997); Ostrom (1990) — commons governance instruments in regulatory sandbox.",
        "debrief": [
            "Is prioritising the highest-margin BU 'rational'? From whose perspective?",
            "How does the Tragedy of the Commons apply to corporate water use?",
            "What would Ostrom's principles suggest for water governance?",
            "How did the Stakeholder Tribunal change your thinking?",
        ],
        "pitfall": "Prioritise Electronics saves $8M short-term but costs $25M+ from social licence collapse, agent cascades, and terminal value penalties.",
        "screenshot": None,
    },
    9: {
        "title": "Just Transition",
        "theme": "The Social Cost of Decarbonisation",
        "icon": "✊",
        "briefing": (
            "Decarbonisation commitments require closing 3 legacy factories. 2,000 jobs "
            "are at risk. Community protests are escalating. If burnout is high and social "
            "licence is low, strike probability reaches 50-75%."
        ),
        "pre_gate": None,
        "options": [
            ["A", "Immediate Closure", "+$5M", "immediate_closure", "Close factories now for cost savings. -20 social licence, -15 rep. If SLO < threshold: 50-75% strike probability that ZEROS revenue for 1 round."],
            ["B", "Managed Transition", "-$12M", "managed_transition", "2-year phase-out with retraining and severance. +10 social licence, +8 rep, -4 CI. Sets managed_transition (+0.12 M_R)."],
            ["C", "Community Investment Fund", "-$20M", "community_fund", "Create $20M fund for community development and green jobs. +18 social licence, +12 rep, -5 gov risk. Sets community_fund (+0.18 M_R)."],
        ],
        "hidden": "Strike probability = base_rate × (burnout/100) × (1 - SLO/100). Teams with burnout >60% and SLO <40 face 66%+ strike chance. Strike zeros ALL revenue for 1 round — catastrophic for terminal value. HR investment across R1-R8 is the primary defence.",
        "theory": "Rawlsian Justice — Difference Principle applied to factory closures; Freeman Stakeholder Theory — who bears transition costs?; Sen Capabilities Approach — green job training expands capabilities; Hirschman Exit/Voice/Loyalty — community response to closure.",
        "debrief": [
            "Who bears the cost of decarbonisation? Is that just?",
            "What would Rawls say about your approach to factory closures?",
            "How did your HR investment history affect your R9 options?",
            "What is the ROI of the Community Fund in M_R terms?",
            "How does this mirror real-world Just Transition debates?",
        ],
        "pitfall": "Teams that neglected HR for 8 rounds face impossible R9: high burnout + low SLO = near-certain strike. The 'cheapest' option (+$5M) can cost $50M+ in zeroed revenue.",
        "screenshot": None,
    },
    10: {
        "title": "Grand Finale",
        "theme": "Year 5 Activist Ultimatum & Terminal Valuation",
        "icon": "🏛️",
        "briefing": (
            "An activist investor consortium has acquired a blocking stake. They demand "
            "strategic restructuring. The board must decide the company's Year 5 trajectory. "
            "Terminal valuation determines your final score."
        ),
        "pre_gate": "Synergy Gate: Option A (Resist & Integrate) is DISABLED if Synergy Score ≤ 80. Teams that under-invested in cross-BU integration lose access to the highest-value option.",
        "options": [
            ["A", "Resist & Integrate", "-$5M", "resist_integrate", "Fight the activist, keep all BUs integrated, leverage synergy. REQUIRES Synergy > 80. +5 rep, +3 social licence, -3 gov risk, -3 CI."],
            ["B", "Spin-Off", "+$10M", "spinoff", "Spin off weakest BU as separate entity. +$10M treasury, +2 rep, -5 social licence, +3 gov risk."],
            ["C", "Divest", "+$25M", "divest", "Full divestiture of non-core assets. Synergy WIPED to 0. -10 rep, -12 social licence, +5 gov risk, +8 NCD. Maximum cash extraction."],
        ],
        "hidden": "M_R is calculated from all accumulated flags across R1-R9. Archetype classification: Regenerative Titan (M_R ≥ 1.8), De-risked Safe Haven (≥ 1.2), Fragile Giant (≥ 0.8), Stranded Relic (< 0.8). Ending pathway modifies archetype names.",
        "theory": "Porter CSV — shared value creation as strategy; Kolb Experiential Learning — full cycle completion; Meadows Leverage Points — debrief reveals system intervention hierarchy; Thiagarajan Debrief Protocol — 3-phase structured reflection.",
        "debrief": [
            "Compare terminal values across teams. What explains the 25× gap between Titans and Relics?",
            "Walk through your M_R breakdown. Which bonuses did you earn? Which did you miss?",
            "If you could replay with perfect information, what single decision would you change?",
            "What transferable principle would you take to a real boardroom?",
            "How does your R1 mental model compare to your R10 understanding?",
        ],
        "pitfall": "Teams choose Divest for +$25M cash but wipe synergy to 0, losing far more in terminal value multiplication.",
        "screenshot": "Final Report showing terminal valuation breakdown and archetype",
    },
}

def build_section4(doc):
    add_page_break(doc)
    doc.add_heading('PART 2 — ROUND-BY-ROUND FACILITATION GUIDE', level=1)
    doc.add_heading('§4. Round-by-Round Guide (R1–R10)', level=1)
    doc.add_paragraph('Each round follows a consistent template. The briefing text shown below is the exact content displayed to players on screen.')

    for rnum, rd in ROUNDS.items():
        if rnum > 1:
            add_page_break(doc)
        doc.add_heading(f'Round {rnum}: {rd["title"]} — {rd["theme"]}', level=2)
        
        # Briefing Document (exact player-facing text)
        doc.add_heading('Player Briefing (On-Screen Text)', level=3)
        p = doc.add_paragraph()
        r = p.add_run(f'{rd["icon"]} ')
        r.font.size = Pt(14)
        r2 = p.add_run(rd["briefing"])
        r2.font.italic = True
        r2.font.size = Pt(10.5)
        
        # Pre-Decision Gate
        if rd.get("pre_gate"):
            doc.add_heading('Pre-Decision Gate', level=3)
            doc.add_paragraph(rd["pre_gate"])
        
        # Screenshot
        if rd.get("screenshot"):
            add_screenshot_placeholder(doc, rd["screenshot"])
        
        # Options Table
        doc.add_heading('Strategic Options', level=3)
        opt_rows = [[o[0], o[1], o[2], o[3], o[4]] for o in rd["options"]]
        add_styled_table(doc, ['Option', 'Title', 'Cost', 'Flag Set', 'Description & Impacts'], opt_rows,
                        col_widths=[0.5, 1.2, 0.7, 1.2, 3.5])
        
        # Hidden Mechanics
        doc.add_heading('Hidden Mechanics (DO NOT REVEAL)', level=3)
        add_callout(doc, rd["hidden"], "warning")
        
        # Theory Connection
        doc.add_heading('Theory Connection', level=3)
        doc.add_paragraph(rd["theory"])
        
        # Debrief Prompts
        doc.add_heading('Debrief Prompts', level=3)
        add_bullet_list(doc, rd["debrief"])
        
        # Common Pitfall
        doc.add_heading('Common Pitfall', level=3)
        add_callout(doc, rd["pitfall"], "important")
