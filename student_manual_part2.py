"""
Muressons Global Corporation — Student Manual Generator (Part 2)
Sections 8-14: Math Engines, KPIs, Scoring, Glossary, Appendices
"""
import os
from student_manual_helpers import *

IMG = os.path.join(os.path.dirname(__file__), 'guide_images')

def build_part2(doc):
    # ══════════════════ PART III HEADER ══════════════════
    t = h(doc, 'PART III: UNDER THE HOOD', 1, TEAL)
    page_break(doc)

    # ══════════════════ § 8: MATH ENGINES ══════════════════
    h(doc, '8. Mathematical Engines Explained', 1)
    body(doc, 'The simulation is powered by a suite of mathematical engines that process your decisions. Understanding these engines is key to strategic mastery.')

    h(doc, '8.1 Core Engines', 2)

    formula_block(doc, '8.1.1 Corporate Strategic Fund (CSF)',
        'CSF = Σ(Revenue_i - OPEX_i) - Dividends_Paid',
        'Calculates net cash added to treasury each round. If total CAPEX exceeds 20% of treasury, a loan is triggered at 12% interest.',
        ['Given: Pharma Rev=$18M, OPEX=$11M; Electronics Rev=$22M, OPEX=$14M; CG Rev=$15M, OPEX=$9M; Software Rev=$20M, OPEX=$8M',
         'Gross Profit = (18-11)+(22-14)+(15-9)+(20-8) = 7+8+6+12 = $33M',
         'Dividends = $2M → CSF = $33M - $2M = $31M added to treasury'])

    formula_block(doc, '8.1.2 Contagion Engine (Sigmoid Model)',
        'Group_Rep = AVG(BU_Rep) - 50 × sigmoid((severity - 30) / 15)',
        'Uses an S-curve (sigmoid) centred at severity=30. Low severity (<15): minimal impact. Medium (20-40): rapid erosion. High (>50): saturating damage.',
        ['Given: BU Reps = [70, 58, 74, 82], Crisis Severity = 40',
         'AVG Rep = (70+58+74+82)/4 = 71.0',
         'sigmoid((40-30)/15) = sigmoid(0.667) = 1/(1+e^-0.667) ≈ 0.661',
         'Group_Rep = 71.0 - 50 × 0.661 = 71.0 - 33.05 = 37.95',
         'If electronics_blindspot active: severity doubles to 80 → Group_Rep = 71 - 48.4 = 22.6'])

    formula_block(doc, '8.1.3 Synergy Engine (Diminishing Returns)',
        'effective_ratio = √(ratio) × 0.7; New_OPEX = Old_OPEX × (1 - effective_ratio × Synergy_Mult)',
        'Uses square-root scaling: first dollars yield outsized returns, later dollars hit diminishing marginal efficiency.',
        ['Given: OPEX=$11M, Investment_Ratio=0.25, Synergy_Mult=1.08',
         'effective_ratio = √(0.25) × 0.7 = 0.5 × 0.7 = 0.35',
         'factor = 1 - (0.35 × 1.08) = 1 - 0.378 = 0.622',
         'New_OPEX = $11M × 0.622 = $6.84M (savings of $4.16M)'])

    formula_block(doc, '8.1.4 Natural Capital Cost of Debt',
        'Interest_Rate = Base_Rate + (NCD × 0.0001); Debt_Next = Debt + (Debt × Rate)',
        'Environmental debt compounds each round. At NCD=100: rate ≈ 6%. At NCD=500: rate ≈ 10%. At NCD=1000: rate ≈ 15%.',
        ['Given: NCD=5,200, Base_Rate=0.05',
         'Rate = 0.05 + (5200 × 0.0001) = 0.57 (57%)',
         'Debt_Next = 5,200 + (5,200 × 0.57) = 8,164 — compounds aggressively!'])

    formula_block(doc, '8.1.5 VRIO Decay',
        'Advantage_Next = Advantage_Current × (1 - Decay_Rate)',
        'Prevents synergy from staying permanently high. Default decay = 5% per round.',
        ['Given: Synergy_Mult=1.38, Decay_Rate=0.05',
         'Next = 1.38 × 0.95 = 1.311',
         'After 3 rounds: 1.38 → 1.311 → 1.245 → 1.183'])

    formula_block(doc, '8.1.6 Talent Brain-Drain',
        'Penalty = 1 + MAX(0, (65-Rep)/100) × 1.5 + burnout_adj',
        'Software BU OPEX inflates when Group Reputation < 65. Burnout > 50 adds further overhead.',
        ['Given: Group_Rep=55, Software OPEX=$8M, Burnout=60',
         'Rep Penalty = 1 + ((65-55)/100) × 1.5 = 1.15',
         'Burnout adj = ((60-50)/100) × 2.0 = 0.20',
         'Total: 1.35 → New OPEX = $8M × 1.35 = $10.8M (+35%)'])

    formula_block(doc, '8.1.7 Strike Probability (R9)',
        'P_Strike = Base_Risk + ((1 - SLO/100) × 0.4)',
        'Triggered in R9 with Immediate Closure option. Burnout > 50 adds up to +20%.',
        ['Given: Base_Risk=0.25, SLO=35, Burnout=65',
         'P_Strike = 0.25 + ((1 - 0.35) × 0.4) = 0.25 + 0.26 = 0.51',
         'Burnout boost = 0.06 → Final = 0.57 (57% chance)',
         'If strike fires: revenue for ALL BUs zeroed for the round'])

    formula_block(doc, '8.1.8 Natural Decay (Entropy)',
        'If CAPEX = 0: Rep_Next = Rep × 0.98, SLO_Next = SLO × 0.98',
        'BUs receiving zero investment decay 2% per round. Simulates organisational entropy.',
        ['Given: Rep=70, SLO=65, No investment',
         'Rep_Next = 70 × 0.98 = 68.6, SLO_Next = 65 × 0.98 = 63.7',
         'After 5 rounds of neglect: Rep = 70 × 0.98^5 = 63.3'])

    h(doc, '8.2 Advanced Engines (Available in Advanced/Expert Tiers)', 2)
    adv_engines = [
        ('Macroeconomic Inflation', '+2.5% OPEX per round — players must invest just to tread water'),
        ('Execution Overrun Risk', '25% chance of +15% cost overrun if CAPEX > $3M'),
        ('Technical Debt', '+4% OPEX after 2+ consecutive zero-investment rounds'),
        ('Revenue Cannibalization', 'Market-overlap matrix penalises dominant BUs stealing sibling revenue'),
        ('Stakeholder Fatigue', 'Trust recovery efficiency = 1/(1 + 0.3 × crisis_count)'),
        ('Supply Chain Contagion', 'High governance risk spreads OPEX surcharges across BUs'),
        ('Competitive NPC Index', 'NPC competitor grows at 6%/round — falling behind loses market share'),
        ('Working Capital / Cash Conversion', 'Governance risk reduces realised cash'),
        ('Dividend Ratchet', 'Cutting dividends >20% triggers -5 reputation penalty'),
        ('Talent Allocation Pressure', 'BUs receiving <15% CAPEX share get 2% OPEX surcharge'),
        ('Technology Lock-In', 'Same BU getting highest CAPEX for 3+ rounds penalises others'),
        ('ESG Greenwashing Engine', 'Green rhetoric without investment (avg ratio < 15%) triggers scandal'),
        ('FX Risk Engine', '±5% stochastic currency movements (exposure-weighted by BU)'),
        ('Macro Interest Rate Cycles', 'R1-3: easing (-0.5%), R4-6: neutral, R7-9: tightening (+0.5%), R10: crisis (+1%)'),
    ]
    for name, desc in adv_engines:
        bullet(doc, desc, bold_prefix=f'{name}: ')
    page_break(doc)

    # ══════════════════ § 9: KPI DEEP DIVE ══════════════════
    h(doc, '9. KPI Deep Dive', 1)
    body(doc, 'Understanding every Key Performance Indicator is essential for strategic success:')
    styled_table(doc,
        ['KPI', 'Range', 'Good ↑', 'Bad ↓', 'Why It Matters'],
        [('Corporate Treasury', '$0 → ∞', '> $30M', '< $5M', 'Investment capacity, loan triggers'),
         ('Group Reputation', '0–100', '> 65', '< 40', 'Brain-drain trigger, contagion vulnerability'),
         ('Carbon Intensity', '0–100', '< 25', '> 50', 'Carbon tax cost, climate tipping points'),
         ('Synergy Multiplier', '0.5–2.0+', '> 1.3', '< 0.8', 'OPEX reduction effectiveness, R10 gate'),
         ('Social License (SLO)', '0–100', '> 75', '< 40', 'Strike risk, M_R instability discount'),
         ('Natural Capital Debt', '0–1M', '< 100', '> 500', 'Debt compounding, interest surcharge'),
         ('Governance Risk', '0–100', '< 15', '> 30', 'Cash conversion delay, supply chain contagion'),
         ('Staff Burnout', '0–100', '< 20', '> 70', 'OPEX penalty, M_R wellbeing bonus'),
         ('Workforce Readiness', '0–100', '> 75', '< 40', 'Pillar effectiveness, M_R bonus')])
    body(doc, 'Critical Thresholds to Monitor:', bold=True)
    bullet(doc, 'Treasury < $5M → Triggers Turnaround Mode (survival phase)')
    bullet(doc, 'SLO < 75 across all BUs → Triggers -0.40 Instability Discount on M_R')
    bullet(doc, 'Burnout > 70 → Critical OPEX penalties + governance risk increase')
    bullet(doc, 'Carbon Intensity > 50 → Triggers stranded asset penalties in Climate pathway')
    page_break(doc)

    # ══════════════════ § 10: SCORING & TERMINAL VALUATION ══════════════════
    h(doc, '10. Scoring & Terminal Valuation', 1)

    h(doc, '10.1 Terminal EBITDA Calculation', 2)
    body(doc, 'Formula:', bold=True)
    body(doc, 'Terminal_EBITDA = Σ(Revenue_i - OPEX_i) - (Carbon_Tonnage × Carbon_Tax_Per_Ton)')
    body(doc, 'Carbon_Tonnage = Σ(BU_Carbon_Intensity × BU_Revenue / 1,000,000)')
    bullet(doc, 'Standard Carbon Tax: $250/tonne')
    bullet(doc, 'Climate Black Swan pathway: $750/tonne')
    bullet(doc, 'Example: Gross Profit=$33M, Carbon=2,850t → Tax=$712,500 → EBITDA=$32.29M')

    h(doc, '10.2 Regenerative Multiple (M_R)', 2)
    body(doc, 'The M_R is the sustainability-adjusted valuation multiplier that directly multiplies your Terminal Value:')
    styled_table(doc,
        ['Component', 'Value', 'Trigger Condition', 'Source Round'],
        [('Base', '+1.00', 'Always applied', '—'),
         ('CSRD Governance', '+0.10', 'R2A: materiality_aligned flag', 'R2'),
         ('Synergy Excellence', '+0.30', 'R7C: synergy_unlock + synergy ≥ 0.80', 'R7'),
         ('Resilience Champion', '+0.20', 'NOT insurance_only AND NOT electronics_water_priority', 'R5/R8'),
         ('Truth Premium', '+0.15', 'R6B: ethical_ai_overhaul flag', 'R6'),
         ('Community Champion', '+0.18', 'R9C: community_fund flag (× JT scaling)', 'R9'),
         ('Just Transition', '+0.12', 'R9B: managed_transition (alternative)', 'R9'),
         ('Workforce Excellence', '+0.10', 'workforce_readiness ≥ 75 at R10', 'Cumulative HR'),
         ('Wellbeing Champion', '+0.05', 'avg burnout < 20 at R10', 'Cumulative HR'),
         ('Instability Discount', '−0.40', 'avg Social License < 75', 'Cumulative'),
         ('MAXIMUM ACHIEVABLE', '2.08', 'All bonuses, no penalties', '—')])

    h(doc, '10.3 Terminal Value Formula', 2)
    body(doc, 'TV = (Terminal_EBITDA + Green_Fund_Balance) × Exit_Multiple × M_R', bold=True)
    bullet(doc, 'Exit Multiple: 12× (standard) — represents investor confidence')
    bullet(doc, 'Example Titan: EBITDA=$32.29M, Green Fund=$2M, M_R=2.08 → TV = $34.29M × 12 × 2.08 = $856M')
    bullet(doc, 'Example Relic: EBITDA=$28M, Green Fund=$0, M_R=0.60 → TV = $28M × 12 × 0.60 = $202M')

    tv_img = os.path.join(IMG, 'terminal_valuation.png')
    if os.path.exists(tv_img):
        add_image(doc, tv_img, caption='Figure 10.1 — Terminal Valuation Breakdown Screen')

    h(doc, '10.4 What-If Scenario Comparison', 2)
    styled_table(doc,
        ['Scenario', 'M_R', 'Terminal Value', 'Delta vs Baseline'],
        [('Baseline (Fragile Giant)', '1.05', '~$478M', '—'),
         ('+ Resilient Choices (R5B + R8A)', '1.25', '~$570M', '+$91M'),
         ('+ Titan Strategy (all bonuses)', '1.65', '~$752M', '+$273M'),
         ('Maximum Achievable', '2.08', '~$948M', '+$469M')])
    page_break(doc)

    # ══════════════════ § 11: FLAG DEPENDENCIES ══════════════════
    h(doc, '11. Flag Dependencies & Cascades', 1)
    body(doc, 'The "Butterfly Effect" system means early-round decisions compound through cross-round flag dependencies:')
    styled_table(doc,
        ['Source', 'Flag', 'Target', 'Cascade Effect'],
        [('R1A', 'electronics_blindspot', 'R4', 'DOUBLES crisis severity (40→80)'),
         ('R1B', 'deep_audit_completed', 'R4', 'HALVES crisis severity'),
         ('R2A', 'materiality_aligned', 'R10', '+0.10 M_R Governance bonus'),
         ('R3C', 'greenwash_risk', 'R5+', 'Triggers greenwash if avg inv < 15%'),
         ('R3A', 'early_decarboniser', 'R7', '+0.10 synergy multiplier'),
         ('R5C', 'insurance_only', 'R10', 'BLOCKS +0.20 Resilience M_R'),
         ('R6B', 'ethical_ai_overhaul', 'R10', '+0.15 Truth Premium M_R'),
         ('R6C', 'ai_monetised', 'R7+', 'EU AI Act costs from R7 onward'),
         ('R7C', 'synergy_unlock', 'R10', '+0.30 Synergy M_R (highest bonus)'),
         ('R8B', 'electronics_water_priority', 'R10', 'BLOCKS +0.20 Resilience M_R'),
         ('R9C', 'community_fund', 'R10', '+0.18 Community Champion M_R'),
         ('R9B', 'managed_transition', 'R10', '+0.12 Just Transition M_R')])
    body(doc, 'Key Insight: The most impactful flags are set in R1 (blindspot), R6 (ethics), and R7 (synergy). These three rounds alone account for over 60% of M_R variability.', bold=True, italic=True)
    page_break(doc)

    # ══════════════════ PART IV HEADER ══════════════════
    t = h(doc, 'PART IV: REFERENCE', 1, TEAL)
    page_break(doc)

    # ══════════════════ § 12: STRATEGIC TIPS ══════════════════
    h(doc, '12. Strategic Tips & Common Mistakes', 1)
    h(doc, '12.1 Top 5 Strategic Tips', 2)
    tips = [
        ('Invest in R1 Deep Audit (Option B)', 'Spending $3M in R1 halves R4 crisis damage. This is the highest-ROI decision in the entire simulation — it prevents $6M+ in downstream losses.'),
        ('Never ignore a BU for 2+ rounds', 'Technical Debt engine adds 4% OPEX compounding. Combined with Natural Decay (2% reputation/SLO loss), neglect spirals quickly.'),
        ('Watch Social License carefully', 'If average SLO drops below 75, the Instability Discount wipes 0.40 from M_R — equivalent to losing ~$180M in terminal value.'),
        ('Target the Synergy Unlock (R7C)', 'At +0.30 M_R, this is the single highest bonus. Ensure synergy_multiplier ≥ 0.80 to qualify.'),
        ('Think in systems, not rounds', 'Decisions in R1 echo through R10. Map the flag dependency chain before committing.'),
    ]
    for i, (title, desc) in enumerate(tips, 1):
        body(doc, f"Tip {i}: {title}", bold=True)
        body(doc, desc)

    h(doc, '12.2 Common Mistakes', 2)
    mistakes = [
        'Over-investing in one BU — triggers Technology Lock-In and Revenue Cannibalization engines',
        'Choosing "cheap" options without considering flag consequences (R1A saves money but costs $6M+ at R4)',
        'Ignoring HR/talent — burnout compounds and triggers brain-drain OPEX inflation',
        'Cutting dividends sharply — triggers Dividend Ratchet reputation penalty (-5)',
        'Taking insurance-only path in R5 — permanently blocks +0.20 Resilience M_R bonus',
        'Choosing R6C (Monetise Algorithm) — triggers EU AI Act costs AND reputation -20',
    ]
    for m in mistakes:
        bullet(doc, m)
    page_break(doc)

    # ══════════════════ § 13: GLOSSARY ══════════════════
    h(doc, '13. Glossary of Key Terms', 1)
    glossary = [
        ('Business Unit (BU)', 'One of four operational divisions of Muressons Global Corporation. Default: Pharma, Electronics, Consumer Goods, Software.'),
        ('CAPEX', 'Capital Expenditure — investment allocated to each BU per round from the CSF pool.'),
        ('Carbon Intensity (CI)', 'Measure of CO₂ emissions relative to economic activity (0-100). Determines carbon tax at terminal valuation.'),
        ('Contagion Engine', 'Mathematical model propagating reputational damage across BUs using a sigmoid function.'),
        ('Corporate Strategic Fund (CSF)', 'Total capital pool available for investment each round = gross profit minus dividends.'),
        ('CSRD', 'Corporate Sustainability Reporting Directive — EU regulation requiring ESG impact reporting.'),
        ('Decision Paradigm', 'Mode of strategic decision-making: Narrative Crisis (A/B/C), Strategic Pillars, Advanced Climate, or Healthcare.'),
        ('Double Materiality', 'Framework considering both financial materiality (risks to company) and impact materiality (company impact on society).'),
        ('EBITDA', 'Earnings Before Interest, Taxes, Depreciation, and Amortisation — primary profitability metric.'),
        ('ESG', 'Environmental, Social, and Governance — the three pillars of sustainable business practice.'),
        ('Exit Multiple', 'Valuation multiplier applied to terminal EBITDA (default: 12×). Represents investor confidence.'),
        ('Flag', 'Game-state marker set by decisions that carries forward to affect future rounds (e.g., electronics_blindspot).'),
        ('Foreshadowing', 'Subtle news hints injected during R5-R8 indicating which R10 ending pathway is approaching.'),
        ('Governance Risk', 'Score (0-100) reflecting corporate governance quality. High values reduce cash efficiency.'),
        ('Greenwashing Engine', 'Detects green rhetoric without investment (avg ratio < 15%), triggering social licence penalty.'),
        ('Investment Ratio', 'Proportion of CSF allocated to a BU (0.0-1.0). Higher ratios = more OPEX reduction.'),
        ('M_R (Regenerative Multiple)', 'Sustainability-adjusted valuation multiplier (range: ~0.0 to 2.08). Directly multiplies terminal value.'),
        ("Mendelow's Matrix", '2×2 Power-Interest stakeholder mapping framework used in the R1 minigame.'),
        ('Natural Capital Debt (NCD)', 'Liability representing unpriced environmental externalities. Compounds each round via interest.'),
        ('OPEX', 'Operating Expenditure — ongoing cost of running each BU. Reduced by investment and synergy.'),
        ('Scope 3 Emissions', 'Indirect value chain emissions (upstream suppliers, downstream customers). Typically 4× direct emissions.'),
        ('Sigmoid Function', 'S-curve mathematical function used in the Contagion Engine for damage propagation.'),
        ('Social License to Operate (SLO)', 'Score (0-100) reflecting community and stakeholder consent. Below 75 triggers Instability Discount.'),
        ('Stochastic Event', 'Probabilistic game event with outcomes determined by random roll (e.g., R5 cyclone).'),
        ('Synergy Multiplier', 'Factor (0.5-2.0+) amplifying CAPEX effectiveness in reducing OPEX.'),
        ('Terminal Value (TV)', 'Final corporation valuation: EBITDA × Exit Multiple × M_R.'),
        ('VRIO Decay', 'Mechanism eroding competitive advantage over time (5% per round).'),
        ('Workforce Readiness', 'Global competence score (0-100). Below 40: -20% pillar effectiveness. Above 75: +0.10 M_R.'),
    ]
    for term, defn in sorted(glossary, key=lambda x: x[0].lower()):
        p = doc.add_paragraph()
        r = p.add_run(f"{term}: ")
        r.bold = True
        r.font.size = Pt(11)
        r = p.add_run(defn)
        r.font.size = Pt(11)
    page_break(doc)

    # ══════════════════ § 14: QUICK REFERENCE ══════════════════
    h(doc, '14. Quick Reference Card', 1)
    body(doc, 'Print this page as a one-page reference during gameplay.', italic=True)

    body(doc, 'Round Progression:', bold=True)
    styled_table(doc, ['Round', 'Theme', 'Key Flag to Target'],
        [('R1', 'ESG Foundations', 'Option B → deep_audit_completed'),
         ('R2', 'Double Materiality', 'Option A → materiality_aligned (+0.10 M_R)'),
         ('R3', 'Scope 3 Emissions', 'Avoid Option C greenwash_risk'),
         ('R4', 'Contagion Crisis', 'Full Transparency (Option A) for recovery'),
         ('R5', 'Climate Risk', 'Nature-Based (Option B) for resilience'),
         ('R6', 'AI Ethics', 'Option B → ethical_ai_overhaul (+0.15 M_R)'),
         ('R7', 'Circularity', 'Option C → synergy_unlock (+0.30 M_R)'),
         ('R8', 'Water Scarcity', 'Avoid electronics_water_priority'),
         ('R9', 'Just Transition', 'Option C → community_fund (+0.18 M_R)'),
         ('R10', 'Grand Finale', 'All flags evaluated → Terminal Value')])

    body(doc, 'Emergency Signals — When to Worry:', bold=True)
    bullet(doc, '🔴 Treasury < $5M → Turnaround Mode imminent')
    bullet(doc, '🔴 SLO < 40 for any BU → Strike risk + Social Collapse')
    bullet(doc, '🟡 Burnout > 50 → Brain-drain activating, OPEX rising')
    bullet(doc, '🟡 Governance Risk > 30 → Cash conversion degrading')
    bullet(doc, '🟢 M_R > 1.50 → On track for Safe Haven or better')

    roadmap_img = os.path.join(IMG, 'roadmap.png')
    if os.path.exists(roadmap_img):
        add_image(doc, roadmap_img, caption='Figure 14.1 — Round Progression Roadmap')
    page_break(doc)

    # ══════════════════ APPENDICES ══════════════════
    h(doc, 'APPENDICES', 1, TEAL)

    h(doc, 'Appendix A: Decision Paradigm Comparison', 2)
    styled_table(doc, ['Feature', 'Narrative Crisis', 'Strategic Pillars', 'Advanced Climate', 'Healthcare'],
        [('Decision Style', 'A/B/C choice', '5-area toggles', 'Climate-focused', 'Healthcare network'),
         ('Complexity', 'Standard', 'High', 'High', 'Specialised'),
         ('BU Types', 'Corporate (4 BUs)', 'Corporate (4 BUs)', 'Corporate (4 BUs)', 'Hospital/Clinic/Telehealth'),
         ('Best For', 'First-time players', 'Experienced teams', 'Climate-focused courses', 'Healthcare MBA'),
         ('Engine Count', '8 core', '8 core + pillars', '8 core + carbon', '8 core + clinical')])
    spacer(doc)

    h(doc, 'Appendix B: Industry Vertical Alternatives', 2)
    body(doc, 'Facilitators can substitute the default BUs with industry-specific alternatives:')
    styled_table(doc, ['Vertical', 'BU 1', 'BU 2', 'BU 3', 'BU 4'],
        [('Default (Corporate)', 'Pharma', 'Electronics', 'Consumer Goods', 'Software'),
         ('Oil & Gas', 'Upstream', 'Midstream', 'Downstream', 'Renewables'),
         ('Banking', 'Retail Banking', 'Investment Banking', 'Insurance', 'Fintech'),
         ('Retail/FMCG', 'Food & Beverage', 'Fashion', 'Home & Living', 'E-Commerce'),
         ('Agriculture', 'Crop Production', 'Livestock', 'AgTech', 'Distribution'),
         ('Technology', 'Cloud Services', 'Hardware', 'AI/ML', 'Cybersecurity')])
    spacer(doc)

    h(doc, 'Appendix C: Minigames & Side Activities', 2)
    body(doc, 'The simulation includes several interactive minigames that enhance the learning experience:')
    minigames = [
        ("Mendelow's Stakeholder Matrix (R1)", 'Drag-and-drop 10 stakeholders onto a Power-Interest Grid. Achieving 80%+ accuracy earns a reputation bonus. Teaches stakeholder mapping methodology.'),
        ('CSRD Double Materiality Assessment (R2)', 'Assess CSRD issues across Financial and Impact materiality dimensions. Includes CFO budget validation gate. Teaches EU sustainability reporting frameworks.'),
        ('CEO Interview (Post-Game)', 'AI-powered 5-question competency assessment across 6 dimensions: Strategic Thinking, Stakeholder Empathy, Financial Acumen, Ethical Reasoning, Systems Thinking, and Adaptive Leadership. Produces a spider diagram and narrative feedback.'),
        ('Boardroom Showdown (R10)', 'Activist investor negotiation exercise with strategic stake analysis and proxy fight mechanics.'),
    ]
    for title, desc in minigames:
        body(doc, title, bold=True)
        body(doc, desc)

    # ── Footer ──
    page_break(doc)
    spacer(doc)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run('— End of Student Manual —')
    r.font.size = Pt(14)
    r.font.color.rgb = TEAL
    r.italic = True
    spacer(doc)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run('Muressons Global Corporation © 2026')
    r.font.size = Pt(10)
    r.font.color.rgb = RGBColor(0x99, 0x99, 0x99)

    return doc
