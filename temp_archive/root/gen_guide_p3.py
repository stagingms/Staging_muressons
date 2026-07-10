"""Part 3: Sections 12-16 + Appendices."""
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os
doc = Document()
style = doc.styles['Normal']; style.font.name = 'Calibri'; style.font.size = Pt(11)
def H(t,l=1):
    h=doc.add_heading(t,l)
    for r in h.runs: r.font.color.rgb=RGBColor(0x1a,0x3c,0x6e)
def tip(l,t): p=doc.add_paragraph(); r=p.add_run(f"{l}: "); r.bold=True; r.font.color.rgb=RGBColor(0x0a,0x6e,0x2a); p.add_run(t)
def warn(t): p=doc.add_paragraph(); r=p.add_run("⚠️ "); r.bold=True; r2=p.add_run(t); r2.italic=True; r2.font.color.rgb=RGBColor(0xb9,0x1c,0x1c)
def formula(l,f): p=doc.add_paragraph(); r=p.add_run(f"{l}: "); r.bold=True; r2=p.add_run(f); r2.font.name='Cambria Math'; r2.font.size=Pt(12); r2.font.color.rgb=RGBColor(0x8b,0,0)
def tbl(h,rows):
    t=doc.add_table(rows=len(rows)+1,cols=len(h)); t.style='Light Grid Accent 1'
    for j,v in enumerate(h): t.rows[0].cells[j].text=v
    for i,row in enumerate(rows):
        for j,v in enumerate(row): t.rows[i+1].cells[j].text=str(v)
def bl(items):
    for i in items: doc.add_paragraph(i, style='List Bullet')

# ═══ 12. HIDDEN ENGINES ═══
H("12. Hidden Engines — What's Running Behind the Scenes")
doc.add_paragraph("The simulation runs 20+ mathematical engines simultaneously each round. While you don't need to know the exact formulas, understanding what these engines do helps you anticipate consequences and make better decisions.")
H("Financial Engines",2)
tbl(["Engine","What It Does","Your Lever","Why It Matters"],
    [["Synergy Engine","Investment reduces OPEX via √ curve","Invest consistently across BUs","Diminishing returns — first dollar most valuable"],
     ["Natural Capital Debt","Environmental debt compounds with interest each round","Reduce NCD early — it snowballs exponentially","At NCD=500, interest rate hits 10%"],
     ["Macro Inflation","OPEX rises 2.5% every round automatically","Invest just to tread water","Without investment, BUs slowly become unprofitable"],
     ["Cash Conversion","Governance risk reduces revenue collection efficiency","Lower governance risk scores","High gov risk means you collect less of your revenue"],
     ["Dividend Ratchet","Cutting dividends >20% triggers -5 reputation penalty","Maintain steady dividends","Markets punish inconsistency"],
     ["FX Risk","Currency movements affect export-heavy BUs (±5% random)","Diversify revenue exposure","Software 80%, Electronics 75%, Pharma 60%, Consumer 40% exposed"]])
H("ESG & Governance Engines",2)
tbl(["Engine","What It Does","Your Lever","Why It Matters"],
    [["Contagion Engine","Crises spread across all BUs via sigmoid curve","Maintain reputation above 50","Non-linear: medium crises cause the most damage"],
     ["Talent Brain-Drain","Low reputation inflates Software/Healthcare OPEX","Keep Group Reputation above 65","Top talent leaves when reputation falls"],
     ["Burnout Accumulation","Staff burnout rises +3/round without HR investment","Invest in HR pillars regularly","Quadratic OPEX penalty above burnout=20"],
     ["Stakeholder Fatigue","Trust recovery weakens after each crisis","Avoid repeated crises","Each crisis makes the next harder to recover from"],
     ["ESG Greenwashing","Mismatch between ESG claims and investment triggers SLO penalty","Back your ESG choices with actual investment","Choosing 'green' options without investing = -8 SLO"],
     ["Technical Debt","2+ rounds of zero investment → 4% OPEX penalty","Never completely neglect a BU","Accumulated neglect creates structural inefficiency"]])
H("Competitive & Market Engines",2)
tbl(["Engine","What It Does","Your Lever","Why It Matters"],
    [["Revenue Cannibalization","Dominant BUs steal revenue from overlapping units","Balance BU growth","Triggers when BU revenue > 115% of group average"],
     ["Technology Lock-In","Same BU getting highest CAPEX 3+ rounds → 15% synergy penalty for others","Rotate investment focus","Concentration creates rigidity"],
     ["Competitive NPC","NPC competitor grows 3%/round automatically","Outperform the baseline","Your relative performance affects market perception"],
     ["Supply Chain Contagion","Other BUs' governance risk creates OPEX surcharge","Reduce governance risk broadly","Interconnected supply chains share risk"],
     ["Talent Allocation","BUs receiving <15% of total CAPEX incur 2% OPEX surcharge","Allocate at least 15% to each BU","Under-investment creates workforce pressure"],
     ["Execution Overrun","CAPEX above $3M per BU has 25% chance of 15% cost overrun","Be cautious with very large investments","Big bets carry hidden execution risk"]])
doc.add_page_break()

# ═══ 13. COMMON MISTAKES ═══
H("13. Common Strategic Mistakes & How to Avoid Them")
doc.add_paragraph("These are the five most frequent errors observed across hundreds of simulation sessions. Each represents a systematic bias that the simulation is designed to surface and correct.")

H("Mistake 1: Skipping the Deep Audit in Round 1",2)
doc.add_paragraph("The Psychology: The $3M cost seems excessive when you have $50M in treasury and many rounds ahead. Why spend money on an audit when you could invest in growth?")
doc.add_paragraph("The Reality: The 'electronics_blindspot' flag doubles R4 crisis severity from 40 to 80. At severity 80, the sigmoid contagion function saturates — meaning ALL BUs suffer near-maximum reputation damage. The typical cost of recovering from a severity-80 crisis is $15-25M in treasury plus months of reputation recovery. The $3M audit is the best ROI investment in the entire simulation.")
tip("Lesson","Governance infrastructure is an investment, not a cost. The cheapest option in the first round is often the most expensive option in the fourth.")

H("Mistake 2: Ignoring Social License Throughout",2)
doc.add_paragraph("The Psychology: SLO seems like a 'soft' metric compared to treasury and EBITDA. Players focus on financial performance and treat SLO as secondary.")
doc.add_paragraph("The Reality: The Instability Discount (-0.40 Mᵣ) triggers when average SLO falls below 75 at Round 10. Since Mᵣ is multiplicative with EBITDA and the exit multiple, this single penalty can reduce your terminal value by 20-30%. No combination of financial performance bonuses can fully offset it.")
tip("Lesson","Social License is not optional. Monitor it every round and invest in community/workforce welfare to maintain it above 75.")

H("Mistake 3: Choosing Insurance Only in Round 5",2)
doc.add_paragraph("The Psychology: It costs $2M vs $5-8M for the alternatives. Your treasury is probably tight after R4's crisis costs. Insurance seems like the rational, risk-managed choice.")
doc.add_paragraph("The Reality: The 'insurance_only' flag permanently blocks the +0.20 Resilience Champion bonus. At a 12× exit multiple with a typical EBITDA of $20-30M, that 0.20 Mᵣ difference translates to $48-72M in terminal value. You 'saved' $6M to lose $50M+.")
tip("Lesson","Always evaluate decisions against their terminal valuation impact, not just their immediate treasury cost.")

H("Mistake 4: Neglecting HR Investment Across Rounds",2)
doc.add_paragraph("The Psychology: HR investment doesn't produce visible short-term results. There's no immediate revenue boost or OPEX reduction that you can point to.")
doc.add_paragraph("The Reality: Burnout rises +3/round automatically without HR investment. By Round 7, burnout reaches 50+, triggering significant OPEX penalties via the quadratic curve. By Round 9, high burnout dramatically increases strike probability — a strike zeros ALL revenue for the round. Additionally, Workforce Readiness falls to below 40, reducing all strategic pillar effectiveness by 20%. Finally, the JT scaling factor for R9's Community Champion bonus requires sustained HR investment to be maximised.")
tip("Lesson","Allocate to HR pillars in at least 5 of 10 rounds. The cost of prevention is a fraction of the cost of a strike or burnout-driven OPEX explosion.")

H("Mistake 5: Over-Concentrating Investment in One BU",2)
doc.add_paragraph("The Psychology: Software has 50% margins. Why not pour everything into your highest-performing unit?")
doc.add_paragraph("The Reality: Three penalties trigger simultaneously: (1) Technology Lock-In after 3 rounds reduces other BUs' synergy by 15%, (2) neglected BUs decay 2%/round in Rep and SLO, (3) Technical Debt adds 4% OPEX to any BU with zero investment for 2+ rounds. The compounding effect is severe — by Round 8, your neglected BUs are dragging down group averages enough to trigger the Instability Discount.")
tip("Lesson","Diversify. Allocate at least 15% to every BU to prevent decay, then concentrate remaining funds on the round's strategic priority.")
doc.add_page_break()

# ═══ 14. CEO INTERVIEW ═══
H("14. The CEO Interview — Post-Game Assessment")
doc.add_paragraph("After completing Round 10, you may be invited to a reflective CEO interview — a 5-question AI-facilitated conversation that assesses your strategic thinking across six competency dimensions.")
H("The Six Competency Dimensions",2)
tbl(["Dimension","What's Assessed","Data Source","Interview Focus"],
    [["Strategic Thinking","Long-term vs short-term trade-off awareness","Mᵣ score","Can you articulate WHY you made each trade-off?"],
     ["Stakeholder Empathy","Ability to balance competing interests","SLO + Burnout","Do you understand how your decisions affected communities and workers?"],
     ["Financial Acumen","Understanding of value creation mechanics","Treasury + EBITDA","Can you explain the financial logic behind your investment strategy?"],
     ["Ethical Reasoning","Moral framework sophistication","Decision flags","How do you resolve genuine ethical dilemmas (e.g., R6 AI bias)?"],
     ["Systems Thinking","Understanding cross-round dependencies","Synergy + VRIO","Can you trace how early decisions cascaded to later outcomes?"],
     ["Adaptive Leadership","Willingness to change strategy","WR + HR rounds","Did you adjust your approach when circumstances changed?"]])
H("The 50/50 Blending Framework",2)
formula("Final Score","S_final = S_data × 0.5 + S_interview × 0.5")
doc.add_paragraph("Your final competency score blends two sources equally: (1) simulation data — what you actually did (metrics, flags, financial outcomes), and (2) interview responses — how you reflect on and articulate your decisions. This means: a team with mediocre metrics but excellent strategic reflection can score well, and a team with excellent metrics but poor self-awareness will be penalised.")
warn("You cannot 'game' the system through either pure metric optimisation OR interview preparation alone. Both your actions AND your reflections matter equally.")
H("Interview Tips",2)
bl(["Reference specific rounds and decisions in your answers — vague generalities score poorly.",
    "Acknowledge trade-offs honestly. Saying 'I chose the cheaper option because treasury was low' is better than pretending every decision was ethically optimal.",
    "Connect early decisions to later outcomes. 'Our R1 deep audit protected us in R4' demonstrates systems thinking.",
    "Show awareness of what you'd do differently. Reflective learning is scored highly.",
    "Don't memorise answers. The AI interviewer adapts its questions based on your actual game data."])
doc.add_page_break()

# ═══ 15. STRATEGIC PLAYBOOK ═══
H("15. Strategic Playbook — Approaches & Considerations")
doc.add_paragraph("While there's no single 'correct' strategy, here are three coherent approaches observed in high-performing teams:")
H("Approach A: The Sustainability Pioneer",2)
doc.add_paragraph("Philosophy: Invest heavily in ESG from the start, accepting short-term treasury pain for maximum Mᵣ.")
tbl(["Round","Key Choice","Rationale"],
    [["R1","Deep Audit (B)","Protect against R4 blindspot"],["R2","Full Alignment (A)","Earn materiality_aligned flag"],
     ["R3","Green Bond (B)","Steady NCD reduction over time"],["R4","Full Transparency (A)","Maximum reputation recovery"],
     ["R5","Nature-Based (B)","Eco-friendly resilience + protect Mᵣ"],["R6","Ethical Overhaul (B)","Earn Truth Premium"],
     ["R7","Waste-to-Energy (C)","Critical synergy_unlock flag"],["R8","Water for All (A)","Protect SLO across all BUs"],
     ["R9","Community Fund (C)","Maximum community_fund bonus"],["R10","Resist & Integrate (A)","Synergy-powered endgame"]])
doc.add_paragraph("Expected Mᵣ: 1.80-2.08 (Regenerative Titan territory)")
doc.add_paragraph("Risk: Very treasury-intensive. Requires disciplined investment to maintain SLO and WR above thresholds.")

H("Approach B: The Balanced Pragmatist",2)
doc.add_paragraph("Philosophy: Mix moderate ESG investment with financial prudence. Accept slightly lower Mᵣ for treasury stability.")
doc.add_paragraph("Key differences: Choose Option B in most rounds (moderate cost, moderate benefit). Skip the most expensive investments (R8-A, R9-C). Focus on protecting the 'blocking' flags (avoid insurance_only, avoid water_priority).")
doc.add_paragraph("Expected Mᵣ: 1.20-1.60 (De-risked Safe-Haven)")

H("Approach C: The Financial Engineer",2)
doc.add_paragraph("Philosophy: Optimise treasury and EBITDA, relying on financial performance to carry the terminal valuation.")
doc.add_paragraph("Key differences: Choose cheaper options where possible. Prioritise revenue growth over ESG metrics. Accept lower Mᵣ but compensate with higher EBITDA.")
doc.add_paragraph("Risk: The Instability Discount (-0.40) and blocked Mᵣ bonuses often more than offset the financial gains. This strategy is a 'trap' the simulation is designed to expose.")
warn("The simulation systematically rewards Approach A over C. Financial performance alone cannot compensate for a low Mᵣ, because Mᵣ is multiplicative — even excellent EBITDA is severely discounted by a low Mᵣ.")
doc.add_page_break()

# ═══ 16. GLOSSARY ═══
H("16. Quick Reference Glossary")
tbl(["Term","Definition"],
    [["BU","Business Unit — one of your four operating divisions (Pharma, Electronics, Consumer Goods, Software)"],
     ["CAPEX","Capital Expenditure — money invested in BU improvements through the Investment Matrix"],
     ["OPEX","Operating Expenditure — ongoing costs to run a BU. Reduced by synergy investment."],
     ["CSF","Corporate Strategic Fund — your investable cash pool each round, calculated from BU profits minus dividends"],
     ["SLO","Social License to Operate — community consent for operations (0-100, per BU). CRITICAL: avg < 75 = -0.40 Mᵣ"],
     ["NCD","Natural Capital Debt — accumulated environmental liability. Compounds with interest each round."],
     ["Mᵣ","Regenerative Multiple — the sustainability-adjusted valuation multiplier (base 1.0, max 2.08)"],
     ["EBITDA","Earnings Before Interest, Tax, Depreciation & Amortisation — your combined operating profit"],
     ["Terminal Value","Final company valuation: TV = EBITDA × 12 × Mᵣ"],
     ["Contagion","Crisis damage spreading from one BU to the entire group via sigmoid S-curve"],
     ["Synergy","Cross-BU efficiency gains from coordinated investment. Follows diminishing returns (√ curve)."],
     ["Flag","A hidden marker set by your A/B/C decisions that affects future rounds. Cannot be undone."],
     ["Archetype","Your final company profile (Regenerative Titan / Safe-Haven / Fragile Giant / Stranded Relic)"],
     ["JT Scaling","Just Transition multiplier: JT = min(1.5, 1.0 + HR_rounds × 0.10). Amplifies R9 bonuses."],
     ["Turnaround","4-phase distress arc triggered when Treasury ≤ $0 AND Reputation < 30"],
     ["Carbon Tax","$250/tonne CO₂e applied at terminal valuation. Directly reduces EBITDA."],
     ["Sigmoid","S-curve function used by contagion engine: small crises = small impact, medium = rapid damage, large = saturating"],
     ["Foreshadowing","Market Reality Feed hints (R5-R8) that preview the R10 ending pathway"]])
doc.add_page_break()

# ═══ APPENDIX A ═══
H("Appendix A: Formula Quick-Reference Card")
doc.add_paragraph("Keep this page handy during gameplay:")
formula("CSF","CSF = Σ(Revenueᵢ − OPEXᵢ) − Dividends")
formula("Synergy","OPEX_new = OPEX_old × (1 − √(ratio) × 0.7 × Synergy_Mult)")
formula("Contagion","Group_Rep = Avg_Rep − 50 × σ((severity−30)/15)")
formula("NCD Interest","r = Base_Rate + NCD × 0.0001")
formula("Burnout Penalty","Penalty = ((B−20)²) × 0.000028125  [B>20]")
formula("Strike Risk","P = Base_Risk + ((1 − SLO/100) × 0.4)")
formula("Terminal Value","TV = (EBITDA − Carbon_Cost) × 12 × Mᵣ")
formula("JT Scaling","JT = min(1.5, 1.0 + HR_Rounds × 0.10)")
formula("Max Mᵣ","2.08 (requires all flags + SLO≥75 + WR≥75 + Burnout<20)")
doc.add_page_break()

# ═══ APPENDIX B ═══
H("Appendix B: Frequently Asked Questions")
faqs = [
    ("Can I undo a decision after committing?","No. Once you click 'COMMIT DECISIONS', your choices are permanent. This is by design — real CEOs can't undo strategic commitments."),
    ("What happens if my treasury goes negative?","You enter the Turnaround Pathway — a 4-phase distress arc. Investment is frozen in Phase 1, restricted in Phase 2, and only fully restored in Phase 3/4."),
    ("Does the order of investment allocation matter?","No. All allocations are processed simultaneously at the end of the round. There's no advantage to allocating to one BU before another."),
    ("Can two teams get different outcomes with the same decisions?","Yes. Stochastic elements (climate events, FX movements, macro noise) introduce randomness. This simulates real-world uncertainty."),
    ("What if I can't afford the 'best' option?","Adapt. The simulation rewards creative constraint management. A team that makes thoughtful trade-offs under resource pressure often outscores a team that follows a formulaic 'optimal' path."),
    ("How important is the CEO interview vs. game performance?","Equally important — 50/50 blend. A team with average metrics but exceptional strategic reflection can score very well."),
    ("Do I need to read the board member emails?","They contain hints about upcoming crises and strategic advice. Reading them improves your situational awareness significantly."),
    ("What is the 'Market Reality Feed'?","Foreshadowing events (R5-R8) that preview the R10 ending pathway. These are your early warning system."),
]
for q,a in faqs:
    p = doc.add_paragraph()
    r = p.add_run(f"Q: {q}"); r.bold = True
    doc.add_paragraph(f"A: {a}")
    doc.add_paragraph()

# Closing
doc.add_paragraph()
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Good luck, CEO. The future of Muressons is in your hands. 🌍")
r.bold = True; r.font.size = Pt(16); r.font.color.rgb = RGBColor(0x1a,0x3c,0x6e)

out = os.path.join(os.path.dirname(__file__), "_student_guide_part3.docx")
doc.save(out)
print(f"Part 3 saved: {out}")
