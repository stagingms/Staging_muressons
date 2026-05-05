"""Part 2: Sections 7-11."""
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os
IMG = os.path.join(os.path.dirname(__file__), "guide_images")
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
def img(n,w=Inches(6)):
    p=os.path.join(IMG,n)
    if os.path.exists(p): doc.add_picture(p,width=w); doc.paragraphs[-1].alignment=WD_ALIGN_PARAGRAPH.CENTER
def cap(t): p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; r=p.add_run(t); r.italic=True; r.font.size=Pt(9); r.font.color.rgb=RGBColor(0x66,0x66,0x66)
def bl(items):
    for i in items: doc.add_paragraph(i, style='List Bullet')

# ═══ 7. DECISION GATES ═══
H("7. Decision Gates — Making Strategic Choices")
doc.add_paragraph("Each round presents a crisis scenario with three strategic options (A, B, C). These are not 'good/bad/neutral' — each represents a genuine strategic trade-off with different cost profiles, risk exposures, and long-term flag implications.")
H("How to Read a Decision Gate",2)
doc.add_paragraph("Each option displays: a title describing the strategic approach, a description explaining what happens if you choose it, financial impacts (treasury cost, revenue change), ESG impacts (reputation, SLO, carbon intensity, NCD), and flags set — hidden markers that unlock or block future options.")
H("The Three Archetypes of Choice",2)
tbl(["Pattern","Typical Option","Character","Long-term Effect"],
    [["Bold & Expensive","Usually A","Full commitment, high cost","Sets valuable flags, highest Mᵣ potential"],
     ["Moderate & Balanced","Usually B","Partial action, moderate cost","Fewer flags but less risk"],
     ["Cheap & Risky","Usually C","Minimal spend, deferred cost","Often creates downstream penalties"]])
doc.add_paragraph()
warn("Cheap options in early rounds often create compounding penalties in later rounds. The simulation systematically punishes short-termism — a $2M saving in Round 1 can cost $20M+ by Round 10.")
tip("Decision Framework","Before choosing, ask: (1) What flag does this set? (2) Will I need that flag later? (3) Can my treasury absorb the cost? (4) What happens to my SLO and Reputation?")
doc.add_page_break()

# ═══ 8. ROUND-BY-ROUND ═══
H("8. The 10-Round Journey — Detailed Guide")
img("roadmap.png", Inches(5.5))
cap("Figure 8.1 — The Simulation Roadmap: 10 Rounds Across 3 Strategic Years")
doc.add_paragraph()
rounds = [
    ("1","Foundations — ESG Baseline Assessment","📋",
     "The board has mandated an initial ESG assessment across all business units. You must decide the depth and scope of the audit.",
     ["Option A — Surface-Level Scan: Fast and cheap ($0 cost), but creates the 'electronics_blindspot' flag. This flag DOUBLES crisis severity in Round 4 from 40 to 80. You gain $500K revenue short-term but lose -2 Reputation and gain +2 Carbon Intensity.",
      "Option B — Deep Forensic Audit: Costs $3M and reduces short-term revenue by $200K, but gains +5 Reputation, reduces Carbon Intensity by -5, and sets the critical 'deep_audit_completed' flag that protects you in Round 4.",
      "Option C — Phased Audit Rollout: The middle ground at $1.5M. Audits Pharma and Consumer Goods now but defers Electronics and Software. Partial protection — some blind spots remain."],
     "Round 1 is the most consequential decision in the simulation. The deep audit seems expensive at $3M, but the blindspot penalty in Round 4 typically costs $10-20M in reputation recovery. This is the simulation's first lesson in long-term thinking."),
    ("2","Double Materiality — Budget Allocation","📊",
     "The CFO requires all investment proposals to demonstrate alignment with the High Financial Impact / High ESG Impact quadrant per the Double Materiality framework.",
     ["Option A — Full Materiality Alignment: Genuine CSRD compliance with assurance-ready reporting. Costs $2.5M in revenue but gains +5 Reputation, -5 Governance Risk, and sets the 'materiality_aligned' flag worth +0.10 Mᵣ at terminal valuation. In Advanced Climate mode, unlocks NCD forgiveness (+25%).",
      "Option B — Strategic Exceptions: Allow limited off-quadrant spending with CFO approval. Moderate gains (+2 Rep, -2 Gov Risk) at no revenue cost.",
      "Option C — Ignore Materiality: Business-as-usual with no materiality filter. Gains $400K revenue but loses -5 Reputation, +10 Governance Risk, and triggers a 40% budget clawback of materiality capital."],
     "The materiality_aligned flag is one of the easiest Mᵣ bonuses to earn (+0.10). The $2.5M cost pays for itself many times over at terminal valuation."),
    ("3","Scope 3 Emissions — Supply Chain Decarbonisation","🏭",
     "Regulators have signalled mandatory Scope 3 disclosures. Your supply chain carbon footprint is 4× your direct emissions.",
     ["Option A — Rapid Supplier Switch: Costs $4M treasury and $800K revenue, but achieves -15 Carbon Intensity and sets 'early_decarboniser' flag (strategic advantage in R7). Risk: supply chain disruption.",
      "Option B — Green Bond Investment: Issue a green bond for $2M. Reduces NCD by -15 and CI by -8 over 3 rounds. Generates $300K revenue. Sets 'green_bond_active' flag.",
      "Option C — Offset & Defer: Buy carbon offsets for $1M. Minimal CI reduction (-1), increases NCD by +5, and loses -3 Reputation. A delay tactic."],
     "The 'early_decarboniser' flag from Option A provides a synergy multiplier bonus in Round 7. Green bonds (B) are the best risk-adjusted option for most teams."),
    ("4","Contagion — Reputation Crisis Cascade","🔥",
     "A labour-rights exposé in your Electronics supply chain has gone viral. The contagion engine propagates reputational damage across ALL business units using a sigmoid curve.",
     ["Option A — Full Transparency & Remediation: Costs $6M but gains +10 Reputation, +8 SLO. Public disclosure, factory audits, worker compensation.",
      "Option B — Damage Control PR: Costs $2M, gains +2 Rep but loses -3 SLO. Contains narrative but doesn't fix root cause.",
      "Option C — Deny & Deflect: Free but devastating — loses -15 Reputation, -10 SLO. Highest contagion risk."],
     "If you chose the Surface Scan in R1, crisis severity DOUBLES from 40 to 80 — making all impacts roughly twice as severe. This is where R1 decisions come home to roost."),
    ("5","Climate — Physical Risk Event","🌪️",
     "A Category 4 cyclone is projected to hit your primary manufacturing corridor. Base damage: $12M. A stochastic dice roll (75% threshold) determines if it strikes.",
     ["Option A — Hard Engineering Defence: $8M for flood walls. Resilience Factor 0.85, but NO protection this round (completes R7). Adds +10 NCD and +3 Carbon Intensity from construction.",
      "Option B — Nature-Based Solutions: $5M for mangrove restoration. Resilience Factor 0.60, matures by R7. Reduces NCD by -8 and CI by -6. The eco-friendly choice.",
      "Option C — Insurance Only: $2M for comprehensive insurance. ZERO physical resilience. Full damage if cyclone strikes. PERMANENTLY BLOCKS the +0.20 Resilience Bonus at terminal valuation."],
     "This is the simulation's biggest 'trap'. Insurance Only is 4× cheaper but permanently sacrifices +0.20 Mᵣ — worth potentially $50M+ in terminal value. Neither A nor B protects you THIS round."),
]
for rn,title,icon,crisis,options,insight in rounds[:5]:
    H(f"Round {rn}: {title} {icon}",2)
    doc.add_paragraph(crisis)
    H("Options",3)
    for o in options: doc.add_paragraph(o, style='List Bullet')
    tip("Key Insight",insight)
    doc.add_paragraph()
doc.add_page_break()

rounds2 = [
    ("6","AI Bias — Algorithmic Ethics","🤖",
     "Your Software BU's AI recruitment tool has been found to systematically discriminate against minority applicants. The story has reached mainstream media.",
     ["Option A — Monetise the Algorithm: Pivot the AI tool into a commercial product. Gains $10M Software revenue but loses -20 Reputation and spikes the contagion factor. A provocative 'greed' option.",
      "Option B — Ethical AI Overhaul: Shut down the tool, hire an ethics board, retrain models. Costs $8M but gains +15 SLO, +5 Reputation, and sets the 'ethical_ai_overhaul' flag worth +0.15 Mᵣ Truth Premium.",
      "Option C — Quiet Patch: Silently fix the algorithm. Costs $1M but loses -5 Reputation, gains +10 Governance Risk. If leaked later, devastating."],
     "The ethical_ai_overhaul flag unlocks the +0.15 Truth Premium — one of the most valuable Mᵣ bonuses. Option A's $10M revenue is tempting but the -20 Reputation often triggers Talent Brain-Drain."),
    ("7","Circularity — Circular Economy Transition","♻️",
     "New EU circular economy regulations mandate 60% waste diversion by next year. Non-compliance fines: $15M.",
     ["Option A — Full Circular Redesign: $10M to redesign products for disassembly/reuse. -12 NCD, +8 Rep, -8 CI, +$1M revenue.",
      "Option B — Extended Producer Responsibility: $5M for take-back programs and recycling. -6 NCD, +4 Rep, -5 CI.",
      "Option C — Waste-to-Energy Partnership: $7M to build waste-to-energy facility. Sets 'synergy_unlock' flag — the MOST VALUABLE flag in the game, worth +0.30 Mᵣ AND enables R10 Option A."],
     "Option C's synergy_unlock flag is worth +0.30 Mᵣ — the single largest bonus available. It also gates Option A in Round 10 (Resist & Integrate, which requires Synergy ≥ 80). This is arguably the most important round."),
    ("8","Blue Stress — Water Scarcity Emergency","🌊",
     "A multi-year drought has depleted the watershed serving Pharma and Electronics. Government water rationing is imminent.",
     ["Option A — Water Efficiency for All: $12M for equitable upgrades across all BUs. -20 Water Dependency, +5 SLO, -3 CI.",
      "Option B — Prioritise Electronics: $4M to divert water to Electronics (highest margin). Pharma and Consumer Goods suffer -25 SLO each. Sets 'electronics_water_priority' which BLOCKS Resilience bonus.",
      "Option C — Desalination Mega-Project: $30M for a desalination plant. Massive upfront cost with 2-round delay. -30 NCD, -40 Water Dependency. Generates $5M/round from R10."],
     "Option B is another 'trap' — it saves money but permanently blocks the +0.20 Resilience Bonus AND devastates SLO in two BUs, likely triggering the -0.40 Instability Discount."),
    ("9","Just Transition — Workforce & Community Justice","✊",
     "Decarbonisation commitments require closing 3 legacy factories. 2,000 jobs are at risk. Community protests are escalating.",
     ["Option A — Immediate Closure: Gain $5M treasury but lose -20 SLO, -15 Reputation. If SLO is low, 50-75% chance of STRIKE that zeros all revenue for the round.",
      "Option B — Managed Transition: $12M for 2-year phase-out with retraining. +10 SLO, +8 Reputation. Sets 'managed_transition' flag (+0.12×JT Mᵣ).",
      "Option C — Community Investment Fund: $20M for community economic development and green jobs. +18 SLO, +12 Reputation. Sets 'community_fund' flag (+0.18×JT Mᵣ)."],
     "The JT scaling multiplier rewards sustained HR investment: JT = min(1.5, 1.0 + HR_Rounds × 0.10). If you invested in HR for 5+ rounds, Option C's community_fund bonus scales to +0.27 Mᵣ."),
    ("10","Grand Finale — Terminal Valuation","🏛️",
     "An activist investor consortium has acquired a blocking stake. They demand strategic restructuring. Your cumulative decisions determine your final company archetype and valuation.",
     ["Option A — Resist & Integrate: Keep all BUs integrated and leverage synergy. DISABLED if Synergy Score ≤ 80. Costs $5M. Synergy bonus applied.",
      "Option B — Spin-off: Spin off weakest BU as separate entity. Gains $10M treasury. Moderate risk.",
      "Option C — Divest: Full divestiture of non-core assets. Gains $25M but wipes synergy multiplier and reduces long-term value."],
     "Option A is the optimal endgame — but it's LOCKED unless you've built Synergy ≥ 80 (primarily through R7's Waste-to-Energy). This is the ultimate test of long-term strategic planning."),
]
for rn,title,icon,crisis,options,insight in rounds2:
    H(f"Round {rn}: {title} {icon}",2)
    doc.add_paragraph(crisis)
    H("Options",3)
    for o in options: doc.add_paragraph(o, style='List Bullet')
    tip("Key Insight",insight)
    doc.add_paragraph()
doc.add_page_break()

# ═══ 9. FLAG SYSTEM ═══
H("9. How Decisions Connect — The Flag System")
doc.add_paragraph("The flag system is the simulation's core systems-thinking mechanic. Every Option A/B/C sets one or more hidden 'flags' that persist across all remaining rounds. These flags unlock bonuses, block options, or modify crisis severity in future rounds. Understanding flag dependencies is what separates good players from great ones.")
H("Critical Flag Dependencies",2)
tbl(["Round","Decision","Flag Set","Impact in Later Rounds"],
    [["R1","Surface Scan (A)","electronics_blindspot","R4 crisis severity DOUBLES (40→80)"],
     ["R1","Deep Audit (B)","deep_audit_completed","R4 crisis severity stays at 40 (normal)"],
     ["R2","Full Alignment (A)","materiality_aligned","+0.10 Mᵣ governance bonus at terminal valuation"],
     ["R2","Ignore (C)","materiality_ignored","40% budget clawback this round"],
     ["R3","Rapid Switch (A)","early_decarboniser","Synergy bonus in R7 circularity transition"],
     ["R3","Green Bond (B)","green_bond_active","NCD reduced over 3 rounds automatically"],
     ["R5","Insurance Only (C)","insurance_only","PERMANENTLY BLOCKS +0.20 Resilience Mᵣ bonus"],
     ["R6","Ethical Overhaul (B)","ethical_ai_overhaul","+0.15 Truth Premium Mᵣ at terminal valuation"],
     ["R7","Waste-to-Energy (C)","synergy_unlock","+0.30 Synergy Mᵣ bonus + enables R10 Option A"],
     ["R8","Prioritise Electronics (B)","electronics_water_priority","PERMANENTLY BLOCKS +0.20 Resilience bonus"],
     ["R9","Community Fund (C)","community_fund","+0.18×JT Community Champion Mᵣ bonus"],
     ["R9","Managed Transition (B)","managed_transition","+0.12×JT Managed Transition Mᵣ bonus"]])
doc.add_paragraph()
warn("Two flags permanently BLOCK the Resilience Bonus: 'insurance_only' (R5-C) and 'electronics_water_priority' (R8-B). These are irreversible. Choose carefully.")
H("The Golden Path — Maximum Mᵣ Flag Sequence",2)
doc.add_paragraph("To achieve the theoretical maximum Mᵣ of 2.08, you need this specific flag combination:")
bl(["R1-B: deep_audit_completed (protects R4)","R2-A: materiality_aligned (+0.10)","R5-A or B: NOT insurance_only (protects +0.20)","R6-B: ethical_ai_overhaul (+0.15)","R7-C: synergy_unlock (+0.30)","R8-A or C: NOT electronics_water_priority (protects +0.20)","R9-C: community_fund (+0.18×JT)","R10-A: resist_integrate (synergy bonus)","Maintain avg SLO ≥ 75 (avoids -0.40 penalty)","Workforce Readiness ≥ 75 (+0.10)","Avg Burnout < 20 (+0.05)"])
doc.add_page_break()

# ═══ 10. TERMINAL VALUATION ═══
H("10. Terminal Valuation — How You're Scored")
doc.add_paragraph("At Round 10, the simulation calculates your company's final enterprise value. This is the ultimate measure of your strategic performance across all 10 rounds.")
img("terminal_valuation.png", Inches(5.5))
cap("Figure 10.1 — Terminal Valuation Components")
doc.add_paragraph()
H("The Formula",2)
formula("EBITDA 2050","EBITDA = Σ(Revenueᵢ − OPEXᵢ) − (tCO₂e × $250 Carbon Tax)")
formula("Terminal Value","TV = EBITDA × Exit_Multiple(12×) × Mᵣ")
doc.add_paragraph("The three components work multiplicatively — weakness in any one dimension severely impacts the total:")
bl(["EBITDA: Driven by revenue growth, OPEX reduction through synergy, and carbon intensity reduction (lower carbon tax bill).",
    "Exit Multiple (12×): Standard industry multiple. Can be reduced in certain ending pathways (e.g., Hostile Takeover drops it to 8-10×).",
    "Mᵣ (Regenerative Multiple): The sustainability-adjusted multiplier. This is where your ESG decisions pay off or punish you."])
H("Mᵣ Breakdown — Complete Component Table",2)
tbl(["Component","Bonus/Penalty","Condition to Earn","Flag Required"],
    [["Base","1.00","Always applied","—"],
     ["Materiality Governance","+0.10","Full materiality alignment in R2","materiality_aligned"],
     ["Synergy Excellence","+0.30","Waste-to-Energy in R7 AND Synergy ≥ 80","synergy_unlock"],
     ["Resilience Champion","+0.20","Avoid both insurance_only AND water_priority","NOT insurance_only, NOT electronics_water_priority"],
     ["Truth Premium","+0.15","Ethical AI Overhaul in R6","ethical_ai_overhaul"],
     ["Community Champion","+0.18×JT","Community Investment Fund in R9","community_fund"],
     ["Just Transition","+0.12×JT","Managed Transition in R9","managed_transition"],
     ["Workforce Excellence","+0.10","Workforce Readiness ≥ 75 at R10","—"],
     ["Wellbeing Champion","+0.05","Average Burnout < 20 at R10","—"],
     ["Comeback Kid","+0.05","Momentum Score > 70 for 2+ consecutive rounds","—"],
     ["INSTABILITY DISCOUNT","−0.40","PENALTY: Average SLO < 75 at R10","—"]])
doc.add_paragraph()
formula("JT Scaling","JT = min(1.5, 1.0 + HR_Investment_Rounds × 0.10)")
doc.add_paragraph("The JT scaling rewards sustained HR investment. If you invested in HR pillars for 5 rounds, JT = 1.5, making the Community Champion bonus worth +0.27 Mᵣ instead of +0.18.")
formula("Maximum Achievable Mᵣ","2.08")
doc.add_page_break()

# ═══ 11. ARCHETYPES ═══
H("11. Company Archetypes — Your Final Profile")
doc.add_paragraph("Your Mᵣ score at Round 10 determines which archetype your company receives. This is your strategic legacy — the narrative outcome of 10 rounds of decisions.")
img("archetypes.png", Inches(5.5))
cap("Figure 11.1 — The Five Company Archetypes")
doc.add_paragraph()
tbl(["Archetype","Mᵣ Range","Description","What It Tells You"],
    [["🌱 Regenerative Titan","≥ 1.80","You built a truly sustainable enterprise that creates value for all stakeholders.","Exceptional — requires near-perfect flag collection and metric management across all 10 rounds."],
     ["🏦 De-risked Safe-Haven","1.20 – 1.79","Strong ESG integration with solid financial returns. A company built to last.","Very good — the realistic 'best case' for most teams. Demonstrates genuine strategic thinking."],
     ["⚠️ Fragile Giant","0.80 – 1.19","Profitable but vulnerable. You've managed finances but left ESG risks unaddressed.","Average — you survived but haven't built resilience. Future shocks could be devastating."],
     ["💀 Stranded Relic","< 0.80","The market sees your company as a declining asset with unmanageable ESG liabilities.","Poor — systemic underinvestment in sustainability has eroded your enterprise value."],
     ["🔧 Turnaround Manager","Survival Mode","You entered distress mode but demonstrated adaptive leadership in recovery.","Special — awarded when a team successfully navigates the 4-phase turnaround pathway."]])
doc.add_paragraph()
H("Alternative Ending Pathways",2)
doc.add_paragraph("Your facilitator may select one of five different ending pathways, each with unique R10 crises, Mᵣ modifiers, and archetype variants:")
tbl(["Pathway","R10 Crisis","Key Mechanic"],
    [["Activist Ultimatum","Restructuring demand","Standard pathway — synergy-gated options"],
     ["Climate Black Swan","Stranded asset reckoning","Carbon tax triples to $750/t; CI-based exit multiple haircut"],
     ["Stakeholder Revolt","Triple stakeholder ultimatum","SLO and Burnout thresholds gate Social Regeneration bonus (+0.35)"],
     ["Hostile Takeover","Corporate raider bid","Synergy and treasury gate White Knight defence (+0.25)"],
     ["Regulatory Shutdown","Compliance reckoning","Ethical score gates Regulatory Exemplar bonus (+0.30)"]])
doc.add_paragraph()
tip("Note","You won't know which pathway your facilitator has selected. The foreshadowing events in Rounds 5-8 provide clues — read the Market Reality Feed carefully.")

out = os.path.join(os.path.dirname(__file__), "_student_guide_part2.docx")
doc.save(out)
print(f"Part 2 saved: {out}")
