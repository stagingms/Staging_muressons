"""Muressons Student Guide v2 — Part 1: Setup + Sections 1-6."""
from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
import os

IMG = os.path.join(os.path.dirname(__file__), "guide_images")
doc = Document()

# ── Global styles ──
style = doc.styles['Normal']
style.font.name = 'Calibri'; style.font.size = Pt(11)
for s in doc.styles:
    try: s.font.name = 'Calibri'
    except: pass

def H(t, lvl=1):
    h = doc.add_heading(t, lvl)
    for r in h.runs: r.font.color.rgb = RGBColor(0x1a,0x3c,0x6e)
    return h

def para(t, bold=False, italic=False, indent=False):
    p = doc.add_paragraph()
    r = p.add_run(t); r.bold = bold; r.italic = italic
    if indent: p.paragraph_format.left_indent = Inches(0.3)
    return p

def tip(label, text, color=(0x0a,0x6e,0x2a)):
    p = doc.add_paragraph()
    r = p.add_run(f"{label}: "); r.bold = True; r.font.color.rgb = RGBColor(*color)
    p.add_run(text)

def warn(text):
    tip("⚠️ Warning", text, (0xb9,0x1c,0x1c))

def formula(label, f):
    p = doc.add_paragraph()
    r = p.add_run(f"{label}: "); r.bold = True
    r2 = p.add_run(f); r2.font.name = 'Cambria Math'; r2.font.size = Pt(12)
    r2.font.color.rgb = RGBColor(0x8b,0x00,0x00)

def tbl(headers, rows):
    t = doc.add_table(rows=len(rows)+1, cols=len(headers))
    t.style = 'Light Grid Accent 1'; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j,h in enumerate(headers): t.rows[0].cells[j].text = h
    for i,row in enumerate(rows):
        for j,val in enumerate(row): t.rows[i+1].cells[j].text = str(val)
    return t

def img(name, width=Inches(6)):
    path = os.path.join(IMG, name)
    if os.path.exists(path):
        doc.add_picture(path, width=width)
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

def caption(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text); r.italic = True; r.font.size = Pt(9)
    r.font.color.rgb = RGBColor(0x66,0x66,0x66)

def bullet_list(items):
    for item in items:
        doc.add_paragraph(item, style='List Bullet')

# ═══════════════════════════════════════════════════════════════
#  TITLE PAGE
# ═══════════════════════════════════════════════════════════════
doc.add_paragraph(); doc.add_paragraph(); doc.add_paragraph()
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Muressons Global Corporation"); r.bold = True; r.font.size = Pt(32)
r.font.color.rgb = RGBColor(0x1a,0x3c,0x6e)

p2 = doc.add_paragraph(); p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
r2 = p2.add_run("Student & Player Guide"); r2.bold = True; r2.font.size = Pt(22)
r2.font.color.rgb = RGBColor(0x4a,0x4a,0x4a)

doc.add_paragraph()
p3 = doc.add_paragraph(); p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
r3 = p3.add_run("A Comprehensive Guide to the 10-Round\nESG Sustainability Strategy Simulation")
r3.font.size = Pt(14); r3.font.color.rgb = RGBColor(0x66,0x66,0x66)

doc.add_paragraph(); doc.add_paragraph()
p4 = doc.add_paragraph(); p4.alignment = WD_ALIGN_PARAGRAPH.CENTER
r4 = p4.add_run("Version 6.0 — Facilitator-Approved Edition")
r4.font.size = Pt(11); r4.italic = True
doc.add_page_break()

# ═══════════════════════════════════════════════════════════════
#  TABLE OF CONTENTS
# ═══════════════════════════════════════════════════════════════
H("Table of Contents")
toc = [
    "1.  Welcome & Introduction",
    "2.  Getting Started — Login & Interface",
    "3.  Your Company at a Glance",
    "4.  Understanding the Executive Cockpit",
    "5.  Key Performance Metrics Explained",
    "6.  Capital Allocation — The Investment Matrix",
    "7.  Decision Gates — Making Strategic Choices",
    "8.  The 10-Round Journey — Detailed Guide",
    "9.  How Decisions Connect — The Flag System",
    "10. Terminal Valuation — How You're Scored",
    "11. Company Archetypes — Your Final Profile",
    "12. Hidden Engines — What's Running Behind the Scenes",
    "13. Common Strategic Mistakes & How to Avoid Them",
    "14. The CEO Interview — Post-Game Assessment",
    "15. Strategic Playbook — Approaches & Considerations",
    "16. Quick Reference Glossary",
    "Appendix A: Formula Quick-Reference Card",
    "Appendix B: Frequently Asked Questions",
]
for item in toc:
    doc.add_paragraph(item, style='List Number')
doc.add_page_break()

# ═══════════════════════════════════════════════════════════════
#  SECTION 1: WELCOME
# ═══════════════════════════════════════════════════════════════
H("1. Welcome & Introduction")
doc.add_paragraph(
    "Welcome to Muressons Global Corporation — a multi-round strategic simulation that places "
    "you in the role of CEO of Muressons Corporation, a multinational conglomerate with four "
    "business units spanning Pharmaceuticals, Electronics, Consumer Goods, and Software."
)
doc.add_paragraph(
    "Over 10 strategic rounds — representing approximately 5 years of corporate stewardship — "
    "you will face escalating ESG (Environmental, Social, and Governance) crises, make capital "
    "allocation decisions under uncertainty, and navigate the tension between short-term financial "
    "performance and long-term enterprise sustainability. Every decision you make creates ripple "
    "effects that compound across future rounds."
)
H("What Makes This Simulation Unique?", 2)
doc.add_paragraph(
    "Unlike traditional business simulations that optimise for a single metric (e.g. profit), "
    "Muressons Global Corporation uses a multi-dimensional scoring engine with 20+ mathematical "
    "models running simultaneously. Your company is evaluated not just on financial returns, "
    "but on how you manage environmental debt, workforce welfare, community relations, and "
    "ethical governance. The simulation rewards systems thinking — the ability to see how "
    "decisions in one domain affect outcomes in another."
)
H("Learning Objectives", 2)
doc.add_paragraph(
    "By the end of this simulation, you should be able to:"
)
objectives = [
    "Apply the Double Materiality framework to real capital allocation decisions, understanding how financial impact and ESG impact must be considered simultaneously.",
    "Understand how ESG risks compound across interconnected business systems — a supply chain scandal doesn't just affect one unit, it propagates through the entire group.",
    "Navigate genuine trade-offs between financial performance and stakeholder welfare, recognising that 'winning' means balancing multiple competing objectives.",
    "Experience first-hand the consequences of short-term vs. long-term strategic thinking, seeing how early cost-saving decisions can create devastating downstream effects.",
    "Develop adaptive leadership skills under conditions of uncertainty, incomplete information, and crisis pressure.",
    "Articulate and defend a coherent strategic narrative that connects your decisions to outcomes across all 10 rounds.",
]
for obj in objectives:
    doc.add_paragraph(obj, style='List Bullet')

H("Important Ground Rules", 2)
bullet_list([
    "There are no 'right answers' — only trade-offs. The simulation is designed to surface genuine dilemmas, not test whether you can find the 'correct' option.",
    "Your decisions carry forward permanently. Flags set in Round 1 can unlock or block options in Round 10. You cannot undo past choices.",
    "The simulation includes stochastic (random) elements. Two teams making identical decisions may experience different outcomes due to climate events, market noise, and FX fluctuations.",
    "Collaboration and discussion within your team are encouraged. The best outcomes emerge from diverse perspectives and robust debate.",
    "Your facilitator may adjust crisis parameters, ending pathways, or difficulty settings. The experience may differ from what is described in this guide.",
])
doc.add_page_break()

# ═══════════════════════════════════════════════════════════════
#  SECTION 2: GETTING STARTED
# ═══════════════════════════════════════════════════════════════
H("2. Getting Started — Login & Interface")
H("Logging In", 2)
doc.add_paragraph(
    "When you first access the simulation, you will see the Command Access screen. This is "
    "your entry point into the Muressons world."
)
img("login_screen.png", Inches(5))
caption("Figure 2.1 — The Command Access (Login) Screen")
doc.add_paragraph()
doc.add_paragraph(
    "You have two options for accessing the simulation:"
)
H("Option 1: Join a Cohort (Multiplayer)", 3)
doc.add_paragraph(
    "If your facilitator has created a cohort session, you will need two pieces of information:"
)
bullet_list([
    "Executive Identifier — Your unique player ID (e.g. MUR-001). Your facilitator will assign this.",
    "Clearance Cipher — The session password shared by your facilitator.",
])
doc.add_paragraph(
    "Enter both credentials and click 'ESTABLISH LINK' to join the shared session. In cohort mode, "
    "your facilitator controls round pacing — rounds may unlock on a timer or be released manually."
)
H("Option 2: Solo Session", 3)
doc.add_paragraph(
    "Click 'START SOLO SESSION' to begin an individual game. In solo mode, you control your own "
    "pacing and can progress through all 10 rounds at your own speed. This is ideal for practice "
    "or individual assignments."
)
tip("Pro Tip", "If you get disconnected, your progress is saved automatically. Simply log back in with the same credentials to resume where you left off.")
doc.add_page_break()

# ═══════════════════════════════════════════════════════════════
#  SECTION 3: YOUR COMPANY
# ═══════════════════════════════════════════════════════════════
H("3. Your Company at a Glance")
doc.add_paragraph(
    "Muressons Corporation is a diversified conglomerate operating across four distinct "
    "Business Units (BUs). Each unit has different financial profiles, risk exposures, and "
    "ESG characteristics. Understanding these differences is critical to effective capital allocation."
)
H("Business Unit Profiles", 2)

H("💊 Pharmaceuticals (Pharma)", 3)
tbl(["Attribute","Value"],
    [["Starting Revenue","$18.0M"],["OPEX Base","$11.5M"],["Margin","36.1%"],
     ["Social License","55/100"],["Governance Risk","15%"],["Carbon Intensity","Moderate"]])
doc.add_paragraph(
    "Pharma is your most socially sensitive unit. It produces essential medicines, giving it a "
    "natural 'social license' advantage — but this also means any ethical failure here attracts "
    "disproportionate public scrutiny. Pharma is water-dependent, making it vulnerable to the "
    "Round 8 drought crisis. Its moderate margins mean it contributes reliably but isn't your "
    "highest earner."
)

H("⚡ Electronics", 3)
tbl(["Attribute","Value"],
    [["Starting Revenue","$16.5M"],["OPEX Base","$10.8M"],["Margin","34.5%"],
     ["Social License","48/100"],["Governance Risk","20%"],["Carbon Intensity","High"]])
doc.add_paragraph(
    "Electronics is your highest-revenue unit but also your most problematic. It has complex "
    "global supply chains prone to labour-rights issues (Round 4), the highest carbon intensity, "
    "and the worst governance risk score. The Round 1 audit decision directly determines whether "
    "Electronics' hidden risks are detected early or explode in Round 4."
)

H("🛒 Consumer Goods", 3)
tbl(["Attribute","Value"],
    [["Starting Revenue","$10.5M"],["OPEX Base","$7.8M"],["Margin","25.7%"],
     ["Social License","52/100"],["Governance Risk","10%"],["Carbon Intensity","Low-Moderate"]])
doc.add_paragraph(
    "Consumer Goods has the lowest margins but also the lowest governance risk. It's your 'safe' "
    "unit — unlikely to cause crises but also unlikely to drive breakthrough growth. Its market "
    "overlaps with Pharma, meaning the Revenue Cannibalization engine may trigger if one unit "
    "significantly outperforms the other."
)

H("💻 Software", 3)
tbl(["Attribute","Value"],
    [["Starting Revenue","$8.5M"],["OPEX Base","$4.2M"],["Margin","50.6%"],
     ["Social License","60/100"],["Governance Risk","8%"],["Carbon Intensity","Very Low"]])
doc.add_paragraph(
    "Software has the highest margins (>50%) and lowest carbon footprint, making it your most "
    "ESG-friendly unit. However, it is extremely talent-sensitive. When group reputation drops "
    "below 65, the Talent Brain-Drain Engine inflates Software's OPEX as top engineers leave "
    "for competitors. The Round 6 AI bias crisis directly targets this unit."
)

H("Group-Level Starting Conditions", 2)
tbl(["Metric","Starting Value","What It Means"],
    [["Corporate Treasury","$50.0M","Your initial cash reserves for investment"],
     ["Group Reputation","50/100","Neutral starting position — room to improve or decline"],
     ["Synergy Multiplier","1.08","Slight efficiency bonus from cross-BU integration"],
     ["Group EBITDA","$19.2M","Combined earnings across all four BUs"],
     ["Carbon Footprint","183 tCO₂e","Total group emissions baseline"],
     ["Cost of Capital","5%","Your borrowing rate (increases with environmental debt)"],
     ["Workforce Readiness","50/100","Neutral workforce competence level"],
     ["Competitor Intel","TIED (1.00×)","You start level with your NPC competitor"]])
doc.add_page_break()

# ═══════════════════════════════════════════════════════════════
#  SECTION 4: EXECUTIVE COCKPIT
# ═══════════════════════════════════════════════════════════════
H("4. Understanding the Executive Cockpit")
doc.add_paragraph(
    "The Executive Cockpit is your primary interface throughout the simulation. It provides "
    "a comprehensive view of your company's financial performance, ESG metrics, and strategic options."
)
img("cockpit.png", Inches(6.5))
caption("Figure 4.1 — The Executive Cockpit (Round 1 View)")
doc.add_paragraph()

H("Cockpit Layout — Key Areas", 2)

H("① Top Navigation Bar", 3)
doc.add_paragraph(
    "Shows the current round number, turn indicator, round theme, and narrative mode toggle. "
    "The round counter (R1/10) helps you track your position in the 10-round journey."
)

H("② Left Sidebar — Financial Dashboard", 3)
doc.add_paragraph(
    "Displays your four most critical financial metrics at a glance:"
)
bullet_list([
    "Treasury ($50.0M) — Your available cash. This is your strategic war chest.",
    "Green Fund ($0) — Earmarked ESG investment pool (grows through specific decisions).",
    "Reputation (50/100) — Your public perception score. Below 30 triggers distress mode.",
    "EBITDA ($19.2M) — Your combined earnings. The foundation of your terminal valuation.",
])
doc.add_paragraph(
    "Below the key metrics, you'll find the Stock Performance chart (tracking your share price "
    "over time) and the Group EBITDA trend chart."
)

H("③ Centre Panel — Mission Briefing & Tasks", 3)
doc.add_paragraph(
    "The centre panel contains the round's narrative briefing, pedagogical orientation tasks, "
    "and — most importantly — the Investment Matrix and Decision Gate. At the start of each "
    "round, you may need to complete prerequisite tasks (reading briefings, completing the "
    "Stakeholder Map, reading board member profiles) before the Decision Gate unlocks."
)

H("④ Right Sidebar — Intelligence & Actions", 3)
doc.add_paragraph(
    "Contains three key tools:"
)
bullet_list([
    "Simulation Resources — Links to documentation and reference materials.",
    "Competitor Intel — Shows whether you're ahead or behind the NPC competitor.",
    "Mailbox — Board member messages with strategic advice (read these carefully — they contain hints).",
    "Market Reality Feed — Real-time news items that may foreshadow future crises.",
    "Commit Decisions — The button that locks in your choices and advances to the next round.",
])
doc.add_paragraph()
doc.add_paragraph(
    "The readiness tracker at the bottom right shows your progress through the round's "
    "required steps: Brief → Decide → Allocate. All three must be completed before you "
    "can commit your decisions."
)
tip("Important", "The 'COMMIT DECISIONS' button is irreversible. Once you click it, your choices for this round are locked and the simulation engine processes your turn.")
doc.add_page_break()

# ═══════════════════════════════════════════════════════════════
#  SECTION 5: KEY METRICS
# ═══════════════════════════════════════════════════════════════
H("5. Key Performance Metrics — Detailed Explanations")
doc.add_paragraph(
    "Understanding each metric — what drives it up, what drives it down, and why it matters — "
    "is essential to making informed strategic decisions."
)

H("💰 Corporate Treasury", 2)
doc.add_paragraph(
    "Your treasury represents the total cash available for investment and operations. It is "
    "calculated each round as:"
)
formula("CSF Formula", "CSF = Σ(Revenueᵢ − OPEXᵢ) − Dividends_Paid")
doc.add_paragraph(
    "The Corporate Strategic Fund (CSF) is the net cash generated by your four business units "
    "after operating costs and dividend payments. This is the pool you allocate through the "
    "Investment Matrix each round."
)
para("What increases Treasury: Revenue growth, cost reduction through synergy, dividend cuts, asset sales.", indent=True)
para("What decreases Treasury: Crisis costs, strategic investments, high OPEX, loan interest.", indent=True)
warn("If your total capital expenditure exceeds 20% of your treasury, a short-term loan is triggered at 12% interest. If you need to invest more than your CSF allows, you can access Emergency Credit (up to 120% of CSF) — but at a 2% premium interest rate.")
doc.add_paragraph()
H("Danger Zone: Distress Mode", 3)
doc.add_paragraph(
    "If Treasury hits $0 AND Reputation drops below 30, your company enters the Turnaround "
    "Pathway — a 4-phase distress arc with escalating restrictions:"
)
tbl(["Phase","Entry Conditions","What Happens"],
    [["Crisis","Treasury ≤ $0 AND Rep < 30","All investment frozen (0% CapEx). Mᵣ capped at 0.60."],
     ["Stabilisation","Treasury > $0 AND Rep > 20","Investment capped at 50% of normal. Mᵣ capped at 0.80."],
     ["Recovery","Treasury > $10M AND Rep > 45","Full investment restored. Mᵣ cap raised to 1.20."],
     ["Exit","Treasury > $20M AND Rep > 55","Cap lifted. +0.10 Mᵣ bonus for successful turnaround."]])
doc.add_paragraph()

H("📊 Group Reputation (0–100)", 2)
doc.add_paragraph(
    "Reputation reflects how the market, media, and public perceive Muressons Corporation. "
    "It is affected by crisis responses, ethical decisions, and the Contagion Engine."
)
doc.add_paragraph(
    "The Contagion Engine uses a sigmoid (S-curve) function to model how crises spread across "
    "your business units. When a crisis hits one BU, the damage propagates non-linearly:"
)
formula("Contagion Model", "Group_Rep = Avg_BU_Rep − 50 × σ((severity − 30) / 15)")
doc.add_paragraph(
    "This means small crises (severity < 15) have minimal group impact, but medium crises "
    "(severity 20-40) cause rapid erosion, and severe crises (> 50) saturate the damage "
    "curve. The key insight: prevention is exponentially cheaper than cure."
)
para("Key Thresholds:", bold=True)
bullet_list([
    "Below 65: Talent Brain-Drain activates — Software and Healthcare OPEX inflates as top talent leaves.",
    "Below 30: Combined with Treasury ≤ $0, triggers Turnaround (Survival) mode.",
    "Above 80: Potential for premium employer bonuses and lower cost of capital.",
])

H("🤝 Social License to Operate (SLO) — Per BU (0–100)", 2)
doc.add_paragraph(
    "Social License measures community consent for your business operations. Unlike Reputation "
    "(which is group-wide), SLO is tracked per Business Unit. This is arguably the most "
    "important metric in the simulation because of the Instability Discount:"
)
warn("If your AVERAGE SLO across all BUs falls below 75 at Round 10, your entire terminal valuation receives a −0.40 Mᵣ penalty. This single penalty often outweighs ALL accumulated bonuses combined.")
doc.add_paragraph(
    "SLO is affected by workforce decisions (Round 9), community investment, HR investment, "
    "and crisis responses. BUs receiving zero investment lose 2% SLO per round through natural decay."
)

H("🌿 Natural Capital Debt (NCD)", 2)
doc.add_paragraph(
    "NCD represents your accumulated environmental liability — pollution, biodiversity loss, "
    "carbon emissions, and resource depletion. Unlike other metrics, NCD compounds with interest "
    "every round:"
)
formula("NCD Compounding", "NCD_{t+1} = NCD_t + (NCD_t × r)")
formula("Interest Rate", "r = Base_Rate + (NCD × 0.0001)")
doc.add_paragraph(
    "This creates an exponential curve: small NCD values grow slowly, but large values snowball "
    "rapidly. At NCD=100, the rate is ~6%. At NCD=500, it's ~10%. At NCD=1000, it's ~15%. "
    "The lesson: address environmental debt early before it becomes unmanageable."
)

H("📈 Carbon Intensity", 2)
doc.add_paragraph(
    "Carbon Intensity measures your emissions per $M revenue. At Round 10's Terminal Valuation, "
    "a carbon tax of $250/tonne CO₂e is applied directly to your EBITDA. Higher carbon intensity "
    "means a higher carbon tax bill, directly reducing your terminal value."
)
para("Reduction levers: Green technology investment, Nature-Based Solutions (R5), Circular Economy (R7), supply chain decarbonisation (R3).", indent=True)

H("🔥 Workforce Burnout (0–100) — Per BU", 2)
doc.add_paragraph(
    "Burnout tracks staff exhaustion across each business unit. It rises automatically by "
    "+3 points per round when no HR investment is made, and follows a quadratic OPEX penalty curve:"
)
formula("OPEX Penalty", "Penalty = ((Burnout − 20)²) × 0.000028125  [when Burnout > 20]")
doc.add_paragraph(
    "This means burnout below 20 has no penalty, but above 70 it creates severe OPEX inflation "
    "and dramatically increases strike probability. In Round 9, high burnout can trigger a "
    "workforce strike that zeros all revenue for the round."
)

H("⚙️ Workforce Readiness (0–100) — Global", 2)
doc.add_paragraph(
    "Workforce Readiness measures your employees' skills, training, and ability to execute "
    "strategic initiatives. Unlike Burnout (which is per-BU), Readiness is a global metric."
)
bullet_list([
    "High HR investment: +8 per round. Medium: +4. No investment: −5 (skills atrophy).",
    "Below 40: Strategic pillar effectiveness reduced by 20% — your investments are less impactful.",
    "Above 75: Unlocks +0.10 Mᵣ Workforce Excellence bonus at terminal valuation.",
    "Above 75 with low burnout: Additional bonuses in Stakeholder Revolt pathway.",
])
doc.add_page_break()

# ═══════════════════════════════════════════════════════════════
#  SECTION 6: INVESTMENT MATRIX
# ═══════════════════════════════════════════════════════════════
H("6. Capital Allocation — The Investment Matrix")
doc.add_paragraph(
    "The Investment Matrix is where you distribute your Corporate Strategic Fund across your "
    "four business units. This is the most tactically important decision you make each round."
)
img("investment_matrix.png", Inches(6))
caption("Figure 6.1 — The Investment Matrix showing all four BUs with allocation sliders")
doc.add_paragraph()

H("Reading the Investment Matrix", 2)
doc.add_paragraph(
    "The matrix header shows three critical numbers:"
)
bullet_list([
    "CSF Pool — The total cash available for investment this round (calculated from BU profits).",
    "Allocated — How much you've assigned so far across all BU sliders.",
    "Remaining — Unallocated funds. Note: unallocated funds are NOT saved — they are simply not invested.",
])
doc.add_paragraph(
    "Each BU card displays:"
)
bullet_list([
    "Revenue — Current round revenue for this unit.",
    "Allocation Slider — Drag to set investment amount ($0 to your remaining pool).",
    "OPEX Base — Operating costs. Investment reduces this through the Synergy Engine.",
    "Margin — Revenue minus OPEX as a percentage. Higher is better.",
    "Social License — This BU's community consent score (0-100).",
    "Governance Risk — This BU's regulatory/ethical risk percentage.",
    "Natural Capital Debt — Environmental liability accumulated by this BU.",
    "Investment Ratio — What percentage of the CSF pool is going to this BU.",
])

H("The Synergy Engine — How Investment Reduces Costs", 2)
doc.add_paragraph(
    "When you invest in a BU, its OPEX is reduced through the Synergy Engine. However, "
    "the relationship follows a square-root curve, creating diminishing returns:"
)
formula("Effective Ratio", "r_eff = √(Investment_Ratio) × 0.7")
formula("New OPEX", "OPEX_new = OPEX_old × (1 − r_eff × Synergy_Multiplier)")
doc.add_paragraph(
    "This means the first dollar invested in a BU is more impactful than the last. Going from "
    "0% to 25% allocation is more beneficial than going from 75% to 100%. The simulation "
    "rewards balanced, diversified investment rather than extreme concentration."
)

H("Investment Strategy Framework", 2)
tbl(["Strategy","How It Works","Risk"],
    [["Balanced (25% each)","Equal distribution across all 4 BUs","Prevents decay but limits breakthrough"],
     ["Focused (60/20/10/10)","Heavy investment in 1 BU","Tech Lock-In after 3 rounds; decay in others"],
     ["Triage (40/30/30/0)","Abandon weakest BU","Abandoned BU decays rapidly; Technical Debt penalty"],
     ["Responsive","Shift allocation based on round threats","Requires strong situational awareness"],
     ["ESG-Forward","Prioritise BUs by ESG exposure","May sacrifice short-term margin for Mᵣ bonuses"]])
doc.add_paragraph()
H("Critical Investment Rules", 2)
bullet_list([
    "Zero-Investment Decay: BUs receiving $0 investment lose 2% Reputation AND 2% Social License per round through natural entropy.",
    "Technical Debt: BUs with no investment for 2+ consecutive rounds incur an additional 4% OPEX penalty.",
    "Technology Lock-In: If the same BU receives the highest CAPEX for 3+ consecutive rounds, all other BUs lose 15% synergy efficiency.",
    "Emergency Credit: You can borrow up to 120% of your CSF pool — but at a 2% premium interest rate. A 🚨 warning appears when emergency credit is activated.",
    "Talent Allocation Pressure: BUs receiving less than 15% of total CAPEX incur a 2% OPEX surcharge from under-investment effects.",
])
tip("Strategic Advice", "A good default is to allocate at least some investment (≥15%) to every BU to prevent decay and Technical Debt penalties, then concentrate the remaining funds on the BU most relevant to the current round's crisis.")

# Save Part 1
out = os.path.join(os.path.dirname(__file__), "_student_guide_part1.docx")
doc.save(out)
print(f"Part 1 saved: {out}")
