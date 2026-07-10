"""Part 1: Sections 1-3 — Pedagogical Overview, Theory, Math Engine."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from docx_styles import *

def build_title_page(doc):
    for _ in range(6):
        doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("MURESSONS GLOBAL CORPORATION")
    r.font.size = Pt(28); r.font.bold = True; r.font.color.rgb = BRAND_NAVY
    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = p2.add_run("Facilitator's Manual")
    r2.font.size = Pt(20); r2.font.color.rgb = BRAND_BLUE
    p3 = doc.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r3 = p3.add_run("Project Equilibrium — Strategy Simulation")
    r3.font.size = Pt(14); r3.font.color.rgb = BRAND_TEAL
    for _ in range(4):
        doc.add_paragraph()
    info = doc.add_paragraph()
    info.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r4 = info.add_run("CONFIDENTIAL — For Facilitator Use Only\nVersion 1.0 — May 2026\n10-Round Loop | 4 Side Tracks | 5 Ending Pathways | 5 Autonomous Agents")
    r4.font.size = Pt(10); r4.font.color.rgb = BRAND_GRAY
    add_page_break(doc)

def build_toc(doc):
    doc.add_heading('Table of Contents', level=1)
    toc_items = [
        "Part 1 — Foundation & Engine",
        "  §1. Pedagogical Overview & Learning Objectives",
        "  §2. Theoretical Foundations & Academic Integration",
        "  §3. Mathematical Engine Reference",
        "Part 2 — Round-by-Round Facilitation Guide",
        "  §4. Round-by-Round Guide (R1–R10)",
        "Part 3 — Advanced Systems",
        "  §5. Shadow Board Audit Deep Dive",
        "  §6. Ending Pathways",
        "  §7. Terminal Valuation Deep Dive",
        "  §8. Side Tracks",
        "  §9. Autonomous Stakeholder Agents",
        "  §10. Facilitator God Mode & Overrides",
        "Part 4 — Dashboard Guides, Planning & Appendices",
        "  §10A. Facilitator Dashboard Visual Guide",
        "  §10B. God Mode Dashboard Visual Guide",
        "  §10C. Industry Vertical Swapping Guide",
        "  §11. Common Student Pitfalls & Teaching Moments",
        "  §12. Quick-Reference Cards",
        "  §13. Session Planning & Logistics",
        "  §14. Assessment & Grading Rubric",
        "  §15. Facilitator FAQ",
        "  Appendix A: Glossary of Definitions",
        "  Appendix B: Complete Engine Variable Registry",
        "  Appendix C: Academic Reference Matrix",
    ]
    for item in toc_items:
        p = doc.add_paragraph()
        if item.startswith("Part"):
            r = p.add_run(item); r.font.bold = True; r.font.size = Pt(11); r.font.color.rgb = BRAND_NAVY
        elif item.startswith("  App"):
            r = p.add_run(item.strip()); r.font.size = Pt(10); r.font.italic = True
        else:
            r = p.add_run(item.strip()); r.font.size = Pt(10)
        p.paragraph_format.space_after = Pt(2)
    add_page_break(doc)

def build_section1(doc):
    doc.add_heading('PART 1 — FOUNDATION & ENGINE', level=1)
    doc.add_heading('§1. Pedagogical Overview & Learning Objectives', level=1)
    
    doc.add_heading('1.1 Core Narrative & Simulation Premise', level=2)
    doc.add_paragraph(
        'Muressons Global Corporation is a multi-divisional conglomerate operating across four business units: '
        'Pharmaceuticals, Electronics, Consumer Goods, and Software. Over 10 strategic rounds (representing 5 simulated years), '
        'players serve as the executive leadership team navigating interconnected ESG crises, stakeholder pressures, '
        'and systemic sustainability challenges. Every decision creates cascading consequences through hidden mathematical '
        'engines, forcing players to confront the tension between short-term financial performance and long-term '
        'regenerative value creation.'
    )
    doc.add_paragraph(
        'The simulation is built on an immutable state pipeline architecture. The engine.py core executes 20+ '
        'mathematical engines per round in a deterministic sequence, while round_logic.py applies per-round mutations. '
        'This design ensures reproducibility while creating emergent complexity that surprises even experienced players.'
    )
    
    doc.add_heading('1.2 Business Unit Profiles', level=2)
    add_screenshot_placeholder(doc, 'Executive Cockpit — initial state with 4 BU KPI cards')
    add_styled_table(doc,
        ['BU', 'Icon', 'Revenue', 'OPEX', 'Carbon Int.', 'Water Dep.', 'NCD', 'Gov. Risk'],
        [
            ['Pharma', '💊', '$18.0M', '$12.0M', '35', '82', '120', '15'],
            ['Electronics', '⚡', '$16.5M', '$11.5M', '72', '58', '200', '20'],
            ['Consumer Goods', '🛒', '$10.5M', '$7.5M', '48', '65', '150', '10'],
            ['Software', '💻', '$8.5M', '$5.5M', '12', '12', '30', '25'],
        ]
    )
    
    doc.add_heading('1.3 Learning Objectives', level=2)
    lo_table = [
        ['LO1', 'Analyse stakeholder salience using Mendelow\'s Matrix', 'R1, R5, R8', 'Analyse (L4)'],
        ['LO2', 'Evaluate trade-offs between short-term profit and systemic resilience', 'R3, R4, R9', 'Evaluate (L5)'],
        ['LO3', 'Apply double materiality assessment to capital allocation', 'R2', 'Apply (L3)'],
        ['LO4', 'Synthesise ESG strategy that maximises Regenerative Multiple', 'R7, R10', 'Create (L6)'],
        ['LO5', 'Assess autonomous stakeholder reactions and cascade risk', 'R4, R6, R9', 'Evaluate (L5)'],
        ['LO6', 'Design just transition strategies balancing efficiency and equity', 'R9', 'Create (L6)'],
    ]
    add_styled_table(doc, ['LO', 'Description', 'Primary Rounds', 'Bloom\'s Level'], lo_table)
    
    doc.add_heading('1.4 Key Strategic Trade-Offs', level=2)
    tradeoffs = [
        'Short-term cash extraction vs. long-term terminal value: Every dollar saved now compounds against you through NCD interest, VRIO decay, and burnout penalties.',
        'Concentrated investment vs. diversification: Synergy rewards cross-BU integration, but spreading too thin yields diminishing returns (√ scaling).',
        'Transparency vs. containment: Full disclosure costs money upfront but prevents contagion cascades. Deny-and-deflect is free but risks 2× crisis severity.',
        'Adaptation vs. mitigation: Hard engineering builds resilience but adds carbon; nature-based solutions are cheaper but take 2 rounds to mature.',
        'Efficiency vs. equity: Prioritising high-margin BUs maximises short-term EBITDA but triggers social licence collapse and strike risk at R9.',
    ]
    add_bullet_list(doc, tradeoffs, bold_prefix=True)
    
    doc.add_heading('1.5 Simulation Timeline', level=2)
    add_styled_table(doc,
        ['Tier', 'Rounds', 'Theme', 'Cognitive Demand'],
        [
            ['Foundation', 'R1–R3', 'Diagnostic & Strategy Setting', 'Remember → Apply'],
            ['Crisis', 'R4–R6', 'Cascade Management & Ethics', 'Analyse → Evaluate'],
            ['Integration', 'R7–R8', 'Systems Thinking & Resource Allocation', 'Evaluate → Create'],
            ['Finale', 'R9–R10', 'Justice, Valuation & Legacy', 'Create → Synthesise'],
        ]
    )

def build_section2(doc):
    add_page_break(doc)
    doc.add_heading('§2. Theoretical Foundations & Academic Integration', level=1)
    
    doc.add_heading('2.1 Framework-to-Mechanic Mapping', level=2)
    doc.add_paragraph('The simulation embeds 25+ academic frameworks as executable game mechanics. Each theory is experienced before being named — players discover the principle through gameplay, then the facilitator reveals the academic framework during debrief.')
    
    theories = [
        ['Mendelow (1991)', 'Stakeholder Mapping', 'R1', 'Drag-and-drop stakeholder matrix pre-gate'],
        ['Mitchell et al. (1997)', 'Stakeholder Salience', 'R1, R5, R9', 'Power × Legitimacy × Urgency drives agent escalation'],
        ['EU CSRD / ESRS', 'Double Materiality', 'R2', 'CFO materiality gate — 2×2 matrix with budget clawback'],
        ['GHG Protocol', 'Scope 3 Emissions', 'R3', 'Supply chain carbon footprint 4× direct emissions'],
        ['Real Options (Dixit & Pindyck)', 'Option Value of Information', 'R1→R4', 'Deep audit = buying option on future crisis mitigation'],
        ['Argyris (1977)', 'Double-Loop Learning', 'R4', 'Players must question assumptions after R1 cascade reveals'],
        ['Kahneman (2011)', 'System 1/2 Thinking', 'R4, R6', 'Time pressure forces heuristic decision-making'],
        ['Moon (2004)', 'Board Room Moments', 'R4, R5', '3-stage reflection: Noticing → Making Sense → Working with Meaning'],
        ['Schön (1983)', 'Reflection-in-Action', 'R5', 'Shadow Board forces real-time stakeholder perspective-taking'],
        ['Jensen & Meckling (1976)', 'Agency Theory', 'R5', 'Shadow Board persona conflicts embody principal-agent tensions'],
        ['Hirschman (1970)', 'Exit, Voice, Loyalty', 'R5, R9', 'Stakeholder response to dissatisfaction — protest vs. departure'],
        ['Porter (2011)', 'Creating Shared Value', 'R6, R7', 'Ethical AI overhaul and circular economy create dual value'],
        ['Barney (1991)', 'Resource-Based View', 'R7', 'VRIO advantage decays without investment; synergy = rare capability'],
        ['Teece (2007)', 'Dynamic Capabilities', 'R7', 'Workforce readiness gates determine circular economy effectiveness'],
        ['Senge (1990)', 'Learning Organisation', 'R7', 'System archetype detection in reinforcing/balancing loops'],
        ['Hardin (1968)', 'Tragedy of the Commons', 'R8', 'Water scarcity forces collective resource allocation'],
        ['Ostrom (1990)', 'Commons Governance', 'R8', 'Regulatory sandbox Ostrom instruments test self-governance'],
        ['Rawls (1971)', 'Justice as Fairness', 'R9', 'Just transition: efficiency vs. equity in factory closures'],
        ['Freeman (1984)', 'Stakeholder Theory', 'R9', 'Community fund vs. immediate closure — who bears transition cost?'],
        ['Sen (1999)', 'Capabilities Approach', 'R9', 'Green job training expands worker capabilities beyond employment'],
        ['Costanza et al. (1997)', 'Natural Capital', 'All', 'NCD compounding at 6% models ecological debt accumulation'],
        ['Meadows (1999)', 'Leverage Points', 'R10', 'Debrief overlay identifies system intervention hierarchy'],
        ['Kolb (1984)', 'Experiential Learning', 'All', 'Concrete Experience → Reflection → Conceptualisation → Experimentation'],
        ['Thiagarajan (1993)', 'Debrief Protocol', 'R10', '3-phase: How Do You Feel? → What Happened? → So What?'],
        ['Taleb (2012)', 'Antifragility', 'R4, R8', 'Systems that gain from disorder — deep audit teams outperform'],
    ]
    add_styled_table(doc, ['Theory / Author', 'Framework', 'Round(s)', 'Simulation Mechanic'], theories)
    
    doc.add_heading('2.2 Pedagogical Design Principles', level=2)
    principles = [
        'Path Dependency: R1 decisions irrevocably shape R4 crisis severity (40 vs. 80), R9 strike probability, and R10 terminal value. There is no "reset" — every choice persists.',
        'Fog of War: Engine complexity is progressively disclosed. R1-R3 show 5 engines; by R8, all 20+ are visible. This models real-world information asymmetry.',
        'Mechanic Variation: No two rounds use the same decision format — drag-and-drop (R1), 2×2 matrix (R2), slider allocation (R7), tribunal (R8), preventing "solved game" optimisation.',
        'Stochastic Elements: Cyclone probability (75%), whistleblower backfire (40%), macro noise (±3%) — players cannot distinguish luck from strategy without the pedagogical labels.',
        'Hidden Causality: The most important mechanics (contagion sigmoid, burnout quadratic, NCD compounding) are never shown to players. Facilitators reveal them during debrief.',
    ]
    add_bullet_list(doc, principles, bold_prefix=True)

def build_section3(doc):
    add_page_break(doc)
    doc.add_heading('§3. Mathematical Engine Reference', level=1)
    doc.add_paragraph('This section documents every mathematical engine in the simulation\'s process_tick() pipeline. These formulas are HIDDEN from players — they are the facilitator\'s "answer key" for understanding why outcomes occur.')
    add_screenshot_placeholder(doc, 'System architecture flowchart — process_tick() pipeline')
    
    doc.add_heading('3.1 Contagion Engine (Sigmoid)', level=2)
    doc.add_paragraph('Models reputation damage propagation across business units using a sigmoid function on crisis severity.')
    p = doc.add_paragraph(); r = p.add_run('Formula: reputation_hit = max_hit × sigmoid(severity / scale_factor)'); r.font.bold = True; r.font.name = 'Consolas'; r.font.size = Pt(10)
    doc.add_paragraph('Where sigmoid(x) = 1 / (1 + e^(-x)). The non-linear curve means low-severity events are absorbed, but high-severity events cause disproportionate damage. The electronics_blindspot flag DOUBLES severity from 40 to 80, moving the sigmoid from the "manageable" to "catastrophic" region.')
    add_styled_table(doc, ['R1 Choice', 'Severity', 'Sigmoid Output', 'Rep Hit', 'Player Experience'],
        [['Surface Scan (blindspot)', '80', '0.94', '-18.8', 'Devastating cascade'],
         ['Phased Audit (deferred)', '60', '0.82', '-16.4', 'Severe but survivable'],
         ['Deep Audit (no blindspot)', '40', '0.62', '-12.4', 'Manageable crisis']])
    add_callout(doc, 'This is the single most impactful hidden mechanic. The $3M audit in R1 prevents ~$15M in downstream damage — a 5× ROI that players discover only at R4.', 'warning')
    
    doc.add_heading('3.2 Synergy Engine (√ Scaling)', level=2)
    doc.add_paragraph('Models diminishing returns on cross-BU investment using square-root scaling.')
    p = doc.add_paragraph(); r = p.add_run('Formula: synergy_opex = base_opex × √(investment / baseline) × workforce_modifier'); r.font.bold = True; r.font.name = 'Consolas'; r.font.size = Pt(10)
    doc.add_paragraph('The workforce_readiness modifier gates synergy effectiveness: <40 → 30% penalty; 40-60 → neutral; >60 → 10% amplification. This creates a "ceiling" that pure capital investment cannot break through — human capital is the binding constraint.')
    
    doc.add_heading('3.3 NCD Compounding', level=2)
    doc.add_paragraph('Natural Capital Debt compounds at 6% per round, modelling ecological debt accumulation.')
    p = doc.add_paragraph(); r = p.add_run('Formula: NCD_new = NCD_current × 1.06 + round_delta'); r.font.bold = True; r.font.name = 'Consolas'; r.font.size = Pt(10)
    doc.add_paragraph('A team starting with NCD=200 that ignores it for 7 rounds will face NCD=300.7 at R10 — a 50% increase from compound interest alone. This is deducted from terminal value as ecological liability.')
    
    doc.add_heading('3.4 VRIO Decay', level=2)
    doc.add_paragraph('Competitive advantage erodes at 5% per round of neglect. VRIO starts at 0.80 and decays towards 0.50 (industry average) without active investment.')
    p = doc.add_paragraph(); r = p.add_run('Formula: VRIO_new = max(0.50, VRIO_current × 0.95) if no investment this round'); r.font.bold = True; r.font.name = 'Consolas'; r.font.size = Pt(10)
    
    doc.add_heading('3.5 Burnout Engine (Quadratic)', level=2)
    doc.add_paragraph('The burnout penalty follows a quadratic curve — costs accelerate as burnout increases.')
    p = doc.add_paragraph(); r = p.add_run('Formula: burnout_opex_penalty = base × (burnout / 100)²'); r.font.bold = True; r.font.name = 'Consolas'; r.font.size = Pt(10)
    add_styled_table(doc, ['Burnout %', 'OPEX Multiplier', 'Annual Cost Impact', 'Risk Level'],
        [['0-20%', '1.00-1.04', 'Negligible', '🟢 Safe'],
         ['20-40%', '1.04-1.16', '+4-16% OPEX', '🟡 Watch'],
         ['40-60%', '1.16-1.36', '+16-36% OPEX', '🟠 Critical'],
         ['60%+', '1.36+', '+36%+ OPEX', '🔴 Emergency — Strike risk at R9']])
    
    doc.add_heading('3.6 Brain-Drain Engine', level=2)
    doc.add_paragraph('When group reputation drops below 40, the Software BU suffers a talent penalty: -15% revenue per round as top engineers leave for competitors. This creates a vicious cycle — low reputation → talent loss → lower revenue → harder to invest in reputation recovery.')
    
    doc.add_heading('3.7 Terminal Valuation Formula', level=2)
    doc.add_paragraph('The simulation\'s ultimate KPI. Terminal Value determines the company\'s Year 5 worth.')
    p = doc.add_paragraph(); r = p.add_run('TV = (EBITDA - Carbon_Tax × CO₂_Tonnage) × Exit_Multiple × M_R'); r.font.bold = True; r.font.name = 'Consolas'; r.font.size = Pt(10)
    doc.add_paragraph('Where: EBITDA = Σ(BU_Revenue - BU_OPEX), Carbon Tax = $250/ton (default, adjustable via God Mode), Exit Multiple = 12.0×, and M_R = Regenerative Multiple (see §3.8).')
    
    doc.add_heading('3.8 Regenerative Multiple (M_R) Breakdown', level=2)
    doc.add_paragraph('M_R is the simulation\'s "hidden score" — an additive multiplier ranging from 1.0 to ~2.1 that rewards sustainable strategy.')
    add_styled_table(doc, ['Component', 'Bonus', 'Trigger Condition', 'Round Set'],
        [['Base', '1.00', 'Always applied', '—'],
         ['Materiality Governance', '+0.10', 'materiality_aligned flag', 'R2'],
         ['Early Decarboniser', '+0.15', 'early_decarboniser flag', 'R3'],
         ['Remediation Active', '+0.10', 'remediation_active flag', 'R4'],
         ['Truth Premium', '+0.15', 'ethical_ai_overhaul flag', 'R6'],
         ['Resilience Champion', '+0.20', 'nature_based_resilience flag (NOT insurance_only)', 'R5'],
         ['Circularity Bonus', '+0.10 to +0.30', 'circular_redesign or waste_to_energy', 'R7'],
         ['Managed Transition', '+0.12', 'managed_transition flag', 'R9'],
         ['Community Champion', '+0.18', 'community_fund flag', 'R9'],
         ['Instability Discount', '-0.40', 'avg Social License < 75 at R10', 'R10'],
         ['Just Transition Scaling', 'variable', 'HR investment × burnout reduction amplifier', 'R9-R10']])
    add_callout(doc, 'The -0.40 instability discount is the largest single modifier. Teams that neglect Social License will lose more from this penalty than they can gain from all positive bonuses combined.', 'important')
