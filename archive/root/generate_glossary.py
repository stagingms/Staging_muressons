"""Generate Technical Glossary Word Document for Muressons Simulation."""
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml
import os

doc = Document()

# -- Styles --
style = doc.styles['Normal']
style.font.name = 'Calibri'
style.font.size = Pt(11)

def add_heading_styled(text, level=1):
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        run.font.color.rgb = RGBColor(0x1a, 0x3c, 0x6e)
    return h

def add_formula_paragraph(label, formula_text):
    p = doc.add_paragraph()
    run_label = p.add_run(label + ": ")
    run_label.bold = True
    run_label.font.size = Pt(11)
    run_formula = p.add_run(formula_text)
    run_formula.italic = True
    run_formula.font.name = 'Cambria Math'
    run_formula.font.size = Pt(12)
    run_formula.font.color.rgb = RGBColor(0x8b, 0x00, 0x00)
    return p

def add_detail(text):
    p = doc.add_paragraph(text)
    p.paragraph_format.left_indent = Inches(0.3)
    p.style.font.size = Pt(10)
    return p

# ============ TITLE PAGE ============
doc.add_paragraph()
doc.add_paragraph()
t = doc.add_paragraph()
t.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = t.add_run("Muressons Global Corporation")
r.bold = True; r.font.size = Pt(28); r.font.color.rgb = RGBColor(0x1a, 0x3c, 0x6e)

t2 = doc.add_paragraph()
t2.alignment = WD_ALIGN_PARAGRAPH.CENTER
r2 = t2.add_run("Technical Glossary & Mathematical Reference")
r2.bold = True; r2.font.size = Pt(18); r2.font.color.rgb = RGBColor(0x4a, 0x4a, 0x4a)

t3 = doc.add_paragraph()
t3.alignment = WD_ALIGN_PARAGRAPH.CENTER
r3 = t3.add_run("Simulation Engine v6.0 — Comprehensive Formula Documentation")
r3.font.size = Pt(12); r3.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

doc.add_page_break()

# ============ TABLE OF CONTENTS ============
add_heading_styled("Table of Contents", 1)
toc_items = [
    "1. Corporate Strategic Fund (CSF)",
    "2. Contagion Engine (Sigmoid Model)",
    "3. Synergy Engine (Diminishing Returns)",
    "4. Natural Capital Cost of Debt",
    "5. VRIO Decay Function",
    "6. Burnout Accumulation Engine",
    "7. Workforce Readiness Engine",
    "8. Talent Brain-Drain Engine",
    "9. Strike Probability Engine",
    "10. Natural Decay (Entropy)",
    "11. Macroeconomic Inflation Engine",
    "12. Execution Overrun Risk",
    "13. Technical Debt Engine",
    "14. Revenue Cannibalization",
    "15. Stakeholder Fatigue Engine",
    "16. Supply Chain Contagion",
    "17. Competitive NPC Index",
    "18. Cash Conversion / Working Capital",
    "19. Dividend Ratchet Engine",
    "20. Talent Allocation Pressure",
    "21. Technology Lock-In Engine",
    "22. ESG Greenwashing Risk",
    "23. Macro Interest Rate Environment",
    "24. FX Risk Engine",
    "25. DSO / Working Capital Timing",
    "26. Macro-Economic Noise",
    "27. Turnaround Pathway (3-Act Arc)",
    "28. Severity Classification",
    "29. Momentum Score",
    "30. Terminal Valuation & M\u1d63",
    "31. Archetype Determination",
    "32. CEO Interview Scoring",
    "33. Score Blending Framework",
]
for item in toc_items:
    doc.add_paragraph(item, style='List Number')

doc.add_page_break()

# ============ SECTION 1: CSF ============
add_heading_styled("1. Corporate Strategic Fund (CSF)", 1)
doc.add_paragraph("The CSF represents the net operating cash flow available for reinvestment each round.")
add_formula_paragraph("Formula", "CSF = \u03a3(Revenue\u1d62 \u2212 OPEX\u1d62) \u2212 Dividends_Paid")
add_detail("Where Revenue\u1d62 and OPEX\u1d62 are the revenue and operating expenditure of each Business Unit i.")
add_detail("Mutation: Updates global_round_states.corporate_treasury")
add_detail("Loan Trigger: If total CAPEX > 20% of treasury, a short-term loan is triggered at 12% interest.")
add_detail("Hardening: dividends_paid clamped to treasury balance (VULN-001); total CAPEX capped at 2\u00d7 treasury (VULN-006).")

# ============ SECTION 2: Contagion ============
add_heading_styled("2. Contagion Engine (Sigmoid Model)", 1)
doc.add_paragraph("Models crisis reputation propagation using an S-curve for realistic non-linear damage.")
add_formula_paragraph("Sigmoid Function", "\u03c3(x) = 1 / (1 + e\u207b\u02e3)")
add_formula_paragraph("Sigmoid Input", "x = (Crisis_Severity \u2212 30) / 15")
add_formula_paragraph("Group Reputation", "Group_Rep = Avg_BU_Rep \u2212 50 \u00d7 \u03c3(x)")
add_detail("Result clamped to [0, 100].")
add_detail("Low severity (<15): minimal impact. Medium (20-40): rapid erosion. High (>50): saturating damage.")
add_detail("Crisis_severity floored at 0 (VULN-003).")

# ============ SECTION 3: Synergy ============
add_heading_styled("3. Synergy Engine (Diminishing Returns)", 1)
doc.add_paragraph("OPEX reduction via investment, with sqrt scaling for diminishing marginal returns.")
add_formula_paragraph("Effective Ratio", "r_eff = \u221a(Investment_Ratio) \u00d7 0.7")
add_formula_paragraph("New OPEX", "OPEX_new = OPEX_old \u00d7 (1 \u2212 r_eff \u00d7 Synergy_Multiplier)")
add_detail("Investment_Ratio clamped to [0.0, 1.0] (VULN-002).")
add_detail("OPEX floored at 0 to prevent negative values.")

# ============ SECTION 4: NCD ============
add_heading_styled("4. Natural Capital Cost of Debt", 1)
doc.add_paragraph("Environmental debt compounds each round, increasing the cost of capital.")
add_formula_paragraph("Interest Rate", "r = Base_Rate + (NCD \u00d7 0.0001)")
add_formula_paragraph("Debt Compounding", "NCD_{t+1} = NCD_t + (NCD_t \u00d7 r)")
add_detail("At NCD=100: rate \u2248 6.0%. At NCD=500: rate \u2248 10.0%. At NCD=1000: rate \u2248 15.0%.")
add_detail("NCD floored at 0 (VULN-004), capped at 1,000,000 (VULN-007).")

# ============ SECTION 5: VRIO ============
add_heading_styled("5. VRIO Decay Function", 1)
doc.add_paragraph("Competitive advantage erodes over time through imitation.")
add_formula_paragraph("Formula", "Advantage_{t+1} = Advantage_t \u00d7 (1 \u2212 Imitation_Decay_Rate)")
add_detail("Default decay rate: 5% per round.")

# ============ SECTION 6: Burnout ============
add_heading_styled("6. Burnout Accumulation Engine", 1)
doc.add_paragraph("Tracks staff burnout per BU with quadratic OPEX penalty curve.")
add_formula_paragraph("Burnout Update", "B_{t+1} = B_t + \u0394_HR + Natural_Drift")
add_formula_paragraph("OPEX Penalty Rate", "Penalty = ((B \u2212 20)\u00b2) \u00d7 0.000028125    [when B > 20]")
add_detail("Natural drift: +3.0/round when no HR investment. Clamped to [0, 100].")
add_detail("Critical threshold: B > 70 triggers additional governance risk.")
add_detail("HR deltas: positive actions \u2212(8 to 15), overtime push +(12 to 15).")

# ============ SECTION 7: Workforce Readiness ============
add_heading_styled("7. Workforce Readiness Engine", 1)
doc.add_paragraph("Global workforce competence level affecting strategic effectiveness.")
add_formula_paragraph("Formula", "WR_{t+1} = WR_t + \u0394_{HR}")
add_detail("High HR investment: +8. Medium: +4. No investment: \u22125 (skills atrophy).")
add_detail("WR < 40: Strategic pillar effectiveness reduced by 20%.")
add_detail("WR > 75: Synergy multiplier +0.05 bonus at terminal valuation.")

# ============ SECTION 8: Brain Drain ============
add_heading_styled("8. Talent Brain-Drain Engine", 1)
doc.add_paragraph("Applies to Software & Healthcare BUs when group reputation falls below 65.")
add_formula_paragraph("Base Penalty", "P = 1 + max(0, (65 \u2212 Group_Rep) / 100) \u00d7 1.5")
add_formula_paragraph("Burnout Addon", "P += ((Burnout \u2212 50) / 100) \u00d7 2.0    [when Burnout > 50]")
add_formula_paragraph("New OPEX", "OPEX_new = OPEX_current \u00d7 P")

# ============ SECTION 9: Strike ============
add_heading_styled("9. Strike Probability Engine", 1)
doc.add_paragraph("Calculates probability of workforce strike based on governance risk and social license.")
add_formula_paragraph("Formula", "P_Strike = Base_Risk + ((1 \u2212 SLO/100) \u00d7 0.4)")
add_detail("Result clamped to [0.0, 1.0].")

# ============ SECTION 10: Decay ============
add_heading_styled("10. Natural Decay (Entropy)", 1)
doc.add_paragraph("BUs receiving zero investment decay 2% per round.")
add_formula_paragraph("Reputation", "Rep_{t+1} = Rep_t \u00d7 0.98    [if CAPEX = 0]")
add_formula_paragraph("Social License", "SLO_{t+1} = SLO_t \u00d7 0.98    [if CAPEX = 0]")

# ============ SECTION 11: Inflation ============
add_heading_styled("11. Macroeconomic Inflation Engine", 1)
add_formula_paragraph("Formula", "OPEX_new = OPEX \u00d7 (1 + Inflation_Index)")
add_detail("Default inflation_index = 0.025 (2.5% per round).")

# ============ SECTION 12: Overrun ============
add_heading_styled("12. Execution Overrun Risk", 1)
doc.add_paragraph("Stochastic cost overrun when CAPEX exceeds threshold.")
add_formula_paragraph("Condition", "If CAPEX > Threshold: P(overrun) = 0.25")
add_formula_paragraph("Overrun Amount", "Overrun = CAPEX \u00d7 0.15")
add_detail("Default threshold: $3,000,000.")

# ============ SECTION 13: Tech Debt ============
add_heading_styled("13. Technical Debt Engine", 1)
add_formula_paragraph("Formula", "OPEX_new = OPEX \u00d7 (1 + 0.04)    [if zero_rounds \u2265 2]")
add_detail("BUs with no investment for 2+ consecutive rounds incur 4% OPEX penalty.")

# ============ SECTION 14: Cannibalization ============
add_heading_styled("14. Revenue Cannibalization", 1)
doc.add_paragraph("Dynamic market overlap model for intra-group competition.")
add_formula_paragraph("Condition", "Triggers when BU revenue > 115% of group average")
add_formula_paragraph("Penalty", "Penalty = Victim_Rev \u00d7 Rate \u00d7 Overlap_Score")
add_detail("Rate = 3%. Overlap scores range 0.15\u20130.70 based on market similarity.")

# ============ SECTION 15: Stakeholder Fatigue ============
add_heading_styled("15. Stakeholder Fatigue Engine", 1)
add_formula_paragraph("Recovery Efficiency", "\u03b7 = 1 / (1 + Fatigue_Factor \u00d7 Crisis_Count)")
add_formula_paragraph("Effective Recovery", "Recovery_eff = Recovery_amount \u00d7 \u03b7")
add_detail("Default fatigue_factor = 0.3. Trust recovery diminishes after each crisis.")

# ============ SECTION 16: Supply Chain ============
add_heading_styled("16. Supply Chain Contagion", 1)
add_formula_paragraph("Shared Exposure", "Exposure = \u03a3(Other_BU_GovRisk \u00d7 0.002)")
add_formula_paragraph("OPEX Surcharge", "Surcharge = OPEX_base \u00d7 Exposure")

# ============ SECTION 17: Competitor ============
add_heading_styled("17. Competitive NPC Index", 1)
add_formula_paragraph("NPC Growth", "Competitor_EBITDA_{t+1} = Competitor_EBITDA_t \u00d7 (1 + 0.03)")
add_formula_paragraph("Relative Advantage", "Advantage = Player_EBITDA / Competitor_EBITDA")

# ============ SECTION 18: Cash Conversion ============
add_heading_styled("18. Cash Conversion / Working Capital", 1)
add_formula_paragraph("Efficiency", "\u03b7 = Base_Efficiency \u2212 (Gov_Risk / 500)")
add_formula_paragraph("Realized Revenue", "Rev_realized = Revenue \u00d7 \u03b7")
add_detail("Efficiency clamped to [0.5, 1.0].")

# ============ SECTION 19: Dividend Ratchet ============
add_heading_styled("19. Dividend Ratchet Engine", 1)
add_formula_paragraph("Condition", "If Div_t < Div_{t\u22121} \u00d7 0.8 \u2192 Rep penalty = \u22125")
add_detail("Cutting dividends by >20% triggers reputation penalty.")

# ============ SECTION 20: Talent Allocation ============
add_heading_styled("20. Talent Allocation Pressure", 1)
add_formula_paragraph("Condition", "If BU_CAPEX_Share < 15% of Total_CAPEX")
add_formula_paragraph("Surcharge", "Surcharge = OPEX_base \u00d7 0.02")

# ============ SECTION 21: Lock-In ============
add_heading_styled("21. Technology Lock-In Engine", 1)
add_formula_paragraph("Condition", "Same BU receives highest CAPEX for \u2265 3 consecutive rounds")
add_formula_paragraph("Penalty", "Other BU synergy efficiency \u00d7 0.85 (15% reduction)")

# ============ SECTION 22: Greenwashing ============
add_heading_styled("22. ESG Greenwashing Risk", 1)
doc.add_paragraph("Detects misalignment between stated ESG commitments and actual investment.")
add_formula_paragraph("Trigger", "Green choice (A/C) AND Avg_Inv_Ratio < 15%")
add_formula_paragraph("Penalty", "Social License \u2212 8 points")
add_detail("Moderate choices (B): threshold = 10%, penalty halved to \u22124.")

# ============ SECTION 23: Macro Rates ============
add_heading_styled("23. Macro Interest Rate Environment", 1)
doc.add_paragraph("Models central bank policy cycles across 10 rounds.")
table = doc.add_table(rows=5, cols=3)
table.style = 'Light Grid Accent 1'
for i, (period, regime, mod) in enumerate([
    ("R1\u2013R3", "Easing", "\u22120.5%"),
    ("R4\u2013R6", "Neutral", "0.0%"),
    ("R7\u2013R9", "Tightening", "+0.5%"),
    ("R10", "Crisis Premium", "+1.0%"),
]):
    table.rows[i+1].cells[0].text = period
    table.rows[i+1].cells[1].text = regime
    table.rows[i+1].cells[2].text = mod
table.rows[0].cells[0].text = "Rounds"
table.rows[0].cells[1].text = "Regime"
table.rows[0].cells[2].text = "CoC Modifier"

# ============ SECTION 24: FX ============
add_heading_styled("24. FX Risk Engine", 1)
add_formula_paragraph("FX Movement", "FX \u223c Uniform(\u22125%, +5%) per round")
add_formula_paragraph("Revenue Impact", "\u0394Rev = Revenue \u00d7 FX_movement \u00d7 Exposure_%")
add_detail("Exposure: Software 80%, Electronics 75%, Pharma 60%, Consumer Goods 40%.")

# ============ SECTION 25: DSO ============
add_heading_styled("25. DSO / Working Capital Timing", 1)
add_formula_paragraph("DSO Factor", "DSO = 0.02 + 0.001 \u00d7 Gov_Risk")
add_formula_paragraph("Deferred Revenue", "Deferred = Revenue \u00d7 DSO_factor")
add_detail("At gov_risk=0: 2% deferred. At 50: 7%. At 100: 12%. Capped at 15%.")

# ============ SECTION 26: Noise ============
add_heading_styled("26. Macro-Economic Noise", 1)
doc.add_paragraph("Stochastic volatility preventing reverse-engineering of deterministic formulas.")
add_detail("Inflation noise: \u00b10.2%. Carbon price noise: \u00b15%. Micro-strike: 3% per round.")

# ============ SECTION 27: Turnaround ============
add_heading_styled("27. Turnaround Pathway (3-Act Distress Arc)", 1)
doc.add_paragraph("Replaces binary survival mode with progressive recovery phases.")
table2 = doc.add_table(rows=5, cols=4)
table2.style = 'Light Grid Accent 1'
headers = ["Phase", "Entry Conditions", "CapEx Cap", "M\u1d63 Cap"]
for j, h in enumerate(headers):
    table2.rows[0].cells[j].text = h
data = [
    ("Crisis", "Treasury \u2264 $0 AND Rep < 30", "0% (frozen)", "0.60"),
    ("Stabilisation", "Treasury > $0 AND Rep > 20", "50%", "0.80"),
    ("Recovery", "Treasury > $10M AND Rep > 45", "100%", "1.20"),
    ("Exit", "Treasury > $20M AND Rep > 55", "Lifted", "+0.10 bonus"),
]
for i, (phase, cond, capex, mr) in enumerate(data):
    table2.rows[i+1].cells[0].text = phase
    table2.rows[i+1].cells[1].text = cond
    table2.rows[i+1].cells[2].text = capex
    table2.rows[i+1].cells[3].text = mr

# ============ SECTION 28: Severity ============
add_heading_styled("28. Severity Classification", 1)
add_formula_paragraph("Impact %", "Impact = |Amount| / Treasury \u00d7 100")
add_detail("Tiers: Routine (<1%), Noteworthy (1\u20135%), Material (5\u201315%), Critical (>15%).")

# ============ SECTION 29: Momentum ============
add_heading_styled("29. Momentum Score", 1)
add_formula_paragraph("Formula", "M = 50 + 0.4\u00d7\u0394(Treasury_Velocity) + 0.3\u00d7\u0394(Reputation) + 0.3\u00d7\u0394(NCD_Reduction)")
add_detail("Scaled to [0, 100]. Two consecutive rounds at >70 earns 'Comeback Kid' bonus (+0.05 M\u1d63).")

# ============ SECTION 30: Terminal Valuation ============
add_heading_styled("30. Terminal Valuation & Regenerative Multiple (M\u1d63)", 1)

doc.add_paragraph("The capstone calculation determining final company value at Round 10.")
add_formula_paragraph("EBITDA 2050", "EBITDA = \u03a3(Revenue\u1d62 \u2212 OPEX\u1d62) \u2212 (tCO\u2082e \u00d7 Carbon_Tax)")
add_formula_paragraph("Terminal Value", "TV = EBITDA \u00d7 Exit_Multiple(12\u00d7) \u00d7 M\u1d63")

doc.add_paragraph()
doc.add_paragraph("M\u1d63 (Regenerative Multiple) Breakdown:").bold = True
mr_table = doc.add_table(rows=10, cols=3)
mr_table.style = 'Light Grid Accent 1'
mr_table.rows[0].cells[0].text = "Component"
mr_table.rows[0].cells[1].text = "Bonus"
mr_table.rows[0].cells[2].text = "Condition"
mr_data = [
    ("Base", "1.00", "Always"),
    ("Materiality Governance", "+0.10", "materiality_aligned flag"),
    ("Synergy Excellence", "+0.30", "synergy_unlock AND multiplier \u2265 0.80"),
    ("Resilience Champion", "+0.20", "NOT insurance_only AND NOT water_priority"),
    ("Truth Premium", "+0.15", "ethical_ai_overhaul flag"),
    ("Community Champion", "+0.18\u00d7JT", "community_fund flag"),
    ("Just Transition", "+0.12\u00d7JT", "managed_transition flag"),
    ("Workforce Excellence", "+0.10", "Workforce Readiness \u2265 75"),
    ("Wellbeing Champion", "+0.05", "Avg Burnout < 20"),
]
for i, (comp, bonus, cond) in enumerate(mr_data):
    mr_table.rows[i+1].cells[0].text = comp
    mr_table.rows[i+1].cells[1].text = bonus
    mr_table.rows[i+1].cells[2].text = cond

doc.add_paragraph()
add_formula_paragraph("JT Scaling", "JT = min(1.5, 1.0 + HR_Rounds \u00d7 0.10)")
add_formula_paragraph("Instability Discount", "If Avg_SLO < 75: M\u1d63 \u2212= 0.40")
add_detail("Maximum achievable M\u1d63: 2.08")

# ============ SECTION 31: Archetypes ============
add_heading_styled("31. Archetype Determination", 1)
arch_table = doc.add_table(rows=6, cols=3)
arch_table.style = 'Light Grid Accent 1'
arch_table.rows[0].cells[0].text = "Archetype"
arch_table.rows[0].cells[1].text = "M\u1d63 Threshold"
arch_table.rows[0].cells[2].text = "Icon"
arch_data = [
    ("Regenerative Titan", "\u2265 1.80", "\U0001f331"),
    ("De-risked Safe-Haven", "\u2265 1.20", "\U0001f3e6"),
    ("Fragile Giant", "\u2265 0.80", "\u26a0\ufe0f"),
    ("Stranded Relic", "< 0.80", "\U0001f480"),
    ("Turnaround Manager", "Survival mode", "\U0001f527"),
]
for i, (name, thresh, icon) in enumerate(arch_data):
    arch_table.rows[i+1].cells[0].text = name
    arch_table.rows[i+1].cells[1].text = thresh
    arch_table.rows[i+1].cells[2].text = icon

add_detail("Cross-pathway normalization: M\u1d63_normalized = M\u1d63_raw \u00d7 Difficulty_Coefficient")

# ============ SECTION 32: CEO Scoring ============
add_heading_styled("32. CEO Interview Scoring", 1)
doc.add_paragraph("Post-game competency assessment across 6 dimensions (0\u201310 each):")
dim_table = doc.add_table(rows=7, cols=3)
dim_table.style = 'Light Grid Accent 1'
dim_table.rows[0].cells[0].text = "Dimension"
dim_table.rows[0].cells[1].text = "Data Source"
dim_table.rows[0].cells[2].text = "Formula"
dims = [
    ("Strategic Thinking", "M\u1d63", "min(10, max(1, (M\u1d63 \u2212 0.5) / 0.15))"),
    ("Stakeholder Empathy", "SLO + Burnout", "SLO/10 + burnout_bonus"),
    ("Financial Acumen", "Treasury + EBITDA", "Treasury/$5M + EBITDA/$10M"),
    ("Ethical Reasoning", "Flags", "4.0 + flag_bonuses"),
    ("Systems Thinking", "Synergy + VRIO", "(Syn\u22120.7)\u00d710 + VRIO/20"),
    ("Adaptive Leadership", "WR + HR rounds", "WR/15 + HR_rounds"),
]
for i, (dim, src, form) in enumerate(dims):
    dim_table.rows[i+1].cells[0].text = dim
    dim_table.rows[i+1].cells[1].text = src
    dim_table.rows[i+1].cells[2].text = form

# ============ SECTION 33: Blending ============
add_heading_styled("33. Score Blending Framework", 1)
add_formula_paragraph("Final Score", "S_final = S_data \u00d7 0.5 + S_interview \u00d7 0.5")
add_detail("50/50 blend of simulation-derived metrics and LLM-assessed interview responses.")
add_detail("Prevents 'gaming' the system through either pure metric optimisation or interview preparation alone.")

# ============ APPENDIX ============
doc.add_page_break()
add_heading_styled("Appendix A: Vulnerability Hardening Summary", 1)
vuln_table = doc.add_table(rows=8, cols=3)
vuln_table.style = 'Light Grid Accent 1'
vuln_table.rows[0].cells[0].text = "ID"
vuln_table.rows[0].cells[1].text = "Description"
vuln_table.rows[0].cells[2].text = "Fix"
vulns = [
    ("VULN-001", "Dividends exceed treasury", "Clamped to balance"),
    ("VULN-002", "Investment ratio > 1.0", "Hard cap at 1.0"),
    ("VULN-003", "Negative crisis severity", "Floored at 0"),
    ("VULN-004", "Negative NCD", "Floored at 0"),
    ("VULN-006", "CAPEX > 2\u00d7 treasury", "Hard cap applied"),
    ("VULN-007", "NCD overflow", "Capped at 1,000,000"),
    ("HARD-002", "Strike penalty too low", "Minimum 5% of treasury"),
]
for i, (vid, desc, fix) in enumerate(vulns):
    vuln_table.rows[i+1].cells[0].text = vid
    vuln_table.rows[i+1].cells[1].text = desc
    vuln_table.rows[i+1].cells[2].text = fix

# Save
out_path = os.path.join(os.path.dirname(__file__), "Muressons_Technical_Glossary.docx")
doc.save(out_path)
print(f"Document saved to: {out_path}")
