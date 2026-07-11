"""Generate Student/Player Guide for Muressons Simulation."""
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os

doc = Document()
style = doc.styles['Normal']
style.font.name = 'Calibri'
style.font.size = Pt(11)

def H(text, level=1):
    h = doc.add_heading(text, level=level)
    for r in h.runs: r.font.color.rgb = RGBColor(0x1a,0x3c,0x6e)
    return h

def tip(label, text):
    p = doc.add_paragraph()
    r = p.add_run(f"{label}: "); r.bold = True; r.font.color.rgb = RGBColor(0x0a,0x6e,0x2a)
    p.add_run(text)

def warn(text):
    p = doc.add_paragraph()
    r = p.add_run("⚠️ "); r.bold = True
    r2 = p.add_run(text); r2.italic = True; r2.font.color.rgb = RGBColor(0xb9,0x1c,0x1c)

def formula(label, f):
    p = doc.add_paragraph()
    r = p.add_run(f"{label}: "); r.bold = True
    r2 = p.add_run(f); r2.font.name = 'Cambria Math'; r2.font.size = Pt(12)
    r2.font.color.rgb = RGBColor(0x8b,0x00,0x00)

def tbl(headers, rows):
    t = doc.add_table(rows=len(rows)+1, cols=len(headers))
    t.style = 'Light Grid Accent 1'
    for j,h in enumerate(headers): t.rows[0].cells[j].text = h
    for i,row in enumerate(rows):
        for j,val in enumerate(row): t.rows[i+1].cells[j].text = str(val)
    return t

# ═══ TITLE ═══
doc.add_paragraph(); doc.add_paragraph()
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Muressons Global Corporation"); r.bold = True; r.font.size = Pt(28)
r.font.color.rgb = RGBColor(0x1a,0x3c,0x6e)
p2 = doc.add_paragraph(); p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
r2 = p2.add_run("Student & Player Guide"); r2.bold = True; r2.font.size = Pt(20)
r2.font.color.rgb = RGBColor(0x4a,0x4a,0x4a)
p3 = doc.add_paragraph(); p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
p3.add_run("A 10-Round Sustainability Strategy Simulation").font.size = Pt(14)
doc.add_page_break()

# ═══ 1. WELCOME ═══
H("1. Welcome to Muressons Global Corporation")
doc.add_paragraph(
    "You are the newly appointed CEO of Muressons Corporation, a multinational conglomerate "
    "operating across four business units: Pharmaceuticals, Electronics, Consumer Goods, and Software. "
    "Over 10 rounds (representing 5 strategic years), you will navigate ESG crises, allocate capital, "
    "and make decisions that shape your company's terminal valuation and legacy."
)
doc.add_paragraph(
    "This is not a traditional business game. Every decision creates ripple effects across rounds. "
    "There are no 'right answers' — only trade-offs. Your goal is to maximise long-term enterprise "
    "value while maintaining your Social License to Operate and managing environmental debt."
)
H("Learning Objectives", 2)
for obj in [
    "Apply the Double Materiality framework to capital allocation decisions",
    "Understand how ESG risks compound across interconnected business systems",
    "Navigate trade-offs between financial performance and stakeholder welfare",
    "Experience the consequences of short-term vs. long-term strategic thinking",
    "Develop adaptive leadership skills under uncertainty and crisis pressure",
]:
    doc.add_paragraph(obj, style='List Bullet')
doc.add_page_break()

# ═══ 2. YOUR COMPANY ═══
H("2. Your Company at a Glance")
doc.add_paragraph("Muressons Corporation operates four distinct Business Units (BUs):")
tbl(["Business Unit","Strengths","Risks","Starting Revenue"],
    [["Pharmaceuticals","Stable margins, essential products","Water-dependent, regulatory exposure","$18M"],
     ["Electronics","High revenue, tech innovation","Supply chain complexity, carbon-intensive","$22M"],
     ["Consumer Goods","Brand loyalty, low governance risk","Thin margins, market overlap with Pharma","$15M"],
     ["Software","Highest margins, low carbon","Talent-sensitive, reputation-dependent","$20M"]])
doc.add_paragraph()
doc.add_paragraph("Starting Conditions:").bold = True
tbl(["Metric","Starting Value"],
    [["Corporate Treasury","~$38,000,000"],["Group Reputation","68/100"],
     ["Synergy Multiplier","1.08"],["Cost of Capital","5%"],["Workforce Readiness","50/100"]])
doc.add_page_break()

# ═══ 3. HOW TO PLAY ═══
H("3. How to Play — Round Structure")
doc.add_paragraph("Each round follows a consistent structure:")
for i, (phase, desc) in enumerate([
    ("📋 Briefing","Read the crisis scenario and understand what's at stake."),
    ("💰 Capital Allocation","Use the Investment Matrix to distribute your Corporate Strategic Fund across BUs."),
    ("🔀 Decision Gate","Choose Option A, B, or C in response to the round's crisis. Each has different costs, risks, and long-term consequences."),
    ("📊 Results","Review your Executive Cockpit to see how metrics changed. Check Treasury, Reputation, Social License, and Natural Capital Debt."),
    ("🔄 Next Round","Your decisions carry forward. Flags set in early rounds unlock or block options in later rounds."),
], 1):
    doc.add_paragraph(f"Step {i}: {phase} — {desc}")

tip("Pro Tip", "Read the briefing carefully before allocating capital. The crisis context should inform your investment priorities.")
doc.add_page_break()

# ═══ 4. KEY METRICS ═══
H("4. Key Metrics — Your Dashboard")
doc.add_paragraph("Monitor these six critical metrics throughout the simulation:")
tbl(["Metric","What It Measures","Why It Matters","Danger Zone"],
    [["Corporate Treasury","Cash available for investment","Funds your decisions; goes negative = distress","< $0"],
     ["Group Reputation","Public perception (0-100)","Affects talent retention, strike risk, terminal value","< 30"],
     ["Social License (SLO)","Community consent (0-100)","Below 75 triggers Instability Discount (-0.40 Mᵣ)","< 50"],
     ["Natural Capital Debt","Environmental liability","Compounds with interest every round","> 500"],
     ["Carbon Intensity","Emissions per $M revenue","Affects carbon tax at terminal valuation","> 50"],
     ["Workforce Burnout","Staff exhaustion (0-100)","Increases OPEX, strike probability","> 70"]])
doc.add_paragraph()
warn("If Treasury hits $0 AND Reputation drops below 30, your company enters the Turnaround Pathway — a 3-phase distress arc with severe restrictions on spending.")
doc.add_page_break()

# ═══ 5. CAPITAL ALLOCATION ═══
H("5. Capital Allocation — The Investment Matrix")
doc.add_paragraph(
    "Each round, your Corporate Strategic Fund (CSF) is calculated from business unit profits:"
)
formula("CSF Formula", "CSF = Σ(Revenueᵢ − OPEXᵢ) − Dividends")
doc.add_paragraph(
    "You distribute this fund across your four BUs using investment sliders (0-100%). "
    "Higher investment in a BU reduces its OPEX through the Synergy Engine, but with diminishing returns."
)
formula("OPEX Reduction", "OPEX_new = OPEX_old × (1 − √(ratio) × 0.7 × Synergy)")
doc.add_paragraph()
H("Investment Strategy Tips", 2)
for t in [
    "Spreading investment evenly prevents Technical Debt penalties but limits breakthrough gains.",
    "Concentrating on one BU for 3+ rounds triggers Technology Lock-In — other BUs lose 15% synergy efficiency.",
    "BUs receiving zero investment decay 2% per round in Reputation and Social License.",
    "Emergency Credit: If you need to invest more than your CSF allows, you can borrow up to 120% — but at a 2% premium interest rate.",
]:
    doc.add_paragraph(t, style='List Bullet')
doc.add_page_break()

# ═══ 6. ROUND BY ROUND ═══
H("6. Round-by-Round Guide")
rounds = [
    ("1","Foundations","ESG Baseline Assessment","📋",
     "Choose the depth of your initial ESG audit. A deep audit costs $3M but uncovers hidden risks in Electronics that protect you in Round 4.",
     "Choosing a surface-level scan creates a 'blindspot' that DOUBLES the crisis severity in Round 4."),
    ("2","Double Materiality","Budget Allocation","📊",
     "Align your investments with the Double Materiality framework — prioritising areas with both high financial AND high ESG impact.",
     "Full alignment earns a +0.10 Mᵣ governance bonus at terminal valuation."),
    ("3","Scope 3 Emissions","Supply Chain Decarbonisation","🏭",
     "Regulators signal mandatory Scope 3 disclosures. Your supply chain footprint is 4× direct emissions.",
     "Early decarbonisation (Option A) gives a strategic advantage in Round 7's circular economy transition."),
    ("4","Contagion","Reputation Crisis","🔥",
     "An Electronics supply chain scandal goes viral. The Contagion Engine propagates damage across ALL BUs using a sigmoid curve.",
     "If you skipped the deep audit in R1, crisis severity DOUBLES from 40 to 80."),
    ("5","Climate","Physical Risk Event","🌪️",
     "A Category 4 cyclone threatens your manufacturing corridor. Base damage: $12M. A dice roll determines if it strikes.",
     "Choosing 'Insurance Only' blocks the +0.20 Resilience Bonus at terminal valuation. Nature-based solutions have a 25% chance of partial failure."),
    ("6","AI Bias","Algorithmic Ethics","🤖",
     "Your Software BU's AI recruitment tool is found to discriminate. You must decide: monetise it, fix it ethically, or quietly patch it.",
     "The Ethical AI Overhaul (Option B) unlocks the +0.15 Truth Premium on your Regenerative Multiple."),
    ("7","Circularity","Circular Economy","♻️",
     "EU regulations mandate 60% waste diversion. Non-compliance fine: $15M.",
     "The Waste-to-Energy option (C) unlocks the Synergy Multiplier (+0.30 Mᵣ) AND enables Option A in Round 10."),
    ("8","Blue Stress","Water Scarcity","🌊",
     "A drought depletes the watershed serving Pharma and Electronics. Government rationing is imminent.",
     "Prioritising one BU over others devastates Social License for the neglected units (-25 SLO)."),
    ("9","Just Transition","Workforce Justice","✊",
     "Decarbonisation requires closing 3 legacy factories. 2,000 jobs at risk. Community protests escalating.",
     "Immediate closure with low Social License triggers a 50-75% chance of a STRIKE that zeros all revenue for the round."),
    ("10","Grand Finale","Terminal Valuation","🏛️",
     "An activist investor demands restructuring. Your cumulative decisions determine your final company archetype and valuation.",
     "Option A (Resist & Integrate) is LOCKED unless your Synergy Score exceeds 80 — rewarding consistent long-term strategy."),
]
for rn, title, theme, icon, desc, insight in rounds:
    H(f"Round {rn}: {title} — {theme} {icon}", 2)
    doc.add_paragraph(desc)
    tip("Key Insight", insight)
    doc.add_paragraph()
doc.add_page_break()

# ═══ 7. FLAG DEPENDENCIES ═══
H("7. How Decisions Connect — The Flag System")
doc.add_paragraph(
    "Your choices set hidden 'flags' that unlock or block options in future rounds. "
    "This is the simulation's core systems thinking mechanic — early decisions compound."
)
tbl(["Early Decision","Flag Set","Later Impact"],
    [["R1: Surface Scan","electronics_blindspot","R4 crisis severity DOUBLES (40→80)"],
     ["R2: Full Alignment","materiality_aligned","+0.10 Mᵣ governance bonus at R10"],
     ["R3: Rapid Switch","early_decarboniser","+0.10 synergy multiplier in R7"],
     ["R5: Insurance Only","insurance_only","BLOCKS +0.20 Resilience bonus at R10"],
     ["R6: Ethical Overhaul","ethical_ai_overhaul","+0.15 Truth Premium Mᵣ at R10"],
     ["R7: Waste-to-Energy","synergy_unlock","+0.30 Synergy Mᵣ + enables R10 Option A"],
     ["R8: Prioritise Electronics","electronics_water_priority","BLOCKS +0.20 Resilience bonus at R10"],
     ["R9: Community Fund","community_fund","+0.18 Community Champion Mᵣ (×JT scaling)"]])
doc.add_paragraph()
warn("Two flags (insurance_only and electronics_water_priority) permanently BLOCK the Resilience Bonus. These cannot be reversed.")
doc.add_page_break()

# ═══ 8. TERMINAL VALUATION ═══
H("8. Terminal Valuation — How You're Scored")
doc.add_paragraph("At Round 10, your company's final value is calculated:")
formula("EBITDA 2050", "EBITDA = Σ(Revenueᵢ − OPEXᵢ) − (tCO₂e × Carbon Tax)")
formula("Terminal Value", "TV = EBITDA × Exit Multiple (12×) × Mᵣ")
doc.add_paragraph()
doc.add_paragraph("The Regenerative Multiple (Mᵣ) is the key differentiator:").bold = True
tbl(["Component","Bonus","How to Earn It"],
    [["Base","1.00","Always applied"],
     ["Materiality Governance","+0.10","Full materiality alignment in R2"],
     ["Synergy Excellence","+0.30","Waste-to-Energy in R7 + Synergy ≥ 80"],
     ["Resilience Champion","+0.20","Avoid insurance-only (R5) and water-priority (R8)"],
     ["Truth Premium","+0.15","Ethical AI Overhaul in R6"],
     ["Community Champion","+0.18","Community Investment Fund in R9"],
     ["Workforce Excellence","+0.10","Workforce Readiness ≥ 75"],
     ["Wellbeing Champion","+0.05","Average Burnout < 20"],
     ["Instability Discount","−0.40","PENALTY if average SLO < 75"]])
doc.add_paragraph()
formula("Maximum Mᵣ", "2.08 (requires optimal play across all 10 rounds)")
doc.add_page_break()

# ═══ 9. ARCHETYPES ═══
H("9. Company Archetypes — Your Final Profile")
doc.add_paragraph("Your Mᵣ determines which archetype you receive:")
tbl(["Archetype","Mᵣ Range","What It Means"],
    [["🌱 Regenerative Titan","≥ 1.80","Exceptional — you built a truly sustainable enterprise"],
     ["🏦 De-risked Safe-Haven","1.20 – 1.79","Strong — solid ESG integration with good financial returns"],
     ["⚠️ Fragile Giant","0.80 – 1.19","Average — profitable but vulnerable to future ESG shocks"],
     ["💀 Stranded Relic","< 0.80","Poor — the market sees your company as a declining asset"],
     ["🔧 Turnaround Manager","Survival Mode","You entered distress but may have recovered"]])
doc.add_paragraph()
tip("Goal", "Aim for De-risked Safe-Haven (Mᵣ ≥ 1.20) as a realistic target. Regenerative Titan requires near-perfect play.")
doc.add_page_break()

# ═══ 10. HIDDEN ENGINES ═══
H("10. Hidden Engines — What's Running Behind the Scenes")
doc.add_paragraph("The simulation runs 20+ mathematical engines each round. Key ones to be aware of:")
tbl(["Engine","What It Does","Your Lever"],
    [["Synergy Engine","Investment reduces OPEX (diminishing returns)","Invest consistently"],
     ["Contagion Engine","Crises spread across all BUs (sigmoid curve)","Maintain reputation above 50"],
     ["Natural Capital Debt","Environmental debt compounds with interest","Reduce NCD early — it snowballs"],
     ["Talent Brain-Drain","Low reputation inflates Software/Healthcare OPEX","Keep Group Reputation above 65"],
     ["Burnout Accumulation","Staff exhaustion rises +3/round without HR investment","Invest in HR pillars regularly"],
     ["Stakeholder Fatigue","Trust recovery weakens after each crisis","Avoid repeated crises"],
     ["Revenue Cannibalization","Dominant BUs steal revenue from overlapping units","Balance BU growth"],
     ["Macro Inflation","OPEX rises 2.5% every round automatically","Invest just to tread water"],
     ["FX Risk","Currency movements affect export-heavy BUs (±5%)","Diversify revenue exposure"],
     ["Technical Debt","2+ rounds of zero investment → 4% OPEX penalty","Never completely neglect a BU"]])
doc.add_page_break()

# ═══ 11. COMMON MISTAKES ═══
H("11. Common Mistakes — Learn from Others")
for i, (mistake, why, fix) in enumerate([
    ("Skipping the Deep Audit in R1",
     "The $3M seems expensive early on, but the blindspot doubles R4 crisis damage — often costing $10M+ in reputation recovery.",
     "Invest in governance infrastructure early. It's cheaper than crisis management."),
    ("Ignoring Social License",
     "SLO below 75 triggers a −0.40 Instability Discount on your entire terminal value. This single penalty often outweighs all other bonuses combined.",
     "Monitor SLO every round. Invest in community and workforce welfare."),
    ("Choosing Insurance Only in R5",
     "It's the cheapest option ($2M vs $8M) but permanently blocks the +0.20 Resilience Bonus — a $50M+ impact on terminal value.",
     "Think about terminal value, not just this round's treasury."),
    ("Neglecting HR Investment",
     "Burnout rises +3 per round automatically. By Round 7, workforce exhaustion triggers OPEX penalties and increases strike probability.",
     "Allocate to HR pillars in at least 5 of 10 rounds."),
    ("Over-concentrating Investment",
     "Investing heavily in one BU for 3+ rounds triggers Technology Lock-In, reducing synergy efficiency for all other BUs by 15%.",
     "Rotate investment focus. Spread capital to prevent decay and lock-in."),
], 1):
    H(f"Mistake {i}: {mistake}", 2)
    doc.add_paragraph(f"Why it hurts: {why}")
    tip("Fix", fix)
doc.add_page_break()

# ═══ 12. CEO INTERVIEW ═══
H("12. Post-Game: The CEO Interview")
doc.add_paragraph(
    "After Round 10, you may be invited to a reflective interview with the CEO of Muressons. "
    "This is a 5-question conversation assessing your strategic thinking across six competency dimensions:"
)
tbl(["Dimension","What's Assessed"],
    [["Strategic Thinking","Long-term vs short-term trade-off awareness"],
     ["Stakeholder Empathy","Ability to articulate competing stakeholder interests"],
     ["Financial Acumen","Understanding of treasury, EBITDA, and Mᵣ mechanics"],
     ["Ethical Reasoning","Moral framework sophistication"],
     ["Systems Thinking","Understanding of cross-round flag dependencies"],
     ["Adaptive Leadership","Willingness to change strategy based on new information"]])
doc.add_paragraph()
doc.add_paragraph("Your final score blends two sources equally:").bold = True
formula("Final Score", "S = 0.5 × S_simulation + 0.5 × S_interview")
doc.add_paragraph(
    "This means you cannot 'game' the system through either pure metric optimisation OR "
    "interview preparation alone. Both your actions and your reflections matter."
)
doc.add_page_break()

# ═══ 13. STRATEGIC CHEAT SHEET ═══
H("13. Strategic Cheat Sheet")
doc.add_paragraph("A quick-reference guide for maximising your terminal value:")
tbl(["Round","Recommended Focus","Key Action"],
    [["R1","Governance","Choose Deep Forensic Audit (Option B)"],
     ["R2","Materiality","Full Materiality Alignment (Option A)"],
     ["R3","Decarbonisation","Green Bond or Rapid Switch (A or B)"],
     ["R4","Crisis Response","Full Transparency (Option A) if budget allows"],
     ["R5","Climate Resilience","Nature-Based Solutions (B) or Hard Engineering (A)"],
     ["R6","Ethics","Ethical AI Overhaul (Option B)"],
     ["R7","Circularity","Waste-to-Energy (C) for Synergy unlock"],
     ["R8","Water","Water Efficiency for All (A) — protect SLO"],
     ["R9","Just Transition","Community Fund (C) or Managed Transition (B)"],
     ["R10","Endgame","Resist & Integrate (A) if Synergy ≥ 80"]])
doc.add_paragraph()
warn("This cheat sheet shows ONE optimal pathway. The simulation rewards genuine strategic thinking — not memorisation. Your facilitator may change crisis parameters.")
doc.add_page_break()

# ═══ 14. GLOSSARY ═══
H("14. Quick Glossary")
tbl(["Term","Definition"],
    [["BU","Business Unit — one of your four operating divisions"],
     ["CAPEX","Capital Expenditure — money invested in BU improvements"],
     ["OPEX","Operating Expenditure — ongoing costs to run a BU"],
     ["CSF","Corporate Strategic Fund — your investable cash pool each round"],
     ["SLO","Social License to Operate — community consent for your operations"],
     ["NCD","Natural Capital Debt — accumulated environmental liability"],
     ["Mᵣ","Regenerative Multiple — the sustainability-adjusted valuation multiplier"],
     ["EBITDA","Earnings Before Interest, Tax, Depreciation & Amortisation"],
     ["Terminal Value","Final company valuation at Round 10 (EBITDA × 12 × Mᵣ)"],
     ["Contagion","Crisis damage spreading from one BU to the entire group"],
     ["Synergy","Cross-BU efficiency gains from coordinated investment"],
     ["VRIO","Value, Rarity, Imitability, Organisation — competitive advantage framework"],
     ["Carbon Tax","$250/tonne CO₂e applied at terminal valuation"],
     ["Flag","A hidden marker set by your decisions that affects future rounds"],
     ["Archetype","Your final company profile based on Mᵣ score"]])
doc.add_paragraph()
doc.add_paragraph()
p_end = doc.add_paragraph()
p_end.alignment = WD_ALIGN_PARAGRAPH.CENTER
r_end = p_end.add_run("Good luck, CEO. The future of Muressons is in your hands. 🌍")
r_end.bold = True; r_end.font.size = Pt(14)
r_end.font.color.rgb = RGBColor(0x1a,0x3c,0x6e)

out = os.path.join(os.path.dirname(__file__), "Muressons_Student_Guide.docx")
doc.save(out)
print(f"Saved: {out}")
