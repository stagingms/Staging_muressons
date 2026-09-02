"""
Generate Muressons Simulation Context — Elaborated Word Document
Run: python gen_context_docx.py
Output: Muressons_Simulation_Context_Full.docx
"""

from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import copy

# ── Helpers ──────────────────────────────────────────────────────

def set_cell_bg(cell, hex_color):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)

def add_heading(doc, text, level=1):
    h = doc.add_heading(text, level=level)
    run = h.runs[0] if h.runs else h.add_run(text)
    if level == 1:
        run.font.color.rgb = RGBColor(0x05, 0x96, 0x69)   # emerald
    elif level == 2:
        run.font.color.rgb = RGBColor(0x1D, 0x4E, 0xD8)   # blue
    elif level == 3:
        run.font.color.rgb = RGBColor(0x78, 0x71, 0x6C)   # stone
    return h

def add_para(doc, text, bold=False, italic=False, indent=False):
    p = doc.add_paragraph()
    if indent:
        p.paragraph_format.left_indent = Inches(0.3)
    run = p.add_run(text)
    run.bold = bold
    run.italic = italic
    run.font.size = Pt(10.5)
    return p

def add_callout(doc, text, label="ℹ️ Note"):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.3)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(f"{label}  {text}")
    r.italic = True
    r.font.size = Pt(10)
    r.font.color.rgb = RGBColor(0x44, 0x40, 0x3C)

def add_table(doc, headers, rows, header_color="1D4ED8"):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = 'Table Grid'
    # Header row
    hdr_cells = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].text = h
        set_cell_bg(hdr_cells[i], header_color)
        for run in hdr_cells[i].paragraphs[0].runs:
            run.bold = True
            run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            run.font.size = Pt(9.5)
    # Data rows
    for ri, row in enumerate(rows):
        cells = table.rows[ri + 1].cells
        for ci, val in enumerate(row):
            cells[ci].text = str(val)
            for run in cells[ci].paragraphs[0].runs:
                run.font.size = Pt(9.5)
            if ri % 2 == 0:
                set_cell_bg(cells[ci], "F0FDF4")
    doc.add_paragraph()  # spacer
    return table

def add_bullet(doc, text, level=0):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.left_indent = Inches(0.3 + level * 0.2)
    run = p.add_run(text)
    run.font.size = Pt(10.5)
    return p

def divider(doc):
    doc.add_paragraph("─" * 90)

# ── Document Setup ────────────────────────────────────────────────

doc = Document()

# Page margins
for section in doc.sections:
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(2.0)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.0)

# ── COVER PAGE ───────────────────────────────────────────────────

doc.add_paragraph()
title = doc.add_heading("MURESSONS GLOBAL CORPORATION", 0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
title.runs[0].font.color.rgb = RGBColor(0x05, 0x96, 0x69)
title.runs[0].font.size = Pt(24)

sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = sub.add_run("Simulation Context Summary — Comprehensive Reference")
run.font.size = Pt(14)
run.font.bold = True
run.font.color.rgb = RGBColor(0x1D, 0x4E, 0xD8)

doc.add_paragraph()
meta = doc.add_paragraph()
meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
meta.add_run("Version: 2026-05  |  Audience: Facilitators, Developers, AI Assistants\n").font.size = Pt(10)
meta.add_run("All sections cover mechanics, design rationale, and pedagogical intent.").font.size = Pt(10)

doc.add_page_break()

# ════════════════════════════════════════════════════════════════
# SECTION 1: SIMULATION OVERVIEW
# ════════════════════════════════════════════════════════════════

add_heading(doc, "1.  Simulation Overview", 1)

add_para(doc, (
    "Muressons Global Corporation is a multi-round ESG and sustainability strategy simulation "
    "designed for executive education, MBA programmes, and corporate leadership development. "
    "It places teams in the role of the Corporate Strategy & Sustainability Board of a large, "
    "diversified conglomerate and asks them to make interconnected decisions across a simulated "
    "five-year horizon (10 six-month rounds)."
))

add_para(doc, (
    "Unlike simpler compliance training modules, Muressons is built on the principle that "
    "ESG trade-offs are never isolated — every decision ripples through financial performance, "
    "stakeholder trust, regulatory exposure, and enterprise value simultaneously. "
    "The simulation is calibrated so that there is no dominant strategy: "
    "teams that prioritise carbon reduction at the expense of social licence will score differently "
    "from teams that protect employees but defer decarbonisation. "
    "Both approaches have downstream consequences that only become apparent across multiple rounds."
))

add_heading(doc, "1.1  Core Learning Objectives", 2)
bullets = [
    "Master the concept of Double Materiality — understanding that ESG issues affect both financial performance (financial materiality) and the world at large (impact materiality), per CSRD/ESRS 1.",
    "Apply Scope 1/2/3 GHG Protocol carbon accounting under real supply-chain pressure, including the revenue-intensity method for calculating tCO₂e and the role of scope-weighted CI routing.",
    "Navigate crisis management using contagion theory — understanding how reputation damage propagates via an S-curve sigmoid model and how early decisions create or eliminate 'time bomb' flags.",
    "Experience stakeholder fatigue — the discovery that stakeholder trust becomes harder and harder to recover after repeated crises, modelled by a diminishing-returns efficiency formula.",
    "Connect every strategic decision to the Terminal Valuation through the Regenerative Multiple (M_R) — seeing that governance, social, and environmental quality directly affect enterprise value.",
    "Distinguish between short-term cash preservation and long-run value creation — teams that maximise treasury in early rounds often arrive at Round 10 with a structurally impaired valuation.",
    "Understand the Just Transition concept — that workforce communities affected by decarbonisation require investment, and that the quality and consistency of HR investment amplifies the M_R bonus.",
    "Navigate industry-specific ESG risks across multiple sectors (pharma, electronics, oil & gas, agriculture, banking) through the BU substitution system.",
    "Apply real regulatory frameworks: CSRD, ESRS 1, ESRS 2 GOV-1, GHG Protocol, CSDDD, SEBI BRSR, SEC Climate Disclosure, EU CBAM, and SBTi methodologies.",
]
for b in bullets:
    add_bullet(doc, b)

add_heading(doc, "1.2  Simulation Architecture", 2)
add_para(doc, (
    "The simulation runs on a FastAPI Python backend connected to a Next.js frontend. "
    "The core game loop is orchestrated by process_tick() in round_logic.py, which calls all 30+ "
    "engine modules in sequence. Session state is persisted in SQLite via database.py."
))

add_para(doc, "The architecture has three layers of play:", bold=True)
add_bullet(doc, "Main Simulation (10 rounds): The primary decision arc. Each round presents a thematic crisis with three strategic options (A/B/C), plus five pillar investment decisions.")
add_bullet(doc, "Side Tracks (1–6 parallel mini-simulations): Assigned by the Facilitator. The main simulation pauses while a side track runs. Outputs feed back into the main simulation via the Data Bridge contract.")
add_bullet(doc, "Ending Pathways (5 alternate endings): The Facilitator pre-selects one of five alternate Round 10 crisis scenarios. Players receive foreshadowing clues but never see the pathway name directly.")

add_heading(doc, "1.3  Temporal Structure", 2)
add_para(doc, (
    "Each of the 10 rounds represents a six-month decision window. The simulation spans five years. "
    "The macro interest rate environment shifts across the simulation in four phases: "
    "Easing (R1–R2), Neutral (R3–R5), Tightening (R6–R8), and Crisis Premium (R9–R10). "
    "This means decisions about debt, capital allocation, and NCD have a time-value dimension — "
    "the WACC is lowest in early rounds and highest at the terminal valuation moment."
))

add_callout(doc, (
    "The staggered macro environment is intentional pedagogy: teams learn that sustainability "
    "investments made in the easing phase 'compound' into better WACC outcomes at terminal valuation, "
    "while deferred investments accumulate NCD that raises cost of capital at the worst possible time."
), "📐 Design Note")

divider(doc)

# ════════════════════════════════════════════════════════════════
# SECTION 2: BUSINESS UNITS
# ════════════════════════════════════════════════════════════════

add_heading(doc, "2.  Business Units", 1)

add_para(doc, (
    "Muressons is structured as a conglomerate with four active Business Unit (BU) slots. "
    "This structure reflects real-world diversified industrial groups. "
    "Each BU represents a distinct industry with its own carbon profile, water dependency, "
    "social licence sensitivity, and governance risk level. "
    "Teams must manage all four BUs simultaneously — decisions that benefit one BU can "
    "create disruption or cannibalization effects on others."
))

add_heading(doc, "2.1  Default 4-Slot Lineup", 2)

add_table(doc,
    ["BU", "Revenue (USD)", "OPEX (USD)", "CI (tCO2e/USD_M)", "Water Dep.", "Nat. Capital Debt", "Gov. Risk", "SLO Start"],
    [
        ["💊 Pharma",         "$18,000,000", "$12,000,000", "35",  "82", "120", "15", "50"],
        ["⚡ Electronics",    "$16,500,000", "$11,500,000", "72",  "58", "200", "20", "50"],
        ["🛒 Consumer Goods", "$10,500,000",  "$7,500,000", "48",  "65", "150", "10", "50"],
        ["💻 Software",        "$8,500,000",  "$5,500,000", "12",  "12",  "30", "25", "50"],
    ]
)

add_heading(doc, "2.2  Detailed BU Profiles", 2)

# Pharma
add_heading(doc, "Muressons Pharma 💊", 3)
add_para(doc, (
    "Pharma is the highest-revenue BU and the most water-dependent. It represents the "
    "pharmaceutical manufacturing and distribution sector, with significant regulatory scrutiny "
    "from health authorities, environmental agencies, and supply chain labour watchdogs. "
    "Its carbon intensity (35 tCO2e/USD_M revenue) is moderate - reflecting energy-intensive "
    "cleanroom manufacturing but a smaller logistics footprint than Electronics."
))
add_para(doc, (
    "Water dependency of 82 makes it one of the most exposed BUs in the Round 8 (Blue Stress) "
    "drought scenario. If teams choose Option B in Round 8 (Prioritise Electronics), Pharma "
    "suffers a −25 Social Licence hit. Pharma's high social licence sensitivity reflects "
    "patient advocacy groups, employee unions, and community health dependencies."
))
add_para(doc, "Key risk flags unique to Pharma: refinery_blindspot (when substituted with Oil & Gas), land_use_blindspot (when consumer_goods slot uses Agriculture).", italic=True)

# Electronics
add_heading(doc, "Muressons Electronics ⚡", 3)
add_para(doc, (
    "Electronics is the simulation's central 'problem BU'. It has the highest carbon intensity "
    "(72 tCO2e/USD_M) among the defaults - reflecting global electronics manufacturing supply chains "
    "that rely heavily on carbon-intensive materials (rare earths, petrochemical plastics, "
    "energy-intensive semiconductor fabrication). It also carries the highest Natural Capital Debt (200) "
    "at start, representing accumulated environmental liabilities."
))
add_para(doc, (
    "Electronics is the 'blindspot BU' in the default narrative. If the Round 1 audit decision "
    "leaves Electronics uninspected (Options A or C), the 'electronics_blindspot' flag is set. "
    "This flag is a time bomb — it doubles crisis severity in Round 4 from 40 to 80, "
    "causing far greater reputation damage through the Contagion Engine."
))
add_para(doc, (
    "Electronics is also central to the Round 4 (Contagion) narrative — a labour-rights exposé "
    "in its supply chain triggers the reputation cascade. Teams that invested in supply chain "
    "transparency in R1–R2 have a significantly lower base crisis severity."
))

# Consumer Goods
add_heading(doc, "Muressons Consumer Goods 🛒", 3)
add_para(doc, (
    "Consumer Goods is the BU with the highest consumer-facing brand risk. "
    "It is the primary target of the Viral Consumer Boycott Black Swan event (revenue −20%). "
    "Its carbon intensity (48) is mid-range, but its packaging waste and labour-intensive "
    "supply chains make it material for Scope 3 disclosures and Circular Economy compliance."
))
add_para(doc, (
    "Consumer Goods is particularly sensitive to the Round 4 Contagion scenario, the "
    "Round 7 Circular Economy regulations (60% waste diversion mandate), and the "
    "Round 9 Just Transition workforce crisis. The Social Media Boycott Black Swan "
    "exclusively targets Consumer Goods revenue."
))

# Software
add_heading(doc, "Muressons Software 💻", 3)
add_para(doc, (
    "Software is the lowest-carbon, highest-governance-risk BU. Its carbon intensity of 12 "
    "reflects a primarily digital business (SaaS, AI services), but its governance risk score "
    "of 25 — the highest among defaults — reflects data privacy exposure, algorithmic bias risk, "
    "and talent-dependency. The Round 6 (AI Bias) crisis originates in this BU."
))
add_para(doc, (
    "Software is the beneficiary of the AI Disruption Wave Black Swan event (revenue +20%), "
    "but also the most vulnerable to the AI Act regulatory exposure if teams chose "
    "Option A in Round 6 (Monetise the Algorithm). "
    "Its high FX exposure (0.80) also means it is sensitive to macro currency risk."
))

add_heading(doc, "2.3  Universal Starting Values", 2)
add_para(doc, "All BUs, regardless of type, begin with the following shared state values:")
add_table(doc,
    ["State Field", "Starting Value", "Notes"],
    [
        ["social_license_score", "50", "Neutral — neither asset nor liability"],
        ["reputation_score", "55", "Slightly positive brand positioning"],
        ["staff_burnout_index", "10.0", "Low but will drift upward each round without HR investment (+6/round natural drift)"],
        ["vrio_advantage", "0.80", "Decays 2% per round unless reinvested through Operations pillar decisions"],
        ["workforce_readiness", "50", "Group-level metric; changes based on HR pillar choices"],
        ["consecutive_zero_investment_rounds", "0", "Triggers decay acceleration above threshold"],
        ["crisis_count_lifetime", "0", "Feeds Stakeholder Fatigue Engine — higher count = harder to recover trust"],
    ]
)

divider(doc)

# ════════════════════════════════════════════════════════════════
# SECTION 3: GAME STATE KPIs
# ════════════════════════════════════════════════════════════════

add_heading(doc, "3.  Game State KPIs", 1)

add_para(doc, (
    "The simulation tracks two levels of KPIs: group-level metrics that apply to the entire "
    "conglomerate, and per-BU metrics tracked independently for each business unit. "
    "The interplay between these two levels is where the simulation's complexity lives — "
    "a BU-level crisis (e.g., Electronics scandal) immediately affects group-level reputation "
    "through the Contagion Engine."
))

add_heading(doc, "3.1  Group-Level KPIs", 2)
add_table(doc,
    ["KPI", "Scope", "Range", "Key Drivers", "Notes"],
    [
        ["corporate_treasury", "Group", "Can go negative", "Revenue − OPEX − investments − crisis fines", "Starts $50M; primary resource constraint"],
        ["group_reputation", "Group", "0–100", "Crisis outcomes, greenwash, NPC events", "S-curve contagion; S-curve recovery is harder than loss"],
        ["synergy_multiplier", "Group", "0–2.0", "Synergy investments, circular redesign, early_decarboniser flag", "Diminishing returns; sqrt model"],
        ["cost_of_capital / WACC", "Group", "0.05–0.20+", "NCD accumulation, macro rate cycle, regulatory shutdowns", "Directly affects dynamic exit multiple"],
        ["workforce_readiness", "Group", "0–100", "HR pillar decisions; high/medium/no investment tiers", "Starts 50; affects JT scaling and terminal valuation"],
        ["green_fund_balance", "Group", "≥0", "Advanced Climate mode investments only", "Added to EBITDA base in terminal valuation"],
        ["sdg_impact_score", "Group", "−11 to 105", "Corporate SDG side track choices only", "Feeds M_SDG multiplier; 0 if track not played"],
    ],
    "1D4ED8"
)

add_heading(doc, "3.2  Per-BU KPIs", 2)
add_table(doc,
    ["KPI", "Range", "Key Formula / Driver", "Threshold Effects"],
    [
        ["carbon_intensity (CI)", "≥0", "tCO₂e per $1M revenue; weighted by scope ratios", "High CI → carbon tax, litigation risk, CBAM exposure"],
        ["social_license_score (SLO)", "0–100", "Crisis choices, pillar investments, NPC events", "SLO < 40 → Instability Discount −0.40 M_R; SLO = 0 → BU shuttered (Revolt pathway)"],
        ["staff_burnout_index", "0–100", "Natural drift +6/round; HR decisions modify it", "Burnout > 20: quadratic OPEX penalty (max ~18% at 100); > 70: critical flag"],
        ["natural_capital_debt (NCD)", "≥0", "Accumulates without green investment", "Raises WACC; NCD surcharge = base_rate + NCD × 0.0001"],
        ["governance_risk_score", "0–100", "Decision quality, scandal flags, greenwash", "High gov risk → whistleblower Black Swan probability spikes"],
        ["water_dependency", "0–100", "Round 8 choices; desalination reduces by 40", "High dependency at R8 → severe SLO penalties if maladapted"],
        ["vrio_advantage", "0–1.0", "Decays 2%/round unless reinvested", "Low VRIO → lower competitive moats; affects synergy effectiveness"],
        ["reputation_score", "0–100", "Per-BU variant; group_reputation is the weighted avg", "Affected individually by BU-specific crisis events"],
    ],
    "059669"
)

add_heading(doc, "3.3  KPI Interdependencies", 2)
add_para(doc, "The KPIs are not independent — they form a feedback system. Key interdependencies include:")
add_bullet(doc, "High Burnout → OPEX increases → CSF (Corporate Strategic Fund) decreases → treasury pressure → forced shortcuts in investments → further burnout (vicious cycle).")
add_bullet(doc, "High NCD → higher WACC → lower dynamic exit multiple → lower Terminal Value even if EBITDA is strong.")
add_bullet(doc, "Low SLO → higher strike probability → potential revenue zeroing → lower EBITDA base for terminal valuation.")
add_bullet(doc, "High Governance Risk → higher Black Swan event probability (whistleblower, cyber attack, climate litigation) → further reputation and treasury damage.")
add_bullet(doc, "Low Group Reputation → higher Contagion Engine crisis severity in future crisis rounds → reputation further erodes.")

add_callout(doc, (
    "The 'Instability Discount' (−0.40 M_R when avg SLO < 75) is the single largest M_R penalty "
    "in the simulation. Teams that neglect social licence management — even if their financial "
    "metrics look good — will find their terminal valuation severely discounted. "
    "This is the simulation's most important lesson."
), "⚠️ Key Design Insight")

divider(doc)

# ════════════════════════════════════════════════════════════════
# SECTION 4: MAIN SIMULATION — 10 ROUNDS
# ════════════════════════════════════════════════════════════════

add_heading(doc, "4.  Main Simulation — 10 Rounds", 1)

add_para(doc, (
    "The main simulation consists of 10 thematically sequenced rounds. Each round is designed "
    "around a real-world ESG challenge that executives face. The rounds are ordered to create "
    "a logical narrative arc: early rounds establish the company's ESG baseline; "
    "middle rounds test resilience under crisis; late rounds force fundamental strategic choices "
    "with compounding consequences from earlier decisions."
))
add_para(doc, (
    "Each round has two decision layers: (1) a primary crisis decision with three options "
    "(the ABC choice), and (2) five pillar investment decisions that run simultaneously. "
    "Both layers affect the game state, but the ABC choice typically sets the narrative "
    "flags that carry forward into future rounds."
))

# Round 1
add_heading(doc, "Round 1 — Foundations: ESG Baseline Assessment 📋", 2)
add_para(doc, (
    "The board has mandated Muressons' first comprehensive ESG assessment. "
    "The Round 1 decision establishes the company's ESG 'starting posture' — "
    "how deeply the team is willing to invest in understanding its own risks "
    "before the pressure of regulatory deadlines arrives."
))
add_para(doc, "Pedagogical Focus: Risk discovery, audit scope, and the cost of wilful blindness.", italic=True)
add_para(doc, (
    "Option A (Surface-Level Scan): The cheapest choice that saves immediate cash but sets "
    "the 'electronics_blindspot' flag — a hidden time bomb. When the Round 4 labour scandal "
    "erupts in the Electronics supply chain, teams that chose Option A face 2× the crisis "
    "severity (80 instead of 40). The cost of this blindspot far exceeds the short-term saving."
))
add_para(doc, (
    "Option B (Deep Forensic Audit): Costs $3M and takes a small revenue hit, but uncovers "
    "hidden risks, sets 'deep_audit_completed', halves R4 crisis severity, and provides a "
    "clean ESRS data baseline. This is the high-investment, high-information choice that "
    "prepares teams for CSRD disclosure obligations."
))
add_para(doc, (
    "Option C (Phased Audit Rollout): The middle path — audits Pharma and Consumer Goods now, "
    "defers Electronics and Software. Costs $1.5M and avoids the full blindspot, but teams "
    "still carry partial knowledge gaps. The 'deferred_audit' flag can interact with "
    "future regulatory events."
))
add_callout(doc, "Round 1 is the most consequential round for long-term risk profile. The electronics_blindspot flag is the most frequently under-estimated risk in facilitated sessions — teams consistently choose Option A and regret it in Round 4.", "🎓 Facilitator Note")

add_table(doc,
    ["Option", "Title", "Treasury Δ", "Reputation Δ", "Carbon Intensity Δ", "Social Licence Δ", "Gov Risk Δ", "Flag Set"],
    [
        ["A", "Surface-Level Scan", "$0", "−2", "+2", "−3", "+5", "electronics_blindspot"],
        ["B", "Deep Forensic Audit", "−$3M", "+5", "−5", "+5", "−5", "deep_audit_completed"],
        ["C", "Phased Audit Rollout", "−$1.5M", "+2", "−2", "+2", "0", "deferred_audit"],
    ]
)

# Round 2
add_heading(doc, "Round 2 — Double Materiality: Materiality-Based Budget Allocation 📊", 2)
add_para(doc, (
    "The CFO requires all investment proposals to demonstrate alignment with the "
    "High Financial Impact / High ESG Impact quadrant, per the CSRD Double Materiality framework. "
    "This round simulates the real-world tension between formal materiality governance "
    "and the practical pressure to keep the CEO in control of capital allocation."
))
add_para(doc, "Pedagogical Focus: CSRD/ESRS 1 compliance, governance structure, double materiality assessment.", italic=True)
add_para(doc, (
    "Option A (Full Materiality Alignment): Costs $2.5M but earns the 'materiality_aligned' flag "
    "— the only way to unlock the +0.10 M_R Materiality Governance bonus at terminal valuation. "
    "In Advanced Climate mode, it also unlocks an NCD forgiveness multiplier of 1.25×. "
    "This option also ensures the company's report is assurance-ready under ESRS 2 GOV-1."
))
add_para(doc, (
    "Option B (Strategic Exceptions): A pragmatic middle path — allows limited off-quadrant "
    "spending with CFO approval. Partial compliance. This choice often reflects real-world "
    "organisations that have accepted the materiality framework intellectually but not operationally."
))
add_para(doc, (
    "Option C (CEO-Only Sign-Off — ESRS Violation): This option is deliberately designed as a "
    "trap. It appears to save money, but it constitutes a real ESRS 1 §1.51 violation "
    "(the standard requires the management body, not the CEO alone, to oversee materiality). "
    "Institutional investors apply a risk premium, triggering a 40% budget clawback on "
    "any materiality capital released this round. Governance risk spikes +10."
))
add_callout(doc, (
    "The CFO Materiality Gate mechanic means that if players achieve ≥90% materiality accuracy "
    "in their investments, they receive a $2M treasury bonus. This rewards teams that genuinely "
    "internalise the materiality framework rather than just clicking Option A."
), "📐 Special Mechanic")

add_table(doc,
    ["Option", "Title", "Treasury Δ", "Gov Risk Δ", "NCD Δ", "Social Licence Δ", "Flag Set", "Special Consequence"],
    [
        ["A", "Full Materiality Alignment", "−$2.5M", "−5", "−3", "+5", "materiality_aligned", "+0.10 M_R; NCD forgiveness in AC mode"],
        ["B", "Strategic Exceptions", "$0", "−2", "0", "+2", "materiality_exceptions", "Partial compliance; no M_R bonus"],
        ["C", "CEO-Only Sign-Off", "$0", "+10", "+3", "−5", "materiality_ignored", "ESRS §1.51 violation; 40% budget clawback"],
    ]
)

# Round 3
add_heading(doc, "Round 3 — Scope 3: Supply Chain Decarbonisation 🏭", 2)
add_para(doc, (
    "Regulators have signalled mandatory Scope 3 disclosures. Muressons' supply chain carbon "
    "footprint is four times its direct (Scope 1/2) emissions — a realistic figure for "
    "most industrial conglomerates. This round forces teams to grapple with the hardest part "
    "of the decarbonisation agenda: controlling emissions they don't own."
))
add_para(doc, "Pedagogical Focus: GHG Protocol Scope 3, supply chain decarbonisation strategy, Science-Based Targets (SBTi).", italic=True)
add_para(doc, (
    "A key mechanic introduced in this round is scope-weighted CI routing. "
    "Options A and B use 'scope3_weighted' carbon intensity routing, meaning the CI delta "
    "is allocated proportionally to each BU's Scope 3 ratio. Electronics and Consumer Goods — "
    "which have heavy product-lifecycle and material-sourcing emissions — absorb more of the "
    "CI reduction than Pharma or Software."
))
add_para(doc, (
    "Option A (Rapid Supplier Switch): Maximum decarbonisation impact (CI −15) but creates "
    "supply chain disruption risk. Sets the 'early_decarboniser' flag, which grants a "
    "+0.10 synergy multiplier bonus in Round 7 — rewarding teams that move first. "
    "The $4M cost and short-term revenue hit represent the real-world 'greenfield switching cost'."
))
add_para(doc, (
    "Option B (Green Bond Investment): A structured finance approach — issues a green bond "
    "to fund supplier transition. Lower CI reduction (−8) but reduces NCD by 15 units "
    "over three rounds and generates small revenue uplift from the green finance premium. "
    "This models real-world sustainability-linked finance instruments."
))
add_para(doc, (
    "Option C (Offset and Defer): The 'do nothing meaningful' option. Purchases offsets "
    "at minimum cost, retains the carbon deferred flag, and increases NCD. "
    "This choice is a setup for greenwashing risk: if the team later makes "
    "high-green claims without backing them with investment ratios ≥ 15%, "
    "the Greenwashing Engine activates a scandal."
))

add_table(doc,
    ["Option", "Title", "Treasury Δ", "CI Δ (routing)", "NCD Δ", "Flag Set"],
    [
        ["A", "Rapid Supplier Switch", "−$4M", "−15 (scope3-weighted)", "−10", "supply_chain_disruption_risk, early_decarboniser"],
        ["B", "Green Bond Investment", "−$2M", "−8 (scope3-weighted)", "−15", "green_bond_active"],
        ["C", "Offset & Defer", "−$1M", "−1 (uniform)", "+5", "carbon_deferred"],
    ]
)

# Round 4
add_heading(doc, "Round 4 — Contagion: Reputation Crisis Cascade 🔥", 2)
add_para(doc, (
    "A labour-rights exposé in the Electronics supply chain has gone viral. "
    "This is the simulation's first major crisis moment — the moment where all "
    "previous decisions about audit depth, supply chain transparency, and governance quality "
    "begin to pay off or exact their toll."
))
add_para(doc, "Pedagogical Focus: Crisis management, reputational contagion theory, stakeholder communication.", italic=True)
add_para(doc, (
    "The Contagion Engine uses a sigmoid (S-curve) formula to model reputation damage: "
    "Group_Reputation = Avg_Reputation − 50 × sigmoid((severity − 30) / 15). "
    "This means low-severity events barely dent reputation, mid-range events cause "
    "rapid erosion, and very high-severity events plateau at near-maximum damage. "
    "Base crisis severity is 40. If 'electronics_blindspot' is active, severity doubles to 80 "
    "— pushing the curve into its rapid-erosion zone."
))
add_para(doc, (
    "Option A (Full Transparency & Remediation): The most expensive and most effective response. "
    "Opens factories to independent auditors, compensates workers, and publishes findings. "
    "Costs $6M but generates a genuine +10 reputation recovery and +8 SLO improvement. "
    "Sets 'remediation_active', which has positive downstream effects on stakeholder trust."
))
add_para(doc, (
    "Option B (Damage Control PR): Hires a crisis PR firm to control the narrative. "
    "This is a real-world 'spin doctor' approach — it provides a modest +2 reputation boost "
    "but actually reduces SLO by 3 because stakeholders see through the narrative management "
    "without accompanying root-cause fixes. The 'pr_containment' flag carries a credibility discount."
))
add_para(doc, (
    "Option C (Deny and Deflect): The worst possible response in every dimension. "
    "Reputation −15, SLO −10, Governance Risk +8, NCD +5. "
    "This models real-world corporate denial scandals (e.g., Volkswagen emissions, "
    "BP Deepwater Horizon) where denial amplifies rather than contains the crisis."
))

# Round 5
add_heading(doc, "Round 5 — Climate: Physical Climate Risk Event 🌪️", 2)
add_para(doc, (
    "A Category 4 cyclone is projected to hit Muressons' primary manufacturing corridor. "
    "Base damage: $12M. A stochastic dice roll (threshold: 0.75) determines whether the "
    "cyclone actually strikes at full force. This round introduces the concept of "
    "physical climate risk adaptation versus mitigation — and the trade-off between "
    "hard engineering and nature-based solutions."
))
add_para(doc, "Pedagogical Focus: TCFD physical risk, climate adaptation vs. mitigation, resilience investment timing.", italic=True)
add_para(doc, (
    "A critical design feature: both Option A (Hard Engineering) and Option B (Nature-Based Solutions) "
    "have a 2-round construction delay. Protection only activates from Round 7 onward. "
    "This means teams that invest in Round 5 get no protection against the Round 5 cyclone "
    "— but they will be protected in future events. Option C (Insurance Only) provides "
    "no physical protection and permanently blocks the +0.20 Resilience Bonus at terminal valuation."
))
add_para(doc, (
    "Round 5 also activates the Shadow Board — a virtual board of three directors representing "
    "Planet (environmental logic), People/Shareholders (financial logic), and Governance "
    "(regulatory logic). Each director advocates for their preferred option. "
    "If players reject a director's recommendation, a permanent shadow-board penalty flag is set "
    "that affects the terminal valuation in the pathway-specific M_R calculation."
))
add_table(doc,
    ["Option", "Title", "Resilience Factor", "Treasury Δ", "NCD Δ", "CI Δ", "Protection Timing", "Terminal M_R Impact"],
    [
        ["A", "Hard Engineering", "0.85×", "−$8M", "+10", "+3", "R7 onward (2-round delay)", "No M_R penalty"],
        ["B", "Nature-Based Solutions", "0.60×", "−$5M", "−8", "−6", "R7 onward (2-round delay)", "No M_R penalty"],
        ["C", "Insurance Only", "0.00×", "−$2M", "0", "+1", "Never (no physical defence)", "BLOCKS +0.20 Resilience Bonus"],
    ]
)
add_para(doc, "Shadow Board Penalty Flags (set if player rejects director's recommendation):", bold=True)
add_bullet(doc, "Reject Planet director → 'planet_expendable' → −0.20 M_R (all pathways)")
add_bullet(doc, "Reject Shareholder director → 'shareholder_alienated' → −0.20 M_R (Hostile Takeover pathway)")
add_bullet(doc, "Reject Governance director → 'governance_fragility' → −0.25 M_R (Regulatory Shutdown) + BRSR whistleblower leak")

# Round 6
add_heading(doc, "Round 6 — AI Bias: Algorithmic Ethics & Brand Risk 🤖", 2)
add_para(doc, (
    "The Software BU's AI recruitment tool has been found to systematically discriminate "
    "against minority applicants. The story has reached mainstream media. "
    "This round models one of the most topical ESG issues of the 2020s: "
    "the intersection of algorithmic ethics, labour rights, governance, and brand value."
))
add_para(doc, "Pedagogical Focus: AI governance, EU AI Act, responsible technology, social licence through digital ethics.", italic=True)
add_para(doc, (
    "Round 6 also marks the entry into the interest rate 'tightening' phase (R6–R8), "
    "which increases WACC. Teams that have accumulated high NCD will feel this most acutely. "
    "It is also the round where most foreshadowing events begin to arrive (for pathways "
    "other than Climate Black Swan, which starts at R5)."
))
add_para(doc, (
    "Option A (Monetise the Algorithm): The most egregious choice — pivots the biased AI tool "
    "into a commercial product for revenue. Generates $10M Software revenue but causes "
    "Reputation −20 (the largest single-round reputation hit in the simulation), SLO −15, "
    "and sets 'ai_monetised'. From Round 7 onward, EU AI Act compliance costs are applied "
    "as an ongoing OPEX drag."
))
add_para(doc, (
    "Option B (Ethical AI Overhaul): Shuts down the tool, hires an ethics board, "
    "retrains models with bias-corrected datasets. Costs $8M but earns the 'ethical_ai_overhaul' "
    "flag — the only way to unlock the +0.15 Truth Premium M_R bonus at terminal valuation. "
    "Also generates SLO +15, reflecting stakeholders' strong positive response to genuine "
    "ethical commitment."
))
add_para(doc, (
    "Option C (Quiet Patch): Silently fixes the algorithm without public disclosure. "
    "Costs $1M but sets 'quiet_patch' and increases governance risk by 10. "
    "If the algorithm leak is discovered later (through Black Swan events or regulatory investigation), "
    "the penalty is far larger."
))

# Round 7
add_heading(doc, "Round 7 — Circularity: Circular Economy Transition ♻️", 2)
add_para(doc, (
    "New EU circular economy regulations mandate 60% waste diversion by the following year. "
    "Non-compliance fines are set at $15M. This round models the real-world EU Circular Economy "
    "Action Plan and the industry pressure to move from linear 'take-make-dispose' "
    "models to circular product design and extended producer responsibility."
))
add_para(doc, "Pedagogical Focus: EU Circular Economy regulations, EPR (Extended Producer Responsibility), waste-to-energy, synergy mechanics.", italic=True)
add_para(doc, (
    "A key unlock in this round is the 'synergy_unlock' flag (Option C). "
    "Setting this flag at R7 is the primary path to the +0.15 Synergy Strategic Premium M_R. "
    "Note that the synergy bonus is deliberately reduced from an earlier design (+0.30) to "
    "+0.15 because synergy OPEX savings are already captured in the terminal EBITDA calculation — "
    "adding the full +0.30 on top would double-count the benefit. "
    "The +0.15 instead represents the strategic optionality premium investors pay for "
    "integrated, synergistic conglomerate structures."
))
add_para(doc, (
    "The 'early_decarboniser' flag (set in Round 3 if teams chose rapid supplier switch) "
    "provides a +0.10 additional synergy multiplier bonus in this round — "
    "rewarding teams that pursued early supply chain decarbonisation."
))
add_table(doc,
    ["Option", "Title", "Treasury Δ", "NCD Δ", "CI Δ", "Rep Δ", "Social Lic Δ", "Key Unlock"],
    [
        ["A", "Full Circular Redesign", "−$10M", "−12", "−8 (S3W)", "+8", "+6", "circular_redesign"],
        ["B", "Extended Producer Responsibility", "−$5M", "−6", "−5 (S3W)", "+4", "+3", "epr_program"],
        ["C", "Waste-to-Energy Partnership", "−$7M", "−4", "−6 (S3W)", "+0", "+0", "synergy_unlock → +0.15 M_R at R10"],
    ]
)

# Round 8
add_heading(doc, "Round 8 — Blue Stress: Water Scarcity Emergency 🌊", 2)
add_para(doc, (
    "A multi-year drought has depleted the watershed serving Pharma and Electronics. "
    "Government water rationing is imminent. This round models the rapidly escalating "
    "physical climate risk from water scarcity — one of the most material environmental "
    "risks for industrial companies across Asia, Africa, and Southern Europe."
))
add_para(doc, "Pedagogical Focus: Water risk (Blue Stress), climate adaptation, equitable resource allocation, maladaptation.", italic=True)
add_para(doc, (
    "Option B (Prioritise Electronics) is explicitly labelled 'MALADAPTATION (inequitable "
    "resource allocation)' in the config. It allocates water to the highest-margin BU "
    "at the expense of Pharma and Consumer Goods, causing a −25 Social Licence hit to those BUs. "
    "This models real-world cases where businesses prioritise profitable operations over "
    "community or worker welfare during resource crises. "
    "Critically, Option B also blocks the +0.20 Resilience M_R bonus at terminal valuation — "
    "just as 'insurance_only' does. Both represent failures of genuine physical adaptation."
))
add_para(doc, (
    "Option C (Desalination Mega-Project) is the most expensive option at $30M — "
    "a figure large enough to drain a poorly managed treasury. "
    "But it generates $5M/round revenue from Round 10 onward for 3 rounds, "
    "reduces NCD by 30, and cuts water dependency by 40. "
    "Teams that invested heavily in treasury conservation will see this as a viable long-term play."
))
add_table(doc,
    ["Option", "Title", "Treasury Δ", "Water Dep Δ", "Social Lic Δ", "CI Δ", "M_R Impact"],
    [
        ["A", "Water Efficiency for All", "−$12M", "−20", "+5 (all BUs)", "−3", "Preserves +0.20 Resilience bonus"],
        ["B", "Prioritise Electronics", "−$4M", "0", "−25 (Pharma/CG)", "+2", "BLOCKS +0.20 Resilience bonus"],
        ["C", "Desalination Mega-Project", "−$30M", "−40", "+0", "+5", "Preserves bonus; +$5M/round from R10"],
    ]
)

# Round 9
add_heading(doc, "Round 9 — Just Transition: Workforce & Community Justice ✊", 2)
add_para(doc, (
    "Decarbonisation commitments require closing three legacy factories. "
    "2,000 jobs are at risk. Community protests are escalating. "
    "This round tests whether teams understand that decarbonisation without a "
    "'Just Transition' — where affected workers and communities are supported — "
    "destroys the social licence that makes all future operations possible."
))
add_para(doc, "Pedagogical Focus: Just Transition principles, ILO frameworks, worker retraining, community investment, social licence preservation.", italic=True)
add_para(doc, (
    "Round 9 introduces the Just Transition (JT) Scaling mechanic. "
    "The M_R bonuses from Options B and C are multiplied by a JT scaling factor: "
    "min(1.5, 1.0 + HR_investment_rounds × 0.10). "
    "Teams that consistently invested in HR across all previous rounds earn a scaling factor "
    "of up to 1.5× — turning a +0.12 bonus into +0.18 (managed transition) or "
    "a +0.18 bonus into +0.27 (community fund). "
    "This mechanic rewards the entire arc of people investment, not just Round 9 alone."
))
add_para(doc, (
    "Option A (Immediate Closure): Maximises short-term cash (+$5M) but triggers "
    "catastrophic stakeholder consequences. SLO −20, Reputation −15. "
    "If Social Licence is already low (below the threshold), there is a 75% chance "
    "of a full strike that zeroes revenue for the round. "
    "This is explicitly labelled 'MALADAPTATION (short-term extraction)' in the system."
))
add_para(doc, (
    "Option C (Community Investment Fund): Costs $20M — the most expensive R9 choice — "
    "but earns the highest M_R bonus (+0.18, amplified by JT scaling), "
    "SLO +18, and Reputation +12. It represents the 'community-led transformation' "
    "approach recommended by the ILO's Guidelines for a Just Transition."
))
add_table(doc,
    ["Option", "Title", "Treasury Δ", "Social Lic Δ", "Rep Δ", "CI Δ", "M_R Bonus (max with JT×1.5)"],
    [
        ["A", "Immediate Closure", "+$5M", "−20", "−15", "+3", "None; strike risk if SLO low"],
        ["B", "Managed Transition", "−$12M", "+10", "+8", "−4", "+0.12 → up to +0.18 with JT scaling"],
        ["C", "Community Investment Fund", "−$20M", "+18", "+12", "−3", "+0.18 → up to +0.27 with JT scaling"],
    ]
)

# Round 10
add_heading(doc, "Round 10 — Grand Finale: Terminal Valuation 🏛️", 2)
add_para(doc, (
    "Round 10 is the convergence of all prior decisions. The specific crisis scenario is "
    "determined by the ending pathway chosen by the Facilitator (see Section 6). "
    "In the default pathway ('Activist Ultimatum'), an activist consortium that has acquired "
    "a blocking stake demands strategic restructuring."
))
add_para(doc, (
    "After players make their Round 10 crisis decision, the full terminal valuation runs: "
    "EBITDA is calculated from the final BU state, the Regenerative Multiple (M_R) is computed "
    "from all flags accumulated across 10 rounds, the exit multiple (12× default or "
    "WACC-derived dynamic multiple) is applied, and the equity bridge computes "
    "Price Per Share against the IPO anchor of $50.00."
))
add_para(doc, (
    "The final score is not the terminal value alone — it is the company archetype: "
    "Regenerative Titan, De-risked Safe-Haven, Fragile Giant, or Stranded Relic. "
    "Each archetype comes with a custom name, icon, and gradient "
    "that reflects the specific ending pathway."
))

divider(doc)

# ════════════════════════════════════════════════════════════════
# SECTION 5: DECISION PILLARS
# ════════════════════════════════════════════════════════════════

add_heading(doc, "5.  Decision Pillars (Multi-Toggle Paradigm)", 1)

add_para(doc, (
    "In the multi_toggles game paradigm, each round presents five strategic investment pillars "
    "that run simultaneously with the main crisis decision. Players choose one option per pillar, "
    "and all five selections are processed together in the round's process_tick() call. "
    "This models the real-world reality that sustainability decisions are not made one at a time — "
    "a board approves capital allocation across multiple dimensions simultaneously."
))
add_para(doc, (
    "Each pillar has three investment options: typically a high-investment/high-impact choice, "
    "a moderate/incremental choice, and a zero/minimal investment choice. "
    "Unlike the crisis ABC options, pillar decisions are about investment depth "
    "rather than strategic direction."
))

add_heading(doc, "5.1  The Five Pillars", 2)

add_table(doc,
    ["Pillar", "Icon", "What It Models", "Key KPIs Affected"],
    [
        ["Energy", "⚡", "Carbon decarbonisation: renewable energy, efficiency, infrastructure", "carbon_intensity, reputation, NCD"],
        ["Operations", "🏭", "Governance, process redesign, operational resilience, transparency", "governance_risk, reputation, vrio_advantage"],
        ["Supply Chain", "🔗", "Supplier ESG, traceability, diversification, decarbonisation", "carbon_intensity (S3W), SLO, governance_risk"],
        ["Offsetting", "🌱", "Carbon neutrality, community impact, adaptation finance, stakeholder repair", "NCD, social_license, reputation"],
        ["Human Resources", "👥", "Talent, culture, wellbeing, green skills, crisis workforce management", "burnout_index, workforce_readiness, SLO, reputation"],
    ]
)

add_heading(doc, "5.2  Pillar Mechanics", 2)
add_para(doc, "Each pillar option is defined by:", bold=True)
add_bullet(doc, "cost: Treasury delta (negative = investment required; occasionally positive = short-term gain from cutting).")
add_bullet(doc, "impacts: A dictionary of KPI deltas that modify reputation, carbon_intensity, social_license_score, governance_risk, natural_capital_debt, and burnout_index.")
add_bullet(doc, "flags_set: A list of boolean flag identifiers that carry cross-round consequences. These are identical in structure to the crisis ABC flags and interact with the same flag dependency graph.")
add_bullet(doc, "warning_badge: An optional field that displays a risk warning in the UI (e.g., the greenwash risk warning on marketing-only pledges).")

add_heading(doc, "5.3  Round-by-Round Pillar Themes", 2)
add_table(doc,
    ["Round", "Energy", "Operations", "Supply Chain", "Offsetting", "HR"],
    [
        ["1", "Renewable PPA / Solar CapEx / Status Quo", "Lean Process / Digital Twin / No Change", "Full Supplier Audit / Tier-1 Only / Defer", "Nature-Based Offsets / Carbon Credits / No Action", "DEI Program / Leadership Dev / No HR"],
        ["2", "Green Tariff / Efficiency Upgrades / Maintain Baseline", "Materiality Advisory Board / Minimum Compliance / Ignore Materiality", "Blockchain Traceability / Annual ESG Report / No Transparency", "Community Impact Fund / Employee Wellbeing / No Mitigation", "People Analytics / Engagement Survey / No Analytics"],
        ["3", "Fleet Electrification / Hybrid Transition / Keep Diesel", "Closed-Loop Manufacturing / Waste Reduction / No Change", "Rapid Supplier Switch / Green Bond Fund / Offset & Defer", "Science-Based Targets (SBTi) / Voluntary Offsets / Marketing Pledge (greenwash risk)", "Green Skills Academy / Basic OHS Compliance / No Change"],
        ["4", "Green Energy Pivot / Maintain Course / Cut Energy Spending", "Full Factory Transparency / PR Crisis Mgmt / Deny", "Full Supply Chain Remediation / Targeted Fix / Ignore", "Stakeholder Compensation Fund / NGO Partnership / No Action", "Employee Crisis Support / Overtime Push (burnout +12) / No Support"],
        ["5", "Distributed Microgrids / Diesel Generator Backup / No Backup", "Hard Engineering / Nature-Based Solutions / Insurance Only", "Geographic Diversification / Nearshoring / Accept Risk", "Climate Adaptation Fund / Parametric Insurance / No Adaptation", "Emergency Response Training / Basic PPE Upgrade / No Safety Investment"],
        ["6", "Green Data Centres / Optimise Existing / No Change", "Ethical AI Overhaul / Quiet Patch / Monetise Algorithm", "Scope 3 Transparency Programme / Selective Disclosure / No Action", "Integrated Impact Reporting / Minimal Disclosure / None", "Upskilling & Reskilling / Internal Coaching / No Development"],
        ["7", "Hydrogen / Long-Duration Storage / Status Quo", "Circular Product Redesign / Waste Reduction Audit / No Change", "Supplier Circularity Integration / EPR Partnership / No SC Change", "Biodiversity Credits / Voluntary Nature Credits / No Biodiversity", "Just Transition Training / Safety Upskilling / No HR"],
        ["8", "Water-Energy Nexus Optimisation / Basic Metering / No Energy Change", "Water Efficiency Technology / Incremental Reduction / Accept Shortage", "Supply Chain Nearshoring / Dual Sourcing / Accept Risk", "Watershed Restoration Investment / Community Water Fund / No Action", "Worker Wellbeing & Health / Basic Support / No HR"],
        ["9", "Decarbonisation CapEx Programme / Efficiency Retrofit / No Energy", "Factory Repurposing (Green Industry) / Partial Adaptation / Closure", "Community Procurement Policy / Local Supplier Preference / Business As Usual", "Just Transition Community Fund / Worker Retraining Grant / No Action", "Comprehensive Retraining / Basic Support / No Support"],
        ["10", "Green Infrastructure Completion / Partial Completion / None", "Integrated ESG Reporting / Partial Reporting / Minimal", "Stakeholder Compact Finalisation / Selected Commitments / None", "ESG Bond Refinancing / Partial Refinancing / Conventional Debt", "Leadership Legacy Programme / Knowledge Transfer / No HR"],
    ]
)

add_heading(doc, "5.4  Key Pillar Interactions", 2)
add_bullet(doc, "HR Pillar → Just Transition Scaling: Every round where HR investment was made (non-zero choice) counts toward the JT scaling factor applied to R9 community/managed-transition M_R bonuses.")
add_bullet(doc, "Supply Chain Pillar → Black Swan Mitigation: 'blockchain_traceability' (R2 Supply Chain) prevents supply chain scandals and reduces Black Swan conditional probabilities.")
add_bullet(doc, "Offsetting Pillar → Greenwashing Engine: Choosing 'greenwash_risk' (Marketing-Only Pledge) in R3 Offsetting activates a greenwashing audit that checks if investment ratios are ≥ 15% across all decisions.")
add_bullet(doc, "Operations Pillar → Synergy Engine: Digital Twin and Lean Process investments incrementally improve the synergy multiplier, stacking with the major unlock from R7 Waste-to-Energy (crisis option C).")

divider(doc)

# ════════════════════════════════════════════════════════════════
# SECTION 6: ENDING PATHWAYS
# ════════════════════════════════════════════════════════════════

add_heading(doc, "6.  Ending Pathways (5 Alternate Ends)", 1)

add_para(doc, (
    "The Muressons simulation supports five distinct ending pathways. "
    "Each pathway replaces the default Round 10 'Activist Ultimatum' crisis with a unique "
    "existential scenario, complete with its own set of options, M_R bonus/penalty calculators, "
    "archetype override titles, and foreshadowing events injected from Rounds 5–8."
))
add_para(doc, (
    "The pathway is selected by the Facilitator or God Mode at session creation "
    "and can also be set to 'random'. Players are never told the pathway name. "
    "Instead, they receive foreshadowing events — news items, market intelligence reports, "
    "and analyst notes — that hint at what's building. The foreshadowing is calibrated so "
    "that attentive players who track the signals can prepare, while teams focused purely "
    "on quarterly financial metrics will be caught off-guard."
))

add_callout(doc, (
    "The pedagogical purpose of hidden pathways is to simulate real-world strategic uncertainty. "
    "Executives don't know whether their company will face an activist investor, a climate "
    "reckoning, or a regulatory shutdown in Year 5. Building resilience that works across "
    "all five pathways (high SLO, low CI, strong governance, healthy treasury) is the "
    "generalisable lesson."
), "🎓 Pedagogical Purpose")

add_heading(doc, "6.1  Pathway 1: Activist Ultimatum (Default) 🏛️", 2)
add_para(doc, (
    "An activist hedge fund has acquired a blocking stake in Muressons Group and is demanding "
    "a strategic review. The fund's thesis: Muressons is trading at a 'conglomerate discount' "
    "and shareholder value can be unlocked through break-up. The board must choose between "
    "fighting for integration, spinning off the weakest BU, or accepting the activist's terms."
))
add_para(doc, "Real-world parallel: Engine No. 1 / ExxonMobil (2021), Peltz / Unilever, Third Point / Shell.", italic=True)
add_para(doc, "Foreshadowing Events:", bold=True)
add_bullet(doc, "R6: 'Activist Fund Files 13D — 4.9% Stake Acquired' (market intelligence)")
add_bullet(doc, "R7: 'Analyst Note: Muressons Ripe for Restructuring' — Goldman Sachs coverage")
add_bullet(doc, "R8: 'Blocking Stake Reached — Board Engagement Imminent' (flag: pre-takeover_rumour)")

add_para(doc, "R10 Options & Impacts:", bold=True)
add_table(doc,
    ["Option", "Title", "Treasury Δ", "M_R Impact", "Strategic Consequence"],
    [
        ["A", "Resist & Integrate", "−$5M", "Synergy bonus if Synergy > 80", "Requires Synergy Score > 80 (locked if below)"],
        ["B", "Spin-off", "+$10M", "Neutral", "Spins off weakest BU; partial value unlock; SLO −5"],
        ["C", "Divest All", "+$25M", "Synergy wiped", "Maximum cash, minimum long-run value; Rep −10; SLO −12"],
    ]
)

add_heading(doc, "6.2  Pathway 2: Climate Black Swan 🌋", 2)
add_para(doc, (
    "The world has crossed the 1.5°C threshold. Carbon markets are in turmoil — prices have tripled. "
    "Insurance markets are refusing to underwrite carbon-intensive assets. "
    "A cascading climate catastrophe (mega-drought, Arctic methane release, carbon Minsky Moment) "
    "demands an immediate strategic response. This pathway is the most punishing for "
    "teams that deferred decarbonisation."
))
add_para(doc, "Real-world parallel: IPCC AR6, EU ETS price spikes, Lloyd's of London uninsurability reports, Mark Carney's 'Tragedy of the Horizon'.", italic=True)
add_para(doc, "Special Mechanics:", bold=True)
add_bullet(doc, "Carbon tax TRIPLED: $750/tonne instead of $250/tonne. This alone can eliminate 30–40% of terminal EBITDA for high-CI teams.")
add_bullet(doc, "Exit Multiple CI Haircut: Exit_Multiple = 12 × (1 − max(0, (avg_CI − 25) × 0.01)). An avg CI of 75 would reduce the multiple from 12× to 6×.")
add_bullet(doc, "Exit multiple range in this pathway: 6.0× (very high CI) to 12.0× (avg CI ≤ 25).")
add_para(doc, "Foreshadowing Events:", bold=True)
add_bullet(doc, "R5: 'IPCC Special Report: 1.5°C Overshoot Now Likely'")
add_bullet(doc, "R6: 'Carbon Futures Surge 40% — EU ETS Hits Record (€120/tonne)'")
add_bullet(doc, "R7: 'Insurance Consortium: Uninsurable Assets by 2035'")
add_bullet(doc, "R8: 'ALERT: 1.5°C Threshold Breached — Carbon Markets in Turmoil' (flag: climate_threshold_breached)")
add_para(doc, "Pathway-Specific M_R Bonuses/Penalties:", bold=True)
add_table(doc,
    ["Component", "Trigger Condition", "M_R Delta"],
    [
        ["Climate Leader", "avg CI < 25 at R10", "+0.30"],
        ["Adaptation Premium", "nature_based_resilience AND early_decarboniser both active", "+0.20"],
        ["Carbon Transition Bonus", "CI reduced ≥ 40% from R1 baseline to R10", "+0.15"],
        ["Stranded Asset Penalty", "avg CI > 50 at R10", "−0.40"],
        ["Shadow Board Penalty", "planet_expendable flag set (R5 Shadow Board rejection)", "−0.20"],
    ]
)
add_para(doc, "Archetype Overrides in this pathway:", bold=True)
add_table(doc,
    ["Standard Archetype", "Climate Black Swan Override Title", "Icon"],
    [
        ["Regenerative Titan", "The Climate Pioneer", "🌍"],
        ["De-risked Safe-Haven", "The Adapted Enterprise", "🛡️"],
        ["Fragile Giant", "The Stranded Giant", "🏭"],
        ["Stranded Relic", "The Fossil Relic", "🦴"],
    ]
)

add_heading(doc, "6.3  Pathway 3: Stakeholder Revolt 🪧", 2)
add_para(doc, (
    "Employees, communities, and consumers have issued simultaneous ultimatums. "
    "Unionised workers demand burnout protections. Local councils threaten to revoke "
    "operating licences. A consumer boycott is reducing revenue. "
    "This pathway rewards teams that maintained high Social Licence throughout the simulation "
    "and penalises those that prioritised financial efficiency over people and communities."
))
add_para(doc, "Real-world parallel: Amazon warehouse strikes, Shell Nigeria community protests, LVMH labour disputes, social media brand crises.", italic=True)
add_para(doc, "Special Mechanics:", bold=True)
add_bullet(doc, "Social Collapse Threshold: avg SLO < 40 OR avg burnout > 70 → −0.50 M_R (Social Collapse penalty). This is the largest single pathway penalty.")
add_bullet(doc, "If any BU SLO reaches 0 after Option C (Corporate Hardball), that BU is permanently shuttered — removed from EBITDA calculation.")
add_para(doc, "Foreshadowing Events:", bold=True)
add_bullet(doc, "R5: 'Glassdoor Review: Muressons Culture is Toxic'")
add_bullet(doc, "R6: 'Community Coalition Forms Against Industrial Operations'")
add_bullet(doc, "R7: 'Consumer Boycott Hashtag Gains 2M Impressions — #BoycottMuressons'")
add_bullet(doc, "R8: '#MuressonsExposed — Triple Stakeholder Ultimatum' (flag: social_media_campaign)")
add_para(doc, "Pathway-Specific M_R Bonuses/Penalties:", bold=True)
add_table(doc,
    ["Component", "Trigger Condition", "M_R Delta"],
    [
        ["Social Regeneration", "avg SLO ≥ 70 AND avg burnout < 30", "+0.35"],
        ["Employee Champion", "avg burnout < 25 AND workforce_readiness ≥ 70", "+0.15"],
        ["Community Trust", "avg SLO ≥ 80", "+0.15"],
        ["Social Collapse", "avg SLO < 40 OR avg burnout > 70", "−0.50"],
    ]
)
add_para(doc, "Foreshadowing KPI — Social Capital Index (SCI):", bold=True)
add_para(doc, "SCI = (avg_SLO × 0.4) + ((100 − avg_burnout) × 0.3) + (group_reputation × 0.3)", indent=True)
add_para(doc, "Displayed live from R5 to signal social health trajectory.", italic=True, indent=True)

add_heading(doc, "6.4  Pathway 4: Hostile Takeover 🦈", 2)
add_para(doc, (
    "Cerberus Capital has launched a hostile tender offer for Muressons Group at a 15% premium "
    "to current share price. The PE firm plans to break up the conglomerate and sell individual "
    "BUs for parts. The board has 48 hours to respond. Teams' entire strategic track record "
    "determines whether shareholders side with management or the raider."
))
add_para(doc, "Real-world parallel: KKR / Boots (2007), Kraft / Cadbury (2010), Cerberus / Chrysler (2007), Apollo / ADT (2016).", italic=True)
add_para(doc, "Special Mechanics:", bold=True)
add_bullet(doc, "Defence viability threshold: synergy_multiplier ≥ 1.3 makes the White Knight Defence viable (Option A).")
add_bullet(doc, "Takeover Vulnerability Index (TVI): TVI = 100 − (synergy × 30) − (treasury_M × 5) − (EBITDA_margin × 50). Displayed as foreshadowing KPI from R5.")
add_bullet(doc, "Option B (Poison Pill) reduces exit multiple to 10× due to debt overhang from the anti-takeover defence mechanism.")
add_bullet(doc, "Option C (Accept the Bid) locks exit multiple at 8× (breakup discount) and caps M_R at 1.0 — eliminating all ESG premium.")
add_para(doc, "Pathway-Specific M_R Bonuses/Penalties:", bold=True)
add_table(doc,
    ["Component", "Trigger Condition", "M_R Delta"],
    [
        ["Strategic Integration", "synergy ≥ 1.3 AND treasury > $30M", "+0.25"],
        ["Fortress Premium", "EBITDA margin > 20% AND no scandal flags", "+0.20"],
        ["Conglomerate Premium", "synergy ≥ 1.5", "+0.15"],
        ["Vulnerable Target", "synergy < 1.1 AND treasury < $10M", "−0.40"],
        ["Shadow Board Penalty", "shareholder_alienated flag (R5 rejection)", "−0.20"],
    ]
)

add_heading(doc, "6.5  Pathway 5: Regulatory Shutdown ⚖️", 2)
add_para(doc, (
    "A whistleblower has triggered a CSDDD investigation. The environmental regulator "
    "has completed its inquiry and found systematic failures in supply chain due diligence. "
    "Muressons faces a Notice of Violation. The regulator has the power to impose "
    "operational restrictions, heavy fines ($30M base), or a consent decree "
    "requiring third-party monitoring for three years."
))
add_para(doc, "Real-world parallel: VW Dieselgate, OECD CSDDD enforcement cases, SEC greenwashing enforcement against DWS, Glencore FCPA settlement.", italic=True)
add_para(doc, "Special Mechanics:", bold=True)
add_bullet(doc, "Carbon tax elevated to $350/tonne (above standard $250).")
add_bullet(doc, "Ethical Score = (avg_SLO × 0.3 + (100 − avg_CI) × 0.3 + group_reputation × 0.4) / 10. Score range: 0–10. Gates M_R bonuses.")
add_bullet(doc, "Compliance cost for Option A: $4M per BU (4 BUs = $16M total).")
add_bullet(doc, "Option C (Contest the Ruling): If ethical score < 5, court challenge fails — fine doubles to $60M, worst-performing BU suspended, exit multiple drops to 7×.")
add_para(doc, "Pathway-Specific M_R Bonuses/Penalties:", bold=True)
add_table(doc,
    ["Component", "Trigger Condition", "M_R Delta"],
    [
        ["Regulatory Exemplar", "ethical_score > 7 AND no scandal flags", "+0.30"],
        ["Supply Chain Transparency", "scope_3_transparency OR full_remediation flag", "+0.20"],
        ["Proactive Compliance", "ethical_score > 6 AND avg SLO > 60", "+0.15"],
        ["Regulatory Failure", "ethical_score < 4", "−0.45"],
        ["Shadow Board Penalty", "governance_fragility flag (R5 rejection)", "−0.25"],
    ]
)
add_para(doc, "Foreshadowing KPI — Compliance Risk Index (CRI):", bold=True)
add_para(doc, "CRI = (avg_CI × 0.4) + ((100 − avg_SLO) × 0.3) + ((100 − group_reputation) × 0.3)", indent=True)
add_para(doc, "A CRI above 60 indicates high regulatory exposure. Displayed from R5.", italic=True, indent=True)

add_heading(doc, "6.6  Pathway Difficulty and Leaderboard Normalisation", 2)
add_para(doc, (
    "To enable fair cross-session comparison on leaderboards when different facilitators "
    "have used different pathways, M_R scores are normalised by a difficulty coefficient. "
    "This prevents teams who played Activist Ultimatum (the easiest pathway to score well on) "
    "from appearing unfairly superior to teams who navigated Climate Black Swan or Hostile Takeover."
))
add_table(doc,
    ["Pathway", "Difficulty Coefficient", "Effect on Normalised M_R"],
    [
        ["Activist Ultimatum", "1.00", "No adjustment (baseline)"],
        ["Stakeholder Revolt", "1.10", "+10% normalised score"],
        ["Regulatory Shutdown", "1.12", "+12% normalised score"],
        ["Climate Black Swan", "1.15", "+15% normalised score"],
        ["Hostile Takeover", "1.20", "+20% normalised score (hardest to win)"],
    ]
)

divider(doc)

# ════════════════════════════════════════════════════════════════
# SECTION 7: SIDE TRACKS
# ════════════════════════════════════════════════════════════════

add_heading(doc, "7.  Side Tracks (6 Parallel Mini-Simulations)", 1)

add_para(doc, (
    "Side tracks are self-contained mini-simulations that deepen specific ESG competencies. "
    "Each track is a 4–7 round decision arc with its own crisis scenarios, scoring system, "
    "and leaderboard. The main simulation pauses when a side track is active, "
    "and track outcomes feed back into the main simulation through the Data Bridge contract."
))
add_para(doc, "The Data Bridge contract has two mandatory methods:", bold=True)
add_bullet(doc, "seed_from_main_state(): Reads current main-sim state (treasury, NCD, flags, BU metrics) to initialise the side track. This means teams that performed well in the main sim start the side track with better baseline conditions.")
add_bullet(doc, "write_back_to_main(): At track completion, merges specific flags and modifiers back into the main simulation's active_event_flags. This is how side track performance translates to M_R bonuses, regulatory readiness, and Black Swan probability changes.")

add_heading(doc, "7.1  Side Track 1: Supply Chain 🔗", 2)
add_para(doc, (
    "Focuses on end-to-end supply chain management: supplier ESG auditing, visibility mapping, "
    "risk scoring, and circular economy integration. Teams who complete this track with strong "
    "performance reduce their Black Swan conditional probabilities for supply-chain-related events "
    "(Critical Mineral Embargo, Whistleblower Scandal when triggered by supply chain failures)."
))
add_para(doc, "Available window: Main Rounds 3–7 | Length: 5 rounds", italic=True)
add_para(doc, "Scoring dimensions: Supply Visibility (0–100), Supplier Risk Score (0–100), ESG Compliance Rate (0–100), Circular Economy Integration Score (0–100)", italic=True)

add_heading(doc, "7.2  Side Track 2: Ethics & Sustainability 🌿", 2)
add_para(doc, (
    "Covers ethical governance, anti-corruption measures, and human rights due diligence (HRDD). "
    "Completing this track with high scores enriches the BRSR NGRBC starting position "
    "by +10 Governance & Ethics, and contributes to lower governance risk scores in the main sim. "
    "Real-world frameworks covered: OECD Guidelines for Multinational Enterprises, "
    "UN Guiding Principles on Business and Human Rights (UNGPs), and UNGC Ten Principles."
))
add_para(doc, "Available window: Main Rounds 2–7 | Length: 5 rounds", italic=True)

add_heading(doc, "7.3  Side Track 3: Stakeholder Management 🤝", 2)
add_para(doc, (
    "Models complex NPC (Non-Player Character) stakeholder dynamics — trust building, "
    "coalition management, and navigating conflicting stakeholder interests. "
    "The Stakeholder Fatigue Engine applies to this track, meaning recovery efficiency "
    "diminishes after each crisis. Teams learn that proactive relationship management "
    "is far more effective than reactive crisis appeasement."
))
add_para(doc, "Available window: Main Rounds 3–8 | Length: 5 rounds", italic=True)
add_para(doc, "Write-back: SLO floor improvements and Stakeholder Fatigue multiplier modifiers fed back to main sim.", italic=True)

add_heading(doc, "7.4  Side Track 4: Sustainability Reporting 📋", 2)
add_para(doc, (
    "Simulates the process of building a CSRD-compliant sustainability report: "
    "selecting material topics, engaging stakeholders for data, choosing assurance levels, "
    "and managing regulatory disclosure quality. The key output is a 'regulatory_readiness' "
    "score (0–100). If regulatory_readiness > 60, the BRSR NGRBC side track starting position "
    "gains +15 Reporting Quality — reflecting the cross-framework portability of good disclosure practice."
))
add_para(doc, "Available window: Main Rounds 4–8 | Length: 5 rounds", italic=True)
add_para(doc, "Real-world frameworks: CSRD/ESRS, GRI Universal Standards, ISSB S1/S2, TCFD, TNFD.", italic=True)

add_heading(doc, "7.5  Side Track 5: Corporate SDG Deep Track 🌐", 2)
add_para(doc, (
    "A five-round SDG alignment track covering the UN Sustainable Development Goals "
    "across five thematic areas. This is the most mechanically complex side track "
    "because it has a direct multiplier on the terminal valuation formula."
))
add_para(doc, "Available window: Main Rounds 1–8 | Length: 5 rounds", italic=True)

add_para(doc, "Round Themes & BU Targeting:", bold=True)
add_table(doc,
    ["ST Round", "Theme", "SDG Focus", "Target BUs"],
    [
        ["1", "Principal Adverse Impact (PAI) Audit", "SDG 13, 17", "Group-wide"],
        ["2", "Living Wage Commitment", "SDG 8 (Decent Work)", "Electronics, Consumer Goods"],
        ["3", "Circular Procurement", "SDG 12 (Responsible Consumption)", "Electronics, Consumer Goods"],
        ["4", "Biodiversity Net-Gain", "SDG 15 (Life on Land), SDG 14", "Consumer Goods, Pharma"],
        ["5", "Integrated Reporting", "SDG 17 (Partnerships)", "Group-wide"],
    ]
)

add_para(doc, "Terminal Valuation Integration:", bold=True)
add_para(doc, "M_SDG = 1.0 + (SDG_Impact_Score / 100) × 0.25", indent=True)
add_para(doc, "SDG Impact Score range: −11 (all Option C) to 105 (all Option A).", indent=True)
add_para(doc, "M_SDG range: 0.97 → 1.26. This multiplier is applied directly to the terminal value: TV = EBITDA × Exit × M_R × M_SDG.", indent=True)

add_para(doc, "SDG Drag/Boost System (real-time effects on main simulation):", bold=True)
add_bullet(doc, "Cumulative SDG score < 40 → regulatory_ratchet_active flag set. This applies an OPEX uplift penalty in the main simulation's next round — ESG underperformers pay a real operational cost.")
add_bullet(doc, "Score > 70 → reputational tailwind: +2 group reputation per SDG round completed. This creates a compounding brand benefit.")
add_bullet(doc, "circular_leader flag earned → synergy multiplier protected from erosion. A floor of 1.10 is maintained, ensuring circular economy teams never fall below a base synergy level.")
add_bullet(doc, "nature_positive flag → NCD interest rate reduced −1% per subsequent SDG round, reducing the cost-of-capital penalty from Natural Capital Debt.")

add_para(doc, "Greenwash Wiring:", bold=True)
add_para(doc, (
    "If players choose the 'Marketing-Only Pledge' option in ST-R3 (Circular Procurement), "
    "the greenwash_risk flag activates the main engine's scandal detection mechanism. "
    "This triggers a narrative event: NGO analysis reveals no underlying operational change, "
    "SDG 12 claim is performative, and a credibility penalty is applied to brand valuation. "
    "This teaches players that SDG commitments require operational backing, not just disclosure."
))

add_para(doc, "SDG Impact Score → Grade & Archetype:", bold=True)
add_table(doc,
    ["Normalised Score", "Grade", "Archetype"],
    [
        ["≥ 90%", "A+", "SDG Champion — Comprehensive alignment across all dimensions"],
        ["75–89%", "A", "SDG Leader — Strong performance with minor gaps"],
        ["60–74%", "B", "SDG Performer — Meaningful progress with room for improvement"],
        ["40–59%", "C", "SDG Starter — Basic awareness, significant gaps remain"],
        ["< 40%", "D", "SDG Laggard — Critical gaps creating material risk"],
    ]
)

add_heading(doc, "7.6  Side Track 6: BRSR NGRBC Deep Dive 🇮🇳", 2)
add_para(doc, (
    "A ten-round deep dive into the Securities and Exchange Board of India (SEBI) "
    "Business Responsibility and Sustainability Report (BRSR) framework, "
    "covering all nine National Guidelines on Responsible Business Conduct (NGRBC) principles. "
    "This track is specifically designed for Indian corporates and MBA programmes "
    "covering Indian regulatory requirements, but is also relevant globally as a "
    "governance-heavy, multi-stakeholder ESG framework."
))
add_para(doc, "Available window: Main Rounds 2–8 | Length: 10 rounds", italic=True)
add_para(doc, "Cross-track prerequisites: sustainability_reporting + ethics_sustainability (both enrich starting scores)", italic=True)

add_para(doc, "Round Themes & NGRBC Principles:", bold=True)
add_table(doc,
    ["ST Round", "NGRBC Principles", "Focus"],
    [
        ["1", "P1 (Ethics), P7 (Policy Advocacy)", "Governance structure; BRSR Core eligibility; governance_fragility vs brsr_pioneer flags"],
        ["2", "P3 (Employee Wellbeing), P5 (Human Rights)", "Living wage; BRSR Leadership indicators; burnout reduction; human capital KPIs"],
        ["3", "P6 (Environmental), P2 (Product Lifecycle)", "Scope 3 disclosure; environmental stewardship; synergy bonus if Option A"],
        ["4", "P4 (Stakeholder Responsiveness), P8 (Inclusive Growth), P9 (Consumer Responsibility)", "Value chain due diligence; greenwash_risk trigger for SEBI show-cause notice"],
        ["5", "All principles — BRSR Core assurance", "Integrated disclosure; BRSR Core third-party assurance; final reporting quality score"],
    ]
)

add_para(doc, "Scoring Formula:", bold=True)
add_para(doc, "Total BRSR Score = (Governance & Ethics × 0.20) + (Human Capital × 0.20) + (Environmental × 0.25) + (Value Chain × 0.20) + (Reporting Quality × 0.15)", indent=True)

add_para(doc, "Write-back to Main Simulation:", bold=True)
add_bullet(doc, "BRSR Score ≥ 80 → brsr_net_positive_dividend = 0.05 → +0.05 M_R ESG Alpha Dividend at terminal valuation.")
add_bullet(doc, "brsr_pioneer flag → enables BRSR Pioneer archetype pathway.")
add_bullet(doc, "brsr_core_assured flag → in ST-R5, reduces crisis severity by −10.")
add_bullet(doc, "governance_fragility → brsr_truth_premium_cost_doubled and whistleblower leak at ST-R5 (−$2.5M treasury).")
add_bullet(doc, "brsr_greenwash_risk → SEBI show-cause notice at ST-R4: group reputation −12 and narrative event published.")

add_para(doc, "BRSR Archetypes:", bold=True)
add_table(doc,
    ["Score Range", "Archetype", "Icon", "Description"],
    [
        ["≥ 80", "BRSR Pioneer", "🏆", "Exemplary NGRBC Leadership Indicators and rigorous BRSR Core value chain assurance"],
        ["60–79", "Responsible Steward", "🌿", "Meets Essential Indicators reliably and adopts strategic Leadership practices"],
        ["40–59", "Compliance Pragmatist", "📋", "Fulfils mandatory SEBI BRSR requirements but exposed to unchecked ESG risks"],
        ["< 40", "Regulatory Laggard", "⚠️", "Fails basic Essential indicators; high risk of regulatory action"],
    ]
)

divider(doc)

# ════════════════════════════════════════════════════════════════
# SECTION 8: TERMINAL VALUATION
# ════════════════════════════════════════════════════════════════

add_heading(doc, "8.  Terminal Valuation & Archetypes", 1)

add_para(doc, (
    "Terminal valuation is the simulation's climax — the moment where every decision "
    "made across 10 rounds (and any side tracks) crystallises into a single enterprise value, "
    "equity value, and price per share. It is designed to make the connection between "
    "ESG quality and financial value undeniable."
))

add_heading(doc, "8.1  The Full Formula Chain", 2)
add_para(doc, "Step 1: Terminal EBITDA", bold=True)
add_para(doc, "Terminal_EBITDA = Σ(BU Revenue − BU OPEX) − (Total_tCO₂e × Carbon_Tax_Per_Tonne)", indent=True)
add_para(doc, "Where Total_tCO₂e = Σ(carbon_intensity_i × revenue_i / 1,000,000) across all BUs.", indent=True)

add_para(doc, "Step 2: Enterprise Value (Terminal Value)", bold=True)
add_para(doc, "TV = (Terminal_EBITDA + Green_Fund_Balance) × Exit_Multiple × M_R × M_SDG", indent=True)
add_para(doc, "Green Fund Balance is only added in Advanced Climate mode sessions.", indent=True)

add_para(doc, "Step 3: Equity Bridge", bold=True)
add_para(doc, "Equity_Value = Enterprise_Value − Net_Debt", indent=True)
add_para(doc, "Price_Per_Share = Equity_Value / 100,000,000 shares", indent=True)
add_para(doc, "IPO anchor price: $50.00/share. Share price vs. IPO is displayed as a gain/loss percentage.", indent=True)

add_para(doc, "Step 4: Market Multiples (Benchmark Signals)", bold=True)
add_para(doc, "EV/Revenue = Enterprise_Value / Total_Revenue  (sector benchmark: 2.5×)", indent=True)
add_para(doc, "Price/Book = Equity_Value / Book_Equity  (sector benchmark: 1.5×)", indent=True)
add_para(doc, "Signals: Premium (>120% of benchmark) / Fair / Discount (<80% of benchmark)", indent=True)

add_heading(doc, "8.2  Exit Multiple", 2)
add_para(doc, "Two modes for exit multiple calculation:", bold=True)
add_bullet(doc, "Fixed: 12.0× (default for most sessions). Can be overridden by pathway mechanics.")
add_bullet(doc, "Dynamic (WACC-linked): Exit_Multiple = (1 + g) / (WACC − g), where g = 2% long-run growth. Floor: 6×, Ceiling: 18×.")
add_para(doc, (
    "The dynamic mode links WACC directly to the exit multiple, creating a clear incentive "
    "to keep cost of capital low. A team with WACC = 8% gets a 12.25× multiple; "
    "a team with WACC = 14% (due to high NCD and regulatory risk premiums) gets only a 7.4× multiple. "
    "This makes Natural Capital Debt management critical even for financially-minded teams."
))
add_para(doc, "Macro Rate Cycle effect on WACC:", bold=True)
add_table(doc,
    ["Rounds", "Regime", "WACC Modifier", "Design Intent"],
    [
        ["R1–R2", "Easing", "−1%", "Reward early investment; low cost of capital"],
        ["R3–R5", "Neutral", "0%", "Standard conditions"],
        ["R6–R8", "Tightening", "+2%", "Penalise deferred decarbonisation"],
        ["R9–R10", "Crisis Premium", "+3%", "Maximum pressure at terminal valuation moment"],
    ]
)

add_heading(doc, "8.3  Regenerative Multiple (M_R)", 2)
add_para(doc, (
    "M_R is the ESG quality and risk modifier applied to the terminal EBITDA. "
    "It ranges from 0.0 to approximately 2.03. "
    "A team with M_R = 2.0 earns double the enterprise value for the same EBITDA "
    "compared to M_R = 1.0 — this is the quantitative core of the simulation's central argument: "
    "ESG is value creation, not cost."
))
add_table(doc,
    ["M_R Component", "Trigger Condition", "Value", "Notes"],
    [
        ["Base", "Always", "+1.00", "Minimum M_R with no ESG actions"],
        ["Materiality Governance", "materiality_aligned flag (R2 Option A)", "+0.10", "Rewards genuine CSRD compliance"],
        ["Synergy Strategic Premium", "synergy_unlock AND synergy ≥ 0.80 (R7 Option C)", "+0.15", "Reduced from +0.30 to avoid double-counting OPEX savings already in EBITDA"],
        ["Resilience Champion", "No insurance_only AND no electronics_water_priority", "+0.20", "Blocks if teams took shortcut adaptation in R5 or R8"],
        ["Truth Premium", "ethical_ai_overhaul flag (R6 Option B)", "+0.15", "Rewards genuine ethical commitment vs. coverup"],
        ["Community Champion", "community_fund flag (R9 Option C) × JT scaling", "+0.18 → up to +0.27", "JT scaling: up to 1.5× if HR consistently invested"],
        ["Just Transition", "managed_transition flag (R9 Option B) × JT scaling", "+0.12 → up to +0.18", "Same JT scaling as Community Champion"],
        ["Workforce Excellence", "workforce_readiness ≥ 75 at R10", "+0.10", "Rewards sustained HR investment"],
        ["Wellbeing Champion", "avg burnout < 20 across all BUs at R10", "+0.05", "Very hard to achieve — requires consistent HR choices"],
        ["BRSR ESG Alpha Dividend", "brsr_net_positive_dividend (BRSR track score ≥ 80)", "+0.05", "Only available if BRSR side track completed"],
        ["Planet Expendable Penalty", "planet_expendable (R5 Shadow Board rejection)", "−0.20", "Permanent penalty for ignoring environmental logic"],
        ["Instability Discount", "avg SLO < 75 at R10", "−0.40", "The largest single penalty — rewards consistent social licence investment"],
    ]
)

add_callout(doc, (
    "The Instability Discount (−0.40) is the most consequential M_R component. "
    "It means that a team which otherwise earns all positive bonuses "
    "(base + all components = ~1.93) but has neglected Social Licence will score only 1.53 — "
    "the difference between a Regenerative Titan and a De-risked Safe-Haven. "
    "This is the simulation's strongest lesson about stakeholder capitalism."
), "💡 Key Teaching Point")

add_heading(doc, "8.4  SDG Multiplier (M_SDG)", 2)
add_para(doc, "M_SDG = 1.0 + (SDG_Impact_Score / 100) × 0.25")
add_para(doc, (
    "This multiplier is only meaningful if the Corporate SDG side track has been played. "
    "For sessions without the SDG track, SDG_Impact_Score = 0 → M_SDG = 1.0 (neutral). "
    "For a team that earns the maximum 105 SDG points (all Option A), M_SDG = 1.2625. "
    "Applied to TV = EBITDA × Exit × M_R × 1.26, this represents a 26% terminal value uplift "
    "purely from SDG alignment — a meaningful commercial incentive."
))

add_heading(doc, "8.5  Company Archetypes", 2)
add_table(doc,
    ["M_R Range", "Archetype", "Icon", "Meaning", "Default Gradient Colour"],
    [
        ["≥ 1.80", "The Regenerative Titan", "🌱", "Proactive ESG leadership; stakeholder trust; strong governance; low carbon — the ideal end state", "Emerald green"],
        ["1.20–1.79", "The De-risked Safe-Haven", "🏦", "Defensive ESG adoption; manageable risks; acceptable SLO — the institutional investor's preferred outcome", "Blue"],
        ["0.80–1.19", "The Fragile Giant", "⚠️", "Financial metrics intact but ESG risks building; exposed to future regulatory and stakeholder pressure", "Amber"],
        ["< 0.80", "The Stranded Relic", "💀", "ESG failures have materially impaired value; exposed to stranded asset risk and social licence collapse", "Red"],
        ["Survival Mode", "The Turnaround Manager", "🔧", "Activated when a team's treasury crosses into insolvency territory; M_R capped at 0.80; narrative focuses on recovery", "Purple"],
    ]
)
add_para(doc, "Note: Each ending pathway has custom archetype titles and icons that override these defaults (see Section 6 for pathway-specific archetype names).", italic=True)

divider(doc)

# ════════════════════════════════════════════════════════════════
# SECTION 9: STOCHASTIC SYSTEMS
# ════════════════════════════════════════════════════════════════

add_heading(doc, "9.  Stochastic Systems", 1)

add_para(doc, (
    "Several simulation mechanics introduce deliberate randomness to model real-world uncertainty. "
    "These stochastic systems teach teams that good strategic decisions reduce risk exposure "
    "but cannot eliminate uncertainty — and that maintaining financial and social buffers "
    "is valuable precisely because of this irreducible randomness."
))

add_heading(doc, "9.1  Round 5 Cyclone Damage Roll", 2)
add_para(doc, (
    "In Round 5, a stochastic roll determines whether the cyclone strikes at full force. "
    "The roll threshold is 0.75: if random() > 0.75, the cyclone strikes and the base damage "
    "of $12M is applied. The actual damage is then moderated by the team's Resilience Factor "
    "from their chosen option."
))
add_para(doc, "Actual Damage = Base_Damage × (1 − Resilience_Factor)", indent=True)
add_para(doc, (
    "However, neither Hard Engineering (Option A) nor Nature-Based Solutions (Option B) "
    "provides protection in Round 5 itself — both have a 2-round construction delay. "
    "Protection activates from Round 7 onward, providing resilience against any future "
    "stochastic climate events or the cyclone's lingering supply chain effects."
))
add_callout(doc, "Teams often experience cognitive shock when they invest $8M in Hard Engineering in R5 and then suffer the full $12M cyclone damage anyway. This teaches the temporal gap between investment and impact — a critical lesson in long-horizon sustainability planning.", "🎓 Facilitation Moment")

add_heading(doc, "9.2  Round 9 Strike Probability", 2)
add_para(doc, (
    "If Social Licence falls below the threshold AND the 'immediate_closure' flag is set "
    "(Option A in Round 9), there is a 75% probability of a full industrial strike. "
    "A strike zeros revenue for the round — completely eliminating EBITDA contribution "
    "from all BUs for that period. This is a devastating financial outcome for any team "
    "already struggling with treasury management."
))
add_para(doc, (
    "The strike probability is also elevated by the Round 9 special rule: "
    "'low_social_license_strike_trigger' and 'regulatory_friction_enabled'. "
    "These simulate the real-world regulatory environment around industrial closures, "
    "where labour relations legislation creates mandatory notice periods and consultation requirements."
))

add_heading(doc, "9.3  Greenwashing Engine", 2)
add_para(doc, (
    "The Greenwashing Engine activates when players select a high-impact green option "
    "(Options A or C in most rounds) without backing it with sufficient investment ratios "
    "(investment budget ≥ 15% of available capital). This threshold is deliberately set "
    "to reward genuine commitment over performative ESG signalling."
))
add_para(doc, "When the Greenwashing Engine triggers:", bold=True)
add_bullet(doc, "Group reputation penalty: −15 (option A/C with high green claims).")
add_bullet(doc, "Auditor tolerance set to 'Hostile' — future audit interactions become more adversarial.")
add_bullet(doc, "greenwash_exposed flag set — increases Black Swan probability for Whistleblower Scandal event.")
add_bullet(doc, "Option B (moderate choices) has a lower threshold of 10% — reflecting that nuanced positions require less investment backing to be credible.")
add_callout(doc, "The 15% threshold was calibrated against real-world analysis of green investment pledges vs. capital expenditure patterns across European industrials. Companies that spend < 10% of invested capital on ESG while claiming comprehensive sustainability leadership are classified as greenwashers by NGOs and regulators.", "📐 Calibration Note")

add_heading(doc, "9.4  Macro Interest Rate Cycles", 2)
add_para(doc, (
    "The simulation models a four-phase central bank policy cycle over the 10 rounds. "
    "This creates a realistic 'credit cycle' context for capital allocation decisions: "
    "investments made during easing have a lower cost of capital, while debt accumulated "
    "during tightening carries higher servicing costs."
))
add_table(doc,
    ["Rounds", "Regime", "WACC Modifier", "Real-World Parallel"],
    [
        ["R1–R2", "Monetary Easing", "−1% on base WACC", "Post-crisis accommodative policy (e.g., 2009–2015, 2020–2021)"],
        ["R3–R5", "Neutral Rate", "0%", "Steady-state environment; transition period"],
        ["R6–R8", "Tightening Cycle", "+2%", "Inflation-fighting rate hikes (e.g., 2022–2023 Fed/ECB cycle)"],
        ["R9–R10", "Crisis Premium", "+3%", "Elevated risk premium when uncertainty peaks at terminal valuation moment"],
    ]
)

divider(doc)

# ════════════════════════════════════════════════════════════════
# SECTION 10: BLACK SWAN EVENTS
# ════════════════════════════════════════════════════════════════

add_heading(doc, "10.  Black Swan Events", 1)

add_para(doc, (
    "Black Swan events are stochastic, low-probability, high-impact events "
    "drawn from Nassim Taleb's fat-tail probability theory (2007) and "
    "Weick & Sutcliffe's High Reliability Organisation (HRO) framework. "
    "They are evaluated every round via evaluate_black_swans() called from process_tick()."
))
add_para(doc, (
    "The pedagogical purpose of Black Swans is to test whether teams have built "
    "genuine organisational resilience — not just optimised their expected-value path. "
    "Teams with high treasury buffers, low governance risk, and strong social licence "
    "survive Black Swan events far better than teams that optimised only financial KPIs."
))

add_heading(doc, "10.1  Difficulty Scaling", 2)
add_table(doc,
    ["Tier", "Label", "Prob. Multiplier", "Impact Multiplier", "Treasury Floor", "Design Intent"],
    [
        ["Easy", "Introductory", "0.5×", "0.7×", "−$500M", "Lower risk for learning environments; pedagogy over realism"],
        ["Standard", "Professional", "1.0×", "1.0×", "−$200M", "Default; calibrated for MBA cohorts"],
        ["Expert", "Executive", "1.5×", "1.3×", "−$50M", "High-stakes executive simulations; near-insolvency risk is real"],
    ]
)

add_heading(doc, "10.2  Global Black Swan Events (All Regions)", 2)
add_table(doc,
    ["Event", "Icon", "Round Range", "Base Prob", "Key Financial Impact", "Pedagogical Note"],
    [
        ["Sovereign Debt Crisis", "🏦", "R4–R8", "8%", "−12% treasury, +300bps interest, −10% revenue (2 rounds)", "Tests treasury buffer adequacy; geographic diversification value"],
        ["Internal Whistleblower Scandal", "🔔", "R3–R9", "6%", "Rep −20, treasury −8%, SLO −15, Gov Risk +15", "Governance failures create latent liability; greenwash detection amplifies to +21%"],
        ["Pandemic Disruption Wave", "🦠", "R5–R9", "6%", "30% workforce loss, OPEX +15%, burnout +20 (2 rounds)", "Tests operational resilience and pre-pandemic HR investment"],
        ["AI Disruption Wave", "🤖", "R6–R10", "10%", "Software Rev +20%, ops displacement 15%, burnout +10", "Rewards ethical AI overhaul; 'ai_monetised' flag adds +8% trigger probability"],
        ["Climate Litigation Ruling", "⚖️", "R7–R10", "5%", "−$8M, asset writedown 10%, Rep −10, Gov Risk +5", "High CI teams face +27% conditional probability (above CI 80)"],
        ["Critical Mineral Embargo", "🚫", "R4–R9", "7%", "Electronics/Pharma Rev −15%, OPEX +10% (2 rounds)", "Supply chain transparency investment reduces trigger probability"],
        ["Ransomware Attack", "💀", "R3–R10", "7%", "−$5M, Revenue −5%, Rep −8, Gov Risk +12", "Correlates with governance quality; low gov risk = better incident response"],
        ["Viral Consumer Boycott", "📱", "R4–R9", "5%", "Consumer Goods Rev −20%, Rep −12, SLO −10", "Low SLO or low reputation adds +15–27% conditional probability"],
    ]
)

add_heading(doc, "10.3  Region-Specific Black Swan Events", 2)
add_para(doc, (
    "Region-specific events are only triggered when a session's region is set in God Mode. "
    "They model geographic ESG risks relevant to specific markets and are used when "
    "the simulation is customised for regional cohorts (e.g., an Indian corporate programme "
    "would use South Asia events; a European MBA might use EU CBAM)."
))
add_table(doc,
    ["Event", "Icon", "Region", "Round Range", "Base Prob", "Key Impact", "Real-World Basis"],
    [
        ["ASEAN Trade Corridor Dispute", "🚢", "ASEAN", "R3–R8", "10%", "Treasury −8%, OPEX +12%, Revenue −6% (2 rounds)", "South China Sea territorial disputes; Malacca Strait disruption risk"],
        ["South Asia Extreme Monsoon", "🌧️", "South Asia", "R2–R7", "9%", "OPEX +10%, Revenue −8%, SLO −6, Burnout +12 (2 rounds)", "Bangladesh/Pakistan/India monsoon disruption to industrial zones"],
        ["EU Carbon Border Adjustment (CBAM)", "🌿", "Europe", "R4–R9", "11%", "−$4M, OPEX +8%, Rep −6, Gov Risk +5", "EU CBAM now live in transition phase since Oct 2023"],
        ["SEC Climate Disclosure Enforcement", "📋", "North America", "R5–R9", "8%", "−$6M, Rep −10, Gov Risk +10, SLO −5", "SEC climate disclosure rule; greenwash detection adds +12% probability"],
        ["African Resource Nationalisation", "⛏️", "Africa", "R3–R9", "7%", "Treasury −10%, Revenue −7%, Rep −8, SLO −10 (2 rounds)", "DRC cobalt; Zambia copper; South Africa mining charter risk"],
    ]
)

add_heading(doc, "10.4  Conditional Probability Modifiers", 2)
add_para(doc, (
    "Many Black Swan events have conditional modifiers that increase their probability "
    "based on the team's current state. This creates compounding risk: bad decisions "
    "don't just have their immediate impact — they also make future crises more likely."
))
add_bullet(doc, "Whistleblower Scandal: +12% if avg governance risk > 50; +15% if 'greenwashing_detected' flag is active.")
add_bullet(doc, "Climate Litigation: +12% if avg CI > 60; additional +15% if avg CI > 80. High-carbon teams face up to 32% effective probability.")
add_bullet(doc, "AI Disruption Wave: −5% if 'ethical_ai_overhaul' flag is set (investment reduces disruption vulnerability); +8% if 'ai_monetised' flag is set.")
add_bullet(doc, "Consumer Boycott: +15% if avg SLO < 40; +12% if group reputation < 35.")
add_bullet(doc, "CBAM (Europe): +10% if avg CI > 50.")

divider(doc)

# ════════════════════════════════════════════════════════════════
# SECTION 11: FLAG DEPENDENCY GRAPH
# ════════════════════════════════════════════════════════════════

add_heading(doc, "11.  Flag Dependency Graph", 1)

add_para(doc, (
    "The Flag Dependency Graph is the simulation's causal memory. "
    "Flags are boolean state markers set by decisions in one round that "
    "carry forward to affect the game in future rounds, sometimes many rounds later. "
    "This creates a non-Markovian game — history matters. "
    "The graph is the primary mechanism that makes early decisions consequential."
))
add_para(doc, (
    "Understanding the flag dependency graph is essential for facilitators "
    "who want to guide debriefs, and for developers extending the simulation. "
    "Every flag either enables or blocks future benefits, or increases or decreases future risks."
))

add_table(doc,
    ["Source Round", "Flag Set By", "Target Round", "Effect", "Category"],
    [
        ["R1", "electronics_blindspot (Options A or C)", "R4", "Doubles R4 crisis severity from 40 → 80. Massive contagion damage.", "risk"],
        ["R1", "deep_audit_completed (Option B)", "R4", "Halves R4 crisis severity: 80 → 40. Significant risk mitigation.", "governance"],
        ["R2", "materiality_aligned (Option A)", "R10", "+0.10 M_R Materiality Governance bonus. Only path to this bonus.", "governance"],
        ["R2", "blockchain_traceability (Pillar: Supply Chain)", "R8", "Prevents supply chain scandal triggering in Black Swan events.", "supply_chain"],
        ["R3", "early_decarboniser (Option A or Pillar: Rapid Switch)", "R7", "+0.10 synergy multiplier bonus in R7. Rewards early movers.", "climate"],
        ["R3", "greenwash_risk (Pillar: Marketing-Only Pledge)", "R5", "Activates Greenwashing Engine if investment ratio < 15%: −15 reputation.", "risk"],
        ["R5", "insurance_only (Option C or Pillar equivalent)", "R10", "Permanently BLOCKS the +0.20 Resilience Champion M_R bonus.", "climate"],
        ["R5", "planet_expendable (Shadow Board: reject Planet director)", "R10 (all)", "−0.20 M_R penalty. Amplified in Climate Black Swan pathway.", "governance"],
        ["R5", "shareholder_alienated (Shadow Board: reject Shareholder director)", "R10 (HT)", "−0.20 M_R in Hostile Takeover pathway. Weakens institutional support.", "governance"],
        ["R5", "governance_fragility (Shadow Board: reject Governance director)", "R10 (RS) + BRSR-R5", "−0.25 M_R in Regulatory Shutdown pathway. Also triggers BRSR whistleblower leak.", "governance"],
        ["R6", "ethical_ai_overhaul (Option B)", "R10", "+0.15 Truth Premium M_R. Only path to this bonus.", "governance"],
        ["R6", "ai_monetised (Option A)", "R7", "EU AI Act compliance costs applied as OPEX drag from R7 onward.", "risk"],
        ["R7", "synergy_unlock (Option C)", "R10", "+0.15 Synergy Strategic Premium M_R. Also requires synergy ≥ 0.80.", "strategic"],
        ["R8", "electronics_water_priority (Option B)", "R10", "Permanently BLOCKS the +0.20 Resilience Champion M_R bonus.", "risk"],
        ["R9", "community_fund (Option C)", "R10", "+0.18 M_R Community Champion bonus, amplified by JT scaling (up to ×1.5).", "social"],
        ["R9", "managed_transition (Option B)", "R10", "+0.12 M_R Just Transition bonus, amplified by JT scaling.", "social"],
        ["BRSR-R1", "brsr_pioneer (Option A)", "R10", "Enables BRSR Pioneer archetype path with enhanced narrative.", "governance"],
        ["BRSR-R1", "governance_fragility (Option C)", "BRSR-R5", "Triggers whistleblower governance leak in BRSR-R5: −$2.5M treasury.", "governance"],
        ["BRSR-R4", "brsr_greenwash_risk (Option C)", "BRSR-R4", "SEBI show-cause notice: −12 reputation immediately in BRSR-R4.", "risk"],
        ["BRSR-R5", "brsr_net_positive_dividend (BRSR score ≥ 80)", "R10", "+0.05 M_R ESG Alpha Dividend. BRSR Pioneer path exclusive.", "governance"],
    ]
)

add_callout(doc, (
    "The most impactful flag chain is R1 electronics_blindspot → R4 severity doubling. "
    "Teams that do not grasp this connection in Round 1 face a reputation crisis in Round 4 "
    "that often takes two to three further rounds to recover from, permanently discounting "
    "their Social Licence trajectory and risking the −0.40 Instability Discount at terminal valuation."
), "⚠️ Most Impactful Flag Chain")

divider(doc)

# ════════════════════════════════════════════════════════════════
# SECTION 12: CORE ENGINE MODULES
# ════════════════════════════════════════════════════════════════

add_heading(doc, "12.  Core Engine Modules", 1)

add_para(doc, (
    "The simulation's process_tick() function orchestrates 30+ engine modules in sequence "
    "every round. Each module is a pure function that takes state as input and returns "
    "deltas or new state values. This architecture makes modules independently testable "
    "and allows new mechanics to be added without disrupting existing calculations."
))

add_heading(doc, "12.1  Module Inventory", 2)
add_table(doc,
    ["#", "Module", "File", "Core Formula / Mechanic", "Design Rationale"],
    [
        ["1", "Carbon Accounting", "engine.py", "tCO₂e = CI × rev / 1M; Revenue-weighted avg CI = Σ(CI×rev)/Σrev", "GHG Protocol intensity method; revenue-weighting prevents gaming through revenue reduction"],
        ["2", "Corporate Strategic Fund (CSF)", "engine.py", "CSF = Σ(Rev − OPEX) − Dividends_Paid", "Primary cash flow measure; can be negative; no rounding between subtraction steps"],
        ["3", "Contagion Engine", "engine.py", "Rep = Avg_Rep − 50 × sigmoid((severity − 30) / 15)", "S-curve prevents linear extrapolation; models real media contagion dynamics"],
        ["4", "Synergy Engine", "engine.py", "New_OPEX = Old_OPEX × (1 − sqrt(ratio) × 0.7 × Synergy_Mult)", "Diminishing returns on cross-BU investment; prevents trivial OPEX elimination"],
        ["5", "Natural Capital Cost of Debt", "engine.py", "rate = base_rate + NCD × 0.0001 (calibrated: NCD=500 → ~10%, NCD=1000 → ~15%)", "Links ecological debt to financial cost of capital; makes NCD tangible"],
        ["6", "VRIO Decay", "engine.py", "VRIO decays 2%/round without reinvestment", "Competitive advantages erode without maintenance; models strategic drift"],
        ["7", "Burnout Accumulation", "engine.py", "Natural drift +6/round; penalty = (burnout−20)²/10000 × opex (quadratic)", "Quadratic curve ensures non-linear OPEX damage at high burnout levels"],
        ["8", "Workforce Readiness", "engine.py", "High HR: +16; Medium: +8; None: −10/round. Range 0–100", "Skills atrophy model; low readiness (<40) flags penalty; high (>75) flags bonus"],
        ["9", "Talent Brain-Drain", "engine.py", "Attrition probability from burnout + low readiness combination", "Models real-world great resignation; high burnout accelerates skill loss"],
        ["10", "Strike Probability", "engine.py", "P(strike) = f(SLO, burnout, crisis_count, regulatory rules)", "Multi-factor strike model; revenue zeroing if strike occurs"],
        ["11", "Natural Decay", "engine.py", "Scores decay toward baseline each round without active investment", "Prevents static gaming; forces continuous investment to maintain KPIs"],
        ["12", "Macroeconomic Inflation", "engine.py", "OPEX inflation per macro cycle phase", "Models cost-push inflation; OPEX grows without active efficiency investment"],
        ["13", "Execution Overrun Risk", "engine.py", "Capital over-commitment adds OPEX overshoot drag", "Models project management risk; over-investing creates its own costs"],
        ["14", "Technical Debt", "engine.py", "Deferred IT/ops investment accumulates as compounding OPEX cost", "Models real-world technical debt accumulation in large organisations"],
        ["15", "Revenue Cannibalization", "engine.py", "If BU revenue > 15% above group avg: cannibalize overlapping BUs by _MARKET_OVERLAP matrix", "Models conglomerate market overlap; prevents domination by single BU"],
        ["16", "Stakeholder Fatigue", "engine.py", "Recovery efficiency = 1 / (1 + 0.3 × crisis_count_lifetime)", "Diminishing returns on stakeholder recovery; models trust erosion over time"],
        ["17", "Supply Chain Contagion", "engine.py", "SC disruption propagates revenue and OPEX shocks across connected BUs", "Models supply chain interdependencies; Electronics disruption ripples to Pharma"],
        ["18", "Competitor Pressure", "engine.py", "Market share erosion when peers decarbonise faster", "Competitive context; inaction has relative cost even if absolute metrics stable"],
        ["19", "Cash Conversion", "engine.py", "Liquidity ratio = cash / assets; covenant trigger below CONSTRAINT_MIN_LIQUIDITY_RATIO", "Balance sheet solvency constraint; links treasury management to covenant compliance"],
        ["20", "Dividend Ratchet", "engine.py", "Dividend expectations grow ratchet-like with historical profitability", "Models dividend signalling constraint; cutting dividends has SLO and reputation cost"],
        ["21", "Talent Allocation Pressure", "engine.py", "Cross-BU talent competition reduces marginal returns from R3 onward", "Models finite talent pool; over-extending across BUs creates quality degradation"],
        ["22", "Technology Lock-In", "engine.py", "Early technology choices create switching costs in subsequent rounds", "Path dependency; models vendor lock-in and legacy system risk"],
        ["23", "ESG Greenwashing Risk", "engine.py", "Green option + investment_ratio < 0.15 → scandal: Rep −15, auditor hostile", "Checks credibility of ESG claims against investment backing"],
        ["24", "Macro Interest Rate", "engine.py", "4-phase WACC modifier (see Section 9.4)", "Links macroeconomic environment to cost of capital"],
        ["25", "Biodiversity Engine", "biodiversity_engine.py", "Tracks biodiversity net gain/loss from NCD and nature investments", "TNFD alignment; nature-positive vs nature-negative pathways"],
        ["26", "Balance Sheet Engine", "balance_sheet.py", "IAS 1 format; assets = liabilities + equity; liquidity covenant check", "Financial statement discipline; prevents treasury gaming without balance sheet reality check"],
        ["27", "Systemic Risk Engine", "systemic_risk_engine.py", "Emissions cap breach monitoring; systemic risk scoring", "Group-level emissions cap (CONSTRAINT_MAX_CARBON_EMISSIONS = 5,000 tCO₂e)"],
        ["28", "Terminal Valuation", "terminal_valuation.py", "TV = EBITDA × Exit × M_R × M_SDG; Equity Bridge; Archetypes", "Full ESG-financial integration at Round 10 (see Section 8)"],
        ["29", "Regulatory Sandbox", "regulatory_sandbox.py", "CSRD/ESRS gate logic; BRSR filing requirements; SEC disclosure checks", "Simulates regulatory compliance overhead for ESG reporting regimes"],
        ["30", "Black Swan Registry", "black_swan_registry.py", "Stochastic fat-tail events evaluated each round (see Section 10)", "Taleb fat-tail model; tests resilience beyond optimisation"],
    ]
)

divider(doc)

# ════════════════════════════════════════════════════════════════
# SECTION 13: SIMULATION CONFIG
# ════════════════════════════════════════════════════════════════

add_heading(doc, "13.  Simulation Config & Tuneable Parameters", 1)

add_para(doc, (
    "All tuneable simulation parameters are defined in simulation_config.json "
    "and loaded as typed constants by backend/config.py. "
    "This architecture separates game mechanics from game calibration — "
    "the same engine code runs correctly regardless of parameter values, "
    "and facilitators with God Mode access can adjust the parameters "
    "without touching code."
))
add_callout(doc, "Rule: Never hardcode any value from the table below directly in engine logic. Always import the constant from config.py.", "⛔ Engineering Rule")

add_table(doc,
    ["JSON Path", "Config Constant", "Default", "Description", "Calibration Rationale"],
    [
        ["simulation_settings.rounds", "SIM_ROUNDS", "10", "Total main simulation rounds", "10 rounds × 6 months = 5 years; spans a typical strategic planning horizon"],
        ["simulation_settings.agents", "SIM_AGENTS", "5", "Number of BU profiles available", "Default 4 active; 5th is a reserve slot for advanced configurations"],
        ["simulation_settings.initial_budget", "SIM_INITIAL_BUDGET", "$50,000,000", "Starting Corporate Strategic Fund", "Calibrated so early rounds require genuine trade-offs; not so tight as to force constant survival mode"],
        ["economic_parameters.carbon_price_base", "ECONOMIC_CARBON_PRICE_BASE", "$40.00", "Base carbon price (USD/tCO₂e)", "Approximate EU ETS spot price at calibration; real markets ranged $40–120 in 2022–2024"],
        ["economic_parameters.carbon_price_growth_rate", "ECONOMIC_CARBON_PRICE_GROWTH", "0.15 (15%)", "Annual carbon price escalation", "NGFS Orderly Transition scenario carbon price growth trajectory"],
        ["economic_parameters.circular_economy_efficiency_bonus", "ECONOMIC_CIRCULAR_ECONOMY_BONUS", "0.15 (15%)", "OPEX reduction from circular economy choices", "McKinsey/Ellen MacArthur Foundation circular economy efficiency estimates"],
        ["constraints.max_carbon_emissions", "CONSTRAINT_MAX_CARBON_EMISSIONS", "5,000 tCO₂e", "Group-wide absolute emissions cap", "Regulatory compliance threshold; breach triggers systemic risk engine penalty"],
        ["constraints.min_liquidity_ratio", "CONSTRAINT_MIN_LIQUIDITY_RATIO", "0.20 (20%)", "Minimum cash / total assets ratio before covenant breach", "Standard financial covenant ratio in corporate lending; below triggers lender scrutiny"],
    ]
)

add_heading(doc, "13.1  Terminal Valuation Constants (Non-Configurable)", 2)
add_table(doc,
    ["Constant", "Value", "Purpose"],
    [
        ["SHARES_OUTSTANDING", "100,000,000", "Fixed IPO share count for price per share calculation"],
        ["IPO_PRICE_PER_SHARE", "$50.00", "Opening share price; used to calculate % gain/loss vs. start"],
        ["_LONG_RUN_GROWTH", "2%", "Terminal growth rate in Gordon Growth Model for dynamic exit multiple"],
        ["_EXIT_MULTIPLE_FLOOR", "6.0×", "Minimum exit multiple (distressed/regulatory scenarios)"],
        ["_EXIT_MULTIPLE_CEILING", "18.0×", "Maximum exit multiple (very low WACC + high growth)"],
        ["EV_Revenue_Benchmark", "2.5×", "Sector median EV/Revenue for peer comparison signal"],
        ["Price_Book_Benchmark", "1.5×", "Sector median Price/Book for peer comparison signal"],
    ]
)

divider(doc)

# ════════════════════════════════════════════════════════════════
# SECTION 14: INDUSTRY VERTICALS
# ════════════════════════════════════════════════════════════════

add_heading(doc, "14.  Industry Verticals (BU Substitutions)", 1)

add_para(doc, (
    "Industry verticals allow facilitators to customise the BU composition "
    "to match the specific sector context of their cohort. "
    "A session designed for oil & gas executives would substitute the Pharma slot "
    "with Oil & Gas; a fintech-focused programme would replace Software with "
    "Banking & Financial Services."
))
add_para(doc, (
    "Slot-fit restrictions enforce pedagogical coherence: "
    "only verticals that share fundamental industry characteristics "
    "(heavy vs. light, physical vs. digital, regulated vs. market-driven) "
    "can replace each other. This prevents nonsensical substitutions "
    "(e.g., replacing Software with Oil & Gas would create an implausible conglomerate)."
))

add_heading(doc, "14.1  Available Verticals", 2)
add_table(doc,
    ["Vertical", "Icon", "Replaces Slot", "Revenue", "OPEX", "Carbon Intensity", "Water Dep.", "NCD", "Gov Risk", "Key ESG Challenge"],
    [
        ["Oil & Gas", "🛢️", "Pharma OR Electronics", "$22M", "$15M", "95", "70", "350", "20", "Extreme carbon intensity; stranded asset risk; TCFD physical risk; NCD 350 is highest"],
        ["Banking & Financial Services", "🏦", "Software", "$14M", "$8M", "8", "5", "15", "30", "Financed emissions (Scope 3 Category 15); systemic risk; governance complexity; ESG-linked lending"],
        ["Retail / FMCG", "🛍️", "Consumer Goods", "$12M", "$9M", "42", "55", "160", "12", "Packaging waste; last-mile logistics; labour-intensive supply chains; consumer boycott exposure"],
        ["Agriculture", "🌾", "Consumer Goods", "$9M", "$6.5M", "55", "90", "280", "15", "Extreme water dependency (90); biodiversity impact; land-use emissions; deforestation risk"],
        ["Technology (AI/Cloud)", "🧠", "Software", "$15M", "$9M", "15", "10", "40", "28", "Data centre energy growth; AI governance (EU AI Act); talent brain-drain; compute carbon footprint"],
    ]
)

add_heading(doc, "14.2  Slot-Fit Rules", 2)
add_table(doc,
    ["Default Slot", "Compatible Verticals", "Shared Characteristics"],
    [
        ["Pharma", "Oil & Gas", "Heavy industry, physical assets, high regulatory scrutiny, environmental liability"],
        ["Electronics", "Oil & Gas", "High carbon intensity, complex global supply chains, commodity price exposure"],
        ["Consumer Goods", "Retail/FMCG, Agriculture", "Supply chain intensity, natural resource consumption, packaging/waste, consumer brand risk"],
        ["Software", "Banking & Financial Services, Technology", "Asset-light, governance-heavy, talent-dependent, digital risk exposure"],
    ]
)

add_heading(doc, "14.3  Vertical-Specific Blindspot Flags", 2)
add_para(doc, (
    "Each vertical has its own equivalent of the 'electronics_blindspot' flag — "
    "a Round 1 audit risk that surfaces as a crisis multiplier in a later round. "
    "Facilitators running vertical sessions should be aware that the blindspot "
    "narrative changes accordingly."
))
add_table(doc,
    ["BU / Vertical", "Blindspot Flag", "Crisis It Amplifies"],
    [
        ["Electronics (default)", "electronics_blindspot", "R4 Labour Supply Chain Scandal — crisis severity doubles"],
        ["Oil & Gas", "refinery_blindspot", "R4/R6 Environmental compliance failures — regulator investigation probability spikes"],
        ["Banking & Financial Services", "governance_blindspot", "R5/R6 Governance failures — SEC/FCA regulatory enforcement event probability increases"],
        ["Retail / FMCG", "supply_chain_blindspot", "R3/R4 Supply chain labour violations — similar to electronics scenario"],
        ["Agriculture", "land_use_blindspot", "R5/R7 Biodiversity and land-use violations — NGO/investor campaign risk"],
        ["Technology (AI/Cloud)", "data_centre_blindspot", "R6 AI bias / data centre emissions scandal — governance and CI penalty"],
    ]
)

add_heading(doc, "14.4  Market Overlap Matrix (Revenue Cannibalization)", 2)
add_para(doc, (
    "When verticals are introduced, their market overlaps with other BUs are "
    "defined in the VERTICAL_MARKET_OVERLAP matrix. "
    "This feeds the Revenue Cannibalization Engine — BUs that share market space "
    "reduce each other's revenue when one grows aggressively."
))
add_table(doc,
    ["BU Pair", "Overlap Score", "Reason"],
    [
        ["Technology ↔ Software", "0.75", "Direct substitution in enterprise SaaS and cloud platforms"],
        ["Retail/FMCG ↔ Consumer Goods", "0.70", "Direct product category overlap"],
        ["Banking ↔ Technology", "0.55", "Fintech convergence; digital payments overlap"],
        ["Banking ↔ Software", "0.50", "Enterprise software procurement for financial services"],
        ["Retail/FMCG ↔ Agriculture", "0.50", "Food supply chain vertical integration"],
        ["Agriculture ↔ Consumer Goods", "0.45", "Food & beverage input to consumer products"],
        ["Technology ↔ Electronics", "0.40", "Hardware/semiconductor convergence"],
        ["Oil & Gas ↔ Agriculture", "0.30", "Energy inputs, fertiliser feedstock"],
    ]
)

divider(doc)

# ════════════════════════════════════════════════════════════════
# SECTION 15: ROLE HIERARCHY
# ════════════════════════════════════════════════════════════════

add_heading(doc, "15.  Role Hierarchy: God Mode → Facilitator → Player", 1)

add_para(doc, (
    "The simulation operates a three-tier control hierarchy. "
    "Each tier has distinct capabilities and access levels. "
    "This structure allows the simulation to be deployed across a wide range of contexts — "
    "from self-guided online learning to high-stakes executive facilitation — "
    "while maintaining consistency in game mechanics."
))

add_heading(doc, "15.1  God Mode (Platform Administrator)", 2)
add_para(doc, (
    "God Mode is the highest authority tier. "
    "It is accessed by platform administrators who manage the simulation infrastructure "
    "and configure the parameters available to facilitators. "
    "God Mode decisions affect all sessions globally or per-facilitator allocation."
))
add_para(doc, "God Mode capabilities:", bold=True)
add_bullet(doc, "Enable or disable specific side tracks globally and on a per-facilitator basis.")
add_bullet(doc, "Set the global difficulty tier (Easy / Standard / Expert) with different tier defaults per facilitator if required.")
add_bullet(doc, "Force-inject specific Black Swan events by event ID — bypassing stochastic rolls for pedagogical purposes.")
add_bullet(doc, "Set the ending pathway to a specific ID or 'random'.")
add_bullet(doc, "Set the geographic region (ASEAN, South Asia, Europe, North America, Africa) to enable region-specific Black Swan events.")
add_bullet(doc, "Manage player authentication credentials, session passcodes, and RBAC (Role-Based Access Control) assignments.")
add_bullet(doc, "Access the Global Benchmark Report — cross-session performance data showing distribution of M_R scores, archetype frequencies, and optimal strategy statistics across all sessions.")
add_bullet(doc, "Override the decision_overrides.json file to modify specific round option impacts for A/B testing of mechanic changes.")
add_bullet(doc, "Access full admin analytics and real-time session monitoring across all active facilitator sessions.")

add_heading(doc, "15.2  Facilitator", 2)
add_para(doc, (
    "The Facilitator is the primary operator of individual sessions. "
    "Facilitators design and run sessions for their specific cohort — "
    "an MBA class, a corporate leadership team, or a professional development programme. "
    "Their role is to configure the simulation context and guide the debrief."
))
add_para(doc, "Facilitator capabilities:", bold=True)
add_bullet(doc, "Create sessions for their cohort with unique passcodes. Session configuration includes: team size, BU composition (default or vertical substitutions), difficulty tier, ending pathway, region, and assigned side tracks.")
add_bullet(doc, "Assign which side tracks are available to players during the session and set the earliest round they can be triggered.")
add_bullet(doc, "View the Teleprompter — a facilitated script system (admin_teleprompter.py) that provides round-by-round prompts, pedagogical talking points, common player mistakes, and suggested debrief questions.")
add_bullet(doc, "Access the Admin Analytics Dashboard — real-time monitoring of all teams' KPI trajectories, flag states, treasury levels, and decision histories within their session.")
add_bullet(doc, "Override specific round decisions using decision_overrides.json for their session — useful when demonstrating alternative scenarios in debrief.")
add_bullet(doc, "View the Shadow Board audit results — which directors each team agreed with or rejected in Round 5, and the resulting penalty flags.")
add_bullet(doc, "Export session results as the Global Benchmark Report format — comparing their cohort's M_R scores, archetypes, and KPI trajectories against historical benchmarks.")
add_bullet(doc, "Pause and resume side tracks manually — useful for synchronising team progress during live facilitation.")

add_heading(doc, "15.3  Player (Team)", 2)
add_para(doc, (
    "Players are the teams participating in the simulation. "
    "Each team represents the Board of Directors / Sustainability Leadership of Muressons Global. "
    "Teams interact with the simulation through the Next.js frontend, making decisions "
    "each round and receiving feedback through KPI dashboards, event narratives, "
    "and post-round analytics."
))
add_para(doc, "Player experience per round:", bold=True)
add_bullet(doc, "Pre-round: Receive the round briefing — a narrative context document describing the crisis scenario. This includes real-world data references, regulatory context, and stakeholder signals.")
add_bullet(doc, "Decision Phase: Submit the ABC crisis decision and five pillar decisions. Each option includes cost information, impact previews, and optional warning badges.")
add_bullet(doc, "Post-round: View the KPI dashboard update, event narratives (including any Black Swan events triggered and foreshadowing items), and the post-round analytics breakdown (showing all individual engine module contributions to KPI changes).")
add_bullet(doc, "Foreshadowing: From Round 5 onward, receive foreshadowing news items based on the active ending pathway. These are displayed as 'market intelligence' or 'news releases' in the player dashboard.")
add_bullet(doc, "Side Tracks: When activated, the main simulation pauses and the team is presented with the side track scenario. They play through all side track rounds before returning to the main simulation.")
add_bullet(doc, "Terminal Valuation: After Round 10, see the full terminal valuation breakdown: EBITDA, carbon cost, exit multiple, M_R with all components explained, M_SDG, enterprise value, equity bridge, price per share vs. IPO, market multiples, and their company archetype.")

add_heading(doc, "15.4  Facilitation Workflow for Live Sessions", 2)
add_para(doc, "Recommended facilitation sequence for a full-day executive session:", bold=True)
add_bullet(doc, "Pre-session (30 min): Brief players using the Muressons Player Briefing (PPTX). Establish team roles, introduce the scoring system, and explain that early decisions have long-run consequences.")
add_bullet(doc, "Rounds 1–3 (90 min): 'Foundation Phase'. Allow teams 15–20 minutes per round. Focus debrief on audit depth vs. cost trade-off, double materiality governance, and Scope 3 complexity.")
add_bullet(doc, "Rounds 4–6 (90 min): 'Crisis Response Phase'. Debrief after Round 4 on the electronics_blindspot impact — this is typically the highest-engagement moment. Discuss contagion theory, AI ethics, and the Shadow Board in Round 5.")
add_bullet(doc, "Side Track Injection (30–45 min, if used): Facilitator triggers the side track between rounds. Teams complete the mini-simulation while the facilitator monitors through admin analytics.")
add_bullet(doc, "Rounds 7–9 (60 min): 'Transition Phase'. Discuss circular economy, water scarcity, and Just Transition. This is the most emotionally engaging section — workforce closures generate strong team debate.")
add_bullet(doc, "Round 10 + Terminal Valuation (30 min): The pathway crisis plays out. Teams receive their archetype and full valuation breakdown.")
add_bullet(doc, "Debrief (45–60 min): Use the Teleprompter debrief questions. Compare team archetypes, discuss flag dependency graph, and connect back to real-world examples.")

divider(doc)

# ════════════════════════════════════════════════════════════════
# APPENDIX A: KEY CODEBASE FILES
# ════════════════════════════════════════════════════════════════

add_heading(doc, "Appendix A: Key Codebase Files", 1)

add_table(doc,
    ["File", "Role", "Key Contents"],
    [
        ["backend/engine.py", "Core engine", "All 24+ engine formula functions; process_tick() orchestrator; GHG accounting helpers; contagion/synergy/burnout models"],
        ["backend/round_configs.py", "Round definitions", "10 main rounds × 3 options (A/B/C) with full impact dictionaries, flag sets, and special_rules"],
        ["backend/pillar_configs.py", "Pillar definitions", "10 rounds × 5 pillars × 3 options; cost/impacts/flags_set per option; 1,827 lines"],
        ["backend/ending_pathways.py", "Pathway configs", "5 pathway R10 configs; foreshadowing events dict; 4 pathway-specific M_R calculator functions"],
        ["backend/terminal_valuation.py", "Valuation engine", "calculate_mr(), calculate_terminal_value(), calculate_equity_bridge(), determine_archetype(), what_if_terminal(), normalize_mr_for_leaderboard()"],
        ["backend/black_swan_registry.py", "Black Swan events", "13 event definitions; evaluate_black_swans(); apply_black_swan_impacts(); difficulty scaling"],
        ["backend/bu_profiles.py", "BU profiles", "Default 4 BUs + 5 verticals; SLOT_FIT_MAP; VERTICAL_MARKET_OVERLAP matrix; build_bu_states()"],
        ["backend/round_logic.py", "Session orchestration", "Session-level process_tick() call; pre/post tick hooks; side track dispatcher; 137K bytes"],
        ["backend/router.py", "API routes", "FastAPI player-facing endpoints: submit_decision, submit_materiality, get_round_state, etc.; 246K bytes"],
        ["backend/admin_router.py", "Admin API", "God Mode and Facilitator API: session management, override controls, analytics, teleprompter; 366K bytes"],
        ["backend/admin_teleprompter.py", "Facilitation scripts", "Round-by-round facilitator scripts; debrief questions; pedagogical prompts; 121K bytes"],
        ["backend/admin_analytics.py", "Analytics engine", "Real-time session monitoring; KPI trajectory analysis; benchmark comparisons; 51K bytes"],
        ["backend/pillar_configs.py", "Pillar decisions", "Multi-toggle paradigm option definitions for all 10 rounds × 5 pillars"],
        ["backend/side_tracks/__init__.py", "Track registry", "Central side track registry and auto-registration of all 6 tracks"],
        ["backend/side_tracks/base_track.py", "Abstract base", "BaseSideTrack ABC; Data Bridge contract; engine hooks (pre_tick/post_tick)"],
        ["backend/side_tracks/corporate_sdg/", "SDG track", "CorporateSDGTrack; 5-round SDG configs; M_SDG integration; greenwash wiring"],
        ["backend/side_tracks/brsr_ngrbc/", "BRSR track", "BRSRNGRBCTrack; 10-round BRSR configs (62K bytes); score calculator; write-back"],
        ["backend/database.py", "Persistence", "SQLite session storage; game state serialisation/deserialisation; 46K bytes"],
        ["backend/config.py", "Configuration", "Typed constants from simulation_config.json; all tuneable parameters"],
        ["backend/biodiversity_engine.py", "Biodiversity", "TNFD-aligned biodiversity net gain/loss tracking; nature-positive scoring"],
        ["backend/balance_sheet.py", "Financial statements", "IAS 1 balance sheet engine; liquidity covenant enforcement; 42K bytes"],
        ["backend/systemic_risk_engine.py", "Systemic risk", "Group-level emissions cap monitoring; systemic risk score aggregation"],
        ["backend/regulatory_sandbox.py", "Regulatory gate", "CSRD/ESRS compliance checking; BRSR filing validation; SEC disclosure gates"],
        ["backend/pedagogical_engine.py", "Learning analytics", "Post-round pedagogical feedback generation; concept mapping; 35K bytes"],
        ["backend/materiality_db.py", "Materiality data", "Double materiality assessment database; ESRS topic mapping; 55K bytes"],
        ["backend/stakeholder_map.py", "Stakeholder data", "NPC stakeholder profiles; trust/sentiment models; 36K bytes"],
        ["simulation_config.json", "Config source", "Tuneable parameters (source of truth for all config constants)"],
        ["blueprint.md", "Architecture doc", "Module blueprint template; registered module registry (30 modules); validation checklist"],
        ["SIMULATION_CONTEXT.md", "Context summary", "This document's companion markdown; single-page quick reference"],
        ["frontend/app/", "Next.js frontend", "Player and admin UI; KPI dashboards; decision interface; archetype reveal"],
    ]
)

divider(doc)

# ════════════════════════════════════════════════════════════════
# APPENDIX B: OPTIMAL STRATEGY HEURISTICS
# ════════════════════════════════════════════════════════════════

add_heading(doc, "Appendix B: Optimal Strategy Heuristics", 1)

add_para(doc, (
    "The following represents the highest M_R path through the simulation "
    "for a standard session on the Activist Ultimatum pathway. "
    "This is provided for facilitators and developers — NOT for players. "
    "Players discovering the optimal path through gameplay is part of the learning design."
))

add_callout(doc, "This appendix should not be shared with participants before or during the simulation. Its purpose is to help facilitators understand what 'excellent performance' looks like and to support debrief discussions.", "🎓 Facilitator Only")

add_table(doc,
    ["Round", "Crisis Choice", "Key Pillar Choices", "Flags Earned", "M_R Impact"],
    [
        ["R1", "Option B (Deep Forensic Audit)", "Energy: Solar CapEx | Supply Chain: Full Audit | HR: DEI Program", "deep_audit_completed", "Prevents R4 crisis doubling; baseline CI reduced"],
        ["R2", "Option A (Full Materiality Alignment)", "Operations: Materiality Board | Supply Chain: Blockchain Traceability | HR: People Analytics", "materiality_aligned, blockchain_traceability", "+0.10 M_R; SC scandal prevention; governance risk −8"],
        ["R3", "Option A (Rapid Supplier Switch)", "Energy: Fleet Electrification | Offsetting: SBTi Commitment | HR: Green Skills Academy", "early_decarboniser, sbti_committed", "CI −15; synergy bonus at R7; NCD reduced"],
        ["R4", "Option A (Full Transparency & Remediation)", "Operations: Full Factory Transparency | Supply Chain: Full Remediation | Offsetting: Stakeholder Compensation Fund", "remediation_active, supplier_remediation", "Rep +10; SLO +8; damage contained"],
        ["R5", "Option B (Nature-Based Solutions)", "Operations: Nature-Based | Supply Chain: Geographic Diversification | Offsetting: Climate Adaptation Fund", "nature_based_resilience", "NCD −8; CI −6; Resilience M_R preserved; Shadow Board: agree with all directors"],
        ["R6", "Option B (Ethical AI Overhaul)", "Energy: Green Data Centres | Operations: Ethical AI Overhaul | HR: Upskilling & Reskilling", "ethical_ai_overhaul", "+0.15 Truth Premium M_R; SLO +15; CI −10"],
        ["R7", "Option C (Waste-to-Energy Partnership)", "Energy: H2/Long-Duration Storage | Operations: Circular Redesign | Supply Chain: Circularity Integration", "synergy_unlock, waste_to_energy", "+0.15 Synergy M_R; CI −6; NCD −4"],
        ["R8", "Option A (Water Efficiency for All)", "Operations: Water Efficiency Tech | Supply Chain: Nearshoring | Offsetting: Watershed Restoration", "water_efficiency_all", "Resilience M_R preserved (+0.20); SLO +5; water −20"],
        ["R9", "Option C (Community Investment Fund)", "Operations: Factory Repurposing | Offsetting: Just Transition Fund | HR: Comprehensive Retraining", "community_fund", "+0.18 M_R (× JT scaling up to +0.27); SLO +18; Rep +12"],
        ["R10", "Option A (Resist & Integrate)", "All pillars: highest investment options", "resist_integrate", "Synergy bonus applied; terminal valuation calculated"],
    ]
)

add_para(doc, "Theoretical Maximum M_R Calculation (without side tracks):", bold=True)
add_table(doc,
    ["Component", "Value"],
    [
        ["Base", "1.00"],
        ["Materiality Governance", "+0.10"],
        ["Synergy Strategic Premium", "+0.15"],
        ["Resilience Champion", "+0.20"],
        ["Truth Premium", "+0.15"],
        ["Community Champion (JT scaling 1.5×)", "+0.27"],
        ["Workforce Excellence (readiness ≥ 75)", "+0.10"],
        ["Wellbeing Champion (burnout < 20)", "+0.05"],
        ["BRSR ESG Alpha Dividend (if track played)", "+0.05"],
        ["Maximum M_R (with BRSR)", "≈ 2.07"],
        ["Instability Discount (if SLO < 75)", "−0.40"],
        ["Maximum achievable without Instability Discount", "≈ 2.07"],
    ]
)

add_para(doc, "SDG Multiplier boost (if Corporate SDG track, all Option A): M_SDG = 1.26 → Terminal Value boosted by 26%.", bold=True)
add_para(doc, "Combined maximum: TV = EBITDA × Exit × 2.07 × 1.26 ≈ EBITDA × Exit × 2.61", bold=True)
add_para(doc, "(Compared to base case: TV = EBITDA × Exit × 1.00 × 1.00). The ESG premium represents a 2.61× terminal value multiplier for the best possible ESG performance vs. the worst.", italic=True)


# ════════════════════════════════════════════════════════════════
# SECTION 16: RUNTIME DEPENDENCY MAP
# ════════════════════════════════════════════════════════════════

divider(doc)
add_heading(doc, "16.  Runtime Dependency Map", 1)

add_para(doc, (
    "This section documents the live runtime import graph — which Python modules the running "
    "server loads, how they depend on each other, and the rules that govern adding new code. "
    "The full, machine-readable version is in DEPENDENCY_MAP.md at the project root."
))

add_callout(doc,
    "Use this map when adding new features, refactoring imports, or deciding where new modules belong. "
    "Any file NOT listed in the tables below is a standalone script safe to move or archive without "
    "breaking the running application.",
    "📌 Developer Rule"
)

add_heading(doc, "16.1  Application Entry Point", 2)
add_para(doc, "backend/main.py — FastAPI startup sequence:", bold=True)
bullets_16 = [
    "Reads USE_MEMORY_DB env var — selects database.py (PostgreSQL) or database_memory.py (in-memory fallback).",
    "Injects the selected db module as sys.modules[\"database\"] so all routers share the same backend.",
    "Mounts 5 routers: simulation_router, admin_router, teleprompter_router, resources_router, analytics_router.",
    "Seeds missing facilitator cohorts on startup via admin_shared._facilitator_registry.",
]
for b in bullets_16:
    add_bullet(doc, b)

add_heading(doc, "16.2  Layer 1 — Routers", 2)
add_table(doc,
    ["Router File", "URL Prefix", "Responsibility"],
    [
        ["router.py", "/api/*", "All player-facing endpoints: tick, login, decisions, stakeholder map, CEO interview"],
        ["admin_router.py", "/api/admin/*", "Facilitator + God Mode admin endpoints; WebSocket broadcast manager"],
        ["admin_teleprompter.py", "/api/admin/teleprompter/*", "Live teleprompter and slide presentation endpoints"],
        ["admin_resources.py", "/api/admin/resources/*", "File upload/download, quiz bank management"],
        ["admin_analytics.py", "/api/admin/analytics/*", "Session analytics, real-time score aggregation"],
    ],
    header_color="059669"
)

add_heading(doc, "16.3  Layer 2 — Core Infrastructure", 2)
add_table(doc,
    ["Module", "Depends On", "Purpose"],
    [
        ["config.py", "stdlib, dotenv", "All env vars: DATABASE_URL, MASTER_PASSWORD, SIM_ROUNDS, carbon price, etc."],
        ["database.py", "config", "PostgreSQL async connection pool (asyncpg)"],
        ["database_memory.py", "config", "Thread-safe in-memory dict store; optional SQLite snapshot for offline use"],
        ["materiality_db.py", "stdlib", "JSON-backed materiality issue store — no DB connection required"],
        ["admin_shared.py", "config", "Shared in-process mutable state: _facilitator_registry, _god_mode_settings"],
        ["models.py", "pydantic", "Pydantic request/response models"],
        ["password_hashing.py", "bcrypt", "Password hash / verify / upgrade helpers"],
        ["auth_jwt.py", "jose, fastapi", "JWT token issue, verify, cookie management"],
        ["option_shuffle.py", "stdlib", "Deterministic option shuffling per player"],
    ]
)

add_heading(doc, "16.4  Layer 3 — Simulation Engine", 2)
add_table(doc,
    ["Module", "Key Local Imports", "Role"],
    [
        ["engine.py", "rng_util, config, stakeholder_sentiment, systemic_risk_engine, sdg_configs", "Core tick processor — advances game state each round"],
        ["round_logic.py", "round_configs, impact_engine, config, healthcare_configs, npc_stakeholders, pedagogical_engine, round_analytics, dynamic_cases, biodiversity_engine", "Pre/post tick; calls run_new_engines()"],
        ["impact_engine.py", "round_configs", "Computes ESG impact deltas per decision"],
        ["rng_util.py", "stdlib (hashlib)", "Deterministic per-cohort RNG seeding"],
        ["round_configs.py", "stdlib", "Loads per-round configuration; reads simulation_config.json"],
        ["pillar_configs.py", "stdlib", "ESG pillar option configuration"],
        ["healthcare_configs.py", "stdlib", "Healthcare vertical round options"],
    ]
)

add_heading(doc, "16.5  Layer 4 — Extended Engine Modules", 2)
add_para(doc, "All 39 modules below are actively imported by the core routers or engine. None are standalone scripts.", italic=True)
add_table(doc,
    ["Module", "Imported By", "Description"],
    [
        ["autonomous_agents.py", "router", "Autonomous NPC agent logic"],
        ["balance_sheet.py", "router", "IAS 1 balance sheet engine"],
        ["biodiversity_engine.py", "round_logic", "Biodiversity impact scoring"],
        ["black_swan_registry.py", "admin_router", "Fat-tail stochastic event registry + evaluator"],
        ["board_governance.py", "router", "Board governance decision layer"],
        ["branching_engine.py", "router", "Narrative branching logic"],
        ["brsr_controller.py", "admin_router", "BRSR/NGRBC track controller"],
        ["bu_profiles.py", "admin_router", "Business unit profile definitions"],
        ["ceo_diary.py", "router", "CEO diary narrative system"],
        ["ceo_interview.py", "router", "CEO interview dialogue engine"],
        ["consequence_dna_api.py", "router", "Consequence chain API"],
        ["dynamic_cases.py", "router, round_logic", "Dynamic case injection"],
        ["elevenlabs_tts.py", "router", "ElevenLabs TTS voice integration"],
        ["email_service.py", "admin_router", "Email dispatch (SMTP)"],
        ["ending_pathways.py", "router", "Game ending pathway logic"],
        ["journey_improvements.py", "admin_teleprompter", "Player journey improvement suggestions"],
        ["meadows_leverage.py", "router", "Meadows leverage point analysis"],
        ["npc_stakeholders.py", "round_logic", "NPC stakeholder behaviour"],
        ["org_politics.py", "router", "Organisational politics layer"],
        ["pedagogical_engine.py", "round_logic", "Pedagogical scaffolding logic"],
        ["real_world_parallels.py", "admin_teleprompter", "Real-world case parallel data"],
        ["regional_reporting.py", "admin_router", "Regional reporting aggregation"],
        ["regulatory_sandbox.py", "router", "Regulatory sandbox simulation (CSRD/ESRS gate)"],
        ["round_analytics.py", "round_logic", "Per-round analytics computation"],
        ["round_recap_engine.py", "admin_teleprompter", "Round recap generation for facilitators"],
        ["sdg_configs.py", "engine, router", "SDG configuration and linkage data"],
        ["sdg_linkage_engine.py", "router", "SDG linkage scoring engine"],
        ["shadow_board_audit.py", "router", "Shadow board audit layer"],
        ["stakeholder_db.py", "admin_router", "Stakeholder persistence helpers"],
        ["stakeholder_sentiment.py", "engine", "Stakeholder sentiment scoring"],
        ["supply_chain_network.py", "router", "Supply chain network model"],
        ["systemic_risk_engine.py", "engine", "Systemic risk calculation"],
        ["tcfd_scenarios.py", "router", "TCFD climate scenario data"],
        ["teachable_moments.py", "admin_analytics", "Teachable moments identification"],
        ["terminal_valuation.py", "consequence_dna_api, ending_pathways", "Terminal valuation model (M_R, M_SDG, archetypes)"],
        ["vertical_stakeholders.py", "admin_router", "Industry vertical stakeholder sets"],
        ["config_excel.py", "admin_router", "Excel-based session config reader"],
        ["materiality_config_excel.py", "admin_router", "Materiality config Excel reader"],
        ["stakeholder_config_excel.py", "admin_router", "Stakeholder config Excel reader"],
    ]
)

add_heading(doc, "16.6  Dependency Rules for New Development", 2)
dev_rules = [
    "New feature module → per-request: import it in router.py or admin_router.py.",
    "New feature module → per-tick: import it in round_logic.py or engine.py.",
    "Admin/facilitator-only feature: import in one of the admin_*.py modules.",
    "One-shot script (data migration, doc generator): place in scripts/ or temp_archive/ — do NOT import from any runtime module.",
    "Never import router.py or admin_router.py from within an engine module — this creates a circular dependency.",
    "Database access pattern: always use 'import database as db' (resolved by main.py injection). Never import database_memory directly in engine modules.",
    "Adding a new side track: create backend/side_tracks/<name>/track.py extending BaseSideTrack, then register in side_tracks/__init__.py.",
    "Adding a new vertical: add <name>.py with _STAKEHOLDERS, _SALIENCE_MIGRATIONS, _CSRD_ISSUES; export from verticals/__init__.py; reference in vertical_stakeholders.py.",
]
for r in dev_rules:
    add_bullet(doc, r)

divider(doc)

# ════════════════════════════════════════════════════════════════
# SECTION 17: CODEBASE PROVENANCE & REFACTOR LOG
# ════════════════════════════════════════════════════════════════

add_heading(doc, "17.  Codebase Provenance & Refactor Log", 1)

add_heading(doc, "17.1  Infrastructure & Architecture History", 2)
add_table(doc,
    ["Date", "Change"],
    [
        ["2026-05", "Initial production deployment; PostgreSQL + in-memory fallback (SEC-2 durability guard)"],
        ["2026-05", "JWT authentication hardening (SEC-6); CORS explicit origins whitelist (AUDIT-011)"],
        ["2026-05", "HTTP security headers middleware (HIGH-010); generic error handler (LOW-009)"],
        ["2026-05", "Admin router split into four sub-routers: admin_router, teleprompter, resources, analytics (ARCH-002)"],
        ["2026-05", "111 automated tests across 29 test files in backend/tests/ (pytest)"],
        ["2026-07-08", "Refactor-by-isolation: 139 non-runtime files archived to /temp_archive/; DEPENDENCY_MAP.md written"],
    ],
    header_color="1D4ED8"
)

add_heading(doc, "17.2  2026-07-08 Refactor-by-Isolation", 2)
add_para(doc, (
    "A full static dependency trace was performed from backend/main.py using import-chain analysis across "
    "all Python files. 139 files were identified as non-runtime (one-shot scripts, versioned document "
    "duplicates, ad-hoc test scripts, output artifacts) and moved to /temp_archive/ in the project root. "
    "The running application was not affected — zero runtime dependencies were touched."
))

add_para(doc, "Files protected (never moved):", bold=True)
protected = [
    "All 46 core runtime Python modules (traced via full import-chain from main.py)",
    "backend/tests/ — 29-file organized pytest suite",
    "backend/side_tracks/ and backend/verticals/ — runtime plugin sub-packages",
    "frontend/ — entire Next.js application",
    "All Docker, .env, and infrastructure files",
    "sessions.json — live session state for memory-DB mode",
    "backend/market_dynamics.py — kept for future development",
]
for p in protected:
    add_bullet(doc, p)

add_para(doc, "Archive breakdown:", bold=True)
add_table(doc,
    ["Category", "Description", "Files Archived"],
    [
        ["A", "Root-level one-shot document generators", "38"],
        ["B", "Root-level ad-hoc test scripts", "8"],
        ["C", "Root-level output artifacts (.txt, .json, .html)", "5"],
        ["D", "Backend one-shot patch/audit/verify scripts + vertical_csrd_issues.py", "32"],
        ["F", "Superseded versioned .docx duplicates (Facilitator Manual v2–v9, Student Manual v2–v8, Briefings v1–v10)", "35"],
        ["G", "docs/ directory generators + duplicate .docx files", "14"],
        ["H", "scripts/ directory one-shot utilities", "7"],
        ["TOTAL", "", "139"],
    ]
)

add_para(doc, "Safety documents created:", bold=True)
safety_docs = [
    "SAFETY_MANIFEST.txt — logs every moved file: original path, archive destination, rationale (729 lines, 31 KB).",
    "revert.py — restored the 139 files from the operator-local /temp_archive/; removed 2026-09-02 (audit F-38) once the refactor had shipped.",
    "DEPENDENCY_MAP.md — full layer-by-layer import-chain reference for ongoing development (18 KB, 411 lines).",
]
for s in safety_docs:
    add_bullet(doc, s)

add_para(doc, "Latest document versions retained at project root:", bold=True)
retained = [
    "Facilitator Manual: Muressons_Facilitator_Manual_v10.docx",
    "Student Manual: Muressons_Student_Manual_v9.docx",
    "Simulation Briefings: Muressons_Simulation_Briefings ver 11.docx + ver 11_with_CEO_Debrief.docx",
    "Technical Glossary: Muressons_Technical_Glossary_with_CAROIC.docx",
    "Benchmark Report: Muressons_Global_Benchmark_Report_v3.docx",
    "Simulation Context: Muressons_Simulation_Context_Full.docx (this document)",
]
for r in retained:
    add_bullet(doc, r)

divider(doc)

# ── FINAL PAGE ───────────────────────────────────────────────────

doc.add_page_break()
footer_p = doc.add_paragraph()
footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
footer_run = footer_p.add_run(
    "Muressons Global Corporation — Simulation Context Summary | Version 2026-07\n"
    "Maintained by the Muressons Simulation Engineering Team\n"
    "Reference files: round_configs.py · pillar_configs.py · ending_pathways.py · terminal_valuation.py"
    " · black_swan_registry.py · bu_profiles.py · side_tracks/ · DEPENDENCY_MAP.md"
)
footer_run.font.size = Pt(9)
footer_run.font.italic = True
footer_run.font.color.rgb = RGBColor(0x78, 0x71, 0x6C)

# ── SAVE ─────────────────────────────────────────────────────────

output_path = "Muressons_Simulation_Context_Full.docx"
doc.save(output_path)
print("[OK] Saved: " + output_path)
word_count = sum(len(p.text.split()) for p in doc.paragraphs)
print("[INFO] Approximate word count: " + str(word_count))
