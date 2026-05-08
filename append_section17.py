"""
Append Section 17: Regulatory Sandbox — Facilitator Instrument Guide
to Muressons_Simulation_Briefings ver 10.docx → ver 11.
"""
import docx, os
from docx.shared import Pt, RGBColor
from docx.enum.table import WD_TABLE_ALIGNMENT

BASE = r"c:\Users\Home\.gemini\antigravity\scratch\muressons-sim"
SRC = os.path.join(BASE, "Muressons_Simulation_Briefings ver 10.docx")
OUT = os.path.join(BASE, "Muressons_Simulation_Briefings ver 11.docx")

def formula(doc, text):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.name = 'Courier New'
    r.font.size = Pt(10)

def cite(doc, text):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.italic = True
    r.font.size = Pt(10)
    r.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

def tbl(doc, headers, rows):
    t = doc.add_table(rows=1+len(rows), cols=len(headers))
    t.style = 'Light Grid Accent 1'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        t.rows[0].cells[i].text = h
        for run in t.rows[0].cells[i].paragraphs[0].runs:
            run.bold = True
    for ri, row in enumerate(rows, 1):
        for ci, val in enumerate(row):
            t.rows[ri].cells[ci].text = str(val)
    doc.add_paragraph()

def run():
    if not os.path.exists(SRC):
        print(f"Not found: {SRC}"); return
    doc = docx.Document(SRC)
    doc.add_page_break()

    # ═══ SECTION 17 ═══
    doc.add_heading('Section 17: Regulatory Sandbox \u2014 Facilitator Instrument Guide & Theoretical Reference', level=1)

    doc.add_paragraph(
        'This section provides the comprehensive facilitator reference for all six regulatory '
        'instruments available in the Regulatory Sandbox (SE-7). For each instrument, we document '
        'the theoretical foundation, configurable parameters, mathematical effects, time-series '
        'decay mechanics, and worked numerical examples. This guide complements Section 16 '
        '(Middleware Intercept Architecture) by focusing on the pedagogical and operational '
        'aspects of deploying regulations in the classroom.'
    )

    # ─── 17.1 Access Control ────
    doc.add_heading('17.1 Access Control & Enablement', level=2)
    doc.add_paragraph(
        'The Regulatory Sandbox is gated behind a two-layer access control model:'
    )
    doc.add_paragraph('Layer 1 \u2014 God Mode Toggle: The Super Administrator must enable the '
        '"regulatory_sandbox_enabled" toggle in God Mode\'s System Engine Modules panel. '
        'This toggle defaults to OFF (false) and must be explicitly activated before any '
        'facilitator can access the sandbox.', style='List Bullet')
    doc.add_paragraph('Layer 2 \u2014 Role-Based Access: Only Lead Facilitators (role = lead_facilitator) '
        'and Super Administrators (role = super_admin) can see the Regulatory Sandbox tab. '
        'Base facilitators never see it regardless of the God Mode toggle state.', style='List Bullet')
    doc.add_paragraph('Real-Time Sync: The facilitator dashboard polls the scaffolding-status '
        'endpoint every 30 seconds. When God Mode enables the sandbox, the tab appears in '
        'Lead Facilitator sidebars within 30 seconds without requiring a page refresh.', style='List Bullet')
    doc.add_paragraph(
        'Recommended Workflow: Enable the toggle at cohort creation time for expert-tier cohorts. '
        'Avoid enabling mid-session for beginner cohorts, as the sudden appearance of regulatory '
        'instruments can overwhelm students who lack environmental economics foundations.'
    )

    # ─── 17.2 Instrument Overview ────
    doc.add_heading('17.2 Instrument Overview', level=2)
    doc.add_paragraph(
        'Six regulatory instruments are available, each grounded in a distinct theoretical '
        'framework from environmental economics, institutional economics, or international law. '
        'Instruments can be activated independently or in combination (polycentric governance).'
    )
    tbl(doc,
        ['#', 'Instrument', 'Theory Base', 'Primary KPI Impact', 'Default Cost'],
        [
            ['1', 'Carbon Tax', 'Pigou (1920)', 'OPEX increase per BU CI', '$50/tCO2e'],
            ['2', 'Emissions Trading (ETS)', 'Coase (1960)', 'Permit costs, windfall risk', '$45/t base'],
            ['3', 'Mandatory ESG Disclosure', 'Akerlof (1970)', 'Governance risk \u221215, Rep +3', '$500K compliance'],
            ['4', 'Supply Chain Due Diligence', 'Ruggie (2011)', 'SLO +5, supply chain risk \u221210%', '$300K/tier'],
            ['5', 'Nature Restoration Law', 'Dasgupta (2021)', 'EHI +5 (escalating)', '$750K compliance'],
            ['6', 'Just Transition Fund', 'ILO (2015)', 'SLO +8, strike risk \u221215%', '1% of revenue'],
        ])

    # ─── 17.3 Instrument 1: Carbon Tax ────
    doc.add_heading('17.3 Instrument 1: Carbon Tax (Pigouvian Taxation)', level=2)
    cite(doc, 'Pigou, A. C. (1920). The Economics of Welfare. London: Macmillan.')
    doc.add_paragraph(
        'A direct price on carbon emissions that forces firms to internalise negative externalities. '
        'The tax is applied per-Business Unit based on each unit\'s absolute carbon footprint, '
        'creating internal pressure for portfolio restructuring toward low-carbon operations.'
    )
    doc.add_heading('Parameters', level=3)
    tbl(doc, ['Parameter', 'Range', 'Default', 'Unit'],
        [['rate_per_tonne', '10\u2013500', '50', '$/tCO2e'],
         ['annual_escalation_pct', '0\u201320', '5', '%/round'],
         ['border_adjustment', 'true/false', 'true', 'boolean']])

    doc.add_heading('Mathematical Formula', level=3)
    formula(doc,
        'BU_Emissions = Carbon_Intensity \u00d7 Revenue_Base / 1,000,000  (tonnes CO2e)\n'
        'Current_Rate = Base_Rate \u00d7 (1 + Escalation%)^Rounds_Active\n'
        'Tax_Cost = AVG(CI) \u00d7 Current_Rate \u00d7 Num_BUs \u00d7 100\n'
        'Per-BU Penalty = BU_Emissions \u00d7 Current_Rate  (added to BU OPEX)')

    doc.add_heading('Worked Example', level=3)
    doc.add_paragraph('Scenario: Carbon tax at $85/tonne, 5% escalation, Round 7 (2 rounds after activation in R5).', style='List Bullet')
    doc.add_paragraph('Current Rate = $85 \u00d7 (1.05)^2 = $85 \u00d7 1.1025 = $93.71/tonne', style='List Bullet')
    doc.add_paragraph('Electronics BU: CI=60, Revenue=$22M \u2192 Emissions = 60 \u00d7 22,000,000 / 1,000,000 = 1,320t', style='List Bullet')
    doc.add_paragraph('Electronics Penalty = 1,320 \u00d7 $93.71 = $123,697 added to OPEX', style='List Bullet')
    doc.add_paragraph('Software BU: CI=10, Revenue=$20M \u2192 200t \u00d7 $93.71 = $18,742 (6.6\u00d7 less)', style='List Bullet')
    doc.add_paragraph('Decay: Carbon tax has NO decay \u2014 escalation is built into the rate formula.', style='List Bullet')
    doc.add_paragraph(
        'Debrief Point: Ask students to compare the cost differential between high-CI and low-CI '
        'units. Does the tax create sufficient incentive for portfolio restructuring, or is absorbing '
        'the cost cheaper than divesting? What does Pigou\'s theory predict about the "correct" rate?'
    )

    # ─── 17.4 Instrument 2: ETS ────
    doc.add_heading('17.4 Instrument 2: Emissions Trading System (ETS)', level=2)
    cite(doc, 'Coase, R. H. (1960). "The Problem of Social Cost." Journal of Law and Economics, 3, 1\u201344.')
    doc.add_paragraph(
        'A cap-and-trade mechanism with a declining annual cap. Free allocation phases out over time, '
        'causing the effective permit cost to escalate. Models the EU ETS structure with optional '
        'Market Stability Reserve.'
    )
    doc.add_heading('Parameters', level=3)
    tbl(doc, ['Parameter', 'Range', 'Default', 'Unit'],
        [['initial_cap_reduction_pct', '1\u201310', '4.2', '%/year'],
         ['free_allocation_pct', '0\u2013100', '50', '%'],
         ['market_stability_reserve', 'true/false', 'true', 'boolean']])

    doc.add_heading('Decay & Escalation Mechanics', level=3)
    formula(doc,
        'Free_Allocation = MAX(0, Initial_Free% \u2212 0.05 \u00d7 Rounds_Active)\n'
        'Permit_Price = Base_Price \u00d7 (1 + 0.08)^Rounds_Active\n'
        'Effective_Cost = Permit_Price \u00d7 (1 \u2212 Free_Allocation)\n'
        'ETS_Cost = AVG(CI) \u00d7 Effective_Cost \u00d7 Num_BUs \u00d7 50')

    doc.add_heading('Worked Example', level=3)
    doc.add_paragraph('Activation: R4, free allocation 50%, base permit $45. Evaluating at R7 (3 rounds active).', style='List Bullet')
    doc.add_paragraph('Free Allocation = MAX(0, 0.50 \u2212 0.05 \u00d7 3) = MAX(0, 0.35) = 35%', style='List Bullet')
    doc.add_paragraph('Permit Price = $45 \u00d7 (1.08)^3 = $45 \u00d7 1.2597 = $56.69', style='List Bullet')
    doc.add_paragraph('Effective Cost = $56.69 \u00d7 (1 \u2212 0.35) = $56.69 \u00d7 0.65 = $36.85/t', style='List Bullet')
    doc.add_paragraph('With AVG(CI)=37.5 and 4 BUs: ETS_Cost = 37.5 \u00d7 $36.85 \u00d7 4 \u00d7 50 = $276,375', style='List Bullet')
    doc.add_paragraph(
        'Key Insight: Free allocation decay means early rounds are cheap but later rounds become '
        'expensive. Students who delay decarbonisation face escalating permit costs \u2014 a direct '
        'parallel to the EU ETS Phase IV free allocation phase-out schedule.'
    )

    # ─── 17.5 Instrument 3: Mandatory Disclosure ────
    doc.add_heading('17.5 Instrument 3: Mandatory ESG Disclosure (CSRD-style)', level=2)
    cite(doc, 'Akerlof, G. A. (1970). "The Market for Lemons." Quarterly Journal of Economics, 84(3), 488\u2013500.')
    doc.add_paragraph(
        'Mandatory sustainability reporting with assurance requirements. Reduces information asymmetry '
        '(Akerlof\'s "lemons problem") but imposes compliance costs that decay over time as '
        'organisations build internal reporting routines (Arrow 1962 learning curve).'
    )
    doc.add_heading('Decay Mechanics (Arrow 1962 Learning Curve)', level=3)
    formula(doc,
        'Cost(t) = Initial_Cost \u00d7 (1 \u2212 0.40)^t,  floored at 20% of initial\n'
        'Rep_Boost(t) = Initial_Boost \u00d7 (1 \u2212 0.30)^t  (Goodhart\'s Law decay)\n'
        'Governance Risk: \u22125 per BU per round (structural, no decay)')

    doc.add_heading('Worked Example', level=3)
    doc.add_paragraph('Activation: R3, "reasonable" scope, double materiality ON. Evaluating at R6 (3 rounds active).', style='List Bullet')
    doc.add_paragraph('Compliance Cost = $500K \u00d7 (0.60)^3 = $500K \u00d7 0.216 = $108K (floor = $100K \u2192 use $108K)', style='List Bullet')
    doc.add_paragraph('Reputation Boost = 3 \u00d7 (0.70)^3 = 3 \u00d7 0.343 = +1.03 pts (was +3 in R3)', style='List Bullet')
    doc.add_paragraph('Governance Risk: \u22125 per BU every round (cumulative structural improvement)', style='List Bullet')
    doc.add_paragraph(
        'Debrief Point: The compliance cost halves rapidly but the reputation boost also decays \u2014 '
        'illustrating Goodhart\'s Law: once disclosure becomes universal, it no longer differentiates. '
        'Ask: "If everyone discloses, does disclosure still create competitive advantage?"'
    )

    # ─── 17.6 Instrument 4: Due Diligence ────
    doc.add_heading('17.6 Instrument 4: Supply Chain Due Diligence (CS3D-style)', level=2)
    cite(doc, 'Ruggie, J. (2011). Guiding Principles on Business and Human Rights. UN Human Rights Council.')
    doc.add_paragraph(
        'Mandatory human rights and environmental due diligence across configurable supply chain tiers. '
        'Cost decays as audit routines mature, but social license boost also decays as due diligence '
        'becomes table-stakes.'
    )
    doc.add_heading('Decay Mechanics', level=3)
    formula(doc,
        'Cost_Per_Tier(t) = $300K \u00d7 (1 \u2212 0.10)^t,  floored at 50% ($150K)\n'
        'Total_Cost = Cost_Per_Tier \u00d7 Tiers_Covered\n'
        'SLO_Boost(t) = (5/4) \u00d7 (1 \u2212 0.20)^t  per BU per round')

    doc.add_heading('Worked Example', level=3)
    doc.add_paragraph('Activation: R4, 3 tiers, civil liability, safe harbour ON. Evaluating at R8 (4 rounds active).', style='List Bullet')
    doc.add_paragraph('Cost/Tier = $300K \u00d7 (0.90)^4 = $300K \u00d7 0.6561 = $196,830 (\u003e floor $150K)', style='List Bullet')
    doc.add_paragraph('Total Cost = $196,830 \u00d7 3 tiers = $590,490', style='List Bullet')
    doc.add_paragraph('SLO Boost = 1.25 \u00d7 (0.80)^4 = 1.25 \u00d7 0.4096 = +0.51 pts/BU (was +1.25)', style='List Bullet')
    doc.add_paragraph(
        'Debrief Point: Due diligence costs decrease as audit routines mature, but the SLO benefit '
        'also fades as it becomes an industry norm. This illustrates the "first-mover advantage" in '
        'ESG: early adopters gain disproportionate stakeholder trust.'
    )

    # ─── 17.7 Instrument 5: Nature Restoration ────
    doc.add_heading('17.7 Instrument 5: Nature Restoration Law (EU NRL-style)', level=2)
    cite(doc, 'Dasgupta, P. (2021). The Economics of Biodiversity: The Dasgupta Review. HM Treasury, UK.')
    doc.add_paragraph(
        'Binding targets for ecosystem restoration. Unlike other instruments, the EHI (Ecosystem '
        'Health Index) bonus ESCALATES over time as restoration investments compound \u2014 modelling '
        'the positive feedback loop of ecosystem recovery described in Dasgupta (2021).'
    )
    doc.add_heading('Decay & Escalation', level=3)
    formula(doc,
        'Cost(t) = $750K \u00d7 (1 \u2212 0.15)^t,  floored at 30% ($225K)\n'
        'EHI_Bonus(t) = 5 \u00d7 (1 + 0.10)^t  (ESCALATING, not decaying)')

    doc.add_heading('Worked Example', level=3)
    doc.add_paragraph('Activation: R3, 20% restoration target, annual reporting. Evaluating at R7 (4 rounds).', style='List Bullet')
    doc.add_paragraph('Cost = $750K \u00d7 (0.85)^4 = $750K \u00d7 0.522 = $391,500 (\u003e floor $225K)', style='List Bullet')
    doc.add_paragraph('EHI Bonus = 5 \u00d7 (1.10)^4 = 5 \u00d7 1.4641 = +7.32 pts to Ecosystem Health Index', style='List Bullet')
    doc.add_paragraph(
        'Key Insight: Nature restoration is the only instrument where the BENEFIT escalates while '
        'costs decay. This models the real-world phenomenon where ecosystem recovery accelerates '
        'once critical thresholds are passed (tipping points in reverse). Early activation yields '
        'compounding ecological returns.'
    )

    # ─── 17.8 Instrument 6: Just Transition Fund ────
    doc.add_heading('17.8 Instrument 6: Just Transition Fund', level=2)
    cite(doc, 'ILO (2015). Guidelines for a Just Transition towards Environmentally Sustainable Economies and Societies for All.')
    doc.add_paragraph(
        'Mandatory corporate contributions to fund worker reskilling and community transition. '
        'The treasury cost is a fixed percentage of revenue (no decay \u2014 legal obligation), '
        'but the social license and strike-reduction benefits decay over time as goodwill has '
        'a half-life (Goodhart\'s Law).'
    )
    doc.add_heading('Decay Mechanics', level=3)
    formula(doc,
        'Contribution = Total_Revenue \u00d7 Contribution_Rate%  (FIXED, no decay)\n'
        'SLO_Boost(t) = (8/4) \u00d7 (1 \u2212 0.30)^t  per BU per round\n'
        'Strike_Reduction(t) = 0.15 \u00d7 (1 \u2212 0.25)^t\n'
        'Burnout_Reduction = \u22125/4 per BU per round  (structural, no decay)')

    doc.add_heading('Worked Example', level=3)
    doc.add_paragraph('Activation: R5, contribution 1.5% of revenue. Total BU revenue = $75M. At R8 (3 rounds).', style='List Bullet')
    doc.add_paragraph('Contribution = $75M \u00d7 0.015 = $1,125,000 per round (fixed)', style='List Bullet')
    doc.add_paragraph('SLO Boost = 2.0 \u00d7 (0.70)^3 = 2.0 \u00d7 0.343 = +0.686 pts/BU (was +2.0)', style='List Bullet')
    doc.add_paragraph('Strike Reduction = 0.15 \u00d7 (0.75)^3 = 0.15 \u00d7 0.4219 = \u22126.3% (was \u221215%)', style='List Bullet')
    doc.add_paragraph('Burnout Reduction = \u22121.25 per BU every round (constant)', style='List Bullet')

    # ─── 17.9 Complexity & Capture ────
    doc.add_heading('17.9 Regulatory Complexity Index & Capture Risk', level=2)
    doc.add_paragraph(
        'Two meta-indicators track the systemic effects of regulatory layering:'
    )
    doc.add_heading('Complexity Index (0\u2013100)', level=3)
    formula(doc, 'Complexity_Index = MIN(100, Active_Regulations \u00d7 15)')
    doc.add_paragraph('1 instrument = 15, 2 = 30, 3 = 45 ... 7+ = 100 (cap).', style='List Bullet')

    doc.add_heading('Regulatory Capture Risk (Stigler 1971)', level=3)
    cite(doc, 'Stigler, G. J. (1971). "The Theory of Economic Regulation." Bell Journal of Economics, 2(1), 3\u201321.')
    formula(doc,
        'If Active_Regulations > 4:\n'
        '  Capture_Risk = MIN(100, (Active_Regulations \u2212 4) \u00d7 20)\n'
        'Else: Capture_Risk = 0')
    doc.add_paragraph(
        'Warning displayed at capture risk > 40%: "Stigler (1971) warns that excessive regulation '
        'complexity creates opportunities for regulatory capture. Consider simplification."'
    )

    # ─── 17.10 Polycentric Burden ────
    doc.add_heading('17.10 Polycentric Asymmetric Burden (Ostrom 2009)', level=2)
    doc.add_paragraph(
        'When 2+ instruments are simultaneously active, each BU receives an asymmetric compliance '
        'burden based on its industrial and geographic footprint:'
    )
    formula(doc,
        'Carbon_Weight = MIN(CI / 100, 1.0) \u00d7 0.05  (0\u20135% of revenue)\n'
        'Water_Weight  = MIN(Water_Dep, 1.0) \u00d7 0.03  (0\u20133% of revenue)\n'
        'Burden_Cost   = Revenue \u00d7 (Carbon_Weight + Water_Weight)')

    tbl(doc,
        ['Business Unit', 'CI', 'Water Dep', 'Revenue', 'Burden Rate', 'Burden Cost'],
        [['Pharmaceuticals', '45', '0.60', '$18M', '4.05%', '$729K'],
         ['Electronics', '60', '0.80', '$22M', '5.40%', '$1.19M'],
         ['Consumer Goods', '30', '0.30', '$15M', '2.40%', '$360K'],
         ['Software', '10', '0.10', '$20M', '0.80%', '$160K']])

    # ─── 17.11 Classroom Deployment ────
    doc.add_heading('17.11 Classroom Deployment Guide', level=2)

    doc.add_heading('Pre-Session Checklist', level=3)
    doc.add_paragraph('Enable "Regulatory Sandbox" AND "NPC Stakeholders" in God Mode toggles.', style='List Number')
    doc.add_paragraph('Verify cohort is set to Expert experience level.', style='List Number')
    doc.add_paragraph('Brief students on Pigou, Coase, and Ostrom frameworks (15 min pre-reading recommended).', style='List Number')
    doc.add_paragraph('Prepare the sandbox tab with a carbon tax at $85/tonne (recommended starting rate).', style='List Number')

    doc.add_heading('Suggested Activation Timeline', level=3)
    tbl(doc,
        ['Round', 'Action', 'Rationale'],
        [['R3\u2013R4', 'Activate Carbon Tax ($85/t, 5% escalation)', 'Gives students 2\u20133 rounds to observe per-BU cost differential'],
         ['R5', 'Add Mandatory Disclosure (reasonable scope)', 'Tests interaction between pricing and transparency'],
         ['R6', 'Activate ETS (50% free allocation)', 'Creates polycentric governance (3 instruments \u2192 Ostrom kicks in)'],
         ['R7\u2013R8', 'Observe or force-trigger exogenous events', 'Carbon Minsky Moment (R7), Water Shock (R8)'],
         ['R9\u2013R10', 'Debrief using intercept_log diagnostics', 'Walk through exact cause-and-effect chains']])

    doc.add_heading('Common Student Reactions & Facilitator Responses', level=3)
    doc.add_paragraph('"The carbon tax is unfair to Electronics!" \u2014 Response: "That\'s exactly Pigou\'s point. '
        'The tax is proportional to damage. Should polluters pay less than their fair share?"', style='List Bullet')
    doc.add_paragraph('"We can\'t afford compliance AND investment!" \u2014 Response: "This is the regulatory '
        'trilemma: growth, compliance, and sustainability. Which will you sacrifice?"', style='List Bullet')
    doc.add_paragraph('"Too many regulations at once!" \u2014 Response: "You\'re experiencing Ostrom\'s polycentric '
        'governance. Is the complexity a feature or a bug? What does Stigler say about capture risk?"', style='List Bullet')

    # ─── 17.12 Summary of Decay Constants ────
    doc.add_heading('17.12 Summary of All Decay & Escalation Constants', level=2)
    tbl(doc,
        ['Instrument', 'Cost Decay', 'Cost Floor', 'Benefit Decay', 'Special'],
        [['Carbon Tax', 'None', 'N/A', 'None', 'Rate escalates at configured %/round'],
         ['ETS', 'N/A', 'N/A', 'N/A', 'Free alloc \u22125%/round; permit price +8%/round'],
         ['Mandatory Disclosure', '40%/round', '20% of initial', 'Rep boost 30%/round', 'Governance risk reduction constant'],
         ['Due Diligence', '10%/round', '50% of initial', 'SLO boost 20%/round', 'Audit routines mature'],
         ['Nature Restoration', '15%/round', '30% of initial', 'EHI bonus +10%/round', 'Only instrument with escalating benefit'],
         ['Just Transition Fund', 'Fixed (legal)', 'N/A', 'SLO 30%/round; Strike 25%/round', 'Burnout reduction constant']])

    doc.add_paragraph(
        'Note: All decay functions use exponential decay: Value(t) = Initial \u00d7 (1 \u2212 Rate)^t, '
        'floored at Initial \u00d7 Floor_Fraction. This is grounded in Arrow (1962) learning-curve theory '
        'for cost decay and Goodhart\'s Law for benefit signal attenuation.'
    )
    cite(doc, 'Arrow, K. J. (1962). "The Economic Implications of Learning by Doing." '
        'Review of Economic Studies, 29(3), 155\u2013173.')

    # Save
    doc.save(OUT)
    print(f"Successfully created: {OUT}")

if __name__ == '__main__':
    run()
