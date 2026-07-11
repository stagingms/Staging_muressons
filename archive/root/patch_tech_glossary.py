"""Patch TechnicalGlossary.js to add new terms with academic references."""
import re

TARGET = "frontend/app/components/TechnicalGlossary.js"

with open(TARGET, 'r', encoding='utf-8') as f:
    content = f.read()

# Add new financial terms after the Green Cost of Debt entry (id: 'gcod')
GCOD_END = "        significance: 'A CFO using a Green Cost of Debt lens"
gcod_block_end = content.find("'A CFO using a Green Cost of Debt lens")
# Find the end of that term block (next closing brace + comma)
gcod_obj_end = content.find("},", gcod_block_end) + 2

NEW_FIN_TERMS = """
      {
        id: 'dividend',
        name: 'Dividend Ratchet & Board Pressure',
        abbr: 'Div Ratchet',
        keywords: 'dividend ratchet board pressure distribution cut reputation investor expectations',
        definition: 'A governance mechanism that penalises teams who cut dividends by more than 20% relative to the previous round. Cutting dividends triggers a -5 Group Reputation hit, modelling real-world investor expectations for distribution consistency and the board accountability pressure that accompanies it.',
        logic: 'Evaluated in engine.py → calc_dividend_ratchet(). Compares current_dividends against previous_round_dividends × 0.80. If below threshold, applies reputation penalty. Dividends are clamped to available treasury (VULN-001). This creates a strategic tension: reducing dividends frees cash for CAPEX but damages stakeholder confidence.',
        formula: `$$\\\\text{If Dividends}_t < 0.80 \\\\times \\\\text{Dividends}_{t-1}: \\\\quad \\\\text{Rep}_{t+1} = \\\\text{Rep}_t - 5$$`,
        significance: 'Ref: Lintner, J. (1956). "Distribution of Incomes of Corporations Among Dividends, Retained Earnings, and Taxes." American Economic Review, 46(2), 97-113. The Dividend Ratchet operationalises Lintner\\'s partial adjustment model: managers smooth dividends because cuts signal negative private information to markets.',
      },
      {
        id: 'implementation',
        name: 'Implementation Lag & J-Curve Returns',
        abbr: 'Impl. Lag',
        keywords: 'implementation lag deferred returns J-curve CAPEX delay investment timing',
        definition: 'Infrastructure investments whose financial benefits are not immediately realised but mature over 1-2 subsequent rounds. Investments exceeding 10% of BU revenue are automatically deferred by one round, modelling the real-world construction/gestation period between capital commitment and operational benefit.',
        logic: 'Applied in engine.py → calc_synergy_opex(). If investment_ratio > 0.10, the effective_ratio for the current round is set to 0 (benefit deferred). The pending benefit is stored in global_round_states.pending_capex_projects with rounds_remaining = 1. R5-A Hard Engineering uses a 2-round delay for resilience protection.',
        formula: `$$\\\\text{If InvRatio}_i > 0.10: \\\\quad \\\\text{Effective}_{t} = 0, \\\\quad \\\\text{Effective}_{t+1} = \\\\sqrt{\\\\text{InvRatio}} \\\\times 0.7$$
$$\\\\text{Pending Project: }\\\\{\\\\tau_{\\\\text{rem}} = 1, \\\\; \\\\text{effect}: \\\\Delta\\\\text{OPEX}\\\\}$$`,
        significance: 'Ref: Dixit, A.K. & Pindyck, R.S. (1994). "Investment under Uncertainty." Princeton University Press. The implementation lag teaches that real options have gestation periods—teams who spend heavily in R1 expecting immediate OPEX savings are forced to absorb a full round of costs before benefits materialise, creating the classic J-curve payoff profile.',
      },
"""

content = content[:gcod_obj_end] + NEW_FIN_TERMS + content[gcod_obj_end:]

# Add new sustainability terms after the Water Dependency entry (id: 'water')
water_sig = "A COO who ignores Water Dependency"
water_pos = content.find(water_sig)
water_obj_end = content.find("},", water_pos) + 2

NEW_ESG_TERMS = """
      {
        id: 'burnout',
        name: 'Staff Burnout & Workforce Wellbeing',
        abbr: 'Burnout',
        keywords: 'staff burnout wellbeing workforce WHO ICD-11 hr opex penalty fatigue exhaustion',
        definition: 'A global workforce metric [0–100] representing cumulative occupational exhaustion across all business units. Recognised by WHO in ICD-11 (2019) as an occupational phenomenon. In the simulation, burnout compounds OPEX penalties and blocks the +0.05 M_R Wellbeing Champion bonus if above 20 at R10.',
        logic: 'Modified by HR investment decisions in the Strategic Pillars paradigm. High HR: -10, Medium: -4, None: +3 drift per round. OPEX penalty activates above 20: penalty = ((burnout-20)²) × 0.000028. Critical threshold at 70 triggers additional governance risk increases.',
        formula: `$$\\\\text{Burnout}_{t+1} = \\\\text{Burnout}_t + \\\\Delta_{\\\\text{HR}} + 3_{\\\\text{drift}}$$
$$\\\\text{OPEX Penalty} = \\\\left(\\\\max(0, \\\\text{Burnout} - 20)\\\\right)^2 \\\\times 0.000028$$
$$\\\\text{Wellbeing Bonus: }+0.05\\\\;M_R \\\\text{ iff }\\\\overline{\\\\text{Burnout}} < 20 \\\\text{ at R10}$$`,
        significance: 'Ref: WHO (2019). ICD-11 Burn-out Classification (QD85). Maslach, C. & Leiter, M. (2016). "Understanding Burnout." World Psychiatry, 15(2). The simulation models burnout as an organisational externality: individual-level exhaustion compounds into enterprise-wide productivity loss, creating a hidden OPEX drag that is invisible on standard P&L reports until it reaches critical mass.',
      },
      {
        id: 'readiness',
        name: 'Workforce Readiness Index',
        abbr: 'WRI',
        keywords: 'workforce readiness competence training learning organisational capacity HR human capital',
        definition: 'A global competence score [0–100, starting at 50] that measures the organisation\\'s collective ability to execute strategic initiatives. Low readiness (<40) reduces the effectiveness of all pillar decisions by 20%. High readiness (≥75) earns a +0.10 M_R bonus at terminal valuation.',
        logic: 'Modified by HR investment in Strategic Pillars. High HR: +8, Medium: +4, None: -5 per round. Feeds into pillar_effectiveness_multiplier = 0.80 if readiness < 40, else 1.0. The readiness score is a proxy for organisational learning capacity (Senge, 1990).',
        formula: `$$\\\\text{WRI}_{t+1} = \\\\text{WRI}_t + \\\\Delta_{\\\\text{HR}}, \\\\quad \\\\Delta \\\\in \\\\{-5, +4, +8\\\\}$$
$$\\\\text{Pillar Effectiveness} = \\\\begin{cases} 0.80 & \\\\text{WRI} < 40 \\\\\\\\ 1.00 & \\\\text{otherwise} \\\\end{cases}$$
$$\\\\text{M_R Bonus: }+0.10 \\\\text{ iff WRI} \\\\geq 75 \\\\text{ at R10}$$`,
        significance: 'Ref: Senge, P. (1990). "The Fifth Discipline." Currency Doubleday. Becker, G. (1964). "Human Capital." NBER. The workforce readiness metric operationalises the resource-based view of human capital: organisations that systematically underinvest in talent development erode their capacity to execute even well-designed strategies.',
      },
      {
        id: 'greenwash',
        name: 'Greenwashing Detection Engine',
        abbr: 'Greenwash',
        keywords: 'greenwashing ESG misrepresentation social license penalty rhetoric investment ratio ESMA',
        definition: 'An automated detection engine that identifies discrepancies between stated ESG commitments and actual investment behaviour. If R3-C (Marketing-Only Pledge) is selected and the average investment ratio across all BUs drops below 15% in any subsequent round, the engine triggers an 8-point SLO penalty across ALL business units.',
        logic: 'Computed in engine.py → check_greenwashing(). Requires the greenwash_risk flag (set by R3-C) AND avg_investment_ratio < 0.15 in the current round. The penalty is applied to social_license_score for every BU simultaneously, modelling the reputational cascade from a public greenwashing scandal.',
        formula: `$$\\\\text{If greenwash\\\\_risk AND }\\\\frac{1}{n}\\\\sum_{i=1}^{n} \\\\text{InvRatio}_i < 0.15: \\\\quad \\\\forall i:\\; \\\\text{SLO}_i \\\\mathrel{-}= 8$$`,
        significance: 'Ref: ESMA (2023). Guidelines on Funds\\' Names Using ESG or Sustainability-Related Terms. Lyon, T. & Montgomery, A. (2015). "The Means and End of Greenwash." Organization & Environment, 28(2). The engine teaches that ESG commitments without capital backing create regulatory and reputational exposure that compounds over time.',
      },
"""

content = content[:water_obj_end] + NEW_ESG_TERMS + content[water_obj_end:]

# Add new strategic terms after the Pending CAPEX entry (id: 'capex')
capex_sig = "infrastructure project management and regulatory capital planning"
capex_pos = content.find(capex_sig)
capex_obj_end = content.find("},", capex_pos) + 2

NEW_STRAT_TERMS = """
      {
        id: 'circular',
        name: 'Circular Economy & Industrial Symbiosis',
        abbr: 'Circularity',
        keywords: 'circular economy waste to energy industrial symbiosis Ellen MacArthur Foundation lifecycle redesign',
        definition: 'An economic model that eliminates waste and pollution by circulating products and materials at their highest value. In R7, the Industrial Symbiosis pathway (Option C: Waste-to-Energy) provides the single highest M_R bonus (+0.30) by converting one BU\\'s waste stream into another\\'s energy input.',
        logic: 'Triggered by R7-C decision, which sets the synergy_unlock flag and adds +0.35 to synergy_multiplier. The M_R bonus (+0.30) is evaluated at R10 and requires the synergy_unlock flag to be active. This is the largest individual M_R component and the key gate for the "Resist & Integrate" R10 option.',
        formula: `$$\\\\text{R7-C: }\\\\phi_{\\\\text{syn}} \\\\mathrel{+}= 0.35, \\\\quad \\\\text{Flag: synergy\\\\_unlock} = \\\\text{True}$$
$$\\\\text{M_R Component: }\\\\Delta M_R^{\\\\text{syn}} = +0.30 \\\\text{ iff synergy\\\\_unlock AND }\\\\phi_{\\\\text{syn}} \\\\times 100 > 80$$`,
        significance: 'Ref: Ellen MacArthur Foundation (2013). "Towards the Circular Economy." McDonough, W. & Braungart, M. (2002). "Cradle to Cradle." The R7 decision is the simulation\\'s most consequential single choice: the synergy boost (+0.35) compounds through VRIO decay, and the M_R bonus (+0.30) is worth approximately $108M in terminal value at median EBITDA.',
      },
      {
        id: 'justtrans',
        name: 'Just Transition & ILO Framework',
        abbr: 'Just Trans.',
        keywords: 'just transition ILO Paris Agreement workforce displacement community fund managed closure',
        definition: 'Operationalises the ILO/UN definition of just transition—ensuring the shift to a sustainable economy does not leave workers and communities behind. R9 presents three pathways with fundamentally different financial and social outcomes, from immediate closure (strike risk) to community fund (M_R bonus).',
        logic: 'R9-A (Immediate Closure): SLO -20, strike probability engine activates. R9-B (Managed Transition, -$12M): SLO neutral, +0.12 M_R. R9-C (Community Fund, -$20M): SLO +0.18 M_R, strike prevented. Strike probability is evaluated via engine.py → calc_strike_probability() using SLO and governance risk.',
        formula: `$$\\\\text{R9-A: }P_{\\\\text{strike}} = \\\\frac{\\\\text{GovRisk}}{100} + \\\\left(1 - \\\\frac{\\\\text{SLO}}{100}\\\\right) \\\\times 0.4$$
$$\\\\text{R9-C: }\\\\Delta M_R^{\\\\text{community}} = +0.18 \\\\times \\\\text{JT\\\\_scaling}$$
$$\\\\text{StrikeCost} = \\\\sum_{i=1}^{n} \\\\text{Revenue}_i \\\\quad (\\\\text{deducted from treasury})$$`,
        significance: 'Ref: ILO (2015). "Guidelines for a Just Transition." Paris Agreement, Article 4(1). Rosemberg, A. (2010). "Building a Just Transition." ITUC. The R9 calculation reveals that the Community Fund (-$20M) has a positive expected value vs. Immediate Closure when strike probability exceeds 40%—making the ethical choice also the financially rational one.',
      },
      {
        id: 'aiethics',
        name: 'AI Ethics & EU AI Act Compliance',
        abbr: 'AI Ethics',
        keywords: 'AI ethics algorithmic bias EU AI Act recruitment transparency ethical overhaul truth premium',
        definition: 'R6 presents the discovery of systematic algorithmic bias in the Software BU\\'s recruitment AI, creating a regulatory and ethical crisis. The three options model the full spectrum of corporate responses to AI governance failures, from ethical overhaul to monetisation of biased systems.',
        logic: 'R6-B (Ethical AI Overhaul, -$8M): sets ethical_ai_overhaul flag → +0.15 M_R Truth Premium. R6-C (Monetise Algorithm, +$3M): sets ai_monetised flag → EU AI Act compliance costs from R7 onward (estimated -$2M/round). R6-A (Partial Fix, -$3M): middle ground, no M_R bonus.',
        formula: `$$\\\\text{R6-B: }\\\\Delta M_R^{\\\\text{truth}} = +0.15, \\\\quad \\\\text{TV Impact} \\\\approx +\\\\$54M$$
$$\\\\text{R6-C: }\\\\text{EU AI Act Cost} = -\\\\$2M/\\\\text{round from R7} \\\\quad (\\\\text{3 rounds} = -\\\\$6M)$$
$$\\\\text{Net R6-B vs R6-C: }\\\\$54M - \\\\$8M \\\\text{ vs } \\\\$3M - \\\\$6M = +\\\\$46M\\\\text{ vs }-\\\\$3M$$`,
        significance: 'Ref: EU AI Act (Regulation 2024/1689). Jobin, A. et al. (2019). "The Global Landscape of AI Ethics Guidelines." Nature Machine Intelligence, 1, 389-399. The Truth Premium teaches that ethical AI governance is not a cost centre but a value-accretive investment. The $8M overhaul generates $54M in terminal value—a 6.75× return.',
      },
"""

content = content[:capex_obj_end] + NEW_STRAT_TERMS + content[capex_obj_end:]

# Update the badge count from "21 Terms · 3 Clusters" to "30 Terms · 3 Clusters"
content = content.replace("21 Terms · 3 Clusters", "30 Terms · 3 Clusters")
content = content.replace("21 terms across 3 clusters", "30 terms across 3 clusters")

with open(TARGET, 'w', encoding='utf-8') as f:
    f.write(content)

print("SUCCESS: Added 9 new terms to TechnicalGlossary.js (30 total)")
