"""
gen_student_manual_v10.py
Generate Muressons Student Manual v10 — Updated 2026-07-08
Output: docs/Muressons_Student_Manual_v10.docx
"""

import os
from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

ROOT = os.path.dirname(os.path.abspath(__file__))
SCREENSHOTS = os.path.join(ROOT, "docs", "screenshots")
OUTPUT = os.path.join(ROOT, "docs", "Muressons_Student_Manual_v10.docx")


# ── Helpers ──────────────────────────────────────────────────────────────

def set_cell_bg(cell, hex_color):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def add_heading(doc, text, level=1):
    h = doc.add_heading(text, level=level)
    run = h.runs[0] if h.runs else h.add_run(text)
    colors = {1: (0x05, 0x96, 0x69), 2: (0x1D, 0x4E, 0xD8), 3: (0x78, 0x71, 0x6C)}
    c = colors.get(level, (0, 0, 0))
    run.font.color.rgb = RGBColor(*c)
    return h


def add_para(doc, text, bold=False, italic=False, size=10.5):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = bold
    run.italic = italic
    run.font.size = Pt(size)
    return p


def add_bullet(doc, text, bold_prefix=None):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.left_indent = Inches(0.3)
    if bold_prefix:
        r1 = p.add_run(bold_prefix + " ")
        r1.bold = True
        r1.font.size = Pt(10.5)
    run = p.add_run(text)
    run.font.size = Pt(10.5)
    return p


def add_callout(doc, text, label="ℹ️ Note", color=(0x05, 0x96, 0x69)):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.35)
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run(f"{label}  {text}")
    r.italic = True
    r.font.size = Pt(10)
    r.font.color.rgb = RGBColor(*color)


def add_table(doc, headers, rows, header_color="1D4ED8"):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    hdr = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr[i].text = h
        set_cell_bg(hdr[i], header_color)
        for run in hdr[i].paragraphs[0].runs:
            run.bold = True
            run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            run.font.size = Pt(9.5)
    for ri, row in enumerate(rows):
        cells = table.rows[ri + 1].cells
        for ci, val in enumerate(row):
            cells[ci].text = str(val)
            for run in cells[ci].paragraphs[0].runs:
                run.font.size = Pt(9.5)
            if ri % 2 == 0:
                set_cell_bg(cells[ci], "F0FDF4")
    doc.add_paragraph()
    return table


def add_screenshot(doc, filename, caption, width=6.0):
    path = os.path.join(SCREENSHOTS, filename)
    if not os.path.exists(path):
        add_callout(doc, f"[Screenshot not found: {filename}]", "⚠️")
        return
    try:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run()
        run.add_picture(path, width=Inches(width))
    except Exception as e:
        add_callout(doc, f"[Could not embed {filename}: {e}]", "⚠️")
        return
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = cap.add_run(f"Figure: {caption}")
    r.italic = True
    r.font.size = Pt(9)
    r.font.color.rgb = RGBColor(0x78, 0x71, 0x6C)
    doc.add_paragraph()


def divider(doc):
    doc.add_paragraph("─" * 100)


def add_formatted_math(doc, formula):
    import re
    # Pre-process fractions: convert \frac{A}{B} to (A) / (B)
    while r"\frac" in formula:
        match = re.search(r"\\frac\{([^{}]+)\}\{([^{}]+)\}", formula)
        if match:
            numerator, denominator = match.groups()
            formula = formula.replace(match.group(0), f"({numerator}) / ({denominator})")
        else:
            break
            
    # Clean up standard LaTeX constructs
    formula = re.sub(r"\\text\{([^{}]+)\}", r"\1", formula)
    formula = formula.replace(r"\times", " × ")
    formula = formula.replace(r"\sqrt", "√")
    formula = formula.replace(r"\max", "max")
    formula = formula.replace(r"\min", "min")
    formula = formula.replace(r"\left(", "(").replace(r"\right)", ")")
    formula = formula.replace(r"\%", "%")
    formula = formula.replace(r"\$", "$")
    formula = formula.replace(r"\\", "") # clean double backslashes
    formula = formula.strip("$ ") # clean leading/trailing dollar signs
    
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.4)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    
    # Tokenize the formula
    pattern = re.compile(
        r"(_\{[A-Za-z0-9_ ]+\}|_[A-Za-z0-9]+|[A-Za-z]+|[0-9]+(?:\.[0-9]+)?%?|[+\-*/=()<>,√\$×−]|\s+)"
    )
    tokens = pattern.findall(formula)
    
    variables = {
        "PPE", "CAPEX", "ROU", "Inventory", "Brand", "Base", "Reputation", "SLO", "IP", 
        "Goodwill", "Revenue", "OPEX", "Debt", "Equity", "Liabilities", "Assets", 
        "EBITDA", "Cash", "WACC", "Obligation", "Accretion", "Tax", "Profit", 
        "DSO", "DPO", "Risk", "Exposure", "NCD", "Final", "Opening", "final", "opening",
        "allocated", "avg", "min", "max", "total", "net", "gross", "decomm", "interest", 
        "rate", "charge", "provision", "remediation", "events", "shares", "outstanding"
    }
    
    for token in tokens:
        if not token:
            continue
        run = p.add_run()
        run.font.name = "Times New Roman"
        run.font.size = Pt(11)
        
        if token.startswith("_"):
            sub_text = token[2:-1] if token.startswith("_{") else token[1:]
            run.text = sub_text
            run.font.subscript = True
            if sub_text in variables or sub_text.lower() in variables:
                run.italic = True
        elif token in variables or token.lower() in variables:
            if token in ["min", "max", "avg"]:
                run.italic = False
                run.text = token
            else:
                run.italic = True
                run.text = token
        elif token == "*":
            run.text = " × "
        elif token == "-":
            run.text = " − "
        else:
            run.text = token
    return p


# ════════════════════════════════════════════════════════════════════════
# BUILD DOCUMENT
# ════════════════════════════════════════════════════════════════════════

doc = Document()
for section in doc.sections:
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(2.0)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.0)

# ── COVER PAGE ───────────────────────────────────────────────────────────
doc.add_paragraph()
title = doc.add_heading("MURESSONS GLOBAL CORPORATION", 0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
if title.runs:
    title.runs[0].font.color.rgb = RGBColor(0x05, 0x96, 0x69)
    title.runs[0].font.size = Pt(26)

sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = sub.add_run("Student Simulation Manual — Version 10")
r.font.size = Pt(16)
r.bold = True
r.font.color.rgb = RGBColor(0x1D, 0x4E, 0xD8)

doc.add_paragraph()
meta = doc.add_paragraph()
meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
meta.add_run("Updated: July 2026  |  Platform: v4.12  |  Audience: Players & Students\n").font.size = Pt(10)
meta.add_run("Complete guide to accessing, navigating, and excelling at the Muressons simulation.").font.size = Pt(10)

doc.add_page_break()

# ── TABLE OF CONTENTS ────────────────────────────────────────────────────
add_heading(doc, "Table of Contents", 1)
toc_items = [
    ("1", "What is Muressons Global Command?"),
    ("2", "Getting Started — Login & Joining Your Cohort"),
    ("3", "The Player Dashboard — A Complete Tour"),
    ("  3.1", "Navigation Bar"),
    ("  3.2", "Round Briefing Panel"),
    ("  3.3", "Strategic Options Panel"),
    ("  3.4", "Business Unit Strip"),
    ("  3.5", "Right Sidebar (Mailbox, Decisions, Engines)"),
    ("  3.6", "Market Reality Feed & Competitor Intel"),
    ("  3.7", "Capital Allocation Footer"),
    ("  3.8", "KPI / Charts / Metrics Toggle"),
    ("4", "How a Round Works — Step by Step"),
    ("5", "The Stakeholder Power / Interest Grid (Mendelow's Matrix)"),
    ("6", "Making Your Strategic Decision (A / B / C)"),
    ("7", "Capital Allocation Across the Five Pillars"),
    ("8", "Committing Your Turn"),
    ("9", "All 10 Main Rounds — Detailed Walkthroughs"),
    ("10", "Understanding Your KPIs"),
    ("  10.1", "Group-Level KPIs"),
    ("  10.2", "Per-BU KPIs"),
    ("  10.3", "Regenerative Multiple (M_R) & Terminal Valuation"),
    ("11", "Ending Pathways — The 5 Alternate Finals"),
    ("12", "Side Tracks — Parallel Mini-Simulations"),
    ("13", "CEO Interview"),
    ("14", "Black Swan Events"),
    ("15", "The Shadow Board"),
    ("16", "Industry Verticals (Non-Default Cohorts)"),
    ("17", "Regulatory Frameworks Referenced"),
    ("18", "Scoring, Archetypes & Final Report"),
    ("19", "Tips, Common Mistakes & FAQ"),
    ("App. A", "KPI Reference Table"),
    ("App. B", "Flag Dependency Quick Reference"),
    ("App. C", "Glossary of Key Terms"),
    ("App. D", "Balance Sheet & Statement of Financial Position Reference Guide"),
]
for num, toc_title in toc_items:
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.2 if num.startswith(" ") else 0)
    r1 = p.add_run(f"{num.strip()}. ")
    r1.bold = True
    r1.font.size = Pt(10)
    r2 = p.add_run(toc_title)
    r2.font.size = Pt(10)

doc.add_page_break()

# ════════════════════════════════════════════════════════════════════════
# 1: WHAT IS MURESSONS?
# ════════════════════════════════════════════════════════════════════════
add_heading(doc, "1.  What is Muressons Global Command?", 1)
add_para(doc, (
    "Muressons Global Corporation is a multi-round ESG and sustainability strategy simulation. "
    "You step into the role of Chief Sustainability Officer (CSO) of a large publicly listed "
    "conglomerate with four business units: Pharma, Electronics, Consumer Goods, and Software. "
    "Over 10 rounds — each representing a 6-month decision period across 5 simulated years — "
    "you navigate crises, allocate capital, manage stakeholders, and drive the company toward "
    "or away from long-term sustainable value."
))
add_para(doc, (
    "Unlike simpler compliance exercises, Muressons is built on the principle that ESG "
    "trade-offs are never isolated. Every decision ripples through your financials, stakeholder "
    "relationships, regulatory exposure, and ultimately your enterprise value. There is no single "
    "dominant strategy — the goal is to build the strongest possible company by balancing "
    "short-term cash preservation with long-run sustainability quality."
))

add_heading(doc, "Learning Objectives", 2)
objectives = [
    "Apply Double Materiality and CSRD/ESRS 1 frameworks in real decision contexts.",
    "Calculate Scope 1, 2 and 3 GHG emissions using the revenue-intensity method.",
    "Navigate crisis management — understand how reputation damage cascades via contagion theory.",
    "Experience stakeholder fatigue — the compounding difficulty of regaining trust after repeated crises.",
    "Connect every strategic decision to enterprise value through the Regenerative Multiple (M_R).",
    "Distinguish short-term cash preservation from long-run value creation.",
    "Apply regulatory frameworks: CSRD, ESRS, TCFD, CSDDD, SEBI BRSR, EU AI Act, and the GHG Protocol.",
    "Understand the Just Transition concept and how consistent HR investment amplifies your final score.",
]
for o in objectives:
    add_bullet(doc, o)

add_heading(doc, "Your Company at a Glance", 2)
add_table(doc,
    ["Business Unit", "Icon", "Revenue", "Carbon Intensity", "Character"],
    [
        ["Pharma", "💊", "$18.0M", "35 tCO₂e/$M", "High water dependency; IP-driven"],
        ["Electronics", "⚡", "$16.5M", "72 tCO₂e/$M", "Highest carbon; supply chain risk; R1 blindspot"],
        ["Consumer Goods", "🛒", "$10.5M", "48 tCO₂e/$M", "Packaging; brand risk; community-sensitive"],
        ["Software", "💻", "$8.5M", "12 tCO₂e/$M", "Lowest carbon; governance-sensitive; AI risk"],
    ],
    header_color="059669"
)
add_callout(doc,
    "All BUs start with: Treasury = $50M | Reputation = 55 | Social Licence = 50 | Burnout = 10. "
    "Opening share price: $50.00 (100M shares outstanding). Group EBITDA baseline: ~$19M.",
    "📌 Starting Position"
)
divider(doc)

# ════════════════════════════════════════════════════════════════════════
# 2: GETTING STARTED
# ════════════════════════════════════════════════════════════════════════
add_heading(doc, "2.  Getting Started — Login & Joining Your Cohort", 1)
add_para(doc, (
    "Your facilitator will provide: (1) the platform URL, (2) your Executive Identifier "
    "(e.g. MUR-001), and (3) your Clearance Cipher (password). If joining a live cohort, "
    "you will also need the Session Code."
))
add_screenshot(doc, "s01_landing.png", "The Muressons Command Access login screen (v4.12)")
add_heading(doc, "Login Steps", 2)
login_steps = [
    ("Step 1", "Open the platform URL in Chrome or Edge (recommended for WebSocket support)."),
    ("Step 2", "Enter your Executive Identifier in the 'EXECUTIVE IDENTIFIER' field (e.g. MUR-001)."),
    ("Step 3", "Enter your Clearance Cipher (password) in the 'CLEARANCE CIPHER' field."),
    ("Step 4", "Click ESTABLISH LINK to connect to your live cohort session."),
    ("Step 5", "Alternatively, click START SOLO SESSION to practise alone without a facilitator."),
    ("Step 6", "If you forgot your Clearance Cipher, click LOST CIPHER? to request a reset from your facilitator."),
]
for step, desc in login_steps:
    add_bullet(doc, desc, bold_prefix=step + ":")

add_callout(doc,
    "Never share your Clearance Cipher. Each team has a unique identifier. "
    "The platform uses JWT-secured sessions with automatic expiry after inactivity.",
    "🔒 Security Note"
)

add_heading(doc, "After Login — Joining Your Cohort", 2)
add_para(doc, (
    "After login you will be prompted for your cohort's Session Code and your team username. "
    "Once admitted, the Round Briefing for the current round opens automatically. "
    "If a round is already in progress, you enter mid-round and can see any decisions your team has staged."
))
divider(doc)

# ════════════════════════════════════════════════════════════════════════
# 3: PLAYER DASHBOARD TOUR
# ════════════════════════════════════════════════════════════════════════
add_heading(doc, "3.  The Player Dashboard — A Complete Tour", 1)
add_para(doc, (
    "The player dashboard is your command centre for the entire simulation. Every piece of "
    "information you need — from your financial position to stakeholder intelligence — is "
    "accessible from a single screen. The layout is divided into five zones."
))
add_screenshot(doc, "s05_executive_cockpit.png", "The Executive Cockpit — main player dashboard showing all five zones")

add_heading(doc, "3.1  The Navigation Bar (Top)", 2)
add_para(doc, "The navigation bar runs across the top of the screen and shows:", bold=True)
nav_items = [
    "M logo + MURESSONS — click to return to the dashboard from any modal.",
    "Your team name (e.g. WELCOME VERIFIER).",
    "● LIVE / PAUSED indicator — green dot when a round is in progress.",
    "Round number (e.g. Round 1) and current simulated date (e.g. 2026 H1).",
    "Round title (e.g. Foundations — ESG Materiality).",
    "NARRATIVE button — opens the story context for the current round.",
    "Logout button — visible at all times for quick exit.",
]
for item in nav_items:
    add_bullet(doc, item)

add_heading(doc, "3.2  The Round Briefing Panel (Left, Main Area)", 2)
add_screenshot(doc, "s02_round_briefing.png", "Round 1 Briefing: Foundations — ESG Baseline Assessment (Intel brief, objectives, academic framework)")
add_para(doc, "The Round Briefing Panel occupies the left two-thirds of the screen. It contains:")
briefing_items = [
    "Round badge (e.g. ROUND 1) and round title.",
    "BU Selector dropdown — filter the view to a specific Business Unit or 'ALL BUS'.",
    "Intelligence Briefing — the narrative context and crisis description for this round.",
    "Strategic Objectives — the specific decisions you are being asked to make.",
    "Key Metrics to Watch — the KPIs most affected this round.",
    "Academic Framework card — the real-world regulatory or theoretical model this round applies.",
    "Begin Simulation button — starts the 4-step in-round decision workflow.",
]
for item in briefing_items:
    add_bullet(doc, item)

add_heading(doc, "3.3  The Strategic Options Panel", 2)
add_para(doc, (
    "Once you click 'Begin Simulation', the Strategic Options panel appears below the briefing. "
    "It lists your three crisis response choices (A, B, C), each with a treasury cost and brief "
    "description. Click any option to expand its full detail view. You must select exactly one "
    "before proceeding to capital allocation."
))
add_callout(doc,
    "Costs shown in red (e.g. −$3.0M) are debited from Corporate Treasury at tick commit. "
    "Options with no listed cost have $0 cash impact from the crisis choice itself "
    "(pillar investments are separate).",
    "💰 Cost Indicators"
)

add_heading(doc, "3.4  The Business Unit Strip (Bottom)", 2)
add_para(doc, (
    "A scrollable strip at the bottom shows all 4 active Business Units with current Revenue "
    "and a quick ESG indicator. Click any BU card to expand its detailed profile, including "
    "Carbon Intensity, Social Licence Score, Natural Capital Debt, and Governance Risk. "
    "Read BU profiles before every capital allocation decision."
))

add_heading(doc, "3.5  The Right Sidebar", 2)
add_para(doc, "The right sidebar has three tabs:", bold=True)
sidebar_tabs = [
    ("MAILBOX", "Messages from the Board, regulators, and your facilitator. Unread count shown as a badge. Always read before deciding — they contain round-critical intelligence."),
    ("MY DECISIONS", "A log of all decisions staged this round. Review before committing. Decisions cannot be changed after commit."),
    ("ENGINES", "Real-time engine events — carbon accounting updates, stakeholder sentiment shifts, Black Swan alerts, and systemic risk readings. The ENGINES tab is where Black Swan notifications appear."),
]
for tab, desc in sidebar_tabs:
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.3)
    r1 = p.add_run(f"• {tab}: ")
    r1.bold = True
    r1.font.size = Pt(10.5)
    r2 = p.add_run(desc)
    r2.font.size = Pt(10.5)

add_heading(doc, "3.6  Competitor Intelligence & Market Reality Feed", 2)
add_para(doc, (
    "Below the sidebar tabs: the Competitor Intelligence bar shows your synergy multiplier "
    "vs. your nearest competitor. The Market Reality Feed streams live macro events, "
    "carbon price movements, regulatory bulletins, and critical foreshadowing clues. "
    "Reading the feed consistently — especially from Round 5 onward — is essential for "
    "identifying which Ending Pathway your cohort is in."
))

add_heading(doc, "3.7  The Capital Allocation Footer", 2)
add_para(doc, (
    "The footer bar shows Capital Deployed ($X / $10.0M) and a step progress indicator: "
    "Round Briefing → Stakeholder Map → Strategic Decision → Capital Allocation → Commit Turn. "
    "Steps must be completed in order. You cannot commit without completing all prior steps."
))

add_heading(doc, "3.8  KPI / Charts / Metrics Toggle", 2)
add_screenshot(doc, "s06_advanced_metrics.png", "The Metrics tab: Synergy Multiplier = 1.0× and Cost of Capital KPIs visible")
add_para(doc, "Three tabs in the top-right of the briefing panel give different company views:", bold=True)
kpi_tabs = [
    ("KPIS", "Grid of all key performance indicators — Treasury, Reputation, Carbon Intensity, SLO, NCD, Burnout, VRIO, Workforce Readiness."),
    ("CHARTS", "Trend lines for major KPIs across all completed rounds. Use this to identify deteriorating trends before they hit critical thresholds."),
    ("METRICS", "Advanced metrics: Synergy Multiplier, Cost of Capital (WACC), EBITDA margin, and the live M_R estimate."),
]
for tab, desc in kpi_tabs:
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.3)
    r1 = p.add_run(f"• {tab}: ")
    r1.bold = True
    r1.font.size = Pt(10.5)
    r2 = p.add_run(desc)
    r2.font.size = Pt(10.5)
doc.add_paragraph()
divider(doc)

# ════════════════════════════════════════════════════════════════════════
# 4: HOW A ROUND WORKS
# ════════════════════════════════════════════════════════════════════════
add_heading(doc, "4.  How a Round Works — Step by Step", 1)
add_para(doc, "Every round follows the same 5-step sequence. Steps cannot be skipped.")
round_steps = [
    ("Step 1: Read the Round Briefing",
     "Read the intelligence brief, academic framework card, and your Mailbox. "
     "Identify which KPIs are most at risk this round before making any decisions."),
    ("Step 2: Complete the Stakeholder Map",
     "Mandatory in Round 1 and certain later rounds. Drag each stakeholder "
     "into the correct Mendelow Matrix quadrant. The map must be completed before "
     "strategic options unlock (pre-requisite gate)."),
    ("Step 3: Make Your Strategic Decision (A / B / C)",
     "Select one of the three crisis response options. Read all three before choosing. "
     "Consider the treasury cost, KPI impacts, flags set, and regulatory compliance consequences."),
    ("Step 4: Allocate Capital Across the Five Pillars",
     "Select one investment option per pillar (Energy, Operations, Supply Chain, Offsetting, HR). "
     "Total capital deployed must not exceed the round budget shown in the footer."),
    ("Step 5: Commit Your Turn",
     "Review your complete decisions in the MY DECISIONS sidebar tab. "
     "Click COMMIT TURN. The server processes the tick, updates all KPIs, and advances the round counter. "
     "This action is irreversible for players."),
]
for title_s, desc in round_steps:
    add_bullet(doc, desc, bold_prefix=title_s)

add_callout(doc,
    "In a live cohort, all teams must commit before the round officially advances. "
    "Your facilitator controls the pace. Do not commit early if your team is still deliberating.",
    "🤝 Cohort Note"
)
divider(doc)

# ════════════════════════════════════════════════════════════════════════
# 5: STAKEHOLDER MAP
# ════════════════════════════════════════════════════════════════════════
add_heading(doc, "5.  The Stakeholder Power / Interest Grid (Mendelow's Matrix)", 1)
add_screenshot(doc, "s04_stakeholder_map.png", "The Stakeholder Power / Interest Grid — drag stakeholders from the left bank into the correct quadrant")
add_screenshot(doc, "s03_stakeholder_gate.png", "The Pre-Requisite Gate — Stakeholder Map must be completed before strategic options unlock")
add_para(doc, (
    "The Stakeholder Power / Interest Grid (Mendelow's Matrix) is a mandatory prerequisite "
    "in Round 1 and re-opens at key decision points in later rounds. "
    "Classify 10 stakeholders into four quadrants based on their Power over the company "
    "and their Interest in its ESG decisions."
))
add_heading(doc, "The Four Quadrants", 2)
add_table(doc,
    ["Quadrant", "Power", "Interest", "Management Strategy"],
    [
        ["MANAGE CLOSELY", "HIGH", "HIGH", "Engage actively — they can make or break your ESG strategy"],
        ["KEEP SATISFIED", "HIGH", "LOW", "Keep them broadly informed; avoid surprises"],
        ["KEEP INFORMED", "LOW", "HIGH", "Regular updates; they amplify your narrative"],
        ["MONITOR", "LOW", "LOW", "Minimal effort; watch for position changes"],
    ],
    header_color="7C3AED"
)
add_para(doc, (
    "Hover over each stakeholder card in the left bank to read their Intelligence Dossier before "
    "placing them. Incorrect placement does not block progress but calibrates stakeholder "
    "response severity in later rounds. A 5-minute timer is available if your facilitator "
    "asks for a timed exercise."
))
add_heading(doc, "Round 1 Stakeholders", 2)
r1_stakeholders = [
    "FutureFirst Activist Fund",
    "EU Regulators",
    "Deccan Plateau Local Communities",
    "Tier-3 Mine Workers",
    "Factory Floor Employees",
    "Institutional Syndicate Banks",
    "National Government Tax Authority",
    "Corporate Cafeteria Vendors",
    "General Public",
    "Regional Business Journalist",
]
for s in r1_stakeholders:
    add_bullet(doc, s)
divider(doc)

# ════════════════════════════════════════════════════════════════════════
# 6: STRATEGIC DECISION
# ════════════════════════════════════════════════════════════════════════
add_heading(doc, "6.  Making Your Strategic Decision (A / B / C)", 1)
add_para(doc, (
    "Each round's strategic decision is the single most consequential choice you make. "
    "Options A, B, and C are not a ranking — all three are legitimate strategies with "
    "different risk/reward profiles. Always read all three before selecting."
))
add_heading(doc, "How to Evaluate Each Option", 2)
eval_dims = [
    ("Treasury Cost", "Shown in red (e.g. −$3.0M). Cash-preserving options often have hidden downstream costs via flags, reputation penalties, and SLO erosion."),
    ("Flags Set", "Each option sets one or more boolean flags that persist across all remaining rounds. A flag set in R1 can double a crisis in R4."),
    ("KPI Deltas", "Each option's description lists expected changes to Reputation, Carbon Intensity, Social Licence, and other KPIs."),
    ("Regulatory Compliance", "Some options explicitly describe ESRS/CSDDD risks. Non-compliance saves cash now but invites fines and governance risk."),
    ("Pedagogy Label", "A small label (e.g. 'Sweller (1988) Cognitive Load') hints at the academic concept your decision relates to — useful for post-round reflection."),
]
for label, desc in eval_dims:
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.3)
    r1 = p.add_run(f"• {label}: ")
    r1.bold = True
    r1.font.size = Pt(10.5)
    r2 = p.add_run(desc)
    r2.font.size = Pt(10.5)

add_callout(doc,
    "The simulation has no universally 'correct' answer. Teams that always choose the most "
    "expensive option run out of treasury. Teams that always choose the cheapest option accumulate "
    "flags that destroy terminal valuation. The skill is calibrating the right trade-off each round.",
    "🎓 Learning Design"
)
divider(doc)

# ════════════════════════════════════════════════════════════════════════
# 7: CAPITAL ALLOCATION
# ════════════════════════════════════════════════════════════════════════
add_heading(doc, "7.  Capital Allocation Across the Five Pillars", 1)
add_para(doc, (
    "After your strategic decision, allocate capital across five sustainability pillars. "
    "Each pillar has three investment options — select exactly one per pillar. "
    "Pillar costs are in addition to the strategic decision cost."
))
add_table(doc,
    ["Pillar", "Icon", "Focus Area", "Example Choices"],
    [
        ["Energy", "⚡", "Carbon intensity, renewable transition", "Renewable PPA, Solar CapEx, Green Tariff"],
        ["Operations", "🏭", "Process efficiency, governance, resilience", "Digital Twin, Circular Manufacturing, Ethical AI Overhaul"],
        ["Supply Chain", "🔗", "Supplier ESG, transparency, resilience", "Supplier Audit, Blockchain Traceability, Rapid Supplier Switch"],
        ["Offsetting", "🌱", "Carbon credits, community impact, adaptation finance", "Nature-Based Offsets, SBTi Commitment, Watershed Restoration"],
        ["Human Resources", "👥", "Talent, culture, wellbeing, green skills", "DEI Programme, Green Skills Academy, Just Transition Training"],
    ],
    header_color="059669"
)
add_callout(doc,
    "The HR pillar is strategically important because consistent HR investment across rounds "
    "increases the JT Scaling Factor — a multiplier applied to your R9 Just Transition M_R "
    "bonuses. Teams that skip HR every round lose up to 50% of their potential R9 M_R bonus.",
    "💡 HR Strategy Tip"
)
divider(doc)

# ════════════════════════════════════════════════════════════════════════
# 8: COMMITTING YOUR TURN
# ════════════════════════════════════════════════════════════════════════
add_heading(doc, "8.  Committing Your Turn", 1)
add_para(doc, (
    "When all 5 steps are complete, review your decisions in the MY DECISIONS sidebar tab. "
    "Confirm: (1) a strategic option is selected, (2) one option is selected per pillar, "
    "and (3) total capital deployed is within the round budget."
))
add_para(doc, (
    "Click COMMIT TURN in the footer. The server processes your tick within a few seconds. "
    "You will see a processing animation, then your KPI dashboard updates. "
    "Engine events (Black Swans, stakeholder reactions, macro shifts) appear in the ENGINES tab."
))
add_callout(doc,
    "Once committed, decisions are final and cannot be undone by players. "
    "Only a Facilitator with override access can undo a round commit.",
    "⚠️ Irreversible Action"
)
divider(doc)

# ════════════════════════════════════════════════════════════════════════
# 9: ALL 10 ROUNDS
# ════════════════════════════════════════════════════════════════════════
add_heading(doc, "9.  All 10 Main Rounds — Detailed Walkthroughs", 1)

rounds = [
    {
        "num": 1, "icon": "📋",
        "title": "Foundations — ESG Baseline Assessment",
        "theme": "TCFD & CSRD/ESRS Frameworks",
        "scenario": (
            "The Board of Directors has mandated an initial ESG audit across all four Business Units. "
            "You must decide the depth and scope of the assessment. This decision sets the risk baseline "
            "for the entire simulation — a shallow audit saves money today but leaves hidden vulnerabilities "
            "in the Electronics supply chain that will detonate in Round 4."
        ),
        "special": "Stakeholder Map is mandatory in this round. Option A sets electronics_blindspot — a time-bomb that detonates in R4.",
        "options": [
            ("A", "Surface-Level Scan", "$0", "Sets electronics_blindspot → doubles R4 crisis severity 40→80. No CI reduction."),
            ("B", "Deep Forensic Audit", "−$3.0M", "Sets deep_audit_completed → halves R4 severity 80→40. CI −5. SLO +5. Adds +0.05 to M_R foundation."),
            ("C", "Phased Audit Rollout", "−$1.5M", "Sets deferred_audit → partial blindspot. Partial CI reduction."),
        ],
        "consequence": "The electronics_blindspot flag doubles R4 crisis severity. The $3M cost of Option B pays back via avoided R4 damage ($6M+ in protected treasury).",
        "pedagogy": "TCFD & CSRD/ESRS 1 — The audit decision determines your baseline disclosure readiness and supply chain transparency.",
    },
    {
        "num": 2, "icon": "📊",
        "title": "Double Materiality — Budget Allocation",
        "theme": "CSRD/ESRS 1 Double Materiality Assessment",
        "scenario": (
            "Your CFO requires all investment proposals to align with the High Financial Impact / "
            "High ESG Impact quadrant of the Double Materiality framework (ESRS 1). "
            "A Materiality Gate opens: achieving 90%+ accuracy in your materiality assessment "
            "unlocks a $2M treasury bonus. An advanced Climate mode becomes available."
        ),
        "special": "CFO Materiality Gate: 90%+ materiality accuracy → +$2M treasury bonus. Option C violates ESRS 1 §1.51 (management body oversight).",
        "options": [
            ("A", "Full Materiality Alignment", "−$2.5M", "Sets materiality_aligned → +0.10 M_R at R10. Full ESRS 1 compliance."),
            ("B", "Strategic Exceptions", "$0", "Partial compliance. Sets materiality_exceptions. Moderate long-term M_R."),
            ("C", "CEO-Only Sign-Off", "$0", "ESRS 1 §1.51 violation. 40% budget clawback; Gov Risk +10; Rep −5; Cost of Capital increases."),
        ],
        "consequence": "Option C is a real ESRS 1 governance violation — the management body must oversee materiality. Institutional investors apply a risk premium raising WACC.",
        "pedagogy": "Double Materiality: financial materiality (ESG impacts on company) AND impact materiality (company impacts on world). Both dimensions required under ESRS 1.",
    },
    {
        "num": 3, "icon": "🏭",
        "title": "Scope 3 — Supply Chain Decarbonisation",
        "theme": "GHG Protocol Scope 3 Accounting",
        "scenario": (
            "Regulators signal mandatory Scope 3 disclosures. Your supply chain carbon is 4× your "
            "direct emissions. Electronics and Consumer Goods absorb the most risk. "
            "This round introduces scope3_weighted CI routing — CI reductions are distributed "
            "proportionally across BUs based on each BU's Scope 3 exposure ratio."
        ),
        "special": "scope3_weighted routing: CI reductions from Options A/B are distributed proportionally across BUs. Option A sets early_decarboniser — a high-value flag for R7.",
        "options": [
            ("A", "Rapid Supplier Switch", "−$4.0M", "Sets early_decarboniser → +0.10 synergy bonus in R7. CI −15 (scope3-weighted). Supply disruption risk."),
            ("B", "Green Bond Investment", "−$2.0M", "Sets green_bond_active. NCD −15. CI −8 (scope3-weighted). Lower disruption risk."),
            ("C", "Offset & Defer", "−$1.0M", "Sets carbon_deferred. NCD +5. Rep −3. Defers the problem to later rounds."),
        ],
        "consequence": "The early_decarboniser flag (Option A or B in some configurations) unlocks a synergy bonus in R7 and strengthens the Climate Black Swan ending pathway position.",
        "pedagogy": "GHG Protocol Scope 3 — 15 indirect emission categories. Typically 70–90% of a company's total footprint.",
    },
    {
        "num": 4, "icon": "🔥",
        "title": "Contagion — Reputation Crisis Cascade",
        "theme": "Crisis Management & S-Curve Contagion Theory",
        "scenario": (
            "A labour-rights exposé in the Electronics supply chain goes viral. Contagion "
            "propagates via the S-curve sigmoid formula. If electronics_blindspot is active "
            "(R1 Option A), severity doubles from 40 to 80. If deep_audit_completed is active, "
            "severity halves. The crisis fires regardless — the question is how severe it becomes."
        ),
        "special": (
            "Sigmoid formula: Group_Rep = Avg_Rep - 50 × sigmoid((severity - 30) / 15). "
            "Severity: 80 (blindspot), 40 (no flag), 20 (deep_audit_completed)."
        ),
        "options": [
            ("A", "Full Transparency & Remediation", "−$6.0M", "Sets remediation_active. Rep +10. SLO +8. Gov Risk −5. Addresses root cause."),
            ("B", "Damage Control PR", "−$2.0M", "Sets pr_containment. Rep +2. SLO −3. Root cause unaddressed — compounds later."),
            ("C", "Deny & Deflect", "$0", "Sets deny_and_deflect. Rep −15. SLO −10. Gov Risk +8. NCD +5. High risk of escalation."),
        ],
        "consequence": "Option C saves cash but severely damages Social Licence and sets up compounding risk in R9 (strike probability) and the Regulatory Shutdown pathway.",
        "pedagogy": "Stakeholder Fatigue: trust recovery efficiency = 1 / (1 + 0.3 × crisis_count). Each subsequent crisis is harder to recover from.",
    },
    {
        "num": 5, "icon": "🌪️",
        "title": "Climate — Physical Climate Risk Event",
        "theme": "TCFD Physical Risk & Nature-Based Solutions",
        "scenario": (
            "A Category 4 cyclone is projected to make landfall. Base damage: $12M. "
            "A stochastic roll (>0.75 triggers full damage) determines actual impact. "
            "The Shadow Board activates this round — three virtual directors each advocate "
            "for a different option. Players may reject their advice, but each rejection "
            "permanently sets a penalty flag."
        ),
        "special": "Stochastic roll: if RNG value > 0.75, full $12M damage applied. Protection from Options A/B has a 2-round delay (active from R7 onward).",
        "options": [
            ("A", "Hard Engineering Defence", "−$8.0M", "Resilience Factor 0.85. Sets hard_engineering. NCD +10. CI +3. 2-round delay before active."),
            ("B", "Nature-Based Solutions", "−$5.0M", "Resilience Factor 0.60. Sets nature_based_resilience. NCD −8. CI −6. 2-round delay before active."),
            ("C", "Insurance Only", "−$2.0M", "Resilience Factor 0.00. Sets insurance_only → PERMANENTLY BLOCKS +0.20 Resilience M_R bonus at R10."),
        ],
        "consequence": "Option C blocks the +0.20 Resilience M_R bonus — equivalent to destroying $8–15M in terminal value. Nature-Based Solutions (B) typically delivers highest combined value.",
        "pedagogy": "TCFD Physical Risk Scenarios. Nature-Based Solutions as a dual-benefit (mitigation + adaptation) climate strategy.",
    },
    {
        "num": 6, "icon": "🤖",
        "title": "AI Bias — Algorithmic Ethics & Brand Risk",
        "theme": "EU AI Act & Algorithmic Accountability",
        "scenario": (
            "Your Software BU's AI recruitment tool is found to systematically discriminate. "
            "The story reaches mainstream media. Rounds 6–8 enter the 'interest rate tightening' "
            "macro phase — WACC increases, reducing the terminal exit multiple. "
            "Your AI crisis response sets a Truth Premium flag that persists to R10."
        ),
        "special": "R6–R8: macro WACC tightening phase. EU AI Act compliance costs fire from R7 if ai_monetised flag is set.",
        "options": [
            ("A", "Monetise the Algorithm", "+$10.0M (Software Rev)", "Sets ai_monetised. Rep −20. SLO −15. EU AI Act compliance costs fire from R7."),
            ("B", "Ethical AI Overhaul", "−$8.0M", "Sets ethical_ai_overhaul → +0.15 Truth Premium M_R at R10. SLO +15."),
            ("C", "Quiet Patch", "−$1.0M", "Sets quiet_patch. Gov Risk +10. Risk of future leak. No M_R benefit."),
        ],
        "consequence": "Option A generates short-term revenue but EU AI Act costs from R7 often exceed the $10M gain. Option B is the highest M_R choice.",
        "pedagogy": "EU AI Act high-risk system classification. Ethical AI by design vs. retrofit compliance.",
    },
    {
        "num": 7, "icon": "♻️",
        "title": "Circularity — Circular Economy Transition",
        "theme": "EU Circular Economy Regulation & Synergy Engine",
        "scenario": (
            "EU circular economy regulations mandate 60% waste diversion. Non-compliance fine: $15M. "
            "The Synergy Engine activates — choosing Option C unlocks a synergy bonus propagating "
            "to terminal valuation. The early_decarboniser flag (R3 Option A) generates a "
            "+0.10 synergy multiplier bonus this round."
        ),
        "special": "Option C sets synergy_unlock → +0.15 M_R Strategic Synergy Premium at R10. Synergy uses diminishing-returns sqrt model.",
        "options": [
            ("A", "Full Circular Redesign", "−$10.0M", "Sets circular_redesign. NCD −12. CI −8 (scope3-weighted). Rep +8. Maximum environmental benefit."),
            ("B", "Extended Producer Responsibility", "−$5.0M", "Sets epr_program. NCD −6. CI −5. Balanced approach."),
            ("C", "Waste-to-Energy Partnership", "−$7.0M", "Sets waste_to_energy + synergy_unlock → +0.15 M_R at R10 + OPEX savings."),
        ],
        "consequence": "Option C is strategically critical for the Activist Ultimatum pathway — synergy_unlock is required for the highest-value R10 response option.",
        "pedagogy": "Ellen MacArthur Foundation Circular Economy. Synergy: OPEX savings from cross-BU resource efficiency (diminishing-returns sqrt model).",
    },
    {
        "num": 8, "icon": "🌊",
        "title": "Blue Stress — Water Scarcity Emergency",
        "theme": "CDP Water Security & Natural Capital Accounting",
        "scenario": (
            "A multi-year drought depletes the watershed serving Pharma and Electronics. "
            "Government water rationing is imminent. Rounds 8–10 enter the 'crisis premium' "
            "macro phase — WACC is at its highest level. "
            "Option B prioritises Electronics but permanently blocks your Resilience M_R bonus."
        ),
        "special": "Option B sets electronics_water_priority → PERMANENTLY BLOCKS +0.20 Resilience M_R. Option C: Desalination generates $5M/round from R10 (late payback).",
        "options": [
            ("A", "Water Efficiency for All BUs", "−$12.0M", "Sets water_efficiency_all. Water −20 across all BUs. CI −3. SLO +5. Preserves Resilience M_R."),
            ("B", "Prioritise Electronics", "−$4.0M", "Sets electronics_water_priority → BLOCKS +0.20 Resilience M_R. SLO −25 for Pharma/Consumer Goods."),
            ("C", "Desalination Mega-Project", "−$30.0M", "Sets desalination_built. NCD −30. Water −40. $5M/round revenue from R10 (2-round late payback)."),
        ],
        "consequence": "Option B trades $8.5M in savings for a permanent M_R block worth $10–20M in terminal value. Option A is the recommended path for preserving Resilience M_R.",
        "pedagogy": "CDP Water Security Framework. Natural Capital Debt — unpriced environmental liabilities that raise cost of debt by 0.01% per unit.",
    },
    {
        "num": 9, "icon": "✊",
        "title": "Just Transition — Workforce & Community Justice",
        "theme": "ILO Just Transition Framework & JT Scaling Factor",
        "scenario": (
            "Decarbonisation requires closing 3 legacy factories. 2,000 jobs are at risk. "
            "If Social Licence Score is below threshold, there is a 50% chance of a strike "
            "that zeros revenue this round. The regulatory_friction flag may be active (OPEX drag). "
            "This round's M_R bonuses are multiplied by the JT Scaling Factor — teams with "
            "consistent HR investment earn a higher multiplier."
        ),
        "special": "JT Scaling Factor = min(1.5, 1.0 + HR_investment_rounds × 0.10). Strike prob 75% if SLO low and immediate_closure chosen.",
        "options": [
            ("A", "Immediate Closure", "+$5.0M", "Sets immediate_closure. SLO −20. Rep −15. 75% strike chance if SLO < threshold. No M_R bonus."),
            ("B", "Managed Transition", "−$12.0M", "Sets managed_transition → +0.12 M_R Just Transition bonus (×JT scaling). SLO +10. Rep +8."),
            ("C", "Community Investment Fund", "−$20.0M", "Sets community_fund → +0.18 M_R Community Champion bonus (×JT scaling). SLO +18. Rep +12."),
        ],
        "consequence": "Option C with maximum JT scaling (1.5×) delivers +0.27 M_R — the single highest M_R bonus available in one decision. Requires strong treasury and consistent HR history.",
        "pedagogy": "ILO Just Transition Guidelines. Human capital as a long-term value driver. JT scaling rewards consistent investment over time, not one-round fixes.",
    },
    {
        "num": 10, "icon": "🏛️",
        "title": "Grand Finale — Pathway-Dependent Crisis",
        "theme": "Terminal Valuation & ESG Enterprise Value",
        "scenario": (
            "Round 10's crisis depends on which Ending Pathway your facilitator selected. "
            "The default is the Activist Ultimatum — an activist consortium holding a blocking "
            "stake demands restructuring. Alternative pathways replace this crisis entirely "
            "(see Section 11). Terminal Valuation runs after your R10 decision is applied. "
            "Share price is revealed immediately after commit."
        ),
        "special": "Terminal Valuation: TV = (Terminal_EBITDA + Green_Fund) × Exit_Multiple × M_R × M_SDG. Equity Value = TV − Net Debt. Share Price = Equity ÷ 100M shares.",
        "options": [
            ("A", "Resist & Integrate (Default)", "−$5.0M", "Requires Synergy > 0.80. Full synergy bonus + terminal valuation at peak multiplier."),
            ("B", "Spin-off (Default)", "+$10.0M", "Divests weakest BU. Partial value unlock. SLO −5."),
            ("C", "Divest (Default)", "+$25.0M", "Sets synergy_wipe. Divests all BUs. Short-term cash max; synergy value destroyed. Rep −10."),
        ],
        "consequence": "Option C maximises short-term cash but wipes all synergy value built over R1–R7. If synergy_unlock is active, Option A produces the highest terminal value.",
        "pedagogy": "ESG-linked Enterprise Valuation. The Regenerative Multiple — how governance, social, and environmental quality translate directly into exit multiple expansion.",
    },
]

for rd in rounds:
    add_heading(doc, f"Round {rd['num']} — {rd['icon']} {rd['title']}", 2)
    p = doc.add_paragraph()
    r1 = p.add_run("Academic Framework: ")
    r1.bold = True
    r1.font.size = Pt(10.5)
    r2 = p.add_run(rd["theme"])
    r2.font.italic = True
    r2.font.size = Pt(10.5)
    add_para(doc, rd["scenario"])
    add_callout(doc, rd["special"], "⚙️ Special Mechanic", color=(0x1D, 0x4E, 0xD8))
    add_table(doc,
        ["Opt", "Title", "Cost", "Key Effects & Flags"],
        [(o[0], o[1], o[2], o[3]) for o in rd["options"]],
        header_color="1D4ED8"
    )
    add_callout(doc, rd["consequence"], "🔁 Downstream Consequence", color=(0xDC, 0x26, 0x26))
    add_callout(doc, rd["pedagogy"], "📚 Pedagogy", color=(0x78, 0x71, 0x6C))

divider(doc)

# ════════════════════════════════════════════════════════════════════════
# 10: KPIs
# ════════════════════════════════════════════════════════════════════════
add_heading(doc, "10.  Understanding Your KPIs", 1)
add_heading(doc, "10.1  Group-Level KPIs", 2)
add_table(doc,
    ["KPI", "Start", "Range", "What Drives It"],
    [
        ["Corporate Treasury", "$50M", "Unrestricted", "All investment costs, crisis costs, revenue surplus"],
        ["Group Reputation", "55", "0–100", "Crisis responses, contagion events, greenwash detection"],
        ["Synergy Multiplier", "1.0×", "0–2.0×", "Cross-BU investment; circular economy; sqrt diminishing returns"],
        ["WACC / Cost of Capital", "~7%", "5%–20%+", "NCD, macro rate cycle, governance risk, equity premium"],
        ["Workforce Readiness", "50", "0–100", "HR pillar investment; burnout; brain-drain events"],
        ["Share Price", "$50.00", "Calculated R10", "TV = EBITDA × Exit × M_R × M_SDG ÷ 100M shares"],
    ]
)
add_heading(doc, "10.2  Per-BU KPIs", 2)
add_table(doc,
    ["KPI", "Start", "Range", "What Drives It"],
    [
        ["Revenue", "Varies", "≥ $0", "Round outcomes, black swans, competitor pressure, strikes"],
        ["OPEX", "Varies", "> $0", "Synergy engine, burnout penalty, macro inflation, circular economy"],
        ["Carbon Intensity (CI)", "12–72 tCO₂e/$M", "≥ 0", "Energy pillar, supply chain decisions, scope3 routing"],
        ["Social Licence Score (SLO)", "50", "0–100", "Stakeholder decisions, crisis responses, transparency"],
        ["Staff Burnout Index", "10", "0–100", "HR investment, crisis events; OPEX quadratic penalty > 20"],
        ["Natural Capital Debt (NCD)", "Varies", "≥ 0", "Green investment vs. deferral; raises cost_of_debt 0.01%/unit"],
        ["Governance Risk Score", "10–25", "0–100", "Audit depth, transparency decisions, AI ethics, ESRS compliance"],
        ["VRIO Advantage", "0.80", "0–1.0", "2% decay per round unless reinvested; affects competitive position"],
    ]
)
add_heading(doc, "10.3  The Regenerative Multiple (M_R) & Terminal Valuation", 2)
add_para(doc, (
    "The Regenerative Multiple (M_R) is the single most important number in the simulation. "
    "It is an ESG quality multiplier on your terminal exit multiple. "
    "M_R ranges from approximately 0.0 to 2.07 (before the SDG multiplier)."
))
add_table(doc,
    ["M_R Component", "Trigger Condition", "Value"],
    [
        ["Base", "Always", "+1.00"],
        ["Materiality Governance", "materiality_aligned flag", "+0.10"],
        ["Synergy Strategic Premium", "synergy_unlock AND synergy ≥ 0.80", "+0.15"],
        ["Resilience Champion", "No insurance_only AND no electronics_water_priority", "+0.20"],
        ["Truth Premium", "ethical_ai_overhaul flag", "+0.15"],
        ["Community Champion", "community_fund flag (×JT scaling)", "+0.18"],
        ["Just Transition", "managed_transition flag (×JT scaling)", "+0.12"],
        ["Workforce Excellence", "workforce_readiness ≥ 75", "+0.10"],
        ["Wellbeing Champion", "avg burnout < 20", "+0.05"],
        ["BRSR ESG Alpha Dividend", "BRSR track Score ≥ 80", "+0.05"],
        ["Planet Expendable Penalty", "planet_expendable (Shadow Board R5 rejection)", "−0.20"],
        ["Instability Discount", "avg Social Licence < 75", "−0.40"],
    ],
    header_color="059669"
)
add_para(doc, "Terminal Valuation formula:", bold=True)
add_bullet(doc, "Terminal EBITDA = Sum(BU Revenue - BU OPEX) - (Total tCO2e × Carbon Tax per tonne)")
add_bullet(doc, "Terminal Value (EV) = (Terminal EBITDA + Green Fund) × Exit Multiple × M_R × M_SDG")
add_bullet(doc, "Equity Value = Terminal Value - Net Debt")
add_bullet(doc, "Share Price = Equity Value / 100,000,000 shares outstanding")
add_callout(doc, "IPO Price: $50.00/share. A fully regenerative company can deliver 2–3× the terminal value of a purely cash-maximising strategy.", "📈 Value Creation")
divider(doc)

# ════════════════════════════════════════════════════════════════════════
# 11: ENDING PATHWAYS
# ════════════════════════════════════════════════════════════════════════
add_heading(doc, "11.  Ending Pathways — The 5 Alternate Finals", 1)
add_para(doc, (
    "Your facilitator selects one of five Ending Pathways before the session. "
    "Each pathway replaces the default Round 10 'Activist Ultimatum' crisis with a different "
    "scenario. You will NEVER be told the pathway name — instead, foreshadowing clues appear "
    "in the Market Reality Feed from Rounds 5–8. Reading those clues is essential for "
    "arriving at R10 with the right strategy."
))
add_table(doc,
    ["Pathway", "R10 Crisis", "Key Vulnerability", "R8 Foreshadowing Clue"],
    [
        ["Activist Ultimatum (default)", "Activist Ultimatum", "Synergy < 1.3", "'Blocking Stake Reached — Board Engagement Imminent'"],
        ["Climate Black Swan", "Stranded Asset Reckoning", "High Carbon Intensity", "'ALERT: 1.5°C Threshold Breached — Carbon Markets in Turmoil'"],
        ["Stakeholder Revolt", "Social Reckoning", "Low SLO or High Burnout", "'#MuressonsExposed — Triple Stakeholder Ultimatum'"],
        ["Hostile Takeover", "The Corporate Raider", "Low Synergy + Low Treasury", "'Cerberus Files Preliminary Offer with Regulator'"],
        ["Regulatory Shutdown", "Compliance Reckoning", "Low Governance / High CI", "'Regulator Issues Show Cause Notice to Muressons'"],
    ],
    header_color="DC2626"
)
add_callout(doc,
    "Leaderboard difficulty normalisation coefficients (for cross-cohort comparison): "
    "Activist 1.00 | Climate 1.15 | Stakeholder 1.10 | Hostile 1.20 | Regulatory 1.12.",
    "🏆 Leaderboard"
)
divider(doc)

# ════════════════════════════════════════════════════════════════════════
# 12: SIDE TRACKS
# ════════════════════════════════════════════════════════════════════════
add_heading(doc, "12.  Side Tracks — Parallel Mini-Simulations", 1)
add_para(doc, (
    "Side Tracks are self-contained mini-simulations (4–7 rounds each) that your facilitator "
    "may assign at any point. When active, the main simulation pauses. "
    "Side track decisions have real financial and ESG consequences — outputs feed back into "
    "the main simulation via flag write-backs and KPI modifiers."
))
tracks = [
    ("12.1", "Supply Chain 🔗", "R3–R7",
     "Supply chain visibility, supplier risk scoring, and circular economy integration. 5 rounds. "
     "Dimensions: Supply Visibility, Supplier Risk, ESG Compliance, Circular Economy Score. "
     "Write-back: transparency metrics reduce Black Swan probability in main simulation."),
    ("12.2", "Ethics & Sustainability 🌿", "R2–R7",
     "Ethical governance, anti-corruption, and human rights due diligence. "
     "Write-back: ethics integrity flags improve BRSR NGRBC starting position."),
    ("12.3", "Stakeholder Management 🤝", "R3–R8",
     "NPC stakeholder dynamics, trust building, and coalition management. "
     "Write-back: Stakeholder Fatigue Engine modifiers; SLO floor improvements in main simulation."),
    ("12.4", "Sustainability Reporting 📋", "R4–R8",
     "CSRD/ESRS report building, assurance, and disclosure quality. "
     "Write-back: regulatory_readiness score boosts BRSR NGRBC starting position."),
    ("12.5", "Corporate SDG Deep Track 🌐", "R1–R8 (5 rounds)",
     "UN SDG alignment across 5 thematic rounds. SDG Impact Score range: −11 to 105. "
     "Generates M_SDG = 1.0 + (SDG_Score/100) × 0.25. Range: 0.97 (all C) to 1.26 (all A). "
     "M_SDG multiplies your entire Terminal Value. Rounds: PAI Audit | Living Wage | "
     "Circular Procurement | Biodiversity Net-Gain | Integrated Reporting."),
    ("12.6", "BRSR NGRBC Deep Dive 🇮🇳", "R2–R8 (5 rounds)",
     "SEBI BRSR framework — all 9 NGRBC principles, Essential and Leadership indicators. "
     "Rounds: Governance & Ethics (P1/P7) | Human Capital (P3/P5) | Environmental (P6/P2) | "
     "Value Chain (P4/P8/P9) | Integrated BRSR Core Disclosure. "
     "Score ≥ 80 → brsr_net_positive_dividend → +0.05 M_R at R10. "
     "Greenwash risk: if brsr_greenwash_risk active, SEBI issues show-cause notice in ST-R4."),
]
for num, track_name, timing, desc in tracks:
    add_heading(doc, f"{num}  {track_name}  (Available: {timing})", 2)
    add_para(doc, desc)
divider(doc)

# ════════════════════════════════════════════════════════════════════════
# 13: CEO INTERVIEW
# ════════════════════════════════════════════════════════════════════════
add_heading(doc, "13.  CEO Interview", 1)
add_para(doc, (
    "The CEO Interview is an optional debrief tool accessible from the ENGINES sidebar tab. "
    "It presents your CEO (an AI-driven character) who responds to your actual decision "
    "history with narrative reflections, challenges, and strategic questions. "
    "A team that chose Option A in R1 will receive a different conversation than a team "
    "that chose Option C."
))
add_para(doc, (
    "Use the CEO Interview to: (1) understand narrative consequences of your choices, "
    "(2) prepare for facilitated debrief discussions, and "
    "(3) explore the 'what-if' dimensions of strategies you did not choose."
))
divider(doc)

# ════════════════════════════════════════════════════════════════════════
# 14: BLACK SWAN EVENTS
# ════════════════════════════════════════════════════════════════════════
add_heading(doc, "14.  Black Swan Events", 1)
add_para(doc, (
    "Black Swan events are low-probability, high-impact stochastic events evaluated each round. "
    "Drawn from Nassim Taleb's fat-tail theory, they model real unpredictable disruptions. "
    "When a Black Swan fires, it appears as an alert in the ENGINES tab and Market Reality Feed."
))
add_table(doc,
    ["Event", "Rounds", "Base Prob.", "Key Impact"],
    [
        ["Sovereign Debt Crisis", "R4–R8", "8%", "Treasury −12%, interest +300bps, Revenue −10%"],
        ["Internal Whistleblower", "R3–R9", "6%", "Rep −20, Treasury −8%, SLO −15, Gov Risk +15"],
        ["Pandemic Disruption", "R5–R9", "6%", "30% workforce loss, OPEX +15%, Burnout +20"],
        ["AI Disruption Wave", "R6–R10", "10%", "Software Rev +20%, ops displacement 15%, Burnout +10"],
        ["Climate Litigation", "R7–R10", "5%", "Treasury −$8M, asset writedown 10%, Rep −10"],
        ["Critical Mineral Embargo", "R4–R9", "7%", "Electronics/Pharma Rev −15%, OPEX +10%"],
        ["Ransomware Attack", "R3–R10", "7%", "Treasury −$5M, Revenue −5%, Rep −8, Gov Risk +12"],
        ["Consumer Boycott", "R4–R9", "5%", "Consumer Goods Rev −20%, Rep −12, SLO −10"],
    ],
    header_color="DC2626"
)
add_callout(doc,
    "Black Swan probability is conditional on your decisions. Example: Whistleblower probability "
    "+15% if greenwashing_detected is active. Poor early decisions compound your later exposure.",
    "⚡ Conditional Risk"
)
divider(doc)

# ════════════════════════════════════════════════════════════════════════
# 15: SHADOW BOARD
# ════════════════════════════════════════════════════════════════════════
add_heading(doc, "15.  The Shadow Board", 1)
add_para(doc, (
    "The Shadow Board activates in Round 5. Three virtual directors each advocate for "
    "their preferred crisis option:"
))
directors = [
    ("Planet Director", "Advocates for the environmentally superior option (usually Nature-Based Solutions)."),
    ("People Director", "Advocates for the socially superior option — prioritises SLO and workforce impacts."),
    ("Shareholder Director", "Advocates for the financially superior short-term option — warns against cash-heavy choices."),
]
for name, role in directors:
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.3)
    r1 = p.add_run(f"• {name}: ")
    r1.bold = True
    r1.font.size = Pt(10.5)
    r2 = p.add_run(role)
    r2.font.size = Pt(10.5)

add_para(doc, "Rejecting a director permanently sets a penalty flag:", bold=True)
add_table(doc,
    ["Rejected Director", "Flag Set", "Consequence"],
    [
        ["Planet Director", "planet_expendable", "−0.20 M_R (all pathways) + amplifies Climate Black Swan probability"],
        ["Shareholder Director", "shareholder_alienated", "−0.20 M_R (Hostile Takeover pathway only)"],
        ["Governance Director", "governance_fragility", "−0.25 M_R (Regulatory Shutdown) + triggers BRSR Whistleblower leak"],
    ],
    header_color="7C3AED"
)
divider(doc)

# ════════════════════════════════════════════════════════════════════════
# 16: INDUSTRY VERTICALS
# ════════════════════════════════════════════════════════════════════════
add_heading(doc, "16.  Industry Verticals (Non-Default Cohorts)", 1)
add_para(doc, (
    "Facilitators can replace any of the 4 default BU slots with an industry vertical. "
    "If your cohort runs a vertical-enabled session, the BU strip will show a non-default "
    "BU with different starting financials and risk profile."
))
add_table(doc,
    ["Vertical", "Replaces", "Carbon Intensity", "Key Character"],
    [
        ["Oil & Gas", "Pharma slot", "95 tCO2e/$M", "Extreme carbon; stranded asset risk; NCD = 350"],
        ["Banking & Financial Services", "Software slot", "8 tCO2e/$M", "Financed emissions; systemic risk; Gov Risk = 30"],
        ["Retail/FMCG", "Consumer Goods slot", "42 tCO2e/$M", "Packaging; labour-intensive; brand risk"],
        ["Agriculture", "Consumer Goods slot", "55 tCO2e/$M", "Water = 90; biodiversity; land-use emissions"],
        ["Technology/AI", "Software slot", "15 tCO2e/$M", "Data centre energy; talent brain-drain; Gov Risk = 28"],
    ]
)
divider(doc)

# ════════════════════════════════════════════════════════════════════════
# 17: REGULATORY FRAMEWORKS
# ════════════════════════════════════════════════════════════════════════
add_heading(doc, "17.  Regulatory Frameworks Referenced in the Simulation", 1)
frameworks = [
    ("CSRD (Corporate Sustainability Reporting Directive)",
     "EU regulation requiring large companies to report on sustainability impacts, risks, "
     "and opportunities per ESRS standards. Referenced in R2 (Double Materiality), R4 (governance), R7 (circular economy)."),
    ("ESRS 1 (General Requirements)",
     "Sets the Double Materiality methodology. Management body must oversee the process — "
     "bypassing this (R2 Option C) is an explicit ESRS 1 §1.51 violation in the simulation."),
    ("GHG Protocol",
     "Global standard for measuring greenhouse gas emissions across Scope 1, 2, and 3. "
     "Carbon Intensity (tCO2e per $M revenue) is the primary emissions metric."),
    ("TCFD (Task Force on Climate-related Financial Disclosures)",
     "Framework for disclosing climate risks and opportunities. Referenced in R1 (audit), "
     "R5 (physical risk), and foreshadowing KPIs."),
    ("CSDDD (Corporate Sustainability Due Diligence Directive)",
     "EU law requiring companies to identify and address adverse human rights and environmental "
     "impacts in their value chains. Referenced in Regulatory Shutdown pathway."),
    ("SEBI BRSR (Business Responsibility & Sustainability Report)",
     "India's mandatory ESG disclosure framework for listed companies, aligned with 9 NGRBC principles. "
     "Referenced in the BRSR NGRBC side track."),
    ("EU AI Act",
     "Regulation governing AI systems by risk level. High-risk AI systems (e.g. AI recruitment tools) "
     "require conformity assessment. Referenced in Round 6."),
    ("SBTi (Science Based Targets initiative)",
     "Framework for setting corporate emission reduction targets aligned with Paris Agreement 1.5°C. "
     "Referenced in Supply Chain pillar options."),
    ("EU CBAM (Carbon Border Adjustment Mechanism)",
     "Carbon tariff on imports from non-EU countries with lower carbon pricing. "
     "Referenced in region-specific Black Swan events."),
]
for name, desc in frameworks:
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.2)
    r1 = p.add_run(name + "\n")
    r1.bold = True
    r1.font.size = Pt(10.5)
    r2 = p.add_run("  " + desc)
    r2.font.size = Pt(10)
    r2.italic = True
divider(doc)

# ════════════════════════════════════════════════════════════════════════
# 18: SCORING & ARCHETYPES
# ════════════════════════════════════════════════════════════════════════
add_heading(doc, "18.  Scoring, Archetypes & Final Report", 1)
add_screenshot(doc, "s12_leaderboard.png", "The Player Leaderboard — Terminal Value, Total Cash, Synergy, and Reputation columns")
add_para(doc, (
    "After Round 10, terminal valuation runs automatically. Your share price is revealed "
    "and you are assigned a Company Archetype based on your Regenerative Multiple (M_R)."
))
add_table(doc,
    ["M_R Range", "Archetype", "Icon", "Meaning"],
    [
        ["≥ 1.8", "The Regenerative Titan", "🌱", "Exceptional ESG quality; premium market position; ESG investors overweight"],
        ["1.2–1.79", "The De-risked Safe-Haven", "🏦", "Strong ESG credentials; low risk premium; defensive investment grade"],
        ["0.8–1.19", "The Fragile Giant", "⚠️", "Moderate ESG; exposed to regulatory and stakeholder risk"],
        ["< 0.8", "The Stranded Relic", "💀", "ESG failures; stranded assets likely; heavy governance discount"],
        ["Treasury < $0", "The Turnaround Manager", "🔧", "M_R capped at 0.80; requires urgent restructuring"],
    ]
)
add_para(doc, (
    "The leaderboard ranks all teams by Terminal Value (primary) then by Normalized M_R "
    "(accounting for pathway difficulty). Your Final Report — available after R10 — includes: "
    "full equity bridge, EBITDA waterfall, ESG KPI trajectory across all 10 rounds, "
    "flag history, and a personalised debrief narrative."
))
divider(doc)

# ════════════════════════════════════════════════════════════════════════
# 19: TIPS, MISTAKES & FAQ
# ════════════════════════════════════════════════════════════════════════
add_heading(doc, "19.  Tips, Common Mistakes & FAQ", 1)
add_heading(doc, "The 10 Most Common Student Mistakes", 2)
mistakes = [
    ("R1 Option A to save cash",
     "The electronics_blindspot flag doubles your R4 crisis severity (40→80). "
     "The $3M cost of Option B pays back many times over in avoided R4 damage."),
    ("R5 Option C (Insurance Only)",
     "It blocks the +0.20 Resilience M_R bonus permanently — equivalent to destroying "
     "$8–15M in terminal value. Never choose Insurance Only if treasury allows."),
    ("Ignoring the HR pillar",
     "The JT Scaling Factor means consistent HR investment across R1–R9 amplifies your "
     "R9 M_R bonus by up to 50%. HR is a terminal value lever, not a soft cost."),
    ("Maximising treasury at the expense of SLO",
     "The Instability Discount (avg SLO < 75 = −0.40 M_R) is the largest single penalty. "
     "It can destroy 40% of your terminal multiple."),
    ("R6 Option A (Monetise the Algorithm)",
     "The $10M Software revenue is often wiped by EU AI Act costs from R7 onward, "
     "plus Rep −20 and SLO −15 impacts."),
    ("Not reading the Market Reality Feed",
     "Foreshadowing clues from R5–R8 reveal which pathway is active. "
     "Ignoring them means arriving at R10 with the wrong strategy."),
    ("Forgetting Natural Capital Debt",
     "NCD raises your cost of debt by 0.01% per unit. "
     "High NCD across 10 rounds can raise WACC by 3–5%, significantly reducing your exit multiple."),
    ("Rushing the Stakeholder Map",
     "Incorrect placements reduce stakeholder response quality in later rounds and "
     "affect Black Swan conditional probabilities."),
    ("R2 Option C (CEO-Only Sign-Off)",
     "An explicit ESRS 1 §1.51 violation. The 40% budget clawback and Gov Risk +10 "
     "cost more than Option A's upfront investment."),
    ("Not accounting for JT Scaling in R9",
     "With maximum HR investment (6+ rounds) and JT scaling of 1.5×, Option C in R9 "
     "delivers +0.27 M_R — the single highest M_R bonus from one decision in the game."),
]
for i, (title_m, desc) in enumerate(mistakes, 1):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.3)
    r1 = p.add_run(f"{i}. {title_m}: ")
    r1.bold = True
    r1.font.size = Pt(10.5)
    r2 = p.add_run(desc)
    r2.font.size = Pt(10.5)

add_heading(doc, "Frequently Asked Questions", 2)
faqs = [
    ("Can we change a decision after committing?",
     "No. Decisions are final after commit. Only a Facilitator with override access can undo."),
    ("What happens if treasury goes negative?",
     "Simulation continues but you enter Survival Mode — M_R capped at 0.80; Turnaround Manager archetype."),
    ("Are there correct answers?",
     "No. The simulation is calibrated so no single strategy dominates. Learning is in the trade-offs."),
    ("What is the best Round 1 choice?",
     "Option B (Deep Forensic Audit) is highest long-term value for most pathways."),
    ("Can we see other teams' decisions?",
     "Only via the Competitor Intelligence bar (synergy comparison). Specific decisions are private."),
    ("What does the Market Reality Feed tell us?",
     "Macro events, regulatory bulletins, and foreshadowing clues. R8 clue almost always reveals your pathway."),
    ("Does the SDG track affect our main score?",
     "Yes — M_SDG multiplies your entire Terminal Value. Perfect SDG (all A) = M_SDG = 1.26 (26% TV boost)."),
    ("What is the maximum possible score?",
     "TV = EBITDA × Exit × 2.07 × 1.26 = EBITDA × Exit × 2.61, vs. base 1.00. A 2.61× premium for best vs. worst."),
    ("What is Focus Mode?",
     "A deep-work overlay that hides non-essential UI elements for 5 minutes. Triggered by the Re-enter Focus Mode button. Useful during team deliberation."),
    ("Can we use the solo mode to practice?",
     "Yes — click START SOLO SESSION on the login page. You play all rounds against an AI competitor at your own pace."),
]
for q, a in faqs:
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.2)
    r1 = p.add_run(f"Q: {q}\n")
    r1.bold = True
    r1.font.size = Pt(10.5)
    r2 = p.add_run(f"A: {a}")
    r2.font.size = Pt(10.5)
    doc.add_paragraph()
divider(doc)

# ════════════════════════════════════════════════════════════════════════
# APPENDIX A
# ════════════════════════════════════════════════════════════════════════
doc.add_page_break()
add_heading(doc, "Appendix A — KPI Reference Table", 1)
add_table(doc,
    ["KPI", "Scope", "Start", "Range", "Critical Threshold"],
    [
        ["corporate_treasury", "Group", "$50M", "Unrestricted", "< $0 → Survival Mode"],
        ["group_reputation", "Group", "55", "0–100", "< 40 → Black Swan risk elevated"],
        ["synergy_multiplier", "Group", "1.0×", "0–2.0×", "> 1.3 → White Knight defence viable"],
        ["wacc / cost_of_capital", "Group", "~7%", "5%–20%+", "> 9% → WACC Penalty warning"],
        ["workforce_readiness", "Group", "50", "0–100", ">= 75 → Workforce Excellence M_R +0.10"],
        ["carbon_intensity", "Per BU", "12–72", ">= 0", "> 50 → Climate Black Swan elevated penalty"],
        ["social_license_score", "Per BU", "50", "0–100", "< 40 → Strike risk; < 75 → Instability Discount"],
        ["staff_burnout_index", "Per BU", "10", "0–100", "> 20 → OPEX quadratic penalty; > 70 → Revolt risk"],
        ["natural_capital_debt", "Per BU", "Varies", ">= 0", "Raises cost_of_debt 0.01% per unit"],
        ["governance_risk_score", "Per BU", "10–25", "0–100", "High → Greenwash probability; Litigation risk"],
        ["vrio_advantage", "Per BU", "0.80", "0–1.0", "Decays 2%/round unless reinvested"],
        ["sdg_impact_score", "Group (SDG track)", "0", "-11 to 105", "> 70 → Rep +2/round; < 40 → regulatory_ratchet"],
    ]
)

# ════════════════════════════════════════════════════════════════════════
# APPENDIX B
# ════════════════════════════════════════════════════════════════════════
doc.add_page_break()
add_heading(doc, "Appendix B — Flag Dependency Quick Reference", 1)
add_para(doc, "Flags are permanent boolean markers set by decisions. They carry consequences across rounds and into terminal valuation.", italic=True)
add_table(doc,
    ["Flag", "Set By", "Affects", "Effect"],
    [
        ["electronics_blindspot", "R1 Option A", "R4", "Doubles crisis severity 40→80"],
        ["deep_audit_completed", "R1 Option B", "R4", "Halves crisis severity 80→40"],
        ["materiality_aligned", "R2 Option A", "R10 M_R", "+0.10 Materiality Governance bonus"],
        ["early_decarboniser", "R3 Option A", "R7 Synergy", "+0.10 synergy multiplier bonus"],
        ["remediation_active", "R4 Option A", "Ongoing", "Prevents ongoing SLO erosion"],
        ["insurance_only", "R5 Option C", "R10 M_R", "BLOCKS +0.20 Resilience M_R bonus"],
        ["nature_based_resilience", "R5 Option B", "R10 M_R", "Enables Resilience M_R bonus"],
        ["planet_expendable", "R5 Shadow Board rejection", "R10 M_R", "-0.20 M_R (all pathways)"],
        ["ethical_ai_overhaul", "R6 Option B", "R10 M_R", "+0.15 Truth Premium M_R"],
        ["ai_monetised", "R6 Option A", "R7+", "EU AI Act costs from R7 onward"],
        ["synergy_unlock", "R7 Option C", "R10 M_R", "+0.15 Strategic Synergy M_R"],
        ["electronics_water_priority", "R8 Option B", "R10 M_R", "BLOCKS +0.20 Resilience M_R bonus"],
        ["community_fund", "R9 Option C", "R10 M_R", "+0.18 Community Champion M_R (x JT scaling)"],
        ["managed_transition", "R9 Option B", "R10 M_R", "+0.12 Just Transition M_R (x JT scaling)"],
        ["brsr_net_positive_dividend", "BRSR track Score >= 80", "R10 M_R", "+0.05 ESG Alpha Dividend M_R"],
    ]
)

# ════════════════════════════════════════════════════════════════════════
# APPENDIX C: GLOSSARY
# ════════════════════════════════════════════════════════════════════════
doc.add_page_break()
add_heading(doc, "Appendix C — Glossary of Key Terms", 1)
glossary = [
    ("Carbon Intensity (CI)", "Tonnes of CO2 equivalent per $1M of revenue. The primary carbon metric. Weighted by BU revenue for group-level reporting."),
    ("Carbon Tax", "Applied to total tCO2e at terminal valuation. Default $50/tonne; escalates 5% annually. Climate Black Swan pathway triples this rate."),
    ("CSRD", "Corporate Sustainability Reporting Directive — EU law requiring standardised sustainability reporting per ESRS standards."),
    ("Double Materiality", "Two-dimensional materiality test: financial materiality (ESG issues affecting the company) AND impact materiality (company affecting the world)."),
    ("EBITDA", "Earnings Before Interest, Taxes, Depreciation, and Amortisation. Primary earnings metric in terminal valuation."),
    ("ESG Alpha", "The excess return generated by superior ESG quality — captured via M_R premium above 1.0."),
    ("Exit Multiple", "Multiplier applied to EBITDA to derive enterprise value. Default 12x; dynamic WACC-linked range 6–18x."),
    ("Flag", "A permanent boolean state marker set by decisions. Cannot be unset by players."),
    ("Greenwashing", "Claiming environmental credentials without sufficient investment. Detected by the Greenwashing Engine; penalty: Rep -15, Auditor Hostile."),
    ("JT Scaling Factor", "Just Transition multiplier: min(1.5, 1.0 + HR_investment_rounds x 0.10). Rewards consistent HR investment."),
    ("M_R (Regenerative Multiple)", "ESG quality modifier on the exit multiple. Ranges 0–2.07. Determined by flags, KPI thresholds, and pathway bonuses."),
    ("M_SDG", "SDG multiplier on terminal value (Corporate SDG track only). M_SDG = 1.0 + (SDG_Score/100) x 0.25. Range: 0.97–1.26."),
    ("NCD (Natural Capital Debt)", "Unpriced environmental liabilities. Accumulate when green investments are deferred. Raises cost of debt by 0.01% per unit."),
    ("Scope 3", "Indirect emissions in a company's value chain (upstream and downstream). Typically 70–90% of total footprint."),
    ("SLO (Social Licence to Operate)", "Stakeholder trust and acceptance. Range 0–100. Below 75: Instability Discount on M_R. Below 40: strike risk."),
    ("Stakeholder Fatigue", "Trust recovery efficiency decreases after each crisis. Formula: efficiency = 1 / (1 + 0.3 x crisis_count)."),
    ("VRIO Advantage", "Competitive advantage based on Value, Rarity, Imitability, Organisation. Decays 2%/round unless reinvested."),
    ("WACC", "Weighted Average Cost of Capital. Affected by NCD, macro rate cycle, equity risk premium. Floor 5%, ceiling 20%+."),
]
for term, definition in glossary:
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.2)
    r1 = p.add_run(f"{term}: ")
    r1.bold = True
    r1.font.size = Pt(10.5)
    r2 = p.add_run(definition)
    r2.font.size = Pt(10.5)

# ════════════════════════════════════════════════════════════════════════
# APPENDIX D: BALANCE SHEET GUIDE
# ════════════════════════════════════════════════════════════════════════
doc.add_page_break()
add_heading(doc, "Appendix D — Balance Sheet & Statement of Financial Position Guide", 1)
add_para(doc, "This guide explains every element of the Statement of Financial Position (Balance Sheet) in the Muressons simulation, including the governing accounting standards and mathematical formulas in formatted mathematical symbols.", italic=True)

add_heading(doc, "D1.1 Non-Current Assets (Tangible & Intangible)", 2)

add_para(doc, "1. Property, Plant & Equipment (PPE) [IAS 16]", bold=True)
add_para(doc, "PPE represents the capitalized physical infrastructure of the Business Units (BUs). In the simulation, when players allocate CAPEX, 60% is capitalized as PPE, while the remaining 40% is expensed as Opex. Straight-line depreciation is applied at 10% annually (5% per 6-month round). Depreciation in a given round is applied only to the opening PPE balance (prior to new additions), per IAS 16 §55.")
add_para(doc, "Formula (LaTeX):")
add_formatted_math(doc, r"$$\text{PPE}_{\text{final}} = \text{PPE}_{\text{opening}} + (\text{CAPEX}_{\text{allocated}} \times 0.60) - (\text{PPE}_{\text{opening}} \times 0.05)$$")

add_para(doc, "2. Right-of-Use Assets (IFRS 16)", bold=True)
add_para(doc, "ROU Assets represent leased physical resources (e.g. office spaces, machinery). At initialization, it is seeded at 40% of revenue. It is amortized straight-line by 5% annually (2.5% per 6-month round).")
add_para(doc, "Formula (LaTeX):")
add_formatted_math(doc, r"$$\text{ROU}_{\text{final}} = \text{ROU}_{\text{opening}} \times (1 - 0.025)$$")

add_para(doc, "3. Inventory [IAS 2]", bold=True)
add_para(doc, "Inventory represents stockpiled goods, raw materials, and finished products. In Muressons, inventory is dynamically recalculated each round based on a 60-day stock level model of total operating expenses (acting as a proxy for the cost of goods sold).")
add_para(doc, "Formula (LaTeX):")
add_formatted_math(doc, r"$$\text{Inventory} = \frac{\text{Total OPEX}}{365} \times 60$$")

add_para(doc, "4. Brand Value [IAS 38]", bold=True)
add_para(doc, "Brand Value represents intangible corporate reputation. To prevent runaway compounding, the revaluation is calculated against a fixed brand base ($6.25M per BU, or $25.0M for a standard 4-BU group). It scales based on Group Reputation and the average Social License to Operate (SLO) score, subject to a hard floor of $1.0M.")
add_para(doc, "Formula (LaTeX):")
add_formatted_math(doc, r"$$\text{Brand Value} = \text{Brand Base} \times \left(\frac{\text{Group Reputation}}{50}\right) \times \sqrt{\frac{\text{Average SLO}}{50}}$$")

add_para(doc, "5. Intellectual Property (IP) [IAS 38]", bold=True)
add_para(doc, "Seeded at a flat $15.0M base plus $2.0M per BU ($23.0M for a standard 4-BU configuration). This remains flat unless impaired or increased by specific player decisions.")
add_para(doc, "Formula (LaTeX):")
add_formatted_math(doc, r"$$\text{IP} = \$15.0\text{M} + (N_{\text{BUs}} \times \$2.0\text{M})$$")

add_para(doc, "6. Goodwill [IAS 36]", bold=True)
add_para(doc, "Goodwill represents acquisition premiums, seeded at $2.5M per BU ($10.0M for 4 BUs). It is tested for impairment every 2 rounds (annual equivalent). Impairment is triggered if Group Reputation falls below 40 or EBITDA Margin falls below 10%, using a smooth continuous formula:")
add_para(doc, "Formula (LaTeX):")
add_formatted_math(doc, r"$$\text{Rep Impairment \%} = \max\left(0, \frac{40 - \text{Rep}}{200}\right)$$")
add_formatted_math(doc, r"$$\text{Margin Impairment \%} = \max\left(0, (0.10 - \text{EBITDA Margin}) \times 0.5\right)$$")
add_formatted_math(doc, r"$$\text{Total Impairment \%} = \min\left(0.30, \text{Rep Impairment \%} + \text{Margin Impairment \%}\right)$$")

add_para(doc, "7. Non-GAAP ESG Capitals [IAS 38 / <IR> Framework]", bold=True)
add_para(doc, "Internally generated intangibles like community goodwill or employee trust cannot be recognized on a GAAP balance sheet under IAS 38. They are disclosed separately as off-balance sheet disclosures under the Integrated Reporting <IR> Framework:")
add_bullet(doc, "Social Licence Capital:")
add_formatted_math(doc, r"$$\text{Social Licence Capital} = \text{Average SLO} \times \$200,000$$")
add_bullet(doc, "Reputation Capital:")
add_formatted_math(doc, r"$$\text{Reputation Capital} = \text{Group Reputation} \times \$300,000$$")

add_heading(doc, "D1.2 Current Assets", 2)

add_para(doc, "1. Cash & Equivalents", bold=True)
add_para(doc, "Money in bank accounts, synchronized directly with the Corporate Treasury engine.")

add_para(doc, "2. Trade Receivables [IFRS 9 / IFRS 15]", bold=True)
add_para(doc, "Outstanding customer payments, calculated via a Days Sales Outstanding (DSO) proxy that increases with Governance Risk.")
add_para(doc, "Formula (LaTeX):")
add_formatted_math(doc, r"$$\text{DSO Factor} = \min\left(0.25, 0.12 + 0.001 \times \text{Average Gov Risk}\right)$$")
add_formatted_math(doc, r"$$\text{Trade Receivables} = \text{Total Revenue} \times \text{DSO Factor}$$")

add_para(doc, "3. Prepayments", bold=True)
add_para(doc, "Advance payments for services/insurance, seeded at a flat $250K per BU ($1.0M for 4 BUs).")

add_heading(doc, "D1.3 Liabilities (Non-Current & Current)", 2)

add_para(doc, "1. Revolving Credit Facility", bold=True)
add_para(doc, "Long-term bank credit facility, seeded at $12.5M per BU ($50M for 4 BUs). Subject to covenant status.")

add_para(doc, "2. Green Bonds Outstanding", bold=True)
add_para(doc, "Debt issued to fund environmental projects, initialized at $0.0M and incremented by player decisions.")

add_para(doc, "3. Environmental Provisions [IAS 37]", bold=True)
add_para(doc, "Provision for future cleanup costs. Driven by Natural Capital Debt (NCD) and active remediation events, subject to an irreducible floor of $1.0M. Unlike a permanent ratchet, provisions can decrease when NCD drops (IAS 37 §59).")
add_para(doc, "Formula (LaTeX):")
add_formatted_math(doc, r"$$\text{Environmental Provision} = \max\left(\$1.0\text{M}, (\text{Average NCD} \times 5000) + (\text{Active Remediation Events} \times 2,000,000)\right)$$")

add_para(doc, "4. Decommissioning Obligations [IAS 37 / IFRIC 1]", bold=True)
add_para(doc, "Expected asset dismantlement costs, seeded at $750K per BU ($3.0M for 4 BUs). It accretes at a 3% annual discount rate (1.5% per 6-month round), with the accretion recognized as interest expense.")
add_para(doc, "Formula (LaTeX):")
add_formatted_math(doc, r"$$\text{Accretion Charge} = \text{Obligation}_{\text{opening}} \times 0.015$$")
add_formatted_math(doc, r"$$\text{Obligation}_{\text{final}} = \text{Obligation}_{\text{opening}} + \text{Accretion Charge}$$")

add_para(doc, "5. Lease Liabilities (IFRS 16)", bold=True)
add_para(doc, "Outstanding lease obligations, seeded at 35% of total revenue. It amortizes by 5% annually (2.5% per 6-month round).")
add_para(doc, "Formula (LaTeX):")
add_formatted_math(doc, r"$$\text{Lease Liability}_{\text{final}} = \text{Lease Liability}_{\text{opening}} \times 0.975$$")

add_para(doc, "6. Trade Payables", bold=True)
add_para(doc, "Owed supplier payments, scaled by operating expenses and Days Payable Outstanding (DPO).")
add_para(doc, "Formula (LaTeX):")
add_formatted_math(doc, r"$$\text{DPO Factor} = \min\left(0.18, 0.10 + 0.0005 \times \text{Average Gov Risk}\right)$$")
add_formatted_math(doc, r"$$\text{Trade Payables} = \text{Total OPEX} \times \text{DPO Factor}$$")

add_para(doc, "7. Tax Provisions [IAS 12]", bold=True)
add_para(doc, "Taxes owed on current-round profits (prepayments modeling).")
add_para(doc, "Formula (LaTeX):")
add_formatted_math(doc, r"$$\text{Tax Provision} = \max\left(0, \text{Gross Profit} \times 0.25 \times 0.20\right)$$")

add_heading(doc, "D1.4 Shareholders' Equity", 2)

add_para(doc, "1. Share Capital", bold=True)
add_para(doc, "Common stock invested at initialization, seeded at $7.5M per BU ($30.0M for 4 BUs).")

add_para(doc, "2. Other Reserves", bold=True)
add_para(doc, "Capital and hedging reserves, seeded at $1.25M per BU ($5.0M for 4 BUs).")

add_para(doc, "3. Retained Earnings", bold=True)
add_para(doc, "Derived as the closing residual balance to enforce the accounting identity $A = L + E$. Profitability is tracked via Net Income on the accrual-based Income Statement, with dividends deducted separately.")
add_para(doc, "Formula (LaTeX):")
add_formatted_math(doc, r"$$\text{Retained Earnings} = \text{Net Assets} - \text{Share Capital} - \text{Other Reserves}$$")
add_formatted_math(doc, r"$$\text{Net Income} = \text{Gross Profit} - \text{Interest Expense} - \text{Depreciation} - \text{Expensed CAPEX} - \text{Tax Charge}$$")

add_heading(doc, "D1.5 Key Ratios & Covenants", 2)

add_para(doc, "1. Debt / Equity Ratio", bold=True)
add_formatted_math(doc, r"$$\text{Debt / Equity} = \frac{\text{Total Liabilities}}{\text{Total Equity}}$$")

add_para(doc, "2. Net Debt / EBITDA Ratio", bold=True)
add_para(doc, "Measures leverage. Banks set a standard breach trigger at 3.5x. Under the simulation's rules, EBITDA adds back depreciation (D&A) to calculate true earnings, and WACC > 8% tightens the trigger by -0.25x per 1% excess.")
add_para(doc, "Formula (LaTeX):")
add_formatted_math(doc, r"$$\text{Total Debt} = \text{Revolving Credit} + \text{Green Bonds} + \text{Short-Term Debt}$$")
add_formatted_math(doc, r"$$\text{Net Debt} = \text{Total Debt} - \text{Cash}$$")
add_formatted_math(doc, r"$$\text{EBITDA} = \text{Gross Profit} + \text{Depreciation}$$")
add_formatted_math(doc, r"$$\text{Net Debt / EBITDA} = \frac{\text{Net Debt}}{\text{EBITDA}}$$")

add_para(doc, "3. Stranded Asset Exposure", bold=True)
add_para(doc, "Represents the value of PPE at risk from carbon transition and climate pathways (Carbon Tracker methodology).")
add_para(doc, "Formula (LaTeX):")
add_formatted_math(doc, r"$$\text{CI Risk} = \min\left(0.5, \frac{\text{Carbon Intensity Avg}}{200}\right)$$")
add_formatted_math(doc, r"$$\text{Total Risk} = \min(0.80, \text{CI Risk} + \text{Pathway Risk} + \text{Tipping Risk})$$")
add_formatted_math(doc, r"$$\text{Stranded Exposure} = \text{PPE} \times \text{Total Risk}$$")

# ── FINAL PAGE ────────────────────────────────────────────────────────────
doc.add_page_break()
footer_p = doc.add_paragraph()
footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
footer_run = footer_p.add_run(
    "Muressons Global Corporation — Student Simulation Manual | Version 10 | July 2026\n"
    "Platform: v4.12.0  |  Engine Modules: 30+  |  10 Main Rounds + 6 Side Tracks\n"
    "Maintained by the Muressons Simulation Engineering Team"
)
footer_run.font.size = Pt(9)
footer_run.italic = True
footer_run.font.color.rgb = RGBColor(0x78, 0x71, 0x6C)

# ── SAVE ─────────────────────────────────────────────────────────────────
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
doc.save(OUTPUT)
print("[OK] Saved:", OUTPUT)
word_count = sum(len(p.text.split()) for p in doc.paragraphs)
print(f"[INFO] Word count: ~{word_count}")
